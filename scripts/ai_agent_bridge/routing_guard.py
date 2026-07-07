"""Deterministic model-routing guards (user spend orders, 2026-07-05).

Rules that lived only in memory/prose leaked twice with real money attached:

1. **Qwen exclusion** ("too expensive", standing order): a qwen review dispatch
   still fired on 2026-07-04 (`4307-qwen-schema-review`, qwen/qwen3.6-plus) —
   months after the May 2026 qwen3.7-max bakeoffs that created the rule.
2. **No OpenRouter for subscription families** (user order 2026-07-05, hard):
   the user holds Anthropic, OpenAI, and Google subscriptions — paying
   OpenRouter per-token for claude-*/gpt-*/gemini-* wastes money the
   subscription already covers. OpenRouter is ONLY for models with no
   subscription lane (e.g. gemma paid pin, deepseek API).

This module makes both rules load-bearing at every model-invocation choke
point (opencode bridge, reviewer/bakeoff transport, delegate dispatch).

Escape hatch: set ``LU_ROUTING_GUARD_OVERRIDE=1`` for a deliberate,
user-authorized exception; the guard error message names it.
"""

from __future__ import annotations

import os
import re

_QWEN_RE = re.compile(r"(?:^|[/:_-])qwen", re.IGNORECASE)
# Subscription families that must NEVER route through OpenRouter. gemma is
# google/ but has no subscription lane — only gemini is subscription-covered.
_SUBSCRIPTION_VIA_OPENROUTER_RE = re.compile(
    r"openrouter/(?:anthropic/|openai/|google/gemini)", re.IGNORECASE
)
_SUBSCRIPTION_VIA_DEEPSEEK_DIRECT_RE = re.compile(
    r"deepseek-direct/(?:anthropic/|openai/|google/gemini|claude|gpt-|gemini)",
    re.IGNORECASE,
)
_OVERRIDE_ENV = "LU_ROUTING_GUARD_OVERRIDE"


class RoutingGuardError(RuntimeError):
    """A model invocation violates a standing user spend order."""


def assert_model_routing_allowed(model: str | None, *, context: str) -> None:
    """Raise :class:`RoutingGuardError` for forbidden model routings.

    ``context`` names the call site for the error message (and telemetry).
    """
    if os.environ.get(_OVERRIDE_ENV) == "1":
        return
    text = str(model or "").strip()
    if not text:
        return
    if _QWEN_RE.search(text):
        raise RoutingGuardError(
            f"{context}: qwen models are EXCLUDED by standing user order "
            f"(too expensive; May-2026 bakeoff burn). Refusing {text!r}. "
            f"Set {_OVERRIDE_ENV}=1 only with explicit user authorization."
        )
    if _SUBSCRIPTION_VIA_OPENROUTER_RE.search(text):
        raise RoutingGuardError(
            f"{context}: {text!r} routes a SUBSCRIPTION family (anthropic/"
            f"openai/gemini) through OpenRouter — forbidden by user order "
            f"2026-07-05 (subscription already paid; metered spend is waste). "
            f"Use the native subscription lane instead. Set {_OVERRIDE_ENV}=1 "
            f"only with explicit user authorization."
        )
    if _SUBSCRIPTION_VIA_DEEPSEEK_DIRECT_RE.search(text):
        raise RoutingGuardError(
            f"{context}: {text!r} routes a SUBSCRIPTION family (anthropic/"
            f"openai/gemini) through the DeepSeek first-party provider. "
            "deepseek-direct may only run DeepSeek-family pins. Use the "
            "native subscription lane instead. "
            f"Set {_OVERRIDE_ENV}=1 only with explicit user authorization."
        )


def assert_agent_routing_allowed(agent: str | None, *, context: str) -> None:
    """Refuse dispatch agents that are excluded outright (qwen)."""
    if os.environ.get(_OVERRIDE_ENV) == "1":
        return
    if str(agent or "").strip().lower() == "qwen":
        raise RoutingGuardError(
            f"{context}: the qwen dispatch lane is EXCLUDED by standing user "
            f"order (too expensive). Set {_OVERRIDE_ENV}=1 only with explicit "
            f"user authorization."
        )
