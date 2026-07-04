#!/usr/bin/env python3
"""Curate a small UA-GEC gold fixture for the #2156 evaluation harness.

This command intentionally curates, rather than raw-extracts, from the local
UA-GEC clone and ``ua_gec_errors`` table. The filter constants below are
documented and surfaced in the emitted fixture so future maintainers can tune
the policy without guessing why rows were accepted or rejected.

Default curation policy:
- priority tags: ``F/Calque``, ``G/Case``, ``G/Gender``;
- priority order: Russian-source ``F/Calque`` first, then other ``F/Calque``,
  then Russian-source grammar tags, then other grammar rows;
- reject rows without recoverable annotated-file context;
- reject empty edits, duplicate error/correction/tag/source-language pairs,
  known context-stripped junk pairs, and short opaque single-token word forms;
- cap repeated rows from the same document/tag so one source text cannot
  dominate the gold fixture;
- cap the output at a small fixture size suitable for tests and review.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
import sys
from collections import Counter, defaultdict, deque
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
AUDIT_DIR = Path(__file__).resolve().parent
if str(AUDIT_DIR) not in sys.path:
    sys.path.insert(0, str(AUDIT_DIR))

import qg_schema
from _judge_eval_lib import CYRILLIC_TOKEN_RE, UA_GEC_ANN_RE

DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "sources.db"
DEFAULT_UA_GEC_ROOT = PROJECT_ROOT / "data" / "ua-gec"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "ua-gec-gold" / "ua-gec-gold.json"

TARGET_TAGS = ("F/Calque", "G/Case", "G/Gender")
DEFAULT_TAG_LIMITS = {
    "F/Calque": 32,
    "G/Case": 12,
    "G/Gender": 8,
}

MIN_CONTEXT_CHARS = 40
MIN_CONTEXT_TOKENS = 6
MAX_CONTEXT_CHARS = 260
CONTEXT_RADIUS_CHARS = 120
STANDALONE_UNCLEAR_MAX_CHARS = 4
MAX_ROWS_PER_DOC_TAG = 3

KNOWN_CONTEXT_STRIPPED_JUNK = frozenset(
    {
        ("F/Calque", "рожі", "мармизи"),
        ("F/Calque", "вдів", "одягнув"),
    }
)

SOURCE_LANG_FOR_SCHEMA = {
    "de": "other",
    "fr": "other",
    "uk": "unknown",
}


@dataclass(frozen=True, slots=True)
class UaGecCandidate:
    """One row from ``ua_gec_errors``."""

    id: int
    error: str
    correction: str
    tag: str
    doc_id: str
    annotator_id: str
    partition: str
    is_native: int | None
    raw_source_lang: str | None


@dataclass(frozen=True, slots=True)
class TextWindow:
    """A plain-text excerpt plus a span relative to that excerpt."""

    excerpt: str
    span: dict[str, int]


@dataclass(frozen=True, slots=True)
class AnnotationContext:
    """Context recovered from one UA-GEC annotated document."""

    source_excerpt: str
    corrected_excerpt: str
    source_span: dict[str, int]
    correction_span: dict[str, int]
    line: int


@dataclass(frozen=True, slots=True)
class ParsedAnnotation:
    """One in-text UA-GEC annotation with plain-source/target spans."""

    error: str
    correction: str
    tag: str
    source_start: int
    source_end: int
    target_start: int
    target_end: int
    line: int


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    """Plain source/target text plus all extracted annotation spans."""

    source_text: str
    target_text: str
    annotations: list[ParsedAnnotation]


@dataclass(frozen=True, slots=True)
class CurationConfig:
    """Tunable curation constants included in the fixture provenance."""

    min_context_chars: int = MIN_CONTEXT_CHARS
    min_context_tokens: int = MIN_CONTEXT_TOKENS
    max_context_chars: int = MAX_CONTEXT_CHARS
    context_radius_chars: int = CONTEXT_RADIUS_CHARS
    standalone_unclear_max_chars: int = STANDALONE_UNCLEAR_MAX_CHARS
    max_rows_per_doc_tag: int = MAX_ROWS_PER_DOC_TAG
    tag_limits: Mapping[str, int] | None = None

    def limits(self) -> dict[str, int]:
        return dict(self.tag_limits or DEFAULT_TAG_LIMITS)

    def fixture_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["tag_limits"] = self.limits()
        return out


@dataclass(frozen=True, slots=True)
class RejectedCandidate:
    """Rejected candidate id and reason for dry-run accounting."""

    candidate_id: int
    tag: str
    raw_source_lang: str | None
    reason: str


@dataclass(frozen=True, slots=True)
class CurationReport:
    """Kept fixture rows plus candidate/rejection counters."""

    total_candidates: int
    per_tag: Counter[str]
    per_source_lang: Counter[str]
    kept_rows: list[dict[str, Any]]
    rejected: list[RejectedCandidate]

    @property
    def rejection_reasons(self) -> Counter[str]:
        return Counter(item.reason for item in self.rejected)

    @property
    def kept_by_tag(self) -> Counter[str]:
        return Counter(str(row["tag"]) for row in self.kept_rows)


def _clean_source_lang(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _source_lang_bucket(value: str | None) -> str:
    return _clean_source_lang(value) or "unknown"


def _schema_source_lang(value: str | None) -> str | None:
    raw = _clean_source_lang(value)
    if raw is None:
        return None
    lower = raw.lower()
    if lower in SOURCE_LANG_FOR_SCHEMA:
        return SOURCE_LANG_FOR_SCHEMA[lower]
    try:
        return qg_schema.normalize_source_lang(lower)
    except ValueError:
        return "other"


def _annotation_key(
    *,
    partition: str,
    doc_id: str,
    annotator_id: str,
    tag: str,
    error: str,
    correction: str,
) -> tuple[str, str, str, str, str, str]:
    return (
        partition,
        doc_id,
        annotator_id,
        tag,
        _normalize_edit_text(error),
        _normalize_edit_text(correction),
    )


def _candidate_annotation_key(candidate: UaGecCandidate) -> tuple[str, str, str, str, str, str]:
    return _annotation_key(
        partition=candidate.partition,
        doc_id=candidate.doc_id,
        annotator_id=candidate.annotator_id,
        tag=candidate.tag,
        error=candidate.error,
        correction=candidate.correction,
    )


def _normalize_edit_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _token_count(text: str) -> int:
    return len(CYRILLIC_TOKEN_RE.findall(text))


def _single_token_max_chars(error: str, correction: str) -> int | None:
    error_tokens = CYRILLIC_TOKEN_RE.findall(error)
    correction_tokens = CYRILLIC_TOKEN_RE.findall(correction)
    if len(error_tokens) == 1 and len(correction_tokens) == 1:
        return max(len(error_tokens[0]), len(correction_tokens[0]))
    return None


def _trimmed_span(raw_text: str, base_start: int) -> tuple[str, int, int]:
    leading = len(raw_text) - len(raw_text.lstrip())
    stripped = raw_text.strip()
    return stripped, base_start + leading, base_start + leading + len(stripped)


def parse_annotated_text(text: str) -> ParsedDocument:
    """Parse UA-GEC inline annotations into source/target plain text spans."""
    source_parts: list[str] = []
    target_parts: list[str] = []
    annotations: list[ParsedAnnotation] = []
    last = 0
    source_pos = 0
    target_pos = 0

    for match in UA_GEC_ANN_RE.finditer(text):
        prefix = text[last:match.start()]
        source_parts.append(prefix)
        target_parts.append(prefix)
        source_pos += len(prefix)
        target_pos += len(prefix)

        raw_error = match.group(1)
        raw_correction = match.group(2)
        tag = match.group(3).strip()

        error, source_start, source_end = _trimmed_span(raw_error, source_pos)
        correction, target_start, target_end = _trimmed_span(raw_correction, target_pos)
        line = text.count("\n", 0, match.start()) + 1

        source_parts.append(raw_error)
        target_parts.append(raw_correction)
        source_pos += len(raw_error)
        target_pos += len(raw_correction)
        annotations.append(
            ParsedAnnotation(
                error=error,
                correction=correction,
                tag=tag,
                source_start=source_start,
                source_end=source_end,
                target_start=target_start,
                target_end=target_end,
                line=line,
            )
        )
        last = match.end()

    suffix = text[last:]
    source_parts.append(suffix)
    target_parts.append(suffix)
    return ParsedDocument(
        source_text="".join(source_parts),
        target_text="".join(target_parts),
        annotations=annotations,
    )


def _window_for_span(text: str, start: int, end: int, *, config: CurationConfig) -> TextWindow:
    left_candidates = [text.rfind(boundary, 0, start) for boundary in ".!?…\n"]
    left = max(left_candidates)
    left = 0 if left < 0 else left + 1

    right_candidates = [text.find(boundary, end) for boundary in ".!?…\n"]
    right_candidates = [pos for pos in right_candidates if pos >= 0]
    right = min(right_candidates) + 1 if right_candidates else len(text)

    if right - left > config.max_context_chars:
        left = max(0, start - config.context_radius_chars)
        right = min(len(text), end + config.context_radius_chars)

    raw_excerpt = text[left:right]
    leading_trim = len(raw_excerpt) - len(raw_excerpt.lstrip())
    excerpt = raw_excerpt.strip()
    span_start = start - left - leading_trim
    span_end = end - left - leading_trim
    return TextWindow(
        excerpt=excerpt,
        span={"start": max(0, span_start), "end": max(0, span_end)},
    )


def _context_for_annotation(
    parsed: ParsedDocument,
    annotation: ParsedAnnotation,
    *,
    config: CurationConfig,
) -> AnnotationContext:
    source_window = _window_for_span(
        parsed.source_text,
        annotation.source_start,
        annotation.source_end,
        config=config,
    )
    target_window = _window_for_span(
        parsed.target_text,
        annotation.target_start,
        annotation.target_end,
        config=config,
    )
    return AnnotationContext(
        source_excerpt=source_window.excerpt,
        corrected_excerpt=target_window.excerpt,
        source_span=source_window.span,
        correction_span=target_window.span,
        line=annotation.line,
    )


def annotation_path(root: Path, candidate: UaGecCandidate) -> Path:
    """Return the expected annotated-file path for a DB row."""
    return (
        root
        / "data"
        / candidate.partition
        / "annotated"
        / f"{candidate.doc_id}.a{candidate.annotator_id}.ann"
    )


def load_annotation_contexts(
    ua_gec_root: Path,
    candidates: Sequence[UaGecCandidate],
    *,
    config: CurationConfig,
) -> dict[tuple[str, str, str, str, str, str], deque[AnnotationContext]]:
    """Load needed annotated documents and index contexts by edit tuple."""
    candidate_paths = {annotation_path(ua_gec_root, candidate) for candidate in candidates}
    contexts: dict[tuple[str, str, str, str, str, str], deque[AnnotationContext]] = defaultdict(deque)

    for ann_path in sorted(candidate_paths):
        if not ann_path.exists():
            continue
        try:
            rel = ann_path.relative_to(ua_gec_root / "data")
        except ValueError:
            continue
        if len(rel.parts) < 4:
            continue
        partition = f"{rel.parts[0]}/{rel.parts[1]}"
        stem_match = re.fullmatch(r"(?P<doc_id>[^.]+)\.a(?P<annotator_id>\d+)", ann_path.stem)
        if stem_match is None:
            continue

        parsed = parse_annotated_text(ann_path.read_text(encoding="utf-8", errors="replace"))
        for annotation in parsed.annotations:
            key = _annotation_key(
                partition=partition,
                doc_id=stem_match.group("doc_id"),
                annotator_id=stem_match.group("annotator_id"),
                tag=annotation.tag,
                error=annotation.error,
                correction=annotation.correction,
            )
            contexts[key].append(_context_for_annotation(parsed, annotation, config=config))
    return contexts


def load_candidates(db_path: Path, *, tags: Sequence[str] = TARGET_TAGS) -> list[UaGecCandidate]:
    """Load relevant rows from the local ``ua_gec_errors`` table."""
    if not db_path.exists():
        raise FileNotFoundError(f"UA-GEC sources database not found: {db_path}")

    placeholders = ",".join("?" for _ in tags)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"""
            SELECT id, error, correct, error_type, doc_id, annotator_id,
                   partition, is_native, source_lang
            FROM ua_gec_errors
            WHERE error_type IN ({placeholders})
            ORDER BY
                CASE
                    WHEN error_type = 'F/Calque' AND source_lang = 'ru' THEN 0
                    WHEN error_type = 'F/Calque' THEN 1
                    WHEN error_type = 'G/Case' AND source_lang = 'ru' THEN 2
                    WHEN error_type = 'G/Case' THEN 3
                    WHEN error_type = 'G/Gender' AND source_lang = 'ru' THEN 4
                    ELSE 5
                END,
                id
            """,
            tuple(tags),
        ).fetchall()
    finally:
        conn.close()

    return [
        UaGecCandidate(
            id=int(row["id"]),
            error=str(row["error"]),
            correction=str(row["correct"]),
            tag=str(row["error_type"]),
            doc_id=str(row["doc_id"]),
            annotator_id=str(row["annotator_id"]),
            partition=str(row["partition"]),
            is_native=None if row["is_native"] is None else int(row["is_native"]),
            raw_source_lang=_clean_source_lang(row["source_lang"]),
        )
        for row in rows
    ]


def _first_rejection_reason(
    candidate: UaGecCandidate,
    context: AnnotationContext | None,
    *,
    config: CurationConfig,
) -> str | None:
    error = _normalize_edit_text(candidate.error)
    correction = _normalize_edit_text(candidate.correction)
    if not error:
        return "empty_error"
    if not correction:
        return "empty_correction"
    if (candidate.tag, error, correction) in KNOWN_CONTEXT_STRIPPED_JUNK:
        return "known_context_stripped_junk"
    single_token_chars = _single_token_max_chars(error, correction)
    if single_token_chars is not None and single_token_chars <= config.standalone_unclear_max_chars:
        return "too_short_single_word_form"
    if context is None:
        return "missing_annotated_context"
    if len(context.source_excerpt) < config.min_context_chars:
        return "context_too_short_chars"
    if _token_count(context.source_excerpt) < config.min_context_tokens:
        return "context_too_short_tokens"
    span = context.source_span
    if context.source_excerpt[span["start"] : span["end"]] != error:
        return "span_mismatch"
    return None


def _pair_key(candidate: UaGecCandidate) -> tuple[str, str, str, str]:
    return (
        candidate.tag,
        _normalize_edit_text(candidate.error).lower(),
        _normalize_edit_text(candidate.correction).lower(),
        _source_lang_bucket(candidate.raw_source_lang),
    )


def build_fixture_row(candidate: UaGecCandidate, context: AnnotationContext, *, index: int) -> dict[str, Any]:
    """Build one fixture row with the canonical #2156 finding embedded."""
    schema_source = _schema_source_lang(candidate.raw_source_lang)
    mapped = qg_schema.map_ua_gec_tag(candidate.tag, source_lang=schema_source)
    pair_id = f"ua-gec-errors:{candidate.id}"
    file_ref = f"ua-gec/{candidate.partition}/annotated/{candidate.doc_id}.a{candidate.annotator_id}.ann"
    finding = qg_schema.build_ua_gec_finding(
        error=_normalize_edit_text(candidate.error),
        correction=_normalize_edit_text(candidate.correction),
        tag=candidate.tag,
        source_lang=schema_source,
        file=file_ref,
        line=context.line,
        span=context.source_span,
        doc_id=candidate.doc_id,
        pair_id=pair_id,
        adapter="ua_gec_gold_ingest",
    )
    qg_schema.validate_finding(finding)
    return {
        "id": f"ua-gec-gold-{index:03d}",
        "ua_gec_error_id": candidate.id,
        "tag": candidate.tag,
        "mapped_tag": mapped,
        "error": _normalize_edit_text(candidate.error),
        "correction": _normalize_edit_text(candidate.correction),
        "source_lang": finding["source_lang"],
        "raw_source_lang": candidate.raw_source_lang,
        "doc_id": candidate.doc_id,
        "annotator_id": candidate.annotator_id,
        "partition": candidate.partition,
        "is_native": None if candidate.is_native is None else bool(candidate.is_native),
        "source_excerpt": context.source_excerpt,
        "corrected_excerpt": context.corrected_excerpt,
        "spans": {
            "source": context.source_span,
            "correction": context.correction_span,
        },
        "finding": finding,
    }


