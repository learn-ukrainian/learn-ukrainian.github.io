"""Manage the macOS launchd supervisor for the local Monitor API.

The launch agent owns process lifetime; this module owns the launch contract.
It preserves the existing immutable API release-snapshot model and records every
unexpected child exit before returning a non-zero status to ``launchd``.
"""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import signal
import subprocess
import sys
import threading
from collections import deque
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.api.release_snapshot import build_release, prune_releases

LABEL = "com.learn-ukrainian.monitor-api"
PORT = 8765
THROTTLE_INTERVAL_SECONDS = 30
_LOG_ROTATE_BYTES = 10 * 1024 * 1024


class LaunchdError(RuntimeError):
    """Raised when launchd cannot reach the requested API state."""


def default_repo_root() -> Path:
    """Return the checkout that contains this supervisor."""
    return Path(__file__).resolve().parents[2]


def default_home() -> Path:
    """Return the current user's home without shell expansion."""
    return Path.home()


def plist_path(home: Path) -> Path:
    """Return the per-user LaunchAgent location."""
    return home / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def _pid_dir(repo_root: Path) -> Path:
    return repo_root / ".pids"


def _config_path(repo_root: Path) -> Path:
    return _pid_dir(repo_root) / "api-launchd.json"


def crash_record_path(repo_root: Path) -> Path:
    """Return the durable record that is deliberately not cleared on start."""
    return _pid_dir(repo_root) / "api-last-crash.json"


def _api_log_path(repo_root: Path) -> Path:
    return repo_root / "logs" / "api.log"


def _api_stderr_log_path(repo_root: Path) -> Path:
    return repo_root / "logs" / "api.stderr.log"


def _launchd_stdout_path(repo_root: Path) -> Path:
    return repo_root / "logs" / "api.launchd.stdout.log"


def _launchd_stderr_path(repo_root: Path) -> Path:
    return repo_root / "logs" / "api.launchd.stderr.log"


def _domain() -> str:
    return f"gui/{os.getuid()}"


def _target() -> str:
    return f"{_domain()}/{LABEL}"


def _now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_write(path: Path, content: bytes, *, mode: int = 0o600) -> bool:
    """Atomically replace ``path`` and report whether its content changed."""
    if path.is_file() and path.read_bytes() == content:
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return True


def build_plist(*, repo_root: Path) -> dict[str, object]:
    """Build the persistent LaunchAgent configuration without side effects."""
    root = repo_root.resolve()
    interpreter = root / ".venv" / "bin" / "python"
    return {
        "Label": LABEL,
        "ProcessType": "Background",
        "ProgramArguments": [
            str(interpreter),
            "-m",
            "scripts.api.launchd_supervisor",
            "run",
            "--repo-root",
            str(root),
        ],
        "RunAtLoad": True,
        # The foreground runner returns 0 only when launchd deliberately
        # unloads it. Every unexpected API exit becomes non-zero and restarts.
        "KeepAlive": {"SuccessfulExit": False},
        # launchd applies this between restarts, preventing a crash-loop spin.
        "ThrottleInterval": THROTTLE_INTERVAL_SECONDS,
        "StandardOutPath": str(_launchd_stdout_path(root)),
        "StandardErrorPath": str(_launchd_stderr_path(root)),
        "WorkingDirectory": str(root),
    }


def render_plist(*, repo_root: Path) -> bytes:
    """Render a stable XML plist for inspection and tests."""
    return plistlib.dumps(build_plist(repo_root=repo_root), fmt=plistlib.FMT_XML, sort_keys=True)


def _validate_runtime(repo_root: Path) -> None:
    interpreter = repo_root / ".venv" / "bin" / "python"
    supervisor = repo_root / "scripts" / "api" / "launchd_supervisor.py"
    if not interpreter.is_file() or not os.access(interpreter, os.X_OK):
        raise LaunchdError(f"required interpreter is missing or not executable: {interpreter}")
    if not supervisor.is_file():
        raise LaunchdError(f"required API supervisor is missing: {supervisor}")


def install(*, repo_root: Path, home: Path) -> dict[str, object]:
    """Write or reconcile the LaunchAgent plist without starting the service."""
    root = repo_root.resolve()
    _validate_runtime(root)
    destination = plist_path(home)
    changed = atomic_write(destination, render_plist(repo_root=root))
    return {
        "action": "install",
        "changed": changed,
        "label": LABEL,
        "plist_path": str(destination),
        "repo_root": str(root),
    }


