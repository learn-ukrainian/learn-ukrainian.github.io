#!/usr/bin/env python3
"""Run one private Cycle-007 Gemini packet through the identity-bound transport.

The runner is deliberately packet-scoped. It accepts an operator-owned package,
never discovers one, and emits only text-free receipts on stdout. Private prompt
material is supplied to AGY through a 0600 stdin file; it is never an argument.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projects.open_model_data import phase3_cycle007_evidence_compiler as compiler
from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract
from scripts.projects.open_model_data import phase3_cycle007_evidence_validator as validator

HERE = Path(__file__).resolve().parent
CYCLE = "phase3-v2-1-evaluation-cycle-007"
AMENDMENT_SHA256 = "4f2e3e58964cae391c3933ffdce531296a0744808b0154231ca513049602fea0"
SOURCE_CUSTODY_SHA256 = "7047e8459433376f3b690cfc2f15e115d77a701e79afb0ef2db184b44ea14726"
SOURCE_MANIFEST_SHA256 = "b8d290ffe945a6cc5d36345cbf234ccf79a7df98cb4199ffad0b778cd2b69fab"
ORDERED_IDENTITY_COMMITMENT_SHA256 = "331fd7fbc42e43cb3c218d9c2b790df060c0a553ab7c3a7b3b557f9f2bc3c419"

EXPECTED_CUSTODY_SHA256 = ""
EXPECTED_LABEL_MANIFEST_SHA256 = ""
EXPECTED_EVIDENCE_MANIFEST_SHA256 = ""
EXPECTED_SOURCES_ENDPOINT_IDENTITY: dict[str, Any] = {}

# The installed Cycle007 evidence was compiled and certified against this
# exact compiler identity.  Runtime-only edits to the current compiler module
# (for example, occupancy instrumentation) must not silently redefine the
# identity expected by an already-frozen evidence manifest.  The manifest's
# raw SHA-256 remains independently bound by the controller preflight, and the
# validator still compares every field below exactly.
FROZEN_EVIDENCE_TOKENIZER_ID = "phase3-cycle007-cyrillic-tokenizer-v1"
FROZEN_EVIDENCE_TOKENIZER_VERSION = "1"
FROZEN_EVIDENCE_COMPILER_SHA256 = "8c66529479976f71ce5f28b82765a5916cc06c9dee737d7ce20bd89aa27cc522"
FROZEN_EVIDENCE_CODE_HASHES = {
    "compiler_id": "phase3-cycle007-evidence-compiler-v2",
    "compiler_sha256": FROZEN_EVIDENCE_COMPILER_SHA256,
    "tokenizer_id": FROZEN_EVIDENCE_TOKENIZER_ID,
    "tokenizer_version": FROZEN_EVIDENCE_TOKENIZER_VERSION,
    "tokenizer_sha256": FROZEN_EVIDENCE_COMPILER_SHA256,
    "compound_parser_id": "phase3-cycle007-compound-splitter-v1",
    "compound_parser_version": "2",
    "compound_parser_sha256": FROZEN_EVIDENCE_COMPILER_SHA256,
    "mcp_response_parser_id": "phase3-cycle007-mcp-response-parser-v1",
    "mcp_response_parser_version": "1",
    "mcp_response_parser_sha256": FROZEN_EVIDENCE_COMPILER_SHA256,
    "query_plan_id": "phase3-cycle007-query-plan-v1",
    "query_plan_version": "1",
    "query_plan_sha256": FROZEN_EVIDENCE_COMPILER_SHA256,
}

MODEL = "Gemini 3.6 Flash (High)"
FAMILY = "google"
HARNESS = "agy"
AGY_PRINT_TIMEOUT = "120m"
TIMEOUT_FIX_RECOVERY_SCHEMA = "phase3_cycle007_gemini_timeout_fix_recovery_v1"
OUTPUT = "label-output-gemini-cycle007-v1"
MAX_PACKET_ROWS = 50
DEFAULT_REQUEST_BYTE_BUDGET = 640 * 1024
REQUEST_BYTE_BUDGET_STEPS = (512 * 1024, 640 * 1024, 1024 * 1024, 2 * 1024 * 1024, 4 * 1024 * 1024)
PLANNER_VERSION = "phase3-cycle007-gemini-byte-greedy-v1"
LANES = {"clean_label": 40, "residual_label": 164}
PROMPTS = {
    "clean_label": "prompts/gemini-clean-label.md",
    "residual_label": "prompts/gemini-residual-label.md",
}
SOURCE_VALIDATOR = HERE / "phase3-cycle007-label-validation-v1.py"

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
        "provider_status_quota_or_rate_limit",
        "provider_status_capacity_unavailable",
        "provider_status_structured_request_rejected",
        "provider_status_authentication_or_permission",
        "provider_status_timeout",
        "provider_status_cancelled",
        "provider_status_internal_error",
        "provider_status_unknown",
        "request_byte_budget_exceeded",
        "request_plan_binding_drift",
        "same_size_timeout_retry_forbidden",
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
PROVIDER_STATUS_FAILURE_CODES = frozenset(
    {
        "provider_status_quota_or_rate_limit",
        "provider_status_capacity_unavailable",
        "provider_status_structured_request_rejected",
        "provider_status_authentication_or_permission",
        "provider_status_timeout",
        "provider_status_cancelled",
        "provider_status_internal_error",
        "provider_status_unknown",
    }
)
PROVIDER_STATUS_RECOVERY_CODES = frozenset(
    {
        "provider_status_quota_or_rate_limit",
        "provider_status_capacity_unavailable",
        "provider_status_timeout",
        "provider_status_cancelled",
        "provider_status_internal_error",
    }
)
RECOVERY_RECEIPT = "provider-recovery.json"
SECOND_RECOVERY_RECEIPT = "provider-recovery-attempt-3.json"
ATTEMPT_MARKER_RE = re.compile(
    r"^attempt-(?P<attempt>[1-9][0-9]*)-chunk-(?P<chunk>[0-9]+)\.(?P<state>started|terminal)\.json$"
)

_AGY_PROVIDER_STATUS_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "provider_status_quota_or_rate_limit",
        (
            "quota",
            "rate limit",
            "rate-limit",
            "rate_limit",
            "too many requests",
            "too_many_requests",
            "resource exhausted",
            "resource_exhausted",
            "429",
        ),
    ),
    (
        "provider_status_capacity_unavailable",
        (
            "capacity",
            "overload",
            "overloaded",
            "service unavailable",
            "service_unavailable",
            "temporarily unavailable",
            "temporarily_unavailable",
            "unavailable",
            "503",
        ),
    ),
    (
        "provider_status_structured_request_rejected",
        (
            "structured output",
            "structured_output",
            "json schema",
            "json_schema",
            "schema",
            "invalid request",
            "invalid_request",
            "bad request",
            "bad_request",
            "request rejected",
            "request_rejected",
            "validation",
        ),
    ),
    (
        "provider_status_authentication_or_permission",
        (
            "authentication",
            "unauthenticated",
            "unauthorized",
            "unauthorised",
            "auth error",
            "auth_error",
            "permission denied",
            "permission_denied",
            "forbidden",
            "access denied",
            "access_denied",
            "401",
            "403",
        ),
    ),
    (
        "provider_status_timeout",
        ("timeout", "timed out", "deadline exceeded", "deadline_exceeded"),
    ),
    (
        "provider_status_cancelled",
        ("cancelled", "canceled", "cancelled_by", "canceled_by", "aborted", "interrupted"),
    ),
    (
        "provider_status_internal_error",
        ("internal error", "internal_error", "server error", "server_error", "500"),
    ),
)


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


def _label_prompt_hash(value: str | None) -> str:
    """Require the separately reviewed, lane-specific labeling prompt digest.

    A public canary prompt only proves a two-row liveness challenge.  It is not
    the private 10,159-row labeling instruction and must never become a
    fallback binding for this runner.  Callers therefore supply the exact
    labeling prompt digest for the lane they are executing on every entry
    point; an absent or malformed value is a package-binding failure before
    any provider executable is started.
    """
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise Error("ordinal_identity_binding_drift")
    return value


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


def _get_expected_identity() -> dict[str, Any]:
    server_code_sha = EXPECTED_SOURCES_ENDPOINT_IDENTITY.get("server_code_sha256")
    sources_db_sha = EXPECTED_SOURCES_ENDPOINT_IDENTITY.get("sources_db_sha256")
    vesum_db_sha = EXPECTED_SOURCES_ENDPOINT_IDENTITY.get("vesum_db_sha256")
    if not server_code_sha and compiler.DEFAULT_SERVER_CODE.is_file():
        server_code_sha = contract.sha256_file(compiler.DEFAULT_SERVER_CODE)
    if not sources_db_sha and compiler.DEFAULT_SOURCES_DB.is_file():
        sources_db_sha = contract.sha256_file(compiler.DEFAULT_SOURCES_DB)
    if not vesum_db_sha and compiler.DEFAULT_VESUM_DB.is_file():
        vesum_db_sha = contract.sha256_file(compiler.DEFAULT_VESUM_DB)
    return {
        "tokenizer_id": FROZEN_EVIDENCE_TOKENIZER_ID,
        "tokenizer_version": FROZEN_EVIDENCE_TOKENIZER_VERSION,
        "code_hashes": dict(FROZEN_EVIDENCE_CODE_HASHES),
        "server_code_sha256": server_code_sha or "",
        "sources_db_sha256": sources_db_sha or "",
        "vesum_db_sha256": vesum_db_sha or "",
    }


def _verify_source_package_binding(
    evidence_manifest: dict[str, Any], custody_bytes: bytes, manifest_bytes: bytes, manifest: dict[str, Any]
) -> None:
    """A provider may run only against the current, receipt-bound package."""
    binding = evidence_manifest.get("source_package_binding")
    expected = {
        "source_evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-005",
        "custody_receipt_raw_sha256": digest(custody_bytes),
        "materialization_manifest_sha256": manifest.get("receipt_sha256"),
        "ordered_identity_commitment_sha256": manifest.get("ordered_identity_commitment_sha256"),
        "identity_union_commitment_sha256": manifest.get("identity_union_commitment_sha256"),
        "ordered_packet_commitment_sha256": manifest.get("ordered_packet_commitment_sha256"),
        "packet_count": manifest.get("packet_count"),
        "row_count": manifest.get("row_count"),
    }
    if (
        not isinstance(binding, dict)
        or not isinstance(manifest.get("receipt_sha256"), str)
        or manifest.get("receipt_sha256")
        != digest(canonical({key: value for key, value in manifest.items() if key != "receipt_sha256"}))
        or digest(manifest_bytes) == binding.get("materialization_manifest_sha256")
        or binding != expected
    ):
        raise Error("evidence_manifest_binding_drift")


def packet(package: Path, lane: str, index: int) -> tuple[Path, dict[str, Any], Path, dict[str, Any]]:
    if lane not in LANES or not 1 <= index <= LANES[lane]:
        raise Error("ordinal_identity_binding_drift")
    _private_dir(package)
    custody = package / "custody-receipt.json"
    _mode(custody, 0o600)
    custody_bytes = custody.read_bytes()
    if not EXPECTED_CUSTODY_SHA256 or digest(custody_bytes) != EXPECTED_CUSTODY_SHA256:
        raise Error("ordinal_identity_binding_drift")
    custody_val = _read_json(custody)
    if (
        custody_val.get("schema_version") != "phase3_cycle007_custody_receipt_v1"
        or custody_val.get("evaluation_cycle_id") != CYCLE
        or custody_val.get("source_evaluation_cycle_id") != "phase3-v2-1-evaluation-cycle-005"
        or custody_val.get("source_custody_receipt_raw_sha256") != SOURCE_CUSTODY_SHA256
        or custody_val.get("source_label_manifest_raw_sha256") != SOURCE_MANIFEST_SHA256
        or custody_val.get("ordered_identity_commitment_sha256") != ORDERED_IDENTITY_COMMITMENT_SHA256
        or custody_val.get("text_free") is not True
    ):
        raise Error("ordinal_identity_binding_drift")

    path = package / lane / f"packet-{index:04d}.json"
    _mode(path, 0o600)
    packet_bytes = path.read_bytes()
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
    if (
        set(value) != expected_keys
        or value.get("schema_version")
        not in {"phase3_cycle007_evidence_packet_v1", "phase3_cycle007_private_packet_v1"}
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

    manifest_path = package / "manifest.json"
    if not manifest_path.exists():
        manifest_path = package / "label-manifest.json"
    _mode(manifest_path, 0o600)
    manifest_bytes = manifest_path.read_bytes()
    if not EXPECTED_LABEL_MANIFEST_SHA256 or digest(manifest_bytes) != EXPECTED_LABEL_MANIFEST_SHA256:
        raise Error("ordinal_identity_binding_drift")
    manifest = _read_json(manifest_path)
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
        "raw_sha256": digest(packet_bytes),
        "packet_identity_set_sha256": value["packet_identity_set_sha256"],
    }
    if (
        manifest.get("schema_version")
        not in {"phase3_cycle007_materialization_manifest_v1", "phase3_cycle007_label_manifest_v2"}
        or manifest.get("evaluation_cycle_id") != CYCLE
        or manifest.get("custody_receipt_raw_sha256") != digest(custody_bytes)
        or entries != [expected_entry]
    ):
        raise Error("ordinal_identity_binding_drift")

    evidence_manifest_path = package / "evidence" / "manifest.json"
    _mode(evidence_manifest_path, 0o600)
    ev_bytes = evidence_manifest_path.read_bytes()
    if not EXPECTED_EVIDENCE_MANIFEST_SHA256 or digest(ev_bytes) != EXPECTED_EVIDENCE_MANIFEST_SHA256:
        raise Error("evidence_manifest_binding_drift")
    ev_manifest = _read_json(evidence_manifest_path)
    if (
        ev_manifest.get("schema_version") != "phase3_cycle007_evidence_manifest_v1"
        or ev_manifest.get("evaluation_cycle_id") != CYCLE
        or ev_manifest.get("text_free") is not True
    ):
        raise Error("evidence_manifest_binding_drift")

    body_ev = {k: v for k, v in ev_manifest.items() if k != "manifest_sha256"}
    if ev_manifest.get("manifest_sha256") != contract.sha256_value(body_ev):
        raise Error("evidence_manifest_binding_drift")

    _verify_source_package_binding(ev_manifest, custody_bytes, manifest_bytes, manifest)

    expected_identity = _get_expected_identity()
    try:
        validator.validate_manifest(ev_manifest, expected_identity=expected_identity)
    except validator.EvidenceValidationError as exc:
        raise Error("evidence_manifest_binding_drift") from exc

    sidecar_entries = ev_manifest.get("sidecars")
    if not isinstance(sidecar_entries, list) or not sidecar_entries:
        raise Error("evidence_manifest_binding_drift")

    manifest_packets = manifest.get("packets", [])
    if manifest_packets:
        if len(sidecar_entries) != len(manifest_packets):
            raise Error("evidence_manifest_binding_drift")
        for expected_p, sidecar_e in zip(manifest_packets, sidecar_entries, strict=True):
            if not isinstance(sidecar_e, dict):
                raise Error("evidence_manifest_binding_drift")
            if (
                sidecar_e.get("lane") != expected_p.get("lane")
                or sidecar_e.get("row_count") != expected_p.get("row_count")
                or sidecar_e.get("packet_binding", {}).get("canonical_basename") != expected_p.get("canonical_basename")
                or sidecar_e.get("packet_binding", {}).get("raw_sha256") != expected_p.get("raw_sha256")
                or sidecar_e.get("packet_binding", {}).get("packet_identity_set_sha256")
                != expected_p.get("packet_identity_set_sha256")
            ):
                raise Error("evidence_manifest_binding_drift")

    matching_entries = [
        item
        for item in sidecar_entries
        if isinstance(item, dict)
        and item.get("lane") == lane
        and item.get("packet_binding", {}).get("canonical_basename") == path.name
        and item.get("packet_binding", {}).get("raw_sha256") == digest(packet_bytes)
        and item.get("packet_binding", {}).get("packet_identity_set_sha256") == value["packet_identity_set_sha256"]
    ]
    if len(matching_entries) != 1:
        raise Error("sidecar_binding_drift")

    entry = matching_entries[0]
    global_packet_index = entry.get("packet_index")
    if not isinstance(global_packet_index, int) or global_packet_index < 1:
        raise Error("sidecar_binding_drift")

    sidecar_path = package / "evidence" / f"sidecar-{global_packet_index:04d}.json"
    _mode(sidecar_path, 0o600)
    sidecar_bytes = sidecar_path.read_bytes()
    if digest(sidecar_bytes) != entry.get("sidecar_sha256"):
        raise Error("sidecar_binding_drift")

    sidecar_val = _read_json(sidecar_path)
    if (
        sidecar_val.get("schema_version") != "phase3_cycle007_evidence_sidecar_v1"
        or sidecar_val.get("evaluation_cycle_id") != CYCLE
        or sidecar_val.get("lane") != lane
        or sidecar_val.get("packet_index") != global_packet_index
        or sidecar_val.get("row_count") != count
        or sidecar_val.get("sidecar_id") != entry.get("sidecar_id")
        or sidecar_val.get("packet_binding") != entry.get("packet_binding")
        or not isinstance(sidecar_val.get("rows"), list)
        or len(sidecar_val["rows"]) != count
    ):
        raise Error("sidecar_binding_drift")

    try:
        validator.validate_sidecar(sidecar_val, expected_identity=expected_identity)
    except validator.EvidenceValidationError as exc:
        raise Error("sidecar_binding_drift") from exc

    sidecar_ids = [_identity(row) for row in sidecar_val["rows"] if isinstance(row, dict)]
    if sidecar_ids != identities:
        raise Error("sidecar_binding_drift")

    return path, value, sidecar_path, sidecar_val


def prompt_binding(package: Path, lane: str, *, expected_label_prompt_sha: str | None) -> tuple[bytes, str]:
    """Read and bind the immutable private labeling prompt for this lane."""
    expected_hash = _label_prompt_hash(expected_label_prompt_sha)
    prompt_path = package / PROMPTS[lane]
    _mode(prompt_path, 0o600)
    prompt_raw = prompt_path.read_bytes()
    prompt_sha256 = digest(prompt_raw)
    if prompt_sha256 != expected_hash:
        raise Error("ordinal_identity_binding_drift")
    return prompt_raw, prompt_sha256


def compose_prompt(template: bytes, lane: str, part: dict[str, Any], sidecar_part: dict[str, Any]) -> str:
    """Retain the prompt instructions and append the immutable packet and sidecar JSON."""
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
    sidecar_value = {
        "evaluation_cycle_id": CYCLE,
        "lane": lane,
        "chunk_index": sidecar_part["chunk_index"],
        "chunk_count": sidecar_part["chunk_count"],
        "rows": sidecar_part["rows"],
    }
    return (
        base
        + "\n--- BEGIN IMMUTABLE PRIVATE PACKET JSON ---\n"
        + canonical(packet_value).decode("utf-8")
        + "--- END IMMUTABLE PRIVATE PACKET JSON ---\n"
        + "\n--- BEGIN IMMUTABLE EVIDENCE SIDECAR JSON ---\n"
        + canonical(sidecar_value).decode("utf-8")
        + "--- END IMMUTABLE EVIDENCE SIDECAR JSON ---\n"
    )


def _request_byte_count(
    template: bytes,
    lane: str,
    rows: list[dict[str, Any]],
    sidecar_rows: list[dict[str, Any]],
    *,
    chunk_index: int,
    chunk_count: int,
) -> int:
    if not rows or len(rows) != len(sidecar_rows):
        raise Error("request_plan_binding_drift")
    part = {"chunk_index": chunk_index, "chunk_count": chunk_count, "rows": rows}
    sidecar_part = {"chunk_index": chunk_index, "chunk_count": chunk_count, "rows": sidecar_rows}
    return len(stdin_event(compose_prompt(template, lane, part, sidecar_part)))


def chunks(
    contents: dict[str, Any],
    sidecar_contents: dict[str, Any],
    *,
    template: bytes,
    lane: str,
    request_byte_budget: int,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Greedily pack frozen-order rows under an exact serialized-byte ceiling."""
    if (
        lane not in LANES
        or not isinstance(request_byte_budget, int)
        or isinstance(request_byte_budget, bool)
        or request_byte_budget not in REQUEST_BYTE_BUDGET_STEPS
    ):
        raise Error("request_plan_binding_drift")
    rows = contents.get("rows")
    sidecar_rows = sidecar_contents.get("rows")
    if (
        not isinstance(rows, list)
        or not isinstance(sidecar_rows, list)
        or not rows
        or len(rows) != len(sidecar_rows)
        or len(rows) > MAX_PACKET_ROWS
    ):
        raise Error("request_plan_binding_drift")

    # Four decimal digits are a conservative bound for every Cycle007 packet
    # chunk index/count.  The persisted exact count is always no larger than
    # this planning measurement, so the final stdin cannot cross the budget.
    planned: list[tuple[int, int]] = []
    start = 0
    for end in range(1, len(rows) + 1):
        candidate_bytes = _request_byte_count(
            template,
            lane,
            rows[start:end],
            sidecar_rows[start:end],
            chunk_index=9999,
            chunk_count=9999,
        )
        if candidate_bytes <= request_byte_budget:
            continue
        if end - start == 1:
            raise Error("request_byte_budget_exceeded")
        planned.append((start, end - 1))
        start = end - 1
        single_bytes = _request_byte_count(
            template,
            lane,
            rows[start:end],
            sidecar_rows[start:end],
            chunk_index=9999,
            chunk_count=9999,
        )
        if single_bytes > request_byte_budget:
            raise Error("request_byte_budget_exceeded")
    planned.append((start, len(rows)))

    total = len(planned)
    result: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for offset, (row_start, row_end) in enumerate(planned, 1):
        selected_rows = rows[row_start:row_end]
        selected_sidecar_rows = sidecar_rows[row_start:row_end]
        request_bytes = _request_byte_count(
            template,
            lane,
            selected_rows,
            selected_sidecar_rows,
            chunk_index=offset,
            chunk_count=total,
        )
        if request_bytes > request_byte_budget:
            raise Error("request_byte_budget_exceeded")
        identity_sha256 = digest(canonical([_identity(row) for row in selected_rows]))
        common = {
            "chunk_index": offset,
            "chunk_count": total,
            "row_start": row_start + 1,
            "row_end": row_end,
            "request_byte_count": request_bytes,
            "ordered_identity_sha256": identity_sha256,
        }
        result.append(
            (
                common | {"rows": selected_rows},
                common | {"rows": selected_sidecar_rows},
            )
        )
    return result


