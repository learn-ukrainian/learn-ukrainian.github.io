"""Unit tests for independent human-source dataset quality and evaluation separation (#7431)."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from scripts.projects.open_model_data.v4_dataset_quality_evaluation import (
    assert_no_private_host_paths,
    assess_pilot_dataset,
    verify_assessment,
)


def test_quality_evaluation_schema_valid() -> None:
    repo_root = Path.cwd()
    schema_path = repo_root / "data/projects/open_model_data/contracts/v4_dataset_quality_evaluation_v1.schema.json"
    assert schema_path.exists(), "Missing schema contract"

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)


def test_eval1_denominator_and_residual_accounting() -> None:
    repo_root = Path.cwd()
    assessment = assess_pilot_dataset(repo_root)

    assert assessment["legacy_100_slot_contract_rejected"] is True
    denom = assessment["denominator_accounting"]
    assert denom["total_evaluated_spans"] == 1419
    assert denom["total_admitted_spans"] == 1418
    assert denom["exported_training_spans"] == 614
    assert denom["firewalled_heldout_evaluation_spans"] == 559
    assert denom["development_spans"] == 245
    assert denom["quarantined_spans"] == 1
    assert denom["rejected_spans"] == 0
    assert denom["abstained_spans"] == 0

    residuals = denom["operator_excluded_residuals"]
    strata_names = {r["stratum"] for r in residuals}
    assert "stem_technical_and_exact_sciences" in strata_names
    assert "video_captions_transcripts" in strata_names
    assert "ocr_scanned_unverified_sources" in strata_names
    assert "private_teaching_material" in strata_names


def test_eval2_quality_fidelity_and_split_firewall() -> None:
    repo_root = Path.cwd()
    assessment = assess_pilot_dataset(repo_root)
    q = assessment["quality_fidelity_checks"]

    assert q["verbatim_fidelity_rate"] == 1.0
    assert q["tampering_detected"] is False
    assert q["synthetic_corrections_detected"] is False
    assert q["dual_view_loss_masks_valid"] is True
    assert q["non_target_citations_masked"] is True
    assert q["vesum_sources_validated"] is True
    assert q["unattested_penalized"] is False
    assert q["no_gold_from_model_agreement"] is True
    assert q["split_firewall_cross_family_leaks"] == 0
    assert q["duplicate_spans_detected"] == 0
    assert q["benchmark_contamination_detected"] is False


def test_eval3_legitimate_use_preservation() -> None:
    repo_root = Path.cwd()
    records_path = repo_root / "data/projects/open_model_data/pilot/v4_human_source_pilot_records_v1.jsonl"
    roles = set()
    with records_path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx == 0:
                continue
            rec = json.loads(line)
            role = rec.get("language_views", {}).get("primary_role")
            roles.add(role)

    # Validates registers are preserved without synthetic modernization
    assert "literary_register" in roles or "modern_standard" in roles
    assert "damaged_or_excluded" in roles  # 1 quarantined extraction anomaly preserved honestly


def test_eval4_heldout_evaluation_protocol_and_sealed_custody() -> None:
    repo_root = Path.cwd()
    assessment = assess_pilot_dataset(repo_root)
    proto = assessment["heldout_evaluation_protocol"]

    assert proto["custody_firewall_enforced"] is True
    assert "faithful_view" in proto["consumer_views_evaluated"]
    assert "modern_view" in proto["consumer_views_evaluated"]
    assert "perplexity_faithful_view" in proto["scoring_metrics"]
    assert "perplexity_modern_view" in proto["scoring_metrics"]


def test_eval5_independent_reproduction() -> None:
    repo_root = Path.cwd()
    assessment_rel = "data/projects/open_model_data/pilot/v4_human_source_pilot_quality_assessment_v1.json"
    verified = verify_assessment(repo_root, assessment_rel=assessment_rel)
    assert verified is True

    # Check cohort findings
    assessment_path = repo_root / assessment_rel
    data = json.loads(assessment_path.read_text(encoding="utf-8"))
    cohorts = data.get("cohort_findings", [])
    assert len(cohorts) >= 2
    for c in cohorts:
        assert c["verdict"] == "PASS"
        assert c["verbatim_fidelity_confirmed"] is True
        assert c["split_firewall_confirmed"] is True


def test_eval6_downstream_study_methodology() -> None:
    repo_root = Path.cwd()
    assessment = assess_pilot_dataset(repo_root)
    methodology = assessment["downstream_study_methodology"]

    assert methodology["target_issue"] == 7889
    assert methodology["dataset_quality_verdict"] == "PASS"
    assert methodology["trained_model_utility_verdict"] == "PENDING_EXPERIMENTAL_STUDY"
    assert len(methodology["uncertainty_and_limitations"]) >= 3


def test_privacy_invariants() -> None:
    repo_root = Path.cwd()
    assessment_path = repo_root / "data/projects/open_model_data/pilot/v4_human_source_pilot_quality_assessment_v1.json"
    data = json.loads(assessment_path.read_text(encoding="utf-8"))
    assert_no_private_host_paths(data)
