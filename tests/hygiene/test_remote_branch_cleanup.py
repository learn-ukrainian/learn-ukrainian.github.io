"""Public branch cleanup regressions, including Git's actual conditional delete."""

from __future__ import annotations

import base64
import copy
import hashlib
import io
import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar
from urllib.error import URLError
from urllib.parse import parse_qs, urlsplit

import pytest
import yaml

from scripts.hygiene import remote_branch_cleanup as m
from tests.common.github_cache_isolation import isolate_github_client_cache

REPO = "learn-ukrainian/learn-ukrainian.github.io"
REPO_ID = 1300192
HEAD = "a" * 40
OLD = "b" * 40
NOW = datetime(2026, 10, 17, 12, tzinfo=UTC)
ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def isolated_github_cache(tmp_path, monkeypatch):
    yield from isolate_github_client_cache(tmp_path, monkeypatch)


def branch(name="stale", head=OLD, protected=False):
    return {"name": name, "commit": {"sha": head}, "protected": protected}


def pr(repo=REPO, name="stale", number=1, **extra):
    return {
        "number": number,
        "state": "open",
        "head": {"repo": {"full_name": repo}, "ref": name, "sha": OLD},
        "base": {"repo": {"full_name": REPO}},
        **extra,
    }


def keep(text="main\n"):
    raw = text.encode()
    return {
        "path": m.KEEP_PATH,
        "type": "file",
        "encoding": "base64",
        "sha": hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest(),
        "content": base64.b64encode(raw).decode(),
    }


class API(m.GitHub):
    def __init__(self):
        super().__init__(REPO, "fixture")
        self.objects = {
            "": {"id": REPO_ID, "full_name": REPO, "private": False, "default_branch": "main"},
            "branches/main": branch("main", HEAD, True),
            f"contents/{m.KEEP_PATH}?ref={HEAD}": keep(),
            "branches/stale": branch(),
            f"git/commits/{OLD}": {"sha": OLD, "committer": {"date": "2026-10-15T12:00:00Z"}},
            f"git/commits/{HEAD}": {"sha": HEAD, "committer": {"date": "2026-10-17T12:00:00Z"}},
        }
        self.listings = {"branches": [branch("main", HEAD, True), branch()], "pulls?state=open": []}
        self.calls = []
        self.before_get = None

    def get(self, endpoint):
        self.calls.append(endpoint)
        if self.before_get:
            self.before_get(endpoint)
        if "per_page=" in endpoint:
            path = endpoint.split("&per_page=")[0] if "&per_page=" in endpoint else endpoint.split("?per_page=")[0]
            return copy.deepcopy(self.listings[path]), ""
        return copy.deepcopy(self.objects[endpoint]), ""


@pytest.fixture
def api(monkeypatch):
    value = API()
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("GITHUB_SHA", HEAD)
    real_git = m.git

    def source_git(*args):
        if args[0] == "remote":
            return f"https://github.com/{REPO}.git\n"
        if args[0] == "rev-parse":
            return HEAD + "\n"
        return real_git(*args)

    monkeypatch.setattr(m, "git", source_git)
    return value


def test_cleanup_reports_only_confirmed_name_and_sha(api, monkeypatch):
    deleted = []
    monkeypatch.setattr(m, "delete", deleted.append)
    report = m.cleanup(api, NOW)
    assert report["deleted"] == [{"name": "stale", "sha": OLD}]
    assert report["failures"] == []
    assert report["retained"] == [{"name": "main", "reason": "ineligible"}]
    assert deleted == [m.Candidate("stale", OLD, NOW - timedelta(hours=48), False)]
    assert api.calls.count("pulls?state=open&per_page=100&page=1") == 2
    assert api.calls.count(f"contents/{m.KEEP_PATH}?ref={HEAD}") == 2
    assert api.calls.count("branches/stale") == 2
    assert report["source_sha"] == HEAD


@pytest.mark.parametrize("hours,expected", [(47.999, False), (48, True), (49, True), (-1, False)])
def test_commit_age_boundary(api, hours, expected):
    evidence, _ = m.read_evidence(api)
    assert m.eligible(m.Candidate("stale", OLD, NOW - timedelta(hours=hours), False), evidence, REPO, NOW) is expected


@pytest.mark.parametrize("kind", ["main", "default", "protected", "keep", "open", "draft", "reopened"])
def test_retained_ref_classes(api, kind):
    candidate = m.Candidate("stale", OLD, NOW - timedelta(hours=72), kind == "protected")
    if kind == "main":
        candidate = m.Candidate("main", OLD, candidate.committed, False)
    elif kind == "default":
        api.objects[""]["default_branch"] = "stale"
    elif kind == "keep":
        api.objects[f"contents/{m.KEEP_PATH}?ref={HEAD}"] = keep("main\nstale\n")
    elif kind in {"open", "draft", "reopened"}:
        api.listings["pulls?state=open"] = [pr(draft=kind == "draft")]
    if kind == "default":
        # Default can differ from main; keep is bound to its verified head.
        api.objects["branches/stale"] = branch("stale", HEAD)
        api.listings["branches"][1] = branch("stale", HEAD)
    evidence, _ = m.read_evidence(api)
    assert not m.eligible(candidate, evidence, REPO, NOW)


