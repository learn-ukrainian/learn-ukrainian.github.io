"""Runner — the single entrypoint for all agent CLI invocations.

``runner.invoke(agent_name, prompt, ...)`` is the one public function every
caller in the codebase should use. Bridge, dispatch, delegate (future),
consult (future) — all route through here. No bespoke subprocess building
anywhere else.

Flow (see docs/design/agent-runtime.md § 4.2 for the full spec):

    1. Look up adapter class in registry, import it, instantiate.
    2. Validate mode is in adapter.supported_modes.
    3. Validate cwd is provided for write modes.
    4. Enforce resume policy: delegate/dispatch entrypoints may not pass
       session_id for agents with resume_policy="bridge_only".
    5. Check has_headroom(agent, model) — raise RateLimitedError pre-call
       if we're known rate-limited.
    6. Adapter builds the InvocationPlan.
    7. Spawn subprocess via Popen with watchdog (stall detection).
    8. Poll should_kill() every second; on return or kill, stop watchdog.
    9. Adapter parses the response into ParseResult.
    10. Build Result, write usage record atomically, return Result.
    11. On any failure, write a usage record with the appropriate outcome
        and raise the matching exception.

Issue: #1184
"""

from __future__ import annotations

import contextlib
import contextvars
import importlib
import logging
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ai_llm.fallback import (
    AttemptOutcome,
    CallResult,
    GeminiRung,
    resolve_allowed_auth_modes,
    run_gemini_fallback_ladder,
)

# Registry adapter paths are canonicalized under ``scripts.agent_runtime``.
# Import the ACP scope from that same module identity even when this runner is
# reached through the historical top-level ``agent_runtime`` package alias;
# otherwise ContextVar provenance is set on one module object and checked on
# another.
from scripts.agent_runtime.adapters.acpx import (
    ACPX_PARTICIPANT_CATALOG_TRANSPORTS,
    ACPX_PARTICIPANT_EFFORTS,
    ACPX_SUPPORTED_PARTICIPANTS,
    AcpxShadowRefusalError,
    AcpxTransportProvenance,
    _require_local_metadata_field,
    active_communication_scope,
)
from scripts.agent_runtime.adapters.acpx import TRANSPORT_ENV as ACPX_TRANSPORT_ENV
from scripts.entire.fleet_capture import FleetCapture, resolved_route

from .adapters.base import AgentAdapter
from .attribution import InvocationAttribution, resolve_invocation_attribution
from .env_sanitize import build_agent_env
from .errors import (
    AgentRuntimeError,
    AgentStalledError,
    AgentTimeoutError,
    AgentUnavailableError,
    RateLimitedError,
)
from .failover import (
    FailoverChain,
    FailoverCooldownStore,
    FailoverRoute,
    classify_failover_trigger,
    emit_runner_substitution_marker,
    load_failover_chain,
    ordered_available_routes,
    substitution_for_route,
    tool_config_with_route,
)
from .registry import AGENTS, get_agent_entry
from .result import ParseResult, Result
from .telemetry import InvocationTelemetry, resolve_invocation_telemetry
from .trail_isolation import prepare_trail_isolation
from .usage import has_headroom, write_record
from .watchdog import (
    WatchdogState,
    should_kill,
    start_watchdog,
    stop_watchdog,
    tail_liveness_file_for_debug,
)

try:
    from telemetry.emit import current_run_id, current_session_id
except ImportError:  # pragma: no cover - package import path
    from scripts.telemetry.emit import current_run_id, current_session_id

# Poll interval while waiting on subprocess + watchdog. 1s is a good balance:
# fast enough that stall detection fires within 1s of the threshold, slow
# enough that we don't burn CPU in the wait loop.
_POLL_INTERVAL_S = 1.0
_logger = logging.getLogger(__name__)
_STDIN_TEMP_PREFIX = "agent-runtime-stdin-"
_SHIMS_DIR = Path(__file__).resolve().parent / "shims"
# Repo root that owns this runner (scripts/agent_runtime/runner.py → parents[2]).
# Used by the #4446 write-cwd guard as a cheap pre-filter: only a cwd inside this
# checkout's own file tree can be its protected primary checkout.
_RUNNER_REPO_TREE = Path(__file__).resolve().parents[2]
_MCP_RUNTIME_INIT_TIMEOUT_S = 30.0
_MCP_TOOL_EVENT_RE = re.compile(
    r"\bmcp:\s+(?P<server>[A-Za-z0-9_.-]+)/(?P<tool>[A-Za-z0-9_.-]+)\s+"
    r"(?:started|\(completed\))"
)
_MCP_TRANSPORT_FAILURE_RE = re.compile(r"ERROR\s+rmcp::transport::worker:")
_MCP_FAILURE_URL_RE = re.compile(r"url \((?P<url>https?://[^)\s]+)\)")
_PRIVACY_LIMITED_USAGE_ENTRYPOINTS = frozenset(
    {
        "acpx-pilot-native",
        "acpx-pilot-shadow",
        "acpx-discuss",
        "acpx-discuss-synthesis",
        "acpx-transport",
    }
)
# ACP transports can emit a large JSON-RPC envelope around a concise answer.
# Production observations now include GLM at 4,204,632 bytes (#6159), plus
# Kimi and Grok crossing the former 256 KiB cap before their terminal frames
# (#6235). Keep every enabled ACP route bounded by the same proven envelope;
# the adapter independently caps parsed answer text before it can be returned
# to fleet authority.
_ACPX_DIRECT_OUTPUT_LIMIT_BYTES = 16 * 1024 * 1024
_SAFE_ACP_FAILURE_CODES = frozenset(
    {
        "acp_adapter_incompatible",
        "acp_adapter_missing",
        "acp_agent_disconnected",
        "acp_agent_startup",
        "acp_auth_required",
        "acp_permission_denied",
        "acp_permission_unavailable",
        "acp_session_create_timeout",
        "adapter_refused",
        "protocol_output_limit",
        "provider_unavailable",
        "rate_limited",
        "result_invalid",
        "timeout",
        "transport_error",
        "unknown",
    }
)

# In-process cache of instantiated adapters. Adapters are stateless so we
# can reuse one instance across all invocations of the same agent.
_ADAPTER_CACHE: dict[str, AgentAdapter] = {}
_INVOCATION_ATTRIBUTION: contextvars.ContextVar[InvocationAttribution | None] = (
    contextvars.ContextVar("agent_runtime_invocation_attribution", default=None)
)
_INTER_AGENT_TRANSPORT: contextvars.ContextVar[AcpxTransportProvenance | None] = (
    contextvars.ContextVar("agent_runtime_inter_agent_transport", default=None)
)
_INTER_AGENT_TRANSPORT_NAME = "acp"
_RESERVED_TRANSPORT_PROVENANCE = frozenset({"source", "agent", "via"})


class AgentOutputLimitError(AgentRuntimeError):
    """A bounded ACP direct-route invocation exceeded its streamed-output cap."""

    def __init__(self, agent: str, limit_bytes: int, observed_bytes: int):
        self.agent = agent
        self.limit_bytes = limit_bytes
        self.observed_bytes = observed_bytes
        super().__init__(
            f"{agent} exceeded streamed_output_limit={limit_bytes} bytes "
            f"(observed={observed_bytes})"
        )


class InterAgentTransportError(AgentRuntimeError):
    """Refusal at the ACP-only inter-agent transport boundary.

    This is deliberately distinct from an adapter/process failure: callers
    must not translate it into a legacy bridge retry.  The requested route was
    unavailable, unsupported, malformed, or lacked trusted provenance before
    any provider process could be spawned.
    """


def _streamed_output_limit(*, agent_name: str, entrypoint: str) -> int | None:
    """Return the opt-in cap for isolated ACP direct-only seats only."""
    acpx_seats = {str(route["seat"]) for route in ACPX_SUPPORTED_PARTICIPANTS.values()}
    if (
        agent_name in acpx_seats
        and entrypoint in {"acpx-pilot-shadow", "acpx-discuss", "acpx-transport"}
    ):
        return _ACPX_DIRECT_OUTPUT_LIMIT_BYTES
    return None


def _resolve_plan_telemetry(
    *,
    agent_name: str,
    plan: Any,
    requested_model: str,
    requested_effort: str | None,
    tool_config: Mapping[str, Any] | None,
) -> InvocationTelemetry:
    """Resolve telemetry without pre-sandbox reviewer execution.

    Generic telemetry probes ``argv[0] --version``. For isolated review that
    would execute the reviewer before the runner installs the OS sandbox, so
    version remains explicitly unknown; the exact binary is instead hashed and
    help/version-probed inside the verified sandbox by the isolation layer.
    """
    if tool_config and tool_config.get("review_isolation"):
        return InvocationTelemetry(
            model=requested_model,
            effort=requested_effort or "unknown",
            cli_version="unknown",
        )
    return resolve_invocation_telemetry(
        agent_name=agent_name,
        plan=plan,
        requested_model=requested_model,
        requested_effort=requested_effort,
    )


class _PTYUnavailableError(RuntimeError):
    """Raised when PTY setup itself fails on this host.

    Distinguishes "PTY allocation / termios setup failed" (the
    fail-soft case where we fall back to pipe spawn) from "Popen
    failed because the binary doesn't exist" (a real error the
    caller must surface). Both would otherwise show up as ``OSError``,
    which made the original fail-soft path swallow binary-not-found
    errors with a misleading warning.
    """


def _pty_disabled_via_env() -> bool:
    """Return True when ``DELEGATE_DISABLE_PTY`` opts back into pipe spawn.

    Read at call time (not module import) so tests can flip the env var
    inside a single process without re-importing the module.
    """
    return os.environ.get("DELEGATE_DISABLE_PTY", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _stdin_uses_text_mode(stdin: Any) -> bool:
    """Return True when Popen should use text mode for pipe stdout/stderr."""
    import io

    if stdin in (subprocess.PIPE, subprocess.DEVNULL, None):
        return True
    return isinstance(stdin, io.TextIOBase)


def _prepare_stdin_handle(
    stdin_payload: str,
    *,
    directory: Path | None = None,
    unlink_after_open: bool = False,
) -> tuple[Any, Path | None]:
    """Return ``(stdin_for_Popen, temp_path)`` for a prompt payload.

    PTY-wrapped spawns with ``stdin=PIPE`` plus a large ``write()`` crash
    Codex CLI before session init (#2159). Feeding stdin from a temp file
    matches ``cat prompt.txt | codex exec -`` and avoids the silent exit-1
    path where ``BrokenPipeError`` was previously swallowed.
    """
    if not stdin_payload:
        return subprocess.DEVNULL, None

    fd, path_str = tempfile.mkstemp(
        prefix=_STDIN_TEMP_PREFIX,
        suffix=".txt",
        dir=str(directory) if directory is not None else None,
    )
    path = Path(path_str)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(stdin_payload.encode("utf-8"))
    except OSError:
        with contextlib.suppress(OSError):
            path.unlink()
        raise

    # Ownership transfers to the subprocess lifecycle; _cleanup_stdin_temp
    # closes it in the runner finally block.
    handle = open(path, encoding="utf-8")  # noqa: SIM115
    if unlink_after_open:
        path.unlink()
        return handle, None
    return handle, path


def _cleanup_stdin_temp(path: Path | None, handle: Any) -> None:
    if handle not in (None, subprocess.DEVNULL, subprocess.PIPE):
        with contextlib.suppress(OSError):
            handle.close()
    if path is not None and _is_temp_file(path):
        with contextlib.suppress(OSError):
            path.unlink()


def _spawn_pty_subprocess(
    cmd: Sequence[str],
    *,
    cwd: Path | str,
    env: Mapping[str, str],
    stdin: Any = subprocess.DEVNULL,
    pty_window: tuple[int, int] = (40, 200),
    stderr_pipe: bool = False,
) -> tuple[subprocess.Popen, int, int | None]:
    """Spawn ``cmd`` with PTY stdout and optionally pipe-backed stderr.

    Returns ``(proc, stdout_master_fd, stderr_master_fd)``. When
    ``stderr_pipe`` is true, the final item is ``None`` and stderr is drained
    from ``proc.stderr`` instead. The slave fds are closed in the parent
    immediately after spawn so EOF / EIO propagates when the child closes its
    side.

    PTY usage forces the child's libc to detect a TTY and switch from
    block-buffered to line-buffered stdout. Without this, agents that
    write to stdout via stdio (most CLIs) emit no data to the parent
    for minutes at a time, defeating the watchdog's silence-timeout
    detection. See #2071 + watchdog.py::should_kill incident chain
    (#1184): Gemini block-buffers stdout when not a TTY → stdout
    streamer goes silent → looks identical to a hang but is actually
    successful work.

    Per-slave termios: ``OPOST`` is disabled so the kernel does NOT
    convert ``\\n`` to ``\\r\\n`` on output. That keeps stream-json
    payloads byte-identical to what the child wrote — which the
    streamer's UTF-8 decode + ANSI strip expects. We additionally
    set ``TIOCSWINSZ`` to ``pty_window`` so children that query
    terminal size for output formatting get sane defaults.

    Caller is responsible for closing the master fds via the watchdog's
    ``stop_watchdog(..., stdout_master_fd=..., stderr_master_fd=...)``.
    """
    # --- Phase 1: PTY allocation + termios configuration. ---
    # Failure here is "PTY unavailable on this host" — surface a
    # dedicated exception so the caller can fall back to pipe spawn
    # rather than swallowing unrelated Popen errors with a misleading
    # warning.
    try:
        import fcntl
        import pty
        import struct
        import termios

        stdout_master, stdout_slave = pty.openpty()
        stderr_master: int | None = None
        stderr_slave: int | None = None
        if not stderr_pipe:
            try:
                stderr_master, stderr_slave = pty.openpty()
            except (OSError, AttributeError):
                with contextlib.suppress(OSError):
                    os.close(stdout_master)
                with contextlib.suppress(OSError):
                    os.close(stdout_slave)
                raise

        # Disable OPOST on each slave so \n stays \n (no ONLCR rewrite).
        # Belt-and-suspenders: the streamer also strips \r\n → \n if a
        # platform somehow ignores the termios change. Suppression is
        # narrow — these calls are advisory; the spawn proceeds either
        # way.
        slave_fds = (stdout_slave,) if stderr_slave is None else (stdout_slave, stderr_slave)
        for slave_fd in slave_fds:
            with contextlib.suppress(termios.error, OSError):
                attrs = termios.tcgetattr(slave_fd)
                attrs[1] &= ~termios.OPOST  # oflag
                termios.tcsetattr(slave_fd, termios.TCSANOW, attrs)

        # Set sane window size so agents that query TIOCGWINSZ for output
        # formatting (e.g. ANSI tables) get reasonable defaults.
        winsize = struct.pack("HHHH", pty_window[0], pty_window[1], 0, 0)
        for slave_fd in slave_fds:
            with contextlib.suppress(OSError):
                fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, winsize)
    except (OSError, AttributeError) as exc:
        raise _PTYUnavailableError(f"PTY setup failed ({type(exc).__name__}: {exc})") from exc

    # --- Phase 2: spawn the child against the PTY slaves. ---
    # Any failure here (FileNotFoundError, PermissionError, generic
    # OSError) is a real spawn problem and must propagate UNCHANGED so
    # the runner's existing FileNotFoundError handling can turn it into
    # AgentUnavailableError. Do NOT translate this to PTYUnavailable.
    try:
        text_mode = _stdin_uses_text_mode(stdin)
        proc = subprocess.Popen(
            list(cmd),
            cwd=str(cwd),
            env=dict(env),
            stdin=stdin,
            stdout=stdout_slave,
            stderr=subprocess.PIPE if stderr_pipe else stderr_slave,
            text=text_mode,
            bufsize=1 if text_mode else -1,
            start_new_session=True,
        )
    except BaseException:
        for fd in (stdout_master, stderr_master, stdout_slave, stderr_slave):
            if fd is None:
                continue
            with contextlib.suppress(OSError):
                os.close(fd)
        raise

    # Parent does NOT need slave fds; close them so EOF arrives on
    # master when child closes its side.
    for slave_fd in (stdout_slave, stderr_slave):
        if slave_fd is not None:
            with contextlib.suppress(OSError):
                os.close(slave_fd)

    return proc, stdout_master, stderr_master


