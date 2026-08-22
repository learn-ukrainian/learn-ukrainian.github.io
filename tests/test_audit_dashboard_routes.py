"""Tests for the audit-dashboard live-route contract (#7080).

Kept out of tests/test_dashboards.py so the slim fastlane does not plan the
whole dashboard module for an HTML-only change.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DASHBOARDS_DIR = ROOT / "dashboards"


class TestAuditDashboardLiveRoutes:
    """audit-dashboard.html must only call routes the Monitor API serves.

    The bare prefixes /api/dashboard and /api/state are not routes — they
    return 404. The page used them as JS base constants, so every request
    they prefixed was one string-concat away from a 404 base (#7080).
    """

    def test_no_404_prefix_constants(self):
        html = (DASHBOARDS_DIR / "audit-dashboard.html").read_text(encoding="utf-8")
        for dead in (
            "'/api/dashboard'",
            '"/api/dashboard"',
            "'/api/state'",
            '"/api/state"',
        ):
            assert dead not in html, f"404 API prefix still referenced: {dead}"

    def test_live_routes_present(self):
        html = (DASHBOARDS_DIR / "audit-dashboard.html").read_text(encoding="utf-8")
        for live in (
            "/api/dashboard/overview",
            "/api/dashboard/track/",
            "/api/dashboard/module/",
            "/api/state/module/",
        ):
            assert live in html, f"live route missing from page: {live}"