def test_fork_name_collision_does_not_exclude_local_branch(api):
    api.listings["pulls?state=open"] = [pr(repo="someone/fork", draft=True)]
    evidence, _ = m.read_evidence(api)
    assert m.eligible(m.Candidate("stale", OLD, NOW - timedelta(hours=48), False), evidence, REPO, NOW)


@pytest.mark.parametrize("value", [None, "", "2026-02-30T00:00:00Z", "2026-10-15", "2026-10-15T12:00:00+00:00", 123])
def test_malformed_timestamp_refuses(value):
    with pytest.raises(m.Unknown, match="timestamp"):
        m.utc_timestamp(value)


@pytest.mark.parametrize("change", ["head", "protection", "protected_set", "keep", "pr", "default", "unknown"])
def test_final_evidence_changed_or_unknown_never_deletes(api, monkeypatch, change):
    attempted = []
    monkeypatch.setattr(m, "delete", attempted.append)
    checks = 0

    def mutate(endpoint):
        nonlocal checks
        if endpoint != "":
            return
        checks += 1
        if checks != 2:
            return
        if change == "head":
            api.objects["branches/stale"]["commit"]["sha"] = HEAD
        elif change == "protection":
            api.objects["branches/stale"]["protected"] = True
        elif change == "protected_set":
            api.listings["branches"][1]["protected"] = True
        elif change == "keep":
            api.objects[f"contents/{m.KEEP_PATH}?ref={HEAD}"] = keep("main\nstale\n")
        elif change == "pr":
            api.listings["pulls?state=open"] = [pr()]
        elif change == "default":
            api.objects[""]["default_branch"] = "stale"
            api.objects[f"contents/{m.KEEP_PATH}?ref={OLD}"] = keep()
        else:
            raise m.Unknown("API failed")

    api.before_get = mutate
    report = m.cleanup(api, NOW)
    assert report["deleted"] == []
    assert attempted == []
    assert report["failures"] or {"name": "stale", "reason": "eligibility evidence changed"} in report["retained"]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda a: a.objects[""].update(private=True),
        lambda a: a.objects[""].update(full_name="other/repo"),
        lambda a: a.objects["branches/main"].update(name="wrong"),
        lambda a: a.objects[f"contents/{m.KEEP_PATH}?ref={HEAD}"].update(sha=OLD),
        lambda a: a.objects[f"contents/{m.KEEP_PATH}?ref={HEAD}"].update(type="symlink"),
        lambda a: a.objects[f"contents/{m.KEEP_PATH}?ref={HEAD}"].update(content="!"),
        lambda a: a.objects[f"contents/{m.KEEP_PATH}?ref={HEAD}"].update(content=None),
        lambda a: a.objects[f"contents/{m.KEEP_PATH}?ref={HEAD}"].update(keep("bad ref\n")),
        lambda a: a.listings["branches"].append(branch()),
        lambda a: a.listings["branches"].clear(),
        lambda a: a.listings["pulls?state=open"].append(pr(state="closed")),
        lambda a: a.listings["pulls?state=open"].append(pr(head={"repo": None})),
        lambda a: a.listings["pulls?state=open"].append(pr(base={"repo": {"full_name": "other/repo"}})),
        lambda a: a.listings["pulls?state=open"].extend([pr(), pr()]),
    ],
)
def test_unknown_inventory_refuses(api, monkeypatch, mutation):
    mutation(api)
    monkeypatch.setattr(m, "delete", lambda _: pytest.fail("deletion after unknown evidence"))
    report = m.cleanup(api, NOW)
    assert report["deleted"] == []
    assert len(report["failures"]) == 1


@pytest.mark.parametrize(
    "mutation",
    [
        lambda a: a.objects["branches/stale"].update(protected=None),
        lambda a: a.objects["branches/stale"].update(name="other"),
        lambda a: a.objects[f"git/commits/{OLD}"].update(sha=HEAD),
        lambda a: a.objects[f"git/commits/{OLD}"].update(committer=None),
        lambda a: a.objects[f"git/commits/{OLD}"]["committer"].update(date="tomorrow"),
    ],
)
def test_unknown_candidate_refuses(api, mutation):
    mutation(api)
    report = m.cleanup(api, NOW)
    assert report["deleted"] == []
    assert report["failures"][0]["name"] == "stale"


def test_future_commit_retained(api):
    api.objects[f"git/commits/{OLD}"]["committer"]["date"] = "2026-10-18T00:00:00Z"
    assert m.cleanup(api, NOW)["deleted"] == []


