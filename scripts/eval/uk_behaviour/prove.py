"""The G3 no-paid proof: synthetic fixtures through the complete scoring path.

No provider, dispatcher or Sources server is called. Each case builds a
synthetic request, candidate output, verified receipt ledgers, a judge reply
bound by ``judge.bind_reply`` and a label, scores the cell with
``scorer.score_cell`` and compares the result with a literal expectation:

- the worked ordering of the protocol (O = 10, S = 0), components and reward;
- the clean no-change, partial-answer, empty-output, zero-required-claim gap,
  missing-receipt, fabricated-receipt and size-exhaustion branches;
- maximum-size evidence coverage of every family within the 32-call judge cap;
- the fresh-writer tool boundary and the held-out isolation refusals.

Fixture text is placeholder ASCII: it asserts nothing about Ukrainian.
"""

from __future__ import annotations

import json
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from scripts.common.scratch import ensure_scratch_root
from scripts.review.receipts import ledger

from . import adapters, coverage, judge
from .binding import LedgerIndex, LedgerRef
from .contract import (
    COMPLETE,
    FAMILIES,
    INVALID_FABRICATED_RECEIPT,
    INVALID_OVERPRODUCTION,
    UNRESOLVED_EVALUATOR,
    load_manifest,
)
from .reward import Components, reward
from .scorer import score_cell

PROOF = "uk-behaviour-g3-no-paid/1"
MANIFEST_SHA = "0" * 64
WORKED = {  # the frozen table: (T, C, P, F, X, H, R) with O = 10 and S = 0
    "perfect_or_clean": (1, 1.0, 1.0, 0, 0, 0, 1.0),
    "good_one_error": (1, 0.9, 1.0, 1, 0, 0, 0.829),
    "padder": (1, 1.0, 1.0, 0, 8, 0, 0.28),
    "refusal": (0, 0.0, 0.0, 0, 0, 0, -1.0),
    "accuse_everything": (0, 0.0, 0.0, 10, 0, 1, -2.0),
}


class Fixture:
    """Ledgers, request and label of one synthetic cell, built under a private temporary root."""

    def __init__(self, root: Path, name: str, family: str = "exercise_review") -> None:
        self.family = family
        self.item = {"item_id": f"syn-{name}", "judging_mode": FAMILIES[family].modes[0], "level": "A1"}
        if family == "exercise_review":
            self.item |= {"exercise": {"items": []}, "target": "synthetic", "learner_state": {}}
        elif family == "card_review":
            self.item |= {"card": {}, "context": "synthetic"}
        self.refs: list[LedgerRef] = []
        self.paths: dict[str, Path] = {}
        for role in ("candidate", "judge"):
            path = root / f"rv-{name}" / f"{role}.jsonl"
            ledger.create_empty_ledger(path)
            self.paths[role] = path
            self.refs.append(LedgerRef(role, path, f"rv-{name}", role, MANIFEST_SHA))

    def receipt(self, role: str, word: str, *, found: bool = True) -> str:
        result = f"Found: {1 if found else 0}/1\n- **{word}** — {'FOUND' if found else 'NOT FOUND'}"
        return ledger.append(
            self.paths[role],
            review_id=self.paths[role].parent.name,
            attempt_id=role,
            manifest_sha256=MANIFEST_SHA,
            tool="verify_words",
            server_version="fixture",
            arguments={"words": [word]},
            snapshots={},
            status="ok",
            result=result,
        )

    def index(self) -> LedgerIndex:
        return LedgerIndex(self.refs)


def _envelope(item: dict[str, Any], findings: list[dict[str, Any]], outcome: str | None = None, gaps=()) -> str:
    return json.dumps(
        {
            "item_id": item["item_id"],
            "judging_mode": item["judging_mode"],
            "outcome": outcome or ("findings" if findings else "clean"),
            "findings": findings,
            "gaps": list(gaps),
        },
        indent=2,
    )


def _finding(fid: str, claim: str, receipts: list[str], *, defect: str = "form", edit: bool = False) -> dict:
    return {
        "id": fid,
        "defect": defect,
        "location": {"field": f"/exercise/items/{fid}", "quote": "w"},
        "claim": claim,
        "proposed_edit": {"field": f"/exercise/items/{fid}", "replacement": "z"} if edit else None,
        "receipts": receipts,
    }


