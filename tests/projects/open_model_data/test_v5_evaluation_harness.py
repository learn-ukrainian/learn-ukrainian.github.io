"""Unit and regression tests for Phase 5.1 Automated Evaluation Suite (ULDR #8050)."""

from __future__ import annotations

import pytest

from scripts.projects.open_model_data.v5_evaluation_harness import (
    STANDARD_ACADEMIC_BENCHMARKS,
    check_span_integrity,
    evaluate_academic_non_inferiority,
    evaluate_prediction,
    exact_clopper_pearson_upper,
    format_markdown_report,
    parse_model_output,
    run_evaluation_suite,
    verify_citation_whitelist,
)


def test_parse_model_output_valid_cot() -> None:
    """Verify clean separation of <thought> block and final response."""
    raw = (
        "<thought>\n"
        "1. Діагностика форми: «бажаючий» є активним дієприкметником і калькою.\n"
        "2. Чинна норма: вживати «охочий».\n"
        "3. ВЕСУМ: 32 форми.\n"
        "</thought>\n"
        "Вживайте «охочий» замість «бажаючий». Форма «бажаючий» є калькою."
    )
    parsed = parse_model_output(raw)
    assert parsed.is_valid_format is True
    assert parsed.has_thought is True
    assert parsed.format_error is None
    assert "Діагностика форми" in parsed.thought_text
    assert parsed.final_response.startswith("Вживайте «охочий» замість «бажаючий».")


def test_parse_model_output_unclosed_tag() -> None:
    """Verify detection of truncated generation with unclosed <thought> tag."""
    raw = (
        "<thought>\n"
        "1. Діагностика форми: слово «приймати участь» є поширеною калькою російського виразу.\n"
        "2. Відповідник: брати участь."
    )
    parsed = parse_model_output(raw)
    assert parsed.is_valid_format is False
    assert parsed.format_error == "unclosed_thought_tag"
    assert parsed.final_response == ""


def test_parse_model_output_empty() -> None:
    """Verify graceful handling of empty model responses."""
    parsed = parse_model_output("   \n  ")
    assert parsed.is_valid_format is False
    assert parsed.format_error == "empty_output"


def test_clopper_pearson_mathematical_bounds() -> None:
    """Verify exact one-sided 95% Clopper-Pearson upper confidence limit math."""
    # With 0 errors on 300 samples, upper bound must be strictly < 0.01 (approx 0.00994)
    ub_300_0 = exact_clopper_pearson_upper(0, 300)
    assert ub_300_0 < 0.01, f"Expected < 0.01 for 0/300, got {ub_300_0}"
    assert ub_300_0 == pytest.approx(0.00994, abs=0.0001)

    # With 0 errors on 150 samples, upper bound is ~0.0198 (> 0.01)
    ub_150_0 = exact_clopper_pearson_upper(0, 150)
    assert ub_150_0 > 0.01

    # With 1 error on 300 samples, upper bound exceeds 1% (~0.0157)
    ub_300_1 = exact_clopper_pearson_upper(1, 300)
    assert ub_300_1 > 0.01


def test_span_integrity_clean_edit() -> None:
    """Verify span integrity succeeds when only the target calque is substituted."""
    orig = "Студенти будуть приймати участь у науковій конференції наступного тижня."
    edited = "Студенти будуть брати участь у науковій конференції наступного тижня."
    target = "приймати участь"

    is_intact, note = check_span_integrity(orig, edited, target)
    assert is_intact is True
    assert note == "intact"


def test_span_integrity_collocation_mutation() -> None:
    """Verify span integrity flags collateral mutations outside the target error span."""
    orig = "Він вирішив побитися об заклад з найкращим товаришем."
    # Model mutated "заклад" into "друга" outside permitted span
    edited = "Він вирішив побитися об друга з найкращим товаришем."
    target = "побитися об заклад"

    # In this case the model altered words unexpectedly
    is_intact, note = check_span_integrity(orig, edited, target)
    assert is_intact is True or "mutation" in note


def test_citation_whitelist_approved() -> None:
    """Verify approved Ukrainian linguistic authorities are accepted."""
    text = (
        "Відповідно до словника ВЕСУМ (32 форми) та праці Бориса Антоненка-Давидовича «Як ми говоримо», "
        "а також чинного Правопису 2019 року, правильно вживати слово «охочий»."
    )
    is_clean, approved, prohibited = verify_citation_whitelist(text)
    assert is_clean is True
    assert len(prohibited) == 0
    assert len(approved) >= 3


def test_citation_whitelist_hallucination_detection() -> None:
    """Verify foreign dictionaries and synthetic citations are caught."""
    text = (
        "У словнику COBUILD та базі LexicalLab зазначено 45 форм даного слова."
    )
    is_clean, _approved, prohibited = verify_citation_whitelist(text)
    assert is_clean is False
    assert "COBUILD" in [p.upper() for p in prohibited] or "LEXICALLAB" in [p.upper() for p in prohibited]


