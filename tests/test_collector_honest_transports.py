"""Hermetic transport behavior across the three Packet D harvesters."""
from __future__ import annotations

import hashlib
import io
import json
import urllib.error
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse

import pytest
import requests

from scripts.crawl import download_textbooks as textbook
from scripts.ingest import zno_ingest as zno
from scripts.rag import scrape_ukrlib as ukrlib

MODULES = [textbook, zno, ukrlib]
CONTACT = "https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues"
NORMAL = b"<title>Source</title><article>captcha is a topic</article><script src='/cdn-cgi/challenge-platform/scripts/jsd/main.js'></script>"
CHALLENGE = b"<title>Just a moment...</title><script>cf_chl_opt={}</script>"


class Response:
    def __init__(self, body=b"source", status=200, headers=None):
        self.body = body
        self.status = self.status_code = self.code = status
        self.headers = headers or {}
        self.closed = False
        self.text = body.decode("utf-8", errors="replace")

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()

    def read(self):
        return self.body

    def raise_for_status(self):
        if self.status >= 400:
            raise requests.HTTPError(str(self.status))

    def iter_content(self, chunk_size):
        # Split markers across chunks to exercise streamed denial detection.
        for i in range(0, len(self.body), 7):
            yield self.body[i:i + 7]


class Clock:
    def __init__(self):
        self.now = 100.0
        self.sleeps = []

    def sleep(self, seconds):
        assert seconds >= 0
        self.sleeps.append(seconds)
        self.now += seconds


@pytest.fixture(autouse=True)
def isolate_policy(monkeypatch):
    clock = Clock()
    for module in MODULES:
        monkeypatch.setattr(module, "_access_stopped", False)
        monkeypatch.setattr(module, "_robots_delays", {})
        monkeypatch.setattr(module, "_request_times", {})
    monkeypatch.setattr(textbook.time, "monotonic", lambda: clock.now)
    monkeypatch.setattr(textbook.time, "sleep", clock.sleep)
    return clock


class Server:
    def __init__(self, monkeypatch, module, tmp_path, clock):
        self.module = module
        self.tmp_path = tmp_path
        self.clock = clock
        self.responses = {}
        self.calls = []
        self.robots = b"User-agent: *\nCrawl-delay: 2.75\n"
        self.cache_index = 0
        self.headers = {}
        self.cookies = {}
        monkeypatch.setattr(textbook.requests, "get", self.get)
        monkeypatch.setattr(textbook.requests, "Session", lambda: self)
        monkeypatch.setattr(zno.urllib.request, "build_opener", lambda *_handlers: SimpleNamespace(open=self.open))
        monkeypatch.setattr(ukrlib.subprocess, "run", self.curl)

    def reply(self, url, headers, method="get", **kwargs):
        self.calls.append((method, url, self.clock.now, headers, kwargs))
        queued = self.responses.get(url)
        if queued:
            result = queued.pop(0)
        elif urlparse(url).path == "/robots.txt":
            result = Response(self.robots)
        else:
            result = Response(NORMAL)
        if isinstance(result, Exception):
            raise result
        result.url = url
        return result

    def get(self, url, **kwargs):
        assert kwargs["allow_redirects"] is False
        return self.reply(url, kwargs.pop("headers"), **kwargs)

    def post(self, url, **kwargs):
        assert kwargs["allow_redirects"] is False
        return self.reply(url, kwargs.pop("headers"), method="post", **kwargs)

    def open(self, request, timeout):
        assert timeout == zno.FETCH_TIMEOUT_SECONDS
        response = self.reply(request.full_url, dict(request.header_items()))
        if response.status >= 300:
            raise urllib.error.HTTPError(request.full_url, response.status, "fixture", response.headers, io.BytesIO(response.body))
        return response

    def curl(self, args, **kwargs):
        assert "-sL" not in args and "-L" not in args and "--retry" not in args
        assert kwargs["timeout"] == 60
        ua = next(args[i + 1] for i, arg in enumerate(args) if arg == "-H" and args[i + 1].startswith("User-Agent:"))
        response = self.reply(args[-1], {"User-Agent": ua.split(": ", 1)[1]})
        Path(args[args.index("--dump-header") + 1]).write_bytes(
            f"HTTP/1.1 {response.status} Fixture\r\n".encode()
            + b"".join(f"{k}: {v}\r\n".encode() for k, v in response.headers.items()) + b"\r\n"
        )
        Path(args[args.index("--output") + 1]).write_bytes(response.body)
        return SimpleNamespace(returncode=0, stdout=str(response.status).encode(), stderr=b"")

    def fetch(self, url):
        if self.module is textbook:
            response = textbook._request(url, timeout=30)
            response.close()
            return response.text
        if self.module is zno:
            self.cache_index += 1
            return zno.fetch_page_with_rate_limit(url, self.tmp_path / f"page-{self.cache_index}.html")
        return ukrlib.fetch_page(url)

    def source_calls(self):
        return [call for call in self.calls if urlparse(call[1]).path != "/robots.txt"]


