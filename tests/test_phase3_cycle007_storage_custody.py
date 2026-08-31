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
from scripts.projects.open_model_data import phase3_cycle007_storage_deletion as deletion

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


def _prepare_deletion_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    overlapping_evidence: bool = False,
) -> dict[str, Any]:
    """Build a complete, synthetic, two-domain deletion-execution fixture.

    This deliberately goes through the public staged custody flow before
    creating operator authorization.  The helper owns only ``tmp_path`` and
    never binds the real Cycle007 packages.
    """
    monkeypatch.setattr(
        storage,
        "_physical_failure_domain_sha256",
        lambda root: storage.digest(f"fixture-domain:{root.name}".encode()),
    )
    materialization, _packet_count, _row_count = _build_materialization(tmp_path)
    evidence = _build_evidence(
        materialization if overlapping_evidence else tmp_path,
        materialization,
    )
    sentinel = materialization / "UNSELECTED-sentinel.bin"
    sentinel.write_bytes(b"do-not-delete-this-fixture-sentinel")
    os.chmod(sentinel, storage.PRIVATE_FILE_MODE)

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
    os.chmod(workstation_root, storage.PRIVATE_DIR_MODE)
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
    finalization_challenge = storage.issue_finalization_challenge(
        bindings, primary["primary_stage"], primary["portable_export"]
    )
    finalization_response = storage.workstation_finalization_response_stage(
        primary["portable_export"],
        attested["attestation"],
        finalization_challenge,
        imported_pack,
        workstation_root,
        source_failure_domain_token="fixture-primary-domain",
        workstation_failure_domain_token="fixture-workstation-domain",
        zstd_executable=bindings.zstd_executable,
        fixture=True,
    )
    finalized = storage.finalize_source_deletion_auth_stage(
        bindings,
        primary["primary_stage"],
        primary["portable_export"],
        attested["attestation"],
        attested["backup"],
        attested["restore_proof"],
        primary["pack_manifest"],
        primary["inventory"],
        primary["pack_dir"],
        finalization_challenge,
        finalization_response,
    )

    authorization = deletion.make_operator_authorization(
        finalized["auth"],
        "fixture-cycle007-delete-authorization-0001",
        fixture=True,
    )
    challenge = deletion.issue_deletion_execution_challenge(
        bindings,
        primary["primary_stage"],
        primary["portable_export"],
        finalized["finalize"],
        finalized["auth"],
        authorization,
    )
    pre_response = deletion.workstation_deletion_custody_response_stage(
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
    return {
        "bindings": bindings,
        "materialization": materialization,
        "evidence": evidence,
        "sentinel": sentinel,
        "source_work": source_work,
        "workstation_root": workstation_root,
        "imported_pack": imported_pack,
        "primary": primary,
        "attested": attested,
        "finalized": finalized,
        "authorization": authorization,
        "challenge": challenge,
        "pre_response": pre_response,
    }


def _fixture_source_paths(state: Mapping[str, Any]) -> set[Path]:
    index = storage._path_index(state["bindings"])
    paths: set[Path] = set()
    for item in state["primary"]["inventory"]["objects"]:
        for relative in item["role_relative_paths"]:
            paths.add(index[relative].resolve())
    return paths


def _execute_fixture_deletion(state: Mapping[str, Any], **kwargs: Any) -> dict[str, Any]:
    primary = state["primary"]
    finalized = state["finalized"]
    return deletion.execute_authorized_source_deletion(
        state["bindings"],
        primary["primary_stage"],
        primary["portable_export"],
        primary["inventory"],
        primary["pack_manifest"],
        finalized["finalize"],
        finalized["auth"],
        state["authorization"],
        state["challenge"],
        state["pre_response"],
        primary["pack_dir"],
        quiescence_lock_paths=kwargs.pop("quiescence_lock_paths", []),
        fault_hook=kwargs.pop("fault_hook", None),
        **kwargs,
    )


@pytest.mark.parametrize(
    "alias",
    (
        "materialization//etc/passwd",
        "evidence//etc/passwd",
        "materialization/../outside.bin",
        "evidence/../outside.bin",
    ),
)
def test_deletion_path_layers_reject_absolute_and_parent_escape(
    tmp_path: Path, alias: str
) -> None:
    materialization = tmp_path / "materialization"
    evidence = tmp_path / "evidence"
    work = tmp_path / "work"
    for directory in (materialization, evidence, work):
        directory.mkdir()
    bindings = storage.Bindings(materialization, evidence, work, True)

    with pytest.raises(deletion.DeletionExecutionError):
        deletion._role_path(bindings, alias)
    with pytest.raises(deletion.DeletionExecutionError):
        deletion._open_parent(bindings, alias)


def test_deletion_path_layers_reject_symlinked_parent_escape(tmp_path: Path) -> None:
    materialization = tmp_path / "materialization"
    evidence = tmp_path / "evidence"
    work = tmp_path / "work"
    outside = tmp_path / "outside"
    for directory in (materialization, evidence, work, outside):
        directory.mkdir()
    sentinel = outside / "sentinel.bin"
    sentinel.write_bytes(b"outside-authorized-root")
    (materialization / "escape").symlink_to(outside, target_is_directory=True)
    bindings = storage.Bindings(materialization, evidence, work, True)
    alias = "materialization/escape/sentinel.bin"

    with pytest.raises(deletion.DeletionExecutionError):
        deletion._role_path(bindings, alias)
    with pytest.raises(deletion.DeletionExecutionError):
        deletion._open_parent(bindings, alias)

    assert sentinel.read_bytes() == b"outside-authorized-root"


@pytest.mark.parametrize(
    "process_class",
    sorted(deletion.UNINSPECTABLE_QUIESCENCE_PROCESS_ALLOWLIST),
)
def test_quiescence_allows_only_known_uninspectable_session_infrastructure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    process_class: str,
) -> None:
    proc = tmp_path / "proc"
    descriptor_dir = proc / "101" / "fd"
    descriptor_dir.mkdir(parents=True)
    (proc / "101" / "comm").write_text(process_class + "\n", encoding="utf-8")
    original_iterdir = Path.iterdir

    def guarded_iterdir(path: Path):
        if path == descriptor_dir:
            raise PermissionError("fixture hidden descriptor table")
        return original_iterdir(path)

    monkeypatch.setattr(Path, "iterdir", guarded_iterdir)

    deletion._require_no_open_target_descriptors(
        {"entries": [{"dev": 1, "ino": 2}]},
        fixture=False,
        proc=proc,
    )


@pytest.mark.parametrize(
    "process_class",
    [
        "unknown-worker",
        "ssh-agent-helper",
        "SSHD-session",
        "sshd-session-extra",
        " ssh-agent",
        "ssh-agent ",
        "ssh-agent\r",
        "",
    ],
)
def test_quiescence_rejects_unknown_uninspectable_same_uid_process(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    process_class: str,
) -> None:
    proc = tmp_path / "proc"
    descriptor_dir = proc / "102" / "fd"
    descriptor_dir.mkdir(parents=True)
    (proc / "102" / "comm").write_text(process_class + "\n", encoding="utf-8")
    original_iterdir = Path.iterdir

    def guarded_iterdir(path: Path):
        if path == descriptor_dir:
            raise PermissionError("fixture hidden descriptor table")
        return original_iterdir(path)

    monkeypatch.setattr(Path, "iterdir", guarded_iterdir)

    with pytest.raises(deletion.DeletionExecutionError):
        deletion._require_no_open_target_descriptors(
            {"entries": [{"dev": 1, "ino": 2}]},
            fixture=False,
            proc=proc,
        )


