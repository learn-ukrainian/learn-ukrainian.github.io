"""Tests for scripts/pipeline/config_tables.py — golden fragment resolution."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure scripts/ is on the path so pipeline.config_tables can be imported.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from pipeline.config_tables import GOLDEN_FRAGMENTS, get_golden_fragment

# ---------------------------------------------------------------------------
# 1. GOLDEN_FRAGMENTS dict integrity
# ---------------------------------------------------------------------------

EXPECTED_BANDS = {"early-beginner", "late-beginner", "intermediate", "advanced", "seminar"}


def test_all_bands_present():
    """Every expected band key exists in GOLDEN_FRAGMENTS."""
    assert set(GOLDEN_FRAGMENTS.keys()) == EXPECTED_BANDS


@pytest.mark.parametrize("band", sorted(EXPECTED_BANDS))
def test_fragments_are_nonempty_strings(band: str):
    """Each fragment is a non-empty string with real content."""
    frag = GOLDEN_FRAGMENTS[band]
    assert isinstance(frag, str)
    assert len(frag) > 50, f"Fragment '{band}' too short ({len(frag)} chars)"


def test_seminar_fragment_contains_ukrainian():
    """Seminar fragment should contain substantial Ukrainian text."""
    frag = GOLDEN_FRAGMENTS["seminar"]
    # Must contain Cyrillic characters (Ukrainian)
    cyrillic = sum(1 for c in frag if "\u0400" <= c <= "\u04ff")
    assert cyrillic > 100, f"Seminar fragment has only {cyrillic} Cyrillic chars"


# ---------------------------------------------------------------------------
# 2. get_golden_fragment() — band resolution by track + module_num
# ---------------------------------------------------------------------------

class TestCoreTrackBands:
    """Core tracks (A1-C2) return the correct band fragment."""

    @pytest.mark.parametrize("module_num", [1, 6, 10, 14])
    def test_a1_early_beginner(self, module_num: int):
        result = get_golden_fragment("a1", module_num)
        assert result == GOLDEN_FRAGMENTS["early-beginner"]

    @pytest.mark.parametrize("module_num", [15, 24, 40, 64])
    def test_a1_late_beginner(self, module_num: int):
        result = get_golden_fragment("a1", module_num)
        assert result == GOLDEN_FRAGMENTS["late-beginner"]

    @pytest.mark.parametrize("module_num", [1, 20, 50, 76])
    def test_a2_late_beginner(self, module_num: int):
        result = get_golden_fragment("a2", module_num)
        assert result == GOLDEN_FRAGMENTS["late-beginner"]

    @pytest.mark.parametrize("module_num", [1, 50, 103])
    def test_b1_intermediate(self, module_num: int):
        result = get_golden_fragment("b1", module_num)
        assert result == GOLDEN_FRAGMENTS["intermediate"]

    @pytest.mark.parametrize("track", ["b2", "c1", "c2"])
    def test_advanced_tracks(self, track: str):
        result = get_golden_fragment(track, 1)
        assert result == GOLDEN_FRAGMENTS["advanced"]


class TestSeminarTracks:
    """Seminar tracks return the seminar golden fragment."""

    @pytest.mark.parametrize("track", ["hist", "bio", "istorio", "lit", "oes", "ruth"])
    def test_seminar_tracks_return_seminar_fragment(self, track: str):
        result = get_golden_fragment(track, 1)
        assert result == GOLDEN_FRAGMENTS["seminar"]

    def test_lit_subtrack(self):
        """lit-essay, lit-humor etc. should also get seminar fragment."""
        result = get_golden_fragment("lit-essay", 1)
        assert result == GOLDEN_FRAGMENTS["seminar"]


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_a1_boundary_14_15(self):
        """Module 14 = early-beginner, module 15 = late-beginner."""
        assert get_golden_fragment("a1", 14) == GOLDEN_FRAGMENTS["early-beginner"]
        assert get_golden_fragment("a1", 15) == GOLDEN_FRAGMENTS["late-beginner"]

    def test_unknown_track_returns_advanced(self):
        """Unknown track falls through to advanced band."""
        result = get_golden_fragment("d1", 1)
        assert result == GOLDEN_FRAGMENTS["advanced"]

    def test_b2_pro_returns_advanced(self):
        """Professional tracks return advanced fragment."""
        result = get_golden_fragment("b2-pro", 1)
        assert result == GOLDEN_FRAGMENTS["advanced"]

    def test_c1_pro_returns_advanced(self):
        result = get_golden_fragment("c1-pro", 1)
        assert result == GOLDEN_FRAGMENTS["advanced"]
