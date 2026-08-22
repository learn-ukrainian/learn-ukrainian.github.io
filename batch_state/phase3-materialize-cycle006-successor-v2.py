#!/usr/bin/env python3
"""Materialize a clean Cycle-006 successor from the sealed Cycle-005 package.

Only the Cycle-005 custody package, its text-free label manifest, and public
prompt templates are read.  Source rows are copied into a new transactional
package with their ``evaluation_cycle_id`` changed from Cycle 005 to Cycle
006.  Provider output, labels, responses, captures, adjudications, and
resolutions are deliberately not copied.

The default CLI is pinned to the real Cycle-005 bindings.  ``--fixture`` is a
separate synthetic-only mode used by the behavior proof; it never relaxes the
shape, ordering, identity, mode, or atomicity checks.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CYCLE005 = "phase3-v2-1-evaluation-cycle-005"
CYCLE006 = "phase3-v2-1-evaluation-cycle-006"
AMENDMENT_SHA256 = "524e6eb4f18d38f104413fb32f421ff73c3d80bc411d338a6d8a31fabc087474"
SOURCE_CUSTODY_SHA256 = "7047e8459433376f3b690cfc2f15e115d77a701e79afb0ef2db184b44ea14726"
SOURCE_MANIFEST_SHA256 = "b8d290ffe945a6cc5d36345cbf234ccf79a7df98cb4199ffad0b778cd2b69fab"
ORDERED_IDENTITY_COMMITMENT_SHA256 = "331fd7fbc42e43cb3c218d9c2b790df060c0a553ab7c3a7b3b557f9f2bc3c419"

REAL_ROW_COUNTS = {"clean_label": 2_000, "residual_label": 8_159}
REAL_PACKET_COUNTS = {"clean_label": 40, "residual_label": 164}
LANE_ORDER = ("clean_label", "residual_label")
PACKET_SIZE = 50
GEMINI_CHUNK_SIZE = 20
PRIVATE_DIR_MODE = 0o700
PRIVATE_FILE_MODE = 0o600

OUTPUT_TOP_LEVEL = frozenset(
    {"clean_label", "residual_label", "prompts", "custody-receipt.json", "label-manifest.json"}
)
PROMPT_FILES = {
    ("clean_label", "grok"): "grok-clean-label.md",
    ("residual_label", "grok"): "grok-residual-label.md",
    ("clean_label", "gemini"): "gemini-clean-label.md",
    ("residual_label", "gemini"): "gemini-residual-label.md",
}
PROMPT_TEMPLATES = {
    ("clean_label", "grok"): "phase3-cycle005-clean-heldout-label-prompt-v1.md",
    ("residual_label", "grok"): "phase3-cycle005-residual-heldout-label-prompt-v1.md",
    ("clean_label", "gemini"): "phase3-cycle005-clean-heldout-label-prompt-gemini-v1.md",
    ("residual_label", "gemini"): "phase3-cycle005-residual-heldout-label-prompt-gemini-v1.md",
}

# The materializer itself has no provider or adjudication capability.  These
# are local transport labels for text-free CLI failures, not provider labels.
FAILURE_CODES = frozenset(
    {
        "amendment_binding_drift",
        "source_binding_drift",
        "source_shape_failure",
        "manifest_binding_drift",
        "packet_binding_drift",
        "packet_order_failure",
        "identity_uniqueness_failure",
        "ordered_identity_commitment_failure",
        "prompt_binding_drift",
        "prompt_cycle_leak",
        "fixture_flag_required",
        "output_exists",
        "path_overlap",
        "transaction_failure",
    }
)
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class MaterializationError(ValueError):
    """A fail-closed materialization error with a text-free public code."""

    def __init__(self, code: str) -> None:
        self.code = code if code in FAILURE_CODES else "transaction_failure"
        super().__init__(self.code)


# Short aliases make the failure-oriented behavior proof easy to read and
# preserve the naming used by earlier Phase 3 transport modules.
Error = MaterializationError


@dataclass(frozen=True)
class Config:
    """Validated invocation configuration.

    ``strict_counts`` is intentionally derived from ``fixture``.  Callers may
    construct a non-strict config for synthetic tests only by setting
    ``fixture=True``; a real invocation can never override the frozen counts.
    """

    source: Path
    output: Path
    amendment: Path
    fixture: bool = False
    strict_counts: bool | None = None

    def __post_init__(self) -> None:
        strict = not self.fixture if self.strict_counts is None else self.strict_counts
        if strict and self.fixture:
            strict = False
        object.__setattr__(self, "strict_counts", strict)


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Compatibility spelling used by Phase 3 tests."""

    return digest(data)