def _assertion(aid: str, quote: str, finding: str | None, **fields: Any) -> dict[str, Any]:
    base = {
        "id": aid,
        "span": {"quote": quote, "occurrence": 0},
        "finding_id": finding,
        "facet": "form",
        "kind": "assertion",
        "slot_id": None,
        "duplicate_of": None,
        "verdict": "correct",
        "unchecked_reason": None,
        "false_correction": False,
        "protected_opportunity_id": None,
        "harm": False,
        "bindings": [],
    }
    return base | fields


def _bind(role: str, receipt_id: str, *, found: bool = True) -> dict[str, Any]:
    return {
        "role": role,
        "receipt_id": receipt_id,
        "polarity": "positive" if found else "negative",
        "evidence_excerpt": "Found: 1/1" if found else "Found: 0/1",
        "source_locator": "VESUM",
    }


def _label(item: dict[str, Any], family: str, *, required: int, expected: str = "findings", **extra: Any) -> dict:
    slots = [{"slot_id": f"s{i}", "facet": "form"} for i in range(1, required + 1)]
    return {
        "item_id": item["item_id"],
        "family": family,
        "judging_mode": item["judging_mode"],
        "answerable": True,
        "expected_outcome": expected,
        "O": 10,
        "required_slots": slots,
        "positive_slots": slots,
        "protected": [{"opportunity_id": "p1", "stratum": "heritage"}],
        "obligations": ["o1"],
    } | extra


def _reply(fx: Fixture, assertions: list[dict], *, protected=True, harm=False, satisfied=True, **extra) -> dict:
    return {
        "item_id": fx.item["item_id"],
        "output_id": "out-fixture",
        "response_kind": "answered",
        "outcome_correct": None if assertions else True,
        "assertions": assertions,
        "protected": [{"opportunity_id": "p1", "preserved": protected, "harm": harm}],
        "obligations": [{"id": "o1", "satisfied": satisfied}],
        "sources_calls": 3,
        "budget_exhausted": False,
        "evaluator_limits": [],
    } | extra


def _score(fx: Fixture, label: dict, output: str, reply: dict | None) -> dict[str, Any]:
    index = fx.index()
    sidecar = None
    if reply is not None:
        sidecar = judge.bind_reply(
            json.dumps(reply), item_id=fx.item["item_id"], output_id="out-fixture", output=output, index=index
        )
    return score_cell(fx.family, label=label, item=fx.item, output=output, sidecar=sidecar, index=index)


def _slot_review(fx: Fixture, slots: int, *, extra_true: int = 0, false_edit: bool = False, uncited: int = 0):
    """``slots`` correct slot findings, then ``extra_true`` true extras, then an optional false correction."""
    findings, assertions = [], []
    for i in range(1, slots + extra_true + 1):
        rid = fx.receipt("candidate", f"w{i}")
        cited = [] if i <= uncited else [rid]
        findings.append(_finding(f"F{i}", f"claim number {i:02d} holds", cited))
        slot = f"s{i}" if i <= slots else None
        bindings = [_bind("candidate", rid)] if cited else []
        assertions.append(_assertion(f"A{i}", f"claim number {i:02d} holds", f"F{i}", slot_id=slot, bindings=bindings))
    if false_edit:
        rid = fx.receipt("judge", "wx")
        findings.append(_finding("FX", "claim wx is a wrong form", [], edit=True))
        assertions.append(
            _assertion(
                "AX",
                "claim wx is a wrong form",
                "FX",
                kind="edit",
                verdict="incorrect",
                false_correction=True,
                bindings=[_bind("judge", rid)],
            )
        )
    return _envelope(fx.item, findings), assertions


def _case(name: str, expected: Any, observed: Any) -> dict[str, Any]:
    return {"case": name, "expected": expected, "observed": observed, "pass": expected == observed}


def _components(result: dict[str, Any]) -> tuple:
    c = result["components"]
    return (c["T"], round(c["C"], 6), round(c["P"], 6), c["F"], c["X"], c["H"], result["R"])


