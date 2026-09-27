"""Shared CallResult adapter for non-Gemini agent-runtime writers."""
from __future__ import annotations

import os
import time
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from pathlib import Path

from agent_runtime import runner
from agent_runtime.errors import AgentRuntimeError, AgentTimeoutError, RateLimitedError
from ai_llm.fallback import AttemptRecord, CallResult, visible_sleep


@contextmanager
def _patched_environ(base_env: Mapping[str, str] | None):
    if base_env is None:
        yield
        return

    old_env = os.environ.copy()
    os.environ.clear()
    os.environ.update(base_env)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old_env)


def _build_model_ladder(
    preferred_model: str,
    fallback_models: tuple[str, ...],
) -> list[str]:
    models = (preferred_model, *fallback_models)
    deduped = list(dict.fromkeys(models))
    if preferred_model in fallback_models:
        return list(fallback_models[fallback_models.index(preferred_model):])
    return deduped


def call_agent_with_fallback(
    *,
    agent_name: str,
    prompt: str,
    task_name: str,
    preferred_model: str,
    fallback_models: tuple[str, ...],
    effort: str | None,
    per_rung_timeout_s: int | None,
    overall_timeout_s: int | None,
    max_retries: int,
    cwd: Path | None,
    base_env: Mapping[str, str] | None,
    logger: Callable[[str], None] | None,
    sleep_fn: Callable[[int, str], None] | None,
) -> CallResult:
    """Call an agent-runtime writer and convert attempts to ``CallResult``."""
    emit = logger or print
    sleeper = sleep_fn or (lambda seconds, reason: visible_sleep(seconds, reason, logger=emit))
    workdir = cwd or Path.cwd()
    models = _build_model_ladder(preferred_model, fallback_models)
    attempts: list[AttemptRecord] = []
    overall_start = time.monotonic()
    last_error: str | None = None

    for rung_index, model in enumerate(models, 1):
        for attempt_index in range(1, max_retries + 1):
            hard_timeout = _resolve_attempt_timeout(
                overall_timeout_s=overall_timeout_s,
                per_rung_timeout_s=per_rung_timeout_s,
                overall_start=overall_start,
            )
            if hard_timeout == 0:
                last_error = f"{task_name}: no budget left for {model}"
                return CallResult(
                    response_text=None,
                    model_used=None,
                    auth_mode_used=None,
                    elapsed_s=time.monotonic() - overall_start,
                    attempts=attempts,
                    error_message=last_error,
                )

            emit(
                f"🎯 {agent_name} rung {rung_index}/{len(models)}: {model} "
                f"(attempt {attempt_index}/{max_retries})"
            )
            attempt = _invoke_once(
                agent_name=agent_name,
                prompt=prompt,
                task_name=task_name,
                model=model,
                effort=effort,
                hard_timeout=hard_timeout,
                workdir=workdir,
                base_env=base_env,
            )
            attempts.append(
                AttemptRecord(
                    rung_index=rung_index,
                    rung_total=len(models),
                    model=attempt["model"],
                    auth_mode="api",
                    attempt_index=attempt_index,
                    max_retries=max_retries,
                    status=attempt["status"],
                    elapsed_s=attempt["elapsed_s"],
                    returncode=attempt["returncode"],
                    stderr_excerpt=attempt["error"],
                    response_chars=len(attempt["response"] or ""),
                )
            )

            if attempt["status"] == "success":
                emit(f"  ✓ {agent_name} responded in {attempt['elapsed_s']:.1f}s.")
                return CallResult(
                    response_text=attempt["response"],
                    model_used=attempt["model"],
                    auth_mode_used=None,
                    elapsed_s=time.monotonic() - overall_start,
                    attempts=attempts,
                    error_message=None,
                )

            last_error = attempt["error"] or f"{agent_name} failed for {model}"
            if attempt["status"] == "rate_limited":
                emit(f"  ⚠️  {agent_name} rate-limited: {last_error}")
                break

            emit(f"  ⚠️  {agent_name} failure: {last_error}")
            if attempt_index < max_retries:
                sleeper(10, f"{task_name} {agent_name} retry backoff")

    error = last_error or f"{task_name}: all {agent_name} fallback rungs failed"
    return CallResult(
        response_text=None,
        model_used=None,
        auth_mode_used=None,
        elapsed_s=time.monotonic() - overall_start,
        attempts=attempts,
        error_message=error,
    )


def _resolve_attempt_timeout(
    *,
    overall_timeout_s: int | None,
    per_rung_timeout_s: int | None,
    overall_start: float,
) -> int | None:
    if overall_timeout_s is None:
        return per_rung_timeout_s

    remaining_s = int(overall_timeout_s - (time.monotonic() - overall_start))
    if remaining_s <= 0:
        return 0
    return min(per_rung_timeout_s, remaining_s) if per_rung_timeout_s else remaining_s


def _invoke_once(
    *,
    agent_name: str,
    prompt: str,
    task_name: str,
    model: str,
    effort: str | None,
    hard_timeout: int | None,
    workdir: Path,
    base_env: Mapping[str, str] | None,
) -> dict[str, object]:
    attempt_start = time.monotonic()
    try:
        with _patched_environ(base_env):
            result = runner.invoke(
                agent_name,
                prompt,
                mode="read-only",
                cwd=workdir,
                model=model,
                task_id=task_name,
                tool_config=None,
                entrypoint="runtime",
                hard_timeout=hard_timeout or 24 * 60 * 60,
                effort=effort,
            )
    except RateLimitedError as exc:
        return _attempt("rate_limited", model, time.monotonic() - attempt_start, error=str(exc))
    except AgentTimeoutError as exc:
        return _attempt("timeout", model, time.monotonic() - attempt_start, error=str(exc))
    except AgentRuntimeError as exc:
        return _attempt(
            "retryable_error",
            model,
            time.monotonic() - attempt_start,
            error=str(exc),
        )

    if result.ok:
        return _attempt(
            "success",
            result.model or model,
            result.duration_s,
            response=result.response,
            error=result.stderr_excerpt,
            returncode=result.returncode,
        )

    error = result.stderr_excerpt or f"{agent_name} returned ok=False for {model}"
    return _attempt(
        "retryable_error",
        result.model or model,
        result.duration_s,
        error=error,
        returncode=result.returncode,
    )


def _attempt(
    status: str,
    model: str,
    elapsed_s: float,
    *,
    response: str | None = None,
    error: str | None = None,
    returncode: int | None = None,
) -> dict[str, object]:
    return {
        "status": status,
        "model": model,
        "elapsed_s": elapsed_s,
        "response": response,
        "error": error,
        "returncode": returncode,
    }
