"""Put detached delegate workers in the user slice ``lu-dispatch.slice`` (#8645 part C).

On 2026-09-24 a dispatch fan-out OOM-killed the driver because every worker
shared the driver's cgroup (``docs/bug-autopsies/2026-09-24-dispatch-fanout-oom.md``).
``systemd-run --user --scope`` execs the worker in place, so the ``Popen`` pid,
pipes, return code, and ``cancel`` signal stay the worker's. When the user
manager, cgroup2 memory delegation, the slice limits, or linger is missing —
or ``systemd-run`` fails before that exec — dispatch uses plain ``Popen`` and
records ``popen-fallback``. Isolation is never required for a dispatch to start.

The byte values below match ``MemoryMax=11G`` and ``MemorySwapMax=1G`` in
``packaging/systemd/lu-dispatch.slice``. systemd parses the ``G`` suffix in
base 1024 (``systemd.resource-control(5)``).
"""

from __future__ import annotations

import os
import pwd
import re
import secrets
import select
import signal
import subprocess
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SLICE_UNIT = "lu-dispatch.slice"
MEMORY_MAX_BYTES = 11 * 1024**3
MEMORY_SWAP_MAX_BYTES = 1 * 1024**3
MEMORY_HIGH_BYTES = 10 * 1024**3

LAUNCH_SCOPE = "scope"
LAUNCH_FALLBACK = "popen-fallback"

# One bound for the readiness probe and for systemd-run's own start.
PROBE_TIMEOUT_S = 2.0

# systemd.unit(5): the unit name including its type suffix must not exceed 255
# characters. ``--scope`` appends ``.scope`` when the name does not end with it.
_UNIT_NAME_MAX = 255
_SCOPE_SUFFIX = ".scope"
_UNIT_TOKEN_BYTES = 4

# New stderr appended after a failed scope start. The log is append-only, so
# the read starts at the saved offset and stops after a few KiB.
_STDERR_EXCERPT_BYTES = 4096

ENV_ISOLATION = "LU_DISPATCH_ISOLATION"
_FORCE_FALLBACK = frozenset({"fallback", "popen", "off", "0"})

_Popen = subprocess.Popen
_UNIT_UNSAFE = re.compile(r"[^A-Za-z0-9:_.-]+")
_GIB = 1024**3

# Writes one byte on the inherited fd, then replaces this process with the
# worker. The byte is the signal that systemd-run already exec'd: a failure
# before exec never writes it, and a worker that then dies is not relaunched.
_MARKER_CODE = (
    "import os, sys\n"
    "os.write(int(sys.argv[1]), b'1')\n"
    "os.close(int(sys.argv[1]))\n"
    "os.execv(sys.argv[2], sys.argv[2:])\n"
)


class DispatchIsolationError(RuntimeError):
    """A second worker must not be started.

    Raised when fallback was refused, and when a scoped start did not prove
    that the worker never ran (late start marker, or the scope was still alive
    at the startup timeout). The dispatch is failed instead of relaunched.
    """


@dataclass(frozen=True)
class ProbeResult:
    """Whether a scoped launch is safe to try, and the first failed check."""

    ready: bool
    reason: str | None = None

    @property
    def check(self) -> str | None:
        if self.reason is None:
            return None
        name, _sep, _rest = self.reason.partition(":")
        return name or None


@dataclass(frozen=True)
class WorkerLaunch:
    """What the task record stores next to ``peak_rss_mib``."""

    mode: str
    unit: str | None = None
    fallback_reason: str | None = None

    def as_state(self) -> dict[str, Any]:
        state: dict[str, Any] = {"launch_mode": self.mode}
        if self.unit is not None:
            state["launch_unit"] = self.unit
        if self.fallback_reason is not None:
            state["launch_fallback_reason"] = self.fallback_reason
        return state


