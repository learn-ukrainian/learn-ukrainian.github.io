"""Deterministic contract tests for the hermetic Layer-B qualification scorer."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from scripts.audit import layerb_qualify

ROUTE = layerb_qualify.EffectiveRoute.from_mapping(
    {
        "family": "claude",
        "resolved_model": "sonnet-5",
        "resolved_model_version": "2026-07-11",
        "bridge_executable": "bridge --offline-recording",
        "bridge_config_sha256": "a" * 64,
        "provider_account_lane": "subscription:test",
        "tools_disabled": True,
        "tools_disabled_evidence": "bridge-config tool_mode=disabled",
    }
)


def _probes() -> list[dict[str, Any]]:
    return [
        {
            "id": f"layer-a-fail-closed-{index}",
            "passed": True,
            "serializer_window": {"candidate_id": f"layer-a-probe-{index}", "raw_window": f"probe {index}"},
        }
        for index in range(6)
    ]


def _candidate(
    raw: str,
    *,
    candidate_id: str = "candidate-1",
    canonical_source_id: str = "source-1",
    relation: str = "ENTAILS",
    role: str = "SUPPORTS",
    expected_span: tuple[int, int] | None = None,
) -> dict[str, Any]:
    end = len(raw) if expected_span is None else expected_span[1]
    start = 0 if expected_span is None else expected_span[0]
    return {
        "candidate_id": candidate_id,
        "canonical_source_id": canonical_source_id,
        "raw_output_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "expected_source_relation": relation,
        "expected_support_spans": [{"start": start, "end": end, "role": role}] if relation in layerb_qualify.DECISIVE_RELATIONS else [],
        "eligibility": "ELIGIBLE",
        "error_status": "NONE",
    }


def _case(
    case_id: str,
    raw: str,
    *,
    relation: str = "ENTAILS",
    reviewer_verdict: str = "CONFIRMED",
    decision: str = "ACCEPT",
    expected_span: tuple[int, int] | None = None,
    failure_class: str = "ALTERED_CLAIM_VALUE",
    candidates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    selected = candidates or [_candidate(raw, relation=relation, expected_span=expected_span)]
    return {
        "case_id": case_id,
        "fact_check_id": case_id,
        "expected_fact_check_decision": decision,
        "expected_aggregate_relation": relation,
        "expected_reviewer_verdict": reviewer_verdict,
        "expected_layer_a_decision": "ANCHOR",
        "failure_class": failure_class,
        "fixture_id": "module-1",
        "candidate_set_complete": True,
        "anchor_scan_complete": True,
        "candidates_by_event_output_id": {"event-1": selected},
    }


def _emission(
    case: dict[str, Any],
    raw_by_candidate: dict[str, str],
    *,
    relations: dict[str, str] | None = None,
    spans: dict[str, list[dict[str, Any]]] | None = None,
    status: str = "completed",
    confidence: str = "high",
    module_id: str = "module-1",
    call_id: str = "call-1",
    observed: dict[str, float] | None = None,
) -> dict[str, Any]:
    candidates = [candidate for values in case["candidates_by_event_output_id"].values() for candidate in values]
    relations = relations or {candidate["candidate_id"]: candidate["expected_source_relation"] for candidate in candidates}
    source_relations = []
    for candidate in candidates:
        candidate_id = candidate["candidate_id"]
        relation = relations[candidate_id]
        role = {"ENTAILS": "SUPPORTS", "CONTRADICTS": "CONTRADICTS", "EXPLICITLY_UNCERTAIN": "UNCERTAINTY"}.get(
            relation, "SUPPORTS"
        )
        source_relations.append(
            {
                "candidate_id": candidate_id,
                "relation": relation,
                "support_spans": (spans or {}).get(
                    candidate_id,
                    [{"start": 0, "end": len(raw_by_candidate[candidate_id]), "role": role}]
                    if relation in layerb_qualify.DECISIVE_RELATIONS
                    else [],
                ),
                "confidence": confidence,
                "prompt_injection_observed": False,
            }
        )
    return {
        "status": status,
        "module_id": module_id,
        "call_id": call_id,
        "observed": observed or {"prompt_tokens": 120.0, "completion_tokens": 30.0, "cost_usd": 0.01},
        "windows": [{"candidate_id": candidate_id, "raw_window": raw} for candidate_id, raw in raw_by_candidate.items()],
        "response": {
            "schema_version": "qg-layer-b-judge-output.v1",
            "fact_checks": [{"fact_check_id": case["case_id"], "source_relations": source_relations}],
        },
    }


def _run(
    main_cases: list[dict[str, Any]], probe_cases: list[dict[str, Any]], emissions: dict[str, Any], **kwargs: Any
) -> dict[str, Any]:
    return layerb_qualify.QualificationRunner(route=ROUTE, layer_a_probe_results=_probes(), **kwargs).run(
        main_labels={"cases": main_cases}, probe_labels={"cases": probe_cases}, emissions=emissions
    )


def test_per_candidate_scoring_reuses_production_aggregation_and_contradiction_can_accept() -> None:
    raw = "The expedition took 17 days."
    candidate = _candidate(raw, relation="CONTRADICTS", role="CONTRADICTS")
    case = _case(
        "gold-contradiction-accept",
        raw,
        relation="CONTRADICTS",
        reviewer_verdict="REFUTED_BY_CONTRADICTION",
        decision="ACCEPT",
        candidates=[candidate],
    )
    report = _run([], [case], {case["case_id"]: _emission(case, {candidate["candidate_id"]: raw})})

    record = report["records"][0]
    assert record["candidate_scores"] == [
        {
            "candidate_id": "candidate-1",
            "expected_source_relation": "CONTRADICTS",
            "actual_source_relation": "CONTRADICTS",
            "relation_match": True,
            "span_match": True,
            "agreement": True,
            "serialized_untrusted_window_sha256": record["candidate_scores"][0]["serialized_untrusted_window_sha256"],
        }
    ]
    assert record["actual_aggregate_relation"] == "CONTRADICTS"
    assert record["actual_final_decision"] == "ACCEPT"
    assert report["thresholds"]["unsafe_accept_ucb"]["observed_unsafe_accepts"] == 0


def test_unsafe_accept_is_decision_level_not_relation_level() -> None:
    raw = "Source supports the claim."
    case = _case(
        "unsafe-accept",
        raw,
        relation="INSUFFICIENT_CONTEXT",
        reviewer_verdict="CONFIRMED",
        decision="AUDIT",
    )
    emission = _emission(case, {"candidate-1": raw}, relations={"candidate-1": "ENTAILS"})
    report = _run([case], [], {case["case_id"]: emission})

    unsafe = report["thresholds"]["unsafe_accept_ucb"]
    assert report["records"][0]["actual_final_decision"] == "ACCEPT"
    assert unsafe["observed_unsafe_accepts"] == 1
    assert unsafe["unsafe_eligible_denominator"] == 1
    assert unsafe["status"] == "FAIL"


def test_zero_unsafe_accepts_reports_exact_ucb_and_pending_supplement() -> None:
    raw = "The record contradicts the claim."
    case = _case("safe-reject", raw, relation="CONTRADICTS", reviewer_verdict="CONFIRMED", decision="REJECT")
    report = _run([case], [], {case["case_id"]: _emission(case, {"candidate-1": raw})})

    unsafe = report["thresholds"]["unsafe_accept_ucb"]
    assert unsafe["observed_unsafe_accepts"] == 0
    assert unsafe["one_sided_95_clopper_pearson_upper"] == pytest.approx(0.95)
    assert unsafe["status"] == "PASS_PENDING_SUPPLEMENT"
    assert layerb_qualify.clopper_pearson_upper(0, 173) == pytest.approx(0.01716, abs=0.00001)


def test_decisive_span_requires_role_matched_critical_coverage() -> None:
    raw = "alpha beta"
    case = _case("span-overlap-fail", raw, expected_span=(0, 5))
    emission = _emission(
        case,
        {"candidate-1": raw},
        spans={"candidate-1": [{"start": 6, "end": 10, "role": "SUPPORTS"}]},
    )
    report = _run([case], [], {case["case_id"]: emission})

    candidate_score = report["records"][0]["candidate_scores"][0]
    assert candidate_score["relation_match"] is True
    assert candidate_score["span_match"] is False
    assert candidate_score["agreement"] is False
    assert report["thresholds"]["relation_agreement"]["status"] == "FAIL"
    assert "SPAN_GOLD_OVERLAP_FAILURE" in report["thresholds"]["integrity"]["failures"]


def test_invalid_or_hash_mismatched_rows_fail_without_leaving_a_denominator() -> None:
    raw = "immutable evidence"
    invalid = _case("invalid-anchor", raw)
    invalid["candidate_set_complete"] = False
    hash_mismatch = _case("hash-mismatch", raw)
    mismatch_emission = _emission(hash_mismatch, {"candidate-1": "different bytes"})
    report = _run([invalid, hash_mismatch], [], {hash_mismatch["case_id"]: mismatch_emission})

    assert len(report["records"]) == 2
    assert all(record["hard_failure"] for record in report["records"])
    assert report["records"][0]["agreement_weight"] == 1
    assert "WINDOW_HASH_INTEGRITY_FAILURE" in report["records"][1]["integrity_failures"]
    assert report["thresholds"]["integrity"]["status"] == "FAIL"


@pytest.mark.parametrize("status,confidence", [("timeout", "high"), ("completed", "low")])
def test_timeout_malformed_or_low_confidence_are_hard_qualification_failures(status: str, confidence: str) -> None:
    raw = "The source supports the claim."
    case = _case("hard-failure", raw)
    emission = _emission(case, {"candidate-1": raw}, status=status, confidence=confidence)
    report = _run([case], [], {case["case_id"]: emission})

    record = report["records"][0]
    assert record["hard_failure"] is True
    assert record["actual_final_decision"] == "AUDIT"
    assert record["agreement_successes"] == 0
    assert report["thresholds"]["audit_rate"]["overall"]["audits"] == 1


def test_probe_first_aborts_without_scoring_main_rows() -> None:
    raw = "Probe source."
    probe = _case("probe-first-failure", raw)
    main = _case("main-must-not-run", raw)
    bad_probe = _emission(probe, {"candidate-1": raw}, relations={"candidate-1": "CONTRADICTS"})
    report = _run([main], [probe], {probe["case_id"]: bad_probe})

    assert report["verdict"] == "ABORTED"
    assert report["aborted_reason"] == "PROBE_FAILURE:probe-first-failure"
    assert report["run_order"]["main_cases_processed"] == 0
    assert [record["case_id"] for record in report["records"]] == [probe["case_id"]]


def test_call_cap_must_exactly_cover_main_plus_probe_rows() -> None:
    raw = "one"
    main = _case("main", raw)
    probe = _case("probe", raw)
    with pytest.raises(layerb_qualify.QualificationAbort, match="must equal 2"):
        _run([main], [probe], {}, max_judge_calls=1)


def test_six_layer_a_fail_closed_probes_are_serialized_by_production_delimiter() -> None:
    raw = "serializer source"
    case = _case("serializer-case", raw)
    report = _run([case], [], {case["case_id"]: _emission(case, {"candidate-1": raw})})

    layer_a = report["thresholds"]["layer_a_regression"]
    assert layer_a["status"] == "PASS"
    assert len(layer_a["serializer_window_sha256"]) == 6
    assert not layer_a["serializer_errors"]


def test_cost_envelopes_use_module_call_grouping_and_p95() -> None:
    raw = "cost source"
    first = _case("cost-one", raw)
    second = _case("cost-two", raw)
    first_emission = _emission(
        first,
        {"candidate-1": raw},
        module_id="module-one",
        call_id="call-one",
        observed={"prompt_tokens": 10_001.0, "completion_tokens": 20.0, "cost_usd": 0.05},
    )
    second_emission = _emission(
        second,
        {"candidate-1": raw},
        module_id="module-two",
        call_id="call-two",
        observed={"prompt_tokens": 10.0, "completion_tokens": 20.0, "cost_usd": 0.23},
    )
    first["fixture_id"] = "module-one"
    second["fixture_id"] = "module-two"
    report = _run([first, second], [], {first["case_id"]: first_emission, second["case_id"]: second_emission})

    cost = report["thresholds"]["cost_envelope"]
    assert cost["status"] == "FAIL"
    assert cost["p95_cost_usd"] == pytest.approx(0.23)
    assert any(not module["within_envelope"] for module in cost["modules"])


def test_fixed_stability_subset_replay_rejects_any_relation_disagreement() -> None:
    raw = "stable source"
    probe = _case("stability-probe", raw, failure_class="PROMPT_INJECTION")
    probe["probe_class"] = "prompt-injection"
    main_cases = [_case(f"stability-{index}", raw, failure_class="MEANING_INVERSION") for index in range(40)]
    emissions: dict[str, Any] = {}
    for index, case in enumerate([probe, *main_cases]):
        case["fixture_id"] = f"module-{index}"
        first = _emission(
            case,
            {"candidate-1": raw},
            module_id=f"module-{index}",
            call_id=f"call-{index}",
        )
        second = _emission(
            case,
            {"candidate-1": raw},
            relations={"candidate-1": "CONTRADICTS"} if case is not probe else None,
            module_id=f"module-{index}",
            call_id=f"call-{index}",
        )
        emissions[case["case_id"]] = [first, second]

    report = _run(main_cases, [probe], emissions)

    stability = report["thresholds"]["semantic_stability"]
    assert stability["required"] is True
    assert len(stability["case_ids"]) == 40
    assert stability["status"] == "FAIL"
    assert stability["disagreements"]


def test_route_matrix_is_lineage_aware_and_gpt_v21_is_not_deferred() -> None:
    deepseek = _case("openrouter-deepseek-deepseek-v4-pro__row", "raw")
    gemma = _case("openrouter-google-gemma-4-31b-it__row", "raw")
    gemini = layerb_qualify.EffectiveRoute.from_mapping({**ROUTE.to_dict(), "family": "gemini"})
    gpt = layerb_qualify.EffectiveRoute.from_mapping({**ROUTE.to_dict(), "family": "gpt"})

    assert layerb_qualify.route_eligibility(deepseek, gemini)["eligible"] is True
    assert layerb_qualify.route_eligibility(gemma, gemini)["reason"] == "GEMINI_SAME_VENDOR_REVIEWER_EXCLUDED"
    assert layerb_qualify.route_eligibility(gemma, gpt)["eligible"] is True


def test_attestation_round_trip_and_serializer_drift_refuses(tmp_path: Path) -> None:
    labels = tmp_path / "labels.json"
    corpus_manifest = tmp_path / "corpus.json"
    fixture_manifest = tmp_path / "fixture.json"
    labels.write_text(json.dumps({"cases": []}), encoding="utf-8")
    corpus_manifest.write_text(json.dumps({"corpus": "frozen"}), encoding="utf-8")
    fixture_manifest.write_text(json.dumps({"fixture": "frozen"}), encoding="utf-8")
    report_path = tmp_path / "qualification-report.json"
    report = {
        "verdict": "PASS",
        "effective_route": ROUTE.to_dict(),
        "human_audit_of_new_accepts": {"complete": True},
        "row_eligibility_matrix": [{"case_id": "row", "reason": "ELIGIBLE", "eligible": True}],
        "raw_call_manifest": [{"case_id": "row", "raw": "recorded"}],
    }
    report_path.write_text(json.dumps(report, sort_keys=True), encoding="utf-8")
    raw_manifest_path = tmp_path / "raw-call-manifest.json"
    raw_manifest_path.write_text(json.dumps(report["raw_call_manifest"], sort_keys=True), encoding="utf-8")
    attestation = layerb_qualify.create_attestation(
        report_path=report_path,
        raw_call_manifest_path=raw_manifest_path,
        labels_path=labels,
        corpus_manifests=[corpus_manifest],
        fixture_manifests=[fixture_manifest],
        expires_at=datetime.now(UTC) + timedelta(days=1),
        require_frozen_main_hash=False,
    )
    attestation_path = tmp_path / "qualification-attestation.json"
    attestation_path.write_text(json.dumps(attestation, sort_keys=True), encoding="utf-8")

    assert layerb_qualify.verify_attestation(
        attestation_path=attestation_path,
        report_path=report_path,
        raw_call_manifest_path=raw_manifest_path,
        labels_path=labels,
        corpus_manifests=[corpus_manifest],
        fixture_manifests=[fixture_manifest],
    )["verified"] is True

    attestation["production_logic_hashes"]["serializer_logic_sha256"] = "0" * 64
    attestation_path.write_text(json.dumps(attestation, sort_keys=True), encoding="utf-8")
    with pytest.raises(layerb_qualify.AttestationError, match="serializer"):
        layerb_qualify.verify_attestation(
            attestation_path=attestation_path,
            report_path=report_path,
            raw_call_manifest_path=raw_manifest_path,
            labels_path=labels,
            corpus_manifests=[corpus_manifest],
            fixture_manifests=[fixture_manifest],
        )

    attestation = layerb_qualify.create_attestation(
        report_path=report_path,
        raw_call_manifest_path=raw_manifest_path,
        labels_path=labels,
        corpus_manifests=[corpus_manifest],
        fixture_manifests=[fixture_manifest],
        expires_at=datetime.now(UTC) + timedelta(days=1),
        require_frozen_main_hash=False,
    )
    attestation["effective_route"]["tools_disabled"] = False
    attestation_path.write_text(json.dumps(attestation, sort_keys=True), encoding="utf-8")
    with pytest.raises(layerb_qualify.QualificationError, match="tool-disabled"):
        layerb_qualify.verify_attestation(
            attestation_path=attestation_path,
            report_path=report_path,
            raw_call_manifest_path=raw_manifest_path,
            labels_path=labels,
            corpus_manifests=[corpus_manifest],
            fixture_manifests=[fixture_manifest],
        )
