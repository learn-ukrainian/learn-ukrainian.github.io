#!/usr/bin/env python3
"""Publish hydrated Atlas practice deck shards as one release asset."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PRACTICE_DIR = ROOT / "site" / "public" / "lexicon"
DEFAULT_POINTER = ROOT / "site" / "src" / "data" / "lexicon-practice-deck.pointer.json"
DEFAULT_GZIP = ROOT / "site" / "src" / "data" / "lexicon-practice-deck.json.gz"
DEFAULT_RELEASE_TAG = "atlas-practice-deck"
DEFAULT_REPO = "learn-ukrainian/learn-ukrainian.github.io"
ASSET_NAME = "lexicon-practice-deck.json.gz"
LEVELS = ("A1", "A2", "B1", "B2", "C1")
KINDS = {
    "index": ("practice-index.{level}.json", "atlas-practice-index"),
    "lexemes": ("practice-lexemes.{level}.json", "atlas-practice-lexemes"),
    "cloze": ("practice-cloze.{level}.json", "atlas-practice-cloze"),
}


class PracticeDeckPublishError(RuntimeError):
    """Raised when the practice deck release asset cannot be built."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _asset_url(repo: str, release_tag: str, asset_name: str = ASSET_NAME) -> str:
    return f"https://github.com/{repo}/releases/download/{release_tag}/{quote(asset_name)}"


def _read_json_bytes(path: Path) -> tuple[bytes, dict[str, Any]]:
    data = path.read_bytes()
    payload = json.loads(data.decode("utf-8"))
    if not isinstance(payload, dict):
        raise PracticeDeckPublishError(f"{path} must contain a JSON object")
    return data, payload


def _shard_metadata(path: Path, *, kind: str, level: str, deck_version: str | None) -> tuple[dict[str, Any], str]:
    data, payload = _read_json_bytes(path)
    expected_schema = KINDS[kind][1]
    if payload.get("schema") != expected_schema:
        raise PracticeDeckPublishError(f"{path} schema {payload.get('schema')!r} != {expected_schema!r}")
    if payload.get("schemaVersion") != 1:
        raise PracticeDeckPublishError(f"{path} schemaVersion must be 1")
    if payload.get("level") != level:
        raise PracticeDeckPublishError(f"{path} level {payload.get('level')!r} != {level!r}")
    shard_version = payload.get("deckVersion")
    if not isinstance(shard_version, str) or not shard_version:
        raise PracticeDeckPublishError(f"{path} missing deckVersion")
    if deck_version is not None and shard_version != deck_version:
        raise PracticeDeckPublishError(f"{path} deckVersion {shard_version!r} != {deck_version!r}")

    metadata: dict[str, Any] = {
        "path": path.name,
        "kind": kind,
        "level": level,
        "schema": expected_schema,
        "bytes": len(data),
        "sha256": _sha256(data),
    }
    counts = payload.get("counts")
    if kind == "index" and isinstance(counts, dict):
        metadata["counts"] = {
            "lexemes": counts.get("lexemes"),
            "cloze": counts.get("cloze"),
            "clozeEligibleLexemes": counts.get("clozeEligibleLexemes"),
            "clozeCoverage": counts.get("clozeCoverage"),
        }
    return metadata, shard_version


def collect_shards(practice_dir: Path = DEFAULT_PRACTICE_DIR) -> tuple[str, list[dict[str, Any]], list[dict[str, str]]]:
    deck_version: str | None = None
    pointer_files: list[dict[str, Any]] = []
    package_files: list[dict[str, str]] = []
    for level in LEVELS:
        for kind, (template, _schema) in KINDS.items():
            path = practice_dir / template.format(level=level)
            if not path.exists():
                raise PracticeDeckPublishError(f"{path} is missing")
            metadata, shard_version = _shard_metadata(path, kind=kind, level=level, deck_version=deck_version)
            if deck_version is None:
                deck_version = shard_version
            content = path.read_text(encoding="utf-8")
            pointer_files.append(metadata)
            package_files.append({"path": path.name, "content": content})
    if deck_version is None:
        raise PracticeDeckPublishError("practice deck has no shards")
    return deck_version, pointer_files, package_files


