"""Ownership walk and git-state safety."""

import os
import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml

from scripts.dispatcher import git, worker
from scripts.dispatcher.types import TaskSpec
from tests.dispatcher.conftest import run_git


@pytest.mark.parametrize("attack", ["alias-shell", "alias-empty", "replace", "origin", "insteadOf", "pushInsteadOf"])
def test_worker_git_state_cannot_hide_outside_commit(sandbox, delivery_settle, attack):
    """Worker aliases, replacements and remote rewrites cannot certify owned delivery."""
    record, settle = delivery_settle
    tree = Path(record["cwd"])
    (tree / "outside.txt").write_text("outside scope\n")
    run_git(tree, "add", "outside.txt")
    run_git(tree, "commit", "-m", "outside scope")
    record = settle("pushed")
    assert record["error"] == "outside_owned_paths: outside.txt"
    if attack.startswith("alias"):
        run_git(tree, "config", "alias.log", "!true" if attack == "alias-shell" else "log -n 0")
    elif attack == "replace":
        clean_tree = run_git(tree, "rev-parse", f"{record['worktree_base_sha']}^{{tree}}")
        replacement = run_git(tree, "commit-tree", clean_tree, "-p", record["worktree_base_sha"], "-m", "clean")
        run_git(tree, "replace", record["head_sha"], replacement)
        assert run_git(tree, "log", "-1", "--format=", "--name-only") == ""
    else:
        fake = sandbox.repo.parent / "forged.git"
        run_git(tree, "clone", "--bare", str(tree), str(fake))
        run_git(fake, "update-ref", "refs/heads/release", record["head_sha"])
        if attack == "origin":
            run_git(tree, "remote", "set-url", "origin", str(fake))
        else:
            run_git(tree, "config", f"url.{fake}.{attack}", str(sandbox.remote))
    record.update(status="done", error=None)
    worker._enforce_delivery(record)
    assert record["status"] == "no_deliverable"
    assert record["error"].startswith(
        "outside_owned_paths: outside.txt" if attack == "replace" else "owned_paths_verification_failed: ")


def test_ownership_walk_verifies_distinct_publish_branch(sandbox, delivery_settle):
    """Publish-branch confusion must neither reject owned delivery nor hide outside paths."""
    record, settle = delivery_settle
    tree = Path(record["cwd"])
    record["publish_branch"] = "fix/published"
    delivery_ref = f"refs/heads/{record['publish_branch']}"
    (tree / "delivered.txt").write_text("owned delivery\n")
    run_git(tree, "add", "delivered.txt")
    run_git(tree, "commit", "-m", "owned delivery")
    run_git(tree, "push", "origin", f"HEAD:{delivery_ref}")
    assert run_git(sandbox.remote, "for-each-ref", f"refs/heads/{record['worktree_branch']}") == ""
    delivered = settle()
    assert delivered["remote_ref"] == delivery_ref
    assert (delivered["status"], delivered["error"]) == ("done", None)
    (tree / "outside.txt").write_text("outside scope\n")
    run_git(tree, "add", "outside.txt")
    run_git(tree, "commit", "-m", "outside scope")
    run_git(tree, "push", "origin", f"HEAD:{delivery_ref}")
    rejected = settle()
    assert rejected["remote_ref"] == delivery_ref
    assert (rejected["status"], rejected["error"]) == ("no_deliverable", "outside_owned_paths: outside.txt")


@pytest.mark.parametrize("publish_branch", ["release", "fix/published"])
def test_ownership_walk_requires_distinct_refs_and_nonempty_range(sandbox, delivery_settle, publish_branch):
    """Equal delivery/base refs and empty inspected ranges fail ownership verification."""
    record, settle = delivery_settle
    tree = Path(record["cwd"])
    record["publish_branch"] = publish_branch
    (tree / "outside.txt").write_text("scope fixture\n")
    run_git(tree, "add", "outside.txt")
    run_git(tree, "commit", "-m", "scope fixture")
    refs = list(dict.fromkeys(("refs/heads/release", f"refs/heads/{publish_branch}")))
    run_git(tree, "push", "origin", *(f"HEAD:{ref}" for ref in refs))
    rejected = settle()
    assert rejected["remote_ref"] == f"refs/heads/{publish_branch}"
    assert rejected["commits_ahead"] == 1
    assert (rejected["status"], rejected["error"]) == ("no_deliverable", ("owned_paths_verification_failed: delivery ref must differ from base ref" if publish_branch == "release" else "owned_paths_verification_failed: empty ownership range with recorded commits ahead"))


