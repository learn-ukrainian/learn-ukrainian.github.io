"""Tests for the alignment manifest contract."""

from __future__ import annotations

import copy
import sqlite3
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build import alignment_manifest
from build.phases import wiki_compressor

from audit import config as audit_config


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        "utf-8",
    )


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, "utf-8")


def _build_sources_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE source_chunks (id INTEGER PRIMARY KEY, body TEXT NOT NULL)"
        )
        connection.execute(
            "CREATE INDEX idx_source_chunks_body ON source_chunks(body)"
        )
        connection.execute(
            "INSERT INTO source_chunks(body) VALUES (?)",
            ("first row",),
        )
        connection.commit()


@pytest.fixture
def manifest_fixture(tmp_path: Path, monkeypatch) -> dict[str, Path]:
    repo_root = tmp_path
    curriculum_root = repo_root / "curriculum" / "l2-uk-en"
    plan_path = curriculum_root / "plans" / "a1" / "demo.yaml"
    sources_db_path = repo_root / "data" / "sources.db"
    canonical_anchors_path = repo_root / "data" / "canonical_anchors.yaml"
    decisions_path = repo_root / "docs" / "decisions" / "decisions.yaml"
    phase_template_path = repo_root / "scripts" / "build" / "phases" / "v6-write.md"

    _write_yaml(
        plan_path,
        {
            "slug": "demo",
            "level": "A1",
            "title": "Alignment demo",
            "word_target": 1200,
            "objectives": ["Test the manifest contract."],
        },
    )
    _build_sources_db(sources_db_path)
    _write_text(canonical_anchors_path, "anchors:\n  - id: flag\n")
    _write_yaml(
        decisions_path,
        {
            "decisions": [
                {"id": "dec-001", "status": "active", "scope": "pipeline"},
                {"id": "dec-002", "status": "active", "scope": "architecture"},
                {"id": "dec-003", "status": "active", "scope": "content"},
            ]
        },
    )
    _write_text(phase_template_path, "# Writer prompt\n\nOriginal template.\n")
    _write_text(
        repo_root / ".claude" / "phases" / "claude" / "writer.md",
        "Claude prompt.\n",
    )
    _write_text(
        repo_root / ".gemini" / "phases" / "gemini" / "review.md",
        "Gemini prompt.\n",
    )

    monkeypatch.setattr(alignment_manifest, "PROJECT_ROOT", repo_root)
    monkeypatch.setattr(alignment_manifest, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(alignment_manifest, "SOURCES_DB_PATH", sources_db_path)
    monkeypatch.setattr(alignment_manifest, "CANONICAL_ANCHORS_PATH", canonical_anchors_path)
    monkeypatch.setattr(alignment_manifest, "DECISIONS_PATH", decisions_path)
    monkeypatch.setattr(
        alignment_manifest,
        "PHASE_TEMPLATES_ROOT",
        repo_root / "scripts" / "build" / "phases",
    )
    monkeypatch.setattr(
        alignment_manifest,
        "CLAUDE_PHASES_ROOT",
        repo_root / ".claude" / "phases" / "claude",
    )
    monkeypatch.setattr(
        alignment_manifest,
        "GEMINI_PHASES_ROOT",
        repo_root / ".gemini" / "phases" / "gemini",
    )
    monkeypatch.setattr(alignment_manifest, "REVIEW_TARGET_SCORE", 8.0)
    monkeypatch.setattr(audit_config, "LEVEL_CONFIG", copy.deepcopy(audit_config.LEVEL_CONFIG))

    return {
        "plan_path": plan_path,
        "sources_db_path": sources_db_path,
        "canonical_anchors_path": canonical_anchors_path,
        "decisions_path": decisions_path,
        "phase_template_path": phase_template_path,
    }


def _compose() -> dict:
    return alignment_manifest.compose_manifest(level="a1", slug="demo")


def test_manifest_is_deterministic(manifest_fixture: dict[str, Path]) -> None:
    first = _compose()
    second = _compose()

    assert alignment_manifest.manifest_hash(first) == alignment_manifest.manifest_hash(second)


def test_plan_change_invalidates_manifest(manifest_fixture: dict[str, Path]) -> None:
    first = _compose()

    _write_yaml(
        manifest_fixture["plan_path"],
        {
            "slug": "demo",
            "level": "A1",
            "title": "Alignment demo updated",
            "word_target": 1200,
            "objectives": ["Test the manifest contract."],
        },
    )

    second = _compose()

    assert alignment_manifest.manifest_hash(second) != alignment_manifest.manifest_hash(first)


def test_sources_db_change_invalidates_manifest(manifest_fixture: dict[str, Path]) -> None:
    first = _compose()

    with sqlite3.connect(manifest_fixture["sources_db_path"]) as connection:
        connection.execute(
            "INSERT INTO source_chunks(body) VALUES (?)",
            ("second row",),
        )
        connection.commit()

    second = _compose()

    assert alignment_manifest.manifest_hash(second) != alignment_manifest.manifest_hash(first)


def test_template_change_invalidates_manifest(manifest_fixture: dict[str, Path]) -> None:
    first = _compose()

    _write_text(
        manifest_fixture["phase_template_path"],
        "# Writer prompt\n\nUpdated template.\n",
    )

    second = _compose()

    assert alignment_manifest.manifest_hash(second) != alignment_manifest.manifest_hash(first)


def test_canonical_anchor_change_invalidates_manifest(manifest_fixture: dict[str, Path]) -> None:
    first = _compose()

    _write_text(
        manifest_fixture["canonical_anchors_path"],
        "anchors:\n  - id: flag\n  - id: anthem\n",
    )

    second = _compose()

    assert alignment_manifest.manifest_hash(second) != alignment_manifest.manifest_hash(first)


def test_tokenizer_version_bump_invalidates_manifest(
    manifest_fixture: dict[str, Path],
    monkeypatch,
) -> None:
    first = _compose()

    monkeypatch.setattr(wiki_compressor, "TOKENIZER_VERSION", "2026-04-24")

    second = _compose()

    assert alignment_manifest.manifest_hash(second) != alignment_manifest.manifest_hash(first)


def test_threshold_change_invalidates_manifest(
    manifest_fixture: dict[str, Path],
    monkeypatch,
) -> None:
    first = _compose()

    monkeypatch.setattr(alignment_manifest, "REVIEW_TARGET_SCORE", 8.5)

    second = _compose()

    assert alignment_manifest.manifest_hash(second) != alignment_manifest.manifest_hash(first)


def test_decision_status_change_invalidates_manifest(manifest_fixture: dict[str, Path]) -> None:
    first = _compose()

    _write_yaml(
        manifest_fixture["decisions_path"],
        {
            "decisions": [
                {"id": "dec-001", "status": "superseded", "scope": "pipeline"},
                {"id": "dec-002", "status": "active", "scope": "architecture"},
                {"id": "dec-003", "status": "active", "scope": "content"},
            ]
        },
    )

    second = _compose()

    assert alignment_manifest.manifest_hash(second) != alignment_manifest.manifest_hash(first)


def test_stamp_roundtrip(manifest_fixture: dict[str, Path]) -> None:
    manifest = _compose()
    artifact = {"slug": "demo", "status": "complete"}

    stamped = alignment_manifest.stamp_artifact(artifact, manifest)

    assert alignment_manifest.validate_stamped_artifact(stamped, manifest) == (True, ())
    assert artifact == {"slug": "demo", "status": "complete"}


def test_validate_reports_specific_mismatch(manifest_fixture: dict[str, Path]) -> None:
    manifest = _compose()
    stamped = alignment_manifest.stamp_artifact({"slug": "demo"}, manifest)

    _write_yaml(
        manifest_fixture["plan_path"],
        {
            "slug": "demo",
            "level": "A1",
            "title": "Changed after stamp",
            "word_target": 1200,
            "objectives": ["Test the manifest contract."],
        },
    )
    current_manifest = _compose()

    assert alignment_manifest.validate_stamped_artifact(stamped, current_manifest) == (
        False,
        ("plan_hash",),
    )
