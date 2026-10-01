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
        # Shim pushes build the real public-repository client; it must fail closed, never reach GitHub.
        AGENT_REAL_GH=os.devnull,
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


def _fingerprint(sandbox):
    """The cache fingerprint a shim push in sandbox writes: its matcher and its (copied, identical) scanning code."""
    return f"{gate.matcher_fingerprint(sandbox.tooling)} {git_push.code_digest()}"


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
        [REAL_GIT, "push", "origin", "HEAD:refs/heads/feature"],
        execute=lambda path, argv, env: executed.append(argv),
        public_repository=FakePublic(None, fail=True),
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
    assert (
        "OPSEC: push scan: 2 commit message(s) scanned, 0 skipped as already scanned clean here, 0 hit(s)"
        in first.stderr
    )
    before = push_sandbox.remote_refs()
    sha = push_sandbox.commit("subject " + TOKEN)
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert_blocked(result, push_sandbox, before, f"commit[{sha[:12]}].message")
    assert "1 commit message(s) scanned, 2 skipped as already scanned clean here, 0 hit(s)" in result.stderr


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
    header = f"lu-push-scan-clean 2 {_fingerprint(push_sandbox)}\n"
    content = {
        "valid": f"{header}{sha}\n",
        "garbage": f"{header}{sha}\nnot-a-commit\n",
        "partial": f"{header}{sha}\n{sha[:20]}",
        "foreign": f"lu-push-scan-clean 2 {'f' * 64} {git_push.code_digest()}\n{sha}\n",
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


# --- Round 4: hits already public in the canonical repository are excused ---

PUBLIC_CACHE = Path(".git/lu-push-scan-public")


class FakePublic:
    """The canonical public repository client: a default-branch head and the commits it contains."""

    def __init__(self, head, public=(), *, fail=False):
        self.head, self.public, self.fail = head, set(public), fail
        self.calls = 0
        self.asked: list[str] = []

    def default_head(self):
        if self.fail:
            pytest.fail("the public repository must not be asked")
        self.calls += 1
        return self.head

    def contains(self, head, sha):
        self.calls += 1
        self.asked.append(sha)
        return sha in self.public


def run_main(sandbox, monkeypatch, client, *args, **extra):
    """git_push.main in process with the synthetic matcher and the given public-repository client."""
    monkeypatch.setattr(gate, "catalog", lambda: CATALOG)
    monkeypatch.setattr(gate, "private_tooling", lambda: sandbox.tooling)
    monkeypatch.setattr(gate, "primary_root", lambda cwd=None: sandbox.root)
    monkeypatch.chdir(sandbox.work)
    monkeypatch.setattr(os, "environ", _env(**extra))
    executed = []
    status = git_push.main(
        [REAL_GIT, *(args or ("push", "origin", "HEAD:refs/heads/feature"))],
        execute=lambda path, argv, env: executed.append(argv),
        public_repository=client,
    )
    return status, executed


def test_hit_already_in_public_main_is_excused_and_the_push_proceeds(push_sandbox, monkeypatch, capfd):
    hit = push_sandbox.commit("published subject " + TOKEN)
    public_head = push_sandbox.commit("published clean")
    push_sandbox.commit("new clean work")
    client = FakePublic(public_head)
    status, executed = run_main(push_sandbox, monkeypatch, client)
    err = capfd.readouterr().err
    assert status == 0 and executed, err
    assert "1 hit(s) excused as already public (1 public repository call(s))" in err
    assert "OPSEC blocked" not in err and TOKEN not in err and hit[:12] not in err


def test_hit_excused_by_compare_when_the_public_head_is_not_local(push_sandbox, monkeypatch, capfd):
    hit = push_sandbox.commit("published subject " + TOKEN)
    push_sandbox.commit("new clean work")
    client = FakePublic("e" * 40, public={hit})
    status, executed = run_main(push_sandbox, monkeypatch, client)
    assert status == 0 and executed, capfd.readouterr().err
    assert client.asked == [hit] and client.calls == 2


@pytest.mark.parametrize("head_is_local", [True, False])
def test_hit_not_in_public_main_is_refused(push_sandbox, monkeypatch, capfd, head_is_local):
    base = _git(push_sandbox.work, "rev-parse", "HEAD")
    hit = push_sandbox.commit("subject " + TOKEN)
    client = FakePublic(base if head_is_local else "e" * 40)
    status, executed = run_main(push_sandbox, monkeypatch, client)
    err = capfd.readouterr().err
    assert status == 2 and not executed
    assert f"OPSEC blocked: rule=synthetic-rule class=1 field=commit[{hit[:12]}].message line=1" in err
    assert "0 hit(s) excused" in err and TOKEN not in err


def test_excused_hits_are_cached_as_public_and_never_as_clean(push_sandbox, monkeypatch, capfd):
    hit = push_sandbox.commit("published subject " + TOKEN)
    status, _ = run_main(push_sandbox, monkeypatch, FakePublic(hit))
    assert status == 0, capfd.readouterr().err
    clean = (push_sandbox.work / CACHE).read_text().splitlines()
    public = (push_sandbox.work / PUBLIC_CACHE).read_text().splitlines()
    assert public == [f"lu-push-scan-public 2 {_fingerprint(push_sandbox)}", hit]
    assert hit not in clean and len(clean) == 2  # Header and the clean base commit.
    second = FakePublic(None, fail=True)
    status, executed = run_main(push_sandbox, monkeypatch, second, "push", "origin", "HEAD:refs/heads/other")
    err = capfd.readouterr().err
    assert status == 0 and executed and second.calls == 0, err
    assert "0 commit message(s) scanned, 1 skipped as already scanned clean here, 1 hit(s) excused" in err
    assert "(0 public repository call(s))" in err


def test_a_lost_clean_cache_is_rebuilt_beside_the_public_cache(push_sandbox, monkeypatch, capfd):
    base = _git(push_sandbox.work, "rev-parse", "HEAD")
    hit = push_sandbox.commit("published subject " + TOKEN)
    assert run_main(push_sandbox, monkeypatch, FakePublic(hit))[0] == 0, capfd.readouterr().err
    (push_sandbox.work / CACHE).unlink()
    status, _ = run_main(push_sandbox, monkeypatch, FakePublic(None, fail=True))
    assert status == 0, capfd.readouterr().err
    assert (push_sandbox.work / CACHE).read_text().splitlines()[1:] == [base]


@pytest.mark.parametrize("head_is_local", [True, False])
def test_a_no_answer_is_never_cached(push_sandbox, monkeypatch, capfd, head_is_local):
    base = _git(push_sandbox.work, "rev-parse", "HEAD")
    push_sandbox.commit("subject " + TOKEN)
    status, _ = run_main(push_sandbox, monkeypatch, FakePublic(base if head_is_local else "e" * 40))
    assert status == 2 and not (push_sandbox.work / PUBLIC_CACHE).exists()
    again = FakePublic(base if head_is_local else "e" * 40)
    status, _ = run_main(push_sandbox, monkeypatch, again)
    assert status == 2 and again.calls >= 1, capfd.readouterr().err


@pytest.mark.parametrize("damage", ["garbage", "foreign", "unreadable"])
def test_unusable_public_cache_excuses_nothing_by_itself(push_sandbox, monkeypatch, capfd, damage):
    if damage == "unreadable" and os.geteuid() == 0:
        pytest.skip("root reads mode-000 files")
    hit = push_sandbox.commit("subject " + TOKEN)
    header = f"lu-push-scan-public 2 {_fingerprint(push_sandbox)}\n"
    path = push_sandbox.work / PUBLIC_CACHE
    path.write_text(
        {
            "garbage": f"{header}{hit}\nnot-a-commit\n",
            "foreign": f"lu-push-scan-public 2 {'f' * 64} {git_push.code_digest()}\n{hit}\n",
        }.get(damage, f"{header}{hit}\n")
    )
    if damage == "unreadable":
        path.chmod(0)
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic("e" * 40))
    err = capfd.readouterr().err
    assert status == 2 and not executed and f"field=commit[{hit[:12]}].message" in err
    assert "OPSEC: push scan public cache unusable; hit commits rechecked." in err


