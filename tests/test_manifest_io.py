from __future__ import annotations

import gzip
import hashlib
import io
import json
from pathlib import Path

import pytest

from scripts.lexicon import manifest_io


def _json_bytes(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_pointer(
    pointer_path: Path,
    *,
    json_bytes: bytes,
    gz_bytes: bytes,
    gz_sha256: str | None = None,
) -> None:
    pointer_path.write_text(
        json.dumps(
            {
                "asset_url": "https://example.test/lexicon-manifest.json.gz",
                "release_tag": "atlas-manifest",
                "gz_sha256": gz_sha256 or _sha256(gz_bytes),
                "json_sha256": _sha256(json_bytes),
                "gz_bytes": len(gz_bytes),
                "json_bytes": len(json_bytes),
                "note": "test pointer",
            }
        ),
        encoding="utf-8",
    )


def _pin_defaults(monkeypatch: pytest.MonkeyPatch, manifest_path: Path, pointer_path: Path) -> None:
    monkeypatch.setattr(manifest_io, "DEFAULT_MANIFEST", manifest_path)
    monkeypatch.setattr(manifest_io, "DEFAULT_POINTER", pointer_path)


def test_load_manifest_returns_matching_local_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {"entries": [{"lemma": "дім"}], "enrichment_generated": True}
    json_bytes = _json_bytes(payload)
    gz_bytes = gzip.compress(json_bytes)
    manifest_path = tmp_path / "lexicon-manifest.json"
    pointer_path = tmp_path / "lexicon-manifest.pointer.json"
    manifest_path.write_bytes(json_bytes)
    _write_pointer(pointer_path, json_bytes=json_bytes, gz_bytes=gz_bytes)
    _pin_defaults(monkeypatch, manifest_path, pointer_path)

    def fail_urlopen(*args, **kwargs):
        raise AssertionError("matching local manifest should not fetch")

    monkeypatch.setattr(manifest_io.urllib.request, "urlopen", fail_urlopen)

    assert manifest_io.load_manifest(path=manifest_path) == payload


def test_load_manifest_fetches_decompresses_and_writes_when_absent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {"entries": [{"lemma": "слово"}], "enrichment_generated": True}
    json_bytes = _json_bytes(payload)
    gz_bytes = gzip.compress(json_bytes)
    manifest_path = tmp_path / "lexicon-manifest.json"
    pointer_path = tmp_path / "lexicon-manifest.pointer.json"
    _write_pointer(pointer_path, json_bytes=json_bytes, gz_bytes=gz_bytes)
    _pin_defaults(monkeypatch, manifest_path, pointer_path)

    def fake_urlopen(url: str, timeout: int):
        assert url == "https://example.test/lexicon-manifest.json.gz"
        assert timeout == 60
        return io.BytesIO(gz_bytes)

    monkeypatch.setattr(manifest_io.urllib.request, "urlopen", fake_urlopen)

    assert manifest_io.load_manifest(path=manifest_path) == payload
    assert manifest_path.read_bytes() == json_bytes


def test_load_manifest_raises_on_gz_sha256_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {"entries": [{"lemma": "хиба"}], "enrichment_generated": True}
    json_bytes = _json_bytes(payload)
    gz_bytes = gzip.compress(json_bytes)
    manifest_path = tmp_path / "lexicon-manifest.json"
    pointer_path = tmp_path / "lexicon-manifest.pointer.json"
    _write_pointer(pointer_path, json_bytes=json_bytes, gz_bytes=gz_bytes, gz_sha256="0" * 64)
    _pin_defaults(monkeypatch, manifest_path, pointer_path)

    def fake_urlopen(url: str, timeout: int):
        return io.BytesIO(gz_bytes)

    monkeypatch.setattr(manifest_io.urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(ValueError, match="gz sha256 mismatch") as excinfo:
        manifest_io.load_manifest(path=manifest_path)

    assert "gh release download atlas-manifest" in str(excinfo.value)
    assert not manifest_path.exists()
