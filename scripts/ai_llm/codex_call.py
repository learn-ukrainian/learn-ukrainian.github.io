"""Codex fallback wrapper for wiki compilation."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

from ai_llm.agent_runtime_call import call_agent_with_fallback
from ai_llm.fallback import CallResult

CODEX_MODEL_LADDER = ("gpt-5.5", "gpt-5.4", "gpt-5.4-mini")


def call_codex_with_fallback(
    prompt: str,
    *,
    task_name: str,
    preferred_model: str = "gpt-5.5",
    effort: str | None = "high",
    per_rung_timeout_s: int | None = None,
    overall_timeout_s: int | None = None,
    max_retries: int = 3,
    cwd: Path | None = None,
    base_env: Mapping[str, str] | None = None,
    logger: Callable[[str], None] | None = None,
    sleep_fn: Callable[[int, str], None] | None = None,
) -> CallResult:
    """Call Codex through the agent_runtime adapter."""
    return call_agent_with_fallback(
        agent_name="codex",
        prompt=prompt,
        task_name=task_name,
        preferred_model=preferred_model,
        fallback_models=CODEX_MODEL_LADDER,
        effort=effort,
        per_rung_timeout_s=per_rung_timeout_s,
        overall_timeout_s=overall_timeout_s,
        max_retries=max_retries,
        cwd=cwd,
        base_env=base_env,
        logger=logger,
        sleep_fn=sleep_fn,
    )
