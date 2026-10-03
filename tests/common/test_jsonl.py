"""Shared JSON Lines boundaries and the compatibility import."""

import json

import pytest

from scripts.agent_runtime.jsonl import jsonl_lines as runtime_lines
from scripts.common.jsonl import jsonl_lines


@pytest.mark.parametrize("sep", ["\u0085", "\u2028", "\u2029"], ids=["NEL", "LS", "PS"])
def test_jsonl_strings_survive_physical_lf_splitting(sep):
    records = [{"value": f"a{sep}b"}, {"value": "next"}]
    raw = "\r\n".join(json.dumps(row, ensure_ascii=False) for row in records) + "\r\n"
    assert [json.loads(line) for line in jsonl_lines(raw) if line] == records


@pytest.mark.parametrize("sep", ["\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"])
def test_only_lf_splits_shared_text_and_bytes_splitlines_preserves_separators(sep):
    raw = f"a{sep}b"
    assert jsonl_lines(raw + "\nc") == [raw, "c"]
    assert raw.encode("utf-8").splitlines() == [raw.encode("utf-8")]


def test_compatibility_import_is_the_shared_function():
    assert runtime_lines is jsonl_lines


def test_empty_trailing_lf_and_single_cr_removal():
    assert jsonl_lines("") == [""]
    assert jsonl_lines("a\n") == ["a", ""]
    assert jsonl_lines("a\r\r\nb\rc") == ["a\r", "b\rc"]
