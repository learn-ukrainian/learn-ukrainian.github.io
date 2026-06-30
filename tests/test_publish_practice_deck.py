from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from scripts.practice_deck.publish import (
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


def test_publish_practice_deck_dry_run_builds_hash_pinned_package(tmp_path: Path) -> None:
    practice_dir = tmp_path / "lexicon"
    gzip_path = tmp_path / "lexicon-practice-deck.json.gz"
    _write_practice_deck(practice_dir)

    pointer = publish_practice_deck(practice_dir=practice_dir, gzip_path=gzip_path, dry_run=True)

    assert pointer["deck_version"] == "atlas-practice-v1-test"
    assert pointer["file_count"] == len(LEVELS) * len(KINDS)
    assert gzip_path.exists()
    package = json.loads(gzip.decompress(gzip_path.read_bytes()).decode("utf-8"))
    assert package["schema"] == "atlas-practice-deck-package"
    assert package["deckVersion"] == pointer["deck_version"]
    assert len(package["files"]) == pointer["file_count"]
    assert {row["path"] for row in pointer["files"]} == {row["path"] for row in package["files"]}


def test_publish_practice_deck_rejects_version_mismatch(tmp_path: Path) -> None:
    practice_dir = tmp_path / "lexicon"
    _write_practice_deck(practice_dir)
    payload = json.loads((practice_dir / "practice-cloze.C1.json").read_text(encoding="utf-8"))
    payload["deckVersion"] = "atlas-practice-v1-other"
    _write_json(practice_dir / "practice-cloze.C1.json", payload)

    with pytest.raises(PracticeDeckPublishError, match="deckVersion"):
        publish_practice_deck(practice_dir=practice_dir, gzip_path=tmp_path / "deck.json.gz", dry_run=True)
