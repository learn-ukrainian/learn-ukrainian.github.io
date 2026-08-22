#!/usr/bin/env python3
"""Run one private Cycle-006 Gemini packet through the identity-bound transport.

The runner is deliberately packet-scoped.  It accepts an operator-owned package,
never discovers one, and emits only text-free receipts on stdout.  Private prompt
material is supplied to AGY through a 0600 stdin file; it is never an argument.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
CYCLE = "phase3-v2-1-evaluation-cycle-006"
EXPECTED_CUSTODY_SHA256 = ""
EXPECTED_LABEL_MANIFEST_SHA256 = ""
MODEL = "Gemini 3.6 Flash (High)"
FAMILY = "google"
HARNESS = "agy"
AGY = Path("/Users/krisztiankoos/.local/bin/agy")
OUTPUT = "label-output-gemini-v2"
CHUNK_SIZE = 20
LANES = {"clean_label": 40, "residual_label": 164}
PROMPTS = {
    "clean_label": "prompts/gemini-clean-label.md",
    "residual_label": "prompts/gemini-residual-label.md",
}
SOURCE_VALIDATOR = HERE / "phase3-cycle006-label-validation-v2.py"
SOURCE_VALIDATOR_SHA256 = "a19e34eb5784861155d9a9158b8234c3de1fb8a9448b0d79101a87686a0724ac"
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
    }
)
ATTEMPT_FAILURE_STAGES = frozenset(
    {"package_binding", "executable_binding", "provider_return", "stream_parse", "result_validation"}
)
EVENT_KINDS = frozenset({"empty", "init", "result", "other", "unavailable"})
EXECUTABLE_BINDINGS = frozenset({"not_checked", "verified", "mismatch", "unavailable", "synthetic"})
RETURN_CODES = frozenset({"not_started", "zero", "nonzero"})
RESULT_STATUSES = frozenset({"not_inspected", "success", "non_success", "missing"})
STRUCTURED_OUTPUT_TYPES = frozenset({"not_inspected", "missing", "object", "string", "null", "other"})


def _load_validator() -> Any:
    source_path = SOURCE_VALIDATOR
    if (
        not source_path.is_file()
        or source_path.is_symlink()
        or hashlib.sha256(source_path.read_bytes()).hexdigest() != SOURCE_VALIDATOR_SHA256
    ):
        raise RuntimeError("Cycle-006 semantic validator hash drift")
    spec = importlib.util.spec_from_file_location("cycle006_public_semantic_validator", source_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cycle-006 semantic validator unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SOURCE = _load_validator()


class Error(ValueError):
    """A text-free transport failure."""

    def __init__(self, code: str, *, structural: bool = False) -> None:
        self.code = code if code in FAILURE_CODES else "ordinal_identity_binding_drift"
        self.structural = structural
        super().__init__(self.code)


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise Error("stream_json_invalid", structural=True)
        result[key] = value
    return result


def _mode(path: Path, expected: int) -> None:
    if not path.exists() or path.is_symlink() or stat.S_IMODE(path.stat().st_mode) != expected:
        raise Error("ordinal_identity_binding_drift")


def _private_dir(path: Path) -> None:
    if not path.is_dir() or path.is_symlink() or stat.S_IMODE(path.stat().st_mode) != 0o700:
        raise Error("ordinal_identity_binding_drift")


def _mkdir_private(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path, 0o700)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        _mode(path, 0o600)
        value = json.loads(path.read_bytes().decode("utf-8", "strict"), object_pairs_hook=_pairs)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, Error) as exc:
        raise Error("ordinal_identity_binding_drift") from exc
    if not isinstance(value, dict):
        raise Error("ordinal_identity_binding_drift")
    return value


def _atomic(path: Path, value: Any, *, raw: bool = False) -> str:
    data = value if raw else canonical(value)
    _mkdir_private(path.parent)
    if path.exists() or path.is_symlink():
        _mode(path, 0o600)
        if path.read_bytes() != data:
            raise Error("ordinal_identity_binding_drift")
        return digest(data)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return digest(data)


def _identity(row: dict[str, Any]) -> tuple[str, str]:
    unit_id, unit_sha256 = row.get("unit_id"), row.get("unit_sha256")
    if not isinstance(unit_id, str) or not isinstance(unit_sha256, str) or len(unit_sha256) != 64:
        raise Error("ordinal_identity_binding_drift")
    return unit_id, unit_sha256


def packet(package: Path, lane: str, index: int) -> tuple[Path, dict[str, Any]]:
    if lane not in LANES or not 1 <= index <= LANES[lane]:
        raise Error("ordinal_identity_binding_drift")
    _private_dir(package)
    custody = package / "custody-receipt.json"
    _mode(custody, 0o600)
    if len(EXPECTED_CUSTODY_SHA256) != 64 or digest(custody.read_bytes()) != EXPECTED_CUSTODY_SHA256:
        raise Error("ordinal_identity_binding_drift")
    path = package / lane / f"packet-{index:04d}.json"
    value = _read_json(path)
    count = 9 if lane == "residual_label" and index == LANES[lane] else 50
    expected_keys = {
        "schema_version",
        "evaluation_cycle_id",
        "lane",
        "packet_index",
        "row_count",
        "rows",
        "packet_identity_set_sha256",
    }
    manifest_path = package / "label-manifest.json"
    _mode(manifest_path, 0o600)
    if (
        len(EXPECTED_LABEL_MANIFEST_SHA256) != 64
        or digest(manifest_path.read_bytes()) != EXPECTED_LABEL_MANIFEST_SHA256
    ):
        raise Error("ordinal_identity_binding_drift")
    manifest = _read_json(manifest_path)
    prompt_entries = manifest.get("prompt_bindings")
    custody_value = _read_json(custody)
    custody_bindings = custody_value.get("prompt_bindings")
    expected_prompt_keys = {(prompt_lane, provider) for prompt_lane in LANES for provider in ("gemini", "grok")}
    if (
        not isinstance(prompt_entries, list)
        or prompt_entries != custody_bindings
        or len(prompt_entries) != len(expected_prompt_keys)
    ):
        raise Error("ordinal_identity_binding_drift")
    bindings: dict[tuple[str, str], dict[str, Any]] = {}
    for binding in prompt_entries:
        if not isinstance(binding, dict) or set(binding) != {"lane", "provider", "path", "sha256"}:
            raise Error("ordinal_identity_binding_drift")
        lane_key, provider, prompt_path, prompt_hash = (
            binding.get("lane"),
            binding.get("provider"),
            binding.get("path"),
            binding.get("sha256"),
        )
        if (
            not isinstance(lane_key, str)
            or not isinstance(provider, str)
            or not isinstance(prompt_path, str)
            or not isinstance(prompt_hash, str)
            or len(prompt_hash) != 64
        ):
            raise Error("ordinal_identity_binding_drift")
        identity = (lane_key, provider)
        if identity in bindings:
            raise Error("ordinal_identity_binding_drift")
        bindings[identity] = binding
    if set(bindings) != expected_prompt_keys:
        raise Error("ordinal_identity_binding_drift")
    prompt_hashes = manifest.get("prompt_sha256s")
    if prompt_hashes != custody_value.get("prompt_sha256s") or not isinstance(prompt_hashes, dict):
        raise Error("ordinal_identity_binding_drift")
    for binding in bindings.values():
        if prompt_hashes.get(binding["path"]) != binding["sha256"]:
            raise Error("ordinal_identity_binding_drift")
    if (
        set(value) != expected_keys
        or value.get("schema_version") != "phase3_cycle006_private_packet_v1"
        or value.get("evaluation_cycle_id") != CYCLE
        or value.get("lane") != lane
        or value.get("packet_index") != index
        or value.get("row_count") != count
        or not isinstance(value.get("rows"), list)
        or len(value["rows"]) != count
    ):
        raise Error("ordinal_identity_binding_drift")
    identities = [_identity(row) for row in value["rows"] if isinstance(row, dict)]
    if len(identities) != count or len(identities) != len(set(identities)):
        raise Error("ordinal_identity_binding_drift")
    if value.get("packet_identity_set_sha256") != digest(canonical(sorted(identities))):
        raise Error("ordinal_identity_binding_drift")
    entries = [
        item
        for item in manifest.get("packets", [])
        if isinstance(item, dict) and item.get("lane") == lane and item.get("packet_index") == index
    ]
    expected_entry = {
        "lane": lane,
        "packet_index": index,
        "canonical_basename": path.name,
        "row_count": count,
        "raw_sha256": digest(path.read_bytes()),
        "packet_identity_set_sha256": value["packet_identity_set_sha256"],
    }
    if (
        manifest.get("schema_version") != "phase3_cycle006_label_manifest_v2"
        or manifest.get("evaluation_cycle_id") != CYCLE
        or manifest.get("custody_receipt_raw_sha256") != EXPECTED_CUSTODY_SHA256
        or manifest.get("receipt_sha256")
        != digest(canonical({key: item for key, item in manifest.items() if key != "receipt_sha256"}))
        or entries != [expected_entry]
    ):
        raise Error("ordinal_identity_binding_drift")
    for binding in bindings.values():
        prompt_path = package / binding["path"]
        _mode(prompt_path, 0o600)
        if digest(prompt_path.read_bytes()) != binding["sha256"]:
            raise Error("ordinal_identity_binding_drift")
    return path, value


def frozen_prompt(package: Path, lane: str) -> bytes:
    """Read the materialized immutable prompt, bound by the label-manifest receipt."""
    manifest_path = package / "label-manifest.json"
    _mode(manifest_path, 0o600)
    if (
        len(EXPECTED_LABEL_MANIFEST_SHA256) != 64
        or digest(manifest_path.read_bytes()) != EXPECTED_LABEL_MANIFEST_SHA256
    ):
        raise Error("ordinal_identity_binding_drift")
    manifest = _read_json(manifest_path)
    custody = _read_json(package / "custody-receipt.json")
    bindings = manifest.get("prompt_bindings")
    if bindings != custody.get("prompt_bindings") or not isinstance(bindings, list):
        raise Error("ordinal_identity_binding_drift")
    matches = [
        item
        for item in bindings
        if isinstance(item, dict) and item.get("lane") == lane and item.get("provider") == "gemini"
    ]
    if len(matches) != 1 or matches[0].get("path") != PROMPTS[lane] or not isinstance(matches[0].get("sha256"), str):
        raise Error("ordinal_identity_binding_drift")
    path, expected_hash = package / matches[0]["path"], matches[0]["sha256"]
    _mode(path, 0o600)
    value = path.read_bytes()
    if digest(value) != expected_hash:
        raise Error("ordinal_identity_binding_drift")
    return value


def compose_prompt(template: bytes, lane: str, part: dict[str, Any]) -> str:
    """Retain the manifest-bound Cycle-006 instructions and append only the packet."""
    try:
        base = template.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise Error("ordinal_identity_binding_drift") from exc
    packet_value = {
        "evaluation_cycle_id": CYCLE,
        "lane": lane,
        "chunk_index": part["chunk_index"],
        "chunk_count": part["chunk_count"],
        "rows": part["rows"],
    }
    return (
        base
        + "--- BEGIN IMMUTABLE PRIVATE PACKET JSON ---\n"
        + canonical(packet_value).decode("utf-8")
        + "--- END IMMUTABLE PRIVATE PACKET JSON ---\n"
    )


def chunks(contents: dict[str, Any]) -> list[dict[str, Any]]:
    rows = contents["rows"]
    total = (len(rows) + CHUNK_SIZE - 1) // CHUNK_SIZE
    return [
        {
            "chunk_index": offset + 1,
            "chunk_count": total,
            "rows": rows[offset * CHUNK_SIZE : (offset + 1) * CHUNK_SIZE],
        }
        for offset in range(total)
    ]


def schema(lane: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    if lane not in LANES or not 1 <= len(rows) <= CHUNK_SIZE:
        raise Error("ordinal_identity_binding_drift")

    def label_for(row: dict[str, Any]) -> dict[str, Any]:
        identity = {"unit_id": {"enum": [row["unit_id"]]}, "unit_sha256": {"enum": [row["unit_sha256"]]}}
        if lane == "clean_label":
            return {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "unit_id",
                    "unit_sha256",
                    "decision_code",
                    "clean_modern_standard_prose",
                    "modern_genre_id",
                ],
                "properties": identity
                | {
                    "decision_code": {"enum": sorted(SOURCE.REJECTS)},
                    "clean_modern_standard_prose": {"type": "boolean"},
                    "modern_genre_id": {"anyOf": [{"enum": sorted(SOURCE.GENRES)}, {"type": "null"}]},
                },
            }
        phenomenon = {
            "type": "object",
            "additionalProperties": False,
            "required": ["phenomenon_id", "decision_code", "evidence_sufficiency"],
            "properties": {
                "phenomenon_id": {"enum": list(SOURCE.TAX)},
                "decision_code": {"enum": sorted(SOURCE.DEC)},
                "evidence_sufficiency": {"enum": ["sufficient", "insufficient"]},
            },
        }
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["unit_id", "unit_sha256", "phenomena", "primary_phenomenon_id", "item_decision_rollup"],
            "properties": identity
            | {
                "phenomena": {"type": "array", "minItems": 1, "items": phenomenon},
                "primary_phenomenon_id": {"anyOf": [{"enum": list(SOURCE.TAX)}, {"type": "null"}]},
                "item_decision_rollup": {"enum": sorted(SOURCE.DEC)},
            },
        }

    properties = {f"p{position:02d}": label_for(row) for position, row in enumerate(rows, 1)}
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["labels_by_position"],
        "properties": {
            "labels_by_position": {
                "type": "object",
                "additionalProperties": False,
                "required": list(properties),
                "properties": properties,
            }
        },
    }


def _agy_stream(raw: bytes) -> tuple[dict[str, Any], dict[str, Any]]:
    """Parse the documented AGY stream-json init → result event sequence."""
    try:
        events = [
            json.loads(line, object_pairs_hook=_pairs)
            for line in raw.decode("utf-8", "strict").splitlines()
            if line.strip()
        ]
    except (UnicodeDecodeError, json.JSONDecodeError, Error) as exc:
        raise Error("stream_json_invalid", structural=True) from exc
    if not events:
        raise Error("stream_json_invalid", structural=True)
    init_events = [event for event in events if isinstance(event, dict) and event.get("event") == "init"]
    result_events = [event for event in events if isinstance(event, dict) and event.get("event") == "result"]
    if len(init_events) != 1 or len(result_events) != 1:
        raise Error("terminal_result_count_drift", structural=True)
    if events[0] is not init_events[0] or events[-1] is not result_events[0]:
        raise Error("terminal_result_count_drift", structural=True)
    init, result_event = init_events[0], result_events[0]
    config, result = init.get("init"), result_event.get("result")
    if not isinstance(config, dict) or config.get("model") != MODEL:
        raise Error("structured_output_envelope_drift", structural=True)
    if not isinstance(result, dict) or result.get("status") != "SUCCESS" or "structured_output" not in result:
        raise Error("structured_output_envelope_drift", structural=True)
    return init, result


def _extract(raw: bytes) -> dict[str, Any]:
    _, result = _agy_stream(raw)
    output = result["structured_output"]
    if isinstance(output, str):
        try:
            output = json.loads(output, object_pairs_hook=_pairs)
        except (json.JSONDecodeError, Error) as exc:
            raise Error("label_json_invalid", structural=True) from exc
    if not isinstance(output, dict):
        raise Error("structured_output_envelope_drift", structural=True)
    return output


def _semantic_failure(exc: Exception) -> Error:
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
    }
    return Error(mapping.get(text, "ordinal_identity_binding_drift"), structural=False)


def normalize(lane: str, part: dict[str, Any], structured: dict[str, Any]) -> dict[str, Any]:
    if set(structured) != {"labels_by_position"} or not isinstance(structured.get("labels_by_position"), dict):
        raise Error("label_count_or_envelope_drift", structural=True)
    positions = structured["labels_by_position"]
    expected = [f"p{item:02d}" for item in range(1, len(part["rows"]) + 1)]
    if set(positions) != set(expected):
        raise Error("ordinal_key_drift", structural=True)
    labels: list[dict[str, Any]] = []
    for key, row in zip(expected, part["rows"], strict=True):
        label = positions[key]
        if not isinstance(label, dict) or _identity(label) != _identity(row):
            raise Error("ordinal_identity_binding_drift")
        labels.append(label)
    result = {"labels": labels}
    try:
        SOURCE.validate(lane, {"rows": part["rows"]}, canonical(result))
    except SOURCE.Invalid as exc:
        raise _semantic_failure(exc) from exc
    return result


def _stream_metadata(raw: bytes | None) -> dict[str, Any]:
    """Return bounded stream facts only; never retain an event body."""
    result: dict[str, Any] = {
        "raw_byte_count": 0 if raw is None else len(raw),
        "raw_sha256": digest(b"" if raw is None else raw),
        "init_count": 0,
        "result_count": 0,
        "first_event_kind": "unavailable" if raw is None else "empty",
        "last_event_kind": "unavailable" if raw is None else "empty",
        "model_binding_result": "not_inspected",
        "result_status": "not_inspected",
        "structured_output_type": "not_inspected",
    }
    if raw is None:
        return result
    try:
        events = [json.loads(line, object_pairs_hook=_pairs) for line in raw.decode("utf-8", "strict").splitlines() if line.strip()]
    except (UnicodeDecodeError, json.JSONDecodeError, Error):
        return result
    if not events:
        return result
    def kind(value: Any) -> str:
        value = value.get("event") if isinstance(value, dict) else None
        return value if value in {"init", "result"} else "other"
    result["first_event_kind"], result["last_event_kind"] = kind(events[0]), kind(events[-1])
    init = [event for event in events if isinstance(event, dict) and event.get("event") == "init"]
    terminal = [event for event in events if isinstance(event, dict) and event.get("event") == "result"]
    result["init_count"], result["result_count"] = min(len(init), 255), min(len(terminal), 255)
    if len(init) == 1 and isinstance(init[0].get("init"), dict):
        result["model_binding_result"] = "verified" if init[0]["init"].get("model") == MODEL else "mismatch"
    elif init:
        result["model_binding_result"] = "missing"
    if len(terminal) == 1 and isinstance(terminal[0].get("result"), dict):
        body = terminal[0]["result"]
        result["result_status"] = "success" if body.get("status") == "SUCCESS" else "non_success"
        output = body.get("structured_output")
        result["structured_output_type"] = (
            "missing" if "structured_output" not in body else "object" if isinstance(output, dict) else "string"
            if isinstance(output, str) else "null" if output is None else "other"
        )
    elif terminal:
        result["result_status"] = "missing"
    return result


def _attempt_metadata(
    raw_path: Path | None = None,
    log_path: Path | None = None,
    *,
    provider_call_started: bool = False,
    executable_binding_result: str = "not_checked",
    provider_return_code: str = "not_started",
) -> dict[str, Any]:
    raw = raw_path.read_bytes() if raw_path is not None and raw_path.is_file() and not raw_path.is_symlink() else None
    log = log_path.read_bytes() if log_path is not None and log_path.is_file() and not log_path.is_symlink() else None
    result = _stream_metadata(raw)
    result.update(
        {
            "provider_call_started": provider_call_started,
            "executable_binding_result": executable_binding_result if executable_binding_result in EXECUTABLE_BINDINGS else "unavailable",
            "provider_return_code": provider_return_code if provider_return_code in RETURN_CODES else "nonzero",
            "log_byte_count": 0 if log is None else len(log),
            "log_sha256": digest(b"" if log is None else log),
        }
    )
    return result


def _mark(
    out: Path, lane: str, packet_index: int, chunk_index: int, attempt: int, state: str, code: str | None = None,
    *, metadata: dict[str, Any] | None = None, failure_stage: str | None = None,
) -> None:
    value: dict[str, Any] = {
        "schema_version": "phase3_cycle006_gemini_attempt_v2",
        "evaluation_cycle_id": CYCLE,
        "lane": lane,
        "packet_index": packet_index,
        "chunk_index": chunk_index,
        "attempt": attempt,
        "state": state,
        "exact_model": MODEL,
        "model_family": FAMILY,
        "harness": HARNESS,
        "text_free": True,
    }
    if state == "terminal":
        value["failure_code"] = code if code in FAILURE_CODES else "ordinal_identity_binding_drift"
        value["failure_stage"] = failure_stage if failure_stage in ATTEMPT_FAILURE_STAGES else "package_binding"
        value.update(metadata or _attempt_metadata())
    _atomic(out / f"attempt-{attempt}-chunk-{chunk_index:02d}.{state}.json", value)


def stop(
    package: Path, lane: str, packet_index: int, code: str, *, metadata: dict[str, Any] | None = None,
    failure_stage: str | None = None,
) -> None:
    """Atomically write the first stop; any existing stop is already authoritative."""
    path = package / OUTPUT / "provider-stop.json"
    value = {
        "schema_version": "phase3_cycle006_gemini_provider_stop_v2",
        "evaluation_cycle_id": CYCLE,
        "lane": lane,
        "terminal_packet_index": packet_index,
        "failure_code": code if code in FAILURE_CODES else "ordinal_identity_binding_drift",
        "new_provider_calls_allowed": False,
        "exact_model": MODEL,
        "model_family": FAMILY,
        "harness": HARNESS,
        "text_free": True,
    }
    value["failure_stage"] = failure_stage if failure_stage in ATTEMPT_FAILURE_STAGES else "package_binding"
    value.update(metadata or _attempt_metadata())
    try:
        _mkdir_private(path.parent)
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        existing = _read_json(path)
        if (
            existing.get("schema_version") != "phase3_cycle006_gemini_provider_stop_v2"
            or existing.get("evaluation_cycle_id") != CYCLE
            or existing.get("failure_code") not in FAILURE_CODES
            or existing.get("new_provider_calls_allowed") is not False
            or existing.get("text_free") is not True
        ):
            raise Error("ordinal_identity_binding_drift") from None
        return
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(canonical(value))
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _command(provider: Path, schema_path: Path, log_path: Path) -> list[str]:
    """Use AGY's verified NDJSON stdin protocol; private content is not argv."""
    return [
        str(provider),
        "--model",
        MODEL,
        "--mode",
        "plan",
        "--sandbox",
        "--disable-slash-commands",
        "--input-format",
        "stream-json",
        "--output-format",
        "stream-json",
        "--json-schema",
        str(schema_path),
        "--print",
        "",
        "--log-file",
        str(log_path),
    ]