def sha256_file(path: Path) -> str:
    return digest(_read_regular(path, "hash input"))


def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise MaterializationError("source_shape_failure")
        result[key] = value
    return result


def _regular(path: Path, code: str = "source_shape_failure") -> None:
    try:
        entry = path.lstat()
    except OSError as exc:
        del exc
        raise MaterializationError(code) from None
    if path.is_symlink() or not stat.S_ISREG(entry.st_mode):
        raise MaterializationError(code)


def _directory(path: Path, code: str = "source_shape_failure") -> None:
    try:
        entry = path.lstat()
    except OSError as exc:
        del exc
        raise MaterializationError(code) from None
    if path.is_symlink() or not stat.S_ISDIR(entry.st_mode):
        raise MaterializationError(code)


def _read_regular(path: Path, code: str) -> bytes:
    _regular(path, code)
    try:
        return path.read_bytes()
    except OSError as exc:
        del exc
        raise MaterializationError(code) from None


def strict_json(path: Path, code: str = "source_shape_failure") -> Any:
    raw = _read_regular(path, code)
    try:
        return json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=pairs_hook)
    except (UnicodeDecodeError, json.JSONDecodeError, MaterializationError) as exc:
        del exc
        raise MaterializationError(code) from None


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise MaterializationError(code)


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
    _require(isinstance(unit_sha256, str) and HEX64.fullmatch(unit_sha256) is not None, "packet_binding_drift")
    return unit_id, unit_sha256


def identity_set(rows: Sequence[Mapping[str, Any]]) -> str:
    identities = [_identity(row) for row in rows]
    _require(len(identities) == len(set(identities)), "identity_uniqueness_failure")
    return digest(canonical(sorted(identities)))


def _ordered_identity_commitment(packet_rows: Sequence[Mapping[str, Any]]) -> str:
    """Hash the ordered lane/packet/row identity stream.

    The stream is represented as tuples because packet and row boundaries are
    part of the frozen commitment.  JSON canonicalization turns each tuple
    into a deterministic array while retaining the original sequence.
    """

    return digest(canonical(packet_rows))


def ordered_identity_commitment(records: Sequence[Mapping[str, Any]]) -> str:
    """Public helper for synthetic proofs.

    ``records`` contains one mapping per packet with ``lane``,
    ``packet_index`` and ordered ``identities``.  The helper validates the
    identities before hashing them.
    """

    stream: list[list[Any]] = []
    for record in records:
        lane = record.get("lane")
        index = record.get("packet_index")
        rows = record.get("identities")
        _require(isinstance(lane, str) and isinstance(index, int) and isinstance(rows, list), "packet_binding_drift")
        for row_index, row_identity in enumerate(rows):
            if isinstance(row_identity, Mapping):
                identity = _identity(row_identity)
            else:
                _require(
                    isinstance(row_identity, (list, tuple))
                    and len(row_identity) == 2
                    and isinstance(row_identity[0], str)
                    and isinstance(row_identity[1], str)
                    and HEX64.fullmatch(row_identity[1]) is not None,
                    "packet_binding_drift",
                )
                identity = (row_identity[0], row_identity[1])
            stream.append([lane, index, row_index, identity[0], identity[1]])
    return _ordered_identity_commitment(stream)


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
    except BaseException as exc:
        del exc
        raise MaterializationError("transaction_failure") from None


def atomic(path: Path, value: Any, *, raw: bool = False, mode: int = PRIVATE_FILE_MODE) -> str:
    return _atomic_write(path, value if raw else canonical(value), mode)


