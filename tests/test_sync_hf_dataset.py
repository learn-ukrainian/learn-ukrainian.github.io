"""Unit tests for Hugging Face dataset sync script (#7873)."""

from pathlib import Path

import pytest

from scripts.audio.sync_hf_dataset import (
    scan_local_files,
    sync_hf_dataset,
)


def test_scan_local_files(tmp_path: Path):
    (tmp_path / "a.opus").write_bytes(b"opus")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub/b.opus").write_bytes(b"opus2")
    (tmp_path / "manifest.json").write_text("{}")
    (tmp_path / "ignored.txt").write_text("ignore")

    files = scan_local_files(tmp_path)
    names = {f.name for f in files}
    assert names == {"a.opus", "b.opus", "manifest.json"}


def test_sync_hf_dataset_requires_token(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    with pytest.raises(ValueError, match="HF_TOKEN"):
        sync_hf_dataset(tmp_path, repo_id="test/repo", token=None, dry_run=False)
