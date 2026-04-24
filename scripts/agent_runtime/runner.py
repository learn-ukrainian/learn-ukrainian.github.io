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
import importlib
import os
import shutil
import signal
import subprocess
import time
from dataclasses import dataclass
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

from .adapters.base import AgentAdapter
from .errors import (
    AgentTimeoutError,
    AgentUnavailableError,
    RateLimitedError,
)
from .registry import AGENTS, get_agent_entry
from .result import ParseResult, Result
from .telemetry import InvocationTelemetry, resolve_invocation_telemetry
from .usage import has_headroom, write_record
from .watchdog import (
    WatchdogState,
    should_kill,
    start_watchdog,
    stop_watchdog,
    tail_liveness_file_for_debug,
)

# Poll interval while waiting on subprocess + watchdog. 1s is a good balance:
# fast enough that stall detection fires within 1s of the threshold, slow
# enough that we don't burn CPU in the wait loop.
_POLL_INTERVAL_S = 1.0
_SHIMS_DIR = Path(__file__).resolve().parent / "shims"

# In-process cache of instantiated adapters. Adapters are stateless so we
# can reuse one instance across all invocations of the same agent.
_ADAPTER_CACHE: dict[str, AgentAdapter] = {}


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

    real_gh = shutil.which("gh", path=original_path) if original_path else None
    if real_gh:
        guarded_env["AGENT_REAL_GH"] = real_gh
    else:
        guarded_env.pop("AGENT_REAL_GH", None)

    real_git = shutil.which("git", path=original_path) if original_path else None
    if real_git:
        guarded_env["AGENT_REAL_GIT"] = real_git
    else:
        guarded_env.pop("AGENT_REAL_GIT", None)

    shim_path = str(_SHIMS_DIR)
    guarded_env["PATH"] = (
        f"{shim_path}{os.pathsep}{original_path}" if original_path else shim_path
    )
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


