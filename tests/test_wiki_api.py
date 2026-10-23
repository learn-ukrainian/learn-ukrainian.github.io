"""Tests for wiki monitor API endpoints."""

import sqlite3

import pytest
from fastapi.testclient import TestClient

import scripts.api.wiki_router as wiki_router
from scripts.api.main import app
from scripts.api.monitor_context import fixture_context
from scripts.api.opsec_sanitize import REDACTED_ABSOLUTE_PATH

pytestmark = pytest.mark.reads_content

client = TestClient(app, raise_server_exceptions=False)


def test_article_endpoint_returns_preview_and_word_count(tmp_path, monkeypatch):
    wiki_dir = tmp_path / "wiki"
    article_dir = wiki_dir / "periods"
    article_dir.mkdir(parents=True)
    article_path = article_dir / "kyivan-rus.md"
    article_path.write_text("# Kyivan Rus\n\nKyiv was a major political center.\n", encoding="utf-8")

    monkeypatch.setattr(wiki_router, "_known_tracks", lambda *_a, **_k: ["hist"])
    monkeypatch.setattr("wiki.config.WIKI_DIR", wiki_dir)
    monkeypatch.setattr("wiki.sources.list_discovery_slugs_readonly", lambda track: ["kyivan-rus"] if track == "hist" else [])
    monkeypatch.setattr(
        "wiki.state.list_wiki_articles",
        lambda: [{"path": "periods/kyivan-rus.md"}],
    )
    monkeypatch.setattr(
        "wiki.state.load_progress",
        lambda: {
            "articles": {
                "periods/kyivan-rus": {
                    "status": "compiled",
                    "compiled_at": "2026-04-10T18:45:00+00:00",
                    "source_count": 4,
                }
            }
        },
    )
    monkeypatch.setattr(
        "wiki.sources.gather_discovery_sources_readonly",
        lambda track, slug: {
            "literary_chunks": [],
            "textbook_chunks": [{"chunk_id": "text-1"}],
            "literary_files": [],
        },
    )

    response = client.get("/api/wiki/article/hist/kyivan-rus")

    assert response.status_code == 200
    data = response.json()
    assert data["track"] == "hist"
    assert data["slug"] == "kyivan-rus"
    assert data["compiled"] is True
    assert data["path"] == REDACTED_ABSOLUTE_PATH
    assert data["word_count"] == 9
    assert data["preview"] == article_path.read_text(encoding="utf-8")[:500]
    assert data["source_count"] == 4
    assert data["compiled_at"] == "2026-04-10T18:45:00+00:00"


def test_sources_endpoint_handles_missing_table(tmp_path, monkeypatch):
    db_path = tmp_path / "sources.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE textbooks (id INTEGER PRIMARY KEY)")
    conn.executemany("INSERT INTO textbooks DEFAULT VALUES", [(), (), ()])
    conn.commit()
    conn.close()

    ctx = fixture_context(tmp_path)
    sources_path = ctx.roots.sources_db_path
    sources_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.replace(sources_path)
    monkeypatch.setattr(app.state, "ctx", ctx)

    response = client.get("/api/wiki/sources")

    assert response.status_code == 200
    assert response.json() == {
        "tables": [{"name": "textbooks", "row_count": 3}],
        "total_entries": 3,
    }


def test_status_read_only_does_not_generate_discovery_files(tmp_path, monkeypatch):
    curriculum_dir = tmp_path / "curriculum"
    plans_dir = curriculum_dir / "plans" / "hist"
    plans_dir.mkdir(parents=True)
    (plans_dir / "plan-only.yaml").write_text("title: Plan Only\n", encoding="utf-8")

    monkeypatch.setattr(wiki_router, "_known_tracks", lambda *_a, **_k: ["hist"])
    monkeypatch.setattr("wiki.sources.CURRICULUM_DIR", curriculum_dir)
    monkeypatch.setattr("wiki.state.get_status_summary", lambda: {})
    monkeypatch.setattr("wiki.state.list_wiki_articles", lambda: [])
    monkeypatch.setattr("wiki.state.load_progress", lambda: {"articles": {}})

    response = client.get("/api/wiki/status/hist")

    assert response.status_code == 200
    assert response.json()[0]["slug"] == "plan-only"
    assert not (curriculum_dir / "hist" / "discovery").exists()
