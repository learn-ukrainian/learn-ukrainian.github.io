"""Hard memory enforcement for enrichment workers (#5230 PR1, #9143).

Polling is telemetry only. Limits are enforced by the OS:

- Linux: a transient ``systemd-run --user --scope`` in the caller's own slice
  (the last ``*.slice`` in ``/proc/self/cgroup`` below the user manager; a
  dispatch worker passes ``lu-dispatch.slice``). That worker scope is a
  sibling of the caller's scope inside the caller's slice, so it stays in
  the slice's accounting and limit. Systemd sets the dedicated scope's
  ``MemoryHigh`` and ``MemoryMax``; the worker never writes cgroup files.
  If a scope cannot be created, the child uses ``RLIMIT_AS``.
  ``MemorySwapMax=0`` is set on the scope because
  ``memory.max`` alone is absorbed by swap. The scope is stopped in a
  ``finally`` on normal exit, exceptions, and ``KeyboardInterrupt``.
  ``--slice`` is omitted when the caller's cgroup has no ``user@`` segment.
  The in-scope shell records ``memory.events`` ``oom_kill`` before exit.
  A scope SIGKILL counts as OOM only when that count is positive; an
  external scope kill cannot masquerade as OOM when the shell is killed too.
- Other POSIX: ``RLIMIT_AS`` set in the child before importing the engine.

Whether ``systemd-run --user --scope`` works is probed with the worker's
exact scope properties (running ``/bin/true``). A worker's stderr is never
treated as a failed scope start, so one that prints ``Failed to connect`` runs
once. The mechanism that ran (``systemd_scope``, ``cgroup_v2``,
``rlimit_as``, or ``none``) is logged and stored on the worker result.

A startup self-test must prove enforcement; production refuses to claim
hard-cap protection if neither mechanism works. The self-test's ``kind``
comes from the mechanism that ran, not from the returncode alone.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import json
import logging
import os
import platform
import resource
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Literal

from scripts.common.repo_root import project_interpreter
from scripts.lexicon.runner.contracts import DEFAULT_MEMORY_HIGH_BYTES, DEFAULT_MEMORY_MAX_BYTES

EnforcementKind = Literal["cgroup_v2", "rlimit_as", "none"]
MemoryMechanism = Literal["systemd_scope", "cgroup_v2", "rlimit_as", "none"]

ROOT = Path(__file__).resolve().parents[3]
_LOG = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class MemoryPolicy:
    high_bytes: int = DEFAULT_MEMORY_HIGH_BYTES
    max_bytes: int = DEFAULT_MEMORY_MAX_BYTES


@dataclass(frozen=True, slots=True)
class EnforcementProof:
    kind: EnforcementKind
    enforced: bool
    detail: str
    max_bytes: int


@dataclass(frozen=True, slots=True)
class BoundedCommandResult:
    """A finished command and the cap mechanism that actually ran."""

    completed: subprocess.CompletedProcess[str]
    mechanism: MemoryMechanism
    # ``None`` when the scope's ``memory.events`` could not be read.
    oom_kill: int | None = None


class BoundedTimeoutExpired(subprocess.TimeoutExpired):
    """A timeout carrying the mechanism selected for the actual launch."""

    def __init__(self, exc: subprocess.TimeoutExpired, mechanism: MemoryMechanism) -> None:
        super().__init__(exc.cmd, exc.timeout, output=exc.output, stderr=exc.stderr)
        self.memory_mechanism = mechanism


def _log_mechanism(mechanism: str, unit: str | None) -> None:
    _LOG.info("lexicon memory mechanism=%s unit=%s", mechanism, unit or "-")


def _as_mechanism(value: str) -> MemoryMechanism | None:
    if value == "systemd_scope":
        return "systemd_scope"
    if value == "cgroup_v2":
        return "cgroup_v2"
    if value == "rlimit_as":
        return "rlimit_as"
    if value == "none":
        return "none"
    return None


def _as_enforcement_kind(value: str) -> EnforcementKind | None:
    if value == "cgroup_v2":
        return "cgroup_v2"
    if value == "rlimit_as":
        return "rlimit_as"
    if value == "none":
        return "none"
    return None


def observed_memory_mechanism(launch: MemoryMechanism, child: str) -> MemoryMechanism:
    """Prefer the scope when it launched; otherwise the child's own cap."""
    if launch == "systemd_scope":
        return "systemd_scope"
    reported = _as_mechanism(child)
    if reported is not None:
        return reported
    return launch