@pytest.mark.parametrize("value", ["../bad", "a..b", "foo.lock", "a\nb", "a\u202eb", "", None, "a:b", "a b", "*wild"])
def test_bad_refs_refuse(value):
    with pytest.raises(m.Unknown):
        m.branch_name(value)


@pytest.mark.parametrize("value", [None, "x", "a" * 39, "A" * 40, OLD + ";bad"])
def test_invalid_sha(value):
    with pytest.raises(m.Unknown):
        m.sha(value)


@pytest.mark.parametrize("value", [None, "", "https://github.com/a/b", "a/b/c", "a/..", "a/repo?x", "-x/y\n"])
def test_invalid_repository(value):
    with pytest.raises(m.Unknown):
        m.repository(value)


def test_pagination_follows_complete_set_and_full_page_sentinel(monkeypatch):
    api = m.GitHub(REPO, "fixture")
    calls = []

    def get(path):
        calls.append(path)
        page = int(path.rsplit("=", 1)[1])
        if page == 1:
            return [
                {"n": i} for i in range(100)
            ], f'<{m.API}/repos/{REPO}/pulls?state=open&per_page=100&page=2>; rel="next"'
        if page == 2:
            return [{"n": i} for i in range(100, 200)], ""
        return [], ""

    monkeypatch.setattr(api, "get", get)
    assert api.pages("pulls?state=open") == [{"n": i} for i in range(200)]
    assert len(calls) == 3


@pytest.mark.parametrize(
    "data,link",
    [
        ({}, ""),
        ([None], ""),
        ([{}] * 101, ""),
        ([], "garbage"),
        ([], '<https://evil.test/>; rel="next"'),
        ([], f'<{m.API}/repos/{REPO}/branches?per_page=100&page=3>; rel="next"'),
        ([], f'<{m.API}/repos/{REPO}/branches?per_page=100&page=3>; rel="last"'),
        ([], f'<{m.API}/repos/{REPO}/branches?per_page=100&page=2>; rel="next"'),
    ],
)
def test_bad_pagination_refuses(monkeypatch, data, link):
    api = m.GitHub(REPO, "fixture")
    monkeypatch.setattr(api, "get", lambda _: (data, link))
    with pytest.raises(m.Unknown):
        api.pages("branches")


@pytest.mark.parametrize(
    "failure", [URLError("failed"), OSError("failed"), ValueError("bad JSON"), m.github_client.GitHubRateLimited(None)]
)
def test_api_errors_are_closed(monkeypatch, failure):
    api = m.GitHub(REPO, "fixture")
    monkeypatch.setattr(api.opener, "open", lambda *a, **kw: (_ for _ in ()).throw(failure))
    with pytest.raises(m.Unknown, match="API unavailable"):
        api.get("branches")


def test_api_request_fixed_destination_and_headers(monkeypatch):
    api = m.GitHub(REPO, "fixture")

    class Response(io.BytesIO):
        status = 200
        headers: ClassVar = {"Link": "links"}

    def open_request(request, timeout):
        assert request.full_url == f"{m.API}/repos/{REPO}/branches"
        assert request.get_header("Authorization") == "Bearer fixture"
        assert request.get_header("Cache-control") == "no-cache"
        assert timeout == 30
        return Response(b'{"ok": true}')

    monkeypatch.setattr(api.opener, "open", open_request)
    assert api.get("branches") == ({"ok": True}, "links")
    with pytest.raises(m.Unknown, match="redirect"):
        m.NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.test")
    monkeypatch.setattr(api, "get", lambda _: ([], ""))
    with pytest.raises(m.Unknown):
        api.object("branches")


def test_shared_client_rereads_metadata_and_preserves_pagination(monkeypatch):
    api = m.GitHub(REPO, "fixture")
    link = f'<{m.API}/repos/{REPO}/branches?per_page=100&page=2>; rel="next"'
    calls = []

    def open_request(request, timeout):
        calls.append(request.full_url)
        response = io.BytesIO(json.dumps({"read": len(calls)}).encode())
        response.status = 200
        response.headers = {"Link": link, "ETag": '"fixture"'}
        assert request.get_header("If-none-match") is None
        return response

    monkeypatch.setattr(api.opener, "open", open_request)
    assert api.get("branches") == ({"read": 1}, link)
    assert api.get("branches") == ({"read": 2}, link)
    assert calls == [f"{m.API}/repos/{REPO}/branches"] * 2


@pytest.mark.parametrize("status,body", [(302, b"{}"), (500, b"{}"), (204, b""), (304, b""), (200, b"bad JSON")])
def test_shared_client_bad_response_refuses(monkeypatch, status, body):
    api = m.GitHub(REPO, "fixture")

    def open_request(*args, **kwargs):
        response = io.BytesIO(body)
        response.status = status
        response.headers = {}
        return response

    monkeypatch.setattr(api.opener, "open", open_request)
    with pytest.raises(m.Unknown):
        api.get("branches")