def request_plan(
    contents: dict[str, Any],
    parts: list[tuple[dict[str, Any], dict[str, Any]]],
    *,
    lane: str,
    packet_index: int,
    request_byte_budget: int,
    label_prompt_sha256: str,
) -> dict[str, Any]:
    body = {
        "schema_version": "phase3_cycle007_gemini_request_plan_v1",
        "evaluation_cycle_id": CYCLE,
        "lane": lane,
        "packet_index": packet_index,
        "planner_version": PLANNER_VERSION,
        "request_byte_budget": request_byte_budget,
        "row_count": len(contents["rows"]),
        "packet_identity_set_sha256": contents["packet_identity_set_sha256"],
        "label_prompt_sha256": _label_prompt_hash(label_prompt_sha256),
        "chunks": [
            {
                "chunk_index": part["chunk_index"],
                "row_start": part["row_start"],
                "row_end": part["row_end"],
                "row_count": len(part["rows"]),
                "request_byte_count": part["request_byte_count"],
                "estimated_input_tokens_ceiling": (part["request_byte_count"] * 2 + 4) // 5,
                "ordered_identity_sha256": part["ordered_identity_sha256"],
            }
            for part, _sidecar_part in parts
        ],
        "text_free": True,
    }
    return body | {"plan_sha256": digest(canonical(body))}


