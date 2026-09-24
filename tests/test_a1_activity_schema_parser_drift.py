"""Schema/parser drift guard for the A1 activity schema (#8716).

For every A1 activity type, build a minimal valid item from the schema's
required fields (one variant per ``anyOf`` required-alternative), run it
through ``ActivityParser`` and ``to_mdx`` and assert that no free-text field
the schema requires is silently dropped before it reaches the JSX layer.

Types whose drift is known and needs component work (not a field mapping)
are listed in ``KNOWN_DRIFT``; the test fails when an entry stops being
true, so the list cannot go stale.
"""

from __future__ import annotations

import dataclasses
import itertools
import json
import re
import sys
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from yaml_activities import ActivityParser

from scripts.build.activity_renderer import ImageToLetterShapeError

SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "activities-a1.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
DEFS = SCHEMA["definitions"]
VALIDATOR = Draft7Validator(SCHEMA)
SENTINEL = re.compile(r"SENT\d+_\w+")

# type -> required schema fields the parser/MDX path still drops (see PR #8716).
KNOWN_DRIFT: dict[str, set[str]] = {
    "anagram": {"explanation"},
    "count-syllables": {"explanation"},
    "divide-words": {"explanation"},
    "unjumble": {"explanation"},
    "watch-and-repeat": {"explanation"},
}
# Provenance metadata for the build engine, never rendered to the learner.
INTERNAL_ONLY = {"error_ref"}
# Types the parser rejects outright (loud, not silent); tracked separately.
PARSER_REJECTS = {
    "letter-grid": "parser additionally requires emoji and key_word",
    "phrase-table": "ActivityParser has no phrase-table parser",
}


def _variants(node: dict, path: str, counter) -> list:
    """Minimal valid instances of ``node``; one per anyOf-required alternative."""
    if "$ref" in node:
        return _variants(DEFS[node["$ref"].split("/")[-1]], path, counter)
    for key in ("oneOf", "anyOf"):
        if key in node and "properties" not in node:
            return _variants(node[key][0], path, counter)
    if "const" in node:
        return [node["const"]]
    if node.get("pattern") == "^E-[0-9]{3,}$":
        return ["E-001"]
    if "enum" in node:
        return [node["enum"][0]]
    kind = node.get("type")
    if kind == "object":
        props = node.get("properties", {})
        groups = [node.get("anyOf", []), *(a.get("anyOf", []) for a in node.get("allOf", []))]
        groups = [[a["required"] for a in g if "required" in a] for g in groups if g]
        alternatives = [list(itertools.chain.from_iterable(combo)) for combo in itertools.product(*groups)] or [[]]
        out = []
        for alt in alternatives:
            fields = list(dict.fromkeys([*node.get("required", []), *alt]))
            per_field = [
                [(name, v) for v in _variants(props.get(name, {"type": "string"}), name, counter)] for name in fields
            ]
            out.extend(dict(combo) for combo in itertools.product(*per_field))
        return out
    if kind == "array":
        size = max(node.get("minItems", 1), 1)
        return [
            [_fresh(v, counter) for _ in range(size)]
            for v in _variants(node.get("items", {"type": "string"}), path, counter)
        ]
    if kind == "integer":
        return [max(node.get("minimum", 0), 0)]
    if kind == "boolean":
        return [True]
    return [f"SENT{next(counter)}_{path}"]


def _fresh(value, counter):
    """Deep-copy ``value`` giving every sentinel string a new number."""
    if isinstance(value, dict):
        return {k: _fresh(v, counter) for k, v in value.items()}
    if isinstance(value, list):
        return [_fresh(v, counter) for v in value]
    if isinstance(value, str) and SENTINEL.fullmatch(value):
        return f"SENT{next(counter)}_{value.split('_', 1)[1]}"
    return value


def _cases() -> list[tuple[str, int, dict]]:
    cases = []
    for name, node in DEFS.items():
        counter = itertools.count(1)
        for index, instance in enumerate(_variants(node, "", counter)):
            for row in instance.get("items", []) if isinstance(instance, dict) else []:
                # A text `answer` must name one of the choices to be meaningful.
                for choices in ("words", "options"):
                    if isinstance(row, dict) and "answer" in row and choices in row:
                        row["answer"] = row[choices][0]
            cases.append((name.removesuffix("-a1"), index, instance))
    return cases


CASES = _cases()


