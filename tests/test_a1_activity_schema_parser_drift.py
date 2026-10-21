"""Schema/parser drift guard for the A1 activity schema (#8716).

For every A1 activity type, build a minimal valid item from the schema's
required fields (one variant per ``anyOf`` required-alternative and per
``oneOf``/``anyOf`` branch), push it through BOTH MDX emitters --
``ActivityParser.to_mdx`` and ``activity_renderer.render_activity_to_jsx`` --
and assert that no free-text field the schema requires is silently dropped
before it reaches the JSX layer.

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

from scripts.build.activity_renderer import (
    GroupSortNameError,
    ImageToLetterShapeError,
    QuizCorrectnessError,
    group_sort_group_name,
    image_to_letter_image_kind,
    quiz_correct_indices,
    render_activity_to_jsx,
)
from yaml_activities import ActivityParser

SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "activities-a1.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
DEFS = SCHEMA["definitions"]
VALIDATOR = Draft7Validator(SCHEMA)
SENTINEL = re.compile(r"SENT\d+_\w+")

# type -> required schema fields the parser/MDX path still drops (see PR #8716).
KNOWN_DRIFT: dict[str, set[str]] = {}
# Provenance metadata for the build engine, never rendered to the learner.
INTERNAL_ONLY = {"error_ref"}


def _schema_branch_paths(node, path: str = "") -> set[str]:
    """Every ``oneOf``/``anyOf`` branch path in ``node``, walked from the schema itself."""
    found: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            if key in ("oneOf", "anyOf") and isinstance(value, list):
                found.update(f"{path}/{key}[{i}]" for i in range(len(value)))
            found |= _schema_branch_paths(value, f"{path}/{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            found |= _schema_branch_paths(value, f"{path}[{i}]")
    return found


def _variants(node: dict, path: str, counter, where: str) -> list[tuple[object, frozenset[str]]]:
    """Minimal instances of ``node`` paired with the branch paths each was built for.

    One instance per ``oneOf``/``anyOf`` branch; ``where`` is the schema path of
    ``node`` (the same naming ``_schema_branch_paths`` uses). Instances that a
    branch's extra constraint leaves invalid are dropped by ``_cases``.
    """
    if "$ref" in node:
        name = node["$ref"].split("/")[-1]
        return _variants(DEFS[name], path, counter, name)
    for key in ("oneOf", "anyOf"):
        if key in node and "properties" not in node:
            return [
                (value, tags | {f"{where}/{key}[{i}]"})
                for i, branch in enumerate(node[key])
                for value, tags in _variants(branch, path, counter, f"{where}/{key}[{i}]")
            ]
    if "const" in node:
        return [(node["const"], frozenset())]
    if node.get("pattern") == "^E-[0-9]{3,}$":
        return [("E-001", frozenset())]
    if path == "image" or "png|jpe?g|webp|svg" in node.get("pattern", ""):
        return [(f"SENT{next(counter)}_{path}.svg", frozenset())]
    if "enum" in node:
        return [(node["enum"][0], frozenset())]
    kind = node.get("type")
    if kind == "object":
        props = node.get("properties", {})
        # Each anyOf (on the node or under allOf) contributes one alternative
        # per branch; a branch without ``required`` adds no fields of its own.
        anyofs = [(node["anyOf"], f"{where}/anyOf")] if "anyOf" in node else []
        anyofs += [(a["anyOf"], f"{where}/allOf[{i}]/anyOf") for i, a in enumerate(node.get("allOf", [])) if "anyOf" in a]
        groups = [
            [(branch.get("required", []), f"{group_path}[{i}]") for i, branch in enumerate(branches)]
            for branches, group_path in anyofs
        ]
        out = []
        for combo in itertools.product(*groups):
            fields = list(dict.fromkeys([*node.get("required", []), *itertools.chain.from_iterable(c[0] for c in combo)]))
            alt_tags = frozenset(c[1] for c in combo)
            per_field = [
                [
                    (name, value, tags)
                    for value, tags in _variants(props.get(name, {"type": "string"}), name, counter, f"{where}/properties/{name}")
                ]
                for name in fields
            ]
            for field_combo in itertools.product(*per_field):
                out.append((
                    {name: value for name, value, _ in field_combo},
                    alt_tags.union(*(tags for _, _, tags in field_combo)),
                ))
        return out
    if kind == "array":
        size = max(node.get("minItems", 1), 1)
        return [
            ([_fresh(value, counter) for _ in range(size)], tags)
            for value, tags in _variants(node.get("items", {"type": "string"}), path, counter, f"{where}/items")
        ]
    if kind == "integer":
        return [(max(node.get("minimum", 0), 0), frozenset())]
    if kind == "boolean":
        return [(True, frozenset())]
    return [(f"SENT{next(counter)}_{path}", frozenset())]


def _fresh(value, counter):
    """Deep-copy ``value`` giving every sentinel string a new number."""
    if isinstance(value, dict):
        return {k: _fresh(v, counter) for k, v in value.items()}
    if isinstance(value, list):
        return [_fresh(v, counter) for v in value]
    if isinstance(value, str) and SENTINEL.fullmatch(value):
        return f"SENT{next(counter)}_{value.split('_', 1)[1]}"
    if isinstance(value, str) and value.endswith(".svg") and SENTINEL.fullmatch(value[:-4]):
        return f"SENT{next(counter)}_{value[:-4].split('_', 1)[1]}.svg"
    return value


def _make_answers_meaningful(instance) -> None:
    """Make generated answers name real choices, as an authored item would."""
    if not isinstance(instance, dict):
        return
    for row in instance.get("items", []):
        if not isinstance(row, dict):
            continue
        # A text `answer` must name one of the choices to be meaningful.
        for choices in ("words", "options"):
            if "answer" in row and isinstance(row.get(choices), list):
                first = row[choices][0]
                row["answer"] = first["text"] if isinstance(first, dict) else first
        if "letter" in row and "options" in row:
            row["letter"] = row["options"][0]
        # A quiz marks exactly one object option correct, the first.
        if instance.get("type") == "quiz":
            for position, option in enumerate(row.get("options", [])):
                if isinstance(option, dict):
                    option["correct"] = position == 0
    items = instance.get("items")
    order = instance.get("correct_order")
    # String `correct_order` must be a permutation of the item strings.
    if instance.get("type") == "order" and order and isinstance(order[0], str):
        instance["correct_order"] = list(reversed(items))


def _cases() -> list[tuple[str, int, dict]]:
    cases = []
    for name, node in DEFS.items():
        counter = itertools.count(1)
        for index, (instance, tags) in enumerate(_variants(node, "", counter, name)):
            _make_answers_meaningful(instance)
            # A branch's extra constraint (quiz: some option carries
            # ``correct: true``) can leave a variant built for another branch
            # invalid; branch coverage below proves nothing is lost.
            if VALIDATOR.is_valid([instance]):
                cases.append((name.removesuffix("-a1"), index, instance, tags))
    return cases


_ALL_CASES = _cases()
CASES = [(name, index, instance) for name, index, instance, _ in _ALL_CASES]


CASE_IDS = [f"{c[0]}-{c[1]}" for c in CASES]


def _dropped(example: dict, *outputs: str) -> set[str]:
    """Field names whose sentinel is missing from any of ``outputs``."""
    markers = SENTINEL.findall(json.dumps(example))
    return {
        m.split("_", 1)[1]
        for m in markers
        if m.split("_", 1)[1] not in INTERNAL_ONLY and any(m not in out for out in outputs)
    }


@pytest.mark.parametrize(("activity_type", "index", "example"), CASES, ids=CASE_IDS)
def test_parser_keeps_every_required_field(activity_type, index, example):
    parser = ActivityParser()
    activity = parser._parse_activity(example)
    parsed = json.dumps(dataclasses.asdict(activity), ensure_ascii=False)
    dropped = _dropped(example, parsed, parser.to_mdx([activity]))
    assert dropped == KNOWN_DRIFT.get(activity_type, set()), (
        f"{activity_type}: required fields dropped by ActivityParser/to_mdx = {sorted(dropped)}; "
        f"known drift = {sorted(KNOWN_DRIFT.get(activity_type, set()))}"
    )


@pytest.mark.parametrize(("activity_type", "index", "example"), CASES, ids=CASE_IDS)
def test_renderer_keeps_every_required_field(activity_type, index, example):
    jsx = render_activity_to_jsx(example)
    assert "Unknown activity type" not in jsx
    dropped = _dropped(example, jsx)
    assert dropped == KNOWN_DRIFT.get(activity_type, set()), (
        f"{activity_type}: required fields dropped by activity_renderer = {sorted(dropped)}; "
        f"known drift = {sorted(KNOWN_DRIFT.get(activity_type, set()))}"
    )


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


# ---------------------------------------------------------------------------
# Point 4: image-to-letter schema constraints and validator
# ---------------------------------------------------------------------------


def _itl_item(**overrides) -> dict:
    return {"image": "🍎", "letter": "Я", "options": ["А", "Я"], "explanation": "e", **overrides}


def _itl_activity(item: dict) -> dict:
    return {"type": "image-to-letter", "instruction": "Оберіть букву", "items": [item]}


CYRILLIC_WORD = "".join(chr(cp) for cp in (0x44F, 0x431, 0x43B, 0x443, 0x43A, 0x43E))  # a Cyrillic word
GOOD_IMAGES = [
    "🕷️",
    "👨🏾‍❤️‍💋‍👨🏿",
    "👨‍👩‍👧‍👦",
    "🇺🇦",
    "🍎",
    "\u00a9\ufe0f",  # copyright sign with emoji presentation
    "\u2122\ufe0f",
    "\u25b6\ufe0f",
    "assets/apple.png",
    "img/flag.svg",
    "symbols/star.webp",
    "path/to/pic.jpg",
]
BAD_IMAGES = [
    CYRILLIC_WORD,
    "!!!",
    "🍎🍎",
    "🍎🍌",
    "A",
    "apple-emoji",
    "not an image",
    "cat.txt",
    " 🍎",
    "\u00a9",  # bare text-default symbols are not a picture
    "\u2122",
    "\u25b6",
    "🕷",  # text-default pictograph without U+FE0F
    "🇺",  # a lone Regional_Indicator is half a flag
    "1\ufe0f\u20e3",  # keycap
    "\U0001f3fe",  # lone skin-tone modifier
]


@pytest.mark.parametrize("good_image", GOOD_IMAGES)
def test_image_to_letter_image_accepts_asset_or_one_emoji(good_image):
    assert image_to_letter_image_kind(good_image) is not None
    assert VALIDATOR.is_valid([_itl_activity(_itl_item(image=good_image))])
    _itl_mdx([_itl_item(image=good_image)])  # renderer accepts it too


@pytest.mark.parametrize("bad_image", BAD_IMAGES)
def test_image_to_letter_image_rejects_everything_else(bad_image):
    assert image_to_letter_image_kind(bad_image) is None
    with pytest.raises(ImageToLetterShapeError, match="neither an asset path"):
        _itl_mdx([_itl_item(image=bad_image)])
    with pytest.raises(ImageToLetterShapeError):
        render_activity_to_jsx(_itl_activity(_itl_item(image=bad_image)))


@pytest.mark.parametrize("options", [["Я", "Я"], ["Я", "Я", "Я"]])
def test_image_to_letter_needs_a_distractor_distinct_from_the_letter(options):
    with pytest.raises(ImageToLetterShapeError, match="no choice distinct from letter 'Я'"):
        _itl_mdx([_itl_item(options=options)])


def test_image_to_letter_validator_reports_bad_items_before_render(tmp_path):
    import yaml

    from build.activity_validator import validate_activities  # scripts/ is on sys.path

    path = tmp_path / "module.yaml"
    path.write_text(
        yaml.safe_dump(
            {"inline": [_itl_activity(_itl_item(image=CYRILLIC_WORD)), _itl_activity(_itl_item(options=["Я", "Я"]))]},
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    messages = [i.message for i in validate_activities(path) if i.activity_type == "image-to-letter"]
    assert len(messages) == 2
    assert "neither an asset path" in messages[0]
    assert "no choice distinct" in messages[1]


def test_image_to_letter_validator_rejects_options_without_letter():
    with pytest.raises(ImageToLetterShapeError, match="options do not contain letter 'Я'"):
        _itl_mdx([{"image": "🍎", "letter": "Я", "options": ["А", "О"], "explanation": "e"}])


# ---------------------------------------------------------------------------
# Per-type MDX emission unit tests
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# quiz: one resolver names the correct option for both emitters and the validator
# ---------------------------------------------------------------------------


def _quiz_activity(**item) -> dict:
    row = {"question": "Q?", "explanation": "e", **item}
    return {"type": "quiz", "instruction": "Pick one.", "items": [row]}


def _obj(*flags: bool) -> list[dict]:
    return [{"text": f"opt{i}", "correct": flag} for i, flag in enumerate(flags)]


def _marked_by_emitters(activity: dict) -> tuple[list[str], list[str]]:
    """Texts each emitter marks correct for the first quiz item."""
    parser = ActivityParser()
    mdx = parser.to_mdx([parser._parse_activity(activity)])
    parsed = json.loads(re.search(r"questions=\{JSON\.parse\(`(.*?)`\)\}", mdx, re.S).group(1))
    jsx = render_activity_to_jsx(activity)
    rendered, _ = json.JSONDecoder().raw_decode(jsx[jsx.index("questions={") + len("questions=") + 1 :])
    return (
        [o["text"] for o in parsed[0]["options"] if o["correct"]],
        [o["text"] for o in rendered[0]["options"] if o["correct"]],
    )


CONSISTENT_QUIZZES = {
    "index": ({"options": ["a", "b", "c"], "correct": 1}, ["b"]),
    "index-zero": ({"options": ["a", "b", "c"], "correct": 0}, ["a"]),
    "answer": ({"options": ["a", "b", "c"], "answer": "c"}, ["c"]),
    "index+answer": ({"options": ["a", "b", "c"], "correct": 2, "answer": "c"}, ["c"]),
    "flags-only": ({"options": _obj(False, True, False)}, ["opt1"]),
    "flags+index": ({"options": _obj(False, True, False), "correct": 1}, ["opt1"]),
    "flags+answer": ({"options": _obj(True, False), "answer": "opt0"}, ["opt0"]),
    "flags+index+answer": ({"options": _obj(False, False, True), "correct": 2, "answer": "opt2"}, ["opt2"]),
    "flags+index+answer-agree": (
        {"options": _obj(False, True, False), "correct": 1, "answer": "opt1"}, ["opt1"],
    ),
    "mixed-flag-on-object": ({"options": ["a", {"text": "b", "correct": True}], "correct": 1}, ["b"]),
}


@pytest.mark.parametrize(("item", "expected"), CONSISTENT_QUIZZES.values(), ids=CONSISTENT_QUIZZES)
def test_quiz_marks_the_named_correct_option_in_both_emitters(item, expected):
    activity = _quiz_activity(**item)
    assert VALIDATOR.is_valid([activity])
    assert _marked_by_emitters(activity) == (expected, expected)


CONTRADICTORY_QUIZZES = {
    "all-false-flags+index": {"options": _obj(False, False, False), "correct": 1},
    "all-false-flags+answer": {"options": _obj(False, False), "answer": "opt1"},
    "all-false-flags-alone": {"options": _obj(False, False)},
    "flag-vs-index": {"options": _obj(True, False), "correct": 1},
    "flag-vs-answer": {"options": _obj(True, False), "answer": "opt1"},
    "index-vs-answer": {"options": ["a", "b", "c"], "correct": 0, "answer": "b"},
    "answer-names-no-option": {"options": ["a", "b"], "answer": "z"},
    "no-input-names-an-option": {"options": ["a", "b"]},
    "index-out-of-range": {"options": ["a", "b"], "correct": 5},
    "two-true-flags+index": {"options": _obj(True, True, False), "correct": 0},
    "two-true-flags-alone": {"options": _obj(True, True, False)},
    "two-true-flags-equal-index-list": {"options": _obj(True, True, False), "correct": [0, 1]},
    "mixed-explicit-false-on-named-index": {
        "options": ["a", {"text": "b", "correct": False}], "correct": 1,
    },
    "mixed-index-on-bare-string-vs-flags": {
        "options": ["a", {"text": "b", "correct": False}], "correct": 0,
    },
    "index-not-an-int": {"options": ["a", "b"], "correct": "1"},
    "answer-null": {"options": ["a", "b"], "correct": 0, "answer": None},
    "answer-empty": {"options": ["a", "b"], "correct": 0, "answer": ""},
    "answer-int": {"options": ["a", "b"], "correct": 0, "answer": 3},
    "answer-null-alone": {"options": ["a", "b"], "answer": None},
    "index-null": {"options": ["a", "b"], "correct": None, "answer": "a"},
    "flag-not-a-bool": {"options": ["a", {"text": "b", "correct": None}], "correct": 0},
}


@pytest.mark.parametrize("item", CONTRADICTORY_QUIZZES.values(), ids=CONTRADICTORY_QUIZZES)
def test_quiz_with_contradicting_or_unnamed_answer_is_rejected_never_first_choice(item):
    activity = _quiz_activity(**item)
    with pytest.raises(QuizCorrectnessError, match="quiz item 0"):
        quiz_correct_indices(activity["items"][0])
    with pytest.raises(QuizCorrectnessError, match="quiz item 0"):
        ActivityParser()._parse_activity(activity)
    with pytest.raises(QuizCorrectnessError, match="quiz item 0"):
        render_activity_to_jsx(activity)


def test_quiz_correct_index_list_is_a_claim_of_its_own_set():
    assert quiz_correct_indices({"options": ["a", "b", "c"], "correct": [2]}) == [2]
    assert quiz_correct_indices({"options": _obj(False, False, True), "correct": [2], "answer": "opt2"}) == [2]


def _validate(tmp_path, *activities: dict):
    import yaml

    from build.activity_validator import validate_activities  # scripts/ is on sys.path

    path = tmp_path / "module.yaml"
    path.write_text(yaml.safe_dump({"inline": list(activities)}, allow_unicode=True), encoding="utf-8")
    return validate_activities(path)


@pytest.mark.parametrize("item", CONTRADICTORY_QUIZZES.values(), ids=CONTRADICTORY_QUIZZES)
def test_validator_rejects_quiz_with_contradicting_or_unnamed_answer(tmp_path, item):
    issues = [i for i in _validate(tmp_path, _quiz_activity(**item)) if i.activity_type == "quiz"]
    assert issues
    assert all(i.severity == "error" for i in issues)
    assert any("quiz item 0" in i.message or "out of range" in i.message for i in issues)


@pytest.mark.parametrize(("item", "expected"), CONSISTENT_QUIZZES.values(), ids=CONSISTENT_QUIZZES)
def test_validator_accepts_every_consistent_quiz_shape(tmp_path, item, expected):
    assert _validate(tmp_path, _quiz_activity(**item)) == []


# ---------------------------------------------------------------------------
# group-sort: one resolver names the category for both emitters and the validator
# ---------------------------------------------------------------------------


def _group_sort(*groups: dict) -> dict:
    return {"type": "group-sort", "instruction": "Sort.", "groups": list(groups)}


def _group_keys(activity: dict) -> tuple[list[str], list[str]]:
    parser = ActivityParser()
    mdx = parser.to_mdx([parser._parse_activity(activity)])
    parsed = json.loads(re.search(r"groups=\{JSON\.parse\(`(.*?)`\)\}", mdx, re.S).group(1))
    jsx = render_activity_to_jsx(activity)
    rendered, _ = json.JSONDecoder().raw_decode(jsx[jsx.index("groups={") + len("groups=") + 1 :])
    return list(parsed), list(rendered)


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    [
        ({"label": "L1", "items": ["x"]}, {"label": "L2", "items": ["y"]}, ["L1", "L2"]),
        ({"name": "N1", "items": ["x"]}, {"name": "N2", "items": ["y"]}, ["N1", "N2"]),
        ({"label": "S", "name": "S", "items": ["x"]}, {"name": "N2", "items": ["y"]}, ["S", "N2"]),
    ],
    ids=["label", "name", "label-equals-name"],
)
def test_group_sort_category_name_is_the_same_in_both_emitters(first, second, expected):
    activity = _group_sort(first, second)
    assert VALIDATOR.is_valid([activity])
    assert _group_keys(activity) == (expected, expected)


def test_group_sort_label_and_name_that_differ_are_rejected(tmp_path):
    activity = _group_sort({"label": "L", "name": "N", "items": ["x"]}, {"label": "M", "items": ["y"]})
    assert VALIDATOR.is_valid([activity])  # the schema allows either key; Python decides
    with pytest.raises(GroupSortNameError, match="group-sort group 0"):
        group_sort_group_name(activity["groups"][0])
    with pytest.raises(GroupSortNameError, match="group-sort group 0"):
        ActivityParser()._parse_activity(activity)
    with pytest.raises(GroupSortNameError, match="group-sort group 0"):
        render_activity_to_jsx(activity)
    issues = [i for i in _validate(tmp_path, activity) if i.activity_type == "group-sort"]
    assert len(issues) == 1
    assert issues[0].severity == "error"
    assert issues[0].item_index == 0
    assert "label 'L' and name 'N'" in issues[0].message


# ---------------------------------------------------------------------------
# order: the emitted correct_order prop itself carries the answer
# ---------------------------------------------------------------------------


def _order_props(activity: dict) -> tuple[list, list]:
    parser = ActivityParser()
    mdx = parser.to_mdx([parser._parse_activity(activity)])
    parsed = json.loads(re.search(r"correct_order=\{JSON\.parse\(`(.*?)`\)\}", mdx, re.S).group(1))
    jsx = render_activity_to_jsx(activity)
    rendered, _ = json.JSONDecoder().raw_decode(jsx[jsx.index("correct_order={") + len("correct_order=") + 1 :])
    return parsed, rendered


@pytest.mark.parametrize(
    ("correct_order", "expected"),
    [([2, 0, 1], [2, 0, 1]), (["C", "A", "B"], [2, 0, 1])],
    ids=["indices", "item-strings"],
)
def test_order_emits_correct_order_prop_as_indices_in_both_emitters(correct_order, expected):
    activity = {"type": "order", "instruction": "Order.", "items": ["A", "B", "C"], "correct_order": correct_order}
    assert VALIDATOR.is_valid([activity])
    assert _order_props(activity) == (expected, expected)


def test_order_with_unresolvable_correct_order_is_rejected_by_both_emitters():
    activity = {"type": "order", "instruction": "Order.", "items": ["A", "B", "C"], "correct_order": ["C", "A", "Z"]}
    with pytest.raises(TypeError, match="must contain integers"):
        ActivityParser()._parse_activity(activity)
    with pytest.raises(TypeError, match="must contain integers"):
        render_activity_to_jsx(activity)
