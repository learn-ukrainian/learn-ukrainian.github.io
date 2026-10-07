#!/usr/bin/env python3
"""Change-only Fleet Comms alert for the backup systemd units.

The backup and backup-retention services name
``learn-ukrainian-backup-alert@%n.service`` in ``OnFailure=``; that template
runs ``failed <unit>``. Each service also runs ``recovered <unit>`` as an
``ExecStartPost=`` step, which only runs after a successful ``ExecStart=``.

Alerts are change-only, per unit: the first failure posts one report to the
cto Fleet Comms channel and records the unit as failed; later failures stay
quiet until a successful run posts one recovery report and clears the record.
A publish that fails leaves the record unchanged so the next run retries, and
exits non-zero so the alert unit itself shows as failed in systemd.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATE_DIR = Path("batch_state") / "backups" / "alerts"
LAST_RUN_RECEIPT = Path("batch_state") / "backups" / "last-run.json"
CHANNEL = "cto"
SENDER = "sre-timers"
KIND = "report"
ALLOWED_UNITS = frozenset(
    {
        "learn-ukrainian-backup.service",
        "learn-ukrainian-backup-retention.service",
    }
)

Publisher = Callable[[str, str], None]


class AlertError(RuntimeError):
    """The alert could not be evaluated or delivered."""


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def state_path(state_dir: Path, unit: str) -> Path:
    return state_dir / f"{unit}.state.json"


def read_state(path: Path) -> dict[str, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError):
        # An unreadable record must not silence alerts: treat it as no record.
        return {}
    return data if isinstance(data, dict) else {}


def write_state(path: Path, state: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(state, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def receipt_summary(project_root: Path) -> str:
    try:
        receipt = json.loads((project_root / LAST_RUN_RECEIPT).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "last-run receipt: absent or unreadable"
    if not isinstance(receipt, dict):
        return "last-run receipt: invalid"
    fields = ("status", "exit_status", "run_id", "finished_at_utc")
    parts = [f"{field}={receipt[field]}" for field in fields if receipt.get(field) not in (None, "")]
    return "last-run receipt: " + (" ".join(parts) if parts else "no status fields")


def failure_detail(environment: Mapping[str, str]) -> str:
    # systemd sets MONITOR_* for units started through OnFailure=.
    parts = []
    for label, key in (
        ("result", "MONITOR_SERVICE_RESULT"),
        ("exit_code", "MONITOR_EXIT_CODE"),
        ("exit_status", "MONITOR_EXIT_STATUS"),
    ):
        value = environment.get(key, "")
        if value:
            parts.append(f"{label}={value}")
    return " ".join(parts) if parts else "result=unknown (no MONITOR_* environment)"


def failure_message(unit: str, now: str, environment: Mapping[str, str], project_root: Path) -> str:
    lines = [
        f"[sre-timers] {unit} FAILED at {now}.",
        f"systemd: {failure_detail(environment)}",
    ]
    if unit == "learn-ukrainian-backup.service":
        lines.append(receipt_summary(project_root))
    lines += [
        f"Investigate: journalctl --user -u {unit} -n 200",
        "Change-only: further failures of this unit are not re-posted until it next succeeds.",
    ]
    return "\n".join(lines) + "\n"


def recovery_message(unit: str, now: str, since: str) -> str:
    return f"[sre-timers] {unit} RECOVERED at {now} (failing since {since or 'unknown'}).\n"


def fleet_comms_publisher(project_root: Path) -> Publisher:
    def publish(message: str, idempotency_key: str) -> None:
        command = [
            sys.executable,
            "-m",
            "scripts.fleet_comms",
            "channel",
            "publish",
            CHANNEL,
            "-",
            "--sender",
            SENDER,
            "--kind",
            KIND,
            "--idempotency-key",
            idempotency_key,
        ]
        try:
            result = subprocess.run(
                command,
                input=message,
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False,
                timeout=120,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise AlertError(f"fleet_comms publish could not run: {error}") from error
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise AlertError(f"fleet_comms publish exited {result.returncode}: {detail}")

    return publish


def handle(
    event: str,
    unit: str,
    *,
    state_dir: Path,
    project_root: Path,
    publish: Publisher,
    environment: Mapping[str, str],
    now: str,
) -> str:
    if unit not in ALLOWED_UNITS:
        raise AlertError(f"unit is not a backup unit: {unit}")
    path = state_path(state_dir, unit)
    state = read_state(path)
    invocation = environment.get("MONITOR_INVOCATION_ID") or environment.get("INVOCATION_ID") or now
    if event == "failed":
        if state.get("state") == "failed":
            return f"{unit}: already reported failing since {state.get('since_utc', 'unknown')}; not re-posting"
        publish(failure_message(unit, now, environment, project_root), f"lu-backup-alert:{unit}:failed:{invocation}")
        write_state(path, {"state": "failed", "since_utc": now, "invocation": invocation})
        return f"{unit}: failure reported to the {CHANNEL} channel"
    if event == "recovered":
        if state.get("state") != "failed":
            return f"{unit}: healthy, nothing to report"
        publish(
            recovery_message(unit, now, state.get("since_utc", "")), f"lu-backup-alert:{unit}:recovered:{invocation}"
        )
        path.unlink(missing_ok=True)
        return f"{unit}: recovery reported to the {CHANNEL} channel"
    raise AlertError(f"unknown event: {event}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("event", choices=("failed", "recovered"))
    parser.add_argument("unit", help="the backup unit name, e.g. learn-ukrainian-backup.service")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=None,
        help=f"change-only state directory (default: <project>/{DEFAULT_STATE_DIR})",
    )
    return parser


def main(argv: list[str] | None = None, publish: Publisher | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = args.project_root.resolve()
    state_dir = args.state_dir or project_root / DEFAULT_STATE_DIR
    try:
        print(
            handle(
                args.event,
                args.unit,
                state_dir=state_dir,
                project_root=project_root,
                publish=publish or fleet_comms_publisher(project_root),
                environment=os.environ,
                now=utc_now(),
            )
        )
    except AlertError as error:
        print(f"backup-alert: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