def test_ownership_walk_ignores_worker_config_includes_and_ambient_git_env(sandbox, delivery_settle, monkeypatch):
    """Local/worktree includes and injected process config cannot alter the private walk."""
    record, settle = delivery_settle
    record = settle("pushed")
    tree = Path(record["cwd"])
    included = sandbox.repo.parent / "included.config"
    included.write_text("[worker]\n included = untrusted\n")
    for scope in ("--local", "--worktree"):
        run_git(tree, "config", scope, "worker.marker", "untrusted")
        run_git(tree, "config", scope, "include.path", str(included))
    global_config = sandbox.repo.parent / "global.config"
    global_config.write_text("[worker]\n global = untrusted\n[alias]\n log = !true\n")
    for key, value in {
        "GIT_CONFIG_GLOBAL": str(global_config), "GIT_CONFIG_SYSTEM": str(global_config),
        "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "alias.log", "GIT_CONFIG_VALUE_0": "!true",
        "GIT_CONFIG_PARAMETERS": "'alias.log=log -n 0'", "GIT_DIR": str(sandbox.remote),
        "GIT_CONFIG": str(global_config), "GIT_REPLACE_REF_BASE": "refs/heads/",
    }.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("TMPDIR", raising=False)
    with git.ownership_git(record) as run:
        config = run("config", "--list", "--includes")
        assert "worker." not in config
        assert "alias." not in config
        assert run("rev-parse", "refs/heads/delivery") == record["head_sha"]
    worker._enforce_delivery(record)
    assert (record["status"], record["error"]) == ("done", None)


