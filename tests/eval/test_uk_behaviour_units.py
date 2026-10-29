"""Unit tests of the uk-behaviour/2 scorer parts: reward, binding, adapters, judge, pins."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.eval.uk_behaviour import adapters, judge, pins
from scripts.eval.uk_behaviour.binding import (
    EVIDENCE_INVALID,
    EVIDENCE_MISSING,
    FABRICATED,
    SUM11_POSITIVE,
    VERIFIED,
    LedgerIndex,
    LedgerRef,
    arguments_sha256,
    check_binding,
    sha256_text,
)
from scripts.eval.uk_behaviour.contract import (
    COMPLETE,
    FAMILIES,
    INVALID_FABRICATED_RECEIPT,
    INVALID_OVERPRODUCTION,
    UNRESOLVED_EVALUATOR,
    answer_position_pattern,
    load_manifest,
    manifest_problems,
)
from scripts.eval.uk_behaviour.reward import Components, quality, resolve_status, reward
from scripts.eval.uk_behaviour.runner import admission_refusal, plan_cells
from scripts.review.receipts import ledger

SHA = "0" * 64


# --------------------------------------------------------------------------- reward


def test_complete_safety_passing_outranks_incomplete_and_refusal() -> None:
    worst_complete = reward(Components(1, 0.0, 0.0, 10, 0, 10, 0, 10), status=COMPLETE, response="accepted")
    best_incomplete = reward(Components(0, 1.0, 1.0, 0, 0, 0, 0, 10), status=COMPLETE, response="accepted")
    refusal = reward(Components(0, 0.0, 0.0, 0, 0, 0, 0, 10), status=COMPLETE, response="refusal")
    assert worst_complete == 0.1 > best_incomplete == 0.0 > refusal == -1.0


def test_harm_overrides_every_status_and_invalid_precedes_unresolved() -> None:
    harmed = Components(1, 1.0, 1.0, 0, 0, 0, 1, 10)
    for status in (COMPLETE, UNRESOLVED_EVALUATOR, INVALID_OVERPRODUCTION, INVALID_FABRICATED_RECEIPT):
        assert reward(harmed, status=status, response="accepted") == -2.0
    flags = {UNRESOLVED_EVALUATOR, INVALID_OVERPRODUCTION, INVALID_FABRICATED_RECEIPT}
    assert resolve_status(flags) == INVALID_FABRICATED_RECEIPT
    assert resolve_status(flags - {INVALID_FABRICATED_RECEIPT}) == INVALID_OVERPRODUCTION
    assert resolve_status(set()) == COMPLETE


def test_penalties_saturate_and_o_is_positive() -> None:
    assert quality(Components(1, 1.0, 1.0, 50, 0, 0, 0, 10)) == 0.0
    with pytest.raises(ValueError):
        Components(1, 1.0, 1.0, 0, 0, 0, 0, 0)


def test_missing_output_on_an_unanswerable_item_is_still_silence() -> None:
    nothing = Components(0, 0.0, 0.0, 0, 0, 0, 0, 3)
    assert reward(nothing, status=COMPLETE, response="missing", answerable=False) == -1.0


# --------------------------------------------------------------------------- answer-position rule


@pytest.mark.parametrize(
    ("keys", "defect"),
    [
        ([0, 0, 0, 0, 0, 1], True),  # one position holds 5 of 6 (>= ceil(4.8))
        ([0, 0, 0, 0, 1, 2], False),
        ([0, 1, 0, 1, 0, 1], True),  # period 2
        ([0, 1, 2, 0, 1, 2], True),  # period 3
        ([0, 1, 2, 2, 1, 0], False),
        ([0, 0, 0, 0, 0], False),  # fewer than six items
    ],
)
def test_answer_position_rule(keys: list[int], defect: bool) -> None:
    assert answer_position_pattern(keys) is defect


# --------------------------------------------------------------------------- binding


@pytest.fixture
def index(tmp_path: Path) -> tuple[LedgerIndex, dict[str, str]]:
    path = tmp_path / "rv-unit" / "cand.jsonl"
    ledger.create_empty_ledger(path)
    receipts = {}
    for name, tool, result in (
        ("words", "verify_words", "Found: 1/1\n- **x** — FOUND"),
        ("miss", "verify_words", "Found: 0/1\n- **y** — NOT FOUND"),
        ("sum11", "search_definitions", "СУМ-11 notice\nentry for x"),
        ("slovnyk", "search_slovnyk_me", "Source: СУМ-11\nentry for x"),
    ):
        receipts[name] = ledger.append(
            path,
            review_id="rv-unit",
            attempt_id="cand",
            manifest_sha256=SHA,
            tool=tool,
            server_version="t",
            arguments={"q": name},
            snapshots={},
            status="ok",
            result=result,
        )
    refs = [LedgerRef("candidate", path, "rv-unit", "cand", SHA)]
    return LedgerIndex(refs, {"standard": "line 233: listening"}), receipts


def _binding(index: LedgerIndex, receipt_id: str, excerpt: str, **extra) -> dict:
    record = index.get("candidate", receipt_id)
    return {
        "role": "candidate",
        "receipt_id": receipt_id,
        "tool": record["tool"],
        "arguments_sha256": arguments_sha256(record["arguments"]),
        "result_sha256": sha256_text(record["result"]),
        "evidence_excerpt": excerpt,
        "source_locator": "loc",
    } | extra


def test_binding_verifies_and_types_each_failure(index) -> None:
    idx, receipts = index
    good = _binding(idx, receipts["words"], "Found: 1/1")
    assert check_binding(good, "form", idx).status == VERIFIED
    assert check_binding(good | {"evidence_excerpt": "not there"}, "form", idx).status == EVIDENCE_INVALID
    assert check_binding(good | {"result_sha256": SHA}, "form", idx).status == EVIDENCE_INVALID
    assert check_binding(good, "stress", idx).status == EVIDENCE_INVALID  # verify_words is no stress authority
    assert check_binding(good | {"receipt_id": "rr-" + "a" * 20}, "form", idx).status == FABRICATED
    judge_role = good | {"role": "judge"}
    assert check_binding(judge_role, "form", idx).status == EVIDENCE_MISSING
    miss = _binding(idx, receipts["miss"], "NOT FOUND")
    assert check_binding(miss, "form", idx).status == EVIDENCE_INVALID  # absence is not positive evidence
    assert check_binding(miss | {"polarity": "negative"}, "form", idx).status == VERIFIED


def test_sum11_is_never_positive_authority(index) -> None:
    idx, receipts = index
    assert check_binding(_binding(idx, receipts["sum11"], "entry for x"), "meaning", idx).status == SUM11_POSITIVE
    slovnyk = _binding(idx, receipts["slovnyk"], "entry for x")
    assert check_binding(slovnyk, "meaning", idx).status == EVIDENCE_INVALID  # dictionary not named
    named = slovnyk | {"underlying_dictionary": "СУМ-11"}
    assert check_binding(named, "meaning", idx).status == SUM11_POSITIVE


def test_request_evidence_supports_pedagogy_only(index) -> None:
    idx, _ = index
    binding = {"role": "request", "evidence_id": "standard", "evidence_excerpt": "line 233", "source_locator": "s"}
    assert check_binding(binding, "pedagogy", idx).status == VERIFIED
    assert check_binding(binding, "meaning", idx).status == EVIDENCE_INVALID
    assert check_binding(binding | {"evidence_id": "other"}, "pedagogy", idx).status == EVIDENCE_MISSING


def test_ledger_of_another_attempt_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "rv-x" / "a.jsonl"
    ledger.create_empty_ledger(path)
    ledger.append(
        path,
        review_id="rv-x",
        attempt_id="a",
        manifest_sha256=SHA,
        tool="verify_words",
        server_version="t",
        arguments={},
        snapshots={},
        status="ok",
        result="Found: 1/1",
    )
    from scripts.eval.uk_behaviour.binding import BindingError

    with pytest.raises(BindingError):
        LedgerIndex([LedgerRef("candidate", path, "rv-x", "b", SHA)])


# --------------------------------------------------------------------------- adapters


CARD = {"item_id": "c1", "judging_mode": "repair", "level": "A1", "card": {"lemma": "x"}, "context": "ctx"}


def test_review_request_is_prompt_frame_and_canonical_item() -> None:
    text = adapters.render_review("card_review", CARD, b"PROMPT\n")
    assert text.startswith("PROMPT\n\n## Request\n")
    assert json.loads(text.split("```json\n", 1)[1].split("\n```", 1)[0]) == CARD
    passage = adapters.render_review(
        "passage_review", {"item_id": "p", "judging_mode": "repair", "level": "A1", "passage": "t"}, b"P"
    )
    assert "corrected_text" in passage and passage.startswith("P\n\n## Evaluation input and reply")


def test_mode_and_family_contracts_are_enforced() -> None:
    with pytest.raises(adapters.AdapterError):
        adapters.render_review("card_review", CARD | {"judging_mode": "authoring"}, b"P")
    with pytest.raises(adapters.AdapterError):
        adapters.render_review("fresh_lesson", CARD, b"P")
    v7 = {"item_id": "v", "judging_mode": "authoring", "level": "A2", "writer_prompt": "WRITE"}
    assert adapters.render_v7(v7, b"CONTRACT\n") == "CONTRACT\n\nWRITE"


def test_pinned_bytes_refuse_drift() -> None:
    assert adapters.pinned_bytes(b"p", sha256_text("p"), "x") == b"p"
    with pytest.raises(adapters.AdapterError):
        adapters.pinned_bytes(b"q", sha256_text("p"), "x")


def _envelope(**overrides) -> str:
    value = {"item_id": "c1", "judging_mode": "repair", "outcome": "clean", "findings": [], "gaps": []}
    return json.dumps(value | overrides)


def test_acceptance() -> None:
    assert adapters.accept("card_review", _envelope(), CARD).response == "accepted"
    assert adapters.accept("card_review", "   ", CARD).response == "missing"
    assert adapters.accept("card_review", "no json here", CARD).response == "malformed"
    assert adapters.accept("card_review", _envelope(item_id="other"), CARD).response == "malformed"
    assert adapters.accept("card_review", _envelope(outcome="findings"), CARD).response == "malformed"
    assert adapters.accept("card_review", _envelope(extra=1), CARD).response == "malformed"
    finding = {
        "id": "F1",
        "facet": "stress",
        "location": {"field": "/card", "quote": "x"},
        "claim": "c",
        "proposed_edit": None,
        "receipts": ["rr-" + "1" * 20],
    }
    accepted = adapters.accept("card_review", _envelope(outcome="findings", findings=[finding]), CARD)
    assert accepted.cited_receipts == ["rr-" + "1" * 20]
    pedagogy = finding | {"defect": "child_level", "norm": "ohoiko_method", "anchor": "practice 7"}
    pedagogy.pop("facet")
    item = {"item_id": "c1", "judging_mode": "repair", "level": "A1"}
    assert adapters.accept("pedagogy_review", _envelope(outcome="findings", findings=[pedagogy]), item).response == (
        "accepted"
    )
    edited = pedagogy | {"proposed_edit": {"field": "/snippet", "replacement": "r"}}
    assert adapters.accept("pedagogy_review", _envelope(outcome="findings", findings=[edited]), item).response == (
        "malformed"
    )


def test_every_family_cap_fits_the_judge_budget() -> None:
    from scripts.eval.uk_behaviour.coverage import worst_case_calls

    assert all(worst_case_calls(family) <= 32 for family in FAMILIES)


# --------------------------------------------------------------------------- judge


TEMPLATE = " ".join(judge.PLACEHOLDERS).encode()


def test_judge_request_fills_each_placeholder_once_without_reexpansion() -> None:
    text = judge.render_judge_request(
        TEMPLATE,
        family="card_review",
        request="{{LABEL}}",
        output_id="out-1",
        output="O",
        label={"item_id": "c1"},
        candidate_receipts=[],
    )
    assert text.startswith("{") and "{{LABEL}}" in text  # the request's literal placeholder stays literal
    assert '"item_id": "c1"' in text and "out-1" in text
    with pytest.raises(judge.JudgeError):
        judge.render_judge_request(
            TEMPLATE + b"{{OUTPUT}}",
            family="card_review",
            request="",
            output_id="o",
            output="",
            label={},
            candidate_receipts=[],
        )
    with pytest.raises(judge.JudgeError):
        judge.render_judge_request(
            TEMPLATE,
            family="card_review",
            request="",
            output_id="o",
            output="",
            label={"variant": "v"},
            candidate_receipts=[],
        )


def test_bind_reply_computes_offsets_and_digests(index) -> None:
    idx, receipts = index
    output = "abc claim one, claim one"
    reply = {
        "item_id": "c1",
        "output_id": "out-1",
        "response_kind": "answered",
        "outcome_correct": None,
        "assertions": [
            {
                "id": "A1",
                "span": {"quote": "claim one", "occurrence": 1},
                "finding_id": None,
                "facet": "form",
                "kind": "assertion",
                "slot_id": None,
                "duplicate_of": None,
                "verdict": "correct",
                "unchecked_reason": None,
                "false_correction": False,
                "protected_opportunity_id": None,
                "harm": False,
                "bindings": [
                    {
                        "role": "candidate",
                        "receipt_id": receipts["words"],
                        "evidence_excerpt": "Found: 1/1",
                        "source_locator": "VESUM",
                    }
                ],
            }
        ],
        "protected": [],
        "obligations": [],
        "sources_calls": 1,
        "budget_exhausted": False,
        "evaluator_limits": [],
    }
    sidecar = judge.bind_reply(json.dumps(reply), item_id="c1", output_id="out-1", output=output, index=idx)
    span = sidecar["assertions"][0]["span"]
    assert (span["start"], span["end"]) == (15, 24) and output[15:24] == "claim one"
    assert sidecar["output_sha256"] == sha256_text(output)
    assert check_binding(sidecar["assertions"][0]["bindings"][0], "form", idx).status == VERIFIED
    assert judge.parse_sidecar(json.dumps(sidecar)) == sidecar
    with pytest.raises(judge.JudgeError):
        judge.bind_reply(
            json.dumps(reply | {"output_id": "x"}), item_id="c1", output_id="out-1", output=output, index=idx
        )


def test_shuffle_and_audit_sample_are_seeded_and_stratified() -> None:
    cells = [
        {
            "task_id": f"t-{model}-{family}-{n}",
            "model": model,
            "family": family,
            "judging_mode": "repair" if n % 2 else "authoring",
        }
        for model in ("sol", "terra")
        for family in FAMILIES
        for n in range(6)
    ]
    sample = judge.audit_sample(cells, 32)
    assert sample == judge.audit_sample(list(reversed(cells)), 32)
    chosen = [cell for cell in cells if cell["task_id"] in sample]
    assert {(c["model"], c["family"]) for c in chosen} == {(m, f) for m in ("sol", "terra") for f in FAMILIES}
    for model in ("sol", "terra"):
        modes = {c["judging_mode"] for c in chosen if c["model"] == model and c["family"] == "pedagogy_review"}
        assert modes == {"repair", "authoring"}
    ids = [cell["task_id"] for cell in cells]
    assert judge.shuffled(ids) == judge.shuffled(list(reversed(ids))) != sorted(ids)


# --------------------------------------------------------------------------- runner and manifest


def test_cells_give_both_candidates_identical_bytes_and_refuse_paid_runs() -> None:
    bundle = {
        "bundle": "uk-behaviour-v2/requests",
        "split": "development",
        "items": [{"family": "card_review", "item": CARD}],
    }
    tasks = plan_cells(bundle, {"card_review": b"PROMPT"}, "unit")
    assert len(tasks) == 6 and len({task.prompt for task in tasks}) == 1
    assert {task.seat.model for task in tasks} == {"gpt-6.1-sol", "gpt-6.1-terra"}
    assert {task.repeat for task in tasks} == {1, 2, 3}
    assert admission_refusal(load_manifest()) is not None


def test_manifest_matches_the_scorer_and_pins_its_code() -> None:
    manifest = load_manifest()
    assert manifest_problems(manifest) == []
    found = pins.problems(manifest)
    # Inherited and production asset drift is checked before each phase by verify-pins, not here:
    # an unrelated change to a production file must not fail this suite.
    assert [problem for problem in found if not problem.startswith("asset ")] == []
    freeze = next(asset for asset in manifest["assets"] if asset["path"] == "docs/evaluations/uk-behaviour-freeze.md")
    assert pins.file_sha256(pins.REPO_ROOT / freeze["path"]) == freeze["sha256"]
