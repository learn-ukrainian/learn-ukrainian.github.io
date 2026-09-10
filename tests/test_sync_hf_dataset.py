"""Unit tests for Hugging Face dataset sync script (#7873)."""

from pathlib import Path

import pytest

from scripts.audio.sync_hf_dataset import (
    ensure_dataset_card,
    scan_local_files,
    sync_hf_dataset,
)


def test_ensure_dataset_card_creates_readme(tmp_path: Path):
    readme = ensure_dataset_card(tmp_path)
    assert readme.is_file()
    text = readme.read_text(encoding="utf-8")
    assert "license: cc-by-nc-4.0" in text
    assert "Word Atlas & Practice Hub Ukrainian Audio Dataset" in text
    assert "crypto.subtle.digest" in text


def test_scan_local_files(tmp_path: Path):
    (tmp_path / "a.opus").write_bytes(b"opus")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub/b.opus").write_bytes(b"opus2")
    (tmp_path / "manifest.json").write_text("{}")
    (tmp_path / "ignored.txt").write_text("ignore")

    files = scan_local_files(tmp_path)
    names = {f.name for f in files}
    assert names == {"a.opus", "b.opus", "manifest.json"}


def test_sync_hf_dataset_dry_run(tmp_path: Path):
    (tmp_path / "clip.opus").write_bytes(b"OggS" + b"X" * 1500)
    result = sync_hf_dataset(tmp_path, repo_id="test/repo", dry_run=True)
    assert result["dry_run"] is True
    assert result["opus_files"] == 1
    assert result["total_files"] == 2  # clip.opus + generated README.md
    assert result["repo_id"] == "test/repo"


def test_sync_hf_dataset_requires_token(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    with pytest.raises(ValueError, match="HF_TOKEN"):
        sync_hf_dataset(tmp_path, repo_id="test/repo", token=None, dry_run=False)


def test_sync_hf_dataset_cli_subprocess(tmp_path: Path):
    import os
    import subprocess
    import sys

    (tmp_path / "test.opus").write_bytes(b"OggS" + b"X" * 1500)

    env = os.environ.copy()
    env.pop("PYTHONPATH", None)

    script_path = Path(__file__).resolve().parents[1] / "scripts/audio/sync_hf_dataset.py"
    proc = subprocess.run(
        [sys.executable, str(script_path), "--local-dir", str(tmp_path), "--dry-run"],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    assert proc.returncode == 0, f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "Hugging Face dataset sync status:" in proc.stdout
    assert "'dry_run': True" in proc.stdout
