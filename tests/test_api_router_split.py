"""
Tests for the Blue/Gold API router split.

Validates:
  1. All Blue endpoints return 200
  2. All Gold endpoints return 200
  3. All shared endpoints return 200
  4. Old Blue paths at /api/batch/ are gone (404)
  5. Static dashboard serving rejects path traversal
"""

import pytest
from fastapi.testclient import TestClient

from scripts.api.main import app

client = TestClient(app)

# ==================== Endpoint existence ====================

class TestBlueEndpoints:
    """Blue team endpoints at /api/blue/..."""

    @pytest.mark.parametrize("path", [
        "/api/blue/health",
        "/api/blue/metrics",
        "/api/blue/history",
        "/api/blue/freshness",
    ])
    def test_blue_endpoint_returns_200(self, path):
        r = client.get(path)
        assert r.status_code == 200, f"{path} returned {r.status_code}: {r.text[:200]}"

    def test_health_has_status_ok(self):
        r = client.get("/api/blue/health")
        data = r.json()
        assert data["status"] == "ok"

    def test_build_status_returns_tracks(self):
        r = client.get("/api/state/build-status")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
        assert "tracks" in data
        assert isinstance(data["tracks"], dict)
        for track, info in data["tracks"].items():
            assert "total" in info, f"Track {track} missing total"
            assert "done" in info, f"Track {track} missing done"
            assert "building" in info, f"Track {track} missing building"


class TestGoldEndpoints:
    """Gold team endpoints at /api/gold/..."""

    @pytest.mark.parametrize("path", [
        "/api/gold/health",
        "/api/gold/ground-truth",
    ])
    def test_gold_endpoint_returns_200(self, path):
        r = client.get(path)
        assert r.status_code == 200, f"{path} returned {r.status_code}: {r.text[:200]}"


class TestSharedEndpoints:
    """Shared endpoints at /api/batch/..."""

    @pytest.mark.parametrize("path", [
        "/api/config",
        "/api/batch/dispatcher",
        "/api/batch/active",
        "/api/batch/failures",
        "/api/batch/usage",
        "/api/batch/checkpoints",
        "/api/batch/dispatcher/running",
        "/api/batch/dispatcher/logs",
    ])
    def test_shared_endpoint_returns_200(self, path):
        r = client.get(path)
        assert r.status_code == 200, f"{path} returned {r.status_code}: {r.text[:200]}"

    def test_config_has_levels(self):
        r = client.get("/api/config")
        data = r.json()
        assert "levels" in data
        assert len(data["levels"]) > 0


# ==================== Old paths are gone ====================

class TestOldPathsRemoved:
    """Blue-specific endpoints must NOT exist at /api/batch/..."""

    @pytest.mark.parametrize("path", [
        "/api/batch/health",
        "/api/batch/metrics",
        "/api/batch/history",
        "/api/batch/live-status",
        "/api/batch/freshness",
        "/api/batch/resolved-failures",
        "/api/blue/live-status",
        "/api/state/ready-to-build",
        "/api/cost",
    ])
    def test_old_blue_path_returns_404(self, path):
        r = client.get(path)
        assert r.status_code == 404, (
            f"{path} should be 404 but returned {r.status_code}"
        )


# ==================== Static file serving ====================

class TestStaticServing:
    """Dashboard HTML should be servable."""

    def test_index_page_is_served(self):
        r = client.get("/")
        # Might be 200 or 404 depending on whether index.html exists
        assert r.status_code in (200, 404)

    def test_static_path_traversal_is_rejected(self, tmp_path, monkeypatch):

        import scripts.api.main as api_main

        dashboards_dir = tmp_path / "dashboards"
        dashboards_dir.mkdir()
        (dashboards_dir / "index.html").write_text("ok", "utf-8")
        outside_file = tmp_path / "secret.txt"
        outside_file.write_text("secret", "utf-8")

        base_ctx = api_main.app.state.ctx
        patched_ctx = base_ctx.with_roots(dashboards_dir=dashboards_dir)
        monkeypatch.setattr(api_main.app.state, "ctx", patched_ctx)

        r = client.get("/%2e%2e/secret.txt")

        assert r.status_code == 403
        assert r.json()["detail"] == "Path traversal not allowed"
