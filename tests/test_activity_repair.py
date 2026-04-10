"""Unit tests for activity_repair module.

Tests deterministic fixes in isolation using small YAML fixtures.
See issue #1185 for the acceptance criteria these tests enforce.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from build.activity_repair import repair_activities
from build.activity_validator import validate_activities


def _write_yaml(tmp_path: Path, slug: str, data: dict) -> Path:
    """Write a YAML fixture and return the path."""
    act_dir = tmp_path / slug
    act_dir.mkdir(parents=True, exist_ok=True)
    path = act_dir / f"{slug}.yaml"
    path.write_text(
        yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    return path


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text("utf-8"))


# ---------------------------------------------------------------------------
# Fix 1: Parenthetical hints in fill-in
# ---------------------------------------------------------------------------


def test_strip_parenthetical_hints(tmp_path):
    data = {
        "inline": [
            {
                "id": "fill-1",
                "type": "fill-in",
                "title": "Test",
                "instruction": "Fill in",
                "items": [
                    {"sentence": "Я йду в ____ (магазин).", "answer": "магазин"},
                    {"sentence": "Вона йде в ____ (школа).", "answer": "школу"},
                    {"sentence": "Це звичайне речення без натяку.", "answer": "слово"},
                ],
            }
        ],
        "workbook": [],
    }
    path = _write_yaml(tmp_path, "test-mod", data)
    result = repair_activities(path, "a2", 1)

    assert result.fixes_applied >= 2
    assert result.modified is True

    out = _load_yaml(path)
    items = out["inline"][0]["items"]
    assert items[0]["sentence"] == "Я йду в ____."
    assert items[1]["sentence"] == "Вона йде в ____."
    assert items[2]["sentence"] == "Це звичайне речення без натяку."


# ---------------------------------------------------------------------------
# Fix 2: Deduplicate quiz options
# ---------------------------------------------------------------------------


def test_deduplicate_quiz_options(tmp_path):
    data = {
        "inline": [
            {
                "id": "quiz-1",
                "type": "quiz",
                "title": "Test",
                "instruction": "Pick one",
                "items": [
                    {
                        "question": "Яке правильне?",
                        "options": ["добре", "погано", "добре", "чудово"],
                        "correct": 3,  # "чудово"
                    }
                ],
            }
        ],
        "workbook": [],
    }
    path = _write_yaml(tmp_path, "test-mod", data)
    result = repair_activities(path, "a2", 1)

    assert result.fixes_applied >= 1
    out = _load_yaml(path)
    item = out["inline"][0]["items"][0]
    assert item["options"] == ["добре", "погано", "чудово"]
    # correct should have been re-indexed from 3 → 2
    assert item["correct"] == 2
    assert item["options"][item["correct"]] == "чудово"


def test_deduplicate_quiz_dict_options_preserves_shape_and_merges_correct(tmp_path):
    data = {
        "inline": [
            {
                "id": "quiz-bridge",
                "type": "quiz",
                "title": "Визначення відмінків",
                "items": [
                    {
                        "question": "Це новий **студент**.",
                        "options": [
                            {"text": "Називний", "correct": True},
                            {"text": "Знахідний", "correct": False},
                            {"text": "Називний", "correct": False},
                            {"text": "Кличний", "correct": False},
                        ],
                    }
                ],
            }
        ],
        "workbook": [],
    }
    path = _write_yaml(tmp_path, "test-mod", data)

    result = repair_activities(path, "a2", 1)

    assert result.fixes_applied >= 1
    item = _load_yaml(path)["inline"][0]["items"][0]
    assert item["options"] == [
        {"text": "Називний", "correct": True},
        {"text": "Знахідний", "correct": False},
        {"text": "Кличний", "correct": False},
    ]


# ---------------------------------------------------------------------------
# Fix 3: Match-up duplicate pairs
# ---------------------------------------------------------------------------


def test_match_up_duplicate_pairs_removed(tmp_path):
    data = {
        "inline": [],
        "workbook": [
            {
                "type": "match-up",
                "title": "Match",
                "instruction": "Pair them",
                "pairs": [
                    {"left": "кіт", "right": "cat"},
                    {"left": "пес", "right": "dog"},
                    {"left": "кіт", "right": "cat"},  # duplicate
                    {"left": "риба", "right": "fish"},
                ],
            }
        ],
    }
    path = _write_yaml(tmp_path, "test-mod", data)
    result = repair_activities(path, "a2", 1)

    assert result.fixes_applied >= 1
    out = _load_yaml(path)
    pairs = out["workbook"][0]["pairs"]
    assert len(pairs) == 3
    lefts = [p["left"] for p in pairs]
    assert lefts.count("кіт") == 1


# ---------------------------------------------------------------------------
# Fix 4a: Move WORKBOOK-ONLY type from inline to workbook
# ---------------------------------------------------------------------------


def test_move_workbook_only_type_from_inline(tmp_path):
    data = {
        "inline": [
            {"id": "q1", "type": "quiz", "title": "Q", "items": [{"question": "?", "options": ["a", "b", "c", "d"], "correct": 0}]},
            {
                "id": "essay1",
                "type": "essay-response",
                "title": "Write",
                "prompt": "Напишіть 100 слів про літо.",
            },
        ],
        "workbook": [],
    }
    path = _write_yaml(tmp_path, "test-mod", data)
    result = repair_activities(path, "b1", 1)

    assert result.fixes_applied >= 1
    out = _load_yaml(path)
    # essay-response should be gone from inline
    assert all(a.get("type") != "essay-response" for a in out["inline"])
    # essay-response should be in workbook
    assert any(a.get("type") == "essay-response" for a in out["workbook"])
    # id should be stripped from the moved activity
    moved = next(a for a in out["workbook"] if a.get("type") == "essay-response")
    assert "id" not in moved


# ---------------------------------------------------------------------------
# Fix 4b: Move INLINE-ONLY type from workbook to inline
# ---------------------------------------------------------------------------


def test_move_inline_only_type_from_workbook(tmp_path):
    data = {
        "inline": [],
        "workbook": [
            {"type": "fill-in", "title": "F", "items": [{"sentence": "___", "answer": "a"}]},
            {
                "type": "image-to-letter",
                "title": "Letters",
                "items": [{"image": "🍎", "letter": "А"}],
            },
        ],
    }
    path = _write_yaml(tmp_path, "test-mod", data)
    result = repair_activities(path, "a1", 1)

    assert result.fixes_applied >= 1
    out = _load_yaml(path)
    # image-to-letter should be gone from workbook
    assert all(a.get("type") != "image-to-letter" for a in out["workbook"])
    # image-to-letter should be in inline
    assert any(a.get("type") == "image-to-letter" for a in out["inline"])
    # moved activity should have an id (inline requires it)
    moved = next(a for a in out["inline"] if a.get("type") == "image-to-letter")
    assert moved.get("id")


# ---------------------------------------------------------------------------
# Fix 5: Drop disallowed type (with count OK after drop)
# ---------------------------------------------------------------------------


def test_drop_disallowed_type(tmp_path):
    # A2 doesn't allow essay-response. Put enough workbook to stay above min.
    data = {
        "inline": [
            {"id": f"q{i}", "type": "quiz", "title": "Q", "items": [{"question": "?", "options": ["a", "b", "c", "d"], "correct": 0}]}
            for i in range(6)
        ],
        "workbook": [
            {"type": "fill-in", "title": "F", "items": [{"sentence": "___ word", "answer": "a"}]},
            {"type": "cloze", "title": "C", "passage": "text ___", "blanks": [{"id": 1, "answer": "a", "options": ["a", "b", "c", "d"]}]},
            {"type": "error-correction", "title": "E", "items": [{"sentence": "wrong", "error": "w", "correction": "r"}]},
            {"type": "unjumble", "title": "U", "items": [{"words": ["a", "b", "c"], "correct_order": ["a", "b", "c"]}]},
            {"type": "translate", "title": "T", "items": [{"source": "hi", "target": "привіт"}]},
            {"type": "match-up", "title": "M", "pairs": [{"left": "a", "right": "b"}]},
            {"type": "group-sort", "title": "G", "groups": [{"label": "x", "items": ["1"]}]},
            {"type": "fill-in", "title": "F2", "items": [{"sentence": "___ more", "answer": "b"}]},
            # This one is NOT allowed at A2:
            {"type": "authorial-intent", "title": "Not allowed", "prompt": "Why did the author..."},
        ],
    }
    path = _write_yaml(tmp_path, "test-mod", data)
    result = repair_activities(path, "a2", 1)

    assert result.fixes_applied >= 1
    out = _load_yaml(path)
    # authorial-intent should be dropped entirely
    assert all(a.get("type") != "authorial-intent" for a in out["workbook"])


# ---------------------------------------------------------------------------
# Fix 6: Answer added to options
# ---------------------------------------------------------------------------


def test_answer_added_to_options(tmp_path):
    data = {
        "inline": [
            {
                "id": "fill-1",
                "type": "fill-in",
                "title": "Test",
                "items": [
                    {
                        "sentence": "Я ___ українську.",
                        "answer": "вчу",
                        "options": ["вчиш", "вчить", "вчимо"],  # answer missing
                    }
                ],
            }
        ],
        "workbook": [],
    }
    path = _write_yaml(tmp_path, "test-mod", data)
    result = repair_activities(path, "a2", 1)

    assert result.fixes_applied >= 1
    out = _load_yaml(path)
    item = out["inline"][0]["items"][0]
    assert "вчу" in item["options"]


def test_fill_in_malformed_options_marks_regen_without_mutating_item(tmp_path):
    data = {
        "inline": [
            {
                "id": "fill-1",
                "type": "fill-in",
                "title": "Bad options",
                "items": [
                    {
                        "sentence": "Я ___ українську.",
                        "answer": "вчу",
                        "options": {},
                    }
                ],
            }
        ],
        "workbook": [],
    }
    path = _write_yaml(tmp_path, "test-mod", data)

    result = repair_activities(path, "a2", 1)

    assert any("fill-in options is not a list" in msg for msg in result.needs_regen)
    assert result.modified is False
    assert _load_yaml(path)["inline"][0]["items"][0]["options"] == {}


# ---------------------------------------------------------------------------
# Fix 7: True-false invalid correct field
# ---------------------------------------------------------------------------


def test_true_false_invalid_correct_dropped(tmp_path):
    data = {
        "inline": [
            {
                "id": "tf-1",
                "type": "true-false",
                "title": "TF",
                "items": [
                    {"statement": "Good item", "correct": True},
                    {"statement": "Bad item", "correct": "maybe"},  # invalid
                    {"statement": "Another good", "correct": False},
                    {"statement": "Missing field"},  # no correct
                ],
            }
        ],
        "workbook": [],
    }
    path = _write_yaml(tmp_path, "test-mod", data)
    result = repair_activities(path, "a2", 1)

    assert result.fixes_applied >= 1
    out = _load_yaml(path)
    items = out["inline"][0]["items"]
    assert len(items) == 2
    assert all(isinstance(i.get("correct"), bool) for i in items)


def test_repair_reports_structural_regen_for_bad_sections_items_pairs_and_null_activity(tmp_path):
    data = {
        "inline": "oops",
        "workbook": [
            None,
            {"type": "fill-in", "title": "Broken items", "items": "oops"},
            {"type": "match-up", "title": "Broken pairs", "pairs": {}},
        ],
    }
    path = _write_yaml(tmp_path, "test-mod", data)

    result = repair_activities(path, "a2", 1)

    assert result.modified is True
    assert any("inline section is not a list" in msg for msg in result.needs_regen)
    assert any("workbook activity 0 is not a mapping" in msg for msg in result.needs_regen)
    assert any("fill-in items is not a list" in msg for msg in result.needs_regen)
    assert any("match-up pairs is not a list" in msg for msg in result.needs_regen)

    out = _load_yaml(path)
    assert out["inline"] == []
    assert out["workbook"][0] is None
    assert out["workbook"][1]["items"] == "oops"
    assert out["workbook"][2]["pairs"] == {}


# ---------------------------------------------------------------------------
# needs_regen: count below minimum
# ---------------------------------------------------------------------------


def test_count_below_min_reported_as_regen(tmp_path):
    # A2 requires INLINE_MIN=4, WORKBOOK_MIN=8. Give only 1 of each.
    data = {
        "inline": [
            {"id": "q1", "type": "quiz", "title": "Q", "items": [{"question": "?", "options": ["a", "b", "c", "d"], "correct": 0}]}
        ],
        "workbook": [
            {"type": "fill-in", "title": "F", "items": [{"sentence": "___ word", "answer": "a"}]}
        ],
    }
    path = _write_yaml(tmp_path, "test-mod", data)
    result = repair_activities(path, "a2", 1)

    assert len(result.needs_regen) >= 2  # inline + workbook both below min
    assert any("inline count" in msg for msg in result.needs_regen)
    assert any("workbook count" in msg for msg in result.needs_regen)
    assert result.can_ship is False


# ---------------------------------------------------------------------------
# Idempotency: running twice produces identical output
# ---------------------------------------------------------------------------


def test_repair_is_idempotent(tmp_path):
    data = {
        "inline": [
            {
                "id": "fill-1",
                "type": "fill-in",
                "title": "Test",
                "items": [
                    {"sentence": "Я йду в ____ (магазин).", "answer": "магазин"},
                ],
            }
        ],
        "workbook": [
            {
                "type": "match-up",
                "title": "M",
                "pairs": [
                    {"left": "a", "right": "b"},
                    {"left": "a", "right": "b"},  # duplicate
                ],
            }
        ],
    }
    path = _write_yaml(tmp_path, "test-mod", data)

    result1 = repair_activities(path, "a2", 1)
    content_after_first = path.read_text("utf-8")

    result2 = repair_activities(path, "a2", 1)
    content_after_second = path.read_text("utf-8")

    assert content_after_first == content_after_second
    assert result1.fixes_applied >= 1  # first pass fixes things
    assert result2.fixes_applied == 0  # second pass is a no-op
    assert result2.modified is False


# ---------------------------------------------------------------------------
# Clean module is a no-op
# ---------------------------------------------------------------------------


def test_clean_module_unchanged(tmp_path):
    # Each activity needs ≥ ITEMS_MIN items at a2 (= 8) to satisfy the
    # per-activity density check added 2026-04-11. Use 8 quiz questions
    # per activity and 8 fill-in items per activity so the module is
    # truly clean and repair is a no-op.
    quiz_items = [
        {"question": f"Question {i}?", "options": ["a", "b", "c", "d"], "correct": 0}
        for i in range(8)
    ]
    fillin_items = [
        {
            "sentence": f"Я ___ українську #{i}.",
            "answer": "вчу",
            "options": ["вчу", "вчиш", "вчить", "вчимо"],
        }
        for i in range(8)
    ]
    data = {
        "inline": [
            {"id": f"q{i}", "type": "quiz", "title": "Q", "items": quiz_items}
            for i in range(4)
        ],
        "workbook": [
            {"id": f"f{i}", "type": "fill-in", "title": "F", "items": fillin_items}
            for i in range(8)
        ],
    }
    path = _write_yaml(tmp_path, "test-mod", data)
    before = path.read_text("utf-8")

    result = repair_activities(path, "a2", 1)

    after = path.read_text("utf-8")
    assert before == after
    assert result.fixes_applied == 0
    assert result.modified is False
    assert result.can_ship is True


@pytest.mark.parametrize("root", [[], [None]])
def test_validator_flags_non_mapping_root(tmp_path, root):
    path = _write_yaml(tmp_path, "test-mod", root)

    issues = validate_activities(path, level="a2", module_num=1)

    assert len(issues) == 1
    assert issues[0].message == "root is not a mapping"


def test_validator_flags_dict_quiz_duplicates_and_malformed_structures(tmp_path):
    data = {
        "inline": [
            {
                "id": "quiz-bridge",
                "type": "quiz",
                "title": "Визначення відмінків",
                "items": [
                    {
                        "question": "Це новий **студент**.",
                        "options": [
                            {"text": "Називний", "correct": True},
                            {"text": "Знахідний", "correct": False},
                            {"text": "Називний", "correct": False},
                            {"text": "Кличний", "correct": False},
                        ],
                    }
                ],
            },
            {"type": "fill-in", "title": "Broken options", "items": [{"sentence": "Я ___.", "answer": "вчу", "options": {}}]},
            None,
        ],
        "workbook": [
            {"type": "fill-in", "title": "Broken items", "items": "oops"},
            {"type": "match-up", "title": "Broken pairs", "pairs": {}},
            {"type": "match-up", "title": "Mixed pairs", "pairs": [{"left": "a", "right": "b"}, "oops"]},
        ],
    }
    path = _write_yaml(tmp_path, "test-mod", data)

    issues = validate_activities(path, level="a2", module_num=1)
    messages = [issue.message for issue in issues]

    assert any("duplicate options" in message and "Називний" in message for message in messages)
    assert any(message == "options is not a list: dict" for message in messages)
    assert any(message == "activity entry is not a mapping: NoneType" for message in messages)
    assert any(message == "items is not a list: str" for message in messages)
    assert any(message == "pairs is not a list: dict" for message in messages)
    assert any(message == "pair entry is not a mapping: str" for message in messages)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
