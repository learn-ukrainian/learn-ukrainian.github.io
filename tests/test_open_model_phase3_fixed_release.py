"""Focused closure proof for the Phase 3 fixed-release opening point."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_disposition_audit as audit
from scripts.projects.open_model_data import phase3_evaluation_freeze as freeze
from scripts.projects.open_model_data import phase3_fixed_release as release


def _write(path: Path, value: object, *, private: bool = False) -> Path:
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    if private:
        os.chmod(path, 0o600)
    return path


def _hash() -> str:
    return "a" * 64


def _release_inputs(tmp_path: Path) -> dict[str, Path]:
    artifacts = tmp_path / "reviewed-rule-artifacts.jsonl"
    artifact = {"rule_id": "rule.fixture", "predicate": "fixture"}
    artifacts.write_text(
        json.dumps({"unit_id": "unit.fixture", "unit_sha256": _hash(), "artifact_sha256": release.sha256_value(artifact), "artifact": artifact, "consumer_views": [{"view_id": "fixture"}]}) + "\n",
        encoding="utf-8",
    )
    ledger = _write(tmp_path / "ledger.json", {"schema_version": "phase3_disposition_ledger_v2_1", "text_free": True})
    disposition = _write(tmp_path / "disposition.json", {"schema_version": "phase3_source_disposition_receipt_v2_1", "disposition_ledger": {"row_count": 67041}})
    audit_bundle = {
        "schema_version": "phase3_disposition_audit_bundle_v2_1", "text_free": True,
        "source_universe_receipt_sha256": _hash(), "coverage_contract_sha256": _hash(),
        "base_contract_sha256": release.roles.BASE_SHA256, "amendment_sha256": release.roles.AMENDMENT_SHA256,
        "combined_contract_sha256": release.roles.COMBINED_SHA256,
        "functional_role_contract_sha256": _hash(), "conflict_graph_sha256": _hash(),
        "disposition_ledger_sha256": audit.sha256_value(json.loads(ledger.read_text(encoding="utf-8"))),
        "population_freeze_sha256": _hash(), "seed_receipt_sha256s": [_hash()], "sample_manifest_sha256": _hash(), "audit_results_sha256": _hash(),
    }
    heldout = _write(tmp_path / "heldout.json", {"schema_version": "phase3_heldout_label_public_receipt_v1", "complete": True, "row_count": 2000})
    freeze_receipt = _write(tmp_path / "freeze.json", {"schema_version": "phase3_evaluation_partition_receipt_v1", "aggregates": {"clean_modern_candidate_total": 2000}, "input_bindings": {"evaluation_cycle_id": release.EVALUATION_CYCLE_ID}})
    comprehensive = {
        "schema_version": "phase3_comprehensive_sealed_label_bundle_v1", "text_free": True,
        "evaluation_cycle_id": release.EVALUATION_CYCLE_ID,
        "evaluation_freeze_receipt_sha256": release.sha256_file(freeze_receipt),
        "partition_manifest_sha256": _hash(), "sealed_labels_sha256": _hash(),
        "row_count": 9392, "clean_modern_row_count": 2000, "phenomenon_strata_row_count": 7392,
        "phenomenon_stratum_commitments": {name: _hash() for name in freeze.PHENOMENA},
        "complete": True, "frozen_before_rule_extraction": True,
    }
    comprehensive["receipt_sha256"] = release.sha256_value(comprehensive)
    comprehensive_path = _write(tmp_path / "comprehensive-label-bundle.json", comprehensive)
    public = _write(tmp_path / "public.json", {"schema_version": "phase3_source_production_public_receipt_v1", "review_complete": True, "denominator": {"input_total": 67041}, "reviewed_rule_artifacts_sha256": release.sha256_file(artifacts), "author_manifest_comprehensive_sealed_label_bundle_sha256": release.sha256_file(comprehensive_path)})
    return {
        "reviewed_rule_artifacts_path": artifacts,
        "source_production_public_receipt_path": public,
        "disposition_ledger_path": ledger,
        "disposition_receipt_path": disposition,
        "disposition_audit_bundle_path": _write(tmp_path / "audit.json", audit_bundle),
        "heldout_label_public_receipt_path": heldout,
        "comprehensive_sealed_label_bundle_path": comprehensive_path,
        "evaluation_freeze_receipt_path": freeze_receipt,
        "denominator_contract_path": _write(tmp_path / "denominator.json", {"kind": "denominator"}),
        "threshold_contract_path": _write(tmp_path / "threshold.json", {"kind": "threshold"}),
    }


def test_fixed_release_rehashes_all_artifacts_and_rejects_mutation(tmp_path: Path) -> None:
    manifest = release.build(**_release_inputs(tmp_path), output_dir=tmp_path / "release")
    assert manifest["denominator"] == {
        "source_disposition_total": 67041,
        "sealed_evaluation_total": 9392,
        "sealed_clean_modern_total": 2000,
        "sealed_phenomenon_strata_total": 7392,
    }
    assert manifest["gates"]["heldout_labels_complete"] is True
    assert manifest["gates"]["heldout_plaintext_published"] is False
    manifest_path = tmp_path / "release" / "fixed-release-manifest.json"
    assert release.validate_manifest(manifest_path)["manifest_sha256"] == manifest["manifest_sha256"]
    (tmp_path / "release" / "fixed-release-rules.jsonl").write_text("mutated\n", encoding="utf-8")
    with pytest.raises(release.FixedReleaseError, match="artifact hash drift"):
        release.validate_manifest(manifest_path)


def test_fixed_release_uses_the_audit_hash_domain_and_rejects_release_newline_hash(tmp_path: Path) -> None:
    inputs = _release_inputs(tmp_path)
    ledger = json.loads(inputs["disposition_ledger_path"].read_text(encoding="utf-8"))
    assert audit.sha256_value(ledger) != release.sha256_value(ledger)
    release.build(**inputs, output_dir=tmp_path / "release")
    audit_bundle = json.loads(inputs["disposition_audit_bundle_path"].read_text(encoding="utf-8"))
    audit_bundle["disposition_ledger_sha256"] = release.sha256_value(ledger)
    _write(inputs["disposition_audit_bundle_path"], audit_bundle)
    with pytest.raises(release.FixedReleaseError, match="audit bundle disposition ledger binding drift"):
        release.build(**inputs, output_dir=tmp_path / "second-release")


def test_fixed_release_rejects_a_clean_modern_only_comprehensive_label_claim(tmp_path: Path) -> None:
    inputs = _release_inputs(tmp_path)
    bundle = json.loads(inputs["comprehensive_sealed_label_bundle_path"].read_text(encoding="utf-8"))
    bundle["row_count"] = 2000
    bundle["phenomenon_strata_row_count"] = 0
    body = dict(bundle)
    body.pop("receipt_sha256")
    bundle["receipt_sha256"] = release.sha256_value(body)
    _write(inputs["comprehensive_sealed_label_bundle_path"], bundle)
    with pytest.raises(release.FixedReleaseError, match="2,000 clean_modern plus 7,392 phenomenon"):
        release.build(**inputs, output_dir=tmp_path / "release")


def test_sealed_interface_rejects_the_incomplete_2000_row_label_lane(tmp_path: Path) -> None:
    release.build(**_release_inputs(tmp_path), output_dir=tmp_path / "release")
    labels = _write(tmp_path / "labels.json", [], private=True)
    partition = tmp_path / "partition.jsonl"
    partition.write_text("", encoding="utf-8")
    os.chmod(partition, 0o600)
    bundle = {
        "schema_version": "phase3_comprehensive_sealed_label_bundle_v1", "text_free": True,
        "evaluation_cycle_id": release.EVALUATION_CYCLE_ID,
        "evaluation_freeze_receipt_sha256": release.sha256_file(tmp_path / "freeze.json"),
        "partition_manifest_sha256": release.sha256_file(partition),
        "sealed_labels_sha256": release.sha256_file(labels),
        "row_count": 2000, "clean_modern_row_count": 2000, "phenomenon_strata_row_count": 0,
        "phenomenon_stratum_commitments": {name: _hash() for name in freeze.PHENOMENA},
        "complete": True, "frozen_before_rule_extraction": True,
    }
    bundle["receipt_sha256"] = release.sha256_value(bundle)
    bundle_path = _write(tmp_path / "labels-bundle.json", bundle)
    with pytest.raises(freeze.EvaluationFreezeError, match="2,000 clean_modern plus 7,392 phenomenon"):
        freeze.emit_sealed_interface(
            release_manifest_path=tmp_path / "release" / "fixed-release-manifest.json",
            comprehensive_sealed_label_bundle_path=bundle_path,
            sealed_labels_path=labels,
            partition_path=partition,
            source_jsonl=tmp_path / "not-read.jsonl",
            materialization_receipt_path=tmp_path / "not-read-receipt.json",
            evaluation_freeze_receipt_path=tmp_path / "freeze.json",
            private_dir=tmp_path / "private-interface",
            public_receipt_path=tmp_path / "sealed-interface-receipt.json",
            started_at="2026-08-09T00:00:00Z",
            completed_at="2026-08-09T00:00:01Z",
        )