def worked_ordering(root: Path) -> list[dict[str, Any]]:
    cases = []
    manifest_rows = {row["case"]: row for row in load_manifest()["scoring"]["worked_ordering"]}
    for name, (t, c, p, f, x, h, r) in WORKED.items():
        row = manifest_rows[name]
        frozen = (row["T"], row["C"], row["P"], row["F"], row["X"], row["H"], row["R"])
        cases.append(_case(f"manifest worked row {name} matches the protocol table", (t, c, p, f, x, h, r), frozen))
        direct = Components(T=t, C=c, P=p, F=f, S=0, X=x, H=h, O=10)
        response = "refusal" if name == "refusal" else "accepted"
        cases.append(_case(f"reward formula {name}", r, reward(direct, status=COMPLETE, response=response)))

    fx = Fixture(root, "perfect")
    output, assertions = _slot_review(fx, 9)
    cases.append(
        _case(
            "scored perfect review",
            WORKED["perfect_or_clean"],
            _components(_score(fx, _label(fx.item, fx.family, required=9), output, _reply(fx, assertions))),
        )
    )

    fx = Fixture(root, "clean")
    output = _envelope(fx.item, [], "clean")
    result = _score(fx, _label(fx.item, fx.family, required=0, expected="clean"), output, _reply(fx, []))
    cases.append(_case("scored correct clean no-change", WORKED["perfect_or_clean"], _components(result)))

    fx = Fixture(root, "one-error")
    output, assertions = _slot_review(fx, 9, false_edit=True)
    cases.append(
        _case(
            "scored useful review with one false correction",
            WORKED["good_one_error"],
            _components(_score(fx, _label(fx.item, fx.family, required=9), output, _reply(fx, assertions))),
        )
    )

    fx = Fixture(root, "padder")
    output, assertions = _slot_review(fx, 1, extra_true=8)
    result = _score(fx, _label(fx.item, fx.family, required=1), output, _reply(fx, assertions))
    cases.append(
        _case(
            "scored padder within its size cap", (WORKED["padder"], COMPLETE), (_components(result), result["status"])
        )
    )

    fx = Fixture(root, "refusal")
    output = "I decline to review this exercise."
    reply = _reply(fx, [], protected=None, satisfied=None, response_kind="refusal", outcome_correct=False)
    cases.append(
        _case(
            "scored refusal on an answerable item",
            WORKED["refusal"],
            _components(_score(fx, _label(fx.item, fx.family, required=9), output, reply)),
        )
    )

    fx = Fixture(root, "accuser")
    findings, assertions = [], []
    for i in range(1, 11):
        rid = fx.receipt("judge", f"v{i}")
        claim = f"form v{i:02d} is wrong"
        findings.append(_finding(f"F{i}", claim, []))
        assertions.append(
            _assertion(
                f"A{i}",
                claim,
                f"F{i}",
                kind="accusation",
                verdict="incorrect",
                false_correction=True,
                protected_opportunity_id="p1" if i == 1 else None,
                harm=i == 1,
                bindings=[_bind("judge", rid)],
            )
        )
    reply = _reply(fx, assertions, protected=False, harm=True, satisfied=False)
    cases.append(
        _case(
            "scored accuse-everything with a protected harm",
            WORKED["accuse_everything"],
            _components(_score(fx, _label(fx.item, fx.family, required=9), _envelope(fx.item, findings), reply)),
        )
    )
    return cases


