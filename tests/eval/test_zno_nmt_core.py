from __future__ import annotations

import copy
import os
from pathlib import Path

import pytest

from scripts.eval.zno_nmt import (
    ExamError,
    canonical,
    compare_runs,
    digest,
    prepare_exam,
    read_json,
    score_run,
    validate_key,
    validate_packet,
    write_private_json,
)


def _exam(*, scoring_kind: str = "benchmark", threshold: int | None = None) -> dict:
    return {
        "schema": "zno-nmt.exam.v1",
        "title": "Synthetic paper",
        "subject": "Ukrainian",
        "year": 2022,
        "provenance": {
            "source_url": "https://example.test/paper",
            "source_revision": "synthetic-r1",
            "license": "test-only",
            "exposure": "synthetic",
        },
        "scoring": {
            "kind": scoring_kind,
            "policy_url": "https://example.test/policy" if scoring_kind == "official" else None,
            "pass_threshold": threshold,
            "expected_items": 3,
            "expected_points": 4,
        },
        "items": [
            {
                "id": "source-0",
                "kind": "single",
                "question": "Choose one.",
                "options": [{"id": "A", "text": "first"}, {"id": "B", "text": "second"}],
                "rows": [],
                "correct": "A",
            },
            {
                "id": "source-1",
                "kind": "matching",
                "question": "Match the numbered phrases.",
                "options": [
                    {"id": "A", "text": "one"},
                    {"id": "B", "text": "two"},
                    {"id": "C", "text": "three"},
                ],
                "rows": [{"id": "r1", "text": ""}, {"id": "r2", "text": ""}],
                "correct": {"r1": "A", "r2": "B"},
            },
            {
                "id": "source-2",
                "kind": "single",
                "question": "Choose another.",
                "options": [{"id": "A", "text": "first"}, {"id": "B", "text": "second"}],
                "rows": [],
                "correct": "B",
            },
        ],
    }


def _prepared(*, scoring_kind: str = "benchmark", threshold: int | None = None) -> tuple[dict, dict]:
    return prepare_exam(_exam(scoring_kind=scoring_kind, threshold=threshold))


def _run(
    packet: dict,
    *,
    condition: str,
    status: str = "ok",
    responses: dict | None = None,
    identity: dict | None = None,
    comparison: dict | None = None,
    metrics: dict | None = None,
) -> dict:
    run = {
        "schema": "zno-nmt.run.v1",
        "packet_sha256": packet["packet_sha256"],
        "condition": condition,
        "status": status,
        "responses": {} if responses is None else responses,
        "identity": {
            "model": "synthetic-model",
            "harness": "test-harness",
            "effective_effort": "high",
        }
        if identity is None
        else identity,
        "comparison": {"prompt_sha256": "prompt"} if comparison is None else comparison,
        "metrics": {} if metrics is None else metrics,
    }
    if status == "failed":
        run["failure_reason"] = "synthetic failure"
    return run


def test_canonical_digest_and_prepare_are_deterministic_and_hide_gold() -> None:
    packet, key = _prepared()
    assert canonical({"b": "ю", "a": 1}) == '{"a":1,"b":"ю"}'
    assert digest({"a": 1}) == digest({"a": 1})
    assert packet["items"][0]["id"] == "q0001"
    assert [item["id"] for item in packet["items"]] == ["q0001", "q0002", "q0003"]
    assert all(set(item) == {"id", "kind", "question", "options", "rows"} for item in packet["items"])
    assert "correct" not in packet["items"][0]
    assert "source_url" not in packet
    assert key["answers"] == {"q0001": "A", "q0002": {"r1": "A", "r2": "B"}, "q0003": "B"}
    validate_packet(packet)
    validate_key(packet, key)


def test_packet_and_key_reject_tampering_and_nested_leakage() -> None:
    packet, key = _prepared()
    leaked = copy.deepcopy(packet)
    leaked["items"][0]["correct"] = "A"
    with pytest.raises(ExamError):
        validate_packet(leaked)

    changed_packet = copy.deepcopy(packet)
    changed_packet["items"][0]["question"] = "tampered"
    with pytest.raises(ExamError):
        validate_packet(changed_packet)

    changed_key = copy.deepcopy(key)
    changed_key["answers"]["q0001"] = "B"
    with pytest.raises(ExamError):
        validate_key(packet, changed_key)

    rebound_key = copy.deepcopy(key)
    rebound_key["packet_sha256"] = "0" * 64
    with pytest.raises(ExamError):
        validate_key(packet, rebound_key)


