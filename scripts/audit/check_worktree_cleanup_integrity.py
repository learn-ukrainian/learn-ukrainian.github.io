#!/usr/bin/env python3
"""Detect a dark or red ``com.learn-ukrainian.worktree-cleanup`` launchd job.

#6937: after the 2026-08-15 18:47 primary ``.venv`` rewrite, launchd stopped
starting the job (``Unable to get updated LWCR ... error 0x3``, exit 78) and
no receipt was written for two days. This probe is DETECTION ONLY, mirroring
``check_venv_integrity.py``:

- DETECT: the LaunchAgent is installed and either launchd last-exit is
  non-zero / still needs an LWCR update, or the newest successful receipt is
  older than two scheduled intervals (8h).
- RECORD: every detection appends a JSONL event (same sibling watchdog
  contract) with last-exit, LWCR flags, receipt age, and running dispatches.
- ALERT ONLY, never repairs. Reloading launchd is an explicit operator
  action from the merged primary checkout.

Wired into the same three surfaces as the other integrity watchdogs: the
``cmd_dispatch`` pre-dispatch warning, the post-worker sweep (both in
``scripts/delegate.py``), and the Monitor API health-orient canary
(``scripts/api/main.py``). Callers fail open on any probe exception.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


def _load_sibling(module_name: str, filename: str):
    """Load a sibling module by FILE PATH — see check_venv_integrity.py."""
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, Path(__file__).resolve().parent / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


_check_primary_integrity = _load_sibling(
    "_worktree_cleanup_integrity_check_primary_integrity",
    "check_primary_integrity.py",
)
_append_event = _check_primary_integrity._append_event
_resolve_main_root = _check_primary_integrity._resolve_main_root
_running_dispatches = _check_primary_integrity._running_dispatches

LABEL = "com.learn-ukrainian.worktree-cleanup"
EX_CONFIG = 78
# Two StartInterval periods of the 4-hour job. One missed tick is not
# darkness; two days of no receipt is. 8h is the first "job is dark" bar.
STALE_AFTER = timedelta(hours=8)
_LAST_EXIT_RE = re.compile(r"last exit code = (-?\d+)")
_LAUNCHCTL_LIVE = object()


def plist_path(home: Path) -> Path:
    return home / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def receipt_dir(home: Path) -> Path:
    return home / ".codex" / "worktree-cleanup" / "receipts" / "v2"


def parse_iso(raw: str) -> datetime | None:
    text = raw.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def parse_launchd_snapshot(text: str) -> dict[str, Any]:
    match = _LAST_EXIT_RE.search(text)
    return {
        "last_exit": int(match.group(1)) if match else None,
        "needs_lwcr_update": "needs LWCR update" in text,
        "lwcr_init_failure": "Unable to get updated LWCR" in text,
    }


def latest_receipt_observed_at(receipts: Path) -> datetime | None:
    if not receipts.is_dir():
        return None
    newest: datetime | None = None
    for path in receipts.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        raw = payload.get("observed_at")
        if not isinstance(raw, str):
            continue
        parsed = parse_iso(raw)
        if parsed is not None and (newest is None or parsed > newest):
            newest = parsed
    return newest


def _launchctl_print() -> str | None:
    try:
        proc = subprocess.run(
            ["/bin/launchctl", "print", f"gui/{os.getuid()}/{LABEL}"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    combined = f"{proc.stdout}{proc.stderr}"
    return combined or None


def _age_label(age: timedelta) -> str:
    seconds = int(age.total_seconds())
    if seconds < 0:
        seconds = 0
    hours, rem = divmod(seconds, 3600)
    minutes = rem // 60
    if hours >= 48:
        days, hours = divmod(hours, 24)
        return f"{days}d{hours}h"
    if hours:
        return f"{hours}h{minutes}m"
    return f"{minutes}m"


def check_worktree_cleanup_integrity(
    repo: Path,
    *,
    home: Path | None = None,
    tasks_dir: Path | None = None,
    state_dir: Path | None = None,
    now: datetime | None = None,
    launchctl_text: Any = _LAUNCHCTL_LIVE,
    platform: str | None = None,
) -> tuple[bool, str]:
    """Detect (never repair) a red or dark worktree-cleanup LaunchAgent.

    Returns ``(ok, message)``. ``ok`` is False when the installed job's last
    scheduled exit is non-zero, launchd still needs an LWCR update, or the
    newest receipt is older than ``STALE_AFTER``. Callers must not block
    dispatch or auto-reload launchd on this signal.
    """
    host_platform = platform if platform is not None else sys.platform
    if not host_platform.startswith("darwin"):
        return True, "worktree-cleanup integrity skipped (not macOS)"

    main_root = _resolve_main_root(Path(repo))
    home_root = (home or Path.home()).expanduser()
    destination = plist_path(home_root)
    if not destination.is_file():
        return True, f"worktree-cleanup integrity skipped (job not installed: {destination})"

    observed_now = now or datetime.now(UTC)
    observed_now = (
        observed_now.replace(tzinfo=UTC)
        if observed_now.tzinfo is None
        else observed_now.astimezone(UTC)
    )

    snapshot_text = _launchctl_print() if launchctl_text is _LAUNCHCTL_LIVE else launchctl_text
    snapshot = parse_launchd_snapshot(snapshot_text) if snapshot_text else {
        "last_exit": None,
        "needs_lwcr_update": False,
        "lwcr_init_failure": False,
    }

    last_observed = latest_receipt_observed_at(receipt_dir(home_root))
    receipt_age = (observed_now - last_observed) if last_observed is not None else None
    receipt_stale = last_observed is None or receipt_age >= STALE_AFTER
    last_exit = snapshot["last_exit"]
    launchd_red = bool(
        snapshot["needs_lwcr_update"]
        or snapshot["lwcr_init_failure"]
        or (last_exit is not None and last_exit != 0)
    )

    if not launchd_red and not receipt_stale:
        return True, (
            f"worktree-cleanup integrity ok (last receipt {last_observed.isoformat().replace('+00:00', 'Z')})"
        )

    sdir = state_dir or (main_root / "data" / "telemetry" / "worktree-cleanup-integrity")
    evidence: dict[str, Any] = {
        "last_exit": last_exit,
        "needs_lwcr_update": snapshot["needs_lwcr_update"],
        "lwcr_init_failure": snapshot["lwcr_init_failure"],
        "last_receipt_at": last_observed.isoformat().replace("+00:00", "Z") if last_observed else None,
        "receipt_age_seconds": int(receipt_age.total_seconds()) if receipt_age is not None else None,
        "plist_path": str(destination),
        "running_dispatches": _running_dispatches(tasks_dir),
    }
    _append_event(sdir, "worktree_cleanup_integrity_alert", **evidence)

    reasons: list[str] = []
    if snapshot["lwcr_init_failure"] or snapshot["needs_lwcr_update"] or last_exit == EX_CONFIG:
        reasons.append(
            "launchd LWCR init failure (exit 78 / needs LWCR update) — Program was a "
            "replaceable .venv python; reinstall binds Program to /bin/bash"
        )
    elif last_exit is not None and last_exit != 0:
        reasons.append(f"last scheduled exit {last_exit}")
    if last_observed is None:
        reasons.append(f"no successful receipt under {receipt_dir(home_root)}")
    elif receipt_stale:
        reasons.append(
            f"last successful receipt {last_observed.isoformat().replace('+00:00', 'Z')} "
            f"is {_age_label(receipt_age)} old (stale after {_age_label(STALE_AFTER)})"
        )
    return False, (
        "ALERT: worktree-cleanup scheduled job is red — "
        f"{'; '.join(reasons)}. NOT repaired (detection only). "
        "From the merged primary on main: "
        ".venv/bin/python scripts/orchestration/install_worktree_cleanup_launchd.py install. "
        f"Evidence preserved under {sdir}/events.jsonl."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Detect a red or dark worktree-cleanup LaunchAgent (#6937).",
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="suppress the OK message (alerts still print)")
    parser.add_argument(
        "--repo", type=Path, default=Path(__file__).resolve().parents[2], help="repo path used to resolve telemetry state (default: this project root)"
    )
    parser.add_argument("--home", type=Path, default=None, help="home directory that owns the LaunchAgent (default: ~)")
    parser.add_argument(
        "--tasks-dir", type=Path, default=None, help="dispatch tasks dir for attribution (default: none)"
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=None,
        help="watchdog state/log dir (default: <repo>/data/telemetry/worktree-cleanup-integrity)",
    )
    args = parser.parse_args(argv)

    ok, message = check_worktree_cleanup_integrity(
        args.repo,
        home=args.home,
        tasks_dir=args.tasks_dir,
        state_dir=args.state_dir,
    )
    if not ok:
        print(f"❌ {message}", file=sys.stderr)
        return 1
    if not args.quiet:
        print(f"✅ {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
