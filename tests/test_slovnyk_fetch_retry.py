"""Tests for slovnyk.me retries and the standalone filler's refusal stop."""

import datetime as dt
import json
from types import SimpleNamespace

import pytest
import requests

from scripts.lexicon import enrich_manifest as em
from scripts.lexicon import fill_slovnyk_sum20_cache as filler


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


def test_retries_on_429_then_succeeds(monkeypatch, sleeps):
    monkeypatch.setattr(em, "_parse_slovnyk_entry", lambda *a, **k: {"text": "ok"})
    _queue(monkeypatch, [_FakeResp(429), _FakeResp(429), _FakeResp(200)])
    assert em._fetch_slovnyk_entry("вода", "вода", "newsum") == {"text": "ok"}
    assert len(sleeps) == 2  # two backoff sleeps before the 200


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


_ARTICLE = '<section id="dictionary-article"><article><h1>вода</h1><p>Рідина.</p></article></section>'
_CHALLENGE = "<title>Just a moment...</title>" + _ARTICLE


@pytest.fixture
def curl_queue(monkeypatch, tmp_path):
    """Keep subprocesses, clock, sleeps and all cache bytes in a hermetic fixture."""
    responses = []
    calls = []
    delays = []

    def run(cmd, **kwargs):
        assert cmd[0] == "curl"
        assert kwargs == {"capture_output": True, "text": True, "timeout": 20}
        calls.append(cmd)
        code, body = responses.pop(0)
        return SimpleNamespace(returncode=0, stdout=f"{body}\n{code}")

    class Clock(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 1, 1, tzinfo=tz)

    monkeypatch.setattr(filler.subprocess, "run", run)
    monkeypatch.setattr(filler.time, "sleep", delays.append)
    monkeypatch.setattr(filler.dt, "datetime", Clock)
    monkeypatch.setattr(em, "SLOVNYK_CACHE", tmp_path / "cache")
    return SimpleNamespace(responses=responses, calls=calls, delays=delays)


@pytest.mark.parametrize("code,body,reason", [
    (403, _ARTICLE, "HTTP 403"),
    (200, _CHALLENGE, "Cloudflare challenge (HTTP 200)"),
    (429, _ARTICLE, "HTTP 429"),
], ids=["403", "challenge", "429"])
@pytest.mark.parametrize("legacy_limit", [20, 999, 0])
def test_filler_stops_before_second_request_on_first_refusal(
    curl_queue, tmp_path, capsys, code, body, reason, legacy_limit,
):
    """A refused batch used to continue and could fetch/cache the second word."""
    curl_queue.responses.extend([(code, body), (200, _ARTICLE)])
    stats = filler.fill_slovnyk_newsum_cache(
        ["вода", "книга"], work_dir=tmp_path / "work", consecutive_403_limit=legacy_limit,
    )

    assert len(curl_queue.calls) == 1
    assert curl_queue.calls[0][-1] == "https://slovnyk.me/dict/newsum/%D0%B2%D0%BE%D0%B4%D0%B0"
    assert curl_queue.calls[0][4:6] == ["-A", "learn-ukrainian-word-atlas/1.0"]
    assert stats == {
        "total": 2, "already_cached": 0, "fetched_ok": 0, "not_found_404": 0,
        "cf_challenge_403": int(code != 429), "rate_limited_429": int(code == 429), "other_error": 0,
    }
    assert not em._slovnyk_cache_path("вода").exists()
    assert not em._slovnyk_cache_path("книга").exists()
    assert curl_queue.delays == []
    assert reason in (tmp_path / "work" / "blocked.md").read_text()
    assert "ABORT:" in capsys.readouterr().err


@pytest.mark.parametrize("code,body", [(403, _ARTICLE), (200, _CHALLENGE), (429, _ARTICLE)],
                         ids=["403", "challenge", "429"])
def test_filler_refusal_preserves_existing_cache_bytes_when_forced(curl_queue, code, body):
    path = em._slovnyk_cache_path("вода")
    path.parent.mkdir(parents=True)
    original = b'{"schema_version": 4, "lookups": {"newsum": {"text": "saved"}}}\n'
    path.write_bytes(original)
    curl_queue.responses.extend([(code, body), (200, _ARTICLE)])

    stats = filler.fill_slovnyk_newsum_cache(["вода", "книга"], force=True)

    assert len(curl_queue.calls) == 1
    assert stats["fetched_ok"] == 0
    assert path.read_bytes() == original
    assert not em._slovnyk_cache_path("книга").exists()


