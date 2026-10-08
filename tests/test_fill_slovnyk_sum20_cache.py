"""Hermetic curl/cache boundary tests; no source data or live requests."""

import json
from types import SimpleNamespace

import pytest

from scripts.lexicon import enrich_manifest as em
from scripts.lexicon import fill_slovnyk_sum20_cache as fill


@pytest.fixture(autouse=True)
def transport_state(monkeypatch, tmp_path):
    monkeypatch.setattr(em, "_slovnyk_access_stopped", False, raising=False)
    monkeypatch.setattr(em, "_slovnyk_robots", None, raising=False)
    monkeypatch.setattr(em, "_last_slovnyk_fetch", None, raising=False)
    monkeypatch.setattr(em, "SLOVNYK_CACHE", tmp_path / "cache")
    monkeypatch.setattr(em, "_SLOVNYK_DELAY_SECONDS", 0, raising=False)
    now = [0.0]
    monkeypatch.setattr(em.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(em.time, "sleep", lambda seconds: now.__setitem__(0, now[0] + seconds))
    monkeypatch.setattr(
        em.requests,
        "get",
        lambda *_a, **_k: SimpleNamespace(status_code=200, text="User-agent: *\nCrawl-delay: 5\nDisallow:", headers={}),
    )
    return now


def test_curl_identity_and_robots_floor(monkeypatch, transport_state):
    calls = []

    def run(command, **kwargs):
        calls.append((command, transport_state[0]))
        return SimpleNamespace(returncode=0, stdout="synthetic\n200")

    monkeypatch.setattr(fill.subprocess, "run", run)
    assert fill.fetch_newsum_curl("sample") == (200, "synthetic")
    assert fill.fetch_newsum_curl("other") == (200, "synthetic")
    assert [t for _, t in calls] == [5, 10]
    command = calls[0][0]
    agent = command[command.index("-A") + 1]
    assert "https://github.com/learn-ukrainian/learn-ukrainian.github.io" in agent
    assert "Mozilla" not in agent and "Chrome" not in agent
    assert "--retry" not in command and "-L" not in command


@pytest.mark.parametrize(
    "code,body",
    [
        (403, "denied"),
        (429, "slow down"),
        (401, "denied"),
        (200, "<title>Just a moment...</title>"),
        (200, "<div id='cf-chl-widget'>"),
        (404, "<title>Just a moment...</title>"),
    ],
)
def test_fill_stops_first_denial_preserves_existing(monkeypatch, tmp_path, code, body):
    path = em._slovnyk_cache_path("sample")
    path.parent.mkdir(parents=True)
    original = json.dumps(
        {
            "schema_version": em._SLOVNYK_CACHE_SCHEMA_VERSION,
            "lookups": {"newsum": {"text": "settled cached data"}, "vts": {"text": "other data"}},
        }
    )
    path.write_text(original)
    calls = []

    def fetch(word):
        calls.append(word)
        return code, body

    monkeypatch.setattr(fill, "fetch_newsum_curl", fetch)
    stats = fill.fill_slovnyk_newsum_cache(["sample", "other"], force=True, sleep_seconds=0)
    assert stats["access_stopped"] == 1 and stats["fetched_ok"] == 0
    assert calls == ["sample"] and path.read_text() == original
    with pytest.raises(em._SlovnykAccessStopped):
        em._polite_slovnyk_delay()


def test_cached_entry_does_not_fetch(monkeypatch):
    path = em._slovnyk_cache_path("sample")
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({"schema_version": em._SLOVNYK_CACHE_SCHEMA_VERSION, "lookups": {"newsum": {"text": "existing"}}})
    )
    monkeypatch.setattr(fill, "fetch_newsum_curl", lambda *_: pytest.fail("cached data must stay local"))
    assert fill.fill_slovnyk_newsum_cache(["sample"])["already_cached"] == 1


