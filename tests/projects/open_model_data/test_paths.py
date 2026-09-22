"""Tests for canonical open_model_data paths module (#6321)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.projects.open_model_data.paths import (
    ARCHIVE_DIR,
    ARCHIVED_ULDR_V1_DIR,
    COMPONENTS_DIR,
    CONTRACTS_DIR,
    CORRECTION_PROTECTION_DIR,
    DECOLONIZATION_DIR,
    DIALECTS_DIR,
    GRAMMAR_DIR,
    IDIOMS_DIR,
    OPEN_MODEL_DATA_DIR,
    QUARANTINED_HISTORICAL_DIR,
    RELEASE_DIR,
    REPO_ROOT,
    TEXTBOOKS_DIR,
    ensure_component_directories,
)


def test_paths_relative_hierarchy() -> None:
    """Verify that all paths have the expected parent-child relationships."""
    assert OPEN_MODEL_DATA_DIR == REPO_ROOT / "data" / "projects" / "open_model_data"
    assert COMPONENTS_DIR == OPEN_MODEL_DATA_DIR / "components"
    assert DECOLONIZATION_DIR == COMPONENTS_DIR / "decolonization"
    assert IDIOMS_DIR == COMPONENTS_DIR / "idioms"
    assert GRAMMAR_DIR == COMPONENTS_DIR / "grammar"
    assert TEXTBOOKS_DIR == COMPONENTS_DIR / "textbooks"
    assert DIALECTS_DIR == COMPONENTS_DIR / "dialects"

    assert RELEASE_DIR == OPEN_MODEL_DATA_DIR / "release"
    assert CORRECTION_PROTECTION_DIR == RELEASE_DIR / "correction_protection_v1"

    assert ARCHIVE_DIR == OPEN_MODEL_DATA_DIR / "archive"
    assert ARCHIVED_ULDR_V1_DIR == ARCHIVE_DIR / "uldr_v1_production"
    assert QUARANTINED_HISTORICAL_DIR == ARCHIVE_DIR / "quarantined_historical"

    assert CONTRACTS_DIR == OPEN_MODEL_DATA_DIR / "contracts"


def test_tombstone_exists_in_archived_uldr_v1() -> None:
    """Verify that uldr_v1_production carries its tombstone."""
    tombstone = ARCHIVED_ULDR_V1_DIR / "TOMBSTONE.md"
    assert tombstone.is_file()
    content = tombstone.read_text(encoding="utf-8")
    assert "TOMBSTONE" in content
    assert "DO NOT USE" in content


def test_active_correction_protection_intact() -> None:
    """Verify that correction_protection_v1 is intact in release/."""
    assert CORRECTION_PROTECTION_DIR.is_dir()
    assert (CORRECTION_PROTECTION_DIR / "cases.jsonl").is_file()
    assert (CORRECTION_PROTECTION_DIR / "receipt.json").is_file()


def test_ensure_component_directories(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that ensure_component_directories creates all components."""
    import scripts.projects.open_model_data.paths as paths_mod

    test_components = tmp_path / "components"
    monkeypatch.setattr(paths_mod, "COMPONENTS_DIR", test_components)
    monkeypatch.setattr(paths_mod, "DECOLONIZATION_DIR", test_components / "decolonization")
    monkeypatch.setattr(paths_mod, "IDIOMS_DIR", test_components / "idioms")
    monkeypatch.setattr(paths_mod, "GRAMMAR_DIR", test_components / "grammar")
    monkeypatch.setattr(paths_mod, "TEXTBOOKS_DIR", test_components / "textbooks")
    monkeypatch.setattr(paths_mod, "DIALECTS_DIR", test_components / "dialects")

    ensure_component_directories()

    assert (test_components / "decolonization").is_dir()
    assert (test_components / "idioms").is_dir()
    assert (test_components / "grammar").is_dir()
    assert (test_components / "textbooks").is_dir()
    assert (test_components / "dialects").is_dir()