def test_forged_tracking_ref_and_insteadof_cannot_excuse_a_hit(push_sandbox, monkeypatch, capfd):
    """Only the canonical repository client answers; local refs and URL rewriting are not consulted."""
    base = _git(push_sandbox.work, "rev-parse", "HEAD")
    hit = push_sandbox.commit("subject " + TOKEN)
    for ref in ("refs/remotes/origin/main", "refs/remotes/origin/HEAD", "refs/heads/main"):
        _git(push_sandbox.work, "update-ref", ref, hit)
    # origin names the canonical repository; insteadOf serves it from the local remote.
    _git(push_sandbox.work, "remote", "set-url", "origin", "https://github.com/unit/public.git")
    _git(push_sandbox.work, "config", f"url.{push_sandbox.remote}.insteadOf", "https://github.com/unit/public.git")
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(base))
    assert status == 2 and not executed and f"field=commit[{hit[:12]}].message" in capfd.readouterr().err


@pytest.mark.parametrize("head_is_local", [True, False])
def test_many_published_hits_and_one_new_hit_refuse_only_the_new_one(push_sandbox, monkeypatch, capfd, head_is_local):
    published = [push_sandbox.commit(f"published {number} " + TOKEN) for number in range(30)]
    new = push_sandbox.commit("new subject " + TOKEN)
    client = FakePublic(published[-1] if head_is_local else "e" * 40, public=published)
    status, executed = run_main(push_sandbox, monkeypatch, client)
    err = capfd.readouterr().err
    assert status == 2 and not executed
    assert err.count("rule=synthetic-rule") == 1 and f"field=commit[{new[:12]}].message" in err
    assert "30 hit(s) excused as already public" in err
    # A remote head costs one default-head read, a no for the new hit and one yes covering all 30.
    assert client.calls == (1 if head_is_local else 3), err
    assert (push_sandbox.work / PUBLIC_CACHE).read_text().splitlines()[1:] == sorted(published)