@pytest.mark.parametrize("code", [200, 404, 503, 0])
def test_fill_payload_success_miss_errors(monkeypatch, code):
    monkeypatch.setattr(fill, "fetch_newsum_curl", lambda *_: (code, "synthetic"))
    monkeypatch.setattr(fill, "_parse_slovnyk_entry", lambda *_a, **_k: {"text": "synthetic", "source_url": "source"})
    stats = fill.fill_slovnyk_newsum_cache(["sample"], sleep_seconds=0)
    assert stats["access_stopped"] == 0
    path = em._slovnyk_cache_path("sample")
    if code in {200, 404}:
        row = json.loads(path.read_text())["lookups"]["newsum"]
        assert row == ({"text": "synthetic", "source_url": "source"} if code == 200 else None)
    else:
        assert not path.exists() and stats["other_error"] == 1


@pytest.mark.parametrize(
    "kwargs",
    [{"consecutive_403_limit": 20}, {"sleep_seconds": -1}, {"sleep_seconds": float("nan")}, {"checkpoint_interval": 0}],
)
def test_invalid_parameters_fail_before_requests(kwargs):
    with pytest.raises(ValueError):
        fill.fill_slovnyk_newsum_cache(["sample"], **kwargs)


@pytest.mark.parametrize("result", ["timeout", "exit", "malformed"])
def test_curl_transport_failures(monkeypatch, result):
    def run(*args, **kwargs):
        if result == "timeout":
            raise fill.subprocess.TimeoutExpired("curl", 15)
        return SimpleNamespace(returncode=1 if result == "exit" else 0, stdout="body\ninvalid")

    monkeypatch.setattr(fill.subprocess, "run", run)
    assert fill.fetch_newsum_curl("sample")[0] == 0


def test_main_denial_exit(monkeypatch, tmp_path):
    slugs = tmp_path / "slugs.json"
    slugs.write_text('["sample","other"]')
    monkeypatch.setattr(fill.sys, "argv", ["fill", "--slugs-file", str(slugs), "--work-dir", str(tmp_path / "work")])
    monkeypatch.setattr(fill, "fetch_newsum_curl", lambda *_: (429, "denied"))
    assert fill.main() == 1
    assert "no further requests" in (tmp_path / "work" / "blocked.md").read_text()


def test_curl_challenge_header_stops(monkeypatch):
    monkeypatch.setattr(
        fill.subprocess,
        "run",
        lambda *_a, **_k: SimpleNamespace(returncode=0, stdout="HTTP/2 200\ncf-mitigated: challenge\n\nsynthetic\n200"),
    )
    with pytest.raises(em._SlovnykAccessStopped):
        fill.fetch_newsum_curl("sample")
    assert em._slovnyk_access_stopped


def test_curl_success_strips_transport_headers(monkeypatch):
    monkeypatch.setattr(
        fill.subprocess,
        "run",
        lambda *_a, **_k: SimpleNamespace(returncode=0, stdout="HTTP/2 200\ncontent-type: text/html\n\nsynthetic\n200"),
    )
    assert fill.fetch_newsum_curl("sample") == (200, "synthetic")


def test_fractional_crawl_delay_is_floor(monkeypatch, transport_state):
    monkeypatch.setattr(
        em.requests,
        "get",
        lambda *_a, **_k: SimpleNamespace(
            status_code=200, text="User-agent: *\nCrawl-delay: 2.5\nDisallow:", headers={}
        ),
    )
    monkeypatch.setattr(fill.subprocess, "run", lambda *_a, **_k: SimpleNamespace(returncode=0, stdout="body\n200"))
    fill.fetch_newsum_curl("sample")
    assert transport_state[0] >= 2.5


