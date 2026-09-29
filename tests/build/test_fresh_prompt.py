"""Tests for fresh build engine Part E2 prompt rendering and rendered-prompt checks (#8431 §8.1)."""

from __future__ import annotations

import dataclasses
import hashlib
from pathlib import Path

import pytest

from scripts.build.fresh.immersion import compute_immersion_payload
from scripts.build.fresh.manifest import learner_state_sha256
from scripts.build.fresh.prompt import (
    CARDS_DIR,
    LEARNER_STATE_BEGIN,
    LEARNER_STATE_END,
    SCHEMA_EXEMPLAR_BEGIN,
    SCHEMA_EXEMPLAR_END,
    check_rendered_prompt,
    grammar_points,
    learner_state_block,
    learner_state_view,
    render_lesson_prompt,
    render_recap_prompt,
)
from scripts.curriculum.learner_state.planned import PlannedState

pytestmark = pytest.mark.reads_content

REPO_ROOT = Path(__file__).resolve().parents[2]

SAMPLE_WORD_STORE = {"words": [{"id": "W-base-1", "lemma": "і"}]}


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
        word_store=SAMPLE_WORD_STORE,
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

    check_res = check_rendered_prompt(
        rendered, sample_plan_entry, card_path, learner_state=sample_learner_state, word_store=SAMPLE_WORD_STORE
    )
    assert check_res.passed is True
    assert check_res.errors == []
    assert check_res.prompt_sha256 == hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    assert len(check_res.prompt_sha256) == 64


def test_render_lesson_prompt_uncited_pending_form(sample_plan_entry, sample_learner_state, sample_cited_records):
    """A cited word can contain an uncited pending form without leaking a guessed stress."""
    sample_cited_records["W-001"]["forms"].append({"form": "mamy", "tags": "tag-gen", "stress_source": "pending"})
    rendered = render_lesson_prompt(
        plan_entry=sample_plan_entry,
        cited_records=sample_cited_records,
        learner_state=sample_learner_state,
        word_store=SAMPLE_WORD_STORE,
        immersion=compute_immersion_payload("a1", arc_position=1, lesson_n=1, cumulative_core_count=0),
        level="a1",
        slug="sounds-intro",
        lesson_n=1,
        style_card_path=CARDS_DIR / "a1.md",
    )

    assert "form: mama, tags: tag-nom, stressed: mama, stress_source: vesum" in rendered
    assert (
        "form: mamy, tags: tag-gen, stressed: (pending — no confirmed stress; do not print this form), "
        "stress_source: pending"
    ) in rendered
    assert "stressed: mamy" not in rendered
    assert check_rendered_prompt(
        rendered,
        sample_plan_entry,
        CARDS_DIR / "a1.md",
        learner_state=sample_learner_state,
        word_store=SAMPLE_WORD_STORE,
    ).passed


def test_render_recap_prompt(sample_plan_entry, sample_learner_state, sample_cited_records):
    """Recap prompt variant renders built lessons and passes recap check."""
    imm_payload = compute_immersion_payload("a1", arc_position=1, lesson_n=2, cumulative_core_count=5)
    card_path = CARDS_DIR / "a1.md"
    recap_plan = dict(sample_plan_entry)
    recap_plan["lesson"] = {"module": "a1/sounds-intro", "n": 2}
    built_lessons = [
        {
            "n": 1,
            "title": "Lesson 1",
            "content": "# Built lesson MDX",
            "sha256": hashlib.sha256(b"# Built lesson MDX").hexdigest(),
        }
    ]

    rendered = render_recap_prompt(
        plan_entry=recap_plan,
        built_lessons=built_lessons,
        cited_records=sample_cited_records,
        learner_state=sample_learner_state,
        word_store=SAMPLE_WORD_STORE,
        immersion=imm_payload,
        level="a1",
        slug="sounds-intro",
        lesson_n=2,
        style_card_path=card_path,
    )

    assert "## 2. Built Lessons of this Module" in rendered
    assert "Built Lesson 1: Lesson 1" in rendered
    assert "```mdx\n# Built lesson MDX" in rendered
    assert built_lessons[0]["sha256"] in rendered
    assert SCHEMA_EXEMPLAR_BEGIN in rendered
    assert SCHEMA_EXEMPLAR_END in rendered

    check_res = check_rendered_prompt(
        rendered,
        recap_plan,
        card_path,
        is_recap=True,
        built_lessons=built_lessons,
        learner_state=sample_learner_state,
        word_store=SAMPLE_WORD_STORE,
    )
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
        word_store=SAMPLE_WORD_STORE,
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
        word_store=SAMPLE_WORD_STORE,
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
        word_store=SAMPLE_WORD_STORE,
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


