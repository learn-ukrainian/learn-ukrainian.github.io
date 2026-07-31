"""Contract and behavior tests for the Ukrainian Data Foundry profiler."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

import scripts.projects.open_model_data.profile_corpus as profiler_module
from scripts.projects.open_model_data.profile_corpus import (
    canonical_json,
    main,
    normalize_form,
    profile_corpus,
)

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_SCHEMA = ROOT / "data/projects/open_model_data/contracts/review_candidate_v1.schema.json"
RECEIPT_SCHEMA = ROOT / "data/projects/open_model_data/contracts/corpus_profile_receipt_v1.schema.json"


def test_normalization_removes_stress_without_erasing_ukrainian_diacritics() -> None:
    assert normalize_form("Украї́на") == "україна"
    assert normalize_form("Його") == "його"
    assert normalize_form("з’яви́вся") == "з'явився"


def _write_vesum(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE forms (word_form TEXT NOT NULL, lemma TEXT NOT NULL, tags TEXT NOT NULL, pos TEXT NOT NULL)"
        )
        connection.execute("CREATE INDEX idx_form ON forms(word_form)")
        connection.execute(
            "INSERT INTO forms(word_form, lemma, tags, pos) VALUES (?, ?, ?, ?)",
            ("звучить", "звучати", "verb:imperf:pres:3:s", "verb"),
        )


def _write_sources(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE documents (
                id INTEGER PRIMARY KEY,
                locator TEXT NOT NULL,
                text TEXT NOT NULL,
                period TEXT NOT NULL,
                genre TEXT NOT NULL,
                register TEXT NOT NULL,
                origin TEXT NOT NULL
            )
            """
        )
        connection.executemany(
            "INSERT INTO documents(locator, text, period, genre, register, origin) VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("r1", "звучить", "modern", "fixture", "neutral", "human_authored_source"),
                ("r2", "звучит", "modern", "fixture", "neutral", "human_authored_source"),
                ("r3", "Дивнеім'я", "modern", "fixture", "neutral", "human_authored_source"),
                ("r4", "давньослівце", "middle_ukrainian", "fixture", "literary", "human_authored_source"),
                ("r5", "діалектизмище", "modern", "fixture", "regional_dialectal", "human_authored_source"),
                ("r6", "London", "modern", "fixture", "quoted_foreign", "human_authored_source"),
            ],
        )


def _config(*, database: str = "sources.db") -> dict[str, object]:
    return {
        "schema_version": "corpus_profile_config_v1",
        "profile_id": "fixture-profile-v1",
        "source_snapshot_id": "fixture-source-v1",
        "record_batch_size": 2,
        "top_unknown_limit": 10,
        "vesum": {
            "database": "vesum.db",
            "snapshot_id": "fixture-vesum-v1",
            "interface": "scripts.verification.vesum.verify_words",
            "batch_size": 2,
        },
        "sources": [
            {
                "source_family": "fixture_documents",
                "inventory_asset_id": "db.fixture",
                "adapter": {
                    "kind": "sqlite_query_v1",
                    "database": database,
                    "table": "documents",
                    "id_column": "id",
                    "text_column": "text",
                    "locator_column": "locator",
                    "dimensions": {
                        "period": {"column": "period"},
                        "genre": {"column": "genre"},
                        "register": {"column": "register"},
                        "origin": {"column": "origin"},
                    },
                },
                "evidence": {
                    "provenance_status": "partial",
                    "rights_status": "not_reconstructed",
                    "origin_status": "inventory_classified",
                    "contamination_status": "not_checked",
                    "permitted_use": "provenance_investigation",
                },
                "expected": {"rows": 6, "lexical_words": 6},
            }
        ],
    }


def _run(tmp_path: Path, config: dict[str, object], suffix: str):
    config_path = tmp_path / f"config-{suffix}.json"
    config_path.write_text(canonical_json(config) + "\n", encoding="utf-8")
    return profile_corpus(
        config_path=config_path,
        input_root=tmp_path,
        summary_output=tmp_path / f"summary-{suffix}.json",
        candidates_output=tmp_path / f"candidates-{suffix}.jsonl",
    )


