"""Dashboard and route-registration contract for the Epics overview UI (#7186)."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DASHBOARDS = ROOT / "dashboards"
EPICS_HTML = DASHBOARDS / "epics.html"


def test_epics_page_opsec_and_privacy_guarantees() -> None:
    html = EPICS_HTML.read_text(encoding="utf-8")

    # The HTML template itself must not embed raw private paths or IP addresses
    assert "/Users/" not in html
    assert "/home/" not in html
    assert "127.0.0.1" not in html
    assert "localhost:" not in html
    assert "#0d1117" not in html  # shared parchment design


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
      neverClaimed: displayLeaseState({{ registered: true, lease: null }}),
      noLease: displayLeaseState({{ registered: false, lease: null }}),
      registryRegistered: registryState({{ registered: true }}),
      registryStale: registryState({{ registered: false, stream_name: 'legacy' }}),
      registryStoreOnly: registryState({{ registered: false }}),
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
    assert out["neverClaimed"] == "Never claimed"
    assert out["noLease"] == "No lease"
    assert out["registryRegistered"] == "registered"
    assert out["registryStale"] == "stale"
    assert out["registryStoreOnly"] == "store-only"

    assert out["ageSecs"] == "3m 4s ago"
    assert out["ageMins"] == "45s ago"
    assert out["ageNull"] == "—"

    assert "in 10m" in out["expiryActive"] or "in 9m" in out["expiryActive"]
    assert out["expiryExpired"] == "expired"
    assert out["expiryReleased"] == "—"
    assert out["expiryNone"] == "—"