def branches(root: Path) -> list[dict[str, Any]]:
    cases = []
    fx = Fixture(root, "partial")
    output, assertions = _slot_review(fx, 5)
    result = _score(fx, _label(fx.item, fx.family, required=9), output, _reply(fx, assertions, satisfied=False))
    cases.append(
        _case(
            "partial answer is accepted but incomplete",
            (0, round(-0.5 + 0.5 * 5 / 9, 6), COMPLETE),
            (result["components"]["T"], result["R"], result["status"]),
        )
    )

    fx = Fixture(root, "empty")
    result = _score(fx, _label(fx.item, fx.family, required=9), "", None)
    cases.append(_case("empty output scores as missing", ("missing", -1.0), (result["response"], result["R"])))

    fx = Fixture(root, "gap", "card_review")
    rid = fx.receipt("candidate", "g1", found=False)
    gap = {
        "facet": "meaning",
        "location": {"field": "/card/sense", "quote": "g"},
        "reason": "no source decides",
        "receipts": [rid],
    }
    output = json.dumps(
        {
            "item_id": fx.item["item_id"],
            "judging_mode": "repair",
            "outcome": "evidence_gap",
            "findings": [],
            "gaps": [gap],
        }
    )
    result = _score(fx, _label(fx.item, fx.family, required=0, expected="evidence_gap"), output, _reply(fx, []))
    cases.append(
        _case(
            "zero-required-claim evidence gap scores 1",
            (1, 1.0, 1.0, 1.0, COMPLETE),
            (
                result["components"]["T"],
                result["components"]["C"],
                result["components"]["P"],
                result["R"],
                result["status"],
            ),
        )
    )

    fx = Fixture(root, "silent-gap", "card_review")
    output = json.dumps(
        {"item_id": fx.item["item_id"], "judging_mode": "repair", "outcome": "clean", "findings": [], "gaps": []}
    )
    reply = _reply(fx, [], outcome_correct=False)
    result = _score(fx, _label(fx.item, fx.family, required=0, expected="evidence_gap"), output, reply)
    cases.append(
        _case("a clean reply on a gap item earns no correctness", (0.0, 0.1), (result["components"]["C"], result["R"]))
    )

    fx = Fixture(root, "uncited")
    output, assertions = _slot_review(fx, 9, uncited=1)
    result = _score(fx, _label(fx.item, fx.family, required=9), output, _reply(fx, assertions))
    q = (8 / 9) * (8 / 9)
    cases.append(
        _case(
            "missing receipt earns its claim zero",
            (1, 8, round(0.1 + 0.9 * q, 6), COMPLETE),
            (result["counts"]["missing_receipts"], result["counts"]["credited_slots"], result["R"], result["status"]),
        )
    )

    fx = Fixture(root, "fabricated")
    output, assertions = _slot_review(fx, 9)
    output = output.replace(json.loads(output)["findings"][0]["receipts"][0], "rr-" + "f" * 20)
    result = _score(fx, _label(fx.item, fx.family, required=9), output, _reply(fx, assertions))
    cases.append(
        _case(
            "fabricated receipt invalidates the cell",
            (INVALID_FABRICATED_RECEIPT, -1.5, 1),
            (result["status"], result["R"], result["counts"]["fabricated_receipts"]),
        )
    )

    fx = Fixture(root, "judge-misbinds")
    output, assertions = _slot_review(fx, 3)
    assertions[0]["bindings"] = [_bind("candidate", "rr-" + "e" * 20)]
    assertions[1] |= {"harm": True, "protected_opportunity_id": "p1", "bindings": [_bind("judge", "rr-" + "d" * 20)]}
    result = _score(fx, _label(fx.item, fx.family, required=3), output, _reply(fx, assertions))
    cases.append(
        _case(
            "a judge binding no ledger holds is an evaluator error, and labelled harm still counts",
            (UNRESOLVED_EVALUATOR, -2.0, 0),
            (result["status"], result["R"], result["counts"]["fabricated_receipts"]),
        )
    )

    cases += _passage_cases(root)
    cases += _size_cases(root)
    return cases


def _passage_cases(root: Path) -> list[dict[str, Any]]:
    """The inherited ``uk-preamble-scoring/2`` counts inside a passage cell."""
    text = "aa bb cc dd ee"
    passage = {
        "id": "syn-passage",
        "text": text,
        "errors": [{"id": "e1", "start": 3, "end": 5, "span": "bb", "error_type": "spelling", "accepted": ["BB"]}],
        "protected": [{"id": "p1", "start": 9, "end": 11, "span": "dd", "kind": "heritage"}],
    }
    cases = []
    for name, corrected, expected in (
        ("seed repaired, everything else kept", "aa BB cc dd ee", (1, 1.0, 1.0, 0, 0, 0, 1.0)),
        ("seed repaired, one correct token changed", "aa BB CC dd ee", (1, 0.5, 1.0, 1, 0, 0, 0.505)),
    ):
        fx = Fixture(root, f"passage-{len(cases)}", "passage_review")
        fx.item |= {"passage": text}
        rid = fx.receipt("candidate", "bb")
        findings = [
            {
                "id": "F1",
                "facet": "spelling_style",
                "location": {"field": "/passage", "quote": "bb"},
                "claim": "claim bb is misspelt",
                "proposed_edit": {"field": "/passage", "replacement": "BB"},
                "receipts": [rid],
            }
        ]
        assertions = [
            _assertion(
                "A1",
                "claim bb is misspelt",
                "F1",
                facet="form",
                kind="edit",
                slot_id="e1",
                bindings=[_bind("candidate", rid)],
            )
        ]
        if "CC" in corrected:
            jid = fx.receipt("judge", "cc")
            assertions.append(
                _assertion(
                    "A2",
                    "aa BB CC",
                    None,
                    kind="edit",
                    verdict="incorrect",
                    false_correction=True,
                    bindings=[_bind("judge", jid)],
                )
            )
        output = json.dumps(
            {
                "item_id": fx.item["item_id"],
                "judging_mode": "repair",
                "outcome": "findings",
                "corrected_text": corrected,
                "findings": findings,
                "gaps": [],
            }
        )
        label = _label(fx.item, fx.family, required=0) | {
            "required_slots": [{"slot_id": "e1", "facet": "form"}],
            "positive_slots": [{"slot_id": "e1", "facet": "form"}],
            "passage": passage,
        }
        result = _score(fx, label, output, _reply(fx, assertions))
        cases.append(_case(f"passage: {name}", expected, _components(result)))
    return cases


