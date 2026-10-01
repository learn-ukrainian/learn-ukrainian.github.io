"""git push publication scan through the agent shim (#9339); synthetic data, local bare remotes only."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

from scripts.opsec import git_push
from scripts.opsec import prepublish as gate
from tests.opsec_fixtures import CATALOG, ROOT, TOKEN, make_tooling, synthetic_rules

REAL_GIT = shutil.which("git", path=os.defpath)
pytestmark = pytest.mark.skipif(REAL_GIT is None, reason="git unavailable")


def _env(**extra):
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "PRE_COMMIT", "LU_OPSEC", "PYTHON"))}
    env.update(
        PATH=os.pathsep.join([str(Path(REAL_GIT).parent), os.defpath]),
        AGENT_REAL_GIT=REAL_GIT,
        AGENT_NO_MERGE="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
    )
    env.update(extra)
    return env


def _git(cwd, *args, **kwargs):
    return subprocess.run(
        [REAL_GIT, *args], cwd=cwd, env=_env(), check=True, capture_output=True, text=True, timeout=30, **kwargs
    ).stdout.strip()


@pytest.fixture
def push_sandbox(tmp_path):
    """A shim copy with synthetic tooling, a work repository and a bare local (public) remote."""
    root = tmp_path / "public-fixture"
    (root / "scripts/agent_runtime/shims").mkdir(parents=True)
    (root / "scripts/__init__.py").write_text("")
    shutil.copytree(ROOT / "scripts/opsec", root / "scripts/opsec", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(ROOT / "scripts/agent_runtime/shims/git", root / "scripts/agent_runtime/shims/git")
    (root / "scripts/config").mkdir()
    (root / "scripts/config/fleet_repos.yaml").write_text(json.dumps({"repos": CATALOG}))
    (root / ".venv").symlink_to(Path(sys.executable).parent.parent, target_is_directory=True)
    _git(tmp_path, "init", "-q", str(root))
    tooling = make_tooling(tmp_path / "private-fixture/tools/public_opsec_scan")
    remote = tmp_path / "remote.git"
    _git(tmp_path, "init", "-q", "--bare", str(remote))
    work = tmp_path / "work"
    _git(tmp_path, "init", "-q", "-b", "trunk", str(work))
    _git(work, "config", "user.email", "unit@example.invalid")
    _git(work, "config", "user.name", "unit")
    (work / "file.txt").write_text("clean\n")
    _git(work, "add", "file.txt")
    _git(work, "commit", "-q", "-m", "clean base")
    _git(work, "remote", "add", "origin", str(remote))
    _git(work, "push", "-q", "origin", "trunk")

    class Sandbox:
        shim = root / "scripts/agent_runtime/shims/git"

        def __init__(self):
            self.root, self.tooling, self.remote, self.work = root, tooling, remote, work

        def commit(self, message):
            (work / "file.txt").write_text((work / "file.txt").read_text() + "x\n")
            _git(work, "commit", "-q", "-am", message)
            return _git(work, "rev-parse", "HEAD")

        def push(self, *args, cwd=None, **extra):
            return subprocess.run(
                [str(self.shim), *args],
                cwd=cwd or work,
                env=_env(**extra),
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )

        def remote_refs(self):
            listing = _git(remote, "for-each-ref", "--format=%(refname) %(objectname)")
            return dict(line.split() for line in listing.splitlines())

    return Sandbox()


def assert_blocked(result, sandbox, before, field):
    assert result.returncode == 2, result.stderr
    assert "OPSEC blocked: rule=synthetic-rule" in result.stderr and f"field={field}" in result.stderr
    assert TOKEN not in result.stderr and TOKEN not in result.stdout
    assert sandbox.remote_refs() == before


def test_commit_message_hit_is_refused_with_nothing_sent(push_sandbox):
    before = push_sandbox.remote_refs()
    sha = push_sandbox.commit("clean subject\n\nbody " + TOKEN)
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert_blocked(result, push_sandbox, before, f"commit[{sha[:12]}].message")
    assert "line=3" in result.stderr


def test_branch_name_hit_is_refused_with_nothing_sent(push_sandbox):
    before = push_sandbox.remote_refs()
    push_sandbox.commit("clean")
    result = push_sandbox.push("push", "origin", f"HEAD:refs/heads/feature-{TOKEN}")
    assert_blocked(result, push_sandbox, before, "branch[1].name")


def test_lightweight_tag_name_hit_is_refused_with_nothing_sent(push_sandbox):
    before = push_sandbox.remote_refs()
    _git(push_sandbox.work, "tag", f"v1-{TOKEN}")
    result = push_sandbox.push("push", "origin", "--tags")
    assert_blocked(result, push_sandbox, before, "tag[1].name")


def test_annotated_tag_message_hit_is_refused_with_nothing_sent(push_sandbox):
    before = push_sandbox.remote_refs()
    _git(push_sandbox.work, "tag", "-a", "v1", "-m", "release " + TOKEN)
    tag = _git(push_sandbox.work, "rev-parse", "v1")
    result = push_sandbox.push("push", "origin", "v1")
    assert_blocked(result, push_sandbox, before, f"tag[{tag[:12]}].message")


@pytest.mark.parametrize(
    "args",
    [
        ("push", "-q", "origin", "HEAD:refs/heads/feature"),
        ("push", "--quiet", "origin", "--", "HEAD:refs/heads/feature"),
        ("-c", "push.default=simple", "push", "-fu", "origin", "HEAD:refs/heads/feature"),
    ],
)
def test_quiet_and_global_option_forms_are_still_scanned(push_sandbox, args):
    before = push_sandbox.remote_refs()
    push_sandbox.commit("subject " + TOKEN)
    result = push_sandbox.push(*args)
    assert result.returncode == 2 and "OPSEC blocked" in result.stderr, result.stderr
    assert push_sandbox.remote_refs() == before


def test_directory_option_form_is_scanned(push_sandbox, tmp_path):
    before = push_sandbox.remote_refs()
    push_sandbox.commit("subject " + TOKEN)
    result = push_sandbox.push("-C", str(push_sandbox.work), "push", "origin", "HEAD:refs/heads/feature", cwd=tmp_path)
    assert result.returncode == 2 and "OPSEC blocked" in result.stderr, result.stderr
    assert push_sandbox.remote_refs() == before


def test_clean_push_delivers_unchanged(push_sandbox):
    sha = push_sandbox.commit("clean subject\n\nclean body")
    _git(push_sandbox.work, "tag", "-a", "v1", "-m", "clean release")
    tag = _git(push_sandbox.work, "rev-parse", "v1")
    started = time.perf_counter()
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature", "v1")
    elapsed = time.perf_counter() - started
    assert result.returncode == 0, result.stderr
    refs = push_sandbox.remote_refs()
    assert refs["refs/heads/feature"] == sha and refs["refs/tags/v1"] == tag
    print(f"clean shim push: {elapsed:.3f}s")


def test_history_the_destination_already_has_is_still_scanned(push_sandbox):
    """What the destination advertises is no evidence; only this machine's clean scans skip commits."""
    old = push_sandbox.commit("old " + TOKEN)
    _git(push_sandbox.work, "push", "-q", "origin", "trunk")  # Pushed without the scan.
    before = push_sandbox.remote_refs()
    push_sandbox.commit("clean follow-up")
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert_blocked(result, push_sandbox, before, f"commit[{old[:12]}].message")


