"""Tests for scripts/pipeline/config_tables.py — golden fragment resolution."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure scripts/ is on the path so pipeline.config_tables can be imported.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from pipeline.config_tables import (
    ACTIVITY_CONFIGS,
    GOLDEN_FRAGMENTS,
    get_activity_config,
    get_golden_fragment,
)

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

    # b2-pro / c1-pro tests removed 2026-04-10 — tracks deleted.


# ---------------------------------------------------------------------------
# 3. get_activity_config() — module-number-aware anagram phase-out (#1300)
# ---------------------------------------------------------------------------

def _types(raw: str) -> set[str]:
    """Parse a comma-separated activity-type list into a set for membership tests."""
    return {t.strip() for t in (raw or "").split(",") if t.strip()}


class TestActivityConfigAnagramPhaseout:
    """A1 anagram is Cyrillic-scaffolding only — must be phased out after M10.

    Audit rule: ``scripts/audit/config.py::ACTIVITY_RESTRICTIONS['A1']``
    has ``anagram_limit: 10``. The writer prompt must reflect that rule
    by removing anagram from allowed/priority lists past M10 and adding
    it to FORBIDDEN. Before #1300 the A1 config was static and the
    writer kept emitting anagram for M11+ modules, causing 26
    LEVEL_RESTRICTION violations.
    """

    @pytest.mark.parametrize("module_num", [1, 5, 10])
    def test_a1_m1_m10_keeps_anagram_as_priority(self, module_num: int):
        """M01-M10 is the Cyrillic scaffolding phase — anagram stays a priority type."""
        cfg = get_activity_config("a1", module_num)
        assert "anagram" in _types(cfg["WORKBOOK_ALLOWED_TYPES"])
        assert "anagram" in _types(cfg["WORKBOOK_PRIORITY_TYPES"])
        assert "anagram" in _types(cfg["ALLOWED_ACTIVITY_TYPES"])
        assert "anagram" not in _types(cfg["FORBIDDEN_ACTIVITY_TYPES"])

    @pytest.mark.parametrize("module_num", [11, 13, 18, 35, 53])
    def test_a1_m11_plus_forbids_anagram(self, module_num: int):
        """Past M10 anagram is forbidden — removed from allowed/priority, added to forbidden."""
        cfg = get_activity_config("a1", module_num)
        assert "anagram" not in _types(cfg["WORKBOOK_ALLOWED_TYPES"])
        assert "anagram" not in _types(cfg["WORKBOOK_PRIORITY_TYPES"])
        assert "anagram" not in _types(cfg["ALLOWED_ACTIVITY_TYPES"])
        assert "anagram" not in _types(cfg["PRIORITY_TYPES"])
        assert "anagram" in _types(cfg["FORBIDDEN_ACTIVITY_TYPES"])

    def test_a1_checkpoint_past_m10_also_forbids_anagram(self):
        """A1 checkpoints at M14/M21/M27/... must also forbid anagram (M>10)."""
        cfg = get_activity_config("a1", 14, slug="checkpoint-my-world")
        assert "anagram" not in _types(cfg["WORKBOOK_ALLOWED_TYPES"])
        assert "anagram" not in _types(cfg["WORKBOOK_PRIORITY_TYPES"])
        assert "anagram" in _types(cfg["FORBIDDEN_ACTIVITY_TYPES"])

    def test_a2_still_forbids_anagram(self):
        """A2 already forbids anagram in its static config — behaviour must be preserved."""
        cfg = get_activity_config("a2", 5)
        assert "anagram" in _types(cfg["FORBIDDEN_ACTIVITY_TYPES"])
        assert "anagram" not in _types(cfg["ALLOWED_ACTIVITY_TYPES"])

    def test_returned_config_is_a_copy(self):
        """Mutating the returned dict must not leak into the global ACTIVITY_CONFIGS.

        Before #1300 the function returned the dict by reference; any caller
        that mutated it poisoned every subsequent call. Regression guard.
        """
        original_forbidden = ACTIVITY_CONFIGS["a1"]["FORBIDDEN_ACTIVITY_TYPES"]
        cfg = get_activity_config("a1", 15)
        cfg["FORBIDDEN_ACTIVITY_TYPES"] = "mutated-by-caller"
        assert ACTIVITY_CONFIGS["a1"]["FORBIDDEN_ACTIVITY_TYPES"] == original_forbidden

    def test_m10_vs_m11_boundary(self):
        """Explicit boundary check — M10 keeps anagram, M11 drops it."""
        m10 = get_activity_config("a1", 10)
        m11 = get_activity_config("a1", 11)
        assert "anagram" in _types(m10["WORKBOOK_PRIORITY_TYPES"])
        assert "anagram" not in _types(m11["WORKBOOK_PRIORITY_TYPES"])
        assert "anagram" in _types(m11["FORBIDDEN_ACTIVITY_TYPES"])

    def test_phase_out_is_idempotent(self):
        """Calling the resolver twice with the same M>10 args returns equivalent configs.

        Catches a class of bug where the phase-out helper mutated a shared
        reference and the second call saw a different shape than the first.
        """
        first = get_activity_config("a1", 20)
        second = get_activity_config("a1", 20)
        assert first == second
        assert first is not second  # but still a fresh copy


class TestActivityConfigUnrelatedTracks:
    """Non-A1 tracks are untouched by the anagram phase-out logic."""

    @pytest.mark.parametrize("track,module_num", [("b1", 5), ("b2", 10), ("c1", 3)])
    def test_higher_tracks_still_forbid_anagram(self, track: str, module_num: int):
        """B1/B2/C1 static configs already forbid anagram — module_num must not change that."""
        cfg = get_activity_config(track, module_num)
        assert "anagram" in _types(cfg["FORBIDDEN_ACTIVITY_TYPES"])

    def test_lit_track_returns_lit_config(self):
        """lit-* tracks route to the 'lit' config — anagram forbidden, not scaffolded."""
        cfg = get_activity_config("lit-essay", 1)
        assert "anagram" in _types(cfg["FORBIDDEN_ACTIVITY_TYPES"])


class TestActivityPedagogyMatrix:
    """Phase 2 guard: live config matches docs/best-practices/activity-pedagogy.md."""

    def _doc_matrix(self) -> tuple[list[str], dict[str, dict[str, str]]]:
        doc = Path("docs/best-practices/activity-pedagogy.md").read_text()
        lines = doc.splitlines()
        header_idx = next(i for i, line in enumerate(lines) if line.startswith("| Type | a1 |"))
        levels = [cell.strip() for cell in lines[header_idx].strip("|").split("|")][1:]
        matrix: dict[str, dict[str, str]] = {}
        for line in lines[header_idx + 2:]:
            if not line.startswith("|") or line.startswith("|---"):
                break
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            matrix[cells[0]] = dict(zip(levels, cells[1:], strict=True))
        return levels, matrix

    def test_activity_configs_match_documented_matrix(self):
        levels, matrix = self._doc_matrix()

        for level in levels:
            cfg = ACTIVITY_CONFIGS[level]
            inline = _types(cfg["INLINE_ALLOWED_TYPES"])
            workbook = _types(cfg["WORKBOOK_ALLOWED_TYPES"])
            for activity_type, row in matrix.items():
                expected = row[level]
                actual = (
                    "B" if activity_type in inline and activity_type in workbook
                    else "I" if activity_type in inline
                    else "W" if activity_type in workbook
                    else "-"
                )
                assert actual == expected, f"{level} {activity_type}: config={actual}, docs={expected}"

    def test_select_forbidden_in_every_activity_config(self):
        for level, cfg in ACTIVITY_CONFIGS.items():
            assert "select" in _types(cfg["FORBIDDEN_ACTIVITY_TYPES"]), level
