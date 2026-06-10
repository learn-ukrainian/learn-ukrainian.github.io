import json
import sqlite3

from scripts.lexicon.enrich_manifest import (
    _sense_correct_synonyms,
    clean_gloss,
    clean_html_entities,
)


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE wiktionary (
            word TEXT NOT NULL,
            definitions TEXT DEFAULT '',
            synonyms TEXT DEFAULT ''
        );
        CREATE TABLE ukrajinet (
            words TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE balla_en_uk (
            word TEXT NOT NULL,
            definition TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE sum11 (
            word TEXT NOT NULL,
            definition TEXT NOT NULL DEFAULT ''
        );
        """
    )
    return conn


def test_cleanup_helpers_strip_chunk_and_decode_entities() -> None:
    assert clean_gloss("Good morning — chunk, unstressed `[о]` stays clean") == "Good morning"
    assert clean_html_entities("20&amp;nbsp;Гц &amp;lt;br&amp;gt;") == "20 Гц <br>"


def test_synonyms_filter_polluted_wordnet_rows_to_a1_sense() -> None:
    conn = _conn()
    conn.execute(
        "INSERT INTO wiktionary VALUES (?, ?, ?)",
        ("кава", "[]", json.dumps(["кавове зерно", "кофе", "галка"], ensure_ascii=False)),
    )
    conn.executemany(
        "INSERT INTO ukrajinet VALUES (?, ?)",
        [
            (json.dumps(["Java", "кава"], ensure_ascii=False), "Синоніми: Java, кава"),
            (
                json.dumps(["Палена умбра", "Шоколад", "кава", "темно-коричневий"], ensure_ascii=False),
                "Синоніми: Палена умбра, Шоколад, кава, темно-коричневий",
            ),
            (
                json.dumps(["hot seat", "електричний стілець", "стілець", "стілець смерті"], ensure_ascii=False),
                "Синоніми: hot seat, електричний стілець, стілець, стілець смерті",
            ),
            (
                json.dumps(["toppingly", "дивовижний", "жахливо", "чудово"], ensure_ascii=False),
                "Синоніми: toppingly, дивовижний, жахливо, чудово",
            ),
            (
                json.dumps(["gorgeously", "splendidly", "блискуче", "чудово"], ensure_ascii=False),
                "Синоніми: gorgeously, splendidly, блискуче, чудово",
            ),
            (
                json.dumps(["Chrysanthemum morifolium", "Хризантема флористів", "мама"], ensure_ascii=False),
                "Синоніми: Chrysanthemum morifolium, Хризантема флористів, мама",
            ),
        ],
    )
    conn.executemany(
        "INSERT INTO balla_en_uk VALUES (?, ?, ?)",
        [
            ("mother", "мати, мама, матуся", "mother: мати, мама, матуся"),
            ("chair", "стілець; крісло", "chair: стілець; крісло"),
            ("house", "будинок, дім; хата; домівка", "house: будинок, дім; хата; домівка"),
            ("fine", "прекрасно", "fine: прекрасно"),
        ],
    )
    conn.execute("INSERT INTO sum11 VALUES (?, ?)", ("чудово", "Уживається як вияв похвали; прекрасно, чудесно."))

    assert _sense_correct_synonyms(conn, "кава") == []
    assert _sense_correct_synonyms(conn, "мама") == ["мати", "матуся"]
    assert _sense_correct_synonyms(conn, "стілець") == ["крісло"]
    assert _sense_correct_synonyms(conn, "дім") == ["будинок", "хата", "домівка"]
    assert _sense_correct_synonyms(conn, "чудово") == ["прекрасно", "чудесно", "блискуче"]

    all_synonyms = [
        synonym
        for lemma in ("кава", "мама", "стілець", "дім", "чудово")
        for synonym in _sense_correct_synonyms(conn, lemma)
    ]
    assert not any(any("A" <= char <= "Z" or "a" <= char <= "z" for char in synonym) for synonym in all_synonyms)
    assert "жахливо" not in all_synonyms