def test_compare_calls_are_bounded(push_sandbox, monkeypatch, capfd):
    hits = [push_sandbox.commit(f"unpublished {number} " + TOKEN) for number in range(git_push.COMPARE_LIMIT + 5)]
    client = FakePublic("e" * 40)
    status, _ = run_main(push_sandbox, monkeypatch, client)
    assert status == 2 and client.calls == 1 + git_push.COMPARE_LIMIT
    assert capfd.readouterr().err.count("rule=synthetic-rule") == len(hits)


def compare_runner(compare, *, head="e" * 40, calls=None):
    """A gh transport answering the typed default-head and compare reads."""

    def run(argv, **kwargs):
        if calls is not None:
            calls.append((argv, kwargs))
        if argv[:5] == ["gh", "api", "--method", "POST", "graphql"]:
            body = {"data": {"repository": {"defaultBranchRef": {"target": {"oid": head}}}}}
            return subprocess.CompletedProcess(argv, 0, json.dumps(body), "")
        return compare(argv)

    return run


def _reply(status, body):
    return lambda argv: subprocess.CompletedProcess(
        argv, status, body if isinstance(body, str) else json.dumps(body), ""
    )


def _timeout(argv):
    raise subprocess.TimeoutExpired(argv, git_push.API_TIMEOUT)


@pytest.mark.parametrize(
    "compare",
    [
        pytest.param(_reply(1, ""), id="api-failure"),
        pytest.param(_timeout, id="timeout"),
        pytest.param(_reply(1, {"message": "Not Found", "status": "404"}), id="unknown-commit"),
        pytest.param(_reply(1, {"message": "API rate limit exceeded", "status": "403"}), id="rate-limit"),
        pytest.param(_reply(0, '{"status": "behind", "merge_base_co'), id="truncated"),
        pytest.param(_reply(0, {"status": "behind"}), id="no-merge-base"),
        pytest.param(_reply(0, {"status": "behind", "merge_base_commit": {"sha": "d" * 40}}), id="other-merge-base"),
        pytest.param(_reply(0, {"status": "maybe", "merge_base_commit": {"sha": "d" * 40}}), id="unknown-status"),
        pytest.param(_reply(0, ["behind"]), id="malformed"),
    ],
)
def test_every_failed_or_unclear_answer_refuses(push_sandbox, monkeypatch, capfd, compare):
    hit = push_sandbox.commit("subject " + TOKEN)
    calls = []
    client = git_push.CanonicalPublicRepository(
        "github.com/unit/public", _env(), runner=compare_runner(compare, calls=calls)
    )
    status, executed = run_main(push_sandbox, monkeypatch, client)
    err = capfd.readouterr().err
    assert status == 2 and not executed and f"field=commit[{hit[:12]}].message" in err
    assert not (push_sandbox.work / PUBLIC_CACHE).exists()
    assert [argv[4] for argv, _ in calls[1:]] == [f"repos/unit/public/compare/{'e' * 40}...{hit}?per_page=100"]
    assert all(kwargs["timeout"] == git_push.API_TIMEOUT for _, kwargs in calls)


@pytest.mark.parametrize(
    "head_reply",
    [
        _reply(1, ""),
        _timeout,
        _reply(0, {"data": {"repository": {"defaultBranchRef": None}}}),
        _reply(0, {"data": {"repository": {"defaultBranchRef": {"target": {"oid": "main"}}}}}),
    ],
)
def test_unreadable_public_head_refuses(push_sandbox, monkeypatch, capfd, head_reply):
    hit = push_sandbox.commit("subject " + TOKEN)
    calls = []

    def run(argv, **kwargs):
        calls.append(argv)
        return head_reply(argv)

    client = git_push.CanonicalPublicRepository("github.com/unit/public", _env(), runner=run)
    status, _ = run_main(push_sandbox, monkeypatch, client)
    assert status == 2 and f"field=commit[{hit[:12]}].message" in capfd.readouterr().err
    assert len(calls) == 1 and calls[0][:5] == [
        "gh",
        "api",
        "--method",
        "POST",
        "graphql",
    ]  # No compare without a head.


def test_real_client_excuses_on_a_well_formed_behind_answer(push_sandbox, monkeypatch, capfd):
    hit = push_sandbox.commit("published subject " + TOKEN)
    calls = []
    reply = _reply(0, _consistent(hit))
    client = git_push.CanonicalPublicRepository(
        "github.com/unit/public", _env(GH_REPO="unit/forged"), runner=compare_runner(reply, calls=calls)
    )
    status, executed = run_main(push_sandbox, monkeypatch, client)
    assert status == 0 and executed, capfd.readouterr().err
    assert calls[1][0][4] == f"repos/unit/public/compare/{'e' * 40}...{hit}?per_page=100"
    assert "LU_OPSEC_OVERRIDE" not in calls[1][1]["env"]