def schema(lane: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    if lane not in LANES or not 1 <= len(rows) <= MAX_PACKET_ROWS:
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
                    "evidence_ids",
                ],
                "properties": identity
                | {
                    "decision_code": {"enum": sorted(SOURCE.REJECTS)},
                    "clean_modern_standard_prose": {"type": "boolean"},
                    "modern_genre_id": {"anyOf": [{"enum": sorted(SOURCE.GENRES)}, {"type": "null"}]},
                    "evidence_ids": {"type": "array", "items": {"type": "string"}},
                },
            }
        phenomenon = {
            "type": "object",
            "additionalProperties": False,
            "required": ["phenomenon_id", "decision_code", "evidence_sufficiency", "evidence_ids"],
            "properties": {
                "phenomenon_id": {"enum": list(SOURCE.TAX)},
                "decision_code": {"enum": sorted(SOURCE.DEC)},
                "evidence_sufficiency": {"enum": ["sufficient", "insufficient"]},
                "evidence_ids": {"type": "array", "items": {"type": "string"}},
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


def _agy_static_failure_code(result: Mapping[str, Any]) -> str:
    """Reduce untrusted AGY diagnostics to one closed, text-free status code."""

    def matches(value: Any, patterns: tuple[str, ...], *, depth: int = 0) -> bool:
        if isinstance(value, str):
            lowered = value.lower()
            return any(pattern in lowered for pattern in patterns)
        if not isinstance(value, Mapping) or depth >= 2:
            return False
        keys = ("status", "code", "error_code", "error_type", "reason", "message", "response", "error")
        return any(matches(value.get(key), patterns, depth=depth + 1) for key in keys)

    try:
        for code, patterns in _AGY_PROVIDER_STATUS_PATTERNS:
            if matches(result, patterns):
                return code
    except Exception:
        pass
    return "provider_status_unknown"


def _agy_stream(raw: bytes, *, expected_cwd: Path | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
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
    if expected_cwd is not None:
        reported_cwd = config.get("cwd")
        try:
            if not isinstance(reported_cwd, str) or not Path(reported_cwd).is_absolute() or not Path(
                reported_cwd
            ).samefile(expected_cwd):
                raise Error("structured_output_envelope_drift", structural=True)
        except OSError as exc:
            raise Error("structured_output_envelope_drift", structural=True) from exc
    if not isinstance(result, dict):
        raise Error("structured_output_envelope_drift", structural=True)
    if result.get("status") != "SUCCESS":
        raise Error(_agy_static_failure_code(result), structural=False)
    if "structured_output" not in result and "response" not in result:
        raise Error("structured_output_envelope_drift", structural=True)
    return init, result


def _strict_result_payload(result: Mapping[str, Any]) -> dict[str, Any]:
    """Decode exactly one label object from AGY's schema or response field."""
    if "structured_output" in result:
        output = result["structured_output"]
        if isinstance(output, str):
            try:
                output = json.loads(output, object_pairs_hook=_pairs)
            except (json.JSONDecodeError, Error) as exc:
                raise Error("label_json_invalid", structural=True) from exc
        if not isinstance(output, dict):
            raise Error("structured_output_envelope_drift", structural=True)
        return output

    candidates: list[dict[str, Any]] = []

    def inspect(value: Any, *, depth: int = 0) -> None:
        if depth > 4:
            return
        if isinstance(value, str):
            text = value.strip()
            fence = "`" * 3
            if text.startswith(fence) and text.endswith(fence):
                text = text[len(fence) : -len(fence)].strip()
                if text.startswith("json"):
                    text = text[4:].lstrip()
            try:
                decoded = json.loads(text, object_pairs_hook=_pairs)
            except (json.JSONDecodeError, Error):
                return
            if isinstance(decoded, dict) and "labels_by_position" in decoded:
                candidates.append(decoded)
            return
        if isinstance(value, list):
            for item in value:
                inspect(item, depth=depth + 1)
            return
        if isinstance(value, dict):
            if "labels_by_position" in value:
                candidates.append(value)
                return
            for key in ("content", "message", "parts", "response", "text"):
                if key in value:
                    inspect(value[key], depth=depth + 1)

    inspect(result.get("response"))
    if len(candidates) != 1:
        raise Error("structured_output_envelope_drift", structural=True)
    return candidates[0]


def _extract(raw: bytes, *, expected_cwd: Path | None = None) -> dict[str, Any]:
    _, result = _agy_stream(raw, expected_cwd=expected_cwd)
    return _strict_result_payload(result)


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
        "evidence id order/unique drift": "evidence_id_order_drift",
        "cross_row_evidence": "cross_row_evidence",
        "cross_phenomenon_evidence": "cross_phenomenon_evidence",
        "insufficient_evidence_for_decision": "insufficient_evidence_for_decision",
        "evidence_id_order_drift": "evidence_id_order_drift",
        "evidence_id_hash_drift": "evidence_id_hash_drift",
        "query_sha256_hash_drift": "query_sha256_hash_drift",
        "sidecar row count drift": "sidecar_binding_drift",
        "source_role_boundary_violation": "source_role_boundary_violation",
        "evidence_shape_drift": "evidence_shape_drift",
        "unknown_decision_code": "unknown_decision_code",
    }
    return Error(mapping.get(text, "ordinal_identity_binding_drift"), structural=False)


def normalize(
    lane: str, part: dict[str, Any], structured: dict[str, Any], sidecar_part: dict[str, Any] | None = None
) -> dict[str, Any]:
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
        sidecar_arg = {"rows": sidecar_part["rows"]} if sidecar_part is not None else None
        SOURCE.validate(lane, {"rows": part["rows"]}, canonical(result), sidecar=sidecar_arg)
    except SOURCE.Invalid as exc:
        raise _semantic_failure(exc) from exc
    return result


def _stream_metadata(raw: bytes | None) -> dict[str, Any]:
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
        events = [
            json.loads(line, object_pairs_hook=_pairs)
            for line in raw.decode("utf-8", "strict").splitlines()
            if line.strip()
        ]
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
            "missing"
            if "structured_output" not in body
            else "object"
            if isinstance(output, dict)
            else "string"
            if isinstance(output, str)
            else "null"
            if output is None
            else "other"
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
            "executable_binding_result": executable_binding_result
            if executable_binding_result in EXECUTABLE_BINDINGS
            else "unavailable",
            "provider_return_code": provider_return_code if provider_return_code in RETURN_CODES else "nonzero",
            "log_byte_count": 0 if log is None else len(log),
            "log_sha256": digest(b"" if log is None else log),
        }
    )
    return result


