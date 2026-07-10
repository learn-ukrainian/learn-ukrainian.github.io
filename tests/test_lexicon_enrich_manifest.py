import json
import sqlite3
import typing
from urllib.parse import urlparse

import pytest

from scripts.lexicon import enrich_manifest as enrich_manifest_module
from scripts.lexicon.enrich_manifest import (
    _BALLA_REVERSE_SOURCE,
    _DROP_ANTONYM_LEMMAS,
    _SLOVNYK_UKRENG_SOURCE,
    _STYLE_MARKER_LABELS,
    _WRONG_ANTONYMS,
    _WRONG_SENSE_SYNONYMS,
    KAIKKI_SOURCE,
    _antonyms_wiktionary,
    _base_lemma,
    _build_paradigm,
    _cefr,
    _clean_synonym_candidate,
    _curated_calque,
    _definition_cards,
    _dmklinger_key,
    _etymology,
    _etymology_lookup_variants,
    _idioms,
    _idioms_frazeolohichnyi,
    _idioms_slovnyk,
    _kaikki_meaning,
    _kaikki_pronunciation,
    _kaikki_stress,
    _literary_attestation,
    _literary_excerpt,
    _meaning,
    _merge_slovnyk_warning,
    _morphology,
    _normalize_manifest_entries,
    _parse_translations,
    _prepare_cefr_estimates,
    _proper_noun_wikipedia_meaning,
    _resolve_definition_xref,
    _sense_correct_synonyms,
    _slovnyk_cache,
    _SlovnykTransientError,
    _style_markers_in_tag,
    _sum11_definition_card,
    _surface_gloss_hints,
    _synonyms_slovnyk,
    _translation,
    _verb_aspect,
    _vts_definition_card,
    _warning_slovnyk,
    _xref_provenance_prefix,
    _xref_target_lemmas,
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


def _url_hostname(url: str) -> str | None:
    return urlparse(url).hostname


def test_cleanup_helpers_strip_chunk_and_decode_entities() -> None:
    assert clean_gloss("Good morning — chunk, unstressed `[о]` stays clean") == "Good morning"
    assert clean_html_entities("20&amp;nbsp;Гц &amp;lt;br&amp;gt;") == "20 Гц <br>"


def test_base_lemma_splits_pairs_without_lowercasing_non_pairs() -> None:
    non_pair = " Київ "

    assert _base_lemma("варити / зварити") == "варити"
    assert _base_lemma("Київ") == "Київ"
    assert _base_lemma(non_pair) == non_pair


def test_normalize_manifest_entries_strips_acute_and_merges_duplicates() -> None:
    manifest = {
        "entries": [
            {
                "lemma": "авантю\u0301рний",
                "url_slug": "авантю-рний",
                "gloss": "adventurous",
                "course_usage": [{"track": "a1", "module_num": 1, "slug": "m1", "context": "built_vocabulary"}],
            },
            {
                "lemma": "авантюрний",
                "url_slug": "авантюрний",
                "pos": "adj",
                "course_usage": [{"track": "a1", "module_num": 2, "slug": "m2", "context": "built_vocabulary"}],
            },
            {"lemma": "їжак", "url_slug": "їжак"},
        ]
    }

    assert _normalize_manifest_entries(manifest) > 0

    entries = {entry["lemma"]: entry for entry in manifest["entries"]}
    assert set(entries) == {"авантюрний", "їжак"}
    assert entries["авантюрний"]["url_slug"] == "авантюрний"
    assert entries["авантюрний"]["pos"] == "adj"
    assert [usage["slug"] for usage in entries["авантюрний"]["course_usage"]] == ["m1", "m2"]
    assert "\u0301" not in entries["авантюрний"]["lemma"]
    assert entries["їжак"]["lemma"] == "їжак"


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
    assert paradigm["tenses"]["майбутній"]["множина"]["1"] == "навчатимемось / навчатимемося / навчатимемся"
    assert paradigm["tenses"]["теперішній"]["множина"]["1"] == "навчаємось / навчаємося / навчаємся"
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


# --- #4891: style-marked forms segregated out of the modern paradigm ---


def _korysnyi_vesum_rows() -> list[dict[str, str]]:
    """Minimal VESUM fixture for корисний: the modern paradigm plus the :long
    (нестягнені) forms that must be segregated. Mirrors data/vesum.db shape."""
    return [
        {"word_form": "корисний", "tags": "adj:m:v_naz:compb", "pos": "adj"},
        {"word_form": "корисна", "tags": "adj:f:v_naz:compb", "pos": "adj"},
        {"word_form": "корисне", "tags": "adj:n:v_naz:compb", "pos": "adj"},
        {"word_form": "корисні", "tags": "adj:p:v_naz:compb", "pos": "adj"},
        {"word_form": "корисная", "tags": "adj:f:v_naz:compb:long", "pos": "adj"},
        {"word_form": "кориснеє", "tags": "adj:n:v_naz:compb:long", "pos": "adj"},
        {"word_form": "кориснії", "tags": "adj:p:v_naz:compb:long", "pos": "adj"},
    ]


def test_style_markers_match_whole_tokens_only() -> None:
    # A raw :long adjective tag surfaces the long marker …
    assert _style_markers_in_tag("adj:f:v_naz:compb:long") == ["long"]
    # … a plain modern-paradigm tag surfaces nothing …
    assert _style_markers_in_tag("adj:f:v_naz:compb") == []
    # … `ns` (pluralia tantum) is grammatical, NOT a style marker, so двері is clean.
    assert _style_markers_in_tag("noun:inanim:p:v_naz:ns") == []
    assert "ns" not in _STYLE_MARKER_LABELS


def test_morphology_segregates_marked_forms_into_marked_group(monkeypatch) -> None:
    monkeypatch.setattr(enrich_manifest_module, "verify_lemma", lambda lemma: _korysnyi_vesum_rows())
    monkeypatch.setattr(enrich_manifest_module, "_stress_display_form", lambda form: "")

    morphology = _morphology("корисний")

    assert morphology is not None
    # The modern paradigm carries only the 4 unmarked rows; the count matches.
    modern_forms = {row["form"] for row in morphology["forms"]}
    assert modern_forms == {"корисний", "корисна", "корисне", "корисні"}
    assert morphology["form_count"] == 4
    assert {"корисная", "кориснеє", "кориснії"}.isdisjoint(modern_forms)
    # The :long forms are segregated with the doc-verified нестягнена label.
    assert morphology["marked_form_count"] == 3
    marked = morphology["marked_forms"]
    assert [row["form"] for row in marked] == ["корисная", "кориснеє", "кориснії"]
    assert all(row["marker"] == "long" for row in marked)
    assert all(row["marker_label"] == "нестягнена форма" for row in marked)
    # The grammatical label is preserved alongside the style label.
    assert marked[0]["label"] == "жін., називний"


def test_morphology_marked_form_stress_applies_like_modern_rows(monkeypatch) -> None:
    monkeypatch.setattr(enrich_manifest_module, "verify_lemma", lambda lemma: _korysnyi_vesum_rows())
    monkeypatch.setattr(
        enrich_manifest_module,
        "_stress_display_form",
        lambda form: f"{form}́" if form == "корисная" else "",
    )

    morphology = _morphology("корисний")

    assert morphology is not None
    marked_by_form = {row["form"]: row for row in morphology["marked_forms"]}
    assert marked_by_form["корисная"]["stress"] == "корисная́"
    assert "stress" not in marked_by_form["кориснеє"]


def test_unknown_grammatical_token_stays_in_modern_paradigm(monkeypatch) -> None:
    # A token that is NOT a style marker (grammatical/unknown) must never be
    # segregated — it stays inline, unchanged. `arch` IS a style marker, so it goes.
    rows = [
        {"word_form": "сад", "tags": "noun:inanim:m:v_naz", "pos": "noun"},
        {"word_form": "садку", "tags": "noun:inanim:m:v_dav:xp1", "pos": "noun"},
        {"word_form": "садовий", "tags": "noun:inanim:m:v_naz:arch", "pos": "noun"},
    ]
    monkeypatch.setattr(enrich_manifest_module, "verify_lemma", lambda lemma: rows)
    monkeypatch.setattr(enrich_manifest_module, "_stress_display_form", lambda form: "")

    morphology = _morphology("сад")

    assert morphology is not None
    modern_forms = {row["form"] for row in morphology["forms"]}
    assert "садку" in modern_forms  # grammatical xp1 token → unchanged, stays modern
    assert "садовий" not in modern_forms  # arch → segregated
    assert [row["marker_label"] for row in morphology["marked_forms"]] == ["застаріла форма"]


def test_segregated_but_unlabelled_marker_gets_generic_label(monkeypatch) -> None:
    # If a future VESUM style flag is added to the segregation set before its Ukrainian
    # label is authored, the form is still segregated but carries the honest generic
    # label «інша маркована форма» — never a guessed description (#M-4).
    monkeypatch.setattr(enrich_manifest_module, "_STYLE_MARKERS", frozenset({"long", "newmk"}))
    rows = [
        {"word_form": "новий", "tags": "adj:m:v_naz", "pos": "adj"},
        {"word_form": "новомк", "tags": "adj:m:v_naz:newmk", "pos": "adj"},
    ]
    monkeypatch.setattr(enrich_manifest_module, "verify_lemma", lambda lemma: rows)
    monkeypatch.setattr(enrich_manifest_module, "_stress_display_form", lambda form: "")

    morphology = _morphology("новий")

    assert morphology is not None
    assert {row["form"] for row in morphology["forms"]} == {"новий"}
    marked = morphology["marked_forms"]
    assert marked[0]["marker"] == "newmk"
    assert marked[0]["marker_label"] == enrich_manifest_module._GENERIC_STYLE_MARKER_LABEL
    assert marked[0]["marker_label"] == "інша маркована форма"


def test_morphology_pluralia_tantum_ns_stays_in_modern_paradigm(monkeypatch) -> None:
    # двері carries :ns on every form; that is a grammatical class (pluralia tantum),
    # not a style marker — the whole paradigm must remain modern, else A1 words empty out.
    rows = [
        {"word_form": "двері", "tags": "noun:inanim:p:v_naz:ns", "pos": "noun"},
        {"word_form": "дверей", "tags": "noun:inanim:p:v_rod:ns", "pos": "noun"},
        {"word_form": "дверям", "tags": "noun:inanim:p:v_dav:ns", "pos": "noun"},
    ]
    monkeypatch.setattr(enrich_manifest_module, "verify_lemma", lambda lemma: rows)
    monkeypatch.setattr(enrich_manifest_module, "_stress_display_form", lambda form: "")

    morphology = _morphology("двері")

    assert morphology is not None
    assert morphology["form_count"] == 3
    assert "marked_forms" not in morphology
    assert "marked_form_count" not in morphology


def test_morphology_unmarked_lemma_omits_marked_keys(monkeypatch) -> None:
    # A fully unmarked lemma produces the pre-#4891 shape: no marked_forms /
    # marked_form_count keys, and form_count == len(forms).
    rows = [
        {"word_form": "робота", "tags": "noun:inanim:f:v_naz", "pos": "noun"},
        {"word_form": "роботи", "tags": "noun:inanim:f:v_rod", "pos": "noun"},
    ]
    monkeypatch.setattr(enrich_manifest_module, "verify_lemma", lambda lemma: rows)
    monkeypatch.setattr(enrich_manifest_module, "_stress_display_form", lambda form: "")

    morphology = _morphology("робота")

    assert morphology is not None
    assert set(morphology) == {"pos", "form_count", "forms", "source"}
    assert morphology["form_count"] == len(morphology["forms"]) == 2


def test_morphology_form_count_matches_rendered_rows_after_cap(monkeypatch) -> None:
    # form_count is reported AFTER the cap so it never disagrees with the rows shown
    # (pre-#4891: «41 форм» beside 40 rows). 45 distinct unmarked rows → capped to 40.
    rows = [
        {"word_form": f"форма{i}", "tags": "noun:inanim:f:v_naz", "pos": "noun"} for i in range(45)
    ]
    monkeypatch.setattr(enrich_manifest_module, "verify_lemma", lambda lemma: rows)
    monkeypatch.setattr(enrich_manifest_module, "_stress_display_form", lambda form: "")

    morphology = _morphology("форма")

    assert morphology is not None
    assert len(morphology["forms"]) == enrich_manifest_module._MORPHOLOGY_FORM_CAP
    assert morphology["form_count"] == len(morphology["forms"])


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
    # "чудесно" was only reachable by reading the СУМ-11 definition above; with the
    # Soviet dictionary no longer consulted (2026-06-26) it is correctly dropped.
    assert _sense_correct_synonyms(conn, "чудово") == ["прекрасно"]

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
                "text": ("гарний ГА́РНИЙ (про людину), КРАСИ́ВИЙ, ВРОДЛИ́ВИЙ (УРОДЛИ́ВИЙ), ХОРО́ШИЙ. Джерело: тест"),
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


def test_synonym_qualifiers_and_sense_guard_for_shliakh(monkeypatch) -> None:
    _patch_vesum_analyses(
        monkeypatch,
        {
            "шлях": "noun",
            "дорога": "noun",
            "тракт": "noun",
            "гостинець": "noun",
            "кам'янка": "noun",
            "кам'яниця": "noun",
        },
    )
    cache = {
        "lookups": {
            "synonyms": {
                "dictionary_slug": "synonyms",
                "dictionary_label": "Словник синонімів української мови",
                "word": "шлях",
                "source_url": "https://slovnyk.me/dict/synonyms/шлях",
                "text": "шлях ДОРО́ГА, ТРАКТ заст., ГОСТИ́НЕЦЬ розм., КА́М'ЯНКА діал. (брукована). Джерело: тест",
            },
            "synonyms_karavansky": {
                "dictionary_slug": "synonyms_karavansky",
                "dictionary_label": "Словник синонімів Караванського",
                "word": "шлях",
                "source_url": "https://slovnyk.me/dict/synonyms_karavansky/шлях",
                "text": "шлях ДОРОГА, д. кам'яниця. Джерело: тест",
            },
        }
    }

    section = _synonyms_slovnyk("шлях", cache, entry_pos="noun")
    assert section is not None
    items = section["items"]

    # Verify wrong-sense synonym 'кам'яниця' is dropped
    assert "кам'яниця" not in items
    assert "кам'яниця (діал.)" not in items

    # Verify other synonyms are kept with their qualifiers preserved
    assert "дорога" in items
    assert "тракт (заст.)" in items
    assert "гостинець (розм.)" in items
    assert "кам'янка (діал.)" in items


def test_synonym_frequency_qualifiers_are_preserved(monkeypatch) -> None:
    _patch_vesum_analyses(
        monkeypatch,
        {
            "джерело": "noun",
            "ключ": "noun",
            "криниця": "noun",
            "криничка": "noun",
            "керниця": "noun",
        },
    )
    cache = {
        "lookups": {
            "synonyms": {
                "dictionary_slug": "synonyms",
                "dictionary_label": "Словник синонімів української мови",
                "word": "джерело",
                "source_url": "https://slovnyk.me/dict/synonyms/джерело",
                "text": "джерело ДЖЕРЕЛО́, КЛЮЧ рідше, КРИНИ́ЧКА, КРИНИ́ЦЯ рідко, КЕРНИ́ЦЯ діал. Джерело: тест",
            },
        }
    }

    section = _synonyms_slovnyk("джерело", cache, entry_pos="noun")
    assert section is not None
    items = section["items"]

    assert "ключ (рідше)" in items
    assert "криниця (рідко)" in items
    assert "керниця (діал.)" in items


def test_synonym_sense_guard_for_richka(monkeypatch) -> None:
    _patch_vesum_analyses(
        monkeypatch,
        {
            "річка": "noun",
            "струмок": "noun",
            "звір": "noun",
        },
    )
    cache = {
        "lookups": {
            "synonyms_karavansky": {
                "dictionary_slug": "synonyms_karavansky",
                "dictionary_label": "Словник синонімів Караванського",
                "word": "річка",
                "source_url": "https://slovnyk.me/dict/synonyms_karavansky/річка",
                "text": "річка струмок, звір. Джерело: тест",
            },
        }
    }

    section = _synonyms_slovnyk("річка", cache, entry_pos="noun")
    assert section is not None
    items = section["items"]
    assert "звір" not in items
    assert "струмок" in items


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


def test_wiktionary_antonyms_use_explicit_antonym_column(monkeypatch) -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE wiktionary (
            word TEXT NOT NULL,
            definitions TEXT DEFAULT '',
            synonyms TEXT DEFAULT '',
            antonyms TEXT DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            source TEXT DEFAULT ''
        )
        """
    )
    conn.executemany(
        "INSERT INTO wiktionary (word, antonyms) VALUES (?, ?)",
        [
            ("ніч", json.dumps(["день", "night"], ensure_ascii=False)),
            ("день", json.dumps(["ніч"], ensure_ascii=False)),
        ],
    )
    _patch_vesum_analyses(monkeypatch, {"ніч": "noun", "день": "noun"})

    section = _antonyms_wiktionary(conn, "ніч", entry_pos="noun")

    assert section == {
        "items": ["день"],
        "source": "Вікісловник: explicit antonym list",
        "source_urls": ["https://uk.wiktionary.org/wiki/%D0%BD%D1%96%D1%87"],
    }


def test_wiktionary_antonyms_drop_noise_only_lemma_returns_none(monkeypatch) -> None:
    # #3197 — lemmas whose ENTIRE Вікісловник antonym set is noise yield no section:
    # а→зет (alphabet), брат→ворог (no lexical antonym), не→да (Russian).
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE wiktionary (
            word TEXT NOT NULL,
            antonyms TEXT DEFAULT ''
        )
        """
    )
    conn.executemany(
        "INSERT INTO wiktionary (word, antonyms) VALUES (?, ?)",
        [
            ("а", json.dumps(["зет"], ensure_ascii=False)),
            ("брат", json.dumps(["ворог"], ensure_ascii=False)),
            ("не", json.dumps(["да"], ensure_ascii=False)),
        ],
    )
    _patch_vesum_analyses(monkeypatch, {"зет": "noun", "ворог": "noun", "да": "noun"})

    assert _antonyms_wiktionary(conn, "а", entry_pos="noun") is None
    assert _antonyms_wiktionary(conn, "брат", entry_pos="noun") is None
    assert _antonyms_wiktionary(conn, "не", entry_pos="part") is None


