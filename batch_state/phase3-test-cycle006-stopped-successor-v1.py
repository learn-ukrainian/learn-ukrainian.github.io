#!/usr/bin/env python3
"""Synthetic-only failure proof for the Cycle-006 controlled-stop successor."""

from __future__ import annotations

import importlib.util
import os
import stat
import tempfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def load(name: str, filename: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SUCCESSOR = load("cycle006_stopped_successor", "phase3-prepare-cycle006-stopped-successor-v1.py")
TRANSPORT = load("cycle006_transport_test_helpers", "phase3-test-cycle006-gemini-transport-v2.py")
RUN = TRANSPORT.RUN


def put(path: Path, value: Any, *, raw: bool = False) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    data = value if raw else RUN.canonical(value)
    path.write_bytes(data)
    os.chmod(path, 0o600)
    return data


def seal_packet(package: Path, lane: str, index: int, rows: list[dict[str, Any]]) -> None:
    packet = {
        "schema_version": "phase3_cycle006_private_packet_v1", "evaluation_cycle_id": RUN.CYCLE, "lane": lane,
        "packet_index": index, "row_count": len(rows), "rows": rows,
        "packet_identity_set_sha256": RUN.digest(RUN.canonical(sorted(RUN._identity(row) for row in rows))),
    }
    packet_path = package / lane / f"packet-{index:04d}.json"
    put(packet_path, packet)
    chunks = RUN.chunks(packet)
    entries = []
    for part in chunks:
        number = part["chunk_index"]
        labels = {"labels": list(TRANSPORT.labels_for(part, lane=lane)["labels_by_position"].values())}
        raw = b"{}"
        root = package / RUN.OUTPUT / lane / "chunks" / f"packet-{index:04d}"
        raw_hash = RUN.digest(put(root / f"raw-chunk-{number:02d}.raw", raw, raw=True))
        labels_hash = RUN.digest(put(root / f"labels-chunk-{number:02d}.json", labels))
        receipt = {
            "schema_version": "phase3_cycle006_gemini_chunk_receipt_v2", "evaluation_cycle_id": RUN.CYCLE,
            "lane": lane, "packet_index": index, "chunk_index": number, "chunk_count": part["chunk_count"],
            "row_count": len(part["rows"]), "chunk_identity_set_sha256": RUN.digest(RUN.canonical(sorted(RUN._identity(row) for row in part["rows"]))),
            "response_raw_sha256": raw_hash, "labels_sha256": labels_hash, "attempt_count": 1,
            "exact_model": RUN.MODEL, "model_family": RUN.FAMILY, "harness": RUN.HARNESS, "text_free": True,
        }
        receipt["receipt_sha256"] = RUN.digest(RUN.canonical(receipt))
        receipt_hash = RUN.digest(put(root / f"receipt-chunk-{number:02d}.json", receipt))
        entries.append({"chunk_index": number, "row_count": len(part["rows"]), "response_raw_sha256": raw_hash, "labels_sha256": labels_hash, "chunk_receipt_sha256": receipt_hash})
    out = package / RUN.OUTPUT / lane
    manifest = {"schema_version": "phase3_cycle006_gemini_raw_manifest_v2", "evaluation_cycle_id": RUN.CYCLE, "lane": lane, "packet_index": index, "chunk_count": len(chunks), "chunks": entries, "text_free": True}
    manifest_hash = RUN.digest(put(out / f"raw-manifest-{index:04d}.json", manifest))
    labels = {"labels": [label for part in chunks for label in TRANSPORT.labels_for(part, lane=lane)["labels_by_position"].values()]}
    labels_hash = RUN.digest(put(out / f"labels-{index:04d}.json", labels))
    receipt = {"schema_version": "phase3_cycle006_packet_label_receipt_v2", "evaluation_cycle_id": RUN.CYCLE, "lane": lane, "packet_index": index, "row_count": len(rows), "packet_raw_sha256": RUN.digest(packet_path.read_bytes()), "packet_identity_set_sha256": packet["packet_identity_set_sha256"], "raw_manifest_sha256": manifest_hash, "labels_sha256": labels_hash, "chunk_count": len(chunks), "exact_model": RUN.MODEL, "model_family": RUN.FAMILY, "harness": RUN.HARNESS, "text_free": True}
    receipt["receipt_sha256"] = RUN.digest(RUN.canonical(receipt))
    put(out / f"receipt-{index:04d}.json", receipt)


def fixture(root: Path) -> tuple[Path, Path]:
    package = TRANSPORT.make_package(root, lane="clean_label", count=50)
    # Forty clean and one residual seal establish the exact public 2,050-row
    # adoption denominator without a provider call; fixture content is synthetic only.
    for index in range(1, 41):
        seal_packet(package, "clean_label", index, TRANSPORT.rows(50, "clean_label"))
    seal_packet(package, "residual_label", 1, TRANSPORT.rows(50, "residual_label"))
    manifest = RUN._read_json(package / "label-manifest.json")
    manifest["packets"] = [
        {
            "lane": lane,
            "packet_index": index,
            "canonical_basename": f"packet-{index:04d}.json",
            "row_count": 50,
            "raw_sha256": RUN.digest((package / lane / f"packet-{index:04d}.json").read_bytes()),
            "packet_identity_set_sha256": RUN._read_json(package / lane / f"packet-{index:04d}.json")[
                "packet_identity_set_sha256"
            ],
        }
        for lane, indices in (("clean_label", range(1, 41)), ("residual_label", range(1, 2)))
        for index in indices
    ]
    manifest["receipt_sha256"] = RUN.digest(RUN.canonical({key: value for key, value in manifest.items() if key != "receipt_sha256"}))
    put(package / "label-manifest.json", manifest)
    stop_dir = package / RUN.OUTPUT / "residual_label" / "chunks" / "packet-0002"
    for attempt in (1, 2):
        RUN._mark(stop_dir, "residual_label", 2, 1, attempt, "started")
        RUN._mark(stop_dir, "residual_label", 2, 1, attempt, "terminal", "structured_output_envelope_drift")
    RUN.stop(package, "residual_label", 2, "structured_output_envelope_drift")
    for directory in (package, *[item for item in package.rglob("*") if item.is_dir()]):
        os.chmod(directory, 0o700)
    amendment = root / "amendment.md"
    put(amendment, b"synthetic amendment\n", raw=True)
    return package, amendment


def tree_hash(path: Path) -> str:
    entries = []
    for item in sorted(path.rglob("*")):
        if item.is_file():
            entries.append((str(item.relative_to(path)), RUN.digest(item.read_bytes())))
    return RUN.digest(RUN.canonical(entries))


def inode_state(path: Path) -> list[tuple[str, int, int, int]]:
    result = []
    for item in (path, *sorted(path.rglob("*"))):
        entry = item.stat()
        result.append((str(item.relative_to(path)) if item != path else ".", stat.S_IMODE(entry.st_mode), entry.st_ino, entry.st_nlink))
    return result


def proof() -> None:
    with tempfile.TemporaryDirectory(prefix="cycle006-stop-successor-") as temporary:
        root = Path(temporary)
        source, amendment = fixture(root)
        before = tree_hash(source)
        source_inode_state = inode_state(source)
        destination = root / "successor"
        result = SUCCESSOR.prepare(source, destination, amendment, fixture=True)
        assert result == {"ok": True, "adopted_packet_total": 41, "adopted_row_total": 2050, "text_free": True}
        assert tree_hash(source) == before, "source package changed"
        assert inode_state(source) == source_inode_state, "source inode, mode, or link count changed"
        assert (source / "clean_label" / "packet-0001.json").stat().st_ino != (
            destination / "clean_label" / "packet-0001.json"
        ).stat().st_ino
        assert (source / RUN.OUTPUT / "clean_label" / "labels-0001.json").stat().st_ino != (
            destination / RUN.OUTPUT / "clean_label" / "labels-0001.json"
        ).stat().st_ino
        assert not (destination / RUN.OUTPUT / "provider-stop.json").exists()
        assert not (destination / RUN.OUTPUT / "residual_label" / "chunks" / "packet-0002").exists()
        assert stat.S_IMODE((destination / "stop-successor-provenance-receipt.json").stat().st_mode) == 0o600
        receipt = SUCCESSOR._json(destination / "stop-successor-provenance-receipt.json", "test")
        assert receipt["adopted_row_total"] == 2050 and receipt["third_call_authorization_scope"] == "destination_package_only"
        assert b"synthetic-private" not in (destination / "stop-successor-provenance-receipt.json").read_bytes()
        receipt_body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
        SUCCESSOR._verify_receipt(destination / "stop-successor-provenance-receipt.json", receipt_body)
        wrong_receipt = dict(receipt_body)
        wrong_receipt["adopted_row_total"] = 0
        try:
            SUCCESSOR._verify_receipt(destination / "stop-successor-provenance-receipt.json", wrong_receipt)
        except SUCCESSOR.Error as exc:
            assert exc.code == "destination_verification_drift"
        else:
            raise AssertionError("receipt readback accepted a wrong denominator")
        try:
            SUCCESSOR.prepare(source, destination, amendment, fixture=True)
        except SUCCESSOR.Error as exc:
            assert exc.code == "destination_exists"
        else:
            raise AssertionError("existing destination was overwritten")
        bad_source, bad_amendment = fixture(root / "bad")
        put(bad_source / "unexpected", b"x", raw=True)
        try:
            SUCCESSOR.prepare(bad_source, root / "bad-destination", bad_amendment, fixture=True)
        except SUCCESSOR.Error as exc:
            assert exc.code == "source_shape_drift"
        else:
            raise AssertionError("unexpected state accepted")
        partial_source, partial_amendment = fixture(root / "partial")
        (partial_source / RUN.OUTPUT / "clean_label" / "receipt-0001.json").unlink()
        try:
            SUCCESSOR.prepare(partial_source, root / "partial-destination", partial_amendment, fixture=True)
        except SUCCESSOR.Error as exc:
            assert exc.code == "source_shape_drift"
        else:
            raise AssertionError("partial sealed packet accepted")


if __name__ == "__main__":
    proof()
    print('{"ok":true,"synthetic_only":true,"provider_calls":0,"text_free":true}')
