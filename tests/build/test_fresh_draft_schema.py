"""E1 of the create-path engine (#8397 comment 5773128681): the lesson-draft schema and its validator.

Covers the brief's E1.5 list: a valid draft per level validates; each §4 gap invariant fails its
fixture; each block kind's required fields; the markup regex; `explain` (wrong key) fails; the
generated `$ref`s resolve for every type in each level allowlist; the generate-and-check pattern.
"""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pytest
import yaml
from referencing import Registry

from scripts.build.fresh import gen_draft_schemas
from scripts.build.fresh.draft_schema import (
    CODE_CHECKS,
    INLINE_MARKUP_RE,
    DraftValidationError,
    activity_definitions,
    assert_valid_draft,
    draft_validator,
    validate_draft,
)

REPO = Path(__file__).resolve().parents[2]
SCHEMAS = REPO / "schemas"
FIXTURES = Path(__file__).parent / "fixtures" / "fresh"
LEVELS = gen_draft_schemas.LEVELS


def load_fixture(level: str) -> tuple[dict, dict[str, str]]:
    draft = yaml.safe_load((FIXTURES / f"lesson-draft-{level}-valid.yaml").read_text(encoding="utf-8"))
    types = json.loads((FIXTURES / f"lesson-draft-{level}-types.json").read_text(encoding="utf-8"))
    return draft, types


def checks(errors) -> set[str]:
    return {e.check for e in errors}


# --- a valid draft per level -------------------------------------------------------------------


@pytest.mark.parametrize("level", LEVELS)
def test_valid_draft_per_level_validates(level: str) -> None:
    draft, types = load_fixture(level)
    assert validate_draft(draft, level) == []
    assert validate_draft(draft, level, activity_types=types) == []
    assert validate_draft(draft, None) == [], "the level-agnostic schema accepts every level's valid draft"
    assert_valid_draft(draft, level, activity_types=types)


@pytest.mark.parametrize("level", LEVELS)
def test_fixture_uses_every_block_kind_once_or_more(level: str) -> None:
    draft, _ = load_fixture(level)
    kinds = {b["kind"] for s in draft["steps"] for b in s["blocks"]}
    expected = {"prose", "example", "quote", "paradigm", "table", "pronunciation", "culture", "tip", "summary", "callout", "video", "dialogue", "activity"}
    if level in ("a1", "a2"):
        expected.add("bilingual")
    assert expected <= kinds


def test_wrong_level_module_prefix_fails() -> None:
    draft, _ = load_fixture("a1")
    draft["lesson"]["module"] = "a2/fixture-module"
    assert any(e.path == "/lesson/module" for e in validate_draft(draft, "a1"))


def test_inputs_need_all_six_hashes() -> None:
    draft, _ = load_fixture("a1")
    del draft["inputs"]["style_card_sha256"]
    assert any("style_card_sha256" in e.reason for e in validate_draft(draft, "a1"))
    draft, _ = load_fixture("a1")
    draft["inputs"]["pack_lock"] = "abc"
    assert any(e.path == "/inputs/pack_lock" for e in validate_draft(draft, "a1"))


def test_unknown_top_level_key_fails() -> None:
    draft, _ = load_fixture("a1")
    draft["notes_to_reviewer"] = "none"
    assert any("notes_to_reviewer" in e.reason for e in validate_draft(draft, "a1"))


# --- §4 gap invariants ---------------------------------------------------------------------------


def _gap(step: str = "s2") -> dict:
    return {"step": step, "need": "example", "detail": "No EX- record shows the contrast for the step."}


def test_gap_ok_with_nonempty_gaps_fails() -> None:
    draft, _ = load_fixture("a1")
    draft["gaps"] = [_gap()]
    errors = validate_draft(draft, "a1")
    assert any(e.check == "schema" and e.path == "/gaps" for e in errors)


def test_gap_evidence_gap_with_empty_gaps_fails() -> None:
    draft, _ = load_fixture("a1")
    draft["status"] = "evidence_gap"
    errors = validate_draft(draft, "a1")
    assert any(e.check == "schema" and e.path == "/gaps" for e in errors)


def test_gap_ok_with_an_empty_step_fails() -> None:
    draft, _ = load_fixture("a1")
    draft["steps"][1]["blocks"] = []
    del draft["dialogue"]
    errors = validate_draft(draft, "a1")
    assert any(e.check == "schema" and e.path == "/steps/1/blocks" for e in errors)


