"""Acceptance tests for the Atlas runtime shard exporter (PR #1 contract)."""

from __future__ import annotations

import gzip
import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from scripts.atlas.export_runtime_shards import (
    ExportError,
    export_runtime_shards,
    tree_fingerprint,
    verify_tree,
)
from scripts.atlas.normalization import load_normalization_vectors, normalize_atlas_text

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "atlas.db"
DECK_DIR = ROOT / "site" / "public" / "lexicon"


pytestmark = pytest.mark.skipif(not DB_PATH.is_file(), reason="data/atlas.db not available")


def _fp(root: Path) -> str:
    return tree_fingerprint(root)


def test_normalization_vectors_match_python_rules() -> None:
    for case in load_normalization_vectors():
        assert normalize_atlas_text(case["input"]) == case["expected"], case


def test_export_twice_is_byte_identical(tmp_path: Path) -> None:
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    report_a = export_runtime_shards(
        db_path=DB_PATH,
        out_dir=out_a,
        deck_dir=DECK_DIR if DECK_DIR.is_dir() else None,
        include_decks=DECK_DIR.is_dir(),
        verify=True,
    )
    report_b = export_runtime_shards(
        db_path=DB_PATH,
        out_dir=out_b,
        deck_dir=DECK_DIR if DECK_DIR.is_dir() else None,
        include_decks=DECK_DIR.is_dir(),
        verify=True,
    )
    assert report_a["dataVersion"] == report_b["dataVersion"]
    assert report_a["dataVersion"].startswith("atlas-v1-")
    assert _fp(out_a / "atlas") == _fp(out_b / "atlas")


def test_public_counts_and_alias_targets(tmp_path: Path) -> None:
    out = tmp_path / "out"
    report = export_runtime_shards(
        db_path=DB_PATH,
        out_dir=out,
        include_decks=False,
        deck_dir=None,
        verify=True,
    )
    assert report["counts"]["articles"] == 8206
    assert report["counts"]["formRoutes"] == 336
    assert report["counts"]["publicRoutes"] == 8542
    assert report["counts"]["aliases"] == 9969
    # Aliases must not inflate article totals.
    assert report["counts"]["articles"] + report["counts"]["formRoutes"] == report["counts"][
        "publicRoutes"
    ]

    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        invalid = conn.execute(
            """SELECT COUNT(*)
               FROM aliases AS alias
               LEFT JOIN articles AS article ON article.slug = alias.target_slug
               WHERE alias.visibility = 'public'
                 AND (
                     article.slug IS NULL
                     OR article.review_state != 'approved'
                     OR article.visibility != 'public'
                 )"""
        ).fetchone()[0]
    finally:
        conn.close()
    assert invalid == 0


def test_entry_shard_size_band_and_descriptor_integrity(tmp_path: Path) -> None:
    out = tmp_path / "out"
    report = export_runtime_shards(
        db_path=DB_PATH,
        out_dir=out,
        include_decks=False,
        deck_dir=None,
        verify=True,
    )
    sizes = report["entryShardBytes"]
    assert sizes, "expected entry shards"
    assert min(sizes) >= 524_288, sizes
    assert max(sizes) <= 1_048_576, sizes

    # One-byte corruption must fail closed.
    current = json.loads((out / "atlas" / "current.json").read_text(encoding="utf-8"))
    manifest = json.loads((out / "atlas" / current["manifestUrl"]).read_text(encoding="utf-8"))
    first_id = sorted(manifest["entries"]["shards"])[0]
    descriptor = manifest["entries"]["shards"][first_id]
    shard_path = (out / "atlas" / current["manifestUrl"]).parent / descriptor["url"]
    blob = bytearray(shard_path.read_bytes())
    blob[0] = (blob[0] + 1) % 256
    shard_path.write_bytes(bytes(blob))
    with pytest.raises(ExportError, match=r"sha256 mismatch|verify failed"):
        verify_tree(out, "atlas")


def test_search_families_remain_separate(tmp_path: Path) -> None:
    out = tmp_path / "out"
    report = export_runtime_shards(
        db_path=DB_PATH,
        out_dir=out,
        include_decks=False,
        deck_dir=None,
        verify=True,
    )
    current = json.loads((out / "atlas" / "current.json").read_text(encoding="utf-8"))
    manifest = json.loads((out / "atlas" / current["manifestUrl"]).read_text(encoding="utf-8"))
    for desc in manifest["search"]["articles"]["shards"].values():
        assert desc["url"].startswith("search/articles/")
    for desc in manifest["search"]["aliases"]["shards"].values():
        assert desc["url"].startswith("search/aliases/")
    assert report["counts"]["searchArticles"] == 8206
    assert report["counts"]["searchAliases"] <= report["counts"]["aliases"]
    assert report["counts"]["searchAliases"] > 0


def test_data_version_assert_flag(tmp_path: Path) -> None:
    out = tmp_path / "out"
    report = export_runtime_shards(
        db_path=DB_PATH,
        out_dir=out,
        include_decks=False,
        deck_dir=None,
        verify=False,
    )
    with pytest.raises(ExportError, match="data-version mismatch"):
        export_runtime_shards(
            db_path=DB_PATH,
            out_dir=tmp_path / "out2",
            include_decks=False,
            deck_dir=None,
            expected_data_version="atlas-v1-deadbeefdeadbeef",
        )
    # Matching assert succeeds.
    export_runtime_shards(
        db_path=DB_PATH,
        out_dir=tmp_path / "out3",
        include_decks=False,
        deck_dir=None,
        expected_data_version=report["dataVersion"],
    )


def test_gzip_mtime_zero_and_newline_termination(tmp_path: Path) -> None:
    out = tmp_path / "out"
    export_runtime_shards(
        db_path=DB_PATH,
        out_dir=out,
        include_decks=False,
        deck_dir=None,
        verify=True,
    )
    current = json.loads((out / "atlas" / "current.json").read_text(encoding="utf-8"))
    manifest = json.loads((out / "atlas" / current["manifestUrl"]).read_text(encoding="utf-8"))
    version_root = (out / "atlas" / current["manifestUrl"]).parent
    for descriptor in list(manifest["entries"]["shards"].values())[:3]:
        compressed = (version_root / descriptor["url"]).read_bytes()
        # gzip header mtime bytes 4-7 must be zero for determinism.
        assert compressed[4:8] == b"\x00\x00\x00\x00"
        raw = gzip.decompress(compressed)
        assert raw.endswith(b"\n")
        assert hashlib.sha256(compressed).hexdigest() == descriptor["sha256"]
        assert hashlib.sha256(raw).hexdigest() == descriptor["jsonSha256"]