def scope_unit_name(task_id: str, run_nonce: str) -> str:
    """Unit name unique to this launch.

    Every call adds 8 hex characters from ``secrets.token_hex``, so a
    re-dispatch that reuses ``run_nonce`` cannot collide with a unit systemd
    still has registered. systemd appends ``.scope``; the full name stays
    within the 255-character limit from ``systemd.unit(5)``.
    """
    token = secrets.token_hex(_UNIT_TOKEN_BYTES)
    nonce = _unit_piece(run_nonce, 32)
    overhead = len("lu-worker-") + 1 + len(nonce) + 1 + len(token) + len(_SCOPE_SUFFIX)
    task = _unit_piece(task_id, _UNIT_NAME_MAX - overhead)
    return f"lu-worker-{task}-{nonce}-{token}"


def _unit_piece(value: str, limit: int) -> str:
    cleaned = _UNIT_UNSAFE.sub("-", value).strip("-._")
    piece = (cleaned or "x")[:limit]
    return piece or "x"


def build_scope_argv(
    cmd: Sequence[str],
    *,
    unit: str,
    slice_unit: str = SLICE_UNIT,
) -> list[str]:
    """``systemd-run`` argv. ``--scope`` execs ``cmd`` in place after ``--``."""
    return [
        "systemd-run",
        "--user",
        "--scope",
        f"--slice={slice_unit}",
        f"--unit={unit}",
        "--collect",
        "--quiet",
        "--",
        *cmd,
    ]


def probe_isolation(
    env: Mapping[str, str] | None = None,
    *,
    timeout_s: float = PROBE_TIMEOUT_S,
    cgroup_mount: Path = Path("/sys/fs/cgroup"),
    subtree_path: Path | None = None,
) -> ProbeResult:
    """Return whether ``lu-dispatch.slice`` can contain a worker right now.

    The first failed check wins. ``LU_DISPATCH_ISOLATION=fallback`` forces a
    not-ready result without probing.
    """
    source = os.environ if env is None else env
    forced = _forced_fallback(source)
    if forced is not None:
        return forced
    return _probe_uncached(source, timeout_s=timeout_s, cgroup_mount=cgroup_mount, subtree_path=subtree_path)


def spawn_detached_worker(
    cmd: Sequence[str],
    *,
    task_id: str,
    run_nonce: str,
    popen: Callable[..., subprocess.Popen[Any]] = subprocess.Popen,
    env: Mapping[str, str] | None = None,
    stdin: Any = None,
    stdout: Any = None,
    stderr: Any = None,
    stderr_log: Path | None = None,
    slice_unit: str = SLICE_UNIT,
    check_probe: bool = True,
    allow_fallback: bool = True,
    probe_env: Mapping[str, str] | None = None,
    timeout_s: float = PROBE_TIMEOUT_S,
    cgroup_mount: Path = Path("/sys/fs/cgroup"),
    subtree_path: Path | None = None,
) -> tuple[subprocess.Popen[Any], WorkerLaunch]:
    """Start ``cmd`` in the slice, or plain ``Popen`` when isolation is unavailable.

    ``popen`` is the caller's ``subprocess.Popen`` (so ``delegate`` tests that
    patch ``delegate.subprocess.Popen`` still see the fallback spawn). The
    scope attempt uses a one-byte start marker. Plain ``Popen`` is used only
    when that marker is absent and ``systemd-run`` has already exited on its
    own. A marker that arrives as the scope is stopped, or a scope that is
    still running when the startup window ends, raises
    :class:`DispatchIsolationError` instead of starting a second worker.
    ``start_new_session=True`` matches the historical spawn.
    """
    if not cmd:
        raise ValueError("worker command is empty")
    worker_env = dict(os.environ if env is None else env)
    if check_probe:
        probed = probe_isolation(
            probe_env,
            timeout_s=timeout_s,
            cgroup_mount=cgroup_mount,
            subtree_path=subtree_path,
        )
        if not probed.ready:
            return _fallback(
                cmd,
                popen=popen,
                env=worker_env,
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                reason=probed.reason or "isolation probe failed",
                allow_fallback=allow_fallback,
            )

    unit = scope_unit_name(task_id, run_nonce)
    proc, failure = _try_scope(
        cmd,
        popen=popen,
        env=worker_env,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
        stderr_log=stderr_log,
        slice_unit=slice_unit,
        unit=unit,
        timeout_s=timeout_s,
    )
    if proc is not None:
        return proc, WorkerLaunch(mode=LAUNCH_SCOPE, unit=unit)
    return _fallback(
        cmd,
        popen=popen,
        env=worker_env,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
        reason=failure or "systemd-run failed before the worker started",
        allow_fallback=allow_fallback,
    )


