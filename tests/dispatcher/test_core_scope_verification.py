"""Scope-verification failure, private ownership git and merge-resolution containment."""

import json
import subprocess
from pathlib import Path

import pytest

from scripts.dispatcher import git, worker
from tests.dispatcher.conftest import run_git


@pytest.mark.parametrize("status", ["done", "failed", "cancelled", "timeout", "crashed"])
@pytest.mark.parametrize("command", ["fetch", "merge-base", "version", "rev-list", "log"])
def test_scope_verification_failure_only_rejects_success(delivery_settle, monkeypatch, status, command):
    record, settle = delivery_settle
    record = settle("pushed")
    record.update(status=status, error="original cause")
    original = git._verification_git
    def broken(path, *args, **kwargs):
        if args[0] == command:
            raise subprocess.CalledProcessError(1, ["git", command])
        return original(path, *args, **kwargs)
    monkeypatch.setattr(git, "_verification_git", broken)
    failures = []
    original_cause = worker._verification_cause

    def diagnostic_cause(exc):
        origins = []
        frame = exc.__traceback__
        while frame is not None:
            origins.append((Path(frame.tb_frame.f_code.co_filename).name,
                            frame.tb_frame.f_code.co_name, frame.tb_lineno))
            frame = frame.tb_next
        failures.append({"type": type(exc).__name__, "origins": origins,
                         "filename": getattr(exc, "filename", None),
                         "filename2": getattr(exc, "filename2", None)})
        return original_cause(exc)

    monkeypatch.setattr(worker, "_verification_cause", diagnostic_cause)
    worker._enforce_delivery(record)
    assert record["status"] == ("no_deliverable" if status == "done" else status), failures
    assert record["error"] == (f"owned_paths_verification_failed: git {command} failed" if status == "done" else "original cause"), failures


def test_private_ownership_git_does_not_start_background_maintenance(delivery_settle, monkeypatch, tmp_path):
    """Defect class: a disposable Git namespace starts writers that outlive its fetch."""
    _, settle = delivery_settle
    record = settle("pushed")
    trace = tmp_path / "verification-trace.json"
    original_run = subprocess.run

    def traced_run(argv, *args, **kwargs):
        if argv[0] == git.GIT_BINARY and any(str(arg).startswith("--git-dir=") for arg in argv):
            kwargs["env"] = {**kwargs["env"], "GIT_TRACE2_EVENT": str(trace)}
        return original_run(argv, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", traced_run)
    with git.ownership_git(record) as run:
        assert run("rev-parse", "refs/heads/delivery") == record["head_sha"]
    complete, _, _ = trace.read_text().rpartition("\n")
    events = [json.loads(line) for line in complete.splitlines()]
    assert any(event.get("event") == "start" and "fetch" in event.get("argv", []) for event in events)
    maintenance = [event["argv"] for event in events
                   if event.get("event") == "child_start" and "maintenance" in event.get("argv", [])]
    assert maintenance == []


@pytest.mark.parametrize("history", ["conflict", "no-commit", "unrelated", "parentless", "clean"])
def test_merge_resolution_and_root_paths_cannot_escape_scope(sandbox, delivery_settle, history, monkeypatch):
    record, settle = delivery_settle
    tree = Path(record["cwd"])
    branch = record["worktree_branch"]
    if history in {"unrelated", "parentless"}:
        run_git(tree, "checkout", "--orphan", "new-root")
        run_git(tree, "read-tree", "--empty")
        (tree / "outside.txt").write_text("root addition\n")
        run_git(tree, "add", "outside.txt")
        run_git(tree, "commit", "-m", "parentless outside addition")
        if history == "unrelated":
            run_git(tree, "checkout", branch)
            run_git(tree, "merge", "--allow-unrelated-histories", "--no-edit", "new-root")
        else:
            # Keep the parentless commit as HEAD's first-parent ancestor.
            run_git(tree, "merge", "--allow-unrelated-histories", "--no-edit", branch)
            run_git(tree, "branch", "-f", branch, "HEAD")
            run_git(tree, "checkout", branch)
    else:
        (sandbox.repo / "outside.txt").write_text("upstream\n")
        run_git(sandbox.repo, "add", "outside.txt")
        run_git(sandbox.repo, "commit", "-m", "upstream outside path")
        if history == "conflict":
            (tree / "outside.txt").write_text("worker conflict\n")
            run_git(tree, "add", "outside.txt")
            run_git(tree, "commit", "-m", "worker side")
            # This models a commit already present at dispatch. Only the merge is new.
            record["worktree_base_sha"] = run_git(tree, "rev-parse", "HEAD")
        else:
            run_git(tree, "commit", "--allow-empty", "-m", "worker side")
        merge = subprocess.run(["git", "-C", str(tree), "merge", "--no-commit", "main"],
                               capture_output=True, text=True, timeout=30)
        assert merge.returncode == (1 if history == "conflict" else 0)
        if history != "clean":
            (tree / "outside.txt").write_text("worker merge edit\n")
            run_git(tree, "add", "outside.txt")
        run_git(tree, "commit", "--no-edit")
    run_git(sandbox.repo, "push", "origin", "main:release")
    # A new owned commit makes the supervisor exercise delivery after the merge.
    result = settle("pushed")
    assert result["status"] == ("done" if history == "clean" else "no_deliverable")
    assert result["error"] == (None if history == "clean" else "outside_owned_paths: outside.txt")
    original = git._verification_git
    monkeypatch.setattr(git, "_verification_git", lambda path, command, *args, **kw:
                        "git version 2.35.0" if command == "version" else original(path, command, *args, **kw))
    result.update(status="done", error=None)
    worker._enforce_delivery(result)
    assert (result["status"], result["error"]) == ("no_deliverable", "owned_paths_verification_failed: merge resolution paths cannot be verified")
