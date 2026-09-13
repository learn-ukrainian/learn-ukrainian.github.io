"""Types and schema constants for 150 Human Gold Seeds (#8001)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RawGoldSeedSpec:
    category: str
    target_term: str
    query: str
    is_calque_or_russianism: bool
    source_formation: str
    ukrainian_equivalent_mechanism: str
    historical_suppression_note: str
    restoration_era: str
    primary_living_standard: str
    alternatives: tuple[tuple[str, str, str], ...]  # (lemma, register_tier, evidence_source)
    reasoning_steps: tuple[str, ...]
    final_response: str
    dpo_rejected: str
    dpo_rejected_flaw: str


CATEGORY_QUOTAS: dict[str, int] = {
    "polysemy_sense": 35,
    "prepositional_gov": 25,
    "active_participles": 25,
    "voice_reflexivity": 20,
    "historical_authority": 15,
    "phraseology_collocations": 15,
    "lexical_restitution": 15,
}
