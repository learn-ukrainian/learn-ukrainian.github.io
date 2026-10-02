"""git push publication scan through the agent shim (#9339); synthetic data, local bare remotes only."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zlib
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
    """What the destination advertises is no evidence; only the canonical public head excludes commits."""
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


def test_only_commits_outside_the_public_history_are_enumerated(push_sandbox, monkeypatch):
    published = [push_sandbox.commit(f"published {number}") for number in range(4)]
    new = [push_sandbox.commit(f"new {number}") for number in range(2)]
    captured = []
    monkeypatch.setattr(gate, "check_texts", lambda label, texts, **kw: captured.append(kw["field_names"]))
    monkeypatch.chdir(push_sandbox.work)
    client = FakePublic(published[-1])
    git_push.scan_push(REAL_GIT, ["push", "origin", "HEAD:refs/heads/feature"], _env(), public_repository=client)
    commits = [name for name in captured[0] if name.startswith("commit[")]
    assert sorted(commits) == sorted(f"commit[{sha[:12]}].message" for sha in new)
    assert client.calls == 1


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


def _private(monkeypatch, *paths):
    """Classify the given local remotes as the catalogue's private repository; a scan would fail."""
    monkeypatch.setattr(gate, "catalog", lambda: CATALOG)
    monkeypatch.setattr(gate, "private_tooling", lambda: pytest.fail("private push must not load the matcher"))
    real_destination = git_push.destination
    private = {str(path) for path in paths}
    monkeypatch.setattr(
        git_push, "destination", lambda url: "github.com/unit/private" if url in private else real_destination(url)
    )


def test_private_remote_is_not_scanned_and_gets_the_frozen_push(push_sandbox, monkeypatch, capfd):
    """A destination the catalogue marks private skips scanning (and needs no matcher), not the frozen delivery."""
    _private(monkeypatch, push_sandbox.remote)
    sha = push_sandbox.commit("subject " + TOKEN)
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(None, fail=True), deliver=True, scan=False)
    assert status == 0, capfd.readouterr().err
    assert executed[0][-3:] == ["--", str(push_sandbox.remote), f"{sha}:refs/heads/feature"]
    assert push_sandbox.remote_refs()["refs/heads/feature"] == sha


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
        (["--shallow-file", "x", "push"], (["--shallow-file", "x"], "push", [])),
    ],
)
def test_split_command(argv, expected):
    assert git_push.split_command(argv) == expected


@pytest.mark.parametrize(
    "rest,expected_tail",
    [
        (["-q", "--no-verify", "origin"], ["-q", "--no-verify", "origin", "--verify", "--verbose"]),
        (["-o", "--", "origin"], ["-o", "--", "origin", "--verify", "--verbose"]),
        (["-fo", "x", "origin", "--", "ref"], ["-fo", "x", "origin", "--verify", "--verbose", "--", "ref"]),
        (["-ofoo", "--", "ref"], ["-ofoo", "--verify", "--verbose", "--", "ref"]),
    ],
)
def test_preview_overrides_quiet_before_the_refspec_separator(rest, expected_tail):
    assert git_push.preview_arguments(rest) == ["--dry-run", "--porcelain", *expected_tail]


@pytest.mark.parametrize("output", ["To x\nunexpected line\nDone\n", "To x\n*\tnocolon\t[new branch]\n"])
def test_unparseable_preview_refuses(output):
    with pytest.raises(gate.PublishBlocked, match="unparseable"):
        git_push.parse_porcelain(output)


# --- No destination evidence; grafts, tracing and commit-graph files disabled ---


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
    monkeypatch.setattr(gate, "check_texts", lambda *args, **kwargs: None)
    monkeypatch.chdir(ssh_sandbox.work)
    git_push.scan_push(
        REAL_GIT, ["push", "hosted", "HEAD:refs/heads/feature"], environment, public_repository=FakePublic(None)
    )
    written = {path.name: path.read_text() for path in [*logs.values(), tmp_path / "config-perf.log"] if path.exists()}
    assert not any("synthetic-secret" in text for text in written.values())
    assert all(text == "" for text in written.values()), sorted(written)


# --- Shallow boundaries: refused only inside the scan set ---

SHALLOW_REFUSAL = "OPSEC: shallow boundary inside the scanned range"


def _orphan(cwd, message):
    """A parentless commit object no ref names."""
    return _git(cwd, "commit-tree", _git(cwd, "rev-parse", "HEAD^{tree}"), "-m", message)


def _shallow(work, *commits):
    """Mark commits as shallow boundaries, as a shallow clone (or a forger) would."""
    (work / ".git/shallow").write_text("".join(f"{sha}\n" for sha in commits))


def test_real_shallow_clone_with_its_boundary_pushed_is_refused(push_sandbox, tmp_path):
    push_sandbox.commit("subject " + TOKEN)
    push_sandbox.commit("clean follow-up")
    _git(push_sandbox.work, "push", "-q", "origin", "trunk")
    shallow = tmp_path / "shallow"
    _git(tmp_path, "clone", "-q", "--depth", "1", f"file://{push_sandbox.remote}", str(shallow), "-b", "trunk")
    boundary = _git(shallow, "rev-parse", "HEAD")
    before = push_sandbox.remote_refs()
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature", cwd=shallow)
    assert result.returncode == 2 and f"{SHALLOW_REFUSAL} (commit[{boundary[:12]}])" in result.stderr, result.stderr
    assert "git fetch --unshallow" in result.stderr and "git fetch --deepen=<n>" in result.stderr
    assert TOKEN not in result.stderr and push_sandbox.remote_refs() == before


def test_real_shallow_clone_with_its_boundary_inside_public_history_passes(push_sandbox, monkeypatch, tmp_path, capfd):
    """A depth-2 clone whose boundary is an ancestor of the public head; the hit behind it is public."""
    hit = push_sandbox.commit("published subject " + TOKEN)
    push_sandbox.commit("published clean one")
    public_head = push_sandbox.commit("published clean two")
    _git(push_sandbox.work, "push", "-q", "origin", "trunk")
    clone = tmp_path / "shallow"
    _git(tmp_path, "clone", "-q", "--depth", "2", f"file://{push_sandbox.remote}", str(clone), "-b", "trunk")
    for key, value in (("user.email", "unit@example.invalid"), ("user.name", "unit")):
        _git(clone, "config", key, value)
    assert (clone / ".git/shallow").read_text().split() == [_git(clone, "rev-parse", "HEAD~1")]
    (clone / "file.txt").write_text("new\n")
    _git(clone, "commit", "-q", "-am", "new clean work")
    push_sandbox.work = clone
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(public_head))
    err = capfd.readouterr().err
    assert status == 0 and executed, err
    assert "1 commit(s) scanned" in err and hit[:12] not in err and TOKEN not in err


def test_boundaries_outside_the_scan_set_do_not_refuse_a_clean_push(push_sandbox):
    """The shared repository shape: two boundary commits that are not ancestors of the pushed tip."""
    _shallow(
        push_sandbox.work, _orphan(push_sandbox.work, "unrelated one"), _orphan(push_sandbox.work, "unrelated two")
    )
    sha = push_sandbox.commit("clean subject")
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert result.returncode == 0, result.stderr
    assert "2 commit(s) scanned" in result.stderr and push_sandbox.remote_refs()["refs/heads/feature"] == sha


def test_boundary_ancestor_of_the_tip_and_not_of_the_public_head_is_refused(push_sandbox, monkeypatch, capfd):
    public_head = _git(push_sandbox.work, "rev-parse", "HEAD")
    boundary = push_sandbox.commit("clean one")
    push_sandbox.commit("clean two")
    _shallow(push_sandbox.work, boundary, _orphan(push_sandbox.work, "unrelated"))
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(public_head))
    err = capfd.readouterr().err
    assert status == 2 and not executed and f"{SHALLOW_REFUSAL} (commit[{boundary[:12]}])" in err, err


def test_boundary_inside_the_excluded_public_history_hides_only_public_history(push_sandbox, monkeypatch, capfd):
    hit = push_sandbox.commit("published subject " + TOKEN)
    boundary = push_sandbox.commit("published clean one")
    public_head = push_sandbox.commit("published clean two")
    push_sandbox.commit("new clean work")
    _shallow(push_sandbox.work, boundary)
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(public_head))
    err = capfd.readouterr().err
    assert status == 0 and executed, err
    assert "1 commit(s) scanned" in err and "OPSEC blocked" not in err
    assert hit[:12] not in err and TOKEN not in err


def test_forged_boundary_on_a_new_commit_hiding_a_hit_is_refused(push_sandbox, monkeypatch, capfd):
    public_head = _git(push_sandbox.work, "rev-parse", "HEAD")
    hit = push_sandbox.commit("subject " + TOKEN)
    forged = push_sandbox.commit("clean cover")
    tip = push_sandbox.commit("clean tip")
    _shallow(push_sandbox.work, forged)
    # Positive control: git honours the forged entry and no longer walks to the hit.
    assert _git(push_sandbox.work, "rev-list", tip, f"^{public_head}").split() == [tip, forged]
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(public_head))
    err = capfd.readouterr().err
    assert status == 2 and not executed and f"{SHALLOW_REFUSAL} (commit[{forged[:12]}])" in err, err
    assert hit[:12] not in err and TOKEN not in err


