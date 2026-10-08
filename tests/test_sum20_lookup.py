"""Fake HTTP and clock tests of official lookup transport."""

import time
from types import SimpleNamespace
from urllib.robotparser import RobotFileParser

import pytest

from scripts.lexicon import sum20_lookup as lookup


@pytest.fixture(autouse=True)
def state(monkeypatch):
    monkeypatch.setattr(lookup, "time", time, raising=False)
    monkeypatch.setattr(lookup, "_sum20_robots", None, raising=False)
    monkeypatch.setattr(lookup, "_sum20_last_request", None, raising=False)
    monkeypatch.setattr(lookup, "_sum20_stopped", False, raising=False)
    now = [0.0]
    monkeypatch.setattr(lookup.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(lookup.time, "sleep", lambda s: now.__setitem__(0, now[0] + s))
    return now


def response(code=200, text="", headers=None):
    return SimpleNamespace(status_code=code, text=text, headers=headers or {})


@pytest.mark.parametrize(
    "denial",
    [
        response(403),
        response(429),
        response(401),
        response(text="<title>Just a moment...</title>"),
        response(headers={"cf-mitigated": "challenge"}),
        response(503, "enable javascript and cookies to continue"),
        response(302),
    ],
)
def test_article_denial_stops_siblings_and_later_lookups(monkeypatch, denial):
    calls = []
    replies = iter(
        [
            response(text="User-agent: *\nCrawl-delay: 5\nDisallow:"),
            response(text='<a href="/?wordid=1">sample</a><a href="/?wordid=2">sample</a>'),
            denial,
        ]
    )

    def get(url, **kwargs):
        calls.append(url)
        return next(replies)

    monkeypatch.setattr(lookup.requests, "get", get)
    conn = SimpleNamespace(commit=lambda: None)
    with pytest.raises(lookup._Sum20AccessStopped):
        lookup.fetch_and_cache_sum20("sample", conn)
    with pytest.raises(lookup._Sum20AccessStopped):
        lookup.fetch_and_cache_sum20("other", conn)
    assert len(calls) == 3 and "wordid=1" in calls[-1]


def test_success_identity_and_pacing(monkeypatch, state):
    calls = []
    replies = iter(
        [
            response(text="User-agent: *\nCrawl-delay: 7\nDisallow:"),
            response(text='<a href="/?wordid=5">sample</a><a href="/?wordid=5">sample</a>'),
            response(text="article"),
        ]
    )

    def get(url, **kwargs):
        calls.append((url, state[0], kwargs))
        return next(replies)

    monkeypatch.setattr(lookup.requests, "get", get)
    monkeypatch.setattr(lookup, "parse_sum20_article", lambda body, wordid: (body, wordid))
    saved = []
    monkeypatch.setattr(lookup, "upsert_sum20_article", lambda conn, row: saved.append(row))
    monkeypatch.setattr(lookup, "lookup_sum20_cached", lambda *_: saved)
    assert lookup.fetch_and_cache_sum20("sample", SimpleNamespace(commit=lambda: None)) == [("article", 5)]
    assert [time for _, time, _ in calls] == [0, 7, 14]
    for _, _, kwargs in calls:
        assert "https://github.com/learn-ukrainian/learn-ukrainian.github.io" in kwargs["headers"]["User-Agent"]
        assert "Chrome" not in kwargs["headers"]["User-Agent"] and not kwargs["allow_redirects"]


@pytest.mark.parametrize(
    "robots",
    [
        response(403),
        response(429),
        response(503),
        response(text="User-agent: *\nDisallow: /"),
        response(text="<title>Just a moment...</title>"),
    ],
)
def test_robots_failure_never_requests_content(monkeypatch, robots):
    calls = []
    monkeypatch.setattr(lookup.requests, "get", lambda url, **_k: calls.append(url) or robots)
    with pytest.raises(lookup._Sum20AccessStopped):
        lookup._sum20_get("https://sum20ua.com/List/Search?searchWord=sample", 1)
    assert len(calls) == 1 and calls[0].endswith("robots.txt")


def test_robots_network_error_is_terminal(monkeypatch):
    def get(*_a, **_k):
        raise lookup.requests.ConnectionError("synthetic")

    monkeypatch.setattr(lookup.requests, "get", get)
    with pytest.raises(lookup._Sum20AccessStopped):
        lookup._sum20_get("https://sum20ua.com/", 1)
    assert lookup._sum20_stopped


def test_missing_robots_and_http_miss_are_not_denials(monkeypatch, state):
    replies = iter([response(404), response(404)])
    monkeypatch.setattr(lookup.requests, "get", lambda *_a, **_k: next(replies))
    assert lookup._sum20_get("https://sum20ua.com/", 1).status_code == 404
    assert state[0] == 2 and not lookup._sum20_stopped


def test_negative_article_does_not_discard_success(monkeypatch):
    parser = RobotFileParser()
    parser.parse([])
    monkeypatch.setattr(lookup, "_sum20_robots", parser, raising=False)
    replies = iter(
        [
            response(text='<a href="/?wordid=1">sample</a><a href="/?wordid=2">sample</a>'),
            response(text="good"),
            response(404),
        ]
    )
    monkeypatch.setattr(lookup.requests, "get", lambda *_a, **_k: next(replies))
    monkeypatch.setattr(lookup, "parse_sum20_article", lambda text, wordid: text)
    saved = []
    monkeypatch.setattr(lookup, "upsert_sum20_article", lambda conn, parsed: saved.append(parsed))
    monkeypatch.setattr(lookup, "lookup_sum20_cached", lambda *_: saved)
    assert lookup.fetch_and_cache_sum20("sample", SimpleNamespace(commit=lambda: None)) == ["good"]


def test_fractional_crawl_delay_is_floor(monkeypatch, state):
    replies = iter([response(text="User-agent: *\nCrawl-delay: 2.5\nDisallow:"), response()])
    monkeypatch.setattr(lookup.requests, "get", lambda *_a, **_k: next(replies))
    lookup._sum20_get("https://sum20ua.com/", 1)
    assert state[0] >= 2.5


def test_lookup_preserves_successful_article_before_sibling_denial(monkeypatch):
    parser = RobotFileParser()
    parser.parse([])
    monkeypatch.setattr(lookup, "_sum20_robots", parser)
    replies = iter([response(text='<a href="/?wordid=1">sample</a><a href="/?wordid=2">sample</a>'), response(text="first"), response(429)])
    monkeypatch.setattr(lookup.requests, "get", lambda *a, **k: next(replies))
    monkeypatch.setattr(lookup, "parse_sum20_article", lambda text, wordid: text)
    saved = []
    commits = []
    monkeypatch.setattr(lookup, "upsert_sum20_article", lambda conn, parsed: saved.append(parsed))
    with pytest.raises(lookup._Sum20AccessStopped):
        lookup.fetch_and_cache_sum20("sample", SimpleNamespace(commit=lambda: commits.append(True)))
    assert saved == ["first"] and commits == [True] and lookup._sum20_stopped


def test_test_boundary_isolation_only_resets_loaded_modules(monkeypatch):
    import sys

    from tests.conftest import _isolate_collector_transport_state

    # Synthetic aliases demonstrate reset without importing an absent collector.
    em = SimpleNamespace(_slovnyk_access_stopped=True, _slovnyk_robots=object(), _last_slovnyk_fetch=10)
    ulp = SimpleNamespace(_ulp_stopped=True, _ulp_robots={"host": object()}, _ulp_last_request={"host": 10})
    monkeypatch.setitem(sys.modules, "lexicon.enrich_manifest", em)
    monkeypatch.setitem(sys.modules, "crawl.crawl_ulp", ulp)
    monkeypatch.delitem(sys.modules, "lexicon.sum20_lookup", raising=False)
    boundary = _isolate_collector_transport_state.__wrapped__()
    next(boundary)
    assert not em._slovnyk_access_stopped and em._slovnyk_robots is None and em._last_slovnyk_fetch is None
    assert not ulp._ulp_stopped and ulp._ulp_robots == ulp._ulp_last_request == {}
    assert "lexicon.sum20_lookup" not in sys.modules
    em._slovnyk_access_stopped = True
    assert em._slovnyk_access_stopped  # no per-request reset during the test
    with pytest.raises(StopIteration):
        next(boundary)
    assert not em._slovnyk_access_stopped
