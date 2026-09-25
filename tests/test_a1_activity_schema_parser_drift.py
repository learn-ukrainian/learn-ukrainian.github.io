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

from yaml_activities import ActivityParser

from scripts.build.activity_renderer import (
    ImageToLetterShapeError,
    image_to_letter_image_kind,
    render_activity_to_jsx,
)

SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "activities-a1.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
DEFS = SCHEMA["definitions"]
VALIDATOR = Draft7Validator(SCHEMA)
SENTINEL = re.compile(r"SENT\d+_\w+")

# type -> required schema fields the parser/MDX path still drops (see PR #8716).
KNOWN_DRIFT: dict[str, set[str]] = {}
# Provenance metadata for the build engine, never rendered to the learner.
INTERNAL_ONLY = {"error_ref"}
# Types the parser rejects outright (loud, not silent); tracked separately.
PARSER_REJECTS: dict[str, str] = {}


def _variants(node: dict, path: str, counter) -> list:
    """Minimal valid instances of ``node``; one per anyOf-required alternative."""
    if "$ref" in node:
        return _variants(DEFS[node["$ref"].split("/")[-1]], path, counter)
    for key in ("oneOf", "anyOf"):
        if key in node and "properties" not in node:
            return [v for branch in node[key] for v in _variants(branch, path, counter)]
    if "const" in node:
        return [node["const"]]
    if node.get("pattern") == "^E-[0-9]{3,}$":
        return ["E-001"]
    if path == "image" or "png|jpe?g|webp|svg" in node.get("pattern", ""):
        return [f"SENT{next(counter)}_{path}.svg"]
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
    items = instance.get("items")
    order = instance.get("correct_order")
    # String `correct_order` must be a permutation of the item strings.
    if instance.get("type") == "order" and order and isinstance(order[0], str):
        instance["correct_order"] = list(reversed(items))


def _cases() -> list[tuple[str, int, dict]]:
    cases = []
    for name, node in DEFS.items():
        counter = itertools.count(1)
        for index, instance in enumerate(_variants(node, "", counter)):
            _make_answers_meaningful(instance)
            cases.append((name.removesuffix("-a1"), index, instance))
    return cases


CASES = _cases()


def test_generated_examples_are_schema_valid():
    for name, _, instance in CASES:
        assert VALIDATOR.is_valid([instance]), f"{name}: generated example is not schema-valid"


PARSED_CASES = [c for c in CASES if c[0] not in PARSER_REJECTS]
PARSED_IDS = [f"{c[0]}-{c[1]}" for c in PARSED_CASES]


def _dropped(example: dict, *outputs: str) -> set[str]:
    """Field names whose sentinel is missing from any of ``outputs``."""
    markers = SENTINEL.findall(json.dumps(example))
    return {
        m.split("_", 1)[1]
        for m in markers
        if m.split("_", 1)[1] not in INTERNAL_ONLY and any(m not in out for out in outputs)
    }


def test_every_a1_type_and_branch_is_generated():
    assert {c[0] for c in CASES} == {n.removesuffix("-a1") for n in DEFS}
    # Branch enumeration must widen coverage beyond one case per type.
    assert len(CASES) > len(DEFS)


@pytest.mark.parametrize(("activity_type", "index", "example"), PARSED_CASES, ids=PARSED_IDS)
def test_parser_keeps_every_required_field(activity_type, index, example):
    parser = ActivityParser()
    activity = parser._parse_activity(example)
    parsed = json.dumps(dataclasses.asdict(activity), ensure_ascii=False)
    dropped = _dropped(example, parsed, parser.to_mdx([activity]))
    assert dropped == KNOWN_DRIFT.get(activity_type, set()), (
        f"{activity_type}: required fields dropped by ActivityParser/to_mdx = {sorted(dropped)}; "
        f"known drift = {sorted(KNOWN_DRIFT.get(activity_type, set()))}"
    )


