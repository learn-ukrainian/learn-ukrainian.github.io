#!/usr/bin/env python3
"""Run a large ad-hoc command inside a task-owned disposable scratch directory (#8738).

``run`` allocates one unique directory under ``<scratch root>/task-scratch/``,
points ``TMPDIR``/``TMP``/``TEMP`` and ``$LU_TASK_SCRATCH_DIR`` at it, executes
the command directly (no shell unless you ask for one), forwards
SIGINT/SIGTERM/SIGHUP to the command's process group, and removes the
directory once the group has exited — on success, on failure, and on
interrupt. The child's exit status is preserved.

A wrapper that dies without cleaning (SIGKILL, reboot) leaves a lease behind;
``recover`` (also run by ``scheduled_worktree_cleanup.py``) reclaims it only
after proving the recorded owner and child group dead and the lease older
than the age gate. Anything unowned, malformed, symlinked, or in use is
preserved and reported.

The scratch directory disappears after a successful run. Write anything you
need to keep into ``$LU_TASK_SCRATCH_DIR/evidence/`` and pass
``--evidence-dir`` to copy that small summary out before cleanup.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.common import task_scratch as lifecycle

ATLAS_410K_EXAMPLE = """\
Atlas 410k scale check (both steps share one scratch directory; every large
output lands under $LU_TASK_SCRATCH_DIR and is removed when the run ends):

  .venv/bin/python scripts/tools/task_scratch.py run --task-id atlas-8307-410k \\
      --evidence-dir batch_state/tmp/atlas-8307-410k-evidence -- \\
      bash -euc '
        .venv/bin/python -m scripts.benchmarks.generate_synthetic_atlas \\
            --source-db data/atlas.db --out "$LU_TASK_SCRATCH_DIR/atlas.db" \\
            --seed 8307 --target 410000
        .venv/bin/python -m scripts.atlas.export_runtime_shards \\
            --db "$LU_TASK_SCRATCH_DIR/atlas.db" \\
            --out-dir "$LU_TASK_SCRATCH_DIR/export" --verify
        mkdir -p "$LU_TASK_SCRATCH_DIR/evidence"
        cp "$LU_TASK_SCRATCH_DIR/export/atlas/current.json" "$LU_TASK_SCRATCH_DIR/evidence/"
      '

The single-quoted script runs in `bash -euc`; the $LU_TASK_SCRATCH_DIR
references are expanded by that child shell, not by your interactive shell.
Only the copied evidence survives the run.

Recovery of interrupted runs (dry-run by default; the scheduled hygiene
runner applies it):

  .venv/bin/python scripts/tools/task_scratch.py recover
  .venv/bin/python scripts/tools/task_scratch.py recover --apply
