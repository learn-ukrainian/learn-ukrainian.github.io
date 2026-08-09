#!/usr/bin/env python3
"""Launch an intentional local service outside an agent task's process group.

This is deliberately not a general background-task runner.  It exists for
operator-owned local services that must survive the completion or cancellation
of the harness task that launched them.  The launcher double-forks and creates
a new session, so a later process-group cleanup for the task cannot signal the
service.  It requires explicit durable lifecycle paths: a working directory,
an append-only log file, and a PID file for deliberate shutdown.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import resource
import shutil
import signal
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

_TASK_SCOPED_ENV_KEYS = frozenset(
    {
        "AGENT_NO_TELEMETRY_FOOTER",
        "LU_RUNTIME_INITIATOR",
        "LU_RUNTIME_INITIATOR_SOURCE",
        "LU_RUNTIME_TMP_BASE_ROOT",
        "LU_RUNTIME_TMP_ROOT",
        "TEMP",
        "TMP",
        "TMPDIR",
    }
)


def _absolute_existing_directory(value: str) -> Path:
    path = Path(value).expanduser().resolve(strict=True)
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"not a directory: {path}")
    return path


def _absolute_output_path(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.parent.is_dir():
        raise argparse.ArgumentTypeError(f"parent directory does not exist: {path.parent}")
    return path


def _command_is_executable(command: Sequence[str]) -> bool:
    executable = command[0]
    if "/" in executable:
        candidate = Path(executable)
        return candidate.is_file() and os.access(candidate, os.X_OK)
    return shutil.which(executable) is not None


def _pid_is_live(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _refuse_live_pid_file(path: Path) -> None:
    try:
        recorded = int(path.read_text(encoding="ascii").strip())
    except FileNotFoundError:
        return
    except (OSError, ValueError):
        return
    if recorded > 0 and _pid_is_live(recorded):
        raise RuntimeError(f"refusing to replace live service PID file: {path}")


def _write_pid_file(path: Path, pid: int) -> None:
    _refuse_live_pid_file(path)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    temporary_path = Path(temporary)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="ascii") as handle:
            handle.write(f"{pid}\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def _sanitize_environment() -> None:
    for key in tuple(os.environ):
        if key in _TASK_SCOPED_ENV_KEYS or key.startswith("SESSION_STREAM_"):
            os.environ.pop(key, None)


def _reset_signal_state() -> None:
    if hasattr(signal, "pthread_sigmask"):
        signal.pthread_sigmask(signal.SIG_SETMASK, set())
    for signum in signal.valid_signals():
        if signum in {signal.SIGKILL, signal.SIGSTOP}:
            continue
        try:
            signal.signal(signum, signal.SIG_DFL)
        except (OSError, RuntimeError, ValueError):
            continue


def _close_inherited_fds(*, preserve: int) -> None:
    maximum, _ = resource.getrlimit(resource.RLIMIT_NOFILE)
    upper_bound = 65_536 if maximum == resource.RLIM_INFINITY else min(maximum, 65_536)
    for descriptor in range(3, int(upper_bound)):
        if descriptor != preserve:
            try:
                os.close(descriptor)
            except OSError:
                continue


def _redirect_standard_streams(log_file: Path) -> None:
    stdin = os.open(os.devnull, os.O_RDONLY)
    log = os.open(log_file, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.dup2(stdin, 0)
        os.dup2(log, 1)
        os.dup2(log, 2)
    finally:
        if stdin > 2:
            os.close(stdin)
        if log > 2:
            os.close(log)


def _send_status(descriptor: int, message: str) -> None:
    try:
        os.write(descriptor, message.encode("ascii", errors="replace")[:512])
    finally:
        os.close(descriptor)


def _detach(
    *,
    command: Sequence[str],
    workdir: Path,
    log_file: Path,
    pid_file: Path,
) -> int:
    read_fd, write_fd = os.pipe()
    try:
        first_child = os.fork()
    except OSError:
        os.close(read_fd)
        os.close(write_fd)
        raise

    if first_child:
        os.close(write_fd)
        try:
            payload = os.read(read_fd, 512).decode("ascii", errors="replace").strip()
        finally:
            os.close(read_fd)
        _pid, status = os.waitpid(first_child, 0)
        if not payload.startswith("OK ") or not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
            raise RuntimeError(payload.removeprefix("ERROR ") or "detached child setup failed")
        try:
            grandchild_pid = int(payload.removeprefix("OK "))
        except ValueError as exc:
            raise RuntimeError("detached child returned an invalid PID") from exc
        try:
            _write_pid_file(pid_file, grandchild_pid)
        except BaseException:
            with contextlib.suppress(OSError):
                os.kill(grandchild_pid, signal.SIGTERM)
            raise
        return grandchild_pid

    os.close(read_fd)
    try:
        os.setsid()
        grandchild = os.fork()
        if grandchild:
            os._exit(0)

        _sanitize_environment()
        os.chdir(workdir)
        os.umask(0o022)
        _reset_signal_state()
        _close_inherited_fds(preserve=write_fd)
        _redirect_standard_streams(log_file)
    except BaseException as exc:
        _send_status(write_fd, f"ERROR {type(exc).__name__}: {exc}")
        os._exit(1)
    _send_status(write_fd, f"OK {os.getpid()}")
    try:
        os.execvp(command[0], list(command))
    except BaseException as exc:
        print(f"detach exec failed: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        os._exit(127)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", required=True, type=_absolute_existing_directory)
    parser.add_argument("--log-file", required=True, type=_absolute_output_path)
    parser.add_argument("--pid-file", required=True, type=_absolute_output_path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command = list(args.command)
    if command[:1] == ["--"]:
        command = command[1:]
    if not command:
        raise SystemExit("a command is required after --")
    if not _command_is_executable(command):
        raise SystemExit(f"command is not executable: {command[0]}")
    try:
        _refuse_live_pid_file(args.pid_file)
        pid = _detach(
            command=command,
            workdir=args.workdir,
            log_file=args.log_file,
            pid_file=args.pid_file,
        )
    except (OSError, RuntimeError) as exc:
        raise SystemExit(f"detach failed: {exc}") from exc
    print(pid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
