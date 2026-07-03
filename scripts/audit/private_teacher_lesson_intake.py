#!/usr/bin/env python3
"""Local-only full-source intake for private teacher-lesson Atlas candidates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if sys.path and Path(sys.path[0]).resolve() == SCRIPT_DIR:
    sys.path.pop(0)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit.atlas_intake_gate import (
    AtlasIntakeGateResult,
    classification_counts,
    classify_candidates,
)
from scripts.audit.source_inventory_intake import (
    SourceInventoryCandidate,
    SourceInventoryError,
    SourceInventoryRecord,
    source_inventory_candidates,
)
from scripts.lexicon.build_data_manifest import _lemma_key
from scripts.lexicon.lemma_normalization import strip_acute_stress

WORKFLOW_ID = "private_teacher_lesson_full_intake.v1"
BULK_TRIAGE_WORKFLOW_ID = "private_teacher_lesson_bulk_triage.v1"
SOURCE_FAMILY = "teacher_lesson"
EXTRACTION_MODE = "private_document_token"
DEFAULT_SOURCE_ID = "private-teacher-lesson-full-source"
DEFAULT_SOURCE_TITLE = "Private teacher lesson source"
DEFAULT_CANDIDATES_OUT = Path("/tmp/atlas-private-teacher-lesson-candidates.json")
DEFAULT_BULK_TRIAGE_OUT = Path("/tmp/atlas-private-teacher-lesson-bulk-triage.json")
DEFAULT_BULK_TRIAGE_REPORT_OUT = Path("/tmp/atlas-private-teacher-lesson-bulk-triage.md")
SUPPORTED_SUFFIXES = {".csv", ".docx", ".md", ".txt", ".tsv", ".xlsx"}
OMITTED_PUBLIC_FIELDS = (
    "raw_text",
    "source_path",
    "source_filename",
    "source_title_from_file",
    "tab_or_sheet_name",
    "context",
    "gloss",
    "notes",
)
TRIAGE_BUCKETS = (
    "atlas_existing",
    "committed_teacher_inventory",
    "low_signal_hold",
    "post_boundary_table_missing",
    "high_frequency_missing",
    "needs_review_bulk",
)
LOW_SIGNAL_LEMMAS = frozenset(
    {
        "або",
        "але",
        "без",
        "би",
        "в",
        "ви",
        "він",
        "вона",
        "вони",
        "для",
        "до",
        "ж",
        "же",
        "з",
        "за",
        "й",
        "його",
        "її",
        "і",
        "на",
        "над",
        "не",
        "ні",
        "під",
        "по",
        "при",
        "про",
        "та",
        "так",
        "то",
        "у",
        "це",
        "цей",
        "чи",
        "що",
        "як",
    }
)
UKRAINIAN_TOKEN_RE = re.compile(
    r"[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]+(?:[ʼ'’`-][А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]+)*"
)
SOURCE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]*$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ROW_LOCATOR_RE = re.compile(r"\brow\s+(\d+)\b")

WORD_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
SHEET_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PKG_REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"


@dataclass(frozen=True)
class PrivateSourceUnit:
    """One top-level private source unit, without its private title/name."""

    source_ref: str
    source_suffix: str
    unit_index: int
    unit_kind: str
    ignored: bool
    shape_signature: str = ""


@dataclass(frozen=True)
class PrivateSourceBlock:
    """One included private source text block, kept local-only."""

    source_ref: str
    source_suffix: str
    unit_index: int
    unit_kind: str
    block_index: int
    locator: str
    text: str
    row_index: int | None = None


@dataclass(frozen=True)
class LoadedPrivateSource:
    """Private source blocks plus safe unit metadata."""

    units: tuple[PrivateSourceUnit, ...]
    blocks: tuple[PrivateSourceBlock, ...]


@dataclass(frozen=True)
class PrivateTeacherIntakeResult:
    """Full local-only intake result, including safe public census."""

    census: Mapping[str, Any]
    candidates: tuple[SourceInventoryCandidate, ...]
    gate_results: tuple[AtlasIntakeGateResult, ...]
    manifest_keys: frozenset[str]
    manifest_sha256: str | None
    source_shape: Mapping[str, Any]


def build_private_teacher_lesson_intake(
    source_paths: Sequence[Path],
    *,
    ignored_tab_indexes: Sequence[int] = (),
    ignored_unit_indexes: Sequence[int] = (),
    source_id: str = DEFAULT_SOURCE_ID,
    source_shape_id: str = DEFAULT_SOURCE_ID,
    expected_source_shape_sha256: str | None = None,
    manifest_path: Path | None = None,
) -> PrivateTeacherIntakeResult:
    """Extract local private text into safe derived candidate/census metadata."""
    if not source_paths:
        raise SourceInventoryError("at least one private source path is required")
    _validate_positive_indexes(ignored_tab_indexes, "--ignore-tab-index")
    _validate_positive_indexes(ignored_unit_indexes, "--ignore-unit-index")
    _validate_source_id(source_id)
    _validate_source_id(source_shape_id)
    ignored_indexes = tuple(sorted(set(ignored_tab_indexes) | set(ignored_unit_indexes)))
    source_shape = inspect_private_source_shape(source_paths, source_shape_id=source_shape_id)
    _validate_source_shape_expectation(
        source_shape,
        expected_source_shape_sha256=expected_source_shape_sha256,
        ignored_indexes=ignored_indexes,
    )

    records: list[SourceInventoryRecord] = []
    units: list[PrivateSourceUnit] = []
    blocks: list[PrivateSourceBlock] = []
    source_files: list[dict[str, Any]] = []
    by_kind: dict[str, Counter[str]] = defaultdict(Counter)
    token_occurrences = 0

    for source_number, source_path in enumerate(source_paths, start=1):
        source_ref = f"private-source-{source_number}"
        numbered_source_id = source_id if len(source_paths) == 1 else f"{source_id}-{source_number}"
        loaded = load_private_source(
            source_path,
            source_ref=source_ref,
            ignored_unit_indexes=ignored_indexes,
        )
        source_units = list(loaded.units)
        source_blocks = list(loaded.blocks)
        units.extend(source_units)
        blocks.extend(source_blocks)

        source_records, source_token_occurrences = _records_from_blocks(
            source_blocks,
            source_id=numbered_source_id,
        )
        records.extend(source_records)
        token_occurrences += source_token_occurrences
        _count_source_kinds(source_units, source_blocks, by_kind=by_kind)
        source_files.append(
            _source_file_payload(
                source_ref=source_ref,
                suffix=source_path.suffix.lower(),
                units=source_units,
                blocks=source_blocks,
                token_occurrences=source_token_occurrences,
            )
        )

    candidates = tuple(source_inventory_candidates(records))
    gate_results = tuple(classify_candidates(candidates))
    manifest_keys, manifest_sha256 = _load_manifest(manifest_path)
    atlas_state_counts = _atlas_state_counts(candidates, manifest_keys=manifest_keys)
    census = _census_payload(
        source_files=source_files,
        source_shape=source_shape,
        units=units,
        blocks=blocks,
        records=records,
        candidates=candidates,
        gate_results=gate_results,
        manifest_loaded=manifest_path is not None and bool(manifest_keys),
        manifest_sha256=manifest_sha256,
        atlas_state_counts=atlas_state_counts,
        token_occurrences=token_occurrences,
        ignored_tab_indexes=ignored_tab_indexes,
        ignored_unit_indexes=ignored_unit_indexes,
        by_kind=by_kind,
    )
    return PrivateTeacherIntakeResult(
        census=census,
        candidates=candidates,
        gate_results=gate_results,
        manifest_keys=manifest_keys,
        manifest_sha256=manifest_sha256,
        source_shape=source_shape,
    )


def inspect_private_source_shape(
    source_paths: Sequence[Path],
    *,
    source_shape_id: str = DEFAULT_SOURCE_ID,
) -> dict[str, Any]:
    """Return a safe structure checksum for private source binding."""
    if not source_paths:
        raise SourceInventoryError("at least one private source path is required")
    _validate_source_id(source_shape_id)

    sources_for_digest: list[dict[str, Any]] = []
    source_files: list[dict[str, Any]] = []
    by_kind: Counter[str] = Counter()
    units_seen = 0
    for source_number, source_path in enumerate(source_paths, start=1):
        source_ref = f"private-source-{source_number}"
        units = _load_private_source_shape(source_path, source_ref=source_ref)
        units_seen += len(units)
        by_kind.update(unit.unit_kind for unit in units)
        source_files.append(
            {
                "source_ref": source_ref,
                "source_suffix": units[0].source_suffix if units else source_path.suffix.lower(),
                "units_seen": len(units),
                "unit_kinds": dict(sorted(Counter(unit.unit_kind for unit in units).items())),
            }
        )
        sources_for_digest.append(
            {
                "source_ref": source_ref,
                "units": [
                    {
                        "unit_index": unit.unit_index,
                        "unit_kind": unit.unit_kind,
                        "source_suffix": unit.source_suffix,
                        "shape_signature": unit.shape_signature,
                    }
                    for unit in units
                ],
            }
        )

    digest_payload = {
        "source_shape_id": source_shape_id,
        "sources": sources_for_digest,
    }
    source_shape_sha256 = hashlib.sha256(
        json.dumps(digest_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {
        "source_shape_id": source_shape_id,
        "source_shape_sha256": source_shape_sha256,
        "source_files": len(source_paths),
        "units_seen": units_seen,
        "by_unit_kind": dict(sorted(by_kind.items())),
        "public_boundary": (
            "This checksum binds the source unit structure before ignored-unit scans. "
            "It does not expose source paths, names, tab labels, or source text."
        ),
    }


def load_private_source(
    source_path: Path,
    *,
    source_ref: str,
    ignored_unit_indexes: Sequence[int],
) -> LoadedPrivateSource:
    """Load supported private source files without exposing names in payloads."""
    path = _resolve_private_source_path(source_path)
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return _load_docx(path, source_ref=source_ref, ignored_unit_indexes=set(ignored_unit_indexes))
    if suffix == ".xlsx":
        return _load_xlsx(path, source_ref=source_ref, ignored_unit_indexes=set(ignored_unit_indexes))
    if suffix in {".csv", ".tsv"}:
        delimiter = "," if suffix == ".csv" else "\t"
        return _load_delimited(
            path,
            source_ref=source_ref,
            ignored_unit_indexes=set(ignored_unit_indexes),
            delimiter=delimiter,
        )
    return _load_text(path, source_ref=source_ref, ignored_unit_indexes=set(ignored_unit_indexes))


def _load_private_source_shape(source_path: Path, *, source_ref: str) -> tuple[PrivateSourceUnit, ...]:
    """Load private source unit structure without extracting candidate text."""
    path = _resolve_private_source_path(source_path)
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return _load_docx_shape(path, source_ref=source_ref)
    if suffix == ".xlsx":
        return _load_xlsx_shape(path, source_ref=source_ref)
    if suffix in {".csv", ".tsv"}:
        delimiter = "," if suffix == ".csv" else "\t"
        return _load_delimited_shape(path, source_ref=source_ref, delimiter=delimiter)
    return _load_text_shape(path, source_ref=source_ref)


def _resolve_private_source_path(source_path: Path) -> Path:
    path = source_path if source_path.is_absolute() else PROJECT_ROOT / source_path
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise SourceInventoryError(
            f"unsupported private source extension {suffix!r}; expected one of {sorted(SUPPORTED_SUFFIXES)}"
        )
    if not path.exists():
        raise SourceInventoryError("private source path not found")
    return path


def candidate_review_payload(result: PrivateTeacherIntakeResult) -> dict[str, Any]:
    """Return derived candidate metadata suitable only for local review output."""
    by_lemma = {gate_result.lemma: gate_result for gate_result in result.gate_results}
    candidate_rows: list[dict[str, Any]] = []
    for candidate in result.candidates:
        gate_result = by_lemma[candidate.lemma]
        row = gate_result.candidate_payload()
        row["atlas_state"] = _atlas_state(candidate.lemma, manifest_keys=result.manifest_keys)
        candidate_rows.append(row)
    return {
        "workflow": WORKFLOW_ID,
        "policy": (
            "Local review-only candidate payload. It contains derived headword metadata "
            "and neutral locators, but no raw private source text, filenames, tab names, "
            "document paths, or learner-surface admission."
        ),
        "production_outputs_updated": [],
        "safety": result.census["safety"],
        "counts": {
            **result.census["counts"],
            "candidate_rows": len(candidate_rows),
        },
        "gate": result.census["gate"],
        "atlas": result.census["atlas"],
        "candidates": candidate_rows,
    }


def write_candidate_review_payload(
    result: PrivateTeacherIntakeResult,
    out: Path = DEFAULT_CANDIDATES_OUT,
) -> Path:
    """Write local candidate metadata outside the repository."""
    output_path = resolve_local_review_output_path(out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(candidate_review_payload(result), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def build_bulk_triage_payload(
    result: PrivateTeacherIntakeResult,
    *,
    committed_inventory_paths: Sequence[Path] | None = None,
    min_frequency: int = 3,
    post_boundary_row: int = 218,
) -> dict[str, Any]:
    """Classify the full local candidate queue into disjoint review buckets."""
    if min_frequency < 1:
        raise SourceInventoryError("--min-frequency must be positive")
    if post_boundary_row < 0:
        raise SourceInventoryError("--post-boundary-row must be non-negative")

    committed_teacher_keys = _committed_teacher_inventory_keys(committed_inventory_paths)
    buckets: dict[str, list[dict[str, Any]]] = {bucket: [] for bucket in TRIAGE_BUCKETS}
    for candidate in result.candidates:
        bucket, reasons = _bulk_triage_bucket(
            candidate,
            result=result,
            committed_teacher_keys=committed_teacher_keys,
            min_frequency=min_frequency,
            post_boundary_row=post_boundary_row,
        )
        row = _bulk_triage_row(candidate, result=result, bucket=bucket, reasons=reasons)
        buckets[bucket].append(row)

    for rows in buckets.values():
        rows.sort(key=_bulk_triage_sort_key)
    counts = {bucket: len(buckets[bucket]) for bucket in TRIAGE_BUCKETS}
    total = len(result.candidates)
    if sum(counts.values()) != total:
        raise SourceInventoryError("bulk triage buckets must be disjoint and exhaustive")

    return {
        "workflow": BULK_TRIAGE_WORKFLOW_ID,
        "policy": (
            "Local review-only bulk triage. Detailed rows contain derived lemmas and neutral locators, "
            "so this payload must stay outside the repository. Public updates may share only counts."
        ),
        "production_outputs_updated": [],
        "source_shape": result.source_shape,
        "atlas": result.census["atlas"],
        "parameters": {
            "min_frequency": min_frequency,
            "post_boundary_row": post_boundary_row,
        },
        "counts": {
            "total_candidates": total,
            **counts,
            "bucket_total": sum(counts.values()),
        },
        "buckets": buckets,
    }


def bulk_triage_public_summary(triage: Mapping[str, Any]) -> dict[str, Any]:
    """Return the deny-by-default public portion of a bulk triage payload."""
    return {
        "workflow": triage["workflow"],
        "production_outputs_updated": [],
        "parameters": dict(triage["parameters"]),
        "counts": dict(triage["counts"]),
    }


def write_bulk_triage_payload(
    triage: Mapping[str, Any],
    out: Path = DEFAULT_BULK_TRIAGE_OUT,
) -> Path:
    """Write local bulk triage JSON outside the repository."""
    output_path = resolve_local_review_output_path(out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(triage, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def write_bulk_triage_report(
    triage: Mapping[str, Any],
    out: Path = DEFAULT_BULK_TRIAGE_REPORT_OUT,
    *,
    report_limit: int = 200,
) -> Path:
    """Write a local Markdown triage report outside the repository."""
    output_path = resolve_local_review_output_path(out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        format_bulk_triage_report(triage, report_limit=report_limit) + "\n",
        encoding="utf-8",
    )
    return output_path


def resolve_local_review_output_path(out: Path) -> Path:
    """Reject repository paths for local private-source candidate output."""
    output_path = out if out.is_absolute() else PROJECT_ROOT / out
    resolved = output_path.resolve()
    if resolved.is_relative_to(PROJECT_ROOT.resolve()):
        raise SourceInventoryError("private-source candidate output must be written outside the repository")
    return resolved


def format_bulk_triage_report(triage: Mapping[str, Any], *, report_limit: int = 200) -> str:
    """Format detailed local-only triage rows for human review."""
    if report_limit < 1:
        raise SourceInventoryError("--report-limit must be positive")
    counts = triage["counts"]
    lines = [
        "# Private Teacher-Lesson Bulk Triage",
        "",
        f"- workflow: `{triage['workflow']}`",
        f"- total_candidates: {counts['total_candidates']}",
        "- production_outputs_updated: []",
        "",
        "## Bucket Counts",
        "",
    ]
    for bucket in TRIAGE_BUCKETS:
        lines.append(f"- `{bucket}`: {counts[bucket]}")
    lines.extend(["", "## Bucket Samples", ""])
    buckets = triage.get("buckets") if isinstance(triage.get("buckets"), Mapping) else {}
    for bucket in TRIAGE_BUCKETS:
        rows = buckets.get(bucket) if isinstance(buckets, Mapping) else None
        rows = rows if isinstance(rows, list) else []
        lines.extend([f"### {bucket}", ""])
        if not rows:
            lines.extend(["- no rows", ""])
            continue
        for row in rows[:report_limit]:
            lines.append(
                "- "
                + "; ".join(
                    [
                        f"lemma={_markdown_inline(row.get('lemma'))}",
                        f"frequency={row.get('frequency', 0)}",
                        f"source_count={row.get('source_count', 0)}",
                        f"atlas_state={_markdown_inline(row.get('atlas_state'))}",
                        f"reasons={_markdown_inline(','.join(row.get('reasons', [])))}",
                    ]
                )
            )
        if len(rows) > report_limit:
            lines.append(f"- ... {len(rows) - report_limit} additional rows omitted from Markdown report")
        lines.append("")
    return "\n".join(lines).rstrip()


def format_markdown_census(
    census: Mapping[str, Any],
    *,
    bulk_triage: Mapping[str, Any] | None = None,
) -> str:
    """Format a safe census summary without lemmas or private source labels."""
    counts = census["counts"]
    atlas = census["atlas"]
    lines = [
        "# Private Teacher-Lesson Full-Source Census",
        "",
        f"- workflow: `{census['workflow']}`",
        f"- source_files: {counts['source_files']}",
        f"- units_seen: {counts['units_seen']}",
        f"- units_included: {counts['units_included']}",
        f"- units_ignored: {counts['units_ignored']}",
        f"- text_blocks_scanned: {counts['text_blocks_scanned']}",
        f"- token_occurrences: {counts['token_occurrences']}",
        f"- deduped_candidates: {counts['deduped_candidates']}",
        f"- max_source_row_index: {counts['max_source_row_index']}",
        f"- source_rows_after_218: {counts['source_rows_after_218']}",
        f"- atlas_manifest_loaded: {str(atlas['manifest_loaded']).lower()}",
        f"- atlas_manifest_sha256: {atlas.get('manifest_sha256') or 'none'}",
        f"- atlas_existing_candidates: {atlas['existing_candidates']}",
        f"- atlas_missing_candidates: {atlas['missing_candidates']}",
        f"- source_shape_sha256: {census['source_shape']['source_shape_sha256']}",
        "- raw_text_included: false",
        "- source_paths_included: false",
        "- production_outputs_updated: []",
        "",
        "## Gate Counts",
        "",
    ]
    gate_counts = census["gate"]["classification_counts"]
    lines.extend(f"- `{key}`: {gate_counts[key]}" for key in sorted(gate_counts))
    lines.extend(["", "## Source Units", ""])
    for kind, row in census["by_unit_kind"].items():
        lines.append(
            f"- `{kind}`: units={row['units']} blocks={row['text_blocks']} "
            f"tokens={row['token_occurrences']}"
        )
    if bulk_triage:
        counts = bulk_triage["counts"]
        lines.extend(["", "## Bulk Triage Counts", ""])
        lines.append(f"- workflow: `{bulk_triage['workflow']}`")
        lines.append(f"- total_candidates: {counts['total_candidates']}")
        for bucket in TRIAGE_BUCKETS:
            lines.append(f"- `{bucket}`: {counts[bucket]}")
    return "\n".join(lines)


def public_census_payload(
    result: PrivateTeacherIntakeResult,
    *,
    bulk_triage: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return public-safe census JSON, optionally with count-only triage data."""
    payload = dict(result.census)
    if bulk_triage:
        payload["bulk_triage"] = bulk_triage_public_summary(bulk_triage)
    return payload