def test_quiescence_rejects_unreadable_process_class(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    proc = tmp_path / "proc"
    descriptor_dir = proc / "102" / "fd"
    descriptor_dir.mkdir(parents=True)
    comm_path = proc / "102" / "comm"
    comm_path.write_text("ssh-agent\n", encoding="utf-8")
    original_iterdir = Path.iterdir
    original_read_bytes = Path.read_bytes

    def guarded_iterdir(path: Path):
        if path == descriptor_dir:
            raise PermissionError("fixture hidden descriptor table")
        return original_iterdir(path)

    def guarded_read_bytes(path: Path) -> bytes:
        if path == comm_path:
            raise PermissionError("fixture hidden process class")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "iterdir", guarded_iterdir)
    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)

    with pytest.raises(deletion.DeletionExecutionError):
        deletion._require_no_open_target_descriptors(
            {"entries": [{"dev": 1, "ino": 2}]},
            fixture=False,
            proc=proc,
        )


def test_quiescence_still_rejects_visible_target_descriptor_with_allowed_hidden_process(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    proc = tmp_path / "proc"
    hidden_descriptors = proc / "103" / "fd"
    hidden_descriptors.mkdir(parents=True)
    (proc / "103" / "comm").write_text("ssh-agent\n", encoding="utf-8")
    visible_descriptors = proc / "104" / "fd"
    visible_descriptors.mkdir(parents=True)
    (proc / "104" / "comm").write_text("ordinary-worker\n", encoding="utf-8")
    target = tmp_path / "authorized-target.bin"
    target.write_bytes(b"target")
    (visible_descriptors / "0").symlink_to(target)
    target_info = target.stat()
    original_iterdir = Path.iterdir

    def guarded_iterdir(path: Path):
        if path == hidden_descriptors:
            raise PermissionError("fixture hidden descriptor table")
        return original_iterdir(path)

    monkeypatch.setattr(Path, "iterdir", guarded_iterdir)

    with pytest.raises(deletion.DeletionExecutionError):
        deletion._require_no_open_target_descriptors(
            {"entries": [{"dev": int(target_info.st_dev), "ino": int(target_info.st_ino)}]},
            fixture=False,
            proc=proc,
        )

    assert target.read_bytes() == b"target"


def test_quiescence_still_scans_inspectable_allowlisted_process(
    tmp_path: Path,
) -> None:
    proc = tmp_path / "proc"
    descriptor_dir = proc / "105" / "fd"
    descriptor_dir.mkdir(parents=True)
    (proc / "105" / "comm").write_text("ssh-agent\n", encoding="utf-8")
    target = tmp_path / "authorized-target.bin"
    target.write_bytes(b"target")
    (descriptor_dir / "0").symlink_to(target)
    target_info = target.stat()

    with pytest.raises(deletion.DeletionExecutionError):
        deletion._require_no_open_target_descriptors(
            {"entries": [{"dev": int(target_info.st_dev), "ino": int(target_info.st_ino)}]},
            fixture=False,
            proc=proc,
        )

    assert target.read_bytes() == b"target"


def test_quiescence_rejects_uninspectable_individual_descriptor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    proc = tmp_path / "proc"
    descriptor_dir = proc / "106" / "fd"
    descriptor_dir.mkdir(parents=True)
    (proc / "106" / "comm").write_text("ordinary-worker\n", encoding="utf-8")
    descriptor = descriptor_dir / "0"
    descriptor.touch()
    original_stat = Path.stat

    def guarded_stat(path: Path, *args: Any, **kwargs: Any):
        if path == descriptor:
            raise PermissionError("fixture hidden descriptor")
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", guarded_stat)

    with pytest.raises(deletion.DeletionExecutionError):
        deletion._require_no_open_target_descriptors(
            {"entries": [{"dev": 1, "ino": 2}]},
            fixture=False,
            proc=proc,
        )


def test_quiescence_rejects_uninspectable_process_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    proc = tmp_path / "proc"
    process = proc / "108"
    (process / "fd").mkdir(parents=True)
    (process / "comm").write_text("ssh-agent\n", encoding="utf-8")
    original_stat = Path.stat

    def guarded_stat(path: Path, *args: Any, **kwargs: Any):
        if path == process:
            raise PermissionError("fixture hidden process metadata")
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", guarded_stat)

    with pytest.raises(deletion.DeletionExecutionError):
        deletion._require_no_open_target_descriptors(
            {"entries": [{"dev": 1, "ino": 2}]},
            fixture=False,
            proc=proc,
        )


@pytest.mark.parametrize("race", ["process_exit", "descriptor_close"])
def test_quiescence_tolerates_only_genuine_process_descriptor_races(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    race: str,
) -> None:
    proc = tmp_path / "proc"
    descriptor_dir = proc / "107" / "fd"
    descriptor_dir.mkdir(parents=True)
    (proc / "107" / "comm").write_text("ordinary-worker\n", encoding="utf-8")
    descriptor = descriptor_dir / "0"
    descriptor.touch()
    original_iterdir = Path.iterdir
    original_stat = Path.stat

    def guarded_iterdir(path: Path):
        if race == "process_exit" and path == descriptor_dir:
            raise FileNotFoundError("fixture process exit")
        return original_iterdir(path)

    def guarded_stat(path: Path, *args: Any, **kwargs: Any):
        if race == "descriptor_close" and path == descriptor:
            raise ProcessLookupError("fixture descriptor close")
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "iterdir", guarded_iterdir)
    monkeypatch.setattr(Path, "stat", guarded_stat)

    deletion._require_no_open_target_descriptors(
        {"entries": [{"dev": 1, "ino": 2}]},
        fixture=False,
        proc=proc,
    )


