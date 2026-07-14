#!/usr/bin/env python3
"""Shared Word Atlas intake core for fail-closed corpus extraction runs.

Extracted from the curriculum intake machinery (#4222 / PR #5136) so
family-specific adapters (curriculum, Ohoiko, …) reuse the same VESUM
resolution, heritage gating, dedupe, and ledger emission without forking.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Literal

import yaml

from scripts.audit.source_inventory_intake import SourceInventoryRecord
from scripts.audit.source_inventory_review_decisions import source_inventory_key
from scripts.lexicon.build_data_manifest import _lemma_key
from scripts.lexicon.content_lexicon_reconciler import (
    LEXICON_MANIFEST_PATH,
    PROJECT_ROOT,
    lemmatize_forms,
)
from scripts.lexicon.heritage_classifier import classify_lemma
from scripts.lexicon.manifest_io import load_manifest

LEDGER_KIND = "atlas_source_inventory_review_decisions"
LEDGER_WORKFLOW = "source_inventory_publish_review_queue.v1"

Classification = Literal["auto_approve", "review_queue", "reject"]
VesumLookup = Callable[[list[str]], dict[str, list[dict[str, Any]]]]
HeritageLookup = Callable[[str], dict[str, Any]]


class AtlasIntakeError(ValueError):
    """A source cannot be safely included in a full-corpus intake."""


@dataclass(frozen=True)
class IntakeOccurrence:
    """One counted Ukrainian form occurrence with safe locator metadata."""

    form: str
    source_id: str
    source_family: str
    extraction_mode: str
    locator: str
    count: int
    explicit_gloss: str | None = None
    source_title: str | None = None
    source_path: str | None = None


@dataclass(frozen=True)
class VesumResolution:
    form: str
    lemma: str | None
    pos: str | None
    reason: str | None


@dataclass(frozen=True)
class IntakeCandidate:
    candidate_key: str
    lemma: str
    forms: tuple[str, ...]
    pos: str | None
    gloss: str | None
    records: tuple[SourceInventoryRecord, ...]
    classification: Classification
    reasons: tuple[str, ...]
    heritage_status: Mapping[str, Any] | None

    @property
    def frequency(self) -> int:
        return sum(record.count for record in self.records)


@dataclass(frozen=True)
class AtlasIntakeResult:
    """Generic intake summary for any source-family adapter."""

    workflow: str
    source_family: str
    source_units: tuple[Mapping[str, Any], ...]
    token_occurrences: int
    unique_forms: int
    candidates: tuple[IntakeCandidate, ...]
    inventory_path: str

    @property
    def classification_counts(self) -> dict[str, int]:
        counts = Counter(candidate.classification for candidate in self.candidates)
        return {
            "auto_approve": counts["auto_approve"],
            "review_queue": counts["review_queue"],
            "reject": counts["reject"],
        }

    @property
    def reason_counts(self) -> dict[str, int]:
        counts: Counter[str] = Counter()
        for candidate in self.candidates:
            counts.update(candidate.reasons)
        return dict(sorted(counts.items()))

    @property
    def records(self) -> tuple[SourceInventoryRecord, ...]:
        return tuple(record for candidate in self.candidates for record in candidate.records)

    def report_payload(self, *, policy: str) -> dict[str, Any]:
        return {
            "workflow": self.workflow,
            "policy": policy,
            "production_outputs_updated": [],
            "surface_admission": {
                "daily_word": "unchanged",
                "practice": "unchanged",
                "cloze": "unchanged",
            },
            "counts": {
                "source_units": len(self.source_units),
                "token_occurrences": self.token_occurrences,
                "unique_forms": self.unique_forms,
                "deduped_candidates": len(self.candidates),
                **self.classification_counts,
            },
            "classification_reasons": self.reason_counts,
            "sources": list(self.source_units),
            "candidate_output": (
                "The decision-ledger-compatible output contains every candidate classification; "
                "this summary intentionally retains only aggregate counts."
            ),
        }


def load_atlas_lemma_keys(manifest_path: Path = LEXICON_MANIFEST_PATH) -> set[str]:
    """Load the current Atlas keys, hydrating the release-pinned default if needed."""

    payload = load_manifest(manifest_path)
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise AtlasIntakeError(f"Atlas manifest has no entries list: {manifest_path}")
    return {
        _lemma_key(lemma)
        for entry in entries
        if isinstance(entry, Mapping)
        for lemma in [entry.get("lemma")]
        if isinstance(lemma, str) and lemma.strip()
    }


def load_existing_ledger_keys(*, project_root: Path = PROJECT_ROOT) -> set[str]:
    """Return lemma keys that have prior source-ledger decisions."""

    root = project_root.resolve()
    keys: set[str] = set()
    for path in sorted((root / "data" / "lexicon" / "source-inventory-review-decisions").glob("*.yaml")):
        payload = load_yaml_mapping(path, label="source decision ledger")
        if payload.get("kind") != LEDGER_KIND:
            continue
        for decision in payload.get("decisions", []):
            lemma = mapping_text(decision, "lemma")
            if lemma:
                keys.add(_lemma_key(lemma))
    return keys


def load_committed_inventory_keys(
    inventory_paths: Sequence[Path],
    *,
    project_root: Path = PROJECT_ROOT,
) -> set[str]:
    """Return lemma keys already present in committed source inventories."""

    from scripts.audit.source_inventory_intake import read_source_inventories

    existing = [path for path in inventory_paths if path.exists()]
    if not existing:
        return set()
    records = read_source_inventories(existing, project_root=project_root)
    return {_lemma_key(record.lemma) for record in records}


def resolve_forms(forms: Sequence[str], *, vesum_lookup: VesumLookup | None) -> dict[str, VesumResolution]:
    matches_by_form = lemmatize_forms(forms) if vesum_lookup is None else lemmatize_forms(forms, vesum_lookup=vesum_lookup)
    resolutions: dict[str, VesumResolution] = {}
    for form in forms:
        matches = matches_by_form.get(form, [])
        lemmas = {
            normalised_text(match.get("lemma"))
            for match in matches
            if isinstance(match, Mapping) and normalised_text(match.get("lemma"))
        }
        if not lemmas:
            resolutions[form] = VesumResolution(form, None, None, "vesum_unrecognized")
            continue
        if len(lemmas) != 1:
            resolutions[form] = VesumResolution(form, None, None, "vesum_ambiguous_lemma")
            continue
        poss = {
            normalised_text(match.get("pos"))
            for match in matches
            if isinstance(match, Mapping) and normalised_text(match.get("pos"))
        }
        lemma = next(iter(lemmas))
        if len(poss) != 1:
            resolutions[form] = VesumResolution(form, lemma, None, "vesum_ambiguous_pos")
            continue
        resolutions[form] = VesumResolution(form, lemma, next(iter(poss)), None)
    return resolutions


def build_intake_candidates(
    occurrences: Sequence[IntakeOccurrence],
    *,
    resolutions: Mapping[str, VesumResolution],
    atlas_keys: set[str],
    ledger_keys: set[str],
    committed_inventory_keys: set[str],
    heritage_lookup: HeritageLookup,
    inventory_path: str,
    source_family: str,
) -> list[IntakeCandidate]:
    resolved: dict[str, list[IntakeOccurrence]] = defaultdict(list)
    unresolved: dict[str, list[IntakeOccurrence]] = defaultdict(list)
    for occurrence in occurrences:
        resolution = resolutions[occurrence.form]
        if resolution.lemma is None:
            unresolved[_lemma_key(occurrence.form)].append(occurrence)
        else:
            resolved[_lemma_key(resolution.lemma)].append(occurrence)
    candidates = build_resolved_candidates(
        resolved,
        resolutions=resolutions,
        atlas_keys=atlas_keys,
        ledger_keys=ledger_keys,
        committed_inventory_keys=committed_inventory_keys,
        heritage_lookup=heritage_lookup,
        inventory_path=inventory_path,
        source_family=source_family,
    )
    for key, grouped_occurrences in unresolved.items():
        forms = tuple(
            sorted({occurrence.form for occurrence in grouped_occurrences}, key=stable_lemma_sort_key)
        )
        records = records_for_occurrences(
            grouped_occurrences,
            lemma=forms[0],
            pos=None,
            gloss=None,
            inventory_path=inventory_path,
            source_family=source_family,
        )
        candidates.append(
            IntakeCandidate(
                candidate_key=f"form:{key}",
                lemma=forms[0],
                forms=forms,
                pos=None,
                gloss=None,
                records=records,
                classification="review_queue",
                reasons=tuple(sorted({resolutions[form].reason or "vesum_unresolved" for form in forms})),
                heritage_status=None,
            )
        )
    return merge_candidate_collisions(candidates)


def merge_candidate_collisions(candidates: Sequence[IntakeCandidate]) -> list[IntakeCandidate]:
    grouped: dict[str, list[IntakeCandidate]] = defaultdict(list)
    for candidate in candidates:
        grouped[candidate.lemma].append(candidate)
    merged: list[IntakeCandidate] = []
    for lemma, group in grouped.items():
        if len(group) == 1:
            merged.append(group[0])
            continue
        classifications = {candidate.classification for candidate in group}
        classification: Classification = "reject" if "reject" in classifications else "review_queue"
        poss = {candidate.pos for candidate in group if candidate.pos}
        glosses = {candidate.gloss for candidate in group if candidate.gloss}
        reasons = {reason for candidate in group for reason in candidate.reasons}
        reasons.add("canonical_headword_collision")
        if len(poss) > 1:
            reasons.add("vesum_conflicting_pos")
        if len(glosses) > 1:
            reasons.add("conflicting_english_anchor")
        pos = next(iter(poss)) if len(poss) == 1 else None
        gloss = next(iter(glosses)) if len(glosses) == 1 else None
        merged.append(
            IntakeCandidate(
                candidate_key=f"merged:{_lemma_key(lemma)}",
                lemma=lemma,
                forms=tuple(
                    sorted(
                        {form for candidate in group for form in candidate.forms},
                        key=stable_lemma_sort_key,
                    )
                ),
                pos=pos,
                gloss=gloss,
                records=merge_records(candidate.records for candidate in group),
                classification=classification,
                reasons=tuple(sorted(reasons)),
                heritage_status=next(
                    (
                        candidate.heritage_status
                        for candidate in group
                        if candidate.heritage_status is not None
                    ),
                    None,
                ),
            )
        )
    return sorted(
        merged,
        key=lambda candidate: (candidate.lemma.casefold(), candidate.lemma, candidate.candidate_key),
    )


def merge_records(
    record_groups: Iterable[Sequence[SourceInventoryRecord]],
) -> tuple[SourceInventoryRecord, ...]:
    merged: dict[tuple[str, str, str, str], SourceInventoryRecord] = {}
    for records in record_groups:
        for record in records:
            key = (
                record.lemma,
                record.source_id or "",
                record.source_path or "",
                record.source_locator or "",
            )
            previous = merged.get(key)
            merged[key] = record if previous is None else replace(previous, count=previous.count + record.count)
    return tuple(
        sorted(
            merged.values(),
            key=lambda record: (
                record.source_path or "",
                record.source_locator or "",
                _lemma_key(record.lemma),
                record.lemma,
            ),
        )
    )


def build_resolved_candidates(
    grouped: Mapping[str, Sequence[IntakeOccurrence]],
    *,
    resolutions: Mapping[str, VesumResolution],
    atlas_keys: set[str],
    ledger_keys: set[str],
    committed_inventory_keys: set[str],
    heritage_lookup: HeritageLookup,
    inventory_path: str,
    source_family: str,
) -> list[IntakeCandidate]:
    drafts: list[
        tuple[str, str, tuple[str, ...], str | None, str | None, tuple[str, ...], tuple[SourceInventoryRecord, ...]]
    ] = []
    for key, grouped_occurrences in grouped.items():
        forms = tuple(sorted({occurrence.form for occurrence in grouped_occurrences}, key=stable_lemma_sort_key))
        lemma = resolutions[forms[0]].lemma
        if lemma is None:
            raise AtlasIntakeError("resolved candidate lost its VESUM lemma")
        poss = {resolutions[form].pos for form in forms if resolutions[form].pos}
        resolution_reasons = {resolutions[form].reason for form in forms if resolutions[form].reason}
        pos = next(iter(poss)) if len(poss) == 1 and not resolution_reasons else None
        glosses = {occurrence.explicit_gloss.strip() for occurrence in grouped_occurrences if occurrence.explicit_gloss}
        gloss = next(iter(glosses)) if len(glosses) == 1 else None
        metadata_reasons = set(resolution_reasons)
        if len(poss) > 1:
            metadata_reasons.add("vesum_conflicting_pos")
        if len(glosses) > 1:
            metadata_reasons.add("conflicting_english_anchor")
        records = records_for_occurrences(
            grouped_occurrences,
            lemma=lemma,
            pos=pos,
            gloss=gloss,
            inventory_path=inventory_path,
            source_family=source_family,
        )
        drafts.append((key, lemma, forms, pos, gloss, tuple(sorted(metadata_reasons)), records))

    candidates: list[IntakeCandidate] = []
    for key, lemma, forms, pos, gloss, metadata_reasons, records in drafts:
        classification, reasons, heritage_status = classify_resolved_candidate(
            lemma=lemma,
            pos=pos,
            gloss=gloss,
            metadata_reasons=metadata_reasons,
            atlas_keys=atlas_keys,
            ledger_keys=ledger_keys,
            committed_inventory_keys=committed_inventory_keys,
            heritage_lookup=heritage_lookup,
        )
        candidates.append(
            IntakeCandidate(
                candidate_key=f"lemma:{key}",
                lemma=lemma,
                forms=forms,
                pos=pos,
                gloss=gloss,
                records=records,
                classification=classification,
                reasons=reasons,
                heritage_status=heritage_status,
            )
        )
    return candidates


def classify_resolved_candidate(
    *,
    lemma: str,
    pos: str | None,
    gloss: str | None,
    metadata_reasons: Sequence[str],
    atlas_keys: set[str],
    ledger_keys: set[str],
    committed_inventory_keys: set[str],
    heritage_lookup: HeritageLookup,
) -> tuple[Classification, tuple[str, ...], Mapping[str, Any] | None]:
    lemma_key = _lemma_key(lemma)
    if lemma_key in atlas_keys:
        return "reject", ("already_in_atlas",), None
    if lemma_key in ledger_keys:
        return "reject", ("already_in_existing_ledger",), None
    if lemma_key in committed_inventory_keys:
        return "reject", ("already_in_committed_source_inventory",), None
    if metadata_reasons:
        return "review_queue", tuple(metadata_reasons), None
    if not pos:
        return "review_queue", ("vesum_ambiguous_pos",), None
    if not gloss:
        return "review_queue", ("missing_english_anchor",), None
    try:
        heritage = heritage_lookup(lemma)
    except Exception:
        return "review_queue", ("heritage_lookup_failed",), None
    classification = normalised_text(heritage.get("classification")) if isinstance(heritage, Mapping) else None
    if not classification:
        return "review_queue", ("heritage_unresolved",), None
    if bool(heritage.get("is_russianism")) or classification == "russianism":
        return "reject", ("heritage_russianism",), heritage
    if classification == "surzhyk":
        return "reject", ("heritage_surzhyk",), heritage
    if bool(heritage.get("russian_shadow")):
        return "review_queue", ("heritage_russian_shadow",), heritage
    sovietization_risk = heritage.get("sovietization_risk")
    if not isinstance(sovietization_risk, int):
        return "review_queue", ("heritage_sovietization_risk_unknown",), heritage
    if sovietization_risk > 0:
        return "review_queue", ("heritage_sovietization_risk",), heritage
    if classification != "standard":
        return "review_queue", ("heritage_nonstandard_classification",), heritage
    return "auto_approve", ("vesum_unique_lemma_pos", "explicit_english_anchor", "heritage_clear"), heritage


def records_for_occurrences(
    occurrences: Sequence[IntakeOccurrence],
    *,
    lemma: str,
    pos: str | None,
    gloss: str | None,
    inventory_path: str,
    source_family: str,
) -> tuple[SourceInventoryRecord, ...]:
    records = [
        SourceInventoryRecord(
            lemma=lemma,
            source_family=source_family,
            extraction_mode=occurrence.extraction_mode,
            inventory_path=inventory_path,
            inventory_locator=safe_locator(occurrence),
            source_id=occurrence.source_id,
            source_title=occurrence.source_title,
            source_path=occurrence.source_path,
            source_locator=safe_locator(occurrence),
            pos=pos,
            gloss=gloss,
            count=occurrence.count,
        )
        for occurrence in occurrences
    ]
    return merge_records((records,))


def safe_locator(occurrence: IntakeOccurrence) -> str:
    return occurrence.locator


def build_ledger_append_payload(
    result: AtlasIntakeResult,
    *,
    batch_id: str,
    batch_label: str,
    reviewed_at: str,
    reviewer: str,
) -> dict[str, Any]:
    auto_count = result.classification_counts["auto_approve"]
    decisions: list[dict[str, Any]] = []
    for candidate in result.candidates:
        primary = candidate.records[0]
        row: dict[str, Any] = {
            "lemma": candidate.lemma,
            "decision": ledger_decision(candidate),
            "sense_note": "Generated from Ohoiko corpus intake; Atlas publication is a later phase.",
            "source_inventory": {
                "key": source_inventory_key(
                    lemma=candidate.lemma,
                    inventory_path=result.inventory_path,
                    locator=primary.inventory_locator,
                ),
                "path": result.inventory_path,
                "locator": primary.inventory_locator,
                "source_id": primary.source_id,
                "source_family": result.source_family,
            },
            "evidence_refs": list(candidate.reasons),
        }
        if candidate.classification == "auto_approve":
            if not candidate.pos or not candidate.gloss:
                raise AtlasIntakeError("auto_approve candidate lacks required POS or gloss")
            row["approved_pos"] = candidate.pos
            row["approved_gloss"] = candidate.gloss
        elif candidate.classification == "review_queue":
            row["review_queue_reasons"] = list(candidate.reasons)
        else:
            row["original_flags"] = list(candidate.reasons)
        decisions.append(row)
    return {
        "version": 1,
        "kind": LEDGER_KIND,
        "batch_id": batch_id,
        "batch_label": batch_label,
        "reviewer": reviewer,
        "reviewed_at": reviewed_at,
        "source_queue": {
            "workflow": LEDGER_WORKFLOW,
            "total_queue_rows": len(result.candidates),
            "approved_in_queue": auto_count,
            "promotion_batch_size": max(auto_count, 1),
        },
        "production_outputs_updated": [],
        "decisions": decisions,
    }


def write_yaml_payload(payload: Mapping[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(dict(payload), allow_unicode=True, sort_keys=False), encoding="utf-8")


def write_flat_source_inventory(records: Sequence[SourceInventoryRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write("[\n")
        for index, record in enumerate(records):
            if index:
                handle.write(",\n")
            json.dump(flat_inventory_row(record), handle, ensure_ascii=False, sort_keys=True)
        handle.write("\n]\n")


def flat_inventory_row(record: SourceInventoryRecord) -> dict[str, Any]:
    row: dict[str, Any] = {
        "lemma": record.lemma,
        "source_family": record.source_family,
        "extraction_mode": record.extraction_mode,
        "source_id": record.source_id,
        "source_title": record.source_title,
        "source_path": record.source_path,
        "source_locator": record.source_locator,
        "count": record.count,
    }
    if record.pos:
        row["pos"] = record.pos
    if record.gloss:
        row["gloss"] = record.gloss
    return row


def write_json_payload(payload: Mapping[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_ledger_inventory_destination(
    inventory_out: Path,
    inventory_path: str,
    *,
    project_root: Path = PROJECT_ROOT,
) -> None:
    try:
        output_path = inventory_out.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError as exc:
        raise AtlasIntakeError(
            "--ledger-out requires --inventory-out inside the project root "
            "so source-ledger metadata remains portable"
        ) from exc
    inventory_prefix = "data/lexicon/source-inventory/"
    if not output_path.startswith(inventory_prefix):
        raise AtlasIntakeError(
            "--ledger-out requires --inventory-out inside data/lexicon/source-inventory"
        )
    if inventory_path != output_path:
        raise AtlasIntakeError(
            "--ledger-out requires --inventory-path to equal the project-relative "
            f"--inventory-out path ({output_path})"
        )


def ledger_decision(candidate: IntakeCandidate) -> str:
    if candidate.classification == "auto_approve":
        return "approve_for_publish"
    return "needs_more_evidence" if candidate.classification == "review_queue" else "reject"


def load_yaml_mapping(path: Path, *, label: str) -> Mapping[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise AtlasIntakeError(f"invalid {label} YAML: {path}") from exc
    if not isinstance(payload, Mapping):
        raise AtlasIntakeError(f"invalid {label} mapping: {path}")
    return payload


def mapping_text(value: object, key: str) -> str | None:
    return normalised_text(value.get(key)) if isinstance(value, Mapping) else None


def normalised_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def stable_lemma_sort_key(value: str) -> tuple[str, str]:
    return _lemma_key(value), value