def _spawn_pipe_subprocess(
    cmd: Sequence[str],
    *,
    cwd: Path | str,
    env: Mapping[str, str],
    stdin: Any = subprocess.DEVNULL,
) -> tuple[subprocess.Popen, None, None]:
    """Spawn ``cmd`` with PIPE stdout/stderr (legacy pre-PTY path).

    Returned only when ``DELEGATE_DISABLE_PTY`` is set OR PTY is
    unavailable on the host (rare; ``pty`` is POSIX). Reserved as an
    escape hatch in case PTY mode regresses for a specific agent
    (e.g. one that emits ANSI codes in the middle of stream-json
    events and breaks parsing). See ``_spawn_subprocess`` for the
    fail-soft selection logic.
    """
    proc = subprocess.Popen(
        list(cmd),
        stdin=stdin,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=_stdin_uses_text_mode(stdin),
        cwd=str(cwd),
        env=dict(env),
        bufsize=1 if _stdin_uses_text_mode(stdin) else -1,
        start_new_session=True,
    )
    return proc, None, None


def _spawn_subprocess(
    cmd: Sequence[str],
    *,
    cwd: Path | str,
    env: Mapping[str, str],
    stdin: Any,
    stderr_pipe: bool = False,
) -> tuple[subprocess.Popen, int | None, int | None]:
    """Spawn ``cmd`` using PTY mode by default; pipe mode on opt-out.

    Fail-soft: if ``pty.openpty()`` or the termios calls raise on the
    host platform (Linux containers without /dev/pts, etc.), fall back
    to pipe-based spawn with a warning rather than crashing the
    runner. Pipe mode is correct but defeats the block-buffer fix —
    that's the trade-off the env var documents.

    Popen failures (missing binary, EACCES) are NOT caught here — they
    propagate as ``FileNotFoundError`` / ``PermissionError`` / ``OSError``
    so the caller's existing ``AgentUnavailableError`` mapping fires.
    """
    if _pty_disabled_via_env():
        return _spawn_pipe_subprocess(cmd, cwd=cwd, env=env, stdin=stdin)
    try:
        return _spawn_pty_subprocess(
            cmd,
            cwd=cwd,
            env=env,
            stdin=stdin,
            stderr_pipe=stderr_pipe,
        )
    except _PTYUnavailableError as exc:
        import warnings

        warnings.warn(
            f"{exc}; falling back to pipe-based spawn. Set DELEGATE_DISABLE_PTY=1 to silence this warning.",
            RuntimeWarning,
            stacklevel=2,
        )
        return _spawn_pipe_subprocess(cmd, cwd=cwd, env=env, stdin=stdin)


def _normalize_mcp_url(url: str | None) -> str:
    """Normalize MCP endpoint URLs for observer attribution."""
    return str(url or "").strip().rstrip("/")


def _validate_agent_name(agent_name: str) -> None:
    """Reject legacy public labels before registry lookup."""
    if agent_name.endswith("-tools") and agent_name not in AGENTS:
        bare_name = agent_name.removesuffix("-tools")
        if bare_name in AGENTS:
            raise ValueError(
                "agent_runtime registry uses bare names — pass "
                f"{bare_name!r} not {agent_name!r}; use tool_config to "
                "indicate tools-enabled"
            )


def _is_agent_runtime_shim(path: str | None) -> bool:
    if not path:
        return False
    candidate = Path(path)
    return len(candidate.parts) >= 3 and candidate.parts[-3:] == ("agent_runtime", "shims", candidate.name)


def _resolve_real_binary(binary: str, *, original_path: str) -> str | None:
    for path_entry in original_path.split(os.pathsep):
        if not path_entry:
            continue
        candidate = Path(path_entry) / binary
        if _is_agent_runtime_shim(str(candidate)):
            continue
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return shutil.which(binary, path=original_path)


def _merge_guard_enabled(*, mode: str, env: dict[str, str]) -> bool:
    """Return whether merge/approve/push-to-main operations must be blocked."""
    if env.get("AGENT_ALLOW_MERGE") == "1":
        return False
    if env.get("AGENT_NO_MERGE") == "1":
        return True
    return mode == "danger"


def _apply_merge_guard(*, mode: str, env: dict[str, str]) -> dict[str, str]:
    """Prepend gh/git shims and stamp env vars when merge guard is active."""
    if not _merge_guard_enabled(mode=mode, env=env):
        unguarded_env = dict(env)
        unguarded_env.pop("AGENT_NO_MERGE", None)
        return unguarded_env

    guarded_env = dict(env)
    original_path = guarded_env.get("PATH", "")
    guarded_env["AGENT_NO_MERGE"] = "1"
    guarded_env["AGENT_ORIGINAL_PATH"] = original_path

    real_gh = _resolve_real_binary("gh", original_path=original_path) if original_path else None
    if real_gh:
        guarded_env["AGENT_REAL_GH"] = real_gh
    else:
        guarded_env.pop("AGENT_REAL_GH", None)

    real_git = _resolve_real_binary("git", original_path=original_path) if original_path else None
    if real_git:
        guarded_env["AGENT_REAL_GIT"] = real_git
    else:
        guarded_env.pop("AGENT_REAL_GIT", None)

    shim_path = str(_SHIMS_DIR)
    guarded_env["PATH"] = f"{shim_path}{os.pathsep}{original_path}" if original_path else shim_path
    return guarded_env


def _kill_process_tree(proc: subprocess.Popen) -> None:
    """Kill a subprocess and all its descendants via process-group SIGKILL.

    When the subprocess was started with ``start_new_session=True`` (which
    calls ``os.setsid()``, putting the child in its own process group), this
    sends SIGKILL to the entire group — ensuring no orphaned children survive.

    If the process wasn't started with ``start_new_session=True`` (shouldn't
    happen, but defensive), falls back to ``proc.kill()`` on the PID alone.

    Issue: #1286 — Codex ``exec`` spawns child processes (sandboxed workloads,
    runtime daemons) that survive when only the parent PID is killed, leading
    to accumulating stale reviewer subprocesses.
    """
    try:
        pgid = os.getpgid(proc.pid)
    except (OSError, ProcessLookupError):
        # Process already gone.
        return

    if pgid == proc.pid:
        # Process IS a process-group leader (started with start_new_session).
        # Kill the entire group.
        with contextlib.suppress(OSError, ProcessLookupError):
            os.killpg(pgid, signal.SIGKILL)
    else:
        # Fallback: not a group leader, just kill the PID.
        with contextlib.suppress(OSError, ProcessLookupError):
            proc.kill()

    # Reap the direct child to prevent zombies. Children in the group are
    # re-parented to init/PID 1 on parent exit; os.killpg already sent them
    # SIGKILL, so init will reap them.
    try:
        proc.wait(timeout=10.0)
    except subprocess.TimeoutExpired:
        # Last resort — non-blocking waitpid to avoid blocking forever.
        with contextlib.suppress(ChildProcessError, OSError):
            os.waitpid(proc.pid, os.WNOHANG)


def _is_temp_file(path: Path) -> bool:
    """Check if a file is in a system temp directory (safe to auto-delete).

    The old guard ``str(path).startswith("/tmp/")`` is Linux-only. On macOS,
    ``tempfile.mkdtemp()`` returns ``/var/folders/.../T/...``, so the guard
    never matched and temp files accumulated.  Issue: #1286.
    """
    import tempfile as _tempfile

    s = str(path)
    # Fast path: covers Linux and explicit /tmp/ usage.
    if s.startswith("/tmp/") or s.startswith("/private/tmp/"):
        return True
    # Cross-platform: check if the file is under the system temp dir.
    try:
        tmpdir = _tempfile.gettempdir()
        return s.startswith(tmpdir + "/")
    except Exception:
        return False


def _load_adapter(name: str, *, allow_direct_only: bool = False) -> AgentAdapter:
    """Import the adapter class for ``name`` and cache the instance.

    Raises:
        AgentUnavailableError: If ``name`` is not in the registry, the
            entry has ``cli_available: False``, or the adapter module
            cannot be imported.
    """
    try:
        entry = get_agent_entry(name)
    except KeyError:
        raise AgentUnavailableError(
            f"Agent {name!r} is not in the registry. Available: {sorted(AGENTS.keys())}"
        ) from None

    direct_only_allowed = allow_direct_only and entry.get("direct_only") is True
    if not entry["cli_available"] and not direct_only_allowed:
        if entry.get("direct_only") is True:
            detail = (
                "Direct-only seats require their dedicated bounded invocation "
                "surface and never participate in normal routing, dispatch, "
                "review, or failover."
            )
        else:
            detail = (
                "This seat has no enabled runtime CLI/adapter. Enable its "
                "intended adapter or launcher and flip the registry flag only "
                "when the seat is operational."
            )
        raise AgentUnavailableError(
            f"Agent {name!r} is registered but not available "
            f"(cli_available=False). {detail}"
        )

    # Permission is checked before cache access. A prior direct-only load must
    # never make the same adapter reachable through normal ``invoke()``.
    if name in _ADAPTER_CACHE:
        return _ADAPTER_CACHE[name]

    dotted_path = entry["adapter"]
    if ":" not in dotted_path:
        raise AgentUnavailableError(
            f"Malformed adapter path in registry: {dotted_path!r}. Expected 'module.path:ClassName'."
        )
    module_path, class_name = dotted_path.split(":", 1)

    # Try the registered dotted path first. If that fails and the path
    # starts with "scripts." (which requires the repo root on sys.path,
    # not just `scripts/`), fall back to the path without that prefix.
    # This lets the runner work whether it's invoked via
    # `python -m scripts.agent_runtime.runner` (repo root on path) or
    # `python scripts/build/v6_build.py` (only scripts/ on path).
    module = None
    import_errors: list[str] = []
    candidates = [module_path]
    if module_path.startswith("scripts."):
        candidates.append(module_path.removeprefix("scripts."))
    for candidate in candidates:
        try:
            module = importlib.import_module(candidate)
            break
        except ImportError as exc:
            import_errors.append(f"{candidate!r}: {exc}")
    if module is None:
        raise AgentUnavailableError(
            f"Failed to import adapter for agent {name!r}. Tried: "
            + "; ".join(import_errors)
            + ". This usually means the adapter file hasn't been implemented yet."
        )

    try:
        adapter_cls = getattr(module, class_name)
    except AttributeError as exc:
        raise AgentUnavailableError(
            f"Adapter class {class_name!r} not found in module {module_path!r} for agent {name!r}."
        ) from exc

    adapter: AgentAdapter = adapter_cls()
    _ADAPTER_CACHE[name] = adapter
    return adapter


def _enforce_resume_policy(
    agent_name: str,
    session_id: str | None,
    entrypoint: str,
) -> None:
    """Enforce resume policy from the registry.

    Design doc § 6.3: bridge-only agents may resume through the bridge.
    Delegate, dispatch, and consult never resume because a worktree is the
    isolation boundary.

    If a caller tries to pass ``session_id`` when policy forbids it, we
    raise ValueError. This is a hard invariant — we'd rather crash loudly
    at the boundary than let a coding-task invocation silently carry
    stale context from a different worktree.
    """
    if session_id is None:
        return  # No resume requested → nothing to enforce.

    entry = get_agent_entry(agent_name)
    policy = entry["resume_policy"]

    if policy == "never":
        raise ValueError(
            f"Agent {agent_name!r} has resume_policy='never' but a session_id "
            f"was passed. This is a hard constraint (see docs/design/"
            f"agent-runtime.md § 6.3). If you believe this is wrong, change "
            f"the registry, not the call site."
        )

    if policy == "bridge_only" and entrypoint not in ("bridge",):
        raise ValueError(
            f"Agent {agent_name!r} has resume_policy='bridge_only' but "
            f"session_id was passed from entrypoint={entrypoint!r}. Only "
            f"the 'bridge' entrypoint may use session resume for this "
            f"agent. delegate/dispatch/consult must always start fresh."
        )


