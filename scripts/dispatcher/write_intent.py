"""Read-only write-intent admission: a write-shaped brief cannot run with ``--mode read-only``.

The CLI checks the brief as given, before any side effect
(#8703, #7814, #9672; C-2188 unit D).
The fence scan (``_without_code_fences`` and its line/fence helpers) is copied unchanged from
``scripts/review/verdict_parser.py``, so dispatch admission does not import the review gate's
verdict module. A parser import or parse failure still propagates and refuses the dispatch.
"""

import re

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


# A CommonMark fence line: at most three leading spaces, then three or more
# backticks or tildes; group 2 is the rest of the line (info string).
_CODE_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


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


def _without_code_fences(text: str, *, keep_unclosed: bool) -> str:
    """Remove fenced spans, retaining unterminated bodies when requested.

    Keep non-fenced text verbatim and leave a paragraph boundary for LF/CRLF
    input where a block was removed. Dispatch/DoR remove only closed top-level
    CommonMark tokens: a container can end a fence without a lexical closer.
    """
    raw_lines = _commonmark_lines(text, keepends=True)
    lines = _commonmark_lines(text)
    spans: list[tuple[int, int]] = []
    # CommonMark fences end at their container boundary. Blockquote maps also
    # include lazy continuations whose source lines have no quote marker.
    # Import/parse failures propagate before either consumer can admit a review.
    from markdown_it import MarkdownIt

    parser = MarkdownIt("commonmark")
    for token in parser.parse("\n".join(lines)):
        # These containers recurse after push() increments the open token's
        # level. At maxNesting, tokenize() silently skips its remaining input;
        # outer maps can still cover every line, so they cannot prove visibility.
        if token.type in {"list_item_open", "blockquote_open"} and token.level + 1 >= parser.options["maxNesting"]:
            raise ValueError("CommonMark verdict visibility nesting limit reached")
        if keep_unclosed:
            if token.type != "fence" or token.level != 0:
                continue
        elif token.type not in {"fence", "code_block", "blockquote_open"}:
            continue
        source_map = token.map
        if not isinstance(source_map, (list, tuple)) or len(source_map) != 2:
            if keep_unclosed:
                continue
            raise ValueError("CommonMark verdict visibility map unavailable")
        start, end = source_map
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(lines):
            if keep_unclosed:
                continue
            raise ValueError("CommonMark verdict visibility map invalid")
        # Dispatch/DoR still require a source closer for top-level data removal.
        # Verdict examples include EOF/container-terminated fences and quotes.
        if not keep_unclosed or (end - 1 > start and _closes_code_fence(lines[end - 1], token.markup)):
            spans.append((start, end))
    parts: list[str] = []
    cursor = 0
    for start, end in sorted(spans):
        if end <= cursor:
            continue
        parts.extend(raw_lines[cursor:start])
        parts.append("\n")
        cursor = end
    parts.extend(raw_lines[cursor:])
    return "".join(parts)


# This is deliberately a narrow, directive-only check.  It catches briefs
# whose first-order outcome is a repository mutation without treating an
# ordinary read-only discussion of a proposed change as write intent.
_WRITE_SHAPED_PROMPT_RE = re.compile(
    r"""(?imx)
    ^\s*(?P<prefix>[-*+]\s+|\d+[.)]\s+|\#{1,6}\s+)?(?:please\s+)?
    (?:
        (?:implement|fix|add|update|modify|edit|remove|delete|refactor|rename|create|build)\b
        |
        write\s+(?:(?:new|the)\s+)?(?:code|tests?|scripts?|files?|documentation|docs?)\b
    )
    """,
)
_BLOCKQUOTE_LINE_RE = re.compile(r"^\s*>.*$", re.MULTILINE)
_HEADING_BOUNDARY_RE = re.compile(r"^\s*\#{1,6}\s+")
_LIST_BOUNDARY_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)")
_THEMATIC_BREAK_RE = re.compile(r"^\s*[-*_]{3,}\s*$")


