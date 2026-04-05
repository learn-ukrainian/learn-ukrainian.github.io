"""Tests for A1/A2 immersion range bands (audit/config.py).

Updated 2026-04-04 to match the April 3 recalibration:
- A1: wider upper bounds (dialogue-rich content raises immersion naturally)
- A2: 5-band graduated system (bridge, ramp, band1, band2, band3)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from audit.config import get_a1_immersion_range, get_a2_immersion_range


class TestA1ImmersionRange:
    """Test get_a1_immersion_range band lookups."""

    def test_phonetics_band(self):
        """M1-3: lowest immersion (phonetics, mostly English)."""
        assert get_a1_immersion_range(1) == (5, 25)
        assert get_a1_immersion_range(3) == (5, 25)

    def test_identity_band(self):
        """M4-6: stress, identity, family."""
        assert get_a1_immersion_range(4) == (8, 30)
        assert get_a1_immersion_range(6) == (8, 30)

    def test_grammar_band(self):
        """M7-14: gender, adjectives, numbers."""
        assert get_a1_immersion_range(7) == (10, 38)
        assert get_a1_immersion_range(14) == (10, 38)

    def test_sentence_building_band(self):
        """M15-24: verbs, questions, possessives."""
        assert get_a1_immersion_range(15) == (15, 35)
        assert get_a1_immersion_range(24) == (15, 35)

    def test_cases_band(self):
        """M25-34: accusative, locative, genitive."""
        assert get_a1_immersion_range(25) == (15, 40)
        assert get_a1_immersion_range(34) == (15, 40)

    def test_daily_life_band(self):
        """M35-54: tense, food, travel."""
        assert get_a1_immersion_range(35) == (20, 40)
        assert get_a1_immersion_range(54) == (20, 40)

    def test_independence_band(self):
        """M55+: practical skills."""
        assert get_a1_immersion_range(55) == (25, 48)
        assert get_a1_immersion_range(64) == (25, 48)

    def test_immersion_increases_monotonically(self):
        """Min immersion never decreases as module number increases."""
        prev_min = 0
        for m in [1, 4, 7, 15, 25, 35, 55]:
            current_min, _ = get_a1_immersion_range(m)
            assert current_min >= prev_min, f"M{m}: {current_min} < {prev_min}"
            prev_min = current_min


class TestA2ImmersionRange:
    """Test get_a2_immersion_range with 5-band graduated system.

    Recalibrated 2026-04-03:
    - Bridge (M01-03): 20-48% — A1→A2 transition, overlaps with A1 finale range
    - Ramp (M04-07): 30-55% — genitive intro, dialogues increasing
    - Band 1 (M08-20): 40-70% — applied grammar, dialogue-rich
    - Band 2 (M21-50): 50-80% — all cases, longer Ukrainian passages
    - Band 3 (M51-63): 65-90% — near-full immersion, B1 prep
    """

    def test_bridge(self):
        """M01-03: bridge from A1."""
        assert get_a2_immersion_range(1) == (20, 48)
        assert get_a2_immersion_range(3) == (20, 48)

    def test_ramp(self):
        """M04-07: ramp up."""
        assert get_a2_immersion_range(4) == (30, 55)
        assert get_a2_immersion_range(7) == (30, 55)

    def test_band1_core_grammar(self):
        """M08-20: applied grammar, dialogue-rich."""
        assert get_a2_immersion_range(8) == (40, 70)
        assert get_a2_immersion_range(20) == (40, 70)

    def test_band2_applied_grammar(self):
        """M21-50: all cases, longer Ukrainian passages."""
        assert get_a2_immersion_range(21) == (50, 80)
        assert get_a2_immersion_range(50) == (50, 80)

    def test_band3_consolidation(self):
        """M51-63: near-full immersion, B1 prep."""
        assert get_a2_immersion_range(51) == (65, 90)
        assert get_a2_immersion_range(63) == (65, 90)

    def test_immersion_increases_monotonically(self):
        """Min immersion never decreases across A2 bands."""
        prev_min = 0
        for m in [1, 4, 8, 21, 51]:
            current_min, _ = get_a2_immersion_range(m)
            assert current_min >= prev_min, f"M{m}: {current_min} < {prev_min}"
            prev_min = current_min
