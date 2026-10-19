from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.practice_deck.markup_integrity import stem_requires_markup
from scripts.practice_deck.zno import (
    LEXICAL_NORM_LIVE_CANDIDATE_COUNT,
    LEXICAL_NORM_SQL,
    MORPHOLOGICAL_NORM_SQL,
    MORPHOLOGY_LIVE_CANDIDATE_COUNT,
    MORPHOLOGY_SQL,
    ORTHOGRAPHY_LIVE_CANDIDATE_COUNT,
    ORTHOGRAPHY_SQL,
    PARONYM_LIVE_CANDIDATE_COUNT,
    PHONETICS_SQL,
    SYNTACTIC_NORM_SQL,
    SYNTAX_SQL,
    build_zno_shards,
    learner_attribution,
    write_zno_fill_residual,
    write_zno_shards,
)


def _database(path: Path) -> Path:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE zno_documents (
            id INTEGER PRIMARY KEY, fetch_status TEXT NOT NULL, year INTEGER NOT NULL, text_layer TEXT NOT NULL
        );
        CREATE TABLE zno_tasks (
            id INTEGER PRIMARY KEY, document_id INTEGER, year INTEGER, exam TEXT, session TEXT,
            task_no INTEGER, task_format TEXT, stem TEXT, options_json TEXT, correct_json TEXT,
            topic_tag TEXT, topic_norm TEXT, task_subtype TEXT, paronym_pair TEXT
        );
        INSERT INTO zno_documents VALUES (1, 'ok', 2021, 'garbled'), (2, 'dead', 2010, 'clean');
        """
    )
    rows = [
        (1, 1, 2021, "zno", "osnovna", 2, "single-choice", " Наголос?\n", '[" а ", "б", "в", "г", "ґ"]', "Б", "ТЕМА: Наголос", "", "", ""),
        (2, 1, 2024, "nmt", "sesiya-1", 3, "single-choice", "Паронім?", '["а", "б", "в", "г", "ґ"]', "Д", "", "", "paronym", ""),
        (3, 1, 2021, "zno", "osnovna", 4, "single-choice", "Лексика?", '["а", "б", "в", "г", "ґ"]', "А", "", "lexical_norm", "word_choice", ""),
        (4, 1, 2021, "zno", "osnovna", 5, "single-choice", "Зламані варіанти", '["а", "а"]', "А", "ТЕМА: Наголос", "", "", ""),
        (5, 1, 2021, "zno", "osnovna", 6, "own-statement", "Власна відповідь", '[]', "", "", "", "", ""),
        (6, 1, 2021, "zno", "osnovna", 7, "single-choice", "Орфографія?", '["а", "б", "в", "г", "ґ"]', "Г", "ТЕМА: Орфографія. Апостроф", "", "", ""),
        (7, 1, 2021, "zno", "osnovna", 8, "single-choice", "Зламані варіанти", '["а", "а"]', "А", "ТЕМА: Орфографія. Апостроф", "", "", ""),
        (8, 1, 2021, "zno", "osnovna", 9, "single-choice", "Морфологія?", '["а", "б", "в", "г", "ґ"]', "В", "ТЕМА: Морфологія", "morphological_norm", "", ""),
        (9, 1, 2021, "zno", "osnovna", 10, "single-choice", "Синтаксис?", '["а", "б", "в", "г", "ґ"]', "Д", "ТЕМА: Синтаксис", "syntactic_norm", "", ""),
        (10, 1, 2021, "zno", "osnovna", 11, "single-choice", "Морфологія без норми?", '["а", "б", "в", "г", "ґ"]', "А", "ТЕМА: Морфологія. Іменник", "", "", ""),
        (11, 1, 2021, "zno", "osnovna", 12, "single-choice", "Синтаксис. Розділові знаки?", '["а", "б", "в", "г", "ґ"]', "Б", "ТЕМА: Синтаксис. Розділові знаки в реченні", "", "", ""),
        (12, 1, 2021, "zno", "osnovna", 13, "single-choice", "Фонетика?", '["а", "б", "в", "г", "ґ"]', "В", "ТЕМА: Фонетика", "", "", ""),
        (
            13,
            1,
            2024,
            "nmt",
            "sesiya-2",
            1,
            "single-choice",
            "Однаковий звук позначають букви, виділені в кожному слові рядка",
            '["бігти, поріг, злегка", "повість, сяйво, свічка", "лічба, почасти, чітко", "кістці, тім\'я, житній"]',
            "Б",
            "ТЕМА: Фонетика. Зміни звуків",
            "",
            "",
            "",
        ),
    ]
    connection.executemany("INSERT INTO zno_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
    connection.commit()
    connection.close()
    return path


def test_builder_keeps_ukrainian_item_text_maps_letter_and_reports_drops(tmp_path: Path) -> None:
    shards, residual, fill_residual = build_zno_shards(_database(tmp_path / "sources.db"))

    stress = shards["stress"]
    assert stress["items"][0]["stem"] == " Наголос?\n"
    assert stress["items"][0]["options"][0] == " а "
    assert stress["items"][0]["correctLetter"] == "Б"
    assert stress["items"][0]["correctIndex"] == 1
    assert stress["items"][0]["znoMode"] == "choice"
    assert stress["items"][0]["znoTaskId"] == "zno:1"
    assert stress["items"][0]["attribution"] == "Джерело: УЦОЯО · ЗНО 2021, основна сесія · завдання №2"
    assert residual["decks"]["stress"]["candidates"] == 2
    assert residual["decks"]["stress"]["emitted"] == 1
    assert residual["decks"]["stress"]["dropped"] == {"invalid_options": 1}
    assert residual["namedResidual"]["emptyKeyOwnStatement"] == 1
    assert residual["namedResidual"]["documentsFetchNotOk"] == 1
    assert residual["namedResidual"]["garbledPdfDocuments"] == 1
    assert residual["namedResidual"]["excluded2009"] == 1
    assert fill_residual["schema"] == "zno-practice-fill-residual"
    assert fill_residual["deckDrops"]["stress"][0]["reason"] == "invalid_options"


def test_lexical_predicate_is_explicit_and_output_is_deterministic(tmp_path: Path) -> None:
    database = _database(tmp_path / "sources.db")
    assert "trim(t.topic_norm) = 'lexical_norm'" in LEXICAL_NORM_SQL
    assert "trim(t.task_subtype) = 'lexical_error'" in LEXICAL_NORM_SQL
    first, first_residual, first_fill = build_zno_shards(database)
    second, second_residual, second_fill = build_zno_shards(database)
    assert first == second
    assert first_residual == second_residual
    assert first_fill == second_fill

    output = tmp_path / "out"
    write_zno_shards(first, first_residual, output)
    write_zno_fill_residual(first_fill, output / "zno-fill-residual.json")
    assert json.loads((output / "practice-zno.paronym.json").read_text(encoding="utf-8"))["thinDeck"] is True
    assert json.loads((output / "zno-fill-residual.json").read_text(encoding="utf-8"))["inventory"]["stress"]["emitted"] == 1


def test_orthography_membership_is_pinned_and_malformed_candidates_drop(tmp_path: Path) -> None:
    shards, residual, _fill = build_zno_shards(_database(tmp_path / "sources.db"))

    assert "instr(t.topic_tag, 'Орфограф') > 0" in ORTHOGRAPHY_SQL
    # This frozen live denominator makes an intentional source-corpus or predicate
    # change visible in review before the generated shard is refreshed.
    assert ORTHOGRAPHY_LIVE_CANDIDATE_COUNT == 168
    assert residual["decks"]["orthography"]["candidates"] == 2
    assert residual["decks"]["orthography"]["emitted"] == 1
    assert residual["decks"]["orthography"]["dropped"] == {"invalid_options": 1}
    assert shards["orthography"]["deckId"] == "zno-orthography"
    assert shards["orthography"]["items"][0]["stem"] == "Орфографія?"


def test_morphological_and_syntactic_norm_decks_use_exact_topic_norm_predicates(tmp_path: Path) -> None:
    shards, residual, _fill = build_zno_shards(_database(tmp_path / "sources.db"))

    assert "trim(t.topic_norm) = 'morphological_norm'" in MORPHOLOGICAL_NORM_SQL
    assert "trim(t.topic_norm) = 'syntactic_norm'" in SYNTACTIC_NORM_SQL
    assert shards["morphological-norm"]["deckId"] == "zno-morphological-norm"
    assert shards["morphological-norm"]["items"][0]["stem"] == "Морфологія?"
    assert shards["syntactic-norm"]["deckId"] == "zno-syntactic-norm"
    assert shards["syntactic-norm"]["items"][0]["stem"] == "Синтаксис?"
    assert residual["decks"]["morphological-norm"]["candidates"] == 1
    assert residual["decks"]["syntactic-norm"]["candidates"] == 1


def test_wave_3_decks_emit_from_broad_topic_tag_families(tmp_path: Path) -> None:
    """#6620: morphology/syntax/phonetics were untapped topic_tag families sitting
    behind the four thin/repetitive original decks; this pins their predicates and
    proves each emits real, letter-valid items when candidates exist."""
    shards, residual, _fill = build_zno_shards(_database(tmp_path / "sources.db"))

    assert "instr(t.topic_tag, 'Морфолог') > 0" in MORPHOLOGY_SQL
    assert "instr(t.topic_tag, 'Словотвір') > 0" in MORPHOLOGY_SQL
    assert "instr(t.topic_tag, 'Синтаксис') > 0" in SYNTAX_SQL
    assert "instr(t.topic_tag, 'Фонетик') > 0" in PHONETICS_SQL
    assert MORPHOLOGY_LIVE_CANDIDATE_COUNT == 195
    assert LEXICAL_NORM_LIVE_CANDIDATE_COUNT == 40
    assert PARONYM_LIVE_CANDIDATE_COUNT == 7

    assert shards["morphology"]["deckId"] == "zno-morphology"
    assert residual["decks"]["morphology"]["candidates"] == 2
    assert residual["decks"]["morphology"]["emitted"] == 2

    assert shards["syntax"]["deckId"] == "zno-syntax"
    assert residual["decks"]["syntax"]["candidates"] == 2
    assert residual["decks"]["syntax"]["emitted"] == 2

    assert shards["phonetics"]["deckId"] == "zno-phonetics"
    assert residual["decks"]["phonetics"]["candidates"] == 2
    assert residual["decks"]["phonetics"]["emitted"] == 1
    assert residual["decks"]["phonetics"]["dropped"] == {"broken_missing_markup": 1}
    assert shards["phonetics"]["items"][0]["stem"] == "Фонетика?"


def test_attribution_uses_ucyoo_and_never_a_mirror() -> None:
    assert learner_attribution(year=2024, exam="nmt", session="sesiya-2", task_no=7) == (
        "Джерело: УЦОЯО · НМТ 2024, сесія 2 · завдання №7"
    )


def test_builder_quarantines_markup_dependent_items_without_overlay(tmp_path: Path) -> None:
    database = _database(tmp_path / "sources.db")
    empty_overlay = tmp_path / "empty-overlay.json"
    empty_overlay.write_text('{"schema":"zno-markup-overlay","schemaVersion":1,"items":{}}', encoding="utf-8")

    shards, residual, _fill = build_zno_shards(database, markup_overlay_path=empty_overlay)

    assert residual["markupIntegrity"]["quarantinedMissingMarkup"] == 1
    assert residual["decks"]["phonetics"]["dropped"]["broken_missing_markup"] == 1
    assert all(item["znoTaskId"] != "zno:13" for item in shards["phonetics"]["items"])
    assert stem_requires_markup(
        "Однаковий звук позначають букви, виділені в кожному слові рядка",
    )


@pytest.mark.parametrize(
    ("spec", "expected", "occurrences", "withheld"),
    [
        ([], (0, 0, 0), 0, []),
        ([("single", 11)], (1, 1, 0), 1, []),
        ([("overlap", 11)], (1, 1, 0), 2, []),
        ([("overlap", 11), ("duplicate", 12), ("quarantine", 13)], (3, 1, 2), 2, [12, 13]),
        ([("duplicate", 12), ("quarantine", 13)], (2, 0, 2), 0, [12, 13]),
        ([("unmatched", 14), ("nonchoice", 15)], (2, 0, 2), 0, [14, 15]),
    ],
    ids=["empty", "single", "overlap", "mixed", "zero", "nonserved"],
)
def test_cli_aggregate_counts_unique_source_tasks(
    tmp_path: Path,
    spec: list[tuple[str, int]],
    expected: tuple[int, int, int],
    occurrences: int,
    withheld: list[int],
) -> None:
    database = _database(tmp_path / "sources.db")
    with sqlite3.connect(database) as connection:
        template = list(connection.execute("SELECT * FROM zno_tasks WHERE id = 8").fetchone())
        markup_row = connection.execute("SELECT * FROM zno_tasks WHERE id = 13").fetchone()
        connection.execute("DELETE FROM zno_tasks")
        for kind, task_id in spec:
            row = template.copy()
            row[0] = task_id
            row[7:10] = ["plain synthetic fixture", json.dumps(["alpha", "beta", "gamma"]), "А"]
            if kind == "single":
                row[10:12] = ["", "lexical_norm"]
            if kind == "duplicate":
                row[8] = json.dumps(["alpha", "alpha", "beta"])
            if kind == "quarantine":
                row[7:9] = markup_row[7:9]
            if kind in ("unmatched", "nonchoice"):
                row[10:12] = ["", ""]
            if kind == "nonchoice":
                row[6], row[9] = "own-statement", ""
            connection.execute("INSERT INTO zno_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", row)

    output = tmp_path / "out"
    fill_path = tmp_path / "fill.json"
    result = subprocess.run(
        [
            sys.executable, "-m", "scripts.practice_deck.zno",
            "--db", str(database), "--out-dir", str(output),
            "--fill-residual", str(fill_path), "--markup-overlay", str(tmp_path / "missing-overlay.json"),
        ],
        capture_output=True, text=True, check=False, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    residual = json.loads((output / "practice-zno.residual.json").read_bytes())
    assert tuple(residual["namedResidual"][key] for key in ("corpusTasks", "emittedItems", "intentionalCut")) == expected
    emitted_ids = [
        item["znoTaskId"]
        for path in output.glob("practice-zno.*.json")
        for item in json.loads(path.read_bytes()).get("items", [])
    ]
    assert len(emitted_ids) == occurrences
    assert set(emitted_ids) == ({"zno:11"} if occurrences else set())
    assert {task_id for _, task_id in spec} - {int(value.split(":")[1]) for value in emitted_ids} == set(withheld)
    for deck in residual["decks"].values():
        assert deck["candidates"] == deck["emitted"] + sum(deck["dropped"].values())

    if expected == (3, 1, 2):
        for key in ("morphological-norm", "morphology"):
            deck = residual["decks"][key]
            assert deck["candidates"] == 3
            assert deck["emitted"] == 1
            assert deck["dropped"] == {"invalid_options": 1, "broken_missing_markup": 1}
        fill = json.loads(fill_path.read_bytes())
        assert fill["blocked"] == [
            {"deck": key, "znoTaskId": task_id, "reason": reason}
            for key in ("morphological-norm", "morphology")
            for task_id, reason in (("zno:12", "invalid_options"), ("zno:13", "broken_missing_markup"))
        ]
        assert fill["unparsed"] == [{"znoTaskId": "zno:12", "reason": "invalid_options"}]
        # Existing quarantine classification remains unresolved under #10701.
        assert fill["predicateMissByTopicNorm"] == {"morphological_norm": 1}
