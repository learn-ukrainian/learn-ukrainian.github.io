"""Offline unit tests for Wikipedia REST query in scripts/rag/source_query.py."""

from __future__ import annotations

from urllib.parse import quote

import pytest
import requests

from scripts.lexicon import enrich_manifest
from scripts.rag.source_query import (
    WIKI_REST,
    WIKI_USER_AGENT,
    _is_disambiguation_summary,
    _wiki_title_candidates,
    wikipedia_summary,
)


class DummyResponse:
    def __init__(self, status_code: int, data: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._data = data
        self.text = text

    def json(self):
        if self._data is not None:
            return self._data
        raise ValueError("Invalid JSON")

    def raise_for_status(self):
        if self.status_code >= 400:
            http_err = requests.HTTPError(f"HTTP {self.status_code}")
            http_err.response = self
            raise http_err


def test_wiki_title_candidates_sentence_case() -> None:
    assert _wiki_title_candidates("ампір") == ["ампір", "Ампір"]
    assert _wiki_title_candidates("школа") == ["школа", "Школа"]
    assert _wiki_title_candidates("вода") == ["вода", "Вода"]
    assert _wiki_title_candidates("абажур") == ["абажур", "Абажур"]
    assert _wiki_title_candidates("ідея") == ["ідея", "Ідея"]
    assert _wiki_title_candidates("їжак") == ["їжак", "Їжак"]
    assert _wiki_title_candidates("єнот") == ["єнот", "Єнот"]
    assert _wiki_title_candidates("ґанок") == ["ґанок", "Ґанок"]
    assert _wiki_title_candidates("Київ") == ["Київ"]
    assert _wiki_title_candidates("київська область") == ["київська область", "Київська область"]
    assert _wiki_title_candidates("") == []
    assert _wiki_title_candidates("   ") == []


def test_is_disambiguation_summary() -> None:
    assert _is_disambiguation_summary({"type": "disambiguation", "title": "Ампір"})
    assert _is_disambiguation_summary({"type": "standard", "title": "Ампір (значення)"})
    assert _is_disambiguation_summary({"type": "standard", "title": "ампір (значення)"})
    assert _is_disambiguation_summary({
        "type": "standard",
        "title": "Ампір",
        "description": "сторінка значень у проекті Вікімедіа",
    })
    assert _is_disambiguation_summary({
        "type": "standard",
        "title": "Ампір",
        "description": "сторінка значень у проєкті Вікімедіа",
    })
    assert not _is_disambiguation_summary({
        "type": "standard",
        "title": "Ампір",
        "description": "стиль пізнього класицизму",
    })


def test_wikipedia_summary_lowercase_403_falls_back_to_capitalized_200(monkeypatch: pytest.MonkeyPatch) -> None:
    recorded_calls: list[tuple[str, dict]] = []

    def mock_get(url: str, headers: dict | None = None, timeout: int = 15):
        recorded_calls.append((url, headers or {}))
        # Lowercase path returns 403 HTML
        if quote("ампір") in url:
            return DummyResponse(403, text="<html>Wikimedia Error 403 Forbidden</html>")
        # Capitalized path returns 200 JSON
        if quote("Ампір") in url:
            return DummyResponse(
                200,
                data={
                    "type": "standard",
                    "title": "Ампір",
                    "description": "стиль у мистецтві",
                    "extract": "Ампі́р — стиль пізнього класицизму...",
                    "content_urls": {
                        "desktop": {
                            "page": "https://uk.wikipedia.org/wiki/%D0%90%D0%BC%D0%BF%D1%96%D1%80"
                        }
                    },
                },
            )
        return DummyResponse(404)

    monkeypatch.setattr(requests, "get", mock_get)

    result = wikipedia_summary("ампір")
    assert result == {
        "title": "Ампір",
        "description": "стиль у мистецтві",
        "extract": "Ампі́р — стиль пізнього класицизму...",
        "url": "https://uk.wikipedia.org/wiki/%D0%90%D0%BC%D0%BF%D1%96%D1%80",
        "type": "standard",
    }
    assert len(recorded_calls) == 2
    assert recorded_calls[0][0] == f"{WIKI_REST}/page/summary/{quote('ампір')}"
    assert recorded_calls[1][0] == f"{WIKI_REST}/page/summary/{quote('Ампір')}"
    for _, hdrs in recorded_calls:
        assert hdrs.get("User-Agent") == WIKI_USER_AGENT
        assert hdrs.get("Accept") == "application/json"


def test_wikipedia_summary_skips_disambiguation_page(monkeypatch: pytest.MonkeyPatch) -> None:
    def mock_get(url: str, headers: dict | None = None, timeout: int = 15):
        return DummyResponse(
            200,
            data={
                "type": "disambiguation",
                "title": "Ампір (значення)",
                "description": "сторінка значень у проєкті Вікімедіа",
                "extract": "Ампі́р: Ампір — стиль...",
                "content_urls": {
                    "desktop": {
                        "page": "https://uk.wikipedia.org/wiki/%D0%90%D0%BC%D0%BF%D1%96%D1%80_(%D0%B7%D0%BD%D0%B0%D1%87%D0%B5%D0%BD%D0%BD%D1%8F)"
                    }
                },
            },
        )

    monkeypatch.setattr(requests, "get", mock_get)

    assert wikipedia_summary("Ампір (значення)") is None
    assert wikipedia_summary("ампір (значення)") is None


def test_wikipedia_summary_honest_miss_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    def mock_get(url: str, headers: dict | None = None, timeout: int = 15):
        return DummyResponse(404, text="Not Found")

    monkeypatch.setattr(requests, "get", mock_get)

    assert wikipedia_summary("абзац") is None


def test_enrich_manifest_query_wikipedia_and_wiki_reference(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    enrich_manifest.query_wikipedia.cache_clear()
    monkeypatch.setattr(enrich_manifest, "_phase1_offline_mode", lambda: False)
    monkeypatch.setattr(enrich_manifest, "WIKI_REFERENCE_CACHE", tmp_path / "wiki_reference.json")
    monkeypatch.setattr(enrich_manifest, "_WIKI_REFERENCE_CACHE_DATA", None)
    monkeypatch.setattr(enrich_manifest, "_WIKI_REFERENCE_CACHE_DIRTY", False)

    def mock_get(url: str, headers: dict | None = None, timeout: int = 15):
        if quote("Школа") in url:
            return DummyResponse(
                200,
                data={
                    "type": "standard",
                    "title": "Школа",
                    "description": "навчальний заклад",
                    "extract": "Шко́ла — заклад освіти...",
                    "content_urls": {
                        "desktop": {
                            "page": "https://uk.wikipedia.org/wiki/%D0%A8%D0%BA%D0%BE%D0%BB%D0%B0"
                        }
                    },
                },
            )
        return DummyResponse(403, text="Forbidden")

    monkeypatch.setattr(requests, "get", mock_get)

    ref = enrich_manifest._wiki_reference("школа", literary_attestation={"text": "attestation"})
    assert ref is not None
    assert ref["wikipedia"]["title"] == "Школа"
    assert ref["wikipedia"]["summary"] == "Шко́ла — заклад освіти..."
    assert ref["wikipedia"]["url"] == "https://uk.wikipedia.org/wiki/%D0%A8%D0%BA%D0%BE%D0%BB%D0%B0"
    assert ref["wiktionary_url"] == f"https://uk.wiktionary.org/wiki/{quote('школа')}"
    assert ref["wikisource_url"] == f"https://uk.wikisource.org/wiki/{quote('школа')}"