def _bulk_triage_bucket(
    candidate: SourceInventoryCandidate,
    *,
    result: PrivateTeacherIntakeResult,
    committed_teacher_keys: frozenset[str],
    min_frequency: int,
    post_boundary_row: int,
) -> tuple[str, list[str]]:
    atlas_state = _atlas_state(candidate.lemma, manifest_keys=result.manifest_keys)
    if atlas_state == "existing":
        return "atlas_existing", ["lemma_already_in_atlas_manifest"]

    lemma_key = _lemma_key(candidate.lemma)
    if lemma_key in committed_teacher_keys:
        return "committed_teacher_inventory", ["lemma_already_in_committed_teacher_inventory"]

    if _low_signal_candidate(candidate):
        return "low_signal_hold", ["low_signal_or_function_word"]

    max_row = _candidate_max_source_row(candidate)
    if max_row is not None and max_row > post_boundary_row:
        return "post_boundary_table_missing", [f"source_row_after_{post_boundary_row}"]

    if candidate.frequency >= min_frequency:
        return "high_frequency_missing", [f"frequency_at_least_{min_frequency}"]

    return "needs_review_bulk", ["missing_candidate_requires_review"]


def _bulk_triage_row(
    candidate: SourceInventoryCandidate,
    *,
    result: PrivateTeacherIntakeResult,
    bucket: str,
    reasons: Sequence[str],
) -> dict[str, Any]:
    locators = _candidate_source_locators(candidate)
    return {
        "lemma": candidate.lemma,
        "pos": candidate.pos,
        "gloss": candidate.gloss,
        "bucket": bucket,
        "reasons": list(reasons),
        "atlas_state": _atlas_state(candidate.lemma, manifest_keys=result.manifest_keys),
        "frequency": candidate.frequency,
        "source_count": candidate.source_count,
        "max_source_row_index": _candidate_max_source_row(candidate),
        "locators": locators,
    }