def test_partial_matching_and_repeated_columns_score_per_pair() -> None:
    packet, key = _prepared()
    run = _run(
        packet,
        condition="sources",
        responses={"q0002": {"r1": "A", "r2": "A"}},
    )
    result = score_run(packet, key, run)
    assert result["raw_points"] == 1
    assert result["max_points"] == 4
    assert result["correct_items"] == 0
    assert result["missing_items"] == 2
    assert result["invalid_items"] == 0
    matching = result["items"][1]
    assert matching["points"] == 1
    assert matching["rows"][0]["correct"] is True
    assert matching["rows"][0]["duplicate"] is True
    assert matching["rows"][1]["correct"] is False
    assert matching["rows"][1]["duplicate"] is True


def test_missing_invalid_and_failed_trials_are_explicit() -> None:
    packet, key = _prepared()
    run = _run(
        packet,
        condition="closed-book",
        responses={"q0001": None, "q0002": {"r1": "A"}, "q0003": "not-an-option"},
    )
    result = score_run(packet, key, run)
    assert result["raw_points"] == 1
    assert result["missing_items"] == 1
    assert result["invalid_items"] == 1
    assert result["items"][2]["outcome"] == "invalid"

    failed = score_run(packet, key, _run(packet, condition="closed-book", status="failed"))
    assert failed["denominator"] == {"items": 3, "points": 4}
    for field in ("raw_points", "max_points", "correct_items", "missing_items", "invalid_items", "passed"):
        assert failed[field] is None
    assert all(item["points"] is None for item in failed["items"])


def test_official_pass_uses_threshold_policy_and_threshold_zero_is_valid() -> None:
    packet, key = _prepared(scoring_kind="official", threshold=0)
    result = score_run(
        packet,
        key,
        _run(
            packet,
            condition="sources",
            responses={"q0001": "A", "q0002": {"r1": "A", "r2": "B"}, "q0003": "B"},
        ),
    )
    assert result["raw_points"] == 4
    assert result["correct_items"] == 3
    assert result["passed"] is True

    no_policy = copy.deepcopy(key)
    no_policy["scoring"]["policy_url"] = None
    no_policy["key_sha256"] = digest({field: no_policy[field] for field in no_policy if field != "key_sha256"})
    assert score_run(
        packet,
        no_policy,
        _run(
            packet,
            condition="sources",
            responses={"q0001": "A", "q0002": {"r1": "A", "r2": "B"}, "q0003": "B"},
        ),
    )["passed"] is False

    partial = score_run(
        packet,
        key,
        _run(
            packet,
            condition="sources",
            responses={"q0001": "A", "q0002": {"r1": "A"}, "q0003": "invalid"},
        ),
    )
    assert partial["raw_points"] == 2
    assert partial["correct_items"] == 1
    assert partial["missing_items"] == 0
    assert partial["invalid_items"] == 1
    assert partial["passed"] is True

    threshold_three = copy.deepcopy(key)
    threshold_three["scoring"]["pass_threshold"] = 3
    threshold_three["key_sha256"] = digest(
        {field: threshold_three[field] for field in threshold_three if field != "key_sha256"}
    )
    below = score_run(
        packet,
        threshold_three,
        _run(
            packet,
            condition="sources",
            responses={"q0001": "A", "q0002": {"r1": "A"}, "q0003": "invalid"},
        ),
    )
    assert below["raw_points"] == 2
    assert below["passed"] is False