def test_quiescence_refusal_precedes_every_deletion_event(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _prepare_deletion_fixture(tmp_path, monkeypatch)
    target_paths = _fixture_source_paths(state)

    def refuse_quiescence(*args: Any, **kwargs: Any) -> None:
        raise deletion.DeletionExecutionError("quiescence_unproved")

    monkeypatch.setattr(
        deletion, "_require_no_open_target_descriptors", refuse_quiescence
    )

    with pytest.raises(deletion.DeletionExecutionError):
        _execute_fixture_deletion(state)

    journal_dir = (
        state["source_work"]
        / "cycle007-storage-primary-stage"
        / "deletion-execution-journal"
    )
    events_dir = journal_dir / "events"
    assert all(path.is_file() for path in target_paths)
    assert state["sentinel"].is_file()
    assert not events_dir.exists() or not tuple(events_dir.iterdir())


def test_authorized_deletion_is_exact_file_only_and_preserves_custody(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _prepare_deletion_fixture(tmp_path, monkeypatch)
    target_paths = _fixture_source_paths(state)
    source_directories = {
        path
        for root in (state["materialization"], state["evidence"])
        for path in root.rglob("*")
        if path.is_dir()
    }
    sentinel = state["sentinel"]
    result = _execute_fixture_deletion(state)

    assert result["unlinked_receipt"]["unlinked_path_count"] == len(target_paths)
    assert result["unlinked_receipt"]["unlinked_object_count"] == state["primary"]["inventory"]["object_count"]
    assert result["unlinked_receipt"]["reclaimed_byte_forecast"] == state["finalized"]["auth"]["reclaimed_byte_forecast"]
    assert all(not path.exists() for path in target_paths)
    assert sentinel.is_file()
    assert sentinel.read_bytes() == b"do-not-delete-this-fixture-sentinel"
    assert all(path.is_dir() for path in source_directories)
    assert state["primary"]["pack_dir"].is_dir()
    assert state["imported_pack"].is_dir()
    assert (state["primary"]["pack_dir"] / "pack-manifest.json").is_file()
    assert (state["imported_pack"] / "pack-manifest.json").is_file()
    assert all(
        not any(path.iterdir())
        for root in (state["materialization"], state["evidence"])
        for path in root.glob(".cycle007-delete-quarantine-*")
    )


@pytest.mark.parametrize("tamper", ["authorization", "custody"])
def test_deletion_refuses_tampered_authorization_or_custody(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tamper: str
) -> None:
    state = _prepare_deletion_fixture(tmp_path, monkeypatch)
    target_paths = _fixture_source_paths(state)
    if tamper == "authorization":
        state["authorization"] = dict(state["authorization"])
        state["authorization"]["auth_receipt_sha256"] = "f" * 64
    else:
        state["pre_response"] = dict(state["pre_response"])
        state["pre_response"]["challenge_nonce"] = "tampered"

    with pytest.raises(deletion.DeletionExecutionError):
        _execute_fixture_deletion(state)

    assert any(path.exists() for path in target_paths)
    assert state["sentinel"].is_file()
    assert state["primary"]["pack_dir"].is_dir()
    assert state["imported_pack"].is_dir()


@pytest.mark.parametrize(
    "mutation", ["hardlink", "symlink", "inode", "hash", "size", "mode"]
)
def test_deletion_refuses_source_link_identity_content_or_mode_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    state = _prepare_deletion_fixture(tmp_path, monkeypatch)
    target = sorted(_fixture_source_paths(state))[0]
    original = target.read_bytes()
    if mutation == "hardlink":
        external = tmp_path / "external-unselected-hardlink.bin"
        os.link(target, external)
    elif mutation == "symlink":
        moved = target.with_name(target.name + ".original")
        os.replace(target, moved)
        os.symlink(moved.name, target)
    elif mutation == "inode":
        replacement = target.with_name(target.name + ".replacement")
        replacement.write_bytes(original)
        os.chmod(replacement, storage.PRIVATE_FILE_MODE)
        os.replace(replacement, target)
    elif mutation == "hash":
        assert original.endswith(b"\n")
        changed = original[:-1] + b" "
        assert changed != original
        assert len(changed) == len(original)
        target.write_bytes(changed)
        os.chmod(target, storage.PRIVATE_FILE_MODE)
    elif mutation == "size":
        target.write_bytes(original + b" ")
        os.chmod(target, storage.PRIVATE_FILE_MODE)
    else:
        target.chmod(0o640)

    with pytest.raises(deletion.DeletionExecutionError):
        _execute_fixture_deletion(state)

    assert target.exists() or mutation == "hardlink"
    assert state["sentinel"].is_file()
    assert state["primary"]["pack_dir"].is_dir()
    assert state["imported_pack"].is_dir()


class _SyntheticDeletionCrash(RuntimeError):
    pass


@pytest.mark.parametrize(
    "crash_point",
    [
        "before_intent",
        "after_intent",
        "after_move",
        "after_move_fsync",
        "after_unlink",
        "after_parent_fsync",
        "before_unlinked_event",
    ],
)
def test_deletion_crash_resume_uses_durable_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, crash_point: str
) -> None:
    state = _prepare_deletion_fixture(tmp_path, monkeypatch)
    target_paths = _fixture_source_paths(state)
    crashed = False

    def fault_hook(event: Any) -> None:
        nonlocal crashed
        event_name = event.get("event") if isinstance(event, Mapping) else event
        normalized = str(event_name).replace("-", "_").upper()
        expected = crash_point.replace("-", "_").upper()
        if not crashed and normalized == expected:
            crashed = True
            raise _SyntheticDeletionCrash(crash_point)

    with pytest.raises(_SyntheticDeletionCrash):
        _execute_fixture_deletion(state, fault_hook=fault_hook)
    assert crashed is True
    journal_dir = (
        state["source_work"]
        / "cycle007-storage-primary-stage"
        / "deletion-execution-journal"
    )
    events_dir = journal_dir / "events"
    journal_entries = tuple(events_dir.glob("*.json")) if events_dir.is_dir() else ()
    intent_entries = tuple(
        path
        for path in journal_entries
        if json.loads(path.read_bytes())["event_type"] == "INTENT"
    )
    if crash_point == "before_intent":
        assert not intent_entries
    else:
        assert journal_entries, "crash must leave a durable deletion journal"
        assert intent_entries

    resumed = _execute_fixture_deletion(state)
    assert resumed["unlinked_receipt"]["unlinked_path_count"] == len(target_paths)
    assert all(not path.exists() for path in target_paths)
    assert state["sentinel"].is_file()
    assert state["primary"]["pack_dir"].is_dir()
    assert state["imported_pack"].is_dir()


def test_finalize_reports_actual_free_delta_separately_from_forecast(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _prepare_deletion_fixture(tmp_path, monkeypatch)
    result = _execute_fixture_deletion(state)
    before = result["unlinked_receipt"]["source_avail_before_bytes"]
    after = result["unlinked_receipt"]["source_avail_after_bytes"]
    forecast = state["finalized"]["auth"]["reclaimed_byte_forecast"]
    post_response = deletion.workstation_deletion_custody_response_stage(
        state["primary"]["portable_export"],
        state["attested"]["attestation"],
        result["post_challenge"],
        state["imported_pack"],
        state["workstation_root"],
        source_failure_domain_token="fixture-primary-domain",
        workstation_failure_domain_token="fixture-workstation-domain",
        zstd_executable=state["bindings"].zstd_executable,
        fixture=True,
    )

    final = deletion.finalize_deletion_execution(
        state["bindings"],
        state["primary"]["inventory"],
        state["primary"]["portable_export"],
        state["authorization"],
        result,
        post_response,
        state["primary"]["pack_dir"],
    )

    assert final["filesystem_avail_before_bytes"] == before
    assert isinstance(after, int)
    assert final["actual_reclaimed_bytes"] == (
        final["filesystem_avail_at_completion_bytes"]
        - final["filesystem_avail_before_bytes"]
    )
    assert final["reclaimed_byte_forecast"] == forecast
    assert final["actual_reclaimed_bytes"] != final["reclaimed_byte_forecast"]
    assert final["forecast_is_not_actual"] is True


def _rehashed(value: Mapping[str, Any], **changes: Any) -> dict[str, Any]:
    body = {key: item for key, item in value.items() if key != "receipt_sha256"}
    body.update(changes)
    return storage._receipt(body)


def test_deletion_refuses_validly_rehashed_custody_misbinding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _prepare_deletion_fixture(tmp_path, monkeypatch)
    state["pre_response"] = _rehashed(
        state["pre_response"], initial_attestation_receipt_sha256="f" * 64
    )

    with pytest.raises(deletion.DeletionExecutionError):
        _execute_fixture_deletion(state)

    assert all(path.exists() for path in _fixture_source_paths(state))


def test_deletion_resume_refuses_validly_rehashed_plan_misbinding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _prepare_deletion_fixture(tmp_path, monkeypatch)

    def stop_before_intent(event: Mapping[str, Any]) -> None:
        if event["event"] == "before_intent":
            raise _SyntheticDeletionCrash("before_intent")

    with pytest.raises(_SyntheticDeletionCrash):
        _execute_fixture_deletion(state, fault_hook=stop_before_intent)
    plan_path = (
        state["source_work"]
        / "cycle007-storage-primary-stage"
        / "deletion-execution-journal"
        / "plan.json"
    )
    plan = json.loads(plan_path.read_bytes())
    storage._atomic_write_json(
        plan_path,
        _rehashed(plan, pre_delete_workstation_response_sha256="e" * 64),
    )

    with pytest.raises(deletion.DeletionExecutionError):
        _execute_fixture_deletion(state)


def test_deletion_resume_refuses_validly_rehashed_plan_target_substitution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _prepare_deletion_fixture(tmp_path, monkeypatch)
    authorized_paths = _fixture_source_paths(state)

    def stop_before_intent(event: Mapping[str, Any]) -> None:
        if event["event"] == "before_intent":
            raise _SyntheticDeletionCrash("before_intent")

    with pytest.raises(_SyntheticDeletionCrash):
        _execute_fixture_deletion(state, fault_hook=stop_before_intent)
    plan_path = (
        state["source_work"]
        / "cycle007-storage-primary-stage"
        / "deletion-execution-journal"
        / "plan.json"
    )
    plan = json.loads(plan_path.read_bytes())
    sentinel = state["sentinel"]
    sentinel_info = sentinel.lstat()
    sentinel_inode = (int(sentinel_info.st_dev), int(sentinel_info.st_ino))
    substituted = dict(plan["entries"][0])
    substituted.update(
        {
            "role_relative_path": "materialization/UNSELECTED-sentinel.bin",
            "role_relative_paths": ["materialization/UNSELECTED-sentinel.bin"],
            "source_path_id_sha256": storage.digest(
                b"materialization/UNSELECTED-sentinel.bin\0"
                + str(sentinel_inode).encode("ascii")
            ),
            "dev": sentinel_inode[0],
            "ino": sentinel_inode[1],
            "mode": stat.S_IMODE(sentinel_info.st_mode),
            "size_bytes": int(sentinel_info.st_size),
            "allocated_bytes": storage.allocated_bytes(sentinel),
            "sha256": storage.digest_file(sentinel),
            "expected_nlink_before": int(sentinel_info.st_nlink),
            "quarantine_role": "materialization",
        }
    )
    substituted_body = {
        key: value
        for key, value in substituted.items()
        if key not in {"entry_id", "quarantine_name"}
    }
    substituted["entry_id"] = storage.digest(storage.canonical(substituted_body))
    substituted["quarantine_name"] = f"{substituted['entry_id']}.pending"
    entries = [substituted, *plan["entries"][1:]]
    entries.sort(key=lambda item: (str(item["role_relative_path"]), str(item["entry_id"])))
    forged_plan = _rehashed(
        plan,
        entries=entries,
        entries_sha256=storage.digest(storage.canonical(entries)),
    )
    storage._atomic_write_json(plan_path, forged_plan)

    with pytest.raises(deletion.DeletionExecutionError):
        _execute_fixture_deletion(state)

    assert sentinel.is_file()
    assert sentinel.read_bytes() == b"do-not-delete-this-fixture-sentinel"
    assert all(path.exists() for path in authorized_paths)


def test_finalize_refuses_validly_rehashed_persisted_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _prepare_deletion_fixture(tmp_path, monkeypatch)
    result = _execute_fixture_deletion(state)
    post_response = deletion.workstation_deletion_custody_response_stage(
        state["primary"]["portable_export"],
        state["attested"]["attestation"],
        result["post_challenge"],
        state["imported_pack"],
        state["workstation_root"],
        source_failure_domain_token="fixture-primary-domain",
        workstation_failure_domain_token="fixture-workstation-domain",
        zstd_executable=state["bindings"].zstd_executable,
        fixture=True,
    )
    unlinked_path = (
        state["source_work"]
        / "cycle007-storage-primary-stage"
        / "deletion-execution-journal"
        / "unlinked.json"
    )
    unlinked = json.loads(unlinked_path.read_bytes())
    storage._atomic_write_json(
        unlinked_path,
        _rehashed(unlinked, journal_terminal_event_sha256="d" * 64),
    )

    with pytest.raises(deletion.DeletionExecutionError):
        deletion.finalize_deletion_execution(
            state["bindings"],
            state["primary"]["inventory"],
            state["primary"]["portable_export"],
            state["authorization"],
            result,
            post_response,
            state["primary"]["pack_dir"],
        )


def test_finalize_resume_refuses_validly_rehashed_completion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _prepare_deletion_fixture(tmp_path, monkeypatch)
    result = _execute_fixture_deletion(state)
    post_response = deletion.workstation_deletion_custody_response_stage(
        state["primary"]["portable_export"],
        state["attested"]["attestation"],
        result["post_challenge"],
        state["imported_pack"],
        state["workstation_root"],
        source_failure_domain_token="fixture-primary-domain",
        workstation_failure_domain_token="fixture-workstation-domain",
        zstd_executable=state["bindings"].zstd_executable,
        fixture=True,
    )
    deletion.finalize_deletion_execution(
        state["bindings"],
        state["primary"]["inventory"],
        state["primary"]["portable_export"],
        state["authorization"],
        result,
        post_response,
        state["primary"]["pack_dir"],
    )
    completion_path = (
        state["source_work"]
        / "cycle007-storage-primary-stage"
        / "deletion-execution-journal"
        / "completion.json"
    )
    completion = json.loads(completion_path.read_bytes())
    storage._atomic_write_json(
        completion_path, _rehashed(completion, directories_removed=1)
    )

    with pytest.raises(deletion.DeletionExecutionError):
        deletion.finalize_deletion_execution(
            state["bindings"],
            state["primary"]["inventory"],
            state["primary"]["portable_export"],
            state["authorization"],
            result,
            post_response,
            state["primary"]["pack_dir"],
        )


def _systemd_proc_stat(pid: int, *, ppid: int = 1, start_time: int = 12345) -> bytes:
    # /proc/PID/stat fields 4..22 are ppid followed by starttime at field 22.
    tail = [str(ppid), *(["0"] * 17), str(start_time)]
    assert len(tail) == 19
    return f"{pid} (systemd) S {' '.join(tail)}\n".encode("ascii")


def _systemd_proc_fixture(
    tmp_path: Path,
    *,
    pid: int = 48001,
    uid: int | None = None,
    comm: bytes = b"systemd\n",
    cgroup: bytes | None = None,
    argv0: bytes = b"/usr/lib/systemd/systemd",
    deserialize: bytes = b"--deserialize=123",
    extra_argv: tuple[bytes, ...] = (),
    final_nul: bool = True,
    status: bytes | None = None,
    stat_bytes: bytes | None = None,
) -> tuple[Path, Path]:
    proc = tmp_path / "proc-systemd-fixture"
    process = proc / str(pid)
    fd_dir = process / "fd"
    fd_dir.mkdir(parents=True)
    own_uid = os.geteuid() if uid is None else uid
    if cgroup is None:
        cgroup = (
            f"0::/user.slice/user-{own_uid}.slice/"
            f"user@{own_uid}.service/init.scope\n"
        ).encode("ascii")
    if status is None:
        status = f"Name:\tsystemd\nUid:\t{own_uid}\t{own_uid}\t{own_uid}\t{own_uid}\n".encode(
            "ascii"
        )
    if stat_bytes is None:
        stat_bytes = _systemd_proc_stat(pid)
    argv = (argv0, b"--user", deserialize, *extra_argv)
    cmdline = b"\0".join(argv) + (b"\0" if final_nul else b"")
    (process / "comm").write_bytes(comm)
    (process / "cgroup").write_bytes(cgroup)
    (process / "cmdline").write_bytes(cmdline)
    (process / "status").write_bytes(status)
    (process / "stat").write_bytes(stat_bytes)
    return proc, fd_dir


def _systemd_plan() -> dict[str, Any]:
    return {"entries": [{"dev": 1, "ino": 2}]}


def _deny_individual_descriptor(
    monkeypatch: pytest.MonkeyPatch, descriptor: Path
) -> None:
    original_stat = Path.stat

    def denied_stat(path: Path, *args: Any, **kwargs: Any):
        if path == descriptor:
            raise PermissionError("fixture individual fd denied")
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", denied_stat)


@pytest.mark.parametrize(
    "argv0", [b"/usr/lib/systemd/systemd", b"/lib/systemd/systemd"]
)
def test_quiescence_accepts_exact_attested_systemd_user_manager_argv0(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, argv0: bytes
) -> None:
    proc, fd_dir = _systemd_proc_fixture(tmp_path, argv0=argv0)
    descriptor = fd_dir / "0"
    descriptor.touch()
    _deny_individual_descriptor(monkeypatch, descriptor)

    deletion._require_no_open_target_descriptors(
        _systemd_plan(), fixture=False, proc=proc
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("stat_bytes", b"not-a-proc-stat\n"),
        ("status", b"Name:\tsystemd\nUid:\tbroken\n"),
        ("cgroup", b"0::/user.slice/user-999.slice/user@999.service/init.scope\n"),
        ("comm", b"systemd\r\n"),
        ("cgroup", b"0::/user.slice/user-48001.slice/user@48001.service/init.scope\r\n"),
        ("status", b"Name:\tsystemd\r\nUid:\t0 0 0 0\r\n"),
    ],
)
def test_quiescence_rejects_malformed_systemd_attestation_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: bytes,
) -> None:
    kwargs: dict[str, Any] = {field: value}
    proc, fd_dir = _systemd_proc_fixture(tmp_path, **kwargs)
    descriptor = fd_dir / "0"
    descriptor.touch()
    _deny_individual_descriptor(monkeypatch, descriptor)

    with pytest.raises(deletion.DeletionExecutionError):
        deletion._require_no_open_target_descriptors(
            _systemd_plan(), fixture=False, proc=proc
        )


