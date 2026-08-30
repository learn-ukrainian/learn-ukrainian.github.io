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
import fcntl
import hashlib
import os
import secrets
import stat
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

DELETE_ROOT = "cycle007-storage-primary-stage/deletion-execution"
FAULT_POINTS = frozenset(
    {
        "before_intent",
        "after_intent",
        "after_unlink",
        "after_parent_fsync",
        "before_unlinked_event",
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
        _require(
            existing.get("operator_authorization_sha256") == authorization.get("receipt_sha256"),
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
    challenge: Mapping[str, Any],
    response: Mapping[str, Any],
    *,
    fixture: bool,
) -> None:
    for value in (portable_export, challenge, response):
        _require_receipt(value, "custody_drift")
    _require(response.get("schema_version") == CUSTODY_RESPONSE_SCHEMA, "custody_drift")
    _require(response.get("challenge_receipt_sha256") == challenge.get("receipt_sha256"), "custody_drift")
    _require(response.get("challenge_nonce") == challenge.get("challenge_nonce"), "custody_drift")
    _require(response.get("phase") == challenge.get("phase"), "custody_drift")
    _require(response.get("portable_export_receipt_sha256") == portable_export.get("receipt_sha256"), "custody_drift")
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


def _role_path(bindings: storage.Bindings, alias: str) -> Path:
    role, separator, relative = alias.partition("/")
    _require(separator == "/" and relative and ".." not in Path(relative).parts, "plan_drift")
    root = (
        bindings.materialization_package
        if role == "materialization"
        else bindings.evidence_package
        if role == "evidence"
        else None
    )
    _require(root is not None, "plan_drift")
    assert root is not None
    return root / relative


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
    targets = auth.get("targets")
    objects = frozen_inventory.get("objects")
    _require(isinstance(targets, list) and isinstance(objects, list), "plan_drift")
    by_primary = {item.get("role_relative_path"): item for item in objects if isinstance(item, Mapping)}
    entries: list[dict[str, Any]] = []
    planned_inodes: set[tuple[int, int]] = set()
    expected_allocation = 0
    for target in targets:
        _require(isinstance(target, Mapping), "plan_drift")
        _require(target.get("deletion_candidate") is True and target.get("link_set_closed") is True, "plan_drift")
        primary_alias = target.get("role_relative_path")
        source = by_primary.get(primary_alias)
        _require(isinstance(source, Mapping), "plan_drift")
        _same_fields(
            target,
            source,
            (
                "role_relative_path",
                "sha256",
                "selection_class",
                "selected_path_count",
                "selected_link_count",
                "link_count",
                "external_link_count",
                "link_set_closed",
            ),
            "plan_drift",
        )
        aliases = tuple(storage._item_relative_paths(source))
        _require(tuple(target.get("role_relative_paths", ())) == aliases, "plan_drift")
        grouped: dict[str, list[str]] = {}
        for alias in aliases:
            path = _role_path(bindings, alias)
            try:
                resolved = str(path.resolve(strict=True))
                info = path.lstat()
            except OSError as exc:
                raise DeletionExecutionError("source_state_drift") from exc
            _require(stat.S_ISREG(info.st_mode) and not path.is_symlink(), "source_state_drift")
            fs = source.get("fs")
            _require(isinstance(fs, Mapping), "plan_drift")
            _require(
                (int(info.st_dev), int(info.st_ino)) == (int(fs.get("dev", -1)), int(fs.get("ino", -1))),
                "source_state_drift",
            )
            grouped.setdefault(resolved, []).append(alias)
        _require(len(grouped) == int(source.get("selected_link_count", -1)), "plan_drift")
        fs = source["fs"]
        inode = (int(fs["dev"]), int(fs["ino"]))
        _require(inode not in planned_inodes, "plan_drift")
        planned_inodes.add(inode)
        expected_allocation += int(source["allocated_bytes"])
        groups = sorted((sorted(values) for values in grouped.values()), key=lambda values: values[0])
        initial_links = int(source["link_count"])
        _require(initial_links == len(groups), "plan_drift")
        for index, group_aliases in enumerate(groups):
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
            }
            entry_body["entry_id"] = storage.digest(storage.canonical(entry_body))
            entries.append(entry_body)
    entries.sort(key=lambda item: (str(item["role_relative_path"]), str(item["entry_id"])))
    _require(len(planned_inodes) == int(auth.get("deletion_candidate_count", -1)), "plan_drift")
    _require(expected_allocation == int(auth.get("reclaimed_byte_forecast", -1)), "plan_drift")
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
            "inode_count": len(planned_inodes),
            "expected_reclaimed_allocated_bytes": expected_allocation,
            "entries_sha256": plan_digest,
            "entries": entries,
            "files_only": True,
            "directories_authorized": 0,
        }
    )


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
    directory.mkdir(mode=storage.PRIVATE_DIR_MODE, exist_ok=True)
    os.chmod(directory, storage.PRIVATE_DIR_MODE)
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


