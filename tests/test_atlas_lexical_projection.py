"""ADR-017 lexical projection schema, quality gates, and deterministic export tests."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.atlas import lexical_projection as projection


def _vesum_db(path: Path, forms: list[str]) -> Path:
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE forms (word_form TEXT NOT NULL)")
        connection.executemany("INSERT INTO forms(word_form) VALUES (?)", [(form,) for form in forms])
    return path


def _attestation(source_id: str, chunk_id: str, text: str, **extra: object) -> dict[str, object]:
    span_start = 0
    span_end = len(text)
    return {
        "record_type": "attestation",
        "attestation_id": projection.deterministic_attestation_id(source_id, chunk_id, span_start, span_end),
        "sense_slug": "прапор:core",
        "source_id": source_id,
        "chunk_id": chunk_id,
        "span_start": span_start,
        "span_end": span_end,
        "text": text,
        **extra,
    }


def _source(source_id: str, *, language_period: str = "modern", source_kind: str = "literary") -> dict[str, str]:
    return {
        "record_type": "source",
        "source_id": source_id,
        "source_work": source_id,
        "language_period": language_period,
        "source_kind": source_kind,
        "license_type": "CC-BY-4.0",
        "attribution_type": "required",
        "rights_status": "redistributable",
    }


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text("".join(f"{projection.canonical_json(record)}\n" for record in records), encoding="utf-8")


def test_round_trip_keeps_good_rows_byte_exact_and_rejects_each_bad_attestation_class(tmp_path: Path) -> None:
    good_attestation = _attestation("literary-modern", "modern-1", "Ми йдемо до школи.")
    bad_archaic = _attestation("literary-archaic", "old-1", "Ми йдемо до школи.")
    bad_russian = _attestation("literary-russian", "russian-1", "Это ёлка.")
    bad_exercise = _attestation(
        "textbook-ukrmova",
        "ukrmova-1",
        "Її зошит лежить на парті.",
        chunk_text="Помилковий вислів стоїть тут. Виправте помилки у реченнях.",
    )
    good_records: list[dict[str, object]] = [
        _source("literary-modern"),
        {
            "record_type": "lemma_entry",
            "entry_slug": "прапор",
            "lemma": "прапор",
            "display_head": "прапор",
            "entry_type": "lemma",
            "route_path": "/dictionary/прапор",
        },
        {
            "record_type": "sense",
            "sense_slug": "прапор:core",
            "entry_slug": "прапор",
            "sense_key": "core",
            "definition": {"uk": "Полотнище на держаку."},
            "review_state": "approved",
        },
        good_attestation,
        {"record_type": "practice_deck", "deck_slug": "a1-flags-v1", "title": "Прапори", "version": "v1"},
        {
            "record_type": "practice_deck_item",
            "deck_slug": "a1-flags-v1",
            "sense_slug": "прапор:core",
            "attestation_id": good_attestation["attestation_id"],
            "card_template": "recognition",
        },
    ]
    records = [
        *good_records,
        _source("literary-archaic", language_period="middle_ukrainian"),
        _source("literary-russian"),
        _source("textbook-ukrmova", source_kind="textbook"),
        bad_archaic,
        bad_russian,
        bad_exercise,
    ]
    input_path = tmp_path / "input.jsonl"
    expected_path = tmp_path / "expected-good.jsonl"
    db_path = tmp_path / "atlas-v2.db"
    export_path = tmp_path / "export.jsonl"
    report_path = tmp_path / "rejections.jsonl"
    _write_jsonl(input_path, records)
    expected_records = (
        sorted([good_records[0], *records[6:9]], key=lambda record: str(record["source_id"])) + good_records[1:]
    )
    _write_jsonl(expected_path, expected_records)
    vesum_db = _vesum_db(tmp_path / "vesum.db", ["ми", "йдемо", "до", "школи"])

    result = projection.build_projection(input_path, db_path, vesum_db=vesum_db)
    projection.export_projection(db_path, export_path)
    projection.write_rejection_report(result, report_path)

    # Exact bytes prove that accepted JSONL records retain their source form.
    assert export_path.read_bytes() == expected_path.read_bytes()
    assert result.accepted_records == 9
    assert result.rejection_counts == {
        "language_period_not_modern": 1,
        "russian_only_letter": 1,
        "textbook_exercise_instruction": 1,
    }
    report_rows = [json.loads(line) for line in report_path.read_text(encoding="utf-8").splitlines()]
    assert {row["gate_failed"] for row in report_rows} == set(result.rejection_counts)

    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("SELECT COUNT(*) FROM attestations").fetchone()[0] == 1
        assert connection.execute("SELECT type FROM sqlite_master WHERE name='articles'").fetchone()[0] == "view"
        assert connection.execute("SELECT slug FROM articles").fetchone()[0] == "прапор"
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO senses(sense_slug, entry_slug, record_json) VALUES ('orphan:core', 'missing', '{}')"
            )


def test_purity_gate_requires_both_signals_and_uses_the_calibrated_ratio(tmp_path: Path) -> None:
    source = _source("literary-modern")
    known_without_ukrainian_specific_letters = _attestation("literary-modern", "known-1", "Там був пан.")
    too_many_unknown_without_ukrainian_specific_letters = _attestation("literary-modern", "unknown-1", "Там був жмур.")
    records: list[dict[str, object]] = [
        source,
        {"record_type": "lemma_entry", "entry_slug": "прапор", "lemma": "прапор", "entry_type": "lemma"},
        {"record_type": "sense", "sense_slug": "прапор:core", "entry_slug": "прапор"},
        known_without_ukrainian_specific_letters,
        too_many_unknown_without_ukrainian_specific_letters,
    ]
    input_path = tmp_path / "input.jsonl"
    _write_jsonl(input_path, records)
    vesum_db = _vesum_db(tmp_path / "vesum.db", ["там", "був", "пан"])

    result = projection.build_projection(input_path, tmp_path / "atlas-v2.db", vesum_db=vesum_db)

    assert result.accepted_records == 4
    assert result.rejection_counts == {"ukrainian_purity_unknown_ratio": 1}


def test_strict_mode_fails_closed_when_a_builder_gate_rejects_an_attestation(tmp_path: Path) -> None:
    bad = _attestation("literary-russian", "russian-1", "Это ёлка.")
    records: list[dict[str, object]] = [
        _source("literary-russian"),
        {"record_type": "lemma_entry", "entry_slug": "прапор", "lemma": "прапор", "entry_type": "lemma"},
        {"record_type": "sense", "sense_slug": "прапор:core", "entry_slug": "прапор"},
        bad,
    ]
    input_path = tmp_path / "input.jsonl"
    output_db = tmp_path / "atlas-v2.db"
    _write_jsonl(input_path, records)
    vesum_db = _vesum_db(tmp_path / "vesum.db", [])

    with pytest.raises(projection.ProjectionError, match="strict build rejected 1"):
        projection.build_projection(input_path, output_db, vesum_db=vesum_db, strict=True)
    assert not output_db.exists()
