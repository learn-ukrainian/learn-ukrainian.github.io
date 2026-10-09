"""Prove the route-wide sanitizer strips leaked absolute paths.

Uses opaque placeholders only.  No real host paths, IPs, SSH aliases, or
occupancy maps appear in these fixtures.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api.lane_health import redact_lane_health_text
from scripts.api.opsec_sanitize import (
    REDACTED_ABSOLUTE_PATH,
    opsec_path_sanitizer_middleware,
    sanitize_document,
    sanitize_text,
)
from scripts.api.opsec_scan import scan_body, scan_text

pytestmark = pytest.mark.repo_invariant

PLANTED_ROOT = "/tmp/opsec-canary-root"
PLANTED_PATH = f"{PLANTED_ROOT}/repo"


@pytest.mark.parametrize("prose", ["~500K/1M", "~2/3", "~50/50", "~35/module"])
def test_numeric_tilde_prose_is_unchanged(prose):
    assert sanitize_text(f"Estimate `{prose}` today.") == f"Estimate `{prose}` today."


@pytest.mark.parametrize("path", [PLANTED_PATH, "~/.ssh/fixture-key", "~fixture/data", r"C:\Users\fixture\key.pem"])
def test_path_tokens_stop_at_backticks(path):
    assert redact_lane_health_text(f"Open `{path}`next.") == f"Open `{REDACTED_ABSOLUTE_PATH}`next."


@pytest.mark.parametrize("scope", [None, "core", "content", "task:cli", "full"])
def test_real_app_rules_json_preserves_source_bytes(scope):
    from scripts.api.main import create_app
    from scripts.api.monitor_context import fixture_context
    from scripts.api.rules_router import _assemble_scope

    root = Path(__file__).resolve().parents[3]
    expected, sources, digest = _assemble_scope(root, scope or "core")
    app = create_app(fixture_context(root))
    url = "/api/rules?format=json" + (f"&scope={scope}" if scope else "")
    response = TestClient(app).get(url)

    assert response.status_code == 200
    payload = response.json()
    assert payload["markdown"].encode("utf-8") == expected.encode("utf-8")
    assert payload["bytes"] == len(payload["markdown"].encode("utf-8"))
    assert payload["hash"] == digest
    assert payload["sources"] == sources


def test_sanitize_document_strips_planted_absolute_paths() -> None:
    leaked = {
        "ok": True,
        "nested": {"repo_root": PLANTED_PATH},
        "hint": f"store lives at {PLANTED_PATH}/data.sqlite",
        "safe_route": "/api/session-streams/v1/health",
        "sha": "0123456789abcdef" * 2 + "01234567",
    }

    before = scan_body(leaked)
    assert any(finding.kind == "filesystem-root" and PLANTED_PATH in finding.token for finding in before)

    sanitized = sanitize_document(leaked)
    encoded = json.dumps(sanitized)
    assert PLANTED_PATH not in encoded
    assert PLANTED_ROOT not in encoded
    assert "/tmp/" not in encoded
    assert sanitized["ok"] is True
    assert sanitized["safe_route"] == "/api/session-streams/v1/health"
    assert sanitized["nested"]["repo_root"] == REDACTED_ABSOLUTE_PATH
    assert REDACTED_ABSOLUTE_PATH in sanitized["hint"]
    assert scan_body(sanitized) == []
    assert scan_text(sanitized["hint"]) == []


def test_sanitize_document_strips_embedded_remote_capsule() -> None:
    """Family-5 shape: a pass-through document must not re-emit planted roots."""
    remote = {
        "primary_checkout": {"main_root": PLANTED_PATH},
        "checked_cwd": f"{PLANTED_PATH}/.worktrees/dispatch/agent/task",
    }
    leaked = {"board": {"orient": remote}}
    assert any(finding.kind == "filesystem-root" for finding in scan_body(leaked))

    sanitized = sanitize_document(leaked)
    encoded = json.dumps(sanitized)
    assert PLANTED_PATH not in encoded
    assert "/tmp/" not in encoded
    assert sanitized["board"]["orient"]["primary_checkout"]["main_root"] == REDACTED_ABSOLUTE_PATH
    assert scan_body(sanitized) == []


def test_middleware_strips_paths_that_a_bare_route_would_leak() -> None:
    def leak() -> dict[str, str]:
        return {"repo_root": PLANTED_PATH}

    bare = FastAPI()
    bare.get("/synthetic")(leak)
    leaked = TestClient(bare).get("/synthetic").json()
    assert leaked["repo_root"] == PLANTED_PATH
    assert any(finding.kind == "filesystem-root" for finding in scan_body(leaked))

    guarded = FastAPI()
    guarded.middleware("http")(opsec_path_sanitizer_middleware)
    guarded.get("/synthetic")(leak)
    sanitized = TestClient(guarded).get("/synthetic").json()
    assert PLANTED_PATH not in json.dumps(sanitized)
    assert sanitized["repo_root"] == REDACTED_ABSOLUTE_PATH
    assert scan_body(sanitized) == []


def test_repeated_strings_scan_once_without_cross_document_cache(monkeypatch):
    """Large projections repeat values; memoization must remain request-local."""
    from scripts.api import opsec_sanitize

    original = opsec_sanitize.scan_text
    calls = []

    def counted(text):
        calls.append(text)
        return original(text)

    monkeypatch.setattr(opsec_sanitize, "scan_text", counted)
    path = "/home/synthetic-private/project/file.json"
    safe = "public-monitor"
    payload = {"items": [{"title": path, "source": safe}] * 20, "attention": [{"title": path, "source": safe}] * 20}
    sanitized = opsec_sanitize.sanitize_document(payload)
    assert calls == [path, safe]
    assert all(row["title"] == "[redacted-path]" for rows in sanitized.values() for row in rows)
    assert payload["items"][0]["title"] == path
    opsec_sanitize.sanitize_document(payload)
    assert calls == [path, safe, path, safe]


def test_memo_preserves_equal_distinct_unchanged_values():
    from scripts.api.opsec_sanitize import sanitize_document

    first = "".join(["public", "-monitor"])
    second = "".join(["public-", "monitor"])
    assert first == second and first is not second
    payload = {"list": [first, second], "tuple": (first, second)}
    assert sanitize_document(payload) is payload
