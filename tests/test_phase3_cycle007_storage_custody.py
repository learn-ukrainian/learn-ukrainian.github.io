"""Synthetic proofs for Cycle007 reversible storage/custody (#7434).

Fixtures are disjoint from held-out production content. No provider execution,
no deletion of originals outside the disposable tmp workspace, and no private
topology disclosure.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import shutil
import stat
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_cycle007_materializer as materializer
from scripts.projects.open_model_data import phase3_cycle007_storage_custody as storage

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_SUMMARY_SCHEMA = ROOT / (
    "data/projects/open_model_data/contracts/"
    "phase3_cycle007_storage_public_summary_v1.schema.json"
)
PUBLIC_SUMMARY = ROOT / (
    "data/projects/open_model_data/reference/"
    "phase3_cycle007_storage_public_summary_v1.json"
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


def test_retention_stays_unresolved_without_held_out_proof() -> None:
    inventory = {
        "packet_count": 3,
        "row_count": 7,
        "object_count": 5,
        "total_allocated_bytes": 1000,
        "receipt_sha256": "a" * 64,
    }
    decision = storage.decide_retention(
        inventory=inventory,
        evaluation_firewall_requires_cycle007_identities=True,
    )
    assert decision["retention_outcome"] is None
    assert decision["retention_status"] == storage.RETENTION_UNRESOLVED
    assert decision["retention_final"] is False
    assert decision["retention_reconciliation_required"] is True
    assert decision["replacement_firewall_owner_issue"] == 7427
    assert decision["preserves_only_non_content_lineage_hashes"] is False
    questions = decision["retention_questions"]
    assert questions["q4_identity_lineage_exclusion_alone_insufficient"] is True
    assert questions["q1_concrete_source_qualified_held_out_function"] is False
    assert questions["q6_replacement_firewall_owner_issue"] == 7427


def test_retention_retain_requires_complete_held_out_proof() -> None:
    inventory = {
        "packet_count": 3,
        "row_count": 7,
        "object_count": 5,
        "total_allocated_bytes": 1000,
        "receipt_sha256": "a" * 64,
    }
    proof = {
        "held_out_evaluation_function_id": "source_qualified_cell_coverage_v1",
        "source_qualified": True,
        "required_fields": ["document_id", "split_id"],
        "required_identities": ["unit_id", "unit_sha256"],
        "named_consumer": "issue-7427-evaluation-steward",
        "text_free_source_rights_adjudication_metadata": True,
    }
    decision = storage.decide_retention(inventory=inventory, held_out_evaluation_proof=proof)
    assert decision["retention_outcome"] == storage.RETAIN_MINIMAL_EVALUATION_ASSET
    assert decision["replacement_firewall_owner_issue"] is None


def test_reversible_lane_authorizes_retention_neutral_expanded_reclaim(tmp_path: Path) -> None:
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
    assert lane["safe_failure_code"] is None
    assert lane["deletion_authorized"] is False
    assert lane["retention_outcome"] is None
    assert lane["retention_final"] is False
    assert lane["retention_reconciliation_required"] is True
    assert lane["retention_neutral_lossless_compaction"] is True
    assert lane["compact_custody_retained_pending_issue"] == 7427
    assert lane["second_expanded_tree"] is False
    assert lane["replacement_firewall_owner_issue"] == 7427
    assert lane["packet_count"] == packet_count
    assert lane["row_count"] == row_count
    assert lane["unique_inode_count"] == lane["object_count"]
    lane_root = work / "cycle007-storage-lane"
    assert (lane_root / "pack").is_dir()
    assert (lane_root / "pack-manifest.receipt.json").is_file()
    assert (lane_root / "roundtrip.json").is_file()
    assert (lane_root / "backup").is_dir()
    assert (lane_root / "backup-restore-proof.json").is_file()
    assert lane["pack_kind"] == "content_compact"
    assert lane["identity_proof_ok"] is True
    assert lane["backup_restore_ok"] is True
    assert lane["roundtrip_ok"] is True
    auth = json.loads((lane_root / "deletion-auth-request.json").read_bytes())
    assert auth["deletion_authorized"] is False
    assert auth["retention_outcome"] is None
    assert auth["retention_final"] is False
    assert auth["retention_neutral_lossless_compaction"] is True
    assert auth["compact_custody_retained_pending_issue"] == 7427
    assert auth["deletion_candidate_count"] == lane["object_count"]
    assert auth["retained_object_count"] == 0
    assert auth["reclaimed_byte_forecast"] == lane["fully_closed_reclaimable_bytes"]
    assert {
        item["authorized_class"] for item in auth["targets"]
    } == {"lossless_expanded_reclaim_candidate"}

    # Originals untouched.
    for path in materialization.rglob("*.json"):
        assert path.is_file()
    for path in evidence.rglob("*.json"):
        assert path.is_file()

    # Modes remain private on lane artifacts.
    for path in (work / "cycle007-storage-lane").rglob("*"):
        mode = stat.S_IMODE(path.stat().st_mode)
        if path.is_dir():
            assert mode == storage.PRIVATE_DIR_MODE
        elif path.is_file():
            assert mode == storage.PRIVATE_FILE_MODE


def test_staged_cross_host_pack_backup_and_finalize_are_lossless_and_non_destructive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        storage,
        "_physical_failure_domain_sha256",
        lambda root: storage.digest(f"fixture-domain:{root.name}".encode()),
    )
    materialization, packet_count, row_count = _build_materialization(tmp_path)
    evidence = _build_evidence(tmp_path, materialization)
    source_work = tmp_path / "source-work"
    source_work.mkdir(mode=storage.PRIVATE_DIR_MODE)
    os.chmod(source_work, storage.PRIVATE_DIR_MODE)
    bindings = storage.resolve_bindings(
        fixture=True,
        materialization=materialization,
        evidence=evidence,
        work_root=source_work,
    )

    primary = storage.primary_universal_pack_stage(bindings)
    assert primary["primary_stage"]["no_deletion_performed"] is True
    assert primary["primary_stage"]["packet_count"] == packet_count
    assert primary["primary_stage"]["row_count"] == row_count
    assert primary["pack_manifest"]["pack_kind"] == "content_compact"
    assert primary["preflight"]["stored_payload_digest"] == primary["pack_manifest"]["stored_payload_digest"]

    workstation_root = tmp_path / "workstation"
    workstation_root.mkdir(mode=storage.PRIVATE_DIR_MODE)
    imported_pack = workstation_root / "imported-pack"
    admission = storage.workstation_backup_admission_stage(
        primary["portable_export"],
        workstation_root,
        imported_pack,
        source_failure_domain_token="fixture-primary-domain",
        workstation_failure_domain_token="fixture-workstation-domain",
        fixture=True,
    )
    assert (workstation_root / "cycle007-storage-backup-admission.json").is_file()
    shutil.copytree(primary["pack_dir"], imported_pack)
    attested = storage.workstation_backup_attestation_stage(
        primary["portable_export"],
        admission,
        imported_pack,
        workstation_root,
        source_failure_domain_token="fixture-primary-domain",
        workstation_failure_domain_token="fixture-workstation-domain",
        zstd_executable=bindings.zstd_executable,
        fixture=True,
    )
    assert attested["attestation"]["independent_failure_domain"] is True
    assert attested["restore_proof"]["proof_mode"] == "portable_stream_decompress_hash"
    assert attested["restore_proof"]["backup_restore_ok"] is True
    assert (
        workstation_root
        / "cycle007-storage-backup-attestation"
        / "attestation.json"
    ).is_file()
    challenge = storage.issue_finalization_challenge(
        bindings, primary["primary_stage"], primary["portable_export"]
    )
    response = storage.workstation_finalization_response_stage(
        primary["portable_export"],
        attested["attestation"],
        challenge,
        imported_pack,
        workstation_root,
        source_failure_domain_token="fixture-primary-domain",
        workstation_failure_domain_token="fixture-workstation-domain",
        zstd_executable=bindings.zstd_executable,
        fixture=True,
    )

    final = storage.finalize_source_deletion_auth_stage(
        bindings,
        primary["primary_stage"],
        primary["portable_export"],
        attested["attestation"],
        attested["backup"],
        attested["restore_proof"],
        primary["pack_manifest"],
        primary["inventory"],
        primary["pack_dir"],
        challenge,
        response,
    )
    assert final["finalize"]["fresh_link_set_closed"] is True
    assert final["auth"]["deletion_authorized"] is False
    assert final["auth"]["retention_neutral_lossless_compaction"] is True
    assert final["auth"]["deletion_candidate_count"] == final["inventory"]["object_count"]
    assert (
        source_work
        / "cycle007-storage-primary-stage"
        / "deletion-auth-request.json"
    ).is_file()

    # The staged code never touches originals or creates an expanded restore.
    assert all(path.is_file() for path in materialization.rglob("*.json"))
    assert all(path.is_file() for path in evidence.rglob("*.json"))
    assert not (workstation_root / "expanded").exists()


def test_staged_backup_refuses_tampered_export_or_same_failure_domain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        storage,
        "_physical_failure_domain_sha256",
        lambda root: storage.digest(f"fixture-domain:{root.name}".encode()),
    )
    materialization, _packet_count, _row_count = _build_materialization(tmp_path)
    evidence = _build_evidence(tmp_path, materialization)
    source_work = tmp_path / "source-work"
    source_work.mkdir(mode=storage.PRIVATE_DIR_MODE)
    os.chmod(source_work, storage.PRIVATE_DIR_MODE)
    bindings = storage.resolve_bindings(
        fixture=True,
        materialization=materialization,
        evidence=evidence,
        work_root=source_work,
    )
    primary = storage.primary_universal_pack_stage(bindings)
    workstation_root = tmp_path / "workstation"
    workstation_root.mkdir(mode=storage.PRIVATE_DIR_MODE)
    imported_pack = workstation_root / "imported-pack"
    admission = storage.workstation_backup_admission_stage(
        primary["portable_export"],
        workstation_root,
        imported_pack,
        source_failure_domain_token="fixture-primary-domain",
        workstation_failure_domain_token="fixture-workstation-domain",
        fixture=True,
    )
    shutil.copytree(primary["pack_dir"], imported_pack)
    tampered_export = dict(primary["portable_export"])
    tampered_export["packet_count"] = 99
    with pytest.raises(storage.StorageCustodyError) as exc:
        storage.workstation_backup_attestation_stage(
            tampered_export,
            admission,
            imported_pack,
            workstation_root,
            source_failure_domain_token="fixture-primary-domain",
            workstation_failure_domain_token="fixture-workstation-domain",
            zstd_executable=bindings.zstd_executable,
            fixture=True,
        )
    assert exc.value.code == "backup_restore_failure"

    with pytest.raises(storage.StorageCustodyError) as exc:
        storage.workstation_backup_attestation_stage(
            primary["portable_export"],
            admission,
            imported_pack,
            workstation_root,
            source_failure_domain_token="fixture-primary-domain",
            workstation_failure_domain_token="fixture-primary-domain",
            zstd_executable=bindings.zstd_executable,
            fixture=True,
        )
    assert exc.value.code == "backup_restore_failure"

    attested = storage.workstation_backup_attestation_stage(
        primary["portable_export"],
        admission,
        imported_pack,
        workstation_root,
        source_failure_domain_token="fixture-primary-domain",
        workstation_failure_domain_token="fixture-workstation-domain",
        zstd_executable=bindings.zstd_executable,
        fixture=True,
    )
    challenge = storage.issue_finalization_challenge(
        bindings, primary["primary_stage"], primary["portable_export"]
    )
    object_rel = primary["pack_manifest"]["objects"][0]["object_relative_path"]
    (imported_pack / object_rel).unlink()
    with pytest.raises(storage.StorageCustodyError) as exc:
        storage.workstation_finalization_response_stage(
            primary["portable_export"],
            attested["attestation"],
            challenge,
            imported_pack,
            workstation_root,
            source_failure_domain_token="fixture-primary-domain",
            workstation_failure_domain_token="fixture-workstation-domain",
            zstd_executable=bindings.zstd_executable,
            fixture=True,
        )
    assert exc.value.code == "backup_restore_failure"


def test_staged_backup_records_cross_filesystem_allocation_without_rejecting_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        storage,
        "_physical_failure_domain_sha256",
        lambda root: storage.digest(f"fixture-domain:{root.name}".encode()),
    )
    materialization, _packet_count, _row_count = _build_materialization(tmp_path)
    evidence = _build_evidence(tmp_path, materialization)
    source_work = tmp_path / "source-work"
    source_work.mkdir(mode=storage.PRIVATE_DIR_MODE)
    os.chmod(source_work, storage.PRIVATE_DIR_MODE)
    bindings = storage.resolve_bindings(
        fixture=True,
        materialization=materialization,
        evidence=evidence,
        work_root=source_work,
    )
    primary = storage.primary_universal_pack_stage(bindings)
    workstation_root = tmp_path / "workstation"
    workstation_root.mkdir(mode=storage.PRIVATE_DIR_MODE)
    imported_pack = workstation_root / "imported-pack"
    admission = storage.workstation_backup_admission_stage(
        primary["portable_export"],
        workstation_root,
        imported_pack,
        source_failure_domain_token="fixture-primary-domain",
        workstation_failure_domain_token="fixture-workstation-domain",
        fixture=True,
    )
    shutil.copytree(primary["pack_dir"], imported_pack)

    source_allocated = primary["pack_manifest"]["total_stored_allocated_bytes"]
    allocation_delta = 22_827_008
    monkeypatch.setattr(
        storage,
        "_pack_payload_allocated_bytes",
        lambda _pack_dir, _manifest: (
            source_allocated
            - storage.ZSTD_METADATA_ALLOWANCE_BYTES
            + allocation_delta
        ),
    )

    attested = storage.workstation_backup_attestation_stage(
        primary["portable_export"],
        admission,
        imported_pack,
        workstation_root,
        source_failure_domain_token="fixture-primary-domain",
        workstation_failure_domain_token="fixture-workstation-domain",
        zstd_executable=bindings.zstd_executable,
        fixture=True,
    )

    assert attested["restore_proof"]["backup_restore_ok"] is True
    assert attested["backup"]["source_compact_allocated_bytes"] == source_allocated
    assert attested["backup"]["backup_allocated_bytes"] == (
        source_allocated + allocation_delta
    )
    assert attested["backup"]["backup_allocation_delta_bytes"] == allocation_delta
    assert attested["attestation"]["backup_allocation_delta_bytes"] == allocation_delta


def test_staged_finalize_refuses_same_content_inode_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        storage,
        "_physical_failure_domain_sha256",
        lambda root: storage.digest(f"fixture-domain:{root.name}".encode()),
    )
    materialization, _packet_count, _row_count = _build_materialization(tmp_path)
    evidence = _build_evidence(tmp_path, materialization)
    source_work = tmp_path / "source-work"
    source_work.mkdir(mode=storage.PRIVATE_DIR_MODE)
    os.chmod(source_work, storage.PRIVATE_DIR_MODE)
    bindings = storage.resolve_bindings(
        fixture=True,
        materialization=materialization,
        evidence=evidence,
        work_root=source_work,
    )
    primary = storage.primary_universal_pack_stage(bindings)
    workstation_root = tmp_path / "workstation"
    workstation_root.mkdir(mode=storage.PRIVATE_DIR_MODE)
    imported_pack = workstation_root / "imported-pack"
    admission = storage.workstation_backup_admission_stage(
        primary["portable_export"],
        workstation_root,
        imported_pack,
        source_failure_domain_token="fixture-primary-domain",
        workstation_failure_domain_token="fixture-workstation-domain",
        fixture=True,
    )
    shutil.copytree(primary["pack_dir"], imported_pack)
    attested = storage.workstation_backup_attestation_stage(
        primary["portable_export"],
        admission,
        imported_pack,
        workstation_root,
        source_failure_domain_token="fixture-primary-domain",
        workstation_failure_domain_token="fixture-workstation-domain",
        zstd_executable=bindings.zstd_executable,
        fixture=True,
    )
    challenge = storage.issue_finalization_challenge(
        bindings, primary["primary_stage"], primary["portable_export"]
    )
    response = storage.workstation_finalization_response_stage(
        primary["portable_export"],
        attested["attestation"],
        challenge,
        imported_pack,
        workstation_root,
        source_failure_domain_token="fixture-primary-domain",
        workstation_failure_domain_token="fixture-workstation-domain",
        zstd_executable=bindings.zstd_executable,
        fixture=True,
    )

    object_rel = primary["pack_manifest"]["objects"][0]["object_relative_path"]
    primary_blob = primary["pack_dir"] / object_rel
    original_blob = primary_blob.read_bytes()
    primary_blob.write_bytes(original_blob[:-1] + bytes([original_blob[-1] ^ 1]))
    with pytest.raises(storage.StorageCustodyError) as exc:
        storage.finalize_source_deletion_auth_stage(
            bindings,
            primary["primary_stage"],
            primary["portable_export"],
            attested["attestation"],
            attested["backup"],
            attested["restore_proof"],
            primary["pack_manifest"],
            primary["inventory"],
            primary["pack_dir"],
            challenge,
            response,
        )
    assert exc.value.code == "backup_restore_failure"
    primary_blob.write_bytes(original_blob)
    os.chmod(primary_blob, storage.PRIVATE_FILE_MODE)

    packet = materialization / "clean_label" / "packet-0001.json"
    replacement = packet.with_name("replacement.json")
    replacement.write_bytes(packet.read_bytes())
    os.chmod(replacement, stat.S_IMODE(packet.stat().st_mode))
    os.replace(replacement, packet)

    with pytest.raises(storage.StorageCustodyError) as exc:
        storage.finalize_source_deletion_auth_stage(
            bindings,
            primary["primary_stage"],
            primary["portable_export"],
            attested["attestation"],
            attested["backup"],
            attested["restore_proof"],
            primary["pack_manifest"],
            primary["inventory"],
            primary["pack_dir"],
            challenge,
            response,
        )
    assert exc.value.code == "identity_roundtrip_failure"


def test_different_domain_labels_cannot_approve_one_physical_filesystem(
    tmp_path: Path,
) -> None:
    materialization, _packet_count, _row_count = _build_materialization(tmp_path)
    evidence = _build_evidence(tmp_path, materialization)
    shared_root = tmp_path / "shared-root"
    shared_root.mkdir(mode=storage.PRIVATE_DIR_MODE)
    os.chmod(shared_root, storage.PRIVATE_DIR_MODE)
    bindings = storage.resolve_bindings(
        fixture=True,
        materialization=materialization,
        evidence=evidence,
        work_root=shared_root,
    )
    primary = storage.primary_universal_pack_stage(bindings)

    with pytest.raises(storage.StorageCustodyError) as exc:
        storage.workstation_backup_admission_stage(
            primary["portable_export"],
            shared_root,
            shared_root / "different-label-backup",
            source_failure_domain_token="fixture-primary-domain",
            workstation_failure_domain_token="different-label",
            fixture=True,
        )
    assert exc.value.code == "backup_restore_failure"


def test_real_workstation_admission_requires_protected_config_and_floor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workstation_root = tmp_path / "workstation"
    workstation_root.mkdir(mode=storage.PRIVATE_DIR_MODE)
    planned = workstation_root / "imported-pack"
    source_token = "approved-source-domain"
    workstation_token = "approved-workstation-domain"
    source_domain = storage._failure_domain_sha256(source_token)
    portable = storage._receipt(
        {
            "schema_version": storage.PORTABLE_EXPORT_SCHEMA_VERSION,
            "outcome_sha256": storage.OUTCOME_SHA256,
            "source_failure_domain_sha256": source_domain,
            "source_physical_domain_sha256": "1" * 64,
            "compact_stored_allocated_bytes": 4096,
        }
    )
    config = tmp_path / "workstation-domain.json"
    config.write_text(
        json.dumps(
            {
                "workstation_root": str(workstation_root),
                "failure_domain_token": workstation_token,
                "approved_source_failure_domain_sha256": source_domain,
            }
        )
    )
    os.chmod(config, storage.PRIVATE_FILE_MODE)
    monkeypatch.setattr(
        storage, "_physical_failure_domain_sha256", lambda _root: "2" * 64
    )
    monkeypatch.setattr(
        storage,
        "available_bytes",
        lambda _root: storage.MIN_FREE_BYTES + 4095,
    )

    with pytest.raises(storage.StorageCustodyError) as exc:
        storage.workstation_backup_admission_stage(
            portable,
            workstation_root,
            planned,
            source_failure_domain_token=source_token,
            workstation_failure_domain_token=workstation_token,
            workstation_domain_config=config,
            fixture=False,
        )
    assert exc.value.code == "capacity_insufficient"


def test_frozen_production_shape_gate_requires_exact_denominator() -> None:
    exact = {
        "packet_count": storage.EXPECTED_PACKET_COUNT,
        "row_count": storage.EXPECTED_ROW_COUNT,
        "selected_path_count": storage.EXPECTED_SELECTED_PATH_COUNT,
        "unique_inode_count": storage.EXPECTED_UNIQUE_INODE_COUNT,
        "duplicate_selected_link_count": storage.EXPECTED_DUPLICATE_SELECTED_LINK_COUNT,
        "total_allocated_bytes": storage.EXPECTED_TOTAL_ALLOCATED_BYTES,
        "object_set_sha256": storage.EXPECTED_OBJECT_SET_SHA256,
        "ordered_row_identity_commitment_sha256": (
            storage.EXPECTED_ORDERED_ROW_IDENTITY_SHA256
        ),
    }
    storage._require_production_inventory_shape(exact)
    drifted = dict(exact)
    drifted["selected_path_count"] -= 1
    with pytest.raises(storage.StorageCustodyError) as exc:
        storage._require_production_inventory_shape(drifted)
    assert exc.value.code == "denominator_drift"


def test_zstd_output_enospc_fails_closed_without_hanging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"cycle007" * (1024 * 1024))
    output = tmp_path / "pack.zst"
    executable = storage._default_fixture_zstd()
    real_open = Path.open

    class FullDestination:
        def write(self, _data: bytes) -> int:
            raise OSError(errno.ENOSPC, "synthetic full destination")

        def close(self) -> None:
            return None

    def controlled_open(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path == output:
            return FullDestination()
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", controlled_open)
    with pytest.raises(storage.StorageCustodyError) as exc:
        storage._compress_source_stream(source, executable, output_path=output)
    assert exc.value.code == "capacity_insufficient"


def test_unresolved_deletion_auth_requires_universal_pack_and_restore_proof(
    tmp_path: Path,
) -> None:
    materialization, _packet_count, _row_count = _build_materialization(tmp_path)
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
    storage.run_reversible_lane(bindings)
    lane_root = work / "cycle007-storage-lane"
    inventory = json.loads((lane_root / "inventory.json").read_bytes())
    pack = json.loads((lane_root / "pack-manifest.receipt.json").read_bytes())
    retention = json.loads((lane_root / "retention-decision.json").read_bytes())
    backup = json.loads((lane_root / "backup.json").read_bytes())
    restore = json.loads((lane_root / "backup-restore-proof.json").read_bytes())

    lineage_only = storage._receipt(
        {
            **{key: value for key, value in pack.items() if key != "receipt_sha256"},
            "pack_kind": "non_content_lineage_hashes",
        }
    )
    lineage_backup = storage._receipt(
        {
            **{key: value for key, value in backup.items() if key != "receipt_sha256"},
            "pack_manifest_sha256": lineage_only["receipt_sha256"],
        }
    )
    lineage_restore = storage._receipt(
        {
            **{key: value for key, value in restore.items() if key != "receipt_sha256"},
            "pack_manifest_sha256": lineage_only["receipt_sha256"],
        }
    )
    with pytest.raises(storage.StorageCustodyError) as exc:
        storage.deletion_auth_request(
            inventory, lineage_only, retention, lineage_backup, lineage_restore
        )
    assert exc.value.code == "retention_blocked"

    invalid_restore = storage._receipt(
        {
            **{key: value for key, value in restore.items() if key != "receipt_sha256"},
            "backup_restore_ok": False,
        }
    )
    with pytest.raises(storage.StorageCustodyError) as exc:
        storage.deletion_auth_request(
            inventory, pack, retention, backup, invalid_restore
        )
    assert exc.value.code == "backup_restore_failure"


def test_reversible_lane_retain_streams_content_pack_proof(tmp_path: Path) -> None:
    materialization, packet_count, row_count = _build_materialization(tmp_path)
    evidence = _build_evidence(tmp_path, materialization)
    work = tmp_path / "work"
    work.mkdir(mode=storage.PRIVATE_DIR_MODE)
    os.chmod(work, storage.PRIVATE_DIR_MODE)
    proof = {
        "held_out_evaluation_function_id": "source_qualified_cell_coverage_v1",
        "source_qualified": True,
        "required_fields": ["document_id", "split_id"],
        "required_identities": ["unit_id", "unit_sha256"],
        "named_consumer": "issue-7427-evaluation-steward",
        "text_free_source_rights_adjudication_metadata": True,
    }
    bindings = storage.resolve_bindings(
        fixture=True,
        materialization=materialization,
        evidence=evidence,
        work_root=work,
    )

    lane = storage.run_reversible_lane(bindings, held_out_evaluation_proof=proof)

    assert lane["lane_complete"] is True
    assert lane["retention_outcome"] == storage.RETAIN_MINIMAL_EVALUATION_ASSET
    assert lane["pack_kind"] == "content_compact"
    assert lane["packet_count"] == packet_count
    assert lane["row_count"] == row_count
    assert lane["identity_proof_ok"] is True
    assert lane["roundtrip_ok"] is True
    assert lane["second_expanded_tree"] is False
    roundtrip = json.loads((work / "cycle007-storage-lane" / "roundtrip.json").read_bytes())
    assert roundtrip["proof_mode"] == "stream_decompress_hash"
    assert roundtrip["roundtrip_ok"] is True


def test_real_mode_refuses_argv_paths(tmp_path: Path) -> None:
    with pytest.raises(storage.StorageCustodyError) as exc:
        storage.resolve_bindings(
            fixture=False,
            materialization=tmp_path / "x",
            evidence=None,
            work_root=tmp_path / "w",
        )
    assert exc.value.code == "path_disclosure_refused"


def test_configured_real_reconcile_does_not_falsely_report_unbound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    zstd = shutil.which("zstd")
    if zstd is None:
        pytest.skip("zstd unavailable")
    materialization, _packet_count, _row_count = _build_materialization(tmp_path)
    evidence = _build_evidence(tmp_path, materialization)
    work = tmp_path / "work"
    work.mkdir(mode=storage.PRIVATE_DIR_MODE)
    os.chmod(work, storage.PRIVATE_DIR_MODE)
    config = tmp_path / "private-config.json"
    config.write_text(
        json.dumps(
            {
                "materialization_package": str(materialization),
                "evidence_package": str(evidence),
                "work_root": str(work),
                "zstd_executable": zstd,
                "failure_domain_token": "test-real-source-domain",
            }
        ),
        encoding="utf-8",
    )
    os.chmod(config, storage.PRIVATE_FILE_MODE)
    monkeypatch.setenv(storage.REAL_CONFIG_ENV, str(config))
    # Fixture-sized packages cannot satisfy the frozen production denominator,
    # but a configured invocation must bind and fail on that denominator rather
    # than returning the false public state UNBOUND.
    with pytest.raises(storage.StorageCustodyError) as exc:
        storage.main(["reconcile"])
    assert exc.value.code == "denominator_drift"


def test_cli_prepare_lane_fixture(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
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
    stdout = json.loads(capsys.readouterr().out)
    _assert_no_host_filesystem_leak(stdout, where="cli stdout")
    summary = json.loads(summary_out.read_bytes())
    assert summary["text_free"] is True
    assert summary["deletion_authorized"] is False
    assert summary["retention_outcome"] is None
    assert summary["evaluation_firewall_requires_cycle007_identities"] is None
    assert summary["replacement_firewall_owner_issue"] == 7427
    assert summary["fixture_roundtrip_ok"] is True
    assert summary["fixture_backup_restore_ok"] is True
    assert summary["fixture_representation_proven"] is True
    assert summary["second_expanded_tree"] is False
    schema = json.loads(PUBLIC_SUMMARY_SCHEMA.read_bytes())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(summary)
    _assert_no_host_filesystem_leak(summary, where="cli public summary")
    assert "filesystem_avail_bytes" not in summary


def test_public_summary_keeps_retention_unresolved_while_production_is_unbound() -> None:
    schema = json.loads(PUBLIC_SUMMARY_SCHEMA.read_bytes())
    summary = json.loads(PUBLIC_SUMMARY.read_bytes())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(summary)
    assert summary["private_binding_state"] == "UNBOUND"
    assert summary["production_inventory_frozen"] is False
    assert summary["retention_outcome"] is None
    assert summary["replacement_firewall_owner_issue"] == 7427
    assert summary["preserves_only_non_content_lineage_hashes"] is False
    assert summary["pack_kind"] is None
    assert summary["deletion_authorized"] is False
    _assert_no_host_filesystem_leak(summary, where="committed public summary")
    assert "filesystem_avail_bytes" not in summary


def test_public_summary_schema_allows_optional_nulls() -> None:
    schema = json.loads(PUBLIC_SUMMARY_SCHEMA.read_bytes())
    properties = schema["properties"]
    for key in (
        "replacement_firewall_owner_issue",
        "pack_kind",
        "safe_failure_code",
        "evaluation_firewall_requires_cycle007_identities",
    ):
        variants = properties[key]["anyOf"]
        assert {"type": "null"} in variants


def test_committed_public_summary_omits_host_filesystem_totals() -> None:
    receipt = json.loads(PUBLIC_SUMMARY.read_bytes())
    schema = json.loads(PUBLIC_SUMMARY_SCHEMA.read_bytes())
    _assert_no_host_filesystem_leak(receipt, where="public summary receipt")
    properties = schema.get("properties") or {}
    assert isinstance(properties, dict)
    _assert_no_host_filesystem_leak(properties, where="public summary schema")
    combined = PUBLIC_SUMMARY.read_text(encoding="utf-8") + PUBLIC_SUMMARY_SCHEMA.read_text(
        encoding="utf-8"
    )
    assert "workstation_filesystem" not in combined
    assert "fixture_filesystem" not in combined
    assert "production_filesystem" not in combined
    assert "filesystem_avail_bytes" not in combined


def test_build_public_summary_does_not_emit_live_statvfs() -> None:
    lane = {
        "lane_complete": True,
        "stopped_at": "deletion_authorization_gate",
        "safe_failure_code": None,
        "retention_outcome": storage.RETIRE_CYCLE007,
        "packet_count": 3,
        "row_count": 7,
        "object_count": 9,
        "total_allocated_bytes": 1,
        "compact_stored_allocated_bytes": 1,
        "reclaimed_byte_forecast": 1,
        "deletion_candidate_count": 1,
        "filesystem_avail_bytes": 123456,
        "fixture_filesystem_avail_bytes": 123456,
        "production_filesystem_total_bytes": 123456,
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
    assert "production_filesystem_total_bytes" not in summary
    assert storage.public_summary_forbidden_fs_keys(
        {"nested": {"workstation_filesystem": {"total_bytes": 1}}}
    ) == ("workstation_filesystem",)


def test_inventory_counts_overlapping_aliases_once_for_allocation(tmp_path: Path) -> None:
    materialization, _packet_count, _row_count = _build_materialization(tmp_path)
    # The evidence root is nested under materialization, so materialization
    # traversal and evidence traversal select the same physical sidecars.
    evidence = _build_evidence(materialization, materialization)
    work = tmp_path / "work"
    work.mkdir(mode=storage.PRIVATE_DIR_MODE)
    os.chmod(work, storage.PRIVATE_DIR_MODE)
    bindings = storage.resolve_bindings(
        fixture=True,
        materialization=materialization,
        evidence=evidence,
        work_root=work,
    )

    inventory = storage.build_inventory(bindings)

    assert inventory["selected_path_count"] > inventory["unique_inode_count"]
    assert inventory["duplicate_selected_link_count"] == (
        inventory["selected_path_count"] - inventory["unique_inode_count"]
    )
    assert inventory["path_sum_allocated_bytes"] > inventory["total_allocated_bytes"]
    assert inventory["external_link_inode_count"] == 0
    assert inventory["fully_closed_reclaimable_bytes"] == inventory["total_allocated_bytes"]
    assert all(len(item["role_relative_paths"]) >= 1 for item in inventory["objects"])


def test_inventory_deduplicates_hard_linked_selected_paths(tmp_path: Path) -> None:
    materialization, _packet_count, _row_count = _build_materialization(tmp_path)
    source = materialization / "clean_label" / "packet-0001.json"
    alias = materialization / "clean_label" / "packet-0003.json"
    os.link(source, alias)
    work = tmp_path / "work"
    work.mkdir(mode=storage.PRIVATE_DIR_MODE)
    os.chmod(work, storage.PRIVATE_DIR_MODE)
    bindings = storage.resolve_bindings(
        fixture=True,
        materialization=materialization,
        work_root=work,
    )

    inventory = storage.build_inventory(bindings)
    packet = next(
        item for item in inventory["objects"] if item["sha256"] == storage.digest_file(source)
    )

    assert inventory["selected_path_count"] == inventory["unique_inode_count"] + 1
    assert inventory["path_sum_allocated_bytes"] > inventory["total_allocated_bytes"]
    assert packet["selected_path_count"] == 2
    assert packet["selected_link_count"] == 2
    assert packet["link_count"] == 2
    assert packet["external_link_count"] == 0
    assert packet["link_set_closed"] is True
    assert packet["path_allocated_bytes"] == packet["allocated_bytes"] * 2


def test_deletion_forecast_with_external_hard_link_claims_no_blocks() -> None:
    inventory = {
        "packet_count": 1,
        "row_count": 1,
        "object_count": 1,
        "total_allocated_bytes": 4096,
        "fully_closed_reclaimable_bytes": 0,
        "object_set_sha256": "1" * 64,
        "receipt_sha256": "a" * 64,
        "objects": [
            {
                "role_relative_path": "materialization/clean_label/packet-0001.json",
                "role_relative_paths": ["materialization/clean_label/packet-0001.json"],
                "selection_class": "materialization_packet",
                "selection_classes": ["materialization_packet"],
                "sha256": "b" * 64,
                "allocated_bytes": 4096,
                "selected_path_count": 1,
                "selected_link_count": 1,
                "link_count": 2,
                "external_link_count": 1,
                "link_set_closed": False,
            }
        ],
    }
    retention = {
        "retention_outcome": storage.RETIRE_CYCLE007,
        "retention_final": True,
        "receipt_sha256": "c" * 64,
    }
    pack = {
        "receipt_sha256": "d" * 64,
        "inventory_receipt_sha256": inventory["receipt_sha256"],
        "object_set_sha256": inventory["object_set_sha256"],
        "total_stored_allocated_bytes": 128,
    }
    backup = {
        "schema_version": storage.BACKUP_SCHEMA_VERSION,
        "receipt_sha256": "e" * 64,
        "pack_manifest_sha256": pack["receipt_sha256"],
        "independent_failure_domain": True,
    }
    restore = {
        "backup_restore_ok": True,
        "proof_mode": "portable_stream_decompress_hash",
        "receipt_sha256": "f" * 64,
        "pack_manifest_sha256": pack["receipt_sha256"],
        "object_set_sha256": inventory["object_set_sha256"],
    }

    inventory = storage._receipt(inventory)
    retention = storage._receipt(retention)
    pack["inventory_receipt_sha256"] = inventory["receipt_sha256"]
    pack = storage._receipt(pack)
    backup["pack_manifest_sha256"] = pack["receipt_sha256"]
    backup = storage._receipt(backup)
    restore["pack_manifest_sha256"] = pack["receipt_sha256"]
    restore = storage._receipt(restore)

    same_domain_backup = storage._receipt(
        {
            **{key: value for key, value in backup.items() if key != "receipt_sha256"},
            "independent_failure_domain": False,
        }
    )
    with pytest.raises(storage.StorageCustodyError) as exc:
        storage.deletion_auth_request(
            inventory, pack, retention, same_domain_backup, restore
        )
    assert exc.value.code == "backup_restore_failure"

    auth = storage.deletion_auth_request(inventory, pack, retention, backup, restore)

    assert auth["deletion_candidate_count"] == 0
    assert auth["reclaimed_byte_forecast"] == 0
    assert auth["targets"][0]["link_set_closed"] is False
    assert auth["targets"][0]["authorized_class"] == "retain_until_link_set_closed"
    assert auth["targets"][0]["reclaimable_allocated_bytes"] == 0


def test_deletion_forecast_counts_closed_inode_allocation_once() -> None:
    inventory = {
        "packet_count": 1,
        "row_count": 1,
        "object_count": 1,
        "total_allocated_bytes": 4096,
        "fully_closed_reclaimable_bytes": 4096,
        "object_set_sha256": "1" * 64,
        "receipt_sha256": "a" * 64,
        "objects": [
            {
                "role_relative_path": "evidence/sidecar-0001.json",
                "role_relative_paths": [
                    "evidence/sidecar-0001.json",
                    "materialization/evidence/sidecar-0001.json",
                ],
                "selection_class": "evidence_sidecar",
                "selection_classes": ["evidence_sidecar"],
                "sha256": "b" * 64,
                "allocated_bytes": 4096,
                "selected_path_count": 2,
                "selected_link_count": 2,
                "link_count": 2,
                "external_link_count": 0,
                "link_set_closed": True,
            }
        ],
    }
    retention = {
        "retention_outcome": storage.RETAIN_MINIMAL_EVALUATION_ASSET,
        "retention_final": True,
        "receipt_sha256": "c" * 64,
    }
    pack = {
        "receipt_sha256": "d" * 64,
        "inventory_receipt_sha256": inventory["receipt_sha256"],
        "object_set_sha256": inventory["object_set_sha256"],
        "total_stored_allocated_bytes": 128,
    }
    backup = {
        "schema_version": storage.BACKUP_SCHEMA_VERSION,
        "receipt_sha256": "e" * 64,
        "pack_manifest_sha256": pack["receipt_sha256"],
        "independent_failure_domain": True,
    }
    restore = {
        "backup_restore_ok": True,
        "proof_mode": "portable_stream_decompress_hash",
        "receipt_sha256": "f" * 64,
        "pack_manifest_sha256": pack["receipt_sha256"],
        "object_set_sha256": inventory["object_set_sha256"],
    }

    inventory = storage._receipt(inventory)
    retention = storage._receipt(retention)
    pack["inventory_receipt_sha256"] = inventory["receipt_sha256"]
    pack = storage._receipt(pack)
    backup["pack_manifest_sha256"] = pack["receipt_sha256"]
    backup = storage._receipt(backup)
    restore["pack_manifest_sha256"] = pack["receipt_sha256"]
    restore = storage._receipt(restore)

    auth = storage.deletion_auth_request(inventory, pack, retention, backup, restore)

    assert auth["deletion_candidate_count"] == 1
    assert auth["reclaimed_byte_forecast"] == 4096
    assert len(auth["targets"]) == 1
    assert auth["targets"][0]["role_relative_paths"] == inventory["objects"][0]["role_relative_paths"]


def test_capacity_forecast_uses_unique_allocation_and_no_second_tree() -> None:
    inventory = {
        "total_allocated_bytes": 4096,
        "path_sum_allocated_bytes": 8192,
        "receipt_sha256": "a" * 64,
    }

    forecast = storage.forecast_peak_temporary_bytes(
        inventory,
        compact_stored_bytes=1024,
        backup_stored_bytes=2048,
        destination_avail_bytes=storage.MIN_FREE_BYTES + 3072,
    )

    assert forecast["peak_temporary_bytes"] == 3072
    assert forecast["duplicate_selected_link_allocated_bytes"] == 4096
    assert forecast["second_expanded_tree_bytes"] == 0
    assert forecast["capacity_sufficient_for_peak"] is True


def test_full_size_pack_forecast_does_not_assume_compression() -> None:
    inventory = {
        "total_size_bytes": 999999,
        "unique_logical_bytes": 4096,
        "receipt_sha256": "a" * 64,
    }

    forecast = storage.forecast_no_write_content_pack_bytes(inventory)

    assert forecast["unique_logical_bytes"] == 4096
    assert forecast["compression_ratio_assumed"] is None
    assert forecast["full_size_upper_bound_bytes"] == 4096 + 1024 * 1024


def test_content_pack_and_backup_keep_aliases_as_one_blob(tmp_path: Path) -> None:
    materialization, _packet_count, _row_count = _build_materialization(tmp_path)
    evidence = _build_evidence(materialization, materialization)
    work = tmp_path / "work"
    work.mkdir(mode=storage.PRIVATE_DIR_MODE)
    os.chmod(work, storage.PRIVATE_DIR_MODE)
    proof = {
        "held_out_evaluation_function_id": "source_qualified_cell_coverage_v1",
        "source_qualified": True,
        "required_fields": ["document_id", "split_id"],
        "required_identities": ["unit_id", "unit_sha256"],
        "named_consumer": "issue-7427-evaluation-steward",
        "text_free_source_rights_adjudication_metadata": True,
    }
    bindings = storage.resolve_bindings(
        fixture=True,
        materialization=materialization,
        evidence=evidence,
        work_root=work,
    )

    lane = storage.run_reversible_lane(bindings, held_out_evaluation_proof=proof)

    assert lane["lane_complete"] is True
    assert lane["pack_kind"] == "content_compact"
    pack = json.loads(
        (work / "cycle007-storage-lane" / "pack" / "pack-manifest.json").read_bytes()
    )
    backup = json.loads((work / "cycle007-storage-lane" / "backup.json").read_bytes())
    assert pack["object_count"] == lane["object_count"]
    assert pack["unique_stored_object_count"] <= pack["object_count"]
    assert backup["backup_unique_inode_count"] <= backup["backup_object_count"]
    assert lane["second_expanded_tree"] is False


def test_separate_backup_filesystem_capacity_is_not_summed() -> None:
    inventory = {
        "total_allocated_bytes": 4096,
        "path_sum_allocated_bytes": 8192,
        "receipt_sha256": "a" * 64,
    }
    forecast = storage.forecast_peak_temporary_bytes(
        inventory,
        compact_stored_bytes=8192,
        backup_stored_bytes=4096,
        destination_avail_bytes=storage.MIN_FREE_BYTES + 8192,
        backup_destination_avail_bytes=storage.MIN_FREE_BYTES + 4096,
    )

    assert forecast["separate_filesystems"] is True
    assert forecast["peak_temporary_bytes"] == 8192
    assert forecast["peak_backup_bytes"] == 4096
    assert forecast["compact_capacity_sufficient"] is True
    assert forecast["backup_capacity_sufficient"] is True
    assert forecast["capacity_sufficient_for_peak"] is True


def test_exact_zstd_preflight_matches_written_unique_payload(tmp_path: Path) -> None:
    materialization, _packet_count, _row_count = _build_materialization(tmp_path)
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
    inventory = storage.build_inventory(bindings)

    forecast = storage.forecast_no_write_content_pack_bytes(inventory, bindings)
    pack = storage.write_pack(inventory, bindings, work / "pack")
    unique_payloads = {
        item["object_relative_path"]: item["stored_size_bytes"] for item in pack["objects"]
    }

    assert forecast["exact_pinned_zstd_preflight"] is True
    assert forecast["codec"] == "zstd"
    assert forecast["zstd"]["level"] == storage.ZSTD_COMPRESSION_LEVEL
    assert forecast["zstd"]["threads"] == storage.ZSTD_THREADS
    assert forecast["zstd"]["checksum"] is storage.ZSTD_CHECKSUM
    assert forecast["stored_payload_bytes"] == sum(unique_payloads.values())
    assert pack["total_stored_payload_bytes"] == forecast["stored_payload_bytes"]
    assert pack["stored_payload_digest"] == forecast["stored_payload_digest"]
    assert pack["compression"] == forecast["zstd"]


def test_rerun_refuses_to_erase_existing_lane_state(tmp_path: Path) -> None:
    materialization, _packet_count, _row_count = _build_materialization(tmp_path)
    evidence = _build_evidence(tmp_path, materialization)
    work = tmp_path / "work"
    work.mkdir(mode=storage.PRIVATE_DIR_MODE)
    os.chmod(work, storage.PRIVATE_DIR_MODE)
    proof = {
        "held_out_evaluation_function_id": "source_qualified_cell_coverage_v1",
        "source_qualified": True,
        "required_fields": ["document_id", "split_id"],
        "required_identities": ["unit_id", "unit_sha256"],
        "named_consumer": "issue-7427-evaluation-steward",
        "text_free_source_rights_adjudication_metadata": True,
    }
    bindings = storage.resolve_bindings(
        fixture=True,
        materialization=materialization,
        evidence=evidence,
        work_root=work,
    )
    first = storage.run_reversible_lane(bindings, held_out_evaluation_proof=proof)
    manifest_path = work / "cycle007-storage-lane" / "pack" / "pack-manifest.json"
    manifest_hash = storage.digest_file(manifest_path)

    with pytest.raises(storage.StorageCustodyError) as exc:
        storage.run_reversible_lane(bindings, held_out_evaluation_proof=proof)

    assert first["lane_complete"] is True
    assert exc.value.code == "existing_lane_state"
    assert storage.digest_file(manifest_path) == manifest_hash


def test_configured_backup_root_receives_backup_artifacts(tmp_path: Path) -> None:
    materialization, _packet_count, _row_count = _build_materialization(tmp_path)
    evidence = _build_evidence(tmp_path, materialization)
    work = tmp_path / "work"
    backup_root = tmp_path / "backup-root"
    work.mkdir(mode=storage.PRIVATE_DIR_MODE)
    backup_root.mkdir(mode=storage.PRIVATE_DIR_MODE)
    os.chmod(work, storage.PRIVATE_DIR_MODE)
    os.chmod(backup_root, storage.PRIVATE_DIR_MODE)
    proof = {
        "held_out_evaluation_function_id": "source_qualified_cell_coverage_v1",
        "source_qualified": True,
        "required_fields": ["document_id", "split_id"],
        "required_identities": ["unit_id", "unit_sha256"],
        "named_consumer": "issue-7427-evaluation-steward",
        "text_free_source_rights_adjudication_metadata": True,
    }
    bindings = storage.resolve_bindings(
        fixture=True,
        materialization=materialization,
        evidence=evidence,
        work_root=work,
        backup_root=backup_root,
    )

    lane = storage.run_reversible_lane(bindings, held_out_evaluation_proof=proof)

    assert lane["lane_complete"] is True
    assert (backup_root / "cycle007-storage-backup" / "pack-manifest.json").is_file()
    assert not (work / "cycle007-storage-lane" / "backup").exists()