def test_shared_client_rate_hold_refuses_without_retry_or_stale_data(monkeypatch):
    api = m.GitHub(REPO, "fixture")
    calls = []

    def open_request(*args, **kwargs):
        calls.append(1)
        response = io.BytesIO(b"[]")
        response.status = 200 if len(calls) == 1 else 429
        response.headers = {} if len(calls) == 1 else {"Retry-After": "60"}
        return response

    monkeypatch.setattr(api.opener, "open", open_request)
    assert api.get("branches") == ([], "")
    for _ in range(2):
        with pytest.raises(m.Unknown, match="API unavailable"):
            api.get("branches")
    assert len(calls) == 2


@pytest.mark.parametrize(
    "field,value",
    [
        ("GITHUB_REF", "refs/tags/main"),
        ("GITHUB_REF", "refs/heads/evil"),
        ("GITHUB_SHA", OLD),
        ("GITHUB_EVENT_NAME", "push"),
    ],
)
def test_untrusted_source_refuses(api, monkeypatch, field, value):
    monkeypatch.setenv(field, value)
    assert m.cleanup(api, NOW)["failures"]


def test_untrusted_remote_refuses(api, monkeypatch):
    monkeypatch.setattr(
        m, "git", lambda *args: "git version fixture" if args == ("--version",) else "https://evil.test/x.git\n"
    )
    assert m.cleanup(api, NOW)["failures"]


def test_non_utc_clock_refuses(api):
    evidence, _ = m.read_evidence(api)
    with pytest.raises(m.Unknown, match="UTC"):
        m.eligible(m.Candidate("stale", OLD, NOW, False), evidence, REPO, NOW.replace(tzinfo=None))


@pytest.mark.parametrize("reason", ["git refused operation", "git unavailable or timed out; outcome unknown"])
def test_failed_delete_not_success_or_inferred_from_absence(api, monkeypatch, reason):
    def fail(_):
        api.objects.pop("branches/stale")
        raise m.Unknown(reason)

    monkeypatch.setattr(m, "delete", fail)
    report = m.cleanup(api, NOW)
    assert report["deleted"] == []
    assert report["failures"] == [{"name": "stale", "reason": reason}]


def test_prior_success_survives_later_failure(api, monkeypatch):
    api.listings["branches"].append(branch("second"))
    api.objects["branches/second"] = branch("second")

    def remove(candidate):
        if candidate.name == "second":
            raise m.Unknown("git refused operation")

    monkeypatch.setattr(m, "delete", remove)
    report = m.cleanup(api, NOW)
    assert report["deleted"] == [{"name": "stale", "sha": OLD}]
    assert report["failures"] == [{"name": "second", "reason": "git refused operation"}]


def test_accepted_metadata_race_is_not_claimed_prevented(api, monkeypatch):
    def remove(_):
        # Metadata arrives after the final read. The ref lease does not cover it.
        api.listings["pulls?state=open"] = [pr()]

    monkeypatch.setattr(m, "delete", remove)
    assert m.cleanup(api, NOW)["deleted"] == [{"name": "stale", "sha": OLD}]
    assert "accepted residual race" in (ROOT / "docs/runbooks/remote-branch-cleanup.md").read_text()


@pytest.mark.parametrize("name", ["stale", "-option", "topic/quote'\";$(false)", "topic/`false`"])
def test_delete_renders_single_explicit_ref_arguments(monkeypatch, name):
    calls = []

    def command(*args):
        calls.append(args)
        if args[0] == "check-ref-format":
            return ""
        return f"-\t:refs/heads/{name}\t[deleted]\n"

    monkeypatch.setattr(m, "git", command)
    m.delete(m.Candidate(name, OLD, NOW, False))
    assert calls[-1] == (
        "-c",
        "remote.origin.mirror=false",
        "-c",
        "push.followTags=false",
        "push",
        "--porcelain",
        f"--force-with-lease=refs/heads/{name}:{OLD}",
        "--no-follow-tags",
        "origin",
        f":refs/heads/{name}",
    )


def test_no_deletion_receipt_is_unknown(monkeypatch):
    monkeypatch.setattr(m, "git", lambda *args: "=\t:refs/heads/stale\t[up to date]\n")
    with pytest.raises(m.Unknown, match="no confirmed deletion"):
        m.delete(m.Candidate("stale", OLD, NOW, False))


@pytest.mark.parametrize("failure", [OSError("failed"), subprocess.TimeoutExpired(["git"], 60)])
def test_git_wrapper_failure(monkeypatch, failure):
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: (_ for _ in ()).throw(failure))
    with pytest.raises(m.Unknown, match="outcome unknown"):
        m.git("--version")