def test_forged_boundary_on_a_new_commit_is_never_delivered(push_sandbox):
    hit = push_sandbox.commit("subject " + TOKEN)
    forged = push_sandbox.commit("clean cover")
    _shallow(push_sandbox.work, forged)
    before = push_sandbox.remote_refs()
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert result.returncode == 2 and f"{SHALLOW_REFUSAL} (commit[{forged[:12]}])" in result.stderr, result.stderr
    assert hit[:12] not in result.stderr and TOKEN not in result.stderr and push_sandbox.remote_refs() == before


@pytest.mark.parametrize("forged", [["head"], ["middle"], ["base"], ["base", "middle", "head"]])
def test_forged_boundary_in_public_history_cannot_shrink_the_scan_set(push_sandbox, monkeypatch, capfd, forged):
    commits = {"base": _git(push_sandbox.work, "rev-parse", "HEAD")}
    commits["middle"] = push_sandbox.commit("published clean one")
    commits["head"] = push_sandbox.commit("published clean two")
    hit = push_sandbox.commit("new subject " + TOKEN)
    _shallow(push_sandbox.work, *(commits[name] for name in forged))
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(commits["head"]))
    err = capfd.readouterr().err
    assert status == 2 and not executed and f"field=commit[{hit[:12]}].message" in err, err
    assert TOKEN not in err


def test_forged_public_boundary_truncating_the_exclusion_scans_more(push_sandbox, monkeypatch, capfd):
    """A boundary on the public head stops the exclusion there: older public history reached another way is scanned."""
    base = _git(push_sandbox.work, "rev-parse", "HEAD")
    push_sandbox.commit("published clean one")
    public_head = push_sandbox.commit("published clean two")
    _git(push_sandbox.work, "checkout", "-q", "-b", "side", base)
    (push_sandbox.work / "side.txt").write_text("side\n")
    _git(push_sandbox.work, "add", "side.txt")
    _git(push_sandbox.work, "commit", "-q", "-m", "new subject " + TOKEN)
    hit = _git(push_sandbox.work, "rev-parse", "HEAD")
    _git(push_sandbox.work, "checkout", "-q", "trunk")
    _git(push_sandbox.work, "merge", "-q", "--no-ff", "-m", "clean merge", "side")
    _shallow(push_sandbox.work, public_head)
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(public_head))
    err = capfd.readouterr().err
    # Without the boundary the scan set is {merge, hit}; with it, base (public) joins it.
    assert status == 2 and not executed and f"field=commit[{hit[:12]}].message" in err, err
    assert "3 commit(s) scanned" in err and TOKEN not in err


@pytest.mark.parametrize(
    "content",
    ["{sha}\n\n", "{sha}\r\n", "{short}\n", "not an id\n"],
    ids=["blank-line", "crlf", "short", "text"],
)
def test_malformed_shallow_file_is_refused(push_sandbox, monkeypatch, capfd, content):
    sha = _orphan(push_sandbox.work, "unrelated")
    push_sandbox.commit("clean subject")
    (push_sandbox.work / ".git/shallow").write_text(content.format(sha=sha, short=sha[:39]))
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(None))
    err = capfd.readouterr().err
    assert status == 2 and not executed, err
    # git itself rejects some shapes in the preview; ours are the ones it would read differently.
    assert "OPSEC: shallow file malformed; push refused." in err or "OPSEC: push preview failed" in err, err


@pytest.mark.parametrize("content", ["{sha} trailing\n", "{upper}\n"], ids=["trailing-text", "uppercase"])
def test_shallow_lines_git_reads_loosely_are_refused_by_the_scan(push_sandbox, monkeypatch, capfd, content):
    """git accepts these lines and reads a boundary from them; the scan refuses rather than guess."""
    sha = _orphan(push_sandbox.work, "unrelated")
    (push_sandbox.work / ".git/shallow").write_text(content.format(sha=sha, upper=sha.upper()))
    push_sandbox.commit("clean subject")
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(None))
    err = capfd.readouterr().err
    assert status == 2 and not executed and "OPSEC: shallow file malformed; push refused." in err, err


def test_shallow_directory_is_refused_as_unreadable(push_sandbox, monkeypatch, capfd):
    (push_sandbox.work / ".git/shallow").mkdir()
    push_sandbox.commit("clean subject")
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(None))
    err = capfd.readouterr().err
    assert status == 2 and not executed and "OPSEC: shallow file unreadable; push refused." in err, err


def test_shallow_boundaries_reader(tmp_path):
    path = tmp_path / "shallow"
    assert git_push.shallow_boundaries(str(path), 40) == set()  # Not shallow.
    path.write_text("")
    assert git_push.shallow_boundaries(str(path), 40) == set()
    path.write_text(f"{'a' * 40}\n{'b' * 40}")  # git reads a last line without its newline.
    assert git_push.shallow_boundaries(str(path), 40) == {"a" * 40, "b" * 40}
    with pytest.raises(gate.PublishBlocked, match="shallow file malformed"):
        git_push.shallow_boundaries(str(path), 64)  # Ids of another object format.
    fifo = tmp_path / "fifo"
    os.mkfifo(fifo)
    with pytest.raises(gate.PublishBlocked, match="shallow file unreadable"):
        git_push.shallow_boundaries(str(fifo), 40)


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads any file")
def test_unreadable_shallow_file_is_refused(tmp_path):
    path = tmp_path / "shallow"
    path.write_text(f"{'a' * 40}\n")
    path.chmod(0)
    try:
        with pytest.raises(gate.PublishBlocked, match="shallow file unreadable"):
            git_push.shallow_boundaries(str(path), 40)
    finally:
        path.chmod(0o600)


def test_linked_worktree_reads_the_shared_shallow_file(push_sandbox, tmp_path):
    linked = tmp_path / "linked"
    _git(push_sandbox.work, "worktree", "add", "-q", "-b", "linked", str(linked))
    (linked / "file.txt").write_text("linked\n")
    _git(linked, "commit", "-q", "-am", "clean linked work")
    boundary = _git(linked, "rev-parse", "HEAD")
    _shallow(push_sandbox.work, boundary)
    assert not (linked / ".git").is_dir()
    before = push_sandbox.remote_refs()
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature", cwd=linked)
    assert result.returncode == 2 and f"{SHALLOW_REFUSAL} (commit[{boundary[:12]}])" in result.stderr, result.stderr
    assert push_sandbox.remote_refs() == before


def test_alternate_shallow_file_option_is_refused(push_sandbox):
    """git --shallow-file takes a value: it must neither hide the push subcommand nor swap the file read."""
    push_sandbox.commit("subject " + TOKEN)
    before = push_sandbox.remote_refs()
    result = push_sandbox.push("--shallow-file", os.devnull, "push", "origin", "HEAD:refs/heads/feature")
    assert result.returncode == 2 and "--shallow-file is not supported for a scanned push" in result.stderr
    assert TOKEN not in result.stderr and push_sandbox.remote_refs() == before


def test_an_overridden_hit_is_scanned_again_on_the_next_push(push_sandbox):
    sha = push_sandbox.commit("subject " + TOKEN)
    overridden = push_sandbox.push(
        "push", "origin", "HEAD:refs/heads/feature", LU_OPSEC_OVERRIDE="synthetic false positive"
    )
    assert overridden.returncode == 0, overridden.stderr
    again = push_sandbox.push("push", "origin", "HEAD:refs/heads/other")
    assert again.returncode == 2 and f"field=commit[{sha[:12]}].message" in again.stderr, again.stderr


def test_rules_update_refuses_a_commit_an_earlier_push_passed(push_sandbox):
    sha = push_sandbox.commit("subject LATER-SENSITIVE")
    assert push_sandbox.push("push", "origin", "HEAD:refs/heads/feature").returncode == 0
    (push_sandbox.tooling / "rules.json").write_text(json.dumps(synthetic_rules(pattern="LATER-SENSITIVE")))
    before = push_sandbox.remote_refs()
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/other")
    assert result.returncode == 2 and f"field=commit[{sha[:12]}].message" in result.stderr, result.stderr
    assert push_sandbox.remote_refs() == before


def _forge_commit_graph(work, child, parent):
    """Rewrite the commit-graph so child's first parent is parent, with a valid trailing checksum."""
    _git(work, "commit-graph", "write", "--reachable", "--no-progress")
    path = work / ".git/objects/info/commit-graph"
    data = bytearray(path.read_bytes())
    assert data[:4] == b"CGPH" and data[5] == 1  # Version 1 with SHA-1 ids.
    chunks = {
        bytes(data[8 + 12 * n : 12 + 12 * n]): int.from_bytes(data[12 + 12 * n : 20 + 12 * n], "big")
        for n in range(data[6])
    }
    count = int.from_bytes(data[chunks[b"OIDF"] + 255 * 4 : chunks[b"OIDF"] + 256 * 4], "big")
    ids = [bytes(data[chunks[b"OIDL"] + 20 * n : chunks[b"OIDL"] + 20 * n + 20]).hex() for n in range(count)]
    entry = chunks[b"CDAT"] + ids.index(child) * 36
    data[entry + 20 : entry + 24] = ids.index(parent).to_bytes(4, "big")
    data[-20:] = hashlib.sha1(bytes(data[:-20])).digest()
    path.chmod(0o644)
    path.write_bytes(bytes(data))


