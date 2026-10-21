from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.audit import atlas_source_census as census
from scripts.audit.source_inventory_intake import SourceInventoryError

pytestmark = pytest.mark.reads_content


def test_textbook_sqlite_and_jsonl_lanes_are_aggregate_only(tmp_path: Path) -> None:
    db_path = tmp_path / "sources.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "create table textbooks (grade text, text text, source_file text, char_count integer)"
        )
        conn.executemany(
            "insert into textbooks values (?, ?, ?, ?)",
            [
                ("1", "Мама читає книжку.", "source-a.pdf", 18),
                ("2", "Тато пише лист.", "source-b.pdf", 15),
            ],
        )
    jsonl_root = tmp_path / "textbook_chunks" / "grade-01"
    jsonl_root.mkdir(parents=True)
    (jsonl_root / "book.jsonl").write_text(
        json.dumps({"grade": 1, "text": "Мама малює.", "chunk_id": "private-id"}, ensure_ascii=False)
        + "\nnot-json\n",
        encoding="utf-8",
    )

    result = census.build_atlas_source_census(
        root=tmp_path,
        manifest_path=_write_manifest(tmp_path, []),
        include_modules=False,
        include_default_inventories=False,
        textbook_txt_root=None,
        textbook_pdf_root=None,
        sources_db_path=db_path,
        textbook_jsonl_root=tmp_path / "textbook_chunks",
    )
    payload = census.public_census_payload(result)

    assert payload["source_inputs"][census.TEXTBOOK_DB]["chunks_scanned"] == 2
    assert payload["source_inputs"][census.TEXTBOOK_DB]["source_files"] == 2
    assert payload["source_inputs"][census.TEXTBOOK_JSONL]["jsonl_files_scanned"] == 1
    assert payload["source_inputs"][census.TEXTBOOK_JSONL]["chunks_scanned"] == 1
    assert payload["source_inputs"][census.TEXTBOOK_JSONL]["malformed_rows"] == 1
    assert payload["textbook_surfaces_by_grade"][census.TEXTBOOK_DB]["grade-01"]["source_units"] == 1
    assert payload["textbook_surfaces_by_grade"][census.TEXTBOOK_DB]["grade-02"]["source_units"] == 1
    assert payload["textbook_surfaces_by_grade"][census.TEXTBOOK_JSONL]["grade-01"]["source_units"] == 1
    public_json = json.dumps(payload, ensure_ascii=False)
    assert "Мама читає" not in public_json
    assert "source-a.pdf" not in public_json
    assert "private-id" not in public_json
    assert "book.jsonl" not in public_json


def test_detail_output_path_must_be_outside_repo(tmp_path: Path) -> None:
    with pytest.raises(SourceInventoryError, match="outside the repository"):
        census.resolve_local_detail_output_path(tmp_path / "details.json", project_root=tmp_path)

    outside = tmp_path.parent / "atlas-census-details.json"
    assert census.resolve_local_detail_output_path(outside, project_root=tmp_path) == outside.resolve()


def _write_manifest(tmp_path: Path, lemmas: list[str]) -> Path:
    manifest_path = tmp_path / "lexicon-manifest.json"
    manifest_path.write_text(
        json.dumps({"entries": [{"lemma": lemma} for lemma in lemmas]}, ensure_ascii=False),
        encoding="utf-8",
    )
    return manifest_path
