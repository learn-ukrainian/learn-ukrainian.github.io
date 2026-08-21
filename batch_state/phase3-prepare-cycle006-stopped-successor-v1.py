#!/usr/bin/env python3
"""Prepare, without provider calls, a clean successor from a stopped Cycle-006 package.

The source is read-only.  The destination is newly created and contains the
unchanged frozen package plus only Gemini packet artifacts that re-verify as
sealed.  Attempt markers, provider stops, and unsealed packet state are never
adopted.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
RUNNER_PATH = HERE / "phase3-run-cycle006-gemini-label-provider-batch-v2.py"
OUTPUT = "label-output-gemini-v2"
FROZEN = frozenset({"clean_label", "residual_label", "prompts", "custody-receipt.json", "label-manifest.json"})
ADOPTED = {"clean_label": tuple(range(1, 41)), "residual_label": (1,)}
EXPECTED_ROWS = {"clean_label": 2_000, "residual_label": 50}
HEX = frozenset("0123456789abcdef")


class Error(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _load_runner() -> Any:
    spec = importlib.util.spec_from_file_location("cycle006_stop_successor_runner", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("runner_unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUN = _load_runner()


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _mode(path: Path, mode: int, code: str) -> None:
    try:
        entry = path.lstat()
    except OSError as exc:
        raise Error(code) from exc
    if path.is_symlink() or stat.S_IMODE(entry.st_mode) != mode:
        raise Error(code)


def _read(path: Path, code: str) -> bytes:
    _mode(path, 0o600, code)
    try:
        return path.read_bytes()
    except OSError as exc:
        raise Error(code) from exc


def _json(path: Path, code: str) -> dict[str, Any]:
    try:
        value = json.loads(_read(path, code).decode("utf-8", "strict"), object_pairs_hook=RUN._pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, RUN.Error) as exc:
        raise Error(code) from exc
    if not isinstance(value, dict):
        raise Error(code)
    return value


def _dir(path: Path, code: str) -> None:
    try:
        entry = path.lstat()
    except OSError as exc:
        raise Error(code) from exc
    if path.is_symlink() or not stat.S_ISDIR(entry.st_mode) or stat.S_IMODE(entry.st_mode) != 0o700:
        raise Error(code)


def _bind(source: Path) -> tuple[str, str]:
    custody, manifest = source / "custody-receipt.json", source / "label-manifest.json"
    custody_hash, manifest_hash = digest(_read(custody, "source_binding_drift")), digest(_read(manifest, "source_binding_drift"))
    RUN.EXPECTED_CUSTODY_SHA256, RUN.EXPECTED_LABEL_MANIFEST_SHA256 = custody_hash, manifest_hash
    return custody_hash, manifest_hash


def _manifest_packet(source: Path, lane: str, index: int) -> tuple[Path, dict[str, Any]]:
    path = source / lane / f"packet-{index:04d}.json"
    packet = _json(path, "source_packet_drift")
    if packet.get("lane") != lane or packet.get("packet_index") != index or not isinstance(packet.get("rows"), list):
        raise Error("source_packet_drift")
    return path, packet


def _verify_chunk_readonly(source: Path, lane: str, index: int, part: dict[str, Any]) -> None:
    """The runner's public chunk receipt schema, checked without touching source modes."""
    number = int(part["chunk_index"])
    root = source / OUTPUT / lane / "chunks" / f"packet-{index:04d}"
    labels_path = root / f"labels-chunk-{number:02d}.json"
    raw_path = root / f"raw-chunk-{number:02d}.raw"
    receipt_path = root / f"receipt-chunk-{number:02d}.json"
    labels, receipt = _json(labels_path, "sealed_output_drift"), _json(receipt_path, "sealed_output_drift")
    raw = _read(raw_path, "sealed_output_drift")
    try:
        RUN.SOURCE.validate(lane, {"rows": part["rows"]}, RUN.canonical(labels))
    except RUN.SOURCE.Invalid as exc:
        raise Error("sealed_output_drift") from exc
    expected = {
        "schema_version": "phase3_cycle006_gemini_chunk_receipt_v2", "evaluation_cycle_id": RUN.CYCLE,
        "lane": lane, "packet_index": index, "chunk_index": number, "chunk_count": part["chunk_count"],
        "row_count": len(part["rows"]),
        "chunk_identity_set_sha256": digest(RUN.canonical(sorted(RUN._identity(row) for row in part["rows"]))),
        "response_raw_sha256": digest(raw), "labels_sha256": digest(_read(labels_path, "sealed_output_drift")),
        "attempt_count": receipt.get("attempt_count"), "exact_model": RUN.MODEL, "model_family": RUN.FAMILY,
        "harness": RUN.HARNESS, "text_free": True,
    }
    if (
        receipt.get("attempt_count") not in {1, 2}
        or set(receipt) != set(expected) | {"receipt_sha256"}
        or any(receipt.get(key) != value for key, value in expected.items())
        or receipt.get("receipt_sha256") != digest(RUN.canonical(expected))
    ):
        raise Error("sealed_output_drift")


