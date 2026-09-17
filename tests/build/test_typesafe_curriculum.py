"""Unit + optional live tests for TypeSafe curriculum triage (#8177–#8179)."""

from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

from scripts.build import typesafe_curriculum as tc


class _FakeResponse:
    def __init__(
        self,
        *,
        nouls: dict | None = None,
        choices: dict | None = None,
        scores: dict | None = None,
        model: str = "jev-test",
        input_tokens: int = 10,
        output_tokens: int = 5,
    ):
        self.nouls = {
            k: SimpleNamespace(noul=v) for k, v in (nouls or {}).items()
        }
        self.choices = {
            k: SimpleNamespace(
                choice=v["choice"],
                confidence=v.get("confidence", 0.9),
                probabilities=v.get("probabilities", {}),
            )
            for k, v in (choices or {}).items()
        }
        self.scores = {
            k: SimpleNamespace(
                score=v["score"],
                confidence=v.get("confidence", 0.5),
                legend=v.get("legend", {0: "a", 1: "b", 2: "c"}),
                probabilities=v.get("probabilities", {}),
            )
            for k, v in (scores or {}).items()
        }
        self.model = model
        self.usage = SimpleNamespace(
            input_tokens=input_tokens, output_tokens=output_tokens
        )
        self.request_id = "req-test"


class _FakeClient:
    def __init__(self, response: _FakeResponse):
        self.response = response
        self.calls: list[dict] = []

    def system_one(self, state, questions, *, model=None):
        self.calls.append({"state": state, "questions": questions, "model": model})
        return self.response

    def close(self):
        return None


def test_exact_winner_and_unaccented_heuristics():
    assert tc.exact_winner_present(["мʼя́та", "мʼята"], "мʼя́та")
    assert not tc.exact_winner_present(["мʼята"], "мʼя́та")
    assert tc.has_unaccented_copy(["мʼя́та", "мʼята"], "мʼя́та")
    assert not tc.has_unaccented_copy(["мʼя́та", "мʼя́со"], "мʼя́та")


def test_evaluate_ec_item_mocked_needs_repair_on_thin_options():
    """#8177 — code routes needs_repair from mechanical + clarity band."""
    client = _FakeClient(
        _FakeResponse(
            nouls={
                "has_winning_chip": 0.95,
                "too_few_options": 0.9,
                "unaccented_copy_of_winner": 0.1,
                "a1_en_scaffold_present": 0.8,
            },
            choices={
                "distractor_family": {
                    "choice": "stress",
                    "confidence": 0.8,
                    "probabilities": {"stress": 0.8},
                }
            },
            scores={
                "pedagogical_clarity": {
                    "score": 0.4,
                    "confidence": 0.4,
                    "legend": {0: "unclear", 1: "usable", 2: "strong"},
                }
            },
        )
    )
    ev = tc.evaluate_ec_item(
        sentence="Я люблю __.",
        error="мята",
        correct_form="мʼя́та",
        options=["мʼя́та"],  # thin
        level="a1",
        prompt_en="Choose the correct form.",
        client=client,
    )
    assert len(client.calls) == 1
    assert set(client.calls[0]["questions"]) == {
        "has_winning_chip",
        "too_few_options",
        "unaccented_copy_of_winner",
        "a1_en_scaffold_present",
        "distractor_family",
        "pedagogical_clarity",
    }
    assert ev.option_count == 1
    assert ev.needs_repair is True
    assert ev.distractor_family.choice == "stress"
    assert ev.pedagogical_clarity.band == "unclear"
    assert ev.receipt.model == "jev-test"
    assert ev.receipt.input_tokens == 10


def test_evaluate_vocab_row_mocked_escalates_russian_shadow():
    """#8178 — russian_shadow_suspect escalates; does not claim VESUM fact."""
    client = _FakeClient(
        _FakeResponse(
            nouls={
                "keep_for_level": 0.4,
                "ocr_junk": 0.05,
                "russian_shadow_suspect": 0.92,
                "proper_name": 0.01,
            },
            choices={
                "dialect_bucket": {"choice": "unclear", "confidence": 0.6},
                "domain": {"choice": "everyday", "confidence": 0.7},
            },
            scores={
                "priority": {
                    "score": 0.2,
                    "legend": {0: "drop", 1: "optional", 2: "core"},
                }
            },
        )
    )
    ev = tc.evaluate_vocab_row(
        lemma="здається",
        example="Мені здається, що...",
        level="a2",
        note="possible calque of кажется",
        client=client,
    )
    assert ev.russian_shadow_suspect.is_true
    assert ev.escalate_to_sources is True
    assert ev.priority.band == "drop"


