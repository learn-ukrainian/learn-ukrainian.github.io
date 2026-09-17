"""Hermetic tests for scripts/typesafe/semantic_find.py.

`_FakeClient` never touches the network or even imports `typesafe_sdk`, so
this suite runs the same with or without the TypeSafe SDK installed — matching
`tests/build/test_typesafe_curriculum.py` in the same epic (#6943) and CI's
lack of the `pypi.typesafe.ai` extra index.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from scripts.typesafe.semantic_find import DEFAULT_MODEL, find

LINES = [
    "Contributions must be your own original work.",
    "You may not upload content you do not have the rights to.",
    "We may suspend or terminate accounts that violate these terms.",
    "Disputes are resolved through binding arbitration.",
]


class _FakeResponse:
    def __init__(self, *, choice_probabilities: dict[str, float], noul: float):
        top_choice = max(choice_probabilities, key=choice_probabilities.get)
        self.nouls = {"exists": SimpleNamespace(noul=noul)}
        self.choices = {
            "where": SimpleNamespace(
                choice=top_choice,
                confidence=choice_probabilities[top_choice],
                probabilities=choice_probabilities,
            )
        }


class _FakeClient:
    def __init__(self, response: _FakeResponse):
        self.response = response
        self.calls: list[dict] = []
        self.closed = False

    def system_one(self, state, questions, *, model=None):
        self.calls.append({"state": state, "questions": questions, "model": model})
        return self.response

    def close(self):
        self.closed = True


def test_find_returns_relevance_in_line_order_and_exists():
    client = _FakeClient(
        _FakeResponse(
            choice_probabilities={"L000": 0.05, "L001": 0.85, "L002": 0.05, "L003": 0.05},
            noul=0.93,
        )
    )

    result = find(LINES, "can I upload content I don't own?", client=client)

    assert result["exists"] == pytest.approx(0.93)
    assert result["relevance"] == [
        pytest.approx(0.05),
        pytest.approx(0.85),
        pytest.approx(0.05),
        pytest.approx(0.05),
    ]


def test_find_empty_lines_short_circuits_without_a_request():
    client = _FakeClient(_FakeResponse(choice_probabilities={"L000": 1.0}, noul=1.0))

    result = find([], "anything", client=client)

    assert result == {"exists": 0.0, "relevance": []}
    assert client.calls == []


def test_find_tags_lines_and_asks_where_and_exists_questions():
    client = _FakeClient(
        _FakeResponse(choice_probabilities={"L000": 1.0, "L001": 0.0}, noul=0.5)
    )

    find(["first line", "second line"], "what is in the second line?", client=client)

    assert len(client.calls) == 1
    call = client.calls[0]
    assert call["state"] == "L000| first line\nL001| second line"
    assert set(call["questions"]) == {"where", "exists"}

    where = call["questions"]["where"]
    assert set(where.criteria) == {"L000", "L001"}
    assert "second line" in where.instructions

    exists = call["questions"]["exists"]
    assert "second line" in exists.instructions


def test_find_defaults_to_the_module_model_and_respects_an_override():
    client = _FakeClient(_FakeResponse(choice_probabilities={"L000": 1.0}, noul=0.1))

    find(["only line"], "anything", client=client)
    assert client.calls[-1]["model"] == DEFAULT_MODEL

    find(["only line"], "anything", client=client, model="jev-1.12")
    assert client.calls[-1]["model"] == "jev-1.12"


def test_find_does_not_close_an_injected_client():
    client = _FakeClient(_FakeResponse(choice_probabilities={"L000": 1.0}, noul=0.2))

    find(["only line"], "anything", client=client)

    assert client.closed is False


def test_find_missing_probabilities_default_to_zero():
    client = _FakeClient(_FakeResponse(choice_probabilities={"L000": 1.0}, noul=0.4))

    result = find(["a", "b", "c"], "query", client=client)

    assert result["relevance"] == [pytest.approx(1.0), 0.0, 0.0]
