#!/usr/bin/env python3
"""Report deterministic, advisory text-difficulty features for module sources.

This Phase 1 tool deliberately reports surface and lexical observations only.
It does not estimate CEFR, apply thresholds, use a parser, download models, or
write generated curriculum artifacts.

Examples:

    .venv/bin/python scripts/audit/text_difficulty.py --track a1 --slug a1-finale
    .venv/bin/python scripts/audit/text_difficulty.py --module a1/a1-finale
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
SCHEMA_VERSION = "text_difficulty.v1"
MATTR_WINDOW_SIZE = 50
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from linguistics.tokenize_uk import tokenize_sents

REGION_ORDER = (
    "headings",
    "prose",
    "lists",
    "tables",
    "block_quotes",
    "fenced_examples",
    "inline_examples",
)

_FRONT_MATTER_DELIMITER = "---"
_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_IMPORT_EXPORT_RE = re.compile(
    r"^\s*(?:"
    r"import\s+(?:[\w*${},\s]+\s+from\s+)?['\"]"
    r"|export\s+(?:default\b|const\b|let\b|var\b|function\b|class\b|\{|\*)"
    r")"
)
_MULTILINE_TAG_START_RE = re.compile(r"^</?\s*[A-Za-z][A-Za-z0-9_.:-]*(?:\s|$)")
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+")
_LIST_RE = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+")
_QUOTE_RE = re.compile(r"^\s*>\s?")
_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
_MARKDOWN_LINK_RE = re.compile(r"!?\[([^\]]*)\]\((?:[^()\\]|\\.|\([^)]*\))*\)")
_RAW_URL_RE = re.compile(r"(?:https?|ftp)://\S+", re.IGNORECASE)
_HTML_OR_JSX_TAG_RE = re.compile(r"</?[A-Za-z][A-Za-z0-9_.:-]*(?:\s+[^<>]*)?/?>")
_JSX_EXPRESSION_RE = re.compile(r"\{[^{}\n]*\}")
_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_STRESS_RE = re.compile("[\u0300\u0301]")
_UA_LETTERS = "А-ЩЬЮЯЄІЇҐа-щьюяєіїґ"
_UA_TOKEN_RE = re.compile(rf"[{_UA_LETTERS}]+(?:['-][{_UA_LETTERS}]+)*")
_EN_TOKEN_RE = re.compile(r"[A-Za-z]+(?:['-][A-Za-z]+)*")
_WORD_TOKEN_RE = re.compile(r"[^\W\d_]+(?:['-][^\W\d_]+)*", re.UNICODE)
_APOSTROPHE_TRANSLATION = str.maketrans(
    {
        "ʼ": "'",
        "’": "'",
        "`": "'",
        "′": "'",
        "‐": "-",
        "‑": "-",
    }
)

# This is source-track metadata, transcribed from
# docs/best-practices/track-architecture.md. It intentionally does not inspect
# plans, front matter, or module content, and does not estimate a level.
TRACK_TARGET_LEVELS = {
    "a1": "A1",
    "a2": "A2",
    "b1": "B1",
    "b2": "B2",
    "bio": "C1",
    "c1": "C1",
    "c2": "C2",
    "folk": "C1",
    "hist": "C1",
    "istorio": "C1",
    "lit": "C1+",
    "lit-drama": "C1+",
    "lit-essay": "C1+",
    "lit-fantastika": "C1+",
    "lit-hist-fic": "C1+",
    "lit-humor": "C1+",
    "lit-war": "C1+",
    "lit-youth": "C1+",
    "oes": "C2",
    "ruth": "C2",
}


@dataclass(frozen=True)
class SourceRef:
    """A selected module source, whether or not its source file exists."""

    track: str
    slug: str
    path: Path

    @property
    def module_path(self) -> str:
        return f"{self.track}/{self.slug}/module.md"


@dataclass(frozen=True)
class RegionText:
    """One cleaned learner-facing Markdown fragment and its source region."""

    region: str
    text: str


def _strip_front_matter(text: str) -> str:
    """Remove YAML front matter only when it begins the document."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != _FRONT_MATTER_DELIMITER:
        return text

    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == _FRONT_MATTER_DELIMITER:
            return "".join(lines[index + 1 :])
    return text


def _normalise_text(text: str) -> str:
    return _STRESS_RE.sub("", unicodedata.normalize("NFC", text).translate(_APOSTROPHE_TRANSLATION)).casefold()


