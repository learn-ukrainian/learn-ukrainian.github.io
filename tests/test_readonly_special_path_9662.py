"""Paths containing ? and # stay read-only through the #9662 slice 3d helpers."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MIGRATED = (
    "scripts/agent_runtime/lane_probe.py",
    "scripts/agent_runtime/runner.py",
    "scripts/api/dashboard_comms.py",
    "scripts/api/preload.py",
    "scripts/api/runtime_router.py",
)
PENDING = {
    "scripts/delegate.py",
    "scripts/projects/open_model_data/admit_existing_corpus.py",
    "scripts/projects/open_model_data/build_decolonization_cases.py",
    "scripts/projects/open_model_data/phase3_heldout_partition.py",
    "scripts/projects/open_model_data/phase3_source_universe.py",
    "scripts/projects/open_model_data/phase3_textbook_nonhit.py",
    "scripts/projects/open_model_data/review_build/components/__init__.py",
}


def _special(tmp_path: Path) -> Path:
    return tmp_path / "observer?# evidence.db"


def _write_db(path: Path, script: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.executescript(script)
    return path


def _assert_exact_readonly(connection: sqlite3.Connection, path: Path) -> None:
    listed = connection.execute("PRAGMA database_list").fetchone()[2]
    assert listed == str(path.resolve())
    with pytest.raises(sqlite3.OperationalError):
        connection.execute("CREATE TABLE forbidden (value TEXT)")


def test_named_module_boundary_refuses_sqlite_and_imports_json():
    from scripts.lib.readonly_sqlite import import_named_module

    with pytest.raises(ImportError):
        import_named_module("sqlite3")
    with pytest.raises(ImportError):
        import_named_module("_sqlite3")
    with pytest.raises(ImportError):
        import_named_module("sqlite3.dbapi2")
    assert import_named_module("json") is json


def test_slice_manifest_rows_are_cleared_and_seven_pending_remain():
    from scripts.hygiene.lint_source_db_writable_connects import classify_source

    manifest = json.loads((ROOT / "scripts/hygiene/sqlite_reference_allowlist.json").read_text())
    pending = {entry["path"] for entry in manifest if entry["kind"] == "reader_pending_migration_9662"}
    assert pending == PENDING
    present = {entry["path"] for entry in manifest}
    for rel in MIGRATED:
        assert rel not in present
        assert classify_source((ROOT / rel).read_text(), rel) == []


def test_preload_keeps_stdlib_sqlite_off_the_named_loader(monkeypatch):
    from scripts.api import preload

    monkeypatch.setattr(preload, "PRELOAD_MODULES", ["sqlite3", "json"])
    monkeypatch.setattr(preload, "OPTIONAL_MODULES", [])
    monkeypatch.setattr(preload, "DYNAMIC_LOADERS", {})
    preload.preload_all()

    monkeypatch.setattr(preload, "PRELOAD_MODULES", ["sqlite3.dbapi2"])
    with pytest.raises(RuntimeError, match=r"sqlite3\.dbapi2"):
        preload.preload_all()


def test_loader_modules_bind_the_named_module_boundary():
    from scripts.agent_runtime import lane_probe, runner
    from scripts.api import preload, runtime_router
    from scripts.lib.readonly_sqlite import import_named_module

    assert lane_probe.import_named_module is import_named_module
    assert runner.import_named_module is import_named_module
    assert preload.import_named_module is import_named_module
    assert runtime_router.import_named_module is import_named_module
    with pytest.raises(ImportError):
        runner.import_named_module("sqlite3")


def test_monitor_read_only_open_keeps_special_path(tmp_path):
    from scripts.api.monitor_context import MonitorContext

    db = _write_db(_special(tmp_path), "CREATE TABLE evidence (value TEXT); INSERT INTO evidence VALUES ('kept');")
    ctx = MonitorContext.__new__(MonitorContext)
    object.__setattr__(ctx, "root", None)
    connection = ctx._open_db(db, read_only=True)
    try:
        _assert_exact_readonly(connection, db)
        assert connection.execute("SELECT value FROM evidence").fetchone()[0] == "kept"
    finally:
        connection.close()


def test_lexical_helpers_read_special_paths(tmp_path):
    from scripts.atlas.lexical_projection import export_projection, load_vesum_forms

    vesum = _write_db(
        tmp_path / "forms?#.db",
        "CREATE TABLE forms (word_form TEXT); INSERT INTO forms VALUES ('мова');",
    )
    assert load_vesum_forms(vesum) == frozenset({"мова"})

    projection = _write_db(
        tmp_path / "projection?#.db",
        """
        CREATE TABLE sources (record_json TEXT);
        CREATE TABLE lemma_entries (record_json TEXT);
        CREATE TABLE senses (record_json TEXT);
        CREATE TABLE attestations (record_json TEXT);
        CREATE TABLE practice_decks (record_json TEXT);
        CREATE TABLE practice_deck_items (record_json TEXT);
        """,
    )
    output = tmp_path / "out.jsonl"
    export_projection(projection, output)
    assert output.read_text(encoding="utf-8") == ""


def test_practice_deck_readers_keep_special_path(tmp_path):
    from scripts.audit.generate_practice_deck import RealVesumVerifier, SqliteSourcePassages, _imperative_connection

    sources = _write_db(
        _special(tmp_path),
        "CREATE TABLE textbooks (chunk_id TEXT, text TEXT); INSERT INTO textbooks VALUES ('c1', 'текст');",
    )
    assert SqliteSourcePassages(sources).chunk_text("c1") == "текст"
    connection = _imperative_connection(RealVesumVerifier(sources))
    try:
        _assert_exact_readonly(connection, sources)
    finally:
        connection.close()


def test_atlas_and_codex_readers_keep_special_path(tmp_path):
    from scripts.benchmarks.generate_synthetic_atlas import _open_readonly as atlas_open
    from scripts.hygiene.codex_rollout_reconcile import _db_uri
    from scripts.hygiene.codex_rollout_reconcile import _open_readonly as codex_open

    db = _write_db(_special(tmp_path), "CREATE TABLE evidence (value TEXT);")
    uri = _db_uri(db)
    assert "%3F" in uri and "%23" in uri and uri.endswith("?mode=ro")
    for opener in (atlas_open, codex_open):
        connection = opener(db)
        try:
            _assert_exact_readonly(connection, db)
        finally:
            connection.close()


def test_control_plane_and_context_store_read_special_path(tmp_path, monkeypatch):
    from scripts.control_plane.storage import StoreId, connect
    from scripts.entire_context.store import ContextLinkStore

    db = _write_db(_special(tmp_path), "CREATE TABLE evidence (value TEXT);")
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY", "sqlite")
    connection = connect(StoreId.FLEET_COMMS, path=db, read_only=True)
    try:
        _assert_exact_readonly(connection, db)
    finally:
        connection.close()
    with ContextLinkStore(db)._connect(write=False) as connection:
        _assert_exact_readonly(connection, db)


def test_retrieval_readers_keep_special_path(tmp_path):
    from scripts.wiki.diagnostics.retrieval_probe_9233 import _lemma_search, _ro_connect

    sources = _write_db(_special(tmp_path), "CREATE TABLE textbooks (id INTEGER, text TEXT);")
    connection = _ro_connect(sources)
    try:
        _assert_exact_readonly(connection, sources)
    finally:
        connection.close()

    index = _write_db(
        tmp_path / "index?#.db",
        """
        CREATE VIRTUAL TABLE lemma_fts USING fts5(
            chunk_id UNINDEXED, source_file UNINDEXED, subject UNINDEXED,
            title_terms, text_terms, tokenize='unicode61'
        );
        INSERT INTO lemma_fts(chunk_id, source_file, subject, title_terms, text_terms)
        VALUES ('chunk-1', 'book', 'grammar', '', 'мова');
        """,
    )
    vesum = sqlite3.connect(":memory:")
    vesum.execute("CREATE TABLE forms_all (id INTEGER, word_form TEXT, lemma TEXT)")
    vesum.execute("CREATE TABLE form_markers (form_id INTEGER, marker TEXT)")
    try:
        assert _lemma_search(index, "мова", vesum, 5) == ["chunk-1"]
    finally:
        vesum.close()


def test_vesum_fixture_manifest_queries_special_path(tmp_path):
    from scripts.rag.vesum_reingest import VesumReingestError, generate_fixture_manifest

    db = _write_db(
        _special(tmp_path),
        """
        CREATE TABLE forms_all (
            id INTEGER, word_form TEXT, lemma TEXT, tags TEXT, entry_id INTEGER
        );
        CREATE TABLE form_markers (form_id INTEGER, marker TEXT);
        """,
    )
    with pytest.raises(VesumReingestError, match="clean"):
        generate_fixture_manifest(
            db,
            {"release_asset": {"version": "v", "url": "u", "sha256": "s"}},
            tmp_path / "manifest.json",
        )


def test_measure_default_opener_reads_special_path(tmp_path, monkeypatch):
    from scripts.atlas import measure_fill_enrich_divergence as measure
    from scripts.lexicon import enrich_manifest as em

    db = _write_db(_special(tmp_path), "CREATE TABLE evidence (value TEXT);")
    seen: list[str] = []

    def remember(connection: sqlite3.Connection, *_args, **_kwargs):
        seen.append(connection.execute("PRAGMA database_list").fetchone()[2])
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("CREATE TABLE forbidden (value TEXT)")
        return None

    empty = {kind: {} for kind in measure.RELATION_KINDS}
    monkeypatch.setattr(em, "_cefr", remember)
    monkeypatch.setattr(em, "_prepare_cefr_estimates", remember)
    monkeypatch.setattr(measure, "fill_local_style_relations", lambda connection, _entries: remember(connection) or empty)
    monkeypatch.setattr(measure, "enrich_style_relations", lambda connection, _manifest: remember(connection) or empty)
    result = measure.measure_divergence([{"lemma": "мова"}], db, {})
    assert result["lemmas"] == ["мова"]
    assert seen == [str(db.resolve())] * 5