def test_wiktionary_antonyms_filter_wrong_terms_keep_valid(monkeypatch) -> None:
    # #3197 — дочка keeps the real opposite (син) and drops the co-hyponym noise
    # (мати-variants + матка = uterus/queen bee, СУМ-11), not a global stoplist.
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE wiktionary (
            word TEXT NOT NULL,
            antonyms TEXT DEFAULT ''
        )
        """
    )
    conn.execute(
        "INSERT INTO wiktionary (word, antonyms) VALUES (?, ?)",
        ("дочка", json.dumps(["син", "мати", "матка", "матуся"], ensure_ascii=False)),
    )
    _patch_vesum_analyses(
        monkeypatch,
        {"син": "noun", "мати": "noun", "матка": "noun", "матуся": "noun"},
    )

    section = _antonyms_wiktionary(conn, "дочка", entry_pos="noun")

    assert section is not None
    assert section["items"] == ["син"]


def test_antonym_filters_are_curated_per_lemma_and_disjoint() -> None:
    # #3197 — a lemma is either whole-dropped OR per-term-filtered, never both;
    # and every per-term filter retains at least one intended valid opposite.
    assert not (_DROP_ANTONYM_LEMMAS & set(_WRONG_ANTONYMS))
    assert all(terms for terms in _WRONG_ANTONYMS.values())


def test_frazeolohichnyi_idioms_keep_phrase_hits_and_drop_definition_noise(monkeypatch) -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE frazeolohichnyi (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL,
            definition TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            source TEXT DEFAULT ''
        )
        """
    )
    conn.executemany(
        "INSERT INTO frazeolohichnyi (word, definition, text, source) VALUES (?, ?, ?, ?)",
        [
            (
                "яблуко розбрату {{</fras>}}",
                "[']я[/']блуко р[']о[/']збрату (чвар), книжн. Причина ворожнечі, суперечок.",
                "яблуко розбрату: Причина ворожнечі.",
                "Фразеологічний словник",
            ),
            (
                "брати верх {{</fras>}}",
                "бр[']а[/']ти верх над ким--чим. Вода була така сильна, що брала верх.",
                "брати верх: Вода була така сильна.",
                "Фразеологічний словник",
            ),
            (
                "яблукові ніде впасти {{</fras>}}",
                "г[']о[/']лці ([']я[/']блуку, [']я[/']блукові) н[']і[/']де вп[']а[/']сти. Дуже людно.",
                "яблукові ніде впасти: Дуже людно.",
                "Фразеологічний словник",
            ),
        ],
    )
    monkeypatch.setattr(
        enrich_manifest_module,
        "_vesum_word_analyses",
        lambda word: (("яблуко", "noun"),) if word in {"яблуку", "яблукові"} else (),
    )

    apple = _idioms_frazeolohichnyi(conn, "яблуко")
    water = _idioms_frazeolohichnyi(conn, "вода")

    assert apple is not None
    assert [item["phrase"] for item in apple["items"]] == [
        "яблуко розбрату (чвар), книжн",
        "голці (яблуку, яблукові) ніде впасти",
    ]
    assert "Причина ворожнечі" in apple["items"][0]["definition"]
    assert water is None


