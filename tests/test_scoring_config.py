"""Tests for scoring/config.py — track config lookup and validation."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestGetTrackConfig:
    def test_known_specialized_track(self):
        from scoring.config import get_track_config
        config = get_track_config("hist")
        assert isinstance(config, dict)
        assert "name" in config

    def test_known_standard_variant(self):
        from scoring.config import get_track_config
        config = get_track_config("a1")
        assert isinstance(config, dict)
        assert config["level_dir"] == "a1"

    def test_unknown_track_raises(self):
        from scoring.config import get_track_config
        with pytest.raises(ValueError, match="Unknown track"):
            get_track_config("nonexistent-track-xyz")

    def test_standard_variant_has_module_count(self):
        from scoring.config import get_track_config
        config = get_track_config("b1")
        assert "module_count" in config
        assert config["module_count"] > 0

    def test_all_standard_variants_resolvable(self):
        from scoring.config import get_track_config, STANDARD_TRACK_VARIANTS
        for track_id in STANDARD_TRACK_VARIANTS:
            config = get_track_config(track_id)
            assert config["level_dir"] == STANDARD_TRACK_VARIANTS[track_id]["level_dir"]


class TestGetAllTrackIds:
    def test_returns_list(self):
        from scoring.config import get_all_track_ids
        ids = get_all_track_ids()
        assert isinstance(ids, list)
        assert len(ids) > 5

    def test_contains_known_tracks(self):
        from scoring.config import get_all_track_ids
        ids = get_all_track_ids()
        assert "hist" in ids
        assert "bio" in ids
        assert "a1" in ids
        assert "b2" in ids

    def test_does_not_contain_generic_standard(self):
        from scoring.config import get_all_track_ids
        ids = get_all_track_ids()
        assert "standard" not in ids

    def test_all_ids_are_valid(self):
        from scoring.config import get_track_config, get_all_track_ids
        for track_id in get_all_track_ids():
            config = get_track_config(track_id)
            assert isinstance(config, dict)


class TestTrackConfigs:
    """Validate TRACK_CONFIGS structure."""

    def test_all_specialized_configs_have_required_keys(self):
        from scoring.config import TRACK_CONFIGS
        required = {"name", "criteria"}
        for track_id, config in TRACK_CONFIGS.items():
            missing = required - set(config.keys())
            assert not missing, f"{track_id} missing keys: {missing}"

    def test_criteria_have_weight(self):
        from scoring.config import TRACK_CONFIGS
        for track_id, config in TRACK_CONFIGS.items():
            for criterion_name, criterion in config.get("criteria", {}).items():
                assert "weight" in criterion, (
                    f"{track_id}.{criterion_name} missing 'weight'"
                )

    def test_weights_sum_to_approximately_1(self):
        from scoring.config import TRACK_CONFIGS
        for track_id, config in TRACK_CONFIGS.items():
            criteria = config.get("criteria", {})
            if not criteria:
                continue
            total = sum(c.get("weight", 0) for c in criteria.values())
            # Weights are 0-1 scale (sum ≈ 1.0) or 0-100 scale (sum ≈ 100)
            assert (0.9 <= total <= 1.1) or (90 <= total <= 110), (
                f"{track_id} weights sum to {total}, expected ~1.0 or ~100"
            )