def ukrainian_tokens(text: str) -> list[str]:
    """Return normalized Ukrainian-script surface tokens in source order.

    This is intentionally script-based, not a lexicon lookup or a language
    classifier. It makes the Phase 1 boundary reproducible and offline.
    """
    normalized = _normalise_text(text)
    return [match.group(0) for match in _UA_TOKEN_RE.finditer(normalized)]


def _language_counts(text: str) -> dict[str, int]:
    normalized = _normalise_text(text)
    counts = Counter()
    for match in _WORD_TOKEN_RE.finditer(normalized):
        token = match.group(0)
        if _UA_TOKEN_RE.fullmatch(token):
            counts["ukrainian"] += 1
        elif _EN_TOKEN_RE.fullmatch(token):
            counts["english"] += 1
        else:
            counts["other"] += 1
    return {
        "ukrainian_token_count": counts["ukrainian"],
        "english_token_count": counts["english"],
        "other_word_token_count": counts["other"],
        "word_token_count": sum(counts.values()),
    }


def _with_rates(counts: dict[str, int]) -> dict[str, int | float]:
    total = counts["word_token_count"]
    result: dict[str, int | float] = dict(counts)
    for language in ("ukrainian", "english", "other_word"):
        count_key = f"{language}_token_count"
        rate_key = f"{language}_token_rate"
        result[rate_key] = counts[count_key] / total if total else 0.0
    return result


def _base_region(line: str) -> tuple[str, str]:
    """Classify one Markdown line and remove only its structural prefix."""
    if _TABLE_SEPARATOR_RE.match(line):
        return "", ""
    if _HEADING_RE.match(line):
        return "headings", _HEADING_RE.sub("", line, count=1)
    if _QUOTE_RE.match(line):
        return "block_quotes", _QUOTE_RE.sub("", line, count=1)
    if _LIST_RE.match(line):
        return "lists", _LIST_RE.sub("", line, count=1)
    if "|" in line:
        return "tables", line
    return "prose", line


def _clean_markdown_text(line: str) -> str:
    """Keep human-readable Markdown text while deleting implementation noise."""
    line = _MARKDOWN_LINK_RE.sub(r"\1", line)
    line = _RAW_URL_RE.sub(" ", line)
    line = _HTML_OR_JSX_TAG_RE.sub(" ", line)
    line = _JSX_EXPRESSION_RE.sub(" ", line)
    line = line.replace("|", " ")
    line = re.sub(r"(?<!\\)[*_~]", "", line)
    return " ".join(line.split())


def extract_markdown_regions(text: str) -> list[RegionText]:
    """Extract reader-visible source text with deterministic region labels.

    Fenced and inline examples are retained because this curriculum uses them
    for learner-facing dialogues and forms. Fence delimiters, front matter,
    comments (including ``INJECT_ACTIVITY`` markers), URLs, imports/exports,
    HTML/JSX tags and their attribute expressions are excluded.
    """
    cleaned_source = _HTML_COMMENT_RE.sub(" ", _strip_front_matter(text))
    regions: list[RegionText] = []
    in_fence = False
    in_multiline_tag = False

    for raw_line in cleaned_source.splitlines():
        if _FENCE_RE.match(raw_line):
            in_fence = not in_fence
            continue

        if in_multiline_tag:
            if ">" in raw_line:
                in_multiline_tag = False
            continue

        stripped = raw_line.strip()
        if not stripped or "INJECT_ACTIVITY" in raw_line or _IMPORT_EXPORT_RE.match(raw_line):
            continue
        if stripped.startswith(":::"):
            continue
        if _MULTILINE_TAG_START_RE.match(stripped) and ">" not in stripped:
            in_multiline_tag = True
            continue

        if in_fence:
            value = _clean_markdown_text(raw_line)
            if value:
                regions.append(RegionText("fenced_examples", value))
            continue

        region, markdown_text = _base_region(raw_line)
        if not region:
            continue
        if "`" not in markdown_text:
            value = _clean_markdown_text(markdown_text)
            if value:
                regions.append(RegionText(region, value))
            continue

        position = 0
        for match in _INLINE_CODE_RE.finditer(markdown_text):
            before = _clean_markdown_text(markdown_text[position : match.start()])
            if before:
                regions.append(RegionText(region, before))
            inline = _clean_markdown_text(match.group(1))
            if inline:
                regions.append(RegionText("inline_examples", inline))
            position = match.end()
        after = _clean_markdown_text(markdown_text[position:])
        if after:
            regions.append(RegionText(region, after))

    return regions


def extract_markdown_text(text: str) -> str:
    """Return the extracted learner-facing text without exposing region internals."""
    return "\n".join(fragment.text for fragment in extract_markdown_regions(text))


