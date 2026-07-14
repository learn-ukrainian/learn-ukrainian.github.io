"""Hermetic contract tests for the marker-preserving VESUM reingest path.

The block sample is intentionally synthetic; it does not vendor VESUM content.
"""

from __future__ import annotations

import bz2
import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from scripts.rag.config import VESUM_URL
from scripts.rag.vesum_reingest import (
    BuildSummary,
    VesumReingestError,
    build_shadow_database,
    generate_fixture_manifest,
    iter_analyses,
    load_lock,
    marker_rows,
    validate_expected_summary,
    verify_pipeline_identity,
)

SYNTHETIC_BLOCKS = """\
clean noun:inanim:m:v_naz    # header provenance
  clean-form noun:inanim:m:v_rod    # form provenance
alternate adj:alt
archaic noun:arch
invalid noun:bad
  invalid-form noun:bad
nonstandard noun:subst
obscene noun:obsc
slangy noun:slang
vulgar noun:vulg
dialect-homograph noun:inanim:m:v_naz    # діалект
  dialect-homograph-form noun:inanim:m:v_rod    # form provenance
dialect-homograph noun:anim:m:v_naz
  dialect-homograph-form noun:anim:m:v_rod
"""


def _write_synthetic_asset(tmp_path: Path) -> Path:
    asset_path = tmp_path / "synthetic.txt.bz2"
    with bz2.open(asset_path, "wt", encoding="utf-8") as target:
        target.write(SYNTHETIC_BLOCKS)
    return asset_path


def _lock_for_asset(asset_path: Path) -> dict[str, object]:
    return {
        "release_asset": {
            "version": "synthetic-v1",
            "url": "https://github.com/brown-uk/dict_uk/releases/download/synthetic-v1/synthetic.txt.bz2",
            "sha256": hashlib.sha256(asset_path.read_bytes()).hexdigest(),
            "size_bytes": asset_path.stat().st_size,
        },
        "known_absent_marker_classes": [
            {
                "marker": "coll",
                "marker_class": "colloquial",
                "status": "known_absent",
            }
        ],
    }


def test_parser_keeps_block_identity_comments_and_line_spans() -> None:
    analyses = list(iter_analyses(SYNTHETIC_BLOCKS.splitlines(keepends=True)))

    assert [analysis.entry_id for analysis in analyses] == [
        1,
        1,
        2,
        3,
        4,
        4,
        5,
        6,
        7,
        8,
        9,
        9,
        10,
        10,
    ]
    assert analyses[0].source_location == "1-2"
    assert analyses[1].source_comment == "header provenance\nform provenance"
    assert analyses[10].source_comment == "діалект"
    assert analyses[11].source_comment == "діалект\nform provenance"
    assert analyses[12].source_comment is None
    assert analyses[10].lemma == analyses[12].lemma == "dialect-homograph"
    assert analyses[10].entry_id != analyses[12].entry_id


def test_marker_normalization_is_per_analysis_and_conservative() -> None:
    assert marker_rows("noun:bad:subst", None) == (
        ("bad", "tag", "invalid"),
        ("subst", "tag", "nonstandard"),
    )
    assert marker_rows("noun:slang", "діалект") == (
        ("dialect", "comment", "dialect"),
        ("slang", "tag", "slang"),
    )
    assert marker_rows("noun", "діалект\nform provenance") == (("dialect", "comment", "dialect"),)
    assert marker_rows("noun:arch", "діалектний") == (("arch", "tag", "archaic"),)


def test_shadow_schema_preserves_all_rows_and_hides_only_three_compatibility_markers(tmp_path: Path) -> None:
    database_path = tmp_path / "shadow.db"
    summary = build_shadow_database(_write_synthetic_asset(tmp_path), database_path)

    assert summary.analysis_count == 14
    assert summary.block_count == 10
    assert summary.forms_compatibility_count == 10
    assert summary.marker_counts == {
        "alt": 1,
        "arch": 1,
        "bad": 2,
        "dialect": 2,
        "obsc": 1,
        "slang": 1,
        "subst": 1,
        "vulg": 1,
    }

    connection = sqlite3.connect(database_path)
    try:
        all_words = {
            row[0]
            for row in connection.execute("SELECT word_form FROM forms_all")
        }
        visible_words = {row[0] for row in connection.execute("SELECT word_form FROM forms")}
        assert {"invalid", "invalid-form", "nonstandard", "obscene"} <= all_words
        assert not {"invalid", "invalid-form", "nonstandard", "obscene"} & visible_words
        assert {
            "alternate",
            "archaic",
            "slangy",
            "vulgar",
            "dialect-homograph",
            "dialect-homograph-form",
        } <= visible_words
        assert connection.execute("SELECT COUNT(*) FROM forms_all").fetchone()[0] == 14
        assert connection.execute("SELECT COUNT(*) FROM forms").fetchone()[0] == 10
        assert connection.execute(
            "SELECT marker FROM form_markers WHERE form_id = 11"
        ).fetchall() == [("dialect",)]
        assert connection.execute(
            "SELECT COUNT(*) FROM form_markers WHERE form_id = 13"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT source_location, source_comment FROM forms_all WHERE id = 11"
        ).fetchone() == ("11-12", "діалект")
    finally:
        connection.close()


