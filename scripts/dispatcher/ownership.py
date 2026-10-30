"""The owned-path rule for a dispatched write task's delivery, and its commit and push check.

Settlement (``worker._enforce_delivery``) is the authority: it refuses a delivery whose commits
touch a path outside the task's owned paths. The commit and push hooks run the same rule early,
so the worker learns of an outside path while it can still drop it (#12113). The hooks never
replace settlement and never widen the owned paths.

Usage from the tracked hooks, with the dispatched task's id in ``LEARN_UKRAINIAN_DISPATCH_TASK_ID``::

    python -m scripts.dispatcher.ownership --worktree ROOT staged
    python -m scripts.dispatcher.ownership --worktree ROOT push < git-pre-push-updates
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path

TASK_ID_ENV = "LEARN_UKRAINIAN_DISPATCH_TASK_ID"
_ZERO = frozenset("0")


def outside_owned(paths: Iterable[str], owned: Sequence[str]) -> list[str]:
    """The changed paths that no owned path covers, sorted and without repeats."""
    from scripts.guardrails.delegate_ownership import path_is_owned

    return sorted(path for path in set(paths) if path and not path_is_owned(path, owned))


def delivered_paths(run: Callable[..., str], head_sha: str, base_sha: str, start_sha: str, *,
                    commits_expected: bool = False) -> list[str]:
    """Every path the task's own commits touch, as settlement reads them.

    The range is ``head`` minus everything reachable from the base or the task's start. Remerge
    diffs isolate edits made during a merge from clean upstream changes; older Git and octopus
    merges cannot prove the absence of resolution edits, so they are refused.
    """
    merge_base = run("merge-base", head_sha, base_sha)
    revision_range = (head_sha, "--not", merge_base, start_sha)
    if commits_expected and not run("rev-list", "--max-count=1", *revision_range):
        raise ValueError("empty ownership range with recorded commits ahead")
    version = tuple(int(part) for part in run("version").split()[2].split(".")[:2])
    remerge = version >= (2, 36)
    paths = run(
        "log", "--format=", "--name-only", "-z", "-r", "--no-renames", "--root",
        "--remerge-diff" if remerge else "--cc", *revision_range, strip=False,
    ).split("\0")
    if run("rev-list", "--min-parents=3" if remerge else "--min-parents=2", *revision_range):
        raise ValueError("merge resolution paths cannot be verified")
    return paths


def failure_detail(exc: Exception) -> str:
    """What stopped an ownership check: the failing Git step, or the check's own refusal."""
    if isinstance(exc, subprocess.TimeoutExpired):
        return f"git {exc.cmd[1]} timed out"
    if isinstance(exc, subprocess.CalledProcessError):
        return f"git {exc.cmd[1]} failed"
    if isinstance(exc, ValueError):
        return str(exc)
    if isinstance(exc, KeyError):
        return f"record field {exc} missing"
    return type(exc).__name__


def _local_git(root: Path) -> Callable[..., str]:
    def run(*args: str, strip: bool = True) -> str:
        output = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True,
                                check=True, timeout=30).stdout
        return output.strip() if strip else output

    return run


def _task_record(root: Path) -> dict | None:
    """The dispatched write task this worktree belongs to, or None when no owned-path rule applies."""
    from scripts.dispatcher import store

    task_id = os.environ.get(TASK_ID_ENV, "")
    if not task_id:
        return None
    record = store.read(task_id)
    worktree = record.get("worktree_path")
    # The task id is inherited by every process the worker starts; only its own worktree is bound.
    if not worktree or Path(worktree).resolve() != root.resolve():
        return None
    if record.get("mode") == "read-only" or not record.get("owned_paths"):
        return None
    return record


def _staged_paths(run: Callable[..., str]) -> list[str]:
    # A merge commit's staged diff holds the clean upstream changes too; the push check reads the
    # merge's own resolution edits with a remerge diff instead.
    if Path(run("rev-parse", "--path-format=absolute", "--git-path", "MERGE_HEAD")).exists():
        return []
    return run("diff", "--cached", "--name-only", "-z", "--no-renames", strip=False).split("\0")


def _pushed_paths(run: Callable[..., str], record: dict, updates: str) -> list[str]:
    base_sha = run("rev-parse", "--verify", f"{record['worktree_base_ref']}^{{commit}}")
    start_sha = record.get("worktree_start_sha", record["worktree_base_sha"])
    paths: list[str] = []
    for line in updates.splitlines():
        fields = line.split()
        if len(fields) != 4 or not fields[2].startswith("refs/heads/") or set(fields[1]) <= _ZERO:
            continue
        paths += delivered_paths(run, fields[1], base_sha, start_sha)
    return paths


def _refusal(stage: str, record: dict, outside: list[str]) -> str:
    from scripts.guardrails.delegate_ownership import sanitize_for_display
    from scripts.secret_redactor import redact_text

    def shown(value: str) -> str:
        return sanitize_for_display(redact_text(value))

    action = "commit" if stage == "staged" else "push"
    drop = ("unstage and restore those paths, then commit again" if stage == "staged" else
            "rewrite the branch so no commit touches those paths; a revert commit still counts")
    lines = [
        f"owned-path check refused this {action} for task {shown(record['task_id'])}.",
        "Its commits change paths outside the task's owned paths:",
        *(f"  - {shown(path)}" for path in outside[:50]),
        *([f"  ... and {len(outside) - 50} more"] if len(outside) > 50 else []),
        "Owned paths: " + ", ".join(shown(path) for path in record["owned_paths"]),
        "Settlement refuses any delivery that touches these paths. Resolve it one of two ways:",
        f"  1. Drop the change: {drop}.",
        "  2. Stop and report the path you need to the coordinator that dispatched this task. It can answer, "
        "or start a new task with wider owned paths; it cannot widen this one.",
        "Never widen the owned paths yourself or bypass this hook.",
    ]
    if stage == "push":
        lines.append("If a listed path came from a base merge, run `git fetch origin` and push again.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--worktree", type=Path, required=True, help="the worktree being committed or pushed")
    parser.add_argument("stage", choices=("staged", "push"), help="what to check: the index, or pushed commits")
    args = parser.parse_args(argv)
    if not os.environ.get(TASK_ID_ENV):
        return 0
    try:
        record = _task_record(args.worktree)
        if record is None:
            return 0
        run = _local_git(args.worktree)
        paths = (_staged_paths(run) if args.stage == "staged" else
                 _pushed_paths(run, record, sys.stdin.read()))
        outside = outside_owned(paths, record["owned_paths"])
    except (OSError, ValueError, KeyError, TypeError, IndexError, subprocess.SubprocessError) as exc:
        # Settlement stays the authority, so an early check that cannot run never blocks the work.
        print(f"owned-path check skipped ({failure_detail(exc)}); settlement still checks the delivery.",
              file=sys.stderr)
        return 0
    if not outside:
        return 0
    print(_refusal(args.stage, record, outside), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
