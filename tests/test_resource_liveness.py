"""Unit tests for scripts.build.resource_liveness (extracted in #3079).

The wikipedia-existence logic (Codex re-review holes #2 and #3) lives here now
that the checker is a shared module reused by both verify_shippable and
v7_build --enhance. These tests exercise it against its new home.
"""

from __future__ import annotations

import scripts.build.resource_liveness as rl


def test_wikipedia_host_matching_normalizes_case_and_port(monkeypatch):
    """A missing wiki article must be caught regardless of host case/port, instead
    of falling through to a curl 200 on the missing-page stub (Codex hole #2)."""
    seen = []

    def fake_curl(url, *, status_only):
        seen.append(url)
        if "api.php" in url:
            # MediaWiki API reports a MISSING article
            return 200, '{"query": {"pages": {"-1": {"missing": ""}}}}'
        return 200, ""  # a missing-page /wiki/ GET would still be HTTP 200

    monkeypatch.setattr(rl, "_curl", fake_curl)
    for url in (
        "https://UK.WIKIPEDIA.ORG/wiki/Definitely_missing_title",
        "https://uk.wikipedia.org:443/wiki/Definitely_missing_title",
        # non-/wiki/ article form must ALSO route to the API (Codex hole #3)
        "https://uk.wikipedia.org/w/index.php?title=Definitely_missing_title",
    ):
        rl._url_live_cache.clear()
        assert rl.url_is_live(url) is False
    # the API path (not a bare curl GET) decided it — the hole would have skipped it
    assert any("api.php" in u for u in seen)


def test_wikipedia_url_without_title_fails_closed(monkeypatch):
    """A wikipedia-host URL with no extractable article title must fail closed,
    not fall through to a curl 200 (Codex hole #3)."""
    curled = []

    def fake_curl(url, *, status_only):
        curled.append(url)
        return 200, ""  # a bare wikipedia GET would be 200 -> the hole if reached

    monkeypatch.setattr(rl, "_curl", fake_curl)
    rl._url_live_cache.clear()
    # /w/index.php?oldid=... has no `title` -> not confirmable -> fail closed,
    # and must NOT be probed with a bare liveness GET.
    assert rl.url_is_live("https://uk.wikipedia.org/w/index.php?oldid=12345") is False
    assert curled == []  # never fell through to a generic curl on a wikipedia host


def test_existing_wikipedia_article_is_live(monkeypatch):
    """A wikipedia article the API reports as present (no `missing` key) is live."""

    def fake_curl(url, *, status_only):
        assert "api.php" in url  # wikipedia always routes through the API
        return 200, '{"query": {"pages": {"12345": {"title": "Реальна_стаття"}}}}'

    monkeypatch.setattr(rl, "_curl", fake_curl)
    rl._url_live_cache.clear()
    assert rl.url_is_live("https://uk.wikipedia.org/wiki/Реальна_стаття") is True


def test_non_wikipedia_url_uses_status_check_and_caches(monkeypatch):
    """Non-wiki URLs use a redirect-following status probe; result is cached."""
    calls = []

    def fake_curl(url, *, status_only):
        calls.append(url)
        return 200, ""  # 2xx -> live

    monkeypatch.setattr(rl, "_curl", fake_curl)
    rl._url_live_cache.clear()
    assert rl.url_is_live("https://ukrlib.com.ua/some/real/path") is True
    # second call is served from cache — no extra curl
    assert rl.url_is_live("https://ukrlib.com.ua/some/real/path") is True
    assert len(calls) == 1


def test_dead_non_wikipedia_url_fails_closed(monkeypatch):
    def fake_curl(url, *, status_only):
        return 0, ""  # network failure / 4xx-5xx -> fail closed

    monkeypatch.setattr(rl, "_curl", fake_curl)
    rl._url_live_cache.clear()
    assert rl.url_is_live("https://example.invalid/dead") is False