def _candidate_source_locators(candidate: SourceInventoryCandidate) -> list[str]:
    locators: set[str] = set()
    for provenance in candidate.source_provenance:
        locator = provenance.get("source_locator") or provenance.get("inventory_locator")
        if isinstance(locator, str) and locator.strip():
            locators.add(locator.strip())
    return sorted(locators)


def _candidate_max_source_row(candidate: SourceInventoryCandidate) -> int | None:
    row_indexes: list[int] = []
    for locator in _candidate_source_locators(candidate):
        match = ROW_LOCATOR_RE.search(locator)
        if match:
            row_indexes.append(int(match.group(1)))
    return max(row_indexes) if row_indexes else None


def _low_signal_candidate(candidate: SourceInventoryCandidate) -> bool:
    lemma_key = _lemma_key(candidate.lemma)
    letters = lemma_key.replace("-", "").replace("'", "")
    if len(letters) <= 2:
        return True
    return candidate.frequency == 1 and lemma_key in LOW_SIGNAL_LEMMAS


def _bulk_triage_sort_key(row: Mapping[str, Any]) -> tuple[int, str]:
    return (-int(row.get("frequency") or 0), str(row.get("lemma") or "").casefold())


def _committed_teacher_inventory_keys(paths: Sequence[Path] | None) -> frozenset[str]:
    if paths is None:
        from scripts.audit.generate_source_inventory_review_candidates import COMMITTED_SOURCE_INVENTORIES

        paths = COMMITTED_SOURCE_INVENTORIES
    from scripts.audit.source_inventory_intake import read_source_inventories

    records = read_source_inventories(paths, project_root=PROJECT_ROOT)
    return frozenset(
        _lemma_key(record.lemma)
        for record in records
        if record.source_family == SOURCE_FAMILY
    )


