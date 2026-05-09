from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
    assert "renderDiscussions" in html
    assert "channels.html?channel=" in html


def test_artifacts_page_uses_metadata_endpoint_and_filters():
    html = (ROOT / "playgrounds" / "artifacts.html").read_text(encoding="utf-8")
    assert "/api/artifacts/html" in html
    assert "class-filter" in html
    assert "status-filter" in html
    assert "author-filter" in html
    assert "date-filter" in html
    assert "artifact-card" in html