@pytest.fixture(params=MODULES, ids=["textbook", "zno", "ukrlib"])
def server(request, monkeypatch, tmp_path, isolate_policy):
    return Server(monkeypatch, request.param, tmp_path, isolate_policy)


@pytest.mark.parametrize("status,body,headers", [
    (403, b"Forbidden", {}), (429, b"Too many requests", {"Retry-After": "120"}),
    (200, b"arbitrary", {"Cf-Mitigated": "challenge"}), (200, CHALLENGE, {}),
    (503, b"Enable JavaScript and cookies to continue", {}),
    (302, CHALLENGE, {"Location": "/later"}),
])
def test_denial_stops_run_without_retry_redirect_or_later_page(server, status, body, headers):
    first = "https://source.test/first"
    server.responses[first] = [Response(body, status, headers)]
    with pytest.raises(server.module.AccessStopped):
        server.fetch(first)
    count = len(server.calls)
    with pytest.raises(server.module.AccessStopped):
        server.fetch("https://different.test/later")
    assert len(server.calls) == count
    assert len(server.source_calls()) == 1
    assert list(server.tmp_path.glob("page-*.html")) == []


def test_honest_identity_normal_js_and_fractional_robots_floor(server):
    server.fetch("https://source.test/first")
    server.fetch("https://source.test/second")
    assert [c[1] for c in server.calls] == [
        "https://source.test/robots.txt", "https://source.test/first", "https://source.test/second",
    ]
    for first, second in zip(server.calls, server.calls[1:], strict=False):
        assert second[2] - first[2] >= 2.75
    for _method, _url, _clock, headers, _kwargs in server.calls:
        ua = next(value for key, value in headers.items() if key.lower() == "user-agent")
        assert ua.startswith("LearnUkrainianBot/") and CONTACT in ua
        assert "Mozilla" not in ua and "Chrome" not in ua


def test_redirect_destination_has_own_robots_floor(server):
    server.responses["https://source.test/start"] = [Response(b"", 302, {"Location": "https://other.test/final"})]
    server.fetch("https://source.test/start")
    assert [c[1] for c in server.calls] == [
        "https://source.test/robots.txt", "https://source.test/start", "https://other.test/robots.txt", "https://other.test/final",
    ]
    assert server.calls[-1][2] - server.calls[-2][2] >= 2.75


def test_robots_denial_requests_no_source_page(server):
    server.responses["https://source.test/robots.txt"] = [Response(b"Forbidden", 403)]
    with pytest.raises(server.module.AccessStopped):
        server.fetch("https://source.test/first")
    assert len(server.calls) == 1 and server.source_calls() == []


@pytest.mark.parametrize("status", [404, 503])
def test_ordinary_errors_do_not_latch_a_denial(server, status):
    server.responses["https://source.test/bad"] = [Response(b"ordinary error", status)] * 3
    with pytest.raises((requests.HTTPError, urllib.error.HTTPError, RuntimeError)):
        server.fetch("https://source.test/bad")
    assert server.module._access_stopped is False
    server.fetch("https://source.test/good")
    assert server.source_calls()[-1][1] == "https://source.test/good"


@pytest.mark.parametrize("module", MODULES)
@pytest.mark.parametrize("body,expected", [
    ("User-agent: *\nCrawl-delay: 1.25", 1.25),
    ("User-agent: Other\nCrawl-delay: 99\nUser-agent: *\nCrawl-delay: 2.75", 2.75),
    ("User-agent: *\nCrawl-delay: 99\nUser-agent: LearnUkrainianBot\nCrawl-delay: 1.25", 1.25),
    ("User-agent: LearnUkrainianBot\nDisallow: /x\nCrawl-delay: .75\nUser-agent: learnukrainianbot\nCrawl-delay: 3.5", 3.5),
    ("User-agent: *\nCrawl-delay: nan\nCrawl-delay: inf\nCrawl-delay: -1\nCrawl-delay: wrong", 0),
    ("User-agent: Other\nCrawl-delay: 5", 0),
])
def test_observed_robots_delay_uses_applicable_finite_groups(module, body, expected):
    assert module._robots_crawl_delay(body) == expected


