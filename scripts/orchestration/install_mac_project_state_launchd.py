#!/usr/bin/env python3
"""Install the Mac project-state reporter LaunchAgent on macOS (#7188)."""

from __future__ import annotations

import argparse
import os
import plistlib
import subprocess
import tempfile
from pathlib import Path
from typing import Any

LABEL = "com.learn-ukrainian.project-state-reporter"
DEFAULT_INTERVAL_MINUTES = 5
LAUNCHD_PATH = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
STABLE_PROGRAM = "/bin/bash"
WRAPPER_NAME = "run_project_state_reporter.sh"


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
        print(plist_bytes.decode("utf-8"))
        return 0
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(plist_bytes)
        tmp_path = tmp.name
    os.replace(tmp_path, target)
    subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}/{LABEL}"], check=False)
    subprocess.run(["launchctl", "bootstrap", f"gui/{os.getuid()}", str(target)], check=True)
    subprocess.run(["launchctl", "enable", f"gui/{os.getuid()}/{LABEL}"], check=True)
    print(f"installed {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