def test_the_default_client_names_the_catalogue_public_repository(monkeypatch):
    """Never the push URL, GH_REPO or local git configuration."""
    monkeypatch.setattr(gate, "catalog", lambda: CATALOG)
    client = git_push.CanonicalPublicRepository.from_catalog({"GH_REPO": "unit/forged", "LU_OPSEC_OVERRIDE": "x"})
    assert client.repo == "github.com/unit/public" and "LU_OPSEC_OVERRIDE" not in client.environment
    monkeypatch.setattr(gate, "catalog", lambda: {"private": CATALOG["infra-private"]})
    assert git_push.CanonicalPublicRepository.from_catalog({}) is None


def test_ref_name_hits_are_never_excused(push_sandbox, monkeypatch, capfd):
    status, _ = run_main(
        push_sandbox, monkeypatch, FakePublic(None, fail=True), "push", "origin", f"HEAD:refs/heads/x-{TOKEN}"
    )
    assert status == 2 and "field=branch[1].name" in capfd.readouterr().err


# --- Round 5: embedded tag names, whole messages, compare replies bound to the queried head ---


def _object(cwd, kind, data: bytes):
    """Write a raw object without git's format checks, as a careless or hand-made object would be."""
    return (
        subprocess.run(
            [REAL_GIT, "hash-object", "-t", kind, "--literally", "-w", "--stdin"],
            cwd=cwd,
            env=_env(),
            input=data,
            capture_output=True,
            check=True,
            timeout=30,
        )
        .stdout.decode()
        .strip()
    )


def _tag(cwd, target, kind, name, message=b"clean release\n"):
    header = f"object {target}\ntype {kind}\ntag {name}\ntagger unit <unit@example.invalid> 0 +0000\n\n"
    return _object(cwd, "tag", header.encode() + message)


def _commit(cwd, message: bytes):
    tree, parent = _git(cwd, "rev-parse", "HEAD^{tree}"), _git(cwd, "rev-parse", "HEAD")
    identity = "unit <unit@example.invalid> 0 +0000"
    header = f"tree {tree}\nparent {parent}\nauthor {identity}\ncommitter {identity}\n\n"
    return _object(cwd, "commit", header.encode() + message)


def test_annotated_tag_embedded_name_hit_is_refused_under_a_clean_alias(push_sandbox):
    before = push_sandbox.remote_refs()
    tag = _tag(push_sandbox.work, _git(push_sandbox.work, "rev-parse", "HEAD"), "commit", f"v1-{TOKEN}")
    result = push_sandbox.push("push", "origin", f"{tag}:refs/tags/clean-alias")
    assert_blocked(result, push_sandbox, before, f"tag[{tag[:12]}].tagname")


def test_nested_tag_embedded_name_hit_is_refused(push_sandbox):
    before = push_sandbox.remote_refs()
    inner = _tag(push_sandbox.work, _git(push_sandbox.work, "rev-parse", "HEAD"), "commit", f"v1-{TOKEN}")
    outer = _tag(push_sandbox.work, inner, "tag", "clean-outer")
    result = push_sandbox.push("push", "origin", f"{outer}:refs/tags/clean-alias")
    assert_blocked(result, push_sandbox, before, f"tag[{inner[:12]}].tagname")


def test_clean_embedded_tag_name_passes(push_sandbox):
    inner = _tag(push_sandbox.work, _git(push_sandbox.work, "rev-parse", "HEAD"), "commit", "v1-clean")
    outer = _tag(push_sandbox.work, inner, "tag", "clean-outer")
    result = push_sandbox.push("push", "origin", f"{outer}:refs/tags/clean-alias")
    assert result.returncode == 0, result.stderr
    assert push_sandbox.remote_refs()["refs/tags/clean-alias"] == outer


def test_embedded_tag_name_hit_is_never_excused(push_sandbox, monkeypatch, capfd):
    """A public commit excuses its own message, never the name of a tag pointing at it."""
    hit = push_sandbox.commit("published subject " + TOKEN)
    tag = _tag(push_sandbox.work, hit, "commit", f"v1-{TOKEN}")
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(hit), "push", "origin", f"{tag}:refs/tags/v1")
    err = capfd.readouterr().err
    assert status == 2 and not executed
    assert f"field=tag[{tag[:12]}].tagname" in err and f"field=commit[{hit[:12]}].message" not in err, err


def test_commit_message_hit_after_a_nul_is_refused_and_never_cached(push_sandbox):
    before = push_sandbox.remote_refs()
    sha = _commit(push_sandbox.work, b"clean subject\x00 " + TOKEN.encode() + b"\n")
    result = push_sandbox.push("push", "origin", f"{sha}:refs/heads/feature")
    assert_blocked(result, push_sandbox, before, f"commit[{sha[:12]}].message")
    cache = push_sandbox.work / CACHE
    assert not cache.exists() or sha not in cache.read_text().split()


@pytest.mark.parametrize("message", [b"clean subject\n\nclean body\n", b"clean subject\x00clean tail\n"])
def test_wholly_scanned_clean_raw_commit_is_cached(push_sandbox, message):
    sha = _commit(push_sandbox.work, message)
    result = push_sandbox.push("push", "origin", f"{sha}:refs/heads/feature")
    assert result.returncode == 0, result.stderr
    assert sha in (push_sandbox.work / CACHE).read_text().split()


