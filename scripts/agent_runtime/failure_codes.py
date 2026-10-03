"""Closed, body-free failure codes the agent runtime persists in usage records.

The runner admits only these codes into ``failure_code``; the runtime API
reads the same set, so every code the runtime emits stays visible (#9532).
"""

from __future__ import annotations

import json
import re

RUNTIME_FAILURE_CODES = frozenset(
    {
        "acp_adapter_incompatible",
        "acp_adapter_missing",
        "acp_agent_disconnected",
        "acp_agent_startup",
        "acp_auth_required",
        "acp_permission_denied",
        "acp_permission_unavailable",
        "acp_review_evidence_invalid",
        "acp_review_evidence_too_large",
        "acp_session_create_timeout",
        "acp_turn_limit",
        "github_secondary_rate_limited",
        "adapter_refused",
        "cwd_unpinned",
        "primary_tree_write",
        "protocol_output_limit",
        "provider_auth",
        "provider_overloaded",
        "provider_policy_refusal",
        "provider_stream_incomplete",
        "provider_unavailable",
        "provider_error",
        "rate_limited",
        "result_invalid",
        "timeout",
        "transport_error",
        "unknown",
    }
)


# These recognizers apply only to provider error fields or whole CLI error
# lines, never to response/tool text. Unknown errors keep provider_error.
_PROVIDER_DIAGNOSTIC_RE = re.compile(
    r"^(?:(?:opencode|kimi|grok|agy|gemini|cursor|provider|acp transport):\s*)?(?:error:\s*)?"
    r"(?:(?:HTTP\s+|unexpected status\s+|status\s+)[45]\d{2}\b|[45]\d{2}\s+(?:RESOURCE_EXHAUSTED|quota|too many|unauthorized)\b|"
    r"(?:RateLimitError|APIError):|RESOURCE_EXHAUSTED\b|"
    r"rate[_ ]limit(?:ed| exceeded| reached)?\b|usage limit reached\b|quota exceeded\b|"
    r"no capacity available\b|daily\s+limit\s+exceeded\b)",
    re.IGNORECASE,
)


def provider_failure_code(message: str, status: object = None) -> str:
    """Classify a caller-attributed provider error, before display truncation."""
    if status in (429, "429", "RESOURCE_EXHAUSTED"):
        return "rate_limited"
    if status in (401, "401", "UNAUTHENTICATED"):
        return "provider_auth"
    if status in (503, "503", "UNAVAILABLE"):
        return "provider_overloaded"
    codes: set[str] = set()
    for line in message.split("\n"):
        line = line.strip()
        if not _PROVIDER_DIAGNOSTIC_RE.match(line):
            codes.add("provider_error")
            continue
        # Numeric provider status takes precedence over words quoted in its
        # error body (e.g. HTTP 400 explaining a rate-limit parameter).
        match = re.match(
            r"^(?:(?:opencode|kimi|grok|agy|gemini|cursor|provider|acp transport):\s*)?"
            r"(?:error:\s*)?(?:(?:HTTP|unexpected status|status)\s+)?(?P<status>[45]\d{2})\b",
            line,
            re.IGNORECASE,
        )
        if match:
            codes.add(
                {"429": "rate_limited", "401": "provider_auth", "503": "provider_overloaded"}.get(
                    match["status"], "provider_error"
                )
            )
        elif re.search(r"no capacity available", line, re.IGNORECASE):
            codes.add("provider_overloaded")
        elif re.search(
            r"RateLimitError|rate[_ ]limit|usage limit|quota exceeded|resource_exhausted|"
            r"daily\s+limit\s+exceeded",
            line,
            re.IGNORECASE,
        ):
            codes.add("rate_limited")
        else:
            codes.add("provider_error")
    if len(codes) == 1:
        return codes.pop()
    return "provider_error"


def provider_stderr_error(stderr: str) -> str:
    """Select only CLI provider diagnostic lines; skip JSON/tool/log prose."""
    # A bare mention such as "rate limit regression test returned 429" is
    # not a diagnostic. Error/provider prefixes, HTTP status lines and the
    # CLI's gRPC/capacity markers are the unstructured fallback boundary.
    diagnostic_prefix = re.compile(
        r"^(?:error:|(?:opencode|kimi|grok|agy|gemini|cursor|provider|acp transport):|"
        r"HTTP\s+[45]\d{2}\b|[45]\d{2}\s+(?:RESOURCE_EXHAUSTED|quota|too many|unauthorized)\b|"
        r"(?:RateLimitError|APIError):|RESOURCE_EXHAUSTED\b|no capacity available\b|"
        r"quota exceeded for (?:project|this account)\b|"
        r"unexpected status\s+[45]\d{2}\b|status\s+[45]\d{2}\b)",
        re.IGNORECASE,
    )
    lines = [
        line.strip()
        for line in stderr.split("\n")
        if diagnostic_prefix.match(line.strip()) and _PROVIDER_DIAGNOSTIC_RE.match(line.strip())
    ]
    return "\n".join(lines)


def opencode_provider_error(stdout: str) -> tuple[str, str | None]:
    """Read top-level OpenCode error envelopes, never nested part/state data."""
    errors: list[tuple[str, str]] = []
    for line in stdout.split("\n"):
        try:
            event = json.loads(line)
        except (ValueError, RecursionError):
            continue
        if not isinstance(event, dict) or event.get("type") != "error":
            continue
        error = event.get("error")
        if not isinstance(error, dict):
            errors.append(("", "provider_error"))
            continue
        data = error.get("data")
        data = data if isinstance(data, dict) else {}
        message = data.get("message")
        message = message if isinstance(message, str) else ""
        errors.append((message, provider_failure_code(message, data.get("statusCode"))))
    if not errors:
        return "", None
    codes = {code for _, code in errors}
    return "\n".join(message for message, _ in errors), codes.pop() if len(codes) == 1 else "provider_error"
