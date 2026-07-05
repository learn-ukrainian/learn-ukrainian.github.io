from __future__ import annotations

from scripts.audit import llm_reviewer, qg_schema

# Ground truth bad content text for B1-27
B1_27_BAD_TEXT = """# Вид у наказовому способі

Тут застосунок має бути відкритий. Застереження каже: будь обережний.
Він радить не робити певної поведінки.
Подумай: дія має дати конкретний результат чи описати процес?
Крім того, доконаний вид дає результат із вікном. У кухні стоїть стіл.
"""

B1_27_GOOD_TEXT = """# Вид у наказовому способі

Відкрийте застосунок, щоб виконати завдання. Будьте обережні.
Зверніть увагу на правила вживання доконаного виду.
Подумайте, який результат ви очікуєте отримати.
На кухні стоїть стіл.
"""

B1_27_BAD_LLM_RESPONSE = """{
  "findings": [
    {
      "issue_id": "AWKWARD_PASSIVE_RESULT_STATE",
      "issue_class": "calque",
      "dimension": "ukrainian_style",
      "severity": "critical",
      "excerpt": "застосунок має бути відкритий",
      "message": "Use an active or impersonal Ukrainian instruction instead of a literal passive state."
    },
    {
      "issue_id": "UNNATURAL_ANTHROPOMORPHISM",
      "issue_class": "other",
      "dimension": "ukrainian_style",
      "severity": "warning",
      "excerpt": "Застереження каже: будь обережний",
      "message": "Abstract lesson metalanguage should not be anthropomorphized as a speaker."
    },
    {
      "issue_id": "UKRAINIAN_GRAMMAR_CALQUE",
      "issue_class": "grammar",
      "dimension": "ukrainian_style",
      "severity": "warning",
      "excerpt": "радить не робити певної поведінки",
      "message": "The government and nominalized behavior phrase are translated and unnatural."
    },
    {
      "issue_id": "UNNATURAL_META_REGISTER",
      "issue_class": "register",
      "dimension": "ukrainian_style",
      "severity": "warning",
      "excerpt": "дія має дати конкретний результат чи описати процес?",
      "message": "This abstract prompt-like sentence is not natural learner-facing Ukrainian."
    },
    {
      "issue_id": "UKRAINIAN_GRAMMAR_CALQUE",
      "issue_class": "grammar",
      "dimension": "ukrainian_style",
      "severity": "warning",
      "excerpt": "доконаний вид дає результат із вікном",
      "message": "The metaphor and argument structure are literal and unidiomatic."
    },
    {
      "issue_id": "CALQUED_PREPOSITION",
      "issue_class": "calque",
      "dimension": "ukrainian_style",
      "severity": "warning",
      "excerpt": "У кухні",
      "message": "In this ordinary locative teaching context, use the idiomatic На кухні."
    }
  ]
}"""


def test_reviewer_prompt_loads_and_assembles() -> None:
    template = llm_reviewer.load_reviewer_prompt_template()
    assert "LLM Reviewer & Evaluator Prompt" in template
    assert "A1/A2" in template
    assert "B1+" in template
    assert "Seminar Register" in template

    prompt = llm_reviewer.build_reviewer_prompt(
        level="b1",
        slug="aspect-in-imperatives",
        module_md=B1_27_BAD_TEXT,
    )
    assert "aspect-in-imperatives" in prompt
    assert "застосунок має бути відкритий" in prompt


