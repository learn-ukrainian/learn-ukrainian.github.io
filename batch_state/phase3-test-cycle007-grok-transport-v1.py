#!/usr/bin/env python3
"""Synthetic tests for the Cycle 007 Grok transport."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projects.open_model_data import phase3_cycle007_evidence_compiler as compiler
from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract


def _load_runner() -> Any:
    path = ROOT / "batch_state" / "phase3-run-cycle007-grok-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_grok_transport", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUN = _load_runner()


def put(path: Path, value: Any) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    data = RUN.canonical(value)
    path.write_bytes(data)
    os.chmod(path, 0o600)
    return data


def put_raw(path: Path, value: bytes) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    path.write_bytes(value)
    os.chmod(path, 0o600)
    return value


def rows(count: int, lane: str = "clean_label") -> list[dict[str, Any]]:
    return [
        {
            "unit_id": f"synthetic-private-{lane}-{position:02d}",
            "unit_sha256": f"{position:064x}",
            "family_id": "pravopys_2026_complete",
        }
        for position in range(1, count + 1)
    ]


def _build_row_evidence(row: dict[str, Any], *, lane: str = "clean_label") -> tuple[dict[str, Any], dict[str, Any]]:
    phenomenon_id = "apostrophe" if lane == "residual_label" else None
    rec = contract.build_evidence_record(
        channel="vesum_attestation",
        source_identity="vesum",
        source_version="v1",
        locator="data/vesum.db#forms",
        query="слово",
        status="attested",
        supports="attestation",
        retrieval_sha256=contract.sha256_value({"mock": "payload"}),
        parser_id="vesum-forms-v1",
        parser_version="1",
        row=row,
        phenomenon_id=phenomenon_id,
    )
    if lane == "residual_label":
        phenomenon_evidence_ids = {k: ([rec["evidence_id"]] if k == "apostrophe" else []) for k in contract.RESIDUAL_PHENOMENON_TAXONOMY}
    else:
        phenomenon_evidence_ids = {}
    row_ev = {
        "unit_id": row["unit_id"],
        "unit_sha256": row["unit_sha256"],
        "evidence": [rec],
        "evidence_ids": [rec["evidence_id"]],
        "phenomenon_evidence_ids": phenomenon_evidence_ids,
        "sufficient_support": True,
        "archaic_only_risk": False,
        "russian_shadow_suspected": False,
    }
    return rec, row_ev


def synthetic_prompt(lane: str) -> bytes:
    title = (
        "Phase 3 Cycle 007 held-out clean-modern label review"
        if lane == "clean_label"
        else "Phase 3 Cycle 007 held-out residual label review"
    )
    return f"# {title}\n\nSynthetic Grok {lane} fixture.\n".encode()


def make_package(root: Path, *, lane: str = "clean_label", index: int = 1, count: int = 50) -> Path:
    package = root / "package"
    package.mkdir(parents=True, mode=0o700)
    os.chmod(package, 0o700)
    for lane_key in RUN.LANES:
        rel = f"prompts/grok-{'clean' if lane_key == 'clean_label' else 'residual'}-label.md"
        payload = synthetic_prompt(lane_key)
        put_raw(package / rel, payload)

    custody_val = {
        "schema_version": "phase3_cycle007_custody_receipt_v1",
        "evaluation_cycle_id": RUN.CYCLE,
        "source_evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-005",
        "amendment_reference": "batch_state/phase3-cycle007-source-grounded-amendment-v1.md",
        "source_custody_receipt_raw_sha256": RUN.SOURCE_CUSTODY_SHA256,
        "source_label_manifest_raw_sha256": RUN.SOURCE_MANIFEST_SHA256,
        "ordered_identity_commitment_sha256": RUN.ORDERED_IDENTITY_COMMITMENT_SHA256,
        "identity_union_commitment_sha256": "5" * 64,
        "ordered_packet_commitment_sha256": "6" * 64,
        "packet_count": 204,
        "row_count": 10159,
        "text_free": True,
    }
    custody_val["receipt_sha256"] = RUN.digest(RUN.canonical(custody_val))
    custody_bytes = put(package / "custody-receipt.json", custody_val)

    packet_rows = rows(count, lane)
    body = {
        "schema_version": "phase3_cycle007_evidence_packet_v1",
        "evaluation_cycle_id": RUN.CYCLE,
        "lane": lane,
        "packet_index": index,
        "row_count": count,
        "rows": packet_rows,
        "packet_identity_set_sha256": RUN.digest(RUN.canonical(sorted(RUN._identity(row) for row in packet_rows))),
    }
    packet_path = package / lane / f"packet-{index:04d}.json"
    packet_bytes = put(packet_path, body)

    entry = {
        "lane": lane,
        "packet_index": index,
        "canonical_basename": packet_path.name,
        "row_count": count,
        "raw_sha256": RUN.digest(packet_bytes),
        "packet_identity_set_sha256": body["packet_identity_set_sha256"],
    }
    manifest = {
        "schema_version": "phase3_cycle007_materialization_manifest_v1",
        "evaluation_cycle_id": RUN.CYCLE,
        "source_evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-005",
        "custody_receipt_raw_sha256": RUN.digest(custody_bytes),
        "ordered_identity_commitment_sha256": RUN.ORDERED_IDENTITY_COMMITMENT_SHA256,
        "identity_union_commitment_sha256": "5" * 64,
        "ordered_packet_commitment_sha256": "6" * 64,
        "packet_count": 204,
        "row_count": 10159,
        "packets": [entry],
        "text_free": True,
    }
    manifest["receipt_sha256"] = RUN.digest(RUN.canonical(manifest))
    manifest_bytes = put(package / "manifest.json", manifest)
    RUN.EXPECTED_CUSTODY_SHA256 = RUN.digest(custody_bytes)
    RUN.EXPECTED_LABEL_MANIFEST_SHA256 = RUN.digest(manifest_bytes)

    # Sidecar
    evidence_records = []
    sidecar_rows = []
    retrieval_payloads = {contract.sha256_value({"mock": "payload"}): {"mock": "payload"}}
    for row in packet_rows:
        rec, row_ev = _build_row_evidence(row, lane=lane)
        evidence_records.append(rec)
        sidecar_rows.append(row_ev)

    sidecar_body = {
        "schema_version": "phase3_cycle007_evidence_sidecar_v1",
        "evaluation_cycle_id": RUN.CYCLE,
        "lane": lane,
        "packet_binding": {
            "canonical_basename": packet_path.name,
            "raw_sha256": RUN.digest(packet_bytes),
            "packet_identity_set_sha256": body["packet_identity_set_sha256"],
        },
        "packet_index": index,
        "row_count": count,
        "tokenizer_id": "phase3-cycle007-cyrillic-tokenizer-v1",
        "tokenizer_version": "1",
        "code_hashes": compiler.CODE_HASHES,
        "server_code_sha256": "f" * 64,
        "sources_db_sha256": "1" * 64,
        "vesum_db_sha256": "2" * 64,
        "network_lookups_performed": 0,
        "rows": sidecar_rows,
        "retrieval_payloads": retrieval_payloads,
    }
    sidecar_body["sidecar_id"] = "cycle007_sidecar:" + contract.sha256_value(sidecar_body)
    sidecar_path = package / "evidence" / f"sidecar-{index:04d}.json"
    sidecar_bytes = put(sidecar_path, sidecar_body)

    ev_manifest = {
        "schema_version": "phase3_cycle007_evidence_manifest_v1",
        "text_free": True,
        "evaluation_cycle_id": RUN.CYCLE,
        "tokenizer_id": "phase3-cycle007-cyrillic-tokenizer-v1",
        "tokenizer_version": "1",
        "code_hashes": compiler.CODE_HASHES,
        "server_code_sha256": "f" * 64,
        "sources_db_sha256": "1" * 64,
        "vesum_db_sha256": "2" * 64,
        "packet_count": 1,
        "row_count": count,
        "network_lookups_performed": 0,
        "sidecars": [
            {
                "packet_index": index,
                "row_count": count,
                "sidecar_sha256": RUN.digest(sidecar_bytes),
                "sidecar_id": sidecar_body["sidecar_id"],
                "lane": lane,
                "packet_binding": sidecar_body["packet_binding"],
            }
        ],
        "source_package_binding": {
            "source_evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-005",
            "custody_receipt_raw_sha256": RUN.digest(custody_bytes),
            "materialization_manifest_sha256": manifest["receipt_sha256"],
            "ordered_identity_commitment_sha256": manifest["ordered_identity_commitment_sha256"],
            "identity_union_commitment_sha256": manifest["identity_union_commitment_sha256"],
            "ordered_packet_commitment_sha256": manifest["ordered_packet_commitment_sha256"],
            "packet_count": manifest["packet_count"],
            "row_count": manifest["row_count"],
        },
    }
    ev_manifest["manifest_sha256"] = contract.sha256_value(ev_manifest)
    ev_manifest_bytes = put(package / "evidence" / "manifest.json", ev_manifest)
    RUN.EXPECTED_EVIDENCE_MANIFEST_SHA256 = RUN.digest(ev_manifest_bytes)
    RUN.EXPECTED_SOURCES_ENDPOINT_IDENTITY = {
        "server_code_sha256": "f" * 64,
        "sources_db_sha256": "1" * 64,
        "vesum_db_sha256": "2" * 64,
    }

    return package


FAKE_GROK = r"""#!/usr/bin/env python3
import json, os, pathlib, sys
prompt = sys.stdin.read()
assert "Phase 3 Cycle 007 held-out" in prompt
assert "--- BEGIN IMMUTABLE PRIVATE PACKET JSON ---" in prompt
assert "--- BEGIN IMMUTABLE EVIDENCE SIDECAR JSON ---" in prompt

