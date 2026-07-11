#!/usr/bin/env python3
"""Build a public-safe planning census for future Word Atlas source intake.

This script is intentionally read-only. It scans source surfaces and reports
aggregate counts that help plan Atlas intake capacity; it does not generate,
promote, enrich, or publish Atlas entries.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if sys.path and Path(sys.path[0]).resolve() == SCRIPT_DIR:
    sys.path.pop(0)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit.source_inventory_intake import (
    SourceInventoryError,
    read_source_inventories,
    source_inventory_candidates,
)
from scripts.lexicon.build_data_manifest import _lemma_key
from scripts.lexicon.content_lexicon_reconciler import (
    extract_ukrainian_tokens,
    strip_mdx_to_prose,
)
from scripts.lexicon.lemma_normalization import strip_acute_stress

WORKFLOW_ID = "atlas_source_census.v1"
DEFAULT_MANIFEST = PROJECT_ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
DEFAULT_TEXTBOOK_TXT_ROOT = PROJECT_ROOT / "docs" / "references" / "private" / "textbooks-txt"
DEFAULT_TEXTBOOK_PDF_ROOT = PROJECT_ROOT / "data" / "textbooks"
DEFAULT_TEXTBOOK_JSONL_ROOT = PROJECT_ROOT / "data" / "textbook_chunks"
DEFAULT_SOURCES_DB = PROJECT_ROOT / "data" / "sources.db"
DEFAULT_OHOIKO_PRIVATE_ROOT = (
    PROJECT_ROOT / "docs" / "references" / "private" / "ohoiko-june-a1-book" / "notes"
)
DEFAULT_OHOIKO_INVENTORIES = (
    PROJECT_ROOT / "data" / "lexicon" / "source-inventory" / "ohoiko-abetka-keywords.yaml",
)
DEFAULT_TEXTBOOK_INVENTORIES = (
    PROJECT_ROOT / "data" / "lexicon" / "source-inventory" / "bolshakova-bukvar-keywords.yaml",
    PROJECT_ROOT / "data" / "lexicon" / "source-inventory" / "vashulenko-grade3-headwords.yaml",
    PROJECT_ROOT / "data" / "lexicon" / "source-inventory" / "vashulenko-grade3-family-numerals.yaml",
)

MODULE_CONTENT = "module_content"
MODULE_ACTIVITY = "module_activity"
MODULE_VOCABULARY = "module_vocabulary"
MODULE_ALL = "module_all"
OHOIKO_PRIVATE = "ohoiko_private_text"
OHOIKO_INVENTORY = "ohoiko_committed_inventory"
TEXTBOOK_TXT = "textbook_extracted_text"
TEXTBOOK_PDF = "textbook_pdf_text"
TEXTBOOK_DB = "textbook_sqlite_db"
TEXTBOOK_JSONL = "textbook_jsonl_chunks"
TEXTBOOK_INVENTORY = "textbook_committed_inventory"

HEADWORD_KEYS = {"headword", "key_word", "lemma", "term", "uk", "word"}
DIRECT_VOCABULARY_ROOT_KEYS = {"letters", "vocabulary"}
DIRECT_ACTIVITY_ROOT_KEYS = {"activities"}
DIRECT_IGNORED_ROOT_KEYS = {"syllables"}
PRIVATE_SAFE_SUFFIXES = {".md", ".markdown", ".txt"}
TEXTBOOK_TXT_SUFFIXES = {".txt"}
TEXTBOOK_PDF_SUFFIXES = {".pdf"}
URL_RE = re.compile(r"https?://\S+")
TEXTBOOK_GRADE_RE = re.compile(
    r"(?:^|[^0-9])(?:(?P<grade1>0?[1-9]|1[01])[-_ ]?klas|(?P<grade2>0?[1-9]|1[01])[-_ ]?клас|grade[-_ ]?(?P<grade3>0?[1-9]|1[01]))",
    re.IGNORECASE,
)
LEADING_GRADE_RE = re.compile(r"^(?P<grade>0?[1-9]|1[01])[-_]")


@dataclass
class SurfaceStats:
    """Aggregate public-safe counts for one source surface."""

    source_units: int = 0
    token_occurrences: int = 0
    forms: Counter[str] = field(default_factory=Counter)
    explicit_headwords: Counter[str] = field(default_factory=Counter)

    def add_text(self, text: str) -> None:
        self.add_counts(candidate_token_counts(text))

    def add_counts(self, counts: Counter[str]) -> None:
        self.token_occurrences += sum(counts.values())
        self.forms.update(counts)

    def add_headwords(self, headwords: Iterable[str]) -> None:
        for headword in headwords:
            normalized = normalize_candidate(headword)
            if normalized:
                self.explicit_headwords[normalized] += 1

    def merge(self, other: SurfaceStats) -> None:
        self.source_units += other.source_units
        self.token_occurrences += other.token_occurrences
        self.forms.update(other.forms)
        self.explicit_headwords.update(other.explicit_headwords)


@dataclass(frozen=True)
class AtlasState:
    """Loaded Atlas manifest state needed for overlap counts."""

    manifest_path: str | None
    manifest_loaded: bool
    manifest_sha256: str | None
    entry_count: int
    lemma_keys: frozenset[str]
    source_family_counts: Mapping[str, int]
    curriculum_provenance_refs: int


@dataclass
class AtlasSourceCensus:
    """Full census with private local details kept out of public payloads."""

    generated_at: str
    atlas: AtlasState
    surfaces: dict[str, SurfaceStats] = field(default_factory=dict)
    by_track: dict[str, SurfaceStats] = field(default_factory=dict)
    by_grade: dict[str, SurfaceStats] = field(default_factory=dict)
    by_surface_grade: dict[str, dict[str, SurfaceStats]] = field(default_factory=dict)
    source_inputs: dict[str, Any] = field(default_factory=dict)


def build_atlas_source_census(
    *,
    root: Path = PROJECT_ROOT,
    manifest_path: Path | None = DEFAULT_MANIFEST,
    include_modules: bool = True,
    include_default_inventories: bool = True,
    include_ohoiko_private: bool = False,
    ohoiko_private_roots: Sequence[Path] = (DEFAULT_OHOIKO_PRIVATE_ROOT,),
    textbook_txt_root: Path | None = DEFAULT_TEXTBOOK_TXT_ROOT,
    textbook_pdf_root: Path | None = DEFAULT_TEXTBOOK_PDF_ROOT,
    sources_db_path: Path | None = DEFAULT_SOURCES_DB,
    textbook_jsonl_root: Path | None = None,
    include_pdfs: bool = False,
) -> AtlasSourceCensus:
    """Scan configured source lanes and return aggregate planning counts."""
    root = root.resolve()
    atlas = load_atlas_state(_resolve_optional_path(manifest_path, root))
    census = AtlasSourceCensus(
        generated_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        atlas=atlas,
    )

    if include_modules:
        scan_module_surfaces(root, census)
    if include_default_inventories:
        scan_inventory_sources(census, DEFAULT_OHOIKO_INVENTORIES, OHOIKO_INVENTORY)
        scan_inventory_sources(census, DEFAULT_TEXTBOOK_INVENTORIES, TEXTBOOK_INVENTORY)
    if include_ohoiko_private:
        scan_private_ohoiko_roots(root, census, ohoiko_private_roots)
    if sources_db_path is not None:
        scan_sources_db_textbooks(root, census, sources_db_path)
    if textbook_jsonl_root is not None:
        scan_textbook_jsonl_root(root, census, textbook_jsonl_root)
    if textbook_txt_root is not None:
        scan_textbook_text_root(root, census, textbook_txt_root)
    if include_pdfs and textbook_pdf_root is not None:
        scan_textbook_pdf_root(root, census, textbook_pdf_root)

    if MODULE_CONTENT in census.surfaces or MODULE_ACTIVITY in census.surfaces or MODULE_VOCABULARY in census.surfaces:
        combined = SurfaceStats()
        for surface_id in (MODULE_CONTENT, MODULE_ACTIVITY, MODULE_VOCABULARY):
            if surface_id in census.surfaces:
                combined.merge(census.surfaces[surface_id])
        census.surfaces[MODULE_ALL] = combined

    return census


def scan_module_surfaces(root: Path, census: AtlasSourceCensus) -> None:
    """Scan committed module lesson, activity, and vocabulary surfaces."""
    curriculum_en = root / "curriculum" / "l2-uk-en"
    curriculum_direct = root / "curriculum" / "l2-uk-direct"
    module_sources = {
        "l2_uk_en_module_md": 0,
        "l2_uk_en_activity_yaml": 0,
        "l2_uk_en_vocabulary_yaml": 0,
        "l2_uk_direct_module_yaml": 0,
    }

    for path in sorted(curriculum_en.glob("*/*/module.md")):
        if not path.is_file():
            continue
        track = _track_from_en_module_path(path)
        text = strip_mdx_to_prose(path.read_text(encoding="utf-8"))
        _add_text_surface(census, MODULE_CONTENT, text, track=track)
        module_sources["l2_uk_en_module_md"] += 1

    for path in sorted(curriculum_en.glob("*/*/activities.yaml")):
        if not path.is_file():
            continue
        track = _track_from_en_module_path(path)
        payload = _load_yaml(path)
        _add_text_surface(census, MODULE_ACTIVITY, "\n".join(_payload_strings(payload)), track=track)
        module_sources["l2_uk_en_activity_yaml"] += 1

    for path in sorted(curriculum_en.glob("*/*/vocabulary.yaml")):
        if not path.is_file():
            continue
        track = _track_from_en_module_path(path)
        payload = _load_yaml(path)
        _add_text_surface(census, MODULE_VOCABULARY, "\n".join(_payload_strings(payload)), track=track)
        census.surfaces[MODULE_VOCABULARY].add_headwords(_explicit_headwords(payload))
        census.by_track[track].add_headwords(_explicit_headwords(payload))
        module_sources["l2_uk_en_vocabulary_yaml"] += 1

    for path in sorted(curriculum_direct.glob("*/*.yaml")):
        if not path.is_file() or path.name in {"manifest.yaml", "bolshakova-letter-order.yaml"}:
            continue
        payload = _load_yaml(path)
        if not isinstance(payload, Mapping) or "module" not in payload:
            continue
        track = str(payload.get("level") or path.parent.name)
        _scan_direct_module_payload(payload, census, track=track)
        module_sources["l2_uk_direct_module_yaml"] += 1

    census.source_inputs["modules"] = module_sources


def scan_inventory_sources(
    census: AtlasSourceCensus,
    paths: Sequence[Path],
    surface_id: str,
) -> None:
    """Add committed source-inventory headwords to the census."""
    existing_paths = [path for path in paths if path.exists()]
    stats = census.surfaces.setdefault(surface_id, SurfaceStats())
    if not existing_paths:
        census.source_inputs[surface_id] = {"inventory_files": 0}
        return

    records = read_source_inventories(existing_paths, project_root=PROJECT_ROOT)
    candidates = source_inventory_candidates(records)
    stats.source_units += len(existing_paths)
    for candidate in candidates:
        normalized = normalize_candidate(candidate.lemma)
        if normalized:
            stats.explicit_headwords[normalized] += max(candidate.frequency, 1)
    census.source_inputs[surface_id] = {
        "inventory_files": len(existing_paths),
        "records": len(records),
        "deduped_candidates": len(candidates),
    }


def scan_private_ohoiko_roots(
    root: Path,
    census: AtlasSourceCensus,
    roots: Sequence[Path],
) -> None:
    """Scan local private Ohoiko text roots, aggregate only."""
    stats = census.surfaces.setdefault(OHOIKO_PRIVATE, SurfaceStats())
    scanned_files = 0
    available_roots = 0
    for raw_root in roots:
        source_root = _resolve_path(raw_root, root)
        if not source_root.exists():
            continue
        available_roots += 1
        files = _private_text_files(source_root)
        for path in files:
            stats.source_units += 1
            stats.add_text(strip_mdx_to_prose(path.read_text(encoding="utf-8")))
            scanned_files += 1
    census.source_inputs[OHOIKO_PRIVATE] = {
        "private_roots_available": available_roots,
        "text_files_scanned": scanned_files,
        "public_boundary": "aggregate counts only; no private paths, filenames, text, or lemmas",
    }


def scan_textbook_text_root(root: Path, census: AtlasSourceCensus, text_root: Path) -> None:
    """Scan extracted textbook text files."""
    source_root = _resolve_path(text_root, root)
    stats = census.surfaces.setdefault(TEXTBOOK_TXT, SurfaceStats())
    files = sorted(path for path in source_root.glob("**/*") if path.is_file() and path.suffix.lower() in TEXTBOOK_TXT_SUFFIXES)
    for path in files:
        grade = _textbook_grade(path)
        text = path.read_text(encoding="utf-8", errors="replace")
        counts = candidate_token_counts(text)
        stats.source_units += 1
        stats.add_counts(counts)
        _add_textbook_grade_counts(census, TEXTBOOK_TXT, grade, counts)
    census.source_inputs[TEXTBOOK_TXT] = {
        "text_root_available": source_root.exists(),
        "text_files_scanned": len(files),
        "public_boundary": "aggregate counts by grade only; no textbook filenames or raw text",
    }


def scan_textbook_pdf_root(root: Path, census: AtlasSourceCensus, pdf_root: Path) -> None:
    """Extract and scan PDFs with pdftotext when local PDFs are available."""
    source_root = _resolve_path(pdf_root, root)
    stats = census.surfaces.setdefault(TEXTBOOK_PDF, SurfaceStats())
    files = sorted(path for path in source_root.glob("**/*") if path.is_file() and path.suffix.lower() in TEXTBOOK_PDF_SUFFIXES)
    pdftotext = _pdftotext_path()
    if not files or not pdftotext:
        census.source_inputs[TEXTBOOK_PDF] = {
            "pdf_root_available": source_root.exists(),
            "pdf_files_seen": len(files),
            "pdf_files_scanned": 0,
            "pdftotext_available": bool(pdftotext),
        }
        return

    scanned = 0
    with tempfile.TemporaryDirectory(prefix="atlas-source-census-pdf-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        for index, path in enumerate(files, start=1):
            out_path = tmp_path / f"textbook-{index}.txt"
            try:
                subprocess.run(
                    [pdftotext, "-layout", str(path), str(out_path)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except (OSError, subprocess.CalledProcessError):
                continue
            text = out_path.read_text(encoding="utf-8", errors="replace")
            grade = _textbook_grade(path)
            counts = candidate_token_counts(text)
            stats.source_units += 1
            stats.add_counts(counts)
            _add_textbook_grade_counts(census, TEXTBOOK_PDF, grade, counts)
            scanned += 1
    census.source_inputs[TEXTBOOK_PDF] = {
        "pdf_root_available": source_root.exists(),
        "pdf_files_seen": len(files),
        "pdf_files_scanned": scanned,
        "pdftotext_available": True,
        "public_boundary": "aggregate counts by grade only; no textbook filenames or raw text",
    }


def scan_sources_db_textbooks(root: Path, census: AtlasSourceCensus, db_path: Path) -> None:
    """Scan the local SQLite textbook corpus aggregate-only."""
    source_db = _resolve_path(db_path, root)
    stats = census.surfaces.setdefault(TEXTBOOK_DB, SurfaceStats())
    if not source_db.exists():
        census.source_inputs[TEXTBOOK_DB] = {
            "sources_db_available": False,
            "chunks_scanned": 0,
            "source_files": 0,
        }
        return

    chunks_scanned = 0
    source_files: set[str] = set()
    char_count = 0
    try:
        with sqlite3.connect(f"file:{source_db}?mode=ro", uri=True) as conn:
            cursor = conn.execute(
                "select coalesce(nullif(grade, ''), 'unknown'), text, source_file, char_count from textbooks"
            )
            for raw_grade, text, source_file, raw_char_count in cursor:
                chunks_scanned += 1
                source_file_text = str(source_file or "").strip()
                if source_file_text:
                    source_files.add(source_file_text)
                try:
                    char_count += int(raw_char_count or 0)
                except (TypeError, ValueError):
                    char_count += len(str(text or ""))
                grade = _grade_label(raw_grade)
                chunk_text = str(text or "")
                counts = candidate_token_counts(chunk_text)
                stats.source_units += 1
                stats.add_counts(counts)
                _add_textbook_grade_counts(census, TEXTBOOK_DB, grade, counts)
    except sqlite3.DatabaseError as exc:
        raise SourceInventoryError(f"could not scan SQLite textbook corpus: {source_db}") from exc

    census.source_inputs[TEXTBOOK_DB] = {
        "sources_db_available": True,
        "chunks_scanned": chunks_scanned,
        "source_files": len(source_files),
        "char_count": char_count,
        "public_boundary": "aggregate counts by grade only; no DB chunk ids, source files, titles, or raw text",
    }


def scan_textbook_jsonl_root(root: Path, census: AtlasSourceCensus, jsonl_root: Path) -> None:
    """Scan textbook chunk JSONL files aggregate-only."""
    source_root = _resolve_path(jsonl_root, root)
    stats = census.surfaces.setdefault(TEXTBOOK_JSONL, SurfaceStats())
    files = sorted(path for path in source_root.glob("**/*.jsonl") if path.is_file()) if source_root.exists() else []
    rows_scanned = 0
    malformed_rows = 0
    for path in files:
        fallback_grade = _textbook_grade(path)
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    malformed_rows += 1
                    continue
                if not isinstance(row, Mapping):
                    malformed_rows += 1
                    continue
                text = str(row.get("text") or "")
                grade = _grade_label(row.get("grade") or fallback_grade)
                counts = candidate_token_counts(text)
                rows_scanned += 1
                stats.source_units += 1
                stats.add_counts(counts)
                _add_textbook_grade_counts(census, TEXTBOOK_JSONL, grade, counts)
    census.source_inputs[TEXTBOOK_JSONL] = {
        "jsonl_root_available": source_root.exists(),
        "jsonl_files_scanned": len(files),
        "chunks_scanned": rows_scanned,
        "malformed_rows": malformed_rows,
        "public_boundary": "aggregate counts by grade only; no JSONL chunk ids, filenames, or raw text",
    }


def public_census_payload(census: AtlasSourceCensus) -> dict[str, Any]:
    """Return aggregate-only JSON safe to commit or share."""
    atlas = census.atlas
    return {
        "workflow": WORKFLOW_ID,
        "generated_at": census.generated_at,
        "production_outputs_updated": [],
        "safety": {
            "public_payload_includes_raw_text": False,
            "public_payload_includes_candidate_lemmas": False,
            "public_payload_includes_private_paths": False,
            "atlas_manifest_mutated": False,
            "surface_token_note": (
                "Lesson, activity, textbook, and private-note counts are normalized Ukrainian surface forms, "
                "not reviewed Atlas lemma admissions."
            ),
        },
        "atlas": {
            "manifest_loaded": atlas.manifest_loaded,
            "manifest_path": atlas.manifest_path,
            "manifest_sha256": atlas.manifest_sha256,
            "entry_count": atlas.entry_count,
            "source_family_counts": dict(sorted(atlas.source_family_counts.items())),
            "curriculum_provenance_refs": atlas.curriculum_provenance_refs,
        },
        "source_inputs": census.source_inputs,
        "surfaces": {
            surface_id: _public_stats_payload(stats, atlas.lemma_keys)
            for surface_id, stats in sorted(census.surfaces.items())
        },
        "modules_by_track": {
            track: _public_stats_payload(stats, atlas.lemma_keys)
            for track, stats in sorted(census.by_track.items())
        },
        "textbooks_by_grade": {
            grade: _public_stats_payload(stats, atlas.lemma_keys)
            for grade, stats in sorted(census.by_grade.items(), key=lambda item: _grade_sort_key(item[0]))
        },
        "textbook_surfaces_by_grade": {
            surface_id: {
                grade: _public_stats_payload(stats, atlas.lemma_keys)
                for grade, stats in sorted(by_grade.items(), key=lambda item: _grade_sort_key(item[0]))
            }
            for surface_id, by_grade in sorted(census.by_surface_grade.items())
        },
    }


def detail_census_payload(census: AtlasSourceCensus, *, limit: int = 200) -> dict[str, Any]:
    """Return local-only details with forms/headwords for review planning."""
    atlas_keys = census.atlas.lemma_keys
    surfaces: dict[str, Any] = {}
    for surface_id, stats in sorted(census.surfaces.items()):
        surfaces[surface_id] = {
            **_public_stats_payload(stats, atlas_keys),
            "top_forms": _top_counter_rows(stats.forms, limit=limit, atlas_keys=atlas_keys),
            "top_explicit_headwords": _top_counter_rows(
                stats.explicit_headwords,
                limit=limit,
                atlas_keys=atlas_keys,
            ),
        }
    return {
        "workflow": WORKFLOW_ID,
        "policy": "Local review-only details. Do not commit; public reports use aggregate counts only.",
        "generated_at": census.generated_at,
        "production_outputs_updated": [],
        "surfaces": surfaces,
    }


def write_public_json(census: AtlasSourceCensus, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(public_census_payload(census), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return out


def write_public_markdown(census: AtlasSourceCensus, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(format_markdown_report(census) + "\n", encoding="utf-8")
    return out


def write_detail_json(census: AtlasSourceCensus, out: Path, *, project_root: Path, limit: int = 200) -> Path:
    output_path = resolve_local_detail_output_path(out, project_root=project_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(detail_census_payload(census, limit=limit), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def resolve_local_detail_output_path(out: Path, *, project_root: Path = PROJECT_ROOT) -> Path:
    """Reject repository paths for detail outputs that include forms/headwords."""
    output_path = out if out.is_absolute() else project_root / out
    resolved = output_path.resolve()
    if resolved.is_relative_to(project_root.resolve()):
        raise SourceInventoryError("atlas source census detail output must be written outside the repository")
    return resolved


def format_markdown_report(census: AtlasSourceCensus) -> str:
    payload = public_census_payload(census)
    atlas = payload["atlas"]
    lines = [
        "# Word Atlas Source Census Planning",
        "",
        f"- workflow: `{payload['workflow']}`",
        f"- generated_at: `{payload['generated_at']}`",
        "- production_outputs_updated: []",
        "- raw_text_included: false",
        "- candidate_lemmas_included: false",
        "- private_paths_included: false",
        f"- atlas_manifest_loaded: {str(atlas['manifest_loaded']).lower()}",
        f"- atlas_manifest_sha256: `{atlas['manifest_sha256'] or 'none'}`",
        f"- atlas_entry_count: {atlas['entry_count']}",
        f"- atlas_curriculum_provenance_refs: {atlas['curriculum_provenance_refs']}",
        "",
        "## Current Atlas Source Provenance",
        "",
    ]
    source_counts = atlas["source_family_counts"]
    if source_counts:
        for source_family, count in source_counts.items():
            lines.append(f"- `{source_family}`: {count}")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Surface Counts",
            "",
            "| surface | source units | token occurrences | unique forms | atlas form overlap | form backlog | explicit headwords | explicit in Atlas | explicit backlog |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for surface_id, stats in payload["surfaces"].items():
        lines.append(_markdown_stats_row(surface_id, stats))

    lines.extend(
        [
            "",
            "## Module Tracks",
            "",
            "| track | source units | token occurrences | unique forms | atlas form overlap | form backlog | explicit headwords | explicit in Atlas | explicit backlog |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for track, stats in payload["modules_by_track"].items():
        lines.append(_markdown_stats_row(track, stats))

    lines.extend(
        [
            "",
            "## Textbooks By Grade And Lane",
            "",
            "| source lane | grade | source units | token occurrences | unique forms | atlas form overlap | form backlog |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    textbook_grade_surfaces = payload["textbook_surfaces_by_grade"]
    if textbook_grade_surfaces:
        for source_lane, by_grade in textbook_grade_surfaces.items():
            for grade, stats in by_grade.items():
                lines.append(
                    f"| `{source_lane}` | `{grade}` | {stats['source_units']} | {stats['token_occurrences']} | "
                    f"{stats['unique_forms']} | {stats['atlas_form_overlap']} | {stats['form_backlog']} |"
                )
    else:
        lines.append("| none | none | 0 | 0 | 0 | 0 | 0 |")

    lines.extend(
        [
            "",
            "## Input Availability",
            "",
            "```json",
            json.dumps(payload["source_inputs"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Caveats",
            "",
            "- Module lesson, activity, textbook, and private-note rows count normalized Ukrainian surface forms, not reviewed lemma admissions.",
            "- Explicit headword rows come from vocabulary/source-inventory fields and are closer to Atlas candidate heads, but still require the normal review gate.",
            "- SQLite, JSONL, TXT, and PDF textbook lanes can overlap; use SQLite as the primary corpus count and JSONL/TXT/PDF as availability/drift checks.",
            "- Textbook corpus counts are aggregate planning numbers only; they do not imply copyright-cleared Atlas publication.",
        ]
    )
    return "\n".join(lines)


def candidate_tokens(text: str) -> list[str]:
    """Return Atlas-candidate Ukrainian surface tokens with low-signal singles removed."""
    clean_text = URL_RE.sub(" ", text)
    tokens: list[str] = []
    for token in extract_ukrainian_tokens(clean_text):
        normalized = normalize_candidate(token)
        if normalized:
            tokens.append(normalized)
    return tokens


def candidate_token_counts(text: str) -> Counter[str]:
    return Counter(candidate_tokens(text))


def normalize_candidate(value: str) -> str | None:
    token = strip_acute_stress(str(value).strip()).replace("ʼ", "'").replace("’", "'").replace("`", "'")
    token = token.casefold().strip(" \t\r\n.,;:!?…")
    if not token:
        return None
    letters = re.sub(r"[^а-щьюяєіїґ']", "", token, flags=re.IGNORECASE)
    if len(letters.replace("'", "")) < 2:
        return None
    return token


def load_atlas_state(manifest_path: Path | None) -> AtlasState:
    if manifest_path is None or not manifest_path.exists():
        return AtlasState(
            manifest_path=str(manifest_path) if manifest_path else None,
            manifest_loaded=False,
            manifest_sha256=None,
            entry_count=0,
            lemma_keys=frozenset(),
            source_family_counts={},
            curriculum_provenance_refs=0,
        )
    raw = manifest_path.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise SourceInventoryError(f"Atlas manifest has no entries list: {manifest_path}")
    lemma_keys: set[str] = set()
    source_family_counts: Counter[str] = Counter()
    curriculum_refs = 0
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        lemma = entry.get("lemma")
        if isinstance(lemma, str) and lemma.strip():
            lemma_keys.add(_lemma_key(lemma))
        provenance = entry.get("source_provenance")
        if not isinstance(provenance, list):
            continue
        for ref in provenance:
            if not isinstance(ref, Mapping):
                continue
            source_family = ref.get("source_family")
            if isinstance(source_family, str) and source_family.strip():
                source_family_counts[source_family] += 1
                if source_family == "curriculum":
                    curriculum_refs += 1
    return AtlasState(
        manifest_path=str(manifest_path),
        manifest_loaded=True,
        manifest_sha256=hashlib.sha256(raw).hexdigest(),
        entry_count=len(entries),
        lemma_keys=frozenset(lemma_keys),
        source_family_counts=dict(source_family_counts),
        curriculum_provenance_refs=curriculum_refs,
    )


def _scan_direct_module_payload(payload: Mapping[str, Any], census: AtlasSourceCensus, *, track: str) -> None:
    content_parts: list[str] = []
    for key, value in payload.items():
        key_text = str(key)
        if key_text in DIRECT_IGNORED_ROOT_KEYS:
            continue
        if key_text in DIRECT_ACTIVITY_ROOT_KEYS:
            _add_text_surface(census, MODULE_ACTIVITY, "\n".join(_payload_strings(value)), track=track)
            continue
        if key_text in DIRECT_VOCABULARY_ROOT_KEYS:
            _add_text_surface(census, MODULE_VOCABULARY, "\n".join(_payload_strings(value)), track=track)
            headwords = tuple(_explicit_headwords(value))
            census.surfaces[MODULE_VOCABULARY].add_headwords(headwords)
            census.by_track[track].add_headwords(headwords)
            continue
        content_parts.extend(_payload_strings(value))
    if content_parts:
        _add_text_surface(census, MODULE_CONTENT, "\n".join(content_parts), track=track)


def _add_text_surface(census: AtlasSourceCensus, surface_id: str, text: str, *, track: str | None = None) -> None:
    stats = census.surfaces.setdefault(surface_id, SurfaceStats())
    stats.source_units += 1
    stats.add_text(text)
    if track is not None:
        track_stats = census.by_track.setdefault(track, SurfaceStats())
        track_stats.source_units += 1
        track_stats.add_text(text)


def _add_textbook_grade_text(census: AtlasSourceCensus, surface_id: str, grade: str, text: str) -> None:
    _add_textbook_grade_counts(census, surface_id, grade, candidate_token_counts(text))


def _add_textbook_grade_counts(
    census: AtlasSourceCensus,
    surface_id: str,
    grade: str,
    counts: Counter[str],
) -> None:
    grade_stats = census.by_grade.setdefault(grade, SurfaceStats())
    grade_stats.source_units += 1
    grade_stats.add_counts(counts)
    surface_grade_stats = census.by_surface_grade.setdefault(surface_id, {}).setdefault(grade, SurfaceStats())
    surface_grade_stats.source_units += 1
    surface_grade_stats.add_counts(counts)


def _payload_strings(payload: object) -> Iterable[str]:
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            if str(key) in DIRECT_IGNORED_ROOT_KEYS:
                continue
            yield from _payload_strings(value)
        return
    if isinstance(payload, list | tuple):
        for value in payload:
            yield from _payload_strings(value)
        return
    if isinstance(payload, str):
        yield payload


def _explicit_headwords(payload: object) -> Iterable[str]:
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            if str(key) in DIRECT_IGNORED_ROOT_KEYS:
                continue
            if str(key).casefold() in HEADWORD_KEYS and isinstance(value, str):
                yield value
            else:
                yield from _explicit_headwords(value)
        return
    if isinstance(payload, list | tuple):
        for value in payload:
            yield from _explicit_headwords(value)


def _public_stats_payload(stats: SurfaceStats, atlas_keys: frozenset[str]) -> dict[str, int]:
    form_keys = {_lemma_key(form) for form in stats.forms}
    headword_keys = {_lemma_key(headword) for headword in stats.explicit_headwords}
    form_overlap = len(form_keys & atlas_keys)
    headword_overlap = len(headword_keys & atlas_keys)
    return {
        "source_units": stats.source_units,
        "token_occurrences": stats.token_occurrences,
        "unique_forms": len(form_keys),
        "atlas_form_overlap": form_overlap,
        "form_backlog": max(len(form_keys) - form_overlap, 0),
        "explicit_headwords": len(headword_keys),
        "explicit_in_atlas": headword_overlap,
        "explicit_backlog": max(len(headword_keys) - headword_overlap, 0),
    }


def _top_counter_rows(counter: Counter[str], *, limit: int, atlas_keys: frozenset[str]) -> list[dict[str, Any]]:
    rows = []
    for value, count in counter.most_common(limit):
        rows.append(
            {
                "value": value,
                "count": count,
                "atlas_state": "existing" if _lemma_key(value) in atlas_keys else "missing",
            }
        )
    return rows


def _markdown_stats_row(label: str, stats: Mapping[str, int]) -> str:
    return (
        f"| `{label}` | {stats['source_units']} | {stats['token_occurrences']} | "
        f"{stats['unique_forms']} | {stats['atlas_form_overlap']} | {stats['form_backlog']} | "
        f"{stats['explicit_headwords']} | {stats['explicit_in_atlas']} | {stats['explicit_backlog']} |"
    )


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _track_from_en_module_path(path: Path) -> str:
    return path.parent.parent.name


def _private_text_files(root: Path) -> list[Path]:
    if root.is_file() and root.suffix.lower() in PRIVATE_SAFE_SUFFIXES:
        return [root]
    if not root.is_dir():
        return []
    return sorted(path for path in root.glob("**/*") if path.is_file() and path.suffix.lower() in PRIVATE_SAFE_SUFFIXES)


def _textbook_grade(path: Path) -> str:
    haystack = " ".join(reversed(path.parts[-3:]))
    match = TEXTBOOK_GRADE_RE.search(haystack)
    if match:
        grade = next(value for value in match.groupdict().values() if value)
        return f"grade-{int(grade):02d}"
    leading = LEADING_GRADE_RE.search(path.name)
    if leading:
        return f"grade-{int(leading.group('grade')):02d}"
    return "unknown"


def _grade_label(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return "unknown"
    if text.startswith("grade-"):
        suffix = text.removeprefix("grade-")
        if suffix.isdigit():
            return f"grade-{int(suffix):02d}"
        return text
    if text.isdigit():
        grade = int(text)
        if 1 <= grade <= 11:
            return f"grade-{grade:02d}"
    return text


def _grade_sort_key(grade: str) -> tuple[int, str]:
    if grade.startswith("grade-"):
        try:
            return (int(grade.removeprefix("grade-")), grade)
        except ValueError:
            pass
    return (99, grade)


def _pdftotext_path() -> str | None:
    return shutil.which("pdftotext")


def _resolve_path(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else root / path


def _resolve_optional_path(path: Path | None, root: Path) -> Path | None:
    if path is None:
        return None
    return _resolve_path(path, root)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a public-safe Word Atlas source intake census.")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT, help="Repository root to scan.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="Atlas manifest JSON path.")
    parser.add_argument("--skip-modules", action="store_true", help="Do not scan committed module surfaces.")
    parser.add_argument(
        "--skip-default-inventories",
        action="store_true",
        help="Do not include committed Ohoiko/textbook source-inventory seeds.",
    )
    parser.add_argument(
        "--include-ohoiko-private",
        action="store_true",
        help="Scan private Ohoiko text roots aggregate-only.",
    )
    parser.add_argument(
        "--ohoiko-private-root",
        type=Path,
        action="append",
        default=None,
        help="Private Ohoiko text root; may be repeated.",
    )
    parser.add_argument(
        "--textbook-txt-root",
        type=Path,
        default=DEFAULT_TEXTBOOK_TXT_ROOT,
        help="Extracted textbook TXT root.",
    )
    parser.add_argument(
        "--textbook-pdf-root",
        type=Path,
        default=DEFAULT_TEXTBOOK_PDF_ROOT,
        help="Local textbook PDF root.",
    )
    parser.add_argument(
        "--sources-db",
        type=Path,
        default=DEFAULT_SOURCES_DB,
        help="Local sources.db path for the SQLite textbook corpus.",
    )
    parser.add_argument("--skip-sources-db", action="store_true", help="Do not scan SQLite textbook corpus.")
    parser.add_argument(
        "--textbook-jsonl-root",
        type=Path,
        default=None,
        help="Optional textbook chunk JSONL root, usually the Google Drive textbook_chunks directory.",
    )
    parser.add_argument("--include-pdfs", action="store_true", help="Scan local textbook PDFs via pdftotext.")
    parser.add_argument("--json-out", type=Path, help="Write public-safe JSON census.")
    parser.add_argument("--markdown-out", type=Path, help="Write public-safe Markdown report.")
    parser.add_argument("--detail-out", type=Path, help="Write local-only detail JSON outside the repository.")
    parser.add_argument("--detail-limit", type=int, default=200, help="Top rows per surface in local detail output.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.detail_limit < 1:
        parser.error("--detail-limit must be positive")

    root = args.root.resolve()
    ohoiko_roots = tuple(args.ohoiko_private_root or (DEFAULT_OHOIKO_PRIVATE_ROOT,))
    try:
        census = build_atlas_source_census(
            root=root,
            manifest_path=args.manifest,
            include_modules=not args.skip_modules,
            include_default_inventories=not args.skip_default_inventories,
            include_ohoiko_private=args.include_ohoiko_private,
            ohoiko_private_roots=ohoiko_roots,
            textbook_txt_root=args.textbook_txt_root,
            textbook_pdf_root=args.textbook_pdf_root,
            sources_db_path=None if args.skip_sources_db else args.sources_db,
            textbook_jsonl_root=args.textbook_jsonl_root,
            include_pdfs=args.include_pdfs,
        )
        if args.json_out:
            write_public_json(census, args.json_out if args.json_out.is_absolute() else root / args.json_out)
        if args.markdown_out:
            write_public_markdown(census, args.markdown_out if args.markdown_out.is_absolute() else root / args.markdown_out)
        if args.detail_out:
            write_detail_json(census, args.detail_out, project_root=root, limit=args.detail_limit)
    except (OSError, json.JSONDecodeError, yaml.YAMLError, SourceInventoryError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not args.json_out and not args.markdown_out:
        print(format_markdown_report(census))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
