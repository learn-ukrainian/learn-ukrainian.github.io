from __future__ import annotations

import gzip
import hashlib
import io
import json
from pathlib import Path

import pytest

from scripts.lexicon import manifest_io

STALE_POINTER_HINT = "Re-downloading cannot fix a stale pointer."


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


def _request_url(request: object) -> str:
    return getattr(request, "full_url", str(request))


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

    def fake_urlopen(request: object, timeout: int):
        assert _request_url(request) == "https://example.test/lexicon-manifest.json.gz"
        assert timeout == 60
        return io.BytesIO(gz_bytes)

    monkeypatch.setattr(manifest_io.urllib.request, "urlopen", fake_urlopen)

    assert manifest_io.load_manifest(path=manifest_path) == payload
    assert manifest_path.read_bytes() == json_bytes


def test_load_manifest_refuses_to_clobber_richer_local_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    release_payload = {
        "entries": [{"lemma": "слово"}],
        "generated_at": "2026-07-05T17:13:27+00:00",
    }
    local_payload = {
        "entries": [{"lemma": "слово"}, {"lemma": "вікно"}],
        "generated_at": "2026-07-06T17:13:27+00:00",
    }
    json_bytes = _json_bytes(release_payload)
    gz_bytes = gzip.compress(json_bytes)
    manifest_path = tmp_path / "lexicon-manifest.json"
    pointer_path = tmp_path / "lexicon-manifest.pointer.json"
    local_bytes = _json_bytes(local_payload)
    manifest_path.write_bytes(local_bytes)
    _write_pointer(pointer_path, json_bytes=json_bytes, gz_bytes=gz_bytes)
    _pin_defaults(monkeypatch, manifest_path, pointer_path)
    monkeypatch.setattr(manifest_io.urllib.request, "urlopen", lambda *_args, **_kwargs: io.BytesIO(gz_bytes))

    with pytest.raises(ValueError, match="refusing to hydrate") as excinfo:
        manifest_io.load_manifest(path=manifest_path)

    assert "2 entries" in str(excinfo.value)
    assert "1 entries" in str(excinfo.value)
    assert "2026-07-06T17:13:27+00:00" in str(excinfo.value)
    assert "2026-07-05T17:13:27+00:00" in str(excinfo.value)
    assert "ATLAS_MANIFEST_FORCE_HYDRATE=1" in str(excinfo.value)
    assert manifest_path.read_bytes() == local_bytes


def test_load_manifest_hydrates_stale_poorer_local_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    release_payload = {
        "entries": [{"lemma": "слово"}, {"lemma": "вікно"}],
        "generated_at": "2026-07-06T17:13:27+00:00",
    }
    local_payload = {
        "entries": [{"lemma": "слово"}],
        "generated_at": "2026-07-05T17:13:27+00:00",
    }
    json_bytes = _json_bytes(release_payload)
    gz_bytes = gzip.compress(json_bytes)
    manifest_path = tmp_path / "lexicon-manifest.json"
    pointer_path = tmp_path / "lexicon-manifest.pointer.json"
    manifest_path.write_bytes(_json_bytes(local_payload))
    _write_pointer(pointer_path, json_bytes=json_bytes, gz_bytes=gz_bytes)
    _pin_defaults(monkeypatch, manifest_path, pointer_path)
    monkeypatch.setattr(manifest_io.urllib.request, "urlopen", lambda *_args, **_kwargs: io.BytesIO(gz_bytes))

    assert manifest_io.load_manifest(path=manifest_path) == release_payload
    assert manifest_path.read_bytes() == json_bytes


def test_load_manifest_force_hydrates_richer_local_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    release_payload = {
        "entries": [{"lemma": "слово"}],
        "generated_at": "2026-07-05T17:13:27+00:00",
    }
    local_payload = {
        "entries": [{"lemma": "слово"}, {"lemma": "вікно"}],
        "generated_at": "2026-07-06T17:13:27+00:00",
    }
    json_bytes = _json_bytes(release_payload)
    gz_bytes = gzip.compress(json_bytes)
    manifest_path = tmp_path / "lexicon-manifest.json"
    pointer_path = tmp_path / "lexicon-manifest.pointer.json"
    manifest_path.write_bytes(_json_bytes(local_payload))
    _write_pointer(pointer_path, json_bytes=json_bytes, gz_bytes=gz_bytes)
    _pin_defaults(monkeypatch, manifest_path, pointer_path)
    monkeypatch.setenv("ATLAS_MANIFEST_FORCE_HYDRATE", "1")
    monkeypatch.setattr(manifest_io.urllib.request, "urlopen", lambda *_args, **_kwargs: io.BytesIO(gz_bytes))

    assert manifest_io.load_manifest(path=manifest_path) == release_payload
    assert manifest_path.read_bytes() == json_bytes


