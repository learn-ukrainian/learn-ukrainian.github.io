"""Recreate missing tmux driver lanes and start their launchers, e.g. after a reboot (#10814).

Runs once at boot from ``learn-ukrainian-lane-relaunch.service``. For each lane in
``scripts/config/driver_lanes.json`` (lead lanes, the CTO, last): a lane whose
tmux session exists is skipped, so a second run is a no-op; otherwise a
detached session is created in the repository root running the lane's
launcher. The relaunch never types into an existing session, so it cannot
disturb a lane a human is using. A launcher that exits within the settle
window (for example a lease conflict: the launcher fails closed) is logged and
the relaunch moves on; it never forces a lease.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.ops.context_guard import Tmux
from scripts.ops.driver_lanes import (
    EXIT_MARKER,
    LaneConfigError,
    Registry,
    default_local_config_path,
    launch_plan,
    load_local_config,
    load_registry,
    relaunch_order,
)

EXIT_RE = re.compile(re.escape(EXIT_MARKER) + r"(\d+)")
DEFAULT_SETTLE_S = 20


@dataclass
class Outcome:
    session: str
    status: str  # exists | started | launcher-exited | create-failed
    detail: str = ""


def plans(registry: Registry, repo_root: Path, local: dict) -> list:
    return [launch_plan(lane, repo_root=repo_root, local=local) for lane in relaunch_order(registry)]


def relaunch(
    registry: Registry,
    *,
    repo_root: Path,
    tmux: Tmux,
    local: dict,
    log: Callable[[str], None],
    settle_s: float = DEFAULT_SETTLE_S,
    server_scope: bool = False,
) -> list[Outcome]:
    outcomes = []
    for plan in plans(registry, repo_root, local):
        if tmux.session_exists(plan.session):
            log(f"{plan.session}: session exists, skipped")
            outcomes.append(Outcome(plan.session, "exists"))
            continue
        argv = ["tmux", "new-session", "-d", "-s", plan.session, "-c", plan.cwd]
        argv += [arg for key, value in sorted(plan.env.items()) for arg in ("-e", f"{key}={value}")]
        argv.append(plan.shell_command())
        if server_scope and tmux.tmux("list-sessions").returncode != 0:
            # No tmux server yet: start it in its own scope so it outlives this oneshot service.
            argv = ["systemd-run", "--user", "--scope", "--collect", "--quiet",
                    f"--unit=lu-tmux-server-{int(tmux.clock())}", *argv]
        result = tmux.run(argv)
        if result.returncode != 0:
            detail = (result.stderr or "").strip()[-200:]
            log(f"{plan.session}: new-session failed rc={result.returncode} {detail}")
            outcomes.append(Outcome(plan.session, "create-failed", detail))
            continue
        outcomes.append(_settle(tmux, plan.session, settle_s, log))
    return outcomes


def _settle(tmux: Tmux, session: str, settle_s: float, log: Callable[[str], None]) -> Outcome:
    """Wait up to ``settle_s`` for an early launcher exit (lease conflict or launch error)."""
    deadline = tmux.clock() + settle_s
    while True:
        found = EXIT_RE.search(tmux.capture(f"={session}:"))
        if found:
            log(f"{session}: launcher exited rc={found.group(1)} (fail closed; lease conflict or launch "
                "error), session kept for inspection, moving on")
            return Outcome(session, "launcher-exited", f"rc={found.group(1)}")
        if tmux.clock() >= deadline:
            log(f"{session}: started")
            return Outcome(session, "started")
        tmux.sleep(2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Recreate missing tmux driver lane sessions and start their launchers (CTO last).\n"
            "Use at boot (learn-ukrainian-lane-relaunch.service) or after a tmux server loss; existing sessions are skipped."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.ops.lane_relaunch --dry-run\n"
            "  .venv/bin/python scripts/ops/lane_relaunch.py\n"
            "Outputs: --dry-run prints the JSON plan (session, command, cwd, env keys without values) and\n"
            "  starts nothing; otherwise creates detached tmux sessions and prints one JSON outcome per lane.\n"
            "Exit codes: 0 every lane exists or started; 1 invalid lane data; 2 invalid arguments;\n"
            "  3 at least one lane failed to start (logged; the others still ran).\n"
            "Related: scripts/config/driver_lanes.json, packaging/systemd/learn-ukrainian-lane-relaunch.service,\n"
            "  docs/runbooks/maintenance-window.md, issue #10814."
        ),
    )
    parser.add_argument("--dry-run", action="store_true", help="Print the relaunch plan for all lanes; start nothing.")
    parser.add_argument(
        "--data", type=Path, default=None, help="Lane data file (default: scripts/config/driver_lanes.json)."
    )
    parser.add_argument(
        "--settle-seconds",
        type=float,
        default=DEFAULT_SETTLE_S,
        help=f"Seconds to watch each new lane for an early launcher exit (default: {DEFAULT_SETTLE_S}).",
    )
    parser.add_argument(
        "--server-scope",
        action="store_true",
        help="Start a missing tmux server in its own systemd user scope (the boot unit passes this).",
    )
    args = parser.parse_args(argv)
    try:
        registry = load_registry(args.data)
        local = load_local_config(default_local_config_path())
    except LaneConfigError as exc:
        print(f"invalid lane data: {exc}", file=sys.stderr)
        return 1
    if args.dry_run:
        print(json.dumps([plan.describe() for plan in plans(registry, REPO_ROOT, local)], indent=1))
        return 0

    def log(message: str) -> None:
        print(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {message}", flush=True)

    outcomes = relaunch(
        registry,
        repo_root=REPO_ROOT,
        tmux=Tmux(),
        local=local,
        log=log,
        settle_s=args.settle_seconds,
        server_scope=args.server_scope,
    )
    print(json.dumps([outcome.__dict__ for outcome in outcomes]))
    return 3 if any(o.status in {"launcher-exited", "create-failed"} for o in outcomes) else 0


if __name__ == "__main__":
    raise SystemExit(main())
