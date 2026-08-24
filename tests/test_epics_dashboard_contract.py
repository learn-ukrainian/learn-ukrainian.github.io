"""Dashboard and route-registration contract for the Epics overview UI (#7186)."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scripts.api.main import app
from scripts.api.route_contracts import contract_for_page, contract_for_route

ROOT = Path(__file__).resolve().parents[1]
DASHBOARDS = ROOT / "dashboards"
EPICS_HTML = DASHBOARDS / "epics.html"


def test_epics_page_is_a_read_only_observer() -> None:
    html = EPICS_HTML.read_text(encoding="utf-8")

    assert 'data-read-only="true"' in html
    assert "Remote lifecycle · TTL-fenced" in html
    assert "Registered epics and active drivers." in html
    assert "Remote authority" in html
    assert "Read-only operator dashboard." in html
    assert "/api/epics/v1" in html
    assert "/api/epics/v1/" in html
    assert "githubIssueUrl" in html
    assert "formatHolder" in html
    assert "getLeaseState" in html
    assert "formatAge" in html
    assert "formatExpiry" in html
    assert 'class="monitor-nav"' in html
    assert '<a class="active" href="/epics.html">Epics</a>' in html
    assert '<link rel="stylesheet" href="/monitor.css">' in html
    assert 'id="error-banner"' in html
    assert 'id="btn-refresh"' in html
    assert 'id="last-updated-text"' in html
    assert 'id="epics-tbody"' in html
    assert 'id="detail-pane"' in html

    # Strict read-only invariant: no mutating POST/PUT/DELETE forms or fetch methods
    for prohibited in (
        "<form",
        "method: 'POST'",
        'method: "POST"',
        "method: 'PUT'",
        'method: "PUT"',
        "method: 'DELETE'",
        'method: "DELETE"',
        "/claim",
        "/heartbeat",
        "/handoff",
        "/release",
    ):
        assert prohibited not in html


def test_epics_page_opsec_and_privacy_guarantees() -> None:
    html = EPICS_HTML.read_text(encoding="utf-8")

    # The HTML template itself must not embed raw private paths or IP addresses
    assert "/Users/" not in html
    assert "/home/" not in html
    assert "127.0.0.1" not in html
    assert "localhost:" not in html
    assert "#0d1117" not in html  # shared parchment design


def test_epics_page_contract_and_index_registration() -> None:
    contract = contract_for_page("epics.html")
    assert contract is not None
    assert contract.url == "/epics.html"
    assert "/api/epics/v1" in contract.source_of_truth
    assert "15s" in contract.freshness
    assert "read-only" in contract.purpose.lower()

    route_contract = contract_for_route("/api/epics/v1", "http")
    assert route_contract is not None
    assert route_contract.pattern == "/api/epics/v1"

    index_html = (DASHBOARDS / "index.html").read_text(encoding="utf-8")
    assert 'href="/epics.html"' in index_html
    assert ">Epics<" in index_html


def test_epics_page_serves_over_http() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/epics.html")
    assert response.status_code == 200
    assert "Registered epics and active drivers." in response.text


def test_epics_page_js_behavioral_logic() -> None:
    """Evaluate epics.html JS formatting and state predicates in Node."""
    if shutil.which("node") is None:
        pytest.skip("node required for JS parity check")

    html_path = json.dumps(str(EPICS_HTML))
    script = f"""
    const fs = require('fs');
    const html = fs.readFileSync({html_path}, 'utf8');
    const start = html.indexOf('function escapeHtml(');
    const end = html.indexOf('async function fetchJson(');
    if (start < 0 || end <= start) throw new Error('helper block not found');
    eval(html.slice(start, end));

    const now = Date.now();
    const futureExpiry = new Date(now + 600000).toISOString(); // 10 mins
    const pastExpiry = new Date(now - 60000).toISOString(); // 1 min ago

    const results = {{
      ghValid: githubIssueUrl('epic:6943'),
      ghInvalid: githubIssueUrl('custom:stream'),
      ghNull: githubIssueUrl(null),
      holderFull: formatHolder({{ agent: 'claude', harness: 'claude-code', host_id: 'local' }}),
      holderPartial: formatHolder({{ agent: 'codex', harness: null, host_id: 'host-job' }}),
      holderEmpty: formatHolder({{}}),
      holderNull: formatHolder(null),
      stateActive: getLeaseState({{ lease: {{ state: 'active', expires_at: futureExpiry }} }}),
      stateExpiredByTime: getLeaseState({{ lease: {{ state: 'active', expires_at: pastExpiry }} }}),
      stateReleased: getLeaseState({{ lease: {{ state: 'released', expires_at: futureExpiry }} }}),
      stateNone: getLeaseState({{ lease: null }}),
      ageSecs: formatAge(184),
      ageMins: formatAge(45),
      ageNull: formatAge(null),
      expiryActive: formatExpiry({{ expires_at: futureExpiry, state: 'active' }}),
      expiryExpired: formatExpiry({{ expires_at: pastExpiry, state: 'active' }}),
      expiryReleased: formatExpiry({{ expires_at: futureExpiry, state: 'released' }}),
      expiryNone: formatExpiry(null),
    }};
    console.log(JSON.stringify(results));
    """
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True, timeout=30)
    out = json.loads(result.stdout)

    assert out["ghValid"] == "https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6943"
    assert out["ghInvalid"] is None
    assert out["ghNull"] is None

    assert out["holderFull"] == "claude · claude-code · local"
    assert out["holderPartial"] == "codex · — · host-job"
    assert out["holderEmpty"] == "—"
    assert out["holderNull"] == "—"

    assert out["stateActive"] == "active"
    assert out["stateExpiredByTime"] == "expired"
    assert out["stateReleased"] == "released"
    assert out["stateNone"] == "none"

    assert out["ageSecs"] == "3m 4s ago"
    assert out["ageMins"] == "45s ago"
    assert out["ageNull"] == "—"

    assert "in 10m" in out["expiryActive"] or "in 9m" in out["expiryActive"]
    assert out["expiryExpired"] == "expired"
    assert out["expiryReleased"] == "—"
    assert out["expiryNone"] == "—"