def test_profiles_fixture_with_pinned_vesum_and_byte_stable_outputs(tmp_path: Path) -> None:
    _write_sources(tmp_path / "sources.db")
    _write_vesum(tmp_path / "vesum.db")

    first = _run(tmp_path, _config(), "first")
    second = _run(tmp_path, _config(), "second")

    assert first.complete is True
    assert first.summary_path.read_bytes() == second.summary_path.read_bytes()
    assert first.candidates_path.read_bytes() == second.candidates_path.read_bytes()
    assert first.summary["coverage"] == {
        "complete": True,
        "expected_lexical_words": 6,
        "expected_rows": 6,
        "inaccessible_sources": [],
        "processed_lexical_words": 6,
        "processed_rows": 6,
        "source_results": [
            {
                "actual": {"lexical_words": 6, "rows": 6},
                "expected": {"lexical_words": 6, "rows": 6},
                "inventory_asset_id": "db.fixture",
                "matches_expected": True,
                "source_family": "fixture_documents",
            }
        ],
    }
    assert first.summary["vesum"]["tokens_attested"] == 1
    assert first.summary["vesum"]["tokens_unknown"] == 5
    assert first.summary["admission_safety"]["zero_current_admissions"] is True
    assert first.summary["admission_safety"]["excluded_rows"] == 6

    schema = json.loads(CANDIDATE_SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    candidates = [json.loads(line) for line in first.candidates_path.read_text(encoding="utf-8").splitlines()]
    assert len(candidates) == 5
    assert all(not list(validator.iter_errors(candidate)) for candidate in candidates)
    by_form = {candidate["normalized_form"]: candidate for candidate in candidates}
    assert "звучить" not in by_form
    assert by_form["звучит"]["candidate_category"] == "non_ukrainian_form_candidate"
    assert by_form["звучит"]["automatic_error_label"] is False
    assert by_form["дивнеім'я"]["candidate_category"] == "proper_name_candidate"
    assert by_form["давньослівце"]["candidate_category"] == "protected_variation_candidate"
    assert by_form["діалектизмище"]["candidate_category"] == "protected_variation_candidate"
    assert by_form["london"]["candidate_category"] == "foreign_language_candidate"
    assert all(candidate["review_disposition"] == "unresolved" for candidate in candidates)

    receipt_schema = json.loads(RECEIPT_SCHEMA.read_text(encoding="utf-8"))
    invalid_receipt = json.loads(first.summary_path.read_text(encoding="utf-8"))
    invalid_receipt["admission_safety"]["zero_current_admissions"] = "false"
    assert list(Draft202012Validator(receipt_schema).iter_errors(invalid_receipt))


def test_reports_inaccessible_required_source_without_reducing_denominator(tmp_path: Path) -> None:
    _write_vesum(tmp_path / "vesum.db")

    result = _run(tmp_path, _config(database="missing.db"), "missing")

    assert result.complete is False
    assert result.summary["coverage"]["expected_rows"] == 6
    assert result.summary["coverage"]["processed_rows"] == 0
    assert result.summary["coverage"]["inaccessible_sources"] == [
        {"reason": "FileNotFoundError", "source_family": "fixture_documents"}
    ]
    assert result.candidates_path.read_bytes() == b""


def test_cli_exit_codes_report_complete_and_incomplete_coverage(tmp_path: Path) -> None:
    _write_sources(tmp_path / "sources.db")
    _write_vesum(tmp_path / "vesum.db")
    complete_config = tmp_path / "complete.json"
    complete_config.write_text(canonical_json(_config()) + "\n", encoding="utf-8")

    common = ["--input-root", str(tmp_path)]
    assert (
        main(
            [
                "--config",
                str(complete_config),
                *common,
                "--summary-output",
                str(tmp_path / "complete-summary.json"),
                "--candidates-output",
                str(tmp_path / "complete-candidates.jsonl"),
            ]
        )
        == 0
    )

    missing_config = tmp_path / "missing.json"
    missing_config.write_text(
        canonical_json(_config(database="missing.db")) + "\n",
        encoding="utf-8",
    )
    assert (
        main(
            [
                "--config",
                str(missing_config),
                *common,
                "--summary-output",
                str(tmp_path / "missing-summary.json"),
                "--candidates-output",
                str(tmp_path / "missing-candidates.jsonl"),
            ]
        )
        == 2
    )


def test_runtime_candidate_schema_is_enforced(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_sources(tmp_path / "sources.db")
    _write_vesum(tmp_path / "vesum.db")
    schema = json.loads(CANDIDATE_SCHEMA.read_text(encoding="utf-8"))
    schema["properties"]["candidate_category"]["enum"] = ["impossible_fixture_category"]
    strict_schema = tmp_path / "strict-candidate.schema.json"
    strict_schema.write_text(canonical_json(schema) + "\n", encoding="utf-8")
    monkeypatch.setattr(profiler_module, "CANDIDATE_SCHEMA_PATH", strict_schema)

    with pytest.raises(ValueError, match="review candidate does not satisfy its schema"):
        _run(tmp_path, _config(), "invalid-candidate")


def test_invalid_receipt_does_not_replace_prior_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_sources(tmp_path / "sources.db")
    _write_vesum(tmp_path / "vesum.db")
    schema = json.loads(RECEIPT_SCHEMA.read_text(encoding="utf-8"))
    schema["properties"]["profile_id"] = {"const": "impossible-profile-id"}
    strict_schema = tmp_path / "strict-receipt.schema.json"
    strict_schema.write_text(canonical_json(schema) + "\n", encoding="utf-8")
    monkeypatch.setattr(profiler_module, "RECEIPT_SCHEMA_PATH", strict_schema)

    config_path = tmp_path / "invalid-receipt-config.json"
    config_path.write_text(canonical_json(_config()) + "\n", encoding="utf-8")
    summary_path = tmp_path / "existing-summary.json"
    summary_path.write_bytes(b"known-good-prior-output\n")

    with pytest.raises(ValueError, match="aggregate receipt does not satisfy its schema"):
        profile_corpus(
            config_path=config_path,
            input_root=tmp_path,
            summary_output=summary_path,
            candidates_output=tmp_path / "invalid-receipt-candidates.jsonl",
        )
    assert summary_path.read_bytes() == b"known-good-prior-output\n"