def test_tag_message_hit_after_a_nul_is_refused(push_sandbox):
    before = push_sandbox.remote_refs()
    head = _git(push_sandbox.work, "rev-parse", "HEAD")
    tag = _tag(push_sandbox.work, head, "commit", "v1", b"clean release\x00 " + TOKEN.encode() + b"\n")
    result = push_sandbox.push("push", "origin", f"{tag}:refs/tags/v1")
    assert_blocked(result, push_sandbox, before, f"tag[{tag[:12]}].message")


def _consistent(hit, head="e" * 40):
    return {
        "status": "behind",
        "ahead_by": 0,
        "behind_by": 3,
        "base_commit": {"sha": head},
        "merge_base_commit": {"sha": hit},
    }


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda body, hit: body.update(base_commit={"sha": "d" * 40}), id="other-base-commit"),
        pytest.param(lambda body, hit: body.pop("base_commit"), id="no-base-commit"),
        pytest.param(lambda body, hit: body.update(base_commit="e" * 40), id="malformed-base-commit"),
        pytest.param(lambda body, hit: body.update(merge_base_commit={"sha": "d" * 40}), id="other-merge-base"),
        pytest.param(lambda body, hit: body.update(ahead_by=1), id="behind-yet-ahead"),
        pytest.param(lambda body, hit: body.update(behind_by=0), id="behind-by-nothing"),
        pytest.param(lambda body, hit: body.pop("behind_by"), id="no-behind-by"),
        pytest.param(lambda body, hit: body.update(status="identical"), id="identical-but-different"),
        pytest.param(lambda body, hit: body.update(status="identical", behind_by=0), id="identical-other-commit"),
    ],
)
def test_compare_reply_not_bound_to_the_queried_head_excuses_nothing(push_sandbox, monkeypatch, capfd, mutate):
    hit = push_sandbox.commit("subject " + TOKEN)
    body = _consistent(hit)
    mutate(body, hit)
    client = git_push.CanonicalPublicRepository(
        "github.com/unit/public", _env(), runner=compare_runner(_reply(0, body))
    )
    status, executed = run_main(push_sandbox, monkeypatch, client)
    err = capfd.readouterr().err
    assert status == 2 and not executed and f"field=commit[{hit[:12]}].message" in err
    assert not (push_sandbox.work / PUBLIC_CACHE).exists()


@pytest.mark.parametrize(
    ("head", "body"),
    [
        pytest.param("e" * 40, _consistent, id="behind"),
        pytest.param(
            None,
            lambda hit, head=None: {
                "status": "identical",
                "ahead_by": 0,
                "behind_by": 0,
                "base_commit": {"sha": hit},
                "merge_base_commit": {"sha": hit},
            },
            id="identical",
        ),
    ],
)
def test_contains_accepts_only_a_consistent_reply_about_the_queried_head(head, body):
    hit = "a" * 40
    head = head or hit
    client = git_push.CanonicalPublicRepository(
        "github.com/unit/public", _env(), runner=compare_runner(_reply(0, body(hit)), head=head)
    )
    assert client.contains(head, hit) is True
    assert client.contains("f" * 40, hit) is None  # The same reply about another head is no answer.


@pytest.mark.parametrize(
    ("raw", "fields", "expected"),
    [
        pytest.param(b"tag v1\n\nclean\x00" + TOKEN.encode(), [(b"tag", b"v1")], ["clean\x00" + TOKEN], id="nul"),
        pytest.param(
            b"tag v1\nmergetag object x\n tag continuation-is-not-a-field\n \n\nbody " + TOKEN.encode(),
            [(b"tag", b"v1"), (b"mergetag", b"object x\ntag continuation-is-not-a-field\n")],
            ["body " + TOKEN],
            id="continuation",
        ),
        pytest.param(b"\nheader-like line\n\n" + TOKEN.encode(), [], ["header-like line", "", TOKEN], id="opens-empty"),
        pytest.param(
            b"encoding ISO-8859-1\n\ncaf\xe9 " + TOKEN.encode(),
            [(b"encoding", b"ISO-8859-1")],
            ["caf� " + TOKEN, "caf\xe9 " + TOKEN],
            id="declared-latin-1",
        ),
        pytest.param(
            b"encoding UTF-16\n\nab" + TOKEN.encode(), [(b"encoding", b"UTF-16")], ["ab" + TOKEN], id="declared-utf-16"
        ),
        pytest.param(
            b"encoding no-such-codec\n\n" + TOKEN.encode(), [(b"encoding", b"no-such-codec")], [TOKEN], id="unknown"
        ),
    ],
)
def test_split_object_keeps_every_reading_of_the_whole_message(raw, fields, expected):
    found_fields, message = git_push.split_object(raw, "commit[unit]")
    assert found_fields == fields
    assert message.split("\n")[: len(expected)] == expected
    assert TOKEN in message


# --- Round 6: text embedded in mergetag headers, objects without a header/body separator ---


