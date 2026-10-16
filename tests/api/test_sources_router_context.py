"""#7269 step 10: sources routes read MonitorContext, not module globals.

Listed in scripts/ci/fastlane_always_tests.txt (repo_invariant).
"""

from __future__ import annotations

import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api.monitor_context import DatabaseHandle, fixture_context
from scripts.api.sources_router import router
from scripts.wiki.sources_db import _get_conn, using_connection

pytestmark = pytest.mark.repo_invariant


def _client_for(root: Path) -> TestClient:
    app = FastAPI()
    app.state.ctx = fixture_context(root)
    app.include_router(router, prefix="/api/sources")
    return TestClient(app)


def _seed_sources_db(path: Path, *, rows: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE textbooks (id INTEGER PRIMARY KEY, text TEXT)")
    connection.executemany("INSERT INTO textbooks (text) VALUES (?)", [("chunk",)] * rows)
    connection.commit()
    connection.close()


def test_using_connection_overrides_module_global(tmp_path: Path) -> None:
    first = sqlite3.connect(":memory:")
    second = sqlite3.connect(":memory:")
    first.execute("CREATE TABLE textbooks (id INTEGER PRIMARY KEY)")
    first.execute("INSERT INTO textbooks DEFAULT VALUES")
    try:
        with using_connection(first):
            assert _get_conn() is first
            assert _get_conn().execute("SELECT COUNT(*) FROM textbooks").fetchone()[0] == 1
        with using_connection(second):
            assert _get_conn() is second
    finally:
        first.close()
        second.close()


def test_browse_images_does_not_see_sibling_context_files(tmp_path: Path) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_grade = first_root / "data" / "textbook_images" / "grade-04"
    second_grade = second_root / "data" / "textbook_images" / "grade-04"
    first_grade.mkdir(parents=True)
    second_grade.mkdir(parents=True)
    (first_grade / "only-first.png").write_bytes(b"\x89PNG" + b"\x00" * 4)
    (second_grade / "only-second.png").write_bytes(b"\x89PNG" + b"\x00" * 4)

    first_client = _client_for(first_root)
    payload = first_client.get("/api/sources/browse_images").json()
    names = {image["name"] for image in payload["images"]}
    assert names == {"only-first.png"}
    assert "only-second.png" not in names


def test_stats_reads_context_sources_handle(tmp_path: Path) -> None:
    root = tmp_path / "isolated"
    ctx = fixture_context(root)
    _seed_sources_db(ctx.roots.sources_db_path, rows=4)

    app = FastAPI()
    app.state.ctx = ctx
    app.include_router(router, prefix="/api/sources")
    client = TestClient(app)

    payload = client.get("/api/sources/stats").json()
    assert payload["sources_db"]["status"] == "ok"
    assert payload["sources_db"]["points_count"] == 4
    assert payload["sources_db"]["tables"]["textbooks"] == 4


def test_search_routes_report_unknown_when_corpus_missing(tmp_path: Path) -> None:
    client = _client_for(tmp_path / "empty")
    for route in ("search_text", "search_literary"):
        response = client.get(f"/api/sources/{route}", params={"q": "мова"})
        assert response.status_code == 503
        assert response.json() == {"detail": {"status": "unknown", "reason": "sources_unavailable"}}
    assert not client.app.state.ctx.roots.sources_db_path.exists()
    assert client.get("/api/sources/search_images", params={"q": "мова"}).status_code == 404
    assert client.get("/api/rag/search_text", params={"q": "мова"}).status_code == 404


def _seed_search_corpus(path: Path, *, populated: bool = True, marker: str = "first") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript("""
            CREATE TABLE textbooks (
                id INTEGER PRIMARY KEY, title TEXT, text TEXT, source_file TEXT,
                grade INTEGER, subject TEXT, trust_tier INTEGER
            );
            CREATE VIRTUAL TABLE textbooks_fts USING fts5(title, text, content='textbooks');
            CREATE TABLE literary_texts (
                id INTEGER PRIMARY KEY, title TEXT, text TEXT, work TEXT,
                genre TEXT, language_period TEXT
            );
            CREATE VIRTUAL TABLE literary_fts USING fts5(title, text, content='literary_texts');
        """)
        if populated:
            text = f"The {marker} corpus contains a searchable needle in this passage. " * 8
            conn.executemany(
                "INSERT INTO textbooks VALUES (?, ?, ?, ?, ?, ?, ?)",
                [(1, "Alpha", text, "alpha.pdf", 4, "ukrmova", 1),
                 (2, "Beta", text, "beta.pdf", 5, "matematyka", 2),
                 (3, "Gamma", text, "gamma.pdf", 4, "ukrmova", 1)],
            )
            conn.executemany(
                "INSERT INTO literary_texts VALUES (?, ?, ?, ?, ?, ?)",
                [(1, "Alpha", text, "Alpha", "poetry", "modern"),
                 (2, "Beta", text, "Beta", "prose", "historical"),
                 (3, "Gamma", text, "Gamma", "poetry", "modern")],
            )
        for table, fts in (("textbooks", "textbooks_fts"), ("literary_texts", "literary_fts")):
            conn.execute(f"INSERT INTO {fts}(rowid, title, text) SELECT id, title, text FROM {table}")


@pytest.mark.parametrize("route", ["search_text", "search_literary"])
def test_unconfigured_source_handle_is_unknown(tmp_path, route):
    client = _client_for(tmp_path)
    ctx = client.app.state.ctx
    _seed_search_corpus(ctx.roots.sources_db_path)
    client.app.state.ctx = replace(ctx, stores=replace(ctx.stores, sources_db=None))
    response = client.get(f"/api/sources/{route}", params={"q": "needle"})
    assert response.status_code == 503
    assert response.json() == {"detail": {"status": "unknown", "reason": "sources_unavailable"}}


@pytest.mark.parametrize("route", ["search_text", "search_literary"])
@pytest.mark.parametrize("populated", [False, True])
def test_real_search_empty_and_no_match_are_success(tmp_path, route, populated):
    client = _client_for(tmp_path)
    _seed_search_corpus(client.app.state.ctx.roots.sources_db_path, populated=populated)
    for query in ("absentword", "" if populated else "needle"):
        response = client.get(f"/api/sources/{route}", params={"q": query})
        assert response.status_code == 200
        assert response.json() == []


@pytest.mark.parametrize(
    ("route", "filters", "filtered_ids"),
    [("search_text", {"grade": 4, "subject": "ukrmova", "trust_tier": 1}, ["1", "3"]),
     ("search_literary", {"genre": "poetry", "period": "modern"}, ["1", "3"])],
)
def test_real_search_hits_filters_limits_and_context_isolation(tmp_path, route, filters, filtered_ids):
    first = _client_for(tmp_path / "first?#")
    second = _client_for(tmp_path / "second")
    for client, marker in ((first, "first"), (second, "second")):
        _seed_search_corpus(client.app.state.ctx.roots.sources_db_path, marker=marker)
        response = client.get(f"/api/sources/{route}", params={"q": "needle"})
        assert response.status_code == 200
        assert [hit["chunk_id"] for hit in response.json()] == ["1", "2", "3"]
        assert all(f"The {marker} corpus" in hit["text"] for hit in response.json())
        filtered = client.get(f"/api/sources/{route}", params={"q": "needle", **filters})
        assert filtered.status_code == 200
        assert [hit["chunk_id"] for hit in filtered.json()] == filtered_ids
        limited = client.get(f"/api/sources/{route}", params={"q": "needle", **filters, "limit": 1})
        assert [hit["chunk_id"] for hit in limited.json()] == ["1"]
        misses = {**filters, "grade" if route == "search_text" else "work": 11 if route == "search_text" else "absent"}
        no_match = client.get(f"/api/sources/{route}", params={"q": "needle", **misses})
        assert no_match.status_code == 200
        assert no_match.json() == []
        assert client.get(f"/api/sources/{route}", params={"q": "needle", "limit": 21}).status_code == 422


@pytest.mark.parametrize("route", ["search_text", "search_literary"])
def test_disappearance_after_exists_does_not_create_corpus(tmp_path, route):
    client = _client_for(tmp_path / "corpus?#")
    ctx = client.app.state.ctx
    handle = ctx.stores.sources_db
    _seed_search_corpus(handle.path)
    attempts = []

    def disappearing_open(path, *, read_only=False):
        attempts.append(read_only)
        assert path.exists()
        path.unlink()
        return handle.connect(read_only=read_only)

    client.app.state.ctx = replace(
        ctx, stores=replace(ctx.stores, sources_db=DatabaseHandle(handle.path, disappearing_open))
    )
    response = client.get(f"/api/sources/{route}", params={"q": "needle"})
    assert attempts == [True]
    assert response.status_code == 503
    assert response.json() == {"detail": {"status": "unknown", "reason": "sources_unavailable"}}
    assert not handle.path.exists()


@pytest.mark.parametrize("route", ["search_text", "search_literary"])
@pytest.mark.parametrize("phase", ["open", "read"])
@pytest.mark.parametrize("error", [PermissionError, sqlite3.OperationalError, sqlite3.DatabaseError])
def test_expected_source_faults_are_sanitized(tmp_path, route, phase, error):
    client = _client_for(tmp_path)
    ctx = client.app.state.ctx
    path = ctx.roots.sources_db_path
    _seed_search_corpus(path)
    closed = []

    class ReadFault(sqlite3.Connection):
        def execute(self, *args, **kwargs):
            raise error("private content /private/location credential")

        def close(self):
            closed.append(True)
            super().close()

    def open_source(path, *, read_only=False):
        assert read_only is True
        if phase == "open":
            raise error("private content /private/location credential")
        return sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, factory=ReadFault)

    client.app.state.ctx = replace(
        ctx, stores=replace(ctx.stores, sources_db=DatabaseHandle(path, open_source))
    )
    response = client.get(f"/api/sources/{route}", params={"q": "needle"})
    assert response.status_code == 503
    assert response.json() == {"detail": {"status": "unknown", "reason": "sources_unavailable"}}
    assert closed == ([True] if phase == "read" else [])