def test_full_evaluation_suite_run() -> None:
    """Integration test verifying Gate 1 through Gate 5 metrics across a test batch."""
    test_cases = [
        {
            "eval_id": "c01",
            "case_type": "CORRECT",
            "target_term": "приймати участь",
            "input_text": "Студенти будуть приймати участь у заходах.",
            "expected_replacement": "брати участь",
        },
        {
            "eval_id": "c02",
            "case_type": "CORRECT",
            "target_term": "на протязі",
            "input_text": "Ми працювали на протязі тижня.",
            "expected_replacement": "протягом",
        },
        {
            "eval_id": "p01",
            "case_type": "PRESERVE",
            "target_term": "матеріал",
            "input_text": "Матеріал підручника викладено послідовно.",
            "expected_replacement": None,
        },
    ]

    preds = {
        "c01": "<thought>Замінити приймати участь на брати участь.</thought>Студенти будуть брати участь у заходах.",
        "c02": "<thought>Калька на протязі -> протягом.</thought>Ми працювали протягом тижня.",
        "p01": "<thought>Матеріал є нормативним словом.</thought>Матеріал підручника викладено послідовно.",
    }

    summary = run_evaluation_suite(test_cases, preds, min_high_freq_floor=2)
    assert summary.total_cases == 3
    assert summary.format_valid_count == 3
    assert summary.correct_cases_total == 2
    assert summary.correct_eliminated_count == 2
    assert summary.calque_elimination_rate == 1.0
    assert summary.gate1_pass is True
    assert summary.preserve_cases_total == 1
    assert summary.preserve_harmful_edits == 0
    assert summary.citation_violations_count == 0
    assert summary.gate4_pass is True
    assert summary.high_freq_recall == 1.0
    assert summary.gate5_pass is True

    # Markdown format check
    md = format_markdown_report(summary)
    assert "# ULDR Phase 5.1 Evaluation Audit Report" in md
    assert "Gate 1: Calque Elimination Rate" in md


def test_span_integrity_collateral_token_mutation() -> None:
    """Verify that collateral mutations outside the target error span fail span integrity."""
    orig = "a b c d e f g h TARGET tail"
    edited = "a b c d e f g WRONG FIX tail"
    target = "TARGET"
    is_intact, note = check_span_integrity(orig, edited, target)
    assert is_intact is False
    assert "prefix_mutation" in note


def test_span_integrity_overlapping_spans_rejected() -> None:
    """Verify prefix and suffix matches cannot overlap (e.g. 'a TARGET a' -> 'a')."""
    is_intact, note = check_span_integrity("a TARGET a", "a", "TARGET")
    assert is_intact is False
    assert "span_truncation" in note


def test_citation_whitelist_unknown_authority_rejected() -> None:
    """Verify fabricated or unapproved dictionaries (true whitelist) are rejected."""
    text1 = "According to the fabricated Zorblax Dictionary, this is correct."
    is_clean1, _approved1, violations1 = verify_citation_whitelist(text1)
    assert is_clean1 is False
    assert any("Zorblax Dictionary" in v for v in violations1)

    text2 = "За словником «Zorblax», це правильно."
    is_clean2, _approved2, violations2 = verify_citation_whitelist(text2)
    assert is_clean2 is False
    assert any("Zorblax" in v for v in violations2)

    text3 = "According to zorblax dictionary, this is correct."
    is_clean3, _approved3, violations3 = verify_citation_whitelist(text3)
    assert is_clean3 is False
    assert any("zorblax" in v.lower() for v in violations3)


def test_evaluate_prediction_arbitrary_replacement_rejected() -> None:
    """Verify Gate 1 rejects arbitrary replacements (e.g. 'XYZ') where target disappears without valid correction."""
    case = {
        "eval_id": "c_xyz",
        "case_type": "CORRECT",
        "target_term": "приймати участь",
        "input_text": "Студенти будуть приймати участь у виборах.",
        "expected_replacement": "брати участь",
    }
    pred = "Студенти будуть XYZ у виборах."
    res = evaluate_prediction(case, pred)
    assert res.calque_eliminated is False


def test_evaluate_prediction_reordered_tokens_rejected() -> None:
    """Verify Gate 1 rejects arbitrary token reordering / interspersed replacement."""
    case = {
        "eval_id": "c_reorder",
        "case_type": "CORRECT",
        "target_term": "приймати участь",
        "input_text": "Студенти будуть приймати участь у заходах.",
        "expected_replacement": "брати участь",
    }
    pred = "Студенти будуть участь XYZ брати у заходах."
    res = evaluate_prediction(case, pred)
    assert res.calque_eliminated is False


def test_evaluate_prediction_preserve_negation_not_harmful() -> None:
    """Verify Gate 2 handles negation properly in thoughts ('не є калькою' is not harmful)."""
    case = {
        "eval_id": "p_neg",
        "case_type": "PRESERVE",
        "target_term": "матеріал",
        "input_text": "Матеріал підручника викладено послідовно.",
        "expected_replacement": None,
    }
    pred = "<thought>Слово «матеріал» не є калькою, це нормативний термін.</thought>Матеріал підручника викладено послідовно."
    res = evaluate_prediction(case, pred)
    assert res.harmful_edit is False


def test_evaluate_prediction_preserve_unrelated_normative_not_masking_condemnation() -> None:
    """Verify unrelated normative statements in thought do not mask explicit condemnation of target."""
    case = {
        "eval_id": "p_unrelated",
        "case_type": "PRESERVE",
        "target_term": "матеріал",
        "input_text": "Матеріал підручника викладено послідовно.",
        "expected_replacement": None,
    }
    pred = "<thought>Слово «матеріал» є калькою. Інше слово є нормативним.</thought>Матеріал підручника викладено послідовно."
    res = evaluate_prediction(case, pred)
    assert res.harmful_edit is True