def test_git_wrapper_no_shell_and_closed_failure(monkeypatch):
    def command(args, **kwargs):
        assert args == ["git", "check-ref-format", "refs/heads/$(false)"]
        assert kwargs.get("shell", False) is False
        assert kwargs["env"]["GIT_TERMINAL_PROMPT"] == "0"
        return SimpleNamespace(returncode=1, stdout="", stderr="private diagnostics")

    monkeypatch.setattr(subprocess, "run", command)
    with pytest.raises(m.Unknown, match=r"^git refused operation$"):
        m.git("check-ref-format", "refs/heads/$(false)")


def test_actual_git_lease_deletion_and_moved_ref_refusal(tmp_path, monkeypatch, record_property):
    """Only newly created local refs/remotes are changed; no live GitHub deletion."""
    remote = tmp_path / "owned.git"
    local = tmp_path / "local"
    local.mkdir()

    def run(*args):
        result = subprocess.run(["git", *args], cwd=local, text=True, capture_output=True, check=True, timeout=30)
        return result.stdout.strip()

    run("init", "--bare", str(remote))
    run("init", "--initial-branch=main")
    run("config", "user.email", "fixture@example.invalid")
    run("config", "user.name", "Fixture")
    run("remote", "add", "origin", str(remote))
    run("-c", "core.hooksPath=/dev/null", "commit", "--allow-empty", "-m", "first")
    first = run("rev-parse", "HEAD")
    run("-c", "core.hooksPath=/dev/null", "commit", "--allow-empty", "-m", "second")
    second = run("rev-parse", "HEAD")
    run("push", "origin", f"{first}:refs/heads/matching", f"{first}:refs/heads/moved")
    run("push", "origin", f"{second}:refs/heads/moved")
    monkeypatch.chdir(local)
    version = m.git("--version").strip()
    record_property("git_oracle", version)
    print(f"Git oracle: {version}; owned disposable local remote")
    m.delete(m.Candidate("matching", first, NOW, False))
    assert run("ls-remote", "origin", "refs/heads/matching") == ""
    with pytest.raises(m.Unknown):
        m.delete(m.Candidate("moved", first, NOW, False))
    assert run("ls-remote", "origin", "refs/heads/moved") == f"{second}\trefs/heads/moved"
    with pytest.raises(m.Unknown):
        m.delete(m.Candidate("preexisting-absent", first, NOW, False))
    for name in ["-option", "topic/quote'\";$(false)", "topic/`false`"]:
        run("push", "origin", f"{first}:refs/heads/{name}")
        m.delete(m.Candidate(name, first, NOW, False))
        assert run("ls-remote", "origin", f"refs/heads/{name}") == ""


def test_main_json_summary_and_failure_exit(api, monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("GH_TOKEN", "fixture")
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    summary = tmp_path / "summary"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.setattr(m, "GitHub", lambda *args: api)
    monkeypatch.setattr(m, "cleanup", lambda *args: {"deleted": [{"name": "a```", "sha": OLD}], "failures": []})
    assert m.main(["--repo", REPO]) == 0
    assert json.loads(capsys.readouterr().out)["deleted"] == [{"name": "a```", "sha": OLD}]
    assert '    "deleted": [' in summary.read_text()
    monkeypatch.delenv("GH_TOKEN")
    assert m.main(["--repo", REPO]) == 1
    assert json.loads(capsys.readouterr().out)["deleted"] == []


def test_cli_help(capsys):
    with pytest.raises(SystemExit) as exc:
        m.main(["--help"])
    assert exc.value.code == 0
    output = capsys.readouterr().out
    assert all(text in output for text in ["--repo", "Outputs:", "Exit codes:", "Related:", "48 hours"])


@pytest.mark.parametrize("event", ["schedule", "workflow_dispatch"])
def test_checkout_origin_workflow_reaches_safe_cleanup(api, monkeypatch, tmp_path, event):
    """Replay the pinned checkout's actual suffixless origin, without network writes."""
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True, timeout=30)
    subprocess.run(
        ["git", "-C", str(tmp_path), "remote", "add", "origin", f"https://github.com/{REPO}"],
        check=True,
        timeout=30,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "remote", "set-url", "--push", "origin", f"https://github.com/{REPO}"],
        check=True,
        timeout=30,
    )
    workflow = yaml.safe_load((ROOT / ".github/workflows/stale-branch-cleanup.yml").read_text())
    script = workflow["jobs"]["cleanup"]["steps"][-1]["run"].strip()
    setup = script.rsplit("\n", 1)[0] if "\n" in script else ""
    monkeypatch.setenv("REPO", REPO)
    monkeypatch.setenv("GITHUB_EVENT_NAME", event)
    subprocess.run(["bash", "-e", "-c", setup], cwd=tmp_path, check=True, timeout=30)
    source_git = m.git

    def checkout_git(*args):
        if args[0] == "remote":
            return subprocess.check_output(["git", "-C", str(tmp_path), *args], text=True, timeout=30)
        return source_git(*args)

    monkeypatch.setattr(m, "git", checkout_git)
    deleted = []
    monkeypatch.setattr(m, "delete", deleted.append)
    report = m.cleanup(api, NOW)
    assert report["deleted"] == [{"name": "stale", "sha": OLD}]
    assert report["failures"] == []
    assert deleted == [m.Candidate("stale", OLD, NOW - timedelta(hours=48), False)]


