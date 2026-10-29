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
from scripts.eval.uk_preamble.common import tokenize
from scripts.review.receipts import ledger

from . import adapters, coverage, judge
from .binding import LedgerIndex, LedgerRef
from .contract import (
    COMPLETE,
    EXERCISE_REQUEST_DEFECTS,
    FAMILIES,
    INVALID_FABRICATED_RECEIPT,
    INVALID_OVERPRODUCTION,
    PEDAGOGY_ANCHORS,
    PEDAGOGY_DEFECTS,
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
            items = [{"stem": f"stem w{n}", "options": ["a", "b", "c"], "key": "a"} for n in range(1, 21)]
            self.item |= {"exercise": {"items": items}, "target": "synthetic", "learner_state": {}}
        elif family == "card_review":
            self.item |= {"card": {}, "context": "synthetic"}
        self.refs: list[LedgerRef] = []
        self.paths: dict[str, Path] = {}
        for role in ("candidate", "judge", "pack"):
            path = root / f"rv-{name}" / f"{role}.jsonl"
            ledger.create_empty_ledger(path)
            self.paths[role] = path
            self.refs.append(LedgerRef(role, path, f"rv-{name}", role, MANIFEST_SHA))

    def receipt(self, role: str, word: str, *, found: bool = True) -> str:
        result = f"Source: VESUM\nFound: {1 if found else 0}/1\n- **{word}** — {'FOUND' if found else 'NOT FOUND'}"
        return self.call(role, "verify_words", {"words": [word]}, result)

    def call(self, role: str, tool: str, arguments: dict[str, Any], result: str) -> str:
        """Append one synthetic Sources call to the role's verified ledger."""
        return ledger.append(
            self.paths[role],
            review_id=self.paths[role].parent.name,
            attempt_id=role,
            manifest_sha256=MANIFEST_SHA,
            tool=tool,
            server_version="fixture",
            arguments=arguments,
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


def _finding(fid: str, n: int, claim: str, receipts: list[str], *, defect: str = "form", edit: bool = False) -> dict:
    """An exercise finding located at item ``n``'s stem, quoting it exactly."""
    field = f"/exercise/items/{n - 1}/stem"
    return {
        "id": fid,
        "defect": defect,
        "location": {"field": field, "quote": f"w{n}"},
        "claim": claim,
        "proposed_edit": {"field": field, "replacement": "z"} if edit else None,
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


def _label(
    item: dict[str, Any], family: str, *, required: int, expected: str = "findings", facet: str = "form", **extra: Any
) -> dict:
    slots = [{"slot_id": f"s{i}", "facet": facet} for i in range(1, required + 1)]
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
        "sources_calls": None,  # filled from the judge's ledger by _score unless a case sets it
        "budget_exhausted": False,
        "evaluator_limits": [],
    } | extra


def _score(fx: Fixture, label: dict, output: str, reply: dict | None) -> dict[str, Any]:
    index = fx.index()
    sidecar = None
    if reply is not None and reply["sources_calls"] is None:
        reply = reply | {"sources_calls": index.counts["judge"]}
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
        findings.append(_finding(f"F{i}", i, f"claim number {i:02d} holds", cited))
        slot = f"s{i}" if i <= slots else None
        bindings = [_bind("candidate", rid)] if cited else []
        assertions.append(_assertion(f"A{i}", f"claim number {i:02d} holds", f"F{i}", slot_id=slot, bindings=bindings))
    if false_edit:
        rid = fx.receipt("judge", "wx")
        findings.append(_finding("FX", 20, "claim wx is a wrong form", [], edit=True))
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
        findings.append(_finding(f"F{i}", i, claim, []))
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

    fx = Fixture(root, "unsettled-extra")
    output, assertions = _slot_review(fx, 0, extra_true=1)
    assertions[0]["bindings"] = [_bind("judge", "rr-" + "c" * 20)]
    result = _score(fx, _label(fx.item, fx.family, required=1), output, _reply(fx, assertions))
    cases.append(
        _case(
            "an assertion the evaluator cannot settle keeps zero provisional credit",
            (UNRESOLVED_EVALUATOR, 0.0, True),
            (result["status"], result["components"]["C"], result["provisional"]),
        )
    )

    cases += _passage_cases(root)
    cases += _evidence_cases(root)
    cases += _size_cases(root)
    return cases


def _one_finding_cell(fx: Fixture, finding: dict[str, Any], quote: str, facet: str) -> dict[str, Any]:
    output = _envelope(fx.item, [finding])
    assertion = _assertion("A1", quote, finding["id"], facet=facet, slot_id="s1")
    return _score(fx, _label(fx.item, fx.family, required=1, facet=facet), output, _reply(fx, [assertion]))


def _evidence_cases(root: Path) -> list[dict[str, Any]]:
    """Findings whose evidence is the request itself: exercise mechanics and pedagogy anchors."""
    cases = []
    keys = ["a", "a", "a", "a", "a", "b"]  # key positions 0,0,0,0,0,1 meet the 80% rule
    block = {"items": [{"stem": f"s{n}", "options": ["a", "b", "c"], "key": key} for n, key in enumerate(keys)]}
    for name, positions, expected in (
        ("answer-position finding with derived key positions earns credit", [0, 0, 0, 0, 0, 1], 1.0),
        ("answer-position finding with wrong key positions earns nothing", [0, 0, 0, 0, 0, 0], 0.1),
    ):
        fx = Fixture(root, f"position-{expected}", "exercise_review")
        fx.item["exercise"] = block
        finding = {
            "id": "F1",
            "defect": "answer_position_pattern",
            "location": {"field": "/exercise", "quote": "s0"},
            "claim": "the key sits first in five of six items",
            "proposed_edit": None,
            "receipts": [],
            "key_positions": positions,
        }
        result = _one_finding_cell(fx, finding, "the key sits first in five of six items", "exercise")
        cases.append(_case(name, expected, result["R"]))
    for name, quote, expected in (
        ("request-only leakage finding quoting the request earns credit", "w3", 1.0),
        ("leakage finding misquoting the request earns nothing", "w99", 0.1),
    ):
        fx = Fixture(root, f"leak-{expected}", "exercise_review")
        finding = _finding("F1", 3, "the gloss gives the answer away", [], defect="giveaway_gloss")
        finding["location"]["quote"] = quote
        result = _one_finding_cell(fx, finding, "the gloss gives the answer away", "exercise")
        cases.append(_case(name, expected, result["R"]))

    norm = [
        {"id": "std-listening", "kind": "standard_lines", "locator": "lines 233-277", "text": "listening line"},
        {"id": "ohoiko-4", "kind": "ohoiko_practice", "locator": "practice 4", "text": "dialogue before breakdown"},
        {"id": "video-1", "kind": "video_resource", "locator": "resource 1", "text": "verified whole video"},
        {"id": "decision", "kind": "video_decision", "locator": "issue comment", "text": "shown whole with sound"},
    ]
    anchors = [
        {"kind": "standard_lines", "evidence": "std-listening", "receipt": None, "quote": "listening line"},
        {"kind": "ohoiko_practice", "evidence": "ohoiko-4", "receipt": None, "quote": "dialogue before"},
        {"kind": "video_resource", "evidence": "video-1", "receipt": None, "quote": "whole video"},
        {"kind": "video_decision", "evidence": "decision", "receipt": None, "quote": "sound"},
    ]
    for name, used, expected in (
        ("pedagogy finding with every required anchor earns credit", anchors, 1.0),
        ("pedagogy finding missing the video decision anchor earns nothing", anchors[:3], 0.1),
    ):
        fx = Fixture(root, f"pedagogy-{len(used)}", "pedagogy_review")
        fx.item = {
            "item_id": "syn-pedagogy",
            "judging_mode": "authoring",
            "level": "A1",
            "shape": "plan",
            "snippet": {"plan": "listening step without the video"},
            "target": "listening",
            "learner_state": {},
            "prerequisites": [],
            "resources": [],
            "norm_evidence": norm,
        }
        finding = {
            "id": "F1",
            "defect": "missing_planned_video",
            "norm": "ohoiko_method",
            "anchors": used,
            "location": {"field": "/snippet/plan", "quote": "without the video"},
            "claim": "the plan ignores the suitable video",
            "proposed_edit": None,
            "receipts": [],
        }
        result = _one_finding_cell(fx, finding, "the plan ignores the suitable video", "pedagogy")
        cases.append(_case(name, expected, result["R"]))

    # The advisor's round-2 probes: anchors must take the one source their kind permits.
    learner = {"steps": "knows no letters yet"}
    textbook = [{"kind": "textbook_page", "evidence": None, "receipt": None, "quote": "x"}]
    for name, anchors_used, receipt_tool, expected in (
        (
            "learner-state text labelled as a textbook page earns nothing",
            [{"kind": "textbook_page", "evidence": "/learner_state/steps", "receipt": None, "quote": "no letters"}],
            None,
            0.1,
        ),
        ("a textbook-page anchor needs a search_text receipt with hits", textbook, "verify_words", 0.1),
        ("a textbook-page anchor with its search_text receipt earns credit", textbook, "search_text", 1.0),
    ):
        fx = Fixture(root, f"textbook-{len(cases)}", "pedagogy_review")
        fx.item = {
            "item_id": "syn-pedagogy-t",
            "judging_mode": "authoring",
            "level": "A1",
            "shape": "lesson",
            "snippet": {"lesson": "letters before sounds"},
            "target": "decoding",
            "learner_state": learner,
            "prerequisites": [],
            "resources": [],
            "norm_evidence": [],
        }
        receipts = []
        used = [dict(anchor) for anchor in anchors_used]
        if receipt_tool:
            rid = ledger.append(
                fx.paths["candidate"],
                review_id=fx.paths["candidate"].parent.name,
                attempt_id="candidate",
                manifest_sha256=MANIFEST_SHA,
                tool=receipt_tool,
                server_version="fixture",
                arguments={"query": "p"},
                snapshots={},
                status="ok",
                result="Found 1 results for: p\nprinted page 13: sounds before letters",
            )
            receipts = [rid]
            used[0] |= {"receipt": rid, "quote": "sounds before letters"}
        finding = {
            "id": "F1",
            "defect": "textbook_sequencing",
            "norm": "ukrainian_school_textbooks",
            "anchors": used,
            "location": {"field": "/snippet/lesson", "quote": "letters before sounds"},
            "claim": "letters come before their sounds",
            "proposed_edit": None,
            "receipts": receipts,
        }
        result = _one_finding_cell(fx, finding, "letters come before their sounds", "pedagogy")
        cases.append(_case(name, expected, result["R"]))

    fx = Fixture(root, "relabel", "pedagogy_review")
    fx.item = {
        "item_id": "syn-pedagogy-r",
        "judging_mode": "repair",
        "level": "A1",
        "shape": "plan",
        "snippet": {"plan": "case system in week one"},
        "target": "cases",
        "learner_state": learner,
        "prerequisites": [],
        "resources": [],
        "norm_evidence": [{"id": "std", "kind": "standard_lines", "locator": "l", "text": "case lines"}],
    }
    finding = {
        "id": "F1",
        "defect": "standard_coverage_or_sequencing",
        "norm": "state_standard_2024",
        "anchors": [
            {"kind": "standard_lines", "evidence": "std", "receipt": None, "quote": "case lines"},
            {"kind": "coverage_map", "evidence": "/learner_state/steps", "receipt": None, "quote": "no letters"},
        ],
        "location": {"field": "/snippet/plan", "quote": "case system"},
        "claim": "the plan defers promised coverage",
        "proposed_edit": None,
        "receipts": [],
    }
    result = _one_finding_cell(fx, finding, "the plan defers promised coverage", "pedagogy")
    cases.append(_case("learner-state text relabelled as the coverage map earns nothing", 0.1, result["R"]))

    for name, tool, polarity, expected in (
        (
            "an exercise stress finding on a verify_stress receipt earns nothing, whatever the judge's facet",
            "verify_stress",
            "positive",
            0.1,
        ),
        ("an exercise stress finding on a verify_stress miss earns nothing", "verify_stress", "negative", 0.1),
        ("an exercise stress finding on a СУМ-20 record earns credit", "query_sum20", "positive", 1.0),
    ):
        fx = Fixture(root, f"stress-{tool}-{polarity}", "exercise_review")
        if tool == "verify_stress":  # its receipt keeps one summary line, never the reading's source
            line = "w5 — ok: w5x" if polarity == "positive" else "w5 — not_found"
            result, excerpt, locator = line, line, "w5"
        else:
            result = _sum20("w5")
            excerpt, locator = "**w5x** (noun)", "https://sum20.example/w5"
        rid = fx.call("candidate", tool, {"word": "w5"}, result)
        finding = _finding("F1", 5, "the stress of w5 is wrong", [rid], defect="stress")
        binding = {
            "role": "candidate",
            "receipt_id": rid,
            "polarity": polarity,
            "evidence_excerpt": excerpt,
            "source_locator": locator,
        }
        assertion = _assertion(
            "A1", "the stress of w5 is wrong", "F1", facet="exercise", slot_id="s1", bindings=[binding]
        )
        label = _label(fx.item, fx.family, required=1, facet="stress")
        result = _score(fx, label, _envelope(fx.item, [finding]), _reply(fx, [assertion]))
        cases.append(_case(name, expected, result["R"]))
    return cases


def _sum20(word: str) -> str:
    """A synthetic ``query_sum20`` result: a header and one record (two evidence units)."""
    return (
        f"**Official СУМ-20 entries for '{word}'**\n\n**{word}x** (noun)\n**Source**: СУМ-20\n"
        f"**URL**: https://sum20.example/{word}\n1. sense of {word}"
    )


def review_probes(root: Path) -> list[dict[str, Any]]:
    """The independent review's round-1 probes: judge fields, integrity and provenance."""
    cases = []
    fx = Fixture(root, "probe-harm-slot")
    output, assertions = _slot_review(fx, 1)
    rid = fx.receipt("judge", "w1")
    assertions[0] |= {
        "slot_id": "s99",
        "harm": True,
        "protected_opportunity_id": "p1",
        "bindings": [_bind("judge", rid)],
    }
    result = _score(fx, _label(fx.item, fx.family, required=1), output, _reply(fx, assertions))
    cases.append(
        _case(
            "labelled harm counts even when the judge names an unknown slot",
            (1, -2.0),
            (result["components"]["H"], result["R"]),
        )
    )

    fx = Fixture(root, "probe-slot-facet")
    finding = _finding("F1", 3, "the gloss gives the answer away", [], defect="giveaway_gloss")
    result = _one_finding_cell(fx, finding, "the gloss gives the answer away", "stress")
    cases.append(
        _case(
            "a request-only finding cannot take a stress slot",
            (0, 0.1),
            (result["counts"]["credited_slots"], result["R"]),
        )
    )

    fx = Fixture(root, "probe-omitted", "card_review")
    rid = fx.receipt("candidate", "c1")
    finding = {
        "id": "F1",
        "facet": "form",
        "location": {"field": "/card", "quote": "c"},
        "claim": "claim c1 is wrong",
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
    reply = _reply(fx, [], outcome_correct=True)
    result = _score(fx, _label(fx.item, fx.family, required=0, expected="clean"), output, reply)
    cases.append(
        _case(
            "a finding the judge omits keeps zero credit on a clean control",
            (0.0, UNRESOLVED_EVALUATOR),
            (result["components"]["C"], result["status"]),
        )
    )

    fx = Fixture(root, "probe-two-bindings")
    output, assertions = _slot_review(fx, 1, false_edit=True)
    assertions[-1]["bindings"].append(_bind("judge", "rr-" + "b" * 20))
    result = _score(fx, _label(fx.item, fx.family, required=1), output, _reply(fx, assertions))
    cases.append(_case("one broken binding does not erase a verified false correction", 1, result["components"]["F"]))

    # A judge naming an unknown slot, a slot of another facet or an unlabelled protected
    # opportunity loses that assertion's credit, not its verified false correction.
    fx = Fixture(root, "probe-misnamed-false-edits")
    output, assertions = _slot_review(fx, 1)
    findings = json.loads(output)["findings"]
    for n, misnamed in ((18, {"slot_id": "s99"}), (19, {"slot_id": "s2"}), (20, {"protected_opportunity_id": "p9"})):
        claim = f"claim w{n} is a wrong form"
        findings.append(_finding(f"FX{n}", n, claim, [], edit=True))
        binding = _bind("judge", fx.receipt("judge", f"wx{n}"))
        fields = {"kind": "edit", "verdict": "incorrect", "false_correction": True, "bindings": [binding]}
        assertions.append(_assertion(f"AX{n}", claim, f"FX{n}", **fields, **misnamed))
    slots = [{"slot_id": "s1", "facet": "form"}, {"slot_id": "s2", "facet": "stress"}]
    label = _label(fx.item, fx.family, required=1, positive_slots=slots)
    result = _score(fx, label, _envelope(fx.item, findings), _reply(fx, assertions))
    cases.append(
        _case(
            "a misnamed slot, facet or protected id does not erase a verified false correction",
            (3, UNRESOLVED_EVALUATOR),
            (result["components"]["F"], result["status"]),
        )
    )

    cap = FAMILIES["card_review"].cap.max_bytes
    for name, output in (("malformed", "x" * (cap + 1)), ("blank", " " * (cap + 1))):
        fx = Fixture(root, f"probe-oversize-{name}", "card_review")
        result = _score(fx, _label(fx.item, fx.family, required=1), output, None)
        cases.append(
            _case(
                f"an oversized {name} output is overproduction",
                (INVALID_OVERPRODUCTION, -1.5),
                (result["status"], result["R"]),
            )
        )

    fx = Fixture(root, "probe-wrong-item", "card_review")
    output = json.dumps(
        {
            "item_id": "another",
            "judging_mode": "repair",
            "outcome": "findings",
            "findings": [{"id": "F1", "receipts": ["rr-" + "a" * 20]}],
            "gaps": [],
        }
    )
    result = _score(fx, _label(fx.item, fx.family, required=1), output, None)
    cases.append(
        _case(
            "a malformed envelope citing an absent receipt is fabrication",
            (INVALID_FABRICATED_RECEIPT, -1.5, 1),
            (result["status"], result["R"], result["counts"]["fabricated_receipts"]),
        )
    )

    fx = Fixture(root, "probe-escaped-receipt", "card_review")
    finding = {
        "id": "F1",
        "facet": "form",
        "location": {"field": "/card", "quote": "c"},
        "claim": "claim c1 is wrong",
        "proposed_edit": None,
        "receipts": ["rr-" + "a" * 20],
    }
    observed = []
    for item_id in (fx.item["item_id"], "another"):  # accepted, then malformed
        envelope = {"item_id": item_id, "judging_mode": "repair", "outcome": "findings", "findings": [finding]}
        output = json.dumps(envelope | {"gaps": []}).replace('"rr-', '"\\u0072r-')
        result = _score(fx, _label(fx.item, fx.family, required=1), output, None)
        observed.append((result["response"], result["status"], result["counts"]["fabricated_receipts"]))
    # A repeated key keeps only its last value when parsed, so the escaped id sits in the first copy.
    output = output.replace('"another"', json.dumps(fx.item["item_id"])).replace('"]}]', '"], "receipts": []}]')
    result = _score(fx, _label(fx.item, fx.family, required=1), output, None)
    observed.append((result["response"], result["status"], result["counts"]["fabricated_receipts"]))
    deep = Fixture(root, "probe-deep-receipt", "v7_module")
    output = "[" * 1200 + '"\\u0072r-' + "a" * 20 + '"' + "]" * 1200  # within the caps, past the recursion limit
    result = _score(deep, _label(deep.item, deep.family, required=1), output, None)
    observed.append((result["response"], result["status"], result["counts"]["fabricated_receipts"]))
    cases.append(
        _case(
            "a receipt id cited in JSON escapes is authenticated, accepted or not",
            [
                ("accepted", INVALID_FABRICATED_RECEIPT, 1),
                ("malformed", INVALID_FABRICATED_RECEIPT, 1),
                ("accepted", INVALID_FABRICATED_RECEIPT, 1),
                ("accepted", INVALID_FABRICATED_RECEIPT, 1),
            ],
            observed,
        )
    )

    mixed = (
        'Found 2 slovnyk.me result(s) for: "m1"\n\n### Result 1\n- **Headword**: m1\n'
        "- **Dictionary**: ВТС\n- **URL**: https://slovnyk.example/vts/m1\n- **Snippet**: modern sense\n\n"
        "### Result 2\n- **Headword**: m1\n- **Dictionary**: СУМ-11\n"
        "- **URL**: https://slovnyk.example/sum/m1\n- **Snippet**: soviet sense\n"
    )
    for name, dictionary, locator, expected in (
        (
            "a СУМ-11 entry relabelled as ВТС in a mixed result earns nothing",
            "ВТС",
            "https://slovnyk.example/sum/m1",
            (0.1, 0),
        ),
        ("a СУМ-11 entry in a mixed result counts in S", "СУМ-11", "https://slovnyk.example/sum/m1", (0.1, 1)),
        ("an invented locator binds nothing", "ВТС", "invented locator", (0.1, 0)),
        ("the ВТС entry of a mixed result earns credit", "ВТС", "https://slovnyk.example/vts/m1", (1.0, 0)),
    ):
        fx = Fixture(root, f"probe-slovnyk-{len(cases)}", "card_review")
        rid = fx.call("candidate", "search_slovnyk_me", {"query": "m1"}, mixed)
        excerpt = "soviet sense" if "sum" in locator else "modern sense"
        finding = {
            "id": "F1",
            "facet": "meaning",
            "location": {"field": "/card", "quote": "m"},
            "claim": "the sense of m1 is wrong",
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
        binding = {
            "role": "candidate",
            "receipt_id": rid,
            "polarity": "positive",
            "evidence_excerpt": excerpt,
            "source_locator": locator,
            "underlying_dictionary": dictionary,
        }
        assertion = _assertion(
            "A1", "the sense of m1 is wrong", "F1", facet="meaning", slot_id="s1", bindings=[binding]
        )
        label = _label(fx.item, fx.family, required=1, facet="meaning")
        result = _score(fx, label, output, _reply(fx, [assertion]))
        cases.append(_case(name, expected, (result["R"], result["components"]["S"])))

    fx = Fixture(root, "probe-judge-calls")
    output, assertions = _slot_review(fx, 1)
    result = _score(fx, _label(fx.item, fx.family, required=1), output, _reply(fx, assertions, sources_calls=5))
    cases.append(
        _case("judge-reported calls must equal the judge's own ledger", UNRESOLVED_EVALUATOR, result["status"])
    )

    nested = {
        "item_id": "c",
        "judging_mode": "repair",
        "level": "A1",
        "card": {"labels": {"protected": []}},
        "context": "c",
    }
    cases.append(
        _case(
            "label metadata nested inside an allowlisted field is refused",
            True,
            _refused(lambda: adapters.render_review("card_review", nested, b"prompt")),
        )
    )
    inputs = {key: {"x": {"content_sha256": "0" * 64}} for key in adapters.WORD_CARD_INPUTS}
    cases.append(
        _case(
            "a nested answerable or O is refused, but a word card's build inputs are kept",
            (True, True, False),
            tuple(
                _refused(lambda card=card: adapters.render_review("card_review", nested | {"card": card}, b"prompt"))
                for card in ({"answerable": False}, {"x": [{"O": 10}]}, {"build": {"inputs": inputs}})
            ),
        )
    )
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
                "facet": "form",
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


FRESH_FIXTURE = "tests/build/fixtures/fresh/lesson-draft-a1-valid.yaml"
PAD = "Read each line aloud once more."


def _vesum_batch(words: list[str]) -> str:
    lines = "\n".join(f"- **{word}** — FOUND" for word in words)
    return f"Source: VESUM\nFound: {len(words)}/{len(words)}\n{lines}"


def _textbook(n: int) -> str:
    return (
        f'Found 1 results for: "q{n}"\n\n### Result 1\n- **Chunk ID**: `chunk-{n:02d}`\n'
        f"- **Text**:\nsentence {n:02d} of the page"
    )


def _bound(fx: Fixture, role: str, rid: str, excerpt: str, locator: str) -> dict[str, Any]:
    return {
        "role": role,
        "receipt_id": rid,
        "polarity": "positive",
        "evidence_excerpt": excerpt,
        "source_locator": locator,
    }


def _pad(text: str, family: str, filler: str) -> str:
    """``text`` grown with ``filler`` close to whichever of the family's caps binds first."""
    cap = FAMILIES[family].cap
    by_bytes = (cap.max_bytes - 512 - len(text.encode("utf-8"))) // len(filler.encode("utf-8"))
    by_tokens = (cap.max_tokens - 256 - len(tokenize(text))) // len(tokenize(filler))
    return text + filler * max(0, min(by_bytes, by_tokens))


def _writer_claims(fx: Fixture, batched_role: str, words: list[str], claims: list[str]):
    """Batched form claims on shared verify_words receipts, and one search_text receipt per claim."""
    slots, assertions = [], []
    for start in range(0, len(words), 200):
        chunk = words[start : start + 200]
        rid = fx.call(batched_role, "verify_words", {"words": chunk}, _vesum_batch(chunk))
        for word in chunk:
            slots.append({"slot_id": f"b-{word}", "facet": "form"})
            assertions.append(
                _assertion(
                    f"A-{word}",
                    word,
                    None,
                    slot_id=f"b-{word}",
                    bindings=[_bound(fx, batched_role, rid, f"- **{word}** — FOUND", "VESUM")],
                )
            )
    for n, claim in enumerate(claims, 1):
        rid = fx.call("judge", "search_text", {"query": f"q{n}"}, _textbook(n))
        slots.append({"slot_id": f"i{n}", "facet": "naturalness"})
        assertions.append(
            _assertion(
                f"I{n}",
                claim,
                None,
                facet="naturalness",
                slot_id=f"i{n}",
                bindings=[_bound(fx, "judge", rid, f"sentence {n:02d} of the page", f"chunk-{n:02d}")],
            )
        )
    return slots, assertions


def _max_fresh(root: Path, family: str) -> tuple[Fixture, str, list, list, Any]:
    import yaml

    from scripts.build.fresh.writer import parse_and_validate_reply

    from .contract import REPO_ROOT

    cap = FAMILIES[family].cap
    fx = Fixture(root, f"max-{family}", family)
    fx.item = {
        "item_id": f"syn-max-{family}",
        "judging_mode": "authoring",
        "level": "A1",
        "slug": "s",
        "lesson_n": 1,
        "inputs": {"plan_entry": {}, "cited_records": {}, "learner_state": {}, "immersion": {}},
    }
    draft = yaml.safe_load((REPO_ROOT / FRESH_FIXTURE).read_text(encoding="utf-8"))
    words = [f"w{n:03d}{side}" for n in range(1, cap.batched // 2 + 1) for side in "ab"]
    claims = [f"Line {n:02d} is read twice." for n in range(1, cap.max_claims + 1)]
    blocks = draft["steps"][0]["blocks"]
    blocks.append({"kind": "table", "rows": [words[i : i + 2] for i in range(0, len(words), 2)], "explains": ["T-003"]})
    blocks += [{"kind": "tip", "text": claim} for claim in claims]
    base = yaml.safe_dump(draft, allow_unicode=True, sort_keys=False)
    tips = yaml.safe_dump({"b": [{"kind": "tip", "text": PAD} for _ in range(10)]})  # distinct: no aliases
    empty = yaml.safe_dump({"b": []})
    per_bytes = (len(tips.encode()) - len(empty.encode())) / 10
    per_tokens = (len(tokenize(tips)) - len(tokenize(empty))) / 10
    count = min(
        (cap.max_bytes - 1024 - len(base.encode())) / per_bytes,
        (cap.max_tokens - 256 - len(tokenize(base))) / per_tokens,
    )
    blocks += [{"kind": "tip", "text": PAD} for _ in range(int(count))]  # whichever cap binds first
    output = yaml.safe_dump(draft, allow_unicode=True, sort_keys=False)
    while len(output.encode()) > cap.max_bytes - 256 or len(tokenize(output)) > cap.max_tokens - 64:
        del blocks[-20:]  # the estimate ignores nesting depth; trim back under the caps
        output = yaml.safe_dump(draft, allow_unicode=True, sort_keys=False)
    slots, assertions = _writer_claims(fx, "pack", words, claims)

    def validate(reply: str, level: str) -> Any:  # the production validator; the fixture is shape-only
        return parse_and_validate_reply(reply, level.lower())

    return fx, output, slots, assertions, validate


def _max_v7(root: Path) -> tuple[Fixture, str, list, list, Any]:
    cap = FAMILIES["v7_module"].cap
    fx = Fixture(root, "max-v7", "v7_module")
    fx.item = {"item_id": "syn-max-v7", "judging_mode": "authoring", "level": "A2", "writer_prompt": "write"}
    words = [f"v{n:03d}{side}" for n in range(1, cap.batched // 2 + 1) for side in "ab"]
    claims = [f"Line {n:02d} is read twice." for n in range(1, cap.max_claims + 1)]
    text = "# Module\n\n" + "\n".join(f"| {a} | {b} |" for a, b in zip(words[::2], words[1::2], strict=True))
    text += "\n\n" + "\n".join(claims) + "\n\n"
    output = _pad(text, "v7_module", PAD + "\n")
    slots, assertions = _writer_claims(fx, "candidate", words, claims)
    return fx, output, slots, assertions, None


def _max_review(root: Path, family: str) -> tuple[Fixture, str, list, list, Any]:
    cap = FAMILIES[family].cap
    fx = Fixture(root, f"max-{family}", family)
    n_claims = cap.max_claims
    findings, slots, assertions = [], [], []
    if family == "pedagogy_review":
        norm = [
            {"id": f"n-{kind}", "kind": kind, "locator": f"loc-{kind}", "text": f"evidence for {kind}"}
            for kind in (
                "standard_lines",
                "coverage_map",
                "ohoiko_practice",
                "ohoiko_progression",
                "adult_adaptation",
                "video_resource",
                "video_decision",
            )
        ]
        fx.item = {
            "item_id": "syn-max-pedagogy",
            "judging_mode": "authoring",
            "level": "A1",
            "shape": "plan",
            "snippet": {"text": "the snippet under review"},
            "target": "t",
            "learner_state": {"known": "the learner state"},
            "prerequisites": [],
            "resources": [],
            "norm_evidence": norm,
        }
    elif family == "passage_review":
        seeds = [f"e{n:02d}" for n in range(1, n_claims + 1)]
        text = " ".join(f"t{n:02d} {seed}" for n, seed in enumerate(seeds, 1)) + " p01 end"
        fx.item |= {"passage": text}
        errors = [
            {
                "id": seed,
                "start": text.index(seed),
                "end": text.index(seed) + 3,
                "span": seed,
                "error_type": "spelling",
                "accepted": [seed.upper()],
            }
            for seed in seeds
        ]
        at = text.index("p01")
        fx.passage = {
            "id": "syn-max-passage",
            "text": text,
            "errors": errors,
            "protected": [{"id": "p1", "start": at, "end": at + 3, "span": "p01", "kind": "heritage"}],
        }
        corrected = text
        for seed in seeds:
            corrected = corrected.replace(seed, seed.upper())
    form_words = [f"f{n:02d}" for n in range(1, n_claims + 1)]
    batch = fx.call("candidate", "verify_words", {"words": form_words}, _vesum_batch(form_words))
    pad = "x" * 40
    for n in range(1, n_claims + 1):
        fid, claim = f"F{n}", f"claim {n:02d} holds"
        if family == "pedagogy_review":
            defect = PEDAGOGY_DEFECTS[(n - 1) % len(PEDAGOGY_DEFECTS)]
            anchors, receipts = [], []
            for part in PEDAGOGY_ANCHORS[defect]:
                kind = part[0]
                if kind == "textbook_page":
                    rid = fx.call("candidate", "search_text", {"query": f"q{n}"}, _textbook(n))
                    receipts.append(rid)
                    anchors.append({"kind": kind, "evidence": None, "receipt": rid, "quote": f"sentence {n:02d}"})
                elif kind == "learner_state":
                    anchors.append(
                        {"kind": kind, "evidence": "/learner_state/known", "receipt": None, "quote": "learner state"}
                    )
                elif kind == "leak":
                    anchors.append({"kind": kind, "evidence": "/snippet/text", "receipt": None, "quote": "snippet"})
                else:
                    anchors.append(
                        {"kind": kind, "evidence": f"n-{kind}", "receipt": None, "quote": f"evidence for {kind}"}
                    )
            finding = {
                "id": fid,
                "defect": defect,
                "norm": "ohoiko_method",
                "anchors": anchors,
                "location": {"field": "/snippet/text", "quote": "under review"},
                "claim": claim + pad,
                "proposed_edit": None,
                "receipts": receipts,
            }
            facet = "pedagogy"
            binding = {
                "role": "request",
                "evidence_id": "/snippet/text",
                "evidence_excerpt": "under review",
                "source_locator": "/snippet/text",
            }
        elif family == "exercise_review":
            defect = ("giveaway_gloss", "stem_names_answer", "form", "wrong_key", "stress", "form")[(n - 1) % 6]
            receipts = []
            if defect in EXERCISE_REQUEST_DEFECTS:
                facet = "exercise"
                binding = {
                    "role": "request",
                    "evidence_id": f"/exercise/items/{n - 1}/stem",
                    "evidence_excerpt": f"w{n}",
                    "source_locator": f"/exercise/items/{n - 1}/stem",
                }
            elif defect == "form":
                facet, receipts = "form", [batch]
                binding = _bound(fx, "candidate", batch, f"- **f{n:02d}** — FOUND", "VESUM")
            else:
                facet = "meaning" if defect == "wrong_key" else "stress"
                rid = fx.call("candidate", "query_sum20", {"word": f"s{n:02d}"}, _sum20(f"s{n:02d}"))
                receipts = [rid]
                binding = _bound(fx, "candidate", rid, f"**s{n:02d}x** (noun)", f"https://sum20.example/s{n:02d}")
            finding = _finding(fid, n, claim + pad, receipts, defect=defect)
        else:
            facet = ("meaning", "stress", "form")[(n - 1) % 3] if family == "card_review" else "form"
            if facet == "form":
                receipts = [batch]
                binding = _bound(fx, "candidate", batch, f"- **f{n:02d}** — FOUND", "VESUM")
            else:
                rid = fx.call("candidate", "query_sum20", {"word": f"s{n:02d}"}, _sum20(f"s{n:02d}"))
                receipts = [rid]
                binding = _bound(fx, "candidate", rid, f"**s{n:02d}x** (noun)", f"https://sum20.example/s{n:02d}")
            field = "/passage" if family == "passage_review" else "/card"
            edit = {"field": field, "replacement": f"E{n:02d}"} if family == "passage_review" else None
            finding = {
                "id": fid,
                "facet": facet,
                "location": {"field": field, "quote": "x"},
                "claim": claim + pad,
                "proposed_edit": edit,
                "receipts": receipts,
            }
        slot = f"e{n:02d}" if family == "passage_review" else f"s{n}"
        slots.append({"slot_id": slot, "facet": facet})
        kind = "edit" if family == "passage_review" else "assertion"
        assertions.append(_assertion(f"A{n}", claim, fid, facet=facet, kind=kind, slot_id=slot, bindings=[binding]))
        findings.append(finding)
    envelope = {
        "item_id": fx.item["item_id"],
        "judging_mode": fx.item["judging_mode"],
        "outcome": "findings",
        "findings": findings,
        "gaps": [],
    }
    if family == "passage_review":
        envelope["corrected_text"] = corrected
    output = json.dumps(envelope, indent=1)
    while (  # grow the claims towards whichever cap binds first
        len(output.encode()) + len(pad) * n_claims < cap.max_bytes - 256
        and len(tokenize(output)) + 2 * n_claims < cap.max_tokens - 64
    ):
        for finding in findings:
            finding["claim"] += pad
        output = json.dumps(envelope, indent=1)
    return fx, output, slots, assertions, None


def max_size_cells(root: Path) -> list[dict[str, Any]]:
    """Accepted, production-shaped outputs at each family's caps, every claim bound within 32 calls."""
    cases = []
    for family in FAMILIES:
        if family in ("fresh_lesson", "fresh_activities"):
            fx, output, slots, assertions, validate = _max_fresh(root, family)
        elif family == "v7_module":
            fx, output, slots, assertions, validate = _max_v7(root)
        else:
            fx, output, slots, assertions, validate = _max_review(root, family)
        label = _label(fx.item, family, required=0) | {
            "required_slots": slots,
            "positive_slots": slots,
            "protected": [],
            "obligations": [],
            "O": len(slots) + 3,
        }
        if family == "passage_review":
            label |= {"passage": fx.passage, "protected": [{"opportunity_id": "p1", "stratum": "heritage"}]}
        judge_calls = len(ledger.records(fx.paths["judge"]))
        reply = _reply(fx, assertions, sources_calls=judge_calls)
        reply["protected"] = (
            [{"opportunity_id": "p1", "preserved": True, "harm": False}] if family == ("passage_review") else []
        )
        reply["obligations"] = []
        index = fx.index()
        sidecar = judge.bind_reply(
            json.dumps(reply), item_id=fx.item["item_id"], output_id="out-fixture", output=output, index=index
        )
        result = score_cell(
            family, label=label, item=fx.item, output=output, sidecar=sidecar, index=index, validate_draft=validate
        )
        cap = FAMILIES[family].cap
        fill = max(len(output.encode("utf-8")) / cap.max_bytes, len(tokenize(output)) / cap.max_tokens)
        cases.append(
            _case(
                f"{family}: accepted maximum-size output, every claim bound within 32 judge calls",
                ("accepted", COMPLETE, 1.0, len(assertions), True, True),
                (
                    result["response"],
                    result["status"],
                    result["R"],
                    result["counts"]["receipt_bound_assertions"],
                    judge_calls <= 32,
                    fill >= 0.9,
                ),
            )
        )
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
        cases = worked_ordering(root) + branches(root) + review_probes(root) + max_size_coverage()
        cases += max_size_cells(root) + boundaries(root)
    return {"proof": PROOF, "cases": cases, "pass": all(case["pass"] for case in cases)}
