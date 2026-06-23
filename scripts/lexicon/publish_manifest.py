#!/usr/bin/env python3
"""Publish the hydrated Word Atlas manifest release asset.

This is intentionally separate from ``make atlas``: the atlas target builds and
verifies the DB-backed manifest, then this script packages that exact output,
uploads it to the GitHub Release asset, and rewrites the small pointer committed
to git.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import quote

from scripts.lexicon.manifest_fingerprint import DEFAULT_FINGERPRINT

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
DEFAULT_POINTER = ROOT / "site" / "src" / "data" / "lexicon-manifest.pointer.json"
DEFAULT_GZIP = ROOT / "site" / "src" / "data" / "lexicon-manifest.json.gz"
DEFAULT_RELEASE_TAG = "atlas-manifest"
DEFAULT_REPO = "learn-ukrainian/learn-ukrainian.github.io"
ASSET_NAME = "lexicon-manifest.json.gz"
REQUIRED_POINTER_KEYS = (
    "asset_url",
    "release_tag",
    "manifest_version",
    "manifest_fingerprint",
    "fingerprint_schema_version",
    "gz_sha256",
    "json_sha256",
    "gz_bytes",
    "json_bytes",
)


class ManifestPublishError(RuntimeError):
    """Raised when the manifest and pointer metadata cannot be made consistent."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ManifestPublishError(f"{path} must contain a JSON object")
    return payload


def _asset_url(repo: str, release_tag: str, asset_name: str = ASSET_NAME) -> str:
    return f"https://github.com/{repo}/releases/download/{release_tag}/{quote(asset_name)}"


def validate_manifest_fingerprint(
    manifest: dict[str, Any],
    fingerprint: dict[str, Any],
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
) -> None:
    """Require the built manifest to embed the sidecar fingerprint."""
    embedded = manifest.get("manifest_fingerprint")
    if not isinstance(embedded, dict):
        raise ManifestPublishError(
            f"{manifest_path} lacks manifest_fingerprint; run `make atlas` before publishing."
        )

    expected_schema = fingerprint.get("schema_version")
    expected_fingerprint = fingerprint.get("fingerprint")
    if embedded.get("schema_version") != expected_schema:
        raise ManifestPublishError(
            "manifest_fingerprint.schema_version does not match "
            "site/src/data/lexicon-manifest.fingerprint.json"
        )
    if embedded.get("fingerprint") != expected_fingerprint:
        raise ManifestPublishError(
            "manifest_fingerprint.fingerprint does not match "
            "site/src/data/lexicon-manifest.fingerprint.json"
        )