def test_gap_step_must_exist(a1_gap_draft: dict) -> None:
    a1_gap_draft["gaps"][0]["step"] = "s9"
    a1_gap_draft["steps"][1]["blocks"] = [{"kind": "tip", "text": "filled again"}]
    assert {"gap_steps_exist", "gap_steps_empty"} <= checks(validate_draft(a1_gap_draft, "a1"))


def test_gap_named_step_must_be_empty(a1_gap_draft: dict) -> None:
    a1_gap_draft["steps"][1]["blocks"] = [{"kind": "tip", "text": "filled although a gap names it"}]
    assert checks(validate_draft(a1_gap_draft, "a1")) == {"gap_steps_empty"}


def test_gap_unnamed_step_must_not_be_empty(a1_gap_draft: dict) -> None:
    a1_gap_draft["steps"][0]["blocks"] = []
    found = checks(validate_draft(a1_gap_draft, "a1"))
    assert "gap_steps_empty" in found
    assert found <= {"gap_steps_empty", "activity_declared_used"}, "emptying s1 also un-places its activities; nothing else"


def test_gap_declared_correctly_passes(a1_gap_draft: dict) -> None:
    assert validate_draft(a1_gap_draft, "a1") == []


def test_gap_need_is_the_contract_enum() -> None:
    draft, _ = load_fixture("a1")
    draft["status"] = "evidence_gap"
    draft["steps"][1]["blocks"] = []
    del draft["dialogue"]
    draft["gaps"] = [{"step": "s2", "need": "inspiration", "detail": "x"}]
    assert any(e.path == "/gaps/0/need" for e in validate_draft(draft, "a1"))


@pytest.fixture
def a1_gap_draft() -> dict:
    draft, _ = load_fixture("a1")
    draft["status"] = "evidence_gap"
    draft["steps"][1]["blocks"] = []
    del draft["dialogue"]
    draft["gaps"] = [_gap("s2")]
    return draft


# --- block kinds and their required fields -------------------------------------------------------

BLOCK_REQUIRED = {
    "prose": {"text", "explains"},
    "example": {"ref"},
    "quote": {"ref"},
    "paradigm": {"ref"},
    "table": {"rows", "explains"},
    "pronunciation": {"text", "explains"},
    "bilingual": {"uk", "en"},
    "culture": {"text", "explains"},
    "tip": {"text"},
    "summary": {"text"},
    "callout": {"text"},
    "video": {"ref"},
    "dialogue": set(),
    "activity": {"ref"},
}


def _find_block(draft: dict, kind: str) -> tuple[int, int, dict]:
    for s_index, step in enumerate(draft["steps"]):
        for b_index, block in enumerate(step["blocks"]):
            if block["kind"] == kind:
                return s_index, b_index, block
    raise AssertionError(kind)


@pytest.mark.parametrize("kind,field", [(k, f) for k, fields in BLOCK_REQUIRED.items() for f in sorted(fields)])
def test_block_required_field(kind: str, field: str) -> None:
    draft, _ = load_fixture("a1")
    s_index, b_index, block = _find_block(draft, kind)
    del block[field]
    errors = validate_draft(draft, "a1")
    assert any(e.check == "schema" and e.path.startswith(f"/steps/{s_index}/blocks/{b_index}") for e in errors)


@pytest.mark.parametrize("kind", sorted(BLOCK_REQUIRED))
def test_block_rejects_extra_field(kind: str) -> None:
    draft, _ = load_fixture("a1")
    s_index, b_index, block = _find_block(draft, kind)
    block["note"] = "no field for commentary"
    assert any(e.path.startswith(f"/steps/{s_index}/blocks/{b_index}") for e in validate_draft(draft, "a1"))


def test_unknown_block_kind_fails() -> None:
    draft, _ = load_fixture("a1")
    draft["steps"][0]["blocks"].append({"kind": "lead_in", "text": "lead_in is a field, not a block kind"})
    assert any(e.path.startswith("/steps/0/blocks/") for e in validate_draft(draft, "a1"))


def test_lead_in_is_a_field_of_step_video_and_consolidation() -> None:
    draft, _ = load_fixture("a1")
    assert "lead_in" in draft["steps"][1]
    assert "lead_in" in _find_block(draft, "video")[2]
    assert "lead_in" in draft["consolidation"]
    assert validate_draft(draft, "a1") == []