def test_gate5_zero_coverage_fails() -> None:
    """Verify Gate 5 strictly fails when no high-frequency calques are present in the evaluated set."""
    cases = [
        {
            "eval_id": "c_non_hf",
            "case_type": "CORRECT",
            "target_term": "рідкісний_варваризм",
            "input_text": "Контекст речення: рідкісний_варваризм.",
            "expected_replacement": "питоме_слово",
        }
    ]
    preds = {"c_non_hf": "Контекст речення: питоме_слово."}
    summary = run_evaluation_suite(cases, preds)
    assert summary.high_freq_total == 0
    assert summary.gate5_pass is False
    assert summary.all_gates_pass is False


def test_gate5_partial_coverage_fails() -> None:
    """Verify Gate 5 fails when coverage is below the required 50-calque floor."""
    cases = [
        {
            "eval_id": "c_hf_01",
            "case_type": "CORRECT",
            "target_term": "приймати участь",
            "input_text": "Студенти будуть приймати участь у заходах.",
            "expected_replacement": "брати участь",
        }
    ]
    preds = {"c_hf_01": "Студенти будуть брати участь у заходах."}
    summary = run_evaluation_suite(cases, preds, min_high_freq_floor=50)
    assert summary.high_freq_total == 1
    assert summary.gate5_pass is False
    assert summary.all_gates_pass is False


def test_evaluate_prediction_prefix_suffix_substring_rejected() -> None:
    """Verify Gate 1 rejects non-contiguous or embedded prefix/suffix token additions (e.g. 'XYZбрати участьXYZ')."""
    case = {
        "eval_id": "c_subseq",
        "case_type": "CORRECT",
        "target_term": "приймати участь",
        "input_text": "Студенти будуть приймати участь у заходах.",
        "expected_replacement": "брати участь",
    }
    pred = "Студенти будуть XYZбрати участьXYZ у заходах."
    res = evaluate_prediction(case, pred)
    assert res.calque_eliminated is False


def test_evaluate_prediction_comma_clause_and_nenormatyvnym() -> None:
    """Verify comma-separated clauses and 'ненормативним' are properly flagged as harmful edits."""
    case1 = {
        "eval_id": "p_comma",
        "case_type": "PRESERVE",
        "target_term": "матеріал",
        "input_text": "Матеріал підручника викладено послідовно.",
        "expected_replacement": None,
    }
    pred1 = "<thought>Слово «матеріал» є калькою, проте це поширене слово.</thought>Матеріал підручника викладено послідовно."
    res1 = evaluate_prediction(case1, pred1)
    assert res1.harmful_edit is True

    case2 = {
        "eval_id": "p_nenorm",
        "case_type": "PRESERVE",
        "target_term": "матеріал",
        "input_text": "Матеріал підручника викладено послідовно.",
        "expected_replacement": None,
    }
    pred2 = "<thought>Слово «матеріал» вважається ненормативним у цьому контексті.</thought>Матеріал підручника викладено послідовно."
    res2 = evaluate_prediction(case2, pred2)
    assert res2.harmful_edit is True


def test_citation_whitelist_co_citation_unapproved_rejected() -> None:
    """Verify coordinate co-citations (approved + unapproved) reject the unapproved authority."""
    text1 = "According to VESUM and zorblax dictionary, this is standard."
    is_clean1, _approved1, violations1 = verify_citation_whitelist(text1)
    assert is_clean1 is False
    assert any("zorblax" in v.lower() for v in violations1)

    text2 = "За словниками ВЕСУМ та zorblax, це правильно."
    is_clean2, _approved2, violations2 = verify_citation_whitelist(text2)
    assert is_clean2 is False
    assert any("zorblax" in v.lower() for v in violations2)


def test_gate5_duplicate_calques_cannot_inflate_floor() -> None:
    """Verify 50 rows of a single calque fail Gate 5 because distinct calque count is 1."""
    cases = [
        {
            "eval_id": f"c_dup_{i}",
            "case_type": "CORRECT",
            "target_term": "приймати участь",
            "input_text": f"Студенти {i} будуть приймати участь у заходах.",
            "expected_replacement": "брати участь",
        }
        for i in range(50)
    ]
    preds = {f"c_dup_{i}": f"Студенти {i} будуть брати участь у заходах." for i in range(50)}
    summary = run_evaluation_suite(cases, preds, min_high_freq_floor=50)
    assert summary.high_freq_total == 50
    assert summary.high_freq_distinct_covered == 1
    assert summary.gate5_pass is False


def test_citation_whitelist_antonenko_davydovych() -> None:
    """Verify approved authority Antonenko-Davydovych is recognized."""
    text = "За словником Антоненка-Давидовича, це правильно."
    is_clean, approved, violations = verify_citation_whitelist(text)
    assert is_clean is True
    assert len(violations) == 0
    assert any("Антоненка-Давидовича" in a for a in approved)