def agy_executable_sha256(provider: Path = AGY) -> str:
    """Hash the exact resolved executable immediately before a real AGY call."""
    try:
        resolved = provider.resolve(strict=True)
    except OSError as exc:
        raise Error("structured_output_envelope_drift", structural=True) from exc
    if not resolved.is_file():
        raise Error("structured_output_envelope_drift", structural=True)
    return digest(resolved.read_bytes())


def _real_agy_provider(provider: Path) -> bool:
    try:
        return provider.resolve(strict=True) == AGY.resolve(strict=True)
    except OSError:
        return False


def stdin_event(prompt: str) -> bytes:
    return canonical({"event": "user", "message": {"content": [{"type": "text", "text": prompt}]}})


def _chunk_dir(package: Path, lane: str, index: int) -> Path:
    root = package / OUTPUT
    _mkdir_private(root)
    _mkdir_private(root / lane)
    _mkdir_private(root / lane / "chunks")
    path = root / lane / "chunks" / f"packet-{index:04d}"
    _mkdir_private(path)
    return path


def _run_chunk(
    package: Path,
    lane: str,
    packet_index: int,
    part: dict[str, Any],
    provider: Path,
    expected_agy_sha256: str | None,
) -> dict[str, Any]:
    chunk_index = int(part["chunk_index"])
    out = _chunk_dir(package, lane, packet_index)
    labels_path = out / f"labels-chunk-{chunk_index:02d}.json"
    receipt_path = out / f"receipt-chunk-{chunk_index:02d}.json"
    if labels_path.exists() or receipt_path.exists():
        if not (labels_path.exists() and receipt_path.exists()):
            raise Error("ordinal_identity_binding_drift")
        _verify_chunk(package, lane, packet_index, part)
        return {"chunk_index": chunk_index, "resumed": True, "text_free": True}
    if (package / OUTPUT / "provider-stop.json").exists():
        raise Error("ordinal_identity_binding_drift")
    for attempt in (1, 2):
        started = out / f"attempt-{attempt}-chunk-{chunk_index:02d}.started.json"
        terminal = out / f"attempt-{attempt}-chunk-{chunk_index:02d}.terminal.json"
        if started.exists() and not terminal.exists():
            raise Error("ordinal_identity_binding_drift")
        if terminal.exists():
            if attempt == 2:
                raise Error("ordinal_identity_binding_drift")
            marker = _read_json(terminal)
            if marker.get("failure_code") not in {
                "stream_json_invalid",
                "terminal_result_count_drift",
                "structured_output_envelope_drift",
                "ordinal_key_drift",
                "label_json_invalid",
                "label_count_or_envelope_drift",
            }:
                raise Error("ordinal_identity_binding_drift")
            continue
        runtime = Path(
            tempfile.mkdtemp(
                prefix=f".cycle006-gemini-{lane}-{packet_index:04d}-{chunk_index:02d}-{attempt}-", dir=package
            )
        )
        os.chmod(runtime, 0o700)
        marked = False
        stdin_path: Path | None = None
        raw_path: Path | None = None
        log_path: Path | None = None
        metadata = _attempt_metadata()
        failure_stage = "package_binding"
        try:
            stdin_path, raw_path, schema_path, log_path = (
                runtime / "prompt.stdin",
                runtime / "provider.raw",
                runtime / "response-schema.json",
                runtime / "agy.log",
            )
            prompt = compose_prompt(frozen_prompt(package, lane), lane, part)
            _atomic(stdin_path, stdin_event(prompt), raw=True)
            _atomic(schema_path, schema(lane, part["rows"]))
            _atomic(log_path, b"", raw=True)
            _mark(out, lane, packet_index, chunk_index, attempt, "started")
            marked = True
            if expected_agy_sha256 is not None and agy_executable_sha256(provider) != expected_agy_sha256:
                metadata = _attempt_metadata(raw_path, log_path, executable_binding_result="mismatch")
                failure_stage = "executable_binding"
                raise Error("structured_output_envelope_drift", structural=True)
            metadata = _attempt_metadata(raw_path, log_path, executable_binding_result=("verified" if expected_agy_sha256 else "synthetic"))
            with stdin_path.open("rb") as stdin, raw_path.open("xb") as stdout:
                os.chmod(raw_path, 0o600)
                metadata = _attempt_metadata(
                    raw_path, log_path, provider_call_started=True,
                    executable_binding_result=("verified" if expected_agy_sha256 else "synthetic"),
                )
                completed = subprocess.run(
                    _command(provider, schema_path, log_path),
                    stdin=stdin,
                    stdout=stdout,
                    stderr=subprocess.DEVNULL,
                    check=False,
                    shell=False,
                )
            metadata = _attempt_metadata(
                raw_path, log_path, provider_call_started=True,
                executable_binding_result=("verified" if expected_agy_sha256 else "synthetic"),
                provider_return_code="zero" if completed.returncode == 0 else "nonzero",
            )
            if completed.returncode:
                failure_stage = "provider_return"
                raise Error("structured_output_envelope_drift")
            raw = raw_path.read_bytes()
            try:
                labels = normalize(lane, part, _extract(raw))
            except Error as exc:
                failure_stage = "stream_parse" if exc.code in {
                    "stream_json_invalid", "terminal_result_count_drift", "structured_output_envelope_drift", "label_json_invalid"
                } else "result_validation"
                _mark(
                    out, lane, packet_index, chunk_index, attempt, "terminal", exc.code,
                    metadata=metadata, failure_stage=failure_stage,
                )
                if exc.structural and attempt == 1:
                    continue
                stop(package, lane, packet_index, exc.code, metadata=metadata, failure_stage=failure_stage)
                raise
            raw_hash = _atomic(out / f"raw-chunk-{chunk_index:02d}.raw", raw, raw=True)
            labels_hash = _atomic(labels_path, labels)
            receipt = {
                "schema_version": "phase3_cycle006_gemini_chunk_receipt_v2",
                "evaluation_cycle_id": CYCLE,
                "lane": lane,
                "packet_index": packet_index,
                "chunk_index": chunk_index,
                "chunk_count": part["chunk_count"],
                "row_count": len(part["rows"]),
                "chunk_identity_set_sha256": digest(canonical(sorted(_identity(row) for row in part["rows"]))),
                "response_raw_sha256": raw_hash,
                "labels_sha256": labels_hash,
                "attempt_count": attempt,
                "exact_model": MODEL,
                "model_family": FAMILY,
                "harness": HARNESS,
                "text_free": True,
            }
            receipt["receipt_sha256"] = digest(canonical(receipt))
            _atomic(receipt_path, receipt)
            return {"chunk_index": chunk_index, "attempt_count": attempt, "text_free": True}
        except Error as exc:
            terminal = out / f"attempt-{attempt}-chunk-{chunk_index:02d}.terminal.json"
            if marked and not terminal.exists():
                _mark(
                    out, lane, packet_index, chunk_index, attempt, "terminal", exc.code,
                    metadata=metadata, failure_stage=failure_stage,
                )
            stop(package, lane, packet_index, exc.code, metadata=metadata, failure_stage=failure_stage)
            raise
        finally:
            shutil.rmtree(runtime, ignore_errors=True)
    raise Error("structured_output_envelope_drift")


