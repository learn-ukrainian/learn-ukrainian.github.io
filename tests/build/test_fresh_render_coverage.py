"""Check-9 render coverage, independently walking the live draft/activity schemas.

Synthetic English markers test transport, not Ukrainian correctness or admission.
Locks and prior learner state are isolated only for these renderer contract tests.
"""

from __future__ import annotations

import ast
import copy
import inspect
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import jsonschema
import pytest

from scripts.build.fresh import assemble
from scripts.build.fresh.draft_schema import draft_validator
from scripts.build.fresh.gen_draft_schemas import META_KEYS
from scripts.curriculum.resolver import receipts
from scripts.generate_mdx.converters import process_story_sections

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / "fixtures/render_coverage"
LEVELS = ("a1", "a2", "b1", "b2")


def maximal_draft(level):
    activities = json.loads((FIXTURES / f"activities-{level}.json").read_text())
    schema = json.loads((ROOT / f"schemas/lesson-draft-{level}-v1.schema.json").read_text())
    blocks = []
    for name, definition in schema["$defs"].items():
        if not name.startswith("block_"):
            continue
        kind = definition["properties"]["kind"]["const"]
        block = {"kind": kind}
        for key in definition["properties"]:
            if key == "text":
                block[key] = f"{kind} body {{" + "{gloss:W-1}} and {{uk:sample}}."
            elif key == "explains":
                block[key] = ["T-1"]
            elif key == "rows":
                block[key] = [["Header one", "Header two"], ["Cell one", "Cell two"]]
            elif key == "uk":
                block[key] = ["Passage first", "Passage second"]
            elif key == "en":
                block[key] = ["Translation first", "Translation second"]
            elif key == "lead_in":
                block[key] = "Video lead in."
            elif key == "ref":
                block[key] = {
                    "example": "EX-1",
                    "quote": "T-1",
                    "paradigm": "P-1",
                    "video": "V-1",
                    "activity": next(iter(activities.values()))["id"],
                }[kind]
        blocks.append(block)
    # The remaining activities are in the consolidation block.
    first = next(iter(activities.values()))["id"]
    draft = {
        "draft_schema": 1,
        "lesson": {"module": f"{level}/render-coverage", "n": 1},
        "inputs": {k: "0" * 64 for k in schema["properties"]["inputs"]["required"]},
        "status": "ok",
        "steps": [{"id": "s1", "lead_in": "Step lead in.", "blocks": blocks}],
        "consolidation": {
            "lead_in": "Consolidation lead in.",
            "activities": [a["id"] for a in activities.values() if a["id"] != first],
        },
        "dialogue": {
            "lines": [{"speaker": "First", "text": "Dialogue first"}, {"speaker": "Second", "text": "Dialogue second"}],
            "translation_en": ["English first", "English second"],
        },
        "activities": list(activities.values()),
        "gaps": [],
    }
    words = {
        "words": [
            {
                "id": f"W-{i}",
                "lemma": f"lemma{i}",
                "pos": "noun",
                "gloss_en": f"gloss{i}",
                "forms": [
                    {
                        "tags": "noun:inanim:m:v_naz",
                        "form": f"lemma{i}",
                        "stressed": f"lemma{i}",
                        "stress_source": "ulif",
                        "learner": True,
                    }
                ],
            }
            for i in (1, 2)
        ]
    }
    pack = {
        "texts": [
            {
                "id": "T-1",
                "quote": "Source quote.",
                "source": {"kind": "textbook", "file": "1-klas-bukvar-zaharijchuk-2025-1", "page": 10},
            }
        ],
        "examples": [
            {
                "id": "EX-1",
                "text": "Source example.",
                "translation_en": "Example English.",
                "source": {"kind": "textbook", "file": "1-klas-bukvar-zaharijchuk-2025-1", "page": 11},
            }
        ],
        "videos": [
            {
                "id": "V-1",
                "url": "https://www.youtube.com/watch?v=fixture9526",
                "channel": "Video channel",
                "use": "Video use.",
            }
        ],
        "errors": [
            {
                "id": "E-001",
                "incorrect": activities.get("error-correction", {}).get("items", [{}])[0].get("error", ""),
                "correct": activities.get("error-correction", {}).get("items", [{}])[0].get("correction", ""),
            }
        ],
    }
    lesson = {
        "n": 1,
        "title": "Render coverage",
        "job": "Coverage",
        "steps": [
            {
                "id": "s1",
                "practice": [first],
                "evidence": ["T-1", "EX-1", "V-1"],
                "paradigm": {"id": "P-1", "word": "W-1", "forms": ["noun:inanim:m:v_naz"]},
            }
        ],
        "videos": [{"evidence": "V-1", "use": "Video use."}],
        "inventory": {
            "vocabulary": {
                "core": [{"evidence": "W-1", "forms": ["noun:inanim:m:v_naz"]}],
                "incidental": [{"evidence": "W-2"}],
            }
        },
        "activities": [
            {"id": act["id"], "type": typ, "placement": "workbook" if typ == "translate" else "practice", "focus": typ}
            for typ, act in activities.items()
        ],
    }
    plan = {"arc_ref": {"position": 1}, "lessons": [lesson]}
    return draft, plan, pack, words


