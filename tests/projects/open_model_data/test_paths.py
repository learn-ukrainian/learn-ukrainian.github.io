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


def test_execute_mining_and_release_forwards_replay_arguments(
    tmp_path: Path, isolated_vesum_db: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify that execute_mining_and_release exposes and forwards replay arguments to builder."""
    from typing import Any

    import scripts.projects.open_model_data.v5_mine_dialect_corpus as mdc

    captured_kwargs: dict[str, Any] = {}

    def mock_build_sft(_candidates, **kwargs):
        captured_kwargs.update(kwargs)
        raise ValueError("StopPipelineAfterForwarding")

    monkeypatch.setattr(mdc, "mine_all_candidate_sentences", lambda _db: [])
    monkeypatch.setattr(mdc, "partition_candidates_by_lemma", lambda _c: ([], []))
    monkeypatch.setattr(mdc, "build_evaluation_benchmark", lambda *args, **kwargs: [])
    monkeypatch.setattr(mdc, "build_sft_dialect_dataset", mock_build_sft)

    out_dir = tmp_path / "out"
    dummy_db = tmp_path / "dummy.db"
    dummy_db.touch()
    shards_dir = tmp_path / "custom_shards"

    with pytest.raises(ValueError, match="StopPipelineAfterForwarding"):
        mdc.execute_mining_and_release(
            db_path=dummy_db,
            vesum_db=isolated_vesum_db,
            output_dir=out_dir,
            replay_quota=42,
            replay_shards_dir=shards_dir,
        )

    assert captured_kwargs["replay_quota"] == 42
    assert captured_kwargs["replay_shards_dir"] == shards_dir
    assert captured_kwargs["sft_dialect_quota"] == 500 - 42


def test_execute_mining_and_release_receipt_generation_derived_counts(
    tmp_path: Path, isolated_vesum_db: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify that execute_mining_and_release dynamically derives dialect vs replay counts in the receipt."""
    import hashlib
    import json

    import jsonschema

    import scripts.projects.open_model_data.v5_mine_dialect_corpus as mdc

    mock_eval = (
        [{"macro_zone": "southwestern", "sub_zone": "hutsul", "case_type": "PRESERVE"}] * 600
        + [{"macro_zone": "northern", "sub_zone": "polissian", "case_type": "PRESERVE"}] * 400
        + [{"macro_zone": "southeastern", "sub_zone": "slobozhan", "case_type": "PRESERVE"}] * 500
    )

    monkeypatch.setattr(mdc, "mine_all_candidate_sentences", lambda _db: [])
    monkeypatch.setattr(mdc, "partition_candidates_by_lemma", lambda _c: ([], []))
    monkeypatch.setattr(mdc, "build_evaluation_benchmark", lambda *args, **kwargs: mock_eval)
    # Bypass per-case schema validation for mocked minimal objects
    monkeypatch.setattr(mdc, "EVAL_SCHEMA_FILE", tmp_path / "no_eval_schema.json")
    monkeypatch.setattr(mdc, "TRAJECTORY_SCHEMA_FILE", tmp_path / "no_traj_schema.json")

    dummy_db = tmp_path / "dummy.db"
    dummy_db.touch()

    # Case 1: Default execution (replay_quota = 0 -> 500 dialect, 0 replay)
    out_dir_1 = tmp_path / "out1"
    mock_sft_1 = [
        {"trajectory_id": f"traj.dial.{i}", "is_calque_or_russianism": False}
        for i in range(500)
    ]
    monkeypatch.setattr(mdc, "build_sft_dialect_dataset", lambda *args, **kwargs: mock_sft_1)

    receipt_1 = mdc.execute_mining_and_release(
        db_path=dummy_db,
        vesum_db=isolated_vesum_db,
        output_dir=out_dir_1,
        replay_quota=0,
    )

    assert receipt_1["sft_training_dataset"]["total_trajectories"] == 500
    assert receipt_1["sft_training_dataset"]["dialect_trajectories"] == 500
    assert receipt_1["sft_training_dataset"]["replay_buffer_trajectories"] == 0

    # Ensure disk artifacts exist and sha256 matches
    receipt_file_1 = out_dir_1 / "release_receipt.json"
    assert receipt_file_1.exists()
    expected_sha_1 = hashlib.sha256(receipt_file_1.read_bytes()).hexdigest()
    assert (out_dir_1 / "release_receipt.json.sha256").read_text(encoding="utf-8").startswith(expected_sha_1)

    # Validate against actual repository receipt schema
    schema = json.loads(mdc.RECEIPT_SCHEMA_FILE.read_text(encoding="utf-8"))
    jsonschema.validate(receipt_1, schema)

    # Case 2: Mixed execution with replay (e.g. 450 dialect, 50 replay)
    out_dir_2 = tmp_path / "out2"
    mock_sft_2 = [
        {"trajectory_id": f"traj.dial.{i}", "is_calque_or_russianism": False}
        for i in range(450)
    ] + [
        {"trajectory_id": f"traj.replay.{i}", "is_calque_or_russianism": True}
        for i in range(50)
    ]
    monkeypatch.setattr(mdc, "build_sft_dialect_dataset", lambda *args, **kwargs: mock_sft_2)

    receipt_2 = mdc.execute_mining_and_release(
        db_path=dummy_db,
        vesum_db=isolated_vesum_db,
        output_dir=out_dir_2,
        replay_quota=50,
    )

    assert receipt_2["sft_training_dataset"]["total_trajectories"] == 500
    assert receipt_2["sft_training_dataset"]["dialect_trajectories"] == 450
    assert receipt_2["sft_training_dataset"]["replay_buffer_trajectories"] == 50
    jsonschema.validate(receipt_2, schema)