@pytest.mark.parametrize(
    "cmdline_kwargs",
    [
        {"final_nul": False},
        {"deserialize": b"--deserialize="},
        {"deserialize": b"--deserialize=00123"},
        {"deserialize": b"--deserialize=+123"},
        {"deserialize": b"--deserialize= 123"},
        {"extra_argv": (b"unexpected",)},
    ],
)
def test_quiescence_rejects_noncanonical_systemd_cmdline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    cmdline_kwargs: dict[str, Any],
) -> None:
    proc, fd_dir = _systemd_proc_fixture(tmp_path, **cmdline_kwargs)
    descriptor = fd_dir / "0"
    descriptor.touch()
    _deny_individual_descriptor(monkeypatch, descriptor)

    with pytest.raises(deletion.DeletionExecutionError):
        deletion._require_no_open_target_descriptors(
            _systemd_plan(), fixture=False, proc=proc
        )


@pytest.mark.parametrize(
    "status",
    [
        b"Name:\tsystemd\nUid:\t0 0 0 1\n",
        b"Name:\tsystemd\nUid:\t0 0 0\n",
        b"Name:\tsystemd\nUid:\t0 0 0 0 0\n",
    ],
)
def test_quiescence_rejects_systemd_status_uid_shape_or_ownership_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: bytes
) -> None:
    proc, fd_dir = _systemd_proc_fixture(tmp_path, status=status)
    descriptor = fd_dir / "0"
    descriptor.touch()
    _deny_individual_descriptor(monkeypatch, descriptor)

    with pytest.raises(deletion.DeletionExecutionError):
        deletion._require_no_open_target_descriptors(
            _systemd_plan(), fixture=False, proc=proc
        )


