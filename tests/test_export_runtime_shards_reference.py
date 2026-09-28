"""Runtime shard exporter reference tests, split for loadfile scheduling."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import random
import sqlite3
from pathlib import Path

import pytest

from scripts.atlas import export_runtime_shards as exporter
from scripts.atlas.export_runtime_shards import (
    EntryReplay,
    ExportError,
    compress_stream_bounded,
    compute_data_version,
    gzip_bytes,
    load_entry_records,
    load_search_rows,
    open_readonly_db,
    verify_tree,
)
from scripts.atlas.normalization import normalize_atlas_text
from tests.test_export_runtime_shards import (
    _REEXPORT_STAGES,
    _export,
    _fail_after_writes,
    _Injected,
    _make_source_db,
    _ref_data_version,
    _ref_load_entry_records,
    _ref_load_search_rows,
    _reference_export,
    _snapshot,
    _traced_in_fresh_interpreter,
    _version_dirs,
)

pytest_plugins = ("tests._export_runtime_shards_fixtures",)

def test_fixture_export_is_byte_identical_to_reference(fixture_db: Path, tmp_path: Path) -> None:
    data_version, files, _ = _reference_export(
        fixture_db, compression_level=9, entry_max=8_000, search_max=1_000
    )
    out = tmp_path / "out"
    _export(fixture_db, out, entry_max_gzip_bytes=8_000, search_max_gzip_bytes=1_000)
    tree = _snapshot(out / "atlas" / "versions" / data_version)
    assert {name: blob for name, blob in tree.items() if name != "manifest.json"} == files


def test_replay_records_and_search_rows_match_reference_loaders(edge_db: Path, fixture_db: Path) -> None:
    for db in (edge_db, fixture_db):
        conn = open_readonly_db(db)
        try:
            expected = _ref_load_entry_records(conn, {"слово001": ["A1", "B1"]})
            replay = EntryReplay(conn, practice_levels_by_slug={"слово001": ["A1", "B1"]})
            assert list(replay.iter_records()) == expected
            assert [replay.record_for_slug(r["slug"]) for r in expected] == expected
            assert load_entry_records(conn, practice_levels_by_slug={"слово001": ["A1", "B1"]}) == expected
            assert load_search_rows(conn) == _ref_load_search_rows(conn)
        finally:
            conn.close()


def test_export_rejects_legacy_soviet_citation_in_learner_card(tmp_path: Path) -> None:
    conn = sqlite3.connect(_make_source_db(tmp_path / "legacy.db"))
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT slug, payload_json FROM article_payloads WHERE is_public_route = 1 LIMIT 1").fetchone()
    assert row is not None
    payload = json.loads(row[1])
    payload["sections"] = {"synonyms": {"items": ["слово"], "source": "СУМ-11"}}
    conn.execute(
        "UPDATE article_payloads SET payload_json = ? WHERE slug = ?",
        (json.dumps(payload, ensure_ascii=False), row[0]),
    )
    conn.commit()
    with pytest.raises(ExportError, match="СУМ-11 citation outside"):
        EntryReplay(conn, practice_levels_by_slug={}).record_for_slug(row[0])
    conn.close()


def test_export_rejects_unmarked_contrast_citation(tmp_path: Path) -> None:
    conn = sqlite3.connect(_make_source_db(tmp_path / "unmarked.db"))
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT slug, payload_json FROM article_payloads WHERE is_public_route = 1 LIMIT 1").fetchone()
    assert row is not None
    payload = json.loads(row[1])
    payload["soviet_colonization_context"] = {
        "source": "СУМ-11", "definition": "historical contrast", "sovietization_risk": 1
    }
    payload["red_flag"] = True  # An unrelated field cannot mark the cited context.
    conn.execute(
        "UPDATE article_payloads SET payload_json = ? WHERE slug = ?",
        (json.dumps(payload, ensure_ascii=False), row[0]),
    )
    conn.commit()
    with pytest.raises(ExportError, match="russification marker"):
        EntryReplay(conn, practice_levels_by_slug={}).record_for_slug(row[0])
    conn.close()


def test_export_accepts_marked_contrast_citation(tmp_path: Path) -> None:
    conn = sqlite3.connect(_make_source_db(tmp_path / "marked.db"))
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT slug, payload_json FROM article_payloads WHERE is_public_route = 1 LIMIT 1").fetchone()
    assert row is not None
    payload = json.loads(row[1])
    payload["soviet_colonization_context"] = {
        "source": "СУМ-11",
        "red_flag": True,
        "sovietization_risk": 1,
        "definition": "historical contrast",
    }
    conn.execute(
        "UPDATE article_payloads SET payload_json = ? WHERE slug = ?",
        (json.dumps(payload, ensure_ascii=False), row[0]),
    )
    conn.commit()
    record = EntryReplay(conn, practice_levels_by_slug={}).record_for_slug(row[0])
    assert record["slug"] == row[0]
    conn.close()


def test_search_alias_dedup_keeps_reference_survivors(edge_db: Path) -> None:
    conn = open_readonly_db(edge_db)
    try:
        _, aliases = load_search_rows(conn)
        raw = conn.execute("SELECT COUNT(*) FROM aliases WHERE visibility = 'public'").fetchone()[0]
        assert len(aliases) < raw, "fixture must actually contain normalization duplicates"
        assert aliases == _ref_load_search_rows(conn)[1]
        assert len({(normalize_atlas_text(a["a"]), a["s"]) for a in aliases}) == len(aliases)
    finally:
        conn.close()


def test_unicode_search_order_follows_code_points(edge_db: Path) -> None:
    conn = open_readonly_db(edge_db)
    try:
        articles, _ = load_search_rows(conn)
    finally:
        conn.close()
    heads = [normalize_atlas_text(row["l"]) for row in articles]
    assert heads == sorted(heads)
    assert heads.index("ﬀ") < heads.index("\U0001f600"), "UTF-16 order would invert these"


def test_data_version_hasher_matches_reference_identity(edge_db: Path) -> None:
    conn = open_readonly_db(edge_db)
    try:
        records = _ref_load_entry_records(conn, {})
        articles, aliases = _ref_load_search_rows(conn)
    finally:
        conn.close()
    deck_index = {"levels": {"B1": {"deckVersion": "d2"}, "A1": {"deckVersion": "d1"}}}
    kwargs = {
        "generated_at": "2026-01-02T03:04:05+00:00", "article_rows": articles,
        "alias_rows": aliases, "deck_index": deck_index,
    }
    assert compute_data_version(entry_records=records, **kwargs) == _ref_data_version(
        entry_records=records, **kwargs
    )
    empty = {"generated_at": "g", "article_rows": [], "alias_rows": [], "deck_index": {"levels": {}}}
    assert compute_data_version(entry_records=[], **empty) == _ref_data_version(entry_records=[], **empty)


@pytest.mark.parametrize("level", [0, 1, 2, 5, 6, 9])
def test_stream_compression_matches_one_shot_gzip(level: int) -> None:
    rng = random.Random(level)
    text = "".join(rng.choice("абвгдеж abc012,.\n") for _ in range(400_000)).encode("utf-8")
    for size in (0, 1, 300, 70_000, len(text)):
        raw = text[:size]
        expected = gzip_bytes(raw, compression_level=level)
        for chunk in (1, 7, 4_096, 65_536 + 3):
            chunks = [raw[i : i + chunk] for i in range(0, len(raw), chunk)]
            result = compress_stream_bounded(lambda chunks=chunks: chunks, compression_level=level, max_bytes=None)
            assert result is not None
            assert result.compressed == expected
            assert result.uncompressed_bytes == len(raw)
            assert result.json_sha256 == hashlib.sha256(raw).hexdigest()
            assert gzip.decompress(result.compressed) == raw
        # Exact cap boundary: fits at len, aborts at len - 1.
        chunks = [raw[i : i + 999] for i in range(0, len(raw), 999)]
        source = lambda chunks=chunks: chunks  # noqa: E731
        assert compress_stream_bounded(source, compression_level=level, max_bytes=len(expected)) is not None
        assert compress_stream_bounded(source, compression_level=level, max_bytes=len(expected) - 1) is None


def test_stream_compression_aborts_before_consuming_source() -> None:
    pulled = 0

    def source():
        nonlocal pulled
        rng = random.Random(1)
        while True:
            pulled += 1
            yield bytes(rng.getrandbits(8) for _ in range(4_096))

    for level in (0, 1, 9):
        pulled = 0
        assert compress_stream_bounded(source, compression_level=level, max_bytes=20_000) is None
        assert pulled < 20, "an oversized candidate must stop the replay early"


def test_oversized_entry_leaf_matches_reference_error(edge_db: Path, tmp_path: Path) -> None:
    with pytest.raises(ExportError) as expected:
        _reference_export(edge_db, compression_level=9, entry_max=300, search_max=524_288)
    with pytest.raises(ExportError) as actual:
        _export(edge_db, tmp_path / "out", entry_max_gzip_bytes=300)
    assert str(actual.value) == str(expected.value)
    assert "single entry record exceeds" in str(actual.value)
    assert not (tmp_path / "out" / "atlas" / "current.json").exists()


def test_unsplittable_search_shard_matches_reference_error(edge_db: Path, tmp_path: Path) -> None:
    with pytest.raises(ExportError) as expected:
        _reference_export(edge_db, compression_level=9, entry_max=1_048_576, search_max=150)
    with pytest.raises(ExportError) as actual:
        _export(edge_db, tmp_path / "out", search_max_gzip_bytes=150)
    assert str(actual.value) == str(expected.value)
    assert "cannot split" in str(actual.value)


def test_failed_first_export_publishes_nothing(edge_db: Path, tmp_path: Path, monkeypatch) -> None:
    def boom(*_args, **_kwargs):
        raise RuntimeError("injected")

    monkeypatch.setattr(exporter, "verify_tree", boom)
    out = tmp_path / "out"
    with pytest.raises(RuntimeError, match="injected"):
        _export(edge_db, out)
    assert not (out / "atlas" / "current.json").exists()
    assert _snapshot(out) == {}, "no staged objects may remain"


@pytest.mark.parametrize("stage", _REEXPORT_STAGES)
def test_failed_reexport_keeps_current_pointer_and_referenced_tree_byte_identical(
    edge_db: Path, tmp_path: Path, monkeypatch, stage: str
) -> None:
    out = tmp_path / "out"
    kwargs = {"entry_max_gzip_bytes": 9_000, "search_max_gzip_bytes": 1_200}
    report = _export(edge_db, out, **kwargs)
    before = _snapshot(out)
    current = json.loads(before["atlas/current.json"])
    assert current["dataVersion"] == report["dataVersion"]  # re-export targets the referenced version
    total_objects = sum(1 for name in before if name.startswith(f"atlas/versions/{report['dataVersion']}/"))
    transport = stage.endswith("-transport")
    reexport = {**kwargs, "compression_level": 6} if transport else kwargs

    real_rename, real_replace = os.rename, os.replace
    if stage == "first-leaf":
        _fail_after_writes(monkeypatch, 0)
    elif stage == "mid-export":
        _fail_after_writes(monkeypatch, total_objects // 2)
    elif stage == "manifest":
        _fail_after_writes(monkeypatch, total_objects - 1)
    elif stage == "verify":
        monkeypatch.setattr(exporter, "verify_tree", lambda *a, **k: (_ for _ in ()).throw(_Injected("verify")))
    elif stage == "swap-transport":
        def rename(src, dst, *a, **k):
            if Path(src).name.startswith(".export-"):
                raise _Injected("swap")
            return real_rename(src, dst, *a, **k)

        monkeypatch.setattr(exporter.os, "rename", rename)
    else:
        def replace(src, dst, *a, **k):
            if Path(dst).name == "current.json":
                raise _Injected("pointer")
            return real_replace(src, dst, *a, **k)

        monkeypatch.setattr(exporter.os, "replace", replace)

    with pytest.raises(_Injected):
        _export(edge_db, out, **reexport)
    monkeypatch.undo()
    after = _snapshot(out)
    # The pointer and every previously installed object are byte-identical; the only
    # thing a failure may leave is a complete, unreferenced alternate tree.
    assert {name: blob for name, blob in after.items() if name in before} == before
    assert all(
        name.startswith(f"atlas/versions/{report['dataVersion']}-transport-") for name in after.keys() - before.keys()
    )
    if stage != "pointer-transport":
        assert after.keys() == before.keys()
    assert verify_tree(out, "atlas")["dataVersion"] == report["dataVersion"]
    assert _snapshot(out) == after

    # And a subsequent healthy re-export still succeeds and the referenced tree is intact.
    _export(edge_db, out, **reexport)
    healed = _snapshot(out)
    assert {name: blob for name, blob in healed.items() if name in before and name != "atlas/current.json"} == {
        name: blob for name, blob in before.items() if name != "atlas/current.json"
    }
    assert verify_tree(out, "atlas")["dataVersion"] == report["dataVersion"]
    if not transport:
        assert healed == before


def test_stale_staging_from_killed_export_is_reclaimed(edge_db: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    versions = out / "atlas" / "versions"
    dead = versions / ".export-999999999-deadbeef"
    dead.mkdir(parents=True)
    (dead / "orphan.bin").write_bytes(b"x")
    alive = versions / f".export-{os.getpid()}-cafebabe"
    alive.mkdir()
    _export(edge_db, out)
    assert not dead.exists()
    assert alive.exists(), "another live exporter's staging tree must not be touched"


def test_export_memory_is_bounded_by_leaf_not_corpus(tmp_path: Path) -> None:
    """Peak Python heap stays a small fraction of the payload volume being exported."""
    db = _make_source_db(tmp_path / "big.db", records=240, filler_chars=60_000, seed=5)
    payload_bytes = sum(
        len(row[0]) for row in sqlite3.connect(db).execute("SELECT payload_json FROM article_payloads")
    )
    assert payload_bytes > 14_000_000
    kwargs = {"include_decks": False, "deck_dir": None, "verify": True, "compression_level": 1,
              "entry_max_gzip_bytes": 150_000}
    error, peak = _traced_in_fresh_interpreter("export", db=db, out=tmp_path / "out", kwargs=kwargs)
    assert error is None
    assert peak < payload_bytes * 0.25, f"peak {peak} vs payload {payload_bytes}"


def test_identical_reexport_reuses_installed_tree_untouched(edge_db: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    report = _export(edge_db, out)
    tree = out / "atlas" / "versions" / report["dataVersion"]
    before, stat = _snapshot(out), tree.stat()
    again = _export(edge_db, out)
    assert _snapshot(out) == before
    assert tree.stat().st_ino == stat.st_ino and tree.stat().st_mtime_ns == stat.st_mtime_ns
    assert _version_dirs(out) == [report["dataVersion"]]
    assert report["manifestUrl"] == again["manifestUrl"] == f"versions/{report['dataVersion']}/manifest.json"
