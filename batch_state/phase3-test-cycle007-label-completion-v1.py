#!/usr/bin/env python3
"""Synthetic tests for Phase 3 Cycle 007 label completion verifier."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract

HERE = Path(__file__).resolve().parent
VERIFY_PATH = HERE / "phase3-verify-cycle007-label-completion-v1.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


verify_mod = _load_module(VERIFY_PATH, "verify_mod")


def _setup_certified_package(tmp_path: Path):
    pkg = tmp_path / "pkg"
    pkg.mkdir(parents=True, mode=0o700)

    # 1. Packets setup: 204 packets (40 clean, 164 residual), 10159 rows
    packets_meta = []
    ordered_identities = []

    # Clean packets (40 packets of 50 rows = 2000 rows)
    clean_dir = pkg / "clean_label"
    clean_dir.mkdir(parents=True, mode=0o700)
    for idx in range(1, 41):
        rows = [
            {
                "unit_id": f"clean.{idx}.{r}",
                "unit_sha256": verify_mod.digest(f"clean.{idx}.{r}".encode()),
                "clean_modern_standard_prose": True,
            }
            for r in range(50)
        ]
        p_p = clean_dir / f"packet-{idx:04d}.json"
        id_set = verify_mod.digest(verify_mod.canonical(sorted((r["unit_id"], r["unit_sha256"]) for r in rows)))
        p_p.write_text(json.dumps({"packet_identity_set_sha256": id_set, "rows": rows}, sort_keys=True) + "\n")
        p_p.chmod(0o600)
        packets_meta.append({
            "lane": "clean_label",
            "packet_index": idx,
            "canonical_basename": f"packet-{idx:04d}.json",
            "row_count": 50,
            "raw_sha256": verify_mod.digest(p_p.read_bytes()),
            "packet_identity_set_sha256": id_set,
        })
        for r_idx, r in enumerate(rows):
            ordered_identities.append(["clean_label", idx, r_idx, r["unit_id"], r["unit_sha256"]])

    # Residual packets (163 packets of 50 rows = 8150 + 1 packet of 9 rows = 8159 rows)
    res_dir = pkg / "residual_label"
    res_dir.mkdir(parents=True, mode=0o700)
    for idx in range(1, 165):
        count = 9 if idx == 164 else 50
        rows = [
            {
                "unit_id": f"residual.{idx}.{r}",
                "unit_sha256": verify_mod.digest(f"residual.{idx}.{r}".encode()),
                "family_id": "standard",
            }
            for r in range(count)
        ]
        p_p = res_dir / f"packet-{idx:04d}.json"
        id_set = verify_mod.digest(verify_mod.canonical(sorted((r["unit_id"], r["unit_sha256"]) for r in rows)))
        p_p.write_text(json.dumps({"packet_identity_set_sha256": id_set, "rows": rows}, sort_keys=True) + "\n")
        p_p.chmod(0o600)
        packets_meta.append({
            "lane": "residual_label",
            "packet_index": idx,
            "canonical_basename": f"packet-{idx:04d}.json",
            "row_count": count,
            "raw_sha256": verify_mod.digest(p_p.read_bytes()),
            "packet_identity_set_sha256": id_set,
        })
        for r_idx, r in enumerate(rows):
            ordered_identities.append(["residual_label", idx, r_idx, r["unit_id"], r["unit_sha256"]])

    # Commitment for fixture
    commitment = verify_mod.digest(verify_mod.canonical(ordered_identities))

    # Custody & Manifest
    custody = {
        "schema_version": "phase3_cycle007_custody_receipt_v1",
        "evaluation_cycle_id": verify_mod.CYCLE,
        "source_evaluation_cycle_id": verify_mod.SOURCE_CYCLE,
        "amendment_reference": "batch_state/phase3-cycle007-source-grounded-amendment-v1.md",
        "source_custody_receipt_raw_sha256": verify_mod.SOURCE_CUSTODY_SHA256,
        "source_label_manifest_raw_sha256": verify_mod.SOURCE_MANIFEST_SHA256,
        "ordered_identity_commitment_sha256": commitment,
        "packet_count": 204,
        "row_count": 10159,
        "lane_row_counts": {"clean_label": 2000, "residual_label": 8159},
        "packet_size": 50,
        "provider_artifacts_copied": False,
        "labels_copied": False,
        "responses_copied": False,
        "prompts_generated": False,
        "evidence_sidecars_generated": False,
        "text_free": True,
    }
    custody_p = pkg / "custody-receipt.json"
    custody_p.write_text(json.dumps(custody, sort_keys=True) + "\n")
    custody_p.chmod(0o600)
    custody_hash = verify_mod.digest(custody_p.read_bytes())

    manifest = {
        "schema_version": "phase3_cycle007_materialization_manifest_v1",
        "evaluation_cycle_id": verify_mod.CYCLE,
        "source_evaluation_cycle_id": verify_mod.SOURCE_CYCLE,
        "text_free": True,
        "custody_receipt_raw_sha256": custody_hash,
        "ordered_identity_commitment_sha256": commitment,
        "identity_union_commitment_sha256": "union_sha",
        "ordered_packet_commitment_sha256": "order_sha",
        "packet_count": 204,
        "row_count": 10159,
        "lane_row_counts": {"clean_label": 2000, "residual_label": 8159},
        "packets": packets_meta,
    }
    manifest_p = pkg / "manifest.json"
    manifest_p.write_text(json.dumps(manifest, sort_keys=True) + "\n")
    manifest_p.chmod(0o600)

    # Evidence directory
    ev_dir = pkg / "evidence"
    ev_dir.mkdir(parents=True, mode=0o700)

    sidecar_meta = []
    for p_meta in packets_meta:
        lane = p_meta["lane"]
        idx = p_meta["packet_index"]
        count = p_meta["row_count"]
        global_idx = idx if lane == "clean_label" else 40 + idx

        rows_ev = []
        retrieval_payload = {"data": "evidence"}
        r_sha = contract.sha256_value(retrieval_payload)
        retrieval_payloads = {r_sha: retrieval_payload}

        for r_num in range(count):
            u_id = f"{'clean' if lane == 'clean_label' else 'residual'}.{idx}.{r_num}"
            u_sha = verify_mod.digest(u_id.encode("utf-8"))
            row_dict = {"unit_id": u_id, "unit_sha256": u_sha}
            rec = contract.build_evidence_record(
                channel="vesum_attestation",
                source_identity="vesum",
                source_version="v1",
                locator="data/vesum.db",
                query="query",
                status="attested",
                supports="attestation",
                retrieval_sha256=r_sha,
                parser_id="p1",
                parser_version="1",
                row=row_dict,
                phenomenon_id=None if lane == "clean_label" else "apostrophe",
            )
            phenom_map = {p: [] for p in contract.RESIDUAL_PHENOMENON_TAXONOMY} if lane == "residual_label" else {}
            if lane == "residual_label":
                phenom_map["apostrophe"] = [rec["evidence_id"]]
            rows_ev.append({
                "unit_id": u_id,
                "unit_sha256": u_sha,
                "evidence": [rec],
                "evidence_ids": [rec["evidence_id"]],
                "phenomenon_evidence_ids": phenom_map,
                "sufficient_support": True,
                "archaic_only_risk": False,
                "russian_shadow_suspected": False,
            })

        sidecar = {
            "schema_version": "phase3_cycle007_evidence_sidecar_v1",
            "evaluation_cycle_id": verify_mod.CYCLE,
            "lane": lane,
            "packet_binding": {
                "canonical_basename": p_meta["canonical_basename"],
                "raw_sha256": p_meta["raw_sha256"],
                "packet_identity_set_sha256": p_meta["packet_identity_set_sha256"],
            },
            "packet_index": global_idx,
            "row_count": count,
            "tokenizer_id": "phase3-cycle007-cyrillic-tokenizer-v1",
            "tokenizer_version": "1",
            "code_hashes": {"compiler_id": "c1"},
            "server_code_sha256": "srv",
            "sources_db_sha256": "src",
            "vesum_db_sha256": "vsm",
            "network_lookups_performed": 0,
            "rows": rows_ev,
            "retrieval_payloads": retrieval_payloads,
        }
        sidecar["sidecar_id"] = "cycle007_sidecar:" + contract.sha256_value(sidecar)
        s_p = ev_dir / f"sidecar-{global_idx:04d}.json"
        s_p.write_text(json.dumps(sidecar, sort_keys=True) + "\n")
        s_p.chmod(0o600)

        sidecar_meta.append({
            "packet_index": global_idx,
            "row_count": count,
            "sidecar_sha256": verify_mod.digest(s_p.read_bytes()),
            "sidecar_id": sidecar["sidecar_id"],
            "lane": lane,
            "packet_binding": sidecar["packet_binding"],
        })

    ev_manifest = {
        "schema_version": "phase3_cycle007_evidence_manifest_v1",
        "text_free": True,
        "evaluation_cycle_id": verify_mod.CYCLE,
        "tokenizer_id": "phase3-cycle007-cyrillic-tokenizer-v1",
        "tokenizer_version": "1",
        "code_hashes": {"compiler_id": "c1"},
        "server_code_sha256": "srv",
        "sources_db_sha256": "src",
        "vesum_db_sha256": "vsm",
        "packet_count": 204,
        "row_count": 10159,
        "network_lookups_performed": 0,
        "sidecars": sidecar_meta,
        "source_package_binding": None,
    }
    ev_manifest["manifest_sha256"] = contract.sha256_value(ev_manifest)
    ev_m_p = ev_dir / "manifest.json"
    ev_m_p.write_text(json.dumps(ev_manifest, sort_keys=True) + "\n")
    ev_m_p.chmod(0o600)

    # Comparison batch receipt
    comp_dir = pkg / verify_mod.COMPARE_ROOT
    comp_dir.mkdir(parents=True, mode=0o700)
    comp_batch = {
        "schema_version": "phase3_cycle007_dual_label_batch_receipt_v1",
        "evaluation_cycle_id": verify_mod.CYCLE,
        "packet_count": 204,
        "row_count": 10159,
        "clean_consensus_count": 10000,
        "risk_triggered_consensus_count": 100,
        "disagreement_count": 59,
        "text_free": True,
    }
    (comp_dir / "batch-receipt.json").write_text(json.dumps(comp_batch) + "\n")
    (comp_dir / "batch-receipt.json").chmod(0o600)

    # Consensus audit batch receipt
    audit_dir = pkg / verify_mod.AUDIT_ROOT
    audit_dir.mkdir(parents=True, mode=0o700)
    audit_batch = {
        "schema_version": "phase3_cycle007_consensus_audit_batch_receipt_v1",
        "evaluation_cycle_id": verify_mod.CYCLE,
        "clean_audited_count": 600,
        "one_sided_95_bound": 0.004975,
        "terminal_findings_count": 0,
        "passed": True,
        "text_free": True,
    }
    (audit_dir / "batch-receipt.json").write_text(json.dumps(audit_batch) + "\n")
    (audit_dir / "batch-receipt.json").chmod(0o600)

    # Resolution final labels
    res_dir = pkg / verify_mod.RESOLUTION_ROOT
    res_dir.mkdir(parents=True, mode=0o700)
    final_clean = res_dir / "final" / "clean_label"
    final_clean.mkdir(parents=True, mode=0o700)
    final_res = res_dir / "final" / "residual_label"
    final_res.mkdir(parents=True, mode=0o700)

    for idx in range(1, 41):
        global_idx = idx
        s_p = ev_dir / f"sidecar-{global_idx:04d}.json"
        s_data = json.loads(s_p.read_text())
        lbls = []
        for r_ev in s_data["rows"]:
            lbls.append({
                "unit_id": r_ev["unit_id"],
                "unit_sha256": r_ev["unit_sha256"],
                "decision_code": "agree",
                "clean_modern_standard_prose": True,
                "modern_genre_id": "expository_narrative",
                "evidence_ids": r_ev["evidence_ids"],
            })
        lp = final_clean / f"labels-{idx:04d}.json"
        lp.write_text(json.dumps({"labels": lbls}) + "\n")
        lp.chmod(0o600)

    for idx in range(1, 165):
        global_idx = 40 + idx
        s_p = ev_dir / f"sidecar-{global_idx:04d}.json"
        s_data = json.loads(s_p.read_text())
        lbls = []
        for r_ev in s_data["rows"]:
            lbls.append({
                "unit_id": r_ev["unit_id"],
                "unit_sha256": r_ev["unit_sha256"],
                "phenomena": [
                    {
                        "phenomenon_id": "apostrophe",
                        "decision_code": "positive",
                        "evidence_sufficiency": "sufficient",
                        "evidence_ids": r_ev["phenomenon_evidence_ids"]["apostrophe"],
                    }
                ],
                "primary_phenomenon_id": "apostrophe",
                "item_decision_rollup": "positive",
            })
        lp = final_res / f"labels-{idx:04d}.json"
        lp.write_text(json.dumps({"labels": lbls}) + "\n")
        lp.chmod(0o600)

    res_batch = {
        "schema_version": "phase3_cycle007_operator_resolution_batch_receipt_v1",
        "evaluation_cycle_id": verify_mod.CYCLE,
        "packet_count": 204,
        "total_rows": 10159,
        "unresolved_remaining_count": 0,
        "text_free": True,
    }
    (res_dir / "batch-receipt.json").write_text(json.dumps(res_batch) + "\n")
    (res_dir / "batch-receipt.json").chmod(0o600)

    return pkg


def test_certifier_success_fixture_mode(tmp_path):
    pkg = _setup_certified_package(tmp_path)
    cert = verify_mod.certify_completion(pkg, fixture=True)
    assert cert["schema_version"] == "phase3_cycle007_label_completion_receipt_v1"
    assert cert["unresolved_remaining_count"] == 0
    assert cert["terminal_findings_count"] == 0
    assert cert["text_free"] is True


def test_certifier_fails_on_permission_drift(tmp_path):
    pkg = _setup_certified_package(tmp_path)
    # Drift file permission to world readable 0644
    (pkg / "manifest.json").chmod(0o644)

    with pytest.raises(verify_mod.Error) as exc:
        verify_mod.certify_completion(pkg, fixture=True)
    assert exc.value.failure_code == "package_modes"


def test_certifier_fails_on_provider_stop_presence(tmp_path):
    pkg = _setup_certified_package(tmp_path)
    stop_file = pkg / verify_mod.GROK_ROOT / "provider-stop.json"
    stop_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    stop_file.write_text("{}\n")
    stop_file.chmod(0o600)

    with pytest.raises(verify_mod.Error) as exc:
        verify_mod.certify_completion(pkg, fixture=True)
    assert exc.value.failure_code == "no_provider_stop"


def test_certifier_fails_on_unresolved_remaining(tmp_path):
    pkg = _setup_certified_package(tmp_path)
    # Drift res_batch unresolved_remaining_count to 1
    res_batch = {
        "schema_version": "phase3_cycle007_operator_resolution_batch_receipt_v1",
        "evaluation_cycle_id": verify_mod.CYCLE,
        "packet_count": 204,
        "total_rows": 10159,
        "unresolved_remaining_count": 1,
        "text_free": True,
    }
    (pkg / verify_mod.RESOLUTION_ROOT / "batch-receipt.json").write_text(json.dumps(res_batch) + "\n")

    with pytest.raises(verify_mod.Error) as exc:
        verify_mod.certify_completion(pkg, fixture=True)
    assert exc.value.failure_code == "final_residual_zero"


def test_certifier_fails_on_terminal_audit_finding(tmp_path):
    pkg = _setup_certified_package(tmp_path)
    audit_batch = {
        "schema_version": "phase3_cycle007_consensus_audit_batch_receipt_v1",
        "evaluation_cycle_id": verify_mod.CYCLE,
        "clean_audited_count": 600,
        "one_sided_95_bound": 0.004975,
        "terminal_findings_count": 1,
        "passed": False,
        "text_free": True,
    }
    (pkg / verify_mod.AUDIT_ROOT / "batch-receipt.json").write_text(json.dumps(audit_batch) + "\n")

    with pytest.raises(verify_mod.Error) as exc:
        verify_mod.certify_completion(pkg, fixture=True)
    assert exc.value.failure_code == "terminal_audit_finding"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))

