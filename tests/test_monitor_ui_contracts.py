from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DASHBOARDS = ROOT / "dashboards"
PRIMARY_NAV_HREFS = [
    "/",
    "/orient.html",
    "/channels.html",
    "/comms.html",
    "/artifacts/",
    "/runtime.html",
]


def test_index_page_uses_shared_parchment_monitor_design():
    html = (DASHBOARDS / "index.html").read_text(encoding="utf-8")
    assert '<link rel="stylesheet" href="/monitor.css">' in html
    assert '<a class="active" href="/">Home</a>' in html
    assert "Operations launchpad" in html
    assert 'href="/artifacts/"' in html
    assert "#0d1117" not in html
    for href in [
        "/admin.html",
        "/channels.html",
        "/comms.html",
        "/audit-dashboard.html",
        "/build-events.html",
        "/consultation.html",
        "/cost.html",
        "/curriculum-dashboard.html",
        "/delegate.html",
        "/artifacts/",
        "/image-explorer.html",
        "/orient.html",
        "/progress.html",
        "/quality.html",
        "/runtime.html",
        "/track-health.html",
        "/wiki.html",
    ]:
        assert f'href="{href}"' in html


@pytest.mark.parametrize(
    ("filename", "active_link", "heading"),
    [
        ("orient.html", '<a class="active" href="/orient.html">Orient</a>', "One-page session orientation snapshot"),
        ("channels.html", '<a class="active" href="/channels.html">Channels</a>', "Agent Channels"),
        ("comms.html", '<a class="active" href="/comms.html">Comms</a>', "Agent Comms"),
    ],
)
def test_playground_page_uses_shared_parchment_monitor_design(filename, active_link, heading):
    html = (ROOT / "dashboards" / filename).read_text(encoding="utf-8")
    assert '<link rel="stylesheet" href="/monitor.css">' in html
    assert 'class="monitor-nav"' in html
    assert 'aria-label="Monitor sections"' in html
    assert active_link in html
    assert heading in html
    assert ":root" not in html
    assert "!important" not in html
    assert "#0d1117" not in html


def test_channels_page_has_shareable_deeplink_contract():
    html = (DASHBOARDS / "channels.html").read_text(encoding="utf-8")
    assert "new URLSearchParams(location.search)" in html
    assert "params.get('channel')" in html
    assert "params.get('thread')" in html
    assert "history.replaceState" in html
    assert "pendingThreadParam" in html
    assert "startsWith(pendingThreadParam)" in html


def test_orient_page_renders_active_discussions_widget():
    html = (DASHBOARDS / "orient.html").read_text(encoding="utf-8")
    assert "Active Discussions" in html
    assert "/api/discussions/active" in html
    assert "Promise.allSettled" in html
    assert "Discussion lookup unavailable" in html
    assert "renderDiscussions" in html
    assert "channels.html?channel=" in html


def test_runtime_page_keeps_primary_monitor_nav():
    html = (DASHBOARDS / "runtime.html").read_text(encoding="utf-8")
    assert '<link rel="stylesheet" href="/monitor.css">' in html
    assert '<a class="active" href="/runtime.html">Runtime</a>' in html
    for href in [
        "/orient.html",
        "/channels.html",
        "/comms.html",
        "/artifacts/",
        "/runtime.html",
    ]:
        assert f'href="{href}"' in html


def test_shared_monitor_css_targets_unified_nav_classes():
    css = (DASHBOARDS / "monitor.css").read_text(encoding="utf-8")
    assert ".topbar .nav" not in css
    assert ".topbar .monitor-nav" in css
    assert ".top-bar .monitor-nav" in css


def test_comms_page_keeps_secondary_dashboard_links():
    html = (DASHBOARDS / "comms.html").read_text(encoding="utf-8")
    for href in [
        "/audit-dashboard.html",
        "/progress.html",
        "/curriculum-dashboard.html",
        "/quality.html",
        "/track-health.html",
    ]:
        assert f'href="{href}"' in html


def test_artifacts_page_uses_metadata_endpoint_and_filters():
    html = (DASHBOARDS / "artifacts.html").read_text(encoding="utf-8")
    assert "/api/artifacts/html" in html
    assert "class-filter" in html
    assert "status-filter" in html
    assert "author-filter" in html
    assert "date-filter" in html
    assert "artifact-card" in html


def test_artifacts_page_preserves_legacy_dashboard_links():
    html = (DASHBOARDS / "artifacts.html").read_text(encoding="utf-8")
    assert 'href="/"' in html
    for href in [
        "/admin.html",
        "/channels.html",
        "/comms.html",
        "/audit-dashboard.html",
        "/build-events.html",
        "/consultation.html",
        "/cost.html",
        "/curriculum-dashboard.html",
        "/delegate.html",
        "/image-explorer.html",
        "/orient.html",
        "/progress.html",
        "/quality.html",
        "/runtime.html",
        "/track-health.html",
        "/wiki.html",
    ]:
        assert f'href="{href}"' in html
        assert (DASHBOARDS / href.lstrip("/")).exists()


def test_all_playground_pages_use_single_monitor_shell():
    for path in sorted(DASHBOARDS.glob("*.html")):
        html = path.read_text(encoding="utf-8")
        assert '<link rel="stylesheet" href="/monitor.css">' in html, path.name
        assert 'class="monitor-nav"' in html, path.name
        for href in PRIMARY_NAV_HREFS:
            assert f'href="{href}"' in html, path.name
        if "#0d1117" in html:
            assert html.rfind('<link rel="stylesheet" href="/monitor.css">') > html.rfind("</style>"), path.name


def test_operations_pages_keep_secondary_navigation():
    pages_to_hrefs = {
        "audit-dashboard.html": ["/track-health.html", "/docs"],
        "curriculum-dashboard.html": [
            "/audit-dashboard.html",
            "/progress.html",
            "/quality.html",
            "/track-health.html",
        ],
        "progress.html": ["/audit-dashboard.html", "/quality.html", "/track-health.html", "/docs"],
        "quality.html": ["/audit-dashboard.html", "/progress.html", "/track-health.html", "/docs"],
        "track-health.html": [
            "/progress.html",
            "/audit-dashboard.html",
            "/quality.html",
            "/curriculum-dashboard.html",
            "/docs",
        ],
    }
    for page, hrefs in pages_to_hrefs.items():
        html = (DASHBOARDS / page).read_text(encoding="utf-8")
        assert 'class="ops-nav"' in html, page
        for href in hrefs:
            assert f'href="{href}"' in html, page
