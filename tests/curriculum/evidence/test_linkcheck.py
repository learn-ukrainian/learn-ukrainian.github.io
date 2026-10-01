"""Honest link-check identity, bounded retries and strict classified verification."""

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest

from scripts.curriculum.evidence import sources


@contextmanager
def link_server(statuses, *, reject_old_agent=False, retry_after=None):
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            agent = self.headers.get("User-Agent", "")
            seen.append(agent)
            status = statuses[min(len(seen) - 1, len(statuses) - 1)]
            if reject_old_agent and not agent.startswith("Mozilla/5.0 (compatible; learn-ukrainian-linkcheck/"):
                status = 403
            self.send_response(status)
            self.send_header("Content-Type", "text/html")
            if retry_after is not None:
                self.send_header("Retry-After", retry_after)
            if status == 302:
                self.send_header("Location", "/final")
            self.end_headers()

        def log_message(self, *args):
            pass

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = Thread(target=server.serve_forever)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}/page", seen
        finally:
            server.shutdown()
            thread.join()


@pytest.mark.parametrize(
    "statuses,reject_old,expected,calls",
    [
        ([200], True, 200, 1),
        ([403], False, 403, 1),
        ([429, 200], False, 200, 2),
        ([503], False, 503, 3),
        ([404], False, 404, 1),
        ([410], False, 410, 1),
        ([401], False, 401, 1),
        ([302, 200], False, 200, 2),
    ],
)
def test_link_check_local_http_server(monkeypatch, statuses, reject_old, expected, calls):
    delays = []
    monkeypatch.setattr(sources.time, "sleep", delays.append)
    with link_server(statuses, reject_old_agent=reject_old) as (url, seen):
        result = sources.check_url(url, timeout=1)
    assert result["http_status"] == expected
    assert len(seen) == calls
    assert all("learn-ukrainian-linkcheck/1.0" in agent for agent in seen)
    assert all("+https://github.com/learn-ukrainian/learn-ukrainian.github.io" in agent for agent in seen)
    assert len(delays) == (2 if expected == 503 else 1 if statuses[0] == 429 else 0)
    # The persisted checked shape is unchanged, including for failed checks.
    assert set(result) == {"http_status", "final_url", "content_type", "date"}


def test_retry_after_is_capped(monkeypatch):
    delays = []
    monkeypatch.setattr(sources.time, "sleep", delays.append)
    with link_server([429, 200], retry_after="99999") as (url, _):
        assert sources.check_url(url, timeout=1)["http_status"] == 200
    assert delays == [5.0]


@pytest.mark.parametrize("retry_after", ["garbage", "-1", "0"])
def test_retry_after_invalid_or_small_uses_backoff(retry_after):
    assert sources._url_retry_delay(retry_after, 0) == 0.5
    assert sources._url_retry_delay(retry_after, 1) == 1.0


def test_retry_after_http_date():
    from datetime import UTC, datetime, timedelta
    from email.utils import format_datetime

    future = format_datetime(datetime.now(UTC) + timedelta(seconds=120), usegmt=True)
    past = format_datetime(datetime.now(UTC) - timedelta(seconds=120), usegmt=True)
    assert sources._url_retry_delay(future, 0) == 5.0
    assert sources._url_retry_delay(past, 0) == 0.5


@pytest.mark.parametrize("recovers", [False, True])
def test_timeout_retries_are_bounded(monkeypatch, recovers):
    import urllib.error

    delays = []
    with link_server([200]) as (url, _):
        real_open = sources.urllib.request.urlopen
        calls = []

        def open_or_timeout(*args, **kwargs):
            calls.append(kwargs["timeout"])
            if recovers and len(calls) == 2:
                return real_open(*args, **kwargs)
            raise urllib.error.URLError(TimeoutError("synthetic timeout"))

        monkeypatch.setattr(sources.urllib.request, "urlopen", open_or_timeout)
        monkeypatch.setattr(sources.time, "sleep", delays.append)
        if recovers:
            assert sources.check_url(url, timeout=0.1)["http_status"] == 200
            assert calls == [0.1, 0.1]
            assert delays == [0.5]
        else:
            with pytest.raises(ConnectionError, match="after 3 attempts"):
                sources.check_url(url, timeout=0.1)
            assert calls == [0.1] * 3
            assert delays == [0.5, 1.0]