@pytest.mark.parametrize("kind", ["prose", "table", "pronunciation", "culture"])
def test_explains_must_be_non_empty_record_ids(kind: str) -> None:
    draft, _ = load_fixture("a1")
    _, _, block = _find_block(draft, kind)
    block["explains"] = []
    assert validate_draft(draft, "a1")
    block["explains"] = ["G-a1-001"]
    assert validate_draft(draft, "a1"), "a grammar-point id is not a pack record"


@pytest.mark.parametrize("kind,bad_ref", [("example", "T-001"), ("quote", "EX-001"), ("paradigm", "W-012"), ("video", "EX-002"), ("activity", "s1")])
def test_ref_pattern_per_kind(kind: str, bad_ref: str) -> None:
    draft, _ = load_fixture("a1")
    _, _, block = _find_block(draft, kind)
    block["ref"] = bad_ref
    assert validate_draft(draft, "a1")


def test_tip_may_not_carry_explains() -> None:
    draft, _ = load_fixture("a1")
    _, _, block = _find_block(draft, "tip")
    block["explains"] = ["T-003"]
    assert validate_draft(draft, "a1"), "connective blocks have no field for a claim's record (§6)"


# --- draft-internal code checks -----------------------------------------------------------------


def test_bilingual_unequal_length_fails() -> None:
    draft, _ = load_fixture("a1")
    _, _, block = _find_block(draft, "bilingual")
    block["en"] = block["en"][:1]
    assert checks(validate_draft(draft, "a1")) == {"bilingual_equal_length"}


def test_translation_en_unequal_length_fails() -> None:
    draft, _ = load_fixture("a1")
    draft["dialogue"]["translation_en"] = draft["dialogue"]["translation_en"][:1]
    assert checks(validate_draft(draft, "a1")) == {"translation_en_length"}


def test_translation_en_absent_as_a_whole_passes() -> None:
    draft, _ = load_fixture("a1")
    del draft["dialogue"]["translation_en"]
    assert validate_draft(draft, "a1") == []


def test_dialogue_block_and_top_level_dialogue_go_together() -> None:
    draft, _ = load_fixture("a1")
    del draft["dialogue"]
    assert checks(validate_draft(draft, "a1")) == {"dialogue_block_once"}
    draft, _ = load_fixture("a1")
    draft["steps"][0]["blocks"].append({"kind": "dialogue"})
    assert checks(validate_draft(draft, "a1")) == {"dialogue_block_once"}


def test_activity_refs_must_be_declared_and_placed_once() -> None:
    draft, _ = load_fixture("a1")
    draft["consolidation"]["activities"].append("a9")
    assert checks(validate_draft(draft, "a1")) == {"activity_ref_declared"}
    draft, _ = load_fixture("a1")
    draft["consolidation"]["activities"].append("a1")
    assert checks(validate_draft(draft, "a1")) == {"activity_declared_used"}
    draft, _ = load_fixture("a1")
    draft["consolidation"]["activities"].remove("a4")
    assert checks(validate_draft(draft, "a1")) == {"activity_declared_used"}


def test_duplicate_ids_fail() -> None:
    draft, _ = load_fixture("a1")
    draft["steps"][1]["id"] = "s1"
    assert "step_ids_unique" in checks(validate_draft(draft, "a1"))
    draft, _ = load_fixture("a1")
    draft["activities"][1]["id"] = "a1"
    assert "activity_ids_unique" in checks(validate_draft(draft, "a1"))


def test_code_checks_are_documented() -> None:
    names = [name for name, _ in CODE_CHECKS]
    assert len(names) == len(set(names))
    assert {"gap_steps_exist", "gap_steps_empty", "bilingual_equal_length", "translation_en_length", "no_combining_accent", "inline_markup", "activity_items_per_type"} <= set(names)


# --- the inline markup regex and the accent ban ---------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "Plain English narration.",
        "A term {{uk:слово}} inside English.",
        "An incidental word {{gloss:W-040}} glossed by the engine.",
        "Two tokens {{uk:слово}} and {{gloss:W-7}} side by side.",
    ],
)
def test_markup_regex_accepts(text: str) -> None:
    assert INLINE_MARKUP_RE.fullmatch(text)


