"""Hard memory enforcement for enrichment workers (#5230 PR1, #9143).

Polling is telemetry only. Limits are enforced by the OS:

- Linux: a transient ``systemd-run --user --scope`` whose cgroup contains only
  that worker. ``memory.high`` / ``memory.max`` are written only after
  ``cgroup.procs`` lists that worker alone. A shared cgroup is never written;
  the worker falls back to ``RLIMIT_AS``. ``MemorySwapMax=0`` is set on the
  scope because ``memory.max`` alone is absorbed by swap. OOM is the scope
  exit signal (typically SIGKILL, returncode -9) or ``MemoryError``.
- Other POSIX: ``RLIMIT_AS`` set in the child before importing the engine.

A startup self-test must prove enforcement; production refuses to claim hard-cap
protection if neither mechanism works.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import json
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

ROOT = Path(__file__).resolve().parents[3]


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


def apply_worker_memory_limit(policy: MemoryPolicy) -> EnforcementKind:
    """Apply the best available hard limit in the current (child) process."""
    if sys.platform.startswith("linux") and _apply_cgroup_v2(policy):
        return "cgroup_v2"
    try:
        _try_set_rlimit_as(policy.max_bytes)
        return "rlimit_as"
    except (ValueError, OSError) as exc:
        if os.environ.get("LEXICON_MEMORY_DEBUG"):
            print(f"RLIMIT_AS failed: {exc}", file=sys.stderr)
        return "none"


def _self_cgroup_dir() -> Path | None:
    """Return this process's cgroup v2 directory, or None when it cannot be read."""
    try:
        text = Path("/proc/self/cgroup").read_text(encoding="utf-8")
    except OSError:
        return None
    for line in text.splitlines():
        if line.startswith("0::"):
            relative = line.split(":", 2)[2].lstrip("/")
            return Path("/sys/fs/cgroup") / relative
    return None


def _cgroup_procs_exclusive(cgroup_dir: Path, worker_pid: int) -> bool:
    """True when ``cgroup.procs`` lists ``worker_pid`` and no other process."""
    if worker_pid <= 0:
        return False
    try:
        text = (cgroup_dir / "cgroup.procs").read_text(encoding="utf-8")
    except OSError:
        return False
    pids: set[int] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            pids.add(int(stripped))
        except ValueError:
            return False
    return pids == {worker_pid}


def _try_apply_cgroup_limit(cgroup_dir: Path, policy: MemoryPolicy, worker_pid: int) -> bool:
    """Write ``memory.high`` / ``memory.max`` only for an exclusive worker cgroup.

    A shared cgroup is left unchanged. Callers fall back to ``RLIMIT_AS``.
    """
    if not _cgroup_procs_exclusive(cgroup_dir, worker_pid):
        return False
    high_path = cgroup_dir / "memory.high"
    max_path = cgroup_dir / "memory.max"
    if not os.access(max_path, os.W_OK):
        return False
    try:
        with high_path.open("w", encoding="utf-8") as handle:
            handle.write(str(policy.high_bytes))
        with max_path.open("w", encoding="utf-8") as handle:
            handle.write(str(policy.max_bytes))
    except OSError:
        return False
    return True


def _apply_cgroup_v2(policy: MemoryPolicy) -> bool:
    """Best-effort exclusive-cgroup write. Shared cgroups are not modified."""
    cgroup_dir = _self_cgroup_dir()
    if cgroup_dir is None:
        return False
    return _try_apply_cgroup_limit(cgroup_dir, policy, os.getpid())


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


def _systemd_scope_rejected(proc: subprocess.CompletedProcess[str]) -> bool:
    """True when ``systemd-run`` exited without exec'ing the worker."""
    if proc.returncode <= 0:
        return False
    text = f"{proc.stderr or ''}{proc.stdout or ''}"
    markers = (
        "Failed to connect",
        "Failed to start transient",
        "Failed to create bus",
        "not been booted",
        "Access denied",
        "Interactive authentication",
        "Failed to parse",
    )
    return any(marker in text for marker in markers)


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


def _scope_argv(cmd: list[str], policy: MemoryPolicy, unit: str) -> list[str]:
    """``systemd-run --scope`` argv. ``--scope`` execs ``cmd`` in place after ``--``.

    ``MemorySwapMax=0`` is required for the cap to SIGKILL: with swap left at
    ``max``, anonymous allocations are swapped and ``memory.max`` never fires.
    """
    return [
        "systemd-run",
        "--user",
        "--scope",
        "--expand-environment=no",
        "--collect",
        "--quiet",
        f"--unit={unit}",
        "-p",
        f"MemoryMax={policy.max_bytes}",
        "-p",
        f"MemoryHigh={policy.high_bytes}",
        "-p",
        "MemorySwapMax=0",
        "--",
        *cmd,
    ]


def run_bounded_command(
    cmd: list[str],
    policy: MemoryPolicy,
    *,
    cwd: str,
    timeout_s: float | None,
) -> subprocess.CompletedProcess[str]:
    """Run ``cmd`` under a dedicated user scope, or as a plain child if that fails.

    The plain child still calls :func:`apply_worker_memory_limit`, which refuses
    to write a shared cgroup and uses ``RLIMIT_AS``.
    """
    scope_env = _user_systemd_environ()
    if scope_env is not None:
        unit = f"lexicon-cap-{os.getpid()}-{uuid.uuid4().hex[:8]}"
        try:
            proc = subprocess.run(
                _scope_argv(cmd, policy, unit),
                cwd=cwd,
                env=scope_env,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
        except FileNotFoundError:
            proc = None
        except subprocess.TimeoutExpired:
            _stop_user_scope(unit, scope_env)
            raise
        if proc is not None and not _systemd_scope_rejected(proc):
            return proc
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )


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


def _self_test_child_main(max_bytes: int, result_path: str) -> int:
    """Entry for ``python -m scripts.lexicon.runner.memory --self-test-child``."""
    kind = apply_worker_memory_limit(MemoryPolicy(high_bytes=max_bytes, max_bytes=max_bytes))
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
        proc = run_bounded_command(
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
        if result_path.is_file():
            data = json.loads(result_path.read_text(encoding="utf-8"))
            kind_s = str(data.get("kind") or "none")
            return EnforcementProof(
                kind=kind_s if kind_s in {"cgroup_v2", "rlimit_as", "none"} else "none",
                enforced=bool(data.get("enforced")),
                detail=str(data.get("detail") or ""),
                max_bytes=test_max_bytes,
            )
        # No result file — the scope SIGKILL (returncode -9) or exit 137 is OOM.
        if classify_oom_exit(proc.returncode):
            kind: EnforcementKind = "cgroup_v2" if sys.platform.startswith("linux") else "rlimit_as"
            return EnforcementProof(
                kind=kind,
                enforced=True,
                detail=f"child terminated by OS (returncode={proc.returncode})",
                max_bytes=test_max_bytes,
            )
        detail = (proc.stderr or proc.stdout or "").strip() or f"no result (returncode={proc.returncode})"
        return EnforcementProof(
            kind="none",
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


def classify_oom_exit(exitcode: int | None, *, memory_error: bool = False) -> bool:
    """Return True when a worker exit should be classified as OOM."""
    if memory_error:
        return True
    if exitcode is None:
        return False
    if exitcode < 0:
        return True
    return exitcode in {137, 9}


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
    if len(args) == 3 and args[0] == "--self-test-child":
        return _self_test_child_main(int(args[1]), args[2])
    print("usage: python -m scripts.lexicon.runner.memory --self-test-child MAX RESULT", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
