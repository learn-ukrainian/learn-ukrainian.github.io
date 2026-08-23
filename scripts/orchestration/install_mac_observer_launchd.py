#!/usr/bin/env python3
"""Install the Mac GUI observer presence heartbeat LaunchAgent on macOS (#7104)."""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

LABEL = "com.learn-ukrainian.mac-observer-heartbeat"
DEFAULT_INTERVAL_MINUTES = 8
LAUNCHD_PATH = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
# launchd binds LWCR to ProgramArguments[0]. /bin/bash is Apple-signed and
# survives a primary .venv rebuild; pointing Program at .venv/bin/python
# is what produced exit 78 after the 2026-08-15 uv rewrite (#6937, #6941).
STABLE_PROGRAM = "/bin/bash"
WRAPPER_NAME = "run_mac_observer_heartbeat.sh"


class LaunchdError(RuntimeError):
    """The requested launchd state could not be verified."""


def default_repo_root() -> Path:
    """Return the checkout containing this installer."""
    return Path(__file__).resolve().parents[2]


def default_home() -> Path:
    """Return the current user's home without consulting shell expansion."""
    return Path.home()


def plist_path(home: Path) -> Path:
    """Return the per-user LaunchAgent path."""
    return home / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def state_dir(home: Path) -> Path:
    """Return the durable logs and state directory outside the checkout."""
    return home / ".codex" / "mac-observer"


def wrapper_path(repo_root: Path) -> Path:
    """Return the stable bash wrapper launchd executes."""
    return repo_root / "scripts" / "orchestration" / WRAPPER_NAME


def build_plist(
    *,
    repo_root: Path,
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
            STABLE_PROGRAM,
            "--noprofile",
            "--norc",
            str(wrapper_path(repo_root)),
            "--repo-root",
            str(repo_root),
        ],
        "RunAtLoad": True,
        "StandardErrorPath": str(runtime / "logs" / "stderr.log"),
        "StandardOutPath": str(runtime / "logs" / "stdout.log"),
        "StartInterval": interval_minutes * 60,
        "WorkingDirectory": str(repo_root),
    }


def render_plist(
    *,
    repo_root: Path,
    home: Path,
    interval_minutes: int,
) -> bytes:
    """Render a stable XML plist for inspection and tests."""
    return plistlib.dumps(
        build_plist(
            repo_root=repo_root,
            home=home,
            interval_minutes=interval_minutes,
        ),
        fmt=plistlib.FMT_XML,
        sort_keys=True,
    )


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    try:
        descriptor = os.open(path, flags)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError:
        pass


def atomic_write(path: Path, content: bytes, *, mode: int = 0o600) -> bool:
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


def _validate_runtime(repo_root: Path, *, require_interpreter: bool = False) -> None:
    if not (repo_root / ".git").is_dir() and not (repo_root / ".git").is_file():
        raise LaunchdError(f"repository root is missing .git: {repo_root}")
    if require_interpreter:
        interpreter = repo_root / ".venv" / "bin" / "python"
        if not interpreter.is_file() or not os.access(interpreter, os.X_OK):
            raise LaunchdError(f"required interpreter is missing: {interpreter}")
        heartbeat_script = repo_root / "scripts" / "orchestration" / "observer_heartbeat.py"
        if not heartbeat_script.is_file():
            raise LaunchdError(f"observer heartbeat script is missing: {heartbeat_script}")
        wrapper = wrapper_path(repo_root)
        if not wrapper.is_file():
            raise LaunchdError(f"heartbeat wrapper is missing: {wrapper}")
        if not os.access(STABLE_PROGRAM, os.X_OK):
            raise LaunchdError(f"stable launchd program is missing: {STABLE_PROGRAM}")


def install(
    *,
    repo_root: Path,
    home: Path,
    interval_minutes: int,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    _validate_runtime(repo_root, require_interpreter=True)
    destination = plist_path(home)
    content = render_plist(
        repo_root=repo_root,
        home=home,
        interval_minutes=interval_minutes,
    )
    runtime = state_dir(home)
    logs_dir = runtime / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(logs_dir, 0o700)
    destination.parent.mkdir(parents=True, exist_ok=True)

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
        "interval_minutes": interval_minutes,
        "label": LABEL,
        "loaded": True,
        "plist_path": str(destination),
        "repo_root": str(repo_root),
        "wrote_plist": wrote_plist,
    }


def _valid_persisted_plist(
    payload: Any,
    *,
    repo_root: Path,
    home: Path,
    interval_minutes: int,
) -> bool:
    if not isinstance(payload, dict):
        return False
    arguments = payload.get("ProgramArguments")
    if not isinstance(arguments, list) or len(arguments) < 5:
        return False
    if arguments[0] != STABLE_PROGRAM:
        return False
    if any(".venv/bin/python" in str(arg) for arg in arguments):
        return False
    return payload == build_plist(
        repo_root=repo_root,
        home=home,
        interval_minutes=interval_minutes,
    )


def status(
    *,
    repo_root: Path,
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
        repo_root=repo_root.resolve(),
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=default_repo_root())
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


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root.expanduser().resolve()
    home = args.home.expanduser().resolve()
    if args.command == "render":
        print(
            render_plist(
                repo_root=repo_root,
                home=home,
                interval_minutes=args.interval_minutes,
            ).decode("utf-8"),
            end="",
        )
        return 0
    if args.command == "install":
        result = install(
            repo_root=repo_root,
            home=home,
            interval_minutes=args.interval_minutes,
        )
        return_code = 0
    elif args.command == "status":
        result, return_code = status(
            repo_root=repo_root,
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
        print(json.dumps({"error": str(exc), "label": LABEL}, sort_keys=True))
        raise SystemExit(2) from None
