"""Prove the route-wide sanitizer strips leaked absolute paths.

Uses opaque placeholders only.  No real host paths, IPs, SSH aliases, or
occupancy maps appear in these fixtures.
"""

from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api.opsec_sanitize import (
    REDACTED_ABSOLUTE_PATH,
    opsec_path_sanitizer_middleware,
    sanitize_document,
)
from scripts.api.opsec_scan import scan_body, scan_text

pytestmark = pytest.mark.repo_invariant

PLANTED_ROOT = "/tmp/opsec-canary-root"
PLANTED_PATH = f"{PLANTED_ROOT}/repo"


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
