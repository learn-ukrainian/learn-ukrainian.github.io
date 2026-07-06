from __future__ import annotations

import gzip
import json
import subprocess
from pathlib import Path

import pytest

from scripts.practice_deck.publish import (
    ASSET_NAME,
    KINDS,
    LEVELS,
    PracticeDeckPublishError,
    publish_practice_deck,
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_practice_deck(practice_dir: Path, *, deck_version: str = "atlas-practice-v1-test") -> None:
    for level in LEVELS:
        _write_json(
            practice_dir / f"practice-index.{level}.json",
            {
                "schema": "atlas-practice-index",
                "schemaVersion": 1,
                "deckVersion": deck_version,
                "level": level,
                "counts": {
                    "lexemes": 1,
                    "cloze": 0,
                    "clozeEligibleLexemes": 0,
                    "clozeCoverage": 0.0,
                },
                "items": [],
            },
        )
        _write_json(
            practice_dir / f"practice-lexemes.{level}.json",
            {
                "schema": "atlas-practice-lexemes",
                "schemaVersion": 1,
                "deckVersion": deck_version,
                "level": level,
                "lexemes": [],
            },
        )
        _write_json(
            practice_dir / f"practice-cloze.{level}.json",
            {
                "schema": "atlas-practice-cloze",
                "schemaVersion": 1,
                "deckVersion": deck_version,
                "level": level,
                "cloze": [],
            },
        )
        for kind, (_template, schema) in KINDS.items():
            if kind in {"index", "lexemes", "cloze"}:
                continue
            _write_json(
                practice_dir / f"practice-{kind}.{level}.json",
                {
                    "schema": schema,
                    "schemaVersion": 1,
                    "deckVersion": deck_version,
                    "level": level,
                    kind: [],
                },
            )


def test_publish_practice_deck_dry_run_builds_hash_pinned_package(tmp_path: Path) -> None:
    practice_dir = tmp_path / "lexicon"
    gzip_path = tmp_path / "lexicon-practice-deck.json.gz"
    manifest_path = tmp_path / "lexicon-manifest.json"
    _write_json(manifest_path, {"entries": []})

    from scripts.practice_deck.publish import expected_deck_version, versioned_asset_name
    expected_version = expected_deck_version(manifest_path)
    _write_practice_deck(practice_dir, deck_version=expected_version)

    pointer = publish_practice_deck(
        practice_dir=practice_dir,
        gzip_path=gzip_path,
        manifest_path=manifest_path,
        dry_run=True,
    )

    assert pointer["deck_version"] == expected_version
    assert pointer["file_count"] == len(LEVELS) * len(KINDS)
    expected_name = versioned_asset_name(expected_version)
    assert pointer["asset_url"].endswith(f"/{expected_name}")
    assert gzip_path.exists()
    package = json.loads(gzip.decompress(gzip_path.read_bytes()).decode("utf-8"))
    assert package["schema"] == "atlas-practice-deck-package"
    assert package["deckVersion"] == pointer["deck_version"]
    assert len(package["files"]) == pointer["file_count"]
    assert {row["path"] for row in pointer["files"]} == {row["path"] for row in package["files"]}


def test_publish_practice_deck_rejects_version_mismatch(tmp_path: Path) -> None:
    practice_dir = tmp_path / "lexicon"
    manifest_path = tmp_path / "lexicon-manifest.json"
    _write_json(manifest_path, {"entries": []})
    _write_practice_deck(practice_dir, deck_version="atlas-practice-v1-other")

    with pytest.raises(PracticeDeckPublishError, match="does not match expected version"):
        publish_practice_deck(
            practice_dir=practice_dir,
            gzip_path=tmp_path / "deck.json.gz",
            manifest_path=manifest_path,
            dry_run=True,
        )


def test_publish_practice_deck_uploads_versioned_and_canonical_assets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    practice_dir = tmp_path / "lexicon"
    manifest_path = tmp_path / "lexicon-manifest.json"
    gzip_path = tmp_path / "lexicon-practice-deck.json.gz"
    pointer_path = tmp_path / "lexicon-practice-deck.pointer.json"

    _write_json(manifest_path, {"entries": []})

    from scripts.practice_deck.publish import expected_deck_version, versioned_asset_name
    expected_version = expected_deck_version(manifest_path)
    _write_practice_deck(practice_dir, deck_version=expected_version)
    expected_versioned_name = versioned_asset_name(expected_version)

    upload_calls: list[list[str]] = []

    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        if args[:3] == ["gh", "release", "view"]:
            return subprocess.CompletedProcess(args, 0, stdout='{"assets":[]}', stderr="")
        if args[:3] == ["gh", "release", "upload"]:
            assert Path(args[4]).exists()
            upload_calls.append(args)
            return subprocess.CompletedProcess(args, 0)
        raise AssertionError(f"unexpected command: {args}")

    monkeypatch.setattr(subprocess, "run", fake_run)

    pointer = publish_practice_deck(
        practice_dir=practice_dir,
        gzip_path=gzip_path,
        pointer_path=pointer_path,
        manifest_path=manifest_path,
        repo="learn-ukrainian/example",
    )

    assert pointer["asset_url"].endswith(f"/{expected_versioned_name}")
    assert json.loads(pointer_path.read_text(encoding="utf-8")) == pointer
    assert [Path(call[4]).name for call in upload_calls] == [expected_versioned_name, ASSET_NAME]
    assert "--clobber" not in upload_calls[0]
    assert "--clobber" in upload_calls[1]


def test_publish_practice_deck_skips_existing_verified_versioned_asset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    practice_dir = tmp_path / "lexicon"
    manifest_path = tmp_path / "lexicon-manifest.json"
    gzip_path = tmp_path / "lexicon-practice-deck.json.gz"
    pointer_path = tmp_path / "lexicon-practice-deck.pointer.json"

    _write_json(manifest_path, {"entries": []})

    from scripts.practice_deck.publish import expected_deck_version, versioned_asset_name
    expected_version = expected_deck_version(manifest_path)
    _write_practice_deck(practice_dir, deck_version=expected_version)
    expected_versioned_name = versioned_asset_name(expected_version)

    upload_calls: list[list[str]] = []
    download_calls: list[str] = []

    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        if args[:3] == ["gh", "release", "view"]:
            payload = {"assets": [{"name": expected_versioned_name}]}
            return subprocess.CompletedProcess(args, 0, stdout=json.dumps(payload), stderr="")
        if args[:3] == ["gh", "release", "download"]:
            download_calls.append(args[5])
            return subprocess.CompletedProcess(args, 0, stdout=gzip_path.read_bytes(), stderr=b"")
        if args[:3] == ["gh", "release", "upload"]:
            upload_calls.append(args)
            return subprocess.CompletedProcess(args, 0)
        raise AssertionError(f"unexpected command: {args}")

    monkeypatch.setattr(subprocess, "run", fake_run)

    # First compile gzip so it exists for download mock
    publish_practice_deck(
        practice_dir=practice_dir,
        gzip_path=gzip_path,
        pointer_path=pointer_path,
        manifest_path=manifest_path,
        repo="learn-ukrainian/example",
        dry_run=True,
    )

    publish_practice_deck(
        practice_dir=practice_dir,
        gzip_path=gzip_path,
        pointer_path=pointer_path,
        manifest_path=manifest_path,
        repo="learn-ukrainian/example",
    )

    assert download_calls == [expected_versioned_name]
    assert [Path(call[4]).name for call in upload_calls] == [ASSET_NAME]
    assert "--clobber" in upload_calls[0]
