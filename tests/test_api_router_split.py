"""
Tests for the Blue/Gold API router split.

Validates:
  1. All Blue endpoints return 200
  2. All Gold endpoints return 200
  3. All shared endpoints return 200
  4. Old Blue paths at /api/batch/ are gone (404)
  5. Dashboard HTML calls the correct API paths
  6. No stale /api/batch/ paths for Blue-specific endpoints in dashboard
  7. Every apiFetch() call in dashboard has a corresponding server endpoint
"""

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scripts.api.main import app

client = TestClient(app)

DASHBOARD_PATH = Path(__file__).resolve().parent.parent / "playgrounds" / "v2-blue" / "batch-monitor.html"


# ==================== Endpoint existence ====================

class TestBlueEndpoints:
    """Blue team endpoints at /api/blue/..."""

    @pytest.mark.parametrize("path", [
        "/api/blue/health",
        "/api/blue/metrics",
        "/api/blue/history",
        "/api/blue/live-status",
        "/api/blue/freshness",
    ])
    def test_blue_endpoint_returns_200(self, path):
        r = client.get(path)
        assert r.status_code == 200, f"{path} returned {r.status_code}: {r.text[:200]}"

    def test_health_has_status_ok(self):
        r = client.get("/api/blue/health")
        data = r.json()
        assert data["status"] == "ok"

    def test_live_status_returns_tracks(self):
        r = client.get("/api/blue/live-status")
        data = r.json()
        assert isinstance(data, dict)
        # Should have at least some tracks
        assert len(data) > 0, "live-status returned empty dict"
        # Each track should have module_count and states
        for track, info in data.items():
            assert "module_count" in info, f"Track {track} missing module_count"
            assert "states" in info, f"Track {track} missing states"
            assert "modules" in info, f"Track {track} missing modules"


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
    ])
    def test_old_blue_path_returns_404(self, path):
        r = client.get(path)
        assert r.status_code == 404, (
            f"{path} should be 404 (moved to /api/blue/) but returned {r.status_code}"
        )


# ==================== Dashboard integration ====================

class TestDashboardApiPaths:
    """Verify the dashboard HTML calls the correct API paths."""

    @pytest.fixture(autouse=True)
    def load_dashboard(self):
        assert DASHBOARD_PATH.exists(), f"Dashboard not found: {DASHBOARD_PATH}"
        self.html = DASHBOARD_PATH.read_text()
        # Extract all apiFetch('/path') calls
        self.api_calls = re.findall(r"apiFetch\(['\"]([^'\"]+)['\"]", self.html)

    def test_no_stale_blue_paths(self):
        """Dashboard must not call old /api/batch/ paths for Blue-specific endpoints."""
        blue_specific = {"health", "metrics", "history", "live-status", "freshness", "resolved-failures"}
        stale = []
        for call in self.api_calls:
            if call.startswith("/api/batch/"):
                suffix = call.replace("/api/batch/", "").split("?")[0]
                if suffix in blue_specific:
                    stale.append(call)
        assert stale == [], f"Dashboard still calls old Blue paths: {stale}"

    def test_blue_calls_use_blue_prefix(self):
        """Blue-specific calls must use /api/blue/ prefix."""
        blue_calls = [c for c in self.api_calls if c.startswith("/api/blue/")]
        assert len(blue_calls) >= 5, (
            f"Expected at least 5 /api/blue/ calls, found {len(blue_calls)}: {blue_calls}"
        )

    def test_every_api_call_has_server_endpoint(self):
        """Every apiFetch() path in the dashboard should resolve to a real endpoint."""
        # These are POST-only or have params, skip them
        known_post_only = {
            "/api/batch/dispatcher/start",
            "/api/batch/dispatcher/stop",
            "/api/batch/dispatcher/scan",
            "/api/batch/cleanup",
        }
        missing = []
        for path in set(self.api_calls):
            if path in known_post_only:
                continue
            r = client.get(path)
            if r.status_code == 404:
                missing.append(path)
        assert missing == [], f"Dashboard calls endpoints that return 404: {missing}"

    def test_shared_calls_still_at_batch(self):
        """Shared endpoints (dispatcher, checkpoints, etc.) must stay at /api/batch/."""
        shared_calls = [c for c in self.api_calls if c.startswith("/api/batch/")]
        # Should have at least dispatcher, checkpoints, failures, usage
        shared_suffixes = {c.replace("/api/batch/", "").split("/")[0] for c in shared_calls}
        for expected in ["dispatcher", "checkpoints", "failures", "usage"]:
            assert expected in shared_suffixes, (
                f"Expected /api/batch/{expected} call in dashboard, found: {shared_suffixes}"
            )

    def test_no_loadResolvedFailures_call(self):
        """loadResolvedFailures() should not make an API call (endpoint removed)."""
        # The function definition might still exist but should not call apiFetch
        resolved_calls = [c for c in self.api_calls if "resolved" in c]
        assert resolved_calls == [], (
            f"Dashboard still calls resolved-failures endpoint: {resolved_calls}"
        )


# ==================== Static file serving ====================

class TestStaticServing:
    """Dashboard HTML should be servable."""

    def test_dashboard_is_served(self):
        r = client.get("/v2-blue/batch-monitor.html")
        assert r.status_code == 200
        assert "Blue Team" in r.text

    def test_index_page_is_served(self):
        r = client.get("/")
        # Might be 200 or 404 depending on whether index.html exists
        assert r.status_code in (200, 404)
