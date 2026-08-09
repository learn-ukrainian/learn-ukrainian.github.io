from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from scripts.practice_deck.zno import (
    LEXICAL_NORM_SQL,
    MORPHOLOGICAL_NORM_SQL,
    ORTHOGRAPHY_LIVE_CANDIDATE_COUNT,
    ORTHOGRAPHY_SQL,
    SYNTACTIC_NORM_SQL,
    build_zno_shards,
    learner_attribution,
    write_zno_shards,
)


def _database(path: Path) -> Path:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE zno_documents (id INTEGER PRIMARY KEY, fetch_status TEXT NOT NULL);
        CREATE TABLE zno_tasks (
            id INTEGER PRIMARY KEY, document_id INTEGER, year INTEGER, exam TEXT, session TEXT,
            task_no INTEGER, task_format TEXT, stem TEXT, options_json TEXT, correct_json TEXT,
            topic_tag TEXT, topic_norm TEXT, task_subtype TEXT, paronym_pair TEXT
        );
        INSERT INTO zno_documents VALUES (1, 'ok'), (2, 'dead');
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
    ]
    connection.executemany("INSERT INTO zno_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
    connection.commit()
    connection.close()
    return path


def test_builder_keeps_ukrainian_item_text_maps_letter_and_reports_drops(tmp_path: Path) -> None:
    shards, residual = build_zno_shards(_database(tmp_path / "sources.db"))

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


def test_lexical_predicate_is_explicit_and_output_is_deterministic(tmp_path: Path) -> None:
    database = _database(tmp_path / "sources.db")
    assert "trim(t.topic_norm) = 'lexical_norm'" in LEXICAL_NORM_SQL
    first, first_residual = build_zno_shards(database)
    second, second_residual = build_zno_shards(database)
    assert first == second
    assert first_residual == second_residual

    output = tmp_path / "out"
    write_zno_shards(first, first_residual, output)
    assert json.loads((output / "practice-zno.paronym.json").read_text(encoding="utf-8"))["thinDeck"] is True


def test_orthography_membership_is_pinned_and_malformed_candidates_drop(tmp_path: Path) -> None:
    shards, residual = build_zno_shards(_database(tmp_path / "sources.db"))

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
    shards, residual = build_zno_shards(_database(tmp_path / "sources.db"))

    assert "trim(t.topic_norm) = 'morphological_norm'" in MORPHOLOGICAL_NORM_SQL
    assert "trim(t.topic_norm) = 'syntactic_norm'" in SYNTACTIC_NORM_SQL
    assert shards["morphological-norm"]["deckId"] == "zno-morphological-norm"
    assert shards["morphological-norm"]["items"][0]["stem"] == "Морфологія?"
    assert shards["syntactic-norm"]["deckId"] == "zno-syntactic-norm"
    assert shards["syntactic-norm"]["items"][0]["stem"] == "Синтаксис?"
    assert residual["decks"]["morphological-norm"]["candidates"] == 1
    assert residual["decks"]["syntactic-norm"]["candidates"] == 1


def test_attribution_uses_ucyoo_and_never_a_mirror() -> None:
    assert learner_attribution(year=2024, exam="nmt", session="sesiya-2", task_no=7) == (
        "Джерело: УЦОЯО · НМТ 2024, сесія 2 · завдання №7"
    )