@pytest.mark.parametrize("helper", ["commit-graph", "replace"])
def test_local_parent_data_cannot_place_a_hit_inside_the_public_history(push_sandbox, monkeypatch, capfd, helper):
    """Only parents recorded in the hashed commits decide ancestry: no commit-graph or replacement object."""
    hit = push_sandbox.commit("subject " + TOKEN)
    public_head = _git(push_sandbox.work, "rev-parse", "HEAD~1")
    # Make the local view of the public head's history include the hit.
    if helper == "replace":
        tree = _git(push_sandbox.work, "rev-parse", f"{public_head}^{{tree}}")
        forged = _git(push_sandbox.work, "commit-tree", tree, "-p", hit, "-m", "clean base")
        _git(push_sandbox.work, "replace", public_head, forged)
    else:
        _forge_commit_graph(push_sandbox.work, public_head, hit)
    # Positive control: plain git, honouring the forged data, would exclude the hit.
    assert _git(push_sandbox.work, "rev-list", hit, f"^{public_head}") == ""
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(public_head))
    err = capfd.readouterr().err
    assert status == 2 and not executed and f"field=commit[{hit[:12]}].message" in err, err


# --- History already on the public default branch is excluded by its authoritative head ---


class FakePublic:
    """The canonical public repository client seam: the default-branch head it reports."""

    def __init__(self, head, *, fail=False):
        self.head, self.fail = head, fail
        self.calls = 0

    def default_head(self):
        if self.fail:
            pytest.fail("the public repository must not be asked")
        self.calls += 1
        return self.head


def run_main(sandbox, monkeypatch, client, *args, deliver=False, scan=True, **extra):
    """git_push.main in process with the synthetic matcher and the given public-repository client.

    Every push main runs is recorded; deliver=True also runs it, and the local
    bookkeeping after it, with the real git. scan=False keeps the caller's
    catalogue and matcher seams.
    """
    if scan:
        monkeypatch.setattr(gate, "catalog", lambda: CATALOG)
        monkeypatch.setattr(gate, "private_tooling", lambda: sandbox.tooling)
    monkeypatch.setattr(gate, "primary_root", lambda cwd=None: sandbox.root)
    monkeypatch.chdir(sandbox.work)
    monkeypatch.setattr(os, "environ", _env(**extra))
    executed = []

    def run(argv, **kwargs):
        if "push" in argv:
            executed.append(argv)
        if deliver:
            return subprocess.run(argv, timeout=30, **kwargs)
        return subprocess.CompletedProcess(argv, 0)

    status = git_push.main(
        [REAL_GIT, *(args or ("push", "origin", "HEAD:refs/heads/feature"))],
        execute=lambda *_: pytest.fail("a push is never run unchanged"),
        run=run,
        public_repository=client,
    )
    return status, executed


FETCH_HINT = "fetching the public default branch lets the scan skip history that is already public"


def test_hit_in_public_main_history_is_neither_refused_nor_scanned(push_sandbox, monkeypatch, capfd):
    hit = push_sandbox.commit("published subject " + TOKEN)
    public_head = push_sandbox.commit("published clean")
    push_sandbox.commit("new clean work")
    client = FakePublic(public_head)
    status, executed = run_main(push_sandbox, monkeypatch, client)
    err = capfd.readouterr().err
    assert status == 0 and executed, err
    assert "1 commit(s) scanned; public default-branch head present (1 public repository call(s))" in err
    assert "OPSEC blocked" not in err and TOKEN not in err and hit[:12] not in err


def test_new_hit_on_top_of_public_main_is_refused(push_sandbox, monkeypatch, capfd):
    public_head = _git(push_sandbox.work, "rev-parse", "HEAD")
    hit = push_sandbox.commit("subject " + TOKEN)
    client = FakePublic(public_head)
    status, executed = run_main(push_sandbox, monkeypatch, client)
    err = capfd.readouterr().err
    assert status == 2 and not executed and client.calls == 1
    assert f"OPSEC blocked: rule=synthetic-rule class=1 field=commit[{hit[:12]}].message line=1" in err
    assert TOKEN not in err and FETCH_HINT not in err


def test_many_published_hits_and_one_new_hit_refuse_only_the_new_one(push_sandbox, monkeypatch, capfd):
    published = [push_sandbox.commit(f"published {number} " + TOKEN) for number in range(30)]
    new = push_sandbox.commit("new subject " + TOKEN)
    client = FakePublic(published[-1])
    status, executed = run_main(push_sandbox, monkeypatch, client)
    err = capfd.readouterr().err
    assert status == 2 and not executed
    assert err.count("rule=synthetic-rule") == 1 and f"field=commit[{new[:12]}].message" in err
    assert "1 commit(s) scanned" in err and client.calls == 1


def test_absent_public_head_scans_all_history_and_names_the_fetch(push_sandbox, monkeypatch, capfd):
    hit = push_sandbox.commit("published subject " + TOKEN)
    push_sandbox.commit("new clean work")
    client = FakePublic("e" * 40)  # Not an object in this repository.
    status, executed = run_main(push_sandbox, monkeypatch, client)
    err = capfd.readouterr().err
    assert status == 2 and not executed and client.calls == 1
    assert f"field=commit[{hit[:12]}].message" in err and FETCH_HINT in err
    assert "3 commit(s) scanned; public default-branch head absent here" in err
    assert TOKEN not in err


def test_absent_public_head_hint_is_only_for_history_older_than_the_tips(push_sandbox, monkeypatch, capfd):
    hit = push_sandbox.commit("subject " + TOKEN)
    status, _ = run_main(push_sandbox, monkeypatch, FakePublic("e" * 40))
    err = capfd.readouterr().err
    assert status == 2 and f"field=commit[{hit[:12]}].message" in err and FETCH_HINT not in err


def test_absent_public_head_and_clean_history_passes(push_sandbox, monkeypatch, capfd):
    push_sandbox.commit("clean one")
    push_sandbox.commit("clean two")
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic("e" * 40))
    err = capfd.readouterr().err
    assert status == 0 and executed, err
    assert "3 commit(s) scanned; public default-branch head absent here (1 public repository call(s))" in err


def test_one_public_repository_call_per_push(push_sandbox, monkeypatch, capfd):
    """Several refs, tags and destinations still cost one read; a push that sends no commit costs none."""
    head = _git(push_sandbox.work, "rev-parse", "HEAD")
    push_sandbox.commit("clean one")
    _git(push_sandbox.work, "tag", "-a", "v1", "-m", "clean release")
    _git(push_sandbox.work, "remote", "set-url", "--add", "--push", "origin", str(push_sandbox.remote))
    _git(push_sandbox.work, "remote", "set-url", "--add", "--push", "origin", str(push_sandbox.remote))
    client = FakePublic(head)
    status, _ = run_main(
        push_sandbox, monkeypatch, client, "push", "origin", "HEAD:refs/heads/a", "HEAD~1:refs/heads/b", "v1"
    )
    assert status == 0 and client.calls == 1, capfd.readouterr().err
    _git(push_sandbox.work, "push", "-q", str(push_sandbox.remote), "HEAD:refs/heads/gone")
    deletion = FakePublic(None, fail=True)
    status, _ = run_main(push_sandbox, monkeypatch, deletion, "push", "origin", ":refs/heads/gone")
    assert status == 0 and deletion.calls == 0, capfd.readouterr().err


@pytest.mark.parametrize("answer", [None, "local-hit"])
def test_forged_tracking_ref_and_insteadof_cannot_exclude_a_hit(push_sandbox, monkeypatch, capfd, answer):
    """Only the canonical repository client names the public head; local refs and URL rewriting are not read."""
    base = _git(push_sandbox.work, "rev-parse", "HEAD")
    hit = push_sandbox.commit("subject " + TOKEN)
    for ref in ("refs/remotes/origin/main", "refs/remotes/origin/HEAD", "refs/heads/main"):
        _git(push_sandbox.work, "update-ref", ref, hit)
    # origin names the canonical repository; insteadOf serves it from the local remote.
    _git(push_sandbox.work, "remote", "set-url", "origin", "https://github.com/unit/public.git")
    _git(push_sandbox.work, "config", f"url.{push_sandbox.remote}.insteadOf", "https://github.com/unit/public.git")
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(base if answer else None))
    assert status == 2 and not executed and f"field=commit[{hit[:12]}].message" in capfd.readouterr().err


