"""Tests for P2 follow-up endpoints (#1313 / Codex 6, 7).

Covers:
    /api/issues/map       Codex-6 — grouped open issues + supersede hints
    /api/runtime/auth     Codex-7 — per-agent auth-mode snapshot
"""

from __future__ import annotations

from fastapi.testclient import TestClient

import scripts.api.issues_router as issues_router
import scripts.api.main as api_main

client = TestClient(api_main.app, raise_server_exceptions=False)


# ---------------------------------------------------------------------
# /api/issues/map
# ---------------------------------------------------------------------


_FAKE_ISSUES_JSON = """[
  {"number": 1309, "title": "Monitor API audit",
   "labels": [{"name": "infrastructure"}, {"name": "priority:high"}],
   "body": "",
   "createdAt": "2026-04-15T00:00:00Z", "updatedAt": "2026-04-17T00:00:00Z",
   "assignees": [{"login": "claude"}], "url": "https://example/issues/1309"},
  {"number": 1142, "title": "V6 refactor",
   "labels": [{"name": "pipeline"}, {"name": "agent:codex"}],
   "body": "superseded-by: #1310\\n",
   "createdAt": "2026-04-10T00:00:00Z", "updatedAt": "2026-04-16T00:00:00Z",
   "assignees": [], "url": "https://example/issues/1142"},
  {"number": 1122, "title": "A2 build batch",
   "labels": [{"name": "content"}],
   "body": "merged-in PR #1200\\n",
   "createdAt": "2026-04-05T00:00:00Z", "updatedAt": "2026-04-15T00:00:00Z",
   "assignees": [{"login": "gemini"}], "url": "https://example/issues/1122"},
  {"number": 1100, "title": "Random noise",
   "labels": [],
   "body": "",
   "createdAt": "2026-04-01T00:00:00Z", "updatedAt": "2026-04-01T00:00:00Z",
   "assignees": [], "url": "https://example/issues/1100"}
]"""


def test_issues_map_buckets_by_category(monkeypatch):
    monkeypatch.setattr(
        issues_router, "_run_gh",
        lambda *_a, **_kw: (0, _FAKE_ISSUES_JSON, ""),
    )

    body = client.get("/api/issues/map").json()
    assert body["count"] == 4

    cats = body["categories"]
    # infrastructure wins over priority:high for #1309 because it comes
    # first in _CATEGORY_ORDER.
    assert cats["infrastructure"][0]["number"] == 1309
    assert cats["pipeline"][0]["number"] == 1142
    assert cats["content"][0]["number"] == 1122
    assert cats["other"][0]["number"] == 1100


def test_issues_map_extracts_supersedes_variant(monkeypatch):
    """Codex CONCERN: ``Supersedes #N`` wording was missed by the old regex."""
    fake = (
        '[{"number": 1184, "title": "Old plumbing",'
        ' "labels": [{"name": "pipeline"}],'
        ' "body": "Supersedes #1100\\nLanded in PR #1200",'
        ' "createdAt": null, "updatedAt": null, "assignees": [], "url": ""}]'
    )
    monkeypatch.setattr(
        issues_router, "_run_gh", lambda *_a, **_kw: (0, fake, ""),
    )
    body = client.get("/api/issues/map").json()
    item = body["categories"]["pipeline"][0]
    assert item["superseded_by"] == 1100
    assert item["merged_in_pr"] == 1200


def test_issues_map_extracts_supersede_and_merged_in(monkeypatch):
    monkeypatch.setattr(
        issues_router, "_run_gh",
        lambda *_a, **_kw: (0, _FAKE_ISSUES_JSON, ""),
    )

    body = client.get("/api/issues/map").json()
    by_num = {
        item["number"]: item
        for bucket in body["categories"].values()
        for item in bucket
    }
    assert by_num[1142]["superseded_by"] == 1310
    assert by_num[1122]["merged_in_pr"] == 1200
    assert "superseded_by" not in by_num[1309]


def test_issues_map_degrades_when_gh_missing(monkeypatch):
    monkeypatch.setattr(
        issues_router, "_run_gh",
        lambda *_a, **_kw: (127, "", "FileNotFoundError: gh not found"),
    )
    body = client.get("/api/issues/map").json()
    assert body["count"] == 0
    assert body["categories"] == {}
    assert "FileNotFoundError" in body["error"]


