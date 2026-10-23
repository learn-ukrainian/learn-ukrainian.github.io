"""Tests for deriving API seminar roster from curriculum.yaml (#5245)."""

from pathlib import Path

import pytest
import yaml

from scripts.api import config

pytestmark = pytest.mark.reads_content


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
