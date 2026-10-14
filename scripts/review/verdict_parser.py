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
# either a colon surrounded by emphasis/backticks/whitespace or at least one
# emphasis/backtick/whitespace separator, then the token and a word boundary
# (#8532). This accepts ``VERDICT APPROVE`` and ``**VERDICT** APPROVE``.
# Anything may follow the token — reviewers write
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
# CommonMark line endings are LF, CR, and CRLF. str.splitlines() also breaks
# on VT, FF, and Unicode separators, which moves fence spans off the real text.
_COMMONMARK_LINE_RE = re.compile(r"\r\n|\r|\n")


def _commonmark_lines(text: str, *, keepends: bool = False) -> list[str]:
    """Split on CommonMark line endings, matching str.splitlines for those three."""
    if text == "":
        return []
    if keepends:
        return _commonmark_keepends(text)
    lines = _COMMONMARK_LINE_RE.split(text)
    if text.endswith(("\n", "\r")) and lines and lines[-1] == "":
        lines.pop()
    return lines


def _commonmark_keepends(text: str) -> list[str]:
    lines: list[str] = []
    cursor = 0
    for match in _COMMONMARK_LINE_RE.finditer(text):
        lines.append(text[cursor : match.end()])
        cursor = match.end()
    if cursor < len(text):
        lines.append(text[cursor:])
    return lines


_VERDICT_LINE_PREFIX = r"^ {0,3}(?:#{1,6} +)?(?:[*_][*_\s]*)?VERDICT[*_`\s]*:[*_`\s]*"
_REVIEW_VERDICT_LINE_RE = re.compile(
    r"^ {0,3}(?:#{1,6} +)?(?:[*_][*_\s]*)?VERDICT"
    r"(?:[*_`\s]*:[*_`\s]*|[*_`\s]+)"
    r"(APPROVED?|CHANGES_REQUESTED|REQUEST_CHANGES|BLOCKED)"
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


def _code_fence_spans(lines: list[str]) -> Iterator[tuple[int, int, bool]]:
    """Yield (start, exclusive end, closed) line spans using CommonMark §4.5.

    https://spec.commonmark.org/0.31.2/#fenced-code-blocks
    This is a lexical scan of fence lines with 0–3 leading spaces, not a
    container parser. Dispatch/DoR instead use CommonMark token maps directly.
    The explicit closed flag lets callers choose their unclosed-body policy.
    """
    open_fence: str | None = None
    start = 0
    for index, line in enumerate(lines):
        if open_fence is not None:
            if _closes_code_fence(line, open_fence):
                yield start, index + 1, True
                open_fence = None
            continue
        open_fence = _code_fence_opener(line)
        if open_fence is not None:
            start = index
    if open_fence is not None:
        yield start, len(lines), False


def _without_code_fences(text: str, *, keep_unclosed: bool) -> str:
    """Remove fenced spans, retaining unterminated bodies when requested.

    Keep non-fenced text verbatim and leave a paragraph boundary for LF/CRLF
    input where a block was removed. Dispatch/DoR remove only closed top-level
    CommonMark tokens: a container can end a fence without a lexical closer.
    """
    raw_lines = _commonmark_lines(text, keepends=True)
    lines = _commonmark_lines(text)
    spans: list[tuple[int, int]] = []
    if keep_unclosed:
        # Use one parser for both context and spans; lexical state can drift
        # across container exits. Import/parse failures propagate before effects.
        # Import locally so verdict-only consumers retain their lexical policy.
        from markdown_it import MarkdownIt

        for token in MarkdownIt("commonmark").parse("\n".join(lines)):
            if token.type != "fence" or token.level != 0:
                continue
            source_map = token.map
            if not isinstance(source_map, (list, tuple)) or len(source_map) != 2:
                continue
            start, end = source_map
            if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(lines):
                continue
            # Maps also describe EOF/container-terminated fences. A separate
            # source closer, of the opener's marker and length, proves closure.
            if end - 1 > start and _closes_code_fence(lines[end - 1], token.markup):
                spans.append((start, end))
    else:
        spans = [(start, end) for start, end, _closed in _code_fence_spans(lines)]
    parts: list[str] = []
    cursor = 0
    for start, end in spans:
        parts.extend(raw_lines[cursor:start])
        parts.append("\n")
        cursor = end
    parts.extend(raw_lines[cursor:])
    return "".join(parts)


def recognized_verdicts(response: str) -> list[str]:
    """Return recognized verdict tokens in order, excluding code and examples.

    Selection and normalization belong to consumers. An unclosed CommonMark
    fence suppresses the rest of the response.
    """
    verdicts: list[str] = []
    for line in _without_code_fences(response, keep_unclosed=False).splitlines():
        match = _REVIEW_VERDICT_LINE_RE.match(line)
        if match:
            verdicts.append(match.group(1).upper())
    return verdicts


def unsupported_verdict_tokens(response: str) -> list[str]:
    """Return safe unsupported own tokens verbatim, for diagnostics only.

    Recognized lines keep their existing boundary policy; this reader never
    admits a review or changes a consumer's recognized-token precedence.
    """
    tokens: list[str] = []
    for line in _without_code_fences(response, keep_unclosed=False).splitlines():
        if _REVIEW_VERDICT_LINE_RE.match(line):
            continue
        match = _UNSUPPORTED_VERDICT_LINE_RE.match(line)
        if match and len(match.group(1)) <= 64:
            tokens.append(match.group(1))
    return tokens
