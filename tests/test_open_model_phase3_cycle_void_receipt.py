"""Hermetic verification tests for the Phase 3 cycle-001 void receipt."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_cycle_void_receipt as void


def _write(path: Path, value: object | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    if isinstance(value, bytes):
        path.write_bytes(value)
    else:
        path.write_text(void.canonical_json(value) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)


def _packet(index: int, item_count: int) -> dict[str, object]:
    return {
        "packet_index": index,
        "packet_id": f"packet-{index:05d}",
        "items": [{"identity": {"packet": index, "item": item}} for item in range(item_count)],
    }


def _fixture(tmp_path: Path) -> Path:
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    packets = []
    for index in range(1, void.EXPECTED_AUTHOR_PACKET_COUNT + 1):
        item_count = 45 if index == 776 else 41 if index in void.EXPECTED_INDICES else 1
        packet = _packet(index, item_count)
        packet_path = root / "author" / "packets" / f"{index:05d}.json"
        _write(packet_path, packet)
        packets.append(
            {
                "packet_index": index,
                "packet_id": packet["packet_id"],
                "packet_sha256": void.sha256_file(packet_path) if packet_path.exists() else "0" * 64,
                "item_count": item_count,
                "relative_path": f"author/packets/{index:05d}.json",
            }
        )
    manifest: dict[str, object] = {
        "schema_version": "phase3_source_production_manifest_v1",
        "bindings": {"evaluation_cycle_id": void.CYCLE_ID},
        "denominator": {"heldout_labels": void.EXPECTED_HELDOUT_LABELS},
        "author_packet_count": void.EXPECTED_AUTHOR_PACKET_COUNT,
        "author_packets": packets,
    }
    manifest["manifest_sha256"] = void.sha256_value(manifest)
    _write(root / "manifest.json", manifest)
    _write(root / "deterministic-partition-dispositions.jsonl", b"{}\n")
    for index in void.EXPECTED_INDICES:
        raw = root / "author" / "raw" / f"{index:05d}.raw"
        incoming = root / "author" / "incoming" / f"{index:05d}.raw"
        response = root / "author" / "responses" / f"{index:05d}.json"
        raw_value = f"opaque raw response {index}".encode()
        _write(raw, raw_value)
        _write(incoming, raw_value)
        _write(response, {"opaque": index})
        stdout = root / "author" / "provider-logs" / f"{index:05d}.stdout"
        stderr = root / "author" / "provider-logs" / f"{index:05d}.stderr"
        _write(stdout, f"stdout {index}".encode())
        _write(stderr, b"")
        invocation = {
            "schema_version": "phase3_source_production_provider_invocation_v1",
            "packet_id": f"packet-{index:05d}",
            "raw_sha256": void.sha256_file(raw),
            "stdout_sha256": void.sha256_file(stdout),
            "stderr_sha256": void.sha256_file(stderr),
            "exit_code": 0,
        }
        invocation_path = root / "author" / "invocations" / f"{index:05d}.json"
        _write(invocation_path, invocation)
        _write(
            root / "author" / "records" / f"{index:05d}.json",
            {
                "schema_version": "phase3_source_production_author_transport_v1",
                "packet_index": index,
                "packet_id": f"packet-{index:05d}",
                "packet_sha256": packets[index - 1]["packet_sha256"],
                "raw_sha256": void.sha256_file(raw),
                "response_sha256": void.sha256_file(response),
                "invocation_receipt_sha256": void.sha256_file(invocation_path),
            },
        )
    for path in (root / "author").rglob("*"):
        if path.is_dir():
            os.chmod(path, 0o700)
    os.chmod(root / "author", 0o700)
    return root


def test_build_receipt_is_text_free_and_accepts_private_preseal_mode(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    receipt = void.build_receipt(root)
    assert receipt["text_free"] is True
    assert receipt["completed_packet_indices"] == list(void.EXPECTED_INDICES)
    assert receipt["author_packet_count"] == 918
    assert receipt["completed_referenced_unit_count"] == 947
    assert receipt["downstream_ingest"] == {
        "review": False,
        "assembly": False,
        "disposition": False,
        "author_ingest_not_asserted": True,
    }
    assert "opaque raw response" not in void.canonical_json(receipt)
    assert void.verify_receipt_value(receipt) == receipt


def test_produce_requires_explicit_new_public_output_and_preserves_private_files(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    before = {path.relative_to(root): void.sha256_file(path) for path in root.rglob("*") if path.is_file()}
    output = tmp_path / "public" / "cycle-void.json"
    receipt = void.produce(root, output)
    assert json.loads(output.read_text(encoding="utf-8")) == receipt
    after = {path.relative_to(root): void.sha256_file(path) for path in root.rglob("*") if path.is_file()}
    assert after == before
    with pytest.raises(void.CycleVoidReceiptError, match="already exists"):
        void.produce(root, output)


@pytest.mark.parametrize("mutation", ["extra", "symlink", "mode", "review"])
def test_build_receipt_rejects_tree_or_custody_drift(tmp_path: Path, mutation: str) -> None:
    root = _fixture(tmp_path)
    if mutation == "extra":
        _write(root / "author" / "records" / "00021.json", {})
    elif mutation == "symlink":
        (root / "author" / "raw" / "00001.raw").unlink()
        (root / "author" / "raw" / "00001.raw").symlink_to(root / "manifest.json")
    elif mutation == "mode":
        os.chmod(root / "author" / "responses" / "00001.json", 0o200)
    else:
        (root / "review").mkdir(mode=0o700)
    with pytest.raises(void.CycleVoidReceiptError):
        void.build_receipt(root)
