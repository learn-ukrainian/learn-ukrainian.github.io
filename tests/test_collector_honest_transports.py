"""Hermetic transport behavior across the three Packet D harvesters."""
from __future__ import annotations

import hashlib
import io
import json
import urllib.error
from itertools import pairwise
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
        self.body = self.content = body
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
        monkeypatch.setattr(module, "_robots_states", {})
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


@pytest.fixture
def curl_capture(monkeypatch):
    """Write frozen wire bytes at the subprocess boundary, using the real reader."""
    def capture(raw_headers, *, stdout=b"200", returncode=0):
        body = bytes(range(256))
        calls = []

        def run(args, **kwargs):
            calls.append(args)
            assert kwargs == {"capture_output": True, "timeout": 60}
            assert args[0] == "curl" and args[-1] == "https://source.test/page"
            assert "-L" not in args and "--retry" not in args
            Path(args[args.index("--dump-header") + 1]).write_bytes(raw_headers)
            Path(args[args.index("--output") + 1]).write_bytes(body)
            return SimpleNamespace(stdout=stdout, returncode=returncode, stderr=b"")

        monkeypatch.setattr(ukrlib.subprocess, "run", run)
        result = ukrlib._curl_response("https://source.test/page")
        assert len(calls) == 1
        assert result[2] == body
        assert result[3] == returncode
        return result

    return capture


@pytest.mark.parametrize("eol", [b"\r\n", b"\n"], ids=["crlf", "lf"])
@pytest.mark.parametrize("stdout,returncode,status", [
    (b"200", 0, 200), (b"503\n", 22, 503), (b"", 7, 0),
])
def test_curl_response_physical_headers_and_capture_metadata(curl_capture, eol, stdout, returncode, status):
    raw = eol.join([b"HTTP/1.1 200 OK", b"Content-Type: text/html", b"X-Value \t: \t a:b \t", b"X-Empty:\t ", b"", b""])
    actual_status, headers, _body, _rc = curl_capture(raw, stdout=stdout, returncode=returncode)
    assert actual_status == status
    assert headers == {"content-type": "text/html", "x-value": "a:b", "x-empty": ""}


@pytest.mark.parametrize("eol", [b"\r\n", b"\n"], ids=["crlf", "lf"])
@pytest.mark.parametrize("value,expected", [
    (b"safe\x85Cf-Mitigated: challenge", "safe\x85Cf-Mitigated: challenge"),
    (b"safe\x85Location: /private", "safe\x85Location: /private"),
    (b"safe\x85Retry-After: 999", "safe\x85Retry-After: 999"),
    (b"safe\x85HTTP/1.1 200 OK", "safe\x85HTTP/1.1 200 OK"),
], ids=["challenge-field", "redirect-field", "retry-field", "status-reset"])
def test_curl_response_nel_cannot_invent_fields_or_reset_block(curl_capture, eol, value, expected):
    # Literal controls and expectations are independent of the parser's framing.
    raw = eol.join([b"HTTP/1.1 200 OK", b"Cf-Mitigated: challenge", b"X-Opaque: " + value, b"X-After: retained", b"", b""])
    status, headers, _body, _rc = curl_capture(raw)
    assert status == 200
    assert headers == {"cf-mitigated": "challenge", "x-opaque": expected, "x-after": "retained"}


@pytest.mark.parametrize("eol", [b"\r\n", b"\n"], ids=["crlf", "lf"])
@pytest.mark.parametrize("octet", range(0x80, 0x100), ids=lambda octet: f"{octet:02x}")
def test_curl_response_preserves_every_opaque_octet(curl_capture, eol, octet):
    opaque = bytes([octet])
    value = opaque + b":field HTTP/1.1 200 OK" + opaque
    raw = eol.join([
        b"HTTP/1.1 200 OK", b"X-Before: retained", b"X-Opaque: \t" + value + b" \t",
        b"X-Single: " + opaque, b"X-After: retained", b"", b"",
    ])
    _status, headers, _body, _rc = curl_capture(raw)
    assert headers == {
        "x-before": "retained", "x-opaque": value.decode("iso-8859-1"),
        "x-single": chr(octet), "x-after": "retained",
    }


@pytest.mark.parametrize("eol", [b"\r\n", b"\n"], ids=["crlf", "lf"])
def test_curl_response_genuine_status_blocks_reset_headers(curl_capture, eol):
    raw = eol.join([
        b"HTTP/1.1 200 Connection established", b"X-Proxy: obsolete", b"",
        b"HTTP/1.1 100 Continue", b"X-Interim: obsolete", b"",
        b"HTTP/2 200", b"X-Final: retained", b"X-Opaque: \x85\xa0", b"", b"",
    ])
    status, headers, _body, _rc = curl_capture(raw)
    assert status == 200
    assert headers == {"x-final": "retained", "x-opaque": "\x85\xa0"}


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
    ("User-agent: Other\nCrawl-delay: 99\nUser-agent: *\nCrawl-delay: 2.75", 99),
    ("User-agent: *\nCrawl-delay: 99\nUser-agent: LearnUkrainianBot\nCrawl-delay: 1.25", 99),
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
    monkeypatch.setattr(zno, "_robots_states", {"http://source.test": zno._robots_parse(b"", zno.USER_AGENT)})
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


# Disclosed controls, handwritten here. They are regression evidence, never
# independent held-outs. None imports an adviser/reference implementation.
def group(*lines):
    return b"User-agent: *\n" + b"\n".join(lines) + b"\n"


RFC_GROUPS = (b"User-Agent: *\nDisallow: *.gif$\nDisallow: /example/\nAllow: /publications/\n\n"
              b"User-Agent: foobot\nDisallow:/\nAllow:/example/page.html\nAllow:/example/allowed.gif\n\n"
              b"User-Agent: barbot\nUser-Agent: bazbot\nDisallow: /example/page.html\n\nUser-Agent: quxbot\n\nEOF\n")
