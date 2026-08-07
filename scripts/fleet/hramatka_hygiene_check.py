#!/usr/bin/env python3
"""Read-only hygiene/closeout gate for Hramatka driver handoffs.

Verifies the invariants PR-1 (`docs/runbooks/hramatka-driver-queue.md`) put in
writing: the public epic (#4542) stays charter-only (no live checklist) and
keeps its pointer to the private priority board (#349); the local dispatch
tree carries no orphaned worktrees for already-finished tasks; disk headroom
is above the configured high-water mark. It never mutates GitHub or the
filesystem — this is PR-4 of the stream-hygiene package
(`conversation_7b6241377cd44c7ea5265da5c85efb5c`); it does not implement or
import the PR-2 scope gate (`hramatka_scope_gate.py`) or the PR-3 reaper
(`post_task_reap.py`) bodies, by design, so this gate has no hard dependency
on either PR's merge order.

Usage:
  .venv/bin/python -m scripts.fleet.hramatka_hygiene_check

Exit codes:
  0  verified — every check ran and came back clean
  1  stale    — at least one check ran and found a real problem
  2  unknown  — GitHub (public epic or private board) was unreachable; a
                driver must never read this as a clean handoff

JSON receipt (stdout): policy_version, status, epic_charter_ok,
queue_pointer_ok, zombie_worktrees, df, plus supporting detail
(reasons, zombie_worktrees_detectable, high_water_percent).
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from collections.abc import Callable
from enum import StrEnum
from pathlib import Path
from typing import Any

from scripts.common.repo_root import main_checkout_root

REPO_ROOT = main_checkout_root(Path(__file__).resolve().parents[2])

POLICY_VERSION = "hramatka-hygiene-v1"

PUBLIC_REPOSITORY = "learn-ukrainian/learn-ukrainian.github.io"
PUBLIC_EPIC = 4542
PRIVATE_REPOSITORY = "learn-ukrainian/learn-ukrainian-infra-private"
PRIVATE_BOARD = 349

DEFAULT_HIGH_WATER_PERCENT = 95
GH_TIMEOUT_SECONDS = 15.0

_TASKS_DIR = REPO_ROOT / "batch_state" / "tasks"
_DISPATCH_WORKTREES_ROOT = REPO_ROOT / ".worktrees" / "dispatch"

# Same terminal-status vocabulary as post_task_reap.py / the drive-epic
# settle-loop contract, duplicated (not imported) so this gate has no import
# dependency on the PR-3 reaper module.
_TERMINAL_STATUSES = frozenset(
    {
        "done",
        "failed",
        "timeout",
        "rate_limited",
        "cancelled",
        "crashed",
        "dry_run",
        "needs_finalize",
        "no_deliverable",
    }
)

_TASK_LIST_ITEM_RE = re.compile(r"(?im)^[ \t]*[-*][ \t]+\[([ xX])\][ \t]+\S")


class Status(StrEnum):
    """The only overall dispositions this gate can emit."""

    VERIFIED = "verified"
    STALE = "stale"
    UNKNOWN = "unknown"


_EXIT_CODES: dict[Status, int] = {
    Status.VERIFIED: 0,
    Status.STALE: 1,
    Status.UNKNOWN: 2,
}


class GhUnavailable(RuntimeError):
    """GitHub did not return a trusted issue observation."""


IssueReader = Callable[[str, int], dict[str, Any]]


def _gh_issue(
    repo: str,
    number: int,
    *,
    timeout: float = GH_TIMEOUT_SECONDS,
    cwd: Path = REPO_ROOT,
) -> dict[str, Any]:
    """Read one repo-qualified issue's number/body/state through `gh api`.

    Failures are deliberately normalized to ``GhUnavailable`` — callers must
    not distinguish "issue doesn't exist" from "API unreachable" and allow a
    verified-clean result on a guess.
    """
    try:
        proc = subprocess.run(
            [
                "gh",
                "api",
                f"repos/{repo}/issues/{number}",
                "--jq",
                "{number: .number, body: .body, state: .state}",
            ],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GhUnavailable(f"gh api unreachable for {repo}#{number}") from exc
    if proc.returncode != 0:
        raise GhUnavailable(f"gh api failed for {repo}#{number}")
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise GhUnavailable(f"gh api returned malformed JSON for {repo}#{number}") from exc
    if not isinstance(data, dict) or data.get("number") != number or not isinstance(data.get("body"), str):
        raise GhUnavailable(f"gh api response has an invalid shape for {repo}#{number}")
    return data


def _pointer_pattern(private_repo: str, private_board: int) -> re.Pattern[str]:
    short = re.escape(f"{private_repo}#{private_board}")
    long = re.escape(f"{private_repo}/issues/{private_board}")
    return re.compile(f"{short}|{long}")


def _count_task_list_items(body: str) -> tuple[int, int]:
    """Return (checked, unchecked) GitHub task-list item counts in ``body``."""
    checked = 0
    unchecked = 0
    for match in _TASK_LIST_ITEM_RE.finditer(body):
        if match.group(1).strip().lower() == "x":
            checked += 1
        else:
            unchecked += 1
    return checked, unchecked


def _registered_worktrees(repo_root: Path) -> list[Path] | None:
    """Return every registered git worktree path, or None if not detectable."""
    try:
        proc = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    paths: list[Path] = []
    for line in (proc.stdout or "").splitlines():
        if line.startswith("worktree "):
            paths.append(Path(line[len("worktree ") :].strip()).resolve())
    return paths


def _is_under_dispatch_worktrees(path: Path, dispatch_root: Path) -> bool:
    """True for paths inside dispatch_root but outside the ACP runtime subtree.

    ACP runtime-review worktrees are reaped on process-liveness, not task
    status (see post_task_reap.py) — they are out of scope for this
    task-status-driven zombie check.
    """
    try:
        rel = path.resolve().relative_to(dispatch_root.resolve())
    except ValueError:
        return False
    return rel.parts[:1] != ("acp",)


def _task_state_index(tasks_dir: Path) -> dict[Path, dict[str, Any]]:
    """Map resolved worktree path -> task state, for every readable task file."""
    index: dict[Path, dict[str, Any]] = {}
    if not tasks_dir.is_dir():
        return index
    for path in sorted(tasks_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        raw = data.get("worktree_path") or data.get("cwd")
        if not raw:
            continue
        try:
            resolved = Path(str(raw)).resolve()
        except OSError:
            continue
        index[resolved] = data
    return index


def _detect_zombie_worktrees(
    *,
    repo_root: Path,
    dispatch_root: Path,
    tasks_dir: Path,
) -> tuple[list[dict[str, Any]], bool]:
    """Return (zombies, detectable). Read-only: never removes anything.

    A worktree is flagged only when it is a registered dispatch worktree
    whose bound task state is found and terminal — an unbound path is not
    evidence either way and is left out, matching the "if detectable"
    qualifier in the hygiene contract.
    """
    worktrees = _registered_worktrees(repo_root)
    if worktrees is None:
        return [], False

    index = _task_state_index(tasks_dir)
    zombies: list[dict[str, Any]] = []
    for worktree in worktrees:
        if not _is_under_dispatch_worktrees(worktree, dispatch_root):
            continue
        state = index.get(worktree)
        if state is None:
            continue
        status = state.get("status")
        status_str = str(status) if status is not None else None
        if status_str in _TERMINAL_STATUSES:
            zombies.append(
                {
                    "path": str(worktree),
                    "task_id": state.get("task_id") or worktree.name,
                    "status": status_str,
                }
            )
    return zombies, True


def _disk_report(path: Path, high_water_percent: int) -> dict[str, Any]:
    try:
        usage = shutil.disk_usage(path)
    except OSError as exc:
        return {
            "path": str(path),
            "error": str(exc),
            "use_percent": None,
            "high_water_percent": high_water_percent,
            "ok": None,
        }
    use_percent = round((usage.used / usage.total) * 100, 1) if usage.total else 0.0
    return {
        "path": str(path),
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "use_percent": use_percent,
        "high_water_percent": high_water_percent,
        "ok": use_percent < high_water_percent,
    }


def _receipt(
    *,
    status: Status,
    epic_charter_ok: bool | None,
    queue_pointer_ok: bool | None,
    zombie_worktrees: list[dict[str, Any]],
    zombie_worktrees_detectable: bool,
    df: dict[str, Any] | None,
    reasons: list[str],
    high_water_percent: int,
) -> dict[str, Any]:
    return {
        "policy_version": POLICY_VERSION,
        "status": status.value,
        "epic_charter_ok": epic_charter_ok,
        "queue_pointer_ok": queue_pointer_ok,
        "zombie_worktrees": zombie_worktrees,
        "zombie_worktrees_detectable": zombie_worktrees_detectable,
        "df": df,
        "high_water_percent": high_water_percent,
        "reasons": reasons,
    }


def hygiene_check(
    *,
    public_repo: str = PUBLIC_REPOSITORY,
    public_epic: int = PUBLIC_EPIC,
    private_repo: str = PRIVATE_REPOSITORY,
    private_board: int = PRIVATE_BOARD,
    high_water_percent: int = DEFAULT_HIGH_WATER_PERCENT,
    disk_path: Path = REPO_ROOT,
    repo_root: Path = REPO_ROOT,
    dispatch_worktrees_root: Path = _DISPATCH_WORKTREES_ROOT,
    tasks_dir: Path = _TASKS_DIR,
    reader: IssueReader = _gh_issue,
) -> dict[str, Any]:
    """Run every hygiene check and return the JSON receipt (never raises)."""
    reasons: list[str] = []

    try:
        epic_issue = reader(public_repo, public_epic)
    except GhUnavailable as exc:
        return _receipt(
            status=Status.UNKNOWN,
            epic_charter_ok=None,
            queue_pointer_ok=None,
            zombie_worktrees=[],
            zombie_worktrees_detectable=False,
            df=None,
            reasons=[f"public epic API unreachable: {exc}"],
            high_water_percent=high_water_percent,
        )

    body = epic_issue.get("body") or ""
    _checked, unchecked = _count_task_list_items(body)
    epic_charter_ok = unchecked == 0
    if not epic_charter_ok:
        reasons.append(f"public epic #{public_epic} still has {unchecked} live (unchecked) checkbox item(s)")

    queue_pointer_ok = bool(_pointer_pattern(private_repo, private_board).search(body))
    if not queue_pointer_ok:
        reasons.append(f"public epic #{public_epic} is missing the {private_repo}#{private_board} pointer")

    try:
        reader(private_repo, private_board)
    except GhUnavailable as exc:
        return _receipt(
            status=Status.UNKNOWN,
            epic_charter_ok=epic_charter_ok,
            queue_pointer_ok=queue_pointer_ok,
            zombie_worktrees=[],
            zombie_worktrees_detectable=False,
            df=None,
            reasons=[*reasons, f"private board API unreachable: {exc}"],
            high_water_percent=high_water_percent,
        )

    zombies, detectable = _detect_zombie_worktrees(
        repo_root=repo_root,
        dispatch_root=dispatch_worktrees_root,
        tasks_dir=tasks_dir,
    )
    if zombies:
        reasons.append(f"{len(zombies)} orphan dispatch worktree(s) bound to finished tasks")

    df = _disk_report(disk_path, high_water_percent)
    if df.get("ok") is False:
        reasons.append(f"disk use {df['use_percent']}% at or above high water {high_water_percent}%")

    status = Status.VERIFIED if not reasons else Status.STALE
    return _receipt(
        status=status,
        epic_charter_ok=epic_charter_ok,
        queue_pointer_ok=queue_pointer_ok,
        zombie_worktrees=zombies,
        zombie_worktrees_detectable=detectable,
        df=df,
        reasons=reasons,
        high_water_percent=high_water_percent,
    )


def main(argv: list[str] | None = None, *, reader: IssueReader = _gh_issue) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--public-repo", default=PUBLIC_REPOSITORY, help="owner/name of the public repo")
    parser.add_argument("--public-epic", type=int, default=PUBLIC_EPIC, help="public Hramatka epic issue number")
    parser.add_argument("--private-repo", default=PRIVATE_REPOSITORY, help="owner/name of the private repo")
    parser.add_argument("--private-board", type=int, default=PRIVATE_BOARD, help="private priority-board issue number")
    parser.add_argument(
        "--high-water-percent",
        type=int,
        default=DEFAULT_HIGH_WATER_PERCENT,
        help="disk Use%% at/above which the gate reports stale",
    )
    parser.add_argument("--disk-path", type=Path, default=REPO_ROOT, help="path whose filesystem df is reported")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT, help="primary checkout used for git worktree list")
    parser.add_argument(
        "--dispatch-worktrees-root",
        type=Path,
        default=_DISPATCH_WORKTREES_ROOT,
        help=".worktrees/dispatch root to scan for zombies",
    )
    parser.add_argument("--tasks-dir", type=Path, default=_TASKS_DIR, help="batch_state/tasks directory")
    args = parser.parse_args(argv)

    receipt = hygiene_check(
        public_repo=args.public_repo,
        public_epic=args.public_epic,
        private_repo=args.private_repo,
        private_board=args.private_board,
        high_water_percent=args.high_water_percent,
        disk_path=args.disk_path,
        repo_root=args.repo_root,
        dispatch_worktrees_root=args.dispatch_worktrees_root,
        tasks_dir=args.tasks_dir,
        reader=reader,
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return _EXIT_CODES[Status(receipt["status"])]


if __name__ == "__main__":
    raise SystemExit(main())
