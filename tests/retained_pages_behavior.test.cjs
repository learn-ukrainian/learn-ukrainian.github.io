'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { execFileSync } = require('node:child_process');
const { createRequire } = require('node:module');
const { test, before, after } = require('node:test');
const root = path.resolve(__dirname, '..');
const pages = ['acp', 'cost', 'fleet', 'runtime', 'work'];

for (const name of pages) {
  test(`${name}: source and cache clocks retain real fetch time across loading and errors`, () => {
    const html = fs.readFileSync(path.join(root, 'dashboards', `${name}.html`), 'utf8');
    const helper = html.slice(html.indexOf('// Retained panel clocks:'), html.indexOf('// End retained panel clocks.'));
    let now = 0;
    const ticks = [];
    const nodes = {};
    const ageNode = { dataset: { retainedAge: '1', received: '0' } };
    const make = () => ({ dataset: {}, style: {}, textContent: '', setAttribute(key, value) { this[key] = value; }, after(node) { this.status = node; } });
    const context = { Map, Date, Number, String, Math, performance: { now: () => now }, setInterval(fn) { ticks.push(fn); }, document: {
      querySelectorAll: () => [ageNode],
      getElementById: id => id === 'missing' ? null : (nodes[id] ||= make()), createElement: make,
    } };
    vm.createContext(context);
    vm.runInContext(helper, context);
    context.retainedStatus('panel', 'Loading');
    assert.match(nodes.panel.status.textContent, /Source age unknown.*No successful fetch/);
    assert.equal(nodes.panel['aria-busy'], 'true');
    context.retainedStatus('panel', 'Partial', { fetched: true, sourceAge: null, cacheAge: 0 });
    assert.match(nodes.panel.status.textContent, /Partial.*Source age unknown.*Cache\/read age 0s.*Last successful fetch/);
    now = 4000;
    context.retainedStatus('panel', 'Stale', { note: 'Upstream stale' });
    assert.match(nodes.panel.status.textContent, /Stale.*Cache\/read age 4s.*Upstream stale/);
    assert.equal(nodes.panel['aria-busy'], 'false');
    context.retainedStatus('panel', 'Error');
    assert.match(nodes.panel.status.textContent, /Error.*Cache\/read age 4s.*Last successful fetch/);
    context.retainedStatus('panel', 'Unknown', { fetched: true, sourceAge: 0, cacheAge: null });
    now = 7000;
    context.retainedStatus('panel', 'Unknown');
    assert.match(nodes.panel.status.textContent, /Source age 3s/);
    for (const invalid of [null, undefined, -1, NaN, Infinity, '0']) {
      context.retainedStatus('panel', 'Unknown', { fetched: true, sourceAge: invalid });
      assert.match(nodes.panel.status.textContent, /Source age unknown/);
    }
    context.retainedStatus('missing', 'Error');
    ticks.forEach(tick => tick());
    if (context.retainedAge) assert.equal(ageNode.textContent, '8s');
    if (context.retainedAge) {
      assert.equal(context.retainedAge(null), 'unknown');
      assert.equal(context.retainedAge(0, 0, false), 'unknown');
      assert.match(context.retainedAge(1, 0), />8s</);
    }
  });
}

let browser;
before(async () => {
  const gitDir = execFileSync('git', ['rev-parse', '--path-format=absolute', '--git-common-dir'], { cwd: root, encoding: 'utf8' }).trim();
  const requireProject = createRequire(path.join(path.dirname(gitDir), 'package.json'));
  const puppeteer = requireProject('puppeteer');
  const executablePath = [process.env.PUPPETEER_EXECUTABLE_PATH, '/usr/bin/chromium', '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable'].find(file => file && fs.existsSync(file));
  browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'], ...(executablePath ? { executablePath } : {}) });
});
after(async () => { if (browser) await browser.close(); });