@pytest.fixture
def render_environment(monkeypatch):
    monkeypatch.setattr(assemble.lesson_lock, "check_lesson_lock", lambda *a, **k: (True, ""))
    monkeypatch.setattr(
        assemble.lesson_lock, "compute_lesson_lock", lambda *a, **k: {"lessons": [{"n": 1, "entry_sha256": "0" * 64}]}
    )
    monkeypatch.setattr(
        assemble, "planned_state", lambda *a, **k: SimpleNamespace(waiver=None, cumulative_core_count=2)
    )


def check_render(inputs, level):
    draft, plan, pack, words = inputs
    expanded, provenance = assemble.assemble_expanded_document(draft, plan, pack, words, level, "render-coverage", 1)
    result = assemble.check_9_stress_and_render(
        expanded, draft, plan, pack, words, {"tokens": []}, level, "render-coverage", 1, provenance_doc=provenance
    )
    return result, expanded


def schema_leaves(schema, path=(), document=None):
    """Walk alternatives and arrays, retaining property paths (not array indices)."""
    if "$ref" in schema and document is not None:
        target = document
        for part in schema["$ref"].removeprefix("#/").split("/"):
            target = target[part]
        yield from schema_leaves(target, path, document)
    elif "properties" in schema:
        for key, child in schema["properties"].items():
            yield from schema_leaves(child, (*path, key), document)
    elif schema.get("type") == "array":
        yield from schema_leaves(schema.get("items", {}), (*path, "*"), document)
    elif "oneOf" in schema or "anyOf" in schema:
        for child in schema.get("oneOf", schema.get("anyOf", [])):
            yield from schema_leaves(child, path, document)
    else:
        yield path


