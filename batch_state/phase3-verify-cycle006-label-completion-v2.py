#!/usr/bin/env python3
"""Fail-closed, text-free certification of the complete Cycle-006 label path.

The verifier is read-only with respect to the private package.  It consumes the
materialized packets and the sealed Grok, Gemini, comparison, adjudication, and
candidate-resolution artifacts, then writes one aggregate receipt containing
counts and hashes only.  It never prints packet, label, prompt, or provider
response content.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import stat
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CYCLE = "phase3-v2-1-evaluation-cycle-006"
AMENDMENT_SHA256 = "524e6eb4f18d38f104413fb32f421ff73c3d80bc411d338a6d8a31fabc087474"
SOURCE_CUSTODY_SHA256 = "7047e8459433376f3b690cfc2f15e115d77a701e79afb0ef2db184b44ea14726"
SOURCE_MANIFEST_SHA256 = "b8d290ffe945a6cc5d36345cbf234ccf79a7df98cb4199ffad0b778cd2b69fab"
ORDERED_IDENTITY_COMMITMENT_SHA256 = "331fd7fbc42e43cb3c218d9c2b790df060c0a553ab7c3a7b3b557f9f2bc3c419"
LANES = {"clean_label": 40, "residual_label": 164}
LANE_ROW_COUNTS = {"clean_label": 2_000, "residual_label": 8_159}
ROW_COUNT = 10_159
PACKET_COUNT = 204
GROK_ROOT = "label-output-grok-cycle006-v2"
GEMINI_ROOT = "label-output-gemini-cycle006-v2"
COMPARE_ROOT = "dual-label-output-cycle006-v2"
ADJUDICATION_ROOT = "dual-label-adjudication-cycle006-v2"
RESOLUTION_ROOT = "dual-label-final-cycle006-v2"
LABEL_VALIDATOR = HERE / "phase3-cycle006-label-validation-v2.py"
ADJUDICATION_PROMPT = HERE / "phase3-cycle005-dual-label-adjudication-prompt-v1.md"
ADJUDICATION_PROMPT_SHA256 = "8b932ccaf2626092b85ceed48d2ffc42abf007a472c22fbbee915e0e8ab3034e"
EXPECTED_MODELS = {
    "grok": {"exact_model": "grok-4.5", "model_family": "xai", "harness": "native_grok"},
    "gemini": {
        "exact_model": "Gemini 3.6 Flash (High)",
        "model_family": "google",
        "harness": "agy",
    },
}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
MARKER_NAMES = re.compile(r"^(?:attempt-\d+.*|invalid-\d+.*)\.(?:json|raw)$")
FAILURE_CODES = frozenset(
    {
        "operator_inspected_count",
        "package_modes",
        "no_temp_dirs",
        "no_provider_stop",
        "legacy_output_dependency",
        "source_manifest_binding",
        "exact_packet_denominator",
        "ordered_identity_denominator",
        "provider_receipt_coverage",
        "comparison_receipts",
        "comparison_batch_receipt",
        "adjudication_candidate_partition",
        "resolution_authorization",
        "final_identity_union",
        "final_residual_zero",
        "closure_validation_failed",
    }
)


class Error(ValueError):
    """A closed, text-free certification failure."""

    def __init__(self, code: str):
        self.code = code if code in FAILURE_CODES else "closure_validation_failed"
        super().__init__(self.code)


def _load(name: str, path: Path) -> ModuleType:
    if path.is_symlink() or not path.is_file():
        raise Error("closure_validation_failed")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise Error("closure_validation_failed")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GROK = _load("cycle006_completion_grok", HERE / "phase3-run-cycle006-grok-label-provider-batch-v2.py")
CMP = _load("cycle006_completion_compare", HERE / "phase3-compare-cycle006-dual-labels-v2.py")
ADJ = _load("cycle006_completion_adjudication", HERE / "phase3-run-cycle006-dual-label-adjudication-v2.py")
RES = _load("cycle006_completion_resolution", HERE / "phase3-apply-cycle006-operator-resolutions-v2.py")


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in items:
        if key in value:
            raise Error("closure_validation_failed")
        value[key] = item
    return value


def _regular(path: Path, mode: int = 0o600) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        raise Error("closure_validation_failed") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != mode:
        raise Error("package_modes")


def _directory(path: Path, mode: int = 0o700) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        raise Error("closure_validation_failed") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) != mode:
        raise Error("package_modes")


def _read_json(path: Path, *, canonical_bytes: bool = True) -> tuple[dict[str, Any], bytes]:
    _regular(path)
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=_pairs)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, Error) as exc:
        raise Error("closure_validation_failed") from exc
    if not isinstance(value, dict) or (canonical_bytes and raw != canonical(value)):
        raise Error("closure_validation_failed")
    return value, raw


def _atomic(path: Path, value: dict[str, Any]) -> str:
    data = canonical(value)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.exists() or path.is_symlink():
        _regular(path)
        if path.read_bytes() != data:
            raise Error("closure_validation_failed")
        return digest(data)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
        os.chmod(path, 0o600)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
    return digest(data)


def _identity(row: Any) -> tuple[str, str]:
    if not isinstance(row, dict):
        raise Error("ordered_identity_denominator")
    unit_id, unit_sha256 = row.get("unit_id"), row.get("unit_sha256")
    if (
        not isinstance(unit_id, str)
        or not unit_id
        or not isinstance(unit_sha256, str)
        or HEX64.fullmatch(unit_sha256) is None
    ):
        raise Error("ordered_identity_denominator")
    return unit_id, unit_sha256


def _identities(rows: list[Any]) -> list[tuple[str, str]]:
    values = [_identity(row) for row in rows]
    if len(values) != len(set(values)):
        raise Error("ordered_identity_denominator")
    return values


def _walk_modes(package: Path) -> None:
    _directory(package)
    for path in (package, *package.rglob("*")):
        if path.is_symlink():
            raise Error("package_modes")
        if path.is_dir():
            if stat.S_IMODE(path.stat().st_mode) != 0o700:
                raise Error("package_modes")
        elif path.is_file():
            if stat.S_IMODE(path.stat().st_mode) != 0o600:
                raise Error("package_modes")
        else:
            raise Error("package_modes")


def _no_temp_dirs(package: Path) -> None:
    for path in package.rglob("*"):
        if path.is_dir() and path.name.startswith(".cycle006-"):
            raise Error("no_temp_dirs")


def _package_roots(package: Path) -> None:
    legacy = {
        "label-output",
        "label-output-gemini-v2",
        "dual-label-output",
        "label-output-grok-cycle006-v1",
        "label-output-gemini-cycle006-v1",
        "dual-label-adjudication-cycle006-v1",
        "dual-label-final-cycle006-v1",
    }
    if any((package / name).exists() or (package / name).is_symlink() for name in legacy):
        raise Error("legacy_output_dependency")
    stop_roots = (GROK_ROOT, GEMINI_ROOT, COMPARE_ROOT, ADJUDICATION_ROOT)
    if any((package / root / "provider-stop.json").exists() for root in stop_roots):
        raise Error("no_provider_stop")


def _manifest(package: Path) -> tuple[dict[str, Any], dict[str, Any], str, str]:
    _directory(package)
    custody, custody_raw = _read_json(package / "custody-receipt.json")
    manifest, manifest_raw = _read_json(package / "label-manifest.json")
    custody_hash = digest(custody_raw)
    manifest_hash = digest(manifest_raw)
    if (
        custody.get("schema_version") != "phase3_cycle006_custody_receipt_v2"
        or custody.get("evaluation_cycle_id") != CYCLE
        or custody.get("source_evaluation_cycle_id") != "phase3-v2-1-evaluation-cycle-005"
        or custody.get("cycle006_amendment_raw_sha256") != AMENDMENT_SHA256
        or custody.get("source_custody_receipt_raw_sha256") != SOURCE_CUSTODY_SHA256
        or custody.get("source_label_manifest_raw_sha256") != SOURCE_MANIFEST_SHA256
        or custody.get("ordered_identity_commitment_sha256") != ORDERED_IDENTITY_COMMITMENT_SHA256
        or custody.get("packet_count") != PACKET_COUNT
        or custody.get("row_count") != ROW_COUNT
        or custody.get("lane_row_counts") != LANE_ROW_COUNTS
        or custody.get("packet_size") != 50
        or custody.get("gemini_chunk_size") != 20
        or custody.get("provider_artifacts_copied") is not False
        or custody.get("labels_copied") is not False
        or custody.get("responses_copied") is not False
        or custody.get("text_free") is not True
        or custody.get("receipt_sha256")
        != digest(canonical({key: item for key, item in custody.items() if key != "receipt_sha256"}))
        or manifest.get("schema_version") != "phase3_cycle006_label_manifest_v2"
        or manifest.get("evaluation_cycle_id") != CYCLE
        or manifest.get("source_evaluation_cycle_id") != "phase3-v2-1-evaluation-cycle-005"
        or manifest.get("custody_receipt_raw_sha256") != custody_hash
        or manifest.get("cycle006_amendment_raw_sha256") != AMENDMENT_SHA256
        or manifest.get("source_custody_receipt_raw_sha256") != SOURCE_CUSTODY_SHA256
        or manifest.get("source_label_manifest_raw_sha256") != SOURCE_MANIFEST_SHA256
        or manifest.get("ordered_identity_commitment_sha256") != ORDERED_IDENTITY_COMMITMENT_SHA256
        or manifest.get("packet_count") != PACKET_COUNT
        or manifest.get("row_count") != ROW_COUNT
        or manifest.get("lane_row_counts") != LANE_ROW_COUNTS
        or manifest.get("text_free") is not True
        or manifest.get("receipt_sha256")
        != digest(canonical({key: item for key, item in manifest.items() if key != "receipt_sha256"}))
    ):
        raise Error("source_manifest_binding")
    bindings = manifest.get("prompt_bindings")
    prompt_hashes = manifest.get("prompt_sha256s")
    if bindings != custody.get("prompt_bindings") or prompt_hashes != custody.get("prompt_sha256s"):
        raise Error("source_manifest_binding")
    if not isinstance(bindings, list) or not isinstance(prompt_hashes, dict):
        raise Error("source_manifest_binding")
    binding_keys: set[tuple[str, str]] = set()
    for binding in bindings:
        if not isinstance(binding, dict) or set(binding) != {"lane", "provider", "path", "sha256"}:
            raise Error("source_manifest_binding")
        key = (binding.get("lane"), binding.get("provider"))
        path = binding.get("path")
        prompt_hash = binding.get("sha256")
        if key in binding_keys or key not in {(lane, provider) for lane in LANES for provider in ("grok", "gemini")}:
            raise Error("source_manifest_binding")
        if (
            not isinstance(path, str)
            or Path(path).is_absolute()
            or ".." in Path(path).parts
            or not isinstance(prompt_hash, str)
            or HEX64.fullmatch(prompt_hash) is None
        ):
            raise Error("source_manifest_binding")
        if prompt_hashes.get(path) != prompt_hash:
            raise Error("source_manifest_binding")
        prompt_path = package / path
        _regular(prompt_path)
        if digest(prompt_path.read_bytes()) != prompt_hash:
            raise Error("source_manifest_binding")
        binding_keys.add(key)
    if binding_keys != {(lane, provider) for lane in LANES for provider in ("grok", "gemini")}:
        raise Error("source_manifest_binding")
    packets = manifest.get("packets")
    if not isinstance(packets, list) or len(packets) != PACKET_COUNT:
        raise Error("exact_packet_denominator")
    expected_order = [(lane, index) for lane, count in LANES.items() for index in range(1, count + 1)]
    actual_order = [(item.get("lane"), item.get("packet_index")) for item in packets if isinstance(item, dict)]
    if actual_order != expected_order:
        raise Error("ordered_identity_denominator")
    return manifest, custody, custody_hash, manifest_hash


def _packet(package: Path, manifest: dict[str, Any], lane: str, index: int) -> tuple[Path, dict[str, Any]]:
    if lane not in LANES or not 1 <= index <= LANES[lane]:
        raise Error("exact_packet_denominator")
    expected_count = 9 if lane == "residual_label" and index == LANES[lane] else 50
    path = package / lane / f"packet-{index:04d}.json"
    value, raw = _read_json(path)
    if (
        set(value)
        != {
            "schema_version",
            "evaluation_cycle_id",
            "lane",
            "packet_index",
            "row_count",
            "rows",
            "packet_identity_set_sha256",
        }
        or value.get("schema_version") != "phase3_cycle006_private_packet_v1"
        or value.get("evaluation_cycle_id") != CYCLE
        or value.get("lane") != lane
        or value.get("packet_index") != index
        or value.get("row_count") != expected_count
        or not isinstance(value.get("rows"), list)
        or len(value["rows"]) != expected_count
        or raw != canonical(value)
    ):
        raise Error("exact_packet_denominator")
    identities = _identities(value["rows"])
    if value.get("packet_identity_set_sha256") != digest(canonical(sorted(identities))):
        raise Error("ordered_identity_denominator")
    matches = [
        item
        for item in manifest["packets"]
        if isinstance(item, dict) and item.get("lane") == lane and item.get("packet_index") == index
    ]
    expected = {
        "lane": lane,
        "packet_index": index,
        "canonical_basename": path.name,
        "row_count": expected_count,
        "raw_sha256": digest(raw),
        "packet_identity_set_sha256": value["packet_identity_set_sha256"],
    }
    if matches != [expected]:
        raise Error("ordered_identity_denominator")
    return path, value


def _prompt_path(package: Path, lane: str, provider: str) -> tuple[str, str]:
    manifest, custody, _custody_hash, _manifest_hash = _manifest(package)
    bindings = [
        item for item in manifest["prompt_bindings"] if item.get("lane") == lane and item.get("provider") == provider
    ]
    if len(bindings) != 1:
        raise Error("source_manifest_binding")
    binding = bindings[0]
    path, prompt_hash = binding["path"], binding["sha256"]
    _regular(package / path)
    if (
        digest((package / path).read_bytes()) != prompt_hash
        or custody.get("prompt_sha256s", {}).get(path) != prompt_hash
    ):
        raise Error("source_manifest_binding")
    return path, prompt_hash


def _adjudication_prompt_hash() -> str:
    """Independently bind the frozen adjudicator prompt by hash only."""
    _regular(ADJUDICATION_PROMPT, 0o644)
    if (
        getattr(ADJ, "PROMPT", None) != ADJUDICATION_PROMPT
        or getattr(ADJ, "PROMPT_SHA256", None) != ADJUDICATION_PROMPT_SHA256
        or digest(ADJUDICATION_PROMPT.read_bytes()) != ADJUDICATION_PROMPT_SHA256
    ):
        raise Error("source_manifest_binding")
    return ADJUDICATION_PROMPT_SHA256


def _provider_shape(package: Path, root: str, lane: str, count: int, provider: str) -> None:
    output = package / root
    _directory(output)
    lane_dir = output / lane
    _directory(lane_dir)
    expected = {
        *(f"labels-{index:04d}.json" for index in range(1, count + 1)),
        *(f"receipt-{index:04d}.json" for index in range(1, count + 1)),
        *(f"raw-manifest-{index:04d}.json" for index in range(1, count + 1)),
    }
    if provider == "grok":
        expected |= {f"raw-{index:04d}.raw" for index in range(1, count + 1)}
    names = {path.name for path in lane_dir.iterdir() if path.is_file()}
    extras = names - expected
    if not expected.issubset(names) or any(not MARKER_NAMES.fullmatch(name) for name in extras):
        raise Error("provider_receipt_coverage")
    directories = {path.name for path in lane_dir.iterdir() if path.is_dir()}
    if provider == "grok" and directories:
        raise Error("provider_receipt_coverage")
    if provider == "gemini" and directories != {"chunks"}:
        raise Error("provider_receipt_coverage")
    if provider == "gemini":
        chunks = lane_dir / "chunks"
        _directory(chunks)
        packet_names = {path.name for path in chunks.iterdir() if path.is_dir()}
        expected_packets = {f"packet-{index:04d}" for index in range(1, count + 1)}
        if packet_names != expected_packets:
            raise Error("provider_receipt_coverage")


def _verify_compare_packet(
    package: Path,
    manifest: dict[str, Any],
    lane: str,
    index: int,
    custody_hash: str,
    manifest_hash: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    _packet_path, contents = _packet(package, manifest, lane, index)
    try:
        contents_checked, grok_labels, gemini_labels = CMP.inputs(package, lane, index, manifest)
    except Exception as exc:
        raise Error("comparison_receipts") from exc
    if contents_checked != contents:
        raise Error("comparison_receipts")
    compare_dir = package / COMPARE_ROOT / lane
    receipt, receipt_raw = _read_json(compare_dir / f"receipt-{index:04d}.json")
    consensus, consensus_raw = _read_json(compare_dir / f"consensus-{index:04d}.json")
    disagreements, disagreements_raw = _read_json(compare_dir / f"disagreements-{index:04d}.json")
    expected_common = {
        "schema_version": "phase3_cycle006_dual_label_packet_receipt_v2",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": custody_hash,
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": manifest_hash,
        "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
        "lane": lane,
        "packet_index": index,
        "row_count": contents["row_count"],
        "packet_identity_set_sha256": contents["packet_identity_set_sha256"],
        "grok": EXPECTED_MODELS["grok"],
        "gemini": EXPECTED_MODELS["gemini"],
        "silent_selection": False,
        "text_free": True,
    }
    if (
        not isinstance(consensus, dict)
        or set(consensus) != {"labels"}
        or not isinstance(consensus["labels"], list)
        or consensus_raw != canonical(consensus)
    ):
        raise Error("comparison_receipts")
    if (
        not isinstance(disagreements, dict)
        or set(disagreements) != {"records"}
        or not isinstance(disagreements["records"], list)
        or disagreements_raw != canonical(disagreements)
    ):
        raise Error("comparison_receipts")
    expected_consensus = [
        left
        for left, right in zip(grok_labels, gemini_labels, strict=True)
        if CMP.semantic(left) == CMP.semantic(right)
    ]
    expected_disagreements = [
        {"source_row": source, "grok_label": left, "gemini_label": right}
        for source, left, right in zip(contents["rows"], grok_labels, gemini_labels, strict=True)
        if CMP.semantic(left) != CMP.semantic(right)
    ]
    if consensus["labels"] != expected_consensus or disagreements["records"] != expected_disagreements:
        raise Error("comparison_receipts")
    expected = {
        **expected_common,
        "consensus_count": len(expected_consensus),
        "disagreement_count": len(expected_disagreements),
        "consensus_sha256": digest(consensus_raw),
        "disagreements_sha256": digest(disagreements_raw),
    }
    if (
        set(receipt) != set(expected) | {"receipt_sha256"}
        or any(receipt.get(key) != value for key, value in expected.items())
        or receipt.get("receipt_sha256") != digest(canonical(expected))
        or receipt_raw != canonical(receipt)
    ):
        raise Error("comparison_receipts")
    return contents, grok_labels, gemini_labels, receipt


def _check_compare_batch(package: Path, receipts: list[dict[str, Any]], custody_hash: str, manifest_hash: str) -> str:
    value, raw = _read_json(package / COMPARE_ROOT / "batch-receipt.json")
    expected = {
        "schema_version": "phase3_cycle006_dual_label_batch_receipt_v2",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": custody_hash,
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": manifest_hash,
        "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
        "packet_count": PACKET_COUNT,
        "row_count": ROW_COUNT,
        "consensus_count": sum(item["consensus_count"] for item in receipts),
        "disagreement_count": sum(item["disagreement_count"] for item in receipts),
        "packet_receipt_union_sha256": digest(canonical([item["receipt_sha256"] for item in receipts])),
        "grok": EXPECTED_MODELS["grok"],
        "gemini": EXPECTED_MODELS["gemini"],
        "silent_selection": False,
        "text_free": True,
    }
    if (
        set(value) != set(expected) | {"receipt_sha256"}
        or any(value.get(key) != item for key, item in expected.items())
        or value.get("receipt_sha256") != digest(canonical(expected))
        or raw != canonical(value)
    ):
        raise Error("comparison_batch_receipt")
    return digest(raw)


def _verify_adjudication_packet(
    package: Path,
    lane: str,
    index: int,
    expected_rows: int,
    custody_hash: str,
    manifest_hash: str,
    compare_receipt: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], int, int]:
    try:
        result = ADJ.verify_packet(package, lane, index)
    except Exception as exc:
        raise Error("adjudication_candidate_partition") from exc
    labels_path = package / ADJUDICATION_ROOT / "final" / lane / f"labels-{index:04d}.json"
    unresolved_path = package / ADJUDICATION_ROOT / "final" / lane / f"unresolved-{index:04d}.json"
    receipt_path = package / ADJUDICATION_ROOT / "final" / lane / f"receipt-{index:04d}.json"
    labels, labels_raw = _read_json(labels_path)
    unresolved, unresolved_raw = _read_json(unresolved_path)
    receipt, receipt_raw = _read_json(receipt_path)
    if (
        set(labels) != {"labels"}
        or not isinstance(labels["labels"], list)
        or labels_raw != canonical(labels)
        or set(unresolved) != {"identities"}
        or not isinstance(unresolved["identities"], list)
        or unresolved_raw != canonical(unresolved)
        or receipt.get("schema_version") != "phase3_cycle006_final_label_packet_receipt_v2"
        or receipt.get("evaluation_cycle_id") != CYCLE
        or receipt.get("amendment_sha256") != AMENDMENT_SHA256
        or receipt.get("custody_receipt_raw_sha256") != custody_hash
        or receipt.get("source_label_manifest_raw_sha256") != SOURCE_MANIFEST_SHA256
        or receipt.get("ordered_identity_commitment_sha256") != ORDERED_IDENTITY_COMMITMENT_SHA256
        or receipt.get("lane") != lane
        or receipt.get("packet_index") != index
        or receipt.get("row_count") != expected_rows
        or receipt.get("packet_identity_set_sha256") != compare_receipt["packet_identity_set_sha256"]
        or receipt.get("compare_receipt_sha256") != compare_receipt["receipt_sha256"]
        or receipt.get("candidate_only") is not True
        or receipt.get("text_free") is not True
        or receipt.get("labels_sha256") != digest(labels_raw)
        or receipt.get("unresolved_sha256") != digest(unresolved_raw)
        or receipt.get("receipt_sha256")
        != digest(canonical({key: item for key, item in receipt.items() if key != "receipt_sha256"}))
        or receipt_raw != canonical(receipt)
        or result.get("accepted_count") != len(labels["labels"])
        or result.get("unresolved_count") != len(unresolved["identities"])
    ):
        raise Error("adjudication_candidate_partition")
    return labels, unresolved, receipt["selection_count"], receipt["unresolved_count"]


def _verify_resolution(
    package: Path, lane: str, index: int, source_ids: list[tuple[str, str]]
) -> tuple[dict[str, Any], int, int, int]:
    try:
        result = RES.effective(package, lane, index)
    except Exception as exc:
        raise Error("resolution_authorization") from exc
    labels = result.get("labels")
    unresolved = result.get("unresolved")
    if not isinstance(labels, list) or not isinstance(unresolved, list):
        raise Error("resolution_authorization")
    label_ids = _identities(labels)
    unresolved_ids = _identities(unresolved)
    if (
        len(label_ids) + len(unresolved_ids) != len(source_ids)
        or set(label_ids + unresolved_ids) != set(source_ids)
        or set(label_ids).intersection(unresolved_ids)
    ):
        raise Error("final_identity_union")
    operator_count = result.get("operator_resolution_count")
    advisor_count = result.get("designated_advisor_resolution_count")
    if type(operator_count) is not int or type(advisor_count) is not int or operator_count < 0 or advisor_count < 0:
        raise Error("resolution_authorization")
    if result.get("accepted_count") != len(labels) or result.get("unresolved_count") != len(unresolved):
        raise Error("resolution_authorization")
    resolution_paths = RES._paths(package, lane, index)
    if not any(path.exists() or path.is_symlink() for path in resolution_paths) and (operator_count or advisor_count):
        raise Error("resolution_authorization")
    if all(path.exists() and not path.is_symlink() for path in resolution_paths) and not (
        operator_count or advisor_count
    ):
        raise Error("resolution_authorization")
    return result, len(labels), len(unresolved), operator_count + advisor_count


def _code_hashes() -> dict[str, str]:
    paths = {
        "label_validator": LABEL_VALIDATOR,
        "grok": HERE / "phase3-run-cycle006-grok-label-provider-batch-v2.py",
        "gemini": HERE / "phase3-run-cycle006-gemini-label-provider-batch-v2.py",
        "compare": HERE / "phase3-compare-cycle006-dual-labels-v2.py",
        "adjudication": HERE / "phase3-run-cycle006-dual-label-adjudication-v2.py",
        "resolution": HERE / "phase3-apply-cycle006-operator-resolutions-v2.py",
        "certifier": HERE / "phase3-verify-cycle006-label-completion-v2.py",
    }
    for path in paths.values():
        _regular(path, 0o644)
    return {name: digest(path.read_bytes()) for name, path in paths.items()}


def verify(package: Path, output: Path, operator_inspected_count: int) -> dict[str, Any]:
    gates = {
        name: False
        for name in (
            "operator_inspected_count",
            "package_modes",
            "no_temp_dirs",
            "no_provider_stop",
            "source_manifest_binding",
            "exact_packet_denominator",
            "ordered_identity_denominator",
            "provider_receipt_coverage",
            "comparison_receipts",
            "comparison_batch_receipt",
            "adjudication_candidate_partition",
            "resolution_authorization",
            "final_identity_union",
            "final_residual_zero",
        )
    }
    evidence: dict[str, Any] = {
        "schema_version": "phase3_cycle006_label_completion_receipt_v2",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "operator_inspected_count": operator_inspected_count,
        "expected": {
            "source_custody_receipt_raw_sha256": SOURCE_CUSTODY_SHA256,
            "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
            "packet_count": PACKET_COUNT,
            "row_count": ROW_COUNT,
            "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
        },
        "package": {
            "custody_receipt_raw_sha256": None,
            "label_manifest_raw_sha256": None,
        },
        "adjudication_prompt_sha256": None,
        "provider_coverage": {
            "grok": {"packet_count": 0, "row_count": 0},
            "gemini": {"packet_count": 0, "row_count": 0},
        },
        "totals": {
            "consensus": 0,
            "disagreement": 0,
            "adjudicated": 0,
            "operator_resolved": 0,
            "advisor_resolved": 0,
            "accepted": 0,
            "unresolved": 0,
        },
        "union": {
            "source_identity_count": 0,
            "final_identity_count": 0,
            "identity_union_commitment_sha256": None,
            "final_identity_union_commitment_sha256": None,
            "ordered_identity_stream_sha256": None,
        },
        "upstream_receipts": {},
        "code_hashes": {},
        "gates": gates,
        "reason_codes": [],
        "text_free": True,
        "complete": False,
        "certified": False,
    }
    reasons: set[str] = set()

    def gate(name: str, passed: bool) -> None:
        gates[name] = bool(passed)
        if not passed:
            reasons.add(name)

    try:
        gate(
            "operator_inspected_count",
            type(operator_inspected_count) is int and 0 <= operator_inspected_count <= ROW_COUNT,
        )
        _walk_modes(package)
        gate("package_modes", True)
        _no_temp_dirs(package)
        gate("no_temp_dirs", True)
        _package_roots(package)
        gate("no_provider_stop", True)
        manifest, custody, custody_hash, manifest_hash = _manifest(package)
        evidence["package"] = {
            "custody_receipt_raw_sha256": custody_hash,
            "label_manifest_raw_sha256": manifest_hash,
        }
        evidence["adjudication_prompt_sha256"] = _adjudication_prompt_hash()
        gate("source_manifest_binding", True)
        source_ids: list[tuple[str, str]] = []
        ordered_stream: list[list[Any]] = []
        packet_keys: set[tuple[str, int]] = set()
        packet_records = manifest["packets"]
        for lane, count in LANES.items():
            _directory(package / lane)
            actual_names = {path.name for path in (package / lane).iterdir() if path.is_file()}
            expected_names = {f"packet-{index:04d}.json" for index in range(1, count + 1)}
            if actual_names != expected_names:
                raise Error("exact_packet_denominator")
            for index in range(1, count + 1):
                packet_path, contents = _packet(package, manifest, lane, index)
                del packet_path
                packet_keys.add((lane, index))
                identities = _identities(contents["rows"])
                source_ids.extend(identities)
                ordered_stream.extend(
                    [
                        [lane, index, row_index, identity[0], identity[1]]
                        for row_index, identity in enumerate(identities)
                    ]
                )
        expected_packet_keys = {(lane, index) for lane, count in LANES.items() for index in range(1, count + 1)}
        if packet_keys != expected_packet_keys or len(source_ids) != ROW_COUNT or len(set(source_ids)) != ROW_COUNT:
            raise Error("exact_packet_denominator")
        gate("exact_packet_denominator", True)
        identity_union = digest(canonical(sorted(source_ids)))
        ordered_hash = digest(canonical(ordered_stream))
        packet_hash = digest(canonical(packet_records))
        if (
            manifest.get("identity_union_commitment_sha256") != identity_union
            or custody.get("identity_union_commitment_sha256") != identity_union
            or manifest.get("ordered_identity_commitment_sha256") != ordered_hash
            or custody.get("ordered_identity_commitment_sha256") != ordered_hash
            or manifest.get("ordered_packet_commitment_sha256") != packet_hash
            or custody.get("ordered_packet_commitment_sha256") != packet_hash
        ):
            raise Error("ordered_identity_denominator")
        evidence["union"]["identity_union_commitment_sha256"] = identity_union
        evidence["union"]["ordered_identity_stream_sha256"] = ordered_hash
        gate("ordered_identity_denominator", True)
        for lane, count in LANES.items():
            _provider_shape(package, GROK_ROOT, lane, count, "grok")
            _provider_shape(package, GEMINI_ROOT, lane, count, "gemini")
        gate("provider_receipt_coverage", True)
        comparison_receipts: list[dict[str, Any]] = []
        adjudication_receipts: list[str] = []
        resolution_receipts: list[str] = []
        consensus_total = disagreement_total = adjudicated_total = operator_total = advisor_total = accepted_total = (
            unresolved_total
        ) = 0
        final_ids: list[tuple[str, str]] = []
        source_offset = 0
        for lane, count in LANES.items():
            for index in range(1, count + 1):
                contents, grok_labels, gemini_labels, compare_receipt = _verify_compare_packet(
                    package, manifest, lane, index, custody_hash, manifest_hash
                )
                comparison_receipts.append(compare_receipt)
                evidence["provider_coverage"]["grok"]["packet_count"] += 1
                evidence["provider_coverage"]["grok"]["row_count"] += len(grok_labels)
                evidence["provider_coverage"]["gemini"]["packet_count"] += 1
                evidence["provider_coverage"]["gemini"]["row_count"] += len(gemini_labels)
                source_packet_ids = [_identity(row) for row in contents["rows"]]
                if source_ids[source_offset : source_offset + len(source_packet_ids)] != source_packet_ids:
                    raise Error("ordered_identity_denominator")
                source_offset += len(source_packet_ids)
                labels, unresolved, adj_receipt, _adj_unresolved = _verify_adjudication_packet(
                    package,
                    lane,
                    index,
                    len(source_packet_ids),
                    custody_hash,
                    manifest_hash,
                    compare_receipt,
                )
                adj_receipt_value, adj_receipt_raw = _read_json(
                    package / ADJUDICATION_ROOT / "final" / lane / f"receipt-{index:04d}.json"
                )
                del labels, unresolved
                adjudication_receipts.append(digest(adj_receipt_raw))
                del adj_receipt
                result, accepted, unresolved_count, resolution_count = _verify_resolution(
                    package, lane, index, source_packet_ids
                )
                final_ids.extend(_identity(label) for label in result["labels"])
                final_ids.extend(_identity(identity) for identity in result["unresolved"])
                consensus_total += compare_receipt["consensus_count"]
                disagreement_total += compare_receipt["disagreement_count"]
                adjudicated_total += adj_receipt_value["selection_count"] - adj_receipt_value["unresolved_count"]
                operator_total += result["operator_resolution_count"]
                advisor_total += result["designated_advisor_resolution_count"]
                accepted_total += accepted
                unresolved_total += unresolved_count
                if resolution_count:
                    paths = RES._paths(package, lane, index)
                    resolution_receipts.append(digest(_read_json(paths[2])[1]))
        gate(
            "operator_inspected_count",
            gates["operator_inspected_count"] and operator_inspected_count == operator_total,
        )
        gate("comparison_receipts", True)
        if len(comparison_receipts) != PACKET_COUNT:
            raise Error("comparison_receipts")
        comparison_batch_hash = _check_compare_batch(
            package,
            comparison_receipts,
            evidence["package"]["custody_receipt_raw_sha256"],
            evidence["package"]["label_manifest_raw_sha256"],
        )
        gate("comparison_batch_receipt", True)
        if evidence["provider_coverage"]["grok"] != {"packet_count": PACKET_COUNT, "row_count": ROW_COUNT} or evidence[
            "provider_coverage"
        ]["gemini"] != {"packet_count": PACKET_COUNT, "row_count": ROW_COUNT}:
            raise Error("provider_receipt_coverage")
        gate("adjudication_candidate_partition", True)
        gate("resolution_authorization", True)
        if len(final_ids) != ROW_COUNT or len(set(final_ids)) != ROW_COUNT or set(final_ids) != set(source_ids):
            raise Error("final_identity_union")
        final_union = digest(canonical(sorted(final_ids)))
        evidence["union"]["source_identity_count"] = len(set(source_ids))
        evidence["union"]["final_identity_count"] = len(set(final_ids))
        evidence["union"]["final_identity_union_commitment_sha256"] = final_union
        gate("final_identity_union", final_union == identity_union)
        if (
            consensus_total + disagreement_total != ROW_COUNT
            or accepted_total + unresolved_total != ROW_COUNT
            or consensus_total + adjudicated_total + operator_total + advisor_total + unresolved_total != ROW_COUNT
        ):
            raise Error("final_residual_zero")
        evidence["totals"] = {
            "consensus": consensus_total,
            "disagreement": disagreement_total,
            "adjudicated": adjudicated_total,
            "operator_resolved": operator_total,
            "advisor_resolved": advisor_total,
            "accepted": accepted_total,
            "unresolved": unresolved_total,
        }
        gate("final_residual_zero", unresolved_total == 0)
        evidence["upstream_receipts"] = {
            "compare_batch_receipt_sha256": comparison_batch_hash,
            "compare_packet_receipt_union_sha256": digest(
                canonical([item["receipt_sha256"] for item in comparison_receipts])
            ),
            "adjudication_packet_receipt_union_sha256": digest(canonical(adjudication_receipts)),
            "resolution_packet_receipt_union_sha256": digest(canonical(resolution_receipts)),
        }
        evidence["code_hashes"] = _code_hashes()
    except Error as exc:
        reasons.add(exc.code)
    except Exception:
        reasons.add("closure_validation_failed")
    evidence["reason_codes"] = sorted(reasons)
    evidence["complete"] = not reasons
    evidence["certified"] = evidence["complete"] and evidence["totals"]["unresolved"] == 0
    evidence["receipt_sha256"] = digest(canonical(evidence))
    _atomic(output, evidence)
    return evidence


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True, help="explicit 0700 operator-owned Cycle-006 package")
    parser.add_argument("--operator-inspected-count", type=int, required=True)
    parser.add_argument("--receipt", type=Path, help="optional 0600 receipt path directly under package/control")
    args = parser.parse_args(argv)
    result: dict[str, Any]
    try:
        package = args.package.resolve()
        receipt = (args.receipt or package / "control/certification-receipt-v2.json").resolve()
        if receipt.parent != (package / "control").resolve():
            raise Error("closure_validation_failed")
        result = verify(package, receipt, args.operator_inspected_count)
    except Error as exc:
        result = {"complete": False, "failure_code": exc.code, "text_free": True}
    except Exception:
        result = {"complete": False, "failure_code": "closure_validation_failed", "text_free": True}
    print(
        json.dumps(
            {
                "complete": result.get("complete", False),
                "certified": result.get("certified", False),
                "reason_count": len(result.get("reason_codes", [result.get("failure_code")]))
                if isinstance(result, dict)
                else 1,
                "text_free": True,
            },
            separators=(",", ":"),
        )
    )
    return 0 if result.get("complete") else 2


if __name__ == "__main__":
    raise SystemExit(main())
