#!/usr/bin/env python3
"""Install the dual-repository worktree cleanup LaunchAgent on macOS."""

from __future__ import annotations

import argparse
import json
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

from scripts.orchestration import scheduled_worktree_cleanup

LABEL = "com.learn-ukrainian.worktree-cleanup"
DEFAULT_INTERVAL_MINUTES = 15
LAUNCHD_PATH = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"


class LaunchdError(RuntimeError):
    """The requested launchd state could not be verified."""


def default_home() -> Path:
    return Path.home()


def plist_path(home: Path) -> Path:
    return home / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def state_dir(home: Path) -> Path:
    return home / ".codex" / "worktree-cleanup"


def build_plist(
    *,
    public_repo: Path,
    private_repo: Path,
    home: Path,
    interval_minutes: int,
) -> dict[str, Any]:
    runtime = state_dir(home)
    return {
        "Label": LABEL,
        "EnvironmentVariables": {"PATH": LAUNCHD_PATH},
        "LowPriorityIO": True,
        "ProcessType": "Background",
        "ProgramArguments": [
            str(public_repo / ".venv" / "bin" / "python"),
            str(
                public_repo
                / "scripts"
                / "orchestration"
                / "scheduled_worktree_cleanup.py"
            ),
            "--apply",
            "--repo-root",
            str(public_repo),
            "--repo-root",
            str(private_repo),
            "--receipt-dir",
            str(runtime / "receipts" / "v1"),
        ],
        "RunAtLoad": True,
        "StandardErrorPath": str(runtime / "logs" / "stderr.log"),
        "StandardOutPath": str(runtime / "logs" / "stdout.log"),
        "StartInterval": interval_minutes * 60,
        "WorkingDirectory": str(public_repo),
    }


def render_plist(
    *,
    public_repo: Path,
    private_repo: Path,
    home: Path,
    interval_minutes: int,
) -> bytes:
    return plistlib.dumps(
        build_plist(
            public_repo=public_repo,
            private_repo=private_repo,
            home=home,
            interval_minutes=interval_minutes,
        ),
        fmt=plistlib.FMT_XML,
        sort_keys=True,
    )


def _launchctl(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["/bin/launchctl", *command],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise LaunchdError("/bin/launchctl is unavailable; macOS is required") from exc


def _domain() -> str:
    return f"gui/{os.getuid()}"


def _service_target() -> str:
    return f"{_domain()}/{LABEL}"


def _loaded_readback() -> subprocess.CompletedProcess[str]:
    return _launchctl(["print", _service_target()])


def _failure(action: str, result: subprocess.CompletedProcess[str]) -> LaunchdError:
    detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
    return LaunchdError(f"launchctl {action} failed: {detail}")


def _validate_primary(repo_root: Path, *, require_interpreter: bool = False) -> None:
    if not (repo_root / ".git").is_dir():
        raise LaunchdError(f"repository is not a primary checkout: {repo_root}")
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
        env=scheduled_worktree_cleanup.reap_worktrees.sanitized_git_env(),
    )
    if branch.returncode != 0 or branch.stdout.strip() != "main":
        raise LaunchdError(f"repository primary must be on main: {repo_root}")
    if require_interpreter:
        interpreter = repo_root / ".venv" / "bin" / "python"
        if not interpreter.is_file() or not os.access(interpreter, os.X_OK):
            raise LaunchdError(f"required interpreter is missing: {interpreter}")
        cleanup_script = (
            repo_root / "scripts" / "orchestration" / "scheduled_worktree_cleanup.py"
        )
        if not cleanup_script.is_file():
            raise LaunchdError(f"cleanup script is missing: {cleanup_script}")


