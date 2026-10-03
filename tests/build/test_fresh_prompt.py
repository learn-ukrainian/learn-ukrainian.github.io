"""Tests for fresh build engine Part E2 prompt rendering and rendered-prompt checks (#8431 §8.1)."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.build.fresh import runner
from scripts.build.fresh.immersion import compute_immersion_payload
from scripts.build.fresh.manifest import learner_state_document, learner_state_sha256, materialize_learner_state
from scripts.build.fresh.prompt import (
    CARDS_DIR,
    CITED_RECORDS_BEGIN,
    CITED_RECORDS_END,
    EVIDENCE_PACK_SCHEMA,
    LEARNER_STATE_BEGIN,
    LEARNER_STATE_END,
    RECORD_ID_RE,
    RECORD_KINDS,
    SCHEMA_EXEMPLAR_BEGIN,
    SCHEMA_EXEMPLAR_END,
    check_rendered_prompt,
    cited_record_views,
    grammar_points,
    learner_state_block,
    learner_state_view,
    render_lesson_prompt,
    render_recap_prompt,
)
from scripts.build.fresh.requires_confirm import questions_from_draft, write_questions
from scripts.curriculum.evidence import lock
from scripts.curriculum.learner_state.planned import PlannedState
from scripts.delegate import _read_only_write_intent_error
from scripts.review.prompts.render import ManifestReader, _learner_state_context

pytestmark = pytest.mark.reads_content

SAMPLE_WORD_STORE = {"words": [{"id": "W-base-1", "lemma": "і"}]}

SHA = "0" * 64

# Real-shaped records of every evidence-pack v1 kind (schemas/evidence-pack-v1.schema.json), with sources and
# field values as the A1 position-1 pack carries them (#9185).
ULP_SOURCE = {
    "author": "Ukrainian Lessons Podcast",
    "chunk_id": "ulp-1-00-lesson-notes_l0005_w003",
    "file": "ulp-1-00-lesson-notes",
    "grade": "",
    "kind": "textbook",
    "page": None,
    "row_sha256": SHA,
    "section_id": None,
}
PRIMER_SOURCE = {
    "author": "zaharijchuk",
    "chunk_id": "1-klas-bukvar-zaharijchuk-2025-1_s0012",
    "file": "1-klas-bukvar-zaharijchuk-2025-1",
    "grade": "1",
    "kind": "textbook",
    "page": 15,
    "row_sha256": SHA,
    "section_id": 12963,
}
TEXT_RECORD = {
    "id": "T-004",
    "source": ULP_SOURCE,
    "quote": "the podcast for learning how to pronounce и:\n 1. In the English language",
    "sha256": SHA,
    "supports": "Adult L2 И sound and comparison with І for English speakers; ULP Season 1 lesson 5 trainer.",
}
EXERCISE_RECORD = {
    "id": "X-004",
    "source": PRIMER_SOURCE,
    "quote": "Відшукай «загублений» склад у словах.\nма- __ -на",
    "sha256": SHA,
    "pattern": "Pick a missing syllable from a bounded list to complete a known word.",
    "items_sample": ["Відшукай «загублений» склад у словах.\nма- __ -на", "со- __ ма-, -ва, -ла"],
}
EXAMPLE_RECORD = {
    "id": "EX-001",
    "source": {
        "kind": "literary",
        "file": "shevchenko-kobzar",
        "author": "Тарас Шевченко",
        "work": "Кобзар",
        "year": 1840,
        "page": None,
        "chunk_id": 7,
    },
    "text": "Добрий день, пане!",
    "sha256": SHA,
    "sentence_ref": {"words": ["W-555"]},
    "translation_en": "Good day, sir!",
}
ERROR_RECORD = {
    "id": "E-001",
    "source": {"table": "ua_gec_errors", "id": 4821, "row_sha256": SHA},
    "incorrect": "приймати участь",
    "correct": "брати участь",
    "error_type": "Calque",
    "pattern": "Russian calque of принимать участие.",
}
NOTE_RECORD = {
    "id": "N-001",
    "source": {"table": "style_guide", "id": 312},
    "word": "вибачте",
    "section": None,
    "text": "Вибачте — ввічливе прохання.",
    "excerpt_full": None,
    "russianism_pattern": None,
}
VIDEO_RECORD = {
    "id": "V-004",
    "url": "https://www.youtube.com/watch?v=W-1rCu0indE",
    "channel": "Ukrainian Lessons",
    "use": "Listening model for the informal greeting in lesson 1.",
    "checked": {
        "http_status": 200,
        "final_url": "https://www.youtube.com/watch?v=W-1rCu0indE",
        "content_type": "text/html",
        "date": "2026-09-29",
    },
}
STANDARD_RECORD = {
    "id": "S-001",
    "lines": "351-353",
    "text": "      1.3.1.1. Особа вміє:\n      написати власне прізвище та ім’я;",
    "file_sha256": SHA,
}
UNSUPPORTED_RECORD = {
    "id": "U-001",
    "claim": "A1 learners confuse И and І by ear.",
    "searches": [{"tool": "search_text", "query": "и і розрізнення"}],
    "status": "open",
}


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
        "EX-001": {**EXAMPLE_RECORD, "id": "EX-001", "text": "mama doma", "translation_en": "mom is home"},
        "T-001": {**TEXT_RECORD, "id": "T-001", "quote": "Attested rule text"},
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


@pytest.mark.parametrize("level", ["a2", "b1", "b2"])
@pytest.mark.parametrize("recap", [False, True])
def test_non_a1_rendered_prompts_keep_main_candidate_wording(
    sample_plan_entry, sample_learner_state, sample_cited_records, level: str, recap: bool
) -> None:
    sample_cited_records["W-001"]["lemma"] = "книга"
    sample_cited_records["W-001"]["forms"][0].update(
        {"form": "книга", "tags": "noun:inanim:f:v_naz", "stressed": "кни́га", "learner": True}
    )
    sample_plan_entry["lesson"] = {"module": f"{level}/sounds-intro", "n": 2 if recap else 1}
    common = dict(
        plan_entry=sample_plan_entry,
        cited_records=sample_cited_records,
        learner_state=sample_learner_state,
        word_store=SAMPLE_WORD_STORE,
        immersion=compute_immersion_payload("a1", arc_position=1, lesson_n=1, cumulative_core_count=0),
        level=level,
        slug="sounds-intro",
        lesson_n=2 if recap else 1,
    )
    rendered = render_recap_prompt(built_lessons=[], **common) if recap else render_lesson_prompt(**common)
    assert (
        "Use one form from its bound record per option. State the complete slot `requires`; "
        "choose one admitted key and distractors that differ in `tests_feature`. "
        "The engine generates the item-specific subset and checks every written option."
    ) in rendered
    assert "partitive genitive after request" not in rendered


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
            **EXAMPLE_RECORD,
            "id": "EX-001",
            "text": "Це <приклад> & тест",
            "translation_en": "This is an <example> & test",
        },
        "T-001": {**TEXT_RECORD, "id": "T-001", "quote": "Rule: <a> & <b>"},
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


@pytest.mark.parametrize("recap", [False, True], ids=["lesson-writer", "recap-writer"])
@pytest.mark.parametrize("state_fixture", ["sample_learner_state", "full_learner_state"], ids=["letters", "later"])
def test_read_only_writer_prompt_contract(request, sample_plan_entry, sample_cited_records, state_fixture, recap):
    """Both writer templates must pass the dispatch guard in both learner stages (#9375)."""
    state = request.getfixturevalue(state_fixture)
    plan = dict(sample_plan_entry)
    n = state.lesson_n + int(recap)
    plan["lesson"] = {**plan["lesson"], "n": n}
    kwargs = dict(
        plan_entry=plan,
        cited_records=sample_cited_records,
        learner_state=state,
        immersion=compute_immersion_payload(
            "a1", arc_position=state.position, lesson_n=n, cumulative_core_count=state.cumulative_core_count
        ),
        level="a1",
        slug=plan["slug"],
        lesson_n=n,
        style_card_path=CARDS_DIR / "a1.md",
        word_store=SAMPLE_WORD_STORE if state_fixture == "sample_learner_state" else STATE_WORD_STORE,
        grammar_registry=STATE_GRAMMAR,
    )
    if recap:
        content = "# Built lesson MDX"
        kwargs["built_lessons"] = [
            {
                "n": n - 1,
                "title": "Earlier lesson",
                "content": content,
                "sha256": hashlib.sha256(content.encode()).hexdigest(),
            }
        ]
    rendered = (render_recap_prompt if recap else render_lesson_prompt)(**kwargs)

    assert _read_only_write_intent_error(mode="read-only", prompt=rendered) is None
    assert (
        "Examples and activity items must use only this lesson's own plan entry (its letters, grammar and words) "
        "and the material taught before this lesson listed in this section."
    ) in rendered


def test_read_only_requires_confirm_prompt_contract(tmp_path, sample_plan_entry, sample_cited_records):
    """Exercise question and option loops through the production confirmation renderer."""
    record = sample_cited_records["W-001"]
    draft = {
        "activities": [
            {
                "id": "a1",
                "items": [
                    {
                        "kind": "form",
                        "sentence": "___",
                        "options": [record["forms"][0]["form"], record["lemma"]],
                        "correct": 0,
                        "requires": {"Case": "Nom"},
                    }
                ],
            }
        ]
    }
    lesson = {**sample_plan_entry, "lesson": {"level": "a1", "slug": sample_plan_entry["slug"], "n": 1}}
    batch = questions_from_draft(draft, lesson, {"draft_sha256": SHA})
    write_questions(tmp_path, 1, batch)
    rendered = (tmp_path / "lesson-1.requires-confirm.prompt.md").read_text(encoding="utf-8")

    assert "## a1/0" in rendered
    assert f"- 0: {record['lemma']} [key]" in rendered
    assert f"- 1: {record['lemma']}" in rendered
    assert _read_only_write_intent_error(mode="read-only", prompt=rendered) is None


def test_read_only_constrained_resolution_prompt_contract(
    tmp_path, monkeypatch, sample_plan_entry, sample_cited_records
):
    """Capture the runner's actual inline prompt without invoking a provider."""
    batch = {
        "lesson": {"level": "a1", "slug": sample_plan_entry["slug"], "n": 1},
        "questions": [
            {
                "id": "Q-001",
                "sentence": "___",
                "candidates": [
                    {"record": record_id, **record}
                    for record_id, record in sample_cited_records.items()
                    if record_id.startswith("W-")
                ],
            }
        ],
    }
    answer_file = tmp_path / "answers.yaml"
    answer_file.write_text("answers: []\n", encoding="utf-8")
    prompts = []

    def fake_run(cmd, **kwargs):
        if "dispatch" in cmd:
            assert cmd[cmd.index("--mode") + 1] == "read-only"
            prompts.append(Path(cmd[cmd.index("--prompt-file") + 1]).read_text(encoding="utf-8"))
            output = ""
        else:
            assert "wait" in cmd
            output = json.dumps({"status": "done", "result_file": str(answer_file)})
        return subprocess.CompletedProcess(cmd, 0, stdout=output, stderr="")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    assert runner.dispatch_questions(batch, "codex:fixture", repo_root=tmp_path) == {"answers": []}
    assert len(prompts) == 1
    assert yaml.safe_load(prompts[0].split("\n\n", 1)[1]) == batch
    assert _read_only_write_intent_error(mode="read-only", prompt=prompts[0]) is None


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


@pytest.mark.parametrize("plan_order", [("Б", "А"), ("А", "Б")])
def test_the_reviewer_reads_the_taught_order_the_writer_saw(
    tmp_path, sample_plan_entry, full_learner_state, sample_cited_records, plan_order
):
    """The saved learner state keeps the letters' taught order, and its identity hash covers that order (#9182)."""
    letters = {letter: {"position": 1, "lesson": 2} for letter in plan_order}
    state = dataclasses.replace(full_learner_state, letters=letters)
    writer_block = _state_block(_render_state_prompt(sample_plan_entry, state, sample_cited_records))

    state_path = tmp_path / "curriculum/l2-uk-en/evidence/a1/_state/sample/lesson-3.learner-state.yaml"
    identity = learner_state_sha256(state)
    manifest = {
        "kind": "module",
        "inputs": {"learner_state": materialize_learner_state(state_path, learner_state_document(state), tmp_path)},
        "learner_state": {"sha256": identity, "source": "planned_state"},
    }
    reviewed = _learner_state_context(ManifestReader(manifest, tmp_path), manifest)
    reviewer_state = yaml.safe_load(reviewed["learner_state_yaml"])

    assert list(reviewer_state["letters"]) == list(plan_order)
    assert learner_state_block(reviewer_state, STATE_WORD_STORE, STATE_GRAMMAR) == writer_block
    assert reviewed["learner_state_sha256"] == identity
    reversed_letters = dataclasses.replace(state, letters=dict(reversed(letters.items())))
    # Teaching the same letters in another order is another learner state: an order-only change in an
    # earlier plan must change the identity every freshness check compares.
    assert learner_state_sha256(reversed_letters) != identity
    if list(plan_order) == sorted(plan_order):  # a code-point-ordered state keeps the bytes and hash it had
        canonical = json.dumps(state.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        assert identity == hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        assert state_path.read_bytes() == lock.yaml_bytes(learner_state_document(state))


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


# --- #9185: the cited-records section renders every pack record kind from its schema fields -------------------

ALL_KINDS = {
    "E-001": ERROR_RECORD,
    "EX-001": EXAMPLE_RECORD,
    "N-001": NOTE_RECORD,
    "S-001": STANDARD_RECORD,
    "T-004": TEXT_RECORD,
    "U-001": UNSUPPORTED_RECORD,
    "V-004": VIDEO_RECORD,
    "W-001": {
        "lemma": "mama",
        "pos": "noun",
        "forms": [{"form": "mama", "tags": "tag-nom", "stressed": "mama", "stress_source": "vesum"}],
    },
    "X-004": EXERCISE_RECORD,
}


def _citing(plan_entry, ids, **changes):
    """The sample plan entry with step s1 citing ``ids`` as evidence."""
    steps = [dict(plan_entry["steps"][0], evidence=sorted(ids)), *plan_entry["steps"][1:]]
    return {**plan_entry, "steps": steps, **changes}


def _render(plan_entry, learner_state, cited, *, recap=False):
    common = dict(
        cited_records=cited,
        learner_state=learner_state,
        word_store=SAMPLE_WORD_STORE,
        immersion=compute_immersion_payload("a1", arc_position=1, lesson_n=1, cumulative_core_count=0),
        level="a1",
        slug="sounds-intro",
        lesson_n=1,
        style_card_path=CARDS_DIR / "a1.md",
    )
    if recap:
        return render_recap_prompt(plan_entry, built_lessons=[], **common)
    return render_lesson_prompt(plan_entry, **common)


def _check(prompt, plan_entry, learner_state, *, recap=False):
    return check_rendered_prompt(
        prompt,
        plan_entry,
        CARDS_DIR / "a1.md",
        is_recap=recap,
        built_lessons=[],
        learner_state=learner_state,
        word_store=SAMPLE_WORD_STORE,
    )


def _cited_block(prompt: str) -> str:
    return prompt.split(CITED_RECORDS_BEGIN, 1)[1].split(CITED_RECORDS_END, 1)[0]


@pytest.mark.parametrize("recap", [False, True])
def test_every_pack_record_kind_renders_from_its_schema_fields(sample_plan_entry, sample_learner_state, recap):
    plan = _citing(sample_plan_entry, ALL_KINDS)
    prompt = _render(plan, sample_learner_state, ALL_KINDS, recap=recap)
    block = _cited_block(prompt)

    expected = [
        # text: quote bytes fenced, source attribution without the null page and empty grade, supports
        "### Record `T-004`\n- Kind: text\n- Source: textbook: Ukrainian Lessons Podcast, ulp-1-00-lesson-notes\n"
        "- Supports: Adult L2 И sound and comparison with І for English speakers; ULP Season 1 lesson 5 trainer.\n"
        "- Quote (verbatim source text):\n```text\nthe podcast for learning how to pronounce и:\n"
        " 1. In the English language\n```",
        # exercise: pattern, quote, and only the sample items the quote does not already show
        "### Record `X-004`\n- Kind: exercise\n"
        "- Source: textbook: zaharijchuk, 1-klas-bukvar-zaharijchuk-2025-1, grade 1, page 15\n"
        "- Pattern: Pick a missing syllable from a bounded list to complete a known word.\n"
        "- Quote (verbatim source text):\n```text\nВідшукай «загублений» склад у словах.\nма- __ -на\n```\n"
        "- Sample item 1:\n```text\nсо- __ ма-, -ва, -ла\n```",
        # example: text and translation_en, literary source
        "### Record `EX-001`\n- Kind: example\n- Source: literary: Тарас Шевченко, Кобзар, 1840, shevchenko-kobzar\n"
        "- Text (verbatim):\n```text\nДобрий день, пане!\n```\n"
        "- English translation (the engine prints it; do not translate): Good day, sir!",
        "### Record `E-001`\n- Kind: error\n- Source: ua_gec_errors row 4821\n- Incorrect: приймати участь\n"
        "- Correct: брати участь\n- Error type: Calque\n- Pattern: Russian calque of принимать участие.",
        # note: null section, excerpt and russianism pattern are left out
        "### Record `N-001`\n- Kind: note\n- Source: style_guide row 312\n- Word: вибачте\n"
        "- Text:\n```text\nВибачте — ввічливе прохання.\n```\n\n",
        "### Record `V-004`\n- Kind: video\n- Channel: Ukrainian Lessons\n"
        "- URL: https://www.youtube.com/watch?v=W-1rCu0indE\n"
        "- Use: Listening model for the informal greeting in lesson 1.\n"
        "- Models: undeclared (listening_model_undeclared)\n- Link check: HTTP 200 on 2026-09-29\n",
        "### Record `S-001`\n- Kind: standard\n- Source: State Standard, lines 351-353\n- Text (verbatim):\n"
        "```text\n      1.3.1.1. Особа вміє:\n      написати власне прізвище та ім’я;\n```",
        "### Record `U-001`\n- Kind: unsupported\n- Claim: A1 learners confuse И and І by ear.\n- Status: open\n"
        "- Searches: search_text: и і розрізнення",
        "### Record `W-001`\n- Kind: word\n- Lemma: mama\n- Part of Speech: noun\n- Forms:\n"
        "  - form: mama, tags: tag-nom, stressed: mama, stress_source: vesum",
    ]
    for chunk in expected:
        assert chunk in block
    assert block.count("ма- __ -на") == 1
    assert "W-555" not in prompt  # an example's sentence_ref is engine data, not writer input
    assert "None" not in block and "Raw:" not in prompt and "{'" not in block
    assert _check(prompt, plan, sample_learner_state, recap=recap).errors == []


@pytest.mark.parametrize(
    ("record_id", "record", "line"),
    [
        pytest.param("V-004", {**VIDEO_RECORD, "checked": None}, "- Link check: not checked\n", id="video-unchecked"),
        pytest.param(
            "V-004",
            {**VIDEO_RECORD, "checked": {**VIDEO_RECORD["checked"], "final_url": "https://youtu.be/x"}},
            "- Link check: HTTP 200 on 2026-09-29, final URL https://youtu.be/x\n",
            id="video-redirected",
        ),
        pytest.param(
            "N-001",
            {**NOTE_RECORD, "section": "Етикет", "excerpt_full": "Повний текст.", "russianism_pattern": "извините"},
            "- Section: Етикет\n- Text:\n```text\nВибачте — ввічливе прохання.\n```\n- Full excerpt:\n"
            "```text\nПовний текст.\n```\n- Russianism pattern: извините\n",
            id="note-full",
        ),
        pytest.param(
            "U-001",
            {**UNSUPPORTED_RECORD, "status": "resolved", "resolved_by": {"record": "T-004"}},
            "- Status: resolved\n- Searches: search_text: и і розрізнення\n- Resolved by: T-004\n",
            id="unsupported-resolved",
        ),
        pytest.param(
            "T-004",
            {**TEXT_RECORD, "quote": "Code: ```x```"},
            "````text\nCode: ```x```\n````",
            id="fence-outruns-backticks",
        ),
    ],
)
def test_optional_record_fields_render_when_present(sample_plan_entry, sample_learner_state, record_id, record, line):
    cited = {record_id: record}
    plan = _citing(sample_plan_entry, [record_id, "T-004"])  # T-004: the record U-001 is resolved by
    prompt = _render(plan, sample_learner_state, cited)
    assert line in _cited_block(prompt)
    assert _check(prompt, plan, sample_learner_state).errors == []


@pytest.mark.parametrize(
    ("cited", "message"),
    [
        pytest.param({"Q-001": {"text": "x"}}, "'Q-001' is not a known record kind", id="unknown-kind"),
        pytest.param(
            {"T-004": {k: v for k, v in TEXT_RECORD.items() if k != "quote"}},
            "text record 'T-004' lacks ['quote']",
            id="text-without-quote",
        ),
        pytest.param(
            {"V-004": {k: v for k, v in VIDEO_RECORD.items() if k != "channel"}},
            "video record 'V-004' lacks ['channel']",
            id="video-without-channel",
        ),
        pytest.param(
            {"T-004": {**TEXT_RECORD, "source": {**ULP_SOURCE, "kind": "podcast"}}},
            "unknown source kind 'podcast'",
            id="unknown-source-kind",
        ),
    ],
)
def test_an_unknown_or_incomplete_record_fails_the_render(sample_plan_entry, sample_learner_state, cited, message):
    with pytest.raises(ValueError, match=f"^cited_record_invalid: .*{re.escape(message)}"):
        cited_record_views(cited)
    with pytest.raises(ValueError, match="cited_record_invalid"):
        _render(_citing(sample_plan_entry, cited), sample_learner_state, cited)


def test_record_kinds_cover_every_record_kind_of_the_pack_schema():
    defs = json.loads(EVIDENCE_PACK_SCHEMA.read_text(encoding="utf-8"))["$defs"]
    schema_kinds = {
        spec["properties"]["id"]["pattern"].removeprefix("^").split("-", 1)[0]: name.removesuffix("_record")
        for name, spec in defs.items()
        if name.endswith("_record")
    }
    assert schema_kinds == {prefix: kind for prefix, kind in RECORD_KINDS.items() if prefix != "W"}


def test_video_models_are_rendered_as_structured_data(sample_plan_entry, sample_learner_state):
    models = {"letters": ["А"], "words": ["W-001"], "segment": "00:05–00:12"}
    record = {**VIDEO_RECORD, "models": models}
    prompt = _render(_citing(sample_plan_entry, ["V-004"]), sample_learner_state, {"V-004": record})
    line = next(line for line in _cited_block(prompt).splitlines() if line.startswith("- Models (structured): "))
    assert json.loads(line.removeprefix("- Models (structured): ")) == models
    assert "Never infer a model from `use` or a primer quotation" in prompt


def test_video_without_models_is_an_explicit_prompt_gap(sample_plan_entry, sample_learner_state):
    prompt = _render(_citing(sample_plan_entry, ["V-004"]), sample_learner_state, {"V-004": VIDEO_RECORD})
    assert "- Models: undeclared (listening_model_undeclared)" in _cited_block(prompt)


def test_lesson_numbers_in_cited_source_prose_are_not_curriculum_references(sample_plan_entry, sample_learner_state):
    """The cited block's `supports` names ULP lesson 5 and a video's `use` names lesson 1; neither is flagged,
    while the same reference anywhere outside the block still is."""
    plan = _citing(sample_plan_entry, ALL_KINDS)
    prompt = _render(plan, sample_learner_state, ALL_KINDS)
    assert "ULP Season 1 lesson 5" in _cited_block(prompt)
    assert _check(prompt, plan, sample_learner_state).errors == []

    outside = prompt.replace("First phonetics step.", "First phonetics step, as in ULP Season 1 lesson 5.")
    assert any(
        e.startswith("unauthorized_lesson_number: lesson number 5")
        for e in _check(outside, plan, sample_learner_state).errors
    )
    after_block = prompt.replace(CITED_RECORDS_END, CITED_RECORDS_END + "\nSee lesson 7.")
    assert any("lesson number 7" in e for e in _check(after_block, plan, sample_learner_state).errors)

    no_markers = prompt.replace(CITED_RECORDS_BEGIN, "")
    errors = _check(no_markers, plan, sample_learner_state).errors
    assert any(e.startswith("missing_cited_records_marker") for e in errors)
    assert any("lesson number 5" in e for e in errors)


def test_lesson_numbers_the_plan_entry_states_are_its_own_input(sample_plan_entry, sample_learner_state):
    """A plan that cites "ULP S1 lesson 10" or models an activity on "lesson 2 a5" (A1 position 1 does both)
    renders; a lesson number the plan entry does not state still fails."""
    plan = _citing(
        sample_plan_entry,
        ALL_KINDS,
        rationale="ULP S1 lesson 10 supplies the review shape.",
        activities=[{**sample_plan_entry["activities"][0], "focus": "Modeled on the choice of lesson 2 a5."}],
    )
    prompt = _render(plan, sample_learner_state, ALL_KINDS)
    assert "ULP S1 lesson 10" in prompt and "lesson 2 a5" in prompt
    assert _check(prompt, plan, sample_learner_state).errors == []

    tampered = prompt.replace("the review shape.", "the review shape of lesson 4.")
    assert any("lesson number 4" in e for e in _check(tampered, plan, sample_learner_state).errors)


def test_record_id_scan_matches_only_schema_id_shapes(sample_plan_entry, sample_learner_state):
    assert RECORD_ID_RE.findall("Latin P-looking shape; watch?v=W-1rCu0indE; T-4, G-a1-001, EX-12x, W-11.") == [
        "T-4",
        "G-a1-001",
        "W-11",
    ]
    plan = _citing(sample_plan_entry, ALL_KINDS, rationale="Override the Latin P-looking shape.")
    prompt = _render(plan, sample_learner_state, ALL_KINDS)
    assert _check(prompt, plan, sample_learner_state).errors == []


def _schema_id_prefixes():
    """Every id prefix of the pack schema's ``<kind>_record`` definitions, plus the word store's ``W``."""
    defs = json.loads(EVIDENCE_PACK_SCHEMA.read_text(encoding="utf-8"))["$defs"]
    pack = {
        spec["properties"]["id"]["pattern"].removeprefix("^").split("-", 1)[0]
        for n, spec in defs.items()
        if n.endswith("_record")
    }
    return sorted({*pack, "W"})


@pytest.mark.parametrize("prefix", _schema_id_prefixes())
def test_uncited_record_id_of_every_schema_kind_fails_the_check(sample_plan_entry, sample_learner_state, prefix):
    """An uncited ``<prefix>-999`` fails for every record kind the pack schema defines; the plan's cited record
    of that kind in the same place passes."""
    plan = _citing(sample_plan_entry, ALL_KINDS)
    prompt = _render(plan, sample_learner_state, ALL_KINDS)
    assert "First phonetics step." in prompt

    uncited = prompt.replace("First phonetics step.", f"First phonetics step, see {prefix}-999.")
    errors = _check(uncited, plan, sample_learner_state).errors
    assert any(e.startswith(f"uncited_record_id: record '{prefix}-999'") for e in errors), errors

    (cited_id,) = [rid for rid in ALL_KINDS if rid.split("-", 1)[0] == prefix]
    cited = prompt.replace("First phonetics step.", f"First phonetics step, see {cited_id}.")
    assert _check(cited, plan, sample_learner_state).errors == []


def test_lesson_without_consolidation_renders(sample_plan_entry, sample_learner_state):
    """A lesson plan entry may omit `consolidation` (module-plan-v2 does not require it for any lesson kind)."""
    plan = {k: v for k, v in _citing(sample_plan_entry, ALL_KINDS).items() if k != "consolidation"}
    prompt = _render(plan, sample_learner_state, ALL_KINDS)
    assert "### Consolidation" not in prompt
    assert _check(prompt, plan, sample_learner_state).errors == []


def test_lesson_with_consolidation_lists_its_activities(sample_plan_entry, sample_learner_state):
    plan = _citing(sample_plan_entry, ALL_KINDS)
    prompt = _render(plan, sample_learner_state, ALL_KINDS)
    assert "### Consolidation\n- activities: a1\n" in prompt


def test_recap_without_consolidation_renders(sample_plan_entry, sample_learner_state):
    """A recap plan entry may omit `consolidation` (module-plan-v2 does not require it; A1 position 1 lesson 6)."""
    plan = {k: v for k, v in _citing(sample_plan_entry, ALL_KINDS, kind="recap").items() if k != "consolidation"}
    prompt = _render(plan, sample_learner_state, ALL_KINDS, recap=True)
    assert "### Consolidation" not in prompt
    assert _check(prompt, plan, sample_learner_state, recap=True).errors == []


@pytest.mark.parametrize("recap", [False, True])
def test_legacy_activity_prompt_bytes_unchanged(sample_plan_entry, sample_learner_state, sample_cited_records, recap):
    """Fixed inputs pin the pre-#9541 activity format without pinning evolving plan/pack bytes."""
    sample_plan_entry["activities"] = [
        {"id": "a1", "type": "quiz", "placement": "inline", "focus": "Identify letter"},
        {
            "id": "a2",
            "type": "error-correction",
            "placement": "workbook",
            "focus": "Repair spelling",
            "error_refs": ["E-001", "E-002"],
            "model": "X-004",
        },
        {"id": "a3", "type": "quiz", "placement": "inline", "focus": "Choose letter", "error_refs": [], "model": ""},
    ]
    prompt = _render(sample_plan_entry, sample_learner_state, sample_cited_records, recap=recap)
    expected = (
        "\n\n- `a1`: type: `quiz`, placement: `inline`, focus: Identify letter\n\n"
        "- `a2`: type: `error-correction`, placement: `workbook`, focus: Repair spelling, "
        "error_refs: E-001, E-002, model: X-004\n\n"
        "- `a3`: type: `quiz`, placement: `inline`, focus: Choose letter\n\n\n"
    )
    activity_block = prompt.split("### Activities", 1)[1].split("### Inventory", 1)[0]
    assert activity_block.encode("utf-8") == expected.encode("utf-8")
    for field in ("targets", "options", "learner_reads"):
        assert f"Binding {field}:" not in prompt


@pytest.mark.parametrize("recap", [False, True])
def test_structured_activity_constraints_render_even_when_empty(
    sample_plan_entry, sample_learner_state, sample_cited_records, recap
):
    from scripts.build.fresh.prompt import extract_plan_citations

    activity = sample_plan_entry["activities"][0]
    activity.update(targets=[], options=[], learner_reads=[])
    common = dict(
        plan_entry=sample_plan_entry,
        cited_records=sample_cited_records,
        learner_state=sample_learner_state,
        word_store=SAMPLE_WORD_STORE,
        immersion=compute_immersion_payload("a1", arc_position=1, lesson_n=1, cumulative_core_count=0),
        level="a1",
        slug="sounds-intro",
        lesson_n=1,
    )
    prompt = render_recap_prompt(built_lessons=[], **common) if recap else render_lesson_prompt(**common)
    for field in ("targets", "options", "learner_reads"):
        assert f"Binding {field}: []" in prompt
    activity.update(
        targets=["W-123"],
        options=["мама", "п'ять"],
        learner_reads=["T-123", {"ref": "X-123", "words": ["добрий день"]}],
    )
    assert {"W-123", "T-123", "X-123"} <= extract_plan_citations(sample_plan_entry)
    prompt = render_recap_prompt(built_lessons=[], **common) if recap else render_lesson_prompt(**common)
    assert 'Binding targets: ["W-123"]' in prompt
    assert "Binding options:" in prompt and "exact case" in prompt
    assert 'Binding options: ["мама", "п\'ять"]' in prompt
    assert '"words": ["добрий день"]' in prompt
    assert "\\u" not in prompt.split("Binding options:", 1)[1].split("\n", 1)[0]
    assert "Binding learner_reads:" in prompt and "T-123" in prompt and "X-123" in prompt


def test_structured_citations_reach_the_writer_record_loader():
    from scripts.build.fresh.cli import _load_cited_records

    target = {"id": "W-123", "lemma": "fixture"}
    quote = {"id": "T-123", "quote": "fixture"}
    exercise = {"id": "X-123", "items_sample": ["fixture"]}
    entry = {"activities": [{"targets": ["W-123"], "learner_reads": ["T-123", {"ref": "X-123", "words": []}]}]}
    assert _load_cited_records(entry, {"texts": [quote], "exercises": [exercise]}, {"words": [target]}) == {
        "W-123": target,
        "T-123": quote,
        "X-123": exercise,
    }


def test_structured_citation_discovery_preserves_existing_sources_and_ignores_prose():
    from scripts.build.fresh.prompt import extract_plan_citations

    entry = {
        "steps": [{"explains": ["T-1"], "evidence": ["EX-1"], "ref": "T-2", "paradigm": {"id": "P-1", "word": "W-1"}}],
        "activities": [
            {
                "error_refs": ["E-1"],
                "targets": ["W-2"],
                "options": ["W-999 text"],
                "learner_reads": ["T-3", {"ref": "X-1", "words": ["W-998"]}],
                "model": "X-2",
                "focus": "W-997",
            }
        ],
        "dialogue": {"evidence": ["T-4"], "speakers": [{"evidence": "W-3"}], "places": [{"evidence": "W-4"}]},
        "inventory": {
            "vocabulary": {"core": [{"evidence": "W-5"}], "incidental": [{"evidence": "W-6"}], "recycled": ["W-7"]},
            "grammar": [{"id": "G-a1-001"}],
        },
        "videos": [{"evidence": "V-1"}],
    }
    assert extract_plan_citations(entry) == {
        "T-1",
        "EX-1",
        "T-2",
        "P-1",
        "W-1",
        "E-1",
        "W-2",
        "T-3",
        "X-1",
        "X-2",
        "T-4",
        "W-3",
        "W-4",
        "W-5",
        "W-6",
        "W-7",
        "G-a1-001",
        "V-1",
    }
