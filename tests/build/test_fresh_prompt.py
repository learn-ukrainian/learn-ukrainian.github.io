"""Tests for fresh build engine Part E2 prompt rendering and rendered-prompt checks (#8431 §8.1)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts.build.fresh.immersion import compute_immersion_payload
from scripts.build.fresh.prompt import (
    CARDS_DIR,
    check_rendered_prompt,
    render_lesson_prompt,
    render_recap_prompt,
    style_card_info,
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
        "activities": [
            {"id": "a1", "type": "quiz", "placement": "inline", "focus": "Identify letter"}
        ],
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

    check_res = check_rendered_prompt(rendered, recap_plan, card_path, is_recap=True, built_lessons=built_lessons)
    assert check_res.passed is True
    assert check_res.errors == []


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


def test_check_fails_v1_path(sample_plan_entry):
    card_path = CARDS_DIR / "a1.md"
    bad_prompt = "Reference to curriculum/l2-uk-en/plans/a1-mod.yaml"
    res = check_rendered_prompt(bad_prompt, sample_plan_entry, card_path)
    assert res.passed is False
    assert any("forbidden_v1_path" in e for e in res.errors)

    bad_prompt_2 = "Reference to curriculum/l2-uk-en/a1-v1/intro.md"
    res_2 = check_rendered_prompt(bad_prompt_2, sample_plan_entry, card_path)
    assert res_2.passed is False
    assert any("forbidden_v1_path" in e for e in res_2.errors)


def test_check_fails_uncited_record_id(sample_plan_entry):
    card_path = CARDS_DIR / "a1.md"
    # Prompt contains extra T-999 in cited records
    prompt = (
        "## 2. Cited Evidence Records\n\n"
        "### Record T-999\n- Text: Uncited text\n\n"
        "---"
    )
    res = check_rendered_prompt(prompt, sample_plan_entry, card_path)
    assert res.passed is False
    assert any("uncited_record_id" in e and "T-999" in e for e in res.errors)


def test_check_fails_unauthorized_lesson_content(sample_plan_entry):
    card_path = CARDS_DIR / "a1.md"
    prompt = "Lesson 1 text with ## Built Lessons of this Module included."
    res = check_rendered_prompt(prompt, sample_plan_entry, card_path, is_recap=False)
    assert res.passed is False
    assert any("unauthorized_lesson_content" in e for e in res.errors)


def test_check_fails_style_card_mismatch(sample_plan_entry):
    card_path = CARDS_DIR / "a1.md"
    # Prompt missing card sha
    prompt = "Prompt without the required card hash."
    res = check_rendered_prompt(prompt, sample_plan_entry, card_path)
    assert res.passed is False
    assert any("card_hash_mismatch" in e for e in res.errors)
