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


def _retained_script(page: str, start: str, end: str) -> str:
    return _script(page, "const retainedPanels", "// End retained panel clocks.") + _script(page, start, end)


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
// Run page clocks without keeping the subprocess alive after its assertions finish.
const setInterval = (...args) => require('node:timers').setInterval(...args).unref();
const elements = new Map();
const makeElement = () => ({textContent: 'old data', innerHTML: 'old data', className: '',
  dataset: {}, style: {}, after(node) {this.nextElementSibling = node;},
  setAttribute(key, value) {this[key] = value;}, classList: {toggle() {}, add() {}, remove() {}}});
const document = {createElement: makeElement, querySelectorAll: () => [], getElementById(id) {
  if (!elements.has(id)) elements.set(id, makeElement());
  return elements.get(id);
}};
const tick = () => new Promise(resolve => setImmediate(resolve));
"""


def test_runtime_panels_paint_independently_and_empty_is_not_error():
    code = _retained_script("runtime.html", "const runtimeTargets", "\nfunction setBanner") + _script(
        "runtime.html", "let runtimeLoading", "\nfunction refreshRuntime"
    )
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
  if (url.includes('/usage')) return {by_agent: {}};
  if (url.includes('/recent')) return {records: []};
  throw new Error(`Unexpected URL: ${url}`);
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
  resolveAcpx({seats: [], transport: {}});
  await first;
  assert.match(document.getElementById('last-refresh').textContent, /Refresh attempted/);
})().catch(e => {console.error(e); process.exitCode = 1;});
"""
    )