def fixture_leaves(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from fixture_leaves(child, (*path, key))
    elif isinstance(value, list):
        for child in value:
            yield from fixture_leaves(child, (*path, "*"))
    else:
        yield path


def expansion_fields():
    """Walk the expansion's reachable helpers as well as prompt precedence.

    Literal keys conservatively overcount fields; helpers cannot hide a new
    unit-producing key. Inspect repository functions without executing them.
    """
    pending = [assemble.assemble_expanded_document, receipts.requirement_sentence]
    seen, fields = set(), set()
    while pending:
        function = pending.pop()
        if function in seen:
            continue
        seen.add(function)
        tree = ast.parse(inspect.getsource(function))
        fields.update(n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            target = node.func
            names = []
            while isinstance(target, ast.Attribute):
                names.append(target.attr)
                target = target.value
            if not isinstance(target, ast.Name):
                continue
            candidate = function.__globals__.get(target.id)
            for name in reversed(names):
                candidate = getattr(candidate, name, None)
            if inspect.isfunction(candidate) and candidate.__module__ in {assemble.__name__, receipts.__name__}:
                pending.append(candidate)
    return fields


@pytest.mark.parametrize("level", LEVELS)
def test_fresh_schema_walk_exercises_expansion_fields(level):
    draft, _, _, _ = maximal_draft(level)
    draft_validator(level).validate(draft)
    schema = json.loads((ROOT / f"schemas/activities-{level}.schema.json").read_text())
    fixtures = json.loads((FIXTURES / f"activities-{level}.json").read_text())
    assert set(fixtures) == {name.removesuffix("-" + level) for name in schema["definitions"]}
    missing = []
    for name, definition in schema["definitions"].items():
        typ = name.removesuffix("-" + level)
        act = fixtures[typ]
        # The engine, rather than the draft, supplies these plan metadata fields.
        payload = {k: v for k, v in {**act, "type": typ, "title": typ}.items() if k in definition["properties"]}
        jsonschema.Draft7Validator(definition).validate(payload)
        metadata = {
            "kind",
            "ref",
            "record",
            "error_ref",
            "error_type",
            "host",
            "requires",
            "option_records",
            "target_record",
            "tests_feature",
        }
        expected = {
            p
            for p in schema_leaves(definition)
            if p
            and p[0] not in META_KEYS - {"instruction"}
            and not metadata.intersection(p)
            and next((part for part in reversed(p) if part != "*"), "")
            in expansion_fields() - {"items", "groups", "pairs"}
        }
        actual = set(fixture_leaves(act))
        missing.extend(f"{level}/{typ}:" + ".".join(p) for p in expected if p not in actual)
    missing.extend(document_coverage_gaps(level, draft))
    assert not missing, "Unit-producing schema paths not exercised:\n" + "\n".join(sorted(missing))


@pytest.mark.parametrize("level", LEVELS)
def test_fresh_maximal_draft_reaches_check_9(level, render_environment):
    inputs = maximal_draft(level)
    draft_validator(level).validate(inputs[0])
    result, expanded = check_render(inputs, level)
    assert {u["tab"] for u in expanded["units"]} == {"urok", "vpravy", "slovnyk", "resursy"}
    assert result.passed, result.to_dict()
    assert len(result.artifacts["provenance"]["spans"]) == len(expanded["units"])
    assert set(result.artifacts["external_resources"]) == {"books", "youtube"}
    assert {u["block"] for u in expanded["units"] if u["tab"] == "slovnyk"} == {"core_W-1", "inc_W-2"}


@pytest.mark.parametrize("level", LEVELS)
def test_fresh_every_activity_render_gap_is_reported(level, render_environment):
    inputs = maximal_draft(level)
    gaps = []
    # A failing early block must not conceal a second gap. Exercise each activity
    # separately without the dialogue to enumerate all component lookup failures.
    for act in inputs[0]["activities"]:
        isolated = copy.deepcopy(inputs)
        isolated[0]["steps"] = [{"id": "s1", "blocks": [{"kind": "activity", "ref": act["id"]}]}]
        isolated[0].pop("dialogue")
        isolated[0]["activities"] = [act]
        isolated[0]["consolidation"] = {"activities": []}
        result, _ = check_render(isolated, level)
        if not result.passed:
            gaps.append(f"{level}/{act['id']}: {result.reason}")
    assert not gaps, "\n".join(gaps)


def document_coverage_gaps(level, draft):
    """Keep block variants distinct; prose.text cannot stand in for tip.text."""
    schema = json.loads((ROOT / f"schemas/lesson-draft-{level}-v1.schema.json").read_text())
    blocks = {b["kind"]: b for step in draft["steps"] for b in step["blocks"]}
    cases = [
        (name, definition, blocks.get(definition["properties"]["kind"]["const"], {}))
        for name, definition in schema["$defs"].items()
        if name.startswith("block_")
    ]
    cases.extend(
        [
            ("step", schema["$defs"]["step"], draft["steps"][0]),
            ("dialogue", schema["properties"]["dialogue"], draft.get("dialogue", {})),
            ("consolidation", schema["properties"]["consolidation"], draft["consolidation"]),
        ]
    )
    gaps = []
    for name, definition, value in cases:
        expected = {
            p
            for p in schema_leaves(definition, document=schema)
            if p
            and not {"kind", "explains", "ref", "id", "speaker", "activities", "blocks"}.intersection(p)
            and next((part for part in reversed(p) if part != "*"), "") in expansion_fields()
        }
        actual = set(fixture_leaves(value))
        gaps.extend(name + "." + ".".join(p) for p in expected if p not in actual)
    return gaps


def test_fresh_schema_walk_rejects_an_unexercised_optional_translation():
    draft, *_ = maximal_draft("a1")
    draft["dialogue"].pop("translation_en")
    # This remains schema-valid. Coverage must independently refuse the omission.
    draft_validator("a1").validate(draft)
    assert "dialogue.translation_en.*" in document_coverage_gaps("a1", draft)


@pytest.mark.parametrize("kind", ["tip", "summary", "callout", "video"])
def test_fresh_schema_walk_rejects_an_unexercised_block_field(kind):
    draft, *_ = maximal_draft("a1")
    block = next(b for b in draft["steps"][0]["blocks"] if b["kind"] == kind)
    key = "lead_in" if kind == "video" else "text"
    block.pop(key)
    assert f"block_{kind}.{key}" in document_coverage_gaps("a1", draft)


def test_coverage_walk_follows_transitive_helpers(monkeypatch):
    # Add a field exclusively in a helper reached through another helper, not
    # in the expansion function or in a manually maintained helper allowlist.
    from scripts.build.fresh import assemble as module

    monkeypatch.setattr(coverage_probe_helper, "__module__", module.__name__)
    monkeypatch.setattr(coverage_probe_leaf, "__module__", module.__name__)
    monkeypatch.setattr(module, "string_key_answer", coverage_probe_helper)
    monkeypatch.setattr(module, "derive_record_kind", coverage_probe_leaf)
    assert "helper_only_coverage_field" in expansion_fields()


def coverage_probe_helper(*args):
    return assemble.derive_record_kind(*args)


def coverage_probe_leaf(*args):
    return {"helper_only_coverage_field": args}


@pytest.mark.parametrize("level", LEVELS)
@pytest.mark.parametrize("blank", [" ", "\t\n", "\u00a0"])
def test_translate_whitespace_choice_fails_live_activity_and_draft_schema(level, blank):
    from scripts.build.fresh.draft_schema import validate_draft

    inputs = maximal_draft(level)
    draft, plan, *_ = inputs
    types = {a["id"]: a["type"] for a in plan["lessons"][0]["activities"]}
    act = next(a for a in draft["activities"] if types[a["id"]] == "translate")
    definition = json.loads((ROOT / f"schemas/activities-{level}.schema.json").read_text())["definitions"][f"translate-{level}"]
    payload = {key: value for key, value in {**act, "type": "translate", "title": "Learner title"}.items() if key in definition["properties"]}
    jsonschema.Draft7Validator(definition).validate(payload)
    act["items"][0]["options"][0]["text"] = blank
    payload["items"] = act["items"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft7Validator(definition).validate(payload)
    with pytest.raises(jsonschema.ValidationError):
        draft_validator(level).validate(draft)
    assert any("pattern" in e.reason or "match" in e.reason for e in validate_draft(draft, level, activity_types=types))


@pytest.mark.parametrize("filename", ["activities-base.schema.json", *[f"activities-{level}.schema.json" for level in LEVELS]])
def test_every_choice_schema_rejects_whitespace_and_accepts_edge_spaces(filename):
    def choices(node):
        if isinstance(node, dict):
            for key, child in node.items():
                if key in {"options", "choices", "words", "letters", "syllables"} and isinstance(child, dict) and child.get("type") == "array":
                    yield child["items"]
                yield from choices(child)
        elif isinstance(node, list):
            for child in node:
                yield from choices(child)

    def texts(node):
        if node.get("type") == "string":
            yield node
        elif node.get("type") == "object" and "text" in node.get("properties", {}):
            yield node["properties"]["text"]
        for variant in node.get("oneOf", []) + node.get("anyOf", []):
            yield from texts(variant)

    schemas = [text for choice in choices(json.loads((ROOT / "schemas" / filename).read_text())) for text in texts(choice)]
    assert schemas
    for schema in schemas:
        validator = jsonschema.Draft7Validator(schema)
        for blank in ("", " ", "\n\t", "\u00a0"):
            assert not validator.is_valid(blank), schema
        validator.validate("  Learner choice  ")


@pytest.mark.parametrize("level", ["a2", "b1", "b2"])
@pytest.mark.parametrize("prefix", ["Story", "Text", "Reading", "Dialogue", "Conversation", "Passage"])
def test_instruction_heading_is_never_processed_as_story(level, prefix, render_environment):
    inputs = maximal_draft(level)
    types = {a["id"]: a["type"] for a in inputs[1]["lessons"][0]["activities"]}
    count = 0
    for activity in inputs[0]["activities"]:
        if types[activity["id"]] in assemble._PAGE_INSTRUCTION_FIELD:
            activity["instruction"] = f"{prefix} learner instruction."
            count += 1
    assert count > 0
    result, _ = check_render(inputs, level)
    assert result.passed, result.to_dict()
    assert result.artifacts["mdx"].count(f"{prefix} learner instruction.") == count


@pytest.mark.parametrize("prefix", ["Story", "Text", "Reading", "Dialogue", "Conversation", "Passage"])
def test_story_parser_keeps_a_multiline_activity_payload_byte_for_byte(prefix):
    mdx = f'### {prefix} instruction\n\n<Cloze\n  text="First line"\n  instruction="Second line"\n/>\n'
    assert process_story_sections(mdx) == mdx


@pytest.mark.parametrize(
    "translation", ['He said "hello".', "Don't lose a backslash: \\ or a newline:\nsecond line.", "<br /> & support"]
)
def test_fresh_dialogue_translation_roundtrips_escaped_bytes(translation, render_environment):
    inputs = maximal_draft("a1")
    inputs[0]["dialogue"]["translation_en"][0] = translation
    result, expanded = check_render(inputs, "a1")
    assert result.passed, result.to_dict()
    spans = result.artifacts["provenance"]["spans"]
    idx = next(i for i, u in enumerate(expanded["units"]) if u["block"] == "dialogue_translation_0")
    assert spans[idx]["text"] == translation


def test_fresh_story_spacing_preserves_a_rendered_reading_activity():
    mdx = '### Reading\n\n<ReadingActivity title="Read this passage." />\n'
    assert process_story_sections(mdx) == mdx
    assert (
        process_story_sections("### Story\nFirst paragraph.\nSecond paragraph.")
        == "### Story\n\nFirst paragraph.\n\nSecond paragraph."
    )


@pytest.mark.parametrize(
    "typ", ["cloze", "essay-response", "critical-analysis", "comparative-study", "authorial-intent", "reading"]
)
def test_fresh_instruction_lookup_requires_the_exact_visible_title(typ):
    field = "_heading" if typ == "cloze" else "title"
    assert assemble.page_field_text(typ, {field: "Read this."}, None, "instruction") == "Read this."
    assert assemble.page_field_text(typ, {}, None, "instruction") is None
    assert assemble.page_field_text(typ, {field: "Other words."}, None, "instruction") == "Other words."


@pytest.mark.parametrize("with_options", [True, False])
def test_fresh_translate_candidate_edges_match_the_parser(with_options, render_environment):
    inputs = maximal_draft("a1")
    act = next(
        a
        for a in inputs[0]["activities"]
        if a["id"] == next(p["id"] for p in inputs[1]["lessons"][0]["activities"] if p["type"] == "translate")
    )
    item = act["items"][0]
    if with_options:
        for option in item["options"]:
            option["text"] = "  " + option["text"] + "  "
        item["answer"] = item["options"][0]["text"]
    else:
        item.pop("options")
        item.pop("option_why", None)
        item["answer"] = "  Candidate answer  "
    draft_validator("a1").validate(inputs[0])
    result, _ = check_render(inputs, "a1")
    assert result.passed, result.to_dict()


@pytest.mark.parametrize("level", LEVELS)
@pytest.mark.site_toolchain
def test_fresh_every_plan_and_draft_text_field_is_mdx_safe(level, render_environment):
    from scripts.build.mdx_render_gate import check_mdx_render

    inputs = maximal_draft(level)
    inputs[1]["lessons"][0]["reading_passages"] = [
        {"title": "Read this", "genre": "Passage", "reading_slug": "fixture-reading"}
    ]
    # Structural identities, enum selectors, references, URLs and tag strings
    # are deliberately fixed. Every learner/writer text leaf receives the same
    # suffix, so text-valued answer keys keep matching their options.
    structural = {
        "id",
        "type",
        "kind",
        "ref",
        "explains",
        "evidence",
        "video",
        "word_ref",
        "word_id",
        "error_ref",
        "mode",
        "placement",
        "module",
        "tests_feature",
        "tests_features",
        "learner",
        "record",
        "lemma_ref",
        "gap_id",
        "url",
        "reading_slug",
        "forms",
        "pos",
        "source",
        "tags",
        "image",
        "lesson_lock_entry_sha256",
        "pack_lock_sha256",
        "words_lock_sha256",
        "style_card_sha256",
        "plan_entry_sha256",
        "state_sha256",
        "inventory_sha256",
        "style_sha256",
        "learner_state_sha256",
    }
    visited = []

    def inject(value, path=()):
        if isinstance(value, dict):
            return {k: inject(v, (*path, k)) for k, v in value.items()}
        if isinstance(value, list):
            return [inject(v, (*path, i)) for i, v in enumerate(value)]
        keys = [p for p in path if isinstance(p, str)]
        if isinstance(value, str) and not any(k in structural or k.endswith("sha256") for k in keys):
            if value in {"ok", "evidence_gap"} or value.startswith(("W-", "P-", "T-", "EX-", "E-", "V-")):
                return value
            visited.append(path)
            if keys[-1] == "image" and value.endswith(".svg"):
                return value.removesuffix(".svg") + " { } < > ` $.svg"
            return value + " { } < > ` $"
        return value

    inputs = (inject(inputs[0]), inject(inputs[1]), inputs[2], inputs[3])
    assert any("instruction" in path for path in visited)
    assert any("focus" in path for path in visited)
    assert any("title" in path for path in visited)
    with patch("scripts.generate_mdx.core.reading_href_for", return_value="/readings/fixture-reading/"):
        result, _ = check_render(inputs, level)
    assert result.passed, result.to_dict()
    report = check_mdx_render(result.artifacts["mdx"])
    assert report["passed"] is True, report["failures"]


def test_fresh_plan_directives_never_supply_activity_headings(render_environment):
    inputs = maximal_draft("a1")
    for activity in inputs[1]["lessons"][0]["activities"]:
        activity["focus"] = "WRITER DIRECTIVE: consult evidence {kind: dialogue}"
    result, _ = check_render(inputs, "a1")
    assert result.passed, result.to_dict()
    assert "WRITER DIRECTIVE" not in result.artifacts["mdx"]
