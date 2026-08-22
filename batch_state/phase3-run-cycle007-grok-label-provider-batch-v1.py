#!/usr/bin/env python3
"""Cycle-007 v1 private Grok transport with immutable resumable seals and evidence sidecars.

The module deliberately contains no provider-specific private data. A live
package is supplied by the operator outside disposable worktrees; synthetic
tests replace the provider executable and prompt bindings locally.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

HERE = Path(__file__).resolve().parent
GROK = Path("/Users/krisztiankoos/.local/bin/grok")
CYCLE = "phase3-v2-1-evaluation-cycle-007"
AMENDMENT_SHA256 = "4f2e3e58964cae391c3933ffdce531296a0744808b0154231ca513049602fea0"
CYCLE007_AMENDMENT_SHA256 = AMENDMENT_SHA256
CUSTODY_SHA256 = "7047e8459433376f3b690cfc2f15e115d77a701e79afb0ef2db184b44ea14726"
CUSTODY = CUSTODY_SHA256
SOURCE_CUSTODY_SHA256 = CUSTODY_SHA256
SOURCE_MANIFEST_SHA256 = "b8d290ffe945a6cc5d36345cbf234ccf79a7df98cb4199ffad0b778cd2b69fab"
MANIFEST_SHA256 = SOURCE_MANIFEST_SHA256
ORDERED_IDENTITY_COMMITMENT_SHA256 = "331fd7fbc42e43cb3c218d9c2b790df060c0a553ab7c3a7b3b557f9f2bc3c419"
LANES = {"clean_label": 40, "residual_label": 164}
ROW_COUNT = 10159
PACKET_COUNT = 204
PACKET_SCHEMA_VERSION = "phase3_cycle007_evidence_packet_v1"
MANIFEST_SCHEMA_VERSION = "phase3_cycle007_materialization_manifest_v1"
EVIDENCE_MANIFEST_SCHEMA_VERSION = "phase3_cycle007_evidence_manifest_v1"
OUTPUT_ROOT = "label-output-grok-cycle007-v1"
PACKET_SIZE = 50
FINAL_PACKET_SIZE = 9

PROMPTS = {
    "clean_label": "prompts/grok-clean-label.md",
    "residual_label": "prompts/grok-residual-label.md",
}
SOURCE_VALIDATOR = HERE / "phase3-cycle007-label-validation-v1.py"


def _load_validator() -> Any:
    source_path = SOURCE_VALIDATOR
    if not source_path.is_file() or source_path.is_symlink():
        raise RuntimeError("Cycle-007 semantic validator unavailable")
    spec = importlib.util.spec_from_file_location("cycle007_public_semantic_validator", source_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cycle-007 semantic validator unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SOURCE = _load_validator()
REJECTS = SOURCE.REJECTS
GENRES = SOURCE.GENRES
TAX = SOURCE.TAX
DEC = SOURCE.DEC

FAILURE_CODES = frozenset(
    {
        "stream_json_invalid",
        "terminal_result_count_drift",
        "structured_output_envelope_drift",
        "ordinal_key_drift",
        "ordinal_identity_binding_drift",
        "label_json_invalid",
        "label_count_or_envelope_drift",
        "identity_or_order_drift",
        "identity_uniqueness_drift",
        "clean_label_schema_drift",
        "clean_label_invariant_drift",
        "residual_label_schema_drift",
        "residual_phenomenon_drift",
        "residual_scored_decision_insufficiency",
        "residual_2019_positive_forbidden",
        "residual_taxonomy_order_or_uniqueness_drift",
        "residual_primary_or_rollup_drift",
        "residual_null_rollup_drift",
        "cross_row_evidence",
        "cross_phenomenon_evidence",
        "evidence_id_order_drift",
        "insufficient_evidence_for_decision",
        "evidence_id_hash_drift",
        "query_sha256_hash_drift",
        "sidecar_binding_drift",
        "evidence_manifest_binding_drift",
        "materialization_manifest_binding_drift",
        "source_binding_drift",
        "unknown_decision_code",
        "evidence_shape_drift",
        "source_role_boundary_violation",
    }
)
STRUCTURAL_CODES = frozenset(
    {
        "stream_json_invalid",
        "terminal_result_count_drift",
        "structured_output_envelope_drift",
        "ordinal_key_drift",
        "ordinal_identity_binding_drift",
        "label_json_invalid",
        "label_count_or_envelope_drift",
        "clean_label_schema_drift",
        "residual_label_schema_drift",
        "residual_phenomenon_drift",
    }
)


class Error(ValueError):
    """Closed, privacy-safe transport failure."""

    def __init__(self, failure_code: str):
        self.failure_code = failure_code if failure_code in FAILURE_CODES else "stream_json_invalid"
        self.code = self.failure_code
        super().__init__(self.failure_code)


class Invalid(Error):
    pass


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in items:
        if key in value:
            raise Invalid("stream_json_invalid")
        value[key] = item
    return value


def _regular(path: Path, mode: int | None = None) -> None:
    try:
        info = path.lstat()
    except OSError:
        raise Error("label_count_or_envelope_drift") from None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise Error("label_count_or_envelope_drift")
    if mode is not None and stat.S_IMODE(info.st_mode) != mode:
        raise Error("label_count_or_envelope_drift")


def _directory(path: Path, mode: int | None = None) -> None:
    try:
        info = path.lstat()
    except OSError:
        raise Error("label_count_or_envelope_drift") from None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise Error("label_count_or_envelope_drift")
    if mode is not None and stat.S_IMODE(info.st_mode) != mode:
        raise Error("label_count_or_envelope_drift")


def atomic(path: Path, value: Any, raw: bool = False) -> str:
    """Write one immutable mode-0600 seal transactionally."""
    if path.exists() or path.is_symlink():
        raise Error("label_count_or_envelope_drift")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    _directory(path.parent, 0o700)
    data = value if raw else canonical(value)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return digest(data)


def read(path: Path, label: str = "private value", *, response: bool = False) -> Any:
    try:
        _regular(path, 0o600)
        value = json.loads(path.read_bytes().decode("utf-8", "strict"), object_pairs_hook=pairs)
    except Error as exc:
        if response:
            raise Invalid(exc.failure_code) from exc
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, Invalid):
        del label
        if response:
            raise Invalid("stream_json_invalid") from None
        raise Error("label_count_or_envelope_drift") from None
    return value


def _identity(row: Any) -> tuple[str, str]:
    if not isinstance(row, dict):
        raise Invalid("identity_or_order_drift")
    unit_id, unit_sha256 = row.get("unit_id"), row.get("unit_sha256")
    if (
        not isinstance(unit_id, str)
        or not isinstance(unit_sha256, str)
        or len(unit_sha256) != 64
        or any(character not in "0123456789abcdef" for character in unit_sha256)
    ):
        raise Invalid("identity_or_order_drift")
    return unit_id, unit_sha256


def identities(rows: list[Any]) -> list[tuple[str, str]]:
    values = [_identity(row) for row in rows]
    if len(values) != len(set(values)):
        raise Invalid("identity_uniqueness_drift")
    return values


def _packet_count(lane: str, index: int) -> int:
    if lane not in LANES or not 1 <= index <= LANES[lane]:
        raise Error("label_count_or_envelope_drift")
    return FINAL_PACKET_SIZE if lane == "residual_label" and index == LANES[lane] else PACKET_SIZE


def _manifest_path(package: Path) -> Path:
    path = package / "manifest.json"
    if not path.exists():
        path = package / "label-manifest.json"
    _regular(path, 0o600)
    return path


def _manifest(package: Path) -> dict[str, Any]:
    value = read(_manifest_path(package), "label manifest")
    custody_hash = _custody(package)
    if not isinstance(value, dict):
        raise Error("label_count_or_envelope_drift")
    if (
        value.get("schema_version") not in {MANIFEST_SCHEMA_VERSION, "phase3_cycle007_label_manifest_v2"}
        or value.get("evaluation_cycle_id") != CYCLE
        or value.get("source_evaluation_cycle_id") != "phase3-v2-1-evaluation-cycle-005"
        or value.get("custody_receipt_raw_sha256") != custody_hash
        or value.get("text_free") is not True
        or not isinstance(value.get("packets"), list)
    ):
        raise Error("label_count_or_envelope_drift")
    return value


def _custody(package: Path) -> str:
    path = package / "custody-receipt.json"
    _regular(path, 0o600)
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, Invalid):
        raise Error("label_count_or_envelope_drift") from None
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != "phase3_cycle007_custody_receipt_v1"
        or value.get("evaluation_cycle_id") != CYCLE
        or value.get("source_evaluation_cycle_id") != "phase3-v2-1-evaluation-cycle-005"
        or value.get("source_custody_receipt_raw_sha256") != SOURCE_CUSTODY_SHA256
        or value.get("source_label_manifest_raw_sha256") != SOURCE_MANIFEST_SHA256
        or value.get("ordered_identity_commitment_sha256") != ORDERED_IDENTITY_COMMITMENT_SHA256
        or value.get("text_free") is not True
    ):
        raise Error("label_count_or_envelope_drift")
    return digest(raw)


def prompt_binding(package: Path, lane: str) -> tuple[Path, str, str]:
    relative = PROMPTS[lane]
    prompt_path = package / relative
    _regular(prompt_path, 0o600)
    prompt_raw = prompt_path.read_bytes()
    expected_hash = digest(prompt_raw)
    return prompt_path, relative, expected_hash


def packet(package: Path, lane: str, index: int) -> tuple[Path, dict[str, Any], Path, dict[str, Any]]:
    _directory(package, 0o700)
    if lane not in LANES:
        raise Error("label_count_or_envelope_drift")
    count = _packet_count(lane, index)
    path = package / lane / f"packet-{index:04d}.json"
    _regular(path, 0o600)
    value = read(path, "private packet")
    if (
        not isinstance(value, dict)
        or set(value)
        != {
            "schema_version",
            "evaluation_cycle_id",
            "lane",
            "packet_index",
            "row_count",
            "rows",
            "packet_identity_set_sha256",
        }
        or value.get("schema_version") not in {PACKET_SCHEMA_VERSION, "phase3_cycle007_private_packet_v1"}
        or value.get("evaluation_cycle_id") != CYCLE
        or value.get("lane") != lane
        or value.get("packet_index") != index
        or value.get("row_count") != count
        or not isinstance(value.get("rows"), list)
        or len(value["rows"]) != count
    ):
        raise Error("label_count_or_envelope_drift")
    ids = identities(value["rows"])
    if value.get("packet_identity_set_sha256") != digest(canonical(sorted(ids))):
        raise Error("identity_or_order_drift")
    manifest = _manifest(package)
    matches = [
        item
        for item in manifest["packets"]
        if isinstance(item, dict) and item.get("lane") == lane and item.get("packet_index") == index
    ]
    expected = {
        "lane": lane,
        "packet_index": index,
        "canonical_basename": path.name,
        "row_count": count,
        "raw_sha256": digest(path.read_bytes()),
        "packet_identity_set_sha256": value["packet_identity_set_sha256"],
    }
    if len(matches) != 1 or matches[0] != expected:
        raise Error("identity_or_order_drift")

    sidecar_path = package / lane / f"evidence-{index:04d}.json"
    _regular(sidecar_path, 0o600)
    sidecar_val = read(sidecar_path, "evidence sidecar")
    if (
        not isinstance(sidecar_val, dict)
        or sidecar_val.get("schema_version") != "phase3_cycle007_evidence_sidecar_v1"
        or sidecar_val.get("evaluation_cycle_id") != CYCLE
        or sidecar_val.get("lane") != lane
        or sidecar_val.get("packet_index") != index
        or sidecar_val.get("row_count") != count
        or not isinstance(sidecar_val.get("rows"), list)
        or len(sidecar_val["rows"]) != count
    ):
        raise Error("sidecar_binding_drift")
    sidecar_ids = identities(sidecar_val["rows"])
    if sidecar_ids != ids:
        raise Error("sidecar_binding_drift")

    return path, value, sidecar_path, sidecar_val


def _semantic_failure(exc: Exception) -> Invalid:
    text = str(exc)
    mapping = {
        "response envelope drift": "label_count_or_envelope_drift",
        "identity/order drift": "identity_or_order_drift",
        "identity uniqueness drift": "identity_uniqueness_drift",
        "clean schema drift": "clean_label_schema_drift",
        "clean invariant": "clean_label_invariant_drift",
        "residual schema drift": "residual_label_schema_drift",
        "residual phenomenon drift": "residual_phenomenon_drift",
        "scored decision insufficiency": "residual_scored_decision_insufficiency",
        "2019 positive forbidden": "residual_2019_positive_forbidden",
        "taxonomy order/unique drift": "residual_taxonomy_order_or_uniqueness_drift",
        "primary/rollup drift": "residual_primary_or_rollup_drift",
        "null rollup drift": "residual_null_rollup_drift",
        "evidence id order/unique drift": "evidence_id_order_drift",
        "cross_row_evidence": "cross_row_evidence",
        "cross_phenomenon_evidence": "cross_phenomenon_evidence",
        "insufficient_evidence_for_decision": "insufficient_evidence_for_decision",
        "evidence_id_hash_drift": "evidence_id_hash_drift",
        "query_sha256_hash_drift": "query_sha256_hash_drift",
        "sidecar row count drift": "sidecar_binding_drift",
        "source_role_boundary_violation": "source_role_boundary_violation",
        "evidence_shape_drift": "evidence_shape_drift",
        "unknown_decision_code": "unknown_decision_code",
    }
    return Invalid(mapping.get(text, "stream_json_invalid"))


def validate(
    lane: str, packet_value: dict[str, Any], raw: bytes, sidecar: dict[str, Any] | None = None
) -> dict[str, Any]:
    try:
        return SOURCE.validate(lane, packet_value, raw, sidecar=sidecar)
    except SOURCE.Invalid as exc:
        raise _semantic_failure(exc) from exc


def _decode_provider(raw: bytes, packet_value: dict[str, Any], sidecar_value: dict[str, Any] | None = None) -> bytes:
    try:
        direct = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, Invalid):
        lines = [line for line in raw.splitlines() if line.strip()]
        if not lines:
            raise Invalid("stream_json_invalid") from None
        events: list[Any] = []
        for line in lines:
            try:
                events.append(json.loads(line.decode("utf-8", "strict"), object_pairs_hook=pairs))
            except (UnicodeDecodeError, json.JSONDecodeError, Invalid):
                raise Invalid("stream_json_invalid") from None
        results = [item for item in events if isinstance(item, dict) and item.get("event") == "result"]
        if len(results) != 1:
            raise Invalid("terminal_result_count_drift") from None
        result = results[0]
        if result.get("status") != "SUCCESS" or not isinstance(result.get("structured_output"), dict):
            raise Invalid("structured_output_envelope_drift") from None
        direct = result["structured_output"]
    if isinstance(direct, dict) and "structured_output" in direct:
        if (
            set(direct) != {"status", "structured_output"}
            or direct.get("status") != "SUCCESS"
            or not isinstance(direct["structured_output"], dict)
        ):
            raise Invalid("structured_output_envelope_drift")
        direct = direct["structured_output"]
    canonical_value = canonical(direct)
    validate(packet_value["lane"], packet_value, canonical_value, sidecar=sidecar_value)
    return canonical_value


def _prompt(package_packet: Path, sidecar_path: Path, lane: str) -> bytes:
    try:
        package = package_packet.parents[1]
        prompt_path, basename, expected_hash = prompt_binding(package, lane)
        prompt_raw = prompt_path.read_bytes()
    except (KeyError, Error, OSError):
        raise Error("label_count_or_envelope_drift") from None
    if prompt_path.as_posix().endswith(basename) is False or digest(prompt_raw) != expected_hash:
        raise Error("label_count_or_envelope_drift")
    return (
        prompt_raw
        + b"\n\n--- BEGIN IMMUTABLE PRIVATE PACKET JSON ---\n"
        + package_packet.read_bytes()
        + b"\n--- END IMMUTABLE PRIVATE PACKET JSON ---\n"
        + b"\n--- BEGIN IMMUTABLE EVIDENCE SIDECAR JSON ---\n"
        + sidecar_path.read_bytes()
        + b"\n--- END IMMUTABLE EVIDENCE SIDECAR JSON ---\n"
    )


def _mark(out: Path, lane: str, index: int, attempt: int, code: str, *, retryable: bool) -> None:
    atomic(
        out / f"attempt-{attempt}-{index:04d}.terminal.json",
        {
            "schema_version": "phase3_cycle007_grok_attempt_v1",
            "evaluation_cycle_id": CYCLE,
            "amendment_sha256": AMENDMENT_SHA256,
            "lane": lane,
            "packet_index": index,
            "attempt": attempt,
            "failure_code": code if code in FAILURE_CODES else "stream_json_invalid",
            "retryable": retryable,
            "text_free": True,
        },
    )


def _stop(package: Path, lane: str, index: int, code: str) -> None:
    path = package / OUTPUT_ROOT / "provider-stop.json"
    if path.exists() or path.is_symlink():
        return
    atomic(
        path,
        {
            "schema_version": "phase3_cycle007_grok_provider_stop_v1",
            "evaluation_cycle_id": CYCLE,
            "amendment_sha256": AMENDMENT_SHA256,
            "lane": lane,
            "terminal_packet_index": index,
            "failure_code": code if code in FAILURE_CODES else "stream_json_invalid",
            "new_provider_calls_allowed": False,
            "text_free": True,
        },
    )


def _receipt_paths(package: Path, lane: str, index: int) -> tuple[Path, Path, Path, Path]:
    out = package / OUTPUT_ROOT / lane
    return (
        out / f"labels-{index:04d}.json",
        out / f"receipt-{index:04d}.json",
        out / f"raw-manifest-{index:04d}.json",
        out / f"raw-{index:04d}.raw",
    )


def _verify_sealed(
    package: Path,
    lane: str,
    index: int,
    packet_path: Path,
    packet_value: dict[str, Any],
    sidecar_path: Path,
    sidecar_value: dict[str, Any],
) -> dict[str, Any]:
    labels_path, receipt_path, raw_manifest_path, raw_path = _receipt_paths(package, lane, index)
    paths = (labels_path, receipt_path, raw_manifest_path, raw_path)
    present = [path.exists() or path.is_symlink() for path in paths]
    if not any(present):
        raise Error("label_count_or_envelope_drift")
    if not all(present):
        raise Error("label_count_or_envelope_drift")
    for path in paths:
        _regular(path, 0o600)
    labels = read(labels_path, "labels")
    validate(lane, packet_value, canonical(labels), sidecar=sidecar_value)
    raw_manifest = read(raw_manifest_path, "raw manifest")
    receipt = read(receipt_path, "provider receipt")
    dynamic_manifest_hash = digest(_manifest_path(package).read_bytes())
    dynamic_custody_hash = digest((package / "custody-receipt.json").read_bytes())
    ev_manifest_path = package / "evidence-manifest.json"
    dynamic_ev_manifest_hash = digest(ev_manifest_path.read_bytes()) if ev_manifest_path.exists() else ""
    _prompt_path, prompt_name, prompt_hash = prompt_binding(package, lane)
    expected_manifest = {
        "schema_version": "phase3_cycle007_grok_raw_manifest_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "lane": lane,
        "packet_index": index,
        "row_count": packet_value["row_count"],
        "packet_raw_sha256": digest(packet_path.read_bytes()),
        "packet_identity_set_sha256": packet_value["packet_identity_set_sha256"],
        "sidecar_raw_sha256": digest(sidecar_path.read_bytes()),
        "sidecar_id": sidecar_value.get("sidecar_id", ""),
        "response_raw_sha256": digest(raw_path.read_bytes()),
        "text_free": True,
    }
    if (
        not isinstance(raw_manifest, dict)
        or set(raw_manifest) != set(expected_manifest) | {"manifest_sha256"}
        or any(raw_manifest.get(key) != value for key, value in expected_manifest.items())
        or raw_manifest.get("manifest_sha256") != digest(canonical(expected_manifest))
    ):
        raise Error("label_count_or_envelope_drift")
    expected_receipt = {
        "schema_version": "phase3_cycle007_grok_packet_label_receipt_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": dynamic_custody_hash,
        "materialization_manifest_raw_sha256": dynamic_manifest_hash,
        "lane": lane,
        "packet_index": index,
        "row_count": packet_value["row_count"],
        "packet_raw_sha256": digest(packet_path.read_bytes()),
        "packet_identity_set_sha256": packet_value["packet_identity_set_sha256"],
        "sidecar_raw_sha256": digest(sidecar_path.read_bytes()),
        "sidecar_id": sidecar_value.get("sidecar_id", ""),
        "raw_manifest_sha256": digest(raw_manifest_path.read_bytes()),
        "labels_sha256": digest(labels_path.read_bytes()),
        "response_raw_sha256": digest(raw_path.read_bytes()),
        "prompt_path": prompt_name,
        "prompt_sha256": prompt_hash,
        "attempt_count": receipt.get("attempt_count"),
        "exact_model": "grok-4.5",
        "model_family": "xai",
        "harness": "native_grok",
        "text_free": True,
    }
    if dynamic_ev_manifest_hash:
        expected_receipt["evidence_manifest_raw_sha256"] = dynamic_ev_manifest_hash
    if (
        not isinstance(receipt, dict)
        or receipt.get("receipt_sha256")
        != digest(canonical({key: value for key, value in receipt.items() if key != "receipt_sha256"}))
        or set(receipt) != set(expected_receipt) | {"receipt_sha256"}
        or receipt.get("attempt_count") not in {1, 2}
        or any(receipt.get(key) != value for key, value in expected_receipt.items())
    ):
        raise Error("label_count_or_envelope_drift")
    return {
        "ok": True,
        "lane": lane,
        "packet_index": index,
        "attempt_count": receipt["attempt_count"],
        "resumed": True,
        "text_free": True,
    }


def _provider_command(provider: Path) -> list[str]:
    return [
        str(provider),
        "--model",
        "grok-4.5",
        "--reasoning-effort",
        "high",
        "--output-format",
        "plain",
        "--permission-mode",
        "plan",
        "--no-alt-screen",
        "--no-memory",
        "--no-subagents",
        "--disable-web-search",
        "--verbatim",
    ]


def _provider_mode(provider: Path, *, synthetic_provider: bool) -> None:
    """Make synthetic executables explicit and reject fake live providers."""
    try:
        resolved = provider.resolve(strict=True)
        live = GROK.resolve(strict=True)
    except OSError as exc:
        if synthetic_provider:
            return
        raise Error("label_count_or_envelope_drift") from exc
    if synthetic_provider:
        if resolved == live:
            raise Error("label_count_or_envelope_drift")
    elif resolved != live:
        raise Error("label_count_or_envelope_drift")


def run_packet(
    package: Path,
    lane: str,
    index: int,
    provider: Path = GROK,
    *,
    synthetic_provider: bool = False,
) -> dict[str, Any]:
    _provider_mode(provider, synthetic_provider=synthetic_provider)
    packet_path, packet_value, sidecar_path, sidecar_value = packet(package, lane, index)
    labels_path, receipt_path, raw_manifest_path, raw_path = _receipt_paths(package, lane, index)
    present = [path.exists() or path.is_symlink() for path in (labels_path, receipt_path, raw_manifest_path, raw_path)]
    if all(present):
        return _verify_sealed(package, lane, index, packet_path, packet_value, sidecar_path, sidecar_value)
    if any(present):
        _stop(package, lane, index, "label_count_or_envelope_drift")
        raise Error("label_count_or_envelope_drift")
    if (package / OUTPUT_ROOT / "provider-stop.json").exists():
        raise Error("label_count_or_envelope_drift")
    out = package / OUTPUT_ROOT / lane
    out.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(package / OUTPUT_ROOT, 0o700)
    os.chmod(out, 0o700)
    try:
        prompt_bytes = _prompt(packet_path, sidecar_path, lane)
        for attempt in (1, 2):
            marker = out / f"attempt-{attempt}-{index:04d}.terminal.json"
            started = out / f"attempt-{attempt}-{index:04d}.started.json"
            if started.exists() and not marker.exists():
                raise Error("label_count_or_envelope_drift")
            if marker.exists():
                if attempt == 2:
                    raise Error("label_count_or_envelope_drift")
                continue
            atomic(
                started,
                {
                    "schema_version": "phase3_cycle007_grok_attempt_v1",
                    "evaluation_cycle_id": CYCLE,
                    "amendment_sha256": AMENDMENT_SHA256,
                    "lane": lane,
                    "packet_index": index,
                    "attempt": attempt,
                    "state": "started",
                    "text_free": True,
                },
            )
            raw_capture: bytes | None = None
            try:
                run = subprocess.run(
                    _provider_command(provider),
                    input=prompt_bytes,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
                if run.returncode != 0:
                    raise Invalid("stream_json_invalid")
                raw_capture = run.stdout
                canonical_labels = _decode_provider(raw_capture, packet_value, sidecar_value=sidecar_value)
            except Invalid as exc:
                retryable = attempt == 1 and exc.failure_code in STRUCTURAL_CODES
                _mark(out, lane, index, attempt, exc.failure_code, retryable=retryable)
                if retryable:
                    continue
                _stop(package, lane, index, exc.failure_code)
                raise Error(exc.failure_code) from None
            assert raw_capture is not None
            atomic(raw_path, raw_capture, raw=True)
            atomic(labels_path, json.loads(canonical_labels.decode("utf-8")), raw=False)
            dynamic_manifest_hash = digest(_manifest_path(package).read_bytes())
            dynamic_custody_hash = digest((package / "custody-receipt.json").read_bytes())
            ev_manifest_path = package / "evidence-manifest.json"
            dynamic_ev_manifest_hash = digest(ev_manifest_path.read_bytes()) if ev_manifest_path.exists() else ""
            _prompt_path, prompt_name, prompt_hash = prompt_binding(package, lane)
            raw_manifest_data = {
                "schema_version": "phase3_cycle007_grok_raw_manifest_v1",
                "evaluation_cycle_id": CYCLE,
                "amendment_sha256": AMENDMENT_SHA256,
                "lane": lane,
                "packet_index": index,
                "row_count": packet_value["row_count"],
                "packet_raw_sha256": digest(packet_path.read_bytes()),
                "packet_identity_set_sha256": packet_value["packet_identity_set_sha256"],
                "sidecar_raw_sha256": digest(sidecar_path.read_bytes()),
                "sidecar_id": sidecar_value.get("sidecar_id", ""),
                "response_raw_sha256": digest(raw_capture),
                "text_free": True,
            }
            raw_manifest_data["manifest_sha256"] = digest(canonical(raw_manifest_data))
            atomic(raw_manifest_path, raw_manifest_data)
            receipt_data = {
                "schema_version": "phase3_cycle007_grok_packet_label_receipt_v1",
                "evaluation_cycle_id": CYCLE,
                "amendment_sha256": AMENDMENT_SHA256,
                "custody_receipt_raw_sha256": dynamic_custody_hash,
                "materialization_manifest_raw_sha256": dynamic_manifest_hash,
                "lane": lane,
                "packet_index": index,
                "row_count": packet_value["row_count"],
                "packet_raw_sha256": digest(packet_path.read_bytes()),
                "packet_identity_set_sha256": packet_value["packet_identity_set_sha256"],
                "sidecar_raw_sha256": digest(sidecar_path.read_bytes()),
                "sidecar_id": sidecar_value.get("sidecar_id", ""),
                "raw_manifest_sha256": digest(raw_manifest_path.read_bytes()),
                "labels_sha256": digest(labels_path.read_bytes()),
                "response_raw_sha256": digest(raw_capture),
                "prompt_path": prompt_name,
                "prompt_sha256": prompt_hash,
                "attempt_count": attempt,
                "exact_model": "grok-4.5",
                "model_family": "xai",
                "harness": "native_grok",
                "text_free": True,
            }
            if dynamic_ev_manifest_hash:
                receipt_data["evidence_manifest_raw_sha256"] = dynamic_ev_manifest_hash
            receipt_data["receipt_sha256"] = digest(canonical(receipt_data))
            atomic(receipt_path, receipt_data)
            return {
                "ok": True,
                "lane": lane,
                "packet_index": index,
                "attempt_count": attempt,
                "text_free": True,
            }
    except Error:
        raise
    except BaseException as exc:
        _stop(package, lane, index, "stream_json_invalid")
        raise Error("stream_json_invalid") from exc
    raise Error("stream_json_invalid")


def verify_packet(package: Path, lane: str, index: int) -> dict[str, Any]:
    packet_path, packet_value, sidecar_path, sidecar_value = packet(package, lane, index)
    return _verify_sealed(package, lane, index, packet_path, packet_value, sidecar_path, sidecar_value)


def batch(
    package: Path,
    lane: str,
    start: int,
    end: int,
    provider: Path = GROK,
    *,
    concurrency: int = 1,
    synthetic_provider: bool = False,
) -> dict[str, Any]:
    """Execute packet range with concurrency fixed at 1."""
    if lane not in LANES or not 1 <= start <= end <= LANES[lane] or concurrency != 1:
        raise Error("label_count_or_envelope_drift")
    if (package / OUTPUT_ROOT / "provider-stop.json").exists():
        raise Error("label_count_or_envelope_drift")
    results = []
    for index in range(start, end + 1):
        if (package / OUTPUT_ROOT / "provider-stop.json").exists():
            raise Error("label_count_or_envelope_drift")
        results.append(run_packet(package, lane, index, provider, synthetic_provider=synthetic_provider))
    return {
        "ok": True,
        "lane": lane,
        "start": start,
        "end": end,
        "packet_count": len(results),
        "concurrency": 1,
        "text_free": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True, help="0700 operator-owned Cycle-007 package")
    parser.add_argument("--lane", choices=tuple(LANES), required=True, help="frozen packet lane")
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--packet-index", type=int, help="one-based frozen packet index")
    selector.add_argument("--start", type=int, help="inclusive contiguous batch range start")
    parser.add_argument("--end", type=int, help="inclusive contiguous batch range end (required with --start)")
    parser.add_argument("--concurrency", type=int, default=1, help="must remain one for fail-stop execution")
    parser.add_argument("--test-provider-bin", type=Path, help="synthetic provider executable only")
    args = parser.parse_args()
    try:
        if args.concurrency != 1:
            raise Error("label_count_or_envelope_drift")
        package = args.package.resolve()
        synthetic = args.test_provider_bin is not None
        provider = args.test_provider_bin.resolve() if synthetic else GROK
        if args.packet_index is not None:
            if args.end is not None:
                raise Error("label_count_or_envelope_drift")
            result = run_packet(package, args.lane, args.packet_index, provider, synthetic_provider=synthetic)
        elif args.start is not None and args.end is not None:
            result = batch(
                package,
                args.lane,
                args.start,
                args.end,
                provider,
                concurrency=args.concurrency,
                synthetic_provider=synthetic,
            )
        else:
            raise Error("label_count_or_envelope_drift")
    except Error as exc:
        result = {"ok": False, "failure_code": exc.failure_code, "text_free": True}
    except Exception:
        result = {"ok": False, "failure_code": "stream_json_invalid", "text_free": True}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