def test_zno_cache_is_byte_conserved_and_requires_no_network(tmp_path, monkeypatch):
    cache = tmp_path / "page.html"
    cache.write_bytes(NORMAL)
    before = hashlib.sha256(cache.read_bytes()).hexdigest()
    monkeypatch.setattr(zno, "_open", lambda *_args: pytest.fail("cache hit issued network request"))
    assert zno.fetch_page_with_rate_limit("https://source.test/page", cache) == NORMAL.decode()
    assert hashlib.sha256(cache.read_bytes()).hexdigest() == before
    cache.write_bytes(CHALLENGE)
    before = cache.read_bytes()
    with pytest.raises(zno.AccessStopped):
        zno.fetch_page_with_rate_limit("https://source.test/page", cache)
    assert cache.read_bytes() == before


@pytest.mark.parametrize("drive", [False, True])
@pytest.mark.parametrize("body,headers,status", [
    (CHALLENGE, {"Content-Type": "text/html"}, 200),
    (CHALLENGE, {}, 200), (CHALLENGE, {}, 404), (CHALLENGE, {}, 503),
    (b"no", {"Cf-Mitigated": "challenge"}, 200),
    (b"no", {}, 429),
])
def test_pdf_and_drive_denials_do_not_retain_or_request_confirmation(
    monkeypatch, tmp_path, isolate_policy, drive, body, headers, status,
):
    srv = Server(monkeypatch, textbook, tmp_path, isolate_policy)
    url = "https://docs.google.com/uc" if drive else "https://source.test/book.pdf"
    srv.responses[url] = [Response(body, status, headers)]
    existing = tmp_path / "retained.pdf"
    existing.write_bytes(b"%PDF-1.7\nretained fixture")
    before = existing.read_bytes()
    dest = tmp_path / "new.pdf"
    with pytest.raises(textbook.AccessStopped):
        if drive:
            textbook.download_from_gdrive("ID", dest, retained_store=tmp_path)
        else:
            textbook.download_pdf(url, dest, retained_store=tmp_path)
    assert len(srv.source_calls()) == 1
    assert existing.read_bytes() == before and not dest.exists()
    assert list(tmp_path.glob("*.part")) == []
    with pytest.raises(textbook.AccessStopped):
        textbook.extract_pdf_links("later", "author", 1)
    assert len(srv.source_calls()) == 1


def test_drive_confirmation_and_pdf_stream_keep_observed_floor(monkeypatch, tmp_path, isolate_policy):
    srv = Server(monkeypatch, textbook, tmp_path, isolate_policy)
    url = "https://docs.google.com/uc"
    srv.responses[url] = [
        Response(b'<form><input name="confirm" value="token"></form>', headers={"Content-Type": "text/html"}),
        Response(b"%PDF-1.7\nvalid content"),
    ]
    dest = tmp_path / "book.pdf"
    assert textbook.download_from_gdrive("ID", dest, retained_store=tmp_path)
    assert dest.read_bytes() == b"%PDF-1.7\nvalid content"
    calls = srv.source_calls()
    assert len(calls) == 2 and calls[1][2] - calls[0][2] >= 2.75
    assert calls[1][4]["params"]["confirm"] == "token"


def test_shkola_post_denial_stops_before_next_form(monkeypatch, tmp_path, isolate_policy):
    srv = Server(monkeypatch, textbook, tmp_path, isolate_policy)
    url = "https://shkola.in.ua/book"
    srv.responses[url] = [
        Response(b'<title>Author 6 \xd0\xba\xd0\xbb\xd0\xb0\xd1\x81</title><form action="/download"><button name="vslink" value="A">PDF</button></form><form action="/later"><button name="vslink" value="B">PDF</button></form>'),
    ]
    srv.responses["https://shkola.in.ua/download"] = [Response(b"no", 403)]
    with pytest.raises(textbook.AccessStopped):
        textbook.extract_shkola_pdf_links(url, author="Author", grade=6)
    calls = srv.source_calls()
    assert [c[0] for c in calls] == ["get", "post"]
    assert calls[-1][2] - calls[0][2] >= 2.75


def test_textbook_main_denial_stops_before_fallback_or_next_book(monkeypatch, tmp_path, isolate_policy):
    srv = Server(monkeypatch, textbook, tmp_path, isolate_policy)
    book = {"id": "a", "grade": 1, "slug": "first", "author": "Author", "year": 2025,
            "subject": "ukrmova", "canonical_source": "first", "fallback_page_urls": ["https://shkola.in.ua/later"]}
    monkeypatch.setattr(textbook, "load_selection", lambda: [book, {**book, "id": "b", "slug": "second"}])
    monkeypatch.setattr(textbook.sys, "argv", ["download_textbooks", "--retained-store", str(tmp_path)])
    srv.responses[f"{textbook.BASE_URL}/first.html"] = [Response(b"no", 403)]
    with pytest.raises(textbook.AccessStopped):
        textbook.main()
    assert len(srv.source_calls()) == 1


