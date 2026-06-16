import json
from pathlib import Path

from scripts.lexicon.build_kaikki_lookup import (
    _clean_gloss,
    build_lookup,
    extract_glosses,
    lookup_key,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_lookup_key_strips_stress_and_lowercases() -> None:
    assert lookup_key("А́втобус") == "автобус"


def test_clean_gloss_keeps_real_translations() -> None:
    # plain translations pass through untouched
    assert _clean_gloss("water") == "water"
    assert _clean_gloss("railway, railroad") == "railway, railroad"
    assert _clean_gloss("to calculate, to compute, to figure out") == (
        "to calculate, to compute, to figure out"
    )
    # single grammatical-looking word that is a real translation survives
    assert _clean_gloss("present") == "present"
    assert _clean_gloss("plural") == "plural"


def test_clean_gloss_drops_pure_grammatical_form_glosses() -> None:
    # bare inflected-form descriptors (no "of <lemma>" tail) are NOT translations
    assert _clean_gloss("accusative singular") == ""
    assert _clean_gloss("vocative singular") == ""
    assert _clean_gloss("nominative plural") == ""
    assert _clean_gloss("inanimate accusative plural") == ""
    assert _clean_gloss("nominative/vocative plural") == ""
    assert _clean_gloss("nominative/accusative/vocative plural") == ""


def test_clean_gloss_strips_meta_clause_keeps_translation() -> None:
    assert _clean_gloss("one can, one may, alternative form of мо́жна (móžna)") == (
        "one can, one may"
    )
    assert _clean_gloss("Alternative form of кабачо́к: zucchini") == "zucchini"
    assert _clean_gloss("what, alternative form of що (ščo)") == "what"
    assert _clean_gloss("a male patronymic; obsolete form of І́горьович") == (
        "a male patronymic"
    )
    assert _clean_gloss("to wash up, passive of вмива́ти (vmyváty)") == "to wash up"
    # pure meta drops entirely
    assert _clean_gloss("common misspelling of Строго́нівка (Strohónivka)") == ""


def test_extract_glosses_filters_form_entries() -> None:
    # an inflected-form entry yields no translation glosses
    entry = {"senses": [{"glosses": ["accusative singular", "vocative singular"]}]}
    assert extract_glosses(entry) == []
    # a real lemma keeps its translation, drops the meta sense
    entry2 = {
        "senses": [
            {"glosses": ["to wash up"]},
            {"glosses": ["passive of вмива́ти (vmyváty)"]},
        ]
    }
    assert extract_glosses(entry2) == ["to wash up"]


def test_build_lookup_aggregates_ipa_etymology_and_pos(tmp_path: Path) -> None:
    raw = tmp_path / "kaikki-uk.jsonl"
    _write_jsonl(
        raw,
        [
            {
                "word": "соба́ка",
                "lang_code": "uk",
                "pos": "noun",
                "etymology_text": "Inherited from Proto-Slavic.",
                "sounds": [{"ipa": "[sɔˈbakɐ]"}],
                "senses": [{"glosses": ["dog"]}],
            },
            {
                "word": "собака",
                "lang_code": "uk",
                "pos": "noun",
                "etymology_text": "Borrowed note from a second line.",
                "sounds": [{"ipa": "[soˈbɑkɐ]"}, {"ipa": "[sɔˈbakɐ]"}],
                "senses": [{"glosses": []}],
            },
            {
                "word": "добрий день",
                "lang_code": "uk",
                "pos": "phrase",
                "sounds": [{"ipa": "[ˈdɔbrɪj dɛnʲ]"}],
            },
            {
                "word": "кіт",
                "lang_code": "en",
                "pos": "noun",
                "sounds": [{"ipa": "[kʲit]"}],
            },
        ],
    )

    lookup = build_lookup(raw)

    assert list(lookup) == ["собака"]
    assert lookup["собака"]["ipa"] == ["[sɔˈbakɐ]", "[soˈbɑkɐ]"]
    assert lookup["собака"]["pos"] == ["noun"]
    assert lookup["собака"]["etymology_text"] == (
        "Inherited from Proto-Slavic.\n\nBorrowed note from a second line."
    )
