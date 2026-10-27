"""Read-only write-intent admission: a write-shaped brief cannot run with ``--mode read-only``.

Mechanical copy of ``scripts/delegate.py`` ``_read_only_write_intent_error`` and its helpers
(#8703, #7814, #9672; C-2188 unit D). The CLI checks the brief as given, before any side effect.
"""

import re

from scripts.review.verdict_parser import _without_code_fences

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
        "Re-run with --mode workspace-write --worktree for repository edits "
        "(or --mode danger --worktree only when its extra permissions are required)."
    )