def test_quiescence_rejects_systemd_ppid_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proc, fd_dir = _systemd_proc_fixture(
        tmp_path, stat_bytes=_systemd_proc_stat(48001, ppid=2)
    )
    descriptor = fd_dir / "0"
    descriptor.touch()

    # PPID is validated on the attestation path, which is entered only when
    # an individual descriptor cannot be inspected.
    _deny_individual_descriptor(monkeypatch, descriptor)
    with pytest.raises(deletion.DeletionExecutionError):
        deletion._require_no_open_target_descriptors(
            _systemd_plan(), fixture=False, proc=proc
        )


def test_quiescence_rejects_systemd_differing_status_uid_ownership(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    uid = os.geteuid()
    status = f"Name:\tsystemd\nUid:\t{uid}\t{uid}\t{uid}\t{uid + 1}\n".encode(
        "ascii"
    )
    proc, fd_dir = _systemd_proc_fixture(tmp_path, status=status)
    descriptor = fd_dir / "0"
    descriptor.touch()
    _deny_individual_descriptor(monkeypatch, descriptor)
    with pytest.raises(deletion.DeletionExecutionError):
        deletion._require_no_open_target_descriptors(
            _systemd_plan(), fixture=False, proc=proc
        )


@pytest.mark.parametrize(
    "comm", [b"systemd-user\n", b"Systemd\n", b"systemd \n", b"systemd\r\n"]
)
def test_quiescence_rejects_near_systemd_comm(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, comm: bytes
) -> None:
    proc, fd_dir = _systemd_proc_fixture(tmp_path, comm=comm)
    descriptor = fd_dir / "0"
    descriptor.touch()
    _deny_individual_descriptor(monkeypatch, descriptor)

    with pytest.raises(deletion.DeletionExecutionError):
        deletion._require_no_open_target_descriptors(
            _systemd_plan(), fixture=False, proc=proc
        )


@pytest.mark.parametrize("disappearance", [False, True])
def test_quiescence_rejects_systemd_pid_start_time_drift_or_disappearance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    disappearance: bool,
) -> None:
    proc, fd_dir = _systemd_proc_fixture(tmp_path)
    descriptor = fd_dir / "0"
    descriptor.touch()
    _deny_individual_descriptor(monkeypatch, descriptor)
    stat_path = proc / "48001" / "stat"
    original_read_bytes = Path.read_bytes
    reads = 0

    def changing_read_bytes(path: Path) -> bytes:
        nonlocal reads
        if path == stat_path:
            reads += 1
            if reads >= 2:
                if disappearance:
                    raise FileNotFoundError("fixture PID exited")
                return _systemd_proc_stat(48001, start_time=67890)
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", changing_read_bytes)
    with pytest.raises(deletion.DeletionExecutionError):
        deletion._require_no_open_target_descriptors(
            _systemd_plan(), fixture=False, proc=proc
        )
    assert reads >= 2


