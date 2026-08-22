#!/usr/bin/env python3
"""Deterministic full-denominator comparison for Cycle-006 v2 labels."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import stat
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CYCLE = "phase3-v2-1-evaluation-cycle-006"
CYCLE006_AMENDMENT_SHA256 = "524e6eb4f18d38f104413fb32f421ff73c3d80bc411d338a6d8a31fabc087474"
AMENDMENT_SHA256 = CYCLE006_AMENDMENT_SHA256
CUSTODY_SHA256 = "7047e8459433376f3b690cfc2f15e115d77a701e79afb0ef2db184b44ea14726"
SOURCE_MANIFEST_SHA256 = "b8d290ffe945a6cc5d36345cbf234ccf79a7df98cb4199ffad0b778cd2b69fab"
MANIFEST_SHA256 = SOURCE_MANIFEST_SHA256
ORDERED_IDENTITY_COMMITMENT_SHA256 = "331fd7fbc42e43cb3c218d9c2b790df060c0a553ab7c3a7b3b557f9f2bc3c419"
LANES = {"clean_label": 40, "residual_label": 164}
ROW_COUNT = 10159
PACKET_COUNT = 204
GROK = {
    "root": "label-output-grok-cycle006-v2",
    "exact_model": "grok-4.5",
    "model_family": "xai",
    "harness": "native_grok",
}
GEMINI = {
    "root": "label-output-gemini-cycle006-v2",
    "exact_model": "Gemini 3.6 Flash (High)",
    "model_family": "google",
    "harness": "agy",
}
OUTPUT = "dual-label-output-cycle006-v2"
OUTPUT_ROOT = OUTPUT
CHUNK_SIZE = 20


def _load_source() -> Any:
    path = ROOT / "batch_state/phase3-run-cycle006-grok-label-provider-batch-v2.py"
    spec = importlib.util.spec_from_file_location("cycle006_v2_grok_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("source validator unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SOURCE = _load_source()
Error = SOURCE.Error
Invalid = SOURCE.Invalid
atomic = SOURCE.atomic
canonical = SOURCE.canonical
digest = SOURCE.digest
packet = SOURCE.packet
validate = SOURCE.validate
pairs = SOURCE.pairs


def _regular(path: Path, mode: int | None = None) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        del exc
        raise Error("label_count_or_envelope_drift") from None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise Error("label_count_or_envelope_drift")
    if mode is not None and stat.S_IMODE(info.st_mode) != mode:
        raise Error("label_count_or_envelope_drift")


def _directory(path: Path, mode: int | None = None) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        del exc
        raise Error("label_count_or_envelope_drift") from None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise Error("label_count_or_envelope_drift")
    if mode is not None and stat.S_IMODE(info.st_mode) != mode:
        raise Error("label_count_or_envelope_drift")


def read(path: Path, label: str = "sealed value") -> Any:
    try:
        _regular(path, 0o600)
        return json.loads(path.read_bytes().decode("utf-8", "strict"), object_pairs_hook=pairs)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, Invalid, Error) as exc:
        del label, exc
        raise Error("label_count_or_envelope_drift") from None


def _manifest(package: Path) -> dict[str, Any]:
    _directory(package, 0o700)
    value = read(package / "label-manifest.json", "manifest")
    custody_hash = digest((package / "custody-receipt.json").read_bytes())
    SOURCE._custody(package)
    if not isinstance(value, dict):
        raise Error("label_count_or_envelope_drift")
    if (
        value.get("schema_version") != "phase3_cycle006_label_manifest_v2"
        or value.get("evaluation_cycle_id") != CYCLE
        or value.get("source_evaluation_cycle_id") != "phase3-v2-1-evaluation-cycle-005"
        or value.get("custody_receipt_raw_sha256") != custody_hash
        or value.get("source_label_manifest_raw_sha256") != SOURCE_MANIFEST_SHA256
        or value.get("source_custody_receipt_raw_sha256") != SOURCE.SOURCE_CUSTODY_SHA256
        or value.get("cycle006_amendment_raw_sha256") != AMENDMENT_SHA256
        or value.get("packet_count") != PACKET_COUNT
        or value.get("row_count") != ROW_COUNT
        or value.get("ordered_identity_commitment_sha256") != ORDERED_IDENTITY_COMMITMENT_SHA256
        or value.get("text_free") is not True
        or not isinstance(value.get("packets"), list)
        or len(value["packets"]) != PACKET_COUNT
        or value.get("receipt_sha256")
        != digest(canonical({key: item for key, item in value.items() if key != "receipt_sha256"}))
    ):
        raise Error("label_count_or_envelope_drift")
    return value


def manifest(package: Path) -> dict[str, Any]:
    return _manifest(package)


def _manifest_packet(
    manifest_value: dict[str, Any], lane: str, index: int, path: Path, contents: dict[str, Any]
) -> None:
    matches = [
        item
        for item in manifest_value["packets"]
        if isinstance(item, dict) and item.get("lane") == lane and item.get("packet_index") == index
    ]
    expected = {
        "lane": lane,
        "packet_index": index,
        "canonical_basename": path.name,
        "row_count": contents["row_count"],
        "raw_sha256": digest(path.read_bytes()),
        "packet_identity_set_sha256": contents["packet_identity_set_sha256"],
    }
    if len(matches) != 1 or matches[0] != expected:
        raise Error("identity_or_order_drift")


def _prompt_binding(package: Path, lane: str, provider: dict[str, str]) -> tuple[Path, str, str]:
    """Resolve a provider-specific prompt from the sealed package bindings."""
    manifest_value = _manifest(package)
    bindings = manifest_value.get("prompt_bindings")
    if not isinstance(bindings, list):
        raise Error("label_count_or_envelope_drift")
    provider_name = "grok" if provider is GROK else "gemini"
    matches = [
        item
        for item in bindings
        if isinstance(item, dict) and item.get("lane") == lane and item.get("provider") == provider_name
    ]
    if len(matches) != 1:
        raise Error("label_count_or_envelope_drift")
    binding = matches[0]
    relative, expected_hash = binding.get("path"), binding.get("sha256")
    if (
        not isinstance(relative, str)
        or Path(relative).is_absolute()
        or ".." in Path(relative).parts
        or not isinstance(expected_hash, str)
    ):
        raise Error("label_count_or_envelope_drift")
    path = package / relative
    SOURCE._regular(path, 0o600)
    custody = SOURCE.read(package / "custody-receipt.json", "custody receipt")
    prompt_hashes = manifest_value.get("prompt_sha256s")
    if (
        not isinstance(custody, dict)
        or custody.get("prompt_bindings") != bindings
        or custody.get("prompt_sha256s") != prompt_hashes
        or not isinstance(prompt_hashes, dict)
        or prompt_hashes.get(relative) != expected_hash
        or digest(path.read_bytes()) != expected_hash
    ):
        raise Error("label_count_or_envelope_drift")
    return path, relative, expected_hash


def _packet(package: Path, lane: str, index: int, manifest_value: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    try:
        path, contents = packet(package, lane, index)
    except Exception as exc:
        del exc
        raise Error("identity_or_order_drift") from None
    _manifest_packet(manifest_value, lane, index, path, contents)
    return path, contents


def _receipt_common(
    provider: dict[str, str], package: Path, lane: str, index: int, contents: dict[str, Any], packet_path: Path
) -> tuple[dict[str, Any], Path, Path, dict[str, Any]]:
    out = package / provider["root"] / lane
    _directory(package / provider["root"], 0o700)
    _directory(out, 0o700)
    labels_path = out / f"labels-{index:04d}.json"
    receipt_path = out / f"receipt-{index:04d}.json"
    _regular(labels_path, 0o600)
    _regular(receipt_path, 0o600)
    value = read(receipt_path, "provider receipt")
    if not isinstance(value, dict):
        raise Error("label_count_or_envelope_drift")
    _prompt_path, prompt_name, prompt_hash = _prompt_binding(package, lane, provider)
    common = {
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()),
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": digest((package / "label-manifest.json").read_bytes()),
        "lane": lane,
        "packet_index": index,
        "row_count": contents["row_count"],
        "packet_raw_sha256": digest(packet_path.read_bytes()),
        "packet_identity_set_sha256": contents["packet_identity_set_sha256"],
        "labels_sha256": digest(labels_path.read_bytes()),
        "exact_model": provider["exact_model"],
        "model_family": provider["model_family"],
        "harness": provider["harness"],
        "prompt_path": prompt_name,
        "prompt_sha256": prompt_hash,
        "text_free": True,
    }
    return value, labels_path, receipt_path, common


def _verify_grok(
    package: Path, lane: str, index: int, contents: dict[str, Any], packet_path: Path
) -> list[dict[str, Any]]:
    value, labels_path, _receipt_path, common = _receipt_common(GROK, package, lane, index, contents, packet_path)
    out = package / GROK["root"] / lane
    raw_manifest_path = out / f"raw-manifest-{index:04d}.json"
    raw_path = out / f"raw-{index:04d}.raw"
    _regular(raw_manifest_path, 0o600)
    _regular(raw_path, 0o600)
    raw_manifest = read(raw_manifest_path, "grok raw manifest")
    expected_raw = {
        "schema_version": "phase3_cycle006_grok_raw_manifest_v2",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "lane": lane,
        "packet_index": index,
        "row_count": contents["row_count"],
        "packet_raw_sha256": common["packet_raw_sha256"],
        "packet_identity_set_sha256": contents["packet_identity_set_sha256"],
        "response_raw_sha256": digest(raw_path.read_bytes()),
        "text_free": True,
    }
    if (
        not isinstance(raw_manifest, dict)
        or set(raw_manifest) != set(expected_raw) | {"manifest_sha256"}
        or any(raw_manifest.get(key) != item for key, item in expected_raw.items())
        or raw_manifest.get("manifest_sha256") != digest(canonical(expected_raw))
    ):
        raise Error("label_count_or_envelope_drift")
    expected = {
        "schema_version": "phase3_cycle006_grok_packet_label_receipt_v2",
        **common,
        "raw_manifest_sha256": digest(raw_manifest_path.read_bytes()),
        "response_raw_sha256": digest(raw_path.read_bytes()),
        "attempt_count": value.get("attempt_count"),
    }
    if (
        value.get("receipt_sha256")
        != digest(canonical({key: item for key, item in value.items() if key != "receipt_sha256"}))
        or set(value) != set(expected) | {"receipt_sha256"}
        or value.get("attempt_count") not in {1, 2}
        or any(value.get(key) != item for key, item in expected.items())
    ):
        raise Error("label_count_or_envelope_drift")
    labels = read(labels_path, "grok labels")
    if canonical(labels) != labels_path.read_bytes():
        raise Error("label_count_or_envelope_drift")
    try:
        validate(lane, contents, canonical(labels))
    except Invalid as exc:
        raise Error(exc.failure_code) from None
    return labels["labels"]


def _verify_gemini(
    package: Path, lane: str, index: int, contents: dict[str, Any], packet_path: Path
) -> list[dict[str, Any]]:
    value, labels_path, _receipt_path, common = _receipt_common(GEMINI, package, lane, index, contents, packet_path)
    out = package / GEMINI["root"] / lane
    raw_manifest_path = out / f"raw-manifest-{index:04d}.json"
    _regular(raw_manifest_path, 0o600)
    raw_manifest = read(raw_manifest_path, "gemini raw manifest")
    chunk_count = (contents["row_count"] + CHUNK_SIZE - 1) // CHUNK_SIZE
    if (
        not isinstance(raw_manifest, dict)
        or set(raw_manifest)
        != {
            "schema_version",
            "evaluation_cycle_id",
            "amendment_sha256",
            "lane",
            "packet_index",
            "chunk_count",
            "chunks",
            "text_free",
            "manifest_sha256",
        }
        or raw_manifest.get("schema_version") != "phase3_cycle006_gemini_raw_manifest_v2"
        or raw_manifest.get("evaluation_cycle_id") != CYCLE
        or raw_manifest.get("amendment_sha256") != AMENDMENT_SHA256
        or raw_manifest.get("lane") != lane
        or raw_manifest.get("packet_index") != index
        or raw_manifest.get("chunk_count") != chunk_count
        or not isinstance(raw_manifest.get("chunks"), list)
        or len(raw_manifest["chunks"]) != chunk_count
        or raw_manifest.get("text_free") is not True
        or raw_manifest.get("manifest_sha256")
        != digest(canonical({key: item for key, item in raw_manifest.items() if key != "manifest_sha256"}))
    ):
        raise Error("label_count_or_envelope_drift")
    chunk_dir = out / "chunks" / f"packet-{index:04d}"
    _directory(out / "chunks", 0o700)
    _directory(chunk_dir, 0o700)
    chunk_labels: list[dict[str, Any]] = []
    for chunk_index, entry in enumerate(raw_manifest["chunks"], 1):
        start = (chunk_index - 1) * CHUNK_SIZE
        rows = contents["rows"][start : start + CHUNK_SIZE]
        count = len(rows)
        if (
            not isinstance(entry, dict)
            or set(entry)
            != {"chunk_index", "row_count", "response_raw_sha256", "labels_sha256", "chunk_receipt_sha256"}
            or entry.get("chunk_index") != chunk_index
            or entry.get("row_count") != count
        ):
            raise Error("label_count_or_envelope_drift")
        labels_chunk = chunk_dir / f"labels-chunk-{chunk_index:02d}.json"
        raw_chunk = chunk_dir / f"raw-chunk-{chunk_index:02d}.raw"
        receipt_chunk = chunk_dir / f"receipt-chunk-{chunk_index:02d}.json"
        _regular(labels_chunk, 0o600)
        _regular(raw_chunk, 0o600)
        _regular(receipt_chunk, 0o600)
        chunk_receipt = read(receipt_chunk, "gemini chunk receipt")
        expected_chunk = {
            "schema_version": "phase3_cycle006_gemini_chunk_receipt_v2",
            "evaluation_cycle_id": CYCLE,
            "amendment_sha256": AMENDMENT_SHA256,
            "lane": lane,
            "packet_index": index,
            "chunk_index": chunk_index,
            "chunk_count": chunk_count,
            "row_count": count,
            "chunk_identity_set_sha256": digest(
                canonical(sorted((row["unit_id"], row["unit_sha256"]) for row in rows))
            ),
            "response_raw_sha256": digest(raw_chunk.read_bytes()),
            "labels_sha256": digest(labels_chunk.read_bytes()),
            "attempt_count": chunk_receipt.get("attempt_count") if isinstance(chunk_receipt, dict) else None,
            "exact_model": GEMINI["exact_model"],
            "model_family": GEMINI["model_family"],
            "harness": GEMINI["harness"],
            "text_free": True,
        }
        if (
            not isinstance(chunk_receipt, dict)
            or set(chunk_receipt) != set(expected_chunk) | {"receipt_sha256"}
            or chunk_receipt.get("receipt_sha256")
            != digest(canonical({key: item for key, item in chunk_receipt.items() if key != "receipt_sha256"}))
            or chunk_receipt.get("attempt_count") not in {1, 2}
            or any(chunk_receipt.get(key) != item for key, item in expected_chunk.items())
            or entry.get("response_raw_sha256") != expected_chunk["response_raw_sha256"]
            or entry.get("labels_sha256") != expected_chunk["labels_sha256"]
            or entry.get("chunk_receipt_sha256") != chunk_receipt["receipt_sha256"]
        ):
            raise Error("label_count_or_envelope_drift")
        labels = read(labels_chunk, "gemini chunk labels")
        try:
            validate(lane, {"rows": rows}, canonical(labels))
        except Invalid as exc:
            raise Error(exc.failure_code) from None
        chunk_labels.extend(labels["labels"])
    expected = {
        "schema_version": "phase3_cycle006_gemini_packet_label_receipt_v2",
        **common,
        "raw_manifest_sha256": digest(raw_manifest_path.read_bytes()),
        "chunk_count": chunk_count,
    }
    if (
        value.get("receipt_sha256")
        != digest(canonical({key: item for key, item in value.items() if key != "receipt_sha256"}))
        or set(value) != set(expected) | {"receipt_sha256"}
        or any(value.get(key) != item for key, item in expected.items())
    ):
        raise Error("label_count_or_envelope_drift")
    labels = read(labels_path, "gemini labels")
    if canonical(labels) != labels_path.read_bytes() or labels.get("labels") != chunk_labels:
        raise Error("identity_or_order_drift")
    try:
        validate(lane, contents, canonical(labels))
    except Invalid as exc:
        raise Error(exc.failure_code) from None
    return labels["labels"]


def _provider_names(package: Path, provider: dict[str, str], lane: str, count: int) -> tuple[set[str], set[str]]:
    out = package / provider["root"] / lane
    _directory(out, 0o700)
    names = {
        path.name
        for path in out.iterdir()
        if (path.is_file() or path.is_symlink())
        and path.name.startswith(("labels-", "receipt-", "raw-manifest-", "raw-"))
    }
    expected = {
        *(f"labels-{index:04d}.json" for index in range(1, count + 1)),
        *(f"receipt-{index:04d}.json" for index in range(1, count + 1)),
        *(f"raw-manifest-{index:04d}.json" for index in range(1, count + 1)),
    }
    if provider is GROK:
        expected |= {f"raw-{index:04d}.raw" for index in range(1, count + 1)}
    return names, expected


def semantic(label: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in label.items() if key not in {"unit_id", "unit_sha256"}}


def inputs(
    package: Path,
    lane: str,
    index: int,
    manifest_value: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    value = manifest_value or _manifest(package)
    packet_path, contents = _packet(package, lane, index, value)
    grok = _verify_grok(package, lane, index, contents, packet_path)
    gemini = _verify_gemini(package, lane, index, contents, packet_path)
    if len(grok) != len(gemini) or len(grok) != contents["row_count"]:
        raise Error("label_count_or_envelope_drift")
    return contents, grok, gemini


def compare_inputs(
    package: Path, lane: str, index: int
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    return inputs(package, lane, index)


def _compare_body(
    package: Path,
    lane: str,
    index: int,
    prepared: tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    value = _manifest(package)
    contents, grok, gemini = prepared or inputs(package, lane, index, value)
    consensus: list[dict[str, Any]] = []
    disagreements: list[dict[str, Any]] = []
    for source, left, right in zip(contents["rows"], grok, gemini, strict=True):
        identity = (source["unit_id"], source["unit_sha256"])
        if (left.get("unit_id"), left.get("unit_sha256")) != identity or (
            right.get("unit_id"),
            right.get("unit_sha256"),
        ) != identity:
            raise Error("identity_or_order_drift")
        if semantic(left) == semantic(right):
            consensus.append(left)
        else:
            disagreements.append(
                {
                    "source_row": source,
                    "grok_label": left,
                    "gemini_label": right,
                }
            )
    out = package / OUTPUT / lane
    out.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(out.parent, 0o700)
    consensus_hash = atomic(out / f"consensus-{index:04d}.json", {"labels": consensus})
    disagreements_hash = atomic(out / f"disagreements-{index:04d}.json", {"records": disagreements})
    body = {
        "schema_version": "phase3_cycle006_dual_label_packet_receipt_v2",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()),
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": digest((package / "label-manifest.json").read_bytes()),
        "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
        "lane": lane,
        "packet_index": index,
        "row_count": contents["row_count"],
        "packet_identity_set_sha256": contents["packet_identity_set_sha256"],
        "grok": {key: GROK[key] for key in ("exact_model", "model_family", "harness")},
        "gemini": {key: GEMINI[key] for key in ("exact_model", "model_family", "harness")},
        "consensus_count": len(consensus),
        "disagreement_count": len(disagreements),
        "consensus_sha256": consensus_hash,
        "disagreements_sha256": disagreements_hash,
        "silent_selection": False,
        "text_free": True,
    }
    body["receipt_sha256"] = digest(canonical(body))
    atomic(out / f"receipt-{index:04d}.json", body)
    return body


def _verify_existing_compare(
    package: Path,
    lane: str,
    index: int,
    prepared: tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]],
) -> dict[str, Any] | None:
    """Verify a complete immutable packet seal before allowing --all to skip it."""
    out = package / OUTPUT / lane
    paths = (
        out / f"consensus-{index:04d}.json",
        out / f"disagreements-{index:04d}.json",
        out / f"receipt-{index:04d}.json",
    )
    present = [path.exists() or path.is_symlink() for path in paths]
    if not any(present):
        return None
    if not all(present):
        raise Error("label_count_or_envelope_drift")
    for path in paths:
        _regular(path, 0o600)
    contents, grok, gemini = prepared
    consensus = read(paths[0], "consensus")
    disagreements = read(paths[1], "disagreements")
    receipt = read(paths[2], "comparison receipt")
    expected_consensus: list[dict[str, Any]] = []
    expected_disagreements: list[dict[str, Any]] = []
    for source, left, right in zip(contents["rows"], grok, gemini, strict=True):
        if semantic(left) == semantic(right):
            expected_consensus.append(left)
        else:
            expected_disagreements.append({"source_row": source, "grok_label": left, "gemini_label": right})
    if (
        not isinstance(consensus, dict)
        or set(consensus) != {"labels"}
        or consensus["labels"] != expected_consensus
        or canonical(consensus) != paths[0].read_bytes()
        or not isinstance(disagreements, dict)
        or set(disagreements) != {"records"}
        or disagreements["records"] != expected_disagreements
        or canonical(disagreements) != paths[1].read_bytes()
    ):
        raise Error("label_count_or_envelope_drift")
    expected = {
        "schema_version": "phase3_cycle006_dual_label_packet_receipt_v2",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()),
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": digest((package / "label-manifest.json").read_bytes()),
        "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
        "lane": lane,
        "packet_index": index,
        "row_count": contents["row_count"],
        "packet_identity_set_sha256": contents["packet_identity_set_sha256"],
        "grok": {key: GROK[key] for key in ("exact_model", "model_family", "harness")},
        "gemini": {key: GEMINI[key] for key in ("exact_model", "model_family", "harness")},
        "consensus_count": len(expected_consensus),
        "disagreement_count": len(expected_disagreements),
        "consensus_sha256": digest(paths[0].read_bytes()),
        "disagreements_sha256": digest(paths[1].read_bytes()),
        "silent_selection": False,
        "text_free": True,
    }
    if (
        not isinstance(receipt, dict)
        or set(receipt) != set(expected) | {"receipt_sha256"}
        or any(receipt.get(key) != value for key, value in expected.items())
        or receipt.get("receipt_sha256") != digest(canonical(expected))
        or canonical(receipt) != paths[2].read_bytes()
    ):
        raise Error("label_count_or_envelope_drift")
    return receipt


def _existing_compare(
    package: Path,
    lane: str,
    index: int,
    prepared: tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]] | None = None,
) -> dict[str, Any] | None:
    if prepared is None:
        prepared = inputs(package, lane, index)
    return _verify_existing_compare(package, lane, index, prepared)


def compare(
    package: Path,
    lane: str,
    index: int,
    prepared: tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    if lane not in LANES or not 1 <= index <= LANES[lane]:
        raise Error("label_count_or_envelope_drift")
    existing = _existing_compare(package, lane, index, prepared or inputs(package, lane, index))
    if existing is not None:
        return existing
    return _compare_body(package, lane, index, prepared)


def compare_all(package: Path) -> dict[str, Any]:
    value = _manifest(package)
    expected_packets = {(lane, index) for lane, count in LANES.items() for index in range(1, count + 1)}
    records = {(item.get("lane"), item.get("packet_index")) for item in value["packets"] if isinstance(item, dict)}
    if records != expected_packets:
        raise Error("identity_or_order_drift")
    prepared: dict[tuple[str, int], tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]] = {}
    for lane, count in LANES.items():
        packet_dir = package / lane
        _directory(packet_dir, 0o700)
        packet_names = {path.name for path in packet_dir.iterdir() if path.is_file() or path.is_symlink()}
        expected_names = {f"packet-{index:04d}.json" for index in range(1, count + 1)}
        if packet_names != expected_names:
            raise Error("identity_or_order_drift")
        for provider in (GROK, GEMINI):
            names, expected = _provider_names(package, provider, lane, count)
            if names != expected:
                raise Error("label_count_or_envelope_drift")
        for index in range(1, count + 1):
            prepared[(lane, index)] = inputs(package, lane, index, value)
    receipts: list[dict[str, Any]] = []
    for lane, index in sorted(expected_packets):
        packet_prepared = prepared[(lane, index)]
        existing = _verify_existing_compare(package, lane, index, packet_prepared)
        receipts.append(existing if existing is not None else _compare_body(package, lane, index, packet_prepared))
    if sum(item["row_count"] for item in receipts) != ROW_COUNT:
        raise Error("label_count_or_envelope_drift")
    body = {
        "schema_version": "phase3_cycle006_dual_label_batch_receipt_v2",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()),
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": digest((package / "label-manifest.json").read_bytes()),
        "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
        "packet_count": len(receipts),
        "row_count": sum(item["row_count"] for item in receipts),
        "consensus_count": sum(item["consensus_count"] for item in receipts),
        "disagreement_count": sum(item["disagreement_count"] for item in receipts),
        "packet_receipt_union_sha256": digest(canonical([item["receipt_sha256"] for item in receipts])),
        "grok": {key: GROK[key] for key in ("exact_model", "model_family", "harness")},
        "gemini": {key: GEMINI[key] for key in ("exact_model", "model_family", "harness")},
        "silent_selection": False,
        "text_free": True,
    }
    batch_path = package / OUTPUT / "batch-receipt.json"
    if batch_path.exists() or batch_path.is_symlink():
        _regular(batch_path, 0o600)
        existing_batch = read(batch_path, "comparison batch receipt")
        if (
            not isinstance(existing_batch, dict)
            or set(existing_batch) != set(body) | {"receipt_sha256"}
            or any(existing_batch.get(key) != value for key, value in body.items())
            or existing_batch.get("receipt_sha256") != digest(canonical(body))
            or canonical(existing_batch) != batch_path.read_bytes()
        ):
            raise Error("label_count_or_envelope_drift")
        return existing_batch
    body["receipt_sha256"] = digest(canonical(body))
    atomic(batch_path, body)
    return body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--lane", choices=tuple(LANES))
    parser.add_argument("--packet-index", type=int)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.all:
            result = compare_all(args.package)
        elif args.lane is not None and args.packet_index is not None:
            result = compare(args.package, args.lane, args.packet_index)
        else:
            raise Error("label_count_or_envelope_drift")
    except Error as exc:
        result = {"ok": False, "failure_code": exc.failure_code, "text_free": True}
    except Exception:
        result = {"ok": False, "failure_code": "label_count_or_envelope_drift", "text_free": True}
    else:
        result = {"ok": True, **result}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