@pytest.mark.parametrize("code", [200, 404])
@pytest.mark.parametrize("lookups", [None, {"vts": {"text": "retained"}}, []])
def test_filler_keeps_success_and_404_cache_format(curl_queue, capsys, code, lookups):
    path = em._slovnyk_cache_path("вода")
    if lookups is not None:
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({
            "schema_version": em._SLOVNYK_CACHE_SCHEMA_VERSION, "lemma": "вода",
            "lookup_word": "вода", "lookups": lookups,
        }))
    curl_queue.responses.append((code, _ARTICLE))

    stats = filler.fill_slovnyk_newsum_cache(["вода"], checkpoint_interval=1)

    cached = json.loads(path.read_text())
    assert cached["lemma"] == "вода"
    assert cached["lookup_word"] == "вода"
    assert cached["schema_version"] == em._SLOVNYK_CACHE_SCHEMA_VERSION
    if code == 200:
        row = cached["lookups"]["newsum"]
        assert row["text"] == "вода Рідина."
        assert row["word"] == "вода"
        assert row["source_url"] == "https://slovnyk.me/dict/newsum/%D0%B2%D0%BE%D0%B4%D0%B0"
        assert cached["fetched_at"] == "2026-01-01T00:00:00+00:00"
    else:
        assert cached["lookups"]["newsum"] is None
    if isinstance(lookups, dict):
        assert cached["lookups"]["vts"] == {"text": "retained"}
    assert stats["fetched_ok"] == int(code == 200)
    assert stats["not_found_404"] == int(code == 404)
    assert "[1/1] Progress:" in capsys.readouterr().out
    assert curl_queue.delays == [0.3]
    if code == 200:
        saved = path.read_bytes()
        stats = filler.fill_slovnyk_newsum_cache(["вода"], checkpoint_interval=1)
        assert stats["already_cached"] == 1
        assert len(curl_queue.calls) == 1
        assert path.read_bytes() == saved
        assert "cached=1" in capsys.readouterr().out


@pytest.mark.parametrize("code,body", [(200, "<html></html>"), (500, "error")])
def test_filler_counts_ordinary_errors_and_continues(curl_queue, code, body):
    curl_queue.responses.extend([(code, body), (404, "missing")])

    stats = filler.fill_slovnyk_newsum_cache(["вода", "книга"], sleep_seconds=0)

    assert stats["other_error"] == 1
    assert stats["not_found_404"] == 1
    assert len(curl_queue.calls) == 2
    assert not em._slovnyk_cache_path("вода").exists()
    assert json.loads(em._slovnyk_cache_path("книга").read_text())["lookups"] == {"newsum": None}
    assert curl_queue.delays == []


@pytest.mark.parametrize("code,body,exit_code", [
    (403, _ARTICLE, 1), (200, _CHALLENGE, 1), (429, _ARTICLE, 1),
    (200, _ARTICLE, 0), (404, "missing", 0),
], ids=["403", "challenge", "429", "200", "404"])
@pytest.mark.parametrize("audit_format", [False, True])
def test_filler_cli_refusal_is_failure_even_with_legacy_limit(
    curl_queue, monkeypatch, tmp_path, capsys, code, body, exit_code, audit_format,
):
    words = tmp_path / "words.json"
    words.write_text(json.dumps(
        {"class_b_detail": [{"url_slug": "вода"}, {"lemma": "книга"}]} if audit_format else ["вода", "книга"],
    ))
    args = [
        "fill_slovnyk_sum20_cache.py", "--slugs-file", str(words), "--work-dir", str(tmp_path / "work"),
        "--consecutive-403-limit", "999", "--sleep", "0", "--force",
    ]
    if not audit_format:
        args.extend(["--limit", "1"])
    monkeypatch.setattr(filler.sys, "argv", args)
    curl_queue.responses.extend([(code, body), (404, "missing")])

    assert filler.main() == exit_code
    assert len(curl_queue.calls) == (2 if audit_format and exit_code == 0 else 1)
    assert "Finished. Summary:" in capsys.readouterr().out