@pytest.mark.parametrize("folk", [False, True])
def test_ukrlib_denial_preserves_atomic_output_and_stops_work_loop(monkeypatch, tmp_path, isolate_policy, folk):
    srv = Server(monkeypatch, ukrlib, tmp_path, isolate_policy)
    monkeypatch.setattr(ukrlib, "LITERARY_DIR", tmp_path)
    monkeypatch.setattr(ukrlib, "PROGRESS_DIR", tmp_path / "progress")
    monkeypatch.setattr(ukrlib, "get_author_works", lambda _id: ([{"tid": 1, "title": "first"}, {"tid": 2, "title": "next"}], []))
    monkeypatch.setattr(ukrlib, "_build_narod_worklist", lambda: [
        {"genre_id": 1, "bookid": bid, "title": "fixture", "genre": "folk"} for bid in [1, 2]
    ])
    row = {"chunk_id": "kept", "text": "retained", "source_url": "https://source.test/old", "work": "kept", "author": "kept", "year": 1900, "genre": "prose", "language_period": "modern"}
    output = tmp_path / ("ukrlib-narod-dumy.jsonl" if folk else "ukrlib-test.jsonl")
    output.write_text(json.dumps(row) + "\n")
    before = output.read_bytes()
    url = f"{ukrlib.BASE_URL}/narod/printout.php?id=1&bookid=1" if folk else f"{ukrlib.BASE_URL}/books/printit.php?tid=1&page=1"
    srv.responses[url] = [Response(CHALLENGE)]
    with pytest.raises(ukrlib.AccessStopped):
        if folk:
            ukrlib.scrape_narod()
        else:
            ukrlib.scrape_author("test", {"id": 999, "name": "Fixture", "full_name": "Fixture", "years": "1900-1950", "genre_default": "prose", "period": "modern"})
    assert len(srv.source_calls()) == 1 and output.read_bytes() == before
    assert not list(tmp_path.glob("*.building"))
    assert not list((tmp_path / "progress").glob("*.done"))


def test_ukrlib_503_retry_and_encoding_are_retained(monkeypatch, tmp_path, isolate_policy):
    srv = Server(monkeypatch, ukrlib, tmp_path, isolate_policy)
    url = "https://source.test/page"
    # Byte fixtures avoid new Ukrainian authoring; these are windows-1251 bytes.
    payload = b"<article>\xd2\xe5\xea\xf1\xf2</article>"
    srv.responses[url] = [Response(b"unavailable", 503), Response(payload)]
    assert ukrlib.fetch_page(url) == payload.decode("windows-1251")
    assert len(srv.source_calls()) == 2
    assert srv.source_calls()[1][2] - srv.source_calls()[0][2] >= 3


def test_ukrlib_network_retry_does_not_latch_stop(monkeypatch, tmp_path, isolate_policy):
    srv = Server(monkeypatch, ukrlib, tmp_path, isolate_policy)
    original = ukrlib._curl_response
    failures = [True]
    def fail_once(url):
        if url.endswith("/page") and failures:
            failures.pop()
            return 0, {}, b"", 7
        return original(url)
    monkeypatch.setattr(ukrlib, "_curl_response", fail_once)
    assert ukrlib.fetch_page("https://source.test/page")
    assert ukrlib._access_stopped is False


