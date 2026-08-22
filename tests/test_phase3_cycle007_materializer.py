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
    os.chmod(path.parent, materializer.PRIVATE_DIR_MODE)
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


# --------------------------------------------------------------------------
# Amendment step 14: a post-commit diagnostic failure must never delete the
# just-installed output, and rollback removes only this call's own staging
# directory — never a concurrently created destination.
# --------------------------------------------------------------------------


def test_materializer_never_deletes_output_when_a_post_replace_check_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    source, output, _rows = _fixture(tmp_path)
    real_walk_modes = materializer._walk_modes
    call_count = {"n": 0}

    def _fail_second_call(root: Path) -> None:
        call_count["n"] += 1
        if call_count["n"] == 2:  # the post-os.replace() call on config.output
            raise RuntimeError("synthetic post-replace diagnostic failure")
        real_walk_modes(root)

    monkeypatch.setattr(materializer, "_walk_modes", _fail_second_call)
    with pytest.raises(materializer.MaterializationError) as excinfo:
        materializer.materialize(source, output, fixture=True)
    assert excinfo.value.code == "transaction_failure"
    # The rename already happened — the correctly-built output must survive
    # a later diagnostic failure untouched.
    assert output.exists()
    custody = materializer.strict_json(output / "custody-receipt.json")
    assert custody["evaluation_cycle_id"] == materializer.CYCLE007