def _signed_tag(cwd, target, name, message="clean release\n"):
    """A tag git treats as signed: merging it embeds the whole tag object in a mergetag header."""
    armor = "-----BEGIN PGP SIGNATURE-----\n\nAAAA\n-----END PGP SIGNATURE-----\n"
    tag = _tag(cwd, target, "commit", name, (message + armor).encode())
    _git(cwd, "update-ref", f"refs/tags/{name}", tag)
    return name


def _side(sandbox, branch, message="side work"):
    """A commit on a new branch off the base, leaving the work tree on trunk."""
    work = sandbox.work
    _git(work, "checkout", "-q", "-b", branch, "trunk")
    (work / f"{branch}.txt").write_text("side\n")
    _git(work, "add", f"{branch}.txt")
    _git(work, "commit", "-q", "-m", message)
    sha = _git(work, "rev-parse", "HEAD")
    _git(work, "checkout", "-q", "trunk")
    return sha


def _merge(sandbox, *tags):
    _git(sandbox.work, "merge", "-q", "--no-ff", "-m", "clean merge", *tags)
    merge = _git(sandbox.work, "rev-parse", "HEAD")
    assert _git(sandbox.work, "cat-file", "commit", merge).count("\nmergetag ") == len(tags)
    return merge


def _cached(sandbox):
    cache = sandbox.work / CACHE
    return set(cache.read_text().split()) if cache.exists() else set()


@pytest.mark.parametrize(
    ("name", "message", "field"),
    [
        pytest.param("v1", f"clean release\n\nbody {TOKEN}\n", "message", id="embedded-message"),
        pytest.param(f"v1-{TOKEN}", "clean release\n", "tagname", id="embedded-name"),
    ],
)
def test_mergetag_hit_under_a_clean_merge_message_is_refused_and_never_cached(push_sandbox, name, message, field):
    before = push_sandbox.remote_refs()
    tag = _signed_tag(push_sandbox.work, _side(push_sandbox, "side"), name, message)
    merge = _merge(push_sandbox, tag)
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert_blocked(result, push_sandbox, before, f"commit[{merge[:12]}].mergetag[1].{field}")
    assert f"commit[{merge[:12]}].message" not in result.stderr
    assert merge not in _cached(push_sandbox)


def test_clean_signed_tag_merge_still_delivers_and_is_cached(push_sandbox):
    merge = _merge(push_sandbox, _signed_tag(push_sandbox.work, _side(push_sandbox, "side"), "v1"))
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert result.returncode == 0, result.stderr
    assert push_sandbox.remote_refs()["refs/heads/feature"] == merge
    assert merge in _cached(push_sandbox)


def test_octopus_merge_hit_in_the_second_mergetag_only_is_refused(push_sandbox):
    before = push_sandbox.remote_refs()
    first = _signed_tag(push_sandbox.work, _side(push_sandbox, "one"), "v1")
    second = _signed_tag(push_sandbox.work, _side(push_sandbox, "two"), "v2", f"clean release\n\nbody {TOKEN}\n")
    merge = _merge(push_sandbox, first, second)
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert_blocked(result, push_sandbox, before, f"commit[{merge[:12]}].mergetag[2].message")
    assert "mergetag[1]" not in result.stderr
    assert merge not in _cached(push_sandbox)


def test_mergetag_hit_in_an_already_public_merge_is_excused(push_sandbox, monkeypatch, capfd):
    """The merge commit carries the embedded tag, so a public merge has already published it."""
    merge = _merge(push_sandbox, _signed_tag(push_sandbox.work, _side(push_sandbox, "side"), f"v1-{TOKEN}"))
    push_sandbox.commit("new clean work")
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(merge))
    err = capfd.readouterr().err
    assert status == 0 and executed, err
    assert "1 hit(s) excused as already public" in err and TOKEN not in err
    assert merge not in _cached(push_sandbox)


def test_commit_without_a_header_body_separator_is_refused_and_never_cached(push_sandbox):
    before = push_sandbox.remote_refs()
    tree, parent = _git(push_sandbox.work, "rev-parse", "HEAD^{tree}"), _git(push_sandbox.work, "rev-parse", "HEAD")
    identity = "unit <unit@example.invalid> 0 +0000"
    raw = f"tree {tree}\nparent {parent}\nauthor {identity}\ncommitter {identity}\nclean subject {TOKEN}\n"
    sha = _object(push_sandbox.work, "commit", raw.encode())
    result = push_sandbox.push("push", "origin", f"{sha}:refs/heads/feature")
    assert result.returncode == 2, result.stderr
    assert f"OPSEC: commit[{sha[:12]}] has no header/body separator; push refused." in result.stderr
    assert TOKEN not in result.stderr and TOKEN not in result.stdout
    assert push_sandbox.remote_refs() == before
    assert sha not in _cached(push_sandbox)