def test_shim_push_without_a_reachable_api_scans_in_full(push_sandbox):
    """The sandbox shim has no publisher read path and no gh, so its client answers nothing and nothing is excluded."""
    hit = push_sandbox.commit("published subject " + TOKEN)
    push_sandbox.commit("clean follow-up")
    before = push_sandbox.remote_refs()
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert_blocked(result, push_sandbox, before, f"commit[{hit[:12]}].message")
    assert "public default-branch head unavailable (1 public repository call(s))" in result.stderr


def head_runner(reply, *, calls):
    """A gh transport answering only the typed default-head read; records (argv, kwargs, document)."""

    def run(argv, **kwargs):
        assert argv[:5] == ["gh", "api", "--method", "POST", "graphql"], argv
        calls.append((argv, kwargs, json.loads(Path(argv[argv.index("--input") + 1]).read_text())))
        return reply(argv)

    return run


def _reply(status, body):
    return lambda argv: subprocess.CompletedProcess(
        argv, status, body if isinstance(body, str) else json.dumps(body), ""
    )


def _timeout(argv):
    raise subprocess.TimeoutExpired(argv, git_push.API_TIMEOUT)


def _head_body(head, *, name="unit/public", branch="main"):
    return {
        "data": {"repository": {"nameWithOwner": name, "defaultBranchRef": {"name": branch, "target": {"oid": head}}}}
    }


@pytest.mark.parametrize(
    "reply",
    [
        pytest.param(lambda head: _reply(1, ""), id="api-failure"),
        pytest.param(lambda head: _timeout, id="timeout"),
        pytest.param(lambda head: _reply(1, {"message": "Not Found", "status": "404"}), id="not-found"),
        pytest.param(lambda head: _reply(1, {"message": "API rate limit exceeded", "status": "403"}), id="rate-limit"),
        pytest.param(lambda head: _reply(0, json.dumps(_head_body(head))[:-7]), id="truncated"),
        pytest.param(lambda head: _reply(0, [head]), id="malformed"),
        pytest.param(
            lambda head: _reply(
                0, {"data": {"repository": {"nameWithOwner": "unit/public", "defaultBranchRef": None}}}
            ),
            id="no-branch",
        ),
        pytest.param(lambda head: _reply(0, _head_body(head, name="unit/forged")), id="wrong-repository"),
        pytest.param(
            lambda head: _reply(
                0, {"data": {"repository": {"defaultBranchRef": {"name": "main", "target": {"oid": head}}}}}
            ),
            id="no-repository-identity",
        ),
        pytest.param(lambda head: _reply(0, _head_body(head, branch="release")), id="wrong-branch"),
        pytest.param(lambda head: _reply(0, _head_body("main")), id="non-hex"),
        pytest.param(lambda head: _reply(0, _head_body(head.upper())), id="uppercase-hex"),
        pytest.param(lambda head: _reply(0, _head_body(head + "0" * 24)), id="long-hex"),
        pytest.param(
            lambda head: _reply(0, {**_head_body(head), "errors": [{"message": "partial"}]}), id="graphql-errors"
        ),
        pytest.param(lambda head: _reply(1, _head_body(head)), id="failed-exit"),
    ],
)
def test_every_failed_or_unbound_head_reply_excludes_nothing(push_sandbox, monkeypatch, capfd, reply):
    hit = push_sandbox.commit("published subject " + TOKEN)
    public_head = push_sandbox.commit("published clean")
    push_sandbox.commit("new clean work")
    calls = []
    client = git_push.CanonicalPublicRepository(
        "github.com/unit/public", _env(), runner=head_runner(reply(public_head), calls=calls)
    )
    status, executed = run_main(push_sandbox, monkeypatch, client)
    err = capfd.readouterr().err
    assert status == 2 and not executed and f"field=commit[{hit[:12]}].message" in err, err
    assert "public default-branch head unavailable (1 public repository call(s))" in err
    assert len(calls) == 1 and calls[0][1]["timeout"] == git_push.API_TIMEOUT


def test_real_client_excludes_on_a_bound_reply_from_the_catalogue_repository(push_sandbox, monkeypatch, capfd):
    push_sandbox.commit("published subject " + TOKEN)
    public_head = push_sandbox.commit("published clean")
    push_sandbox.commit("new clean work")
    calls = []
    client = git_push.CanonicalPublicRepository(
        "github.com/unit/public",
        _env(GH_REPO="unit/forged", LU_OPSEC_OVERRIDE="x"),
        runner=head_runner(_reply(0, _head_body(public_head, name="Unit/Public")), calls=calls),
    )
    status, executed = run_main(push_sandbox, monkeypatch, client)
    assert status == 0 and executed, capfd.readouterr().err
    ((_, kwargs, document),) = calls
    assert document["variables"] == {"owner": "unit", "name": "public"}
    assert "nameWithOwner" in document["query"] and "LU_OPSEC_OVERRIDE" not in kwargs["env"]


def test_the_default_client_names_the_catalogue_public_repository(monkeypatch):
    """Never the push URL, GH_REPO or local git configuration."""
    monkeypatch.setattr(gate, "catalog", lambda: CATALOG)
    client = git_push.CanonicalPublicRepository.from_catalog({"GH_REPO": "unit/forged", "LU_OPSEC_OVERRIDE": "x"})
    assert client.repo == "github.com/unit/public" and "LU_OPSEC_OVERRIDE" not in client.environment
    monkeypatch.setattr(gate, "catalog", lambda: {"private": CATALOG["infra-private"]})
    assert git_push.CanonicalPublicRepository.from_catalog({}) is None


def test_ref_name_hits_are_scanned_even_when_the_commit_is_public(push_sandbox, monkeypatch, capfd):
    head = _git(push_sandbox.work, "rev-parse", "HEAD")
    status, _ = run_main(push_sandbox, monkeypatch, FakePublic(head), "push", "origin", f"HEAD:refs/heads/x-{TOKEN}")
    assert status == 2 and "field=branch[1].name" in capfd.readouterr().err


STALE_CACHES = {
    "lu-push-scan-clean": "lu-push-scan-clean 2 {fingerprint}\n{sha}\n",
    "lu-push-scan-public": "lu-push-scan-public 2 {fingerprint}\n{sha}\n",
}


def _scan_files(sandbox):
    return {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in (sandbox.work / ".git").glob("lu-push-scan*")
    }


def test_no_scan_cache_is_created(push_sandbox):
    push_sandbox.commit("clean one")
    for ref in ("feature", "other"):
        result = push_sandbox.push("push", "origin", f"HEAD:refs/heads/{ref}")
        assert result.returncode == 0 and "2 commit(s) scanned" in result.stderr, result.stderr
    assert _scan_files(push_sandbox) == {}


def test_a_stale_cache_from_an_older_scanner_is_ignored_and_untouched(push_sandbox):
    sha = push_sandbox.commit("subject " + TOKEN)
    for name, content in STALE_CACHES.items():
        (push_sandbox.work / ".git" / name).write_text(content.format(fingerprint="f" * 64 + " " + "c" * 64, sha=sha))
        (push_sandbox.work / ".git" / f"{name}.lock").write_text("")
    files = _scan_files(push_sandbox)
    before = push_sandbox.remote_refs()
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert_blocked(result, push_sandbox, before, f"commit[{sha[:12]}].message")
    assert _scan_files(push_sandbox) == files


# --- Embedded tag names, whole messages ---


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


@pytest.mark.parametrize(
    ("name", "message", "field"),
    [
        pytest.param(f"v1-{TOKEN}", b"clean release\n", "tagname", id="tag-name"),
        pytest.param("v1", f"release {TOKEN}\n".encode(), "message", id="tag-message"),
    ],
)
def test_annotated_tag_on_a_public_commit_is_still_scanned(push_sandbox, monkeypatch, capfd, name, message, field):
    """A public commit excludes its own message, never the name or message of a tag pointing at it."""
    hit = push_sandbox.commit("published subject " + TOKEN)
    tag = _tag(push_sandbox.work, hit, "commit", name, message)
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(hit), "push", "origin", f"{tag}:refs/tags/v1")
    err = capfd.readouterr().err
    assert status == 2 and not executed
    assert f"field=tag[{tag[:12]}].{field}" in err and f"field=commit[{hit[:12]}].message" not in err, err
    assert "0 commit(s) scanned" in err


def test_commit_message_hit_after_a_nul_is_refused(push_sandbox):
    before = push_sandbox.remote_refs()
    sha = _commit(push_sandbox.work, b"clean subject\x00 " + TOKEN.encode() + b"\n")
    result = push_sandbox.push("push", "origin", f"{sha}:refs/heads/feature")
    assert_blocked(result, push_sandbox, before, f"commit[{sha[:12]}].message")


@pytest.mark.parametrize("message", [b"clean subject\n\nclean body\n", b"clean subject\x00clean tail\n"])
def test_wholly_scanned_clean_raw_commit_is_delivered(push_sandbox, message):
    sha = _commit(push_sandbox.work, message)
    result = push_sandbox.push("push", "origin", f"{sha}:refs/heads/feature")
    assert result.returncode == 0, result.stderr
    assert push_sandbox.remote_refs()["refs/heads/feature"] == sha


