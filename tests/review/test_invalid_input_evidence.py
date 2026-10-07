"""Invalid-input sources calls are rejected evidence, never hits (#9979).

The denominator is every ``REVIEW_TOOLS`` handler that can return invalid
input, read from the sources server and the V4 handlers it delegates to:
verify_word, verify_words, verify_lemma, inspect_word, inspect_words,
verify_stress, check_text, query_sum20, query_pravopys.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from scripts.review.receipts.ledger import REVIEW_TOOLS
from scripts.review.receipts.outcomes import classify_outcome
from scripts.review.validate.validate import _outcome_shown

SERVER_PATH = Path(__file__).resolve().parents[2] / ".mcp" / "servers" / "sources" / "server.py"
REJECTED = {"call_status": "ok", "hits": 0, "status": "error", "unavailable": False}

# Empty and malformed arguments. None of these reach a database.
INVALID_CALLS = (
    ("verify_word", {}),
    ("verify_word", {"word": "  "}),
    ("verify_word", {"word": 1}),
    ("verify_words", {}),
    ("verify_words", {"words": []}),
    ("verify_words", {"words": ["  "]}),
    ("verify_lemma", {}),
    ("verify_lemma", {"lemma": ""}),
    ("inspect_word", {}),
    ("inspect_word", {"word": "  "}),
    ("inspect_words", {"words": []}),
    ("inspect_words", {"words": [1]}),
    ("verify_stress", {}),
    ("verify_stress", {"word": ""}),
    ("check_text", {}),
    ("check_text", {"text": "x", "items": [{"id": "a", "text": "x"}]}),
    ("query_sum20", {}),
    ("query_sum20", {"word": "  "}),
    ("query_pravopys", {}),
    ("query_pravopys", {"topic": ""}),
)


def _server():
    spec = importlib.util.spec_from_file_location("sources_server_invalid_input", SERVER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("sources server could not be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _prose(result: object) -> str:
    if isinstance(result, tuple):
        result = result[0]
    if isinstance(result, list):
        text = result[0].text
        if not isinstance(text, str):
            raise AssertionError("handler text is not a string")
        return text
    raise AssertionError(f"unexpected handler result {type(result)!r}")


@pytest.fixture(scope="module")
def server():
    return _server()


def test_enumerated_tools_are_review_tools() -> None:
    tools = {tool for tool, _args in INVALID_CALLS}
    assert tools <= REVIEW_TOOLS
    assert tools == {
        "verify_word",
        "verify_words",
        "verify_lemma",
        "inspect_word",
        "inspect_words",
        "verify_stress",
        "check_text",
        "query_sum20",
        "query_pravopys",
    }


@pytest.mark.parametrize(("tool", "arguments"), INVALID_CALLS)
def test_real_handler_invalid_input_is_a_rejected_call(server, tool: str, arguments: dict) -> None:
    handler = getattr(server, f"handle_{tool}")
    prose = _prose(asyncio.run(handler(arguments)))
    facts = classify_outcome(tool, "ok", prose)
    assert facts == REJECTED
    record = {"status": "ok", "tool": tool, "result": prose, "outcome_facts": facts}
    assert _outcome_shown("error", record) is True
    assert _outcome_shown("no_hits", record) is False
    assert _outcome_shown("hits_but_no_support", record) is False


@pytest.mark.parametrize(
    ("tool", "result"),
    [
        ("verify_word", "'книга' — matches in VESUM:\n- **lemma**: книга"),
        ("verify_lemma", "Lemma 'книга' — NOT FOUND in VESUM."),
        (
            "verify_stress",
            json.dumps({"status": "ok", "input": "книга", "matches": [{"stressed_form": "кни́га"}]}),
        ),
        ("query_sum20", "**Official СУМ-20 entries for 'книга'**"),
    ],
)
def test_populated_calls_keep_their_hit_classification(tool: str, result: str) -> None:
    facts = classify_outcome(tool, "ok", result)
    if "NOT FOUND" in result:
        assert facts["status"] == "no_hits"
        assert facts["hits"] == 0
    else:
        assert facts["status"] == "hits_found"
        assert facts["hits"] >= 1
