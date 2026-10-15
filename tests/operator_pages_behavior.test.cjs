const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

// Run the shipped page scripts, including their startup loaders, with controlled
// HTTP responses. No private payloads or live mutations enter these fixtures.
function page(name, responder = async () => { throw Error('offline'); }) {
  const nodes = new Map();
  const listeners = {};
  const document = {
    hidden: false,
    activeElement: null,
    getElementById(id) {
      if (!nodes.has(id)) nodes.set(id, element(id));
      return nodes.get(id);
    },
    querySelector: () => document.getElementById('modal'),
    querySelectorAll: () => [],
    addEventListener(key, fn) { listeners[key] = fn; },
  };
  function element(id) {
    const classes = new Set();
    const attrs = {};
    return {
      id, innerHTML: '', textContent: '', value: '', style: {}, dataset: {}, isConnected: true,
      setAttribute(key, value) { attrs[key] = value; },
      getAttribute(key) { return attrs[key]; },
      removeAttribute(key) { delete attrs[key]; },
      classList: {add: key => classes.add(key), remove: key => classes.delete(key), contains: key => classes.has(key)},
      querySelectorAll: () => [], contains: () => false,
      addEventListener(key, fn) { this[key] = fn; },
      focus() { document.activeElement = this; },
    };
  }
  const calls = [];
  let handler = responder;
  const context = vm.createContext({
    document, console: {info() {}, error() {}}, URL, AbortController, Date,
    setTimeout, clearTimeout, setInterval: () => 1, clearInterval() {},
    fetch: async url => {
      calls.push(url);
      const data = await handler(url);
      return {ok: true, status: 200, text: async () => typeof data === 'string' ? data : JSON.stringify(data)};
    },
  });
  const html = fs.readFileSync(`dashboards/${name}.html`, 'utf8');
  let script = [...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');
  // Expose the existing lexical scope without replacing any application code.
  if (['epics', 'epics-map'].includes(name)) script = script.replace('(function () {', '').replace(/\}\)\(\);\s*$/, '');
  vm.runInContext(script, context, {filename: `dashboards/${name}.html`});
  return {context, nodes, document, calls, listeners, setResponder(fn) { handler = fn; }, run: code => vm.runInContext(code, context)};
}
const tick = () => new Promise(setImmediate);
const task = (status, id = status || 'unknown-status') => ({task_id: id, status, agent: 'seat-a'});
const stream = id => ({stream_id: id, registered: true, lease: null});
const detail = id => ({schema:'remote-epic-lifecycle.v1', ...stream(id), digest: {pinned: [], recent: []}});
const list = streams => ({schema: 'remote-epic-lifecycle.v1', streams});
const graph = () => ({schema: 'epics-graph.v1', nodes: {areas: [], epics: []}, edges: []});

for (const name of ['delegate', 'epics', 'epics-map', 'orient', 'routing']) {
  test(`${name}: HTTP-200 invalid JSON and scalar bodies are errors`, async () => {
    const p = page(name); await tick();
    p.setResponder(async () => '<html>upstream error</html>');
    await assert.rejects(p.run("fetchJson('/synthetic')"), /Malformed JSON/);
    p.setResponder(async () => 'null');
    await assert.rejects(p.run("fetchJson('/synthetic')"), /Malformed response object/);
    assert.equal(p.run(`escapeHtml('"<&\\\'')`), '&quot;&lt;&amp;&#39;');
  });
}

test('Delegate preserves every status, its loaded denominator and unknown new states', async () => {
  const statuses = ['spawning', 'running', 'done', 'failed', 'blocked', 'timeout', 'rate_limited', 'cancelled', 'crashed', 'dry_run', 'needs_finalize', 'no_deliverable', 'zombie', 'new-status', null, ''];
  const p = page('delegate', async () => ({total: 21, tasks: statuses.map(s => task(s))})); await tick();
  for (const status of statuses.slice(2).filter(Boolean)) assert.match(p.nodes.get('completed-content').innerHTML, new RegExp(`>${status}<`));
  for (const status of statuses.slice(0, 2)) assert.match(p.nodes.get('active-content').innerHTML, new RegExp(`>${status}<`));
  assert.match(p.nodes.get('completed-content').innerHTML, />unknown</);
  assert.match(p.nodes.get('last-refresh').textContent, /16 of 21 task records loaded/);
  assert.equal(p.nodes.get('active-content').getAttribute('aria-busy'), undefined);
  p.setResponder(async () => ({tasks: null}));
  await p.run('loadTasks()');
  assert.match(p.nodes.get('active-banner').textContent, /Malformed task list/);
  assert.match(p.nodes.get('active-banner').textContent, /historical/);
  assert.match(p.nodes.get('completed-content').innerHTML, />needs_finalize</);
});

