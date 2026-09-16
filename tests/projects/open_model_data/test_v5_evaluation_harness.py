"""Unit and regression tests for Phase 5.1 Automated Evaluation Suite (ULDR #8050)."""

from __future__ import annotations

import pytest

from scripts.projects.open_model_data.v5_evaluation_harness import (
    STANDARD_ACADEMIC_BENCHMARKS,
    check_span_integrity,
    evaluate_academic_non_inferiority,
    evaluate_prediction,
    exact_clopper_pearson_upper,
    extract_benchmark_score,
    format_markdown_report,
    is_approved_authority,
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

    # Russian-Soviet occupation SUM-11 is quarantined and must be rejected as an unapproved positive authority
    text2 = "За словниками ВЕСУМ, СУМ-11, це правильно."
    is_clean2, approved2, violations2 = verify_citation_whitelist(text2)
    assert is_clean2 is False
    assert any("СУМ-11" in v for v in violations2)
    assert any("ВЕСУМ" in a for a in approved2)

    # Modern decolonized SUM-20 is approved
    text3 = "За словниками ВЕСУМ, СУМ-20, це правильно."
    is_clean3, approved3, violations3 = verify_citation_whitelist(text3)
    assert is_clean3 is True
    assert len(violations3) == 0
    assert any("ВЕСУМ" in a for a in approved3)
    assert any("СУМ-20" in a for a in approved3)


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
    # When citing modern decolonized СУМ-20 alongside ВЕСУМ and an unapproved authority
    text = "Згідно з ВЕСУМ, Зорблаксом та СУМ-20, це правильно."
    is_clean, app, viol = verify_citation_whitelist(text)
    assert is_clean is False
    assert "Зорблаксом" in viol
    assert "ВЕСУМ" in app
    assert "СУМ-20" in app

    # Verify bare unversioned СУМ is rejected as ambiguous/unapproved (neither -11 nor bare is allowed)
    bare_text = "Згідно з ВЕСУМ, Зорблаксом та СУМ, це правильно."
    bare_clean, bare_app, bare_viol = verify_citation_whitelist(bare_text)
    assert bare_clean is False
    assert "Зорблаксом" in bare_viol
    assert "СУМ" in bare_viol
    assert "ВЕСУМ" in bare_app
    assert "СУМ" not in bare_app


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


def test_evaluate_academic_non_inferiority_r11_f1_metadata_samples_rejected() -> None:
    """Verify non-score metadata fields like 'samples' are not compared as scores (R11-F1)."""
    base_scores = {
        "mmlu_ua": {"acc_norm,none": 0.70, "samples": 100},
        "arc_ua": {"acc_norm,none": 0.60, "samples": 100},
        "hellaswag_ua": {"acc_norm,none": 0.65, "samples": 100},
        "gsm8k_ua": {"exact_match,none": 0.50, "samples": 100},
    }
    aligned_scores = {
        "mmlu_ua": {"acc,none": 0.10, "samples": 100},
        "arc_ua": {"acc_norm,none": 0.60, "samples": 100},
        "hellaswag_ua": {"acc_norm,none": 0.65, "samples": 100},
        "gsm8k_ua": {"exact_match,none": 0.50, "samples": 100},
    }
    result = evaluate_academic_non_inferiority(base_scores, aligned_scores)
    assert result.overall_passed is False
    task_map = {t.benchmark: t for t in result.tasks}
    assert task_map["mmlu_ua"].passed is False
    assert "No matching score metric found" in (task_map["mmlu_ua"].details.get("error") or "")


def test_evaluate_prediction_r11_f2_replace_directive_not_masked_by_error_negation() -> None:
    """Verify negating error does not mask explicit replacement instruction (R11-F2)."""
    case = {
        "target_term": "матеріал",
        "case_type": "PRESERVE",
        "input_text": "Матеріал підручника викладено послідовно.",
        "expected_replacement": None,
    }
    pred = (
        "<thought>Замініть «матеріал» — це слово не є помилкою.</thought>"
        "Матеріал підручника викладено послідовно."
    )
    res = evaluate_prediction(case, pred)
    assert res.harmful_edit is True
    assert "Harmful over-correction detected" in res.details


def test_citation_whitelist_r11_f3_fabricated_suffix_on_adjective_authority_rejected() -> None:
    """Verify fabricated suffixes attached to adjective authority prefix are rejected (R11-F3)."""
    text = "Згідно з “академічнZorblax СУМ”, це правильно."
    is_clean, _app, viol = verify_citation_whitelist(text)
    assert is_clean is False
    assert any("академічнZorblax СУМ" in v for v in viol)


def test_citation_whitelist_r11_f4_two_authority_extraction_across_supported_prefixes() -> None:
    """Verify coordinate authority extraction across Відповідно до and За даними (R11-F4)."""
    text1 = "Відповідно до ВЕСУМ, Зорблакса, це правильно."
    is_clean1, app1, viol1 = verify_citation_whitelist(text1)
    assert is_clean1 is False
    assert any("Зорблакса" in v for v in viol1)
    assert any("ВЕСУМ" in a for a in app1)

    text2 = "За даними ВЕСУМ, Зорблакса, це правильно."
    is_clean2, app2, viol2 = verify_citation_whitelist(text2)
    assert is_clean2 is False
    assert any("Зорблакса" in v for v in viol2)
    assert any("ВЕСУМ" in a for a in app2)


def test_evaluate_academic_non_inferiority_r12_f1_normalization_key_rejected() -> None:
    """Verify metadata keys like 'normalization' are rejected as score metrics (R12-F1)."""
    base_scores = {
        "mmlu_ua": {"acc_norm,none": 0.70, "normalization": 1},
        "arc_ua": {"acc_norm,none": 0.60, "normalization": 1},
        "hellaswag_ua": {"acc_norm,none": 0.65, "normalization": 1},
        "gsm8k_ua": {"exact_match,none": 0.50, "normalization": 1},
    }
    aligned_scores = {
        "mmlu_ua": {"acc,none": 0.10, "normalization": 1},
        "arc_ua": {"acc_norm,none": 0.60, "normalization": 1},
        "hellaswag_ua": {"acc_norm,none": 0.65, "normalization": 1},
        "gsm8k_ua": {"exact_match,none": 0.50, "normalization": 1},
    }
    result = evaluate_academic_non_inferiority(base_scores, aligned_scores)
    assert result.overall_passed is False
    task_map = {t.benchmark: t for t in result.tasks}
    assert task_map["mmlu_ua"].passed is False
    assert "No matching score metric found" in (task_map["mmlu_ua"].details.get("error") or "")


def test_evaluate_prediction_r12_f2_replacement_negation_scoped_to_target() -> None:
    """Verify replacement negation is strictly scoped to the target term (R12-F2)."""
    case = {
        "target_term": "матеріал",
        "case_type": "PRESERVE",
        "input_text": "Матеріал підручника викладено послідовно.",
        "expected_replacement": None,
    }
    # 1. Thought replaces target, but negates replacement for unrelated word: must be harmful edit
    pred1 = (
        "<thought>Замініть «матеріал» — інше слово не потребує заміни.</thought>"
        "Матеріал підручника викладено послідовно."
    )
    res1 = evaluate_prediction(case, pred1)
    assert res1.harmful_edit is True
    assert "Harmful over-correction detected" in res1.details

    # 2. Thought negates replacement of target: must NOT be harmful edit
    pred2 = (
        "<thought>Не слід замінити «матеріал».</thought>"
        "Матеріал підручника викладено послідовно."
    )
    res2 = evaluate_prediction(case, pred2)
    assert res2.harmful_edit is False

    # 3. Thought negates replacement with imperfective verb: must NOT be harmful edit
    pred3 = (
        "<thought>Не слід замінювати «матеріал».</thought>"
        "Матеріал підручника викладено послідовно."
    )
    res3 = evaluate_prediction(case, pred3)
    assert res3.harmful_edit is False


def test_citation_whitelist_r12_f3_sentence_subject_not_mistaken_for_authority() -> None:
    """Verify sentence subject followed by comma is not captured as unapproved authority (R12-F3)."""
    text1 = "Згідно з ВЕСУМ, Школа, описана вище, є правильною."
    is_clean1, app1, viol1 = verify_citation_whitelist(text1)
    assert is_clean1 is True
    assert "ВЕСУМ" in app1
    assert "Школа" not in viol1
    assert len(viol1) == 0

    text2 = "Згідно з ВЕСУМ, Зорблаксом, це правильно."
    is_clean2, _app2, viol2 = verify_citation_whitelist(text2)
    assert is_clean2 is False
    assert any("Зорблаксом" in v for v in viol2)


def test_citation_whitelist_r12_f4_approved_identities_grinchenko_shevchenko_franko() -> None:
    """Verify nominative forms of Grinchenko, Shevchenko, and Franko are approved (R12-F4)."""
    for name in ("Грінченко", "Шевченко", "Франко"):
        text = f"Згідно з “{name}”, це правильно."
        is_clean, app, viol = verify_citation_whitelist(text)
        assert is_clean is True, f"Failed for {name}: {viol}"
        assert any(name in a for a in app)
        assert len(viol) == 0


def test_evaluate_prediction_r13_f1_token_boundary_and_unquoted_directive() -> None:
    """Verify left token boundary on target and unquoted replacement directives (R13-F1)."""
    case = {
        "target_term": "матеріал",
        "case_type": "PRESERVE",
        "input_text": "Матеріал підручника викладено послідовно.",
        "expected_replacement": None,
    }
    # 1. Target replaced, negation is for distinct token Xматеріал: harmful edit
    pred1 = (
        "<thought>Замініть «матеріал» — «Xматеріал» не потребує заміни.</thought>"
        "Матеріал підручника викладено послідовно."
    )
    res1 = evaluate_prediction(case, pred1)
    assert res1.harmful_edit is True

    # 2. Xматеріал requires replacement, target preserved: NOT harmful edit
    pred2 = (
        "<thought>«Xматеріал» потребує заміни — збережіть «матеріал».</thought>"
        "Матеріал підручника викладено послідовно."
    )
    res2 = evaluate_prediction(case, pred2)
    assert res2.harmful_edit is False

    # 3. Unquoted target in replacement directive: harmful edit
    pred3 = (
        "<thought>Виправте матеріал.</thought>"
        "Матеріал підручника викладено послідовно."
    )
    res3 = evaluate_prediction(case, pred3)
    assert res3.harmful_edit is True


def test_citation_whitelist_r13_f2_compound_subject_not_mistaken_for_authorities() -> None:
    """Verify compound sentence subject with conjunction is not treated as unapproved authority (R13-F2)."""
    text = "Згідно з ВЕСУМ, Школа та Університет, описані вище, є правильними."
    is_clean, app, viol = verify_citation_whitelist(text)
    assert is_clean is True
    assert "ВЕСУМ" in app
    assert len(viol) == 0


def test_citation_whitelist_r13_f3_genitive_co_citation_zorblaka_detected() -> None:
    """Verify genitive co-citations like Зорблака are detected across Відповідно до and За даними (R13-F3)."""
    text1 = "За даними ВЕСУМ, Зорблака, це правильно."
    is_clean1, app1, viol1 = verify_citation_whitelist(text1)
    assert is_clean1 is False
    assert any("Зорблака" in v for v in viol1)
    assert any("ВЕСУМ" in a for a in app1)

    text2 = "Відповідно до ВЕСУМ, Зорблака, це правильно."
    is_clean2, app2, viol2 = verify_citation_whitelist(text2)
    assert is_clean2 is False
    assert any("Зорблака" in v for v in viol2)
    assert any("ВЕСУМ" in a for a in app2)


def test_citation_whitelist_r14_f1_attribution_boundary_disambiguation() -> None:
    """Verify sentence subject followed by participle clause is not mistaken for co-citation (R14-F1)."""
    # 1. 'За даними' with sentence subject 'Школа' followed by participle clause
    text1 = "За даними ВЕСУМ, Школа, описана вище, є правильною."
    is_clean1, app1, viol1 = verify_citation_whitelist(text1)
    assert is_clean1 is True
    assert app1 == ["ВЕСУМ"]
    assert viol1 == []

    # 2. 'Відповідно до' with sentence subject 'Школа' followed by participle clause
    text2 = "Відповідно до ВЕСУМ, Школа, описана вище, є правильною."
    is_clean2, app2, viol2 = verify_citation_whitelist(text2)
    assert is_clean2 is True
    assert app2 == ["ВЕСУМ"]
    assert viol2 == []

    # 3. 'Згідно з' with sentence subject 'Школа' followed by participle clause
    text3 = "Згідно з ВЕСУМ, Школа, описана вище, є правильною."
    is_clean3, app3, viol3 = verify_citation_whitelist(text3)
    assert is_clean3 is True
    assert app3 == ["ВЕСУМ"]
    assert viol3 == []

    # 4. 'Відповідно до' and 'За даними' with co-citation 'Зорблакса'
    text4 = "Відповідно до ВЕСУМ, Зорблакса, це правильно."
    is_clean4, app4, viol4 = verify_citation_whitelist(text4)
    assert is_clean4 is False
    assert any("Зорблакса" in v for v in viol4)
    assert any("ВЕСУМ" in a for a in app4)

    text5 = "За даними ВЕСУМ, Зорблакса, це правильно."
    is_clean5, app5, viol5 = verify_citation_whitelist(text5)
    assert is_clean5 is False
    assert any("Зорблакса" in v for v in viol5)
    assert any("ВЕСУМ" in a for a in app5)

    # 5. Quoted subject followed by participle clause (R15-F1 non-backtracking)
    text6 = "За даними ВЕСУМ, «Школа», описана вище, є правильною."
    is_clean6, app6, viol6 = verify_citation_whitelist(text6)
    assert is_clean6 is True
    assert app6 == ["ВЕСУМ"]
    assert viol6 == []

    text7 = "Відповідно до ВЕСУМ, «Школа», описана вище, є правильною."
    is_clean7, app7, viol7 = verify_citation_whitelist(text7)
    assert is_clean7 is True
    assert app7 == ["ВЕСУМ"]
    assert viol7 == []

    text8 = "Згідно з ВЕСУМ, «Школа», описана вище, є правильною."
    is_clean8, app8, viol8 = verify_citation_whitelist(text8)
    assert is_clean8 is True
    assert app8 == ["ВЕСУМ"]
    assert viol8 == []


def test_citation_whitelist_r16_f1_compound_quoted_subject_disambiguation() -> None:
    """Verify compound quoted subjects followed by participle clause are not captured as authorities (R16-F1)."""
    # 1. Quoted compound subjects with conjunction followed by participle clause
    text1 = "Згідно з ВЕСУМ, «Школа» та «Університет», описані вище, є правильними."
    is_clean1, app1, viol1 = verify_citation_whitelist(text1)
    assert is_clean1 is True
    assert app1 == ["ВЕСУМ"]
    assert viol1 == []

    text2 = "За даними ВЕСУМ, «Школа» та «Університет», описані вище, є правильними."
    is_clean2, app2, viol2 = verify_citation_whitelist(text2)
    assert is_clean2 is True
    assert app2 == ["ВЕСУМ"]
    assert viol2 == []

    text3 = "Відповідно до ВЕСУМ, «Школа» та «Університет», описані вище, є правильними."
    is_clean3, app3, viol3 = verify_citation_whitelist(text3)
    assert is_clean3 is True
    assert app3 == ["ВЕСУМ"]
    assert viol3 == []

    # 2. Quoted compound subjects with commas and conjunction followed by participle clause
    text4 = "Згідно з ВЕСУМ, «Школа», «Коледж» та «Університет», описані вище, є правильними."
    is_clean4, app4, viol4 = verify_citation_whitelist(text4)
    assert is_clean4 is True
    assert app4 == ["ВЕСУМ"]
    assert viol4 == []

    # 3. Genuine co-citations without participle clauses are caught
    text5 = "Згідно з ВЕСУМ, «Зорблакс» та «Фальшсловник», це правильно."
    is_clean5, app5, viol5 = verify_citation_whitelist(text5)
    assert is_clean5 is False
    assert any("Зорблакс" in v for v in viol5)
    assert any("Фальшсловник" in v for v in viol5)
    assert any("ВЕСУМ" in a for a in app5)

    text6 = "За даними ВЕСУМ, Зорблака та «Фальшсловник», це правильно."
    is_clean6, app6, viol6 = verify_citation_whitelist(text6)
    assert is_clean6 is False
    assert any("Зорблака" in v for v in viol6)
    assert any("Фальшсловник" in v for v in viol6)
    assert any("ВЕСУМ" in a for a in app6)

    # 4. Approved multi-authority co-citations remain approved
    text7 = "Згідно з ВЕСУМ, УЛІФ та Грінченком, це правильно."
    is_clean7, app7, viol7 = verify_citation_whitelist(text7)
    assert is_clean7 is True
    assert "ВЕСУМ" in app7
    assert "УЛІФ" in app7
    assert any("Грінченк" in a for a in app7)
    assert viol7 == []


def test_citation_whitelist_r17_findings_sentence_subject_and_repeated_conjunctions() -> None:
    """Verify sentence subject without comma and repeated conjunctions with participle guard (R17)."""
    # 1. Finding 1: Sentence subject after introductory comma without closing comma
    text1 = "Згідно з ВЕСУМ, «Школа» є правильною."
    is_clean1, app1, viol1 = verify_citation_whitelist(text1)
    assert is_clean1 is True
    assert app1 == ["ВЕСУМ"]
    assert viol1 == []

    text2 = "За даними ВЕСУМ, «Школа» є правильною."
    is_clean2, app2, viol2 = verify_citation_whitelist(text2)
    assert is_clean2 is True
    assert app2 == ["ВЕСУМ"]
    assert viol2 == []

    text3 = "Відповідно до ВЕСУМ, «Школа» є правильною."
    is_clean3, app3, viol3 = verify_citation_whitelist(text3)
    assert is_clean3 is True
    assert app3 == ["ВЕСУМ"]
    assert viol3 == []

    # 2. Finding 2: Repeated conjunctions followed by participle clause
    text4 = "Згідно з ВЕСУМ, «Школа» та «Коледж» та «Університет», описані вище, є правильними."
    is_clean4, app4, viol4 = verify_citation_whitelist(text4)
    assert is_clean4 is True
    assert app4 == ["ВЕСУМ"]
    assert viol4 == []

    text5 = "За даними ВЕСУМ, «Школа» та «Коледж» та «Університет», описані вище, є правильними."
    is_clean5, app5, viol5 = verify_citation_whitelist(text5)
    assert is_clean5 is True
    assert app5 == ["ВЕСУМ"]
    assert viol5 == []

    text6 = "Відповідно до ВЕСУМ, «Школа» та «Коледж» та «Університет», описані вище, є правильними."
    is_clean6, app6, viol6 = verify_citation_whitelist(text6)
    assert is_clean6 is True
    assert app6 == ["ВЕСУМ"]
    assert viol6 == []


def test_citation_whitelist_r18_findings_and_academic_metrics() -> None:
    """Verify Round 18 findings: unapproved authorities, parenthetical subjects, float precision, perplexity."""
    # 1. Finding 1: Coordinate unapproved authority followed by quoted subject
    text1 = "Згідно з ВЕСУМ, Zorblax, «Школа» є правильною."
    is_clean1, app1, viol1 = verify_citation_whitelist(text1)
    assert is_clean1 is False
    assert app1 == ["ВЕСУМ"]
    assert viol1 == ["Zorblax"]

    text2 = "За даними ВЕСУМ, Zorblax, «Школа» є правильною."
    is_clean2, app2, viol2 = verify_citation_whitelist(text2)
    assert is_clean2 is False
    assert app2 == ["ВЕСУМ"]
    assert viol2 == ["Zorblax"]

    text3 = "Відповідно до ВЕСУМ, Zorblax, «Школа» є правильною."
    is_clean3, app3, viol3 = verify_citation_whitelist(text3)
    assert is_clean3 is False
    assert app3 == ["ВЕСУМ"]
    assert viol3 == ["Zorblax"]

    # 2. Finding 2: Parenthetical clause modifying subject does not turn subject into authority
    text4 = "Згідно з ВЕСУМ, «Школа», як зазначено вище, є правильною."
    is_clean4, app4, viol4 = verify_citation_whitelist(text4)
    assert is_clean4 is True
    assert app4 == ["ВЕСУМ"]
    assert viol4 == []

    text5 = "За даними ВЕСУМ, «Школа», як зазначено вище, є правильною."
    is_clean5, app5, viol5 = verify_citation_whitelist(text5)
    assert is_clean5 is True
    assert app5 == ["ВЕСУМ"]
    assert viol5 == []

    text6 = "Відповідно до ВЕСУМ, «Школа», як зазначено вище, є правильною."
    is_clean6, app6, viol6 = verify_citation_whitelist(text6)
    assert is_clean6 is True
    assert app6 == ["ВЕСУМ"]
    assert viol6 == []

    # 3. Finding 3: Numerically stable 2% degradation float precision
    base_eval = {
        "mmlu_ua": {"acc_norm": 0.5},
        "arc_ua": {"acc_norm": 0.5},
        "hellaswag_ua": {"acc_norm": 0.5},
        "gsm8k_ua": {"exact_match": 0.5},
    }
    aligned_eval = {
        "mmlu_ua": {"acc_norm": 0.49},
        "arc_ua": {"acc_norm": 0.49},
        "hellaswag_ua": {"acc_norm": 0.49},
        "gsm8k_ua": {"exact_match": 0.49},
    }
    rep = evaluate_academic_non_inferiority(base_eval, aligned_eval)
    assert rep.overall_passed is True
    for t in rep.tasks:
        assert t.passed is True

    # 4. Finding 4: Perplexity is lower-is-better; worsening fails non-inferiority
    base_ppl = {
        "mmlu_ua": {"perplexity": 10.0},
        "arc_ua": {"perplexity": 10.0},
        "hellaswag_ua": {"perplexity": 10.0},
        "gsm8k_ua": {"perplexity": 10.0},
    }
    aligned_ppl_worse = {
        "mmlu_ua": {"perplexity": 20.0},
        "arc_ua": {"perplexity": 20.0},
        "hellaswag_ua": {"perplexity": 20.0},
        "gsm8k_ua": {"perplexity": 20.0},
    }
    rep_ppl_worse = evaluate_academic_non_inferiority(base_ppl, aligned_ppl_worse)
    assert rep_ppl_worse.overall_passed is False
    for t in rep_ppl_worse.tasks:
        assert t.passed is False
        assert t.degradation_pct == 100.0

    aligned_ppl_better = {
        "mmlu_ua": {"perplexity": 5.0},
        "arc_ua": {"perplexity": 5.0},
        "hellaswag_ua": {"perplexity": 5.0},
        "gsm8k_ua": {"perplexity": 5.0},
    }
    rep_ppl_better = evaluate_academic_non_inferiority(base_ppl, aligned_ppl_better)
    assert rep_ppl_better.overall_passed is True
    for t in rep_ppl_better.tasks:
        assert t.passed is True
        assert t.degradation_pct == 0.0


def test_citation_whitelist_r19_findings_and_metrics():
    # R19-F1: словник «Абетка» and За даними ВЕСУМ та «Абетка», це правильно.
    text1 = "словник «Абетка» є чудовим ресурсом."
    is_clean1, _app1, viol1 = verify_citation_whitelist(text1)
    assert is_clean1 is False
    assert any("Абетка" in v for v in viol1)

    text2 = "За даними ВЕСУМ та «Абетка», це правильно."
    is_clean2, app2, viol2 = verify_citation_whitelist(text2)
    assert is_clean2 is False
    assert "ВЕСУМ" in app2
    assert any("Абетка" in v for v in viol2)

    # R19-F2: Згідно з ВЕСУМ, Zorblax, «Мова» є правильною.
    text3 = "Згідно з ВЕСУМ, Zorblax, «Мова» є правильною."
    is_clean3, app3, viol3 = verify_citation_whitelist(text3)
    assert is_clean3 is False
    assert "ВЕСУМ" in app3
    assert any("Zorblax" in v for v in viol3)
    assert not any("Мова" in v for v in viol3)

    # R19-F3: Згідно з ВЕСУМ, «Мова», як зазначено вище, є правильною.
    text4 = "Згідно з ВЕСУМ, «Мова», як зазначено вище, є правильною."
    is_clean4, app4, viol4 = verify_citation_whitelist(text4)
    assert is_clean4 is True
    assert app4 == ["ВЕСУМ"]
    assert viol4 == []

    # R19-F4: loss metric support in extract_benchmark_score and academic non-inferiority
    score, metric = extract_benchmark_score({"loss": 2.5})
    assert score == 2.5
    assert metric == "loss"

    base_loss = {
        "mmlu_ua": {"loss": 5.0},
        "arc_ua": {"loss": 5.0},
        "hellaswag_ua": {"loss": 5.0},
        "gsm8k_ua": {"loss": 5.0},
    }
    aligned_loss_better = {
        "mmlu_ua": {"loss": 2.5},
        "arc_ua": {"loss": 2.5},
        "hellaswag_ua": {"loss": 2.5},
        "gsm8k_ua": {"loss": 2.5},
    }
    rep_loss = evaluate_academic_non_inferiority(base_loss, aligned_loss_better)
    assert rep_loss.overall_passed is True
    for t in rep_loss.tasks:
        assert t.passed is True
        assert t.degradation_pct == 0.0

    aligned_loss_worse = {
        "mmlu_ua": {"loss": 10.0},
        "arc_ua": {"loss": 10.0},
        "hellaswag_ua": {"loss": 10.0},
        "gsm8k_ua": {"loss": 10.0},
    }
    rep_loss_worse = evaluate_academic_non_inferiority(base_loss, aligned_loss_worse)
    assert rep_loss_worse.overall_passed is False
    for t in rep_loss_worse.tasks:
        assert t.passed is False
        assert t.degradation_pct == 100.0

    # R19-F5: acc,ppl_filter metric direction (higher is better, falling score fails)
    base_filter = {
        "mmlu_ua": {"acc,ppl_filter": 0.8},
        "arc_ua": {"acc,ppl_filter": 0.8},
        "hellaswag_ua": {"acc,ppl_filter": 0.8},
        "gsm8k_ua": {"acc,ppl_filter": 0.8},
    }
    aligned_filter_worse = {
        "mmlu_ua": {"acc,ppl_filter": 0.4},
        "arc_ua": {"acc,ppl_filter": 0.4},
        "hellaswag_ua": {"acc,ppl_filter": 0.4},
        "gsm8k_ua": {"acc,ppl_filter": 0.4},
    }
    rep_filter_worse = evaluate_academic_non_inferiority(base_filter, aligned_filter_worse)
    assert rep_filter_worse.overall_passed is False
    for t in rep_filter_worse.tasks:
        assert t.passed is False
        assert t.degradation_pct == 50.0


def test_citation_whitelist_r20_findings():
    # R20-F1: Unapproved coordinate still dropped in compound subject context
    t1 = "Згідно з ВЕСУМ, Zorblax, «Мова» та «Абетка» є правильними."
    ok1, app1, viol1 = verify_citation_whitelist(t1)
    assert ok1 is False
    assert "Zorblax" in viol1
    assert "ВЕСУМ" in app1
    assert "Мова" not in viol1
    assert "Абетка" not in viol1

    t1b = "За даними ВЕСУМ, Zorblax, «Мова» та «Абетка» є правильними."
    ok1b, app1b, viol1b = verify_citation_whitelist(t1b)
    assert ok1b is False
    assert "Zorblax" in viol1b
    assert "ВЕСУМ" in app1b

    t1c = "Відповідно до ВЕСУМ, Zorblax, «Мова» та «Абетка» є правильними."
    ok1c, app1c, viol1c = verify_citation_whitelist(t1c)
    assert ok1c is False
    assert "Zorblax" in viol1c
    assert "ВЕСУМ" in app1c

    # R20-F2: Negated and adverbially modified predicates («не є», «також є»)
    t2 = "Згідно з ВЕСУМ, «Мова», як зазначено вище, не є правильною."
    ok2, app2, viol2 = verify_citation_whitelist(t2)
    assert ok2 is True
    assert app2 == ["ВЕСУМ"]
    assert viol2 == []

    t2b = "За даними ВЕСУМ, «Мова», як зазначено вище, також є правильною."
    ok2b, app2b, viol2b = verify_citation_whitelist(t2b)
    assert ok2b is True
    assert app2b == ["ВЕСУМ"]
    assert viol2b == []


def test_citation_whitelist_r21_findings():
    # R21-F1: Combined modifiers («також не є») before predicate verbs
    t1 = "Згідно з ВЕСУМ, «Мова», як зазначено вище, також не є правильною."
    ok1, app1, viol1 = verify_citation_whitelist(t1)
    assert ok1 is True
    assert app1 == ["ВЕСУМ"]
    assert viol1 == []

    t2 = "За даними ВЕСУМ, «Мова», як зазначено вище, також не є правильною."
    ok2, app2, viol2 = verify_citation_whitelist(t2)
    assert ok2 is True
    assert app2 == ["ВЕСУМ"]
    assert viol2 == []

    t3 = "Відповідно до ВЕСУМ, «Мова», як зазначено вище, також не є правильною."
    ok3, app3, viol3 = verify_citation_whitelist(t3)
    assert ok3 is True
    assert app3 == ["ВЕСУМ"]
    assert viol3 == []


def test_citation_whitelist_r22_findings_sum11_quarantine_and_unambiguous_sum20():
    """Verify permanent quarantine of Bilodid's СУМ-11 and unambiguous 20-volume СУМ requirement (Astra Finding 3)."""
    # 1. Bilodid's Russian-Soviet occupation СУМ-11 positive citations must be rejected
    ok1, _, viol1 = verify_citation_whitelist("За СУМ-11, це правильно.")
    assert ok1 is False
    assert "СУМ-11" in viol1

    ok2, _, viol2 = verify_citation_whitelist("Це правильно (СУМ-11).")
    assert ok2 is False
    assert "СУМ-11" in viol2

    ok3, _, _ = verify_citation_whitelist("Згідно зі Словником української мови в 11 томах, це правильно.")
    assert ok3 is False

    ok4, _, _ = verify_citation_whitelist("За Білодідом, це правильно.")
    assert ok4 is False

    # 2. Ambiguous bare 'Словник української мови' or 'СУМ' without 20 volumes must be rejected
    assert is_approved_authority("Словник української мови") is False
    assert is_approved_authority("академічний словник української мови") is False
    assert is_approved_authority("СУМ") is False
    assert is_approved_authority("СУМ-11") is False

    ok5, _, _ = verify_citation_whitelist("За Словником української мови, це правильно.")
    assert ok5 is False

    # 3. Unambiguous modern decolonized СУМ-20 and VESUM must be approved
    assert is_approved_authority("СУМ-20") is True
    assert is_approved_authority("Словник української мови в 20 томах") is True
    assert is_approved_authority("академічний Словник української мови в 20 томах") is True
    assert is_approved_authority("ВЕСУМ") is True

    ok6, app6, viol6 = verify_citation_whitelist("За СУМ-20, це правильно.")
    assert ok6 is True
    assert "СУМ-20" in app6
    assert viol6 == []

    ok7, app7, viol7 = verify_citation_whitelist("Це правильно (ВЕСУМ).")
    assert ok7 is True
    assert "ВЕСУМ" in app7
    assert viol7 == []

    ok8, app8, viol8 = verify_citation_whitelist("За Словником української мови в 20 томах, це правильно.")
    assert ok8 is True
    assert any("20 томах" in a for a in app8)
    assert viol8 == []


def test_citation_whitelist_r23_astra_r2_probes():
    """Verify Astra R2 probes for ambiguous dictionary titles and ordinary prose phrases."""
    # Finding 3: Ambiguous dictionary titles must NOT bypass СУМ-20 requirement
    assert is_approved_authority("Словник української мови том 11") is False
    assert is_approved_authority("Словник української мови 2020") is False

    ok1, _, viol1 = verify_citation_whitelist("Це правильно (Словник української мови том 11).")
    assert ok1 is False
    assert any("української мови том 11" in v for v in viol1)

    ok2, _, viol2 = verify_citation_whitelist("Це правильно (Словник української мови 2020).")
    assert ok2 is False
    assert any("української мови 2020" in v for v in viol2)

    # Finding 4: Ordinary prose introductory phrases must not fail Gate 4
    ok3, app3, viol3 = verify_citation_whitelist("За потреби, збережіть слово.")
    assert ok3 is True
    assert app3 == []
    assert viol3 == []

    ok4, app4, viol4 = verify_citation_whitelist("За бажанням, збережіть слово.")
    assert ok4 is True
    assert app4 == []
    assert viol4 == []

    ok5, app5, viol5 = verify_citation_whitelist("За наявності, збережіть слово.")
    assert ok5 is True
    assert app5 == []
    assert viol5 == []

    ok6, app6, viol6 = verify_citation_whitelist("За замовчуванням, збережіть слово.")
    assert ok6 is True
    assert app6 == []
    assert viol6 == []