def test_tag_message_hit_after_a_nul_is_refused(push_sandbox):
    before = push_sandbox.remote_refs()
    head = _git(push_sandbox.work, "rev-parse", "HEAD")
    tag = _tag(push_sandbox.work, head, "commit", "v1", b"clean release\x00 " + TOKEN.encode() + b"\n")
    result = push_sandbox.push("push", "origin", f"{tag}:refs/tags/v1")
    assert_blocked(result, push_sandbox, before, f"tag[{tag[:12]}].message")


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


# --- Text embedded in mergetag headers, objects without a header/body separator ---


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


@pytest.mark.parametrize(
    ("name", "message", "field"),
    [
        pytest.param("v1", f"clean release\n\nbody {TOKEN}\n", "message", id="embedded-message"),
        pytest.param(f"v1-{TOKEN}", "clean release\n", "tagname", id="embedded-name"),
    ],
)
def test_mergetag_hit_under_a_clean_merge_message_is_refused(push_sandbox, name, message, field):
    before = push_sandbox.remote_refs()
    tag = _signed_tag(push_sandbox.work, _side(push_sandbox, "side"), name, message)
    merge = _merge(push_sandbox, tag)
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert_blocked(result, push_sandbox, before, f"commit[{merge[:12]}].mergetag[1].{field}")
    assert f"commit[{merge[:12]}].message" not in result.stderr


def test_clean_signed_tag_merge_still_delivers(push_sandbox):
    merge = _merge(push_sandbox, _signed_tag(push_sandbox.work, _side(push_sandbox, "side"), "v1"))
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert result.returncode == 0, result.stderr
    assert push_sandbox.remote_refs()["refs/heads/feature"] == merge


def test_octopus_merge_hit_in_the_second_mergetag_only_is_refused(push_sandbox):
    before = push_sandbox.remote_refs()
    first = _signed_tag(push_sandbox.work, _side(push_sandbox, "one"), "v1")
    second = _signed_tag(push_sandbox.work, _side(push_sandbox, "two"), "v2", f"clean release\n\nbody {TOKEN}\n")
    merge = _merge(push_sandbox, first, second)
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert_blocked(result, push_sandbox, before, f"commit[{merge[:12]}].mergetag[2].message")
    assert "mergetag[1]" not in result.stderr


def test_public_merge_is_excluded_with_its_embedded_tag_text(push_sandbox, monkeypatch, capfd):
    """The merge commit carries the embedded tag, so a public merge has already published it."""
    merge = _merge(push_sandbox, _signed_tag(push_sandbox.work, _side(push_sandbox, "side"), f"v1-{TOKEN}"))
    push_sandbox.commit("new clean work")
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(merge))
    err = capfd.readouterr().err
    assert status == 0 and executed, err
    assert "1 commit(s) scanned" in err and TOKEN not in err and merge[:12] not in err


def test_new_merge_on_top_of_public_main_has_its_mergetag_text_scanned(push_sandbox, monkeypatch, capfd):
    public_head = _git(push_sandbox.work, "rev-parse", "HEAD")
    merge = _merge(push_sandbox, _signed_tag(push_sandbox.work, _side(push_sandbox, "side"), f"v1-{TOKEN}"))
    # The new merge and its side commit are scanned; the merge's mergetag text is read with it.
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(public_head))
    err = capfd.readouterr().err
    assert status == 2 and not executed
    assert f"field=commit[{merge[:12]}].mergetag[1].tagname" in err and "2 commit(s) scanned" in err, err


def test_commit_without_a_header_body_separator_is_refused(push_sandbox):
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


@pytest.mark.parametrize("raw", [b"tag v1\nno separator " + TOKEN.encode(), b" opening continuation\n\nbody"])
def test_split_object_refuses_text_outside_any_message(raw):
    with pytest.raises(gate.PublishBlocked) as raised:
        git_push.split_object(raw, "commit[unit]")
    assert str(raised.value).startswith("OPSEC: commit[unit] ") and TOKEN not in str(raised.value)


# --- Nothing an earlier push decided is trusted; linear unfolding ---

# Each edit reverts one mergetag/separator fix in the sandbox copy, giving its shim an older, weaker scanner.
WEAKER_SCANNERS = {
    "mergetag": ('if key == b"mergetag"]', 'if key == b"weaker"]'),
    "separator": ("    if not separator:\n", "    if False:\n"),
}


def _with_scanner(sandbox, *edits):
    """Swap the scanner source the sandbox shim runs: (old, new) edits, or none for the reviewed code."""
    original = (ROOT / "scripts/opsec/git_push.py").read_text()
    for edit in edits:
        assert original.count(edit[0]) == 1, edit[0]
        original = original.replace(*edit)
    (sandbox.root / "scripts/opsec/git_push.py").write_text(original)


def _unseparated_hit(sandbox):
    tree, parent = _git(sandbox.work, "rev-parse", "HEAD^{tree}"), _git(sandbox.work, "rev-parse", "HEAD")
    identity = "unit <unit@example.invalid> 0 +0000"
    raw = f"tree {tree}\nparent {parent}\nauthor {identity}\ncommitter {identity}\nclean subject {TOKEN}\n"
    return _object(sandbox.work, "commit", raw.encode())


@pytest.mark.parametrize("weakness", sorted(WEAKER_SCANNERS))
def test_a_commit_an_older_scanner_passed_is_rescanned_and_refused(push_sandbox, weakness):
    """An older scanner's clean verdict is never carried into a later push."""
    if weakness == "mergetag":
        sha = _merge(push_sandbox, _signed_tag(push_sandbox.work, _side(push_sandbox, "side"), f"v1-{TOKEN}"))
    else:
        sha = _unseparated_hit(push_sandbox)
    _with_scanner(push_sandbox, WEAKER_SCANNERS[weakness])
    older = push_sandbox.push("push", "origin", f"{sha}:refs/heads/older")
    assert older.returncode == 0, older.stderr
    _with_scanner(push_sandbox)
    before = push_sandbox.remote_refs()
    result = push_sandbox.push("push", "origin", f"{sha}:refs/heads/feature")
    if weakness == "mergetag":
        assert_blocked(result, push_sandbox, before, f"commit[{sha[:12]}].mergetag[1].tagname")
    else:
        assert result.returncode == 2, result.stderr
        assert f"OPSEC: commit[{sha[:12]}] has no header/body separator; push refused." in result.stderr
        assert TOKEN not in result.stderr and push_sandbox.remote_refs() == before
    assert _scan_files(push_sandbox) == {}


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


# --- An alternate shallow file named by the environment is refused ---


def test_shallow_file_environment_variable_is_refused(push_sandbox, tmp_path):
    """GIT_SHALLOW_FILE changes the file git walks while git rev-parse --git-path still names the usual one."""
    base = _git(push_sandbox.work, "rev-parse", "HEAD")
    hit = push_sandbox.commit("subject " + TOKEN)
    cover = push_sandbox.commit("clean cover")
    alternate = tmp_path / "alternate-shallow"
    alternate.write_text(f"{cover}\n")
    # Positive control: git honours the variable and no longer walks to the hit.
    walked = subprocess.run(
        [REAL_GIT, "rev-list", cover, f"^{base}"],
        cwd=push_sandbox.work,
        env=_env(GIT_SHALLOW_FILE=str(alternate)),
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    ).stdout.split()
    assert walked == [cover] and hit not in walked
    before = push_sandbox.remote_refs()
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature", GIT_SHALLOW_FILE=str(alternate))
    assert result.returncode == 2 and "GIT_SHALLOW_FILE is not supported for a scanned push" in result.stderr
    assert TOKEN not in result.stderr and push_sandbox.remote_refs() == before


# --- The real push sends exactly the scanned objects to the scanned names ---


def _move_after_the_scan(monkeypatch, move):
    """Run move once the scan's check_texts has passed: another process changing refs before the real push."""
    check = gate.check_texts

    def check_then_move(*args, **kwargs):
        check(*args, **kwargs)
        move()

    monkeypatch.setattr(gate, "check_texts", check_then_move)


def _remote_has(sandbox, sha):
    return subprocess.run([REAL_GIT, "cat-file", "-e", sha], cwd=sandbox.remote, env=_env(), timeout=30).returncode == 0


def test_branch_moved_after_the_scan_is_not_published(push_sandbox, monkeypatch, capfd):
    scanned = push_sandbox.commit("clean subject")
    tree = _git(push_sandbox.work, "rev-parse", "HEAD^{tree}")
    hit = _git(push_sandbox.work, "commit-tree", tree, "-p", scanned, "-m", "subject " + TOKEN)
    _move_after_the_scan(monkeypatch, lambda: _git(push_sandbox.work, "update-ref", "refs/heads/trunk", hit))
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(None), deliver=True)
    assert status == 0 and executed, capfd.readouterr().err
    # Positive control: the caller's HEAD now names the hit, so re-resolving it would have sent it.
    assert _git(push_sandbox.work, "rev-parse", "HEAD") == hit
    assert push_sandbox.remote_refs()["refs/heads/feature"] == scanned and not _remote_has(push_sandbox, hit)
    assert executed[0][-3:] == ["--", str(push_sandbox.remote), f"{scanned}:refs/heads/feature"]


