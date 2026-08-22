#!/usr/bin/env python3
"""Synthetic tests for Phase 3 Cycle 007 operator resolutions."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract

RES_PATH = HERE / "phase3-apply-cycle007-operator-resolutions-v1.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


res_mod = _load_module(RES_PATH, "res_mod")


def _setup_resolution_package(tmp_path: Path, *, unresolved_count: int = 1, clean_count: int = 1):
    pkg = tmp_path / "pkg"
    pkg.mkdir(parents=True, mode=0o700)

    rows = []
    for i in range(1, clean_count + 1):
        rows.append(
            {"unit_id": f"u-clean-{i}", "unit_sha256": f"{i:02d}" + "1" * 62, "clean_modern_standard_prose": True}
        )
    for i in range(1, unresolved_count + 1):
        rows.append(
            {"unit_id": f"u-unres-{i}", "unit_sha256": f"{i:02d}" + "2" * 62, "clean_modern_standard_prose": True}
        )

    # 1. Packet
    clean_dir = pkg / "clean_label"
    clean_dir.mkdir(parents=True, mode=0o700)
    p1 = clean_dir / "packet-0001.json"
    id_set = res_mod.digest(res_mod.canonical(sorted((r["unit_id"], r["unit_sha256"]) for r in rows)))
    p1_data = {"packet_identity_set_sha256": id_set, "rows": rows}
    p1.write_text(json.dumps(p1_data, sort_keys=True) + "\n")
    p1.chmod(0o600)
    p1_raw = p1.read_bytes()

    # 2. Custody & Manifest
    custody = {
        "schema_version": "phase3_cycle007_custody_receipt_v1",
        "evaluation_cycle_id": res_mod.CYCLE,
        "source_evaluation_cycle_id": res_mod.SOURCE_CYCLE,
        "source_custody_receipt_raw_sha256": res_mod.SOURCE_CUSTODY_SHA256,
        "source_label_manifest_raw_sha256": res_mod.SOURCE_MANIFEST_SHA256,
        "ordered_identity_commitment_sha256": "order_comm",
        "packet_count": 1,
        "row_count": len(rows),
        "lane_row_counts": {"clean_label": len(rows), "residual_label": 0},
        "provider_artifacts_copied": False,
        "labels_copied": False,
        "responses_copied": False,
        "text_free": True,
    }
    custody_p = pkg / "custody-receipt.json"
    custody_p.write_text(json.dumps(custody, sort_keys=True) + "\n")
    custody_p.chmod(0o600)
    custody_hash = res_mod.digest(custody_p.read_bytes())

    manifest = {
        "schema_version": "phase3_cycle007_materialization_manifest_v1",
        "evaluation_cycle_id": res_mod.CYCLE,
        "source_evaluation_cycle_id": res_mod.SOURCE_CYCLE,
        "text_free": True,
        "custody_receipt_raw_sha256": custody_hash,
        "ordered_identity_commitment_sha256": "order_comm",
        "packet_count": 1,
        "row_count": len(rows),
        "packets": [
            {
                "lane": "clean_label",
                "packet_index": 1,
                "canonical_basename": "packet-0001.json",
                "row_count": len(rows),
                "raw_sha256": res_mod.digest(p1_raw),
                "packet_identity_set_sha256": id_set,
            }
        ],
    }
    manifest_p = pkg / "manifest.json"
    manifest_p.write_text(json.dumps(manifest, sort_keys=True) + "\n")
    manifest_p.chmod(0o600)
    manifest_hash = res_mod.digest(manifest_p.read_bytes())

    # 3. Evidence sidecar & manifest
    ev_dir = pkg / "evidence"
    ev_dir.mkdir(parents=True, mode=0o700)

    rows_ev = []
    retrieval_payload = {"data": "attestation"}
    r_sha = contract.sha256_value(retrieval_payload)
    for r in rows:
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
            row=r,
            phenomenon_id=None,
        )
        rows_ev.append(
            {
                "unit_id": r["unit_id"],
                "unit_sha256": r["unit_sha256"],
                "evidence": [rec],
                "evidence_ids": [rec["evidence_id"]],
                "phenomenon_evidence_ids": {},
                "sufficient_support": True,
                "archaic_only_risk": False,
                "russian_shadow_suspected": False,
            }
        )

    sidecar = {
        "schema_version": "phase3_cycle007_evidence_sidecar_v1",
        "evaluation_cycle_id": res_mod.CYCLE,
        "lane": "clean_label",
        "packet_binding": {
            "canonical_basename": "packet-0001.json",
            "raw_sha256": res_mod.digest(p1_raw),
            "packet_identity_set_sha256": id_set,
        },
        "packet_index": 1,
        "row_count": len(rows),
        "tokenizer_id": "phase3-cycle007-cyrillic-tokenizer-v1",
        "tokenizer_version": "1",
        "code_hashes": {"compiler_id": "c1"},
        "server_code_sha256": "srv",
        "sources_db_sha256": "src",
        "vesum_db_sha256": "vsm",
        "network_lookups_performed": 0,
        "rows": rows_ev,
        "retrieval_payloads": {r_sha: retrieval_payload},
    }
    sidecar["sidecar_id"] = "cycle007_sidecar:" + contract.sha256_value(sidecar)
    s_p = ev_dir / "sidecar-0001.json"
    s_p.write_text(json.dumps(sidecar, sort_keys=True) + "\n")
    s_p.chmod(0o600)

    ev_manifest = {
        "schema_version": "phase3_cycle007_evidence_manifest_v1",
        "text_free": True,
        "evaluation_cycle_id": res_mod.CYCLE,
        "tokenizer_id": "phase3-cycle007-cyrillic-tokenizer-v1",
        "tokenizer_version": "1",
        "code_hashes": {"compiler_id": "c1"},
        "server_code_sha256": "srv",
        "sources_db_sha256": "src",
        "vesum_db_sha256": "vsm",
        "packet_count": 1,
        "row_count": len(rows),
        "network_lookups_performed": 0,
        "sidecars": [
            {
                "packet_index": 1,
                "row_count": len(rows),
                "sidecar_sha256": res_mod.digest(s_p.read_bytes()),
                "sidecar_id": sidecar["sidecar_id"],
                "lane": "clean_label",
                "packet_binding": sidecar["packet_binding"],
            }
        ],
        "source_package_binding": None,
    }
    ev_manifest["manifest_sha256"] = contract.sha256_value(ev_manifest)
    ev_m_p = ev_dir / "manifest.json"
    ev_m_p.write_text(json.dumps(ev_manifest, sort_keys=True) + "\n")
    ev_m_p.chmod(0o600)

    # 4. Comparison output
    comp_dir = pkg / res_mod.COMPARE_OUTPUT / "clean_label"
    comp_dir.mkdir(parents=True, mode=0o700)

    clean_records = []
    for r in rows[:clean_count]:
        clean_records.append(
            {
                "source_row": r,
                "label": {
                    "unit_id": r["unit_id"],
                    "unit_sha256": r["unit_sha256"],
                    "decision_code": "agree",
                    "clean_modern_standard_prose": True,
                    "modern_genre_id": "expository_narrative",
                    "evidence_ids": [rows_ev[0]["evidence"][0]["evidence_id"]],
                },
            }
        )

    disag_records = []
    for idx, r in enumerate(rows[clean_count:], start=clean_count):
        ev_id = rows_ev[idx]["evidence"][0]["evidence_id"]
        disag_records.append(
            {
                "source_row": r,
                "grok_label": {
                    "unit_id": r["unit_id"],
                    "unit_sha256": r["unit_sha256"],
                    "decision_code": "agree",
                    "clean_modern_standard_prose": True,
                    "modern_genre_id": "expository_narrative",
                    "evidence_ids": [ev_id],
                },
                "gemini_label": {
                    "unit_id": r["unit_id"],
                    "unit_sha256": r["unit_sha256"],
                    "decision_code": "reject_fragment_or_too_short",
                    "clean_modern_standard_prose": False,
                    "modern_genre_id": None,
                    "evidence_ids": [],
                },
            }
        )

    clean_p = comp_dir / "clean-consensus-0001.json"
    clean_p.write_text(json.dumps({"records": clean_records}, sort_keys=True) + "\n")
    clean_p.chmod(0o600)

    risk_p = comp_dir / "risk-consensus-0001.json"
    risk_p.write_text(json.dumps({"records": []}, sort_keys=True) + "\n")
    risk_p.chmod(0o600)

    disag_p = comp_dir / "disagreements-0001.json"
    disag_p.write_text(json.dumps({"records": disag_records}, sort_keys=True) + "\n")
    disag_p.chmod(0o600)

    comp_rcpt = {
        "schema_version": "phase3_cycle007_dual_label_packet_receipt_v1",
        "evaluation_cycle_id": res_mod.CYCLE,
        "amendment_sha256": res_mod.AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": custody_hash,
        "source_label_manifest_raw_sha256": res_mod.SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": manifest_hash,
        "ordered_identity_commitment_sha256": "order_comm",
        "lane": "clean_label",
        "packet_index": 1,
        "row_count": len(rows),
        "clean_consensus_sha256": res_mod.digest(clean_p.read_bytes()),
        "risk_consensus_sha256": res_mod.digest(risk_p.read_bytes()),
        "disagreements_sha256": res_mod.digest(disag_p.read_bytes()),
        "text_free": True,
    }
    comp_rcpt["receipt_sha256"] = res_mod.digest(res_mod.canonical(comp_rcpt))
    comp_rcpt_p = comp_dir / "receipt-0001.json"
    comp_rcpt_p.write_text(json.dumps(comp_rcpt, sort_keys=True) + "\n")
    comp_rcpt_p.chmod(0o600)

    # Compare batch receipt
    comp_batch = {
        "schema_version": "phase3_cycle007_dual_label_batch_receipt_v1",
        "evaluation_cycle_id": res_mod.CYCLE,
        "amendment_sha256": res_mod.AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": custody_hash,
        "source_label_manifest_raw_sha256": res_mod.SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": manifest_hash,
        "ordered_identity_commitment_sha256": "order_comm",
        "packet_count": 1,
        "row_count": len(rows),
        "clean_consensus_count": len(clean_records),
        "risk_triggered_consensus_count": 0,
        "disagreement_count": len(disag_records),
        "packet_receipt_union_sha256": res_mod.digest(res_mod.canonical([comp_rcpt["receipt_sha256"]])),
        "text_free": True,
    }
    comp_batch["receipt_sha256"] = res_mod.digest(res_mod.canonical(comp_batch))
    (pkg / res_mod.COMPARE_OUTPUT / "batch-receipt.json").write_text(json.dumps(comp_batch, sort_keys=True) + "\n")
    (pkg / res_mod.COMPARE_OUTPUT / "batch-receipt.json").chmod(0o600)

    # 5. Adjudication output
    adj_dir = pkg / res_mod.ADJUDICATION_OUTPUT / "final" / "clean_label"
    adj_dir.mkdir(parents=True, mode=0o700)

    adj_labels_p = adj_dir / "labels-0001.json"
    adj_labels_p.write_text(json.dumps({"labels": []}, sort_keys=True) + "\n")
    adj_labels_p.chmod(0o600)

    adj_unres_p = adj_dir / "unresolved-0001.json"
    adj_unres_p.write_text(json.dumps({"records": disag_records}, sort_keys=True) + "\n")
    adj_unres_p.chmod(0o600)

    adj_rcpt = {
        "schema_version": "phase3_cycle007_dual_label_adjudication_packet_receipt_v1",
        "evaluation_cycle_id": res_mod.CYCLE,
        "amendment_sha256": res_mod.AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": custody_hash,
        "source_label_manifest_raw_sha256": res_mod.SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": manifest_hash,
        "ordered_identity_commitment_sha256": "order_comm",
        "lane": "clean_label",
        "packet_index": 1,
        "model": "Claude Sonnet 4.6 (Thinking)",
        "model_family": "anthropic",
        "harness": "agy",
        "labels_sha256": res_mod.digest(adj_labels_p.read_bytes()),
        "unresolved_sha256": res_mod.digest(adj_unres_p.read_bytes()),
        "disagreement_count": len(disag_records),
        "adjudicated_count": 0,
        "unresolved_count": len(disag_records),
        "text_free": True,
    }
    adj_rcpt["receipt_sha256"] = res_mod.digest(res_mod.canonical(adj_rcpt))
    adj_rcpt_p = adj_dir / "receipt-0001.json"
    adj_rcpt_p.write_text(json.dumps(adj_rcpt, sort_keys=True) + "\n")
    adj_rcpt_p.chmod(0o600)

    # Adjudication batch receipt
    adj_batch = {
        "schema_version": "phase3_cycle007_dual_label_adjudication_batch_receipt_v1",
        "evaluation_cycle_id": res_mod.CYCLE,
        "amendment_sha256": res_mod.AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": custody_hash,
        "source_label_manifest_raw_sha256": res_mod.SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": manifest_hash,
        "ordered_identity_commitment_sha256": "order_comm",
        "packet_count": 1,
        "total_disagreements": len(disag_records),
        "total_adjudicated": 0,
        "total_unresolved": len(disag_records),
        "model": "Claude Sonnet 4.6 (Thinking)",
        "model_family": "anthropic",
        "harness": "agy",
        "packet_receipt_union_sha256": res_mod.digest(res_mod.canonical([adj_rcpt["receipt_sha256"]])),
        "text_free": True,
    }
    adj_batch["receipt_sha256"] = res_mod.digest(res_mod.canonical(adj_batch))
    (pkg / res_mod.ADJUDICATION_OUTPUT / "batch-receipt.json").write_text(json.dumps(adj_batch, sort_keys=True) + "\n")
    (pkg / res_mod.ADJUDICATION_OUTPUT / "batch-receipt.json").chmod(0o600)

    return pkg, rows, rows_ev


def _make_authorization(pkg: Path, authorizations: list[dict[str, Any]]) -> Path:
    identity_order = [(item["unit_id"], item["unit_sha256"]) for item in authorizations]
    auth_doc = {
        "schema_version": res_mod.AUTHORIZATION_SCHEMA_VERSION,
        "evaluation_cycle_id": res_mod.CYCLE,
        "amendment_sha256": res_mod.AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": res_mod.digest((pkg / "custody-receipt.json").read_bytes()),
        "source_label_manifest_raw_sha256": res_mod.SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": res_mod.digest((pkg / "manifest.json").read_bytes()),
        "ordered_identity_commitment_sha256": "order_comm",
        "request_raw_sha256": None,
        "decision_authority": "operator",
        "operator_id": "operator.fixture",
        "authorized_identity": {"identity_type": "human", "identity_id": "operator.fixture"},
        "identity_order_sha256": res_mod.digest(res_mod.canonical([list(identity) for identity in identity_order])),
        "nonce_sha256": hashlib.sha256(b"synthetic-operator-nonce").hexdigest(),
        "authorizations": authorizations,
        "text_free": True,
    }
    auth_doc["receipt_sha256"] = res_mod.digest(res_mod.canonical(auth_doc))
    auth_p = pkg / res_mod.RESOLUTION_OUTPUT / "authorization.json"
    auth_p.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    auth_p.write_bytes(res_mod.canonical(auth_doc))
    auth_p.chmod(0o600)
    return auth_p


def _make_resolution_request(pkg: Path, records: list[dict[str, Any]]) -> Path:
    request = {
        "schema_version": "phase3_cycle007_operator_resolution_request_v1",
        "evaluation_cycle_id": res_mod.CYCLE,
        "amendment_sha256": res_mod.AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": res_mod.digest((pkg / "custody-receipt.json").read_bytes()),
        "source_label_manifest_raw_sha256": res_mod.SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": res_mod.digest((pkg / "manifest.json").read_bytes()),
        "ordered_identity_commitment_sha256": "order_comm",
        "unresolved_count": len(records),
        "unresolved_records": records,
        "text_free": False,
    }
    request["request_sha256"] = res_mod.digest(res_mod.canonical(request))
    request_p = pkg / res_mod.ADJUDICATION_OUTPUT / "operator-resolution-request.json"
    request_p.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    request_p.write_bytes(res_mod.canonical(request))
    request_p.chmod(0o600)
    return request_p


def test_operator_resolution_success(tmp_path):
    pkg, rows, _rows_ev = _setup_resolution_package(tmp_path, unresolved_count=1, clean_count=1)
    unres_row = rows[1]
    auth_p = _make_authorization(
        pkg,
        [
            {
                "unit_id": unres_row["unit_id"],
                "unit_sha256": unres_row["unit_sha256"],
                "selection": "grok",
                "source_bound_rationale": "Grok label agrees with Slovnyk normative entry",
                "source_authority_reference": "pravopys_2026:section_1",
            }
        ],
    )

    auths = res_mod.validate_authorization_file(auth_p, pkg, fixture=True)
    assert (unres_row["unit_id"], unres_row["unit_sha256"]) in auths

    result = res_mod.resolve_packet(pkg, "clean_label", 1, auths, fixture=True)
    assert result["unresolved_remaining_count"] == 0
    assert result["clean_consensus_count"] == 1
    assert result["operator_resolved_count"] == 1

    final_labels_p = pkg / res_mod.RESOLUTION_OUTPUT / "final" / "clean_label" / "labels-0001.json"
    final_data = json.loads(final_labels_p.read_text())
    assert len(final_data["labels"]) == 2
    assert final_data["labels"][1]["decision_code"] == "agree"


def test_operator_resolution_missing_sidecar_fails_closed(tmp_path):
    pkg, rows, _ = _setup_resolution_package(tmp_path, unresolved_count=1, clean_count=1)
    unres_row = rows[1]
    auth_p = _make_authorization(
        pkg,
        [
            {
                "unit_id": unres_row["unit_id"],
                "unit_sha256": unres_row["unit_sha256"],
                "selection": "grok",
                "source_bound_rationale": "Valid rationale",
                "source_authority_reference": "pravopys_2026:section_1",
            }
        ],
    )
    auths = res_mod.validate_authorization_file(auth_p, pkg, fixture=True)
    (pkg / "evidence" / "sidecar-0001.json").unlink()

    with pytest.raises(res_mod.Error) as exc:
        res_mod.resolve_packet(pkg, "clean_label", 1, auths, fixture=True)
    assert exc.value.failure_code == "missing_evidence_sidecar"


def test_operator_authorization_requires_human_identity_and_authority(tmp_path):
    pkg, rows, _ = _setup_resolution_package(tmp_path, unresolved_count=1, clean_count=0)
    unres_row = rows[0]
    auth_p = _make_authorization(
        pkg,
        [
            {
                "unit_id": unres_row["unit_id"],
                "unit_sha256": unres_row["unit_sha256"],
                "selection": "grok",
                "source_bound_rationale": "Valid rationale",
                "source_authority_reference": "pravopys_2026:section_1",
            }
        ],
    )
    auth_doc = json.loads(auth_p.read_text())
    del auth_doc["authorized_identity"]
    auth_doc["receipt_sha256"] = res_mod.digest(
        res_mod.canonical({key: value for key, value in auth_doc.items() if key != "receipt_sha256"})
    )
    auth_p.write_bytes(res_mod.canonical(auth_doc))

    with pytest.raises(res_mod.Error) as exc:
        res_mod.validate_authorization_file(auth_p, pkg, fixture=True)
    assert exc.value.failure_code == "authorization_binding_failure"


def test_live_authorization_receipt_cannot_live_inside_package(tmp_path):
    pkg, rows, _ = _setup_resolution_package(tmp_path, unresolved_count=1, clean_count=0)
    unres_row = rows[0]
    auth_p = _make_authorization(
        pkg,
        [
            {
                "unit_id": unres_row["unit_id"],
                "unit_sha256": unres_row["unit_sha256"],
                "selection": "grok",
                "source_bound_rationale": "Valid rationale",
                "source_authority_reference": "pravopys_2026:section_1",
            }
        ],
    )

    with pytest.raises(res_mod.Error) as exc:
        res_mod.validate_authorization_file(auth_p, pkg)
    assert exc.value.failure_code == "authorization_binding_failure"


def test_operator_resolution_extra_or_foreign_authorization(tmp_path):
    pkg, rows, _ = _setup_resolution_package(tmp_path, unresolved_count=1, clean_count=1)
    unres_row = rows[1]
    auth_p = _make_authorization(
        pkg,
        [
            {
                "unit_id": unres_row["unit_id"],
                "unit_sha256": unres_row["unit_sha256"],
                "selection": "grok",
                "source_bound_rationale": "Valid rationale",
                "source_authority_reference": "pravopys_2026:section_1",
            },
            {
                "unit_id": "u-foreign-999",
                "unit_sha256": "9" * 64,
                "selection": "grok",
                "source_bound_rationale": "Foreign row rationale",
                "source_authority_reference": "pravopys_2026:section_1",
            },
        ],
    )

    with pytest.raises(res_mod.Error) as exc:
        res_mod.resolve_all(pkg, auth_p, fixture=True)
    assert exc.value.failure_code in {"foreign_authorization", "extra_authorization"}


def test_operator_resolution_already_resolved_authorization(tmp_path):
    pkg, rows, _ = _setup_resolution_package(tmp_path, unresolved_count=1, clean_count=1)
    clean_row = rows[0]
    unres_row = rows[1]
    # Authorizing clean_row which is already in clean_consensus!
    auth_p = _make_authorization(
        pkg,
        [
            {
                "unit_id": unres_row["unit_id"],
                "unit_sha256": unres_row["unit_sha256"],
                "selection": "grok",
                "source_bound_rationale": "Valid rationale",
                "source_authority_reference": "pravopys_2026:section_1",
            },
            {
                "unit_id": clean_row["unit_id"],
                "unit_sha256": clean_row["unit_sha256"],
                "selection": "grok",
                "source_bound_rationale": "Already resolved row",
                "source_authority_reference": "pravopys_2026:section_1",
            },
        ],
    )

    with pytest.raises(res_mod.Error) as exc:
        res_mod.resolve_all(pkg, auth_p, fixture=True)
    assert exc.value.failure_code == "already_resolved_authorization"


def test_operator_resolution_source_blind_authorization(tmp_path):
    pkg, rows, _ = _setup_resolution_package(tmp_path, unresolved_count=1, clean_count=0)
    unres_row = rows[0]
    # Empty source_bound_rationale
    auth_p = _make_authorization(
        pkg,
        [
            {
                "unit_id": unres_row["unit_id"],
                "unit_sha256": unres_row["unit_sha256"],
                "selection": "grok",
                "source_bound_rationale": "   ",
                "source_authority_reference": "pravopys_2026:section_1",
            }
        ],
    )

    with pytest.raises(res_mod.Error) as exc:
        res_mod.validate_authorization_file(auth_p, pkg, fixture=True)
    assert exc.value.failure_code == "authorization_tamper_detected"


def test_operator_resolution_candidate_invention_rejected(tmp_path):
    pkg, rows, _ = _setup_resolution_package(tmp_path, unresolved_count=1, clean_count=0)
    unres_row = rows[0]
    auth_p = _make_authorization(
        pkg,
        [
            {
                "unit_id": unres_row["unit_id"],
                "unit_sha256": unres_row["unit_sha256"],
                "selection": "invented_third_model",
                "source_bound_rationale": "Invalid",
                "source_authority_reference": "ref",
            }
        ],
    )

    with pytest.raises(res_mod.Error) as exc:
        res_mod.validate_authorization_file(auth_p, pkg, fixture=True)
    assert exc.value.failure_code == "authorization_tamper_detected"


def test_operator_resolution_partition_overlap_rejected(tmp_path):
    pkg, rows, _ = _setup_resolution_package(tmp_path, unresolved_count=1, clean_count=1)
    clean_row = rows[0]
    unres_row = rows[1]
    auth_p = _make_authorization(
        pkg,
        [
            {
                "unit_id": unres_row["unit_id"],
                "unit_sha256": unres_row["unit_sha256"],
                "selection": "grok",
                "source_bound_rationale": "Valid rationale",
                "source_authority_reference": "pravopys_2026:section_1",
            }
        ],
    )
    auths = res_mod.validate_authorization_file(auth_p, pkg, fixture=True)

    # Corrupt risk-consensus to also include clean_row
    risk_p = pkg / res_mod.COMPARE_OUTPUT / "clean_label" / "risk-consensus-0001.json"
    risk_p.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "source_row": clean_row,
                        "label": {
                            "unit_id": clean_row["unit_id"],
                            "unit_sha256": clean_row["unit_sha256"],
                            "decision_code": "agree",
                            "clean_modern_standard_prose": True,
                            "modern_genre_id": "expository_narrative",
                            "evidence_ids": [],
                        },
                    }
                ]
            }
        )
        + "\n"
    )
    # Update compare receipt hash to match modified risk_p so we test partition overlap
    comp_rcpt_p = pkg / res_mod.COMPARE_OUTPUT / "clean_label" / "receipt-0001.json"
    rcpt_val = json.loads(comp_rcpt_p.read_text())
    rcpt_val["risk_consensus_sha256"] = res_mod.digest(risk_p.read_bytes())
    rcpt_val["receipt_sha256"] = res_mod.digest(
        res_mod.canonical({k: v for k, v in rcpt_val.items() if k != "receipt_sha256"})
    )
    comp_rcpt_p.write_text(json.dumps(rcpt_val) + "\n")

    with pytest.raises(res_mod.Error) as exc:
        res_mod.resolve_packet(pkg, "clean_label", 1, auths, fixture=True)
    assert exc.value.failure_code == "partition_overlap_drift"


def test_operator_resolution_partition_omission_rejected(tmp_path):
    pkg, rows, _ = _setup_resolution_package(tmp_path, unresolved_count=1, clean_count=1)
    unres_row = rows[1]
    auth_p = _make_authorization(
        pkg,
        [
            {
                "unit_id": unres_row["unit_id"],
                "unit_sha256": unres_row["unit_sha256"],
                "selection": "grok",
                "source_bound_rationale": "Valid rationale",
                "source_authority_reference": "pravopys_2026:section_1",
            }
        ],
    )
    auths = res_mod.validate_authorization_file(auth_p, pkg, fixture=True)

    # Empty out clean-consensus so clean_row is omitted
    clean_p = pkg / res_mod.COMPARE_OUTPUT / "clean_label" / "clean-consensus-0001.json"
    clean_p.write_text(json.dumps({"records": []}) + "\n")
    comp_rcpt_p = pkg / res_mod.COMPARE_OUTPUT / "clean_label" / "receipt-0001.json"
    rcpt_val = json.loads(comp_rcpt_p.read_text())
    rcpt_val["clean_consensus_sha256"] = res_mod.digest(clean_p.read_bytes())
    rcpt_val["receipt_sha256"] = res_mod.digest(
        res_mod.canonical({k: v for k, v in rcpt_val.items() if k != "receipt_sha256"})
    )
    comp_rcpt_p.write_text(json.dumps(rcpt_val) + "\n")

    with pytest.raises(res_mod.Error) as exc:
        res_mod.resolve_packet(pkg, "clean_label", 1, auths, fixture=True)
    assert exc.value.failure_code == "partition_omission_drift"


def test_operator_resolution_forged_upstream_receipt_rejected(tmp_path):
    pkg, rows, _ = _setup_resolution_package(tmp_path, unresolved_count=1, clean_count=1)
    unres_row = rows[1]
    auth_p = _make_authorization(
        pkg,
        [
            {
                "unit_id": unres_row["unit_id"],
                "unit_sha256": unres_row["unit_sha256"],
                "selection": "grok",
                "source_bound_rationale": "Valid rationale",
                "source_authority_reference": "pravopys_2026:section_1",
            }
        ],
    )
    auths = res_mod.validate_authorization_file(auth_p, pkg, fixture=True)

    # Tamper with compare receipt hash
    comp_rcpt_p = pkg / res_mod.COMPARE_OUTPUT / "clean_label" / "receipt-0001.json"
    rcpt_val = json.loads(comp_rcpt_p.read_text())
    rcpt_val["clean_consensus_sha256"] = "0" * 64
    comp_rcpt_p.write_text(json.dumps(rcpt_val) + "\n")

    with pytest.raises(res_mod.Error) as exc:
        res_mod.resolve_packet(pkg, "clean_label", 1, auths, fixture=True)
    assert exc.value.failure_code == "upstream_receipt_drift"


def test_operator_resolution_missing_authorization(tmp_path):
    pkg, _rows, _ = _setup_resolution_package(tmp_path, unresolved_count=1, clean_count=0)
    auth_p = _make_authorization(pkg, [])
    auths = res_mod.validate_authorization_file(auth_p, pkg, fixture=True)

    with pytest.raises(res_mod.Error) as exc:
        res_mod.resolve_packet(pkg, "clean_label", 1, auths, fixture=True)
    assert exc.value.failure_code == "missing_authorization"


def test_operator_resolution_resolve_all_fixture(tmp_path):
    pkg, rows, _ = _setup_resolution_package(tmp_path, unresolved_count=1, clean_count=1)
    unres_row = rows[1]
    auth_p = _make_authorization(
        pkg,
        [
            {
                "unit_id": unres_row["unit_id"],
                "unit_sha256": unres_row["unit_sha256"],
                "selection": "grok",
                "source_bound_rationale": "Grok label agrees with Slovnyk normative entry",
                "source_authority_reference": "pravopys_2026:section_1",
            }
        ],
    )

    batch_rcpt = res_mod.resolve_all(pkg, auth_p, fixture=True)
    assert batch_rcpt["schema_version"] == "phase3_cycle007_operator_resolution_batch_receipt_v1"
    assert batch_rcpt["total_rows"] == 2
    assert batch_rcpt["unresolved_remaining_count"] == 0
    assert batch_rcpt["text_free"] is True


def test_resolution_request_must_match_exact_unresolved_records(tmp_path):
    pkg, rows, _ = _setup_resolution_package(tmp_path, unresolved_count=1, clean_count=1)
    unres_row = rows[1]
    auth_p = _make_authorization(
        pkg,
        [
            {
                "unit_id": unres_row["unit_id"],
                "unit_sha256": unres_row["unit_sha256"],
                "selection": "grok",
                "source_bound_rationale": "Valid rationale",
                "source_authority_reference": "pravopys_2026:section_1",
            }
        ],
    )
    unresolved_path = pkg / res_mod.ADJUDICATION_OUTPUT / "final" / "clean_label" / "unresolved-0001.json"
    unresolved_records = json.loads(unresolved_path.read_text())["records"]
    forged_records = json.loads(json.dumps(unresolved_records))
    forged_records[0]["grok_label"]["unit_id"] = "forged-unresolved-item"
    _make_resolution_request(pkg, forged_records)

    with pytest.raises(res_mod.Error) as exc:
        res_mod.resolve_all(pkg, auth_p, fixture=True)
    assert exc.value.failure_code == "authorization_identity_failure"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