def curate_candidates(
    candidates: Sequence[UaGecCandidate],
    contexts: Mapping[tuple[str, str, str, str, str, str], deque[AnnotationContext]],
    *,
    config: CurationConfig,
) -> CurationReport:
    """Apply deterministic curation filters and fixture-size caps."""
    tag_limits = config.limits()
    seen_pairs: set[tuple[str, str, str, str]] = set()
    kept_by_tag: Counter[str] = Counter()
    kept_by_doc_tag: Counter[tuple[str, str]] = Counter()
    kept_rows: list[dict[str, Any]] = []
    rejected: list[RejectedCandidate] = []
    per_tag = Counter(candidate.tag for candidate in candidates)
    per_source_lang = Counter(_source_lang_bucket(candidate.raw_source_lang) for candidate in candidates)

    context_queues = {key: deque(value) for key, value in contexts.items()}
    for candidate in candidates:
        context = None
        queue = context_queues.get(_candidate_annotation_key(candidate))
        if queue:
            context = queue.popleft()

        reason = None
        pair_key = _pair_key(candidate)
        if pair_key in seen_pairs:
            reason = "duplicate_pair"
        else:
            reason = _first_rejection_reason(candidate, context, config=config)

        if reason is None and kept_by_doc_tag[(candidate.tag, candidate.doc_id)] >= config.max_rows_per_doc_tag:
            reason = "doc_tag_limit_reached"

        if reason is None and kept_by_tag[candidate.tag] >= tag_limits.get(candidate.tag, 0):
            reason = "tag_limit_reached"

        if reason is not None:
            rejected.append(
                RejectedCandidate(
                    candidate_id=candidate.id,
                    tag=candidate.tag,
                    raw_source_lang=candidate.raw_source_lang,
                    reason=reason,
                )
            )
            continue

        if context is None:
            rejected.append(
                RejectedCandidate(
                    candidate_id=candidate.id,
                    tag=candidate.tag,
                    raw_source_lang=candidate.raw_source_lang,
                    reason="missing_annotated_context",
                )
            )
            continue

        seen_pairs.add(pair_key)
        kept_by_tag[candidate.tag] += 1
        kept_by_doc_tag[(candidate.tag, candidate.doc_id)] += 1
        kept_rows.append(build_fixture_row(candidate, context, index=len(kept_rows) + 1))

    return CurationReport(
        total_candidates=len(candidates),
        per_tag=per_tag,
        per_source_lang=per_source_lang,
        kept_rows=kept_rows,
        rejected=rejected,
    )