def test_matching_push_does_not_publish_a_branch_matched_after_the_scan(push_sandbox, monkeypatch, capfd):
    base = _git(push_sandbox.work, "rev-parse", "HEAD")
    hit = push_sandbox.commit("subject " + TOKEN)
    _git(push_sandbox.work, "branch", "other", hit)
    _git(push_sandbox.work, "reset", "-q", "--hard", base)
    scanned = push_sandbox.commit("clean subject")
    _move_after_the_scan(monkeypatch, lambda: _git(push_sandbox.remote, "update-ref", "refs/heads/other", base))
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(None), "push", "origin", ":", deliver=True)
    assert status == 0 and executed, capfd.readouterr().err
    # Positive control: a matching push now also matches other, and would send the hit.
    preview = _git(push_sandbox.work, "push", "--dry-run", "--porcelain", "origin", ":")
    assert "refs/heads/other:refs/heads/other" in preview
    refs = push_sandbox.remote_refs()
    assert refs["refs/heads/trunk"] == scanned and refs["refs/heads/other"] == base
    assert not _remote_has(push_sandbox, hit)


def test_frozen_push_replaces_ref_selection_with_the_scanned_mapping(push_sandbox, monkeypatch, capfd):
    sha = push_sandbox.commit("clean subject")
    _git(push_sandbox.work, "tag", "-a", "v1", "-m", "clean release")
    tag = _git(push_sandbox.work, "rev-parse", "v1")
    _git(push_sandbox.work, "push", "-q", "origin", "HEAD:refs/heads/gone")
    status, executed = run_main(
        push_sandbox,
        monkeypatch,
        FakePublic(None),
        "-c",
        "push.followTags=true",
        "push",
        "-qf",
        "--follow-tags",
        "--atomic",
        "origin",
        "HEAD:refs/heads/feature",
        "v1",
        ":refs/heads/gone",
    )
    assert status == 0, capfd.readouterr().err
    assert executed == [
        [
            REAL_GIT,
            "-c",
            "push.followTags=true",
            "-c",
            f"core.hooksPath={git_push.HOOKS / 'guard'}",
            "push",
            "-qf",
            "--atomic",
            "--verify",
            "--no-follow-tags",
            "--",
            str(push_sandbox.remote),
            ":refs/heads/gone",
            f"{sha}:refs/heads/feature",
            f"{tag}:refs/tags/v1",
        ]
    ]


def test_forced_update_stays_forced(push_sandbox, monkeypatch, capfd):
    push_sandbox.commit("clean one")
    _git(push_sandbox.work, "push", "-q", "origin", "HEAD:refs/heads/feature")
    _git(push_sandbox.work, "reset", "-q", "--hard", "HEAD~1")
    rewritten = push_sandbox.commit("clean rewritten")
    status, executed = run_main(
        push_sandbox, monkeypatch, FakePublic(None), "push", "origin", "+HEAD:refs/heads/feature", deliver=True
    )
    assert status == 0 and executed[0][-1] == f"+{rewritten}:refs/heads/feature", capfd.readouterr().err
    assert push_sandbox.remote_refs()["refs/heads/feature"] == rewritten


@pytest.mark.parametrize(
    "args,branch",
    [
        (("push", "-u", "origin", "HEAD:refs/heads/feature"), "feature"),
        (("push", "--set-upstream", "origin", "HEAD"), "trunk"),
    ],
)
def test_set_upstream_is_recorded_after_the_frozen_push(push_sandbox, args, branch):
    sha = push_sandbox.commit("clean subject")
    result = push_sandbox.push(*args)
    assert result.returncode == 0, result.stderr
    assert push_sandbox.remote_refs()[f"refs/heads/{branch}"] == sha
    assert _git(push_sandbox.work, "config", "branch.trunk.remote") == "origin"
    assert _git(push_sandbox.work, "config", "branch.trunk.merge") == f"refs/heads/{branch}"
    assert f"branch 'trunk' set up to track 'origin/{branch}'." in result.stdout
    assert _git(push_sandbox.work, "rev-parse", "--abbrev-ref", "@{upstream}") == f"origin/{branch}"
    assert _git(push_sandbox.work, "rev-parse", f"refs/remotes/origin/{branch}") == sha


def test_set_upstream_honours_auto_setup_rebase_and_dry_run(push_sandbox):
    push_sandbox.commit("clean subject")
    _git(push_sandbox.work, "config", "branch.autoSetupRebase", "always")
    before = push_sandbox.remote_refs()
    dry = push_sandbox.push("push", "-n", "-u", "origin", "HEAD:refs/heads/feature")
    assert dry.returncode == 0 and push_sandbox.remote_refs() == before, dry.stderr
    assert subprocess.run(
        [REAL_GIT, "config", "branch.trunk.merge"], cwd=push_sandbox.work, env=_env(), timeout=30
    ).returncode
    real = push_sandbox.push("push", "-u", "origin", "HEAD:refs/heads/feature")
    assert real.returncode == 0 and _git(push_sandbox.work, "config", "branch.trunk.rebase") == "true", real.stderr


@pytest.mark.parametrize(
    "args,refusal",
    [
        (("push", "--follow", "origin", "HEAD:refs/heads/feature"), "push option not recognised"),
        (
            ("push", "--force-with-lease", "--force-if-includes", "origin", "HEAD:refs/heads/feature"),
            "--force-if-includes cannot apply to the frozen push",
        ),
    ],
)
def test_forms_that_cannot_be_frozen_are_refused(push_sandbox, args, refusal):
    push_sandbox.commit("clean subject")
    _git(push_sandbox.work, "branch", "--set-upstream-to=origin/trunk")
    before = push_sandbox.remote_refs()
    result = push_sandbox.push(*args)
    assert result.returncode == 2 and refusal in result.stderr, result.stderr
    assert push_sandbox.remote_refs() == before


def test_each_push_url_receives_its_own_previewed_refs(push_sandbox, tmp_path, monkeypatch, capfd):
    """A matching push can send different refs to each push URL; each gets exactly its own."""
    second = tmp_path / "second.git"
    _git(tmp_path, "init", "-q", "--bare", str(second))
    _git(push_sandbox.work, "branch", "other")
    _git(push_sandbox.work, "push", "-q", str(second), "trunk", "other")
    for url in (push_sandbox.remote, second):
        _git(push_sandbox.work, "remote", "set-url", "--add", "--push", "origin", str(url))
    sha = push_sandbox.commit("clean subject")
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(None), "push", "origin", ":", deliver=True)
    assert status == 0, capfd.readouterr().err
    other = _git(push_sandbox.work, "rev-parse", "other")
    assert [argv[argv.index("--") + 1 :] for argv in executed] == [
        [str(push_sandbox.remote), f"{sha}:refs/heads/trunk"],
        [str(second), f"{other}:refs/heads/other", f"{sha}:refs/heads/trunk"],
    ]
    assert push_sandbox.remote_refs() == {"refs/heads/trunk": sha}
    assert _git(second, "for-each-ref", "--format=%(refname) %(objectname)").splitlines() == [
        f"refs/heads/other {other}",
        f"refs/heads/trunk {sha}",
    ]


@pytest.mark.parametrize(
    "rest,kept,flags",
    [
        (["-fuo", "x", "origin", "main"], ["-fo", "x"], {}),
        (["--repo", "origin", "-d", "--tags", "-qn"], ["-qn"], {"dry_run": True, "quiet": True}),
        (["--push-option=a", "--no-verify", "--", "url", "main"], ["--push-option=a"], {"verify": False}),
        (
            ["--force-if-includes", "--no-force-if-includes", "-v", "o"],
            ["--force-if-includes", "--no-force-if-includes", "-v"],
            {},
        ),
        (["-ofoo", "origin"], ["-ofoo"], {}),
        (["--receive-pack", "rp", "origin"], ["--receive-pack", "rp"], {"receive_pack": True}),
        (
            ["--force-with-lease", "--no-force-with-lease", "--force-with-lease=a", "--force-with-lease", "o"],
            [],
            {"leases": ["a", None]},
        ),
    ],
)
def test_push_arguments(rest, kept, flags):
    parsed = git_push.push_arguments(rest)
    assert parsed.kept == kept
    names = ("dry_run", "quiet", "force_if_includes", "verify", "receive_pack", "leases")
    defaults = {"dry_run": False, "quiet": False, "force_if_includes": False, "verify": True, "receive_pack": False}
    assert {name: getattr(parsed, name) for name in names} == {**defaults, "leases": [], **flags}


@pytest.mark.parametrize("rest", [["--mir"], ["-x"], ["--repo"], ["-o"], ["--unknown", "origin"]])
def test_push_arguments_refuse_abbreviated_or_unknown_options(rest):
    with pytest.raises(gate.PublishBlocked, match="push option not recognised"):
        git_push.push_arguments(rest)


# --- Exclusion relies only on public history whose bytes match their ids ---


