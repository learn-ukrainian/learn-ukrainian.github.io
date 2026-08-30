#!/usr/bin/env python3
"""Authorized, exact-entry Cycle007 expanded-source deletion (#7434).

This is deliberately separate from the reversible custody lane.  It consumes
that lane's exact authorization request, proves both compact copies, journals
every individual directory-entry unlink, and never removes a directory.
Private paths remain private; durable receipts use only role-relative aliases
and opaque filesystem identities.
"""

from __future__ import annotations

import contextlib
import ctypes
import fcntl
import hashlib
import os
import secrets
import stat
import sys
from collections.abc import Callable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any

from scripts.projects.open_model_data import phase3_cycle007_storage_custody as storage

AUTHORIZED_REQUEST_SHA256 = "e3c464f5f97aeb0e8314e98526043ebb9ce9571ca2125d2c7fe46c6bd554cc5b"
AUTHORIZED_RECLAIMED_BYTES = 86_922_608_640
OPERATOR_AUTH_SCHEMA = "phase3_cycle007_storage_operator_authorization_v1"
EXECUTION_CHALLENGE_SCHEMA = "phase3_cycle007_storage_deletion_challenge_v1"
CUSTODY_RESPONSE_SCHEMA = "phase3_cycle007_storage_deletion_custody_response_v1"
PLAN_SCHEMA = "phase3_cycle007_storage_deletion_plan_v1"
EVENT_SCHEMA = "phase3_cycle007_storage_deletion_event_v1"
UNLINKED_SCHEMA = "phase3_cycle007_storage_deletion_unlinked_v1"
POST_CHALLENGE_SCHEMA = "phase3_cycle007_storage_post_deletion_challenge_v1"
COMPLETION_SCHEMA = "phase3_cycle007_storage_deletion_completion_v1"

DELETE_ROOT = "cycle007-storage-primary-stage/deletion-execution-journal"
FAULT_POINTS = frozenset(
    {
        "before_intent",
        "after_intent",
        "after_move",
        "after_move_fsync",
        "after_unlink",
        "after_parent_fsync",
        "before_unlinked_event",
    }
)
RENAME_NOREPLACE = 1
UNINSPECTABLE_QUIESCENCE_PROCESS_ALLOWLIST = frozenset(
    {
        "(sd-pam)",
        "ssh-agent",
        "sshd-session",
    }
)
SYSTEMD_USER_MANAGER_ARGV0_ALLOWLIST = frozenset(
    {
        b"/lib/systemd/systemd",
        b"/usr/lib/systemd/systemd",
    }
)


class DeletionExecutionError(ValueError):
    """Fail-closed exact deletion error represented by a safe code."""


def _fail(code: str) -> None:
    raise DeletionExecutionError(code)


def _require(condition: bool, code: str) -> None:
    if not condition:
        _fail(code)


def _require_receipt(value: Mapping[str, Any], code: str) -> None:
    try:
        storage._require_receipt(value, code)
    except storage.StorageCustodyError as exc:
        raise DeletionExecutionError(code) from exc


def _receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    return storage._receipt(value)


def _read_receipt(path: Path, schema: str, code: str) -> dict[str, Any]:
    try:
        value = storage._read_json(path, code)
    except storage.StorageCustodyError as exc:
        raise DeletionExecutionError(code) from exc
    _require(isinstance(value, Mapping), code)
    result = dict(value)
    _require_receipt(result, code)
    _require(result.get("schema_version") == schema, code)
    return result


def _write_new_receipt(path: Path, value: Mapping[str, Any], code: str) -> None:
    if os.path.lexists(path):
        _fail(code)
    try:
        storage._atomic_write_json(path, value)
    except OSError as exc:
        raise DeletionExecutionError(code) from exc


def _persist_or_match_receipt(path: Path, value: Mapping[str, Any], schema: str, code: str) -> dict[str, Any]:
    _require_receipt(value, code)
    _require(value.get("schema_version") == schema, code)
    if os.path.lexists(path):
        existing = _read_receipt(path, schema, code)
        _require(existing == value, code)
        return existing
    result = dict(value)
    _write_new_receipt(path, result, code)
    return result


def _fsync_directory(path: Path, code: str = "journal_drift") -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise DeletionExecutionError(code) from exc


def _rename_noreplace(
    source_parent: int,
    source_name: str,
    destination_parent: int,
    destination_name: str,
    *,
    fixture: bool,
) -> None:
    """Atomically rename without ever replacing another directory entry."""
    if sys.platform.startswith("linux"):
        libc = ctypes.CDLL(None, use_errno=True)
        renameat2 = getattr(libc, "renameat2", None)
        _require(renameat2 is not None, "source_state_drift")
        assert renameat2 is not None
        renameat2.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        renameat2.restype = ctypes.c_int
        result = renameat2(
            source_parent,
            os.fsencode(source_name),
            destination_parent,
            os.fsencode(destination_name),
            RENAME_NOREPLACE,
        )
        if result != 0:
            error = ctypes.get_errno()
            raise DeletionExecutionError("source_state_drift") from OSError(error, os.strerror(error))
        return
    _require(fixture, "source_state_drift")
    try:
        os.stat(destination_name, dir_fd=destination_parent, follow_symlinks=False)
    except FileNotFoundError:
        pass
    else:
        _fail("source_state_drift")
    try:
        os.rename(
            source_name,
            destination_name,
            src_dir_fd=source_parent,
            dst_dir_fd=destination_parent,
        )
    except OSError as exc:
        raise DeletionExecutionError("source_state_drift") from exc


def _same_fields(
    first: Mapping[str, Any],
    second: Mapping[str, Any],
    fields: Sequence[str],
    code: str,
) -> None:
    for field in fields:
        _require(first.get(field) == second.get(field), code)


def _deletion_root(bindings: storage.Bindings) -> Path:
    root = bindings.work_root / DELETE_ROOT
    try:
        root.relative_to(bindings.work_root)
    except ValueError:
        _fail("execution_state_drift")
    return root


def _source_capacity_path(bindings: storage.Bindings) -> Path:
    source = bindings.evidence_package or bindings.materialization_package
    _require(source is not None, "source_state_drift")
    assert source is not None
    return source


def make_operator_authorization(
    auth: Mapping[str, Any],
    authorization_id: str,
    *,
    fixture: bool = False,
) -> dict[str, Any]:
    """Create the private machine receipt for the operator's exact decision."""
    _require_receipt(auth, "authorization_drift")
    _require(auth.get("schema_version") == storage.AUTH_SCHEMA_VERSION, "authorization_drift")
    _require(auth.get("deletion_authorized") is False, "authorization_drift")
    _require(auth.get("authorization_gate") == "operator_explicit_authorization_required", "authorization_drift")
    _require(isinstance(authorization_id, str) and bool(authorization_id.strip()), "authorization_drift")
    request_sha256 = str(auth.get("receipt_sha256"))
    forecast = int(auth.get("reclaimed_byte_forecast", -1))
    candidates = int(auth.get("deletion_candidate_count", -1))
    _require(candidates > 0 and int(auth.get("retained_object_count", -1)) == 0, "authorization_drift")
    _require(int(auth.get("link_set_closed_candidate_count", -1)) == candidates, "authorization_drift")
    _require(forecast == int(auth.get("fully_closed_reclaimable_bytes", -2)), "authorization_drift")
    if not fixture:
        _require(request_sha256 == AUTHORIZED_REQUEST_SHA256, "authorization_drift")
        _require(forecast == AUTHORIZED_RECLAIMED_BYTES, "authorization_drift")
        _require(candidates == storage.EXPECTED_UNIQUE_INODE_COUNT, "authorization_drift")
    return _receipt(
        {
            "schema_version": OPERATOR_AUTH_SCHEMA,
            "outcome_sha256": storage.OUTCOME_SHA256,
            "operator_decision": "AUTHORIZE_EXACT_EXPANDED_SOURCE_DELETION",
            "authorization_id": authorization_id,
            "authorized_deletion_request_sha256": request_sha256,
            "authorized_reclaimed_byte_forecast": forecast,
            "authorized_candidate_count": candidates,
            "authorized_target_policy": "exact_candidates_only_no_directories",
            "compact_custody_must_be_retained": True,
            "fixture": fixture,
        }
    )


def _validate_authorization(auth: Mapping[str, Any], authorization: Mapping[str, Any], *, fixture: bool) -> None:
    _require_receipt(auth, "authorization_drift")
    _require_receipt(authorization, "authorization_drift")
    _require(authorization.get("schema_version") == OPERATOR_AUTH_SCHEMA, "authorization_drift")
    _require(
        authorization.get("operator_decision") == "AUTHORIZE_EXACT_EXPANDED_SOURCE_DELETION", "authorization_drift"
    )
    _require(
        authorization.get("authorized_deletion_request_sha256") == auth.get("receipt_sha256"), "authorization_drift"
    )
    _require(
        authorization.get("authorized_reclaimed_byte_forecast") == auth.get("reclaimed_byte_forecast"),
        "authorization_drift",
    )
    _require(
        authorization.get("authorized_candidate_count") == auth.get("deletion_candidate_count"),
        "authorization_drift",
    )
    _require(authorization.get("compact_custody_must_be_retained") is True, "authorization_drift")
    _require(bool(authorization.get("fixture")) == fixture, "authorization_drift")
    if not fixture:
        _require(auth.get("receipt_sha256") == AUTHORIZED_REQUEST_SHA256, "authorization_drift")
        _require(auth.get("reclaimed_byte_forecast") == AUTHORIZED_RECLAIMED_BYTES, "authorization_drift")