def _journal_state(plan: Mapping[str, Any], events: Sequence[Mapping[str, Any]]) -> tuple[set[str], str | None]:
    valid = {str(item["entry_id"]) for item in plan["entries"]}
    completed: set[str] = set()
    inflight: str | None = None
    for event in events:
        event_type = event.get("event_type")
        entry_id = event.get("entry_id")
        if event_type == "START":
            _require(entry_id is None and not completed and inflight is None, "journal_drift")
        elif event_type == "INTENT":
            _require(isinstance(entry_id, str) and entry_id in valid, "journal_drift")
            _require(inflight is None and entry_id not in completed, "journal_drift")
            inflight = entry_id
        elif event_type in {"UNLINKED", "RECOVERED_UNLINKED"}:
            _require(entry_id == inflight and isinstance(entry_id, str), "journal_drift")
            completed.add(entry_id)
            inflight = None
        else:
            _fail("journal_drift")
    return completed, inflight


def _open_parent(bindings: storage.Bindings, alias: str) -> tuple[int, str]:
    role, separator, relative = alias.partition("/")
    _require(separator == "/" and relative, "source_state_drift")
    parts = Path(relative).parts
    _require(parts and all(part not in {"", ".", ".."} for part in parts), "source_state_drift")
    root = (
        bindings.materialization_package
        if role == "materialization"
        else bindings.evidence_package
        if role == "evidence"
        else None
    )
    _require(root is not None, "source_state_drift")
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


def _fsync_entry_parent(bindings: storage.Bindings, entry: Mapping[str, Any]) -> None:
    parent, _leaf = _open_parent(bindings, str(entry["role_relative_path"]))
    try:
        os.fsync(parent)
    except OSError as exc:
        raise DeletionExecutionError("source_state_drift") from exc
    finally:
        os.close(parent)