def _loose(store, sha):
    return store / sha[:2] / sha[2:]


def _write_loose(store, sha, raw):
    path = _loose(store, sha)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.chmod(0o644)
    path.write_bytes(zlib.compress(b"commit %d\0" % len(raw) + raw))


@pytest.mark.parametrize("store", ["own", "alternate"])
def test_altered_public_history_bytes_exclude_nothing(push_sandbox, monkeypatch, capfd, tmp_path, store):
    """Bytes under the authoritative head's id that name the hit as a parent must not hide the hit."""
    public_head = push_sandbox.commit("published clean")
    hit = push_sandbox.commit("subject " + TOKEN)
    genuine = subprocess.run(
        [REAL_GIT, "cat-file", "commit", public_head],
        cwd=push_sandbox.work,
        env=_env(),
        capture_output=True,
        check=True,
        timeout=30,
    ).stdout
    forged = re.sub(rb"\nparent [0-9a-f]{40}\n", f"\nparent {hit}\n".encode(), genuine, count=1)
    assert forged != genuine
    objects = push_sandbox.work / ".git/objects"
    if store == "own":
        _write_loose(objects, public_head, forged)
    else:
        alternate = tmp_path / "alternate/objects"
        _write_loose(alternate, public_head, forged)
        _loose(objects, public_head).unlink()
        (objects / "info/alternates").write_text(f"{alternate}\n")
    # Positive control: git trusts the stored bytes and would exclude the hit.
    assert _git(push_sandbox.work, "rev-list", hit, f"^{public_head}") == ""
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(public_head))
    err = capfd.readouterr().err
    assert status == 2 and not executed and f"field=commit[{hit[:12]}].message" in err, err
    assert "public default-branch head unverified here" in err and FETCH_HINT not in err


def test_history_verification_reads_every_public_commit(push_sandbox, monkeypatch, capfd):
    """A missing ancestor of the public head leaves its history unverified, so nothing is excluded."""
    root = _git(push_sandbox.work, "rev-parse", "HEAD")
    public_head = push_sandbox.commit("published clean")
    push_sandbox.commit("new clean work")
    repository = git_push.Repository(REAL_GIT, [], _env())
    monkeypatch.chdir(push_sandbox.work)
    assert git_push.history_verified(repository, public_head, "sha1")
    _loose(push_sandbox.work / ".git/objects", root).unlink()
    assert not git_push.history_verified(repository, public_head, "sha1")


# --- Delivery goes to the inspected destination; configuration read later cannot redirect it ---


def _bare(tmp_path, name):
    path = tmp_path / name
    _git(tmp_path, "init", "-q", "--bare", str(path))
    return path


def test_private_remote_reconfigured_public_after_the_preview_publishes_nothing(
    push_sandbox, tmp_path, monkeypatch, capfd
):
    public = _bare(tmp_path, "public.git")
    _private(monkeypatch, push_sandbox.remote)
    sha = push_sandbox.commit("subject " + TOKEN)
    _move_after_the_scan(monkeypatch, lambda: _git(push_sandbox.work, "remote", "set-url", "origin", str(public)))
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(None, fail=True), deliver=True, scan=False)
    assert status == 0, capfd.readouterr().err
    # Positive control: the remote name now resolves to the public destination.
    assert _git(push_sandbox.work, "remote", "get-url", "--push", "origin") == str(public)
    assert executed[0][-2] == str(push_sandbox.remote)
    assert push_sandbox.remote_refs()["refs/heads/feature"] == sha
    assert _git(public, "for-each-ref") == "" and _git(public, "count-objects") == "0 objects, 0 kilobytes"


@pytest.mark.parametrize(
    "change",
    [
        lambda work, public: _git(work, "remote", "set-url", "--push", "origin", str(public)),
        lambda work, public: _git(work, "config", "remote.origin.pushurl", str(public)),
    ],
    ids=["set-url", "pushurl"],
)
def test_push_url_changed_after_the_preview_still_goes_to_the_inspected_url(
    push_sandbox, tmp_path, monkeypatch, capfd, change
):
    other = _bare(tmp_path, "other.git")
    sha = push_sandbox.commit("clean subject")
    _move_after_the_scan(monkeypatch, lambda: change(push_sandbox.work, other))
    status, _ = run_main(push_sandbox, monkeypatch, FakePublic(None), deliver=True)
    assert status == 0, capfd.readouterr().err
    assert push_sandbox.remote_refs()["refs/heads/feature"] == sha
    assert _git(other, "for-each-ref") == ""


@pytest.mark.parametrize("kind", ["insteadOf", "pushInsteadOf"])
def test_url_rewrite_added_after_the_preview_is_refused_by_the_guard(push_sandbox, tmp_path, monkeypatch, capfd, kind):
    other = _bare(tmp_path, "other.git")
    before = push_sandbox.remote_refs()
    push_sandbox.commit("clean subject")
    rewrite = ("config", f"url.{other}.{kind}", str(push_sandbox.remote))
    _move_after_the_scan(monkeypatch, lambda: _git(push_sandbox.work, *rewrite))
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(None), deliver=True)
    err = capfd.readouterr().err
    assert executed and status == 1, err
    assert "OPSEC: the push destination is not the one the scan inspected; push refused." in err
    assert push_sandbox.remote_refs() == before and _git(other, "for-each-ref") == ""
    # Positive control: git now rewrites the inspected URL to the other repository.
    preview = _git(push_sandbox.work, "push", "--dry-run", "--porcelain", str(push_sandbox.remote), "HEAD:refs/heads/x")
    assert f"To {other}" in preview


def test_guard_refuses_any_other_url_and_runs_the_caller_hook_on_a_match(tmp_path):
    guard = git_push.HOOKS / "guard/pre-push"
    record = tmp_path / "record"
    caller = tmp_path / "caller-hook"
    caller.write_text(f'#!/bin/sh\nprintf "%s %s " "$1" "$2" > {record}\ncat >> {record}\n')
    caller.chmod(0o755)

    def run(url, **env):
        return subprocess.run(
            [str(guard), "url-name", url],
            input="refs line\n",
            env={"PATH": os.defpath, **env},
            capture_output=True,
            text=True,
            timeout=30,
        )

    unset = run("https://example.invalid/x")
    assert unset.returncode == 1 and "push refused" in unset.stderr
    other = run("https://example.invalid/y", LU_OPSEC_PUSH_URL="https://example.invalid/x")
    assert other.returncode == 1 and not record.exists()
    match = run(
        "https://example.invalid/x",
        LU_OPSEC_PUSH_URL="https://example.invalid/x",
        LU_OPSEC_PUSH_REMOTE="origin",
        LU_OPSEC_PUSH_HOOK=str(caller),
    )
    assert match.returncode == 0 and record.read_text() == "origin https://example.invalid/x refs line\n"
    assert run("-n", LU_OPSEC_PUSH_URL="-n").returncode == 0


def test_configured_mirror_remote_delivers_the_previewed_refs(push_sandbox):
    _git(push_sandbox.work, "config", "remote.origin.mirror", "true")
    sha = push_sandbox.commit("clean subject")
    result = push_sandbox.push("push", "origin")
    assert result.returncode == 0, result.stderr
    assert "can't be combined with refspecs" not in result.stderr
    assert push_sandbox.remote_refs()["refs/heads/trunk"] == sha


def test_ordinary_push_to_the_upstream_updates_the_tracking_ref(push_sandbox):
    _git(push_sandbox.work, "branch", "--set-upstream-to=origin/trunk")
    sha = push_sandbox.commit("clean subject")
    result = push_sandbox.push("push")
    assert result.returncode == 0, result.stderr
    assert push_sandbox.remote_refs()["refs/heads/trunk"] == sha
    assert _git(push_sandbox.work, "rev-parse", "refs/remotes/origin/trunk") == sha
    assert _git(push_sandbox.work, "status", "-sb").splitlines()[0] == "## trunk...origin/trunk"


def test_auto_setup_remote_push_records_the_upstream(push_sandbox):
    _git(push_sandbox.work, "switch", "-q", "-c", "topic")
    sha = push_sandbox.commit("clean subject")
    result = push_sandbox.push("-c", "push.autoSetupRemote=true", "push")
    assert result.returncode == 0, result.stderr
    assert push_sandbox.remote_refs()["refs/heads/topic"] == sha
    assert _git(push_sandbox.work, "rev-parse", "--abbrev-ref", "@{upstream}") == "origin/topic"


def test_push_to_a_url_updates_no_tracking_ref(push_sandbox):
    sha = push_sandbox.commit("clean subject")
    result = push_sandbox.push("push", str(push_sandbox.remote), "HEAD:refs/heads/feature")
    assert result.returncode == 0, result.stderr
    assert push_sandbox.remote_refs()["refs/heads/feature"] == sha
    assert "refs/remotes/origin/feature" not in _git(push_sandbox.work, "for-each-ref")


