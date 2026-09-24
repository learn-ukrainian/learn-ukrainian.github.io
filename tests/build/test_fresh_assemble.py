from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

import jsonschema
import pytest
import yaml

from scripts.build.fresh.assemble import (
    ACTIVITY_NOT_FOUND,
    DRAFT_STATUS_NOT_OK,
    PRIOR_PLANS_MISSING,
    AssemblerError,
    _render_urok_markdown,
    apply_stress,
    apply_stress_to_activities,
    assemble_expanded_document,
    assemble_lesson,
    build_resursy_tab,
    build_slovnyk_tab,
    check_5_assembly,
    check_9_stress_and_render,
    get_expanded_validator,
)
from scripts.build.fresh.draft_schema import draft_validator
from scripts.curriculum.evidence import lesson_lock
from scripts.curriculum.learner_state.immersion import compute_lesson_immersion_band

pytestmark = pytest.mark.reads_content

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPANDED_SCHEMA_PATH = REPO_ROOT / "schemas" / "lesson-expanded-v1.schema.json"
PACK_SCHEMA_PATH = REPO_ROOT / "schemas" / "evidence-pack-v1.schema.json"
WORDS_SCHEMA_PATH = REPO_ROOT / "schemas" / "evidence-words-v1.schema.json"
PLAN_SCHEMA_PATH = REPO_ROOT / "schemas" / "module-plan-v2.schema.json"

_PACK_VALIDATOR = jsonschema.Draft202012Validator(json.loads(PACK_SCHEMA_PATH.read_text(encoding="utf-8")))
_WORDS_VALIDATOR = jsonschema.Draft202012Validator(json.loads(WORDS_SCHEMA_PATH.read_text(encoding="utf-8")))
_PLAN_VALIDATOR = jsonschema.Draft202012Validator(json.loads(PLAN_SCHEMA_PATH.read_text(encoding="utf-8")))
_EXPANDED_VALIDATOR = jsonschema.Draft202012Validator(json.loads(EXPANDED_SCHEMA_PATH.read_text(encoding="utf-8")))


def validate_fixture_pack(pack: dict[str, Any]) -> None:
    _PACK_VALIDATOR.validate(pack)


def validate_fixture_words(words_store: dict[str, Any]) -> None:
    _WORDS_VALIDATOR.validate(words_store)


def validate_fixture_plan(plan: dict[str, Any]) -> None:
    _PLAN_VALIDATOR.validate(plan)


def validate_fixture_draft(draft: dict[str, Any], level: str = "a1") -> None:
    validator = draft_validator(level)
    validator.validate(draft)


# --- Canonical Schema-Valid Fixture Builders ---


def make_pack(
    *,
    texts: list[dict[str, Any]] | None = None,
    examples: list[dict[str, Any]] | None = None,
    videos: list[dict[str, Any]] | None = None,
    module: str = "a1/sample-slug",
) -> dict[str, Any]:
    pack = {
        "evidence_schema": 1,
        "module": module,
        "built_with": {
            "mcp_commit": "0" * 40,
            "sources_db": "0" * 64,
            "vesum": "0" * 64,
            "trie": "0" * 64,
            "ulif_forms": "0" * 64,
            "standard_sha256": "0" * 64,
        },
        "texts": texts or [],
        "exercises": [],
        "examples": examples or [],
        "errors": [],
        "notes": [],
        "videos": videos or [],
        "standard": [],
        "unsupported": [],
    }
    validate_fixture_pack(pack)
    return pack


def make_text_record(
    number: int,
    quote: str,
    *,
    author: str = "Shevchenko",
    work: str = "Kobzar",
    year: int = 1840,
    page: int = 10,
) -> dict[str, Any]:
    return {
        "id": f"T-{number}",
        "source": {
            "kind": "textbook",
            "file": "tb.txt",
            "grade": 1,
            "author": author,
            "section_id": 1,
            "page": page,
            "chunk_id": number,
        },
        "quote": quote,
        "sha256": "0" * 64,
        "supports": "concept",
    }


def make_example_record(
    number: int,
    text: str,
    translation_en: str,
    *,
    words: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": f"EX-{number}",
        "source": {
            "kind": "textbook",
            "file": "tb.txt",
            "grade": 1,
            "author": "Author",
            "section_id": 1,
            "page": 1,
            "chunk_id": number,
        },
        "text": text,
        "translation_en": translation_en,
        "sha256": "0" * 64,
        "sentence_ref": {"words": words or ["W-1"]},
    }


def make_video_record(
    number: int,
    url: str,
    channel: str,
    use: str = "Watch the video",
) -> dict[str, Any]:
    return {
        "id": f"V-{number}",
        "url": url,
        "channel": channel,
        "use": use,
        "checked": None,
    }


def make_words_store(
    *,
    words: list[dict[str, Any]] | None = None,
    level: str = "a1",
) -> dict[str, Any]:
    ws = {
        "evidence_schema": 1,
        "level": level,
        "built_with": {
            "mcp_commit": "0" * 40,
            "sources_db": "0" * 64,
            "vesum": "0" * 64,
            "trie": "0" * 64,
            "ulif_forms": "0" * 64,
            "russian_patterns": "0" * 64,
            "built_at": "2026-01-01T00:00:00Z",
        },
        "words": words or [],
    }
    validate_fixture_words(ws)
    return ws


def make_word_record(
    number: int,
    lemma: str,
    pos: str = "noun",
    *,
    forms: list[dict[str, Any]] | None = None,
    gloss_en: str | None = None,
    sense_gloss: str | None = None,
) -> dict[str, Any]:
    rec: dict[str, Any] = {
        "id": f"W-{number}",
        "lemma": lemma,
        "pos": pos,
        "entry": {"source": "vesum", "entry_id": 900000 + number},
        "ulif": "pending",
        "forms": forms
        or [
            {
                "form": lemma,
                "tags": f"{pos}:inanim:m:v_naz",
                "stress_source": "ulif",
                "markers": [],
                "learner": True,
                "stressed": lemma,
            }
        ],
    }
    if gloss_en is not None:
        rec["gloss_en"] = gloss_en
        rec["gloss_source"] = {"table": "dmklinger_uk_en", "id": number}
    if sense_gloss is not None:
        rec["sense_gloss"] = sense_gloss
    return rec


def make_plan_lesson(
    n: int,
    steps: list[dict[str, Any]],
    *,
    core_words: list[dict[str, Any]] | None = None,
    incidental_words: list[dict[str, Any]] | None = None,
    videos: list[dict[str, Any]] | None = None,
    activities: list[dict[str, Any]] | None = None,
    job: str = "Greet people",
    rationale: str = "Introductory lesson",
) -> dict[str, Any]:
    core = []
    for w in core_words or []:
        tags = [f["tags"] for f in w.get("forms", [])]
        core.append({"lemma": w["lemma"], "evidence": w["id"], "forms": tags})
    incidental = []
    for w in incidental_words or []:
        incidental.append({"lemma": w["lemma"], "evidence": w["id"]})

    return {
        "n": n,
        "slug": f"lesson-{n}",
        "title": f"Lesson {n}",
        "kind": "teach",
        "job": job,
        "rationale": rationale,
        "word_target": 10,
        "inventory": {
            "vocabulary": {
                "core": core,
                "incidental": incidental,
                "recycled": [],
            }
        },
        "steps": steps,
        "activities": activities or [],
        "videos": videos or [],
    }


def make_plan(
    *,
    lessons: list[dict[str, Any]] | None = None,
    module: str = "sample-slug",
    level: str = "a1",
    arc_position: int = 1,
) -> dict[str, Any]:
    plan = {
        "plan_schema": 2,
        "module": module,
        "level": level,
        "sequence": 1,
        "slug": module,
        "version": 1,
        "title": "Sample Title",
        "arc_ref": {"level": level, "position": arc_position},
        "evidence_ref": {"path": f"curriculum/l2-uk-en/evidence/{level}/{module}.yaml", "sha256": "0" * 64},
        "lessons": lessons or [],
    }
    validate_fixture_plan(plan)
    return plan


def make_draft(
    *,
    steps: list[dict[str, Any]] | None = None,
    activities: list[dict[str, Any]] | None = None,
    consolidation: dict[str, Any] | None = None,
    dialogue: dict[str, Any] | None = None,
    module: str = "a1/sample-slug",
    n: int = 1,
    lesson_lock_entry_sha256: str = "0" * 64,
    status: str = "ok",
    gaps: list[dict[str, Any]] | None = None,
    validate: bool = True,
) -> dict[str, Any]:
    draft: dict[str, Any] = {
        "draft_schema": 1,
        "lesson": {"module": module, "n": n},
        "inputs": {
            "plan_sha256": "0" * 64,
            "pack_lock": "0" * 64,
            "words_lock": "0" * 64,
            "lesson_lock_entry_sha256": lesson_lock_entry_sha256,
            "learner_state_sha256": "0" * 64,
            "style_card_sha256": "0" * 64,
        },
        "status": status,
        "steps": steps or [],
        "consolidation": consolidation or {"activities": []},
        "activities": activities or [],
        "gaps": gaps or [],
    }
    if dialogue is not None:
        draft["dialogue"] = dialogue
    if validate:
        validate_fixture_draft(draft)
    return draft


