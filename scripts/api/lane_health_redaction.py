"""Diagnostic redaction confined to the served lane-health view (#9899).

Apply after the shared secret redactor. Local .diag files, stored messages,
telemetry and other API routes retain their existing redaction contracts.
"""

from __future__ import annotations

import re
from urllib.parse import unquote_plus

try:
    from secret_redactor import REDACTION, redact_value
except ImportError:
    from scripts.secret_redactor import REDACTION, redact_value

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
_URL_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9+.-]*://[^\s<>\"`]+")
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
    """Rewrite diagnostic shapes without changing any shared redactor.

    All URL hosts and ports are redacted; path, non-secret query and fragment
    bytes are preserved. In a malformed URL, host:digits/ is ambiguous with
    a slash-containing password: preserve
    it as a port/path. Unambiguous digits-only userinfo (u:123@host) is redacted.
    Raw ? and # in passwords remain outside the slash-password fallback;
    RFC 3986 requires encoding them as data in userinfo.
    """
    parts = []
    cursor = 0
    for match in _URL_RE.finditer(text):
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
    raw = match.group()
    authority_start = raw.index("://") + 3
    # RFC 3986 section 3.2: /, ? and # terminate the authority.
    authority_end = min(
        (index for delimiter in "/?#" if (index := raw.find(delimiter, authority_start)) >= 0),
        default=len(raw),
    )
    prefix = raw[authority_start:authority_end]
    # Diagnostic-only accommodation for unescaped base64 / in a password.
    # A numeric port followed by / must never turn an @path into userinfo.
    if ":" in prefix and "@" not in prefix and not prefix.rsplit(":", 1)[1].isdigit():
        userinfo_limit = min(
            (index for delimiter in "?#" if (index := raw.find(delimiter, authority_start)) >= 0),
            default=len(raw),
        )
        userinfo_end = raw.rfind("@", authority_start, userinfo_limit)
        if userinfo_end >= 0:
            authority_end = min(
                (index for delimiter in "/?#" if (index := raw.find(delimiter, userinfo_end + 1)) >= 0),
                default=len(raw),
            )
    rewritten = raw
    fragment_start = raw.find("#", authority_end)
    query_end = fragment_start if fragment_start >= 0 else len(raw)
    query_marker = raw.find("?", authority_end, query_end)
    if query_marker >= 0:
        query_start = query_marker + 1
        query = _QUERY_PARAMETER_RE.sub(_redact_query_match, raw[query_start:query_end])
        rewritten = raw[:query_start] + query + raw[query_end:]
    userinfo, separator, host = raw[authority_start:authority_end].rpartition("@")
    authority = "[redacted-host]"
    if host.startswith("[redacted-ip]") or any(f.kind in {"ipv4", "ipv6"} for f in scan_text(host)):
        authority = "[redacted-ip]"
    if separator:
        username, colon, _password = userinfo.partition(":")
        credentials = username + ":" + REDACTION if colon else username
        authority = credentials + "@" + authority
    return rewritten[:authority_start] + authority + rewritten[authority_end:]


def _redact_query_match(match: re.Match[str]) -> str:
    key = unquote_plus(match.group("key"))
    if (
        key.lower() in {"sig", "signature", "x-amz-signature", "x-goog-signature"}
        or redact_value({key: ""})[key] == REDACTION
    ):
        return match.group("prefix") + REDACTION
    return match.group()
