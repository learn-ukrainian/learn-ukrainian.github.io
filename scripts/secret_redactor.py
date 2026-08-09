"""Best-effort secret redaction for agent egress paths.

This is a security control, so the unquoted-assignment gate fails CLOSED: a
secret-named key is redacted unless the value is *unambiguously* a code
expression. The only pass-through is a *spaced* assignment (``key = value``,
code / INI style) whose value carries call/subscript/collection punctuation
(``( ) [ ] { }`` or a comma) — exactly what corrupted reviewed diffs in the
2026-07-12 burn (function calls, comprehensions, set/list literals). A *tight*
assignment (``KEY=value`` with no whitespace around ``=`` — env / shell / .env /
docker-compose style) is ALWAYS redacted, because env dumps are the canonical
place real secrets leak and are virtually never PEP8-spaced.

Two accepted, deliberate gaps (both err toward NOT leaking secrets):

- Spaced bare identifiers / dotted refs assigned to a secret-named key
  (``token_fn = vesum_gate.check_tokens``) stay REDACTED — they lack code
  punctuation, so they fail closed. A rare mangled code line is acceptable; a
  leaked secret is not.
- Spaced INI-style secret values (``password = hunter2``) are redacted. That is
  the correct side of the trade for a security control.

Quoted (``key = 'secret'``) and JSON (``{"key": "secret"}``) forms are always
covered, unconditionally.
"""

from __future__ import annotations

import math
import re
from collections import Counter
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

# Code-shape VETO for the UNQUOTED assignment pattern only. `_ASSIGNMENT_PATTERNS[1]`
# matches any `key = <rest of line>`, so a secret-*named* LHS identifier
# (token_verdicts, secret_keys, ...) used to nuke a benign RHS such as
# `vesum_gate.check_tokens(sentence)` or `[t for t in words if len(t) > 1]`,
# corrupting reviewed diffs and producing bogus "blocking" review findings
# (2026-07-12 burn). We do NOT allowlist secret-*shaped* values — that under-
# redacted real env secrets carrying `@`, `$`, `!`, or trailing comments (the
# PR #5047 regression). Instead we redact by default and veto only a *spaced*
# assignment whose value carries these call/subscript/collection characters,
# which is exactly what function calls, comprehensions, and set/list/dict
# literals — and virtually no env-dump secret value — contain.
_CODE_EXPRESSION_CHARS = frozenset("()[]{},")

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


def _is_code_expression(value: str) -> bool:
    """True when an unquoted RHS carries call/subscript/collection punctuation."""
    return any(char in _CODE_EXPRESSION_CHARS for char in value)


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
    if not quote:
        # Unquoted assignment. Read the spacing around `=` off the prefix group,
        # which captured `key\s*=\s*` — no line re-scan needed. A tight `KEY=value`
        # (no surrounding whitespace) is env / shell / .env / compose style and is
        # ALWAYS redacted. A spaced `key = value` is code / INI style: redact by
        # default, veto only when the value is unambiguously a code expression.
        spaced = bool(re.search(r"\s", match.group("prefix")))
        if spaced and _is_code_expression(match.group("value")):
            return match.group(0)

    return f"{match.group('prefix')}{quote}{REDACTION}{quote}"
