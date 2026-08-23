#!/usr/bin/env python3
"""Inert Cycle 007 evidence-compile throughput helpers.

These helpers are scaffolding for a reviewed resume addendum. They are not
imported by ``phase3_cycle007_evidence_compiler`` or
``batch_state/phase3-compile-cycle007-evidence-v1.py``. Calling them does
not compile evidence, start Sources, or install a sidecar bundle.

Public surfaces stay text-free: counts, hashes, tool names, and closed
failure codes only.
"""

from __future__ import annotations

import json
import os
import re
import stat
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from scripts.projects.open_model_data import phase3_cycle007_evidence_compiler as compiler
from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract

ACTIVATION_STATE = "scaffolding_only"
PROGRESS_SCHEMA_VERSION = "phase3_cycle007_compile_progress_v1"
EVALUATION_CYCLE_ID = compiler.EVALUATION_CYCLE_ID
CALL_CHAIN_SEED = "phase3-cycle007-mcp-tool-call-chain-v1"
SIDECAR_NAME_RE = re.compile(r"sidecar-(\d{4})\.json\Z")
TEMP_SIDECAR_NAME_RE = re.compile(r"\.sidecar-\d{4}\.json\.")
PRODUCTION_PACKET_WORKERS = 1
MAX_REVIEWED_PACKET_WORKERS = 4

PROGRESS_REQUIRED_KEYS: frozenset[str] = frozenset(
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
        "ordered_call_commitment_sha256",
        "tool_call_count",
        "counts_by_tool",
        "progress_sha256",
    }
)
PRIVATE_PROGRESS_KEYS: frozenset[str] = frozenset(
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
    }
)
_IDENTITY_COMPARE_KEYS: tuple[str, ...] = (
    "tokenizer_id",
    "tokenizer_version",
    "code_hashes",
    "server_code_sha256",
    "sources_db_sha256",
    "vesum_db_sha256",
)


class ThroughputScaffoldingError(ValueError):
    """Closed, text-free helper failure."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def initial_call_commitment() -> str:
    """Return the same call-chain seed ``LocalMcpSourcesClient`` starts from."""
    return contract.sha256_text(CALL_CHAIN_SEED)


def identity_sha256(expected_identity: Mapping[str, Any]) -> str:
    missing = [key for key in _IDENTITY_COMPARE_KEYS if key not in expected_identity]
    if missing:
        raise ThroughputScaffoldingError("identity_incomplete")
    return contract.sha256_value({key: expected_identity[key] for key in _IDENTITY_COMPARE_KEYS})


def sidecar_filename(packet_index: int) -> str:
    if not isinstance(packet_index, int) or isinstance(packet_index, bool) or packet_index < 1:
        raise ThroughputScaffoldingError("packet_index_invalid")
    return f"sidecar-{packet_index:04d}.json"


def bound_packet_workers(requested: int, *, authorized: bool = False) -> int:
    """Fail closed unless packet-parallel workers are explicitly authorized.

    Production wiring is serial (``requested == 1``). Option B remains off
    until a reviewed addendum sets ``authorized=True`` and a later PR
    actually starts N clients.
    """
    if not isinstance(requested, int) or isinstance(requested, bool):
        raise ThroughputScaffoldingError("packet_workers_out_of_range")
    if requested < 1 or requested > MAX_REVIEWED_PACKET_WORKERS:
        raise ThroughputScaffoldingError("packet_workers_out_of_range")
    if requested != PRODUCTION_PACKET_WORKERS and not authorized:
        raise ThroughputScaffoldingError("packet_workers_not_authorized")
    return requested


def extend_serial_call_commitment(
    prior_commitment: str,
    calls: Sequence[Mapping[str, Any]],
    *,
    starting_ordinal: int,
) -> tuple[str, int]:
    """Continue the compiler's ordered MCP call-chain without issuing calls."""
    if not _is_sha256(prior_commitment):
        raise ThroughputScaffoldingError("call_commitment_invalid")
    if not isinstance(starting_ordinal, int) or isinstance(starting_ordinal, bool) or starting_ordinal < 1:
        raise ThroughputScaffoldingError("call_ordinal_invalid")
    commitment = prior_commitment
    ordinal = starting_ordinal
    for raw_call in calls:
        if not isinstance(raw_call, Mapping):
            raise ThroughputScaffoldingError("call_record_invalid")
        tool = raw_call.get("tool")
        arguments_sha256 = raw_call.get("arguments_sha256")
        response_sha256 = raw_call.get("response_sha256")
        if not isinstance(tool, str) or not tool:
            raise ThroughputScaffoldingError("call_record_invalid")
        if not _is_sha256(arguments_sha256) or not _is_sha256(response_sha256):
            raise ThroughputScaffoldingError("call_record_invalid")
        call = {
            "ordinal": ordinal,
            "tool": tool,
            "arguments_sha256": arguments_sha256,
            "response_sha256": response_sha256,
        }
        commitment = contract.sha256_text(commitment + "\n" + contract.canonical_json(call))
        ordinal += 1
    return commitment, ordinal


