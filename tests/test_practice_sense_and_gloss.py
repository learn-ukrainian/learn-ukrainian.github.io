"""Regression tests for #8729 (Classify keys a homograph) and #8715 (stub glosses).

Entries mirror the published ``atlas-practice-v1-c0c3f3242b5134b6`` evidence:
the Atlas morphology of «до», «коло» and «п'ята» is the VESUM analysis of a
noun homograph, and B1+ glosses are dictionary articles whose first-comma cut
left «Той», «1. Те саме» or «і ж.».
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import scripts.audit.generate_practice_deck as generate_practice_deck
from scripts.audit.generate_practice_deck import (
    BuildConfig,
    JsonVesumVerifier,
    ReviewedSourceAllowlist,
    VesumLemmaEvidence,
    _build_classify_items,
    _build_lexeme,
    _vesum_lemma_evidence,
    build_practice_shards,
)

pytestmark = pytest.mark.reads_content


@pytest.fixture(autouse=True)
def synthetic_creation_baseline(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.practice.creation_review import CreationReview

    policy = CreationReview.from_path(Path("tests/fixtures/lexicon-practice-creation-review.json"))
    monkeypatch.setattr(CreationReview, "from_path", classmethod(lambda cls: policy))


def _noun_forms(gender: str) -> list[dict[str, str]]:
    return [
        {"form": "x", "label": f"{gender}, називний"},
        {"form": "x", "label": f"{gender}, родовий"},
        {"form": "x", "label": "множина, називний"},
    ]


def _entry(lemma: str, pos: str, gloss: str, level: str, **enrichment: Any) -> dict[str, Any]:
    return {
        "lemma": lemma,
        "url_slug": lemma,
        "gloss": gloss,
        "pos": pos,
        "primary_source": "course_vocab",
        "enrichment": {"cefr": {"level": level}, **enrichment},
    }


# VESUM analyses as returned by scripts.verification.vesum.verify_words.
VESUM_ROWS: dict[str, list[dict[str, str]]] = {
    "до": [
        {"lemma": "до", "pos": "noun", "tags": "noun:inanim:n:v_naz:nv"},
        {"lemma": "до", "pos": "prep", "tags": "prep"},
    ],
    "коло": [
        {"lemma": "коло", "pos": "noun", "tags": "noun:inanim:n:v_naz"},
        {"lemma": "коло", "pos": "prep", "tags": "prep"},
    ],
    "п'ята": [
        {"lemma": "п'ята", "pos": "noun", "tags": "noun:inanim:f:v_naz"},
        {"lemma": "п'ятий", "pos": "adj", "tags": "adj:f:v_naz:numr"},
    ],
    "кілька": [
        {"lemma": "кілька", "pos": "noun", "tags": "noun:anim:f:v_naz"},
        {"lemma": "кілька", "pos": "numr", "tags": "numr:p:v_naz:pron:ind"},
    ],
    "він": [{"lemma": "він", "pos": "noun", "tags": "noun:unanim:m:v_naz:pron:pers:3"}],
    "вона": [{"lemma": "вона", "pos": "noun", "tags": "noun:unanim:f:v_naz:pron:pers:3"}],
    "воно": [{"lemma": "воно", "pos": "noun", "tags": "noun:unanim:n:v_naz:pron:pers:3"}],
    "вони": [{"lemma": "вони", "pos": "noun", "tags": "noun:unanim:p:v_naz:pron:pers:3"}],
    "хто": [{"lemma": "хто", "pos": "noun", "tags": "noun:anim:m:v_naz:pron:int:rel"}],
    "цей": [{"lemma": "цей", "pos": "adj", "tags": "adj:m:v_naz:pron:dem"}],
    "книга": [{"lemma": "книга", "pos": "noun", "tags": "noun:inanim:f:v_naz"}],
    # Same-POS homographs (VESUM xp1/xp2) that agree on gender.
    "замок": [
        {"lemma": "замок", "pos": "noun", "tags": "noun:inanim:m:v_naz:xp1"},
        {"lemma": "замок", "pos": "noun", "tags": "noun:inanim:m:v_naz:xp2"},
        {"lemma": "замокти", "pos": "verb", "tags": "verb:perf:past:m"},
    ],
    # A common-gender noun: the displayed sense cannot be bound to one gender.
    "сирота": [
        {"lemma": "сирота", "pos": "noun", "tags": "noun:anim:f:v_naz"},
        {"lemma": "сирота", "pos": "noun", "tags": "noun:anim:m:v_naz"},
    ],
    "двері": [{"lemma": "двері", "pos": "noun", "tags": "noun:inanim:p:v_naz:ns"}],
    "мати": [
        {"lemma": "мати", "pos": "noun", "tags": "noun:anim:f:v_naz"},
        {"lemma": "мати", "pos": "verb", "tags": "verb:imperf:inf"},
    ],
    "лютий": [
        {"lemma": "лютий", "pos": "adj", "tags": "adj:m:v_naz:compb"},
        {"lemma": "лютий", "pos": "noun", "tags": "noun:inanim:m:v_naz"},
    ],
    # sources.inspect_words, VESUM source version 53923150073b4fc7 (2026-09-28):
    # each exact lemma has both an adjective and a noun nominative analysis.
    "святий": [
        {"lemma": "святий", "pos": "adj", "tags": "adj:m:v_naz:compb"},
        {"lemma": "святий", "pos": "noun", "tags": "noun:anim:m:v_naz"},
    ],
    "вчений": [
        {"lemma": "вчений", "pos": "adj", "tags": "adj:m:v_naz:adjp:pasv:imperf"},
        {"lemma": "вчений", "pos": "noun", "tags": "noun:anim:m:v_naz"},
    ],
    "психічний": [
        {"lemma": "психічний", "pos": "adj", "tags": "adj:m:v_naz"},
        {"lemma": "психічний", "pos": "noun", "tags": "noun:anim:m:v_naz"},
    ],
}


def _classify_by_lemma(entries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    shards = build_practice_shards(
        entries,
        ReviewedSourceAllowlist.from_payload([]),
        JsonVesumVerifier(VESUM_ROWS),
        [],
        BuildConfig(target=len(entries), source_label="fixture"),
        heritage_pairs=[],
        paronym_pairs=[],
        synonym_verdicts={"approved": [], "rejected": []},
    )
    return {item["lemma"]: item["sets"] for level in shards.values() for item in level["classify"]["classify"]}


def _set_answers(sets: list[dict[str, Any]]) -> dict[str, list[str]]:
    return {item["setId"]: item.get("answers", [item["answer"]]) for item in sets}


def test_classify_never_keys_noun_grammar_for_a_displayed_preposition() -> None:
    """A1 «до» (preposition, «before») was keyed neuter from the note «до»."""
    classify = _classify_by_lemma(
        [
            _entry(
                "до",
                "preposition",
                "until, by; to",
                "A1",
                morphology={"pos": "іменник", "forms": _noun_forms("сер.")},
            ),
            _entry("коло", "preposition", "near", "A2", morphology={"pos": "іменник", "forms": _noun_forms("сер.")}),
        ]
    )

    assert "до" not in classify
    assert "коло" not in classify


def test_classify_withholds_an_ordinal_whose_only_analysis_is_the_heel_noun() -> None:
    """A2 «п'ята» («fifth (feminine)») was keyed feminine noun from «п'ята» (heel)."""
    classify = _classify_by_lemma(
        [
            _entry(
                "п'ята",
                "ordinal chunk",
                "five o'clock; fifth (feminine)",
                "A2",
                morphology={"pos": "іменник", "forms": _noun_forms("жін.")},
                translation={"en": ["heel (anatomy: part of the foot)"], "pos": "noun"},
            )
        ]
    )

    assert "п'ята" not in classify


def test_classify_withholds_the_numeral_when_morphology_is_the_fish_noun_for_kilka() -> None:
    classify = _classify_by_lemma(
        [_entry("кілька", "numeral", "several", "B1", morphology={"pos": "іменник", "forms": _noun_forms("жін.")})]
    )

    assert "кілька" not in classify


def test_classify_keeps_noun_gender_when_morphology_is_the_displayed_noun() -> None:
    classify = _classify_by_lemma(
        [_entry("книга", "noun", "book", "A2", morphology={"pos": "іменник", "forms": _noun_forms("жін.")})]
    )

    assert _set_answers(classify["книга"]) == {"gender": ["feminine"], "pos": ["noun"]}


def test_classify_keys_no_gender_for_a_noun_vesum_does_not_attest() -> None:
    """Review (#8729): an A1 noun with no exact-lemma VESUM noun reading was keyed masculine."""
    classify = _classify_by_lemma(
        [_entry("столик", "noun", "small table", "A1", morphology={"pos": "іменник", "forms": _noun_forms("чол.")})]
    )

    assert "столик" not in classify


@pytest.mark.parametrize(
    ("lemma", "gloss", "level"),
    [("святий", "holy", "A2"), ("вчений", "learned", "A2"), ("психічний", "mental", "B1")],
)
def test_classify_withholds_noun_pos_when_displayed_sense_has_adjective_morphology(
    lemma: str, gloss: str, level: str
) -> None:
    """The exact lemma's VESUM noun analysis cannot license this adjective sense's noun key."""
    classify = _classify_by_lemma(
        [_entry(lemma, "noun", gloss, level, morphology={"pos": "прикметник", "forms": [{"label": "чол., називний"}]})]
    )

    assert lemma not in classify


@pytest.mark.parametrize("lemma", ["святий", "вчений", "психічний"])
def test_classify_names_pos_mismatch_residual_for_adjectival_morphology(lemma: str) -> None:
    entry = _entry(lemma, "noun", "adjectival sense", "B1", morphology={"pos": "прикметник"})
    evidence = _vesum_lemma_evidence([lemma], JsonVesumVerifier(VESUM_ROWS))[lemma]
    residuals: list[dict[str, str]] = []

    assert (
        _build_classify_items(
            entry,
            {"lemmaId": lemma, "lemma": lemma, "cefr": "B1"},
            vesum_evidence=evidence,
            pos_residuals=residuals,
        )
        == []
    )
    assert residuals == [{"lemmaId": lemma, "lemma": lemma, "cefr": "B1", "reason": "morphology_pos_mismatch"}]


def test_classify_keeps_attested_noun_pos_when_morphology_is_noun() -> None:
    lemma = "святий"
    classify = _classify_by_lemma([_entry(lemma, "noun", "saint", "B1", morphology={"pos": "іменник"})])

    assert _set_answers(classify[lemma]) == {"pos": ["noun"]}


def test_classify_does_not_reuse_displayed_pos_as_missing_morphology_pos() -> None:
    entry = _entry("святий", "noun", "holy", "B1", morphology={"forms": [{"label": "чол., називний"}]})
    evidence = _vesum_lemma_evidence(["святий"], JsonVesumVerifier(VESUM_ROWS))["святий"]
    residuals: list[dict[str, str]] = []

    assert (
        _build_classify_items(
            entry,
            {"lemmaId": "святий", "lemma": "святий", "cefr": "B1"},
            vesum_evidence=evidence,
            pos_residuals=residuals,
        )
        == []
    )
    assert residuals[0]["reason"] == "morphology_pos_mismatch"


def test_classify_binds_noun_gender_to_the_displayed_sense() -> None:
    """Same-POS homographs must agree on gender, and the enrichment analysis must confirm VESUM."""
    classify = _classify_by_lemma(
        [
            _entry("замок", "noun", "castle", "A1", morphology={"pos": "іменник", "forms": _noun_forms("чол.")}),
            # A common-gender noun: VESUM gives two genders.
            _entry("сирота", "noun", "orphan", "A1", morphology={"pos": "іменник", "forms": _noun_forms("жін.")}),
            # The enrichment analysis names another gender.
            _entry("книга", "noun", "book", "A1", morphology={"pos": "іменник", "forms": _noun_forms("чол.")}),
            # Noun and verb forms merged (Atlas «мати», glossed «to have»): the labels confirm no gender.
            _entry(
                "мати",
                "noun",
                "to have",
                "A1",
                morphology={"pos": "іменник", "forms": [{"label": "жін., називний"}, {"label": "минулий, чол."}]},
            ),
            # The enrichment analysis is the adjective, not the displayed noun.
            _entry("лютий", "noun", "fierce", "A1", morphology={"pos": "прикметник", "forms": _noun_forms("чол.")}),
        ]
    )

    assert classify == {"замок": [classify["замок"][0]]}
    assert _set_answers(classify["замок"]) == {"gender": ["masculine"]}


@pytest.mark.parametrize(
    "evidence",
    [None, VesumLemmaEvidence(), VesumLemmaEvidence(frozenset({"verb"}), {"noun": frozenset({"masculine"})})],
)
def test_classify_items_need_vesum_noun_evidence_for_gender(evidence: VesumLemmaEvidence | None) -> None:
    entry = _entry("замок", "noun", "castle", "A1", morphology={"pos": "іменник", "forms": _noun_forms("чол.")})
    lexeme = {"lemmaId": "замок", "lemma": "замок", "cefr": "A1"}

    assert _build_classify_items(entry, lexeme, vesum_evidence=evidence) == []


@pytest.mark.parametrize(
    ("lemma", "label", "expected"),
    [
        ("він", "чол.", "masculine"),
        ("вона", "жін.", "feminine"),
        ("воно", "сер.", "neuter"),
        ("вони", "чол.", None),
        ("хто", "чол.", None),
        ("цей", "чол.", None),
    ],
)
def test_classify_keeps_gender_only_for_a_personal_pronoun(lemma: str, label: str, expected: str | None) -> None:
    """Review (#8729): «він/вона/воно» keep their gender card from the exact-lemma pronoun analysis."""
    # The Atlas morphology of «він» is VESUM's noun-filed pronoun analysis.
    forms = [{"label": f"{label}, називний, 3 ос."}, {"label": f"{label}, давальний, 3 ос."}]
    classify = _classify_by_lemma([_entry(lemma, "pronoun", "he", "A1", morphology={"pos": "іменник", "forms": forms})])

    if expected is None:
        assert lemma not in classify
    else:
        assert _set_answers(classify[lemma]) == {"gender": [expected]}


def test_vesum_lemma_evidence_counts_only_analyses_of_the_exact_lemma() -> None:
    evidence = _vesum_lemma_evidence(
        ["п'ята", "кілька", "він", "хто", "замок", "сирота", "двері", "невідоме"], JsonVesumVerifier(VESUM_ROWS)
    )

    assert evidence == {
        "п'ята": VesumLemmaEvidence(frozenset({"noun"}), {"noun": frozenset({"feminine"})}),
        "кілька": VesumLemmaEvidence(frozenset({"noun", "numeral", "pronoun"}), {"noun": frozenset({"feminine"})}),
        "він": VesumLemmaEvidence(frozenset({"noun", "pronoun"}), {"pronoun": frozenset({"masculine"})}),
        "хто": VesumLemmaEvidence(frozenset({"noun", "pronoun"})),
        "замок": VesumLemmaEvidence(frozenset({"noun"}), {"noun": frozenset({"masculine"})}),
        "сирота": VesumLemmaEvidence(frozenset({"noun"}), {"noun": frozenset({"feminine", "masculine"})}),
        "двері": VesumLemmaEvidence(frozenset({"noun"})),
    }


SELF_FORMS = JsonVesumVerifier(
    {
        "хіті": [{"lemma": "хіть", "pos": "noun", "tags": "noun:inanim:f:v_rod"}],
        "присмерки": [{"lemma": "присмерк", "pos": "noun", "tags": "noun:inanim:p:v_naz"}],
        "довкола": [{"lemma": "довкола", "pos": "adv", "tags": "adv"}],
    }
)


@pytest.mark.parametrize(
    ("lemma", "gloss", "published_stub", "expected"),
    [
        (
            "дворище",
            "1. Те саме, що двір¹ 1, 5. — Достану грошенят — у мене буде рай: Будинок, дворище (Гл., Вибр., 1957, 171)",
            "1. Те саме",
            "Те саме, що двір",
        ),
        (
            "абонент",
            "Той, хто користується абонементом. Не менше також треба було вважати [Целі] на окремі полички",
            "Той",
            "Той, хто користується абонементом",
        ),
        ("бідолаха", "і ж., розм. Бідна, нещасна людина; бідняга. Чисто на сміх", "і ж.", "Бідна, нещасна людина"),
        ("всякий", "означ, 1. Який завгодно; кожний. Усякий кулик до свого озера привик", "означ", "Який завгодно"),
        ("глава", "1. ж., заст. Те саме, що голова́ 1. До його кралася змія", "1. ж.", "Те саме, що голова́"),
        (
            "постать",
            "1. кого, чия. Зовнішній вигляд, обриси тіла людини. Було щось",
            "1. кого",
            "Зовнішній вигляд, обриси тіла людини",
        ),
        ("фальш", "і у, ч. 1. Підробка, обман, шахрайство. — І я, братику", "і у", "Підробка, обман, шахрайство"),
        (
            "хіть",
            "хі́ті, ж., розм. 1. перев. до чого або з інфін. Бажання, прагнення здійснити, виконати щось. На другий день",
            "хі́ті",
            "Бажання, прагнення здійснити, виконати щось",
        ),
        (
            "щільний",
            "1. Такий, складові частини якого міцно з’єднані між собою; який у малому об’ємі",
            "1. Такий",
            "Такий, складові частини якого міцно з’єднані між собою",
        ),
        ("диво", "те, що викликає подив, здивування; чудо", "те", "те, що викликає подив, здивування"),
        (
            "бажаний",
            "такий, якого бажають, чекають, до якого прагнуть",
            "такий",
            "такий, якого бажають, чекають, до якого прагнуть",
        ),
        ("похитати", "кого, що і без прям. дод. Хитати якийсь час; хитнути кілька разів.", "кого", "Хитати якийсь час"),
        (
            "ввозити",
            "ВВО́ЗИТИ (УВО́ЗИТИ), вво́жу, вво́зиш, недок., ВВЕЗТИ́ (УВЕЗТИ́), ввезу́; мин. ч. ввіз; док.; перех. Везучи, доставляти кудись. Кіт",
            "ВВО́ЗИТИ (УВО́ЗИТИ)",
            "Везучи, доставляти кудись",
        ),
        (
            "вибиратися",
            "ВИБИРА́ТИСЯ, а́юся, а́єшся, недок., ВИ́БРАТИСЯ, беруся, док. 1. З труднощами виходити з тісного місця. Далі",
            "ВИБИРА́ТИСЯ",
            "З труднощами виходити з тісного місця",
        ),
        (
            "абстрактно",
            "Присл. до абстра́ктний. Мислити абстрактно",
            "Присл. до абстра́ктний. Мислити абстрактно",
            "Присл. до абстра́ктний",
        ),
        ("довкіл", "довко́ла.", "довко́ла.", "довко́ла"),
    ],
    ids=lambda value: value if value.isalpha() else "",
)
def test_ukrainian_gloss_clean_is_the_first_sense_not_a_stub(
    lemma: str, gloss: str, published_stub: str, expected: str
) -> None:
    lexeme = _build_lexeme(_entry(lemma, "noun", gloss, "B1"), SELF_FORMS)

    assert generate_practice_deck._gloss_clean(gloss) == published_stub
    assert lexeme is not None
    assert lexeme["glossClean"] == expected
    assert lexeme["meaningMcEligible"] is False


def test_self_form_gloss_falls_back_to_the_english_source_gloss() -> None:
    entry = _entry(
        "присмерк",
        "noun",
        "при́смерки.",
        "B1",
        translation={"en": ["twilight (light before rising and after the setting of the Sun)"], "source": "dmklinger"},
    )

    lexeme = _build_lexeme(entry, SELF_FORMS)

    assert lexeme is not None
    assert lexeme["glossClean"] == "twilight"


def test_sourced_ukrainian_definition_stands_in_before_english() -> None:
    entry = _entry(
        "присмерк",
        "noun",
        "при́смерки.",
        "B1",
        meaning={"definitions": ["слабке світло після заходу сонця"], "source": "Вікісловник"},
        translation={"en": ["twilight"], "source": "dmklinger"},
    )

    lexeme = _build_lexeme(entry, SELF_FORMS)

    assert lexeme is not None
    assert lexeme["glossClean"] == "слабке світло після заходу сонця"


def test_english_fallback_rejects_a_bare_grammar_code_and_withholds_a_meaningless_lexeme() -> None:
    no_meaning = _entry("мотиватор", "noun", "МОТИВА́ТОР.", "C1")
    grammar_code = _entry(
        "перетравити",
        "verb",
        "ПЕРЕТРАВИ́ТИ¹ див. перетра́влювати¹. ПЕРЕТРАВИ́ТИ² див. перетра́влювати².",
        "B2",
        translation={"en": ["P vt"], "source": "e2u.org.ua (Rysin, Starko et al.)"},
    )

    assert _build_lexeme(no_meaning, SELF_FORMS) is None
    assert _build_lexeme(grammar_code, SELF_FORMS) is None


def test_english_gloss_clean_still_cuts_at_the_first_comma() -> None:
    lexeme = _build_lexeme(_entry("книга", "noun", "book, volume; tome", "A2"), SELF_FORMS)

    assert lexeme is not None
    assert lexeme["glossClean"] == "book"


def test_homoglyph_repair_touches_only_mixed_script_words() -> None:
    repair = generate_practice_deck._repair_homoglyphs

    assert repair("вести cебе") == "вести себе"
    assert repair("у вiзочку пiд яблунею") == "у візочку під яблунею"
    assert repair("Xмара") == "Хмара"
    assert repair("café, CEO та Wi-Fi") == "café, CEO та Wi-Fi"
    assert repair("дgом") == "дgом"
    # The apostrophe belongs to the word, so a homoglyph beyond it is repaired too.
    assert repair("м'ясo і п’ятa, don't") == "м'ясо і п’ята, don't"


def _deck(**kinds: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    return {"B2": kinds}


def test_deck_text_gate_rejects_mixed_script_words_and_stub_glosses() -> None:
    planted = _deck(
        heritage={"heritage": [{"heritageId": "her_071765e3cc25", "options": [{"label": "вести cебе"}]}]},
        lexemes={
            "lexemes": [
                {"lemmaId": "абонент", "lemma": "абонент", "glossClean": "Той"},
                {"lemmaId": "хіть", "lemma": "хіть", "glossClean": "хі́ті"},
                {"lemmaId": "книга", "lemma": "книга", "glossClean": "book"},
                {"lemmaId": "довкіл", "lemma": "довкіл", "glossClean": "довко́ла"},
            ]
        },
    )

    errors = generate_practice_deck.validate_deck_text(planted, SELF_FORMS)

    assert errors == [
        "heritage.B2.heritage[0].options[0].label: mixed Cyrillic/Latin word 'cебе'",
        "lexemes.B2: абонент glossClean is a stub 'Той'",
        "lexemes.B2: хіть glossClean is a stub 'хі́ті'",
    ]


@pytest.mark.parametrize("word", ["m'ясо", "m’ясо", "mʼясо"])
def test_deck_text_gate_rejects_a_mixed_script_word_split_by_an_apostrophe(word: str) -> None:
    """Review (#8715): «m'ясо» with a Latin m was read as «m» plus «ясо» and passed."""
    planted = _deck(heritage={"heritage": [{"options": [{"label": f"{word}, l'amour, don't"}]}]})

    assert generate_practice_deck.validate_deck_text(planted) == [
        f"heritage.B2.heritage[0].options[0].label: mixed Cyrillic/Latin word {word!r}"
    ]


@pytest.mark.parametrize("apostrophe", ["'", "’", "ʼ"])
def test_homoglyph_gate_reads_a_stressed_word_as_one_word(apostrophe: str) -> None:
    """Review (#8715): the stress mark split «м'я́co» into «м'я́» plus a Latin «co», so it passed."""
    stressed = f"м{apostrophe}я\u0301co"
    planted = _deck(heritage={"heritage": [{"options": [{"label": f"{stressed}, cafe\u0301"}]}]})

    assert generate_practice_deck.validate_deck_text(planted) == [
        f"heritage.B2.heritage[0].options[0].label: mixed Cyrillic/Latin word {stressed!r}"
    ]
    assert generate_practice_deck._repair_homoglyphs(f"{stressed}, cafe\u0301") == (
        f"м{apostrophe}я\u0301со, cafe\u0301"
    )
    assert generate_practice_deck.validate_deck_text(generate_practice_deck._repair_deck_homoglyphs(planted)) == []


def test_shard_build_repairs_homoglyphs_and_fails_on_an_unrepairable_one() -> None:
    def build(gloss: str) -> dict[str, dict[str, dict[str, Any]]]:
        return build_practice_shards(
            [_entry("книга", "noun", gloss, "A1")],
            ReviewedSourceAllowlist.from_payload([]),
            JsonVesumVerifier(VESUM_ROWS),
            [],
            BuildConfig(target=1, source_label="fixture"),
            heritage_pairs=[],
            paronym_pairs=[],
            synonym_verdicts={"approved": [], "rejected": []},
        )

    repaired = build("book (у вiзочку)")
    assert repaired["A1"]["lexemes"]["lexemes"][0]["gloss"] == "book (у візочку)"

    with pytest.raises(ValueError, match="mixed Cyrillic/Latin word 'дgом'"):
        build("book (дgом)")