def test_deletion_publishes_no_text_and_needs_no_matcher(push_sandbox):
    _git(push_sandbox.work, "push", "-q", "origin", f"trunk:refs/heads/feature-{TOKEN}")
    shutil.rmtree(push_sandbox.tooling)
    result = push_sandbox.push("push", "origin", f":refs/heads/feature-{TOKEN}")
    assert result.returncode == 0, result.stderr
    assert f"refs/heads/feature-{TOKEN}" not in push_sandbox.remote_refs()


def test_missing_matcher_fails_closed(push_sandbox):
    before = push_sandbox.remote_refs()
    push_sandbox.commit("clean")
    shutil.rmtree(push_sandbox.tooling)
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert result.returncode == 2 and "unavailable" in result.stderr, result.stderr
    assert push_sandbox.remote_refs() == before


def test_failed_preview_refuses_without_sending(push_sandbox, tmp_path):
    result = push_sandbox.push("push", str(tmp_path / "absent.git"), "HEAD:refs/heads/feature")
    assert result.returncode == 2 and "push preview failed" in result.stderr


def test_failed_preview_output_never_replays_git_text(push_sandbox):
    """git names the bad source ref in its error; the refusal must not repeat it."""
    before = push_sandbox.remote_refs()
    result = push_sandbox.push("push", "origin", f"refs/heads/absent-{TOKEN}:refs/heads/feature")
    assert result.returncode == 2 and "OPSEC: push preview failed (exit 1); push refused." in result.stderr
    for part in TOKEN.split("-"):
        assert part not in result.stderr and part not in result.stdout
    assert push_sandbox.remote_refs() == before


