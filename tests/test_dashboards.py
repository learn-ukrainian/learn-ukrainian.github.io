"""Tests for dashboard data generation and HTML validation."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import ClassVar

import pytest

ROOT = Path(__file__).resolve().parent.parent
DASHBOARDS_DIR = ROOT / "dashboards"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "generate_mdx"))


# ── Data parsing tests ──────────────────────────────────────────

class TestParseWordCount:
    def setup_method(self):
        from generate_playground_data import parse_word_count
        self.parse = parse_word_count

    def test_standard_format(self):
        count, target = self.parse("3375/3000 (raw: 3539)")
        assert count == 3375
        assert target == 3000


# ── HTML validation tests ───────────────────────────────────────

class TestHtmlValidation:
    """Validate dashboard HTML files have valid structure."""

    HTML_FILES = sorted(DASHBOARDS_DIR.glob("*.html"))

    def test_index_footer_has_no_hardcoded_host(self):
        """index.html must label its own origin dynamically (#8542).

        The footer used to read "Serving from localhost:8765", which is wrong
        whenever the Monitor API is served from anywhere else. It now derives
        the label from ``location.host`` at render time.
        """
        text = (DASHBOARDS_DIR / "index.html").read_text()
        assert "localhost:8765" not in text
        assert "127.0.0.1" not in text
        assert 'id="footer-origin"' in text
        assert "location.host" in text


# ── API endpoint coverage ───────────────────────────────────────

class TestApiEndpoints:
    """Verify dashboard API endpoints are defined in the API server."""

    # All endpoints referenced in dashboard HTML files
    EXPECTED_ENDPOINTS: ClassVar[set[str]] = {
        "/api/agent-monitor/status",
        "/api/artifacts/html",
        "/api/build/events/active",
        "/api/build/events/recent",
        "/api/comms/batch-progress",
        "/api/comms/health",
        "/api/comms/messages",
        "/api/comms/stats",
        "/api/comms/zombies",
        "/api/dashboard/overview",
        "/api/state/build-status",
        "/api/state/enrichment-status",
        "/api/state/issues",
        "/api/state/pipeline-versions",
        "/api/state/research-coverage",
        "/api/state/review-coverage",
        "/api/state/routing-budget",
        "/api/state/summary",
        "/api/state/weak-points",
    }

    @pytest.mark.repo_wide
    def test_endpoints_defined_in_router(self):
        """Check that API endpoints are defined in router files."""
        api_dir = ROOT / "scripts" / "api"
        if not api_dir.exists():
            pytest.skip("API directory not found")

        # Read all router files
        router_text = ""
        for py_file in api_dir.glob("*.py"):
            router_text += py_file.read_text()

        missing = []
        for endpoint in self.EXPECTED_ENDPOINTS:
            # Extract the last path segment (e.g., /api/state/summary → summary)
            segments = endpoint.rstrip("/").split("/")
            last_segment = segments[-1]
            # Also try the router-relative path: /state/summary, /comms/health
            # Routers mount at /state, /comms, /dashboard — routes are relative
            route_relative = "/" + "/".join(segments[3:]) if len(segments) > 3 else "/" + last_segment

            path_variants = [
                endpoint,                    # /api/state/summary
                route_relative,              # /summary or /enrichment-status
                f'"{route_relative}"',       # quoted in decorator
                f'"/{last_segment}"',        # just the last segment quoted
                last_segment.replace("-", "_"),  # function name convention
            ]
            found = any(v in router_text for v in path_variants)
            if not found:
                missing.append(endpoint)

        assert not missing, "API endpoints referenced in dashboards but not found in routers:\n" + "\n".join(missing)

    def test_fetch_calls_in_html(self):
        """Verify all fetch calls reference known endpoints."""
        all_endpoints = set()
        for html_file in DASHBOARDS_DIR.glob("*.html"):
            text = html_file.read_text()
            # Extract fetch URLs, strip query params
            fetches = re.findall(r"fetch\(['\"]([^'\"]+)['\"]", text)
            for url in fetches:
                clean = url.split("?")[0]
                all_endpoints.add(clean)

        # All found endpoints should be in our known set
        unknown = all_endpoints - self.EXPECTED_ENDPOINTS
        assert not unknown, f"Unknown API endpoints in dashboards: {unknown}"


# ── Dashboard inventory ─────────────────────────────────────────

class TestDashboardInventory:
    """Verify expected dashboards exist."""

    EXPECTED_DASHBOARDS: ClassVar[set[str]] = {
        "index.html",
        "progress.html",
        "quality.html",
        "admin.html",
        "comms.html",
        "audit-dashboard.html",
        "curriculum-dashboard.html",
        "track-health.html",
    }


# ── #7024 overview last-good honesty ─────────────────────────────

def _published_summary(*, total: int = 80, published_mdx: int = 55, research_done: int = 40) -> dict:
    return {
        "generated_at": "2026-08-18T16:20:00Z",
        "tracks": {
            "a1": {
                "total": total,
                "generated_md": 0,
                "published_mdx": published_mdx,
                "research_done": research_done,
                "audit_passing": 0,
                "content_done": 0,
                "audit_stale": 0,
                "reviewed": 0,
                "final_review_done": 0,
                "prompt_reviewed": 0,
                "is_seminar": False,
                "module_source": "curriculum.yaml",
            }
        },
    }


class TestOverviewLastGoodHonesty:
    """#7024: cold last-good + published_mdx must not report missing=total."""

    def setup_method(self):
        import scripts.api.dashboard_router as dashboard_router

        dashboard_router.reset_overview_state_for_tests()

    def teardown_method(self):
        import scripts.api.dashboard_router as dashboard_router

        dashboard_router.reset_overview_state_for_tests()

    def _client(self):
        from fastapi.testclient import TestClient

        from scripts.api.main import app

        return TestClient(app, raise_server_exceptions=False)

    def test_cold_process_published_is_not_all_missing(self, monkeypatch, tmp_path):
        import scripts.api.dashboard_router as dashboard_router

        monkeypatch.setenv(
            dashboard_router.DASHBOARD_OVERVIEW_LAST_GOOD_ENV,
            str(tmp_path / "overview_last_good.json"),
        )
        monkeypatch.setattr(
            dashboard_router,
            "_peek_state_summary",
            lambda *_a, **_k: (_published_summary(), "hit", 0.0),
        )
        monkeypatch.setattr(dashboard_router, "_schedule_overview_refresh", lambda *_a, **_k: None)

        before = {
            "pass": 0,
            "missing": 1932,
            "total": 1932,
            "published_mdx": 0,
            "generated_md": 0,
        }
        resp = self._client().get("/api/dashboard/overview")
        assert resp.status_code == 200
        data = resp.json()
        totals = data["totals"]
        assert before["missing"] == before["total"]
        assert totals["pass"] == 0
        assert totals["published_mdx"] == 55
        assert totals["missing"] < totals["total"]
        assert totals["missing"] != totals["total"]
        a1 = next(track for track in data["tracks"] if track["id"] == "a1")
        assert a1["stats"]["missing"] == 80 - 55
        assert a1["stats"]["pass"] == 0
        assert a1["stats"]["research"]["total"] == 40
        assert data["meta"].get("track_scan") == "skipped"
        assert data["meta"].get("refreshing") is True

    def test_bounce_reloads_persisted_last_good(self, monkeypatch, tmp_path):
        import scripts.api.dashboard_router as dashboard_router

        last_good_path = tmp_path / "overview_last_good.json"
        monkeypatch.setenv(
            dashboard_router.DASHBOARD_OVERVIEW_LAST_GOOD_ENV,
            str(last_good_path),
        )
        payload = {
            "tracks": [
                {
                    "id": "a1",
                    "name": "A1",
                    "module_count": 80,
                    "published_mdx": 55,
                    "generated_md": 0,
                    "stats": {
                        "pass": 0,
                        "missing": 80,
                        "content_complete": 0,
                        "fail": 0,
                        "unaudited": 0,
                        "shippable": 0,
                        "research": {"total": 40},
                    },
                }
            ],
            "totals": {
                "pass": 0,
                "missing": 80,
                "total": 80,
                "published_mdx": 0,
                "content_complete": 0,
                "fail": 0,
                "unaudited": 0,
                "shippable": 0,
            },
            "meta": {"track_scan": "hit", "source": "fs:dashboard-summary+state-summary"},
            "timestamp": "2026-08-18T16:21:47Z",
        }
        dashboard_router.persist_overview_last_good(payload)
        dashboard_router.simulate_overview_process_bounce_for_tests()
        monkeypatch.setattr(dashboard_router, "_schedule_overview_refresh", lambda *_a, **_k: None)
        monkeypatch.setattr(
            dashboard_router,
            "_peek_state_summary",
            lambda *_a, **_k: (_published_summary(), "hit", 0.0),
        )

        resp = self._client().get("/api/dashboard/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["totals"]["pass"] == 0
        assert data["totals"]["published_mdx"] == 55
        assert data["totals"]["missing"] == 25
        assert data["totals"]["missing"] != data["totals"]["total"]
        assert data["meta"]["track_scan"] == "stale"
        assert not data["meta"].get("refreshing")
