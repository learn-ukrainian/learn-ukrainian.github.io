"""Hermetic tests for the Phase 3 university source-admission gate."""

from __future__ import annotations

import copy

import pytest

from scripts.projects.open_model_data import phase3_university_source_admission as admission


def _decision(source_id: str) -> dict[str, object]:
    return {
        "source_id": source_id,
        "final_disposition": "needs_more_evidence",
        "source_state": "db_resident" if source_id in admission.DB_RESIDENT_IDS else "staged_not_ingested",
        "audience_class": "A_ukrainian_university_audience",
        "allowed_lanes": [],
        "orthography_regime": "post_2019",
        "rights_capability": "cc_by_4_0",
        "primary_source_roles": ["explicit_rule"],
        "claim_types": ["unresolved"],
        "supported_uses": [],
        "prohibited_uses": ["all_production_use_before_exact_evidence"],
        "exactness_status": "insufficient",
        "evidence_hashes": ["a" * 64],
        "missing_evidence": ["exact_source_level_admission_evidence"],
        "reason": "The source remains default-deny until the named evidence exists.",
    }


def _review() -> dict[str, object]:
    return {
        "schema_version": "phase3_v3_final_source_admission_review_v1",
        "reviewer_identity": "controller_phase3_ukrainian_reviewer_01",
        "role": "ukrainian_source_reviewer",
        "verified_inputs": {**admission.EXPECTED_INPUT_HASHES, "prior_reviews_verified": True},
        "denominator": list(admission.SOURCE_IDS),
        "decisions": [_decision(source_id) for source_id in admission.SOURCE_IDS],
        "findings": [],
        "complete_residuals": ["complete source freeze remains separate"],
        "review_disposition": "APPROVE_POLICY_GENERATION",
        "policy_generation_authorized": True,
        "database_ingest_authorized": False,
        "source_freeze_authorized": False,
        "phase3_complete": False,
        "phase4_blocked": True,
    }


def _scope_review() -> dict[str, object]:
    topic_matrix = []
    for area in admission.TOPIC_AREAS:
        topic_matrix.append(
            {
                "area": area,
                "status": "partial",
                "bounded_scope": "Only the exact reviewed source scope receives credit.",
                "supporting_source_ids": [admission.SOURCE_IDS[0]],
                "residual": "A complete source-family depth proof remains open.",
            }
        )
    return {
        "schema_version": "phase3_university_source_scope_review_v1",
        "reviewer_identity": "controller_phase3_scope_critic_01",
        "role": "scope_circularity_critic",
        "verified_inputs": admission.EXPECTED_SCOPE_INPUT_HASHES,
        "source_set_check": {
            "total_unique_sources": 30,
            "admit_scoped_count": 11,
            "contextual_only_count": 15,
            "quarantine_count": 4,
            "no_extras": True,
            "no_omissions": True,
            "no_duplicate_credit": True,
            "quarantines_preserved": True,
        },
        "source_disposition_corrections": [],
        "topic_matrix": topic_matrix,
        "topic_counts": {"sufficient": 0, "partial": 26, "missing": 0, "total": 26},
        "rights_and_exactness_residuals": [],
        "findings": [],
        "complete_residuals": ["database ingest and the complete freeze remain separate"],
        "matrix_disposition": "APPROVE_ADMISSION_MATRIX",
        "source_admission_matrix_ready": True,
        "database_ingest_authorized": False,
        "source_freeze_authorized": False,
        "phase3_complete": False,
        "phase4_blocked": True,
    }


def _source_matrix() -> dict[str, object]:
    rows = [
        *({"source_id": source_id, "disposition": "admit_candidate"} for source_id in admission.SOURCE_IDS),
        *(
            {"source_id": source_id, "disposition": "contextual_only"}
            for source_id in sorted(admission.CONTEXTUAL_ONLY_IDS)
        ),
        *({"source_id": source_id, "disposition": "quarantine"} for source_id in sorted(admission.QUARANTINE_IDS)),
    ]
    return {
        "schema_version": "phase3-university-source-matrix-consolidated.v3",
        "text_free": True,
        "source_disposition_counts": {
            "admit_candidate": 11,
            "contextual_only": 15,
            "quarantine": 4,
            "total_unique_sources": 30,
        },
        "source_dispositions": rows,
    }


