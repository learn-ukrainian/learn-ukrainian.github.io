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

    def test_simple_format(self):
        count, target = self.parse("1200/1200")
        assert count == 1200
        assert target == 1200

    def test_invalid_returns_zero(self):
        count, target = self.parse("invalid")
        assert count == 0
        assert target == 0

    def test_empty_returns_zero(self):
        count, target = self.parse("")
        assert count == 0
        assert target == 0


class TestParseActivityCount:
    def setup_method(self):
        from generate_playground_data import parse_activity_count
        self.parse = parse_activity_count

    def test_standard(self):
        assert self.parse("13/8") == 13

    def test_invalid(self):
        assert self.parse("nope") == 0


class TestParseNaturalness:
    def setup_method(self):
        from generate_playground_data import parse_naturalness
        self.parse = parse_naturalness

    def test_standard(self):
        assert self.parse("9/10 (High)") == 9

    def test_low_score(self):
        assert self.parse("5/10") == 5

    def test_invalid(self):
        assert self.parse("N/A") == 0


# ── HTML validation tests ───────────────────────────────────────

class TestHtmlValidation:
    """Validate dashboard HTML files have valid structure."""

    HTML_FILES = sorted(DASHBOARDS_DIR.glob("*.html"))

    @pytest.mark.parametrize("html_file", HTML_FILES, ids=lambda p: p.name)
    def test_has_doctype(self, html_file):
        text = html_file.read_text()
        assert "<!DOCTYPE html>" in text or "<!doctype html>" in text

    @pytest.mark.parametrize("html_file", HTML_FILES, ids=lambda p: p.name)
    def test_has_charset(self, html_file):
        text = html_file.read_text()
        assert 'charset="UTF-8"' in text or "charset='UTF-8'" in text

    @pytest.mark.parametrize("html_file", HTML_FILES, ids=lambda p: p.name)
    def test_has_title(self, html_file):
        text = html_file.read_text()
        assert "<title>" in text and "</title>" in text

    @pytest.mark.parametrize("html_file", HTML_FILES, ids=lambda p: p.name)
    def test_balanced_tags(self, html_file):
        """Check major tags are balanced (html, head, body, script, style)."""
        text = html_file.read_text()
        for tag in ("html", "head", "body"):
            opens = len(re.findall(rf"<{tag}[\s>]", text, re.I))
            closes = len(re.findall(rf"</{tag}>", text, re.I))
            assert opens == closes, f"Unbalanced <{tag}> in {html_file.name}: {opens} open, {closes} close"

    @pytest.mark.parametrize("html_file", HTML_FILES, ids=lambda p: p.name)
    def test_no_broken_script_tags(self, html_file):
        """Verify all <script> tags are properly closed."""
        text = html_file.read_text()
        opens = len(re.findall(r"<script[\s>]", text, re.I))
        closes = len(re.findall(r"</script>", text, re.I))
        assert opens == closes, f"Unbalanced <script> in {html_file.name}: {opens} open, {closes} close"


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

    def test_expected_dashboards_exist(self):
        actual = {f.name for f in DASHBOARDS_DIR.glob("*.html")}
        missing = self.EXPECTED_DASHBOARDS - actual
        assert not missing, f"Missing dashboards: {missing}"

    def test_index_links_to_other_dashboards(self):
        """Index page should link to other dashboards."""
        index = DASHBOARDS_DIR / "index.html"
        if not index.exists():
            pytest.skip("No index.html")
        text = index.read_text()
        # Should reference at least a few other dashboard files
        linked = sum(1 for name in self.EXPECTED_DASHBOARDS
                     if name != "index.html" and name in text)
        assert linked >= 3, f"Index links to only {linked} dashboards"


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


class TestHomeLoadStatsPublished:
    """Home must show the published count overview already has on each track."""

    def test_index_loadstats_surfaces_published_from_overview(self):
        text = (DASHBOARDS_DIR / "index.html").read_text(encoding="utf-8")
        assert "track.published_mdx" in text
        assert "t.published" in text
        assert "passing · ${t.published} published" in text
        assert "${t.pass} passing / ${t.total} total" not in text


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

    def test_successful_refresh_settles_without_refreshing(self, monkeypatch, tmp_path):
        import scripts.api.dashboard_router as dashboard_router
        import scripts.api.state_helpers as state_helpers

        monkeypatch.setenv(
            dashboard_router.DASHBOARD_OVERVIEW_LAST_GOOD_ENV,
            str(tmp_path / "overview_last_good.json"),
        )
        summary = _published_summary()
        seeded = dashboard_router._build_overview_from_state_summary(
            summary, "hit", 0.0, track_scan="hit"
        )
        seeded["meta"]["track_scan"] = "hit"
        state_helpers.cache_set(dashboard_router._overview_cache_key(), seeded)
        scope = dashboard_router._overview_scope()
        dashboard_router._overview_last_good_by_scope[scope] = seeded
        monkeypatch.setattr(
            dashboard_router,
            "_peek_state_summary",
            lambda *_a, **_k: (summary, "hit", 0.0),
        )
        monkeypatch.setattr(dashboard_router, "_schedule_overview_refresh", lambda *_a, **_k: None)

        resp = self._client().get("/api/dashboard/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["meta"]["track_scan"] == "hit"
        assert "refreshing" not in data["meta"] or data["meta"].get("refreshing") is False
        assert data["totals"]["pass"] == 0
        assert data["totals"]["published_mdx"] == 55
        assert data["totals"]["missing"] != data["totals"]["total"]

    def test_stale_last_good_does_not_keep_refreshing(self, monkeypatch, tmp_path):
        import scripts.api.dashboard_router as dashboard_router

        monkeypatch.setenv(
            dashboard_router.DASHBOARD_OVERVIEW_LAST_GOOD_ENV,
            str(tmp_path / "overview_last_good.json"),
        )
        summary = _published_summary()
        seeded = dashboard_router._build_overview_from_state_summary(
            summary, "hit", 0.0, track_scan="hit"
        )
        dashboard_router._overview_last_good_by_scope[dashboard_router._overview_scope()] = seeded
        dashboard_router._overview_disk_loaded_by_scope[dashboard_router._overview_scope()] = True
        monkeypatch.setattr(
            dashboard_router,
            "_peek_state_summary",
            lambda *_a, **_k: (summary, "hit", 0.0),
        )
        monkeypatch.setattr(dashboard_router, "_schedule_overview_refresh", lambda *_a, **_k: None)

        resp = self._client().get("/api/dashboard/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["meta"]["track_scan"] == "stale"
        assert not data["meta"].get("refreshing")
        assert data["totals"]["published_mdx"] == 55
        assert data["totals"]["missing"] < data["totals"]["total"]
