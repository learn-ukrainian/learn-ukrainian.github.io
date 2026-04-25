"""Claude Code fallback wrapper for wiki compilation."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

from ai_llm.agent_runtime_call import call_agent_with_fallback
from ai_llm.fallback import CallResult

CLAUDE_MODEL_LADDER = ("claude-opus-4-7", "claude-sonnet-4-5")


def call_claude_with_fallback(
    prompt: str,
    *,
    task_name: str,
    preferred_model: str = "claude-opus-4-7",
    effort: str | None = "xhigh",
    per_rung_timeout_s: int | None = None,
    overall_timeout_s: int | None = None,
    max_retries: int = 3,
    cwd: Path | None = None,
    base_env: Mapping[str, str] | None = None,
    logger: Callable[[str], None] | None = None,
    sleep_fn: Callable[[int, str], None] | None = None,
) -> CallResult:
    """Call Claude Code through the agent_runtime adapter."""
    return call_agent_with_fallback(
        agent_name="claude",
        prompt=prompt,
        task_name=task_name,
        preferred_model=preferred_model,
        fallback_models=CLAUDE_MODEL_LADDER,
        effort=effort,
        per_rung_timeout_s=per_rung_timeout_s,
        overall_timeout_s=overall_timeout_s,
        max_retries=max_retries,
        cwd=cwd,
        base_env=base_env,
        logger=logger,
        sleep_fn=sleep_fn,
    )