def test_issues_map_handles_invalid_json(monkeypatch):
    monkeypatch.setattr(
        issues_router, "_run_gh",
        lambda *_a, **_kw: (0, "not json{{{", ""),
    )
    body = client.get("/api/issues/map").json()
    assert body["count"] == 0
    assert "invalid gh json" in body["error"]


# ---------------------------------------------------------------------
# /api/runtime/auth
# ---------------------------------------------------------------------


def test_runtime_auth_reports_subscription_mode(monkeypatch, tmp_path):
    """GEMINI_AUTH_MODE=subscription → auth_mode: subscription + no keys exposed."""
    monkeypatch.setenv("GEMINI_AUTH_MODE", "subscription")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    # Redirect ``~/.gemini`` so oauth_creds lookup is deterministic.
    fake_home = tmp_path / "home"
    (fake_home / ".gemini").mkdir(parents=True)
    (fake_home / ".gemini" / "oauth_creds.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr("pathlib.Path.home", classmethod(lambda _: fake_home))

    body = client.get("/api/runtime/auth").json()
    assert body["gemini"]["auth_mode"] == "subscription"
    assert body["gemini"]["auth_mode_raw_valid"] is True
    assert body["gemini"]["auth_mode_raw_length"] == len("subscription")
    assert body["gemini"]["api_key_present"] is False
    assert body["gemini"]["google_key_present"] is False
    assert body["gemini"]["google_oauth_cred"] is True
    assert body["claude"]["api_key_present"] is False
    assert body["codex"]["api_key_present"] is False


def test_runtime_auth_reports_api_key_presence(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_AUTH_MODE", "api")
    monkeypatch.setenv("GEMINI_API_KEY", "secret")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-secret")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-secret")

    fake_home = tmp_path / "no-home"
    fake_home.mkdir()
    monkeypatch.setattr("pathlib.Path.home", classmethod(lambda _: fake_home))

    body = client.get("/api/runtime/auth").json()
    assert body["gemini"]["auth_mode"] == "api"
    assert body["gemini"]["api_key_present"] is True
    assert body["gemini"]["google_oauth_cred"] is False
    assert body["claude"]["source"] == "ANTHROPIC_API_KEY"
    assert body["codex"]["source"] == "OPENAI_API_KEY"
    # Keys themselves MUST NOT appear in the response.
    assert "secret" not in body["gemini"].get("api_key_value", "")
    assert all(
        "secret" not in str(v)
        for v in (body["gemini"], body["claude"], body["codex"])
    )


def test_runtime_auth_invalid_mode_uses_default_resolution(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_AUTH_MODE", "bogus-value")
    fake_home = tmp_path
    monkeypatch.setattr("pathlib.Path.home", classmethod(lambda _: fake_home))

    body = client.get("/api/runtime/auth").json()
    assert body["gemini"]["auth_mode"] == "api"
    # Raw is NOT echoed — just flagged as invalid with a length.
    assert body["gemini"]["auth_mode_raw_valid"] is False
    assert body["gemini"]["auth_mode_raw_length"] == len("bogus-value")


def test_runtime_auth_never_echoes_raw_env_value(monkeypatch, tmp_path):
    """Regression for Codex BLOCKER on #1312 pre-merge: if a secret
    is accidentally pasted into GEMINI_AUTH_MODE (typo in a shell
    profile, for example), it must NEVER appear in the response.

    The fixture value below is a high-entropy marker string, NOT a
    real key — it exists only so we can assert its absence in the
    response text. Kept alphanumeric and without the common
    ``sk-``/``api-`` prefixes so secret scanners don't flag it.
    """
    high_entropy_marker = "MARKERzzz9h7k3Q2xN5pW8vR4tY6uIaSdFgHjKlMn"
    monkeypatch.setenv("GEMINI_AUTH_MODE", high_entropy_marker)
    fake_home = tmp_path
    monkeypatch.setattr("pathlib.Path.home", classmethod(lambda _: fake_home))

    resp = client.get("/api/runtime/auth")
    assert resp.status_code == 200
    assert high_entropy_marker not in resp.text, (
        "runtime/auth must never echo the raw GEMINI_AUTH_MODE value"
    )
    body = resp.json()
    # The invalid flag + length still give operators enough to debug.
    assert body["gemini"]["auth_mode_raw_valid"] is False
    assert body["gemini"]["auth_mode_raw_length"] == len(high_entropy_marker)
