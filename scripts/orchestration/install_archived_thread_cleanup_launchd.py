#!/usr/bin/env python3
"""Install the deterministic archived-thread cleanup launchd job on macOS."""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path

LABEL = "com.learn-ukrainian.codex-archived-thread-cleanup"
DEFAULT_WEEKDAY = "sunday"
DEFAULT_HOUR = 3
WEEKDAYS = {
    "sunday": 0,
    "monday": 1,
    "tuesday": 2,
    "wednesday": 3,
    "thursday": 4,
    "friday": 5,
    "saturday": 6,
}


class LaunchdError(RuntimeError):
    """Raised when launchd cannot reach the requested final state."""


def default_repo_root() -> Path:
    """Return the checkout containing this installer."""
    return Path(__file__).resolve().parents[2]


def default_home() -> Path:
    """Return the current user's home without consulting shell expansion."""
    return Path.home()


def valid_hour(value: str) -> int:
    """Parse and validate a launch hour in local time."""
    try:
        hour = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("hour must be an integer from 0 through 23") from exc
    if not 0 <= hour <= 23:
        raise argparse.ArgumentTypeError("hour must be an integer from 0 through 23")
    return hour


def plist_path(home: Path) -> Path:
    """Return the per-user launch agent path."""
    return home / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def state_dir(home: Path) -> Path:
    """Return the durable scheduler log and cleanup-state directory."""
    return home / ".codex" / "thread-cleanup"


def resolve_codex_binary(configured: Path | None) -> Path:
    """Resolve and validate the supported Codex CLI before persisting its path."""
    if configured is None:
        discovered = shutil.which("codex")
        if discovered is None:
            raise LaunchdError("codex is not on PATH; pass --codex-binary with its absolute path")
        candidate = Path(discovered)
    else:
        candidate = configured.expanduser()

    absolute = candidate.absolute()
    if not absolute.is_file() or not os.access(absolute, os.X_OK):
        raise LaunchdError(f"Codex CLI is missing or not executable: {absolute}")
    return absolute


def build_plist(
    *, repo_root: Path, home: Path, codex_binary: Path, weekday: str, hour: int
) -> dict[str, object]:
    """Build the launchd configuration without touching disk or launchd."""
    cleanup_script = repo_root / "scripts" / "orchestration" / "archived_thread_cleanup.py"
    interpreter = repo_root / ".venv" / "bin" / "python"
    log_dir = state_dir(home) / "logs"
    return {
        "Label": LABEL,
        "LowPriorityIO": True,
        "ProcessType": "Background",
        "ProgramArguments": [
            str(interpreter),
            str(cleanup_script),
            "--apply",
            "--repo-root",
            str(repo_root),
            "--retention-days",
            "30",
            "--observation-interval-days",
            "7",
            "--codex-binary",
            str(codex_binary),
        ],
        "RunAtLoad": False,
        "StandardErrorPath": str(log_dir / "stderr.log"),
        "StandardOutPath": str(log_dir / "stdout.log"),
        "StartCalendarInterval": {
            "Hour": hour,
            "Minute": 0,
            "Weekday": WEEKDAYS[weekday],
        },
        "WorkingDirectory": str(repo_root),
    }


def render_plist(
    *, repo_root: Path, home: Path, codex_binary: Path, weekday: str, hour: int
) -> bytes:
    """Render a stable XML plist for inspection and tests."""
    payload = build_plist(
        repo_root=repo_root,
        home=home,
        codex_binary=codex_binary,
        weekday=weekday,
        hour=hour,
    )
    return plistlib.dumps(payload, fmt=plistlib.FMT_XML, sort_keys=True)


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_write(path: Path, content: bytes, *, mode: int = 0o644) -> bool:
    """Atomically replace path and report whether its contents changed."""
    if path.is_file() and path.read_bytes() == content:
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_path, mode)
        os.replace(temporary_path, path)
        _fsync_directory(path.parent)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
    return True


