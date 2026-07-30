"""Durable local mirror for the Atlas 20k runner work-dir (#5884, sibling of #6014)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from scripts.lexicon.runner.durable_mirror import (
    DurableMirrorError,
    build_manifest,
    main,
    read_manifest,
    require_durable,
    snapshot,
    verify_manifest,
    write_manifest,
)


def _populate(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "ledger.sqlite").write_bytes(b"fake-ledger-bytes")
    (root / "network-cache.sqlite").write_bytes(b"fake-cache-bytes")
    sub = root / "offline_enrich"
    sub.mkdir()
    (sub / "candidate-enriched.json").write_text('{"entries": []}\n', encoding="utf-8")
    (root / "enrich.log").write_text("noop\n", encoding="utf-8")
    (root / "enrich-driver.pid").write_text("12345\n", encoding="utf-8")
    (root / ".DS_Store").write_bytes(b"\x00")


def test_build_manifest_excludes_pid_and_ds_store(tmp_path: Path) -> None:
    source = tmp_path / "work"
    _populate(source)

    manifest = build_manifest(source)

    paths = {entry["path"] for entry in manifest["files"]}
    assert paths == {
        "ledger.sqlite",
        "network-cache.sqlite",
        "offline_enrich/candidate-enriched.json",
        "enrich.log",
    }
    assert manifest["file_count"] == 4
    assert manifest["total_bytes"] == sum((source / p).stat().st_size for p in paths)


def test_snapshot_syncs_and_writes_verifiable_manifest(tmp_path: Path) -> None:
    source = tmp_path / "work"
    mirror = tmp_path / "mirror"
    _populate(source)

    manifest = snapshot(str(source), mirror, allow_live=True)

    assert (mirror / "manifest.json").is_file()
    assert (mirror / "ledger.sqlite").read_bytes() == b"fake-ledger-bytes"
    assert (mirror / "offline_enrich" / "candidate-enriched.json").is_file()
    assert not (mirror / "enrich-driver.pid").exists()
    assert not (mirror / ".DS_Store").exists()

    result = verify_manifest(read_manifest(mirror), mirror)
    assert result.ok, result


def test_snapshot_delete_removes_stale_mirror_files(tmp_path: Path) -> None:
    source = tmp_path / "work"
    mirror = tmp_path / "mirror"
    _populate(source)
    snapshot(str(source), mirror, allow_live=True)

    (source / "network-cache.sqlite").unlink()
    manifest = snapshot(str(source), mirror, allow_live=True)

    assert not (mirror / "network-cache.sqlite").exists()
    assert "network-cache.sqlite" not in {entry["path"] for entry in manifest["files"]}


def test_verify_detects_corruption(tmp_path: Path) -> None:
    source = tmp_path / "work"
    mirror = tmp_path / "mirror"
    _populate(source)
    snapshot(str(source), mirror, allow_live=True)

    (mirror / "ledger.sqlite").write_bytes(b"corrupted")

    result = verify_manifest(read_manifest(mirror), mirror)
    assert not result.ok
    assert "ledger.sqlite" in result.mismatched


def test_verify_detects_missing_file(tmp_path: Path) -> None:
    source = tmp_path / "work"
    mirror = tmp_path / "mirror"
    _populate(source)
    snapshot(str(source), mirror, allow_live=True)

    (mirror / "enrich.log").unlink()

    result = verify_manifest(read_manifest(mirror), mirror)
    assert not result.ok
    assert "enrich.log" in result.missing


def test_require_durable_fails_closed_when_mirror_absent(tmp_path: Path) -> None:
    mirror = tmp_path / "missing-mirror"
    with pytest.raises(DurableMirrorError, match="no durable mirror manifest"):
        require_durable(mirror)


def test_require_durable_fails_closed_when_empty(tmp_path: Path) -> None:
    mirror = tmp_path / "empty-mirror"
    mirror.mkdir()
    write_manifest(build_manifest(mirror), mirror)

    with pytest.raises(DurableMirrorError, match="empty"):
        require_durable(mirror)


def test_require_durable_fails_closed_when_stale(tmp_path: Path) -> None:
    source = tmp_path / "work"
    mirror = tmp_path / "mirror"
    _populate(source)
    stale_time = time.time() - 48 * 3600
    manifest = snapshot(str(source), mirror, allow_live=True)
    manifest["generated_at"] = stale_time
    write_manifest(manifest, mirror)

    with pytest.raises(DurableMirrorError, match="old"):
        require_durable(mirror, max_age_hours=24.0)


def test_require_durable_fails_closed_on_corruption(tmp_path: Path) -> None:
    source = tmp_path / "work"
    mirror = tmp_path / "mirror"
    _populate(source)
    snapshot(str(source), mirror, allow_live=True)
    (mirror / "ledger.sqlite").write_bytes(b"tampered")

    with pytest.raises(DurableMirrorError, match="failed verification"):
        require_durable(mirror)


def test_require_durable_succeeds_for_fresh_verified_mirror(tmp_path: Path) -> None:
    source = tmp_path / "work"
    mirror = tmp_path / "mirror"
    _populate(source)
    snapshot(str(source), mirror, allow_live=True)

    manifest = require_durable(mirror)
    assert manifest["file_count"] == 4


def test_cli_snapshot_then_verify_then_require(tmp_path: Path) -> None:
    source = tmp_path / "work"
    mirror = tmp_path / "mirror"
    _populate(source)

    assert main(["snapshot", "--source", str(source), "--mirror-dir", str(mirror), "--allow-live"]) == 0
    assert main(["verify", "--mirror-dir", str(mirror)]) == 0
    assert main(["require", "--mirror-dir", str(mirror)]) == 0


def test_cli_require_exits_nonzero_when_not_durable(tmp_path: Path) -> None:
    mirror = tmp_path / "missing-mirror"
    assert main(["require", "--mirror-dir", str(mirror)]) == 2


def test_cli_dry_run_snapshot_does_not_write_manifest(tmp_path: Path) -> None:
    source = tmp_path / "work"
    mirror = tmp_path / "mirror"
    _populate(source)

    assert main(["snapshot", "--source", str(source), "--mirror-dir", str(mirror), "--dry-run", "--allow-live"]) == 0
    assert not (mirror / "manifest.json").exists()


def test_verify_fails_when_extra_files_present(tmp_path: Path) -> None:
    """F001: unexpected files in the mirror are verification failures."""
    source = tmp_path / "work"
    mirror = tmp_path / "mirror"
    _populate(source)
    snapshot(str(source), mirror, allow_live=True)
    (mirror / "sneaky.extra").write_text("nope", encoding="utf-8")
    manifest = read_manifest(mirror)
    result = verify_manifest(manifest, mirror)
    assert result.ok is False
    assert any(path.endswith("sneaky.extra") or path == "sneaky.extra" for path in result.extra)


def test_require_durable_fails_on_future_generated_at(tmp_path: Path) -> None:
    """F002: future-dated manifests fail closed (not treated as age zero)."""
    source = tmp_path / "work"
    mirror = tmp_path / "mirror"
    _populate(source)
    snapshot(str(source), mirror, allow_live=True)
    manifest = read_manifest(mirror)
    manifest["generated_at"] = time.time() + 3600
    write_manifest(manifest, mirror)
    with pytest.raises(DurableMirrorError, match="future"):
        require_durable(mirror, max_age_hours=24.0)


def test_verify_rejects_path_escape(tmp_path: Path) -> None:
    source = tmp_path / "work"
    mirror = tmp_path / "mirror"
    _populate(source)
    snapshot(str(source), mirror, allow_live=True)
    manifest = read_manifest(mirror)
    manifest["files"].append({"path": "../outside.txt", "bytes": 1, "sha256": "0" * 64})
    write_manifest(manifest, mirror)
    with pytest.raises(DurableMirrorError, match="unsafe|escape"):
        verify_manifest(read_manifest(mirror), mirror)


def test_read_manifest_rejects_invalid_json(tmp_path: Path) -> None:
    mirror = tmp_path / "mirror"
    mirror.mkdir()
    (mirror / "manifest.json").write_text("{not-json", encoding="utf-8")
    with pytest.raises(DurableMirrorError, match="unreadable"):
        read_manifest(mirror)


def test_require_rejects_nan_max_age(tmp_path: Path) -> None:
    source = tmp_path / "work"
    mirror = tmp_path / "mirror"
    _populate(source)
    snapshot(str(source), mirror, allow_live=True)
    with pytest.raises(DurableMirrorError, match="invalid max_age"):
        require_durable(mirror, max_age_hours=float("nan"))


def test_snapshot_refuses_live_pid_by_default(tmp_path: Path) -> None:
    source = tmp_path / "work"
    mirror = tmp_path / "mirror"
    _populate(source)
    with pytest.raises(DurableMirrorError, match="live runner"):
        snapshot(str(source), mirror, allow_live=False)


def test_require_rejects_bad_generated_at(tmp_path: Path) -> None:
    source = tmp_path / "work"
    mirror = tmp_path / "mirror"
    _populate(source)
    snapshot(str(source), mirror, allow_live=True)
    manifest = read_manifest(mirror)
    manifest["generated_at"] = "not-a-number"
    write_manifest(manifest, mirror)
    with pytest.raises(DurableMirrorError, match="invalid generated_at"):
        require_durable(mirror)