def _verify_chunk(package: Path, lane: str, packet_index: int, part: dict[str, Any]) -> dict[str, Any]:
    out = _chunk_dir(package, lane, packet_index)
    chunk_index = int(part["chunk_index"])
    labels_path, raw_path, receipt_path = (
        out / f"labels-chunk-{chunk_index:02d}.json",
        out / f"raw-chunk-{chunk_index:02d}.raw",
        out / f"receipt-chunk-{chunk_index:02d}.json",
    )
    labels, receipt = _read_json(labels_path), _read_json(receipt_path)
    _mode(raw_path, 0o600)
    try:
        SOURCE.validate(lane, {"rows": part["rows"]}, canonical(labels))
    except SOURCE.Invalid as exc:
        raise _semantic_failure(exc) from exc
    expected = {
        "schema_version": "phase3_cycle006_gemini_chunk_receipt_v2",
        "evaluation_cycle_id": CYCLE,
        "lane": lane,
        "packet_index": packet_index,
        "chunk_index": chunk_index,
        "chunk_count": part["chunk_count"],
        "row_count": len(part["rows"]),
        "chunk_identity_set_sha256": digest(canonical(sorted(_identity(row) for row in part["rows"]))),
        "response_raw_sha256": digest(raw_path.read_bytes()),
        "labels_sha256": digest(labels_path.read_bytes()),
        "attempt_count": receipt.get("attempt_count"),
        "exact_model": MODEL,
        "model_family": FAMILY,
        "harness": HARNESS,
        "text_free": True,
    }
    if (
        receipt.get("attempt_count") not in {1, 2}
        or set(receipt) != set(expected) | {"receipt_sha256"}
        or any(receipt.get(key) != value for key, value in expected.items())
        or receipt.get("receipt_sha256") != digest(canonical(expected))
    ):
        raise Error("ordinal_identity_binding_drift")
    return labels