@pytest.mark.parametrize(
    "text",
    [
        "{{uk:{{gloss:W-040}}}}",
        "{{gloss:{{uk:x}}}}",
        "{{uk:a {{uk:b}} c}}",
        "{{gloss:W-040 }}",
        "{{gloss:040}}",
        "{{UK:x}}",
        "{{uk:}}",
        "{{uk:x}",
        "a { b",
        "a } b",
        "{{stress:x}}",
        "Приві́т",
        "{{uk:Приві́т}}",
        "гра̀ве",
    ],
)
def test_markup_regex_rejects(text: str) -> None:
    assert not INLINE_MARKUP_RE.fullmatch(text)


def test_accent_in_narration_fails_schema_gate() -> None:
    draft, _ = load_fixture("a1")
    draft["steps"][0]["blocks"][0]["text"] = "Say {{uk:Приві́т}} first."
    errors = validate_draft(draft, "a1")
    assert any(e.check == "schema" and e.path.startswith("/steps/0/blocks/0") for e in errors)


def test_accent_inside_an_activity_item_fails_by_code() -> None:
    draft, types = load_fixture("a1")
    draft["activities"][0]["items"][0]["explanation"] = "with an accent: о́"
    assert checks(validate_draft(draft, "a1", activity_types=types)) == {"no_combining_accent"}


def test_stray_brace_inside_an_activity_string_fails_by_code() -> None:
    draft, types = load_fixture("a1")
    draft["activities"][0]["items"][0]["explanation"] = "{{uk:{{gloss:W-1}}}}"
    assert checks(validate_draft(draft, "a1", activity_types=types)) == {"inline_markup"}


def test_speaker_may_not_carry_markup() -> None:
    draft, _ = load_fixture("a1")
    draft["dialogue"]["lines"][0]["speaker"] = "{{uk:x}}"
    assert any(e.path == "/dialogue/lines/0/speaker" for e in validate_draft(draft, "a1"))


# --- activities: the per-type binding -------------------------------------------------------------


def test_explain_wrong_key_fails() -> None:
    draft, types = load_fixture("a1")
    item = draft["activities"][0]["items"][0]
    item["explain"] = item.pop("explanation")
    untyped = validate_draft(draft, "a1")
    assert untyped and all(e.check == "schema" for e in untyped)
    typed = validate_draft(draft, "a1", activity_types=types)
    assert typed and all(e.check == "activity_items_per_type" for e in typed)
    assert any("explanation" in e.reason or "explain" in e.reason for e in typed)


def test_activity_may_not_repeat_type_or_placement() -> None:
    for key in ("type", "placement", "title"):
        draft, _ = load_fixture("a1")
        draft["activities"][0][key] = "quiz"
        assert any(e.path.startswith("/activities/0") for e in validate_draft(draft, "a1")), key


def test_activity_payload_bound_to_plan_type() -> None:
    draft, types = load_fixture("a1")
    types = dict(types, a1="true-false")
    errors = validate_draft(draft, "a1", activity_types=types)
    assert errors and all(e.check == "activity_items_per_type" for e in errors)


def test_activity_without_a_type_in_the_map_fails() -> None:
    draft, types = load_fixture("a1")
    types = {k: v for k, v in types.items() if k != "a2"}
    assert any(e.check == "activity_items_per_type" and "no type" in e.reason for e in validate_draft(draft, "a1", activity_types=types))


def test_activity_type_outside_level_allowlist_fails() -> None:
    draft, types = load_fixture("a1")
    types = dict(types, a1="cloze")
    assert any("allowlist" in e.reason for e in validate_draft(draft, "a1", activity_types=types))


def test_error_correction_item_needs_error_ref() -> None:
    draft, types = load_fixture("a1")
    item = next(a for a in draft["activities"] if types[a["id"]] == "error-correction")["items"][0]
    del item["error_ref"]
    assert validate_draft(draft, "a1")
    item["error_ref"] = "E-1"
    assert validate_draft(draft, "a1")
    item["error_ref"] = "E-001"
    assert validate_draft(draft, "a1") == []


def test_cloze_blank_markers_are_allowed_inside_activity_strings() -> None:
    draft, types = load_fixture("a2")
    cloze = next(a for a in draft["activities"] if types[a["id"]] == "cloze")
    assert "{{1}}" in cloze["text"]
    assert validate_draft(draft, "a2", activity_types=types) == []


