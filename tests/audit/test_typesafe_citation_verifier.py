"""Offline tests for the TypeSafe citation verifier (#8192)."""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path

import pytest

from scripts.audit import typesafe_citation_verifier as v
from scripts.typesafe.client import TypeSafeError

FIXTURE = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "typesafe_citation_cases.jsonl"
SOURCE = "Альфа сидить на дубі. Бета співає пісню про мед."


class FakeClient:
    def __init__(self, response: dict | None = None, error: BaseException | None = None):
        self.response = response if response is not None else _answer("supports", 0.91)
        self.error = error
        self.calls: list[dict] = []

    def system_one(self, state, questions, *, model="jev-latest", timeout=60):
        self.calls.append({"state": state, "questions": questions, "model": model, "timeout": timeout})
        if self.error is not None:
            raise self.error
        return self.response


def _answer(choice: str, confidence: float, *, probabilities: dict | None = None, drop: str | None = None) -> dict:
    if probabilities is None:
        others = [opt for opt in v.CHOICE_OPTIONS if opt != choice]
        probabilities = {opt: 0.1 for opt in others}
        probabilities[choice] = 1.0 - 0.1 * len(others)
    body: dict = {
        "choice": choice,
        "confidence": confidence,
        "probabilities": probabilities,
    }
    if drop:
        body.pop(drop, None)
    return {
        "model": "jev-test",
        "answers": {v.QUESTION_ID: body},
        "usage": {"input_tokens": 11, "output_tokens": 3},
    }


def _case(quote: str = "Альфа сидить на дубі.", source: str = SOURCE, claim: str = "Alpha sits on an oak.") -> dict:
    return {"id": "t", "claim": claim, "quote": quote, "source_text": source}


def test_exact_hit_calls_client_once_and_verifies():
    client = FakeClient()
    receipt = v.verify_citation(_case(), client=client)
    assert len(client.calls) == 1
    criteria = client.calls[0]["questions"][v.QUESTION_ID]["criteria"]
    assert set(criteria) == {"supports", "contradicts", "says_nothing"}
    assert receipt["verdict"] == "verified"
    assert receipt["accepted"] is True
    assert receipt["decided_by"] == "system_one"
    assert receipt["model"] == "jev-test"
    assert receipt["question_ids"] == [v.QUESTION_ID]
    assert receipt["confidence"] == pytest.approx(0.91)
    assert receipt["usage"]["input_tokens"] == 11


def test_fabricated_quote_does_not_call_the_client():
    client = FakeClient()
    receipt = v.verify_citation(_case(quote="Цього речення в джерелі немає."), client=client)
    assert client.calls == []
    assert receipt["verdict"] == "fabricated"
    assert receipt["decided_by"] == "deterministic"
    assert receipt["accepted"] is False
    assert receipt["model"] is None


@pytest.mark.parametrize(
    ("quote", "source"),
    [
        ("риб'ячу гідність береже", "риб\u2019ячу гідність береже"),
        ("риб\u02bcячу гідність береже", "риб'ячу гідність береже"),
        ("Та принесла я вам літечко", "Та принесла\n\nя вам   літечко."),
        ("Київ-місто на Дніпрі", "Київ\u2014місто на Дніпрі"),
        ("риба мовчить тут", "риб\u00adа мовчить тут"),
        ('Він сказав "мед"', "Він сказав «мед» вчора"),
    ],
)
def test_apostrophe_whitespace_dash_and_quote_variants_still_match(quote, source):
    client = FakeClient()
    receipt = v.verify_citation(_case(quote=quote, source=source), client=client)
    assert len(client.calls) == 1
    assert receipt["verdict"] == "verified"


def test_elision_matches_in_order_and_fails_out_of_order():
    source = "Альфа сидить на дубі. Бета співає пісню. Гамма мовчить."
    in_order = FakeClient()
    hit = v.verify_citation(_case(quote="Альфа сидить [...] Бета співає", source=source), client=in_order)
    assert len(in_order.calls) == 1
    assert hit["verdict"] == "verified"

    out_of_order = FakeClient()
    miss = v.verify_citation(_case(quote="Бета співає […] Альфа сидить", source=source), client=out_of_order)
    assert out_of_order.calls == []
    assert miss["verdict"] == "fabricated"

    dotted = FakeClient()
    dotted_hit = v.verify_citation(_case(quote="Альфа сидить ... Гамма мовчить", source=source), client=dotted)
    assert len(dotted.calls) == 1
    assert dotted_hit["verdict"] == "verified"

    ellipsis_only = FakeClient()
    empty_segments = v.verify_citation(_case(quote="…", source=source), client=ellipsis_only)
    assert ellipsis_only.calls == []
    assert empty_segments["verdict"] == "fabricated"