def _reassemble(
    package: Path,
    lane: str,
    packet_index: int,
    source_path: Path,
    contents: dict[str, Any],
    parts: list[dict[str, Any]],
) -> dict[str, Any]:
    out = package / OUTPUT / lane
    labels_path, receipt_path, raw_manifest_path = (
        out / f"labels-{packet_index:04d}.json",
        out / f"receipt-{packet_index:04d}.json",
        out / f"raw-manifest-{packet_index:04d}.json",
    )
    if labels_path.exists() or receipt_path.exists() or raw_manifest_path.exists():
        if not (labels_path.exists() and receipt_path.exists() and raw_manifest_path.exists()):
            raise Error("ordinal_identity_binding_drift")
        return verify_packet(package, lane, packet_index)
    answers, entries = [], []
    for part in parts:
        labels = _verify_chunk(package, lane, packet_index, part)
        answers.extend(labels["labels"])
        receipt = _read_json(_chunk_dir(package, lane, packet_index) / f"receipt-chunk-{part['chunk_index']:02d}.json")
        entries.append(
            {
                "chunk_index": part["chunk_index"],
                "row_count": len(part["rows"]),
                "response_raw_sha256": receipt["response_raw_sha256"],
                "labels_sha256": receipt["labels_sha256"],
                "chunk_receipt_sha256": receipt["receipt_sha256"],
            }
        )
    result = {"labels": answers}
    try:
        SOURCE.validate(lane, {"rows": contents["rows"]}, canonical(result))
    except SOURCE.Invalid as exc:
        raise _semantic_failure(exc) from exc
    manifest = {
        "schema_version": "phase3_cycle006_gemini_raw_manifest_v2",
        "evaluation_cycle_id": CYCLE,
        "lane": lane,
        "packet_index": packet_index,
        "chunk_count": len(parts),
        "chunks": entries,
        "text_free": True,
    }
    manifest_hash, labels_hash = _atomic(raw_manifest_path, manifest), _atomic(labels_path, result)
    receipt = {
        "schema_version": "phase3_cycle006_packet_label_receipt_v2",
        "evaluation_cycle_id": CYCLE,
        "lane": lane,
        "packet_index": packet_index,
        "row_count": contents["row_count"],
        "packet_raw_sha256": digest(source_path.read_bytes()),
        "packet_identity_set_sha256": contents["packet_identity_set_sha256"],
        "raw_manifest_sha256": manifest_hash,
        "labels_sha256": labels_hash,
        "chunk_count": len(parts),
        "exact_model": MODEL,
        "model_family": FAMILY,
        "harness": HARNESS,
        "text_free": True,
    }
    receipt["receipt_sha256"] = digest(canonical(receipt))
    _atomic(receipt_path, receipt)
    return {"ok": True, "lane": lane, "packet_index": packet_index, "chunk_count": len(parts), "text_free": True}