# --- Tests ---


def test_no_cyrillic_string_literals_in_assembler():
    """Nothing typed: assert that scripts/build/fresh/assemble.py has NO Cyrillic string literals."""
    assemble_file = REPO_ROOT / "scripts" / "build" / "fresh" / "assemble.py"
    source = assemble_file.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(assemble_file))

    cyrillic_pattern = re.compile(r"[\u0400-\u04FF]")
    found_literals: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and cyrillic_pattern.search(node.value):
            found_literals.append((getattr(node, "lineno", 0), node.value))

    assert len(found_literals) == 0, f"Found Cyrillic string literals in assemble.py: {found_literals}"


def test_r11_forbidden_paths_in_assemble():
    """R-11: assemble.py never opens or references legacy v1 paths or plans dir."""
    assemble_file = REPO_ROOT / "scripts" / "build" / "fresh" / "assemble.py"
    content = assemble_file.read_text(encoding="utf-8")

    forbidden = [
        "curriculum/l2-uk-en/plans/",
        "curriculum/l2-uk-en/a1-v1/",
        "curriculum/l2-uk-en/a2-v1/",
        "curriculum/l2-uk-en/b1-v1/",
        "curriculum/l2-uk-en/b2-v1/",
        "curriculum/l2-uk-en/<level>-v1/",
        "/plans/",
        "'plans'",
        '"plans"',
    ]
    for term in forbidden:
        assert term not in content, f"Forbidden term {term!r} found in assemble.py"


def test_expanded_document_schema_valid():
    """Validate a properly-formed expanded document against schemas/lesson-expanded-v1.schema.json."""
    assert EXPANDED_SCHEMA_PATH.is_file()
    sample_doc = {
        "expanded_schema": 1,
        "lesson": {"level": "a1", "slug": "test-slug", "n": 1},
        "units": [
            {
                "tab": "urok",
                "step": "s1",
                "activity": None,
                "item": None,
                "block": 0,
                "role": "narration",
                "text": "Hello world and plain Ukrainian text without accents",
            },
            {
                "tab": "vpravy",
                "step": "s1",
                "activity": "a1",
                "item": 0,
                "block": "instruction",
                "role": "instruction",
                "text": "Choose the correct answer",
            },
            {
                "tab": "slovnyk",
                "step": None,
                "activity": None,
                "item": None,
                "block": "core_W1",
                "role": "record_print",
                "text": "Plain lemma",
            },
        ],
    }

    errors = list(_EXPANDED_VALIDATOR.iter_errors(sample_doc))
    assert len(errors) == 0


def test_combining_accent_fails_expanded_schema_and_check_5():
    """A combining accent in the expanded document is a bug that fails schema validation and check 5."""
    doc_with_accent = {
        "expanded_schema": 1,
        "lesson": {"level": "a1", "slug": "test-slug", "n": 1},
        "units": [
            {
                "tab": "urok",
                "step": "s1",
                "activity": None,
                "item": None,
                "block": 0,
                "role": "narration",
                "text": "Украї\u0301на",  # combining acute
            }
        ],
    }

    errors = list(_EXPANDED_VALIDATOR.iter_errors(doc_with_accent))
    assert len(errors) > 0

    w1 = make_word_record(1, "слово")
    step = {
        "id": "s1",
        "kind": "teach",
        "teach": "Intro",
        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-1"]},
        "uses": {"grammar": [], "vocabulary": []},
        "evidence": [],
        "practice": [],
    }
    plan = make_plan(
        module="test-slug",
        lessons=[make_plan_lesson(1, [step], core_words=[w1])],
    )
    draft_step = {
        "id": "s1",
        "blocks": [{"kind": "prose", "text": "Украї\u0301на with accent", "explains": ["W-1"]}],
    }
    draft = {
        "draft_schema": 1,
        "lesson": {"module": "a1/test-slug", "n": 1},
        "inputs": {
            "plan_sha256": "0" * 64,
            "pack_lock": "0" * 64,
            "words_lock": "0" * 64,
            "lesson_lock_entry_sha256": "0" * 64,
            "learner_state_sha256": "0" * 64,
            "style_card_sha256": "0" * 64,
        },
        "status": "ok",
        "steps": [draft_step],
        "consolidation": {"activities": []},
        "activities": [],
        "gaps": [],
    }
    pack = make_pack(module="a1/test-slug")
    words_store = make_words_store(words=[w1])

    res = check_5_assembly(draft, plan, pack, words_store, "a1", "test-slug", 1)
    assert res.passed is False
    assert "combining accent" in (res.reason or "") or "schema validation" in (res.reason or "")


def test_step_ids_on_units_in_expanded_document():
    """Every unit carries step (the plan step id, or null for tabs/blocks without steps)."""
    w1 = make_word_record(1, "слово", gloss_en="word")
    w2 = make_word_record(2, "мова", gloss_en="language")
    words_store = make_words_store(words=[w1, w2])

    t1 = make_text_record(1, "Цитата")
    ex1 = make_example_record(1, "Приклад", "Example", words=["W-1"])
    v1 = make_video_record(1, "https://youtube.com/watch?v=123", "LearnUA", use="Alphabet song")
    pack = make_pack(texts=[t1], examples=[ex1], videos=[v1])

    plan_steps = [
        {
            "id": "s1",
            "kind": "teach",
            "teach": "Intro",
            "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-1"]},
            "uses": {"grammar": [], "vocabulary": []},
            "evidence": ["T-1", "EX-1", "V-1"],
            "practice": ["a1"],
        },
        {
            "id": "s2",
            "kind": "teach",
            "teach": "Exchange",
            "introduces": {"letters": [], "grammar": [], "vocabulary": []},
            "uses": {"grammar": [], "vocabulary": ["W-1"]},
            "evidence": [],
            "practice": [],
        },
    ]
    plan_videos = [{"evidence": "V-1", "use": "Watch the alphabet song"}]
    plan_activities = [{"id": "a1", "type": "quiz", "placement": "inline", "focus": "Quiz"}]
    lesson = make_plan_lesson(
        1,
        plan_steps,
        core_words=[w1],
        incidental_words=[w2],
        videos=plan_videos,
        activities=plan_activities,
    )
    plan = make_plan(lessons=[lesson])

    draft_steps = [
        {
            "id": "s1",
            "lead_in": "Welcome",
            "blocks": [
                {"kind": "prose", "text": "First explanation", "explains": ["W-1"]},
                {"kind": "example", "ref": "EX-1"},
                {"kind": "quote", "ref": "T-1"},
                {"kind": "video", "ref": "V-1"},
            ],
        },
        {
            "id": "s2",
            "blocks": [
                {"kind": "prose", "text": "Second explanation", "explains": ["W-1"]},
                {"kind": "dialogue"},
            ],
        },
    ]
    draft_dialogue = {
        "lines": [{"speaker": "SpeakerA", "text": "Привіт"}],
        "translation_en": ["Hello"],
    }
    draft_activities = [
        {
            "id": "a1",
            "instruction": "Answer question",
            "items": [
                {
                    "question": "Question 1",
                    "options": ["Opt 1", "Opt 2"],
                    "correct": 0,
                    "explanation": "Opt 1 explanation",
                }
            ],
        }
    ]
    draft = make_draft(
        steps=draft_steps,
        activities=draft_activities,
        dialogue=draft_dialogue,
    )

    exp_doc, _prov_doc = assemble_expanded_document(draft, plan, pack, words_store, "a1", "sample-slug", 1)

    assert exp_doc["expanded_schema"] == 1
    units = exp_doc["units"]
    assert len(units) > 0

    # Step propagation: s1 units carry step="s1"
    s1_units = [u for u in units if u.get("step") == "s1"]
    assert len(s1_units) >= 4  # lead_in, prose, example, quote, video

    # Step propagation: s2 units carry step="s2"
    s2_units = [u for u in units if u.get("step") == "s2"]
    assert len(s2_units) >= 2  # prose, dialogue line

    # Slovnyk and Resursy units have step = None
    slovnyk_units = [u for u in units if u.get("tab") == "slovnyk"]
    assert len(slovnyk_units) >= 2
    for u in slovnyk_units:
        assert u.get("step") is None

    # Activity unit associated with step s1
    act_units = [u for u in units if u.get("activity") == "a1"]
    assert len(act_units) >= 1
    for u in act_units:
        assert u.get("step") == "s1"

    errors = list(get_expanded_validator().iter_errors(exp_doc))
    assert len(errors) == 0


