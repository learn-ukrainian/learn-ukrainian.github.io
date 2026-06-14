import json
import sqlite3

import pytest

from scripts.lexicon import enrich_manifest as enrich_manifest_module
from scripts.lexicon.enrich_manifest import (
    _WRONG_SENSE_SYNONYMS,
    KAIKKI_SOURCE,
    _base_lemma,
    _build_paradigm,
    _cefr,
    _clean_synonym_candidate,
    _curated_calque,
    _definition_cards,
    _dmklinger_key,
    _etymology,
    _idioms_slovnyk,
    _kaikki_pronunciation,
    _literary_attestation,
    _literary_excerpt,
    _meaning,
    _merge_slovnyk_warning,
    _morphology,
    _sense_correct_synonyms,
    _slovnyk_cache,
    _SlovnykTransientError,
    _synonyms_slovnyk,
    _translation,
    _warning_slovnyk,
    clean_gloss,
    clean_html_entities,
)


def _patch_vesum_analyses(monkeypatch, pos_by_word: dict[str, str]) -> None:
    def fake_analyses(word: str) -> tuple[tuple[str, str], ...]:
        pos = pos_by_word.get(word)
        return ((word, pos),) if pos else ()

    monkeypatch.setattr(enrich_manifest_module, "_vesum_word_analyses", fake_analyses)


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
        CREATE TABLE grinchenko (
            word TEXT NOT NULL,
            definition TEXT NOT NULL DEFAULT '',
            source TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE puls_cefr (
            word TEXT NOT NULL,
            guideword TEXT DEFAULT '',
            level TEXT DEFAULT '',
            pos TEXT DEFAULT '',
            type TEXT DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            source TEXT DEFAULT ''
        );
        CREATE TABLE literary_texts (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            source_file TEXT NOT NULL DEFAULT '',
            source_url TEXT DEFAULT '',
            author TEXT DEFAULT '',
            work TEXT DEFAULT '',
            work_id TEXT DEFAULT '',
            year INTEGER,
            genre TEXT DEFAULT '',
            language_period TEXT DEFAULT '',
            char_count INTEGER DEFAULT 0
        );
        CREATE VIRTUAL TABLE literary_fts USING fts5(
            title,
            text,
            content='literary_texts',
            content_rowid='id',
            tokenize='unicode61'
        );
        """
    )
    return conn


def test_cleanup_helpers_strip_chunk_and_decode_entities() -> None:
    assert clean_gloss("Good morning — chunk, unstressed `[о]` stays clean") == "Good morning"
    assert clean_html_entities("20&amp;nbsp;Гц &amp;lt;br&amp;gt;") == "20 Гц <br>"


def test_base_lemma_splits_pairs_without_lowercasing_non_pairs() -> None:
    non_pair = " Київ "

    assert _base_lemma("варити / зварити") == "варити"
    assert _base_lemma("Київ") == "Київ"
    assert _base_lemma(non_pair) == non_pair


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


def test_morphology_can_use_base_form_from_pair_lemma(monkeypatch) -> None:
    calls: list[str] = []

    def fake_verify_lemma(lemma: str) -> list[dict[str, str]]:
        calls.append(lemma)
        if lemma != "варити":
            return []
        return [
            {"word_form": "варити", "tags": "verb:inf", "pos": "verb"},
            {"word_form": "варю", "tags": "verb:pres:s:1", "pos": "verb"},
        ]

    monkeypatch.setattr(enrich_manifest_module, "verify_lemma", fake_verify_lemma)
    monkeypatch.setattr(enrich_manifest_module, "_stress_display_form", lambda form: "")

    morphology = _morphology(_base_lemma("варити / зварити"))

    assert calls == ["варити"]
    assert morphology is not None
    assert morphology["pos"] == "дієслово"
    assert morphology["forms"][0] == {"form": "варити", "label": "інфінітив"}


def test_legacy_synonym_sources_drop_wordnet_and_ukrajinet_noise() -> None:
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
    assert _sense_correct_synonyms(conn, "чудово") == ["прекрасно", "чудесно"]

    all_synonyms = [
        synonym
        for lemma in ("кава", "мама", "стілець", "дім", "чудово")
        for synonym in _sense_correct_synonyms(conn, lemma)
    ]
    assert not any(any("A" <= char <= "Z" or "a" <= char <= "z" for char in synonym) for synonym in all_synonyms)
    assert "жахливо" not in all_synonyms
    assert "блискуче" not in all_synonyms


def test_slovnyk_synonyms_extract_known_garnyi_word(monkeypatch) -> None:
    _patch_vesum_analyses(
        monkeypatch,
        {
            "гарний": "adj",
            "красивий": "adj",
            "вродливий": "adj",
            "хороший": "adj",
            "гожий": "adj",
        },
    )
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


def test_slovnyk_synonyms_omit_wrong_sense_voda(monkeypatch) -> None:
    _patch_vesum_analyses(
        monkeypatch,
        {
            "вода": "noun",
            "багатослів'я": "noun",
            "велемовність": "noun",
            "пиття": "noun",
            "напій": "noun",
        },
    )
    cache = {
        "lookups": {
            "synonyms": {
                "dictionary_slug": "synonyms",
                "dictionary_label": "Словник синонімів української мови",
                "source_url": "https://slovnyk.me/dict/synonyms/вода",
                "word": "вода",
                "text": (
                    "вода БАГАТОСЛІВ'Я (уживання без потреби великої кількості слів), "
                    "ВЕЛЕМОВНІСТЬ; ВОДА розм. Джерело: тест"
                ),
            },
            "synonyms_karavansky": {
                "dictionary_slug": "synonyms_karavansky",
                "dictionary_label": "Словник синонімів Караванського",
                "source_url": "https://slovnyk.me/dict/synonyms_karavansky/вода",
                "word": "вода",
                "text": "вода (газована) пиття, напій; П. багатослів'я. Джерело: тест",
            },
        }
    }

    section = _synonyms_slovnyk("вода", cache, entry_pos="noun")

    items = section["items"] if section else []
    assert "багатослів'я" not in items
    assert "велемовність" not in items


def test_wrong_sense_synonym_excluded_per_lemma_not_globally() -> None:
    # #3116: кам'яниця (stone building, Грінченко) and звір (ravine/beast) are
    # authentic words the Karavansky synset over-includes for шлях/річка. They are
    # dropped for THAT lemma only — never globally — so a stoplist that would
    # repeat the блискучий heritage error is avoided.
    assert _clean_synonym_candidate("кам'яниця", "шлях") is None
    assert _clean_synonym_candidate("звір", "річка") is None
    # valid same-sense synonyms survive
    assert _clean_synonym_candidate("дорога", "шлях") == "дорога"
    assert _clean_synonym_candidate("струмок", "річка") == "струмок"
    # NOT a global block: кам'яниця stays valid as a synonym of a different lemma
    assert _clean_synonym_candidate("кам'яниця", "будинок") == "кам'яниця"


def test_wrong_sense_synonyms_are_authentic_not_russianisms() -> None:
    # Contract guard: every excluded term is per-lemma sense-scoped, never a
    # blanket entry. Keys are base lemmas; the excluded words must NOT leak into
    # the global _BLOCKED_SYNONYMS stoplist (they are valid Ukrainian).
    blocked = enrich_manifest_module._BLOCKED_SYNONYMS
    for lemma, excluded in _WRONG_SENSE_SYNONYMS.items():
        assert lemma == lemma.casefold(), f"key {lemma!r} must be casefolded"
        assert excluded, f"{lemma} must list at least one excluded term"
        for term in excluded:
            assert term not in blocked, f"{term} is valid Ukrainian — must not be globally blocked"


def test_slovnyk_synonyms_promote_clean_sources_for_sample(monkeypatch) -> None:
    _patch_vesum_analyses(
        monkeypatch,
        {
            "варити": "verb",
            "готувати": "verb",
            "куховарити": "verb",
            "фальсифікувати": "verb",
            "хата": "noun",
            "домівка": "noun",
            "господа": "noun",
            "притулок": "noun",
            "житло": "noun",
            "оселя": "noun",
            "помешкання": "noun",
            "дім": "noun",
            "бариги": "noun",
            "шлях": "noun",
            "дорога": "noun",
            "маршрут": "noun",
            "курс": "noun",
            "путь": "noun",
            "тракт": "noun",
            "мрія": "noun",
            "марення": "noun",
            "бажання": "noun",
            "прагнення": "noun",
            "надія": "noun",
        },
    )
    samples = {
        "варити / зварити": (
            "verb",
            {
                "lookups": {
                    "synonyms": {
                        "dictionary_slug": "synonyms",
                        "dictionary_label": "Словник синонімів української мови",
                        "source_url": "https://slovnyk.me/dict/synonyms/варити",
                        "word": "варити",
                        "text": "варити ВАРИТИ (про їжу), ГОТУВАТИ, КУХОВАРИТИ. — Док.: зварити. Джерело: тест",
                    }
                }
            },
            ["готувати", "куховарити"],
        ),
        "хата": (
            "noun",
            {
                "lookups": {
                    "synonyms_karavansky": {
                        "dictionary_slug": "synonyms_karavansky",
                        "dictionary_label": "Словник синонімів Караванського",
                        "source_url": "https://slovnyk.me/dict/synonyms_karavansky/хата",
                        "word": "хата",
                        "text": "хата домівка, господа, притулок; П. бариги. Джерело: тест",
                    },
                    "synonyms": {
                        "dictionary_slug": "synonyms",
                        "dictionary_label": "Словник синонімів української мови",
                        "source_url": "https://slovnyk.me/dict/synonyms/хата",
                        "word": "хата",
                        "text": "хата ЖИТЛО, ОСЕЛЯ, ПОМЕШКАННЯ, ДІМ, ДОМІВКА, ХАТА. Джерело: тест",
                    },
                }
            },
            ["домівка", "господа", "притулок", "житло", "оселя", "помешкання", "дім"],
        ),
        "шлях": (
            "noun",
            {
                "lookups": {
                    "synonyms_karavansky": {
                        "dictionary_slug": "synonyms_karavansky",
                        "dictionary_label": "Словник синонімів Караванського",
                        "source_url": "https://slovnyk.me/dict/synonyms_karavansky/шлях",
                        "word": "шлях",
                        "text": "шлях ДОРОГА, маршрут, курс; П. спосіб. Джерело: тест",
                    },
                    "synonyms": {
                        "dictionary_slug": "synonyms",
                        "dictionary_label": "Словник синонімів української мови",
                        "source_url": "https://slovnyk.me/dict/synonyms/шлях",
                        "word": "шлях",
                        "text": "шлях ДОРОГА (смуга землі), ШЛЯХ, ПУТЬ, ТРАКТ. Джерело: тест",
                    },
                }
            },
            ["дорога", "маршрут", "курс", "путь", "тракт"],
        ),
        "мрія": (
            "noun",
            {
                "lookups": {
                    "synonyms_karavansky": {
                        "dictionary_slug": "synonyms_karavansky",
                        "dictionary_label": "Словник синонімів Караванського",
                        "source_url": "https://slovnyk.me/dict/synonyms_karavansky/мрія",
                        "word": "мрія",
                        "text": "мрія МАРЕННЯ, бажання, прагнення; П. ілюзія. Джерело: тест",
                    },
                    "synonyms": {
                        "dictionary_slug": "synonyms",
                        "dictionary_label": "Словник синонімів української мови",
                        "source_url": "https://slovnyk.me/dict/synonyms/мрія",
                        "word": "мрія",
                        "text": "мрія БАЖАННЯ (те, чого хочеться), МРІЯ, ПРАГНЕННЯ, НАДІЯ. Джерело: тест",
                    },
                }
            },
            ["марення", "бажання", "прагнення", "надія"],
        ),
    }

    for lemma, (entry_pos, cache, expected) in samples.items():
        section = _synonyms_slovnyk(lemma, cache, entry_pos=entry_pos)

        assert section is not None
        assert section["items"] == expected
        assert not {"фальсифікувати", "бариги", "java", "hot seat"}.intersection(section["items"])


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
    assert section["items"][0]["text"] == "яблуко розбрату (чвар), книжн"
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


def test_curated_calque_matches_participle_entry() -> None:
    card = _curated_calque("діючий", "діючий")

    assert card == {
        "kind": "participle",
        "corrections": ["чинний"],
        "note": "діючий закон → чинний закон (рос. действующий)",
        "source": ["glazova-11", "avramenko-11"],
    }


def test_curated_calque_matches_sense_restricted_entry_with_both_senses() -> None:
    card = _curated_calque("виглядати", "виглядати")

    assert card is not None
    assert card["kind"] == "sense_restricted"
    assert card["corrections"] == ["здаватися", "видаватися"]
    assert card["calque_sense"] == "to seem / appear that (рос. выглядит = 'it seems')"
    assert card["authentic_sense"] == "to look (well/ill); to peer out (гарно виглядати; виглядати у вікно)"
    assert "calque only when" in card["note"]
    assert card["source"] == ["grinchenko", "sum-20", "grok-3098"]


def test_curated_calque_matches_phrasal_entry() -> None:
    card = _curated_calque("точка зору", "точка")

    assert card == {
        "kind": "phrasal",
        "corrections": ["погляд"],
        "note": "рос. точка зрения; цієї точки зору → цього погляду",
        "source": ["ua-gec", "grok-3098"],
    }


def test_curated_calque_unknown_lemma_returns_none() -> None:
    assert _curated_calque("яблуко", "яблуко") is None


def test_curated_calque_lexicalised_safe_lemma_returns_none() -> None:
    assert _curated_calque("блискучий", "блискучий") is None


def test_fetch_slovnyk_entry_raises_transient_for_5xx(monkeypatch) -> None:
    class FakeResponse:
        status_code = 503
        text = ""

        def raise_for_status(self) -> None:
            raise AssertionError("5xx should be classified before raise_for_status")

    monkeypatch.setattr(enrich_manifest_module, "_polite_slovnyk_delay", lambda: None)
    monkeypatch.setattr(enrich_manifest_module.requests, "get", lambda *args, **kwargs: FakeResponse())

    with pytest.raises(_SlovnykTransientError):
        enrich_manifest_module._fetch_slovnyk_entry("тест", "тест", "newsum")


def test_fetch_slovnyk_entry_raises_transient_for_connection_error(monkeypatch) -> None:
    def fake_get(*args, **kwargs):
        raise enrich_manifest_module.requests.ConnectionError("connection timed out")

    monkeypatch.setattr(enrich_manifest_module, "_polite_slovnyk_delay", lambda: None)
    monkeypatch.setattr(enrich_manifest_module.requests, "get", fake_get)

    with pytest.raises(_SlovnykTransientError):
        enrich_manifest_module._fetch_slovnyk_entry("тест", "тест", "newsum")


def test_slovnyk_cache_keeps_transient_slug_absent_and_refetches(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(enrich_manifest_module, "SLOVNYK_CACHE", tmp_path)
    monkeypatch.setattr(enrich_manifest_module, "_SLOVNYK_LOOKUP_SLUGS", ("newsum", "synonyms"))

    calls: list[str] = []

    def fake_fetch(lemma: str, lookup_word: str, slug: str) -> dict[str, str]:
        calls.append(slug)
        if slug == "synonyms" and calls.count("synonyms") == 1:
            raise _SlovnykTransientError("timeout")
        return {"dictionary_slug": slug, "text": f"{lookup_word}:{slug}"}

    monkeypatch.setattr(enrich_manifest_module, "_fetch_slovnyk_entry", fake_fetch)

    first = _slovnyk_cache("тест")
    cache_path = enrich_manifest_module._slovnyk_cache_path("тест")
    persisted = json.loads(cache_path.read_text(encoding="utf-8"))

    assert first["lookups"]["newsum"]["text"] == "тест:newsum"
    assert "synonyms" not in first["lookups"]
    assert "synonyms" not in persisted["lookups"]

    second = _slovnyk_cache("тест")

    assert calls == ["newsum", "synonyms", "synonyms"]
    assert second["lookups"]["synonyms"]["text"] == "тест:synonyms"


def test_slovnyk_cache_persists_genuine_none_miss_without_refetch(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(enrich_manifest_module, "SLOVNYK_CACHE", tmp_path)
    monkeypatch.setattr(enrich_manifest_module, "_SLOVNYK_LOOKUP_SLUGS", ("newsum",))

    calls: list[str] = []

    def fake_fetch(lemma: str, lookup_word: str, slug: str) -> None:
        calls.append(slug)
        return None

    monkeypatch.setattr(enrich_manifest_module, "_fetch_slovnyk_entry", fake_fetch)

    first = _slovnyk_cache("немає")
    persisted = json.loads(enrich_manifest_module._slovnyk_cache_path("немає").read_text(encoding="utf-8"))

    assert first["lookups"]["newsum"] is None
    assert persisted["lookups"]["newsum"] is None

    _slovnyk_cache("немає")

    assert calls == ["newsum"]


def test_slovnyk_cache_migrates_v1_none_misses_to_retryable_absences(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(enrich_manifest_module, "SLOVNYK_CACHE", tmp_path)
    monkeypatch.setattr(enrich_manifest_module, "_SLOVNYK_LOOKUP_SLUGS", ("newsum", "synonyms", "phraseology"))

    cache_path = enrich_manifest_module._slovnyk_cache_path("слово")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "lemma": "слово",
                "lookup_word": "слово",
                "fetched_at": "2026-01-01T00:00:00+00:00",
                "lookups": {
                    "newsum": {"dictionary_slug": "newsum", "text": "kept hit"},
                    "synonyms": None,
                    "phraseology": None,
                },
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    calls: list[str] = []

    def fake_fetch(lemma: str, lookup_word: str, slug: str) -> dict[str, str]:
        calls.append(slug)
        return {"dictionary_slug": slug, "text": f"refetched {slug}"}

    monkeypatch.setattr(enrich_manifest_module, "_fetch_slovnyk_entry", fake_fetch)

    cache = _slovnyk_cache("слово")
    persisted = json.loads(cache_path.read_text(encoding="utf-8"))

    assert calls == ["synonyms", "phraseology"]
    assert cache["schema_version"] == 2
    assert cache["lookups"]["newsum"]["text"] == "kept hit"
    assert cache["lookups"]["synonyms"]["text"] == "refetched synonyms"
    assert persisted["schema_version"] == 2
    assert persisted["lookups"]["phraseology"]["text"] == "refetched phraseology"


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


def test_definition_cards_emit_separate_visible_sources_with_sum11_risk(monkeypatch) -> None:
    conn = _conn()
    conn.execute(
        "INSERT INTO grinchenko (word, definition, source) VALUES (?, ?, ?)",
        ("прапор", "Прапоръ, -ра, м. Знамя.", "Грінченко"),
    )
    conn.execute(
        """
        INSERT INTO sum11
            (word, definition, text, sovietization_risk, sovietization_keywords)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "прапор",
            "ПРАПОР, а, ч. Символ держави. Прапор Леніна.",
            "",
            2,
            "ленін,партійн",
        ),
    )
    monkeypatch.setattr(
        enrich_manifest_module,
        "_sum20_definition_card",
        lambda lemma, cache=None: {
            "id": "sum20",
            "source": "СУМ-20",
            "source_pill": "СУМ-20",
            "note": "сучасний тлумачний словник",
            "definitions": ["ПРАПОР, а, ч. Офіційний символ."],
        },
    )

    cards = _definition_cards(conn, "прапор", has_sum11_flags=True)

    assert [card["id"] for card in cards] == ["sum20", "sum11-flagged"]
    assert cards[0]["source"] == "СУМ-20"
    assert cards[1]["sovietization_risk"] == 2
    assert cards[1]["sovietization_keywords"] == ["ленін", "партійн"]
    assert cards[1]["flag_note"] == "⚠ СУМ-11 — радянське видання; подаємо обережно, перевага СУМ-20/Вікісловнику"
    assert all(card["source"] != "Грінченко 1907" for card in cards)


