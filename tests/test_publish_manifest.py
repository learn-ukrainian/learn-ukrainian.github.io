import gzip
import hashlib
import json
from pathlib import Path

import pytest

from scripts.lexicon.publish_manifest import (
    ManifestPublishError,
    build_pointer_payload,
    gzip_manifest,
    validate_pointer_freshness,
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def test_build_pointer_payload_records_manifest_version_and_fingerprint(tmp_path: Path) -> None:
    fingerprint = {"schema_version": 1, "fingerprint": "abc123"}
    manifest = {
        "version": "0.1",
        "generated_at": "2026-06-23T00:00:00+00:00",
        "manifest_fingerprint": fingerprint,
        "entries": [],
    }
    manifest_path = tmp_path / "lexicon-manifest.json"
    fingerprint_path = tmp_path / "lexicon-manifest.fingerprint.json"
    gzip_path = tmp_path / "lexicon-manifest.json.gz"
    _write_json(manifest_path, manifest)
    _write_json(fingerprint_path, fingerprint)

    gzip_bytes = gzip_manifest(manifest_path, gzip_path)
    payload = build_pointer_payload(
        manifest_path=manifest_path,
        gzip_path=gzip_path,
        fingerprint_path=fingerprint_path,
        repo="learn-ukrainian/example",
    )

    manifest_bytes = manifest_path.read_bytes()
    assert gzip.decompress(gzip_bytes) == manifest_bytes
    assert payload["asset_url"].endswith("/learn-ukrainian/example/releases/download/atlas-manifest/lexicon-manifest.json.gz")
    assert payload["manifest_version"] == "0.1"
    assert payload["manifest_fingerprint"] == "abc123"
    assert payload["fingerprint_schema_version"] == 1
    assert payload["json_sha256"] == _sha256(manifest_bytes)
    assert payload["gz_sha256"] == _sha256(gzip_path.read_bytes())


def test_pointer_freshness_guard_fails_on_stale_pointer_fixture() -> None:
    fingerprint = {"schema_version": 1, "fingerprint": "current"}
    pointer = {
        "asset_url": "https://example.test/lexicon-manifest.json.gz",
        "release_tag": "atlas-manifest",
        "manifest_version": "0.1",
        "manifest_fingerprint": "stale",
        "fingerprint_schema_version": 1,
        "gz_sha256": "0" * 64,
        "json_sha256": "1" * 64,
        "gz_bytes": 10,
        "json_bytes": 20,
    }

    with pytest.raises(ManifestPublishError, match="fingerprint is stale"):
        validate_pointer_freshness(pointer, fingerprint)