def test_build_slovnyk_and_resursy_tabs(monkeypatch):
    """Verify build_slovnyk_tab and build_resursy_tab structure and content."""
    monkeypatch.setattr("scripts.build.fresh.assemble.atlas_href_for", lambda lemma: f"/lexicon/{lemma}/")
    w1_forms = [
        {
            "form": "добрий",
            "tags": "adj:m:v_naz",
            "stress_source": "ulif",
            "markers": [],
            "learner": True,
            "stressed": "до́брий",
        },
        {
            "form": "доброго",
            "tags": "adj:m:v_rod",
            "stress_source": "ulif",
            "markers": [],
            "learner": True,
            "stressed": "до́брого",
        },
    ]
    w1 = make_word_record(1, "добрий", pos="adj", forms=w1_forms, gloss_en="good")

    w2_forms = [
        {
            "form": "день",
            "tags": "noun:inanim:m:v_naz",
            "stress_source": "ulif",
            "markers": [],
            "learner": True,
            "stressed": "де́нь",
        }
    ]
    w2 = make_word_record(2, "день", pos="noun", forms=w2_forms, sense_gloss="day")
    words_store = make_words_store(words=[w1, w2])

    t1 = make_text_record(1, "Цитата підручника", author="Shevchenko", work="Kobzar", year=1840, page=10)
    t_uncited = make_text_record(2, "Нецитована цитата")
    v1 = make_video_record(1, "https://youtube.com/watch?v=123", "LearnUA", use="Default use")
    v_uncited = make_video_record(2, "https://youtube.com/watch?v=999", "OtherUA")
    pack = make_pack(texts=[t1, t_uncited], videos=[v1, v_uncited])

    steps = [
        {
            "id": "s1",
            "kind": "teach",
            "teach": "Teach greetings",
            "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-1"]},
            "uses": {"grammar": [], "vocabulary": []},
            "evidence": ["T-1"],
            "practice": [],
        }
    ]
    videos = [{"evidence": "V-1", "use": "Watch the alphabet song"}]
    lesson_plan = make_plan_lesson(1, steps, core_words=[w1], incidental_words=[w2], videos=videos)

    slovnyk = build_slovnyk_tab(lesson_plan, words_store)
    assert len(slovnyk) == 2
    assert slovnyk[0]["lemma"] == "до́брий"
    assert slovnyk[0]["translation"] == "good"
    assert slovnyk[0]["pos"] == "adj"
    assert "atlas_href" in slovnyk[0]
    assert slovnyk[0]["forms"] == ["до́брий", "до́брого"]

    assert slovnyk[1]["lemma"] == "де́нь"
    assert slovnyk[1]["translation"] == "day"
    assert slovnyk[1]["pos"] == "noun"

    resursy = build_resursy_tab(lesson_plan, pack)
    assert "books" in resursy
    assert len(resursy["books"]) == 1
    assert resursy["books"][0]["source"] == "T-1"

    assert "youtube" in resursy
    assert len(resursy["youtube"]) == 1
    assert resursy["youtube"][0]["channel"] == "LearnUA"
    assert resursy["youtube"][0]["description"] == "Watch the alphabet song"


def test_whole_sentence_rendered_with_inline_markup():
    """Blocker 2: Reassemble all spans in order; 'Say {{uk:x}} when you greet a friend.' renders in full."""
    w1 = make_word_record(1, "привіт", gloss_en="hello")
    words_store = make_words_store(words=[w1])
    pack = make_pack()

    step = {
        "id": "s1",
        "kind": "teach",
        "teach": "Greetings",
        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-1"]},
        "uses": {"grammar": [], "vocabulary": []},
        "evidence": [],
        "practice": [],
    }
    plan = make_plan(lessons=[make_plan_lesson(1, [step], core_words=[w1])])

    # Draft has a sentence with inline {{uk:...}} markup, plus a table and bilingual row
    draft_step = {
        "id": "s1",
        "blocks": [
            {
                "kind": "prose",
                "text": "Say {{uk:привіт}} when you greet a friend.",
                "explains": ["W-1"],
            },
            {
                "kind": "table",
                "rows": [["Header", "Column"], ["{{uk:привіт}}", "Greeting"]],
                "explains": ["W-1"],
            },
            {
                "kind": "bilingual",
                "uk": ["{{uk:привіт}}"],
                "en": ["hello"],
            },
        ],
    }
    draft = make_draft(steps=[draft_step])

    exp_doc, _ = assemble_expanded_document(draft, plan, pack, words_store, "a1", "sample-slug", 1)

    # Unit 0 is prose span 0: 'Say '
    # Unit 1 is prose span 1: 'привіт'
    # Unit 2 is prose span 2: ' when you greet a friend.'
    prose_units = [u for u in exp_doc["units"] if u.get("tab") == "urok" and u.get("block") == 0]
    assert len(prose_units) == 3
    assert prose_units[0]["text"] == "Say "
    assert prose_units[1]["text"] == "привіт"
    assert prose_units[2]["text"] == " when you greet a friend."

    # Synthetic stream resolving Unit 1 to stressed 'приві́т'
    mock_stream = type(
        "MockStream",
        (),
        {
            "tokens": [
                {
                    "unit_index": 1,
                    "offset": 0,
                    "token": "привіт",
                    "class": "resolved",
                    "selected": {"stressed": "приві́т", "record": "W-1"},
                }
            ],
            "failures": [],
        },
    )()

    stressed_doc = apply_stress(exp_doc, mock_stream)
    urok_md, rendered_by_unit = _render_urok_markdown(draft, stressed_doc, pack, words_store)

    # Assert whole sentence is rendered, NOT truncated to ' when you greet a friend.'
    assert "Say приві́т when you greet a friend." in urok_md
    # The renderer reports its unit->output mapping: one rendered piece per consumed unit
    assert [rendered_by_unit[i] for i in range(3)] == ["Say ", "приві́т", " when you greet a friend."]

    # Assert table rendered with {{uk:...}} stripped
    assert "| Header | Column |" in urok_md
    assert "| привіт | Greeting |" in urok_md

    # Assert bilingual row rendered with {{uk:...}} stripped and no typed English chrome
    assert "| привіт | hello |" in urok_md
    assert "| --- | --- |" in urok_md


def test_activities_stress_applied_from_stream():
    """Blocker 2: Activities (Вправи) receive stress applied from resolver stream."""
    w1 = make_word_record(1, "слово", gloss_en="word")
    words_store = make_words_store(words=[w1])
    pack = make_pack()

    step = {
        "id": "s1",
        "kind": "teach",
        "teach": "Teach",
        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-1"]},
        "uses": {"grammar": [], "vocabulary": []},
        "evidence": [],
        "practice": ["a1"],
    }
    plan_activities = [{"id": "a1", "type": "quiz", "placement": "inline", "focus": "Quiz"}]
    plan = make_plan(lessons=[make_plan_lesson(1, [step], core_words=[w1], activities=plan_activities)])

    act_quiz = {
        "id": "a1",
        "instruction": "Say {{uk:слово}} please",
        "items": [
            {
                "question": "What is {{uk:слово}}?",
                "options": ["слово", "інше"],
                "correct": 0,
                "explanation": "Because {{gloss:W-1}} means word",
            }
        ],
    }
    draft = make_draft(
        steps=[{"id": "s1", "blocks": [{"kind": "prose", "text": "intro", "explains": ["W-1"]}]}],
        activities=[act_quiz],
    )

    exp_doc, _ = assemble_expanded_document(draft, plan, pack, words_store, "a1", "sample-slug", 1)

    # Find unit indices for activity instruction and question
    mock_tokens = []
    for idx, u in enumerate(exp_doc["units"]):
        if u.get("tab") == "vpravy" and u.get("text") == "слово":
            mock_tokens.append(
                {
                    "unit_index": idx,
                    "offset": 0,
                    "token": "слово",
                    "class": "resolved",
                    "selected": {"stressed": "сло́во", "record": "W-1"},
                }
            )

    mock_stream = type("MockStream", (), {"tokens": mock_tokens, "failures": []})()
    stressed_doc = apply_stress(exp_doc, mock_stream)

    def fake_replace_gloss(match: re.Match) -> str:
        return "word"

    stressed_acts, act_pieces = apply_stress_to_activities(draft["activities"], stressed_doc, fake_replace_gloss)
    assert "Say сло́во please" in stressed_acts[0]["instruction"]
    assert "What is сло́во?" in stressed_acts[0]["items"][0]["question"]
    assert "word" in stressed_acts[0]["items"][0]["explanation"]
    # Every vpravy unit of the quiz was consumed by the renderer, glosses replaced per unit
    vpravy_units = [i for i, u in enumerate(exp_doc["units"]) if u["tab"] == "vpravy"]
    assert sorted(act_pieces) == vpravy_units
    assert "word" in act_pieces[max(vpravy_units)]