def _load_adapter(name: str) -> AgentAdapter:
    """Import the adapter class for ``name`` and cache the instance.

    Raises:
        AgentUnavailableError: If ``name`` is not in the registry, the
            entry has ``cli_available: False``, or the adapter module
            cannot be imported.
    """
    if name in _ADAPTER_CACHE:
        return _ADAPTER_CACHE[name]

    try:
        entry = get_agent_entry(name)
    except KeyError:
        raise AgentUnavailableError(
            f"Agent {name!r} is not in the registry. "
            f"Available: {sorted(AGENTS.keys())}"
        ) from None

    if not entry["cli_available"]:
        raise AgentUnavailableError(
            f"Agent {name!r} is registered but not available "
            f"(cli_available=False). This usually means its CLI does not "
            f"exist yet (e.g., grok). Implement adapters/{name}.py and "
            f"flip the registry flag to enable it."
        )

    dotted_path = entry["adapter"]
    if ":" not in dotted_path:
        raise AgentUnavailableError(
            f"Malformed adapter path in registry: {dotted_path!r}. "
            f"Expected 'module.path:ClassName'."
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
            f"Adapter class {class_name!r} not found in module "
            f"{module_path!r} for agent {name!r}."
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

    Design doc § 6.3: Codex is always fresh-session. Claude/Gemini bridge
    paths may keep resume (cache economics). delegate/dispatch never use
    resume (worktree is the isolation boundary).

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
) -> dict[str, Any]:
    """Assemble the usage record dict per design doc § 4.5 schema."""
    # Ensure unbounded strings are capped so the JSON stays under POSIX PIPE_BUF (4KB)
    # to maintain atomic append guarantees in usage.py.
    safe_cwd = str(cwd)[-250:] if cwd else ""
    safe_task_id = task_id[:100] if task_id else None
    safe_session_id = session_id[:100] if session_id else None

    return {
        "ts": datetime.now(UTC).isoformat(),
        "agent": agent,
        "entrypoint": entrypoint,
        "task_id": safe_task_id,
        "cwd": safe_cwd,
        "model": model,
        "mode": mode,
        "session_id": safe_session_id,
        "duration_s": round(duration_s, 2),
        "input_chars": input_chars,
        "output_chars": output_chars,
        "returncode": returncode,
        "outcome": outcome,
        "rate_limited": rate_limited,
        "stalled": stalled,
        "stderr_excerpt": (stderr_excerpt or "")[:500] if stderr_excerpt else None,
        "tokens": tokens,
    }


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
        env["GEMINI_AUTH_MODE"] = _normalize_gemini_tool_auth_mode(
            tool_config.get("auth_mode")
        )
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
    attempt_tool_config = dict(tool_config or {})
    attempt_tool_config["auth_mode"] = (
        "subscription" if rung.auth_mode == "oauth" else "api"
    )
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
) -> _ExecutionOutcome:
    """Spawn one plan, run watchdog/parse flow, and return raw execution state."""
    env = {**os.environ, **plan.env_overrides}
    for key in plan.env_unsets:
        env.pop(key, None)
    env = _apply_merge_guard(mode=mode, env=env)

    start_time = time.monotonic()
    proc: subprocess.Popen | None = None
    watchdog_state: WatchdogState | None = None
    watchdog_threads: list = []
    liveness_paths: tuple[Path, ...] = ()

    try:
        try:
            proc = subprocess.Popen(
                plan.cmd,
                stdin=subprocess.PIPE if plan.stdin_payload else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(cwd),
                env=env,
                bufsize=1,
                start_new_session=True,
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
                stderr_excerpt=(
                    f"Popen failed: {type(exc).__name__}: {exc}"
                )[:500],
                tokens=None,
            )
            write_record(record)
            raise AgentUnavailableError(
                f"{agent_name!r} Popen failed: {type(exc).__name__}: {exc}"
            ) from exc

        if plan.stdin_payload and proc.stdin is not None:
            try:
                proc.stdin.write(plan.stdin_payload)
                proc.stdin.close()
            except BrokenPipeError:
                pass

        liveness_paths = tuple(adapter.liveness_signal_paths(plan))
        if plan.output_file is not None and plan.output_file not in liveness_paths:
            liveness_paths = (*liveness_paths, plan.output_file)
        watchdog_state, watchdog_threads = start_watchdog(proc, list(liveness_paths))

        early_reap_check = getattr(adapter, "check_early_reap", None)
        kill_reason: str | None = None
        while True:
            returncode = proc.poll()
            if returncode is not None:
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

            kill_reason = should_kill(watchdog_state, stall_timeout, hard_timeout)
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

        for thread in watchdog_threads:
            if "stdout" in thread.name or "stderr" in thread.name:
                thread.join(timeout=5.0)

        stdout_text = "".join(watchdog_state.stdout_lines)
        stderr_text = "".join(watchdog_state.stderr_lines)

        stop_watchdog(watchdog_state, watchdog_threads, proc=proc)
        parse = adapter.parse_response(
            stdout=stdout_text,
            stderr=stderr_text,
            returncode=proc.returncode if proc.returncode is not None else -1,
            output_file=plan.output_file,
            plan=plan,
            call_start_time=start_time,
        )
        return _ExecutionOutcome(
            parse=parse,
            duration_s=duration_s,
            returncode=proc.returncode,
            kill_reason=kill_reason,
            stdout_text=stdout_text,
            stderr_text=stderr_text,
            liveness_paths=liveness_paths,
        )
    finally:
        if proc is not None and proc.poll() is None:
            with contextlib.suppress(Exception):
                _kill_process_tree(proc)

        if watchdog_state is not None:
            stop_watchdog(watchdog_state, watchdog_threads, proc=proc)

        if (
            plan.output_file is not None
            and plan.output_file.exists()
            and _is_temp_file(plan.output_file)
        ):
            should_delete = False
            try:
                file_size = plan.output_file.stat().st_size
            except OSError:
                file_size = -1

            if (
                file_size == 0
                or (proc is not None and proc.returncode == 0)
                or (
                    proc is not None
                    and proc.returncode is not None
                    and proc.returncode < 0
                )
            ):
                should_delete = True

            if should_delete:
                with contextlib.suppress(OSError):
                    plan.output_file.unlink()


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
    effort: str | None = None,
) -> Result:
    """Run Gemini through the shared model/auth fallback ladder."""
    last_telemetry: InvocationTelemetry | None = None

    def _attempt_runner(
        rung: GeminiRung,
        _attempt_index: int,
        timeout_s: int | None,
    ) -> AttemptOutcome:
        nonlocal last_telemetry
        attempt_tool_config = _build_gemini_attempt_tool_config(tool_config, rung)
        plan = adapter.build_invocation(
            prompt=prompt,
            mode=mode,
            cwd=cwd,
            model=rung.model,
            task_id=task_id,
            session_id=session_id,
            tool_config=attempt_tool_config,
            effort=effort,
        )
        last_telemetry = resolve_invocation_telemetry(
            agent_name=agent_name,
            plan=plan,
            requested_model=rung.model,
            requested_effort=effort,
        )
        execution = _execute_invocation_plan(
            agent_name=agent_name,
            adapter=adapter,
            plan=plan,
            prompt=prompt,
            mode=mode,
            cwd=cwd,
            model=rung.model,
            task_id=task_id,
            session_id=session_id,
            entrypoint=entrypoint,
            hard_timeout=timeout_s or hard_timeout,
            stall_timeout=stall_timeout,
        )
        parse = execution.parse

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
        or (
            last_attempt_record.model
            if last_attempt_record and last_attempt_record.model
            else model
        )
    )
    record_effort = last_telemetry.effort if last_telemetry is not None else "unknown"
    record_cli_version = (
        last_telemetry.cli_version if last_telemetry is not None else "unknown"
    )
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
            tokens=None,
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
            stderr_excerpt=stderr_excerpt,
            duration_s=call_result.elapsed_s,
            session_id=None,
            rate_limited=False,
            stalled=False,
            returncode=returncode,
            usage_record=record,
        )

    if call_result.attempts and all(
        attempt.status == "rate_limited" for attempt in call_result.attempts
    ):
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
            tokens=None,
        )
        write_record(record)
        raise RateLimitedError(agent_name, record_model, reason=(stderr_excerpt or "")[:200])

    if (
        (last_attempt_record is not None and last_attempt_record.status == "timeout")
        or "no budget left" in (call_result.error_message or "").lower()
    ):
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
            tokens=None,
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
        tokens=None,
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
        stderr_excerpt=stderr_excerpt,
        duration_s=call_result.elapsed_s,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=returncode,
        usage_record=record,
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
    hard_timeout: int = 86400,  # 24h — last-resort leak guard, NOT a
                                 # tuning knob for expected runtime. See
                                 # the header comment in
                                 # scripts/batch/batch_gemini_config.py
                                 # for the full design rationale.
    stall_timeout: int = 180,  # accepted but ignored; see docstring
    effort: str | None = None,
) -> Result:
    """Single entry point for all agent CLI invocations.

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
    adapter = _load_adapter(agent_name)

    # ---------- 2. Validate mode ----------
    if mode not in adapter.supported_modes:
        raise ValueError(
            f"Agent {agent_name!r} does not support mode {mode!r}. "
            f"Supported modes: {sorted(adapter.supported_modes)}"
        )

    # ---------- 3. Validate cwd for write modes ----------
    if mode in ("workspace-write", "danger") and cwd is None:
        raise ValueError(
            f"cwd is mandatory for mode={mode!r}. Write-capable invocations "
            f"must pin their working directory to prevent cross-worktree "
            f"contamination."
        )
    effective_cwd = cwd or Path.cwd()

    # ---------- 4. Resume policy ----------
    _enforce_resume_policy(agent_name, session_id, entrypoint)

    # ---------- 5. Pre-call rate-limit check ----------
    effective_model = model or adapter.default_model
    ok, reason = has_headroom(agent_name, effective_model)
    if not ok:
        # Record the short-circuit for observability — the caller didn't
        # burn a quota slot, but we still want the usage log to show it.
        record = _build_usage_record(
            agent=agent_name,
            entrypoint=entrypoint,
            model=effective_model,
            mode=mode,
            task_id=task_id,
            cwd=effective_cwd,
            session_id=session_id,
            duration_s=0.0,
            input_chars=len(prompt),
            output_chars=0,
            returncode=None,
            outcome="rate_limited",
            rate_limited=True,
            stalled=False,
            stderr_excerpt=f"pre-call headroom check: {reason}",
            tokens=None,
        )
        write_record(record)
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
            effort=effort,
        )

    # ---------- 6. Build invocation plan ----------
    plan = adapter.build_invocation(
        prompt=prompt,
        mode=mode,
        cwd=effective_cwd,
        model=effective_model,
        task_id=task_id,
        session_id=session_id,
        tool_config=tool_config,
        effort=effort,
    )

    telemetry = resolve_invocation_telemetry(
        agent_name=agent_name,
        plan=plan,
        requested_model=effective_model,
        requested_effort=effort,
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
    )
    parse = execution.parse

    if execution.kill_reason == "hard_timeout" and not parse.ok:
        record = _build_usage_record(
            agent=agent_name,
            entrypoint=entrypoint,
            model=effective_model,
            mode=mode,
            task_id=task_id,
            cwd=effective_cwd,
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
            tokens=None,
        )
        write_record(record)
        raise AgentTimeoutError(agent_name, hard_timeout)

    if parse.rate_limited:
        outcome = "rate_limited"
    elif parse.ok:
        outcome = "ok"
    else:
        outcome = "error"

    record = _build_usage_record(
        agent=agent_name,
        entrypoint=entrypoint,
        model=telemetry.model,
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
    )
    write_record(record)

    if parse.rate_limited:
        raise RateLimitedError(
            agent_name,
            telemetry.model,
            reason=(parse.stderr_excerpt or "")[:200],
        )

    return Result(
        ok=parse.ok,
        agent=agent_name,
        model=telemetry.model,
        mode=mode,
        effort=telemetry.effort,
        cli_version=telemetry.cli_version,
        response=parse.response,
        stderr_excerpt=parse.stderr_excerpt,
        duration_s=execution.duration_s,
        session_id=parse.session_id,
        rate_limited=parse.rate_limited,
        stalled=False,
        returncode=execution.returncode,
        usage_record=record,
    )
