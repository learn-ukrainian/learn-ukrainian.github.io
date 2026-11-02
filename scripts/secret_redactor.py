"""Best-effort secret redaction for agent egress paths.

Values assigned to recognized secret names are always redacted, including YAML
pairs and spaced code expressions. Punctuation cannot establish that a value
is safe to publish.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Iterator, Mapping
from itertools import pairwise
from typing import Any

REDACTION = "[REDACTED_SECRET]"

_KEY_NAME = r"[A-Za-z_][A-Za-z0-9_]*"

_ASSIGNMENT_PATTERNS = (
    re.compile(
        rf"(?P<prefix>\b(?P<key>{_KEY_NAME})\b\s*=\s*)(?P<quote>['\"])(?P<value>.*?)(?P=quote)",
        re.IGNORECASE,
    ),
    re.compile(
        rf"(?P<prefix>\b(?P<key>{_KEY_NAME})\b\s*=\s*)(?P<value>[^\r\n]+)",
        re.IGNORECASE,
    ),
    re.compile(
        rf"(?P<prefix>(?<![\w'\"])(?P<key_quote>['\"]?)(?P<key>{_KEY_NAME})(?P=key_quote)\s*:\s*)(?P<quote>\")(?P<value>(?:\\[^\r\n]|[^\"\\\r\n])*)(?P=quote)",
        re.IGNORECASE,
    ),
    re.compile(
        rf"(?P<prefix>(?<![\w'\"])(?P<key_quote>['\"]?)(?P<key>{_KEY_NAME})(?P=key_quote)\s*:\s*)(?P<quote>')(?P<value>(?:''|[^'\r\n])*)(?P=quote)",
        re.IGNORECASE,
    ),
    re.compile(
        rf"(?P<prefix>(?<![\w'\"])(?P<key_quote>['\"]?)(?P<key>{_KEY_NAME})(?P=key_quote)\s*:\s*)(?P<value>[^'\"\s\r\n][^\r\n]*)",
        re.IGNORECASE,
    ),
)

_BLOCK_PATTERNS = (
    re.compile(
        r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----",
        re.DOTALL,
    ),
)

_TOKEN_PATTERNS = (
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\b(?:key_[0-9A-Fa-f]{64}|crsr_[A-Za-z0-9]{40,})\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bASIA[0-9A-Z]{16}\b"),
    re.compile(
        r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
    ),
)

# A non-vendor secret can appear inside an OAuth/provider error message without
# a secret-named key. Restrict the generic detector to long ASCII token runs so
# natural-language prose is not treated as a credential. Punctuated candidates
# need substantially more entropy because prose commonly has dates, versions,
# and hyphenated title case; unpunctuated alphanumeric/letter-only candidates
# have separate thresholds for their narrower alphabets.
_OPAQUE_TOKEN_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_+./~=-])(?P<value>[A-Za-z0-9_+./~-]{32,})(?:={1,2})?"
    r"(?![A-Za-z0-9_+./~=-])"
)
_OPAQUE_TOKEN_MIN_ENTROPY = 3.5
_OPAQUE_ALPHA_TOKEN_MIN_ENTROPY = 4.0
_OPAQUE_PUNCTUATED_TOKEN_MIN_ENTROPY = 4.5
_OPAQUE_TOKEN_PUNCTUATION = frozenset("_+./~-")

_URL_SCHEME = r"\b[A-Za-z][A-Za-z0-9+.-]*://"
# First bound the whole token; URL boundaries within it depend on userinfo.
URL_PATTERN = re.compile(rf"{_URL_SCHEME}[^\s<>\"`]*")
_URL_BOUNDARY_PATTERN = re.compile(rf"[,;]?(?P<scheme>{_URL_SCHEME})")
# RFC 3986 unreserved, sub-delims and pct-encoded, excluding the password colon.
_URL_USERNAME_PATTERN = re.compile(r"(?:[A-Za-z0-9._~!$&'()*+,;=-]|%[0-9A-Fa-f]{2})*")


def _url_authority_bounds(raw: str) -> tuple[int, int]:
    """Resolve authority, including the guarded malformed-userinfo fallback."""
    start = raw.index("://") + 3
    end = min(
        (index for delimiter in "/?#" if (index := raw.find(delimiter, start)) >= 0),
        default=len(raw),
    )
    if "@" not in raw[start:end]:
        username, colon, password_prefix = raw[start:end].partition(":")
        if (
            colon
            and _URL_USERNAME_PATTERN.fullmatch(username)
            and password_prefix
            and not password_prefix.isdigit()
        ):
            userinfo_end = raw.find("@", end)
            if userinfo_end >= 0:
                end = min(
                    (index for delimiter in "/?#" if (index := raw.find(delimiter, userinfo_end + 1)) >= 0),
                    default=len(raw),
                )
    return start, end


def iter_url_matches(text: str) -> Iterator[re.Match[str]]:
    """Split token URLs only after resolving the current URL's userinfo.

    A scheme inside a password cannot become a new URL. Comma/semicolon
    joiners after resolved userinfo remain outside matches, as in round b.
    """
    for token in URL_PATTERN.finditer(text):
        cursor = token.start()
        while cursor < token.end():
            raw = text[cursor:token.end()]
            start, end = _url_authority_bounds(raw)
            userinfo_end = raw.rfind("@", start, end)
            boundary = _URL_BOUNDARY_PATTERN.search(text, cursor + max(start, userinfo_end + 1), token.end())
            limit = boundary.start() if boundary else token.end()
            yield URL_PATTERN.match(text, cursor, limit)
            if boundary is None:
                break
            cursor = boundary.start("scheme")


def redact_url_authority(raw: str) -> tuple[str, str, str]:
    """Split a scheme:// URL token into prefix, redacted authority and suffix.

    RFC 3986 section 3.2 ends authority at the first /, ? or #. Only an @
    within that authority normally identifies userinfo; replace everything
    after its first colon up to @, preserving username, host and suffix bytes.

    Diagnostics also contain malformed passwords with raw /, ? or #. If the
    initial authority has no @, accept the first later @ in this same token
    only when the initial authority starts with an RFC username and colon,
    followed by a nonempty, nonnumeric password prefix. Extend authority to
    the first /, ? or # after that @. Numeric and empty prefixes stay ports:
    ordinary host:port URLs cannot trigger this fallback, even with @ in a
    path, query or fragment. Bracketed IP hosts cannot match the username.

    Deliberately leave ambiguous numeric/empty prefixes before a delimiter,
    username-only userinfo, schemeless credentials and tokens without @ alone.
    The shared iterator resolves userinfo before bounding at a later scheme.
    No decoding or normalization occurs.
    """
    start, end = _url_authority_bounds(raw)
    authority = raw[start:end]
    userinfo, separator, host = authority.rpartition("@")
    if separator:
        username, colon, _password = userinfo.partition(":")
        if colon:
            authority = username + ":" + REDACTION + "@" + host
    return raw[:start], authority, raw[end:]


def redact_text(value: str | None) -> str | None:
    """Redact token-looking substrings from text before external egress."""
    if value is None:
        return None

    text = str(value)
    parts = []
    cursor = 0
    for match in iter_url_matches(text):
        parts.append(text[cursor:match.start()])
        parts.extend(redact_url_authority(match.group()))
        cursor = match.end()
    parts.append(text[cursor:])
    text = "".join(parts)
    for pattern in _BLOCK_PATTERNS:
        text = pattern.sub(REDACTION, text)
    for pattern in _ASSIGNMENT_PATTERNS:
        text = pattern.sub(
            _redact_assignment_match,
            text,
        )
    for pattern in _TOKEN_PATTERNS:
        text = pattern.sub(REDACTION, text)
    text = _OPAQUE_TOKEN_PATTERN.sub(_redact_opaque_token_match, text)
    return text


def redact_value(value: Any) -> Any:
    """Recursively redact strings inside JSON-like values."""
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, Mapping):
        return {
            key: REDACTION if _is_secret_key(str(key)) else redact_value(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_value(item) for item in value)
    return value


def _is_secret_key(key: str) -> bool:
    parts = [part for part in re.split(r"[^A-Z0-9]+", key.upper()) if part]
    if not parts:
        return False

    if any(part in {"TOKEN", "SECRET", "PASSWORD", "CREDENTIAL", "CREDENTIALS"} for part in parts):
        return True
    if "PASS" in parts:
        return True

    pairs = set(pairwise(parts))
    if ("PRIVATE", "KEY") in pairs or ("ACCESS", "KEY") in pairs:
        return True
    if len(parts) >= 2 and parts[-2:] == ["API", "KEY"]:
        return True
    return bool(parts and parts[-1] == "APIKEY")


def _shannon_entropy(value: str) -> float:
    """Return the per-character Shannon entropy for an ASCII token candidate."""
    length = len(value)
    return -sum(
        (count / length) * math.log2(count / length)
        for count in Counter(value).values()
    )


def _looks_like_opaque_secret(value: str) -> bool:
    """True for a high-entropy opaque token rather than ordinary prose."""
    if not any(char.isalpha() for char in value):
        return False

    entropy = _shannon_entropy(value)
    if _OPAQUE_TOKEN_PUNCTUATION.intersection(value):
        return entropy >= _OPAQUE_PUNCTUATED_TOKEN_MIN_ENTROPY
    if not any(char.isdigit() for char in value):
        return entropy >= _OPAQUE_ALPHA_TOKEN_MIN_ENTROPY
    return entropy >= _OPAQUE_TOKEN_MIN_ENTROPY


def _redact_opaque_token_match(match: re.Match[str]) -> str:
    """Redact only generic candidates that satisfy the entropy detector."""
    return REDACTION if _looks_like_opaque_secret(match.group("value")) else match.group(0)


def _redact_assignment_match(match: re.Match[str]) -> str:
    if not _is_secret_key(match.group("key")):
        return match.group(0)

    quote = match.groupdict().get("quote") or ""
    return f"{match.group('prefix')}{quote}{REDACTION}{quote}"
