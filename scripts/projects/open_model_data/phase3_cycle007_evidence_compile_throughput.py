#!/usr/bin/env python3
"""Durable, text-free sealed-packet resume custody for Cycle 007.

The evidence compiler remains serial and the frozen evidence protocol is
unchanged. This module only makes a validated sealed packet prefix durable
across process failure and installs the finished bundle with one no-replace
directory rename.
"""

from __future__ import annotations

import contextlib
import ctypes
import fcntl
import json
import os
import re
import stat
import sys
import tempfile
from collections import Counter
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any

from scripts.projects.open_model_data import phase3_cycle007_evidence_compiler as compiler
from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract

ACTIVATION_STATE = "resume_only_reviewed_v1"
PROGRESS_SCHEMA_VERSION = "phase3_cycle007_compile_progress_v2"
EVALUATION_CYCLE_ID = compiler.EVALUATION_CYCLE_ID
CALL_CHAIN_SEED = "phase3-cycle007-mcp-tool-call-chain-v1"
SIDECAR_NAME_RE = re.compile(r"sidecar-(\d{4})\.json\Z")
TEMP_SIDECAR_NAME_RE = re.compile(r"\.sidecar-(\d{4})\.json\..+\Z")
TEMP_PROGRESS_NAME_RE = re.compile(r"\.progress\.json\..+\Z")
PRODUCTION_PACKET_WORKERS = 1
MAX_REVIEWED_PACKET_WORKERS = 1
PROGRESS_NAME = "progress.json"
LOCK_NAME = "compile.lock"
BUNDLE_NAME = "bundle"

PROGRESS_REQUIRED_KEYS = frozenset(
    {
        "schema_version",
        "text_free",
        "evaluation_cycle_id",
        "activation_state",
        "sealed_packet_count",
        "next_packet_index",
        "target_packet_count",
        "target_row_count",
        "last_sealed_sidecar_sha256",
        "last_sealed_sidecar_id",
        "identity_sha256",
        "mcp_transport_attestation",
        "mcp_call_records",
        "progress_sha256",
    }
)
CALL_RECORD_KEYS = frozenset({"ordinal", "tool", "arguments_sha256", "response_sha256"})
PRIVATE_PROGRESS_KEYS = frozenset(
    {
        "query",
        "row_identity",
        "locator",
        "negative_reason",
        "retrieval_payloads",
        "source_text",
        "unit_id",
        "path",
        "endpoint",
        "host",
        "prompt",
        "response",
        "label",
    }
)
_IDENTITY_COMPARE_KEYS = (
    "tokenizer_id",
    "tokenizer_version",
    "code_hashes",
    "server_code_sha256",
    "sources_db_sha256",
    "vesum_db_sha256",
)


