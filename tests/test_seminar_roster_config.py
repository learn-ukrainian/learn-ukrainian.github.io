"""Tests for deriving API seminar roster from curriculum.yaml (#5245)."""

from pathlib import Path
import pytest
import yaml

from scripts.api import config, state_helpers, dashboard_helpers
from scripts.orchestration import curriculum_readiness


def test_seminar_track_ids_derived_from_curriculum_manifest() -> None:
    """Verify SEMINAR_TRACK_IDS matches active tracks of type 'track' in curriculum.yaml."""
    manifest = curriculum_readiness.load_active_manifest(config.LIVE_REPO_ROOT)
    expected_seminar = {
        track_id
        for track_id, info in manifest["tracks"].items()
        if info.get("type") == "track"
    }

    assert config.SEMINAR_TRACK_IDS == expected_seminar
    assert "lit-doc" not in config.SEMINAR_TRACK_IDS
    assert "lit-crimea" not in config.SEMINAR_TRACK_IDS
    assert "hist" in config.SEMINAR_TRACK_IDS
    assert "bio" in config.SEMINAR_TRACK_IDS
    assert "folk" in config.SEMINAR_TRACK_IDS


def test_levels_derived_from_curriculum_manifest() -> None:
    """Verify LEVELS matches active tracks in order in curriculum.yaml."""
    manifest = curriculum_readiness.load_active_manifest(config.LIVE_REPO_ROOT)
    expected_ids = list(manifest["tracks"].keys())
    actual_ids = [lvl["id"] for lvl in config.LEVELS]

    assert actual_ids == expected_ids
    assert "a1" in actual_ids
    assert "c2" in actual_ids
    assert "hist" in actual_ids


def test_roster_loads_from_custom_manifest_root(tmp_path: Path) -> None:
    """Verify load_seminar_track_ids and load_levels adapt to custom manifest files."""
    curriculum_dir = tmp_path / "curriculum" / "l2-uk-en"
    curriculum_dir.mkdir(parents=True)
    manifest_data = {
        "version": "1.0",
        "description": "Test manifest",
        "levels": {
            "a1": {"type": "core", "modules": ["m1"]},
            "custom_seminar": {"type": "track", "modules": ["s1"]},
        },
    }
    (curriculum_dir / "curriculum.yaml").write_text(yaml.safe_dump(manifest_data), encoding="utf-8")

    derived_seminar = config.load_seminar_track_ids(tmp_path)
    assert derived_seminar == {"custom_seminar"}

    derived_levels = config.load_levels(tmp_path)
    assert len(derived_levels) == 2
    assert derived_levels[0]["id"] == "a1"
    assert derived_levels[1]["id"] == "custom_seminar"


def test_profile_map_reflects_derived_seminar_tracks() -> None:
    """Verify state_helpers.PROFILE_MAP identifies all seminar tracks correctly."""
    for track_id in config.SEMINAR_TRACK_IDS:
        assert state_helpers.PROFILE_MAP.get(track_id) == "seminar"

    assert state_helpers.PROFILE_MAP.get("a1") == "core"
    assert state_helpers.PROFILE_MAP.get("c1") == "core"
