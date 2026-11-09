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


@pytest.mark.parametrize("paradigm", [False, True])
def test_folded_indexes_reach_mixed_case_and_preserve_marker_filter(tmp_path: Path, paradigm: bool) -> None:
    from scripts.curriculum.evidence.sources import Sources
    from scripts.rag.word_identity import normalize_evidence_form

    asset = tmp_path / "folded.txt.bz2"
    with bz2.open(asset, "wt", encoding="utf-8") as target:
        target.write("MiXeD’HeAd noun\n  MiXeD’FoRm noun\nMiXeD’HeAd noun:bad\n  MiXeD’FoRm noun:bad\n")
    database = tmp_path / "folded.db"
    build_shadow_database(asset, database)
    column = "lemma" if paradigm else "word_form"
    value = "mixed'head" if paradigm else "mixed'form"
    with sqlite3.connect(database) as conn:
        assert len(conn.execute("SELECT * FROM forms").fetchone()) == 4
        for word, lemma, folded_word, folded_lemma in conn.execute(
            "SELECT word_form, lemma, word_form_folded, lemma_folded FROM forms_all"
        ):
            assert folded_word == normalize_evidence_form(word)
            assert folded_lemma == normalize_evidence_form(lemma)
        plan = conn.execute(
            f"EXPLAIN QUERY PLAN SELECT word_form, lemma, pos, tags FROM forms WHERE {column} IN "
            f"(SELECT {column} FROM forms_all WHERE {column}_folded IN (?))", (value,),
        ).fetchall()
        assert any(f"idx_forms_all_{column}_folded" in row[3] for row in plan)
        assert any(f"idx_forms_all_{column} (" in row[3] for row in plan)
    with Sources(vesum_db=database) as api:
        rows = api._receipt_vesum_rows([value], paradigm=paradigm).raw[value]
        assert len(rows) == (2 if paradigm else 1)
        assert all(row["tags"] == "noun" for row in rows)
        assert rows[0][column] == ("MiXeD’HeAd" if paradigm else "MiXeD’FoRm")


@pytest.mark.parametrize("text,expected", [
    ("MiXeD’Fo\u0301Rm", "mixed'form"),
    ("MiXeDʼFo\u0300Rm", "mixed'form"),
    ("MiXeD‘FoRm", "mixed'form"),
    ("MiXeD`FoRm", "mixed'form"),
    (" One  Two-іЇй! ", " one  two-іїй! "),
])
def test_folded_build_identity_is_exact_except_case_stress_apostrophes(text: str, expected: str) -> None:
    from scripts.rag.word_identity import normalize_evidence_form

    assert normalize_evidence_form(text) == expected


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
    assert fixture["generated_by"]["importer_version"] == lock["pipeline"]["importer_version"]
    assert fixture["known_absent_classes"] == lock["known_absent_marker_classes"]


@pytest.mark.parametrize("mode", ["missing", "stale", "wrong_path"])
def test_folded_builder_pins_the_normalizer_identity(mode: str) -> None:
    root = Path(__file__).resolve().parents[1]
    lock = load_lock(root / "scripts/config/vesum_source.lock.json")
    if mode == "missing":
        del lock["pipeline"]["word_identity"]
    elif mode == "stale":
        lock["pipeline"]["word_identity"]["sha256"] = "0" * 64
    else:
        lock["pipeline"]["word_identity"]["path"] = "other.py"
    with pytest.raises(VesumReingestError, match="word_identity"):
        verify_pipeline_identity(lock)


def test_shadow_builder_refuses_production_database_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    asset_path = _write_synthetic_asset(tmp_path)
    production_path = tmp_path / "production.db"
    monkeypatch.setattr("scripts.rag.vesum_reingest.PRODUCTION_DB_PATH", production_path)

    with pytest.raises(VesumReingestError, match="step 1 only"):
        build_shadow_database(asset_path, production_path)


def test_release_download_uses_client_and_verified_cache(tmp_path, monkeypatch):
    import io

    from scripts.rag import vesum_reingest
    asset = _write_synthetic_asset(tmp_path)
    lock = _lock_for_asset(asset)
    calls = []
    def opened(request, **kwargs):
        calls.append(request.full_url)
        return io.BytesIO(asset.read_bytes())
    monkeypatch.setattr(vesum_reingest.github_client, "http_open", opened)
    downloaded = vesum_reingest.fetch_release_asset(lock, tmp_path / "cache")
    assert downloaded.read_bytes() == asset.read_bytes()
    assert vesum_reingest.fetch_release_asset(lock, tmp_path / "cache") == downloaded
    assert calls == [lock["release_asset"]["url"]]


def test_release_limit_preserves_cache_and_has_no_retry(tmp_path, monkeypatch):
    from scripts.common.github_client import GitHubRateLimited
    from scripts.rag import vesum_reingest
    lock = _lock_for_asset(_write_synthetic_asset(tmp_path))
    calls = []
    def unavailable(request, **kwargs):
        calls.append(request.full_url)
        raise GitHubRateLimited(2000)
    monkeypatch.setattr(vesum_reingest.github_client, "http_open", unavailable)
    with pytest.raises(GitHubRateLimited):
        vesum_reingest.fetch_release_asset(lock, tmp_path / "cache")
    assert len(calls) == 1
    assert list((tmp_path / "cache").iterdir()) == []
