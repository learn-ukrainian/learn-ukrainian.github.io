#!/usr/bin/env python3
"""Install the Mac project-state reporter LaunchAgent on macOS (#7188).

The plist is written to a temporary file and renamed into place; a symlinked
plist, or a symlink in any directory from the home directory down to
``Library/LaunchAgents``, is refused, including under --dry-run.
"""

from __future__ import annotations

import argparse
import os
import plistlib
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.common.safe_unit_install import InstallError, install_unit, load_unit

LABEL = "com.learn-ukrainian.project-state-reporter"
DEFAULT_INTERVAL_MINUTES = 5
DEFAULT_LAUNCHCTL_TIMEOUT_SECONDS = 30.0
LAUNCHD_PATH = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
STABLE_PROGRAM = "/bin/bash"
WRAPPER_NAME = "run_project_state_reporter.sh"


class LaunchdError(RuntimeError):
    """The requested launchd state could not be verified."""


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def plist_path(home: Path) -> Path:
    return home / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def wrapper_path(repo_root: Path) -> Path:
    return repo_root / "scripts" / "orchestration" / WRAPPER_NAME


def build_plist(*, repo_root: Path, home: Path, interval_minutes: int) -> dict[str, Any]:
    return {
        "Label": LABEL,
        "EnvironmentVariables": {"PATH": LAUNCHD_PATH},
        "LowPriorityIO": True,
        "ProcessType": "Background",
        "ProgramArguments": [
            STABLE_PROGRAM,
            "--noprofile",
            "--norc",
            str(wrapper_path(repo_root)),
        ],
        "RunAtLoad": True,
        "StandardErrorPath": str(home / ".codex" / "project-state-reporter" / "logs" / "stderr.log"),
        "StandardOutPath": str(home / ".codex" / "project-state-reporter" / "logs" / "stdout.log"),
        "StartInterval": interval_minutes * 60,
        "WorkingDirectory": str(repo_root),
    }


def _domain() -> str:
    return f"gui/{os.getuid()}"


def _service_target() -> str:
    return f"{_domain()}/{LABEL}"


def _launchctl(command: Sequence[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["/bin/launchctl", *command],
            capture_output=True,
            text=True,
            check=check,
            timeout=DEFAULT_LAUNCHCTL_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise LaunchdError("/bin/launchctl is unavailable; macOS is required") from exc
    except subprocess.TimeoutExpired as exc:
        raise LaunchdError(
            f"/bin/launchctl {' '.join(command)} timed out after {DEFAULT_LAUNCHCTL_TIMEOUT_SECONDS}s"
        ) from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install Mac project-state reporter LaunchAgent.")
    parser.add_argument("--repo-root", type=Path, default=default_repo_root())
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--interval-minutes", type=int, default=DEFAULT_INTERVAL_MINUTES)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    runtime = args.home / ".codex" / "project-state-reporter"
    (runtime / "logs").mkdir(parents=True, exist_ok=True)
    plist = build_plist(
        repo_root=args.repo_root.resolve(),
        home=args.home,
        interval_minutes=args.interval_minutes,
    )
    plist_bytes = plistlib.dumps(plist, fmt=plistlib.FMT_XML, sort_keys=True)
    target = plist_path(args.home)
    if args.dry_run:
        load_unit(target, home=args.home)
        print(plist_bytes.decode("utf-8"))
        return 0
    install_unit(target, plist_bytes, mode=0o600, home=args.home)
    _launchctl(["bootout", _service_target()], check=False)
    _launchctl(["bootstrap", _domain(), str(target)], check=True)
    _launchctl(["enable", _service_target()], check=True)
    print(f"installed {target}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (LaunchdError, InstallError) as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(2) from None