RFC_PREFIX = b"User-Agent: foobot\nAllow: /example/page/\nDisallow: /example/page/disallowed.gif\n"
ALLOW = "allow"
DENY = "robots_disallowed"
AMBIGUOUS = "robots_ambiguous"
UNRESOLVED = "robots_unresolved"
SUM_HEADER = "learn-ukrainian-sum20/1.0"
# id, raw body, exact target, decision; optional header replaces the D header.
LEGACY_CONTROLS = [
    ("F4.1", group(b"Disallow: /foo/bar?baz=quz"), "/foo/bar?baz=quz", DENY),
    ("F4.2a", group(b"Disallow: /foo/bar?baz=https%3A%2F%2Ffoo.bar"), "/foo/bar?baz=https%3A%2F%2Ffoo.bar", DENY),
    ("F4.2b", group(b"Disallow: /foo/bar?baz=https%3a%2f%2ffoo.bar"), "/foo/bar?baz=https%3A%2F%2Ffoo.bar", DENY),
    ("F4.2c", group(b"Disallow: /foo/bar?baz=https%3A%2F%2Ffoo.bar"), "/foo/bar?baz=https://foo.bar", AMBIGUOUS),
    ("F4.3a", group(b"Disallow: /foo/bar/\xe3\x83\x84"), "/foo/bar/%E3%83%84", DENY),
    ("F4.3b", group(b"Disallow: /foo/bar/\xe3\x83\x84"), "/foo/bar/" + b"\xe3\x83\x84".decode(), DENY),
    ("F4.3c", group(b"Disallow: /foo/bar/%e3%83%84"), "/foo/bar/" + b"\xe3\x83\x84".decode(), DENY),
    ("F4.4", group(b"Disallow: /foo/bar/%E3%83%84"), "/foo/bar/%e3%83%84", DENY),
    ("F4.5a", group(b"Disallow: /foo/bar/baz"), "/foo/bar/%62%61%7A", DENY),
    ("F4.5b", group(b"Disallow: /foo/bar/%62%61%7A"), "/foo/bar/baz", DENY),
    ("F4.5c", group(b"Disallow: /foo/bar/%62%61%7a"), "/foo/bar/%62%61%7A", DENY),
    ("F4.5d", group(b"Disallow: /foo/bar/%62%61%7A$"), "/foo/bar/baz", DENY),
    ("U.tilde", group(b"Disallow: /~user"), "/%7Euser/x", DENY),
    ("U.mixed", group(b"Disallow: /a-b_c.d"), "/a%2Db%5Fc%2Ed", DENY),
    ("F6.1a", group(b"Disallow: /path/file-with-a-%2A.html"), "/path/file-with-a-*.html", DENY),
    ("F6.1b", group(b"Disallow: /path/file-with-a-%2a.html"), "/path/file-with-a-%2A.html", DENY),
    ("F6.1c", group(b"Disallow: /path/file-with-a-%2A.html"), "/path/file-with-a-x.html", ALLOW),
    ("F6.2a", group(b"Disallow: /path/foo-%24"), "/path/foo-$", DENY),
    ("F6.2b", group(b"Disallow: /path/foo-%24"), "/path/foo-%24", DENY),
    ("F6.2c", group(b"Disallow: /path/foo-%24"), "/path/foo-", ALLOW),
    ("F6.2d", group(b"Disallow: /path/foo-%24$"), "/path/foo-$x", ALLOW),
    ("OP.star", group(b"Disallow: /this/*/exactly"), "/this/a/b/exactly", DENY),
    ("OP.star0", group(b"Disallow: /this/*/exactly"), "/this//exactly", DENY),
    ("OP.dollar", group(b"Allow: /", b"Disallow: /this/path/exactly$"), "/this/path/exactly", DENY),
    ("OP.dollar2", group(b"Disallow: /this/path/exactly$"), "/this/path/exactly/more", ALLOW),
    ("OP.dollarq", group(b"Disallow: /*.pdf$"), "/x/y.pdf?a=1", ALLOW),
    ("OP.midDollar", group(b"Disallow: /a$b"), "/a$b", DENY),
    ("OP.midDollarEnc", group(b"Disallow: /a$b"), "/a%24b", DENY),
    ("OP.dollarDollar", group(b"Disallow: /a$$"), "/a$", DENY),
    ("OP.dollarDollar2", group(b"Disallow: /a$$"), "/a$b", ALLOW),
    ("OP.starLiteralUri", group(b"Disallow: /a*c"), "/a*c", DENY),
    ("OP.starStar", group(b"Disallow: /a**b"), "/aXXb", DENY),
    ("OP.starOnly", group(b"Disallow: *"), "/anything", DENY),
    ("OP.starTie", group(b"Disallow: *", b"Allow: /"), "/anything", AMBIGUOUS),
    ("OP.starDollar", group(b"Disallow: /*$"), "/x?y", DENY),
    ("OP.noLeadingSlash", group(b"Disallow: private"), "/private", UNRESOLVED),
    ("OP.escapeAtomic", group(b"Disallow: /*2F"), "/a%2F", AMBIGUOUS),
    ("OP.escapeAtomic2", group(b"Disallow: /*%2F"), "/a%2F", DENY),
    ("OP.escapePrefix", group(b"Disallow: /a%"), "/a%2F", UNRESOLVED),
    ("R.slash", group(b"Disallow: /a%2Fb"), "/a/b", AMBIGUOUS),
    ("R.slash2", group(b"Disallow: /a/b"), "/a%2Fb", AMBIGUOUS),
    ("R.slash3", group(b"Disallow: /a%2fb"), "/a%2Fb", DENY),
    ("R.eq", group(b"Disallow: /s?q=a%3Db"), "/s?q=a=b", AMBIGUOUS),
    ("R.amp", group(b"Disallow: /s?a=1&b"), "/s?a=1%26b", AMBIGUOUS),
    ("R.qmark", group(b"Disallow: /a?"), "/a%3F", AMBIGUOUS),
    ("R.semicolon", group(b"Disallow: /a;p"), "/a;p=1", DENY),
    ("R.colonRaw", group(b"Disallow: /a:b"), "/a:b", DENY),
    ("E.stray", group(b"Disallow: /a%zz"), "/a%zz", UNRESOLVED),
    ("E.strayEq25", group(b"Disallow: /a%zz"), "/a%25zz", UNRESOLVED),
    ("E.trailing", group(b"Disallow: /a%"), "/a%", UNRESOLVED),
    ("E.half", group(b"Disallow: /a%4"), "/a%4", UNRESOLVED),
    ("E.halfNotA", group(b"Disallow: /a%4"), "/aA", UNRESOLVED),
    ("E.pct25", group(b"Disallow: /100%25"), "/100%25", DENY),
    ("N.cyr", group(b"Disallow: /\xd0\xba\xd0\xbd\xd0\xb8\xd0\xb3\xd0\xb0"), "/%D0%BA%D0%BD%D0%B8%D0%B3%D0%B0/1", DENY),
    ("N.cyrRawUri", group(b"Disallow: /%D0%BA%D0%BD%D0%B8%D0%B3%D0%B0"), "/" + b"\xd0\xba\xd0\xbd\xd0\xb8\xd0\xb3\xd0\xb0".decode(), DENY),
    ("N.badUtf8", group(b"Disallow: /\xff\xfe"), "/%FF%FE/x", UNRESOLVED),
    ("N.badUtf8Other", group(b"Disallow: /\xff", b"Disallow: /private"), "/private/x", UNRESOLVED),
    ("N.fffdNotBad", group(b"Disallow: /\xff"), "/%EF%BF%BD", UNRESOLVED),
    ("C.space", group(b"Disallow: /a b"), "/a%20b", UNRESOLVED),
    ("C.tabTrim", b"User-agent: *\nDisallow:\t/a\t\n", "/a", DENY),
    ("C.nul", group(b"Disallow: /a\x00b"), "/a%00b", UNRESOLVED),
    ("C.ffInValue", group(b"Disallow: /a\x0cb"), "/a%0Cb", UNRESOLVED),
    ("C.pipe", group(b"Disallow: /a|b"), "/a%7Cb", DENY),
    ("C.caseSensitive", group(b"Disallow: /Admin"), "/admin", ALLOW),
    ("L.inlineComment", group(b"Disallow: /foo/quz#qux", b"Allow: /"), "/foo/quz", DENY),
    ("L.commentOnly", b"# Disallow: /\nUser-agent: *\nAllow: /\n", "/x", ALLOW),
    ("L.commentedRule", group(b"# Disallow: /x"), "/x", ALLOW),
    ("L.cr", b"User-agent: *\rDisallow: /a\r", "/a", DENY),
    ("L.crlf", b"User-agent: *\r\nDisallow: /a\r\n", "/a", DENY),
    ("L.bom", b"\xef\xbb\xbfUser-agent: *\nDisallow: /a\n", "/a", DENY),
    ("L.keyCase", b"USER-AGENT: *\nDISALLOW: /a\n", "/a", DENY),
    ("L.noColon", b"User-agent: *\nDisallow /a\n", "/a", UNRESOLVED),
    ("L.blankInGroup", b"User-agent: *\n\nDisallow: /a\n", "/a", DENY),
    ("G.exact", b"User-agent: bot\nDisallow: /\nUser-agent: *\nAllow: /\n", "/x", UNRESOLVED),
    ("G.version", b"User-agent: LearnUkrainianBot/1.0\nDisallow: /\n", "/x", UNRESOLVED),
    ("G.merge", b"User-agent: learnukrainianbot\nDisallow: /a\nUser-agent: LEARNUKRAINIANBOT\nDisallow: /b\n", "/b", DENY),
    ("G.replacesStar", b"User-agent: *\nDisallow: /\nUser-agent: LearnUkrainianBot\nDisallow: /private\n", "/public", ALLOW),
    ("G.multiUA", b"User-agent: a\nUser-agent: learnukrainianbot\nDisallow: /\n", "/x", UNRESOLVED),
    ("G.sitemap", b"User-agent: a\nSitemap: https://h.test/s.xml\nUser-agent: learnukrainianbot\nDisallow: /\n", "/x", UNRESOLVED),
    ("G.beforeGroup", b"Disallow: /\nUser-agent: *\nAllow: /\n", "/x", ALLOW),
    ("G.noMatchNoStar", b"User-agent: otherbot\nDisallow: /\n", "/x", ALLOW),
    ("G.noGroups", b"", "/x", ALLOW),
    ("G.starWord", b"User-agent: *bot\nDisallow: /\n", "/x", UNRESOLVED),
    ("G.starComment", b"User-agent: * # all\nDisallow: /\n", "/x", DENY),
    ("G.hyphenToken", b"User-agent: learn\nDisallow: /\nUser-agent: learn-ukrainian-sum20\nAllow: /\n", "/x", UNRESOLVED, SUM_HEADER),
    ("G.hyphenToken2", b"User-agent: learn\nDisallow: /\n", "/x", UNRESOLVED, SUM_HEADER),
    ("G.emptyRuleSplits", b"User-agent: a\nDisallow:\nUser-agent: learnukrainianbot\nDisallow: /x\n", "/x", UNRESOLVED),
    ("G.emptyDisallow", group(b"Disallow:"), "/x", ALLOW),
    ("S.longest", group(b"Disallow: /a", b"Allow: /a/b"), "/a/b", ALLOW),
    ("S.tie", group(b"Disallow: /p", b"Allow: /p"), "/p", ALLOW),
    ("S.equivSpelling", group(b"Disallow: /foo/bar/%62%61%7A", b"Allow: /foo/bar/baz"), "/foo/bar/baz", ALLOW),
    ("S.escapeCounts3", group(b"Allow: /a%2F", b"Disallow: /a%2Fb"), "/a%2Fb", DENY),
    ("S.escapeCounts3b", group(b"Allow: /a%2Fb", b"Disallow: /a%2F*"), "/a%2Fb", AMBIGUOUS),
    ("S.nonAsciiCounts", group(b"Allow: /\xd0\xb6", b"Disallow: /%D0%B6x"), "/" + b"\xd0\xb6".decode() + "x", DENY),
    ("RFC5.1a", RFC_GROUPS, "/a/b.gif", DENY),
    ("RFC5.1b", RFC_GROUPS, "/publications/x", ALLOW),
    ("RFC5.1c", RFC_GROUPS, "/example/x", DENY),
    ("RFC5.1d", RFC_GROUPS, "/example/page.html", ALLOW, "foobot/1.0"),
    ("RFC5.1e", RFC_GROUPS, "/example/allowed.gif", ALLOW, "foobot/1.0"),
    ("RFC5.1f", RFC_GROUPS, "/x", DENY, "foobot/1.0"),
    ("RFC5.1g", RFC_GROUPS, "/example/page.html", DENY, "bazbot/1.0"),
    ("RFC5.1h", RFC_GROUPS, "/x.gif", ALLOW, "quxbot/1.0"),
    ("RFC5.2a", RFC_PREFIX, "/example/page/disallowed.gif", DENY, "foobot/1.0"),
    ("RFC5.2b", RFC_PREFIX, "/example/page/x", ALLOW, "foobot/1.0"),
    ("T.query", group(b"Disallow: /books/author.php?id="), "/books/author.php?id=7&page=1", DENY),
    ("T.fragment", group(b"Disallow: /a$"), "https://h.test/a#frag", DENY),
    ("T.emptyPath", group(b"Disallow: /$"), "https://h.test", DENY),
    ("T.queryOnly", group(b"Disallow: /?x"), "https://h.test?x=1", DENY),
    ("T.robots", group(b"Disallow: /"), "/robots.txt", ALLOW),
    ("T.robotsCase", group(b"Disallow: /"), "/ROBOTS.TXT", DENY),
    ("T.trailingQ", group(b"Disallow: /a?$"), "/a?", DENY),
    ("T.robotsEnc", group(b"Disallow: /"), "/robots%2Etxt", ALLOW),
    ("T.robotsQuery", group(b"Disallow: /"), "/robots.txt?x=1", ALLOW),
]

DECISION_CONTROLS = [
    ("P1", group(b"Disallow: /admin/", b"Disallow: /search", b"Allow: /"), "/books/printit.php?tid=1234", ALLOW),
    ("P2", group(b"Disallow: /admin/", b"Disallow: /search", b"Allow: /"), "/%D0%BA%D0%BD%D0%B8%D0%B3%D0%B8/1.pdf", ALLOW),
    ("P3", group(b"Disallow: /*?sort=", b"Disallow: /*.php$"), "/books/printit.php?tid=1", ALLOW),
    ("P4", group(b"Disallow: /a", b"Allow: /a/b"), "/a/b/c", ALLOW),
    ("P5", b"User-agent: *\nDisallow: /\nUser-agent: LearnUkrainianBot\nDisallow: /private\n", "/public?id=7", ALLOW),
    ("P6", b"User-agent: learn-ukrainian-sum\nAllow: /\nUser-agent: *\nDisallow: /\n", "/?word=%D0%BA%D1%96%D1%82&page=0", ALLOW, SUM_HEADER),
    ("P7", group(b"Disallow: /foo/bar?baz=https%3A%2F%2Ffoo.bar"), "/foo/bar?baz=quz", ALLOW),
    ("P8", group(b"Disallow: /caf%C3%A9"), "/cafe", ALLOW),
    ("P9", group(b"Disallow: /*/print/"), "/a/%D0%BA/", ALLOW),
    ("P10", group(b"Disallow: /private", b"Allow: /", b"Allow: /pub\xff"), "/public", ALLOW),
    ("P11", b"User-agent: Googlebot\nDisallow: /\nUser-agent: *\nAllow: /\n", "/x", ALLOW),
    ("P12", b"Allow: /x\nUser-agent: *\nDisallow: /y\n", "/x", ALLOW),
    ("P13", group(b"Disallow: /"), "/robots.txt?x=1", ALLOW),
    ("P14", group(b"Disallow: /p", b"Allow: /p"), "/p", ALLOW),
    # P15 is a robots transport status, tested separately on every D helper.
    ("B1a", b"User-agent: learn-ukrainian-sum20\nDisallow: /word\nUser-agent: *\nAllow: /\n", "/word/x", UNRESOLVED, SUM_HEADER),
    ("B1b", b"User-agent: learn\nDisallow: /\nUser-agent: *\nAllow: /\n", "/x", UNRESOLVED),
    ("B1c", b"User-agent: LearnUkrainianBot/1.0\nAllow: /\nUser-agent: *\nDisallow: /\n", "/x", UNRESOLVED),
    ("B1d", b"User-agent: learn-ukrainian-sum\nDisallow: /word\n", "/word/x", DENY, SUM_HEADER),
    ("B1e", b"User-agent: *bot\nDisallow: /\n", "/x", UNRESOLVED),
    ("B1f", b"User-agent:\nDisallow: /\n", "/x", UNRESOLVED),
    ("B2a", group(b"Disallow: /foo/bar?baz=https%3A%2F%2Ffoo.bar"), "/foo/bar?baz=https://foo.bar", AMBIGUOUS),
    ("B2b", group(b"Disallow: /a/b"), "/a%2Fb", AMBIGUOUS),
    ("B2c", group(b"Disallow: /a%2Fb"), "/a/b", AMBIGUOUS),
    ("B2d", group(b"Disallow: /s?q=a%3Db"), "/s?q=a=b", AMBIGUOUS),
    ("B2e", group(b"Disallow: /a%2Fb"), "/a%2fb", DENY),
    ("B3a", group(b"Disallow: /private", b"Allow: /private/\xff"), "/private/%FF", DENY),
    ("B3b", group(b"Disallow: /private/\xff"), "/public", UNRESOLVED),
    ("B3c", group(b"Disallow: /\xea\xed\xe8\xe3\xe8"), "/%D0%BA%D0%BD%D0%B8%D0%B3%D0%B8", UNRESOLVED),
    ("B3d", group(b"Disallow: /\xff"), "/%EF%BF%BD", UNRESOLVED),
    ("B3e", b"User-agent: *\nDisallow /a\n", "/a", UNRESOLVED),
    ("B3f", group(b"Disallow: private"), "/private", UNRESOLVED),
    ("B3g", group(b"Disallow: /a%"), "/a%2F", UNRESOLVED),
    ("B4a", group(b"Disallow: /*2F"), "/a%2F", AMBIGUOUS),
    ("B4b", group(b"Disallow: /*84"), "/x/%E3%83%84", AMBIGUOUS),
    ("B4c", group(b"Disallow: /*%2F"), "/a%2F", DENY),
    ("T1", group(b"Disallow: *", b"Allow: /"), "/x", AMBIGUOUS),
    ("X1", b"#" + b"x" * 512000, "/x", UNRESOLVED),
    ("X2", b"\xff\xfeU\x00s\x00e\x00r\x00", "/x", UNRESOLVED),
]
DISCLOSED_SEVEN = [
    ("prior1", group(b"Disallow: /foo/bar/baz"), "/foo/bar/%62%61%7A", DENY),
    ("prior2", group(b"Disallow: /foo/bar/%62%61%7A"), "/foo/bar/baz", DENY),
    ("prior3", group(b"Disallow: /path/file-with-a-%2A.html"), "/path/file-with-a-*.html", DENY),
    ("prior4", group(b"Disallow: /path/foo-%24"), "/path/foo-$", DENY),
    ("prior5", group(b"Disallow: /a%2Fb"), "/a/b", AMBIGUOUS),
    ("prior6", group(b"Disallow: /path/*.html"), "/path/file.html", DENY),
    ("prior7", group(b"Disallow: /caf%C3%A9"), "/caf%c3%a9", DENY),
]
ADMISSION_CONTROLS = [
    ("orphan-deny", b"Disallow: /private\nUser-agent: other\nAllow: /\n", "/private", DENY),
    ("orphan-malformed", b"Disallow /private\nUser-agent: other\nAllow: /\n", "/public", UNRESOLVED),
    ("ignored-malformed", b"User-agent: Googlebot\nDisallow: /bad%\nUser-agent: *\nAllow: /\n", "/public", ALLOW),
    ("missing-agent-colon", b"User-agent LearnUkrainianBot\nAllow: /\n", "/robots.txt", UNRESOLVED),
    ("utf32be", b"\x00\x00\xfe\xff", "/robots.txt", UNRESOLVED),
    ("utf16be", b"\xfe\xff", "/robots.txt", UNRESOLVED),
    ("malformed-allow-slash", group(b"Disallow: /", b"Allow: public"), "/public", DENY),
    ("malformed-allow-percent", group(b"Disallow: /", b"Allow: /public%"), "/public%25", DENY),
    ("malformed-allow-dollar", group(b"Disallow: /", b"Allow: /public$x"), "/public$x", DENY),
    ("malformed-allow-colon", b"User-agent: *\nDisallow: /\nAllow /public\n", "/public", UNRESOLVED),
    ("malformed-allow-ctl", group(b"Disallow: /", b"Allow: /public\x7f"), "/public%7F", DENY),
    ("misspelled-record", b"Usr-agent: *\nDisalow: /\n", "/public", ALLOW),
    ("all-equivalent-ties", group(b"Disallow: /p", b"Disallow: /%70", b"Allow: /p"), "/p", ALLOW),
    ("mixed-ties", group(b"Disallow: *", b"Disallow: /", b"Allow: /"), "/p", AMBIGUOUS),
    ("top-allow-only", group(b"Allow: /p", b"Disallow: /"), "/p", ALLOW),
    ("anchor-non-equivalent", group(b"Allow: /a$", b"Disallow: /a*"), "/a", AMBIGUOUS),
]


