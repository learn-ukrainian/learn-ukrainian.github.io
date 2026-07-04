from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.audit import atlas_source_census
from scripts.audit import atlas_source_entry_count as entry_count
from scripts.audit.source_inventory_intake import SourceInventoryError


def test_vesum_backed_lane_counts_existing_and_backlog_without_form_aliases(tmp_path: Path) -> None:
    module_dir = tmp_path / "curriculum" / "l2-uk-en" / "a1" / "demo"
    module_dir.mkdir(parents=True)
    (module_dir / "module.md").write_text("Коти бачать замки.", encoding="utf-8")
    manifest_path = _write_manifest(
        tmp_path,
        [
            _entry("кіт", entry_type="lemma"),
            _entry("коти", form_of={"lemma": "кіт", "url_slug": "кіт"}),
        ],
    )

    result = entry_count.build_source_entry_count(
        root=tmp_path,
        manifest_path=manifest_path,
        include_committed_inventories=False,
        textbook_txt_root=None,
        sources_db_path=None,
        textbook_jsonl_root=None,
        vesum_lookup=_fake_vesum,
    ).public_payload

    reviewed = result["reviewed_atlas"]
    lane = result["source_lanes"][atlas_source_census.MODULE_CONTENT]

    assert reviewed["total_reviewed_entries"] == 1
    assert reviewed["non_entry_records"]["form_alias"] == 1
    assert lane["existing_reviewed_by_bucket"]["lemma"] == 1
    assert lane["estimated_backlog_by_bucket"]["lemma"] == 2
    assert lane["classification_methods"]["manifest_entry_type"] == 1
    assert lane["classification_methods"]["vesum_backed_lemma"] == 2
    public_json = json.dumps(result, ensure_ascii=False)
    assert "Коти бачать" not in public_json
    assert "замок" not in public_json
    assert "кіт" not in public_json


