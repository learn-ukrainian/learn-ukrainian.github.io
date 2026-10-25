"""Literal status-token corpus, including identifiers, decimals and markers."""

import pytest

from scripts.common.http_status import has_http_status

CODES = (401, 403, 404, 429, 500, 502, 503, 504, 599)
NONCES = (
    "c0ffee4019ab77de", "c0ffee4039ab77de", "c0ffee4049ab77de",
    "7f3a429c9e1b2d44", "7f3a500c9e1b2d44", "7f3a502c9e1b2d44",
    "7f3a503c9e1b2d44", "7f3a504c9e1b2d44", "7f3a599c9e1b2d44",
)
DIGESTS = (
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "abcdef429401403502503504500599404abcdef0123456789abcdef012345678",
)
NEGATIVES = (*NONCES, *DIGESTS,
    "z429x401g403h502i503j504k500l599m404Z",
    "_429", "429_", "a503b", "pid503", "503pid", "1503", "5030",
    "0.503", "v1.429", "1.2.504", "503.1", "503.٥", "503.５", "HTTP503.1", "HTTP/1.429",
    "xHTTP503", "_HTTP429", "status503abc", "error401x", "HTTP５０３",
    "HTTP٥٠٣", "HTTP5０3", "é503", "503é", "", "ordinary failure",
)
POSITIVES = (
    ("HTTP 429", 429), ("HTTP429", 429), ("status: 503", 503),
    ("429 Too Many Requests", 429), ("Error 502", 502),
    ("503", 503), ("pid 503", 503), ("HTTP503", 503),
    ("http/1.1 503", 503), ("HTTP/2 429", 429), ("STATUS CODE=403", 403),
    ("error code:401", 401), ("[504]", 504), ("(500)", 500),
    ("x/599/y", 599), ("x-404-y", 404), ("503. Failed", 503),
    ('{"status":503}', 503), ("\n429\n", 429), ("a=401,b=403", 401),
)


def test_frozen_identifier_corpus_shape():
    assert all(len(value) == 16 for value in NONCES)
    assert all(len(value) == 64 for value in DIGESTS)
    assert all(set(value) <= set("0123456789abcdef") for value in (*NONCES, *DIGESTS))


@pytest.mark.parametrize("message", NEGATIVES)
def test_identifiers_and_nonstatus_numbers_do_not_match(message):
    assert has_http_status(message, CODES) is False


@pytest.mark.parametrize("message,code", POSITIVES)
def test_standalone_and_marked_codes_match(message, code):
    assert has_http_status(message, (code,)) is True


@pytest.mark.parametrize("code", range(500, 600))
def test_entire_server_status_class(code):
    assert has_http_status(f"HTTP{code}", range(500, 600)) is True
    assert has_http_status(f"ab{code}cd", range(500, 600)) is False


def test_selection_and_later_matches():
    assert has_http_status("401 HTTP503", (503,)) is True
    assert has_http_status("HTTP503", (429,)) is False
    assert has_http_status("HTTP503", ()) is False


@pytest.mark.parametrize("text,start,expected", [
    ("x429", 1, False), ("0.429", 2, False), (" 429", 1, True),
    ("HTTP429", 4, True), ("429 before", 1, False), ("429 429", 4, True),
])
def test_tail_keeps_original_token_context(text, start, expected):
    assert has_http_status(text, (429,), start=start) is expected


def test_both_helper_import_styles():
    from common.http_status import has_http_status as cli_match

    assert cli_match("HTTP503", (503,)) is True
    assert cli_match("ab503cd", (503,)) is False