def test_canonical_jsonl_hash_is_independent_of_shadow_path(tmp_path: Path) -> None:
    asset_path = _write_synthetic_asset(tmp_path)
    first = build_shadow_database(asset_path, tmp_path / "first.db")
    second = build_shadow_database(asset_path, tmp_path / "second.db")

    assert first.canonical_jsonl_sha256 == second.canonical_jsonl_sha256
    assert len(first.canonical_jsonl_sha256) == 64


def test_fixture_manifest_is_generated_from_database_with_attribution(tmp_path: Path) -> None:
    asset_path = _write_synthetic_asset(tmp_path)
    database_path = tmp_path / "shadow.db"
    build_shadow_database(asset_path, database_path)
    manifest_path = tmp_path / "fixture-manifest.json"

    manifest_sha256 = generate_fixture_manifest(
        database_path,
        _lock_for_asset(asset_path),
        manifest_path,
    )

    content = manifest_path.read_text(encoding="utf-8")
    manifest = json.loads(content)
    assert manifest_sha256 == hashlib.sha256(content.encode("utf-8")).hexdigest()
    assert manifest["source"]["license"] == "CC BY-NC-SA 4.0"
    assert manifest["selection"].startswith("lowest binary SQLite")
    assert [fixture["class"] for fixture in manifest["fixtures"]] == [
        "clean",
        "alt",
        "arch",
        "bad",
        "obsc",
        "slang",
        "subst",
        "vulg",
        "dialect",
    ]
    assert next(fixture for fixture in manifest["fixtures"] if fixture["class"] == "bad")[
        "compatibility_visible"
    ] is False
    assert next(fixture for fixture in manifest["fixtures"] if fixture["class"] == "slang")[
        "compatibility_visible"
    ] is True
    assert manifest["known_absent_classes"][0]["marker"] == "coll"


def test_expected_summary_is_fail_closed_on_any_semantic_difference() -> None:
    summary = BuildSummary(
        analysis_count=2,
        block_count=1,
        forms_compatibility_count=1,
        marker_counts={"bad": 1},
        canonical_jsonl_sha256="a" * 64,
        fixture_manifest_sha256="b" * 64,
    )
    lock = {"expected": summary.as_lock_expected()}

    validate_expected_summary(lock, summary)
    with pytest.raises(VesumReingestError, match="canonical_jsonl_sha256"):
        validate_expected_summary(
            lock,
            BuildSummary(
                analysis_count=2,
                block_count=1,
                forms_compatibility_count=1,
                marker_counts={"bad": 1},
                canonical_jsonl_sha256="c" * 64,
                fixture_manifest_sha256="b" * 64,
            ),
        )


def test_pipeline_identity_is_fail_closed_when_the_lock_has_stale_code_hashes() -> None:
    with pytest.raises(VesumReingestError, match="pipeline identity mismatch"):
        verify_pipeline_identity(
            {
                "pipeline": {
                    "parser_module": {"path": "scripts/rag/vesum_reingest.py", "sha256": "0" * 64},
                    "operator_entrypoint": {
                        "path": "scripts/rag/build_vesum_shadow.py",
                        "sha256": "0" * 64,
                    },
                }
            }
        )


def test_committed_lock_matches_the_current_pipeline_and_generated_fixture_manifest() -> None:
    project_root = Path(__file__).resolve().parents[1]
    lock = load_lock(project_root / "scripts" / "config" / "vesum_source.lock.json")
    fixture_path = project_root / "tests" / "fixtures" / "vesum_v680_fixture_manifest.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

    verify_pipeline_identity(lock)
    assert lock["release_asset"]["url"] == VESUM_URL
    assert hashlib.sha256(fixture_path.read_bytes()).hexdigest() == lock["expected"][
        "fixture_manifest_sha256"
    ]
    assert fixture["source"]["sha256"] == lock["release_asset"]["sha256"]
    assert fixture["known_absent_classes"] == lock["known_absent_marker_classes"]


def test_shadow_builder_refuses_production_database_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    asset_path = _write_synthetic_asset(tmp_path)
    production_path = tmp_path / "production.db"
    monkeypatch.setattr("scripts.rag.vesum_reingest.PRODUCTION_DB_PATH", production_path)

    with pytest.raises(VesumReingestError, match="step 1 only"):
        build_shadow_database(asset_path, production_path)