def test_new_destination_url_is_scanned_despite_old_tracking_refs(push_sandbox, tmp_path):
    """Tracking refs from a previous URL are no evidence of what the new destination has."""
    sha = push_sandbox.commit("subject " + TOKEN)
    _git(push_sandbox.work, "push", "-q", "origin", "trunk")  # Tracking ref now covers the hit.
    fresh = tmp_path / "fresh.git"
    _git(tmp_path, "init", "-q", "--bare", str(fresh))
    _git(push_sandbox.work, "remote", "set-url", "origin", str(fresh))
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert result.returncode == 2 and f"field=commit[{sha[:12]}].message" in result.stderr, result.stderr
    assert _git(fresh, "for-each-ref") == ""


def test_forged_tracking_ref_does_not_suppress_the_scan(push_sandbox):
    before = push_sandbox.remote_refs()
    sha = push_sandbox.commit("subject " + TOKEN)
    _git(push_sandbox.work, "update-ref", "refs/remotes/origin/forged", sha)
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert_blocked(result, push_sandbox, before, f"commit[{sha[:12]}].message")


def test_incremental_push_enumerates_only_commits_not_yet_scanned_clean(push_sandbox, monkeypatch):
    for number in range(4):
        push_sandbox.commit(f"published {number}")
    first = push_sandbox.push("push", "origin", "trunk")
    assert first.returncode == 0 and "5 commit message(s) scanned, 0 skipped" in first.stderr, first.stderr
    new = [push_sandbox.commit(f"new {number}") for number in range(2)]
    captured = []
    monkeypatch.setattr(gate, "check_texts", lambda label, texts, **kw: captured.append(kw["field_names"]) or set())
    fingerprint = gate.matcher_fingerprint(push_sandbox.tooling)  # The key the shim push cached under.
    monkeypatch.setattr(gate, "matcher_fingerprint", lambda: fingerprint)
    monkeypatch.chdir(push_sandbox.work)
    git_push.scan_push(REAL_GIT, ["push", "origin", "HEAD:refs/heads/feature"], _env())
    commits = [name for name in captured[0] if name.startswith("commit[")]
    assert sorted(commits) == sorted(f"commit[{sha[:12]}].message" for sha in new)


@pytest.mark.parametrize("extra", [(), ("-c", "core.useReplaceRefs=true")])
def test_replacement_object_does_not_hide_the_sent_commit(push_sandbox, extra):
    """git replace changes what readers see but not what the pack sends; scan the sent object."""
    before = push_sandbox.remote_refs()
    sha = push_sandbox.commit("subject " + TOKEN)
    tree, parent = _git(push_sandbox.work, "rev-parse", "HEAD^{tree}", "HEAD^").split()
    clean = _git(push_sandbox.work, "commit-tree", tree, "-p", parent, "-m", "clean replacement")
    _git(push_sandbox.work, "replace", sha, clean)
    result = push_sandbox.push(*extra, "push", "origin", "HEAD:refs/heads/feature")
    assert_blocked(result, push_sandbox, before, f"commit[{sha[:12]}].message")


FAKE_SSH = """#!/bin/sh
# Serve an ssh git URL from a local directory: the last argument is the remote command.
for last; do :; done
command=${last%% *}; path=${last#* }; path=${path#\\'}; path=${path%\\'}
exec git "${command#git-}" "$FAKE_SSH_ROOT/${path#/}"
"""


