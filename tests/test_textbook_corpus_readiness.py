from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.projects.open_model_data import textbook_corpus_readiness as readiness


def _write_jsonl(path: Path, rows: list[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_selection(path: Path, *slugs: str) -> None:
    path.write_text(
        "books:\n" + "".join(f"  - id: {slug}-id\n    slug: {slug}\n" for slug in slugs),
        encoding="utf-8",
    )


def _write_db(path: Path, rows: list[tuple[str, int]]) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE textbooks (id INTEGER PRIMARY KEY, source_file TEXT, text TEXT)"
        )
        row_id = 1
        for source, count in rows:
            for _ in range(count):
                connection.execute(
                    "INSERT INTO textbooks(id, source_file, text) VALUES (?, ?, ?)",
                    (row_id, source, "fixture"),
                )
                row_id += 1


def _source(report: dict, name: str) -> dict:
    return next(item for item in report["sources"] if item["source"] == name)


def test_reconciles_required_statuses_and_counts(tmp_path: Path) -> None:
    root = tmp_path / "drive"
    root.mkdir()
    (root / "ready.pdf").write_bytes(b"%PDF-ready")
    _write_jsonl(root / "ready.jsonl", [{"text": "one"}, {"text": "two"}, {"text": "three"}])
    (root / "pdf-only.pdf").write_bytes(b"%PDF-only")
    _write_jsonl(root / "chunks-only.jsonl", [{"text": "orphan"}, {"text": "orphan-2"}, {"text": "orphan-3"}])
    (root / "not-ingested.pdf").write_bytes(b"%PDF-not-ingested")
    _write_jsonl(root / "not-ingested.jsonl", [{"text": str(index)} for index in range(3)])
    (root / "tiny.pdf").write_bytes(b"%PDF-tiny")
    _write_jsonl(root / "tiny.jsonl", [{"text": "front"}, {"text": "matter"}])

    selection = tmp_path / "selection.yaml"
    _write_selection(selection, "ready", "pdf-only", "chunks-only", "not-ingested", "tiny", "missing")
    db = tmp_path / "sources.db"
    _write_db(db, [("ready", 3), ("tiny", 2), ("db-only", 4)])

    report = readiness.build_report(
        gdrive_root=root,
        db_path=db,
        selection_path=selection,
    )

    assert _source(report, "ready")["status"] == "ready"
    assert _source(report, "pdf-only")["status"] == "pdf_without_chunks"
    assert _source(report, "chunks-only")["states"] == ["chunks_without_pdf", "chunks_not_ingested"]
    assert _source(report, "not-ingested")["status"] == "chunks_not_ingested"
    assert _source(report, "db-only")["status"] == "db_without_chunks"
    assert _source(report, "tiny")["status"] == "suspect_extraction"
    assert _source(report, "missing")["status"] == "missing_selected_source"
    assert report["counts"] == {
        "chunk_files": 4,
        "chunk_rows": 11,
        "db_rows": 9,
        "pdf_files": 4,
        "unique_chunk_payloads": 11,
        "unique_pdf_hashes": 4,
    }


def test_split_volumes_are_one_selected_source_with_explicit_components(tmp_path: Path) -> None:
    root = tmp_path / "drive"
    root.mkdir()
    slug = "6-klas-matematyka-ister-2023"
    pdf_data = b"%PDF-split-volume"
    (root / f"{slug}-1.pdf").write_bytes(pdf_data)
    (root / f"{slug}-2.pdf").write_bytes(pdf_data)
    rows = [
        {"chunk_id": "one", "text": "a"},
        {"chunk_id": "two", "text": "b"},
        {"chunk_id": "three", "text": "c"},
    ]
    _write_jsonl(root / f"{slug}-1.jsonl", rows)
    _write_jsonl(root / f"{slug}-2.jsonl", rows)
    selection = tmp_path / "selection.yaml"
    _write_selection(selection, slug)
    db = tmp_path / "sources.db"
    _write_db(db, [(f"{slug}-1", 3), (f"{slug}-2", 3)])
    first_map = tmp_path / "source-map.yaml"
    first_map.write_text(f"{slug}: https://one.example/book.html\n", encoding="utf-8")
    second_map = tmp_path / "acquisition-map.yaml"
    second_map.write_text(f"{slug}-2: https://two.example/book-part-2.pdf\n", encoding="utf-8")

    report = readiness.build_report(
        gdrive_root=root,
        db_path=db,
        selection_path=selection,
        url_maps=[first_map, second_map],
    )
    source = _source(report, slug)

    assert len(report["sources"]) == 1
    assert source["status"] == "ready"
    assert [component["component"] for component in source["components"]] == ["part-1", "part-2"]
    assert {item["locator"] for item in source["acquisition_locators"]} == {
        "https://one.example/book.html",
        "https://two.example/book-part-2.pdf",
    }
    assert {item["map_index"] for item in source["acquisition_locators"]} == {0, 1}
    assert len(report["duplicates"]["duplicate_pdf_hashes"]) == 1
    assert report["duplicates"]["duplicate_pdf_hashes"][0]["count"] == 2
    assert len(report["duplicates"]["duplicate_chunk_payload_hashes"]) == 3
    assert source["chunks"]["row_count"] == 6
    assert source["chunks"]["unique_payload_count"] == 3
    assert report["counts"]["unique_pdf_hashes"] == 1
    assert report["counts"]["unique_chunk_payloads"] == 3


def test_sparse_273_page_fixture_and_mojibake_are_flagged_without_text_output(tmp_path: Path) -> None:
    root = tmp_path / "drive"
    root.mkdir()
    (root / "biology.pdf").write_bytes(b"%PDF-1.4\n" + b"/Type /Page " * 273)
    _write_jsonl(
        root / "biology.jsonl",
        [{"text": "ОÂА пошкоджено; äóøà. Îñü"}, {"text": "front matter"}],
    )
    selection = tmp_path / "selection.yaml"
    _write_selection(selection, "biology")
    db = tmp_path / "sources.db"
    _write_db(db, [("biology", 2)])

    report = readiness.build_report(
        gdrive_root=root,
        db_path=db,
        selection_path=selection,
    )
    source = _source(report, "biology")
    assert source["status"] == "suspect_extraction"
    assert report["files"]["pdfs"][0]["page_count"] == 273
    assert report["mojibake"] == {
        "files": ["biology.jsonl"],
        "jsonl_files": 1,
        "rows": 1,
    }
    serialized = readiness.canonical_json(report)
    assert "ОÂА" not in serialized
    assert "äóøà" not in serialized
    assert str(tmp_path) not in serialized


def test_mojibake_detector_does_not_flag_single_accented_letters(tmp_path: Path) -> None:
    root = tmp_path / "drive"
    root.mkdir()
    (root / "book.pdf").write_bytes(b"%PDF-book")
    _write_jsonl(
        root / "book.jsonl",
        [
            {"text": "café, naïve, à la carte"},
            {"text": "clean Ukrainian"},
            {"text": "another clean row"},
        ],
    )
    selection = tmp_path / "selection.yaml"
    _write_selection(selection, "book")
    db = tmp_path / "sources.db"
    _write_db(db, [("book", 3)])

    report = readiness.build_report(
        gdrive_root=root,
        db_path=db,
        selection_path=selection,
    )

    assert report["mojibake"]["rows"] == 0


def test_project_drive_layout_ignores_non_textbook_corpora(tmp_path: Path) -> None:
    root = tmp_path / "drive"
    (root / "textbooks" / "grade-06").mkdir(parents=True)
    (root / "textbook_chunks" / "grade-06").mkdir(parents=True)
    (root / "literary_texts").mkdir()
    (root / "textbooks" / "grade-06" / "book.pdf").write_bytes(b"%PDF-book")
    _write_jsonl(
        root / "textbook_chunks" / "grade-06" / "book.jsonl",
        [{"text": "one"}, {"text": "two"}, {"text": "three"}],
    )
    (root / "literary_texts" / "not-a-textbook.pdf").write_bytes(b"%PDF-literary")
    _write_jsonl(root / "literary_texts" / "not-a-textbook.jsonl", [{"text": "literary"}])
    selection = tmp_path / "selection.yaml"
    _write_selection(selection, "book")
    db = tmp_path / "sources.db"
    _write_db(db, [("book", 3)])

    report = readiness.build_report(
        gdrive_root=root,
        db_path=db,
        selection_path=selection,
    )

    assert report["counts"]["pdf_files"] == 1
    assert report["counts"]["chunk_files"] == 1
    assert report["counts"]["chunk_rows"] == 3


def test_selection_page_slug_matches_canonical_retained_name_by_metadata(tmp_path: Path) -> None:
    root = tmp_path / "drive"
    root.mkdir()
    retained = "6-klas-ukrmova-golub-2023"
    (root / f"{retained}.pdf").write_bytes(b"%PDF-book")
    _write_jsonl(
        root / f"{retained}.jsonl",
        [{"text": "one"}, {"text": "two"}, {"text": "three"}],
    )
    selection = tmp_path / "selection.yaml"
    selection.write_text(
        """books:
  - id: g6-mova-golub
    grade: 6
    subject: ukrainska_mova
    author: Голуб
    year: 2023
    slug: 2595-ukrmova-6-klas-golub
""",
        encoding="utf-8",
    )
    db = tmp_path / "sources.db"
    _write_db(db, [(retained, 3)])

    report = readiness.build_report(
        gdrive_root=root,
        db_path=db,
        selection_path=selection,
    )

    assert len(report["sources"]) == 1
    source = _source(report, "2595-ukrmova-6-klas-golub")
    assert source["selected"] is True
    assert source["status"] == "ready"
    assert source["pdf"]["paths"] == [f"{retained}.pdf"]
    assert source["chunks"]["paths"] == [f"{retained}.jsonl"]
    assert source["db"]["source_files"] == [retained]


def test_selection_canonical_source_is_an_exact_retained_alias(tmp_path: Path) -> None:
    root = tmp_path / "drive"
    root.mkdir()
    retained = "5-klas-mystetstvo-rublia-2022"
    (root / f"{retained}.pdf").write_bytes(b"%PDF-book")
    _write_jsonl(
        root / f"{retained}.jsonl",
        [{"text": "one"}, {"text": "two"}, {"text": "three"}],
    )
    selection = tmp_path / "selection.yaml"
    selection.write_text(
        """books:
  - id: g5-mystetstvo-rublia
    slug: 1709-mystectstvo-rublia-5-klas
    canonical_source: 5-klas-mystetstvo-rublia-2022
""",
        encoding="utf-8",
    )
    db = tmp_path / "sources.db"
    _write_db(db, [(retained, 3)])

    report = readiness.build_report(
        gdrive_root=root,
        db_path=db,
        selection_path=selection,
    )

    source = _source(report, "1709-mystectstvo-rublia-5-klas")
    assert source["status"] == "ready"
    assert source["pdf"]["paths"] == [f"{retained}.pdf"]
    assert source["chunks"]["paths"] == [f"{retained}.jsonl"]
    assert source["db"]["source_files"] == [retained]


def test_metadata_match_refuses_wrong_year_and_ambiguous_selection(tmp_path: Path) -> None:
    root = tmp_path / "drive"
    root.mkdir()
    retained = "6-klas-ukrmova-golub-2022"
    (root / f"{retained}.pdf").write_bytes(b"%PDF-book")
    selection = tmp_path / "selection.yaml"
    selection.write_text(
        """books:
  - id: first
    grade: 6
    subject: ukrainska_mova
    author: Голуб
    year: 2023
    slug: first-page-slug
  - id: second
    grade: 6
    subject: ukrainska_mova
    author: Голуб
    year: 2023
    slug: second-page-slug
""",
        encoding="utf-8",
    )
    db = tmp_path / "sources.db"
    _write_db(db, [])

    report = readiness.build_report(
        gdrive_root=root,
        db_path=db,
        selection_path=selection,
    )

    assert _source(report, "first-page-slug")["status"] == "missing_selected_source"
    assert _source(report, "second-page-slug")["status"] == "missing_selected_source"
    assert _source(report, retained)["selected"] is False


def test_metadata_match_handles_grade_one_bukvar_and_combined_grade_volume(tmp_path: Path) -> None:
    root = tmp_path / "drive"
    root.mkdir()
    sources = [
        "1-klas-bukvar-bolshakova-2025-1",
        "10-11-klas-mystectvo-nazarenko-2018",
    ]
    for source in sources:
        (root / f"{source}.pdf").write_bytes(f"%PDF-{source}".encode())
        _write_jsonl(
            root / f"{source}.jsonl",
            [{"text": "one"}, {"text": "two"}, {"text": "three"}],
        )
    selection = tmp_path / "selection.yaml"
    selection.write_text(
        """books:
  - id: bukvar
    grade: 1
    subject: ukrainska_mova
    author: Большакова
    year: 2025
    slug: page-bukvar
  - id: art
    grade: 10
    subject: mystetstvo
    author: Назаренко
    year: 2018
    slug: page-art
""",
        encoding="utf-8",
    )
    db = tmp_path / "sources.db"
    _write_db(db, [(source, 3) for source in sources])

    report = readiness.build_report(
        gdrive_root=root,
        db_path=db,
        selection_path=selection,
    )

    assert _source(report, "page-bukvar")["status"] == "ready"
    assert _source(report, "page-art")["status"] == "ready"


def test_missing_url_map_is_tolerated_and_output_is_atomic_deterministic(tmp_path: Path) -> None:
    root = tmp_path / "drive"
    root.mkdir()
    (root / "book.pdf").write_bytes(b"%PDF-book")
    _write_jsonl(root / "book.jsonl", [{"text": "a"}, {"text": "b"}, {"text": "c"}])
    selection = tmp_path / "selection.yaml"
    _write_selection(selection, "book")
    db = tmp_path / "sources.db"
    _write_db(db, [("book", 3)])
    existing_map = tmp_path / "existing.yaml"
    existing_map.write_text("book: https://example.test/book\n", encoding="utf-8")
    missing_map = tmp_path / "missing.yaml"
    output = tmp_path / "receipts" / "readiness.json"
    output.parent.mkdir()
    output.write_text("old\n", encoding="utf-8")

    first = readiness.build_report(
        gdrive_root=root,
        db_path=db,
        selection_path=selection,
        url_maps=[existing_map, missing_map],
    )
    second = readiness.build_report(
        gdrive_root=root,
        db_path=db,
        selection_path=selection,
        url_maps=[existing_map, missing_map],
    )
    assert first == second
    readiness.write_atomic_json(output, first)
    assert json.loads(output.read_text(encoding="utf-8")) == first
    assert not list(output.parent.glob("*.tmp"))
    assert [item["present"] for item in first["url_maps"]] == [True, False]
    assert first["sources"][0]["acquisition_locators"] == [
        {"map_index": 0, "locator": "https://example.test/book"}
    ]
    assert str(tmp_path) not in output.read_text(encoding="utf-8")


def test_cli_writes_canonical_receipt(tmp_path: Path) -> None:
    root = tmp_path / "drive"
    root.mkdir()
    (root / "book.pdf").write_bytes(b"%PDF-book")
    _write_jsonl(root / "book.jsonl", [{"text": "one"}, {"text": "two"}, {"text": "three"}])
    selection = tmp_path / "selection.yaml"
    _write_selection(selection, "book")
    db = tmp_path / "sources.db"
    _write_db(db, [("book", 3)])
    output = tmp_path / "receipt.json"

    assert readiness.main(
        [
            "--gdrive-root",
            str(root),
            "--db",
            str(db),
            "--selection",
            str(selection),
            "--output",
            str(output),
        ]
    ) == 0
    assert output.read_text(encoding="utf-8").endswith("\n")
    assert json.loads(output.read_text(encoding="utf-8"))["schema_version"] == readiness.SCHEMA_VERSION


def test_missing_database_fails_closed_without_writing_a_receipt(tmp_path: Path) -> None:
    root = tmp_path / "drive"
    root.mkdir()
    selection = tmp_path / "selection.yaml"
    _write_selection(selection, "book")
    output = tmp_path / "receipt.json"

    with pytest.raises(readiness.ReadinessError, match="database_missing"):
        readiness.build_report(
            gdrive_root=root,
            db_path=tmp_path / "missing.db",
            selection_path=selection,
        )

    assert readiness.main(
        [
            "--gdrive-root",
            str(root),
            "--db",
            str(tmp_path / "missing.db"),
            "--selection",
            str(selection),
            "--output",
            str(output),
        ]
    ) == 2
    assert not output.exists()