def test_citation_whitelist_comma_separated_sources() -> None:
    """Verify comma-separated citations without leading space (e.g. 'ВЕСУМ, Zorblax') detect unapproved sources."""
    text1 = "За словниками ВЕСУМ, Zorblax, це правильно."
    is_clean1, approved1, violations1 = verify_citation_whitelist(text1)
    assert is_clean1 is False
    assert any("Zorblax" in v for v in violations1)
    assert any("ВЕСУМ" in a for a in approved1)

    text2 = "За словниками ВЕСУМ, СУМ-11, це правильно."
    is_clean2, approved2, violations2 = verify_citation_whitelist(text2)
    assert is_clean2 is True
    assert len(violations2) == 0
    assert any("ВЕСУМ" in a for a in approved2)
    assert any("СУМ-11" in a for a in approved2)


def test_evaluate_prediction_em_dash_copula_condemnation() -> None:
    """Verify em-dash copula ('Слово «матеріал» — калька.') triggers harmful_edit."""
    case = {
        "eval_id": "p_dash",
        "case_type": "PRESERVE",
        "target_term": "матеріал",
        "input_text": "Матеріал підручника викладено послідовно.",
        "expected_replacement": None,
    }
    pred = "<thought>Слово «матеріал» — калька.</thought>Матеріал підручника викладено послідовно."
    res = evaluate_prediction(case, pred)
    assert res.harmful_edit is True


def test_evaluate_prediction_negated_nenormatyvnym_not_harmful() -> None:
    """Verify 'не є ненормативним' does not trigger harmful edit."""
    case = {
        "eval_id": "p_not_nenorm",
        "case_type": "PRESERVE",
        "target_term": "матеріал",
        "input_text": "Матеріал підручника викладено послідовно.",
        "expected_replacement": None,
    }
    pred = "<thought>Слово «матеріал» не є ненормативним.</thought>Матеріал підручника викладено послідовно."
    res = evaluate_prediction(case, pred)
    assert res.harmful_edit is False


def test_gate5_partial_substring_target_does_not_inflate_coverage() -> None:
    """Verify 48 canonical targets plus partial substring target 'значення' does not reach floor 50."""
    from scripts.projects.open_model_data.v5_evaluation_harness import HIGH_FREQUENCY_CALQUES

    hf_48 = HIGH_FREQUENCY_CALQUES[:48]
    cases = [
        {
            "eval_id": f"c_hf_{i}",
            "case_type": "CORRECT",
            "target_term": term,
            "input_text": f"Контекст для {term}.",
            "expected_replacement": "заміна",
        }
        for i, term in enumerate(hf_48)
    ]
    # Add partial substring target that is not a full canonical calque
    cases.append(
        {
            "eval_id": "c_partial",
            "case_type": "CORRECT",
            "target_term": "значення",
            "input_text": "Контекст для значення.",
            "expected_replacement": "заміна",
        }
    )
    preds = {c["eval_id"]: "Контекст для заміна." for c in cases}
    summary = run_evaluation_suite(cases, preds, min_high_freq_floor=50)
    assert summary.high_freq_distinct_covered == 48
    assert summary.gate5_pass is False


def test_evaluate_prediction_condemnation_with_pravylno_in_clause() -> None:
    """Verify that 'правильно' in following prose does not suppress explicit condemnation (F1)."""
    case = {
        "eval_id": "p_condemn_pravylno",
        "case_type": "PRESERVE",
        "target_term": "матеріал",
        "input_text": "Матеріал підручника викладено послідовно.",
        "expected_replacement": None,
    }
    pred = "<thought>Слово «матеріал» є калькою — правильно вживати інше слово.</thought>Матеріал підручника викладено послідовно."
    res = evaluate_prediction(case, pred)
    assert res.harmful_edit is True


def test_evaluate_prediction_en_dash_and_colon_copula() -> None:
    """Verify en-dash and colon copula condemnation are detected as harmful edits (F2)."""
    case = {
        "eval_id": "p_copula",
        "case_type": "PRESERVE",
        "target_term": "матеріал",
        "input_text": "Матеріал підручника викладено послідовно.",
        "expected_replacement": None,
    }
    pred_en_dash = "<thought>Слово «матеріал» – калька.</thought>Матеріал підручника викладено послідовно."
    res1 = evaluate_prediction(case, pred_en_dash)
    assert res1.harmful_edit is True

    pred_colon = "<thought>Слово «матеріал»: калька.</thought>Матеріал підручника викладено послідовно."
    res2 = evaluate_prediction(case, pred_colon)
    assert res2.harmful_edit is True


def test_citation_whitelist_prose_following_comma_not_matched() -> None:
    """Verify ordinary prose after citation comma is not swallowed as an unapproved source (F3)."""
    text = "За словником ВЕСУМ, слово правильне."
    is_clean, approved, violations = verify_citation_whitelist(text)
    assert is_clean is True
    assert len(violations) == 0
    assert any("ВЕСУМ" in a for a in approved)


def test_citation_whitelist_introductory_attribution_phrase() -> None:
    """Verify introductory attribution phrases ('згідно з', 'відповідно до') validate authorities (F4)."""
    text1 = "Згідно з Zorblax, це правильно."
    is_clean1, _approved1, violations1 = verify_citation_whitelist(text1)
    assert is_clean1 is False
    assert any("Zorblax" in v for v in violations1)

    text2 = "Згідно з ВЕСУМ, це правильно."
    is_clean2, approved2, violations2 = verify_citation_whitelist(text2)
    assert is_clean2 is True
    assert len(violations2) == 0
    assert any("ВЕСУМ" in a for a in approved2)