def _strip_quoted_content(prompt: str) -> str:
    """Drop closed fences and Markdown blockquotes before write-intent and DoR scans.

    A critique dispatch attaches or includes the brief under review, and that
    brief legitimately contains write-shaped lines ("Add a CLI …").  Quoted
    content is data for the worker to critique, not a directive to mutate the
    repository, so it must not trip the read-only gate (#7814 item 6).
    Unterminated bodies and nested-container fences remain visible to both
    safety checks; only parser-mapped, source-closed top-level fences are
    removed (#9672), so a container exit cannot hide a later directive.
    """
    without_fences = _without_code_fences(prompt, keep_unclosed=True)
    return _BLOCKQUOTE_LINE_RE.sub("", without_fences)


def _is_write_directive(line: str, prev_non_empty: str | None) -> bool:
    """Classify whether a line in a prompt is a write directive (#8703).

    A line is a directive only if:
    1. It matches the write verb action pattern.
    2. It does not end in '?' (which indicates a question to the reviewer).
    3. It starts a sentence:
       - The line itself is a numbered/bulleted item or heading; OR
       - The previous non-empty line is absent (e.g. first line of the prompt); OR
       - The previous non-empty line ends in '.', ':', '!', '?'; OR
       - The previous non-empty line is a list item or heading boundary.
    A line that continues the previous line's sentence is prose, not a directive.
    """
    match = _WRITE_SHAPED_PROMPT_RE.match(line)
    if not match:
        return False

    # A line ending in '?' is a question to the reviewer, not a directive.
    stripped = line.rstrip()
    if stripped.endswith("?") or stripped.rstrip("\"'`").endswith("?"):
        return False

    # A numbered or bulleted item (or heading) starting with a write verb is a directive.
    if match.group("prefix"):
        return True

    # Continuation rule: a line without a list/heading prefix is a directive
    # only if it starts a sentence (the previous non-empty line is absent,
    # ends in '.', ':', '!', '?', or is a list item / heading boundary).
    # A line that continues the previous line's sentence is prose, not a directive.
    if prev_non_empty is None:
        return True

    prev_stripped = prev_non_empty.rstrip()
    if prev_stripped.rstrip("\"')`").endswith((".", ":", "!", "?")):
        return True

    if _HEADING_BOUNDARY_RE.match(prev_stripped) or _THEMATIC_BREAK_RE.match(prev_stripped):
        return True

    if _LIST_BOUNDARY_RE.match(prev_stripped):
        # Indented line under an unpunctuated list item continues that item's sentence
        is_indented_continuation = line.startswith(("  ", "\t")) and not prev_stripped.rstrip("\"')`").endswith(
            (".", ":", "!", "?")
        )
        return not is_indented_continuation

    return False


def _has_write_directive(prompt: str) -> bool:
    """Scan stripped prompt lines for an unquoted write directive (#8703)."""
    stripped_prompt = _strip_quoted_content(prompt)
    prev_non_empty: str | None = None
    for line in stripped_prompt.splitlines():
        if not line.strip():
            prev_non_empty = None
            continue
        if _is_write_directive(line, prev_non_empty):
            return True
        prev_non_empty = line
    return False


def _read_only_write_intent_error(*, mode: str, prompt: str) -> str | None:
    """Reject clearly write-shaped briefs before a read-only worker starts.

    ``read-only`` remains the default for genuine review and investigation
    work.  A directive to change repository content, however, cannot produce
    its requested deliverable in that mode and must fail before it can look
    like a successful no-op.  The conservative expression intentionally
    requires an instruction-shaped line, rather than matching incidental
    words such as "changes" in a review prompt.  Fenced blocks and blockquote
    lines are excluded from the scan: they carry the brief under critique,
    not the worker's own instructions.  Wrapped continuation prose and
    review questions ending in '?' are not classified as directives (#8703).
    """
    if mode != "read-only":
        return None
    if not _has_write_directive(prompt):
        return None
    return (
        "❌ write-shaped prompt cannot run with --mode read-only. "
        "Re-run with --mode workspace-write --worktree for repository edits."
    )