def test_materializer_rollback_never_touches_a_concurrently_created_destination(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    source, output, _rows = _fixture(tmp_path)

    def _boom(*_args: Any, **_kwargs: Any):
        raise RuntimeError("synthetic mid-build failure")

    monkeypatch.setattr(materializer, "_packet_rows", _boom)
    # Simulate a concurrent process having already created the destination
    # with unrelated content between _validate_paths() and _build_stage().
    output.mkdir(mode=materializer.PRIVATE_DIR_MODE)
    os.chmod(output, materializer.PRIVATE_DIR_MODE)
    (output / "concurrent-marker.json").write_bytes(b"{}")
    os.chmod(output / "concurrent-marker.json", materializer.PRIVATE_FILE_MODE)
    with pytest.raises(materializer.MaterializationError) as excinfo:
        materializer.materialize(source, output, fixture=True)
    # _validate_paths refuses the pre-existing destination outright...
    assert excinfo.value.code == "output_exists"
    # ...and, crucially, never deletes it.
    assert output.exists()
    assert (output / "concurrent-marker.json").exists()


def test_materializer_toctou_race_fails_closed_when_output_appears_after_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Deterministic race: a concurrent actor wins between _validate_paths() and install.

    A plain ``os.replace(staging, output)`` would silently succeed here,
    because POSIX rename replaces an existing *empty* directory. The
    install step must instead fail closed and leave the racing actor's own
    directory untouched.
    """
    source, output, _rows = _fixture(tmp_path)
    real_mkdir = os.mkdir
    racer_ran = {"done": False}

    def _racing_mkdir(path: Any, *args: Any, **kwargs: Any) -> None:
        if Path(path) == output and not racer_ran["done"]:
            racer_ran["done"] = True
            # Simulate a concurrent actor creating the destination the
            # instant after _validate_paths()'s existence check passed —
            # an empty directory, which os.replace() would silently accept.
            real_mkdir(path, materializer.PRIVATE_DIR_MODE)
            os.chmod(path, materializer.PRIVATE_DIR_MODE)
            (Path(path) / "concurrent-marker.json").write_bytes(b"{}")
            os.chmod(Path(path) / "concurrent-marker.json", materializer.PRIVATE_FILE_MODE)
        return real_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(materializer.os, "mkdir", _racing_mkdir)
    with pytest.raises(materializer.MaterializationError) as excinfo:
        materializer.materialize(source, output, fixture=True)
    assert excinfo.value.code == "output_exists"
    assert racer_ran["done"]
    # The racing actor's own directory survives untouched — our rollback
    # only ever removes this call's own staging path.
    assert output.exists()
    assert (output / "concurrent-marker.json").exists()
    assert not (output / "custody-receipt.json").exists()
    leftovers = [path for path in tmp_path.iterdir() if path.name.startswith(f".{output.name}.staging-")]
    assert leftovers == []


def test_materializer_rolls_back_the_claimed_destination_when_a_mid_install_rename_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """A failed second install rename must leave neither a partial output nor staging debris."""
    source, output, _rows = _fixture(tmp_path)
    real_rename = os.rename
    forward_renames = {"count": 0}

    def _fail_second_forward_rename(old: Any, new: Any, *args: Any, **kwargs: Any) -> None:
        if Path(new).parent == output and Path(old).parent != output:
            forward_renames["count"] += 1
            if forward_renames["count"] == 2:
                raise OSError("synthetic mid-install rename failure")
        return real_rename(old, new, *args, **kwargs)

    monkeypatch.setattr(materializer.os, "rename", _fail_second_forward_rename)
    with pytest.raises(materializer.MaterializationError) as excinfo:
        materializer.materialize(source, output, fixture=True)
    assert excinfo.value.code == "transaction_failure"
    assert forward_renames["count"] == 2
    assert not output.exists()
    assert list(tmp_path.glob(f".{output.name}.staging-*")) == []


# --------------------------------------------------------------------------
# Amendment step 15: source package mode verification, real-mode path
# disclosure refusal (env/config only, never argv).
# --------------------------------------------------------------------------


def test_materializer_real_mode_rejects_a_world_readable_source_package(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    source, output, _rows = _fixture(tmp_path)
    os.chmod(source / "custody-receipt.json", 0o644)  # no longer mode-0600
    # Bind the frozen hashes to this fixture so we get past source_binding_drift
    # and reach the mode-verification step this test is actually about.
    custody_raw = (source / "custody-receipt.json").read_bytes()
    manifest_raw = (source / "label-manifest.json").read_bytes()
    monkeypatch.setattr(materializer, "SOURCE_CUSTODY_SHA256", materializer.digest(custody_raw))
    monkeypatch.setattr(materializer, "SOURCE_MANIFEST_SHA256", materializer.digest(manifest_raw))
    with pytest.raises(materializer.MaterializationError) as excinfo:
        materializer.materialize(source, output, fixture=False)
    assert excinfo.value.code == "source_mode_drift"
    assert not output.exists()


def test_main_real_mode_refuses_argv_source_and_output(tmp_path: Path):
    source, output, _rows = _fixture(tmp_path)
    exit_code = materializer.main(["--source", str(source), "--output", str(output)])
    assert exit_code == 2
    assert not output.exists()


def test_main_real_mode_resolves_paths_from_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    source, output, _rows = _fixture(tmp_path)
    monkeypatch.setenv(materializer.REAL_SOURCE_ENV, str(source))
    monkeypatch.setenv(materializer.REAL_OUTPUT_ENV, str(output))
    monkeypatch.delenv(materializer.REAL_CONFIG_ENV, raising=False)
    # Real mode still enforces the frozen Cycle-005 hash pins against this
    # synthetic fixture, so it fails closed on source_binding_drift — the
    # point of this test is that it reaches that check at all (i.e. argv
    # was never required and env resolution worked), not that it succeeds.
    exit_code = materializer.main([])
    assert exit_code == 2
    assert not output.exists()


# --------------------------------------------------------------------------
# Amendment (fixes v3, item 4): exact package/packet binding — duplicate
# identities across packets, claimed/actual row count drift, lane/order
# swap, raw hash drift, and ordered-commitment drift.
# --------------------------------------------------------------------------


def _rewrite_manifest(source: Path, manifest: dict[str, Any]) -> None:
    manifest = dict(manifest)
    manifest.pop("receipt_sha256", None)
    manifest["receipt_sha256"] = materializer._hash_receipt(manifest)
    manifest_path = source / "label-manifest.json"
    manifest_path.unlink()
    manifest_path.write_bytes(materializer.canonical(manifest))
    os.chmod(manifest_path, materializer.PRIVATE_FILE_MODE)


def test_materializer_rejects_duplicate_identities_across_packets(tmp_path: Path):
    source, output, _rows = _fixture(tmp_path)
    manifest = materializer.strict_json(source / "label-manifest.json")
    # Clone packet 1's first row's identity into residual_label packet 1 —
    # a duplicate unit_id/unit_sha256 across two distinct packets.
    clean_packet = materializer.strict_json(source / "clean_label" / "packet-0001.json")
    residual_path = source / "residual_label" / "packet-0001.json"
    residual_packet = materializer.strict_json(residual_path)
    residual_packet = dict(residual_packet)
    residual_packet["rows"] = [dict(clean_packet["rows"][0]), *residual_packet["rows"][1:]]
    residual_packet["packet_identity_set_sha256"] = materializer.identity_set(residual_packet["rows"])
    residual_path.unlink()
    residual_raw = materializer.canonical(residual_packet)
    residual_path.write_bytes(residual_raw)
    os.chmod(residual_path, materializer.PRIVATE_FILE_MODE)

    records = [dict(record) for record in manifest["packets"]]
    for record in records:
        if record["lane"] == "residual_label" and record["packet_index"] == 1:
            record["raw_sha256"] = materializer.digest(residual_raw)
            record["packet_identity_set_sha256"] = residual_packet["packet_identity_set_sha256"]
    manifest = dict(manifest)
    manifest["packets"] = records
    _rewrite_manifest(source, manifest)

    with pytest.raises(materializer.MaterializationError) as excinfo:
        materializer.materialize(source, output, fixture=True)
    assert excinfo.value.code == "identity_uniqueness_failure"
    assert not output.exists()


def test_materializer_rejects_claimed_actual_row_count_drift(tmp_path: Path):
    source, output, _rows = _fixture(tmp_path)
    manifest = materializer.strict_json(source / "label-manifest.json")
    records = [dict(record) for record in manifest["packets"]]
    for record in records:
        if record["lane"] == "clean_label" and record["packet_index"] == 1:
            # Claim a row_count that no longer matches the actual packet
            # file — bump the manifest's own total in lockstep so the drift
            # is only detectable against the actual packet file's row list,
            # not the manifest's internal row_count sum.
            record["row_count"] = record["row_count"] + 1
    manifest = dict(manifest)
    manifest["packets"] = records
    manifest["row_count"] = manifest["row_count"] + 1
    _rewrite_manifest(source, manifest)

    with pytest.raises(materializer.MaterializationError) as excinfo:
        materializer.materialize(source, output, fixture=True)
    assert excinfo.value.code == "packet_binding_drift"
    assert not output.exists()


def test_materializer_rejects_a_lane_order_swap(tmp_path: Path):
    source, output, _rows = _fixture(tmp_path)
    manifest = materializer.strict_json(source / "label-manifest.json")
    records = [dict(record) for record in manifest["packets"]]
    # LANE_ORDER is ("clean_label", "residual_label") — swap them so the
    # manifest's own packet list is out of frozen lane order.
    swapped = sorted(records, key=lambda record: (record["lane"] != "residual_label", record["packet_index"]))
    manifest = dict(manifest)
    manifest["packets"] = swapped
    _rewrite_manifest(source, manifest)

    with pytest.raises(materializer.MaterializationError) as excinfo:
        materializer.materialize(source, output, fixture=True)
    assert excinfo.value.code == "packet_order_failure"
    assert not output.exists()


def test_materializer_rejects_raw_packet_hash_drift(tmp_path: Path):
    source, output, _rows = _fixture(tmp_path)
    packet_path = source / "clean_label" / "packet-0001.json"
    packet = materializer.strict_json(packet_path)
    packet = dict(packet)
    packet["rows"] = [dict(row, source_text="TAMPERED-AFTER-MANIFEST-SEALED") for row in packet["rows"]]
    packet_path.unlink()
    packet_path.write_bytes(materializer.canonical(packet))
    os.chmod(packet_path, materializer.PRIVATE_FILE_MODE)
    # The manifest's raw_sha256 for this packet now drifts from the actual
    # (tampered) file bytes on disk.

    with pytest.raises(materializer.MaterializationError) as excinfo:
        materializer.materialize(source, output, fixture=True)
    assert excinfo.value.code == "packet_binding_drift"
    assert not output.exists()


def _uniform_fixture(root: Path, *, packet_size: int) -> Path:
    """A real-mode-shaped fixture: one clean_label + one residual_label packet, both exactly packet_size rows."""
    source = root / "cycle005-source-uniform"
    source.mkdir(mode=materializer.PRIVATE_DIR_MODE)
    os.chmod(source, materializer.PRIVATE_DIR_MODE)
    packet_records: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    for lane in ("clean_label", "residual_label"):
        start = len(all_rows)
        rows = [_row(start + offset, lane, include_cycle=False) for offset in range(packet_size)]
        all_rows.extend(rows)
        packet = {
            "schema_version": "phase3_cycle005_private_packet_v1",
            "evaluation_cycle_id": materializer.CYCLE005,
            "lane": lane,
            "packet_index": 1,
            "row_count": packet_size,
            "rows": rows,
            "packet_identity_set_sha256": materializer.identity_set(rows),
        }
        packet_path = source / lane / "packet-0001.json"
        packet_raw = _write(packet_path, packet)
        packet_records.append(
            {
                "lane": lane,
                "packet_index": 1,
                "canonical_basename": packet_path.name,
                "row_count": packet_size,
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
    return source


def test_materializer_recomputes_ordered_identity_and_rejects_a_claimed_commitment_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Real (non-fixture) mode never trusts a claimed ordered_identity_commitment_sha256."""
    packet_size = 2
    source = _uniform_fixture(tmp_path, packet_size=packet_size)
    output = tmp_path / "cycle007-successor-uniform"
    manifest = materializer.strict_json(source / "label-manifest.json")
    manifest = dict(manifest)
    fake_commitment = "9" * 64
    manifest["ordered_identity_commitment_sha256"] = fake_commitment
    _rewrite_manifest(source, manifest)

    custody_raw = (source / "custody-receipt.json").read_bytes()
    manifest_raw = (source / "label-manifest.json").read_bytes()
    monkeypatch.setattr(materializer, "SOURCE_CUSTODY_SHA256", materializer.digest(custody_raw))
    monkeypatch.setattr(materializer, "SOURCE_MANIFEST_SHA256", materializer.digest(manifest_raw))
    # This fixture's true (small, uniform) shape — real mode otherwise
    # enforces the frozen 40+164/2000+8159 denominator and the 50-row
    # packet size, neither of which a synthetic fixture can satisfy.
    monkeypatch.setattr(materializer, "REAL_PACKET_COUNTS", {"clean_label": 1, "residual_label": 1})
    monkeypatch.setattr(materializer, "REAL_ROW_COUNTS", {"clean_label": packet_size, "residual_label": packet_size})
    monkeypatch.setattr(materializer, "PACKET_SIZE", packet_size)
    # The manifest's claimed commitment must match the frozen pin too, or
    # the earlier pin check fires first — pin it to our fabricated value so
    # this test isolates the "recompute from actual rows" check specifically.
    monkeypatch.setattr(materializer, "ORDERED_IDENTITY_COMMITMENT_SHA256", fake_commitment)

    with pytest.raises(materializer.MaterializationError) as excinfo:
        materializer.materialize(source, output, fixture=False, strict_counts=True)
    assert excinfo.value.code == "ordered_identity_commitment_failure"
    assert not output.exists()


def test_main_real_mode_config_file_must_be_mode_0600(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    source, output, _rows = _fixture(tmp_path)
    config_path = tmp_path / "materializer-config.json"
    config_path.write_text(materializer.json.dumps({"source": str(source), "output": str(output)}))
    os.chmod(config_path, 0o644)  # world-readable — must be refused
    monkeypatch.setenv(materializer.REAL_CONFIG_ENV, str(config_path))
    monkeypatch.delenv(materializer.REAL_SOURCE_ENV, raising=False)
    monkeypatch.delenv(materializer.REAL_OUTPUT_ENV, raising=False)
    exit_code = materializer.main([])
    assert exit_code == 2
    assert not output.exists()
