#!/usr/bin/env python3
"""Publish the open Word Atlas dataset as a GitHub Release asset."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET_ROOT = ROOT / "data" / "lexicon-dataset"
DEFAULT_POINTER = ROOT / "data" / "lexicon-dataset.pointer.json"
DEFAULT_GZIP = ROOT / "data" / "lexicon-open-dataset.json.gz"
DEFAULT_RELEASE_TAG = "atlas-open-dataset"
DEFAULT_REPO = "learn-ukrainian/learn-ukrainian.github.io"
ASSET_NAME = "lexicon-open-dataset.json.gz"
REQUIRED_DATASET_FILES = (
    "README.md",
    "ATTRIBUTION.md",
    "NOTICE.md",
    "dataset/_metadata.json",
)


class OpenDatasetPublishError(RuntimeError):
    """Raised when the open dataset package cannot be published."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _asset_url(repo: str, release_tag: str, asset_name: str = ASSET_NAME) -> str:
    return f"https://github.com/{repo}/releases/download/{release_tag}/{quote(asset_name)}"


def _load_metadata(dataset_root: Path) -> dict[str, Any]:
    metadata_path = dataset_root / "dataset" / "_metadata.json"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise OpenDatasetPublishError(f"{metadata_path} missing") from exc
    if not isinstance(metadata, dict):
        raise OpenDatasetPublishError(f"{metadata_path} must contain a JSON object")
    return metadata


def collect_dataset(dataset_root: Path = DEFAULT_DATASET_ROOT) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, str]]]:
    """Collect dataset files and metadata for a deterministic package."""

    if not dataset_root.exists():
        raise OpenDatasetPublishError(f"{dataset_root} missing; run scripts/lexicon/export_open_dataset.py first")
    missing = [path for path in REQUIRED_DATASET_FILES if not (dataset_root / path).exists()]
    if missing:
        raise OpenDatasetPublishError(f"{dataset_root} missing required files: {', '.join(missing)}")

    metadata = _load_metadata(dataset_root)
    pointer_files: list[dict[str, Any]] = []
    package_files: list[dict[str, str]] = []
    for path in sorted(p for p in dataset_root.rglob("*") if p.is_file()):
        rel_path = path.relative_to(dataset_root).as_posix()
        data = path.read_bytes()
        pointer_files.append(
            {
                "path": rel_path,
                "bytes": len(data),
                "sha256": _sha256(data),
            }
        )
        package_files.append(
            {
                "path": rel_path,
                "content": data.decode("utf-8"),
            }
        )
    if not package_files:
        raise OpenDatasetPublishError(f"{dataset_root} contains no files")
    return metadata, pointer_files, package_files


def build_package(metadata: dict[str, Any], files: list[dict[str, str]]) -> bytes:
    package = {
        "schema": "atlas-open-dataset-package",
        "schemaVersion": 1,
        "generated_at": metadata.get("generated_at"),
        "manifest_version": metadata.get("version"),
        "manifest_stats": metadata.get("stats", {}),
        "files": files,
    }
    return json.dumps(package, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_pointer(
    *,
    metadata: dict[str, Any],
    pointer_files: list[dict[str, Any]],
    package_bytes: bytes,
    gzip_bytes: bytes,
    release_tag: str = DEFAULT_RELEASE_TAG,
    repo: str = DEFAULT_REPO,
) -> dict[str, Any]:
    return {
        "asset_url": _asset_url(repo, release_tag),
        "release_tag": release_tag,
        "package_schema_version": 1,
        "generated_at": metadata.get("generated_at"),
        "manifest_version": metadata.get("version"),
        "manifest_stats": metadata.get("stats", {}),
        "gz_sha256": _sha256(gzip_bytes),
        "package_sha256": _sha256(package_bytes),
        "gz_bytes": len(gzip_bytes),
        "package_bytes": len(package_bytes),
        "file_count": len(pointer_files),
        "files": pointer_files,
        "note": "Pins the open Word Atlas dataset for #3449; hydrate it from the Release asset instead of committing shards.",
    }


def write_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    pointer_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = pointer_path.with_suffix(f"{pointer_path.suffix}.tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp_path.replace(pointer_path)


def ensure_release(release_tag: str, repo: str) -> None:
    existing = subprocess.run(
        ["gh", "release", "view", release_tag, "--repo", repo],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if existing.returncode == 0:
        return
    subprocess.run(
        [
            "gh",
            "release",
            "create",
            release_tag,
            "--repo",
            repo,
            "--title",
            "Word Atlas open dataset",
            "--notes",
            "Release asset storage for the open Word Atlas lexicon dataset.",
        ],
        check=True,
    )


def upload_release_asset(gzip_path: Path, *, release_tag: str, repo: str) -> None:
    ensure_release(release_tag, repo)
    subprocess.run(
        [
            "gh",
            "release",
            "upload",
            release_tag,
            str(gzip_path),
            "--repo",
            repo,
            "--clobber",
        ],
        check=True,
    )


def publish_open_dataset(
    *,
    dataset_root: Path = DEFAULT_DATASET_ROOT,
    gzip_path: Path = DEFAULT_GZIP,
    pointer_path: Path = DEFAULT_POINTER,
    release_tag: str = DEFAULT_RELEASE_TAG,
    repo: str = DEFAULT_REPO,
    dry_run: bool = False,
) -> dict[str, Any]:
    metadata, pointer_files, package_files = collect_dataset(dataset_root)
    package_bytes = build_package(metadata, package_files)
    gzip_bytes = gzip.compress(package_bytes, compresslevel=9, mtime=0)
    gzip_path.parent.mkdir(parents=True, exist_ok=True)
    gzip_path.write_bytes(gzip_bytes)
    pointer = build_pointer(
        metadata=metadata,
        pointer_files=pointer_files,
        package_bytes=package_bytes,
        gzip_bytes=gzip_bytes,
        release_tag=release_tag,
        repo=repo,
    )
    if dry_run:
        return pointer
    upload_release_asset(gzip_path, release_tag=release_tag, repo=repo)
    write_pointer(pointer_path, pointer)
    return pointer


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--gzip", type=Path, default=DEFAULT_GZIP)
    parser.add_argument("--pointer", type=Path, default=DEFAULT_POINTER)
    parser.add_argument("--release-tag", default=DEFAULT_RELEASE_TAG)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--dry-run", action="store_true", help="Build package metadata without uploading/writing pointer")
    args = parser.parse_args()
    pointer = publish_open_dataset(
        dataset_root=args.dataset_root,
        gzip_path=args.gzip,
        pointer_path=args.pointer,
        release_tag=args.release_tag,
        repo=args.repo,
        dry_run=args.dry_run,
    )
    print(
        "Word Atlas open dataset pointer "
        f"{'would publish' if args.dry_run else 'published'}: "
        f"{pointer['manifest_version']} {pointer['generated_at']} {pointer['file_count']} files"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
