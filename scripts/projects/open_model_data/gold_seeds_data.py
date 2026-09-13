"""Curated specifications for 150 Human Gold Seeds (ULDR Phase 2, #8001).

Priority categories and quotas per DECOLONIZATION_EPIC_ARCHITECTURE.md § 3:
1. polysemy_sense (35 seeds): Polysemy & Sense Disambiguation
2. prepositional_gov (25 seeds): Prepositional Government
3. active_participles (25 seeds): Active Present Participles
4. voice_reflexivity (20 seeds): Voice, Reflexivity & Argument Structure
5. historical_authority (15 seeds): Historical Authority & Conflicting Lexicography
6. phraseology_collocations (15 seeds): Phraseology & Collocations
7. lexical_restitution (15 seeds): Lexical Interference & Purged Terminology
Total = 150 exemplar records.
"""

from __future__ import annotations

from scripts.projects.open_model_data.gold_seeds_types import CATEGORY_QUOTAS, RawGoldSeedSpec
from scripts.projects.open_model_data.seeds_history import HISTORY_SEEDS
from scripts.projects.open_model_data.seeds_participles import PARTICIPLE_SEEDS
from scripts.projects.open_model_data.seeds_phraseology import PHRASEOLOGY_SEEDS
from scripts.projects.open_model_data.seeds_polysemy import POLYSEMY_SEEDS
from scripts.projects.open_model_data.seeds_prepositions import PREPOSITION_SEEDS
from scripts.projects.open_model_data.seeds_restitution import RESTITUTION_SEEDS
from scripts.projects.open_model_data.seeds_voice import VOICE_SEEDS

RAW_GOLD_SEEDS: list[RawGoldSeedSpec] = [
    *POLYSEMY_SEEDS,
    *PREPOSITION_SEEDS,
    *PARTICIPLE_SEEDS,
    *VOICE_SEEDS,
    *HISTORY_SEEDS,
    *PHRASEOLOGY_SEEDS,
    *RESTITUTION_SEEDS,
]

# Invariant checks at import time
assert len(RAW_GOLD_SEEDS) == 150, f"Expected exactly 150 gold seeds, got {len(RAW_GOLD_SEEDS)}"

for cat, expected_count in CATEGORY_QUOTAS.items():
    actual_count = sum(1 for s in RAW_GOLD_SEEDS if s.category == cat)
    assert actual_count == expected_count, (
        f"Category quota mismatch for {cat}: expected {expected_count}, got {actual_count}"
    )