def _proof_kind(launch: MemoryMechanism, child_kind: str | None) -> EnforcementKind:
    """Map the mechanism that ran onto the self-test kind. Ignores returncode."""
    if launch == "systemd_scope":
        return "cgroup_v2"
    if child_kind is not None:
        reported = _as_enforcement_kind(child_kind)
        if reported is not None:
            return reported
    if launch == "rlimit_as":
        return "rlimit_as"
    return "none"


def _is_finite_positive_ceiling(limit: int) -> bool:
    """True when ``limit`` is a usable RLIMIT ceiling (not 0/negative/RLIM_INFINITY)."""
    # RLIM_INFINITY is platform-dependent: often 2**63-1 (Darwin) or -1 (some Linux).
    return limit > 0 and limit != resource.RLIM_INFINITY


def _try_set_rlimit_as(max_bytes: int) -> None:
    if not _is_finite_positive_ceiling(max_bytes):
        raise ValueError("invalid RLIMIT_AS ceiling")
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    new_hard = max_bytes if hard == resource.RLIM_INFINITY else min(hard, max_bytes)
    new_soft = min(soft if soft != resource.RLIM_INFINITY else new_hard, new_hard)
    if not _is_finite_positive_ceiling(new_soft) or not _is_finite_positive_ceiling(new_hard):
        raise ValueError("invalid RLIMIT_AS ceiling")
    resource.setrlimit(resource.RLIMIT_AS, (new_soft, new_hard))


def apply_worker_memory_limit(policy: MemoryPolicy, *, scope_capped: bool = False) -> EnforcementKind:
    """Use the enclosing scope's cap, or set ``RLIMIT_AS`` in a plain child."""
    # The scope's MemoryMax is already active. RLIMIT_AS would turn its
    # SIGKILL into MemoryError and hide the kernel's oom_kill evidence.
    if scope_capped:
        return "cgroup_v2"
    try:
        _try_set_rlimit_as(policy.max_bytes)
        return "rlimit_as"
    except (ValueError, OSError) as exc:
        if os.environ.get("LEXICON_MEMORY_DEBUG"):
            print(f"RLIMIT_AS failed: {exc}", file=sys.stderr)
        return "none"


def self_cgroup_relative() -> str | None:
    """This process's cgroup v2 path relative to ``/sys/fs/cgroup``, or None."""
    try:
        text = Path("/proc/self/cgroup").read_text(encoding="utf-8")
    except OSError:
        return None
    for line in text.splitlines():
        if line.startswith("0::"):
            return line.split(":", 2)[2]
    return None


def slice_name_from_cgroup_relative(relative: str) -> str | None:
    """Last ``*.slice`` below the ``user@*.service`` segment, or None.

    ``.../user@1000.service/lu.slice/lu-dispatch.slice/<scope>.scope`` yields
    ``lu-dispatch.slice``, the slice a dispatch worker must pass to
    ``systemd-run --slice``. A cgroup with no ``user@`` segment (an ssh
    session scope, a system slice) returns None so the caller omits
    ``--slice`` instead of inventing a slice inside the user manager.
    """
    parts = [part for part in relative.split("/") if part]
    service_at: int | None = None
    for index, part in enumerate(parts):
        if part.startswith("user@") and part.endswith(".service"):
            service_at = index
    if service_at is None:
        return None
    for part in reversed(parts[service_at + 1 :]):
        if part.endswith(".slice"):
            return part
    return None


def caller_slice_name() -> str | None:
    """Systemd slice that contains this process, for ``--slice=``."""
    relative = self_cgroup_relative()
    if not relative:
        return None
    return slice_name_from_cgroup_relative(relative)


def _user_systemd_environ() -> dict[str, str] | None:
    """Return an environment that can talk to the user systemd bus.

    ``None`` when that bus socket is absent. Creating the scope does not need
    root; a missing user bus means the caller must use ``RLIMIT_AS``.
    """
    env = os.environ.copy()
    runtime = env.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    bus = Path(runtime) / "bus"
    if not env.get("DBUS_SESSION_BUS_ADDRESS"):
        if not bus.exists():
            return None
        env["XDG_RUNTIME_DIR"] = runtime
        env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={bus}"
    else:
        env.setdefault("XDG_RUNTIME_DIR", runtime)
    return env