@pytest.mark.parametrize("module", MODULES)
@pytest.mark.parametrize("case", LEGACY_CONTROLS + DECISION_CONTROLS + DISCLOSED_SEVEN + ADMISSION_CONTROLS, ids=lambda row: row[0])
def test_complete_permission_contract(module, case, monkeypatch):
    _id, body, target, expected, *headers = case
    header = headers[0] if headers else module.USER_AGENT
    monkeypatch.setattr(module, "USER_AGENT", header)
    url = target if target.startswith(("http://", "https://")) else "https://h.test" + target
    origin = "https://h.test"
    state = module._robots_parse(body, header)
    module._robots_states[origin] = state
    if expected == ALLOW:
        module._robots_check_target(url)
        assert module._access_stopped is False
    else:
        with pytest.raises(module.AccessStopped, match=expected):
            module._robots_check_target(url)
        assert module._access_stopped is True
        with pytest.raises(module.AccessStopped):
            module._robots_check_target("https://other.test/robots.txt")


def test_disclosed_control_denominators():
    assert len(LEGACY_CONTROLS) == 113
    assert len(DISCLOSED_SEVEN) == 7
    assert len([row for row in DECISION_CONTROLS if row[0].startswith("P")]) == 14
    assert len([row for row in DECISION_CONTROLS if not row[0].startswith("P")]) == 24


# Handwritten disclosed controls for the adopted structural rule, not held-outs.
N1_CONTROLS = [
    ("V1a", group(b"Disallow: /private"), "/public", ALLOW),
    ("V1b", group(b"Disallow: /private"), "/private", DENY),
    ("V2", group(b"  Disallow  :  /private"), "/private", DENY),
    ("V3", group(b"\tDISALLOW\t:/private"), "/private", DENY),
    ("V4a", group(b"Disallow: /private?x=a:b"), "/private?x=a:b", DENY),
    ("V4b", group(b"Disallow: /private?x=a:b"), "/public", ALLOW),
    ("V5", b"User-agent :  *\nAllow : /\nDisallow: /private\n", "/public", ALLOW),
    ("V6", group(b"Disallow:"), "/x", ALLOW),
    ("N1a", group(b"Disallow /private?x=a:b"), "/private?x=a:b", UNRESOLVED),
    ("N1b", group(b"Disallow /private?x=a:b"), "/public", UNRESOLVED),
    ("N1c", group(b"Disallow /private"), "/public", UNRESOLVED),
    ("N1d", group(b"  disallow\t/a:b"), "/public", UNRESOLVED),
    ("N1e", group(b"Disallow /p # note: x"), "/public", UNRESOLVED),
    ("N1f", group(b"Allow: /", b"User-agent learnukrainianbot (+https://example.org/bot)", b"Disallow: /"), "/x", UNRESOLVED),
    ("N1g", group(b"Disallow /private?x=a:b", b"User-agent: Googlebot", b"Allow: /"), "/x", UNRESOLVED),
    ("N1h", b"User-agent: Googlebot\nDisallow /x:y\nUser-agent: *\nAllow: /\n", "/x", UNRESOLVED),
    ("N1i", group(b"Allow /public?a:b", b"User-agent: Googlebot", b"Disallow: /"), "/x", UNRESOLVED),
    ("N1i0", group(b"Allow /public", b"User-agent: Googlebot", b"Disallow: /"), "/x", UNRESOLVED),
    ("N1j", group(b"Crawl-delay 5 x:y", b"User-agent: Googlebot", b"Disallow: /"), "/x", UNRESOLVED),
    ("N1j0", group(b"Crawl-delay 5", b"User-agent: Googlebot", b"Disallow: /"), "/x", UNRESOLVED),
    ("N1k", group(b"Disallow: /", b"Allow /pub:lic"), "/pub:lic", UNRESOLVED),
    ("N1l", group(b"User-agent *:", b"Disallow: /p"), "/x", UNRESOLVED),
    ("L1", group(b"Disallowance: /x"), "/x", ALLOW),
    ("L2", group(b"X-Disallow: /x"), "/x", ALLOW),
    ("L3", group(b"Disallow-Extra: /x"), "/x", ALLOW),
    ("L4", group(b"Disallow_v2: /x"), "/x", ALLOW),
    ("L5", group(b"Sitemap: https://example.org/s.xml", b"Host: example.org", b"Clean-param: ref /a"), "/x", ALLOW),
    ("L6", b"User-agent: Googlebot\nDisallow: /\nUseragent: *\nDisallow: /private\n", "/private", ALLOW),
    ("L7", b"User-agent: Googlebot\nDisallow: /\nUser agent: *\nDisallow: /private\n", "/private", ALLOW),
    ("G1", group(b"Disallow/private"), "/private", UNRESOLVED),
    ("G2", group(b"Disallow/private:x"), "/private", UNRESOLVED),
    ("G3", group(b"Disallow;/private"), "/private", UNRESOLVED),
    ("G4", group(b"Disallow=/private"), "/private", UNRESOLVED),
    ("G5", group(b"Disallow\x0b/private"), "/private", UNRESOLVED),
    ("G6", group(b"Disallow\x0b: /private"), "/private", UNRESOLVED),
    ("G7", group(b"\x0bDisallow: /private"), "/private", UNRESOLVED),
    ("G8", group(b"Disallow\xc2\xa0/private"), "/private", UNRESOLVED),
    ("G9", group(b"Disallow2: /x"), "/public", UNRESOLVED),
    ("G10", group(b"\xe2\x80\x8bDisallow: /private"), "/private", ALLOW),
    ("G11", group(b"Disallow: /", b"Allow/"), "/x", UNRESOLVED),
    ("C1", group(b"dIsAlLoW /p:x"), "/public", UNRESOLVED),
    ("C2a", group(b"DISALLOW: /P"), "/P", DENY),
    ("C2b", group(b"DISALLOW: /P"), "/p", ALLOW),
    ("C3", group(b"Disallow /p\x01:x"), "/public", UNRESOLVED),
    ("C4", group(b"Disallow: /p\x01"), "/public", UNRESOLVED),
    ("C5", group(b"# Disallow /p:x"), "/p:x", ALLOW),
    ("C6", group(b"Disallow /\xd0\xba:x"), "/public", UNRESOLVED),
    ("C7", group(b"Crawl-delay 5 x:y"), "/x", UNRESOLVED),
    ("C8", b"Disallow /private?x=a:b\nUser-agent: *\nAllow: /\n", "/public", UNRESOLVED),
    ("C9", b"Allow /x:y\nUser-agent: *\nDisallow: /y\n", "/x", UNRESOLVED),
    ("C10", group(b"Disallow :/p"), "/p", DENY),
    ("C11", group(b"Disallow : x:/p"), "/public", UNRESOLVED),
    ("C12", group(b"Disallow x:"), "/public", UNRESOLVED),
    ("D1", group(b"Crawl-delay: 5"), "/x", ALLOW),
    ("D2", group(b"Allow"), "/x", UNRESOLVED),
    ("C13", b"User-agent: learnukrainianbot\nDisallow /x:y\nUser-agent: *\nAllow: /\n", "/public", UNRESOLVED),
]
N1_BOUNDARY_CONTROLS = [
    ("ff-leading", group(b"\x0cAllow: /x"), "/x", UNRESOLVED),
    ("ff-delimiter", group(b"Disallow\x0c: /x"), "/public", UNRESOLVED),
    ("mixed-leading", group(b" \t\x0b\x0cCrawl-delay: 5"), "/x", UNRESOLVED),
    ("orphan-agent", b"User-agent/Googlebot\nUser-agent: *\nAllow: /\n", "/x", UNRESOLVED),
    ("orphan-delay", b"Crawl-delay=5\nUser-agent: *\nAllow: /\n", "/x", UNRESOLVED),
    ("unknown-group-run", group(b"Disallow-Extra /x", b"User-agent: Googlebot", b"Disallow: /x"), "/x", DENY),
    ("empty-identifier", group(b" : /x", b"123: /x"), "/x", ALLOW),
    ("bom-cr-lf", b"\xef\xbb\xbfUser-agent:\t*\rAllow :\t/\r\nDisallow:\t/private\n", "/public", ALLOW),
    ("middle-bom", group(b"\xef\xbb\xbfDisallow: /x"), "/x", ALLOW),
    ("nbsp-leading", group(b"\xc2\xa0Disallow: /x"), "/x", ALLOW),
    ("value-ff-allow", group(b"Disallow: /", b"Allow: /\x0c"), "/x", DENY),
    ("ignored-unknown-ff", group(b"\x0cUnknown: /x"), "/x", ALLOW),
]


def test_n1_disclosed_denominator():
    assert len(N1_CONTROLS) == 56
    assert len({row[0] for row in N1_CONTROLS}) == 56


@pytest.mark.parametrize("case", N1_CONTROLS + N1_BOUNDARY_CONTROLS, ids=lambda row: row[0])
def test_n1_structural_recognition_and_global_transport_stop(server, case):
    import os
    case_id, body, target, expected = case
    module = server.module
    server.robots = body
    parsed = module._robots_parse(body, module.USER_AGENT)
    assert parsed["unresolved"] is (expected == UNRESOLVED)
    if case_id == "D1":
        assert parsed["delay"] == 5
    url = "https://source.test" + target
    if expected == ALLOW:
        assert server.fetch(url) == NORMAL.decode()
        assert not module._access_stopped
        assert [call[1] for call in server.source_calls()] == [url]
    else:
        with pytest.raises(module.AccessStopped, match=expected):
            server.fetch(url)
        assert module._access_stopped
        assert server.source_calls() == []
        before = list(server.calls)
        for followup in (url, "https://other.test/robots.txt", "https://other.test/public"):
            with pytest.raises(module.AccessStopped):
                server.fetch(followup)
        assert server.calls == before
    if root := os.environ.get("LU_PERMISSION_EVIDENCE_DIR"):
        Path(root, f"n1-{module.__name__}-{case_id}.json").write_text(json.dumps({
            "id": case_id, "body_hex": body.hex(), "target": target,
            "expected": expected, "unresolved": parsed["unresolved"],
            "latched": module._access_stopped, "requests": server.calls,
            "not_held_out": True,
        }, indent=2))