def test_empty_quote_or_source_is_fabricated_without_a_call():
    client = FakeClient()
    assert v.verify_citation(_case(quote=""), client=client)["verdict"] == "fabricated"
    assert v.verify_citation(_case(quote="   \n"), client=client)["verdict"] == "fabricated"
    assert v.verify_citation(_case(source=""), client=client)["verdict"] == "fabricated"
    assert client.calls == []


def test_contradicts_at_low_confidence_is_still_contradicted():
    client = FakeClient(_answer("contradicts", 0.11))
    receipt = v.verify_citation(_case(), client=client)
    assert receipt["verdict"] == "contradicted"
    assert receipt["accepted"] is False
    assert receipt["confidence"] == pytest.approx(0.11)


def test_supports_threshold_is_the_module_constant():
    below = FakeClient(_answer("supports", 0.79))
    assert v.verify_citation(_case(), client=below)["verdict"] == "needs_human_review"
    at = FakeClient(_answer("supports", 0.80))
    hit = v.verify_citation(_case(), client=at)
    assert hit["verdict"] == "verified"
    assert hit["accepted"] is True
    assert v.ACCEPT_CONFIDENCE == 0.80


def test_says_nothing_at_threshold_is_unsupported_not_an_accept():
    low = FakeClient(_answer("says_nothing", 0.79))
    assert v.verify_citation(_case(), client=low)["verdict"] == "needs_human_review"
    high = FakeClient(_answer("says_nothing", 0.80))
    receipt = v.verify_citation(_case(), client=high)
    assert receipt["verdict"] == "unsupported"
    assert receipt["accepted"] is False


def test_api_failure_needs_human_review():
    client = FakeClient(error=TypeSafeError("System One HTTP 503"))
    receipt = v.verify_citation(_case(), client=client)
    assert receipt["verdict"] == "needs_human_review"
    assert receipt["decided_by"] == "system_one"
    assert receipt["accepted"] is False
    assert "503" not in json.dumps(receipt)
    dumped = json.dumps(receipt)
    assert "Bearer" not in dumped


def test_malformed_answer_needs_human_review():
    missing_confidence = FakeClient(_answer("supports", 0.95, drop="confidence"))
    receipt = v.verify_citation(_case(), client=missing_confidence)
    assert receipt["verdict"] == "needs_human_review"
    assert receipt["model"] == "jev-test"
    assert receipt["choice"] is None

    bad_choice = FakeClient(_answer("maybe", 0.99))
    assert v.verify_citation(_case(), client=bad_choice)["verdict"] == "needs_human_review"

    not_an_object = FakeClient({"model": "jev-test", "answers": None})
    assert v.verify_citation(_case(), client=not_an_object)["verdict"] == "needs_human_review"


def test_missing_probabilities_needs_human_review():
    client = FakeClient(_answer("supports", 0.95, drop="probabilities"))
    receipt = v.verify_citation(_case(), client=client)
    assert receipt["verdict"] == "needs_human_review"
    assert receipt["accepted"] is False
    assert receipt["choice"] is None


def test_non_numeric_probability_needs_human_review():
    probabilities = {"supports": "0.8", "contradicts": 0.1, "says_nothing": 0.1}
    client = FakeClient(_answer("supports", 0.95, probabilities=probabilities))
    receipt = v.verify_citation(_case(), client=client)
    assert receipt["verdict"] == "needs_human_review"
    assert receipt["accepted"] is False


def test_choice_that_is_not_the_argmax_needs_human_review():
    probabilities = {"supports": 0.2, "contradicts": 0.7, "says_nothing": 0.1}
    client = FakeClient(_answer("supports", 0.95, probabilities=probabilities))
    receipt = v.verify_citation(_case(), client=client)
    assert receipt["verdict"] == "needs_human_review"
    assert receipt["accepted"] is False
    assert receipt["choice"] is None