@pytest.mark.parametrize("route", ["search_text", "search_literary"])
@pytest.mark.parametrize("query", ["needle", "", "x"])
def test_corrupt_source_corpus_is_unknown(tmp_path, route, query):
    client = _client_for(tmp_path)
    path = client.app.state.ctx.roots.sources_db_path
    path.parent.mkdir(parents=True)
    path.write_bytes(b"not a SQLite database: private content")
    response = client.get(f"/api/sources/{route}", params={"q": query})
    assert response.status_code == 503
    assert response.json() == {"detail": {"status": "unknown", "reason": "sources_unavailable"}}


@pytest.mark.parametrize("route", ["search_text", "search_literary"])
@pytest.mark.parametrize("phase", ["open", "read"])
@pytest.mark.parametrize("error", [RuntimeError, TypeError, sqlite3.ProgrammingError])
def test_programming_defects_propagate(tmp_path, route, phase, error):
    client = _client_for(tmp_path)
    ctx = client.app.state.ctx
    _seed_search_corpus(ctx.roots.sources_db_path)

    class BrokenRead(sqlite3.Connection):
        def execute(self, *args, **kwargs):
            raise error("programming defect")

    def broken_open(path, *, read_only=False):
        if phase == "open":
            raise error("programming defect")
        return sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, factory=BrokenRead)

    client.app.state.ctx = replace(
        ctx, stores=replace(ctx.stores, sources_db=DatabaseHandle(ctx.roots.sources_db_path, broken_open))
    )
    with pytest.raises(error, match="programming defect"):
        client.get(f"/api/sources/{route}", params={"q": "needle"})