@pytest.fixture
def ssh_sandbox(push_sandbox, tmp_path):
    """Hosted-looking ssh URLs served from local bare repositories by a fake ssh."""
    served = tmp_path / "ssh-root"
    for name in ("private", "public"):
        _git(tmp_path, "init", "-q", "--bare", str(served / "unit" / f"{name}.git"))
    ssh = tmp_path / "fake-ssh"
    ssh.write_text(FAKE_SSH)
    ssh.chmod(0o755)
    push_sandbox.ssh_env = {"GIT_SSH_COMMAND": str(ssh), "GIT_SSH_VARIANT": "ssh", "FAKE_SSH_ROOT": str(served)}
    push_sandbox.served = served
    return push_sandbox


@pytest.mark.parametrize(
    "url", ["git@github.com:unit/private.git", "ssh://git@github.com/unit/private.git", "github.com:unit/private"]
)
@pytest.mark.parametrize("by_name", [False, True])
def test_private_ssh_remote_is_neither_blocked_nor_scanned(ssh_sandbox, url, by_name):
    sha = ssh_sandbox.commit("subject " + TOKEN)
    shutil.rmtree(ssh_sandbox.tooling)  # A scan would fail closed without the matcher.
    if by_name:
        _git(ssh_sandbox.work, "remote", "add", "hosted", url)
    result = ssh_sandbox.push("push", "hosted" if by_name else url, "HEAD:refs/heads/feature", **ssh_sandbox.ssh_env)
    assert result.returncode == 0, result.stderr
    assert _git(ssh_sandbox.served / "unit/private.git", "rev-parse", "refs/heads/feature") == sha


@pytest.mark.parametrize("url", ["git@github.com:unit/public.git", "ssh://git@github.com/unit/public.git"])
def test_public_ssh_remote_is_scanned(ssh_sandbox, url):
    sha = ssh_sandbox.commit("subject " + TOKEN)
    result = ssh_sandbox.push("push", url, "HEAD:refs/heads/feature", **ssh_sandbox.ssh_env)
    assert result.returncode == 2 and f"field=commit[{sha[:12]}].message" in result.stderr, result.stderr
    assert TOKEN not in result.stderr
    assert _git(ssh_sandbox.served / "unit/public.git", "for-each-ref") == ""


def test_public_ssh_destination_advertisement_is_not_evidence(ssh_sandbox):
    url = "git@github.com:unit/public.git"
    old = ssh_sandbox.commit("old " + TOKEN)
    subprocess.run(
        [REAL_GIT, "push", "-q", url, "trunk"],
        cwd=ssh_sandbox.work,
        env=_env(**ssh_sandbox.ssh_env),
        check=True,
        timeout=30,
    )
    ssh_sandbox.commit("clean follow-up")
    result = ssh_sandbox.push("push", url, "HEAD:refs/heads/feature", **ssh_sandbox.ssh_env)
    assert result.returncode == 2 and f"field=commit[{old[:12]}].message" in result.stderr, result.stderr
    assert _git(ssh_sandbox.served / "unit/public.git", "for-each-ref", "refs/heads/feature") == ""


def test_override_is_logged_and_single_use(push_sandbox):
    push_sandbox.commit("subject " + TOKEN)
    first = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature", LU_OPSEC_OVERRIDE="synthetic false positive")
    assert first.returncode == 0, first.stderr
    log = push_sandbox.root / "batch_state/opsec/overrides.jsonl"
    rows = [json.loads(line) for line in log.read_text().splitlines()]
    assert len(rows) == 1 and rows[0]["rule_ids"] == ["synthetic-rule"]
    assert rows[0]["reason"] == "synthetic false positive" and TOKEN not in log.read_text()
    push_sandbox.commit("second " + TOKEN)
    again = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature", LU_OPSEC_OVERRIDE="synthetic false positive")
    assert again.returncode == 2 and "override already consumed" in again.stderr


