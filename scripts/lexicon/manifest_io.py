"""Hydrate and load the release-pinned Atlas lexicon manifest."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import urllib.request
from contextlib import suppress
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
DEFAULT_POINTER = ROOT / "site" / "src" / "data" / "lexicon-manifest.pointer.json"
RECOVERY_COMMAND = (
    "gh release download atlas-manifest -p lexicon-manifest.json.gz -O - "
    "| gunzip -c > site/src/data/lexicon-manifest.json"
)
REQUIRED_POINTER_KEYS = (
    "asset_url",
    "release_tag",
    "gz_sha256",
    "json_sha256",
    "gz_bytes",
    "json_bytes",
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _repo_path(path: Path | str) -> Path:
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = ROOT / resolved
    return resolved


def _is_default_manifest(path: Path) -> bool:
    return path.resolve() == DEFAULT_MANIFEST.resolve()


def _load_pointer() -> dict[str, Any]:
    pointer = json.loads(DEFAULT_POINTER.read_text(encoding="utf-8"))
    if not isinstance(pointer, dict):
        raise ValueError(f"{DEFAULT_POINTER} must contain a JSON object")
    missing = [key for key in REQUIRED_POINTER_KEYS if key not in pointer]
    if missing:
        raise ValueError(f"{DEFAULT_POINTER} missing required keys: {', '.join(missing)}")
    return pointer


def _decode_manifest(data: bytes, source: Path | str) -> dict[str, Any]:
    manifest = json.loads(data.decode("utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError(f"{source} must contain a JSON object")
    return manifest


def _read_local(path: Path) -> dict[str, Any]:
    return _decode_manifest(path.read_bytes(), path)


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    try:
        tmp_path.write_bytes(data)
        os.replace(tmp_path, path)
    finally:
        with suppress(FileNotFoundError):
            tmp_path.unlink()


def _download(pointer: dict[str, Any]) -> bytes:
    with urllib.request.urlopen(pointer["asset_url"], timeout=60) as response:
        return response.read()


def _hydrate(path: Path, pointer: dict[str, Any]) -> dict[str, Any]:
    gz_bytes = _download(pointer)
    gz_sha = _sha256(gz_bytes)
    if gz_sha != pointer["gz_sha256"]:
        raise ValueError(
            "gz sha256 mismatch: "
            f"expected {pointer['gz_sha256']}, got {gz_sha}. "
            f"Manual recovery command: {RECOVERY_COMMAND}"
        )

    json_bytes = gzip.decompress(gz_bytes)
    json_sha = _sha256(json_bytes)
    if json_sha != pointer["json_sha256"]:
        raise ValueError(
            "json sha256 mismatch after gzip decompress: "
            f"expected {pointer['json_sha256']}, got {json_sha}. "
            f"Manual recovery command: {RECOVERY_COMMAND}"
        )

    manifest = _decode_manifest(json_bytes, pointer["asset_url"])
    _write_atomic(path, json_bytes)
    return manifest


def load_manifest(path: Path | str = DEFAULT_MANIFEST) -> dict[str, Any]:
    """Load the Atlas manifest, hydrating the release-pinned default path if needed.

    Explicit alternate paths are treated as local fixture/override manifests to
    preserve existing CLI behavior for verification scripts.
    """

    manifest_path = _repo_path(path)
    if not _is_default_manifest(manifest_path):
        return _read_local(manifest_path)

    pointer = _load_pointer()
    if manifest_path.exists():
        data = manifest_path.read_bytes()
        if _sha256(data) == pointer["json_sha256"]:
            return _decode_manifest(data, manifest_path)

    return _hydrate(manifest_path, pointer)