def test_cefr_lookup_uses_exact_puls_row() -> None:
    conn = _conn()
    conn.execute(
        "INSERT INTO puls_cefr (word, level, pos, text) VALUES (?, ?, ?, ?)",
        ("вікно", "A1", "іменник", "вікно (A1, іменник)"),
    )

    cefr = _cefr(conn, "вікно")

    assert cefr == {
        "level": "A1",
        "source": "PULS CEFR",
        "pos": "іменник",
        "text": "вікно (A1, іменник)",
    }


def test_literary_attestation_requires_exact_form_hit() -> None:
    conn = _conn()
    conn.execute(
        """
        INSERT INTO literary_texts
            (id, chunk_id, title, text, source_file, author, work, year)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            "chunk-1",
            "",
            "Крізь вікно видно сад і ранкове світло.",
            "fixture.jsonl",
            "Автор",
            "Твір",
            1900,
        ),
    )
    conn.execute("INSERT INTO literary_fts(literary_fts) VALUES('rebuild')")

    attestation = _literary_attestation(conn, "вікно")

    assert attestation is not None
    assert attestation["source"] == "literary_fts"
    assert attestation["source_label"] == "Автор · Твір · 1900"
    assert "вікно" in attestation["text"]


def test_literary_excerpt_indexes_stripped_text_with_source_stress_marks() -> None:
    excerpt = _literary_excerpt("Далека доро́га вела до вікно і саду.", "вікно", radius=8)

    assert excerpt.startswith("…вела до")
    assert "вікно" in excerpt


def test_kaikki_pronunciation_uses_stress_stripped_lookup() -> None:
    lookup = {"автобус": {"ipa": ["[ɐu̯ˈtɔbʊs]"], "etymology_text": "", "pos": ["noun"]}}

    pronunciation = _kaikki_pronunciation(lookup, "авто́бус")

    assert pronunciation == {"ipa": "[ɐu̯ˈtɔbʊs]", "source": KAIKKI_SOURCE}


def test_kaikki_etymology_is_final_fallback() -> None:
    conn = _conn()
    lookup = {
        "місто": {
            "ipa": [],
            "etymology_text": "From Old East Slavic мѣсто.",
            "pos": ["noun"],
        }
    }

    etymology = _etymology(conn, "місто", lookup)

    assert etymology == {"text": "From Old East Slavic мѣсто.", "source": KAIKKI_SOURCE}


@pytest.mark.parametrize(
    ("derived", "base"),
    [
        ("добре", "добрий"),
        ("чудово", "чудо"),
        ("пізно", "пізній"),
        ("нормально", "нормальний"),
        ("сьома", "сім"),
        ("навчатися", "вчити"),
        ("вмиватися", "мити"),
        ("збиратися", "брати"),
        ("одягатися", "одяг"),
        ("повертатися", "вертати"),
    ],
)
def test_derivational_etymology_falls_back_to_base_forms(derived: str, base: str) -> None:
    conn = _conn()
    conn.execute(
        """
        CREATE TABLE goroh_etymology (
            requested_lemma TEXT NOT NULL,
            headword TEXT NOT NULL,
            etymology_text TEXT NOT NULL,
            source_url TEXT
        )
        """
    )
    conn.execute(
        "INSERT INTO goroh_etymology VALUES (?, ?, ?, ?)",
        (base, base, f"Fixture etymology for {base}.", f"https://goroh.example/{base}"),
    )

    etymology = _etymology(conn, derived, {})

    assert etymology == {
        "text": f"Fixture etymology for {base}.",
        "source": f"Горох (за ЕСУМ) (etymology of base form {base})",
        "source_url": f"https://goroh.example/{base}",
    }


def test_compositional_greeting_phrases_have_no_etymology_fallback() -> None:
    conn = _conn()
    conn.execute(
        """
        CREATE TABLE goroh_etymology (
            requested_lemma TEXT NOT NULL,
            headword TEXT NOT NULL,
            etymology_text TEXT NOT NULL,
            source_url TEXT
        )
        """
    )
    conn.execute(
        "INSERT INTO goroh_etymology VALUES (?, ?, ?, ?)",
        ("До побачення!", "до побачення", "Fixture phrase etymology.", "https://goroh.example/phrase"),
    )

    assert _etymology(conn, "До побачення!", {}) is None


def test_kaikki_etymology_skips_russian_labeled_cyrillic() -> None:
    conn = _conn()
    lookup = {
        "базовий": {
            "ipa": [],
            "etymology_text": "From ба́за. Compare Russian ба́зовый (bázovyj), Belarusian ба́завы.",
            "pos": ["adjective"],
        }
    }

    assert _etymology(conn, "базовий", lookup) is None


def test_kaikki_etymology_does_not_overwrite_goroh() -> None:
    conn = _conn()
    conn.execute(
        """
        CREATE TABLE goroh_etymology (
            requested_lemma TEXT NOT NULL,
            headword TEXT NOT NULL,
            etymology_text TEXT NOT NULL,
            source_url TEXT
        )
        """
    )
    conn.execute(
        "INSERT INTO goroh_etymology VALUES (?, ?, ?, ?)",
        ("книга", "книга", "Goroh etymology text.", "https://goroh.pp.ua/Етимологія/книга"),
    )
    lookup = {
        "книга": {
            "ipa": [],
            "etymology_text": "Kaikki etymology text that must not win.",
            "pos": ["noun"],
        }
    }

    etymology = _etymology(conn, "книга", lookup)

    assert etymology == {
        "text": "Goroh etymology text.",
        "source": "Горох (за ЕСУМ)",
        "source_url": "https://goroh.pp.ua/Етимологія/книга",
    }


def test_enrich_uses_base_form_for_pair_single_form_sections(monkeypatch, tmp_path) -> None:
    manifest_path = tmp_path / "manifest.json"
    db_path = tmp_path / "sources.sqlite"
    manifest_path.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "lemma": "робота / працювати",
                        "gloss": "work",
                        "pos": "noun",
                    }
                ]
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE goroh_etymology (
            requested_lemma TEXT NOT NULL,
            headword TEXT NOT NULL,
            etymology_text TEXT NOT NULL,
            source_url TEXT
        )
        """
    )
    conn.execute(
        "INSERT INTO goroh_etymology VALUES (?, ?, ?, ?)",
        ("робота", "робота", "Goroh etymology for робота.", "https://goroh.pp.ua/Етимологія/робота"),
    )
    conn.commit()
    conn.close()

    cache = {
        "lookups": {
            "synonyms": {
                "dictionary_slug": "synonyms",
                "dictionary_label": "Словник синонімів української мови",
                "source_url": "https://slovnyk.me/dict/synonyms/робота",
                "word": "робота",
                "text": "робота ПРАЦЯ. Джерело: тест",
            }
        }
    }
    verify_calls: list[str] = []

    def fake_verify_lemma(lemma: str) -> list[dict[str, str]]:
        verify_calls.append(lemma)
        if lemma != "робота":
            return []
        return [{"word_form": "робота", "tags": "noun:s:f:v_naz", "pos": "noun"}]

    _patch_vesum_analyses(monkeypatch, {"робота": "noun", "праця": "noun"})
    monkeypatch.setattr(enrich_manifest_module, "MANIFEST", manifest_path)
    monkeypatch.setattr(enrich_manifest_module, "SOURCES_DB", db_path)
    monkeypatch.setattr(enrich_manifest_module, "_load_kaikki_lookup", lambda: {})
    monkeypatch.setattr(enrich_manifest_module, "_slovnyk_cache", lambda lemma: cache)
    monkeypatch.setattr(
        enrich_manifest_module,
        "classify_lemma",
        lambda lemma: {
            "classification": "unknown",
            "attestations": [],
            "is_russianism": False,
            "russian_shadow": False,
            "sovietization_risk": 0,
            "calque_warning": None,
        },
    )
    monkeypatch.setattr(enrich_manifest_module, "_sum11_has_flag_columns", lambda conn: True)
    monkeypatch.setattr(enrich_manifest_module, "_definition_cards", lambda *args, **kwargs: [])
    monkeypatch.setattr(enrich_manifest_module, "_kaikki_pronunciation", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_idioms_slovnyk", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_stress_display_form", lambda form: "")
    monkeypatch.setattr(enrich_manifest_module, "_cefr", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_meaning", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_literary_attestation", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_translation", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "verify_lemma", fake_verify_lemma)

    assert enrich_manifest_module.enrich() == (1, 1)

    enriched = json.loads(manifest_path.read_text(encoding="utf-8"))["entries"][0]
    assert enriched["lemma"] == "робота / працювати"
    assert enriched["sections"]["synonyms"]["items"] == ["праця"]
    assert enriched["enrichment"]["etymology"]["text"] == "Goroh etymology for робота."
    assert enriched["enrichment"]["morphology"]["forms"] == [{"form": "робота", "label": "однина, жін., називний"}]
    assert verify_calls == ["робота"]


def test_dmklinger_key_strips_stress_and_casefolds() -> None:
    # dmklinger stores STRESSED headwords; manifest lemmas are unstressed.
    # The key must reduce both sides to the same stress-free, casefolded form,
    # otherwise exact matching misses ~93% of common words.
    assert _dmklinger_key("робо́та") == _dmklinger_key("робота") == "робота"
    assert _dmklinger_key("Украї́на") == "україна"
    assert _dmklinger_key("  бу́ти ") == "бути"


def test_translation_matches_stress_stripped_dmklinger_headword(monkeypatch) -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE dmklinger_uk_en (word TEXT, pos TEXT, translations TEXT)")
    conn.execute(
        "INSERT INTO dmklinger_uk_en (word, pos, translations) VALUES (?, ?, ?)",
        ("робо́та", "noun", json.dumps(["work (labour)", "job", "work (labour)"])),
    )
    # Reset the module-level dmklinger index cache so it reloads from this DB.
    monkeypatch.setattr(enrich_manifest_module, "_DMKLINGER_INDEX", None)

    block = _translation(conn, "робота")  # unstressed manifest lemma

    assert block == {
        "en": ["work (labour)", "job"],  # deduped, order preserved
        "source": "dmklinger",
        "pos": "noun",
    }


def test_translation_returns_none_when_lemma_absent(monkeypatch) -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE dmklinger_uk_en (word TEXT, pos TEXT, translations TEXT)")
    monkeypatch.setattr(enrich_manifest_module, "_DMKLINGER_INDEX", None)

    assert _translation(conn, "неіснуючеслово") is None


def test_wiki_reference_success(monkeypatch) -> None:
    fake_wiki_data = {
        "title": "Україна",
        "description": "держава в Східній Європі",
        "extract": "Україна — держава в Східній Європі.",
        "url": "https://uk.wikipedia.org/wiki/Україна",
    }

    def mock_query(title: str) -> dict | None:
        if title == "Україна":
            return fake_wiki_data
        return None

    monkeypatch.setattr(enrich_manifest_module, "query_wikipedia", mock_query)

    # test without literary attestation
    ref = enrich_manifest_module._wiki_reference("Україна")
    assert ref is not None
    assert ref["wikipedia"]["title"] == "Україна"
    assert ref["wikipedia"]["summary"] == "Україна — держава в Східній Європі."
    assert ref["wikipedia"]["url"] == "https://uk.wikipedia.org/wiki/Україна"
    assert "uk.wiktionary.org" in ref["wiktionary_url"]
    assert ref["wikisource_url"] is None

    # test with literary attestation
    ref_with_lit = enrich_manifest_module._wiki_reference("Україна", {"text": "some excerpt"})
    assert ref_with_lit is not None
    assert ref_with_lit["wikisource_url"] is not None
    assert "uk.wikisource.org" in ref_with_lit["wikisource_url"]


def test_wiki_reference_missing(monkeypatch) -> None:
    def mock_query(title: str) -> dict | None:
        return None

    monkeypatch.setattr(enrich_manifest_module, "query_wikipedia", mock_query)

    ref = enrich_manifest_module._wiki_reference("варити")
    assert ref is None