def verify_packet(package: Path, lane: str, packet_index: int) -> dict[str, Any]:
    source_path, contents = packet(package, lane, packet_index)
    parts = chunks(contents)
    out = package / OUTPUT / lane
    labels_path, receipt_path, manifest_path = (
        out / f"labels-{packet_index:04d}.json",
        out / f"receipt-{packet_index:04d}.json",
        out / f"raw-manifest-{packet_index:04d}.json",
    )
    labels, receipt, manifest = _read_json(labels_path), _read_json(receipt_path), _read_json(manifest_path)
    for part in parts:
        _verify_chunk(package, lane, packet_index, part)
    try:
        SOURCE.validate(lane, {"rows": contents["rows"]}, canonical(labels))
    except SOURCE.Invalid as exc:
        raise _semantic_failure(exc) from exc
    expected_manifest = {
        "schema_version": "phase3_cycle006_gemini_raw_manifest_v2",
        "evaluation_cycle_id": CYCLE,
        "lane": lane,
        "packet_index": packet_index,
        "chunk_count": len(parts),
        "chunks": manifest.get("chunks"),
        "text_free": True,
    }
    if manifest != expected_manifest:
        raise Error("ordinal_identity_binding_drift")
    expected = {
        "schema_version": "phase3_cycle006_packet_label_receipt_v2",
        "evaluation_cycle_id": CYCLE,
        "lane": lane,
        "packet_index": packet_index,
        "row_count": contents["row_count"],
        "packet_raw_sha256": digest(source_path.read_bytes()),
        "packet_identity_set_sha256": contents["packet_identity_set_sha256"],
        "raw_manifest_sha256": digest(manifest_path.read_bytes()),
        "labels_sha256": digest(labels_path.read_bytes()),
        "chunk_count": len(parts),
        "exact_model": MODEL,
        "model_family": FAMILY,
        "harness": HARNESS,
        "text_free": True,
    }
    if (
        set(receipt) != set(expected) | {"receipt_sha256"}
        or any(receipt.get(key) != value for key, value in expected.items())
        or receipt.get("receipt_sha256") != digest(canonical(expected))
    ):
        raise Error("ordinal_identity_binding_drift")
    return {
        "ok": True,
        "lane": lane,
        "packet_index": packet_index,
        "row_count": contents["row_count"],
        "text_free": True,
    }


