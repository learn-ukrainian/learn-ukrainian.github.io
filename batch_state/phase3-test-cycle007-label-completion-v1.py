#!/usr/bin/env python3
"""Synthetic tests for Phase 3 Cycle 007 label completion verifier."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

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

    # Clean rows: 2 rows
    # row 0: agree / expository_narrative (both models agree -> clean consensus)
    # row 1: grok says agree, gemini says reject_fragment_or_too_short -> disagreement -> adjudicated as grok agree
    clean_rows = [
        {
            "unit_id": "clean.1.0",
            "unit_sha256": "10" + "0" * 62,
            "clean_modern_standard_prose": True,
        },
        {
            "unit_id": "clean.1.1",
            "unit_sha256": "11" + "0" * 62,
            "clean_modern_standard_prose": True,
        },
    ]

    # Residual rows: 2 rows
    # row 0: positive apostrophe (both models agree -> clean consensus)
    # row 1: positive apostrophe, but tagged is_negative_control -> risk consensus
    residual_rows = [
        {
            "unit_id": "residual.1.0",
            "unit_sha256": "20" + "0" * 62,
            "family_id": "standard",
        },
        {
            "unit_id": "residual.1.1",
            "unit_sha256": "21" + "0" * 62,
            "family_id": "standard",
            "is_negative_control": True,
        },
    ]

    # 1. Packets setup
    clean_dir = pkg / "clean_label"
    clean_dir.mkdir(parents=True, mode=0o700)
    p_clean = clean_dir / "packet-0001.json"
    id_set_clean = verify_mod.digest(verify_mod.canonical(sorted((r["unit_id"], r["unit_sha256"]) for r in clean_rows)))
    p_clean.write_text(
        json.dumps({"packet_identity_set_sha256": id_set_clean, "rows": clean_rows}, sort_keys=True) + "\n"
    )
    p_clean.chmod(0o600)
    p_clean_raw = p_clean.read_bytes()

    res_dir = pkg / "residual_label"
    res_dir.mkdir(parents=True, mode=0o700)
    p_res = res_dir / "packet-0001.json"
    id_set_res = verify_mod.digest(
        verify_mod.canonical(sorted((r["unit_id"], r["unit_sha256"]) for r in residual_rows))
    )
    p_res.write_text(
        json.dumps({"packet_identity_set_sha256": id_set_res, "rows": residual_rows}, sort_keys=True) + "\n"
    )
    p_res.chmod(0o600)
    p_res_raw = p_res.read_bytes()

    ordered_identities = [
        ["clean_label", 1, 0, clean_rows[0]["unit_id"], clean_rows[0]["unit_sha256"]],
        ["clean_label", 1, 1, clean_rows[1]["unit_id"], clean_rows[1]["unit_sha256"]],
        ["residual_label", 1, 0, residual_rows[0]["unit_id"], residual_rows[0]["unit_sha256"]],
        ["residual_label", 1, 1, residual_rows[1]["unit_id"], residual_rows[1]["unit_sha256"]],
    ]
    commitment = verify_mod.digest(verify_mod.canonical(ordered_identities))

    # 2. Custody & Manifest
    custody = {
        "schema_version": "phase3_cycle007_custody_receipt_v1",
        "evaluation_cycle_id": verify_mod.CYCLE,
        "source_evaluation_cycle_id": verify_mod.SOURCE_CYCLE,
        "source_custody_receipt_raw_sha256": verify_mod.SOURCE_CUSTODY_SHA256,
        "source_label_manifest_raw_sha256": verify_mod.SOURCE_MANIFEST_SHA256,
        "ordered_identity_commitment_sha256": commitment,
        "packet_count": 2,
        "row_count": 4,
        "lane_row_counts": {"clean_label": 2, "residual_label": 2},
        "provider_artifacts_copied": False,
        "labels_copied": False,
        "responses_copied": False,
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
        "packet_count": 2,
        "row_count": 4,
        "lane_row_counts": {"clean_label": 2, "residual_label": 2},
        "packets": [
            {
                "lane": "clean_label",
                "packet_index": 1,
                "canonical_basename": "packet-0001.json",
                "row_count": 2,
                "raw_sha256": verify_mod.digest(p_clean_raw),
                "packet_identity_set_sha256": id_set_clean,
            },
            {
                "lane": "residual_label",
                "packet_index": 1,
                "canonical_basename": "packet-0001.json",
                "row_count": 2,
                "raw_sha256": verify_mod.digest(p_res_raw),
                "packet_identity_set_sha256": id_set_res,
            },
        ],
    }
    manifest_p = pkg / "manifest.json"
    manifest_p.write_text(json.dumps(manifest, sort_keys=True) + "\n")
    manifest_p.chmod(0o600)
    manifest_hash = verify_mod.digest(manifest_p.read_bytes())

    # 3. Evidence sidecars & manifest
    ev_dir = pkg / "evidence"
    ev_dir.mkdir(parents=True, mode=0o700)

    # Clean sidecar
    retrieval_payload = {"data": "attested"}
    r_sha = contract.sha256_value(retrieval_payload)
    clean_ev_rows = []
    for r in clean_rows:
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
        clean_ev_rows.append(
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
    s_clean = {
        "schema_version": "phase3_cycle007_evidence_sidecar_v1",
        "evaluation_cycle_id": verify_mod.CYCLE,
        "lane": "clean_label",
        "packet_binding": {
            "canonical_basename": "packet-0001.json",
            "raw_sha256": verify_mod.digest(p_clean_raw),
            "packet_identity_set_sha256": id_set_clean,
        },
        "packet_index": 1,
        "row_count": 2,
        "tokenizer_id": "phase3-cycle007-cyrillic-tokenizer-v1",
        "tokenizer_version": "1",
        "code_hashes": {"compiler_id": "c1"},
        "server_code_sha256": "srv",
        "sources_db_sha256": "src",
        "vesum_db_sha256": "vsm",
        "network_lookups_performed": 0,
        "rows": clean_ev_rows,
        "retrieval_payloads": {r_sha: retrieval_payload},
    }
    s_clean["sidecar_id"] = "cycle007_sidecar:" + contract.sha256_value(s_clean)
    s_clean_p = ev_dir / "sidecar-0001.json"
    s_clean_p.write_text(json.dumps(s_clean, sort_keys=True) + "\n")
    s_clean_p.chmod(0o600)

    # Residual sidecar
    res_ev_rows = []
    for r in residual_rows:
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
            phenomenon_id="apostrophe",
        )
        phenom_map = {p: [] for p in contract.RESIDUAL_PHENOMENON_TAXONOMY}
        phenom_map["apostrophe"] = [rec["evidence_id"]]
        res_ev_rows.append(
            {
                "unit_id": r["unit_id"],
                "unit_sha256": r["unit_sha256"],
                "evidence": [rec],
                "evidence_ids": [rec["evidence_id"]],
                "phenomenon_evidence_ids": phenom_map,
                "sufficient_support": True,
                "archaic_only_risk": False,
                "russian_shadow_suspected": False,
            }
        )
    s_res = {
        "schema_version": "phase3_cycle007_evidence_sidecar_v1",
        "evaluation_cycle_id": verify_mod.CYCLE,
        "lane": "residual_label",
        "packet_binding": {
            "canonical_basename": "packet-0001.json",
            "raw_sha256": verify_mod.digest(p_res_raw),
            "packet_identity_set_sha256": id_set_res,
        },
        "packet_index": 2,
        "row_count": 2,
        "tokenizer_id": "phase3-cycle007-cyrillic-tokenizer-v1",
        "tokenizer_version": "1",
        "code_hashes": {"compiler_id": "c1"},
        "server_code_sha256": "srv",
        "sources_db_sha256": "src",
        "vesum_db_sha256": "vsm",
        "network_lookups_performed": 0,
        "rows": res_ev_rows,
        "retrieval_payloads": {r_sha: retrieval_payload},
    }
    s_res["sidecar_id"] = "cycle007_sidecar:" + contract.sha256_value(s_res)
    s_res_p = ev_dir / "sidecar-0002.json"
    s_res_p.write_text(json.dumps(s_res, sort_keys=True) + "\n")
    s_res_p.chmod(0o600)

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
        "packet_count": 2,
        "row_count": 4,
        "network_lookups_performed": 0,
        "sidecars": [
            {
                "packet_index": 1,
                "row_count": 2,
                "sidecar_sha256": verify_mod.digest(s_clean_p.read_bytes()),
                "sidecar_id": s_clean["sidecar_id"],
                "lane": "clean_label",
                "packet_binding": s_clean["packet_binding"],
            },
            {
                "packet_index": 2,
                "row_count": 2,
                "sidecar_sha256": verify_mod.digest(s_res_p.read_bytes()),
                "sidecar_id": s_res["sidecar_id"],
                "lane": "residual_label",
                "packet_binding": s_res["packet_binding"],
            },
        ],
        "source_package_binding": None,
    }
    ev_manifest["manifest_sha256"] = contract.sha256_value(ev_manifest)
    ev_m_p = ev_dir / "manifest.json"
    ev_m_p.write_text(json.dumps(ev_manifest, sort_keys=True) + "\n")
    ev_m_p.chmod(0o600)

    # 4. Provider outputs (Grok & Gemini)
    grok_clean_labels = [
        {
            "unit_id": "clean.1.0",
            "unit_sha256": clean_rows[0]["unit_sha256"],
            "decision_code": "agree",
            "clean_modern_standard_prose": True,
            "modern_genre_id": "expository_narrative",
            "evidence_ids": clean_ev_rows[0]["evidence_ids"],
        },
        {
            "unit_id": "clean.1.1",
            "unit_sha256": clean_rows[1]["unit_sha256"],
            "decision_code": "agree",
            "clean_modern_standard_prose": True,
            "modern_genre_id": "expository_narrative",
            "evidence_ids": clean_ev_rows[1]["evidence_ids"],
        },
    ]
    gemini_clean_labels = [
        {
            "unit_id": "clean.1.0",
            "unit_sha256": clean_rows[0]["unit_sha256"],
            "decision_code": "agree",
            "clean_modern_standard_prose": True,
            "modern_genre_id": "expository_narrative",
            "evidence_ids": clean_ev_rows[0]["evidence_ids"],
        },
        {
            "unit_id": "clean.1.1",
            "unit_sha256": clean_rows[1]["unit_sha256"],
            "decision_code": "reject_fragment_or_too_short",
            "clean_modern_standard_prose": False,
            "modern_genre_id": None,
            "evidence_ids": [],
        },
    ]

    def _make_res_lbl(uid: str, usha: str, ev_ids: list[str], code: str = "positive") -> dict[str, Any]:
        phenomena = []
        for p in contract.RESIDUAL_PHENOMENON_TAXONOMY:
            if p == "apostrophe":
                phenomena.append(
                    {
                        "phenomenon_id": p,
                        "decision_code": code,
                        "evidence_sufficiency": "sufficient",
                        "evidence_ids": ev_ids,
                    }
                )
            else:
                phenomena.append(
                    {
                        "phenomenon_id": p,
                        "decision_code": "abstention",
                        "evidence_sufficiency": "insufficient",
                        "evidence_ids": [],
                    }
                )
        return {
            "unit_id": uid,
            "unit_sha256": usha,
            "phenomena": phenomena,
            "primary_phenomenon_id": "apostrophe",
            "item_decision_rollup": code,
        }

    grok_res_labels = [
        _make_res_lbl("residual.1.0", residual_rows[0]["unit_sha256"], res_ev_rows[0]["evidence_ids"], code="positive"),
        _make_res_lbl(
            "residual.1.1", residual_rows[1]["unit_sha256"], res_ev_rows[1]["evidence_ids"], code="acceptable_control"
        ),
    ]
    gemini_res_labels = [
        _make_res_lbl("residual.1.0", residual_rows[0]["unit_sha256"], res_ev_rows[0]["evidence_ids"], code="positive"),
        _make_res_lbl(
            "residual.1.1", residual_rows[1]["unit_sha256"], res_ev_rows[1]["evidence_ids"], code="acceptable_control"
        ),
    ]

    # Write Grok
    grok_dir = pkg / verify_mod.GROK_ROOT
    for lane, idx, lbls, p_raw, idset in [
        ("clean_label", 1, grok_clean_labels, p_clean_raw, id_set_clean),
        ("residual_label", 1, grok_res_labels, p_res_raw, id_set_res),
    ]:
        ldir = grok_dir / lane
        ldir.mkdir(parents=True, exist_ok=True, mode=0o700)
        lp = ldir / f"labels-{idx:04d}.json"
        lp.write_text(json.dumps({"labels": lbls}, sort_keys=True) + "\n")
        lp.chmod(0o600)
        rcpt = {
            "schema_version": "phase3_cycle007_grok_packet_label_receipt_v1",
            "evaluation_cycle_id": verify_mod.CYCLE,
            "amendment_sha256": verify_mod.AMENDMENT_SHA256,
            "custody_receipt_raw_sha256": custody_hash,
            "manifest_raw_sha256": manifest_hash,
            "ordered_identity_commitment_sha256": commitment,
            "lane": lane,
            "packet_index": idx,
            "row_count": len(lbls),
            "packet_raw_sha256": verify_mod.digest(p_raw),
            "packet_identity_set_sha256": idset,
            "exact_model": "grok-4.5",
            "model_family": "xai",
            "harness": "native_grok",
            "labels_sha256": verify_mod.digest(lp.read_bytes()),
            "text_free": True,
        }
        rcpt["receipt_sha256"] = verify_mod.digest(verify_mod.canonical(rcpt))
        rp = ldir / f"receipt-{idx:04d}.json"
        rp.write_text(json.dumps(rcpt, sort_keys=True) + "\n")
        rp.chmod(0o600)

    # Write Gemini
    gemini_dir = pkg / verify_mod.GEMINI_ROOT
    for lane, idx, lbls, p_raw, idset in [
        ("clean_label", 1, gemini_clean_labels, p_clean_raw, id_set_clean),
        ("residual_label", 1, gemini_res_labels, p_res_raw, id_set_res),
    ]:
        ldir = gemini_dir / lane
        ldir.mkdir(parents=True, exist_ok=True, mode=0o700)
        lp = ldir / f"labels-{idx:04d}.json"
        lp.write_text(json.dumps({"labels": lbls}, sort_keys=True) + "\n")
        lp.chmod(0o600)
        rcpt = {
            "schema_version": "phase3_cycle007_gemini_packet_label_receipt_v1",
            "evaluation_cycle_id": verify_mod.CYCLE,
            "amendment_sha256": verify_mod.AMENDMENT_SHA256,
            "custody_receipt_raw_sha256": custody_hash,
            "manifest_raw_sha256": manifest_hash,
            "ordered_identity_commitment_sha256": commitment,
            "lane": lane,
            "packet_index": idx,
            "row_count": len(lbls),
            "packet_raw_sha256": verify_mod.digest(p_raw),
            "packet_identity_set_sha256": idset,
            "exact_model": "Gemini 3.6 Flash (High)",
            "model_family": "google",
            "harness": "agy",
            "labels_sha256": verify_mod.digest(lp.read_bytes()),
            "text_free": True,
        }
        rcpt["receipt_sha256"] = verify_mod.digest(verify_mod.canonical(rcpt))
        rp = ldir / f"receipt-{idx:04d}.json"
        rp.write_text(json.dumps(rcpt, sort_keys=True) + "\n")
        rp.chmod(0o600)

    # 5. Compare outputs
    comp_dir = pkg / verify_mod.COMPARE_ROOT
    comp_rcpts = []
    # Clean lane compare
    c_clean_p = comp_dir / "clean_label" / "clean-consensus-0001.json"
    c_clean_p.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    c_clean_p.write_text(
        json.dumps({"records": [{"source_row": clean_rows[0], "label": grok_clean_labels[0]}]}, sort_keys=True) + "\n"
    )
    c_clean_p.chmod(0o600)

    c_risk_p = comp_dir / "clean_label" / "risk-consensus-0001.json"
    c_risk_p.write_text(json.dumps({"records": []}, sort_keys=True) + "\n")
    c_risk_p.chmod(0o600)

    c_disag_p = comp_dir / "clean_label" / "disagreements-0001.json"
    c_disag_p.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "source_row": clean_rows[1],
                        "grok_label": grok_clean_labels[1],
                        "gemini_label": gemini_clean_labels[1],
                    }
                ]
            },
            sort_keys=True,
        )
        + "\n"
    )
    c_disag_p.chmod(0o600)

    c_rcpt = {
        "schema_version": "phase3_cycle007_dual_label_packet_receipt_v1",
        "evaluation_cycle_id": verify_mod.CYCLE,
        "amendment_sha256": verify_mod.AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": custody_hash,
        "manifest_raw_sha256": manifest_hash,
        "ordered_identity_commitment_sha256": commitment,
        "lane": "clean_label",
        "packet_index": 1,
        "row_count": 2,
        "clean_consensus_sha256": verify_mod.digest(c_clean_p.read_bytes()),
        "risk_consensus_sha256": verify_mod.digest(c_risk_p.read_bytes()),
        "disagreements_sha256": verify_mod.digest(c_disag_p.read_bytes()),
        "text_free": True,
    }
    c_rcpt["receipt_sha256"] = verify_mod.digest(verify_mod.canonical(c_rcpt))
    c_rcpt_p = comp_dir / "clean_label" / "receipt-0001.json"
    c_rcpt_p.write_text(json.dumps(c_rcpt, sort_keys=True) + "\n")
    c_rcpt_p.chmod(0o600)
    comp_rcpts.append(c_rcpt)

    # Residual lane compare
    r_clean_p = comp_dir / "residual_label" / "clean-consensus-0001.json"
    r_clean_p.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    r_clean_p.write_text(
        json.dumps({"records": [{"source_row": residual_rows[0], "label": grok_res_labels[0]}]}, sort_keys=True) + "\n"
    )
    r_clean_p.chmod(0o600)

    r_risk_p = comp_dir / "residual_label" / "risk-consensus-0001.json"
    r_risk_p.write_text(
        json.dumps(
            {
                "records": [
                    {"source_row": residual_rows[1], "label": grok_res_labels[1], "risk_reasons": ["negative_control"]}
                ]
            },
            sort_keys=True,
        )
        + "\n"
    )
    r_risk_p.chmod(0o600)

    r_disag_p = comp_dir / "residual_label" / "disagreements-0001.json"
    r_disag_p.write_text(json.dumps({"records": []}, sort_keys=True) + "\n")
    r_disag_p.chmod(0o600)

    r_rcpt = {
        "schema_version": "phase3_cycle007_dual_label_packet_receipt_v1",
        "evaluation_cycle_id": verify_mod.CYCLE,
        "amendment_sha256": verify_mod.AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": custody_hash,
        "manifest_raw_sha256": manifest_hash,
        "ordered_identity_commitment_sha256": commitment,
        "lane": "residual_label",
        "packet_index": 1,
        "row_count": 2,
        "clean_consensus_sha256": verify_mod.digest(r_clean_p.read_bytes()),
        "risk_consensus_sha256": verify_mod.digest(r_risk_p.read_bytes()),
        "disagreements_sha256": verify_mod.digest(r_disag_p.read_bytes()),
        "text_free": True,
    }
    r_rcpt["receipt_sha256"] = verify_mod.digest(verify_mod.canonical(r_rcpt))
    r_rcpt_p = comp_dir / "residual_label" / "receipt-0001.json"
    r_rcpt_p.write_text(json.dumps(r_rcpt, sort_keys=True) + "\n")
    r_rcpt_p.chmod(0o600)
    comp_rcpts.append(r_rcpt)

    comp_batch = {
        "schema_version": "phase3_cycle007_dual_label_batch_receipt_v1",
        "evaluation_cycle_id": verify_mod.CYCLE,
        "packet_count": 2,
        "row_count": 4,
        "clean_consensus_count": 2,
        "risk_triggered_consensus_count": 1,
        "disagreement_count": 1,
        "packet_receipt_union_sha256": verify_mod.digest(
            verify_mod.canonical([c_rcpt["receipt_sha256"], r_rcpt["receipt_sha256"]])
        ),
        "text_free": True,
    }
    comp_batch["receipt_sha256"] = verify_mod.digest(verify_mod.canonical(comp_batch))
    (comp_dir / "batch-receipt.json").write_text(json.dumps(comp_batch, sort_keys=True) + "\n")
    (comp_dir / "batch-receipt.json").chmod(0o600)

    # 6. Consensus audit outputs
    audit_dir = pkg / verify_mod.AUDIT_ROOT
    audit_dir.mkdir(parents=True, mode=0o700)

    seed = verify_mod.digest(f"phase3-cycle007-consensus-audit-v1\n{custody_hash}{manifest_hash}{commitment}".encode())
    sample_recs = [
        {"source_row": clean_rows[0], "label": grok_clean_labels[0], "lane": "clean_label"},
        {"source_row": residual_rows[0], "label": grok_res_labels[0], "lane": "residual_label"},
    ]
    sample_sorted = sorted(
        sample_recs, key=lambda x: (x["lane"], x["source_row"]["unit_id"], x["source_row"]["unit_sha256"])
    )
    sample_comm = verify_mod.digest(
        verify_mod.canonical([(r["source_row"]["unit_id"], r["source_row"]["unit_sha256"]) for r in sample_sorted])
    )

    sample_doc = {
        "schema_version": "phase3_cycle007_clean_consensus_sample_v1",
        "evaluation_cycle_id": verify_mod.CYCLE,
        "seed": seed,
        "population_count": 2,
        "audited_count": 2,
        "one_sided_95_bound": 1.0 - (0.05 ** (1.0 / 2)),
        "sample_identity_commitment_sha256": sample_comm,
        "text_free": True,
    }
    sample_doc["receipt_sha256"] = verify_mod.digest(verify_mod.canonical(sample_doc))
    (audit_dir / "clean-consensus-sample.json").write_text(json.dumps(sample_doc, sort_keys=True) + "\n")
    (audit_dir / "clean-consensus-sample.json").chmod(0o600)

    risk_rcpt = {
        "schema_version": "phase3_cycle007_risk_review_receipt_v1",
        "evaluation_cycle_id": verify_mod.CYCLE,
        "risk_population_count": 1,
        "reviewed_count": 1,
        "terminal_findings_count": 0,
        "text_free": True,
    }
    risk_rcpt["receipt_sha256"] = verify_mod.digest(verify_mod.canonical(risk_rcpt))
    (audit_dir / "risk-review-receipt.json").write_text(json.dumps(risk_rcpt, sort_keys=True) + "\n")
    (audit_dir / "risk-review-receipt.json").chmod(0o600)

    clean_rcpt = {
        "schema_version": "phase3_cycle007_clean_audit_receipt_v1",
        "evaluation_cycle_id": verify_mod.CYCLE,
        "clean_population_count": 2,
        "audited_count": 2,
        "terminal_findings_count": 0,
        "text_free": True,
    }
    clean_rcpt["receipt_sha256"] = verify_mod.digest(verify_mod.canonical(clean_rcpt))
    (audit_dir / "clean-audit-receipt.json").write_text(json.dumps(clean_rcpt, sort_keys=True) + "\n")
    (audit_dir / "clean-audit-receipt.json").chmod(0o600)

    audit_batch = {
        "schema_version": "phase3_cycle007_consensus_audit_batch_receipt_v1",
        "evaluation_cycle_id": verify_mod.CYCLE,
        "clean_audited_count": 2,
        "one_sided_95_bound": sample_doc["one_sided_95_bound"],
        "terminal_findings_count": 0,
        "passed": True,
        "text_free": True,
    }
    audit_batch["receipt_sha256"] = verify_mod.digest(verify_mod.canonical(audit_batch))
    (audit_dir / "batch-receipt.json").write_text(json.dumps(audit_batch, sort_keys=True) + "\n")
    (audit_dir / "batch-receipt.json").chmod(0o600)

    # 7. Adjudication outputs
    adj_dir = pkg / verify_mod.ADJUDICATION_ROOT / "final"
    adj_rcpts = []

    # clean_label adjudication (adjudicating clean.1.1 with grok's label)
    adj_c_dir = adj_dir / "clean_label"
    adj_c_dir.mkdir(parents=True, mode=0o700)
    adj_c_lbl = adj_c_dir / "labels-0001.json"
    adj_c_lbl.write_text(json.dumps({"labels": [grok_clean_labels[1]]}, sort_keys=True) + "\n")
    adj_c_lbl.chmod(0o600)
    adj_c_unres = adj_c_dir / "unresolved-0001.json"
    adj_c_unres.write_text(json.dumps({"records": []}, sort_keys=True) + "\n")
    adj_c_unres.chmod(0o600)

    adj_c_rcpt = {
        "schema_version": "phase3_cycle007_dual_label_adjudication_packet_receipt_v1",
        "evaluation_cycle_id": verify_mod.CYCLE,
        "model_family": "anthropic",
        "labels_sha256": verify_mod.digest(adj_c_lbl.read_bytes()),
        "unresolved_sha256": verify_mod.digest(adj_c_unres.read_bytes()),
        "text_free": True,
    }
    adj_c_rcpt["receipt_sha256"] = verify_mod.digest(verify_mod.canonical(adj_c_rcpt))
    (adj_c_dir / "receipt-0001.json").write_text(json.dumps(adj_c_rcpt, sort_keys=True) + "\n")
    (adj_c_dir / "receipt-0001.json").chmod(0o600)
    adj_rcpts.append(adj_c_rcpt)

    # residual_label adjudication (empty)
    adj_r_dir = adj_dir / "residual_label"
    adj_r_dir.mkdir(parents=True, mode=0o700)
    adj_r_lbl = adj_r_dir / "labels-0001.json"
    adj_r_lbl.write_text(json.dumps({"labels": []}, sort_keys=True) + "\n")
    adj_r_lbl.chmod(0o600)
    adj_r_unres = adj_r_dir / "unresolved-0001.json"
    adj_r_unres.write_text(json.dumps({"records": []}, sort_keys=True) + "\n")
    adj_r_unres.chmod(0o600)

    adj_r_rcpt = {
        "schema_version": "phase3_cycle007_dual_label_adjudication_packet_receipt_v1",
        "evaluation_cycle_id": verify_mod.CYCLE,
        "model_family": "anthropic",
        "labels_sha256": verify_mod.digest(adj_r_lbl.read_bytes()),
        "unresolved_sha256": verify_mod.digest(adj_r_unres.read_bytes()),
        "text_free": True,
    }
    adj_r_rcpt["receipt_sha256"] = verify_mod.digest(verify_mod.canonical(adj_r_rcpt))
    (adj_r_dir / "receipt-0001.json").write_text(json.dumps(adj_r_rcpt, sort_keys=True) + "\n")
    (adj_r_dir / "receipt-0001.json").chmod(0o600)
    adj_rcpts.append(adj_r_rcpt)

    adj_batch = {
        "schema_version": "phase3_cycle007_dual_label_adjudication_batch_receipt_v1",
        "evaluation_cycle_id": verify_mod.CYCLE,
        "model_family": "anthropic",
        "total_disagreements": 1,
        "total_adjudicated": 1,
        "total_unresolved": 0,
        "packet_receipt_union_sha256": verify_mod.digest(
            verify_mod.canonical([adj_c_rcpt["receipt_sha256"], adj_r_rcpt["receipt_sha256"]])
        ),
        "text_free": True,
    }
    adj_batch["receipt_sha256"] = verify_mod.digest(verify_mod.canonical(adj_batch))
    (pkg / verify_mod.ADJUDICATION_ROOT / "batch-receipt.json").write_text(json.dumps(adj_batch, sort_keys=True) + "\n")
    (pkg / verify_mod.ADJUDICATION_ROOT / "batch-receipt.json").chmod(0o600)

    # 8. Resolution output (Final Labels)
    res_dir = pkg / verify_mod.RESOLUTION_ROOT
    res_rcpts = []

    # Final clean_label
    res_c_dir = res_dir / "final" / "clean_label"
    res_c_dir.mkdir(parents=True, mode=0o700)
    res_c_lbl = res_c_dir / "labels-0001.json"
    res_c_lbl.write_text(json.dumps({"labels": [grok_clean_labels[0], grok_clean_labels[1]]}, sort_keys=True) + "\n")
    res_c_lbl.chmod(0o600)
    res_c_dec = res_c_dir / "decisions-0001.json"
    res_c_dec.write_text(
        json.dumps({"decisions": [{"origin": "consensus"}, {"origin": "adjudication"}]}, sort_keys=True) + "\n"
    )
    res_c_dec.chmod(0o600)

    res_c_rcpt = {
        "schema_version": "phase3_cycle007_operator_resolution_packet_receipt_v1",
        "evaluation_cycle_id": verify_mod.CYCLE,
        "labels_sha256": verify_mod.digest(res_c_lbl.read_bytes()),
        "decisions_sha256": verify_mod.digest(res_c_dec.read_bytes()),
        "unresolved_remaining_count": 0,
        "text_free": True,
    }
    res_c_rcpt["receipt_sha256"] = verify_mod.digest(verify_mod.canonical(res_c_rcpt))
    (res_c_dir / "receipt-0001.json").write_text(json.dumps(res_c_rcpt, sort_keys=True) + "\n")
    (res_c_dir / "receipt-0001.json").chmod(0o600)
    res_rcpts.append(res_c_rcpt)

    # Final residual_label
    res_r_dir = res_dir / "final" / "residual_label"
    res_r_dir.mkdir(parents=True, mode=0o700)
    res_r_lbl = res_r_dir / "labels-0001.json"
    res_r_lbl.write_text(json.dumps({"labels": [grok_res_labels[0], grok_res_labels[1]]}, sort_keys=True) + "\n")
    res_r_lbl.chmod(0o600)
    res_r_dec = res_r_dir / "decisions-0001.json"
    res_r_dec.write_text(
        json.dumps({"decisions": [{"origin": "consensus"}, {"origin": "risk_consensus"}]}, sort_keys=True) + "\n"
    )
    res_r_dec.chmod(0o600)

    res_r_rcpt = {
        "schema_version": "phase3_cycle007_operator_resolution_packet_receipt_v1",
        "evaluation_cycle_id": verify_mod.CYCLE,
        "labels_sha256": verify_mod.digest(res_r_lbl.read_bytes()),
        "decisions_sha256": verify_mod.digest(res_r_dec.read_bytes()),
        "unresolved_remaining_count": 0,
        "text_free": True,
    }
    res_r_rcpt["receipt_sha256"] = verify_mod.digest(verify_mod.canonical(res_r_rcpt))
    (res_r_dir / "receipt-0001.json").write_text(json.dumps(res_r_rcpt, sort_keys=True) + "\n")
    (res_r_dir / "receipt-0001.json").chmod(0o600)
    res_rcpts.append(res_r_rcpt)

    res_batch = {
        "schema_version": "phase3_cycle007_operator_resolution_batch_receipt_v1",
        "evaluation_cycle_id": verify_mod.CYCLE,
        "packet_count": 2,
        "total_rows": 4,
        "unresolved_remaining_count": 0,
        "packet_receipt_union_sha256": verify_mod.digest(
            verify_mod.canonical([res_c_rcpt["receipt_sha256"], res_r_rcpt["receipt_sha256"]])
        ),
        "text_free": True,
    }
    res_batch["receipt_sha256"] = verify_mod.digest(verify_mod.canonical(res_batch))
    (res_dir / "batch-receipt.json").write_text(json.dumps(res_batch, sort_keys=True) + "\n")
    (res_dir / "batch-receipt.json").chmod(0o600)

    for directory in [pkg, *(path for path in pkg.rglob("*") if path.is_dir())]:
        directory.chmod(0o700)
    return pkg


def test_certifier_successful_exact_fixture_closure(tmp_path):
    pkg = _setup_certified_package(tmp_path)
    cert = verify_mod.certify_completion(pkg, fixture=True)
    assert cert["schema_version"] == "phase3_cycle007_label_completion_receipt_v1"
    assert cert["clean_consensus_count"] == 2
    assert cert["risk_triggered_consensus_count"] == 1
    assert cert["disagreement_count"] == 1
    assert cert["audited_consensus_count"] == 2
    assert cert["unresolved_remaining_count"] == 0
    assert cert["terminal_findings_count"] == 0
    assert cert["text_free"] is True
    assert (pkg / verify_mod.RESOLUTION_ROOT / "certification-receipt.json").exists()


def test_certifier_fails_on_permission_drift(tmp_path):
    pkg = _setup_certified_package(tmp_path)
    (pkg / "manifest.json").chmod(0o644)

    with pytest.raises(verify_mod.Error) as exc:
        verify_mod.certify_completion(pkg, fixture=True)
    assert exc.value.failure_code == "package_modes"


def test_certifier_fails_on_stop_residue(tmp_path):
    pkg = _setup_certified_package(tmp_path)
    stop_file = pkg / verify_mod.GROK_ROOT / "provider-stop.json"
    stop_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    stop_file.write_text("{}\n")
    stop_file.chmod(0o600)

    with pytest.raises(verify_mod.Error) as exc:
        verify_mod.certify_completion(pkg, fixture=True)
    assert exc.value.failure_code == "no_provider_stop"


def test_certifier_fails_on_missing_provider_packet(tmp_path):
    pkg = _setup_certified_package(tmp_path)
    (pkg / verify_mod.GROK_ROOT / "clean_label" / "labels-0001.json").unlink()

    with pytest.raises(verify_mod.Error) as exc:
        verify_mod.certify_completion(pkg, fixture=True)
    assert exc.value.failure_code == "provider_receipt_coverage"


def test_certifier_fails_on_wrong_provider_model(tmp_path):
    pkg = _setup_certified_package(tmp_path)
    rcpt_p = pkg / verify_mod.GROK_ROOT / "clean_label" / "receipt-0001.json"
    rcpt = json.loads(rcpt_p.read_text())
    rcpt["exact_model"] = "grok-4.0"  # Expected grok-4.5
    rcpt["receipt_sha256"] = verify_mod.digest(
        verify_mod.canonical({k: v for k, v in rcpt.items() if k != "receipt_sha256"})
    )
    rcpt_p.write_text(json.dumps(rcpt) + "\n")

    with pytest.raises(verify_mod.Error) as exc:
        verify_mod.certify_completion(pkg, fixture=True)
    assert exc.value.failure_code == "provider_receipt_coverage"


def test_certifier_fails_on_forged_comparison_receipt_counts_or_hashes(tmp_path):
    pkg = _setup_certified_package(tmp_path)
    comp_batch_p = pkg / verify_mod.COMPARE_ROOT / "batch-receipt.json"
    comp_batch = json.loads(comp_batch_p.read_text())
    comp_batch["clean_consensus_count"] = 999  # Forged count
    comp_batch["receipt_sha256"] = verify_mod.digest(
        verify_mod.canonical({k: v for k, v in comp_batch.items() if k != "receipt_sha256"})
    )
    comp_batch_p.write_text(json.dumps(comp_batch) + "\n")

    with pytest.raises(verify_mod.Error) as exc:
        verify_mod.certify_completion(pkg, fixture=True)
    assert exc.value.failure_code == "comparison_batch_receipt"


def test_certifier_fails_on_incomplete_risk_review(tmp_path):
    pkg = _setup_certified_package(tmp_path)
    risk_p = pkg / verify_mod.AUDIT_ROOT / "risk-review-receipt.json"
    risk_rcpt = json.loads(risk_p.read_text())
    risk_rcpt["reviewed_count"] = 0  # Incomplete review
    risk_rcpt["receipt_sha256"] = verify_mod.digest(
        verify_mod.canonical({k: v for k, v in risk_rcpt.items() if k != "receipt_sha256"})
    )
    risk_p.write_text(json.dumps(risk_rcpt) + "\n")

    with pytest.raises(verify_mod.Error) as exc:
        verify_mod.certify_completion(pkg, fixture=True)
    assert exc.value.failure_code == "risk_review_incomplete"


def test_certifier_fails_on_incomplete_sample_audit(tmp_path):
    pkg = _setup_certified_package(tmp_path)
    clean_p = pkg / verify_mod.AUDIT_ROOT / "clean-audit-receipt.json"
    clean_rcpt = json.loads(clean_p.read_text())
    clean_rcpt["audited_count"] = 0  # Incomplete sample
    clean_rcpt["receipt_sha256"] = verify_mod.digest(
        verify_mod.canonical({k: v for k, v in clean_rcpt.items() if k != "receipt_sha256"})
    )
    clean_p.write_text(json.dumps(clean_rcpt) + "\n")

    with pytest.raises(verify_mod.Error) as exc:
        verify_mod.certify_completion(pkg, fixture=True)
    assert exc.value.failure_code == "sample_audit_incomplete"


def test_certifier_fails_on_terminal_audit_finding(tmp_path):
    pkg = _setup_certified_package(tmp_path)
    audit_batch_p = pkg / verify_mod.AUDIT_ROOT / "batch-receipt.json"
    audit_batch = json.loads(audit_batch_p.read_text())
    audit_batch["terminal_findings_count"] = 1
    audit_batch["passed"] = False
    audit_batch["receipt_sha256"] = verify_mod.digest(
        verify_mod.canonical({k: v for k, v in audit_batch.items() if k != "receipt_sha256"})
    )
    audit_batch_p.write_text(json.dumps(audit_batch) + "\n")

    with pytest.raises(verify_mod.Error) as exc:
        verify_mod.certify_completion(pkg, fixture=True)
    assert exc.value.failure_code == "terminal_audit_finding"


def test_certifier_fails_on_adjudication_mismatch(tmp_path):
    pkg = _setup_certified_package(tmp_path)
    adj_lbl_p = pkg / verify_mod.ADJUDICATION_ROOT / "final" / "clean_label" / "labels-0001.json"
    # Invent a third label not present in grok or gemini
    invented = [
        {
            "unit_id": "clean.1.1",
            "unit_sha256": "11" + "0" * 62,
            "decision_code": "reject_exercise_or_task_prompt",
            "clean_modern_standard_prose": False,
            "modern_genre_id": None,
            "evidence_ids": [],
        }
    ]
    adj_lbl_p.write_text(json.dumps({"labels": invented}, sort_keys=True) + "\n")
    adj_rcpt_p = pkg / verify_mod.ADJUDICATION_ROOT / "final" / "clean_label" / "receipt-0001.json"
    rcpt = json.loads(adj_rcpt_p.read_text())
    rcpt["labels_sha256"] = verify_mod.digest(adj_lbl_p.read_bytes())
    rcpt["receipt_sha256"] = verify_mod.digest(
        verify_mod.canonical({k: v for k, v in rcpt.items() if k != "receipt_sha256"})
    )
    adj_rcpt_p.write_text(json.dumps(rcpt) + "\n")

    with pytest.raises(verify_mod.Error) as exc:
        verify_mod.certify_completion(pkg, fixture=True)
    assert exc.value.failure_code == "adjudication_candidate_partition"


def test_certifier_fails_on_final_label_tamper(tmp_path):
    pkg = _setup_certified_package(tmp_path)
    final_lbl_p = pkg / verify_mod.RESOLUTION_ROOT / "final" / "clean_label" / "labels-0001.json"
    data = json.loads(final_lbl_p.read_text())
    data["labels"][0]["modern_genre_id"] = "invalid_genre"  # Tampered genre
    final_lbl_p.write_text(json.dumps(data, sort_keys=True) + "\n")
    res_rcpt_p = pkg / verify_mod.RESOLUTION_ROOT / "final" / "clean_label" / "receipt-0001.json"
    rcpt = json.loads(res_rcpt_p.read_text())
    rcpt["labels_sha256"] = verify_mod.digest(final_lbl_p.read_bytes())
    rcpt["receipt_sha256"] = verify_mod.digest(
        verify_mod.canonical({k: v for k, v in rcpt.items() if k != "receipt_sha256"})
    )
    res_rcpt_p.write_text(json.dumps(rcpt) + "\n")

    with pytest.raises(verify_mod.Error) as exc:
        verify_mod.certify_completion(pkg, fixture=True)
    assert exc.value.failure_code == "final_identity_union"


def test_certifier_fails_on_unresolved_remaining(tmp_path):
    pkg = _setup_certified_package(tmp_path)
    res_batch_p = pkg / verify_mod.RESOLUTION_ROOT / "batch-receipt.json"
    res_batch = json.loads(res_batch_p.read_text())
    res_batch["unresolved_remaining_count"] = 1
    res_batch["receipt_sha256"] = verify_mod.digest(
        verify_mod.canonical({k: v for k, v in res_batch.items() if k != "receipt_sha256"})
    )
    res_batch_p.write_text(json.dumps(res_batch) + "\n")

    with pytest.raises(verify_mod.Error) as exc:
        verify_mod.certify_completion(pkg, fixture=True)
    assert exc.value.failure_code == "final_residual_zero"


def test_certifier_fails_on_partition_overlap_or_omission(tmp_path):
    pkg = _setup_certified_package(tmp_path)
    # Put clean.1.1 in clean_consensus as well as disagreements
    clean_p = pkg / verify_mod.COMPARE_ROOT / "clean_label" / "clean-consensus-0001.json"
    data = json.loads(clean_p.read_text())
    data["records"].append(
        {
            "source_row": {"unit_id": "clean.1.1", "unit_sha256": "11" + "0" * 62, "clean_modern_standard_prose": True},
            "label": {
                "unit_id": "clean.1.1",
                "unit_sha256": "11" + "0" * 62,
                "decision_code": "agree",
                "clean_modern_standard_prose": True,
                "modern_genre_id": "expository_narrative",
                "evidence_ids": [],
            },
        }
    )
    clean_p.write_text(json.dumps(data, sort_keys=True) + "\n")
    comp_rcpt_p = pkg / verify_mod.COMPARE_ROOT / "clean_label" / "receipt-0001.json"
    rcpt = json.loads(comp_rcpt_p.read_text())
    rcpt["clean_consensus_sha256"] = verify_mod.digest(clean_p.read_bytes())
    rcpt["receipt_sha256"] = verify_mod.digest(
        verify_mod.canonical({k: v for k, v in rcpt.items() if k != "receipt_sha256"})
    )
    comp_rcpt_p.write_text(json.dumps(rcpt) + "\n")

    with pytest.raises(verify_mod.Error) as exc:
        verify_mod.certify_completion(pkg, fixture=True)
    assert exc.value.failure_code == "comparison_receipts"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
