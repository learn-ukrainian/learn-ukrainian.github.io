from __future__ import annotations

import gzip
import json
import sqlite3
import subprocess
from pathlib import Path

import pytest

from scripts.audit.generate_practice_deck import (
    BuildConfig,
    JsonVesumVerifier,
    ReviewedSourceAllowlist,
    build_practice_shards,
    read_cloze_sources,
    read_heritage_pairs,
    read_manifest,
    write_shards,
)
from scripts.practice_deck import publish as publish_module
from scripts.practice_deck.publish import (
    ASSET_NAME,
    KINDS,
    LEVELS,
    PracticeDeckPublishError,
    publish_practice_deck,
)

FIXTURES = Path("tests/fixtures")
MANIFEST = FIXTURES / "lexicon-practice-manifest.json"
ALLOWLIST = FIXTURES / "lexicon-practice-reviewed-allowlist.json"
VESUM = FIXTURES / "lexicon-practice-vesum.json"
CLOZE_SOURCES = FIXTURES / "lexicon-practice-cloze-sources.json"
HERITAGE_PAIRS = FIXTURES / "lexicon-practice-heritage-pairs.yaml"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_atlas_db(
    path: Path,
    entries: list[dict[str, object]],
    *,
    public_flags: list[bool] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE article_payloads (
                slug TEXT PRIMARY KEY,
                route_order INTEGER NOT NULL,
                payload_json TEXT NOT NULL,
                is_public_route INTEGER NOT NULL
            )
            """
        )
        for index, entry in enumerate(entries):
            slug = str(entry.get("url_slug") or entry.get("slug") or f"entry-{index}")
            is_public = public_flags[index] if public_flags is not None else True
            conn.execute(
                """
                INSERT INTO article_payloads (slug, route_order, payload_json, is_public_route)
                VALUES (?, ?, ?, ?)
                """,
                (slug, index, json.dumps(entry, ensure_ascii=False), 1 if is_public else 0),
            )
        conn.commit()
    finally:
        conn.close()


def _write_publish_inputs(
    base_dir: Path,
    *,
    entries: list[dict[str, object]] | None = None,
    heritage_pairs: list[dict[str, object]] | None = None,
    synonym_verdicts: dict[str, object] | None = None,
    cloze_sources: list[dict[str, object]] | None = None,
    public_flags: list[bool] | None = None,
) -> dict[str, Path]:
    paths = {
        "atlas_db_path": base_dir / "atlas.db",
        "heritage_pairs_path": base_dir / "heritage_pairs.yaml",
        "synonym_verdicts_path": base_dir / "synonym_pair_verdicts.yaml",
        "cloze_sources_path": base_dir / "lexicon-practice-cloze-sources.json",
    }
    _write_atlas_db(paths["atlas_db_path"], entries or [], public_flags=public_flags)
    if heritage_pairs is not None:
        _write_json(paths["heritage_pairs_path"], {"pairs": heritage_pairs})
    if synonym_verdicts is not None:
        _write_json(paths["synonym_verdicts_path"], synonym_verdicts)
    if cloze_sources is not None:
        _write_json(paths["cloze_sources_path"], cloze_sources)
    return paths


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
    input_paths = _write_publish_inputs(tmp_path / "inputs")

    from scripts.practice_deck.publish import expected_deck_version, versioned_asset_name
    expected_version = expected_deck_version(**input_paths)
    _write_practice_deck(practice_dir, deck_version=expected_version)

    pointer = publish_practice_deck(
        practice_dir=practice_dir,
        gzip_path=gzip_path,
        dry_run=True,
        **input_paths,
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
    input_paths = _write_publish_inputs(tmp_path / "inputs")
    _write_practice_deck(practice_dir, deck_version="atlas-practice-v1-other")

    with pytest.raises(PracticeDeckPublishError, match="does not match expected version"):
        publish_practice_deck(
            practice_dir=practice_dir,
            gzip_path=tmp_path / "deck.json.gz",
            dry_run=True,
            **input_paths,
        )


def test_publish_practice_deck_uploads_versioned_and_canonical_assets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    practice_dir = tmp_path / "lexicon"
    gzip_path = tmp_path / "lexicon-practice-deck.json.gz"
    pointer_path = tmp_path / "lexicon-practice-deck.pointer.json"
    input_paths = _write_publish_inputs(tmp_path / "inputs")

    from scripts.practice_deck.publish import expected_deck_version, versioned_asset_name
    expected_version = expected_deck_version(**input_paths)
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
        repo="learn-ukrainian/example",
        **input_paths,
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
    gzip_path = tmp_path / "lexicon-practice-deck.json.gz"
    pointer_path = tmp_path / "lexicon-practice-deck.pointer.json"
    input_paths = _write_publish_inputs(tmp_path / "inputs")

    from scripts.practice_deck.publish import expected_deck_version, versioned_asset_name
    expected_version = expected_deck_version(**input_paths)
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
        repo="learn-ukrainian/example",
        dry_run=True,
        **input_paths,
    )

    publish_practice_deck(
        practice_dir=practice_dir,
        gzip_path=gzip_path,
        pointer_path=pointer_path,
        repo="learn-ukrainian/example",
        **input_paths,
    )

    assert download_calls == [expected_versioned_name]
    assert [Path(call[4]).name for call in upload_calls] == [ASSET_NAME]
    assert "--clobber" in upload_calls[0]


def test_expected_deck_version_uses_public_atlas_db_projection(tmp_path: Path) -> None:
    entries = read_manifest(MANIFEST)
    public_only_paths = _write_publish_inputs(
        tmp_path / "public-only",
        entries=[entries[0]],
    )
    with_private_paths = _write_publish_inputs(
        tmp_path / "with-private",
        entries=[entries[0], entries[1]],
        public_flags=[True, False],
    )

    from scripts.practice_deck.publish import expected_deck_version

    assert expected_deck_version(**with_private_paths) == expected_deck_version(**public_only_paths)


@pytest.mark.parametrize("stale_input", ["entries", "heritage_pairs", "synonym_verdicts", "cloze_sources"])
def test_publish_guard_passes_fresh_regen_and_fails_stale_shards(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stale_input: str,
) -> None:
    monkeypatch.setattr(publish_module, "LEVELS", ("A1",))
    practice_dir = tmp_path / "lexicon"
    gzip_path = tmp_path / "lexicon-practice-deck.json.gz"
    entries = read_manifest(MANIFEST)
    cloze_sources = read_cloze_sources(CLOZE_SOURCES)
    heritage_pairs = read_heritage_pairs(HERITAGE_PAIRS)
    synonym_verdicts = {"approved": [], "rejected": []}
    input_paths = _write_publish_inputs(
        tmp_path / "inputs",
        entries=entries,
        heritage_pairs=heritage_pairs,
        synonym_verdicts=synonym_verdicts,
        cloze_sources=cloze_sources,
    )
    shards = build_practice_shards(
        entries,
        ReviewedSourceAllowlist.from_path(ALLOWLIST),
        JsonVesumVerifier.from_path(VESUM),
        cloze_sources,
        BuildConfig(),
        heritage_pairs=heritage_pairs,
        synonym_verdicts=synonym_verdicts,
    )
    write_shards(shards, practice_dir)

    pointer = publish_practice_deck(
        practice_dir=practice_dir,
        gzip_path=gzip_path,
        dry_run=True,
        **input_paths,
    )
    assert pointer["deck_version"] == next(
        payload["deckVersion"]
        for level_shards in shards.values()
        for payload in level_shards.values()
    )

    if stale_input == "entries":
        stale_entries = json.loads(json.dumps(entries))
        stale_entries[0]["gloss"] = "changed stale gloss"
        _write_atlas_db(input_paths["atlas_db_path"], stale_entries)
    elif stale_input == "heritage_pairs":
        stale_heritage_pairs = json.loads(json.dumps(heritage_pairs))
        stale_heritage_pairs[0]["rationale"] = "changed stale rationale"
        _write_json(input_paths["heritage_pairs_path"], {"pairs": stale_heritage_pairs})
    elif stale_input == "synonym_verdicts":
        stale_synonym_verdicts = {
            "approved": [{"a": "кіт", "b": "пес", "polarity": "synonym"}],
            "rejected": [],
        }
        _write_json(input_paths["synonym_verdicts_path"], stale_synonym_verdicts)
    else:
        stale_cloze_sources = json.loads(json.dumps(cloze_sources))
        stale_cloze_sources[0]["sentence"] = "Свіжа версія має інше речення з ___."
        _write_json(input_paths["cloze_sources_path"], stale_cloze_sources)

    with pytest.raises(PracticeDeckPublishError, match="does not match expected version"):
        publish_practice_deck(
            practice_dir=practice_dir,
            gzip_path=gzip_path,
            dry_run=True,
            **input_paths,
        )


def test_publish_script_style_invocation_reaches_projection_read(tmp_path: Path) -> None:
    """The documented invocation (`make practice-deck-publish` → `$(PYTHON)
    scripts/practice_deck/publish.py`) runs SCRIPT-style, without a package context.
    The lazy `scripts.*` imports inside expected_deck_version() must still resolve
    (#4660 review fix — sys.path bootstrap; the #4529 lazy-absolute-import class).
    Hermetic: fixture shards in a tmp practice dir get PAST collect_shards, and an
    empty sqlite file gets PAST the exists() guard and INTO the lazy-import path."""
    import sys

    repo_root = Path(publish_module.__file__).resolve().parents[2]
    practice_dir = tmp_path / "lexicon"
    _write_practice_deck(practice_dir)
    empty_db = tmp_path / "atlas.db"
    empty_db.write_bytes(b"")
    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "practice_deck" / "publish.py"),
            "--dry-run",
            "--practice-dir",
            str(practice_dir),
            "--gzip",
            str(tmp_path / "deck.json.gz"),
            "--pointer",
            str(tmp_path / "pointer.json"),
            "--atlas-db",
            str(empty_db),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    combined = result.stdout + result.stderr
    assert result.returncode != 0
    assert "No module named 'scripts'" not in combined
    assert "Failed to calculate expected deck version" in combined