packet_json = prompt.split("--- BEGIN IMMUTABLE PRIVATE PACKET JSON ---\n", 1)[1].split("--- END", 1)[0]
rows = json.loads(packet_json)["rows"]
lane = json.loads(packet_json)["lane"]

sidecar_json = prompt.split("--- BEGIN IMMUTABLE EVIDENCE SIDECAR JSON ---\n", 1)[1].split("--- END", 1)[0]
sidecar_rows = json.loads(sidecar_json)["rows"]

state_path = os.environ.get("FAKE_STATE")
count = 0
if state_path:
    state = pathlib.Path(state_path)
    count = int(state.read_text()) if state.exists() else 0
    state.write_text(str(count + 1))

mode = os.environ.get("FAKE_MODE", "valid")
if mode == "invalid" or (mode == "retry" and count == 0):
    print("not-json")
    raise SystemExit(0)
if mode == "nonzero":
    print("not-json")
    raise SystemExit(23)

labels = []
for position, (row, row_ev) in enumerate(zip(rows, sidecar_rows), 1):
    evidence_ids = row_ev.get("evidence_ids", [])
    if lane == "clean_label":
        labels.append({
            "unit_id": row["unit_id"],
            "unit_sha256": row["unit_sha256"],
            "decision_code": "agree",
            "clean_modern_standard_prose": True,
            "modern_genre_id": "scientific_expository",
            "evidence_ids": evidence_ids,
        })
    else:
        phenomenon_id = "apostrophe"
        phenom_ids = row_ev.get("phenomenon_evidence_ids", {}).get(phenomenon_id, evidence_ids)
        labels.append({
            "unit_id": row["unit_id"],
            "unit_sha256": row["unit_sha256"],
            "phenomena": [
                {
                    "phenomenon_id": phenomenon_id,
                    "decision_code": "positive",
                    "evidence_sufficiency": "sufficient",
                    "evidence_ids": phenom_ids,
                }
            ],
            "primary_phenomenon_id": phenomenon_id,
            "item_decision_rollup": "positive",
        })

