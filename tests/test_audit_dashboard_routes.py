"""Tests for retired Audit Dashboard redirect (#7992 / formerly #7080)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DASHBOARDS_DIR = ROOT / "dashboards"


class TestAuditDashboardRedirect:
    """audit-dashboard.html is a bookmark-safe redirect to Quality."""

    def test_redirects_to_quality(self):
        html = (DASHBOARDS_DIR / "audit-dashboard.html").read_text(encoding="utf-8")
        assert 'http-equiv="refresh"' in html
        assert 'url=/quality.html' in html
        assert 'href="/quality.html"' in html
        assert "/api/dashboard/overview" not in html
