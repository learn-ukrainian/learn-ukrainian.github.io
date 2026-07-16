"""Acceptance tests for the Atlas runtime shard exporter (PR #1 contract).

Core contract tests run against a committed hermetic fixture DB so CI does not
depend on the ~149 MB ``data/atlas.db``. Real-DB count assertions remain
opt-in via ``skipif`` when the full atlas is present locally.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path

import pytest

from scripts.atlas.export_runtime_shards import (
    ExportError,
    export_runtime_shards,
    find_component_tokens,
    load_component_tokenization_vectors,
    load_entry_records,
    load_practice_levels_by_slug,
    open_readonly_db,
    tree_fingerprint,
    verify_tree,
)
from scripts.atlas.normalization import load_normalization_vectors, normalize_atlas_text

ROOT = Path(__file__).resolve().parents[1]
REAL_DB_PATH = ROOT / "data" / "atlas.db"
FIXTURE_DB_PATH = ROOT / "tests" / "fixtures" / "atlas" / "runtime_shards_fixture.db"
PRACTICE_DECKS_ROOT = ROOT / "tests" / "fixtures" / "atlas" / "practice_decks"
EXPORTER_SCRIPT = ROOT / "scripts" / "atlas" / "export_runtime_shards.py"


@pytest.fixture(scope="module")
def fixture_db() -> Path:
    assert FIXTURE_DB_PATH.is_file(), f"missing fixture DB: {FIXTURE_DB_PATH}"
    return FIXTURE_DB_PATH


def _fp(root: Path) -> str:
    return tree_fingerprint(root)


def test_normalization_vectors_match_python_rules() -> None:
    for case in load_normalization_vectors():
        assert normalize_atlas_text(case["input"]) == case["expected"], case


def test_component_tokenization_vectors_match_python_rules() -> None:
    for case in load_component_tokenization_vectors():
        assert find_component_tokens(str(case["input"])) == case["expected"], case


def test_script_path_invocation_exits_zero() -> None:
    """F007: ``python scripts/atlas/export_runtime_shards.py`` must not ModuleNotFoundError."""
    result = subprocess.run(
        [str(ROOT / ".venv" / "bin" / "python"), str(EXPORTER_SCRIPT), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout.lower()


def test_practice_levels_prefer_api_lexicon_and_lemma_id_only(fixture_db: Path) -> None:
    """F002: mirror SqliteAtlasDataSource — api/lexicon first, index lemmaId only."""
    deck_dir = PRACTICE_DECKS_ROOT / "lexicon"
    levels = load_practice_levels_by_slug(deck_dir)
    # api/lexicon A1 wins over lexicon/ A1 (which only lists файний).
    assert levels["прапор"] == ["A1"]
    assert levels["доконаний-вид"] == ["A1"]
    assert "файний" not in levels
    # lexicon-only A2 still applies when api has no A2 index.
    assert levels["іван"] == ["A2"]
    # lemma text must not become an index key (would poison ласка / вид).
    assert "ласка" not in levels
    assert "вид" not in levels

    conn = open_readonly_db(fixture_db)
    try:
        records = {
            record["slug"]: record
            for record in load_entry_records(conn, practice_levels_by_slug=levels)
        }
    finally:
        conn.close()

    assert records["прапор"]["renderContext"]["practiceLevels"] == ["A1"]
    assert records["доконаний-вид"]["renderContext"]["practiceLevels"] == ["A1"]
    assert records["іван"]["renderContext"]["practiceLevels"] == ["A2"]
    assert records["ласка"]["renderContext"]["practiceLevels"] == []
    assert records["вид"]["renderContext"]["practiceLevels"] == []
    assert records["файний"]["renderContext"]["practiceLevels"] == []


def test_export_twice_is_byte_identical(fixture_db: Path, tmp_path: Path) -> None:
    """Determinism must not depend on hydrated practice decks."""
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    report_a = export_runtime_shards(
        db_path=fixture_db,
        out_dir=out_a,
        deck_dir=None,
        include_decks=False,
        verify=True,
    )
    report_b = export_runtime_shards(
        db_path=fixture_db,
        out_dir=out_b,
        deck_dir=None,
        include_decks=False,
        verify=True,
    )
    assert report_a["dataVersion"] == report_b["dataVersion"]
    assert report_a["dataVersion"].startswith("atlas-v1-")
    assert _fp(out_a / "atlas") == _fp(out_b / "atlas")


def test_fixture_covers_representative_entry_shapes(fixture_db: Path) -> None:
    conn = open_readonly_db(fixture_db)
    try:
        records = load_entry_records(conn, practice_levels_by_slug={})
    finally:
        conn.close()

    by_slug = {record["slug"]: record for record in records}
    assert "прапор" in by_slug
    assert by_slug["прапор"]["kind"] == "article"
    morph = (by_slug["прапор"]["entry"].get("enrichment") or {}).get("morphology")
    assert isinstance(morph, dict) and morph.get("marked_forms")

    assert by_slug["іване"]["kind"] == "form_route"
    assert by_slug["іване"]["entry"]["form_of"]["url_slug"] == "іван"

    assert any(alias["alias"] == "prapor" for alias in by_slug["прапор"]["aliases"])
    assert by_slug["достовірний"]["entry"]["heritage_status"]["classification"] == "russianism"

    links = by_slug["доконаний-вид"]["renderContext"]["componentLinks"]
    assert links == [
        {"text": "доконаний", "targetSlug": "доконаний"},
        {"text": "вид", "targetSlug": "вид"},
    ]


def test_trie_split_and_checksum_fail_closed(fixture_db: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    # Force the SHA-256 prefix trie to split by lowering the entry gzip ceiling.
    report = export_runtime_shards(
        db_path=fixture_db,
        out_dir=out,
        include_decks=False,
        deck_dir=None,
        verify=True,
        # Large enough for the biggest single fixture record (~4 KiB gzip),
        # small enough to force the SHA-256 prefix trie to split the set.
        entry_max_gzip_bytes=8_000,
    )
    assert report["counts"]["entryShards"] >= 2, report["counts"]

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


def test_search_families_remain_separate(fixture_db: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    report = export_runtime_shards(
        db_path=fixture_db,
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
    assert report["counts"]["searchArticles"] == report["counts"]["articles"]
    assert report["counts"]["searchAliases"] <= report["counts"]["aliases"]
    assert report["counts"]["searchAliases"] > 0


def test_exported_entry_records_match_sqlite_projection(fixture_db: Path, tmp_path: Path) -> None:
    """Export records must match the Sqlite data-source projection (parity input)."""
    out = tmp_path / "out"
    export_runtime_shards(
        db_path=fixture_db,
        out_dir=out,
        include_decks=False,
        deck_dir=None,
        verify=True,
    )
    conn = open_readonly_db(fixture_db)
    try:
        expected = {
            record["slug"]: record
            for record in load_entry_records(conn, practice_levels_by_slug={})
        }
    finally:
        conn.close()

    current = json.loads((out / "atlas" / "current.json").read_text(encoding="utf-8"))
    version_root = (out / "atlas" / current["manifestUrl"]).parent
    manifest = json.loads((version_root / "manifest.json").read_text(encoding="utf-8"))
    exported: dict[str, dict] = {}
    for descriptor in manifest["entries"]["shards"].values():
        raw = gzip.decompress((version_root / descriptor["url"]).read_bytes())
        payload = json.loads(raw.decode("utf-8"))
        for record in payload["records"]:
            exported[record["slug"]] = record

    assert set(exported) == set(expected)
    for slug, left in expected.items():
        right = exported[slug]
        assert right["kind"] == left["kind"]
        assert right["entry"] == left["entry"]
        assert right["aliases"] == left["aliases"]
        assert right["relations"] == left["relations"]
        assert right["provenance"] == left["provenance"]
        assert right["renderContext"] == left["renderContext"]


def test_data_version_assert_flag(fixture_db: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    report = export_runtime_shards(
        db_path=fixture_db,
        out_dir=out,
        include_decks=False,
        deck_dir=None,
        verify=False,
    )
    with pytest.raises(ExportError, match="data-version mismatch"):
        export_runtime_shards(
            db_path=fixture_db,
            out_dir=tmp_path / "out2",
            include_decks=False,
            deck_dir=None,
            expected_data_version="atlas-v1-deadbeefdeadbeef",
        )
    export_runtime_shards(
        db_path=fixture_db,
        out_dir=tmp_path / "out3",
        include_decks=False,
        deck_dir=None,
        expected_data_version=report["dataVersion"],
    )


def test_gzip_mtime_zero_and_newline_termination(fixture_db: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    export_runtime_shards(
        db_path=fixture_db,
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
        assert compressed[4:8] == b"\x00\x00\x00\x00"
        raw = gzip.decompress(compressed)
        assert raw.endswith(b"\n")
        assert hashlib.sha256(compressed).hexdigest() == descriptor["sha256"]
        assert hashlib.sha256(raw).hexdigest() == descriptor["jsonSha256"]


@pytest.mark.skipif(not REAL_DB_PATH.is_file(), reason="data/atlas.db not available")
def test_real_db_public_counts_and_alias_targets(tmp_path: Path) -> None:
    out = tmp_path / "out"
    report = export_runtime_shards(
        db_path=REAL_DB_PATH,
        out_dir=out,
        include_decks=False,
        deck_dir=None,
        verify=True,
    )
    assert report["counts"]["articles"] == 8206
    assert report["counts"]["formRoutes"] == 336
    assert report["counts"]["publicRoutes"] == 8542
    assert report["counts"]["aliases"] == 9969
    assert report["counts"]["articles"] + report["counts"]["formRoutes"] == report["counts"][
        "publicRoutes"
    ]

    conn = sqlite3.connect(f"file:{REAL_DB_PATH}?mode=ro", uri=True)
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


@pytest.mark.skipif(not REAL_DB_PATH.is_file(), reason="data/atlas.db not available")
def test_real_db_entry_shard_size_band(tmp_path: Path) -> None:
    out = tmp_path / "out"
    report = export_runtime_shards(
        db_path=REAL_DB_PATH,
        out_dir=out,
        include_decks=False,
        deck_dir=None,
        verify=True,
    )
    sizes = report["entryShardBytes"]
    assert sizes, "expected entry shards"
    assert min(sizes) >= 524_288, sizes
    assert max(sizes) <= 1_048_576, sizes