def test_isolated_private_https_fetch_credentials_never_escape_exact_registered_remote(
    sandbox, delivery_settle, monkeypatch, tmp_path,
):
    """Missing private HTTPS auth rejected pushed work; host-wide auth could leak to another repo.

    Real Git and a fake gh helper exercise credential selection on both production
    fetch paths. Only the network transport is replaced by the disposable remote
    after credential fill succeeds. No live credentials or network are used.
    """
    import shlex

    from scripts.common import git_credentials
    from scripts.orchestration import merge_closeout

    record, settle = delivery_settle
    record = settle("pushed")
    tree = Path(record["cwd"])
    remote = "https://github.com/fixture/private.git"
    run_git(sandbox.repo, "update-ref", "refs/pull/42/head", record["head_sha"])
    run_git(tree, "push", "origin", "HEAD:refs/pull/42/head")
    run_git(tree, "config", "remote.origin.url", remote)
    record["worktree_remote_url"] = remote
    registry = tmp_path / "registry.yaml"
    registry.write_text(yaml.safe_dump({"repos": {"fixture": {"github": "fixture/private", "transport": "https"}}}))
    monkeypatch.setattr(git_credentials, "CONFIG", registry)
    log = tmp_path / "helper-contexts"
    marker = tmp_path / "untrusted-helper-ran"
    fake_gh = tmp_path / "fake gh"
    fake_gh.write_text(
        '#!/bin/sh\n[ "$*" = "auth git-credential get" ] || exit 1\n'
        f"cat >> {shlex.quote(str(log))}\n"
        "printf 'username=fixture-user\\npassword=fixture-password\\n'\n"
    )
    fake_gh.chmod(0o700)
    monkeypatch.setenv("AGENT_REAL_GH", str(fake_gh))
    home = tmp_path / "home"
    home.mkdir()
    included = tmp_path / "untrusted.config"
    included.write_text(f"[credential]\n helper = !touch {shlex.quote(str(marker))}\n[worker]\n global = consulted\n")
    (home / ".gitconfig").write_text(f"[include]\n path = {included}\n")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(included))
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", str(included))
    # The cleanup runner also has to reset URL-scoped primary-repo helpers.
    run_git(tree, "config", f"credential.{remote}.helper", f"!touch {shlex.quote(str(marker))}")
    real_run = subprocess.run
    prefixes = []
    local_imports = []

    def local_transport(argv, **kwargs):
        if "fetch" not in argv:
            return real_run(argv, **kwargs)
        index = argv.index("fetch")
        prefix = argv[:index]
        env = kwargs["env"]
        assert env["GIT_CONFIG_GLOBAL"] == env["GIT_CONFIG_SYSTEM"] == os.devnull
        assert env["GIT_TERMINAL_PROMPT"] == "0" and env["PATH"] == os.defpath
        credentials = real_run(
            [*prefix, "credential", "fill"], cwd=kwargs.get("cwd"), env=env,
            input=f"url={remote}\n\n", capture_output=True, text=True, check=False, timeout=10,
        )
        if any(arg.startswith("file://") for arg in argv[index:]):
            assert env["GIT_ALLOW_PROTOCOL"] == "file"
            assert credentials.returncode != 0
            assert "fixture-password" not in credentials.stdout
            assert not any(".helper=!" in arg for arg in prefix)
            local_imports.append(argv)
            return real_run(argv, **kwargs)
        assert Path(kwargs.get("cwd") or argv[argv.index("-C") + 1]) != sandbox.repo
        assert credentials.returncode == 0
        assert "username=fixture-user\npassword=fixture-password\n" in credentials.stdout
        before = log.read_text()
        config = real_run([*prefix, "config", "--list", "--includes"], cwd=kwargs.get("cwd"), env=env,
                          capture_output=True, text=True, check=True, timeout=10).stdout
        assert "worker.global" not in config
        for other in (
            "https://github.com/fixture/other.git", "https://github.com/other/private.git",
            remote + "/child", remote + "-suffix", remote.removesuffix(".git"),
            "https://other.invalid/fixture/private.git", "http://github.com/fixture/private.git",
        ):
            result = real_run([*prefix, "credential", "fill"], cwd=kwargs.get("cwd"), env=env,
                              input=f"url={other}\n\n", capture_output=True, text=True, check=False, timeout=10)
            assert result.returncode != 0 and "fixture-password" not in result.stdout
        assert log.read_text() == before
        prefixes.append((prefix, kwargs.get("cwd"), env))
        fetch_args = [str(sandbox.remote) if arg == "origin" else arg for arg in argv[index:]]
        return real_run([*prefix, *fetch_args], **kwargs)

    monkeypatch.setattr(subprocess, "run", local_transport)
    worker._enforce_delivery(record)
    assert (record["status"], record["error"]) == ("done", None)
    assert merge_closeout._fetch_live_pr_head(sandbox.repo, 42) == (record["head_sha"], None)
    assert len(prefixes) >= 3  # ownership's bounded fetches and closeout's live PR fetch
    assert len(local_imports) == 1
    expected_contexts = log.read_text()
    assert expected_contexts.count("protocol=https\nhost=github.com\npath=fixture/private.git\n") == len(prefixes)
    assert not marker.exists()
    for other in ("https://github.com/fixture/other.git", "https://user@github.com/fixture/private.git",
                  "git@github.com:fixture/private.git", str(sandbox.remote)):
        assert git_credentials.verification_credentials(other) == []


