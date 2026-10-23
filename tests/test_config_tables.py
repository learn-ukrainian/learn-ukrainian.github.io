"""Tests for scripts/pipeline/config_tables.py — golden fragment resolution."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure scripts/ is on the path so pipeline.config_tables can be imported.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from pipeline.config_tables import (
    ACTIVITY_CONFIGS,
    get_activity_config,
)

# ---------------------------------------------------------------------------
# 1. GOLDEN_FRAGMENTS dict integrity
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 2. get_golden_fragment() — band resolution by track + module_num
# ---------------------------------------------------------------------------

    # Professional-track golden fragment tests removed 2026-04-10 — tracks deleted.


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

    @pytest.mark.parametrize("module_num", [11, 13, 18, 35, 53])
    def test_a1_m11_plus_forbids_anagram(self, module_num: int):
        """Past M10 anagram is forbidden — removed from allowed/priority, added to forbidden."""
        cfg = get_activity_config("a1", module_num)
        assert "anagram" not in _types(cfg["WORKBOOK_ALLOWED_TYPES"])
        assert "anagram" not in _types(cfg["WORKBOOK_PRIORITY_TYPES"])
        assert "anagram" not in _types(cfg["ALLOWED_ACTIVITY_TYPES"])
        assert "anagram" not in _types(cfg["PRIORITY_TYPES"])
        assert "anagram" in _types(cfg["FORBIDDEN_ACTIVITY_TYPES"])

    def test_returned_config_is_a_copy(self):
        """Mutating the returned dict must not leak into the global ACTIVITY_CONFIGS.

        Before #1300 the function returned the dict by reference; any caller
        that mutated it poisoned every subsequent call. Regression guard.
        """
        original_forbidden = ACTIVITY_CONFIGS["a1"]["FORBIDDEN_ACTIVITY_TYPES"]
        cfg = get_activity_config("a1", 15)
        cfg["FORBIDDEN_ACTIVITY_TYPES"] = "mutated-by-caller"
        assert ACTIVITY_CONFIGS["a1"]["FORBIDDEN_ACTIVITY_TYPES"] == original_forbidden
