"""Tests for the corpus training-usability decision audit."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.projects.open_model_data import audit_corpus_training_usability as audit


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False) + "\n", encoding="utf-8")


def _jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def _inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    drive = tmp_path / "drive"
    literary_row = {
        "text": "Український текст",
        "source_url": "https://www.ukrlib.com.ua/books/example",
        "work": "Твір",
        "author": "Автор",
        "year": 2024,
        "genre": "prose",
        "language_period": "modern",
    }
    _jsonl(drive / "literary_texts/ukrlib-one.jsonl", [literary_row])
    _jsonl(
        drive / "literary_texts/wikisource-one.jsonl",
        [{**literary_row, "source_url": "", "source": "uk.wikisource.org"}],
    )
    _jsonl(
        drive / "textbook_chunks/grade-01/book-one.jsonl",
        [
            {"text": "Чистий текст", "quality": {"is_clean": True, "clean_ratio": 1.0}},
            {"text": "ОÂА пошкоджено", "quality": {"is_clean": False, "clean_ratio": 0.5}},
        ],
    )
    (drive / "textbooks").mkdir(parents=True)
    (drive / "textbooks/book-one.pdf").write_bytes(b"%PDF-fixture")
    url_map = tmp_path / "urls.yaml"
    url_map.write_text("book-one: https://pidruchnyk.com.ua/example.html\n", encoding="utf-8")
    profile = tmp_path / "profile.json"
    _json(
        profile,
        {
            "schema_version": "corpus_profile_receipt_v1",
            "coverage": {"complete": True, "processed_rows": 7, "processed_lexical_words": 70},
            "distributions": {
                "period": {
                    "modern": {"rows": 5, "lexical_words": 50},
                    "middle_ukrainian": {"rows": 1, "lexical_words": 10},
                    "old_east_slavic": {"rows": 1, "lexical_words": 10},
                },
                "source_family": {
                    "literary": {"rows": 2, "lexical_words": 20},
                    "public_textbooks": {"rows": 2, "lexical_words": 20},
                    "external_articles": {"rows": 1, "lexical_words": 10},
                    "wikipedia": {"rows": 2, "lexical_words": 20},
                },
            },
            "vesum": {"tokens_attested": 60, "tokens_unknown": 10},
        },
    )
    detector = tmp_path / "detector.json"
    _json(
        detector,
        {
            "schema_version": "language_contact_receipt_v1",
            "coverage": {"complete": True, "processed_rows": 7, "processed_lexical_words": 70},
            "candidate_arithmetic": {"total_candidates": 3},
        },
    )
    return drive, url_map, profile, detector


def test_audit_produces_deterministic_continue_decision(tmp_path: Path) -> None:
    drive, url_map, profile, detector = _inputs(tmp_path)
    kwargs = {
        "literary_dir": drive / "literary_texts",
        "textbook_chunks_dir": drive / "textbook_chunks",
        "textbook_pdfs_dir": drive / "textbooks",
        "textbook_url_map": url_map,
        "profile_receipt": profile,
        "detector_receipt": detector,
    }

    first = audit.build_decision(**kwargs)
    second = audit.build_decision(**kwargs)

    assert first == second
    assert first["project_verdict"] == "continue"
    assert first["lineage"]["literary"]["rows_with_source_locator"] == 2
    assert first["lineage"]["textbooks"]["mojibake_rows"] == 1
    assert first["capability_decisions"]["local_research_and_model_training"] == (
        "operator_approved_for_project_goal"
    )
    assert first["capability_decisions"]["raw_source_redistribution"] == "separate_decision_required"
    assert str(tmp_path) not in audit.canonical_json(first)

    output = tmp_path / "decision.json"
    audit.write_validated(output, first)
    assert json.loads(output.read_text(encoding="utf-8")) == first


def test_audit_rejects_incomplete_or_disagreeing_receipts(tmp_path: Path) -> None:
    drive, url_map, profile, detector = _inputs(tmp_path)
    detector_value = json.loads(detector.read_text(encoding="utf-8"))
    detector_value["coverage"]["processed_rows"] = 8
    _json(detector, detector_value)

    with pytest.raises(audit.UsabilityAuditError, match="totals disagree"):
        audit.build_decision(
            literary_dir=drive / "literary_texts",
            textbook_chunks_dir=drive / "textbook_chunks",
            textbook_pdfs_dir=drive / "textbooks",
            textbook_url_map=url_map,
            profile_receipt=profile,
            detector_receipt=detector,
        )