def _size_cases(root: Path) -> list[dict[str, Any]]:
    cases = []
    cap = FAMILIES["card_review"].cap
    fx = Fixture(root, "bytes", "card_review")
    rid = fx.receipt("candidate", "b1")
    finding = {
        "id": "F1",
        "facet": "form",
        "location": {"field": "/card/form", "quote": "b"},
        "claim": "claim b1 holds " + "x" * cap.max_bytes,
        "proposed_edit": None,
        "receipts": [rid],
    }
    output = json.dumps(
        {
            "item_id": fx.item["item_id"],
            "judging_mode": "repair",
            "outcome": "findings",
            "findings": [finding],
            "gaps": [],
        }
    )
    reply = _reply(fx, [_assertion("A1", "claim b1 holds", "F1", slot_id="s1", bindings=[_bind("candidate", rid)])])
    result = _score(fx, _label(fx.item, fx.family, required=1), output, reply)
    cases.append(
        _case(
            "output over its byte cap is overproduction",
            (INVALID_OVERPRODUCTION, -1.5),
            (result["status"], result["R"]),
        )
    )

    fx = Fixture(root, "claims", "card_review")
    findings, assertions = [], []
    for i in range(1, cap.max_claims + 2):
        rid = fx.receipt("candidate", f"c{i}")
        findings.append(
            {
                "id": f"F{i}",
                "facet": "form",
                "location": {"field": "/card", "quote": "c"},
                "claim": f"claim c{i:02d} holds",
                "proposed_edit": None,
                "receipts": [rid],
            }
        )
        assertions.append(
            _assertion(
                f"A{i}",
                f"claim c{i:02d} holds",
                f"F{i}",
                slot_id="s1" if i == 1 else None,
                bindings=[_bind("candidate", rid)],
            )
        )
    output = json.dumps(
        {
            "item_id": fx.item["item_id"],
            "judging_mode": "repair",
            "outcome": "findings",
            "findings": findings,
            "gaps": [],
        }
    )
    result = _score(fx, _label(fx.item, fx.family, required=1), output, _reply(fx, assertions))
    cases.append(
        _case(
            "claims over the cap are overproduction, not evaluator failure",
            (INVALID_OVERPRODUCTION, -1.5),
            (result["status"], result["R"]),
        )
    )

    fx = Fixture(root, "padding-exhausts")
    output, assertions = _slot_review(fx, 1, extra_true=3)
    assertions[-1] |= {"verdict": "unchecked", "unchecked_reason": "budget"}
    reply = _reply(fx, assertions, sources_calls=32, budget_exhausted=True)
    result = _score(fx, _label(fx.item, fx.family, required=1), output, reply)
    cases.append(
        _case(
            "off-contract padding that exhausts the judge is overproduction",
            (INVALID_OVERPRODUCTION, -1.5),
            (result["status"], result["R"]),
        )
    )

    fx = Fixture(root, "judge-exhausts")
    output, assertions = _slot_review(fx, 3)
    assertions[-1] |= {"verdict": "unchecked", "unchecked_reason": "budget"}
    reply = _reply(fx, assertions, sources_calls=32, budget_exhausted=True)
    result = _score(fx, _label(fx.item, fx.family, required=3), output, reply)
    cases.append(
        _case(
            "in-contract judge exhaustion is an evaluator failure",
            (UNRESOLVED_EVALUATOR, True),
            (result["status"], result["provisional"]),
        )
    )

    fx = Fixture(root, "harm-unresolved")
    output, assertions = _slot_review(fx, 3)
    assertions[-1] |= {"verdict": "unchecked", "unchecked_reason": "tool_unavailable"}
    reply = _reply(fx, assertions, protected=False, harm=True)
    result = _score(fx, _label(fx.item, fx.family, required=3), output, reply)
    cases.append(
        _case(
            "verified harm scores -2 even in an unresolved cell",
            (UNRESOLVED_EVALUATOR, -2.0, True),
            (result["status"], result["R"], result["safety_failed"]),
        )
    )
    return cases