def _transport() -> dict[str, object]:
    return {
        "ukrainian_review": {
            "task_id": "phase3-v3-final-source-admission-review-20-correction",
            "normalized_status": "failed_metadata_only",
            "exit_code": 0,
            "raw_result_sha256": admission.EXPECTED_SCOPE_INPUT_HASHES["university_source_admission_review_sha256"],
            "semantic_result_sha256": admission.EXPECTED_SCOPE_INPUT_HASHES[
                "university_source_admission_review_sha256"
            ],
            "normalization": "direct_json",
            "metadata_only_mutation_paths": [".agent/sessions/reviewer.json"],
        },
        "scope_review": {
            "task_id": "phase3-v3-university-source-scope-review-21",
            "normalized_status": "done",
            "exit_code": 0,
            "raw_result_sha256": "c" * 64,
            "semantic_result_sha256": "c" * 64,
            "normalization": "direct_json",
            "metadata_only_mutation_paths": [],
        },
    }


def test_valid_exact_denominator_builds_deterministic_text_free_gate() -> None:
    review = _review()
    scope_review = _scope_review()
    first = admission.build_gate(
        review,
        scope_review,
        _source_matrix(),
        review_sha256=admission.EXPECTED_SCOPE_INPUT_HASHES["university_source_admission_review_sha256"],
        scope_review_sha256="c" * 64,
        transport=_transport(),
    )
    second = admission.build_gate(
        copy.deepcopy(review),
        copy.deepcopy(scope_review),
        copy.deepcopy(_source_matrix()),
        review_sha256=admission.EXPECTED_SCOPE_INPUT_HASHES["university_source_admission_review_sha256"],
        scope_review_sha256="c" * 64,
        transport=copy.deepcopy(_transport()),
    )
    assert first == second
    assert first["denominator_count"] == 11
    assert first["disposition_counts"] == {
        "admit_scoped": 0,
        "contextual_only": 0,
        "quarantine": 0,
        "needs_more_evidence": 11,
    }
    assert first["policy_generation_ready"] is True
    assert first["scope_review_ready"] is True
    assert first["topic_counts"]["total"] == 26
    assert first["scope_review_finding_counts"] == {"material": 0, "minor": 0}
    assert first["complete_residual_count"] == 1
    assert first["database_ingest_authorized"] is False
    assert first["source_freeze_ready"] is False
    assert first["phase4_blocked"] is True
    assert "reason" not in first["decisions"][0]


def test_missing_or_reordered_source_fails_closed() -> None:
    review = _review()
    review["denominator"][0], review["denominator"][1] = review["denominator"][1], review["denominator"][0]
    with pytest.raises(admission.SourceAdmissionError, match="exact sorted 11-source"):
        admission.validate_review(review)


def test_source_state_drift_fails_closed() -> None:
    review = _review()
    review["decisions"][0]["source_state"] = "db_resident"
    with pytest.raises(admission.SourceAdmissionError, match="source-state drift"):
        admission.validate_review(review)


def test_blocked_source_cannot_enter_production_lane() -> None:
    review = _review()
    review["decisions"][0]["allowed_lanes"] = ["contextual_retrieval"]
    with pytest.raises(admission.SourceAdmissionError, match="blocked source cannot enter"):
        admission.validate_review(review)


def test_rule_evidence_requires_explicit_rule_role_and_verified_exactness() -> None:
    review = _review()
    decision = review["decisions"][0]
    decision.update(
        {
            "final_disposition": "admit_scoped",
            "allowed_lanes": ["contextual_retrieval", "corpus_ingest", "linguistic_rule_evidence"],
            "exactness_status": "verified_for_scoped_use",
            "missing_evidence": [],
            "primary_source_roles": ["ordinary_narration"],
        }
    )
    with pytest.raises(admission.SourceAdmissionError, match="explicit-rule role"):
        admission.validate_review(review)


