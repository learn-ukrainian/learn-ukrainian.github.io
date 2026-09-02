"""Fixture-driven adversarial coverage for the V4 arena receipt."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

from scripts.projects.open_model_data import v4_arena_receipt as arena

H = "a" * 64
REPO_ROOT = Path(__file__).resolve().parents[1]


def _proposal(candidate_id: str, provider_id: str, labels: list[str]) -> str:
    return arena.format_proposal(
        {
            "schema_version": arena.PROPOSAL_SCHEMA_VERSION,
            "candidate_id": candidate_id,
            "provider_id": provider_id,
            "cases": [
                {"case_id": f"synthetic-{index:02d}", "label": label, "tags": ["synthetic"]}
                for index, label in enumerate(labels, 1)
            ],
        }
    )


def _fixture() -> dict[str, object]:
    cases = [f"synthetic-{index:02d}" for index in range(1, 21)]
    candidates = {
        f"candidate-{index}": {"provider_id": f"provider-{index}", "route_id": f"route-{index}"}
        for index in range(1, 5)
    }
    common = ["accept"] * 17
    outputs = {
        "candidate-1": _proposal("candidate-1", "provider-1", [*common, "accept", "reject", "accept"]),
        "candidate-2": _proposal("candidate-2", "provider-2", [*common, "reject", "reject", "accept"]),
        "candidate-3": _proposal("candidate-3", "provider-3", [*common, "accept", "accept", "reject"]),
        "candidate-4": "not a marker payload after retry",
    }
    ballots = [
        {"voter_candidate_id": voter, "candidate_id": target, "case_id": case_id, "label": "accept"}
        for voter in candidates
        for target in candidates
        if voter != target
        for case_id in cases
    ]
    return {
        "outcome_sha256": H,
        "prompt_sha256": "b" * 64,
        "case_ids": cases,
        "route_denominator": [f"route-{index}" for index in range(1, 5)],
        "candidate_map": candidates,
        "provider_outputs": outputs,
        "ballots": ballots,
        "allowed_labels": ["accept", "reject"],
        "allowed_tags": ["synthetic"],
    }


def test_observed_twenty_case_shape_is_quarantined_and_text_free() -> None:
    fixture = _fixture()
    receipts = arena.build_receipts(**fixture)  # type: ignore[arg-type]
    public, private = receipts["public"], receipts["private"]
    assert public["counts"] == {
        "declared_routes": 4,
        "valid_routes": 3,
        "invalid_routes": 1,
        "exact_agreement_cases": 17,
        "disputed_cases": 3,
    }
    assert all(case["disposition"] == arena.QUARANTINE for case in public["cases"])
    assert public["eligibility"] == {"gold": False, "training": False, "evaluation": False, "teaching": False, "coverage": False}
    assert "not a marker payload" not in arena.canonical_json(public)
    assert "not a marker payload" not in arena.canonical_json(private)
    assert arena.verify_receipt(public) == public
    assert arena.verify_receipt(private) == private


def test_denominator_shrink_and_candidate_map_drift_fail_closed() -> None:
    fixture = _fixture()
    fixture["route_denominator"] = ["route-1", "route-2", "route-3"]
    try:
        arena.build_receipts(**fixture)  # type: ignore[arg-type]
    except arena.ArenaReceiptError as exc:
        assert "route" in str(exc)
    else:
        raise AssertionError("denominator shrink was accepted")


def test_duplicate_provider_bindings_fail_closed() -> None:
    fixture = _fixture()
    fixture["candidate_map"]["candidate-2"]["provider_id"] = "provider-1"  # type: ignore[index]
    try:
        arena.build_receipts(**fixture)  # type: ignore[arg-type]
    except arena.ArenaReceiptError as exc:
        assert str(exc) == "candidate map has duplicate provider binding"
    else:
        raise AssertionError("duplicate provider binding was accepted")


def test_bad_ballots_are_explicit_residuals() -> None:
    fixture = _fixture()
    ballots = fixture["ballots"]
    assert isinstance(ballots, list)
    ballots.append(copy.deepcopy(ballots[0]))
    ballots.append({"voter_candidate_id": "candidate-1", "candidate_id": "candidate-1", "case_id": "synthetic-01", "label": "accept"})
    ballots.append({"voter_candidate_id": "candidate-1", "candidate_id": "invented", "case_id": "synthetic-01", "label": "accept"})
    receipts = arena.build_receipts(**fixture)  # type: ignore[arg-type]
    codes = {item["code"] for item in receipts["public"]["residuals"]}
    assert {"DUPLICATE_CASE_BALLOT", "SELF_VOTE", "UNKNOWN_CANDIDATE"} <= codes


def test_duplicate_case_ids_and_malformed_provider_output_are_residuals() -> None:
    fixture = _fixture()
    raw = json.loads(_proposal("candidate-2", "provider-2", ["accept"] * 20).split("\n", 1)[1].rsplit("\n", 1)[0])
    raw["cases"][1]["case_id"] = "synthetic-01"
    fixture["provider_outputs"]["candidate-2"] = arena.format_proposal(raw)  # type: ignore[index]
    receipts = arena.build_receipts(**fixture)  # type: ignore[arg-type]
    codes = {item["code"] for item in receipts["public"]["residuals"]}
    assert "DUPLICATE_CASE_ID" in codes
    assert "MALFORMED_PROVIDER_OUTPUT" in codes


def test_missing_case_ballots_are_not_normalized_away() -> None:
    fixture = _fixture()
    fixture["ballots"] = [  # type: ignore[index]
        ballot for ballot in fixture["ballots"]
        if not (ballot["voter_candidate_id"] == "candidate-3" and ballot["candidate_id"] == "candidate-2" and ballot["case_id"] == "synthetic-20")
    ]
    receipts = arena.build_receipts(**fixture)  # type: ignore[arg-type]
    assert "MISSING_CASE_BALLOT" in {item["code"] for item in receipts["public"]["residuals"]}


def test_hash_replay_and_cli_are_deterministic(tmp_path: Path) -> None:
    fixture = _fixture()
    assert arena.build_receipts(**fixture) == arena.build_receipts(**copy.deepcopy(fixture))  # type: ignore[arg-type]
    input_path, private_path, public_path = tmp_path / "input.json", tmp_path / "private.json", tmp_path / "public.json"
    input_path.write_text(json.dumps(fixture), encoding="utf-8")
    command = [sys.executable, str(REPO_ROOT / "scripts/projects/open_model_data/v4_arena_receipt.py"), "--input", str(input_path), "--private-output", str(private_path), "--public-output", str(public_path)]
    result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    assert arena.verify_receipt(json.loads(public_path.read_text()))["receipt_sha256"]


def test_one_format_only_retry_recovers_a_malformed_primary_output() -> None:
    fixture = _fixture()
    recovered = arena.format_proposal(
        {
            "schema_version": arena.PROPOSAL_SCHEMA_VERSION,
            "candidate_id": "candidate-4",
            "provider_id": "provider-4",
            "cases": [{"case_id": cid, "label": "accept", "tags": ["synthetic"]} for cid in [f"synthetic-{i:02d}" for i in range(1, 21)]],
        }
    )
    fixture["provider_outputs"]["candidate-4"] = {"primary": "not a marker payload", "retry": recovered}
    receipts = arena.build_receipts(**fixture)  # type: ignore[arg-type]
    statuses = {item["candidate_id"]: item for item in receipts["public"]["route_statuses"]}
    assert statuses["candidate-4"]["status"] == "valid"
    assert statuses["candidate-4"]["retried"] is True
    assert receipts["public"]["counts"]["valid_routes"] == 4


def test_one_format_only_retry_still_records_failure_when_retry_also_malformed() -> None:
    fixture = _fixture()
    fixture["provider_outputs"]["candidate-4"] = {"primary": "still not a marker payload", "retry": "also not a marker payload"}
    receipts = arena.build_receipts(**fixture)  # type: ignore[arg-type]
    statuses = {item["candidate_id"]: item for item in receipts["public"]["route_statuses"]}
    assert statuses["candidate-4"]["status"] == "invalid"
    assert statuses["candidate-4"]["retried"] is True
    assert statuses["candidate-4"]["residual_code"] == "MALFORMED_PROVIDER_OUTPUT"


def test_non_format_failure_is_never_retried() -> None:
    fixture = _fixture()
    # PROVIDER_ID_DRIFT is a content/schema failure, not a format failure -- a
    # retry payload must never be consulted for it.
    wrong_provider = arena.format_proposal(
        {
            "schema_version": arena.PROPOSAL_SCHEMA_VERSION,
            "candidate_id": "candidate-4",
            "provider_id": "not-the-bound-provider",
            "cases": [{"case_id": cid, "label": "accept", "tags": ["synthetic"]} for cid in [f"synthetic-{i:02d}" for i in range(1, 21)]],
        }
    )
    fixture["provider_outputs"]["candidate-4"] = {"primary": wrong_provider, "retry": _proposal("candidate-4", "provider-4", ["accept"] * 20)}
    receipts = arena.build_receipts(**fixture)  # type: ignore[arg-type]
    statuses = {item["candidate_id"]: item for item in receipts["public"]["route_statuses"]}
    assert statuses["candidate-4"]["status"] == "invalid"
    assert statuses["candidate-4"]["retried"] is False
    assert statuses["candidate-4"]["residual_code"] == "PROVIDER_ID_DRIFT"


def test_leave_one_out_ballots_never_mix_in_a_candidates_own_self_report() -> None:
    fixture = _fixture()
    # Every candidate's own ballots vote "accept" for every peer/case in the base
    # fixture; make candidate-2 vote "reject" for candidate-1's first case only, and
    # confirm the leave-one-out summary reflects only *peer* ballots (never
    # candidate-1's own proposal label, which is "accept" for that case).
    ballots = fixture["ballots"]
    assert isinstance(ballots, list)
    for ballot in ballots:
        if ballot["voter_candidate_id"] == "candidate-2" and ballot["candidate_id"] == "candidate-1" and ballot["case_id"] == "synthetic-01":
            ballot["label"] = "reject"
    receipts = arena.build_receipts(**fixture)  # type: ignore[arg-type]
    first_case = receipts["public"]["cases"][0]
    assert first_case["case_id"] == "synthetic-01"
    loo = {item["candidate_id"]: item for item in first_case["leave_one_out_ballots"]}
    assert loo["candidate-1"]["label_counts"] == {"accept": 2, "reject": 1}
    assert loo["candidate-1"]["unanimous"] is False
    assert loo["candidate-1"]["voter_count"] == 3
    assert loo["candidate-1"]["consensus_label"] == "accept"


def test_leave_one_out_ballots_report_no_consensus_on_an_exact_split() -> None:
    fixture = _fixture()
    ballots = fixture["ballots"]
    assert isinstance(ballots, list)
    for ballot in ballots:
        if ballot["candidate_id"] == "candidate-1" and ballot["case_id"] == "synthetic-01" and ballot["voter_candidate_id"] in {"candidate-2", "candidate-3"}:
            ballot["label"] = "reject" if ballot["voter_candidate_id"] == "candidate-2" else "accept"
        elif ballot["candidate_id"] == "candidate-1" and ballot["case_id"] == "synthetic-01":
            ballot["label"] = "reject"
    receipts = arena.build_receipts(**fixture)  # type: ignore[arg-type]
    loo = {item["candidate_id"]: item for item in receipts["public"]["cases"][0]["leave_one_out_ballots"]}
    assert loo["candidate-1"]["label_counts"] == {"accept": 1, "reject": 2}
    assert loo["candidate-1"]["consensus_label"] == "reject"


def test_receipt_schema_drift_fails_closed_even_when_rehashed() -> None:
    receipt = arena.build_receipts(**_fixture())["public"]  # type: ignore[arg-type]
    receipt["unexpected"] = True
    receipt["receipt_sha256"] = arena.sha256_value({key: value for key, value in receipt.items() if key != "receipt_sha256"})
    try:
        arena.verify_receipt(receipt)
    except arena.ArenaReceiptError as exc:
        assert "schema drift" in str(exc)
    else:
        raise AssertionError("rehashed schema drift was accepted")