def test_immersion_band_key_matches_function(monkeypatch):
    """Major 3: compute_lesson_immersion_band called with real signature, no bare except."""
    w1 = make_word_record(1, "слово", gloss_en="word")
    words_store = make_words_store(words=[w1])
    pack = make_pack()

    step = {
        "id": "s1",
        "kind": "teach",
        "teach": "Teach",
        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-1"]},
        "uses": {"grammar": [], "vocabulary": []},
        "evidence": [],
        "practice": [],
    }
    plan = make_plan(arc_position=3, lessons=[make_plan_lesson(1, [step], core_words=[w1])])
    draft = make_draft(
        steps=[{"id": "s1", "blocks": [{"kind": "prose", "text": "добрий день", "explains": ["W-1"]}]}],
        lesson_lock_entry_sha256="abc" * 21 + "a",
    )

    exp_doc, _ = assemble_expanded_document(draft, plan, pack, words_store, "a1", "sample-slug", 1)
    mock_stream = type("MockStream", (), {"tokens": [], "failures": []})()

    # Monkeypatch planned_state to return known count 25
    monkeypatch.setattr(
        "scripts.build.fresh.assemble.planned_state",
        lambda *args, **kwargs: type("State", (), {"cumulative_core_count": 25})(),
    )
    monkeypatch.setattr(lesson_lock, "check_lesson_lock", lambda *args, **kwargs: (True, ""))
    monkeypatch.setattr(
        lesson_lock,
        "compute_lesson_lock",
        lambda *args, **kwargs: {"lessons": [{"n": 1, "entry_sha256": "abc" * 21 + "a"}]},
    )

    expected_band = compute_lesson_immersion_band("a1", 3, 1, 25)

    res = check_9_stress_and_render(
        exp_doc,
        draft,
        plan,
        pack,
        words_store,
        mock_stream,
        "a1",
        "sample-slug",
        1,
    )
    assert res.passed is True
    assert res.artifacts["meta_data"]["immersion"] == expected_band.band_key

    # Assert failure fails assembly with a code (no bare except fallback)
    def boom(*args, **kwargs):
        raise RuntimeError("simulated immersion crash")

    monkeypatch.setattr("scripts.build.fresh.assemble.compute_lesson_immersion_band", boom)
    res_fail = check_9_stress_and_render(
        exp_doc,
        draft,
        plan,
        pack,
        words_store,
        mock_stream,
        "a1",
        "sample-slug",
        1,
    )
    assert res_fail.passed is False
    assert "immersion band computation failed" in (res_fail.reason or "")


def test_assemble_refuses_site_write_on_open_or_failed_stream(tmp_path, monkeypatch):
    """Major 4: assemble_lesson refuses to write into site/ on open tokens or failures."""
    w1 = make_word_record(1, "слово", gloss_en="word")
    words_store = make_words_store(words=[w1])
    pack = make_pack()

    step = {
        "id": "s1",
        "kind": "teach",
        "teach": "Teach",
        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-1"]},
        "uses": {"grammar": [], "vocabulary": []},
        "evidence": [],
        "practice": [],
    }
    plan = make_plan(lessons=[make_plan_lesson(1, [step], core_words=[w1])])
    draft = make_draft(
        steps=[{"id": "s1", "blocks": [{"kind": "prose", "text": "слово", "explains": ["W-1"]}]}],
        lesson_lock_entry_sha256="abc" * 21 + "a",
    )

    state_dir = tmp_path / "state"
    site_dir = tmp_path / "site"

    # 1. Stream with open token (stress_open) -> site write refused
    stream_with_open = type(
        "MockStream",
        (),
        {
            "tokens": [
                {
                    "unit_index": 0,
                    "offset": 0,
                    "token": "слово",
                    "class": "stress_open",
                    "selected": None,
                }
            ],
            "failures": [],
            "to_bytes": lambda self: b"mock",
        },
    )()

    monkeypatch.setattr("scripts.build.fresh.assemble.atlas_href_for", lambda lemma: f"/lexicon/{lemma}/")
    monkeypatch.setattr("scripts.build.fresh.assemble.resolve", lambda *args, **kwargs: stream_with_open)

    rep = assemble_lesson(
        "a1",
        "sample-slug",
        1,
        draft_dict=draft,
        plan_dict=plan,
        pack_dict=pack,
        words_dict=words_store,
        output_dir=state_dir,
        site_dir=site_dir,
    )
    assert rep["ok"] is False
    assert "blocking token" in rep.get("message", "")
    assert "слово" in rep.get("blocking_tokens", [])
    # State file written
    assert (state_dir / "lesson-1.stressed.yaml").is_file()
    # Site file NOT written
    assert not (site_dir / "1.mdx").exists()

    # 2. Clean stream -> site write succeeds
    stream_clean = type(
        "MockStream",
        (),
        {
            "tokens": [
                {
                    "unit_index": 0,
                    "offset": 0,
                    "token": "слово",
                    "class": "resolved",
                    "selected": {"stressed": "сло́во", "record": "W-1"},
                }
            ],
            "failures": [],
            "to_bytes": lambda self: b"mock",
        },
    )()

    monkeypatch.setattr("scripts.build.fresh.assemble.resolve", lambda *args, **kwargs: stream_clean)
    monkeypatch.setattr(
        "scripts.build.fresh.assemble.planned_state",
        lambda *args, **kwargs: type("State", (), {"cumulative_core_count": 10})(),
    )
    monkeypatch.setattr(lesson_lock, "check_lesson_lock", lambda *args, **kwargs: (True, ""))
    monkeypatch.setattr(
        lesson_lock,
        "compute_lesson_lock",
        lambda *args, **kwargs: {"lessons": [{"n": 1, "entry_sha256": "abc" * 21 + "a"}]},
    )
    monkeypatch.setattr(
        "scripts.build.fresh.assemble.check_11_render",
        lambda *args, **kwargs: type(
            "Check", (), {"passed": True, "to_dict": lambda s: {"check": 11, "passed": True}}
        )(),
    )

    rep_clean = assemble_lesson(
        "a1",
        "sample-slug",
        1,
        draft_dict=draft,
        plan_dict=plan,
        pack_dict=pack,
        words_dict=words_store,
        output_dir=state_dir,
        site_dir=site_dir,
    )
    assert rep_clean["ok"] is True
    # Site file written
    assert (site_dir / "1.mdx").is_file()


def test_slovnyk_selected_sense_and_forms_and_pending_stress(monkeypatch):
    """Major 5: Selected sense, taught forms, lemma stress from lemma form, pending prints no stress."""
    monkeypatch.setattr("scripts.build.fresh.assemble.atlas_href_for", lambda lemma: f"/lexicon/{lemma}/")
    # Word 1 has pending stress on lemma form
    w1_forms = [
        {
            "form": "день",
            "tags": "noun:inanim:m:v_naz",
            "stress_source": "pending",
            "markers": [],
            "learner": True,
        }
    ]
    w1 = make_word_record(1, "день", forms=w1_forms, gloss_en="day", sense_gloss="selected day")

    # Word 2 has learner form first with different stress, but lemma form has correct stress
    w2_forms = [
        {
            "form": "слово",
            "tags": "noun:inanim:n:v_naz",
            "stress_source": "ulif",
            "markers": [],
            "learner": False,
            "stressed": "сло́во",
        },
        {
            "form": "слова",
            "tags": "noun:inanim:n:v_rod",
            "stress_source": "ulif",
            "markers": [],
            "learner": True,
            "stressed": "слова́",
        },
    ]
    w2 = make_word_record(2, "слово", forms=w2_forms, gloss_en="word")
    words_store = make_words_store(words=[w1, w2])

    step = {
        "id": "s1",
        "kind": "teach",
        "teach": "Teach",
        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-1", "W-2"]},
        "uses": {"grammar": [], "vocabulary": []},
        "evidence": [],
        "practice": [],
    }
    lesson = make_plan_lesson(1, [step], core_words=[w1, w2])

    # Resolver stream selected record W-1 with specific sense
    stream = type(
        "MockStream",
        (),
        {
            "tokens": [
                {
                    "token": "день",
                    "class": "resolved",
                    "selected": {"record": "W-1", "stressed": None},
                }
            ]
        },
    )()

    slovnyk = build_slovnyk_tab(lesson, words_store, stream)
    assert len(slovnyk) == 2

    # W-1: stress_source: pending prints no stress (unstressed lemma 'день')
    assert slovnyk[0]["lemma"] == "день"
    assert slovnyk[0]["translation"] == "selected day"

    # W-2: lemma stress comes from lemma form ('сло́во'), not learner form ('слова́')
    assert slovnyk[1]["lemma"] == "сло́во"
    assert slovnyk[1]["translation"] == "word"


