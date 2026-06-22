from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from scripts.readings.clean_text_resolver import (
    load_work_index,
    main,
    resolve_clean_text,
)


def test_public_domain_work_in_corpus_is_hostable(tmp_path: Path) -> None:
    db_path = _write_sources_db(tmp_path)
    index = load_work_index(db_path)

    result = resolve_clean_text("Заповіт", "Шевченко Т.", index, current_year=2026)

    assert result["in_corpus"] is True
    assert result["hostable_full"] is True
    assert result["rights_class"] == "public_domain"
    assert result["clean_text_source"] == {
        "source_file": "ukrlib-shevchenko",
        "chunk_ids": [1],
        "full_text_chars": len(ZAPOVIT_TEXT),
    }
    assert result["free_full_text_link"] is None


def test_author_embedded_work_title_matches_clean_demand(tmp_path: Path) -> None:
    db_path = _write_sources_db(tmp_path)
    index = load_work_index(db_path)

    result = resolve_clean_text("Заповіт", "Шевченко Т.", index, current_year=2026)

    assert result["in_corpus"] is True
    assert result["corpus_match"] in {"exact", "substring"}
    assert result["matched_work"] == "Заповіт"


def test_in_copyright_work_in_corpus_emits_unverified_link(tmp_path: Path) -> None:
    db_path = _write_sources_db(tmp_path)
    index = load_work_index(db_path)

    # A modern, non-persecuted author on a non-free source — the only in-copyright case.
    result = resolve_clean_text("Нічний вірш", "Сучасна Авторка", index, current_year=2026)

    assert result["in_corpus"] is True
    assert result["hostable_full"] is False
    assert result["rights_class"] == "in_copyright"
    assert result["clean_text_source"] is None
    link = result["free_full_text_link"]
    assert link is not None
    assert link["url"] == "https://example.test/suchasna-avtorka-nichnyi-virsh"
    assert link["source"] == "corpus_source_url"
    assert link["verified"] is False


def test_not_in_corpus_emits_unverified_candidate_link(tmp_path: Path) -> None:
    db_path = _write_sources_db(tmp_path)
    index = load_work_index(db_path)

    result = resolve_clean_text(
        "Ця назва не існує в корпусі",
        "Ніхто",
        index,
        current_year=2026,
    )

    assert result["in_corpus"] is False
    assert result["corpus_match"] is None
    assert result["hostable_full"] is False
    assert result["clean_text_source"] is None
    link = result["free_full_text_link"]
    assert link is not None
    assert link["source"] == "ukrlib_candidate"
    assert link["verified"] is False


def test_multi_chunk_assembly_orders_chunk_ids_and_counts_text(tmp_path: Path) -> None:
    db_path = _write_sources_db(tmp_path)
    index = load_work_index(db_path)

    result = resolve_clean_text("Лісова пісня", "Леся Українка", index)

    assert result["in_corpus"] is True
    assert result["chunk_ids"] == [1, 2, 3]
    assert result["full_text_chars"] == len(LISOVA_1 + LISOVA_2 + LISOVA_3)
    assert result["clean_text_source"] is not None
    assert result["clean_text_source"]["chunk_ids"] == [1, 2, 3]


