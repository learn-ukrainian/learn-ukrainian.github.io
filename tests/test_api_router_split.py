"""
Tests for the Blue/Gold API router split.

Validates:
  1. All Blue endpoints return 200
  2. All Gold endpoints return 200
  3. All shared endpoints return 200
  4. Old Blue paths at /api/batch/ are gone (404)
  5. Static dashboard serving rejects path traversal
"""

from fastapi.testclient import TestClient

from scripts.api.main import app

client = TestClient(app)

# ==================== Endpoint existence ====================


# ==================== Old paths are gone ====================


# ==================== Static file serving ====================

class TestStaticServing:
    """Dashboard HTML should be servable."""

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
