"""Diagnostic redaction confined to the served lane-health view (#9899).

Apply after the shared secret redactor. Local .diag files, stored messages,
telemetry and other API routes retain their existing redaction contracts.
"""

from __future__ import annotations

import re
from urllib.parse import unquote_plus

try:
    from secret_redactor import REDACTION, iter_url_matches, redact_url_authority, redact_value
except ImportError:
    from scripts.secret_redactor import REDACTION, iter_url_matches, redact_url_authority, redact_value

try:
    from api.opsec_scan import scan_text
except ImportError:
    from scripts.api.opsec_scan import scan_text

OPSEC_PLACEHOLDERS = {
    "filesystem-root": "[redacted-path]",
    "user-at-host": "[redacted-host]",
    "host-port": "[redacted-host]",
    "ssh-alias": "[redacted-host]",
    "ipv4": "[redacted-ip]",
    "ipv6": "[redacted-ip]",
}
REDACTION_PLACEHOLDER_RE = re.compile("|".join(re.escape(value) for value in {REDACTION, *OPSEC_PLACEHOLDERS.values()}))
_QUERY_PARAMETER_RE = re.compile(r"(?P<prefix>(?:^|&)(?P<key>[^=&]+)=)(?P<value>[^&]*)")
_DIAGNOSTIC_PATH_PATTERNS = (
    re.compile(r"(?<![A-Za-z0-9_./\\-])(?:[A-Za-z]:[\\/]|\\\\[A-Za-z0-9_.-]+\\)[^\s\"'<>`]+"),
    re.compile(r"(?<![A-Za-z0-9_./-])~(?:[A-Za-z_][A-Za-z0-9_-]*)?/[^\s\"'<>`]+"),
)
_RESOLVER_HOST_RE = re.compile(
    r"(?i)\b(?:ENOTFOUND|EAI_AGAIN|EAI_NONAME|ENODATA)[ \t]+['\"]?"
    r"(?P<host>[A-Za-z0-9][A-Za-z0-9_.-]*)(?![A-Za-z0-9_.:/@-])"
)


def redact_lane_health_diagnostics(text: str) -> str:
    """Rewrite diagnostic shapes using the shared URL-userinfo rule.

    All URL hosts and ports are redacted; path, non-secret query and fragment
    bytes are preserved. The shared rule handles malformed passwords with
    raw /, ? and # while preserving ambiguous numeric-port/path shapes.
    """
    parts = []
    cursor = 0
    for match in iter_url_matches(text):
        parts.append(_redact_non_url_diagnostics(text[cursor : match.start()]))
        parts.append(_redact_url_match(match))
        cursor = match.end()
    parts.append(_redact_non_url_diagnostics(text[cursor:]))
    return "".join(parts)


def _redact_non_url_diagnostics(text: str) -> str:
    """Apply diagnostic rules outside URLs so their suffix bytes survive."""
    rewritten = text
    for pattern in _DIAGNOSTIC_PATH_PATTERNS:
        rewritten = pattern.sub(_redact_path_match, rewritten)
    rewritten = _RESOLVER_HOST_RE.sub(_redact_resolver_host_match, rewritten)
    # Markdown delimiters bound scanner spans here; the shared scanner retains
    # its existing contract. URLs are handled separately.
    findings = []
    for segment in re.finditer(r"[^`]+", rewritten):
        for finding in scan_text(segment.group(), operation="lane_health"):
            if finding.kind not in OPSEC_PLACEHOLDERS:
                continue
            start, end = segment.start() + finding.start, segment.start() + finding.end
            findings.append((start, end, OPSEC_PLACEHOLDERS[finding.kind]))
    for start, end, placeholder in sorted(findings, reverse=True):
        rewritten = rewritten[:start] + placeholder + rewritten[end:]
    return rewritten


def _redact_path_match(match: re.Match[str]) -> str:
    raw = match.group()
    token = raw.rstrip(".,;:!?)]}")
    return "[redacted-path]" + raw[len(token) :]


def _redact_resolver_host_match(match: re.Match[str]) -> str:
    host = match.group("host").rstrip(".")
    if host.upper() in {"ENOTFOUND", "EAI_AGAIN", "EAI_NONAME", "ENODATA"}:
        return match.group()
    start = match.start("host") - match.start()
    raw = match.group()
    return raw[:start] + "[redacted-host]" + raw[start + len(host) :]


def _redact_url_match(match: re.Match[str]) -> str:
    prefix, raw_authority, suffix = redact_url_authority(match.group())
    if not raw_authority and not suffix:
        return prefix
    fragment_start = suffix.find("#")
    query_end = fragment_start if fragment_start >= 0 else len(suffix)
    query_marker = suffix.find("?", 0, query_end)
    if query_marker >= 0:
        query_start = query_marker + 1
        query = _QUERY_PARAMETER_RE.sub(_redact_query_match, suffix[query_start:query_end])
        suffix = suffix[:query_start] + query + suffix[query_end:]
    userinfo, separator, host = raw_authority.rpartition("@")
    authority = "[redacted-host]"
    if host.startswith("[redacted-ip]") or any(f.kind in {"ipv4", "ipv6"} for f in scan_text(host)):
        authority = "[redacted-ip]"
    if separator:
        authority = userinfo + "@" + authority
    return prefix + authority + suffix


def _redact_query_match(match: re.Match[str]) -> str:
    key = unquote_plus(match.group("key"))
    if (
        key.lower() in {"sig", "signature", "x-amz-signature", "x-goog-signature"}
        or redact_value({key: ""})[key] == REDACTION
    ):
        return match.group("prefix") + REDACTION
    return match.group()
