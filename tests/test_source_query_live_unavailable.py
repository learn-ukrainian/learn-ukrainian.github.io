"""Hermetic tests: live-fetch tools must report `unavailable` on an outage,
never collapse it into a false `not_found` (#9005).

Covers scripts/rag/source_query.py: slovnyk_me_lookup, e2u_translate_with_status,
grac_concordance, grac_collocations. No network access — every HTTP call is
monkeypatched at the requests.Session.get level (not the module-local `_get`
wrapper), since scripts.rag.source_query and rag.source_query can load as two
distinct module objects with their own `_get`/`_SESSION`, depending on import
path; patching the requests.Session class method is robust to either alias.
"""

from __future__ import annotations

import pytest
import requests

from scripts.rag.source_query import (
    E2ULookupStatus,
    e2u_translate_with_status,
    grac_collocations,
    grac_concordance,
    slovnyk_me_lookup,
)


class DummyResponse:
    def __init__(self, status_code: int, text: str = "", data: dict | None = None):
        self.status_code = status_code
        self.text = text
        self._data = data

    def json(self):
        if self._data is not None:
            return self._data
        raise ValueError("Invalid JSON")

    def raise_for_status(self):
        if self.status_code >= 400:
            err = requests.HTTPError(f"HTTP {self.status_code}")
            err.response = self
            raise err


def _patch_get(monkeypatch: pytest.MonkeyPatch, respond):
    """Patch requests.Session.get for every Session instance, everywhere.

    `respond` is either a DummyResponse (returned as-is) or a callable that
    raises (for network-error simulation).
    """

    def fake_get(self, url, **kwargs):
        if callable(respond):
            return respond(url, **kwargs)
        return respond

    monkeypatch.setattr(requests.Session, "get", fake_get)


CLOUDFLARE_CHALLENGE_HTML = (
    "<html><head><title>Just a moment...</title></head>"
    "<body>Checking your browser before accessing slovnyk.me. "
    "cf-browser-verification cf-chl-widget</body></html>"
)


class TestSlovnykMeLookup:
    def test_found_returns_status_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        html = "<html><body><h1>хата</h1><p>оселя, житловий будинок</p></body></html>"
        _patch_get(monkeypatch, DummyResponse(200, html))
        result = slovnyk_me_lookup("хата", "vts")
        assert result["status"] == "found"
        assert "оселя" in result["text"]
        assert result["dict"] == "vts"

    def test_404_is_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_get(monkeypatch, DummyResponse(404))
        result = slovnyk_me_lookup("несловоякогонема", "vts")
        assert result["status"] == "not_found"

    def test_real_empty_article_is_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        html = "<html><body><h1></h1><footer>nav</footer></body></html>"
        _patch_get(monkeypatch, DummyResponse(200, html))
        result = slovnyk_me_lookup("хата", "vts")
        assert result["status"] == "not_found"

    def test_network_exception_is_unavailable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def raise_conn_error(url, **kwargs):
            raise requests.ConnectionError("boom")

        _patch_get(monkeypatch, raise_conn_error)
        result = slovnyk_me_lookup("хата", "vts")
        assert result["status"] == "unavailable"
        assert result["reason"] == "ConnectionError"

    def test_timeout_is_unavailable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def raise_timeout(url, **kwargs):
            raise requests.Timeout("timed out")

        _patch_get(monkeypatch, raise_timeout)
        result = slovnyk_me_lookup("хата", "vts")
        assert result["status"] == "unavailable"
        assert result["reason"] == "Timeout"

    def test_cloudflare_403_challenge_is_unavailable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_get(monkeypatch, DummyResponse(403, CLOUDFLARE_CHALLENGE_HTML))
        result = slovnyk_me_lookup("хата", "vts")
        assert result["status"] == "unavailable"
        assert result["challenge"] is True
        assert result["http_status"] == 403

    def test_429_is_unavailable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_get(monkeypatch, DummyResponse(429, "Too Many Requests"))
        result = slovnyk_me_lookup("хата", "vts")
        assert result["status"] == "unavailable"
        assert result["http_status"] == 429

    def test_5xx_is_unavailable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_get(monkeypatch, DummyResponse(503, "Service Unavailable"))
        result = slovnyk_me_lookup("хата", "vts")
        assert result["status"] == "unavailable"
        assert result["http_status"] == 503

    def test_unparseable_page_is_unavailable_not_not_found(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_get(monkeypatch, DummyResponse(200, "<html><body>no headings here</body></html>"))
        result = slovnyk_me_lookup("хата", "vts")
        assert result["status"] == "unavailable"
        assert result["reason"] == "unparseable_page"


class TestE2uTranslateWithStatus:
    def test_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        html = '<td class="result_row"><b>hello</b> привіт</td>'
        _patch_get(monkeypatch, DummyResponse(200, html))
        status, entries = e2u_translate_with_status("hello")
        assert status == E2ULookupStatus.FOUND
        assert entries[0]["headword"] == "hello"

    def test_404_is_not_found_within_verified_coverage(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_get(monkeypatch, DummyResponse(404))
        status, entries = e2u_translate_with_status("zzznotaword")
        assert status == E2ULookupStatus.NOT_FOUND_WITHIN_VERIFIED_COVERAGE
        assert entries == []

    def test_genuinely_empty_page_is_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_get(monkeypatch, DummyResponse(200, "<html><body>no entries</body></html>"))
        status, entries = e2u_translate_with_status("zzznotaword")
        assert status == E2ULookupStatus.NOT_FOUND_WITHIN_VERIFIED_COVERAGE
        assert entries == []

    def test_network_exception_is_source_unavailable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def raise_conn_error(url, **kwargs):
            raise requests.ConnectionError("boom")

        _patch_get(monkeypatch, raise_conn_error)
        status, entries = e2u_translate_with_status("hello")
        assert status == E2ULookupStatus.SOURCE_UNAVAILABLE
        assert entries == []

    def test_5xx_is_source_unavailable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_get(monkeypatch, DummyResponse(503))
        status, entries = e2u_translate_with_status("hello")
        assert status == E2ULookupStatus.SOURCE_UNAVAILABLE
        assert entries == []


class TestGracConcordanceCollocationsUnavailable:
    def test_concordance_genuine_empty_returns_empty_list(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_get(monkeypatch, DummyResponse(200, data={"Lines": []}))
        assert grac_concordance("zzznotaword") == []

    def test_concordance_network_exception_returns_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def raise_timeout(url, **kwargs):
            raise requests.Timeout("timed out")

        _patch_get(monkeypatch, raise_timeout)
        assert grac_concordance("книга") is None

    def test_concordance_5xx_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_get(monkeypatch, DummyResponse(503))
        assert grac_concordance("книга") is None

    def test_collocations_genuine_empty_returns_empty_list(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_get(monkeypatch, DummyResponse(200, data={"Items": []}))
        assert grac_collocations("zzznotaword") == []

    def test_collocations_network_exception_returns_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def raise_conn_error(url, **kwargs):
            raise requests.ConnectionError("boom")

        _patch_get(monkeypatch, raise_conn_error)
        assert grac_collocations("книга") is None