def _max_output(family: str) -> str:
    """Placeholder text at the family's byte cap and within its token cap."""
    cap = FAMILIES[family].cap
    word = "x" * (cap.max_bytes // cap.max_tokens + 1)
    count = (cap.max_bytes + 1) // (len(word) + 1)
    return " ".join([word] * count).ljust(cap.max_bytes, "x")


def max_size_coverage() -> list[dict[str, Any]]:
    cases = []
    for family, contract in FAMILIES.items():
        cap = contract.cap
        text = _max_output(family)
        individual = [coverage.Claim(f"i{n}", "spelling_style") for n in range(cap.max_claims)]
        batched = [coverage.Claim(f"b{n}", "form" if n % 2 else "meaning") for n in range(cap.batched)]
        plan = coverage.plan_calls(family, individual + batched)
        at_cap = adapters.size_problems(
            family, text, individual=cap.max_claims, batched=cap.batched, edits=cap.max_edits
        )
        over = adapters.size_problems(
            family, text + "x", individual=cap.max_claims + 1, batched=cap.batched + 1, edits=cap.max_edits + 1
        )
        cases.append(
            _case(
                f"{family}: maximum-size output with every claim off-label fits 32 calls",
                (True, [], plan.total),
                (plan.fits, at_cap, coverage.worst_case_calls(family)),
            )
        )
        cases.append(_case(f"{family}: one byte, claim or edit beyond the cap is caught", 4, len(over)))
    return cases


def boundaries(root: Path) -> list[dict[str, Any]]:
    cases = []
    for family in FAMILIES:
        expected = family not in ("fresh_lesson", "fresh_activities")
        cases.append(
            _case(
                f"{family}: Sources tools only where the production contract allows",
                expected,
                adapters.tool_policy(family)["sources"],
            )
        )
    seen: dict[str, Any] = {}

    def renderer(plan_entry, cited_records, learner_state, immersion, **options):
        seen.update(args=(plan_entry, cited_records, learner_state, immersion), options=options)
        return "production prompt"

    item = {
        "item_id": "syn-fresh",
        "judging_mode": "authoring",
        "level": "A1",
        "slug": "s",
        "lesson_n": 1,
        "inputs": {"plan_entry": {"p": 1}, "cited_records": {}, "learner_state": {}, "immersion": {}},
    }
    rendered = adapters.render_fresh("fresh_lesson", item, renderer)
    cases.append(
        _case(
            "fresh writer gets exactly the production prompt over four inputs, no mode field",
            ("production prompt", ["lesson_n", "level", "slug"]),
            (rendered, sorted(seen["options"])),
        )
    )
    cases.append(
        _case(
            "fresh writer refuses a fifth input",
            True,
            _refused(
                lambda: adapters.render_fresh(
                    "fresh_lesson", item | {"inputs": item["inputs"] | {"search": 1}}, renderer
                )
            ),
        )
    )

    fx = Fixture(root, "fresh-tools", "fresh_lesson")
    fx.item = item
    fx.receipt("candidate", "t1")
    label = _label(item, "fresh_lesson", required=0, expected="clean")
    result = score_cell(
        "fresh_lesson",
        label=label,
        item=item,
        output="draft",
        sidecar=None,
        index=fx.index(),
        validate_draft=lambda text, level: {"draft": text},
    )
    cases.append(_case("a fresh writer that reached Sources is not scorable", UNRESOLVED_EVALUATOR, result["status"]))

    review = {"item_id": "syn-card", "judging_mode": "repair", "level": "A1", "card": {}, "context": "c"}
    for leak in ("labels", "accepted_answers", "protected", "expected_outcome"):
        cases.append(
            _case(
                f"held-out isolation: a request carrying {leak} is refused",
                True,
                _refused(lambda leak=leak: adapters.render_review("card_review", review | {leak: []}, b"prompt")),
            )
        )
    cases.append(
        _case(
            "held-out isolation: an unpinned prompt is refused",
            True,
            _refused(lambda: adapters.pinned_bytes(b"prompt", None, "card prompt")),
        )
    )
    cases.append(
        _case(
            "blind judging: a label naming the candidate is refused",
            True,
            _refused(lambda: judge._blind({"model": "x"})),
        )
    )
    return cases


def _refused(action: Callable[[], Any]) -> bool:
    try:
        action()
    except (adapters.AdapterError, judge.JudgeError):
        return True
    return False


def run() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="uk-behaviour-proof-", dir=ensure_scratch_root()) as tmp:
        root = Path(tmp)
        cases = worked_ordering(root) + branches(root) + max_size_coverage() + boundaries(root)
    return {"proof": PROOF, "cases": cases, "pass": all(case["pass"] for case in cases)}