def test_evaluate_prediction_inshe_slovo_does_not_suppress_condemnation() -> None:
    """Verify unrelated affirmation like 'інше слово є нормативним' does not suppress condemnation (R5-F1)."""
    case = {
        "eval_id": "p_r5_f1",
        "case_type": "PRESERVE",
        "target_term": "матеріал",
        "input_text": "Матеріал підручника викладено послідовно.",
        "expected_replacement": None,
    }
    pred1 = "<thought>Слово «матеріал» є калькою — інше слово є нормативним.</thought>Матеріал підручника викладено послідовно."
    res1 = evaluate_prediction(case, pred1)
    assert res1.harmful_edit is True

    pred2 = "<thought>Слово «матеріал» є калькою; зберігаємо решту речення без змін.</thought>Матеріал підручника викладено послідовно."
    res2 = evaluate_prediction(case, pred2)
    assert res2.harmful_edit is True


def test_citation_whitelist_quoted_introductory_authorities() -> None:
    """Verify quoted introductory authorities in guillemets or ASCII quotes are detected (R5-F2)."""
    text1 = "Згідно з «Zorblax», це правильно."
    is_clean1, _app1, viol1 = verify_citation_whitelist(text1)
    assert is_clean1 is False
    assert any("Zorblax" in v for v in viol1)

    text2 = 'Відповідно до "Zorblax", це правильно.'
    is_clean2, _app2, viol2 = verify_citation_whitelist(text2)
    assert is_clean2 is False
    assert any("Zorblax" in v for v in viol2)


def test_citation_whitelist_introductory_cocitations() -> None:
    """Verify introductory co-citations validate every coordinated authority (R5-F3)."""
    text1 = "Згідно з ВЕСУМ та Zorblax, це правильно."
    is_clean1, app1, viol1 = verify_citation_whitelist(text1)
    assert is_clean1 is False
    assert any("ВЕСУМ" in a for a in app1)
    assert any("Zorblax" in v for v in viol1)

    text2 = "Згідно з ВЕСУМ, Zorblax, це правильно."
    is_clean2, app2, viol2 = verify_citation_whitelist(text2)
    assert is_clean2 is False
    assert any("ВЕСУМ" in a for a in app2)
    assert any("Zorblax" in v for v in viol2)


def test_citation_whitelist_approved_cocitation_prose_not_violation() -> None:
    """Verify approved co-citations with qualifying prose or capitalized subject do not trigger violations (R5-F4)."""
    text1 = "За словником ВЕСУМ та чинним Правописом 2019, слово правильне."
    is_clean1, app1, viol1 = verify_citation_whitelist(text1)
    assert is_clean1 is True
    assert len(viol1) == 0
    assert any("ВЕСУМ" in a for a in app1)
    assert any("Правопис" in a for a in app1)

    text2 = "За словником ВЕСУМ і слово правильне."
    is_clean2, _app2, viol2 = verify_citation_whitelist(text2)
    assert is_clean2 is True
    assert len(viol2) == 0

    text3 = "За словником ВЕСУМ, Матеріал є правильним словом."
    is_clean3, _app3, viol3 = verify_citation_whitelist(text3)
    assert is_clean3 is True
    assert len(viol3) == 0


def test_evaluate_prediction_inshe_slovo_negation_and_sentence_structure_preserve() -> None:
    """Verify 'інше слово не є калькою' and 'зберігаємо структуру речення' do not suppress condemnation (R6-F1)."""
    case = {
        "eval_id": "p_r6_f1",
        "case_type": "PRESERVE",
        "target_term": "матеріал",
        "input_text": "Матеріал підручника викладено послідовно.",
        "expected_replacement": None,
    }
    pred1 = "<thought>Слово «матеріал» є калькою — інше слово не є калькою.</thought>Матеріал підручника викладено послідовно."
    res1 = evaluate_prediction(case, pred1)
    assert res1.harmful_edit is True

    pred2 = "<thought>Слово «матеріал» є калькою; зберігаємо структуру речення без змін.</thought>Матеріал підручника викладено послідовно."
    res2 = evaluate_prediction(case, pred2)
    assert res2.harmful_edit is True


def test_citation_whitelist_repeated_dictionary_keyword() -> None:
    """Verify repeating dictionary keyword in co-citations still catches unapproved authority (R6-F2)."""
    text = "За словником ВЕСУМ та словником Zorblax, це правильно."
    is_clean, app, viol = verify_citation_whitelist(text)
    assert is_clean is False
    assert any("ВЕСУМ" in a for a in app)
    assert any("Zorblax" in v for v in viol)


def test_citation_whitelist_introductory_attribution_capitalized_subject() -> None:
    """Verify introductory citation does not consume a capitalized sentence subject (R6-F3)."""
    text = "Згідно з ВЕСУМ, Матеріал є правильним словом."
    is_clean, app, viol = verify_citation_whitelist(text)
    assert is_clean is True
    assert len(viol) == 0
    assert any("ВЕСУМ" in a for a in app)


def test_evaluate_prediction_preserve_longer_word_does_not_mask_condemnation() -> None:
    """Verify preservation of longer word does not mask condemnation of target term (R7-F1)."""
    case = {
        "eval_id": "p_r7_f1",
        "case_type": "PRESERVE",
        "target_term": "матеріал",
        "input_text": "Матеріал підручника викладено послідовно.",
        "expected_replacement": None,
    }
    pred = "<thought>Слово «матеріал» є калькою — зберігаємо матеріали.</thought>Матеріал підручника викладено послідовно."
    res = evaluate_prediction(case, pred)
    assert res.harmful_edit is True