def test_is_archived_or_quarantined_path() -> None:
    """Verify archive detection logic."""
    from scripts.projects.open_model_data.paths import (
        assert_not_archived_path,
        is_archived_or_quarantined_path,
    )

    assert is_archived_or_quarantined_path(ARCHIVE_DIR) is True
    assert is_archived_or_quarantined_path(ARCHIVED_ULDR_V1_DIR) is True
    assert is_archived_or_quarantined_path(ARCHIVED_ULDR_V1_DIR / "sft") is True
    assert is_archived_or_quarantined_path(ARCHIVED_ULDR_V1_DIR / "sft" / "shard_1.jsonl") is True
    assert is_archived_or_quarantined_path(QUARANTINED_HISTORICAL_DIR) is True

    assert is_archived_or_quarantined_path(RELEASE_DIR) is False
    assert is_archived_or_quarantined_path(CORRECTION_PROTECTION_DIR) is False
    assert is_archived_or_quarantined_path(COMPONENTS_DIR) is False
    assert is_archived_or_quarantined_path(None) is False

    with pytest.raises(ValueError, match="Prohibited"):
        assert_not_archived_path(ARCHIVED_ULDR_V1_DIR / "sft", context="test")

    # Should not raise
    assert_not_archived_path(CORRECTION_PROTECTION_DIR, context="test")
    assert_not_archived_path(None, context="test")


@pytest.fixture
def isolated_vesum_db(tmp_path: Path) -> Path:
    """Provide an isolated, fixture-backed SQLite database to avoid depending on data/vesum.db."""
    db_path = tmp_path / "isolated_vesum.db"
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE forms_all (lemma TEXT, pos TEXT)")
    con.commit()
    con.close()
    return db_path


def test_dialect_builder_refuses_archive_replay(isolated_vesum_db: Path) -> None:
    """Verify that build_sft_dialect_dataset strictly refuses replay paths in archive/."""
    from scripts.projects.open_model_data.v5_mine_dialect_corpus import build_sft_dialect_dataset

    with pytest.raises(ValueError, match="Prohibited dialect replay shards on archived/quarantined path"):
        build_sft_dialect_dataset(
            sft_candidates=[],
            vesum_db=isolated_vesum_db,
            sft_dialect_quota=0,
            replay_quota=10,
            replay_shards_dir=ARCHIVED_ULDR_V1_DIR / "sft",
        )


def test_dialect_builder_fails_closed_when_replay_missing(isolated_vesum_db: Path) -> None:
    """Verify that build_sft_dialect_dataset fails closed instead of synthesizing fake replay rows."""
    from scripts.projects.open_model_data.v5_mine_dialect_corpus import build_sft_dialect_dataset

    with pytest.raises(ValueError, match="Insufficient verified anti-calque replay trajectories"):
        build_sft_dialect_dataset(
            sft_candidates=[],
            vesum_db=isolated_vesum_db,
            sft_dialect_quota=0,
            replay_quota=5,
            replay_shards_dir=None,
        )


def test_dialect_builder_loads_verified_non_archived_replay(tmp_path: Path, isolated_vesum_db: Path) -> None:
    """Verify that build_sft_dialect_dataset loads verified non-archived replay shards."""
    from scripts.projects.open_model_data.v5_mine_dialect_corpus import build_sft_dialect_dataset

    shards_dir = tmp_path / "verified_shards"
    shards_dir.mkdir(parents=True, exist_ok=True)
    sample_record = {
        "schema_version": "v1_decolonization_trajectory",
        "format_type": "deep_analysis",
        "trajectory_id": "traj.verified.001",
        "is_calque_or_russianism": True,
        "query": "test query",
    }
    (shards_dir / "sft_shard_001.jsonl").write_text(json.dumps(sample_record) + "\n", encoding="utf-8")

    trajs = build_sft_dialect_dataset(
        sft_candidates=[],
        vesum_db=isolated_vesum_db,
        sft_dialect_quota=0,
        replay_quota=1,
        replay_shards_dir=shards_dir,
    )
    assert len(trajs) == 1
    assert trajs[0]["trajectory_id"] == "traj.verified.001"