def test_runtime_failed_agent_inventory_does_not_claim_empty_headroom():
    code = _retained_script("runtime.html", "const runtimeTargets", "\nfunction setBanner") + _script(
        "runtime.html", "let runtimeLoading", "\nfunction refreshRuntime"
    )
    _node(
        _DOM
        + r"""
const fetchJson = async url => {
  if (url.endsWith('/agents')) throw new Error('unavailable');
  if (url.includes('/usage')) return {by_agent: {}};
  if (url.includes('/recent')) return {records: []};
  if (url.includes('/acpx')) return {seats: [], transport: {}};
  if (url.includes('/routing-assignments')) return {assignments: []};
  throw new Error(`Unexpected URL: ${url}`);
};
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
    code = _retained_script(
        "runtime.html", "async function refreshAgentMonitor", "document.addEventListener('DOMContentLoaded'"
    )
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
    code = _retained_script("fleet.html", "function validateFleetPanel", "\nfunction queueRefresh")
    _node(
        _DOM
        + r"""
let resolveOld, old = true;
const errors = [], occupancyAttention = [];
const oldResponse = new Promise(resolve => {resolveOld = resolve;});
const fixtures = {
  '/api/fleet/health': {authority_health: {}},
  '/api/fleet/overview': {counts: {}},
  '/api/fleet/operations': {broker: {}, zombies: {}, batches: {}},
  '/api/fleet/authority/jobs': {jobs: []},
  '/api/fleet/reviews': {reviews: []},
  '/api/fleet/acp/conversations': {conversations: []},
  '/api/fleet/dead-letters': {dead_letters: []},
  '/api/fleet/workers/v1': {hosts: []},
  '/api/occupancy': {hosts: {}, attention: []},
  '/api/fleet/projects/v1': {hosts: {}},
  '/api/fleet/activity': {records: []},
  '/api/fleet/messages': {messages: []},
  '/api/ops/entire-context/status': {recall: {}},
};
const fetchJson = async url => {
  assert.ok(url in fixtures, `Unexpected URL: ${url}`);
  if (old) return {...fixtures[url], ...await oldResponse};
  if (url === '/api/occupancy' || url === '/api/fleet/health') throw new Error('failed');
  return {...fixtures[url], marker: 'new'};
};
const query = url => url;
const setError = text => errors.push(text);
const renderHealth = data => {document.getElementById('plane-status').textContent = data.marker;};
const renderOccupancy = data => {document.getElementById('occupancy-content').textContent = data.marker;};
const renderOccupancyAttention = data => occupancyAttention.push(data);
const renderOverview = data => {document.getElementById('requests-total').textContent = data.marker;};
const renderOperations = () => {}, renderRequests = () => {};
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
  assert.equal(document.getElementById('requests-total').textContent, 'new');
  assert.match(document.getElementById('occupancy-content').textContent, /Unavailable/);
  assert.match(document.getElementById('plane-status').textContent, /Unavailable/);
  assert.deepEqual(occupancyAttention, [[]]);
  assert.match(errors.at(-1), /Observer data could not be read/);
  resolveOld({marker: 'stale'});
  await first;
  assert.equal(document.getElementById('requests-total').textContent, 'new');
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
    code = _retained_script("work.html", "  function recordWorkFetch", "\n  function refilterOnly")
    _node(
        _DOM
        + r"""
const pending = [], installed = [];
const PUBLIC_PROJECTION_URL = '/public', PRIVATE_PROJECTION_URL = '/private', PRIVATE_TIMEOUT_MS = 5000;
const PUBLIC_SOURCE_ID = 'public-monitor', PRIVATE_SOURCE_ID = 'private-local-adapter';
const state = {receivedAt: new Map()};
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
  pending[2].resolve({marker: 'new', sources: [{source_id: PUBLIC_SOURCE_ID, status: 'ok'}]});
  await tick();
  assert.deepEqual(installed, ['new']);
  assert.equal(state.privateStatusText, 'Checking capability…');
  pending[0].resolve({marker: 'old', sources: [{source_id: PUBLIC_SOURCE_ID, status: 'ok'}]});
  pending[1].reject(new Error('old private unavailable'));
  await first;
  assert.deepEqual(installed, ['new']);
  pending[3].reject(new Error('private unavailable'));
  await second;
  assert.deepEqual(installed, ['new', 'new']);
})().catch(e => {console.error(e); process.exitCode = 1;});
"""
    )


def test_cleared_work_selection_stays_clear_until_private_settles():
    install = _script("work.html", "  function installView", "  function recordWorkFetch")
    keyboard = _script("work.html", "  document.addEventListener('keydown'", "  applyFiltersToControls")
    _node(
        _DOM
        + r"""
const details = [];
const state = {selectedId: null, selectedIndex: -1, selectionCleared: false, attention: [], itemsById: new Map()};
const els = {cmd: {classList: {contains() { return false; }}}, list: {focus() {}}, cmdInput: {}};
const listeners = {};
document.addEventListener = (type, fn) => { listeners[type] = fn; };
const controlsToFilters = () => ({view: 'all'});
const writeFiltersToUrl = () => {};
const applyLocalFilters = projection => ({items: projection.items, attention: projection.attention, filteredCount: 0, totalMatching: projection.items.length});
const renderSources = () => {};
const renderActionableBanner = () => {};
const renderList = () => {};
const renderDetail = item => details.push(item ? item.work_id : null);
const selectIndex = () => { state.selectionCleared = false; state.selectedId = 'chosen'; };
const openPalette = () => {};
const closePalette = () => {};
"""
        + install
        + keyboard
        + r"""
const doc = {items: [{work_id: 'public-row'}], attention: [{work_id: 'public-row'}]};
installView(doc, {deferSelection: true});
assert.equal(state.selectedId, null, 'public-first must not select before private settles');
listeners.keydown({key: 'Escape', target: {tagName: 'DIV'}, preventDefault() {}});
assert.equal(state.selectionCleared, true);
assert.equal(state.selectedId, null);
installView(doc);
assert.equal(state.selectedId, null, 'cleared selection stays cleared');
assert.equal(details.at(-1), null);
state.selectionCleared = false;
installView(doc);
assert.equal(state.selectedId, 'public-row');
"""
    )


def test_stale_monitor_failure_does_not_overwrite_newer_success():
    code = _retained_script(
        "runtime.html", "async function refreshAgentMonitor", "document.addEventListener('DOMContentLoaded'"
    )
    _node(
        _DOM
        + r"""
let releaseOld;
const oldFetch = new Promise(resolve => { releaseOld = resolve; });
let calls = 0;
const fetch = async () => {
  calls += 1;
  if (calls === 1) {
    await oldFetch;
    return {ok: false};
  }
  return {ok: true, json: async () => ({severity: 'healthy', ram: {available_mb: 1, total_mb: 2, used_percent: 10},
    load_1m_5m_15m: [0, 0], capacity_reservations: {active_leases_count: 0, total_reserved_ram_mb: 0}})};
};
"""
        + code
        + r"""
(async () => {
  const older = refreshAgentMonitor();
  const newer = refreshAgentMonitor();
  await newer;
  assert.equal(document.getElementById('agent-monitor-status-badge').textContent, 'HEALTHY');
  assert.equal(String(document.getElementById('active-leases-count').textContent), '0');
  releaseOld();
  await older;
  assert.equal(document.getElementById('agent-monitor-status-badge').textContent, 'HEALTHY');
  assert.notEqual(document.getElementById('agent-monitor-status-badge').textContent, 'UNAVAILABLE');
})().catch(e => {console.error(e); process.exitCode = 1;});
"""
    )


def test_missing_counts_stay_unknown_and_observed_zero_stays_zero():
    work = _script("work.html", "  function sectionCount", "  function publicStreamsComplete")
    runtime = _script("runtime.html", "function segment", "function renderHeadroom")
    fleet = _script("fleet.html", "function summaryDetail", "function renderHealth") + _script(
        "fleet.html", "function renderOverview", "function renderContextHealth"
    )
    cost = _script("cost.html", "function fmtInt", "async function fetchJson") + _script(
        "cost.html", "function renderWarnings", "function renderSummary"
    )
    _node(
        _DOM
        + "const escapeHtml = value => String(value ?? '');\nconst formatDuration = () => 'unknown';\nconst esc = value => String(value ?? '');\n"
        + work
        + runtime
        + fleet
        + cost
        + r"""
assert.equal(sectionCount({}, 'issues'), 'unknown');
assert.equal(sectionCount({issues: {status: 'ok'}}, 'issues'), 'unknown');
assert.equal(sectionCount({issues: {count: 0}}, 'issues'), 0);
assert.equal(sectionCount({prs: {count: 2}}, 'prs'), 2);
renderUsage({});
assert.match(document.getElementById('usage-content').innerHTML, /Usage count unknown/);
assert.doesNotMatch(document.getElementById('usage-content').innerHTML, /\b0\b/);
renderUsage({safe: {total: 0, ok: 0}});
assert.match(document.getElementById('usage-content').innerHTML, /0 calls/);
renderOverview({counts: {}});
assert.equal(document.getElementById('requests-total').textContent, 'Unknown');
assert.equal(document.getElementById('requests-detail').textContent, 'Count unknown');
renderOverview({counts: {requests: {total: 0, by_state: {open: 0}}}});
assert.equal(document.getElementById('requests-total').textContent, '0');
assert.equal(document.getElementById('requests-detail').textContent, 'open 0');
renderWarnings({warnings: [], prompt_bloat_watch: [{phase: 'safe', median_prompt_chars: null, calls: null}]});
assert.match(document.getElementById('warnings').innerHTML, /Unknown call/);
assert.doesNotMatch(document.getElementById('warnings').innerHTML, /0 call/);
renderWarnings({warnings: [], prompt_bloat_watch: [{phase: 'safe', median_prompt_chars: 1, calls: 0}]});
assert.match(document.getElementById('warnings').innerHTML, /0 call/);
assert.equal(fmtInt(0), '0');
assert.equal(fmtInt(undefined), 'Unknown');
"""
    )


def test_rejected_private_document_does_not_keep_a_certified_clock():
    code = _retained_script("work.html", "  function recordWorkFetch", "\n  function refilterOnly")
    _node(
        _DOM
        + r"""
const pending = [];
const PUBLIC_PROJECTION_URL = '/public', PRIVATE_PROJECTION_URL = '/private', PRIVATE_TIMEOUT_MS = 5000;
const PUBLIC_SOURCE_ID = 'public-monitor', PRIVATE_SOURCE_ID = 'private-local-adapter';
const state = {receivedAt: new Map(), privateStatusText: ''};
const showError = () => {};
const installView = () => {};
const admitPublicDocument = doc => ({ok: true, doc});
const admitPrivateDocument = doc => ({ok: true, doc, sourceStatus: 'ok'});
const mergeProjections = () => ({ok: false});
const fetchJson = () => new Promise((resolve, reject) => pending.push({resolve, reject}));
const classifyPublicFailure = () => 'unreachable';
const classifyPrivateFailure = () => 'unreachable';
const privateMetaFromCode = code => code || 'admitted';
const els = {publicMeta: {textContent: ''}, privateMeta: {textContent: ''}, list: {innerHTML: '', removeAttribute() {}}};
const accepted = {cache_age_s: 30, sources: [{source_id: PRIVATE_SOURCE_ID, status: 'ok', freshness: {observed_at: '2020-01-01T00:00:00Z', age_s: 20}, sections: {}, truncation: {}}]};
const rejected = {cache_age_s: 40, sources: [{source_id: PRIVATE_SOURCE_ID, status: 'ok', freshness: {observed_at: '2020-01-01T00:00:00Z', age_s: 99}, sections: {}, truncation: {}}]};
const privateStatus = () => document.getElementById('source-private-meta').nextElementSibling.textContent;
"""
        + code
        + r"""
(async () => {
  recordWorkFetch('source-private-meta', accepted);
  assert.match(privateStatus(), /Source age 20s/);
  assert.match(privateStatus(), /Cache\/read age 30s/);
  assert.doesNotMatch(privateStatus(), /50s/);
  const load = loadProjection();
  pending[0].resolve({sources: [{source_id: PUBLIC_SOURCE_ID, status: 'ok'}]});
  pending[1].resolve(rejected);
  await load;
  assert.match(privateStatus(), /Unavailable/);
  assert.match(privateStatus(), /Source age 20s/);
  assert.match(privateStatus(), /Cache\/read age 30s/);
  assert.doesNotMatch(privateStatus(), /99s/);
  assert.doesNotMatch(privateStatus(), /40s/);
  assert.doesNotMatch(privateStatus(), /50s/);
  const fresh = loadProjection();
  pending[2].resolve({sources: [{source_id: PUBLIC_SOURCE_ID, status: 'ok'}]});
  pending[3].resolve(rejected);
  await fresh;
  assert.match(privateStatus(), /Source age 20s/);
})().catch(e => {console.error(e); process.exitCode = 1;});
"""
    )
