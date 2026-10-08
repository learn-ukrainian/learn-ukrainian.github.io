"""ULP transport proof with hermetic HTTP clients and clock."""

import time
from types import SimpleNamespace

import pytest

from scripts.crawl import crawl_ulp as ulp


class FakeClient:
    def __init__(self, replies, clock):
        self.replies = iter(replies)
        self.clock = clock
        self.calls = []
        self.headers = {}
        self.closed = False

    def get(self, url, **kwargs):
        self.calls.append((url, self.clock[0], kwargs))
        return next(self.replies)

    def close(self):
        self.closed = True


def response(code=200, text="", headers=None):
    return SimpleNamespace(
        status_code=code, text=text, headers=headers or {}, raise_for_status=lambda: None, json=lambda: {"results": []}
    )


@pytest.fixture(autouse=True)
def state(monkeypatch):
    monkeypatch.setattr(ulp, "time", time, raising=False)
    monkeypatch.setattr(ulp, "_ulp_robots", {}, raising=False)
    monkeypatch.setattr(ulp, "_ulp_last_request", {}, raising=False)
    monkeypatch.setattr(ulp, "_ulp_stopped", False, raising=False)
    clock = [0.0]
    monkeypatch.setattr(ulp.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(ulp.time, "sleep", lambda s: clock.__setitem__(0, clock[0] + s))
    return clock


@pytest.mark.parametrize(
    "denial",
    [
        response(403),
        response(429),
        response(401),
        response(302),
        response(text="<title>Just a moment...</title>"),
        response(headers={"cf-mitigated": "challenge"}),
        response(text="<div id='cf_chl_widget'>"),
    ],
)
def test_website_denial_no_retry_or_followup(monkeypatch, state, denial):
    client = FakeClient([response(text="User-agent: *\nCrawl-delay: 4\nDisallow:"), denial], state)
    monkeypatch.setattr(ulp.requests, "Session", lambda: client)
    with pytest.raises(ulp._ULPAccessStopped):
        ulp.scrape_season1_from_website()
    with pytest.raises(ulp._ULPAccessStopped):
        ulp.scrape_season1_from_website()
    assert len(client.calls) == 2 and client.closed
    assert client.calls[1][1] == 4
    assert all(not k["allow_redirects"] for _, _, k in client.calls)
    assert client.headers == {"User-Agent": ulp.USER_AGENT}
    assert "https://github.com/learn-ukrainian/learn-ukrainian.github.io" in ulp.USER_AGENT
    assert "Chrome" not in ulp.USER_AGENT


def test_itunes_identity_robots_delay_and_payload(monkeypatch, state):
    client = FakeClient([response(text="User-agent: *\nCrawl-delay: 3\nDisallow:"), response(), response()], state)
    config = []

    def factory(**kwargs):
        config.append(kwargs)
        return client

    monkeypatch.setattr(ulp.httpx, "Client", factory)
    assert ulp.fetch_itunes_episodes(1) == []
    assert ulp.fetch_itunes_episodes(2) == []
    assert [t for _, t, _ in client.calls] == [0, 3, 6]
    assert config[0]["headers"] == {"User-Agent": ulp.USER_AGENT}
    assert config[0]["follow_redirects"] is False and client.closed


@pytest.mark.parametrize(
    "robots",
    [
        response(403),
        response(429),
        response(503),
        response(text="User-agent: *\nDisallow: /season1"),
        response(text="enable javascript and cookies to continue"),
    ],
)
def test_robots_stop_before_content(state, robots):
    client = FakeClient([robots], state)
    with pytest.raises(ulp._ULPAccessStopped):
        ulp._ulp_get(client, f"{ulp.BASE_URL}/season1/")
    assert len(client.calls) == 1


def test_website_success_preserves_shape(monkeypatch, state):
    client = FakeClient(
        [response(404), response(text='<a href="https://www.ukrainianlessons.com/episode1/">Synthetic metadata</a>')],
        state,
    )
    monkeypatch.setattr(ulp.requests, "Session", lambda: client)
    entries = ulp.scrape_season1_from_website()
    assert len(entries) == 1 and entries[0]["id"] == "ulp-ep-001"
    assert entries[0]["title"] == "Synthetic metadata" and client.closed
    assert client.calls[-1][1] == 2


def test_main_denial_preserves_output_and_skips_fmu(monkeypatch, tmp_path):
    output = tmp_path / "metadata.json"
    output.write_bytes(b"settled existing metadata\n")
    monkeypatch.setattr(ulp.sys, "argv", ["ulp", "--output", str(output)])
    calls = []

    def fetch(podcast_id, **kwargs):
        calls.append(podcast_id)
        return [{"trackName": "ULP 2-41 | Synthetic metadata", "kind": "podcast-episode"}]

    monkeypatch.setattr(ulp, "fetch_itunes_episodes", fetch)

    def deny():
        raise ulp._ULPAccessStopped("synthetic denial")

    monkeypatch.setattr(ulp, "scrape_season1_from_website", deny)
    monkeypatch.setattr(ulp, "season1_fallback", lambda: pytest.fail("denial must not become catalog success"))
    assert ulp.main() == 1
    assert calls == [ulp.ULP_ITUNES_ID] and output.read_bytes() == b"settled existing metadata\n"


def test_main_blog_only_never_uses_http(monkeypatch, tmp_path):
    output = tmp_path / "blog.json"
    monkeypatch.setattr(ulp.sys, "argv", ["ulp", "--blog-only", "--output", str(output)])
    monkeypatch.setattr(ulp, "fetch_itunes_episodes", lambda *_a, **_k: pytest.fail("blog catalog is local"))
    assert ulp.main() == 0 and output.is_file()


def test_fractional_crawl_delay_is_floor(state):
    client = FakeClient([response(text="User-agent: *\nCrawl-delay: 2.5\nDisallow:"), response()], state)
    ulp._ulp_get(client, f"{ulp.BASE_URL}/season1/")
    assert state[0] >= 2.5


def test_robots_network_failure_is_terminal(state):
    client = FakeClient([], state)

    def get(*_a, **_k):
        raise ulp.httpx.ConnectError("synthetic")

    client.get = get
    with pytest.raises(ulp._ULPAccessStopped):
        ulp._ulp_get(client, f"{ulp.BASE_URL}/season1/")
    assert ulp._ulp_stopped


def test_main_successful_episode_payload(monkeypatch, tmp_path):
    import json

    output = tmp_path / "metadata.json"
    monkeypatch.setattr(ulp.sys, "argv", ["ulp", "--episodes-only", "--output", str(output)])

    def fetch(podcast_id, **kwargs):
        return [{"trackName": "ULP 2-41 | Synthetic metadata"}] if podcast_id == ulp.ULP_ITUNES_ID else []

    monkeypatch.setattr(ulp, "fetch_itunes_episodes", fetch)
    monkeypatch.setattr(ulp, "scrape_season1_from_website", lambda: [])
    assert ulp.main() == 0
    payload = json.loads(output.read_text())
    assert payload["version"] == "3.0" and payload["stats"]["ulp_episodes"] == 41


def test_blog_catalog_import_failure(monkeypatch):
    import builtins

    original = builtins.__import__

    def importer(name, *args, **kwargs):
        if name == "crawl_ulp_blog":
            raise ImportError("synthetic missing module")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", importer)
    assert ulp.load_blog_articles() == []


@pytest.mark.parametrize("snippet", ["<script src='/cdn-cgi/challenge-platform/scripts/jsd/api.js'></script>", "<div class='g-recaptcha h-captcha'>verify you are human</div>"])
def test_normal_page_with_detection_or_captcha_still_parses(monkeypatch, state, snippet):
    page = snippet + '<a href="https://www.ukrainianlessons.com/episode1/">Synthetic metadata</a>'
    client = FakeClient([response(404), response(text=page)], state)
    monkeypatch.setattr(ulp.requests, "Session", lambda: client)
    assert ulp.scrape_season1_from_website()[0]["title"] == "Synthetic metadata"
    assert not ulp._ulp_stopped and len(client.calls) == 2 and client.closed
