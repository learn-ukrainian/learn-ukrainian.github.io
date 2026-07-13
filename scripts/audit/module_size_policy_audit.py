#!/usr/bin/env python3
"""Measure evidence-led module size and deterministic anti-bloat signals.

Plan floors remain binding. Advisory ceilings describe review pressure, while
Markdown-aware authored/quoted counts and paragraph repetition evidence make
the policy useful across core and seminar tracks without treating raw markup as
instructional prose.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
RESEARCH_ROOT = PROJECT_ROOT / "docs" / "research"

CORE_TRACKS = {"a1", "a2", "b1", "b2", "c1", "c2"}
SEMINAR_TRACKS = {
    "bio",
    "folk",
    "hist",
    "history",
    "istorio",
    "lit",
    "lit-crimea",
    "lit-doc",
    "lit-drama",
    "lit-essay",
    "lit-fantastika",
    "lit-hist-fic",
    "lit-humor",
    "lit-war",
    "lit-youth",
    "oes",
    "ruth",
}
CORE_RESEARCH_TRACKS = CORE_TRACKS

MODULE_SIZE_BANDS: dict[str, tuple[int, int | None]] = {
    "sparse": (3800, 5000),
    "normal": (5000, 6500),
    "dense": (6500, 8000),
    "exceptional": (8000, None),
}

_URL_RE = re.compile(r"https?://[^\s)>\"]+")
_MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_MD_INLINE_LINK_RE = re.compile(
    r"!?\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)"
)
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+", re.MULTILINE)
_WORD_RE = re.compile(r"\S+")
_LEXICAL_WORD_RE = re.compile(r"[^\W_]+(?:[’'ʼ:-][^\W_]+)*", re.UNICODE)
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_HTML_TAG_RE = re.compile(r"</?[A-Za-z][^>]*>")
_COMPONENT_EXPRESSION_RE = re.compile(r"\{(?:[^{}]|\{[^{}]*\})*\}")
_DIRECTIVE_OPEN_RE = re.compile(r"^\s*:{3,}\s*([a-z][a-z0-9-]*)\b", re.IGNORECASE)
_DIRECTIVE_CLOSE_RE = re.compile(r"^\s*:{3,}\s*$")
_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
_HEADING_LINE_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*)$")
_LIST_LINE_RE = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+")
_ACTIVITY_HEADING_RE = re.compile(
    r"^(?:activities|activity|exercises|exercise|workbook|"
    r"вправи|вправа|завдання|самоперевірка|робочий зошит)$",
    re.IGNORECASE,
)
_SIZE_POLICY_MISMATCH_RE = re.compile(r"\bSIZE_POLICY_MISMATCH\b")
_LEGACY_PRIMARY_OPEN_RE = re.compile(
    r"^<!--\s*PRIMARY-READING\s*-->$", re.IGNORECASE
)
_LEGACY_PRIMARY_CLOSE_RE = re.compile(
    r"^<!--\s*/PRIMARY-READING\s*-->$", re.IGNORECASE
)
_LEGACY_PRIMARY_OPEN_SENTINEL = "\x00PRIMARY_OPEN\x00"
_LEGACY_PRIMARY_CLOSE_SENTINEL = "\x00PRIMARY_CLOSE\x00"
_LEGACY_PRIMARY_SENTINEL_RE = re.compile(
    f"({_LEGACY_PRIMARY_OPEN_SENTINEL}|{_LEGACY_PRIMARY_CLOSE_SENTINEL})"
)
_YAML_PAYLOAD_DIRECTIVES = {"myth-box", "high-culture-bridge"}

REPETITION_SHINGLE_WORDS = 5
REPETITION_MIN_PARAGRAPH_WORDS = 40
REPETITION_MIN_SHARED_SHINGLES = 8
REPETITION_JACCARD_THRESHOLD = 0.55
REPETITION_CONTAINMENT_THRESHOLD = 0.82
REPETITION_MIN_LENGTH_RATIO = 0.70
_CHUNK_ID_RE = re.compile(
    r"\b(?:[0-9a-f]{8}_c\d{4}|[a-z0-9-]+_s\d{4}|wikipedia:[^\s`]+:chunk_\d+)\b",
    re.IGNORECASE,
)
_SOURCE_SIGNAL_RE = re.compile(
    r"(?:"
    r"verify_quote|search_literary|search_sources|search_grinchenko|search_heritage|"
    r"Джерельна опора|Джерельний статус|Основні опори|Raw evidence|Raw verify|"
    r"Named recording|edition-like references|Source-disagreement|"
    r"Українська літературна енциклопедія|Енциклопедія українознавства|"
    r"Енциклопедія Сучасної України|Історія української культури|"
    r"Грушевськ|Крип'якевич|Заболотн|Авраменк|Антонович|Колесс|Грінченк"
    r")",
    re.IGNORECASE,
)
_PRIMARY_MARKERS_RE = re.compile(
    r"\b(?:primary|quote|verbatim|архів|архівн|першоджерел|цитат|вериф|корпус|"
    r"виданн|запис|рукопис)\w*",
    re.IGNORECASE,
)
_CONTESTED_MARKERS_RE = re.compile(
    r"\b(?:contested|debate|disagree|myth|decolon|дискус|супереч|міф|"
    r"деколон|колон|радянськ|імпер)\w*",
    re.IGNORECASE,
)
_VARIANT_MARKERS_RE = re.compile(
    r"\b(?:variant|ritual|performance|region|варіант|обряд|ритуал|"
    r"виконав|побутув|регіон|локаль)\w*",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class DensityMetrics:
    words: int
    headings: int
    source_refs: int
    primary_markers: int
    contested_markers: int
    variant_markers: int


@dataclass(frozen=True)
class MarkdownWordMetrics:
    """Structured module counts; ``raw_whitespace_tokens`` is compatibility-only."""

    learner_visible_words: int
    authored_instructional_words: int
    quoted_primary_source_words: int
    excluded_markup_directive_url_tokens: int
    raw_whitespace_tokens: int


@dataclass(frozen=True)
class AuthoredParagraph:
    start_line: int
    end_line: int
    heading: str | None
    normalized_words: tuple[str, ...]


@dataclass(frozen=True)
class RepetitionMatch:
    first_start_line: int
    first_end_line: int
    second_start_line: int
    second_end_line: int
    first_heading: str | None
    second_heading: str | None
    match_type: str
    jaccard_similarity: float
    shorter_paragraph_containment: float
    shared_shingle_count: int
    shared_text: str


@dataclass(frozen=True)
class RepetitionEvidence:
    algorithm: str
    eligible_paragraphs: int
    matches: tuple[RepetitionMatch, ...]


@dataclass(frozen=True)
class SizePolicyRecord:
    track: str
    slug: str
    basis: str
    plan_path: str
    dossier_path: str | None
    module_path: str | None
    plan_floor: int | None
    plan_outline_words: int | None
    actual_words: int | None
    density_band: str
    band_min: int | None
    band_max: int | None
    effective_min: int | None
    advisory_ceiling: int | None
    status: str
    notes: list[str]
    metrics: DensityMetrics | None
    content_metrics: MarkdownWordMetrics | None = None
    repetition: RepetitionEvidence | None = None
    size_policy_mismatch: bool = False
    legacy_raw_whitespace_words: int | None = None
    decision_signals: tuple[str, ...] = ()


@dataclass(frozen=True)
class SizePolicyOverride:
    """A human-reviewed per-plan replacement for generic density-band limits."""

    floor_words: int
    recommended_min: int
    recommended_max: int
    ceiling_words: int
    basis: str
    saturation_evidence: str


def display_path(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def _blank_preserving_newlines(value: str) -> str:
    return "".join("\n" if char == "\n" else " " for char in value)


def _strip_nonvisible_regions(text: str) -> tuple[str, int]:
    excluded = 0

    def replace_comment(match: re.Match[str]) -> str:
        nonlocal excluded
        value = match.group(0)
        token_count = len(_WORD_RE.findall(value))
        if _LEGACY_PRIMARY_OPEN_RE.fullmatch(value.strip()):
            excluded += token_count
            return _LEGACY_PRIMARY_OPEN_SENTINEL.ljust(len(value), " ")
        if _LEGACY_PRIMARY_CLOSE_RE.fullmatch(value.strip()):
            excluded += token_count
            return _LEGACY_PRIMARY_CLOSE_SENTINEL.ljust(len(value), " ")
        excluded += token_count
        return _blank_preserving_newlines(value)

    text = _HTML_COMMENT_RE.sub(replace_comment, text)
    lines = text.splitlines(keepends=True)
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() != "---":
                continue
            for frontmatter_index in range(index + 1):
                excluded += len(_WORD_RE.findall(lines[frontmatter_index]))
                lines[frontmatter_index] = _blank_preserving_newlines(
                    lines[frontmatter_index]
                )
            break
    return "".join(lines), excluded


def _clean_visible_line(line: str) -> tuple[str, int]:
    """Return learner-visible text and a deterministic excluded-token count."""
    excluded = 0

    def replace_link(match: re.Match[str]) -> str:
        nonlocal excluded
        excluded += 1
        return match.group(1)

    line = _MD_INLINE_LINK_RE.sub(replace_link, line)
    urls = list(_URL_RE.finditer(line))
    excluded += len(urls)
    line = _URL_RE.sub(" ", line)

    tags = list(_HTML_TAG_RE.finditer(line))
    excluded += sum(len(_WORD_RE.findall(match.group(0))) for match in tags)
    line = _HTML_TAG_RE.sub(" ", line)

    expressions = list(_COMPONENT_EXPRESSION_RE.finditer(line))
    excluded += sum(len(_WORD_RE.findall(match.group(0))) for match in expressions)
    line = _COMPONENT_EXPRESSION_RE.sub(" ", line)

    line = re.sub(r"^\s*>\s?", "", line)
    line = _LIST_LINE_RE.sub("", line)
    return line.strip(), excluded


def _normalized_words(text: str) -> tuple[str, ...]:
    words: list[str] = []
    for match in _LEXICAL_WORD_RE.finditer(text):
        value = match.group(0)
        if any(char.isalpha() for char in value):
            words.append(value.casefold())
    return tuple(words)


def _shingles(words: tuple[str, ...]) -> set[tuple[str, ...]]:
    if len(words) < REPETITION_SHINGLE_WORDS:
        return set()
    return {
        words[index : index + REPETITION_SHINGLE_WORDS]
        for index in range(len(words) - REPETITION_SHINGLE_WORDS + 1)
    }


def _shared_text(first: tuple[str, ...], second: tuple[str, ...]) -> str:
    block = SequenceMatcher(None, first, second, autojunk=False).find_longest_match()
    if block.size == 0:
        return ""
    value = " ".join(first[block.a : block.a + block.size])
    return value if len(value) <= 240 else value[:237].rstrip() + "..."


def detect_authored_repetition(
    paragraphs: list[AuthoredParagraph],
) -> RepetitionEvidence:
    """Find exact/near duplicates using deterministic five-word shingle overlap.

    Paragraphs shorter than 40 lexical words are excluded as deliberate recaps.
    A pair is actionable when it has at least eight shared shingles and either
    Jaccard overlap is at least 0.55 or shorter-paragraph containment is at
    least 0.82 with a length ratio of at least 0.70.
    """
    matches: list[RepetitionMatch] = []
    shingle_sets = [_shingles(paragraph.normalized_words) for paragraph in paragraphs]
    for first_index, first in enumerate(paragraphs):
        first_shingles = shingle_sets[first_index]
        for second_index in range(first_index + 1, len(paragraphs)):
            second = paragraphs[second_index]
            second_shingles = shingle_sets[second_index]
            shared = first_shingles & second_shingles
            if len(shared) < REPETITION_MIN_SHARED_SHINGLES:
                continue
            union = first_shingles | second_shingles
            jaccard = len(shared) / len(union) if union else 0.0
            shorter = min(len(first_shingles), len(second_shingles))
            containment = len(shared) / shorter if shorter else 0.0
            length_ratio = min(
                len(first.normalized_words), len(second.normalized_words)
            ) / max(len(first.normalized_words), len(second.normalized_words))
            exact = first.normalized_words == second.normalized_words
            near = jaccard >= REPETITION_JACCARD_THRESHOLD or (
                containment >= REPETITION_CONTAINMENT_THRESHOLD
                and length_ratio >= REPETITION_MIN_LENGTH_RATIO
            )
            if not exact and not near:
                continue
            matches.append(
                RepetitionMatch(
                    first_start_line=first.start_line,
                    first_end_line=first.end_line,
                    second_start_line=second.start_line,
                    second_end_line=second.end_line,
                    first_heading=first.heading,
                    second_heading=second.heading,
                    match_type="exact" if exact else "near_duplicate",
                    jaccard_similarity=round(jaccard, 6),
                    shorter_paragraph_containment=round(containment, 6),
                    shared_shingle_count=len(shared),
                    shared_text=_shared_text(
                        first.normalized_words, second.normalized_words
                    ),
                )
            )
    return RepetitionEvidence(
        algorithm=(
            "paragraph_5_word_shingles_v1:jaccard>=0.55_or_"
            "containment>=0.82,length_ratio>=0.70,min_shared=8,min_words=40"
        ),
        eligible_paragraphs=len(paragraphs),
        matches=tuple(matches),
    )


def markdown_module_evidence(
    text: str,
) -> tuple[MarkdownWordMetrics, RepetitionEvidence, bool]:
    """Extract Markdown-aware counts, repetition evidence, and mismatch marker."""
    text = unicodedata.normalize("NFC", text)
    raw_whitespace_tokens = len(_WORD_RE.findall(text))
    has_mismatch_marker = bool(_SIZE_POLICY_MISMATCH_RE.search(text))
    visible_text, excluded = _strip_nonvisible_regions(text)
    directive_stack: list[str] = []
    current_heading: str | None = None
    activity_section = False
    in_fence = False
    in_legacy_primary = False
    authored_words = 0
    primary_words = 0
    paragraphs: list[AuthoredParagraph] = []
    paragraph_lines: list[str] = []
    paragraph_start = 0
    paragraph_end = 0
    paragraph_heading: str | None = None

    def flush_paragraph() -> None:
        nonlocal paragraph_lines, paragraph_start, paragraph_end, paragraph_heading
        if paragraph_lines:
            words = _normalized_words(" ".join(paragraph_lines))
            if len(words) >= REPETITION_MIN_PARAGRAPH_WORDS:
                paragraphs.append(
                    AuthoredParagraph(
                        start_line=paragraph_start,
                        end_line=paragraph_end,
                        heading=paragraph_heading,
                        normalized_words=words,
                    )
                )
        paragraph_lines = []
        paragraph_start = 0
        paragraph_end = 0
        paragraph_heading = None

    def record_content(
        raw_line: str,
        content_line: str,
        line_number: int,
        *,
        in_primary: bool,
    ) -> None:
        nonlocal authored_words, excluded, paragraph_end, paragraph_heading
        nonlocal paragraph_start, primary_words
        in_yaml_payload = any(
            directive in _YAML_PAYLOAD_DIRECTIVES for directive in directive_stack
        )
        if in_yaml_payload:
            content_line = re.sub(
                r"^\s*(?:-\s*)?[A-Za-z_][A-Za-z0-9_-]*:\s*",
                "",
                content_line,
            )
        cleaned, line_excluded = _clean_visible_line(content_line)
        excluded += line_excluded
        words = _normalized_words(cleaned)
        if in_primary:
            flush_paragraph()
            primary_words += len(words)
            return

        authored_words += len(words)
        non_prose = (
            in_fence
            or raw_line.lstrip().startswith(">")
            or bool(_LIST_LINE_RE.match(raw_line))
            or raw_line.lstrip().startswith("|")
            or activity_section
            or in_yaml_payload
        )
        if non_prose:
            flush_paragraph()
            return
        if cleaned:
            if not paragraph_lines:
                paragraph_start = line_number
                paragraph_heading = current_heading
            paragraph_lines.append(cleaned)
            paragraph_end = line_number

    for line_number, raw_line in enumerate(visible_text.splitlines(), 1):
        stripped = raw_line.strip()
        if (
            _LEGACY_PRIMARY_OPEN_SENTINEL in raw_line
            or _LEGACY_PRIMARY_CLOSE_SENTINEL in raw_line
        ):
            for segment in _LEGACY_PRIMARY_SENTINEL_RE.split(raw_line):
                if segment == _LEGACY_PRIMARY_OPEN_SENTINEL:
                    flush_paragraph()
                    in_legacy_primary = True
                elif segment == _LEGACY_PRIMARY_CLOSE_SENTINEL:
                    flush_paragraph()
                    in_legacy_primary = False
                elif segment:
                    record_content(
                        raw_line,
                        segment,
                        line_number,
                        in_primary=in_legacy_primary
                        or "primary-reading" in directive_stack,
                    )
            continue
        directive_open = _DIRECTIVE_OPEN_RE.match(raw_line)
        if directive_open:
            flush_paragraph()
            directive_kind = directive_open.group(1).casefold()
            directive_stack.append(directive_kind)
            title_match = re.search(r"\[([^\]]+)\]", raw_line)
            title_words = (
                _normalized_words(title_match.group(1))
                if title_match is not None and directive_kind != "primary-reading"
                else ()
            )
            authored_words += len(title_words)
            excluded += max(1, len(_WORD_RE.findall(raw_line)) - len(title_words))
            continue
        if _DIRECTIVE_CLOSE_RE.match(raw_line):
            flush_paragraph()
            if directive_stack:
                directive_stack.pop()
            excluded += len(_WORD_RE.findall(raw_line))
            continue
        if _FENCE_RE.match(raw_line):
            flush_paragraph()
            in_fence = not in_fence
            excluded += len(_WORD_RE.findall(raw_line))
            continue
        if not stripped:
            flush_paragraph()
            continue

        heading_match = _HEADING_LINE_RE.match(raw_line)
        if heading_match:
            flush_paragraph()
            cleaned, line_excluded = _clean_visible_line(heading_match.group(2))
            excluded += line_excluded + 1
            words = _normalized_words(cleaned)
            if in_legacy_primary or "primary-reading" in directive_stack:
                primary_words += len(words)
            else:
                authored_words += len(words)
                current_heading = cleaned or None
                activity_section = bool(
                    current_heading
                    and _ACTIVITY_HEADING_RE.fullmatch(current_heading)
                )
            continue

        record_content(
            raw_line,
            raw_line,
            line_number,
            in_primary=in_legacy_primary or "primary-reading" in directive_stack,
        )

    flush_paragraph()
    metrics = MarkdownWordMetrics(
        learner_visible_words=authored_words + primary_words,
        authored_instructional_words=authored_words,
        quoted_primary_source_words=primary_words,
        excluded_markup_directive_url_tokens=excluded,
        raw_whitespace_tokens=raw_whitespace_tokens,
    )
    return metrics, detect_authored_repetition(paragraphs), has_mismatch_marker


def module_content_evidence(
    path: Path,
) -> tuple[MarkdownWordMetrics, RepetitionEvidence, bool]:
    return markdown_module_evidence(path.read_text(encoding="utf-8"))


def word_count(path: Path) -> int:
    """Return canonical authored instructional words for floor enforcement."""
    metrics, _, _ = module_content_evidence(path)
    return metrics.authored_instructional_words


def read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _sum_outline_words(items: Any) -> int | None:
    if not isinstance(items, list):
        return None
    total = 0
    seen = False
    for item in items:
        if not isinstance(item, dict):
            continue
        value = item.get("words")
        if isinstance(value, int):
            total += value
            seen = True
        elif isinstance(value, str) and value.isdigit():
            total += int(value)
            seen = True
    return total if seen else None


def _source_ref_count(text: str) -> int:
    refs: set[str] = set()
    refs.update(match.group(0) for match in _URL_RE.finditer(text))
    refs.update(match.group(1) for match in _MD_LINK_RE.finditer(text))
    refs.update(match.group(0) for match in _CHUNK_ID_RE.finditer(text))
    for line_number, line in enumerate(text.splitlines(), 1):
        if _SOURCE_SIGNAL_RE.search(line):
            refs.add(f"source-line:{line_number}")
    return len(refs)


def dossier_metrics(path: Path) -> DensityMetrics:
    text = path.read_text(encoding="utf-8")
    return DensityMetrics(
        words=len(_WORD_RE.findall(text)),
        headings=len(_HEADING_RE.findall(text)),
        source_refs=_source_ref_count(text),
        primary_markers=len(_PRIMARY_MARKERS_RE.findall(text)),
        contested_markers=len(_CONTESTED_MARKERS_RE.findall(text)),
        variant_markers=len(_VARIANT_MARKERS_RE.findall(text)),
    )


def _track_profile(track: str) -> str:
    normalized = track.lower()
    if normalized == "folk":
        return "folk"
    if normalized == "bio":
        return "bio"
    if normalized in CORE_RESEARCH_TRACKS:
        return "core"
    return "seminar"


def classify_dossier(track: str, metrics: DensityMetrics) -> str:
    """Return an advisory source-density band normalized by track.

    The thresholds intentionally treat FOLK as dossier-heavy because its
    existing quality contract says thin dossiers usually mean insufficient
    corpus work, not a genuinely sparse topic.
    """
    profile = _track_profile(track)
    evidence_markers = (
        metrics.primary_markers + metrics.contested_markers + metrics.variant_markers
    )

    if profile == "folk":
        if metrics.words < 2500 or metrics.source_refs < 4 or evidence_markers < 6:
            return "sparse"
        if metrics.words >= 5500 and metrics.source_refs >= 8 and evidence_markers >= 14:
            return "dense"
        return "normal"

    if profile == "bio":
        if metrics.words < 1200 or metrics.source_refs < 2:
            return "sparse"
        if metrics.words >= 2600 and metrics.source_refs >= 8 and evidence_markers >= 8:
            return "dense"
        return "normal"

    if metrics.words < 2200 or metrics.source_refs < 3:
        return "sparse"
    if metrics.words >= 5200 and metrics.source_refs >= 8 and evidence_markers >= 10:
        return "dense"
    return "normal"


def classify_core_evidence(plan: dict[str, Any]) -> str:
    """Classify A1-C2 modules by plan/evidence pressure, not dossier size."""
    target = _as_int(plan.get("word_target"))
    outline_words = _sum_outline_words(plan.get("content_outline"))
    refs = plan.get("references")
    ref_count = len(refs) if isinstance(refs, list) else 0
    primary_sources = 0
    for section in plan.get("content_outline") or []:
        if isinstance(section, dict) and isinstance(section.get("primary_sources"), list):
            primary_sources += len(section["primary_sources"])

    if target and target >= 5000 and (ref_count >= 3 or primary_sources >= 2):
        return "core_research_extended"
    if outline_words and outline_words > 4500:
        return "core_research_extended"
    return "core_pedagogy_standard"


def band_limits(band: str) -> tuple[int | None, int | None]:
    if band == "core_research_extended":
        return 4500, 6500
    if band == "core_pedagogy_standard":
        return 3500, 5000
    low, high = MODULE_SIZE_BANDS[band]
    return low, high


def _as_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _is_positive_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def validate_size_policy_override(plan: Mapping[str, Any]) -> list[str]:
    """Return deterministic schema errors for an explicit plan size override.

    An absent ``size_policy`` is intentionally valid: generic dossier/evidence
    bands remain the policy for legacy plans.  A present policy must be fully
    reviewed and self-contained before it can replace those bands.
    """
    if "size_policy" not in plan:
        return []

    policy = plan["size_policy"]
    if not isinstance(policy, Mapping):
        return ["size_policy must be a mapping."]

    errors: list[str] = []
    floor = policy.get("floor_words")
    recommended_range = policy.get("recommended_range")
    ceiling = policy.get("ceiling_words")

    if not _is_positive_integer(floor):
        errors.append("size_policy.floor_words must be a positive integer.")

    recommended_min: int | None = None
    recommended_max: int | None = None
    if (
        not isinstance(recommended_range, list)
        or len(recommended_range) != 2
        or not all(_is_positive_integer(value) for value in recommended_range)
    ):
        errors.append(
            "size_policy.recommended_range must be a two-item list of positive integers."
        )
    else:
        recommended_min, recommended_max = recommended_range
        if recommended_min > recommended_max:
            errors.append("size_policy.recommended_range must not be inverted.")
        if _is_positive_integer(floor) and recommended_min < floor:
            errors.append(
                "size_policy.recommended_range[0] must be at least size_policy.floor_words."
            )

    if not _is_positive_integer(ceiling):
        errors.append("size_policy.ceiling_words must be a positive integer.")
    else:
        if _is_positive_integer(floor) and ceiling < floor:
            errors.append(
                "size_policy.ceiling_words must be at least size_policy.floor_words."
            )
        if recommended_max is not None and ceiling < recommended_max:
            errors.append(
                "size_policy.ceiling_words must be at least size_policy.recommended_range[1]."
            )

    word_target = _as_int(plan.get("word_target"))
    if not _is_positive_integer(word_target):
        errors.append("size_policy requires word_target to be a positive integer.")
    elif _is_positive_integer(floor) and floor != word_target:
        errors.append(
            "size_policy.floor_words "
            f"({floor}) must equal word_target ({word_target})."
        )

    for field in ("basis", "saturation_evidence"):
        value = policy.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"size_policy.{field} must be a nonempty string.")

    if policy.get("exceptional_justification") != "required_above_ceiling":
        errors.append(
            "size_policy.exceptional_justification must be required_above_ceiling."
        )

    return errors


def explicit_size_policy_override(
    plan: Mapping[str, Any],
) -> tuple[SizePolicyOverride | None, list[str]]:
    """Return a parsed override or the actionable errors that reject it."""
    errors = validate_size_policy_override(plan)
    if errors or "size_policy" not in plan:
        return None, errors

    policy = plan["size_policy"]
    assert isinstance(policy, Mapping)
    recommended_range = policy["recommended_range"]
    assert isinstance(recommended_range, list)
    return (
        SizePolicyOverride(
            floor_words=policy["floor_words"],
            recommended_min=recommended_range[0],
            recommended_max=recommended_range[1],
            ceiling_words=policy["ceiling_words"],
            basis=policy["basis"].strip(),
            saturation_evidence=policy["saturation_evidence"].strip(),
        ),
        [],
    )


def build_explicit_size_policy_record(
    *,
    track: str,
    slug: str,
    plan_path: str,
    dossier_path: str | None,
    module_path: str | None,
    plan_floor: int | None,
    plan_outline_words: int | None,
    actual_words: int | None,
    metrics: DensityMetrics | None,
    override: SizePolicyOverride,
    content_metrics: MarkdownWordMetrics | None = None,
    repetition: RepetitionEvidence | None = None,
    size_policy_mismatch: bool = False,
) -> SizePolicyRecord:
    """Build the effective record for a valid, reviewed plan override."""
    notes = [
        "A reviewed explicit plan size policy override replaces generic density-band limits.",
        f"Review basis: {override.basis}",
        f"Saturation evidence: {override.saturation_evidence}",
        (
            "Above the explicit advisory ceiling, exceptional justification is "
            "required."
        ),
    ]
    signals: list[str] = []
    if size_policy_mismatch:
        signals.append("plan_review_needed")
        notes.append(
            "SIZE_POLICY_MISMATCH declares exhausted grounded material; stop automatic expansion and route to plan review."
        )
    if actual_words is not None and actual_words < override.floor_words:
        signals.append("below_plan_floor")
        notes.append("Built module is below the current plan floor.")
    elif actual_words is not None and actual_words > override.ceiling_words:
        signals.append("over_advisory_ceiling")
        notes.append(
            "Built module exceeds the explicit advisory ceiling; review sourced pedagogy without failing on length alone."
        )
    if repetition is not None and repetition.matches:
        signals.append("repetitive_authored_prose")
        notes.append(
            f"Detected {len(repetition.matches)} actionable exact/near-duplicate authored paragraph pair(s)."
        )

    if "plan_review_needed" in signals:
        status = "plan_review_needed"
    elif "below_plan_floor" in signals:
        status = "below_plan_floor"
    elif "repetitive_authored_prose" in signals:
        status = "repetitive_authored_prose"
    elif "over_advisory_ceiling" in signals:
        status = "over_advisory_ceiling"
    else:
        status = "explicit_override"

    return SizePolicyRecord(
        track=track,
        slug=slug,
        basis="explicit_plan_size_policy",
        plan_path=plan_path,
        dossier_path=dossier_path,
        module_path=module_path,
        plan_floor=plan_floor,
        plan_outline_words=plan_outline_words,
        actual_words=actual_words,
        density_band="reviewed_plan_override",
        band_min=override.recommended_min,
        band_max=override.recommended_max,
        effective_min=override.floor_words,
        advisory_ceiling=override.ceiling_words,
        status=status,
        notes=notes,
        metrics=metrics,
        content_metrics=content_metrics,
        repetition=repetition,
        size_policy_mismatch=size_policy_mismatch,
        legacy_raw_whitespace_words=(
            content_metrics.raw_whitespace_tokens if content_metrics else None
        ),
        decision_signals=tuple(signals),
    )


def _plan_paths_for_track(track: str) -> list[Path]:
    plans_dir = CURRICULUM_ROOT / "plans" / track
    if not plans_dir.exists():
        return []
    return sorted(path for path in plans_dir.glob("*.yaml") if not path.name.endswith(".bak.yaml"))


def _module_path(track: str, slug: str) -> Path:
    track_dir = CURRICULUM_ROOT / track
    nested = track_dir / slug / "module.md"
    candidates = [
        nested,
        track_dir / f"{slug}.md",
        *sorted(track_dir.glob(f"[0-9]*-{slug}.md")),
    ]
    return next((candidate for candidate in candidates if candidate.exists()), nested)


def _dossier_from_plan(plan: dict[str, Any]) -> Path | None:
    references = plan.get("references")
    if not isinstance(references, list):
        return None
    for reference in references:
        if not isinstance(reference, dict):
            continue
        path_value = reference.get("path")
        if reference.get("type") != "dossier" or not isinstance(path_value, str):
            continue
        path = Path(path_value)
        candidate = path if path.is_absolute() else PROJECT_ROOT / path
        if candidate.exists():
            return candidate
    return None


def _dossier_path(track: str, slug: str, plan: dict[str, Any]) -> Path | None:
    from_plan = _dossier_from_plan(plan)
    if from_plan is not None:
        return from_plan

    candidates = [
        RESEARCH_ROOT / track / f"{slug}.md",
        CURRICULUM_ROOT / track / "research" / f"{slug}-research.md",
        CURRICULUM_ROOT / track / "research" / f"{slug}.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _status_and_notes(
    *,
    track: str,
    plan_floor: int | None,
    actual_words: int | None,
    band: str,
    band_max: int | None,
    advisory_ceiling: int | None,
    dossier_path: Path | None,
    repetition: RepetitionEvidence | None = None,
    size_policy_mismatch: bool = False,
) -> tuple[str, list[str], tuple[str, ...]]:
    notes: list[str] = []
    signals: list[str] = []

    if plan_floor is None:
        return (
            "missing_plan_word_target",
            ["Plan has no numeric word_target."],
            ("missing_plan_word_target",),
        )

    if size_policy_mismatch:
        signals.append("plan_review_needed")
        notes.append(
            "SIZE_POLICY_MISMATCH declares exhausted grounded material; stop automatic expansion and route to plan review."
        )

    if track.lower() in SEMINAR_TRACKS and dossier_path is None:
        signals.append("missing_dossier")
        notes.append("Seminar module has no discoverable research dossier.")

    if band == "sparse":
        notes.append(
            "Sparse classification is not permission to underbuild; require source-saturation evidence before lowering a plan."
        )
    if band.startswith("core_"):
        notes.append(
            "Core A1-C2 uses a pedagogy/evidence-packet basis; do not apply seminar dossier ceilings mechanically."
        )

    if band_max is not None and plan_floor > band_max:
        if "plan_review_needed" not in signals:
            signals.append("plan_review_needed")
        notes.append(
            "Plan floor exceeds the dossier/evidence advisory ceiling; review the plan before asking writers to expand."
        )

    if actual_words is not None:
        if actual_words < plan_floor:
            signals.append("below_plan_floor")
            if "plan_review_needed" in signals:
                notes.append(
                    "Built module is below the current plan floor, but the plan floor already exceeds the advisory ceiling; review the plan before expanding."
                )
            else:
                notes.append("Built module is below the current plan floor.")
        elif advisory_ceiling is not None and actual_words > advisory_ceiling:
            signals.append("over_advisory_ceiling")
            notes.append(
                "Built module exceeds the advisory ceiling; expansion should be justified by sourced pedagogy."
            )
        if actual_words >= MODULE_SIZE_BANDS["exceptional"][0]:
            signals.append("exceptional_justification_required")
            notes.append("Modules at 8000+ words require explicit justification.")

    if repetition is not None and repetition.matches:
        signals.append("repetitive_authored_prose")
        notes.append(
            f"Detected {len(repetition.matches)} actionable exact/near-duplicate authored paragraph pair(s)."
        )

    priority = (
        "missing_plan_word_target",
        "missing_dossier",
        "plan_review_needed",
        "below_plan_floor",
        "repetitive_authored_prose",
        "exceptional_justification_required",
        "over_advisory_ceiling",
    )
    status = next((signal for signal in priority if signal in signals), "advisory_ok")
    return status, notes, tuple(dict.fromkeys(signals))


def build_record(track: str, plan_path: Path) -> SizePolicyRecord:
    plan = read_yaml(plan_path)
    slug = str(plan.get("slug") or plan_path.stem)
    plan_floor = _as_int(plan.get("word_target"))
    plan_outline_words = _sum_outline_words(plan.get("content_outline"))
    module_path = _module_path(track, slug)
    content_metrics: MarkdownWordMetrics | None = None
    repetition: RepetitionEvidence | None = None
    size_policy_mismatch = False
    if module_path.exists():
        content_metrics, repetition, size_policy_mismatch = module_content_evidence(
            module_path
        )
    actual_words = (
        content_metrics.authored_instructional_words if content_metrics else None
    )
    dossier_path = _dossier_path(track, slug, plan)

    metrics = dossier_metrics(dossier_path) if dossier_path else None
    override, override_errors = explicit_size_policy_override(plan)
    displayed_plan_path = display_path(plan_path) or str(plan_path)
    displayed_dossier_path = display_path(dossier_path)
    displayed_module_path = display_path(module_path) if module_path.exists() else None
    if override is not None:
        return build_explicit_size_policy_record(
            track=track,
            slug=slug,
            plan_path=displayed_plan_path,
            dossier_path=displayed_dossier_path,
            module_path=displayed_module_path,
            plan_floor=plan_floor,
            plan_outline_words=plan_outline_words,
            actual_words=actual_words,
            metrics=metrics,
            override=override,
            content_metrics=content_metrics,
            repetition=repetition,
            size_policy_mismatch=size_policy_mismatch,
        )

    if metrics is not None:
        basis = "research_dossier"
        band = classify_dossier(track, metrics)
    elif track.lower() in CORE_RESEARCH_TRACKS:
        basis = "core_evidence_packet"
        band = classify_core_evidence(plan)
    else:
        basis = "missing_research_dossier"
        band = "sparse"

    band_min, band_max = band_limits(band)
    effective_min = plan_floor
    advisory_ceiling = None
    if plan_floor is not None:
        advisory_ceiling = max(plan_floor, band_max) if band_max is not None else None

    status, notes, decision_signals = _status_and_notes(
        track=track,
        plan_floor=plan_floor,
        actual_words=actual_words,
        band=band,
        band_max=band_max,
        advisory_ceiling=advisory_ceiling,
        dossier_path=dossier_path,
        repetition=repetition,
        size_policy_mismatch=size_policy_mismatch,
    )
    if override_errors:
        status = "invalid_size_policy"
        decision_signals = ("invalid_size_policy", *decision_signals)
        notes.extend(
            [
                "Explicit size_policy is invalid and cannot replace generic density-band limits.",
                *override_errors,
            ]
        )

    return SizePolicyRecord(
        track=track,
        slug=slug,
        basis=basis,
        plan_path=displayed_plan_path,
        dossier_path=displayed_dossier_path,
        module_path=displayed_module_path,
        plan_floor=plan_floor,
        plan_outline_words=plan_outline_words,
        actual_words=actual_words,
        density_band=band,
        band_min=band_min,
        band_max=band_max,
        effective_min=effective_min,
        advisory_ceiling=advisory_ceiling,
        status=status,
        notes=notes,
        metrics=metrics,
        content_metrics=content_metrics,
        repetition=repetition,
        size_policy_mismatch=size_policy_mismatch,
        legacy_raw_whitespace_words=(
            content_metrics.raw_whitespace_tokens if content_metrics else None
        ),
        decision_signals=tuple(dict.fromkeys(decision_signals)),
    )


def select_plan_paths(
    tracks: list[str],
    slugs: set[str] | None,
    built_only: bool,
) -> list[tuple[str, Path]]:
    selected: list[tuple[str, Path]] = []
    for track in tracks:
        for plan_path in _plan_paths_for_track(track):
            plan = read_yaml(plan_path)
            slug = str(plan.get("slug") or plan_path.stem)
            if slugs is not None and slug not in slugs:
                continue
            if built_only and not _module_path(track, slug).exists():
                continue
            selected.append((track, plan_path))
    return selected


def _parse_slug_filter(values: list[str] | None) -> set[str] | None:
    if not values:
        return None
    slugs: set[str] = set()
    for value in values:
        slugs.update(part.strip() for part in value.split(",") if part.strip())
    return slugs or None


def _record_to_dict(record: SizePolicyRecord) -> dict[str, Any]:
    return asdict(record)


def build_records(
    *,
    tracks: list[str],
    slugs: set[str] | None = None,
    built_only: bool = False,
) -> list[SizePolicyRecord]:
    """Build advisory size-policy records for selected module plans."""
    normalized_tracks = [track.lower() for track in tracks]
    return [
        build_record(track, plan_path)
        for track, plan_path in select_plan_paths(normalized_tracks, slugs, built_only)
    ]


def build_report(
    *,
    tracks: list[str],
    slugs: set[str] | None = None,
    built_only: bool = False,
) -> list[dict[str, Any]]:
    """Return a stable JSON-serializable advisory report."""
    records = build_records(tracks=tracks, slugs=slugs, built_only=built_only)
    return [_record_to_dict(record) for record in records]


def print_summary(records: list[SizePolicyRecord]) -> None:
    if not records:
        print("No module plans selected.")
        return

    headers = [
        "track",
        "slug",
        "basis",
        "band",
        "plan",
        "authored",
        "visible",
        "raw",
        "ceiling",
        "repeat",
        "status",
    ]
    rows: list[list[str]] = []
    for record in records:
        rows.append(
            [
                record.track,
                record.slug,
                record.basis,
                record.density_band,
                str(record.plan_floor if record.plan_floor is not None else "-"),
                str(record.actual_words if record.actual_words is not None else "-"),
                str(
                    record.content_metrics.learner_visible_words
                    if record.content_metrics
                    else "-"
                ),
                str(
                    record.legacy_raw_whitespace_words
                    if record.legacy_raw_whitespace_words is not None
                    else "-"
                ),
                str(
                    record.advisory_ceiling
                    if record.advisory_ceiling is not None
                    else "-"
                ),
                str(len(record.repetition.matches) if record.repetition else "-"),
                record.status,
            ]
        )

    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    print("  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(value.ljust(widths[index]) for index, value in enumerate(row)))
    print()
    print(
        "Advisory only: this command reports policy pressure and returns 0; it does not change build gates."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Report dossier/evidence-led module size policy signals.",
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--tracks",
        nargs="+",
        default=["bio", "folk"],
        help="Track directories under curriculum/l2-uk-en/plans/ to inspect.",
    )
    parser.add_argument(
        "--slugs",
        nargs="*",
        help="Optional slug filter; accepts repeated values or comma-separated lists.",
    )
    parser.add_argument(
        "--built-only",
        action="store_true",
        help="Only report plans with an existing curriculum/l2-uk-en/{track}/{slug}/module.md.",
    )
    parser.add_argument(
        "--format",
        choices=("summary", "json"),
        default="summary",
        help="Output format.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    slugs = _parse_slug_filter(args.slugs)
    records = build_records(tracks=args.tracks, slugs=slugs, built_only=args.built_only)

    if args.format == "json":
        report = [_record_to_dict(record) for record in records]
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_summary(records)
    return 0


if __name__ == "__main__":
    sys.exit(main())
