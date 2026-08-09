"""Tests for open dataset shard export integrity, sha256 recording, and atomic file renames."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.lexicon import export_open_dataset as export_mod


def test_export_open_dataset_integrity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest_path = tmp_path / "lexicon-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "version": "0.1",
                "entries": [
                    {"lemma": "абзац", "url_slug": "абзац", "gloss": "paragraph"},
                    {"lemma": "базар", "url_slug": "базар", "gloss": "bazaar"},
                    {"lemma": "123", "url_slug": "123", "gloss": "numbers"},
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    dataset_root = tmp_path / "lexicon-dataset"
    dataset_dir = dataset_root / "dataset"

    monkeypatch.setattr(export_mod, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(export_mod, "DATASET_ROOT", dataset_root)
    monkeypatch.setattr(export_mod, "DATASET_DIR", dataset_dir)

    entry_count, shard_count = export_mod.export_dataset()

    assert entry_count == 3
    assert shard_count == 3
    assert (dataset_root / "ATTRIBUTION.md").exists()
    assert (dataset_root / "NOTICE.md").exists()
    assert (dataset_root / "README.md").exists()

    meta_file = dataset_dir / "_metadata.json"
    assert meta_file.exists()
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    assert "shard_integrity" in meta
    integrity = meta["shard_integrity"]

    for shard_name, info in integrity.items():
        shard_file = dataset_dir / shard_name
        assert shard_file.exists()
        assert "sha256" in info
        assert "bytes" in info
        assert "entries" in info
        assert shard_file.stat().st_size == info["bytes"]

        # Verify no tmp files remain
        assert not (dataset_dir / f"{shard_name}.tmp").exists()

    assert not (dataset_dir / "_metadata.json.tmp").exists()
