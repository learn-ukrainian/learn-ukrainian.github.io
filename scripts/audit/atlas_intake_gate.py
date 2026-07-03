#!/usr/bin/env python3
"""Deterministic candidate gate for Atlas intake foundation runs."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from scripts.audit.atlas_intake_registry import is_registered_source_family
from scripts.audit.source_inventory_intake import SourceInventoryCandidate

CLASSIFICATION_AUTO_APPROVE = "auto_approve"
CLASSIFICATION_REVIEW_QUEUE = "review_queue"
CLASSIFICATION_REJECT = "reject"

AtlasGateClassification = Literal["auto_approve", "review_queue", "reject"]

CLASSIFICATIONS: tuple[AtlasGateClassification, ...] = (
    CLASSIFICATION_AUTO_APPROVE,
    CLASSIFICATION_REVIEW_QUEUE,
    CLASSIFICATION_REJECT,
)


@dataclass(frozen=True)
class AtlasIntakeGateResult:
    """One deterministic gate decision for a source-inventory candidate."""

    lemma: str
    classification: AtlasGateClassification
    gate_evidence: dict[str, object]

    def candidate_payload(self) -> dict[str, object]:
        """Return the safe derived candidate schema for review/status output."""
        source_families = list(self.gate_evidence["source_families"])
        return {
            "lemma": self.lemma,
            "headword": self.lemma,
            "source_family": source_families[0] if len(source_families) == 1 else "multiple",
            "source_families": source_families,
            "source_ids": list(self.gate_evidence["source_ids"]),
            "locators": list(self.gate_evidence["locators"]),
            "count": self.gate_evidence["source_count"],
            "frequency": self.gate_evidence["frequency"],
            "classification": self.classification,
            "gate_evidence": self.gate_evidence,
        }


def classify_candidate(candidate: SourceInventoryCandidate) -> AtlasIntakeGateResult:
    """Classify one source-inventory candidate without mutating Atlas outputs."""
    source_families = _source_families(candidate.source_provenance)
    source_ids = _source_ids(candidate.source_provenance)
    locators = _locators(candidate.source_provenance)

    reject_reasons: list[str] = []
    review_reasons: list[str] = []

    if not _has_text(candidate.lemma):
        reject_reasons.append("missing_lemma")
    if not candidate.source_provenance:
        reject_reasons.append("missing_source_provenance")
    unknown_families = [family for family in source_families if not is_registered_source_family(family)]
    reject_reasons.extend(f"unknown_source_family:{family}" for family in unknown_families)
    if not source_families:
        reject_reasons.append("missing_source_family")
    if not source_ids:
        review_reasons.append("missing_source_id")
    if not locators:
        review_reasons.append("missing_locator")
    if not _has_text(candidate.pos):
        review_reasons.append("missing_pos")
    if not _has_text(candidate.gloss):
        review_reasons.append("missing_english_anchor")

    if reject_reasons:
        classification: AtlasGateClassification = CLASSIFICATION_REJECT
        reasons = reject_reasons + review_reasons
    elif review_reasons:
        classification = CLASSIFICATION_REVIEW_QUEUE
        reasons = review_reasons
    else:
        classification = CLASSIFICATION_AUTO_APPROVE
        reasons = ["deterministic_contract_satisfied"]

    source_count = candidate.source_count or len(candidate.source_provenance)
    frequency = candidate.frequency or _frequency(candidate.source_provenance) or source_count
    return AtlasIntakeGateResult(
        lemma=candidate.lemma,
        classification=classification,
        gate_evidence={
            "workflow": "atlas_intake_gate.v1",
            "source_families": source_families,
            "source_ids": source_ids,
            "locators": locators,
            "source_count": source_count,
            "frequency": frequency,
            "has_pos": _has_text(candidate.pos),
            "has_english_anchor": _has_text(candidate.gloss),
            "reasons": reasons,
        },
    )


def classify_candidates(
    candidates: Sequence[SourceInventoryCandidate],
) -> list[AtlasIntakeGateResult]:
    """Classify candidates in deterministic order."""
    return sorted(
        (classify_candidate(candidate) for candidate in candidates),
        key=lambda result: result.lemma.casefold(),
    )


def classification_counts(results: Sequence[AtlasIntakeGateResult]) -> dict[str, int]:
    """Return stable counts for all supported gate classifications."""
    counts = Counter(result.classification for result in results)
    return {classification: counts.get(classification, 0) for classification in CLASSIFICATIONS}


def _source_families(provenance: Sequence[Mapping[str, object]]) -> list[str]:
    families = {_clean_text(row.get("source_family")) for row in provenance}
    return sorted(family for family in families if family)


def _source_ids(provenance: Sequence[Mapping[str, object]]) -> list[str]:
    ids = {_clean_text(row.get("source_id")) for row in provenance}
    return sorted(source_id for source_id in ids if source_id)


def _locators(provenance: Sequence[Mapping[str, object]]) -> list[str]:
    locators = {
        _clean_text(row.get("source_locator")) or _clean_text(row.get("inventory_locator"))
        for row in provenance
    }
    return sorted(locator for locator in locators if locator)


def _frequency(provenance: Sequence[Mapping[str, object]]) -> int:
    total = 0
    for row in provenance:
        count = row.get("count", 1)
        if isinstance(count, int) and count > 0:
            total += count
        else:
            total += 1
    return total


def _clean_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _has_text(value: object) -> bool:
    return _clean_text(value) is not None