def test_compare_requires_pair_identity_and_reports_descriptive_deltas() -> None:
    packet, key = _prepared()
    control = _run(
        packet,
        condition="closed-book",
        responses={"q0001": "B", "q0002": {"r1": "A"}, "q0003": "B"},
        metrics={"tool_calls": 0, "runtime_ms": 10},
    )
    treatment = _run(
        packet,
        condition="sources",
        responses={"q0001": "A", "q0002": {"r1": "A", "r2": "B"}, "q0003": "A"},
        metrics={"tool_calls": 2, "runtime_ms": 20, "cost_usd": 0.5},
    )
    result = compare_runs(packet, key, control, treatment)
    assert result["score_delta"] == 1
    assert result["control_points"] == 2
    assert result["treatment_points"] == 3
    assert (result["wins"], result["losses"], result["ties"]) == (2, 1, 0)
    assert result["metrics"]["tool_calls"]["delta"] == 2
    assert result["metrics"]["cost_usd"] == {"control": None, "treatment": None, "delta": None}
    assert result["significance"] is None

    drifted = copy.deepcopy(treatment)
    drifted["packet_sha256"] = "0" * 64
    with pytest.raises(ExamError, match="different packet"):
        compare_runs(packet, key, control, drifted)

    mismatched = copy.deepcopy(treatment)
    mismatched["identity"]["model"] = "other-model"
    with pytest.raises(ExamError, match="identity field"):
        compare_runs(packet, key, control, mismatched)

    different_comparison = copy.deepcopy(treatment)
    different_comparison["comparison"]["prompt_sha256"] = "other"
    with pytest.raises(ExamError, match="comparison configuration"):
        compare_runs(packet, key, control, different_comparison)


def test_runner_identity_aliases_and_pair_repeat_are_accepted() -> None:
    packet, key = _prepared()
    identity = {
        "adapter": "claude",
        "requested_model": "model-v1",
        "effective_model": "model-v1",
        "requested_effort": "high",
        "effective_effort": "unknown",
    }
    control = _run(
        packet,
        condition="closed-book",
        responses={"q0001": "A", "q0002": {}, "q0003": "B"},
        identity=identity,
    )
    treatment = _run(
        packet,
        condition="sources",
        responses={"q0001": "A", "q0002": {}, "q0003": "B"},
        identity=identity,
    )
    control["repeat"] = 1
    treatment["repeat"] = 1
    result = compare_runs(packet, key, control, treatment)
    assert result["identity"] == {
        "model": "model-v1",
        "harness": "claude",
        "effective_effort": "unknown",
        "requested_model": "model-v1",
        "effective_model": "model-v1",
        "requested_effort": "high",
    }

    ok_with_reason = copy.deepcopy(control)
    ok_with_reason["failure_reason"] = "should not be accepted"
    with pytest.raises(ExamError, match="failure_reason"):
        compare_runs(packet, key, ok_with_reason, treatment)

    for field in ("requested_model", "effective_model", "requested_effort"):
        changed = copy.deepcopy(treatment)
        changed["identity"][field] = "different"
        with pytest.raises(ExamError, match="identity field"):
            compare_runs(packet, key, control, changed)


def test_strict_json_rejects_duplicates_and_nonfinite_numbers(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"outer":{"x":1,"x":2}}', encoding="utf-8")
    with pytest.raises(ExamError, match="duplicate"):
        read_json(duplicate)

    nonfinite = tmp_path / "nonfinite.json"
    nonfinite.write_text('{"value":NaN}', encoding="utf-8")
    with pytest.raises(ExamError, match="non-finite"):
        read_json(nonfinite)

    with pytest.raises(ExamError):
        canonical({"value": float("inf")})


def test_private_json_is_mode_six_hundred_and_never_overwritten(tmp_path: Path) -> None:
    path = tmp_path / "private" / "artifact.json"
    write_private_json(path, {"first": True})
    original = path.read_bytes()
    assert os.stat(path).st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        write_private_json(path, {"second": True})
    assert path.read_bytes() == original
    assert read_json(path) == {"first": True}


def test_unsupported_item_kind_and_invalid_score_shape_are_rejected() -> None:
    invalid = _exam()
    invalid["items"][0]["kind"] = "essay"
    with pytest.raises(ExamError, match="unsupported item kind"):
        prepare_exam(invalid)

    invalid = _exam()
    invalid["scoring"]["expected_points"] = 99
    with pytest.raises(ExamError, match="expected_points"):
        prepare_exam(invalid)

    invalid = _exam()
    invalid["items"][0]["question"] = " \u2003 "
    with pytest.raises(ExamError, match="question"):
        prepare_exam(invalid)
