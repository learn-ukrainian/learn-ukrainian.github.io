"""Synthetic proofs for Cycle007 reversible storage/custody (#7434).

Fixtures are disjoint from held-out production content. No provider execution,
no deletion of originals outside the disposable tmp workspace, and no private
topology disclosure.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any, Mapping

import pytest

from scripts.projects.open_model_data import phase3_cycle007_materializer as materializer
from scripts.projects.open_model_data import phase3_cycle007_storage_custody as storage


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_SUMMARY_JSON = (
    ROOT / "data/projects/open_model_data/reference/phase3_cycle007_storage_public_summary_v1.json"
)
PUBLIC_SUMMARY_SCHEMA = (
    ROOT
    / "data/projects/open_model_data/contracts/phase3_cycle007_storage_public_summary_v1.schema.json"
)


def _assert_no_host_filesystem_leak(payload: Mapping[str, Any], *, where: str) -> None:
    leaked = storage.public_summary_forbidden_fs_keys(payload)
    assert leaked == (), f"{where} leaked host filesystem keys: {leaked}"



def _write(path: Path, value: Any, *, raw: bool = False) -> bytes:
    payload = value if raw else materializer.canonical(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, storage.PRIVATE_DIR_MODE)
    path.write_bytes(payload)
    os.chmod(path, storage.PRIVATE_FILE_MODE)
    return payload


def _row(index: int, lane: str) -> dict[str, Any]:
    unit_id = f"synthetic.storage.{lane}.{index:04d}"
    return {
        "unit_id": unit_id,
        "unit_sha256": hashlib.sha256(unit_id.encode()).hexdigest(),
        "family_id": "synthetic_storage_family",
        "source_text": f"PRIVATE-SYNTHETIC-STORAGE-{index}",
        "evaluation_cycle_id": materializer.CYCLE007,
    }


def _build_materialization(root: Path) -> tuple[Path, int, int]:
    package = root / "materialization"
    package.mkdir(mode=storage.PRIVATE_DIR_MODE)
    os.chmod(package, storage.PRIVATE_DIR_MODE)
    specs = (("clean_label", 1, 2), ("clean_label", 2, 2), ("residual_label", 1, 3))
    packet_records: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    for lane, index, count in specs:
        start = len(all_rows)
        rows = [_row(start + offset, lane) for offset in range(count)]
        all_rows.extend(rows)
        packet = {
            "schema_version": "phase3_cycle007_evidence_packet_v1",
            "evaluation_cycle_id": materializer.CYCLE007,
            "lane": lane,
            "packet_index": index,
            "row_count": count,
            "rows": rows,
            "packet_identity_set_sha256": materializer.identity_set(rows),
        }
        path = package / lane / f"packet-{index:04d}.json"
        raw = _write(path, packet)
        packet_records.append(
            {
                "lane": lane,
                "packet_index": index,
                "canonical_basename": path.name,
                "row_count": count,
                "raw_sha256": materializer.digest(raw),
                "packet_identity_set_sha256": packet["packet_identity_set_sha256"],
            }
        )
    custody = {
        "schema_version": "phase3_cycle007_custody_receipt_v1",
        "evaluation_cycle_id": materializer.CYCLE007,
        "text_free": True,
        "packet_count": len(packet_records),
        "row_count": len(all_rows),
        "source_evaluation_cycle_id": materializer.CYCLE005,
        "source_custody_receipt_raw_sha256": materializer.SOURCE_CUSTODY_SHA256,
        "source_label_manifest_raw_sha256": materializer.SOURCE_MANIFEST_SHA256,
        "ordered_identity_commitment_sha256": materializer.ORDERED_IDENTITY_COMMITMENT_SHA256,
        "amendment_reference": "synthetic-storage-fixture",
    }
    custody["receipt_sha256"] = materializer._hash_receipt(custody)
    custody_raw = _write(package / "custody-receipt.json", custody)
    manifest = {
        "schema_version": "phase3_cycle007_materialization_manifest_v1",
        "evaluation_cycle_id": materializer.CYCLE007,
        "text_free": True,
        "source_evaluation_cycle_id": materializer.CYCLE005,
        "custody_receipt_raw_sha256": materializer.digest(custody_raw),
        "packet_count": len(packet_records),
        "row_count": len(all_rows),
        "packets": packet_records,
        "ordered_identity_commitment_sha256": materializer.ORDERED_IDENTITY_COMMITMENT_SHA256,
    }
    manifest["receipt_sha256"] = materializer._hash_receipt(manifest)
    _write(package / "manifest.json", manifest)
    return package, len(packet_records), len(all_rows)


def _build_evidence(root: Path, materialization: Path) -> Path:
    evidence = root / "evidence"
    evidence.mkdir(mode=storage.PRIVATE_DIR_MODE)
    os.chmod(evidence, storage.PRIVATE_DIR_MODE)
    sidecars: list[dict[str, Any]] = []
    packet_index = 0
    for lane in materializer.LANE_ORDER:
        lane_dir = materialization / lane
        if not lane_dir.is_dir():
            continue
        for packet_path in sorted(lane_dir.glob("packet-*.json")):
            packet_index += 1
            packet = json.loads(packet_path.read_bytes())
            rows = []
            for row in packet["rows"]:
                rows.append(
                    {
                        "unit_id": row["unit_id"],
                        "unit_sha256": row["unit_sha256"],
                        "tokenizer_id": "synthetic",
                        "tokenizer_version": "1",
                        "extracted_forms": ["synthetic"],
                        "evidence": [
                            {
                                "schema_version": "phase3_cycle007_evidence_v1",
                                "channel": "source_metadata",
                                "status": "attested",
                                "support": "metadata_only",
                                "claim_id": "synthetic.claim",
                                "evidence_id": "cycle007_evidence:" + ("a" * 64),
                            }
                        ],
                        "evidence_ids": ["cycle007_evidence:" + ("a" * 64)],
                        "phenomenon_evidence_ids": {},
                        "sufficient_support": True,
                        "archaic_only_risk": False,
                        "russian_shadow_suspected": False,
                    }
                )
            raw_sha256 = materializer.digest(packet_path.read_bytes())
            body = {
                "schema_version": "phase3_cycle007_evidence_sidecar_v1",
                "evaluation_cycle_id": materializer.CYCLE007,
                "lane": lane,
                "packet_binding": {
                    "canonical_basename": packet_path.name,
                    "raw_sha256": raw_sha256,
                    "packet_identity_set_sha256": packet["packet_identity_set_sha256"],
                },
                "packet_index": packet_index,
                "row_count": len(rows),
                "tokenizer_id": "synthetic",
                "tokenizer_version": "1",
                "code_hashes": {
                    "compiler_id": "synthetic",
                    "compiler_sha256": "b" * 64,
                    "tokenizer_id": "synthetic",
                    "tokenizer_version": "1",
                    "tokenizer_sha256": "c" * 64,
                    "compound_parser_id": "synthetic",
                    "compound_parser_version": "1",
                    "compound_parser_sha256": "d" * 64,
                    "mcp_response_parser_id": "synthetic",
                    "mcp_response_parser_version": "1",
                    "mcp_response_parser_sha256": "e" * 64,
                    "query_plan_id": "synthetic",
                    "query_plan_version": "1",
                    "query_plan_sha256": "f" * 64,
                },
                "server_code_sha256": "1" * 64,
                "sources_db_sha256": "2" * 64,
                "vesum_db_sha256": "3" * 64,
                "network_lookups_performed": 0,
                "rows": rows,
                "retrieval_payloads": {"padding": "x" * 4096},
            }
            sidecar_id = "cycle007_sidecar:" + hashlib.sha256(
                materializer.canonical(body)
            ).hexdigest()
            body["sidecar_id"] = sidecar_id
            path = evidence / f"sidecar-{packet_index:04d}.json"
            raw = _write(path, body)
            sidecars.append(
                {
                    "packet_index": packet_index,
                    "lane": lane,
                    "row_count": len(rows),
                    "sidecar_id": sidecar_id,
                    "sidecar_sha256": materializer.digest(raw),
                }
            )
    manifest = {
        "schema_version": "phase3_cycle007_evidence_manifest_v1",
        "evaluation_cycle_id": materializer.CYCLE007,
        "text_free": True,
        "packet_count": len(sidecars),
        "row_count": sum(item["row_count"] for item in sidecars),
        "sidecars": sidecars,
    }
    _write(evidence / "manifest.json", manifest)
    return evidence


def test_reconcile_reports_unbound_without_private_binding() -> None:
    reconcile = storage.reconcile_public_private(private_bound=False, inventory=None)
    assert reconcile["text_free"] is True
    assert reconcile["private_binding_state"] == "UNBOUND"
    assert reconcile["safe_failure_code"] == "private_binding_unbound"
    assert reconcile["public"]["public_packet_count"] == 204
    assert reconcile["public"]["public_row_count"] == 10159


def test_retention_chooses_minimal_evaluation_asset() -> None:
    inventory = {
        "packet_count": 3,
        "row_count": 7,
        "object_count": 5,
        "total_allocated_bytes": 1000,
        "receipt_sha256": "a" * 64,
    }
    decision = storage.decide_retention(inventory=inventory)
    assert decision["retention_outcome"] == storage.RETAIN_MINIMAL_EVALUATION_ASSET
    assert decision["rationale_code"] == "evaluation_firewall_requires_identity_assets"


def test_reversible_lane_roundtrip_backup_and_auth_gate(tmp_path: Path) -> None:
    materialization, packet_count, row_count = _build_materialization(tmp_path)
    evidence = _build_evidence(tmp_path, materialization)
    work = tmp_path / "work"
    work.mkdir(mode=storage.PRIVATE_DIR_MODE)
    os.chmod(work, storage.PRIVATE_DIR_MODE)

    bindings = storage.resolve_bindings(
        fixture=True,
        materialization=materialization,
        evidence=evidence,
        work_root=work,
    )
    lane = storage.run_reversible_lane(bindings)

    assert lane["lane_complete"] is True
    assert lane["stopped_at"] == "deletion_authorization_gate"
    assert lane["deletion_authorized"] is False
    assert lane["retention_outcome"] == storage.RETAIN_MINIMAL_EVALUATION_ASSET
    assert lane["packet_count"] == packet_count
    assert lane["row_count"] == row_count
    assert lane["identity_proof_ok"] is True
    assert lane["backup_restore_ok"] is True
    assert lane["roundtrip_ok"] is True
    assert lane["deletion_candidate_count"] >= 1
    assert isinstance(lane["reclaimed_byte_forecast"], int)
    assert lane["reclaimed_byte_forecast"] > 0

    # Originals untouched.
    for path in materialization.rglob("*.json"):
        assert path.is_file()
    for path in evidence.rglob("*.json"):
        assert path.is_file()

    auth = json.loads((work / "cycle007-storage-lane" / "deletion-auth-request.json").read_bytes())
    assert auth["deletion_authorized"] is False
    assert auth["issue_7434_is_not_deletion_authorization"] is True
    assert auth["authorization_gate"] == "operator_explicit_authorization_required"

    # Modes remain private on lane artifacts.
    for path in (work / "cycle007-storage-lane").rglob("*"):
        mode = stat.S_IMODE(path.stat().st_mode)
        if path.is_dir():
            assert mode == storage.PRIVATE_DIR_MODE
        elif path.is_file():
            assert mode == storage.PRIVATE_FILE_MODE


def test_real_mode_refuses_argv_paths(tmp_path: Path) -> None:
    with pytest.raises(storage.StorageCustodyError) as exc:
        storage.resolve_bindings(
            fixture=False,
            materialization=tmp_path / "x",
            evidence=None,
            work_root=tmp_path / "w",
        )
    assert exc.value.code == "path_disclosure_refused"


def test_cli_prepare_lane_fixture(tmp_path: Path) -> None:
    materialization, _packet_count, _row_count = _build_materialization(tmp_path)
    evidence = _build_evidence(tmp_path, materialization)
    work = tmp_path / "work"
    work.mkdir()
    summary_out = tmp_path / "public-summary.json"
    code = storage.main(
        [
            "prepare-lane",
            "--fixture",
            "--materialization",
            str(materialization),
            "--evidence",
            str(evidence),
            "--work-root",
            str(work),
            "--public-summary-out",
            str(summary_out),
        ]
    )
    assert code == 0
    summary = json.loads(summary_out.read_bytes())
    assert summary["text_free"] is True
    assert summary["deletion_authorized"] is False
    assert summary["retention_outcome"] == storage.RETAIN_MINIMAL_EVALUATION_ASSET
    assert summary["roundtrip_ok"] is True
    assert summary["backup_restore_ok"] is True
    _assert_no_host_filesystem_leak(summary, where="cli public summary")
    assert "filesystem_avail_bytes" not in summary


def test_committed_public_summary_omits_host_filesystem_totals() -> None:
    receipt = json.loads(PUBLIC_SUMMARY_JSON.read_bytes())
    schema = json.loads(PUBLIC_SUMMARY_SCHEMA.read_bytes())
    _assert_no_host_filesystem_leak(receipt, where="public summary receipt")
    properties = schema.get("properties") or {}
    assert isinstance(properties, dict)
    _assert_no_host_filesystem_leak(properties, where="public summary schema")
    combined = PUBLIC_SUMMARY_JSON.read_text(encoding="utf-8") + PUBLIC_SUMMARY_SCHEMA.read_text(
        encoding="utf-8"
    )
    assert "workstation_filesystem" not in combined
    assert "fixture_filesystem" not in combined


def test_build_public_summary_does_not_emit_live_statvfs() -> None:
    lane = {
        "lane_complete": True,
        "stopped_at": "deletion_authorization_gate",
        "safe_failure_code": None,
        "retention_outcome": storage.RETAIN_MINIMAL_EVALUATION_ASSET,
        "packet_count": 3,
        "row_count": 7,
        "object_count": 9,
        "total_allocated_bytes": 1,
        "compact_stored_allocated_bytes": 1,
        "reclaimed_byte_forecast": 1,
        "deletion_candidate_count": 1,
        "filesystem_avail_bytes": 123456,
        "fixture_filesystem_avail_bytes": 123456,
        "workstation_filesystem": {"total_bytes": 1, "avail_bytes": 1},
        "peak_temporary_bytes": 1,
        "capacity_sufficient_for_peak": True,
        "identity_proof_ok": True,
        "backup_restore_ok": True,
        "roundtrip_ok": True,
        "receipt_sha256": "a" * 64,
    }
    reconcile = {
        "private_binding_state": "UNBOUND",
        "safe_failure_code": "private_binding_unbound",
        "receipt_sha256": "b" * 64,
    }
    summary = storage.build_public_summary(lane, reconcile)
    _assert_no_host_filesystem_leak(summary, where="build_public_summary")
    assert "filesystem_avail_bytes" not in summary
    assert "workstation_filesystem" not in summary
    assert "fixture_filesystem_avail_bytes" not in summary