def issue_deletion_execution_challenge(
    bindings: storage.Bindings,
    primary: Mapping[str, Any],
    portable_export: Mapping[str, Any],
    finalize: Mapping[str, Any],
    auth: Mapping[str, Any],
    authorization: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist a single deletion nonce issued only after exact authorization."""
    for value in (primary, portable_export, finalize, auth, authorization):
        _require_receipt(value, "authorization_drift")
    _validate_authorization(auth, authorization, fixture=bindings.fixture)
    _require(finalize.get("schema_version") == storage.FINALIZE_SCHEMA_VERSION, "authorization_drift")
    _require(finalize.get("deletion_auth_request_sha256") == auth.get("receipt_sha256"), "authorization_drift")
    _require(primary.get("receipt_sha256") == portable_export.get("primary_stage_receipt_sha256"), "custody_drift")
    _require(finalize.get("primary_stage_receipt_sha256") == primary.get("receipt_sha256"), "custody_drift")
    _require(finalize.get("portable_export_receipt_sha256") == portable_export.get("receipt_sha256"), "custody_drift")
    root = _deletion_root(bindings)
    root.mkdir(parents=True, exist_ok=True, mode=storage.PRIVATE_DIR_MODE)
    os.chmod(root, storage.PRIVATE_DIR_MODE)
    path = root / "challenge.json"
    if os.path.lexists(path):
        existing = _read_receipt(path, EXECUTION_CHALLENGE_SCHEMA, "execution_state_drift")
        expected = {
            "outcome_sha256": storage.OUTCOME_SHA256,
            "deletion_auth_request_sha256": auth["receipt_sha256"],
            "operator_authorization_sha256": authorization["receipt_sha256"],
            "primary_stage_receipt_sha256": primary["receipt_sha256"],
            "portable_export_receipt_sha256": portable_export["receipt_sha256"],
            "finalize_receipt_sha256": finalize["receipt_sha256"],
            "phase": "pre_delete",
            "single_use": True,
            "no_deletion_performed": True,
        }
        for field, value in expected.items():
            _require(existing.get(field) == value, "execution_state_drift")
        _require(
            isinstance(existing.get("challenge_nonce"), str) and len(str(existing["challenge_nonce"])) == 64,
            "execution_state_drift",
        )
        return existing
    challenge = _receipt(
        {
            "schema_version": EXECUTION_CHALLENGE_SCHEMA,
            "outcome_sha256": storage.OUTCOME_SHA256,
            "deletion_auth_request_sha256": auth["receipt_sha256"],
            "operator_authorization_sha256": authorization["receipt_sha256"],
            "primary_stage_receipt_sha256": primary["receipt_sha256"],
            "portable_export_receipt_sha256": portable_export["receipt_sha256"],
            "finalize_receipt_sha256": finalize["receipt_sha256"],
            "challenge_nonce": secrets.token_hex(32),
            "phase": "pre_delete",
            "single_use": True,
            "no_deletion_performed": True,
        }
    )
    _write_new_receipt(path, challenge, "execution_state_drift")
    return challenge


def workstation_deletion_custody_response_stage(
    portable_export: Mapping[str, Any],
    initial_attestation: Mapping[str, Any],
    challenge: Mapping[str, Any],
    backup_pack_dir: Path,
    workstation_root: Path,
    *,
    source_failure_domain_token: str,
    workstation_failure_domain_token: str,
    zstd_executable: Path | None = None,
    fixture: bool = False,
) -> dict[str, Any]:
    """Answer a pre- or post-delete nonce with a fresh workstation stream proof."""
    for value in (portable_export, initial_attestation, challenge):
        _require_receipt(value, "custody_drift")
    schema = challenge.get("schema_version")
    _require(schema in {EXECUTION_CHALLENGE_SCHEMA, POST_CHALLENGE_SCHEMA}, "custody_drift")
    _require(challenge.get("portable_export_receipt_sha256") == portable_export.get("receipt_sha256"), "custody_drift")
    _require(
        initial_attestation.get("portable_export_receipt_sha256") == portable_export.get("receipt_sha256"),
        "custody_drift",
    )
    source_domain = storage._failure_domain_sha256(source_failure_domain_token)
    workstation_domain = storage._failure_domain_sha256(workstation_failure_domain_token)
    workstation_physical = storage._physical_failure_domain_sha256(workstation_root)
    _require(source_domain == portable_export.get("source_failure_domain_sha256"), "custody_drift")
    _require(source_domain != workstation_domain, "custody_drift")
    _require(portable_export.get("source_physical_domain_sha256") != workstation_physical, "custody_drift")
    proof = storage._portable_content_stream_proof(backup_pack_dir, portable_export, zstd_executable=zstd_executable)
    available = storage.available_bytes(workstation_root)
    if not fixture:
        _require(available >= storage.MIN_FREE_BYTES, "custody_drift")
    response = _receipt(
        {
            "schema_version": CUSTODY_RESPONSE_SCHEMA,
            "outcome_sha256": storage.OUTCOME_SHA256,
            "phase": challenge.get("phase"),
            "portable_export_receipt_sha256": portable_export["receipt_sha256"],
            "initial_attestation_receipt_sha256": initial_attestation["receipt_sha256"],
            "challenge_receipt_sha256": challenge["receipt_sha256"],
            "challenge_nonce": challenge["challenge_nonce"],
            "source_failure_domain_sha256": source_domain,
            "workstation_failure_domain_sha256": workstation_domain,
            "source_physical_domain_sha256": portable_export["source_physical_domain_sha256"],
            "workstation_physical_domain_sha256": workstation_physical,
            "fresh_restore_proof": proof,
            "workstation_avail_after_bytes": available,
            "fresh_workstation_custody_ok": True,
            "fixture": fixture,
        }
    )
    response_root = workstation_root / "cycle007-storage-deletion-responses"
    response_root.mkdir(parents=True, exist_ok=True, mode=storage.PRIVATE_DIR_MODE)
    os.chmod(response_root, storage.PRIVATE_DIR_MODE)
    path = response_root / f"{challenge['receipt_sha256']}.json"
    if os.path.lexists(path):
        existing = _read_receipt(path, CUSTODY_RESPONSE_SCHEMA, "execution_state_drift")
        _require(existing == response, "execution_state_drift")
        return existing
    _write_new_receipt(path, response, "execution_state_drift")
    return response


def _validate_custody_response(
    portable_export: Mapping[str, Any],
    expected_attestation: Mapping[str, Any],
    challenge: Mapping[str, Any],
    response: Mapping[str, Any],
    *,
    fixture: bool,
) -> None:
    for value in (portable_export, expected_attestation, challenge, response):
        _require_receipt(value, "custody_drift")
    _require(response.get("schema_version") == CUSTODY_RESPONSE_SCHEMA, "custody_drift")
    _require(response.get("challenge_receipt_sha256") == challenge.get("receipt_sha256"), "custody_drift")
    _require(response.get("challenge_nonce") == challenge.get("challenge_nonce"), "custody_drift")
    _require(response.get("phase") == challenge.get("phase"), "custody_drift")
    _require(response.get("portable_export_receipt_sha256") == portable_export.get("receipt_sha256"), "custody_drift")
    _require(
        response.get("initial_attestation_receipt_sha256") == expected_attestation.get("receipt_sha256"),
        "custody_drift",
    )
    for field in (
        "source_failure_domain_sha256",
        "workstation_failure_domain_sha256",
        "source_physical_domain_sha256",
        "workstation_physical_domain_sha256",
    ):
        _require(response.get(field) == expected_attestation.get(field), "custody_drift")
    _require(
        response.get("source_physical_domain_sha256") == portable_export.get("source_physical_domain_sha256"),
        "custody_drift",
    )
    _require(
        response.get("source_physical_domain_sha256") != response.get("workstation_physical_domain_sha256"),
        "custody_drift",
    )
    proof = response.get("fresh_restore_proof")
    _require(isinstance(proof, Mapping), "custody_drift")
    _require_receipt(proof, "custody_drift")
    _require(proof.get("backup_restore_ok") is True, "custody_drift")
    _require(proof.get("proof_mode") == "portable_stream_decompress_hash", "custody_drift")
    _require(proof.get("pack_manifest_sha256") == portable_export.get("pack_manifest_sha256"), "custody_drift")
    _require(
        proof.get("pack_manifest_sha256") == expected_attestation.get("pack_manifest_sha256"),
        "custody_drift",
    )
    _require(expected_attestation.get("backup_restore_ok") is True, "custody_drift")
    _require(expected_attestation.get("independent_failure_domain") is True, "custody_drift")
    _require(response.get("fresh_workstation_custody_ok") is True, "custody_drift")
    if not fixture:
        _require(
            int(response.get("workstation_avail_after_bytes", -1)) >= storage.MIN_FREE_BYTES,
            "custody_drift",
        )
    _require(bool(response.get("fixture")) == fixture, "custody_drift")


def _critical_inventory_match(frozen: Mapping[str, Any], fresh: Mapping[str, Any], auth: Mapping[str, Any]) -> None:
    fields = (
        "packet_count",
        "row_count",
        "object_count",
        "selected_path_count",
        "unique_inode_count",
        "duplicate_selected_link_count",
        "total_allocated_bytes",
        "fully_closed_reclaimable_bytes",
        "external_link_inode_count",
        "object_set_sha256",
        "ordered_row_identity_commitment_sha256",
        "deletion_state_sha256",
    )
    _same_fields(frozen, fresh, fields, "source_state_drift")
    _require(auth.get("inventory_receipt_sha256") == frozen.get("receipt_sha256"), "authorization_drift")
    _require(fresh.get("external_link_inode_count") == 0, "source_state_drift")
    _require(fresh.get("fully_closed_reclaimable_bytes") == fresh.get("total_allocated_bytes"), "source_state_drift")


def _validate_authorized_request_chain(
    bindings: storage.Bindings,
    frozen_inventory: Mapping[str, Any],
    pack_manifest: Mapping[str, Any],
    finalize: Mapping[str, Any],
    auth: Mapping[str, Any],
) -> None:
    """Revalidate every load-bearing receipt and exact target aggregate."""
    for value in (frozen_inventory, pack_manifest, finalize, auth):
        _require_receipt(value, "authorization_drift")
    _require(auth.get("schema_version") == storage.AUTH_SCHEMA_VERSION, "authorization_drift")
    _require(auth.get("outcome_sha256") == storage.OUTCOME_SHA256, "authorization_drift")
    _require(auth.get("deletion_authorized") is False, "authorization_drift")
    _require(auth.get("retention_neutral_lossless_compaction") is True, "authorization_drift")
    _require(auth.get("compact_custody_retained_pending_issue") == 7427, "authorization_drift")
    _require(auth.get("inventory_receipt_sha256") == frozen_inventory.get("receipt_sha256"), "authorization_drift")
    _require(auth.get("pack_manifest_sha256") == pack_manifest.get("receipt_sha256"), "authorization_drift")
    _require(finalize.get("deletion_auth_request_sha256") == auth.get("receipt_sha256"), "authorization_drift")
    _require(finalize.get("fresh_link_set_closed") is True, "authorization_drift")
    targets = auth.get("targets")
    _require(isinstance(targets, list) and bool(targets), "authorization_drift")
    candidates = [item for item in targets if isinstance(item, Mapping) and item.get("deletion_candidate") is True]
    _require(len(candidates) == len(targets) == int(auth.get("deletion_candidate_count", -1)), "authorization_drift")
    _require(int(auth.get("retained_object_count", -1)) == 0, "authorization_drift")
    _require(
        len({str(item.get("role_relative_path")) for item in candidates}) == len(candidates), "authorization_drift"
    )
    _require(
        all(
            item.get("link_set_closed") is True
            and int(item.get("external_link_count", -1)) == 0
            and item.get("authorized_class") == "lossless_expanded_reclaim_candidate"
            and int(item.get("reclaimable_allocated_bytes", -1)) == int(item.get("allocated_bytes", -2))
            for item in candidates
        ),
        "authorization_drift",
    )
    reclaim = sum(int(item["reclaimable_allocated_bytes"]) for item in candidates)
    _require(reclaim == int(auth.get("reclaimed_byte_forecast", -1)), "authorization_drift")
    _require(reclaim == int(auth.get("fully_closed_reclaimable_bytes", -2)), "authorization_drift")
    _require(reclaim == int(frozen_inventory.get("total_allocated_bytes", -3)), "authorization_drift")
    _same_fields(
        frozen_inventory,
        pack_manifest,
        (
            "packet_count",
            "row_count",
            "object_count",
            "object_set_sha256",
            "ordered_row_identity_commitment_sha256",
            "deletion_state_sha256",
        ),
        "custody_drift",
    )
    stage_root = _deletion_root(bindings).parent
    backup = _read_receipt(
        stage_root / "backup-receipt.imported.json",
        storage.BACKUP_SCHEMA_VERSION,
        "custody_drift",
    )
    restore = _read_receipt(
        stage_root / "backup-restore-proof.imported.json",
        "phase3_cycle007_storage_backup_restore_proof_v1",
        "custody_drift",
    )
    attestation = _read_receipt(
        stage_root / "backup-attestation.imported.json",
        storage.BACKUP_ATTESTATION_SCHEMA_VERSION,
        "custody_drift",
    )
    _require(auth.get("backup_receipt_sha256") == backup.get("receipt_sha256"), "custody_drift")
    _require(auth.get("backup_restore_proof_sha256") == restore.get("receipt_sha256"), "custody_drift")
    _require(finalize.get("backup_attestation_receipt_sha256") == attestation.get("receipt_sha256"), "custody_drift")
    _require(attestation.get("backup_receipt_sha256") == backup.get("receipt_sha256"), "custody_drift")
    _require(attestation.get("backup_restore_proof_sha256") == restore.get("receipt_sha256"), "custody_drift")
    _require(restore.get("backup_restore_ok") is True, "custody_drift")


def _load_imported_attestation(bindings: storage.Bindings) -> dict[str, Any]:
    return _read_receipt(
        _deletion_root(bindings).parent / "backup-attestation.imported.json",
        storage.BACKUP_ATTESTATION_SCHEMA_VERSION,
        "custody_drift",
    )


def _role_path(bindings: storage.Bindings, alias: str) -> Path:
    role, separator, relative = alias.partition("/")
    relative_path = Path(relative)
    _require(
        separator == "/"
        and relative
        and not relative_path.is_absolute()
        and all(part not in {"", ".", ".."} for part in relative_path.parts),
        "plan_drift",
    )
    root = (
        bindings.materialization_package
        if role == "materialization"
        else bindings.evidence_package
        if role == "evidence"
        else None
    )
    _require(root is not None, "plan_drift")
    assert root is not None
    try:
        resolved_root = root.resolve(strict=True)
        candidate = root / relative_path
        resolved_candidate = candidate.resolve(strict=False)
    except OSError as exc:
        raise DeletionExecutionError("plan_drift") from exc
    _require(resolved_candidate.is_relative_to(resolved_root), "plan_drift")
    return candidate


def _role_root(bindings: storage.Bindings, role: str) -> Path:
    root = (
        bindings.materialization_package
        if role == "materialization"
        else bindings.evidence_package
        if role == "evidence"
        else None
    )
    _require(root is not None, "plan_drift")
    assert root is not None
    return root


def _prepare_quarantine_directories(bindings: storage.Bindings, directory_name: str, roles: Sequence[str]) -> None:
    _require(directory_name.startswith(".cycle007-delete-quarantine-"), "plan_drift")
    for role in sorted(set(roles)):
        root = _role_root(bindings, role)
        quarantine = root / directory_name
        if os.path.lexists(quarantine):
            _require(quarantine.is_dir() and not quarantine.is_symlink(), "plan_drift")
            _require(stat.S_IMODE(quarantine.stat().st_mode) == storage.PRIVATE_DIR_MODE, "plan_drift")
            try:
                _require(not any(quarantine.iterdir()), "plan_drift")
            except OSError as exc:
                raise DeletionExecutionError("plan_drift") from exc
            continue
        try:
            quarantine.mkdir(mode=storage.PRIVATE_DIR_MODE)
            os.chmod(quarantine, storage.PRIVATE_DIR_MODE)
        except OSError as exc:
            raise DeletionExecutionError("plan_drift") from exc
        _fsync_directory(root, "plan_drift")


def _canonical_authorized_entries(
    bindings: storage.Bindings,
    frozen_inventory: Mapping[str, Any],
    auth: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], int, int]:
    """Derive the only deletable entries from immutable authorization inputs."""
    targets = auth.get("targets")
    objects = frozen_inventory.get("objects")
    _require(isinstance(targets, list) and isinstance(objects, list), "plan_drift")
    by_primary = {item.get("role_relative_path"): item for item in objects if isinstance(item, Mapping)}
    _require(len(by_primary) == len(objects), "plan_drift")
    entries: list[dict[str, Any]] = []
    planned_inodes: set[tuple[int, int]] = set()
    expected_allocation = 0
    for target in targets:
        _require(isinstance(target, Mapping), "plan_drift")
        primary_alias = target.get("role_relative_path")
        source = by_primary.get(primary_alias)
        _require(isinstance(source, Mapping), "plan_drift")
        aliases = tuple(storage._item_relative_paths(source))
        allocation = int(source.get("inode_allocation_bytes", source.get("allocated_bytes", -1)))
        expected_target = {
            "role_relative_path": source.get("role_relative_path"),
            "role_relative_paths": list(aliases),
            "selection_class": source.get("selection_class"),
            "selection_classes": sorted(
                {str(value) for value in source.get("selection_classes", [source.get("selection_class")])}
            ),
            "sha256": source.get("sha256"),
            "allocated_bytes": allocation,
            "reclaimable_allocated_bytes": allocation,
            "selected_path_count": source.get("selected_path_count", 1),
            "selected_link_count": source.get("selected_link_count", 1),
            "link_count": source.get("link_count", 1),
            "external_link_count": source.get("external_link_count", 0),
            "link_set_closed": True,
            "deletion_candidate": True,
            "authorized_class": "lossless_expanded_reclaim_candidate",
        }
        _require(dict(target) == expected_target, "plan_drift")
        fs = source.get("fs")
        _require(isinstance(fs, Mapping), "plan_drift")
        inode = (int(fs.get("dev", -1)), int(fs.get("ino", -1)))
        _require(inode not in planned_inodes and min(inode) >= 0, "plan_drift")
        planned_inodes.add(inode)
        expected_allocation += allocation

        grouped: dict[str, list[str]] = {}
        for alias in aliases:
            path = _role_path(bindings, alias)
            try:
                canonical_path = str(path.resolve(strict=False))
            except OSError as exc:
                raise DeletionExecutionError("plan_drift") from exc
            grouped.setdefault(canonical_path, []).append(alias)
        _require(len(grouped) == int(source.get("selected_link_count", -1)), "plan_drift")
        groups = sorted((sorted(values) for values in grouped.values()), key=lambda values: values[0])
        initial_links = int(source.get("link_count", -1))
        _require(initial_links == len(groups), "plan_drift")
        for index, group_aliases in enumerate(groups):
            quarantine_role = str(group_aliases[0]).split("/", 1)[0]
            entry_body = {
                "role_relative_path": group_aliases[0],
                "role_relative_paths": group_aliases,
                "source_path_id_sha256": storage.digest(
                    group_aliases[0].encode("utf-8") + b"\0" + str(inode).encode("ascii")
                ),
                "dev": inode[0],
                "ino": inode[1],
                "mode": int(source["mode"]),
                "size_bytes": int(source["size_bytes"]),
                "allocated_bytes": int(source["allocated_bytes"]),
                "sha256": source["sha256"],
                "expected_nlink_before": initial_links - index,
                "reclaims_inode_allocation": index == len(groups) - 1,
                "quarantine_role": quarantine_role,
            }
            entry_body["entry_id"] = storage.digest(storage.canonical(entry_body))
            entry_body["quarantine_name"] = f"{entry_body['entry_id']}.pending"
            entries.append(entry_body)
    entries.sort(key=lambda item: (str(item["role_relative_path"]), str(item["entry_id"])))
    _require(len(planned_inodes) == int(auth.get("deletion_candidate_count", -1)), "plan_drift")
    _require(expected_allocation == int(auth.get("reclaimed_byte_forecast", -1)), "plan_drift")
    return entries, len(planned_inodes), expected_allocation


def _build_plan(
    bindings: storage.Bindings,
    frozen_inventory: Mapping[str, Any],
    fresh_inventory: Mapping[str, Any],
    auth: Mapping[str, Any],
    authorization: Mapping[str, Any],
    challenge: Mapping[str, Any],
    pre_response: Mapping[str, Any],
    primary_proof: Mapping[str, Any],
) -> dict[str, Any]:
    entries, inode_count, expected_allocation = _canonical_authorized_entries(
        bindings,
        frozen_inventory,
        auth,
    )
    quarantine_directory_name = ".cycle007-delete-quarantine-" + str(authorization["receipt_sha256"])[:16]
    for entry in entries:
        for alias in entry["role_relative_paths"]:
            path = _role_path(bindings, alias)
            try:
                info = path.lstat()
            except OSError as exc:
                raise DeletionExecutionError("source_state_drift") from exc
            _require(stat.S_ISREG(info.st_mode) and not path.is_symlink(), "source_state_drift")
            _require(
                (int(info.st_dev), int(info.st_ino)) == (int(entry["dev"]), int(entry["ino"])),
                "source_state_drift",
            )
    _prepare_quarantine_directories(
        bindings,
        quarantine_directory_name,
        [str(item["quarantine_role"]) for item in entries],
    )
    root_ids = {
        "materialization": storage._opaque_fs_id(bindings.materialization_package),
        "evidence": storage._opaque_fs_id(bindings.evidence_package),
    }
    plan_digest = storage.digest(storage.canonical(entries))
    return _receipt(
        {
            "schema_version": PLAN_SCHEMA,
            "outcome_sha256": storage.OUTCOME_SHA256,
            "deletion_auth_request_sha256": auth["receipt_sha256"],
            "operator_authorization_sha256": authorization["receipt_sha256"],
            "execution_challenge_sha256": challenge["receipt_sha256"],
            "pre_delete_workstation_response_sha256": pre_response["receipt_sha256"],
            "fresh_inventory_receipt_sha256": fresh_inventory["receipt_sha256"],
            "frozen_inventory_receipt_sha256": frozen_inventory["receipt_sha256"],
            "fresh_primary_roundtrip_sha256": primary_proof["receipt_sha256"],
            "root_identities": root_ids,
            "entry_count": len(entries),
            "inode_count": inode_count,
            "expected_reclaimed_allocated_bytes": expected_allocation,
            "entries_sha256": plan_digest,
            "quarantine_directory_name": quarantine_directory_name,
            "entries": entries,
            "files_only": True,
            "directories_authorized": 0,
        }
    )


def _validate_persisted_plan(
    bindings: storage.Bindings,
    plan: Mapping[str, Any],
    frozen_inventory: Mapping[str, Any],
    auth: Mapping[str, Any],
    authorization: Mapping[str, Any],
    challenge: Mapping[str, Any],
    pre_response: Mapping[str, Any],
    primary_roundtrip: Mapping[str, Any],
) -> None:
    _require_receipt(plan, "plan_drift")
    expected_entries, expected_inode_count, expected_allocation = _canonical_authorized_entries(
        bindings,
        frozen_inventory,
        auth,
    )
    expected_quarantine_directory = ".cycle007-delete-quarantine-" + str(authorization["receipt_sha256"])[:16]
    expected = {
        "schema_version": PLAN_SCHEMA,
        "outcome_sha256": storage.OUTCOME_SHA256,
        "deletion_auth_request_sha256": auth["receipt_sha256"],
        "operator_authorization_sha256": authorization["receipt_sha256"],
        "execution_challenge_sha256": challenge["receipt_sha256"],
        "pre_delete_workstation_response_sha256": pre_response["receipt_sha256"],
        "frozen_inventory_receipt_sha256": frozen_inventory["receipt_sha256"],
        "fresh_primary_roundtrip_sha256": primary_roundtrip["receipt_sha256"],
        "entry_count": len(expected_entries),
        "inode_count": expected_inode_count,
        "expected_reclaimed_allocated_bytes": expected_allocation,
        "entries_sha256": storage.digest(storage.canonical(expected_entries)),
        "quarantine_directory_name": expected_quarantine_directory,
        "entries": expected_entries,
        "root_identities": {
            "materialization": storage._opaque_fs_id(bindings.materialization_package),
            "evidence": storage._opaque_fs_id(bindings.evidence_package),
        },
        "files_only": True,
        "directories_authorized": 0,
    }
    for field, value in expected.items():
        _require(plan.get(field) == value, "plan_drift")
    _require(
        isinstance(plan.get("fresh_inventory_receipt_sha256"), str)
        and len(str(plan["fresh_inventory_receipt_sha256"])) == 64,
        "plan_drift",
    )
    _require(expected_allocation == int(authorization["authorized_reclaimed_byte_forecast"]), "plan_drift")
    _require(expected_inode_count == int(authorization["authorized_candidate_count"]), "plan_drift")


def _event_dir(root: Path) -> Path:
    return root / "events"


def _load_events(root: Path, plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    directory = _event_dir(root)
    if not directory.exists():
        return []
    _require(directory.is_dir() and not directory.is_symlink(), "journal_drift")
    events: list[dict[str, Any]] = []
    names = sorted(path.name for path in directory.iterdir())
    _require(all(name.endswith(".json") and name[:-5].isdigit() for name in names), "journal_drift")
    previous: str | None = None
    for sequence, name in enumerate(names):
        _require(name == f"{sequence:06d}.json", "journal_drift")
        event = _read_receipt(directory / name, EVENT_SCHEMA, "journal_drift")
        _require(event.get("sequence") == sequence, "journal_drift")
        _require(event.get("plan_receipt_sha256") == plan.get("receipt_sha256"), "journal_drift")
        _require(event.get("previous_event_sha256") == previous, "journal_drift")
        previous = event["receipt_sha256"]
        events.append(event)
    return events


def _append_event(
    root: Path,
    plan: Mapping[str, Any],
    events: list[dict[str, Any]],
    event_type: str,
    *,
    entry_id: str | None = None,
    detail: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    directory = _event_dir(root)
    created = not os.path.lexists(directory)
    directory.mkdir(mode=storage.PRIVATE_DIR_MODE, exist_ok=True)
    os.chmod(directory, storage.PRIVATE_DIR_MODE)
    if created:
        # The first event is not durable unless the journal root's directory
        # entry for ``events`` is durable too.
        _fsync_directory(root)
    event = _receipt(
        {
            "schema_version": EVENT_SCHEMA,
            "outcome_sha256": storage.OUTCOME_SHA256,
            "plan_receipt_sha256": plan["receipt_sha256"],
            "sequence": len(events),
            "previous_event_sha256": events[-1]["receipt_sha256"] if events else None,
            "event_type": event_type,
            "entry_id": entry_id,
            "detail": dict(detail or {}),
        }
    )
    _write_new_receipt(directory / f"{len(events):06d}.json", event, "journal_drift")
    events.append(event)
    return event


def _journal_state(
    plan: Mapping[str, Any], events: Sequence[Mapping[str, Any]]
) -> tuple[set[str], str | None, str | None]:
    valid = {str(item["entry_id"]) for item in plan["entries"]}
    completed: set[str] = set()
    inflight: str | None = None
    inflight_phase: str | None = None
    for event in events:
        event_type = event.get("event_type")
        entry_id = event.get("entry_id")
        if event_type == "START":
            _require(
                entry_id is None and not completed and inflight is None and inflight_phase is None,
                "journal_drift",
            )
        elif event_type == "INTENT":
            _require(isinstance(entry_id, str) and entry_id in valid, "journal_drift")
            _require(inflight is None and entry_id not in completed, "journal_drift")
            inflight = entry_id
            inflight_phase = "INTENT"
        elif event_type in {"MOVED", "RECOVERED_MOVED"}:
            _require(entry_id == inflight and inflight_phase == "INTENT", "journal_drift")
            inflight_phase = "MOVED"
        elif event_type in {"UNLINKED", "RECOVERED_UNLINKED"}:
            _require(
                entry_id == inflight and isinstance(entry_id, str) and inflight_phase == "MOVED",
                "journal_drift",
            )
            completed.add(entry_id)
            inflight = None
            inflight_phase = None
        else:
            _fail("journal_drift")
    return completed, inflight, inflight_phase


def _open_parent(bindings: storage.Bindings, alias: str) -> tuple[int, str]:
    role, separator, relative = alias.partition("/")
    relative_path = Path(relative)
    _require(separator == "/" and relative and not relative_path.is_absolute(), "source_state_drift")
    parts = relative_path.parts
    _require(parts and all(part not in {"", ".", ".."} for part in parts), "source_state_drift")
    root = (
        bindings.materialization_package
        if role == "materialization"
        else bindings.evidence_package
        if role == "evidence"
        else None
    )
    _require(root is not None, "source_state_drift")
    assert root is not None
    try:
        resolved_root = root.resolve(strict=True)
        resolved_candidate = (root / relative_path).resolve(strict=False)
    except OSError as exc:
        raise DeletionExecutionError("source_state_drift") from exc
    _require(resolved_candidate.is_relative_to(resolved_root), "source_state_drift")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(root, flags)
        for part in parts[:-1]:
            child = os.open(part, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor, parts[-1]
    except OSError as exc:
        with contextlib.suppress(UnboundLocalError, OSError):
            os.close(descriptor)
        raise DeletionExecutionError("source_state_drift") from exc


def _fd_sha256(descriptor: int) -> str:
    hasher = hashlib.sha256()
    os.lseek(descriptor, 0, os.SEEK_SET)
    while True:
        chunk = os.read(descriptor, 1024 * 1024)
        if not chunk:
            break
        hasher.update(chunk)
    return hasher.hexdigest()


def _allocated_from_stat(info: os.stat_result) -> int:
    blocks = int(getattr(info, "st_blocks", 0))
    return blocks * 512 if blocks else int(info.st_size)


def _entry_present_exact(bindings: storage.Bindings, entry: Mapping[str, Any]) -> bool:
    parent, leaf = _open_parent(bindings, str(entry["role_relative_path"]))
    try:
        try:
            info = os.stat(leaf, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            return False
        _require(stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode), "source_state_drift")
        _require((int(info.st_dev), int(info.st_ino)) == (entry["dev"], entry["ino"]), "source_state_drift")
        return True
    finally:
        os.close(parent)


def _require_entry_aliases_absent(bindings: storage.Bindings, entry: Mapping[str, Any]) -> None:
    aliases = entry.get("role_relative_paths")
    _require(isinstance(aliases, list) and bool(aliases), "plan_drift")
    for alias in aliases:
        parent, leaf = _open_parent(bindings, str(alias))
        try:
            try:
                os.stat(leaf, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError:
                continue
            _fail("source_state_drift")
        finally:
            os.close(parent)


def _open_quarantine(bindings: storage.Bindings, plan: Mapping[str, Any], entry: Mapping[str, Any]) -> tuple[int, str]:
    role = str(entry.get("quarantine_role"))
    directory_name = str(plan.get("quarantine_directory_name"))
    _require(directory_name.startswith(".cycle007-delete-quarantine-"), "plan_drift")
    root = _role_root(bindings, role)
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    root_descriptor = -1
    try:
        root_descriptor = os.open(root, flags)
        descriptor = os.open(directory_name, flags, dir_fd=root_descriptor)
    except OSError as exc:
        raise DeletionExecutionError("source_state_drift") from exc
    finally:
        if root_descriptor >= 0:
            os.close(root_descriptor)
    return descriptor, str(entry["quarantine_name"])


def _quarantine_present_exact(bindings: storage.Bindings, plan: Mapping[str, Any], entry: Mapping[str, Any]) -> bool:
    quarantine, name = _open_quarantine(bindings, plan, entry)
    try:
        try:
            info = os.stat(name, dir_fd=quarantine, follow_symlinks=False)
        except FileNotFoundError:
            return False
        _require(stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode), "source_state_drift")
        _require(
            (int(info.st_dev), int(info.st_ino)) == (entry["dev"], entry["ino"]),
            "source_state_drift",
        )
        return True
    finally:
        os.close(quarantine)


def _fsync_move_directories(bindings: storage.Bindings, plan: Mapping[str, Any], entry: Mapping[str, Any]) -> None:
    parent, _leaf = _open_parent(bindings, str(entry["role_relative_path"]))
    quarantine, _name = _open_quarantine(bindings, plan, entry)
    try:
        os.fsync(parent)
        os.fsync(quarantine)
    except OSError as exc:
        raise DeletionExecutionError("source_state_drift") from exc
    finally:
        os.close(parent)
        os.close(quarantine)


def _fault(
    fault_hook: Callable[[Mapping[str, Any]], None] | None,
    event: str,
    entry_id: str,
) -> None:
    if fault_hook is not None:
        fault_hook({"event": event, "entry_id": entry_id})


def _validate_open_file(descriptor: int, entry: Mapping[str, Any]) -> os.stat_result:
    info = os.fstat(descriptor)
    expected_identity = (int(entry["dev"]), int(entry["ino"]))
    _require(stat.S_ISREG(info.st_mode), "source_state_drift")
    _require((int(info.st_dev), int(info.st_ino)) == expected_identity, "source_state_drift")
    _require(stat.S_IMODE(info.st_mode) == int(entry["mode"]), "source_state_drift")
    _require(int(info.st_size) == int(entry["size_bytes"]), "source_state_drift")
    _require(_allocated_from_stat(info) == int(entry["allocated_bytes"]), "source_state_drift")
    _require(int(info.st_nlink) == int(entry["expected_nlink_before"]), "source_state_drift")
    _require(_fd_sha256(descriptor) == entry["sha256"], "source_state_drift")
    return info


def _move_exact_to_quarantine(
    bindings: storage.Bindings,
    plan: Mapping[str, Any],
    entry: Mapping[str, Any],
    fault_hook: Callable[[Mapping[str, Any]], None] | None,
) -> None:
    parent, leaf = _open_parent(bindings, str(entry["role_relative_path"]))
    quarantine, quarantine_name = _open_quarantine(bindings, plan, entry)
    file_descriptor = -1
    try:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        file_descriptor = os.open(leaf, flags, dir_fd=parent)
        _validate_open_file(file_descriptor, entry)
        expected_identity = (int(entry["dev"]), int(entry["ino"]))
        current = os.stat(leaf, dir_fd=parent, follow_symlinks=False)
        _require((int(current.st_dev), int(current.st_ino)) == expected_identity, "source_state_drift")
        _require(stat.S_ISREG(current.st_mode) and not stat.S_ISLNK(current.st_mode), "source_state_drift")
        _rename_noreplace(
            parent,
            leaf,
            quarantine,
            quarantine_name,
            fixture=bindings.fixture,
        )
        _fault(fault_hook, "after_move", str(entry["entry_id"]))
        moved = os.stat(quarantine_name, dir_fd=quarantine, follow_symlinks=False)
        if (int(moved.st_dev), int(moved.st_ino)) != expected_identity:
            # Never unlink a swapped-in entry. Restore it without overwriting a
            # new source entry, then fail closed.
            _rename_noreplace(
                quarantine,
                quarantine_name,
                parent,
                leaf,
                fixture=bindings.fixture,
            )
            os.fsync(parent)
            os.fsync(quarantine)
            _fail("source_state_drift")
        os.fsync(parent)
        os.fsync(quarantine)
        _fault(fault_hook, "after_move_fsync", str(entry["entry_id"]))
        try:
            os.stat(leaf, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            _fail("source_state_drift")
        _require_entry_aliases_absent(bindings, entry)
    except OSError as exc:
        raise DeletionExecutionError("source_state_drift") from exc
    finally:
        if file_descriptor >= 0:
            os.close(file_descriptor)
        os.close(parent)
        os.close(quarantine)


def _unlink_quarantined_exact(
    bindings: storage.Bindings,
    plan: Mapping[str, Any],
    entry: Mapping[str, Any],
    fault_hook: Callable[[Mapping[str, Any]], None] | None,
) -> None:
    quarantine, name = _open_quarantine(bindings, plan, entry)
    descriptor = -1
    try:
        descriptor = os.open(name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=quarantine)
        _validate_open_file(descriptor, entry)
        current = os.stat(name, dir_fd=quarantine, follow_symlinks=False)
        _require(
            (int(current.st_dev), int(current.st_ino)) == (entry["dev"], entry["ino"]),
            "source_state_drift",
        )
        os.unlink(name, dir_fd=quarantine)
        _fault(fault_hook, "after_unlink", str(entry["entry_id"]))
        os.fsync(quarantine)
        _fault(fault_hook, "after_parent_fsync", str(entry["entry_id"]))
        try:
            os.stat(name, dir_fd=quarantine, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            _fail("source_state_drift")
    except OSError as exc:
        raise DeletionExecutionError("source_state_drift") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(quarantine)


def _validate_root_identities(bindings: storage.Bindings, plan: Mapping[str, Any]) -> None:
    roots = plan.get("root_identities")
    _require(isinstance(roots, Mapping), "plan_drift")
    _require(roots.get("materialization") == storage._opaque_fs_id(bindings.materialization_package), "plan_drift")
    _require(roots.get("evidence") == storage._opaque_fs_id(bindings.evidence_package), "plan_drift")


@contextlib.contextmanager
def _execution_locks(root: Path, quiescence_lock_paths: Sequence[Path]) -> Iterator[None]:
    lock_path = root / "executor.lock"
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    descriptors: list[int] = []
    try:
        descriptor = os.open(lock_path, flags, storage.PRIVATE_FILE_MODE)
        os.fchmod(descriptor, storage.PRIVATE_FILE_MODE)
        descriptors.append(descriptor)
        lock_identities: set[tuple[int, int]] = set()
        for path in quiescence_lock_paths:
            _require(path.is_absolute(), "quiescence_unproved")
            info = path.lstat()
            _require(stat.S_ISREG(info.st_mode) and not path.is_symlink(), "quiescence_unproved")
            _require(stat.S_IMODE(info.st_mode) == storage.PRIVATE_FILE_MODE, "quiescence_unproved")
            identity = (int(info.st_dev), int(info.st_ino))
            _require(identity not in lock_identities, "quiescence_unproved")
            lock_identities.add(identity)
            descriptors.append(os.open(path, os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)))
        for item in descriptors:
            try:
                fcntl.flock(item, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise DeletionExecutionError("quiescence_unproved") from exc
        yield
    finally:
        for descriptor in reversed(descriptors):
            with contextlib.suppress(OSError):
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            with contextlib.suppress(OSError):
                os.close(descriptor)


def _require_no_open_target_descriptors(
    plan: Mapping[str, Any],
    *,
    fixture: bool,
    proc: Path = Path("/proc"),
) -> None:
    if fixture:
        return
    _require(proc.is_dir(), "quiescence_unproved")
    targets = {(int(item["dev"]), int(item["ino"])) for item in plan["entries"]}
    own_pid = os.getpid()
    own_uid = os.geteuid()
    try:
        processes = list(proc.iterdir())
    except OSError as exc:
        raise DeletionExecutionError("quiescence_unproved") from exc
    for process in processes:
        if not process.name.isdigit() or int(process.name) == own_pid:
            continue
        try:
            process_uid = process.stat().st_uid
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError as exc:
            raise DeletionExecutionError("quiescence_unproved") from exc
        if process_uid != own_uid:
            continue
        systemd_generation: bytes | None = None
        try:
            if (process / "comm").read_bytes() == b"systemd\n":
                systemd_generation = _attest_systemd_user_manager(
                    process,
                    own_uid=own_uid,
                )
        except (OSError, ValueError, DeletionExecutionError):
            # Attestation is required only if an individual descriptor cannot
            # be inspected.  Fully inspectable processes still proceed through
            # the ordinary target-inode scan below.
            systemd_generation = None
        try:
            descriptors = list((process / "fd").iterdir())
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError as exc:
            # Linux intentionally hides descriptor tables for a small set of
            # same-UID session infrastructure processes.  They are not
            # Cycle007 producers; those remain excluded by the three held
            # guardian/controller/execution locks.  Unknown hidden processes
            # still fail closed.
            try:
                process_class = (process / "comm").read_bytes()
            except OSError:
                raise DeletionExecutionError("quiescence_unproved") from exc
            _require(
                any(
                    process_class == allowed_process_class.encode("ascii") + b"\n"
                    for allowed_process_class in UNINSPECTABLE_QUIESCENCE_PROCESS_ALLOWLIST
                ),
                "quiescence_unproved",
            )
            continue
        used_systemd_descriptor_exception = False
        for descriptor in descriptors:
            try:
                info = descriptor.stat()
            except (FileNotFoundError, ProcessLookupError):
                continue
            except PermissionError as exc:
                if systemd_generation is None:
                    raise DeletionExecutionError("quiescence_unproved") from exc
                # This is trusted-infrastructure classification for the
                # controlled source host, not authentication against hostile
                # same-UID execution.  The exact cgroup/UID/PPID/cmdline and
                # PID-generation binding below keep the exception confined to
                # the kernel-managed user systemd manager observed there.
                used_systemd_descriptor_exception = True
                continue
            if (int(info.st_dev), int(info.st_ino)) in targets:
                _fail("quiescence_unproved")
        if used_systemd_descriptor_exception:
            _require(
                _systemd_process_generation(process) == systemd_generation,
                "quiescence_unproved",
            )


def _canonical_decimal(value: bytes) -> bool:
    return bool(value) and value.isdigit() and str(int(value)).encode("ascii") == value


def _systemd_process_generation(process: Path) -> bytes:
    try:
        raw = (process / "stat").read_bytes()
    except OSError as exc:
        raise DeletionExecutionError("quiescence_unproved") from exc
    marker = raw.rfind(b") ")
    _require(
        marker > 0 and raw.endswith(b"\n") and b"\r" not in raw,
        "quiescence_unproved",
    )
    prefix = raw[:marker]
    suffix = raw[marker + 2 : -1].split(b" ")
    _require(prefix == process.name.encode("ascii") + b" (systemd", "quiescence_unproved")
    _require(
        len(suffix) >= 20 and len(suffix[0]) == 1 and suffix[0] in b"RSDZTWXIP" and b"" not in suffix,
        "quiescence_unproved",
    )
    _require(suffix[1] == b"1", "quiescence_unproved")
    start_time = suffix[19]
    _require(_canonical_decimal(start_time), "quiescence_unproved")
    return start_time


def _attest_systemd_user_manager(process: Path, *, own_uid: int) -> bytes:
    generation = _systemd_process_generation(process)
    uid = str(own_uid).encode("ascii")
    expected_uid_line = b"Uid:\t" + b"\t".join((uid, uid, uid, uid))
    expected_cgroup = b"0::/user.slice/user-" + uid + b".slice/user@" + uid + b".service/init.scope\n"
    try:
        comm = (process / "comm").read_bytes()
        cgroup = (process / "cgroup").read_bytes()
        cmdline = (process / "cmdline").read_bytes()
        status_lines = (process / "status").read_bytes().split(b"\n")
    except OSError as exc:
        raise DeletionExecutionError("quiescence_unproved") from exc
    _require(comm == b"systemd\n", "quiescence_unproved")
    _require(cgroup == expected_cgroup, "quiescence_unproved")
    _require(cmdline.endswith(b"\0"), "quiescence_unproved")
    arguments = cmdline.split(b"\0")
    _require(len(arguments) == 4 and arguments[-1] == b"", "quiescence_unproved")
    executable, user_flag, deserialize = arguments[:3]
    _require(executable in SYSTEMD_USER_MANAGER_ARGV0_ALLOWLIST, "quiescence_unproved")
    _require(user_flag == b"--user", "quiescence_unproved")
    deserialize_prefix = b"--deserialize="
    _require(deserialize.startswith(deserialize_prefix), "quiescence_unproved")
    _require(
        _canonical_decimal(deserialize[len(deserialize_prefix) :]),
        "quiescence_unproved",
    )
    uid_lines = [line for line in status_lines if line.startswith(b"Uid:")]
    _require(uid_lines == [expected_uid_line], "quiescence_unproved")
    return generation


def _verify_pending_presence(
    bindings: storage.Bindings,
    plan: Mapping[str, Any],
    completed: set[str],
    inflight: str | None,
) -> None:
    expected_quarantine_by_role: dict[str, set[str]] = {}
    for entry in plan["entries"]:
        entry_id = str(entry["entry_id"])
        present = _entry_present_exact(bindings, entry)
        quarantined = _quarantine_present_exact(bindings, plan, entry)
        if quarantined:
            expected_quarantine_by_role.setdefault(str(entry["quarantine_role"]), set()).add(
                str(entry["quarantine_name"])
            )
        if entry_id in completed:
            _require(not present, "journal_drift")
            _require(not quarantined, "journal_drift")
            _require_entry_aliases_absent(bindings, entry)
        elif entry_id != inflight:
            _require(present, "source_state_drift")
            _require(not quarantined, "source_state_drift")
    directory_name = str(plan["quarantine_directory_name"])
    roles = {str(entry["quarantine_role"]) for entry in plan["entries"]}
    for role in roles:
        quarantine = _role_root(bindings, role) / directory_name
        try:
            actual = {path.name for path in quarantine.iterdir() if path.is_file() and not path.is_symlink()}
            all_names = {path.name for path in quarantine.iterdir()}
        except OSError as exc:
            raise DeletionExecutionError("journal_drift") from exc
        _require(actual == all_names, "journal_drift")
        _require(actual == expected_quarantine_by_role.get(role, set()), "journal_drift")


def _validate_unlinked_receipt(
    unlinked: Mapping[str, Any],
    plan: Mapping[str, Any],
    authorization: Mapping[str, Any],
    events: Sequence[Mapping[str, Any]],
    post_primary: Mapping[str, Any],
) -> None:
    _require_receipt(unlinked, "execution_state_drift")
    expected = {
        "schema_version": UNLINKED_SCHEMA,
        "outcome_sha256": storage.OUTCOME_SHA256,
        "plan_receipt_sha256": plan["receipt_sha256"],
        "operator_authorization_sha256": authorization["receipt_sha256"],
        "journal_terminal_event_sha256": events[-1]["receipt_sha256"],
        "unlinked_entry_count": plan["entry_count"],
        "unlinked_path_count": plan["entry_count"],
        "unlinked_inode_count": plan["inode_count"],
        "unlinked_object_count": plan["inode_count"],
        "expected_reclaimed_allocated_bytes": plan["expected_reclaimed_allocated_bytes"],
        "reclaimed_byte_forecast": plan["expected_reclaimed_allocated_bytes"],
        "forecast_and_observed_are_distinct": True,
        "fresh_post_unlink_primary_roundtrip_sha256": post_primary["receipt_sha256"],
        "all_authorized_entries_absent": True,
        "directories_removed": 0,
        "compact_primary_retained": True,
        "awaiting_post_delete_workstation_proof": True,
    }
    for field, value in expected.items():
        _require(unlinked.get(field) == value, "execution_state_drift")
    before = int(unlinked.get("filesystem_avail_before_bytes", -1))
    after = int(unlinked.get("filesystem_avail_after_unlink_bytes", -1))
    _require(unlinked.get("source_avail_before_bytes") == before, "execution_state_drift")
    _require(unlinked.get("source_avail_after_bytes") == after, "execution_state_drift")
    _require(
        unlinked.get("observed_filesystem_avail_delta_bytes") == after - before,
        "execution_state_drift",
    )


def _validate_post_challenge(
    post_challenge: Mapping[str, Any],
    unlinked: Mapping[str, Any],
    authorization: Mapping[str, Any],
    portable_export: Mapping[str, Any],
) -> None:
    _require_receipt(post_challenge, "execution_state_drift")
    expected = {
        "schema_version": POST_CHALLENGE_SCHEMA,
        "outcome_sha256": storage.OUTCOME_SHA256,
        "phase": "post_delete",
        "unlinked_receipt_sha256": unlinked["receipt_sha256"],
        "operator_authorization_sha256": authorization["receipt_sha256"],
        "portable_export_receipt_sha256": portable_export["receipt_sha256"],
        "single_use": True,
    }
    for field, value in expected.items():
        _require(post_challenge.get(field) == value, "execution_state_drift")
    _require(
        isinstance(post_challenge.get("challenge_nonce"), str) and len(str(post_challenge["challenge_nonce"])) == 64,
        "execution_state_drift",
    )


def _validate_completion_receipt(
    completion: Mapping[str, Any],
    plan: Mapping[str, Any],
    authorization: Mapping[str, Any],
    unlinked: Mapping[str, Any],
    post_response: Mapping[str, Any],
    primary_roundtrip: Mapping[str, Any],
    events: Sequence[Mapping[str, Any]],
) -> None:
    _require_receipt(completion, "execution_state_drift")
    expected = {
        "schema_version": COMPLETION_SCHEMA,
        "outcome_sha256": storage.OUTCOME_SHA256,
        "deletion_complete": True,
        "operator_authorization_sha256": authorization["receipt_sha256"],
        "plan_receipt_sha256": plan["receipt_sha256"],
        "unlinked_receipt_sha256": unlinked["receipt_sha256"],
        "post_delete_workstation_response_sha256": post_response["receipt_sha256"],
        "fresh_final_primary_roundtrip_sha256": primary_roundtrip["receipt_sha256"],
        "compact_copy_count_freshly_verified": 2,
        "authorized_entry_count": plan["entry_count"],
        "authorized_inode_count": plan["inode_count"],
        "expected_reclaimed_allocated_bytes": plan["expected_reclaimed_allocated_bytes"],
        "reclaimed_byte_forecast": plan["expected_reclaimed_allocated_bytes"],
        "filesystem_avail_before_bytes": unlinked["filesystem_avail_before_bytes"],
        "forecast_and_observed_are_distinct": True,
        "forecast_is_not_actual": True,
        "all_authorized_entries_absent": True,
        "directories_removed": 0,
        "compact_primary_retained": True,
        "compact_workstation_backup_retained": True,
        "journal_event_count": len(events),
        "journal_terminal_event_sha256": events[-1]["receipt_sha256"],
    }
    for field, value in expected.items():
        _require(completion.get(field) == value, "execution_state_drift")
    before = int(completion["filesystem_avail_before_bytes"])
    after = int(completion.get("filesystem_avail_at_completion_bytes", -1))
    _require(completion.get("observed_filesystem_avail_delta_bytes") == after - before, "execution_state_drift")
    _require(completion.get("actual_reclaimed_bytes") == after - before, "execution_state_drift")


def execute_authorized_source_deletion(
    bindings: storage.Bindings,
    primary: Mapping[str, Any],
    portable_export: Mapping[str, Any],
    frozen_inventory: Mapping[str, Any],
    pack_manifest: Mapping[str, Any],
    finalize: Mapping[str, Any],
    auth: Mapping[str, Any],
    authorization: Mapping[str, Any],
    challenge: Mapping[str, Any],
    pre_response: Mapping[str, Any],
    primary_pack_dir: Path,
    *,
    quiescence_lock_paths: Sequence[Path],
    fault_hook: Callable[[Mapping[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Unlink only authorized entries, durably journaling crash recovery."""
    _require(bindings.private_bound, "source_state_drift")
    if not bindings.fixture:
        # Guardian, controller, and worker execution locks are the complete
        # producer-side quiescence set for this frozen Cycle007 tree.
        _require(len(quiescence_lock_paths) == 3, "quiescence_unproved")
    for value in (
        primary,
        portable_export,
        frozen_inventory,
        pack_manifest,
        finalize,
        auth,
        authorization,
        challenge,
        pre_response,
    ):
        _require_receipt(value, "authorization_drift")
    _validate_authorization(auth, authorization, fixture=bindings.fixture)
    _validate_authorized_request_chain(bindings, frozen_inventory, pack_manifest, finalize, auth)
    imported_attestation = _load_imported_attestation(bindings)
    _validate_custody_response(
        portable_export,
        imported_attestation,
        challenge,
        pre_response,
        fixture=bindings.fixture,
    )
    _require(challenge.get("schema_version") == EXECUTION_CHALLENGE_SCHEMA, "authorization_drift")
    _require(
        challenge.get("operator_authorization_sha256") == authorization.get("receipt_sha256"), "authorization_drift"
    )
    _require(challenge.get("deletion_auth_request_sha256") == auth.get("receipt_sha256"), "authorization_drift")
    _require(finalize.get("deletion_auth_request_sha256") == auth.get("receipt_sha256"), "authorization_drift")
    _require(pack_manifest.get("receipt_sha256") == portable_export.get("pack_manifest_sha256"), "custody_drift")
    root = _deletion_root(bindings)
    _require(root.is_dir() and not root.is_symlink(), "execution_state_drift")
    persisted_challenge = _read_receipt(root / "challenge.json", EXECUTION_CHALLENGE_SCHEMA, "execution_state_drift")
    _require(persisted_challenge == challenge, "execution_state_drift")
    _persist_or_match_receipt(
        root / "operator-authorization.json",
        authorization,
        OPERATOR_AUTH_SCHEMA,
        "execution_state_drift",
    )
    _persist_or_match_receipt(
        root / "pre-delete-workstation-response.json",
        pre_response,
        CUSTODY_RESPONSE_SCHEMA,
        "execution_state_drift",
    )
    plan_path = root / "plan.json"
    with _execution_locks(root, quiescence_lock_paths):
        try:
            primary_roundtrip, _identity = storage.prove_content_pack_stream(
                frozen_inventory,
                primary_pack_dir,
                zstd_executable=bindings.zstd_executable,
            )
        except storage.StorageCustodyError as exc:
            raise DeletionExecutionError("custody_drift") from exc
        if os.path.lexists(plan_path):
            plan = _read_receipt(plan_path, PLAN_SCHEMA, "plan_drift")
        else:
            events_path = _event_dir(root)
            _require(not os.path.lexists(events_path), "journal_drift")
            try:
                fresh_inventory = storage.build_inventory(bindings)
                if not bindings.fixture:
                    storage._require_production_inventory_shape(fresh_inventory)
            except storage.StorageCustodyError as exc:
                raise DeletionExecutionError("source_state_drift") from exc
            _critical_inventory_match(frozen_inventory, fresh_inventory, auth)
            plan = _build_plan(
                bindings,
                frozen_inventory,
                fresh_inventory,
                auth,
                authorization,
                challenge,
                pre_response,
                primary_roundtrip,
            )
            _write_new_receipt(plan_path, plan, "plan_drift")
        _validate_persisted_plan(
            bindings,
            plan,
            frozen_inventory,
            auth,
            authorization,
            challenge,
            pre_response,
            primary_roundtrip,
        )
        _validate_root_identities(bindings, plan)
        _require(
            plan.get("expected_reclaimed_allocated_bytes") == authorization.get("authorized_reclaimed_byte_forecast"),
            "plan_drift",
        )
        _require_no_open_target_descriptors(plan, fixture=bindings.fixture)
        events = _load_events(root, plan)
        if not events:
            _verify_pending_presence(bindings, plan, set(), None)
            _append_event(
                root,
                plan,
                events,
                "START",
                detail={"filesystem_avail_before_bytes": storage.available_bytes(_source_capacity_path(bindings))},
            )
        completed, inflight, inflight_phase = _journal_state(plan, events)
        by_id = {str(entry["entry_id"]): entry for entry in plan["entries"]}
        if inflight is not None:
            entry = by_id[inflight]
            source_present = _entry_present_exact(bindings, entry)
            quarantine_present = _quarantine_present_exact(bindings, plan, entry)
            if inflight_phase == "INTENT":
                if source_present and not quarantine_present:
                    _move_exact_to_quarantine(bindings, plan, entry, fault_hook)
                    _append_event(root, plan, events, "MOVED", entry_id=inflight)
                elif not source_present and quarantine_present:
                    _require_entry_aliases_absent(bindings, entry)
                    _fsync_move_directories(bindings, plan, entry)
                    _append_event(root, plan, events, "RECOVERED_MOVED", entry_id=inflight)
                else:
                    _fail("journal_drift")
            elif inflight_phase != "MOVED":
                _fail("journal_drift")
            if _quarantine_present_exact(bindings, plan, entry):
                _unlink_quarantined_exact(bindings, plan, entry, fault_hook)
            else:
                # A durable MOVED state plus an absent quarantine entry is the
                # crash window after exact unlink but before its event.
                quarantine, _name = _open_quarantine(bindings, plan, entry)
                try:
                    os.fsync(quarantine)
                finally:
                    os.close(quarantine)
                _require_entry_aliases_absent(bindings, entry)
            _append_event(root, plan, events, "RECOVERED_UNLINKED", entry_id=inflight)
            completed.add(inflight)
            inflight = None
        _verify_pending_presence(bindings, plan, completed, inflight)
        for entry in plan["entries"]:
            entry_id = str(entry["entry_id"])
            if entry_id in completed:
                continue
            _fault(fault_hook, "before_intent", entry_id)
            _append_event(root, plan, events, "INTENT", entry_id=entry_id)
            _fault(fault_hook, "after_intent", entry_id)
            _move_exact_to_quarantine(bindings, plan, entry, fault_hook)
            _append_event(root, plan, events, "MOVED", entry_id=entry_id)
            _unlink_quarantined_exact(bindings, plan, entry, fault_hook)
            _fault(fault_hook, "before_unlinked_event", entry_id)
            _append_event(root, plan, events, "UNLINKED", entry_id=entry_id)
            completed.add(entry_id)
        _require(len(completed) == int(plan["entry_count"]), "journal_drift")
        _verify_pending_presence(bindings, plan, completed, None)
        start = events[0].get("detail", {})
        avail_before = int(start.get("filesystem_avail_before_bytes", -1))
        avail_after = storage.available_bytes(_source_capacity_path(bindings))
        try:
            post_primary, _post_identity = storage.prove_content_pack_stream(
                frozen_inventory,
                primary_pack_dir,
                zstd_executable=bindings.zstd_executable,
            )
        except storage.StorageCustodyError as exc:
            raise DeletionExecutionError("custody_drift") from exc
        unlinked_path = root / "unlinked.json"
        if os.path.lexists(unlinked_path):
            unlinked = _read_receipt(unlinked_path, UNLINKED_SCHEMA, "execution_state_drift")
        else:
            unlinked = _receipt(
                {
                    "schema_version": UNLINKED_SCHEMA,
                    "outcome_sha256": storage.OUTCOME_SHA256,
                    "plan_receipt_sha256": plan["receipt_sha256"],
                    "operator_authorization_sha256": authorization["receipt_sha256"],
                    "journal_terminal_event_sha256": events[-1]["receipt_sha256"],
                    "unlinked_entry_count": len(completed),
                    "unlinked_inode_count": plan["inode_count"],
                    "unlinked_path_count": len(completed),
                    "unlinked_object_count": plan["inode_count"],
                    "expected_reclaimed_allocated_bytes": plan["expected_reclaimed_allocated_bytes"],
                    "reclaimed_byte_forecast": plan["expected_reclaimed_allocated_bytes"],
                    "filesystem_avail_before_bytes": avail_before,
                    "filesystem_avail_after_unlink_bytes": avail_after,
                    "source_avail_before_bytes": avail_before,
                    "source_avail_after_bytes": avail_after,
                    "observed_filesystem_avail_delta_bytes": avail_after - avail_before,
                    "forecast_and_observed_are_distinct": True,
                    "fresh_post_unlink_primary_roundtrip_sha256": post_primary["receipt_sha256"],
                    "all_authorized_entries_absent": True,
                    "directories_removed": 0,
                    "compact_primary_retained": True,
                    "awaiting_post_delete_workstation_proof": True,
                }
            )
            _write_new_receipt(unlinked_path, unlinked, "execution_state_drift")
        _validate_unlinked_receipt(unlinked, plan, authorization, events, post_primary)
        post_path = root / "post-delete-challenge.json"
        if os.path.lexists(post_path):
            post_challenge = _read_receipt(post_path, POST_CHALLENGE_SCHEMA, "execution_state_drift")
        else:
            post_challenge = _receipt(
                {
                    "schema_version": POST_CHALLENGE_SCHEMA,
                    "outcome_sha256": storage.OUTCOME_SHA256,
                    "phase": "post_delete",
                    "unlinked_receipt_sha256": unlinked["receipt_sha256"],
                    "operator_authorization_sha256": authorization["receipt_sha256"],
                    "portable_export_receipt_sha256": portable_export["receipt_sha256"],
                    "challenge_nonce": secrets.token_hex(32),
                    "single_use": True,
                }
            )
            _write_new_receipt(post_path, post_challenge, "execution_state_drift")
        _validate_post_challenge(post_challenge, unlinked, authorization, portable_export)
        return {
            "plan": plan,
            "unlinked_receipt": unlinked,
            "post_challenge": post_challenge,
        }


def finalize_deletion_execution(
    bindings: storage.Bindings,
    frozen_inventory: Mapping[str, Any],
    portable_export: Mapping[str, Any],
    authorization: Mapping[str, Any],
    pre_result: Mapping[str, Any],
    post_response: Mapping[str, Any],
    primary_pack_dir: Path,
) -> dict[str, Any]:
    """Close deletion only after fresh post-delete proof of both compact copies."""
    plan = pre_result.get("plan")
    unlinked = pre_result.get("unlinked_receipt")
    post_challenge = pre_result.get("post_challenge")
    _require(isinstance(plan, Mapping), "execution_state_drift")
    _require(isinstance(unlinked, Mapping), "execution_state_drift")
    _require(isinstance(post_challenge, Mapping), "execution_state_drift")
    for value in (frozen_inventory, portable_export, authorization, plan, unlinked, post_challenge, post_response):
        _require_receipt(value, "execution_state_drift")
    root = _deletion_root(bindings)
    persisted_authorization = _read_receipt(
        root / "operator-authorization.json",
        OPERATOR_AUTH_SCHEMA,
        "execution_state_drift",
    )
    _require(persisted_authorization == authorization, "execution_state_drift")
    auth = _read_receipt(
        root.parent / "deletion-auth-request.json",
        storage.AUTH_SCHEMA_VERSION,
        "execution_state_drift",
    )
    _validate_authorization(auth, authorization, fixture=bindings.fixture)
    challenge = _read_receipt(
        root / "challenge.json",
        EXECUTION_CHALLENGE_SCHEMA,
        "execution_state_drift",
    )
    pre_response = _read_receipt(
        root / "pre-delete-workstation-response.json",
        CUSTODY_RESPONSE_SCHEMA,
        "execution_state_drift",
    )
    persisted_plan = _read_receipt(root / "plan.json", PLAN_SCHEMA, "execution_state_drift")
    _require(persisted_plan == plan, "execution_state_drift")
    persisted_unlinked = _read_receipt(root / "unlinked.json", UNLINKED_SCHEMA, "execution_state_drift")
    _require(persisted_unlinked == unlinked, "execution_state_drift")
    persisted_post_challenge = _read_receipt(
        root / "post-delete-challenge.json",
        POST_CHALLENGE_SCHEMA,
        "execution_state_drift",
    )
    _require(persisted_post_challenge == post_challenge, "execution_state_drift")
    events = _load_events(root, plan)
    completed, inflight, inflight_phase = _journal_state(plan, events)
    _require(
        inflight is None and inflight_phase is None and len(completed) == int(plan["entry_count"]),
        "journal_drift",
    )
    _validate_root_identities(bindings, plan)
    _verify_pending_presence(bindings, plan, completed, None)
    try:
        primary_roundtrip, _identity = storage.prove_content_pack_stream(
            frozen_inventory,
            primary_pack_dir,
            zstd_executable=bindings.zstd_executable,
        )
    except storage.StorageCustodyError as exc:
        raise DeletionExecutionError("custody_drift") from exc
    _validate_persisted_plan(
        bindings,
        plan,
        frozen_inventory,
        auth,
        authorization,
        challenge,
        pre_response,
        primary_roundtrip,
    )
    _validate_unlinked_receipt(unlinked, plan, authorization, events, primary_roundtrip)
    _validate_post_challenge(post_challenge, unlinked, authorization, portable_export)
    imported_attestation = _load_imported_attestation(bindings)
    _validate_custody_response(
        portable_export,
        imported_attestation,
        post_challenge,
        post_response,
        fixture=bindings.fixture,
    )
    _persist_or_match_receipt(
        root / "post-delete-workstation-response.json",
        post_response,
        CUSTODY_RESPONSE_SCHEMA,
        "execution_state_drift",
    )
    current_avail = storage.available_bytes(_source_capacity_path(bindings))
    initial_avail = int(unlinked["filesystem_avail_before_bytes"])
    completion_path = root / "completion.json"
    if os.path.lexists(completion_path):
        completion = _read_receipt(completion_path, COMPLETION_SCHEMA, "execution_state_drift")
        _validate_completion_receipt(
            completion,
            plan,
            authorization,
            unlinked,
            post_response,
            primary_roundtrip,
            events,
        )
        return completion
    completion = _receipt(
        {
            "schema_version": COMPLETION_SCHEMA,
            "outcome_sha256": storage.OUTCOME_SHA256,
            "deletion_complete": True,
            "operator_authorization_sha256": authorization["receipt_sha256"],
            "plan_receipt_sha256": plan["receipt_sha256"],
            "unlinked_receipt_sha256": unlinked["receipt_sha256"],
            "post_delete_workstation_response_sha256": post_response["receipt_sha256"],
            "fresh_final_primary_roundtrip_sha256": primary_roundtrip["receipt_sha256"],
            "compact_copy_count_freshly_verified": 2,
            "authorized_entry_count": plan["entry_count"],
            "authorized_inode_count": plan["inode_count"],
            "expected_reclaimed_allocated_bytes": plan["expected_reclaimed_allocated_bytes"],
            "reclaimed_byte_forecast": plan["expected_reclaimed_allocated_bytes"],
            "filesystem_avail_before_bytes": initial_avail,
            "filesystem_avail_at_completion_bytes": current_avail,
            "observed_filesystem_avail_delta_bytes": current_avail - initial_avail,
            "actual_reclaimed_bytes": current_avail - initial_avail,
            "forecast_and_observed_are_distinct": True,
            "forecast_is_not_actual": True,
            "all_authorized_entries_absent": True,
            "directories_removed": 0,
            "compact_primary_retained": True,
            "compact_workstation_backup_retained": True,
            "journal_event_count": len(events),
            "journal_terminal_event_sha256": events[-1]["receipt_sha256"],
        }
    )
    _validate_completion_receipt(
        completion,
        plan,
        authorization,
        unlinked,
        post_response,
        primary_roundtrip,
        events,
    )
    _write_new_receipt(completion_path, completion, "execution_state_drift")
    return completion
