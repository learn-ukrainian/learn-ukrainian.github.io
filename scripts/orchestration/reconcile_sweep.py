#!/usr/bin/env python3
"""Thin wrapper for scheduled task and claim reconciliation.

Runs:
1. `dispatch_settle release-stale` (releases write-ownership claims for inactive tasks)
2. Lazy heal path (`delegate.py status`) for running task records whose PID is dead
3. Logs a one-line summary (counts) to stdout (journal)

DEFAULT DRY-RUN: without `--apply`, only reports what would be settled.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sqlite3
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
for path in (PROJECT_ROOT, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from scripts import delegate
from scripts.guardrails.delegate_ownership import (
    OwnershipLedger,
    _task_still_active,
    default_ledger_path,
)
from scripts.orchestration import dispatch_settle


def default_task_dir(repo_root: Path | None = None) -> Path:
    root = repo_root or PROJECT_ROOT
    return root / "batch_state" / "tasks"


@dataclass
class ReconcileSweepReport:
    mode: str
    scanned_tasks: int
    zombie_tasks: list[str]
    stale_claims: list[str]
    live_tasks: list[str]
    unparseable_tasks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def summary_line(self) -> str:
        zombie_label = "zombies_crashed" if self.mode == "apply" else "zombie_tasks"
        claim_label = "stale_claims_released" if self.mode == "apply" else "stale_claims"
        summary = (
            f"reconcile-sweep: mode={self.mode} scanned_tasks={self.scanned_tasks} "
            f"{zombie_label}={len(self.zombie_tasks)} {claim_label}={len(self.stale_claims)}"
        )
        if self.unparseable_tasks:
            summary += f" unparseable_tasks={len(self.unparseable_tasks)}"
        return summary


def _parse_pid(raw_pid: Any) -> int | None:
    if isinstance(raw_pid, bool):
        return None
    if isinstance(raw_pid, int) and raw_pid > 0:
        return raw_pid
    if isinstance(raw_pid, str) and raw_pid.strip().isdigit():
        val = int(raw_pid.strip())
        if val > 0:
            return val
    return None


def _probe_stale_claims(ledger: OwnershipLedger) -> list[str]:
    """Report inactive claims without mutating the ownership ledger."""
    if not ledger.path.is_file():
        return []
    would_release: list[str] = []
    try:
        conn = ledger._connect(read_only=True)
        try:
            rows = conn.execute(
                "SELECT task_id, pid, MIN(created_at) AS created_at FROM write_claims GROUP BY task_id, pid"
            ).fetchall()
            for row in rows:
                task_id = str(row["task_id"])
                pid = row["pid"]
                pid_i = int(pid) if pid is not None else None
                created = float(row["created_at"]) if row["created_at"] is not None else None
                if not _task_still_active(task_id, pid_i, ledger.task_state_dir, created_at=created):
                    would_release.append(task_id)
        finally:
            conn.close()
    except sqlite3.OperationalError as exc:
        if "no such table: write_claims" in str(exc):
            return []
        sys.stderr.write(f"warning: error probing stale claims: {exc}\n")
    except Exception as exc:
        sys.stderr.write(f"warning: error probing stale claims: {exc}\n")
    return sorted(set(would_release))


def run_reconcile_sweep(
    *,
    apply: bool = False,
    repo_root: Path | None = None,
    task_dir: Path | None = None,
    ledger: OwnershipLedger | None = None,
) -> ReconcileSweepReport:
    root = repo_root or PROJECT_ROOT
    tdir = task_dir or default_task_dir(root)
    own_ledger = ledger or OwnershipLedger(default_ledger_path(), task_state_dir=tdir)

    # 1. Stale ownership claims reconciliation / probe
    if apply:
        stale_claims = sorted(set(dispatch_settle.release_inactive_claims(own_ledger)))
    else:
        stale_claims = _probe_stale_claims(own_ledger)

    # 2. Zombie task reconciliation / probe
    zombie_tasks: list[str] = []
    live_tasks: list[str] = []
    unparseable_tasks: list[str] = []
    task_files = sorted(tdir.glob("*.json")) if tdir.is_dir() else []
    scanned_tasks = len(task_files)

    for state_file in task_files:
        task_id = state_file.stem
        try:
            try:
                state = json.loads(state_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                unparseable_tasks.append(task_id)
                continue
            if not isinstance(state, dict):
                unparseable_tasks.append(task_id)
                continue

            task_id = str(state.get("task_id") or task_id)
            status = state.get("status")
            if status in ("running", "spawning"):
                raw_pid = state.get("pid")
                pid = _parse_pid(raw_pid)
                if pid is None:
                    unparseable_tasks.append(task_id)
                    continue

                try:
                    pid_alive = delegate._pid_alive(pid)
                except Exception:
                    unparseable_tasks.append(task_id)
                    continue

                if not pid_alive:
                    zombie_tasks.append(task_id)
                    if apply:
                        # Invoke lazy heal path via delegate.cmd_status
                        saved_tasks_dir = delegate._TASKS_DIR
                        try:
                            delegate._TASKS_DIR = tdir
                            with (
                                contextlib.redirect_stdout(io.StringIO()),
                                contextlib.redirect_stderr(io.StringIO()),
                            ):
                                delegate.cmd_status(argparse.Namespace(task_id=task_id, run_nonce=None))
                        finally:
                            delegate._TASKS_DIR = saved_tasks_dir
                else:
                    live_tasks.append(task_id)
        except Exception:
            unparseable_tasks.append(task_id)
            continue

    mode = "apply" if apply else "dry_run"
    return ReconcileSweepReport(
        mode=mode,
        scanned_tasks=scanned_tasks,
        zombie_tasks=zombie_tasks,
        stale_claims=stale_claims,
        live_tasks=live_tasks,
        unparseable_tasks=unparseable_tasks,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reconcile_sweep.py",
        description=(
            "Reconcile stale write-ownership claims and heal dead-PID zombie task records.\n"
            "Use on scheduled timer or manual sweep; do not use as a replacement for dispatch_settle on active tasks."
        ),
        epilog=(
            "Examples:\n"
            "  # Dry-run report (default — read-only inspection, zero mutations):\n"
            "  .venv/bin/python scripts/orchestration/reconcile_sweep.py\n\n"
            "  # Apply reconciliation (heal zombies and release stale claims):\n"
            "  .venv/bin/python scripts/orchestration/reconcile_sweep.py --apply\n\n"
            "  # Machine-readable JSON output:\n"
            "  .venv/bin/python scripts/orchestration/reconcile_sweep.py --json\n\n"
            "Outputs:\n"
            "  Stdout: one-line summary line (and optional JSON payload).\n"
            "  In --apply mode: updates batch_state/tasks/*.json statuses to 'crashed' via delegate.py status\n"
            "  and removes stale rows from write-ownership.sqlite3.\n\n"
            "Exit codes:\n"
            "  0 on successful sweep (in dry-run or apply mode);\n"
            "  2 on invalid CLI arguments.\n\n"
            "Related:\n"
            "  Dispatch settle: scripts/orchestration/dispatch_settle.py\n"
            "  Ownership ledger: scripts/guardrails/delegate_ownership.py\n"
            "  Systemd timer: packaging/systemd/learn-ukrainian-reconcile.timer\n"
            "  Decision: infra-private #625, issue #7584, PR #7585\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply reconciliation (mark zombies crashed and release stale claims). Default: false (dry-run report only).",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=PROJECT_ROOT,
        help="Repository root path (default: %(default)s).",
    )
    parser.add_argument(
        "--task-dir",
        type=Path,
        default=None,
        help="Task state directory (default: <repo-root>/batch_state/tasks).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON summary in addition to one-line log. Default: false.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = args.repo_root.expanduser().resolve()
    task_dir = args.task_dir.expanduser().resolve() if args.task_dir else default_task_dir(repo_root)

    report = run_reconcile_sweep(
        apply=bool(args.apply),
        repo_root=repo_root,
        task_dir=task_dir,
    )

    print(report.summary_line())
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
