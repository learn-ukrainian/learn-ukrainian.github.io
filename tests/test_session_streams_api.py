"""PR-K Monitor surfaces for session streams (read-only)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api.session_streams_router import router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api/session-streams")
    return TestClient(app)


def test_session_streams_health_and_dual_write() -> None:
    client = _client()
    h = client.get("/api/session-streams/v1/health")
    assert h.status_code == 200
    body = h.json()
    assert body["ok"] is True
    assert "db_exists" in body

    d = client.get("/api/session-streams/v1/dual-write-status")
    assert d.status_code == 200
    dual = d.json()
    assert "candidates" in dual
    assert dual["total"] >= 0

    c = client.get("/api/session-streams/v1/plane-continuity")
    assert c.status_code == 200
    assert c.json()["cutover"] == "operator-gated"


def test_session_stream_status_and_digest_for_harness() -> None:
    client = _client()
    s = client.get("/api/session-streams/v1/status/epic:4707")
    assert s.status_code in {200, 404}
    if s.status_code == 200:
        assert s.json()["stream_id"] == "epic:4707"

    dig = client.get("/api/session-streams/v1/digest/epic:4707", params={"limit": 5})
    assert dig.status_code in {200, 404}
    if dig.status_code == 200:
        assert dig.json()["limit"] == 5
        assert "pinned" in dig.json()
        assert "recent" in dig.json()


def test_session_stream_status_rejects_bad_id() -> None:
    client = _client()
    r = client.get("/api/session-streams/v1/status/not-an-epic")
    assert r.status_code == 400


def test_session_streams_repo_root_uses_live_primary_under_release(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """PR-K residual: release code root must not own .agent/session-streams."""
    from scripts.api import session_streams_router as ssr

    live = tmp_path / "live"
    live.mkdir()
    db_dir = live / ".agent" / "session-streams" / "v1"
    db_dir.mkdir(parents=True)
    db = db_dir / "session-streams.sqlite3"
    db.write_bytes(b"")

    # Synthetic release path shape: .runtime/api/releases/<40-hex>
    release = (
        tmp_path
        / ".runtime"
        / "api"
        / "releases"
        / ("a" * 40)
    )
    release.mkdir(parents=True)

    monkeypatch.setattr(ssr, "PROJECT_ROOT", release)
    monkeypatch.setattr(ssr, "LIVE_REPO_ROOT", live)

    assert ssr._repo_root() == live
    assert ssr._db_path() == db
    health = ssr.session_streams_health()
    assert health["db_exists"] is True
    assert health["repo_root"] == str(live)
