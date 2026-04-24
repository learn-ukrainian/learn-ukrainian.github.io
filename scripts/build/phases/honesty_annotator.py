"""Deterministic VERIFY marker insertion for precise prose claims."""

from __future__ import annotations

import re

_PERCENT_RE = re.compile(r"\b\d+(?:[–\-]\d+)?\s*%")
_LINGUISTIC_UNIT_RE = re.compile(
    r"\b\d+\s+"
    r"(?:звук\w*|літер\w*|голосн\w*|приголосн\w*|буков\w*|склад\w*|відмін\w*|"
    r"sound\w*|letter\w*|vowel\w*|consonant\w*|phoneme\w*|syllable\w*|case\w*|gender\w*)\b",
    re.IGNORECASE,
)
_COMMENT_ONLY_RE = re.compile(r"^\s*<!--.*-->\s*$")
_SENTENCE_TERMINATOR_RE = re.compile(r"[.!?]\s+")


def _line_body_and_ending(line: str) -> tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith(("\n", "\r")):
        return line[:-1], line[-1]
    return line, ""


def _is_structural_line(line_body: str) -> bool:
    stripped = line_body.strip()
    if not stripped:
        return True
    lstripped = line_body.lstrip()
    return (
        lstripped.startswith("#")
        or lstripped.startswith(":::")
        or _COMMENT_ONLY_RE.fullmatch(line_body) is not None
    )


def _distinct_matches(line_body: str) -> list[tuple[int, str]]:
    """Return (position, matched_text) tuples for distinct precise-claim matches, sorted by position."""
    found: list[tuple[int, str]] = []
    for pattern in (_PERCENT_RE, _LINGUISTIC_UNIT_RE):
        found.extend((match.start(), match.group(0)) for match in pattern.finditer(line_body))

    results: list[tuple[int, str]] = []
    seen: set[str] = set()
    for pos, value in sorted(found, key=lambda item: item[0]):
        if value in seen:
            continue
        seen.add(value)
        results.append((pos, value))
    return results


def _marker_for(match_values: list[str]) -> str:
    preview = "; ".join(match_values[:3])[:80]
    return f" <!-- VERIFY: precise claim ({preview}) -->"


def _sentence_spans(line_body: str) -> list[tuple[int, int]]:
    """Return [start, end) spans for sentences within line_body.

    A sentence ends at `[.!?]` followed by whitespace; `end` is the position
    just after the terminator character (before the separating whitespace).
    If no terminator is found the whole line is returned as a single span —
    callers treat that as "fall back to end-of-line append."
    """
    spans: list[tuple[int, int]] = []
    cursor = 0
    for match in _SENTENCE_TERMINATOR_RE.finditer(line_body):
        terminator_end = match.start() + 1
        spans.append((cursor, terminator_end))
        cursor = match.end()
    if cursor < len(line_body):
        spans.append((cursor, len(line_body)))
    if not spans:
        spans.append((0, len(line_body)))
    return spans


def _inject_marker(line_body: str, marker: str, first_match_pos: int) -> str:
    """Insert `marker` at the end of the sentence containing `first_match_pos`.

    If the line has no sentence terminator, fall back to end-of-line append —
    preserves the pre-sentence-scoping behavior for single-sentence lines.
    """
    spans = _sentence_spans(line_body)
    if len(spans) == 1:
        return f"{line_body}{marker}"
    target_end = spans[-1][1]
    for _, end in spans:
        if first_match_pos < end:
            target_end = end
            break
    return f"{line_body[:target_end]}{marker}{line_body[target_end:]}"


def annotate_content(content: str) -> tuple[str, list[dict]]:
    """Return content with VERIFY markers appended to precise-claim prose lines."""
    annotated_lines: list[str] = []
    annotation_log: list[dict] = []
    in_fence = False

    for line_num, line in enumerate(content.splitlines(keepends=True), start=1):
        line_body, line_ending = _line_body_and_ending(line)
        if line_body.lstrip().startswith("```"):
            in_fence = not in_fence
            annotated_lines.append(line)
            continue

        if in_fence or _is_structural_line(line_body) or "<!-- VERIFY" in line_body:
            annotated_lines.append(line)
            continue

        matches = _distinct_matches(line_body)
        if not matches:
            annotated_lines.append(line)
            continue

        match_values = [value for _, value in matches]
        first_match_pos = matches[0][0]
        marker = _marker_for(match_values)
        new_line_body = _inject_marker(line_body, marker, first_match_pos)
        annotated_lines.append(f"{new_line_body}{line_ending}")
        annotation_log.append(
            {
                "line_num": line_num,
                "line": line_body,
                "matches": match_values,
                "marker": marker,
            }
        )

    return "".join(annotated_lines), annotation_log