def test_private_remote_is_not_scanned(push_sandbox, monkeypatch):
    """A destination the catalogue marks private skips scanning (and needs no matcher)."""
    monkeypatch.setattr(gate, "catalog", lambda: CATALOG)
    monkeypatch.setattr(gate, "private_tooling", lambda: pytest.fail("private push must not load the matcher"))
    real_destination = git_push.destination
    remote = str(push_sandbox.remote)
    monkeypatch.setattr(
        git_push, "destination", lambda url: "github.com/unit/private" if url == remote else real_destination(url)
    )
    sha = push_sandbox.commit("subject " + TOKEN)
    monkeypatch.chdir(push_sandbox.work)
    monkeypatch.setattr(os, "environ", _env())
    executed = []
    status = git_push.main(
        [REAL_GIT, "push", "origin", "HEAD:refs/heads/feature"], execute=lambda path, argv, env: executed.append(argv)
    )
    assert status == 0 and executed == [[REAL_GIT, "push", "origin", "HEAD:refs/heads/feature"]]
    assert "refs/heads/feature" not in push_sandbox.remote_refs() and sha


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://github.com/unit/private.git", "github.com/unit/private"),
        ("https://user@github.com/unit/private", "github.com/unit/private"),
        ("git@github.com:unit/private.git", "github.com/unit/private"),
        ("ssh://git@github.com:22/unit/private.git", "github.com/unit/private"),
        ("ssh://github.com/unit/private", "github.com/unit/private"),
        ("github.com:unit/private.git", "github.com/unit/private"),
        ("git@github.com:/unit/private.git", "github.com/unit/private"),
        ("git+ssh://github.com/unit/private.git", "github.com/unit/private"),
        ("git://github.com/unit/private.git", "github.com/unit/private"),
        ("../remote.git", "unknown"),
        ("/srv/unit/remote.git", "unknown"),
        ("./unit:private.git", "unknown"),
        ("file:///srv/unit/private.git", "unknown"),
        ("helper::github.com/unit/private", "unknown"),
        ("ftp://github.com/unit/private", "unknown"),
        ("", "unknown"),
    ],
)
def test_push_url_destinations(url, expected):
    assert git_push.destination(url) == expected


@pytest.mark.parametrize(
    "argv,expected",
    [
        (["push", "origin"], ([], "push", ["origin"])),
        (["-C", "push", "push"], (["-C", "push"], "push", [])),
        (["-c", "a=b", "--no-pager", "status"], (["-c", "a=b", "--no-pager"], "status", [])),
        (["--version"], (["--version"], None, [])),
    ],
)
def test_split_command(argv, expected):
    assert git_push.split_command(argv) == expected


@pytest.mark.parametrize(
    "rest,expected_tail",
    [
        (["-q", "origin"], ["-q", "origin", "--verbose"]),
        (["-o", "--", "origin"], ["-o", "--", "origin", "--verbose"]),
        (["-fo", "x", "origin", "--", "ref"], ["-fo", "x", "origin", "--verbose", "--", "ref"]),
        (["-ofoo", "--", "ref"], ["-ofoo", "--verbose", "--", "ref"]),
    ],
)
def test_preview_overrides_quiet_before_the_refspec_separator(rest, expected_tail):
    assert git_push.preview_arguments(rest) == ["--dry-run", "--porcelain", "--no-verify", *expected_tail]


@pytest.mark.parametrize("output", ["To x\nunexpected line\nDone\n", "To x\n*\tnocolon\t[new branch]\n"])
def test_unparseable_preview_refuses(output):
    with pytest.raises(gate.PublishBlocked, match="unparseable"):
        git_push.parse_porcelain(output)


# --- Round 3: no destination evidence; local clean-commit cache; grafts and tracing disabled ---

CACHE = Path(".git/lu-push-scan-clean")


def test_forged_advertisement_does_not_suppress_the_scan(push_sandbox, tmp_path):
    """An upload-pack advertising a locally known hit commit is never consulted."""
    before = push_sandbox.remote_refs()
    sha = push_sandbox.commit("subject " + TOKEN)
    decoy = tmp_path / "decoy.git"
    _git(tmp_path, "init", "-q", "--bare", str(decoy))
    _git(push_sandbox.work, "push", "-q", str(decoy), "HEAD:refs/heads/trunk")  # The decoy advertises the hit.
    alias = str(tmp_path / "alias.git")
    _git(push_sandbox.work, "remote", "set-url", "origin", alias)
    _git(push_sandbox.work, "config", f"url.{push_sandbox.remote}.pushInsteadOf", alias)
    _git(push_sandbox.work, "config", f"url.{decoy}.insteadOf", str(push_sandbox.remote))  # Fetch-side only.
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert_blocked(result, push_sandbox, before, f"commit[{sha[:12]}].message")