def _launchctl(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["/bin/launchctl", *command],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise LaunchdError("/bin/launchctl is unavailable; this installer requires macOS") from exc


def _domain() -> str:
    return f"gui/{os.getuid()}"


def _service_target() -> str:
    return f"{_domain()}/{LABEL}"


def _loaded_readback() -> subprocess.CompletedProcess[str]:
    return _launchctl(["print", _service_target()])


def _failure(action: str, result: subprocess.CompletedProcess[str]) -> LaunchdError:
    detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
    return LaunchdError(f"launchctl {action} failed: {detail}")


def _validate_runtime(repo_root: Path, codex_binary: Path) -> None:
    interpreter = repo_root / ".venv" / "bin" / "python"
    cleanup_script = repo_root / "scripts" / "orchestration" / "archived_thread_cleanup.py"
    if not interpreter.is_file() or not os.access(interpreter, os.X_OK):
        raise LaunchdError(f"required interpreter is missing or not executable: {interpreter}")
    if not cleanup_script.is_file():
        raise LaunchdError(f"cleanup script is missing: {cleanup_script}")
    if not codex_binary.is_file() or not os.access(codex_binary, os.X_OK):
        raise LaunchdError(f"Codex CLI is missing or not executable: {codex_binary}")


def install(
    *, repo_root: Path, home: Path, codex_binary: Path, weekday: str, hour: int
) -> dict[str, object]:
    """Install or reconcile the launch agent, then verify launchd readback."""
    _validate_runtime(repo_root, codex_binary)
    destination = plist_path(home)
    content = render_plist(
        repo_root=repo_root,
        home=home,
        codex_binary=codex_binary,
        weekday=weekday,
        hour=hour,
    )
    runtime_state = state_dir(home)
    runtime_state.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(runtime_state, 0o700)
    logs = runtime_state / "logs"
    logs.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(logs, 0o700)

    before = _loaded_readback()
    was_loaded = before.returncode == 0
    changed = not destination.is_file() or destination.read_bytes() != content

    if changed and was_loaded:
        bootout = _launchctl(["bootout", _service_target()])
        if bootout.returncode != 0:
            raise _failure("bootout", bootout)

    wrote_plist = atomic_write(destination, content)
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
        "codex_binary": str(codex_binary),
        "hour": hour,
        "label": LABEL,
        "loaded": True,
        "plist_path": str(destination),
        "repo_root": str(repo_root),
        "weekday": weekday,
        "wrote_plist": wrote_plist,
    }


def status(*, home: Path) -> tuple[dict[str, object], int]:
    """Read both the persisted plist and launchd's current service state."""
    destination = plist_path(home)
    readback = _loaded_readback()
    installed = destination.is_file()
    loaded = readback.returncode == 0
    valid_plist = False
    configuration: dict[str, object] = {}
    parse_error: str | None = None

    if installed:
        try:
            parsed = plistlib.loads(destination.read_bytes())
            if not isinstance(parsed, dict):
                raise ValueError("top-level plist value is not a dictionary")
            configuration = {
                "label": parsed.get("Label"),
                "program_arguments": parsed.get("ProgramArguments"),
                "schedule": parsed.get("StartCalendarInterval"),
                "working_directory": parsed.get("WorkingDirectory"),
            }
            arguments = parsed.get("ProgramArguments")
            schedule = parsed.get("StartCalendarInterval")
            valid_plist = (
                parsed.get("Label") == LABEL
                and isinstance(arguments, list)
                and len(arguments) >= 3
                and all(isinstance(argument, str) for argument in arguments)
                and Path(arguments[1]).name == "archived_thread_cleanup.py"
                and "--apply" in arguments
                and isinstance(schedule, dict)
                and isinstance(schedule.get("Weekday"), int)
            )
        except (OSError, ValueError, plistlib.InvalidFileException) as exc:
            parse_error = str(exc)

    payload: dict[str, object] = {
        "action": "status",
        "configuration": configuration,
        "installed": installed,
        "label": LABEL,
        "launchctl_error": None if loaded else (readback.stderr.strip() or readback.stdout.strip()),
        "loaded": loaded,
        "parse_error": parse_error,
        "plist_path": str(destination),
        "valid_plist": valid_plist,
    }
    return payload, 0 if installed and loaded and valid_plist else 1


