"""Best-effort secret redaction for agent egress paths."""

from __future__ import annotations

import re
from collections.abc import Mapping
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
        rf"(?P<prefix>['\"](?P<key>{_KEY_NAME})['\"]\s*:\s*)(?P<quote>['\"])(?P<value>.*?)(?P=quote)",
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
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bASIA[0-9A-Z]{16}\b"),
    re.compile(
        r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
    ),
)


def redact_text(value: str | None) -> str | None:
    """Redact token-looking substrings from text before external egress."""
    if value is None:
        return None

    text = str(value)
    for pattern in _BLOCK_PATTERNS:
        text = pattern.sub(REDACTION, text)
    for pattern in _ASSIGNMENT_PATTERNS:
        text = pattern.sub(
            _redact_assignment_match,
            text,
        )
    for pattern in _TOKEN_PATTERNS:
        text = pattern.sub(REDACTION, text)
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


def _redact_assignment_match(match: re.Match[str]) -> str:
    if not _is_secret_key(match.group("key")):
        return match.group(0)

    quote = match.groupdict().get("quote") or ""
    return f"{match.group('prefix')}{quote}{REDACTION}{quote}"