def _launchctl(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["/bin/launchctl", *command],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise LaunchdError("/bin/launchctl is unavailable; Monitor API supervision requires macOS") from exc


def _loaded_readback() -> subprocess.CompletedProcess[str]:
    return _launchctl(["print", _target()])


def _failure(action: str, result: subprocess.CompletedProcess[str]) -> LaunchdError:
    detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
    return LaunchdError(f"launchctl {action} failed: {detail}")


def _set_launch_config(*, repo_root: Path, live_mode: bool, port: int) -> None:
    payload = {
        "live_mode": live_mode,
        "port": port,
        "updated_at": _now_z(),
    }
    atomic_write(_config_path(repo_root), (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8"))


def _load_launch_config(repo_root: Path) -> tuple[bool, int]:
    try:
        data = json.loads(_config_path(repo_root).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, PORT
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise LaunchdError(f"invalid API launch configuration at {_config_path(repo_root)}") from exc

    live_mode = data.get("live_mode") is True
    port = data.get("port", PORT)
    if not isinstance(port, int) or not 1 <= port <= 65535:
        raise LaunchdError(f"invalid API port in {_config_path(repo_root)}: {port!r}")
    return live_mode, port


def start(*, repo_root: Path, home: Path, live_mode: bool, port: int = PORT) -> dict[str, object]:
    """Enable and start the LaunchAgent after recording its launch mode."""
    root = repo_root.resolve()
    if not 1 <= port <= 65535:
        raise LaunchdError(f"invalid API port: {port}")
    result = install(repo_root=root, home=home)
    _set_launch_config(repo_root=root, live_mode=live_mode, port=port)

    enabled = _launchctl(["enable", _target()])
    if enabled.returncode != 0:
        raise _failure("enable", enabled)

    loaded = _loaded_readback()
    if loaded.returncode != 0:
        bootstrapped = _launchctl(["bootstrap", _domain(), str(plist_path(home))])
        if bootstrapped.returncode != 0:
            raise _failure("bootstrap", bootstrapped)

    kicked = _launchctl(["kickstart", "-k", _target()])
    if kicked.returncode != 0:
        raise _failure("kickstart", kicked)

    readback = _loaded_readback()
    if readback.returncode != 0:
        raise _failure("print", readback)
    return {
        **result,
        "action": "start",
        "live_mode": live_mode,
        "loaded": True,
        "port": port,
    }


def stop(*, home: Path) -> dict[str, object]:
    """Disable then unload the agent so an operator stop remains stopped."""
    disabled = _launchctl(["disable", _target()])
    if disabled.returncode != 0:
        raise _failure("disable", disabled)

    loaded = _loaded_readback()
    if loaded.returncode == 0:
        booted_out = _launchctl(["bootout", _target()])
        if booted_out.returncode != 0:
            raise _failure("bootout", booted_out)

    readback = _loaded_readback()
    if readback.returncode == 0:
        raise LaunchdError(f"launchd service remains loaded after stop: {_target()}")
    return {"action": "stop", "label": LABEL, "loaded": False, "plist_path": str(plist_path(home))}


def uninstall(*, home: Path) -> dict[str, object]:
    """Disable, unload, and remove the plist while preserving crash evidence."""
    result = stop(home=home)
    destination = plist_path(home)
    existed = destination.exists()
    if existed:
        destination.unlink()
        _fsync_directory(destination.parent)
    return {
        **result,
        "action": "uninstall",
        "plist_existed": existed,
        "crash_evidence_preserved": True,
    }


def status(*, home: Path) -> tuple[dict[str, object], int]:
    """Report persisted configuration and launchd state."""
    destination = plist_path(home)
    loaded = _loaded_readback()
    installed = destination.is_file()
    valid_plist = False
    parse_error: str | None = None
    if installed:
        try:
            payload = plistlib.loads(destination.read_bytes())
            valid_plist = (
                isinstance(payload, dict)
                and payload.get("Label") == LABEL
                and payload.get("KeepAlive") == {"SuccessfulExit": False}
                and payload.get("ThrottleInterval") == THROTTLE_INTERVAL_SECONDS
            )
        except (OSError, ValueError, plistlib.InvalidFileException) as exc:
            parse_error = str(exc)
    result = {
        "action": "status",
        "installed": installed,
        "label": LABEL,
        "launchctl_error": None if loaded.returncode == 0 else (loaded.stderr.strip() or loaded.stdout.strip()),
        "loaded": loaded.returncode == 0,
        "parse_error": parse_error,
        "plist_path": str(destination),
        "valid_plist": valid_plist,
    }
    return result, 0 if installed and loaded.returncode == 0 and valid_plist else 1


def _rotate_log(path: Path) -> None:
    if not path.is_file() or path.stat().st_size <= _LOG_ROTATE_BYTES:
        return
    oldest = path.with_name(f"{path.name}.3")
    oldest.unlink(missing_ok=True)
    for index in (2, 1):
        previous = path.with_name(f"{path.name}.{index}")
        if previous.exists():
            previous.replace(path.with_name(f"{path.name}.{index + 1}"))
    path.replace(path.with_name(f"{path.name}.1"))


def _append_log(handle: Any, message: str) -> None:
    handle.write(message.encode("utf-8", errors="replace") + b"\n")
    handle.flush()


def _record_unexpected_exit(
    *,
    repo_root: Path,
    pid: int | None,
    returncode: int,
    stderr_tail: list[str],
) -> None:
    signal_name: str | None = None
    exit_code = returncode
    if returncode < 0:
        signal_number = -returncode
        try:
            signal_name = signal.Signals(signal_number).name
        except ValueError:
            signal_name = f"SIG{signal_number}"
        exit_code = 128 + signal_number
    payload = {
        "timestamp": _now_z(),
        "pid": pid,
        "exit_code": exit_code,
        "returncode": returncode,
        "signal": signal_name,
        "stderr_tail": stderr_tail,
    }
    atomic_write(
        crash_record_path(repo_root),
        (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )


def _prepare_api_command(repo_root: Path, *, live_mode: bool, port: int) -> tuple[list[str], Path, dict[str, str], str]:
    if live_mode:
        launch_dir = repo_root
        release_line = "WARNING: API live mode enabled; serving mutable checkout code"
    else:
        head_sha = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--verify", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        release_dir, reused = build_release(repo_root, head_sha)
        prune_result = prune_releases(repo_root, keep=3)
        launch_dir = release_dir
        release_line = (
            f"release: {head_sha} reused: {reused} "
            f"pruned: {','.join(prune_result.removed) or 'none'}"
        )

    environment = os.environ.copy()
    for key in (
        "GIT_INDEX_FILE",
        "GIT_PREFIX",
        "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_NAMESPACE",
        "GIT_CEILING_DIRECTORIES",
        "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    ):
        environment.pop(key, None)
    environment["LEARN_UK_REPO_ROOT"] = str(repo_root)
    environment["GIT_DIR"] = str(repo_root / ".git")
    environment["GIT_WORK_TREE"] = str(repo_root)
    environment["PYTHONPATH"] = str(launch_dir) + os.pathsep + environment.get("PYTHONPATH", "")
    command = [
        str(repo_root / ".venv" / "bin" / "python"),
        "-m",
        "uvicorn",
        "scripts.api.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        str(port),
        "--log-config",
        "scripts/api/logging.json",
        "--timeout-graceful-shutdown",
        "8",
    ]
    return command, launch_dir, environment, release_line


def run_managed_api(
    *,
    repo_root: Path,
    live_mode: bool | None = None,
    port: int | None = None,
    prepare_command: Callable[[Path, bool, int], tuple[list[str], Path, dict[str, str], str]] | None = None,
) -> int:
    """Run one API child in the foreground and preserve unexpected-exit evidence."""
    root = repo_root.resolve()
    configured_live, configured_port = _load_launch_config(root)
    effective_live = configured_live if live_mode is None else live_mode
    effective_port = configured_port if port is None else port
    logs_dir = root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    _pid_dir(root).mkdir(parents=True, exist_ok=True)
    api_log = _api_log_path(root)
    stderr_log = _api_stderr_log_path(root)
    _rotate_log(api_log)
    _rotate_log(stderr_log)
    stopped_by_launchd = threading.Event()
    child: subprocess.Popen[bytes] | None = None

    def _on_stop(_signum: int, _frame: Any) -> None:
        stopped_by_launchd.set()
        if child is not None and child.poll() is None:
            child.terminate()

    previous_handlers: dict[int, Any] = {}
    if threading.current_thread() is threading.main_thread():
        for signum in (signal.SIGTERM, signal.SIGINT):
            previous_handlers[signum] = signal.signal(signum, _on_stop)

    stderr_tail: deque[str] = deque(maxlen=50)
    try:
        with api_log.open("ab") as combined, stderr_log.open("ab") as stderr_handle:
            try:
                factory = prepare_command or (
                    lambda root_path, live, selected_port: _prepare_api_command(
                        root_path, live_mode=live, port=selected_port
                    )
                )
                command, launch_dir, environment, release_line = factory(root, effective_live, effective_port)
                _append_log(combined, release_line)
                if stopped_by_launchd.is_set():
                    return 0
                child = subprocess.Popen(
                    command,
                    cwd=launch_dir,
                    env=environment,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            except Exception as exc:
                message = f"API launch preparation failed: {type(exc).__name__}: {exc}"
                _append_log(combined, message)
                _append_log(stderr_handle, message)
                _record_unexpected_exit(repo_root=root, pid=None, returncode=1, stderr_tail=[message])
                return 1

            assert child.stdout is not None
            assert child.stderr is not None

            def _pump(stream: Any, *, stderr: bool) -> None:
                for line in iter(stream.readline, b""):
                    combined.write(line)
                    combined.flush()
                    if stderr:
                        stderr_handle.write(line)
                        stderr_handle.flush()
                        stderr_tail.append(line.decode("utf-8", errors="replace").rstrip())
                stream.close()

            stdout_thread = threading.Thread(target=_pump, args=(child.stdout,), kwargs={"stderr": False}, daemon=True)
            stderr_thread = threading.Thread(target=_pump, args=(child.stderr,), kwargs={"stderr": True}, daemon=True)
            stdout_thread.start()
            stderr_thread.start()
            returncode = child.wait()
            stdout_thread.join(timeout=2)
            stderr_thread.join(timeout=2)

        if stopped_by_launchd.is_set():
            return 0
        _record_unexpected_exit(
            repo_root=root,
            pid=child.pid,
            returncode=returncode,
            stderr_tail=list(stderr_tail),
        )
        # A clean child exit is still unexpected for this always-on service;
        # convert it to non-zero so KeepAlive.SuccessfulExit=false restarts it.
        return 1
    finally:
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_repo_arguments(command: argparse.ArgumentParser) -> None:
        command.add_argument("--repo-root", type=Path, default=default_repo_root())
        command.add_argument("--home", type=Path, default=default_home(), help=argparse.SUPPRESS)

    install_parser = subparsers.add_parser("install", help="write the LaunchAgent plist")
    add_repo_arguments(install_parser)
    install_parser.add_argument("--dry-render", action="store_true", help="print the plist without writing it")

    render_parser = subparsers.add_parser("render", help="print the LaunchAgent plist")
    add_repo_arguments(render_parser)

    start_parser = subparsers.add_parser("start", help="enable and start the supervised API")
    add_repo_arguments(start_parser)
    start_parser.add_argument("--live", action="store_true", help="serve the mutable checkout for emergency recovery")
    start_parser.add_argument("--port", type=int, default=PORT, help=argparse.SUPPRESS)

    stop_parser = subparsers.add_parser("stop", help="disable and unload the supervised API")
    stop_parser.add_argument("--home", type=Path, default=default_home(), help=argparse.SUPPRESS)

    uninstall_parser = subparsers.add_parser("uninstall", help="remove the LaunchAgent plist")
    uninstall_parser.add_argument("--home", type=Path, default=default_home(), help=argparse.SUPPRESS)

    status_parser = subparsers.add_parser("status", help="show persistent and launchd state")
    status_parser.add_argument("--home", type=Path, default=default_home(), help=argparse.SUPPRESS)

    run_parser = subparsers.add_parser("run", help=argparse.SUPPRESS)
    run_parser.add_argument("--repo-root", type=Path, default=default_repo_root())
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    home = getattr(args, "home", default_home()).expanduser().resolve()
    try:
        if args.command in {"install", "render"}:
            root = args.repo_root.expanduser().resolve()
            rendered = render_plist(repo_root=root)
            if args.command == "render" or args.dry_render:
                print(rendered.decode("utf-8"), end="")
                return 0
            print(json.dumps(install(repo_root=root, home=home), sort_keys=True))
            return 0
        if args.command == "start":
            print(
                json.dumps(
                    start(repo_root=args.repo_root.expanduser().resolve(), home=home, live_mode=args.live, port=args.port),
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "stop":
            print(json.dumps(stop(home=home), sort_keys=True))
            return 0
        if args.command == "uninstall":
            print(json.dumps(uninstall(home=home), sort_keys=True))
            return 0
        if args.command == "status":
            payload, returncode = status(home=home)
            print(json.dumps(payload, sort_keys=True))
            return returncode
        if args.command == "run":
            return run_managed_api(repo_root=args.repo_root.expanduser().resolve())
    except LaunchdError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
