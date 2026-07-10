"""Hydrate and load the release-pinned Atlas lexicon manifest."""

from __future__ import annotations

import gzip
import hashlib
import http.client
import json
import os
import urllib.error
import urllib.parse
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
STALE_POINTER_HINT = (
    "If your branch predates the latest manifest publish, its committed pointer is stale — "
    "update the branch from origin/main (gh pr update-branch <N> / git merge origin/main). "
    "Re-downloading cannot fix a stale pointer."
)
REQUIRED_POINTER_KEYS = (
    "asset_url",
    "release_tag",
    "gz_sha256",
    "json_sha256",
    "gz_bytes",
    "json_bytes",
)
DOWNLOAD_ATTEMPTS = 3


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


def serialize_manifest(manifest: dict[str, Any]) -> bytes:
    """Return the canonical UTF-8 serialization for a lexicon manifest."""
    return (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write_manifest(path: Path | str, manifest: dict[str, Any]) -> None:
    """Atomically write a manifest using its canonical serialization."""
    _write_atomic(_repo_path(path), serialize_manifest(manifest))


def _download_url(pointer: dict[str, Any], attempt: int) -> str:
    asset_url = pointer["asset_url"]
    if attempt == 0:
        return asset_url

    split = urllib.parse.urlsplit(asset_url)
    query = urllib.parse.parse_qsl(split.query, keep_blank_values=True)
    query.extend(
        [
            ("atlas_manifest_sha256", pointer["gz_sha256"]),
            ("atlas_manifest_attempt", str(attempt)),
        ]
    )
    return urllib.parse.urlunsplit(split._replace(query=urllib.parse.urlencode(query)))


def _download(pointer: dict[str, Any], *, attempt: int = 0) -> bytes:
    request = urllib.request.Request(
        _download_url(pointer, attempt),
        headers={
            "Accept": "application/gzip, application/octet-stream;q=0.9, */*;q=0.1",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "User-Agent": "learn-ukrainian-atlas-manifest-hydrate/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def _hydrate(path: Path, pointer: dict[str, Any]) -> dict[str, Any]:
    gz_bytes: bytes | None = None
    gz_sha = ""
    last_error: BaseException | None = None
    last_failure = ""
    for attempt in range(DOWNLOAD_ATTEMPTS):
        try:
            gz_bytes = _download(pointer, attempt=attempt)
        except (OSError, urllib.error.URLError, http.client.HTTPException) as exc:
            last_error = exc
            last_failure = "error"
            continue
        gz_sha = _sha256(gz_bytes)
        if gz_sha == pointer["gz_sha256"]:
            break
        last_failure = "mismatch"
    else:
        if last_error is not None and last_failure == "error":
            raise ValueError(
                "failed to download Atlas manifest release asset "
                f"after {DOWNLOAD_ATTEMPTS} attempts: {last_error}. "
                f"Manual recovery command: {RECOVERY_COMMAND}"
            ) from last_error
        raise ValueError(
            "gz sha256 mismatch: "
            f"expected {pointer['gz_sha256']}, got {gz_sha} "
            f"after {DOWNLOAD_ATTEMPTS} download attempts. "
            f"Manual recovery command: {RECOVERY_COMMAND}. "
            f"{STALE_POINTER_HINT}"
        )

    assert gz_bytes is not None
    json_bytes = gzip.decompress(gz_bytes)
    json_sha = _sha256(json_bytes)
    if json_sha != pointer["json_sha256"]:
        raise ValueError(
            "json sha256 mismatch after gzip decompress: "
            f"expected {pointer['json_sha256']}, got {json_sha}. "
            f"Manual recovery command: {RECOVERY_COMMAND}. "
            f"{STALE_POINTER_HINT}"
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
