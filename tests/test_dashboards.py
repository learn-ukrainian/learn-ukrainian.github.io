"""Tests for dashboard data generation and HTML validation."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import ClassVar

import pytest

ROOT = Path(__file__).resolve().parent.parent
# The learn-ukrainian pages live in the product package (Monitor split, C-4687).
PRODUCT_PAGES_DIR = ROOT / "scripts" / "project_api" / "static"
PAGE_DIRS = (PRODUCT_PAGES_DIR,)
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

    HTML_FILES = sorted(path for page_dir in PAGE_DIRS for path in page_dir.glob("*.html"))

    def test_index_footer_does_not_reveal_an_internal_origin(self):
        """Defect class: the home page wrote ``location.host`` into the footer.

        #8542 stopped hardcoding ``localhost:8765``. Printing the live host
        replaced that with the view's internal origin. The footer must show
        neither a hardcoded host nor the live one.
        """
        text = (PRODUCT_PAGES_DIR / "index.html").read_text()
        assert "localhost:8765" not in text
        assert "127.0.0.1" not in text
        assert "location.host" not in text
        assert "footer-origin" not in text
        assert "Serving from" not in text

    def test_home_freshness_line_shows_age_and_stale_source(self):
        """Defect class: stale source data appeared current on the home page."""
        text = (PRODUCT_PAGES_DIR / "index.html").read_text()
        assert "cached copy older than" not in text
        assert "s limit" not in text
        assert "Computed ${meta.generated_at}" not in text
        assert "function freshnessLine" in text
        assert "toLocaleString" in text
        assert "s old" in text
        assert " · Stale" in text
        assert "setTimeout(refreshStats, 30000)" in text
        assert "white-space:nowrap" in text

    def test_dashboard_tiles_stay_uniform_and_do_not_break_names(self):
        """Defect class: tile area followed module count.

        BIO and LIT grew into empty blocks, ``overflow-wrap: anywhere`` broke
        long ids mid-word, and the select-a-module hint fell below that block.
        """
        text = (PRODUCT_PAGES_DIR / "curriculum-dashboard.html").read_text()
        assert "module_count / totalModules" not in text
        assert "overflow-wrap:anywhere" not in text
        assert "overflow-wrap: anywhere" not in text
        assert "repeat(auto-fill, minmax(10.25rem, 1fr))" in text
        assert "hyphens: none" in text
        assert "white-space: nowrap" in text
        assert ".right-panel:has(.empty)" in text
        assert "order: -1" in text
        assert 'id="dashboard-hint"' in text

    def test_home_and_dashboard_have_skip_link_main_and_os_scheme(self):
        """Defect class: no skip link, no dashboard main landmark, OS scheme ignored."""
        css = (PRODUCT_PAGES_DIR / "monitor.css").read_text()
        assert "@media (prefers-color-scheme: dark)" in css
        assert ".skip-link:focus" in css
        for name in ("index.html", "curriculum-dashboard.html"):
            text = (PRODUCT_PAGES_DIR / name).read_text()
            assert 'class="skip-link" href="#main"' in text
            assert "<main" in text
            assert 'id="main"' in text


def _channel(value: float) -> float:
    value = value / 255
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def _blend(background: str, ink: str, alpha: float) -> str:
    """Composite ``ink`` at ``alpha`` over an opaque ``#rrggbb`` background."""

    def channels(color: str) -> tuple[int, int, int]:
        return (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))

    base, layer = channels(background), channels(ink)
    mixed = tuple(round(base[i] * (1 - alpha) + layer[i] * alpha) for i in range(3))
    return "#" + "".join(f"{channel:02x}" for channel in mixed)


def _contrast(foreground: str, background: str) -> float:
    """WCAG 2.x contrast ratio for two ``#rrggbb`` colors."""

    def luminance(hex_color: str) -> float:
        red = int(hex_color[1:3], 16)
        green = int(hex_color[3:5], 16)
        blue = int(hex_color[5:7], 16)
        return 0.2126 * _channel(red) + 0.7152 * _channel(green) + 0.0722 * _channel(blue)

    lighter = max(luminance(foreground), luminance(background))
    darker = min(luminance(foreground), luminance(background))
    return (lighter + 0.05) / (darker + 0.05)


def _palette(css: str) -> dict[str, str]:
    return {name: value.lower() for name, value in re.findall(r"--([a-z0-9-]+):\s*(#[0-9a-fA-F]{6})\b", css)}


