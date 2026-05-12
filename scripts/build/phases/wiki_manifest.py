"""Extract deterministic wiki obligations for V7 writer/reviewer prompts."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class L2Error:
    id: str
    incorrect: str
    correct: str
    why: str
    treatment: Literal["contrast_pair", "prose_explanation"]
    source_lines: str


@dataclass(frozen=True, slots=True)
class SequenceStep:
    id: str
    heading: str
    step_num: int
    required_claim: str
    source_lines: str


@dataclass(frozen=True, slots=True)
class PhoneticRule:
    id: str
    written: str
    spoken: str
    treatment: Literal["explicit_explanation"]
    source_lines: str


@dataclass(frozen=True, slots=True)
class DecolonizationBan:
    id: str
    rule: str
    source_lines: str


@dataclass(frozen=True, slots=True)
class WikiManifest:
    slug: str
    wiki_path: str
    sequence_steps: list[SequenceStep]
    l2_errors: list[L2Error]
    phonetic_rules: list[PhoneticRule]
    decolonization_bans: list[DecolonizationBan]


_SEQUENCE_HEADING_RE = re.compile(r"^##\s+Послідовність\s+(?:викладання|введення)\b", re.IGNORECASE)
_L2_HEADING_RE = re.compile(r"^##\s+Типові\s+помилки\s+L2\b", re.IGNORECASE)
_BAN_HEADING_RE = re.compile(r"^##\s+Деколонізаційні\s+застереження\b", re.IGNORECASE)
_ANY_H2_RE = re.compile(r"^##\s+\S")
_STEP_RE = re.compile(r"^\s*(?:[-*]\s*)?(?:\*\*)?Крок\s+(?P<num>\d+)\s*[:.]\s*(?P<title>.+?)\s*$")
_META_SLUG_RE = re.compile(r"^\s*slug\s*:\s*(?P<slug>[-\w]+)\s*$", re.MULTILINE)
_IPA_RE = re.compile(r"\[(?![SС]\d)(?=[^\]\n]*(?:[:'ʼ’]|[A-Za-z]))[^\]\n]{1,60}\]")
_WRITTEN_RE = re.compile(r"(?<!\w)(-[\w'’ʼ-]{0,12}ся|-шся|-ться)(?!\w)", re.IGNORECASE)


def extract_manifest(wiki_path: str | Path) -> dict[str, Any]:
    """Extract a JSON-serializable wiki obligations manifest."""
    path = Path(wiki_path)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    slug = _extract_slug(text, path)

    manifest = WikiManifest(
        slug=slug,
        wiki_path=str(path),
        sequence_steps=_extract_sequence_steps(lines),
        l2_errors=_extract_l2_errors(lines),
        phonetic_rules=_extract_phonetic_rules(lines),
        decolonization_bans=_extract_decolonization_bans(lines),
    )
    return asdict(manifest)


def _extract_slug(text: str, path: Path) -> str:
    match = _META_SLUG_RE.search(text)
    return match.group("slug").strip() if match else path.stem


def _section_span(lines: list[str], heading_re: re.Pattern[str]) -> tuple[int, int] | None:
    start = None
    for index, line in enumerate(lines):
        if heading_re.search(line):
            start = index
            break
    if start is None:
        return None
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if _ANY_H2_RE.search(lines[index]):
            end = index
            break
    return start, end


def _line_range(start_index: int, end_index: int) -> str:
    start = start_index + 1
    end = end_index + 1
    return str(start) if start == end else f"{start}-{end}"


def _clean_inline(text: str) -> str:
    text = text.replace("`", "")
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_sequence_steps(lines: list[str]) -> list[SequenceStep]:
    span = _section_span(lines, _SEQUENCE_HEADING_RE)
    if not span:
        return []
    start, end = span
    step_starts: list[tuple[int, re.Match[str]]] = []
    for index in range(start + 1, end):
        match = _STEP_RE.match(lines[index])
        if match:
            step_starts.append((index, match))

    steps: list[SequenceStep] = []
    for seq_index, (line_index, match) in enumerate(step_starts, start=1):
        next_line = step_starts[seq_index][0] if seq_index < len(step_starts) else end
        body = " ".join(line.strip() for line in lines[line_index:next_line] if line.strip())
        body = _clean_inline(body)
        step_num = int(match.group("num"))
        title = _clean_inline(match.group("title"))
        heading = f"Крок {step_num}: {title}"
        steps.append(
            SequenceStep(
                id=f"step-{step_num}",
                heading=heading,
                step_num=step_num,
                required_claim=body,
                source_lines=_line_range(line_index, max(line_index, next_line - 1)),
            )
        )
    return steps


def _parse_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    cells = [cell.strip() for cell in stripped.strip("|").split("|")]
    return [_clean_inline(cell) for cell in cells]


def _is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def _extract_l2_errors(lines: list[str]) -> list[L2Error]:
    span = _section_span(lines, _L2_HEADING_RE)
    if not span:
        return []
    start, end = span
    errors: list[L2Error] = []
    table_started = False
    for index in range(start + 1, end):
        cells = _parse_table_row(lines[index])
        if not cells:
            if table_started:
                break
            continue
        if _is_separator_row(cells):
            table_started = True
            continue
        lowered = " ".join(cells).casefold()
        if "помилково" in lowered and "правильно" in lowered:
            table_started = True
            continue
        table_started = True
        if len(cells) < 3:
            continue
        errors.append(
            L2Error(
                id=f"err-{len(errors) + 1}",
                incorrect=cells[0],
                correct=cells[1],
                why=" | ".join(cells[2:]),
                treatment="contrast_pair",
                source_lines=_line_range(index, index),
            )
        )
    return errors


def _extract_phonetic_rules(lines: list[str]) -> list[PhoneticRule]:
    rules: list[PhoneticRule] = []
    seen: set[tuple[str, str]] = set()
    for index, line in enumerate(lines):
        clean = _clean_inline(line)
        if not clean or not _IPA_RE.search(clean):
            continue
        if "вимов" not in clean.casefold() and not _WRITTEN_RE.search(clean):
            continue
        written = _WRITTEN_RE.findall(clean)
        spoken = _IPA_RE.findall(clean)
        if not written or not spoken:
            continue
        for written_item, spoken_item in zip(written, spoken, strict=False):
            key = (written_item, spoken_item)
            if key in seen:
                continue
            seen.add(key)
            rules.append(
                PhoneticRule(
                    id=f"phon-{len(rules) + 1}",
                    written=written_item,
                    spoken=spoken_item,
                    treatment="explicit_explanation",
                    source_lines=_line_range(index, index),
                )
            )
    return rules


def _extract_decolonization_bans(lines: list[str]) -> list[DecolonizationBan]:
    span = _section_span(lines, _BAN_HEADING_RE)
    if not span:
        return []
    start, end = span
    bans: list[DecolonizationBan] = []
    paragraph_lines: list[str] = []
    paragraph_start = start + 1

    def flush(last_index: int) -> None:
        nonlocal paragraph_lines, paragraph_start
        if not paragraph_lines:
            return
        rule = _clean_inline(" ".join(paragraph_lines))
        if rule:
            bans.append(
                DecolonizationBan(
                    id=f"ban-{len(bans) + 1}",
                    rule=rule,
                    source_lines=_line_range(paragraph_start, last_index),
                )
            )
        paragraph_lines = []

    for index in range(start + 1, end):
        line = lines[index].strip()
        if not line:
            flush(index - 1)
            paragraph_start = index + 1
            continue
        if not paragraph_lines:
            paragraph_start = index
        paragraph_lines.append(line)
    flush(end - 1)
    return bans
