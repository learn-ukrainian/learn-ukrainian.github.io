#!/usr/bin/env python3
"""Sol PR-L: dry retention plan engine.

Builds a content-addressed retention plan from the lane disk scanner and
optional home-session hints. It never mutates anything: the dispatcher removes
each task's own worktree when the task settles (FR-01b), so the plan carries no
worktree removal candidates.

Usage::

    .venv/bin/python scripts/hygiene/retention_engine.py plan
    .venv/bin/python scripts/hygiene/retention_engine.py latest
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import stat
import sys
from dataclasses import asdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PLAN_DIR = REPO_ROOT / "batch_state" / "fleet-comms" / "retention"
DEFAULT_OBSERVATION_LOG = DEFAULT_PLAN_DIR / "gate5-observation-log.json"
DEFAULT_ARCHIVE_ROOT = Path.home() / "Library" / "Application Support" / "learn-ukrainian" / "retention-archives"
GATE5_TARGET_DAYS = 7

# Ensure repo scripts/ is importable when invoked as a file path.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.hygiene.lane_disk_retention import (
    scan_dispatch_worktrees,
    scan_home_session_hints,
)
from scripts.orchestration.reap_worktrees import primary_checkout_root, resolve_repo_root
from scripts.path_safety import assert_delete_target

EXIT_OK = 0
EXIT_USAGE = 2


def _unlink_temp_file(
    root_fd: int,
    name: str,
    *,
    root: Path,
    expected_dev: int,
    expected_ino: int,
) -> None:
    """Unlink one proven regular-file child of the temp root, by descriptor.

    Refuses identity drift, foreign ownership, extra hard links, a device
    change and bind-mount targets. In a sticky temp directory only the owner
    can replace the entry between this check and ``unlinkat``, and the owner
    is the sweeping user.
    """
    from scripts.common.task_scratch import ContainmentError, mount_points

    mounts = mount_points()
    if mounts is None:
        raise ContainmentError("mount information unavailable (/proc/self/mountinfo); refusing to delete")
    if str(root / name) in mounts:
        raise ContainmentError(f"{name!r} is a mount point")
    info = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode):
        raise ContainmentError(f"{name!r} is not a regular file")
    if (info.st_dev, info.st_ino) != (expected_dev, expected_ino):
        raise ContainmentError(f"{name!r} no longer matches its recorded device/inode")
    if info.st_uid != os.geteuid():
        raise ContainmentError(f"{name!r} is not owned by uid {os.geteuid()}")
    if info.st_nlink != 1:
        raise ContainmentError(f"{name!r} has other hard links")
    if info.st_dev != os.fstat(root_fd).st_dev:
        raise ContainmentError(f"{name!r} sits on a different device than the temp root")
    os.unlink(name, dir_fd=root_fd)


def reap_attributed_temp(
    path: Path,
    *,
    temp_root: Path,
    repo_root: Path,
    expected_dev: int,
    expected_ino: int,
) -> None:
    """Use the common descriptor-safe scratch reaper for a proven legacy child.

    The caller owns attribution, age and live-process rechecks. This layer
    enforces direct-child containment and recorded identity without introducing
    another recursive deletion implementation. Directories go through the
    task-scratch tree remover; a regular file (unattributed scratch, #9737)
    is unlinked by descriptor after the same identity checks.
    """
    from scripts.common.task_scratch import _DIR_OPEN_FLAGS, _remove_invocation_dir

    if temp_root.is_symlink() or not temp_root.is_dir():
        raise ValueError("temporary root is not a plain directory")
    root = temp_root.resolve(strict=True)
    if path.parent != root or path.is_symlink():
        raise ValueError("temporary target must be a plain direct child")
    target = assert_delete_target(path, repo_root=repo_root, approved_temp_roots=(root,))
    if target != path:
        raise ValueError("temporary target changed during containment check")
    root_fd = os.open(root, _DIR_OPEN_FLAGS)
    try:
        if stat.S_ISREG(os.stat(path.name, dir_fd=root_fd, follow_symlinks=False).st_mode):
            _unlink_temp_file(
                root_fd,
                path.name,
                root=root,
                expected_dev=expected_dev,
                expected_ino=expected_ino,
            )
            return
        _remove_invocation_dir(
            root_fd,
            path.name,
            namespace=root,
            expected_dev=expected_dev,
            expected_ino=expected_ino,
        )
    finally:
        os.close(root_fd)


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def plan_digest(plan_body: dict[str, Any]) -> str:
    """SHA-256 over the plan body excluding volatile envelope fields."""
    body = {k: v for k, v in plan_body.items() if k not in {"created_at", "digest", "plan_path", "receipt"}}
    return hashlib.sha256(_canonical_json(body).encode("utf-8")).hexdigest()


def build_plan(
    *,
    repo_root: Path,
    archive_root: Path,
    stale_hours: float = 72.0,
    include_home: bool = False,
) -> dict[str, Any]:
    """Assemble a dry retention plan (zero mutations)."""
    repo_root = repo_root.resolve()
    primary = primary_checkout_root(repo_root)

    scanner = scan_dispatch_worktrees(repo_root=primary, stale_hours=stale_hours)
    home = scan_home_session_hints() if include_home else []

    candidates = {
        "scanner_stale": [asdict(w) for w in scanner if w.recommendation != "ok"],
        "home_sessions": home,
    }
    plan: dict[str, Any] = {
        "schema": "fleet-comms.retention.plan.v1",
        "mode": "dry-run",
        "created_at": _utc_now(),
        "repo_root": str(primary),
        "archive_root": str(archive_root.expanduser()),
        "policy": {
            "stale_hours": float(stale_hours),
            "include_home": include_home,
            "session_stream_history_excluded": True,
        },
        "candidates": candidates,
        "counts": {
            "scanner_stale": len(candidates["scanner_stale"]),
            "home_sessions": len(home),
        },
        "mutations": 0,
    }
    plan["digest"] = plan_digest(plan)
    return plan


def write_plan(plan: dict[str, Any], plan_dir: Path) -> Path:
    plan_dir.mkdir(parents=True, exist_ok=True)
    stamp = plan["created_at"].replace(":", "").replace("-", "")
    path = plan_dir / f"plan-{stamp}-{plan['digest'][:12]}.json"
    latest = plan_dir / "latest.json"
    text = json.dumps(plan, indent=2, sort_keys=True, default=str) + "\n"
    path.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    plan["plan_path"] = str(path)
    return path


def _gate5_ready_for_apply_go(
    days: list[str],
    *,
    target_days: int,
    now_utc: str,
) -> bool:
    """True when the trailing ``target_days`` labels are contiguous and fresh.

    Sparse multi-year samples must not report ready (CF #5667 P1). Latest day
    must be within 1 calendar day of ``now_utc``.
    """
    if target_days < 1:
        return False
    try:
        parsed = sorted({date.fromisoformat(d) for d in days})
        today = date.fromisoformat(now_utc[:10])
    except ValueError:
        return False
    if len(parsed) < target_days:
        return False
    latest = parsed[-1]
    if (today - latest) > timedelta(days=1):
        return False
    tail = parsed[-target_days:]
    return all((tail[i] - tail[i - 1]).days == 1 for i in range(1, len(tail)))


def record_gate5_observation(
    plan: dict[str, Any],
    *,
    plan_path: Path,
    log_path: Path = DEFAULT_OBSERVATION_LOG,
    target_days: int = GATE5_TARGET_DAYS,
) -> dict[str, Any]:
    """Append Gate 5 dry-run evidence. One calendar day (UTC) per unique day label.

    Does **not** arm apply. ``apply_armed`` stays false until an explicit operator
    GO after ``target_days`` *contiguous* observation days (Sol Gate 5).
    """
    day = str(plan.get("created_at") or _utc_now())[:10]
    entry = {
        "file": plan_path.name,
        "created_at": plan.get("created_at"),
        "digest": plan.get("digest"),
        "mode": plan.get("mode", "dry-run"),
        "mutations": int(plan.get("mutations") or 0),
        "scanner_stale": int((plan.get("counts") or {}).get("scanner_stale") or 0),
    }

    log_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = log_path.with_suffix(log_path.suffix + ".lock")
    # Exclusive lock around read-modify-write (CF concurrent-plan safety).
    with lock_path.open("a+", encoding="utf-8") as lock_fh:
        try:
            import fcntl

            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX)
        except (ImportError, OSError):
            pass  # Windows / exotic FS: best-effort without lock

        log: dict[str, Any]
        if log_path.is_file():
            try:
                raw = json.loads(log_path.read_text(encoding="utf-8"))
                log = raw if isinstance(raw, dict) else {}
            except (OSError, json.JSONDecodeError, UnicodeError):
                log = {}
        else:
            log = {}

        days = [str(d) for d in (log.get("observation_days_recorded") or []) if d]
        if day not in days:
            days.append(day)
        days = sorted(set(days))

        plans = list(log.get("plans") or [])
        if not any(
            isinstance(p, dict) and p.get("file") == entry["file"] and p.get("digest") == entry["digest"] for p in plans
        ):
            plans.append(entry)

        now = _utc_now()
        ready = _gate5_ready_for_apply_go(days, target_days=target_days, now_utc=now)

        log.update(
            {
                "schema": "fleet-comms.retention.gate5-observation.v1",
                "updated_at": now,
                "policy_note": (
                    f"{target_days}d contiguous observation before scheduled apply; "
                    "apply OFF until contiguous days + recent sample + operator GO"
                ),
                "apply_armed": False,
                "observation_days_recorded": days,
                "days_count": len(days),
                "target_days": target_days,
                "plans": plans[-50:],  # bound growth
                "ready_for_apply_go": ready,
            }
        )
        payload = json.dumps(log, indent=2, sort_keys=True, default=str) + "\n"
        tmp_path = log_path.with_suffix(log_path.suffix + f".tmp.{os.getpid()}")
        try:
            tmp_path.write_text(payload, encoding="utf-8")
            os.replace(tmp_path, log_path)
        finally:
            if tmp_path.exists():
                with contextlib.suppress(OSError, ValueError):
                    # Observation log lives under batch_state/fleet-comms/, not
                    # batch_state/tmp/ — approve only the log's parent directory.
                    guarded = assert_delete_target(
                        tmp_path,
                        repo_root=REPO_ROOT,
                        approved_temp_roots=(log_path.parent,),
                    )
                    guarded.unlink()
        try:
            import fcntl

            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)
        except (ImportError, OSError):
            pass
    return log


def cmd_plan(args: argparse.Namespace) -> int:
    try:
        root = resolve_repo_root(Path(args.repo_root).resolve() if args.repo_root else None)
    except RuntimeError:
        root = Path(args.repo_root or REPO_ROOT).resolve()
    plan = build_plan(
        repo_root=root,
        archive_root=Path(args.archive_root),
        stale_hours=args.stale_hours,
        include_home=args.include_home,
    )
    plan_dir = Path(args.plan_dir)
    path = write_plan(plan, plan_dir)
    observation = record_gate5_observation(
        plan,
        plan_path=path,
        log_path=plan_dir / "gate5-observation-log.json",
    )
    out = {
        **plan,
        "plan_path": str(path),
        "gate5_observation": {
            "days_count": observation.get("days_count"),
            "target_days": observation.get("target_days"),
            "ready_for_apply_go": observation.get("ready_for_apply_go"),
            "apply_armed": observation.get("apply_armed"),
            "log_path": str(plan_dir / "gate5-observation-log.json"),
        },
    }
    sys.stdout.write(json.dumps(out, indent=2, sort_keys=True, default=str) + "\n")
    return EXIT_OK


def cmd_latest(args: argparse.Namespace) -> int:
    latest = Path(args.plan_dir) / "latest.json"
    if not latest.is_file():
        sys.stdout.write(
            json.dumps(
                {
                    "schema": "fleet-comms.retention.plan.v1",
                    "missing": True,
                    "plan_dir": str(Path(args.plan_dir)),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        return EXIT_OK
    sys.stdout.write(latest.read_text(encoding="utf-8"))
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Write a dry, digest-stamped retention plan from the lane disk scanner; it never mutates.\n"
            "Use for dispatch-worktree retention evidence; not for temp scratch (use scripts.hygiene.tmp_sweep)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/hygiene/retention_engine.py plan\n"
            "  .venv/bin/python scripts/hygiene/retention_engine.py latest\n"
            "Outputs: plan writes plan-<stamp>-<digest>.json, latest.json and the Gate 5 observation log under "
            "--plan-dir; every subcommand prints JSON to stdout.\n"
            "Exit codes: 0 success; 2 invalid usage.\n"
            "Related: Sol PR-L retention Gate 5; #9737; docs/runbooks/tmp-retention.md; "
            "scripts/hygiene/lane_disk_retention.py."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="{plan,latest}")

    plan = sub.add_parser(
        "plan",
        help="Write a dry retention plan and digest; never mutates worktrees.",
        description="Write a content-addressed dry retention plan and record a Gate 5 observation day.",
    )
    plan.add_argument(
        "--repo-root",
        default=None,
        help="Repository whose primary checkout is planned (default: this checkout; example: .).",
    )
    plan.add_argument(
        "--plan-dir",
        type=Path,
        default=DEFAULT_PLAN_DIR,
        help="Directory for plan files and the observation log (default: batch_state/fleet-comms/retention).",
    )
    plan.add_argument(
        "--archive-root",
        type=Path,
        default=DEFAULT_ARCHIVE_ROOT,
        help="Archive destination recorded in the plan (default: per-user retention-archives directory).",
    )
    plan.add_argument(
        "--stale-hours",
        type=float,
        default=72.0,
        help="Lane-scanner staleness threshold in hours (default: 72; example: 48).",
    )
    plan.add_argument(
        "--include-home",
        action="store_true",
        help="Also list home-directory session hints (default: off; never deleted).",
    )
    plan.set_defaults(func=cmd_plan)

    latest = sub.add_parser(
        "latest",
        help="Print the latest plan JSON, or a 'missing' marker.",
        description="Print latest.json from the plan directory, or a JSON 'missing' marker when absent.",
    )
    latest.add_argument(
        "--plan-dir",
        type=Path,
        default=DEFAULT_PLAN_DIR,
        help="Directory holding latest.json (default: batch_state/fleet-comms/retention).",
    )
    latest.set_defaults(func=cmd_latest)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
