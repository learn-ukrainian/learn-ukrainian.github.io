#!/usr/bin/env python3
"""Local-only full-source intake for private teacher-lesson Atlas candidates."""

from __future__ import annotations

import argparse
import csv
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
SOURCE_FAMILY = "teacher_lesson"
EXTRACTION_MODE = "private_document_token"
DEFAULT_SOURCE_ID = "private-teacher-lesson-full-source"
DEFAULT_SOURCE_TITLE = "Private teacher lesson source"
DEFAULT_CANDIDATES_OUT = Path("/tmp/atlas-private-teacher-lesson-candidates.json")
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
UKRAINIAN_TOKEN_RE = re.compile(
    r"[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]+(?:[ʼ'’`-][А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]+)*"
)
SOURCE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]*$")

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


def build_private_teacher_lesson_intake(
    source_paths: Sequence[Path],
    *,
    ignored_tab_indexes: Sequence[int] = (),
    ignored_unit_indexes: Sequence[int] = (),
    source_id: str = DEFAULT_SOURCE_ID,
    manifest_path: Path | None = None,
) -> PrivateTeacherIntakeResult:
    """Extract local private text into safe derived candidate/census metadata."""
    if not source_paths:
        raise SourceInventoryError("at least one private source path is required")
    _validate_positive_indexes(ignored_tab_indexes, "--ignore-tab-index")
    _validate_positive_indexes(ignored_unit_indexes, "--ignore-unit-index")
    _validate_source_id(source_id)
    ignored_indexes = tuple(sorted(set(ignored_tab_indexes) | set(ignored_unit_indexes)))

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
    manifest_keys = frozenset(_load_manifest_keys(manifest_path))
    atlas_state_counts = _atlas_state_counts(candidates, manifest_keys=manifest_keys)
    census = _census_payload(
        source_files=source_files,
        units=units,
        blocks=blocks,
        records=records,
        candidates=candidates,
        gate_results=gate_results,
        manifest_loaded=manifest_path is not None and bool(manifest_keys),
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
    )


def load_private_source(
    source_path: Path,
    *,
    source_ref: str,
    ignored_unit_indexes: Sequence[int],
) -> LoadedPrivateSource:
    """Load supported private source files without exposing names in payloads."""
    path = source_path if source_path.is_absolute() else PROJECT_ROOT / source_path
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise SourceInventoryError(
            f"unsupported private source extension {suffix!r}; expected one of {sorted(SUPPORTED_SUFFIXES)}"
        )
    if not path.exists():
        raise SourceInventoryError("private source path not found")
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


def resolve_local_review_output_path(out: Path) -> Path:
    """Reject repository paths for local private-source candidate output."""
    output_path = out if out.is_absolute() else PROJECT_ROOT / out
    resolved = output_path.resolve()
    if resolved.is_relative_to(PROJECT_ROOT.resolve()):
        raise SourceInventoryError("private-source candidate output must be written outside the repository")
    return resolved


def format_markdown_census(census: Mapping[str, Any]) -> str:
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
        f"- atlas_existing_candidates: {atlas['existing_candidates']}",
        f"- atlas_missing_candidates: {atlas['missing_candidates']}",
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
    return "\n".join(lines)


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


def _load_manifest_keys(manifest_path: Path | None) -> set[str]:
    if manifest_path is None:
        return set()
    path = manifest_path if manifest_path.is_absolute() else PROJECT_ROOT / manifest_path
    if not path.exists():
        raise SourceInventoryError("Atlas manifest path not found")
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("entries") if isinstance(payload, Mapping) else None
    if not isinstance(entries, list):
        raise SourceInventoryError("Atlas manifest entries must be a list")
    return {
        _lemma_key(str(entry.get("lemma")))
        for entry in entries
        if isinstance(entry, Mapping) and entry.get("lemma")
    }


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
    units: Sequence[PrivateSourceUnit],
    blocks: Sequence[PrivateSourceBlock],
    records: Sequence[SourceInventoryRecord],
    candidates: Sequence[SourceInventoryCandidate],
    gate_results: Sequence[AtlasIntakeGateResult],
    manifest_loaded: bool,
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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = build_private_teacher_lesson_intake(
            args.sources,
            ignored_tab_indexes=tuple(args.ignore_tab_index),
            ignored_unit_indexes=tuple(args.ignore_unit_index),
            source_id=args.source_id,
            manifest_path=args.manifest,
        )
        if args.candidates_out:
            write_candidate_review_payload(result, args.candidates_out)
    except (OSError, SourceInventoryError, zipfile.BadZipFile, ET.ParseError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.format == "markdown":
        print(format_markdown_census(result.census))
    else:
        print(json.dumps(result.census, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
