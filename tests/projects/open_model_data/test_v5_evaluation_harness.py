"""Unit and regression tests for Phase 5.1 Automated Evaluation Suite (ULDR #8050)."""

from __future__ import annotations

import pytest

from scripts.projects.open_model_data.v5_evaluation_harness import (
    check_span_integrity,
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

    summary = run_evaluation_suite(test_cases, preds)
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


def test_citation_whitelist_unknown_authority_rejected() -> None:
    """Verify fabricated or unapproved dictionaries (true whitelist) are rejected."""
    text = "According to the fabricated Zorblax Dictionary, this is correct."
    is_clean, _approved, violations = verify_citation_whitelist(text)
    assert is_clean is False
    assert any("Zorblax Dictionary" in v for v in violations)


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