@pytest.mark.parametrize("module", MODULES)
@pytest.mark.parametrize("header,token", [
    ("LearnUkrainianBot/1.0", b"learnukrainianbot"),
    ("learn-ukrainian-word-atlas/1.0", b"learn-ukrainian-word-atlas"),
    ("learn-ukrainian-ulp/1.0", b"learn-ukrainian-ulp"),
    (SUM_HEADER, b"learn-ukrainian-sum"),
    ("learn-ukrainian-sum20-ingest/1.0", b"learn-ukrainian-sum"),
    ("_BOT-name123/1.0", b"_bot-name"),
])
def test_header_derived_product_and_exact_group_use_same_token(module, header, token):
    assert module._robots_token(header) == token
    assert token in header.lower().encode()
    body = b"User-agent: " + token + b"\nCrawl-delay: .75\nDisallow: /private\nUser-agent: *\nCrawl-delay: 99\nDisallow: /\n"
    state = module._robots_parse(body, header)
    assert state == {"unresolved": False, "delay": .75, "rules": [(False, b"/private")]}


@pytest.mark.parametrize("header", ["", "123Bot/1", "/Bot", " Bot"])
def test_empty_token_stops_before_any_transport(server, monkeypatch, header):
    monkeypatch.setattr(server.module, "USER_AGENT", header)
    if server.module is textbook:
        monkeypatch.setitem(textbook.HEADERS, "User-Agent", header)
    with pytest.raises(server.module.AccessStopped, match="robots_configuration"):
        server.fetch("https://source.test/page")
    assert server.calls == []


@pytest.mark.parametrize("module", MODULES)
@pytest.mark.parametrize("state", [None, {"unresolved": True, "rules": [], "delay": 0}])
def test_missing_and_unresolved_state_precede_robots_exception(module, state):
    module._robots_states["https://source.test"] = state
    with pytest.raises(module.AccessStopped, match=UNRESOLVED):
        module._robots_check_target("https://source.test/robots.txt?x=1")


