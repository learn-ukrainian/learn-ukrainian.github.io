"""Tests for immediate access stops and transient retry contracts (#8999, #3097)."""

import json
from pathlib import Path

import pytest
import requests

from scripts.lexicon import build_slovnyk_mirror as mirror
from scripts.lexicon import enrich_manifest as em


class _FakeResp:
    def __init__(self, status_code: int, text: str = "<html></html>", headers: dict | None = None):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")


@pytest.fixture
def sleeps(monkeypatch):
    """Neutralize delays; record backoff sleep durations."""
    recorded: list[float] = []
    monkeypatch.delenv("LEXICON_SLOVNYK_OFFLINE", raising=False)
    monkeypatch.setattr(em, "_polite_slovnyk_delay", lambda: None)
    monkeypatch.setattr(em.time, "sleep", recorded.append)
    monkeypatch.setattr(em.random, "uniform", lambda a, b: 0.0)
    return recorded


def _queue(monkeypatch, responses: list[_FakeResp]) -> None:
    it = iter(responses)
    monkeypatch.setattr(em.requests, "get", lambda url, **kw: next(it))


def test_parse_retry_after():
    assert em._parse_retry_after("5") == 5.0
    assert em._parse_retry_after("0") == 0.0
    assert em._parse_retry_after("") is None
    assert em._parse_retry_after(None) is None
    assert em._parse_retry_after("soon") is None


@pytest.mark.parametrize("headers", [{}, {"Retry-After": "7"}])
def test_429_stops_once_without_retry_or_sleep(monkeypatch, sleeps, headers):
    calls = []
    monkeypatch.setattr(em.requests, "get", lambda url, **kw: calls.append(url) or _FakeResp(429, headers=headers))
    with pytest.raises(em._SlovnykAccessStopped):
        em._fetch_slovnyk_entry("вода", "вода", "newsum")
    assert len(calls) == 1 and sleeps == [] and em._slovnyk_access_stopped
    with pytest.raises(em._SlovnykAccessStopped):
        em._fetch_slovnyk_entry("other", "other", "vts")
    assert len(calls) == 1 and sleeps == []


def test_retries_on_5xx_then_succeeds(monkeypatch, sleeps):
    monkeypatch.setattr(em, "_parse_slovnyk_entry", lambda *a, **k: {"text": "ok"})
    _queue(monkeypatch, [_FakeResp(503), _FakeResp(200)])
    assert em._fetch_slovnyk_entry("вода", "вода", "newsum") == {"text": "ok"}
    assert len(sleeps) == 1


def test_404_returns_none_without_retry(monkeypatch, sleeps):
    _queue(monkeypatch, [_FakeResp(404)])
    assert em._fetch_slovnyk_entry("неслово", "неслово", "newsum") is None
    assert sleeps == []


def test_persistent_503_raises_transient_after_max_retries(monkeypatch, sleeps):
    _queue(monkeypatch, [_FakeResp(503)] * (em._SLOVNYK_MAX_RETRIES + 1))
    with pytest.raises(em._SlovnykTransientError):
        em._fetch_slovnyk_entry("вода", "вода", "newsum")
    assert len(sleeps) == em._SLOVNYK_MAX_RETRIES  # slept between retries, not after the last


def test_honors_retry_after_header(monkeypatch, sleeps):
    monkeypatch.setattr(em, "_parse_slovnyk_entry", lambda *a, **k: {"text": "ok"})
    _queue(monkeypatch, [_FakeResp(503, headers={"Retry-After": "7"}), _FakeResp(200)])
    assert em._fetch_slovnyk_entry("вода", "вода", "newsum") == {"text": "ok"}
    assert sleeps == [7.0]  # honored Retry-After exactly (jitter mocked to 0)


def test_network_error_retries_then_raises(monkeypatch, sleeps):
    def boom(url, **kw):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(em.requests, "get", boom)
    with pytest.raises(em._SlovnykTransientError):
        em._fetch_slovnyk_entry("вода", "вода", "newsum")
    assert len(sleeps) == em._SLOVNYK_MAX_RETRIES


def test_manifest_lemmas_dedupes_preserving_order(tmp_path: Path):
    manifest = tmp_path / "m.json"
    manifest.write_text(
        json.dumps(
            {"entries": [{"lemma": "вода"}, {"lemma": "дім"}, {"lemma": "вода"}, {"no_lemma": 1}]}
        ),
        encoding="utf-8",
    )
    assert mirror._manifest_lemmas(manifest) == ["вода", "дім"]
