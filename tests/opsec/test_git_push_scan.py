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
from tests.opsec_fixtures import CATALOG, ROOT, TOKEN, make_tooling

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


def test_history_already_on_the_remote_is_not_rescanned(push_sandbox):
    push_sandbox.commit("old " + TOKEN)
    _git(push_sandbox.work, "push", "-q", "origin", "trunk")  # Already public before this change.
    sha = push_sandbox.commit("clean follow-up")
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert result.returncode == 0, result.stderr
    assert push_sandbox.remote_refs()["refs/heads/feature"] == sha


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
    assert "full reachable history scanned" in result.stderr
    assert _git(fresh, "for-each-ref") == ""


def test_forged_tracking_ref_does_not_suppress_the_scan(push_sandbox):
    before = push_sandbox.remote_refs()
    sha = push_sandbox.commit("subject " + TOKEN)
    _git(push_sandbox.work, "update-ref", "refs/remotes/origin/forged", sha)
    result = push_sandbox.push("push", "origin", "HEAD:refs/heads/feature")
    assert_blocked(result, push_sandbox, before, f"commit[{sha[:12]}].message")


def test_incremental_push_enumerates_only_commits_the_destination_lacks(push_sandbox, monkeypatch):
    for number in range(4):
        push_sandbox.commit(f"published {number}")
    _git(push_sandbox.work, "push", "-q", "origin", "trunk")
    new = [push_sandbox.commit(f"new {number}") for number in range(2)]
    captured = []
    monkeypatch.setattr(gate, "check_texts", lambda label, texts, **kw: captured.append(kw["field_names"]))
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


def test_public_ssh_incremental_push_uses_the_destination_advertisement(ssh_sandbox):
    url = "git@github.com:unit/public.git"
    ssh_sandbox.commit("old " + TOKEN)
    subprocess.run(
        [REAL_GIT, "push", "-q", url, "trunk"],
        cwd=ssh_sandbox.work,
        env=_env(**ssh_sandbox.ssh_env),
        check=True,
        timeout=30,
    )
    sha = ssh_sandbox.commit("clean follow-up")
    result = ssh_sandbox.push("push", url, "HEAD:refs/heads/feature", **ssh_sandbox.ssh_env)
    assert result.returncode == 0, result.stderr
    assert _git(ssh_sandbox.served / "unit/public.git", "rev-parse", "refs/heads/feature") == sha


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
    "url,expected",
    [
        ("git@github.com:unit/private.git", "github.com:unit/private.git"),
        ("ssh://git@github.com:22/unit/private.git", "ssh://github.com:22/unit/private.git"),
        ("https://user:secret@github.com/unit/private", "https://github.com/unit/private"),
        ("https://github.com/unit/a@b", "https://github.com/unit/a@b"),
        ("/srv/unit@x:remote.git", "/srv/unit@x:remote.git"),
        ("unit@hostonly", "unit@hostonly"),
    ],
)
def test_anonymized_url_matches_the_preview_form(url, expected):
    assert git_push.anonymize_url(url) == expected


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