def test_muted_text_tokens_clear_wcag_aa_on_every_surface():
    """Defect class: muted ink ``#7a736a`` was 4.07:1 on ``#f5efde`` and 4.34:1 on ``#faf6ef``.

    ``#8a8377`` (the old ``--gray``) was 3.48:1 on the page background. Both
    tokens have to clear 4.5:1 on ``--bg``, ``--bg2`` and ``--bg3`` in light
    and dark. A 0.4 opacity on legacy rows dimmed every color in the row.
    The pending and unknown build badges painted ``--text3`` on
    ``rgba(72,79,88,0.2)``, which composites to about 4.32:1 on ``--bg``.
    """
    assert _contrast("#7a736a", "#f5efde") < 4.5
    assert _contrast("#7a736a", "#faf6ef") < 4.5
    assert _contrast("#8a8377", "#faf6ef") < 4.5
    # The gray wash over the page background, the pair the badge used to paint.
    assert _contrast("#665e56", _blend("#faf6ef", "#484f58", 0.2)) < 4.5
    dashboard = (PRODUCT_PAGES_DIR / "curriculum-dashboard.html").read_text()
    assert "opacity: 0.4" not in dashboard
    pending = re.search(r"\.module-table \.ver-pending \{([^}]+)\}", dashboard)
    assert pending is not None
    rule = pending.group(1)
    assert "rgba(" not in rule
    assert "background: var(--bg3)" in rule
    assert "color: var(--text3)" in rule

    css = (PRODUCT_PAGES_DIR / "monitor.css").read_text()
    light_css, dark_css = css.split("@media (prefers-color-scheme: dark)", 1)
    surfaces = ("bg", "bg2", "bg3")
    inks = ("text3", "gray")
    for scheme, palette in (("light", _palette(light_css)), ("dark", _palette(dark_css))):
        for ink in inks:
            for surface in surfaces:
                ratio = _contrast(palette[ink], palette[surface])
                assert ratio >= 4.5, f"{scheme} --{ink} on --{surface} is {ratio:.2f}:1"


# ── API endpoint coverage ───────────────────────────────────────


class TestApiEndpoints:
    """Verify dashboard API endpoints are defined in the API server."""

    # All endpoints referenced in dashboard HTML files
    EXPECTED_ENDPOINTS: ClassVar[set[str]] = {
        "/api/artifacts/html",
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
        api_dirs = [ROOT / "scripts" / "api", ROOT / "scripts" / "project_api"]
        if not all(api_dir.exists() for api_dir in api_dirs):
            pytest.skip("API directory not found")

        # Read all router files: machinery and product halves of the Monitor API
        router_text = ""
        for api_dir in api_dirs:
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
                endpoint,  # /api/state/summary
                route_relative,  # /summary or /enrichment-status
                f'"{route_relative}"',  # quoted in decorator
                f'"/{last_segment}"',  # just the last segment quoted
                last_segment.replace("-", "_"),  # function name convention
            ]
            found = any(v in router_text for v in path_variants)
            if not found:
                missing.append(endpoint)

        assert not missing, "API endpoints referenced in dashboards but not found in routers:\n" + "\n".join(missing)

    def test_fetch_calls_in_html(self):
        """Verify all fetch calls reference known endpoints."""
        all_endpoints = set()
        for html_file in (path for page_dir in PAGE_DIRS for path in page_dir.glob("*.html")):
            text = html_file.read_text()
            # Extract fetch URLs, strip query params
            fetches = re.findall(r"fetch\(['\"]([^'\"]+)['\"]", text)
            for url in fetches:
                clean = url.split("?")[0]
                all_endpoints.add(clean)

        # All found endpoints should be in our known set
        unknown = all_endpoints - self.EXPECTED_ENDPOINTS
        assert not unknown, f"Unknown API endpoints in dashboards: {unknown}"


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
        import scripts.project_api.dashboard_router as dashboard_router

        dashboard_router.reset_overview_state_for_tests()

    def teardown_method(self):
        import scripts.project_api.dashboard_router as dashboard_router

        dashboard_router.reset_overview_state_for_tests()

    def _client(self):
        from fastapi.testclient import TestClient
        from lu_machinery.api.main import app

        return TestClient(app, raise_server_exceptions=False)

    def test_cold_process_published_is_not_all_missing(self, monkeypatch, tmp_path):
        import scripts.project_api.dashboard_router as dashboard_router

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
        import scripts.project_api.dashboard_router as dashboard_router

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

    @pytest.mark.parametrize("cached", [False, True])
    @pytest.mark.parametrize("source_age", [30, 61, 46800, None])
    def test_source_age_not_cache_age_and_stale_source_labelled(self, monkeypatch, tmp_path, cached, source_age):
        """Defect class: a newly cached old snapshot reports age zero and fresh."""
        from datetime import UTC, datetime, timedelta

        import scripts.project_api.dashboard_router as dashboard_router

        now = datetime(2026, 11, 14, 6, 0, tzinfo=UTC)

        class Clock(datetime):
            @classmethod
            def now(cls, tz=None):
                return now

        monkeypatch.setattr(dashboard_router, "datetime", Clock)
        monkeypatch.setenv(dashboard_router.DASHBOARD_OVERVIEW_LAST_GOOD_ENV, str(tmp_path / "last-good.json"))
        monkeypatch.setattr(dashboard_router, "_schedule_overview_refresh", lambda *_a, **_k: None)
        summary = _published_summary()
        generated_at = (now - timedelta(seconds=source_age)).isoformat() if source_age is not None else None
        payload = {
            "tracks": [{"id": "a1", "module_count": 80, "stats": {"missing": 25}}],
            "totals": {"total": 80},
            "meta": {"generated_at": generated_at, "age_s": 0.0},
        }
        # An unrelated, fresh state-summary cache must not reset the track scan age.
        monkeypatch.setattr(dashboard_router, "_peek_state_summary", lambda *_a, **_k: (summary, "hit", 0.0))
        if cached:
            monkeypatch.setattr(dashboard_router, "cache_get_with_age", lambda *_a, **_k: (payload, 0.0))
        else:
            dashboard_router.persist_overview_last_good(payload)
        response = self._client().get("/api/dashboard/overview")
        assert response.status_code == 200
        meta = response.json()["meta"]
        assert meta["generated_at"] == generated_at
        assert meta["age_s"] == source_age
        assert meta["stale"] is (not cached or source_age is None or source_age > 60)
