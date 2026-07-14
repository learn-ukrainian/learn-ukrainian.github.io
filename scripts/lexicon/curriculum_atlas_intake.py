#!/usr/bin/env python3
"""Fail-closed full-text curriculum intake for Word Atlas (#4222).

This Phase 1 command inventories owned module Markdown and legacy
activity/vocabulary YAML, resolves Ukrainian forms through the project's VESUM
helpers, and emits safe source metadata. It never changes Atlas or learner
surface outputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Literal

import yaml

from scripts.audit.source_inventory_intake import (
    SourceInventoryRecord,
)
from scripts.audit.source_inventory_review_decisions import source_inventory_key
from scripts.lexicon.build_data_manifest import _lemma_key
from scripts.lexicon.content_lexicon_reconciler import (
    LEXICON_MANIFEST_PATH,
    PROJECT_ROOT,
    extract_ukrainian_tokens,
    lemmatize_forms,
    strip_mdx_to_prose,
)
from scripts.lexicon.heritage_classifier import classify_lemma
from scripts.lexicon.manifest_io import load_manifest

DEFAULT_CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
DEFAULT_INVENTORY_OUT = Path("/tmp/atlas-curriculum-full-text-inventory.json")
DEFAULT_REPORT_OUT = Path("/tmp/atlas-curriculum-full-text-intake.json")
DEFAULT_INVENTORY_PATH = "data/lexicon/source-inventory/curriculum-full-text-intake.json"
WORKFLOW_ID = "curriculum_full_text_atlas_intake.v1"
LEDGER_KIND = "atlas_source_inventory_review_decisions"
LEDGER_WORKFLOW = "source_inventory_publish_review_queue.v1"

SourceKind = Literal["module", "activity", "vocabulary"]
Classification = Literal["auto_approve", "review_queue", "reject"]
VesumLookup = Callable[[list[str]], dict[str, list[dict[str, Any]]]]
HeritageLookup = Callable[[str], dict[str, Any]]

SOURCE_PATTERNS: tuple[tuple[SourceKind, str, str], ...] = (
    ("module", "*/*/module.md", "module_markdown_token"),
    ("activity", "*/*/activities.yaml", "activity_token"),
    ("activity", "*/activities/*.yaml", "activity_token"),
    ("vocabulary", "*/*/vocabulary.yaml", "vocabulary_yaml_item"),
    ("vocabulary", "*/vocabulary/*.yaml", "vocabulary_yaml_item"),
)
METADATA_YAML_KEYS = frozenset(
    {
        "id",
        "module",
        "version",
        "level",
        "pos",
        "gender",
        "translation",
        "verified",
    }
)


class CurriculumIntakeError(ValueError):
    """A source cannot be safely included in a full-corpus intake."""


@dataclass(frozen=True)
class CurriculumSource:
    path: Path
    relative_path: str
    kind: SourceKind
    extraction_mode: str
    source_id: str


@dataclass(frozen=True)
class TokenOccurrence:
    form: str
    source: CurriculumSource
    locator: str
    count: int
    explicit_gloss: str | None = None


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
class CurriculumIntakeResult:
    sources: tuple[CurriculumSource, ...]
    token_occurrences: int
    unique_forms: int
    candidates: tuple[IntakeCandidate, ...]

    @property
    def source_counts(self) -> dict[str, int]:
        counts = Counter(source.kind for source in self.sources)
        return {
            "module": counts["module"],
            "activity": counts["activity"],
            "vocabulary": counts["vocabulary"],
        }

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

    def report_payload(self) -> dict[str, Any]:
        return {
            "workflow": WORKFLOW_ID,
            "policy": (
                "Full running-text curriculum intake. Uncertain VESUM or heritage outcomes "
                "are review_queue. This command does not update Atlas or learner surfaces."
            ),
            "production_outputs_updated": [],
            "surface_admission": {
                "daily_word": "unchanged",
                "practice": "unchanged",
                "cloze": "unchanged",
            },
            "counts": {
                "source_files": len(self.sources),
                **self.source_counts,
                "token_occurrences": self.token_occurrences,
                "unique_forms": self.unique_forms,
                "deduped_candidates": len(self.candidates),
                **self.classification_counts,
            },
            "classification_reasons": self.reason_counts,
            "sources": [
                {
                    "source_id": source.source_id,
                    "source_family": "curriculum",
                    "source_path": source.relative_path,
                    "source_kind": source.kind,
                    "extraction_mode": source.extraction_mode,
                }
                for source in self.sources
            ],
            "candidate_output": (
                "The decision-ledger-compatible output contains every candidate classification; "
                "this summary intentionally retains only aggregate counts."
            ),
        }


def discover_curriculum_sources(
    curriculum_root: Path = DEFAULT_CURRICULUM_ROOT,
    *,
    project_root: Path = PROJECT_ROOT,
) -> list[CurriculumSource]:
    """Discover each in-scope module, activity, and vocabulary source path."""

    root = curriculum_root.resolve()
    if not root.is_dir():
        raise CurriculumIntakeError(f"curriculum root not found: {curriculum_root}")
    sources: list[CurriculumSource] = []
    seen: set[Path] = set()
    for kind, pattern, extraction_mode in SOURCE_PATTERNS:
        for path in sorted(root.glob(pattern)):
            resolved = path.resolve()
            if not path.is_file() or resolved in seen:
                continue
            seen.add(resolved)
            try:
                relative_path = resolved.relative_to(project_root.resolve()).as_posix()
            except ValueError as exc:
                raise CurriculumIntakeError(f"source is outside project root: {resolved}") from exc
            sources.append(
                CurriculumSource(
                    path=resolved,
                    relative_path=relative_path,
                    kind=kind,
                    extraction_mode=extraction_mode,
                    source_id=source_id_for_path(relative_path),
                )
            )
    return sorted(sources, key=lambda source: source.relative_path)


def collect_curriculum_occurrences(sources: Sequence[CurriculumSource]) -> list[TokenOccurrence]:
    """Extract Ukrainian token counts from every running-text source scalar."""

    occurrences: list[TokenOccurrence] = []
    for source in sources:
        text = read_source_text(source)
        if source.kind == "module":
            occurrences.extend(token_occurrences(source, "module_body", strip_mdx_to_prose(text)))
            continue
        payload = load_yaml_source(source, text)
        if payload is None:
            continue
        for locator, value, explicit_gloss in iter_yaml_text(payload):
            if explicit_gloss:
                occurrences.extend(token_occurrences(source, locator, value, explicit_gloss=explicit_gloss))
            else:
                occurrences.extend(token_occurrences(source, locator, value))
    return compact_occurrences(occurrences)


def build_curriculum_intake(
    *,
    curriculum_root: Path = DEFAULT_CURRICULUM_ROOT,
    project_root: Path = PROJECT_ROOT,
    manifest_lemma_keys: set[str] | None = None,
    existing_ledger_keys: set[str] | None = None,
    vesum_lookup: VesumLookup | None = None,
    heritage_lookup: HeritageLookup = classify_lemma,
    inventory_path: str = DEFAULT_INVENTORY_PATH,
) -> CurriculumIntakeResult:
    """Run the complete read-only Phase 1 extraction and classification."""

    sources = discover_curriculum_sources(curriculum_root, project_root=project_root)
    occurrences = collect_curriculum_occurrences(sources)
    forms = tuple(sorted({occurrence.form for occurrence in occurrences}, key=stable_lemma_sort_key))
    resolutions = resolve_forms(forms, vesum_lookup=vesum_lookup)
    atlas_keys = manifest_lemma_keys if manifest_lemma_keys is not None else load_atlas_lemma_keys()
    ledger_keys = (
        existing_ledger_keys
        if existing_ledger_keys is not None
        else load_existing_ledger_keys(project_root=project_root)
    )
    candidates = build_candidates(
        occurrences,
        resolutions=resolutions,
        atlas_keys={_lemma_key(lemma) for lemma in atlas_keys},
        ledger_keys={_lemma_key(lemma) for lemma in ledger_keys},
        heritage_lookup=heritage_lookup,
        inventory_path=inventory_path,
    )
    return CurriculumIntakeResult(
        sources=tuple(sources),
        token_occurrences=sum(occurrence.count for occurrence in occurrences),
        unique_forms=len(forms),
        candidates=tuple(candidates),
    )


def load_atlas_lemma_keys(manifest_path: Path = LEXICON_MANIFEST_PATH) -> set[str]:
    """Load the current Atlas keys, hydrating the release-pinned default if needed."""

    payload = load_manifest(manifest_path)
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise CurriculumIntakeError(f"Atlas manifest has no entries list: {manifest_path}")
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


def build_ledger_append_payload(
    result: CurriculumIntakeResult,
    *,
    batch_id: str,
    batch_label: str,
    reviewed_at: str,
    inventory_path: str,
) -> dict[str, Any]:
    """Build a decision-ledger-compatible append without publishing any Atlas data."""

    auto_count = result.classification_counts["auto_approve"]
    decisions: list[dict[str, Any]] = []
    for candidate in result.candidates:
        primary = candidate.records[0]
        row: dict[str, Any] = {
            "lemma": candidate.lemma,
            "decision": ledger_decision(candidate),
            "sense_note": "Generated from full curriculum text; Atlas publication is a later phase.",
            "source_inventory": {
                "key": source_inventory_key(
                    lemma=candidate.lemma,
                    inventory_path=inventory_path,
                    locator=primary.inventory_locator,
                ),
                "path": inventory_path,
                "locator": primary.inventory_locator,
                "source_id": primary.source_id,
                "source_family": "curriculum",
            },
            "evidence_refs": list(candidate.reasons),
        }
        if candidate.classification == "auto_approve":
            if not candidate.pos or not candidate.gloss:
                raise CurriculumIntakeError("auto_approve candidate lacks required POS or gloss")
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
        "reviewer": "curriculum-intake-automation",
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


def write_flat_source_inventory(result: CurriculumIntakeResult, path: Path) -> None:
    """Stream source records in the established flat JSON inventory format."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write("[\n")
        for index, record in enumerate(result.records):
            if index:
                handle.write(",\n")
            json.dump(flat_inventory_row(record), handle, ensure_ascii=False, sort_keys=True)
        handle.write("\n]\n")


def flat_inventory_row(record: SourceInventoryRecord) -> dict[str, Any]:
    """Convert one safe record to the flat source-inventory schema."""

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
    """Require ledger metadata to name the exact inventory file being written."""

    try:
        output_path = inventory_out.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError as exc:
        raise CurriculumIntakeError(
            "--ledger-out requires --inventory-out inside the project root "
            "so source-ledger metadata remains portable"
        ) from exc
    inventory_prefix = "data/lexicon/source-inventory/"
    if not output_path.startswith(inventory_prefix):
        raise CurriculumIntakeError(
            "--ledger-out requires --inventory-out inside "
            "data/lexicon/source-inventory"
        )
    if inventory_path != output_path:
        raise CurriculumIntakeError(
            "--ledger-out requires --inventory-path to equal the project-relative "
            f"--inventory-out path ({output_path})"
        )


def format_summary(result: CurriculumIntakeResult) -> str:
    counts = result.classification_counts
    source_counts = result.source_counts
    return "\n".join(
        (
            "Curriculum Word Atlas intake",
            f"source_files: {len(result.sources)}",
            f"module_files: {source_counts['module']}",
            f"activity_files: {source_counts['activity']}",
            f"vocabulary_files: {source_counts['vocabulary']}",
            f"token_occurrences: {result.token_occurrences}",
            f"unique_forms: {result.unique_forms}",
            f"deduped_candidates: {len(result.candidates)}",
            f"auto_approve: {counts['auto_approve']}",
            f"review_queue: {counts['review_queue']}",
            f"reject: {counts['reject']}",
            "production_outputs_updated: []",
            "surface_admission: Daily Word unchanged; Practice unchanged; Cloze unchanged",
        )
    )


def read_source_text(source: CurriculumSource) -> str:
    try:
        return source.path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CurriculumIntakeError(f"cannot read curriculum source: {source.relative_path}") from exc


def load_yaml_source(source: CurriculumSource, text: str) -> object | None:
    try:
        payload = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise CurriculumIntakeError(f"invalid curriculum YAML: {source.relative_path}") from exc
    return payload


def load_yaml_mapping(path: Path, *, label: str) -> Mapping[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise CurriculumIntakeError(f"invalid {label} YAML: {path}") from exc
    if not isinstance(payload, Mapping):
        raise CurriculumIntakeError(f"invalid {label} mapping: {path}")
    return payload


def iter_yaml_text(payload: object, locator: str = "") -> Iterable[tuple[str, str, str | None]]:
    """Yield all learner-facing YAML scalar strings with structural locators."""

    if isinstance(payload, Mapping):
        direct_headword = mapping_text(payload, "lemma") or mapping_text(payload, "word")
        anchored_key = "lemma" if mapping_text(payload, "lemma") else "word"
        explicit_gloss = mapping_text(payload, "translation") if direct_headword else None
        for key, value in payload.items():
            key_text = str(key)
            child_locator = f"{locator}.{key_text}" if locator else key_text
            if key_text in METADATA_YAML_KEYS:
                continue
            if key_text in {"word", "lemma"} and isinstance(value, str):
                yield child_locator, value, explicit_gloss if key_text == anchored_key else None
            else:
                yield from iter_yaml_text(value, child_locator)
        return
    if isinstance(payload, list):
        for index, item in enumerate(payload):
            child_locator = f"{locator}[{index}]" if locator else f"[{index}]"
            yield from iter_yaml_text(item, child_locator)
        return
    if isinstance(payload, str):
        yield locator or "value", payload, None


def token_occurrences(
    source: CurriculumSource,
    locator: str,
    text: str,
    *,
    explicit_gloss: str | None = None,
) -> list[TokenOccurrence]:
    forms = extract_ukrainian_tokens(text)
    gloss = explicit_gloss if len(forms) == 1 else None
    counts = Counter(forms)
    return [
        TokenOccurrence(form=form, source=source, locator=locator, count=count, explicit_gloss=gloss)
        for form, count in sorted(counts.items(), key=lambda item: _lemma_key(item[0]))
    ]


def compact_occurrences(occurrences: Sequence[TokenOccurrence]) -> list[TokenOccurrence]:
    grouped: dict[tuple[str, str, str, str | None], TokenOccurrence] = {}
    for occurrence in occurrences:
        key = (
            occurrence.form,
            occurrence.source.relative_path,
            occurrence.locator,
            occurrence.explicit_gloss,
        )
        previous = grouped.get(key)
        grouped[key] = (
            occurrence
            if previous is None
            else TokenOccurrence(
                form=previous.form,
                source=previous.source,
                locator=previous.locator,
                count=previous.count + occurrence.count,
                explicit_gloss=previous.explicit_gloss,
            )
        )
    return sorted(
        grouped.values(),
        key=lambda item: (item.source.relative_path, item.locator, _lemma_key(item.form), item.explicit_gloss or ""),
    )


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


def build_candidates(
    occurrences: Sequence[TokenOccurrence],
    *,
    resolutions: Mapping[str, VesumResolution],
    atlas_keys: set[str],
    ledger_keys: set[str],
    heritage_lookup: HeritageLookup,
    inventory_path: str,
) -> list[IntakeCandidate]:
    resolved: dict[str, list[TokenOccurrence]] = defaultdict(list)
    unresolved: dict[str, list[TokenOccurrence]] = defaultdict(list)
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
        heritage_lookup=heritage_lookup,
        inventory_path=inventory_path,
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
    """Merge only exact emitted headword collisions before ledger emission.

    A VESUM-unresolved form can have the same normalized key as a resolved
    lemma. Case or stress variants must remain separate: their inventory rows
    have distinct raw lemmas, and retaining them gives reviewers the uncertain
    form instead of changing a known Atlas duplicate's disposition. Exact raw
    headword collisions, however, would create duplicate ledger keys at a
    shared locator, so they are consolidated deterministically.
    """

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
    """Combine same-headword source locations while preserving their total count."""

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
    grouped: Mapping[str, Sequence[TokenOccurrence]],
    *,
    resolutions: Mapping[str, VesumResolution],
    atlas_keys: set[str],
    ledger_keys: set[str],
    heritage_lookup: HeritageLookup,
    inventory_path: str,
) -> list[IntakeCandidate]:
    drafts: list[tuple[str, str, tuple[str, ...], str | None, str | None, tuple[str, ...], tuple[SourceInventoryRecord, ...]]] = []
    for key, occurrences in grouped.items():
        forms = tuple(sorted({occurrence.form for occurrence in occurrences}, key=stable_lemma_sort_key))
        lemma = resolutions[forms[0]].lemma
        if lemma is None:
            raise CurriculumIntakeError("resolved candidate lost its VESUM lemma")
        poss = {resolutions[form].pos for form in forms if resolutions[form].pos}
        resolution_reasons = {resolutions[form].reason for form in forms if resolutions[form].reason}
        pos = next(iter(poss)) if len(poss) == 1 and not resolution_reasons else None
        glosses = {occurrence.explicit_gloss.strip() for occurrence in occurrences if occurrence.explicit_gloss}
        gloss = next(iter(glosses)) if len(glosses) == 1 else None
        metadata_reasons = set(resolution_reasons)
        if len(poss) > 1:
            metadata_reasons.add("vesum_conflicting_pos")
        if len(glosses) > 1:
            metadata_reasons.add("conflicting_english_anchor")
        records = records_for_occurrences(
            occurrences,
            lemma=lemma,
            pos=pos,
            gloss=gloss,
            inventory_path=inventory_path,
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
    heritage_lookup: HeritageLookup,
) -> tuple[Classification, tuple[str, ...], Mapping[str, Any] | None]:
    lemma_key = _lemma_key(lemma)
    if lemma_key in atlas_keys:
        return "reject", ("already_in_atlas",), None
    if lemma_key in ledger_keys:
        return "reject", ("already_in_existing_ledger",), None
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
    occurrences: Sequence[TokenOccurrence],
    *,
    lemma: str,
    pos: str | None,
    gloss: str | None,
    inventory_path: str,
) -> tuple[SourceInventoryRecord, ...]:
    records = [
        SourceInventoryRecord(
            lemma=lemma,
            source_family="curriculum",
            extraction_mode=occurrence.source.extraction_mode,
            inventory_path=inventory_path,
            inventory_locator=safe_locator(occurrence),
            source_id=occurrence.source.source_id,
            source_title="Owned curriculum text",
            source_path=occurrence.source.relative_path,
            source_locator=safe_locator(occurrence),
            pos=pos,
            gloss=gloss,
            count=occurrence.count,
        )
        for occurrence in occurrences
    ]
    return merge_records((records,))