def position_set_match(raw, target, reading):
    """Seeded independent matcher mechanics, deliberately not a normative oracle."""
    unreserved = set(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")
    reserved = set(b":/?#[]@!&'()+,;=")
    def units(data, is_rule):
        result = []
        anchor = is_rule and data.endswith(b"$")
        if anchor:
            data = data[:-1]
        i = 0
        while i < len(data):
            b = data[i]
            if b == 37 and i + 2 < len(data) and all(c in b"0123456789abcdefABCDEF" for c in data[i + 1:i + 3]):
                b = int(data[i + 1:i + 3], 16)
                encoded = b not in unreserved
                i += 3
            else:
                i += 1
                if is_rule and b == 42:
                    result.append(None)
                    continue
                encoded = b not in unreserved and (reading == 2 or b not in reserved)
            if encoded:
                result.extend(list(f"%{b:02X}") if reading == 2 else [("octet", b)])
            else:
                result.append(chr(b))
        return result, anchor
    pattern, anchored = units(raw, True)
    text, _anchor = units(target, False)
    positions = {0}
    for atom in pattern:
        if atom is None:
            positions = {p for start in positions for p in range(start, len(text) + 1)}
        else:
            positions = {p + 1 for p in positions if p < len(text) and text[p] == atom}
        if not positions:
            return False
    return len(text) in positions if anchored else bool(positions)


@pytest.mark.parametrize("module", MODULES)
def test_seeded_two_reading_greedy_vs_position_set_mechanics(module):
    import random
    rng = random.Random(8999)
    alphabet = [b"a", b"b", b"/", b"%2F", b"%61", b"*", b"$", b"\xd0\xb6", b"%2A", b"?", b"%zz", b"%84"]
    for _ in range(20000):
        rule = b"/" + b"".join(rng.choices(alphabet, k=rng.randrange(8)))
        target = b"/" + b"".join(rng.choices(alphabet, k=rng.randrange(10)))
        for reading in (1, 2):
            pattern, anchor, _weight = module._robots_canonical(rule, rule=True, reading=reading)
            canonical = module._robots_canonical(target, rule=False, reading=reading)[0]
            assert module._robots_match(pattern, anchor, canonical) == position_set_match(rule, target, reading), (rule, target, reading)


@pytest.mark.parametrize("module", MODULES)
@pytest.mark.parametrize("shape", ["many-rules", "many-wildcards", "long-needles", "escape-flood", "over-limit"])
def test_both_readings_each_hostile_shape_under_five_seconds(module, shape):
    import time
    bodies = {
        "many-rules": b"User-agent: *\n" + b"Disallow: /*a*a*a*a*b\n" * (512000 // 22),
        "many-wildcards": group(b"Disallow: /" + b"*a" * ((512000 - 40) // 2) + b"b"),
        "long-needles": b"User-agent: *\n" + (b"Disallow: /*" + b"a" * 98 + b"b\n") * (512000 // 103),
        "escape-flood": group(b"Disallow: /" + b"%zz%E3" * (512000 // 7)),
        "over-limit": group(b"Disallow: /" + b"x" * (2 * 512000)),
    }
    start = time.perf_counter()
    state = module._robots_parse(bodies[shape], module.USER_AGENT)
    module._robots_states["https://h.test"] = state
    if shape in {"escape-flood", "over-limit", "long-needles"}:
        with pytest.raises(module.AccessStopped, match=UNRESOLVED):
            module._robots_check_target("https://h.test/" + "a" * 8000)
    else:
        module._robots_check_target("https://h.test/" + "a" * 8000)
    elapsed = time.perf_counter() - start
    assert elapsed < 5, (shape, elapsed)
    import os
    if root := os.environ.get("LU_PERMISSION_EVIDENCE_DIR"):
        Path(root, f"hostile-{module.__name__}-{shape}.json").write_text(json.dumps({"shape": shape, "seconds": elapsed, "both_readings": True, "under_five_seconds": elapsed < 5}))


@pytest.mark.parametrize("status", [200, 201, 204, 206, 400, 401, 404, 410, 418, 451, 499])
def test_robots_2xx_parse_and_other_4xx_allow_all_P15(server, status):
    body = group(b"Disallow: /private", b"Crawl-delay: 3.25")
    server.responses["https://source.test/robots.txt"] = [Response(body, status)]
    server.fetch("https://source.test/public")
    if status < 300:
        assert server.module._robots_states["https://source.test"]["rules"] == [(False, b"/private")]
        assert server.calls[-1][2] - server.calls[0][2] >= 3.25
    else:
        assert server.module._robots_states["https://source.test"] == {"unresolved": False, "rules": [], "delay": 0}
    assert len(server.source_calls()) == 1


@pytest.mark.parametrize("status,headers,body,reason", [
    (403, {}, b"Forbidden", None), (429, {}, b"Rate limit", None),
    (200, {"Cf-Mitigated": "challenge"}, b"", None),
    (503, {}, CHALLENGE, None),
    (500, {}, b"Ordinary failure", "robots_unreachable"),
    (503, {}, b"Ordinary failure", "robots_unreachable"),
    (599, {}, b"Ordinary failure", "robots_unreachable"),
    (301, {}, b"", "robots_unreachable"),
    (302, {}, b"", "robots_unreachable"),
    (304, {"Location": "/later"}, b"", "robots_unreachable"),
    (0, {}, b"", "robots_unreachable"),
    (200, {}, group(b"Disallow: /"), DENY),
    (200, {}, group(b"Disallow: /bad\xff"), UNRESOLVED),
    (200, {}, group(b"Disallow: *", b"Allow: /"), AMBIGUOUS),
])
def test_robots_failure_latches_with_no_source_or_within_run_retry(server, status, headers, body, reason):
    server.responses["https://source.test/robots.txt"] = [Response(body, status, headers)]
    with pytest.raises(server.module.AccessStopped, match=reason):
        server.fetch("https://source.test/page")
    assert len(server.calls) == 1 and not server.source_calls()
    for url in ("https://source.test/page2", "https://other.test/page", "https://source.test/robots.txt"):
        with pytest.raises(server.module.AccessStopped):
            server.fetch(url)
    assert len(server.calls) == 1


def test_robots_network_error_installs_unresolved_state_before_fetch(server, monkeypatch):
    def fail(*_args, **_kwargs):
        assert server.module._robots_states["https://source.test"] is None
        server.calls.append(("get", "https://source.test/robots.txt", 0, {}, {}))
        if server.module is textbook:
            raise requests.ConnectionError("fixture")
        if server.module is zno:
            raise urllib.error.URLError("fixture")
        raise RuntimeError("curl fixture timeout")
    if server.module is textbook:
        monkeypatch.setattr(textbook.requests, "get", fail)
    elif server.module is zno:
        monkeypatch.setattr(zno, "_open", fail)
    else:
        monkeypatch.setattr(ukrlib, "_curl_response", fail)
    with pytest.raises(server.module.AccessStopped, match="robots_unreachable"):
        server.fetch("https://source.test/page")
    with pytest.raises(server.module.AccessStopped):
        server.fetch("https://source.test/page2")
    assert len(server.calls) == 1 and server.source_calls() == []


def test_robots_curl_nonzero_is_unreachable(monkeypatch, tmp_path, isolate_policy):
    server = Server(monkeypatch, ukrlib, tmp_path, isolate_policy)
    def failed(url):
        server.calls.append(("get", url, 0, {}, {}))
        return 200, {}, b"User-agent: *\nAllow: /", 7
    monkeypatch.setattr(ukrlib, "_curl_response", failed)
    with pytest.raises(ukrlib.AccessStopped, match="robots_unreachable"):
        server.fetch("https://source.test/page")
    assert len(server.calls) == 1


@pytest.mark.parametrize("hops", [0, 1, 10, 11])
def test_robots_redirect_hops_and_initial_origin_binding(server, hops):
    start = "https://source.test/robots.txt"
    urls = [start] + [f"https://robots.test/redirect-{i}" for i in range(hops)]
    for url, following in pairwise(urls):
        server.responses[url] = [Response(b"", 302, {"Location": following})]
    server.responses[urls[-1]] = [Response(group(b"Disallow: /private", b"Crawl-delay: 4.25"))]
    if hops > 10:
        with pytest.raises(server.module.AccessStopped, match="robots_unreachable"):
            server.fetch("https://source.test/public")
        assert not any(c[1] == "https://source.test/public" for c in server.calls)
        assert [c[1] for c in server.calls] == urls[:-1]
    else:
        server.fetch("https://source.test/public")
        assert [c[1] for c in server.calls] == [*urls, "https://source.test/public"]
        assert set(server.module._robots_states) == {"https://source.test"}
        assert server.module._robots_delays["https://source.test"] == 4.25
        with pytest.raises(server.module.AccessStopped, match=DENY):
            server.fetch("https://source.test/private")
        assert len(server.calls) == len(urls) + 1


@pytest.mark.parametrize("cross_origin", [False, True])
@pytest.mark.parametrize("hops", [8, 9])
def test_content_redirect_limit_is_eight_hops(server, hops, cross_origin):
    urls = ["https://source.test/start"] + [f"https://{'other' if cross_origin else 'source'}.test/hop-{i}" for i in range(hops)]
    for url, following in pairwise(urls):
        server.responses[url] = [Response(b"", 307, {"Location": following})]
    if hops == 8:
        server.fetch(urls[0])
    else:
        with pytest.raises((requests.TooManyRedirects, urllib.error.URLError, RuntimeError)):
            server.fetch(urls[0])
    assert [c[1] for c in server.source_calls()] == urls[:9]
    assert server.module._access_stopped is False


@pytest.mark.parametrize("cross_origin", [False, True])
def test_content_redirect_permission_stops_before_denied_destination(server, cross_origin):
    denied = f"https://{'other' if cross_origin else 'source'}.test/private"
    server.robots = group(b"Disallow: /private")
    server.responses["https://source.test/start"] = [Response(b"", 302, {"Location": denied})]
    with pytest.raises(server.module.AccessStopped, match=DENY):
        server.fetch("https://source.test/start")
    assert [c[1] for c in server.source_calls()] == ["https://source.test/start"]
    assert len(server.calls) == (3 if cross_origin else 2)


@pytest.mark.parametrize("params,target", [
    ({"word": "a/b", "page": 0}, b"/?word=a%2Fb&page=0"),
    ({"confirm": "yes", "id": "ID"}, b"/?confirm=yes&id=ID"),
])
def test_textbook_permission_uses_exact_prepared_query(monkeypatch, tmp_path, isolate_policy, params, target):
    srv = Server(monkeypatch, textbook, tmp_path, isolate_policy)
    srv.robots = group(b"Disallow: " + target)
    with pytest.raises(textbook.AccessStopped, match=DENY):
        textbook._request("https://source.test", params=params)
    assert [c[1] for c in srv.calls] == ["https://source.test/robots.txt"]


def test_actual_textbook_header_controls_token_not_module_constant(monkeypatch, tmp_path, isolate_policy):
    srv = Server(monkeypatch, textbook, tmp_path, isolate_policy)
    header = "SpecificBot/1.0 (+" + CONTACT + ")"
    monkeypatch.setitem(textbook.HEADERS, "User-Agent", header)
    srv.robots = b"User-agent: specificbot\nDisallow: /private\nUser-agent: *\nDisallow: /\n"
    srv.fetch("https://source.test/public")
    assert all(c[3]["User-Agent"] == header for c in srv.calls)
    with pytest.raises(textbook.AccessStopped, match=DENY):
        srv.fetch("https://source.test/private")
    assert len(srv.source_calls()) == 1


@pytest.mark.parametrize("floor", [.3, .5, 2.0])
def test_fractional_max_delay_fake_clock(server, floor):
    server.robots = group(b"Crawl-delay: .75", b"Crawl-delay: 1.25")
    server.fetch("https://source.test/first")
    origin = "https://source.test"
    before = server.clock.now
    server.module._wait_for_request(origin + "/second", floor)
    assert server.clock.now - before == max(floor, 1.25)


@pytest.mark.parametrize("site", ["listing", "shkola-get", "shkola-post", "pdf", "drive-initial", "drive-confirmation", "zno", "ukrlib"])
@pytest.mark.parametrize("denied", [False, True])
def test_all_eight_actual_request_sites_permission_ledger(monkeypatch, tmp_path, isolate_policy, site, denied):
    module = zno if site == "zno" else ukrlib if site == "ukrlib" else textbook
    srv = Server(monkeypatch, module, tmp_path, isolate_policy)
    page = b'<title>Author 6 \xd0\xba\xd0\xbb\xd0\xb0\xd1\x81</title><form action="/download"><button name="vslink" value="A">PDF</button></form>'
    payload = b"%PDF-1.7\nfixture"
    expected_before = []
    if site == "listing":
        url = f"{textbook.BASE_URL}/book.html"
        srv.responses[url] = [Response(page)]
        def call():
            return textbook.extract_pdf_links("book", author="Author", grade=6)
    elif site in {"shkola-get", "shkola-post"}:
        url = "https://shkola.in.ua/book" if site == "shkola-get" else "https://shkola.in.ua/download"
        srv.responses["https://shkola.in.ua/book"] = [Response(page)]
        srv.responses["https://shkola.in.ua/download"] = [Response(b"", 303, {"Location": "/book.pdf"})]
        srv.responses["https://shkola.in.ua/book.pdf"] = [Response(payload)]
        def call():
            return textbook.extract_shkola_pdf_links("https://shkola.in.ua/book", author="Author", grade=6)
        if site == "shkola-post":
            expected_before = ["https://shkola.in.ua/book"]
    elif site == "pdf":
        url = "https://source.test/book.pdf"
        srv.responses[url] = [Response(payload)]
        def call():
            return textbook.download_pdf(url, tmp_path / "new.pdf", retained_store=tmp_path)
    elif site.startswith("drive"):
        url = "https://docs.google.com/uc"
        srv.responses[url] = [Response(payload)]
        if site == "drive-confirmation":
            srv.responses[url] = [Response(b'<form><input name="confirm" value="yes"></form>', headers={"Content-Type": "text/html"}), Response(payload)]
            expected_before = [url]
        def call():
            return textbook.download_from_gdrive("ID", tmp_path / "new.pdf", retained_store=tmp_path)
    else:
        url = "https://source.test/page"
        def call():
            return srv.fetch(url)
    if denied:
        rule = (b"/uc?export=download&id=ID&confirm=yes" if site == "drive-confirmation" else urlparse(url).path.encode())
        srv.robots = group(b"Disallow: " + rule)
        with pytest.raises(module.AccessStopped, match=DENY):
            call()
        assert [c[1] for c in srv.source_calls()] == expected_before
        count = len(srv.calls)
        with pytest.raises(module.AccessStopped):
            srv.fetch("https://later.test/page")
        assert len(srv.calls) == count
        assert not list(tmp_path.rglob("*.part")) and not (tmp_path / "new.pdf").exists()
    else:
        call()
        assert url in [c[1] for c in srv.source_calls()]
        if site == "shkola-post":
            assert [c[0] for c in srv.source_calls()] == ["get", "post"]
        if site == "drive-confirmation":
            assert len(srv.source_calls()) == 2
    import os
    root = os.environ.get("LU_PERMISSION_EVIDENCE_DIR")
    if root:
        Path(root, f"request-{site}-{denied}.json").write_text(json.dumps({"site": site, "denied": denied, "requests": srv.calls}, indent=2))


def test_shared_iterator_replays_html_labelled_two_mib_pdf(monkeypatch, tmp_path, isolate_policy):
    srv = Server(monkeypatch, textbook, tmp_path, isolate_policy)
    payload = b"%PDF-1.7\n" + b"x" * (2 * 1024 * 1024 - 9)
    response = Response(payload, headers={"Content-Type": "text/html"})
    calls = []
    consumed = []
    def stream(chunk_size):
        calls.append(chunk_size)
        for offset in range(0, len(payload), 4096):
            consumed.append(offset)
            yield payload[offset:offset + 4096]
    response.iter_content = stream
    srv.responses["https://source.test/book.pdf"] = [response]
    destination = tmp_path / "new.pdf"
    assert textbook.download_pdf("https://source.test/book.pdf", destination, retained_store=tmp_path)
    assert destination.read_bytes() == payload and len(payload) == 2 * 1024 * 1024
    assert calls == [8192]
    assert consumed == list(range(0, len(payload), 4096))
    assert response.closed and not list(tmp_path.glob("*.part"))


@pytest.mark.parametrize("chunk_size", [1, 4096, 16384])
@pytest.mark.parametrize("confirmation", [False, True])
def test_drive_html_labelled_two_mib_pdf_uses_one_stream(
    monkeypatch, tmp_path, isolate_policy, chunk_size, confirmation,
):
    srv = Server(monkeypatch, textbook, tmp_path, isolate_policy)
    # Confirmation-looking PDF bytes must never cause a second request.
    prefix = b'%PDF-1.7\n<form><input name="confirm" value="spurious"></form>\n'
    payload = prefix + b"x" * (2 * 1024 * 1024 - len(prefix))
    incoming = tmp_path / "incoming.bin"
    incoming.write_bytes(payload)
    incoming_before = hashlib.sha256(incoming.read_bytes()).hexdigest()
    response = Response(incoming.read_bytes(), headers={"Content-Type": "text/html"})
    del response.content, response.text  # No eager body hydration on the PDF path.
    calls, consumed = [], []
    def stream(chunk_size):
        calls.append(chunk_size)
        for offset in range(0, len(payload), block_size):
            consumed.append(offset)
            yield payload[offset:offset + block_size]
    block_size = chunk_size
    response.iter_content = stream
    warning = Response(b'<form><input name="confirm" value="yes"></form>', headers={"Content-Type": "text/html"})
    srv.responses["https://docs.google.com/uc"] = ([warning] if confirmation else []) + [response]
    old = tmp_path / "retained.pdf"
    old.write_bytes(b"%PDF-1.7\nretained fixture")
    before = hashlib.sha256(old.read_bytes()).hexdigest()
    destination = tmp_path / "new.pdf"
    assert textbook.download_from_gdrive("ID", destination, retained_store=tmp_path)
    assert len(payload) == 2 * 1024 * 1024 and destination.read_bytes() == payload
    assert calls == [8192] and consumed == list(range(0, len(payload), block_size))
    assert len(srv.source_calls()) == (2 if confirmation else 1)
    assert old.exists() and hashlib.sha256(old.read_bytes()).hexdigest() == before
    assert hashlib.sha256(incoming.read_bytes()).hexdigest() == incoming_before
    assert response.closed and not list(tmp_path.glob(".*.part"))
    if confirmation:
        assert warning.closed and srv.source_calls()[1][4]["params"]["confirm"] == "yes"
    import os
    if root := os.environ.get("LU_PERMISSION_EVIDENCE_DIR"):
        Path(root, f"drive-f3-{block_size}-{confirmation}.json").write_text(json.dumps({
            "size": len(payload), "payload_sha256": hashlib.sha256(payload).hexdigest(),
            "retained_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
            "old_before": before, "old_after": hashlib.sha256(old.read_bytes()).hexdigest(),
            "incoming_path": str(incoming), "incoming_before": incoming_before,
            "incoming_after": hashlib.sha256(incoming.read_bytes()).hexdigest(),
            "iterator_calls": calls, "consumed_chunks": len(consumed), "requests": srv.calls,
            "closed": response.closed, "part_files": [str(p) for p in tmp_path.glob(".*.part")],
            "not_held_out": True,
        }, indent=2))


@pytest.mark.parametrize("failure", ["declared-size", "streamed-size", "stream-error"])
def test_drive_mislabeled_pdf_retention_failure_conserves_old_files(
    monkeypatch, tmp_path, isolate_policy, failure,
):
    srv = Server(monkeypatch, textbook, tmp_path, isolate_policy)
    payload = b"%PDF-1.7\n" + b"x" * 16000
    headers = {"Content-Type": "text/html"}
    if failure == "declared-size":
        headers["Content-Length"] = str(len(payload))
    response = Response(payload, headers=headers)
    calls = []
    def stream(chunk_size):
        calls.append(chunk_size)
        yield payload[:8192]
        if failure == "stream-error":
            raise OSError("interrupted PDF stream")
        yield payload[8192:]
    response.iter_content = stream
    srv.responses["https://docs.google.com/uc"] = [response]
    old = tmp_path / "retained.pdf"
    old.write_bytes(b"%PDF-1.7\nretained fixture")
    before = hashlib.sha256(old.read_bytes()).hexdigest()
    error = OSError if failure == "stream-error" else textbook.DownloadValidationError
    message = "interrupted PDF stream" if failure == "stream-error" else "response size"
    with pytest.raises(error, match=message):
        textbook.download_from_gdrive("ID", tmp_path / "new.pdf", retained_store=tmp_path, max_size_bytes=9000)
    assert calls == [8192] and len(srv.source_calls()) == 1
    assert hashlib.sha256(old.read_bytes()).hexdigest() == before
    assert response.closed and not (tmp_path / "new.pdf").exists() and not list(tmp_path.glob(".*.part"))


def test_zno_content_strict_utf8_and_robots_raw_bytes(monkeypatch, tmp_path, isolate_policy):
    server = Server(monkeypatch, zno, tmp_path, isolate_policy)
    server.responses["https://source.test/bad"] = [Response(b"\xff")]
    with pytest.raises(UnicodeDecodeError):
        server.fetch("https://source.test/bad")
    assert not server.module._access_stopped
    server.fetch("https://source.test/good")
    assert len(server.source_calls()) == 2


def test_three_retained_synthetic_inputs_fresh_conservation(monkeypatch, tmp_path, isolate_policy):
    import os
    cache, pdf, jsonl = tmp_path / "cache.html", tmp_path / "retained.pdf", tmp_path / "ukrlib-test.jsonl"
    cache.write_bytes(NORMAL)
    pdf.write_bytes(b"%PDF-1.7\nretained fixture")
    row = {"chunk_id": "kept", "text": "retained", "source_url": "https://source.test/old", "work": "kept", "author": "kept", "year": 1900, "genre": "prose", "language_period": "modern"}
    jsonl.write_text(json.dumps(row) + "\n")
    paths = [cache, pdf, jsonl]
    def snapshot():
        rows = []
        for p in paths:
            stat = p.stat()
            rows.append({"path": str(p), "size": stat.st_size, "device": stat.st_dev,
                         "inode": stat.st_ino, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
        return rows
    before = snapshot()
    srv = Server(monkeypatch, ukrlib, tmp_path, isolate_policy)
    assert zno.fetch_page_with_rate_limit("https://source.test/cache", cache) == NORMAL.decode()
    assert not textbook.download_pdf("https://source.test/pdf", pdf)
    assert not srv.calls
    monkeypatch.setattr(ukrlib, "LITERARY_DIR", tmp_path)
    monkeypatch.setattr(ukrlib, "PROGRESS_DIR", tmp_path / "progress")
    monkeypatch.setattr(ukrlib, "get_author_works", lambda _id: ([{"tid": 1, "title": "first"}, {"tid": 2, "title": "second"}], []))
    srv.robots = group(b"Disallow: /books/printit.php?tid=1")
    with pytest.raises(ukrlib.AccessStopped, match=DENY):
        ukrlib.scrape_author("test", {"id": 999, "name": "Fixture", "full_name": "Fixture", "years": "1900-1950", "genre_default": "prose", "period": "modern"})
    after = snapshot()
    assert before == after
    assert not list(tmp_path.glob("*.building")) and not list(tmp_path.glob("*.part"))
    if root := os.environ.get("LU_PERMISSION_EVIDENCE_DIR"):
        Path(root, "synthetic-conservation.json").write_text(json.dumps({"before": before, "after": after, "equal": before == after, "requests": srv.calls}, indent=2))


@pytest.mark.parametrize("module", MODULES)
def test_target_path_without_authority_and_orphan_delay(module):
    assert module._robots_target("/a;p?x=%2F#fragment") == b"/a;p?x=%2F"
    state = module._robots_parse(b"Crawl-delay: 99\nUser-agent: *\nCrawl-delay 90\n", module.USER_AGENT)
    assert state["delay"] == 0
    assert state["unresolved"] is True
    module._robots_states["https://source.test"] = state
    with pytest.raises(module.AccessStopped, match=UNRESOLVED):
        module._robots_check_target("https://source.test/public")
    assert module._access_stopped is True


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_post_redirect_method_and_query_are_checked_per_hop(monkeypatch, tmp_path, isolate_policy, status):
    srv = Server(monkeypatch, textbook, tmp_path, isolate_policy)
    start, final = "https://source.test/form", "https://other.test/result?confirmed=1"
    srv.responses[start] = [Response(b"", status, {"Location": final})]
    response = textbook._request(start, session=srv, method="post", data={"token": "fixture"}, params={"initial": "yes"})
    response.close()
    assert [c[1] for c in srv.source_calls()] == [start, final]
    following = srv.source_calls()[-1]
    assert following[0] == ("post" if status in {307, 308} else "get")
    assert "params" not in following[4]
    assert ("data" in following[4]) == (status in {307, 308})


def test_urllib_real_loopback_redirect_handler_checks_before_followup(monkeypatch, tmp_path):
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer
    seen = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass
        def do_GET(self):
            seen.append((self.path, self.headers["User-Agent"]))
            if self.path == "/robots.txt":
                body = group(b"Disallow: /private")
                status, location = 200, None
            elif self.path == "/start":
                body, status, location = b"", 302, "/private"
            else:
                body, status, location = NORMAL, 200, None
            self.send_response(status)
            if location:
                self.send_header("Location", location)
            self.end_headers()
            self.wfile.write(body)
    with HTTPServer(("localhost", 0), Handler) as httpd:
        worker = threading.Thread(target=httpd.serve_forever)
        worker.start()
        try:
            url = f"http://localhost:{httpd.server_port}"
            with pytest.raises(zno.AccessStopped, match=DENY):
                zno.fetch_page_with_rate_limit(url + "/start", tmp_path / "page")
            with pytest.raises(zno.AccessStopped):
                zno.fetch_page_with_rate_limit(url + "/later", tmp_path / "later")
            assert [path for path, _header in seen] == ["/robots.txt", "/start"]
            assert all(header == zno.USER_AGENT for _path, header in seen)
            assert not (tmp_path / "page").exists()
        finally:
            httpd.shutdown()
            worker.join(timeout=5)
            assert not worker.is_alive()


@pytest.fixture
def h_loopback(request):
    """Real HTTP request targets, with no transport mocks or external sources."""
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    servers = []

    def create(routes):
        ledger = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_GET(self):
                ledger.append((self.path, self.headers.get("User-Agent")))
                status, headers, body = routes.get(self.path, (200, {}, NORMAL))
                self.send_response(status)
                for key, value in headers.items():
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        httpd = HTTPServer(("localhost", 0), Handler)
        worker = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": .01})
        worker.start()
        servers.append((httpd, worker, ledger))
        return f"http://localhost:{httpd.server_port}", ledger

    try:
        yield create
    finally:
        h_record("loopback-" + hashlib.sha256(request.node.nodeid.encode()).hexdigest()[:16],
                 test=request.node.nodeid, ledgers=[ledger for _httpd, _worker, ledger in servers])
        for httpd, worker, _ledger in servers:
            httpd.shutdown()
            worker.join(timeout=5)
            httpd.server_close()
            assert not worker.is_alive()


def h_fetch(module, url, cache):
    if module is textbook:
        response = module._request(url, timeout=5)
        try:
            return response.content
        finally:
            response.close()
    if module is zno:
        return module.fetch_page_with_rate_limit(url, cache).encode()
    status, body, rc = module._curl_request(url)
    assert (status, rc) == (200, 0)
    return body


def h_record(name, **row):
    import os
    if root := os.environ.get("LU_PERMISSION_EVIDENCE_DIR"):
        Path(root, f"h-{name}.json").write_text(json.dumps(row, indent=2))


@pytest.mark.parametrize("target", [
    "/{public,private}/x?q={a,b}", "/book[1-2];p?x=[3-4]",
    "/public/../private/y;p?q=one", "/public/./x;p?q=two",
])
@pytest.mark.parametrize("entry", ["initial", "absolute", "relative", "robots"])
@pytest.mark.parametrize("denied", [False, True])
def test_h_curl_actual_target_equals_permission_target(
    monkeypatch, tmp_path, isolate_policy, h_loopback, target, entry, denied,
):
    from urllib.parse import urljoin

    routes = {}
    base, ledger = h_loopback(routes)
    # Relative redirects are resolved by the existing urljoin; the check must
    # match the result that curl actually sends, including params and query.
    location = base + target if entry == "absolute" else target
    actual = ukrlib._robots_target(urljoin(base + "/start", location)).decode() if entry == "relative" else target
    rule_target = actual.replace("{", "%7B").replace("}", "%7D")
    allowed_rules = b"Disallow: /blocked" if entry == "relative" and actual.startswith("/private/") else b"Disallow: /private"
    rules = group((b"Disallow: " + rule_target.encode()) if denied else allowed_rules)
    routes["/robots.txt"] = (200, {}, rules)
    if entry == "robots":
        routes["/robots.txt"] = (302, {"Location": base + target}, b"")
        routes[target] = (200, {}, group(b"Disallow: /private"))
    else:
        routes["/start"] = (302, {"Location": location}, b"")
        routes[actual] = (200, {}, NORMAL)
    checked, paced = [], []
    check, wait = ukrlib._robots_check_target, ukrlib._wait_for_request

    def observe_check(url):
        checked.append(ukrlib._robots_target(url).decode())
        check(url)

    def observe_wait(url, floor):
        wait(url, floor)
        paced.append((ukrlib._robots_target(url).decode(), isolate_policy.now))

    monkeypatch.setattr(ukrlib, "_robots_check_target", observe_check)
    monkeypatch.setattr(ukrlib, "_wait_for_request", observe_wait)
    cache = tmp_path / "body"
    if entry == "robots":
        result = h_fetch(ukrlib, base + "/public", cache)
        assert result == NORMAL
        expected, expected_checked = ["/robots.txt", target, "/public"], ["/public"]
    elif denied:
        with pytest.raises(ukrlib.AccessStopped, match=DENY):
            h_fetch(ukrlib, base + (target if entry == "initial" else "/start"), cache)
        expected = ["/robots.txt"] + ([] if entry == "initial" else ["/start"])
        expected_checked = ([] if entry == "initial" else ["/start"]) + [actual]
        other, other_ledger = h_loopback({})
        with pytest.raises(ukrlib.AccessStopped):
            h_fetch(ukrlib, other + "/later", cache)
        assert other_ledger == [] and ukrlib._access_stopped
        assert not cache.exists() and not list(tmp_path.iterdir())
    else:
        assert h_fetch(ukrlib, base + (target if entry == "initial" else "/start"), cache) == NORMAL
        expected = ["/robots.txt"] + ([] if entry == "initial" else ["/start"]) + [actual]
        expected_checked = ([] if entry == "initial" else ["/start"]) + [actual]
    assert [path for path, _ua in ledger] == expected
    assert all(ua == ukrlib.USER_AGENT for _path, ua in ledger)
    assert checked == expected_checked
    assert [path for path, _time in paced] == expected
    assert all(b[1] - a[1] >= ukrlib.DELAY_BETWEEN_PAGES - 1e-8 for a, b in pairwise(paced))
    assert all(path in checked for path in expected if path not in {"/robots.txt", target if entry == "robots" else ""})
    h_record(f"target-{entry}-{denied}-{hashlib.sha256(target.encode()).hexdigest()[:8]}",
             target=target, ledger=ledger, checked=checked, paced=paced, denied=denied, entry=entry)


@pytest.mark.parametrize("module", MODULES)
@pytest.mark.parametrize("scheme", ["dict", "ftp", "file", "data", "DiCt", "FtP", "FiLe", "DaTa", "schemeless", "relative"])
@pytest.mark.parametrize("entry", ["initial", "content-redirect", "robots-redirect"])
def test_h_http_only_before_any_destination_io(
    monkeypatch, tmp_path, isolate_policy, h_loopback, module, scheme, entry,
):
    import socket

    routes = {"/robots.txt": (200, {}, group(b"Disallow: /private"))}
    base, ledger = h_loopback(routes)
    other, other_ledger = h_loopback({})
    cache = tmp_path / "page"
    with socket.socket() as listener:
        listener.bind(("localhost", 0))
        listener.listen()
        listener.setblocking(False)
        address = f"localhost:{listener.getsockname()[1]}"
        target = f"{scheme}://{address}/x"
        if scheme == "data" or scheme == "DaTa":
            target = scheme + ":text/plain,source"
        elif scheme == "schemeless":
            target = f"//{base.split('://', 1)[1]}/public;p?x=1"
        elif scheme == "relative":
            target = "/public;p?x=1"
        supported = scheme in {"schemeless", "relative"} and entry != "initial"
        checked, paced = [], []
        check, wait = module._robots_check_target, module._wait_for_request

        def observe_check(url):
            checked.append(module._robots_target(url).decode())
            check(url)

        def observe_wait(url, floor):
            wait(url, floor)
            paced.append(module._robots_target(url).decode())

        monkeypatch.setattr(module, "_robots_check_target", observe_check)
        monkeypatch.setattr(module, "_wait_for_request", observe_wait)
        if entry == "initial":
            url, expected = target, []
        elif entry == "content-redirect":
            routes["/start"] = (302, {"Location": target}, b"")
            url, expected = base + "/start", ["/robots.txt", "/start"]
        else:
            routes["/robots.txt"] = (302, {"Location": target}, b"")
            routes["/public;p?x=1"] = (200, {}, group(b"Disallow: /private"))
            url, expected = base + "/start", ["/robots.txt"]
        if supported:
            h_fetch(module, url, cache)
            expected += ["/public;p?x=1"] + (["/start"] if entry == "robots-redirect" else [])
            assert not module._access_stopped
            assert checked == (["/start", "/public;p?x=1"] if entry == "content-redirect" else ["/start"])
        else:
            with pytest.raises(module.AccessStopped, match="robots_unreachable: unsupported scheme"):
                h_fetch(module, url, cache)
            assert module._access_stopped
            with pytest.raises(module.AccessStopped):
                h_fetch(module, other + "/later", cache)
            assert other_ledger == [] and not cache.exists()
            assert not list(tmp_path.iterdir())
            assert checked == (["/start"] if entry == "content-redirect" else [])
        assert [path for path, _ua in ledger] == expected
        assert all(ua == module.USER_AGENT for _path, ua in ledger)
        assert paced == expected
        with pytest.raises(BlockingIOError):
            listener.accept()
        h_record(f"scheme-{module.__name__}-{scheme}-{entry}",
                 ledger=ledger, checked=checked, paced=paced, unsupported=not supported,
                 destination_connections=0, second_origin_ledger=other_ledger, cache=cache.exists())


@pytest.mark.parametrize("module", MODULES)
@pytest.mark.parametrize("entry", ["initial", "same-origin", "cross-origin"])
@pytest.mark.parametrize("target", ["/ordinary;p?x=1", "/public/../private/y;p?x=1", "/public/./y;p?x=2"])
def test_h_valid_http_hops_check_actual_raw_target(
    monkeypatch, tmp_path, isolate_policy, h_loopback, module, entry, target,
):
    routes = {"/robots.txt": (200, {}, group(b"Disallow: /blocked"))}
    other_routes = dict(routes)
    base, ledger = h_loopback(routes)
    other, other_ledger = h_loopback(other_routes)
    checked, paced = [], []
    check, wait = module._robots_check_target, module._wait_for_request

    def observe_check(url):
        checked.append((urlparse(url).netloc, module._robots_target(url).decode()))
        check(url)

    def observe_wait(url, floor):
        wait(url, floor)
        paced.append((urlparse(url).netloc, module._robots_target(url).decode(), isolate_policy.now))

    monkeypatch.setattr(module, "_robots_check_target", observe_check)
    monkeypatch.setattr(module, "_wait_for_request", observe_wait)
    # Uppercase HTTP must stay usable. requests prepares dot paths; urllib
    # and the explicitly literal curl transport preserve absolute dot paths.
    destination = other if entry == "cross-origin" else base
    absolute = destination.replace("http:", "HTTP:") + target
    routes["/start"] = (302, {"Location": absolute}, b"")
    actual = target
    if module is textbook:
        actual = target.replace("/public/../", "/").replace("/public/./", "/public/")
    url = absolute if entry == "initial" else base + "/start"
    assert h_fetch(module, url, tmp_path / "page") == NORMAL
    expected = ["/robots.txt"] + ([] if entry == "initial" else ["/start"])
    if entry == "cross-origin":
        assert [path for path, _ua in ledger] == expected
        assert [path for path, _ua in other_ledger] == ["/robots.txt", actual]
    else:
        expected += [actual]
        assert [path for path, _ua in ledger] == expected and not other_ledger
    assert checked == ([] if entry == "initial" else [(urlparse(base).netloc, "/start")]) + [(urlparse(destination).netloc, actual)]
    assert all(ua == module.USER_AGENT for _path, ua in ledger + other_ledger)
    # The requests transport prepares its URL before the check and the send;
    # the existing pacer keys the original URL to the same origin.
    assert len(paced) == len(ledger) + len(other_ledger)
    for origin in {row[0] for row in paced}:
        times = [row[2] for row in paced if row[0] == origin]
        floor = .3 if module is ukrlib else 2
        assert all(b - a >= floor - 1e-8 for a, b in pairwise(times))
    assert not module._access_stopped
    h_record(f"valid-{module.__name__}-{entry}-{hashlib.sha256(target.encode()).hexdigest()[:8]}",
             ledger=ledger, other_ledger=other_ledger, checked=checked, paced=paced, target=actual)


@pytest.mark.parametrize("scheme", ["dict", "ftp", "file", "data", "DiCt", "FtP", "FiLe", "DaTa"])
def test_h_curl_protocol_restriction_blocks_low_level_io(tmp_path, scheme):
    import socket

    sentinel = tmp_path / "source"
    sentinel.write_bytes(b"private synthetic content")
    before = sentinel.stat(), sentinel.read_bytes()
    with socket.socket() as listener:
        listener.bind(("localhost", 0))
        listener.listen()
        listener.setblocking(False)
        target = f"{scheme}://localhost:{listener.getsockname()[1]}/x"
        if scheme.lower() == "file":
            target = scheme + "://" + str(sentinel)
        elif scheme.lower() == "data":
            target = scheme + ":text/plain,private"
        status, _headers, body, rc = ukrlib._curl_response(target)
        assert status == 0 and rc != 0 and body == b""
        with pytest.raises(BlockingIOError):
            listener.accept()
    assert (sentinel.stat(), sentinel.read_bytes()) == before
    h_record(f"proto-{scheme}", status=status, rc=rc, body_hex=body.hex(), connections=0,
             source_sha256=hashlib.sha256(before[1]).hexdigest())


@pytest.mark.parametrize("links,expected", [
    (["/book-2020.pdf", "/book-2024.pdf", "book.pdf"], ["book-2024.pdf"]),
    (["book.pdf"], ["book.pdf"]),
    (["https://source.test/book-2025.pdf"], ["book-2025.pdf"]),
])
def test_listing_year_selection_and_relative_links(monkeypatch, tmp_path, isolate_policy, links, expected):
    srv = Server(monkeypatch, textbook, tmp_path, isolate_policy)
    title = b'<title>Author 6 \xd0\xba\xd0\xbb\xd0\xb0\xd1\x81</title>'
    body = title + "".join(f'<a href="{link}">PDF</a>' for link in links).encode()
    srv.responses[f"{textbook.BASE_URL}/book.html"] = [Response(body)]
    result = textbook.extract_pdf_links("book", author="Author", grade=6, target_year=2025)
    assert [row["filename"] for row in result] == expected
    assert all(row["url"].startswith("https://") for row in result)


@pytest.mark.parametrize("scenario", ["invalid-host", "invalid-title", "missing-value", "no-location", "duplicate"])
def test_shkola_resolver_invalid_inputs_and_duplicate_forms(monkeypatch, tmp_path, isolate_policy, scenario):
    srv = Server(monkeypatch, textbook, tmp_path, isolate_policy)
    url = "https://shkola.in.ua/book"
    title = b'<title>Author 6 \xd0\xba\xd0\xbb\xd0\xb0\xd1\x81</title>'
    form = b'<form action="/download"><button name="vslink" value="A">PDF</button></form>'
    body = title + form
    if scenario == "invalid-host":
        with pytest.raises(ValueError, match="requires"):
            textbook.extract_shkola_pdf_links("https://other.test/book", author="Author", grade=6)
        assert not srv.calls
        return
    if scenario == "invalid-title":
        body = b"<title>Wrong</title>"
    if scenario == "missing-value":
        body = title + b'<form></form><form><input name="vslink"></form>'
    if scenario == "duplicate":
        body += form
    srv.responses[url] = [Response(body)]
    srv.responses["https://shkola.in.ua/download"] = [Response(b"", 302, {} if scenario == "no-location" else {"Location": "/book.pdf"})] * 2
    if scenario == "invalid-title":
        with pytest.raises(textbook.TitleGuardError):
            textbook.extract_shkola_pdf_links(url, author="Author", grade=6)
    else:
        result = textbook.extract_shkola_pdf_links(url, author="Author", grade=6)
        assert len(result) == (1 if scenario == "duplicate" else 0)
        if result:
            assert result[0]["url"] == "https://shkola.in.ua/book.pdf"


@pytest.mark.parametrize("html,cookies,confirm,uuid", [
    (b'<a href="https://source.test/download?confirm=yes&amp;uuid=uuid">download</a>', {}, "yes", "uuid"),
    (b'<form action="https://source.test/download"><input name="other" value="x"></form><a href="https://source.test/download?confirm=yes">download</a>', {}, "yes", None),
    (b'<span data="confirm=yes&uuid=uuid">source</span>', {}, "yes", "uuid"),
    (b'<p>ordinary</p>', {"other": "ignored", "download_warning_fixture": "cookie"}, "cookie", None),
])
def test_drive_confirmation_links_regex_and_cookie_backups(monkeypatch, tmp_path, isolate_policy, html, cookies, confirm, uuid):
    srv = Server(monkeypatch, textbook, tmp_path, isolate_policy)
    srv.cookies = cookies
    payload = b"%PDF-1.7\nfixture"
    srv.responses["https://docs.google.com/uc"] = [Response(html, headers={"Content-Type": "text/html"}), Response(payload)]
    srv.responses["https://source.test/download?confirm=yes&uuid=uuid"] = [Response(payload)]
    srv.responses["https://source.test/download?confirm=yes"] = [Response(payload)]
    srv.responses["https://source.test/download"] = [Response(payload)]
    destination = tmp_path / "new.pdf"
    assert textbook.download_from_gdrive("ID", destination, retained_store=tmp_path)
    assert destination.read_bytes() == payload
    params = srv.source_calls()[-1][4]["params"]
    assert params["confirm"] == confirm
    assert params.get("uuid") == uuid
    assert len(srv.source_calls()) == 2


@pytest.mark.parametrize("scenario", [
    "retained", "missing-source", "manual", "override", "registry", "fallback-registry", "no-pdfs",
    "success", "skipped", "alternate-fails", "fallback-pdf", "fallback-drive", "all-fail", "title-mismatch", "fallback-page-fails",
])
def test_textbook_main_retention_and_ordinary_completion_routes(monkeypatch, tmp_path, capsys, scenario):
    book = {"id": "book", "grade": 6, "slug": "book", "author": "Author", "year": 2025,
            "subject": "ukrmova", "canonical_source": "fixture", "fallback_page_urls": []}
    pdf = {"url": "https://source.test/book.pdf", "filename": "book.pdf"}
    listing = [pdf]
    calls = []
    if scenario == "missing-source":
        book["canonical_source"] = ""
    if scenario in {"manual", "registry"}:
        book["slug"] = ""
    if scenario == "manual":
        book["status"] = "needs_manual_pdf"
    if scenario == "override":
        book["override_pdfs"] = ["https://source.test/book.pdf"]
    if scenario in {"registry", "fallback-registry"}:
        book["gdrive_id"] = "ID"
    if scenario in {"no-pdfs", "fallback-registry"}:
        listing = []
    if scenario == "alternate-fails":
        pdf["alternate_downloads"] = [{"url": "https://other.test/book.pdf", "label": "mirror"}]
    if scenario in {"fallback-pdf", "fallback-drive", "all-fail", "fallback-page-fails"}:
        book["fallback_page_urls"] = ["https://shkola.in.ua/book"]
    def extract(*_args, **_kwargs):
        if scenario == "title-mismatch":
            raise textbook.TitleGuardError("fixture")
        return listing
    def fallback(*_args, **_kwargs):
        if scenario == "fallback-page-fails":
            raise ValueError("ordinary fixture")
        return [{"url": "https://fallback.test/book.pdf", "filename": "book.pdf", **({"gdrive_id": "F"} if scenario == "fallback-drive" else {})}]
    def download(url, destination, **_kwargs):
        calls.append((url, str(destination)))
        if scenario in {"alternate-fails", "fallback-pdf", "fallback-drive", "all-fail", "fallback-page-fails"} and "fallback" not in url:
            raise textbook.DownloadValidationError("ordinary fixture")
        if scenario == "all-fail":
            raise textbook.DownloadValidationError("ordinary fallback fixture")
        return scenario != "skipped"
    def drive(drive_id, destination, **_kwargs):
        calls.append((drive_id, str(destination)))
        return True
    monkeypatch.setattr(textbook, "load_selection", lambda: [book])
    monkeypatch.setattr(textbook, "find_retained_book_pdfs", lambda *_args: [tmp_path / "old.pdf"] if scenario == "retained" else [])
    monkeypatch.setattr(textbook, "extract_pdf_links", extract)
    monkeypatch.setattr(textbook, "extract_shkola_pdf_links", fallback)
    monkeypatch.setattr(textbook, "download_pdf", download)
    monkeypatch.setattr(textbook, "download_from_gdrive", drive)
    monkeypatch.setattr(textbook.sys, "argv", ["download_textbooks", "--retained-store", str(tmp_path), "--only", "6", "--ids", "book", "--all-editions"])
    textbook.main()
    output = capsys.readouterr().out
    assert "SUMMARY" in output
    skipped = scenario in {"retained", "manual", "skipped"}
    failed = scenario in {"missing-source", "no-pdfs", "alternate-fails", "all-fail", "title-mismatch", "fallback-page-fails"}
    assert f"Downloaded: {int(not skipped and not failed)}" in output
    assert f"Skipped (exist): {int(skipped)}" in output
    assert f"Failed: {int(failed)}" in output
    if calls:
        assert all(destination.endswith("grade-06/fixture.pdf") for _url, destination in calls)
    assert not list(tmp_path.rglob("*.part"))


@pytest.mark.parametrize("default,arguments", [(None, []), ("valid", []), ("valid", ["--ids", "missing"]), ("valid", ["--only", "1"])])
def test_textbook_main_default_store_and_argument_validation(monkeypatch, tmp_path, capsys, default, arguments):
    monkeypatch.setattr(textbook, "default_retained_store", lambda: tmp_path if default else None)
    monkeypatch.setattr(textbook, "load_selection", lambda: [])
    monkeypatch.setattr(textbook.sys, "argv", ["download_textbooks", *arguments])
    if default is None or arguments == ["--ids", "missing"]:
        with pytest.raises(SystemExit) as exc:
            textbook.main()
        assert exc.value.code == 2
        assert "error:" in capsys.readouterr().err
    else:
        textbook.main()
        assert "Selected 0 books" in capsys.readouterr().out


# Literal author expectations for the adopted grouping amendment. Advice cases
# (including corrected E5a/b) are disclosed controls, never fresh held-outs.
CD_OWN = b"User-agent: learnukrainianbot\n"
CD_GROUP_CONTROLS = [
    ("E1", CD_OWN + b"Crawl-delay: 1\nUser-agent: *\nDisallow: /", "/x", AMBIGUOUS, 1, None),
    ("E2a", group(b"Crawl-delay: 5", b"Disallow: /x"), "/y", ALLOW, 5, None),
    ("E2b", group(b"Crawl-delay: 5", b"Disallow: /x"), "/x", DENY, 5, None),
    ("E3", CD_OWN + b"Crawl-delay: 2\nDisallow: /p", "/q", ALLOW, 2, None),
    ("E4", CD_OWN + b"Crawl-delay: 1\nHost: example.org\n# note\n\nCrawl-delay: 3\nUser-agent: *\nDisallow: /", "/x", AMBIGUOUS, 3, None),
    ("E5a", b"User-agent: a\nCrawl-delay: 1\n" + CD_OWN + b"Crawl-delay: 2\nUser-agent: c\nDisallow: /p", "/p", UNRESOLVED, 2, None),
    ("E5b", b"User-agent: a\nCrawl-delay: 1\n" + CD_OWN + b"Crawl-delay: 2\nUser-agent: c\nDisallow: /p", "/q", UNRESOLVED, 2, None),
    ("E5c", b"User-agent: zz\nCrawl-delay: 1\n" + CD_OWN + b"Crawl-delay: 2\nUser-agent: c\nDisallow: /p", "/p", AMBIGUOUS, 2, None),
    ("E5d", b"User-agent: zz\nCrawl-delay: 1\n" + CD_OWN + b"Crawl-delay: 2\nUser-agent: c\nDisallow: /p", "/q", ALLOW, 2, None),
    ("E6a", b"Crawl-delay: 9\nUser-agent: *\nDisallow: /p", "/q", ALLOW, 0, None),
    ("E6b", b"Crawl-delay: 9\nUser-agent: *\nDisallow: /p", "/p", DENY, 0, None),
    ("E7", b"Crawl-delay: 9\n" + CD_OWN + b"User-agent: *\nDisallow: /", "/x", DENY, 0, None),
    *[("E8" + label, CD_OWN + b"Crawl-delay: " + value + b"\nUser-agent: *\nDisallow: /", "/x", AMBIGUOUS, delay, None)
      for label, value, delay in [("a", b"", 0), ("b", b"abc", 0), ("c", b"inf", 0),
                                  ("d", b"-1", 0), ("e", b"nan", 0), ("f", b"1,5", 0), ("g", b"0.25", .25)]],
    ("E9", CD_OWN + b"Crawl-delay 1\nUser-agent: *\nDisallow: /", "/x", UNRESOLVED, 0, None),
    ("E10a", CD_OWN + b"Crawl-delay: 1\nDisallow: /p\nUser-agent: *\nDisallow: /", "/x", ALLOW, 1, None),
    ("E10b", CD_OWN + b"Crawl-delay: 1\nDisallow: /p\nUser-agent: *\nDisallow: /", "/p", DENY, 1, None),
    ("E10c", CD_OWN + b"Crawl-delay: 1\nAllow: /\nUser-agent: *\nDisallow: /", "/x", ALLOW, 1, None),
    ("E10d", CD_OWN + b"Crawl-delay: 1\nDisallow:\nUser-agent: *\nDisallow: /", "/x", ALLOW, 1, None),
    ("E10e", CD_OWN + b"Allow: nope\nUser-agent: *\nDisallow: /", "/x", ALLOW, 0, None),
    ("E10f", CD_OWN + b"Crawl-delay: 1\nDisallow: nope\nUser-agent: *\nAllow: /", "/x", UNRESOLVED, 1, None),
    ("E11a", group(b"Crawl-delay: 10", b"User-agent: AhrefsBot", b"Disallow: /"), "/x", AMBIGUOUS, 10, None),
    ("E11b", b"User-agent: AhrefsBot\nCrawl-delay: 10\nUser-agent: *\nDisallow: /admin", "/x", ALLOW, 10, None),
    ("E11c", b"User-agent: AhrefsBot\nCrawl-delay: 10\nUser-agent: *\nDisallow: /admin", "/admin", DENY, 10, None),
    ("E12a", b"User-agent: LearnUkrainianBot/1.0\nCrawl-delay: 1\nUser-agent: *\nAllow: /", "/x", UNRESOLVED, 1, None),
    ("E12b", b"User-agent: learn\nCrawl-delay: 1\nUser-agent: *\nAllow: /", "/x", UNRESOLVED, 1, None),
    ("E12c", b"User-agent: googlebot\nCrawl-delay: 1\nUser-agent: *\nDisallow: /p", "/q", ALLOW, 1, None),
    ("E13", group(b"Crawl-delay: 99", b"User-agent: LearnUkrainianBot", b"Crawl-delay: 1.25"), "/x", ALLOW, 99, None),
    ("E14a", b"User-agent: Other\nCrawl-delay: 99\nUser-agent: *\nCrawl-delay: 2.75", "/x", ALLOW, 99, None),
    ("E14b", b"User-agent: Other\nCrawl-delay: 99\nDisallow: /o\nUser-agent: *\nCrawl-delay: 2.75", "/x", ALLOW, 2.75, None),
    ("E15", CD_OWN + b"Crawl-delay: 1\nUser-agent: otherbot\nAllow: /private\n" + CD_OWN + b"Disallow: /private", "/private", AMBIGUOUS, 1, None),
    ("E16a", group(b"Crawl-delay: 10", b"User-agent: Googlebot", b"Allow: /search", b"User-agent: *", b"Disallow: /search"), "/search", AMBIGUOUS, 10, None),
    ("E16b", group(b"Crawl-delay: 10", b"User-agent: Googlebot", b"Allow: /search/books", b"User-agent: *", b"Disallow: /search"), "/search/books/1", AMBIGUOUS, 10, None),
    ("E17", CD_OWN + b"Crawl-delay: 1\nUser-agent: *\nDisallow: /\n" + CD_OWN + b"Disallow: /p", "/p", DENY, 1, None),
    ("E18", CD_OWN + b"Crawl-delay: 1\nUser-agent: otherbot\nDisallow: nope\nUser-agent: *\nAllow: /", "/x", UNRESOLVED, 1, None),
    ("E19a", CD_OWN + b"Crawl-delay: 1\nUser-agent: *\nDisallow: /a%2Fb", "/a/b", AMBIGUOUS, 1, None),
    ("E19b", CD_OWN + b"Crawl-delay: 1\nUser-agent: *\nDisallow: /a%2Fb", "/a%2Fb", AMBIGUOUS, 1, None),
    ("E20", group(b"Disallow: /", b"User-agent: LearnUkrainianBot", b"Crawl-delay: 1", b"Disallow: /private"), "/public", ALLOW, 1, None),
    ("E21", b"User-agent: learn-ukrainian-sum\nCrawl-delay: 1\nUser-agent: *\nDisallow: /", "/x", AMBIGUOUS, 1, SUM_HEADER),
    ("E22", CD_OWN + b"Request-rate: 1/5\nUser-agent: *\nDisallow: /", "/x", DENY, 0, None),
    ("E23", b"User-agent: otherbot\nSitemap: https://source.test/s\n" + CD_OWN + b"Disallow: /", "/x", DENY, 0, None),
    ("E24", CD_OWN + b"User-agent: *\nCrawl-delay: 1\nDisallow: /", "/x", DENY, 1, None),
    ("E25", CD_OWN + b"Crawl-delay: 1\n\nUser-agent: *\nDisallow: /", "/x", AMBIGUOUS, 1, None),
    ("E26", CD_OWN + b"Crawl-delay: 1\nUser-agent: *\nDisallow: /", "/robots.txt", ALLOW, 1, None),
    ("E27", group(b"Crawl-delay: 4", b"User-agent: otherbot", b"Allow: /"), "/x", ALLOW, 4, None),
]


@pytest.mark.parametrize("case,body,target,expected,delay,header", CD_GROUP_CONTROLS, ids=[r[0] for r in CD_GROUP_CONTROLS])
def test_adopted_dual_grouping_literal_matrix(server, monkeypatch, case, body, target, expected, delay, header):
    module = server.module
    if header:
        monkeypatch.setattr(module, "USER_AGENT", header)
        if module is textbook:
            monkeypatch.setitem(textbook.HEADERS, "User-Agent", header)
    state = module._robots_parse(body, module.USER_AGENT)
    assert state["delay"] == delay
    server.robots = body
    url = "https://source.test" + target
    if expected == ALLOW:
        server.fetch(url)
        assert not module._access_stopped
        assert len(server.source_calls()) == (0 if target == "/robots.txt" else 1)
    else:
        with pytest.raises(module.AccessStopped, match=expected):
            server.fetch(url)
        assert module._access_stopped and server.source_calls() == []
        before = list(server.calls)
        with pytest.raises(module.AccessStopped):
            server.fetch("https://other.test/later")
        assert server.calls == before
        assert not list(server.tmp_path.glob("page-*.html"))
    import os
    if root := os.environ.get("LU_PERMISSION_EVIDENCE_DIR"):
        Path(root, f"i-group-{module.__name__}-{case}.json").write_text(json.dumps({
            "case": case, "expected": expected, "delay": delay,
            "state": repr(state), "requests": server.calls, "latched": module._access_stopped,
            "not_held_out": True,
        }))


@pytest.mark.parametrize("module", MODULES)
@pytest.mark.parametrize("shape", ["many-rules", "many-wildcards"])
def test_four_group_reading_evaluations_hostile_shape_under_five_seconds(module, shape, monkeypatch):
    import time
    bodies = {
        "many-rules": b"User-agent: *\n" + b"Disallow: /*a*a*a*a*b\n" * (512000 // 22),
        "many-wildcards": group(b"Disallow: /" + b"*a" * ((512000 - 40) // 2) + b"b"),
    }
    # Retain the original near-limit body intact: prepending group records
    # would correctly exceed the admission bound. Compose a worst-case state
    # from two actually parsed inputs, keeping the full hostile rules in both
    # lists. This is a conservative evaluation stress bound, not a larger
    # admitted robots file or a replacement for the literal grouping matrix.
    evaluations = []
    original = module._robots_canonical
    def canonical(raw, *, rule, reading):
        if not rule and raw.endswith(b"a" * 8000):
            evaluations.append(reading)
        return original(raw, rule=rule, reading=reading)
    monkeypatch.setattr(module, "_robots_canonical", canonical)
    start = time.perf_counter()
    hostile = module._robots_parse(bodies[shape], module.USER_AGENT)
    state = module._robots_parse(group(b"Crawl-delay: 1", b"User-agent: otherbot", b"Allow: /unused"), module.USER_AGENT)
    assert "legacy_rules" in state and not state["unresolved"] and not hostile["unresolved"]
    state["rules"].extend(hostile["rules"])
    state["legacy_rules"].extend(hostile["rules"])
    module._robots_states["https://h.test"] = state
    module._robots_check_target("https://h.test/" + "a" * 8000)
    elapsed = time.perf_counter() - start
    assert evaluations == [1, 1, 2, 1, 2]  # robots-path exception, then four evaluations
    assert elapsed < 5, (shape, elapsed)
    import os
    if root := os.environ.get("LU_PERMISSION_EVIDENCE_DIR"):
        Path(root, f"i-hostile-{module.__name__}-{shape}.json").write_text(json.dumps({
            "shape": shape, "seconds": elapsed, "evaluations": evaluations[1:], "composed_worst_case_state": True,
            "payload_octets": len(bodies[shape]), "under_five_seconds": elapsed < 5,
        }))


@pytest.mark.parametrize("module", MODULES)
def test_admitted_grouped_hostile_file_four_evaluations(module, monkeypatch):
    import time
    prefix = group(b"Crawl-delay: 1", b"User-agent: otherbot", b"Allow: /unused") + b"User-agent: *\n"
    rule = b"Disallow: /*a*a*a*a*b\n"
    # A separate maximal admitted grouped file; the original hostile fixtures
    # and their full-payload stress checks above remain unchanged.
    body = prefix + rule * ((512000 - len(prefix)) // len(rule))
    assert 511900 <= len(body) <= 512000
    readings = []
    original = module._robots_canonical
    def canonical(raw, *, rule, reading):
        if not rule and raw.endswith(b"a" * 8000):
            readings.append(reading)
        return original(raw, rule=rule, reading=reading)
    monkeypatch.setattr(module, "_robots_canonical", canonical)
    start = time.perf_counter()
    state = module._robots_parse(body, module.USER_AGENT)
    assert not state["unresolved"] and "legacy_rules" in state
    module._robots_states["https://h.test"] = state
    module._robots_check_target("https://h.test/" + "a" * 8000)
    elapsed = time.perf_counter() - start
    assert readings == [1, 1, 2, 1, 2] and elapsed < 5
    import os
    if root := os.environ.get("LU_PERMISSION_EVIDENCE_DIR"):
        Path(root, f"i-admitted-hostile-{module.__name__}.json").write_text(json.dumps({
            "body_octets": len(body), "seconds": elapsed, "evaluations": readings[1:],
            "actual_admitted_file": True, "under_five_seconds": elapsed < 5,
        }))