def test_quiescence_rejects_systemd_generation_change_during_fd_enumeration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    proc, fd_dir = _systemd_proc_fixture(tmp_path)
    descriptor = fd_dir / "0"
    descriptor.touch()
    _deny_individual_descriptor(monkeypatch, descriptor)
    stat_path = proc / "48001" / "stat"
    original_iterdir = Path.iterdir
    original_read_bytes = Path.read_bytes
    enumerated = False

    def changing_iterdir(path: Path):
        nonlocal enumerated
        if path == fd_dir:
            enumerated = True
        return original_iterdir(path)

    def changing_read_bytes(path: Path) -> bytes:
        if path == stat_path and enumerated:
            return _systemd_proc_stat(48001, start_time=67890)
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "iterdir", changing_iterdir)
    monkeypatch.setattr(Path, "read_bytes", changing_read_bytes)

    with pytest.raises(deletion.DeletionExecutionError):
        deletion._require_no_open_target_descriptors(
            _systemd_plan(), fixture=False, proc=proc
        )


def test_quiescence_rejects_any_readable_systemd_target_inode(
    tmp_path: Path,
) -> None:
    proc, fd_dir = _systemd_proc_fixture(tmp_path)
    target = tmp_path / "authorized-target.bin"
    target.write_bytes(b"target")
    (fd_dir / "0").symlink_to(target)
    info = target.stat()

    with pytest.raises(deletion.DeletionExecutionError):
        deletion._require_no_open_target_descriptors(
            {
                "entries": [
                    {"dev": int(info.st_dev), "ino": int(info.st_ino)},
                ]
            },
            fixture=False,
            proc=proc,
        )
    assert target.read_bytes() == b"target"


def test_quiescence_rejects_systemd_fd_directory_permission_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proc, fd_dir = _systemd_proc_fixture(tmp_path)
    original_iterdir = Path.iterdir

    def denied_iterdir(path: Path):
        if path == fd_dir:
            raise PermissionError("fixture systemd fd table denied")
        return original_iterdir(path)

    monkeypatch.setattr(Path, "iterdir", denied_iterdir)
    with pytest.raises(deletion.DeletionExecutionError):
        deletion._require_no_open_target_descriptors(
            _systemd_plan(), fixture=False, proc=proc
        )


