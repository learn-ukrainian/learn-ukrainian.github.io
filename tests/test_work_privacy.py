"""Privacy oracle for the public Work foundation + browser-local private boundary."""

from __future__ import annotations

import re
from pathlib import Path

from fastapi.testclient import TestClient

import scripts.api.work_router as work_router
from scripts.api.main import app
from scripts.api.state_helpers import cache_invalidate
from scripts.work.normalize import build_projection
from scripts.work.schema import SchemaValidationError, parse_saved_view_params
from scripts.work.sources_public import SectionResult, private_capability_seam

ROOT = Path(__file__).resolve().parents[1]
CANARY_FILE = ROOT / "tests" / "fixtures" / "work" / "fx07_canaries.txt"
PRIVATE_URL = "http://127.0.0.1:8769/v1/projection"
# Product + fixture surfaces only. Privacy tests may inject canaries as inputs;
# the oracle asserts they never appear in public outputs or non-test artifacts.
WORK_OWNED = [
    ROOT / "scripts" / "work",
    ROOT / "scripts" / "api" / "work_router.py",
    ROOT / "dashboards" / "work.html",
    ROOT / "tests" / "fixtures" / "work",
    ROOT / "docs" / "decisions" / "ADR-019-work-control-plane.md",
    ROOT / "docs" / "monitor-api" / "work.md",
    ROOT / "tests" / "test_work_dashboard.py",
    ROOT / "tests" / "test_work_privacy.py",
    ROOT / "tests" / "test_work_dashboard_private_integration.py",
]

client = TestClient(app, raise_server_exceptions=False)


def _load_canaries() -> list[str]:
    values: list[str] = []
    for line in CANARY_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        values.append(line.split("=", 1)[1].strip())
    assert len(values) >= 3
    return values


def test_fx07_canaries_never_enter_public_api_payload(monkeypatch):
    """FX-07: injected private canaries never appear in the public projection payload."""
    canaries = _load_canaries()
    cache_invalidate("work:v1:projection")
    body_canary, secret_canary, path_canary, *_rest = [*canaries, ""]

    sections = {
        "issues": SectionResult(
            "issues",
            "ok",
            payload=[
                {
                    "number": 1,
                    "title": "Public title only",
                    "labels": [],
                    "assignees": [],
                    "body": body_canary,
                    "createdAt": "2026-08-01T00:00:00Z",
                    "updatedAt": "2026-08-01T00:00:00Z",
                    "url": "https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1",
                    "state": "OPEN",
                }
            ],
            count=1,
        ),
        "prs": SectionResult("prs", "ok", payload=[], count=0),
        "streams": SectionResult(
            "streams",
            "ok",
            payload={
                "orphans": [],
                "multi_homed": [],
                "pending_native_link": [],
                "open_total": 1,
                "effective_membership": {"1": path_canary},
                "open_issue_numbers": [1],
            },
            count=1,
        ),
        "delegate_active": SectionResult(
            "delegate_active", "ok", payload={"total": 0, "tasks": []}, count=0
        ),
        "delegate_tasks": SectionResult(
            "delegate_tasks",
            "ok",
            payload={
                "total": 1,
                "tasks": [
                    {
                        "task_id": "t1",
                        "agent": "codex",
                        "status": "done",
                        "result": secret_canary,
                        "result_file": path_canary,
                    }
                ],
            },
            count=1,
        ),
        "fleet_reviews": SectionResult(
            "fleet_reviews",
            "ok",
            payload={
                "total": 0,
                "reviews": [
                    {
                        "review_id": "r1",
                        "sealed_verdict_available": True,
                        "sealed_blob": secret_canary,
                    }
                ],
            },
            count=0,
        ),
    }

    monkeypatch.setattr(
        work_router,
        "build_public_projection",
        lambda **kwargs: build_projection(
            sections,
            repository_id="learn-ukrainian/learn-ukrainian.github.io",
            **{k: v for k, v in kwargs.items() if k in {"filters", "cache_age_s"}},
        ),
    )

    response = client.get("/api/work/v1/projection")
    assert response.status_code == 200
    blob = response.text
    for canary in canaries:
        assert canary not in blob, f"canary leaked into API: {canary}"

    data = response.json()
    assert data["capabilities"]["private_source"]["available"] is False
    assert data["capabilities"]["private_source"]["endpoint"] is None


def test_private_capability_seam_is_truthful_and_non_proxying():
    seam = private_capability_seam()
    assert seam["available"] is False
    assert seam["reason_if_unavailable"] == "not_configured"
    assert seam["endpoint"] is None
    # Public router module must not implement private HTTP fetch helpers.
    source = (ROOT / "scripts" / "api" / "work_router.py").read_text(encoding="utf-8")
    assert "requests.get" not in source
    assert "httpx" not in source
    assert "private-local-adapter" in source or "private_capability" in source
    # Public server must never hardcode the private loopback adapter URL.
    assert PRIVATE_URL not in source
    assert "127.0.0.1:8769" not in source


def test_saved_view_urls_reject_private_values():
    try:
        parse_saved_view_params({"endpoint": "http://127.0.0.1:9999/v1"})
        raised = False
    except SchemaValidationError:
        raised = True
    assert raised
    try:
        parse_saved_view_params({"favorite": "my private board"})
        raised = False
    except SchemaValidationError:
        raised = True
    assert raised


def test_owned_paths_and_work_html_have_no_canaries_or_private_paths():
    canaries = _load_canaries()
    private_path_re = re.compile(r"/Users/[^\"'\s]+/learn-ukrainian-infra-private")
    for path in WORK_OWNED:
        if not path.exists():
            continue
        files = [path] if path.is_file() else sorted(path.rglob("*"))
        for file in files:
            if not file.is_file():
                continue
            if file.name == "fx07_canaries.txt":
                continue
            text = file.read_text(encoding="utf-8", errors="replace")
            for canary in canaries:
                assert canary not in text, f"{file}: contains canary"
            assert private_path_re.search(text) is None, f"{file}: private checkout path"


def test_work_html_is_read_only_and_browser_local_private_only():
    """FX-10 + FX-09 adjacent: work.html stays read-only; private URL is fixed/non-configurable."""
    html = (ROOT / "dashboards" / "work.html").read_text(encoding="utf-8")
    assert 'data-read-only="true"' in html
    assert "FOUNDATION_COMPLETE" in html
    assert "/api/work/v1/projection" in html
    assert PRIVATE_URL in html
    assert "method: 'POST'" not in html
    assert 'method: "POST"' not in html
    assert "method: 'PUT'" not in html
    assert "method: 'PATCH'" not in html
    assert "method: 'DELETE'" not in html
    assert "dispatch" in html.lower()  # mention only
    # Fixed private URL only; no configurability surfaces.
    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert "document.cookie" not in html
    assert "private_endpoint" in html  # explicitly rejected
    # Must not hardcode private absolute paths or private host canaries
    for canary in _load_canaries():
        assert canary not in html


def test_public_server_owned_python_never_imports_private_adapter_url():
    """Architecture invariant: only browser JS may fetch the fixed private URL."""
    server_paths = [
        ROOT / "scripts" / "api" / "work_router.py",
        ROOT / "scripts" / "work",
    ]
    for path in server_paths:
        files = [path] if path.is_file() else sorted(path.rglob("*.py"))
        for file in files:
            text = file.read_text(encoding="utf-8", errors="replace")
            assert PRIVATE_URL not in text, f"{file} embeds private adapter URL"
            assert "8769/v1/projection" not in text, f"{file} embeds private adapter path"
