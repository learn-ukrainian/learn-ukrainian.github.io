#!/usr/bin/env python3
"""Hydrate the open Word Atlas dataset from its pinned Release asset."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET_ROOT = ROOT / "data" / "lexicon-dataset"
DEFAULT_POINTER = ROOT / "data" / "lexicon-dataset.pointer.json"
ASSET_NAME = "lexicon-open-dataset.json.gz"
REQUIRED_POINTER_KEYS = (
    "asset_url",
    "release_tag",
    "package_schema_version",
    "gz_sha256",
    "package_sha256",
    "gz_bytes",
    "package_bytes",
    "file_count",
    "files",
)


class OpenDatasetHydrationError(RuntimeError):
    """Raised when the pinned open dataset cannot be hydrated."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_pointer(pointer_path: Path = DEFAULT_POINTER) -> dict[str, Any]:
    payload = json.loads(pointer_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise OpenDatasetHydrationError(f"{pointer_path} must contain a JSON object")
    missing = [key for key in REQUIRED_POINTER_KEYS if key not in payload]
    if missing:
        raise OpenDatasetHydrationError(f"{pointer_path} missing required keys: {', '.join(missing)}")
    if payload.get("package_schema_version") != 1:
        raise OpenDatasetHydrationError("unsupported open dataset package schema")
    files = payload.get("files")
    if not isinstance(files, list) or len(files) != payload.get("file_count"):
        raise OpenDatasetHydrationError("open dataset pointer file_count does not match files")
    return payload


def _download_with_gh(pointer: dict[str, Any], repo: str) -> bytes | None:
    release_tag = pointer.get("release_tag")
    if not isinstance(release_tag, str) or not release_tag:
        return None
    try:
        result = subprocess.run(
            [
                "gh",
                "release",
                "download",
                release_tag,
                "-p",
                ASSET_NAME,
                "-O",
                "-",
                "--repo",
                repo,
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def download_asset(pointer: dict[str, Any], *, repo: str) -> bytes:
    gh_bytes = _download_with_gh(pointer, repo)
    if gh_bytes is not None:
        return gh_bytes

    asset_url = pointer.get("asset_url")
    if not isinstance(asset_url, str) or not asset_url:
        raise OpenDatasetHydrationError("open dataset pointer lacks asset_url")
    request = Request(asset_url, headers={"User-Agent": "learn-ukrainian-open-dataset-hydrate/1.0"})
    with urlopen(request, timeout=60) as response:
        return response.read()


def _safe_output_path(dataset_root: Path, rel_path: str) -> Path:
    if rel_path.startswith("/") or ".." in Path(rel_path).parts:
        raise OpenDatasetHydrationError(f"unsafe open dataset path in package: {rel_path!r}")
    return dataset_root / rel_path


def hydrate_open_dataset(
    *,
    pointer_path: Path = DEFAULT_POINTER,
    dataset_root: Path = DEFAULT_DATASET_ROOT,
    package_path: Path | None = None,
    repo: str = "learn-ukrainian/learn-ukrainian.github.io",
) -> dict[str, Any]:
    pointer = read_pointer(pointer_path)
    gzip_bytes = package_path.read_bytes() if package_path else download_asset(pointer, repo=repo)
    gz_sha = _sha256(gzip_bytes)
    if gz_sha != pointer["gz_sha256"]:
        raise OpenDatasetHydrationError(f"open dataset gz sha mismatch: expected {pointer['gz_sha256']}, got {gz_sha}")
    if len(gzip_bytes) != pointer["gz_bytes"]:
        raise OpenDatasetHydrationError(f"open dataset gz byte mismatch: expected {pointer['gz_bytes']}, got {len(gzip_bytes)}")

    package_bytes = gzip.decompress(gzip_bytes)
    package_sha = _sha256(package_bytes)
    if package_sha != pointer["package_sha256"]:
        raise OpenDatasetHydrationError(
            f"open dataset package sha mismatch: expected {pointer['package_sha256']}, got {package_sha}"
        )
    if len(package_bytes) != pointer["package_bytes"]:
        raise OpenDatasetHydrationError(
            f"open dataset package byte mismatch: expected {pointer['package_bytes']}, got {len(package_bytes)}"
        )

    package = json.loads(package_bytes.decode("utf-8"))
    if not isinstance(package, dict) or package.get("schema") != "atlas-open-dataset-package":
        raise OpenDatasetHydrationError("open dataset package has unexpected schema")
    if package.get("schemaVersion") != pointer["package_schema_version"]:
        raise OpenDatasetHydrationError("open dataset package schema version does not match pointer")
    package_files = package.get("files")
    if not isinstance(package_files, list) or len(package_files) != pointer["file_count"]:
        raise OpenDatasetHydrationError("open dataset package file_count does not match pointer")

    expected_by_path = {
        file_info["path"]: file_info
        for file_info in pointer["files"]
        if isinstance(file_info, dict) and isinstance(file_info.get("path"), str)
    }
    if len(expected_by_path) != pointer["file_count"]:
        raise OpenDatasetHydrationError("open dataset pointer has duplicate or invalid file entries")

    temp_root = dataset_root.with_name(f"{dataset_root.name}.tmp")
    if temp_root.exists():
        shutil.rmtree(temp_root)
    temp_root.mkdir(parents=True, exist_ok=True)
    try:
        seen: set[str] = set()
        for file_payload in package_files:
            if not isinstance(file_payload, dict):
                raise OpenDatasetHydrationError("open dataset package file entry must be object")
            rel_path = file_payload.get("path")
            content = file_payload.get("content")
            if not isinstance(rel_path, str) or not isinstance(content, str):
                raise OpenDatasetHydrationError("open dataset package file entry missing path/content")
            expected = expected_by_path.get(rel_path)
            if expected is None:
                raise OpenDatasetHydrationError(f"open dataset package contains unexpected file {rel_path}")
            data = content.encode("utf-8")
            if len(data) != expected["bytes"] or _sha256(data) != expected["sha256"]:
                raise OpenDatasetHydrationError(f"open dataset package file digest mismatch for {rel_path}")
            out_path = _safe_output_path(temp_root, rel_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(data)
            seen.add(rel_path)
        missing = sorted(set(expected_by_path) - seen)
        if missing:
            raise OpenDatasetHydrationError(f"open dataset package missing files: {', '.join(missing[:5])}")
        if dataset_root.exists():
            shutil.rmtree(dataset_root)
        temp_root.replace(dataset_root)
    except Exception:
        if temp_root.exists():
            shutil.rmtree(temp_root)
        raise

    return {
        "file_count": pointer["file_count"],
        "generated_at": pointer.get("generated_at"),
        "manifest_version": pointer.get("manifest_version"),
        "manifest_stats": pointer.get("manifest_stats", {}),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pointer", type=Path, default=DEFAULT_POINTER)
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--package", type=Path, default=None, help="Read a local gzipped package instead of downloading")
    parser.add_argument("--repo", default="learn-ukrainian/learn-ukrainian.github.io")
    args = parser.parse_args()
    result = hydrate_open_dataset(
        pointer_path=args.pointer,
        dataset_root=args.dataset_root,
        package_path=args.package,
        repo=args.repo,
    )
    print(
        "✓ hydrated open dataset "
        f"{result['file_count']} files from manifest {result['manifest_version']} "
        f"generated {result['generated_at']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