def test_load_manifest_refuses_newer_local_manifest_with_equal_entry_count(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    release_payload = {
        "entries": [{"lemma": "слово"}],
        "generated_at": "2026-07-05T17:13:27+00:00",
    }
    local_payload = {
        "entries": [{"lemma": "слово"}],
        "generated_at": "2026-07-06T17:13:27+00:00",
    }
    json_bytes = _json_bytes(release_payload)
    gz_bytes = gzip.compress(json_bytes)
    manifest_path = tmp_path / "lexicon-manifest.json"
    pointer_path = tmp_path / "lexicon-manifest.pointer.json"
    local_bytes = _json_bytes(local_payload)
    manifest_path.write_bytes(local_bytes)
    _write_pointer(pointer_path, json_bytes=json_bytes, gz_bytes=gz_bytes)
    _pin_defaults(monkeypatch, manifest_path, pointer_path)
    monkeypatch.setattr(manifest_io.urllib.request, "urlopen", lambda *_args, **_kwargs: io.BytesIO(gz_bytes))

    with pytest.raises(ValueError, match="refusing to hydrate"):
        manifest_io.load_manifest(path=manifest_path)

    assert manifest_path.read_bytes() == local_bytes


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

    def fake_urlopen(request: object, timeout: int):
        return io.BytesIO(gz_bytes)

    monkeypatch.setattr(manifest_io.urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(ValueError, match="gz sha256 mismatch") as excinfo:
        manifest_io.load_manifest(path=manifest_path)

    assert "gh release download atlas-manifest" in str(excinfo.value)
    assert STALE_POINTER_HINT in str(excinfo.value)
    assert not manifest_path.exists()


def test_load_manifest_retries_gz_sha256_mismatch_with_cache_bust(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {"entries": [{"lemma": "повтор"}], "enrichment_generated": True}
    json_bytes = _json_bytes(payload)
    gz_bytes = gzip.compress(json_bytes)
    stale_gz_bytes = gzip.compress(_json_bytes({"entries": [{"lemma": "старий"}]}))
    manifest_path = tmp_path / "lexicon-manifest.json"
    pointer_path = tmp_path / "lexicon-manifest.pointer.json"
    _write_pointer(pointer_path, json_bytes=json_bytes, gz_bytes=gz_bytes)
    _pin_defaults(monkeypatch, manifest_path, pointer_path)
    urls: list[str] = []

    def fake_urlopen(request: object, timeout: int):
        assert timeout == 60
        urls.append(_request_url(request))
        return io.BytesIO(stale_gz_bytes if len(urls) == 1 else gz_bytes)

    monkeypatch.setattr(manifest_io.urllib.request, "urlopen", fake_urlopen)

    assert manifest_io.load_manifest(path=manifest_path) == payload
    assert manifest_path.read_bytes() == json_bytes
    assert urls == [
        "https://example.test/lexicon-manifest.json.gz",
        (
            "https://example.test/lexicon-manifest.json.gz"
            f"?atlas_manifest_sha256={_sha256(gz_bytes)}&atlas_manifest_attempt=1"
        ),
    ]


def test_load_manifest_retries_transient_download_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {"entries": [{"lemma": "мережа"}], "enrichment_generated": True}
    json_bytes = _json_bytes(payload)
    gz_bytes = gzip.compress(json_bytes)
    manifest_path = tmp_path / "lexicon-manifest.json"
    pointer_path = tmp_path / "lexicon-manifest.pointer.json"
    _write_pointer(pointer_path, json_bytes=json_bytes, gz_bytes=gz_bytes)
    _pin_defaults(monkeypatch, manifest_path, pointer_path)
    urls: list[str] = []

    def fake_urlopen(request: object, timeout: int):
        assert timeout == 60
        urls.append(_request_url(request))
        if len(urls) == 1:
            raise manifest_io.urllib.error.URLError("temporary release edge failure")
        return io.BytesIO(gz_bytes)

    monkeypatch.setattr(manifest_io.urllib.request, "urlopen", fake_urlopen)

    assert manifest_io.load_manifest(path=manifest_path) == payload
    assert manifest_path.read_bytes() == json_bytes
    assert urls[1] == (
        "https://example.test/lexicon-manifest.json.gz"
        f"?atlas_manifest_sha256={_sha256(gz_bytes)}&atlas_manifest_attempt=1"
    )


def test_load_manifest_reports_final_download_error_after_prior_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {"entries": [{"lemma": "збій"}], "enrichment_generated": True}
    json_bytes = _json_bytes(payload)
    gz_bytes = gzip.compress(json_bytes)
    stale_gz_bytes = gzip.compress(_json_bytes({"entries": [{"lemma": "старий"}]}))
    manifest_path = tmp_path / "lexicon-manifest.json"
    pointer_path = tmp_path / "lexicon-manifest.pointer.json"
    _write_pointer(pointer_path, json_bytes=json_bytes, gz_bytes=gz_bytes)
    _pin_defaults(monkeypatch, manifest_path, pointer_path)
    urls: list[str] = []

    def fake_urlopen(request: object, timeout: int):
        assert timeout == 60
        urls.append(_request_url(request))
        if len(urls) == 1:
            return io.BytesIO(stale_gz_bytes)
        raise manifest_io.http.client.IncompleteRead(b"partial")

    monkeypatch.setattr(manifest_io.urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(ValueError, match="failed to download Atlas manifest") as excinfo:
        manifest_io.load_manifest(path=manifest_path)

    assert "IncompleteRead" in str(excinfo.value)
    assert "gz sha256 mismatch" not in str(excinfo.value)
    assert not manifest_path.exists()