def run_curation(
    *,
    db_path: Path,
    ua_gec_root: Path,
    config: CurationConfig,
) -> CurationReport:
    candidates = load_candidates(db_path)
    contexts = load_annotation_contexts(ua_gec_root, candidates, config=config)
    return curate_candidates(candidates, contexts, config=config)


def source_commit(ua_gec_root: Path) -> str:
    """Return the local UA-GEC git commit, or ``unknown`` if unavailable."""
    proc = subprocess.run(
        ["git", "-C", str(ua_gec_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return "unknown"
    return proc.stdout.strip() or "unknown"


def source_version(ua_gec_root: Path) -> str:
    readme = ua_gec_root / "README.md"
    if not readme.exists():
        return "unknown"
    text = readme.read_text(encoding="utf-8", errors="replace")
    if "Version 2.0 released" in text:
        return "2.0"
    return "unknown"


def attribution_block(ua_gec_root: Path, *, retrieval_date: str) -> dict[str, Any]:
    """Build top-level CC-BY-4.0 attribution and source provenance."""
    return {
        "dataset": "UA-GEC",
        "source": "grammarly/ua-gec",
        "repository": "https://github.com/grammarly/ua-gec",
        "license": "CC BY 4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "citation": "Syvokon et al., UNLP 2023",
        "retrieval_date": retrieval_date,
        "source_commit": source_commit(ua_gec_root),
        "source_version": source_version(ua_gec_root),
    }


def build_fixture(
    report: CurationReport,
    *,
    ua_gec_root: Path,
    retrieval_date: str,
    config: CurationConfig,
) -> dict[str, Any]:
    """Assemble the tracked gold fixture JSON."""
    return {
        "fixture_id": "ua-gec-gold-small-v1",
        "schema_version": "ua_gec_gold_fixture.v1",
        "evidence_schema_version": qg_schema.SCHEMA_VERSION,
        "attribution": attribution_block(ua_gec_root, retrieval_date=retrieval_date),
        "curation": {
            "mode": "curated_not_raw_extract",
            "target_tags": list(TARGET_TAGS),
            "filter_constants": config.fixture_dict(),
            "known_context_stripped_junk": [
                {"tag": tag, "error": error, "correction": correction}
                for tag, error, correction in sorted(KNOWN_CONTEXT_STRIPPED_JUNK)
            ],
            "rejection_reasons": dict(sorted(report.rejection_reasons.items())),
        },
        "counts": {
            "total_candidates": report.total_candidates,
            "kept": len(report.kept_rows),
            "rejected": len(report.rejected),
            "per_tag": dict(sorted(report.per_tag.items())),
            "per_source_lang": dict(sorted(report.per_source_lang.items())),
            "kept_by_tag": dict(sorted(report.kept_by_tag.items())),
        },
        "items": report.kept_rows,
    }


def write_fixture(path: Path, fixture: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def format_report(report: CurationReport, *, output_path: Path | None = None, dry_run: bool) -> str:
    lines = [
        "UA-GEC gold ingestion summary",
        f"total candidates: {report.total_candidates}",
        "per tag:",
    ]
    for tag in TARGET_TAGS:
        lines.append(f"  {tag}: {report.per_tag.get(tag, 0)}")
    lines.append("per source_lang:")
    for source_lang, count in sorted(report.per_source_lang.items()):
        lines.append(f"  {source_lang}: {count}")
    lines.append(f"curated: {len(report.kept_rows)} kept / {len(report.rejected)} rejected")
    lines.append("kept by tag:")
    for tag in TARGET_TAGS:
        lines.append(f"  {tag}: {report.kept_by_tag.get(tag, 0)}")
    lines.append("rejected by reason:")
    for reason, count in sorted(report.rejection_reasons.items()):
        lines.append(f"  {reason}: {count}")
    if dry_run:
        lines.append("dry-run: no files written")
    elif output_path is not None:
        lines.append(f"wrote: {output_path}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH, help="Path to data/sources.db.")
    parser.add_argument(
        "--ua-gec-root",
        type=Path,
        default=DEFAULT_UA_GEC_ROOT,
        help="Path to the local grammarly/ua-gec clone.",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Fixture JSON path.")
    parser.add_argument("--dry-run", action="store_true", help="Print curation counts and write nothing.")
    parser.add_argument(
        "--retrieval-date",
        default=datetime.now(UTC).date().isoformat(),
        help="YYYY-MM-DD date for attribution.",
    )
    parser.add_argument("--f-calque-limit", type=int, default=DEFAULT_TAG_LIMITS["F/Calque"])
    parser.add_argument("--g-case-limit", type=int, default=DEFAULT_TAG_LIMITS["G/Case"])
    parser.add_argument("--g-gender-limit", type=int, default=DEFAULT_TAG_LIMITS["G/Gender"])
    parser.add_argument("--min-context-chars", type=int, default=MIN_CONTEXT_CHARS)
    parser.add_argument("--min-context-tokens", type=int, default=MIN_CONTEXT_TOKENS)
    parser.add_argument("--standalone-unclear-max-chars", type=int, default=STANDALONE_UNCLEAR_MAX_CHARS)
    parser.add_argument("--max-rows-per-doc-tag", type=int, default=MAX_ROWS_PER_DOC_TAG)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = CurationConfig(
        min_context_chars=args.min_context_chars,
        min_context_tokens=args.min_context_tokens,
        standalone_unclear_max_chars=args.standalone_unclear_max_chars,
        max_rows_per_doc_tag=args.max_rows_per_doc_tag,
        tag_limits={
            "F/Calque": args.f_calque_limit,
            "G/Case": args.g_case_limit,
            "G/Gender": args.g_gender_limit,
        },
    )
    report = run_curation(db_path=args.db_path, ua_gec_root=args.ua_gec_root, config=config)
    if args.dry_run:
        print(format_report(report, dry_run=True))
        return 0

    fixture = build_fixture(
        report,
        ua_gec_root=args.ua_gec_root,
        retrieval_date=args.retrieval_date,
        config=config,
    )
    write_fixture(args.output, fixture)
    print(format_report(report, output_path=args.output, dry_run=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
