"""Behavioral regressions for Monitor loading and honest queue evidence (#7684)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scripts.api import work_router
from scripts.api.main import app

ROOT = Path(__file__).resolve().parents[2]


def _node(script: str) -> None:
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr


def _script(page: str, start: str, end: str) -> str:
    html = (ROOT / "dashboards" / page).read_text()
    return html[html.index(start) : html.index(end, html.index(start))]


@pytest.mark.parametrize("source_status", ["ok", "degraded", "unavailable"])
def test_next_empty_queue_preserves_source_completeness(monkeypatch, source_status):
    source = {
        "source_id": "public-monitor",
        "status": source_status,
        "sections": {"issues": {"status": "ok" if source_status == "ok" else "timeout", "count": 0}},
    }
    denominator = {
        "issues_open": 0,
        "omissions": [] if source_status == "ok" else [{"class": "issues", "reason": "timeout"}],
    }
    payload = {
        "items": [],
        "sources": [source, {"source_id": "private-local-adapter", "status": "unavailable"}],
        "denominator": denominator,
        "generated_at": "2026-09-04T00:00:00Z",
    }
    monkeypatch.setattr(work_router, "_known_streams", lambda _ctx: ["infra-harness"])
    monkeypatch.setattr(work_router, "cache_get_with_age", lambda *_args: (payload, 1.0))
    response = TestClient(app).get("/api/work/v1/next?stream=infra-harness")
    assert response.status_code == 200
    assert response.json()["queue"] == []
    assert response.json()["sources"] == [source]
    assert response.json()["denominator"] == denominator


def test_projection_direct_json_retains_opsec_middleware(monkeypatch):
    payload = {"items": [{"title": "/home/synthetic-private/data.json"}], "attention": [], "cache_age_s": 0}
    monkeypatch.setattr(work_router, "cache_get_with_age", lambda *_args: (payload, 1.0))
    response = TestClient(app).get("/api/work/v1/projection")
    assert response.status_code == 200
    assert response.json()["items"] == [{"title": "[redacted-path]"}]
    assert response.json()["cache_age_s"] == 1.0
    assert payload["items"][0]["title"] == "/home/synthetic-private/data.json"


_DOM = r"""
const assert = require('node:assert/strict');
const elements = new Map();
const document = {getElementById(id) {
  if (!elements.has(id)) elements.set(id, {textContent: 'old data', innerHTML: 'old data', className: '',
    setAttribute() {}, classList: {toggle() {}, add() {}, remove() {}}});
  return elements.get(id);
}};
const tick = () => new Promise(resolve => setImmediate(resolve));
"""


def test_runtime_panels_paint_independently_and_empty_is_not_error():
    code = _script("runtime.html", "let runtimeLoading", "\nfunction refreshRuntime")
    _node(
        _DOM
        + r"""
const calls = [], painted = [], banners = {};
let resolveAcpx;
const pendingAcpx = new Promise(resolve => {resolveAcpx = resolve;});
const fetchJson = async url => {
  calls.push(url);
  if (url.includes('/acpx')) return pendingAcpx;
  if (url.endsWith('/agents')) return {agents: []};
  if (url.includes('/routing-assignments')) throw new Error('unavailable');
  return {};
};
const setBanner = (id, text) => banners[id] = text;
const renderAgents = () => painted.push('agents');
const renderUsage = () => painted.push('usage');
const renderRecent = () => painted.push('recent');
const renderAcpx = () => painted.push('acpx');
const renderRoutingAssignments = () => {};
const renderHeadroom = () => {};
"""
        + code
        + r"""
(async () => {
  const first = loadRuntime();
  await tick();
  assert.deepEqual(painted.sort(), ['agents', 'recent', 'usage']);
  assert.equal(calls.length, 5);
  await loadRuntime();
  assert.equal(calls.length, 5, 'overlap must not duplicate requests');
  assert.match(document.getElementById('headroom-content').innerHTML, /No runtime agents/);
  assert.equal(banners['headroom-banner'], '');
  assert.match(document.getElementById('routing-assignments-status').textContent, /unknown/);
  resolveAcpx({});
  await first;
  assert.match(document.getElementById('last-refresh').textContent, /Refresh attempted/);
})().catch(e => {console.error(e); process.exitCode = 1;});
"""
    )


def test_runtime_failed_agent_inventory_does_not_claim_empty_headroom():
    code = _script("runtime.html", "let runtimeLoading", "\nfunction refreshRuntime")
    _node(
        _DOM
        + r"""
const fetchJson = async url => {if (url.endsWith('/agents')) throw new Error('unavailable'); return {};};
const setBanner = () => {};
const renderAgents = () => {}, renderUsage = () => {}, renderRecent = () => {};
const renderAcpx = () => {}, renderRoutingAssignments = () => {}, renderHeadroom = () => {};
"""
        + code
        + r"""
