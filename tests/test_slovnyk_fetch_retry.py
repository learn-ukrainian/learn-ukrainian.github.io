"""Tests for the 429-friendly slovnyk.me fetch + mirror builder (#3097)."""

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


def test_retries_on_429_then_succeeds(monkeypatch, sleeps):
    monkeypatch.setattr(em, "_parse_slovnyk_entry", lambda *a, **k: {"text": "ok"})
    _queue(monkeypatch, [_FakeResp(429), _FakeResp(429), _FakeResp(200)])
    assert em._fetch_slovnyk_entry("вода", "вода", "newsum") == {"text": "ok"}
    assert len(sleeps) == 2  # two backoff sleeps before the 200


def test_retries_on_5xx_then_succeeds(monkeypatch, sleeps):
    monkeypatch.setattr(em, "_parse_slovnyk_entry", lambda *a, **k: {"text": "ok"})
    _queue(monkeypatch, [_FakeResp(503), _FakeResp(200)])
    assert em._fetch_slovnyk_entry("вода", "вода", "newsum") == {"text": "ok"}
    assert len(sleeps) == 1


def test_404_returns_none_without_retry(monkeypatch, sleeps):
    _queue(monkeypatch, [_FakeResp(404)])
    assert em._fetch_slovnyk_entry("неслово", "неслово", "newsum") is None
    assert sleeps == []


def test_persistent_429_raises_transient_after_max_retries(monkeypatch, sleeps):
    _queue(monkeypatch, [_FakeResp(429)] * (em._SLOVNYK_MAX_RETRIES + 1))
    with pytest.raises(em._SlovnykTransientError):
        em._fetch_slovnyk_entry("вода", "вода", "newsum")
    assert len(sleeps) == em._SLOVNYK_MAX_RETRIES  # slept between retries, not after the last


def test_honors_retry_after_header(monkeypatch, sleeps):
    monkeypatch.setattr(em, "_parse_slovnyk_entry", lambda *a, **k: {"text": "ok"})
    _queue(monkeypatch, [_FakeResp(429, headers={"Retry-After": "7"}), _FakeResp(200)])
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
