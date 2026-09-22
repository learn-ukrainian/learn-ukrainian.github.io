"""Tests for fresh build engine Part E2 prompt rendering and rendered-prompt checks (#8431 §8.1)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts.build.fresh.immersion import compute_immersion_payload
from scripts.build.fresh.prompt import (
    CARDS_DIR,
    SCHEMA_EXEMPLAR_BEGIN,
    SCHEMA_EXEMPLAR_END,
    check_rendered_prompt,
    render_lesson_prompt,
    render_recap_prompt,
)
from scripts.curriculum.learner_state.planned import PlannedState

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def sample_plan_entry():
    return {
        "slug": "sound-intro",
        "title": "Sounds and letters",
        "kind": "teach",
        "job": "Learner can recognize letter A.",
        "rationale": "First phonetics step.",
        "word_target": 8,
        "lesson": {"module": "a1/sounds-intro", "n": 1},
        "steps": [
            {
                "id": "s1",
                "kind": "teach",
                "teach": "Pronounce letter A.",
                "explains": ["T-001"],
                "ref": "EX-001",
                "needs": ["example"],
            },
            {
                "id": "s2",
                "kind": "teach",
                "teach": "Practice words.",
                "ref": "P-01",
                "paradigm": {"id": "P-01", "word": "W-001", "forms": ["tag-nom"]},
                "practice": ["a1"],
            },
        ],
        "consolidation": ["a1"],
        "activities": [{"id": "a1", "type": "quiz", "placement": "inline", "focus": "Identify letter"}],
        "inventory": {
            "vocabulary": {
                "core": [{"lemma": "mama", "evidence": "W-001", "forms": ["tag-nom"]}],
                "incidental": [],
                "recycled": [],
            },
            "grammar": [],
            "phonetics": {"letters": ["А"]},
        },
    }


@pytest.fixture
def sample_learner_state():
    return PlannedState(
        level="a1",
        position=1,
        lesson_n=1,
        base_ids=("W-base-1",),
        core_ids={},
        grammar_ids={},
        letters={"А": {"position": 1, "lesson": 1}},
        name_ids={},
        cumulative_core_count=0,
    )


@pytest.fixture
def sample_cited_records():
    return {
        "W-001": {
            "lemma": "mama",
            "pos": "noun",
            "forms": [{"form": "mama", "tags": "tag-nom", "stressed": "mama", "stress_source": "vesum"}],
        },
        "EX-001": {
            "example": "mama doma",
            "translation": "mom is home",
            "source": "textbook-1",
        },
        "T-001": {
            "text": "Attested rule text",
            "source": "textbook-1",
        },
    }


def test_render_lesson_prompt_clean(sample_plan_entry, sample_learner_state, sample_cited_records):
    """Rendering a prompt from clean inputs passes the rendered-prompt check."""
    imm_payload = compute_immersion_payload("a1", arc_position=1, lesson_n=1, cumulative_core_count=0)
    card_path = CARDS_DIR / "a1.md"

    rendered = render_lesson_prompt(
        plan_entry=sample_plan_entry,
        cited_records=sample_cited_records,
        learner_state=sample_learner_state,
        immersion=imm_payload,
        level="a1",
        slug="sounds-intro",
        lesson_n=1,
        style_card_path=card_path,
    )

    assert "## 1. Plan Entry" in rendered
    assert "## 2. Cited Evidence Records" in rendered
    assert "W-001" in rendered
    assert "EX-001" in rendered
    assert SCHEMA_EXEMPLAR_BEGIN in rendered
    assert SCHEMA_EXEMPLAR_END in rendered

    check_res = check_rendered_prompt(rendered, sample_plan_entry, card_path)
    assert check_res.passed is True
    assert check_res.errors == []
    assert check_res.prompt_sha256 == hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    assert len(check_res.prompt_sha256) == 64


def test_render_recap_prompt(sample_plan_entry, sample_learner_state, sample_cited_records):
    """Recap prompt variant renders built lessons and passes recap check."""
    imm_payload = compute_immersion_payload("a1", arc_position=1, lesson_n=2, cumulative_core_count=5)
    card_path = CARDS_DIR / "a1.md"
    recap_plan = dict(sample_plan_entry)
    recap_plan["lesson"] = {"module": "a1/sounds-intro", "n": 2}
    built_lessons = [{"n": 1, "title": "Lesson 1", "content": "draft_schema: 1"}]

    rendered = render_recap_prompt(
        plan_entry=recap_plan,
        built_lessons=built_lessons,
        cited_records=sample_cited_records,
        learner_state=sample_learner_state,
        immersion=imm_payload,
        level="a1",
        slug="sounds-intro",
        lesson_n=2,
        style_card_path=card_path,
    )

    assert "## 2. Built Lessons of this Module" in rendered
    assert "Built Lesson 1: Lesson 1" in rendered
    assert SCHEMA_EXEMPLAR_BEGIN in rendered
    assert SCHEMA_EXEMPLAR_END in rendered

    check_res = check_rendered_prompt(rendered, recap_plan, card_path, is_recap=True, built_lessons=built_lessons)
    assert check_res.passed is True
    assert check_res.errors == []


def test_check_fails_missing_schema_summary_marker(sample_plan_entry):
    """Finding 5: A missing delimiter marker for the schema exemplar fails the check."""
    card_path = CARDS_DIR / "a1.md"
    prompt = "Prompt without delimiter markers."
    res = check_rendered_prompt(prompt, sample_plan_entry, card_path)
    assert res.passed is False
    assert any("missing_schema_summary_marker" in e for e in res.errors)


def test_check_fails_unresolved_placeholder(sample_plan_entry):
    card_path = CARDS_DIR / "a1.md"

    # 1. Invalid double braces
    bad_prompt_1 = "Some text with {{ invalid_var }} placeholder."
    res_1 = check_rendered_prompt(bad_prompt_1, sample_plan_entry, card_path)
    assert res_1.passed is False
    assert any("unresolved_placeholder" in e for e in res_1.errors)

    # 2. Jinja statement
    bad_prompt_2 = "Some text with {% if foo %} bar {% endif %}."
    res_2 = check_rendered_prompt(bad_prompt_2, sample_plan_entry, card_path)
    assert res_2.passed is False
    assert any("unrendered Jinja" in e for e in res_2.errors)

    # 3. Explicit TODO marker
    bad_prompt_3 = "Text with <TODO> here."
    res_3 = check_rendered_prompt(bad_prompt_3, sample_plan_entry, card_path)
    assert res_3.passed is False
    assert any("TODO" in e for e in res_3.errors)

    # 4. Leaked None value
    bad_prompt_4 = "field: None"
    res_4 = check_rendered_prompt(bad_prompt_4, sample_plan_entry, card_path)
    assert res_4.passed is False
    assert any("template variable rendered as 'None'" in e for e in res_4.errors)


@pytest.mark.parametrize(
    "v1_snippet",
    [
        "curriculum/l2-uk-en/a1-v1/lesson-1.yaml",
        "curriculum/l2-uk-en/b2-v1/mod.yaml",
        "curriculum/l2-uk-en/plans/a1/sounds.yaml",
        "curriculum/l2-uk-en/plans",
        "a1-v1/lesson-1.md",
        "c1-v1/lesson-1.md",
        "-v1/intro.yaml",
        "/plans/a1/mod.yaml",
        "plans/a1/sounds-intro.yaml",
        "lesson-plans/sounds-intro-v1/plan.yaml",
    ],
)
def test_check_fails_forbidden_v1_path_patterns(sample_plan_entry, v1_snippet: str):
    """Finding 5: Test each forbidden v1 path pattern named by the reviewer and brief."""
    card_path = CARDS_DIR / "a1.md"
    bad_prompt = f"Prompt mentioning forbidden path: {v1_snippet}"
    res = check_rendered_prompt(bad_prompt, sample_plan_entry, card_path)
    assert res.passed is False
    assert any("forbidden_v1_path" in e for e in res.errors)


@pytest.mark.parametrize(
    "schema_name",
    [
        "lesson-draft-v1",
        "evidence-words-v1",
        "lesson-draft-a1-v1",
        "schemas/lesson-draft-v1.schema.json",
        "schemas/templates/lesson-draft-v1.template.json",
        "document conforming to `lesson-draft-v1`",
    ],
)
def test_check_schema_names_do_not_trigger_v1_forbidden(sample_plan_entry, schema_name: str):
    """Schema names ending in -v1 must not be flagged as forbidden v1 curriculum paths."""
    card_path = CARDS_DIR / "a1.md"
    clean_prompt = f"# Header\n\nPrompt referencing valid schema name {schema_name} and allowed W-001.\n"
    res = check_rendered_prompt(clean_prompt, sample_plan_entry, card_path)
    assert not any("forbidden_v1_path" in e for e in res.errors)


def test_check_fails_uncited_record_id_anywhere_in_prompt(
    sample_plan_entry, sample_learner_state, sample_cited_records
):
    """Finding 5: Uncited ID scan covers the WHOLE rendered prompt (outside the delimited schema exemplar)."""
    imm_payload = compute_immersion_payload("a1", arc_position=1, lesson_n=1, cumulative_core_count=0)
    card_path = CARDS_DIR / "a1.md"

    rendered = render_lesson_prompt(
        plan_entry=sample_plan_entry,
        cited_records=sample_cited_records,
        learner_state=sample_learner_state,
        immersion=imm_payload,
        level="a1",
        slug="sounds-intro",
        lesson_n=1,
        style_card_path=card_path,
    )

    # Inject uncited ID into the plan section
    tampered_plan = rendered.replace("Sounds and letters", "Sounds and letters with uncited EX-999")
    res_plan = check_rendered_prompt(tampered_plan, sample_plan_entry, card_path)
    assert res_plan.passed is False
    assert any("uncited_record_id" in e and "EX-999" in e for e in res_plan.errors)

    # Inject uncited ID into the style card section
    tampered_card = rendered + "\nExtra style card note with T-777\n"
    res_card = check_rendered_prompt(tampered_card, sample_plan_entry, card_path)
    assert res_card.passed is False
    assert any("uncited_record_id" in e and "T-777" in e for e in res_card.errors)


def test_check_fails_unauthorized_lesson_number(sample_plan_entry, sample_learner_state, sample_cited_records):
    """Finding 5: Enforce nothing from another lesson by number."""
    imm_payload = compute_immersion_payload("a1", arc_position=1, lesson_n=1, cumulative_core_count=0)
    card_path = CARDS_DIR / "a1.md"

    rendered = render_lesson_prompt(
        plan_entry=sample_plan_entry,
        cited_records=sample_cited_records,
        learner_state=sample_learner_state,
        immersion=imm_payload,
        level="a1",
        slug="sounds-intro",
        lesson_n=1,
        style_card_path=card_path,
    )

    # Inject reference to Lesson 5 into lesson 1 prompt
    tampered = rendered.replace("First phonetics step.", "First phonetics step from Lesson 5.")
    res = check_rendered_prompt(tampered, sample_plan_entry, card_path)
    assert res.passed is False
    assert any("unauthorized_lesson_number" in e and "5" in e for e in res.errors)


def test_check_honors_style_card_path(sample_plan_entry, sample_learner_state, sample_cited_records, tmp_path):
    """Finding 12: style_card_path parameter of render functions is honored."""
    custom_card = tmp_path / "custom_card.md"
    card_text = "Custom style card content with unique phrase: #xyz-unique-style."
    custom_card.write_text(card_text, encoding="utf-8")
    expected_sha = hashlib.sha256(card_text.encode("utf-8")).hexdigest()

    imm_payload = compute_immersion_payload("a1", arc_position=1, lesson_n=1, cumulative_core_count=0)

    rendered = render_lesson_prompt(
        plan_entry=sample_plan_entry,
        cited_records=sample_cited_records,
        learner_state=sample_learner_state,
        immersion=imm_payload,
        level="a1",
        slug="sounds-intro",
        lesson_n=1,
        style_card_path=custom_card,
    )

    assert card_text in rendered
    assert expected_sha in rendered
    assert custom_card.name in rendered


def test_check_fails_unauthorized_lesson_content(sample_plan_entry):
    card_path = CARDS_DIR / "a1.md"
    prompt = (
        f"Lesson 1 text with ## Built Lessons of this Module included.\n{SCHEMA_EXEMPLAR_BEGIN}\n{SCHEMA_EXEMPLAR_END}"
    )
    res = check_rendered_prompt(prompt, sample_plan_entry, card_path, is_recap=False)
    assert res.passed is False
    assert any("unauthorized_lesson_content" in e for e in res.errors)


def test_check_fails_style_card_mismatch(sample_plan_entry):
    card_path = CARDS_DIR / "a1.md"
    prompt = f"Prompt without the required card hash.\n{SCHEMA_EXEMPLAR_BEGIN}\n{SCHEMA_EXEMPLAR_END}"
    res = check_rendered_prompt(prompt, sample_plan_entry, card_path)
    assert res.passed is False
    assert any("card_hash_mismatch" in e for e in res.errors)