@pytest.mark.parametrize("via_environment", [False, True])
def test_grafted_history_is_refused(push_sandbox, tmp_path, via_environment):
    """A graft hides a hit ancestor that the destination already holds as an unreferenced object."""
    base = _git(push_sandbox.work, "rev-parse", "HEAD")
    hit = push_sandbox.commit("subject " + TOKEN)
    clean = push_sandbox.commit("clean follow-up")
    _git(push_sandbox.work, "push", "-q", "origin", f"{hit}:refs/heads/seed")
    _git(push_sandbox.work, "push", "-q", "origin", ":refs/heads/seed")  # Object stays, ref goes.
    before = push_sandbox.remote_refs()
    graft = tmp_path / "grafts" if via_environment else push_sandbox.work / ".git/info/grafts"
    graft.parent.mkdir(exist_ok=True)
    graft.write_text(f"{clean} {base}\n")
    extra = {"GIT_GRAFT_FILE": str(graft)} if via_environment else {}
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature", **extra)
    assert result.returncode == 2 and "OPSEC: grafted history present; push refused." in result.stderr, result.stderr
    assert TOKEN not in result.stderr and push_sandbox.remote_refs() == before


def test_git_tracing_never_records_the_scan(ssh_sandbox, tmp_path, monkeypatch):
    """Caller tracing (environment or config) must not log the scan's git calls or URL userinfo."""
    url = "ssh://unit:synthetic-secret@github.com/unit/public.git"
    _git(ssh_sandbox.work, "remote", "add", "hosted", url)
    ssh_sandbox.commit("clean subject")
    logs = {
        name: tmp_path / f"{name}.log" for name in ("GIT_TRACE", "GIT_TRACE_PACKET", "GIT_TRACE2", "GIT_TRACE2_EVENT")
    }
    config = tmp_path / "trace.gitconfig"
    config.write_text(f"[trace2]\n\tperfTarget = {tmp_path / 'config-perf.log'}\n")
    environment = _env(
        **ssh_sandbox.ssh_env,
        **{name: str(path) for name, path in logs.items()},
        GIT_CONFIG_GLOBAL=str(config),
        GIT_CURL_VERBOSE="1",
    )
    monkeypatch.setattr(gate, "check_texts", lambda *args, **kwargs: set())
    monkeypatch.setattr(gate, "matcher_fingerprint", lambda *args: "0" * 64, raising=False)
    monkeypatch.chdir(ssh_sandbox.work)
    git_push.scan_push(REAL_GIT, ["push", "hosted", "HEAD:refs/heads/feature"], environment)
    written = {path.name: path.read_text() for path in [*logs.values(), tmp_path / "config-perf.log"] if path.exists()}
    assert not any("synthetic-secret" in text for text in written.values())
    assert all(text == "" for text in written.values()), sorted(written)


def test_cached_clean_commits_are_skipped_and_a_new_hit_is_refused(push_sandbox):
    push_sandbox.commit("clean one")
    first = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert first.returncode == 0, first.stderr
    assert "OPSEC: push scan: 2 commit message(s) scanned, 0 skipped as already scanned clean here." in first.stderr
    before = push_sandbox.remote_refs()
    sha = push_sandbox.commit("subject " + TOKEN)
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert_blocked(result, push_sandbox, before, f"commit[{sha[:12]}].message")
    assert "1 commit message(s) scanned, 2 skipped as already scanned clean here." in result.stderr