async function openPage(name, handler, query = '') {
  const page = await browser.newPage();
  const pageOrigin = name === 'work' ? 'http://127.0.0.1:8765' : 'http://retained.test';
  await page.setRequestInterception(true);
  page.on('request', async request => {
    const url = new URL(request.url());
    if (url.pathname === `/${name}.html`) return request.respond({ contentType: 'text/html', body: fs.readFileSync(path.join(root, 'dashboards', `${name}.html`), 'utf8') });
    if (url.pathname === '/monitor.css') return request.respond({ contentType: 'text/css', body: fs.readFileSync(path.join(root, 'dashboards', 'monitor.css'), 'utf8') });
    if (!url.pathname.startsWith('/api/') && !url.pathname.endsWith('/v1/projection')) return request.respond({ status: 200, body: '' });
    assert.equal(request.method(), 'GET');
    try {
      const result = await handler(url, request);
      if (request.isInterceptResolutionHandled()) return;
      await request.respond({ headers: { 'Access-Control-Allow-Origin': pageOrigin }, contentType: 'application/json', status: result?.status || 200, body: typeof result?.body === 'string' ? result.body : JSON.stringify(result?.body ?? result) });
    } catch { if (!request.isInterceptResolutionHandled()) await request.abort(); }
  });
  await page.goto(`${pageOrigin}/${name}.html${query}`, { waitUntil: 'domcontentloaded' });
  return page;
}
const status = (page, id) => page.$eval(`#${id} + .retained-status`, node => node.textContent);
const waitState = (page, id, expected) => page.waitForFunction((id, expected) => document.getElementById(id)?.nextElementSibling?.dataset.state === expected, {}, id, expected);
function costs(label = 'safe phase', calls = 0) {
  const data = { scope: { label }, totals: { calls, prompt_tokens_est: null, response_tokens_est: 0, cost_usd_est: null }, per_phase: [], per_model: [], top_modules: [], warnings: [], prompt_bloat_watch: [] };
  return { windows: { all_time: data, last_7_days: data, last_30_days: data } };
}