def test_idioms_merge_slovnyk_cache_and_frazeolohichnyi_fallback(monkeypatch) -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE frazeolohichnyi (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL,
            definition TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            source TEXT DEFAULT ''
        )
        """
    )
    conn.execute(
        "INSERT INTO frazeolohichnyi (word, definition, text, source) VALUES (?, ?, ?, ?)",
        (
            "яблукові ніде впасти {{</fras>}}",
            "г[']о[/']лці ([']я[/']блуку, [']я[/']блукові) н[']і[/']де вп[']а[/']сти. Дуже людно.",
            "яблукові ніде впасти: Дуже людно.",
            "Фразеологічний словник",
        ),
    )
    cache = {
        "lookups": {
            "phraseology": {
                "dictionary_slug": "phraseology",
                "dictionary_label": "Фразеологічний словник української мови",
                "source_url": "https://slovnyk.me/dict/phraseology/яблуко",
                "word": "яблуко",
                "text": "яблуко я́блуко ро́збрату (чвар), книжн. Причина ворожнечі. Джерело: тест",
            }
        }
    }
    monkeypatch.setattr(
        enrich_manifest_module,
        "_vesum_word_analyses",
        lambda word: (("яблуко", "noun"),) if word in {"яблуку", "яблукові"} else (),
    )

    section = _idioms(conn, "яблуко", cache)

    assert section is not None
    assert [item["phrase"] for item in section["items"]] == [
        "яблуко розбрату (чвар), книжн",
        "голці (яблуку, яблукові) ніде впасти",
    ]


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

    assert card is not None
    assert card["kind"] == "participle"
    # sense-split (#3098 review): діючий закон → чинний; діючий вулкан → активний (Avramenko Grade-7)
    assert card["corrections"] == ["чинний", "активний"]
    assert card["note"] == (
        "sense-split: діючий закон → чинний закон; діючий вулкан → активний вулкан (рос. действующий)"
    )
    assert "glazova-11" in card["source"]
    assert any("чинний" in item for item in card["evidence"])
    assert any("активний" in item for item in card["evidence"])
    assert "search_heritage" in card["heritage_guard"]


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

    assert card is not None
    assert card["kind"] == "phrasal"
    assert card["corrections"] == ["погляд"]
    assert card["note"] == "рос. точка зрения; цієї точки зору → цього погляду"
    assert card["source"] == ["ua-gec", "grok-3098"]


def test_curated_calque_matches_collocation_slice2_phrasal_entries() -> None:
    expected = {
        "при допомозі": "за допомогою",
        "співпадати": "збігатися",
        "в кінці кінців": "врешті-решт",
    }
    for phrase, correction in expected.items():
        card = _curated_calque(phrase, phrase)
        assert card is not None
        assert card["kind"] == "phrasal"
        assert correction in card["corrections"]
        assert card["evidence"]
        assert "search_heritage" in card["heritage_guard"]


def test_curated_calque_matches_collocation_slice2_sense_restricted_entries() -> None:
    expected = {
        "на протязі": "протягом",
        "являтися": "бути",
        "дякуючи": "завдяки",
        "так як": "оскільки",
        "біля": "близько",
        "на рахунок": "щодо",
    }
    for phrase, correction in expected.items():
        card = _curated_calque(phrase, phrase)
        assert card is not None
        assert card["kind"] == "sense_restricted"
        assert correction in card["corrections"]
        assert card["calque_sense"] != card["authentic_sense"]
        assert card["evidence"]
        assert "search_heritage" in card["heritage_guard"]


def test_curated_calque_matches_single_word_lexical_slice3_entries() -> None:
    expected = {
        "слідуючий": ("lexical", "наступний"),
        "багаточисельний": ("lexical", "численний"),
        "міроприємство": ("lexical", "захід"),
        "учбовий": ("lexical", "навчальний"),
        "любий": ("sense_restricted", "будь-який"),
        "неділя": ("sense_restricted", "тиждень"),
    }
    for headword, (kind, correction) in expected.items():
        card = _curated_calque(headword, headword)
        assert card is not None
        assert card["kind"] == kind
        assert correction in card["corrections"]
        assert card["evidence"]
        assert "search_heritage" in card["heritage_guard"]


def test_collocation_slice2_authentic_phrases_are_not_exact_flagged() -> None:
    assert _curated_calque("біля школи", "біля школи") is None
    assert _curated_calque("на рахунок у банку", "на рахунок у банку") is None


def test_single_word_lexical_slice3_authentic_phrases_are_not_exact_flagged() -> None:
    assert _curated_calque("любий друже", "любий друже") is None
    assert _curated_calque("у неділю", "у неділю") is None
    assert _curated_calque("яблуко", "яблуко") is None


def test_curated_calque_unknown_lemma_returns_none() -> None:
    assert _curated_calque("яблуко", "яблуко") is None


def test_curated_calque_lexicalised_safe_lemma_returns_none() -> None:
    assert _curated_calque("блискучий", "блискучий") is None


def test_fetch_slovnyk_entry_raises_transient_for_5xx(monkeypatch) -> None:
    class FakeResponse:
        status_code = 503
        text = ""
        headers: typing.ClassVar[dict] = {}

        def raise_for_status(self) -> None:
            raise AssertionError("5xx should be classified before raise_for_status")

    monkeypatch.setattr(enrich_manifest_module, "_polite_slovnyk_delay", lambda: None)
    monkeypatch.setattr(enrich_manifest_module.time, "sleep", lambda *_: None)
    monkeypatch.setattr(enrich_manifest_module.requests, "get", lambda *args, **kwargs: FakeResponse())

    # 5xx now retries with backoff, then raises transient after exhausting retries (#3097).
    with pytest.raises(_SlovnykTransientError):
        enrich_manifest_module._fetch_slovnyk_entry("тест", "тест", "newsum")


def test_fetch_slovnyk_entry_raises_transient_for_connection_error(monkeypatch) -> None:
    def fake_get(*args, **kwargs):
        raise enrich_manifest_module.requests.ConnectionError("connection timed out")

    monkeypatch.setattr(enrich_manifest_module, "_polite_slovnyk_delay", lambda: None)
    monkeypatch.setattr(enrich_manifest_module.time, "sleep", lambda *_: None)
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


def test_sum11_is_never_used_as_meaning_source() -> None:
    """СУМ-11 (Soviet-era dictionary) must NEVER surface as a meaning, even when it
    is the only source for a word (decolonization decision 2026-06-26)."""
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

    # No Вікісловник/kaikki entry exists, so СУМ-11 used to fill this. It must not now.
    assert meaning is None


def test_definition_cards_exclude_sum11(monkeypatch) -> None:
    """Only modern Ukrainian-grounded sources (СУМ-20) emit definition cards;
    СУМ-11 (Soviet-era dictionary) is never emitted, regardless of risk
    (decolonization decision 2026-06-26)."""
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
    # Isolate from the live VTS lookup — this test asserts СУМ-11 exclusion, not coverage.
    monkeypatch.setattr(enrich_manifest_module, "_vts_definition_card", lambda lemma, cache=None: None)

    cards = _definition_cards(conn, "прапор", has_sum11_flags=True)

    # СУМ-11 card (even a flagged one) must be absent — only the СУМ-20 card survives.
    assert [card["id"] for card in cards] == ["sum20"]
    assert all("СУМ-11" not in (card.get("source") or "") for card in cards)
    assert all(card["id"] not in ("sum11", "sum11-flagged") for card in cards)


def test_vts_fills_definition_when_sum20_missing(monkeypatch) -> None:
    """When СУМ-20 has no entry, VTS (Великий тлумачний словник — modern, non-Soviet)
    fills the definition card. This is the clean replacement for the removed СУМ-11
    fallback (decolonization decision 2026-06-26)."""
    conn = _conn()
    # No СУМ-20 coverage for this word.
    monkeypatch.setattr(enrich_manifest_module, "_sum20_definition_card", lambda lemma, cache=None: None)
    monkeypatch.setattr(
        enrich_manifest_module,
        "_fetch_slovnyk_entry",
        lambda lemma, lookup_word, slug: (
            {"word": "вишиванка", "text": "вишива́нка -и, ж. розм. Вишита сорочка.", "source_url": ""}
            if slug == "vts"
            else None
        ),
    )

    cards = _definition_cards(conn, "вишиванка", has_sum11_flags=False)

    assert [card["id"] for card in cards] == ["vts"]
    assert cards[0]["source"] == "ВТС"
    assert "Вишита сорочка" in cards[0]["definitions"][0]
    # СУМ-20 also present → BOTH cards show, VTS on top and СУМ-20 below.
    monkeypatch.setattr(
        enrich_manifest_module,
        "_sum20_definition_card",
        lambda lemma, cache=None: {"id": "sum20", "source": "СУМ-20", "definitions": ["x"]},
    )
    assert [c["id"] for c in _definition_cards(conn, "вишиванка", has_sum11_flags=False)] == ["vts", "sum20"]


def test_definition_card_resolves_inflected_form_to_base_lemma(monkeypatch) -> None:
    """An inflected-form entry (моєму) resolves to its base lemma (мій) so a clean
    dictionary still covers it — closing the apparent coverage gap from removing
    СУМ-11 without ever touching the Soviet source (2026-06-26)."""
    conn = _conn()
    monkeypatch.setattr(enrich_manifest_module, "_sum20_definition_card", lambda lemma, cache=None: None)
    monkeypatch.setattr(
        enrich_manifest_module,
        "_vesum_base_lemma",
        lambda word: "мій" if word == "моєму" else None,
    )
    enrich_manifest_module._slovnyk_base_row.cache_clear()
    monkeypatch.setattr(
        enrich_manifest_module,
        "_fetch_slovnyk_entry",
        lambda lemma, lookup_word, slug: (
            {"word": "мій", "text": "МІЙ, моя́, моє́. Займ. присв. до я.", "source_url": ""}
            if (slug == "vts" and lemma == "мій")
            else None
        ),
    )

    cards = _definition_cards(conn, "моєму", has_sum11_flags=False)

    # Card built from the base lemma's VTS entry (leading headword "МІЙ" is stripped
    # by _definition_body, so assert on the surviving definition text).
    assert [c["id"] for c in cards] == ["vts"]
    assert "присв" in cards[0]["definitions"][0]
    enrich_manifest_module._slovnyk_base_row.cache_clear()


def test_pos_matched_base_lookup_rejects_wrong_pos_homograph(monkeypatch) -> None:
    def fake_analyses(word: str) -> tuple[tuple[str, str], ...]:
        if word == "бачу":
            return (("бачити", "verb"),)
        if word == "добре":
            return (("добрий", "adj"),)
        return ()

    monkeypatch.setattr(enrich_manifest_module, "_vesum_word_analyses", fake_analyses)

    assert enrich_manifest_module._base_lookup_for_entry("бачу", "verb") == "бачити"
    assert enrich_manifest_module._base_lookup_for_entry("добре", "adverb") is None


def test_enrich_entry_uses_pos_matched_base_translation_fallback(monkeypatch) -> None:
    def none(*args, **kwargs):
        return None

    monkeypatch.setattr(enrich_manifest_module, "_slovnyk_cache", lambda lemma: {})
    monkeypatch.setattr(enrich_manifest_module, "_definition_cards", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        enrich_manifest_module,
        "classify_lemma",
        lambda lemma: {
            "classification": "standard",
            "is_russianism": False,
            "russian_shadow": False,
            "calque_warning": None,
            "attestations": [],
        },
    )
    monkeypatch.setattr(enrich_manifest_module, "_warning_slovnyk", none)
    monkeypatch.setattr(enrich_manifest_module, "_curated_calque", none)
    monkeypatch.setattr(enrich_manifest_module, "_reverse_calques", none)
    monkeypatch.setattr(enrich_manifest_module, "_kaikki_pronunciation", none)
    monkeypatch.setattr(enrich_manifest_module, "_synonyms_slovnyk", none)
    monkeypatch.setattr(enrich_manifest_module, "_antonyms_wiktionary", none)
    monkeypatch.setattr(enrich_manifest_module, "_idioms", none)
    monkeypatch.setattr(enrich_manifest_module, "_stress_display_form", lambda *args, **kwargs: "")
    monkeypatch.setattr(enrich_manifest_module, "_kaikki_stress", none)
    monkeypatch.setattr(enrich_manifest_module, "_cefr", none)
    monkeypatch.setattr(enrich_manifest_module, "_morphology", none)
    monkeypatch.setattr(enrich_manifest_module, "_meaning", none)
    monkeypatch.setattr(enrich_manifest_module, "_etymology", none)
    monkeypatch.setattr(enrich_manifest_module, "_literary_attestation", none)
    monkeypatch.setattr(enrich_manifest_module, "_wiki_reference", none)
    monkeypatch.setattr(enrich_manifest_module, "_base_lookup_for_entry", lambda lemma, pos: "бачити")

    def fake_translation(conn, lemma: str, kaikki_lookup, **kwargs):
        if lemma == "бачити":
            return {"en": ["to see"], "source": "fixture"}
        return None

    monkeypatch.setattr(enrich_manifest_module, "_translation", fake_translation)

    entry = {"lemma": "бачу", "pos": "verb"}
    attached = enrich_manifest_module.enrich_entry(
        entry,
        sqlite3.connect(":memory:"),
        {},
        has_sum11_flags=False,
    )

    assert attached is True
    assert entry["enrichment"]["translation"] == {
        "en": ["to see"],
        "source": "fixture (base form бачити)",
    }


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


def test_cefr_estimate_is_labelled_from_grac_cache(monkeypatch, tmp_path) -> None:
    conn = _conn()
    cache_path = tmp_path / "grac_frequency.json"
    cache_path.write_text(
        json.dumps(
            {
                "абетка": {"word": "абетка", "freq": 200, "rel_freq": 4.0},
                "бариста": {"word": "бариста", "freq": 20, "rel_freq": 0.4},
                "вдома": {"word": "вдома", "freq": 9000, "rel_freq": 45.0},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(enrich_manifest_module, "GRAC_FREQUENCY_CACHE", cache_path)
    monkeypatch.setattr(enrich_manifest_module, "_GRAC_FREQUENCY_CACHE_DATA", None)
    monkeypatch.setattr(enrich_manifest_module, "_GRAC_FREQUENCY_CACHE_DIRTY", False)

    _prepare_cefr_estimates(
        conn,
        {"entries": [{"lemma": "вдома"}, {"lemma": "абетка"}, {"lemma": "бариста"}]},
    )

    assert _cefr(conn, "вдома") == {
        "level": "A1",
        "source": "estimated (GRAC frequency)",
        "text": "A1 (орієнтовно / estimated; GRAC 45.00/million, rank 1/3)",
    }


def test_cefr_puls_row_wins_over_grac_estimate(monkeypatch, tmp_path) -> None:
    conn = _conn()
    conn.execute(
        "INSERT INTO puls_cefr (word, level, pos, text) VALUES (?, ?, ?, ?)",
        ("вдома", "A2", "прислівник", "вдома (A2, прислівник)"),
    )
    cache_path = tmp_path / "grac_frequency.json"
    cache_path.write_text(
        json.dumps({"вдома": {"word": "вдома", "freq": 9000, "rel_freq": 45.0}}, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(enrich_manifest_module, "GRAC_FREQUENCY_CACHE", cache_path)
    monkeypatch.setattr(enrich_manifest_module, "_GRAC_FREQUENCY_CACHE_DATA", None)
    monkeypatch.setattr(enrich_manifest_module, "_GRAC_FREQUENCY_CACHE_DIRTY", False)

    _prepare_cefr_estimates(conn, {"entries": [{"lemma": "вдома"}]})

    assert _cefr(conn, "вдома") == {
        "level": "A2",
        "source": "PULS CEFR",
        "pos": "прислівник",
        "text": "вдома (A2, прислівник)",
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


def test_kaikki_stress_maps_ipa_primary_stress_to_lemma_vowel() -> None:
    lookup = {
        "україна": {
            "ipa": ["[ʊkrɐˈjinɐ]"],
            "etymology_text": "",
            "pos": ["name"],
            "glosses": [],
        }
    }

    stress = _kaikki_stress(lookup, "Україна")

    assert stress == {"form": "Украї́на", "source": KAIKKI_SOURCE, "ipa": "[ʊkrɐˈjinɐ]"}


def test_kaikki_stress_rejects_syllable_count_mismatch() -> None:
    lookup = {"тестовий": {"ipa": ["[ˈtɛst]"], "etymology_text": "", "pos": ["adj"], "glosses": []}}

    assert _kaikki_stress(lookup, "тестовий") is None


def test_kaikki_stress_marks_unambiguous_one_vowel_lemma() -> None:
    lookup = {
        "львів": {
            "ipa": ["[lʲʋʲiu̯]"],
            "etymology_text": "",
            "pos": ["name"],
            "glosses": [],
        }
    }

    assert _kaikki_stress(lookup, "Львів") == {"form": "Льві́в", "source": KAIKKI_SOURCE, "ipa": "[lʲʋʲiu̯]"}


def test_kaikki_meaning_uses_direct_glosses() -> None:
    lookup = {
        "абетка": {
            "ipa": [],
            "etymology_text": "",
            "pos": ["noun"],
            "glosses": ["alphabet", "alphabet"],
        }
    }

    assert _kaikki_meaning(lookup, "абетка") == {
        "definitions": ["alphabet"],
        "source": KAIKKI_SOURCE,
        "note": "English Wiktionary gloss fallback; direct per-lemma row.",
    }


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


def test_etymology_does_not_fall_back_to_derived_base_forms() -> None:
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
        ("добрий", "добрий", "Fixture etymology for добрий.", "https://goroh.example/добрий"),
    )

    assert _etymology(conn, "добре", {}) is None


def test_etymology_lookup_variants_include_normalised_apostrophe_and_v_u_alternates() -> None:
    variants = _etymology_lookup_variants("Ув’язнення")

    assert "ув'язнення" in variants
    assert "вв'язнення" in variants


def test_esum_etymology_uses_normalised_variant_match() -> None:
    conn = _conn()
    conn.execute(
        """
        CREATE TABLE esum_etymology (
            lemma TEXT NOT NULL,
            etymology_text TEXT NOT NULL,
            cognates TEXT DEFAULT '',
            vol TEXT DEFAULT '',
            page TEXT DEFAULT ''
        )
        """
    )
    conn.execute(
        "INSERT INTO esum_etymology VALUES (?, ?, ?, ?, ?)",
        ("ув'язнення", "Fixture ЕСУМ etymology for ув'язнення.", "[]", "1", "42"),
    )

    etymology = _etymology(conn, "Ув’язнення", {})

    assert etymology == {
        "text": "Fixture ЕСУМ etymology for ув'язнення.",
        "source": "ЕСУМ, т. 1, с. 42",
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


def test_kaikki_etymology_allows_direct_cognate_comparisons() -> None:
    conn = _conn()
    lookup = {
        "базовий": {
            "ipa": [],
            "etymology_text": "From ба́за. Compare Russian ба́зовый (bázovyj), Belarusian ба́завы.",
            "pos": ["adjective"],
        }
    }

    assert _etymology(conn, "базовий", lookup) == {
        "text": "From ба́за. Compare Russian ба́зовый (bázovyj), Belarusian ба́завы.",
        "source": KAIKKI_SOURCE,
    }


def test_kaikki_etymology_skips_garbled_tree_text() -> None:
    conn = _conn()
    lookup = {
        "японія": {
            "ipa": [],
            "etymology_text": "Etymology tree Hokkien 日本 bor. Ukrainian Японія.",
            "pos": ["name"],
        }
    }

    assert _etymology(conn, "Японія", lookup) is None


def test_kaikki_etymology_does_not_treat_labor_as_garbled_marker() -> None:
    conn = _conn()
    lookup = {
        "робота": {
            "ipa": [],
            "etymology_text": "Old East Slavic робота (robota, “labor, work”), itself from Proto-Slavic *orbota.",
            "pos": ["noun"],
        }
    }

    assert _etymology(conn, "робота", lookup) == {
        "text": "Old East Slavic робота (robota, “labor, work”), itself from Proto-Slavic *orbota.",
        "source": KAIKKI_SOURCE,
    }


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
    monkeypatch.setattr(enrich_manifest_module, "_prepare_cefr_estimates", lambda *args, **kwargs: None)
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


def test_enrich_populates_antonyms_phraseology_and_variant_etymology(monkeypatch, tmp_path) -> None:
    manifest_path = tmp_path / "manifest.json"
    db_path = tmp_path / "sources.sqlite"
    before = {
        "entries": [
            {
                "lemma": "Ув’язнення",
                "gloss": "imprisonment",
                "pos": "noun",
            }
        ]
    }
    manifest_path.write_text(json.dumps(before, ensure_ascii=False) + "\n", encoding="utf-8")
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE esum_etymology (
            lemma TEXT NOT NULL,
            etymology_text TEXT NOT NULL,
            cognates TEXT DEFAULT '',
            vol TEXT DEFAULT '',
            page TEXT DEFAULT ''
        );
        CREATE TABLE wiktionary (
            word TEXT NOT NULL,
            definitions TEXT DEFAULT '',
            synonyms TEXT DEFAULT '',
            antonyms TEXT DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            source TEXT DEFAULT ''
        );
        CREATE TABLE frazeolohichnyi (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL,
            definition TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            source TEXT DEFAULT ''
        );
        """
    )
    conn.execute(
        "INSERT INTO esum_etymology VALUES (?, ?, ?, ?, ?)",
        ("ув'язнення", "Fixture ЕСУМ etymology for ув'язнення.", "[]", "1", "42"),
    )
    conn.execute(
        "INSERT INTO wiktionary (word, antonyms) VALUES (?, ?)",
        ("Ув’язнення", json.dumps(["воля", "detention"], ensure_ascii=False)),
    )
    conn.execute(
        "INSERT INTO frazeolohichnyi (word, definition, text, source) VALUES (?, ?, ?, ?)",
        (
            "ув'язнення духу {{</fras>}}",
            "ув'язнення духу. Обмеження внутрішньої свободи.",
            "ув'язнення духу: Обмеження внутрішньої свободи.",
            "Фразеологічний словник",
        ),
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(enrich_manifest_module, "MANIFEST", manifest_path)
    monkeypatch.setattr(enrich_manifest_module, "SOURCES_DB", db_path)
    monkeypatch.setattr(enrich_manifest_module, "_load_kaikki_lookup", lambda: {})
    monkeypatch.setattr(enrich_manifest_module, "_slovnyk_cache", lambda lemma: {"lookups": {}})
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
    monkeypatch.setattr(enrich_manifest_module, "_prepare_cefr_estimates", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_cefr", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_morphology", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_meaning", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_literary_attestation", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_translation", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        enrich_manifest_module,
        "_vesum_word_analyses",
        lambda word: ((word, "noun"),) if word in {"воля", "ув'язнення"} else (),
    )

    assert enrich_manifest_module.enrich() == (1, 1)

    enriched = json.loads(manifest_path.read_text(encoding="utf-8"))["entries"][0]
    print("UNIT SAMPLE before sections:", before["entries"][0].get("sections"))
    print("UNIT SAMPLE after sections:", json.dumps(enriched.get("sections"), ensure_ascii=False, sort_keys=True))
    print("UNIT SAMPLE after etymology:", json.dumps(enriched["enrichment"]["etymology"], ensure_ascii=False))

    assert enriched["sections"]["antonyms"]["items"] == ["воля"]
    assert enriched["sections"]["idioms"]["items"][0]["phrase"] == "ув'язнення духу"
    assert enriched["enrichment"]["etymology"] == {
        "text": "Fixture ЕСУМ etymology for ув'язнення.",
        "source": "ЕСУМ, т. 1, с. 42",
    }


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


def test_parse_translations_cleans_dmklinger_meta_glosses() -> None:
    raw = json.dumps(
        [
            "Alternative form of кабачо́к: zucchini",
            "plain translation",
            "common misspelling of Строго́нівка (Strohónivka)",
        ]
    )

    assert _parse_translations(raw) == ["zucchini", "plain translation"]


def test_translation_returns_none_when_lemma_absent(monkeypatch) -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE dmklinger_uk_en (word TEXT, pos TEXT, translations TEXT)")
    monkeypatch.setattr(enrich_manifest_module, "_DMKLINGER_INDEX", None)
    monkeypatch.setattr(enrich_manifest_module, "_BALLA_REVERSE_INDEX", {})

    assert _translation(conn, "неіснуючеслово") is None


def test_translation_uses_unambiguous_reverse_balla_after_source_misses(monkeypatch) -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE dmklinger_uk_en (word TEXT, pos TEXT, translations TEXT)")
    conn.execute("CREATE TABLE balla_en_uk (word TEXT, definition TEXT, text TEXT)")
    conn.execute(
        "INSERT INTO balla_en_uk (word, definition, text) VALUES (?, ?, ?)",
        ("stir", "v 1) мішати, помішувати, розмішувати; збовтувати", ""),
    )
    monkeypatch.setattr(enrich_manifest_module, "_DMKLINGER_INDEX", None)
    monkeypatch.setattr(enrich_manifest_module, "_BALLA_REVERSE_INDEX", {})
    _patch_vesum_analyses(monkeypatch, {"помішувати": "verb"})

    assert _translation(conn, "помішувати", {}, entry_pos="verb") is None
    assert _translation(conn, "помішувати", {}, entry_pos="verb", gloss_hints={"stir"}) == {
        "en": ["stir"],
        "source": _BALLA_REVERSE_SOURCE,
        "note": (
            "Reverse lookup from an exact Ukrainian token in Балла EN→UK, "
            "validated by the source learner gloss; skipped when ambiguous."
        ),
    }


def test_translation_skips_ambiguous_reverse_balla(monkeypatch) -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE dmklinger_uk_en (word TEXT, pos TEXT, translations TEXT)")
    conn.execute("CREATE TABLE balla_en_uk (word TEXT, definition TEXT, text TEXT)")
    conn.executemany(
        "INSERT INTO balla_en_uk (word, definition, text) VALUES (?, ?, ?)",
        [
            ("mix", "v змішувати, помішувати", ""),
            ("stir", "v мішати, помішувати", ""),
        ],
    )
    monkeypatch.setattr(enrich_manifest_module, "_DMKLINGER_INDEX", None)
    monkeypatch.setattr(enrich_manifest_module, "_BALLA_REVERSE_INDEX", {})
    _patch_vesum_analyses(monkeypatch, {"помішувати": "verb"})

    assert (
        _translation(conn, "помішувати", {}, entry_pos="verb", gloss_hints={"mix", "stir"})
        is None
    )


def test_translation_prefers_kaikki_over_reverse_balla(monkeypatch) -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE dmklinger_uk_en (word TEXT, pos TEXT, translations TEXT)")
    conn.execute("CREATE TABLE balla_en_uk (word TEXT, definition TEXT, text TEXT)")
    conn.execute(
        "INSERT INTO balla_en_uk (word, definition, text) VALUES (?, ?, ?)",
        ("stir", "v помішувати", ""),
    )
    monkeypatch.setattr(enrich_manifest_module, "_DMKLINGER_INDEX", None)
    monkeypatch.setattr(enrich_manifest_module, "_BALLA_REVERSE_INDEX", {})
    _patch_vesum_analyses(monkeypatch, {"помішувати": "verb"})

    assert _translation(conn, "помішувати", {"помішувати": {"glosses": ["to stir"]}}) == {
        "en": ["to stir"],
        "source": KAIKKI_SOURCE,
    }


def test_translation_reverse_balla_ignores_example_sentences(monkeypatch) -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE dmklinger_uk_en (word TEXT, pos TEXT, translations TEXT)")
    conn.execute("CREATE TABLE balla_en_uk (word TEXT, definition TEXT, text TEXT)")
    conn.execute(
        "INSERT INTO balla_en_uk (word, definition, text) VALUES (?, ?, ?)",
        ("dash", "v he ~ed the book on the floor — він шпурнув книгу додолу", ""),
    )
    monkeypatch.setattr(enrich_manifest_module, "_DMKLINGER_INDEX", None)
    monkeypatch.setattr(enrich_manifest_module, "_BALLA_REVERSE_INDEX", {})
    _patch_vesum_analyses(monkeypatch, {"книга": "noun"})

    assert _translation(conn, "книга", {}, entry_pos="noun", gloss_hints={"dash"}) is None


def test_translation_reverse_balla_requires_single_token_segment(monkeypatch) -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE dmklinger_uk_en (word TEXT, pos TEXT, translations TEXT)")
    conn.execute("CREATE TABLE balla_en_uk (word TEXT, definition TEXT, text TEXT)")
    conn.execute(
        "INSERT INTO balla_en_uk (word, definition, text) VALUES (?, ?, ?)",
        ("home", "n 1) дім 2) порт базування", ""),
    )
    monkeypatch.setattr(enrich_manifest_module, "_DMKLINGER_INDEX", None)
    monkeypatch.setattr(enrich_manifest_module, "_BALLA_REVERSE_INDEX", {})
    _patch_vesum_analyses(monkeypatch, {"базування": "noun", "дім": "noun"})

    assert _translation(conn, "базування", {}, entry_pos="noun", gloss_hints={"home"}) is None
    assert _translation(conn, "дім", {}, entry_pos="noun", gloss_hints={"home"}) == {
        "en": ["home"],
        "source": _BALLA_REVERSE_SOURCE,
        "note": (
            "Reverse lookup from an exact Ukrainian token in Балла EN→UK, "
            "validated by the source learner gloss; skipped when ambiguous."
        ),
    }


def test_surface_gloss_hints_skip_noun_normalization() -> None:
    entry = {
        "lemma": "вершок",
        "atlas_normalizations": [
            {
                "reason": (
                    "VESUM: inflected surface «вершки» (surface gloss='cream', "
                    "pos='noun:pl') folded into a NEWLY-CREATED lemma page «вершок»."
                )
            }
        ],
    }

    assert _surface_gloss_hints(entry) == set()


def test_translation_uses_curated_learner_gloss_after_source_misses(monkeypatch) -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE dmklinger_uk_en (word TEXT, pos TEXT, translations TEXT)")
    monkeypatch.setattr(enrich_manifest_module, "_DMKLINGER_INDEX", None)
    monkeypatch.setattr(enrich_manifest_module, "_BALLA_REVERSE_INDEX", {})

    assert _translation(conn, "ого", {}) == {
        "en": ["wow", "whoa"],
        "source": "curated learner gloss",
    }


def test_translation_uses_slovnyk_ukreng_after_source_misses(monkeypatch) -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE dmklinger_uk_en (word TEXT, pos TEXT, translations TEXT)")
    monkeypatch.setattr(enrich_manifest_module, "_DMKLINGER_INDEX", None)
    monkeypatch.setattr(enrich_manifest_module, "_BALLA_REVERSE_INDEX", {})
    cache = {
        "lookups": {
            "ukreng": {
                "dictionary_slug": "ukreng",
                "dictionary_label": "Українсько-англійський словник",
                "word": "наголос",
                "source_url": "https://slovnyk.me/dict/ukreng/наголос",
                "text": (
                    "наголос 1) лінгв. accent, stress; (перен. тж.) emphasis "
                    "наголос падає на другий склад — stress on the second syllable. "
                    "Джерело: Українсько-англійський словник на Slovnyk.me"
                ),
            }
        }
    }

    assert _translation(conn, "наголос", {}, slovnyk_cache=cache) == {
        "en": ["accent", "stress", "emphasis"],
        "source": _SLOVNYK_UKRENG_SOURCE,
        "source_url": "https://slovnyk.me/dict/ukreng/наголос",
    }


def test_translation_parses_slovnyk_ukreng_plural_label(monkeypatch) -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE dmklinger_uk_en (word TEXT, pos TEXT, translations TEXT)")
    monkeypatch.setattr(enrich_manifest_module, "_DMKLINGER_INDEX", None)
    monkeypatch.setattr(enrich_manifest_module, "_BALLA_REVERSE_INDEX", {})
    cache = {
        "lookups": {
            "ukreng": {
                "dictionary_slug": "ukreng",
                "dictionary_label": "Українсько-англійський словник",
                "word": "бризки",
                "source_url": "https://slovnyk.me/dict/ukreng/бризки",
                "text": (
                    "бризки мн. splashes ( pl. ), spray ( sg. ); "
                    "( розплавленого металу ) sparks ( pl. ); "
                    "( дощу ) fine drops of rain "
                    "Джерело: Українсько-англійський словник на Slovnyk.me"
                ),
            }
        }
    }

    assert _translation(conn, "бризки", {}, slovnyk_cache=cache) == {
        "en": ["splashes", "spray"],
        "source": _SLOVNYK_UKRENG_SOURCE,
        "source_url": "https://slovnyk.me/dict/ukreng/бризки",
    }


def test_translation_prefers_kaikki_over_curated_learner_gloss(monkeypatch) -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE dmklinger_uk_en (word TEXT, pos TEXT, translations TEXT)")
    monkeypatch.setattr(enrich_manifest_module, "_DMKLINGER_INDEX", None)
    monkeypatch.setattr(enrich_manifest_module, "_BALLA_REVERSE_INDEX", {})

    assert _translation(conn, "ого", {"ого": {"glosses": ["oh wow"]}}) == {
        "en": ["oh wow"],
        "source": KAIKKI_SOURCE,
    }


def test_wiki_reference_success(monkeypatch, tmp_path) -> None:
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

    monkeypatch.setattr(enrich_manifest_module, "WIKI_REFERENCE_CACHE", tmp_path / "wiki_reference.json")
    monkeypatch.setattr(enrich_manifest_module, "_WIKI_REFERENCE_CACHE_DATA", None)
    monkeypatch.setattr(enrich_manifest_module, "_WIKI_REFERENCE_CACHE_DIRTY", False)
    monkeypatch.setattr(enrich_manifest_module, "query_wikipedia", mock_query)

    # test without literary attestation
    ref = enrich_manifest_module._wiki_reference("Україна")
    assert ref is not None
    assert ref["wikipedia"]["title"] == "Україна"
    assert ref["wikipedia"]["summary"] == "Україна — держава в Східній Європі."
    assert ref["wikipedia"]["url"] == "https://uk.wikipedia.org/wiki/Україна"
    assert _url_hostname(ref["wiktionary_url"]) == "uk.wiktionary.org"
    assert _url_hostname("https://uk.wiktionary.org.attacker.example/wiki/Україна") != "uk.wiktionary.org"
    assert ref["wikisource_url"] is None

    # test with literary attestation
    ref_with_lit = enrich_manifest_module._wiki_reference("Україна", {"text": "some excerpt"})
    assert ref_with_lit is not None
    assert ref_with_lit["wikisource_url"] is not None
    assert _url_hostname(ref_with_lit["wikisource_url"]) == "uk.wikisource.org"


def test_proper_noun_wikipedia_meaning_uses_one_line_cached_gloss(monkeypatch, tmp_path) -> None:
    fake_wiki_data = {
        "title": "Штати",
        "extract": "Сполучені Штати Америки — держава в Північній Америці. Друге речення не входить.",
        "url": "https://uk.wikipedia.org/wiki/Сполучені_Штати_Америки",
    }

    def mock_query(title: str) -> dict | None:
        if title == "Штати":
            return fake_wiki_data
        return None

    monkeypatch.setattr(enrich_manifest_module, "WIKI_REFERENCE_CACHE", tmp_path / "wiki_reference.json")
    monkeypatch.setattr(enrich_manifest_module, "_WIKI_REFERENCE_CACHE_DATA", None)
    monkeypatch.setattr(enrich_manifest_module, "_WIKI_REFERENCE_CACHE_DIRTY", False)
    monkeypatch.setattr(enrich_manifest_module, "query_wikipedia", mock_query)

    assert _proper_noun_wikipedia_meaning("Штати") == {
        "definitions": ["Сполучені Штати Америки — держава в Північній Америці."],
        "source": "Вікіпедія",
    }


def test_wiki_reference_missing(monkeypatch, tmp_path) -> None:
    def mock_query(title: str) -> dict | None:
        return None

    monkeypatch.setattr(enrich_manifest_module, "WIKI_REFERENCE_CACHE", tmp_path / "wiki_reference.json")
    monkeypatch.setattr(enrich_manifest_module, "_WIKI_REFERENCE_CACHE_DATA", None)
    monkeypatch.setattr(enrich_manifest_module, "_WIKI_REFERENCE_CACHE_DIRTY", False)
    monkeypatch.setattr(enrich_manifest_module, "query_wikipedia", mock_query)

    ref = enrich_manifest_module._wiki_reference("варити")
    assert ref is None


def test_wiki_reference_uses_disk_cache(monkeypatch, tmp_path) -> None:
    cache_path = tmp_path / "wiki_reference.json"
    fake_wiki_data = {
        "title": "Україна",
        "extract": "Україна — держава в Східній Європі.",
        "url": "https://uk.wikipedia.org/wiki/Україна",
    }
    calls: list[str] = []

    def mock_query(title: str) -> dict | None:
        calls.append(title)
        return fake_wiki_data

    monkeypatch.setattr(enrich_manifest_module, "WIKI_REFERENCE_CACHE", cache_path)
    monkeypatch.setattr(enrich_manifest_module, "_WIKI_REFERENCE_CACHE_DATA", None)
    monkeypatch.setattr(enrich_manifest_module, "_WIKI_REFERENCE_CACHE_DIRTY", False)
    monkeypatch.setattr(enrich_manifest_module, "query_wikipedia", mock_query)

    first = enrich_manifest_module._wiki_reference("Україна")

    assert first is not None
    assert calls == ["Україна"]
    assert json.loads(cache_path.read_text(encoding="utf-8")) == {"Україна": fake_wiki_data}

    monkeypatch.setattr(enrich_manifest_module, "_WIKI_REFERENCE_CACHE_DATA", None)

    def fail_query(title: str) -> dict | None:
        raise AssertionError(f"live query should not run for cached title: {title}")

    monkeypatch.setattr(enrich_manifest_module, "query_wikipedia", fail_query)

    second = enrich_manifest_module._wiki_reference("Україна")

    assert second == first


def test_wiki_reference_caches_missing_results(monkeypatch, tmp_path) -> None:
    cache_path = tmp_path / "wiki_reference.json"
    calls: list[str] = []

    def mock_query(title: str) -> dict | None:
        calls.append(title)
        return None

    monkeypatch.setattr(enrich_manifest_module, "WIKI_REFERENCE_CACHE", cache_path)
    monkeypatch.setattr(enrich_manifest_module, "_WIKI_REFERENCE_CACHE_DATA", None)
    monkeypatch.setattr(enrich_manifest_module, "_WIKI_REFERENCE_CACHE_DIRTY", False)
    monkeypatch.setattr(enrich_manifest_module, "query_wikipedia", mock_query)

    assert enrich_manifest_module._wiki_reference("варити") is None
    assert calls == ["варити"]
    assert json.loads(cache_path.read_text(encoding="utf-8")) == {"варити": None}

    monkeypatch.setattr(enrich_manifest_module, "_WIKI_REFERENCE_CACHE_DATA", None)

    def fail_query(title: str) -> dict | None:
        raise AssertionError(f"live query should not run for cached miss: {title}")

    monkeypatch.setattr(enrich_manifest_module, "query_wikipedia", fail_query)

    assert enrich_manifest_module._wiki_reference("варити") is None


# --- «див.» cross-reference resolution (issue #4220) ------------------------


def _sum11_conn(rows: dict[str, str]) -> sqlite3.Connection:
    """In-memory conn whose sum11 table holds {word: definition} — deterministic,
    no network, for exercising _sum11_definition_card's xref resolution."""
    conn = _conn()
    conn.executemany(
        "INSERT INTO sum11(word, definition) VALUES(?, ?)",
        list(rows.items()),
    )
    return conn


def test_xref_target_lemmas_detects_cross_reference_only() -> None:
    # Bare «див. X» (with a stressed headword echo) → the target lemma, destressed.
    assert _xref_target_lemmas("захова́ти див. заховувати .", "заховати") == ["заховувати"]
    # Uppercase headword echo + stressed target (СУМ-20 shape).
    assert _xref_target_lemmas("ВБЛАГА́ТИ див. ублага́ти .", "вблагати") == ["ублагати"]
    # No headword echo at all.
    assert _xref_target_lemmas("див. святий .", "свят") == ["святий"]
    # Multiple comma-separated targets, in order.
    assert _xref_target_lemmas("x див. заховувати, ховати .", "x") == ["заховувати", "ховати"]


def test_xref_target_lemmas_fail_closed_on_real_definitions() -> None:
    # A genuine definition that merely starts with the headword is NOT a xref.
    assert _xref_target_lemmas("ХОВА́ТИ 1. Класти що-небудь у таємному місці.", "ховати") == []
    # «пор.» (compare) is a different marker — not a definition substitute.
    assert _xref_target_lemmas("порівняй заховувати", "заховати") == []
    # A sentence trailing «див.» exceeds the target cap → left alone (fail-closed).
    assert _xref_target_lemmas("див. класти що-небудь у певне таємне місце", "x") == []
    # Real text BEFORE «див.» (unexpected token in the pre-region) → not xref-only.
    assert _xref_target_lemmas("щось інше зовсім див. заховувати", "заховати") == []
    assert _xref_target_lemmas("", "заховати") == []


def test_verb_aspect_reads_vesum_tags() -> None:
    # VESUM-backed: perfective vs imperfective infinitives (data/vesum.db).
    assert _verb_aspect("заховати") == "perf"
    assert _verb_aspect("заховувати") == "imperf"
    assert _verb_aspect("підбігти") == "perf"
    assert _verb_aspect("підбігати") == "imperf"
    # Non-verb / unknown → None (no aspect claim).
    assert _verb_aspect("святий") is None
    assert _verb_aspect("щqz-not-a-word") is None


def test_xref_provenance_prefix_renders_aspect_pair() -> None:
    # Perfective lemma glossed by its imperfective → standard «докон. до X» form.
    assert _xref_provenance_prefix("заховати", "заховувати") == "(докон. до заховувати / див. заховувати) "
    # Imperfective → perfective would render «недок. до X».
    assert _xref_provenance_prefix("заховувати", "заховати") == "(недок. до заховати / див. заховати) "
    # No aspect pair (non-verb cross-ref) → keep only the visible cross-reference.
    assert _xref_provenance_prefix("свят", "святий") == "(див. святий) "


def test_sum11_definition_card_resolves_cross_reference_one_level() -> None:
    target_def = "Класти що-небудь у таємному місці, щоб ніхто не міг знайти."
    conn = _sum11_conn({"заховати": "заховати див. заховувати", "заховувати": target_def})
    card = _sum11_definition_card(conn, "заховати", has_sum11_flags=True)
    assert card is not None
    # Verbatim target body, prefixed with the honest aspect+cross-ref provenance note.
    assert card["definitions"] == [f"(докон. до заховувати / див. заховувати) {target_def}"]
    assert card["cross_reference"] == {"raw": "заховати див. заховувати", "target": "заховувати"}


def test_sum11_definition_card_resolves_inflected_target() -> None:
    # Cross-ref points at an inflected form (ховаєш) → VESUM-lemmatize to ховати.
    target_def = "Класти що-небудь у таємному місці."
    conn = _sum11_conn({"назахову": "назахову див. ховаєш", "ховати": target_def})
    card = _sum11_definition_card(conn, "назахову", has_sum11_flags=True)
    assert card is not None
    assert card["cross_reference"]["target"] == "ховати"
    assert card["definitions"][0].endswith(target_def)


def test_sum11_definition_card_refuses_cross_reference_chain() -> None:
    # target ужалити is ITSELF a «див.» → one level only, refuse the chain.
    conn = _sum11_conn({"вжалити": "вжалити див. ужалити", "ужалити": "ужалити див. жалити"})
    card = _sum11_definition_card(conn, "вжалити", has_sum11_flags=True)
    assert card is not None
    assert card["definitions"] == ["вжалити див. ужалити"]
    assert "cross_reference" not in card


def test_sum11_definition_card_leaves_absent_target_unresolved() -> None:
    # Target ублагати not in the source → fail-closed, no invented gloss.
    conn = _sum11_conn({"вблагати": "вблагати див. ублагати"})
    card = _sum11_definition_card(conn, "вблагати", has_sum11_flags=True)
    assert card is not None
    assert card["definitions"] == ["вблагати див. ублагати"]
    assert "cross_reference" not in card


def test_sum11_definition_card_ordinary_lemma_byte_identical() -> None:
    # Regression: a normal, non-«див.» card is untouched — resolve on/off identical.
    conn = _sum11_conn({"ховати": "Класти що-небудь у таємному місці."})
    resolved = _sum11_definition_card(conn, "ховати", has_sum11_flags=True)
    plain = _sum11_definition_card(conn, "ховати", has_sum11_flags=True, resolve_xref=False)
    assert resolved == plain
    assert "cross_reference" not in resolved


def test_resolve_definition_xref_uses_same_source_fetcher() -> None:
    # The fetcher must be called with the (lemmatized) target and only once here.
    calls: list[str] = []

    def fetch_target(target: str):
        calls.append(target)
        return {"source": "ВТС", "definitions": ["Реальне тлумачення слова."]}

    card = {"source": "ВТС", "definitions": ["захова́ти див. заховувати ."]}
    resolved = _resolve_definition_xref(card, "заховати", fetch_target)
    assert calls == ["заховувати"]
    assert resolved is not None
    assert resolved["definitions"][0].endswith("Реальне тлумачення слова.")
    # A non-cross-reference card yields None and never calls the fetcher.
    calls.clear()
    assert _resolve_definition_xref({"source": "ВТС", "definitions": ["1. Справжнє тлумачення."]}, "х", fetch_target) is None
    assert calls == []


def test_vts_definition_card_resolves_cross_reference_live_shape(monkeypatch) -> None:
    # Exercise the real shipping path (_vts_definition_card) with a stubbed
    # slovnyk fetch: source card is «див. X», target card is a real definition.
    rows = {
        "заховати": {
            "word": "заховати",
            "text": "заховати захова́ти див. заховувати . Джерело: Великий тлумачний словник",
            "source_url": "https://slovnyk.me/dict/vts/заховати",
        },
        "заховувати": {
            "word": "заховувати",
            "text": "заховувати захо́вувати -ую, -уєш, недок. Класти що-небудь у невідоме місце.",
            "source_url": "https://slovnyk.me/dict/vts/заховувати",
        },
    }

    def fake_fetch(lemma: str, lookup_word: str, slug: str):
        assert slug == "vts"
        return rows.get(lemma)

    monkeypatch.setattr(enrich_manifest_module, "_fetch_slovnyk_entry", fake_fetch)
    monkeypatch.setattr(enrich_manifest_module, "_slovnyk_base_row", lambda base, slug: None)

    card = _vts_definition_card("заховати")
    assert card is not None
    assert card["source"] == "ВТС"
    assert card["definitions"][0].startswith("(докон. до заховувати / див. заховувати) ")
    assert card["definitions"][0].endswith("Класти що-небудь у невідоме місце.")
    assert card["cross_reference"]["target"] == "заховувати"
