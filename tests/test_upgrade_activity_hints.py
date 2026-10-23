"""Tests for scripts/tools/upgrade_activity_hints.py — hint classification and YAML parsing."""

from __future__ import annotations

import sys
from pathlib import Path

# Add scripts/ to path
scripts_dir = str(Path(__file__).resolve().parent.parent / "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from tools.upgrade_activity_hints import (
    parse_agy_response,
)

# --- is_hint_vague ---


# --- count_vague_hints ---


# --- parse_agy_response ---


class TestParseAgyResponse:
    def test_plain_yaml(self):
        response = """\
- type: quiz
  focus: "Що ми чуємо? (звуки | літери)"
  items: 6
- type: match-up
  focus: "Match pairs"
  pairs:
  - "привіт ↔ hello"
"""
        result = parse_agy_response(response)
        assert result is not None
        assert len(result) == 2
        assert result[0]["type"] == "quiz"
        assert result[1]["type"] == "match-up"

    def test_fenced_yaml(self):
        response = """\
```yaml
- type: fill-in
  focus: "Я {люблю|подобається} читати."
  items: 4
```
"""
        result = parse_agy_response(response)
        assert result is not None
        assert len(result) == 1
        assert result[0]["type"] == "fill-in"

    def test_not_a_list(self):
        response = "type: quiz\nfocus: test\n"
        result = parse_agy_response(response)
        assert result is None

    def test_missing_required_fields(self):
        response = "- items: 6\n  something: else\n"
        result = parse_agy_response(response)
        assert result is None


# --- build_agy_prompt ---