def test_structural_checks_for_model_answers() -> None:
    # B2 productive task missing model answer -> FAIL
    bad_activities = """
- id: wb-essay-missing
  type: essay-response
  title: Напишіть есе
  instruction: Напишіть 120-160 слів.
  prompt: "Поясніть роль..."
"""
    findings = llm_reviewer.run_structural_checks("b2", bad_activities)
    assert len(findings) == 1
    assert findings[0]["issue_id"] == "MISSING_MODEL_ANSWER"
    assert findings[0]["dimension"] == "pedagogical"
    assert findings[0]["severity"] == "critical"
    assert findings[0]["file"] == "activities.yaml"
    assert findings[0]["line"] == 2
    qg_schema.validate_finding(findings[0])

    # B2 productive task with correct model answer -> PASS
    good_activities = """
- id: wb-essay-good
  type: essay-response
  title: Напишіть есе
  instruction: Напишіть 120-160 слів.
  prompt: "Поясніть роль..."
  model_answer: |
    > [!model-answer]
    > Це правильна модельна відповідь.
"""
    findings_good = llm_reviewer.run_structural_checks("b2", good_activities)
    assert len(findings_good) == 0

    # Low level (A1) task missing model answer -> PASS (no structural check for model answer in A1/A2/B1)
    findings_a1 = llm_reviewer.run_structural_checks("a1", bad_activities)
    assert len(findings_a1) == 0


def test_b1_27_bad_calibration_produces_expected_findings() -> None:
    findings = llm_reviewer.parse_and_evaluate_llm_response(
        B1_27_BAD_LLM_RESPONSE,
        module_md=B1_27_BAD_TEXT,
    )

    # 6 expected style/grammar defects
    assert len(findings) == 6

    # Ensure they are valid schema findings
    for finding in findings:
        qg_schema.validate_finding(finding)

    by_issue = {f["issue_id"] for f in findings}
    assert {
        "AWKWARD_PASSIVE_RESULT_STATE",
        "UNNATURAL_ANTHROPOMORPHISM",
        "UKRAINIAN_GRAMMAR_CALQUE",
        "UNNATURAL_META_REGISTER",
        "CALQUED_PREPOSITION",
    } <= by_issue

    # Verify excerpt line mapping
    passive_finding = next(f for f in findings if f["issue_id"] == "AWKWARD_PASSIVE_RESULT_STATE")
    assert passive_finding["line"] == 3
    assert passive_finding["file"] == "module.md"
    assert passive_finding["span"]["start"] is not None


def test_b1_27_good_calibration_passes() -> None:
    # Good text returned from LLM with zero findings
    findings = llm_reviewer.parse_and_evaluate_llm_response(
        '{"findings": []}',
        module_md=B1_27_GOOD_TEXT,
    )
    assert len(findings) == 0


def test_seminar_vital_status_and_pathos_calibration() -> None:
    # Living subject biography with "Legacy" or "Last Years" header -> FAIL
    living_subject_bad = """---
level: bio
slug: oleksandra-matviichuk
---

# Олександра Матвійчук

Олександра Матвійчук — відома українська правозахисниця.

## Останні роки
Вона продовжує очолювати Центр громадянських свобод.
"""
    living_subject_bad_llm_response = """{
      "findings": [
        {
          "issue_id": "SEMINAR_OBITUARY_STYLE",
          "issue_class": "register",
          "dimension": "seminar_sensitivity",
          "severity": "critical",
          "excerpt": "## Останні роки",
          "message": "Living biography subjects must not use obituary-style headers like 'Last Years'."
        }
      ]
    }"""

    findings = llm_reviewer.parse_and_evaluate_llm_response(
        living_subject_bad_llm_response,
        module_md=living_subject_bad,
    )
    assert len(findings) == 1
    assert findings[0]["issue_id"] == "SEMINAR_OBITUARY_STYLE"
    assert findings[0]["dimension"] == "seminar_sensitivity"
    assert findings[0]["severity"] == "critical"
    qg_schema.validate_finding(findings[0])


def test_llm_response_parse_failure_emits_valid_finding() -> None:
    # Malformed LLM response
    findings = llm_reviewer.parse_and_evaluate_llm_response(
        "This is not JSON",
        module_md=B1_27_BAD_TEXT,
    )
    assert len(findings) == 1
    assert findings[0]["issue_id"] == "LLM_RESPONSE_PARSE_FAILURE"
    assert findings[0]["dimension"] == "mechanics"
    assert findings[0]["severity"] == "critical"
    qg_schema.validate_finding(findings[0])
