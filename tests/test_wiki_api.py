"""Tests for wiki monitor API endpoints."""

import sqlite3

from fastapi.testclient import TestClient

import scripts.api.wiki_router as wiki_router
from scripts.api.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_status_returns_track_summary(tmp_path, monkeypatch):
    wiki_dir = tmp_path / "wiki"
    article_dir = wiki_dir / "periods"
    article_dir.mkdir(parents=True)
    (article_dir / "kyivan-rus.md").write_text("# Kyivan Rus\n\nOne two three four\n", encoding="utf-8")

    monkeypatch.setattr(wiki_router, "_known_tracks", lambda: ["hist"])
    monkeypatch.setattr("wiki.config.WIKI_DIR", wiki_dir)
    monkeypatch.setattr("wiki.state.get_status_summary", lambda: {"total_compiled": 1, "total_words": 6})
    monkeypatch.setattr("wiki.state.list_wiki_articles", lambda: [{"path": "periods/kyivan-rus.md"}])
    monkeypatch.setattr(
        "wiki.state.load_progress",
        lambda: {
            "articles": {
                "periods/kyivan-rus": {
                    "status": "compiled",
                    "compiled_at": "2026-04-10T18:45:00+00:00",
                    "source_count": 3,
                }
            }
        },
    )
    monkeypatch.setattr("wiki.sources.list_discovery_slugs", lambda track: ["kyivan-rus"] if track == "hist" else [])
    monkeypatch.setattr(
        "wiki.sources.gather_discovery_sources",
        lambda track, slug: {
            "literary_chunks": [{"chunk_id": "lit-1"}],
            "textbook_chunks": [{"chunk_id": "text-1"}],
            "literary_files": [],
        },
    )

    response = client.get("/api/wiki/status")

    assert response.status_code == 200
    data = response.json()
    assert data == {
        "tracks": [
            {
                "track": "hist",
                "total": 1,
                "compiled": 1,
                "pct": 100.0,
                "total_words": 7,
            }
        ]
    }


def test_status_for_unknown_track_returns_404():
    response = client.get("/api/wiki/status/doesnotexist")
    assert response.status_code == 404
    assert response.json()["detail"] == "Track not found: doesnotexist"


def test_article_endpoint_returns_preview_and_word_count(tmp_path, monkeypatch):
    wiki_dir = tmp_path / "wiki"
    article_dir = wiki_dir / "periods"
    article_dir.mkdir(parents=True)
    article_path = article_dir / "kyivan-rus.md"
    article_path.write_text("# Kyivan Rus\n\nKyiv was a major political center.\n", encoding="utf-8")

    monkeypatch.setattr("wiki.config.WIKI_DIR", wiki_dir)
    monkeypatch.setattr("wiki.sources.list_discovery_slugs", lambda track: ["kyivan-rus"] if track == "hist" else [])
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
        "wiki.sources.gather_discovery_sources",
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
    assert data["path"] == str(article_path)
    assert data["word_count"] == 9
    assert data["preview"] == article_path.read_text(encoding="utf-8")[:500]
    assert data["source_count"] == 4
    assert data["compiled_at"] == "2026-04-10T18:45:00+00:00"


def test_quality_gate_aggregates_tracks(monkeypatch):
    monkeypatch.setattr(wiki_router, "_known_tracks", lambda: ["hist", "folk"])

    def fake_scan_track(track):
        if track == "hist":
            return {"periods/kyivan-rus.md": ["SHORT (900w < 1500)"]}
        if track == "folk":
            return {}
        return {"unexpected": ["should not happen"]}

    monkeypatch.setattr("wiki.quality_gate.scan_track", fake_scan_track)

    response = client.get("/api/wiki/quality-gate")

    assert response.status_code == 200
    assert response.json() == {
        "hist": {"periods/kyivan-rus.md": ["SHORT (900w < 1500)"]},
        "folk": {},
    }


def test_build_log_respects_limit_param(monkeypatch):
    monkeypatch.setattr(
        "wiki.state.read_log",
        lambda track=None, last_n=None: [{"idx": idx} for idx in range(100)],
    )

    response = client.get("/api/wiki/build-log?limit=10")

    assert response.status_code == 200
    assert len(response.json()["events"]) == 10


def test_build_log_filters_by_track(monkeypatch):
    seen = {}

    def fake_read_log(track=None, last_n=None):
        seen["track"] = track
        seen["last_n"] = last_n
        return []

    monkeypatch.setattr("wiki.state.read_log", fake_read_log)

    response = client.get("/api/wiki/build-log?track=hist")

    assert response.status_code == 200
    assert seen == {"track": "hist", "last_n": 50}


def test_sources_endpoint_handles_missing_table(tmp_path, monkeypatch):
    db_path = tmp_path / "sources.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE textbooks (id INTEGER PRIMARY KEY)")
    conn.executemany("INSERT INTO textbooks DEFAULT VALUES", [(), (), ()])
    conn.commit()
    conn.close()

    monkeypatch.setattr(wiki_router, "SOURCES_DB_PATH", db_path)

    response = client.get("/api/wiki/sources")

    assert response.status_code == 200
    assert response.json() == {
        "tables": [{"name": "textbooks", "row_count": 3}],
        "total_entries": 3,
    }


def test_sources_per_module_returns_404_when_discovery_missing(monkeypatch):
    monkeypatch.setattr("wiki.sources.list_discovery_slugs", lambda track: ["kyivan-rus"] if track == "hist" else [])

    def fake_gather_discovery_sources(track, slug):
        raise FileNotFoundError("missing discovery")

    monkeypatch.setattr("wiki.sources.gather_discovery_sources", fake_gather_discovery_sources)

    response = client.get("/api/wiki/sources/hist/kyivan-rus")

    assert response.status_code == 404
    assert response.json()["detail"] == "Discovery not found: hist/kyivan-rus"
