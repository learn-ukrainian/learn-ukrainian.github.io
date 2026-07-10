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
    shard_bytes: bytes = b"content-data",
    lexeme_count: int | None = None,
) -> None:
    shard = {
        "path": "practice-index.A1.json",
        "kind": "index",
        "level": "A1",
        "schema": "atlas-practice-index",
        "bytes": len(shard_bytes),
        "sha256": _sha256(shard_bytes),
    }
    if lexeme_count is not None:
        shard["counts"] = {"lexemes": lexeme_count}
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
                "files": [shard],
                "note": "test pointer",
            }
        ),
        encoding="utf-8",
    )


def _pin_defaults(monkeypatch: pytest.MonkeyPatch, practice_dir: Path, pointer_path: Path) -> None:
    monkeypatch.setattr(practice_deck_io, "DEFAULT_PRACTICE_DIR", practice_dir)
    monkeypatch.setattr(practice_deck_io, "DEFAULT_POINTER", pointer_path)


def test_compute_deck_version_fingerprints_all_inputs() -> None:
    entries = [{"lemmaId": "knyha", "lemma": "knyha", "gloss": "book"}]
    heritage_pairs = [{"nativeSlug": "knyha", "rationale": "fixture"}]
    paronym_pairs = [{"slugA": "knyha", "slugB": "книга", "frames": [], "citations": ["t"]}]
    synonym_verdicts = {
        "approved": [{"a": "knyha", "b": "tom", "polarity": "synonym"}],
        "rejected": [],
    }
    cloze_sources = [{"lemmaId": "knyha", "sentence": "I read ___."}]

    version = practice_deck_io.compute_deck_version(
        entries,
        heritage_pairs,
        paronym_pairs,
        synonym_verdicts,
        cloze_sources,
        1,
    )

    assert version.startswith("atlas-practice-v1-")
    fingerprint = version.removeprefix("atlas-practice-v1-")
    assert len(fingerprint) == 16
    assert all(char in "0123456789abcdef" for char in fingerprint)

    variants = [
        ([{**entries[0], "gloss": "book volume"}], heritage_pairs, paronym_pairs, synonym_verdicts, cloze_sources),
        (entries, [{**heritage_pairs[0], "rationale": "changed"}], paronym_pairs, synonym_verdicts, cloze_sources),
        (
            entries,
            heritage_pairs,
            paronym_pairs,
            {"approved": synonym_verdicts["approved"], "rejected": [{"a": "x", "b": "y", "polarity": "antonym"}]},
            cloze_sources,
        ),
        (entries, heritage_pairs, paronym_pairs, synonym_verdicts, [{**cloze_sources[0], "sentence": "Changed ___."}]),
    ]
    changed_versions = {
        practice_deck_io.compute_deck_version(
            variant_entries,
            variant_heritage_pairs,
            variant_paronym_pairs,
            variant_synonym_verdicts,
            variant_cloze_sources,
            1,
        )
        for variant_entries, variant_heritage_pairs, variant_paronym_pairs, variant_synonym_verdicts, variant_cloze_sources in variants
    }

    assert version not in changed_versions
    assert len(changed_versions) == len(variants)


def test_compute_deck_version_hashes_missing_inputs_as_empty_sentinels() -> None:
    assert practice_deck_io.compute_deck_version(None, None, None, None, None, 1) == (
        practice_deck_io.compute_deck_version([], [], [], {}, [], 1)
    )


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


def test_ensure_practice_deck_hydrated_refuses_to_clobber_richer_local_deck(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    practice_dir = tmp_path / "lexicon"
    pointer_path = tmp_path / "lexicon-practice-deck.pointer.json"
    release_content = _json_bytes({"counts": {"lexemes": 3}})
    local_content = _json_bytes({"counts": {"lexemes": 5}})
    package = {
        "schema": "atlas-practice-deck-package",
        "schemaVersion": 1,
        "deckVersion": "deck-v1",
        "files": [{"path": "practice-index.A1.json", "content": release_content.decode("utf-8")}],
    }
    package_bytes = _json_bytes(package)
    gz_bytes = gzip.compress(package_bytes)
    shard_path = practice_dir / "practice-index.A1.json"
    shard_path.parent.mkdir(parents=True, exist_ok=True)
    shard_path.write_bytes(local_content)
    _write_pointer(
        pointer_path,
        package_bytes=package_bytes,
        gz_bytes=gz_bytes,
        shard_bytes=release_content,
        lexeme_count=3,
    )
    _pin_defaults(monkeypatch, practice_dir, pointer_path)
    monkeypatch.setattr(practice_deck_io.urllib.request, "urlopen", lambda *_args, **_kwargs: io.BytesIO(gz_bytes))

    with pytest.raises(practice_deck_io.PracticeDeckHydrationError, match="refusing to overwrite"):
        practice_deck_io.ensure_practice_deck_hydrated(practice_dir=practice_dir, pointer_path=pointer_path)

    assert shard_path.read_bytes() == local_content


def test_ensure_practice_deck_hydrated_force_restores_richer_local_deck(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    practice_dir = tmp_path / "lexicon"
    pointer_path = tmp_path / "lexicon-practice-deck.pointer.json"
    release_content = _json_bytes({"counts": {"lexemes": 3}})
    package = {
        "schema": "atlas-practice-deck-package",
        "schemaVersion": 1,
        "deckVersion": "deck-v1",
        "files": [{"path": "practice-index.A1.json", "content": release_content.decode("utf-8")}],
    }
    package_bytes = _json_bytes(package)
    gz_bytes = gzip.compress(package_bytes)
    shard_path = practice_dir / "practice-index.A1.json"
    shard_path.parent.mkdir(parents=True, exist_ok=True)
    shard_path.write_bytes(_json_bytes({"counts": {"lexemes": 5}}))
    _write_pointer(
        pointer_path,
        package_bytes=package_bytes,
        gz_bytes=gz_bytes,
        shard_bytes=release_content,
        lexeme_count=3,
    )
    _pin_defaults(monkeypatch, practice_dir, pointer_path)
    monkeypatch.setenv("ATLAS_MANIFEST_FORCE_HYDRATE", "1")
    monkeypatch.setattr(practice_deck_io.urllib.request, "urlopen", lambda *_args, **_kwargs: io.BytesIO(gz_bytes))

    assert practice_deck_io.ensure_practice_deck_hydrated(practice_dir=practice_dir, pointer_path=pointer_path)
    assert shard_path.read_bytes() == release_content


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