def test_shallow_repository_is_refused(push_sandbox, tmp_path):
    push_sandbox.commit("subject " + TOKEN)
    push_sandbox.commit("clean follow-up")
    _git(push_sandbox.work, "push", "-q", "origin", "trunk")
    shallow = tmp_path / "shallow"
    _git(tmp_path, "clone", "-q", "--depth", "1", f"file://{push_sandbox.remote}", str(shallow), "-b", "trunk")
    before = push_sandbox.remote_refs()
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature", cwd=shallow)
    assert result.returncode == 2 and "OPSEC: shallow history cannot be scanned in full" in result.stderr
    assert push_sandbox.remote_refs() == before


def test_hit_commit_is_never_cached(push_sandbox):
    base = _git(push_sandbox.work, "rev-parse", "HEAD")
    sha = push_sandbox.commit("subject " + TOKEN)
    refused = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert refused.returncode == 2 and not (push_sandbox.work / CACHE).exists()
    overridden = push_sandbox.push(
        "push", "origin", "HEAD:refs/heads/feature", LU_OPSEC_OVERRIDE="synthetic false positive"
    )
    assert overridden.returncode == 0, overridden.stderr
    cached = (push_sandbox.work / CACHE).read_text().splitlines()[1:]
    assert cached == [base]
    again = push_sandbox.push("push", "origin", "HEAD:refs/heads/other")
    assert again.returncode == 2 and f"field=commit[{sha[:12]}].message" in again.stderr, again.stderr


@pytest.mark.parametrize("damage", ["valid", "garbage", "partial", "foreign", "header-only-text", "unreadable"])
def test_unusable_cache_scans_everything(push_sandbox, damage):
    """Only a well-formed cache for the current matcher skips anything; every defect scans in full."""
    if damage == "unreadable" and os.geteuid() == 0:
        pytest.skip("root reads mode-000 files")
    sha = push_sandbox.commit("subject " + TOKEN)
    header = f"lu-push-scan-clean 1 {gate.matcher_fingerprint(push_sandbox.tooling)}\n"
    content = {
        "valid": f"{header}{sha}\n",
        "garbage": f"{header}{sha}\nnot-a-commit\n",
        "partial": f"{header}{sha}\n{sha[:20]}",
        "foreign": f"lu-push-scan-clean 1 {'f' * 64}\n{sha}\n",
        "header-only-text": f"{sha}\n",
        "unreadable": f"{header}{sha}\n",
    }[damage]
    path = push_sandbox.work / CACHE
    path.write_text(content)
    if damage == "unreadable":
        path.chmod(0)
    before = push_sandbox.remote_refs()
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    if damage == "valid":  # Positive control: the trusted cache entry is what skips the hit.
        assert result.returncode == 0, result.stderr
        return
    assert_blocked(result, push_sandbox, before, f"commit[{sha[:12]}].message")
    assert "OPSEC: push scan cache unusable; every reachable commit scanned." in result.stderr


def test_rules_update_rescans_cached_commits(push_sandbox):
    """A cache entry is only as good as the matcher that produced it."""
    sha = push_sandbox.commit("subject LATER-SENSITIVE")
    assert push_sandbox.push("push", "origin", "HEAD:refs/heads/feature").returncode == 0
    (push_sandbox.tooling / "rules.json").write_text(json.dumps(synthetic_rules(pattern="LATER-SENSITIVE")))
    before = push_sandbox.remote_refs()
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/other")
    assert result.returncode == 2 and f"field=commit[{sha[:12]}].message" in result.stderr, result.stderr
    assert "push scan cache unusable" in result.stderr and push_sandbox.remote_refs() == before


CONCURRENT_WRITER = """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from scripts.opsec.git_push import CleanCache
cache = CleanCache(Path(sys.argv[2]), "f" * 64)
writer = int(sys.argv[3])
for batch in range(25):
    if not cache.record([f"{writer:08x}{batch:04x}{item:028x}" for item in range(8)], full=True):
        raise SystemExit(1)
"""


def test_concurrent_records_append_without_corruption(tmp_path):
    writers = [
        subprocess.Popen([sys.executable, "-c", CONCURRENT_WRITER, str(ROOT), str(tmp_path), str(number)])
        for number in range(6)
    ]
    assert [writer.wait(timeout=60) for writer in writers] == [0] * 6
    ids, unusable = git_push.CleanCache(tmp_path, "f" * 64).read()
    assert not unusable and len(ids) == 6 * 25 * 8
