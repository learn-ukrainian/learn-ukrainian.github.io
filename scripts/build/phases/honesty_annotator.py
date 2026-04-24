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


def _distinct_matches(line_body: str) -> list[str]:
    found = []
    for pattern in (_PERCENT_RE, _LINGUISTIC_UNIT_RE):
        found.extend((match.start(), match.group(0)) for match in pattern.finditer(line_body))

    matches: list[str] = []
    seen: set[str] = set()
    for _, value in sorted(found, key=lambda item: item[0]):
        if value in seen:
            continue
        seen.add(value)
        matches.append(value)
    return matches


def _marker_for(matches: list[str]) -> str:
    preview = "; ".join(matches[:3])[:80]
    return f" <!-- VERIFY: precise claim ({preview}) -->"


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

        marker = _marker_for(matches)
        annotated_lines.append(f"{line_body}{marker}{line_ending}")
        annotation_log.append(
            {
                "line_num": line_num,
                "line": line_body,
                "matches": matches,
                "marker": marker,
            }
        )

    return "".join(annotated_lines), annotation_log
