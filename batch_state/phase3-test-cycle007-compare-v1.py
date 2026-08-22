#!/usr/bin/env python3
"""Synthetic tests for Phase 3 Cycle 007 dual label comparator."""

from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_cycle007_evidence_compiler as compiler
from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract

HERE = Path(__file__).resolve().parent
COMPARE_PATH = HERE / "phase3-compare-cycle007-dual-labels-v1.py"


def _load_compare():
    spec = importlib.util.spec_from_file_location("compare_mod", COMPARE_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


compare_mod = _load_compare()


CURRENT_CODE_HASHES = compiler.CODE_HASHES
TOKENIZER_ID = compiler.TOKENIZER_ID
TOKENIZER_VERSION = compiler.TOKENIZER_VERSION
SERVER_CODE_SHA256 = "a" * 64
SOURCES_DB_SHA256 = "b" * 64
VESUM_DB_SHA256 = "c" * 64


def _private_tree(package: Path) -> None:
    for directory in [package, *(path for path in package.rglob("*") if path.is_dir())]:
        directory.chmod(0o700)


def _row_evidence(row, records, phenomenon_evidence_ids):
    return {
        "unit_id": row["unit_id"],
        "unit_sha256": row["unit_sha256"],
        "tokenizer_id": TOKENIZER_ID,
        "tokenizer_version": TOKENIZER_VERSION,
        "extracted_forms": [],
        "evidence": records,
        "evidence_ids": sorted(record["evidence_id"] for record in records),
        "phenomenon_evidence_ids": phenomenon_evidence_ids,
        "sufficient_support": any(contract.is_sufficient_positive(record) for record in records),
        "archaic_only_risk": contract.is_archaic_only_risk(records),
        "russian_shadow_suspected": any(
            record["channel"] == "russian_shadow_suspicion" and record["status"] == "attested"
            for record in records
        ),
    }


def _make_fixture_package(tmp_path: Path, *, clean_rows=2, residual_rows=2, is_negative_control=False):
    pkg = tmp_path / "pkg"
    pkg.mkdir(parents=True, mode=0o700)

    clean_row_list = [
        {
            "unit_id": f"clean-{i}",
            "unit_sha256": f"{i:02d}" + "a" * 62,
            "clean_modern_standard_prose": True,
            **({"is_negative_control": True} if is_negative_control and i == 1 else {}),
        }
        for i in range(1, clean_rows + 1)
    ]
    residual_row_list = [
        {"unit_id": f"residual-{i}", "unit_sha256": f"{i:02d}" + "b" * 62, "family_id": "standard"}
        for i in range(1, residual_rows + 1)
    ]

    clean_id_set = compare_mod.digest(compare_mod.canonical(sorted((r["unit_id"], r["unit_sha256"]) for r in clean_row_list)))
    res_id_set = compare_mod.digest(compare_mod.canonical(sorted((r["unit_id"], r["unit_sha256"]) for r in residual_row_list)))

    # Materialization manifest & packets
    clean_dir = pkg / "clean_label"
    clean_dir.mkdir(parents=True, mode=0o700)
    res_dir = pkg / "residual_label"
    res_dir.mkdir(parents=True, mode=0o700)

    clean_p1 = clean_dir / "packet-0001.json"
    clean_p1.write_text(json.dumps({"packet_identity_set_sha256": clean_id_set, "rows": clean_row_list}) + "\n")
    clean_p1.chmod(0o600)

    res_p1 = res_dir / "packet-0001.json"
    res_p1.write_text(json.dumps({"packet_identity_set_sha256": res_id_set, "rows": residual_row_list}) + "\n")
    res_p1.chmod(0o600)

    packets_meta = [
        {
            "lane": "clean_label",
            "packet_index": 1,
            "canonical_basename": "packet-0001.json",
            "row_count": clean_rows,
            "raw_sha256": compare_mod.digest(clean_p1.read_bytes()),
            "packet_identity_set_sha256": clean_id_set,
        },
        {
            "lane": "residual_label",
            "packet_index": 1,
            "canonical_basename": "packet-0001.json",
            "row_count": residual_rows,
            "raw_sha256": compare_mod.digest(res_p1.read_bytes()),
            "packet_identity_set_sha256": res_id_set,
        },
    ]
    identity_union_commitment = compare_mod.digest(
        compare_mod.canonical(
            sorted(
                (row["unit_id"], row["unit_sha256"])
                for row in [*clean_row_list, *residual_row_list]
            )
        )
    )
    ordered_packet_commitment = compare_mod.digest(compare_mod.canonical(packets_meta))

    manifest = {
        "schema_version": "phase3_cycle007_materialization_manifest_v1",
        "evaluation_cycle_id": compare_mod.CYCLE,
        "source_evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-005",
        "text_free": True,
        "custody_receipt_raw_sha256": "",
        "ordered_identity_commitment_sha256": compare_mod.ORDERED_IDENTITY_COMMITMENT_SHA256,
        "identity_union_commitment_sha256": identity_union_commitment,
        "ordered_packet_commitment_sha256": ordered_packet_commitment,
        "packet_count": len(packets_meta),
        "row_count": clean_rows + residual_rows,
        "lane_row_counts": {"clean_label": clean_rows, "residual_label": residual_rows},
        "packets": packets_meta,
    }

    custody = {
        "schema_version": "phase3_cycle007_custody_receipt_v1",
        "evaluation_cycle_id": compare_mod.CYCLE,
        "source_evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-005",
        "amendment_reference": "batch_state/phase3-cycle007-source-grounded-amendment-v1.md",
        "source_custody_receipt_raw_sha256": compare_mod.SOURCE_CUSTODY_SHA256,
        "source_label_manifest_raw_sha256": compare_mod.SOURCE_MANIFEST_SHA256,
        "ordered_identity_commitment_sha256": compare_mod.ORDERED_IDENTITY_COMMITMENT_SHA256,
        "identity_union_commitment_sha256": identity_union_commitment,
        "ordered_packet_commitment_sha256": ordered_packet_commitment,
        "packet_count": len(packets_meta),
        "row_count": clean_rows + residual_rows,
        "lane_row_counts": {"clean_label": clean_rows, "residual_label": residual_rows},
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

    manifest["custody_receipt_raw_sha256"] = compare_mod.digest(custody_p.read_bytes())
    manifest_p = pkg / "manifest.json"
    manifest_p.write_text(json.dumps(manifest, sort_keys=True) + "\n")
    manifest_p.chmod(0o600)
    manifest["receipt_sha256"] = compare_mod.digest(compare_mod.canonical(manifest))
    manifest_p.write_text(json.dumps(manifest, sort_keys=True) + "\n")
    manifest_p.chmod(0o600)

    # Evidence setup
    evidence_dir = pkg / "evidence"
    evidence_dir.mkdir(parents=True, mode=0o700)

    # Build sidecars
    retrieval_payload = {"test": "payload"}
    r_sha = contract.sha256_value(retrieval_payload)
    retrieval_payloads = {r_sha: retrieval_payload}

    clean_ev_rows = []
    for r in clean_row_list:
        rec = contract.build_evidence_record(
            channel="vesum_attestation",
            source_identity="vesum",
            source_version="v1",
            locator="locator",
            query="form",
            status="attested",
            supports="attestation",
            retrieval_sha256=r_sha,
            parser_id="p1",
            parser_version="1",
            row=r,
        )
        clean_ev_rows.append(_row_evidence(r, [rec], {}))

    clean_sidecar = {
        "schema_version": "phase3_cycle007_evidence_sidecar_v1",
        "evaluation_cycle_id": compare_mod.CYCLE,
        "lane": "clean_label",
        "packet_binding": {
            "canonical_basename": "packet-0001.json",
            "raw_sha256": packets_meta[0]["raw_sha256"],
            "packet_identity_set_sha256": packets_meta[0]["packet_identity_set_sha256"],
        },
        "packet_index": 1,
        "row_count": clean_rows,
        "tokenizer_id": TOKENIZER_ID,
        "tokenizer_version": TOKENIZER_VERSION,
        "code_hashes": CURRENT_CODE_HASHES,
        "server_code_sha256": SERVER_CODE_SHA256,
        "sources_db_sha256": SOURCES_DB_SHA256,
        "vesum_db_sha256": VESUM_DB_SHA256,
        "network_lookups_performed": 0,
        "rows": clean_ev_rows,
        "retrieval_payloads": retrieval_payloads,
    }
    clean_sidecar["sidecar_id"] = "cycle007_sidecar:" + contract.sha256_value(clean_sidecar)
    s1_p = evidence_dir / "sidecar-0001.json"
    s1_p.write_text(json.dumps(clean_sidecar, sort_keys=True) + "\n")
    s1_p.chmod(0o600)

    # Residual sidecar
    res_ev_rows = []
    for r in residual_row_list:
        records = [
            contract.build_evidence_record(
                channel="vesum_attestation",
                source_identity="vesum",
                source_version="v1",
                locator="locator",
                query="form",
                status="attested",
                supports="attestation",
                retrieval_sha256=r_sha,
                parser_id="p1",
                parser_version="1",
                row=r,
                phenomenon_id=phenomenon_id,
            )
            for phenomenon_id in contract.RESIDUAL_PHENOMENON_TAXONOMY
        ]
        phenom_map = {record["phenomenon_id"]: [record["evidence_id"]] for record in records}
        res_ev_rows.append(_row_evidence(r, records, phenom_map))

    res_sidecar = {
        "schema_version": "phase3_cycle007_evidence_sidecar_v1",
        "evaluation_cycle_id": compare_mod.CYCLE,
        "lane": "residual_label",
        "packet_binding": {
            "canonical_basename": "packet-0001.json",
            "raw_sha256": packets_meta[1]["raw_sha256"],
            "packet_identity_set_sha256": packets_meta[1]["packet_identity_set_sha256"],
        },
        "packet_index": 2,
        "row_count": residual_rows,
        "tokenizer_id": TOKENIZER_ID,
        "tokenizer_version": TOKENIZER_VERSION,
        "code_hashes": CURRENT_CODE_HASHES,
        "server_code_sha256": SERVER_CODE_SHA256,
        "sources_db_sha256": SOURCES_DB_SHA256,
        "vesum_db_sha256": VESUM_DB_SHA256,
        "network_lookups_performed": 0,
        "rows": res_ev_rows,
        "retrieval_payloads": retrieval_payloads,
    }
    res_sidecar["sidecar_id"] = "cycle007_sidecar:" + contract.sha256_value(res_sidecar)
    s2_p = evidence_dir / "sidecar-0002.json"
    s2_p.write_text(json.dumps(res_sidecar, sort_keys=True) + "\n")
    s2_p.chmod(0o600)

    # Evidence manifest
    all_ev_rows = [*clean_ev_rows, *res_ev_rows]
    all_records = [record for row in all_ev_rows for record in row["evidence"]]
    counts_by_channel = dict(
        sorted(Counter(record["channel"] for record in all_records).items())
    )
    counts_by_status = dict(sorted(Counter(record["status"] for record in all_records).items()))
    counts_by_supports = dict(sorted(Counter(record["supports"] for record in all_records).items()))
    ev_manifest = {
        "schema_version": "phase3_cycle007_evidence_manifest_v1",
        "text_free": True,
        "evaluation_cycle_id": compare_mod.CYCLE,
        "tokenizer_id": TOKENIZER_ID,
        "tokenizer_version": TOKENIZER_VERSION,
        "code_hashes": CURRENT_CODE_HASHES,
        "server_code_sha256": SERVER_CODE_SHA256,
        "sources_db_sha256": SOURCES_DB_SHA256,
        "vesum_db_sha256": VESUM_DB_SHA256,
        "packet_count": 2,
        "row_count": clean_rows + residual_rows,
        "network_lookups_performed": 0,
        "counts_by_channel": counts_by_channel,
        "counts_by_status": counts_by_status,
        "counts_by_supports": counts_by_supports,
        "sufficient_support_rows": sum(row["sufficient_support"] for row in all_ev_rows),
        "archaic_only_risk_rows": sum(row["archaic_only_risk"] for row in all_ev_rows),
        "russian_shadow_suspected_rows": sum(row["russian_shadow_suspected"] for row in all_ev_rows),
        "sidecars": [
            {
                "packet_index": 1,
                "row_count": clean_rows,
                "sidecar_sha256": compare_mod.digest(s1_p.read_bytes()),
                "sidecar_id": clean_sidecar["sidecar_id"],
                "lane": "clean_label",
                "packet_binding": clean_sidecar["packet_binding"],
            },
            {
                "packet_index": 2,
                "row_count": residual_rows,
                "sidecar_sha256": compare_mod.digest(s2_p.read_bytes()),
                "sidecar_id": res_sidecar["sidecar_id"],
                "lane": "residual_label",
                "packet_binding": res_sidecar["packet_binding"],
            },
        ],
        "source_package_binding": {
            "source_evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-005",
            "custody_receipt_raw_sha256": compare_mod.digest(custody_p.read_bytes()),
            "materialization_manifest_sha256": manifest["receipt_sha256"],
            "ordered_identity_commitment_sha256": manifest["ordered_identity_commitment_sha256"],
            "identity_union_commitment_sha256": manifest["identity_union_commitment_sha256"],
            "ordered_packet_commitment_sha256": manifest["ordered_packet_commitment_sha256"],
            "packet_count": manifest["packet_count"],
            "row_count": manifest["row_count"],
        },
        "mcp_transport_attestation": None,
    }
    ev_manifest["manifest_sha256"] = contract.sha256_value(ev_manifest)
    ev_manifest_p = evidence_dir / "manifest.json"
    ev_manifest_p.write_text(json.dumps(ev_manifest, sort_keys=True) + "\n")
    ev_manifest_p.chmod(0o600)

    _private_tree(pkg)
    return pkg, clean_row_list, residual_row_list, clean_ev_rows, res_ev_rows


def _setup_provider_labels(pkg: Path, lane: str, index: int, grok_labels: list, gemini_labels: list):
    for provider, labels, schema_name in [
        (compare_mod.GROK, grok_labels, "phase3_cycle007_grok_packet_label_receipt_v1"),
        (compare_mod.GEMINI, gemini_labels, "phase3_cycle007_gemini_packet_label_receipt_v1"),
    ]:
        out = pkg / provider["root"] / lane
        out.mkdir(parents=True, exist_ok=True, mode=0o700)
        lbl_p = out / f"labels-{index:04d}.json"
        lbl_p.write_text(json.dumps({"labels": labels}, sort_keys=True) + "\n")
        lbl_p.chmod(0o600)

        packet_p = pkg / lane / f"packet-{index:04d}.json"
        packet_contents = compare_mod.read(packet_p, "packet")
        evidence_manifest = compare_mod.read(pkg / "evidence" / "manifest.json", "evidence manifest")
        sidecar_entry = next(
            entry
            for entry in evidence_manifest["sidecars"]
            if entry["lane"] == lane
            and entry["packet_binding"]["raw_sha256"] == compare_mod.digest(packet_p.read_bytes())
        )
        sidecar_p = pkg / "evidence" / f"sidecar-{sidecar_entry['packet_index']:04d}.json"
        raw_manifest_p = out / f"raw-manifest-{index:04d}.json"
        raw_manifest_p.write_text(json.dumps({"synthetic": provider["root"]}, sort_keys=True) + "\n")
        raw_manifest_p.chmod(0o600)
        receipt = {
            "schema_version": schema_name,
            "evaluation_cycle_id": compare_mod.CYCLE,
            "amendment_sha256": compare_mod.AMENDMENT_SHA256,
            "custody_receipt_raw_sha256": compare_mod.digest((pkg / "custody-receipt.json").read_bytes()),
            "materialization_manifest_raw_sha256": compare_mod.digest((pkg / "manifest.json").read_bytes()),
            "evidence_manifest_raw_sha256": compare_mod.digest((pkg / "evidence" / "manifest.json").read_bytes()),
            "lane": lane,
            "packet_index": index,
            "row_count": len(labels),
            "packet_raw_sha256": compare_mod.digest(packet_p.read_bytes()),
            "packet_identity_set_sha256": packet_contents.get("packet_identity_set_sha256"),
            "sidecar_raw_sha256": compare_mod.digest(sidecar_p.read_bytes()),
            "sidecar_id": sidecar_entry["sidecar_id"],
            "raw_manifest_sha256": compare_mod.digest(raw_manifest_p.read_bytes()),
            "labels_sha256": compare_mod.digest(lbl_p.read_bytes()),
            "exact_model": provider["exact_model"],
            "model_family": provider["model_family"],
            "harness": provider["harness"],
            "text_free": True,
        }
        if provider is compare_mod.GROK:
            raw_p = out / f"raw-{index:04d}.raw"
            raw_p.write_bytes(b"{}\n")
            raw_p.chmod(0o600)
            prompt_p = pkg / "prompts" / f"grok-{'clean' if lane == 'clean_label' else 'residual'}-label.md"
            prompt_p.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            prompt_p.write_text("synthetic fixture\n")
            prompt_p.chmod(0o600)
            receipt.update(
                {
                    "response_raw_sha256": compare_mod.digest(raw_p.read_bytes()),
                    "prompt_path": prompt_p.relative_to(pkg).as_posix(),
                    "prompt_sha256": compare_mod.digest(prompt_p.read_bytes()),
                    "attempt_count": 1,
                }
            )
        else:
            receipt["chunk_count"] = (len(labels) + compare_mod.CHUNK_SIZE - 1) // compare_mod.CHUNK_SIZE
        receipt["receipt_sha256"] = compare_mod.digest(compare_mod.canonical(receipt))
        rcpt_p = out / f"receipt-{index:04d}.json"
        rcpt_p.write_text(json.dumps(receipt, sort_keys=True) + "\n")
        rcpt_p.chmod(0o600)
    _private_tree(pkg)


def test_compare_refuses_to_run_without_both_provider_seals(tmp_path):
    pkg, clean_rows, _, clean_ev, _ = _make_fixture_package(tmp_path)
    # Only Grok is setup
    grok_labels = [
        {
            "unit_id": r["unit_id"],
            "unit_sha256": r["unit_sha256"],
            "decision_code": "agree",
            "clean_modern_standard_prose": True,
            "modern_genre_id": "expository_narrative",
            "evidence_ids": clean_ev[i]["evidence_ids"],
        }
        for i, r in enumerate(clean_rows)
    ]
    out = pkg / compare_mod.GROK["root"] / "clean_label"
    out.mkdir(parents=True, exist_ok=True, mode=0o700)
    lbl_p = out / "labels-0001.json"
    lbl_p.write_text(json.dumps({"labels": grok_labels}) + "\n")
    lbl_p.chmod(0o600)
    _private_tree(pkg)

    with pytest.raises(compare_mod.Error) as exc:
        compare_mod.compare(pkg, "clean_label", 1)
    assert exc.value.failure_code == "label_count_or_envelope_drift"


def test_compare_partitions_clean_consensus_risk_consensus_and_disagreements(tmp_path):
    pkg, clean_rows, _, clean_ev, _ = _make_fixture_package(tmp_path, clean_rows=2)

    # Row 1: Consensus clean
    # Row 2: Disagreement
    grok_labels = [
        {
            "unit_id": clean_rows[0]["unit_id"],
            "unit_sha256": clean_rows[0]["unit_sha256"],
            "decision_code": "agree",
            "clean_modern_standard_prose": True,
            "modern_genre_id": "expository_narrative",
            "evidence_ids": clean_ev[0]["evidence_ids"],
        },
        {
            "unit_id": clean_rows[1]["unit_id"],
            "unit_sha256": clean_rows[1]["unit_sha256"],
            "decision_code": "agree",
            "clean_modern_standard_prose": True,
            "modern_genre_id": "scientific_expository",
            "evidence_ids": clean_ev[1]["evidence_ids"],
        },
    ]
    gemini_labels = [
        {
            "unit_id": clean_rows[0]["unit_id"],
            "unit_sha256": clean_rows[0]["unit_sha256"],
            "decision_code": "agree",
            "clean_modern_standard_prose": True,
            "modern_genre_id": "expository_narrative",
            "evidence_ids": clean_ev[0]["evidence_ids"],
        },
        {
            "unit_id": clean_rows[1]["unit_id"],
            "unit_sha256": clean_rows[1]["unit_sha256"],
            "decision_code": "reject_fragment_or_too_short",
            "clean_modern_standard_prose": False,
            "modern_genre_id": None,
            "evidence_ids": [],
        },
    ]

    _setup_provider_labels(pkg, "clean_label", 1, grok_labels, gemini_labels)
    result = compare_mod.compare(pkg, "clean_label", 1)

    assert result["clean_consensus_count"] == 1
    assert result["risk_triggered_consensus_count"] == 0
    assert result["disagreement_count"] == 1

    clean_file = pkg / compare_mod.OUTPUT / "clean_label" / "clean-consensus-0001.json"
    disagreements_file = pkg / compare_mod.OUTPUT / "clean_label" / "disagreements-0001.json"
    assert clean_file.exists()
    assert disagreements_file.exists()


def test_compare_risk_triggers_on_negative_control(tmp_path):
    pkg, clean_rows, _, _clean_ev, _ = _make_fixture_package(tmp_path, clean_rows=1, is_negative_control=True)

    grok_labels = [
        {
            "unit_id": clean_rows[0]["unit_id"],
            "unit_sha256": clean_rows[0]["unit_sha256"],
            "decision_code": "reject_dialectal_regional_surzhyk",
            "clean_modern_standard_prose": False,
            "modern_genre_id": None,
            "evidence_ids": [],
        }
    ]
    gemini_labels = [
        {
            "unit_id": clean_rows[0]["unit_id"],
            "unit_sha256": clean_rows[0]["unit_sha256"],
            "decision_code": "reject_dialectal_regional_surzhyk",
            "clean_modern_standard_prose": False,
            "modern_genre_id": None,
            "evidence_ids": [],
        }
    ]

    _setup_provider_labels(pkg, "clean_label", 1, grok_labels, gemini_labels)
    result = compare_mod.compare(pkg, "clean_label", 1)

    assert result["clean_consensus_count"] == 0
    assert result["risk_triggered_consensus_count"] == 1
    assert result["disagreement_count"] == 0


def test_compare_rejects_invalid_evidence_reference(tmp_path):
    pkg, clean_rows, _, _clean_ev, _ = _make_fixture_package(tmp_path, clean_rows=1)
    grok_labels = [
        {
            "unit_id": clean_rows[0]["unit_id"],
            "unit_sha256": clean_rows[0]["unit_sha256"],
            "decision_code": "agree",
            "clean_modern_standard_prose": True,
            "modern_genre_id": "expository_narrative",
            "evidence_ids": ["cycle007_evidence:invented" + "f" * 48],
        }
    ]
    gemini_labels = grok_labels

    _setup_provider_labels(pkg, "clean_label", 1, grok_labels, gemini_labels)
    with pytest.raises(compare_mod.Error) as exc:
        compare_mod.compare(pkg, "clean_label", 1)
    assert exc.value.failure_code == "evidence_reference_invalid"


def test_compare_rejects_missing_source_package_binding(tmp_path):
    pkg, *_ = _make_fixture_package(tmp_path, clean_rows=1, residual_rows=1)
    path = pkg / "evidence" / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["source_package_binding"] = None
    manifest["manifest_sha256"] = contract.sha256_value({k: v for k, v in manifest.items() if k != "manifest_sha256"})
    path.write_text(json.dumps(manifest, sort_keys=True) + "\n")
    path.chmod(0o600)

    with pytest.raises(compare_mod.Error) as exc:
        compare_mod._evidence_manifest(pkg, compare_mod._manifest(pkg))
    assert exc.value.failure_code == "missing_evidence_sidecar"


def test_compare_rejects_omitted_provider_receipt_field(tmp_path):
    pkg, clean_rows, _, clean_ev, _ = _make_fixture_package(tmp_path, clean_rows=1, residual_rows=1)
    labels = [
        {
            "unit_id": clean_rows[0]["unit_id"],
            "unit_sha256": clean_rows[0]["unit_sha256"],
            "decision_code": "agree",
            "clean_modern_standard_prose": True,
            "modern_genre_id": "expository_narrative",
            "evidence_ids": clean_ev[0]["evidence_ids"],
        }
    ]
    _setup_provider_labels(pkg, "clean_label", 1, labels, labels)
    receipt_path = pkg / compare_mod.GEMINI["root"] / "clean_label" / "receipt-0001.json"
    receipt = json.loads(receipt_path.read_text())
    receipt.pop("sidecar_id")
    receipt["receipt_sha256"] = compare_mod.digest(
        compare_mod.canonical({key: value for key, value in receipt.items() if key != "receipt_sha256"})
    )
    receipt_path.write_text(json.dumps(receipt, sort_keys=True) + "\n")
    receipt_path.chmod(0o600)

    with pytest.raises(compare_mod.Error) as exc:
        compare_mod.compare(pkg, "clean_label", 1)
    assert exc.value.failure_code == "label_count_or_envelope_drift"


@pytest.mark.parametrize("field", ["sidecar_sha256", "sidecar_id", "packet_binding_raw_sha256"])
def test_compare_rejects_substituted_sidecar_entry_hash_id_or_packet_binding(tmp_path, field):
    pkg, *_ = _make_fixture_package(tmp_path, clean_rows=1, residual_rows=1)
    path = pkg / "evidence" / "manifest.json"
    manifest = json.loads(path.read_text())
    if field == "packet_binding_raw_sha256":
        manifest["sidecars"][0]["packet_binding"]["raw_sha256"] = "0" * 64
    else:
        manifest["sidecars"][0][field] = "0" * 64
    manifest["manifest_sha256"] = contract.sha256_value({k: v for k, v in manifest.items() if k != "manifest_sha256"})
    path.write_text(json.dumps(manifest, sort_keys=True) + "\n")
    path.chmod(0o600)

    with pytest.raises(compare_mod.Error) as exc:
        compare_mod.compare_all(pkg, fixture=True)
    assert exc.value.failure_code == "missing_evidence_sidecar"


@pytest.mark.parametrize("mutate", ["missing", "duplicate"])
def test_compare_rejects_missing_or_duplicate_row_evidence(tmp_path, mutate):
    pkg, *_ = _make_fixture_package(tmp_path, clean_rows=2, residual_rows=1)
    sidecar_path = pkg / "evidence" / "sidecar-0001.json"
    sidecar = json.loads(sidecar_path.read_text())
    if mutate == "missing":
        sidecar["rows"] = sidecar["rows"][:-1]
        sidecar["row_count"] = 1
    else:
        sidecar["rows"][1] = sidecar["rows"][0]
    sidecar.pop("sidecar_id")
    sidecar["sidecar_id"] = "cycle007_sidecar:" + contract.sha256_value(sidecar)
    sidecar_path.write_text(json.dumps(sidecar, sort_keys=True) + "\n")
    sidecar_path.chmod(0o600)
    manifest_path = pkg / "evidence" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["sidecars"][0]["sidecar_sha256"] = compare_mod.digest(sidecar_path.read_bytes())
    manifest["sidecars"][0]["sidecar_id"] = sidecar["sidecar_id"]
    manifest["sidecars"][0]["row_count"] = sidecar["row_count"]
    manifest["manifest_sha256"] = contract.sha256_value({k: v for k, v in manifest.items() if k != "manifest_sha256"})
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n")
    manifest_path.chmod(0o600)

    with pytest.raises(compare_mod.Error) as exc:
        compare_mod.compare_all(pkg, fixture=True)
    assert exc.value.failure_code == "missing_evidence_sidecar"


def test_compare_residual_lane(tmp_path):
    pkg, _, res_rows, _, res_ev = _make_fixture_package(tmp_path, clean_rows=1, residual_rows=2)

    grok_labels = [
        {
            "unit_id": res_rows[0]["unit_id"],
            "unit_sha256": res_rows[0]["unit_sha256"],
            "phenomena": [
                {
                    "phenomenon_id": "apostrophe",
                    "decision_code": "positive",
                    "evidence_sufficiency": "sufficient",
                    "evidence_ids": res_ev[0]["phenomenon_evidence_ids"]["apostrophe"],
                }
            ],
            "primary_phenomenon_id": "apostrophe",
            "item_decision_rollup": "positive",
        },
        {
            "unit_id": res_rows[1]["unit_id"],
            "unit_sha256": res_rows[1]["unit_sha256"],
            "phenomena": [
                {
                    "phenomenon_id": "apostrophe",
                    "decision_code": "abstention",
                    "evidence_sufficiency": "insufficient",
                    "evidence_ids": [],
                }
            ],
            "primary_phenomenon_id": None,
            "item_decision_rollup": "abstention",
        },
    ]
    gemini_labels = list(grok_labels)

    _setup_provider_labels(pkg, "residual_label", 1, grok_labels, gemini_labels)
    result = compare_mod.compare(pkg, "residual_label", 1)

    assert result["clean_consensus_count"] == 0
    assert result["risk_triggered_consensus_count"] == 2
    assert result["disagreement_count"] == 0
    risk_records = compare_mod.read(
        pkg / compare_mod.OUTPUT / "residual_label" / "risk-consensus-0001.json",
        "risk records",
    )["records"]
    assert all("missing_normative_rule" in record["risk_reasons"] for record in risk_records)


def test_compare_all_fixture_mode(tmp_path):
    pkg, clean_rows, res_rows, clean_ev, res_ev = _make_fixture_package(tmp_path, clean_rows=2, residual_rows=2)

    clean_grok = [
        {
            "unit_id": r["unit_id"],
            "unit_sha256": r["unit_sha256"],
            "decision_code": "agree",
            "clean_modern_standard_prose": True,
            "modern_genre_id": "expository_narrative",
            "evidence_ids": clean_ev[i]["evidence_ids"],
        }
        for i, r in enumerate(clean_rows)
    ]
    res_grok = [
        {
            "unit_id": r["unit_id"],
            "unit_sha256": r["unit_sha256"],
            "phenomena": [
                {
                    "phenomenon_id": "apostrophe",
                    "decision_code": "positive",
                    "evidence_sufficiency": "sufficient",
                    "evidence_ids": res_ev[i]["phenomenon_evidence_ids"]["apostrophe"],
                }
            ],
            "primary_phenomenon_id": "apostrophe",
            "item_decision_rollup": "positive",
        }
        for i, r in enumerate(res_rows)
    ]

    _setup_provider_labels(pkg, "clean_label", 1, clean_grok, clean_grok)
    _setup_provider_labels(pkg, "residual_label", 1, res_grok, res_grok)

    batch_receipt = compare_mod.compare_all(pkg, fixture=True)
    assert batch_receipt["packet_count"] == 2
    assert batch_receipt["row_count"] == 4
    assert batch_receipt["clean_consensus_count"] == 2
    assert batch_receipt["risk_triggered_consensus_count"] == 2
    assert batch_receipt["disagreement_count"] == 0


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