def test_render_prompt_does_not_html_escape(sample_plan_entry, sample_learner_state):
    """Rendered prompt preserves literal <, >, and & characters without HTML entity escaping."""
    cited_records = {
        "W-001": {
            "lemma": "mama",
            "pos": "noun",
            "forms": [{"form": "mama", "tags": "tag-nom", "stressed": "mama", "stress_source": "vesum"}],
        },
        "EX-001": {
            "example": "Це <приклад> & тест",
            "translation": "This is an <example> & test",
            "source": "textbook-1",
        },
        "T-001": {
            "text": "Rule: <a> & <b>",
            "source": "textbook-1",
        },
    }
    imm_payload = compute_immersion_payload("a1", arc_position=1, lesson_n=1, cumulative_core_count=0)
    card_path = CARDS_DIR / "a1.md"

    rendered = render_lesson_prompt(
        plan_entry=sample_plan_entry,
        cited_records=cited_records,
        learner_state=sample_learner_state,
        word_store=SAMPLE_WORD_STORE,
        immersion=imm_payload,
        level="a1",
        slug="sounds-intro",
        lesson_n=1,
        style_card_path=card_path,
    )

    assert "Це <приклад> & тест" in rendered
    assert "This is an <example> & test" in rendered
    assert "Rule: <a> & <b>" in rendered
    assert "&lt;" not in rendered
    assert "&gt;" not in rendered
    assert "&amp;" not in rendered

    res = check_rendered_prompt(
        rendered, sample_plan_entry, card_path, learner_state=sample_learner_state, word_store=SAMPLE_WORD_STORE
    )
    assert res.passed is True


# --- #9182: the writer sees the complete planned learner state -------------------------------------------------

STATE_WORD_STORE = {
    "words": [
        {"id": "W-2", "lemma": "я"},
        {"id": "W-10", "lemma": "і"},
        {"id": "W-3", "lemma": "привіт"},
        {"id": "W-11", "lemma": "день"},
        {"id": "W-40", "lemma": "Оксана"},
    ]
}
STATE_GRAMMAR = {
    "G-a1-001": "A sound and a letter are different units.",
    "G-a1-002": "Vowels and consonants are different sound classes.",
}
STATE_SOURCES = {"word_store": STATE_WORD_STORE, "grammar_registry": STATE_GRAMMAR}


@pytest.fixture
def full_learner_state():
    return PlannedState(
        level="a1",
        position=2,
        lesson_n=3,
        base_ids=("W-10", "W-2"),
        core_ids={"W-11": {"position": 2, "lesson": 1}, "W-3": {"position": 1, "lesson": 2}},
        grammar_ids={"G-a1-002": {"position": 1, "lesson": 3}, "G-a1-001": {"position": 1, "lesson": 2}},
        letters={
            "М": {"position": 2, "lesson": 1},
            "О": {"position": 1, "lesson": 2},
            "А": {"position": 1, "lesson": 2},
            "І": {"position": 1, "lesson": 3},
            "Г": {"position": 1, "lesson": 3},
        },
        name_ids={"W-40": {"position": 2, "lesson": 3}},
        cumulative_core_count=2,
    )


def _render_state_prompt(plan_entry, state, cited, *, recap: bool = False, **kw):
    common = dict(
        cited_records=cited,
        learner_state=state,
        immersion=compute_immersion_payload("a1", arc_position=2, lesson_n=3, cumulative_core_count=2),
        level="a1",
        slug="sounds-intro",
        lesson_n=1,
        style_card_path=CARDS_DIR / "a1.md",
        **STATE_SOURCES,
        **kw,
    )
    if recap:
        return render_recap_prompt(plan_entry, built_lessons=[], **common)
    return render_lesson_prompt(plan_entry, **common)


def _state_block(prompt: str) -> str:
    return prompt.split(LEARNER_STATE_BEGIN, 1)[1].split(LEARNER_STATE_END, 1)[0]