@pytest.mark.parametrize(("activity_type", "index", "example"), CASES, ids=[f"{c[0]}-{c[1]}" for c in CASES])
def test_renderer_keeps_every_required_field(activity_type, index, example):
    jsx = render_activity_to_jsx(example)
    assert "Unknown activity type" not in jsx
    dropped = _dropped(example, jsx)
    assert dropped == KNOWN_DRIFT.get(activity_type, set()), (
        f"{activity_type}: required fields dropped by activity_renderer = {sorted(dropped)}; "
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


# ---------------------------------------------------------------------------
# Point 4: image-to-letter schema constraints and validator
# ---------------------------------------------------------------------------


def test_image_to_letter_schema_requires_options():
    bad = {
        "type": "image-to-letter",
        "instruction": "Оберіть букву",
        "items": [{"image": "🍎", "letter": "Я", "explanation": "e"}],
    }
    assert not VALIDATOR.is_valid([bad])


def test_image_to_letter_schema_requires_min_two_options():
    bad = {
        "type": "image-to-letter",
        "instruction": "Оберіть букву",
        "items": [{"image": "🍎", "letter": "Я", "options": ["Я"], "explanation": "e"}],
    }
    assert not VALIDATOR.is_valid([bad])


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
    "assets/apple.png",
    "img/flag.svg",
    "symbols/star.webp",
    "path/to/pic.jpg",
]
BAD_IMAGES = [CYRILLIC_WORD, "!!!", "🍎🍎", "🍎🍌", "A", "apple-emoji", "not an image", "cat.txt", " 🍎"]


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


def test_image_to_letter_schema_leaves_the_image_rule_to_python():
    image = DEFS["image-to-letter-a1"]["properties"]["items"]["items"]["properties"]["image"]
    assert "pattern" not in image
    assert image["minLength"] == 1
    assert "image_to_letter_image_kind" in image["description"]


def test_image_to_letter_schema_requires_unique_options():
    assert not VALIDATOR.is_valid([_itl_activity(_itl_item(options=["Я", "Я"]))])


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


def test_anagram_mdx_contains_all_required_and_optional_fields():
    parser = ActivityParser()
    act = parser._parse_activity({
        "type": "anagram",
        "title": "Склади слово",
        "instruction": "Перестав букви",
        "items": [{"scrambled": "блуяко", "answer": "яблуко", "hint": "фрукт", "explanation": "Це яблуко."}],
    })
    mdx = parser.to_mdx([act])
    assert "<Anagram" in mdx
    assert "Склади слово" in mdx
    assert "Перестав букви" in mdx
    assert "блуяко" in mdx
    assert "яблуко" in mdx
    assert "фрукт" in mdx
    assert "Це яблуко." in mdx


def test_count_syllables_mdx_contains_all_required_and_optional_fields():
    parser = ActivityParser()
    act = parser._parse_activity({
        "type": "count-syllables",
        "title": "Порахуй склади",
        "instruction": "Скільки складів?",
        "max_count": 5,
        "items": [{"word": "мама", "correct": 2, "translation": "mother", "explanation": "Два склади: ма-ма."}],
    })
    mdx = parser.to_mdx([act])
    assert "<CountSyllables" in mdx
    assert "Скільки складів?" in mdx
    assert "мама" in mdx
    assert '"correct": 2' in mdx or '"correct":2' in mdx
    assert "mother" in mdx
    assert "Два склади: ма-ма." in mdx
    assert "maxCount={5}" in mdx


def test_divide_words_mdx_contains_all_required_and_optional_fields():
    parser = ActivityParser()
    act = parser._parse_activity({
        "type": "divide-words",
        "title": "Поділи на склади",
        "instruction": "Розділи слово дефісом",
        "items": [{"word": "вода", "answer": "во-да", "hint": "2 склади", "explanation": "Правильно: во-да."}],
    })
    mdx = parser.to_mdx([act])
    assert "<DivideWords" in mdx
    assert "Розділи слово дефісом" in mdx
    assert "вода" in mdx
    assert "во-да" in mdx
    assert "2 склади" in mdx
    assert "Правильно: во-да." in mdx


