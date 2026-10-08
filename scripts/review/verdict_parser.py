"""Lightweight shared Markdown verdict-line scanner (#9756).

Extracted from dispatch's proven scanner; consumer decision policies stay local.
"""

from __future__ import annotations

import re
from collections.abc import Iterator

ACCEPTED_VERDICT_TOKENS = (
    "APPROVE",
    "APPROVED",
    "CHANGES_REQUESTED",
    "REQUEST_CHANGES",
    "BLOCKED",
)

# Verdict vocabulary mirrors the live review parsers — no third vocabulary
# (#8421): APPROVE is accepted by scripts/build/cf_preflight.py, and
# APPROVED / CHANGES_REQUESTED / BLOCKED by
# scripts/fleet_comms/review_publication.py (and formerly
# scripts/ai_agent_bridge/_review_verdict.py, removed in #8520). REQUEST_CHANGES is the token
# cf_preflight.py and the review prompts actually ask reviewers to write.
# Reviewers routinely render the label and token in Markdown emphasis
# (``**Verdict**: **APPROVE**``, ``VERDICT: **REQUEST_CHANGES**``); those are
# full verdicts and must not be misread as missing (#8786). A verdict line
# STARTS with the label: optional emphasis (``*``, ``_``), ``VERDICT``, then
# emphasis/backticks/whitespace around its colon, then the token and a word
# boundary. Anything may follow the token — reviewers write
# ``**VERDICT: APPROVE.** Both issues are fixed.`` and
# ``**VERDICT: APPROVE** (three non-blocking findings below)``. An inline or
# quoted example ("I will report ``VERDICT: APPROVE`` later",
# ``> VERDICT: APPROVE``) does not start with the label, so is not a verdict.
# The boundary treats ``_`` as emphasis (``__APPROVE__``) unless a letter or
# digit follows it (``APPROVE_LATER``), so ``APPROVEX`` is not a verdict.
# Indentation follows CommonMark: at most three leading spaces; four or more,
# or a tab, make the line an indented code block, i.e. an example.
# After that indentation an ATX heading marker (``#`` to ``######`` plus at
# least one space) may precede the label, so ``## VERDICT: REQUEST_CHANGES``
# and ``# **VERDICT: APPROVE**`` are verdicts (#9305). ``##VERDICT: APPROVE``
# has no space, which CommonMark does not treat as a heading, and
# ``## The VERDICT: APPROVE`` does not start with the label; neither counts.
_VERDICT_LINE_PREFIX = r"^ {0,3}(?:#{1,6} +)?(?:[*_][*_\s]*)?VERDICT[*_`\s]*:[*_`\s]*"
_REVIEW_VERDICT_LINE_RE = re.compile(
    _VERDICT_LINE_PREFIX + r"(APPROVED?|CHANGES_REQUESTED|REQUEST_CHANGES|BLOCKED)"
    r"(?![^\W_]|_+[^\W_])",
    re.IGNORECASE,
)
# Diagnostics echo only bounded ASCII identifier tokens, never paths, URLs or
# arbitrary verdict-line text. Trailing underscores may be Markdown emphasis.
_UNSUPPORTED_VERDICT_LINE_RE = re.compile(
    _VERDICT_LINE_PREFIX + r"(?a:([A-Za-z][A-Za-z0-9]*(?:[_-]+[A-Za-z0-9]+)*))"
    r"(?=$|[*_`]*(?:\s|[.,;:!?][*_`]*(?:\s|$)|$))",
    re.IGNORECASE,
)
# A CommonMark fence line: at most three leading spaces, then three or more
# backticks or tildes; group 2 is the rest of the line (info string).
_CODE_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


def _code_fence_opener(line: str) -> str | None:
    """Return the fence run when ``line`` opens a CommonMark code fence.

    A backtick fence's info string may not contain a backtick (that line is
    inline code, not a fence).
    """
    match = _CODE_FENCE_RE.match(line)
    if match is None:
        return None
    fence, info = match.groups()
    if fence[0] == "`" and "`" in info:
        return None
    return fence


def _closes_code_fence(line: str, opener: str) -> bool:
    """Return whether ``line`` closes the fence opened by ``opener``.

    Per CommonMark the closer uses the opener's character, is at least as
    long, and carries nothing but trailing spaces or tabs; any other line —
    including a fence of the other character — is block content.
    """
    match = _CODE_FENCE_RE.match(line)
    if match is None:
        return False
    fence, rest = match.groups()
    return fence[0] == opener[0] and len(fence) >= len(opener) and not rest.strip(" \t")


def _own_verdict_lines(response: str) -> Iterator[str]:
    """Yield non-code lines for both token readers using the same exclusions."""
    open_fence: str | None = None
    for line in response.splitlines():
        if open_fence is not None:
            if _closes_code_fence(line, open_fence):
                open_fence = None
            continue
        open_fence = _code_fence_opener(line)
        if open_fence is not None:
            continue
        yield line


def recognized_verdicts(response: str) -> list[str]:
    """Return recognized verdict tokens in order, excluding code and examples.

    Selection and normalization belong to consumers. An unclosed CommonMark
    fence suppresses the rest of the response.
    """
    return [
        match.group(1).upper()
        for line in _own_verdict_lines(response)
        if (match := _REVIEW_VERDICT_LINE_RE.match(line))
    ]


def unsupported_verdict_tokens(response: str) -> list[str]:
    """Return safe unsupported own tokens verbatim, for diagnostics only.

    Recognized lines keep their existing boundary policy; this reader never
    admits a review or changes a consumer's recognized-token precedence.
    """
    tokens: list[str] = []
    for line in _own_verdict_lines(response):
        if _REVIEW_VERDICT_LINE_RE.match(line):
            continue
        match = _UNSUPPORTED_VERDICT_LINE_RE.match(line)
        if match and len(match.group(1)) <= 64:
            tokens.append(match.group(1))
    return tokens