def _mark(
    out: Path,
    lane: str,
    packet_index: int,
    chunk_index: int,
    attempt: int,
    state: str,
    code: str | None = None,
    *,
    metadata: dict[str, Any] | None = None,
    failure_stage: str | None = None,
    request_plan_sha256: str | None = None,
    request_byte_budget: int | None = None,
    request_byte_count: int | None = None,
) -> None:
    value: dict[str, Any] = {
        "schema_version": "phase3_cycle007_gemini_attempt_v1",
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
    request_binding = (request_plan_sha256, request_byte_budget, request_byte_count)
    if any(value is not None for value in request_binding):
        if (
            not isinstance(request_plan_sha256, str)
            or len(request_plan_sha256) != 64
            or not isinstance(request_byte_budget, int)
            or isinstance(request_byte_budget, bool)
            or request_byte_budget not in REQUEST_BYTE_BUDGET_STEPS
            or not isinstance(request_byte_count, int)
            or isinstance(request_byte_count, bool)
            or not 0 < request_byte_count <= request_byte_budget
        ):
            raise Error("request_plan_binding_drift")
        value |= {
            "schema_version": "phase3_cycle007_gemini_attempt_v2",
            "request_plan_sha256": request_plan_sha256,
            "request_byte_budget": request_byte_budget,
            "request_byte_count": request_byte_count,
        }
    if state == "terminal":
        value["failure_code"] = code if code in FAILURE_CODES else "ordinal_identity_binding_drift"
        value["failure_stage"] = failure_stage if failure_stage in ATTEMPT_FAILURE_STAGES else "package_binding"
        value.update(metadata or _attempt_metadata())
    _atomic(out / f"attempt-{attempt}-chunk-{chunk_index:02d}.{state}.json", value)


def stop(
    package: Path,
    lane: str,
    packet_index: int,
    code: str,
    *,
    metadata: dict[str, Any] | None = None,
    failure_stage: str | None = None,
    chunk_index: int | None = None,
    attempt: int | None = None,
    terminal_marker_sha256: str | None = None,
) -> None:
    """Atomically write the first stop; any existing stop is already authoritative."""
    path = package / OUTPUT / "provider-stop.json"
    occurrence = (chunk_index, attempt, terminal_marker_sha256)
    occurrence_bound = all(value is not None for value in occurrence)
    if any(value is not None for value in occurrence) and not occurrence_bound:
        raise Error("ordinal_identity_binding_drift")
    if occurrence_bound and (
        not isinstance(chunk_index, int)
        or isinstance(chunk_index, bool)
        or chunk_index < 1
        or not isinstance(attempt, int)
        or isinstance(attempt, bool)
        or attempt < 1
        or not isinstance(terminal_marker_sha256, str)
        or len(terminal_marker_sha256) != 64
        or any(character not in "0123456789abcdef" for character in terminal_marker_sha256)
    ):
        raise Error("ordinal_identity_binding_drift")
    value = {
        "schema_version": (
            "phase3_cycle007_gemini_provider_stop_v3"
            if occurrence_bound and metadata is not None and "request_plan_sha256" in metadata
            else "phase3_cycle007_gemini_provider_stop_v2"
            if occurrence_bound
            else "phase3_cycle007_gemini_provider_stop_v1"
        ),
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
    if occurrence_bound:
        value |= {
            "chunk_index": chunk_index,
            "attempt": attempt,
            "terminal_marker_sha256": terminal_marker_sha256,
        }
    try:
        _mkdir_private(path.parent)
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        existing = _read_json(path)
        if (
            existing.get("schema_version")
            not in {
                "phase3_cycle007_gemini_provider_stop_v1",
                "phase3_cycle007_gemini_provider_stop_v2",
                "phase3_cycle007_gemini_provider_stop_v3",
            }
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


def _recovery_candidates(
    package: Path, out: Path, chunk_index: int, authorized_attempt: int
) -> tuple[Path, ...]:
    local = out / f"provider-recovery-chunk-{chunk_index:02d}-attempt-{authorized_attempt}.json"
    legacy: Path | None = None
    if out == package / OUTPUT / "clean_label/chunks/packet-0001" and chunk_index == 1:
        if authorized_attempt == 2:
            legacy = package / OUTPUT / RECOVERY_RECEIPT
        elif authorized_attempt == 3:
            legacy = package / OUTPUT / SECOND_RECOVERY_RECEIPT
    return (local,) if legacy is None else (legacy, local)


def _recovery_path(
    package: Path, out: Path, chunk_index: int, authorized_attempt: int
) -> Path | None:
    candidates = [
        path
        for path in _recovery_candidates(package, out, chunk_index, authorized_attempt)
        if path.exists() or path.is_symlink()
    ]
    if len(candidates) > 1:
        raise Error("ordinal_identity_binding_drift")
    return candidates[0] if candidates else None


def _verify_recovery_receipt(
    package: Path,
    out: Path,
    chunk_index: int,
    failed_attempt: int,
    *,
    prior_recovery_raw: bytes | None,
    prior_provider_call_count: int | None,
    request_byte_budget: int,
) -> tuple[bytes, dict[str, Any]]:
    """Require one exact, marker-bound operator authorization for the next call."""
    authorized_attempt = failed_attempt + 1
    path = _recovery_path(package, out, chunk_index, authorized_attempt)
    if path is None or path.is_symlink():
        raise Error("ordinal_identity_binding_drift")
    receipt = _read_json(path)
    _mode(path, 0o600)
    started = out / f"attempt-{failed_attempt}-chunk-{chunk_index:02d}.started.json"
    terminal = out / f"attempt-{failed_attempt}-chunk-{chunk_index:02d}.terminal.json"
    for marker in (started, terminal):
        _mode(marker, 0o600)
    terminal_value = _read_json(terminal)
    call_count = receipt.get("prior_provider_call_count")
    timeout_fix = receipt.get("schema_version") == TIMEOUT_FIX_RECOVERY_SCHEMA
    expected = {
        "schema_version": receipt.get("schema_version"),
        "evaluation_cycle_id": CYCLE,
        "source_provider_stop_sha256": receipt.get("source_provider_stop_sha256"),
        "started_marker_sha256": digest(started.read_bytes()),
        "terminal_marker_sha256": digest(terminal.read_bytes()),
        "failure_code": terminal_value.get("failure_code"),
        "failure_stage": terminal_value.get("failure_stage"),
        "prior_provider_call_count": call_count,
        "authorized_additional_provider_calls": 1,
        "exact_model": MODEL,
        "model_family": FAMILY,
        "harness": HARNESS,
        "text_free": True,
    }
    if timeout_fix:
        if (
            terminal_value.get("schema_version") != "phase3_cycle007_gemini_attempt_v2"
            or terminal_value.get("failure_code") != "provider_status_timeout"
            or terminal_value.get("request_byte_budget") not in REQUEST_BYTE_BUDGET_STEPS
            or terminal_value.get("request_byte_budget") != request_byte_budget
        ):
            raise Error("ordinal_identity_binding_drift")
        expected |= {
            "authorized_attempt": authorized_attempt,
            "request_byte_budget": request_byte_budget,
            "gemini_runner_sha256": digest(Path(__file__).read_bytes()),
            "agy_print_timeout": AGY_PRINT_TIMEOUT,
        }
    elif expected["schema_version"] != (
        "phase3_cycle007_gemini_provider_recovery_v1"
        if prior_recovery_raw is None
        else "phase3_cycle007_gemini_provider_second_recovery_v1"
    ):
        raise Error("ordinal_identity_binding_drift")
    if prior_recovery_raw is not None:
        expected |= {
            "prior_recovery_receipt_sha256": digest(prior_recovery_raw),
            "authorized_attempt": authorized_attempt,
        }
    stop_hash = expected["source_provider_stop_sha256"]
    if (
        not isinstance(stop_hash, str)
        or len(stop_hash) != 64
        or any(character not in "0123456789abcdef" for character in stop_hash)
        or not isinstance(call_count, int)
        or isinstance(call_count, bool)
        or call_count < 1
        or (
            prior_provider_call_count is not None
            and call_count != prior_provider_call_count + 1
        )
        or set(receipt) != set(expected) | {"receipt_sha256"}
        or any(receipt.get(key) != value for key, value in expected.items())
        or receipt.get("receipt_sha256") != digest(canonical(expected))
    ):
        raise Error("ordinal_identity_binding_drift")
    return path.read_bytes(), receipt


def _next_attempt(
    package: Path,
    out: Path,
    chunk_index: int,
    *,
    request_byte_budget: int = DEFAULT_REQUEST_BYTE_BUDGET,
) -> int:
    """Resolve the one explicitly authorized next call without a retry ceiling."""
    retryable = {
        "stream_json_invalid",
        "terminal_result_count_drift",
        "structured_output_envelope_drift",
        "ordinal_key_drift",
        "label_json_invalid",
        "label_count_or_envelope_drift",
    } | PROVIDER_STATUS_RECOVERY_CODES
    observed: dict[tuple[int, str], Path] = {}
    for path in out.iterdir():
        match = ATTEMPT_MARKER_RE.fullmatch(path.name)
        if match is None or int(match["chunk"]) != chunk_index:
            continue
        key = (int(match["attempt"]), match["state"])
        if key in observed or path.is_symlink():
            raise Error("ordinal_identity_binding_drift")
        observed[key] = path
    if not observed:
        return 1
    attempts = sorted({attempt for attempt, _state in observed})
    if attempts != list(range(1, len(attempts) + 1)):
        raise Error("ordinal_identity_binding_drift")
    maximum = len(attempts)

    prior_recovery_raw: bytes | None = None
    prior_provider_call_count: int | None = None
    for attempt in range(1, maximum + 1):
        started = out / f"attempt-{attempt}-chunk-{chunk_index:02d}.started.json"
        terminal = out / f"attempt-{attempt}-chunk-{chunk_index:02d}.terminal.json"
        if not started.exists() or started.is_symlink():
            raise Error("ordinal_identity_binding_drift")
        if not terminal.exists():
            if attempt != maximum:
                raise Error("ordinal_identity_binding_drift")
            raise Error("ordinal_identity_binding_drift")
        _mode(started, 0o600)
        _mode(terminal, 0o600)
        marker = _read_json(terminal)
        failure_code = marker.get("failure_code")
        if failure_code not in retryable:
            raise Error("ordinal_identity_binding_drift")
        same_size_timeout = False
        if failure_code == "provider_status_timeout":
            prior_budget = marker.get("request_byte_budget")
            if prior_budget is None:
                # Legacy pre-byte-plan markers remain verifiable only through
                # their exact recovery chain.  Every newly written marker is
                # budget-bound and therefore enters the fail-closed branch.
                pass
            elif prior_budget == request_byte_budget:
                same_size_timeout = True
            elif (
                not isinstance(prior_budget, int)
                or isinstance(prior_budget, bool)
                or prior_budget <= request_byte_budget
            ):
                raise Error("request_plan_binding_drift")
        recovery_path = _recovery_path(package, out, chunk_index, attempt + 1)
        if (
            attempt == 1
            and failure_code in retryable - PROVIDER_STATUS_RECOVERY_CODES
            and recovery_path is None
        ):
            continue
        if same_size_timeout and recovery_path is None:
            raise Error("same_size_timeout_retry_forbidden")
        prior_recovery_raw, receipt = _verify_recovery_receipt(
            package,
            out,
            chunk_index,
            attempt,
            prior_recovery_raw=prior_recovery_raw,
            prior_provider_call_count=prior_provider_call_count,
            request_byte_budget=request_byte_budget,
        )
        if same_size_timeout and receipt.get("schema_version") != TIMEOUT_FIX_RECOVERY_SCHEMA:
            raise Error("same_size_timeout_retry_forbidden")
        prior_provider_call_count = receipt["prior_provider_call_count"]
    return maximum + 1


def _command(provider: Path, schema_path: Path, log_path: Path) -> list[str]:
    # AGY stream-input mode reads turns only from stdin; --print would add a
    # conflicting headless prompt and can yield SUCCESS with an empty result.
    return [
        str(provider),
        "--model",
        MODEL,
        "--mode",
        "plan",
        "--new-project",
        "--sandbox",
        "--disable-slash-commands",
        "--input-format",
        "stream-json",
        "--output-format",
        "stream-json",
        "--print-timeout",
        AGY_PRINT_TIMEOUT,
        "--json-schema",
        str(schema_path),
        "--log-file",
        str(log_path),
    ]


def agy_executable_sha256(provider: Path) -> str:
    try:
        if provider.is_symlink():
            raise Error("structured_output_envelope_drift", structural=True)
        resolved = provider.resolve(strict=True)
    except OSError as exc:
        raise Error("structured_output_envelope_drift", structural=True) from exc
    if not resolved.is_file():
        raise Error("structured_output_envelope_drift", structural=True)
    return digest(resolved.read_bytes())


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


def _bind_request_plan(out: Path, plan: dict[str, Any]) -> str:
    path = out / "request-plan.json"
    expected_hash = plan.get("plan_sha256")
    if (
        not isinstance(expected_hash, str)
        or len(expected_hash) != 64
        or expected_hash != digest(canonical({key: value for key, value in plan.items() if key != "plan_sha256"}))
    ):
        raise Error("request_plan_binding_drift")
    _atomic(path, plan)
    if _read_json(path) != plan:
        raise Error("request_plan_binding_drift")
    return expected_hash


def _write_pre_call_receipt(
    out: Path,
    *,
    lane: str,
    packet_index: int,
    part: dict[str, Any],
    attempt: int,
    request_plan_sha256: str,
    request_byte_budget: int,
) -> None:
    body = {
        "schema_version": "phase3_cycle007_gemini_pre_call_v1",
        "evaluation_cycle_id": CYCLE,
        "lane": lane,
        "packet_index": packet_index,
        "chunk_index": part["chunk_index"],
        "attempt": attempt,
        "request_plan_sha256": request_plan_sha256,
        "planner_version": PLANNER_VERSION,
        "row_count": len(part["rows"]),
        "request_byte_budget": request_byte_budget,
        "request_byte_count": part["request_byte_count"],
        "estimated_input_tokens_ceiling": (part["request_byte_count"] * 2 + 4) // 5,
        "ordered_identity_sha256": part["ordered_identity_sha256"],
        "text_free": True,
    }
    body["receipt_sha256"] = digest(canonical(body))
    _atomic(out / f"pre-call-attempt-{attempt}-chunk-{part['chunk_index']:02d}.json", body)


def _verify_pre_call_receipt(
    out: Path,
    *,
    lane: str,
    packet_index: int,
    part: dict[str, Any],
    attempt: int,
    request_plan_sha256: str,
    request_byte_budget: int,
) -> None:
    path = out / f"pre-call-attempt-{attempt}-chunk-{part['chunk_index']:02d}.json"
    receipt = _read_json(path)
    expected = {
        "schema_version": "phase3_cycle007_gemini_pre_call_v1",
        "evaluation_cycle_id": CYCLE,
        "lane": lane,
        "packet_index": packet_index,
        "chunk_index": part["chunk_index"],
        "attempt": attempt,
        "request_plan_sha256": request_plan_sha256,
        "planner_version": PLANNER_VERSION,
        "row_count": len(part["rows"]),
        "request_byte_budget": request_byte_budget,
        "request_byte_count": part["request_byte_count"],
        "estimated_input_tokens_ceiling": (part["request_byte_count"] * 2 + 4) // 5,
        "ordered_identity_sha256": part["ordered_identity_sha256"],
        "text_free": True,
    }
    if (
        set(receipt) != set(expected) | {"receipt_sha256"}
        or any(receipt.get(key) != value for key, value in expected.items())
        or receipt.get("receipt_sha256") != digest(canonical(expected))
    ):
        raise Error("request_plan_binding_drift")


def _run_chunk(
    package: Path,
    lane: str,
    packet_index: int,
    part: dict[str, Any],
    sidecar_part: dict[str, Any],
    provider: Path,
    expected_agy_sha256: str | None,
    expected_label_prompt_sha: str,
    request_plan_sha256: str,
    request_byte_budget: int,
) -> dict[str, Any]:
    chunk_index = int(part["chunk_index"])
    out = _chunk_dir(package, lane, packet_index)
    labels_path = out / f"labels-chunk-{chunk_index:02d}.json"
    receipt_path = out / f"receipt-chunk-{chunk_index:02d}.json"
    if labels_path.exists() or receipt_path.exists():
        if not (labels_path.exists() and receipt_path.exists()):
            raise Error("ordinal_identity_binding_drift")
        _verify_chunk(
            package,
            lane,
            packet_index,
            part,
            sidecar_part,
            expected_label_prompt_sha=expected_label_prompt_sha,
            request_plan_sha256=request_plan_sha256,
            request_byte_budget=request_byte_budget,
        )
        return {"chunk_index": chunk_index, "resumed": True, "text_free": True}
    if (package / OUTPUT / "provider-stop.json").exists():
        raise Error("ordinal_identity_binding_drift")
    while True:
        attempt = _next_attempt(package, out, chunk_index, request_byte_budget=request_byte_budget)
        terminal = out / f"attempt-{attempt}-chunk-{chunk_index:02d}.terminal.json"
        runtime = Path(
            tempfile.mkdtemp(
                prefix=f".cycle007-gemini-{lane}-{packet_index:04d}-{chunk_index:02d}-{attempt}-", dir=package
            )
        )
        os.chmod(runtime, 0o700)
        marked = False
        stdin_path: Path | None = None
        raw_path: Path | None = None
        log_path: Path | None = None
        metadata = _attempt_metadata()
        request_metadata = {
            "request_plan_sha256": request_plan_sha256,
            "request_byte_budget": request_byte_budget,
            "request_byte_count": part["request_byte_count"],
        }
        metadata.update(request_metadata)
        failure_stage = "package_binding"
        try:
            stdin_path, raw_path, schema_path, log_path = (
                runtime / "prompt.stdin",
                runtime / "provider.raw",
                runtime / "response-schema.json",
                runtime / "agy.log",
            )
            prompt_template, prompt_sha256 = prompt_binding(
                package, lane, expected_label_prompt_sha=expected_label_prompt_sha
            )
            prompt = compose_prompt(prompt_template, lane, part, sidecar_part)
            stdin_bytes = stdin_event(prompt)
            if (
                len(stdin_bytes) != part.get("request_byte_count")
                or len(stdin_bytes) > request_byte_budget
            ):
                raise Error("request_byte_budget_exceeded")
            _atomic(stdin_path, stdin_bytes, raw=True)
            _atomic(schema_path, schema(lane, part["rows"]))
            _atomic(log_path, b"", raw=True)
            _write_pre_call_receipt(
                out,
                lane=lane,
                packet_index=packet_index,
                part=part,
                attempt=attempt,
                request_plan_sha256=request_plan_sha256,
                request_byte_budget=request_byte_budget,
            )
            _mark(
                out,
                lane,
                packet_index,
                chunk_index,
                attempt,
                "started",
                request_plan_sha256=request_plan_sha256,
                request_byte_budget=request_byte_budget,
                request_byte_count=len(stdin_bytes),
            )
            marked = True
            if expected_agy_sha256 is not None and agy_executable_sha256(provider) != expected_agy_sha256:
                metadata = _attempt_metadata(raw_path, log_path, executable_binding_result="mismatch")
                metadata.update(request_metadata)
                failure_stage = "executable_binding"
                raise Error("structured_output_envelope_drift", structural=True)
            metadata = _attempt_metadata(
                raw_path, log_path, executable_binding_result=("verified" if expected_agy_sha256 else "synthetic")
            )
            metadata.update(request_metadata)
            with stdin_path.open("rb") as stdin, raw_path.open("xb") as stdout:
                os.chmod(raw_path, 0o600)
                metadata = _attempt_metadata(
                    raw_path,
                    log_path,
                    provider_call_started=True,
                    executable_binding_result=("verified" if expected_agy_sha256 else "synthetic"),
                )
                metadata.update(request_metadata)
                provider_started_ns = time.monotonic_ns()
                completed = subprocess.run(
                    _command(provider, schema_path, log_path),
                    stdin=stdin,
                    stdout=stdout,
                    stderr=subprocess.DEVNULL,
                    check=False,
                    shell=False,
                    cwd=runtime,
                )
                elapsed_milliseconds = (time.monotonic_ns() - provider_started_ns + 999_999) // 1_000_000
            metadata = _attempt_metadata(
                raw_path,
                log_path,
                provider_call_started=True,
                executable_binding_result=("verified" if expected_agy_sha256 else "synthetic"),
                provider_return_code="zero" if completed.returncode == 0 else "nonzero",
            )
            metadata.update(request_metadata)
            metadata["elapsed_milliseconds"] = elapsed_milliseconds
            if completed.returncode:
                failure_stage = "provider_return"
                try:
                    _agy_stream(raw_path.read_bytes(), expected_cwd=runtime)
                except Error as exc:
                    if exc.code in PROVIDER_STATUS_FAILURE_CODES:
                        raise exc
                raise Error("structured_output_envelope_drift")
            raw = raw_path.read_bytes()
            try:
                labels = normalize(lane, part, _extract(raw, expected_cwd=runtime), sidecar_part=sidecar_part)
            except Error as exc:
                failure_stage = (
                    "provider_return"
                    if exc.code in PROVIDER_STATUS_FAILURE_CODES
                    else "stream_parse"
                    if exc.code in {
                        "stream_json_invalid",
                        "terminal_result_count_drift",
                        "structured_output_envelope_drift",
                        "label_json_invalid",
                    }
                    else "result_validation"
                )
                _mark(
                    out,
                    lane,
                    packet_index,
                    chunk_index,
                    attempt,
                    "terminal",
                    exc.code,
                    metadata=metadata,
                    failure_stage=failure_stage,
                    request_plan_sha256=request_plan_sha256,
                    request_byte_budget=request_byte_budget,
                    request_byte_count=len(stdin_bytes),
                )
                if exc.structural and attempt == 1:
                    continue
                stop(
                    package,
                    lane,
                    packet_index,
                    exc.code,
                    metadata=metadata,
                    failure_stage=failure_stage,
                    chunk_index=chunk_index,
                    attempt=attempt,
                    terminal_marker_sha256=digest(terminal.read_bytes()),
                )
                raise
            raw_hash = _atomic(out / f"raw-chunk-{chunk_index:02d}.raw", raw, raw=True)
            labels_hash = _atomic(labels_path, labels)
            receipt = {
                "schema_version": "phase3_cycle007_gemini_chunk_receipt_v2",
                "evaluation_cycle_id": CYCLE,
                "lane": lane,
                "packet_index": packet_index,
                "chunk_index": chunk_index,
                "chunk_count": part["chunk_count"],
                "row_count": len(part["rows"]),
                "chunk_identity_set_sha256": digest(canonical(sorted(_identity(row) for row in part["rows"]))),
                "ordered_identity_sha256": part["ordered_identity_sha256"],
                "request_plan_sha256": request_plan_sha256,
                "planner_version": PLANNER_VERSION,
                "request_byte_budget": request_byte_budget,
                "request_byte_count": len(stdin_bytes),
                "elapsed_milliseconds": elapsed_milliseconds,
                "prompt_sha256": prompt_sha256,
                "label_prompt_sha256": expected_label_prompt_sha,
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
                    out,
                    lane,
                    packet_index,
                    chunk_index,
                    attempt,
                    "terminal",
                    exc.code,
                    metadata=metadata,
                    failure_stage=failure_stage,
                    request_plan_sha256=request_plan_sha256,
                    request_byte_budget=request_byte_budget,
                    request_byte_count=part["request_byte_count"],
                )
            stop(
                package,
                lane,
                packet_index,
                exc.code,
                metadata=metadata,
                failure_stage=failure_stage,
                **(
                    {
                        "chunk_index": chunk_index,
                        "attempt": attempt,
                        "terminal_marker_sha256": digest(terminal.read_bytes()),
                    }
                    if terminal.is_file() and not terminal.is_symlink()
                    else {}
                ),
            )
            raise
        finally:
            shutil.rmtree(runtime, ignore_errors=True)


def _verify_chunk(
    package: Path,
    lane: str,
    packet_index: int,
    part: dict[str, Any],
    sidecar_part: dict[str, Any] | None = None,
    *,
    expected_label_prompt_sha: str | None,
    request_plan_sha256: str,
    request_byte_budget: int,
) -> dict[str, Any]:
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
        sidecar_arg = {"rows": sidecar_part["rows"]} if sidecar_part is not None else None
        SOURCE.validate(lane, {"rows": part["rows"]}, canonical(labels), sidecar=sidecar_arg)
    except SOURCE.Invalid as exc:
        raise _semantic_failure(exc) from exc
    _prompt_template, prompt_sha256 = prompt_binding(package, lane, expected_label_prompt_sha=expected_label_prompt_sha)
    expected = {
        "schema_version": "phase3_cycle007_gemini_chunk_receipt_v2",
        "evaluation_cycle_id": CYCLE,
        "lane": lane,
        "packet_index": packet_index,
        "chunk_index": chunk_index,
        "chunk_count": part["chunk_count"],
        "row_count": len(part["rows"]),
        "chunk_identity_set_sha256": digest(canonical(sorted(_identity(row) for row in part["rows"]))),
        "ordered_identity_sha256": part["ordered_identity_sha256"],
        "request_plan_sha256": request_plan_sha256,
        "planner_version": PLANNER_VERSION,
        "request_byte_budget": request_byte_budget,
        "request_byte_count": part["request_byte_count"],
        "elapsed_milliseconds": receipt.get("elapsed_milliseconds"),
        "prompt_sha256": prompt_sha256,
        "label_prompt_sha256": _label_prompt_hash(expected_label_prompt_sha),
        "response_raw_sha256": digest(raw_path.read_bytes()),
        "labels_sha256": digest(labels_path.read_bytes()),
        "attempt_count": receipt.get("attempt_count"),
        "exact_model": MODEL,
        "model_family": FAMILY,
        "harness": HARNESS,
        "text_free": True,
    }
    attempt_count = receipt.get("attempt_count")
    elapsed_milliseconds = receipt.get("elapsed_milliseconds")
    if (
        not isinstance(attempt_count, int)
        or isinstance(attempt_count, bool)
        or attempt_count < 1
        or not isinstance(elapsed_milliseconds, int)
        or isinstance(elapsed_milliseconds, bool)
        or elapsed_milliseconds < 0
        or set(receipt) != set(expected) | {"receipt_sha256"}
        or any(receipt.get(key) != value for key, value in expected.items())
        or receipt.get("receipt_sha256") != digest(canonical(expected))
    ):
        raise Error("ordinal_identity_binding_drift")
    _verify_pre_call_receipt(
        out,
        lane=lane,
        packet_index=packet_index,
        part=part,
        attempt=attempt_count,
        request_plan_sha256=request_plan_sha256,
        request_byte_budget=request_byte_budget,
    )
    return labels


def _reassemble(
    package: Path,
    lane: str,
    packet_index: int,
    source_path: Path,
    contents: dict[str, Any],
    sidecar_path: Path,
    sidecar_contents: dict[str, Any],
    parts: list[tuple[dict[str, Any], dict[str, Any]]],
    *,
    expected_label_prompt_sha: str,
    request_plan_sha256: str,
    request_byte_budget: int,
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
        return verify_packet(
            package,
            lane,
            packet_index,
            expected_label_prompt_sha=expected_label_prompt_sha,
            request_byte_budget=request_byte_budget,
        )
    answers, entries = [], []
    for part, sidecar_part in parts:
        labels = _verify_chunk(
            package,
            lane,
            packet_index,
            part,
            sidecar_part,
            expected_label_prompt_sha=expected_label_prompt_sha,
            request_plan_sha256=request_plan_sha256,
            request_byte_budget=request_byte_budget,
        )
        answers.extend(labels["labels"])
        receipt = _read_json(_chunk_dir(package, lane, packet_index) / f"receipt-chunk-{part['chunk_index']:02d}.json")
        entries.append(
            {
                "chunk_index": part["chunk_index"],
                "row_count": len(part["rows"]),
                "request_byte_count": receipt["request_byte_count"],
                "elapsed_milliseconds": receipt["elapsed_milliseconds"],
                "response_raw_sha256": receipt["response_raw_sha256"],
                "labels_sha256": receipt["labels_sha256"],
                "chunk_receipt_sha256": receipt["receipt_sha256"],
            }
        )
    result = {"labels": answers}
    try:
        SOURCE.validate(lane, {"rows": contents["rows"]}, canonical(result), sidecar={"rows": sidecar_contents["rows"]})
    except SOURCE.Invalid as exc:
        raise _semantic_failure(exc) from exc
    manifest = {
        "schema_version": "phase3_cycle007_gemini_raw_manifest_v2",
        "evaluation_cycle_id": CYCLE,
        "lane": lane,
        "packet_index": packet_index,
        "chunk_count": len(parts),
        "request_plan_sha256": request_plan_sha256,
        "planner_version": PLANNER_VERSION,
        "request_byte_budget": request_byte_budget,
        "label_prompt_sha256": _label_prompt_hash(expected_label_prompt_sha),
        "chunks": entries,
        "text_free": True,
    }
    manifest_hash, labels_hash = _atomic(raw_manifest_path, manifest), _atomic(labels_path, result)
    receipt = {
        "schema_version": "phase3_cycle007_gemini_packet_label_receipt_v2",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()),
        "materialization_manifest_raw_sha256": digest((package / "manifest.json").read_bytes()),
        "evidence_manifest_raw_sha256": digest((package / "evidence" / "manifest.json").read_bytes()),
        "lane": lane,
        "packet_index": packet_index,
        "row_count": contents["row_count"],
        "packet_raw_sha256": digest(source_path.read_bytes()),
        "packet_identity_set_sha256": contents["packet_identity_set_sha256"],
        "sidecar_raw_sha256": digest(sidecar_path.read_bytes()),
        "sidecar_id": sidecar_contents.get("sidecar_id", ""),
        "prompt_sha256": prompt_binding(package, lane, expected_label_prompt_sha=expected_label_prompt_sha)[1],
        "label_prompt_sha256": _label_prompt_hash(expected_label_prompt_sha),
        "raw_manifest_sha256": manifest_hash,
        "labels_sha256": labels_hash,
        "chunk_count": len(parts),
        "request_plan_sha256": request_plan_sha256,
        "planner_version": PLANNER_VERSION,
        "request_byte_budget": request_byte_budget,
        "exact_model": MODEL,
        "model_family": FAMILY,
        "harness": HARNESS,
        "text_free": True,
    }
    receipt["receipt_sha256"] = digest(canonical(receipt))
    _atomic(receipt_path, receipt)
    return {"ok": True, "lane": lane, "packet_index": packet_index, "chunk_count": len(parts), "text_free": True}


def verify_packet(
    package: Path,
    lane: str,
    packet_index: int,
    *,
    expected_label_prompt_sha: str | None,
    request_byte_budget: int = DEFAULT_REQUEST_BYTE_BUDGET,
) -> dict[str, Any]:
    source_path, contents, sidecar_path, sidecar_contents = packet(package, lane, packet_index)
    prompt_template, _prompt_sha256 = prompt_binding(
        package, lane, expected_label_prompt_sha=expected_label_prompt_sha
    )
    parts = chunks(
        contents,
        sidecar_contents,
        template=prompt_template,
        lane=lane,
        request_byte_budget=request_byte_budget,
    )
    plan = request_plan(
        contents,
        parts,
        lane=lane,
        packet_index=packet_index,
        request_byte_budget=request_byte_budget,
        label_prompt_sha256=_label_prompt_hash(expected_label_prompt_sha),
    )
    request_plan_sha256 = _bind_request_plan(_chunk_dir(package, lane, packet_index), plan)
    out = package / OUTPUT / lane
    labels_path, receipt_path, manifest_path = (
        out / f"labels-{packet_index:04d}.json",
        out / f"receipt-{packet_index:04d}.json",
        out / f"raw-manifest-{packet_index:04d}.json",
    )
    labels, receipt, manifest = _read_json(labels_path), _read_json(receipt_path), _read_json(manifest_path)
    for part, sidecar_part in parts:
        _verify_chunk(
            package,
            lane,
            packet_index,
            part,
            sidecar_part,
            expected_label_prompt_sha=expected_label_prompt_sha,
            request_plan_sha256=request_plan_sha256,
            request_byte_budget=request_byte_budget,
        )
    try:
        SOURCE.validate(lane, {"rows": contents["rows"]}, canonical(labels), sidecar={"rows": sidecar_contents["rows"]})
    except SOURCE.Invalid as exc:
        raise _semantic_failure(exc) from exc
    expected_manifest = {
        "schema_version": "phase3_cycle007_gemini_raw_manifest_v2",
        "evaluation_cycle_id": CYCLE,
        "lane": lane,
        "packet_index": packet_index,
        "chunk_count": len(parts),
        "request_plan_sha256": request_plan_sha256,
        "planner_version": PLANNER_VERSION,
        "request_byte_budget": request_byte_budget,
        "label_prompt_sha256": _label_prompt_hash(expected_label_prompt_sha),
        "chunks": manifest.get("chunks"),
        "text_free": True,
    }
    if manifest != expected_manifest:
        raise Error("ordinal_identity_binding_drift")
    expected = {
        "schema_version": "phase3_cycle007_gemini_packet_label_receipt_v2",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()),
        "materialization_manifest_raw_sha256": digest((package / "manifest.json").read_bytes()),
        "evidence_manifest_raw_sha256": digest((package / "evidence" / "manifest.json").read_bytes()),
        "lane": lane,
        "packet_index": packet_index,
        "row_count": contents["row_count"],
        "packet_raw_sha256": digest(source_path.read_bytes()),
        "packet_identity_set_sha256": contents["packet_identity_set_sha256"],
        "sidecar_raw_sha256": digest(sidecar_path.read_bytes()),
        "sidecar_id": sidecar_contents.get("sidecar_id", ""),
        "prompt_sha256": prompt_binding(package, lane, expected_label_prompt_sha=expected_label_prompt_sha)[1],
        "label_prompt_sha256": _label_prompt_hash(expected_label_prompt_sha),
        "raw_manifest_sha256": digest(manifest_path.read_bytes()),
        "labels_sha256": digest(labels_path.read_bytes()),
        "chunk_count": len(parts),
        "request_plan_sha256": request_plan_sha256,
        "planner_version": PLANNER_VERSION,
        "request_byte_budget": request_byte_budget,
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
    package: Path,
    lane: str,
    packet_index: int,
    provider: Path,
    *,
    expected_agy_sha256: str | None = None,
    expected_custody_sha256: str | None = None,
    expected_label_manifest_sha256: str | None = None,
    expected_evidence_manifest_sha256: str | None = None,
    expected_label_prompt_sha: str | None = None,
    request_byte_budget: int = DEFAULT_REQUEST_BYTE_BUDGET,
    max_new_chunks: int | None = None,
) -> dict[str, Any]:
    global EXPECTED_CUSTODY_SHA256, EXPECTED_LABEL_MANIFEST_SHA256, EXPECTED_EVIDENCE_MANIFEST_SHA256
    if max_new_chunks not in {None, 1}:
        raise Error("request_plan_binding_drift")
    if expected_custody_sha256 is not None:
        EXPECTED_CUSTODY_SHA256 = expected_custody_sha256
    if expected_label_manifest_sha256 is not None:
        EXPECTED_LABEL_MANIFEST_SHA256 = expected_label_manifest_sha256
    if expected_evidence_manifest_sha256 is not None:
        EXPECTED_EVIDENCE_MANIFEST_SHA256 = expected_evidence_manifest_sha256
    expected_label_prompt_sha = _label_prompt_hash(expected_label_prompt_sha)
    if expected_agy_sha256 is not None and (
        not isinstance(expected_agy_sha256, str) or len(expected_agy_sha256) != 64
    ):
        raise Error("ordinal_identity_binding_drift")
    source_path, contents, sidecar_path, sidecar_contents = packet(package, lane, packet_index)
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
        return verify_packet(
            package,
            lane,
            packet_index,
            expected_label_prompt_sha=expected_label_prompt_sha,
            request_byte_budget=request_byte_budget,
        )
    prompt_template, _prompt_sha256 = prompt_binding(
        package, lane, expected_label_prompt_sha=expected_label_prompt_sha
    )
    parts = chunks(
        contents,
        sidecar_contents,
        template=prompt_template,
        lane=lane,
        request_byte_budget=request_byte_budget,
    )
    plan = request_plan(
        contents,
        parts,
        lane=lane,
        packet_index=packet_index,
        request_byte_budget=request_byte_budget,
        label_prompt_sha256=expected_label_prompt_sha,
    )
    request_plan_sha256 = _bind_request_plan(_chunk_dir(package, lane, packet_index), plan)
    try:
        new_chunks = 0
        for part, sidecar_part in parts:
            chunk_result = _run_chunk(
                package,
                lane,
                packet_index,
                part,
                sidecar_part,
                provider,
                expected_agy_sha256,
                expected_label_prompt_sha,
                request_plan_sha256,
                request_byte_budget,
            )
            if chunk_result.get("resumed") is not True:
                new_chunks += 1
            if max_new_chunks is not None and new_chunks >= max_new_chunks:
                return {
                    "ok": True,
                    "partial": True,
                    "lane": lane,
                    "packet_index": packet_index,
                    "new_chunk_count": new_chunks,
                    "request_plan_sha256": request_plan_sha256,
                    "request_byte_budget": request_byte_budget,
                    "planner_version": PLANNER_VERSION,
                    "text_free": True,
                }
        _reassemble(
            package,
            lane,
            packet_index,
            source_path,
            contents,
            sidecar_path,
            sidecar_contents,
            parts,
            expected_label_prompt_sha=expected_label_prompt_sha,
            request_plan_sha256=request_plan_sha256,
            request_byte_budget=request_byte_budget,
        )
        return verify_packet(
            package,
            lane,
            packet_index,
            expected_label_prompt_sha=expected_label_prompt_sha,
            request_byte_budget=request_byte_budget,
        )
    except Error as exc:
        stop(package, lane, packet_index, exc.code)
        raise


def batch(
    package: Path,
    lane: str,
    start: int,
    end: int,
    provider: Path,
    *,
    concurrency: int = 1,
    expected_agy_sha256: str | None = None,
    expected_custody_sha256: str | None = None,
    expected_label_manifest_sha256: str | None = None,
    expected_evidence_manifest_sha256: str | None = None,
    expected_label_prompt_sha: str | None = None,
    request_byte_budget: int = DEFAULT_REQUEST_BYTE_BUDGET,
) -> dict[str, Any]:
    """Resume one contiguous packet range with fail-stop concurrency fixed at one."""
    global EXPECTED_CUSTODY_SHA256, EXPECTED_LABEL_MANIFEST_SHA256, EXPECTED_EVIDENCE_MANIFEST_SHA256
    if expected_custody_sha256 is not None:
        EXPECTED_CUSTODY_SHA256 = expected_custody_sha256
    if expected_label_manifest_sha256 is not None:
        EXPECTED_LABEL_MANIFEST_SHA256 = expected_label_manifest_sha256
    if expected_evidence_manifest_sha256 is not None:
        EXPECTED_EVIDENCE_MANIFEST_SHA256 = expected_evidence_manifest_sha256
    expected_label_prompt_sha = _label_prompt_hash(expected_label_prompt_sha)
    if lane not in LANES or not 1 <= start <= end <= LANES[lane] or concurrency != 1:
        raise Error("ordinal_identity_binding_drift")
    if (package / OUTPUT / "provider-stop.json").exists():
        raise Error("ordinal_identity_binding_drift")
    results: list[dict[str, Any]] = []
    for index in range(start, end + 1):
        if (package / OUTPUT / "provider-stop.json").exists():
            raise Error("ordinal_identity_binding_drift")
        results.append(
            run_packet(
                package,
                lane,
                index,
                provider,
                expected_agy_sha256=expected_agy_sha256,
                expected_label_prompt_sha=expected_label_prompt_sha,
                request_byte_budget=request_byte_budget,
            )
        )
    return {
        "ok": True,
        "lane": lane,
        "start": start,
        "end": end,
        "packet_count": len(results),
        "concurrency": 1,
        "label_prompt_sha256": expected_label_prompt_sha,
        "request_byte_budget": request_byte_budget,
        "planner_version": PLANNER_VERSION,
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
    parser.add_argument(
        "--request-byte-budget",
        type=int,
        choices=REQUEST_BYTE_BUDGET_STEPS,
        default=DEFAULT_REQUEST_BYTE_BUDGET,
        help="exact serialized stdin ceiling; frozen into the packet request plan",
    )
    parser.add_argument(
        "--max-new-chunks",
        type=int,
        choices=(1,),
        help="pilot-only fail-stop boundary; return after one newly committed production chunk",
    )
    provider = parser.add_mutually_exclusive_group(required=True)
    provider.add_argument("--provider-bin", type=Path, help="explicit real AGY executable")
    provider.add_argument("--test-provider-bin", type=Path, help="synthetic provider executable only")
    parser.add_argument(
        "--expected-agy-executable-sha", help="controller-bound AGY executable SHA256; required for real provider calls"
    )
    parser.add_argument("--expected-custody-sha", required=True, help="controller-bound custody receipt SHA256")
    parser.add_argument("--expected-label-manifest-sha", required=True, help="controller-bound label manifest SHA256")
    parser.add_argument(
        "--expected-evidence-manifest-sha", required=True, help="controller-bound evidence manifest SHA256"
    )
    parser.add_argument("--expected-server-code-sha", required=True, help="controller-bound Sources server SHA256")
    parser.add_argument("--expected-sources-db-sha", required=True, help="controller-bound sources DB SHA256")
    parser.add_argument("--expected-vesum-db-sha", required=True, help="controller-bound VESUM DB SHA256")
    parser.add_argument(
        "--expected-label-prompt-sha",
        required=True,
        help="independently reviewed immutable labeling-prompt SHA256 for the selected lane",
    )
    args = parser.parse_args()
    try:
        if args.concurrency != 1:
            raise Error("ordinal_identity_binding_drift")
        if args.provider_bin is not None:
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
            or len(args.expected_evidence_manifest_sha) != 64
            or any(character not in "0123456789abcdef" for character in args.expected_custody_sha)
            or any(character not in "0123456789abcdef" for character in args.expected_label_manifest_sha)
            or any(character not in "0123456789abcdef" for character in args.expected_evidence_manifest_sha)
            or any(
                len(value) != 64 or any(character not in "0123456789abcdef" for character in value)
                for value in (
                    args.expected_server_code_sha,
                    args.expected_sources_db_sha,
                    args.expected_vesum_db_sha,
                )
            )
            or len(args.expected_label_prompt_sha) != 64
            or any(character not in "0123456789abcdef" for character in args.expected_label_prompt_sha)
        ):
            raise Error("ordinal_identity_binding_drift")
        global EXPECTED_CUSTODY_SHA256, EXPECTED_LABEL_MANIFEST_SHA256, EXPECTED_EVIDENCE_MANIFEST_SHA256
        global EXPECTED_SOURCES_ENDPOINT_IDENTITY
        EXPECTED_CUSTODY_SHA256 = args.expected_custody_sha
        EXPECTED_LABEL_MANIFEST_SHA256 = args.expected_label_manifest_sha
        EXPECTED_EVIDENCE_MANIFEST_SHA256 = args.expected_evidence_manifest_sha
        EXPECTED_SOURCES_ENDPOINT_IDENTITY = {
            "server_code_sha256": args.expected_server_code_sha,
            "sources_db_sha256": args.expected_sources_db_sha,
            "vesum_db_sha256": args.expected_vesum_db_sha,
        }
        if args.packet_index is not None:
            if args.end is not None:
                raise Error("ordinal_identity_binding_drift")
            result = run_packet(
                args.package.resolve(),
                args.lane,
                args.packet_index,
                args.provider_bin or args.test_provider_bin,
                expected_agy_sha256=args.expected_agy_executable_sha,
                expected_label_prompt_sha=args.expected_label_prompt_sha,
                request_byte_budget=args.request_byte_budget,
                max_new_chunks=args.max_new_chunks,
            )
        elif args.start is not None and args.end is not None:
            if args.max_new_chunks is not None:
                raise Error("request_plan_binding_drift")
            result = batch(
                args.package.resolve(),
                args.lane,
                args.start,
                args.end,
                args.provider_bin or args.test_provider_bin,
                concurrency=args.concurrency,
                expected_agy_sha256=args.expected_agy_executable_sha,
                expected_label_prompt_sha=args.expected_label_prompt_sha,
                request_byte_budget=args.request_byte_budget,
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
