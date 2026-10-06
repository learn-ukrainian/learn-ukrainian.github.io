"""Child interpreter for hook audit runs (#9807).

The audit hook is installed before any production module is imported or
executed. Events are appended with ``os.write`` so a caught exception cannot
drop them, and so a forked child can record ``os.exec`` before the new image
replaces it. Shell and native descendants are not instrumented: only this
interpreter and Python children that inherit the hook are visible.

A recording stand-in answers a launch only after the same classifier accepts
it. Every other process start is blocked after it is recorded, except
``os.fork`` / ``os.forkpty`` (the child must still emit its exec event) and an
optional exact argv the descendant-boundary probe is allowed to exec.
``os.putenv`` and ``os.unsetenv`` are recorded as key names only.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from collections.abc import Mapping
from io import StringIO
from pathlib import Path

# Repo root on sys.path lets this driver import its policy. It is not PYTHONPATH.
_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from tests.hooks_runtime.policy import (
    ObservedStart,
    allowed_template,
    injection_names,
    looks_like_python,
    text_argv,
)
from tests.hooks_runtime.standin import install as install_standin

_PARENT_PID = os.getpid()
_STATE = {"index": -1}
_LOCAL = threading.local()
_LOG_FD = -1
_ALLOW_ARGV: tuple[str, ...] | None = None
_COLLECT_CHILDREN = True
_WRITE_LOCK = threading.Lock()
_BASELINE: dict[str, str] = {}
# putenv/unsetenv do not update os.environ. None means the key was unset.
_DELTA: dict[str, str | None] = {}

_FORK_EVENTS = frozenset({"os.fork", "os.forkpty"})
_ENV_EVENTS = frozenset({"os.putenv", "os.unsetenv"})
_PROCESS_EVENTS = frozenset(
    {
        "subprocess.Popen",
        "os.system",
        "os.exec",
        "os.posix_spawn",
        "os.spawn",
        "pty.spawn",
        "os.fork",
        "os.forkpty",
    }
)


def _text(value: object) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", "surrogateescape")
    return str(value)


def _mapping(value: object) -> dict[str, str] | None:
    """Copy a process environment. ``os.environ`` is a mapping, not a ``dict``."""
    if not isinstance(value, Mapping):
        return None
    return {_text(key): _text(item) for key, item in value.items()}


def _first(value: object) -> str:
    words = text_argv(value)
    if not words:
        return ""
    return words[0]


def _merged_inherited() -> dict[str, str]:
    """Process environment plus decoded putenv/unsetenv that os.environ missed."""
    merged = dict(os.environ)
    with _WRITE_LOCK:
        delta = dict(_DELTA)
    for key, value in delta.items():
        if value is None:
            merged.pop(key, None)
        else:
            merged[key] = value
    return merged


def _observe(
    event: str,
    *,
    executable: str,
    argv: tuple[str, ...],
    explicit_env: dict[str, str] | None,
    shell_mediated: str,
) -> ObservedStart:
    names = injection_names(
        explicit=explicit_env,
        inherited=_merged_inherited() if explicit_env is None else {},
        baseline=_BASELINE,
        python_launch=looks_like_python(argv),
    )
    return ObservedStart(
        event=event,
        pid=os.getpid(),
        parent_pid=_PARENT_PID,
        pair_index=int(_STATE["index"]),
        executable=executable,
        argv=argv,
        explicit_env=None,
        inherited_dangerous={},
        shell_mediated=shell_mediated,
        env_injection=names,
        explicit=explicit_env is not None,
    )


def _public_record(start: ObservedStart) -> dict[str, object]:
    """Log record. Environment values are not included."""
    return {
        "event": start.event,
        "pid": start.pid,
        "parent_pid": start.parent_pid,
        "pair_index": start.pair_index,
        "executable": start.executable,
        "argv": list(start.argv),
        "explicit": start.explicit,
        "shell_mediated": start.shell_mediated,
        "env_injection": list(start.env_injection or ()),
    }


def _write_record(record: dict[str, object]) -> None:
    line = (json.dumps(record, separators=(",", ":")) + "\n").encode("utf-8")
    with _WRITE_LOCK:
        os.write(_LOG_FD, line)


def _normalize(event: str, args: tuple[object, ...]) -> ObservedStart | None:
    """Return one observed start, or None when the event is not a process start."""
    executable = ""
    argv: tuple[str, ...] | None = None
    explicit: dict[str, str] | None = None
    shell_mediated = ""
    if event == "subprocess.Popen" and len(args) >= 4:
        executable = _first(args[0])
        argv = text_argv(args[1]) or ()
        explicit = _mapping(args[3])
    elif event == "os.system" and args:
        argv = text_argv(args[0]) or ()
        executable = ""
        explicit = None
        shell_mediated = "os.system"
    elif event in {"os.exec", "os.posix_spawn", "os.spawn"} and len(args) >= 2:
        executable = _first(args[0])
        argv = text_argv(args[1]) or ()
        explicit = _mapping(args[2]) if len(args) >= 3 else None
    elif event == "pty.spawn" and args:
        argv = text_argv(args[0]) or ()
        executable = argv[0] if argv else ""
        explicit = None
    elif event in _FORK_EVENTS:
        argv = ()
        explicit = None
    else:
        return None
    return _observe(
        event,
        executable=executable,
        argv=argv or (),
        explicit_env=explicit,
        shell_mediated=shell_mediated,
    )


def _record_env(event: str, args: tuple[object, ...]) -> None:
    """Track putenv/unsetenv by key name. The value is not written to the log."""
    if not args:
        return
    key = _text(args[0])
    if event == "os.unsetenv":
        op = "unset"
        stored: str | None = None
    elif len(args) < 2:
        return
    else:
        op = "set"
        stored = _text(args[1])
    record = {"event": event, "op": op, "key": key, "pair_index": int(_STATE["index"])}
    line = (json.dumps(record, separators=(",", ":")) + "\n").encode("utf-8")
    with _WRITE_LOCK:
        _DELTA[key] = stored
        os.write(_LOG_FD, line)


def _audit(event: str, args: tuple[object, ...]) -> None:
    # Re-entrancy is per thread. A sibling thread's process start must still be recorded.
    if event not in _PROCESS_EVENTS and event not in _ENV_EVENTS:
        return
    if getattr(_LOCAL, "in_hook", False):
        return
    pid = os.getpid()
    if pid != _PARENT_PID and not _COLLECT_CHILDREN:
        return
    _LOCAL.in_hook = True
    try:
        if event in _ENV_EVENTS:
            _record_env(event, args)
            return
        if os.environ.get("HOOK_RUNTIME_HOLD_HOOK") == "1":
            time.sleep(0.2)
        start = _normalize(event, args)
        if start is None:
            return
        _write_record(_public_record(start))
        if event in _FORK_EVENTS:
            return
        if _ALLOW_ARGV is not None and start.argv == _ALLOW_ARGV:
            # Parent and the forked child both let this exact image exec.
            return
        if pid != _PARENT_PID:
            # Do not exec the target, and do not resume this driver's loop.
            os._exit(126)
        raise FileNotFoundError("audit hook blocked process start")
    finally:
        _LOCAL.in_hook = False


def _decide(args: object, executable: object, env: object, shell: bool) -> str | None:
    """Classify before any canned answer. None falls through to the real constructor."""
    if shell or isinstance(args, (str, bytes)) or not isinstance(args, (list, tuple)):
        return None
    argv = text_argv(args)
    if not argv:
        return None
    exe = _text(executable) if executable else argv[0]
    explicit = _mapping(env) if env is not None else None
    start = _observe(
        "subprocess.Popen",
        executable=exe,
        argv=argv,
        explicit_env=explicit,
        shell_mediated="",
    )
    ident = allowed_template(start)
    if ident is None:
        return None
    _write_record(_public_record(start))
    return ident


def _run_canary() -> None:
    if os.environ.get("HOOK_RUNTIME_SKIP_CANARY") == "1":
        return
    import subprocess

    _STATE["index"] = -1
    try:
        subprocess.run(["__audit_canary__", "intercept"], check=False, timeout=30)
    except FileNotFoundError:
        return


def _run_pairs(entry: str, commands: list[str]) -> dict[str, object]:
    source = Path(entry).read_text(encoding="utf-8")
    code = compile(source, entry, "exec")
    errors: list[str] = []
    completed = 0
    for index, command in enumerate(commands):
        _STATE["index"] = index
        payload = {"tool_name": "Bash", "tool_input": {"command": command, "cwd": os.getcwd()}}
        sys.stdin = StringIO(json.dumps(payload))
        globals_dict = {
            "__name__": "__main__",
            "__file__": entry,
            "__package__": None,
            "__builtins__": __builtins__,
        }
        try:
            exec(code, globals_dict, globals_dict)  # the entry under test is the program
        except (FileNotFoundError, SystemExit):
            completed += 1
        except Exception as exc:
            errors.append(f"{index}:{type(exc).__name__}:{exc}")
        else:
            completed += 1
    return {"completed": completed, "expected": len(commands), "pair_errors": errors}


def _write_summary(summary_fd: int, entry: str, body: dict[str, object]) -> None:
    if os.environ.get("HOOK_RUNTIME_OMIT_SUMMARY") == "1":
        return
    summary = {"entry": entry, "canary_ran": os.environ.get("HOOK_RUNTIME_SKIP_CANARY") != "1", **body}
    os.write(summary_fd, (json.dumps(summary) + "\n").encode("utf-8"))


def main() -> int:
    global _LOG_FD, _ALLOW_ARGV, _COLLECT_CHILDREN
    sys.dont_write_bytecode = True
    _BASELINE.update(os.environ)
    log_path = os.environ["HOOK_RUNTIME_LOG"]
    _LOG_FD = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    _COLLECT_CHILDREN = os.environ.get("HOOK_RUNTIME_COLLECT_FORK_CHILDREN", "1") != "0"
    allow = os.environ.get("HOOK_RUNTIME_ALLOW_ARGV")
    if allow:
        _ALLOW_ARGV = tuple(json.loads(allow))
    sys.addaudithook(_audit)
    install_standin(_decide)
    summary_fd = os.dup(1)
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, 1)
    os.dup2(devnull, 2)
    os.close(devnull)
    _run_canary()
    entry = os.environ["HOOK_RUNTIME_ENTRY"]
    commands = json.loads(Path(os.environ["HOOK_RUNTIME_COMMANDS"]).read_text(encoding="utf-8"))
    try:
        body = _run_pairs(entry, commands)
    except Exception as exc:
        body = {"completed": 0, "expected": len(commands), "pair_errors": [f"driver:{type(exc).__name__}:{exc}"]}
    _write_summary(summary_fd, entry, body)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FileNotFoundError:
        raise SystemExit(0) from None
