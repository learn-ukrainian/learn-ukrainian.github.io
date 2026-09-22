"""Tests for canonical open_model_data paths module (#6321)."""

from __future__ import annotations

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