def test_cli_work_author_prints_valid_json(tmp_path: Path, capsys) -> None:
    db_path = _write_sources_db(tmp_path)

    exit_code = main(
        [
            "--db",
            str(db_path),
            "--work",
            "Заповіт",
            "--author",
            "Шевченко Т.",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["in_corpus"] is True
    assert payload["hostable_full"] is True
    assert payload["free_full_text_link"] is None


def test_cli_manifest_writes_summary_with_expected_keys(tmp_path: Path) -> None:
    db_path = _write_sources_db(tmp_path)
    plans_dir = _write_plan_fixture(tmp_path)
    out_path = tmp_path / "primary_text_clean_resolution.json"

    exit_code = main(
        [
            "--manifest",
            "--db",
            str(db_path),
            "--plans-dir",
            str(plans_dir),
            "--out",
            str(out_path),
        ]
    )

    assert exit_code == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["summary"] == {
        "total_works": 2,
        "in_corpus_count": 1,
        "hostable_full_count": 1,
        "needs_link_count": 1,
    }
    assert sorted(payload["summary"]) == [
        "hostable_full_count",
        "in_corpus_count",
        "needs_link_count",
        "total_works",
    ]
    assert len(payload["entries"]) == 2


ZAPOVIT_TEXT = "Як умру, то поховайте мене на могилі."
# A genuinely in-copyright work: a modern, non-persecuted author whose text carries NO
# free-source signal (not on ukrlib / not in the textbook corpus). This is the only case
# that resolves in_copyright → excerpt + unverified free-full-text link.
MODERN_INCOPYRIGHT_TEXT = "Сучасний вірш, рядок за рядком."
LISOVA_1 = "Лісова пісня початок. "
LISOVA_2 = "Лісова пісня середина. "
LISOVA_3 = "Лісова пісня кінець."


def _write_sources_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "sources.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE literary_texts (
              id INTEGER,
              chunk_id INTEGER,
              title TEXT,
              text TEXT,
              source_file TEXT,
              author TEXT,
              work TEXT,
              work_id TEXT,
              year INTEGER,
              genre TEXT,
              language_period TEXT,
              char_count INTEGER,
              source_url TEXT
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO literary_texts (
              id,
              chunk_id,
              title,
              text,
              source_file,
              author,
              work,
              work_id,
              year,
              genre,
              language_period,
              char_count,
              source_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    1,
                    1,
                    "Заповіт",
                    ZAPOVIT_TEXT,
                    "ukrlib-shevchenko",
                    "Шевченко Т.",
                    "Тарас Шевченко. Заповіт",
                    "shevchenko-zapovit",
                    1845,
                    "poetry",
                    "modern",
                    len(ZAPOVIT_TEXT),
                    None,
                ),
                (
                    2,
                    1,
                    "Нічний вірш",
                    MODERN_INCOPYRIGHT_TEXT,
                    "suchasna-zbirka-2019",
                    "Сучасна Авторка",
                    "Сучасна Авторка. Нічний вірш",
                    "suchasna-avtorka-nichnyi-virsh",
                    2015,
                    "poetry",
                    "modern",
                    len(MODERN_INCOPYRIGHT_TEXT),
                    "https://example.test/suchasna-avtorka-nichnyi-virsh",
                ),
                (
                    5,
                    3,
                    "Лісова пісня",
                    LISOVA_3,
                    "ukrlib-ukrainka",
                    "Леся Українка",
                    "Лісова пісня",
                    "lisova-pisnia",
                    1911,
                    "drama",
                    "modern",
                    len(LISOVA_3),
                    None,
                ),
                (
                    3,
                    1,
                    "Лісова пісня",
                    LISOVA_1,
                    "ukrlib-ukrainka",
                    "Леся Українка",
                    "Лісова пісня",
                    "lisova-pisnia",
                    1911,
                    "drama",
                    "modern",
                    len(LISOVA_1),
                    None,
                ),
                (
                    4,
                    2,
                    "Лісова пісня",
                    LISOVA_2,
                    "ukrlib-ukrainka",
                    "Леся Українка",
                    "Лісова пісня",
                    "lisova-pisnia",
                    1911,
                    "drama",
                    "modern",
                    len(LISOVA_2),
                    None,
                ),
            ],
        )
    return db_path


def _write_plan_fixture(tmp_path: Path) -> Path:
    plans_dir = tmp_path / "plans"
    (plans_dir / "lit").mkdir(parents=True)
    (plans_dir / "lit" / "primary-texts.yaml").write_text(
        """
grade: LIT
references:
  - title: Заповіт
    author: Шевченко Т.
    type: primary
  - title: Ця назва не існує в корпусі
    author: Ніхто
    type: primary
""",
        encoding="utf-8",
    )
    return plans_dir