def test_pre_2019_admission_requires_current_orthography_restriction() -> None:
    review = _review()
    decision = review["decisions"][2]
    decision.update(
        {
            "final_disposition": "admit_scoped",
            "allowed_lanes": ["contextual_retrieval", "corpus_ingest", "linguistic_rule_evidence"],
            "orthography_regime": "pre_2019",
            "exactness_status": "verified_for_scoped_use",
            "missing_evidence": [],
            "prohibited_uses": ["unrelated_restriction"],
        }
    )
    with pytest.raises(admission.SourceAdmissionError, match="post-2019 authority restriction"):
        admission.validate_review(review)


def test_pre_2019_restriction_rejects_descriptive_marker_sentence() -> None:
    review = _review()
    decision = review["decisions"][2]
    decision.update(
        {
            "final_disposition": "admit_scoped",
            "allowed_lanes": ["contextual_retrieval", "corpus_ingest", "linguistic_rule_evidence"],
            "orthography_regime": "pre_2019",
            "exactness_status": "verified_for_scoped_use",
            "missing_evidence": [],
            "prohibited_uses": ["discusses_commercial_trends_after_post_2019"],
        }
    )
    with pytest.raises(admission.SourceAdmissionError, match="post-2019 authority restriction"):
        admission.validate_review(review)


def test_noncommercial_rights_cannot_lose_commercial_restriction() -> None:
    review = _review()
    decision = review["decisions"][0]
    decision["rights_capability"] = "cc_by_nc_4_0_noncommercial_only"
    decision["prohibited_uses"] = ["automatic_admission"]
    with pytest.raises(admission.SourceAdmissionError, match="non-commercial rights restriction"):
        admission.validate_review(review)


def test_noncommercial_restriction_rejects_uncontrolled_commercial_marker() -> None:
    review = _review()
    decision = review["decisions"][0]
    decision["rights_capability"] = "cc_by_nc_4_0_noncommercial_only"
    decision["prohibited_uses"] = ["commercial_topic_context"]
    with pytest.raises(admission.SourceAdmissionError, match="non-commercial rights restriction"):
        admission.validate_review(review)


def test_gate_metadata_fields_reject_free_form_source_text() -> None:
    review = _review()
    review["decisions"][0]["supported_uses"] = ["verbatim source passage"]
    with pytest.raises(admission.SourceAdmissionError, match="schema violation"):
        admission.validate_review(review)


def test_review_input_hash_drift_fails_closed() -> None:
    review = _review()
    review["verified_inputs"]["university_source_matrix_v3_sha256"] = "0" * 64
    with pytest.raises(admission.SourceAdmissionError, match="input hashes"):
        admission.validate_review(review)


def test_policy_generation_boolean_must_match_disposition() -> None:
    review = _review()
    review["review_disposition"] = "CHANGES_REQUIRED"
    with pytest.raises(admission.SourceAdmissionError, match="policy authorization disagree"):
        admission.validate_review(review)


def test_scope_review_rejects_quarantine_coverage_credit() -> None:
    review = _scope_review()
    review["topic_matrix"][0]["supporting_source_ids"] = [next(iter(admission.QUARANTINE_IDS))]
    with pytest.raises(admission.SourceAdmissionError, match="quarantined source"):
        admission.validate_scope_review(review, _source_matrix())


def test_scope_review_requires_exact_26_area_order() -> None:
    review = _scope_review()
    review["topic_matrix"][0], review["topic_matrix"][1] = review["topic_matrix"][1], review["topic_matrix"][0]
    with pytest.raises(admission.SourceAdmissionError, match="exact ordered 26-area"):
        admission.validate_scope_review(review, _source_matrix())


def test_scope_review_source_set_facts_are_derived_from_matrix_rows() -> None:
    review = _scope_review()
    review["source_set_check"]["no_extras"] = False
    with pytest.raises(admission.SourceAdmissionError, match="source-set facts"):
        admission.validate_scope_review(review, _source_matrix())


def test_negative_scope_review_can_encode_a_matrix_extra() -> None:
    matrix = _source_matrix()
    matrix["source_dispositions"].append({"source_id": "unexpected-source", "disposition": "contextual_only"})
    matrix["source_disposition_counts"].update({"contextual_only": 16, "total_unique_sources": 31})
    review = _scope_review()
    review["source_set_check"].update({"total_unique_sources": 31, "contextual_only_count": 16, "no_extras": False})
    review["matrix_disposition"] = "CHANGES_REQUIRED"
    review["source_admission_matrix_ready"] = False
    assert admission.validate_scope_review(review, matrix)["source_set_check"]["no_extras"] is False