def test_check_9_lock_mismatch_and_missing_lock_fails(monkeypatch):
    """Major 6: check 9 compares against on-disk lock and draft entry; missing fails."""
    w1 = make_word_record(1, "слово", gloss_en="word")
    words_store = make_words_store(words=[w1])
    pack = make_pack()

    step = {
        "id": "s1",
        "kind": "teach",
        "teach": "Teach",
        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-1"]},
        "uses": {"grammar": [], "vocabulary": []},
        "evidence": [],
        "practice": [],
    }
    plan = make_plan(lessons=[make_plan_lesson(1, [step], core_words=[w1])])
    mock_stream = type("MockStream", (), {"tokens": [], "failures": []})()

    # Draft with missing lesson_lock_entry_sha256
    draft_missing = {
        "draft_schema": 1,
        "lesson": {"module": "a1/sample-slug", "n": 1},
        "inputs": {
            "plan_sha256": "0" * 64,
            "pack_lock": "0" * 64,
            "words_lock": "0" * 64,
            "learner_state_sha256": "0" * 64,
            "style_card_sha256": "0" * 64,
        },
        "status": "ok",
        "steps": [{"id": "s1", "blocks": [{"kind": "prose", "text": "слово", "explains": ["W-1"]}]}],
        "consolidation": {"activities": []},
        "activities": [],
        "gaps": [],
    }
    exp_doc, _ = assemble_expanded_document(draft_missing, plan, pack, words_store, "a1", "sample-slug", 1)

    monkeypatch.setattr(lesson_lock, "check_lesson_lock", lambda *args, **kwargs: (True, ""))
    monkeypatch.setattr(
        lesson_lock,
        "compute_lesson_lock",
        lambda *args, **kwargs: {"lessons": [{"n": 1, "entry_sha256": "1" * 64}]},
    )

    res = check_9_stress_and_render(
        exp_doc,
        draft_missing,
        plan,
        pack,
        words_store,
        mock_stream,
        "a1",
        "sample-slug",
        1,
    )
    assert res.passed is False
    assert "missing lesson_lock_entry_sha256" in (res.reason or "")

    # Draft with mismatched lock entry
    draft_mismatch = make_draft(
        steps=[{"id": "s1", "blocks": [{"kind": "prose", "text": "слово", "explains": ["W-1"]}]}],
        lesson_lock_entry_sha256="2" * 64,
    )
    res_mismatch = check_9_stress_and_render(
        exp_doc,
        draft_mismatch,
        plan,
        pack,
        words_store,
        mock_stream,
        "a1",
        "sample-slug",
        1,
    )
    assert res_mismatch.passed is False
    assert "draft lesson_lock_entry_sha256" in (res_mismatch.reason or "")

    # On-disk lock check fails
    monkeypatch.setattr(lesson_lock, "check_lesson_lock", lambda *args, **kwargs: (False, "diff error"))
    res_disk_fail = check_9_stress_and_render(
        exp_doc,
        draft_mismatch,
        plan,
        pack,
        words_store,
        mock_stream,
        "a1",
        "sample-slug",
        1,
    )
    assert res_disk_fail.passed is False
    assert "lessons.lock.yaml check failed" in (res_disk_fail.reason or "")


def test_missing_record_fails_closed_with_named_code():
    """Blocker 1: Missing record fails closed with named code, never empty unit."""
    w1 = make_word_record(1, "слово")
    words_store = make_words_store(words=[w1])
    pack = make_pack()

    step = {
        "id": "s1",
        "kind": "teach",
        "teach": "Teach",
        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-1"]},
        "uses": {"grammar": [], "vocabulary": []},
        "evidence": [],
        "practice": [],
    }
    plan = make_plan(lessons=[make_plan_lesson(1, [step], core_words=[w1])])

    # 1. Missing example
    draft_missing_ex = make_draft(steps=[{"id": "s1", "blocks": [{"kind": "example", "ref": "EX-99"}]}])
    with pytest.raises(AssemblerError) as exc:
        assemble_expanded_document(draft_missing_ex, plan, pack, words_store, "a1", "sample-slug", 1)
    assert exc.value.code == "example_not_found"

    # 2. Missing text quote
    draft_missing_text = make_draft(steps=[{"id": "s1", "blocks": [{"kind": "quote", "ref": "T-99"}]}])
    with pytest.raises(AssemblerError) as exc:
        assemble_expanded_document(draft_missing_text, plan, pack, words_store, "a1", "sample-slug", 1)
    assert exc.value.code == "text_not_found"

    # 3. Missing video
    draft_missing_video = make_draft(steps=[{"id": "s1", "blocks": [{"kind": "video", "ref": "V-99"}]}])
    with pytest.raises(AssemblerError) as exc:
        assemble_expanded_document(draft_missing_video, plan, pack, words_store, "a1", "sample-slug", 1)
    assert exc.value.code == "video_not_found"


def test_accented_record_stripped_in_expanded_doc():
    """Minor 13: An accented word record in vocabulary is stripped in the expanded doc."""
    # Lemma carrying combining acute accent
    w_accent = {
        "id": "W-1",
        "lemma": "сло́во",  # accented lemma
        "pos": "noun",
        "entry": {"source": "vesum", "entry_id": 101},
        "ulif": "pending",
        "forms": [
            {
                "form": "слово",
                "tags": "noun:inanim:n:v_naz",
                "stress_source": "ulif",
                "markers": [],
                "learner": True,
                "stressed": "сло́во",
            }
        ],
    }
    words_store = {
        "evidence_schema": 1,
        "level": "a1",
        "built_with": {
            "mcp_commit": "0" * 40,
            "sources_db": "0" * 64,
            "vesum": "0" * 64,
            "trie": "0" * 64,
            "ulif_forms": "0" * 64,
            "russian_patterns": "0" * 64,
            "built_at": "2026-01-01T00:00:00Z",
        },
        "words": [w_accent],
    }
    pack = make_pack()
    step = {
        "id": "s1",
        "kind": "teach",
        "teach": "Teach",
        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-1"]},
        "uses": {"grammar": [], "vocabulary": []},
        "evidence": [],
        "practice": [],
    }
    plan = make_plan(lessons=[make_plan_lesson(1, [step], core_words=[w_accent])])
    draft = make_draft(
        steps=[{"id": "s1", "blocks": [{"kind": "prose", "text": "intro", "explains": ["W-1"]}]}],
    )

    exp_doc, _ = assemble_expanded_document(draft, plan, pack, words_store, "a1", "sample-slug", 1)
    # The slovnyk unit for W-1 must have the accent stripped
    slovnyk_unit = next(u for u in exp_doc["units"] if u.get("tab") == "slovnyk")
    assert "\u0301" not in slovnyk_unit["text"]
    assert slovnyk_unit["text"] == "слово"


def test_output_page_path_and_navigation(tmp_path, monkeypatch):
    """Minor 11 & 12: Atomic write used, output page is <n>.mdx, navigation uses lesson order."""
    w1 = make_word_record(1, "слово")
    words_store = make_words_store(words=[w1])
    pack = make_pack()

    steps = [
        {
            "id": "s1",
            "kind": "teach",
            "teach": "Teach",
            "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-1"]},
            "uses": {"grammar": [], "vocabulary": []},
            "evidence": [],
            "practice": [],
        }
    ]
    # Plan has 2 lessons so navigation prev/next can be tested
    l1 = make_plan_lesson(1, steps, core_words=[w1])
    l2 = make_plan_lesson(2, steps, core_words=[w1])
    plan = make_plan(lessons=[l1, l2])

    draft = make_draft(
        steps=[{"id": "s1", "blocks": [{"kind": "prose", "text": "слово", "explains": ["W-1"]}]}],
        lesson_lock_entry_sha256="abc" * 21 + "a",
    )
    exp_doc, _ = assemble_expanded_document(draft, plan, pack, words_store, "a1", "sample-slug", 1)
    mock_stream = type(
        "MockStream",
        (),
        {
            "tokens": [{"unit_index": 0, "token": "слово", "class": "resolved", "selected": {"stressed": "сло́во"}}],
            "failures": [],
        },
    )()

    monkeypatch.setattr(
        "scripts.build.fresh.assemble.planned_state",
        lambda *args, **kwargs: type("State", (), {"cumulative_core_count": 10})(),
    )
    monkeypatch.setattr(lesson_lock, "check_lesson_lock", lambda *args, **kwargs: (True, ""))
    monkeypatch.setattr(
        lesson_lock,
        "compute_lesson_lock",
        lambda *args, **kwargs: {"lessons": [{"n": 1, "entry_sha256": "abc" * 21 + "a"}]},
    )

    state_dir = tmp_path / "state"
    site_dir = tmp_path / "site"

    res = check_9_stress_and_render(
        exp_doc,
        draft,
        plan,
        pack,
        words_store,
        mock_stream,
        "a1",
        "sample-slug",
        1,
        output_dir=state_dir,
        site_dir=site_dir,
    )
    assert res.passed is True
    # Output file is 1.mdx, NOT lesson-1.mdx
    assert (site_dir / "1.mdx").is_file()
    assert not (site_dir / "lesson-1.mdx").exists()

    meta = res.artifacts["meta_data"]
    # Navigation uses lesson order
    assert meta["prev"] == "/a1/sample-slug/"
    assert meta["next"] == "/a1/sample-slug/2/"


