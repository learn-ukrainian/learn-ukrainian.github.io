"""Unit + optional live tests for TypeSafe curriculum triage."""

from __future__ import annotations

from types import SimpleNamespace

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
