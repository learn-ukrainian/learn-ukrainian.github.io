import json
import sqlite3

from scripts.lexicon.enrich_manifest import (
    _build_paradigm,
    _idioms_slovnyk,
    _meaning,
    _merge_slovnyk_warning,
    _sense_correct_synonyms,
    _synonyms_slovnyk,
    _warning_slovnyk,
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
            definition TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            sovietization_risk INTEGER NOT NULL DEFAULT 0,
            sovietization_keywords TEXT NOT NULL DEFAULT ''
        );
        """
    )
    return conn


def test_cleanup_helpers_strip_chunk_and_decode_entities() -> None:
    assert clean_gloss("Good morning — chunk, unstressed `[о]` stays clean") == "Good morning"
    assert clean_html_entities("20&amp;nbsp;Гц &amp;lt;br&amp;gt;") == "20 Гц <br>"


def test_build_noun_paradigm_groups_cases_by_number() -> None:
    forms = [
        {"form": "вікну", "label": "сер., давальний"},
        {"form": "вікно", "label": "сер., кличний"},
        {"form": "вікні", "label": "сер., місцевий"},
        {"form": "вікну", "label": "сер., місцевий"},
        {"form": "вікно", "label": "сер., називний"},
        {"form": "вікном", "label": "сер., орудний"},
        {"form": "вікна", "label": "сер., родовий"},
        {"form": "вікно", "label": "сер., знахідний"},
        {"form": "вікнам", "label": "множина, давальний"},
        {"form": "вікна", "label": "множина, кличний"},
        {"form": "вікнах", "label": "множина, місцевий"},
        {"form": "вікна", "label": "множина, називний"},
        {"form": "вікнами", "label": "множина, орудний"},
        {"form": "вікон", "label": "множина, родовий"},
        {"form": "вікна", "label": "множина, знахідний"},
    ]

    paradigm = _build_paradigm("noun", forms)

    assert paradigm is not None
    assert paradigm["kind"] == "noun"
    cases = paradigm["cases"]
    assert list(cases) == [
        "називний",
        "родовий",
        "давальний",
        "знахідний",
        "орудний",
        "місцевий",
        "кличний",
    ]
    assert cases["називний"] == {"singular": "вікно", "plural": "вікна"}
    assert cases["родовий"] == {"singular": "вікна", "plural": "вікон"}
    assert cases["давальний"] == {"singular": "вікну", "plural": "вікнам"}
    assert cases["знахідний"] == {"singular": "вікно", "plural": "вікна"}
    assert cases["орудний"] == {"singular": "вікном", "plural": "вікнами"}
    assert cases["місцевий"] == {"singular": "вікні / вікну", "plural": "вікнах"}
    assert cases["кличний"] == {"singular": "вікно", "plural": "вікна"}


def test_build_verb_paradigm_collapses_variants() -> None:
    forms = [
        {"form": "навчатимемось", "label": "майбутній, множина, 1 ос."},
        {"form": "навчатимемося", "label": "майбутній, множина, 1 ос."},
        {"form": "навчатимемся", "label": "майбутній, множина, 1 ос."},
        {"form": "навчатиметесь", "label": "майбутній, множина, 2 ос."},
        {"form": "навчатиметеся", "label": "майбутній, множина, 2 ос."},
        {"form": "навчатимуться", "label": "майбутній, множина, 3 ос."},
        {"form": "навчатимусь", "label": "майбутній, однина, 1 ос."},
        {"form": "навчатимуся", "label": "майбутній, однина, 1 ос."},
        {"form": "навчатимешся", "label": "майбутній, однина, 2 ос."},
        {"form": "навчатиметься", "label": "майбутній, однина, 3 ос."},
        {"form": "навчаймось", "label": "наказовий, множина, 1 ос."},
        {"form": "навчаймося", "label": "наказовий, множина, 1 ос."},
        {"form": "навчайтесь", "label": "наказовий, множина, 2 ос."},
        {"form": "навчайтеся", "label": "наказовий, множина, 2 ос."},
        {"form": "навчайсь", "label": "наказовий, однина, 2 ос."},
        {"form": "навчайся", "label": "наказовий, однина, 2 ос."},
        {"form": "навчатися", "label": "інфінітив"},
        {"form": "навчатись", "label": "інфінітив"},
        {"form": "навчаться", "label": "інфінітив"},
        {"form": "навчалась", "label": "минулий, жін."},
        {"form": "навчалася", "label": "минулий, жін."},
        {"form": "навчавсь", "label": "минулий, чол."},
        {"form": "навчався", "label": "минулий, чол."},
        {"form": "навчалось", "label": "минулий, сер."},
        {"form": "навчалося", "label": "минулий, сер."},
        {"form": "навчались", "label": "минулий, множина"},
        {"form": "навчалися", "label": "минулий, множина"},
        {"form": "навчаємось", "label": "теперішній, множина, 1 ос."},
        {"form": "навчаємося", "label": "теперішній, множина, 1 ос."},
        {"form": "навчаємся", "label": "теперішній, множина, 1 ос."},
        {"form": "навчаєтесь", "label": "теперішній, множина, 2 ос."},
        {"form": "навчаєтеся", "label": "теперішній, множина, 2 ос."},
        {"form": "навчаються", "label": "теперішній, множина, 3 ос."},
        {"form": "навчаюсь", "label": "теперішній, однина, 1 ос."},
        {"form": "навчаюся", "label": "теперішній, однина, 1 ос."},
        {"form": "навчаєшся", "label": "теперішній, однина, 2 ос."},
        {"form": "навчається", "label": "теперішній, однина, 3 ос."},
    ]

    paradigm = _build_paradigm("verb", forms)

    assert paradigm is not None
    assert paradigm["kind"] == "verb"
    assert paradigm["infinitive"] == "навчатися / навчатись"
    assert "навчаться" not in paradigm["infinitive"]
    assert (
        paradigm["tenses"]["майбутній"]["множина"]["1"]
        == "навчатимемось / навчатимемося / навчатимемся"
    )
    assert (
        paradigm["tenses"]["теперішній"]["множина"]["1"]
        == "навчаємось / навчаємося / навчаємся"
    )
    assert paradigm["tenses"]["теперішній"]["однина"]["3"] == "навчається"
    assert paradigm["imperative"]["множина"]["1"] == "навчаймось / навчаймося"
    assert paradigm["imperative"]["однина"]["2"] == "навчайсь / навчайся"
    assert paradigm["past"]["чол."] == "навчавсь / навчався"
    assert paradigm["past"]["жін."] == "навчалась / навчалася"
    assert paradigm["past"]["сер."] == "навчалось / навчалося"
    assert paradigm["past"]["множина"] == "навчались / навчалися"


def test_build_paradigm_omits_unstructured_pos() -> None:
    assert _build_paradigm("adv", [{"form": "добре", "label": ""}]) is None


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
    conn.execute(
        "INSERT INTO sum11 (word, definition) VALUES (?, ?)",
        ("чудово", "Уживається як вияв похвали; прекрасно, чудесно."),
    )

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


def test_slovnyk_synonyms_extract_known_garnyi_word() -> None:
    cache = {
        "lookups": {
            "synonyms": {
                "dictionary_slug": "synonyms",
                "dictionary_label": "Словник синонімів української мови",
                "source_url": "https://slovnyk.me/dict/synonyms/гарний",
                "word": "гарний",
                "text": (
                    "гарний ГА́РНИЙ (про людину), КРАСИ́ВИЙ, "
                    "ВРОДЛИ́ВИЙ (УРОДЛИ́ВИЙ), ХОРО́ШИЙ. Джерело: тест"
                ),
            },
            "synonyms_karavansky": {
                "dictionary_slug": "synonyms_karavansky",
                "dictionary_label": "Словник синонімів Караванського",
                "source_url": "https://slovnyk.me/dict/synonyms_karavansky/гарний",
                "word": "гарний",
                "text": "гарний Не поганий; (- вроду) вродливий, гожий, хороший. Джерело: тест",
            },
        }
    }

    section = _synonyms_slovnyk("гарний", cache)

    assert section is not None
    assert "красивий" in section["items"]
    assert "вродливий" in section["items"]
    assert "хороший" in section["items"]
    assert "гарний" not in section["items"]
    assert section["source"].startswith("slovnyk.me:")


def test_slovnyk_idioms_extract_known_phrase_card() -> None:
    cache = {
        "lookups": {
            "phraseology": {
                "dictionary_slug": "phraseology",
                "dictionary_label": "Фразеологічний словник української мови",
                "source_url": "https://slovnyk.me/dict/phraseology/яблуко",
                "word": "яблуко",
                "text": (
                    "яблуко я́блуко ро́збрату (чвар), книжн. "
                    "Причина ворожнечі, суперечок, незгод між ким-небудь. Джерело: тест"
                ),
            }
        }
    }

    section = _idioms_slovnyk("яблуко", cache)

    assert section is not None
    assert section["items"][0]["phrase"] == "яблуко розбрату (чвар), книжн"
    assert "Причина ворожнечі" in section["items"][0]["definition"]


def test_slovnyk_warning_merges_known_russianism_alternative() -> None:
    cache = {
        "lookups": {
            "davydov": {
                "dictionary_slug": "davydov",
                "dictionary_label": "«Як ми говоримо» Антоненка-Давидовича",
                "source_url": "https://slovnyk.me/dict/davydov/міроприємство",
                "word": "міроприємство",
                "text": (
                    "міроприємство Міроприємство — захід, заходи "
                    "Такого слова не було й нема в українській мові. Джерело: тест"
                ),
            }
        }
    }

    warning = _warning_slovnyk("міроприємство", cache)
    status = _merge_slovnyk_warning(
        {
            "classification": "unknown",
            "attestations": [],
            "is_russianism": False,
            "russian_shadow": False,
            "sovietization_risk": 0,
            "calque_warning": None,
        },
        warning,
    )

    assert warning is not None
    assert warning["alternatives"] == ["захід", "заходи"]
    assert status["classification"] == "russianism"
    assert status["is_russianism"] is True
    assert any(
        attestation["source"] == "standard_alternative" and attestation["ref"] == "захід"
        for attestation in status["attestations"]
    )


def test_sum11_meaning_carries_source_sovietization_risk() -> None:
    conn = _conn()
    conn.execute(
        """
        INSERT INTO sum11
            (word, definition, text, sovietization_risk, sovietization_keywords)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "ленінізм",
            "Учення В. І. Леніна, що являє собою розвиток марксизму.",
            "",
            2,
            "ленін,маркс",
        ),
    )

    meaning = _meaning(conn, "ленінізм")

    assert meaning is not None
    assert meaning["source"] == "СУМ-11"
    assert meaning["sovietization_risk"] == 2
    assert meaning["sovietization_keywords"] == ["ленін", "маркс"]