def _build_usage_record(
    *,
    agent: str,
    entrypoint: str,
    model: str,
    mode: str,
    task_id: str | None,
    cwd: Path,
    session_id: str | None,
    duration_s: float,
    input_chars: int,
    output_chars: int,
    returncode: int | None,
    outcome: str,
    rate_limited: bool,
    stalled: bool,
    stderr_excerpt: str | None,
    tokens: int | None,
    substitution: dict[str, Any] | None = None,
    failure_code: str | None = None,
) -> dict[str, Any]:
    """Assemble the usage record dict per design doc § 4.5 schema."""
    # Ensure unbounded strings are capped so the JSON stays under POSIX PIPE_BUF (4KB)
    # to maintain atomic append guarantees in usage.py.
    privacy_limited = entrypoint in _PRIVACY_LIMITED_USAGE_ENTRYPOINTS
    safe_cwd = None if privacy_limited else (str(cwd)[-250:] if cwd else "")
    safe_task_id = None if privacy_limited else (task_id[:100] if task_id else None)
    safe_provider_session_id = (
        None if privacy_limited else (session_id[:100] if session_id else None)
    )
    telemetry_source = None if privacy_limited else os.environ.get("LU_TELEMETRY_SOURCE")
    attribution = _INVOCATION_ATTRIBUTION.get() or resolve_invocation_attribution(
        task_id=task_id
    )
    transport = _INTER_AGENT_TRANSPORT.get()

    failure_code = _privacy_safe_failure_code(
        outcome=outcome,
        rate_limited=rate_limited,
        stalled=stalled,
        returncode=returncode,
        explicit_code=failure_code,
    )
    record = {
        "ts": datetime.now(UTC).isoformat(),
        "agent": agent,
        "entrypoint": entrypoint,
        "task_id": safe_task_id,
        "cwd": safe_cwd,
        "model": model,
        "mode": mode,
        "run_id": None if privacy_limited else current_run_id()[:100],
        "session_id": None if privacy_limited else current_session_id()[:100],
        "provider_session_id": safe_provider_session_id,
        "level": None if privacy_limited else os.environ.get("LU_TELEMETRY_LEVEL"),
        "slug": None if privacy_limited else os.environ.get("LU_TELEMETRY_SLUG"),
        "track": None if privacy_limited else os.environ.get("LU_TELEMETRY_TRACK"),
        "source": telemetry_source[:100] if telemetry_source else None,
        "initiator": attribution.initiator,
        "attribution_source": attribution.source,
        "attribution_task_id": attribution.task_id,
        "duration_s": round(duration_s, 2),
        "input_chars": input_chars,
        "output_chars": output_chars,
        "returncode": returncode,
        "outcome": outcome,
        "rate_limited": rate_limited,
        "stalled": stalled,
        "failure_code": failure_code,
        "stderr_excerpt": (
            None
            if privacy_limited
            else ((stderr_excerpt or "")[:500] if stderr_excerpt else None)
        ),
        "tokens": tokens,
    }
    safe_substitution = _safe_substitution_record(substitution)
    if safe_substitution is not None:
        record["substitution"] = safe_substitution
    if transport is not None:
        # The context is installed only by invoke_inter_agent(); no caller
        # metadata is permitted to supply or overwrite these fields.
        record["transport"] = transport.metadata()
    return record


def _privacy_safe_failure_code(
    *,
    outcome: str,
    rate_limited: bool,
    stalled: bool,
    returncode: int | None,
    explicit_code: str | None = None,
) -> str | None:
    """Classify a failure without persisting provider text or dynamic detail."""
    normalized_outcome = str(outcome or "").casefold()
    if normalized_outcome == "ok":
        return None
    if explicit_code in _SAFE_ACP_FAILURE_CODES:
        return explicit_code
    if rate_limited or normalized_outcome == "rate_limited":
        return "rate_limited"
    if stalled or normalized_outcome in {"timeout", "hard_timeout", "stalled"}:
        return "timeout"

    code = "transport_error" if returncode not in (None, 0) else "unknown"
    return code if code in _SAFE_ACP_FAILURE_CODES else "unknown"