def _verify_sealed(source: Path, lane: str, index: int) -> int:
    """Use the existing chunk and semantic validators without retaining labels."""
    try:
        # This is the runner's complete custody, manifest, prompt-binding and
        # packet validator.  It is read-only for an existing, correctly-moded
        # package and keeps this successor aligned with the transport contract.
        _path, packet = RUN.packet(source, lane, index)
    except RUN.Error as exc:
        raise Error("source_packet_drift") from exc
    parts = RUN.chunks(packet)
    try:
        for part in parts:
            _verify_chunk_readonly(source, lane, index, part)
        labels = _json(source / OUTPUT / lane / f"labels-{index:04d}.json", "sealed_output_drift")
        RUN.SOURCE.validate(lane, {"rows": packet["rows"]}, RUN.canonical(labels))
    except (RUN.Error, RUN.SOURCE.Invalid, Error) as exc:
        raise Error("sealed_output_drift") from exc
    receipt = _json(source / OUTPUT / lane / f"receipt-{index:04d}.json", "sealed_output_drift")
    manifest = _json(source / OUTPUT / lane / f"raw-manifest-{index:04d}.json", "sealed_output_drift")
    expected = {
        "schema_version": "phase3_cycle006_packet_label_receipt_v2", "evaluation_cycle_id": RUN.CYCLE,
        "lane": lane, "packet_index": index, "row_count": packet.get("row_count"),
        "packet_raw_sha256": digest(_read(_path, "source_packet_drift")),
        "packet_identity_set_sha256": packet.get("packet_identity_set_sha256"),
        "raw_manifest_sha256": digest(_read(source / OUTPUT / lane / f"raw-manifest-{index:04d}.json", "sealed_output_drift")),
        "labels_sha256": digest(_read(source / OUTPUT / lane / f"labels-{index:04d}.json", "sealed_output_drift")),
        "chunk_count": len(parts), "exact_model": RUN.MODEL, "model_family": RUN.FAMILY, "harness": RUN.HARNESS,
        "text_free": True,
    }
    if set(receipt) != set(expected) | {"receipt_sha256"} or any(receipt.get(k) != v for k, v in expected.items()):
        raise Error("sealed_output_drift")
    if receipt.get("receipt_sha256") != digest(canonical(expected)) or manifest.get("chunk_count") != len(parts):
        raise Error("sealed_output_drift")
    return len(packet["rows"])


def _verify_stop(source: Path) -> None:
    stop = _json(source / OUTPUT / "provider-stop.json", "stop_state_drift")
    if not (
        stop.get("evaluation_cycle_id") == RUN.CYCLE and stop.get("lane") == "residual_label"
        and stop.get("terminal_packet_index") == 2 and stop.get("failure_code") == "structured_output_envelope_drift"
        and stop.get("new_provider_calls_allowed") is False and stop.get("text_free") is True
    ):
        raise Error("stop_state_drift")
    attempt_dir = source / OUTPUT / "residual_label" / "chunks" / "packet-0002"
    _dir(attempt_dir, "stop_state_drift")
    expected = {f"attempt-{attempt}-chunk-01.{state}.json" for attempt in (1, 2) for state in ("started", "terminal")}
    if {item.name for item in attempt_dir.iterdir()} != expected:
        raise Error("stop_state_drift")
    for attempt in (1, 2):
        marker = _json(attempt_dir / f"attempt-{attempt}-chunk-01.terminal.json", "stop_state_drift")
        if marker.get("failure_code") != "structured_output_envelope_drift" or marker.get("state") != "terminal":
            raise Error("stop_state_drift")