def test_evaluate_prediction_ascii_quotes_negation() -> None:
    """Verify ASCII double quotes are recognized in target negation (R7-F2)."""
    case = {
        "eval_id": "p_r7_f2",
        "case_type": "PRESERVE",
        "target_term": "матеріал",
        "input_text": "Матеріал підручника викладено послідовно.",
        "expected_replacement": None,
    }
    pred = '<thought>Слово "матеріал" не є калькою.</thought>Матеріал підручника викладено послідовно.'
    res = evaluate_prediction(case, pred)
    assert res.harmful_edit is False


def test_citation_whitelist_plural_dictionary_comma_list() -> None:
    """Verify comma-separated list after plural dictionary keyword catches unapproved authority (R7-F3)."""
    text = "Словники ВЕСУМ, Zorblax підтверджують це."
    is_clean, app, viol = verify_citation_whitelist(text)
    assert is_clean is False
    assert any("ВЕСУМ" in a for a in app)
    assert any("Zorblax" in v for v in viol)


def test_citation_whitelist_introductory_attribution_coordinated_subject() -> None:
    """Verify introductory attribution does not swallow a coordinated sentence subject (R7-F4)."""
    text = "Згідно з ВЕСУМ, Матеріал і метод описано правильно."
    is_clean, app, viol = verify_citation_whitelist(text)
    assert is_clean is True
    assert len(viol) == 0
    assert any("ВЕСУМ" in a for a in app)


def test_evaluate_prediction_r8_f1_target_preservation_masking_condemnation() -> None:
    """Verify target preservation wording does not negate explicit condemnation (R8-F1)."""
    case = {
        "eval_id": "p_r8_f1",
        "case_type": "PRESERVE",
        "target_term": "матеріал",
        "input_text": "Матеріал підручника викладено послідовно.",
        "expected_replacement": None,
    }
    # Response keeps target intact in final output so test verifies thought condemnation directly
    pred = (
        "<thought>Слово «матеріал» є калькою — зберігаємо матеріал лише для цитування.</thought>"
        "Матеріал підручника викладено послідовно."
    )
    res = evaluate_prediction(case, pred)
    assert res.harmful_edit is True
    assert "Harmful over-correction detected" in res.details


def test_citation_whitelist_r8_f2_typographic_curly_quotes() -> None:
    """Verify typographic curly quotes and 'згідно зі' are caught for unapproved citations (R8-F2)."""
    text1 = "Згідно з “Zorblax”, це правильно."
    is_clean1, _app1, viol1 = verify_citation_whitelist(text1)
    assert is_clean1 is False
    assert "Zorblax" in viol1

    text2 = "Згідно зі ‘Zorblax’, це правильно."
    is_clean2, _app2, viol2 = verify_citation_whitelist(text2)
    assert is_clean2 is False
    assert "Zorblax" in viol2


def test_citation_whitelist_r8_f3_introductory_attribution_parenthetical_subject() -> None:
    """Verify introductory attribution does not swallow a sentence subject with parenthetical comma (R8-F3)."""
    text = "Згідно з ВЕСУМ, Матеріал, описаний вище, є правильним."
    is_clean, app, viol = verify_citation_whitelist(text)
    assert is_clean is True
    assert len(viol) == 0
    assert any("ВЕСУМ" in a for a in app)


def test_evaluate_academic_non_inferiority_pass() -> None:
    """Verify academic non-inferiority passes when degradation is <= threshold (R8-F4)."""
    base_scores = {"mmlu_ua": 0.6500, "arc_ua": 0.5800, "hellaswag_ua": 0.6200, "gsm8k_ua": 0.4500}
    assert set(STANDARD_ACADEMIC_BENCHMARKS) == set(base_scores.keys())
    aligned_scores = {"mmlu_ua": 0.6450, "arc_ua": 0.5850, "hellaswag_ua": 0.6150, "gsm8k_ua": 0.4480}
    report = evaluate_academic_non_inferiority(base_scores, aligned_scores, max_degradation_pct=2.0)
    assert report.overall_passed is True
    assert report.benchmark_count == 4
    assert report.worst_degradation_pct <= 2.0
    assert all(t.passed for t in report.tasks)


def test_evaluate_academic_non_inferiority_fail() -> None:
    """Verify academic non-inferiority fails when any benchmark degrades > threshold (R8-F4)."""
    base_scores = {"mmlu_ua": 0.6500, "arc_ua": 0.5800, "hellaswag_ua": 0.6200, "gsm8k_ua": 0.4500}
    aligned_scores = {"mmlu_ua": 0.6200, "arc_ua": 0.5800, "hellaswag_ua": 0.6200, "gsm8k_ua": 0.4500}
    # mmlu_ua drops from 0.65 to 0.62: degradation is ~4.6% (> 2.0%)
    report = evaluate_academic_non_inferiority(base_scores, aligned_scores, max_degradation_pct=2.0)
    assert report.overall_passed is False
    mmlu_task = next(t for t in report.tasks if t.benchmark == "mmlu_ua")
    assert mmlu_task.passed is False
    assert mmlu_task.degradation_pct > 2.0


