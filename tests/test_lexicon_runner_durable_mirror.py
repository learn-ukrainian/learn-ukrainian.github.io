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

    manifest = snapshot(str(source), mirror)

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
    snapshot(str(source), mirror)

    (source / "network-cache.sqlite").unlink()
    manifest = snapshot(str(source), mirror)

    assert not (mirror / "network-cache.sqlite").exists()
    assert "network-cache.sqlite" not in {entry["path"] for entry in manifest["files"]}


def test_verify_detects_corruption(tmp_path: Path) -> None:
    source = tmp_path / "work"
    mirror = tmp_path / "mirror"
    _populate(source)
    snapshot(str(source), mirror)

    (mirror / "ledger.sqlite").write_bytes(b"corrupted")

    result = verify_manifest(read_manifest(mirror), mirror)
    assert not result.ok
    assert "ledger.sqlite" in result.mismatched


def test_verify_detects_missing_file(tmp_path: Path) -> None:
    source = tmp_path / "work"
    mirror = tmp_path / "mirror"
    _populate(source)
    snapshot(str(source), mirror)

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
    manifest = snapshot(str(source), mirror)
    manifest["generated_at"] = stale_time
    write_manifest(manifest, mirror)

    with pytest.raises(DurableMirrorError, match="old"):
        require_durable(mirror, max_age_hours=24.0)


def test_require_durable_fails_closed_on_corruption(tmp_path: Path) -> None:
    source = tmp_path / "work"
    mirror = tmp_path / "mirror"
    _populate(source)
    snapshot(str(source), mirror)
    (mirror / "ledger.sqlite").write_bytes(b"tampered")

    with pytest.raises(DurableMirrorError, match="failed verification"):
        require_durable(mirror)


def test_require_durable_succeeds_for_fresh_verified_mirror(tmp_path: Path) -> None:
    source = tmp_path / "work"
    mirror = tmp_path / "mirror"
    _populate(source)
    snapshot(str(source), mirror)

    manifest = require_durable(mirror)
    assert manifest["file_count"] == 4


def test_cli_snapshot_then_verify_then_require(tmp_path: Path) -> None:
    source = tmp_path / "work"
    mirror = tmp_path / "mirror"
    _populate(source)

    assert main(["snapshot", "--source", str(source), "--mirror-dir", str(mirror)]) == 0
    assert main(["verify", "--mirror-dir", str(mirror)]) == 0
    assert main(["require", "--mirror-dir", str(mirror)]) == 0


def test_cli_require_exits_nonzero_when_not_durable(tmp_path: Path) -> None:
    mirror = tmp_path / "missing-mirror"
    assert main(["require", "--mirror-dir", str(mirror)]) == 2


def test_cli_dry_run_snapshot_does_not_write_manifest(tmp_path: Path) -> None:
    source = tmp_path / "work"
    mirror = tmp_path / "mirror"
    _populate(source)

    assert main(["snapshot", "--source", str(source), "--mirror-dir", str(mirror), "--dry-run"]) == 0
    assert not (mirror / "manifest.json").exists()
