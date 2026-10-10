"""Tests for A1/A2 immersion range bands (audit/config.py).

Approved #10105 A1 editorial bands with legacy module-position lookup:
- A1: 0–15%, 10–20%, 15–30%, 25–40%, 35–50%, 45–60%, 55–70%
- A2: easy Ukrainian is the default body voice; English is limited to glosses or one-line clarification
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from audit.config import get_a1_immersion_range, get_a2_immersion_range
from scripts.config import compute_immersion_band


class TestA1ImmersionRange:
    """Test get_a1_immersion_range band lookups."""

    def test_phonetics_band(self):
        """M1-3: approved initial English scaffolding band."""
        assert get_a1_immersion_range(1) == (0, 15)
        assert get_a1_immersion_range(3) == (0, 15)

    def test_identity_band(self):
        """M4-6: stress, identity, family."""
        assert get_a1_immersion_range(4) == (10, 20)
        assert get_a1_immersion_range(6) == (10, 20)

    def test_grammar_band(self):
        """M7-14: gender, adjectives, numbers."""
        assert get_a1_immersion_range(7) == (15, 30)
        assert get_a1_immersion_range(14) == (15, 30)

    def test_sentence_building_band(self):
        """M15-24: verbs, questions, possessives."""
        assert get_a1_immersion_range(15) == (25, 40)
        assert get_a1_immersion_range(24) == (25, 40)

    def test_cases_band(self):
        """M25-34: accusative, locative, genitive."""
        assert get_a1_immersion_range(25) == (35, 50)
        assert get_a1_immersion_range(34) == (35, 50)

    def test_daily_life_band(self):
        """M35-54: tense, food, travel."""
        assert get_a1_immersion_range(35) == (45, 60)
        assert get_a1_immersion_range(54) == (45, 60)

    def test_independence_band(self):
        """M55+: practical skills."""
        assert get_a1_immersion_range(55) == (55, 70)
        assert get_a1_immersion_range(64) == (55, 70)

    def test_immersion_increases_monotonically(self):
        """Min immersion never decreases as module number increases."""
        prev_min = 0
        for m in [1, 4, 7, 15, 25, 35, 55]:
            current_min, _ = get_a1_immersion_range(m)
            assert current_min >= prev_min, f"M{m}: {current_min} < {prev_min}"
            prev_min = current_min


class TestA2ImmersionRange:
    """Test get_a2_immersion_range with 5-band graduated system.

    Recalibrated 2026-06-16:
    - Bridge (M01-03): 75-100% — very easy Ukrainian after A1
    - Ramp (M04-07): 85-100% — easy Ukrainian body prose
    - Band 1 (M08-20): 85-100% — core A2 Ukrainian explanations
    - Band 2 (M21-50): 90-100% — richer Ukrainian with controlled connectors
    - Band 3 (M51-63): 95-100% — near-B1 Ukrainian, B1 prep
    """

    def test_bridge(self):
        """M01-03: bridge from A1."""
        assert get_a2_immersion_range(1) == (75, 100)
        assert get_a2_immersion_range(3) == (75, 100)

    def test_ramp(self):
        """M04-07: ramp up."""
        assert get_a2_immersion_range(4) == (85, 100)
        assert get_a2_immersion_range(7) == (85, 100)

    def test_band1_core_grammar(self):
        """M08-20: applied grammar, dialogue-rich."""
        assert get_a2_immersion_range(8) == (85, 100)
        assert get_a2_immersion_range(20) == (85, 100)

    def test_band2_applied_grammar(self):
        """M21-50: all cases, longer Ukrainian passages."""
        assert get_a2_immersion_range(21) == (90, 100)
        assert get_a2_immersion_range(50) == (90, 100)

    def test_band3_consolidation(self):
        """M51-63: near-full immersion, B1 prep."""
        assert get_a2_immersion_range(51) == (95, 100)
        assert get_a2_immersion_range(63) == (95, 100)

    def test_immersion_increases_monotonically(self):
        """Min immersion never decreases across A2 bands."""
        prev_min = 0
        for m in [1, 4, 8, 21, 51]:
            current_min, _ = get_a2_immersion_range(m)
            assert current_min >= prev_min, f"M{m}: {current_min} < {prev_min}"
            prev_min = current_min


@pytest.mark.parametrize("count,key,share", [
    (0, "a1-m01-03", (0, 15)), (24, "a1-m01-03", (0, 15)),
    (25, "a1-m04-06", (10, 20)), (59, "a1-m04-06", (10, 20)),
    (60, "a1-m07-14", (15, 30)), (139, "a1-m07-14", (15, 30)),
    (140, "a1-m15-24", (25, 40)), (241, "a1-m15-24", (25, 40)),
    (242, "a1-m25-34", (35, 50)), (399, "a1-m25-34", (35, 50)),
    (400, "a1-m35-54", (45, 60)), (599, "a1-m35-54", (45, 60)),
    (600, "a1-m55+", (55, 70)),
])
def test_explicit_core_counts_select_approved_bands_independent_of_position(count, key, share):
    for position in (1, 64):
        band = compute_immersion_band("a1", position, {"cumulative_vocabulary": count})
        assert band["key"] == key
        assert (band["advisory_pct_min"], band["advisory_pct_max"]) == share