def install(
    *,
    public_repo: Path,
    private_repo: Path,
    home: Path,
    interval_minutes: int,
) -> dict[str, Any]:
    public_repo = public_repo.resolve()
    private_repo = private_repo.resolve()
    _validate_primary(public_repo, require_interpreter=True)
    _validate_primary(private_repo)
    destination = plist_path(home)
    content = render_plist(
        public_repo=public_repo,
        private_repo=private_repo,
        home=home,
        interval_minutes=interval_minutes,
    )
    runtime = state_dir(home)
    for directory in (
        runtime,
        runtime / "logs",
        runtime / "receipts",
        runtime / "receipts" / "v1",
    ):
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(directory, 0o700)
    destination.parent.mkdir(parents=True, exist_ok=True)

    before = _loaded_readback()
    was_loaded = before.returncode == 0
    changed = not destination.is_file() or destination.read_bytes() != content
    if changed and was_loaded:
        bootout = _launchctl(["bootout", _service_target()])
        if bootout.returncode != 0:
            raise _failure("bootout", bootout)

    wrote_plist = changed
    if changed:
        scheduled_worktree_cleanup.atomic_write(destination, content)
    if changed or not was_loaded:
        bootstrap = _launchctl(["bootstrap", _domain(), str(destination)])
        if bootstrap.returncode != 0:
            raise _failure("bootstrap", bootstrap)

    readback = _loaded_readback()
    if readback.returncode != 0:
        raise _failure("print", readback)
    return {
        "action": "install",
        "changed": changed,
        "interval_minutes": interval_minutes,
        "label": LABEL,
        "loaded": True,
        "plist_path": str(destination),
        "private_repo": str(private_repo),
        "public_repo": str(public_repo),
        "wrote_plist": wrote_plist,
    }


def _valid_persisted_plist(
    payload: Any,
    *,
    public_repo: Path,
    private_repo: Path,
    home: Path,
    interval_minutes: int,
) -> bool:
    return payload == build_plist(
        public_repo=public_repo,
        private_repo=private_repo,
        home=home,
        interval_minutes=interval_minutes,
    )


def status(
    *,
    public_repo: Path,
    private_repo: Path,
    home: Path,
    interval_minutes: int,
) -> tuple[dict[str, Any], int]:
    destination = plist_path(home)
    loaded = _loaded_readback().returncode == 0
    persisted: Any = None
    parse_error = None
    if destination.is_file():
        try:
            persisted = plistlib.loads(destination.read_bytes())
        except Exception as exc:
            parse_error = str(exc)
    valid = _valid_persisted_plist(
        persisted,
        public_repo=public_repo.resolve(),
        private_repo=private_repo.resolve(),
        home=home,
        interval_minutes=interval_minutes,
    )
    result = {
        "action": "status",
        "installed": destination.is_file(),
        "interval_minutes": interval_minutes,
        "label": LABEL,
        "loaded": loaded,
        "parse_error": parse_error,
        "plist_path": str(destination),
        "valid_plist": valid,
    }
    return result, 0 if loaded and valid else 1


def uninstall(*, home: Path) -> dict[str, Any]:
    destination = plist_path(home)
    was_loaded = _loaded_readback().returncode == 0
    if was_loaded:
        bootout = _launchctl(["bootout", _service_target()])
        if bootout.returncode != 0:
            raise _failure("bootout", bootout)
    destination.unlink(missing_ok=True)
    return {
        "action": "uninstall",
        "label": LABEL,
        "loaded": False,
        "plist_path": str(destination),
        "preserved_state_dir": str(state_dir(home)),
    }


def positive_interval(value: str) -> int:
    try:
        interval = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("interval must be a positive integer") from exc
    if interval <= 0:
        raise argparse.ArgumentTypeError("interval must be a positive integer")
    return interval


def build_parser() -> argparse.ArgumentParser:
    public_repo = scheduled_worktree_cleanup.default_public_repo()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-repo", type=Path, default=public_repo)
    parser.add_argument(
        "--private-repo",
        type=Path,
        default=None,
    )
    parser.add_argument("--home", type=Path, default=default_home())
    parser.add_argument(
        "--interval-minutes",
        type=positive_interval,
        default=DEFAULT_INTERVAL_MINUTES,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("render")
    subparsers.add_parser("install")
    subparsers.add_parser("status")
    subparsers.add_parser("uninstall")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    public_repo = args.public_repo.expanduser().resolve()
    private_repo = (
        args.private_repo.expanduser().resolve()
        if args.private_repo is not None
        else scheduled_worktree_cleanup.default_private_repo(public_repo).resolve()
    )
    home = args.home.expanduser().resolve()
    if args.command == "render":
        print(
            render_plist(
                public_repo=public_repo,
                private_repo=private_repo,
                home=home,
                interval_minutes=args.interval_minutes,
            ).decode("utf-8"),
            end="",
        )
        return 0
    if args.command == "install":
        result = install(
            public_repo=public_repo,
            private_repo=private_repo,
            home=home,
            interval_minutes=args.interval_minutes,
        )
        return_code = 0
    elif args.command == "status":
        result, return_code = status(
            public_repo=public_repo,
            private_repo=private_repo,
            home=home,
            interval_minutes=args.interval_minutes,
        )
    else:
        result = uninstall(home=home)
        return_code = 0
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return return_code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LaunchdError as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True))
        raise SystemExit(2) from None
