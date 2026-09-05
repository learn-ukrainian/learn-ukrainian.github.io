const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync('dashboards/orient.html', 'utf8');
function setup(fetchJson = async () => { throw Error('offline'); }) {
  const nodes = {};
  const context = vm.createContext({Date, Set, JSON, fetchJson, document: {
    getElementById(id) { return nodes[id] ||= {innerHTML: '', textContent: ''}; },
  }});
  vm.runInContext(`function escapeHtml(v) { return String(v ?? '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;'); }` + html.slice(html.indexOf('function opaqueHost('), html.indexOf('function stopRefresh(')), context);
  return {context, nodes};
}
const worker = {kind:'delegate', agent:'codex', id:'seat-one', state:'live', run_id:'12345678'};
const host = {host_id:'host-teacher', freshness:'fresh', workers_status:'reported', workers:[worker, worker]};
const project = {freshness:'fresh', primary:{origin_main_sha:'b'.repeat(40)}, services:[{name:'monitor', repo:'public', state:'running', serving_mode:'release', serving_sha:'a'.repeat(40), drift:true}]};
test('all four panels precede session details and have mobile layout', () => {
  for (const name of ['epics','hosts','workers','projects']) assert.ok(html.indexOf(`id="glance-${name}"`) < html.indexOf('id="git-content"'));
  assert.match(html, /max-width: 900px/);
});
test('epic driver and opaque host with expired and malformed lease health', () => {
  const {context:c} = setup();
  const render = lease => c.renderGlanceEpics({streams:[{stream_id:'epic:7177',lease}]});
  const out = render({state:'active',expires_at:'2000-01-01',holder:{agent:'codex',host_id:'host-teacher'}});
  for (const text of ['epic:7177','codex','host-teacher','expired']) assert.match(out,new RegExp(text));
  assert.doesNotMatch(render({state:'active',expires_at:'bad',holder:{host_id:'private.example'}}), /private.example|<td>active/);
  assert.match(render(null), /no lease/);
});
test('Mac stays visible and unknown cannot become idle', () => {
  const {context:c} = setup();
  for (const status of ['stale','unavailable',undefined]) {
    const out=c.renderGlanceHosts({hosts:{'host-teacher':{status,burn_state:'idle'}}});
    assert.match(out,/mac-operator/); assert.doesNotMatch(out, /<td>idle<\/td>/);
  }
  assert.match(c.renderGlanceHosts({hosts:{'host-teacher':{status:'fresh',burn_state:'idle'}}}), /<td>idle<\/td>/);
});
test('canonical worker rows appear once, distinct runs survive, stale seats are not live', () => {
  const {context:c} = setup();
  assert.equal((c.renderGlanceWorkers({hosts:[host]}).match(/seat-one/g)||[]).length,1);
  assert.equal((c.renderGlanceWorkers({hosts:[{...host,workers:[worker,{...worker,run_id:'87654321'}]}]}).match(/seat-one/g)||[]).length,2);
  assert.doesNotMatch(c.renderGlanceWorkers({hosts:[{...host,freshness:'stale'}]}), /<td>live<\/td>/);
  assert.doesNotMatch(c.renderGlanceWorkers({hosts:[{...host,workers_status:'unreported'}]}), /No AI workers reported/);
});
test('release and checkout SHA drift, unknown upstream, stale report, sibling', () => {
  const {context:c} = setup();
  const render = p => c.renderGlanceProjects({hosts:{'host-teacher':p}});
  assert.match(render(project), /aaaaaaaa/); assert.match(render(project), /bbbbbbbb/); assert.match(render(project), /<td>drift<\/td>/);
  const service = {...project.services[0], serving_mode:'checkout', checkout_sha:'b'.repeat(40), drift:false};
  assert.match(render({...project,services:[service]}), /in sync/);
  assert.doesNotMatch(render({...project,freshness:'stale',services:[service]}), /in sync/);
  assert.doesNotMatch(render({...project,services:[{...service,drift:'unknown'}]}), /in sync/);
  assert.doesNotMatch(render({...project,services:[{...service,repo:'sibling',drift:'not_applicable'}]}), /bbbbbbbb<\/td><td>bbbbbbbb/);
});
test('untrusted fields are escaped and invalid host identifiers never displayed', () => {
  const {context:c} = setup();
  const out=c.renderGlanceWorkers({hosts:[{...host,workers:[{...worker,id:'<img src=x>'}]},{...host,host_id:'private.example'}]});
  assert.match(out,/&lt;img/); assert.doesNotMatch(out,/<img|private.example/);
});
test('requests start independently; failure clears old state and next refresh recovers', async () => {
  const calls=[]; let offline=false; let resolveEpics;
  const {context:c,nodes}=setup(async url => {
    calls.push(url);
    if (offline) throw Error('offline');
    if (url==='/api/epics/v1') return new Promise(resolve => {resolveEpics=resolve;});
    if (url==='/api/occupancy') return {hosts:{}};
    if (url==='/api/fleet/workers/v1') return {hosts:[host]};
    return {hosts:{'host-teacher':project}};
  });
  const pending=c.loadGlance(); await new Promise(setImmediate);
  assert.equal(calls.length,4); assert.match(nodes['glance-projects'].innerHTML,/aaaaaaaa/);
  resolveEpics({streams:[]}); await pending;
  offline=true; await c.loadGlance();
  for (const key of ['epics','hosts','workers','projects']) assert.equal(nodes[`glance-${key}`].textContent,'Unknown — lookup unavailable');
  offline=false; const retry=c.loadGlance(); await new Promise(setImmediate); resolveEpics({streams:[]}); await retry;
  assert.match(nodes['glance-workers'].innerHTML,/seat-one/);
});
test('malformed payload is unavailable, not an empty fleet', async () => {
  const {context:c,nodes}=setup(async () => ({})); await c.loadGlance();
  for (const key of ['epics','hosts','workers','projects']) assert.match(nodes[`glance-${key}`].textContent,/unavailable/);
});
test('related cross-source observations form one seat without swallowing different runs', () => {
  const {context:c}=setup();
  const driver={kind:'driver',source:'driver',agent:'codex',id:'instance-one',state:'live',related:[{source:'delegate',id:'seat-one'}]};
  const delegate={...worker,source:'delegate',related:[{source:'driver',id:'instance-one'}]};
  assert.equal(c.uniqueSeats([driver,delegate]).length,1);
  assert.equal(c.uniqueSeats([driver,delegate,{...delegate,run_id:'87654321'}]).length,2);
  const conflict=c.uniqueSeats([driver,{...delegate,state:'zombie'}]);
  assert.equal(conflict[0].state,'unknown (conflicting reports)');
  assert.equal(c.uniqueSeats([{...driver,related:[]},{...delegate,related:[]}]).length,2);
});
test('one failed lookup leaves the other three panels usable with a four-second deadline', async () => {
  const {context:c,nodes}=setup(async (url, timeout) => {
    assert.equal(timeout,4000);
    if (url==='/api/occupancy') throw Error('offline');
    if (url==='/api/epics/v1') return {streams:[]};
    if (url==='/api/fleet/workers/v1') return {hosts:[host]};
    return {hosts:{'host-teacher':project}};
  });
  await c.loadGlance();
  assert.match(nodes['glance-hosts'].textContent,/unavailable/);
  assert.match(nodes['glance-epics'].innerHTML,/No epics reported/);
  assert.match(nodes['glance-workers'].innerHTML,/seat-one/);
  assert.match(nodes['glance-projects'].innerHTML,/aaaaaaaa/);
});