@pytest.mark.parametrize("recap", [False, True])
def test_prompt_lists_every_letter_grammar_point_and_word(
    sample_plan_entry, full_learner_state, sample_cited_records, recap
):
    """Both writer paths render the whole state in a fixed order and pass the check with it."""
    prompt = _render_state_prompt(sample_plan_entry, full_learner_state, sample_cited_records, recap=recap)
    block = _state_block(prompt)

    assert "**Letters taught** (5, in taught order): О А І Г М" in block
    assert "  - `G-a1-001`: A sound and a letter are different units.\n  - `G-a1-002`: Vowels" in block
    assert "**Allowed words** (5; any form of each may be used)" in block
    assert "  - Base layer (2): `W-2` я, `W-10` і\n" in block
    assert "  - Core words of earlier lessons (2): `W-3` привіт, `W-11` день\n" in block
    assert "  - Names admitted for use (1): `W-40` Оксана\n" in block
    assert "Recycle earlier words and grammar wherever a step allows." in prompt
    assert "write read and copy items only with letters taught above" in prompt
    assert "**Cumulative Core Count**: 2" in prompt
    assert "**Allowed Word IDs**: 5 words" in prompt

    check = check_rendered_prompt(
        prompt,
        sample_plan_entry,
        CARDS_DIR / "a1.md",
        is_recap=recap,
        learner_state=full_learner_state,
        **STATE_SOURCES,
    )
    assert check.errors == []


@pytest.mark.parametrize("plan_order", [("О", "А"), ("А", "О")])
def test_letters_of_one_lesson_render_in_the_plans_order(
    sample_plan_entry, full_learner_state, sample_cited_records, plan_order
):
    """Letters introduced in the same lesson keep the plan's order in the writer block and the rebuilt block."""
    letters = {letter: {"position": 1, "lesson": 2} for letter in plan_order}
    state = dataclasses.replace(full_learner_state, letters=letters)
    prompt = _render_state_prompt(sample_plan_entry, state, sample_cited_records)
    block = _state_block(prompt)

    assert f"**Letters taught** (2, in taught order): {' '.join(plan_order)}" in block
    assert block == learner_state_block(state, STATE_WORD_STORE, STATE_GRAMMAR)
    assert block == learner_state_block(state.to_dict(), STATE_WORD_STORE, STATE_GRAMMAR)
    assert learner_state_view(state, STATE_WORD_STORE, STATE_GRAMMAR)["letters"] == list(plan_order)
    assert _state_errors(prompt, sample_plan_entry, state, **STATE_SOURCES) == []


def test_state_section_is_deterministic_and_matches_the_reviewer_document(
    sample_plan_entry, full_learner_state, sample_cited_records
):
    """The PlannedState and its to_dict() document (what the reviewer receives) render byte-identically."""
    first = _render_state_prompt(sample_plan_entry, full_learner_state, sample_cited_records)
    again = _render_state_prompt(sample_plan_entry, full_learner_state, sample_cited_records)
    as_document = _render_state_prompt(sample_plan_entry, full_learner_state.to_dict(), sample_cited_records)
    assert first == again
    assert _state_block(first) == _state_block(as_document)


def test_state_section_keeps_the_learner_state_echo_and_hash(
    sample_plan_entry, full_learner_state, sample_cited_records
):
    """Rendering the section neither changes the state identity nor the echoed learner_state_sha256."""
    identity = learner_state_sha256(full_learner_state)
    prompt = _render_state_prompt(
        sample_plan_entry, full_learner_state, sample_cited_records, learner_state_sha256=identity
    )
    assert f'learner_state_sha256: "{identity}"' in prompt
    assert learner_state_sha256(full_learner_state) == identity
    check = check_rendered_prompt(
        prompt, sample_plan_entry, CARDS_DIR / "a1.md", learner_state=full_learner_state, **STATE_SOURCES
    )
    assert check.prompt_sha256 == hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def test_render_fails_when_a_state_id_has_no_lemma_or_point(
    sample_plan_entry, full_learner_state, sample_cited_records
):
    with pytest.raises(ValueError, match=r"learner_state_unresolved.*W-40.*G-a1-002"):
        learner_state_view(
            full_learner_state,
            {"words": [row for row in STATE_WORD_STORE["words"] if row["id"] != "W-40"]},
            {"G-a1-001": STATE_GRAMMAR["G-a1-001"]},
        )


