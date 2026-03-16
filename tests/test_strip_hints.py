"""Tests for deterministic hint field stripping in screen.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from pipeline.screen import _strip_hints_recursive


class TestStripHintsRecursive:

    def test_strips_item_level_hints(self):
        data = [
            {
                "type": "anagram",
                "title": "Unscramble",
                "items": [
                    {"scrambled": "А М А М", "answer": "МАМА", "hint": "mom"},
                    {"scrambled": "Т І К", "answer": "КІТ", "hint": "cat"},
                ],
            }
        ]
        count = _strip_hints_recursive(data)
        assert count == 2
        for item in data[0]["items"]:
            assert "hint" not in item

    def test_strips_activity_level_hints(self):
        data = [
            {
                "type": "quiz",
                "title": "Test",
                "hint": "This is a quiz",
                "items": [{"question": "What?", "answer": "Yes"}],
            }
        ]
        count = _strip_hints_recursive(data)
        assert count == 1
        assert "hint" not in data[0]

    def test_no_hints_returns_zero(self):
        data = [
            {
                "type": "quiz",
                "title": "Clean",
                "items": [{"question": "Q", "answer": "A"}],
            }
        ]
        count = _strip_hints_recursive(data)
        assert count == 0

    def test_deeply_nested_hints(self):
        data = [
            {
                "type": "fill-in",
                "title": "Fill",
                "items": [
                    {
                        "sentence": "Test",
                        "options": [
                            {"text": "A", "hint": "first"},
                            {"text": "B"},
                        ],
                        "hint": "item hint",
                    }
                ],
            }
        ]
        count = _strip_hints_recursive(data)
        assert count == 2  # item-level + option-level

    def test_non_list_returns_zero(self):
        count = _strip_hints_recursive({"key": "value"})
        # Still processes the dict — but no hint key
        assert count == 0

    def test_empty_list(self):
        count = _strip_hints_recursive([])
        assert count == 0

    def test_preserves_other_fields(self):
        data = [
            {
                "type": "anagram",
                "title": "Test",
                "items": [
                    {"scrambled": "А М", "answer": "МА", "hint": "mom", "explanation": "keep"},
                ],
            }
        ]
        _strip_hints_recursive(data)
        item = data[0]["items"][0]
        assert "hint" not in item
        assert item["explanation"] == "keep"
        assert item["scrambled"] == "А М"
