#!/usr/bin/env python3
"""Produce and verify a text-free receipt voiding Phase 3 cycle 001.

The verifier reads private execution artifacts only to validate their custody
hashes and packet cardinalities.  It never prints private paths or bodies and
only writes a receipt to an explicitly supplied public output path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "data/projects/open_model_data/contracts/phase3_cycle_void_receipt_v1.schema.json"
CYCLE_ID = "phase3-v2-1-evaluation-cycle-001"
EXPECTED_INDICES = tuple((*range(1, 21), 24, 45, 776))
EXPECTED_AUTHOR_PACKET_COUNT = 918
EXPECTED_COMPLETED_REFERENCED_UNIT_COUNT = 947
EXPECTED_HELDOUT_LABELS = 2_000
PRIVATE_FILE_MODES = frozenset((0o400, 0o600))


class CycleVoidReceiptError(ValueError):
    """The private cycle-001 execution state is unsafe or not the expected void state."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CycleVoidReceiptError(message)


def _relative(root: Path, path: Path, label: str) -> Path:
    try:
        return path.relative_to(root)
    except ValueError as exc:
        raise CycleVoidReceiptError(f"{label} escapes private root") from exc


def _reject_symlink_components(root: Path, path: Path, label: str) -> None:
    relative = _relative(root, path, label)
    current = root
    require(not current.is_symlink(), "private root is a symlink")
    for component in relative.parts:
        current = current / component
        require(not current.is_symlink(), f"{label} contains a symlink")


def _private_root(path: Path) -> Path:
    require(path.is_dir() and not path.is_symlink(), "private root is not a real directory")
    require(stat.S_IMODE(path.stat().st_mode) == 0o700, "private root mode must be 0700")
    return path.resolve()


def _regular(root: Path, path: Path, label: str) -> None:
    _reject_symlink_components(root, path, label)
    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        raise CycleVoidReceiptError(f"missing {label}") from exc
    require(stat.S_ISREG(mode), f"{label} is not a regular file")
    require(stat.S_IMODE(mode) in PRIVATE_FILE_MODES, f"{label} mode must be 0400 or 0600")


def _read_json(root: Path, path: Path, label: str) -> dict[str, Any]:
    _regular(root, path, label)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CycleVoidReceiptError(f"cannot read {label}") from exc
    require(isinstance(value, dict), f"{label} must be an object")
    return value


def _assert_exact_directory(
    root: Path, directory: Path, expected_names: set[str], label: str
) -> None:
    _reject_symlink_components(root, directory, label)
    require(directory.is_dir() and not directory.is_symlink(), f"{label} is not a directory")
    require(stat.S_IMODE(directory.stat().st_mode) == 0o700, f"{label} mode must be 0700")
    names = {entry.name for entry in directory.iterdir()}
    require(names == expected_names, f"unexpected or missing {label} items")
    for entry in directory.iterdir():
        _regular(root, entry, label)


def _manifest(root: Path) -> dict[str, Any]:
    path = root / "manifest.json"
    manifest = _read_json(root, path, "manifest")
    require(manifest.get("schema_version") == "phase3_source_production_manifest_v1", "manifest schema drift")
    require(manifest.get("manifest_sha256") == sha256_value({key: value for key, value in manifest.items() if key != "manifest_sha256"}), "manifest self-hash drift")
    bindings = manifest.get("bindings")
    denominator = manifest.get("denominator")
    require(isinstance(bindings, Mapping) and bindings.get("evaluation_cycle_id") == CYCLE_ID, "manifest cycle drift")
    require(isinstance(denominator, Mapping) and denominator.get("heldout_labels") == EXPECTED_HELDOUT_LABELS, "manifest heldout-label denominator drift")
    entries = manifest.get("author_packets")
    require(
        isinstance(entries, list)
        and manifest.get("author_packet_count") == EXPECTED_AUTHOR_PACKET_COUNT
        and len(entries) == EXPECTED_AUTHOR_PACKET_COUNT,
        "author packet count drift",
    )
    expected_indices = list(range(1, EXPECTED_AUTHOR_PACKET_COUNT + 1))
    require([entry.get("packet_index") if isinstance(entry, Mapping) else None for entry in entries] == expected_indices, "manifest packet index order drift")
    require(all(isinstance(entry, Mapping) for entry in entries), "manifest packet entries drift")
    return manifest


