#!/usr/bin/env python3
"""Lane disk-retention scanner (#4956).

Policy (operator 2026-07-11):
- Each lane cleans **its own** session stores and dispatch worktrees.
- Dispatch worktrees that are merged → reap.
- Dirty/unpushed worktrees older than **72h** → push+PR or declare abandonable.
- Sessions/logs older than **14d** → archive then delete (manual / Drive).

This script is **read-only by default** (``--dry-run``). It never deletes
another lane's uncommitted work. Use ``--json`` for machine-readable output.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WORKTREE_STALE_HOURS = 72
DEFAULT_SESSION_STALE_DAYS = 14


@dataclass(frozen=True)
class WorktreeReport:
    path: str
    branch: str
    age_hours: float
    dirty: bool
    ahead_of_remote: bool
    recommendation: str


def _git(args: list[str], *, cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    return (result.stdout or "").strip()


def scan_dispatch_worktrees(
    *,
    repo_root: Path = REPO_ROOT,
    stale_hours: float = DEFAULT_WORKTREE_STALE_HOURS,
    now: float | None = None,
) -> list[WorktreeReport]:
    """Scan ``.worktrees/dispatch/**`` for stale / dirty / merged candidates."""
    root = repo_root / ".worktrees" / "dispatch"
    if not root.is_dir():
        return []
    clock = now if now is not None else time.time()
    reports: list[WorktreeReport] = []
    for agent_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for task_dir in sorted(p for p in agent_dir.iterdir() if p.is_dir()):
            git_dir = task_dir / ".git"
            if not git_dir.exists():
                continue
            mtime = task_dir.stat().st_mtime
            age_hours = max((clock - mtime) / 3600.0, 0.0)
            branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=task_dir) or "(unknown)"
            status = _git(["status", "--porcelain"], cwd=task_dir)
            dirty = bool(status)
            ahead = False
            counts = _git(["rev-list", "--left-right", "--count", "@{u}...HEAD"], cwd=task_dir)
            if counts and "\t" in counts:
                _behind, ahead_s = counts.split("\t", 1)
                try:
                    ahead = int(ahead_s) > 0
                except ValueError:
                    ahead = False
            if age_hours < stale_hours and not dirty:
                rec = "ok"
            elif dirty and age_hours >= stale_hours:
                rec = "stale-dirty: push+PR or mark abandonable on tracking issue, then reap"
            elif ahead and age_hours >= stale_hours:
                rec = "stale-unpushed: push branch / open PR or abandon + worktree remove"
            elif age_hours >= stale_hours:
                rec = "stale-clean: candidate for worktree remove if PR merged"
            else:
                rec = "active-dirty: finish or checkpoint soon"
            reports.append(
                WorktreeReport(
                    path=str(task_dir.relative_to(repo_root)),
                    branch=branch,
                    age_hours=round(age_hours, 1),
                    dirty=dirty,
                    ahead_of_remote=ahead,
                    recommendation=rec,
                )
            )
    return reports


def scan_home_session_hints(
    *,
    stale_days: float = DEFAULT_SESSION_STALE_DAYS,
) -> list[dict[str, object]]:
    """Non-destructive size/age hints for known session roots (home only)."""
    home = Path.home()
    candidates = [
        home / ".codex",
        home / ".claude",
        home / ".cursor",
        home / ".grok",
    ]
    clock = time.time()
    out: list[dict[str, object]] = []
    for path in candidates:
        if not path.exists():
            continue
        try:
            size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        except OSError:
            size = -1
        mtime = path.stat().st_mtime
        age_days = max((clock - mtime) / 86400.0, 0.0)
        out.append(
            {
                "path": str(path),
                "size_gb": round(size / (1024**3), 2) if size >= 0 else None,
                "age_days": round(age_days, 1),
                "recommendation": (
                    f"archive sessions older than {stale_days:g}d to Drive, then delete locally"
                    if age_days >= stale_days
                    else "within retention window"
                ),
            }
        )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--stale-hours", type=float, default=DEFAULT_WORKTREE_STALE_HOURS)
    parser.add_argument("--session-stale-days", type=float, default=DEFAULT_SESSION_STALE_DAYS)
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON report")
    parser.add_argument(
        "--include-home",
        action="store_true",
        help="Also scan ~/.codex ~/.claude ~/.cursor ~/.grok size hints (read-only)",
    )
    args = parser.parse_args(argv)

    worktrees = scan_dispatch_worktrees(
        repo_root=args.repo_root,
        stale_hours=args.stale_hours,
    )
    home = scan_home_session_hints(stale_days=args.session_stale_days) if args.include_home else []

    if args.json:
        print(
            json.dumps(
                {
                    "worktrees": [asdict(w) for w in worktrees],
                    "home_sessions": home,
                    "policy": {
                        "worktree_stale_hours": args.stale_hours,
                        "session_stale_days": args.session_stale_days,
                        "mutate": False,
                    },
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    print(f"Dispatch worktrees under {args.repo_root / '.worktrees' / 'dispatch'} "
          f"(stale ≥ {args.stale_hours:g}h): {len(worktrees)}")
    for w in worktrees:
        flags = []
        if w.dirty:
            flags.append("dirty")
        if w.ahead_of_remote:
            flags.append("ahead")
        flag_s = f" [{','.join(flags)}]" if flags else ""
        print(f"  {w.path}  branch={w.branch}  age={w.age_hours}h{flag_s}")
        print(f"    → {w.recommendation}")
    if home:
        print("\nHome session roots (hints only):")
        for row in home:
            print(f"  {row['path']}  ~{row['size_gb']} GiB  age={row['age_days']}d")
            print(f"    → {row['recommendation']}")
    print(
        "\nNo files were deleted. Reap merged worktrees with "
        "`git worktree remove …` after PR merge; archive sessions to Drive per #4956."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