@pytest.fixture
def wire_api(api, monkeypatch):
    """Real get/pages/shared-client stack; HTTP bodies use GitHub's public shapes."""
    client = m.GitHub(REPO, "fixture")
    calls = []
    options = {"numeric": True, "pr_on_page_two": False, "bad_link": None}

    def open_request(request, timeout):
        url = request.full_url
        calls.append(url)
        # Even numeric Link paths must never become request destinations.
        assert url.startswith(f"{m.API}/repos/{REPO}/")
        endpoint = url.removeprefix(f"{m.API}/repos/{REPO}/")
        parsed = urlsplit(endpoint)
        query = parse_qs(parsed.query)
        link = ""
        if "page" in query:
            assert query["per_page"] == ["100"]
            page = int(query["page"][0])
            collection = parsed.path
            assert query == ({"state": ["open"]} if collection == "pulls" else {}) | {
                "per_page": ["100"],
                "page": [str(page)],
            }
            if collection == "branches":
                data = [api.objects["branches/main"]] if page == 1 else [api.objects["branches/stale"]]
            else:
                open_pr = pr()
                open_pr["head"]["sha"] = api.objects["branches/stale"]["commit"]["sha"]
                data = (
                    [pr(name="unrelated", number=2)] if page == 1 else ([open_pr] if options["pr_on_page_two"] else [])
                )
            path = f"repositories/{REPO_ID}" if options["numeric"] else f"repos/{REPO}"
            filters = "state=open&" if collection == "pulls" else ""
            collection_url = f"{m.API}/{path}/{collection}?{filters}per_page=100"
            if page == 1:
                link = f'<{collection_url}&page=2>; rel="next", <{collection_url}&page=2>; rel="last"'
                if options["bad_link"] and collection == "pulls":
                    link = options["bad_link"]
            else:
                link = f'<{collection_url}&page=1>; rel="prev", <{collection_url}&page=1>; rel="first"'
            assert page in {1, 2}
        else:
            data = api.objects[endpoint]
        response = io.BytesIO(json.dumps(data).encode())
        response.status = 200
        response.headers = {"Link": link}
        return response

    monkeypatch.setattr(client.opener, "open", open_request)
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    monkeypatch.setenv("GH_TOKEN", "fixture")
    monkeypatch.setattr(m, "GitHub", lambda *args: client)
    return client, calls, options