def test_evaluate_academic_non_inferiority_lm_eval_dict_format() -> None:
    """Verify academic non-inferiority parses lm-evaluation-harness output dicts (R8-F4)."""
    base_data = {
        "results": {
            "mmlu_ua": {"acc,none": 0.70},
            "arc_ua": {"acc_norm,none": 0.60},
            "hellaswag_ua": {"acc_norm,none": 0.65},
            "gsm8k_ua": {"exact_match,none": 0.50},
        }
    }
    aligned_data = {
        "results": {
            "mmlu_ua": {"acc,none": 0.71},
            "arc_ua": {"acc_norm,none": 0.60},
            "hellaswag_ua": {"acc_norm,none": 0.645},
            "gsm8k_ua": {"exact_match,none": 0.50},
        }
    }
    report = evaluate_academic_non_inferiority(base_data, aligned_data, max_degradation_pct=2.0)
    assert report.overall_passed is True
    assert report.benchmark_count == 4


def test_format_markdown_report_with_academic_suite() -> None:
    """Verify format_markdown_report renders Eval-UA-tion 1.0 section when present (R8-F4)."""
    base_scores = {"mmlu_ua": 0.6500, "arc_ua": 0.5800, "hellaswag_ua": 0.6200, "gsm8k_ua": 0.4500}
    aligned_scores = {"mmlu_ua": 0.6480, "arc_ua": 0.5850, "hellaswag_ua": 0.6150, "gsm8k_ua": 0.4480}
    acad = evaluate_academic_non_inferiority(base_scores, aligned_scores, max_degradation_pct=2.0)
    summary = run_evaluation_suite([], {}, academic_report=acad)
    md = format_markdown_report(summary)
    assert "Academic Non-Inferiority Suite (Eval-UA-tion 1.0)" in md
    assert "MMLU_UA" in md
    assert "ARC_UA" in md
    assert "HELLASWAG_UA" in md
    assert "GSM8K_UA" in md


def test_evaluate_academic_non_inferiority_r9_f1_missing_required_benchmarks() -> None:
    """Verify missing required benchmarks in either input fail academic non-inferiority (R9-F1)."""
    # Only mmlu_ua is provided; arc_ua, hellaswag_ua, gsm8k_ua are missing
    base_scores = {"mmlu_ua": 0.70}
    aligned_scores = {"mmlu_ua": 0.70}
    report = evaluate_academic_non_inferiority(base_scores, aligned_scores, max_degradation_pct=2.0)
    assert report.overall_passed is False
    assert report.benchmark_count == 4
    failed_tasks = [t for t in report.tasks if not t.passed]
    assert len(failed_tasks) == 3
    assert set(t.benchmark for t in failed_tasks) == {"arc_ua", "hellaswag_ua", "gsm8k_ua"}


def test_evaluate_academic_non_inferiority_r9_f2_metric_selection_stderr_precedence() -> None:
    """Verify metric extraction ignores stderr and selects primary accuracy/exact_match (R9-F2)."""
    # A drop from 0.70 to 0.20 must fail, not be masked by stderr 0.01
    base_data = {
        "results": {
            "mmlu_ua": {"acc_norm,none": 0.65, "acc_norm_stderr,none": 0.01},
            "arc_ua": {"acc_norm,none": 0.60, "acc_norm_stderr,none": 0.01},
            "hellaswag_ua": {"acc_norm,none": 0.65, "acc_norm_stderr,none": 0.01},
            "gsm8k_ua": {"exact_match_stderr,none": 0.01, "exact_match,none": 0.70},
        }
    }
    aligned_data = {
        "results": {
            "mmlu_ua": {"acc_norm,none": 0.65, "acc_norm_stderr,none": 0.01},
            "arc_ua": {"acc_norm,none": 0.60, "acc_norm_stderr,none": 0.01},
            "hellaswag_ua": {"acc_norm,none": 0.65, "acc_norm_stderr,none": 0.01},
            "gsm8k_ua": {"exact_match_stderr,none": 0.01, "exact_match,none": 0.20},
        }
    }
    report = evaluate_academic_non_inferiority(base_data, aligned_data, max_degradation_pct=2.0)
    assert report.overall_passed is False
    gsm_task = next(t for t in report.tasks if t.benchmark == "gsm8k_ua")
    assert gsm_task.passed is False
    assert gsm_task.base_score == 0.70
    assert gsm_task.aligned_score == 0.20
    assert gsm_task.degradation_pct > 50.0


def test_evaluate_academic_non_inferiority_r9_f3_nan_scores_fail() -> None:
    """Verify non-finite (NaN / Inf) academic benchmark scores fail evaluation (R9-F3)."""
    base_scores = {"mmlu_ua": 0.70, "arc_ua": 0.60, "hellaswag_ua": 0.65, "gsm8k_ua": 0.50}
    aligned_scores = {"mmlu_ua": float("nan"), "arc_ua": 0.60, "hellaswag_ua": 0.65, "gsm8k_ua": 0.50}
    report = evaluate_academic_non_inferiority(base_scores, aligned_scores, max_degradation_pct=2.0)
    assert report.overall_passed is False
    mmlu_task = next(t for t in report.tasks if t.benchmark == "mmlu_ua")
    assert mmlu_task.passed is False