def _fsync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError as exc:
        del exc
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


def _source_template_root() -> Path:
    return Path(__file__).resolve().parents[1] / "batch_state"


def _fresh_prompt(template: bytes, lane: str, provider: str) -> bytes:
    try:
        text = template.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        del exc
        raise MaterializationError("prompt_binding_drift") from None
    # Make a genuinely Cycle-006 prompt from the public, cycle-neutralized
    # Cycle-005 contract.  This does not carry any packet or provider output.
    replacements = (
        ("Cycle 005", "Cycle 006"),
        ("Cycle-005", "Cycle-006"),
        ("cycle005", "cycle006"),
        ("cycle-005", "cycle-006"),
        ("CYCLE005", "CYCLE006"),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    if CYCLE005 in text:
        raise MaterializationError("prompt_cycle_leak")
    if provider == "gemini":
        text += (
            "\n\n## Cycle 006 ordinal response contract\n\n"
            "For a chunk containing N rows, return one strict JSON object with "
            "exactly one top-level key `labels_by_position`. Its keys are exactly "
            "`p01` through `pNN` (for example, `p01` … `p20`), with no missing, "
            "duplicate, or additional keys. Each value is one label object for "
            "that ordinal and must copy that row's `unit_id` and `unit_sha256` "
            "unchanged. The response object has `additionalProperties: false`; "
            "do not return a `labels` array. The transport normalizer visits "
            "ordinals numerically and emits the unchanged `labels` validator "
            "envelope.\n"
        )
    else:
        text += (
            "\n\n## Cycle 006 Grok transport contract\n\n"
            "Return only the unchanged strict JSON `labels` envelope, with one "
            "label object per source row in exact source order. The complete "
            "prompt and packet are delivered through stdin; never repeat source "
            "text, locators, labels, or explanations outside that envelope.\n"
        )
    if CYCLE005 in text:
        raise MaterializationError("prompt_cycle_leak")
    return text.encode("utf-8")


def _fixture_prompt(lane: str, provider: str) -> bytes:
    if provider == "gemini":
        body = (
            f"Synthetic Cycle 006 {lane} Gemini contract. Return exactly "
            "labels_by_position with ordinal keys p01 through pNN, "
            "additionalProperties false, and one bound label object per key.\n"
        )
    else:
        body = (
            f"Synthetic Cycle 006 {lane} Grok contract. Return exactly the "
            "unchanged labels envelope in source order through stdin.\n"
        )
    return body.encode("utf-8")


def _prompt_payloads(fixture: bool) -> dict[str, bytes]:
    payloads: dict[str, bytes] = {}
    for (lane, provider), filename in PROMPT_FILES.items():
        if fixture:
            payload = _fixture_prompt(lane, provider)
        else:
            template = _source_template_root() / PROMPT_TEMPLATES[(lane, provider)]
            payload = _fresh_prompt(_read_regular(template, "prompt_binding_drift"), lane, provider)
        _require(CYCLE005 not in payload.decode("utf-8", "strict"), "prompt_cycle_leak")
        payloads[filename] = payload
    return payloads


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
    _require(isinstance(records, list) and records, "manifest_binding_drift")
    _require(manifest.get("packet_count") == len(records), "manifest_binding_drift")
    _require(
        manifest.get("row_count")
        == sum(record.get("row_count", -1) for record in records if isinstance(record, Mapping)),
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


def _packet_rows(source: Path, record: Mapping[str, Any], fixture: bool) -> tuple[dict[str, Any], bytes]:
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
    _require(
        packet.get("packet_identity_set_sha256") == record.get("packet_identity_set_sha256"), "packet_binding_drift"
    )
    for row in rows:
        _require(isinstance(row, Mapping), "packet_binding_drift")
        if "evaluation_cycle_id" in row:
            _require(row.get("evaluation_cycle_id") == CYCLE005, "packet_binding_drift")
        _identity(row)
    return dict(packet), raw


def _find_reported_commitment(manifest: Mapping[str, Any], custody: Mapping[str, Any]) -> str | None:
    keys = (
        "ordered_identity_commitment_sha256",
        "ordered_lane_packet_row_identity_commitment_sha256",
        "identity_order_commitment_sha256",
    )
    for value in (manifest, custody):
        for key in keys:
            candidate = value.get(key)
            if isinstance(candidate, str):
                return candidate
    return None


def _validate_union_and_commitment(
    source_records: Sequence[Mapping[str, Any]],
    manifest: Mapping[str, Any],
    custody: Mapping[str, Any],
    config: Config,
) -> tuple[list[list[Any]], str, str]:
    identities: list[tuple[str, str]] = []
    stream: list[list[Any]] = []
    for record in source_records:
        packet = record.get("_packet")
        _require(isinstance(packet, Mapping), "packet_binding_drift")
        rows = packet.get("rows")
        _require(isinstance(rows, list), "packet_binding_drift")
        for row_index, row in enumerate(rows):
            identity = _identity(row)
            identities.append(identity)
            stream.append([record["lane"], record["packet_index"], row_index, identity[0], identity[1]])
    _require(len(identities) == len(set(identities)), "identity_uniqueness_failure")
    union = digest(canonical(sorted(identities)))
    _require(manifest.get("identity_union_commitment_sha256") == union, "manifest_binding_drift")
    packet_records = [
        {key: value for key, value in record.items() if not key.startswith("_")} for record in source_records
    ]
    _require(
        manifest.get("ordered_packet_commitment_sha256") == digest(canonical(packet_records)), "manifest_binding_drift"
    )
    if config.fixture:
        commitment = _ordered_identity_commitment(stream)
    else:
        computed = _ordered_identity_commitment(stream)
        _require(computed == ORDERED_IDENTITY_COMMITMENT_SHA256, "ordered_identity_commitment_failure")
        reported = _find_reported_commitment(manifest, custody)
        if reported is not None:
            _require(reported == computed, "ordered_identity_commitment_failure")
        commitment = computed
    return stream, commitment, union


def _write_prompt_dir(stage: Path, payloads: Mapping[str, bytes]) -> dict[str, str]:
    prompts = stage / "prompts"
    prompts.mkdir(mode=PRIVATE_DIR_MODE)
    os.chmod(prompts, PRIVATE_DIR_MODE)
    hashes: dict[str, str] = {}
    for filename, payload in payloads.items():
        hashes[f"prompts/{filename}"] = _atomic_write(prompts / filename, payload)
    _fsync_directory(prompts)
    return hashes


def _build_stage(config: Config, stage: Path) -> dict[str, Any]:
    source = config.source
    _directory(source, "source_binding_drift")
    manifest, custody_raw, custody = _source_manifest(source, config)
    expected = _expected_order(manifest, bool(config.fixture))
    lane_counts = {lane: 0 for lane in LANE_ORDER}
    output_records: list[dict[str, Any]] = []
    source_records: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    ordered_source_stream: list[list[Any]] = []
    for record in expected:
        packet, _source_raw = _packet_rows(source, record, bool(config.fixture))
        rows = packet["rows"]
        identities = [_identity(row) for row in rows]
        _require(not (seen & set(identities)), "identity_uniqueness_failure")
        seen.update(identities)
        lane = str(record["lane"])
        lane_counts[lane] += len(rows)
        packet_out = copy.deepcopy(packet)
        packet_out["schema_version"] = "phase3_cycle006_private_packet_v1"
        packet_out["evaluation_cycle_id"] = CYCLE006
        packet_out["rows"] = []
        for source_row in rows:
            output_row = copy.deepcopy(source_row)
            if "evaluation_cycle_id" in source_row:
                output_row["evaluation_cycle_id"] = CYCLE006
            packet_out["rows"].append(output_row)
        packet_out["packet_identity_set_sha256"] = identity_set(packet_out["rows"])
        output_path = stage / lane / str(record["canonical_basename"])
        atomic(output_path, packet_out)
        # Re-read the sealed staged packet and prove every source row field was
        # preserved, with the sole row-level change being evaluation_cycle_id.
        sealed = strict_json(output_path, "transaction_failure")
        _require(isinstance(sealed, Mapping), "transaction_failure")
        for source_row, output_row in zip(rows, sealed["rows"], strict=True):
            expected_row = copy.deepcopy(source_row)
            if "evaluation_cycle_id" in source_row:
                expected_row["evaluation_cycle_id"] = CYCLE006
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
        source_records.append({**dict(record), "_packet": packet})
        for row_index, identity in enumerate(identities):
            ordered_source_stream.append([lane, record["packet_index"], row_index, identity[0], identity[1]])
    _require(
        lane_counts["clean_label"] + lane_counts["residual_label"] == sum(lane_counts.values()), "source_shape_failure"
    )
    if config.strict_counts:
        _require(lane_counts == REAL_ROW_COUNTS, "source_shape_failure")
        _require(len(expected) == sum(REAL_PACKET_COUNTS.values()), "source_shape_failure")
    _, commitment, identity_union_commitment = _validate_union_and_commitment(source_records, manifest, custody, config)
    if config.fixture:
        _require(
            _ordered_identity_commitment(ordered_source_stream) == commitment,
            "ordered_identity_commitment_failure",
        )
    payloads = _prompt_payloads(bool(config.fixture))
    prompt_hashes = _write_prompt_dir(stage, payloads)
    prompt_bindings = [
        {
            "lane": lane,
            "provider": provider,
            "path": f"prompts/{filename}",
            "sha256": prompt_hashes[f"prompts/{filename}"],
        }
        for lane, provider, filename in sorted(
            (lane, provider, filename) for (lane, provider), filename in PROMPT_FILES.items()
        )
    ]
    packet_count = len(output_records)
    row_count = sum(record["row_count"] for record in output_records)
    _require(packet_count == len(expected) and row_count == sum(lane_counts.values()), "source_shape_failure")
    if config.strict_counts:
        _require(packet_count == 204 and row_count == 10_159, "source_shape_failure")
    ordered_packet_commitment = digest(canonical(output_records))
    custody_value = _receipt(
        {
            "schema_version": "phase3_cycle006_custody_receipt_v2",
            "evaluation_cycle_id": CYCLE006,
            "source_evaluation_cycle_id": CYCLE005,
            "cycle006_amendment_raw_sha256": digest(_read_regular(config.amendment, "amendment_binding_drift")),
            "source_custody_receipt_raw_sha256": digest(custody_raw),
            "source_label_manifest_raw_sha256": digest(
                _read_regular(source / "label-manifest.json", "source_binding_drift")
            ),
            "ordered_identity_commitment_sha256": commitment,
            "identity_union_commitment_sha256": identity_union_commitment,
            "ordered_packet_commitment_sha256": ordered_packet_commitment,
            "packet_count": packet_count,
            "row_count": row_count,
            "lane_row_counts": lane_counts,
            "packet_size": PACKET_SIZE,
            "gemini_chunk_size": GEMINI_CHUNK_SIZE,
            "prompt_sha256s": prompt_hashes,
            "prompt_bindings": prompt_bindings,
            "provider_artifacts_copied": False,
            "labels_copied": False,
            "responses_copied": False,
            "text_free": True,
        }
    )
    custody_path = stage / "custody-receipt.json"
    custody_hash = atomic(custody_path, custody_value)
    manifest_value = _receipt(
        {
            "schema_version": "phase3_cycle006_label_manifest_v2",
            "evaluation_cycle_id": CYCLE006,
            "source_evaluation_cycle_id": CYCLE005,
            "text_free": True,
            "custody_receipt_raw_sha256": custody_hash,
            "cycle006_amendment_raw_sha256": custody_value["cycle006_amendment_raw_sha256"],
            "source_custody_receipt_raw_sha256": custody_value["source_custody_receipt_raw_sha256"],
            "source_label_manifest_raw_sha256": custody_value["source_label_manifest_raw_sha256"],
            "ordered_identity_commitment_sha256": commitment,
            "identity_union_commitment_sha256": identity_union_commitment,
            "ordered_packet_commitment_sha256": ordered_packet_commitment,
            "packet_count": packet_count,
            "row_count": row_count,
            "lane_row_counts": lane_counts,
            "prompt_sha256s": prompt_hashes,
            "prompt_bindings": prompt_bindings,
            "packets": output_records,
        }
    )
    atomic(stage / "label-manifest.json", manifest_value)
    _fsync_directory(stage / "clean_label")
    _fsync_directory(stage / "residual_label")
    _fsync_directory(stage)
    return {
        "ok": True,
        "packet_count": packet_count,
        "row_count": row_count,
        "ordered_identity_commitment_sha256": commitment,
        "custody_receipt_sha256": custody_hash,
        "label_manifest_sha256": digest(canonical(manifest_value)),
        "text_free": True,
    }


def _validate_paths(config: Config) -> None:
    _regular(config.amendment, "amendment_binding_drift")
    if not config.fixture:
        _require(sha256_file(config.amendment) == AMENDMENT_SHA256, "amendment_binding_drift")
    _directory(config.source, "source_binding_drift")
    if config.output.exists() or config.output.is_symlink():
        raise MaterializationError("output_exists")
    source_resolved = config.source.resolve()
    output_resolved = config.output.resolve()
    _require(source_resolved != output_resolved, "path_overlap")
    _require(not output_resolved.is_relative_to(source_resolved), "path_overlap")
    _require(not source_resolved.is_relative_to(output_resolved), "path_overlap")


def materialize(
    source: Path,
    output: Path,
    amendment: Path,
    *,
    fixture: bool = False,
    strict_counts: bool | None = None,
) -> dict[str, Any]:
    """Materialize one successor package and return a text-free receipt."""

    config = Config(Path(source), Path(output), Path(amendment), fixture=fixture, strict_counts=strict_counts)
    if not config.fixture and config.strict_counts is not True:
        # Defensive barrier: a caller cannot weaken real-mode frozen counts.
        raise MaterializationError("fixture_flag_required")
    _validate_paths(config)
    try:
        output_parent = config.output.parent
        output_parent.mkdir(parents=True, exist_ok=True, mode=PRIVATE_DIR_MODE)
        staging = Path(tempfile.mkdtemp(prefix=f".{config.output.name}.staging-", dir=output_parent))
        os.chmod(staging, PRIVATE_DIR_MODE)
    except MaterializationError:
        raise
    except BaseException as exc:
        del exc
        raise MaterializationError("transaction_failure") from None
    committed = False
    try:
        result = _build_stage(config, staging)
        _require(set(path.name for path in staging.iterdir()) == OUTPUT_TOP_LEVEL, "transaction_failure")
        _walk_modes(staging)
        os.replace(staging, config.output)
        _fsync_directory(config.output.parent)
        _walk_modes(config.output)
        committed = True
        return result
    except MaterializationError:
        raise
    except BaseException as exc:
        del exc
        raise MaterializationError("transaction_failure") from None
    finally:
        if not committed:
            shutil.rmtree(staging, ignore_errors=True)
            if config.output.exists() and not config.output.is_symlink():
                # The destination did not exist before validation; removing a
                # partially committed directory restores the transaction.
                shutil.rmtree(config.output, ignore_errors=True)


def build(config: Config) -> dict[str, Any]:
    """Compatibility entry point for callers passing a ``Config`` object."""

    return materialize(
        config.source,
        config.output,
        config.amendment,
        fixture=bool(config.fixture),
        strict_counts=config.strict_counts,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", "--source-package", dest="source", type=Path, required=True)
    parser.add_argument("--output", "--output-package", dest="output", type=Path, required=True)
    parser.add_argument("--amendment", type=Path, required=True)
    parser.add_argument(
        "--fixture",
        action="store_true",
        help="use isolated synthetic bindings; never use this for a live package",
    )
    args = parser.parse_args(argv)
    try:
        result = materialize(args.source, args.output, args.amendment, fixture=args.fixture)
    except MaterializationError as exc:
        print(json.dumps({"ok": False, "failure_code": exc.code, "text_free": True}, separators=(",", ":")))
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