if mode == "semantic":
    labels[0]["evidence_ids"] = ["cycle007_evidence:invented" + "0" * 48]

out = {"labels": labels}
print(json.dumps(out))
"""


def _make_fake_bin(tmp_path: Path) -> Path:
    bin_path = tmp_path / "fake_grok"
    bin_path.write_text(FAKE_GROK)
    bin_path.chmod(0o755)
    return bin_path


def test_valid_clean_packet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pkg = make_package(tmp_path, lane="clean_label", count=50)
    fake_bin = _make_fake_bin(tmp_path)
    state_file = tmp_path / "state.txt"
    monkeypatch.setenv("FAKE_STATE", str(state_file))
    monkeypatch.setenv("FAKE_MODE", "valid")

    res = RUN.run_packet(pkg, "clean_label", 1, fake_bin, synthetic_provider=True)
    assert res["ok"] is True

    out_dir = pkg / RUN.OUTPUT_ROOT / "clean_label"
    assert (out_dir / "labels-0001.json").exists()
    assert (out_dir / "receipt-0001.json").exists()
    assert (out_dir / "raw-manifest-0001.json").exists()
    assert (out_dir / "raw-0001.raw").exists()


def test_valid_residual_packet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pkg = make_package(tmp_path, lane="residual_label", count=50)
    fake_bin = _make_fake_bin(tmp_path)
    state_file = tmp_path / "state.txt"
    monkeypatch.setenv("FAKE_STATE", str(state_file))
    monkeypatch.setenv("FAKE_MODE", "valid")

    res = RUN.run_packet(pkg, "residual_label", 1, fake_bin, synthetic_provider=True)
    assert res["ok"] is True


def test_resume_sealed_packet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pkg = make_package(tmp_path, lane="clean_label", count=50)
    fake_bin = _make_fake_bin(tmp_path)
    state_file = tmp_path / "state.txt"
    monkeypatch.setenv("FAKE_STATE", str(state_file))
    monkeypatch.setenv("FAKE_MODE", "valid")

    RUN.run_packet(pkg, "clean_label", 1, fake_bin, synthetic_provider=True)
    count_1 = int(state_file.read_text())

    # Resume without executing provider
    res2 = RUN.run_packet(pkg, "clean_label", 1, fake_bin, synthetic_provider=True)
    assert res2["ok"] is True
    count_2 = int(state_file.read_text())
    assert count_1 == count_2


def test_retryable_structural_failure_recovers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pkg = make_package(tmp_path, lane="clean_label", count=50)
    fake_bin = _make_fake_bin(tmp_path)
    state_file = tmp_path / "state.txt"
    monkeypatch.setenv("FAKE_STATE", str(state_file))
    monkeypatch.setenv("FAKE_MODE", "retry")

    res = RUN.run_packet(pkg, "clean_label", 1, fake_bin, synthetic_provider=True)
    assert res["ok"] is True
    assert int(state_file.read_text()) == 2
    out_dir = pkg / RUN.OUTPUT_ROOT / "clean_label"
    assert (out_dir / "attempt-1-0001.terminal.json").exists()


def test_two_structural_failures_writes_stop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pkg = make_package(tmp_path, lane="clean_label", count=50)
    fake_bin = _make_fake_bin(tmp_path)
    state_file = tmp_path / "state.txt"
    monkeypatch.setenv("FAKE_STATE", str(state_file))
    monkeypatch.setenv("FAKE_MODE", "invalid")

    with pytest.raises(RUN.Error):
        RUN.run_packet(pkg, "clean_label", 1, fake_bin, synthetic_provider=True)
    assert (pkg / RUN.OUTPUT_ROOT / "provider-stop.json").exists()


def test_semantic_failure_immediately_stops(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pkg = make_package(tmp_path, lane="clean_label", count=50)
    fake_bin = _make_fake_bin(tmp_path)
    state_file = tmp_path / "state.txt"
    monkeypatch.setenv("FAKE_STATE", str(state_file))
    monkeypatch.setenv("FAKE_MODE", "semantic")

    with pytest.raises(RUN.Error):
        RUN.run_packet(pkg, "clean_label", 1, fake_bin, synthetic_provider=True)
    assert int(state_file.read_text()) == 1  # No retry for semantic failure
    assert (pkg / RUN.OUTPUT_ROOT / "provider-stop.json").exists()


def test_stop_idempotence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pkg = make_package(tmp_path, lane="clean_label", count=50)
    fake_bin = _make_fake_bin(tmp_path)
    state_file = tmp_path / "state.txt"
    monkeypatch.setenv("FAKE_STATE", str(state_file))
    monkeypatch.setenv("FAKE_MODE", "valid")

    RUN._stop(pkg, "clean_label", 1, "identity_or_order_drift")
    assert (pkg / RUN.OUTPUT_ROOT / "provider-stop.json").exists()

    with pytest.raises(RUN.Error, match="label_count_or_envelope_drift"):
        RUN.run_packet(pkg, "clean_label", 1, fake_bin, synthetic_provider=True)
    assert not state_file.exists()


def test_concurrency_must_be_one(tmp_path: Path) -> None:
    pkg = make_package(tmp_path, lane="clean_label", count=50)
    fake_bin = _make_fake_bin(tmp_path)
    with pytest.raises(RUN.Error, match="label_count_or_envelope_drift"):
        RUN.batch(pkg, "clean_label", 1, 1, fake_bin, concurrency=2, synthetic_provider=True)


def test_partial_seal_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pkg = make_package(tmp_path, lane="clean_label", count=50)
    fake_bin = _make_fake_bin(tmp_path)
    monkeypatch.setenv("FAKE_MODE", "valid")
    out_dir = pkg / RUN.OUTPUT_ROOT / "clean_label"
    out_dir.mkdir(parents=True, mode=0o700)
    # Write only labels-0001.json
    (out_dir / "labels-0001.json").write_text("{}")
    os.chmod(out_dir / "labels-0001.json", 0o600)
    with pytest.raises(RUN.Error, match="label_count_or_envelope_drift"):
        RUN.run_packet(pkg, "clean_label", 1, fake_bin, synthetic_provider=True)
    assert (pkg / RUN.OUTPUT_ROOT / "provider-stop.json").exists()


def test_no_private_disclosure_in_receipts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pkg = make_package(tmp_path, lane="clean_label", count=50)
    fake_bin = _make_fake_bin(tmp_path)
    monkeypatch.setenv("FAKE_MODE", "valid")
    res = RUN.run_packet(pkg, "clean_label", 1, fake_bin, synthetic_provider=True)
    assert res["text_free"] is True

    receipt_path = pkg / RUN.OUTPUT_ROOT / "clean_label" / "receipt-0001.json"
    receipt = json.loads(receipt_path.read_text())
    assert receipt.get("text_free") is True
    assert "rows" not in receipt
    assert "prompt" not in receipt


def test_wrong_evidence_manifest_hash_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pkg = make_package(tmp_path, lane="clean_label", count=50)
    fake_bin = _make_fake_bin(tmp_path)
    monkeypatch.setenv("FAKE_MODE", "valid")
    RUN.EXPECTED_EVIDENCE_MANIFEST_SHA256 = "0" * 64
    with pytest.raises(RUN.Error) as exc_info:
        RUN.run_packet(pkg, "clean_label", 1, fake_bin, synthetic_provider=True)
    assert exc_info.value.code in {"evidence_manifest_binding_drift", "label_count_or_envelope_drift"}


def test_missing_evidence_manifest_hash_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pkg = make_package(tmp_path, lane="clean_label", count=50)
    fake_bin = _make_fake_bin(tmp_path)
    monkeypatch.setenv("FAKE_MODE", "valid")
    RUN.EXPECTED_EVIDENCE_MANIFEST_SHA256 = ""
    with pytest.raises(RUN.Error) as exc_info:
        RUN.run_packet(pkg, "clean_label", 1, fake_bin, synthetic_provider=True)
    assert exc_info.value.code in {"evidence_manifest_binding_drift", "label_count_or_envelope_drift"}


def test_missing_source_package_binding_rejected_before_synthetic_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pkg = make_package(tmp_path, lane="clean_label", count=50)
    fake_bin = _make_fake_bin(tmp_path)
    monkeypatch.setenv("FAKE_MODE", "valid")
    manifest_path = pkg / "evidence" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["source_package_binding"] = None
    manifest["manifest_sha256"] = contract.sha256_value(
        {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    )
    manifest_bytes = put(manifest_path, manifest)
    RUN.EXPECTED_EVIDENCE_MANIFEST_SHA256 = RUN.digest(manifest_bytes)

    with pytest.raises(RUN.Error) as exc_info:
        RUN.run_packet(pkg, "clean_label", 1, fake_bin, synthetic_provider=True)
    assert exc_info.value.code == "evidence_manifest_binding_drift"


def test_sidecar_path_drift_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pkg = make_package(tmp_path, lane="clean_label", count=50)
    fake_bin = _make_fake_bin(tmp_path)
    monkeypatch.setenv("FAKE_MODE", "valid")
    # Move sidecar to legacy path
    sidecar_old = pkg / "evidence" / "sidecar-0001.json"
    sidecar_new = pkg / "clean_label" / "evidence-0001.json"
    sidecar_new.write_bytes(sidecar_old.read_bytes())
    os.chmod(sidecar_new, 0o600)
    sidecar_old.unlink()
    with pytest.raises(RUN.Error) as exc_info:
        RUN.run_packet(pkg, "clean_label", 1, fake_bin, synthetic_provider=True)
    assert exc_info.value.code in {"sidecar_binding_drift", "label_count_or_envelope_drift"}


def test_duplicate_or_foreign_sidecar_manifest_entry_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pkg = make_package(tmp_path, lane="clean_label", count=50)
    fake_bin = _make_fake_bin(tmp_path)
    monkeypatch.setenv("FAKE_MODE", "valid")
    ev_manifest_path = pkg / "evidence" / "manifest.json"
    ev_manifest = json.loads(ev_manifest_path.read_text())
    # Add duplicate entry
    ev_manifest["sidecars"].append(ev_manifest["sidecars"][0])
    ev_manifest["manifest_sha256"] = contract.sha256_value(
        {k: v for k, v in ev_manifest.items() if k != "manifest_sha256"}
    )
    ev_bytes = put(ev_manifest_path, ev_manifest)
    RUN.EXPECTED_EVIDENCE_MANIFEST_SHA256 = RUN.digest(ev_bytes)
    with pytest.raises(RUN.Error) as exc_info:
        RUN.run_packet(pkg, "clean_label", 1, fake_bin, synthetic_provider=True)
    assert exc_info.value.code in {"evidence_manifest_binding_drift", "sidecar_binding_drift", "label_count_or_envelope_drift"}


def test_prompt_tamper_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pkg = make_package(tmp_path, lane="clean_label", count=50)
    fake_bin = _make_fake_bin(tmp_path)
    monkeypatch.setenv("FAKE_MODE", "valid")
    prompt_file = pkg / "prompts" / "grok-clean-label.md"
    prompt_file.write_bytes(b"tampered content")
    os.chmod(prompt_file, 0o600)
    with pytest.raises(RUN.Error):
        RUN.run_packet(pkg, "clean_label", 1, fake_bin, synthetic_provider=True)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="grok_test_"))
    try:
        mp = pytest.MonkeyPatch()
        test_valid_clean_packet(tmp / "t1", mp)
        test_valid_residual_packet(tmp / "t2", mp)
        test_resume_sealed_packet(tmp / "t3", mp)
        test_retryable_structural_failure_recovers(tmp / "t4", mp)
        test_two_structural_failures_writes_stop(tmp / "t5", mp)
        test_semantic_failure_immediately_stops(tmp / "t6", mp)
        test_stop_idempotence(tmp / "t7", mp)
        test_concurrency_must_be_one(tmp / "t8")
        test_partial_seal_rejected(tmp / "t9", mp)
        test_no_private_disclosure_in_receipts(tmp / "t10", mp)
        test_wrong_evidence_manifest_hash_rejected(tmp / "t11", mp)
        test_missing_evidence_manifest_hash_rejected(tmp / "t12", mp)
        test_sidecar_path_drift_rejected(tmp / "t13", mp)
        test_duplicate_or_foreign_sidecar_manifest_entry_rejected(tmp / "t14", mp)
        test_prompt_tamper_rejected(tmp / "t15", mp)
        print(
            json.dumps(
                {"ok": True, "synthetic_only": True, "provider_calls": 0, "text_free": True},
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 0
    finally:
        import shutil

        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
