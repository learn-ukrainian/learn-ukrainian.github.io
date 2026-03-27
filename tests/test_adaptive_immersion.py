"""Tests for A1/A2 immersion range bands (audit/config.py)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from audit.config import get_a1_immersion_range, get_a2_immersion_range


class TestA1ImmersionRange:
    """Test get_a1_immersion_range band lookups."""

    def test_phonetics_band(self):
        """M1-3: lowest immersion (phonetics, mostly English)."""
        assert get_a1_immersion_range(1) == (5, 15)
        assert get_a1_immersion_range(3) == (5, 15)

    def test_identity_band(self):
        """M4-6: stress, identity, family."""
        assert get_a1_immersion_range(4) == (8, 25)
        assert get_a1_immersion_range(6) == (8, 25)

    def test_grammar_band(self):
        """M7-14: gender, adjectives, numbers."""
        assert get_a1_immersion_range(7) == (10, 30)
        assert get_a1_immersion_range(14) == (10, 30)

    def test_sentence_building_band(self):
        """M15-24: verbs, questions, possessives."""
        assert get_a1_immersion_range(15) == (15, 25)
        assert get_a1_immersion_range(24) == (15, 25)

    def test_cases_band(self):
        """M25-34: accusative, locative, genitive."""
        assert get_a1_immersion_range(25) == (15, 30)
        assert get_a1_immersion_range(34) == (15, 30)

    def test_daily_life_band(self):
        """M35-54: tense, food, travel."""
        assert get_a1_immersion_range(35) == (20, 35)
        assert get_a1_immersion_range(54) == (20, 35)

    def test_independence_band(self):
        """M55+: practical skills."""
        assert get_a1_immersion_range(55) == (25, 40)
        assert get_a1_immersion_range(64) == (25, 40)

    def test_immersion_increases_monotonically(self):
        """Min immersion never decreases as module number increases."""
        prev_min = 0
        for m in [1, 4, 7, 15, 25, 35, 55]:
            current_min, _ = get_a1_immersion_range(m)
            assert current_min >= prev_min, f"M{m}: {current_min} < {prev_min}"
            prev_min = current_min

    def test_sandbox_param_accepted(self):
        """sandbox_lemma_count param is accepted (backward compat)."""
        # Function accepts but ignores sandbox_lemma_count
        result = get_a1_immersion_range(10, sandbox_lemma_count=5)
        assert isinstance(result, tuple)
        assert len(result) == 2


class TestA2ImmersionRange:
    """Test get_a2_immersion_range with revised bands."""

    def test_band1_core_grammar(self):
        assert get_a2_immersion_range(1) == (45, 65)
        assert get_a2_immersion_range(10) == (45, 65)
        assert get_a2_immersion_range(20) == (45, 65)

    def test_band2_applied_grammar(self):
        assert get_a2_immersion_range(21) == (55, 75)
        assert get_a2_immersion_range(35) == (55, 75)
        assert get_a2_immersion_range(50) == (55, 75)

    def test_band3_consolidation(self):
        assert get_a2_immersion_range(51) == (70, 90)
        assert get_a2_immersion_range(60) == (70, 90)
        assert get_a2_immersion_range(70) == (70, 90)