def safe_locator(occurrence: TokenOccurrence) -> str:
    """Return a ledger-unique, repository-safe source path and section locator."""

    return f"{occurrence.source.relative_path}::{occurrence.locator}"


def ledger_decision(candidate: IntakeCandidate) -> str:
    if candidate.classification == "auto_approve":
        return "approve_for_publish"
    return "needs_more_evidence" if candidate.classification == "review_queue" else "reject"


def source_id_for_path(relative_path: str) -> str:
    return f"curriculum-{hashlib.sha256(relative_path.encode('utf-8')).hexdigest()[:16]}"


def mapping_text(value: object, key: str) -> str | None:
    return normalised_text(value.get(key)) if isinstance(value, Mapping) else None


def normalised_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def stable_lemma_sort_key(value: str) -> tuple[str, str]:
    """Sort normalized headwords with their raw spelling as a deterministic tie-break."""

    return _lemma_key(value), value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run fail-closed full-text curriculum Word Atlas intake.")
    parser.add_argument("--curriculum-root", type=Path, default=DEFAULT_CURRICULUM_ROOT)
    parser.add_argument("--manifest", type=Path, default=LEXICON_MANIFEST_PATH)
    parser.add_argument("--inventory-path", default=DEFAULT_INVENTORY_PATH)
    parser.add_argument("--inventory-out", type=Path, default=DEFAULT_INVENTORY_OUT)
    parser.add_argument("--report-out", type=Path, default=DEFAULT_REPORT_OUT)
    parser.add_argument("--ledger-out", type=Path)
    parser.add_argument("--batch-id")
    parser.add_argument("--batch-label")
    parser.add_argument("--reviewed-at", help="Required when --ledger-out is supplied (YYYY-MM-DD).")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.ledger_out and not all((args.batch_id, args.batch_label, args.reviewed_at)):
        parser.error("--ledger-out requires --batch-id, --batch-label, and --reviewed-at")
    try:
        if args.ledger_out:
            assert_ledger_inventory_destination(args.inventory_out, args.inventory_path)
        result = build_curriculum_intake(
            curriculum_root=args.curriculum_root,
            manifest_lemma_keys=load_atlas_lemma_keys(args.manifest),
            inventory_path=args.inventory_path,
        )
        write_flat_source_inventory(result, args.inventory_out)
        write_json_payload(result.report_payload(), args.report_out)
        if args.ledger_out:
            write_yaml_payload(
                build_ledger_append_payload(
                    result,
                    batch_id=args.batch_id,
                    batch_label=args.batch_label,
                    reviewed_at=args.reviewed_at,
                    inventory_path=args.inventory_path,
                ),
                args.ledger_out,
            )
    except (CurriculumIntakeError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(format_summary(result))
    print(f"inventory_out: {args.inventory_out}")
    print(f"report_out: {args.report_out}")
    if args.ledger_out:
        print(f"ledger_out: {args.ledger_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
