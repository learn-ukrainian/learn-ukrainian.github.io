"""Synthetic, source-free behavior proof for the Cycle 007 materializer.

Never touches the private 10,159-row denominator or a real Cycle-005/006
package; every fixture here is synthetic and disjoint from held-out data.
"""

from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path
from typing import Any

import pytest

from scripts.projects.open_model_data import phase3_cycle007_materializer as materializer


def _write(path: Path, value: Any, *, raw: bool = False) -> bytes:
    payload = value if raw else materializer.canonical(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    os.chmod(path, materializer.PRIVATE_FILE_MODE)
    return payload


def _row(index: int, lane: str, *, include_cycle: bool, forbidden_keys: dict[str, Any] | None = None) -> dict[str, Any]:
    unit_id = f"synthetic.{lane}.{index:03d}"
    row: dict[str, Any] = {
        "unit_id": unit_id,
        "unit_sha256": hashlib.sha256(unit_id.encode()).hexdigest(),
        "family_id": "synthetic_family",
        "source_text": f"PRIVATE-SYNTHETIC-SOURCE-{index}",
        "source_record": {"locator": f"synthetic-locator-{index}"},
        "nested_source": {"order": [index, "value"], "unicode": "українська"},
    }
    if include_cycle:
        row["evaluation_cycle_id"] = materializer.CYCLE005
    if forbidden_keys:
        row.update(forbidden_keys)
    return row


def _fixture(root: Path, *, forbidden_row_keys: dict[str, Any] | None = None) -> tuple[Path, Path, list[dict[str, Any]]]:
    source = root / "cycle005-source"
    source.mkdir(mode=materializer.PRIVATE_DIR_MODE)
    os.chmod(source, materializer.PRIVATE_DIR_MODE)
    packet_specs = (("clean_label", 1, 2), ("clean_label", 2, 1), ("residual_label", 1, 3))
    packet_records: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    for lane, index, count in packet_specs:
        start = len(all_rows)
        rows = [
            _row(
                start + offset,
                lane,
                include_cycle=(start + offset) % 2 == 0,
                forbidden_keys=forbidden_row_keys if (lane, index, offset) == ("clean_label", 1, 0) else None,
            )
            for offset in range(count)
        ]
        all_rows.extend(rows)
        packet = {
            "schema_version": "phase3_cycle005_private_packet_v1",
            "evaluation_cycle_id": materializer.CYCLE005,
            "lane": lane,
            "packet_index": index,
            "row_count": count,
            "rows": rows,
            "packet_identity_set_sha256": materializer.identity_set(rows),
        }
        packet_path = source / lane / f"packet-{index:04d}.json"
        packet_raw = _write(packet_path, packet)
        packet_records.append(
            {
                "lane": lane,
                "packet_index": index,
                "canonical_basename": packet_path.name,
                "row_count": count,
                "raw_sha256": materializer.digest(packet_raw),
                "packet_identity_set_sha256": packet["packet_identity_set_sha256"],
            }
        )
    manifest = {
        "schema_version": "phase3_cycle005_label_manifest_v1",
        "evaluation_cycle_id": materializer.CYCLE005,
        "text_free": True,
        "custody_receipt_raw_sha256": "",
        "packet_count": len(packet_records),
        "row_count": len(all_rows),
        "packets": packet_records,
    }
    custody = {
        "schema_version": "phase3_cycle005_custody_receipt_v1",
        "evaluation_cycle_id": materializer.CYCLE005,
        "text_free": True,
        "provider_artifacts_copied": False,
    }
    custody["receipt_sha256"] = materializer._hash_receipt(custody)
    custody_raw = _write(source / "custody-receipt.json", custody)
    manifest["custody_receipt_raw_sha256"] = materializer.digest(custody_raw)
    manifest["receipt_sha256"] = materializer._hash_receipt(manifest)
    _write(source / "label-manifest.json", manifest)
    # A source-side provider artifact proves the materializer is selective:
    # it must never appear anywhere in the fresh Cycle 007 output.
    _write(source / "label-output-grok-cycle005" / "raw-provider-response.raw", b"PRIVATE-PROVIDER-ARTIFACT", raw=True)
    return source, root / "cycle007-successor", all_rows


def test_identity_and_order_preserved_with_only_cycle_id_changed(tmp_path: Path):
    source, output, all_rows = _fixture(tmp_path)
    result = materializer.materialize(source, output, fixture=True)
    assert result["ok"] is True
    assert result["packet_count"] == 3
    assert result["row_count"] == len(all_rows)

    expected_by_id = {row["unit_id"]: row for row in all_rows}
    for lane, index in (("clean_label", 1), ("clean_label", 2), ("residual_label", 1)):
        packet = materializer.strict_json(output / lane / f"packet-{index:04d}.json")
        assert packet["evaluation_cycle_id"] == materializer.CYCLE007
        for row in packet["rows"]:
            expected_row = dict(expected_by_id[row["unit_id"]])
            if "evaluation_cycle_id" in expected_row:
                expected_row["evaluation_cycle_id"] = materializer.CYCLE007
            assert row == expected_row


def test_materializer_output_top_level_excludes_labels_and_prompts(tmp_path: Path):
    source, output, _rows = _fixture(tmp_path)
    materializer.materialize(source, output, fixture=True)
    assert {path.name for path in output.iterdir()} == materializer.OUTPUT_TOP_LEVEL
    # The source-side provider artifact directory must never appear.
    assert not (output / "label-output-grok-cycle005").exists()
    for forbidden in ("prompts", "raw", "responses", "sealed", "transports", "assembled"):
        assert not (output / forbidden).exists()
    custody = materializer.strict_json(output / "custody-receipt.json")
    assert custody["labels_copied"] is False
    assert custody["provider_artifacts_copied"] is False
    assert custody["prompts_generated"] is False


def test_materializer_rejects_forbidden_row_keys_as_label_leak(tmp_path: Path):
    source, output, _rows = _fixture(tmp_path, forbidden_row_keys={"labels": [{"decision_code": "agree"}]})
    with pytest.raises(materializer.MaterializationError) as excinfo:
        materializer.materialize(source, output, fixture=True)
    assert excinfo.value.code == "label_leak_detected"
    assert not output.exists()


def test_materializer_refuses_to_overwrite_existing_output(tmp_path: Path):
    source, output, _rows = _fixture(tmp_path)
    materializer.materialize(source, output, fixture=True)
    with pytest.raises(materializer.MaterializationError) as excinfo:
        materializer.materialize(source, output, fixture=True)
    assert excinfo.value.code == "output_exists"


def test_materializer_output_permissions_are_0700_and_0600(tmp_path: Path):
    source, output, _rows = _fixture(tmp_path)
    materializer.materialize(source, output, fixture=True)
    assert stat.S_IMODE(output.stat().st_mode) == materializer.PRIVATE_DIR_MODE
    for path in output.rglob("*"):
        assert not path.is_symlink()
        mode = stat.S_IMODE(path.stat().st_mode)
        if path.is_dir():
            assert mode == materializer.PRIVATE_DIR_MODE
        else:
            assert mode == materializer.PRIVATE_FILE_MODE


def test_materializer_fsyncs_directories(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    source, output, _rows = _fixture(tmp_path)
    calls = {"count": 0}
    real_fsync = os.fsync

    def _counting_fsync(fd: int) -> None:
        calls["count"] += 1
        real_fsync(fd)

    monkeypatch.setattr(materializer.os, "fsync", _counting_fsync)
    materializer.materialize(source, output, fixture=True)
    # Every packet file, both manifests, and every directory fsync at least once.
    assert calls["count"] >= 3 + 2 + 3


def test_materializer_rolls_back_on_mid_build_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    source, output, _rows = _fixture(tmp_path)

    def _boom(*_args: Any, **_kwargs: Any):
        raise RuntimeError("synthetic mid-build failure")

    monkeypatch.setattr(materializer, "_packet_rows", _boom)
    with pytest.raises(materializer.MaterializationError) as excinfo:
        materializer.materialize(source, output, fixture=True)
    assert excinfo.value.code == "transaction_failure"
    assert not output.exists()
    # No leftover staging directories beside the (still-present) source.
    leftovers = [path for path in tmp_path.iterdir() if path.name.startswith(f".{output.name}.staging-")]
    assert leftovers == []


def test_materializer_rolls_back_when_output_top_level_drifts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    source, output, _rows = _fixture(tmp_path)
    real_build_stage = materializer._build_stage

    def _inject_extra_file(config, stage):
        result = real_build_stage(config, stage)
        (stage / "unexpected-file.json").write_bytes(b"{}")
        os.chmod(stage / "unexpected-file.json", materializer.PRIVATE_FILE_MODE)
        return result

    monkeypatch.setattr(materializer, "_build_stage", _inject_extra_file)
    with pytest.raises(materializer.MaterializationError) as excinfo:
        materializer.materialize(source, output, fixture=True)
    assert excinfo.value.code == "transaction_failure"
    assert not output.exists()


def test_materializer_non_fixture_mode_fails_closed_on_synthetic_data(tmp_path: Path):
    """Real (non-fixture) mode never relaxes the frozen Cycle-005 hash pins."""
    source, output, _rows = _fixture(tmp_path)
    with pytest.raises(materializer.MaterializationError) as excinfo:
        materializer.materialize(source, output, fixture=False)
    assert excinfo.value.code == "source_binding_drift"
    assert not output.exists()


def test_materializer_forbids_weakening_strict_counts_in_real_mode(tmp_path: Path):
    source, output, _rows = _fixture(tmp_path)
    with pytest.raises(materializer.MaterializationError) as excinfo:
        materializer.materialize(source, output, fixture=False, strict_counts=False)
    assert excinfo.value.code == "fixture_flag_required"
    assert not output.exists()


def test_materializer_path_overlap_rejected(tmp_path: Path):
    source, _output, _rows = _fixture(tmp_path)
    with pytest.raises(materializer.MaterializationError) as excinfo:
        materializer.materialize(source, source / "nested-output", fixture=True)
    assert excinfo.value.code == "path_overlap"