test('Delegate detail is selection guarded, nullable results stay unknown, and Escape returns focus', async () => {
  const pending = new Map();
  const p = page('delegate', async () => ({total: 0, tasks: []})); await tick();
  p.setResponder(url => new Promise(resolve => pending.set(url.split('/').pop(), resolve)));
  const opener = p.document.getElementById('opener'); opener.focus();
  const first = p.run("openDetail('old')"); const second = p.run("openDetail('new')");
  pending.get('new')({task: task('needs_finalize', 'new'), result: null, result_truncated: false}); await second;
  assert.match(p.nodes.get('task-json').textContent, /needs_finalize/);
  assert.match(p.nodes.get('task-result').textContent, /completion is not established/);
  pending.get('old')({task: task('done', 'old'), result: 'old result', result_truncated: false}); await first;
  assert.doesNotMatch(p.nodes.get('task-json').textContent, /"old"/);
  p.listeners.keydown({key: 'Escape'});
  assert.equal(p.document.activeElement, opener);
  assert.equal(p.nodes.get('overlay').classList.contains('open'), false);
  p.setResponder(async () => ({task: task('done', 'wrong'), result: '', result_truncated: false}));
  await p.run("openDetail('requested')");
  assert.match(p.nodes.get('detail-banner').textContent, /Malformed task detail/);
});

