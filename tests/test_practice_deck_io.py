from __future__ import annotations

import gzip
import hashlib
import io
import json
from pathlib import Path

import pytest

from scripts.practice_deck import io as practice_deck_io


def _json_bytes(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_pointer(
    pointer_path: Path,
    *,
    package_bytes: bytes,
    gz_bytes: bytes,
    gz_sha256: str | None = None,
    package_sha256: str | None = None,
    deck_version: str = "deck-v1",
) -> None:
    pointer_path.write_text(
        json.dumps(
            {
                "asset_url": "https://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/download/atlas-practice-deck/lexicon-practice-deck.json.gz",
                "release_tag": "atlas-practice-deck",
                "deck_version": deck_version,
                "package_schema_version": 1,
                "gz_sha256": gz_sha256 or _sha256(gz_bytes),
                "package_sha256": package_sha256 or _sha256(package_bytes),
                "gz_bytes": len(gz_bytes),
                "package_bytes": len(package_bytes),
                "file_count": 1,
                "files": [
                    {
                        "path": "practice-index.A1.json",
                        "kind": "index",
                        "level": "A1",
                        "schema": "atlas-practice-index",
                        "bytes": len(b"content-data"),
                        "sha256": _sha256(b"content-data"),
                    }
                ],
                "note": "test pointer",
            }
        ),
        encoding="utf-8",
    )


def _pin_defaults(monkeypatch: pytest.MonkeyPatch, practice_dir: Path, pointer_path: Path) -> None:
    monkeypatch.setattr(practice_deck_io, "DEFAULT_PRACTICE_DIR", practice_dir)
    monkeypatch.setattr(practice_deck_io, "DEFAULT_POINTER", pointer_path)


def _request_url(request: object) -> str:
    return getattr(request, "full_url", str(request))


def test_ensure_practice_deck_hydrated_returns_matching_local(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    practice_dir = tmp_path / "lexicon"
    pointer_path = tmp_path / "lexicon-practice-deck.pointer.json"

    shard_path = practice_dir / "practice-index.A1.json"
    shard_path.parent.mkdir(parents=True, exist_ok=True)
    shard_path.write_bytes(b"content-data")

    package = {
        "schema": "atlas-practice-deck-package",
        "schemaVersion": 1,
        "deckVersion": "deck-v1",
        "files": [{"path": "practice-index.A1.json", "content": "content-data"}],
    }
    package_bytes = _json_bytes(package)
    gz_bytes = gzip.compress(package_bytes)

    _write_pointer(pointer_path, package_bytes=package_bytes, gz_bytes=gz_bytes)
    _pin_defaults(monkeypatch, practice_dir, pointer_path)

    def fail_urlopen(*args, **kwargs):
        raise AssertionError("matching local practice deck should not fetch")

    monkeypatch.setattr(practice_deck_io.urllib.request, "urlopen", fail_urlopen)

    assert practice_deck_io.ensure_practice_deck_hydrated(
        practice_dir=practice_dir, pointer_path=pointer_path
    ) is not None


def test_ensure_practice_deck_hydrated_fetches_decompresses_and_writes_when_absent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    practice_dir = tmp_path / "lexicon"
    pointer_path = tmp_path / "lexicon-practice-deck.pointer.json"

    package = {
        "schema": "atlas-practice-deck-package",
        "schemaVersion": 1,
        "deckVersion": "deck-v1",
        "files": [{"path": "practice-index.A1.json", "content": "content-data"}],
    }
    package_bytes = _json_bytes(package)
    gz_bytes = gzip.compress(package_bytes)

    _write_pointer(pointer_path, package_bytes=package_bytes, gz_bytes=gz_bytes)
    _pin_defaults(monkeypatch, practice_dir, pointer_path)

    expected_url = "https://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/download/atlas-practice-deck/lexicon-practice-deck.json.gz"

    def fake_urlopen(request: object, timeout: int):
        assert _request_url(request) == expected_url
        assert timeout == 60
        return io.BytesIO(gz_bytes)

    monkeypatch.setattr(practice_deck_io.urllib.request, "urlopen", fake_urlopen)

    assert practice_deck_io.ensure_practice_deck_hydrated(
        practice_dir=practice_dir, pointer_path=pointer_path
    ) is not None
    shard_path = practice_dir / "practice-index.A1.json"
    assert shard_path.exists()
    assert shard_path.read_bytes() == b"content-data"


def test_ensure_practice_deck_hydrated_raises_on_gz_sha256_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    practice_dir = tmp_path / "lexicon"
    pointer_path = tmp_path / "lexicon-practice-deck.pointer.json"

    package = {
        "schema": "atlas-practice-deck-package",
        "schemaVersion": 1,
        "deckVersion": "deck-v1",
        "files": [{"path": "practice-index.A1.json", "content": "content-data"}],
    }
    package_bytes = _json_bytes(package)
    gz_bytes = gzip.compress(package_bytes)

    _write_pointer(pointer_path, package_bytes=package_bytes, gz_bytes=gz_bytes, gz_sha256="0" * 64)
    _pin_defaults(monkeypatch, practice_dir, pointer_path)

    def fake_urlopen(request: object, timeout: int):
        return io.BytesIO(gz_bytes)

    monkeypatch.setattr(practice_deck_io.urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(RuntimeError, match="gz sha256 mismatch") as excinfo:
        practice_deck_io.ensure_practice_deck_hydrated(
            practice_dir=practice_dir, pointer_path=pointer_path
        )

    assert "Re-downloading cannot fix a stale pointer" in str(excinfo.value)
    assert not (practice_dir / "practice-index.A1.json").exists()


def test_ensure_practice_deck_hydrated_retries_gz_sha256_mismatch_with_cache_bust(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    practice_dir = tmp_path / "lexicon"
    pointer_path = tmp_path / "lexicon-practice-deck.pointer.json"

    package = {
        "schema": "atlas-practice-deck-package",
        "schemaVersion": 1,
        "deckVersion": "deck-v1",
        "files": [{"path": "practice-index.A1.json", "content": "content-data"}],
    }
    package_bytes = _json_bytes(package)
    gz_bytes = gzip.compress(package_bytes)
    stale_gz_bytes = gzip.compress(_json_bytes({"schema": "wrong"}))

    _write_pointer(pointer_path, package_bytes=package_bytes, gz_bytes=gz_bytes)
    _pin_defaults(monkeypatch, practice_dir, pointer_path)
    urls: list[str] = []

    def fake_urlopen(request: object, timeout: int):
        assert timeout == 60
        urls.append(_request_url(request))
        return io.BytesIO(stale_gz_bytes if len(urls) == 1 else gz_bytes)

    monkeypatch.setattr(practice_deck_io.urllib.request, "urlopen", fake_urlopen)

    assert practice_deck_io.ensure_practice_deck_hydrated(
        practice_dir=practice_dir, pointer_path=pointer_path
    ) is not None
    shard_path = practice_dir / "practice-index.A1.json"
    assert shard_path.read_bytes() == b"content-data"
    expected_base_url = "https://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/download/atlas-practice-deck/lexicon-practice-deck.json.gz"
    assert urls == [
        expected_base_url,
        (
            f"{expected_base_url}"
            f"?atlas_practice_deck_sha256={_sha256(gz_bytes)}&atlas_practice_deck_attempt=1"
        ),
    ]