"""


def _scratch_root(value: str | None) -> Path | None:
    return Path(value).expanduser() if value else None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="task_scratch.py",
        description=__doc__,
        epilog=ATLAS_410K_EXAMPLE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser(
        "run",
        help="run a command inside a fresh task-owned scratch directory",
        description="Run COMMAND with TMPDIR and $LU_TASK_SCRATCH_DIR pointing at a private scratch "
        "directory that is removed when the command's process group exits.",
        epilog=ATLAS_410K_EXAMPLE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    run.add_argument("--task-id", required=True, help="task/issue label recorded in the lease (metadata only)")
    run.add_argument(
        "--scratch-root",
        default=None,
        help="override the fleet scratch root (default: $LU_SCRATCH_ROOT or /var/tmp/lu)",
    )
    run.add_argument("--cwd", default=None, help="working directory for the command (default: current)")
    run.add_argument(
        "--keep", action="store_true", help="never delete the scratch directory (scheduled recovery reclaims it later)"
    )
    run.add_argument(
        "--keep-on-failure", action="store_true", help="keep the scratch directory when the command exits nonzero"
    )
    run.add_argument(
        "--evidence-dir",
        default=None,
        help="copy $LU_TASK_SCRATCH_DIR/evidence/ (max 16 MiB) here before cleanup; the scratch itself is not kept",
    )
    run.add_argument(
        "--group-grace-s",
        type=float,
        default=lifecycle.DEFAULT_GROUP_GRACE_S,
        help="seconds to wait for surviving group members after the command exits before TERM/KILL escalation",
    )
    run.add_argument(
        "--kill-after-s",
        type=float,
        default=lifecycle.DEFAULT_KILL_AFTER_S,
        help="after a forwarded SIGINT/SIGTERM, seconds before the group is SIGKILLed",
    )
    run.add_argument("--json", action="store_true", help="print a JSON outcome line on stderr")
    run.add_argument("argv", nargs=argparse.REMAINDER, help="-- COMMAND [ARGS...]")

    recover = sub.add_parser(
        "recover",
        help="inventory the managed namespace and reclaim proven orphans",
        description="Dry-run by default: lists every lease with the guard that preserves it. --apply deletes "
        "only leases whose owner and child group are provably dead and which are older than the age gate.",
    )
    recover.add_argument("--apply", action="store_true", help="delete proven orphans (default: dry-run)")
    recover.add_argument("--scratch-root", default=None, help="override the fleet scratch root")
    recover.add_argument("--min-age-s", type=float, default=lifecycle.DEFAULT_MIN_AGE_S)
    recover.add_argument("--pressure-min-age-s", type=float, default=lifecycle.DEFAULT_PRESSURE_MIN_AGE_S)
    recover.add_argument("--min-free-gb", type=float, default=lifecycle.DEFAULT_MIN_FREE_GB)
    recover.add_argument("--json", action="store_true", help="print the JSON report")
    return parser


def _command_argv(raw: list[str]) -> list[str]:
    argv = list(raw)
    if argv and argv[0] == "--":
        argv = argv[1:]
    if not argv:
        raise SystemExit("task_scratch.py run: missing command after '--'")
    return argv


def _print_recovery(report: dict) -> None:
    mode = "APPLY" if report["apply"] else "DRY-RUN"
    free = report.get("free_gb")
    free_text = f"{free:.1f} GiB free" if isinstance(free, int | float) else "free unknown"
    print(
        f"task-scratch recovery [{mode}]: candidates={report['candidates']} reaped={report['reaped']} "
        f"preserved={report['preserved']} errors={report['errors']} bytes_freed={report['bytes_freed']} "
        f"min_age_s={int(report['min_age_s'])} ({free_text})"
    )
    for entry in report["entries"]:
        age = f" age={entry['age_s']}s" if entry.get("age_s") is not None else ""
        print(
            f"  {entry['action']}: {entry['name']} task={entry['task_id']} reason={entry['reason']}{age} bytes={entry['bytes']}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "recover":
        report = lifecycle.recover_orphans(
            apply=args.apply,
            root=_scratch_root(args.scratch_root),
            min_age_s=args.min_age_s,
            pressure_min_age_s=args.pressure_min_age_s,
            min_free_gb=args.min_free_gb,
        )
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            _print_recovery(report)
        return 1 if report["errors"] else 0

    command = _command_argv(args.argv)
    outcome = lifecycle.run_task(
        args.task_id,
        command,
        root=_scratch_root(args.scratch_root),
        cwd=Path(args.cwd) if args.cwd else None,
        keep=args.keep,
        keep_on_failure=args.keep_on_failure,
        evidence_dir=Path(args.evidence_dir) if args.evidence_dir else None,
        group_grace_s=args.group_grace_s,
        kill_after_s=args.kill_after_s,
    )
    if args.json:
        payload = {
            "task_id": args.task_id,
            "invocation_id": outcome.invocation_id,
            "returncode": outcome.returncode,
            "exit_status": outcome.exit_status,
            "action": outcome.action,
            "group_status": outcome.group_status,
            "interrupted_by": outcome.interrupted_by,
            "evidence": outcome.evidence,
            "detail": outcome.detail,
        }
        sys.stderr.write(json.dumps(payload, sort_keys=True) + "\n")
    return outcome.exit_status


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    raise SystemExit(main())