class ThroughputResumeError(ValueError):
    """Closed, text-free resume failure."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


ThroughputScaffoldingError = ThroughputResumeError


def initial_call_commitment() -> str:
    return contract.sha256_text(CALL_CHAIN_SEED)


def sidecar_filename(packet_index: int) -> str:
    _require_count(packet_index, minimum=1)
    return f"sidecar-{packet_index:04d}.json"


def resume_root_for(output_dir: Path) -> Path:
    return output_dir.with_name(f".{output_dir.name}.resume-v1")


def bundle_dir_for(output_dir: Path) -> Path:
    return resume_root_for(output_dir) / BUNDLE_NAME


def build_resume_identity(
    expected_identity: Mapping[str, Any],
    *,
    source_package_binding: Mapping[str, Any] | None,
    packet_bindings: Sequence[Mapping[str, Any] | None],
    residual_lane_packets: Sequence[bool],
    target_packet_count: int,
    target_row_count: int,
) -> dict[str, Any]:
    missing = [key for key in _IDENTITY_COMPARE_KEYS if key not in expected_identity]
    if missing:
        raise ThroughputResumeError("identity_incomplete")
    return {
        "resume_implementation_sha256": contract.sha256_file(Path(__file__)),
        "expected_identity": {key: expected_identity[key] for key in _IDENTITY_COMPARE_KEYS},
        "source_package_binding_sha256": contract.sha256_value(source_package_binding),
        "packet_bindings_sha256": contract.sha256_value(list(packet_bindings)),
        "residual_lane_packets_sha256": contract.sha256_value(list(residual_lane_packets)),
        "target_packet_count": target_packet_count,
        "target_row_count": target_row_count,
    }


def identity_sha256(resume_identity: Mapping[str, Any]) -> str:
    return contract.sha256_value(resume_identity)


def extend_serial_call_commitment(
    prior_commitment: str,
    calls: Sequence[Mapping[str, Any]],
    *,
    starting_ordinal: int,
) -> tuple[str, int]:
    if not _is_sha256(prior_commitment):
        raise ThroughputResumeError("call_commitment_invalid")
    _require_count(starting_ordinal, minimum=1)
    commitment = prior_commitment
    ordinal = starting_ordinal
    for raw in calls:
        if not isinstance(raw, Mapping) or set(raw) != CALL_RECORD_KEYS:
            raise ThroughputResumeError("call_record_invalid")
        if raw.get("ordinal") != ordinal:
            raise ThroughputResumeError("call_ordinal_invalid")
        if not isinstance(raw.get("tool"), str) or not raw["tool"]:
            raise ThroughputResumeError("call_record_invalid")
        if not _is_sha256(raw.get("arguments_sha256")) or not _is_sha256(raw.get("response_sha256")):
            raise ThroughputResumeError("call_record_invalid")
        commitment = contract.sha256_text(commitment + "\n" + contract.canonical_json(dict(raw)))
        ordinal += 1
    return commitment, ordinal


def validate_transport_state(
    attestation: Mapping[str, Any],
    call_records: Sequence[Mapping[str, Any]],
    *,
    expected_transport: str,
    expected_endpoint_sha256: str,
    expected_tool_set_sha256: str,
) -> None:
    required = {
        "schema_version",
        "transport",
        "endpoint_sha256",
        "required_tool_set_sha256",
        "tool_call_count",
        "counts_by_tool",
        "server_identity_call_count",
        "ordered_call_commitment_sha256",
    }
    if not isinstance(attestation, Mapping) or set(attestation) != required:
        raise ThroughputResumeError("transport_shape_invalid")
    if attestation.get("schema_version") != "phase3_cycle007_mcp_transport_attestation_v1":
        raise ThroughputResumeError("transport_schema_drift")
    if (
        attestation.get("transport") != expected_transport
        or attestation.get("endpoint_sha256") != expected_endpoint_sha256
        or attestation.get("required_tool_set_sha256") != expected_tool_set_sha256
    ):
        raise ThroughputResumeError("transport_identity_drift")
    count = attestation.get("tool_call_count")
    _require_count(count)
    if count != len(call_records):
        raise ThroughputResumeError("transport_count_drift")
    commitment, next_ordinal = extend_serial_call_commitment(
        initial_call_commitment(), call_records, starting_ordinal=1
    )
    if next_ordinal != count + 1 or commitment != attestation.get("ordered_call_commitment_sha256"):
        raise ThroughputResumeError("transport_commitment_drift")
    counts = Counter(str(record["tool"]) for record in call_records)
    if dict(sorted(counts.items())) != attestation.get("counts_by_tool"):
        raise ThroughputResumeError("transport_tool_counts_drift")
    if counts.get("mcp_server_identity", 0) != attestation.get("server_identity_call_count"):
        raise ThroughputResumeError("transport_identity_count_drift")


def build_progress_receipt(
    *,
    sealed_packet_count: int,
    target_packet_count: int,
    target_row_count: int,
    last_sealed_sidecar_sha256: str | None,
    last_sealed_sidecar_id: str | None,
    resume_identity: Mapping[str, Any],
    mcp_transport_attestation: Mapping[str, Any],
    mcp_call_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    _require_count(sealed_packet_count)
    _require_count(target_packet_count, minimum=1)
    _require_count(target_row_count, minimum=1)
    if sealed_packet_count > target_packet_count:
        raise ThroughputResumeError("sealed_prefix_overflow")
    if sealed_packet_count == 0:
        if last_sealed_sidecar_sha256 is not None or last_sealed_sidecar_id is not None:
            raise ThroughputResumeError("progress_last_sidecar_invalid")
    elif not _is_sha256(last_sealed_sidecar_sha256) or not isinstance(last_sealed_sidecar_id, str):
        raise ThroughputResumeError("progress_last_sidecar_invalid")
    validate_transport_state(
        mcp_transport_attestation,
        mcp_call_records,
        expected_transport=str(mcp_transport_attestation.get("transport")),
        expected_endpoint_sha256=str(mcp_transport_attestation.get("endpoint_sha256")),
        expected_tool_set_sha256=str(mcp_transport_attestation.get("required_tool_set_sha256")),
    )
    receipt = {
        "schema_version": PROGRESS_SCHEMA_VERSION,
        "text_free": True,
        "evaluation_cycle_id": EVALUATION_CYCLE_ID,
        "activation_state": ACTIVATION_STATE,
        "sealed_packet_count": sealed_packet_count,
        "next_packet_index": sealed_packet_count + 1,
        "target_packet_count": target_packet_count,
        "target_row_count": target_row_count,
        "last_sealed_sidecar_sha256": last_sealed_sidecar_sha256,
        "last_sealed_sidecar_id": last_sealed_sidecar_id,
        "identity_sha256": identity_sha256(resume_identity),
        "mcp_transport_attestation": dict(mcp_transport_attestation),
        "mcp_call_records": [dict(record) for record in mcp_call_records],
    }
    _reject_private_keys_recursive(receipt)
    receipt["progress_sha256"] = contract.sha256_value(receipt)
    return receipt


def validate_progress_receipt(
    receipt: Mapping[str, Any],
    resume_identity: Mapping[str, Any],
    *,
    expected_transport: str,
    expected_endpoint_sha256: str,
    expected_tool_set_sha256: str,
    sealed_packet_count: int | None = None,
    last_sealed_sidecar_sha256: str | None = None,
) -> None:
    if not isinstance(receipt, Mapping) or set(receipt) != PROGRESS_REQUIRED_KEYS:
        raise ThroughputResumeError("progress_shape_invalid")
    _reject_private_keys_recursive(receipt)
    if receipt.get("schema_version") != PROGRESS_SCHEMA_VERSION:
        raise ThroughputResumeError("progress_schema_drift")
    if receipt.get("text_free") is not True or receipt.get("evaluation_cycle_id") != EVALUATION_CYCLE_ID:
        raise ThroughputResumeError("progress_identity_drift")
    if receipt.get("activation_state") != ACTIVATION_STATE:
        raise ThroughputResumeError("progress_activation_drift")
    unsigned = {key: value for key, value in receipt.items() if key != "progress_sha256"}
    if receipt.get("progress_sha256") != contract.sha256_value(unsigned):
        raise ThroughputResumeError("progress_hash_drift")
    if receipt.get("identity_sha256") != identity_sha256(resume_identity):
        raise ThroughputResumeError("identity_drift")
    sealed = receipt.get("sealed_packet_count")
    _require_count(sealed)
    if receipt.get("next_packet_index") != sealed + 1:
        raise ThroughputResumeError("progress_next_index_mismatch")
    if sealed_packet_count is not None and sealed != sealed_packet_count:
        raise ThroughputResumeError("progress_prefix_mismatch")
    if last_sealed_sidecar_sha256 is not None and receipt.get("last_sealed_sidecar_sha256") != last_sealed_sidecar_sha256:
        raise ThroughputResumeError("progress_last_sidecar_mismatch")
    records = receipt.get("mcp_call_records")
    attestation = receipt.get("mcp_transport_attestation")
    if not isinstance(records, list) or not isinstance(attestation, Mapping):
        raise ThroughputResumeError("transport_shape_invalid")
    validate_transport_state(
        attestation,
        records,
        expected_transport=expected_transport,
        expected_endpoint_sha256=expected_endpoint_sha256,
        expected_tool_set_sha256=expected_tool_set_sha256,
    )


def read_progress(path: Path) -> dict[str, Any]:
    _assert_private_path(path, directory=False)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ThroughputResumeError("progress_unreadable") from exc
    if not isinstance(value, dict):
        raise ThroughputResumeError("progress_shape_invalid")
    return value


def write_progress(root: Path, receipt: Mapping[str, Any]) -> None:
    _assert_private_path(root, directory=True)
    destination = root / PROGRESS_NAME
    encoded = (contract.canonical_json(receipt) + "\n").encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{PROGRESS_NAME}.", dir=root)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            os.fchmod(handle.fileno(), compiler.PRIVATE_FILE_MODE)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        _fsync_directory(root)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def prepare_resume_root(output_dir: Path) -> tuple[Path, Path]:
    parent = output_dir.parent
    _assert_private_path(parent, directory=True)
    root = resume_root_for(output_dir)
    tombstone = root.with_name(f"{root.name}.cleanup")
    if os.path.lexists(tombstone):
        raise ThroughputResumeError("cleanup_tombstone_exists")
    if os.path.lexists(root):
        _assert_private_path(root, directory=True)
    else:
        try:
            os.mkdir(root, compiler.PRIVATE_DIR_MODE)
        except FileExistsError:
            _assert_private_path(root, directory=True)
        _fsync_directory(parent)
        _assert_private_path(root, directory=True)
    bundle = root / BUNDLE_NAME
    if os.path.lexists(bundle):
        _assert_private_path(bundle, directory=True)
    else:
        try:
            os.mkdir(bundle, compiler.PRIVATE_DIR_MODE)
        except FileExistsError:
            _assert_private_path(bundle, directory=True)
        _fsync_directory(root)
        _assert_private_path(bundle, directory=True)
    return root, bundle


def inspect_resume_root(root: Path) -> None:
    """Reject foreign root entries and discard one interrupted progress temp."""
    _assert_private_path(root, directory=True)
    progress_temps: list[Path] = []
    for path in sorted(root.iterdir()):
        if path.name in {BUNDLE_NAME, PROGRESS_NAME, LOCK_NAME}:
            _assert_private_path(path, directory=path.name == BUNDLE_NAME)
        elif TEMP_PROGRESS_NAME_RE.fullmatch(path.name):
            _assert_private_path(path, directory=False)
            progress_temps.append(path)
        else:
            raise ThroughputResumeError("resume_foreign_entry")
    if len(progress_temps) > 1:
        raise ThroughputResumeError("resume_temp_invalid")
    if progress_temps:
        progress_temps[0].unlink()
        _fsync_directory(root)


@contextlib.contextmanager
def exclusive_resume_lock(root: Path) -> Iterator[None]:
    _assert_private_path(root, directory=True)
    path = root / LOCK_NAME
    flags = os.O_CREAT | os.O_RDWR
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, compiler.PRIVATE_FILE_MODE)
    try:
        os.fchmod(descriptor, compiler.PRIVATE_FILE_MODE)
        _assert_private_stat(os.fstat(descriptor), directory=False)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ThroughputResumeError("compiler_lock_held") from exc
        yield
    finally:
        with contextlib.suppress(OSError):
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def inspect_sealed_prefix(bundle: Path) -> tuple[list[int], int]:
    _assert_private_path(bundle, directory=True)
    indexes: list[int] = []
    temp_paths: list[tuple[int, Path]] = []
    for path in sorted(bundle.iterdir()):
        if path.is_symlink():
            raise ThroughputResumeError("resume_symlink")
        sidecar_match = SIDECAR_NAME_RE.fullmatch(path.name)
        temp_match = TEMP_SIDECAR_NAME_RE.fullmatch(path.name)
        if sidecar_match:
            _assert_private_path(path, directory=False)
            indexes.append(int(sidecar_match.group(1)))
        elif temp_match:
            _assert_private_path(path, directory=False)
            temp_paths.append((int(temp_match.group(1)), path))
        elif path.name == "manifest.json":
            _assert_private_path(path, directory=False)
        else:
            raise ThroughputResumeError("resume_foreign_entry")
    sealed = assert_consecutive_prefix(indexes)
    if len(temp_paths) > 1 or (temp_paths and temp_paths[0][0] != sealed + 1):
        raise ThroughputResumeError("resume_temp_invalid")
    if temp_paths:
        temp_paths[0][1].unlink()
        _fsync_directory(bundle)
    return indexes, sealed


def assert_consecutive_prefix(indexes: Sequence[int]) -> int:
    if list(indexes) != list(range(1, len(indexes) + 1)):
        raise ThroughputResumeError("sealed_prefix_gap")
    return indexes[-1] if indexes else 0


def load_sidecar(path: Path) -> dict[str, Any]:
    _assert_private_path(path, directory=False)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ThroughputResumeError("sidecar_unreadable") from exc
    if not isinstance(value, dict):
        raise ThroughputResumeError("sidecar_shape_invalid")
    return value


def atomic_install_bundle(bundle: Path, output_dir: Path) -> None:
    _assert_private_path(bundle, directory=True)
    if os.path.lexists(output_dir):
        raise ThroughputResumeError("output_exists")
    source_parent = bundle.parent
    _rename_directory_noreplace(bundle, output_dir)
    _fsync_directory(source_parent)
    _fsync_directory(output_dir.parent)


def _rename_directory_noreplace(source_path: Path, destination_path: Path) -> None:
    """Atomically rename one directory while refusing any destination."""
    source = os.fsencode(source_path)
    destination = os.fsencode(destination_path)
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform.startswith("linux") and hasattr(libc, "renameat2"):
        rename = libc.renameat2
        rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        result = rename(-100, source, -100, destination, 1)
    elif sys.platform == "darwin" and hasattr(libc, "renamex_np"):
        rename = libc.renamex_np
        rename.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        result = rename(source, destination, 0x00000004)
    else:
        raise ThroughputResumeError("atomic_noreplace_unavailable")
    if result != 0:
        error = ctypes.get_errno()
        if error in {17, 39}:
            raise ThroughputResumeError("output_exists")
        raise OSError(error, os.strerror(error))


def cleanup_resume_metadata(root: Path) -> None:
    """Atomically retire the live root, then best-effort remove its tombstone.

    Once the rename commits, later invocations validate the installed output
    without depending on cleanup metadata. A crash during unlink/rmdir can
    therefore leave only an inert tombstone, never a recovery blocker.
    """
    tombstone = root.with_name(f"{root.name}.cleanup")
    if os.path.lexists(tombstone):
        raise ThroughputResumeError("cleanup_tombstone_exists")
    _rename_directory_noreplace(root, tombstone)
    _fsync_directory(root.parent)
    _remove_cleanup_tombstone(tombstone)


def reap_cleanup_tombstone(root: Path) -> bool:
    """Finish an interrupted cleanup without racing a still-live cleaner."""
    tombstone = root.with_name(f"{root.name}.cleanup")
    if not os.path.lexists(tombstone):
        return False
    _assert_private_path(tombstone, directory=True)
    lock_path = tombstone / LOCK_NAME
    descriptor: int | None = None
    if os.path.lexists(lock_path):
        flags = os.O_RDWR
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(lock_path, flags)
        _assert_private_stat(os.fstat(descriptor), directory=False)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(descriptor)
            return False
    try:
        _remove_cleanup_tombstone(tombstone)
    finally:
        if descriptor is not None:
            with contextlib.suppress(OSError):
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)
    return True


def _remove_cleanup_tombstone(tombstone: Path) -> None:
    allowed = {PROGRESS_NAME, LOCK_NAME}
    try:
        entries = list(tombstone.iterdir())
    except FileNotFoundError:
        return
    for path in entries:
        if path.name not in allowed:
            raise ThroughputResumeError("cleanup_foreign_entry")
        if os.path.lexists(path):
            _assert_private_path(path, directory=False)
    for name in (PROGRESS_NAME, LOCK_NAME):
        path = tombstone / name
        if os.path.lexists(path):
            _assert_private_path(path, directory=False)
            path.unlink()
    with contextlib.suppress(FileNotFoundError):
        os.rmdir(tombstone)
    _fsync_directory(tombstone.parent)


def assert_private_tree(root: Path) -> None:
    _assert_private_path(root, directory=True)
    for path in sorted(root.rglob("*")):
        _assert_private_path(path, directory=path.is_dir())


def bound_packet_workers(requested: int, *, authorized: bool = False) -> int:
    del authorized
    if requested != 1:
        raise ThroughputResumeError("packet_workers_not_authorized")
    return 1


def packet_loop_is_serial() -> bool:
    return True


def _assert_private_path(path: Path, *, directory: bool) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        raise ThroughputResumeError("resume_path_unavailable") from exc
    if stat.S_ISLNK(info.st_mode):
        raise ThroughputResumeError("resume_symlink")
    _assert_private_stat(info, directory=directory)


def _assert_private_stat(info: os.stat_result, *, directory: bool) -> None:
    wanted_type = stat.S_ISDIR if directory else stat.S_ISREG
    if not wanted_type(info.st_mode):
        raise ThroughputResumeError("resume_path_type_invalid")
    expected_mode = compiler.PRIVATE_DIR_MODE if directory else compiler.PRIVATE_FILE_MODE
    if stat.S_IMODE(info.st_mode) != expected_mode:
        raise ThroughputResumeError("resume_mode_drift")
    if info.st_uid != os.geteuid():
        raise ThroughputResumeError("resume_owner_drift")


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _require_count(value: Any, *, minimum: int = 0) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ThroughputResumeError("count_invalid")


def _reject_private_keys_recursive(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in PRIVATE_PROGRESS_KEYS:
                raise ThroughputResumeError("progress_not_text_free")
            _reject_private_keys_recursive(child)
    elif isinstance(value, list):
        for child in value:
            _reject_private_keys_recursive(child)
