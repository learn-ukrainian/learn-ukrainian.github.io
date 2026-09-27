"""Synonym-pair emission gates (#8714).

Every emitted synonym item must pair true synonyms in the displayed sense,
with the same part of speech, never an aspect or reflexive pair, and with
distractors that are not themselves accepted answers.  Each fixture below
reproduces one example quoted in the issue; the assertions fail on the
pre-#8714 generator and pass afterwards.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit.generate_practice_deck import (
    BuildConfig,
    JsonVesumVerifier,
    ReviewedSourceAllowlist,
    build_practice_shards,
    validate_mode_items,
    validate_synonym_option_sets,
)


def _entry(
    lemma: str,
    pos: str,
    gloss: str,
    *,
    en: list[str] | None = None,
    level: str = "B1",
    aspect_partner: str | None = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "lemma": lemma,
        "url_slug": lemma,
        "gloss": gloss,
        "pos": pos,
        "primary_source": "course_vocab",
        "course_usage": [{"track": level.lower(), "slug": f"{level.lower()}-synonyms"}],
        "enrichment": {
            "cefr": {"level": level},
            "translation": {"en": list(en) if en is not None else [gloss], "source": "fixture", "pos": pos},
        },
    }
    if aspect_partner:
        entry["enrichment"]["verb_pedagogy"] = {"aspect_partner": {"lemma": aspect_partner, "source": "fixture"}}
    return entry


_NOUN_FILLERS = [
    _entry("книга", "noun", "book"),
    _entry("стіл", "noun", "table"),
    _entry("вікно", "noun", "window"),
    _entry("місто", "noun", "city"),
    _entry("ріка", "noun", "river"),
]
_VERB_FILLERS = [
    _entry("читати", "verb", "read", en=["to read"]),
    _entry("писати", "verb", "write", en=["to write"]),
    _entry("спати", "verb", "sleep", en=["to sleep"]),
    _entry("малювати", "verb", "draw", en=["to draw"]),
]
_ADJ_FILLERS = [
    _entry("старий", "adj", "old"),
    _entry("новий", "adj", "new"),
    _entry("чистий", "adj", "clean"),
    _entry("теплий", "adj", "warm"),
]
_ADV_FILLERS = [
    _entry("повільно", "adverb", "slowly"),
    _entry("тихо", "adverb", "quietly"),
    _entry("голосно", "adverb", "loudly"),
    _entry("рано", "adverb", "early"),
]
_CONJ_FILLERS = [
    _entry("щоб", "conj", "so that"),
    _entry("ніж", "conj", "than"),
    _entry("поки", "conj", "while"),
    _entry("бо", "conj", "because"),
    _entry("якщо", "conj", "if"),
]

_VESUM_VERBS = {
    "кидати": [{"lemma": "кидати", "pos": "verb", "tags": "verb:imperf:inf"}],
    "кинути": [{"lemma": "кинути", "pos": "verb", "tags": "verb:perf:inf"}],
    "жбурляти": [{"lemma": "жбурляти", "pos": "verb", "tags": "verb:imperf:inf"}],
    "вітати": [{"lemma": "вітати", "pos": "verb", "tags": "verb:imperf:inf"}],
    "вітатися": [{"lemma": "вітатися", "pos": "verb", "tags": "verb:rev:imperf:inf"}],
    "говорити": [{"lemma": "говорити", "pos": "verb", "tags": "verb:imperf:inf"}],
    "базікати": [{"lemma": "базікати", "pos": "verb", "tags": "verb:imperf:inf"}],
    "балакати": [{"lemma": "балакати", "pos": "verb", "tags": "verb:imperf:inf"}],
    "читати": [{"lemma": "читати", "pos": "verb", "tags": "verb:imperf:inf"}],
    "писати": [{"lemma": "писати", "pos": "verb", "tags": "verb:imperf:inf"}],
    "спати": [{"lemma": "спати", "pos": "verb", "tags": "verb:imperf:inf"}],
    "малювати": [{"lemma": "малювати", "pos": "verb", "tags": "verb:imperf:inf"}],
}


def _approved(a: str, b: str, *, sources: list[str] | None = None, polarity: str = "synonym") -> dict[str, Any]:
    return {"a": a, "b": b, "polarity": polarity, "sources": ["synonyms"] if sources is None else sources}


def _synonym_items(manifest: list[dict[str, Any]], approved: list[dict[str, Any]]) -> list[dict[str, Any]]:
    shards = build_practice_shards(
        manifest,
        ReviewedSourceAllowlist.from_payload([]),
        JsonVesumVerifier(_VESUM_VERBS),
        cloze_sources=None,
        config=BuildConfig(target=200),
        synonym_verdicts={"approved": approved, "rejected": []},
    )
    return [item for level in shards for item in shards[level].get("synonym", {}).get("synonym", [])]


def _pairs(items: list[dict[str, Any]]) -> set[tuple[str, str]]:
    return {(item["prompt"], item["answer"]) for item in items}


def test_wrong_sense_pair_is_withheld() -> None:
    # Issue example syn_47451f934c94: депресія → розклад (B1).  Both are nouns and the
    # synonym dictionary co-lists them in the economic-decline sense, but the displayed
    # sense of депресія is "depression" and розклад never translates to it.
    manifest = [
        _entry("депресія", "noun", "depression", en=["depression (psychology: state of mind)"]),
        _entry("розклад", "noun", "schedule", en=["schedule, timetable", "decomposition"]),
        *_NOUN_FILLERS,
    ]
    items = _synonym_items(manifest, [_approved("депресія", "розклад")])
    assert _pairs(items) == set(), _pairs(items)


def test_sense_support_is_directional() -> None:
    # але (displayed "but") → однак is supported because однак translates to "but";
    # однак (displayed "however") → але is not, because але never means "however".
    manifest = [
        _entry("але", "conj", "but"),
        _entry("однак", "conj", "however", en=["however, but"]),
        *_CONJ_FILLERS,
    ]
    items = _synonym_items(manifest, [_approved("але", "однак")])
    assert _pairs(items) == {("але", "однак")}, _pairs(items)


def test_aspect_pair_is_withheld_but_same_aspect_synonym_ships() -> None:
    # Issue example syn_542704e10746: кидати → кинути (perfective partner, not a synonym).
    manifest = [
        _entry("кидати", "verb", "throw", en=["to throw"], aspect_partner="кинути"),
        _entry("кинути", "verb", "throw", en=["to throw"], aspect_partner="кидати"),
        _entry("жбурляти", "verb", "throw, hurl", en=["to throw", "to hurl"]),
        *_VERB_FILLERS,
    ]
    items = _synonym_items(manifest, [_approved("кидати", "кинути"), _approved("кидати", "жбурляти")])
    pairs = _pairs(items)
    assert ("кидати", "кинути") not in pairs and ("кинути", "кидати") not in pairs, pairs
    assert ("кидати", "жбурляти") in pairs, pairs


def test_aspect_pair_is_withheld_on_vesum_tags_alone() -> None:
    # No Atlas aspect-partner link: VESUM ``imperf``/``perf`` tags alone must decide.
    manifest = [
        _entry("кидати", "verb", "throw", en=["to throw"]),
        _entry("кинути", "verb", "throw", en=["to throw"]),
        *_VERB_FILLERS,
    ]
    items = _synonym_items(manifest, [_approved("кидати", "кинути")])
    assert _pairs(items) == set(), _pairs(items)


def test_reflexive_pair_is_withheld() -> None:
    # Issue example: вітатися → вітати (reflexive/active pair with different meanings).
    manifest = [
        _entry("вітати", "verb", "greet", en=["to greet"]),
        _entry("вітатися", "verb", "greet", en=["to greet (each other)", "to say hello"]),
        *_VERB_FILLERS,
    ]
    items = _synonym_items(manifest, [_approved("вітати", "вітатися")])
    assert _pairs(items) == set(), _pairs(items)


def test_cross_pos_pair_is_withheld() -> None:
    # Issue example: високий (adj) → високо (adverb).
    manifest = [
        _entry("високий", "adj", "high, tall"),
        _entry("високо", "adverb", "high, highly"),
        *_ADJ_FILLERS,
        *_ADV_FILLERS,
    ]
    items = _synonym_items(manifest, [_approved("високий", "високо")])
    assert _pairs(items) == set(), _pairs(items)


def test_spelling_variant_is_withheld() -> None:
    # Issue example: учитель → вчитель is an euphonic spelling variant, not a synonym.
    manifest = [
        _entry("учитель", "noun", "teacher"),
        _entry("вчитель", "noun", "teacher"),
        *_NOUN_FILLERS,
    ]
    items = _synonym_items(manifest, [_approved("учитель", "вчитель")])
    assert _pairs(items) == set(), _pairs(items)


def test_pair_without_dictionary_source_is_withheld() -> None:
    manifest = [
        _entry("швидко", "adverb", "quickly"),
        _entry("прудко", "adverb", "quickly, briskly"),
        *_ADV_FILLERS,
    ]
    dictionary = _synonym_items(manifest, [_approved("швидко", "прудко", sources=["synonyms_karavansky"])])
    assert _pairs(dictionary) == {("швидко", "прудко"), ("прудко", "швидко")}, _pairs(dictionary)
    school_site_only = _synonym_items(manifest, [_approved("швидко", "прудко", sources=["miyklas.com.ua"])])
    assert _pairs(school_site_only) == set(), _pairs(school_site_only)


def test_distractor_is_never_an_accepted_synonym_of_the_prompt() -> None:
    # Issue example syn_0bd5164f658d: але → одначе offered проте and однак as distractors,
    # although both are accepted answers for але elsewhere in the same deck.
    manifest = [
        _entry("але", "conj", "but"),
        _entry("одначе", "conj", "but, however"),
        _entry("проте", "conj", "however, but"),
        _entry("однак", "conj", "however", en=["however, but"]),
        *_CONJ_FILLERS,
    ]
    items = _synonym_items(
        manifest,
        [_approved("але", "одначе"), _approved("але", "проте"), _approved("але", "однак")],
    )
    but_items = [item for item in items if item["prompt"] == "але"]
    assert {item["answer"] for item in but_items} == {"одначе", "проте", "однак"}
    for item in but_items:
        distractors = {option["label"] for option in item["options"] if option["kind"] == "distractor"}
        assert distractors.isdisjoint({"одначе", "проте", "однак"}), (item["answer"], distractors)
    assert validate_synonym_option_sets(items) == []


def test_distractor_sharing_an_english_sense_with_the_prompt_is_excluded() -> None:
    # балакати is not adjudicated as a partner of говорити here, yet it shares the
    # displayed sense "to talk"; it must not be marked wrong as a distractor.
    manifest = [
        _entry("говорити", "verb", "speak, talk", en=["to speak", "to talk"]),
        _entry("базікати", "verb", "chatter, talk", en=["to chatter", "to talk"]),
        _entry("балакати", "verb", "talk, chat", en=["to talk", "to chat"]),
        *_VERB_FILLERS,
    ]
    items = _synonym_items(manifest, [_approved("говорити", "базікати")])
    assert ("говорити", "базікати") in _pairs(items), _pairs(items)
    for item in items:
        distractors = {option["label"] for option in item["options"] if option["kind"] == "distractor"}
        assert "балакати" not in distractors, (item["prompt"], item["answer"], distractors)


def _item(prompt: str, answer: str, distractors: list[str], polarity: str = "synonym") -> dict[str, Any]:
    options = [{"label": answer, "lemmaId": answer, "kind": "answer"}]
    options.extend({"label": label, "lemmaId": label, "kind": "distractor"} for label in distractors)
    return {
        "synonymId": f"syn_{prompt}_{answer}",
        "lemmaId": prompt,
        "targetLemmaId": answer,
        "polarity": polarity,
        "prompt": prompt,
        "answer": answer,
        "options": options,
        "source": "fixture",
    }


def test_build_gate_rejects_distractor_that_is_another_items_answer() -> None:
    # Planted failure: the same deck accepts проте for але, so проте cannot be a
    # distractor of але → одначе.
    planted = [
        _item("але", "одначе", ["проте", "щоб", "ніж"]),
        _item("але", "проте", ["щоб", "ніж", "поки"]),
    ]
    errors = validate_mode_items("synonym", planted)
    assert any("проте" in error and "одначе" in error for error in errors), errors

    clean = [
        _item("але", "одначе", ["бо", "щоб", "ніж"]),
        _item("але", "проте", ["щоб", "ніж", "поки"]),
    ]
    assert validate_synonym_option_sets(clean) == []
    # Antonym-polarity answers are a different relation; they are not synonym answers.
    mixed = [
        _item("великий", "величезний", ["малий", "новий", "старий"]),
        _item("великий", "малий", ["новий", "старий", "теплий"], polarity="antonym"),
    ]
    assert validate_synonym_option_sets(mixed) == []