@pytest.mark.parametrize("numeric", [False, True])
@pytest.mark.parametrize("pr_on_page_two", [False, True])
def test_cli_real_pagination_deletes_or_retains_from_all_pages(wire_api, monkeypatch, capsys, numeric, pr_on_page_two):
    _, calls, options = wire_api
    options.update(numeric=numeric, pr_on_page_two=pr_on_page_two)
    deleted = []
    monkeypatch.setattr(m, "delete", deleted.append)
    assert m.main(["--repo", REPO]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["failures"] == []
    assert report["deleted"] == ([] if pr_on_page_two else [{"name": "stale", "sha": OLD}])
    assert len(deleted) == (0 if pr_on_page_two else 1)
    for endpoint in ["branches?", "pulls?state=open&"]:
        assert f"{m.API}/repos/{REPO}/{endpoint}per_page=100&page=2" in calls


@pytest.mark.parametrize("numeric", [False, True])
@pytest.mark.parametrize("pr_on_page_two", [False, True])
def test_wire_pagination_with_actual_disposable_git_remote(
    api, wire_api, monkeypatch, tmp_path, capsys, numeric, pr_on_page_two
):
    """Only the source-identity seam is faked; deletion uses Git against our local bare remote."""
    _, calls, options = wire_api
    options.update(numeric=numeric, pr_on_page_two=pr_on_page_two)
    remote = tmp_path / "owned.git"
    local = tmp_path / "local"
    local.mkdir()

    def run(*args):
        result = subprocess.run(["git", *args], cwd=local, text=True, capture_output=True, timeout=30, check=False)
        assert result.returncode == 0, result.stderr
        return result.stdout.strip()

    run("init", "--bare", str(remote))
    run("init", "--initial-branch=fixture-default")
    run("config", "user.email", "fixture@example.invalid")
    run("config", "user.name", "Fixture")
    run("remote", "add", "origin", str(remote))
    monkeypatch.setenv("GIT_COMMITTER_DATE", "2026-10-15T12:00:00Z")
    run("-c", "core.hooksPath=/dev/null", "commit", "--allow-empty", "-m", "old")
    old_sha = run("rev-parse", "HEAD")
    monkeypatch.setenv("GIT_COMMITTER_DATE", "2026-10-17T12:00:00Z")
    run("-c", "core.hooksPath=/dev/null", "commit", "--allow-empty", "-m", "default")
    main_sha = run("rev-parse", "HEAD")
    run("push", "origin", f"{main_sha}:refs/heads/fixture-default", f"{old_sha}:refs/heads/stale")
    api.objects[""]["default_branch"] = "fixture-default"
    api.objects["branches/main"] = branch("fixture-default", main_sha, True)
    api.objects["branches/fixture-default"] = api.objects["branches/main"]
    api.objects["branches/stale"] = branch("stale", old_sha)
    for value, date in [(old_sha, "2026-10-15T12:00:00Z"), (main_sha, "2026-10-17T12:00:00Z")]:
        api.objects[f"git/commits/{value}"] = {"sha": value, "committer": {"date": date}}
    api.objects[f"contents/{m.KEEP_PATH}?ref={main_sha}"] = keep()
    monkeypatch.setenv("GITHUB_SHA", main_sha)
    monkeypatch.setenv("GITHUB_REF", "refs/heads/fixture-default")
    original = m.git

    def source_git(*args):
        if args == ("rev-parse", "HEAD"):
            return main_sha + "\n"
        return original(*args)

    monkeypatch.setattr(m, "git", source_git)
    monkeypatch.chdir(local)
    assert m.main(["--repo", REPO]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["deleted"] == ([] if pr_on_page_two else [{"name": "stale", "sha": old_sha}])
    assert report["failures"] == []
    assert run("ls-remote", "origin", "refs/heads/stale") == (f"{old_sha}\trefs/heads/stale" if pr_on_page_two else "")
    assert run("ls-remote", "origin", "refs/heads/fixture-default") == f"{main_sha}\trefs/heads/fixture-default"
    assert f"{m.API}/repos/{REPO}/pulls?state=open&per_page=100&page=2" in calls


@pytest.mark.parametrize(
    "url",
    [
        f"https://api.github.com/repositories/{REPO_ID + 1}/pulls?state=open&per_page=100&page=2",
        "https://api.github.com/repos/someone/else/pulls?state=open&per_page=100&page=2",
        f"https://api.github.com/repositories/{REPO_ID}/issues?state=open&per_page=100&page=2",
        f"https://evil.test/repositories/{REPO_ID}/pulls?state=open&per_page=100&page=2",
        f"http://api.github.com/repositories/{REPO_ID}/pulls?state=open&per_page=100&page=2",
        f"https://user@api.github.com/repositories/{REPO_ID}/pulls?state=open&per_page=100&page=2",
        f"https://api.github.com:443/repositories/{REPO_ID}/pulls?state=open&per_page=100&page=2",
        f"https://api.github.com/repositories/{REPO_ID}/pulls?state=open&per_page=100&page=2#fragment",
        *[
            f"https://api.github.com/repositories/{REPO_ID}/pulls?{query}"
            for query in [
                "per_page=100&page=2",
                "state=closed&per_page=100&page=2",
                "state=open&state=closed&per_page=100&page=2",
                "state=open&per_page=100&per_page=100&page=2",
                "state=open&page=2",
                "state=open&per_page=30&page=2",
                "state=open&per_page=100&page=1",
                "state=open&per_page=100&page=3",
                "state=open&per_page=100&page=2&page=3",
                "state=open&per_page=100&page=NaN",
                "state=open&per_page=100&page=2&base=main",
            ]
        ],
    ],
)
def test_cli_untrusted_pagination_refuses_without_following_link(wire_api, monkeypatch, capsys, url):
    _, calls, options = wire_api
    options["bad_link"] = f'<{url}>; rel="next"'
    monkeypatch.setattr(m, "delete", lambda _: pytest.fail("untrusted pagination allowed deletion"))
    assert m.main(["--repo", REPO]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["deleted"] == []
    assert len(report["failures"]) == 1
    assert calls[-1] == f"{m.API}/repos/{REPO}/pulls?state=open&per_page=100&page=1"


@pytest.mark.parametrize("value", [None, True, "1300192", 0, -1])
def test_repository_id_unknown_refuses(api, monkeypatch, value):
    api.objects[""]["id"] = value
    monkeypatch.setattr(m, "delete", lambda _: pytest.fail("unknown repository ID allowed deletion"))
    report = m.cleanup(api, NOW)
    assert report["deleted"] == []
    assert report["failures"] == [{"reason": "repository ID unknown or changed"}]


def test_repository_id_changed_at_final_read_refuses(api, monkeypatch):
    def change(endpoint):
        if endpoint == "" and api.calls.count("") == 2:
            api.objects[""]["id"] += 1

    api.before_get = change
    monkeypatch.setattr(m, "delete", lambda _: pytest.fail("changed repository ID allowed deletion"))
    report = m.cleanup(api, NOW)
    assert report["deleted"] == []
    assert report["failures"] == [{"name": "stale", "reason": "repository ID unknown or changed"}]


def test_numeric_pagination_without_repository_binding_refuses(monkeypatch):
    client = m.GitHub(REPO, "fixture")
    calls = []

    def get(endpoint):
        calls.append(endpoint)
        return [{}], f'<{m.API}/repositories/{REPO_ID}/branches?per_page=100&page=2>; rel="next"'

    monkeypatch.setattr(client, "get", get)
    with pytest.raises(m.Unknown, match="untrusted pagination link"):
        client.pages("branches")
    assert calls == ["branches?per_page=100&page=1"]


@pytest.mark.parametrize("omit_filter", [False, True])
def test_pagination_preserves_all_original_filters(monkeypatch, omit_filter):
    client = m.GitHub(REPO, "fixture")
    calls = []

    def get(endpoint):
        calls.append(endpoint)
        if len(calls) == 1:
            filters = "state=open&" if omit_filter else "state=open&base=main&"
            return [{"number": 1}], f'<{m.API}/repos/{REPO}/pulls?{filters}per_page=100&page=2>; rel="next"'
        return [{"number": 2}], ""

    monkeypatch.setattr(client, "get", get)
    if omit_filter:
        with pytest.raises(m.Unknown, match="untrusted pagination link"):
            client.pages("pulls?state=open&base=main")
        assert calls == ["pulls?state=open&base=main&per_page=100&page=1"]
    else:
        assert client.pages("pulls?state=open&base=main") == [{"number": 1}, {"number": 2}]
        assert calls == [
            "pulls?state=open&base=main&per_page=100&page=1",
            "pulls?state=open&base=main&per_page=100&page=2",
        ]


@pytest.mark.parametrize("scope", ["fetch", "push"])
@pytest.mark.parametrize(
    "url",
    [
        f"https://github.com/{REPO}",
        f"http://github.com/{REPO}.git",
        f"https://user@github.com/{REPO}.git",
        f"https://github.com:443/{REPO}.git",
        f"https://github.com/{REPO}.git?query",
        f"https://github.com/{REPO}.git#fragment",
        f"https://elsewhere.test/{REPO}.git",
        "https://github.com/someone/else.git",
        f"https://github.com/{REPO}.git\nhttps://github.com/{REPO}.git",
    ],
)
def test_source_exact_fetch_and_push_guards_remain(api, monkeypatch, scope, url):
    original = m.git

    def git(*args):
        if args[0] == "remote" and ("--push" in args) == (scope == "push"):
            return url + "\n"
        return original(*args)

    monkeypatch.setattr(m, "git", git)
    monkeypatch.setattr(m, "delete", lambda _: pytest.fail("untrusted origin allowed deletion"))
    report = m.cleanup(api, NOW)
    assert report["deleted"] == []
    assert report["failures"] == [{"reason": "untrusted origin URL"}]


def test_workflow_default_source_shared_entrypoint_and_permissions():
    workflow = yaml.safe_load((ROOT / ".github/workflows/stale-branch-cleanup.yml").read_text())
    triggers = workflow.get("on", workflow.get(True))
    assert set(triggers) == {"schedule", "workflow_dispatch"}
    assert triggers["schedule"] == [{"cron": "43 4 * * *"}]
    assert workflow["permissions"] == {}
    assert workflow["concurrency"]["cancel-in-progress"] is False
    job = workflow["jobs"]["cleanup"]
    assert job["if"] == "github.ref == format('refs/heads/{0}', github.event.repository.default_branch)"
    assert job["permissions"] == {"contents": "write", "pull-requests": "read"}
    checkout = job["steps"][0]
    assert checkout["with"]["ref"] == "${{ github.sha }}"
    assert checkout["with"]["persist-credentials"] is False
    invocations = [step for step in job["steps"] if "run" in step]
    assert len(invocations) == 1
    assert invocations[0]["run"].splitlines() == [
        'git remote set-url origin "https://github.com/$REPO.git"',
        'git remote set-url --push origin "https://github.com/$REPO.git"',
        'python -m scripts.hygiene.remote_branch_cleanup --repo "$REPO"',
    ]


def test_workflow_sparse_checkout_can_execute_module(tmp_path):
    workflow = yaml.safe_load((ROOT / ".github/workflows/stale-branch-cleanup.yml").read_text())
    paths = workflow["jobs"]["cleanup"]["steps"][0]["with"]["sparse-checkout"].splitlines()
    for path in paths:
        destination = tmp_path / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / path).read_bytes())
    result = subprocess.run(
        [sys.executable, "-m", "scripts.hygiene.remote_branch_cleanup", "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "48 hours" in result.stdout