@pytest.mark.parametrize("code", [200, 404])
@pytest.mark.parametrize("lookups", [{"vts": {"text": "settled sibling"}}, "legacy malformed"])
def test_refill_existing_preserves_sibling_payload(monkeypatch, code, lookups):
    path = em._slovnyk_cache_path("sample")
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"schema_version": em._SLOVNYK_CACHE_SCHEMA_VERSION, "lookups": lookups}))
    monkeypatch.setattr(fill, "fetch_newsum_curl", lambda *_: (code, "synthetic"))
    monkeypatch.setattr(fill, "_parse_slovnyk_entry", lambda *_a, **_k: {"text": "positive"})
    fill.fill_slovnyk_newsum_cache(["sample"], force=True, sleep_seconds=1, checkpoint_interval=1)
    saved = json.loads(path.read_text())["lookups"]
    assert saved["newsum"] == ({"text": "positive"} if code == 200 else None)
    if isinstance(lookups, dict):
        assert saved["vts"] == lookups["vts"]


def test_cached_checkpoint_and_empty_parse(monkeypatch):
    path = em._slovnyk_cache_path("sample")
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({"schema_version": em._SLOVNYK_CACHE_SCHEMA_VERSION, "lookups": {"newsum": {"text": "cached"}}})
    )
    monkeypatch.setattr(fill, "fetch_newsum_curl", lambda *_: (200, "empty article"))
    monkeypatch.setattr(fill, "_parse_slovnyk_entry", lambda *_a, **_k: None)
    stats = fill.fill_slovnyk_newsum_cache(["sample", "other"], checkpoint_interval=1, sleep_seconds=0)
    assert stats["already_cached"] == 1 and stats["other_error"] == 1


def test_main_audit_input_limit_success(monkeypatch, tmp_path):
    slugs = tmp_path / "slugs.json"
    slugs.write_text('{"class_b_detail": [{"url_slug": "sample"}, {"lemma": "other"}]}')
    monkeypatch.setattr(
        fill.sys, "argv", ["fill", "--slugs-file", str(slugs), "--work-dir", str(tmp_path / "work"), "--limit", "1"]
    )
    monkeypatch.setattr(fill, "fetch_newsum_curl", lambda *_: (404, ""))
    assert fill.main() == 0


def test_main_invalid_input(monkeypatch, tmp_path):
    slugs = tmp_path / "slugs.json"
    slugs.write_text("{}")
    monkeypatch.setattr(fill.sys, "argv", ["fill", "--slugs-file", str(slugs)])
    with pytest.raises(ValueError, match="unrecognized"):
        fill.main()


@pytest.mark.parametrize("code,body", [(403, "denied"), (429, "slow down"), (200, "<div id='cf_chl_widget'>")])
def test_direct_curl_stop_latches_before_next_call(monkeypatch, code, body):
    calls = []
    monkeypatch.setattr(fill.subprocess, "run", lambda *a, **k: calls.append(a) or SimpleNamespace(returncode=0, stdout=f"{body}\n{code}"))
    with pytest.raises(em._SlovnykAccessStopped):
        fill.fetch_newsum_curl("sample")
    with pytest.raises(em._SlovnykAccessStopped):
        fill.fetch_newsum_curl("other")
    assert len(calls) == 1 and em._slovnyk_access_stopped


def test_proxy_header_block_does_not_hide_challenge(monkeypatch):
    raw = "HTTP/1.1 200 Connection established\n\nHTTP/2 200\nCF-Mitigated: challenge\n\nbody\n200"
    monkeypatch.setattr(fill.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0, stdout=raw))
    with pytest.raises(em._SlovnykAccessStopped):
        fill.fetch_newsum_curl("sample")
    assert em._slovnyk_access_stopped


def test_detection_script_is_content_not_access_stop(monkeypatch):
    body = "<script src='/cdn-cgi/challenge-platform/scripts/jsd/api.js'></script>"
    monkeypatch.setattr(fill.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0, stdout=body + "\n200"))
    assert fill.fetch_newsum_curl("sample") == (200, body)
    assert not em._slovnyk_access_stopped