def test_approved_scope_review_rejects_swapped_disposition_groups() -> None:
    matrix = _source_matrix()
    candidate = next(row for row in matrix["source_dispositions"] if row["disposition"] == "admit_candidate")
    contextual = next(row for row in matrix["source_dispositions"] if row["disposition"] == "contextual_only")
    candidate["disposition"], contextual["disposition"] = contextual["disposition"], candidate["disposition"]
    with pytest.raises(admission.SourceAdmissionError, match="wrong disposition group"):
        admission.validate_scope_review(_scope_review(), matrix)


def test_approved_scope_review_can_report_findings_applied_to_final_matrix() -> None:
    review = _scope_review()
    review["findings"] = [
        {
            "severity": "material",
            "finding": "A material circularity defect remains.",
            "required_action": "Correct the matrix.",
        }
    ]
    assert admission.validate_scope_review(review, _source_matrix())["findings"] == review["findings"]


def test_dispatch_transport_accepts_only_known_ignored_metadata_leak(tmp_path) -> None:
    result = tmp_path / "review.result"
    result.write_text("{}", encoding="utf-8")
    state = {
        "task_id": "review-task",
        "status": "failed",
        "exit_code": 0,
        "result_file": str(result),
        "last_error": "read-only checkout mutation detected: .agent/sessions/review.json",
        "read_only_mutation_paths": [".agent/sessions/review.json", ".entire/metadata/review/prompt.txt"],
    }
    receipt = admission.validate_dispatch_transport(
        state,
        expected_task_id="review-task",
        result_path=result,
        raw_result_sha256=admission.sha256_file(result),
        semantic_result_sha256=admission.sha256_file(result),
        normalization="direct_json",
    )
    assert receipt["normalized_status"] == "failed_metadata_only"


def test_dispatch_transport_rejects_non_metadata_mutation(tmp_path) -> None:
    result = tmp_path / "review.result"
    result.write_text("{}", encoding="utf-8")
    state = {
        "task_id": "review-task",
        "status": "failed",
        "exit_code": 0,
        "result_file": str(result),
        "last_error": "read-only checkout mutation detected: source.py",
        "read_only_mutation_paths": ["source.py"],
    }
    with pytest.raises(admission.SourceAdmissionError, match="non-metadata path"):
        admission.validate_dispatch_transport(
            state,
            expected_task_id="review-task",
            result_path=result,
            raw_result_sha256=admission.sha256_file(result),
            semantic_result_sha256=admission.sha256_file(result),
            normalization="direct_json",
        )


def test_review_result_strips_only_one_non_json_prefix(tmp_path) -> None:
    result = tmp_path / "review.result"
    result.write_text('progress note\n{"ok":true}', encoding="utf-8")
    value, raw_sha256, semantic_sha256, normalization = admission.read_review_result(result)
    assert value == {"ok": True}
    assert raw_sha256 != semantic_sha256
    assert normalization == "stripped_non_json_prefix"


def test_review_result_rejects_trailing_commentary(tmp_path) -> None:
    result = tmp_path / "review.result"
    result.write_text('{"ok":true}\ntrailing note', encoding="utf-8")
    with pytest.raises(admission.SourceAdmissionError, match="no recoverable JSON"):
        admission.read_review_result(result)


def test_review_result_rejects_prefix_with_earlier_json_opener(tmp_path) -> None:
    result = tmp_path / "review.result"
    result.write_text('progress {not json}\n{"ok":true}', encoding="utf-8")
    with pytest.raises(admission.SourceAdmissionError, match="payload is malformed"):
        admission.read_review_result(result)


def test_atomic_receipt_write_replaces_complete_file(tmp_path) -> None:
    output = tmp_path / "nested" / "gate.json"
    admission.write_text_atomic(output, "first\n")
    admission.write_text_atomic(output, "second\n")
    assert output.read_text(encoding="utf-8") == "second\n"
    assert not list(output.parent.glob(".gate.json.*.tmp"))