def test_tag_without_a_header_body_separator_is_refused(push_sandbox):
    before = push_sandbox.remote_refs()
    head = _git(push_sandbox.work, "rev-parse", "HEAD")
    raw = f"object {head}\ntype commit\ntag v1\ntagger unit <unit@example.invalid> 0 +0000\nrelease {TOKEN}\n"
    tag = _object(push_sandbox.work, "tag", raw.encode())
    result = push_sandbox.push("push", "origin", f"{tag}:refs/tags/v1")
    assert result.returncode == 2, result.stderr
    assert f"OPSEC: tag[{tag[:12]}] has no header/body separator; push refused." in result.stderr
    assert TOKEN not in result.stderr and TOKEN not in result.stdout
    assert push_sandbox.remote_refs() == before


def test_mergetag_without_a_header_body_separator_is_refused(push_sandbox):
    before = push_sandbox.remote_refs()
    tree, parent = _git(push_sandbox.work, "rev-parse", "HEAD^{tree}"), _git(push_sandbox.work, "rev-parse", "HEAD")
    identity = "unit <unit@example.invalid> 0 +0000"
    raw = (
        f"tree {tree}\nparent {parent}\nauthor {identity}\ncommitter {identity}\n"
        f"mergetag object {parent}\n type commit\n tag v1\n release {TOKEN}\n\nclean merge\n"
    )
    sha = _object(push_sandbox.work, "commit", raw.encode())
    result = push_sandbox.push("push", "origin", f"{sha}:refs/heads/feature")
    assert result.returncode == 2, result.stderr
    assert f"OPSEC: commit[{sha[:12]}].mergetag[1] has no header/body separator; push refused." in result.stderr
    assert TOKEN not in result.stderr and push_sandbox.remote_refs() == before
    assert sha not in _cached(push_sandbox)


@pytest.mark.parametrize("raw", [b"tag v1\nno separator " + TOKEN.encode(), b" opening continuation\n\nbody"])
def test_split_object_refuses_text_outside_any_message(raw):
    with pytest.raises(gate.PublishBlocked) as raised:
        git_push.split_object(raw, "commit[unit]")
    assert str(raised.value).startswith("OPSEC: commit[unit] ") and TOKEN not in str(raised.value)


# --- Round 7: cache entries are bound to the scanning code that wrote them; linear unfolding ---

# Each edit reverts one round-6 fix in the sandbox copy, giving its shim an older, weaker scanner.
WEAKER_SCANNERS = {
    "mergetag": ('if key == b"mergetag"]', 'if key == b"weaker"]'),
    "separator": ("    if not separator:\n", "    if False:\n"),
}
COMMENT_ONLY = ("COMPARE_LIMIT = 20\n", "COMPARE_LIMIT = 20  # Any code change, however small.\n")


def _with_scanner(sandbox, edit=None):
    """Swap the scanner source the sandbox shim runs: one (old, new) edit, or None for the reviewed code."""
    original = (ROOT / "scripts/opsec/git_push.py").read_text()
    if edit is not None:
        assert original.count(edit[0]) == 1, edit[0]
        original = original.replace(*edit)
    (sandbox.root / "scripts/opsec/git_push.py").write_text(original)


def _trusted(sandbox, name=git_push.CACHE_NAME):
    """Ids the reviewed scanner would take from a cache file."""
    ids, _ = git_push.CleanCache(sandbox.work / ".git", _fingerprint(sandbox), name).read()
    return ids


def _mergetag_hit(sandbox):
    return _merge(sandbox, _signed_tag(sandbox.work, _side(sandbox, "side"), f"v1-{TOKEN}"))


def _unseparated_hit(sandbox):
    tree, parent = _git(sandbox.work, "rev-parse", "HEAD^{tree}"), _git(sandbox.work, "rev-parse", "HEAD")
    identity = "unit <unit@example.invalid> 0 +0000"
    raw = f"tree {tree}\nparent {parent}\nauthor {identity}\ncommitter {identity}\nclean subject {TOKEN}\n"
    return _object(sandbox.work, "commit", raw.encode())


@pytest.mark.parametrize("weakness", sorted(WEAKER_SCANNERS))
def test_a_commit_an_older_scanner_cached_clean_is_rescanned_and_refused(push_sandbox, weakness):
    """The review reproduction: an older scanner caches the hit clean, then the reviewed scanner is swapped in."""
    sha = _mergetag_hit(push_sandbox) if weakness == "mergetag" else _unseparated_hit(push_sandbox)
    _with_scanner(push_sandbox, WEAKER_SCANNERS[weakness])
    older = push_sandbox.push("push", "origin", f"{sha}:refs/heads/older")
    assert older.returncode == 0 and sha in _cached(push_sandbox), older.stderr
    _with_scanner(push_sandbox)
    before = push_sandbox.remote_refs()
    result = push_sandbox.push("push", "origin", f"{sha}:refs/heads/feature")
    assert "OPSEC: push scan cache unusable; every reachable commit scanned." in result.stderr
    if weakness == "mergetag":
        assert_blocked(result, push_sandbox, before, f"commit[{sha[:12]}].mergetag[1].tagname")
    else:
        assert result.returncode == 2, result.stderr
        assert f"OPSEC: commit[{sha[:12]}] has no header/body separator; push refused." in result.stderr
        assert TOKEN not in result.stderr and push_sandbox.remote_refs() == before
    assert sha not in _trusted(push_sandbox)