def _coverage(regions: Iterable[RegionText]) -> dict[str, Any]:
    per_region = {region: _with_rates(_language_counts("")) for region in REGION_ORDER}
    aggregate = _language_counts("")
    for fragment in regions:
        fragment_counts = _language_counts(fragment.text)
        region_counts = per_region[fragment.region]
        for key in (
            "ukrainian_token_count",
            "english_token_count",
            "other_word_token_count",
            "word_token_count",
        ):
            region_counts[key] = int(region_counts[key]) + fragment_counts[key]
            aggregate[key] += fragment_counts[key]

    for region, counts in per_region.items():
        per_region[region] = _with_rates({key: int(value) for key, value in counts.items() if key.endswith("count")})
    return {
        "language": _with_rates(aggregate),
        "regions": per_region,
    }


def _sentence_tokens(text: str) -> list[list[str]]:
    """Use the vendored deterministic UA tokenizer, then retain UA tokens only."""
    return [tokens for sentence in tokenize_sents(text) if (tokens := ukrainian_tokens(sentence))]


def _mattr(tokens: Sequence[str]) -> dict[str, int | float | str]:
    if len(tokens) < MATTR_WINDOW_SIZE:
        return {
            "status": "unavailable",
            "reason": "insufficient_ukrainian_tokens",
            "window_size": MATTR_WINDOW_SIZE,
            "minimum_token_count": MATTR_WINDOW_SIZE,
            "observed_token_count": len(tokens),
        }
    window_rates = [
        len(set(tokens[start : start + MATTR_WINDOW_SIZE])) / MATTR_WINDOW_SIZE
        for start in range(len(tokens) - MATTR_WINDOW_SIZE + 1)
    ]
    return {
        "status": "available",
        "window_size": MATTR_WINDOW_SIZE,
        "window_count": len(window_rates),
        "value": sum(window_rates) / len(window_rates),
    }


def _surface_features(text: str) -> dict[str, Any]:
    tokens = ukrainian_tokens(text)
    counts = Counter(tokens)
    sentence_tokens = _sentence_tokens(text)
    token_count = len(tokens)
    unique_count = len(counts)
    hapax_count = sum(count == 1 for count in counts.values())

    return {
        "ukrainian_token_count": token_count,
        "ukrainian_sentence_count": len(sentence_tokens),
        "average_ukrainian_token_length": (
            sum(len(token.replace("'", "").replace("-", "")) for token in tokens) / token_count if token_count else None
        ),
        "average_ukrainian_sentence_length": (
            sum(len(sentence) for sentence in sentence_tokens) / len(sentence_tokens) if sentence_tokens else None
        ),
        "unique_ukrainian_form_count": unique_count,
        "unique_ukrainian_form_rate": unique_count / token_count if token_count else None,
        "hapax_ukrainian_form_count": hapax_count,
        "hapax_ukrainian_form_rate": hapax_count / token_count if token_count else None,
        "mattr": _mattr(tokens),
    }


def _unavailable_parser_capabilities() -> dict[str, dict[str, str]]:
    reason = "ukrainian_ud_parser_model_not_declared_pinned_or_tested"
    return {
        "clauses_per_sentence": {"status": "unavailable", "reason": reason},
        "dependency_tree_depth": {"status": "unavailable", "reason": reason},
    }


def _declared_target_level(track: str) -> str | None:
    """Read a documented label from the source directory name; do not infer one."""
    return TRACK_TARGET_LEVELS.get(track.casefold())


def _source_metadata(source: SourceRef) -> dict[str, str | None]:
    return {
        "declared_target_level": _declared_target_level(source.track),
        "declared_target_level_source": "source_track_directory",
        "module_path": source.module_path,
        "slug": source.slug,
        "track": source.track,
    }


def analyze_source(source: SourceRef) -> dict[str, Any]:
    """Analyze one selected source, preserving unavailable states explicitly."""
    result: dict[str, Any] = {"source": _source_metadata(source)}
    if not source.path.exists():
        result.update({"status": "missing_source", "reason": "module_md_not_found"})
        return result
    if not source.path.is_file():
        result.update({"status": "skipped", "reason": "module_md_not_regular_file"})
        return result

    try:
        raw_text = source.path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        result.update({"status": "skipped", "reason": "module_md_unreadable", "detail": type(error).__name__})
        return result

    regions = extract_markdown_regions(raw_text)
    extracted_text = "\n".join(fragment.text for fragment in regions)
    result["coverage"] = _coverage(regions)
    result["features"] = _surface_features(extracted_text)
    result["capabilities"] = _unavailable_parser_capabilities()
    result["status"] = "analyzed" if result["features"]["ukrainian_token_count"] else "no_ukrainian_text"
    return result