def test_unjumble_mdx_contains_all_required_and_optional_fields():
    parser = ActivityParser()
    act = parser._parse_activity({
        "type": "unjumble",
        "title": "Віднови порядок",
        "instruction": "Склади речення",
        "items": [{"words": ["є", "Це", "кіт"], "answer": "Це є кіт", "hint": "Почніть з Це", "explanation": "Це є кіт."}],
    })
    mdx = parser.to_mdx([act])
    assert "<Unjumble" in mdx
    assert "Склади речення" in mdx
    assert "є / Це / кіт" in mdx
    assert "Це є кіт" in mdx
    assert "Почніть з Це" in mdx
    assert "Це є кіт." in mdx


def test_watch_and_repeat_mdx_contains_all_required_and_optional_fields():
    parser = ActivityParser()
    act = parser._parse_activity({
        "type": "watch-and-repeat",
        "title": "Дивись і повторюй",
        "instruction": "Повторюй за відео",
        "items": [{
            "video": "video.mp4",
            "letter": "А",
            "word": "автобус",
            "sound": "/a/",
            "note": "голосний",
            "explanation": "Звук [а] відкритий.",
        }],
    })
    mdx = parser.to_mdx([act])
    assert "<WatchAndRepeat" in mdx
    assert "video.mp4" in mdx
    assert "А" in mdx
    assert "автобус" in mdx
    assert "/a/" in mdx
    assert "голосний" in mdx
    assert "Звук [а] відкритий." in mdx


def test_letter_grid_mdx_without_optional_fields():
    parser = ActivityParser()
    act = parser._parse_activity({
        "type": "letter-grid",
        "title": "Алфавіт",
        "instruction": "Вивчи літери",
        "letters": [{"upper": "А", "lower": "а"}],
    })
    mdx = parser.to_mdx([act])
    assert "<LetterGrid" in mdx
    assert '"upper": "А"' in mdx or '"upper":"А"' in mdx
    assert '"lower": "а"' in mdx or '"lower":"а"' in mdx
    assert "Алфавіт" in mdx
    assert "Вивчи літери" in mdx


def test_letter_grid_mdx_with_optional_fields():
    parser = ActivityParser()
    act = parser._parse_activity({
        "type": "letter-grid",
        "letters": [{"upper": "Б", "lower": "б", "name": "бе", "emoji": "🥖", "key_word": "булка"}],
    })
    mdx = parser.to_mdx([act])
    assert "<LetterGrid" in mdx
    assert '"name": "бе"' in mdx or '"name":"бе"' in mdx
    assert '"emoji": "🥖"' in mdx or '"emoji":"🥖"' in mdx
    assert '"key_word": "булка"' in mdx or '"key_word":"булка"' in mdx


def test_phrase_table_mdx_emission():
    parser = ActivityParser()
    act = parser._parse_activity({
        "type": "phrase-table",
        "title": "Корисні фрази",
        "instruction": "Запам'ятайте фрази",
        "groups": [
            {
                "label": "Привітання",
                "phrases": [
                    "Добрий день",
                    {"phrase": "Привіт", "context": "неформальне", "emoji": "👋"},
                ],
            }
        ],
    })
    mdx = parser.to_mdx([act])
    assert "<PhraseTable" in mdx
    assert "Корисні фрази" in mdx
    assert "Запам'ятайте фрази" in mdx
    assert "Привітання" in mdx
    assert "Добрий день" in mdx
    assert "Привіт" in mdx
    assert "неформальне" in mdx
    assert "👋" in mdx


@pytest.mark.parametrize("value", ["", None, 7, ["🍎"]])
def test_image_to_letter_image_kind_rejects_non_strings_and_empty(value):
    assert image_to_letter_image_kind(value) is None
