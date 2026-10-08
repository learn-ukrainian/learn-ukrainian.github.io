"""Lightweight shared Markdown verdict-line scanner (#9756).

Extracted from dispatch's proven scanner; consumer decision policies stay local.
"""

from __future__ import annotations

import re
from collections.abc import Iterator

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
_REVIEW_VERDICT_LINE_RE = re.compile(
    r"^ {0,3}(?:#{1,6} +)?(?:[*_][*_\s]*)?VERDICT[*_`\s]*:[*_`\s]*"
    r"(APPROVED?|CHANGES_REQUESTED|REQUEST_CHANGES|BLOCKED)"
    r"(?![^\W_]|_+[^\W_])",
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
    container parser. Safety consumers validate container context separately.
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
    input where a block was removed. Dispatch/DoR retain container spans:
    a list item can end its fence before a later item's apparent closer.
    """
    raw_lines = text.splitlines(keepends=True)
    lines = text.splitlines()
    container_spans: list[list[int]] = []
    if keep_unclosed:
        # Existing CommonMark dependency supplies container boundaries only;
        # the shared lexical scanner and verdict policy remain unchanged.
        # Import locally so verdict-only consumers stay lightweight.
        from markdown_it import MarkdownIt

        container_spans = [
            token.map for token in MarkdownIt("commonmark").parse("\n".join(lines))
            if token.type in {"list_item_open", "blockquote_open"} and token.map is not None
        ]
    parts: list[str] = []
    cursor = 0
    for start, end, closed in _code_fence_spans(lines):
        if keep_unclosed and (not closed or any(lo <= start < hi for lo, hi in container_spans)):
            continue
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