test('Delegate untrusted task ids remain inert attributes and observer summary excludes private fields', async () => {
  const hostile = `quote'\"><img src=x onerror=alert(1)>`;
  const p = page('delegate', async () => ({total: 1, tasks: [task('done', hostile)]})); await tick();
  const html = p.nodes.get('completed-content').innerHTML;
  assert.doesNotMatch(html, /<img/); assert.match(html, /&quot;&gt;&lt;img/);
  assert.match(html, /onclick='openDetail\(this.dataset.taskId\)'/);
  assert.doesNotMatch(html, /onclick='openDetail\("quote/);
  assert.equal(p.run(`JSON.stringify(observerTaskView({task_id:'safe', cwd:'private', result_file:'private'}))`), '{"task_id":"safe","agent":null,"model":null,"status":null}');
});

test('Epics list validates boundaries and keeps unknown lease data and unregistered rows', async () => {
  const p = page('epics', async () => list([{stream_id: 'epic:1', registered: false}, stream('epic:2')])); await tick();
  assert.match(p.nodes.get('epics-tbody').innerHTML, /unknown/);
  assert.match(p.nodes.get('list-count-meta').textContent, /2 of 2 streams known to the session store/);
  assert.equal(p.run("getLeaseState({lease:{}})"), 'unknown');
  assert.equal(p.run("getLeaseState({lease:null})"), 'none');
  p.setResponder(async () => ({schema: 'remote-epic-lifecycle.v1', streams: 'wrong'})); await p.run('loadStreams()');
  assert.match(p.nodes.get('error-banner').textContent, /Malformed stream list/);
  assert.match(p.nodes.get('epics-tbody').innerHTML, /epic:2/);
  assert.match(p.nodes.get('last-updated-text').textContent, /Last successful fetch/);
});

test('Epics reverse detail responses, background refresh and late errors cannot replace selection', async () => {
  const p = page('epics', async () => list([stream('epic:1'), stream('epic:2')])); await tick();
  const pending = [];
  p.setResponder(url => url === '/api/epics/v1' ? Promise.resolve(list([stream('epic:1'), stream('epic:2')])) : new Promise(resolve => pending.push({url, resolve})));
  const first = p.run("selectEpic('epic:1')"); const second = p.run("selectEpic('epic:2')");
  pending[1].resolve(detail('epic:2')); await second;
  pending[0].resolve({error: 'malformed old response'}); await first;
  assert.match(p.nodes.get('detail-meta').textContent, /^epic:2/);
  await p.run('loadStreams()'); // Starts background refresh of epic:2.
  const third = p.run("selectEpic('epic:1')");
  pending[3].resolve(detail('epic:1')); await third;
  pending[2].resolve(detail('epic:2')); await tick();
  assert.match(p.nodes.get('detail-meta').textContent, /^epic:1/);
  p.setResponder(async () => ({...stream('epic:1'), digest: null}));
  await p.run("selectEpic('epic:1')");
  assert.match(p.nodes.get('detail-pane').innerHTML, /Malformed stream detail/);
});

test('Epics quotes in snippets, identity and digest classes cannot create attributes', async () => {
  const payload = {...stream(`epic:3\" data-injected=\"yes`), last_state: {body: '\" onmouseover=\"bad()'}};
  const p = page('epics', async () => list([payload])); await tick();
  assert.doesNotMatch(p.nodes.get('epics-tbody').innerHTML, /title="" onmouseover|data-stream-id="epic:3" data-injected/);
  assert.match(p.nodes.get('epics-tbody').innerHTML, /&quot;/);
});

test('Graph preserves incomplete membership and provides a safe keyboard list alternative', async () => {
  const data = graph();
  data.nodes.areas = [{id: 'area:unsafe" title="bad', title: '<img src=x>', stream_id: 'area-one'}];
  data.nodes.epics = [{id: 'epic:9', area_id: 'area-one', title: 'title" onfocus="bad', lease: null}];
  data.membership_complete = false;
  data.issues_by_epic = {'9': {items: [], total_open: 0, truncated: false}};
  data.stale = true;
  const p = page('epics-map', async () => data); await tick();
  const html = p.nodes.get('map-content').innerHTML;
  assert.match(html, /Relationship list alternative/);
  assert.match(html, /<button/); assert.match(html, /area-heading-0/);
  assert.doesNotMatch(html, /<img|aria-label="[^"]*" onfocus/);
  const membership = p.run('renderIssueSection({number:9})');
  assert.match(membership, /incomplete in the stale cache/); assert.doesNotMatch(membership, /0 open issues/);
  p.setResponder(async () => ({schema: 'epics-graph.v1', nodes: {}})); await p.run('loadGraph()');
  assert.match(p.nodes.get('error-banner').textContent, /schema/);
  assert.match(p.nodes.get('map-content').innerHTML, /Relationship list alternative/);
});

const routing = {agents: {}, in_flight: {}, recommendation: {warnings: []}, claude_accounts: {}};
function routingResponse(url) {
  if (url.includes('routing-budget')) return routing;
  if (url.includes('/agents')) return {agents: [{name: 'seat-a'}]};
  if (url.includes('/usage')) return {records_total: 0, by_agent: {}};
  return {total: 0, tasks: []};
}

test('Routing independently validates four feeds and never renders failed usage or tasks as zero', async () => {
  const p = page('routing', async url => {
    if (url.includes('/usage') || url.includes('/tasks')) throw Error('synthetic unavailable');
    return routingResponse(url);
  }); await tick();
  assert.match(p.nodes.get('agent-table').innerHTML, /seat-a/);
  assert.match(p.nodes.get('summary-grid').innerHTML, /7-Day Runtime Calls<\/h3>\s*<div class="value">unknown/);
  assert.match(p.nodes.get('delegate-table').textContent, /task state unknown/);
  assert.match(p.nodes.get('refresh-status').textContent, /2 failed/);
  p.setResponder(async url => routingResponse(url)); await p.run('loadRouting()');
  assert.match(p.nodes.get('summary-grid').innerHTML, /7-Day Runtime Calls<\/h3>\s*<div class="value">0/);
  p.setResponder(async url => url.includes('/usage') ? {records_total: null, by_agent: {}} : routingResponse(url)); await p.run('loadRouting()');
  assert.match(p.nodes.get('summary-grid').innerHTML, /Malformed runtime usage/);
  assert.match(p.nodes.get('summary-grid').innerHTML, /7-Day Runtime Calls<\/h3>\s*<div class="value">unknown/);
});

test('Routing good siblings render while another feed is pending and duplicate refreshes coalesce', async () => {
  let release;
  const p = page('routing', url => url.includes('routing-budget') ? new Promise(resolve => {release = resolve;}) : Promise.resolve(routingResponse(url)));
  await tick();
  assert.match(p.nodes.get('agent-table').innerHTML, /seat-a/);
  const count = p.calls.length; await p.run('loadRouting()'); assert.equal(p.calls.length, count);
  release(routing); await tick();
  assert.match(p.nodes.get('subscriptions-table').innerHTML, /Source age unknown/);
});

test('Routing uses actual account rows and withholds ambiguous capacity with null, invalid or future ages', async () => {
  const p = page('routing', async routingUrl => routingResponse(routingUrl)); await tick();
  const accounts = {
    'claude:a': {status:'unknown', reason:'account_ambiguous', age_s:null, session5h:{left_pct:90}, weekly:{left_pct:80}},
    'claude:b': {status:'stale', stale:true, reason:'timeout', age_s:15, weekly:{left_pct:0, pace:'<bad>'}},
  };
  p.context.sample = {claude_accounts:accounts}; p.run('renderClaudeAccounts(sample)');
  const html = p.nodes.get('claude-accounts-table').innerHTML;
  assert.doesNotMatch(html, /90%|80%|0s ago|<bad>/);
  assert.match(html, /Source age unknown/); assert.match(html, /stale historical sample/); assert.match(html, />0%/);
  assert.equal(p.run('formatAge(null)'), 'Source age unknown');
  assert.equal(p.run('formatAge(Infinity)'), 'Source age unknown');
  assert.equal(p.run('formatAge(-1)'), 'Source age unknown');
  p.context.sample = {claude_accounts:{'claude:a':{status:'ok', updated:'2999-01-01', age_s:0}}};
  p.run('renderClaudeAccounts(sample)'); assert.match(p.nodes.get('claude-accounts-table').innerHTML, /Source age unknown/);
  p.context.sample = {api_accounts:{'safe-account':{probe_state:'NEED_PROBE'}}}; p.run('renderApiAccounts(sample)');
  assert.match(p.nodes.get('api-accounts-table').innerHTML, /safe-account/);
  assert.doesNotMatch(p.nodes.get('api-accounts-table').innerHTML, /openrouter|deepseek/);
});

const orient = {git:{branch:'safe'}, issues:[], pipeline:{}, runtime:{}, delegate:{recent:[],active_count:null}, bridge_pending:{}, wiki:{}, health:{api:true, sources_db:false}, session_hints:[]};
function orientResponse(url) {
  if (url === '/api/orient') return orient;
  if (url.includes('/discussions')) return {discussions:[]};
  if (url.includes('/delegate')) return {total:0,tasks:[]};
  if (url.includes('/epics/')) return {streams:[]};
  if (url.includes('/workers/')) return {hosts:[]};
  return {hosts:{}};
}

test('Orient health retains true, false, missing and null independently', async () => {
  const p = page('orient', async url => orientResponse(url)); await tick();
  p.run('renderHealth({api:true,mcp_sources:null,sources_db:false})');
  const html = p.nodes.get('health-content').innerHTML;
  assert.equal((html.match(/healthy/g)||[]).length, 1);
  assert.equal((html.match(/down/g)||[]).length, 1);
  assert.equal((html.match(/unknown/g)||[]).length, 2);
  p.run('renderHealth({api:"false"})');
  assert.doesNotMatch(p.nodes.get('health-content').innerHTML, /healthy|down/);
});

test('Orient malformed sections and snapshot timeout leave independent feeds and valid health usable', async () => {
  const p = page('orient', async url => url === '/api/orient' ? {...orient, issues:null, pipeline:{error:'unavailable'}} : orientResponse(url)); await tick();
  assert.match(p.nodes.get('health-content').innerHTML, /healthy/);
  assert.match(p.nodes.get('issues-content').innerHTML, /State unknown/);
  assert.match(p.nodes.get('pipeline-content').innerHTML, /State unknown/);
  assert.match(p.nodes.get('discussions-content').innerHTML, /Source age unknown/);
  p.setResponder(async url => { if (url === '/api/orient') throw Error('Request timed out'); return orientResponse(url); });
  await p.run('loadOrient()');
  assert.match(p.nodes.get('page-banner').textContent, /timed out/);
  assert.match(p.nodes.get('health-content').innerHTML, /historical/);
  assert.match(p.nodes.get('discussions-content').innerHTML, /Source age unknown/);
});

test('Orient malformed delegate cross-check cannot establish empty or zero active tasks', async () => {
  const p = page('orient', async url => orientResponse(url)); await tick();
  p.setResponder(async () => ({tasks:'invalid'})); await p.run('renderDelegate({})');
  assert.match(p.nodes.get('delegate-content').innerHTML, /live delegate list is unavailable/);
  assert.match(p.nodes.get('delegate-muted').textContent, /unknown active/);
});

test('Partial task and stream lists retain valid rows and expose omitted coverage', async () => {
  const delegate = page('delegate', async () => ({total: 3, tasks: [null, task('blocked'), task('future-status')]})); await tick();
  assert.match(delegate.nodes.get('completed-content').innerHTML, />blocked</);
  assert.match(delegate.nodes.get('active-banner').textContent, /Partial task list: 1 malformed/);
  assert.match(delegate.nodes.get('last-refresh').textContent, /2 of 3/);
  const epics = page('epics', async () => list([null, stream('epic:8')])); await tick();
  assert.match(epics.nodes.get('epics-tbody').innerHTML, /epic:8/);
  assert.match(epics.nodes.get('error-banner').textContent, /Partial stream list: 1 malformed/);
});

test('Invalid active-lease expiry cannot establish active state', async () => {
  for (const name of ['epics', 'epics-map']) {
    const p = page(name); await tick();
    assert.equal(p.run("getLeaseState({lease:{state:'active',expires_at:'invalid'}})"), 'unknown');
    assert.equal(p.run("getLeaseState({lease:{state:'active'}})"), 'unknown');
  }
});

test('Retained source and heartbeat ages advance from their original observation baseline', async () => {
  const p = page('routing', async url => routingResponse(url)); await tick();
  const cell = {dataset:{sourceAge:'10', ageAt:String(Date.now() - 65000)}, textContent:''};
  p.document.querySelectorAll = () => [cell]; p.run('updateSourceAges()');
  assert.equal(cell.textContent, '1m ago');
  const q = page('epics', async () => list([])); await tick();
  q.run('state.lastUpdated = new Date(Date.now() - 65000)');
  const heartbeat = {textContent:'', getAttribute:key => key === 'data-heartbeat-age' ? '10' : ''};
  q.document.querySelectorAll = selector => selector === '[data-heartbeat-age]' ? [heartbeat] : [];
  q.run('updateLiveCountdowns()');
  assert.match(heartbeat.textContent, /^1m 1[5-6]s ago$/);
});

test('Populated graph detail keeps selected identity and known membership counts', async () => {
  const data = graph();
  data.nodes.areas = [{id:'area:one', title:'Area one', stream_id:'one'}];
  data.nodes.epics = [{id:'epic:7', number:7, area_id:'one', title:'Epic seven', lease:{state:'released',holder:{agent:'seat-a'}}, open_issue_count:1}];
  data.issues_by_epic = {'7':{items:[{number:11,title:'Issue eleven'}],total_open:1,truncated:false}};
  const p = page('epics-map', async () => data); await tick();
  p.run("selectEpic('epic:7')");
  assert.match(p.nodes.get('detail-pane').innerHTML, /1 open issue in the cache/);
  assert.match(p.nodes.get('detail-pane').innerHTML, /Issue eleven/);
});

test('Populated Orient sections retain individual runtime counts and navigable discussions', async () => {
  const p = page('orient', async url => {
    if (url === '/api/orient') return {...orient,
      git:{branch:'safe', recent_commits:[{sha:'abc',subject:'Change one'}]},
      issues:[{number:11,title:'Issue eleven',age_days:1,labels:['safe']}],
      bridge_pending:{'seat-a':{count:1,oldest_hours:2}},
      runtime:{agents:['seat-a'],headroom:{'seat-a':true},by_agent:{'seat-a':{ok:3,error:1,rate_limited:2}}},
    };
    if (url.includes('/discussions')) return {discussions:[{thread_id:'safe-thread',channel:'review',agents:['seat-a'],status:'running',last_message_at:new Date().toISOString()}]};
    return orientResponse(url);
  }); await tick();
  assert.match(p.nodes.get('runtime-content').innerHTML, /ok 3/);
  assert.match(p.nodes.get('issues-content').innerHTML, /Issue eleven/);
  assert.match(p.nodes.get('discussions-content').innerHTML, /<a href="\/fleet.html\?conversation=safe-thread">/);
  p.run('manualRefresh()'); await tick();
});

test('Populated Routing keeps source allotment, measured zero and individual in-flight counts', async () => {
  const p = page('routing', async url => {
    if (url.includes('routing-budget')) return {...routing, in_flight:{cursor:2}, agents:{cursor:{status:'cool', login_state:'authenticated',probe_state:'healthy',provider_windows:{auto:{used_pct:25,remaining_pct:75,window_minutes:40000}},codexbar:{age_s:12},fleet_burn:{windows:{'7d':{counts:{total:3}}}}}},api_accounts:{openrouter:{probe_state:'OK',limit_remaining_usd:0,age_s:12}}};
    return routingResponse(url);
  }); await tick();
  const html = p.nodes.get('subscriptions-table').innerHTML;
  assert.match(html, /25% used · 75% left/);
  assert.match(html, /7d: 3/);
  assert.match(html, /<td>2<\/td>/);
  assert.match(p.nodes.get('api-accounts-table').innerHTML, /\$0\.00/);
});

test('Unrecognized status and digest classes stay visible as neutral text', async () => {
  const p = page('epics', async () => list([stream('epic:1')])); await tick();
  assert.equal(p.run("renderPill('hidden')"), '<span class="pill unknown">HIDDEN</span>');
  p.context.sample = {...detail('epic:1'), digest:{pinned:[],recent:[{type:'hidden',body:'Digest remains visible',ts:'2026-01-01'}]}};
  p.run('renderDetail(sample)');
  assert.match(p.nodes.get('detail-pane').innerHTML, /digest-card entry/);
  assert.doesNotMatch(p.nodes.get('detail-pane').innerHTML, /class="[^"]*hidden/);
  const q = page('routing', async url => routingResponse(url)); await tick();
  assert.equal(q.run("statusPill('hidden')"), '<span class="pill unknown">hidden</span>');
});

test('Orient report ages preserve known samples and reject unavailable or future observations', async () => {
  const p = page('orient', async url => orientResponse(url)); await tick();
  assert.equal(p.run('glanceAge(25)'), '25s at fetch');
  assert.equal(p.run('glanceAge(null)'), 'Source age unknown');
  assert.equal(p.run("glanceAge(0, '2999-01-01')"), 'Source age unknown');
  const unavailable = p.run("renderGlanceHosts({hosts:{'host-teacher':{status:'unavailable',age_seconds:0}}})");
  assert.match(unavailable, /Source age unknown/);
  assert.doesNotMatch(unavailable, /0s at fetch/);
  const stale = p.run("renderGlanceHosts({hosts:{'host-teacher':{status:'stale',age_seconds:200}}})");
  assert.match(stale, /200s at fetch/);
});

test('Malformed runtime modes cannot throw from an otherwise successful agent feed', async () => {
  const p = page('routing', async url => url.includes('/agents') ? {agents:[{name:'seat-a',supported_modes:{}}]} : routingResponse(url)); await tick();
  assert.match(p.nodes.get('agent-table').innerHTML, /Malformed runtime agents/);
  assert.match(p.nodes.get('subscriptions-table').innerHTML, /Source age unknown/);
});