def _expected_paths(root: Path, index: int) -> dict[str, Path]:
    stem = f"{index:05d}"
    return {
        "record": root / "author" / "records" / f"{stem}.json",
        "raw": root / "author" / "raw" / f"{stem}.raw",
        "incoming": root / "author" / "incoming" / f"{stem}.raw",
        "invocation": root / "author" / "invocations" / f"{stem}.json",
        "response": root / "author" / "responses" / f"{stem}.json",
        "stdout": root / "author" / "provider-logs" / f"{stem}.stdout",
        "stderr": root / "author" / "provider-logs" / f"{stem}.stderr",
    }


def _verify_author_tree(root: Path, manifest: Mapping[str, Any]) -> None:
    author = root / "author"
    _reject_symlink_components(root, author, "author root")
    require(author.is_dir() and not author.is_symlink(), "author root is not a directory")
    require(stat.S_IMODE(author.stat().st_mode) == 0o700, "author root mode must be 0700")
    expected_dirs = {"packets", "records", "raw", "incoming", "invocations", "responses", "provider-logs"}
    require({entry.name for entry in author.iterdir()} == expected_dirs, "unexpected author-root items")
    expected_json = {f"{index:05d}.json" for index in EXPECTED_INDICES}
    expected_raw = {f"{index:05d}.raw" for index in EXPECTED_INDICES}
    _assert_exact_directory(root, author / "records", expected_json, "author records")
    _assert_exact_directory(root, author / "raw", expected_raw, "author raw")
    _assert_exact_directory(root, author / "incoming", expected_raw, "author incoming")
    _assert_exact_directory(root, author / "invocations", expected_json, "author invocations")
    _assert_exact_directory(root, author / "responses", expected_json, "author responses")
    expected_logs = {
        f"{index:05d}.{suffix}" for index in EXPECTED_INDICES for suffix in ("stdout", "stderr")
    }
    _assert_exact_directory(root, author / "provider-logs", expected_logs, "author provider logs")
    packets = author / "packets"
    _reject_symlink_components(root, packets, "author packets")
    require(packets.is_dir() and not packets.is_symlink(), "author packets is not a directory")
    require(stat.S_IMODE(packets.stat().st_mode) == 0o700, "author packets mode must be 0700")
    entries = manifest["author_packets"]
    expected_packets = {f"{index:05d}.json" for index in range(1, EXPECTED_AUTHOR_PACKET_COUNT + 1)}
    _assert_exact_directory(root, packets, expected_packets, "author packets")
    for entry in entries:
        require(isinstance(entry, Mapping), "manifest packet entry is not an object")
        relative = entry.get("relative_path")
        require(isinstance(relative, str), "manifest packet path is missing")
        packet = root / relative
        _regular(root, packet, "author packet")
        require(entry.get("packet_sha256") == sha256_file(packet), "packet hash drift")


def _packet_entry(manifest: Mapping[str, Any], index: int) -> Mapping[str, Any]:
    entries = manifest["author_packets"]
    entry = entries[index - 1]
    require(isinstance(entry, Mapping), "manifest packet entry is not an object")
    return entry


def _verify_packet_reference(root: Path, manifest: Mapping[str, Any], index: int) -> Mapping[str, Any]:
    entry = _packet_entry(manifest, index)
    relative = entry.get("relative_path")
    require(isinstance(relative, str) and relative == f"author/packets/{index:05d}.json", "packet path drift")
    packet = root / relative
    _regular(root, packet, "author packet")
    require(entry.get("packet_sha256") == sha256_file(packet), "packet hash drift")
    value = _read_json(root, packet, "author packet")
    items = value.get("items")
    require(isinstance(items, list) and len(items) == entry.get("item_count"), "packet item count drift")
    return entry