def run_packet(
    package: Path, lane: str, packet_index: int, provider: Path = AGY, *, expected_agy_sha256: str | None = None
) -> dict[str, Any]:
    if _real_agy_provider(provider):
        if not isinstance(expected_agy_sha256, str) or len(expected_agy_sha256) != 64:
            raise Error("ordinal_identity_binding_drift")
    elif expected_agy_sha256 is not None:
        raise Error("ordinal_identity_binding_drift")
    source_path, contents = packet(package, lane, packet_index)
    if (package / OUTPUT / "provider-stop.json").exists():
        raise Error("ordinal_identity_binding_drift")
    final_paths = [
        package / OUTPUT / lane / f"labels-{packet_index:04d}.json",
        package / OUTPUT / lane / f"receipt-{packet_index:04d}.json",
        package / OUTPUT / lane / f"raw-manifest-{packet_index:04d}.json",
    ]
    if any(path.exists() or path.is_symlink() for path in final_paths):
        if not all(path.exists() and not path.is_symlink() for path in final_paths):
            stop(package, lane, packet_index, "ordinal_identity_binding_drift", failure_stage="package_binding")
            raise Error("ordinal_identity_binding_drift")
        return verify_packet(package, lane, packet_index)
    parts = chunks(contents)
    try:
        for part in parts:
            _run_chunk(package, lane, packet_index, part, provider, expected_agy_sha256)
        _reassemble(package, lane, packet_index, source_path, contents, parts)
        return verify_packet(package, lane, packet_index)
    except Error as exc:
        stop(package, lane, packet_index, exc.code)
        raise


