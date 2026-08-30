#!/usr/bin/env python3
"""Reversible Cycle007 storage/custody compaction lane (#7434).

Text-free identities, allocated-byte inventory, capacity measurement, retention
decision, versioned compact pack, exact round-trip proof, recoverable backup,
and deletion-target forecast. Does not delete, truncate, unlink, or reclaim
originals; relabel; execute providers; or print private topology or content.
"""

from __future__ import annotations

import argparse
import contextlib
import errno
import hashlib
import json
import lzma
import os
import re
import secrets
import shutil
import socket
import stat
import subprocess
import tempfile
import threading
import uuid
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
EXPECTED_SELECTED_PATH_COUNT = 624
EXPECTED_UNIQUE_INODE_COUNT = 419
EXPECTED_DUPLICATE_SELECTED_LINK_COUNT = 205
EXPECTED_PHYSICAL_SIDECAR_COUNT = 204
EXPECTED_LOGICAL_SIDECAR_SELECTION_COUNT = 408
EXPECTED_TOTAL_ALLOCATED_BYTES = 86_922_608_640
EXPECTED_OBJECT_SET_SHA256 = "af94e8d12c075e1e5e1816de076327dd68a3fd5d5f06ec77debcbbd590bcc9ec"
EXPECTED_ORDERED_ROW_IDENTITY_SHA256 = (
    "d873d7493c6cd276a9604954c9c7aa07e760ca4f47a276658fd28956d6fa940b"
)
EVALUATION_CYCLE_ID = materializer.CYCLE007
PACK_SCHEMA_VERSION = "phase3_cycle007_storage_pack_v1"
INVENTORY_SCHEMA_VERSION = "phase3_cycle007_storage_inventory_v1"
LANE_RECEIPT_SCHEMA_VERSION = "phase3_cycle007_storage_lane_receipt_v1"
BACKUP_SCHEMA_VERSION = "phase3_cycle007_storage_backup_v1"
AUTH_SCHEMA_VERSION = "phase3_cycle007_storage_deletion_auth_request_v1"

RETAIN_MINIMAL_EVALUATION_ASSET = "RETAIN_MINIMAL_EVALUATION_ASSET"
RETIRE_CYCLE007 = "RETIRE_CYCLE007"
RETENTION_OUTCOMES = frozenset({RETAIN_MINIMAL_EVALUATION_ASSET, RETIRE_CYCLE007})
RETENTION_UNRESOLVED = "RETENTION_UNRESOLVED"
REPLACEMENT_FIREWALL_OWNER_ISSUE = 7427
MIN_FREE_BYTES = 10 * 1024 * 1024 * 1024
LINEAGE_PACK_SCHEMA_VERSION = "phase3_cycle007_storage_lineage_pack_v1"
IDENTITY_BEARING_CLASSES = frozenset(
    {
        "materialization_packet",
        "materialization_custody",
        "materialization_manifest",
        "evidence_manifest",
    }
)
CONTENT_EXPANSION_CLASSES = frozenset(
    {
        "evidence_sidecar",
        "labeling_expansion",
        "compile_expansion",
    }
)

PRIVATE_DIR_MODE = 0o700
PRIVATE_FILE_MODE = 0o600
REAL_CONFIG_ENV = "PHASE3_CYCLE007_STORAGE_CONFIG"
REAL_MATERIALIZATION_ENV = "PHASE3_CYCLE007_STORAGE_MATERIALIZATION_PACKAGE"
REAL_EVIDENCE_ENV = "PHASE3_CYCLE007_STORAGE_EVIDENCE_PACKAGE"
REAL_WORK_ENV = "PHASE3_CYCLE007_STORAGE_WORK_ROOT"
REAL_BACKUP_ENV = "PHASE3_CYCLE007_STORAGE_BACKUP_ROOT"
REAL_ZSTD_ENV = "PHASE3_CYCLE007_STORAGE_ZSTD_EXECUTABLE"
REAL_FAILURE_DOMAIN_ENV = "PHASE3_CYCLE007_STORAGE_FAILURE_DOMAIN_TOKEN"

PRIMARY_STAGE_SCHEMA_VERSION = "phase3_cycle007_storage_primary_stage_v1"
PORTABLE_EXPORT_SCHEMA_VERSION = "phase3_cycle007_storage_portable_export_v1"
BACKUP_ADMISSION_SCHEMA_VERSION = "phase3_cycle007_storage_backup_admission_v1"
BACKUP_ATTESTATION_SCHEMA_VERSION = "phase3_cycle007_storage_backup_attestation_v1"
FINALIZATION_CHALLENGE_SCHEMA_VERSION = (
    "phase3_cycle007_storage_finalization_challenge_v1"
)
FINALIZATION_RESPONSE_SCHEMA_VERSION = "phase3_cycle007_storage_finalization_response_v1"
FINALIZE_SCHEMA_VERSION = "phase3_cycle007_storage_finalize_v1"

# The no-write forecast and pack writer share this exact command line.  The
# executable itself is privately bound; only its digest/version and these safe
# settings are ever included in receipts.
ZSTD_COMPRESSION_LEVEL = 3
ZSTD_THREADS = 1
ZSTD_CHECKSUM = False
ZSTD_METADATA_ALLOWANCE_BYTES = 1024 * 1024
ZSTD_COMPRESS_ARGS = (
    "--quiet",
    "--stdout",
    "--compress",
    f"--threads={ZSTD_THREADS}",
    f"-{ZSTD_COMPRESSION_LEVEL}",
    "--no-check",
)
ZSTD_DECOMPRESS_ARGS = ("--quiet", "--stdout", "--decompress")
ZSTD_VERSION_RE = re.compile(r"\bv(\d+\.\d+(?:\.\d+)?)\b")

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

PUBLIC_SUMMARY_FORBIDDEN_FS_KEYS = frozenset(
    {
        "workstation_filesystem",
        "filesystem",
        "filesystem_avail_bytes",
        "filesystem_total_bytes",
        "filesystem_used_bytes",
        "filesystem_free_bytes",
        "filesystem_f_bavail_free_bytes",
    }
)
PUBLIC_SUMMARY_FORBIDDEN_FS_PREFIXES = ("fixture_filesystem_", "production_filesystem_", "filesystem_")


def public_summary_forbidden_fs_keys(value: Any) -> tuple[str, ...]:
    """Return forbidden host-filesystem keys found anywhere in public JSON."""
    leaked: set[str] = set()

    def visit(node: Any) -> None:
        if isinstance(node, Mapping):
            for key, child in node.items():
                key_text = str(key)
                if key_text in PUBLIC_SUMMARY_FORBIDDEN_FS_KEYS or key_text.startswith(
                    PUBLIC_SUMMARY_FORBIDDEN_FS_PREFIXES
                ):
                    leaked.add(key_text)
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(value)
    return tuple(sorted(leaked))


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
        "existing_lane_state",
        "source_mode_drift",
        "stage_state_failure",
        "staged_lane_required",
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


def _require_receipt(value: Mapping[str, Any], code: str) -> None:
    receipt_sha256 = value.get("receipt_sha256")
    _require(
        isinstance(receipt_sha256, str)
        and len(receipt_sha256) == 64
        and receipt_sha256 == _hash_receipt(value),
        code,
    )


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


def _default_fixture_zstd() -> Path:
    """Resolve a known absolute fixture executable without consulting PATH."""
    for candidate in (
        Path("/opt/homebrew/bin/zstd"),
        Path("/usr/local/bin/zstd"),
        Path("/usr/bin/zstd"),
        Path("/bin/zstd"),
    ):
        try:
            resolved = candidate.resolve(strict=True)
        except OSError:
            continue
        if resolved.is_file() and os.access(resolved, os.X_OK):
            return resolved
    raise StorageCustodyError("private_binding_unbound")


def _validate_zstd_executable(path: Path | None, code: str = "private_binding_unbound") -> Path:
    """Validate and return an absolute executable without exposing its locator."""
    _require(path is not None and path.is_absolute(), code)
    assert path is not None
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise StorageCustodyError(code) from exc
    _regular(resolved, code)
    _require(os.access(resolved, os.X_OK), code)
    return resolved


def _effective_zstd_executable(path: Path | None = None) -> Path:
    return _validate_zstd_executable(path or _default_fixture_zstd())


