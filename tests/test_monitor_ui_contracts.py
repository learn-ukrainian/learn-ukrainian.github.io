from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_index_page_uses_shared_parchment_monitor_design():
    html = (ROOT / "playgrounds" / "index.html").read_text(encoding="utf-8")
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


def test_channels_page_has_shareable_deeplink_contract():
    html = (ROOT / "playgrounds" / "channels.html").read_text(encoding="utf-8")
    assert "new URLSearchParams(location.search)" in html
    assert "params.get('channel')" in html
    assert "params.get('thread')" in html
    assert "history.replaceState" in html
    assert "pendingThreadParam" in html
    assert "startsWith(pendingThreadParam)" in html


def test_orient_page_renders_active_discussions_widget():
    html = (ROOT / "playgrounds" / "orient.html").read_text(encoding="utf-8")
    assert "Active Discussions" in html
    assert "/api/discussions/active" in html
    assert "Promise.allSettled" in html
    assert "Discussion lookup unavailable" in html
    assert "renderDiscussions" in html
    assert "channels.html?channel=" in html


def test_runtime_page_keeps_primary_monitor_nav():
    html = (ROOT / "playgrounds" / "runtime.html").read_text(encoding="utf-8")
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


def test_comms_page_keeps_secondary_dashboard_links():
    html = (ROOT / "playgrounds" / "comms.html").read_text(encoding="utf-8")
    for href in [
        "/audit-dashboard.html",
        "/progress.html",
        "/curriculum-dashboard.html",
        "/quality.html",
        "/track-health.html",
    ]:
        assert f'href="{href}"' in html


def test_artifacts_page_uses_metadata_endpoint_and_filters():
    html = (ROOT / "playgrounds" / "artifacts.html").read_text(encoding="utf-8")
    assert "/api/artifacts/html" in html
    assert "class-filter" in html
    assert "status-filter" in html
    assert "author-filter" in html
    assert "date-filter" in html
    assert "artifact-card" in html


def test_artifacts_page_preserves_legacy_dashboard_links():
    html = (ROOT / "playgrounds" / "artifacts.html").read_text(encoding="utf-8")
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
        assert (ROOT / "playgrounds" / href.lstrip("/")).exists()