def batch(
    package: Path,
    lane: str,
    start: int,
    end: int,
    provider: Path = AGY,
    *,
    concurrency: int = 1,
    expected_agy_sha256: str | None = None,
) -> dict[str, Any]:
    """Resume one contiguous packet range with fail-stop concurrency fixed at one."""
    if lane not in LANES or not 1 <= start <= end <= LANES[lane] or concurrency != 1:
        raise Error("ordinal_identity_binding_drift")
    if (package / OUTPUT / "provider-stop.json").exists():
        raise Error("ordinal_identity_binding_drift")
    results: list[dict[str, Any]] = []
    for index in range(start, end + 1):
        if (package / OUTPUT / "provider-stop.json").exists():
            raise Error("ordinal_identity_binding_drift")
        results.append(run_packet(package, lane, index, provider, expected_agy_sha256=expected_agy_sha256))
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
    parser.add_argument("--package", type=Path, required=True, help="0700 operator-owned Cycle-006 package")
    parser.add_argument("--lane", choices=tuple(LANES), required=True, help="frozen packet lane")
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--packet-index", type=int, help="one-based frozen packet index")
    selector.add_argument("--start", type=int, help="inclusive contiguous batch range start")
    parser.add_argument("--end", type=int, help="inclusive contiguous batch range end (required with --start)")
    parser.add_argument("--concurrency", type=int, default=1, help="must remain one for fail-stop execution")
    parser.add_argument("--test-provider-bin", type=Path, help="synthetic provider only; omitted selects AGY")
    parser.add_argument(
        "--expected-agy-executable-sha", help="controller-bound AGY executable SHA256; required for real provider calls"
    )
    parser.add_argument("--expected-custody-sha", required=True, help="controller-bound custody receipt SHA256")
    parser.add_argument("--expected-label-manifest-sha", required=True, help="controller-bound label manifest SHA256")
    args = parser.parse_args()
    try:
        if args.test_provider_bin is None:
            if (
                not isinstance(args.expected_agy_executable_sha, str)
                or len(args.expected_agy_executable_sha) != 64
                or any(character not in "0123456789abcdef" for character in args.expected_agy_executable_sha)
            ):
                raise Error("ordinal_identity_binding_drift")
        elif args.expected_agy_executable_sha is not None:
            raise Error("ordinal_identity_binding_drift")
        if (
            len(args.expected_custody_sha) != 64
            or len(args.expected_label_manifest_sha) != 64
            or any(character not in "0123456789abcdef" for character in args.expected_custody_sha)
            or any(character not in "0123456789abcdef" for character in args.expected_label_manifest_sha)
        ):
            raise Error("ordinal_identity_binding_drift")
        global EXPECTED_CUSTODY_SHA256, EXPECTED_LABEL_MANIFEST_SHA256
        EXPECTED_CUSTODY_SHA256 = args.expected_custody_sha
        EXPECTED_LABEL_MANIFEST_SHA256 = args.expected_label_manifest_sha
        if args.packet_index is not None:
            if args.end is not None:
                raise Error("ordinal_identity_binding_drift")
            result = run_packet(
                args.package.resolve(),
                args.lane,
                args.packet_index,
                args.test_provider_bin or AGY,
                expected_agy_sha256=args.expected_agy_executable_sha,
            )
        elif args.start is not None and args.end is not None:
            result = batch(
                args.package.resolve(),
                args.lane,
                args.start,
                args.end,
                args.test_provider_bin or AGY,
                concurrency=args.concurrency,
                expected_agy_sha256=args.expected_agy_executable_sha,
            )
        else:
            raise Error("ordinal_identity_binding_drift")
    except Error as exc:
        result = {"ok": False, "failure_code": exc.code, "text_free": True}
    except Exception:
        result = {"ok": False, "failure_code": "ordinal_identity_binding_drift", "text_free": True}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