loadRuntime().then(() => {
  assert.match(document.getElementById('headroom-content').innerHTML, /Unable to load/);
}).catch(e => {console.error(e); process.exitCode = 1;});
"""
    )


def test_monitor_http_failure_clears_previous_capacity():
    code = _script("runtime.html", "async function refreshAgentMonitor", "document.addEventListener('DOMContentLoaded'")
    _node(
        _DOM
        + "const fetch = async () => ({ok: false});\n"
        + code
        + r"""
refreshAgentMonitor().then(() => {
  assert.equal(document.getElementById('agent-monitor-status-badge').textContent, 'UNAVAILABLE');
  for (const id of ['ram-avail', 'sys-load', 'active-leases-count', 'reserved-ram'])
    assert.equal(document.getElementById(id).textContent, 'Unknown');
}).catch(e => {console.error(e); process.exitCode = 1;});
"""
    )


def test_fleet_failed_panels_clear_old_data_and_old_refresh_cannot_overwrite():
    code = _script("fleet.html", "let fleetGeneration", "\nfunction queueRefresh")
    _node(
        _DOM
        + r"""
let resolveOld, old = true;
const errors = [], occupancyAttention = [];
const oldResponse = new Promise(resolve => {resolveOld = resolve;});
const fetchJson = async url => {
  if (old) return oldResponse;
  if (url === '/api/occupancy' || url === '/api/fleet/health') throw new Error('failed');
  return {marker: 'new'};
};
const query = url => url;
const setError = text => errors.push(text);
const renderHealth = data => {document.getElementById('plane-status').textContent = data.marker;};
const renderOccupancy = data => {document.getElementById('occupancy-content').textContent = data.marker;};
const renderOccupancyAttention = data => occupancyAttention.push(data);
const renderOverview = () => {}, renderOperations = () => {}, renderRequests = () => {};
const renderAuthorityJobs = () => {}, renderReviews = () => {}, renderAcp = () => {};
const renderDeadLetters = () => {}, renderWorkers = () => {}, renderProjects = () => {};
const renderActivity = () => {}, renderMessages = () => {}, refreshConversationContext = async () => {};
"""
        + code
        + r"""
(async () => {
  const first = refreshFleet();
  old = false;
  await refreshFleet();
  assert.match(document.getElementById('occupancy-content').textContent, /Unavailable/);
  assert.match(document.getElementById('plane-status').textContent, /Unavailable/);
  assert.deepEqual(occupancyAttention, [[]]);
  assert.match(errors.at(-1), /Observer data could not be read/);
  resolveOld({marker: 'stale'});
  await first;
  assert.match(document.getElementById('occupancy-content').textContent, /Unavailable/);
  assert.match(document.getElementById('plane-status').textContent, /Unavailable/);
})().catch(e => {console.error(e); process.exitCode = 1;});
"""
    )


@pytest.mark.parametrize("body", ["not-json", "null", "[]"])
def test_fleet_invalid_json_is_an_error(body):
    code = _script("fleet.html", "async function fetchJson", "\nfunction setError")
    _node(
        _DOM
        + "const API_TIMEOUT_MS = 1000;\nconst fetch = async () => ({ok: true, text: async () => "
        + json.dumps(body)
        + "});\n"
        + code
        + r"""
assert.rejects(fetchJson('/fixture'), /Invalid/).catch(e => {console.error(e); process.exitCode = 1;});
"""
    )


def test_work_new_refresh_wins_while_private_is_pending():
    code = _script("work.html", "  let projectionGeneration", "\n  function refilterOnly")
    _node(
        _DOM
        + r"""
const pending = [], installed = [];
const PUBLIC_PROJECTION_URL = '/public', PRIVATE_PROJECTION_URL = '/private', PRIVATE_TIMEOUT_MS = 5000;
const state = {};
const showError = () => {};
const installView = doc => installed.push(doc.marker);
const admitPublicDocument = doc => ({ok: true, doc});
const fetchJson = url => new Promise((resolve, reject) => pending.push({url, resolve, reject}));
const classifyPrivateFailure = () => 'unreachable';
const privateMetaFromCode = code => code;
"""
        + code
        + r"""
(async () => {
  const first = loadProjection();
  const second = loadProjection();
  pending[2].resolve({marker: 'new'});
  await tick();
  assert.deepEqual(installed, ['new']);
  assert.equal(state.privateStatusText, 'Checking capability…');
  pending[0].resolve({marker: 'old'});
  pending[1].reject(new Error('old private unavailable'));
  await first;
  assert.deepEqual(installed, ['new']);
  pending[3].reject(new Error('private unavailable'));
  await second;
  assert.deepEqual(installed, ['new', 'new']);
})().catch(e => {console.error(e); process.exitCode = 1;});
"""
    )