def build_package(deck_version: str, files: list[dict[str, str]]) -> bytes:
    package = {
        "schema": "atlas-practice-deck-package",
        "schemaVersion": 1,
        "deckVersion": deck_version,
        "files": files,
    }
    return json.dumps(package, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_pointer(
    *,
    deck_version: str,
    pointer_files: list[dict[str, Any]],
    package_bytes: bytes,
    gzip_bytes: bytes,
    release_tag: str = DEFAULT_RELEASE_TAG,
    repo: str = DEFAULT_REPO,
) -> dict[str, Any]:
    return {
        "asset_url": _asset_url(repo, release_tag),
        "release_tag": release_tag,
        "deck_version": deck_version,
        "package_schema_version": 1,
        "gz_sha256": _sha256(gzip_bytes),
        "package_sha256": _sha256(package_bytes),
        "gz_bytes": len(gzip_bytes),
        "package_bytes": len(package_bytes),
        "file_count": len(pointer_files),
        "files": pointer_files,
        "note": "Pins GitHub Release asset practice deck for #3796; hydrate it build/test time instead of committing shards.",
    }


def write_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    pointer_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = pointer_path.with_suffix(f"{pointer_path.suffix}.tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp_path.replace(pointer_path)


def ensure_release(release_tag: str, repo: str) -> None:
    existing = subprocess.run(
        ["gh", "release", "view", release_tag, "--repo", repo],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if existing.returncode == 0:
        return
    subprocess.run(
        [
            "gh",
            "release",
            "create",
            release_tag,
            "--repo",
            repo,
            "--title",
            "Atlas practice deck",
            "--notes",
            "Release asset storage for generated Atlas practice deck shards.",
        ],
        check=True,
    )


def upload_release_asset(gzip_path: Path, *, release_tag: str, repo: str) -> None:
    ensure_release(release_tag, repo)
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


def publish_practice_deck(
    *,
    practice_dir: Path = DEFAULT_PRACTICE_DIR,
    gzip_path: Path = DEFAULT_GZIP,
    pointer_path: Path = DEFAULT_POINTER,
    release_tag: str = DEFAULT_RELEASE_TAG,
    repo: str = DEFAULT_REPO,
    dry_run: bool = False,
) -> dict[str, Any]:
    deck_version, pointer_files, package_files = collect_shards(practice_dir)
    package_bytes = build_package(deck_version, package_files)
    gzip_bytes = gzip.compress(package_bytes, compresslevel=9, mtime=0)
    gzip_path.parent.mkdir(parents=True, exist_ok=True)
    gzip_path.write_bytes(gzip_bytes)
    pointer = build_pointer(
        deck_version=deck_version,
        pointer_files=pointer_files,
        package_bytes=package_bytes,
        gzip_bytes=gzip_bytes,
        release_tag=release_tag,
        repo=repo,
    )
    if dry_run:
        return pointer
    upload_release_asset(gzip_path, release_tag=release_tag, repo=repo)
    write_pointer(pointer_path, pointer)
    return pointer


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish the Atlas practice deck release asset.")
    parser.add_argument("--practice-dir", type=Path, default=DEFAULT_PRACTICE_DIR)
    parser.add_argument("--gzip", type=Path, default=DEFAULT_GZIP)
    parser.add_argument("--pointer", type=Path, default=DEFAULT_POINTER)
    parser.add_argument("--release-tag", default=DEFAULT_RELEASE_TAG)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--dry-run", action="store_true", help="Build metadata without uploading/writing pointer")
    args = parser.parse_args()
    pointer = publish_practice_deck(
        practice_dir=args.practice_dir,
        gzip_path=args.gzip,
        pointer_path=args.pointer,
        release_tag=args.release_tag,
        repo=args.repo,
        dry_run=args.dry_run,
    )
    print(
        "Atlas practice deck pointer "
        f"{'would publish' if args.dry_run else 'published'}: "
        f"{pointer['deck_version']} {pointer['file_count']} shards"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