def test_activities_render_real_components_in_mdx(tmp_path, monkeypatch):
    """Blocker 1: Activities render as real components (<FillIn, <TrueFalse) in MDX."""
    w1 = make_word_record(1, "слово")
    words_store = make_words_store(words=[w1])
    pack = make_pack()

    step = {
        "id": "s1",
        "kind": "teach",
        "teach": "Teach",
        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-1"]},
        "uses": {"grammar": [], "vocabulary": []},
        "evidence": [],
        "practice": ["a1"],
    }
    plan_activities = [
        {"id": "a1", "type": "fill-in", "placement": "inline", "focus": "Fill-in focus"},
        {"id": "a2", "type": "true-false", "placement": "workbook", "focus": "True-false focus"},
    ]
    plan = make_plan(lessons=[make_plan_lesson(1, [step], core_words=[w1], activities=plan_activities)])

    act_fill = {
        "id": "a1",
        "instruction": "Заповніть пропуск.",
        "items": [
            {
                "sentence": "Це ____.",
                "answer": "слово",
                "options": ["слово", "мова"],
                "explanation": "Це правильне слово.",
            }
        ],
    }
    act_tf = {
        "id": "a2",
        "instruction": "Правда чи ні?",
        "items": [
            {
                "statement": "Слово це одиниця мови.",
                "correct": True,
                "explanation": "Так, це одиниця мови.",
            }
        ],
    }
    draft = make_draft(
        steps=[
            {
                "id": "s1",
                "blocks": [
                    {"kind": "prose", "text": "слово", "explains": ["W-1"]},
                    {"kind": "activity", "ref": "a1"},
                ],
            }
        ],
        activities=[act_fill, act_tf],
        consolidation={"activities": ["a2"]},
        lesson_lock_entry_sha256="abc" * 21 + "a",
    )

    exp_doc, _ = assemble_expanded_document(draft, plan, pack, words_store, "a1", "sample-slug", 1)
    mock_stream = type(
        "MockStream",
        (),
        {
            "tokens": [{"unit_index": 0, "token": "слово", "class": "resolved", "selected": {"stressed": "сло́во"}}],
            "failures": [],
        },
    )()

    monkeypatch.setattr(
        "scripts.build.fresh.assemble.planned_state",
        lambda *args, **kwargs: type("State", (), {"cumulative_core_count": 10, "waiver": None})(),
    )
    monkeypatch.setattr(lesson_lock, "check_lesson_lock", lambda *args, **kwargs: (True, ""))
    monkeypatch.setattr(
        lesson_lock,
        "compute_lesson_lock",
        lambda *args, **kwargs: {"lessons": [{"n": 1, "entry_sha256": "abc" * 21 + "a"}]},
    )

    state_dir = tmp_path / "state"
    site_dir = tmp_path / "site"

    res = check_9_stress_and_render(
        exp_doc,
        draft,
        plan,
        pack,
        words_store,
        mock_stream,
        "a1",
        "sample-slug",
        1,
        output_dir=state_dir,
        site_dir=site_dir,
    )
    assert res.passed is True
    mdx = res.artifacts["mdx"]
    assert "<FillIn client:only='react'" in mdx
    assert "<TrueFalse client:only='react'" in mdx
    assert "Це правильне слово." in mdx
    assert "Так, це одиниця мови." in mdx


def test_draft_activity_not_in_plan_fails_assembly():
    """Blocker 1: A draft activity not in plan fails assembly with named code."""
    w1 = make_word_record(1, "слово")
    words_store = make_words_store(words=[w1])
    pack = make_pack()

    step = {
        "id": "s1",
        "kind": "teach",
        "teach": "Teach",
        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-1"]},
        "uses": {"grammar": [], "vocabulary": []},
        "evidence": [],
        "practice": [],
    }
    plan = make_plan(lessons=[make_plan_lesson(1, [step], core_words=[w1], activities=[])])

    orphan_act = {
        "id": "a99",
        "instruction": "Orphan instruction",
        "items": [],
    }
    draft = make_draft(
        steps=[{"id": "s1", "blocks": [{"kind": "prose", "text": "слово", "explains": ["W-1"]}]}],
        activities=[orphan_act],
        validate=False,
    )

    with pytest.raises(AssemblerError) as exc:
        assemble_expanded_document(draft, plan, pack, words_store, "a1", "sample-slug", 1)
    assert exc.value.code == ACTIVITY_NOT_FOUND

    c5 = check_5_assembly(draft, plan, pack, words_store, "a1", "sample-slug", 1)
    assert c5.passed is False
    assert ACTIVITY_NOT_FOUND in (c5.reason or "")


def test_non_ok_draft_fails_closed_without_site_write(tmp_path):
    """Blocker 2: Refuse any draft whose status is not ok (e.g. evidence_gap)."""
    w1 = make_word_record(1, "слово")
    words_store = make_words_store(words=[w1])
    pack = make_pack()

    step = {
        "id": "s1",
        "kind": "teach",
        "teach": "Teach",
        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-1"]},
        "uses": {"grammar": [], "vocabulary": []},
        "evidence": [],
        "practice": [],
    }
    plan = make_plan(lessons=[make_plan_lesson(1, [step], core_words=[w1])])

    gap_draft = make_draft(
        steps=[{"id": "s1", "blocks": []}],
        status="evidence_gap",
        gaps=[{"step": "s1", "need": "example", "detail": "Missing example"}],
        validate=True,
    )

    state_dir = tmp_path / "state"
    site_dir = tmp_path / "site"

    rep = assemble_lesson(
        "a1",
        "sample-slug",
        1,
        draft_dict=gap_draft,
        plan_dict=plan,
        pack_dict=pack,
        words_dict=words_store,
        output_dir=state_dir,
        site_dir=site_dir,
    )
    assert rep["ok"] is False
    assert DRAFT_STATUS_NOT_OK in rep["failure"]["reason"]
    assert not site_dir.exists() or not list(site_dir.iterdir())


def test_expanded_schema_min_items_on_units():
    """Blocker 2: Expanded schema requires minItems: 1 on units."""
    valid_doc = {
        "expanded_schema": 1,
        "lesson": {"level": "a1", "slug": "test", "n": 1},
        "units": [
            {
                "tab": "urok",
                "step": "s1",
                "activity": None,
                "item": None,
                "block": "prose_0",
                "role": "instruction",
                "text": "test",
            }
        ],
    }
    _EXPANDED_VALIDATOR.validate(valid_doc)

    empty_doc = {
        "expanded_schema": 1,
        "lesson": {"level": "a1", "slug": "test", "n": 1},
        "units": [],
    }
    with pytest.raises(jsonschema.ValidationError):
        _EXPANDED_VALIDATOR.validate(empty_doc)


def test_taught_forms_reach_component_data(tmp_path, monkeypatch):
    """Major 1: Taught forms reach vocab_items and VocabCard component data."""
    w1 = {
        "id": "W-1",
        "lemma": "брат",
        "pos": "noun",
        "entry": {"source": "vesum", "entry_id": 10},
        "ulif": "pending",
        "forms": [
            {
                "form": "брата",
                "tags": "noun:anim:m:v_rod",
                "stress_source": "ulif",
                "markers": [],
                "learner": True,
                "stressed": "бра́та",
            },
            {
                "form": "братові",
                "tags": "noun:anim:m:v_dav",
                "stress_source": "ulif",
                "markers": [],
                "learner": True,
                "stressed": "бра́тові",
            },
        ],
    }
    words_store = make_words_store(words=[w1])
    pack = make_pack()

    step = {
        "id": "s1",
        "kind": "teach",
        "teach": "Teach",
        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-1"]},
        "uses": {"grammar": [], "vocabulary": []},
        "evidence": [],
        "practice": [],
    }
    lesson = make_plan_lesson(
        1,
        [step],
        core_words=[w1],
    )
    plan = make_plan(lessons=[lesson])

    draft = make_draft(
        steps=[{"id": "s1", "blocks": [{"kind": "prose", "text": "слово", "explains": ["W-1"]}]}],
        lesson_lock_entry_sha256="abc" * 21 + "a",
    )

    exp_doc, _ = assemble_expanded_document(draft, plan, pack, words_store, "a1", "sample-slug", 1)
    mock_stream = type(
        "MockStream",
        (),
        {
            "tokens": [{"unit_index": 0, "token": "слово", "class": "resolved", "selected": {"stressed": "сло́во"}}],
            "failures": [],
        },
    )()

    monkeypatch.setattr(
        "scripts.build.fresh.assemble.planned_state",
        lambda *args, **kwargs: type("State", (), {"cumulative_core_count": 5, "waiver": None})(),
    )
    monkeypatch.setattr(lesson_lock, "check_lesson_lock", lambda *args, **kwargs: (True, ""))
    monkeypatch.setattr(
        lesson_lock,
        "compute_lesson_lock",
        lambda *args, **kwargs: {"lessons": [{"n": 1, "entry_sha256": "abc" * 21 + "a"}]},
    )

    res = check_9_stress_and_render(
        exp_doc,
        draft,
        plan,
        pack,
        words_store,
        mock_stream,
        "a1",
        "sample-slug",
        1,
        output_dir=tmp_path / "state",
        site_dir=tmp_path / "site",
    )
    assert res.passed is True
    vocab = res.artifacts["vocab_items"]
    assert len(vocab) == 1
    assert vocab[0]["forms"] == ["бра́та", "бра́тові"]
    mdx = res.artifacts["mdx"]
    assert '"forms":["бра́та","бра́тові"]' in mdx or '"forms": ["бра́та", "бра́тові"]' in mdx