def build_progress_receipt(
    *,
    sealed_packet_count: int,
    target_packet_count: int = compiler.REAL_PACKET_COUNT,
    target_row_count: int = compiler.REAL_ROW_COUNT,
    last_sealed_sidecar_sha256: str | None,
    last_sealed_sidecar_id: str | None,
    expected_identity: Mapping[str, Any],
    ordered_call_commitment_sha256: str,
    tool_call_count: int,
    counts_by_tool: Mapping[str, int],
) -> dict[str, Any]:
    """Build a text-free sealed-prefix receipt. Does not write it."""
    _require_count(sealed_packet_count, "sealed_packet_count")
    _require_count(target_packet_count, "target_packet_count", minimum=1)
    _require_count(target_row_count, "target_row_count", minimum=1)
    if sealed_packet_count > target_packet_count:
        raise ThroughputScaffoldingError("sealed_prefix_overflow")
    next_packet_index = sealed_packet_count + 1
    if sealed_packet_count == 0:
        if last_sealed_sidecar_sha256 is not None or last_sealed_sidecar_id is not None:
            raise ThroughputScaffoldingError("progress_last_sidecar_invalid")
    else:
        if not _is_sha256(last_sealed_sidecar_sha256):
            raise ThroughputScaffoldingError("progress_last_sidecar_invalid")
        if not isinstance(last_sealed_sidecar_id, str) or not last_sealed_sidecar_id.startswith("cycle007_sidecar:"):
            raise ThroughputScaffoldingError("progress_last_sidecar_invalid")
    if not _is_sha256(ordered_call_commitment_sha256):
        raise ThroughputScaffoldingError("call_commitment_invalid")
    _require_count(tool_call_count, "tool_call_count")
    if any(not isinstance(name, str) or not name for name in counts_by_tool):
        raise ThroughputScaffoldingError("tool_counts_invalid")
    if any(not isinstance(count, int) or isinstance(count, bool) or count < 0 for count in counts_by_tool.values()):
        raise ThroughputScaffoldingError("tool_counts_invalid")
    if sum(counts_by_tool.values()) != tool_call_count:
        raise ThroughputScaffoldingError("tool_counts_invalid")

    receipt = {
        "schema_version": PROGRESS_SCHEMA_VERSION,
        "text_free": True,
        "evaluation_cycle_id": EVALUATION_CYCLE_ID,
        "activation_state": ACTIVATION_STATE,
        "sealed_packet_count": sealed_packet_count,
        "next_packet_index": next_packet_index,
        "target_packet_count": target_packet_count,
        "target_row_count": target_row_count,
        "last_sealed_sidecar_sha256": last_sealed_sidecar_sha256,
        "last_sealed_sidecar_id": last_sealed_sidecar_id,
        "identity_sha256": identity_sha256(expected_identity),
        "ordered_call_commitment_sha256": ordered_call_commitment_sha256,
        "tool_call_count": tool_call_count,
        "counts_by_tool": dict(sorted(counts_by_tool.items())),
    }
    _reject_private_progress_keys(receipt)
    receipt["progress_sha256"] = contract.sha256_value(receipt)
    return receipt


