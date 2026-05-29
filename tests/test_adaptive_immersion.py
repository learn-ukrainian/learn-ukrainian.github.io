"""Tests for A1/A2 immersion range bands (audit/config.py).

Updated 2026-05-30 for the Ohoiko/ULP S1 harness:
- A1: every core band uses 40-55% Ukrainian-first immersion
- A2: S1 bridge/ramp/band1 use 40-55%, later A2 bands continue to ramp
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from audit.config import get_a1_immersion_range, get_a2_immersion_range


class TestA1ImmersionRange:
    """Test get_a1_immersion_range band lookups."""

    def test_phonetics_band(self):
        """M1-3: ULP S1 baseline."""
        assert get_a1_immersion_range(1) == (40, 55)
        assert get_a1_immersion_range(3) == (40, 55)

    def test_identity_band(self):
        """M4-6: stress, identity, family."""
        assert get_a1_immersion_range(4) == (40, 55)
        assert get_a1_immersion_range(6) == (40, 55)

    def test_grammar_band(self):
        """M7-14: gender, adjectives, numbers."""
        assert get_a1_immersion_range(7) == (40, 55)
        assert get_a1_immersion_range(14) == (40, 55)

    def test_sentence_building_band(self):
        """M15-24: verbs, questions, possessives."""
        assert get_a1_immersion_range(15) == (40, 55)
        assert get_a1_immersion_range(24) == (40, 55)

    def test_cases_band(self):
        """M25-34: accusative, locative, genitive."""
        assert get_a1_immersion_range(25) == (40, 55)
        assert get_a1_immersion_range(34) == (40, 55)

    def test_daily_life_band(self):
        """M35-54: tense, food, travel."""
        assert get_a1_immersion_range(35) == (40, 55)
        assert get_a1_immersion_range(54) == (40, 55)

    def test_independence_band(self):
        """M55+: practical skills."""
        assert get_a1_immersion_range(55) == (40, 55)
        assert get_a1_immersion_range(64) == (40, 55)

    def test_immersion_increases_monotonically(self):
        """Min immersion never decreases as module number increases."""
        prev_min = 0
        for m in [1, 4, 7, 15, 25, 35, 55]:
            current_min, _ = get_a1_immersion_range(m)
            assert current_min >= prev_min, f"M{m}: {current_min} < {prev_min}"
            prev_min = current_min


class TestA2ImmersionRange:
    """Test get_a2_immersion_range with 5-band graduated system.

    Recalibrated 2026-05-30:
    - Bridge (M01-03): 40-55% — ULP S1 baseline
    - Ramp (M04-07): 40-55% — ULP S1 baseline
    - Band 1 (M08-20): 40-55% — ULP S1 baseline
    - Band 2 (M21-50): 50-80% — all cases, longer Ukrainian passages
    - Band 3 (M51-63): 65-90% — near-full immersion, B1 prep
    """

    def test_bridge(self):
        """M01-03: bridge from A1."""
        assert get_a2_immersion_range(1) == (40, 55)
        assert get_a2_immersion_range(3) == (40, 55)

    def test_ramp(self):
        """M04-07: ramp up."""
        assert get_a2_immersion_range(4) == (40, 55)
        assert get_a2_immersion_range(7) == (40, 55)

    def test_band1_core_grammar(self):
        """M08-20: applied grammar, dialogue-rich."""
        assert get_a2_immersion_range(8) == (40, 55)
        assert get_a2_immersion_range(20) == (40, 55)

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