def test_missing_prior_plans_fails_assembly(monkeypatch, tmp_path):
    """Major 2: planned_state called without waiver; missing prior plans fail assembly."""
    w1 = make_word_record(1, "слово")
    words_store = make_words_store(words=[w1])
    pack = make_pack()

    step = {
        "id": "s1",
        "kind": "teach",
        "teach": "Teach",
        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-1"]},
        "uses": {"grammar": [], "vocabulary": []},
        "evidence": [],
        "practice": [],
    }

    # 1. Lesson 1 of position 1 has no prior plans and passes
    plan_pos1 = make_plan(arc_position=1, lessons=[make_plan_lesson(1, [step], core_words=[w1])])
    draft = make_draft(
        steps=[{"id": "s1", "blocks": [{"kind": "prose", "text": "слово", "explains": ["W-1"]}]}],
        lesson_lock_entry_sha256="abc" * 21 + "a",
    )
    exp_doc, _ = assemble_expanded_document(draft, plan_pos1, pack, words_store, "a1", "sample-slug", 1)
    mock_stream = type(
        "MockStream",
        (),
        {
            "tokens": [{"unit_index": 0, "token": "слово", "class": "resolved", "selected": {"stressed": "сло́во"}}],
            "failures": [],
        },
    )()

    monkeypatch.setattr(lesson_lock, "check_lesson_lock", lambda *args, **kwargs: (True, ""))
    monkeypatch.setattr(
        lesson_lock,
        "compute_lesson_lock",
        lambda *args, **kwargs: {"lessons": [{"n": 1, "entry_sha256": "abc" * 21 + "a"}]},
    )
    monkeypatch.setattr("scripts.curriculum.learner_state.planned.resolve_base_ids", lambda *a, **kw: [])

    p_dir = tmp_path / "plans"
    p_dir.mkdir(parents=True, exist_ok=True)
    plan_path = p_dir / "01-sample-slug.yaml"
    plan_path.write_text(yaml.safe_dump(plan_pos1), encoding="utf-8")

    res_pos1 = check_9_stress_and_render(
        exp_doc,
        draft,
        plan_pos1,
        pack,
        words_store,
        mock_stream,
        "a1",
        "sample-slug",
        1,
        plans_dir=p_dir,
    )
    assert res_pos1.passed is True

    # 2. Position 2 with missing position 1 plan fails with PRIOR_PLANS_MISSING
    p_dir2 = tmp_path / "plans2"
    p_dir2.mkdir(parents=True, exist_ok=True)
    plan_pos2 = make_plan(arc_position=2, lessons=[make_plan_lesson(1, [step], core_words=[w1])])
    (p_dir2 / "02-sample-slug.yaml").write_text(yaml.safe_dump(plan_pos2), encoding="utf-8")

    res_pos2 = check_9_stress_and_render(
        exp_doc,
        draft,
        plan_pos2,
        pack,
        words_store,
        mock_stream,
        "a1",
        "sample-slug",
        1,
        plans_dir=p_dir2,
    )
    assert res_pos2.passed is False
    assert PRIOR_PLANS_MISSING in (res_pos2.reason or "")


def test_frontmatter_job_quotes_and_colons_roundtrip():
    """Minor 1: job with quotes and colons round-trips cleanly through YAML parser."""
    from scripts.generate_mdx.core import generate_mdx

    job_text = 'Learn Ukrainian: the "gold" standard for A1'
    meta = {
        "title": "Title",
        "subtitle": "Subtitle",
        "job": job_text,
        "immersion": "low_scaffold",
        "evidence": {"plan_sha256": "0" * 64},
        "prev": "/a1/prev/",
        "next": "/a1/next/",
        "lesson": 1,
        "module_slug": "slug",
    }

    mdx = generate_mdx(
        md_content="## Heading\n\nContent",
        module_num=1,
        meta_data=meta,
        fresh=True,
    )

    parts = mdx.split("---")
    assert len(parts) >= 3
    fm_raw = parts[1]
    parsed = yaml.safe_load(fm_raw)
    assert parsed["job"] == job_text
    assert "&quot;" not in fm_raw


def test_cli_blocked_report_prints_tokens_and_failures(capsys, monkeypatch):
    """Minor 2: CLI prints blocking tokens and failures, not 'Check None: None'."""
    from scripts.build.fresh import cli

    blocked_rep = {
        "ok": False,
        "blocking_tokens": ["слово", "мова"],
        "stream_failures": ["unresolved token at unit 2"],
        "message": "stream has 2 blocking token(s) and 1 failure(s); refusing site write",
    }
    monkeypatch.setattr("scripts.build.fresh.assemble.assemble_lesson", lambda *args, **kwargs: blocked_rep)

    rc = cli.main(["assemble", "a1", "sample-slug", "--lesson", "1"])
    assert rc == 1

    captured = capsys.readouterr()
    err = captured.err
    assert "Check None: None" not in err
    assert "Blocking token: слово" in err
    assert "Blocking token: мова" in err
    assert "Stream failure: unresolved token at unit 2" in err


def test_fill_in_modes_appear_in_assembler_fill_in_props(tmp_path, monkeypatch):
    """Blocker: Both fill-in modes appear in generated <FillIn> props from the assembler."""
    w1 = make_word_record(1, "слово")
    words_store = make_words_store(words=[w1])
    pack = make_pack()

    step = {
        "id": "s1",
        "kind": "teach",
        "teach": "Teach",
        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-1"]},
        "uses": {"grammar": [], "vocabulary": []},
        "evidence": [],
        "practice": ["a1"],
    }
    plan_activities = [
        {"id": "a1", "type": "fill-in", "placement": "inline", "focus": "Fill-in focus"},
    ]
    plan = make_plan(lessons=[make_plan_lesson(1, [step], core_words=[w1], activities=plan_activities)])

    act_fill = {
        "id": "a1",
        "instruction": "Заповніть пропуски.",
        "items": [
            {
                "sentence": "Це ____ слово.",
                "answer": "гарне",
                "options": ["гарне", "гарна"],
                "explanation": "Виберіть форму.",
                "mode": "form-choice",
                "record": "W-1",
                "answer_tags": "adj:n:v_naz",
            },
            {
                "sentence": "Це м____ясо.",
                "answer": "'",
                "options": ["'", ""],
                "explanation": "Правопис апострофа.",
                "mode": "orthography",
            },
        ],
    }
    draft = make_draft(
        steps=[
            {
                "id": "s1",
                "blocks": [
                    {"kind": "prose", "text": "слово", "explains": ["W-1"]},
                    {"kind": "activity", "ref": "a1"},
                ],
            }
        ],
        activities=[act_fill],
        consolidation={"activities": []},
        lesson_lock_entry_sha256="abc" * 21 + "a",
    )

    exp_doc, _ = assemble_expanded_document(draft, plan, pack, words_store, "a1", "sample-slug", 1)
    mock_stream = type(
        "MockStream",
        (),
        {
            "tokens": [{"unit_index": 0, "token": "слово", "class": "resolved", "selected": {"stressed": "сло́во"}}],
            "failures": [],
        },
    )()

    monkeypatch.setattr(
        "scripts.build.fresh.assemble.planned_state",
        lambda *args, **kwargs: type("State", (), {"cumulative_core_count": 10, "waiver": None})(),
    )
    monkeypatch.setattr(lesson_lock, "check_lesson_lock", lambda *args, **kwargs: (True, ""))
    monkeypatch.setattr(
        lesson_lock,
        "compute_lesson_lock",
        lambda *args, **kwargs: {"lessons": [{"n": 1, "entry_sha256": "abc" * 21 + "a"}]},
    )

    state_dir = tmp_path / "state"
    site_dir = tmp_path / "site"

    res = check_9_stress_and_render(
        exp_doc,
        draft,
        plan,
        pack,
        words_store,
        mock_stream,
        "a1",
        "sample-slug",
        1,
        output_dir=state_dir,
        site_dir=site_dir,
    )
    assert res.passed is True
    mdx = res.artifacts["mdx"]
    assert "<FillIn client:only='react'" in mdx
    assert '"mode": "form-choice"' in mdx
    assert '"mode": "orthography"' in mdx


