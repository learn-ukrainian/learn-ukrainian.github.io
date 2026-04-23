"""Per-consumer tests — every migrated consumer reads thresholds from
``scripts/common/thresholds`` and exposes values consistent with the
single source of truth.

These tests would catch a silent regression where a consumer still imports
the name but re-binds it to a different number, or where an alias drifts.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from common.thresholds import (
    LEVEL_THRESHOLDS,
    REVIEW_PASS_FLOOR,
    REVIEW_REJECT_FLOOR,
    STYLE_REVIEW_DIMENSION_FLOOR,
    STYLE_REVIEW_TARGET,
    LevelThresholds,
    get_level_thresholds,
    get_naturalness_min,
    get_target_words,
)

# ---------------------------------------------------------------------------
# thresholds.py — shape and invariants
# ---------------------------------------------------------------------------

class TestThresholdsModule:
    def test_canonical_values_present(self) -> None:
        assert REVIEW_PASS_FLOOR == 8.0
        assert REVIEW_REJECT_FLOOR == 6.0
        assert STYLE_REVIEW_TARGET == 9.0
        assert STYLE_REVIEW_DIMENSION_FLOOR == 8.5

    def test_level_thresholds_covers_all_families(self) -> None:
        expected = {"A1", "A2", "B1", "B2", "C1", "C2"}
        assert set(LEVEL_THRESHOLDS) == expected

    def test_level_thresholds_is_immutable_mapping(self) -> None:
        with pytest.raises(TypeError):
            LEVEL_THRESHOLDS["A1"] = LevelThresholds(target_words=1, naturalness_min=1.0)  # type: ignore[index]

    def test_level_thresholds_dataclass_is_frozen(self) -> None:
        with pytest.raises(AttributeError):
            LEVEL_THRESHOLDS["A1"].target_words = 9999  # type: ignore[misc]

    def test_get_level_thresholds_accepts_variants(self) -> None:
        assert get_level_thresholds("A1") == LEVEL_THRESHOLDS["A1"]
        assert get_level_thresholds("A1-checkpoint") == LEVEL_THRESHOLDS["A1"]
        assert get_level_thresholds("B2-grammar") == LEVEL_THRESHOLDS["B2"]
        assert get_level_thresholds("c2-literary") == LEVEL_THRESHOLDS["C2"]

    def test_get_level_thresholds_unknown_falls_back_to_default(self) -> None:
        unknown = get_level_thresholds("ZZ")
        assert unknown.naturalness_min == 8.0
        assert unknown.target_words == 4000

    def test_get_level_thresholds_none_returns_default(self) -> None:
        assert get_level_thresholds(None).naturalness_min == 8.0

    def test_shortcut_functions_match_full_resolver(self) -> None:
        for code in ("A1", "B2-grammar", "C2-literary", None, "ZZ"):
            resolved = get_level_thresholds(code)
            assert get_naturalness_min(code) == resolved.naturalness_min
            assert get_target_words(code) == resolved.target_words


# ---------------------------------------------------------------------------
# v6_build.py — legacy aliases carry canonical values
# ---------------------------------------------------------------------------

class TestV6BuildAliases:
    def test_review_target_score_alias(self) -> None:
        from build import v6_build
        assert v6_build.REVIEW_TARGET_SCORE == REVIEW_PASS_FLOOR

    def test_review_reject_score_alias(self) -> None:
        from build import v6_build
        assert v6_build.REVIEW_REJECT_SCORE == REVIEW_REJECT_FLOOR

    def test_style_review_target_score_alias(self) -> None:
        from build import v6_build
        assert v6_build.STYLE_REVIEW_TARGET_SCORE == STYLE_REVIEW_TARGET

    def test_style_review_dimension_floor_matches(self) -> None:
        from build import v6_build
        assert v6_build.STYLE_REVIEW_DIMENSION_FLOOR == STYLE_REVIEW_DIMENSION_FLOOR


# ---------------------------------------------------------------------------
# audit/config.py — AUDIT_THRESHOLDS + LEVEL_CONFIG derive from thresholds
# ---------------------------------------------------------------------------

class TestAuditConfig:
    def test_audit_thresholds_naturalness_matches_thresholds_table(self) -> None:
        from audit.config import AUDIT_THRESHOLDS
        mins = AUDIT_THRESHOLDS["naturalness_min_score"]
        for level, entry in LEVEL_THRESHOLDS.items():
            assert mins[level] == entry.naturalness_min
        assert mins["default"] == get_naturalness_min(None)

    def test_get_naturalness_min_score_family_prefix(self) -> None:
        from audit.config import get_naturalness_min_score
        assert get_naturalness_min_score("A1") == LEVEL_THRESHOLDS["A1"].naturalness_min
        assert get_naturalness_min_score("A1-checkpoint") == LEVEL_THRESHOLDS["A1"].naturalness_min
        assert get_naturalness_min_score("b2-grammar") == LEVEL_THRESHOLDS["B2"].naturalness_min

    def test_level_config_family_target_words(self) -> None:
        from audit.config import LEVEL_CONFIG
        for level, entry in LEVEL_THRESHOLDS.items():
            assert LEVEL_CONFIG[level]["target_words"] == entry.target_words

    def test_get_word_target_honors_variants_and_family_default(self) -> None:
        from audit.config import get_word_target
        # Family entry (no focus): reads LEVEL_THRESHOLDS.A1.
        assert get_word_target("A1") == LEVEL_THRESHOLDS["A1"].target_words
        # Variant: A1-checkpoint has a smaller override (1000) documented
        # inline in LEVEL_CONFIG — not pulled into the common table.
        assert get_word_target("A1", module_focus="checkpoint") == 1000


# ---------------------------------------------------------------------------
# Other migrated consumers
# ---------------------------------------------------------------------------

class TestOtherConsumers:
    def test_review_validation_constants(self) -> None:
        from audit.checks import review_validation
        assert review_validation._V6_REVIEW_MIN_SCORE == REVIEW_PASS_FLOOR
        assert review_validation._STYLE_REVIEW_DIMENSION_FLOOR == STYLE_REVIEW_DIMENSION_FLOOR

    def test_scoring_sampling_naturalness_threshold(self) -> None:
        from scoring import sampling
        assert sampling.NATURALNESS_THRESHOLD == REVIEW_PASS_FLOOR

    def test_batch_fix_review_pass_threshold(self) -> None:
        from batch import batch_fix_review
        assert batch_fix_review.PASS_THRESHOLD == STYLE_REVIEW_TARGET


# ---------------------------------------------------------------------------
# scripts/config.py — dead field stays dead
# ---------------------------------------------------------------------------

class TestConfigLegacyDeadFields:
    def test_track_config_has_no_word_floor(self) -> None:
        import config as scripts_config  # scripts/config.py via sys.path
        for track, entry in scripts_config.TRACK_CONFIG.items():
            assert "word_floor" not in entry, f"{track} still carries dead word_floor"