def test_overflow_confidence_needs_human_review():
    payload = _answer("supports", 0.95)
    payload["answers"][v.QUESTION_ID]["confidence"] = 10**400
    client = FakeClient(payload)
    receipt = v.verify_citation(_case(), client=client)
    assert receipt["verdict"] == "needs_human_review"
    assert receipt["accepted"] is False


def test_substring_inside_a_word_is_not_a_match():
    assert v.quote_occurs_in_source("art", "A cart.") is False
    assert v.quote_occurs_in_source("п'ять", "У хлопця є п'ять яблук.") is True
    assert v.quote_occurs_in_source("ять", "У хлопця є п'ять яблук.") is False
    assert v.quote_word_tokens("п'ять") == ["п'ять"]


def test_two_word_quote_needs_human_review_without_a_client_call():
    client = FakeClient()
    receipt = v.verify_citation(_case(quote="Альфа сидить"), client=client)
    assert client.calls == []
    assert receipt["verdict"] == "needs_human_review"
    assert receipt["decided_by"] == "deterministic"
    assert receipt["reason"] == "quote_too_short"
    assert receipt["accepted"] is False
    assert v.MIN_QUOTE_WORD_TOKENS == 3


def test_unexpected_exception_needs_human_review_and_the_run_continues(monkeypatch):
    def explode(case, **kwargs):
        if case.get("id") == "bad":
            raise RuntimeError("leak this message")
        return v._base_receipt(case, verdict="fabricated", decided_by="deterministic")

    monkeypatch.setattr(v, "verify_citation", explode)
    good = _case()
    bad = _case()
    bad["id"] = "bad"
    results = v.verify_citations([good, bad, good])
    assert [row["verdict"] for row in results] == ["fabricated", "needs_human_review", "fabricated"]
    assert results[1]["reason"] == "internal_error"
    assert results[1]["exception_type"] == "RuntimeError"
    assert "leak this message" not in json.dumps(results[1])


def test_mock_cli_fail_closes_without_network(tmp_path):
    src = tmp_path / "cases.jsonl"
    src.write_text(
        "\n".join(
            [
                json.dumps(_case(), ensure_ascii=False),
                json.dumps(_case(quote="немає такого рядка"), ensure_ascii=False),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    out = tmp_path / "receipt.json"
    code = v.main(["--input", str(src), "--out", str(out), "--mock"])
    assert code == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["mock"] is True
    assert [row["verdict"] for row in payload["citations"]] == ["needs_human_review", "fabricated"]
    assert "Authorization" not in out.read_text(encoding="utf-8")


def test_fixture_has_fifty_labelled_classes_and_quote_marks():
    rows = v.load_cases(FIXTURE)
    assert len(rows) == 50
    counts = Counter(row["expected"] for row in rows)
    assert counts["accurate"] >= 10
    assert counts["fabricated"] >= 10
    assert counts["contradicted"] >= 10
    assert counts["out_of_context"] >= 10
    assert sum(counts.values()) == 50
    for row in rows:
        assert row["table"] == "literary_texts"
        assert isinstance(row["row_id"], int)
        found = v.quote_occurs_in_source(row["quote"], row["source_text"])
        if row["expected"] == "fabricated":
            assert row["invented_quote"] is True
            assert row["quote_origin"] == "invented"
            assert found is False
        else:
            assert row["invented_quote"] is False
            assert row["quote_origin"] == "corpus"
            assert found is True


@pytest.mark.live_network
@pytest.mark.skipif(
    os.environ.get("TYPESAFE_LIVE", "") != "1",
    reason="Set TYPESAFE_LIVE=1 to hit jev-latest (spend).",
)
def test_live_one_citation_returns_a_model_id():
    case = {
        "id": "live-smoke",
        "claim": "The hornet says the bee's labor can bring her death instead of a reward.",
        "quote": "приносячи замість нагороди смерть",
        "source_text": (
            "Чи знаєш ти, що плоди твоєї праці не стільки тобі самій, як людям корисні, "
            "а тобі часто і шкодять, приносячи замість нагороди смерть; одначе не перестаєш "
            "через дурість свою збирати мед."
        ),
    }
    receipt = v.verify_citation(case)
    assert receipt["decided_by"] == "system_one"
    assert receipt["model"]
    assert receipt["verdict"] in v.VERDICTS
    assert receipt["verdict"] != "fabricated"
    dumped = json.dumps(receipt)
    assert "Bearer" not in dumped
    assert "typesafe-ai.key" not in dumped
