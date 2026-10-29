"""The G3 no-paid proof of uk-behaviour/2: every case passes, with no provider calls."""

from __future__ import annotations

import pytest

from scripts.eval.uk_behaviour import prove
from scripts.eval.uk_behaviour.contract import FAMILIES

RESULT = prove.run()
CASES = {case["case"]: case for case in RESULT["cases"]}

# Branches the protocol names for G3 (lines 463-481 and 621-631); the proof may not drop one.
REQUIRED = [
    "scored perfect review",
    "scored correct clean no-change",
    "scored useful review with one false correction",
    "scored padder within its size cap",
    "scored refusal on an answerable item",
    "scored accuse-everything with a protected harm",
    "partial answer is accepted but incomplete",
    "empty output scores as missing",
    "zero-required-claim evidence gap scores 1",
    "missing receipt earns its claim zero",
    "fabricated receipt invalidates the cell",
    "a judge binding no ledger holds is an evaluator error, and labelled harm still counts",
    "output over its byte cap is overproduction",
    "claims over the cap are overproduction, not evaluator failure",
    "off-contract padding that exhausts the judge is overproduction",
    "in-contract judge exhaustion is an evaluator failure",
    "verified harm scores -2 even in an unresolved cell",
    "fresh writer gets exactly the production prompt over four inputs, no mode field",
    "a fresh writer that reached Sources is not scorable",
] + [f"{family}: maximum-size output with every claim off-label fits 32 calls" for family in FAMILIES]


@pytest.mark.parametrize("name", sorted(CASES))
def test_proof_case(name: str) -> None:
    case = CASES[name]
    assert case["observed"] == case["expected"], case


@pytest.mark.parametrize("name", REQUIRED)
def test_required_branch_is_proved(name: str) -> None:
    assert name in CASES


def test_worked_ordering_is_literal() -> None:
    rewards = [
        CASES[f"scored {name}"]["observed"][-1]
        for name in (
            "perfect review",
            "useful review with one false correction",
            "refusal on an answerable item",
            "accuse-everything with a protected harm",
        )
    ]
    assert rewards == [1.0, 0.829, -1.0, -2.0]
    assert CASES["scored padder within its size cap"]["observed"][0][-1] == 0.28
    assert RESULT["pass"]
