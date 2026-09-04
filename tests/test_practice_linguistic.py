"""Tests for the Practice Hub linguistic quality gate."""

from __future__ import annotations

from pathlib import Path

from scripts.audit.generate_practice_deck import JsonVesumVerifier
from scripts.audit.practice_linguistic import (
    RULE_HOMOGRAPH,
    RULE_IDENTITY_LABEL,
    RULE_LEADING_QUIZ,
    RULE_PREP_NOM,
    RULE_STRESS,
    check_cloze_item,
    check_homograph_oblique,
    check_identity_rule_consistency,
    check_leading_quiz,
    check_nominative_only_after_prep,
    check_stress_item,
    index_from_generator_candidates,
    is_identity_form,
    plain,
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
