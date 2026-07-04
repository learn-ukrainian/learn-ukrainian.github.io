from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from scripts.audit import ingest_ua_gec_gold as ingest

qg_schema = ingest.qg_schema


def _write_ua_gec_db(path: Path, rows: list[dict[str, Any]]) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE ua_gec_errors (
                id INTEGER PRIMARY KEY,
                error TEXT NOT NULL,
                correct TEXT NOT NULL,
                error_type TEXT NOT NULL,
                doc_id TEXT NOT NULL,
                annotator_id TEXT NOT NULL,
                partition TEXT NOT NULL,
                is_native INTEGER,
                source_lang TEXT
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO ua_gec_errors (
                id, error, correct, error_type, doc_id, annotator_id,
                partition, is_native, source_lang
            )
            VALUES (
                :id, :error, :correct, :error_type, :doc_id, :annotator_id,
                :partition, :is_native, :source_lang
            )
            """,
            rows,
        )


def _row(
    row_id: int,
    error: str,
    correction: str,
    tag: str,
    *,
    source_lang: str | None = "ru",
) -> dict[str, Any]:
    return {
        "id": row_id,
        "error": error,
        "correct": correction,
        "error_type": tag,
        "doc_id": "0001",
        "annotator_id": "1",
        "partition": "gec-fluency/train",
        "is_native": 0,
        "source_lang": source_lang,
    }


def _write_mini_ua_gec_root(path: Path) -> None:
    ann_dir = path / "data" / "gec-fluency" / "train" / "annotated"
    ann_dir.mkdir(parents=True)
    (path / "LICENSE").write_text("Attribution 4.0 International\n", encoding="utf-8")
    (path / "README.md").write_text("November 2022: Version 2.0 released.\n", encoding="utf-8")
    (ann_dir / "0001.a1.ann").write_text(
        "\n".join(
            [
                "У звіті автор написав {на протязі=>протягом:::error_type=F/Calque} двох тижнів, і редактор зберіг повний контекст.",
                "Вона пишається {місто=>містом:::error_type=G/Case} у великому есе про подорожі та сімейні історії.",
                "Це була {важливий=>важлива:::error_type=G/Gender} зустріч для всієї групи студентів.",
                "У чернетці лишився {рожі=>мармизи:::error_type=F/Calque} посеред довгого речення з іншими словами.",
                "У репліці трапилося {Ах=>Ох:::error_type=F/Calque} у достатньо довгому реченні, але сама пара непридатна.",
            ]
        ),
        encoding="utf-8",
    )


def test_parse_annotated_text_preserves_plain_text_and_spans() -> None:
    parsed = ingest.parse_annotated_text(
        "Перед {на протязі=>протягом:::error_type=F/Calque} дня була примітка."
    )

    assert parsed.source_text == "Перед на протязі дня була примітка."
    assert parsed.target_text == "Перед протягом дня була примітка."
    annotation = parsed.annotations[0]
    assert annotation.tag == "F/Calque"
    assert parsed.source_text[annotation.source_start : annotation.source_end] == "на протязі"
    assert parsed.target_text[annotation.target_start : annotation.target_end] == "протягом"


def test_curation_rejects_known_junk_and_short_word_forms_but_keeps_contextual_rows(tmp_path: Path) -> None:
    ua_gec_root = tmp_path / "ua-gec"
    db_path = tmp_path / "sources.db"
    _write_mini_ua_gec_root(ua_gec_root)
    _write_ua_gec_db(
        db_path,
        [
            _row(1, "на протязі", "протягом", "F/Calque"),
            _row(2, "рожі", "мармизи", "F/Calque"),
            _row(3, "Ах", "Ох", "F/Calque"),
        ],
    )

    report = ingest.run_curation(
        db_path=db_path,
        ua_gec_root=ua_gec_root,
        config=ingest.CurationConfig(tag_limits={"F/Calque": 10, "G/Case": 0, "G/Gender": 0}),
    )

    assert [row["error"] for row in report.kept_rows] == ["на протязі"]
    rejected_by_id = {item.candidate_id: item.reason for item in report.rejected}
    assert rejected_by_id[2] == "known_context_stripped_junk"
    assert rejected_by_id[3] == "too_short_single_word_form"


def test_fixture_round_trip_preserves_attribution_tags_spans_and_schema(tmp_path: Path) -> None:
    ua_gec_root = tmp_path / "ua-gec"
    db_path = tmp_path / "sources.db"
    output_path = tmp_path / "ua-gec-gold.json"
    _write_mini_ua_gec_root(ua_gec_root)
    _write_ua_gec_db(
        db_path,
        [
            _row(1, "на протязі", "протягом", "F/Calque"),
            _row(2, "місто", "містом", "G/Case"),
            _row(3, "важливий", "важлива", "G/Gender"),
        ],
    )
    config = ingest.CurationConfig(tag_limits={"F/Calque": 10, "G/Case": 10, "G/Gender": 10})
    report = ingest.run_curation(db_path=db_path, ua_gec_root=ua_gec_root, config=config)
    fixture = ingest.build_fixture(
        report,
        ua_gec_root=ua_gec_root,
        retrieval_date="2026-07-05",
        config=config,
    )

    ingest.write_fixture(output_path, fixture)
    loaded = json.loads(output_path.read_text(encoding="utf-8"))

    assert loaded["attribution"]["dataset"] == "UA-GEC"
    assert loaded["attribution"]["source"] == "grammarly/ua-gec"
    assert loaded["attribution"]["license"] == "CC BY 4.0"
    assert loaded["attribution"]["retrieval_date"] == "2026-07-05"
    assert loaded["attribution"]["source_version"] == "2.0"

    assert [item["tag"] for item in loaded["items"]] == ["F/Calque", "G/Case", "G/Gender"]
    for item in loaded["items"]:
        span = item["spans"]["source"]
        assert item["source_excerpt"][span["start"] : span["end"]] == item["error"]
        assert item["finding"]["ua_gec_tag"] == item["tag"]
        assert item["finding"]["attribution"]["license"] == "CC-BY-4.0"
        assert item["mapped_tag"] == qg_schema.map_ua_gec_tag(item["tag"], source_lang=item["source_lang"])
        qg_schema.validate_finding(item["finding"])


def test_committed_fixture_preserves_tags_spans_and_attribution() -> None:
    fixture_path = Path(__file__).resolve().parents[1] / "data" / "ua-gec-gold" / "ua-gec-gold.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

    assert fixture["attribution"]["dataset"] == "UA-GEC"
    assert fixture["attribution"]["source"] == "grammarly/ua-gec"
    assert fixture["attribution"]["license"] == "CC BY 4.0"
    assert fixture["counts"]["kept"] == len(fixture["items"])
    assert set(fixture["counts"]["kept_by_tag"]) == {"F/Calque", "G/Case", "G/Gender"}

    for item in fixture["items"]:
        span = item["spans"]["source"]
        assert item["source_excerpt"][span["start"] : span["end"]] == item["error"]
        assert item["finding"]["span"] == span
        assert item["finding"]["ua_gec_tag"] == item["tag"]
        assert item["finding"]["attribution"]["license"] == "CC-BY-4.0"
        qg_schema.validate_finding(item["finding"])