def _verify_output_shape(source: Path) -> None:
    """Reject output outside the sealed adoption set and the known stopped attempt."""
    root = source / OUTPUT
    _dir(root, "source_shape_drift")
    if {item.name for item in root.iterdir()} != {"clean_label", "residual_label", "provider-stop.json"}:
        raise Error("source_shape_drift")
    for lane, indices in ADOPTED.items():
        lane_root = root / lane
        chunks_root = lane_root / "chunks"
        _dir(lane_root, "source_shape_drift")
        _dir(chunks_root, "source_shape_drift")
        expected_final = {
            f"{prefix}-{index:04d}.json" for index in indices for prefix in ("labels", "receipt", "raw-manifest")
        }
        if {item.name for item in lane_root.iterdir() if item.name != "chunks"} != expected_final:
            raise Error("source_shape_drift")
        expected_chunks = {f"packet-{index:04d}" for index in indices}
        if lane == "residual_label":
            expected_chunks.add("packet-0002")
        if {item.name for item in chunks_root.iterdir()} != expected_chunks:
            raise Error("source_shape_drift")
        for index in indices:
            packet = _manifest_packet(source, lane, index)[1]
            packet_dir = chunks_root / f"packet-{index:04d}"
            _dir(packet_dir, "source_shape_drift")
            expected = {
                f"{prefix}-chunk-{int(part['chunk_index']):02d}.{suffix}"
                for part in RUN.chunks(packet)
                for prefix, suffix in (("labels", "json"), ("raw", "raw"), ("receipt", "json"))
            }
            observed = {item.name for item in packet_dir.iterdir()}
            # Retried, fully sealed chunks may retain their text-free terminal
            # markers, but no other runtime or partial file is admitted.
            allowed_markers = {
                f"attempt-{attempt}-chunk-{int(part['chunk_index']):02d}.{state}.json"
                for part in RUN.chunks(packet)
                for attempt in (1, 2)
                for state in ("started", "terminal")
            }
            if not expected <= observed or not observed <= expected | allowed_markers:
                raise Error("source_shape_drift")


def _copy(source: Path, destination: Path) -> None:
    """Exclusively publish a fsynced copy; source inode/link state is untouched."""
    if source.is_symlink():
        raise Error("source_shape_drift")
    entry = source.lstat()
    if stat.S_ISREG(entry.st_mode):
        _mode(source, 0o600, "source_shape_drift")
        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(destination.parent, 0o700)
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
        temporary = Path(temporary_name)
        try:
            with source.open("rb") as input_stream, os.fdopen(descriptor, "wb") as output_stream:
                os.fchmod(output_stream.fileno(), 0o600)
                shutil.copyfileobj(input_stream, output_stream)
                output_stream.flush()
                os.fsync(output_stream.fileno())
            # link(2) is exclusive publication; it cannot replace a raced-in
            # destination and the temporary inode is never source-owned.
            os.link(temporary, destination)
        except FileExistsError as exc:
            raise Error("destination_exists") from exc
        finally:
            temporary.unlink(missing_ok=True)
    elif stat.S_ISDIR(entry.st_mode):
        _dir(source, "source_shape_drift")
        destination.mkdir(mode=0o700)
        os.chmod(destination, 0o700)
        for child in sorted(source.iterdir(), key=lambda item: item.name):
            _copy(child, destination / child.name)
    else:
        raise Error("source_shape_drift")


def _copy_packet(source: Path, destination: Path, lane: str, index: int) -> None:
    root, target = source / OUTPUT / lane, destination / OUTPUT / lane
    for name in (f"labels-{index:04d}.json", f"receipt-{index:04d}.json", f"raw-manifest-{index:04d}.json"):
        _copy(root / name, target / name)
    packet_dir = root / "chunks" / f"packet-{index:04d}"
    target_packet = target / "chunks" / f"packet-{index:04d}"
    _dir(packet_dir, "sealed_output_drift")
    target_packet.mkdir(parents=True, mode=0o700)
    os.chmod(target_packet.parent, 0o700)
    os.chmod(target_packet, 0o700)
    for chunk in RUN.chunks(_manifest_packet(source, lane, index)[1]):
        number = int(chunk["chunk_index"])
        for prefix in ("labels", "raw", "receipt"):
            suffix = "raw" if prefix == "raw" else "json"
            _copy(packet_dir / f"{prefix}-chunk-{number:02d}.{suffix}", target_packet / f"{prefix}-chunk-{number:02d}.{suffix}")


