"""Tests for playground data generation and HTML validation."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLAYGROUNDS_DIR = ROOT / "playgrounds"
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
    """Validate playground HTML files have valid structure."""

    HTML_FILES = sorted(PLAYGROUNDS_DIR.glob("*.html"))

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

    # All endpoints referenced in playground HTML files
    EXPECTED_ENDPOINTS = {
        "/api/comms/batch-progress",
        "/api/comms/health",
        "/api/comms/live-activity",
        "/api/comms/messages",
        "/api/comms/send",
        "/api/comms/stats",
        "/api/comms/zombies",
        "/api/dashboard/overview",
        "/api/state/build-status",
        "/api/state/enrichment-status",
        "/api/state/issues",
        "/api/state/pipeline-versions",
        "/api/state/research-coverage",
        "/api/state/review-coverage",
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
        for html_file in PLAYGROUNDS_DIR.glob("*.html"):
            text = html_file.read_text()
            # Extract fetch URLs, strip query params
            fetches = re.findall(r"fetch\(['\"]([^'\"]+)['\"]", text)
            for url in fetches:
                clean = url.split("?")[0]
                all_endpoints.add(clean)

        # All found endpoints should be in our known set
        unknown = all_endpoints - self.EXPECTED_ENDPOINTS
        assert not unknown, f"Unknown API endpoints in playgrounds: {unknown}"


# ── Dashboard inventory ─────────────────────────────────────────

class TestDashboardInventory:
    """Verify expected dashboards exist."""

    EXPECTED_DASHBOARDS = {
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
        actual = {f.name for f in PLAYGROUNDS_DIR.glob("*.html")}
        missing = self.EXPECTED_DASHBOARDS - actual
        assert not missing, f"Missing dashboards: {missing}"

    def test_index_links_to_other_dashboards(self):
        """Index page should link to other dashboards."""
        index = PLAYGROUNDS_DIR / "index.html"
        if not index.exists():
            pytest.skip("No index.html")
        text = index.read_text()
        # Should reference at least a few other dashboard files
        linked = sum(1 for name in self.EXPECTED_DASHBOARDS
                     if name != "index.html" and name in text)
        assert linked >= 3, f"Index links to only {linked} dashboards"