def test_quiescence_allows_only_attested_systemd_individual_descriptor_denial(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proc, fd_dir = _systemd_proc_fixture(tmp_path)
    descriptor = fd_dir / "0"
    descriptor.touch()
    original_stat = Path.stat

    def denied_stat(path: Path, *args: Any, **kwargs: Any):
        if path == descriptor:
            raise PermissionError("fixture individual systemd fd denied")
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", denied_stat)
    deletion._require_no_open_target_descriptors(
        _systemd_plan(), fixture=False, proc=proc
    )


def test_quiescence_rejects_non_attested_individual_descriptor_denial(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proc, fd_dir = _systemd_proc_fixture(tmp_path, comm=b"ordinary-worker\n")
    descriptor = fd_dir / "0"
    descriptor.touch()
    original_stat = Path.stat

    def denied_stat(path: Path, *args: Any, **kwargs: Any):
        if path == descriptor:
            raise PermissionError("fixture individual fd denied")
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", denied_stat)
    with pytest.raises(deletion.DeletionExecutionError):
        deletion._require_no_open_target_descriptors(
            _systemd_plan(), fixture=False, proc=proc
        )


def test_quiescence_rejects_mixed_denied_systemd_fd_and_visible_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proc, fd_dir = _systemd_proc_fixture(tmp_path)
    denied = fd_dir / "0"
    denied.touch()
    target = tmp_path / "authorized-target.bin"
    target.write_bytes(b"target")
    visible = fd_dir / "1"
    visible.symlink_to(target)
    info = target.stat()
    original_stat = Path.stat

    def mixed_stat(path: Path, *args: Any, **kwargs: Any):
        if path == denied:
            raise PermissionError("fixture individual systemd fd denied")
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", mixed_stat)
    with pytest.raises(deletion.DeletionExecutionError):
        deletion._require_no_open_target_descriptors(
            {
                "entries": [{"dev": int(info.st_dev), "ino": int(info.st_ino)}]
            },
            fixture=False,
            proc=proc,
        )
    assert target.read_bytes() == b"target"


def test_systemd_quiescence_refusal_precedes_journal_and_source_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _prepare_deletion_fixture(tmp_path, monkeypatch)
    proc, fd_dir = _systemd_proc_fixture(tmp_path)
    original_require = deletion._require_no_open_target_descriptors
    original_iterdir = Path.iterdir

    def denied_iterdir(path: Path):
        if path == fd_dir:
            raise PermissionError("fixture systemd fd table denied")
        return original_iterdir(path)

    def force_quiescence(plan: Mapping[str, Any], *, fixture: bool) -> None:
        original_require(plan, fixture=False, proc=proc)

    monkeypatch.setattr(Path, "iterdir", denied_iterdir)
    monkeypatch.setattr(deletion, "_require_no_open_target_descriptors", force_quiescence)
    targets = _fixture_source_paths(state)

    with pytest.raises(deletion.DeletionExecutionError):
        _execute_fixture_deletion(state)

    journal_root = (
        state["source_work"]
        / "cycle007-storage-primary-stage"
        / "deletion-execution-journal"
    )
    events = journal_root / "events"
    assert not events.exists() or not tuple(events.iterdir())
    assert all(path.is_file() for path in targets)
    assert state["sentinel"].is_file()
    assert state["primary"]["pack_dir"].is_dir()
    assert state["imported_pack"].is_dir()


def _fixture_deletion_journal_root(state: Mapping[str, Any]) -> Path:
    return (
        state["source_work"]
        / "cycle007-storage-primary-stage"
        / "deletion-execution-journal"
    )


def test_new_deletion_moves_use_exact_source_parent_even_when_role_root_shares_device(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _prepare_deletion_fixture(tmp_path, monkeypatch)
    target_paths = _fixture_source_paths(state)
    real_fstat = os.fstat

    def crash_after_intent(event: Mapping[str, Any]) -> None:
        if event["event"] == "after_intent":
            raise _SyntheticDeletionCrash("after_intent")

    with pytest.raises(_SyntheticDeletionCrash):
        _execute_fixture_deletion(state, fault_hook=crash_after_intent)

    journal_root = _fixture_deletion_journal_root(state)
    plan_path = journal_root / "plan.json"
    plan = json.loads(plan_path.read_bytes())
    role_root_ids = set()
    for role in ("materialization", "evidence"):
        role_root = deletion._role_root(state["bindings"], role)
        quarantine = role_root / plan["quarantine_directory_name"]
        info = quarantine.stat()
        role_root_ids.add((int(info.st_dev), int(info.st_ino)))

    real_rename = deletion._rename_noreplace
    rename_parent_pairs: list[tuple[tuple[int, int], tuple[int, int]]] = []
    role_root_rename_attempts: list[tuple[int, str]] = []

    def recording_rename(
        source_parent: int,
        source_name: str,
        destination_parent: int,
        destination_name: str,
        **kwargs: Any,
    ) -> None:
        source_info = real_fstat(source_parent)
        destination_info = real_fstat(destination_parent)
        source_identity = (int(source_info.st_dev), int(source_info.st_ino))
        destination_identity = (int(destination_info.st_dev), int(destination_info.st_ino))
        rename_parent_pairs.append((source_identity, destination_identity))
        if destination_identity in role_root_ids:
            role_root_rename_attempts.append((destination_parent, destination_name))
            # A bind mount can report the same st_dev while rename still fails
            # with EXDEV.  The production path must not try this destination.
            raise OSError(errno.EXDEV, "modeled bind-mount quarantine EXDEV")
        real_rename(
            source_parent,
            source_name,
            destination_parent,
            destination_name,
            **kwargs,
        )

    monkeypatch.setattr(deletion, "_rename_noreplace", recording_rename)

    resumed = _execute_fixture_deletion(state)

    assert rename_parent_pairs
    assert all(source == destination for source, destination in rename_parent_pairs)
    assert role_root_rename_attempts == []
    assert resumed["unlinked_receipt"]["unlinked_path_count"] == int(plan["entry_count"])
    assert all(not path.exists() for path in target_paths)
    assert state["sentinel"].is_file()
    assert all(
        int(
            (
                deletion._role_root(state["bindings"], str(entry["quarantine_role"]))
                / plan["quarantine_directory_name"]
            ).stat().st_dev
        )
        == int(entry["dev"])
        for entry in plan["entries"]
    )
    for role in ("materialization", "evidence"):
        quarantine = (
            deletion._role_root(state["bindings"], role)
            / plan["quarantine_directory_name"]
        )
        assert quarantine.is_dir()
        assert not any(quarantine.iterdir())


def test_deletion_recovers_same_device_legacy_moved_state_without_rewriting_plan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _prepare_deletion_fixture(tmp_path, monkeypatch)
    target_paths = _fixture_source_paths(state)

    def crash_after_intent(event: Mapping[str, Any]) -> None:
        if event["event"] == "after_intent":
            raise _SyntheticDeletionCrash("after_intent")

    with pytest.raises(_SyntheticDeletionCrash):
        _execute_fixture_deletion(state, fault_hook=crash_after_intent)

    journal_root = _fixture_deletion_journal_root(state)
    plan_path = journal_root / "plan.json"
    plan_bytes = plan_path.read_bytes()
    plan = json.loads(plan_bytes)
    events_dir = journal_root / "events"
    events = deletion._load_events(journal_root, plan)
    assert [event["event_type"] for event in events] == [
        "START",
        "INTENT",
    ]
    first = plan["entries"][0]
    first_source = deletion._role_path(
        state["bindings"], str(first["role_relative_path"])
    )
    legacy_quarantine = (
        deletion._role_root(state["bindings"], str(first["quarantine_role"]))
        / plan["quarantine_directory_name"]
        / first["quarantine_name"]
    )
    assert not legacy_quarantine.exists()
    os.rename(first_source, legacy_quarantine)
    deletion._append_event(
        journal_root,
        plan,
        events,
        "MOVED",
        entry_id=str(first["entry_id"]),
    )
    assert not first_source.exists()
    assert legacy_quarantine.is_file()

    resumed = _execute_fixture_deletion(state)

    events_after = [json.loads(path.read_bytes()) for path in sorted(events_dir.glob("*.json"))]
    assert any(event["event_type"] == "RECOVERED_UNLINKED" for event in events_after)
    assert resumed["unlinked_receipt"]["all_authorized_entries_absent"] is True
    assert plan_path.read_bytes() == plan_bytes
    assert all(not path.exists() for path in target_paths)
    assert state["sentinel"].is_file()


def test_legacy_moved_unlink_crash_resume_fsyncs_both_dirs_before_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _prepare_deletion_fixture(tmp_path, monkeypatch)
    target_paths = _fixture_source_paths(state)

    def crash_after_intent(event: Mapping[str, Any]) -> None:
        if event["event"] == "after_intent":
            raise _SyntheticDeletionCrash("after_intent")

    with pytest.raises(_SyntheticDeletionCrash):
        _execute_fixture_deletion(state, fault_hook=crash_after_intent)

    journal_root = _fixture_deletion_journal_root(state)
    plan_path = journal_root / "plan.json"
    plan = json.loads(plan_path.read_bytes())
    events = deletion._load_events(journal_root, plan)
    first = plan["entries"][0]
    source = deletion._role_path(
        state["bindings"], str(first["role_relative_path"])
    )
    source_parent = source.parent
    legacy_directory = (
        deletion._role_root(state["bindings"], str(first["quarantine_role"]))
        / plan["quarantine_directory_name"]
    )
    legacy_slot = legacy_directory / str(first["quarantine_name"])
    source_parent_identity = (
        int(source_parent.stat().st_dev),
        int(source_parent.stat().st_ino),
    )
    legacy_directory_identity = (
        int(legacy_directory.stat().st_dev),
        int(legacy_directory.stat().st_ino),
    )

    # Persist a genuine old-format MOVED state: the exact object is in the
    # role-root slot, not the new source-parent slot, before the unlink starts.
    os.rename(source, legacy_slot)
    deletion._append_event(
        journal_root,
        plan,
        events,
        "MOVED",
        entry_id=str(first["entry_id"]),
    )
    assert not source.exists()
    assert legacy_slot.is_file()

    def crash_after_legacy_unlink(event: Mapping[str, Any]) -> None:
        if event["event"] == "after_unlink":
            raise _SyntheticDeletionCrash("after_legacy_unlink")

    with pytest.raises(_SyntheticDeletionCrash):
        _execute_fixture_deletion(state, fault_hook=crash_after_legacy_unlink)

    assert not source.exists()
    assert not legacy_slot.exists()
    events_after_crash = [
        json.loads(path.read_bytes())
        for path in sorted((journal_root / "events").glob("*.json"))
    ]
    assert [event["event_type"] for event in events_after_crash] == [
        "START",
        "INTENT",
        "MOVED",
    ]

    real_fstat = os.fstat
    real_fsync = os.fsync
    fsync_identities: list[tuple[int, int]] = []
    recovered_event_fsyncs: list[tuple[tuple[int, int], ...]] = []

    def traced_fsync(descriptor: int) -> None:
        info = real_fstat(descriptor)
        fsync_identities.append((int(info.st_dev), int(info.st_ino)))
        real_fsync(descriptor)

    real_append_event = deletion._append_event

    def traced_append_event(
        root: Path,
        persisted_plan: Mapping[str, Any],
        persisted_events: list[dict[str, Any]],
        event_type: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        if event_type == "RECOVERED_UNLINKED":
            recovered_event_fsyncs.append(tuple(fsync_identities))
        return real_append_event(
            root,
            persisted_plan,
            persisted_events,
            event_type,
            **kwargs,
        )

    monkeypatch.setattr(os, "fsync", traced_fsync)
    monkeypatch.setattr(deletion, "_append_event", traced_append_event)
    resumed = _execute_fixture_deletion(state)

    assert resumed["unlinked_receipt"]["all_authorized_entries_absent"] is True
    assert recovered_event_fsyncs
    fsyncs_before_recovered_event = recovered_event_fsyncs[0]
    assert source_parent_identity in fsyncs_before_recovered_event
    assert legacy_directory_identity in fsyncs_before_recovered_event
    assert all(not path.exists() for path in target_paths)
    assert state["sentinel"].is_file()


@pytest.mark.parametrize(
    "recovery_drift",
    ["both_exact_slots", "wrong_source_slot", "wrong_legacy_slot", "source_topology"],
)
def test_deletion_recovery_probes_both_exact_slots_and_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    recovery_drift: str,
) -> None:
    state = _prepare_deletion_fixture(tmp_path, monkeypatch)
    target_paths = _fixture_source_paths(state)

    def crash_after_intent(event: Mapping[str, Any]) -> None:
        if event["event"] == "after_intent":
            raise _SyntheticDeletionCrash("after_intent")

    with pytest.raises(_SyntheticDeletionCrash):
        _execute_fixture_deletion(state, fault_hook=crash_after_intent)

    journal_root = _fixture_deletion_journal_root(state)
    plan_path = journal_root / "plan.json"
    plan_bytes = plan_path.read_bytes()
    plan = json.loads(plan_bytes)
    events_dir = journal_root / "events"
    first = plan["entries"][0]
    source = deletion._role_path(
        state["bindings"], str(first["role_relative_path"])
    )
    source_bytes = source.read_bytes()
    source_slot = source.parent / str(first["quarantine_name"])
    legacy_slot = (
        deletion._role_root(state["bindings"], str(first["quarantine_role"]))
        / plan["quarantine_directory_name"]
        / str(first["quarantine_name"])
    )
    displaced = tmp_path / "source-topology-drift.bin"

    if recovery_drift == "both_exact_slots":
        os.link(source, source_slot)
        os.link(source, legacy_slot)
    elif recovery_drift == "wrong_source_slot":
        source_slot.write_bytes(b"wrong-source-slot")
        os.chmod(source_slot, storage.PRIVATE_FILE_MODE)
    elif recovery_drift == "wrong_legacy_slot":
        legacy_slot.write_bytes(b"wrong-legacy-slot")
        os.chmod(legacy_slot, storage.PRIVATE_FILE_MODE)
    else:
        os.rename(source, displaced)

    with pytest.raises(deletion.DeletionExecutionError):
        _execute_fixture_deletion(state)

    assert plan_path.read_bytes() == plan_bytes
    events_after = [
        json.loads(path.read_bytes()) for path in sorted(events_dir.glob("*.json"))
    ]
    assert [event["event_type"] for event in events_after] == ["START", "INTENT"]
    if recovery_drift == "source_topology":
        assert not source.exists()
        assert displaced.read_bytes() == source_bytes
    else:
        assert all(path.is_file() for path in target_paths)
    if recovery_drift == "both_exact_slots":
        assert source_slot.is_file()
        assert legacy_slot.is_file()
    elif recovery_drift == "wrong_source_slot":
        assert source_slot.read_bytes() == b"wrong-source-slot"
        assert not legacy_slot.exists()
    elif recovery_drift == "wrong_legacy_slot":
        assert legacy_slot.read_bytes() == b"wrong-legacy-slot"
        assert not source_slot.exists()


def test_rename_noreplace_never_overwrites_an_existing_quarantine_slot(
    tmp_path: Path,
) -> None:
    source_parent = tmp_path / "source-parent"
    destination_parent = tmp_path / "destination-parent"
    source_parent.mkdir(mode=storage.PRIVATE_DIR_MODE)
    destination_parent.mkdir(mode=storage.PRIVATE_DIR_MODE)
    source = source_parent / "payload"
    destination = destination_parent / "slot"
    source.write_bytes(b"authorized-source")
    destination.write_bytes(b"unrelated-existing-slot")
    os.chmod(source, storage.PRIVATE_FILE_MODE)
    os.chmod(destination, storage.PRIVATE_FILE_MODE)
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    source_descriptor = os.open(source_parent, flags)
    destination_descriptor = os.open(destination_parent, flags)
    try:
        with pytest.raises(deletion.DeletionExecutionError):
            deletion._rename_noreplace(
                source_descriptor,
                "payload",
                destination_descriptor,
                "slot",
                fixture=True,
            )
    finally:
        os.close(source_descriptor)
        os.close(destination_descriptor)
    assert source.read_bytes() == b"authorized-source"
    assert destination.read_bytes() == b"unrelated-existing-slot"


def test_deletion_handles_overlapping_aliases_without_enumerating_or_removing_parents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _prepare_deletion_fixture(
        tmp_path,
        monkeypatch,
        overlapping_evidence=True,
    )
    inventory = state["primary"]["inventory"]
    alias_objects = [
        item for item in inventory["objects"] if len(item["role_relative_paths"]) > 1
    ]
    assert alias_objects
    target_paths = _fixture_source_paths(state)
    target_parents = {path.parent for path in target_paths}
    source_directories = {
        path
        for root in (state["materialization"], state["evidence"])
        for path in root.rglob("*")
        if path.is_dir()
    }
    directory_identity = {
        path: (int(path.stat().st_dev), int(path.stat().st_ino))
        for path in source_directories
    }
    enumerated_source_parents: list[Path] = []
    original_iterdir = Path.iterdir

    def guarded_iterdir(path: Path):
        if path in target_parents:
            enumerated_source_parents.append(path)
        return original_iterdir(path)

    monkeypatch.setattr(Path, "iterdir", guarded_iterdir)
    result = _execute_fixture_deletion(state)
    monkeypatch.setattr(Path, "iterdir", original_iterdir)

    assert not enumerated_source_parents
    assert result["unlinked_receipt"]["unlinked_inode_count"] == inventory["object_count"]
    assert result["unlinked_receipt"]["directories_removed"] == 0
    assert all(not path.exists() for path in target_paths)
    for item in alias_objects:
        for alias in item["role_relative_paths"]:
            assert not deletion._role_path(state["bindings"], str(alias)).exists()
    for path, identity in directory_identity.items():
        info = path.stat()
        assert path.is_dir()
        assert (int(info.st_dev), int(info.st_ino)) == identity
    assert state["primary"]["pack_dir"].is_dir()
    assert state["imported_pack"].is_dir()


def test_deletion_resume_accepts_persisted_plan_and_receipts_without_rewriting_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _prepare_deletion_fixture(tmp_path, monkeypatch)
    target_paths = _fixture_source_paths(state)

    def crash_after_intent(event: Mapping[str, Any]) -> None:
        if event["event"] == "after_intent":
            raise _SyntheticDeletionCrash("after_intent")

    with pytest.raises(_SyntheticDeletionCrash):
        _execute_fixture_deletion(state, fault_hook=crash_after_intent)

    stage_root = state["source_work"] / "cycle007-storage-primary-stage"
    journal_root = stage_root / "deletion-execution-journal"
    plan_path = journal_root / "plan.json"
    plan_bytes = plan_path.read_bytes()
    events_before = {
        path.name: path.read_bytes()
        for path in sorted((journal_root / "events").glob("*.json"))
    }

    # Rehydrate every input that the executor persists.  This models a fresh
    # process resuming from the existing plan/journal rather than a live dict.
    state["primary"]["primary_stage"] = json.loads(
        (stage_root / "primary-stage.json").read_bytes()
    )
    state["primary"]["portable_export"] = json.loads(
        (stage_root / "portable-export.json").read_bytes()
    )
    state["primary"]["inventory"] = json.loads((stage_root / "inventory.json").read_bytes())
    state["primary"]["pack_manifest"] = json.loads(
        (stage_root / "pack-manifest.receipt.json").read_bytes()
    )
    state["finalized"]["finalize"] = json.loads((stage_root / "finalize.json").read_bytes())
    state["finalized"]["auth"] = json.loads(
        (stage_root / "deletion-auth-request.json").read_bytes()
    )
    state["authorization"] = json.loads(
        (journal_root / "operator-authorization.json").read_bytes()
    )
    state["challenge"] = json.loads((journal_root / "challenge.json").read_bytes())
    state["pre_response"] = json.loads(
        (journal_root / "pre-delete-workstation-response.json").read_bytes()
    )

    resumed = _execute_fixture_deletion(state)

    assert resumed["unlinked_receipt"]["all_authorized_entries_absent"] is True
    assert plan_path.read_bytes() == plan_bytes
    assert {
        path.name: path.read_bytes()
        for path in sorted((journal_root / "events").glob("*.json"))
        if path.name in events_before
    } == events_before
    assert all(not path.exists() for path in target_paths)
    assert state["sentinel"].is_file()