@pytest.mark.parametrize("via", ["hooks", "hooksPath"])
@pytest.mark.parametrize("verify", [True, False])
def test_the_callers_pre_push_hook_still_runs(push_sandbox, tmp_path, via, verify):
    hooks = push_sandbox.work / ".git/hooks" if via == "hooks" else tmp_path / "caller-hooks"
    hooks.mkdir(exist_ok=True)
    record = tmp_path / "record"
    (hooks / "pre-push").write_text(f'#!/bin/sh\nprintf "%s %s\\n" "$1" "$2" >> {record}\ncat >> {record}\n')
    (hooks / "pre-push").chmod(0o755)
    sha = push_sandbox.commit("clean subject")
    options = ("-c", f"core.hooksPath={hooks}") if via == "hooksPath" else ()
    flags = () if verify else ("--no-verify",)
    result = push_sandbox.push(*options, "push", *flags, "origin", "HEAD:refs/heads/feature")
    assert result.returncode == 0, result.stderr
    assert push_sandbox.remote_refs()["refs/heads/feature"] == sha
    if verify:
        zero = "0" * 40
        assert record.read_text() == f"origin {push_sandbox.remote}\n{sha} {sha} refs/heads/feature {zero}\n"
    else:
        assert not record.exists()


def test_caller_no_verify_does_not_disable_the_guard(push_sandbox, tmp_path, monkeypatch, capfd):
    other = _bare(tmp_path, "other.git")
    before = push_sandbox.remote_refs()
    push_sandbox.commit("clean subject")
    rewrite = ("config", f"url.{other}.insteadOf", str(push_sandbox.remote))
    _move_after_the_scan(monkeypatch, lambda: _git(push_sandbox.work, *rewrite))
    status, executed = run_main(
        push_sandbox, monkeypatch, FakePublic(None), "push", "--no-verify", "origin", "HEAD:refs/heads/f", deliver=True
    )
    assert status == 1 and "--verify" in executed[0], capfd.readouterr().err
    assert push_sandbox.remote_refs() == before and _git(other, "for-each-ref") == ""


def test_lease_is_frozen_from_the_tracking_ref_and_enforced(push_sandbox, monkeypatch, capfd):
    first = push_sandbox.commit("clean one")
    _git(push_sandbox.work, "push", "-q", "origin", "HEAD:refs/heads/feature")
    _git(push_sandbox.work, "fetch", "-q", "origin")
    _git(push_sandbox.work, "reset", "-q", "--hard", "HEAD~1")
    rewritten = push_sandbox.commit("clean rewritten")
    args = ("push", "--force-with-lease", "origin", "HEAD:refs/heads/feature")
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(None), *args, deliver=True)
    assert status == 0, capfd.readouterr().err
    assert f"--force-with-lease=refs/heads/feature:{first}" in executed[0]
    assert executed[0][-1] == f"{rewritten}:refs/heads/feature"  # A + would defeat the lease.
    assert push_sandbox.remote_refs()["refs/heads/feature"] == rewritten
    assert _git(push_sandbox.work, "rev-parse", "refs/remotes/origin/feature") == rewritten


def test_lease_broken_after_the_preview_rejects_the_push(push_sandbox, monkeypatch, capfd):
    push_sandbox.commit("clean one")
    _git(push_sandbox.work, "push", "-q", "origin", "HEAD:refs/heads/feature")
    _git(push_sandbox.work, "fetch", "-q", "origin")
    base = _git(push_sandbox.work, "rev-parse", "HEAD~1")
    _git(push_sandbox.work, "reset", "-q", "--hard", "HEAD~1")
    push_sandbox.commit("clean rewritten")
    # Another pusher moves the remote ref after the scan; the lease must still protect it.
    _move_after_the_scan(monkeypatch, lambda: _git(push_sandbox.remote, "update-ref", "refs/heads/feature", base))
    args = ("push", "--force-with-lease=feature", "origin", "HEAD:refs/heads/feature")
    status, _ = run_main(push_sandbox, monkeypatch, FakePublic(None), *args, deliver=True)
    assert status == 1 and "stale info" in capfd.readouterr().err
    assert push_sandbox.remote_refs()["refs/heads/feature"] == base


def test_remote_receive_pack_is_carried_to_the_url(push_sandbox, monkeypatch, capfd):
    _git(push_sandbox.work, "config", "remote.origin.receivepack", "git-receive-pack")
    push_sandbox.commit("clean subject")
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(None), deliver=True)
    assert status == 0 and "--receive-pack=git-receive-pack" in executed[0], capfd.readouterr().err


def test_remote_proxy_that_cannot_follow_the_url_is_refused(push_sandbox):
    _git(push_sandbox.work, "config", "remote.origin.proxy", "http://proxy.invalid")
    before = push_sandbox.remote_refs()
    push_sandbox.commit("clean subject")
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert result.returncode == 2 and "vcs or proxy setting cannot be carried" in result.stderr, result.stderr
    assert push_sandbox.remote_refs() == before


def test_unexecutable_push_hooks_refuse(push_sandbox, monkeypatch, tmp_path, capfd):
    hooks = tmp_path / "hooks"
    shutil.copytree(git_push.HOOKS, hooks)
    (hooks / "guard/pre-push").chmod(0o644)
    monkeypatch.setattr(git_push, "HOOKS", hooks)
    push_sandbox.commit("clean subject")
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(None))
    assert status == 2 and not executed and "push hooks not executable" in capfd.readouterr().err


@pytest.mark.parametrize(
    "fetch,name,expected",
    [
        (["+refs/heads/*:refs/remotes/origin/*"], "refs/heads/a/b", "refs/remotes/origin/a/b"),
        (["+refs/heads/*:refs/remotes/origin/*"], "refs/tags/v1", None),
        (["refs/heads/main:refs/remotes/o/main"], "refs/heads/main", "refs/remotes/o/main"),
        (["refs/heads/main"], "refs/heads/main", None),
        (["+refs/heads/*:refs/remotes/o/*", "^refs/heads/wip*"], "refs/heads/wip1", None),
        (["refs/heads/x*y:refs/r/*"], "refs/heads/xy", "refs/r/"),
        (["refs/heads/a:refs/r/first", "refs/heads/*:refs/r/*"], "refs/heads/a", "refs/r/first"),
    ],
)
def test_tracking_ref(fetch, name, expected):
    assert git_push.tracking_ref(fetch, name) == expected


@pytest.mark.parametrize(
    "short,full,expected",
    [("main", "refs/heads/main", True), ("heads/main", "refs/heads/main", True), ("ain", "refs/heads/main", False)],
)
def test_refname_match(short, full, expected):
    assert git_push.refname_match(short, full) is expected


def test_explicit_leases_are_resolved_once(push_sandbox, monkeypatch, capfd):
    first = push_sandbox.commit("clean one")
    _git(push_sandbox.work, "push", "-q", "origin", "HEAD:refs/heads/feature")
    _git(push_sandbox.work, "reset", "-q", "--hard", "HEAD~1")
    rewritten = push_sandbox.commit("clean rewritten")
    args = (
        "push",
        f"--force-with-lease=feature:{first}",
        "--force-with-lease=refs/heads/new:",
        "origin",
        "HEAD:refs/heads/feature",
        "HEAD:refs/heads/new",
    )
    status, executed = run_main(push_sandbox, monkeypatch, FakePublic(None), *args, deliver=True)
    assert status == 0, capfd.readouterr().err
    assert f"--force-with-lease=refs/heads/feature:{first}" in executed[0]
    assert "--force-with-lease=refs/heads/new:" in executed[0]
    refs = push_sandbox.remote_refs()
    assert refs["refs/heads/feature"] == rewritten and refs["refs/heads/new"] == rewritten


def test_ssh_command_configured_after_the_preview_is_not_used(ssh_sandbox, tmp_path, monkeypatch, capfd):
    """core.sshCommand decides where an unchanged ssh URL connects; the preview's choice is pinned."""
    url = "git@github.com:unit/public.git"
    decoy = tmp_path / "decoy-root"
    _git(tmp_path, "init", "-q", "--bare", str(decoy / "unit/public.git"))
    env = dict(ssh_sandbox.ssh_env)
    ssh = env.pop("GIT_SSH_COMMAND")
    _git(ssh_sandbox.work, "config", "core.sshCommand", ssh)
    sha = ssh_sandbox.commit("clean subject")
    redirect = ("config", "core.sshCommand", f"FAKE_SSH_ROOT={decoy} {ssh}")
    _move_after_the_scan(monkeypatch, lambda: _git(ssh_sandbox.work, *redirect))
    status, _ = run_main(
        ssh_sandbox, monkeypatch, FakePublic(None), "push", url, "HEAD:refs/heads/feature", deliver=True, **env
    )
    assert status == 0, capfd.readouterr().err
    assert _git(ssh_sandbox.served / "unit/public.git", "rev-parse", "refs/heads/feature") == sha
    assert _git(decoy / "unit/public.git", "for-each-ref") == ""
    # Positive control: a push resolving the ssh command now reaches the decoy.
    _git(ssh_sandbox.work, "push", "-q", url, "HEAD:refs/heads/control")
    assert _git(decoy / "unit/public.git", "rev-parse", "refs/heads/control") == sha
