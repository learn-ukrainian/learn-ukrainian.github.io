from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.open_dataset.hydrate import OpenDatasetHydrationError, _download_with_gh, hydrate_open_dataset
from scripts.open_dataset.publish import publish_open_dataset, write_pointer


def _write_fixture_dataset(root: Path) -> None:
    (root / "dataset").mkdir(parents=True)
    (root / "README.md").write_text("# Dataset\n", encoding="utf-8")
    (root / "ATTRIBUTION.md").write_text("# Attribution\n", encoding="utf-8")
    (root / "NOTICE.md").write_text("# Notice\n", encoding="utf-8")
    (root / "dataset" / "_metadata.json").write_text(
        json.dumps(
            {
                "version": "0.1",
                "generated_at": "2026-06-30T00:00:00+00:00",
                "stats": {"lemmas_total": 2, "form_of_count": 1},
            }
        ),
        encoding="utf-8",
    )
    (root / "dataset" / "А.jsonl").write_text(
        json.dumps({"lemma": "абетка", "url_slug": "абетка"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def test_open_dataset_publish_pointer_and_hydrate_round_trip(tmp_path: Path) -> None:
    dataset_root = tmp_path / "dataset-source"
    _write_fixture_dataset(dataset_root)
    gzip_path = tmp_path / "lexicon-open-dataset.json.gz"
    pointer_path = tmp_path / "lexicon-dataset.pointer.json"

    pointer = publish_open_dataset(
        dataset_root=dataset_root,
        gzip_path=gzip_path,
        pointer_path=pointer_path,
        release_tag="test-open-dataset",
        repo="example/repo",
        dry_run=True,
    )
    write_pointer(pointer_path, pointer)

    assert pointer["file_count"] == 5
    assert pointer["manifest_stats"] == {"lemmas_total": 2, "form_of_count": 1}
    assert {file_info["path"] for file_info in pointer["files"]} == {
        "ATTRIBUTION.md",
        "NOTICE.md",
        "README.md",
        "dataset/_metadata.json",
        "dataset/А.jsonl",
    }

    hydrated_root = tmp_path / "hydrated"
    result = hydrate_open_dataset(
        pointer_path=pointer_path,
        dataset_root=hydrated_root,
        package_path=gzip_path,
        repo="example/repo",
    )

    assert result["file_count"] == 5
    assert json.loads((hydrated_root / "dataset" / "_metadata.json").read_text(encoding="utf-8"))["stats"][
        "lemmas_total"
    ] == 2
    assert "абетка" in (hydrated_root / "dataset" / "А.jsonl").read_text(encoding="utf-8")


def test_open_dataset_hydrate_rejects_digest_mismatch(tmp_path: Path) -> None:
    dataset_root = tmp_path / "dataset-source"
    _write_fixture_dataset(dataset_root)
    gzip_path = tmp_path / "lexicon-open-dataset.json.gz"
    pointer_path = tmp_path / "lexicon-dataset.pointer.json"
    pointer = publish_open_dataset(
        dataset_root=dataset_root,
        gzip_path=gzip_path,
        pointer_path=pointer_path,
        release_tag="test-open-dataset",
        repo="example/repo",
        dry_run=True,
    )
    pointer["gz_sha256"] = "0" * 64
    write_pointer(pointer_path, pointer)

    with pytest.raises(OpenDatasetHydrationError, match="gz sha mismatch"):
        hydrate_open_dataset(
            pointer_path=pointer_path,
            dataset_root=tmp_path / "hydrated",
            package_path=gzip_path,
            repo="example/repo",
        )


def test_open_dataset_gh_download_missing_binary_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing_gh(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
        raise FileNotFoundError("gh")

    monkeypatch.setattr(subprocess, "run", missing_gh)

    assert _download_with_gh({"release_tag": "atlas-open-dataset"}, repo="example/repo") is None