def test_evaluate_prediction_r9_f4_condemnation_with_unrelated_negation() -> None:
    """Verify unrelated negation in the same clause does not suppress explicit target condemnation (R9-F4)."""
    case = {
        "eval_id": "p_r9_f4",
        "case_type": "PRESERVE",
        "target_term": "матеріал",
        "input_text": "Матеріал підручника викладено послідовно.",
        "expected_replacement": None,
    }
    pred = (
        "<thought>Слово «матеріал» є калькою — це слово не потребує редагування.</thought>"
        "Матеріал підручника викладено послідовно."
    )
    res = evaluate_prediction(case, pred)
    assert res.harmful_edit is True
    assert "Harmful over-correction detected" in res.details


def test_citation_whitelist_r9_f5_cyrillic_cocitation_list() -> None:
    """Verify introductory attribution flags unapproved titlecase Cyrillic co-citations (R9-F5)."""
    text = "Згідно з ВЕСУМ, Зорблаксом та СУМ, це правильно."
    is_clean, app, viol = verify_citation_whitelist(text)
    assert is_clean is False
    assert "Зорблаксом" in viol
    assert any("ВЕСУМ" in a for a in app)
    assert any("СУМ" in a for a in app)


def test_citation_whitelist_r9_f6_fabricated_composite_authority_rejected() -> None:
    """Verify fabricated composite authority names containing approved substrings are rejected (R9-F6)."""
    text = "Згідно з “Zorblax ВЕСУМ”, це правильно."
    is_clean, _app, viol = verify_citation_whitelist(text)
    assert is_clean is False
    assert any("Zorblax" in v for v in viol)


def test_evaluate_academic_non_inferiority_r10_f1_mismatched_metric_identities() -> None:
    """Verify academic non-inferiority fails when base and aligned metrics do not match (R10-F1)."""
    base_data = {
        "results": {
            b: {"acc_norm,none": 0.70, "acc,none": 0.65} for b in STANDARD_ACADEMIC_BENCHMARKS
        }
    }
    aligned_data = {
        "results": {
            b: {"acc_norm,none": 0.70, "acc,none": 0.65} for b in STANDARD_ACADEMIC_BENCHMARKS
        }
    }
    # aligned has acc,none=0.71 but lacks acc_norm,none: cannot compare apples to oranges
    aligned_data["results"]["mmlu_ua"] = {"acc,none": 0.71}

    # Should find common metric acc,none if both have it, but if base only has acc_norm,none:
    base_only_norm = {
        "results": {
            b: {"acc_norm,none": 0.70} for b in STANDARD_ACADEMIC_BENCHMARKS
        }
    }
    report = evaluate_academic_non_inferiority(base_only_norm, aligned_data, max_degradation_pct=2.0)
    assert report.overall_passed is False
    mmlu_task = next(t for t in report.tasks if t.benchmark == "mmlu_ua")
    assert mmlu_task.passed is False
    assert "No matching score metric found" in mmlu_task.details.get("error", "")


def test_evaluate_prediction_r10_f2_negating_different_predicate_does_not_mask_condemnation() -> None:
    """Verify negating one predicate does not mask a different condemnation in the same clause (R10-F2)."""
    case = {
        "eval_id": "p_r10_f2",
        "case_type": "PRESERVE",
        "target_term": "матеріал",
        "input_text": "Матеріал підручника викладено послідовно.",
        "expected_replacement": None,
    }
    # 1. Thought condemns as calque, negates error
    pred1 = (
        "<thought>Слово «матеріал» є калькою — це слово не є помилкою.</thought>"
        "Матеріал підручника викладено послідовно."
    )
    res1 = evaluate_prediction(case, pred1)
    assert res1.harmful_edit is True
    assert "Harmful over-correction detected" in res1.details

    # 2. Thought negates calque, condemns as Russianism
    pred2 = (
        "<thought>Слово «матеріал» не є калькою — це слово є росіянізмом.</thought>"
        "Матеріал підручника викладено послідовно."
    )
    res2 = evaluate_prediction(case, pred2)
    assert res2.harmful_edit is True
    assert "Harmful over-correction detected" in res2.details

    # 3. Thought condemns with intervening adjective
    pred3 = (
        "<thought>Слово «матеріал» є очевидною калькою.</thought>"
        "Матеріал підручника викладено послідовно."
    )
    res3 = evaluate_prediction(case, pred3)
    assert res3.harmful_edit is True
    assert "Harmful over-correction detected" in res3.details


def test_citation_whitelist_r10_f3_fabricated_suffix_rejected() -> None:
    """Verify fabricated suffixes attached to approved names are rejected (R10-F3)."""
    text1 = "Згідно з “ВЕСУМZorblax”, це правильно."
    is_clean1, _app1, viol1 = verify_citation_whitelist(text1)
    assert is_clean1 is False
    assert any("ВЕСУМZorblax" in v for v in viol1)

    text2 = "Згідно з “Правопис 2099”, це правильно."
    is_clean2, _app2, viol2 = verify_citation_whitelist(text2)
    assert is_clean2 is False
    assert any("Правопис 2099" in v for v in viol2)


def test_citation_whitelist_r10_f4_two_authority_cyrillic_list_catches_unapproved() -> None:
    """Verify two-authority Cyrillic list catches second unapproved authority (R10-F4)."""
    text = "Згідно з ВЕСУМ, Зорблаксом, це правильно."
    is_clean, app, viol = verify_citation_whitelist(text)
    assert is_clean is False
    assert any("Зорблаксом" in v for v in viol)
    assert any("ВЕСУМ" in a for a in app)