def validate_pointer_freshness(
    pointer: dict[str, Any],
    fingerprint: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> None:
    """Mirror the build-time guard for DB-free pytest coverage."""
    missing = [key for key in REQUIRED_POINTER_KEYS if pointer.get(key) in (None, "")]
    if missing:
        raise ManifestPublishError(f"Atlas manifest pointer missing freshness keys: {', '.join(missing)}")

    if pointer.get("fingerprint_schema_version") != fingerprint.get("schema_version"):
        raise ManifestPublishError("Atlas manifest pointer fingerprint schema is stale")
    if pointer.get("manifest_fingerprint") != fingerprint.get("fingerprint"):
        raise ManifestPublishError("Atlas manifest pointer fingerprint is stale")

    if manifest is None:
        return

    if manifest.get("version") != pointer.get("manifest_version"):
        raise ManifestPublishError("Atlas manifest pointer version is stale")
    embedded = manifest.get("manifest_fingerprint")
    if not isinstance(embedded, dict):
        raise ManifestPublishError("Atlas manifest lacks manifest_fingerprint")
    if embedded.get("schema_version") != pointer.get("fingerprint_schema_version"):
        raise ManifestPublishError("Atlas manifest fingerprint schema does not match pointer")
    if embedded.get("fingerprint") != pointer.get("manifest_fingerprint"):
        raise ManifestPublishError("Atlas manifest fingerprint does not match pointer")


def gzip_manifest(manifest_path: Path = DEFAULT_MANIFEST, gzip_path: Path = DEFAULT_GZIP) -> bytes:
    """Write a deterministic gzip for the manifest and return its bytes."""
    manifest_bytes = manifest_path.read_bytes()
    gzip_bytes = gzip.compress(manifest_bytes, compresslevel=9, mtime=0)
    gzip_path.write_bytes(gzip_bytes)
    return gzip_bytes


def build_pointer_payload(
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
    gzip_path: Path = DEFAULT_GZIP,
    fingerprint_path: Path = DEFAULT_FINGERPRINT,
    release_tag: str = DEFAULT_RELEASE_TAG,
    repo: str = DEFAULT_REPO,
) -> dict[str, Any]:
    manifest_bytes = manifest_path.read_bytes()
    gzip_bytes = gzip_path.read_bytes()
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    if not isinstance(manifest, dict):
        raise ManifestPublishError(f"{manifest_path} must contain a JSON object")
    fingerprint = _read_json(fingerprint_path)
    validate_manifest_fingerprint(manifest, fingerprint, manifest_path=manifest_path)

    manifest_version = manifest.get("version")
    if not isinstance(manifest_version, str) or not manifest_version:
        raise ManifestPublishError(f"{manifest_path} must contain a non-empty version")

    pointer = {
        "asset_url": _asset_url(repo, release_tag),
        "release_tag": release_tag,
        "manifest_version": manifest_version,
        "manifest_fingerprint": fingerprint["fingerprint"],
        "fingerprint_schema_version": fingerprint["schema_version"],
        "generated_at": manifest.get("generated_at"),
        "gz_sha256": _sha256(gzip_bytes),
        "json_sha256": _sha256(manifest_bytes),
        "gz_bytes": len(gzip_bytes),
        "json_bytes": len(manifest_bytes),
        "note": "Pins GitHub Release asset manifest for #3659; hydrate it build time instead committing raw JSON.",
    }
    validate_pointer_freshness(pointer, fingerprint, manifest=manifest)
    return pointer


def write_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    pointer_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = pointer_path.with_suffix(f"{pointer_path.suffix}.tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp_path.replace(pointer_path)


def upload_release_asset(
    gzip_path: Path = DEFAULT_GZIP,
    *,
    release_tag: str = DEFAULT_RELEASE_TAG,
    repo: str = DEFAULT_REPO,
) -> None:
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


def publish_manifest(
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
    gzip_path: Path = DEFAULT_GZIP,
    pointer_path: Path = DEFAULT_POINTER,
    fingerprint_path: Path = DEFAULT_FINGERPRINT,
    release_tag: str = DEFAULT_RELEASE_TAG,
    repo: str = DEFAULT_REPO,
    dry_run: bool = False,
) -> dict[str, Any]:
    gzip_manifest(manifest_path, gzip_path)
    pointer = build_pointer_payload(
        manifest_path=manifest_path,
        gzip_path=gzip_path,
        fingerprint_path=fingerprint_path,
        release_tag=release_tag,
        repo=repo,
    )

    if dry_run:
        return pointer

    upload_release_asset(gzip_path, release_tag=release_tag, repo=repo)
    write_pointer(pointer_path, pointer)
    return pointer


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish the Word Atlas manifest release asset.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--gzip", type=Path, default=DEFAULT_GZIP)
    parser.add_argument("--pointer", type=Path, default=DEFAULT_POINTER)
    parser.add_argument("--fingerprint", type=Path, default=DEFAULT_FINGERPRINT)
    parser.add_argument("--release-tag", default=DEFAULT_RELEASE_TAG)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--dry-run", action="store_true", help="Build metadata without uploading or writing pointer")
    args = parser.parse_args()

    pointer = publish_manifest(
        manifest_path=args.manifest,
        gzip_path=args.gzip,
        pointer_path=args.pointer,
        fingerprint_path=args.fingerprint,
        release_tag=args.release_tag,
        repo=args.repo,
        dry_run=args.dry_run,
    )
    print(
        "Atlas manifest pointer "
        f"{'would publish' if args.dry_run else 'published'}: "
        f"{pointer['manifest_version']} {pointer['manifest_fingerprint']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