@pytest.mark.parametrize("shape", ["linear", "merge"])
def test_ownership_walk_does_not_fetch_full_history(tmp_path, monkeypatch, shape):
    """A multi-gigabyte remote must not be fetched whole: only blob-less history since the task base.

    A delivery containing a merge is the exception: re-running a merge needs the complete ancestry
    of its parents. The merge shape has a common ancestor older than the bounded window, and the
    walk must obtain non-shallow history and apply the ownership rules to it.
    """
    remote, tree = tmp_path / "remote.git", tmp_path / "tree"
    run_git(tmp_path, "init", "--bare", str(remote))
    run_git(remote, "config", "uploadpack.allowFilter", "true")
    run_git(tmp_path, "init", "-b", "main", str(tree))
    run_git(tree, "config", "user.email", "stub@example.invalid")
    run_git(tree, "config", "user.name", "Stub")
    run_git(tree, "remote", "add", "origin", str(remote))
    old_commits, old_blobs = set(), set()
    for n in range(20):
        monkeypatch.setenv("GIT_COMMITTER_DATE", f"2020-01-{n + 1:02d}T00:00:00Z")
        (tree / f"old-{n}.txt").write_text(f"old history {n}\n")
        run_git(tree, "add", ".")
        run_git(tree, "commit", "-m", f"old history {n}")
        commit, blob = run_git(tree, "rev-parse", "HEAD", f"HEAD:old-{n}.txt").split()
        old_commits.add(commit)
        old_blobs.add(blob)
    if shape == "merge":
        (tree / "outside.txt").write_text("outside\n")
        run_git(tree, "add", "outside.txt")
        run_git(tree, "commit", "-m", "A")
    monkeypatch.delenv("GIT_COMMITTER_DATE")
    if shape == "linear":
        run_git(tree, "commit", "--allow-empty", "-m", "task base")
        run_git(tree, "push", "origin", "main")
        run_git(tree, "checkout", "-b", "sol/fetch")
    else:
        # A is older than the bounded window; P and Q are newer and share only A as an ancestor.
        # B = merge(P, Q) is the task base.
        run_git(tree, "checkout", "-b", "q")
        (tree / "q.txt").write_text("q\n")
        run_git(tree, "add", "q.txt")
        run_git(tree, "commit", "-m", "Q")
        run_git(tree, "checkout", "main")
        run_git(tree, "rm", "outside.txt")
        run_git(tree, "commit", "-m", "P")
        run_git(tree, "merge", "--no-ff", "-m", "task base", "q")
        run_git(tree, "push", "origin", "main")
        # The delivery branch has two merges above the task base: D of P and Q, then F of B into D.
        run_git(tree, "checkout", "-b", "sol/fetch", "main^1")
        run_git(tree, "merge", "--no-ff", "--no-commit", "q")
        run_git(tree, "checkout", "main^1^1", "--", "outside.txt")
        run_git(tree, "commit", "-m", "D")
        run_git(tree, "merge", "--no-commit", "main")
        run_git(tree, "rm", "outside.txt")
        run_git(tree, "commit", "-m", "F")
    (tree / "delivered.txt").write_text("delivery\n")
    run_git(tree, "add", "delivered.txt")
    run_git(tree, "commit", "-m", "delivery")
    run_git(tree, "push", "origin", "HEAD")
    base, head = run_git(tree, "rev-parse", "main", "HEAD").split()
    record = dict(
        task_id="fetch", worktree_path=str(tree), worktree_remote_url=str(remote),
        worktree_base_ref="refs/remotes/origin/main", worktree_base_sha=base, worktree_branch="sol/fetch",
        head_sha=head, mode="workspace-write", status="done", owned_paths=["delivered.txt"],
        worktree_dirty_on_exit=False, commits_ahead=1, push_state="pushed",
    )
    with git.ownership_git(record) as run:
        present = set(run("cat-file", "--batch-all-objects", "--batch-check=%(objectname)").split())
        shallow = run("rev-parse", "--is-shallow-repository")
    assert {base, head} <= present
    assert old_blobs.isdisjoint(present)
    assert run_git(tree, "rev-parse", "HEAD:delivered.txt") not in present
    if shape == "linear":
        assert shallow == "true"
        assert old_commits.isdisjoint(present)
        expected = ("done", None)
    else:
        assert shallow == "false"
        expected = ("no_deliverable", "outside_owned_paths: outside.txt")
    worker._enforce_delivery(record)
    assert (record["status"], record.get("error")) == expected


