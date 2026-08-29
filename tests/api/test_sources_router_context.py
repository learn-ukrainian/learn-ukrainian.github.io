"""#7269 step 10: sources/RAG routes read MonitorContext, not module globals.

Listed in scripts/ci/fastlane_always_tests.txt (repo_invariant).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api.monitor_context import fixture_context
from scripts.api.rag_router import router
from scripts.wiki.sources_db import _get_conn, using_connection

pytestmark = pytest.mark.repo_invariant


def _client_for(root: Path) -> TestClient:
    app = FastAPI()
    app.state.ctx = fixture_context(root)
    app.include_router(router, prefix="/api/sources")
    app.include_router(router, prefix="/api/rag")
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


def test_search_routes_return_empty_when_corpus_missing(tmp_path: Path) -> None:
    client = _client_for(tmp_path / "empty")
    assert client.get("/api/sources/search_text", params={"q": "мова"}).json() == []
    assert client.get("/api/sources/search_literary", params={"q": "мова"}).json() == []
    assert client.get("/api/sources/search_images", params={"q": "мова"}).json() == []
    assert client.get("/api/rag/search_text", params={"q": "мова"}).json() == []
