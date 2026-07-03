from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
import yaml

from scripts.audit import atlas_source_census as census
from scripts.audit.source_inventory_intake import SourceInventoryError


def test_module_census_separates_content_activities_and_vocabulary(tmp_path: Path) -> None:
    module_dir = tmp_path / "curriculum" / "l2-uk-en" / "a1" / "demo"
    module_dir.mkdir(parents=True)
    (module_dir / "module.md").write_text("# Заголовок\n\nКоти читають урок.", encoding="utf-8")
    (module_dir / "activities.yaml").write_text(
        yaml.safe_dump(
            {"inline": [{"id": "act-1", "instruction": "Мами пишуть слова."}]},
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (module_dir / "vocabulary.yaml").write_text(
        yaml.safe_dump(
            [{"word": "кіт", "translation": "cat", "example": "Кіт читає."}],
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    manifest = _write_manifest(tmp_path, ["кіт"])

    result = census.build_atlas_source_census(
        root=tmp_path,
        manifest_path=manifest,
        include_default_inventories=False,
        textbook_txt_root=None,
        textbook_pdf_root=None,
        sources_db_path=None,
    )
    payload = census.public_census_payload(result)

    assert payload["source_inputs"]["modules"] == {
        "l2_uk_en_module_md": 1,
        "l2_uk_en_activity_yaml": 1,
        "l2_uk_en_vocabulary_yaml": 1,
        "l2_uk_direct_module_yaml": 0,
    }
    assert payload["surfaces"][census.MODULE_CONTENT]["source_units"] == 1
    assert payload["surfaces"][census.MODULE_ACTIVITY]["source_units"] == 1
    assert payload["surfaces"][census.MODULE_VOCABULARY]["explicit_headwords"] == 1
    assert payload["surfaces"][census.MODULE_VOCABULARY]["explicit_in_atlas"] == 1
    assert payload["surfaces"][census.MODULE_ALL]["source_units"] == 3
    assert payload["modules_by_track"]["a1"]["source_units"] == 3
    public_json = json.dumps(payload, ensure_ascii=False)
    assert "Коти читають" not in public_json
    assert "кіт" not in public_json


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


def test_textbook_grade_parser_accepts_zero_padded_names() -> None:
    assert census._textbook_grade(Path("textbook_chunks/grade-01/chunks.jsonl")) == "grade-01"
    assert census._textbook_grade(Path("texts/02-klas-book.txt")) == "grade-02"


def _write_manifest(tmp_path: Path, lemmas: list[str]) -> Path:
    manifest_path = tmp_path / "lexicon-manifest.json"
    manifest_path.write_text(
        json.dumps({"entries": [{"lemma": lemma} for lemma in lemmas]}, ensure_ascii=False),
        encoding="utf-8",
    )
    return manifest_path
