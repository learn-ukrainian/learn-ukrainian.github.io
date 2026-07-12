from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from scripts.lexicon import generate_antonym_candidates as antonyms
from scripts.lexicon import mine_wikipedia_relations as wikipedia


def _vesum_db(path: Path, rows: list[tuple[str, str, str, str]]) -> Path:
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, tags TEXT, pos TEXT)")
    connection.executemany("INSERT INTO forms VALUES (?, ?, ?, ?)", rows)
    connection.commit()
    connection.close()
    return path


def test_wikipedia_parser_keeps_curated_pairs_and_glosses() -> None:
    text = """
== За лексичним значенням ==
* '''Синонімічні''': ''повідь'' — ''повінь''; ''крапля'' — ''капля''.
* ''земний'' («пов'язаний із землею») — ''земельний'' («пов'язаний із землекористуванням») — ''земляний''.
Звичайне речення: слово має значення — інше значення.
"""

    rows = wikipedia.parse_curated_pairs(text, default_relation="paronym")

    assert [(row["word_a"], row["word_b"], row["relation"]) for row in rows] == [
        ("повідь", "повінь", "synonym"),
        ("крапля", "капля", "synonym"),
        ("земний", "земельний", "paronym"),
        ("земельний", "земляний", "paronym"),
    ]
    assert rows[2]["gloss_a"] == "пов'язаний із землею"


def test_wikipedia_parser_accepts_same_form_homonyms_but_not_phrases() -> None:
    text = """
== Повні омоніми ==
* ''ключ'' (від замка) — ''ключ'' (джерело); стати ''по три'' — ''потри''.
"""

    rows = wikipedia.parse_curated_pairs(text, default_relation="homonym")

    assert [(row["word_a"], row["word_b"]) for row in rows] == [("ключ", "ключ")]


def test_wikipedia_mine_requires_exact_vesum_lemmas(tmp_path: Path, monkeypatch) -> None:
    db = _vesum_db(
        tmp_path / "vesum.db",
        [
            ("повідь", "повідь", "noun:m", "noun"),
            ("повінь", "повінь", "noun:f", "noun"),
            ("крапля", "крапля", "noun:f", "noun"),
            ("капля", "капля", "noun:f", "noun"),
        ],
    )

    monkeypatch.setattr(
        wikipedia,
        "fetch_article",
        lambda title: (title, "Синонім", "* ''повідь'' — ''повінь''; ''крапля'' — ''капля''; ''невідоме'' — ''слово''"),
    )
    monkeypatch.setattr(wikipedia, "ARTICLE_TITLES", ("Пароніми",))
    rows, report = wikipedia.mine(vesum_db=db)

    assert [(row["word_a"], row["word_b"]) for row in rows] == [("повідь", "повінь"), ("крапля", "капля")]
    assert report["articles"]["Пароніми"]["vesum_passed"] == 2


def test_morphological_generator_requires_base_and_same_pos(tmp_path: Path) -> None:
    db = _vesum_db(
        tmp_path / "vesum.db",
        [
            ("правда", "правда", "noun", "noun"),
            ("неправда", "неправда", "noun", "noun"),
            ("герой", "герой", "noun", "noun"),
            ("антигерой", "антигерой", "noun", "noun"),
            ("добрий", "добрий", "adj", "adj"),
            ("недобрий", "недобрий", "adj", "adj"),
            ("невірний", "невірний", "adj", "adj"),
            ("безпорадний", "безпорадний", "adj", "adj"),
            ("рідкісний", "рідкісний", "adj:rare", "adj"),
            ("нерідкісний", "нерідкісний", "adj", "adj"),
            ("неправда", "неправда", "verb", "verb"),
        ],
    )

    rows, summary = antonyms.generate(vesum_db=db)
    pairs = {(row["word_a"], row["word_b"], row["pos"]) for row in rows}

    assert ("правда", "неправда", "noun") in pairs
    assert ("герой", "антигерой", "noun") in pairs
    assert ("добрий", "недобрий", "adj") in pairs
    assert ("рідкісний", "нерідкісний", "adj") not in pairs
    assert ("порадний", "безпорадний", "adj") not in pairs
    assert summary["base_lemma_gate_dropped"] >= 2
    assert summary["candidate_count"] == len(rows)


def test_outputs_are_json_serializable(tmp_path: Path) -> None:
    db = _vesum_db(tmp_path / "vesum.db", [("добрий", "добрий", "adj", "adj")])
    rows, summary = antonyms.generate(vesum_db=db)
    json.dumps({"relations": rows, "summary": summary}, ensure_ascii=False)
