#!/usr/bin/env python3
"""Count aggregate source-corpus Atlas entry demand by finalized buckets.

This Phase 2 census bridges the aggregate source-surface census and the
finalized Word Atlas entry model. Public output is aggregate-only: it reports
counts, methods, and caveats, but never source text, private paths, source
filenames, Atlas entry lists, or candidate lemma lists.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if sys.path and Path(sys.path[0]).resolve() == SCRIPT_DIR:
    sys.path.pop(0)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit import atlas_source_census
from scripts.audit.atlas_entry_model_census import (
    DEFAULT_MANIFEST,
    ENTRY_TYPES,
    NON_ENTRY_TYPES,
    build_entry_model_census,
    classify_entry,
)
from scripts.audit.atlas_intake_census import discover_inventory_paths
from scripts.audit.source_inventory_intake import (
    SourceInventoryCandidate,
    SourceInventoryError,
    SourceInventoryRecord,
    read_source_inventories,
    source_inventory_candidates,
)
from scripts.lexicon.build_data_manifest import _lemma_key
from scripts.lexicon.content_lexicon_reconciler import VesumLookup, lemmatize_forms
from scripts.lexicon.lemma_normalization import strip_acute_stress
from scripts.verification.vesum import verify_words

WORKFLOW_ID = "atlas_source_entry_count.v1"
DETAIL_POLICY = "Local review-only details. Do not commit; public reports use aggregate counts only."

SOURCE_ENTRY_BUCKETS = (
    *ENTRY_TYPES,
    "noise_rejected",
    "needs_review",
    "unknown",
)
DETAIL_LIMIT_DEFAULT = 200
DEFAULT_TEXTBOOK_JSONL_ROOT = PROJECT_ROOT / "data" / "textbook_chunks"
INVENTORY_ALL_LANE = "committed_source_inventory"
INVENTORY_FAMILY_PREFIX = "committed_inventory_"
TEXTBOOK_SURFACE_LANES = {
    atlas_source_census.TEXTBOOK_DB,
    atlas_source_census.TEXTBOOK_JSONL,
    atlas_source_census.TEXTBOOK_TXT,
}

WORD_TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яЄєІіЇїҐґ0-9'’ʼ-]+")
MULTIWORD_DELIMITER_RE = re.compile(r"\s|/|\.\.\.")

METHOD_PRIORITY = {
    "manifest_entry_type": 100,
    "source_inventory_headword": 80,
    "module_explicit_headword": 75,
    "vesum_backed_lemma": 70,
    "heuristic_multiword_needs_review": 60,
    "unknown_needs_review": 40,
    "lemmatizer_unavailable": 30,
    "noise_filter": 10,
}


@dataclass(frozen=True)
class ReviewedAtlasState:
    """Read-only reviewed Atlas state used for overlap and exact baseline."""

    manifest_loaded: bool
    manifest_sha256: str | None
    reviewed_bucket_by_key: Mapping[str, str]
    entry_census: Mapping[str, Any]


@dataclass
class LemmatizationSummary:
    """Aggregate lemmatization metadata for one lane."""

    available: bool
    method: str
    unique_forms: int = 0
    forms_with_matches: int = 0
    unrecognized_forms: int = 0
    lemma_candidates: int = 0

    def public_payload(self) -> dict[str, int | bool | str]:
        return {
            "available": self.available,
            "method": self.method,
            "unique_forms": self.unique_forms,
            "forms_with_matches": self.forms_with_matches,
            "unrecognized_forms": self.unrecognized_forms,
            "lemma_candidates": self.lemma_candidates,
        }


@dataclass
class CandidateRecord:
    """One internal candidate record. Values appear only in local detail output."""

    key: str
    value: str
    bucket: str
    method: str
    existing_reviewed: bool
    occurrences: int = 0
    source_count: int = 1


@dataclass
class LaneAccumulator:
    """Aggregate candidate records for one source lane."""

    lane_id: str
    counting_method: str
    candidates: dict[str, CandidateRecord]

    @classmethod
    def create(cls, lane_id: str, counting_method: str) -> LaneAccumulator:
        return cls(lane_id=lane_id, counting_method=counting_method, candidates={})

    def add(
        self,
        *,
        key: str,
        value: str,
        bucket: str,
        method: str,
        existing_reviewed: bool,
        occurrences: int = 0,
        source_count: int = 1,
    ) -> None:
        current = self.candidates.get(key)
        if current is None:
            self.candidates[key] = CandidateRecord(
                key=key,
                value=value,
                bucket=bucket,
                method=method,
                existing_reviewed=existing_reviewed,
                occurrences=occurrences,
                source_count=source_count,
            )
            return

        current.occurrences += occurrences
        current.source_count += source_count
        if _method_priority(method) > _method_priority(current.method):
            current.value = value
            current.bucket = bucket
            current.method = method
            current.existing_reviewed = existing_reviewed

    def public_payload(
        self,
        *,
        source_units: int,
        token_occurrences: int,
        unique_surface_forms: int,
        explicit_headwords: int,
        lemmatization: LemmatizationSummary,
    ) -> dict[str, Any]:
        candidate_counts = _bucket_counts(self.candidates.values())
        existing_counts = _bucket_counts(
            candidate for candidate in self.candidates.values() if candidate.existing_reviewed
        )
        backlog_counts = _bucket_counts(
            candidate
            for candidate in self.candidates.values()
            if not candidate.existing_reviewed and candidate.bucket != "noise_rejected"
        )
        method_counts = Counter(candidate.method for candidate in self.candidates.values())
        existing_total = sum(existing_counts.values())
        backlog_total = sum(backlog_counts.values())
        return {
            "counting_method": self.counting_method,
            "source_units": source_units,
            "token_occurrences": token_occurrences,
            "unique_surface_forms": unique_surface_forms,
            "explicit_headwords": explicit_headwords,
            "candidate_entries": sum(candidate_counts.values()),
            "existing_reviewed_overlap": existing_total,
            "estimated_backlog": backlog_total,
            "candidates_by_bucket": dict(candidate_counts),
            "existing_reviewed_by_bucket": dict(existing_counts),
            "estimated_backlog_by_bucket": dict(backlog_counts),
            "classification_methods": dict(sorted(method_counts.items())),
            "lemmatization": lemmatization.public_payload(),
        }

    def detail_rows(self, *, limit: int) -> list[dict[str, Any]]:
        rows = sorted(
            self.candidates.values(),
            key=lambda candidate: (
                candidate.existing_reviewed,
                candidate.bucket,
                -candidate.occurrences,
                candidate.value.casefold(),
            ),
        )
        return [
            {
                "value": candidate.value,
                "bucket": candidate.bucket,
                "method": candidate.method,
                "existing_reviewed": candidate.existing_reviewed,
                "occurrences": candidate.occurrences,
                "source_count": candidate.source_count,
            }
            for candidate in rows[:limit]
        ]


@dataclass
class Lemmatizer:
    """Cached VESUM lookup wrapper that can degrade to unknown counts."""

    vesum_lookup: VesumLookup | None
    available: bool = True
    unavailable_reason: str | None = None
    cache: dict[str, list[dict[str, Any]]] | None = None

    def __post_init__(self) -> None:
        self.available = self.vesum_lookup is not None
        self.cache = {}
        if self.vesum_lookup is None:
            self.unavailable_reason = "disabled"

    def lookup(self, forms: Sequence[str]) -> dict[str, list[dict[str, Any]]] | None:
        if not self.available:
            return None
        assert self.cache is not None
        missing = [form for form in forms if form not in self.cache]
        if missing:
            try:
                batch = lemmatize_forms(missing, vesum_lookup=self.vesum_lookup or verify_words)
            except FileNotFoundError as exc:
                self.available = False
                self.unavailable_reason = str(exc).splitlines()[0]
                return None
            self.cache.update(batch)
        return {form: self.cache.get(form, []) for form in forms}

    def method_label(self) -> str:
        if self.available:
            return "VESUM-backed unique lemma estimate"
        if self.unavailable_reason == "disabled":
            return "lemmatizer disabled; counted as unknown source forms"
        return "lemmatizer unavailable; counted as unknown source forms"


@dataclass
class SourceEntryCountResult:
    """Public payload plus local-only detail rows."""

    public_payload: dict[str, Any]
    lane_details: Mapping[str, LaneAccumulator]
    textbook_grade_details: Mapping[str, Mapping[str, LaneAccumulator]]


def build_source_entry_count(
    *,
    root: Path = PROJECT_ROOT,
    manifest_path: Path | None = DEFAULT_MANIFEST,
    include_modules: bool = True,
    include_committed_inventories: bool = True,
    inventory_paths: Sequence[Path] | None = None,
    include_ohoiko_private: bool = False,
    ohoiko_private_roots: Sequence[Path] = (atlas_source_census.DEFAULT_OHOIKO_PRIVATE_ROOT,),
    textbook_txt_root: Path | None = atlas_source_census.DEFAULT_TEXTBOOK_TXT_ROOT,
    sources_db_path: Path | None = atlas_source_census.DEFAULT_SOURCES_DB,
    textbook_jsonl_root: Path | None = DEFAULT_TEXTBOOK_JSONL_ROOT,
    vesum_lookup: VesumLookup | None = verify_words,
) -> SourceEntryCountResult:
    """Build aggregate source-entry demand counts without publishing details."""
    root = root.resolve()
    manifest = _read_manifest_state(_resolve_optional_path(manifest_path, root))
    lemmatizer = Lemmatizer(vesum_lookup=vesum_lookup)
    source_surface_census = atlas_source_census.build_atlas_source_census(
        root=root,
        manifest_path=manifest_path,
        include_modules=include_modules,
        include_default_inventories=False,
        include_ohoiko_private=include_ohoiko_private,
        ohoiko_private_roots=ohoiko_private_roots,
        textbook_txt_root=textbook_txt_root,
        textbook_pdf_root=None,
        sources_db_path=sources_db_path,
        textbook_jsonl_root=textbook_jsonl_root,
        include_pdfs=False,
    )

    lane_payloads: dict[str, Any] = {}
    lane_details: dict[str, LaneAccumulator] = {}
    for lane_id, stats in sorted(source_surface_census.surfaces.items()):
        accumulator, lemmatization = _summarize_surface_lane(
            lane_id=lane_id,
            stats=stats,
            reviewed_bucket_by_key=manifest.reviewed_bucket_by_key,
            lemmatizer=lemmatizer,
        )
        lane_payloads[lane_id] = accumulator.public_payload(
            source_units=stats.source_units,
            token_occurrences=stats.token_occurrences,
            unique_surface_forms=len({_lemma_key(form) for form in stats.forms}),
            explicit_headwords=len({_lemma_key(headword) for headword in stats.explicit_headwords}),
            lemmatization=lemmatization,
        )
        lane_details[lane_id] = accumulator

    inventory_inputs: dict[str, Any] = {
        "included": include_committed_inventories,
        "inventory_files": 0,
        "records": 0,
        "deduped_candidates": 0,
        "by_family": {},
        "public_boundary": "aggregate counts only; no inventory filenames, source titles, paths, text, or candidate lists",
    }
    if include_committed_inventories:
        inventory_payloads, inventory_details, inventory_inputs = _build_inventory_lanes(
            inventory_paths=inventory_paths,
            project_root=root,
            reviewed_bucket_by_key=manifest.reviewed_bucket_by_key,
        )
        lane_payloads.update(inventory_payloads)
        lane_details.update(inventory_details)

    textbook_grade_payloads: dict[str, dict[str, Any]] = {}
    textbook_grade_details: dict[str, dict[str, LaneAccumulator]] = {}
    for lane_id, by_grade in sorted(source_surface_census.by_surface_grade.items()):
        if lane_id not in TEXTBOOK_SURFACE_LANES:
            continue
        textbook_grade_payloads[lane_id] = {}
        textbook_grade_details[lane_id] = {}
        for grade, stats in sorted(by_grade.items(), key=lambda item: atlas_source_census._grade_sort_key(item[0])):
            accumulator, lemmatization = _summarize_surface_lane(
                lane_id=f"{lane_id}:{grade}",
                stats=stats,
                reviewed_bucket_by_key=manifest.reviewed_bucket_by_key,
                lemmatizer=lemmatizer,
                include_explicit_headwords=False,
            )
            textbook_grade_payloads[lane_id][grade] = accumulator.public_payload(
                source_units=stats.source_units,
                token_occurrences=stats.token_occurrences,
                unique_surface_forms=len({_lemma_key(form) for form in stats.forms}),
                explicit_headwords=0,
                lemmatization=lemmatization,
            )
            textbook_grade_details[lane_id][grade] = accumulator

    source_inputs = _public_source_inputs(source_surface_census.source_inputs)
    source_inputs["committed_source_inventories"] = inventory_inputs
    payload = {
        "workflow": WORKFLOW_ID,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "production_outputs_updated": [],
        "safety": {
            "public_payload_includes_raw_text": False,
            "public_payload_includes_candidate_lemmas": False,
            "public_payload_includes_private_paths": False,
            "public_payload_includes_private_filenames": False,
            "atlas_manifest_mutated": False,
            "details_must_be_outside_repo": True,
        },
        "reviewed_atlas": {
            "manifest_loaded": manifest.manifest_loaded,
            "manifest_sha256": manifest.manifest_sha256,
            "manifest_records": manifest.entry_census["manifest_records"],
            "total_reviewed_entries": manifest.entry_census["total_reviewed_entries"],
            "reviewed_entries_by_type": manifest.entry_census["reviewed_entries_by_type"],
            "non_entry_records": manifest.entry_census["non_entry_records"],
        },
        "source_inputs": source_inputs,
        "source_lanes": lane_payloads,
        "textbook_grades_by_lane": textbook_grade_payloads,
        "caveats": [
            "Reviewed Atlas counts are exact manifest article-entry counts; source-corpus counts are planning estimates.",
            "VESUM-backed lanes count unique candidate lemmas inferred from unique surface forms; ambiguous forms may contribute more than one possible lemma.",
            "Unrecognized forms, unreviewed multiword headwords, and unavailable lemmatizer lanes are counted as needs_review or unknown, not as approved entries.",
            "Current Atlas reviewed entries, source-corpus candidates, and backlog counts are separate numbers and should not be added together.",
            "Module content/activity/vocabulary lanes overlap; module_all is a convenience union for module surfaces.",
            "SQLite, JSONL, and extracted-TXT textbook lanes can overlap; use SQLite as the primary local corpus lane when available and JSONL/TXT as availability or drift checks.",
            "Committed source-inventory lanes are explicit reviewed/headword-style evidence, but they still require the normal Atlas review/publish gate for missing entries.",
            "No Phase 2 design or POC drift was found beyond the entry-model drift already documented in PR #4245.",
        ],
    }
    return SourceEntryCountResult(
        public_payload=payload,
        lane_details=lane_details,
        textbook_grade_details=textbook_grade_details,
    )


def format_markdown_report(payload: Mapping[str, Any]) -> str:
    """Format a public-safe aggregate Markdown report."""
    reviewed = payload["reviewed_atlas"]
    lines = [
        "# Word Atlas Source Entry Count",
        "",
        f"- workflow: `{payload['workflow']}`",
        f"- generated_at: `{payload['generated_at']}`",
        "- production_outputs_updated: []",
        "- raw_text_included: false",
        "- candidate_lemmas_included: false",
        "- private_paths_included: false",
        "- private_filenames_included: false",
        "",
        "## Exact Reviewed Atlas Baseline",
        "",
        f"- manifest_loaded: {str(reviewed['manifest_loaded']).lower()}",
        f"- manifest_sha256: `{reviewed['manifest_sha256'] or 'none'}`",
        f"- manifest_records: {reviewed['manifest_records']}",
        f"- total_reviewed_entries: {reviewed['total_reviewed_entries']}",
        "",
        "| entry bucket | exact reviewed entries |",
        "| --- | ---: |",
    ]
    for bucket in ENTRY_TYPES:
        lines.append(f"| `{bucket}` | {reviewed['reviewed_entries_by_type'].get(bucket, 0)} |")

    lines.extend(["", "### Exact Non-Entry Manifest Records", "", "| bucket | records |", "| --- | ---: |"])
    for bucket in NON_ENTRY_TYPES:
        lines.append(f"| `{bucket}` | {reviewed['non_entry_records'].get(bucket, 0)} |")

    lines.extend(
        [
            "",
            "## Estimated Source-Corpus Backlog By Lane",
            "",
            "| source lane | source units | unique forms | explicit headwords | candidate entries | reviewed overlap | estimated backlog | lemma | expression | phraseologism | proverb | multiword term | proper name | needs review | unknown | noise rejected |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for lane_id, lane in payload["source_lanes"].items():
        backlog = lane["estimated_backlog_by_bucket"]
        lines.append(
            f"| `{lane_id}` | {lane['source_units']} | {lane['unique_surface_forms']} | "
            f"{lane['explicit_headwords']} | {lane['candidate_entries']} | "
            f"{lane['existing_reviewed_overlap']} | {lane['estimated_backlog']} | "
            f"{backlog.get('lemma', 0)} | {backlog.get('expression', 0)} | "
            f"{backlog.get('phraseologism', 0)} | {backlog.get('proverb', 0)} | "
            f"{backlog.get('multiword_term', 0)} | {backlog.get('proper_name', 0)} | "
            f"{backlog.get('needs_review', 0)} | {backlog.get('unknown', 0)} | "
            f"{backlog.get('noise_rejected', 0)} |"
        )

    lines.extend(
        [
            "",
            "## Classification Methods By Lane",
            "",
            "| source lane | method | candidates |",
            "| --- | --- | ---: |",
        ]
    )
    for lane_id, lane in payload["source_lanes"].items():
        methods = lane["classification_methods"] or {"none": 0}
        for method, count in methods.items():
            lines.append(f"| `{lane_id}` | `{method}` | {count} |")

    lines.extend(
        [
            "",
            "## Textbook Grades By Lane",
            "",
            "| source lane | grade | source units | unique forms | candidate entries | reviewed overlap | estimated backlog | lemma | needs review | unknown |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    textbook_rows = payload["textbook_grades_by_lane"]
    if textbook_rows:
        for lane_id, by_grade in textbook_rows.items():
            for grade, stats in by_grade.items():
                backlog = stats["estimated_backlog_by_bucket"]
                lines.append(
                    f"| `{lane_id}` | `{grade}` | {stats['source_units']} | "
                    f"{stats['unique_surface_forms']} | {stats['candidate_entries']} | "
                    f"{stats['existing_reviewed_overlap']} | {stats['estimated_backlog']} | "
                    f"{backlog.get('lemma', 0)} | {backlog.get('needs_review', 0)} | "
                    f"{backlog.get('unknown', 0)} |"
                )
    else:
        lines.append("| none | none | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |")

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
        ]
    )
    lines.extend(f"- {note}" for note in payload["caveats"])
    return "\n".join(lines)


def write_public_json(result: SourceEntryCountResult, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result.public_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return out


def write_public_markdown(result: SourceEntryCountResult, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(format_markdown_report(result.public_payload) + "\n", encoding="utf-8")
    return out


def write_detail_json(
    result: SourceEntryCountResult,
    out: Path,
    *,
    project_root: Path,
    limit: int = DETAIL_LIMIT_DEFAULT,
) -> Path:
    output_path = resolve_local_detail_output_path(out, project_root=project_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(detail_payload(result, limit=limit), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def resolve_local_detail_output_path(out: Path, *, project_root: Path = PROJECT_ROOT) -> Path:
    """Reject repository paths for detail outputs that include candidate values."""
    output_path = out if out.is_absolute() else project_root / out
    resolved = output_path.resolve()
    if resolved.is_relative_to(project_root.resolve()):
        raise SourceInventoryError("atlas source entry-count detail output must be written outside the repository")
    return resolved


def detail_payload(result: SourceEntryCountResult, *, limit: int = DETAIL_LIMIT_DEFAULT) -> dict[str, Any]:
    """Return local-only details with candidate values for review planning."""
    return {
        "workflow": WORKFLOW_ID,
        "policy": DETAIL_POLICY,
        "generated_at": result.public_payload["generated_at"],
        "production_outputs_updated": [],
        "lanes": {
            lane_id: accumulator.detail_rows(limit=limit)
            for lane_id, accumulator in result.lane_details.items()
        },
        "textbook_grades_by_lane": {
            lane_id: {
                grade: accumulator.detail_rows(limit=limit)
                for grade, accumulator in by_grade.items()
            }
            for lane_id, by_grade in result.textbook_grade_details.items()
        },
    }


def _summarize_surface_lane(
    *,
    lane_id: str,
    stats: atlas_source_census.SurfaceStats,
    reviewed_bucket_by_key: Mapping[str, str],
    lemmatizer: Lemmatizer,
    include_explicit_headwords: bool = True,
) -> tuple[LaneAccumulator, LemmatizationSummary]:
    accumulator = LaneAccumulator.create(
        lane_id=lane_id,
        counting_method=(
            "VESUM-backed unique lemma estimate for surface forms; explicit headwords retained as "
            "source headword candidates; unrecognized forms and unreviewed multiword headwords require review"
        ),
    )
    lemmatization = _add_surface_forms(
        accumulator=accumulator,
        forms=stats.forms,
        reviewed_bucket_by_key=reviewed_bucket_by_key,
        lemmatizer=lemmatizer,
    )
    if include_explicit_headwords:
        for headword, count in stats.explicit_headwords.items():
            _add_explicit_headword(
                accumulator=accumulator,
                value=headword,
                pos=None,
                reviewed_bucket_by_key=reviewed_bucket_by_key,
                method="module_explicit_headword",
                occurrences=count,
            )
    return accumulator, lemmatization


def _add_surface_forms(
    *,
    accumulator: LaneAccumulator,
    forms: Counter[str],
    reviewed_bucket_by_key: Mapping[str, str],
    lemmatizer: Lemmatizer,
) -> LemmatizationSummary:
    unique_forms = tuple(sorted(forms))
    summary = LemmatizationSummary(
        available=lemmatizer.available,
        method=lemmatizer.method_label(),
        unique_forms=len(unique_forms),
    )
    if not unique_forms:
        return summary

    matches_by_form = lemmatizer.lookup(unique_forms)
    summary.available = lemmatizer.available
    summary.method = lemmatizer.method_label()
    if matches_by_form is None:
        summary.unrecognized_forms = len(unique_forms)
        for form in unique_forms:
            accumulator.add(
                key=_private_candidate_key("unknown", form),
                value=form,
                bucket="unknown",
                method="lemmatizer_unavailable",
                existing_reviewed=False,
                occurrences=forms[form],
            )
        return summary

    lemma_candidate_keys: set[str] = set()
    for form in unique_forms:
        matches = matches_by_form.get(form, [])
        lemmas = _match_lemmas(matches)
        if not lemmas:
            summary.unrecognized_forms += 1
            accumulator.add(
                key=_private_candidate_key("unrecognized", form),
                value=form,
                bucket="needs_review",
                method="unknown_needs_review",
                existing_reviewed=False,
                occurrences=forms[form],
            )
            continue
        summary.forms_with_matches += 1
        for lemma in lemmas:
            lemma_key = _lemma_key(lemma)
            if not lemma_key:
                continue
            lemma_candidate_keys.add(lemma_key)
            bucket = reviewed_bucket_by_key.get(lemma_key, "lemma")
            accumulator.add(
                key=f"lemma:{lemma_key}",
                value=lemma,
                bucket=bucket,
                method="manifest_entry_type" if lemma_key in reviewed_bucket_by_key else "vesum_backed_lemma",
                existing_reviewed=lemma_key in reviewed_bucket_by_key,
                occurrences=forms[form],
            )
    summary.lemma_candidates = len(lemma_candidate_keys)
    return summary


def _build_inventory_lanes(
    *,
    inventory_paths: Sequence[Path] | None,
    project_root: Path,
    reviewed_bucket_by_key: Mapping[str, str],
) -> tuple[dict[str, Any], dict[str, LaneAccumulator], dict[str, Any]]:
    paths = tuple(inventory_paths) if inventory_paths is not None else discover_inventory_paths()
    records = read_source_inventories(paths, project_root=project_root) if paths else []
    all_candidates = source_inventory_candidates(records) if records else []
    payloads: dict[str, Any] = {}
    details: dict[str, LaneAccumulator] = {}

    all_accumulator = _inventory_accumulator(
        lane_id=INVENTORY_ALL_LANE,
        candidates=all_candidates,
        records=records,
        reviewed_bucket_by_key=reviewed_bucket_by_key,
    )
    payloads[INVENTORY_ALL_LANE] = all_accumulator.public_payload(
        source_units=_inventory_source_units(records),
        token_occurrences=0,
        unique_surface_forms=0,
        explicit_headwords=len(all_candidates),
        lemmatization=LemmatizationSummary(
            available=False,
            method="explicit committed inventory headwords; no surface-form lemmatization",
        ),
    )
    details[INVENTORY_ALL_LANE] = all_accumulator

    records_by_family: dict[str, list[SourceInventoryRecord]] = defaultdict(list)
    for record in records:
        records_by_family[record.source_family].append(record)

    inputs_by_family: dict[str, Any] = {}
    for family, family_records in sorted(records_by_family.items()):
        family_candidates = source_inventory_candidates(family_records)
        lane_id = f"{INVENTORY_FAMILY_PREFIX}{family}"
        accumulator = _inventory_accumulator(
            lane_id=lane_id,
            candidates=family_candidates,
            records=family_records,
            reviewed_bucket_by_key=reviewed_bucket_by_key,
        )
        payloads[lane_id] = accumulator.public_payload(
            source_units=_inventory_source_units(family_records),
            token_occurrences=0,
            unique_surface_forms=0,
            explicit_headwords=len(family_candidates),
            lemmatization=LemmatizationSummary(
                available=False,
                method="explicit committed inventory headwords; no surface-form lemmatization",
            ),
        )
        details[lane_id] = accumulator
        inputs_by_family[family] = {
            "records": len(family_records),
            "deduped_candidates": len(family_candidates),
            "source_units": _inventory_source_units(family_records),
        }

    inventory_inputs = {
        "included": True,
        "inventory_files": len(paths),
        "records": len(records),
        "deduped_candidates": len(all_candidates),
        "by_family": inputs_by_family,
        "public_boundary": "aggregate counts only; no inventory filenames, source titles, paths, text, or candidate lists",
    }
    return payloads, details, inventory_inputs


def _inventory_accumulator(
    *,
    lane_id: str,
    candidates: Sequence[SourceInventoryCandidate],
    records: Sequence[SourceInventoryRecord],
    reviewed_bucket_by_key: Mapping[str, str],
) -> LaneAccumulator:
    accumulator = LaneAccumulator.create(
        lane_id=lane_id,
        counting_method=(
            "Explicit committed source-inventory headwords; existing reviewed entries bucketed from the "
            "manifest; missing multiword headwords require review before bucket admission"
        ),
    )
    del records
    for candidate in candidates:
        _add_explicit_headword(
            accumulator=accumulator,
            value=candidate.lemma,
            pos=candidate.pos,
            reviewed_bucket_by_key=reviewed_bucket_by_key,
            method="source_inventory_headword",
            occurrences=candidate.frequency,
            source_count=max(candidate.source_count, 1),
        )
    return accumulator


def _add_explicit_headword(
    *,
    accumulator: LaneAccumulator,
    value: str,
    pos: str | None,
    reviewed_bucket_by_key: Mapping[str, str],
    method: str,
    occurrences: int = 0,
    source_count: int = 1,
) -> None:
    normalized = _normalize_headword(value)
    if normalized is None:
        accumulator.add(
            key=_private_candidate_key("noise", value),
            value=value,
            bucket="noise_rejected",
            method="noise_filter",
            existing_reviewed=False,
            occurrences=occurrences,
            source_count=source_count,
        )
        return

    key = _lemma_key(normalized)
    if key in reviewed_bucket_by_key:
        accumulator.add(
            key=f"entry:{key}",
            value=normalized,
            bucket=reviewed_bucket_by_key[key],
            method="manifest_entry_type",
            existing_reviewed=True,
            occurrences=occurrences,
            source_count=source_count,
        )
        return

    if _looks_like_multiword(normalized):
        bucket = "needs_review"
        final_method = "heuristic_multiword_needs_review"
    else:
        bucket = "proper_name" if _looks_like_proper_name(pos) else "lemma"
        final_method = method

    accumulator.add(
        key=f"headword:{key}",
        value=normalized,
        bucket=bucket,
        method=final_method,
        existing_reviewed=False,
        occurrences=occurrences,
        source_count=source_count,
    )


def _read_manifest_state(manifest_path: Path | None) -> ReviewedAtlasState:
    if manifest_path is None or not manifest_path.exists():
        empty_census = build_entry_model_census({"entries": []})
        return ReviewedAtlasState(
            manifest_loaded=False,
            manifest_sha256=None,
            reviewed_bucket_by_key={},
            entry_census=empty_census,
        )

    raw = manifest_path.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, Mapping):
        raise SourceInventoryError(f"Atlas manifest must contain a JSON object: {manifest_path}")

    reviewed_bucket_by_key: dict[str, str] = {}
    entries = payload.get("entries", [])
    if not isinstance(entries, list):
        raise SourceInventoryError(f"Atlas manifest has no entries list: {manifest_path}")
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        classification = classify_entry(entry)
        if not classification.counts_as_entry:
            continue
        lemma = str(entry.get("lemma") or "").strip()
        key = _lemma_key(lemma)
        if key:
            reviewed_bucket_by_key.setdefault(key, classification.bucket)

    return ReviewedAtlasState(
        manifest_loaded=True,
        manifest_sha256=hashlib.sha256(raw).hexdigest(),
        reviewed_bucket_by_key=reviewed_bucket_by_key,
        entry_census=build_entry_model_census(payload),
    )


def _public_source_inputs(inputs: Mapping[str, Any]) -> dict[str, Any]:
    """Return source-input metadata after stripping any accidental path-like keys."""
    forbidden_keys = {"path", "paths", "filename", "filenames", "source_title", "source_titles"}

    def clean(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {
                str(key): clean(item)
                for key, item in value.items()
                if str(key).casefold() not in forbidden_keys
            }
        if isinstance(value, list):
            return [clean(item) for item in value]
        return value

    return clean(dict(inputs))


def _match_lemmas(matches: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    lemmas = {
        str(match.get("lemma", "")).strip()
        for match in matches
        if isinstance(match, Mapping) and str(match.get("lemma", "")).strip()
    }
    return tuple(sorted(lemmas, key=_lemma_key))


def _normalize_headword(value: str) -> str | None:
    text = strip_acute_stress(str(value).strip()).replace("ʼ", "'").replace("’", "'").replace("`", "'")
    text = re.sub(r"\s+", " ", text).casefold().strip(" \t\r\n.,;:!?…")
    if not text:
        return None
    letters = re.sub(r"[^а-щьюяєіїґ']", "", text, flags=re.IGNORECASE)
    if len(letters.replace("'", "")) < 2:
        return None
    return text


def _looks_like_multiword(value: str) -> bool:
    return bool(MULTIWORD_DELIMITER_RE.search(value)) and len(WORD_TOKEN_RE.findall(value)) >= 2


def _looks_like_proper_name(pos: str | None) -> bool:
    if not pos:
        return False
    label = str(pos).casefold().replace("-", "_").replace(" ", "_")
    return "proper" in label or label in {"propn", "prop_noun"}


def _bucket_counts(candidates: Sequence[CandidateRecord]) -> Counter[str]:
    counts = Counter(candidate.bucket for candidate in candidates)
    return Counter({bucket: counts.get(bucket, 0) for bucket in SOURCE_ENTRY_BUCKETS})


def _inventory_source_units(records: Sequence[SourceInventoryRecord]) -> int:
    units = {
        (
            record.source_family,
            record.source_id or "<missing-source-id>",
            record.inventory_path,
        )
        for record in records
    }
    return len(units)


def _method_priority(method: str) -> int:
    return METHOD_PRIORITY.get(method, 0)


def _private_candidate_key(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}:{digest}"


def _resolve_path(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else root / path


def _resolve_optional_path(path: Path | None, root: Path) -> Path | None:
    if path is None:
        return None
    return _resolve_path(path, root)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a public-safe Word Atlas source entry-count census.")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT, help="Repository root to scan.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="Atlas manifest JSON path.")
    parser.add_argument("--skip-modules", action="store_true", help="Do not scan committed module surfaces.")
    parser.add_argument(
        "--skip-committed-inventories",
        action="store_true",
        help="Do not scan committed source-inventory files.",
    )
    parser.add_argument(
        "--inventory",
        dest="inventory_paths",
        action="append",
        type=Path,
        help="Committed source-inventory file to include; may be repeated.",
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
        default=atlas_source_census.DEFAULT_TEXTBOOK_TXT_ROOT,
        help="Extracted textbook TXT root.",
    )
    parser.add_argument("--skip-textbook-txt", action="store_true", help="Do not scan extracted textbook TXT.")
    parser.add_argument(
        "--sources-db",
        type=Path,
        default=atlas_source_census.DEFAULT_SOURCES_DB,
        help="Local sources.db path for the SQLite textbook corpus.",
    )
    parser.add_argument("--skip-sources-db", action="store_true", help="Do not scan SQLite textbook corpus.")
    parser.add_argument(
        "--textbook-jsonl-root",
        type=Path,
        default=DEFAULT_TEXTBOOK_JSONL_ROOT,
        help="Textbook chunk JSONL root; availability is reported aggregate-only.",
    )
    parser.add_argument("--skip-textbook-jsonl", action="store_true", help="Do not scan textbook JSONL chunks.")
    parser.add_argument("--skip-vesum", action="store_true", help="Do not lemmatize forms with VESUM.")
    parser.add_argument("--json-out", type=Path, help="Write public-safe JSON census.")
    parser.add_argument("--markdown-out", type=Path, help="Write public-safe Markdown report.")
    parser.add_argument("--detail-out", type=Path, help="Write local-only detail JSON outside the repository.")
    parser.add_argument("--detail-limit", type=int, default=DETAIL_LIMIT_DEFAULT, help="Top rows per lane in details.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.detail_limit < 1:
        parser.error("--detail-limit must be positive")

    root = args.root.resolve()
    ohoiko_roots = tuple(args.ohoiko_private_root or (atlas_source_census.DEFAULT_OHOIKO_PRIVATE_ROOT,))
    inventory_paths = tuple(args.inventory_paths) if args.inventory_paths else None
    try:
        result = build_source_entry_count(
            root=root,
            manifest_path=args.manifest,
            include_modules=not args.skip_modules,
            include_committed_inventories=not args.skip_committed_inventories,
            inventory_paths=inventory_paths,
            include_ohoiko_private=args.include_ohoiko_private,
            ohoiko_private_roots=ohoiko_roots,
            textbook_txt_root=None if args.skip_textbook_txt else args.textbook_txt_root,
            sources_db_path=None if args.skip_sources_db else args.sources_db,
            textbook_jsonl_root=None if args.skip_textbook_jsonl else args.textbook_jsonl_root,
            vesum_lookup=None if args.skip_vesum else verify_words,
        )
        if args.json_out:
            out = args.json_out if args.json_out.is_absolute() else root / args.json_out
            write_public_json(result, out)
        if args.markdown_out:
            out = args.markdown_out if args.markdown_out.is_absolute() else root / args.markdown_out
            write_public_markdown(result, out)
        if args.detail_out:
            write_detail_json(result, args.detail_out, project_root=root, limit=args.detail_limit)
    except (OSError, json.JSONDecodeError, SourceInventoryError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not args.json_out and not args.markdown_out:
        print(format_markdown_report(result.public_payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