def test_unchanged_scanning_code_reuses_its_cache_and_any_change_rescans(push_sandbox):
    push_sandbox.commit("clean one")
    first = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert first.returncode == 0 and "2 commit message(s) scanned, 0 skipped" in first.stderr, first.stderr
    second = push_sandbox.push("push", "origin", "HEAD:refs/heads/other")
    assert second.returncode == 0 and "0 commit message(s) scanned, 2 skipped" in second.stderr, second.stderr
    assert "unusable" not in second.stderr
    _with_scanner(push_sandbox, COMMENT_ONLY)
    third = push_sandbox.push("push", "origin", "HEAD:refs/heads/third")
    assert third.returncode == 0 and "2 commit message(s) scanned, 0 skipped" in third.stderr, third.stderr
    assert "OPSEC: push scan cache unusable; every reachable commit scanned." in third.stderr
    fourth = push_sandbox.push("push", "origin", "HEAD:refs/heads/fourth")
    assert "0 commit message(s) scanned, 2 skipped" in fourth.stderr, fourth.stderr


def test_a_public_excuse_recorded_by_other_scanning_code_is_rechecked(push_sandbox, monkeypatch, capfd):
    hit = push_sandbox.commit("published subject " + TOKEN)
    assert run_main(push_sandbox, monkeypatch, FakePublic(hit))[0] == 0, capfd.readouterr().err
    assert (push_sandbox.work / PUBLIC_CACHE).read_text().split()[-1] == hit
    # The shim's own client never answers (no gh), so only the cache can excuse the hit.
    same = push_sandbox.push("push", "origin", "HEAD:refs/heads/same")
    assert same.returncode == 0, same.stderr
    assert "1 hit(s) excused as already public (0 public repository call(s))" in same.stderr
    _with_scanner(push_sandbox, COMMENT_ONLY)
    before = push_sandbox.remote_refs()
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert_blocked(result, push_sandbox, before, f"commit[{hit[:12]}].message")
    assert "OPSEC: push scan public cache unusable; hit commits rechecked." in result.stderr


@pytest.mark.parametrize("code", ["readable", "missing", "unreadable"])
def test_unreadable_scanning_code_never_reuses_either_cache(push_sandbox, monkeypatch, capfd, tmp_path, code):
    if code == "unreadable" and os.geteuid() == 0:
        pytest.skip("root reads mode-000 files")
    base = _git(push_sandbox.work, "rev-parse", "HEAD")
    excused = push_sandbox.commit("published subject " + TOKEN)
    cached = push_sandbox.commit("subject " + TOKEN)
    fingerprint = _fingerprint(push_sandbox)
    assert git_push.CleanCache(push_sandbox.work / ".git", fingerprint).record([base, cached], full=True)
    public = git_push.CleanCache(push_sandbox.work / ".git", fingerprint, git_push.PUBLIC_CACHE_NAME)
    assert public.record([excused], full=True)
    files = {path: path.read_bytes() for path in (push_sandbox.work / CACHE, push_sandbox.work / PUBLIC_CACHE)}
    if code != "readable":
        extra = tmp_path / "scanner-part.py"
        if code == "unreadable":
            extra.write_text("# part of the scan\n")
            extra.chmod(0)
        monkeypatch.setattr(git_push, "SCAN_SOURCES", (*git_push.SCAN_SOURCES, extra))
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic("e" * 40))
    err = capfd.readouterr().err
    if code == "readable":  # Positive control: while the code is readable both cached entries are honoured.
        assert status == 0 and executed, err
        return
    assert status == 2 and not executed, err
    assert "OPSEC: push scan code unreadable; caches unused." in err
    assert "push scan cache unusable" in err and "push scan public cache unusable" in err
    assert f"field=commit[{cached[:12]}].message" in err and TOKEN not in err
    assert {path: path.read_bytes() for path in files} == files  # Never rewritten without a fingerprint.


def _unfold_seconds(size, repeats=5):
    """Best time to split a commit whose mergetag header continues over size bytes of 256-byte lines."""
    line = b" " + b"x" * 255
    raw = b"tree 0\nmergetag object 0" + (b"\n" + line) * (size // 256) + b"\n\nclean\n"
    best = float("inf")
    for _ in range(repeats):
        started = time.perf_counter()
        fields, _ = git_push.split_object(raw, "commit[unit]")
        best = min(best, time.perf_counter() - started)
    assert len(fields[1][1]) == len(b"object 0") + (size // 256) * 256
    return best


def test_continuation_unfolding_is_linear_in_the_header_size():
    """Four times the continuation costs about four times as long (quadratic unfolding costs sixteen)."""
    small, large = _unfold_seconds(512 << 10), _unfold_seconds(2 << 20)
    assert large < 8 * small, (small, large)
    assert _unfold_seconds(8 << 20, repeats=1) < 5  # Generous: quadratic unfolding took over 25 s here.