def slice_usage_clause(*, timeout_s: float = PROBE_TIMEOUT_S) -> str | None:
    """Admission text for an active slice, or ``None`` when it is not active.

    A missing user manager, a not-found unit, or an inactive slice omits the
    clause. The read is not cached: admission must not repeat a stale sample.
    """
    try:
        completed = _run(
            ["systemctl", "--user", "show", "-p", "ActiveState,MemoryCurrent,MemoryMax", SLICE_UNIT],
            os.environ,
            timeout_s,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return format_slice_show(completed.stdout)


def format_slice_show(text: str) -> str | None:
    """Turn ``systemctl show`` text into ``lu-dispatch.slice 0.4/11.0 GiB``, or ``None``."""
    props = _properties(text)
    if props.get("LoadState") == "not-found":
        return None
    if props.get("ActiveState") != "active":
        return None
    current = _parse_bytes(props.get("MemoryCurrent"))
    if current is None:
        return None
    limit = _parse_bytes(props.get("MemoryMax"))
    current_gib = current / _GIB
    if limit is None:
        return f"{SLICE_UNIT} {current_gib:.1f} GiB (MemoryMax infinity)"
    return f"{SLICE_UNIT} {current_gib:.1f}/{limit / _GIB:.1f} GiB"


def _fallback(
    cmd: Sequence[str],
    *,
    popen: Callable[..., subprocess.Popen[Any]],
    env: dict[str, str],
    stdin: Any,
    stdout: Any,
    stderr: Any,
    reason: str,
    allow_fallback: bool,
) -> tuple[subprocess.Popen[Any], WorkerLaunch]:
    if not allow_fallback:
        raise DispatchIsolationError(reason)
    _warn(reason)
    proc = popen(list(cmd), **_popen_kwargs(env=env, stdin=stdin, stdout=stdout, stderr=stderr))
    return proc, WorkerLaunch(mode=LAUNCH_FALLBACK, fallback_reason=reason)


def _try_scope(
    cmd: Sequence[str],
    *,
    popen: Callable[..., subprocess.Popen[Any]],
    env: dict[str, str],
    stdin: Any,
    stdout: Any,
    stderr: Any,
    stderr_log: Path | None,
    slice_unit: str,
    unit: str,
    timeout_s: float,
) -> tuple[subprocess.Popen[Any] | None, str | None]:
    read_fd, write_fd = os.pipe()
    try:
        os.set_inheritable(write_fd, True)
        wrapped = [cmd[0], "-c", _MARKER_CODE, str(write_fd), *cmd]
        argv = build_scope_argv(wrapped, unit=unit, slice_unit=slice_unit)
        start = _file_size(stderr_log)
        try:
            proc = popen(
                argv,
                pass_fds=(write_fd,),
                **_popen_kwargs(env=env, stdin=stdin, stdout=stdout, stderr=stderr),
            )
        except (OSError, ValueError) as exc:
            return None, f"systemd-run: {type(exc).__name__}: {exc}"
        if _marker_seen(proc, read_fd, timeout_s):
            return proc, None
        # The marker can arrive after select returns. An already-exited
        # process with no marker is systemd-run's own failure: the worker
        # never started. A process that is still alive is not that proof.
        if proc.poll() is not None:
            if _consume_marker(read_fd):
                return proc, None
            return None, _scope_failure_reason(proc, stderr_log, start)
        _kill_if_alive(proc)
        if _consume_marker(read_fd):
            raise DispatchIsolationError(
                "systemd-run: worker start marker arrived after the startup "
                f"timeout ({timeout_s:g}s) for unit {unit}; the scope was stopped "
                "and will not be relaunched"
            )
        raise DispatchIsolationError(
            "systemd-run: did not exec the worker within "
            f"{timeout_s:g}s for unit {unit}; startup is ambiguous and the worker "
            "will not be relaunched"
        )
    finally:
        os.close(write_fd)
        os.close(read_fd)


def _popen_kwargs(*, env: dict[str, str], stdin: Any, stdout: Any, stderr: Any) -> dict[str, Any]:
    return {
        "stdin": stdin,
        "stdout": stdout,
        "stderr": stderr,
        "env": env,
        "start_new_session": True,
        "close_fds": True,
    }


def _marker_seen(proc: subprocess.Popen[Any], read_fd: int, timeout_s: float) -> bool:
    deadline = time.monotonic() + timeout_s
    while True:
        remaining = deadline - time.monotonic()
        if remaining < 0:
            remaining = 0
        readable, _w, _x = select.select([read_fd], [], [], remaining)
        if readable:
            try:
                return bool(os.read(read_fd, 16))
            except OSError:
                return False
        if proc.poll() is not None or remaining == 0:
            return False


def _scope_failure_reason(
    proc: subprocess.Popen[Any],
    stderr_log: Path | None,
    start: int,
) -> str:
    detail = _stderr_delta(stderr_log, start)
    reason = f"systemd-run: exited {proc.returncode} before the worker started"
    if detail:
        reason = f"{reason}: {detail}"
    return reason


def _consume_marker(read_fd: int) -> bool:
    """Read a start marker that arrived after the startup ``select`` returned."""
    readable, _w, _x = select.select([read_fd], [], [], 0)
    if not readable:
        return False
    try:
        return bool(os.read(read_fd, 16))
    except OSError:
        return False


def _stderr_delta(path: Path | None, start: int) -> str:
    if path is None or not path.is_file():
        return ""
    try:
        with path.open("rb") as handle:
            handle.seek(start)
            data = handle.read(_STDERR_EXCERPT_BYTES)
    except OSError:
        return ""
    text = data.decode("utf-8", errors="replace").strip()
    if not text:
        return ""
    return text.splitlines()[0][:300]


def _file_size(path: Path | None) -> int:
    if path is None or not path.is_file():
        return 0
    try:
        return path.stat().st_size
    except OSError:
        return 0


def _kill_if_alive(proc: subprocess.Popen[Any]) -> None:
    if proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            proc.kill()
        except (ProcessLookupError, OSError):
            return
    try:
        proc.wait(timeout=PROBE_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return


def _warn(reason: str) -> None:
    print(
        f"⚠️  dispatch isolation: {reason}; launching the worker with plain Popen",
        file=sys.stderr,
    )


def _forced_fallback(env: Mapping[str, str]) -> ProbeResult | None:
    raw = env.get(ENV_ISOLATION, "").strip().lower()
    if raw in _FORCE_FALLBACK:
        return ProbeResult(ready=False, reason=f"forced: {ENV_ISOLATION}={raw}")
    return None


def _probe_uncached(
    env: Mapping[str, str],
    *,
    timeout_s: float,
    cgroup_mount: Path,
    subtree_path: Path | None,
) -> ProbeResult:
    manager = _slice_properties(env, timeout_s)
    if isinstance(manager, str):
        return ProbeResult(ready=False, reason=manager)
    load_state = manager.get("LoadState")
    if load_state != "loaded":
        return ProbeResult(ready=False, reason=f"load-state: LoadState={load_state or 'missing'}")
    cgroup_type = _cgroup_fs_type(env, cgroup_mount, timeout_s)
    if isinstance(cgroup_type, str) and cgroup_type.startswith("cgroup2:"):
        return ProbeResult(ready=False, reason=cgroup_type)
    if cgroup_type != "cgroup2fs":
        shown = cgroup_type or "missing"
        return ProbeResult(ready=False, reason=f"cgroup2: /sys/fs/cgroup is {shown}, expected cgroup2fs")
    subtree = _subtree_memory(subtree_path)
    if subtree is not None:
        return ProbeResult(ready=False, reason=subtree)
    memory = _memory_limits(manager)
    if memory is not None:
        return ProbeResult(ready=False, reason=memory)
    linger = _linger(env, timeout_s)
    if linger is not None:
        return ProbeResult(ready=False, reason=linger)
    return ProbeResult(ready=True)


def _slice_properties(env: Mapping[str, str], timeout_s: float) -> dict[str, str] | str:
    try:
        completed = _run(
            ["systemctl", "--user", "show", "-p", "LoadState,MemoryMax,MemorySwapMax", SLICE_UNIT],
            env,
            timeout_s,
        )
    except subprocess.TimeoutExpired:
        return "user-manager: systemctl --user show timed out"
    except OSError as exc:
        return f"user-manager: {type(exc).__name__}: {exc}"
    if completed.returncode != 0:
        detail = (completed.stderr or "").strip().splitlines()
        line = detail[-1] if detail else f"exit {completed.returncode}"
        return f"user-manager: {line}"
    return _properties(completed.stdout)


def _cgroup_fs_type(env: Mapping[str, str], mount: Path, timeout_s: float) -> str | None:
    """``stat -f -c %T`` name. cgroup v2 reports ``cgroup2fs``."""
    try:
        completed = _run(["stat", "-f", "-c", "%T", str(mount)], env, timeout_s)
    except subprocess.TimeoutExpired:
        return "cgroup2: stat timed out"
    except OSError as exc:
        return f"cgroup2: {type(exc).__name__}: {exc}"
    if completed.returncode != 0:
        detail = (completed.stderr or "").strip().splitlines()
        line = detail[-1] if detail else f"exit {completed.returncode}"
        return f"cgroup2: {line}"
    return (completed.stdout or "").strip() or None


def _subtree_memory(path: Path | None) -> str | None:
    subtree = path if path is not None else _user_manager_subtree()
    try:
        text = subtree.read_text(encoding="ascii", errors="replace")
    except OSError as exc:
        return f"subtree-control: cannot read {subtree}: {exc.strerror or exc}"
    controllers = text.split()
    if "memory" not in controllers:
        shown = " ".join(controllers) or "(empty)"
        return f"subtree-control: memory is not delegated ({shown})"
    return None


def _user_manager_subtree() -> Path:
    uid = os.getuid()
    return Path(f"/sys/fs/cgroup/user.slice/user-{uid}.slice/user@{uid}.service/cgroup.subtree_control")


def _memory_limits(props: Mapping[str, str]) -> str | None:
    memory_max = props.get("MemoryMax")
    memory_swap = props.get("MemorySwapMax")
    if memory_max != str(MEMORY_MAX_BYTES):
        return f"memory-max: MemoryMax={memory_max or 'missing'}, expected {MEMORY_MAX_BYTES}"
    if memory_swap != str(MEMORY_SWAP_MAX_BYTES):
        return f"memory-swap-max: MemorySwapMax={memory_swap or 'missing'}, expected {MEMORY_SWAP_MAX_BYTES}"
    return None


def _linger(env: Mapping[str, str], timeout_s: float) -> str | None:
    user = env.get("USER") or pwd.getpwuid(os.getuid()).pw_name
    try:
        completed = _run(["loginctl", "show-user", user, "-p", "Linger"], env, timeout_s)
    except subprocess.TimeoutExpired:
        return "linger: loginctl show-user timed out"
    except OSError as exc:
        return f"linger: {type(exc).__name__}: {exc}"
    if completed.returncode != 0:
        detail = (completed.stderr or "").strip().splitlines()
        line = detail[-1] if detail else f"exit {completed.returncode}"
        return f"linger: {line}"
    linger = _properties(completed.stdout).get("Linger")
    if linger != "yes":
        return f"linger: Linger={linger or 'missing'}, expected yes"
    return None


def _properties(text: str) -> dict[str, str]:
    props: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        props[key.strip()] = value.strip()
    return props


def _parse_bytes(value: str | None) -> int | None:
    if value is None or value in {"", "infinity", "[not set]", "[not set] "} or value.startswith("["):
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _run(argv: Sequence[str], env: Mapping[str, str], timeout_s: float) -> subprocess.CompletedProcess[str]:
    """Run a short probe without ``subprocess.run``.

    ``subprocess.run`` enters ``Popen`` as a context manager. Dispatch tests
    replace ``subprocess.Popen`` with a fake that is not one, so the probe
    keeps the ``Popen`` class captured at import.
    """
    proc = _Popen(
        list(argv),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=dict(env),
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        raise subprocess.TimeoutExpired(list(argv), timeout_s, output=stdout, stderr=stderr) from None
    return subprocess.CompletedProcess(list(argv), int(proc.returncode or 0), stdout, stderr)