def validate_progress_receipt(
    receipt: Mapping[str, Any],
    expected_identity: Mapping[str, Any],
    *,
    sealed_packet_count: int | None = None,
    last_sealed_sidecar_sha256: str | None = None,
) -> None:
    if not isinstance(receipt, Mapping) or set(receipt) != PROGRESS_REQUIRED_KEYS:
        raise ThroughputScaffoldingError("progress_shape_invalid")
    _reject_private_progress_keys(receipt)
    if receipt.get("schema_version") != PROGRESS_SCHEMA_VERSION:
        raise ThroughputScaffoldingError("progress_schema_drift")
    if receipt.get("text_free") is not True:
        raise ThroughputScaffoldingError("progress_not_text_free")
    if receipt.get("evaluation_cycle_id") != EVALUATION_CYCLE_ID:
        raise ThroughputScaffoldingError("progress_cycle_drift")
    if receipt.get("activation_state") != ACTIVATION_STATE:
        raise ThroughputScaffoldingError("progress_activation_drift")
    unsigned = {key: value for key, value in receipt.items() if key != "progress_sha256"}
    if receipt.get("progress_sha256") != contract.sha256_value(unsigned):
        raise ThroughputScaffoldingError("progress_hash_drift")
    if receipt.get("identity_sha256") != identity_sha256(expected_identity):
        raise ThroughputScaffoldingError("identity_drift")
    if sealed_packet_count is not None and receipt.get("sealed_packet_count") != sealed_packet_count:
        raise ThroughputScaffoldingError("progress_prefix_mismatch")
    if (
        last_sealed_sidecar_sha256 is not None
        and receipt.get("last_sealed_sidecar_sha256") != last_sealed_sidecar_sha256
    ):
        raise ThroughputScaffoldingError("progress_last_sidecar_mismatch")
    expected_next = int(receipt["sealed_packet_count"]) + 1
    if receipt.get("next_packet_index") != expected_next:
        raise ThroughputScaffoldingError("progress_next_index_mismatch")


def discard_incomplete_sidecar_temps(staging_dir: Path) -> int:
    """Remove compiler ``mkstemp`` leftovers. Never deletes a sealed sidecar."""
    if not staging_dir.is_dir() or staging_dir.is_symlink():
        raise ThroughputScaffoldingError("staging_unavailable")
    removed = 0
    for path in sorted(staging_dir.iterdir()):
        if path.is_symlink() or not path.is_file():
            continue
        if TEMP_SIDECAR_NAME_RE.search(path.name) is None:
            continue
        path.unlink()
        removed += 1
    return removed


def list_sealed_sidecar_indexes(staging_dir: Path) -> list[int]:
    if not staging_dir.is_dir() or staging_dir.is_symlink():
        raise ThroughputScaffoldingError("staging_unavailable")
    indexes: list[int] = []
    for path in sorted(staging_dir.iterdir()):
        if path.is_symlink():
            raise ThroughputScaffoldingError("staging_symlink")
        match = SIDECAR_NAME_RE.fullmatch(path.name)
        if match is None:
            if path.name == "progress.json" or TEMP_SIDECAR_NAME_RE.search(path.name):
                continue
            raise ThroughputScaffoldingError("staging_foreign_file")
        if not path.is_file():
            raise ThroughputScaffoldingError("staging_foreign_file")
        indexes.append(int(match.group(1)))
    return indexes


def assert_consecutive_prefix(indexes: Sequence[int]) -> int:
    if not indexes:
        return 0
    expected = list(range(1, len(indexes) + 1))
    if list(indexes) != expected:
        raise ThroughputScaffoldingError("sealed_prefix_gap")
    return indexes[-1]