def _verify_receipt(path: Path, expected: dict[str, Any]) -> None:
    """Read back the staged provenance receipt before destination publication."""
    receipt = _json(path, "destination_verification_drift")
    sealed = dict(expected)
    sealed["receipt_sha256"] = digest(canonical(expected))
    if set(receipt) != set(sealed) or receipt != sealed:
        raise Error("destination_verification_drift")
    if receipt["source_custody_receipt_sha256"] != receipt["destination_custody_receipt_sha256"]:
        raise Error("destination_verification_drift")
    if receipt["source_label_manifest_sha256"] != receipt["destination_label_manifest_sha256"]:
        raise Error("destination_verification_drift")
    if receipt["adopted_packet_counts"] != {lane: len(indices) for lane, indices in ADOPTED.items()}:
        raise Error("destination_verification_drift")
    if receipt["adopted_row_counts"] != expected["adopted_row_counts"]:
        raise Error("destination_verification_drift")


def prepare(source: Path, destination: Path, amendment: Path, *, fixture: bool = False) -> dict[str, Any]:
    source, destination, amendment = Path(source), Path(destination), Path(amendment)
    _dir(source, "source_shape_drift")
    _mode(amendment, 0o600, "amendment_binding_drift")
    if destination.exists() or destination.is_symlink() or source.resolve() == destination.resolve():
        raise Error("destination_exists")
    names = {item.name for item in source.iterdir()}
    if names != FROZEN | {OUTPUT}:
        raise Error("source_shape_drift")
    custody_hash, manifest_hash = _bind(source)
    _verify_output_shape(source)
    adopted_rows = {lane: sum(_verify_sealed(source, lane, index) for index in indices) for lane, indices in ADOPTED.items()}
    _verify_stop(source)
    if not fixture and adopted_rows != EXPECTED_ROWS:
        raise Error("adopted_denominator_drift")
    parent = destination.parent
    parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    stage = Path(tempfile.mkdtemp(prefix=f".{destination.name}.stage-", dir=parent))
    os.chmod(stage, 0o700)
    try:
        for name in sorted(FROZEN):
            _copy(source / name, stage / name)
        (stage / OUTPUT).mkdir(mode=0o700)
        os.chmod(stage / OUTPUT, 0o700)
        for lane, indices in ADOPTED.items():
            for index in indices:
                _copy_packet(source, stage, lane, index)
        _bind(stage)
        verified = {lane: sum(_verify_sealed(stage, lane, index) for index in indices) for lane, indices in ADOPTED.items()}
        if verified != adopted_rows or (stage / OUTPUT / "provider-stop.json").exists():
            raise Error("destination_verification_drift")
        receipt = {
            "schema_version": "phase3_cycle006_stopped_successor_receipt_v1", "evaluation_cycle_id": RUN.CYCLE,
            "amendment_raw_sha256": digest(_read(amendment, "amendment_binding_drift")),
            "source_custody_receipt_sha256": custody_hash, "source_label_manifest_sha256": manifest_hash,
            "destination_custody_receipt_sha256": digest(_read(stage / "custody-receipt.json", "destination_verification_drift")),
            "destination_label_manifest_sha256": digest(_read(stage / "label-manifest.json", "destination_verification_drift")),
            "adopted_packet_counts": {lane: len(indices) for lane, indices in ADOPTED.items()},
            "adopted_row_counts": adopted_rows, "adopted_packet_total": sum(len(v) for v in ADOPTED.values()),
            "adopted_row_total": sum(adopted_rows.values()), "source_unchanged": True,
            "incomplete_residual_packet_omitted": 2, "provider_stop_omitted": True,
            "third_call_authorization_scope": "destination_package_only", "text_free": True,
        }
        path = stage / "stop-successor-provenance-receipt.json"
        with path.open("xb") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(canonical({**receipt, "receipt_sha256": digest(canonical(receipt))}))
            stream.flush()
            os.fsync(stream.fileno())
        _verify_receipt(path, receipt)
        os.replace(stage, destination)
        return {"ok": True, "adopted_packet_total": receipt["adopted_packet_total"], "adopted_row_total": receipt["adopted_row_total"], "text_free": True}
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--amendment", type=Path, required=True)
    parser.add_argument("--fixture", action="store_true")
    args = parser.parse_args()
    try:
        print(canonical(prepare(args.source, args.destination, args.amendment, fixture=args.fixture)).decode(), end="")
    except Error as exc:
        print(canonical({"ok": False, "failure_code": exc.code, "text_free": True}).decode(), end="")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