def _zstd_metadata(executable: Path) -> dict[str, Any]:
    """Return safe compressor identity/settings; never return path or argv."""
    executable = _validate_zstd_executable(executable)
    try:
        result = subprocess.run(
            [str(executable), "--version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise StorageCustodyError("private_binding_unbound") from exc
    version_match = ZSTD_VERSION_RE.search(result.stdout)
    _require(version_match is not None, "private_binding_unbound")
    return {
        "codec": "zstd",
        "level": ZSTD_COMPRESSION_LEVEL,
        "threads": ZSTD_THREADS,
        "checksum": ZSTD_CHECKSUM,
        "version": version_match.group(1),
        "executable_sha256": digest_file(executable),
    }


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


def _physical_inode_key(path: Path) -> tuple[int, int]:
    """Return the opaque physical identity used for allocation deduplication."""
    info = path.lstat()
    return int(info.st_dev), int(info.st_ino)


def _failure_domain_sha256(token: str) -> str:
    """Hash an operator-bound failure-domain token without recording the token.

    A hostname/device tuple is not a custody attestation: mounted remote
    storage can report the same host, and device numbers are local namespaces.
    Staged production custody therefore accepts only an explicit private token
    supplied by the operator of each failure domain.
    """
    _require(isinstance(token, str) and bool(token.strip()), "backup_restore_failure")
    return digest(b"phase3-cycle007-failure-domain-v1\0" + token.encode("utf-8"))


def _physical_failure_domain_sha256(root: Path) -> str:
    """Opaque machine/filesystem binding independent of the operator label."""
    _directory(root, "backup_restore_failure")
    machine_id_path = Path("/etc/machine-id")
    if machine_id_path.is_file():
        machine_identity = machine_id_path.read_bytes().strip()
    else:
        machine_identity = f"{socket.gethostname()}\0{uuid.getnode()}".encode()
    device = int(root.stat().st_dev)
    return digest(
        b"phase3-cycle007-physical-domain-v1\0"
        + machine_identity
        + b"\0"
        + str(device).encode()
    )


def _resolved_path_key(path: Path) -> str:
    """Identify one selected directory entry without exposing it in receipts.

    Overlapping package roots can enumerate the same directory entry through
    different role-relative names.  ``st_dev/st_ino`` groups hard links, while
    the resolved path separates genuinely distinct hard-link directory entries
    for the ``st_nlink`` closure check.
    """
    try:
        return str(path.resolve(strict=True))
    except OSError:
        # The caller already holds an lstat-able regular file.  This fallback
        # keeps inventory deterministic on filesystems that reject strict
        # resolution for a transiently changing parent.
        return str(path.absolute())


def _item_relative_paths(item: Mapping[str, Any]) -> tuple[str, ...]:
    """Return every role-relative alias represented by one physical object."""
    aliases = item.get("role_relative_paths")
    if isinstance(aliases, (list, tuple)) and aliases:
        values = tuple(str(value) for value in aliases)
        primary = item.get("role_relative_path")
        if isinstance(primary, str) and primary:
            if primary in values:
                return (primary, *(value for value in values if value != primary))
            return (primary, *values)
        return values
    primary = item.get("role_relative_path")
    return (primary,) if isinstance(primary, str) and primary else ()


def _object_set_digest(items: Sequence[Mapping[str, Any]]) -> str:
    """Commit to all logical aliases while counting each physical object once."""
    pairs: list[tuple[str, str]] = []
    for item in items:
        sha256 = item.get("sha256")
        if not isinstance(sha256, str):
            continue
        pairs.extend((rel, sha256) for rel in _item_relative_paths(item))
    pairs.sort()
    return digest("\n".join(f"{rel}\t{sha256}" for rel, sha256 in pairs).encode("utf-8"))


def _deletion_state_digest(items: Sequence[Mapping[str, Any]]) -> str:
    """Commit to the source path/inode/link state relevant to reclamation."""
    stable: list[dict[str, Any]] = []
    for item in items:
        stable.append(
            {
                "role_relative_path": item.get("role_relative_path"),
                "role_relative_paths": list(_item_relative_paths(item)),
                "selection_class": item.get("selection_class"),
                "selection_classes": sorted(item.get("selection_classes", [])),
                "sha256": item.get("sha256"),
                "size_bytes": item.get("size_bytes"),
                "allocated_bytes": item.get("allocated_bytes"),
                "mode": item.get("mode"),
                "allocation_identity": item.get("allocation_identity"),
                "selected_path_count": item.get("selected_path_count"),
                "selected_link_count": item.get("selected_link_count"),
                "link_count": item.get("link_count"),
                "external_link_count": item.get("external_link_count"),
                "link_set_closed": item.get("link_set_closed"),
            }
        )
    return digest(canonical(stable))


def _pairs_digest(pairs: Sequence[tuple[str, str]]) -> str:
    ordered = sorted((str(rel), str(sha256)) for rel, sha256 in pairs)
    return digest("\n".join(f"{rel}\t{sha256}" for rel, sha256 in ordered).encode("utf-8"))


def _link_set_closed(item: Mapping[str, Any]) -> bool:
    """Whether deleting this selected physical object can reclaim its blocks.

    ``st_nlink`` counts all directory entries for an inode, including links
    outside the selected roots.  A path alias from overlapping roots is not a
    second directory entry, so compare it with the distinct resolved paths,
    not with the number of role aliases.  Older synthetic mappings without
    link metadata remain compatible and are treated as closed.
    """
    explicit = item.get("link_set_closed")
    if isinstance(explicit, bool):
        return explicit
    link_count = item.get("link_count")
    selected_link_count = item.get("selected_link_count")
    if link_count is None or selected_link_count is None:
        return True
    try:
        return int(link_count) > 0 and int(selected_link_count) >= int(link_count)
    except (TypeError, ValueError):
        return False


@dataclass(frozen=True)
class Bindings:
    materialization_package: Path | None
    evidence_package: Path | None
    work_root: Path
    fixture: bool
    backup_root: Path | None = None
    zstd_executable: Path | None = None
    failure_domain_token: str | None = None

    @property
    def private_bound(self) -> bool:
        return self.materialization_package is not None or self.evidence_package is not None


def resolve_bindings(
    *,
    fixture: bool = False,
    materialization: Path | None = None,
    evidence: Path | None = None,
    work_root: Path | None = None,
    backup_root: Path | None = None,
    zstd_executable: Path | None = None,
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
        if backup_root is not None:
            if not backup_root.exists():
                backup_root.mkdir(parents=True, mode=PRIVATE_DIR_MODE)
            _directory(backup_root, "work_root_failure")
            os.chmod(backup_root, PRIVATE_DIR_MODE)
        fixture_zstd = _effective_zstd_executable(zstd_executable)
        return Bindings(
            materialization,
            evidence,
            work_root,
            True,
            backup_root,
            fixture_zstd,
            "fixture-primary-domain",
        )

    _require(materialization is None and evidence is None and work_root is None, "path_disclosure_refused")
    config_env = os.environ.get(REAL_CONFIG_ENV)
    mat_path: Path | None = None
    evid_path: Path | None = None
    work_path: Path | None = None
    backup_path: Path | None = None
    zstd_path: Path | None = None
    failure_domain_token: str | None = None
    if config_env:
        config_path = Path(config_env)
        _regular(config_path, "path_disclosure_refused")
        _require(stat.S_IMODE(config_path.stat().st_mode) == PRIVATE_FILE_MODE, "path_disclosure_refused")
        payload = _read_json(config_path, "path_disclosure_refused")
        _require(isinstance(payload, Mapping), "path_disclosure_refused")
        for key in (
            "materialization_package",
            "evidence_package",
            "work_root",
            "backup_root",
            "zstd_executable",
            "failure_domain_token",
        ):
            value = payload.get(key)
            if value is None:
                continue
            if key == "failure_domain_token":
                _require(isinstance(value, str) and bool(value.strip()), "path_disclosure_refused")
                failure_domain_token = value
                continue
            _require(isinstance(value, str) and value.startswith("/"), "path_disclosure_refused")
            resolved = Path(value)
            if key == "work_root":
                work_path = resolved
            elif key == "backup_root":
                backup_path = resolved
            elif key == "zstd_executable":
                zstd_path = resolved
            elif key == "materialization_package":
                mat_path = resolved
            else:
                evid_path = resolved
    mat_env = os.environ.get(REAL_MATERIALIZATION_ENV)
    evid_env = os.environ.get(REAL_EVIDENCE_ENV)
    work_env = os.environ.get(REAL_WORK_ENV)
    backup_env = os.environ.get(REAL_BACKUP_ENV)
    zstd_env = os.environ.get(REAL_ZSTD_ENV)
    if mat_env:
        _require(mat_env.startswith("/"), "path_disclosure_refused")
        mat_path = Path(mat_env)
    if evid_env:
        _require(evid_env.startswith("/"), "path_disclosure_refused")
        evid_path = Path(evid_env)
    if work_env:
        _require(work_env.startswith("/"), "path_disclosure_refused")
        work_path = Path(work_env)
    if backup_env:
        _require(backup_env.startswith("/"), "path_disclosure_refused")
        backup_path = Path(backup_env)
    if zstd_env:
        _require(zstd_env.startswith("/"), "path_disclosure_refused")
        zstd_path = Path(zstd_env)
    domain_env = os.environ.get(REAL_FAILURE_DOMAIN_ENV)
    if domain_env:
        # Tokens are intentionally accepted only from the private config.  An
        # environment override would make a staged receipt ambiguous.
        raise StorageCustodyError("path_disclosure_refused")
    _require(work_path is not None, "private_binding_unbound")
    assert work_path is not None
    if not work_path.exists():
        work_path.mkdir(parents=True, mode=PRIVATE_DIR_MODE)
    _directory(work_path, "work_root_failure")
    os.chmod(work_path, PRIVATE_DIR_MODE)
    if backup_path is not None:
        _require(backup_path.is_absolute(), "path_disclosure_refused")
        if not backup_path.exists():
            backup_path.mkdir(parents=True, mode=PRIVATE_DIR_MODE)
        _directory(backup_path, "private_binding_unbound")
        os.chmod(backup_path, PRIVATE_DIR_MODE)
    if mat_path is not None:
        _directory(mat_path, "private_binding_unbound")
        _require(stat.S_IMODE(mat_path.stat().st_mode) == PRIVATE_DIR_MODE, "source_mode_drift")
    if evid_path is not None:
        _directory(evid_path, "private_binding_unbound")
        _require(stat.S_IMODE(evid_path.stat().st_mode) == PRIVATE_DIR_MODE, "source_mode_drift")
    zstd_bound = _validate_zstd_executable(zstd_path)
    return Bindings(
        mat_path,
        evid_path,
        work_path,
        False,
        backup_path,
        zstd_bound,
        failure_domain_token,
    )


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
    roots: list[tuple[str, Path]] = []
    if bindings.materialization_package is not None:
        roots.append(("materialization", bindings.materialization_package))
    if bindings.evidence_package is not None:
        roots.append(("evidence", bindings.evidence_package))
    _require(bool(roots), "private_binding_unbound")

    # Keep all logical role aliases, but group allocation by physical inode.
    # The evidence package is sometimes nested below the materialization root;
    # in that case the same directory entry is discovered twice with different
    # role-relative names.  ``st_nlink`` alone cannot distinguish that case.
    candidates_by_inode: dict[tuple[int, int], list[dict[str, Any]]] = {}
    selected_path_count = 0
    path_sum_alloc = 0
    path_sum_size = 0
    selection_counts: dict[str, int] = {}
    for role, root in roots:
        for rel, path, selection in iter_selected_files(root, role=role):
            info = path.lstat()
            key = _physical_inode_key(path)
            size = int(info.st_size)
            alloc = allocated_bytes(path)
            candidate = {
                "role_relative_path": rel,
                "path": path,
                "selection_class": selection,
                "size_bytes": size,
                "allocated_bytes": alloc,
                "mode": stat.S_IMODE(info.st_mode),
                "resolved_path": _resolved_path_key(path),
                "st_nlink": int(getattr(info, "st_nlink", 1)),
            }
            candidates_by_inode.setdefault(key, []).append(candidate)
            selected_path_count += 1
            path_sum_alloc += alloc
            path_sum_size += size
            selection_counts[selection] = selection_counts.get(selection, 0) + 1

    selection_priority = {
        "materialization_packet": 0,
        "materialization_custody": 1,
        "materialization_manifest": 2,
        "evidence_sidecar": 3,
        "evidence_manifest": 4,
        "labeling_expansion": 5,
        "compile_expansion": 6,
    }
    objects: list[dict[str, Any]] = []
    row_identities: list[tuple[str, str]] = []
    # The sums above intentionally use path counts, not unique inode counts.
    packet_files = selection_counts.get("materialization_packet", 0)
    sidecar_files = selection_counts.get("evidence_sidecar", 0)
    total_alloc = 0
    total_size = 0
    fully_closed_reclaimable = 0
    external_link_inode_count = 0
    has_materialization_packets = packet_files > 0

    for inode_key, candidates in candidates_by_inode.items():
        candidates.sort(
            key=lambda candidate: (
                selection_priority.get(str(candidate["selection_class"]), 99),
                str(candidate["role_relative_path"]),
            )
        )
        primary = candidates[0]
        primary_path = primary["path"]
        raw_sha256 = digest_file(primary_path)
        size = int(primary["size_bytes"])
        alloc = int(primary["allocated_bytes"])
        aliases = sorted(str(candidate["role_relative_path"]) for candidate in candidates)
        selected_links = {str(candidate["resolved_path"]) for candidate in candidates}
        link_count = int(primary["st_nlink"])
        selected_link_count = len(selected_links)
        link_set_closed = link_count > 0 and selected_link_count >= link_count
        external_link_count = max(link_count - selected_link_count, 0)
        if external_link_count:
            external_link_inode_count += 1
        total_alloc += alloc
        total_size += size
        if link_set_closed:
            fully_closed_reclaimable += alloc

        entry: dict[str, Any] = {
            "role_relative_path": aliases[0],
            "role_relative_paths": aliases,
            "selection_class": primary["selection_class"],
            "selection_classes": sorted(
                {str(candidate["selection_class"]) for candidate in candidates}
            ),
            "sha256": raw_sha256,
            "size_bytes": size,
            "path_size_bytes": size * len(candidates),
            "allocated_bytes": alloc,
            "path_allocated_bytes": alloc * len(candidates),
            "mode": int(primary["mode"]),
            "fs": {"dev": int(inode_key[0]), "ino": int(inode_key[1])},
            "allocation_identity": {"dev": int(inode_key[0]), "ino": int(inode_key[1])},
            "selected_path_count": len(candidates),
            "selected_link_count": selected_link_count,
            "link_count": link_count,
            "external_link_count": external_link_count,
            "link_set_closed": link_set_closed,
        }

        class_to_candidate = {
            str(candidate["selection_class"]): candidate for candidate in candidates
        }
        packet_candidate = class_to_candidate.get("materialization_packet")
        sidecar_candidate = class_to_candidate.get("evidence_sidecar")
        if packet_candidate is not None:
            count, identities = _identity_fields_from_packet(packet_candidate["path"])
            entry["row_count"] = count
            entry["packet_identity_set_sha256"] = materializer.identity_set(
                [{"unit_id": u, "unit_sha256": s} for u, s in identities]
            )
            row_identities.extend(identities)
        elif sidecar_candidate is not None:
            meta = _sidecar_identity(sidecar_candidate["path"])
            entry["sidecar_id"] = meta["sidecar_id"]
            entry["packet_index"] = meta["packet_index"]
            entry["row_count"] = meta["row_count"]
            entry["lane"] = meta["lane"]
            entry["packet_raw_sha256"] = meta["packet_raw_sha256"]
            entry["packet_identity_set_sha256"] = meta["packet_identity_set_sha256"]
            if not has_materialization_packets:
                row_identities.extend(meta["row_identities"])
        objects.append(entry)

    objects.sort(key=lambda item: item["role_relative_path"])
    ordered_identity_commitment = digest(
        "\n".join(f"{unit_id}\t{unit_sha256}" for unit_id, unit_sha256 in row_identities).encode("utf-8")
    )
    object_set_sha256 = _object_set_digest(objects)
    deletion_state_sha256 = _deletion_state_digest(objects)

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
        _require(
            bindings.materialization_package is not None
            and bindings.evidence_package is not None,
            "denominator_drift",
        )
        _require(packet_count == EXPECTED_PACKET_COUNT, "denominator_drift")
        _require(row_count == EXPECTED_ROW_COUNT, "denominator_drift")
        _require(selected_path_count == EXPECTED_SELECTED_PATH_COUNT, "denominator_drift")
        _require(len(objects) == EXPECTED_UNIQUE_INODE_COUNT, "denominator_drift")
        _require(
            selected_path_count - len(objects) == EXPECTED_DUPLICATE_SELECTED_LINK_COUNT,
            "denominator_drift",
        )
        _require(packet_files == EXPECTED_PACKET_COUNT, "denominator_drift")
        _require(
            sidecar_files == EXPECTED_LOGICAL_SIDECAR_SELECTION_COUNT,
            "denominator_drift",
        )
        physical_sidecars = sum(
            1
            for item in objects
            if "evidence_sidecar"
            in item.get("selection_classes", [item["selection_class"]])
        )
        _require(
            physical_sidecars == EXPECTED_PHYSICAL_SIDECAR_COUNT,
            "denominator_drift",
        )
        _require(external_link_inode_count == 0, "denominator_drift")
        _require(fully_closed_reclaimable == total_alloc, "denominator_drift")
        _require(total_alloc == EXPECTED_TOTAL_ALLOCATED_BYTES, "denominator_drift")
        _require(object_set_sha256 == EXPECTED_OBJECT_SET_SHA256, "denominator_drift")
        _require(
            ordered_identity_commitment == EXPECTED_ORDERED_ROW_IDENTITY_SHA256,
            "denominator_drift",
        )

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
            "path_sum_size_bytes": path_sum_size,
            "unique_logical_bytes": total_size,
            "total_allocated_bytes": total_alloc,
            "path_sum_allocated_bytes": path_sum_alloc,
            "selected_path_count": selected_path_count,
            "unique_inode_count": len(objects),
            "duplicate_selected_link_count": selected_path_count - len(objects),
            "fully_closed_reclaimable_bytes": fully_closed_reclaimable,
            "external_link_inode_count": external_link_inode_count,
            "ordered_row_identity_commitment_sha256": ordered_identity_commitment,
            "object_set_sha256": object_set_sha256,
            "deletion_state_sha256": deletion_state_sha256,
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


def evaluate_held_out_proof(proof: Mapping[str, Any] | None) -> dict[str, Any]:
    """Adversarial gate for RETAIN_MINIMAL_EVALUATION_ASSET.

    Identity-lineage exclusion alone is insufficient. Text-free source/rights/
    adjudication metadata must prove a concrete source-qualified held-out
    evaluation function, required fields/identities, and a named consumer.
    """
    questions = {
        "q1_concrete_source_qualified_held_out_function": False,
        "q2_required_fields_and_identities_present": False,
        "q3_named_consumer_present": False,
        "q4_identity_lineage_exclusion_alone_insufficient": True,
        "q5_text_free_source_rights_adjudication_metadata_present": False,
        "q6_replacement_firewall_owner_issue": REPLACEMENT_FIREWALL_OWNER_ISSUE,
    }
    if not isinstance(proof, Mapping):
        return {
            "proof_valid": False,
            "questions": questions,
            "failure_reason": "held_out_evaluation_proof_absent",
        }
    function_id = proof.get("held_out_evaluation_function_id")
    required_fields = proof.get("required_fields")
    required_identities = proof.get("required_identities")
    consumer = proof.get("named_consumer")
    source_qualified = proof.get("source_qualified") is True
    text_free_meta = proof.get("text_free_source_rights_adjudication_metadata") is True
    questions["q1_concrete_source_qualified_held_out_function"] = bool(
        isinstance(function_id, str)
        and function_id.strip()
        and source_qualified
    )
    questions["q2_required_fields_and_identities_present"] = bool(
        isinstance(required_fields, list)
        and len(required_fields) > 0
        and all(isinstance(item, str) and item for item in required_fields)
        and isinstance(required_identities, list)
        and len(required_identities) > 0
        and all(isinstance(item, str) and item for item in required_identities)
    )
    questions["q3_named_consumer_present"] = bool(isinstance(consumer, str) and consumer.strip())
    questions["q5_text_free_source_rights_adjudication_metadata_present"] = bool(text_free_meta)
    # q4 remains True: lineage exclusion never upgrades to RETAIN on its own.
    proof_valid = all(
        (
            questions["q1_concrete_source_qualified_held_out_function"],
            questions["q2_required_fields_and_identities_present"],
            questions["q3_named_consumer_present"],
            questions["q5_text_free_source_rights_adjudication_metadata_present"],
        )
    )
    return {
        "proof_valid": proof_valid,
        "questions": questions,
        "failure_reason": None if proof_valid else "held_out_evaluation_proof_incomplete",
    }


def decide_retention(
    *,
    inventory: Mapping[str, Any],
    labeling_state: str = "OFF",
    provider_calls: int = 0,
    provider_derived_training_labels: int = 0,
    held_out_evaluation_proof: Mapping[str, Any] | None = None,
    evaluation_firewall_requires_cycle007_identities: bool | None = None,
) -> dict[str, Any]:
    """Return a retention decision without treating missing proof as retirement.

    A missing or incomplete held-out proof leaves retention unresolved.  The
    storage lane must not turn an evaluation gap into a destructive-looking
    ``RETIRE_CYCLE007`` disposition; that outcome requires a separately
    reconciled, source-qualified decision owned by the evaluation firewall.
    """
    _require(labeling_state == "OFF", "retention_blocked")
    _require(provider_calls == 0, "retention_blocked")
    _require(provider_derived_training_labels == 0, "retention_blocked")
    packet_count = inventory.get("packet_count")
    row_count = inventory.get("row_count")
    object_count = inventory.get("object_count")
    _require(isinstance(packet_count, int) and packet_count > 0, "retention_blocked")
    _require(isinstance(row_count, int) and row_count > 0, "retention_blocked")
    _require(isinstance(object_count, int) and object_count > 0, "retention_blocked")

    proof = evaluate_held_out_proof(held_out_evaluation_proof)
    # Legacy boolean alone is treated as lineage-exclusion claim, not proof.
    lineage_only_claim = bool(evaluation_firewall_requires_cycle007_identities)
    if proof["proof_valid"]:
        outcome = RETAIN_MINIMAL_EVALUATION_ASSET
        rationale_code = "held_out_evaluation_function_proven"
        retention_final = True
        retention_status = RETAIN_MINIMAL_EVALUATION_ASSET
    else:
        outcome = None
        rationale_code = "held_out_evaluation_reconciliation_pending"
        retention_final = False
        retention_status = RETENTION_UNRESOLVED

    return _receipt(
        {
            "schema_version": "phase3_cycle007_storage_retention_decision_v1",
            "outcome_sha256": OUTCOME_SHA256,
            "retention_outcome": outcome,
            "retention_status": retention_status,
            "retention_final": retention_final,
            "retention_reconciliation_required": not retention_final,
            "rationale_code": rationale_code,
            "labeling_state": labeling_state,
            "provider_calls": provider_calls,
            "provider_derived_training_labels": provider_derived_training_labels,
            "evaluation_firewall_requires_cycle007_identities": lineage_only_claim,
            "held_out_evaluation_proof_valid": proof["proof_valid"],
            "held_out_evaluation_proof_failure_reason": proof["failure_reason"],
            "retention_questions": proof["questions"],
            "replacement_firewall_owner_issue": (
                None if outcome == RETAIN_MINIMAL_EVALUATION_ASSET else REPLACEMENT_FIREWALL_OWNER_ISSUE
            ),
            "preserves_only_non_content_lineage_hashes": False,
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
    destination_avail_bytes: int,
    backup_destination_avail_bytes: int | None = None,
    min_free_bytes: int = MIN_FREE_BYTES,
    backup_min_free_bytes: int | None = None,
    second_expanded_tree: bool = False,
) -> dict[str, Any]:
    allocated = int(inventory["total_allocated_bytes"])
    path_sum_allocated = int(
        inventory.get("path_sum_allocated_bytes", inventory["total_allocated_bytes"])
    )
    _require(allocated >= 0 and path_sum_allocated >= allocated, "inventory_shape_failure")
    _require(compact_stored_bytes >= 0 and backup_stored_bytes >= 0, "inventory_shape_failure")
    # Reversible peaks while originals remain untouched. A second expanded tree
    # is forbidden on the custody lane; streaming identity proof replaces it.
    # When backup has its own filesystem, the pack and backup peaks cannot be
    # added together: each destination sees only the bytes written there.
    separate_filesystems = backup_destination_avail_bytes is not None
    backup_floor = min_free_bytes if backup_min_free_bytes is None else backup_min_free_bytes
    peak_compact = compact_stored_bytes
    peak_backup = (
        backup_stored_bytes
        if separate_filesystems
        else compact_stored_bytes + backup_stored_bytes
    )
    peak_hash_index = (
        max(compact_stored_bytes, backup_stored_bytes)
        if separate_filesystems
        else compact_stored_bytes + backup_stored_bytes
    )
    peak = max(peak_compact, peak_backup, peak_hash_index)
    second_expanded_tree_bytes = 0
    compact_peak_for_capacity = peak_compact
    backup_peak_for_capacity = peak_backup
    if second_expanded_tree:
        # If a caller explicitly models the forbidden path, use the unique
        # physical allocation exactly once.  The previous formula added the
        # path-summed allocation twice and overstated the peak for aliases.
        second_expanded_tree_bytes = allocated
        if separate_filesystems:
            compact_peak_for_capacity = allocated + compact_stored_bytes
            backup_peak_for_capacity = backup_stored_bytes
        else:
            compact_peak_for_capacity = allocated + compact_stored_bytes + backup_stored_bytes
            backup_peak_for_capacity = compact_peak_for_capacity
        peak = max(peak, compact_peak_for_capacity, backup_peak_for_capacity)
    compact_remaining = destination_avail_bytes - compact_peak_for_capacity
    backup_avail = destination_avail_bytes if backup_destination_avail_bytes is None else backup_destination_avail_bytes
    backup_remaining = backup_avail - backup_peak_for_capacity
    remaining_after_peak = min(compact_remaining, backup_remaining)
    compact_capacity_sufficient = compact_remaining >= min_free_bytes
    backup_capacity_sufficient = backup_remaining >= backup_floor
    return _receipt(
        {
            "schema_version": "phase3_cycle007_storage_peak_forecast_v1",
            "outcome_sha256": OUTCOME_SHA256,
            "original_allocated_bytes": allocated,
            "path_sum_allocated_bytes": path_sum_allocated,
            "duplicate_selected_link_allocated_bytes": path_sum_allocated - allocated,
            "compact_stored_bytes": compact_stored_bytes,
            "backup_stored_bytes": backup_stored_bytes,
            "second_expanded_tree_bytes": second_expanded_tree_bytes,
            "peak_temporary_bytes": peak,
            "peak_compact_bytes": peak_compact,
            "peak_backup_bytes": peak_backup,
            "peak_hash_index_bytes": peak_hash_index,
            "compact_peak_for_capacity_bytes": compact_peak_for_capacity,
            "backup_peak_for_capacity_bytes": backup_peak_for_capacity,
            "destination_avail_bytes": destination_avail_bytes,
            "backup_destination_avail_bytes": backup_destination_avail_bytes,
            "separate_filesystems": separate_filesystems,
            "min_free_bytes": min_free_bytes,
            "backup_min_free_bytes": backup_floor,
            "compact_remaining_after_peak_bytes": compact_remaining,
            "backup_remaining_after_peak_bytes": backup_remaining,
            "remaining_after_peak_bytes": remaining_after_peak,
            "compact_capacity_sufficient": compact_capacity_sufficient,
            "backup_capacity_sufficient": backup_capacity_sufficient,
            "capacity_sufficient_for_peak": compact_capacity_sufficient and backup_capacity_sufficient,
            "second_expanded_tree": second_expanded_tree,
            "inventory_receipt_sha256": inventory.get("receipt_sha256"),
        }
    )


def _store_object_bytes(raw: bytes) -> tuple[str, bytes, int]:
    compressed = lzma.compress(raw, preset=6)
    if len(compressed) + 64 < len(raw):
        return "lzma", compressed, len(compressed)
    return "raw", raw, len(raw)


def _atomic_write_stream(
    path: Path,
    chunks: Iterator[bytes],
    *,
    mode: int = PRIVATE_FILE_MODE,
) -> tuple[str, int]:
    """Atomically write a byte stream while hashing it, without buffering it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, PRIVATE_DIR_MODE)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    hasher = hashlib.sha256()
    size = 0
    try:
        with os.fdopen(fd, "wb") as handle:
            for chunk in chunks:
                if not isinstance(chunk, bytes):
                    raise StorageCustodyError("pack_shape_failure")
                handle.write(chunk)
                hasher.update(chunk)
                size += len(chunk)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp_path, mode)
        os.replace(tmp_path, path)
        dir_fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except OSError as exc:
        if exc.errno == errno.ENOSPC:
            raise StorageCustodyError("capacity_insufficient") from exc
        raise StorageCustodyError("pack_shape_failure") from exc
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
    return hasher.hexdigest(), size


def _iter_file_chunks(path: Path) -> Iterator[bytes]:
    with path.open("rb") as handle:
        yield from iter(lambda: handle.read(1024 * 1024), b"")


def _iter_stored_raw_chunks(
    path: Path,
    storage: str,
    zstd_executable: Path | None = None,
) -> Iterator[bytes]:
    if storage == "raw":
        yield from _iter_file_chunks(path)
        return
    if storage == "lzma":
        try:
            with lzma.open(path, "rb") as handle:
                yield from iter(lambda: handle.read(1024 * 1024), b"")
        except (OSError, lzma.LZMAError) as exc:
            raise StorageCustodyError("identity_roundtrip_failure") from exc
        return
    if storage != "zstd":
        raise StorageCustodyError("pack_shape_failure")
    executable = _effective_zstd_executable(zstd_executable)
    process: subprocess.Popen[bytes] | None = None
    try:
        with path.open("rb") as source:
            process = subprocess.Popen(
                [str(executable), *ZSTD_DECOMPRESS_ARGS],
                stdin=source,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            assert process.stdout is not None
            yield from iter(lambda: process.stdout.read(1024 * 1024), b"")
            return_code = process.wait()
        if return_code != 0:
            raise StorageCustodyError("identity_roundtrip_failure")
    except (OSError, subprocess.SubprocessError) as exc:
        raise StorageCustodyError("identity_roundtrip_failure") from exc
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()


def _compress_source_stream(
    source: Path,
    executable: Path,
    *,
    output_path: Path | None = None,
) -> tuple[str, int, str, int]:
    """Compress one source by streaming through pinned zstd.

    The optional output path is a private temporary file used by the pack
    writer.  With no output path, stdout is drained and hashed only, which is
    the exact no-write preflight operation.  The reader thread is required to
    prevent a large zstd frame from filling the subprocess pipe while stdin is
    still being fed.
    """
    _regular(source, "identity_roundtrip_failure")
    executable = _validate_zstd_executable(executable)
    raw_hasher = hashlib.sha256()
    compressed_hasher = hashlib.sha256()
    raw_size = 0
    compressed_size = 0
    output_error: list[BaseException] = []
    output_failed = threading.Event()
    process: subprocess.Popen[bytes] | None = None
    output_handle = None
    reader: threading.Thread | None = None

    try:
        process = subprocess.Popen(
            [str(executable), *ZSTD_COMPRESS_ARGS],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        assert process.stdin is not None and process.stdout is not None
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            os.chmod(output_path.parent, PRIVATE_DIR_MODE)
            output_handle = output_path.open("wb")

        def consume_output() -> None:
            nonlocal compressed_size
            try:
                while True:
                    chunk = process.stdout.read(1024 * 1024)
                    if not chunk:
                        break
                    compressed_hasher.update(chunk)
                    compressed_size += len(chunk)
                    if output_handle is not None:
                        output_handle.write(chunk)
            except BaseException as exc:  # propagate through the owner thread
                output_error.append(exc)
                output_failed.set()
                # If the destination write failed (including ENOSPC), stop
                # zstd immediately.  Otherwise the owner can block writing
                # stdin while this reader has exited and zstd is blocked on a
                # full stdout pipe.
                if process is not None and process.poll() is None:
                    with contextlib.suppress(OSError):
                        process.terminate()

        reader = threading.Thread(target=consume_output, name="cycle007-zstd-reader")
        reader.start()
        with source.open("rb") as source_handle:
            for chunk in iter(lambda: source_handle.read(1024 * 1024), b""):
                if output_failed.is_set():
                    break
                raw_hasher.update(chunk)
                raw_size += len(chunk)
                process.stdin.write(chunk)
        if output_failed.is_set():
            if isinstance(output_error[0], OSError) and output_error[0].errno == errno.ENOSPC:
                raise StorageCustodyError("capacity_insufficient") from output_error[0]
            raise StorageCustodyError("pack_shape_failure") from output_error[0]
        process.stdin.close()
        return_code = process.wait()
        reader.join()
        if output_error:
            if isinstance(output_error[0], OSError) and output_error[0].errno == errno.ENOSPC:
                raise StorageCustodyError("capacity_insufficient") from output_error[0]
            raise StorageCustodyError("pack_shape_failure") from output_error[0]
        if output_handle is not None:
            output_handle.flush()
            os.fsync(output_handle.fileno())
        if return_code != 0:
            raise StorageCustodyError("pack_shape_failure")
    except OSError as exc:
        if exc.errno == errno.ENOSPC:
            raise StorageCustodyError("capacity_insufficient") from exc
        raise StorageCustodyError("pack_shape_failure") from exc
    except (BrokenPipeError, subprocess.SubprocessError) as exc:
        raise StorageCustodyError("pack_shape_failure") from exc
    finally:
        if process is not None:
            if process.stdin is not None and not process.stdin.closed:
                process.stdin.close()
            if process.poll() is None:
                process.kill()
                process.wait()
        if reader is not None:
            reader.join()
        if output_handle is not None:
            output_handle.close()
    return raw_hasher.hexdigest(), raw_size, compressed_hasher.hexdigest(), compressed_size


def _stream_digest_chunks(chunks: Iterator[bytes]) -> tuple[str, int]:
    hasher = hashlib.sha256()
    size = 0
    for chunk in chunks:
        if not isinstance(chunk, bytes):
            raise StorageCustodyError("identity_roundtrip_failure")
        hasher.update(chunk)
        size += len(chunk)
    return hasher.hexdigest(), size


def _stream_object_to_pack(
    source: Path,
    object_path_base: Path,
    *,
    expected_sha256: str,
    zstd_executable: Path | None = None,
) -> tuple[str, Path, str, int]:
    """Write one unique source inode as one content-addressed physical blob.

    Pinned zstd is fed incrementally and admitted only when it is smaller than
    the exact logical-size upper bound.  If it is not smaller, the compressed
    candidate is removed before the raw stream is atomically written.  This
    keeps the operation bounded to one source file plus one candidate blob and
    never materializes a second expanded tree.
    """
    object_path_base.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(object_path_base.parent, PRIVATE_DIR_MODE)
    source_size = int(source.stat().st_size)
    compressed_fd, compressed_tmp_name = tempfile.mkstemp(
        prefix=f".{object_path_base.name}.", dir=str(object_path_base.parent)
    )
    os.close(compressed_fd)
    compressed_tmp = Path(compressed_tmp_name)
    try:
        executable = _effective_zstd_executable(zstd_executable)
        raw_sha256, raw_size, compressed_sha256, compressed_size = _compress_source_stream(
            source,
            executable,
            output_path=compressed_tmp,
        )
        _require(raw_sha256 == expected_sha256, "identity_roundtrip_failure")
        _require(raw_size == source_size, "identity_roundtrip_failure")
        if compressed_size + 64 < source_size:
            object_path = object_path_base.with_suffix(".zst")
            if object_path.exists():
                compressed_tmp.unlink(missing_ok=True)
                _regular(object_path, "pack_shape_failure")
                stored_sha256 = digest_file(object_path)
                _require(stored_sha256 == compressed_sha256, "identity_roundtrip_failure")
                return "zstd", object_path, stored_sha256, int(object_path.stat().st_size)
            os.chmod(compressed_tmp, PRIVATE_FILE_MODE)
            os.replace(compressed_tmp, object_path)
            dir_fd = os.open(str(object_path.parent), os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
            return "zstd", object_path, compressed_sha256, compressed_size

        compressed_tmp.unlink(missing_ok=True)
        object_path = object_path_base.with_suffix(".raw")
        if object_path.exists():
            _regular(object_path, "pack_shape_failure")
            stored_sha256 = digest_file(object_path)
            _require(stored_sha256 == expected_sha256, "identity_roundtrip_failure")
            return "raw", object_path, stored_sha256, int(object_path.stat().st_size)

        def raw_chunks() -> Iterator[bytes]:
            with source.open("rb") as source_handle:
                yield from iter(lambda: source_handle.read(1024 * 1024), b"")

        stored_sha256, stored_size = _atomic_write_stream(object_path, raw_chunks())
        _require(stored_sha256 == expected_sha256, "identity_roundtrip_failure")
        return "raw", object_path, stored_sha256, stored_size
    finally:
        compressed_tmp.unlink(missing_ok=True)


def write_lineage_pack(inventory: Mapping[str, Any], pack_dir: Path) -> dict[str, Any]:
    """RETIRE path: store only text-free identity/lineage hashes (no content bodies)."""
    if pack_dir.exists():
        raise StorageCustodyError("pack_shape_failure")
    pack_dir.mkdir(mode=PRIVATE_DIR_MODE)
    os.chmod(pack_dir, PRIVATE_DIR_MODE)
    lineage_objects: list[dict[str, Any]] = []
    for item in inventory["objects"]:
        entry = {
            "role_relative_path": item["role_relative_path"],
            "role_relative_paths": list(_item_relative_paths(item)),
            "selection_class": item["selection_class"],
            "selection_classes": item.get("selection_classes", [item["selection_class"]]),
            "sha256": item["sha256"],
            "size_bytes": item["size_bytes"],
            "allocated_bytes": item["allocated_bytes"],
            "selected_path_count": item.get("selected_path_count", 1),
            "selected_link_count": item.get("selected_link_count", 1),
            "link_count": item.get("link_count", 1),
            "external_link_count": item.get("external_link_count", 0),
            "link_set_closed": _link_set_closed(item),
            "mode": item["mode"],
            "packet_identity_set_sha256": item.get("packet_identity_set_sha256"),
            "sidecar_id": item.get("sidecar_id"),
            "row_count": item.get("row_count"),
            "packet_index": item.get("packet_index"),
            "lane": item.get("lane"),
            "content_retained": False,
        }
        lineage_objects.append(entry)
    body = {
        "schema_version": LINEAGE_PACK_SCHEMA_VERSION,
        "outcome_sha256": OUTCOME_SHA256,
        "evaluation_cycle_id": EVALUATION_CYCLE_ID,
        "pack_kind": "non_content_lineage_hashes",
        "fixture": inventory.get("fixture", False),
        "packet_count": inventory["packet_count"],
        "row_count": inventory["row_count"],
        "object_count": len(lineage_objects),
        "ordered_row_identity_commitment_sha256": inventory[
            "ordered_row_identity_commitment_sha256"
        ],
        "object_set_sha256": inventory["object_set_sha256"],
        "inventory_receipt_sha256": inventory["receipt_sha256"],
        "total_original_allocated_bytes": inventory["total_allocated_bytes"],
        "objects": lineage_objects,
        "replacement_firewall_owner_issue": REPLACEMENT_FIREWALL_OWNER_ISSUE,
    }
    pack_manifest = _receipt(body)
    _atomic_write_json(pack_dir / "pack-manifest.json", pack_manifest)
    # Store a second durable copy of the object digest set only.
    digest_pairs = [
        (rel, str(item["sha256"]))
        for item in lineage_objects
        for rel in _item_relative_paths(item)
    ]
    digest_blob = ("\n".join(
        f"{rel}\t{sha256}" for rel, sha256 in sorted(digest_pairs)
    ) + "\n").encode("utf-8")
    stored_alloc = allocated_bytes(pack_dir / "pack-manifest.json")
    digest_path = pack_dir / "object-digest-set.txt"
    _atomic_write(digest_path, digest_blob)
    stored_alloc += allocated_bytes(digest_path)
    pack_manifest = _receipt(
        {
            **{k: v for k, v in pack_manifest.items() if k != "receipt_sha256"},
            "total_stored_allocated_bytes": stored_alloc,
            "content_bodies_stored": False,
        }
    )
    _atomic_write_json(pack_dir / "pack-manifest.json", pack_manifest)
    return pack_manifest


def prove_lineage_against_sources(
    inventory: Mapping[str, Any],
    bindings: Bindings,
    pack_manifest: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Exact identity proof without creating a second expanded tree."""
    _require(pack_manifest.get("schema_version") == LINEAGE_PACK_SCHEMA_VERSION, "pack_shape_failure")
    path_index = _path_index(bindings)
    verified: list[tuple[str, str]] = []
    digest_cache: dict[tuple[int, int], str] = {}
    pack_by_rel = {
        rel: entry
        for entry in pack_manifest["objects"]
        for rel in _item_relative_paths(entry)
    }
    for item in inventory["objects"]:
        for rel in _item_relative_paths(item):
            source = path_index[rel]
            _regular(source, "identity_roundtrip_failure")
            inode_key = _physical_inode_key(source)
            sha = digest_cache.get(inode_key)
            if sha is None:
                sha = digest_file(source)
                digest_cache[inode_key] = sha
            _require(sha == item["sha256"], "identity_roundtrip_failure")
            _require(rel in pack_by_rel, "identity_roundtrip_failure")
            _require(sha == pack_by_rel[rel]["sha256"], "identity_roundtrip_failure")
            verified.append((rel, sha))
    object_set = _pairs_digest(verified)
    _require(object_set == inventory["object_set_sha256"], "identity_roundtrip_failure")
    _require(object_set == pack_manifest["object_set_sha256"], "identity_roundtrip_failure")
    roundtrip = _receipt(
        {
            "schema_version": "phase3_cycle007_storage_roundtrip_v1",
            "outcome_sha256": OUTCOME_SHA256,
            "pack_manifest_sha256": pack_manifest["receipt_sha256"],
            "object_count": len(inventory["objects"]),
            "object_set_sha256": object_set,
            "ordered_row_identity_commitment_sha256": inventory[
                "ordered_row_identity_commitment_sha256"
            ],
            "packet_count": inventory["packet_count"],
            "row_count": inventory["row_count"],
            "roundtrip_ok": True,
            "second_expanded_tree": False,
            "proof_mode": "stream_hash_against_sources",
        }
    )
    identity_proof = _receipt(
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
            "second_expanded_tree": False,
            "proof_mode": "stream_hash_against_sources",
        }
    )
    return roundtrip, identity_proof


def prove_backup_byte_identity(pack_dir: Path, backup_dir: Path) -> dict[str, Any]:
    """Prove backup restores to the compact/lineage pack without expanding content."""
    _directory(pack_dir, "backup_restore_failure")
    _directory(backup_dir, "backup_restore_failure")
    pack_files: dict[str, str] = {}
    for dirpath, _dirnames, filenames in os.walk(pack_dir, followlinks=False):
        for filename in sorted(filenames):
            path = Path(dirpath) / filename
            if path.is_symlink() or not path.is_file():
                continue
            rel = path.relative_to(pack_dir).as_posix()
            pack_files[rel] = digest_file(path)
    backup_files: dict[str, str] = {}
    for dirpath, _dirnames, filenames in os.walk(backup_dir, followlinks=False):
        for filename in sorted(filenames):
            path = Path(dirpath) / filename
            if path.is_symlink() or not path.is_file():
                continue
            rel = path.relative_to(backup_dir).as_posix()
            backup_files[rel] = digest_file(path)
    _require(pack_files == backup_files, "backup_restore_failure")
    manifest = _read_json(backup_dir / "pack-manifest.json", "backup_restore_failure")
    return _receipt(
        {
            "schema_version": "phase3_cycle007_storage_backup_restore_proof_v1",
            "outcome_sha256": OUTCOME_SHA256,
            "pack_manifest_sha256": manifest["receipt_sha256"],
            "object_set_sha256": manifest.get("object_set_sha256"),
            "object_count": manifest.get("object_count"),
            "packet_count": manifest.get("packet_count"),
            "row_count": manifest.get("row_count"),
            "backup_restore_ok": True,
            "second_expanded_tree": False,
            "proof_mode": "byte_identity_pack_to_backup",
        }
    )


def estimate_content_pack_bytes(inventory: Mapping[str, Any]) -> int:
    """Exact no-write full-size upper bound for a content pack.

    Capacity admission never relies on observed compression ratios.  Every
    unique physical source object is allowed to remain raw, with a bounded
    manifest/index allowance.  Overlapping roots and hard-link aliases are
    therefore counted once in the forecast.
    """
    unique_size = inventory.get("unique_logical_bytes", inventory.get("total_size_bytes"))
    _require(isinstance(unique_size, int) and unique_size >= 0, "inventory_shape_failure")
    # One MiB covers the manifest and digest index for the current packet
    # denominator while remaining deliberately independent of compression.
    return int(unique_size) + ZSTD_METADATA_ALLOWANCE_BYTES


def _round_allocated(size: int, allocation_unit: int) -> int:
    _require(size >= 0 and allocation_unit > 0, "inventory_shape_failure")
    return ((size + allocation_unit - 1) // allocation_unit) * allocation_unit


def forecast_zstd_content_pack_bytes(
    inventory: Mapping[str, Any],
    bindings: Bindings,
) -> dict[str, Any]:
    """Measure the exact pinned-zstd payload without creating pack files.

    Each content hash is compressed once through the same streaming helper used
    by :func:`write_pack`.  Only byte counts/hashes are retained; no compressed
    candidate is written to disk.  The metadata allowance remains conservative
    because the final receipt contains the measured payload sizes themselves.
    """
    executable = _effective_zstd_executable(bindings.zstd_executable)
    compression = _zstd_metadata(executable)
    path_index = _path_index(bindings)
    sources_by_sha: dict[str, tuple[Path, int]] = {}
    for item in inventory["objects"]:
        sha256 = item.get("sha256")
        rel = item.get("role_relative_path")
        _require(isinstance(sha256, str) and len(sha256) == 64, "inventory_shape_failure")
        _require(isinstance(rel, str) and rel in path_index, "inventory_shape_failure")
        source = path_index[rel]
        size = int(item.get("size_bytes", source.stat().st_size))
        existing = sources_by_sha.get(sha256)
        if existing is None:
            sources_by_sha[sha256] = (source, size)
        else:
            _require(existing[1] == size, "identity_roundtrip_failure")

    allocation_unit = int(os.statvfs(bindings.work_root).f_frsize)
    backup_root = bindings.backup_root or bindings.work_root
    backup_allocation_unit = int(os.statvfs(backup_root).f_frsize)
    stored_payload_bytes = 0
    stored_payload_allocated_bytes = 0
    backup_payload_allocated_bytes = 0
    temporary_candidate_overhead_bytes = 0
    unique_logical_bytes = 0
    stored_entries: list[dict[str, Any]] = []
    for sha256 in sorted(sources_by_sha):
        source, source_size = sources_by_sha[sha256]
        raw_sha256, raw_size, compressed_sha256, compressed_size = _compress_source_stream(
            source,
            executable,
        )
        _require(raw_sha256 == sha256, "identity_roundtrip_failure")
        _require(raw_size == source_size, "identity_roundtrip_failure")
        use_compressed = compressed_size + 64 < source_size
        storage = "zstd" if use_compressed else "raw"
        stored_size = compressed_size if use_compressed else source_size
        stored_sha256 = compressed_sha256 if use_compressed else raw_sha256
        stored_allocated = _round_allocated(stored_size, allocation_unit)
        compressed_allocated = _round_allocated(compressed_size, allocation_unit)
        temporary_candidate_overhead_bytes = max(
            temporary_candidate_overhead_bytes,
            max(compressed_allocated - stored_allocated, 0),
        )
        stored_payload_bytes += stored_size
        stored_payload_allocated_bytes += stored_allocated
        backup_payload_allocated_bytes += _round_allocated(stored_size, backup_allocation_unit)
        unique_logical_bytes += source_size
        stored_entries.append(
            {
                "sha256": sha256,
                "storage": storage,
                "stored_sha256": stored_sha256,
                "stored_size_bytes": stored_size,
            }
        )
    metadata_allowance = ZSTD_METADATA_ALLOWANCE_BYTES
    full_size = unique_logical_bytes + metadata_allowance
    stored_payload_digest = digest(canonical(stored_entries))
    return _receipt(
        {
            "schema_version": "phase3_cycle007_storage_content_pack_forecast_v1",
            "outcome_sha256": OUTCOME_SHA256,
            "codec": "zstd",
            "zstd": compression,
            "unique_source_count": len(sources_by_sha),
            "unique_logical_bytes": unique_logical_bytes,
            "stored_payload_bytes": stored_payload_bytes,
            "stored_payload_allocated_bytes": stored_payload_allocated_bytes,
            "compact_stored_allocated_bytes": stored_payload_allocated_bytes + metadata_allowance,
            "temporary_candidate_overhead_bytes": temporary_candidate_overhead_bytes,
            "primary_peak_write_bytes": (
                stored_payload_allocated_bytes
                + metadata_allowance
                + temporary_candidate_overhead_bytes
            ),
            "backup_stored_allocated_bytes": backup_payload_allocated_bytes + metadata_allowance,
            "allocation_unit_bytes": allocation_unit,
            "backup_allocation_unit_bytes": backup_allocation_unit,
            "metadata_allowance_bytes": metadata_allowance,
            "full_size_upper_bound_bytes": full_size,
            "compression_ratio_assumed": None,
            "exact_pinned_zstd_preflight": True,
            "stored_payload_digest": stored_payload_digest,
            "inventory_receipt_sha256": inventory.get("receipt_sha256"),
        }
    )


def forecast_no_write_content_pack_bytes(
    inventory: Mapping[str, Any],
    bindings: Bindings | None = None,
) -> dict[str, Any]:
    """Return a no-write pack forecast.

    Without a private binding this retains the public conservative upper bound
    API.  A bound lane performs the exact pinned-zstd preflight above.
    """
    if bindings is not None:
        return forecast_zstd_content_pack_bytes(inventory, bindings)
    full_size = estimate_content_pack_bytes(inventory)
    return _receipt(
        {
            "schema_version": "phase3_cycle007_storage_content_pack_forecast_v1",
            "outcome_sha256": OUTCOME_SHA256,
            "unique_logical_bytes": int(
                inventory.get("unique_logical_bytes", inventory.get("total_size_bytes", 0))
            ),
            "metadata_allowance_bytes": ZSTD_METADATA_ALLOWANCE_BYTES,
            "full_size_upper_bound_bytes": full_size,
            "compression_ratio_assumed": None,
            "exact_pinned_zstd_preflight": False,
            "inventory_receipt_sha256": inventory.get("receipt_sha256"),
        }
    )


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
    total_payload = 0
    stored_paths: set[Path] = set()
    stored_payload_entries: list[dict[str, Any]] = []
    path_index = _path_index(bindings)
    zstd_executable = _effective_zstd_executable(bindings.zstd_executable)
    compression = _zstd_metadata(zstd_executable)

    for item in inventory["objects"]:
        rel = item["role_relative_path"]
        source = path_index[rel]
        object_path_base = objects_dir / item["sha256"][:2] / item["sha256"]
        # A content hash can be shared by distinct inodes as well as by role
        # aliases.  Keep one physical blob and let every logical object point
        # to it; never add its blocks once per alias.
        zstd_path = object_path_base.with_suffix(".zst")
        lzma_path = object_path_base.with_suffix(".lzma")
        raw_path = object_path_base.with_suffix(".raw")
        existing = (
            zstd_path
            if zstd_path.exists()
            else lzma_path
            if lzma_path.exists()
            else raw_path
            if raw_path.exists()
            else None
        )
        if existing is not None:
            _regular(existing, "pack_shape_failure")
            object_path = existing
            storage = {
                ".zst": "zstd",
                ".lzma": "lzma",
                ".raw": "raw",
            }.get(existing.suffix)
            _require(storage is not None, "pack_shape_failure")
            stored_sha256 = digest_file(object_path)
            if storage == "raw":
                _require(stored_sha256 == item["sha256"], "identity_roundtrip_failure")
            else:
                _require(object_path.stat().st_size > 0, "pack_shape_failure")
            stored_size = int(object_path.stat().st_size)
        else:
            storage, object_path, stored_sha256, stored_size = _stream_object_to_pack(
                source,
                object_path_base,
                expected_sha256=item["sha256"],
                zstd_executable=zstd_executable,
            )
        if object_path not in stored_paths:
            total_stored += allocated_bytes(object_path)
            total_payload += stored_size
            stored_paths.add(object_path)
            stored_payload_entries.append(
                {
                    "sha256": item["sha256"],
                    "storage": storage,
                    "stored_sha256": stored_sha256,
                    "stored_size_bytes": stored_size,
                }
            )
        stored_objects.append(
            {
                "role_relative_path": rel,
                "role_relative_paths": list(_item_relative_paths(item)),
                "selection_class": item["selection_class"],
                "selection_classes": item.get("selection_classes", [item["selection_class"]]),
                "sha256": item["sha256"],
                "size_bytes": item["size_bytes"],
                "allocated_bytes": item["allocated_bytes"],
                "selected_path_count": item.get("selected_path_count", 1),
                "selected_link_count": item.get("selected_link_count", 1),
                "link_count": item.get("link_count", 1),
                "external_link_count": item.get("external_link_count", 0),
                "link_set_closed": _link_set_closed(item),
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
                "content_retained": True,
            }
        )

    pack_manifest = _receipt(
        {
            "schema_version": PACK_SCHEMA_VERSION,
            "outcome_sha256": OUTCOME_SHA256,
            "evaluation_cycle_id": EVALUATION_CYCLE_ID,
            "pack_kind": "content_compact",
            "fixture": bindings.fixture,
            "packet_count": inventory["packet_count"],
            "row_count": inventory["row_count"],
            "object_count": len(stored_objects),
            "ordered_row_identity_commitment_sha256": inventory[
                "ordered_row_identity_commitment_sha256"
            ],
            "object_set_sha256": inventory["object_set_sha256"],
            "deletion_state_sha256": inventory["deletion_state_sha256"],
            "inventory_receipt_sha256": inventory["receipt_sha256"],
            "total_original_allocated_bytes": inventory["total_allocated_bytes"],
            # The preflight reserves the same bounded metadata allowance.  It
            # is deliberately part of the recorded pack allocation so the
            # finalize stage can compare the no-write forecast and the actual
            # writer without assuming a compression ratio or omitting the
            # manifest/index overhead.
            "total_stored_allocated_bytes": total_stored + ZSTD_METADATA_ALLOWANCE_BYTES,
            "total_stored_payload_bytes": total_payload,
            "metadata_allowance_bytes": ZSTD_METADATA_ALLOWANCE_BYTES,
            "stored_payload_digest": digest(canonical(sorted(
                stored_payload_entries,
                key=lambda entry: str(entry["sha256"]),
            ))),
            "unique_stored_object_count": len(stored_paths),
            "compression": compression,
            "content_bodies_stored": True,
            "objects": stored_objects,
        }
    )
    _atomic_write_json(pack_dir / "pack-manifest.json", pack_manifest)
    return pack_manifest


def _require_production_inventory_shape(inventory: Mapping[str, Any]) -> None:
    """Bind a real run to the frozen Cycle007 physical denominator."""
    if inventory.get("fixture") is True:
        return
    _require(inventory.get("packet_count") == EXPECTED_PACKET_COUNT, "denominator_drift")
    _require(inventory.get("row_count") == EXPECTED_ROW_COUNT, "denominator_drift")
    _require(inventory.get("selected_path_count") == EXPECTED_SELECTED_PATH_COUNT, "denominator_drift")
    _require(inventory.get("unique_inode_count") == EXPECTED_UNIQUE_INODE_COUNT, "denominator_drift")
    _require(
        inventory.get("duplicate_selected_link_count") == EXPECTED_DUPLICATE_SELECTED_LINK_COUNT,
        "denominator_drift",
    )
    _require(inventory.get("total_allocated_bytes") == EXPECTED_TOTAL_ALLOCATED_BYTES, "denominator_drift")
    _require(inventory.get("object_set_sha256") == EXPECTED_OBJECT_SET_SHA256, "denominator_drift")
    _require(
        inventory.get("ordered_row_identity_commitment_sha256")
        == EXPECTED_ORDERED_ROW_IDENTITY_SHA256,
        "denominator_drift",
    )


def _require_preflight_runtime_match(
    preflight: Mapping[str, Any], pack_manifest: Mapping[str, Any]
) -> None:
    """Refuse a writer whose realised payload differs from exact preflight."""
    _require_receipt(preflight, "pack_shape_failure")
    _require_receipt(pack_manifest, "pack_shape_failure")
    _require(preflight.get("exact_pinned_zstd_preflight") is True, "pack_shape_failure")
    _require(pack_manifest.get("pack_kind") == "content_compact", "pack_shape_failure")
    for field in (
        "inventory_receipt_sha256",
        "stored_payload_digest",
        "stored_payload_bytes",
        "compact_stored_allocated_bytes",
    ):
        source_field = {
            "stored_payload_bytes": "total_stored_payload_bytes",
            "compact_stored_allocated_bytes": "total_stored_allocated_bytes",
        }.get(field, field)
        _require(preflight.get(field) == pack_manifest.get(source_field), "pack_shape_failure")
    _require(preflight.get("zstd") == pack_manifest.get("compression"), "pack_shape_failure")


def _pack_payload_allocated_bytes(pack_dir: Path, manifest: Mapping[str, Any]) -> int:
    """Allocated bytes for physical content blobs, excluding manifest overhead."""
    seen: set[Path] = set()
    total = 0
    objects = manifest.get("objects")
    _require(isinstance(objects, list), "pack_shape_failure")
    for item in objects:
        _require(isinstance(item, Mapping), "pack_shape_failure")
        relative = item.get("object_relative_path")
        _require(isinstance(relative, str), "pack_shape_failure")
        path = pack_dir / relative
        _regular(path, "pack_shape_failure")
        resolved = path.resolve(strict=True)
        if resolved not in seen:
            seen.add(resolved)
            total += allocated_bytes(path)
    return total


def _cleanup_partial_pack(pack_dir: Path, stage_root: Path) -> None:
    """Remove only a pack directory created by this call after a failed write.

    This is staging cleanup, never source reclamation: the directory must be a
    direct child of the newly created stage root and no original path is ever
    passed here.
    """
    try:
        if pack_dir.parent == stage_root and pack_dir.is_dir():
            shutil.rmtree(pack_dir)
    except OSError:
        # The original failure remains authoritative; a leftover partial pack
        # is fail-closed because subsequent runs reject existing stage state.
        pass


def primary_universal_pack_stage(bindings: Bindings) -> dict[str, Any]:
    """Source-side stage: exact universal pack plus portable self-hashed receipt.

    It deliberately never selects a retention outcome or removes originals.
    A caller transports only the compact ``pack`` directory and the returned
    ``portable_export`` receipt to the independent workstation.
    """
    _require(bindings.private_bound, "private_binding_unbound")
    if not bindings.fixture:
        _require(bool(bindings.failure_domain_token), "private_binding_unbound")
    stage_root = bindings.work_root / "cycle007-storage-primary-stage"
    if os.path.lexists(stage_root):
        raise StorageCustodyError("existing_lane_state")
    stage_root.mkdir(mode=PRIVATE_DIR_MODE)
    os.chmod(stage_root, PRIVATE_DIR_MODE)

    inventory = build_inventory(bindings)
    _require_production_inventory_shape(inventory)
    reconcile = reconcile_public_private(private_bound=True, inventory=inventory)
    if not bindings.fixture:
        _require(reconcile.get("denominator_match") is True, "denominator_drift")
    preflight = forecast_no_write_content_pack_bytes(inventory, bindings)
    required = int(
        preflight.get(
            "primary_peak_write_bytes",
            preflight["compact_stored_allocated_bytes"],
        )
    )
    source_avail_before = available_bytes(bindings.work_root)
    if not bindings.fixture:
        _require(source_avail_before - required >= MIN_FREE_BYTES, "capacity_insufficient")

    pack_dir = stage_root / "pack"
    try:
        pack_manifest = write_pack(inventory, bindings, pack_dir)
        _require_preflight_runtime_match(preflight, pack_manifest)
        source_avail_after = available_bytes(bindings.work_root)
        if not bindings.fixture:
            _require(source_avail_after >= MIN_FREE_BYTES, "capacity_insufficient")
        roundtrip, identity_proof = prove_content_pack_stream(
            inventory, pack_dir, zstd_executable=bindings.zstd_executable
        )
    except (OSError, StorageCustodyError):
        _cleanup_partial_pack(pack_dir, stage_root)
        raise
    source_domain = _failure_domain_sha256(
        bindings.failure_domain_token or "fixture-primary-domain"
    )
    source_physical_domain = _physical_failure_domain_sha256(bindings.work_root)
    primary = _receipt(
        {
            "schema_version": PRIMARY_STAGE_SCHEMA_VERSION,
            "outcome_sha256": OUTCOME_SHA256,
            "fixture": bindings.fixture,
            "inventory_receipt_sha256": inventory["receipt_sha256"],
            "reconcile_receipt_sha256": reconcile["receipt_sha256"],
            "preflight_receipt_sha256": preflight["receipt_sha256"],
            "pack_manifest_sha256": pack_manifest["receipt_sha256"],
            "roundtrip_receipt_sha256": roundtrip["receipt_sha256"],
            "identity_proof_sha256": identity_proof["receipt_sha256"],
            "source_failure_domain_sha256": source_domain,
            "source_physical_domain_sha256": source_physical_domain,
            "packet_count": inventory["packet_count"],
            "row_count": inventory["row_count"],
            "object_count": inventory["object_count"],
            "total_allocated_bytes": inventory["total_allocated_bytes"],
            "object_set_sha256": inventory["object_set_sha256"],
            "deletion_state_sha256": inventory["deletion_state_sha256"],
            "compact_stored_allocated_bytes": pack_manifest["total_stored_allocated_bytes"],
            "source_avail_before_bytes": source_avail_before,
            "source_avail_after_bytes": source_avail_after,
            "min_free_bytes": MIN_FREE_BYTES,
            "roundtrip_ok": roundtrip["roundtrip_ok"],
            "identity_proof_ok": identity_proof["identity_proof_ok"],
            "no_deletion_performed": True,
        }
    )
    portable_export = _receipt(
        {
            "schema_version": PORTABLE_EXPORT_SCHEMA_VERSION,
            "outcome_sha256": OUTCOME_SHA256,
            "primary_stage_receipt_sha256": primary["receipt_sha256"],
            "inventory_receipt_sha256": inventory["receipt_sha256"],
            "preflight_receipt_sha256": preflight["receipt_sha256"],
            "pack_manifest_sha256": pack_manifest["receipt_sha256"],
            "source_failure_domain_sha256": source_domain,
            "source_physical_domain_sha256": source_physical_domain,
            "packet_count": inventory["packet_count"],
            "row_count": inventory["row_count"],
            "object_count": inventory["object_count"],
            "total_allocated_bytes": inventory["total_allocated_bytes"],
            "object_set_sha256": inventory["object_set_sha256"],
            "deletion_state_sha256": inventory["deletion_state_sha256"],
            "compact_stored_allocated_bytes": pack_manifest["total_stored_allocated_bytes"],
            "no_deletion_performed": True,
        }
    )
    _atomic_write_json(stage_root / "inventory.json", inventory)
    _atomic_write_json(stage_root / "reconcile.json", reconcile)
    _atomic_write_json(stage_root / "preflight.json", preflight)
    _atomic_write_json(stage_root / "pack-manifest.receipt.json", pack_manifest)
    _atomic_write_json(stage_root / "roundtrip.json", roundtrip)
    _atomic_write_json(stage_root / "identity-proof.json", identity_proof)
    _atomic_write_json(stage_root / "primary-stage.json", primary)
    _atomic_write_json(stage_root / "portable-export.json", portable_export)
    return {
        "primary_stage": primary,
        "portable_export": portable_export,
        "inventory": inventory,
        "preflight": preflight,
        "pack_manifest": pack_manifest,
        "roundtrip": roundtrip,
        "identity_proof": identity_proof,
        "pack_dir": pack_dir,
    }


def _portable_content_stream_proof(
    pack_dir: Path, portable_export: Mapping[str, Any], *, zstd_executable: Path | None
) -> dict[str, Any]:
    """Full streaming decompression/hash proof without source filesystem access."""
    _require_receipt(portable_export, "backup_restore_failure")
    _require(portable_export.get("schema_version") == PORTABLE_EXPORT_SCHEMA_VERSION, "backup_restore_failure")
    manifest = _read_json(pack_dir / "pack-manifest.json", "backup_restore_failure")
    _require(isinstance(manifest, Mapping), "backup_restore_failure")
    _require_receipt(manifest, "backup_restore_failure")
    _require(manifest.get("pack_kind") == "content_compact", "backup_restore_failure")
    for field in (
        "packet_count",
        "row_count",
        "object_count",
        "object_set_sha256",
        "deletion_state_sha256",
    ):
        _require(manifest.get(field) == portable_export.get(field), "backup_restore_failure")
    _require(manifest.get("receipt_sha256") == portable_export.get("pack_manifest_sha256"), "backup_restore_failure")
    pairs: list[tuple[str, str]] = []
    for item in manifest.get("objects", []):
        _require(isinstance(item, Mapping), "backup_restore_failure")
        relative = item.get("object_relative_path")
        _require(isinstance(relative, str), "backup_restore_failure")
        object_path = pack_dir / relative
        _regular(object_path, "backup_restore_failure")
        _require(digest_file(object_path) == item.get("stored_sha256"), "backup_restore_failure")
        raw_digest, raw_size = _stream_digest_chunks(
            _iter_stored_raw_chunks(object_path, str(item.get("storage")), zstd_executable)
        )
        _require(raw_digest == item.get("sha256"), "backup_restore_failure")
        _require(raw_size == item.get("size_bytes"), "backup_restore_failure")
        pairs.extend((rel, raw_digest) for rel in _item_relative_paths(item))
    object_set = _pairs_digest(pairs)
    _require(object_set == portable_export.get("object_set_sha256"), "backup_restore_failure")
    return _receipt(
        {
            "schema_version": "phase3_cycle007_storage_backup_restore_proof_v1",
            "outcome_sha256": OUTCOME_SHA256,
            "pack_manifest_sha256": manifest["receipt_sha256"],
            "object_set_sha256": object_set,
            "object_count": manifest["object_count"],
            "packet_count": manifest["packet_count"],
            "row_count": manifest["row_count"],
            "backup_restore_ok": True,
            "second_expanded_tree": False,
            "proof_mode": "portable_stream_decompress_hash",
        }
    )


def workstation_backup_admission_stage(
    portable_export: Mapping[str, Any],
    workstation_root: Path,
    planned_backup_pack_dir: Path,
    *,
    source_failure_domain_token: str,
    workstation_failure_domain_token: str,
    workstation_domain_config: Path | None = None,
    fixture: bool = False,
) -> dict[str, Any]:
    """Fresh pre-transport capacity and failure-domain admission receipt."""
    _require_receipt(portable_export, "backup_restore_failure")
    _require(
        portable_export.get("schema_version") == PORTABLE_EXPORT_SCHEMA_VERSION,
        "backup_restore_failure",
    )
    _directory(workstation_root, "backup_restore_failure")
    _require(not os.path.lexists(planned_backup_pack_dir), "existing_lane_state")
    _require(
        planned_backup_pack_dir.parent.resolve(strict=True)
        == workstation_root.resolve(strict=True),
        "backup_restore_failure",
    )
    source_domain = _failure_domain_sha256(source_failure_domain_token)
    workstation_domain = _failure_domain_sha256(workstation_failure_domain_token)
    workstation_physical_domain = _physical_failure_domain_sha256(workstation_root)
    if not fixture:
        _require(workstation_domain_config is not None, "private_binding_unbound")
        assert workstation_domain_config is not None
        _regular(workstation_domain_config, "path_disclosure_refused")
        _require(
            stat.S_IMODE(workstation_domain_config.stat().st_mode) == PRIVATE_FILE_MODE,
            "path_disclosure_refused",
        )
        domain_config = _read_json(
            workstation_domain_config, "path_disclosure_refused"
        )
        _require(isinstance(domain_config, Mapping), "path_disclosure_refused")
        configured_root = domain_config.get("workstation_root")
        configured_token = domain_config.get("failure_domain_token")
        approved_source = domain_config.get("approved_source_failure_domain_sha256")
        _require(
            isinstance(configured_root, str)
            and Path(configured_root).resolve(strict=True)
            == workstation_root.resolve(strict=True)
            and configured_token == workstation_failure_domain_token
            and approved_source == source_domain,
            "backup_restore_failure",
        )
    _require(
        source_domain == portable_export.get("source_failure_domain_sha256"),
        "backup_restore_failure",
    )
    _require(source_domain != workstation_domain, "backup_restore_failure")
    _require(
        portable_export.get("source_physical_domain_sha256")
        != workstation_physical_domain,
        "backup_restore_failure",
    )
    required = int(portable_export.get("compact_stored_allocated_bytes", -1))
    _require(required >= 0, "backup_restore_failure")
    avail_before = available_bytes(workstation_root)
    if not fixture:
        _require(avail_before - required >= MIN_FREE_BYTES, "capacity_insufficient")
    admission = _receipt(
        {
            "schema_version": BACKUP_ADMISSION_SCHEMA_VERSION,
            "outcome_sha256": OUTCOME_SHA256,
            "portable_export_receipt_sha256": portable_export["receipt_sha256"],
            "source_failure_domain_sha256": source_domain,
            "workstation_failure_domain_sha256": workstation_domain,
            "source_physical_domain_sha256": portable_export[
                "source_physical_domain_sha256"
            ],
            "workstation_physical_domain_sha256": workstation_physical_domain,
            "required_write_bytes": required,
            "workstation_avail_before_bytes": avail_before,
            "min_free_bytes": MIN_FREE_BYTES,
            "capacity_admitted": True,
            "destination_absent_before_transport": True,
        }
    )
    admission_path = workstation_root / "cycle007-storage-backup-admission.json"
    if os.path.lexists(admission_path):
        raise StorageCustodyError("existing_lane_state")
    _atomic_write_json(admission_path, admission)
    return admission


def workstation_backup_attestation_stage(
    portable_export: Mapping[str, Any],
    admission: Mapping[str, Any],
    backup_pack_dir: Path,
    workstation_root: Path,
    *,
    source_failure_domain_token: str,
    workstation_failure_domain_token: str,
    zstd_executable: Path | None = None,
    fixture: bool = False,
) -> dict[str, Any]:
    """Workstation stage: attest an imported compact pack in an independent domain.

    The import itself is an external transport operation.  This stage proves
    every stored blob by streaming decompression and hashes; it does not create
    any expanded restoration tree.
    """
    _require_receipt(portable_export, "backup_restore_failure")
    _require_receipt(admission, "backup_restore_failure")
    _require(
        admission.get("schema_version") == BACKUP_ADMISSION_SCHEMA_VERSION,
        "backup_restore_failure",
    )
    _require(
        admission.get("portable_export_receipt_sha256")
        == portable_export.get("receipt_sha256"),
        "backup_restore_failure",
    )
    _directory(workstation_root, "backup_restore_failure")
    _directory(backup_pack_dir, "backup_restore_failure")
    _require(os.stat(backup_pack_dir).st_dev == os.stat(workstation_root).st_dev, "backup_restore_failure")
    source_domain = _failure_domain_sha256(source_failure_domain_token)
    workstation_domain = _failure_domain_sha256(workstation_failure_domain_token)
    _require(source_domain == portable_export.get("source_failure_domain_sha256"), "backup_restore_failure")
    _require(source_domain != workstation_domain, "backup_restore_failure")
    _require(
        admission.get("source_failure_domain_sha256") == source_domain
        and admission.get("workstation_failure_domain_sha256") == workstation_domain,
        "backup_restore_failure",
    )
    _require(
        admission.get("source_physical_domain_sha256")
        == portable_export.get("source_physical_domain_sha256")
        and admission.get("workstation_physical_domain_sha256")
        == _physical_failure_domain_sha256(workstation_root),
        "backup_restore_failure",
    )
    manifest = _read_json(backup_pack_dir / "pack-manifest.json", "backup_restore_failure")
    _require(isinstance(manifest, Mapping), "backup_restore_failure")
    _require_receipt(manifest, "backup_restore_failure")
    source_allocated = int(portable_export.get("compact_stored_allocated_bytes", -1))
    backup_allocated = (
        _pack_payload_allocated_bytes(backup_pack_dir, manifest)
        + ZSTD_METADATA_ALLOWANCE_BYTES
    )
    # ``st_blocks`` is a property of the destination filesystem, not of the
    # transported bytes.  APFS, ext4, and network-backed filesystems can
    # legitimately allocate different block counts for the exact same pack.
    # Bind the portable source forecast to the manifest/admission, then record
    # the workstation's actual allocation independently.  Content equality is
    # proved below by a full stored-hash + stream-decompression pass, while the
    # fresh post-copy floor is the authoritative destination-capacity gate.
    _require(
        source_allocated == int(manifest.get("total_stored_allocated_bytes", -1)),
        "backup_restore_failure",
    )
    _require(
        admission.get("required_write_bytes") == source_allocated,
        "backup_restore_failure",
    )
    _require(backup_allocated >= ZSTD_METADATA_ALLOWANCE_BYTES, "backup_restore_failure")
    restore_proof = _portable_content_stream_proof(
        backup_pack_dir, portable_export, zstd_executable=zstd_executable
    )
    avail_after = available_bytes(workstation_root)
    if not fixture:
        _require(avail_after >= MIN_FREE_BYTES, "capacity_insufficient")
    backup = _receipt(
        {
            "schema_version": BACKUP_SCHEMA_VERSION,
            "outcome_sha256": OUTCOME_SHA256,
            "pack_manifest_sha256": manifest["receipt_sha256"],
            "backup_object_count": manifest["object_count"],
            "backup_unique_inode_count": manifest.get("unique_stored_object_count"),
            "backup_duplicate_selected_link_count": 0,
            "backup_allocated_bytes": backup_allocated,
            "source_compact_allocated_bytes": source_allocated,
            "backup_allocation_delta_bytes": backup_allocated - source_allocated,
            "backup_set_sha256": digest(canonical({"pack_manifest_sha256": manifest["receipt_sha256"]})),
            "source_failure_domain_sha256": source_domain,
            "backup_failure_domain_sha256": workstation_domain,
            "source_physical_domain_sha256": admission[
                "source_physical_domain_sha256"
            ],
            "backup_physical_domain_sha256": admission[
                "workstation_physical_domain_sha256"
            ],
            "independent_failure_domain": True,
            "restore_proof_pending": False,
        }
    )
    attestation = _receipt(
        {
            "schema_version": BACKUP_ATTESTATION_SCHEMA_VERSION,
            "outcome_sha256": OUTCOME_SHA256,
            "portable_export_receipt_sha256": portable_export["receipt_sha256"],
            "backup_admission_receipt_sha256": admission["receipt_sha256"],
            "pack_manifest_sha256": manifest["receipt_sha256"],
            "backup_receipt_sha256": backup["receipt_sha256"],
            "backup_restore_proof_sha256": restore_proof["receipt_sha256"],
            "source_failure_domain_sha256": source_domain,
            "workstation_failure_domain_sha256": workstation_domain,
            "source_physical_domain_sha256": admission[
                "source_physical_domain_sha256"
            ],
            "workstation_physical_domain_sha256": admission[
                "workstation_physical_domain_sha256"
            ],
            "independent_failure_domain": True,
            "workstation_avail_before_bytes": admission[
                "workstation_avail_before_bytes"
            ],
            "workstation_avail_after_bytes": avail_after,
            "min_free_bytes": MIN_FREE_BYTES,
            "source_compact_allocated_bytes": source_allocated,
            "backup_allocated_bytes": backup_allocated,
            "backup_allocation_delta_bytes": backup_allocated - source_allocated,
            "backup_restore_ok": True,
            "proof_mode": "portable_stream_decompress_hash",
            "no_deletion_performed": True,
        }
    )
    attestation_root = workstation_root / "cycle007-storage-backup-attestation"
    if os.path.lexists(attestation_root):
        raise StorageCustodyError("existing_lane_state")
    attestation_root.mkdir(mode=PRIVATE_DIR_MODE)
    os.chmod(attestation_root, PRIVATE_DIR_MODE)
    _atomic_write_json(attestation_root / "backup.json", backup)
    _atomic_write_json(attestation_root / "backup-restore-proof.json", restore_proof)
    _atomic_write_json(attestation_root / "attestation.json", attestation)
    return {
        "backup": backup,
        "restore_proof": restore_proof,
        "attestation": attestation,
    }


def issue_finalization_challenge(
    bindings: Bindings,
    primary: Mapping[str, Any],
    portable_export: Mapping[str, Any],
) -> dict[str, Any]:
    """Issue one persisted nonce after initial two-copy custody proof."""
    _require_receipt(primary, "stage_state_failure")
    _require_receipt(portable_export, "stage_state_failure")
    _require(
        primary.get("receipt_sha256")
        == portable_export.get("primary_stage_receipt_sha256"),
        "stage_state_failure",
    )
    stage_root = bindings.work_root / "cycle007-storage-primary-stage"
    _directory(stage_root, "stage_state_failure")
    challenge_path = stage_root / "finalization-challenge.json"
    if os.path.lexists(challenge_path):
        raise StorageCustodyError("existing_lane_state")
    challenge = _receipt(
        {
            "schema_version": FINALIZATION_CHALLENGE_SCHEMA_VERSION,
            "outcome_sha256": OUTCOME_SHA256,
            "primary_stage_receipt_sha256": primary["receipt_sha256"],
            "portable_export_receipt_sha256": portable_export["receipt_sha256"],
            "challenge_nonce": secrets.token_hex(32),
            "single_use": True,
        }
    )
    _atomic_write_json(challenge_path, challenge)
    return challenge


def workstation_finalization_response_stage(
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
    """Answer a single-use source nonce with a fresh live-backup proof."""
    for value in (portable_export, initial_attestation, challenge):
        _require_receipt(value, "backup_restore_failure")
    _require(
        challenge.get("schema_version") == FINALIZATION_CHALLENGE_SCHEMA_VERSION,
        "backup_restore_failure",
    )
    _require(
        challenge.get("portable_export_receipt_sha256")
        == portable_export.get("receipt_sha256"),
        "backup_restore_failure",
    )
    _require(
        initial_attestation.get("portable_export_receipt_sha256")
        == portable_export.get("receipt_sha256"),
        "backup_restore_failure",
    )
    source_domain = _failure_domain_sha256(source_failure_domain_token)
    workstation_domain = _failure_domain_sha256(workstation_failure_domain_token)
    workstation_physical_domain = _physical_failure_domain_sha256(workstation_root)
    _require(
        source_domain == portable_export.get("source_failure_domain_sha256")
        and source_domain != workstation_domain
        and portable_export.get("source_physical_domain_sha256")
        != workstation_physical_domain,
        "backup_restore_failure",
    )
    _directory(backup_pack_dir, "backup_restore_failure")
    fresh_proof = _portable_content_stream_proof(
        backup_pack_dir,
        portable_export,
        zstd_executable=zstd_executable,
    )
    avail_after = available_bytes(workstation_root)
    if not fixture:
        _require(avail_after >= MIN_FREE_BYTES, "capacity_insufficient")
    response = _receipt(
        {
            "schema_version": FINALIZATION_RESPONSE_SCHEMA_VERSION,
            "outcome_sha256": OUTCOME_SHA256,
            "portable_export_receipt_sha256": portable_export["receipt_sha256"],
            "initial_attestation_receipt_sha256": initial_attestation[
                "receipt_sha256"
            ],
            "challenge_receipt_sha256": challenge["receipt_sha256"],
            "challenge_nonce": challenge["challenge_nonce"],
            "source_failure_domain_sha256": source_domain,
            "workstation_failure_domain_sha256": workstation_domain,
            "source_physical_domain_sha256": portable_export[
                "source_physical_domain_sha256"
            ],
            "workstation_physical_domain_sha256": workstation_physical_domain,
            "fresh_restore_proof": fresh_proof,
            "workstation_avail_after_bytes": avail_after,
            "min_free_bytes": MIN_FREE_BYTES,
            "backup_live_at_response": True,
        }
    )
    response_path = (
        workstation_root
        / "cycle007-storage-backup-attestation"
        / "finalization-response.json"
    )
    if os.path.lexists(response_path):
        raise StorageCustodyError("existing_lane_state")
    _atomic_write_json(response_path, response)
    return response


def finalize_source_deletion_auth_stage(
    bindings: Bindings,
    primary: Mapping[str, Any],
    portable_export: Mapping[str, Any],
    backup_attestation: Mapping[str, Any],
    backup: Mapping[str, Any],
    restore_proof: Mapping[str, Any],
    pack_manifest: Mapping[str, Any],
    frozen_inventory: Mapping[str, Any],
    primary_pack_dir: Path,
    challenge: Mapping[str, Any],
    finalization_response: Mapping[str, Any],
    *,
    held_out_evaluation_proof: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Source-side final gate after imported independent backup proof.

    It rescans source inodes and link closure immediately before emitting a
    non-authorizing deletion request.  It never unlinks any source entry.
    """
    for value in (
        primary,
        portable_export,
        backup_attestation,
        backup,
        restore_proof,
        pack_manifest,
        frozen_inventory,
        challenge,
        finalization_response,
    ):
        _require_receipt(value, "backup_restore_failure")
    _require(primary.get("schema_version") == PRIMARY_STAGE_SCHEMA_VERSION, "backup_restore_failure")
    _require(portable_export.get("schema_version") == PORTABLE_EXPORT_SCHEMA_VERSION, "backup_restore_failure")
    _require(backup_attestation.get("schema_version") == BACKUP_ATTESTATION_SCHEMA_VERSION, "backup_restore_failure")
    _require(primary.get("receipt_sha256") == portable_export.get("primary_stage_receipt_sha256"), "backup_restore_failure")
    _require(portable_export.get("receipt_sha256") == backup_attestation.get("portable_export_receipt_sha256"), "backup_restore_failure")
    _require(backup_attestation.get("backup_receipt_sha256") == backup.get("receipt_sha256"), "backup_restore_failure")
    _require(backup_attestation.get("backup_restore_proof_sha256") == restore_proof.get("receipt_sha256"), "backup_restore_failure")
    _require(backup_attestation.get("backup_restore_ok") is True, "backup_restore_failure")
    _require(
        backup_attestation.get("proof_mode") == "portable_stream_decompress_hash"
        and restore_proof.get("proof_mode") == "portable_stream_decompress_hash",
        "backup_restore_failure",
    )
    _require(
        backup_attestation.get("independent_failure_domain") is True
        and backup.get("independent_failure_domain") is True,
        "backup_restore_failure",
    )
    _require(
        backup_attestation.get("source_failure_domain_sha256")
        == primary.get("source_failure_domain_sha256")
        == portable_export.get("source_failure_domain_sha256")
        == backup.get("source_failure_domain_sha256"),
        "backup_restore_failure",
    )
    _require(
        backup_attestation.get("workstation_failure_domain_sha256")
        == backup.get("backup_failure_domain_sha256"),
        "backup_restore_failure",
    )
    _require(
        backup_attestation.get("source_physical_domain_sha256")
        == primary.get("source_physical_domain_sha256")
        == portable_export.get("source_physical_domain_sha256")
        == backup.get("source_physical_domain_sha256")
        and backup_attestation.get("workstation_physical_domain_sha256")
        == backup.get("backup_physical_domain_sha256")
        and backup_attestation.get("source_physical_domain_sha256")
        != backup_attestation.get("workstation_physical_domain_sha256"),
        "backup_restore_failure",
    )
    _require(
        backup_attestation.get("workstation_avail_after_bytes", -1) >= MIN_FREE_BYTES
        and backup_attestation.get("min_free_bytes") == MIN_FREE_BYTES,
        "capacity_insufficient",
    )
    _require(
        isinstance(backup_attestation.get("backup_admission_receipt_sha256"), str)
        and len(backup_attestation["backup_admission_receipt_sha256"]) == 64,
        "backup_restore_failure",
    )
    _require(pack_manifest.get("receipt_sha256") == primary.get("pack_manifest_sha256"), "backup_restore_failure")
    _require(
        challenge.get("schema_version") == FINALIZATION_CHALLENGE_SCHEMA_VERSION
        and finalization_response.get("schema_version")
        == FINALIZATION_RESPONSE_SCHEMA_VERSION,
        "backup_restore_failure",
    )
    _require(
        challenge.get("primary_stage_receipt_sha256") == primary.get("receipt_sha256")
        and challenge.get("portable_export_receipt_sha256")
        == portable_export.get("receipt_sha256")
        and finalization_response.get("challenge_receipt_sha256")
        == challenge.get("receipt_sha256")
        and finalization_response.get("challenge_nonce")
        == challenge.get("challenge_nonce")
        and finalization_response.get("initial_attestation_receipt_sha256")
        == backup_attestation.get("receipt_sha256"),
        "backup_restore_failure",
    )
    challenge_proof = finalization_response.get("fresh_restore_proof")
    _require(isinstance(challenge_proof, Mapping), "backup_restore_failure")
    _require_receipt(challenge_proof, "backup_restore_failure")
    _require(
        challenge_proof.get("proof_mode") == "portable_stream_decompress_hash"
        and challenge_proof.get("backup_restore_ok") is True
        and challenge_proof.get("pack_manifest_sha256")
        == pack_manifest.get("receipt_sha256")
        and finalization_response.get("backup_live_at_response") is True
        and finalization_response.get("workstation_avail_after_bytes", -1)
        >= MIN_FREE_BYTES
        and finalization_response.get("min_free_bytes") == MIN_FREE_BYTES,
        "backup_restore_failure",
    )
    _require(
        finalization_response.get("source_physical_domain_sha256")
        == primary.get("source_physical_domain_sha256")
        and finalization_response.get("workstation_physical_domain_sha256")
        == backup_attestation.get("workstation_physical_domain_sha256"),
        "backup_restore_failure",
    )
    _require(
        pack_manifest.get("deletion_state_sha256")
        == portable_export.get("deletion_state_sha256")
        == frozen_inventory.get("deletion_state_sha256"),
        "identity_roundtrip_failure",
    )
    fresh_primary_proof = _portable_content_stream_proof(
        primary_pack_dir,
        portable_export,
        zstd_executable=bindings.zstd_executable,
    )
    source_avail_before = available_bytes(bindings.work_root)
    if not bindings.fixture:
        _require(source_avail_before >= MIN_FREE_BYTES, "capacity_insufficient")
    inventory = build_inventory(bindings)
    _require_production_inventory_shape(inventory)
    # ``statvfs`` is deliberately part of the fresh inventory receipt, so its
    # capacity fields change after writing the compact pack.  Compare the
    # frozen semantic/physical denominator rather than demanding the old
    # receipt byte-for-byte.
    for field in (
        "packet_count",
        "row_count",
        "object_count",
        "total_allocated_bytes",
        "object_set_sha256",
        "deletion_state_sha256",
    ):
        _require(inventory.get(field) == primary.get(field), "identity_roundtrip_failure")
        _require(inventory.get(field) == frozen_inventory.get(field), "identity_roundtrip_failure")
    _require(inventory.get("fully_closed_reclaimable_bytes") == inventory.get("total_allocated_bytes"), "identity_roundtrip_failure")
    retention = decide_retention(inventory=inventory, held_out_evaluation_proof=held_out_evaluation_proof)
    # The pack commits to the frozen pre-write receipt.  The fresh rescan above
    # proves that its semantic denominator and every link set remain intact;
    # authorization targets remain anchored to that immutable pack commitment.
    frozen_retention = decide_retention(
        inventory=frozen_inventory, held_out_evaluation_proof=held_out_evaluation_proof
    )
    auth = deletion_auth_request(frozen_inventory, pack_manifest, frozen_retention, backup, restore_proof)
    source_avail_after = available_bytes(bindings.work_root)
    if not bindings.fixture:
        _require(source_avail_after >= MIN_FREE_BYTES, "capacity_insufficient")
    final = _receipt(
        {
            "schema_version": FINALIZE_SCHEMA_VERSION,
            "outcome_sha256": OUTCOME_SHA256,
            "primary_stage_receipt_sha256": primary["receipt_sha256"],
            "portable_export_receipt_sha256": portable_export["receipt_sha256"],
            "backup_attestation_receipt_sha256": backup_attestation["receipt_sha256"],
            "finalization_challenge_receipt_sha256": challenge["receipt_sha256"],
            "finalization_response_receipt_sha256": finalization_response[
                "receipt_sha256"
            ],
            "fresh_inventory_receipt_sha256": inventory["receipt_sha256"],
            "retention_receipt_sha256": frozen_retention["receipt_sha256"],
            "fresh_retention_receipt_sha256": retention["receipt_sha256"],
            "deletion_auth_request_sha256": auth["receipt_sha256"],
            "fresh_primary_restore_proof_sha256": fresh_primary_proof[
                "receipt_sha256"
            ],
            "source_avail_before_bytes": source_avail_before,
            "source_avail_after_bytes": source_avail_after,
            "min_free_bytes": MIN_FREE_BYTES,
            "fresh_link_set_closed": True,
            "deletion_authorized": False,
            "no_deletion_performed": True,
        }
    )
    final_root = bindings.work_root / "cycle007-storage-primary-stage"
    _directory(final_root, "stage_state_failure")
    final_path = final_root / "finalize.json"
    if os.path.lexists(final_path):
        raise StorageCustodyError("existing_lane_state")
    _atomic_write_json(final_root / "backup-attestation.imported.json", backup_attestation)
    _atomic_write_json(final_root / "backup-receipt.imported.json", backup)
    _atomic_write_json(final_root / "backup-restore-proof.imported.json", restore_proof)
    _atomic_write_json(final_root / "finalization-response.imported.json", finalization_response)
    _atomic_write_json(final_root / "fresh-inventory.json", inventory)
    _atomic_write_json(final_root / "fresh-primary-restore-proof.json", fresh_primary_proof)
    _atomic_write_json(final_root / "retention-decision.finalize.json", frozen_retention)
    _atomic_write_json(final_root / "deletion-auth-request.json", auth)
    _atomic_write_json(final_path, final)
    return {
        "inventory": inventory,
        "retention": frozen_retention,
        "fresh_retention": retention,
        "auth": auth,
        "finalize": final,
    }


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


def expand_pack(
    pack_dir: Path,
    destination: Path,
    *,
    zstd_executable: Path | None = None,
) -> dict[str, Any]:
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
        _regular(object_path, "pack_shape_failure")
        _require(digest_file(object_path) == item["stored_sha256"], "identity_roundtrip_failure")
        aliases = _item_relative_paths(item)
        _require(bool(aliases), "pack_shape_failure")
        target = destination / aliases[0]
        target.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(target.parent, PRIVATE_DIR_MODE)
        raw_sha256, raw_size = _atomic_write_stream(
            target,
            _iter_stored_raw_chunks(
                object_path,
                str(item["storage"]),
                zstd_executable,
            ),
            mode=int(item["mode"]),
        )
        _require(raw_sha256 == item["sha256"], "identity_roundtrip_failure")
        _require(raw_size == item["size_bytes"], "identity_roundtrip_failure")
        # Recreate logical overlap aliases as hard links.  This preserves the
        # source identity shape without allocating another content body.
        for alias in aliases[1:]:
            alias_target = destination / alias
            alias_target.parent.mkdir(parents=True, exist_ok=True)
            os.chmod(alias_target.parent, PRIVATE_DIR_MODE)
            os.link(target, alias_target)
            os.chmod(alias_target, int(item["mode"]))
        restored.append(
            {
                "role_relative_path": item["role_relative_path"],
                "role_relative_paths": list(aliases),
                "sha256": item["sha256"],
                "size_bytes": item["size_bytes"],
                "selection_class": item["selection_class"],
            }
        )

    object_set_sha256 = _object_set_digest(restored)
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
        "materialization_packet" in item.get("selection_classes", [item["selection_class"]])
        for item in inventory["objects"]
    )
    for item in inventory["objects"]:
        aliases = _item_relative_paths(item)
        _require(bool(aliases), "identity_roundtrip_failure")
        path = restored_root / aliases[0]
        _regular(path, "identity_roundtrip_failure")
        raw_sha256 = digest_file(path)
        _require(raw_sha256 == item["sha256"], "identity_roundtrip_failure")
        for alias in aliases:
            alias_path = restored_root / alias
            _regular(alias_path, "identity_roundtrip_failure")
            _require(digest_file(alias_path) == raw_sha256, "identity_roundtrip_failure")
            restored_objects.append((alias, raw_sha256))
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
    object_set = _pairs_digest(restored_objects)
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


def create_backup(
    pack_dir: Path,
    backup_dir: Path,
    *,
    source_failure_domain_token: str | None = None,
    backup_failure_domain_token: str | None = None,
) -> dict[str, Any]:
    """Copy a pack without expanding it and bind the copy to two domain tokens.

    The legacy fixture lane supplies deterministic local tokens.  Production
    staged custody must pass operator-provided tokens through
    :func:`attest_independent_backup`; this function never derives a domain
    from hostname or ``st_dev``.
    """
    if backup_dir.exists():
        raise StorageCustodyError("backup_restore_failure")

    _directory(pack_dir, "backup_restore_failure")
    backup_dir.mkdir(mode=PRIVATE_DIR_MODE)
    os.chmod(backup_dir, PRIVATE_DIR_MODE)
    source_inode_destinations: dict[tuple[int, int], Path] = {}
    source_files: list[tuple[str, Path]] = []
    for dirpath, dirnames, filenames in os.walk(pack_dir, followlinks=False):
        dirnames[:] = sorted(dirnames)
        filenames = sorted(filenames)
        relative_dir = Path(dirpath).relative_to(pack_dir)
        destination_dir = backup_dir / relative_dir
        destination_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(destination_dir, PRIVATE_DIR_MODE)
        for filename in filenames:
            source = Path(dirpath) / filename
            _regular(source, "backup_restore_failure")
            relative = source.relative_to(pack_dir).as_posix()
            destination = backup_dir / relative
            inode_key = _physical_inode_key(source)
            previous = source_inode_destinations.get(inode_key)
            if previous is not None:
                os.link(previous, destination)
            else:
                def chunks(source_path: Path = source) -> Iterator[bytes]:
                    with source_path.open("rb") as source_handle:
                        yield from iter(lambda: source_handle.read(1024 * 1024), b"")

                _atomic_write_stream(destination, chunks())
                source_inode_destinations[inode_key] = destination
            os.chmod(destination, PRIVATE_FILE_MODE)
            source_files.append((relative, destination))
    manifest = _read_json(backup_dir / "pack-manifest.json", "backup_restore_failure")
    _require_receipt(manifest, "backup_restore_failure")
    backup_set: list[tuple[str, str]] = []
    total_alloc = 0
    backup_inode_keys: set[tuple[int, int]] = set()
    for rel, path in source_files:
        sha = digest_file(path)
        backup_set.append((rel, sha))
        inode_key = _physical_inode_key(path)
        if inode_key not in backup_inode_keys:
            total_alloc += allocated_bytes(path)
            backup_inode_keys.add(inode_key)
    backup_set_sha256 = _pairs_digest(backup_set)
    source_failure_domain = _failure_domain_sha256(
        source_failure_domain_token or "legacy-source-domain"
    )
    backup_failure_domain = _failure_domain_sha256(
        backup_failure_domain_token or "legacy-backup-domain"
    )
    return _receipt(
        {
            "schema_version": BACKUP_SCHEMA_VERSION,
            "outcome_sha256": OUTCOME_SHA256,
            "pack_manifest_sha256": manifest["receipt_sha256"],
            "backup_object_count": len(backup_set),
            "backup_unique_inode_count": len(backup_inode_keys),
            "backup_duplicate_selected_link_count": len(backup_set) - len(backup_inode_keys),
            "backup_allocated_bytes": total_alloc + ZSTD_METADATA_ALLOWANCE_BYTES,
            "backup_set_sha256": backup_set_sha256,
            "source_failure_domain_sha256": source_failure_domain,
            "backup_failure_domain_sha256": backup_failure_domain,
            "independent_failure_domain": (
                source_failure_domain != backup_failure_domain
            ),
            "restore_proof_pending": True,
        }
    )


def prove_backup_restore(
    backup_dir: Path,
    restore_dir: Path,
    *,
    zstd_executable: Path | None = None,
) -> dict[str, Any]:
    roundtrip = expand_pack(backup_dir, restore_dir, zstd_executable=zstd_executable)
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
    _require_receipt(inventory, "identity_roundtrip_failure")
    _require_receipt(pack_manifest, "identity_roundtrip_failure")
    _require_receipt(retention, "retention_blocked")
    _require_receipt(backup, "backup_restore_failure")
    _require_receipt(restore_proof, "backup_restore_failure")
    retention_outcome = retention.get("retention_outcome")
    retention_final = retention.get("retention_final") is True
    retention_unresolved = bool(
        retention_outcome is None
        and retention.get("retention_status") == RETENTION_UNRESOLVED
        and not retention_final
    )
    _require(
        (retention_outcome in RETENTION_OUTCOMES and retention_final)
        or retention_unresolved,
        "retention_blocked",
    )
    _require(backup.get("schema_version") == BACKUP_SCHEMA_VERSION, "backup_restore_failure")
    _require(restore_proof.get("backup_restore_ok") is True, "backup_restore_failure")
    _require(
        pack_manifest.get("fixture") is True
        or backup.get("independent_failure_domain") is True,
        "backup_restore_failure",
    )
    _require(
        pack_manifest.get("fixture") is True
        or restore_proof.get("proof_mode") == "portable_stream_decompress_hash",
        "backup_restore_failure",
    )
    _require(
        pack_manifest.get("inventory_receipt_sha256") == inventory.get("receipt_sha256"),
        "identity_roundtrip_failure",
    )
    _require(
        pack_manifest.get("object_set_sha256") == inventory.get("object_set_sha256"),
        "identity_roundtrip_failure",
    )
    _require(
        backup.get("pack_manifest_sha256") == pack_manifest.get("receipt_sha256"),
        "backup_restore_failure",
    )
    _require(
        restore_proof.get("pack_manifest_sha256") == pack_manifest.get("receipt_sha256"),
        "backup_restore_failure",
    )
    _require(
        restore_proof.get("object_set_sha256") == inventory.get("object_set_sha256"),
        "backup_restore_failure",
    )
    if retention_unresolved:
        # Retention-neutral compaction does not decide whether Cycle007 is a
        # future held-out asset or is eventually retired.  It replaces every
        # selected expanded original with two proved copies of the universal
        # lossless content pack; that compact custody asset remains protected
        # until #7427 makes the separate retention decision.
        _require(pack_manifest.get("pack_kind") == "content_compact", "retention_blocked")
        _require(pack_manifest.get("content_bodies_stored") is True, "retention_blocked")

    targets: list[dict[str, Any]] = []
    reclaim = 0
    retain_minimal = retention_outcome == RETAIN_MINIMAL_EVALUATION_ASSET
    for item in inventory["objects"]:
        selection = item["selection_class"]
        selection_classes = set(
            item.get("selection_classes", [selection])
        )
        # Under RETAIN_MINIMAL, only expansion-class originals are proposed for
        # deletion after compact+backup proof. Identity-bearing materialization
        # packets/custody remain until a later explicit authorization.
        expansion_only = bool(selection_classes) and selection_classes <= CONTENT_EXPANSION_CLASSES
        if retention_unresolved:
            authorized_class = "lossless_expanded_reclaim_candidate"
        elif retain_minimal and expansion_only:
            authorized_class = "expansion_reclaim_candidate"
        elif retention_outcome == RETIRE_CYCLE007:
            authorized_class = "full_retirement_candidate"
        else:
            authorized_class = "retain_until_separate_auth"
        link_set_closed = _link_set_closed(item)
        if not link_set_closed:
            authorized_class = "retain_until_link_set_closed"
        deletion_candidate = bool(
            (
                retention_unresolved
                or (retain_minimal and expansion_only)
                or retention_outcome == RETIRE_CYCLE007
            )
            and link_set_closed
        )
        allocation = int(item.get("inode_allocation_bytes", item["allocated_bytes"]))
        if deletion_candidate:
            reclaim += allocation
        targets.append(
            {
                "role_relative_path": item["role_relative_path"],
                "role_relative_paths": list(_item_relative_paths(item)),
                "selection_class": selection,
                "selection_classes": sorted(selection_classes),
                "sha256": item["sha256"],
                "allocated_bytes": allocation,
                "reclaimable_allocated_bytes": allocation if deletion_candidate else 0,
                "selected_path_count": item.get("selected_path_count", 1),
                "selected_link_count": item.get("selected_link_count", 1),
                "link_count": item.get("link_count", 1),
                "external_link_count": item.get("external_link_count", 0),
                "link_set_closed": link_set_closed,
                "deletion_candidate": deletion_candidate,
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
            "retention_outcome": retention_outcome,
            "retention_final": retention_final,
            "retention_neutral_lossless_compaction": retention_unresolved,
            "compact_custody_retained_pending_issue": 7427 if retention_unresolved else None,
            "retention_receipt_sha256": retention["receipt_sha256"],
            "inventory_receipt_sha256": inventory["receipt_sha256"],
            "pack_manifest_sha256": pack_manifest["receipt_sha256"],
            "backup_receipt_sha256": backup["receipt_sha256"],
            "backup_restore_proof_sha256": restore_proof["receipt_sha256"],
            "deletion_candidate_count": sum(1 for item in targets if item["deletion_candidate"]),
            "retained_object_count": sum(1 for item in targets if not item["deletion_candidate"]),
            "fully_closed_reclaimable_bytes": int(
                inventory.get("fully_closed_reclaimable_bytes", reclaim)
            ),
            "link_set_closed_candidate_count": sum(
                1 for item in targets if item["deletion_candidate"] and item["link_set_closed"]
            ),
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


def prove_content_pack_stream(
    inventory: Mapping[str, Any],
    pack_dir: Path,
    *,
    zstd_executable: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Exact content-pack round-trip by streaming decompress+hash; no second tree."""
    _directory(pack_dir, "pack_shape_failure")
    manifest = _read_json(pack_dir / "pack-manifest.json", "pack_shape_failure")
    _require(isinstance(manifest, Mapping), "pack_shape_failure")
    _require(manifest.get("schema_version") == PACK_SCHEMA_VERSION, "pack_shape_failure")
    _require_receipt(manifest, "pack_shape_failure")
    manifest_objects = manifest.get("objects")
    _require(isinstance(manifest_objects, list), "pack_shape_failure")
    _require(len(manifest_objects) == int(inventory.get("object_count", -1)), "pack_shape_failure")
    restored_objects: list[tuple[str, str]] = []
    by_rel = {item["role_relative_path"]: item for item in inventory["objects"]}
    seen_object_paths: set[str] = set()
    stored_payload_entries: list[dict[str, Any]] = []
    for raw_item in manifest_objects:
        _require(isinstance(raw_item, Mapping), "pack_shape_failure")
        item = raw_item
        object_relative_path = item.get("object_relative_path")
        _require(isinstance(object_relative_path, str), "pack_shape_failure")
        object_relative = Path(object_relative_path)
        _require(
            not object_relative.is_absolute() and ".." not in object_relative.parts,
            "pack_shape_failure",
        )
        _require(object_relative_path not in seen_object_paths, "pack_shape_failure")
        seen_object_paths.add(object_relative_path)
        object_path = pack_dir / object_relative
        _regular(object_path, "pack_shape_failure")
        _require(digest_file(object_path) == item["stored_sha256"], "identity_roundtrip_failure")
        sha, raw_size = _stream_digest_chunks(
            _iter_stored_raw_chunks(
                object_path,
                str(item["storage"]),
                zstd_executable,
            )
        )
        _require(sha == item["sha256"], "identity_roundtrip_failure")
        _require(raw_size == item["size_bytes"], "identity_roundtrip_failure")
        role_relative_path = item.get("role_relative_path")
        _require(isinstance(role_relative_path, str) and role_relative_path in by_rel, "identity_roundtrip_failure")
        inv = by_rel[role_relative_path]
        _require(sha == inv["sha256"], "identity_roundtrip_failure")
        restored_objects.extend((rel, sha) for rel in _item_relative_paths(item))
        stored_payload_entries.append(
            {
                "sha256": item["sha256"],
                "storage": item["storage"],
                "stored_sha256": item["stored_sha256"],
                "stored_size_bytes": int(item["stored_size_bytes"]),
            }
        )
    _require(
        len(restored_objects) == int(inventory.get("selected_path_count", len(restored_objects))),
        "identity_roundtrip_failure",
    )
    _require(
        int(manifest.get("total_stored_payload_bytes", -1))
        == sum(int(item["stored_size_bytes"]) for item in stored_payload_entries),
        "identity_roundtrip_failure",
    )
    _require(
        manifest.get("stored_payload_digest")
        == digest(canonical(sorted(stored_payload_entries, key=lambda entry: str(entry["sha256"]))),),
        "identity_roundtrip_failure",
    )
    expected_files = {"pack-manifest.json", *seen_object_paths}
    actual_files: set[str] = set()
    for dirpath, _dirnames, filenames in os.walk(pack_dir, followlinks=False):
        for filename in filenames:
            path = Path(dirpath) / filename
            if path.is_symlink() or not path.is_file():
                raise StorageCustodyError("pack_shape_failure")
            actual_files.add(path.relative_to(pack_dir).as_posix())
    _require(actual_files == expected_files, "pack_shape_failure")
    object_set = _pairs_digest(restored_objects)
    _require(object_set == inventory["object_set_sha256"], "identity_roundtrip_failure")
    _require(object_set == manifest["object_set_sha256"], "identity_roundtrip_failure")
    roundtrip = _receipt(
        {
            "schema_version": "phase3_cycle007_storage_roundtrip_v1",
            "outcome_sha256": OUTCOME_SHA256,
            "pack_manifest_sha256": manifest["receipt_sha256"],
            "object_count": len(manifest["objects"]),
            "object_set_sha256": object_set,
            "ordered_row_identity_commitment_sha256": inventory[
                "ordered_row_identity_commitment_sha256"
            ],
            "packet_count": inventory["packet_count"],
            "row_count": inventory["row_count"],
            "roundtrip_ok": True,
            "second_expanded_tree": False,
            "proof_mode": "stream_decompress_hash",
        }
    )
    identity_proof = _receipt(
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
            "second_expanded_tree": False,
            "proof_mode": "stream_decompress_hash",
        }
    )
    return roundtrip, identity_proof


def run_reversible_lane(
    bindings: Bindings,
    *,
    held_out_evaluation_proof: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute all safe reversible steps. Never deletes originals."""
    if not bindings.fixture:
        # Production topology is cross-host.  The legacy one-process lane
        # cannot prove a pre-copy workstation floor or independent restore and
        # is therefore fixture-only; use the three staged APIs above.
        raise StorageCustodyError("staged_lane_required")
    work = bindings.work_root / "cycle007-storage-lane"
    # A prior pack/backup is valuable custody state.  Never erase it to make a
    # rerun convenient; an operator can reconcile or explicitly provision a
    # fresh work root after inspecting the durable receipt.
    if os.path.lexists(work):
        raise StorageCustodyError("existing_lane_state")
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

    retention = decide_retention(
        inventory=inventory,
        held_out_evaluation_proof=held_out_evaluation_proof,
    )
    _atomic_write_json(work / "retention-decision.json", retention)

    destination_avail = available_bytes(bindings.work_root)
    retire = retention["retention_outcome"] == RETIRE_CYCLE007
    retention_final = retention.get("retention_final") is True
    # An unresolved decision gets the lossless content pack so either later
    # RETAIN or RETIRE reconciliation has a complete reversible representation.
    # A finalized RETIRE may still use the intentionally non-content lineage
    # pack; it is never selected while retention is unresolved.
    if retire and retention_final:
        # Lineage pack is tiny; forecast before write using a conservative 4 MiB bound.
        pre_compact = 4 * 1024 * 1024
        pre_backup = pre_compact
        preflight = None
    else:
        preflight = forecast_no_write_content_pack_bytes(inventory, bindings)
        pre_compact = int(preflight["compact_stored_allocated_bytes"])
        pre_backup = int(preflight["backup_stored_allocated_bytes"])

    backup_root = bindings.backup_root or bindings.work_root
    backup_root = backup_root.resolve()
    same_filesystem = os.stat(bindings.work_root).st_dev == os.stat(backup_root).st_dev
    backup_destination_avail = available_bytes(backup_root)
    pre_forecast = forecast_peak_temporary_bytes(
        inventory,
        compact_stored_bytes=pre_compact,
        backup_stored_bytes=pre_backup,
        destination_avail_bytes=destination_avail,
        backup_destination_avail_bytes=(None if same_filesystem else backup_destination_avail),
        second_expanded_tree=False,
    )
    _atomic_write_json(work / "peak-forecast-prewrite.json", pre_forecast)
    if not pre_forecast["capacity_sufficient_for_peak"] and not bindings.fixture:
        lane = _receipt(
            {
                "schema_version": LANE_RECEIPT_SCHEMA_VERSION,
                "outcome_sha256": OUTCOME_SHA256,
                "lane_complete": False,
                "stopped_at": "capacity_insufficient",
                "safe_failure_code": "capacity_insufficient",
                "deletion_authorized": False,
                "retention_outcome": retention["retention_outcome"],
                "packet_count": inventory["packet_count"],
                "row_count": inventory["row_count"],
                "object_count": inventory["object_count"],
                "total_allocated_bytes": inventory["total_allocated_bytes"],
                "filesystem_avail_bytes": destination_avail,
                "peak_temporary_bytes": pre_forecast["peak_temporary_bytes"],
                "capacity_sufficient_for_peak": False,
                "min_free_bytes": MIN_FREE_BYTES,
                "reconcile_receipt_sha256": reconcile["receipt_sha256"],
                "inventory_receipt_sha256": inventory["receipt_sha256"],
                "retention_receipt_sha256": retention["receipt_sha256"],
                "peak_forecast_receipt_sha256": pre_forecast["receipt_sha256"],
                "content_pack_preflight_receipt_sha256": (
                    preflight["receipt_sha256"] if preflight is not None else None
                ),
                "replacement_firewall_owner_issue": retention.get(
                    "replacement_firewall_owner_issue"
                ),
            }
        )
        _atomic_write_json(work / "lane-receipt.json", lane)
        return lane

    pack_dir = work / "pack"
    if retire and retention_final:
        pack_manifest = write_lineage_pack(inventory, pack_dir)
        expand_receipt, identity_proof = prove_lineage_against_sources(
            inventory, bindings, pack_manifest
        )
    else:
        pack_manifest = write_pack(inventory, bindings, pack_dir)
        expand_receipt, identity_proof = prove_content_pack_stream(
            inventory,
            pack_dir,
            zstd_executable=bindings.zstd_executable,
        )
    _atomic_write_json(work / "pack-manifest.receipt.json", pack_manifest)
    _atomic_write_json(work / "roundtrip.json", expand_receipt)
    _atomic_write_json(work / "identity-proof.json", identity_proof)

    # A configured backup root is kept as the destination even when a fixture
    # happens to share its device with work_root; the capacity forecast below
    # only treats it as independent when the device ids differ.
    backup_dir = (
        backup_root / "cycle007-storage-backup"
        if bindings.backup_root is not None
        else work / "backup"
    )
    backup = create_backup(pack_dir, backup_dir)
    restore_proof = prove_backup_byte_identity(pack_dir, backup_dir)
    backup["restore_proof_pending"] = False
    backup = _receipt({k: v for k, v in backup.items() if k != "receipt_sha256"})
    _atomic_write_json(work / "backup.json", backup)
    _atomic_write_json(work / "backup-restore-proof.json", restore_proof)

    forecast = forecast_peak_temporary_bytes(
        inventory,
        compact_stored_bytes=int(pack_manifest["total_stored_allocated_bytes"]),
        backup_stored_bytes=int(backup["backup_allocated_bytes"]),
        destination_avail_bytes=destination_avail,
        backup_destination_avail_bytes=(None if same_filesystem else backup_destination_avail),
        second_expanded_tree=False,
    )
    _atomic_write_json(work / "peak-forecast.json", forecast)
    if not forecast["capacity_sufficient_for_peak"] and not bindings.fixture:
        lane = _receipt(
            {
                "schema_version": LANE_RECEIPT_SCHEMA_VERSION,
                "outcome_sha256": OUTCOME_SHA256,
                "lane_complete": False,
                "stopped_at": "capacity_insufficient",
                "safe_failure_code": "capacity_insufficient",
                "deletion_authorized": False,
                "retention_outcome": retention["retention_outcome"],
                "packet_count": inventory["packet_count"],
                "row_count": inventory["row_count"],
                "object_count": inventory["object_count"],
                "total_allocated_bytes": inventory["total_allocated_bytes"],
                "compact_stored_allocated_bytes": pack_manifest["total_stored_allocated_bytes"],
                "filesystem_avail_bytes": destination_avail,
                "peak_temporary_bytes": forecast["peak_temporary_bytes"],
                "capacity_sufficient_for_peak": False,
                "reconcile_receipt_sha256": reconcile["receipt_sha256"],
                "inventory_receipt_sha256": inventory["receipt_sha256"],
                "retention_receipt_sha256": retention["receipt_sha256"],
                "pack_manifest_sha256": pack_manifest["receipt_sha256"],
                "peak_forecast_receipt_sha256": forecast["receipt_sha256"],
                "identity_proof_ok": identity_proof["identity_proof_ok"],
                "backup_restore_ok": restore_proof["backup_restore_ok"],
                "roundtrip_ok": expand_receipt["roundtrip_ok"],
                "replacement_firewall_owner_issue": retention.get(
                    "replacement_firewall_owner_issue"
                ),
            }
        )
        _atomic_write_json(work / "lane-receipt.json", lane)
        return lane

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
            "retention_status": retention.get("retention_status"),
            "retention_final": retention_final,
            "retention_reconciliation_required": not retention_final,
            "retention_neutral_lossless_compaction": not retention_final,
            "compact_custody_retained_pending_issue": 7427 if not retention_final else None,
            "retention_rationale_code": retention["rationale_code"],
            "replacement_firewall_owner_issue": retention.get("replacement_firewall_owner_issue"),
            "preserves_only_non_content_lineage_hashes": retention.get(
                "preserves_only_non_content_lineage_hashes"
            ),
            "pack_kind": pack_manifest.get("pack_kind"),
            "packet_count": inventory["packet_count"],
            "row_count": inventory["row_count"],
            "object_count": inventory["object_count"],
            "selected_path_count": inventory.get("selected_path_count"),
            "unique_inode_count": inventory.get("unique_inode_count"),
            "duplicate_selected_link_count": inventory.get("duplicate_selected_link_count"),
            "fully_closed_reclaimable_bytes": inventory.get(
                "fully_closed_reclaimable_bytes"
            ),
            "external_link_inode_count": inventory.get("external_link_inode_count"),
            "total_allocated_bytes": inventory["total_allocated_bytes"],
            "compact_stored_allocated_bytes": pack_manifest["total_stored_allocated_bytes"],
            "backup_allocated_bytes": backup["backup_allocated_bytes"],
            "reclaimed_byte_forecast": auth["reclaimed_byte_forecast"],
            "deletion_candidate_count": auth["deletion_candidate_count"],
            "filesystem_avail_bytes": destination_avail,
            "filesystem_total_bytes": filesystem_totals(bindings.work_root)["total_bytes"],
            "filesystem_used_bytes": filesystem_totals(bindings.work_root)["total_bytes"]
            - filesystem_totals(bindings.work_root)["free_bytes"],
            "filesystem_f_bavail_free_bytes": destination_avail,
            "min_free_bytes": MIN_FREE_BYTES,
            "peak_temporary_bytes": forecast["peak_temporary_bytes"],
            "capacity_sufficient_for_peak": forecast["capacity_sufficient_for_peak"],
            "second_expanded_tree": False,
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
            "retention_questions": retention.get("retention_questions"),
        }
    )
    _atomic_write_json(work / "lane-receipt.json", lane)
    return lane


def build_public_summary(
    lane: Mapping[str, Any],
    reconcile: Mapping[str, Any],
    *,
    fixture_lane: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Public, topology-free summary safe for issue/PR/repo reference artifacts."""
    bound = reconcile.get("private_binding_state") == "BOUND"
    fixture = fixture_lane or {}
    retention_outcome = (
        lane["retention_outcome"]
        if "retention_outcome" in lane
        else fixture.get("retention_outcome")
    )
    body: dict[str, Any] = {
        "schema_version": "phase3_cycle007_storage_public_summary_v1",
        "outcome_sha256": OUTCOME_SHA256,
        "handoff_receipt_sha256": HANDOFF_RECEIPT_SHA256,
        "issue": 7434,
        "epic": 7423,
        "private_binding_state": reconcile.get("private_binding_state"),
        "retention_outcome": retention_outcome,
        "retention_rationale_code": lane.get("retention_rationale_code")
        or fixture.get("retention_rationale_code"),
        "deletion_authorized": False,
        "issue_7434_is_not_deletion_authorization": True,
        "authorization_gate": "operator_explicit_authorization_required",
        "public_packet_count": EXPECTED_PACKET_COUNT,
        "public_row_count": EXPECTED_ROW_COUNT,
        "labeling_state": "OFF",
        "provider_calls": 0,
        "provider_derived_training_labels": 0,
        # This is deliberately unknown until #7427 supplies a source-qualified
        # firewall decision.  ``false`` would be a fabricated negative claim.
        "evaluation_firewall_requires_cycle007_identities": (
            True if retention_outcome == RETAIN_MINIMAL_EVALUATION_ASSET else None
        ),
        "production_inventory_frozen": bool(bound and lane.get("inventory_receipt_sha256")),
        "fixture_representation_proven": bool(
            fixture.get("lane_complete")
            or (
                fixture.get("pack_kind") == "content_compact"
                and fixture.get("identity_proof_ok") is True
                and fixture.get("backup_restore_ok") is True
                and fixture.get("roundtrip_ok") is True
            )
        ),
        "stopped_at": lane.get("stopped_at"),
        "safe_failure_code": lane.get("safe_failure_code") or reconcile.get("safe_failure_code"),
        "reconcile_receipt_sha256": reconcile.get("receipt_sha256"),
        "retention_receipt_sha256": lane.get("retention_receipt_sha256")
        or fixture.get("retention_receipt_sha256"),
        "replacement_firewall_owner_issue": lane.get("replacement_firewall_owner_issue")
        or fixture.get("replacement_firewall_owner_issue"),
        "preserves_only_non_content_lineage_hashes": lane.get(
            "preserves_only_non_content_lineage_hashes"
        )
        if lane.get("preserves_only_non_content_lineage_hashes") is not None
        else fixture.get("preserves_only_non_content_lineage_hashes", False),
        "pack_kind": lane.get("pack_kind") or fixture.get("pack_kind"),
        "second_expanded_tree": False,
    }
    if bound and lane.get("lane_complete"):
        body.update(
            {
                "production_packet_count": lane.get("packet_count"),
                "production_row_count": lane.get("row_count"),
                "production_object_count": lane.get("object_count"),
                "production_total_allocated_bytes": lane.get("total_allocated_bytes"),
                "production_compact_stored_allocated_bytes": lane.get(
                    "compact_stored_allocated_bytes"
                ),
                "production_reclaimed_byte_forecast": lane.get("reclaimed_byte_forecast"),
                "production_deletion_candidate_count": lane.get("deletion_candidate_count"),
                "production_peak_temporary_bytes": lane.get("peak_temporary_bytes"),
                "production_capacity_sufficient_for_peak": lane.get(
                    "capacity_sufficient_for_peak"
                ),
                "production_identity_proof_ok": lane.get("identity_proof_ok"),
                "production_backup_restore_ok": lane.get("backup_restore_ok"),
                "production_roundtrip_ok": lane.get("roundtrip_ok"),
                "production_lane_receipt_sha256": lane.get("receipt_sha256"),
                "production_min_free_bytes": lane.get("min_free_bytes"),
            }
        )
    if fixture:
        fixture_fields = {
            "fixture_lane_complete": fixture.get("lane_complete"),
            "fixture_packet_count": fixture.get("packet_count"),
            "fixture_row_count": fixture.get("row_count"),
            "fixture_object_count": fixture.get("object_count"),
            "fixture_total_allocated_bytes": fixture.get("total_allocated_bytes"),
            "fixture_compact_stored_allocated_bytes": fixture.get(
                "compact_stored_allocated_bytes"
            ),
            "fixture_reclaimed_byte_forecast": fixture.get("reclaimed_byte_forecast"),
            "fixture_deletion_candidate_count": fixture.get("deletion_candidate_count"),
            "fixture_identity_proof_ok": fixture.get("identity_proof_ok"),
            "fixture_backup_restore_ok": fixture.get("backup_restore_ok"),
            "fixture_roundtrip_ok": fixture.get("roundtrip_ok"),
            "fixture_lane_receipt_sha256": fixture.get("receipt_sha256"),
            "fixture_peak_temporary_bytes": fixture.get("peak_temporary_bytes"),
            "fixture_capacity_sufficient_for_peak": fixture.get(
                "capacity_sufficient_for_peak"
            ),
        }
        body.update({key: value for key, value in fixture_fields.items() if value is not None})
    summary = _receipt(body)
    leaked = public_summary_forbidden_fs_keys(summary)
    if leaked:
        raise StorageCustodyError("path_disclosure_refused")
    return summary


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

    real_bindings_configured = bool(
        os.environ.get(REAL_CONFIG_ENV)
        or os.environ.get(REAL_MATERIALIZATION_ENV)
        or os.environ.get(REAL_EVIDENCE_ENV)
    )
    if (
        args.action == "reconcile"
        and not args.fixture
        and args.materialization is None
        and not real_bindings_configured
    ):
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
        summary = build_public_summary(
            lane,
            reconcile,
            fixture_lane=lane if bindings.fixture else None,
        )
        if args.public_summary_out is not None:
            _atomic_write_json(args.public_summary_out, summary)
        print(json.dumps({
            "text_free": True,
            "lane_complete": lane.get("lane_complete"),
            "stopped_at": lane.get("stopped_at"),
            "safe_failure_code": lane.get("safe_failure_code"),
            "retention_outcome": lane.get("retention_outcome"),
            "replacement_firewall_owner_issue": lane.get("replacement_firewall_owner_issue"),
            "pack_kind": lane.get("pack_kind"),
            "deletion_authorized": False,
            "packet_count": lane.get("packet_count"),
            "row_count": lane.get("row_count"),
            "object_count": lane.get("object_count"),
            "total_allocated_bytes": lane.get("total_allocated_bytes"),
            "compact_stored_allocated_bytes": lane.get("compact_stored_allocated_bytes"),
            "reclaimed_byte_forecast": lane.get("reclaimed_byte_forecast"),
            "deletion_candidate_count": lane.get("deletion_candidate_count"),
            "peak_temporary_bytes": lane.get("peak_temporary_bytes"),
            "capacity_sufficient_for_peak": lane.get("capacity_sufficient_for_peak"),
            "identity_proof_ok": lane.get("identity_proof_ok"),
            "backup_restore_ok": lane.get("backup_restore_ok"),
            "roundtrip_ok": lane.get("roundtrip_ok"),
            "second_expanded_tree": False,
            "receipt_sha256": lane.get("receipt_sha256"),
            "public_summary_sha256": summary["receipt_sha256"],
        }, sort_keys=True))
        return 0 if lane.get("lane_complete") else 2

    if args.action == "public-summary":
        lane_path = bindings.work_root / "cycle007-storage-lane" / "lane-receipt.json"
        reconcile_path = bindings.work_root / "cycle007-storage-lane" / "reconcile.json"
        lane = _read_json(lane_path)
        reconcile = _read_json(reconcile_path)
        summary = build_public_summary(
            lane,
            reconcile,
            fixture_lane=lane if bindings.fixture else None,
        )
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
