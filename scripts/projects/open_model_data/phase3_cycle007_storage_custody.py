#!/usr/bin/env python3
"""Reversible Cycle007 storage/custody compaction lane (#7434).

Text-free identities, allocated-byte inventory, capacity measurement, retention
decision, versioned compact pack, exact round-trip proof, recoverable backup,
and deletion-target forecast. Does not delete, truncate, unlink, reclaim,
relabel, execute providers, or print private topology or content.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
import os
import re
import shutil
import stat
import tempfile
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract
from scripts.projects.open_model_data import phase3_cycle007_materializer as materializer

OUTCOME_SHA256 = "890498103f96a7b8f27fd52bc14418d8752e5b73a72ed8774dd0f52eb3160a47"
HANDOFF_RECEIPT_SHA256 = "056fa042edb4c2ee0df19264107fc3d3bbd9c033158ec52b9df603d6eb1dd94c"
EXPECTED_PACKET_COUNT = 204
EXPECTED_ROW_COUNT = 10_159
EVALUATION_CYCLE_ID = materializer.CYCLE007
PACK_SCHEMA_VERSION = "phase3_cycle007_storage_pack_v1"
INVENTORY_SCHEMA_VERSION = "phase3_cycle007_storage_inventory_v1"
LANE_RECEIPT_SCHEMA_VERSION = "phase3_cycle007_storage_lane_receipt_v1"
BACKUP_SCHEMA_VERSION = "phase3_cycle007_storage_backup_v1"
AUTH_SCHEMA_VERSION = "phase3_cycle007_storage_deletion_auth_request_v1"

RETAIN_MINIMAL_EVALUATION_ASSET = "RETAIN_MINIMAL_EVALUATION_ASSET"
RETIRE_CYCLE007 = "RETIRE_CYCLE007"
RETENTION_OUTCOMES = frozenset({RETAIN_MINIMAL_EVALUATION_ASSET, RETIRE_CYCLE007})

PRIVATE_DIR_MODE = 0o700
PRIVATE_FILE_MODE = 0o600
REAL_CONFIG_ENV = "PHASE3_CYCLE007_STORAGE_CONFIG"
REAL_MATERIALIZATION_ENV = "PHASE3_CYCLE007_STORAGE_MATERIALIZATION_PACKAGE"
REAL_EVIDENCE_ENV = "PHASE3_CYCLE007_STORAGE_EVIDENCE_PACKAGE"
REAL_WORK_ENV = "PHASE3_CYCLE007_STORAGE_WORK_ROOT"

PACKET_NAME_RE = re.compile(r"packet-(\d{4})\.json\Z")
SIDECAR_NAME_RE = re.compile(r"sidecar-(\d{4})\.json\Z")
LABELING_OUTPUT_ROOTS = (
    "label-output-gemini-cycle007-v1",
    "label-output-grok-cycle007-v1",
    "dual-label-output-cycle007-v1",
    "consensus-audit-cycle007-v1",
    "dual-label-adjudication-cycle007-v1",
    "dual-label-final-cycle007-v1",
)

FAILURE_CODES = frozenset(
    {
        "path_disclosure_refused",
        "private_binding_unbound",
        "inventory_shape_failure",
        "denominator_drift",
        "identity_roundtrip_failure",
        "backup_restore_failure",
        "capacity_insufficient",
        "pack_shape_failure",
        "retention_blocked",
        "deletion_not_authorized",
        "fixture_flag_required",
        "work_root_failure",
        "source_mode_drift",
    }
)


class StorageCustodyError(ValueError):
    """Closed, text-free storage/custody failure."""

    def __init__(self, code: str) -> None:
        self.code = code if code in FAILURE_CODES else "inventory_shape_failure"
        super().__init__(self.code)


def canonical(value: Any) -> bytes:
    return (contract.canonical_json(value) + "\n").encode("utf-8")


def digest(data: bytes) -> str:
    return contract.sha256_bytes(data)


def digest_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def allocated_bytes(path: Path) -> int:
    info = path.lstat()
    blocks = getattr(info, "st_blocks", 0)
    return int(blocks * 512) if blocks else int(info.st_size)


def available_bytes(path: Path) -> int:
    value = os.statvfs(path)
    return int(value.f_bavail * value.f_frsize)


def filesystem_totals(path: Path) -> dict[str, int]:
    value = os.statvfs(path)
    return {
        "frsize": int(value.f_frsize),
        "blocks": int(value.f_blocks),
        "bfree": int(value.f_bfree),
        "bavail": int(value.f_bavail),
        "total_bytes": int(value.f_blocks * value.f_frsize),
        "free_bytes": int(value.f_bfree * value.f_frsize),
        "avail_bytes": int(value.f_bavail * value.f_frsize),
    }


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise StorageCustodyError(code)


def _hash_receipt(value: Mapping[str, Any]) -> str:
    return digest(canonical({key: item for key, item in value.items() if key != "receipt_sha256"}))


def _receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    body = dict(value)
    body["text_free"] = True
    body["receipt_sha256"] = _hash_receipt(body)
    return body


def _regular(path: Path, code: str = "inventory_shape_failure") -> None:
    try:
        entry = path.lstat()
    except OSError as exc:
        raise StorageCustodyError(code) from exc
    if path.is_symlink() or not stat.S_ISREG(entry.st_mode):
        raise StorageCustodyError(code)


def _directory(path: Path, code: str = "inventory_shape_failure") -> None:
    try:
        entry = path.lstat()
    except OSError as exc:
        raise StorageCustodyError(code) from exc
    if path.is_symlink() or not stat.S_ISDIR(entry.st_mode):
        raise StorageCustodyError(code)


def _read_json(path: Path, code: str = "inventory_shape_failure") -> Any:
    _regular(path, code)
    try:
        return json.loads(path.read_bytes().decode("utf-8", "strict"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StorageCustodyError(code) from exc


def _atomic_write(path: Path, data: bytes, *, mode: int = PRIVATE_FILE_MODE) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, PRIVATE_DIR_MODE)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp_path, mode)
        os.replace(tmp_path, path)
        dir_fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
    return digest(data)


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> str:
    return _atomic_write(path, canonical(value))


def _opaque_fs_id(path: Path) -> dict[str, int]:
    info = path.lstat()
    return {"dev": int(info.st_dev), "ino": int(info.st_ino)}


@dataclass(frozen=True)
class Bindings:
    materialization_package: Path | None
    evidence_package: Path | None
    work_root: Path
    fixture: bool

    @property
    def private_bound(self) -> bool:
        return self.materialization_package is not None or self.evidence_package is not None


def resolve_bindings(
    *,
    fixture: bool = False,
    materialization: Path | None = None,
    evidence: Path | None = None,
    work_root: Path | None = None,
) -> Bindings:
    if fixture:
        _require(materialization is not None or evidence is not None, "fixture_flag_required")
        _require(work_root is not None, "work_root_failure")
        assert work_root is not None
        _directory(work_root, "work_root_failure")
        if materialization is not None:
            _directory(materialization)
        if evidence is not None:
            _directory(evidence)
        return Bindings(materialization, evidence, work_root, True)

    _require(materialization is None and evidence is None and work_root is None, "path_disclosure_refused")
    config_env = os.environ.get(REAL_CONFIG_ENV)
    mat_path: Path | None = None
    evid_path: Path | None = None
    work_path: Path | None = None
    if config_env:
        config_path = Path(config_env)
        _regular(config_path, "path_disclosure_refused")
        _require(stat.S_IMODE(config_path.stat().st_mode) == PRIVATE_FILE_MODE, "path_disclosure_refused")
        payload = _read_json(config_path, "path_disclosure_refused")
        _require(isinstance(payload, Mapping), "path_disclosure_refused")
        for key in ("materialization_package", "evidence_package", "work_root"):
            value = payload.get(key)
            if value is None:
                continue
            _require(isinstance(value, str) and value.startswith("/"), "path_disclosure_refused")
            resolved = Path(value)
            if key == "work_root":
                work_path = resolved
            elif key == "materialization_package":
                mat_path = resolved
            else:
                evid_path = resolved
    mat_env = os.environ.get(REAL_MATERIALIZATION_ENV)
    evid_env = os.environ.get(REAL_EVIDENCE_ENV)
    work_env = os.environ.get(REAL_WORK_ENV)
    if mat_env:
        mat_path = Path(mat_env)
    if evid_env:
        evid_path = Path(evid_env)
    if work_env:
        work_path = Path(work_env)
    _require(work_path is not None, "private_binding_unbound")
    assert work_path is not None
    if not work_path.exists():
        work_path.mkdir(parents=True, mode=PRIVATE_DIR_MODE)
    _directory(work_path, "work_root_failure")
    os.chmod(work_path, PRIVATE_DIR_MODE)
    if mat_path is not None:
        _directory(mat_path, "private_binding_unbound")
        _require(stat.S_IMODE(mat_path.stat().st_mode) == PRIVATE_DIR_MODE, "source_mode_drift")
    if evid_path is not None:
        _directory(evid_path, "private_binding_unbound")
        _require(stat.S_IMODE(evid_path.stat().st_mode) == PRIVATE_DIR_MODE, "source_mode_drift")
    return Bindings(mat_path, evid_path, work_path, False)


def classify_relative(rel: str, *, role: str) -> str | None:
    name = Path(rel).name
    if name == "custody-receipt.json":
        return "materialization_custody"
    if name == "manifest.json" and "/" not in rel.strip("/"):
        if role == "evidence":
            return "evidence_manifest"
        return "materialization_manifest"
    if PACKET_NAME_RE.fullmatch(name) and rel.split("/", 1)[0] in materializer.LANE_ORDER:
        return "materialization_packet"
    if SIDECAR_NAME_RE.fullmatch(name):
        return "evidence_sidecar"
    if name == "manifest.json":
        return "evidence_manifest"
    if any(root in rel for root in LABELING_OUTPUT_ROOTS):
        return "labeling_expansion"
    if name == "progress.json" or name.startswith(".sidecar-"):
        return "compile_expansion"
    return None


def iter_selected_files(root: Path, *, role: str) -> Iterator[tuple[str, Path, str]]:
    _directory(root)
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames if not Path(dirpath, d).is_symlink())
        for filename in sorted(filenames):
            path = Path(dirpath) / filename
            if path.is_symlink():
                continue
            if not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            selection = classify_relative(rel, role=role)
            if selection is None:
                continue
            yield f"{role}/{rel}", path, selection


def _identity_fields_from_packet(path: Path) -> tuple[int, list[tuple[str, str]]]:
    """Extract only unit_id/unit_sha256; never retain source or evidence text."""
    payload = _read_json(path)
    _require(isinstance(payload, Mapping), "inventory_shape_failure")
    rows = payload.get("rows")
    _require(isinstance(rows, list), "inventory_shape_failure")
    identities: list[tuple[str, str]] = []
    for row in rows:
        _require(isinstance(row, Mapping), "inventory_shape_failure")
        unit_id = row.get("unit_id")
        unit_sha256 = row.get("unit_sha256")
        _require(isinstance(unit_id, str) and bool(unit_id), "inventory_shape_failure")
        _require(isinstance(unit_sha256, str) and len(unit_sha256) == 64, "inventory_shape_failure")
        identities.append((unit_id, unit_sha256))
    return len(identities), identities


def _sidecar_identity(path: Path) -> dict[str, Any]:
    payload = _read_json(path)
    _require(isinstance(payload, Mapping), "inventory_shape_failure")
    sidecar_id = payload.get("sidecar_id")
    packet_index = payload.get("packet_index")
    row_count = payload.get("row_count")
    lane = payload.get("lane")
    binding = payload.get("packet_binding")
    _require(isinstance(sidecar_id, str) and sidecar_id.startswith("cycle007_sidecar:"), "inventory_shape_failure")
    _require(isinstance(packet_index, int) and packet_index >= 1, "inventory_shape_failure")
    _require(isinstance(row_count, int) and row_count >= 1, "inventory_shape_failure")
    _require(lane in materializer.LANE_ORDER, "inventory_shape_failure")
    _require(isinstance(binding, Mapping), "inventory_shape_failure")
    raw_sha256 = binding.get("raw_sha256")
    packet_identity_set_sha256 = binding.get("packet_identity_set_sha256")
    _require(isinstance(raw_sha256, str) and len(raw_sha256) == 64, "inventory_shape_failure")
    _require(
        isinstance(packet_identity_set_sha256, str) and len(packet_identity_set_sha256) == 64,
        "inventory_shape_failure",
    )
    row_identities: list[tuple[str, str]] = []
    rows = payload.get("rows")
    _require(isinstance(rows, list) and len(rows) == row_count, "inventory_shape_failure")
    for row in rows:
        _require(isinstance(row, Mapping), "inventory_shape_failure")
        unit_id = row.get("unit_id")
        unit_sha256 = row.get("unit_sha256")
        _require(isinstance(unit_id, str) and bool(unit_id), "inventory_shape_failure")
        _require(isinstance(unit_sha256, str) and len(unit_sha256) == 64, "inventory_shape_failure")
        row_identities.append((unit_id, unit_sha256))
    return {
        "sidecar_id": sidecar_id,
        "packet_index": packet_index,
        "row_count": row_count,
        "lane": lane,
        "packet_raw_sha256": raw_sha256,
        "packet_identity_set_sha256": packet_identity_set_sha256,
        "row_identities": row_identities,
    }


def build_inventory(bindings: Bindings) -> dict[str, Any]:
    objects: list[dict[str, Any]] = []
    row_identities: list[tuple[str, str]] = []
    packet_files = 0
    sidecar_files = 0
    total_alloc = 0
    total_size = 0
    selection_counts: dict[str, int] = {}

    roots: list[tuple[str, Path]] = []
    if bindings.materialization_package is not None:
        roots.append(("materialization", bindings.materialization_package))
    if bindings.evidence_package is not None:
        roots.append(("evidence", bindings.evidence_package))
    _require(bool(roots), "private_binding_unbound")

    for role, root in roots:
        for rel, path, selection in iter_selected_files(root, role=role):
            raw_sha256 = digest_file(path)
            size = path.stat().st_size
            alloc = allocated_bytes(path)
            mode = stat.S_IMODE(path.stat().st_mode)
            entry: dict[str, Any] = {
                "role_relative_path": rel,
                "selection_class": selection,
                "sha256": raw_sha256,
                "size_bytes": size,
                "allocated_bytes": alloc,
                "mode": mode,
                "fs": _opaque_fs_id(path),
            }
            if selection == "materialization_packet":
                count, identities = _identity_fields_from_packet(path)
                entry["row_count"] = count
                entry["packet_identity_set_sha256"] = materializer.identity_set(
                    [{"unit_id": u, "unit_sha256": s} for u, s in identities]
                )
                row_identities.extend(identities)
                packet_files += 1
            elif selection == "evidence_sidecar":
                meta = _sidecar_identity(path)
                entry["sidecar_id"] = meta["sidecar_id"]
                entry["packet_index"] = meta["packet_index"]
                entry["row_count"] = meta["row_count"]
                entry["lane"] = meta["lane"]
                entry["packet_raw_sha256"] = meta["packet_raw_sha256"]
                entry["packet_identity_set_sha256"] = meta["packet_identity_set_sha256"]
                if bindings.materialization_package is None:
                    row_identities.extend(meta["row_identities"])
                sidecar_files += 1
            objects.append(entry)
            total_alloc += alloc
            total_size += size
            selection_counts[selection] = selection_counts.get(selection, 0) + 1

    objects.sort(key=lambda item: item["role_relative_path"])
    ordered_identity_commitment = digest(
        "\n".join(f"{unit_id}\t{unit_sha256}" for unit_id, unit_sha256 in row_identities).encode("utf-8")
    )
    object_set_sha256 = digest(
        "\n".join(f"{item['role_relative_path']}\t{item['sha256']}" for item in objects).encode("utf-8")
    )

    materialization_counts = _materialization_counts(bindings.materialization_package)
    evidence_counts = _evidence_counts(bindings.evidence_package)

    packet_count = materialization_counts.get("packet_count")
    row_count = materialization_counts.get("row_count")
    if packet_count is None and evidence_counts.get("packet_count") is not None:
        packet_count = evidence_counts["packet_count"]
    if row_count is None and evidence_counts.get("row_count") is not None:
        row_count = evidence_counts["row_count"]
    if packet_count is None:
        packet_count = packet_files or sidecar_files
    if row_count is None:
        row_count = len(row_identities)

    strict = not bindings.fixture
    if strict:
        _require(packet_count == EXPECTED_PACKET_COUNT, "denominator_drift")
        _require(row_count == EXPECTED_ROW_COUNT, "denominator_drift")

    capacity_path = bindings.work_root
    if bindings.evidence_package is not None:
        capacity_path = bindings.evidence_package
    elif bindings.materialization_package is not None:
        capacity_path = bindings.materialization_package

    inventory = _receipt(
        {
            "schema_version": INVENTORY_SCHEMA_VERSION,
            "outcome_sha256": OUTCOME_SHA256,
            "evaluation_cycle_id": EVALUATION_CYCLE_ID,
            "fixture": bindings.fixture,
            "packet_count": int(packet_count),
            "row_count": int(row_count),
            "object_count": len(objects),
            "sidecar_count": sidecar_files,
            "packet_file_count": packet_files,
            "selection_counts": dict(sorted(selection_counts.items())),
            "total_size_bytes": total_size,
            "total_allocated_bytes": total_alloc,
            "ordered_row_identity_commitment_sha256": ordered_identity_commitment,
            "object_set_sha256": object_set_sha256,
            "filesystem": filesystem_totals(capacity_path),
            "materialization_bound": bindings.materialization_package is not None,
            "evidence_bound": bindings.evidence_package is not None,
            "materialization_fs": (
                _opaque_fs_id(bindings.materialization_package)
                if bindings.materialization_package is not None
                else None
            ),
            "evidence_fs": (
                _opaque_fs_id(bindings.evidence_package) if bindings.evidence_package is not None else None
            ),
            "objects": objects,
        }
    )
    return inventory


def _materialization_counts(package: Path | None) -> dict[str, Any]:
    if package is None:
        return {}
    manifest_path = package / "manifest.json"
    if not manifest_path.is_file():
        return {}
    manifest = _read_json(manifest_path)
    _require(isinstance(manifest, Mapping), "inventory_shape_failure")
    return {
        "packet_count": manifest.get("packet_count"),
        "row_count": manifest.get("row_count"),
        "ordered_identity_commitment_sha256": manifest.get("ordered_identity_commitment_sha256"),
        "schema_version": manifest.get("schema_version"),
        "text_free": manifest.get("text_free"),
    }


def _evidence_counts(package: Path | None) -> dict[str, Any]:
    if package is None:
        return {}
    manifest_path = package / "manifest.json"
    if not manifest_path.is_file():
        return {}
    manifest = _read_json(manifest_path)
    _require(isinstance(manifest, Mapping), "inventory_shape_failure")
    sidecars = manifest.get("sidecars")
    sidecar_count = len(sidecars) if isinstance(sidecars, list) else None
    return {
        "packet_count": manifest.get("packet_count"),
        "row_count": manifest.get("row_count"),
        "sidecar_count": sidecar_count,
        "schema_version": manifest.get("schema_version"),
        "text_free": manifest.get("text_free"),
    }


def decide_retention(
    *,
    inventory: Mapping[str, Any],
    labeling_state: str = "OFF",
    provider_calls: int = 0,
    provider_derived_training_labels: int = 0,
    evaluation_firewall_requires_cycle007_identities: bool = True,
) -> dict[str, Any]:
    """Choose retention using custody/evaluation necessity and text-free metrics only."""
    _require(labeling_state == "OFF", "retention_blocked")
    _require(provider_calls == 0, "retention_blocked")
    _require(provider_derived_training_labels == 0, "retention_blocked")
    packet_count = inventory.get("packet_count")
    row_count = inventory.get("row_count")
    object_count = inventory.get("object_count")
    _require(isinstance(packet_count, int) and packet_count > 0, "retention_blocked")
    _require(isinstance(row_count, int) and row_count > 0, "retention_blocked")
    _require(isinstance(object_count, int) and object_count > 0, "retention_blocked")

    if evaluation_firewall_requires_cycle007_identities:
        outcome = RETAIN_MINIMAL_EVALUATION_ASSET
        rationale_code = "evaluation_firewall_requires_identity_assets"
    else:
        # Full retirement is only expressible when evaluation necessity is false.
        outcome = RETIRE_CYCLE007
        rationale_code = "evaluation_firewall_does_not_require_cycle007"

    return _receipt(
        {
            "schema_version": "phase3_cycle007_storage_retention_decision_v1",
            "outcome_sha256": OUTCOME_SHA256,
            "retention_outcome": outcome,
            "rationale_code": rationale_code,
            "labeling_state": labeling_state,
            "provider_calls": provider_calls,
            "provider_derived_training_labels": provider_derived_training_labels,
            "evaluation_firewall_requires_cycle007_identities": (
                evaluation_firewall_requires_cycle007_identities
            ),
            "packet_count": packet_count,
            "row_count": row_count,
            "object_count": object_count,
            "total_allocated_bytes": inventory.get("total_allocated_bytes"),
            "inventory_receipt_sha256": inventory.get("receipt_sha256"),
        }
    )


def forecast_peak_temporary_bytes(
    inventory: Mapping[str, Any],
    *,
    compact_stored_bytes: int,
    backup_stored_bytes: int,
) -> dict[str, Any]:
    allocated = int(inventory["total_allocated_bytes"])
    # Sequential reversible peaks while originals remain untouched:
    # 1) write compact pack beside originals
    # 2) write backup of pack
    # 3) restore into a temporary workspace for proof
    peak_compact = allocated + compact_stored_bytes
    peak_backup = allocated + compact_stored_bytes + backup_stored_bytes
    peak_restore = allocated + compact_stored_bytes + backup_stored_bytes + allocated
    peak = max(peak_compact, peak_backup, peak_restore)
    filesystem = inventory["filesystem"]
    avail = int(filesystem["avail_bytes"])
    return _receipt(
        {
            "schema_version": "phase3_cycle007_storage_peak_forecast_v1",
            "outcome_sha256": OUTCOME_SHA256,
            "original_allocated_bytes": allocated,
            "compact_stored_bytes": compact_stored_bytes,
            "backup_stored_bytes": backup_stored_bytes,
            "peak_temporary_bytes": peak,
            "filesystem_avail_bytes": avail,
            "capacity_sufficient_for_peak": avail >= peak,
            "inventory_receipt_sha256": inventory.get("receipt_sha256"),
        }
    )


def _store_object_bytes(raw: bytes) -> tuple[str, bytes, int]:
    compressed = lzma.compress(raw, preset=6)
    if len(compressed) + 64 < len(raw):
        return "lzma", compressed, len(compressed)
    return "raw", raw, len(raw)


def write_pack(inventory: Mapping[str, Any], bindings: Bindings, pack_dir: Path) -> dict[str, Any]:
    if pack_dir.exists():
        raise StorageCustodyError("pack_shape_failure")
    pack_dir.mkdir(mode=PRIVATE_DIR_MODE)
    os.chmod(pack_dir, PRIVATE_DIR_MODE)
    objects_dir = pack_dir / "objects"
    objects_dir.mkdir(mode=PRIVATE_DIR_MODE)
    os.chmod(objects_dir, PRIVATE_DIR_MODE)

    stored_objects: list[dict[str, Any]] = []
    total_stored = 0
    path_index = _path_index(bindings)

    for item in inventory["objects"]:
        rel = item["role_relative_path"]
        source = path_index[rel]
        raw = source.read_bytes()
        _require(digest(raw) == item["sha256"], "identity_roundtrip_failure")
        storage, payload, stored_size = _store_object_bytes(raw)
        stored_sha256 = digest(payload)
        object_path = objects_dir / item["sha256"][:2] / f"{item['sha256']}.{storage}"
        object_path.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(object_path.parent, PRIVATE_DIR_MODE)
        _atomic_write(object_path, payload)
        total_stored += allocated_bytes(object_path)
        stored_objects.append(
            {
                "role_relative_path": rel,
                "selection_class": item["selection_class"],
                "sha256": item["sha256"],
                "size_bytes": item["size_bytes"],
                "allocated_bytes": item["allocated_bytes"],
                "mode": item["mode"],
                "storage": storage,
                "stored_sha256": stored_sha256,
                "stored_size_bytes": stored_size,
                "object_relative_path": object_path.relative_to(pack_dir).as_posix(),
                "sidecar_id": item.get("sidecar_id"),
                "packet_identity_set_sha256": item.get("packet_identity_set_sha256"),
                "row_count": item.get("row_count"),
                "packet_index": item.get("packet_index"),
                "lane": item.get("lane"),
            }
        )

    pack_manifest = _receipt(
        {
            "schema_version": PACK_SCHEMA_VERSION,
            "outcome_sha256": OUTCOME_SHA256,
            "evaluation_cycle_id": EVALUATION_CYCLE_ID,
            "fixture": bindings.fixture,
            "packet_count": inventory["packet_count"],
            "row_count": inventory["row_count"],
            "object_count": len(stored_objects),
            "ordered_row_identity_commitment_sha256": inventory[
                "ordered_row_identity_commitment_sha256"
            ],
            "object_set_sha256": inventory["object_set_sha256"],
            "inventory_receipt_sha256": inventory["receipt_sha256"],
            "total_original_allocated_bytes": inventory["total_allocated_bytes"],
            "total_stored_allocated_bytes": total_stored,
            "objects": stored_objects,
        }
    )
    _atomic_write_json(pack_dir / "pack-manifest.json", pack_manifest)
    return pack_manifest


def _path_index(bindings: Bindings) -> dict[str, Path]:
    index: dict[str, Path] = {}
    roots: list[tuple[str, Path]] = []
    if bindings.materialization_package is not None:
        roots.append(("materialization", bindings.materialization_package))
    if bindings.evidence_package is not None:
        roots.append(("evidence", bindings.evidence_package))
    for role, root in roots:
        for rel, path, _selection in iter_selected_files(root, role=role):
            index[rel] = path
    return index


def expand_pack(pack_dir: Path, destination: Path) -> dict[str, Any]:
    _directory(pack_dir, "pack_shape_failure")
    manifest = _read_json(pack_dir / "pack-manifest.json", "pack_shape_failure")
    _require(isinstance(manifest, Mapping), "pack_shape_failure")
    _require(manifest.get("schema_version") == PACK_SCHEMA_VERSION, "pack_shape_failure")
    if destination.exists():
        raise StorageCustodyError("pack_shape_failure")
    destination.mkdir(mode=PRIVATE_DIR_MODE)
    os.chmod(destination, PRIVATE_DIR_MODE)

    restored: list[dict[str, Any]] = []
    for item in manifest["objects"]:
        object_path = pack_dir / item["object_relative_path"]
        payload = object_path.read_bytes()
        _require(digest(payload) == item["stored_sha256"], "identity_roundtrip_failure")
        if item["storage"] == "lzma":
            raw = lzma.decompress(payload)
        elif item["storage"] == "raw":
            raw = payload
        else:
            raise StorageCustodyError("pack_shape_failure")
        _require(digest(raw) == item["sha256"], "identity_roundtrip_failure")
        _require(len(raw) == item["size_bytes"], "identity_roundtrip_failure")
        target = destination / item["role_relative_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(target.parent, PRIVATE_DIR_MODE)
        _atomic_write(target, raw, mode=int(item["mode"]))
        restored.append(
            {
                "role_relative_path": item["role_relative_path"],
                "sha256": item["sha256"],
                "size_bytes": item["size_bytes"],
                "selection_class": item["selection_class"],
            }
        )

    object_set_sha256 = digest(
        "\n".join(f"{item['role_relative_path']}\t{item['sha256']}" for item in restored).encode("utf-8")
    )
    _require(object_set_sha256 == manifest["object_set_sha256"], "identity_roundtrip_failure")
    return _receipt(
        {
            "schema_version": "phase3_cycle007_storage_roundtrip_v1",
            "outcome_sha256": OUTCOME_SHA256,
            "pack_manifest_sha256": manifest["receipt_sha256"],
            "object_count": len(restored),
            "object_set_sha256": object_set_sha256,
            "ordered_row_identity_commitment_sha256": manifest[
                "ordered_row_identity_commitment_sha256"
            ],
            "packet_count": manifest["packet_count"],
            "row_count": manifest["row_count"],
            "roundtrip_ok": True,
        }
    )


def verify_roundtrip_identities(
    inventory: Mapping[str, Any],
    restored_root: Path,
) -> dict[str, Any]:
    restored_rows: list[tuple[str, str]] = []
    restored_objects: list[tuple[str, str]] = []
    has_materialization_packets = any(
        item["selection_class"] == "materialization_packet" for item in inventory["objects"]
    )
    for item in inventory["objects"]:
        path = restored_root / item["role_relative_path"]
        _regular(path, "identity_roundtrip_failure")
        raw_sha256 = digest_file(path)
        _require(raw_sha256 == item["sha256"], "identity_roundtrip_failure")
        restored_objects.append((item["role_relative_path"], raw_sha256))
        selection = item["selection_class"]
        if selection == "materialization_packet":
            _count, identities = _identity_fields_from_packet(path)
            restored_rows.extend(identities)
            recomputed = materializer.identity_set(
                [{"unit_id": u, "unit_sha256": s} for u, s in identities]
            )
            _require(recomputed == item["packet_identity_set_sha256"], "identity_roundtrip_failure")
        elif selection == "evidence_sidecar":
            meta = _sidecar_identity(path)
            _require(meta["sidecar_id"] == item["sidecar_id"], "identity_roundtrip_failure")
            _require(
                meta["packet_identity_set_sha256"] == item["packet_identity_set_sha256"],
                "identity_roundtrip_failure",
            )
            if not has_materialization_packets:
                restored_rows.extend(meta["row_identities"])

    if restored_rows:
        ordered = digest(
            "\n".join(f"{unit_id}\t{unit_sha256}" for unit_id, unit_sha256 in restored_rows).encode(
                "utf-8"
            )
        )
        _require(
            ordered == inventory["ordered_row_identity_commitment_sha256"],
            "identity_roundtrip_failure",
        )
    object_set = digest(
        "\n".join(f"{rel}\t{sha}" for rel, sha in restored_objects).encode("utf-8")
    )
    _require(object_set == inventory["object_set_sha256"], "identity_roundtrip_failure")
    return _receipt(
        {
            "schema_version": "phase3_cycle007_storage_identity_proof_v1",
            "outcome_sha256": OUTCOME_SHA256,
            "packet_count": inventory["packet_count"],
            "row_count": inventory["row_count"],
            "object_count": inventory["object_count"],
            "object_set_sha256": object_set,
            "ordered_row_identity_commitment_sha256": inventory[
                "ordered_row_identity_commitment_sha256"
            ],
            "identity_proof_ok": True,
            "inventory_receipt_sha256": inventory["receipt_sha256"],
        }
    )


def create_backup(pack_dir: Path, backup_dir: Path) -> dict[str, Any]:
    if backup_dir.exists():
        raise StorageCustodyError("backup_restore_failure")
    shutil.copytree(pack_dir, backup_dir, symlinks=False)
    for dirpath, _dirnames, filenames in os.walk(backup_dir):
        os.chmod(dirpath, PRIVATE_DIR_MODE)
        for filename in filenames:
            os.chmod(Path(dirpath) / filename, PRIVATE_FILE_MODE)
    manifest = _read_json(backup_dir / "pack-manifest.json", "backup_restore_failure")
    backup_set = []
    total_alloc = 0
    for dirpath, _dirnames, filenames in os.walk(backup_dir):
        for filename in sorted(filenames):
            path = Path(dirpath) / filename
            rel = path.relative_to(backup_dir).as_posix()
            sha = digest_file(path)
            alloc = allocated_bytes(path)
            total_alloc += alloc
            backup_set.append(f"{rel}\t{sha}")
    backup_set_sha256 = digest("\n".join(backup_set).encode("utf-8"))
    return _receipt(
        {
            "schema_version": BACKUP_SCHEMA_VERSION,
            "outcome_sha256": OUTCOME_SHA256,
            "pack_manifest_sha256": manifest["receipt_sha256"],
            "backup_object_count": len(backup_set),
            "backup_allocated_bytes": total_alloc,
            "backup_set_sha256": backup_set_sha256,
            "restore_proof_pending": True,
        }
    )


def prove_backup_restore(backup_dir: Path, restore_dir: Path) -> dict[str, Any]:
    roundtrip = expand_pack(backup_dir, restore_dir)
    _require(roundtrip.get("roundtrip_ok") is True, "backup_restore_failure")
    return _receipt(
        {
            "schema_version": "phase3_cycle007_storage_backup_restore_proof_v1",
            "outcome_sha256": OUTCOME_SHA256,
            "pack_manifest_sha256": roundtrip["pack_manifest_sha256"],
            "object_set_sha256": roundtrip["object_set_sha256"],
            "object_count": roundtrip["object_count"],
            "packet_count": roundtrip["packet_count"],
            "row_count": roundtrip["row_count"],
            "backup_restore_ok": True,
        }
    )


def deletion_auth_request(
    inventory: Mapping[str, Any],
    pack_manifest: Mapping[str, Any],
    retention: Mapping[str, Any],
    backup: Mapping[str, Any],
    restore_proof: Mapping[str, Any],
) -> dict[str, Any]:
    """Exact deletion-target list and reclaim forecast. Does not delete."""
    _require(retention.get("retention_outcome") in RETENTION_OUTCOMES, "retention_blocked")
    _require(backup.get("schema_version") == BACKUP_SCHEMA_VERSION, "backup_restore_failure")
    _require(restore_proof.get("backup_restore_ok") is True, "backup_restore_failure")

    targets: list[dict[str, Any]] = []
    reclaim = 0
    retain_minimal = retention["retention_outcome"] == RETAIN_MINIMAL_EVALUATION_ASSET
    for item in inventory["objects"]:
        selection = item["selection_class"]
        # Under RETAIN_MINIMAL, only expansion-class originals are proposed for
        # deletion after compact+backup proof. Identity-bearing materialization
        # packets/custody remain until a later explicit authorization.
        if retain_minimal and selection in {
            "evidence_sidecar",
            "evidence_manifest",
            "labeling_expansion",
            "compile_expansion",
        }:
            authorized_class = "expansion_reclaim_candidate"
        elif not retain_minimal:
            authorized_class = "full_retirement_candidate"
        else:
            authorized_class = "retain_until_separate_auth"
            targets.append(
                {
                    "role_relative_path": item["role_relative_path"],
                    "selection_class": selection,
                    "sha256": item["sha256"],
                    "allocated_bytes": item["allocated_bytes"],
                    "deletion_candidate": False,
                    "authorized_class": authorized_class,
                }
            )
            continue
        reclaim += int(item["allocated_bytes"])
        targets.append(
            {
                "role_relative_path": item["role_relative_path"],
                "selection_class": selection,
                "sha256": item["sha256"],
                "allocated_bytes": item["allocated_bytes"],
                "deletion_candidate": True,
                "authorized_class": authorized_class,
            }
        )

    return _receipt(
        {
            "schema_version": AUTH_SCHEMA_VERSION,
            "outcome_sha256": OUTCOME_SHA256,
            "deletion_authorized": False,
            "authorization_gate": "operator_explicit_authorization_required",
            "issue_7434_is_not_deletion_authorization": True,
            "retention_outcome": retention["retention_outcome"],
            "retention_receipt_sha256": retention["receipt_sha256"],
            "inventory_receipt_sha256": inventory["receipt_sha256"],
            "pack_manifest_sha256": pack_manifest["receipt_sha256"],
            "backup_receipt_sha256": backup["receipt_sha256"],
            "backup_restore_proof_sha256": restore_proof["receipt_sha256"],
            "deletion_candidate_count": sum(1 for item in targets if item["deletion_candidate"]),
            "retained_object_count": sum(1 for item in targets if not item["deletion_candidate"]),
            "reclaimed_byte_forecast": reclaim,
            "original_allocated_bytes": inventory["total_allocated_bytes"],
            "compact_stored_allocated_bytes": pack_manifest["total_stored_allocated_bytes"],
            "targets": targets,
        }
    )


def reconcile_public_private(
    *,
    private_bound: bool,
    inventory: Mapping[str, Any] | None,
) -> dict[str, Any]:
    public = {
        "handoff_receipt_sha256": HANDOFF_RECEIPT_SHA256,
        "outcome_sha256": OUTCOME_SHA256,
        "public_packet_count": EXPECTED_PACKET_COUNT,
        "public_row_count": EXPECTED_ROW_COUNT,
        "labeling_state": "OFF",
        "provider_calls": 0,
        "provider_derived_training_labels": 0,
        "predecessor_state": "CYCLE007_EVALUATION_ONLY_HISTORICAL",
    }
    if not private_bound:
        return _receipt(
            {
                "schema_version": "phase3_cycle007_storage_reconcile_v1",
                "outcome_sha256": OUTCOME_SHA256,
                "public": public,
                "private_binding_state": "UNBOUND",
                "denominator_match": None,
                "safe_failure_code": "private_binding_unbound",
            }
        )
    assert inventory is not None
    match = (
        inventory["packet_count"] == EXPECTED_PACKET_COUNT
        and inventory["row_count"] == EXPECTED_ROW_COUNT
    )
    return _receipt(
        {
            "schema_version": "phase3_cycle007_storage_reconcile_v1",
            "outcome_sha256": OUTCOME_SHA256,
            "public": public,
            "private_binding_state": "BOUND",
            "private_packet_count": inventory["packet_count"],
            "private_row_count": inventory["row_count"],
            "private_object_count": inventory["object_count"],
            "private_total_allocated_bytes": inventory["total_allocated_bytes"],
            "denominator_match": match,
            "inventory_receipt_sha256": inventory["receipt_sha256"],
            "safe_failure_code": None if match else "denominator_drift",
        }
    )


def run_reversible_lane(bindings: Bindings) -> dict[str, Any]:
    """Execute all safe reversible steps. Never deletes originals."""
    work = bindings.work_root / "cycle007-storage-lane"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(mode=PRIVATE_DIR_MODE)
    os.chmod(work, PRIVATE_DIR_MODE)

    if not bindings.private_bound:
        reconcile = reconcile_public_private(private_bound=False, inventory=None)
        _atomic_write_json(work / "reconcile.json", reconcile)
        lane = _receipt(
            {
                "schema_version": LANE_RECEIPT_SCHEMA_VERSION,
                "outcome_sha256": OUTCOME_SHA256,
                "lane_complete": False,
                "stopped_at": "private_binding_unbound",
                "safe_failure_code": "private_binding_unbound",
                "deletion_authorized": False,
                "reconcile_receipt_sha256": reconcile["receipt_sha256"],
                "retention_outcome": None,
            }
        )
        _atomic_write_json(work / "lane-receipt.json", lane)
        return lane

    inventory = build_inventory(bindings)
    _atomic_write_json(work / "inventory.json", inventory)
    reconcile = reconcile_public_private(private_bound=True, inventory=inventory)
    _atomic_write_json(work / "reconcile.json", reconcile)
    if reconcile.get("denominator_match") is False and not bindings.fixture:
        raise StorageCustodyError("denominator_drift")

    retention = decide_retention(inventory=inventory)
    _atomic_write_json(work / "retention-decision.json", retention)

    pack_dir = work / "pack"
    pack_manifest = write_pack(inventory, bindings, pack_dir)
    _atomic_write_json(work / "pack-manifest.receipt.json", pack_manifest)

    roundtrip_dir = work / "roundtrip-restore"
    expand_receipt = expand_pack(pack_dir, roundtrip_dir)
    identity_proof = verify_roundtrip_identities(inventory, roundtrip_dir)
    _atomic_write_json(work / "roundtrip.json", expand_receipt)
    _atomic_write_json(work / "identity-proof.json", identity_proof)

    backup_dir = work / "backup"
    backup = create_backup(pack_dir, backup_dir)
    restore_dir = work / "backup-restore"
    restore_proof = prove_backup_restore(backup_dir, restore_dir)
    backup["restore_proof_pending"] = False
    backup = _receipt({k: v for k, v in backup.items() if k != "receipt_sha256"})
    _atomic_write_json(work / "backup.json", backup)
    _atomic_write_json(work / "backup-restore-proof.json", restore_proof)

    forecast = forecast_peak_temporary_bytes(
        inventory,
        compact_stored_bytes=int(pack_manifest["total_stored_allocated_bytes"]),
        backup_stored_bytes=int(backup["backup_allocated_bytes"]),
    )
    _atomic_write_json(work / "peak-forecast.json", forecast)
    if not forecast["capacity_sufficient_for_peak"] and not bindings.fixture:
        # Still reversible prep is complete except operator capacity remediation.
        pass

    auth = deletion_auth_request(inventory, pack_manifest, retention, backup, restore_proof)
    _atomic_write_json(work / "deletion-auth-request.json", auth)

    lane = _receipt(
        {
            "schema_version": LANE_RECEIPT_SCHEMA_VERSION,
            "outcome_sha256": OUTCOME_SHA256,
            "lane_complete": True,
            "stopped_at": "deletion_authorization_gate",
            "safe_failure_code": None,
            "deletion_authorized": False,
            "retention_outcome": retention["retention_outcome"],
            "packet_count": inventory["packet_count"],
            "row_count": inventory["row_count"],
            "object_count": inventory["object_count"],
            "total_allocated_bytes": inventory["total_allocated_bytes"],
            "compact_stored_allocated_bytes": pack_manifest["total_stored_allocated_bytes"],
            "reclaimed_byte_forecast": auth["reclaimed_byte_forecast"],
            "deletion_candidate_count": auth["deletion_candidate_count"],
            "filesystem_avail_bytes": inventory["filesystem"]["avail_bytes"],
            "peak_temporary_bytes": forecast["peak_temporary_bytes"],
            "capacity_sufficient_for_peak": forecast["capacity_sufficient_for_peak"],
            "reconcile_receipt_sha256": reconcile["receipt_sha256"],
            "inventory_receipt_sha256": inventory["receipt_sha256"],
            "retention_receipt_sha256": retention["receipt_sha256"],
            "pack_manifest_sha256": pack_manifest["receipt_sha256"],
            "roundtrip_receipt_sha256": expand_receipt["receipt_sha256"],
            "identity_proof_sha256": identity_proof["receipt_sha256"],
            "backup_receipt_sha256": backup["receipt_sha256"],
            "backup_restore_proof_sha256": restore_proof["receipt_sha256"],
            "peak_forecast_receipt_sha256": forecast["receipt_sha256"],
            "deletion_auth_request_sha256": auth["receipt_sha256"],
            "identity_proof_ok": identity_proof["identity_proof_ok"],
            "backup_restore_ok": restore_proof["backup_restore_ok"],
            "roundtrip_ok": expand_receipt["roundtrip_ok"],
        }
    )
    _atomic_write_json(work / "lane-receipt.json", lane)
    return lane


def build_public_summary(lane: Mapping[str, Any], reconcile: Mapping[str, Any]) -> dict[str, Any]:
    """Public, topology-free summary safe for issue/PR/repo reference artifacts."""
    return _receipt(
        {
            "schema_version": "phase3_cycle007_storage_public_summary_v1",
            "outcome_sha256": OUTCOME_SHA256,
            "handoff_receipt_sha256": HANDOFF_RECEIPT_SHA256,
            "issue": 7434,
            "epic": 7423,
            "private_binding_state": reconcile.get("private_binding_state"),
            "lane_complete": lane.get("lane_complete"),
            "stopped_at": lane.get("stopped_at"),
            "safe_failure_code": lane.get("safe_failure_code") or reconcile.get("safe_failure_code"),
            "retention_outcome": lane.get("retention_outcome"),
            "deletion_authorized": False,
            "packet_count": lane.get("packet_count") or EXPECTED_PACKET_COUNT,
            "row_count": lane.get("row_count") or EXPECTED_ROW_COUNT,
            "object_count": lane.get("object_count"),
            "total_allocated_bytes": lane.get("total_allocated_bytes"),
            "compact_stored_allocated_bytes": lane.get("compact_stored_allocated_bytes"),
            "reclaimed_byte_forecast": lane.get("reclaimed_byte_forecast"),
            "deletion_candidate_count": lane.get("deletion_candidate_count"),
            "filesystem_avail_bytes": lane.get("filesystem_avail_bytes"),
            "peak_temporary_bytes": lane.get("peak_temporary_bytes"),
            "capacity_sufficient_for_peak": lane.get("capacity_sufficient_for_peak"),
            "identity_proof_ok": lane.get("identity_proof_ok"),
            "backup_restore_ok": lane.get("backup_restore_ok"),
            "roundtrip_ok": lane.get("roundtrip_ok"),
            "lane_receipt_sha256": lane.get("receipt_sha256"),
            "reconcile_receipt_sha256": reconcile.get("receipt_sha256"),
        }
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=("reconcile", "prepare-lane", "public-summary"),
    )
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--materialization", type=Path)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--public-summary-out", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.action == "reconcile" and not args.fixture and args.materialization is None:
        # Real reconcile without bindings: report unbound without requiring work root.
        reconcile = reconcile_public_private(private_bound=False, inventory=None)
        print(json.dumps({
            "text_free": True,
            "private_binding_state": reconcile["private_binding_state"],
            "safe_failure_code": reconcile["safe_failure_code"],
            "public_packet_count": EXPECTED_PACKET_COUNT,
            "public_row_count": EXPECTED_ROW_COUNT,
            "receipt_sha256": reconcile["receipt_sha256"],
        }, sort_keys=True))
        return 0

    bindings = resolve_bindings(
        fixture=args.fixture,
        materialization=args.materialization,
        evidence=args.evidence,
        work_root=args.work_root,
    )
    if args.action == "prepare-lane":
        lane = run_reversible_lane(bindings)
        reconcile_path = bindings.work_root / "cycle007-storage-lane" / "reconcile.json"
        reconcile = _read_json(reconcile_path)
        summary = build_public_summary(lane, reconcile)
        if args.public_summary_out is not None:
            _atomic_write_json(args.public_summary_out, summary)
        print(json.dumps({
            "text_free": True,
            "lane_complete": lane.get("lane_complete"),
            "stopped_at": lane.get("stopped_at"),
            "safe_failure_code": lane.get("safe_failure_code"),
            "retention_outcome": lane.get("retention_outcome"),
            "deletion_authorized": False,
            "packet_count": lane.get("packet_count"),
            "row_count": lane.get("row_count"),
            "object_count": lane.get("object_count"),
            "total_allocated_bytes": lane.get("total_allocated_bytes"),
            "reclaimed_byte_forecast": lane.get("reclaimed_byte_forecast"),
            "identity_proof_ok": lane.get("identity_proof_ok"),
            "backup_restore_ok": lane.get("backup_restore_ok"),
            "roundtrip_ok": lane.get("roundtrip_ok"),
            "receipt_sha256": lane.get("receipt_sha256"),
            "public_summary_sha256": summary["receipt_sha256"],
        }, sort_keys=True))
        return 0 if lane.get("lane_complete") else 2

    if args.action == "public-summary":
        lane_path = bindings.work_root / "cycle007-storage-lane" / "lane-receipt.json"
        reconcile_path = bindings.work_root / "cycle007-storage-lane" / "reconcile.json"
        lane = _read_json(lane_path)
        reconcile = _read_json(reconcile_path)
        summary = build_public_summary(lane, reconcile)
        if args.public_summary_out is not None:
            _atomic_write_json(args.public_summary_out, summary)
        print(json.dumps({
            "text_free": True,
            "receipt_sha256": summary["receipt_sha256"],
            "retention_outcome": summary.get("retention_outcome"),
            "deletion_authorized": False,
        }, sort_keys=True))
        return 0

    reconcile = reconcile_public_private(
        private_bound=bindings.private_bound,
        inventory=build_inventory(bindings) if bindings.private_bound else None,
    )
    print(json.dumps({
        "text_free": True,
        "private_binding_state": reconcile["private_binding_state"],
        "safe_failure_code": reconcile.get("safe_failure_code"),
        "receipt_sha256": reconcile["receipt_sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