def _verify_chain(root: Path, manifest: Mapping[str, Any], index: int) -> dict[str, str]:
    paths = _expected_paths(root, index)
    for label, path in paths.items():
        _regular(root, path, f"author {label}")
    entry = _verify_packet_reference(root, manifest, index)
    record = _read_json(root, paths["record"], "author record")
    invocation = _read_json(root, paths["invocation"], "author invocation")
    require(
        record.get("schema_version") == "phase3_source_production_author_transport_v1"
        and record.get("packet_index") == index
        and record.get("packet_id") == entry.get("packet_id")
        and record.get("packet_sha256") == entry.get("packet_sha256"),
        "author record packet binding drift",
    )
    raw_sha256 = sha256_file(paths["raw"])
    incoming_sha256 = sha256_file(paths["incoming"])
    response_sha256 = sha256_file(paths["response"])
    invocation_sha256 = sha256_file(paths["invocation"])
    stdout_sha256 = sha256_file(paths["stdout"])
    stderr_sha256 = sha256_file(paths["stderr"])
    require(
        record.get("raw_sha256") == raw_sha256
        and record.get("response_sha256") == response_sha256
        and record.get("invocation_receipt_sha256") == invocation_sha256,
        "author record custody hash drift",
    )
    require(
        incoming_sha256 == raw_sha256
        and invocation.get("schema_version") == "phase3_source_production_provider_invocation_v1"
        and invocation.get("packet_id") == entry.get("packet_id")
        and invocation.get("raw_sha256") == raw_sha256
        and invocation.get("stdout_sha256") == stdout_sha256
        and invocation.get("stderr_sha256") == stderr_sha256
        and invocation.get("exit_code") == 0,
        "author invocation custody drift",
    )
    return {
        "packet_sha256": str(entry["packet_sha256"]),
        "record_sha256": sha256_file(paths["record"]),
        "raw_sha256": raw_sha256,
        "incoming_sha256": incoming_sha256,
        "invocation_sha256": invocation_sha256,
        "response_sha256": response_sha256,
        "stdout_sha256": stdout_sha256,
        "stderr_sha256": stderr_sha256,
    }


def _assert_no_downstream_ingest(root: Path) -> None:
    forbidden = {
        "review",
        "review-manifest.json",
        "assembled",
        "dispositions",
        "disposition-input.json",
        "public-receipt.json",
    }
    names = {entry.name for entry in root.iterdir()}
    require(not names & forbidden, "downstream review, assembly, or disposition ingest exists")
    expected = {"manifest.json", "author", "deterministic-partition-dispositions.jsonl"}
    require(names == expected, "unexpected private-root items")
    _regular(root, root / "deterministic-partition-dispositions.jsonl", "deterministic partition dispositions")


def build_receipt(private_root: Path) -> dict[str, Any]:
    """Verify the private root and return an in-memory, text-free public receipt."""
    root = _private_root(private_root)
    _assert_no_downstream_ingest(root)
    manifest = _manifest(root)
    _verify_author_tree(root, manifest)
    chains = [_verify_chain(root, manifest, index) for index in EXPECTED_INDICES]
    completed_unit_count = sum(_packet_entry(manifest, index)["item_count"] for index in EXPECTED_INDICES)
    require(completed_unit_count == EXPECTED_COMPLETED_REFERENCED_UNIT_COUNT, "completed referenced-unit count drift")
    chain_sha256 = sha256_value(chains)
    receipt: dict[str, Any] = {
        "schema_version": "phase3_cycle_void_receipt_v1",
        "text_free": True,
        "evaluation_cycle_id": CYCLE_ID,
        "voided": True,
        "void_reason": "cycle001_incomplete_author_execution_before_downstream_ingest",
        "manifest_sha256": sha256_file(root / "manifest.json"),
        "heldout_labels": EXPECTED_HELDOUT_LABELS,
        "completed_packet_indices": list(EXPECTED_INDICES),
        "completed_packet_count": len(EXPECTED_INDICES),
        "author_packet_count": EXPECTED_AUTHOR_PACKET_COUNT,
        "completed_referenced_unit_count": EXPECTED_COMPLETED_REFERENCED_UNIT_COUNT,
        "execution_chain_sha256": chain_sha256,
        "downstream_ingest": {
            "review": False,
            "assembly": False,
            "disposition": False,
            "author_ingest_not_asserted": True,
        },
    }
    receipt["receipt_sha256"] = hashlib.sha256((canonical_json(receipt) + "\n").encode("utf-8")).hexdigest()
    return receipt


def verify_receipt_value(value: Mapping[str, Any]) -> dict[str, Any]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda error: list(error.path))
    require(not errors, f"void receipt schema violation: {errors[0].message if errors else ''}")
    body = {key: item for key, item in value.items() if key != "receipt_sha256"}
    require(
        value["receipt_sha256"] == hashlib.sha256((canonical_json(body) + "\n").encode("utf-8")).hexdigest(),
        "void receipt self-hash drift",
    )
    require(value["completed_packet_indices"] == list(EXPECTED_INDICES), "void receipt completed-index drift")
    return dict(value)


def produce(private_root: Path, output_path: Path) -> dict[str, Any]:
    receipt = verify_receipt_value(build_receipt(private_root))
    require(not output_path.exists(), "public output already exists")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(canonical_json(receipt) + "\n", encoding="utf-8")
    return receipt


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Produce a text-free Phase 3 cycle-001 void receipt.")
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        print(canonical_json(produce(args.private_root, args.output)))
    except CycleVoidReceiptError as exc:
        print(canonical_json({"ok": False, "error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