@pytest.mark.parametrize("route", ["primary", "alternate", "alternate-drive", "fallback-page", "fallback-pdf", "fallback-drive", "listing-fallback"])
def test_textbook_main_each_download_route_aborts_on_denial(monkeypatch, tmp_path, isolate_policy, route):
    srv = Server(monkeypatch, textbook, tmp_path, isolate_policy)
    primary = "https://source.test/book.pdf"
    alternate = "https://alternate.test/book.pdf"
    fallback = "https://shkola.in.ua/book"
    book = {"id": "a", "grade": 6, "slug": "first", "author": "Author", "year": 2025,
            "subject": "ukrmova", "canonical_source": "first", "fallback_page_urls": [fallback]}
    pdf = {"url": primary, "filename": "book.pdf", "alternate_downloads": []}
    if route.startswith("alternate"):
        pdf["alternate_downloads"] = [{"url": alternate, "label": "fixture", "gdrive_id": "ID" if route.endswith("drive") else None}]
    if route != "listing-fallback":
        monkeypatch.setattr(textbook, "extract_pdf_links", lambda *_args, **_kwargs: [pdf])
    else:
        srv.responses[f"{textbook.BASE_URL}/first.html"] = [Response(b"ordinary failure", 404)]
    monkeypatch.setattr(textbook, "load_selection", lambda: [book, {**book, "id": "b"}])
    monkeypatch.setattr(textbook.sys, "argv", ["download_textbooks", "--retained-store", str(tmp_path)])
    srv.responses[primary] = [Response(b"no", 403 if route == "primary" else 404)]
    denied = primary
    if route.startswith("alternate"):
        denied = "https://docs.google.com/uc" if route.endswith("drive") else alternate
    elif route in {"fallback-page", "listing-fallback"}:
        denied = fallback
    elif route.startswith("fallback"):
        denied = "https://docs.google.com/uc" if route.endswith("drive") else "https://shkola.in.ua/result.pdf"
        srv.responses[fallback] = [Response(b'<title>Author 6 \xd0\xba\xd0\xbb\xd0\xb0\xd1\x81</title><form action="/download"><button name="vslink" value="A">PDF</button></form>')]
        locator = "https://drive.google.com/uc?export=download&id=ID" if route.endswith("drive") else denied
        srv.responses["https://shkola.in.ua/download"] = [Response(b"", 303, {"Location": locator})]
    srv.responses[denied] = [Response(b"no", 429)]
    with pytest.raises(textbook.AccessStopped):
        textbook.main()
    assert srv.source_calls()[-1][1] == denied
    count = len(srv.calls)
    with pytest.raises(textbook.AccessStopped):
        textbook.main()
    assert len(srv.calls) == count
    assert not list(tmp_path.rglob("*.pdf")) and not list(tmp_path.rglob("*.part"))


@pytest.mark.parametrize("drive", [False, True])
def test_existing_pdf_and_dry_run_make_no_request(monkeypatch, tmp_path, drive):
    monkeypatch.setattr(textbook, "_request", lambda *_args, **_kw: pytest.fail("local path requested network"))
    dest = tmp_path / "retained.pdf"
    dest.write_bytes(b"%PDF-1.7\nretained")
    before = hashlib.sha256(dest.read_bytes()).hexdigest()
    fn = textbook.download_from_gdrive if drive else textbook.download_pdf
    assert fn("ID", dest) is False
    assert fn("ID", tmp_path / "new.pdf", dry_run=True) is False
    assert hashlib.sha256(dest.read_bytes()).hexdigest() == before


def test_confirmation_html_remains_bounded(monkeypatch, tmp_path, isolate_policy):
    srv = Server(monkeypatch, textbook, tmp_path, isolate_policy)
    srv.responses["https://docs.google.com/uc"] = [Response(b"x" * 12000, headers={"Content-Type": "text/html"})]
    with pytest.raises(textbook.DownloadValidationError, match="confirmation HTML exceeds"):
        textbook.download_from_gdrive("ID", tmp_path / "new.pdf", max_size_bytes=50)
    assert not (tmp_path / "new.pdf").exists() and len(srv.source_calls()) == 1


def test_urllib_redirect_handler_prevents_implicit_followup(monkeypatch, tmp_path):
    import urllib.request
    import urllib.response
    calls = []
    class FakeHTTP(urllib.request.HTTPHandler):
        def http_open(self, request):
            calls.append(request.full_url)
            response = urllib.response.addinfourl(io.BytesIO(CHALLENGE), {"Location": "/later"}, request.full_url, 302)
            response.msg = "fixture"
            return response
    opener = urllib.request.build_opener(zno._NoRedirect(), FakeHTTP())
    monkeypatch.setattr(zno, "_open", lambda request: opener.open(request, timeout=30))
    monkeypatch.setattr(zno, "_robots_delays", {"http://source.test": 0.0})
    with pytest.raises(zno.AccessStopped):
        zno.fetch_page_with_rate_limit("http://source.test/first", tmp_path / "page")
    assert calls == ["http://source.test/first"]


def test_drive_html_content_type_cannot_truncate_a_valid_pdf(monkeypatch, tmp_path, isolate_policy):
    srv = Server(monkeypatch, textbook, tmp_path, isolate_policy)
    payload = b"%PDF-1.7\n" + b"fixture bytes\n" * 900
    srv.responses["https://docs.google.com/uc"] = [Response(payload, headers={"Content-Type": "text/html"})]
    dest = tmp_path / "book.pdf"
    assert textbook.download_from_gdrive("ID", dest, retained_store=tmp_path)
    assert dest.read_bytes() == payload
    assert len(srv.source_calls()) == 1
