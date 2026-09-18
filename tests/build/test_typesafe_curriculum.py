"""Unit + optional live tests for TypeSafe curriculum triage."""

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


def test_route_noul_cookbook_band():
    """#8195 — consistency_noul: [0.30, 0.70] inclusive → uncertain."""
    assert tc.route_noul(0.29) == "false"
    assert tc.route_noul(0.30) == "uncertain"
    assert tc.route_noul(0.50) == "uncertain"
    assert tc.route_noul(0.70) == "uncertain"
    assert tc.route_noul(0.71) == "true"


def test_route_choice_uses_top_probability_not_api_confidence():
    """#8195 — consistency_choice: gate on max(probabilities)."""
    assert tc.route_choice_top_prob(0.59) == "escalate"
    assert tc.route_choice_top_prob(0.60) == "act"
    # peaked distribution wins even if API confidence were ignored
    top = tc.choice_top_probability({"stress": 0.72, "soft_sign": 0.28}, confidence=0.1)
    assert top == pytest.approx(0.72)
    assert tc.route_choice_top_prob(top) == "act"


def test_collapse_choice_parent_on_weak_top_prob():
    """#8210 — weak leaf → parent unclear."""
    assert (
        tc.collapse_choice(
            "stress",
            {"stress": 0.45, "soft_sign": 0.40, "unclear": 0.15},
            parent_map=tc.DISTRACTOR_FAMILY_PARENTS,
        )
        == "unclear"
    )
    assert (
        tc.collapse_choice(
            "stress",
            {"stress": 0.80, "soft_sign": 0.10, "unclear": 0.10},
            parent_map=tc.DISTRACTOR_FAMILY_PARENTS,
        )
        == "stress"
    )


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
                    "probabilities": {
                        "stress": 0.55,
                        "soft_sign": 0.35,
                        "unclear": 0.10,
                    },
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
    assert ev.distractor_family.routing == "escalate"  # top p 0.55 < 0.60
    assert ev.effective_distractor_family == "unclear"
    assert ev.family_trusted is False
    assert ev.pedagogical_clarity.band == "unclear"
    assert ev.unaccented_copy_of_winner.decision == "false"
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
                "dialect_bucket": {
                    "choice": "unclear",
                    "confidence": 0.6,
                    "probabilities": {"unclear": 0.65, "standard": 0.35},
                },
                "domain": {
                    "choice": "everyday",
                    "confidence": 0.7,
                    "probabilities": {"everyday": 0.8},
                },
            },
            scores={
                "priority": {
                    "score": 0.2,
                    "confidence": 0.8,
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
    assert ev.russian_shadow_suspect.decision == "true"
    assert ev.escalate_to_sources is True
    assert ev.priority.band == "drop"
    # mid keep_for_level is uncertain, not a hard drop signal by itself
    assert ev.keep_for_level.decision == "uncertain"


def test_evaluate_lesson_readiness_mocked_qg_budget():
    """#8179 — qg_budget Choice surfaces as recommended_qg."""
    client = _FakeClient(
        _FakeResponse(
            nouls={
                "invented_upgrade_defect": 0.1,
                "cf_ready_likely": 0.85,
            },
            choices={
                "qg_budget": {
                    "choice": "light",
                    "confidence": 0.7,
                    "probabilities": {
                        "light": 0.72,
                        "full": 0.18,
                        "skip_to_gates": 0.10,
                    },
                },
            },
            scores={
                "preserve_expand_fidelity": {
                    "score": 1.8,
                    "confidence": 0.9,
                    "legend": {
                        0: "invented_rewrite",
                        1: "light_expand",
                        2: "faithful_preserve_expand",
                    },
                },
                "immersion_fit": {
                    "score": 1.2,
                    "confidence": 0.7,
                    "legend": {0: "english_heavy", 1: "mixed", 2: "immersion_ok"},
                },
                "decolonize_risk": {
                    "score": 1.9,
                    "confidence": 0.85,
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
    assert ev.cf_ready is True
    assert ev.preserve_expand_fidelity.band == "faithful_preserve_expand"
    assert ev.decolonize_risk.band == "clean"


def test_propose_and_run_verify_dispatches_local_tool():
    """#8196 — Choice selects tool; injectable runner executes."""
    client = _FakeClient(
        _FakeResponse(
            choices={
                "verify_tool": {
                    "choice": "check_russian_shadow",
                    "confidence": 0.9,
                    "probabilities": {
                        "check_russian_shadow": 0.85,
                        "verify_stress": 0.10,
                        "none": 0.05,
                    },
                }
            }
        )
    )
    calls: list[str] = []

    def fake_ru(word: str):
        calls.append(word)
        return {"matches_russian": True, "confidence": 0.9}

    prop = tc.propose_and_run_verify(
        word="участвувати",
        context="calque suspect",
        client=client,
        russian_shadow_fn=fake_ru,
    )
    assert prop.tool == "check_russian_shadow"
    assert prop.routing == "act"
    assert prop.ran is True
    assert calls == ["участвувати"]
    assert prop.verify_result is not None
    assert prop.verify_result["matches_russian"] is True


def test_propose_verify_skips_run_when_top_prob_weak():
    client = _FakeClient(
        _FakeResponse(
            choices={
                "verify_tool": {
                    "choice": "verify_stress",
                    "confidence": 0.4,
                    "probabilities": {
                        "verify_stress": 0.40,
                        "none": 0.35,
                        "check_russian_shadow": 0.25,
                    },
                }
            }
        )
    )
    prop = tc.propose_and_run_verify(
        word="мʼята",
        client=client,
        verify_stress_fn=lambda w: {"status": "ok"},
    )
    assert prop.routing == "escalate"
    assert prop.ran is False
    assert prop.verify_result is None


def test_preparsed_candidates_and_pick():
    """#8208 — generators + Choice pick verbatim."""
    stress = tc.stress_candidates("мята")
    assert "мята" in stress
    assert any("\u0301" in s for s in stress)
    apos = tc.apostrophe_candidates("м'ята")
    assert any("ʼ" in s or "'" in s for s in apos)
    soft = tc.soft_sign_candidates("мати")
    assert any("ь" in s for s in soft)

    client = _FakeClient(
        _FakeResponse(
            nouls={"any_adequate": 0.95},
            choices={
                "pick": {
                    "choice": "мʼя́та",
                    "confidence": 0.9,
                    "probabilities": {"мʼя́та": 0.9, "мʼята": 0.1},
                }
            },
        )
    )
    pick = tc.pick_preparsed_value(
        question="Correct stressed form with apostrophe",
        candidates=["мʼята", "мʼя́та"],
        client=client,
    )
    assert pick.selected == "мʼя́та"
    assert pick.routing == "act"


def test_guardrails_block_on_calque():
    """#8209 — clear calque + block severity → block."""
    client = _FakeClient(
        _FakeResponse(
            nouls={
                "russian_calque_suspect": 0.95,
                "invented_upgrade_defect": 0.05,
                "immersion_leak": 0.05,
            },
            scores={
                "hazard_severity": {
                    "score": 1.9,
                    "confidence": 0.9,
                    "legend": {0: "none", 1: "mild", 2: "block"},
                }
            },
        )
    )
    ev = tc.evaluate_upgrade_io_guardrails(
        level="a2",
        excerpt="Я участвую в проекті.",
        client=client,
    )
    assert ev.action == "block"


def test_guardrails_review_on_uncertain_noul():
    client = _FakeClient(
        _FakeResponse(
            nouls={
                "russian_calque_suspect": 0.50,
                "invented_upgrade_defect": 0.10,
                "immersion_leak": 0.10,
            },
            scores={
                "hazard_severity": {
                    "score": 0.2,
                    "confidence": 0.8,
                    "legend": {0: "none", 1: "mild", 2: "block"},
                }
            },
        )
    )
    ev = tc.evaluate_upgrade_io_guardrails(
        level="b1",
        excerpt="Нормальний уривок.",
        client=client,
    )
    assert ev.action == "review"


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