def test_ownership_walk_falls_back_to_full_history_when_tips_predate_skewed_task_base(tmp_path, monkeypatch):
    """Clock skew: a future-dated task base must not reject a valid delivery.

    With both remote tips dated before the cutoff, Git selects no commits for --shallow-since and
    aborts the bounded fetch. The walk must take the full-history fallback and apply the ownership
    rules to it.
    """
    remote, tree = tmp_path / "remote.git", tmp_path / "tree"
    run_git(tmp_path, "init", "--bare", str(remote))
    run_git(remote, "config", "uploadpack.allowFilter", "true")
    run_git(tmp_path, "init", "-b", "main", str(tree))
    run_git(tree, "config", "user.email", "stub@example.invalid")
    run_git(tree, "config", "user.name", "Stub")
    run_git(tree, "remote", "add", "origin", str(remote))
    for date, message in (("2020-01-01", "old history"), ("2099-01-01", "task base")):
        monkeypatch.setenv("GIT_COMMITTER_DATE", f"{date}T00:00:00Z")
        monkeypatch.setenv("GIT_AUTHOR_DATE", f"{date}T00:00:00Z")
        run_git(tree, "commit", "--allow-empty", "-m", message)
    base = run_git(tree, "rev-parse", "HEAD")
    monkeypatch.setenv("GIT_COMMITTER_DATE", "2020-02-01T00:00:00Z")
    monkeypatch.setenv("GIT_AUTHOR_DATE", "2020-02-01T00:00:00Z")
    run_git(tree, "commit", "--allow-empty", "-m", "base branch moves on")
    run_git(tree, "push", "origin", "main")
    run_git(tree, "checkout", "-b", "sol/skew", base)
    (tree / "delivered.txt").write_text("delivery\n")
    run_git(tree, "add", "delivered.txt")
    run_git(tree, "commit", "-m", "delivery")
    run_git(tree, "push", "origin", "HEAD")
    head = run_git(tree, "rev-parse", "HEAD")
    since = int(run_git(tree, "show", "-s", "--format=%ct", base)) - git.HISTORY_SLACK_SECONDS
    probe = tmp_path / "probe.git"
    run_git(tmp_path, "init", "--bare", str(probe))
    rejected = subprocess.run(["git", "-C", str(probe), "fetch", f"--shallow-since=@{since}", str(remote),
                               "main", "sol/skew"], capture_output=True, text=True, timeout=30)
    assert "no commits selected for shallow requests" in rejected.stderr

    def record(owned):
        return dict(
            task_id="skew", worktree_path=str(tree), worktree_remote_url=str(remote),
            worktree_base_ref="refs/remotes/origin/main", worktree_base_sha=base, worktree_branch="sol/skew",
            head_sha=head, mode="workspace-write", status="done", owned_paths=owned,
            worktree_dirty_on_exit=False, commits_ahead=1, push_state="pushed",
        )

    with git.ownership_git(record(["delivered.txt"])) as run:
        assert run("rev-parse", "--is-shallow-repository") == "false"
    for owned, expected in ((["delivered.txt"], ("done", None)),
                            (["other.txt"], ("no_deliverable", "outside_owned_paths: delivered.txt"))):
        settled = record(owned)
        worker._enforce_delivery(settled)
        assert (settled["status"], settled.get("error")) == expected


@pytest.mark.parametrize("missing", ["worktree_remote_url", "git-binary", "scratch", "remote-tip"])
def test_missing_ownership_protection_fails_closed(delivery_settle, monkeypatch, missing):
    record, settle = delivery_settle
    record = settle("pushed")
    if missing == "git-binary":
        monkeypatch.setattr(git, "GIT_BINARY", None)
    elif missing == "scratch":
        monkeypatch.setattr(git, "allocate", Mock(side_effect=worker.TaskScratchError("unavailable")))
    elif missing == "remote-tip":
        record["head_sha"] = "0" * 40
    else:
        record.pop(missing)
    worker._enforce_delivery(record)
    assert (record["status"], record["error"]) == ("no_deliverable",
        "owned_paths_verification_failed: " + {
            "worktree_remote_url": "record field 'worktree_remote_url' missing", "git-binary": "system Git unavailable",
            "scratch": "TaskScratchError", "remote-tip": "remote delivery tip does not match snapshot"}[missing])


@pytest.mark.parametrize("remote_available", [True, False])
def test_delivery_dirty_same_head_cannot_report_pushed_or_unknown(sandbox, remote_available):
    """Uncommitted work is unpushed even when HEAD matches origin or origin cannot be read."""
    record = sandbox.settle(sandbox.dispatch("pushed", "--mode", "workspace-write"))
    worktree = Path(record["cwd"])
    # Settlement removed the published worktree; re-attach it at the same head to probe a dirty tree.
    assert record["worktree_disposition"] == "removed"
    run_git(sandbox.repo, "worktree", "add", "-b", record["worktree_branch"], str(worktree), record["head_sha"])
    (worktree / "delivered.txt").write_text("uncommitted delivery\n")
    if not remote_available:
        run_git(worktree, "remote", "set-url", "origin", str(sandbox.tasks / "missing-remote"))
    probe = TaskSpec(
        record["task_id"],
        "codex",
        "echo",
        None,
        "workspace-write",
        worktree,
        Path(record["prompt_file"]),
        Path(record["result_file"]),
    )
    assert git.snapshot_delivery(probe, record) == {
        "head_sha": record["head_sha"],
        "remote_head_sha": record["head_sha"] if remote_available else None,
        "remote_ref": f"refs/heads/{record['worktree_branch']}" if remote_available else None,
        "publish_branch": None,
        "push_state": "unpushed",
        "push_state_reason": "dirty_worktree",
        "commits_ahead": 1,
        "worktree_dirty_on_exit": True,
    }