def test_evaluate_lesson_readiness_mocked_qg_budget():
    """#8179 — qg_budget Choice surfaces as recommended_qg."""
    client = _FakeClient(
        _FakeResponse(
            nouls={
                "invented_upgrade_defect": 0.1,
                "cf_ready_likely": 0.85,
            },
            choices={
                "qg_budget": {"choice": "light", "confidence": 0.7},
            },
            scores={
                "preserve_expand_fidelity": {
                    "score": 1.8,
                    "legend": {
                        0: "invented_rewrite",
                        1: "light_expand",
                        2: "faithful_preserve_expand",
                    },
                },
                "immersion_fit": {
                    "score": 1.2,
                    "legend": {0: "english_heavy", 1: "mixed", 2: "immersion_ok"},
                },
                "decolonize_risk": {
                    "score": 1.9,
                    "legend": {0: "clear_risk", 1: "mild", 2: "clean"},
                },
            },
        )
    )
    ev = tc.evaluate_lesson_readiness(
        level="a1",
        slug="special-signs",
        lesson_excerpt="Апостроф і мʼякий знак...",
        activities_excerpt="error_correction options...",
        gate_summary="lesson_gates: pass",
        client=client,
    )
    assert ev.recommended_qg == "light"
    assert ev.cf_ready_likely.is_true
    assert ev.preserve_expand_fidelity.band == "faithful_preserve_expand"
    assert ev.decolonize_risk.band == "clean"


@pytest.mark.live_network
@pytest.mark.skipif(
    os.environ.get("TYPESAFE_LIVE", "") != "1",
    reason="Set TYPESAFE_LIVE=1 to hit jev-latest (spend).",
)
def test_live_ec_item_thin_fixture():
    """#8177 live smoke — thin EC should need_repair."""
    ev = tc.evaluate_ec_item(
        sentence="Я пʼю ___.",
        error="мята",
        correct_form="мʼя́та",
        options=["мʼя́та"],
        level="a1",
        prompt_en="Pick the correct spelling with soft sign / apostrophe.",
    )
    assert ev.receipt.model
    assert ev.option_count == 1
    assert ev.needs_repair is True
    assert ev.receipt.input_tokens is not None


@pytest.mark.live_network
@pytest.mark.skipif(
    os.environ.get("TYPESAFE_LIVE", "") != "1",
    reason="Set TYPESAFE_LIVE=1 to hit jev-latest (spend).",
)
def test_live_vocab_calque_suspect():
    """#8178 live smoke — clear Russian calque should escalate."""
    ev = tc.evaluate_vocab_row(
        lemma="участвувати",
        example="Я участвую в проекті.",
        level="a2",
        note="Russian участвовать calque; Ukrainian брати участь",
    )
    assert ev.receipt.model
    assert ev.receipt.input_tokens is not None
    assert ev.russian_shadow_suspect.is_true
    assert ev.escalate_to_sources is True


@pytest.mark.live_network
@pytest.mark.skipif(
    os.environ.get("TYPESAFE_LIVE", "") != "1",
    reason="Set TYPESAFE_LIVE=1 to hit jev-latest (spend).",
)
def test_live_lesson_readiness_a1_snippet():
    """#8179 live smoke — A1 special-signs-ish excerpt returns qg_budget."""
    ev = tc.evaluate_lesson_readiness(
        level="a1",
        slug="special-signs",
        lesson_excerpt=(
            "# Спеціальні знаки\n\n"
            "В українській мові є апостроф і мʼякий знак.\n"
            "English scaffold (A1 by design): soft sign vs apostrophe.\n"
        ),
        activities_excerpt=(
            "error_correction: options [мʼя́та, мʼята]; correctForm мʼя́та"
        ),
        gate_summary="local gates not yet run; pilot readiness only",
    )
    assert ev.receipt.model
    assert ev.qg_budget.choice in {"full", "light", "skip_to_gates"}
    assert ev.receipt.input_tokens is not None