def test_explicit_multiword_headwords_use_reviewed_bucket_or_needs_review(tmp_path: Path) -> None:
    module_dir = tmp_path / "curriculum" / "l2-uk-en" / "a1" / "demo"
    module_dir.mkdir(parents=True)
    (module_dir / "vocabulary.yaml").write_text(
        yaml.safe_dump(
            [
                {"word": "будь ласка", "translation": "please"},
                {"word": "доконаний вид", "translation": "perfective aspect"},
                {"word": "зелена книга", "translation": "green book"},
            ],
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    manifest_path = _write_manifest(
        tmp_path,
        [
            _entry("будь ласка", entry_type="expression"),
            _entry("доконаний вид", entry_type="multiword_term"),
        ],
    )

    result = entry_count.build_source_entry_count(
        root=tmp_path,
        manifest_path=manifest_path,
        include_committed_inventories=False,
        textbook_txt_root=None,
        sources_db_path=None,
        textbook_jsonl_root=None,
        vesum_lookup=_fake_vesum,
    ).public_payload

    lane = result["source_lanes"][atlas_source_census.MODULE_VOCABULARY]

    assert lane["existing_reviewed_by_bucket"]["expression"] == 1
    assert lane["existing_reviewed_by_bucket"]["multiword_term"] == 1
    assert lane["estimated_backlog_by_bucket"]["needs_review"] == 1
    assert lane["classification_methods"]["heuristic_multiword_needs_review"] == 1


def test_committed_inventory_lanes_cover_source_families_and_proper_names(tmp_path: Path) -> None:
    inventory = tmp_path / "inventory.yaml"
    inventory.write_text(
        """
version: 1
kind: atlas_source_inventory
sources:
  - id: teacher-safe
    source_family: teacher_lesson
    extraction_mode: curated_headword
    title: Safe committed inventory
    headwords:
      - lemma: Київ
        pos: proper_noun
        gloss: Kyiv
  - id: textbook-safe
    source_family: textbook
    extraction_mode: headword_inventory
    title: Safe committed inventory
    headwords:
      - lemma: школа
        pos: noun
        gloss: school
""".lstrip(),
        encoding="utf-8",
    )

    result = entry_count.build_source_entry_count(
        root=tmp_path,
        manifest_path=_write_manifest(tmp_path, []),
        include_modules=False,
        inventory_paths=(inventory,),
        textbook_txt_root=None,
        sources_db_path=None,
        textbook_jsonl_root=None,
        vesum_lookup=_fake_vesum,
    ).public_payload

    assert result["source_inputs"]["committed_source_inventories"]["by_family"] == {
        "teacher_lesson": {"deduped_candidates": 1, "records": 1, "source_units": 1},
        "textbook": {"deduped_candidates": 1, "records": 1, "source_units": 1},
    }
    assert result["source_lanes"]["committed_inventory_teacher_lesson"]["estimated_backlog_by_bucket"][
        "proper_name"
    ] == 1
    assert result["source_lanes"]["committed_inventory_textbook"]["estimated_backlog_by_bucket"]["lemma"] == 1
    public_json = json.dumps(result, ensure_ascii=False)
    assert "Safe committed inventory" not in public_json
    assert "Київ" not in public_json


def test_private_ohoiko_public_payload_is_aggregate_only(tmp_path: Path) -> None:
    private_root = tmp_path / "private-ohoiko-root"
    private_root.mkdir()
    (private_root / "secret-note.md").write_text("Секретний уривок має слова.", encoding="utf-8")

    result = entry_count.build_source_entry_count(
        root=tmp_path,
        manifest_path=_write_manifest(tmp_path, []),
        include_modules=False,
        include_committed_inventories=False,
        include_ohoiko_private=True,
        ohoiko_private_roots=(private_root,),
        textbook_txt_root=None,
        sources_db_path=None,
        textbook_jsonl_root=None,
        vesum_lookup=_fake_vesum,
    ).public_payload

    lane = result["source_lanes"][atlas_source_census.OHOIKO_PRIVATE]
    assert lane["source_units"] == 1
    assert lane["unique_surface_forms"] == 4
    public_json = json.dumps(result, ensure_ascii=False)
    assert "secret-note" not in public_json
    assert "private-ohoiko-root" not in public_json
    assert "Секретний уривок" not in public_json
    assert "секретний" not in public_json


def test_textbook_sqlite_and_jsonl_grade_counts_are_aggregate_only(tmp_path: Path) -> None:
    db_path = tmp_path / "sources.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "create table textbooks (grade text, text text, source_file text, char_count integer)"
        )
        conn.execute(
            "insert into textbooks values (?, ?, ?, ?)",
            ("1", "Мами читають книгу.", "private-source-a.pdf", 20),
        )

    jsonl_root = tmp_path / "chunks" / "grade-02"
    jsonl_root.mkdir(parents=True)
    (jsonl_root / "book.jsonl").write_text(
        json.dumps({"grade": 2, "text": "Школи мають класи.", "chunk_id": "private-chunk"}, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )

    result = entry_count.build_source_entry_count(
        root=tmp_path,
        manifest_path=_write_manifest(tmp_path, []),
        include_modules=False,
        include_committed_inventories=False,
        textbook_txt_root=None,
        sources_db_path=db_path,
        textbook_jsonl_root=tmp_path / "chunks",
        vesum_lookup=_fake_vesum,
    ).public_payload

    sqlite_grade = result["textbook_grades_by_lane"][atlas_source_census.TEXTBOOK_DB]["grade-01"]
    jsonl_grade = result["textbook_grades_by_lane"][atlas_source_census.TEXTBOOK_JSONL]["grade-02"]

    assert sqlite_grade["source_units"] == 1
    assert sqlite_grade["estimated_backlog_by_bucket"]["lemma"] == 3
    assert jsonl_grade["source_units"] == 1
    assert jsonl_grade["estimated_backlog_by_bucket"]["lemma"] == 3
    public_json = json.dumps(result, ensure_ascii=False)
    assert "private-source-a.pdf" not in public_json
    assert "private-chunk" not in public_json
    assert "book.jsonl" not in public_json
    assert "Мами читають" not in public_json


def test_detail_output_path_must_be_outside_repo(tmp_path: Path) -> None:
    with pytest.raises(SourceInventoryError, match="outside the repository"):
        entry_count.resolve_local_detail_output_path(tmp_path / "details.json", project_root=tmp_path)

    outside = tmp_path.parent / "atlas-source-entry-count-details.json"
    assert entry_count.resolve_local_detail_output_path(outside, project_root=tmp_path) == outside.resolve()


def _entry(lemma: str, **overrides: object) -> dict[str, object]:
    entry: dict[str, object] = {
        "lemma": lemma,
        "url_slug": lemma.replace(" ", "-"),
        "gloss": "fixture",
        "pos": "noun",
        "primary_source": "test",
        "course_usage": [],
    }
    entry.update(overrides)
    return entry


def _write_manifest(tmp_path: Path, entries: list[dict[str, object]]) -> Path:
    manifest_path = tmp_path / "lexicon-manifest.json"
    manifest_path.write_text(json.dumps({"entries": entries}, ensure_ascii=False), encoding="utf-8")
    return manifest_path


def _fake_vesum(words: list[str]) -> dict[str, list[dict[str, Any]]]:
    matches = {
        "бачать": [{"lemma": "бачити", "pos": "verb", "tags": "verb"}],
        "будь": [{"lemma": "бути", "pos": "verb", "tags": "verb"}],
        "вид": [{"lemma": "вид", "pos": "noun", "tags": "noun"}],
        "доконаний": [{"lemma": "доконаний", "pos": "adj", "tags": "adj"}],
        "зелена": [{"lemma": "зелений", "pos": "adj", "tags": "adj"}],
        "замки": [{"lemma": "замок", "pos": "noun", "tags": "noun"}],
        "книга": [{"lemma": "книга", "pos": "noun", "tags": "noun"}],
        "класи": [{"lemma": "клас", "pos": "noun", "tags": "noun"}],
        "книгу": [{"lemma": "книга", "pos": "noun", "tags": "noun"}],
        "коти": [{"lemma": "кіт", "pos": "noun", "tags": "noun"}],
        "ласка": [{"lemma": "ласка", "pos": "noun", "tags": "noun"}],
        "мають": [{"lemma": "мати", "pos": "verb", "tags": "verb"}],
        "мами": [{"lemma": "мама", "pos": "noun", "tags": "noun"}],
        "читають": [{"lemma": "читати", "pos": "verb", "tags": "verb"}],
        "слова": [{"lemma": "слово", "pos": "noun", "tags": "noun"}],
        "секретний": [{"lemma": "секретний", "pos": "adj", "tags": "adj"}],
        "уривок": [{"lemma": "уривок", "pos": "noun", "tags": "noun"}],
        "школи": [{"lemma": "школа", "pos": "noun", "tags": "noun"}],
    }
    return {word: matches.get(word, []) for word in words}