def _safe_substitution_record(
    substitution: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Return a bounded, non-secret substitution payload for persistence."""
    if not isinstance(substitution, dict):
        return None
    safe: dict[str, Any] = {}
    for key in (
        "requested_provider",
        "requested_model",
        "actual_provider",
        "actual_model",
        "source",
        "marker",
    ):
        value = substitution.get(key)
        safe[key] = str(value)[:200] if value is not None else None
    safe["substituted"] = bool(substitution.get("substituted"))
    return safe


def _emit_substitution_event(
    *,
    agent_name: str,
    entrypoint: str,
    task_id: str | None,
    cwd: Path,
    model: str,
    substitution: dict[str, Any] | None,
    event_sink: Callable[..., None] | None,
) -> None:
    """Emit a telemetry event when a harness-level provider/model changed."""
    safe_substitution = _safe_substitution_record(substitution)
    if not safe_substitution or not safe_substitution.get("substituted"):
        return
    payload = {
        "agent": agent_name,
        "entrypoint": entrypoint,
        "task_id": task_id[:100] if task_id else None,
        "cwd": str(cwd)[-250:] if cwd else "",
        "model": model,
        "substitution": safe_substitution,
    }
    if event_sink is not None:
        with contextlib.suppress(Exception):
            event_sink("agent_runtime_substitution", **payload)
    try:
        try:
            from telemetry.emit import emit_event
        except ImportError:  # pragma: no cover - package import path
            from scripts.telemetry.emit import emit_event

        emit_event("agent_runtime_substitution", payload)
    except Exception:
        pass


@dataclass(frozen=True)
class _ExecutionOutcome:
    """Runner-owned result for one spawned InvocationPlan."""

    parse: ParseResult
    duration_s: float
    returncode: int | None
    kill_reason: str | None
    stdout_text: str
    stderr_text: str
    liveness_paths: tuple[Path, ...]
    isolation_evidence: dict | None = None
    isolation_capability_digest: str | None = None
    isolation_prompt_digest: str | None = None
    isolation_prompt_transport: str | None = None


@dataclass
class _McpRuntimeObserver:
    """Emit one MCP runtime-init status per configured Codex server."""

    event_sink: Callable[..., None]
    agent_name: str
    task_id: str | None
    configured_servers: set[str]
    server_urls: dict[str, str]
    start_time: float
    timeout_s: float = _MCP_RUNTIME_INIT_TIMEOUT_S
    ready_servers: set[str] = field(default_factory=set)
    failed_servers: set[str] = field(default_factory=set)
    timed_out_servers: set[str] = field(default_factory=set)
    pending_ready_events: dict[str, dict[str, str]] = field(default_factory=dict)

    @classmethod
    def from_tool_config(
        cls,
        *,
        agent_name: str,
        task_id: str | None,
        tool_config: dict | None,
        event_sink: Callable[..., None] | None,
        start_time: float,
    ) -> _McpRuntimeObserver | None:
        if event_sink is None or agent_name != "codex":
            return None
        mcp_servers = (tool_config or {}).get("mcp_servers")
        if not isinstance(mcp_servers, dict) or not mcp_servers:
            return None
        server_urls = {
            name: str(config.get("url"))
            for name, config in mcp_servers.items()
            if isinstance(config, dict) and config.get("url")
        }
        return cls(
            event_sink=event_sink,
            agent_name=agent_name,
            task_id=task_id,
            configured_servers=set(mcp_servers),
            server_urls=server_urls,
            start_time=start_time,
        )

    def observe_lines(
        self,
        lines: list[str],
        *,
        start_index: int,
        stream: str,
    ) -> int:
        for line in lines[start_index:]:
            self.observe_line(line, stream=stream)
        return len(lines)

    def observe_line(self, line: str, *, stream: str) -> None:
        tool_match = _MCP_TOOL_EVENT_RE.search(line)
        if tool_match:
            server = tool_match.group("server")
            if server in self.configured_servers:
                self._emit_ready(
                    server,
                    tool=tool_match.group("tool"),
                    stream=stream,
                    line=line,
                )
            return

        failure_match = _MCP_TRANSPORT_FAILURE_RE.search(line)
        if not failure_match:
            return
        url_match = _MCP_FAILURE_URL_RE.search(line)
        servers = self._servers_for_failed_line(url_match.group("url") if url_match else None)
        if not servers:
            self._emit_unattributed_failure(stream=stream, line=line)
            return
        for server in servers:
            self._emit_failed(server, stream=stream, line=line)

    def maybe_emit_timeout(self, now: float) -> None:
        if now - self.start_time < self.timeout_s:
            return
        unresolved = self.configured_servers - self.ready_servers - self.failed_servers - self.timed_out_servers
        for server in sorted(unresolved):
            self.timed_out_servers.add(server)
            self._emit(
                server=server,
                status="timeout",
                stream=None,
                line=(f"no mcp runtime init line observed within {self.timeout_s:.0f}s"),
            )

    def _servers_for_failed_line(self, url: str | None) -> list[str]:
        normalized_url = _normalize_mcp_url(url)
        if not normalized_url:
            return []
        return [
            server
            for server, server_url in self.server_urls.items()
            if _normalize_mcp_url(server_url) == normalized_url
        ]

    def _emit_ready(
        self,
        server: str,
        *,
        tool: str,
        stream: str,
        line: str,
    ) -> None:
        """Record ready as pending; failed is terminal and suppresses it.

        Ordering is intentionally "failed trumps ready": a later transport
        failure for the same server wins over an earlier Codex
        ``mcp: server/tool started`` or ``(completed)`` line.
        """
        if server in self.failed_servers or server in self.timed_out_servers:
            return
        if server in self.ready_servers:
            return
        self.ready_servers.add(server)
        self.pending_ready_events[server] = {
            "tool": tool,
            "stream": stream,
            "line": line,
        }

    def _emit_failed(self, server: str, *, stream: str, line: str) -> None:
        """Emit failed immediately; failed is terminal and suppresses ready.

        If Codex prints both a ready line and a later transport failure for
        the same server, consumers see one final ``failed`` status rather
        than a ready/failed flap.
        """
        if server in self.failed_servers:
            return
        self.failed_servers.add(server)
        self.pending_ready_events.pop(server, None)
        self._emit(server=server, status="failed", stream=stream, line=line)

    def finalize(self) -> None:
        """Emit pending ready statuses that were not superseded by failures."""
        for server in sorted(self.pending_ready_events):
            if server in self.failed_servers:
                continue
            event = self.pending_ready_events[server]
            self._emit(
                server=server,
                status="ready",
                stream=event["stream"],
                line=event["line"],
                tool=event["tool"],
            )
        self.pending_ready_events.clear()

    def _emit_unattributed_failure(self, *, stream: str, line: str) -> None:
        fields: dict[str, Any] = {
            "agent": self.agent_name,
            "raw_line": line[:500],
        }
        if self.task_id:
            fields["task_id"] = self.task_id
        if stream:
            fields["stream"] = stream
        self.event_sink("mcp_runtime_unattributed_failure", **fields)

    def _emit(
        self,
        *,
        server: str,
        status: str,
        stream: str | None,
        line: str,
        tool: str | None = None,
    ) -> None:
        fields: dict[str, Any] = {
            "agent": self.agent_name,
            "server": server,
            "status": status,
            "elapsed_s": round(time.monotonic() - self.start_time, 3),
            "line": line.strip()[:500],
        }
        if self.task_id:
            fields["task_id"] = self.task_id
        if stream:
            fields["stream"] = stream
        if tool:
            fields["tool"] = tool
        self.event_sink("mcp_runtime_init", **fields)


def _normalize_gemini_tool_auth_mode(raw: Any) -> str:
    """Mirror Gemini adapter auth-mode normalization for tool_config overrides."""
    value = str(raw or "auto").strip().lower()
    if value == "api-key":
        return "api"
    if value == "oauth":
        return "subscription"
    if value in {"auto", "subscription", "api"}:
        return value
    return "auto"


def _resolve_gemini_ladder_auth_modes(tool_config: dict | None) -> tuple[str, ...]:
    """Resolve which Gemini auth rungs are allowed for this runtime call."""
    env = dict(os.environ)
    if tool_config and "auth_mode" in tool_config:
        env["GEMINI_AUTH_MODE"] = _normalize_gemini_tool_auth_mode(tool_config.get("auth_mode"))
    return resolve_allowed_auth_modes(env)


def _gemini_per_rung_timeout(prompt: str, hard_timeout: int) -> int:
    """Return the per-rung budget for the Gemini fallback ladder.

    Honors the caller's ``hard_timeout`` without additional ceilings.

    Pre-2026-04-24: the rung budget was
    ``min(hard_timeout, 300 + len(prompt)//500, 900)``. The 900s cap
    silently overrode the caller's ``hard_timeout``, so even after
    production LLM-dispatch timeouts were unified to 24h in
    ``scripts/batch/batch_gemini_config.py``, production Gemini calls
    were still being killed at 15 min. Codex caught this in the
    2026-04-24 architecture discussion (bridge thread 0f94b8c0):
    "the 24h watchdog direction is right, but the tree still contains
    10-15 minute production kill paths."

    The prompt-size heuristic is gone too. Its original purpose was
    "don't wait too long on rung 1 before falling over to rung 2,"
    but rungs fall over on ERRORS (rate limit, auth, model-unavailable)
    which surface fast, NOT on successful-but-slow work. Capping slow-
    but-productive work was the same anti-pattern as the phase-level
    short timeouts this discussion already removed. See the file-level
    header comment in batch_gemini_config.py for the full design story.

    ``prompt`` is retained in the signature for backward compatibility
    with callers that pass it but is no longer read.
    """
    _ = prompt
    return max(1, hard_timeout)


def _build_gemini_attempt_tool_config(
    tool_config: dict | None,
    rung: GeminiRung,
) -> dict:
    """Clone tool_config and pin the current ladder rung's auth mode."""
    if rung.auth_mode is None:
        return dict(tool_config or {})
    attempt_tool_config = dict(tool_config or {})
    attempt_tool_config["auth_mode"] = "subscription" if rung.auth_mode == "oauth" else "api"
    return attempt_tool_config


def _execute_invocation_plan(
    *,
    agent_name: str,
    adapter: AgentAdapter,
    plan: Any,
    prompt: str,
    mode: str,
    cwd: Path,
    model: str,
    task_id: str | None,
    session_id: str | None,
    entrypoint: str,
    hard_timeout: int,
    stall_timeout: int,
    tool_config: dict | None = None,
    event_sink: Callable[..., None] | None = None,
    stdout_silence_timeout: int | None = None,
    initial_response_timeout: int | None = None,
) -> _ExecutionOutcome:
    """Spawn one plan, run watchdog/parse flow, and return raw execution state."""
    # Exact-target review isolation (#5285): when tool_config requests
    # review_isolation, replace ambient agent env + wrap argv with the
    # fail-closed OS sandbox policy. Never silently weaken.
    review_cmd = list(plan.cmd)
    # InvocationPlan.cwd is the authoritative spawn location. Trail isolation
    # uses this to isolate native Grok from ambient project MCP configuration.
    review_cwd = Path(getattr(plan, "cwd", None) or cwd)
    isolation_evidence: dict | None = None
    isolation_capability_digest: str | None = None
    isolation_prompt_digest: str | None = None
    isolation_prompt_transport: str | None = None
    if tool_config and tool_config.get("review_isolation"):
        try:
            from scripts.review.isolation import (
                ReviewIsolationError,
                apply_review_isolation_to_invocation,
            )
        except ImportError:  # pragma: no cover - package path
            from review.isolation import (  # type: ignore
                ReviewIsolationError,
                apply_review_isolation_to_invocation,
            )
        try:
            prompt_transport = "stdin" if plan.stdin_payload else "prompt-file"
            (
                review_cmd,
                env,
                review_cwd,
                isolation_evidence,
                isolation_capability_digest,
                isolation_prompt_digest,
                isolation_prompt_transport,
            ) = apply_review_isolation_to_invocation(
                engine=agent_name,
                cmd=plan.cmd,
                cwd=plan.cwd if getattr(plan, "cwd", None) else cwd,
                tool_config=tool_config,
                env_overrides=plan.env_overrides,
                prompt_payload=plan.stdin_payload or prompt,
                prompt_transport=prompt_transport,
            )
        except ReviewIsolationError as exc:
            raise AgentUnavailableError(f"review isolation refused for {agent_name!r}: {exc}") from exc
        for key in plan.env_unsets:
            env.pop(key, None)
        env["AGENT_NO_TELEMETRY_FOOTER"] = "1"
        # Merge guard shims are host paths outside the sandbox allowlist and
        # are not needed for evidence-only review (no gh merge). Skip them.
    else:
        env = build_agent_env(provider=agent_name, overrides=plan.env_overrides)
        for key in plan.env_unsets:
            env.pop(key, None)
        env["AGENT_NO_TELEMETRY_FOOTER"] = "1"
        env = _apply_merge_guard(mode=mode, env=env)

    start_time = time.monotonic()
    proc: subprocess.Popen | None = None
    watchdog_state: WatchdogState | None = None
    watchdog_threads: list = []
    liveness_paths: tuple[Path, ...] = ()
    stdout_master_fd: int | None = None
    stderr_master_fd: int | None = None
    stdin_handle: Any = subprocess.DEVNULL
    stdin_temp_path: Path | None = None
    output_limit = _streamed_output_limit(agent_name=agent_name, entrypoint=entrypoint)
    observed_output_stdout_lines = 0
    streamed_output_bytes = 0
    fleet_capture: FleetCapture | None = None
    kill_reason: str | None = None

    try:
        try:
            if plan.stdin_payload:
                if tool_config and tool_config.get("review_isolation"):
                    write_root = Path(str(tool_config["review_write_root"]))
                    stdin_handle, stdin_temp_path = _prepare_stdin_handle(
                        plan.stdin_payload,
                        directory=write_root / "tmp",
                        unlink_after_open=True,
                    )
                else:
                    stdin_handle, stdin_temp_path = _prepare_stdin_handle(plan.stdin_payload)
            proc, stdout_master_fd, stderr_master_fd = _spawn_subprocess(
                review_cmd,
                cwd=review_cwd,
                env=env,
                stdin=stdin_handle,
                # PTYs make stdout line-buffered, but macOS can discard bytes
                # still waiting on a PTY master when an instantly failing
                # child closes its slave. Keep stderr on a pipe so CLI errors
                # survive every nonzero exit for task-state/log reporting.
                stderr_pipe=True,
            )
        except (FileNotFoundError, PermissionError, OSError) as exc:
            record = _build_usage_record(
                agent=agent_name,
                entrypoint=entrypoint,
                model=model,
                mode=mode,
                task_id=task_id,
                cwd=cwd,
                session_id=session_id,
                duration_s=time.monotonic() - start_time,
                input_chars=len(prompt),
                output_chars=0,
                returncode=None,
                outcome="error",
                rate_limited=False,
                stalled=False,
                stderr_excerpt=(f"Popen failed: {type(exc).__name__}: {exc}")[:500],
                tokens=None,  # TODO(#3153 PR2): extract tokens for this result path.
                failure_code="provider_unavailable",
            )
            write_record(record)
            raise AgentUnavailableError(f"{agent_name!r} Popen failed: {type(exc).__name__}: {exc}") from exc

        liveness_paths = tuple(adapter.liveness_signal_paths(plan))
        if plan.output_file is not None and plan.output_file not in liveness_paths:
            liveness_paths = (*liveness_paths, plan.output_file)
        watchdog_state, watchdog_threads = start_watchdog(
            proc,
            list(liveness_paths),
            stdout_master_fd=stdout_master_fd,
            stderr_master_fd=stderr_master_fd,
            track_process_activity=bool(stdout_silence_timeout is not None and stdout_silence_timeout > 0),
        )
        capture_repo_raw = None
        if tool_config:
            capture_repo_raw = (
                tool_config.get("repo_read_root")
                or tool_config.get("review_snapshot_root")
            )
        capture_repo = Path(
            str(capture_repo_raw or getattr(plan, "cwd", None) or cwd)
        )
        try:
            fleet_capture = FleetCapture.start(
                host_harness=getattr(plan, "host_harness", None),
                runner_agent=agent_name,
                entrypoint=entrypoint,
                requested_model=model,
                prompt=prompt,
                repo_path=capture_repo,
                runtime_repo_root=_RUNNER_REPO_TREE,
                plan_metadata=getattr(plan, "metadata", None),
            )
        except Exception as exc:
            # Entire is optional: capture setup can never alter the provider call.
            _logger.warning(
                "Entire fleet capture start failed for %s: %s",
                agent_name,
                type(exc).__name__,
            )
            fleet_capture = None
        mcp_observer = _McpRuntimeObserver.from_tool_config(
            agent_name=agent_name,
            task_id=task_id,
            tool_config=tool_config,
            event_sink=event_sink,
            start_time=start_time,
        )
        observed_stdout_lines = 0
        observed_stderr_lines = 0

        early_reap_check = getattr(adapter, "check_early_reap", None)
        returncode: int | None = None
        while True:
            if output_limit is not None:
                new_stdout_lines = watchdog_state.stdout_lines[observed_output_stdout_lines:]
                observed_output_stdout_lines = len(watchdog_state.stdout_lines)
                streamed_output_bytes += sum(
                    len(line.encode("utf-8", errors="replace"))
                    for line in new_stdout_lines
                )
            if mcp_observer is not None:
                observed_stdout_lines = mcp_observer.observe_lines(
                    watchdog_state.stdout_lines,
                    start_index=observed_stdout_lines,
                    stream="stdout",
                )
                observed_stderr_lines = mcp_observer.observe_lines(
                    watchdog_state.stderr_lines,
                    start_index=observed_stderr_lines,
                    stream="stderr",
                )
                mcp_observer.maybe_emit_timeout(time.monotonic())

            returncode = proc.poll()
            if returncode is not None:
                break

            if output_limit is not None and streamed_output_bytes > output_limit:
                kill_reason = "output_limit"
                _kill_process_tree(proc)
                break

            if early_reap_check is not None:
                try:
                    if early_reap_check(plan, call_start_time=start_time):
                        returncode = proc.poll()
                        if returncode is not None:
                            kill_reason = None
                            break
                        kill_reason = "early_reap"
                        _kill_process_tree(proc)
                        break
                except Exception:
                    pass

            kill_reason = should_kill(
                watchdog_state,
                stall_timeout,
                hard_timeout,
                stdout_silence_timeout=stdout_silence_timeout,
                initial_response_timeout=initial_response_timeout,
            )
            if kill_reason is not None:
                returncode = proc.poll()
                if returncode is not None:
                    kill_reason = None
                    break
                _kill_process_tree(proc)
                break
            time.sleep(_POLL_INTERVAL_S)

        duration_s = time.monotonic() - start_time
        assert watchdog_state is not None

        # ``poll()`` is the authoritative completion observation.  Most
        # CPython Popen objects also copy that value to ``.returncode``, but
        # wrappers/adapters can expose the result first.  Do not discard a
        # known terminal exit code while handing it to delegate state (#4837).
        final_returncode = proc.returncode if proc.returncode is not None else returncode
        if final_returncode is None:
            try:
                final_returncode = proc.wait(timeout=10.0)
            except subprocess.TimeoutExpired:
                _kill_process_tree(proc)
                final_returncode = proc.returncode

        for thread in watchdog_threads:
            if "stdout" in thread.name or "stderr" in thread.name:
                thread.join(timeout=5.0)

        if mcp_observer is not None:
            observed_stdout_lines = mcp_observer.observe_lines(
                watchdog_state.stdout_lines,
                start_index=observed_stdout_lines,
                stream="stdout",
            )
            observed_stderr_lines = mcp_observer.observe_lines(
                watchdog_state.stderr_lines,
                start_index=observed_stderr_lines,
                stream="stderr",
            )
            mcp_observer.maybe_emit_timeout(time.monotonic())
            mcp_observer.finalize()

        stdout_text = "".join(watchdog_state.stdout_lines)
        stderr_text = "".join(watchdog_state.stderr_lines)

        stop_watchdog(
            watchdog_state,
            watchdog_threads,
            proc=proc,
            stdout_master_fd=stdout_master_fd,
            stderr_master_fd=stderr_master_fd,
        )
        # stop_watchdog closed the master fds; null out our locals so
        # the finally clause doesn't try to close them again.
        stdout_master_fd = None
        stderr_master_fd = None
        parse = adapter.parse_response(
            stdout=stdout_text,
            stderr=stderr_text,
            returncode=final_returncode if final_returncode is not None else -1,
            output_file=plan.output_file,
            plan=plan,
            call_start_time=start_time,
        )
        if (
            not parse.ok
            and final_returncode not in (None, 0)
            and not parse.response
            and not (parse.stderr_excerpt or "").strip()
            and not stdout_text.strip()
            and not stderr_text.strip()
        ):
            parse = ParseResult(
                ok=False,
                response="",
                stderr_excerpt=(
                    f"{agent_name} subprocess exited rc={final_returncode} in "
                    f"{duration_s:.2f}s with no captured stdout/stderr "
                    f"(stdin_bytes={len(plan.stdin_payload or '')})"
                )[:500],
                rate_limited=parse.rate_limited,
                session_id=parse.session_id,
                tokens=parse.tokens,
                tool_calls=parse.tool_calls,
                substitution=parse.substitution,
            )
        if fleet_capture is not None:
            actual_model, route_metadata = resolved_route(
                requested_model=model,
                plan_metadata=getattr(plan, "metadata", None),
                substitution=parse.substitution,
            )
            fleet_capture.finish(
                response=parse.response,
                outcome=kill_reason or ("ok" if parse.ok else "error"),
                returncode=final_returncode,
                actual_model=actual_model,
                route_metadata=route_metadata,
            )
            fleet_capture = None
        return _ExecutionOutcome(
            parse=parse,
            duration_s=duration_s,
            returncode=final_returncode,
            kill_reason=kill_reason,
            stdout_text=stdout_text,
            stderr_text=stderr_text,
            liveness_paths=liveness_paths,
            isolation_evidence=isolation_evidence,
            isolation_capability_digest=isolation_capability_digest,
            isolation_prompt_digest=isolation_prompt_digest,
            isolation_prompt_transport=isolation_prompt_transport,
        )
    finally:
        if proc is not None and proc.poll() is None:
            with contextlib.suppress(Exception):
                _kill_process_tree(proc)

        if fleet_capture is not None:
            actual_model, route_metadata = resolved_route(
                requested_model=model,
                plan_metadata=getattr(plan, "metadata", None),
                substitution=None,
            )
            fleet_capture.finish(
                response="",
                outcome=kill_reason or "runner_exception",
                returncode=None if proc is None else proc.returncode,
                actual_model=actual_model,
                route_metadata=route_metadata,
            )
            fleet_capture = None

        if watchdog_state is not None:
            stop_watchdog(
                watchdog_state,
                watchdog_threads,
                proc=proc,
                stdout_master_fd=stdout_master_fd,
                stderr_master_fd=stderr_master_fd,
            )

        if plan.output_file is not None and plan.output_file.exists() and _is_temp_file(plan.output_file):
            should_delete = False
            try:
                file_size = plan.output_file.stat().st_size
            except OSError:
                file_size = -1

            if (
                file_size == 0
                or (proc is not None and proc.returncode == 0)
                or (proc is not None and proc.returncode is not None and proc.returncode < 0)
            ):
                should_delete = True

            if should_delete:
                with contextlib.suppress(OSError):
                    plan.output_file.unlink()

        cleanup_invocation = getattr(adapter, "cleanup_invocation", None)
        if cleanup_invocation is not None:
            with contextlib.suppress(Exception):
                cleanup_invocation(plan)

        _cleanup_stdin_temp(stdin_temp_path, stdin_handle)


def _raise_for_kill_reason(
    *,
    agent_name: str,
    kill_reason: str | None,
    execution: _ExecutionOutcome,
    prompt: str,
    entrypoint: str,
    model: str,
    mode: str,
    task_id: str | None,
    cwd: Path,
    session_id: str | None,
    stdout_silence_timeout: int | None,
    initial_response_timeout: int | None,
    stall_timeout: int,
    hard_timeout: int,
    event_sink: Callable[..., None] | None = None,
    substitution: dict[str, Any] | None = None,
) -> None:
    """Map watchdog kill reasons to typed runtime errors + usage records."""
    if not kill_reason:
        return
    parse = execution.parse
    record_substitution = substitution if substitution is not None else parse.substitution
    if kill_reason == "hard_timeout" and parse.ok:
        return
    if kill_reason == "output_limit":
        limit_bytes = _streamed_output_limit(agent_name=agent_name, entrypoint=entrypoint) or 0
        observed_bytes = len(execution.stdout_text.encode("utf-8", errors="replace"))
        record = _build_usage_record(
            agent=agent_name,
            entrypoint=entrypoint,
            model=model,
            mode=mode,
            task_id=task_id,
            cwd=cwd,
            session_id=session_id,
            duration_s=execution.duration_s,
            input_chars=len(prompt),
            output_chars=len(execution.stdout_text),
            returncode=execution.returncode,
            outcome="error",
            rate_limited=False,
            stalled=False,
            stderr_excerpt=(
                f"streamed_output_limit exceeded: limit={limit_bytes} "
                f"observed={observed_bytes}"
            ),
            tokens=None,
            substitution=record_substitution,
            failure_code="protocol_output_limit",
        )
        write_record(record)
        raise AgentOutputLimitError(agent_name, limit_bytes, observed_bytes)
    if kill_reason == "stdout_silence_timeout":
        record = _build_usage_record(
            agent=agent_name,
            entrypoint=entrypoint,
            model=model,
            mode=mode,
            task_id=task_id,
            cwd=cwd,
            session_id=session_id,
            duration_s=execution.duration_s,
            input_chars=len(prompt),
            output_chars=len(execution.stdout_text),
            returncode=execution.returncode,
            outcome="stalled",
            rate_limited=False,
            stalled=True,
            stderr_excerpt=parse.stderr_excerpt or execution.stderr_text[:500],
            tokens=None,  # TODO(#3153 PR2): extract tokens for this result path.
            substitution=record_substitution,
            failure_code="timeout",
        )
        _emit_substitution_event(
            agent_name=agent_name,
            entrypoint=entrypoint,
            task_id=task_id,
            cwd=cwd,
            model=model,
            substitution=record_substitution,
            event_sink=event_sink,
        )
        write_record(record)
        raise AgentStalledError(
            agent_name,
            stdout_silence_timeout or stall_timeout,
            execution.duration_s,
            kind="stdout_silence_timeout",
            substitution=record_substitution,
        )

    if kill_reason == "initial_response_timeout":
        record = _build_usage_record(
            agent=agent_name,
            entrypoint=entrypoint,
            model=model,
            mode=mode,
            task_id=task_id,
            cwd=cwd,
            session_id=session_id,
            duration_s=execution.duration_s,
            input_chars=len(prompt),
            output_chars=len(execution.stdout_text),
            returncode=execution.returncode,
            outcome="stalled",
            rate_limited=False,
            stalled=True,
            stderr_excerpt=(
                parse.stderr_excerpt
                or execution.stderr_text[:500]
                or (
                    f"initial_response_timeout: {agent_name} produced no "
                    f"stdout/stderr/liveness activity within "
                    f"{initial_response_timeout}s"
                )
            ),
            tokens=None,  # TODO(#3153 PR2): extract tokens for this result path.
            substitution=record_substitution,
            failure_code="timeout",
        )
        _emit_substitution_event(
            agent_name=agent_name,
            entrypoint=entrypoint,
            task_id=task_id,
            cwd=cwd,
            model=model,
            substitution=record_substitution,
            event_sink=event_sink,
        )
        write_record(record)
        raise AgentStalledError(
            agent_name,
            initial_response_timeout or stall_timeout,
            execution.duration_s,
            kind="initial_response_timeout",
            substitution=record_substitution,
        )

    if kill_reason == "hard_timeout" and not parse.ok:
        record = _build_usage_record(
            agent=agent_name,
            entrypoint=entrypoint,
            model=model,
            mode=mode,
            task_id=task_id,
            cwd=cwd,
            session_id=session_id,
            duration_s=execution.duration_s,
            input_chars=len(prompt),
            output_chars=len(execution.stdout_text),
            returncode=execution.returncode,
            outcome="hard_timeout",
            rate_limited=False,
            stalled=False,
            stderr_excerpt=(
                parse.stderr_excerpt
                or execution.stderr_text[:500]
                or tail_liveness_file_for_debug(execution.liveness_paths)[:500]
            ),
            tokens=None,  # TODO(#3153 PR2): extract tokens for this result path.
            substitution=record_substitution,
            failure_code="timeout",
        )
        _emit_substitution_event(
            agent_name=agent_name,
            entrypoint=entrypoint,
            task_id=task_id,
            cwd=cwd,
            model=model,
            substitution=record_substitution,
            event_sink=event_sink,
        )
        write_record(record)
        raise AgentTimeoutError(
            agent_name,
            hard_timeout,
            substitution=record_substitution,
        )


def _invoke_gemini_with_fallback(
    *,
    agent_name: str,
    adapter: AgentAdapter,
    prompt: str,
    mode: str,
    cwd: Path,
    model: str,
    task_id: str | None,
    session_id: str | None,
    tool_config: dict | None,
    entrypoint: str,
    hard_timeout: int,
    stall_timeout: int,
    stdout_silence_timeout: int | None = None,
    initial_response_timeout: int | None = None,
    effort: str | None = None,
) -> Result:
    """Run Gemini through the shared model/auth fallback ladder."""
    last_telemetry: InvocationTelemetry | None = None
    last_tool_calls: list[dict[str, Any]] = []

    def _attempt_runner(
        rung: GeminiRung,
        _attempt_index: int,
        timeout_s: int | None,
    ) -> AttemptOutcome:
        nonlocal last_telemetry
        nonlocal last_tool_calls
        try:
            if rung.cli == "agy-cli":
                headroom_ok, headroom_reason = has_headroom("agy", rung.model)
                if not headroom_ok:
                    return AttemptOutcome(
                        status="rate_limited",
                        elapsed_s=0.0,
                        stderr_excerpt=headroom_reason,
                    )
                attempt_agent_name = "agy"
                attempt_adapter = _load_adapter("agy")
                attempt_tool_config = _build_gemini_attempt_tool_config(tool_config, rung)
                attempt_session_id = None
            else:
                attempt_agent_name = agent_name
                attempt_adapter = adapter
                attempt_tool_config = _build_gemini_attempt_tool_config(tool_config, rung)
                attempt_session_id = session_id

            plan = attempt_adapter.build_invocation(
                prompt=prompt,
                mode=mode,
                cwd=cwd,
                model=rung.model,
                task_id=task_id,
                session_id=attempt_session_id,
                tool_config=attempt_tool_config,
                effort=effort,
            )
            last_telemetry = _resolve_plan_telemetry(
                agent_name=attempt_agent_name,
                plan=plan,
                requested_model=rung.model,
                requested_effort=effort,
                tool_config=attempt_tool_config,
            )
            execution = _execute_invocation_plan(
                agent_name=attempt_agent_name,
                adapter=attempt_adapter,
                plan=plan,
                prompt=prompt,
                mode=mode,
                cwd=cwd,
                model=rung.model,
                task_id=task_id,
                session_id=attempt_session_id,
                entrypoint=entrypoint,
                hard_timeout=timeout_s or hard_timeout,
                stall_timeout=stall_timeout,
                tool_config=attempt_tool_config,
                stdout_silence_timeout=stdout_silence_timeout,
                initial_response_timeout=initial_response_timeout,
            )
        except AgentUnavailableError as exc:
            if rung.cli == "agy-cli":
                return AttemptOutcome(
                    status="retryable_error",
                    elapsed_s=0.0,
                    stderr_excerpt=str(exc),
                )
            raise
        parse = execution.parse
        last_tool_calls = list(parse.tool_calls)

        if execution.kill_reason in ("stdout_silence_timeout", "initial_response_timeout"):
            _raise_for_kill_reason(
                agent_name=attempt_agent_name,
                kill_reason=execution.kill_reason,
                execution=execution,
                prompt=prompt,
                entrypoint=entrypoint,
                model=last_telemetry.model if last_telemetry is not None else rung.model,
                mode=mode,
                task_id=task_id,
                cwd=cwd,
                session_id=attempt_session_id,
                stdout_silence_timeout=stdout_silence_timeout,
                initial_response_timeout=initial_response_timeout,
                stall_timeout=stall_timeout,
                hard_timeout=hard_timeout,
            )

        if execution.kill_reason == "hard_timeout" and not parse.ok:
            return AttemptOutcome(
                status="timeout",
                elapsed_s=execution.duration_s,
                stderr_excerpt=(
                    parse.stderr_excerpt
                    or execution.stderr_text[:500]
                    or tail_liveness_file_for_debug(execution.liveness_paths)[:500]
                ),
                returncode=execution.returncode,
            )

        if parse.rate_limited:
            return AttemptOutcome(
                status="rate_limited",
                elapsed_s=execution.duration_s,
                stderr_excerpt=parse.stderr_excerpt,
                returncode=execution.returncode,
            )

        if parse.ok:
            return AttemptOutcome(
                status="success",
                elapsed_s=execution.duration_s,
                response_text=parse.response,
                stderr_excerpt=parse.stderr_excerpt,
                returncode=execution.returncode,
                note=parse.stderr_excerpt,
            )

        return AttemptOutcome(
            status="retryable_error",
            elapsed_s=execution.duration_s,
            stderr_excerpt=parse.stderr_excerpt or execution.stderr_text[:500],
            returncode=execution.returncode,
        )

    call_result: CallResult = run_gemini_fallback_ladder(
        task_name=task_id or f"{agent_name}-runtime",
        preferred_model=model,
        per_rung_timeout_s=_gemini_per_rung_timeout(prompt, hard_timeout),
        overall_timeout_s=hard_timeout,
        attempt_runner=_attempt_runner,
        logger=lambda _msg: None,
        allowed_auth_modes=_resolve_gemini_ladder_auth_modes(tool_config),
    )

    last_attempt_record = call_result.attempts[-1] if call_result.attempts else None
    # Failure-path usage records should attribute the last rung we actually ran,
    # not the caller's preferred model.
    record_model = (
        (last_telemetry.model if last_telemetry is not None else None)
        or call_result.model_used
        or (last_attempt_record.model if last_attempt_record and last_attempt_record.model else model)
    )
    record_effort = last_telemetry.effort if last_telemetry is not None else "unknown"
    record_cli_version = last_telemetry.cli_version if last_telemetry is not None else "unknown"
    stderr_excerpt = (
        (last_attempt_record.note if last_attempt_record and last_attempt_record.note else None)
        or (last_attempt_record.stderr_excerpt if last_attempt_record else None)
        or call_result.error_message
    )
    returncode = last_attempt_record.returncode if last_attempt_record else None

    if call_result.ok:
        response_text = call_result.response_text or ""
        record = _build_usage_record(
            agent=agent_name,
            entrypoint=entrypoint,
            model=record_model,
            mode=mode,
            task_id=task_id,
            cwd=cwd,
            session_id=session_id,
            duration_s=call_result.elapsed_s,
            input_chars=len(prompt),
            output_chars=len(response_text),
            returncode=returncode,
            outcome="ok",
            rate_limited=False,
            stalled=False,
            stderr_excerpt=stderr_excerpt,
            tokens=None,  # TODO(#3153 PR2): extract tokens for this result path.
        )
        write_record(record)
        return Result(
            ok=True,
            agent=agent_name,
            model=record_model,
            mode=mode,
            effort=record_effort,
            cli_version=record_cli_version,
            response=response_text,
            response_envelope=None,
            stderr_excerpt=stderr_excerpt,
            duration_s=call_result.elapsed_s,
            session_id=None,
            rate_limited=False,
            stalled=False,
            returncode=returncode,
            usage_record=record,
            tool_calls=last_tool_calls,
            tool_calls_total=len(last_tool_calls),
            isolation_evidence=None,
        )

    if call_result.attempts and all(attempt.status == "rate_limited" for attempt in call_result.attempts):
        record = _build_usage_record(
            agent=agent_name,
            entrypoint=entrypoint,
            model=record_model,
            mode=mode,
            task_id=task_id,
            cwd=cwd,
            session_id=session_id,
            duration_s=call_result.elapsed_s,
            input_chars=len(prompt),
            output_chars=0,
            returncode=returncode,
            outcome="rate_limited",
            rate_limited=True,
            stalled=False,
            stderr_excerpt=stderr_excerpt,
            tokens=None,  # TODO(#3153 PR2): extract tokens for this result path.
        )
        write_record(record)
        raise RateLimitedError(agent_name, record_model, reason=(stderr_excerpt or "")[:200])

    if (last_attempt_record is not None and last_attempt_record.status == "timeout") or "no budget left" in (
        call_result.error_message or ""
    ).lower():
        record = _build_usage_record(
            agent=agent_name,
            entrypoint=entrypoint,
            model=record_model,
            mode=mode,
            task_id=task_id,
            cwd=cwd,
            session_id=session_id,
            duration_s=call_result.elapsed_s,
            input_chars=len(prompt),
            output_chars=0,
            returncode=returncode,
            outcome="hard_timeout",
            rate_limited=False,
            stalled=False,
            stderr_excerpt=stderr_excerpt,
            tokens=None,  # TODO(#3153 PR2): extract tokens for this result path.
        )
        write_record(record)
        raise AgentTimeoutError(agent_name, hard_timeout)

    record = _build_usage_record(
        agent=agent_name,
        entrypoint=entrypoint,
        model=record_model,
        mode=mode,
        task_id=task_id,
        cwd=cwd,
        session_id=session_id,
        duration_s=call_result.elapsed_s,
        input_chars=len(prompt),
        output_chars=0,
        returncode=returncode,
        outcome="error",
        rate_limited=False,
        stalled=False,
        stderr_excerpt=stderr_excerpt,
        tokens=None,  # TODO(#3153 PR2): extract tokens for this result path.
    )
    write_record(record)
    return Result(
        ok=False,
        agent=agent_name,
        model=record_model,
        mode=mode,
        effort=record_effort,
        cli_version=record_cli_version,
        response="",
        response_envelope=None,
        stderr_excerpt=stderr_excerpt,
        duration_s=call_result.elapsed_s,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=returncode,
        usage_record=record,
        tool_calls=last_tool_calls,
        tool_calls_total=len(last_tool_calls),
        isolation_evidence=None,
    )


# ---------------------------------------------------------------------------
# Write-capable cwd isolation (#4446)
# ---------------------------------------------------------------------------
#
# Write-capable modes (``workspace-write`` / ``danger``) let the spawned CLI
# mutate files via apply_patch / Edit / Bash. Provider hooks (#4448) can miss
# those edit surfaces, so isolation must be correct *by construction*: this
# runner — the single chokepoint every orchestrated invocation funnels through —
# refuses to spawn a write-capable child in a *primary checkout that sits on a
# protected branch*, regardless of how the caller assembled ``cwd``. That is the
# real "never dirty main" hazard #4446 targets, and it aligns the runtime layer
# with the protected-branch scoping of the hook (#4448), monitor tripwire
# (#4449), and git shim (#4450). It backstops delegate's stricter CLI-arg
# preflight (#4445), which additionally requires a worktree for *every* delegate
# write dispatch irrespective of branch — this guard is the universal minimum,
# not a duplicate of that policy. Read-only invocations and worktrees (dispatch
# or otherwise) are always allowed; inspecting from the repo root is legitimate.

_WRITE_CAPABLE_MODES = frozenset({"workspace-write", "danger"})

_WRITE_CWD_HINT = (
    "Write-capable invocations must run inside a dispatch worktree "
    "(.worktrees/dispatch/<agent>/<task>/), never a primary checkout that is on "
    "a protected branch (main/master)."
)


def _load_worktree_containment():
    """Import the shared containment predicate (#4444).

    Mirrors the dual-candidate import in :func:`_load_adapter`: the ``scripts.*``
    name resolves when the repo root is on ``sys.path`` (``python -m ...`` /
    pytest), while the delegate worker and build entrypoints put only
    ``scripts/`` on the path, where the ``scripts.``-stripped name resolves.
    Returns ``None`` only if neither import succeeds (a broken deployment).
    """
    for candidate in (
        "scripts.guardrails.worktree_containment",
        "guardrails.worktree_containment",
    ):
        try:
            return importlib.import_module(candidate)
        except ImportError:
            continue
    return None


def _ensure_write_cwd_isolated(cwd: Path, *, mode: str, agent_name: str) -> None:
    """Refuse a write-capable spawn whose cwd is a protected primary checkout.

    Raises ``ValueError`` when ``cwd`` classifies as ``primary_checkout`` (#4444)
    *and* that checkout is on a protected branch, or when the containment
    predicate cannot be imported (fail closed — a write-capable spawn we cannot
    prove is isolated is exactly what this guard exists to prevent). Dispatch
    worktrees, any other registered worktree, out-of-repo paths, and primary
    checkouts deliberately on a feature branch all pass.
    """
    wc = _load_worktree_containment()
    if wc is None:
        raise ValueError(
            f"cannot verify worktree isolation for write-capable mode={mode!r} "
            f"(agent {agent_name!r}): the containment predicate "
            f"(scripts.guardrails.worktree_containment, #4444) failed to import. "
            f"Refusing to spawn. {_WRITE_CWD_HINT}"
        )
    resolved = wc.canonicalize(cwd)
    # Cheap containment gate: only a cwd inside this checkout's own file tree can
    # be its primary checkout root. Out-of-tree cwds (temp dirs, externally
    # located worktrees) are isolated from the primary checkout by definition, so
    # skip the git-plumbing classify — and its subprocess — entirely for them.
    if not resolved.is_relative_to(_RUNNER_REPO_TREE):
        return
    if wc.classify_repo_path(resolved, cwd=resolved) != "primary_checkout":
        return
    if not wc.is_protected_branch(resolved):
        return
    raise ValueError(
        f"cwd {str(cwd)!r} is the primary checkout on a protected branch; "
        f"write-capable mode={mode!r} for agent {agent_name!r} may not spawn "
        f"there. {_WRITE_CWD_HINT}"
    )


def _write_rate_limited_short_circuit(
    *,
    agent_name: str,
    entrypoint: str,
    model: str,
    mode: str,
    task_id: str | None,
    cwd: Path,
    session_id: str | None,
    prompt: str,
    reason: str,
) -> None:
    record = _build_usage_record(
        agent=agent_name,
        entrypoint=entrypoint,
        model=model,
        mode=mode,
        task_id=task_id,
        cwd=cwd,
        session_id=session_id,
        duration_s=0.0,
        input_chars=len(prompt),
        output_chars=0,
        returncode=None,
        outcome="rate_limited",
        rate_limited=True,
        stalled=False,
        stderr_excerpt=f"pre-call headroom check: {reason}",
        tokens=None,  # TODO(#3153 PR2): extract tokens for this result path.
    )
    write_record(record)


def _route_substitution_for_attempt(
    *,
    requested_route: FailoverRoute,
    actual_route: FailoverRoute,
    source_trigger: str,
    adapter_substitution: dict[str, Any] | None,
) -> dict[str, Any] | None:
    return substitution_for_route(
        requested_route=requested_route,
        actual_route=actual_route,
        source=f"agent-runtime-failover:{source_trigger}",
        adapter_substitution=adapter_substitution,
    )


def _invoke_with_runner_failover(
    *,
    agent_name: str,
    adapter: AgentAdapter,
    chain: FailoverChain,
    prompt: str,
    mode: str,
    cwd: Path,
    task_id: str | None,
    session_id: str | None,
    tool_config: dict | None,
    entrypoint: str,
    hard_timeout: int,
    stall_timeout: int,
    stdout_silence_timeout: int | None,
    initial_response_timeout: int | None,
    event_sink: Callable[..., None] | None,
    effort: str | None,
) -> Result:
    """Run one invocation through the configured runner-level failover chain."""
    store = FailoverCooldownStore()
    routes = ordered_available_routes(chain, store)
    requested_route = chain.routes[0]
    if not routes:
        reason = "all configured runner failover routes are cooling"
        _write_rate_limited_short_circuit(
            agent_name=agent_name,
            entrypoint=entrypoint,
            model=requested_route.model,
            mode=mode,
            task_id=task_id,
            cwd=cwd,
            session_id=session_id,
            prompt=prompt,
            reason=reason,
        )
        raise RateLimitedError(agent_name, requested_route.model, reason)

    overall_start = time.monotonic()
    last_trigger = "requested"
    last_headroom_failure: tuple[FailoverRoute, str] | None = None

    for attempt_index, route in enumerate(routes):
        headroom_ok, headroom_reason = has_headroom(agent_name, route.model)
        has_next_route = attempt_index < len(routes) - 1
        if not headroom_ok:
            store.mark_cooldown(
                route,
                agent_name=agent_name,
                trigger="rate_limited",
                ttl_s=chain.cooldown_ttl_s,
            )
            last_headroom_failure = (route, headroom_reason)
            last_trigger = "rate_limited"
            if has_next_route:
                continue
            _write_rate_limited_short_circuit(
                agent_name=agent_name,
                entrypoint=entrypoint,
                model=route.model,
                mode=mode,
                task_id=task_id,
                cwd=cwd,
                session_id=session_id,
                prompt=prompt,
                reason=headroom_reason,
            )
            raise RateLimitedError(agent_name, route.model, headroom_reason)

        attempt_tool_config = tool_config_with_route(tool_config, route)
        plan = adapter.build_invocation(
            prompt=prompt,
            mode=mode,
            cwd=cwd,
            model=route.model,
            task_id=task_id,
            session_id=session_id,
            tool_config=attempt_tool_config,
            effort=effort,
        )

        telemetry = _resolve_plan_telemetry(
            agent_name=agent_name,
            plan=plan,
            requested_model=route.model,
            requested_effort=effort,
            tool_config=attempt_tool_config,
        )

        execution = _execute_invocation_plan(
            agent_name=agent_name,
            adapter=adapter,
            plan=plan,
            prompt=prompt,
            mode=mode,
            cwd=cwd,
            model=route.model,
            task_id=task_id,
            session_id=session_id,
            entrypoint=entrypoint,
            hard_timeout=hard_timeout,
            stall_timeout=stall_timeout,
            tool_config=attempt_tool_config,
            event_sink=event_sink,
            stdout_silence_timeout=stdout_silence_timeout,
            initial_response_timeout=initial_response_timeout,
        )
        parse = execution.parse
        trigger = None
        if not parse.ok or execution.kill_reason:
            trigger = classify_failover_trigger(
                parse=parse,
                returncode=execution.returncode,
                kill_reason=execution.kill_reason,
                stdout_text=execution.stdout_text,
                stderr_text=execution.stderr_text,
            )

        if trigger:
            store.mark_cooldown(
                route,
                agent_name=agent_name,
                trigger=trigger,
                ttl_s=chain.cooldown_ttl_s,
            )
            last_trigger = trigger
            if has_next_route:
                continue

        if execution.kill_reason:
            source_trigger = trigger or last_trigger
            if route != requested_route and source_trigger == "requested":
                source_trigger = "cooldown"
            timeout_substitution = None
            if route != requested_route or parse.substitution:
                timeout_substitution = _route_substitution_for_attempt(
                    requested_route=requested_route,
                    actual_route=route,
                    source_trigger=source_trigger,
                    adapter_substitution=parse.substitution,
                )
                emit_runner_substitution_marker(
                    timeout_substitution,
                    logger=_logger,
                )
            _raise_for_kill_reason(
                agent_name=agent_name,
                kill_reason=execution.kill_reason,
                execution=execution,
                prompt=prompt,
                entrypoint=entrypoint,
                model=route.model,
                mode=mode,
                task_id=task_id,
                cwd=cwd,
                session_id=session_id,
                stdout_silence_timeout=stdout_silence_timeout,
                initial_response_timeout=initial_response_timeout,
                stall_timeout=stall_timeout,
                hard_timeout=hard_timeout,
                event_sink=event_sink,
                substitution=timeout_substitution,
            )

        if parse.rate_limited:
            outcome = "rate_limited"
        elif parse.ok:
            outcome = "ok"
        else:
            outcome = "error"

        source_trigger = last_trigger
        if route != requested_route and source_trigger == "requested":
            source_trigger = "cooldown"
        substitution = _route_substitution_for_attempt(
            requested_route=requested_route,
            actual_route=route,
            source_trigger=source_trigger,
            adapter_substitution=parse.substitution,
        )
        emit_runner_substitution_marker(substitution, logger=_logger)

        record_model = telemetry.model
        if isinstance(substitution, dict) and substitution.get("substituted") and substitution.get("actual_model"):
            record_model = str(substitution["actual_model"])[:200]

        _emit_substitution_event(
            agent_name=agent_name,
            entrypoint=entrypoint,
            task_id=task_id,
            cwd=cwd,
            model=record_model,
            substitution=substitution,
            event_sink=event_sink,
        )

        duration_s = time.monotonic() - overall_start
        record = _build_usage_record(
            agent=agent_name,
            entrypoint=entrypoint,
            model=record_model,
            mode=mode,
            task_id=task_id,
            cwd=cwd,
            session_id=session_id,
            duration_s=duration_s,
            input_chars=len(prompt),
            output_chars=len(parse.response),
            returncode=execution.returncode,
            outcome=outcome,
            rate_limited=parse.rate_limited,
            stalled=False,
            stderr_excerpt=parse.stderr_excerpt,
            tokens=parse.tokens,
            substitution=substitution,
            failure_code=parse.failure_code,
        )
        write_record(record)

        if parse.rate_limited:
            raise RateLimitedError(
                agent_name,
                record_model,
                reason=(parse.stderr_excerpt or "")[:200],
            )

        return Result(
            ok=parse.ok,
            agent=agent_name,
            model=record_model,
            mode=mode,
            effort=telemetry.effort,
            cli_version=telemetry.cli_version,
            response=parse.response,
            response_envelope=parse.response_envelope,
            stderr_excerpt=parse.stderr_excerpt,
            duration_s=duration_s,
            session_id=parse.session_id,
            rate_limited=parse.rate_limited,
            stalled=False,
            returncode=execution.returncode,
            usage_record=record,
            tool_calls=list(parse.tool_calls),
            tool_calls_total=getattr(parse, "tool_calls_total", len(parse.tool_calls)),
            substitution=substitution,
            isolation_evidence=execution.isolation_evidence,
            isolation_capability_digest=execution.isolation_capability_digest,
            isolation_prompt_digest=execution.isolation_prompt_digest,
            isolation_prompt_transport=execution.isolation_prompt_transport,
        )

    if last_headroom_failure is not None:
        route, reason = last_headroom_failure
        _write_rate_limited_short_circuit(
            agent_name=agent_name,
            entrypoint=entrypoint,
            model=route.model,
            mode=mode,
            task_id=task_id,
            cwd=cwd,
            session_id=session_id,
            prompt=prompt,
            reason=reason,
        )
        raise RateLimitedError(agent_name, route.model, reason)

    raise AgentUnavailableError(f"Agent {agent_name!r} has an empty runner failover route set")


def _invoke_impl(
    agent_name: str,
    prompt: str,
    *,
    mode: str = "read-only",
    cwd: Path | None = None,
    model: str | None = None,
    task_id: str | None = None,
    session_id: str | None = None,
    tool_config: dict | None = None,
    entrypoint: str = "runtime",
    hard_timeout: int = 86400,  # 24h — last-resort leak guard, NOT a
    # tuning knob for expected runtime. See
    # the header comment in
    # scripts/batch/batch_gemini_config.py
    # for the full design rationale.
    stall_timeout: int = 180,  # accepted but ignored; see docstring
    stdout_silence_timeout: int | None = None,
    initial_response_timeout: int | None = None,
    event_sink: Callable[..., None] | None = None,
    effort: str | None = None,
    allow_direct_only: bool = False,
    allow_runner_failover: bool = True,
) -> Result:
    """Runner implementation after any parent-owned isolation preparation.

    Args:
        agent_name: Registry key. Must be in AGENTS and have
            ``cli_available: True``.
        prompt: Prompt text to send to the agent. Adapters decide whether
            to pipe this via stdin or embed it in the command.
        mode: Sandbox mode. One of ``{"read-only", "workspace-write", "danger"}``.
            Must be in ``adapter.supported_modes``.
        cwd: Working directory for the subprocess. MANDATORY for write
            modes (``workspace-write``, ``danger``). Optional for
            ``read-only``. Runner validates this.
        model: Model override. If None, uses ``adapter.default_model``.
        task_id: Optional task identifier carried into the usage record
            and passed to the adapter for session tracking.
        session_id: Session to resume, if the caller's entrypoint and the
            adapter's ``resume_policy`` both allow it. See § 6.3.
        tool_config: Adapter-specific tool configuration dict. For Claude
            and Gemini this carries MCP server names and allowed-tools
            strings. Adapters ignore keys they don't understand.
        entrypoint: Who called us — drives resume policy enforcement and
            usage record labeling. One of: ``"bridge"``, ``"dispatch"``,
            ``"delegate"``, ``"consult"``, ``"runtime"``.
        hard_timeout: Absolute wall-clock max in seconds. Default 30 min.
            Triggers AgentTimeoutError on overflow.
        stall_timeout: Accepted for backward compatibility but NO LONGER
            USED as a kill condition. Removed from the kill path on
            2026-04-10 after repeated production incidents where
            successful long-running calls were killed as false-positive
            stalls. See watchdog.py::should_kill() docstring for the
            full incident chain. hard_timeout is the only safety net now.
        stdout_silence_timeout: Optional per-call composite silence watchdog in
            seconds. Disabled by default. Uses stdout/stderr, liveness-file
            updates, and process-tree CPU/disk activity.
        initial_response_timeout: Optional startup probe in seconds. When set,
            the runtime kills the subprocess if it produces no stdout/stderr
            or liveness-file activity within this window (#2071). Distinct
            from ``stdout_silence_timeout``, which watches composite activity
            after startup.
        event_sink: Optional ``event_sink(event_name, **fields)`` callback for
            dispatch JSONL observability events.
        effort: Cross-agent reasoning/effort level. First-class peer of
            ``model`` (NOT stuffed into ``tool_config``). Accepted values:
            ``"low" | "medium" | "high" | "xhigh" | "max"``. When ``None``,
            each adapter's CLI / config default applies (Claude CLI
            default; Codex's ``~/.codex/config.toml``; Gemini has no
            equivalent yet). See #1396.

    Returns:
        Result with ok, response, timing, session_id, and the full usage
        record that was written to disk.

    Raises:
        AgentUnavailableError: Unknown agent or adapter import failed.
        ValueError: Invalid mode, missing cwd for write mode, or resume
            policy violation.
        RateLimitedError: has_headroom() reports recent rate limit, OR
            adapter.parse_response() classified the failure as rate-limited.
        AgentTimeoutError: Wall-clock runtime exceeded hard_timeout.
    """
    # ---------- 1. Resolve adapter ----------
    _validate_agent_name(agent_name)
    adapter = (
        _load_adapter(agent_name, allow_direct_only=True)
        if allow_direct_only
        else _load_adapter(agent_name)
    )

    # ---------- 2. Validate mode ----------
    if mode not in adapter.supported_modes:
        raise ValueError(
            f"Agent {agent_name!r} does not support mode {mode!r}. Supported modes: {sorted(adapter.supported_modes)}"
        )

    # ---------- 3. Validate cwd for write modes ----------
    if mode in _WRITE_CAPABLE_MODES:
        if cwd is None:
            raise ValueError(
                f"cwd is mandatory for mode={mode!r}. Write-capable invocations "
                f"must pin their working directory to prevent cross-worktree "
                f"contamination."
            )
        # #4446: enforce worktree isolation by construction at the spawn
        # chokepoint — a write-capable child may never run in a protected
        # primary checkout, regardless of how the caller assembled cwd.
        _ensure_write_cwd_isolated(cwd, mode=mode, agent_name=agent_name)
    effective_cwd = cwd or Path.cwd()
    current_run_id()
    current_session_id()

    # ---------- 4. Resume policy ----------
    _enforce_resume_policy(agent_name, session_id, entrypoint)

    # ---------- 5. Pre-call rate-limit check ----------
    effective_model = model or adapter.default_model
    failover_chain = (
        load_failover_chain(agent_name, effective_model=effective_model)
        if allow_runner_failover
        else None
    )
    if allow_direct_only and failover_chain is not None:
        raise AgentUnavailableError(
            f"Direct-only agent {agent_name!r} may not use runner failover"
        )
    if failover_chain is not None:
        return _invoke_with_runner_failover(
            agent_name=agent_name,
            adapter=adapter,
            chain=failover_chain,
            prompt=prompt,
            mode=mode,
            cwd=effective_cwd,
            task_id=task_id,
            session_id=session_id,
            tool_config=tool_config,
            entrypoint=entrypoint,
            hard_timeout=hard_timeout,
            stall_timeout=stall_timeout,
            stdout_silence_timeout=stdout_silence_timeout,
            initial_response_timeout=initial_response_timeout,
            event_sink=event_sink,
            effort=effort,
        )

    ok, reason = has_headroom(agent_name, effective_model)
    if not ok:
        # Record the short-circuit for observability — the caller didn't
        # burn a quota slot, but we still want the usage log to show it.
        _write_rate_limited_short_circuit(
            agent_name=agent_name,
            entrypoint=entrypoint,
            model=effective_model,
            mode=mode,
            task_id=task_id,
            cwd=effective_cwd,
            session_id=session_id,
            prompt=prompt,
            reason=reason,
        )
        raise RateLimitedError(agent_name, effective_model, reason)

    if agent_name == "gemini":
        return _invoke_gemini_with_fallback(
            agent_name=agent_name,
            adapter=adapter,
            prompt=prompt,
            mode=mode,
            cwd=effective_cwd,
            model=effective_model,
            task_id=task_id,
            session_id=session_id,
            tool_config=tool_config,
            entrypoint=entrypoint,
            hard_timeout=hard_timeout,
            stall_timeout=stall_timeout,
            stdout_silence_timeout=stdout_silence_timeout,
            initial_response_timeout=initial_response_timeout,
            effort=effort,
        )

    # ---------- 6. Build invocation plan ----------
    # Direct-only transports may use an adapter-owned model default that is
    # intentionally a telemetry label rather than an argv override. Preserve
    # a caller's explicit ``None`` for those adapters while retaining the
    # effective label for headroom and usage records.
    plan_model = model if allow_direct_only else effective_model
    plan = adapter.build_invocation(
        prompt=prompt,
        mode=mode,
        cwd=effective_cwd,
        model=plan_model,
        task_id=task_id,
        session_id=session_id,
        tool_config=tool_config,
        effort=effort,
    )

    telemetry = _resolve_plan_telemetry(
        agent_name=agent_name,
        plan=plan,
        requested_model=effective_model,
        requested_effort=effort,
        tool_config=tool_config,
    )

    execution = _execute_invocation_plan(
        agent_name=agent_name,
        adapter=adapter,
        plan=plan,
        prompt=prompt,
        mode=mode,
        cwd=effective_cwd,
        model=effective_model,
        task_id=task_id,
        session_id=session_id,
        entrypoint=entrypoint,
        hard_timeout=hard_timeout,
        stall_timeout=stall_timeout,
        tool_config=tool_config,
        event_sink=event_sink,
        stdout_silence_timeout=stdout_silence_timeout,
        initial_response_timeout=initial_response_timeout,
    )
    parse = execution.parse

    if execution.kill_reason:
        _raise_for_kill_reason(
            agent_name=agent_name,
            kill_reason=execution.kill_reason,
            execution=execution,
            prompt=prompt,
            entrypoint=entrypoint,
            model=effective_model,
            mode=mode,
            task_id=task_id,
            cwd=effective_cwd,
            session_id=session_id,
            stdout_silence_timeout=stdout_silence_timeout,
            initial_response_timeout=initial_response_timeout,
            stall_timeout=stall_timeout,
            hard_timeout=hard_timeout,
            event_sink=event_sink,
        )

    if parse.rate_limited:
        outcome = "rate_limited"
    elif parse.ok:
        outcome = "ok"
    else:
        outcome = "error"

    substitution = parse.substitution
    record_model = telemetry.model
    # isinstance guard mirrors _safe_substitution_record: adapters (and test
    # mocks) may hand back arbitrary objects; only a real dict payload may
    # override resolved telemetry.
    if isinstance(substitution, dict) and substitution.get("substituted") and substitution.get("actual_model"):
        record_model = str(substitution["actual_model"])[:200]

    _emit_substitution_event(
        agent_name=agent_name,
        entrypoint=entrypoint,
        task_id=task_id,
        cwd=effective_cwd,
        model=record_model,
        substitution=substitution,
        event_sink=event_sink,
    )

    record = _build_usage_record(
        agent=agent_name,
        entrypoint=entrypoint,
        model=record_model,
        mode=mode,
        task_id=task_id,
        cwd=effective_cwd,
        session_id=session_id,
        duration_s=execution.duration_s,
        input_chars=len(prompt),
        output_chars=len(parse.response),
        returncode=execution.returncode,
        outcome=outcome,
        rate_limited=parse.rate_limited,
        stalled=False,
        stderr_excerpt=parse.stderr_excerpt,
        tokens=parse.tokens,
        substitution=substitution,
        failure_code=parse.failure_code,
    )
    write_record(record)

    if parse.rate_limited:
        raise RateLimitedError(
            agent_name,
            record_model,
            reason=(parse.stderr_excerpt or "")[:200],
        )

    return Result(
        ok=parse.ok,
        agent=agent_name,
        model=record_model,
        mode=mode,
        effort=telemetry.effort,
        cli_version=telemetry.cli_version,
        response=parse.response,
        response_envelope=parse.response_envelope,
        stderr_excerpt=parse.stderr_excerpt,
        duration_s=execution.duration_s,
        session_id=parse.session_id,
        rate_limited=parse.rate_limited,
        stalled=False,
        returncode=execution.returncode,
        usage_record=record,
        tool_calls=list(parse.tool_calls),
        tool_calls_total=getattr(parse, "tool_calls_total", len(parse.tool_calls)),
        substitution=substitution,
        isolation_evidence=execution.isolation_evidence,
        isolation_capability_digest=execution.isolation_capability_digest,
        isolation_prompt_digest=execution.isolation_prompt_digest,
        isolation_prompt_transport=execution.isolation_prompt_transport,
        transport_metadata=(
            _INTER_AGENT_TRANSPORT.get().metadata()
            if _INTER_AGENT_TRANSPORT.get() is not None
            else None
        ),
        transport_outcome=outcome if _INTER_AGENT_TRANSPORT.get() is not None else None,
    )


def invoke(
    agent_name: str,
    prompt: str,
    *,
    mode: str = "read-only",
    cwd: Path | None = None,
    model: str | None = None,
    task_id: str | None = None,
    session_id: str | None = None,
    tool_config: dict | None = None,
    entrypoint: str = "runtime",
    hard_timeout: int = 86400,
    stall_timeout: int = 180,
    stdout_silence_timeout: int | None = None,
    initial_response_timeout: int | None = None,
    event_sink: Callable[..., None] | None = None,
    effort: str | None = None,
    initiator: str | None = None,
) -> Result:
    """Invoke an agent CLI, provisioning trail isolation before any spawn.

    ``tool_config={"trail_isolation": ...}`` is handled before adapter
    planning. Unsupported adapters refuse before spawn, while supported
    profiles receive a private one-server MCP configuration that is removed
    after success, refusal, timeout, or adapter error.
    """
    attribution = resolve_invocation_attribution(
        explicit=initiator,
        task_id=task_id,
    )
    attribution_token = _INVOCATION_ATTRIBUTION.set(attribution)
    launch = None
    try:
        launch = prepare_trail_isolation(
            agent_name=agent_name,
            mode=mode,
            tool_config=tool_config,
        )
        return _invoke_impl(
            agent_name,
            prompt,
            mode=mode,
            cwd=cwd,
            model=model,
            task_id=task_id,
            session_id=session_id,
            tool_config=launch.tool_config if launch is not None else tool_config,
            entrypoint=entrypoint,
            hard_timeout=hard_timeout,
            stall_timeout=stall_timeout,
            stdout_silence_timeout=stdout_silence_timeout,
            initial_response_timeout=initial_response_timeout,
            event_sink=event_sink,
            effort=effort,
        )
    finally:
        if launch is not None:
            launch.cleanup()
        _INVOCATION_ATTRIBUTION.reset(attribution_token)


@dataclass(frozen=True)
class InterAgentRoute:
    """One enabled, fixed ACP participant selected by the runner."""

    participant: str
    seat: str
    target_agent: str
    model: str | None
    effort: str | None


def _require_acp_transport(transport: str | None) -> None:
    """Select ACP only; bridge fallback belongs outside this boundary."""
    selected = _INTER_AGENT_TRANSPORT_NAME if transport is None else str(transport).strip().lower()
    if selected != _INTER_AGENT_TRANSPORT_NAME:
        raise InterAgentTransportError(
            "inter-agent transport supports only 'acp'; it never retries the legacy bridge"
        )
    active = os.environ.get(ACPX_TRANSPORT_ENV, "off").strip().lower()
    if active != "active":
        raise InterAgentTransportError(
            f"ACP transport is unavailable ({ACPX_TRANSPORT_ENV}={active!r}); refusing before spawn"
        )


def _validate_transport_metadata(metadata: Mapping[str, object] | None) -> None:
    """Reject arbitrary metadata so credentials and provenance cannot cross this seam."""
    if metadata is None:
        return
    if not isinstance(metadata, Mapping):
        raise InterAgentTransportError("inter-agent metadata must be a mapping when provided")
    reserved = sorted(
        str(key)
        for key in metadata
        if str(key).strip().casefold() in _RESERVED_TRANSPORT_PROVENANCE
    )
    if reserved:
        raise InterAgentTransportError(
            "Source, Agent, and Via are runner-sealed ACP provenance; "
            f"caller metadata may not override {reserved!r}"
        )
    if metadata:
        raise InterAgentTransportError(
            "inter-agent transport accepts no arbitrary metadata; use its explicit bounded arguments"
        )


def _validate_catalog_model(
    *,
    participant: str,
    model: str,
) -> None:
    """Require a current active catalog model on the adapter's real route."""
    try:
        from scripts.review.model_catalog import load_model_catalog

        catalog = load_model_catalog()
    except (ImportError, OSError, ValueError) as exc:
        raise InterAgentTransportError(
            "ACP model selection is unavailable because the canonical model catalog could not load"
        ) from exc

    try:
        model_entry = catalog["models"][model]
        catalog_transport = ACPX_PARTICIPANT_CATALOG_TRANSPORTS[participant]
    except (KeyError, TypeError) as exc:
        raise InterAgentTransportError(
            f"ACP participant {participant!r} has no enabled catalog route for model {model!r}"
        ) from exc
    if model_entry.get("lifecycle") != "active":
        raise InterAgentTransportError(
            f"ACP participant {participant!r} refuses non-active model {model!r}"
        )
    if catalog_transport not in model_entry.get("transports", []):
        raise InterAgentTransportError(
            f"ACP participant {participant!r} does not implement catalog transport "
            f"{catalog_transport!r} for model {model!r}"
        )


def resolve_inter_agent_route(
    agent: str,
    *,
    model: str | None = None,
    effort: str | None = None,
) -> InterAgentRoute:
    """Validate one ACP participant/model/effort selection without spawning.

    The selection is deliberately narrower than ordinary runtime routing:
    only the pinned ACP adapter registry is considered, and an override may
    only repeat that adapter's current exact pin.  This prevents model catalog
    presence from inventing a new ACP provider route.
    """
    participant = str(agent).strip().lower()
    try:
        raw_route = ACPX_SUPPORTED_PARTICIPANTS[participant]
        seat = raw_route["seat"]
        target_agent = raw_route["agent"]
        pinned_model = raw_route["model"]
    except (KeyError, TypeError) as exc:
        raise InterAgentTransportError(
            f"ACP participant {participant!r} is unsupported; refusing without bridge fallback"
        ) from exc
    if not all(isinstance(value, str) and value for value in (seat, target_agent)):
        raise InterAgentTransportError(
            f"ACP participant {participant!r} has an invalid enabled adapter route"
        )
    try:
        entry = get_agent_entry(seat)
    except KeyError as exc:
        raise InterAgentTransportError(
            f"ACP participant {participant!r} has no registered direct-only seat"
        ) from exc
    if entry.get("direct_only") is not True or entry.get("cli_available") is not False:
        raise InterAgentTransportError(
            f"ACP participant {participant!r} is not an enabled confined direct-only route"
        )

    selected_model = pinned_model
    if pinned_model is None:
        if model is not None:
            _validate_catalog_model(participant=participant, model=model)
            selected_model = model
    elif model is not None and model != pinned_model:
        raise InterAgentTransportError(
            f"ACP participant {participant!r} only supports its registered model pin "
            f"{pinned_model!r}; got {model!r}"
        )
    else:
        _validate_catalog_model(participant=participant, model=pinned_model)

    pinned_effort = ACPX_PARTICIPANT_EFFORTS.get(participant)
    if effort is not None and effort != pinned_effort:
        raise InterAgentTransportError(
            f"ACP participant {participant!r} only supports its registered effort pin "
            f"{pinned_effort!r}; got {effort!r}"
        )
    return InterAgentRoute(
        participant=participant,
        seat=seat,
        target_agent=target_agent,
        model=selected_model,
        effort=pinned_effort,
    )


def _resolve_trusted_transport_source(
    *,
    source: str | None,
    task_id: str,
) -> str:
    """Resolve Source once and refuse unknown/missing provenance before spawn."""
    try:
        attribution = resolve_invocation_attribution(
            explicit=source,
            task_id=task_id,
        )
    except ValueError as exc:
        raise InterAgentTransportError("inter-agent Source is invalid") from exc
    if attribution.initiator == "unknown":
        raise InterAgentTransportError(
            "inter-agent ACP requires a trusted initiating Source; unknown or missing is refused"
        )
    return attribution.initiator


def _normalized_transport_outcome(result: Result) -> str:
    """Expose one bounded terminal vocabulary to communication callers."""
    if result.rate_limited:
        return "rate_limited"
    if result.ok:
        return "ok"
    reported = result.usage_record.get("outcome")
    return reported if reported in {"error", "rate_limited"} else "error"


def invoke_inter_agent(
    agent: str,
    prompt: str,
    *,
    cwd: Path,
    task_id: str,
    correlation_id: str,
    idempotency_key: str,
    source: str | None = None,
    model: str | None = None,
    effort: str | None = None,
    transport: str | None = None,
    metadata: Mapping[str, object] | None = None,
    sealed_review_mcp_config: Path | None = None,
    hard_timeout: int = 300,
) -> Result:
    """Invoke one confined ACP participant through the normal communication seam.

    ACP is the default and only transport exposed here.  It performs one
    direct-only one-shot call, never creates a worktree or provider session,
    and never retries a failed ACP request through the legacy bridge.  The
    returned :class:`Result` carries runner-sealed ``transport_metadata``
    (Source, Agent, Via) and a normalized ``transport_outcome``.
    """
    _require_acp_transport(transport)
    _validate_transport_metadata(metadata)
    if not isinstance(prompt, str) or not prompt.strip():
        raise InterAgentTransportError("inter-agent prompt must be a non-empty string")
    if isinstance(hard_timeout, bool) or not isinstance(hard_timeout, int) or hard_timeout < 1:
        raise InterAgentTransportError("inter-agent hard_timeout must be a positive integer")
    sealed_config = None
    if sealed_review_mcp_config is not None:
        sealed_config = str(Path(sealed_review_mcp_config))

    validated_task_id = _require_local_metadata_field(
        "task_id", task_id, adapter_label="InterAgentTransport"
    )
    validated_correlation_id = _require_local_metadata_field(
        "correlation_id", correlation_id, adapter_label="InterAgentTransport"
    )
    validated_idempotency_key = _require_local_metadata_field(
        "idempotency_key", idempotency_key, adapter_label="InterAgentTransport"
    )
    route = resolve_inter_agent_route(agent, model=model, effort=effort)
    trusted_source = _resolve_trusted_transport_source(
        source=source,
        task_id=validated_task_id,
    )
    provenance = AcpxTransportProvenance(
        source=trusted_source,
        agent=route.participant,
        target_agent=route.target_agent,
    )
    transport_token = _INTER_AGENT_TRANSPORT.set(provenance)
    try:
        with active_communication_scope(
            source=trusted_source,
            agent=route.participant,
            target_agent=route.target_agent,
        ):
            result = _invoke_direct_only(
                route.seat,
                prompt,
                cwd=Path(cwd),
                model=route.model,
                task_id=validated_task_id,
                tool_config={
                    "acpx_transport": True,
                    "target_agent": route.target_agent,
                    "correlation_id": validated_correlation_id,
                    "idempotency_key": validated_idempotency_key,
                    **(
                        {"sealed_review_mcp_config": sealed_config}
                        if sealed_config is not None
                        else {}
                    ),
                },
                hard_timeout=hard_timeout,
                effort=route.effort,
                entrypoint="acpx-transport",
                initiator=trusted_source,
            )
            usage_record = dict(result.usage_record)
            usage_record.setdefault("transport", provenance.metadata())
            return replace(
                result,
                usage_record=usage_record,
                transport_metadata=provenance.metadata(),
                transport_outcome=_normalized_transport_outcome(result),
            )
    finally:
        _INTER_AGENT_TRANSPORT.reset(transport_token)


def _invoke_direct_only(
    agent_name: str,
    prompt: str,
    *,
    cwd: Path,
    model: str | None = None,
    task_id: str,
    tool_config: dict,
    hard_timeout: int = 300,
    effort: str | None = None,
    entrypoint: str = "acpx-pilot-shadow",
    initiator: str | None = None,
) -> Result:
    """Invoke one explicitly marked direct-only, read-only shadow seat.

    This surface is deliberately narrower than :func:`invoke`: it cannot
    resume a session, select a write-capable mode, enter normal
    routing/failover/catalog selection, or choose its own entrypoint. The
    bounded ACPX comparison pilot is the only supported caller.
    """
    try:
        entry = get_agent_entry(agent_name)
    except KeyError:
        raise AgentUnavailableError(f"Agent {agent_name!r} is not in the registry") from None
    if entry.get("direct_only") is not True or entry["cli_available"]:
        raise AgentUnavailableError(
            f"Agent {agent_name!r} is not an unavailable direct-only seat"
        )
    if entrypoint not in {"acpx-pilot-shadow", "acpx-discuss", "acpx-transport"}:
        raise ValueError("ACPX direct-only invocation entrypoint was altered")
    attribution_token = _INVOCATION_ATTRIBUTION.set(
        resolve_invocation_attribution(explicit=initiator, task_id=task_id)
    )
    started_at = time.monotonic()
    try:
        return _invoke_impl(
            agent_name,
            prompt,
            mode="read-only",
            cwd=cwd,
            model=model,
            task_id=task_id,
            session_id=None,
            tool_config=tool_config,
            entrypoint=entrypoint,
            hard_timeout=hard_timeout,
            effort=effort,
            allow_direct_only=True,
            allow_runner_failover=False,
        )
    except AcpxShadowRefusalError as exc:
        write_record(
            _build_usage_record(
                agent=agent_name,
                entrypoint=entrypoint,
                model=model or "unknown",
                mode="read-only",
                task_id=task_id,
                cwd=cwd,
                session_id=None,
                duration_s=time.monotonic() - started_at,
                input_chars=len(prompt),
                output_chars=0,
                returncode=None,
                outcome="error",
                rate_limited=False,
                stalled=False,
                stderr_excerpt=None,
                tokens=None,
                failure_code=exc.failure_code,
            )
        )
        raise
    finally:
        _INVOCATION_ATTRIBUTION.reset(attribution_token)


def _invoke_native_once(
    agent_name: str,
    prompt: str,
    *,
    mode: str = "read-only",
    cwd: Path,
    model: str | None = None,
    task_id: str,
    session_id: str | None = None,
    entrypoint: str = "acpx-pilot-native",
    hard_timeout: int = 300,
    effort: str | None = None,
    initiator: str | None = None,
) -> Result:
    """Invoke one native ACPX-pilot authority call without runner failover."""
    if agent_name not in {"codex", "grok"}:
        raise AgentUnavailableError(
            f"Agent {agent_name!r} is not a supported ACPX pilot native seat"
        )
    permitted_entrypoints = {"acpx-pilot-native", "acpx-discuss-synthesis"}
    if (
        mode != "read-only"
        or session_id is not None
        or entrypoint not in permitted_entrypoints
        or (entrypoint == "acpx-discuss-synthesis" and agent_name != "codex")
    ):
        raise ValueError("ACPX pilot native invocation contract was altered")
    attribution_token = _INVOCATION_ATTRIBUTION.set(
        resolve_invocation_attribution(explicit=initiator, task_id=task_id)
    )
    try:
        return _invoke_impl(
            agent_name,
            prompt,
            mode=mode,
            cwd=cwd,
            model=model,
            task_id=task_id,
            session_id=None,
            tool_config=None,
            entrypoint=entrypoint,
            hard_timeout=hard_timeout,
            effort=effort,
            allow_runner_failover=False,
        )
    finally:
        _INVOCATION_ATTRIBUTION.reset(attribution_token)
