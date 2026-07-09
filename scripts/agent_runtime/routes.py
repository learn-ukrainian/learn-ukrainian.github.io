"""Shared route identity helpers for agent runtime adapters and runner."""
from __future__ import annotations

import os
import re
from typing import Any

RUNTIME_ROUTE_TOOL_CONFIG_KEY = "agent_runtime_route"
HERMES_GLM_FORBIDDEN_MARKER = "HERMES_GLM_FORBIDDEN"

_FORBIDDEN_GLM_MODEL_RE = re.compile(r"(^|[/_.:-])glm($|[/_.:-]|\d)", re.IGNORECASE)


def normalize_route_part(value: Any) -> str:
    return str(value or "").strip()


def is_forbidden_glm_route(provider: Any, model: Any) -> bool:
    """Return True for local-only zai/GLM routes forbidden in automation."""
    provider_text = normalize_route_part(provider).lower()
    model_text = normalize_route_part(model).lower()
    if provider_text in {"zai", "z-ai", "glm"}:
        return True
    if model_text.startswith(("zai/", "z-ai/")):
        return True
    return bool(_FORBIDDEN_GLM_MODEL_RE.search(model_text))


def forbidden_glm_error(
    *,
    provider: Any,
    model: Any,
    source: str,
) -> str:
    """Build the explicit hard-fail text for forbidden zai/GLM routes."""
    return (
        f"{HERMES_GLM_FORBIDDEN_MARKER}: automated Hermes run refused "
        f"local-only zai/GLM route from {source}: "
        f"provider={normalize_route_part(provider)!r} "
        f"model={normalize_route_part(model)!r}"
    )


DEEPSEEK_FIRST_PARTY_FORBIDDEN_MARKER = "DEEPSEEK_FIRST_PARTY_FORBIDDEN"

_CI_ENV_VARS = ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILDKITE", "JENKINS_URL")


def is_deepseek_first_party_forbidden_in_ci(provider: Any, model: Any) -> bool:
    """Return True for first-party DeepSeek (China-hosted, local-only) in CI/automation."""
    # Skip guard during pytest (even in CI) so unit tests can exercise the adapter.
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return False
    provider_text = normalize_route_part(provider).lower()
    if provider_text == "deepseek":
        return any(os.environ.get(v) for v in _CI_ENV_VARS)
    return False


def deepseek_first_party_error(
    *,
    provider: Any,
    model: Any,
    source: str,
) -> str:
    """Build the explicit hard-fail text for first-party DeepSeek in CI."""
    return (
        f"{DEEPSEEK_FIRST_PARTY_FORBIDDEN_MARKER}: automated Hermes run refused "
        f"China-hosted first-party DeepSeek (local-only, never CI) from {source}: "
        f"provider={normalize_route_part(provider)!r} "
        f"model={normalize_route_part(model)!r}"
    )