test('cost: null estimates stay unknown, valid zero remains zero, malformed success is an error', async () => {
  let payload = costs();
  const page = await openPage('cost', () => payload);
  try {
    await waitState(page, 'summary', 'Empty');
    const text = await page.$eval('#summary', node => node.textContent);
    assert.match(text, /Unknown/);
    assert.match(text, /0 output est/);
    assert.doesNotMatch(text, /\$0\.00/);
    assert.match(await status(page, 'summary'), /Source age unknown.*Last successful fetch/);
    payload = { windows: {} };
    await page.evaluate(() => refresh());
    await waitState(page, 'summary', 'Error');
    assert.match(await page.$eval('#banner', node => node.textContent), /Malformed/);
    assert.equal(await page.evaluate(() => window.__costPayload), null);
    payload = costs('safe'); payload.windows.all_time.per_phase = [{ name: '<img src=x onerror=alert(1)>', calls: '\"<img src=x>', prompt_tokens_est: 0, response_tokens_est: 0, cost_usd_est: 0 }];
    await page.evaluate(() => refresh());
    assert.equal(await page.$eval('#per-phase', node => node.querySelectorAll('img').length), 0);
    assert.match(await page.$eval('#per-phase', node => node.textContent), /Unknown/);
    await page.setViewport({ width: 375, height: 800 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  } finally { await page.close(); }
});

test('cost: a late old filter response cannot overwrite the current scope or explicit clear', async () => {
  let release;
  const hold = new Promise(resolve => { release = resolve; });
  const page = await openPage('cost', async url => {
    if (url.searchParams.get('track') === 'old') { await hold; return costs('old'); }
    return costs(url.searchParams.get('track') || 'all');
  });
  try {
    await waitState(page, 'summary', 'Empty');
    await page.evaluate(() => { document.getElementById('scope').value = 'track'; document.getElementById('query').value = 'old'; void refresh(); });
    await page.evaluate(() => { document.getElementById('query').value = ''; return refresh(); });
    release();
    await page.waitForNetworkIdle({ idleTime: 100 });
    assert.equal(await page.$eval('#scope-label', node => node.textContent), 'Scope: all');
  } finally { release(); await page.close(); }
});

test('fleet: unavailable count defaults never display zero and a failed sibling preserves valid metadata', async () => {
  const page = await openPage('fleet', url => {
    if (url.pathname === '/api/fleet/overview') return { availability: 'db_missing', counts: { requests: { total: 0 } } };
    if (url.pathname === '/api/fleet/messages') return { messages: [{ kind: 'note', source: '\"<img src=x>', body_preview: '<script>bad()</script>' }], availability: 'available' };
    if (url.pathname === '/api/fleet/workers/v1') return { hosts: [{ host_id: 'safe-host', freshness: 'stale', workers_status: 'reported', age_s: 60, workers: [{ state: 'live', id: 'safe-worker' }] }] };
    if (url.pathname === '/api/occupancy') return { hosts: { safe: { host_id: 'safe-host', status: 'unavailable', age_seconds: 0 } } };
    return { body: '{invalid json' };
  });
  try {
    await waitState(page, 'requests-total', 'Unavailable');
    await waitState(page, 'workers-content', 'Unknown');
    assert.match(await page.$eval('#requests-total', node => node.textContent), /Unavailable/);
    assert.match(await page.$eval('#messages-content', node => node.textContent), /<script>bad/);
    assert.equal(await page.$eval('#messages-content', node => node.querySelectorAll('script,img').length), 0);
    assert.match(await page.$eval('#workers-content', node => node.textContent), /last observed live; current state unknown/);
    assert.match(await page.$eval('#occupancy-content', node => node.textContent), /Source age unknown/);
    assert.doesNotMatch(await page.$eval('#occupancy-content', node => node.textContent), /0s/);
    assert.match(await status(page, 'messages-content'), /Last successful fetch/);
  } finally { await page.close(); }
});

test('fleet: first partial response keeps independently valid rows and rejects malformed root', async () => {
  const page = await openPage('fleet', url => url.pathname === '/api/fleet/authority/jobs'
    ? { jobs: [null, { job_id: 'safe-job', state: 'running' }], availability: 'partial' } : { status: 503, body: {} });
  try {
    await waitState(page, 'authority-content', 'Partial');
    assert.match(await page.$eval('#authority-content', node => node.textContent), /safe-job/);
    await page.evaluate(() => {
      for (const invalid of [null, [], {}]) {
        let refused = false; try { validateFleetPanel('/api/fleet/authority/jobs', invalid); } catch { refused = true; }
        if (!refused) throw new Error('Malformed root accepted');
      }
    });
  } finally { await page.close(); }
});

test('runtime: malformed successes differ from empty history and failed headroom preserves other agents', async () => {
  const page = await openPage('runtime', url => {
    if (url.pathname === '/api/runtime/agents') return { agents: [{ name: 'first', default_model: 'safe-model' }, { name: 'second', default_model: 'safe-model' }] };
    if (url.pathname === '/api/runtime/headroom') return url.searchParams.get('agent') === 'first' ? { agent: 'first', has_headroom: true } : { status: 503, body: {} };
    if (url.pathname === '/api/runtime/recent') return { records: [] };
    if (url.pathname === '/api/runtime/usage') return {};
    if (url.pathname === '/api/runtime/routing-assignments') return { assignments: [], availability: 'unavailable' };
    return { status: 503, body: {} };
  });
  try {
    await waitState(page, 'headroom-content', 'Partial');
    await waitState(page, 'usage-content', 'Error');
    await waitState(page, 'recent-content', 'Empty');
    assert.match(await page.$eval('#headroom-content', node => node.textContent), /first.*Available.*second.*Unknown/s);
    assert.match(await page.$eval('#recent-content', node => node.textContent), /coverage unknown/);
    assert.match(await status(page, 'routing-assignments-content'), /Unavailable/);
    assert.match(await status(page, 'recent-content'), /Last successful fetch/);
  } finally { await page.close(); }
});

test('ACP: unavailable storage differs from empty, malformed detail is rejected, transcript 403 preserves metadata', async () => {
  let mode = 'unavailable';
  const page = await openPage('acp', url => {
    if (url.pathname.endsWith('/transcript')) return { status: 403, body: {} };
    if (url.pathname.endsWith('/safe-conversation')) return mode === 'malformed' ? {} : { conversation_id: 'safe-conversation', events: [], participants: [] };
    return mode === 'unavailable' ? { availability: 'unavailable', conversations: [] }
      : mode === 'empty' ? { availability: 'empty', conversations: [] }
      : { availability: 'available', conversations: [{ conversation_id: 'safe-conversation', participants: [] }] };
  });
  try {
    await waitState(page, 'conversation-list', 'Unavailable');
    assert.match(await status(page, 'conversation-list'), /No successful fetch/);
    mode = 'empty'; await page.evaluate(() => loadPage());
    await waitState(page, 'conversation-list', 'Empty');
    mode = 'malformed'; await page.evaluate(() => loadPage());
    await waitState(page, 'conversation-detail', 'Error');
    mode = 'available'; await page.evaluate(() => loadPage());
    await waitState(page, 'conversation-detail', 'Unavailable');
    assert.match(await page.$eval('#conversation-detail', node => node.textContent), /safe-conversation.*Transcript is local-only/s);
    assert.match(await page.$eval('#conversation-detail', node => node.textContent), /Rounds completed Unknown/);
    assert.match(await status(page, 'conversation-list'), /Source age unknown.*Last successful fetch/);
  } finally { await page.close(); }
});

test('work: source cache cannot rejuvenate upstream age, local filters preserve clock, unsafe links are withheld', async () => {
  const fixture = JSON.parse(process.env.RETAINED_WORK_FIXTURE);
  const source = fixture.sources.find(row => row.source_id === 'public-monitor');
  source.freshness = { observed_at: '2020-01-01T00:00:00Z', age_s: 3600 };
  fixture.cache_age_s = 0;
  fixture.items[0].urls.html = 'javascript:alert(1)';
  const page = await openPage('work', url => url.pathname === '/api/work/v1/projection' ? fixture : { status: 503, body: {} });
  try {
    await page.waitForFunction(() => document.querySelector('.work-row'));
    await page.waitForFunction(() => !document.getElementById('source-public-meta').nextElementSibling.textContent.startsWith('Loading'));
    assert.match(await status(page, 'source-public-meta'), /Source age 360\ds.*Cache\/read age \ds.*Last successful fetch/);
    assert.equal(await page.$eval('#detail-panel', node => node.querySelectorAll('a[href^="javascript:"]').length), 0);
    const first = await status(page, 'source-public-meta');
    await page.select('#filter-kind', 'issue');
    await page.click('#btn-apply');
    const second = await status(page, 'source-public-meta');
    assert.equal(second.match(/Last successful fetch ([^·]+)/)[1], first.match(/Last successful fetch ([^·]+)/)[1]);
    assert.match(await page.$eval('#source-public-meta', node => node.textContent), /streams=/);
  } finally { await page.close(); }
});

test('fleet: successful panels retain independent operation availability, stale rows, filters and literal metadata', async () => {
  let delay;
  const hold = new Promise(resolve => { delay = resolve; });
  const page = await openPage('fleet', async url => {
    if (url.pathname === '/api/fleet/health') return { authority_health: { state: 'idle', ok: true, jobs: { total: 0 } }, schema: { db_exists: true } };
    if (url.pathname === '/api/fleet/overview') return { counts: { requests: { total: null }, messages: { total: 0 } }, availability: 'available' };
    if (url.pathname === '/api/fleet/operations') return { availability: 'partial', broker: { availability: 'unavailable', unacknowledged_depth: 0 }, zombies: { availability: 'available', items: [] }, batches: { availability: 'degraded', tracks: [] } };
    if (url.pathname === '/api/fleet/projects/v1') return { hosts: { safe: { host_id: 'safe-host', freshness: 'stale', age_s: 70, services: [{ name: 'safe-service', serving_mode: null }] } } };
    if (url.pathname === '/api/fleet/messages') {
      if (url.searchParams.get('agent') === 'old') { await hold; return { messages: [{ kind: 'note', body_preview: 'old scope' }] }; }
      return { messages: [{ kind: 'note', body_preview: 'current scope' }] };
    }
    return { status: 503, body: {} };
  });
  try {
    await waitState(page, 'projects-content', 'Unknown');
    assert.equal(await page.$eval('#requests-total', node => node.textContent), 'Unknown');
    assert.equal(await page.$eval('#messages-total', node => node.textContent), '0');
    assert.match(await status(page, 'broker-operations-content'), /Unavailable/);
    assert.match(await status(page, 'batch-operations-content'), /Partial/);
    assert.doesNotMatch(await page.$eval('#broker-operations-content', node => node.textContent), /\b0\b/);
    assert.match(await page.$eval('#projects-content', node => node.textContent), /unresolved/);
    await page.evaluate(() => { document.getElementById('filter-agent').value = 'old'; void refreshFleet(); });
    await page.evaluate(() => { document.getElementById('filter-agent').value = ''; return refreshFleet(); });
    delay();
    await page.waitForNetworkIdle({ idleTime: 100 });
    assert.match(await page.$eval('#messages-content', node => node.textContent), /current scope/);
    assert.doesNotMatch(await page.$eval('#messages-content', node => node.textContent), /old scope/);
    assert.equal(await page.evaluate(() => fleetPanelState({ availability: 'not_configured' }, false)), 'Not installed');
    assert.equal(await page.evaluate(() => fleetPanelState({ stale: true }, false)), 'Stale');
  } finally { delay(); await page.close(); }
});

test('runtime: valid zero evidence, partial parsing, monitor recovery and refresh coalescing preserve actual states', async () => {
  let malformed = false;
  const page = await openPage('runtime', url => {
    if (url.pathname === '/api/runtime/agents') return { agents: [] };
    if (url.pathname === '/api/runtime/usage') return { by_agent: { safe: { total: null, total_duration_s: null } }, unreadable: { records: 1 } };
    if (url.pathname === '/api/runtime/acpx') return malformed ? { body: '<invalid>' } : { transport: { mode: 'off' }, seats: [{ name: '\"<img src=x>', evidence: { total: null } }], comparison_evidence: { comparisons: null } };
    if (url.pathname === '/api/runtime/recent') return { records: [{ agent: '<img src=x>', outcome: 'ok' }] };
    if (url.pathname === '/api/runtime/routing-assignments') return { assignments: [], availability: 'empty', window: { stale: true } };
    if (url.pathname === '/api/agent-monitor/status') return { severity: 'healthy', ram: { available_mb: 1, total_mb: 2, used_percent: 50 }, load_1m_5m_15m: [0, 0, 0], capacity_reservations: { active_leases_count: 0, total_reserved_ram_mb: 0 } };
    return { status: 503, body: {} };
  });
  try {
    await waitState(page, 'acpx-content', 'Unknown');
    await waitState(page, 'usage-content', 'Partial');
    await waitState(page, 'agent-monitor-status-badge', 'Unknown');
    await waitState(page, 'routing-assignments-content', 'Stale');
    assert.match(await page.$eval('#usage-content', node => node.textContent), /Unknown calls/);
    assert.match(await page.$eval('#acpx-content', node => node.textContent), /Shadow call count unknown/);
    assert.equal(await page.$eval('#acpx-content', node => node.querySelectorAll('img').length), 0);
    assert.equal(await page.evaluate(() => shadowCallCount([{ evidence: { total: 0 } }])), 0);
    assert.equal(await page.evaluate(() => shadowCallCount([])), null);
    assert.equal(await page.$eval('#active-leases-count', node => node.textContent), '0');
    malformed = true;
    await page.evaluate(async () => { await Promise.all([refreshRuntime(), loadRuntime()]); });
    await waitState(page, 'acpx-content', 'Error');
    assert.match(await status(page, 'acpx-content'), /Last successful fetch/);
  } finally { await page.close(); }
});

test('ACP: successful transcript is inert and a late detail cannot replace a newer selection', async () => {
  let release;
  const hold = new Promise(resolve => { release = resolve; });
  let delayed = false;
  const page = await openPage('acp', async url => {
    if (url.pathname.endsWith('/transcript')) return { messages: [{ kind: 'reply', body: '<script>bad()</script>', round: 1 }] };
    if (url.pathname.endsWith('/first') || url.pathname.endsWith('/second')) {
      const id = url.pathname.split('/').at(-1);
      if (id === 'first' && delayed) await hold;
      return { conversation_id: id, participants: [], events: [] };
    }
    return { conversations: [{ conversation_id: 'first' }, { conversation_id: 'second' }] };
  });
  try {
    await waitState(page, 'conversation-detail', 'Unknown');
    assert.match(await page.$eval('#conversation-detail', node => node.textContent), /<script>bad/);
    assert.equal(await page.$eval('#conversation-detail', node => node.querySelectorAll('script').length), 0);
    delayed = true;
    await page.evaluate(() => { void loadPage(); });
    await page.evaluate(() => { history.replaceState(null, '', '?conversation=second'); return loadPage(); });
    release();
    await page.waitForNetworkIdle({ idleTime: 100 });
    assert.equal(await page.$eval('#detail-heading', node => node.textContent), 'second');
    assert.equal(await page.$eval('[aria-current="true"]', node => node.textContent.includes('second')), true);
  } finally { release(); await page.close(); }
});

test('work: missing selected repository is retained, explicit clear stays clear and future source time is unknown', async () => {
  const fixture = JSON.parse(process.env.RETAINED_WORK_FIXTURE);
  const repo = fixture.items[0].repository_id;
  const page = await openPage('work', url => url.pathname === '/api/work/v1/projection' ? fixture : { status: 503, body: {} });
  try {
    await page.waitForFunction(() => document.querySelector('.work-row'));
    await page.select('#filter-repo', repo);
    fixture.items = []; fixture.attention = [];
    const source = fixture.sources.find(row => row.source_id === 'public-monitor');
    source.freshness = { observed_at: '2999-01-01T00:00:00Z', age_s: 0 };
    await page.click('#btn-refresh');
    await page.waitForFunction(() => document.getElementById('filter-repo').selectedOptions[0].textContent.includes('not returned'));
    assert.equal(await page.$eval('#filter-repo', node => node.value), repo);
    assert.match(await status(page, 'source-public-meta'), /Source age unknown/);
    await page.select('#filter-repo', ''); await page.click('#btn-apply');
    assert.equal(await page.$eval('#filter-repo', node => node.value), '');
  } finally { await page.close(); }
});

test('fleet: context panels show independent read age and wholly invalid rows are errors', async () => {
  const page = await openPage('fleet', url => url.pathname === '/api/ops/entire-context/status'
    ? { recall: { projection: { available: true, counts: {}, projection_health: {} } }, use: {} }
    : url.pathname === '/api/ops/entire-context/search' ? { available: true, results: [], omitted: [{ reason: 'source_missing' }] }
    : url.pathname === '/api/fleet/authority/jobs' ? { jobs: [null] } : { status: 503, body: {} }, '?conversation=safe-conversation');
  try {
    await waitState(page, 'context-health-content', 'Unknown');
    await waitState(page, 'context-used-content', 'Partial');
    await waitState(page, 'authority-content', 'Error');
    assert.match(await status(page, 'context-health-content'), /Source age unknown.*Last successful fetch/);
    assert.match(await status(page, 'context-used-content'), /Source age unknown.*Last successful fetch/);
  } finally { await page.close(); }
});

test('fleet: selected context, observed host rows and keyboard filter refresh remain usable together', async () => {
  const conversation = 'conversation_' + 'a'.repeat(32);
  const sha = 'b'.repeat(40);
  const page = await openPage('fleet', url => {
    if (url.pathname === '/api/ops/entire-context/status') return { recall: { projection: { available: true, counts: { promoted: 1 }, projection_health: { acp: { lag_seconds: 0, last_reconciliation_at: '2020-01-01T00:00:00Z' } } } }, use: { by_consumer: { safe: 1 }, receipts: 1 } };
    if (url.pathname === '/api/ops/entire-context/search') return { available: true, results: [{ kind: 'acp_conversation', canonical_id: conversation, locator_id: 'safe-locator', git_sha: sha, excerpt: { state: 'complete' } }], omitted: [] };
    if (url.pathname === '/api/fleet/workers/v1') return { hosts: [{ host_id: 'safe-host', freshness: 'fresh', age_s: 0, workers_status: 'unreported', workers: [] }] };
    if (url.pathname === '/api/fleet/projects/v1') return { hosts: { safe: { host_id: 'safe-host', freshness: 'fresh', age_s: 0, services: [] } } };
    if (url.pathname === '/api/occupancy') return { hosts: { safe: { host_id: 'safe-host', status: 'fresh', observed_at: '2020-01-01T00:00:00Z', age_seconds: 5, idle_or_empty: false, mem: { pct: 20 }, loadavg: [0], occupants: [{ kind: 'worker', agent: 'safe-agent', status: 'running' }], burn_sources: { safe: { state: 'clear', observation_age_s: null } } } } };
    if (url.pathname === '/api/fleet/messages') return { messages: [{ kind: 'note', body_preview: url.searchParams.get('agent') || 'all scope' }] };
    return { status: 503, body: {} };
  }, '?conversation=' + conversation);
  try {
    await waitState(page, 'context-used-content', 'Unknown');
    assert.match(await page.$eval('#context-used-content', node => node.textContent), /Selected conversation/);
    assert.equal(await page.$eval('#context-used-content a', node => new URL(node.href).pathname), '/acp.html');
    assert.match(await page.$eval('#occupancy-content', node => node.textContent), /RAM 20%/);
    assert.match(await page.$eval('#occupancy-content', node => node.textContent), /unknown/);
    assert.match(await page.$eval('#workers-content', node => node.textContent), /Workers unknown/);
    await page.type('#filter-agent', 'new-scope');
    await page.waitForFunction(() => document.getElementById('messages-content').textContent.includes('new-scope'));
    await page.$eval('#filter-agent', node => { node.value = ''; node.dispatchEvent(new Event('input')); });
    await page.waitForFunction(() => document.getElementById('messages-content').textContent.includes('all scope'));
    assert.equal(await page.$eval('#filter-agent', node => node.value), '');
    assert.equal(await page.evaluate(() => document.activeElement.id), 'filter-agent');
  } finally { await page.close(); }
});

test('work: independent public/private failure states preserve the surviving source and clear both on failure', async () => {
  let mode = 'both';
  const publicDoc = JSON.parse(process.env.RETAINED_WORK_FIXTURE);
  const privateDoc = JSON.parse(process.env.RETAINED_PRIVATE_FIXTURE);
  const page = await openPage('work', url => {
    if (url.pathname === '/api/work/v1/projection') return mode === 'both' ? publicDoc : { status: 503, body: {} };
    return mode === 'neither' ? { status: 503, body: {} } : privateDoc;
  }, '?view=all');
  try {
    await page.waitForFunction(() => document.querySelectorAll('.work-row').length === 2);
    assert.match(await status(page, 'source-private-meta'), /Last successful fetch/);
    assert.equal(await page.$eval('#detail-panel a', node => new URL(node.href).origin), 'https://github.com');
    mode = 'private'; await page.click('#btn-refresh');
    await page.waitForFunction(() => document.querySelectorAll('.work-row').length === 1 && document.getElementById('source-public-meta').nextElementSibling.dataset.state === 'Error');
    assert.match(await page.$eval('#attention-list', node => node.textContent), /private-issue-7/);
    mode = 'neither'; await page.click('#btn-refresh');
    await page.waitForFunction(() => document.getElementById('attention-list').textContent.includes('No source projection'));
    assert.equal(await page.$eval('#attention-list', node => node.querySelectorAll('.work-row').length), 0);
    assert.match(await status(page, 'source-public-meta'), /Error/);
    assert.match(await status(page, 'source-private-meta'), /Unavailable/);
  } finally { await page.close(); }
});
