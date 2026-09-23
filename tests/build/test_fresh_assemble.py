"""Tests for fresh lesson assembler (WP 13 part E3a, #8431, #8430, #8397, #8414)."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import jsonschema
import pytest

from scripts.build.fresh.assemble import (
    apply_stress,
    assemble_expanded_document,
    build_resursy_tab,
    build_slovnyk_tab,
    check_5_assembly,
    check_9_stress_and_render,
    get_expanded_validator,
)

pytestmark = pytest.mark.reads_content

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / "fixtures" / "fresh"
EXPANDED_SCHEMA_PATH = REPO_ROOT / "schemas" / "lesson-expanded-v1.schema.json"


def test_no_cyrillic_string_literals_in_assembler():
    """Nothing typed: assert that scripts/build/fresh/assemble.py has NO Cyrillic string literals."""
    assemble_file = REPO_ROOT / "scripts" / "build" / "fresh" / "assemble.py"
    source = assemble_file.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(assemble_file))

    cyrillic_pattern = re.compile(r"[\u0400-\u04FF]")
    found_literals: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and cyrillic_pattern.search(node.value)
        ):
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
    schema = json.loads(EXPANDED_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)

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
                "role": "exposition",
                "text": "Hello world and plain Ukrainian text without accents",
            },
            {
                "tab": "vpravy",
                "step": "s1",
                "activity": "a1",
                "item": 0,
                "block": None,
                "role": "instruction",
                "text": "Choose the correct answer",
            },
            {
                "tab": "slovnyk",
                "step": None,
                "activity": None,
                "item": None,
                "block": None,
                "role": "reference",
                "text": "Plain lemma",
            },
        ],
    }

    errors = list(validator.iter_errors(sample_doc))
    assert len(errors) == 0


def test_combining_accent_fails_expanded_schema_and_check_5():
    """A combining accent in the expanded document is a bug that fails schema validation and check 5."""
    schema = json.loads(EXPANDED_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)

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
                "role": "exposition",
                "text": "Украї\u0301на",  # combining acute
            }
        ],
    }

    errors = list(validator.iter_errors(doc_with_accent))
    assert len(errors) > 0

    # Also verify check_5_assembly catches combining accent
    plan = {
        "lessons": [
            {
                "n": 1,
                "title": "Lesson 1",
                "steps": [{"id": "s1"}],
                "activities": [],
            }
        ]
    }
    draft = {
        "draft_schema": 1,
        "lesson": {"module": "a1/test-slug", "n": 1},
        "steps": [
            {
                "id": "s1",
                "blocks": [
                    {"kind": "prose", "text": "Украї\u0301на with accent"}
                ],
            }
        ],
        "activities": [],
    }
    res = check_5_assembly(draft, plan, {}, {}, "a1", "test-slug", 1)
    assert res.passed is False
    assert "combining accent" in (res.reason or "") or "schema validation" in (res.reason or "")


def test_step_ids_on_units_in_expanded_document():
    """Every unit carries step (the plan step id, or null for tabs/blocks without steps)."""
    plan = {
        "lessons": [
            {
                "n": 1,
                "title": "Lesson 1",
                "steps": [
                    {"id": "step_intro", "teach": "Intro"},
                    {"id": "step_dialogue", "teach": "Exchange"},
                ],
                "activities": [
                    {"id": "act_1", "type": "quiz"},
                ],
                "inventory": {
                    "vocabulary": {
                        "core": [{"evidence": "W-01", "forms": ["слово"]}],
                        "incidental": ["W-02"],
                    }
                },
            }
        ]
    }

    draft = {
        "draft_schema": 1,
        "lesson": {"module": "a1/sample-slug", "n": 1},
        "steps": [
            {
                "id": "step_intro",
                "lead_in": "Welcome",
                "blocks": [
                    {"kind": "prose", "text": "First explanation"},
                ],
            },
            {
                "id": "step_dialogue",
                "blocks": [
                    {"kind": "prose", "text": "Second explanation"},
                ],
            },
        ],
        "dialogue": {
            "lines": [
                {"speaker": "SpeakerA", "text": "Привіт"},
            ],
            "translation_en": ["Hello"],
        },
        "activities": [
            {
                "id": "act_1",
                "instruction": "Answer question",
                "items": [
                    {
                        "question": "Question 1",
                        "options": [
                            {"text": "Opt 1", "correct": True},
                            {"text": "Opt 2", "correct": False},
                        ],
                    }
                ],
            }
        ],
        "consolidation": {
            "lead_in": "Wrap up",
            "activities": ["act_1"],
        },
    }

    pack = {"examples": [], "textbook_chunks": [], "videos": []}
    words_store = {
        "words": [
            {"id": "W-01", "lemma": "слово", "gloss": "word", "pos": "noun", "gender": "neut"},
            {"id": "W-02", "lemma": "мова", "gloss": "language", "pos": "noun", "gender": "fem"},
        ]
    }

    exp_doc, _prov_doc = assemble_expanded_document(draft, plan, pack, words_store, "a1", "sample-slug", 1)

    assert exp_doc["expanded_schema"] == 1
    units = exp_doc["units"]
    assert len(units) > 0

    # Check step propagation
    step_intro_units = [u for u in units if u.get("step") == "step_intro"]
    assert len(step_intro_units) >= 2  # lead_in + prose

    step_dialogue_units = [u for u in units if u.get("step") == "step_dialogue"]
    assert len(step_dialogue_units) >= 1  # prose

    # Slovnyk and Resursy units have step = None
    slovnyk_units = [u for u in units if u.get("tab") == "slovnyk"]
    assert len(slovnyk_units) >= 2  # 2 words
    for u in slovnyk_units:
        assert u.get("step") is None

    # Activity unit associated with step
    act_units = [u for u in units if u.get("activity") == "act_1"]
    assert len(act_units) >= 1
    # Activity mapped to step_intro via plan
    for u in act_units:
        assert u.get("step") in ("step_intro", "consolidation", None)

    # Validate against JSON schema
    validator = get_expanded_validator()
    errors = list(validator.iter_errors(exp_doc))
    assert len(errors) == 0


def test_build_slovnyk_and_resursy_tabs():
    """Verify build_slovnyk_tab and build_resursy_tab structure and content."""
    lesson_plan = {
        "steps": [
            {"id": "s1", "needs": ["V-001"], "use": "Watch the alphabet song"}
        ],
        "inventory": {
            "vocabulary": {
                "core": [{"evidence": "W-001", "forms": ["добрий", "доброго"]}],
                "incidental": ["W-002"],
            }
        },
    }
    words_store = {
        "words": [
            {
                "id": "W-001",
                "lemma": "добрий",
                "gloss": "good",
                "pos": "adj",
                "gender": "masc",
                "forms": [{"form": "добрий", "stressed": "до́брий", "learner": True}],
            },
            {
                "id": "W-002",
                "lemma": "день",
                "gloss": "day",
                "pos": "noun",
                "gender": "masc",
                "forms": [{"form": "день", "stressed": "де́нь", "learner": True}],
            },
        ]
    }
    pack = {
        "textbook_chunks": [
            {
                "id": "TB-01",
                "title": "Ukrainian for Beginners",
                "author": "Shevchenko",
                "pages": "10-15",
                "url": "https://example.com/tb",
                "attribution": "Intro chapter",
            }
        ],
        "videos": [
            {
                "id": "V-001",
                "title": "Alphabet Song",
                "url": "https://youtube.com/watch?v=123",
                "channel": "LearnUA",
                "description": "Default description",
            }
        ],
    }

    slovnyk = build_slovnyk_tab(lesson_plan, words_store)
    assert len(slovnyk) == 2
    assert slovnyk[0]["lemma"] == "до́брий"
    assert slovnyk[0]["translation"] == "good"
    assert slovnyk[0]["pos"] == "adj"
    assert "atlas_href" in slovnyk[0]
    assert slovnyk[0]["forms"] == ["добрий", "доброго"]

    assert slovnyk[1]["lemma"] == "де́нь"
    assert slovnyk[1]["translation"] == "day"

    resursy = build_resursy_tab(lesson_plan, pack)
    assert "books" in resursy
    assert len(resursy["books"]) == 1
    assert resursy["books"][0]["source"] == "TB-01"

    assert "youtube" in resursy
    assert len(resursy["youtube"]) == 1
    # Description pulled from plan's use: line
    assert resursy["youtube"][0]["description"] == "Watch the alphabet song"


def test_apply_stress_and_check_9(tmp_path):
    """Verify apply_stress updates unit text and check_9 produces valid frontmatter."""
    expanded_doc = {
        "expanded_schema": 1,
        "lesson": {"level": "a1", "slug": "test-mod", "n": 1},
        "units": [
            {
                "tab": "urok",
                "step": "s1",
                "activity": None,
                "item": None,
                "block": 0,
                "role": "exposition",
                "text": "добрий день",
            }
        ],
    }

    # Synthetic stream with stressed tokens
    mock_stream = type(
        "MockStream",
        (),
        {
            "tokens": [
                {
                    "unit_index": 0,
                    "offset": 0,
                    "token": "добрий",
                    "selected": {"stressed": "до́брий", "record": "W-001", "gloss": "good"},
                },
                {
                    "unit_index": 0,
                    "offset": 7,
                    "token": "день",
                    "selected": {"stressed": "де́нь", "record": "W-002", "gloss": "day"},
                },
            ]
        },
    )()

    stressed = apply_stress(expanded_doc, mock_stream)
    assert stressed["units"][0]["text"] == "до́брий де́нь"

    plan = {
        "lessons": [
            {
                "n": 1,
                "title": "Greetings",
                "rationale": "Learn hello",
                "job": "Greet people",
                "steps": [{"id": "s1"}],
                "activities": [],
                "inventory": {"vocabulary": {"core": [], "incidental": []}},
            }
        ]
    }
    draft = {
        "draft_schema": 1,
        "lesson": {"module": "a1/test-mod", "n": 1},
        "steps": [{"id": "s1", "blocks": [{"kind": "prose", "text": "добрий день"}]}],
        "activities": [],
    }
    pack = {"examples": [], "textbook_chunks": [], "videos": []}
    words_store = {"words": []}

    site_dir = tmp_path / "site"
    state_dir = tmp_path / "state"

    res = check_9_stress_and_render(
        expanded_doc,
        draft,
        plan,
        pack,
        words_store,
        mock_stream,
        "a1",
        "test-mod",
        1,
        output_dir=state_dir,
        site_dir=site_dir,
    )
    assert res.passed is True
    meta = res.artifacts["meta_data"]
    assert "evidence" in meta
    assert "lessons_lock_sha256" in meta["evidence"]
    assert "lesson_entry_sha256" in meta["evidence"]
    assert "immersion" in meta
    assert meta["job"] == "Greet people"
    assert (site_dir / "lesson-1.mdx").is_file()
    assert (state_dir / "lesson-1.stressed.yaml").is_file()