def load_sidecar(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ThroughputScaffoldingError("sidecar_unreadable")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ThroughputScaffoldingError("sidecar_unreadable") from exc
    if not isinstance(payload, dict):
        raise ThroughputScaffoldingError("sidecar_shape_invalid")
    return payload


def assert_sidecar_identity(
    sidecar: Mapping[str, Any], expected_identity: Mapping[str, Any], packet_index: int
) -> None:
    if sidecar.get("packet_index") != packet_index:
        raise ThroughputScaffoldingError("sidecar_index_mismatch")
    if sidecar.get("evaluation_cycle_id") != EVALUATION_CYCLE_ID:
        raise ThroughputScaffoldingError("sidecar_cycle_drift")
    for key in _IDENTITY_COMPARE_KEYS:
        if sidecar.get(key) != expected_identity.get(key):
            raise ThroughputScaffoldingError("identity_drift")


def resume_next_packet_index(
    staging_dir: Path,
    expected_identity: Mapping[str, Any],
    *,
    progress: Mapping[str, Any] | None = None,
    target_packet_count: int = compiler.REAL_PACKET_COUNT,
) -> int:
    """Return the next packet index for a durable sealed prefix.

    ``1`` means start fresh. ``N+1`` means packets ``1..N`` already sealed.
    Does not compile the next packet and does not install ``output_dir``.
    """
    if not staging_dir.exists():
        if progress is not None:
            raise ThroughputScaffoldingError("progress_without_staging")
        return 1
    discard_incomplete_sidecar_temps(staging_dir)
    indexes = list_sealed_sidecar_indexes(staging_dir)
    sealed = assert_consecutive_prefix(indexes)
    last_sha256: str | None = None
    last_sidecar_id: str | None = None
    for packet_index in indexes:
        path = staging_dir / sidecar_filename(packet_index)
        sidecar = load_sidecar(path)
        assert_sidecar_identity(sidecar, expected_identity, packet_index)
        last_sha256 = contract.sha256_bytes(path.read_bytes())
        last_sidecar_id = str(sidecar.get("sidecar_id"))
    if progress is not None:
        validate_progress_receipt(
            progress,
            expected_identity,
            sealed_packet_count=sealed,
            last_sealed_sidecar_sha256=last_sha256,
        )
        if progress.get("target_packet_count") != target_packet_count:
            raise ThroughputScaffoldingError("progress_target_drift")
        if last_sidecar_id is not None and progress.get("last_sealed_sidecar_id") != last_sidecar_id:
            raise ThroughputScaffoldingError("progress_last_sidecar_mismatch")
    if sealed > target_packet_count:
        raise ThroughputScaffoldingError("sealed_prefix_overflow")
    return sealed + 1


def production_wiring_is_inactive() -> bool:
    """True when the frozen compiler and runner do not import this module."""
    compiler_text = Path(compiler.__file__).read_text(encoding="utf-8")
    runner_path = compiler.ROOT / "batch_state" / "phase3-compile-cycle007-evidence-v1.py"
    runner_text = runner_path.read_text(encoding="utf-8")
    marker = "phase3_cycle007_evidence_compile_throughput"
    return marker not in compiler_text and marker not in runner_text


def packet_loop_is_serial() -> bool:
    """True when ``compile_sidecar_bundle`` still walks packets in a for-loop."""
    text = Path(compiler.__file__).read_text(encoding="utf-8")
    return "for packet_index, (rows, residual_lane, packet_binding) in enumerate(" in text


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _require_count(value: Any, _label: str, *, minimum: int = 0) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ThroughputScaffoldingError("count_invalid")


def _reject_private_progress_keys(receipt: Mapping[str, Any]) -> None:
    if PRIVATE_PROGRESS_KEYS & set(receipt):
        raise ThroughputScaffoldingError("progress_not_text_free")


def write_private_json(path: Path, payload: Mapping[str, Any]) -> str:
    """Atomic mode-0600 write for tests. Not a production installer."""
    encoded = (contract.canonical_json(payload) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True, mode=compiler.PRIVATE_DIR_MODE)
    os.chmod(path.parent, compiler.PRIVATE_DIR_MODE)
    return compiler._atomic_write_private(path, encoded)


def assert_private_modes(root: Path) -> None:
    if stat.S_IMODE(root.stat().st_mode) != compiler.PRIVATE_DIR_MODE:
        raise ThroughputScaffoldingError("staging_mode_drift")
    for path in sorted(root.rglob("*")):
        expected = compiler.PRIVATE_DIR_MODE if path.is_dir() else compiler.PRIVATE_FILE_MODE
        if stat.S_IMODE(path.stat().st_mode) != expected:
            raise ThroughputScaffoldingError("staging_mode_drift")
