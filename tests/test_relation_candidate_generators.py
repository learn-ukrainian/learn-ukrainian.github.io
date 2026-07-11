from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from scripts.lexicon.generate_antonym_candidates import generate as generate_antonyms
from scripts.lexicon.generate_paronym_candidates import generate as generate_paronyms
from scripts.lexicon.mine_wikipedia_relations import (
    _gated_rows,
    _headword_pairs,
    _wiktionary_pairs,
)
from scripts.lexicon.relation_candidate_common import (
    VesumIndex,
    iter_edit_pairs,
    load_artifact,
    merge_rows,
    write_artifact,
)


def _vesum_db(path: Path, rows: list[tuple[str, str, str]]) -> Path:
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE forms (word_form TEXT NOT NULL, lemma TEXT NOT NULL, tags TEXT NOT NULL, pos TEXT NOT NULL)")
    conn.executemany("INSERT INTO forms VALUES (?, ?, ?, ?)", rows)
    conn.commit()
    conn.close()
    return path


def _frequency_json(path: Path, words: list[str], value: int = 5) -> Path:
    path.write_text(json.dumps({word: value for word in words}, ensure_ascii=False), encoding="utf-8")
    return path


def test_paronym_generator_applies_same_pos_frequency_and_seed_gates(tmp_path: Path) -> None:
    db = _vesum_db(
        tmp_path / "vesum.db",
        [
            ("адресант", "адресант", "noun:anim:m:v_naz", "noun"),
            ("адресат", "адресат", "noun:anim:m:v_naz", "noun"),
            ("адресанти", "адресант", "noun:anim:p:v_naz", "noun"),
            ("адресати", "адресат", "noun:anim:p:v_naz", "noun"),
            ("адресанта", "адресант", "noun:anim:m:v_rod", "noun"),
        ],
    )
    sources = tmp_path / "sources.db"
    conn = sqlite3.connect(sources)
    conn.execute("CREATE TABLE zno_tasks (task_subtype TEXT, paronym_pair TEXT)")
    conn.execute("CREATE TABLE paronyms_cache (word_a TEXT, word_b TEXT)")
    conn.execute("INSERT INTO paronyms_cache VALUES ('адресант', 'адресат')")
    conn.commit()
    conn.close()
    frequency = _frequency_json(tmp_path / "frequency.json", ["адресант", "адресат"])

    rows, summary = generate_paronyms(
        vesum_db=db,
        sources_db=sources,
        corpus_db=None,
        frequency_json=frequency,
        min_frequency=2,
    )

    assert [(row["word_a"], row["word_b"], row["pos"]) for row in rows] == [("адресант", "адресат", "noun")]
    assert rows[0]["confidence"] == "medium"
    assert rows[0]["gate"] == {
        "vesum_exact_lemma": True,
        "same_pos": True,
        "not_inflectional_variant": True,
        "frequency_floor": True,
        "not_orthographic_variant": True,
        "confusable_stem_or_seed": True,
    }
    assert summary["edit_distance_distribution"] == {"1": 1, "2": 0}


def test_paronym_generator_rejects_missing_frequency_and_inflection_variant(tmp_path: Path) -> None:
    db = _vesum_db(
        tmp_path / "vesum.db",
        [
            ("книга", "книга", "noun:f:v_naz", "noun"),
            ("книги", "книга", "noun:p:v_naz", "noun"),
            ("книжа", "книжа", "noun:f:v_naz", "noun"),
        ],
    )
    rows, summary = generate_paronyms(
        vesum_db=db,
        sources_db=tmp_path / "missing-sources.db",
        corpus_db=None,
        frequency_json=None,
    )
    assert rows == []
    assert summary["frequency_source"] == "none"


def test_antonym_generator_requires_both_exact_lemmas_and_flags_rare_forms(tmp_path: Path) -> None:
    db = _vesum_db(
        tmp_path / "vesum.db",
        [
            ("можливий", "можливий", "adj:m:v_naz", "adj"),
            ("неможливий", "неможливий", "adj:m:v_naz", "adj"),
            ("нехтувати", "нехтувати", "verb:inf", "verb"),
        ],
    )
    frequency = _frequency_json(tmp_path / "frequency.json", ["можливий"], 5)
    rows, summary = generate_antonyms(
        vesum_db=db,
        corpus_db=None,
        frequency_json=frequency,
    )
    assert len(rows) == 1
    assert rows[0]["word"] == "можливий"
    assert rows[0]["antonym"] == "неможливий"
    assert rows[0]["affix"] == "не-"
    assert rows[0]["confidence"] == "low"
    assert summary["affix_distribution"]["не-"] == 1


def test_wikipedia_parser_preserves_gloss_and_cross_tags(tmp_path: Path) -> None:
    db = _vesum_db(
        tmp_path / "vesum.db",
        [
            ("ефектний", "ефектний", "adj:m:v_naz", "adj"),
            ("ефективний", "ефективний", "adj:m:v_naz", "adj"),
            ("прогрес", "прогрес", "noun:m:v_naz", "noun"),
            ("регрес", "регрес", "noun:m:v_naz", "noun"),
        ],
    )
    text = """'''Пароніми'''\n\n* '''Антонімічні''': прогрес — регрес;\n* ефектний («вражаючий») — ефективний («з позитивними наслідками»)."""
    raw = _headword_pairs(text)
    with VesumIndex(db) as vesum:  # type: ignore[attr-defined]
        rows, _ = _gated_rows(
            raw,
            default_relation="paronym",
            source="uk.wikipedia",
            source_url="https://uk.wikipedia.org/wiki/Пароніми",
            article="Пароніми",
            vesum=vesum,
            confidence="high",
        )
    assert {row["word_a"] for row in rows} == {"ефектний", "прогрес"}
    antonym = next(row for row in rows if row["word_a"] == "прогрес")
    assert antonym["relation"] == "antonym"
    assert "uk.wikipedia.org" in antonym["source_url"]
    assert next(row for row in rows if row["word_a"] == "ефектний")["distinction"] == "вражаючий"


def test_wiktionary_relation_sections_map_to_relation_names() -> None:
    raw = _wiktionary_pairs(
        "ефектний",
        """=== Синоніми ===\n* [[ефектний]]: [[видовищний]]\n=== Антоніми ===\n* [[неефектний]]""",
    )
    assert ("ефектний", "видовищний", "synonym", "ефектний: видовищний") in raw
    assert ("ефектний", "неефектний", "antonym", "неефектний") in raw


def test_relation_artifact_is_stable_and_deduplicated(tmp_path: Path) -> None:
    path = tmp_path / "relations.json"
    payload = load_artifact(path)
    row = {"relation": "antonym", "word": "можливий", "antonym": "неможливий", "source": "test"}
    assert merge_rows(payload, "antonyms", [row, row]) == 1
    write_artifact(payload, path)
    assert json.loads(path.read_text(encoding="utf-8"))["relations"]["antonyms"] == [row]


def test_edit_neighbour_index_covers_substitution_and_insertion() -> None:
    pairs = {(first, second, distance) for first, second, _pos, distance in iter_edit_pairs({"книга": {"noun"}, "книги": {"noun"}, "краса": {"noun"}})}
    assert ("книга", "книги", 1) in pairs
    assert not any(first == "книга" and second == "краса" for first, second, _distance in pairs)