def _state_errors(prompt, plan_entry, state, **sources):
    return check_rendered_prompt(prompt, plan_entry, CARDS_DIR / "a1.md", learner_state=state, **sources).errors


def test_state_block_is_the_block_the_state_renders(sample_plan_entry, full_learner_state, sample_cited_records):
    """The check regenerates the block from the state and its sources: the prompt's block is those exact bytes."""
    prompt = _render_state_prompt(sample_plan_entry, full_learner_state, sample_cited_records)
    assert _state_block(prompt) == learner_state_block(full_learner_state, STATE_WORD_STORE, STATE_GRAMMAR)
    assert _state_errors(prompt, sample_plan_entry, full_learner_state, **STATE_SOURCES) == []


@pytest.mark.parametrize(
    "old, new, line",
    [
        pytest.param("in taught order): О А І Г М", "in taught order): О А І Г М Ф", "О А І Г М Ф", id="extra-letter"),
        pytest.param("in taught order): О А І Г М", "in taught order): О А І Г", "О А І Г'", id="missing-letter"),
        pytest.param(
            "different units.",
            "different sounds.",
            "`G-a1-001`: A sound and a letter are different sounds.",
            id="changed-grammar-point",
        ),
        pytest.param("`W-3` привіт", "`W-3` пока", "`W-3` пока", id="changed-lemma"),
        pytest.param("`W-3` привіт, `W-11` день", "`W-3` привіт", "(2): `W-3` привіт'", id="missing-word"),
        pytest.param("`W-40` Оксана", "`W-40` Оксана, `W-99` кіт", "`W-99` кіт", id="foreign-word"),
        pytest.param(
            "\n  - `G-a1-002`: Vowels and consonants are different sound classes.",
            "",
            "`G-a1-002`",
            id="missing-grammar-point",
        ),
    ],
)
def test_check_rejects_any_departure_from_the_state_block(
    sample_plan_entry, full_learner_state, sample_cited_records, old, new, line
):
    """An extra, missing or changed letter, grammar point, lemma or word fails the exact-block check."""
    prompt = _render_state_prompt(sample_plan_entry, full_learner_state, sample_cited_records)
    assert prompt.count(old) == 1
    errors = _state_errors(prompt.replace(old, new), sample_plan_entry, full_learner_state, **STATE_SOURCES)
    assert any(e.startswith("learner_state_mismatch") and line in e for e in errors), errors


def test_check_admits_state_ids_only_inside_the_block(sample_plan_entry, full_learner_state, sample_cited_records):
    card = CARDS_DIR / "a1.md"
    prompt = _render_state_prompt(sample_plan_entry, full_learner_state, sample_cited_records)

    outside = prompt.replace("First phonetics step.", "First phonetics step with W-11.")
    assert any(
        "uncited_record_id" in e and "W-11" in e
        for e in _state_errors(outside, sample_plan_entry, full_learner_state, **STATE_SOURCES)
    )

    unverified = check_rendered_prompt(prompt, sample_plan_entry, card)
    assert any("learner_state_unverified" in e for e in unverified.errors)

    unresolved = _state_errors(prompt, sample_plan_entry, full_learner_state, word_store=STATE_WORD_STORE)
    assert any(e.startswith("learner_state_unresolved") and "G-a1-001" in e for e in unresolved)

    no_block = prompt.replace(LEARNER_STATE_BEGIN, "")
    assert any(
        "missing_learner_state_marker" in e
        for e in _state_errors(no_block, sample_plan_entry, full_learner_state, **STATE_SOURCES)
    )


def test_grammar_points_reads_the_registry(tmp_path):
    registry = tmp_path / "_grammar.yaml"
    assert grammar_points(registry, "a1") == {}
    registry.write_text(
        "- id: G-a1-001\n  point: A sound and a letter differ.\n  introduced_at: {position: 1, lesson: first}\n",
        encoding="utf-8",
    )
    assert grammar_points(registry, "a1") == {"G-a1-001": "A sound and a letter differ."}
    registry.write_text("- id: bad\n", encoding="utf-8")
    with pytest.raises(ValueError, match="grammar registry"):
        grammar_points(registry, "a1")
