#!/usr/bin/env python3
"""Materialize a fresh Cycle-007 successor from the restored Cycle-005 package.

Per ``batch_state/phase3-cycle007-source-grounded-amendment-v1.md``: the sole
held-out source remains the restored Cycle-005 custody package. Source rows
are copied into a new transactional package with their ``evaluation_cycle_id``
changed from Cycle 005 to Cycle 007. This module never reads, requires, or
copies anything from a Cycle-006 successor package — it reads only the same
Cycle-005 custody receipt / label manifest / packet files that Cycle 006 also
read, and it starts both model lanes at zero: no labels, no provider
artifacts, no prompts are produced here. Row order, packet order, packet
size, lane order, and unit identity are preserved byte-for-value; the only
row field this materializer changes is ``evaluation_cycle_id``.

The default CLI is pinned to the real Cycle-005 bindings. ``--fixture`` is a
separate synthetic-only mode used by the public behavior proof; it never
relaxes shape, ordering, identity, permission, or atomicity checks.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import stat
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract

CYCLE005 = "phase3-v2-1-evaluation-cycle-005"
CYCLE007 = "phase3-v2-1-evaluation-cycle-007"

# The Cycle-005 restored custody package is the same frozen input Cycle 006
# read; these are its already-public identity pins (see
# batch_state/phase3-materialize-cycle006-successor-v2.py), not a Cycle-007
# secret.
SOURCE_CUSTODY_SHA256 = "7047e8459433376f3b690cfc2f15e115d77a701e79afb0ef2db184b44ea14726"
SOURCE_MANIFEST_SHA256 = "b8d290ffe945a6cc5d36345cbf234ccf79a7df98cb4199ffad0b778cd2b69fab"
ORDERED_IDENTITY_COMMITMENT_SHA256 = "331fd7fbc42e43cb3c218d9c2b790df060c0a553ab7c3a7b3b557f9f2bc3c419"

REAL_ROW_COUNTS = {"clean_label": 2_000, "residual_label": 8_159}
REAL_PACKET_COUNTS = {"clean_label": 40, "residual_label": 164}
LANE_ORDER = ("clean_label", "residual_label")
PACKET_SIZE = 50
PRIVATE_DIR_MODE = 0o700
PRIVATE_FILE_MODE = 0o600

# Cycle 007 is evidence-foundation only at this stage: no prompts, no raw/
# response/sealed/transport/assembled label directories are ever produced.
OUTPUT_TOP_LEVEL = frozenset({"clean_label", "residual_label", "custody-receipt.json", "manifest.json"})
FORBIDDEN_ROW_KEYS = frozenset(
    {"decision_code", "clean_modern_standard_prose", "modern_genre_id", "label", "labels", "reviewer"}
)

FAILURE_CODES = frozenset(
    {
        "source_binding_drift",
        "source_shape_failure",
        "manifest_binding_drift",
        "packet_binding_drift",
        "packet_order_failure",
        "identity_uniqueness_failure",
        "ordered_identity_commitment_failure",
        "label_leak_detected",
        "fixture_flag_required",
        "output_exists",
        "path_overlap",
        "transaction_failure",
        "path_disclosure_refused",
        "source_mode_drift",
    }
)

# Amendment step 15: in real (non-fixture) mode, private source/output paths
# are never taken from argv. A protected environment variable pair, or a
# mode-0600 JSON config file (``{"source": ..., "output": ...}``) named by
# ``REAL_CONFIG_ENV``, is the only way to bind them. Public fixture mode may
# still pass ``--source``/``--output`` explicitly.
REAL_SOURCE_ENV = "PHASE3_CYCLE007_SOURCE_PACKAGE"
REAL_OUTPUT_ENV = "PHASE3_CYCLE007_OUTPUT_PACKAGE"
REAL_CONFIG_ENV = "PHASE3_CYCLE007_MATERIALIZER_CONFIG"


class MaterializationError(ValueError):
    """A fail-closed Cycle 007 materialization error with a text-free public code."""

    def __init__(self, code: str) -> None:
        self.code = code if code in FAILURE_CODES else "transaction_failure"
        super().__init__(self.code)


Error = MaterializationError


@dataclass(frozen=True)
class Config:
    """Validated invocation configuration.

    ``strict_counts`` is derived from ``fixture``; a real (non-fixture)
    invocation can never override the frozen 204-packet/10,159-row counts.
    """

    source: Path
    output: Path
    fixture: bool = False
    strict_counts: bool | None = None

    def __post_init__(self) -> None:
        strict = not self.fixture if self.strict_counts is None else self.strict_counts
        if strict and self.fixture:
            strict = False
        object.__setattr__(self, "strict_counts", strict)


def canonical(value: Any) -> bytes:
    return (contract.canonical_json(value) + "\n").encode("utf-8")


def digest(data: bytes) -> str:
    return contract.sha256_bytes(data)


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise MaterializationError(code)


def _pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise MaterializationError("source_shape_failure")
        result[key] = value
    return result


def _regular(path: Path, code: str = "source_shape_failure") -> None:
    try:
        entry = path.lstat()
    except OSError:
        raise MaterializationError(code) from None
    if path.is_symlink() or not stat.S_ISREG(entry.st_mode):
        raise MaterializationError(code)


def _directory(path: Path, code: str = "source_shape_failure") -> None:
    try:
        entry = path.lstat()
    except OSError:
        raise MaterializationError(code) from None
    if path.is_symlink() or not stat.S_ISDIR(entry.st_mode):
        raise MaterializationError(code)


def _read_regular(path: Path, code: str) -> bytes:
    _regular(path, code)
    try:
        return path.read_bytes()
    except OSError:
        raise MaterializationError(code) from None


def strict_json(path: Path, code: str = "source_shape_failure") -> Any:
    raw = _read_regular(path, code)
    try:
        return json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=_pairs_hook)
    except (UnicodeDecodeError, json.JSONDecodeError, MaterializationError):
        raise MaterializationError(code) from None


def _hash_receipt(value: Mapping[str, Any]) -> str:
    return digest(canonical({key: item for key, item in value.items() if key != "receipt_sha256"}))


def _receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    body = dict(value)
    body["text_free"] = True
    body["receipt_sha256"] = _hash_receipt(body)
    return body


def _identity(row: Mapping[str, Any]) -> tuple[str, str]:
    unit_id = row.get("unit_id")
    unit_sha256 = row.get("unit_sha256")
    _require(isinstance(unit_id, str) and bool(unit_id), "packet_binding_drift")
    _require(isinstance(unit_sha256, str) and len(unit_sha256) == 64, "packet_binding_drift")
    return unit_id, unit_sha256


def identity_set(rows: Sequence[Mapping[str, Any]]) -> str:
    identities = [_identity(row) for row in rows]
    _require(len(identities) == len(set(identities)), "identity_uniqueness_failure")
    return digest(canonical(sorted(identities)))


def _ordered_identity_commitment(stream: Sequence[Any]) -> str:
    return digest(canonical(stream))


def _atomic_write(path: Path, payload: bytes, mode: int = PRIVATE_FILE_MODE) -> str:
    if path.exists() or path.is_symlink():
        raise MaterializationError("transaction_failure")
    try:
        path.parent.mkdir(parents=True, exist_ok=True, mode=PRIVATE_DIR_MODE)
        os.chmod(path.parent, PRIVATE_DIR_MODE)
        descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        temporary_path = Path(temporary)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary_path, mode)
            os.replace(temporary_path, path)
            return digest(payload)
        except BaseException:
            temporary_path.unlink(missing_ok=True)
            raise
    except MaterializationError:
        raise
    except BaseException:
        raise MaterializationError("transaction_failure") from None


def atomic(path: Path, value: Any, *, mode: int = PRIVATE_FILE_MODE) -> str:
    return _atomic_write(path, canonical(value), mode)


def _fsync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError:
        raise MaterializationError("transaction_failure") from None


def _walk_modes(root: Path) -> None:
    _directory(root, "transaction_failure")
    _require(stat.S_IMODE(root.stat().st_mode) == PRIVATE_DIR_MODE, "transaction_failure")
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise MaterializationError("transaction_failure")
        mode = stat.S_IMODE(path.stat().st_mode)
        if path.is_dir():
            _require(mode == PRIVATE_DIR_MODE, "transaction_failure")
        elif path.is_file():
            _require(mode == PRIVATE_FILE_MODE, "transaction_failure")
        else:
            raise MaterializationError("transaction_failure")


def _packet_record_shape(record: Any) -> bool:
    return isinstance(record, Mapping) and set(record) == {
        "lane",
        "packet_index",
        "canonical_basename",
        "row_count",
        "raw_sha256",
        "packet_identity_set_sha256",
    }


def _source_manifest(source: Path, config: Config) -> tuple[dict[str, Any], bytes, dict[str, Any]]:
    custody_path = source / "custody-receipt.json"
    manifest_path = source / "label-manifest.json"
    custody_raw = _read_regular(custody_path, "source_binding_drift")
    manifest_raw = _read_regular(manifest_path, "source_binding_drift")
    if not config.fixture:
        _require(digest(custody_raw) == SOURCE_CUSTODY_SHA256, "source_binding_drift")
        _require(digest(manifest_raw) == SOURCE_MANIFEST_SHA256, "source_binding_drift")
    custody = strict_json(custody_path, "source_binding_drift")
    manifest = strict_json(manifest_path, "manifest_binding_drift")
    _require(isinstance(custody, Mapping), "source_binding_drift")
    _require(isinstance(manifest, Mapping), "manifest_binding_drift")
    _require(custody.get("text_free") is True, "source_binding_drift")
    _require(manifest.get("schema_version") == "phase3_cycle005_label_manifest_v1", "manifest_binding_drift")
    _require(manifest.get("evaluation_cycle_id") == CYCLE005, "manifest_binding_drift")
    _require(manifest.get("text_free") is True, "manifest_binding_drift")
    _require(manifest.get("receipt_sha256") == _hash_receipt(manifest), "manifest_binding_drift")
    records = manifest.get("packets")
    _require(isinstance(records, list) and bool(records), "manifest_binding_drift")
    _require(manifest.get("packet_count") == len(records), "manifest_binding_drift")
    _require(
        manifest.get("row_count") == sum(record.get("row_count", -1) for record in records if isinstance(record, Mapping)),
        "manifest_binding_drift",
    )
    _require(manifest.get("custody_receipt_raw_sha256") == digest(custody_raw), "manifest_binding_drift")
    return dict(manifest), custody_raw, dict(custody)


def _expected_order(manifest: Mapping[str, Any], fixture: bool) -> list[dict[str, Any]]:
    records = manifest.get("packets")
    _require(isinstance(records, list), "manifest_binding_drift")
    by_key: dict[tuple[str, int], dict[str, Any]] = {}
    for record in records:
        _require(_packet_record_shape(record), "packet_order_failure")
        lane = record.get("lane")
        index = record.get("packet_index")
        _require(lane in LANE_ORDER and isinstance(index, int), "packet_order_failure")
        key = (lane, index)
        _require(key not in by_key, "packet_order_failure")
        by_key[key] = dict(record)
    counts = {
        lane: max((index for current_lane, index in by_key if current_lane == lane), default=0) for lane in LANE_ORDER
    }
    if not fixture:
        _require(counts == REAL_PACKET_COUNTS, "packet_order_failure")
    expected: list[dict[str, Any]] = []
    for lane in LANE_ORDER:
        lane_count = counts[lane]
        _require(lane_count > 0, "packet_order_failure")
        for index in range(1, lane_count + 1):
            record = by_key.get((lane, index))
            _require(record is not None, "packet_order_failure")
            expected.append(record)
    _require(records == expected, "packet_order_failure")
    return expected


def _packet_rows(source: Path, record: Mapping[str, Any], fixture: bool) -> dict[str, Any]:
    lane = record.get("lane")
    index = record.get("packet_index")
    basename = record.get("canonical_basename")
    _require(isinstance(lane, str) and isinstance(index, int) and isinstance(basename, str), "packet_binding_drift")
    _require(Path(basename).name == basename and basename == f"packet-{index:04d}.json", "packet_binding_drift")
    path = source / lane / basename
    raw = _read_regular(path, "packet_binding_drift")
    _require(digest(raw) == record.get("raw_sha256"), "packet_binding_drift")
    packet = strict_json(path, "packet_binding_drift")
    _require(isinstance(packet, Mapping), "packet_binding_drift")
    _require(
        set(packet)
        == {
            "schema_version",
            "evaluation_cycle_id",
            "lane",
            "packet_index",
            "row_count",
            "rows",
            "packet_identity_set_sha256",
        },
        "packet_binding_drift",
    )
    rows = packet.get("rows")
    row_count = record.get("row_count")
    _require(
        packet.get("schema_version") == "phase3_cycle005_private_packet_v1"
        and packet.get("evaluation_cycle_id") == CYCLE005
        and packet.get("lane") == lane
        and packet.get("packet_index") == index
        and packet.get("row_count") == row_count
        and isinstance(rows, list)
        and len(rows) == row_count,
        "packet_binding_drift",
    )
    if not fixture:
        expected_count = 9 if lane == "residual_label" and index == 164 else PACKET_SIZE
        _require(row_count == expected_count, "packet_binding_drift")
    else:
        _require(isinstance(row_count, int) and 1 <= row_count <= PACKET_SIZE, "packet_binding_drift")
    _require(packet.get("packet_identity_set_sha256") == identity_set(rows), "packet_binding_drift")
    _require(packet.get("packet_identity_set_sha256") == record.get("packet_identity_set_sha256"), "packet_binding_drift")
    for row in rows:
        _require(isinstance(row, Mapping), "packet_binding_drift")
        _require(not (FORBIDDEN_ROW_KEYS & set(row)), "label_leak_detected")
        if "evaluation_cycle_id" in row:
            _require(row.get("evaluation_cycle_id") == CYCLE005, "packet_binding_drift")
        _identity(row)
    return dict(packet)


def _validate_paths(config: Config) -> None:
    _directory(config.source, "source_binding_drift")
    if config.output.exists() or config.output.is_symlink():
        raise MaterializationError("output_exists")
    source_resolved = config.source.resolve()
    output_resolved = config.output.resolve()
    _require(source_resolved != output_resolved, "path_overlap")
    _require(not output_resolved.is_relative_to(source_resolved), "path_overlap")
    _require(not source_resolved.is_relative_to(output_resolved), "path_overlap")


def _verify_source_package_modes(source: Path, manifest: Mapping[str, Any], fixture: bool) -> None:
    """Amendment step 15/fixes v3 item 7: verify the source package's own custody modes.

    Real (non-fixture) mode only — a held-out package must already be
    mode-0700 directories / mode-0600 files ("operator-owned package with
    mode-0600 files"). Fixture packages built by tests may use whatever
    permissions the test harness happens to create.

    Walks *every* directory and file under ``source`` — not only the
    manifest-listed packet/custody/manifest files — so a symlink, fifo,
    device, or unexpected extra file placed anywhere in the package (not
    just the specific paths this materializer reads) is rejected too.
    """
    if fixture:
        return
    _directory(source, "source_mode_drift")
    _require(stat.S_IMODE(source.stat().st_mode) == PRIVATE_DIR_MODE, "source_mode_drift")
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise MaterializationError("source_mode_drift")
        mode = stat.S_IMODE(path.stat().st_mode)
        if path.is_dir():
            _require(mode == PRIVATE_DIR_MODE, "source_mode_drift")
        elif path.is_file():
            _require(mode == PRIVATE_FILE_MODE, "source_mode_drift")
        else:
            # Not a regular file, directory, or symlink — fifo, socket,
            # device, etc. Never permitted anywhere in a source package.
            raise MaterializationError("source_mode_drift")


def _build_stage(config: Config, stage: Path) -> dict[str, Any]:
    source = config.source
    _directory(source, "source_binding_drift")
    manifest, custody_raw, _custody = _source_manifest(source, config)
    _verify_source_package_modes(source, manifest, bool(config.fixture))
    expected = _expected_order(manifest, bool(config.fixture))
    lane_counts = {lane: 0 for lane in LANE_ORDER}
    output_records: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    ordered_source_stream: list[list[Any]] = []
    for record in expected:
        packet = _packet_rows(source, record, bool(config.fixture))
        rows = packet["rows"]
        identities = [_identity(row) for row in rows]
        _require(not (seen & set(identities)), "identity_uniqueness_failure")
        seen.update(identities)
        lane = str(record["lane"])
        lane_counts[lane] += len(rows)
        packet_out = copy.deepcopy(packet)
        packet_out["schema_version"] = "phase3_cycle007_evidence_packet_v1"
        packet_out["evaluation_cycle_id"] = CYCLE007
        packet_out["rows"] = []
        for source_row in rows:
            output_row = copy.deepcopy(source_row)
            if "evaluation_cycle_id" in source_row:
                output_row["evaluation_cycle_id"] = CYCLE007
            packet_out["rows"].append(output_row)
        packet_out["packet_identity_set_sha256"] = identity_set(packet_out["rows"])
        output_path = stage / lane / str(record["canonical_basename"])
        atomic(output_path, packet_out)
        sealed = strict_json(output_path, "transaction_failure")
        _require(isinstance(sealed, Mapping), "transaction_failure")
        for source_row, output_row in zip(rows, sealed["rows"], strict=True):
            expected_row = copy.deepcopy(source_row)
            if "evaluation_cycle_id" in source_row:
                expected_row["evaluation_cycle_id"] = CYCLE007
            _require(output_row == expected_row, "packet_binding_drift")
        raw_out = _read_regular(output_path, "transaction_failure")
        out_record = {
            "lane": lane,
            "packet_index": record["packet_index"],
            "canonical_basename": record["canonical_basename"],
            "row_count": len(rows),
            "raw_sha256": digest(raw_out),
            "packet_identity_set_sha256": packet_out["packet_identity_set_sha256"],
        }
        output_records.append(out_record)
        for row_index, identity in enumerate(identities):
            ordered_source_stream.append([lane, record["packet_index"], row_index, identity[0], identity[1]])
    _require(lane_counts["clean_label"] + lane_counts["residual_label"] == sum(lane_counts.values()), "source_shape_failure")
    if config.strict_counts:
        _require(lane_counts == REAL_ROW_COUNTS, "source_shape_failure")
        _require(len(expected) == sum(REAL_PACKET_COUNTS.values()), "source_shape_failure")
    commitment = _ordered_identity_commitment(ordered_source_stream)
    if not config.fixture:
        reported = manifest.get("ordered_identity_commitment_sha256")
        _require(reported == ORDERED_IDENTITY_COMMITMENT_SHA256, "ordered_identity_commitment_failure")
        _require(commitment == reported, "ordered_identity_commitment_failure")
    identity_union_commitment = digest(canonical(sorted(seen)))
    packet_count = len(output_records)
    row_count = sum(record["row_count"] for record in output_records)
    _require(packet_count == len(expected) and row_count == sum(lane_counts.values()), "source_shape_failure")
    if config.strict_counts:
        _require(packet_count == 204 and row_count == 10_159, "source_shape_failure")
    ordered_packet_commitment = digest(canonical(output_records))
    custody_value = _receipt(
        {
            "schema_version": "phase3_cycle007_custody_receipt_v1",
            "evaluation_cycle_id": CYCLE007,
            "source_evaluation_cycle_id": CYCLE005,
            "amendment_reference": "batch_state/phase3-cycle007-source-grounded-amendment-v1.md",
            "source_custody_receipt_raw_sha256": digest(custody_raw),
            "source_label_manifest_raw_sha256": digest(_read_regular(source / "label-manifest.json", "source_binding_drift")),
            "ordered_identity_commitment_sha256": commitment,
            "identity_union_commitment_sha256": identity_union_commitment,
            "ordered_packet_commitment_sha256": ordered_packet_commitment,
            "packet_count": packet_count,
            "row_count": row_count,
            "lane_row_counts": lane_counts,
            "packet_size": PACKET_SIZE,
            "provider_artifacts_copied": False,
            "labels_copied": False,
            "responses_copied": False,
            "prompts_generated": False,
            "evidence_sidecars_generated": False,
            "text_free": True,
        }
    )
    custody_path = stage / "custody-receipt.json"
    custody_hash = atomic(custody_path, custody_value)
    manifest_value = _receipt(
        {
            "schema_version": "phase3_cycle007_materialization_manifest_v1",
            "evaluation_cycle_id": CYCLE007,
            "source_evaluation_cycle_id": CYCLE005,
            "text_free": True,
            "custody_receipt_raw_sha256": custody_hash,
            "ordered_identity_commitment_sha256": commitment,
            "identity_union_commitment_sha256": identity_union_commitment,
            "ordered_packet_commitment_sha256": ordered_packet_commitment,
            "packet_count": packet_count,
            "row_count": row_count,
            "lane_row_counts": lane_counts,
            "packets": output_records,
        }
    )
    atomic(stage / "manifest.json", manifest_value)
    _fsync_directory(stage / "clean_label")
    _fsync_directory(stage / "residual_label")
    _fsync_directory(stage)
    return {
        "ok": True,
        "packet_count": packet_count,
        "row_count": row_count,
        "ordered_identity_commitment_sha256": commitment,
        "custody_receipt_sha256": custody_hash,
        "materialization_manifest_sha256": digest(canonical(manifest_value)),
        "text_free": True,
    }


def _install_stage(staging: Path, output: Path) -> None:
    """Atomically claim ``output`` and move the staged tree into it.

    Amendment (fixes v3, item 7): closes the destination TOCTOU window a
    plain ``os.replace(staging, output)`` would leave open — POSIX rename
    silently succeeds (replacing the destination) when ``output`` already
    exists as an *empty* directory, which is exactly what a concurrent actor
    could have created in the window between ``_validate_paths``'s earlier
    existence check and this install step. ``os.mkdir`` is a single atomic
    kernel syscall: it fails closed with ``FileExistsError`` if anything —
    including that concurrently created directory — now occupies ``output``,
    and this call never touches or deletes whatever it finds there; it only
    ever removes its own staging path (handled by the caller's ``finally``).
    """
    try:
        os.mkdir(output)
    except FileExistsError:
        raise MaterializationError("output_exists") from None
    except OSError:
        raise MaterializationError("transaction_failure") from None
    os.chmod(output, PRIVATE_DIR_MODE)
    for name in sorted(OUTPUT_TOP_LEVEL):
        os.rename(staging / name, output / name)


def materialize(
    source: Path,
    output: Path,
    *,
    fixture: bool = False,
    strict_counts: bool | None = None,
) -> dict[str, Any]:
    """Materialize one fresh Cycle 007 successor package and return a text-free receipt."""
    config = Config(Path(source), Path(output), fixture=fixture, strict_counts=strict_counts)
    if not config.fixture and config.strict_counts is not True:
        raise MaterializationError("fixture_flag_required")
    _validate_paths(config)
    try:
        output_parent = config.output.parent
        output_parent.mkdir(parents=True, exist_ok=True, mode=PRIVATE_DIR_MODE)
        staging = Path(tempfile.mkdtemp(prefix=f".{config.output.name}.staging-", dir=output_parent))
        os.chmod(staging, PRIVATE_DIR_MODE)
    except MaterializationError:
        raise
    except BaseException:
        raise MaterializationError("transaction_failure") from None
    committed = False
    try:
        result = _build_stage(config, staging)
        _require({path.name for path in staging.iterdir()} == OUTPUT_TOP_LEVEL, "transaction_failure")
        _walk_modes(staging)
        _install_stage(staging, config.output)
        # Amendment step 14: from this point the operation is committed at
        # the filesystem level — a later diagnostic failing must never
        # trigger deleting the artifact that was just correctly installed.
        committed = True
        _fsync_directory(config.output.parent)
        _walk_modes(config.output)
        return result
    except MaterializationError:
        raise
    except BaseException:
        raise MaterializationError("transaction_failure") from None
    finally:
        if not committed:
            # Amendment step 14: on any failure, remove only the
            # task-owned staging path this call created. ``config.output``
            # is never touched here — ``_validate_paths`` already refused a
            # pre-existing destination up front, and by construction this
            # process is never the one that created it if it exists now
            # (a concurrently created destination must survive untouched).
            shutil.rmtree(staging, ignore_errors=True)


def _resolve_real_paths() -> tuple[Path, Path]:
    """Amendment step 15: resolve real-mode source/output from env/config, never argv."""
    config_path_raw = os.environ.get(REAL_CONFIG_ENV)
    if config_path_raw:
        config_path = Path(config_path_raw)
        _regular(config_path, "path_disclosure_refused")
        _require(stat.S_IMODE(config_path.stat().st_mode) == PRIVATE_FILE_MODE, "path_disclosure_refused")
        payload = strict_json(config_path, "path_disclosure_refused")
        _require(
            isinstance(payload, Mapping) and isinstance(payload.get("source"), str) and isinstance(payload.get("output"), str),
            "path_disclosure_refused",
        )
        return Path(payload["source"]), Path(payload["output"])
    source_env = os.environ.get(REAL_SOURCE_ENV)
    output_env = os.environ.get(REAL_OUTPUT_ENV)
    _require(bool(source_env) and bool(output_env), "path_disclosure_refused")
    return Path(source_env), Path(output_env)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", "--source-package", dest="source", type=Path, default=None)
    parser.add_argument("--output", "--output-package", dest="output", type=Path, default=None)
    parser.add_argument(
        "--fixture",
        action="store_true",
        help="use isolated synthetic bindings with explicit --source/--output; never use this for a live package",
    )
    args = parser.parse_args(argv)
    try:
        if args.fixture:
            _require(args.source is not None and args.output is not None, "fixture_flag_required")
            source, output = args.source, args.output
        else:
            # Amendment step 15: real mode never accepts --source/--output —
            # private paths never appear on argv/CLI for a live package.
            _require(args.source is None and args.output is None, "path_disclosure_refused")
            source, output = _resolve_real_paths()
        result = materialize(source, output, fixture=args.fixture)
    except MaterializationError as exc:
        print(json.dumps({"ok": False, "failure_code": exc.code, "text_free": True}, separators=(",", ":")))
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