def test_generated_examples_are_schema_valid():
    for name, _, instance in CASES:
        assert VALIDATOR.is_valid([instance]), f"{name}: generated example is not schema-valid"


@pytest.mark.parametrize(
    ("activity_type", "index", "example"),
    [c for c in CASES if c[0] not in PARSER_REJECTS],
    ids=[f"{c[0]}-{c[1]}" for c in CASES if c[0] not in PARSER_REJECTS],
)
def test_parser_keeps_every_required_field(activity_type, index, example):
    parser = ActivityParser()
    activity = parser._parse_activity(example)
    parsed = json.dumps(dataclasses.asdict(activity), ensure_ascii=False)
    mdx = parser.to_mdx([activity])
    sentinels = {m.group(0).split("_", 1)[1]: m.group(0) for m in SENTINEL.finditer(json.dumps(example))}
    for field in INTERNAL_ONLY:
        sentinels.pop(field, None)
    dropped = {field for field, marker in sentinels.items() if marker not in parsed or marker not in mdx}
    assert dropped == KNOWN_DRIFT.get(activity_type, set()), (
        f"{activity_type}: required fields dropped by ActivityParser/to_mdx = {sorted(dropped)}; "
        f"known drift = {sorted(KNOWN_DRIFT.get(activity_type, set()))}"
    )


@pytest.mark.parametrize("activity_type", sorted(PARSER_REJECTS))
def test_parser_rejections_stay_loud(activity_type):
    example = next(inst for name, _, inst in CASES if name == activity_type)
    with pytest.raises((ValueError, KeyError, TypeError)):
        ActivityParser()._parse_activity(example)


# ---------------------------------------------------------------------------
# image-to-letter: schema shape and legacy shape both reach the component
# ---------------------------------------------------------------------------


def _itl_mdx(items: list[dict], **extra) -> tuple[str, list[dict]]:
    parser = ActivityParser()
    activity = parser._parse_activity(
        {"type": "image-to-letter", "instruction": "Pick the first letter.", "items": items, **extra}
    )
    mdx = parser.to_mdx([activity])
    payload = re.search(r"items=\{JSON\.parse\(`(.*?)`\)\}", mdx, re.S).group(1)
    return mdx, json.loads(payload)


def test_image_to_letter_schema_shape_reaches_component():
    mdx, items = _itl_mdx([{"image": "🍎", "letter": "Я", "options": ["А", "Я", "О"], "explanation": "Яблуко."}])
    assert items == [{"emoji": "🍎", "answer": "Я", "distractors": ["А", "О"], "explanation": "Яблуко."}]
    assert "<ImageToLetter" in mdx
    assert 'instruction={"Pick the first letter."}' in mdx


def test_image_to_letter_legacy_shape_reaches_component():
    _, items = _itl_mdx([{"emoji": "🍎", "answer": "Я", "distractors": ["А", "О"], "note": "n"}])
    assert items == [{"emoji": "🍎", "answer": "Я", "distractors": ["А", "О"], "note": "n"}]


def test_image_to_letter_options_never_duplicate_the_answer():
    _, items = _itl_mdx([{"image": "🍎", "letter": "Я", "options": ["Я", "А", "А", "О"]}])
    assert items[0]["distractors"] == ["А", "О"]


@pytest.mark.parametrize(
    "bad",
    [
        {"word": "яблуко"},
        {"image": "🍎"},
        {"letter": "Я", "options": ["А", "Я"]},
        {"emoji": "🍎"},
        "not-a-mapping",
    ],
)
def test_image_to_letter_item_with_neither_shape_raises_named_error(bad):
    with pytest.raises(ImageToLetterShapeError, match="image-to-letter item 0"):
        _itl_mdx([bad])


def test_fresh_renderer_and_parser_agree_on_image_to_letter():
    from scripts.build.activity_renderer import _render_image_to_letter

    act = {
        "type": "image-to-letter",
        "instruction": "Pick the first letter.",
        "items": [{"image": "🍎", "letter": "Я", "options": ["А", "Я", "О"], "explanation": "e"}],
    }
    rendered = _render_image_to_letter(act)
    assert '"answer": "Я"' in rendered or '"answer":"Я"' in rendered
    assert rendered.count('"Я"') == 1  # the letter is not repeated inside distractors
    # instruction renders as the instruction paragraph, not as the header title
    assert 'instruction={"Pick the first letter."}' in rendered
    assert "title=" not in rendered