def test_true_false_statement_resolved_and_stressed_in_true_false_output(tmp_path, monkeypatch):
    """Major: True/false statement is in expanded units and gets stressed in <TrueFalse> output."""
    w1 = make_word_record(1, "слово")
    words_store = make_words_store(words=[w1])
    pack = make_pack()

    step = {
        "id": "s1",
        "kind": "teach",
        "teach": "Teach",
        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-1"]},
        "uses": {"grammar": [], "vocabulary": []},
        "evidence": [],
        "practice": [],
    }
    plan_activities = [
        {"id": "a1", "type": "true-false", "placement": "workbook", "focus": "True-false focus"},
    ]
    plan = make_plan(lessons=[make_plan_lesson(1, [step], core_words=[w1], activities=plan_activities)])

    act_tf = {
        "id": "a1",
        "instruction": "Правда чи ні?",
        "items": [
            {
                "statement": "Це слово правда.",
                "correct": True,
                "explanation": "Так, це правда.",
            }
        ],
    }
    draft = make_draft(
        steps=[
            {
                "id": "s1",
                "blocks": [
                    {"kind": "prose", "text": "слово", "explains": ["W-1"]},
                ],
            }
        ],
        activities=[act_tf],
        consolidation={"activities": ["a1"]},
        lesson_lock_entry_sha256="abc" * 21 + "a",
    )

    exp_doc, _ = assemble_expanded_document(draft, plan, pack, words_store, "a1", "sample-slug", 1)

    stmt_units = [
        (idx, u)
        for idx, u in enumerate(exp_doc["units"])
        if u.get("tab") == "vpravy" and u.get("activity") == "a1" and u.get("item") == 0 and u.get("block") == "prompt"
    ]
    assert len(stmt_units) == 1
    stmt_idx, stmt_unit = stmt_units[0]
    assert stmt_unit["role"] == "item_prompt"
    assert stmt_unit["text"] == "Це слово правда."

    mock_stream = type(
        "MockStream",
        (),
        {
            "tokens": [
                {
                    "unit_index": 0,
                    "offset": 0,
                    "token": "слово",
                    "class": "resolved",
                    "selected": {"stressed": "сло́во"},
                },
                {
                    "unit_index": stmt_idx,
                    "offset": 3,
                    "token": "слово",
                    "class": "resolved",
                    "selected": {"stressed": "сло́во"},
                },
            ],
            "failures": [],
        },
    )()

    monkeypatch.setattr(
        "scripts.build.fresh.assemble.planned_state",
        lambda *args, **kwargs: type("State", (), {"cumulative_core_count": 10, "waiver": None})(),
    )
    monkeypatch.setattr(lesson_lock, "check_lesson_lock", lambda *args, **kwargs: (True, ""))
    monkeypatch.setattr(
        lesson_lock,
        "compute_lesson_lock",
        lambda *args, **kwargs: {"lessons": [{"n": 1, "entry_sha256": "abc" * 21 + "a"}]},
    )

    state_dir = tmp_path / "state"
    site_dir = tmp_path / "site"

    res = check_9_stress_and_render(
        exp_doc,
        draft,
        plan,
        pack,
        words_store,
        mock_stream,
        "a1",
        "sample-slug",
        1,
        output_dir=state_dir,
        site_dir=site_dir,
    )
    assert res.passed is True
    mdx = res.artifacts["mdx"]
    assert "<TrueFalse client:only='react'" in mdx
    assert "Це сло́во правда." in mdx


def test_true_false_boolean_answer_and_correct_produce_no_answer_units_and_render_correctly(tmp_path, monkeypatch):
    """Major: a true/false item with answer: true and one with correct: false produce no answer unit and render correctly."""
    w1 = make_word_record(1, "слово")
    words_store = make_words_store(words=[w1])
    pack = make_pack()

    step = {
        "id": "s1",
        "kind": "teach",
        "teach": "Teach",
        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-1"]},
        "uses": {"grammar": [], "vocabulary": []},
        "evidence": [],
        "practice": [],
    }
    plan_activities = [
        {"id": "a1", "type": "true-false", "placement": "workbook", "focus": "True-false focus"},
    ]
    plan = make_plan(lessons=[make_plan_lesson(1, [step], core_words=[w1], activities=plan_activities)])

    act_tf = {
        "id": "a1",
        "instruction": "Правда чи ні?",
        "items": [
            {
                "statement": "Це слово правда.",
                "answer": True,
                "explanation": "Так, це правда.",
            },
            {
                "statement": "Це слово неправда.",
                "correct": False,
                "explanation": "Ні, це неправда.",
            },
        ],
    }
    draft = make_draft(
        steps=[
            {
                "id": "s1",
                "blocks": [
                    {"kind": "prose", "text": "слово", "explains": ["W-1"]},
                ],
            }
        ],
        activities=[act_tf],
        consolidation={"activities": ["a1"]},
        lesson_lock_entry_sha256="abc" * 21 + "a",
    )

    exp_doc, _ = assemble_expanded_document(draft, plan, pack, words_store, "a1", "sample-slug", 1)

    # Neither boolean answer: true nor boolean correct: false must produce an answer text unit
    answer_units = [
        u
        for u in exp_doc["units"]
        if u.get("tab") == "vpravy"
        and u.get("activity") == "a1"
        and (u.get("role") == "item_answer" or u.get("block") == "answer")
    ]
    assert len(answer_units) == 0

    stmt_units = [
        (idx, u)
        for idx, u in enumerate(exp_doc["units"])
        if u.get("tab") == "vpravy" and u.get("activity") == "a1" and u.get("block") == "prompt"
    ]
    assert len(stmt_units) == 2
    stmt_0_idx, stmt_0 = stmt_units[0]
    stmt_1_idx, stmt_1 = stmt_units[1]
    assert stmt_0["role"] == "item_prompt"
    assert stmt_0["text"] == "Це слово правда."
    assert stmt_1["role"] == "item_prompt"
    assert stmt_1["text"] == "Це слово неправда."

    mock_stream = type(
        "MockStream",
        (),
        {
            "tokens": [
                {
                    "unit_index": 0,
                    "offset": 0,
                    "token": "слово",
                    "class": "resolved",
                    "selected": {"stressed": "сло́во"},
                },
                {
                    "unit_index": stmt_0_idx,
                    "offset": 3,
                    "token": "слово",
                    "class": "resolved",
                    "selected": {"stressed": "сло́во"},
                },
                {
                    "unit_index": stmt_1_idx,
                    "offset": 3,
                    "token": "слово",
                    "class": "resolved",
                    "selected": {"stressed": "сло́во"},
                },
            ],
            "failures": [],
        },
    )()

    monkeypatch.setattr(
        "scripts.build.fresh.assemble.planned_state",
        lambda *args, **kwargs: type("State", (), {"cumulative_core_count": 10, "waiver": None})(),
    )
    monkeypatch.setattr(lesson_lock, "check_lesson_lock", lambda *args, **kwargs: (True, ""))
    monkeypatch.setattr(
        lesson_lock,
        "compute_lesson_lock",
        lambda *args, **kwargs: {"lessons": [{"n": 1, "entry_sha256": "abc" * 21 + "a"}]},
    )

    state_dir = tmp_path / "state"
    site_dir = tmp_path / "site"

    res = check_9_stress_and_render(
        exp_doc,
        draft,
        plan,
        pack,
        words_store,
        mock_stream,
        "a1",
        "sample-slug",
        1,
        output_dir=state_dir,
        site_dir=site_dir,
    )
    assert res.passed is True
    mdx = res.artifacts["mdx"]
    assert "<TrueFalse client:only='react'" in mdx
    assert "Це сло́во правда." in mdx
    assert "Це сло́во неправда." in mdx

    m = re.search(r"<TrueFalse [^>]*items=\{JSON\.parse\(`([^`]+)`\)\}", mdx)
    assert m is not None
    tf_items = json.loads(m.group(1))
    assert len(tf_items) == 2
    assert tf_items[0]["statement"] == "Це сло́во правда."
    assert tf_items[0]["isTrue"] is True
    assert tf_items[0]["explanation"] == "Так, це правда."
    assert tf_items[1]["statement"] == "Це сло́во неправда."
    assert tf_items[1]["isTrue"] is False
    assert tf_items[1]["explanation"] == "Ні, це неправда."
