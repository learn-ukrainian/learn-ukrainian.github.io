from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.json_parse import extract_json_object


def test_extracts_bare_json_object():
    payload = extract_json_object('{"score": 9, "verdict": "PASS"}')
    assert payload == {"score": 9, "verdict": "PASS"}


def test_extracts_json_object_from_json_fence():
    payload = extract_json_object('```json\n{"score": 8, "verdict": "REVISE"}\n```')
    assert payload == {"score": 8, "verdict": "REVISE"}


def test_extracts_json_object_with_preamble_and_trailing_text():
    response = 'Reviewer output follows:\n{"score": 7, "verdict": "REVISE"}\nDone.'
    payload = extract_json_object(response)
    assert payload == {"score": 7, "verdict": "REVISE"}


def test_extracts_nested_braces_json_object():
    response = """
Preamble
{"findings": [{"location": "body", "raw": {"nested": {"count": 2}}}], "score": 9}
Trailing text
"""
    payload = extract_json_object(response)
    assert payload == {
        "findings": [{"location": "body", "raw": {"nested": {"count": 2}}}],
        "score": 9,
    }


@pytest.mark.parametrize(
    ("response", "excerpt"),
    [
        ('{"score": 9', '{"score": 9'),
        ("No JSON here at all.", "No JSON here at all."),
        ("", "<empty>"),
    ],
)
def test_extract_json_object_failures_include_excerpt(response: str, excerpt: str):
    with pytest.raises(ValueError, match="response excerpt"):
        extract_json_object(response)

    with pytest.raises(ValueError) as excinfo:
        extract_json_object(response)

    assert excerpt in str(excinfo.value)