def _markdown_inline(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("\n", " ").replace("`", "'")


def _records_from_blocks(
    blocks: Sequence[PrivateSourceBlock],
    *,
    source_id: str,
) -> tuple[list[SourceInventoryRecord], int]:
    records: list[SourceInventoryRecord] = []
    token_occurrences = 0
    for block in blocks:
        counts = Counter(_candidate_tokens(block.text))
        token_occurrences += sum(counts.values())
        for lemma, count in sorted(counts.items(), key=lambda item: _lemma_key(item[0])):
            records.append(
                SourceInventoryRecord(
                    lemma=lemma,
                    source_family=SOURCE_FAMILY,
                    extraction_mode=EXTRACTION_MODE,
                    inventory_path=f"local/{source_id}",
                    inventory_locator=block.locator,
                    source_id=source_id,
                    source_title=DEFAULT_SOURCE_TITLE,
                    source_locator=block.locator,
                    count=count,
                )
            )
    return records, token_occurrences


def _candidate_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for match in UKRAINIAN_TOKEN_RE.finditer(text):
        token = _normalize_token(match.group(0))
        if len(token.replace("-", "").replace("'", "")) < 2:
            continue
        tokens.append(token)
    return tokens


def _normalize_token(token: str) -> str:
    cleaned = strip_acute_stress(token).replace("ʼ", "'").replace("’", "'").replace("`", "'")
    if cleaned.isupper() and len(cleaned) > 1:
        return cleaned
    return cleaned.casefold()


def _load_text(
    path: Path,
    *,
    source_ref: str,
    ignored_unit_indexes: set[int],
) -> LoadedPrivateSource:
    suffix = path.suffix.lower()
    units: list[PrivateSourceUnit] = []
    blocks: list[PrivateSourceBlock] = []
    unit_index = 1
    ignored = unit_index in ignored_unit_indexes
    units.append(
        PrivateSourceUnit(
            source_ref=source_ref,
            source_suffix=suffix,
            unit_index=unit_index,
            unit_kind="text_document",
            ignored=ignored,
            shape_signature=_text_shape_signature(path),
        )
    )
    if ignored:
        return LoadedPrivateSource(units=tuple(units), blocks=())
    for block_index, paragraph in enumerate(_paragraphs(path.read_text(encoding="utf-8")), start=1):
        blocks.append(
            PrivateSourceBlock(
                source_ref=source_ref,
                source_suffix=suffix,
                unit_index=unit_index,
                unit_kind="text_document",
                block_index=block_index,
                locator=f"private source unit {unit_index} paragraph {block_index}",
                text=paragraph,
            )
        )
    return LoadedPrivateSource(units=tuple(units), blocks=tuple(blocks))


def _load_text_shape(path: Path, *, source_ref: str) -> tuple[PrivateSourceUnit, ...]:
    return (
        PrivateSourceUnit(
            source_ref=source_ref,
            source_suffix=path.suffix.lower(),
            unit_index=1,
            unit_kind="text_document",
            ignored=False,
            shape_signature=_text_shape_signature(path),
        ),
    )


def _load_delimited(
    path: Path,
    *,
    source_ref: str,
    ignored_unit_indexes: set[int],
    delimiter: str,
) -> LoadedPrivateSource:
    suffix = path.suffix.lower()
    unit_index = 1
    ignored = unit_index in ignored_unit_indexes
    units = (
        PrivateSourceUnit(
            source_ref=source_ref,
            source_suffix=suffix,
            unit_index=unit_index,
            unit_kind="delimited_table",
            ignored=ignored,
            shape_signature=_delimited_shape_signature(path, delimiter=delimiter),
        ),
    )
    if ignored:
        return LoadedPrivateSource(units=units, blocks=())
    blocks: list[PrivateSourceBlock] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        for row_index, row in enumerate(reader, start=1):
            text = " ".join(cell.strip() for cell in row if cell and cell.strip())
            if not text:
                continue
            blocks.append(
                PrivateSourceBlock(
                    source_ref=source_ref,
                    source_suffix=suffix,
                    unit_index=unit_index,
                    unit_kind="delimited_table",
                    block_index=len(blocks) + 1,
                    locator=f"private source unit {unit_index} row {row_index}",
                    text=text,
                    row_index=row_index,
                )
            )
    return LoadedPrivateSource(units=units, blocks=tuple(blocks))


def _load_delimited_shape(
    path: Path,
    *,
    source_ref: str,
    delimiter: str,
) -> tuple[PrivateSourceUnit, ...]:
    return (
        PrivateSourceUnit(
            source_ref=source_ref,
            source_suffix=path.suffix.lower(),
            unit_index=1,
            unit_kind="delimited_table",
            ignored=False,
            shape_signature=_delimited_shape_signature(path, delimiter=delimiter),
        ),
    )


def _load_docx(
    path: Path,
    *,
    source_ref: str,
    ignored_unit_indexes: set[int],
) -> LoadedPrivateSource:
    units: list[PrivateSourceUnit] = []
    blocks: list[PrivateSourceBlock] = []
    with zipfile.ZipFile(path) as archive:
        try:
            document_xml = archive.read("word/document.xml")
        except KeyError as exc:
            raise SourceInventoryError("docx private source is missing word/document.xml") from exc
    root = ET.fromstring(document_xml)
    body = root.find(f"{WORD_NS}body")
    if body is None:
        return LoadedPrivateSource(units=(), blocks=())

    unit_index = 0
    for child in list(body):
        if child.tag == f"{WORD_NS}p":
            unit_index += 1
            ignored = unit_index in ignored_unit_indexes
            units.append(
                PrivateSourceUnit(
                    source_ref=source_ref,
                    source_suffix=".docx",
                    unit_index=unit_index,
                    unit_kind="docx_paragraph",
                    ignored=ignored,
                    shape_signature=_docx_unit_shape_signature(child),
                )
            )
            if ignored:
                continue
            text = _word_text(child)
            if text:
                blocks.append(
                    PrivateSourceBlock(
                        source_ref=source_ref,
                        source_suffix=".docx",
                        unit_index=unit_index,
                        unit_kind="docx_paragraph",
                        block_index=1,
                        locator=f"private source unit {unit_index} paragraph 1",
                        text=text,
                    )
                )
            continue
        if child.tag == f"{WORD_NS}tbl":
            unit_index += 1
            ignored = unit_index in ignored_unit_indexes
            units.append(
                PrivateSourceUnit(
                    source_ref=source_ref,
                    source_suffix=".docx",
                    unit_index=unit_index,
                    unit_kind="docx_table",
                    ignored=ignored,
                    shape_signature=_docx_unit_shape_signature(child),
                )
            )
            if ignored:
                continue
            _append_docx_table_blocks(
                child,
                source_ref=source_ref,
                unit_index=unit_index,
                blocks=blocks,
            )
    return LoadedPrivateSource(units=tuple(units), blocks=tuple(blocks))


def _load_docx_shape(path: Path, *, source_ref: str) -> tuple[PrivateSourceUnit, ...]:
    with zipfile.ZipFile(path) as archive:
        try:
            document_xml = archive.read("word/document.xml")
        except KeyError as exc:
            raise SourceInventoryError("docx private source is missing word/document.xml") from exc
    root = ET.fromstring(document_xml)
    body = root.find(f"{WORD_NS}body")
    if body is None:
        return ()

    units: list[PrivateSourceUnit] = []
    unit_index = 0
    for child in list(body):
        if child.tag == f"{WORD_NS}p":
            unit_index += 1
            units.append(
                PrivateSourceUnit(
                    source_ref=source_ref,
                    source_suffix=".docx",
                    unit_index=unit_index,
                    unit_kind="docx_paragraph",
                    ignored=False,
                    shape_signature=_docx_unit_shape_signature(child),
                )
            )
        elif child.tag == f"{WORD_NS}tbl":
            unit_index += 1
            units.append(
                PrivateSourceUnit(
                    source_ref=source_ref,
                    source_suffix=".docx",
                    unit_index=unit_index,
                    unit_kind="docx_table",
                    ignored=False,
                    shape_signature=_docx_unit_shape_signature(child),
                )
            )
    return tuple(units)


def _append_docx_table_blocks(
    table: ET.Element,
    *,
    source_ref: str,
    unit_index: int,
    blocks: list[PrivateSourceBlock],
) -> None:
    row_index = 0
    for row in table.findall(f"{WORD_NS}tr"):
        row_index += 1
        cell_text = [_word_text(cell) for cell in row.findall(f"{WORD_NS}tc")]
        text = " ".join(text for text in cell_text if text)
        if not text:
            continue
        blocks.append(
            PrivateSourceBlock(
                source_ref=source_ref,
                source_suffix=".docx",
                unit_index=unit_index,
                unit_kind="docx_table",
                block_index=len([block for block in blocks if block.unit_index == unit_index]) + 1,
                locator=f"private source unit {unit_index} row {row_index}",
                text=text,
                row_index=row_index,
            )
        )


def _word_text(element: ET.Element) -> str:
    parts = [node.text or "" for node in element.iter(f"{WORD_NS}t")]
    return _clean_block_text(" ".join(parts))


def _load_xlsx(
    path: Path,
    *,
    source_ref: str,
    ignored_unit_indexes: set[int],
) -> LoadedPrivateSource:
    units: list[PrivateSourceUnit] = []
    blocks: list[PrivateSourceBlock] = []
    with zipfile.ZipFile(path) as archive:
        shared_strings = _xlsx_shared_strings(archive)
        sheets = _xlsx_sheet_targets(archive)
        for unit_index, target in enumerate(sheets, start=1):
            ignored = unit_index in ignored_unit_indexes
            units.append(
                PrivateSourceUnit(
                    source_ref=source_ref,
                    source_suffix=".xlsx",
                    unit_index=unit_index,
                    unit_kind="xlsx_sheet",
                    ignored=ignored,
                    shape_signature=target,
                )
            )
            if ignored:
                continue
            _append_xlsx_sheet_blocks(
                archive,
                target,
                shared_strings=shared_strings,
                source_ref=source_ref,
                unit_index=unit_index,
                blocks=blocks,
            )
    return LoadedPrivateSource(units=tuple(units), blocks=tuple(blocks))


def _load_xlsx_shape(path: Path, *, source_ref: str) -> tuple[PrivateSourceUnit, ...]:
    with zipfile.ZipFile(path) as archive:
        sheets = _xlsx_sheet_targets(archive)
    return tuple(
        PrivateSourceUnit(
            source_ref=source_ref,
            source_suffix=".xlsx",
            unit_index=unit_index,
            unit_kind="xlsx_sheet",
            ignored=False,
            shape_signature=target,
        )
        for unit_index, target in enumerate(sheets, start=1)
    )


def _xlsx_sheet_targets(archive: zipfile.ZipFile) -> list[str]:
    try:
        workbook_xml = archive.read("xl/workbook.xml")
        rels_xml = archive.read("xl/_rels/workbook.xml.rels")
    except KeyError as exc:
        raise SourceInventoryError("xlsx private source is missing workbook metadata") from exc
    workbook = ET.fromstring(workbook_xml)
    rels = ET.fromstring(rels_xml)
    rel_targets = {
        rel.attrib.get("Id"): _normalize_xlsx_target(rel.attrib.get("Target", ""))
        for rel in rels.findall(f"{PKG_REL_NS}Relationship")
    }
    sheets: list[str] = []
    for sheet in workbook.findall(f"{SHEET_NS}sheets/{SHEET_NS}sheet"):
        rel_id = sheet.attrib.get(f"{REL_NS}id")
        target = rel_targets.get(rel_id)
        if target:
            sheets.append(target)
    return sheets


def _normalize_xlsx_target(target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    if target.startswith("xl/"):
        return target
    return f"xl/{target}"


def _xlsx_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        payload = archive.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ET.fromstring(payload)
    strings: list[str] = []
    for item in root.findall(f"{SHEET_NS}si"):
        strings.append(_clean_block_text(" ".join(node.text or "" for node in item.iter(f"{SHEET_NS}t"))))
    return strings


def _append_xlsx_sheet_blocks(
    archive: zipfile.ZipFile,
    target: str,
    *,
    shared_strings: Sequence[str],
    source_ref: str,
    unit_index: int,
    blocks: list[PrivateSourceBlock],
) -> None:
    try:
        root = ET.fromstring(archive.read(target))
    except KeyError as exc:
        raise SourceInventoryError("xlsx private source references a missing worksheet") from exc
    block_index = 0
    for row in root.findall(f"{SHEET_NS}sheetData/{SHEET_NS}row"):
        row_index = _positive_row_index(row.attrib.get("r"), fallback=block_index + 1)
        values = [
            _xlsx_cell_text(cell, shared_strings=shared_strings)
            for cell in row.findall(f"{SHEET_NS}c")
        ]
        text = _clean_block_text(" ".join(value for value in values if value))
        if not text:
            continue
        block_index += 1
        blocks.append(
            PrivateSourceBlock(
                source_ref=source_ref,
                source_suffix=".xlsx",
                unit_index=unit_index,
                unit_kind="xlsx_sheet",
                block_index=block_index,
                locator=f"private source unit {unit_index} row {row_index}",
                text=text,
                row_index=row_index,
            )
        )


def _xlsx_cell_text(cell: ET.Element, *, shared_strings: Sequence[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return _clean_block_text(" ".join(node.text or "" for node in cell.iter(f"{SHEET_NS}t")))
    value_node = cell.find(f"{SHEET_NS}v")
    if value_node is None or value_node.text is None:
        return ""
    value = value_node.text.strip()
    if cell_type == "s":
        try:
            return shared_strings[int(value)]
        except (IndexError, ValueError):
            return ""
    if cell_type in {"str", "b"}:
        return value
    return ""


def _positive_row_index(value: str | None, *, fallback: int) -> int:
    if value is None:
        return fallback
    try:
        row_index = int(value)
    except ValueError:
        return fallback
    return row_index if row_index > 0 else fallback


def _paragraphs(text: str) -> list[str]:
    return [paragraph for paragraph in (_clean_block_text(part) for part in text.splitlines()) if paragraph]


def _clean_block_text(text: str) -> str:
    return " ".join(text.split())


def _shape_signature(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _text_shape_signature(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    paragraphs = _paragraphs(text)
    return _shape_signature(
        {
            "kind": "text_document",
            "suffix": path.suffix.lower(),
            "line_count": len(text.splitlines()),
            "paragraph_count": len(paragraphs),
            "char_count": len(text),
        }
    )


def _delimited_shape_signature(path: Path, *, delimiter: str) -> str:
    widths: list[int] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        for row in reader:
            widths.append(len(row))
    return _shape_signature(
        {
            "kind": "delimited_table",
            "suffix": path.suffix.lower(),
            "row_count": len(widths),
            "column_widths": widths,
        }
    )


def _docx_unit_shape_signature(element: ET.Element) -> str:
    tag = element.tag.removeprefix(WORD_NS)
    text_nodes = [node.text or "" for node in element.iter(f"{WORD_NS}t")]
    rows = element.findall(f".//{WORD_NS}tr")
    return _shape_signature(
        {
            "kind": tag,
            "child_tags": [child.tag.removeprefix(WORD_NS) for child in list(element)],
            "text_node_count": len(text_nodes),
            "text_char_count": sum(len(text) for text in text_nodes),
            "row_count": len(rows),
            "cells_per_row": [
                len(row.findall(f"{WORD_NS}tc"))
                for row in rows
            ],
        }
    )


def _load_manifest(manifest_path: Path | None) -> tuple[frozenset[str], str | None]:
    if manifest_path is None:
        return frozenset(), None
    path = manifest_path if manifest_path.is_absolute() else PROJECT_ROOT / manifest_path
    if not path.exists():
        raise SourceInventoryError("Atlas manifest path not found")
    manifest_text = path.read_text(encoding="utf-8")
    payload = json.loads(manifest_text)
    entries = payload.get("entries") if isinstance(payload, Mapping) else None
    if not isinstance(entries, list):
        raise SourceInventoryError("Atlas manifest entries must be a list")
    return (
        frozenset(
            _lemma_key(str(entry.get("lemma")))
            for entry in entries
            if isinstance(entry, Mapping) and entry.get("lemma")
        ),
        hashlib.sha256(manifest_text.encode("utf-8")).hexdigest(),
    )


def _atlas_state_counts(
    candidates: Sequence[SourceInventoryCandidate],
    *,
    manifest_keys: frozenset[str],
) -> dict[str, int]:
    if not manifest_keys:
        return {"existing": 0, "missing": 0}
    counts = Counter(_atlas_state(candidate.lemma, manifest_keys=manifest_keys) for candidate in candidates)
    return {"existing": counts["existing"], "missing": counts["missing"]}


def _atlas_state(lemma: str, *, manifest_keys: frozenset[str]) -> str:
    if not manifest_keys:
        return "unknown"
    return "existing" if _lemma_key(lemma) in manifest_keys else "missing"


def _count_source_kinds(
    units: Sequence[PrivateSourceUnit],
    blocks: Sequence[PrivateSourceBlock],
    *,
    by_kind: dict[str, Counter[str]],
) -> None:
    for unit in units:
        by_kind[unit.unit_kind]["units"] += 1
        if unit.ignored:
            by_kind[unit.unit_kind]["ignored_units"] += 1
    for block in blocks:
        by_kind[block.unit_kind]["text_blocks"] += 1
        by_kind[block.unit_kind]["token_occurrences"] += len(_candidate_tokens(block.text))


def _source_file_payload(
    *,
    source_ref: str,
    suffix: str,
    units: Sequence[PrivateSourceUnit],
    blocks: Sequence[PrivateSourceBlock],
    token_occurrences: int,
) -> dict[str, Any]:
    row_indexes = [block.row_index for block in blocks if block.row_index is not None]
    return {
        "source_ref": source_ref,
        "source_suffix": suffix,
        "units_seen": len(units),
        "units_included": sum(1 for unit in units if not unit.ignored),
        "units_ignored": sum(1 for unit in units if unit.ignored),
        "text_blocks_scanned": len(blocks),
        "token_occurrences": token_occurrences,
        "max_source_row_index": max(row_indexes) if row_indexes else None,
        "source_rows_after_218": sum(1 for row_index in row_indexes if row_index > 218),
    }


def _census_payload(
    *,
    source_files: Sequence[Mapping[str, Any]],
    source_shape: Mapping[str, Any],
    units: Sequence[PrivateSourceUnit],
    blocks: Sequence[PrivateSourceBlock],
    records: Sequence[SourceInventoryRecord],
    candidates: Sequence[SourceInventoryCandidate],
    gate_results: Sequence[AtlasIntakeGateResult],
    manifest_loaded: bool,
    manifest_sha256: str | None,
    atlas_state_counts: Mapping[str, int],
    token_occurrences: int,
    ignored_tab_indexes: Sequence[int],
    ignored_unit_indexes: Sequence[int],
    by_kind: Mapping[str, Counter[str]],
) -> dict[str, Any]:
    row_indexes = [block.row_index for block in blocks if block.row_index is not None]
    return {
        "workflow": WORKFLOW_ID,
        "source_family": SOURCE_FAMILY,
        "extraction_mode": EXTRACTION_MODE,
        "production_outputs_updated": [],
        "source_shape": dict(source_shape),
        "counts": {
            "source_files": len(source_files),
            "units_seen": len(units),
            "units_included": sum(1 for unit in units if not unit.ignored),
            "units_ignored": sum(1 for unit in units if unit.ignored),
            "text_blocks_scanned": len(blocks),
            "source_rows": len(records),
            "token_occurrences": token_occurrences,
            "deduped_candidates": len(candidates),
            "max_source_row_index": max(row_indexes) if row_indexes else None,
            "source_rows_after_218": sum(1 for row_index in row_indexes if row_index > 218),
        },
        "gate": {
            "workflow": "atlas_intake_gate.v1",
            "classification_counts": classification_counts(gate_results),
        },
        "atlas": {
            "manifest_loaded": manifest_loaded,
            "manifest_sha256": manifest_sha256,
            "existing_candidates": atlas_state_counts["existing"],
            "missing_candidates": atlas_state_counts["missing"],
        },
        "by_unit_kind": {
            unit_kind: {
                "units": counts["units"],
                "ignored_units": counts["ignored_units"],
                "text_blocks": counts["text_blocks"],
                "token_occurrences": counts["token_occurrences"],
            }
            for unit_kind, counts in sorted(by_kind.items())
        },
        "source_files": list(source_files),
        "safety": {
            "raw_text_included": False,
            "source_paths_included": False,
            "private_names_included": False,
            "candidate_lemmas_in_census": False,
            "ignored_tab_indexes": list(ignored_tab_indexes),
            "ignored_unit_indexes": list(ignored_unit_indexes),
            "omitted_fields": list(OMITTED_PUBLIC_FIELDS),
            "public_boundary": (
                "The census emits counts, neutral source refs, neutral locators, "
                "and gate totals only. Candidate lemmas are available only in the "
                "optional local review payload, which must be written outside the repository."
            ),
        },
    }


def _validate_positive_indexes(values: Sequence[int], flag: str) -> None:
    invalid = [value for value in values if value < 1]
    if invalid:
        raise SourceInventoryError(f"{flag} values must be positive 1-based indexes")


def _validate_source_id(source_id: str) -> None:
    if not SOURCE_ID_RE.fullmatch(source_id):
        raise SourceInventoryError("--source-id must be a lowercase neutral slug")


def _validate_source_shape_expectation(
    source_shape: Mapping[str, Any],
    *,
    expected_source_shape_sha256: str | None,
    ignored_indexes: Sequence[int],
) -> None:
    if ignored_indexes and not expected_source_shape_sha256:
        raise SourceInventoryError(
            "--expect-source-shape-sha256 is required when ignoring private source units; "
            "run --print-source-shape first"
        )
    if expected_source_shape_sha256 is None:
        return
    expected = expected_source_shape_sha256.strip().lower()
    if not SHA256_RE.fullmatch(expected):
        raise SourceInventoryError("--expect-source-shape-sha256 must be a lowercase SHA-256 hex digest")
    actual = str(source_shape.get("source_shape_sha256") or "")
    if actual != expected:
        raise SourceInventoryError("private source shape changed; aborting before candidate extraction")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "sources",
        nargs="+",
        type=Path,
        help="Local private source files to scan; paths are never emitted in reports.",
    )
    parser.add_argument(
        "--ignore-tab-index",
        action="append",
        type=int,
        default=[],
        help="1-based private source tab/unit index to exclude before text extraction.",
    )
    parser.add_argument(
        "--ignore-unit-index",
        action="append",
        type=int,
        default=[],
        help="Alias for excluding a private source unit by 1-based index.",
    )
    parser.add_argument(
        "--source-id",
        default=DEFAULT_SOURCE_ID,
        help="Neutral source id for derived provenance.",
    )
    parser.add_argument(
        "--source-shape-id",
        default=DEFAULT_SOURCE_ID,
        help="Neutral id used when computing the private source-shape checksum.",
    )
    parser.add_argument(
        "--print-source-shape",
        action="store_true",
        help="Print safe source-shape checksum JSON and exit without candidate extraction.",
    )
    parser.add_argument(
        "--expect-source-shape-sha256",
        help="Expected source-shape checksum; required when ignoring private source units.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Optional hydrated Atlas manifest for existing-vs-missing counts.",
    )
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument(
        "--candidates-out",
        type=Path,
        help=f"Optional local candidate JSON path outside the repository (example: {DEFAULT_CANDIDATES_OUT}).",
    )
    parser.add_argument(
        "--bulk-triage",
        action="store_true",
        help="Build count-only public bulk triage summary; detailed rows stay local unless output paths are set.",
    )
    parser.add_argument(
        "--triage-out",
        type=Path,
        help=f"Optional local bulk triage JSON path outside the repository (example: {DEFAULT_BULK_TRIAGE_OUT}).",
    )
    parser.add_argument(
        "--triage-report-out",
        type=Path,
        help=(
            "Optional local bulk triage Markdown path outside the repository "
            f"(example: {DEFAULT_BULK_TRIAGE_REPORT_OUT})."
        ),
    )
    parser.add_argument(
        "--min-frequency",
        type=int,
        default=3,
        help="Frequency threshold for the high-frequency missing bucket.",
    )
    parser.add_argument(
        "--post-boundary-row",
        type=int,
        default=218,
        help="Source row boundary for post-boundary table-like missing candidates.",
    )
    parser.add_argument(
        "--report-limit",
        type=int,
        default=200,
        help="Maximum rows per bucket in the local-only Markdown triage report.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.print_source_shape:
            source_shape = inspect_private_source_shape(
                args.sources,
                source_shape_id=args.source_shape_id,
            )
            print(json.dumps(source_shape, ensure_ascii=False, indent=2, sort_keys=True))
            return 0

        result = build_private_teacher_lesson_intake(
            args.sources,
            ignored_tab_indexes=tuple(args.ignore_tab_index),
            ignored_unit_indexes=tuple(args.ignore_unit_index),
            source_id=args.source_id,
            source_shape_id=args.source_shape_id,
            expected_source_shape_sha256=args.expect_source_shape_sha256,
            manifest_path=args.manifest,
        )
        if args.candidates_out:
            write_candidate_review_payload(result, args.candidates_out)
        triage: dict[str, Any] | None = None
        if args.bulk_triage or args.triage_out or args.triage_report_out:
            triage = build_bulk_triage_payload(
                result,
                min_frequency=args.min_frequency,
                post_boundary_row=args.post_boundary_row,
            )
            if args.triage_out:
                write_bulk_triage_payload(triage, args.triage_out)
            if args.triage_report_out:
                write_bulk_triage_report(
                    triage,
                    args.triage_report_out,
                    report_limit=args.report_limit,
                )
    except (OSError, SourceInventoryError, zipfile.BadZipFile, ET.ParseError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.format == "markdown":
        print(format_markdown_census(result.census, bulk_triage=bulk_triage_public_summary(triage) if triage else None))
    else:
        print(json.dumps(public_census_payload(result, bulk_triage=triage), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