# --- the generated schemas and their references -------------------------------------------------


@pytest.mark.parametrize("level", LEVELS)
def test_generated_refs_resolve_for_every_type_in_the_level_allowlist(level: str) -> None:
    schema = json.loads((SCHEMAS / f"lesson-draft-{level}-v1.schema.json").read_text(encoding="utf-8"))
    level_schema = json.loads((SCHEMAS / f"activities-{level}.schema.json").read_text(encoding="utf-8"))
    allowlist = gen_draft_schemas.level_activity_types(level, level_schema)
    assert set(schema["$defs"]["activity_types"]) == set(allowlist)
    resolver = Registry(retrieve=draft_validator(level)._resolver._registry._retrieve).resolver(base_uri=schema["$id"])
    for type_name, entry in schema["$defs"]["activity_types"].items():
        assert entry == {"$ref": f"activities-{level}.schema.json#/definitions/{type_name}-{level}"}
        resolved = resolver.lookup(entry["$ref"]).contents
        assert resolved.get("required") and "type" in resolved["required"]
    for key, entry in schema["$defs"]["activity"]["properties"].items():
        if key in ("id", "instruction"):
            continue
        for ref in entry["anyOf"]:
            assert resolver.lookup(ref["$ref"]).contents


def test_level_allowlist_is_the_definitions_set() -> None:
    for level in LEVELS:
        level_schema = json.loads((SCHEMAS / f"activities-{level}.schema.json").read_text(encoding="utf-8"))
        assert {f"{t}-{level}" for t in activity_definitions(level)} == set(level_schema["definitions"])


def test_generated_schemas_are_valid_2020_12() -> None:
    for level in (*LEVELS, None):
        validator = draft_validator(level)
        assert validator.schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert validator.schema.get("additionalProperties") is False
        assert validator.META_SCHEMA["$id"] == "https://json-schema.org/draft/2020-12/schema"


def test_check_passes_on_committed_files() -> None:
    assert gen_draft_schemas.main(["--check"]) == 0


def test_check_fails_when_a_committed_file_is_stale(tmp_path: Path) -> None:
    shutil.copytree(SCHEMAS, tmp_path / "schemas")
    target = tmp_path / "schemas" / "lesson-draft-a1-v1.schema.json"
    target.write_text(target.read_text(encoding="utf-8").replace('"minimum": 1', '"minimum": 2', 1), encoding="utf-8")
    assert gen_draft_schemas.main(["--check", "--schemas-dir", str(tmp_path / "schemas")]) == 1
    assert gen_draft_schemas.main(["--write", "--schemas-dir", str(tmp_path / "schemas")]) == 0
    assert gen_draft_schemas.main(["--check", "--schemas-dir", str(tmp_path / "schemas")]) == 0


def test_check_fails_when_a_level_schema_changes(tmp_path: Path) -> None:
    shutil.copytree(SCHEMAS, tmp_path / "schemas")
    level_path = tmp_path / "schemas" / "activities-b2.schema.json"
    level_schema = json.loads(level_path.read_text(encoding="utf-8"))
    level_schema["definitions"]["quiz-b2"]["properties"]["hint"] = {"type": "string"}
    level_path.write_text(json.dumps(level_schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    assert gen_draft_schemas.main(["--check", "--schemas-dir", str(tmp_path / "schemas")]) == 1


def test_generator_refuses_a_definition_outside_the_naming_rule(tmp_path: Path) -> None:
    shutil.copytree(SCHEMAS, tmp_path / "schemas")
    level_path = tmp_path / "schemas" / "activities-a2.schema.json"
    level_schema = json.loads(level_path.read_text(encoding="utf-8"))
    level_schema["definitions"]["stray"] = copy.deepcopy(level_schema["definitions"]["quiz-a2"])
    level_path.write_text(json.dumps(level_schema), encoding="utf-8")
    assert gen_draft_schemas.main(["--check", "--schemas-dir", str(tmp_path / "schemas")]) == 2


def test_assert_valid_draft_raises_with_every_error() -> None:
    draft, _ = load_fixture("b1")
    draft["status"] = "evidence_gap"
    with pytest.raises(DraftValidationError) as info:
        assert_valid_draft(draft, "b1")
    assert info.value.errors and info.value.errors[0].as_dict()["check"] == "schema"