def _unlink_exact(
    bindings: storage.Bindings,
    entry: Mapping[str, Any],
    fault_hook: Callable[[str, str], None] | None,
) -> None:
    parent, leaf = _open_parent(bindings, str(entry["role_relative_path"]))
    file_descriptor = -1
    try:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        file_descriptor = os.open(leaf, flags, dir_fd=parent)
        info = os.fstat(file_descriptor)
        expected_identity = (int(entry["dev"]), int(entry["ino"]))
        _require(stat.S_ISREG(info.st_mode), "source_state_drift")
        _require((int(info.st_dev), int(info.st_ino)) == expected_identity, "source_state_drift")
        _require(stat.S_IMODE(info.st_mode) == int(entry["mode"]), "source_state_drift")
        _require(int(info.st_size) == int(entry["size_bytes"]), "source_state_drift")
        _require(_allocated_from_stat(info) == int(entry["allocated_bytes"]), "source_state_drift")
        _require(int(info.st_nlink) == int(entry["expected_nlink_before"]), "source_state_drift")
        _require(_fd_sha256(file_descriptor) == entry["sha256"], "source_state_drift")
        current = os.stat(leaf, dir_fd=parent, follow_symlinks=False)
        _require((int(current.st_dev), int(current.st_ino)) == expected_identity, "source_state_drift")
        _require(stat.S_ISREG(current.st_mode) and not stat.S_ISLNK(current.st_mode), "source_state_drift")
        os.unlink(leaf, dir_fd=parent)
        if fault_hook is not None:
            fault_hook("after_unlink", str(entry["entry_id"]))
        os.fsync(parent)
        if fault_hook is not None:
            fault_hook("after_parent_fsync", str(entry["entry_id"]))
        try:
            os.stat(leaf, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            _fail("source_state_drift")
    except OSError as exc:
        raise DeletionExecutionError("source_state_drift") from exc
    finally:
        if file_descriptor >= 0:
            os.close(file_descriptor)
        os.close(parent)


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
        for path in quiescence_lock_paths:
            _require(path.is_absolute(), "quiescence_unproved")
            info = path.lstat()
            _require(stat.S_ISREG(info.st_mode) and not path.is_symlink(), "quiescence_unproved")
            _require(stat.S_IMODE(info.st_mode) == storage.PRIVATE_FILE_MODE, "quiescence_unproved")
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


def _require_no_open_target_descriptors(plan: Mapping[str, Any], *, fixture: bool) -> None:
    if fixture:
        return
    proc = Path("/proc")
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
            if process.stat().st_uid != own_uid:
                continue
            descriptors = list((process / "fd").iterdir())
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError as exc:
            raise DeletionExecutionError("quiescence_unproved") from exc
        for descriptor in descriptors:
            try:
                info = descriptor.stat()
            except (FileNotFoundError, ProcessLookupError, PermissionError):
                continue
            if (int(info.st_dev), int(info.st_ino)) in targets:
                _fail("quiescence_unproved")


def _verify_pending_presence(
    bindings: storage.Bindings,
    plan: Mapping[str, Any],
    completed: set[str],
    inflight: str | None,
) -> None:
    for entry in plan["entries"]:
        entry_id = str(entry["entry_id"])
        present = _entry_present_exact(bindings, entry)
        if entry_id in completed:
            _require(not present, "journal_drift")
            _require_entry_aliases_absent(bindings, entry)
        elif entry_id != inflight:
            _require(present, "source_state_drift")


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
    fault_hook: Callable[[str, str], None] | None = None,
) -> dict[str, Any]:
    """Unlink only authorized entries, durably journaling crash recovery."""
    _require(bindings.private_bound, "source_state_drift")
    if not bindings.fixture:
        _require(bool(quiescence_lock_paths), "quiescence_unproved")
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
    _validate_custody_response(portable_export, challenge, pre_response, fixture=bindings.fixture)
    _require(challenge.get("schema_version") == EXECUTION_CHALLENGE_SCHEMA, "authorization_drift")
    _require(
        challenge.get("operator_authorization_sha256") == authorization.get("receipt_sha256"), "authorization_drift"
    )
    _require(challenge.get("deletion_auth_request_sha256") == auth.get("receipt_sha256"), "authorization_drift")
    _require(finalize.get("deletion_auth_request_sha256") == auth.get("receipt_sha256"), "authorization_drift")
    _require(pack_manifest.get("receipt_sha256") == portable_export.get("pack_manifest_sha256"), "custody_drift")
    root = _deletion_root(bindings)
    _require(root.is_dir() and not root.is_symlink(), "execution_state_drift")
    plan_path = root / "plan.json"
    with _execution_locks(root, quiescence_lock_paths):
        primary_roundtrip, _identity = storage.prove_content_pack_stream(
            frozen_inventory, primary_pack_dir, zstd_executable=bindings.zstd_executable
        )
        if os.path.lexists(plan_path):
            plan = _read_receipt(plan_path, PLAN_SCHEMA, "plan_drift")
            _require(plan.get("operator_authorization_sha256") == authorization.get("receipt_sha256"), "plan_drift")
            _require(plan.get("deletion_auth_request_sha256") == auth.get("receipt_sha256"), "plan_drift")
        else:
            events_path = _event_dir(root)
            _require(not os.path.lexists(events_path), "journal_drift")
            fresh_inventory = storage.build_inventory(bindings)
            if not bindings.fixture:
                storage._require_production_inventory_shape(fresh_inventory)
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
                detail={"filesystem_avail_before_bytes": storage.available_bytes(bindings.work_root)},
            )
        completed, inflight = _journal_state(plan, events)
        by_id = {str(entry["entry_id"]): entry for entry in plan["entries"]}
        if inflight is not None:
            entry = by_id[inflight]
            if _entry_present_exact(bindings, entry):
                _unlink_exact(bindings, entry, fault_hook)
            else:
                # The durable INTENT makes an absent entry recoverable after a
                # crash in the unlink-to-journal gap.  Persist the parent
                # directory before recording recovered completion.
                _fsync_entry_parent(bindings, entry)
                _require_entry_aliases_absent(bindings, entry)
            _append_event(root, plan, events, "RECOVERED_UNLINKED", entry_id=inflight)
            completed.add(inflight)
            inflight = None
        _verify_pending_presence(bindings, plan, completed, inflight)
        for entry in plan["entries"]:
            entry_id = str(entry["entry_id"])
            if entry_id in completed:
                continue
            if fault_hook is not None:
                fault_hook("before_intent", entry_id)
            _append_event(root, plan, events, "INTENT", entry_id=entry_id)
            if fault_hook is not None:
                fault_hook("after_intent", entry_id)
            _unlink_exact(bindings, entry, fault_hook)
            if fault_hook is not None:
                fault_hook("before_unlinked_event", entry_id)
            _append_event(root, plan, events, "UNLINKED", entry_id=entry_id)
            completed.add(entry_id)
        _require(len(completed) == int(plan["entry_count"]), "journal_drift")
        _verify_pending_presence(bindings, plan, completed, None)
        start = events[0].get("detail", {})
        avail_before = int(start.get("filesystem_avail_before_bytes", -1))
        avail_after = storage.available_bytes(bindings.work_root)
        post_primary, _post_identity = storage.prove_content_pack_stream(
            frozen_inventory, primary_pack_dir, zstd_executable=bindings.zstd_executable
        )
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
                    "expected_reclaimed_allocated_bytes": plan["expected_reclaimed_allocated_bytes"],
                    "filesystem_avail_before_bytes": avail_before,
                    "filesystem_avail_after_unlink_bytes": avail_after,
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
    _validate_custody_response(portable_export, post_challenge, post_response, fixture=bindings.fixture)
    _require(post_challenge.get("unlinked_receipt_sha256") == unlinked.get("receipt_sha256"), "execution_state_drift")
    root = _deletion_root(bindings)
    persisted_plan = _read_receipt(root / "plan.json", PLAN_SCHEMA, "execution_state_drift")
    _require(persisted_plan == plan, "execution_state_drift")
    events = _load_events(root, plan)
    completed, inflight = _journal_state(plan, events)
    _require(inflight is None and len(completed) == int(plan["entry_count"]), "journal_drift")
    _validate_root_identities(bindings, plan)
    _verify_pending_presence(bindings, plan, completed, None)
    primary_roundtrip, _identity = storage.prove_content_pack_stream(
        frozen_inventory, primary_pack_dir, zstd_executable=bindings.zstd_executable
    )
    current_avail = storage.available_bytes(bindings.work_root)
    initial_avail = int(unlinked["filesystem_avail_before_bytes"])
    completion_path = root / "completion.json"
    if os.path.lexists(completion_path):
        completion = _read_receipt(completion_path, COMPLETION_SCHEMA, "execution_state_drift")
        _require(
            completion.get("post_delete_workstation_response_sha256") == post_response.get("receipt_sha256"),
            "execution_state_drift",
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
            "filesystem_avail_before_bytes": initial_avail,
            "filesystem_avail_at_completion_bytes": current_avail,
            "observed_filesystem_avail_delta_bytes": current_avail - initial_avail,
            "forecast_and_observed_are_distinct": True,
            "all_authorized_entries_absent": True,
            "directories_removed": 0,
            "compact_primary_retained": True,
            "compact_workstation_backup_retained": True,
            "journal_event_count": len(events),
            "journal_terminal_event_sha256": events[-1]["receipt_sha256"],
        }
    )
    _write_new_receipt(completion_path, completion, "execution_state_drift")
    return completion