def _parse_module_selector(value: str) -> tuple[str, str]:
    parts = value.split("/")
    if len(parts) != 2 or not all(parts) or any(part in {".", ".."} for part in parts):
        raise argparse.ArgumentTypeError("--module must be TRACK/SLUG")
    return parts[0], parts[1]


def discover_sources(
    curriculum_root: Path,
    *,
    tracks: Sequence[str] = (),
    slugs: Sequence[str] = (),
    modules: Sequence[tuple[str, str]] = (),
) -> list[SourceRef]:
    """Select module.md paths in a deterministic order without requiring existence."""
    if modules and (tracks or slugs):
        raise ValueError("--module cannot be combined with --track or --slug")
    if slugs and len(tracks) != 1:
        raise ValueError("--slug requires exactly one --track")

    root = curriculum_root.resolve()
    selected: set[tuple[str, str]] = set(modules)
    if slugs:
        selected.update((tracks[0], slug) for slug in slugs)
    elif tracks:
        for track in tracks:
            track_root = root / track
            if not track_root.is_dir():
                continue
            selected.update((track, path.parent.name) for path in track_root.glob("*/module.md"))
    elif not modules:
        selected.update((path.parent.parent.name, path.parent.name) for path in root.glob("*/*/module.md"))

    return [
        SourceRef(track=track, slug=slug, path=root / track / slug / "module.md") for track, slug in sorted(selected)
    ]


def build_report(
    curriculum_root: Path = DEFAULT_CURRICULUM_ROOT,
    *,
    tracks: Sequence[str] = (),
    slugs: Sequence[str] = (),
    modules: Sequence[tuple[str, str]] = (),
) -> dict[str, Any]:
    """Build a stable Phase 1 report without a timestamp or a derived verdict."""
    sources = discover_sources(curriculum_root, tracks=tracks, slugs=slugs, modules=modules)
    results = [analyze_source(source) for source in sources]
    status_counts = Counter(result["status"] for result in results)
    return {
        "analysis": {
            "advisory": True,
            "calibration": {
                "status": "uncalibrated",
                "reason": "no_calibrated_cefr_mapping_or_thresholds_in_phase_1",
            },
            "does_not_estimate_cefr": True,
            "feature_definitions": {
                "hapax_ukrainian_form_rate": "Hapax Ukrainian forms divided by Ukrainian token occurrences.",
                "mattr": "Mean type-token ratio over overlapping Ukrainian-token windows of 50.",
                "unique_ukrainian_form_rate": "Unique Ukrainian forms divided by Ukrainian token occurrences.",
                "ukrainian_tokens": "Normalized Ukrainian-script surface tokens; not a parser or lexicon classification.",
            },
            "parser_capabilities": _unavailable_parser_capabilities(),
            "source_surface": "curriculum/l2-uk-en/{track}/{slug}/module.md",
        },
        "results": results,
        "schema_version": SCHEMA_VERSION,
        "selection": {
            "modules": [f"{track}/{slug}" for track, slug in sorted(modules)],
            "slugs": sorted(slugs),
            "tracks": sorted(tracks),
        },
        "summary": {
            "analyzed_source_count": status_counts["analyzed"],
            "missing_source_count": status_counts["missing_source"],
            "no_ukrainian_text_count": status_counts["no_ukrainian_text"],
            "selected_source_count": len(results),
            "skipped_source_count": status_counts["skipped"],
        },
    }


def serialize_report(report: dict[str, Any]) -> str:
    """Serialize reports with explicit stable formatting and key ordering."""
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--curriculum-root",
        type=Path,
        default=DEFAULT_CURRICULUM_ROOT,
        help="Path to curriculum/l2-uk-en (defaults to this repository's source root).",
    )
    parser.add_argument("--track", action="append", default=[], help="Select every module in one source track.")
    parser.add_argument(
        "--slug",
        action="append",
        default=[],
        help="Select one slug within exactly one --track; may be repeated.",
    )
    parser.add_argument(
        "--module",
        action="append",
        type=_parse_module_selector,
        default=[],
        metavar="TRACK/SLUG",
        help="Select one exact source; may be repeated and cannot be mixed with --track/--slug.",
    )
    parser.add_argument("--output", type=Path, help="Write the JSON report to this file instead of stdout.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = build_report(
            args.curriculum_root,
            tracks=args.track,
            slugs=args.slug,
            modules=args.module,
        )
    except ValueError as error:
        build_parser().error(str(error))
    payload = serialize_report(report)
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