def uninstall(*, home: Path) -> dict[str, object]:
    """Idempotently unload and remove the plist while preserving audit state."""
    destination = plist_path(home)
    before = _loaded_readback()
    was_loaded = before.returncode == 0
    existed = destination.exists()

    if was_loaded:
        bootout = _launchctl(["bootout", _service_target()])
        if bootout.returncode != 0:
            raise _failure("bootout", bootout)

    if existed:
        destination.unlink()
        _fsync_directory(destination.parent)

    readback = _loaded_readback()
    if readback.returncode == 0:
        raise LaunchdError(f"launchd service remains loaded after bootout: {_service_target()}")

    return {
        "action": "uninstall",
        "label": LABEL,
        "loaded": False,
        "logs_and_state_preserved": str(state_dir(home)),
        "plist_existed": existed,
        "plist_path": str(destination),
        "was_loaded": was_loaded,
    }


def _add_schedule_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--weekday",
        choices=tuple(WEEKDAYS),
        default=DEFAULT_WEEKDAY,
        help=f"local weekday for the cleanup (default: {DEFAULT_WEEKDAY})",
    )
    parser.add_argument(
        "--hour",
        type=valid_hour,
        default=DEFAULT_HOUR,
        help=f"local hour from 0 through 23 (default: {DEFAULT_HOUR})",
    )


def _add_path_options(parser: argparse.ArgumentParser, *, include_repo: bool) -> None:
    if include_repo:
        parser.add_argument(
            "--repo-root",
            type=Path,
            default=default_repo_root(),
            help="merged repository checkout to execute",
        )
        parser.add_argument(
            "--codex-binary",
            type=Path,
            help="absolute Codex CLI path (default: resolve codex from the installer's PATH)",
        )
    parser.add_argument(
        "--home",
        type=Path,
        default=default_home(),
        help=argparse.SUPPRESS,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("install", help="install or reconcile the launch agent")
    _add_schedule_options(install_parser)
    _add_path_options(install_parser, include_repo=True)
    install_parser.add_argument(
        "--dry-render",
        action="store_true",
        help="render the plist to stdout without disk writes or launchctl calls",
    )

    render_parser = subparsers.add_parser("render", help="render the plist without side effects")
    _add_schedule_options(render_parser)
    _add_path_options(render_parser, include_repo=True)

    status_parser = subparsers.add_parser("status", help="show persisted and launchd state")
    _add_path_options(status_parser, include_repo=False)

    uninstall_parser = subparsers.add_parser("uninstall", help="unload and remove the launch agent")
    _add_path_options(uninstall_parser, include_repo=False)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    home = args.home.expanduser().resolve()

    try:
        if args.command in {"install", "render"}:
            repo_root = args.repo_root.expanduser().resolve()
            codex_binary = resolve_codex_binary(args.codex_binary)
            if args.command == "render" or args.dry_render:
                rendered = render_plist(
                    repo_root=repo_root,
                    home=home,
                    codex_binary=codex_binary,
                    weekday=args.weekday,
                    hour=args.hour,
                )
                print(rendered.decode("utf-8"), end="")
                return 0
            payload = install(
                repo_root=repo_root,
                home=home,
                codex_binary=codex_binary,
                weekday=args.weekday,
                hour=args.hour,
            )
            return_code = 0
        elif args.command == "status":
            payload, return_code = status(home=home)
        else:
            payload = uninstall(home=home)
            return_code = 0
    except LaunchdError as exc:
        print(json.dumps({"error": str(exc), "label": LABEL}, sort_keys=True))
        return 1

    print(json.dumps(payload, sort_keys=True))
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
