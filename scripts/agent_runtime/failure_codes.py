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
        "github_auth_required",
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


# Only callers that have isolated provider error fields may use this search.
# Raw streams must first pass provider_stderr_error's terminal-line boundary.
_KIMI_PROVIDER_CODES = {
    "rate_limit": "rate_limited",
    "auth_error": "provider_auth",
    "overloaded": "provider_overloaded",
    "connection_error": "transport_error",
    "filtered": "provider_policy_refusal",
    "api_error": "provider_error",
}
_PROVIDER_STATUS_RE = re.compile(
    r"(?:\bHTTP\s+|\bunexpected status\s+|\bstatus(?: code)?[\s:=]+|"
    r"\bError code:[ ]*|\bgoogleapi: Error[ ]*|\bfailed with[ ]*|[\"']code[\"']\s*:\s*)([45]\d{2})\b|"
    r"^\s*([45]\d{2})\b",
    re.IGNORECASE | re.MULTILINE,
)
_PROVIDER_MARKERS = (
    (
        "rate_limited",
        re.compile(
            r"RateLimitError|TerminalQuotaError|rate[_ ]limit|usage limit|quota exceeded|"
            r"resource_exhausted|quota_exhausted|too many requests|exhausted your daily quota|"
            r"daily\s+limit\s+exceeded",
            re.IGNORECASE,
        ),
    ),
    (
        "provider_auth",
        re.compile(
            r"unauthorized|unauthenticated|forbidden|invalid api key|authentication (?:failed|required)|"
            r"auth(?:orization)? failed|no api key(?: was)? (?:found|set|configured)|missing api key|"
            r"no credentials? (?:found|set|configured|available)",
            re.IGNORECASE,
        ),
    ),
    (
        "provider_overloaded",
        re.compile(
            r"no capacity available|server error|service unavailable|bad gateway|gateway timeout|"
            r"overloaded|over capacity|upstream error",
            re.IGNORECASE,
        ),
    ),
    (
        "transport_error",
        re.compile(
            r"connection refused|connection reset|connection aborted|econnrefused|econnreset|etimedout|"
            r"network is unreachable|read timeout|timed out|timeout while connecting|"
            r"temporarily unavailable|APIConnection(?:Timeout)?Error",
            re.IGNORECASE,
        ),
    ),
)


def provider_failure_code(message: str, status: object = None) -> str:
    """Classify attributed provider diagnostics; explicit codes outrank prose."""
    if status is not None:
        # An explicit non-retryable status must never fall through to body
        # words (e.g. a 400 discussing rate-limit configuration).
        value = str(status)
        if value in {"429", "RESOURCE_EXHAUSTED"}:
            return "rate_limited"
        if value in {"401", "403", "UNAUTHENTICATED", "PERMISSION_DENIED"}:
            return "provider_auth"
        if value == "UNAVAILABLE" or re.fullmatch(r"5\d{2}", value):
            return "provider_overloaded"
        return "provider_error"

    # Provider names (e.g. provider.openrouter) are not typed failure codes.
    typed_codes = {
        _KIMI_PROVIDER_CODES[match]
        for match in re.findall(r"\bprovider\.([a-z_]+)\b", message)
        if match in _KIMI_PROVIDER_CODES
    }
    if typed_codes:
        return typed_codes.pop() if len(typed_codes) == 1 else "provider_error"
    status_match = _PROVIDER_STATUS_RE.search(message)
    if status_match:
        return provider_failure_code("", status_match[1] or status_match[2])
    codes = {code for code, pattern in _PROVIDER_MARKERS if pattern.search(message)}
    return codes.pop() if len(codes) == 1 else "provider_error"


# These are CLI terminal formats, not generic mentions of status words.
# Kimi wraps typed errors in "error: failed to run prompt: provider.*";
# Gemini prints quota errors / Gaxios errors and an [API Error: ...] wrapper;
# Cursor's auth diagnostic begins "Error: Authentication required.".
_STDERR_GENERIC_PREFIX = re.compile(
    r"^(?:error:|(?:opencode|kimi|grok|agy|gemini|cursor|provider|acp transport):)\s*"
    r"(?:failed to run prompt:\s*(?=provider\.[a-z_]+\b))?",
    re.IGNORECASE,
)
_STDERR_DIAGNOSTIC_PREFIX = re.compile(
    r"^(?:hermes -z: agent failed:|provider\.[a-z_]+:|"
    r"HTTP\s+[45]\d{2}\b|[45]\d{2}\s+(?:RESOURCE_EXHAUSTED|quota|too many|unauthorized)\b|"
    r"(?:RateLimitError|APIError|TerminalQuotaError|RetryableQuotaError|GaxiosError|"
    r"APIConnectionError|APIConnectionTimeoutError):|(?:✕\s+)?\[API Error:|"
    r"Attempt \d+ failed(?: with status [45]\d{2})?[.:]|"
    r"Attempt \d+ failed with (?:429|5xx) error\b|"
    r"RESOURCE_EXHAUSTED\b|no capacity available\b|quota exceeded\b|"
    r"connection (?:refused|reset|aborted)\b|(?:econnrefused|econnreset|etimedout)\b|"
    r"network is unreachable\b|read timeout\b|"
    r"rate limit exceeded\b|The model is overloaded\b|"
    r"unexpected status\s+[45]\d{2}\b|status(?: code)?\s+[45]\d{2}\b|"
    r"Error code:\s*[45]\d{2}\b|Request failed with status code\s+[45]\d{2}\b|"
    r"googleapi: Error\s+[45]\d{2}\b)",
    re.IGNORECASE,
)


def provider_stderr_error(stderr: str) -> str:
    """Select CLI terminal diagnostics, never JSON tool envelopes or log prose."""
    diagnostics: list[str] = []
    offset = 0
    for line in stderr.splitlines(keepends=True):
        diagnostic = line.strip()
        generic_prefix = _STDERR_GENERIC_PREFIX.match(diagnostic)
        # A generic CLI prefix cannot attribute later tool/test text. Only
        # an immediate marker (or Kimi's explicit typed wrapper) admits it.
        marker_text = diagnostic[generic_prefix.end() :] if generic_prefix else diagnostic
        if _STDERR_DIAGNOSTIC_PREFIX.match(marker_text) or (
            generic_prefix and any(pattern.match(marker_text) for _, pattern in _PROVIDER_MARKERS)
        ):
            # Gemini's API Error wrapper may pretty-print its JSON payload.
            # Decode exactly that payload; adjacent tool/log text is excluded.
            if diagnostic.startswith(("[API Error:", "✕ [API Error:")):
                start = offset + line.index("[API Error:") + len("[API Error:")
                payload = stderr[start:].lstrip()
                try:
                    _, end = json.JSONDecoder().raw_decode(payload)
                except (ValueError, RecursionError):
                    pass
                else:
                    diagnostic = "[API Error: " + payload[:end] + "]"
            diagnostics.append(diagnostic)
        offset += len(line)
    return "\n".join(diagnostics)


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