def _probe_systemd_user_scope(policy: MemoryPolicy, timeout_s: float | None) -> bool | None:
    """Return whether ``OOMPolicy`` works, or None if no capped scope launches."""
    env = _user_systemd_environ()
    if env is None:
        return None
    slice_name = caller_slice_name()
    for use_oom_policy in (True, False):
        argv = _scope_argv(
            ["/bin/true"], policy, f"lexicon-probe-{os.getpid()}-{uuid.uuid4().hex[:8]}",
            slice_name, timeout_s=timeout_s, use_oom_policy=use_oom_policy,
        )
        try:
            proc = subprocess.run(
                argv,
                env=env,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if proc.returncode == 0:
            return use_oom_policy
    return None


def systemd_user_scope_available(
    policy: MemoryPolicy | None = None, timeout_s: float | None = None
) -> bool:
    """Whether a scope accepts the exact cap properties for this launch."""
    return _probe_systemd_user_scope(policy or MemoryPolicy(), timeout_s) is not None


# Records ``oom_kill`` after the worker exits and before this process leaves
# the scope. The scope cgroup is removed once its last process exits, which
# is before the parent reaches ``_stop_user_scope``, so the parent cannot
# read ``memory.events`` itself. A missing record is not OOM proof for a scope.
_SCOPE_REAP_SCRIPT = """\
"$@"
rc=$?
rel=$(awk -F: '$1 == "0" { print $3; exit }' /proc/self/cgroup)
events="/sys/fs/cgroup${rel}/memory.events"
if [ -n "$rel" ] && [ -r "$events" ]; then
  awk '$1 == "oom_kill" { print $2; exit }' "$events" > "$LEXICON_OOM_EVENTS_FILE" || true
fi
if [ "$rc" -gt 128 ] && [ "$rc" -lt 256 ]; then
  kill -$((rc - 128)) $$
fi
exit "$rc"
"""


def _scope_reap_argv(cmd: list[str]) -> list[str]:
    """Run ``cmd`` in this cgroup, then record ``oom_kill`` before exiting."""
    return ["/bin/sh", "-c", _SCOPE_REAP_SCRIPT, "lexicon-scope-reap", *cmd]


def _read_recorded_oom_kill(path: Path) -> int | None:
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not text:
        return None
    try:
        value = int(text.split()[0])
    except (ValueError, IndexError):
        return None
    if value < 0:
        return None
    return value


def _stop_user_scope(unit: str, env: dict[str, str]) -> None:
    try:
        subprocess.run(
            ["systemctl", "--user", "stop", f"{unit}.scope"],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return


def _scope_argv(
    cmd: list[str], policy: MemoryPolicy, unit: str, slice_name: str | None,
    *, timeout_s: float | None = None, use_oom_policy: bool = True,
) -> list[str]:
    """``systemd-run --scope`` argv. ``--scope`` execs ``cmd`` in place after ``--``.

    ``--slice`` places the scope in the caller's slice, as a sibling of the
    caller's own scope. ``MemorySwapMax=0`` is required for the cap to
    SIGKILL: with swap left at ``max``, anonymous allocations are swapped
    and ``memory.max`` never fires. ``OOMPolicy=continue`` keeps the reaper
    alive long enough to record ``oom_kill`` after the worker is killed.
    """
    argv = [
        "systemd-run",
        "--user",
        "--scope",
        "--expand-environment=no",
        "--collect",
        "--quiet",
        f"--unit={unit}",
    ]
    if slice_name:
        argv.append(f"--slice={slice_name}")
    argv.extend(
        [
            "-p",
            f"MemoryMax={policy.max_bytes}",
            "-p",
            f"MemoryHigh={policy.high_bytes}",
            "-p",
            "MemorySwapMax=0",
        ]
    )
    if use_oom_policy:
        argv.extend(["-p", "OOMPolicy=continue"])
    if timeout_s is not None:
        argv.extend(["-p", f"RuntimeMaxSec={timeout_s}s"])
    argv.extend(["--", *cmd])
    return argv


def run_bounded_command(
    cmd: list[str],
    policy: MemoryPolicy,
    *,
    cwd: str,
    timeout_s: float | None,
) -> BoundedCommandResult:
    """Run ``cmd`` in a sibling scope, or as a plain child when that is unavailable.

    Availability comes from a scope probe using the launch properties, not
    from the worker's stderr. The scope is stopped in a ``finally`` so a normal
    exit, an exception, and ``KeyboardInterrupt`` all reap it. The plain
    child calls :func:`apply_worker_memory_limit` with ``RLIMIT_AS``.
    """
    use_oom_policy = _probe_systemd_user_scope(policy, timeout_s)
    scope_env = _user_systemd_environ() if use_oom_policy is not None else None
    if scope_env is not None:
        unit = f"lexicon-cap-{os.getpid()}-{uuid.uuid4().hex[:8]}"
        slice_name = caller_slice_name()
        proc: subprocess.CompletedProcess[str] | None = None
        oom_kill: int | None = None
        fd, oom_name = tempfile.mkstemp(prefix="lexicon-oom-")
        os.close(fd)
        oom_file = Path(oom_name)
        launch_env = dict(scope_env)
        launch_env["LEXICON_OOM_EVENTS_FILE"] = str(oom_file)
        try:
            proc = subprocess.run(
                _scope_argv(
                    _scope_reap_argv([*cmd, "--scope-capped"]), policy, unit, slice_name,
                    timeout_s=timeout_s, use_oom_policy=use_oom_policy,
                ),
                cwd=cwd,
                env=launch_env,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
            oom_kill = _read_recorded_oom_kill(oom_file)
        except FileNotFoundError:
            proc = None
        except subprocess.TimeoutExpired as exc:
            _log_mechanism("systemd_scope", unit)
            raise BoundedTimeoutExpired(exc, "systemd_scope") from exc
        except Exception:
            _log_mechanism("systemd_scope", unit)
            raise
        finally:
            _stop_user_scope(unit, scope_env)
            oom_file.unlink(missing_ok=True)
        if proc is not None:
            _log_mechanism("systemd_scope", unit)
            return BoundedCommandResult(completed=proc, mechanism="systemd_scope", oom_kill=oom_kill)
    plain_env = os.environ.copy()
    plain_env.pop("LEXICON_OOM_EVENTS_FILE", None)
    try:
        plain = subprocess.run(
            cmd,
            cwd=cwd,
            env=plain_env,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        _log_mechanism("rlimit_as", None)
        raise BoundedTimeoutExpired(exc, "rlimit_as") from exc
    _log_mechanism("rlimit_as", None)
    return BoundedCommandResult(completed=plain, mechanism="rlimit_as")


def _allocate_until_breach(target_bytes: int) -> None:
    """Allocate anonymous memory until the OS limit stops the process."""
    chunks: list[bytearray] = []
    chunk = 16 * 1024 * 1024
    allocated = 0
    while allocated < target_bytes:
        block = bytearray(chunk)
        for offset in range(0, chunk, 4096):
            block[offset] = 1
        chunks.append(block)
        allocated += chunk


def _self_test_child_main(max_bytes: int, result_path: str, *, scope_capped: bool = False) -> int:
    """Entry for ``python -m scripts.lexicon.runner.memory --self-test-child``."""
    kind = apply_worker_memory_limit(
        MemoryPolicy(high_bytes=max_bytes, max_bytes=max_bytes), scope_capped=scope_capped
    )
    payload: dict[str, object]
    if kind == "none":
        payload = {"kind": "none", "enforced": False, "detail": "no enforcement mechanism available"}
    else:
        try:
            _allocate_until_breach(max_bytes * 4)
            payload = {
                "kind": kind,
                "enforced": False,
                "detail": "allocation succeeded past limit — not enforced",
            }
        except MemoryError:
            payload = {"kind": kind, "enforced": True, "detail": "MemoryError raised under limit"}
        except Exception as exc:
            payload = {
                "kind": kind,
                "enforced": False,
                "detail": f"unexpected: {type(exc).__name__}: {exc}",
            }
    Path(result_path).write_text(json.dumps(payload) + "\n", encoding="utf-8")
    return 0 if payload.get("enforced") else 1


def run_startup_self_test(
    *,
    test_max_bytes: int | None = None,
    timeout_s: float = 30.0,
) -> EnforcementProof:
    """Prove the configured limit is enforced in a disposable child process."""
    interpreter = project_interpreter()
    if test_max_bytes is None:
        rss = current_rss_bytes() or (64 * 1024 * 1024)
        test_max_bytes = max(rss + 64 * 1024 * 1024, 128 * 1024 * 1024)
        test_max_bytes = min(test_max_bytes, 512 * 1024 * 1024)

    with tempfile.TemporaryDirectory(prefix="lexicon-mem-") as tmp:
        result_path = Path(tmp) / "self_test.json"
        policy = MemoryPolicy(high_bytes=test_max_bytes, max_bytes=test_max_bytes)
        bounded = run_bounded_command(
            [
                str(interpreter),
                "-m",
                "scripts.lexicon.runner.memory",
                "--self-test-child",
                str(test_max_bytes),
                str(result_path),
            ],
            policy,
            cwd=str(ROOT),
            timeout_s=timeout_s,
        )
        proc = bounded.completed
        if result_path.is_file():
            data = json.loads(result_path.read_text(encoding="utf-8"))
            child_kind = str(data.get("kind") or "")
            return EnforcementProof(
                kind=_proof_kind(bounded.mechanism, child_kind),
                enforced=bool(data.get("enforced")),
                detail=str(data.get("detail") or ""),
                max_bytes=test_max_bytes,
            )
        # No result file. Kind follows the mechanism that ran. A scope needs
        # an oom_kill record; a plain child can use the SIGKILL fallback.
        kind = _proof_kind(bounded.mechanism, None)
        if classify_oom_exit(
            proc.returncode, oom_kill=bounded.oom_kill,
            require_oom_record=bounded.mechanism == "systemd_scope",
        ) and kind != "none":
            return EnforcementProof(
                kind=kind,
                enforced=True,
                detail=f"child terminated by OS (returncode={proc.returncode})",
                max_bytes=test_max_bytes,
            )
        detail = (proc.stderr or proc.stdout or "").strip() or f"no result (returncode={proc.returncode})"
        return EnforcementProof(
            kind=kind,
            enforced=False,
            detail=detail[:500],
            max_bytes=test_max_bytes,
        )


def require_hard_cap_protection(proof: EnforcementProof) -> None:
    """Refuse to claim hard-cap protection when the self-test did not prove enforcement."""
    if not proof.enforced or proof.kind == "none":
        raise RuntimeError(
            "hard memory cap self-test failed — refusing to claim hard-cap protection: "
            f"{proof.detail}"
        )


def classify_oom_exit(
    exitcode: int | None,
    *,
    memory_error: bool = False,
    oom_kill: int | None = None,
    require_oom_record: bool = False,
) -> bool:
    """Return True when a worker exit should be classified as OOM.

    A readable ``oom_kill`` count decides: only a cgroup OOM kill counts, so
    an external SIGKILL (``oom_kill == 0``) does not. For a scope, an
    unreadable count is not OOM evidence. A plain child can use SIGKILL
    (returncode ``-9`` or ``137``) when no count is available.
    ``-15`` is SIGTERM from stopping the scope and is not an OOM.
    """
    if memory_error:
        return True
    if oom_kill is not None:
        return oom_kill > 0
    if require_oom_record:
        return False
    if exitcode is None:
        return False
    return exitcode in {-9, 137}


def current_rss_bytes() -> int | None:
    """Best-effort RSS for telemetry only (not enforcement)."""
    if platform.system() == "Darwin":
        try:
            libc_name = ctypes.util.find_library("c") or "libc.dylib"
            libc = ctypes.CDLL(libc_name, use_errno=True)

            class Rusage(ctypes.Structure):
                _fields_: ClassVar[list[tuple[str, type]]] = [
                    ("ru_utime", ctypes.c_int64 * 2),
                    ("ru_stime", ctypes.c_int64 * 2),
                    ("ru_maxrss", ctypes.c_int64),
                ]

            getrusage = libc.getrusage
            getrusage.argtypes = [ctypes.c_int, ctypes.POINTER(Rusage)]
            usage = Rusage()
            if getrusage(resource.RUSAGE_SELF, ctypes.byref(usage)) == 0:
                return int(usage.ru_maxrss)
        except OSError:
            return None
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        rss = int(usage.ru_maxrss)
        if platform.system() == "Linux":
            return rss * 1024
        return rss
    except OSError:
        return None


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) in (3, 4) and args[0] == "--self-test-child":
        if len(args) == 4 and args[3] != "--scope-capped":
            return 2
        return _self_test_child_main(int(args[1]), args[2], scope_capped=len(args) == 4)
    print("usage: python -m scripts.lexicon.runner.memory --self-test-child MAX RESULT", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
