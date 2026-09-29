"""Tests for the Practice Hub linguistic quality gate."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.audit.generate_practice_deck import JsonVesumVerifier
from scripts.audit.practice_linguistic import (
    RULE_BLANK_COUNT,
    RULE_CASE_LABEL,
    RULE_DISTRACTOR_DISTINCT,
    RULE_HOMOGRAPH,
    RULE_IDENTITY_LABEL,
    RULE_INTENTIONAL_ERROR_QUARANTINE,
    RULE_LEADING_QUIZ,
    RULE_PREP_NOM,
    RULE_PROMPT_CONTEXT,
    RULE_PROMPT_LEVEL,
    RULE_STRESS,
    RULE_UNIQUE_ANSWER,
    check_cloze_blank_count,
    check_cloze_item,
    check_homograph_oblique,
    check_identity_rule_consistency,
    check_intentional_error_quarantine,
    check_inventory_prompt_context,
    check_inventory_prompt_level,
    check_leading_quiz,
    check_nominative_only_after_prep,
    check_options_uniqueness,
    check_stress_item,
    check_unique_answer_evidence,
    identity_blank_case,
    index_from_generator_candidates,
    inventory_prompt_defect,
    is_identity_form,
    plain,
    prompt_words_above_level,
)


def _verifier() -> JsonVesumVerifier:
    return JsonVesumVerifier(
        {
            "сорока": [
                {"lemma": "сорок", "pos": "numr", "tags": "numr:p:v_rod"},
                {"lemma": "сорок", "pos": "numr", "tags": "numr:p:v_zna"},
                {"lemma": "сорока", "pos": "noun", "tags": "noun:anim:f:v_naz"},
            ],
            "рота": [
                {"lemma": "рот", "pos": "noun", "tags": "noun:inanim:m:v_rod"},
                {"lemma": "рот", "pos": "noun", "tags": "noun:inanim:m:v_zna:var"},
                {"lemma": "рота", "pos": "noun", "tags": "noun:inanim:f:v_naz"},
            ],
            "дурня": [
                {"lemma": "дурень", "pos": "noun", "tags": "noun:anim:m:v_rod"},
                {"lemma": "дурень", "pos": "noun", "tags": "noun:anim:m:v_zna"},
                {"lemma": "дурня", "pos": "noun", "tags": "noun:inanim:f:v_naz"},
            ],
            "вино": [
                {"lemma": "вина", "pos": "noun", "tags": "noun:inanim:f:v_kly"},
                {"lemma": "вино", "pos": "noun", "tags": "noun:inanim:n:v_naz"},
                {"lemma": "вино", "pos": "noun", "tags": "noun:inanim:n:v_zna"},
                {"lemma": "вино", "pos": "noun", "tags": "noun:inanim:n:v_kly"},
            ],
            "більше": [
                {"lemma": "більше", "pos": "adv", "tags": "adv:compc:predic"},
                {"lemma": "більший", "pos": "adj", "tags": "adj:n:v_naz:compc"},
                {"lemma": "більший", "pos": "adj", "tags": "adj:n:v_zna:compc"},
                {"lemma": "більший", "pos": "adj", "tags": "adj:n:v_kly:compc"},
            ],
            "вік": [
                {"lemma": "вік", "pos": "noun", "tags": "noun:inanim:m:v_naz"},
                {"lemma": "вік", "pos": "noun", "tags": "noun:inanim:m:v_zna"},
                {"lemma": "віко", "pos": "noun", "tags": "noun:inanim:p:v_rod"},
            ],
            "прикраса": [
                {"lemma": "прикраса", "pos": "noun", "tags": "noun:inanim:f:v_naz"},
                {"lemma": "прикраса", "pos": "noun", "tags": "noun:inanim:f:v_zna"},
            ],
            "виживання": [
                {"lemma": "виживання", "pos": "noun", "tags": "noun:inanim:n:v_naz"},
                {"lemma": "виживання", "pos": "noun", "tags": "noun:inanim:n:v_rod"},
                {"lemma": "виживання", "pos": "noun", "tags": "noun:inanim:n:v_zna"},
            ],
            "настрій": [
                {"lemma": "настрій", "pos": "noun", "tags": "noun:inanim:m:v_naz"},
                {"lemma": "настрій", "pos": "noun", "tags": "noun:inanim:m:v_zna"},
            ],
            "гарний": [
                {"lemma": "гарний", "pos": "adj", "tags": "adj:m:v_naz"},
                {"lemma": "гарний", "pos": "adj", "tags": "adj:m:v_zna"},
            ],
            "на": [{"lemma": "на", "pos": "prep", "tags": "prep"}],
            "із": [{"lemma": "із", "pos": "prep", "tags": "prep"}],
            "з": [{"lemma": "з", "pos": "prep", "tags": "prep"}],
            "за": [{"lemma": "за", "pos": "prep", "tags": "prep"}],
            "різдвяна": [
                {"lemma": "різдвяний", "pos": "adj", "tags": "adj:f:v_naz"},
            ],
        }
    )


def _identity_item(lemma: str, sentence: str, *, rule_id: str = "nominative_identification") -> dict:
    return {
        "clozeId": f"{lemma}:test",
        "lemmaId": lemma,
        "lemma": lemma,
        "form": lemma,
        "sentence": sentence,
        "blankCase": "nominative",
        "caseRule": {
            "ruleId": rule_id,
            "case": "nominative",
            "caseLabel": "називний",
            "triggerLabel": "словникова форма",
            "feedback": f"словникова форма: {lemma}",
        },
        "provenance": {
            "status": "sentence_inventory",
            "path": "site/src/data/lexicon-sentence-inventory.json",
            "locator": f"fixture-{lemma}",
        },
    }


def test_plain_matches_cznorm_apostrophe_contract() -> None:
    assert plain("З’явитися") == plain("з'явитися")
    assert is_identity_form("Акторка", "акторка")


def test_homograph_drops_soroka_rota_durnya() -> None:
    verifier = _verifier()
    for lemma, sentence in (
        ("сорока", "мішок, зв’язку із ___ білячих шкурок"),
        ("рота", "Упустив рака з ___"),
        ("дурня", "віддати царівну за ___"),
    ):
        findings = check_homograph_oblique(
            _identity_item(lemma, sentence),
            verifier,
            item_id=lemma,
            lemma_plain=lemma,
        )
        assert any(f.rule_id == RULE_HOMOGRAPH for f in findings), lemma


def test_homograph_keeps_vyno_bilshe_vik_prykrasa() -> None:
    verifier = _verifier()
    for lemma, sentence in (
        ("вино", "На столі стоїть ___."),
        ("більше", "___ тебе не буде."),
        ("вік", "Цілий ___ шукав відповідь."),
        ("прикраса", "Різдвяна ___ на палиці."),
    ):
        findings = check_homograph_oblique(
            _identity_item(lemma, sentence),
            verifier,
            item_id=lemma,
            lemma_plain=lemma,
        )
        assert findings == [], (lemma, findings)


def test_prep_nom_keeps_vyzhyvannya_and_nastroi_frame() -> None:
    verifier = _verifier()
    keep_vyzhyvannya = check_nominative_only_after_prep(
        _identity_item("виживання", "шанси на ___"),
        verifier,
        item_id="виживання",
        lemma_plain="виживання",
    )
    assert keep_vyzhyvannya == []
    # «на ___ настрій» blanks the adjective, which is not nom-only.
    keep_adj = check_nominative_only_after_prep(
        {
            **_identity_item("гарний", "налаштовує на ___ настрій"),
            "form": "гарний",
            "lemmaId": "гарний",
            "lemma": "гарний",
        },
        verifier,
        item_id="гарний",
        lemma_plain="гарний",
    )
    assert keep_adj == []


def test_prep_nom_drops_feminine_nom_only_after_prep() -> None:
    verifier = _verifier()
    findings = check_nominative_only_after_prep(
        _identity_item("сорока", "зв’язку із ___ білячих шкурок"),
        verifier,
        item_id="сорока",
        lemma_plain="сорока",
    )
    assert any(f.rule_id == RULE_PREP_NOM for f in findings)


def test_identity_rule_both_directions() -> None:
    ok = _identity_item("книга", "Це ___.")
    assert check_identity_rule_consistency(ok, item_id="книга", lemma_plain="книга") == []
    wrong_rule = _identity_item("книга", "Це ___.", rule_id="accusative_direct_object")
    assert any(
        f.rule_id == RULE_IDENTITY_LABEL
        for f in check_identity_rule_consistency(wrong_rule, item_id="книга", lemma_plain="книга")
    )
    non_identity = {
        **_identity_item("книга", "бачу ___"),
        "form": "книгу",
        "blankCase": "accusative",
        "caseRule": {
            "ruleId": "nominative_identification",
            "case": "nominative",
            "feedback": "словникова форма: книгу",
        },
    }
    assert any(
        f.rule_id == RULE_IDENTITY_LABEL
        for f in check_identity_rule_consistency(
            non_identity, item_id="книга", lemma_plain="книга"
        )
    )


def test_leading_quiz_marker_rejected() -> None:
    findings = check_leading_quiz("x", "Д Це речення.")
    assert any(f.rule_id == RULE_LEADING_QUIZ for f in findings)
    assert check_leading_quiz("x", "Це речення.") == []


def test_stress_recompute_is_not_noop() -> None:
    good = {
        "stressId": "або:stress",
        "lemma": "або",
        "lemmaId": "або",
        "stressed": "або́",
        "unstressed": "або",
        "stressIndex": 2,
        "nuclei": [{"index": 0, "label": "а"}, {"index": 2, "label": "о"}],
    }
    assert check_stress_item(good) == []
    bad = {**good, "unstressed": "абоо", "stressIndex": 0}
    findings = check_stress_item(bad)
    assert any(f.rule_id == RULE_STRESS for f in findings)


def test_source_attested_blank_join() -> None:
    verifier = _verifier()
    candidate = {
        "clozeId": "прикраса:inventory:1",
        "lemmaId": "прикраса",
        "lemma": "прикраса",
        "form": "прикраса",
        "sentence": "Різдвяна ___ на палиці.",
        "sourceType": "sentence_inventory",
        "provenance": {
            "status": "sentence_inventory",
            "path": "site/src/data/lexicon-sentence-inventory.json",
            "locator": "fixture-prykrasa",
        },
    }
    index = index_from_generator_candidates([candidate])
    item = {
        **_identity_item("прикраса", "Різдвяна ___ на палиці."),
        "clozeId": "прикраса:inventory:1",
        "provenance": candidate["provenance"],
    }
    assert check_cloze_item(item, verifier, source_index=index, lemma_plain="прикраса") == []
    corrupted = {**item, "form": "прикраси"}
    findings = check_cloze_item(
        corrupted, verifier, source_index=index, lemma_plain="прикраса"
    )
    assert findings


def test_validate_mode_items_stress_is_not_noop() -> None:
    from scripts.audit.generate_practice_deck import validate_mode_items

    assert validate_mode_items("stress", []) == []
    errors = validate_mode_items(
        "stress",
        [
            {
                "stressId": "bad:stress",
                "lemma": "або",
                "stressed": "або",
                "unstressed": "або",
                "stressIndex": 0,
                "nuclei": [{"index": 0, "label": "а"}, {"index": 2, "label": "о"}],
            }
        ],
    )
    assert errors
    assert any("acute" in error or "stress" in error for error in errors)


def test_check_assets_vesum_flag_runs_linguistic_pack(tmp_path: Path) -> None:
    """Schema-only stays the default; --vesum-db enables the pack."""
    from scripts.audit.check_static_practice_assets import check_assets

    daily = tmp_path / "daily.json"
    reviewed = tmp_path / "reviewed.json"
    practice_dir = tmp_path / "lexicon"
    practice_dir.mkdir(parents=True)
    daily.write_text("[]", encoding="utf-8")
    reviewed.write_text('{"reviewed":[]}', encoding="utf-8")
    # Minimal invalid practice dir → schema errors, but vesum missing must also surface.
    summary = check_assets(
        daily_pool=daily,
        practice_dir=practice_dir,
        reviewed_sources=reviewed,
        levels=("A1",),
        min_daily_pool_size=0,
        min_practice_lexemes_per_level=0,
        vesum_db=tmp_path / "missing.db",
    )
    assert summary["ok"] is False
    assert any("VESUM" in error for error in summary["errors"])


def test_intentional_error_quarantine_rejected() -> None:
    bad_sentences = [
        "НЕПРАВИЛЬНО\nПРАВИЛЬНО\nзатягувати рішення\n_____ з рішенням",
        "Неправильно Правильно ___ відбулася в кабінеті директора",
        "Орфографічну помилку допущено у варіанті: А _____ Б глядацький",
        "Відредагуйте речення: деякі слова можна _____ або замінити",
        "СУРЖИК § 19 Нація — _____ у Вічність",
        "Помилку допущено в рядку А _____ Б аптека",
    ]
    for sent in bad_sentences:
        findings = check_intentional_error_quarantine("item_bad", sent)
        assert any(
            f.rule_id == RULE_INTENTIONAL_ERROR_QUARANTINE for f in findings
        ), f"Expected quarantine rejection for: {sent!r}"

    good_sent = "Учитель уважно пояснив, як правильно написати це слово в зошиті."
    assert check_intentional_error_quarantine("item_good", good_sent) == []


def test_cloze_blank_count_single_blank() -> None:
    assert check_cloze_blank_count("item", "Це гарне _____ речення.") == []
    assert check_cloze_blank_count("item", "Це гарне ___ речення.") == []
    # 0 blanks
    findings_0 = check_cloze_blank_count("item", "Тут немає пропущеного місця.")
    assert any(f.rule_id == RULE_BLANK_COUNT for f in findings_0)
    # Multiple blanks
    findings_multi = check_cloze_blank_count("item", "Перше _____ і друге _____ речення.")
    assert any(f.rule_id == RULE_BLANK_COUNT for f in findings_multi)


def test_options_uniqueness_detects_duplicates() -> None:
    unique_opts = [{"label": "книга"}, {"label": "зошит"}, {"label": "ручка"}]
    assert check_options_uniqueness("item", unique_opts) == []

    dup_opts = [{"label": "книга"}, {"label": "зошит"}, {"label": "книга"}]
    findings = check_options_uniqueness("item", dup_opts)
    assert any(f.rule_id == RULE_DISTRACTOR_DISTINCT for f in findings)


# Analyses copied from data/vesum.db (scripts.verification.vesum.verify_words).
_ISSUE_VESUM = {
    "узбіччя": [
        {"lemma": "узбіччя", "pos": "noun", "tags": "noun:inanim:n:v_naz"},
        {"lemma": "узбіччя", "pos": "noun", "tags": "noun:inanim:n:v_rod"},
        {"lemma": "узбіччя", "pos": "noun", "tags": "noun:inanim:n:v_zna"},
        {"lemma": "узбіччя", "pos": "noun", "tags": "noun:inanim:n:v_kly"},
        {"lemma": "узбіччя", "pos": "noun", "tags": "noun:inanim:p:v_naz"},
        {"lemma": "узбіччя", "pos": "noun", "tags": "noun:inanim:p:v_zna"},
        {"lemma": "узбіччя", "pos": "noun", "tags": "noun:inanim:p:v_kly"},
    ],
    "відновлення": [
        {"lemma": "відновлення", "pos": "noun", "tags": "noun:inanim:n:v_naz"},
        {"lemma": "відновлення", "pos": "noun", "tags": "noun:inanim:n:v_rod"},
        {"lemma": "відновлення", "pos": "noun", "tags": "noun:inanim:n:v_zna"},
        {"lemma": "відновлення", "pos": "noun", "tags": "noun:inanim:n:v_kly"},
        {"lemma": "відновлення", "pos": "noun", "tags": "noun:inanim:p:v_naz"},
        {"lemma": "відновлення", "pos": "noun", "tags": "noun:inanim:p:v_zna"},
        {"lemma": "відновлення", "pos": "noun", "tags": "noun:inanim:p:v_kly"},
    ],
    "укриття": [
        {"lemma": "укриття", "pos": "noun", "tags": "noun:inanim:n:v_naz"},
        {"lemma": "укриття", "pos": "noun", "tags": "noun:inanim:n:v_rod"},
        {"lemma": "укриття", "pos": "noun", "tags": "noun:inanim:n:v_zna"},
        {"lemma": "укриття", "pos": "noun", "tags": "noun:inanim:n:v_kly"},
        {"lemma": "укриття", "pos": "noun", "tags": "noun:inanim:p:v_naz"},
        {"lemma": "укриття", "pos": "noun", "tags": "noun:inanim:p:v_zna"},
        {"lemma": "укриття", "pos": "noun", "tags": "noun:inanim:p:v_kly"},
    ],
    "автомашина": [{"lemma": "автомашина", "pos": "noun", "tags": "noun:inanim:f:v_naz"}],
    "до": [
        {"lemma": "до", "pos": "noun", "tags": "noun:inanim:n:v_naz:nv"},
        {"lemma": "до", "pos": "prep", "tags": "prep"},
    ],
    "для": [{"lemma": "для", "pos": "prep", "tags": "prep"}],
    "ним": [
        {"lemma": "він", "pos": "noun", "tags": "noun:unanim:m:v_oru:pron:pers:3"},
        {"lemma": "воно", "pos": "noun", "tags": "noun:unanim:n:v_oru:pron:pers:3"},
    ],
    "є": [{"lemma": "бути", "pos": "verb", "tags": "verb:imperf:pres:s:3"}],
    "медіаграмотність": [
        {"lemma": "медіаграмотність", "pos": "noun", "tags": "noun:inanim:f:v_naz:up19"},
        {"lemma": "медіаграмотність", "pos": "noun", "tags": "noun:inanim:f:v_zna:up19"},
    ],
    "геймер": [{"lemma": "геймер", "pos": "noun", "tags": "noun:anim:m:v_naz"}],
    "відповісти": [{"lemma": "відповісти", "pos": "verb", "tags": "verb:perf:inf"}],
    "подобається": [{"lemma": "подобатися", "pos": "verb", "tags": "verb:rev:imperf:pres:s:3"}],
    "дієслова": [{"lemma": "дієслово", "pos": "noun", "tags": "noun:inanim:p:v_naz"}],
    "зобразити": [{"lemma": "зобразити", "pos": "verb", "tags": "verb:perf:inf"}],
    "звести": [{"lemma": "звести", "pos": "verb", "tags": "verb:perf:inf"}],
    "вразити": [{"lemma": "вразити", "pos": "verb", "tags": "verb:perf:inf:xp1"}],
    "налітає": [{"lemma": "налітати", "pos": "verb", "tags": "verb:imperf:pres:s:3"}],
    "звірятко": [{"lemma": "звірятко", "pos": "noun", "tags": "noun:anim:n:v_naz"}],
    "прилягло": [{"lemma": "прилягти", "pos": "verb", "tags": "verb:perf:past:n"}],
}

# The live #8726 card (practice-cloze.A2.json, deck atlas-practice-v1-c0c3f3242b5134b6).
_PUBLISHED_UZBICHCHYA = {
    "clozeId": "узбіччя:inventory:4638",
    "lemmaId": "узбіччя",
    "sentence": "Налітає автомашина, звірятко прилягло до ___.",
    "blankCase": "nominative",
    "form": "узбіччя",
    "caseRule": {
        "case": "nominative",
        "caseLabel": "називний",
        "feedback": "словникова форма: узбіччя",
        "ruleId": "nominative_identification",
        "trigger": "dictionary form",
        "triggerLabel": "словникова форма",
    },
    "provenance": {
        "status": "sentence_inventory",
        "path": "site/src/data/lexicon-sentence-inventory.json",
        "locator": "7-klas-ukrlit-zabolotnyi-2024_s0318",
    },
}


def test_identity_blank_case_withholds_case_for_same_form_after_preposition() -> None:
    verifier = JsonVesumVerifier(_ISSUE_VESUM)
    # Issue examples: nominative-identical surfaces in genitive slots.
    assert identity_blank_case(_PUBLISHED_UZBICHCHYA["sentence"], "узбіччя", "узбіччя", verifier) is None
    assert (
        identity_blank_case(
            "Для ___ можна також використати відповідну команду з контекстного меню об’єктів.",
            "відновлення",
            "відновлення",
            verifier,
        )
        is None
    )
    assert identity_blank_case("Перед тим як іти до ___, по змозі перекриваємо вдома газ.", "укриття", "укриття", verifier) is None
    # A nominative-only surface still proves the subject slot.
    assert (
        identity_blank_case("Налітає ___, звірятко прилягло до узбіччя.", "автомашина", "автомашина", verifier)
        == "nominative"
    )


def test_case_label_gate_rejects_published_nominative_label_after_do() -> None:
    verifier = JsonVesumVerifier(_ISSUE_VESUM)
    findings = check_cloze_item(_PUBLISHED_UZBICHCHYA, verifier, lemma_plain="узбіччя", check_agreement=False)
    assert [finding.rule_id for finding in findings] == [RULE_CASE_LABEL]

    repaired = {
        key: value for key, value in _PUBLISHED_UZBICHCHYA.items() if key != "blankCase"
    } | {"caseRule": {"ruleId": "lexical_insertion", "trigger": "lexical insertion"}}
    assert [(f.rule_id, f.message) for f in check_cloze_item(repaired, verifier, lemma_plain="узбіччя", check_agreement=False)] == [
        (RULE_UNIQUE_ANSWER, "no_unique_answer_evidence")
    ]

    mislabelled_insertion = {**repaired, "blankCase": "genitive"}
    assert any(
        finding.rule_id == RULE_IDENTITY_LABEL
        for finding in check_identity_rule_consistency(mislabelled_insertion, item_id="x", lemma_plain="узбіччя")
    )


def test_inventory_prompt_defect_rejects_issue_8724_examples() -> None:
    verifier = JsonVesumVerifier(_ISSUE_VESUM)
    # C1 геймер:inventory:808 — an ironic quotation presented as a definition.
    assert (
        inventory_prompt_defect("___ — важко хвора людина, вилікувати яку майже неможливо.", "Геймер", "геймер", verifier)
        == "definition_prompt"
    )
    # A2 відповісти:inventory:718 — social-media UI chrome.
    assert inventory_prompt_defect("Подобається ___ 2 д.", "Відповісти", "відповісти", verifier) == (
        "capitalized_mid_sentence"
    )
    # C1 медіаграмотність:inventory:2229 — no content word decides the blank.
    assert inventory_prompt_defect("Ним є ___.", "медіаграмотність", "медіаграмотність", verifier) == (
        "context_free_stub"
    )
    # B2 вразити:inventory:608 — a list where many verbs fit.
    assert inventory_prompt_defect("Дієслова: зобразити, звести, ___.", "вразити", "вразити", verifier) == (
        "list_fragment"
    )
    # Mentions and drill notation.
    assert inventory_prompt_defect("Яке значення має слово «___»?", "узбіччя", "узбіччя", verifier) == (
        "metalinguistic_mention"
    )
    assert inventory_prompt_defect("___ — р..місник, який виробляє ложки.", "ложкар", "ложкар", verifier) == (
        "drill_notation"
    )
    # A complete sentence in use stays.
    assert inventory_prompt_defect(_PUBLISHED_UZBICHCHYA["sentence"], "узбіччя", "узбіччя", verifier) is None


@pytest.mark.parametrize(
    ("cloze_id", "sentence", "form", "other"),
    [
        ("там:inventory:4467", "Казав же я йому, що нікого ___ немає.", "там", "ще"),
        ("сімнадцять:inventory:4451", "Бурлаці ж їх дісталося аж ___!", "сімнадцять", "двадцять"),
        ("пошкодження:inventory:3379", "Ці ___ можуть бути різними.", "пошкодження", "тіла"),
        ("поснідати:inventory:3320", "Тоді написало ще: «___.", "Поснідати", "Віддавати"),
        ("досхочу:inventory:1137", "Хочеш, щоб він ___ тебе?", "досхочу", "мовчки"),
        ("п-ятдесят:inventory:2886", "П’ять, сім, тринадцять, ___ три...", "п'ятдесят", "тридцять"),
        ("цікавіший:inventory:4859", "А вчитель був ___.", "цікавіший", "веселий"),
        ("суші:inventory:4426", "Мій чоловік любить ___.", "суші", "пиво"),
        ("урожай:inventory:4671", "Швидше збирай ___.", "урожай", "посуд"),
        ("теща:inventory:4514", "Ти знаєш, що таке ___?", "теща", "тіло"),
        ("дехто:inventory:993", "___ щастям своїм платив.", "дехто", "хтось"),
        ("прикольно:inventory:3491", "Звучить досить ___.", "прикольно", "банально"),
        ("клоун:inventory:1865", "___ роздає цукерки.", "клоун", "Тарас"),
        ("мовчки:inventory:2284", "Той дивиться на його ___.", "мовчки", "радо"),
    ],
)
def test_review_r4_lexical_insertions_require_positive_unique_answer_evidence(
    cloze_id: str, sentence: str, form: str, other: str
) -> None:
    item = {
        "clozeId": cloze_id,
        "sentence": sentence,
        "form": form,
        "lemma": form,
        "caseRule": {"ruleId": "lexical_insertion", "trigger": "lexical insertion"},
        "options": [
            {"label": form, "kind": "answer"},
            {"label": other, "kind": "distractor"},
        ],
        "provenance": {"status": "sentence_inventory", "path": "inventory.json", "locator": cloze_id},
    }
    findings = check_cloze_item(item, _verifier(), lemma_plain=form, check_agreement=False)
    assert any(f.rule_id == RULE_UNIQUE_ANSWER and f.message == "no_unique_answer_evidence" for f in findings)


def test_review_r4_corrupt_inventory_frames_are_rejected() -> None:
    verifier = JsonVesumVerifier(
        {
            "хочеш": [{"lemma": "хотіти", "pos": "verb", "tags": "verb:pres:s:2"}],
            "щоб": [{"lemma": "щоб", "pos": "conj", "tags": "conj"}],
            "він": [{"lemma": "він", "pos": "noun", "tags": "noun:pron:v_naz"}],
            "досхочу": [{"lemma": "досхочу", "pos": "adv", "tags": "adv"}],
            "тебе": [{"lemma": "ти", "pos": "noun", "tags": "noun:pron:v_zna"}],
        }
    )
    assert inventory_prompt_defect("Хочеш, щоб він ___ тебе?", "досхочу", "досхочу", verifier) == (
        "verbless_subordinate_fragment"
    )
    assert inventory_prompt_defect("Тоді написало ще: «___.", "поснідати", "поснідати", verifier) == (
        "unbalanced_quotes"
    )
    for cloze_id, sentence, form, reason in (
        ("досхочу:inventory:1137", "Хочеш, щоб він ___ тебе?", "досхочу", "verbless_subordinate_fragment"),
        ("поснідати:inventory:3320", "Тоді написало ще: «___.", "поснідати", "unbalanced_quotes"),
    ):
        item = {
            "clozeId": cloze_id,
            "sentence": sentence,
            "form": form,
            "lemma": form,
            "provenance": {"status": "sentence_inventory", "path": "inventory.json"},
        }
        assert [(f.rule_id, f.message) for f in check_inventory_prompt_context(item, verifier, item_id=cloze_id)] == [
            (RULE_PROMPT_CONTEXT, reason)
        ]


@pytest.mark.parametrize("closing_quote", ["“", "”"])
def test_inventory_prompt_accepts_low_opening_quote_with_either_closer(closing_quote: str) -> None:
    sentence = f"Він сказав: „Привіт{closing_quote} і пішов ___."
    assert inventory_prompt_defect(sentence, "додому", "додому", _verifier()) != "unbalanced_quotes"


@pytest.mark.parametrize(
    ("cloze_id", "sentence", "form", "decoy", "form_tags", "decoy_tags"),
    [
        ("дехто:inventory:993", "___ щастям своїм платив.", "дехто", "хтось", "noun:anim:m:v_naz:pron:ind", "noun:anim:m:v_naz:pron:ind"),
        ("теща:inventory:4514", "Ти знаєш, що таке ___?", "теща", "тіло", "noun:anim:f:v_naz", "noun:inanim:n:v_naz"),
        ("клоун:inventory:1865", "___ роздає цукерки.", "клоун", "Тарас", "noun:anim:m:v_naz", "noun:anim:m:v_naz:prop:fname"),
    ],
)
def test_review_r4_case_label_does_not_certify_unique_answer(
    cloze_id: str, sentence: str, form: str, decoy: str, form_tags: str, decoy_tags: str
) -> None:
    # Analyses copied from VESUM; each reviewer decoy satisfies the displayed nominative case.
    verifier = JsonVesumVerifier(
        {
            form: [{"lemma": form, "pos": "noun", "tags": form_tags}],
            decoy: [{"lemma": decoy, "pos": "noun", "tags": decoy_tags}],
        }
    )
    item = {
        "clozeId": cloze_id,
        "sentence": sentence,
        "form": form,
        "lemma": form,
        "blankCase": "nominative",
        "caseRule": {"ruleId": "nominative_identification", "case": "nominative"},
        "options": [
            {"kind": "answer", "label": form, "case": "nominative"},
            {"kind": "decoy-lemma", "label": decoy, "case": "nominative"},
        ],
    }
    findings = check_cloze_item(item, verifier, lemma_plain=form, check_agreement=False)
    assert any(f.rule_id == RULE_UNIQUE_ANSWER and f.message == "no_unique_answer_evidence" for f in findings)


def test_case_rule_certifies_only_a_distinct_vesum_case_option() -> None:
    # These four forms and tags are copied from the VESUM «книга» paradigm.
    verifier = JsonVesumVerifier(
        {
            "книгу": [{"lemma": "книга", "pos": "noun", "tags": "noun:inanim:f:v_zna"}],
            "книга": [{"lemma": "книга", "pos": "noun", "tags": "noun:inanim:f:v_naz"}],
            "книзі": [
                {"lemma": "книга", "pos": "noun", "tags": "noun:inanim:f:v_dav"},
                {"lemma": "книга", "pos": "noun", "tags": "noun:inanim:f:v_mis"},
            ],
            "книгою": [{"lemma": "книга", "pos": "noun", "tags": "noun:inanim:f:v_oru"}],
            "тіло": [{"lemma": "тіло", "pos": "noun", "tags": "noun:inanim:n:v_zna"}],
        }
    )
    item = {
        "caseRule": {"ruleId": "accusative_direct_object", "case": "accusative"},
        "options": [
            {"kind": "answer", "label": "книгу"},
            {"kind": "decoy", "label": "книга"},
            {"kind": "decoy", "label": "книзі"},
            {"kind": "decoy", "label": "книгою"},
        ],
    }
    assert check_unique_answer_evidence(item, verifier, item_id="form-case") == []
    item["options"][1]["label"] = "тіло"
    assert [(f.rule_id, f.message) for f in check_unique_answer_evidence(item, verifier, item_id="form-case")] == [
        (RULE_UNIQUE_ANSWER, "no_unique_answer_evidence")
    ]


def test_prompt_context_gate_applies_only_to_inventory_sentences() -> None:
    verifier = JsonVesumVerifier(_ISSUE_VESUM)
    stub = {
        "clozeId": "медіаграмотність:inventory:2229",
        "lemmaId": "медіаграмотність",
        "sentence": "Ним є ___.",
        "form": "медіаграмотність",
        "caseRule": {"ruleId": "lexical_insertion", "trigger": "lexical insertion"},
        "provenance": {"status": "sentence_inventory", "path": "inventory.json", "locator": "x"},
    }
    findings = check_cloze_item(stub, verifier, lemma_plain="медіаграмотність", check_agreement=False)
    assert [(finding.rule_id, finding.message) for finding in findings] == [
        (RULE_UNIQUE_ANSWER, "no_unique_answer_evidence"),
        (RULE_PROMPT_CONTEXT, "context_free_stub"),
    ]
    reviewed = {**stub, "provenance": {"status": "reviewed", "path": "curated.json"}}
    assert [(f.rule_id, f.message) for f in check_cloze_item(reviewed, verifier, lemma_plain="медіаграмотність", check_agreement=False)] == [
        (RULE_UNIQUE_ANSWER, "no_unique_answer_evidence")
    ]


def _level_verifier() -> JsonVesumVerifier:
    return JsonVesumVerifier(
        {
            "мама": [{"lemma": "мама", "pos": "noun", "tags": "noun:anim:f:v_naz"}],
            "читає": [{"lemma": "читати", "pos": "verb", "tags": "verb:imperf:pres:s:3"}],
            "у": [{"lemma": "у", "pos": "prep", "tags": "prep"}],
            "бібліотеці": [{"lemma": "бібліотека", "pos": "noun", "tags": "noun:inanim:f:v_mis"}],
            "призми": [{"lemma": "призма", "pos": "noun", "tags": "noun:inanim:f:v_rod"}],
            "ребру": [{"lemma": "ребро", "pos": "noun", "tags": "noun:inanim:n:v_dav"}],
            "франко": [
                {"lemma": "Франко", "pos": "noun", "tags": "noun:anim:m:v_naz:prop:lname"},
                {"lemma": "франко", "pos": "adv", "tags": "adv"},
            ],
            "грані": [
                {"lemma": "грань", "pos": "noun", "tags": "noun:inanim:p:v_naz"},
                {"lemma": "гран", "pos": "noun", "tags": "noun:inanim:m:v_mis"},
            ],
        }
    )


LEVELS = {"мама": "A1", "читати": "A1", "бібліотека": "A2", "ребро": "B1", "грань": "A1"}


def test_prompt_level_counts_unrated_and_higher_content_words() -> None:
    verifier = _level_verifier()
    # Prepositions, names, digits and one-letter abbreviations carry no level.
    assert prompt_words_above_level("Мама читає ___ у бібліотеці, 2 м.", "A1", LEVELS, verifier) == ["бібліотеці"]
    assert prompt_words_above_level("Франко читає ___.", "A1", LEVELS, verifier) == []
    # призма is unrated (beyond the rated vocabulary); ребро is B1.
    assert prompt_words_above_level("___ призми ребру.", "A1", LEVELS, verifier) == ["призми", "ребру"]
    assert prompt_words_above_level("___ призми ребру.", "B1", LEVELS, verifier) == ["призми"]
    # A homograph takes its lowest rated lemma.
    assert prompt_words_above_level("___ грані.", "A1", LEVELS, verifier) == []


def test_review_r4_a1_politeness_formula_is_one_levelled_unit() -> None:
    verifier = JsonVesumVerifier(
        {
            "сік": [{"lemma": "сік", "pos": "noun", "tags": "noun:inanim:m:v_naz"}],
            "будь": [{"lemma": "бути", "pos": "verb", "tags": "verb:imper"}],
            "ласка": [{"lemma": "ласка", "pos": "noun", "tags": "noun:inanim:f:v_naz"}],
        }
    )
    levels = {"сік": "A1", "бути": "A1", "ласка": "B1"}
    assert prompt_words_above_level("___ сік, будь ласка.", "A1", levels, verifier) == []
    assert prompt_words_above_level("___ сік, ласка.", "A1", levels, verifier) == ["ласка"]
    item = {"sentence": "___ сік, будь ласка.", "provenance": {"status": "sentence_inventory"}}
    assert check_inventory_prompt_level(item, "A1", levels, verifier, item_id="яблучний:inventory:5035") == []


def test_prompt_level_counts_a_word_vesum_cannot_resolve_as_above_level() -> None:
    """Review probe (#8724 r3): an unresolved token must not pass as in-level.

    «бібліотецi» ends in a Latin «i» (mixed-script OCR debris), so VESUM has
    no analysis and no level can be proved for it.
    """
    verifier = _level_verifier()
    assert prompt_words_above_level("Мама читає ___ у бібліотецi.", "C1", LEVELS, verifier) == ["бібліотецi"]
    assert prompt_words_above_level("Мама читає ___ Photoshop.", "A1", LEVELS, verifier) == ["Photoshop"]


def test_prompt_level_gate_admits_only_prompts_with_every_word_at_the_card_level() -> None:
    """AC-02: an inventory prompt is admitted only if no context word is above its level.

    Review probe (#8724 r3): an A1 prompt with one A2 word («бібліотеці») was
    admitted under a one-word tolerance; it is now withheld.
    """
    verifier = _level_verifier()
    inventory = {"clozeId": "x", "provenance": {"status": "sentence_inventory"}}
    in_level = {**inventory, "sentence": "Мама читає ___."}
    one_above = {**inventory, "sentence": "Мама читає ___ у бібліотеці."}
    unresolved = {**inventory, "sentence": "Мама читає ___ у бібліотецi."}
    assert check_inventory_prompt_level(in_level, "A1", LEVELS, verifier, item_id="x") == []
    # The same prompt is at level for an A2 card.
    assert check_inventory_prompt_level(one_above, "A2", LEVELS, verifier, item_id="x") == []
    for item, words in ((one_above, "бібліотеці"), (unresolved, "бібліотецi")):
        findings = check_inventory_prompt_level(item, "A1", LEVELS, verifier, item_id="x")
        assert [(finding.rule_id, finding.message) for finding in findings] == [
            (RULE_PROMPT_LEVEL, f"above A1: {words}")
        ]
    curated = {**one_above, "provenance": {"status": "reviewed", "path": "curated.json"}}
    assert check_inventory_prompt_level(curated, "A1", LEVELS, verifier, item_id="x") == []
