const {test, before, after} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const puppeteer = require('puppeteer');
const root = path.resolve(__dirname, '..');
let browser;
const coverage = new Map();
const attack = `sample'\"><img src=x onerror="window.injected=true">`;
const track = (overrides={}) => ({total:2,profile:'core',module_source:'curriculum',research_done:1,content_done:1,audit_passing:1,reviewed:1,final_review_done:0,dossier_done:0,published_mdx:0,generated_md:1,audit_stale:0,...overrides});
const overviewTrack = (id='a1') => ({id,name:attack,module_count:2,pct_complete:50,stats:{pass:1,content_complete:1,fail:0,unaudited:0,missing:0,final_review:0,research:{total:1}}});
const moduleRow = (slug='one') => ({num:1,slug,status:'pass',word_count:10,word_target:20,pipeline_version:'v6',research:{exists:true,score:8},has_final_review:false});
const moduleDetail = (slug='one', id='a1') => ({track:id,slug,plan:{title:attack,objectives:[attack],content_outline:[{title:attack}],grammar:[attack]},meta:{grammar:attack},lesson:{word_count:10,sections:[attack]},research:{exists:true,words:5,score:8,dimensions:{[attack]:{score:1,max:2}},gaps:[attack],content_alignment:{reasons:[attack]}},status:{overall:{status:'pass'}},status_is_fresh:false,pipeline_version:'v6'});
const wikiTrack = (id='a1') => ({track:id,total:2,compiled:1,pct:50});
const wikiModule = (slug='one') => ({slug,compiled:true,word_count:10,source_count:2,compiled_at:'invalid'});
const weak = (id='a1', slug=attack) => ({track:id,slug,num:1,issues:['audit_fail',`research_score_${attack}`,`low_words_${attack}`,attack],word_count:10,word_target:20,research_score:null});
const issue = (id='a1') => ({track:id,slug:attack,num:1,title:attack,severity:attack,source:attack,location:attack,fix:attack});
const score = (id='folk') => ({track:id,count:2,scored:1,modules:[{num:1,slug:attack,scored:true,status:attack,aggregate:{terminal_verdict:attack,min_dim:attack,min_score:8},dimensions:{pedagogical:8,engagement:6,beauty:4}}, {num:2,slug:'unscored',scored:false,status:'pending'}]});
const base = {
  '/api/dashboard/overview': {tracks:[overviewTrack(),overviewTrack('a2')]},
  '/api/dashboard/track/a1': {track_id:'a1',modules:[moduleRow(),moduleRow('two')],stats:overviewTrack().stats},
  '/api/dashboard/track/a2': {track_id:'a2',modules:[moduleRow('second-track')],stats:overviewTrack().stats},
  '/api/dashboard/module/a1/one':moduleDetail(),
  '/api/dashboard/module/a1/two':moduleDetail('two'),
  '/api/state/summary':{tracks:{a1:track(),a2:track(),planned:track({module_source:'plans-fallback'})},meta:{generated_at:'2026-01-01T00:00:00Z',age_s:12,stale:true}},
  '/api/state/pipeline-versions':{per_track:{a1:{v6:1,v5:1,v3:0,unbuilt:0},a2:{v6:2,v5:0,v3:0,unbuilt:0}}},
  '/api/state/pipeline/a1':{track:'a1',modules:[{...moduleRow(attack),audit:'pass',phases:{[attack]:{status:attack}},dossier:{exists:true,source:attack}}]},
  '/api/state/research-coverage':{tracks:{[attack]:{total_modules:2,has_research:1,pct_coverage:50,quality:{exemplary:1,thin:1},avg_score:8,needs_upgrade:1}}},
  '/api/state/review-coverage':{tracks:{[attack]:{total_built:1,has_review:1,has_final_review:0,avg_score:8,pass_rate:1,total_issues_found:0,plan_reviewed:0,plan_pass:0,plan_fail:0,plan_needs_fixes:0}}},
  '/api/state/issues':{issues:[issue()],total:1},
  '/api/state/weak-points':{modules:[weak()],count:501},
  '/api/state/scores/folk':score(),
  '/api/state/scores/a1':score('a1'),
  '/api/build/events/active':{active:[{level:'a1',slug:attack,current_phase:attack,age_s:30}]},
  '/api/build/events/recent':{events:[{level:'a1',slug:attack,ts:attack,phase:attack,agent:attack,ok:null,duration_s:2}]},
  '/api/wiki/status':{tracks:[wikiTrack(),wikiTrack('a2'),wikiTrack('planned')]},
  '/api/wiki/status/a1':[wikiModule()],
  '/api/wiki/status/a2':[wikiModule('second-track')],
  '/api/wiki/quality-gate/a1':{a1:{'one.md':[attack]}},
  '/api/wiki/quality-gate/a2':{a2:{}},
  '/api/wiki/build-log':{events:[{track:'a1',slug:attack,event:attack,ts:attack,summary:attack}]},
};
before(async () => { browser = await puppeteer.launch({headless:true,args:['--no-sandbox']}); });
after(async () => {
  await browser.close();
  for (const [name, {text, covered, functions}] of coverage) {
    let total=0, used=0;
    for (let i=0;i<text.length;i++) if (/\S/.test(text[i])) {total++; if(covered[i]) used++;}
    const percent=100*used/total;
    console.log(`${name}: browser JS coverage ${percent.toFixed(1)}% (${used}/${total} non-whitespace characters)`);
    assert.ok(percent >= 80, name+' browser script coverage below 80%');
    const critical=name==='/curriculum-dashboard.html'?['loadTrackDetail']:name==='/quality.html'?['loadResearch','loadReviews','filterWeak']:[];
    for (const functionName of critical) {
      const {startOffset,endOffset}=functions.get(functionName);
      const used=covered.slice(startOffset,endOffset).reduce((sum,value)=>sum+value,0);
      const percent=100*used/(endOffset-startOffset);
      console.log(`${name} ${functionName}: V8 function span coverage ${percent.toFixed(1)}% (${used}/${endOffset-startOffset} code units)`);
      assert.ok(percent>=80,functionName+' executable span coverage below 80%');
    }
  }
});
function deferred() { let resolve; const promise = new Promise(r => {resolve=r;}); return {promise,resolve}; }
async function open(name, feeds={}) {
  const page = await browser.newPage();
  const errors = [], calls = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.coverage.startJSCoverage({includeRawScriptCoverage:true});
  await page.setRequestInterception(true);
  page.on('request', async request => {
    const url=new URL(request.url());
    try {
      if (url.pathname.startsWith('/api/')) {
        calls.push(url.pathname+url.search);
        let value = Object.hasOwn(feeds,url.pathname) ? feeds[url.pathname] : base[url.pathname];
        if (typeof value === 'function') value = await value(url,request);
        if (value === undefined) return request.respond({status:404,body:'missing synthetic endpoint'});
        if (value?.http) return request.respond({status:value.http,body:'synthetic unavailable'});
        return request.respond({status:200,contentType:'application/json',body:value?.raw ?? JSON.stringify(value)});
      }
      if (url.pathname === '/' + name + '.html') return request.respond({status:200,contentType:'text/html',body:fs.readFileSync(path.join(root,'dashboards',name+'.html'),'utf8')});
      return request.respond({status:200,body:''});
    } catch (error) { errors.push(error.message); }
  });
  await page.goto('http://reader.test/'+name+'.html',{waitUntil:'domcontentloaded'});
  return {page,errors,calls,feeds};
}
async function settled(page, id) { await page.waitForFunction(id=>document.getElementById(id)?.getAttribute('aria-busy') === 'false',{},id); }
async function text(page,id) { return page.$eval('#'+id,n=>n.textContent); }
async function inert(page) {
  assert.equal(await page.evaluate(()=>Boolean(window.injected)),false);
  assert.equal(await page.$$eval('img,[onerror],[onfocus]',nodes=>nodes.length),0);
}
async function finish(ctx) {
  assert.deepEqual(ctx.errors,[]);
  assert.ok(ctx.calls.every(c=>!c.includes('fresh=')&&!c.includes('agent-monitor')));
  for (const entry of await ctx.page.coverage.stopJSCoverage()) {
    if (!entry.url.startsWith('http://reader.test/')) continue;
    const name=new URL(entry.url).pathname;
    if (!coverage.has(name)) coverage.set(name,{text:entry.text,covered:new Uint8Array(entry.text.length),functions:new Map()});
    const merged=coverage.get(name);
    for (const {start,end} of entry.ranges) merged.covered.fill(1,start,end);
    for (const fn of entry.rawScriptCoverage.functions) if (fn.functionName) merged.functions.set(fn.functionName,fn.ranges[0]);
  }
  await ctx.page.close();
}

test('R05 curriculum has scoped failure/retry at overview, track and module; metadata stays inert', async () => {
  const ctx=await open('curriculum-dashboard',{'/api/dashboard/overview':{http:503}}), {page,feeds}=ctx;
  await settled(page,'overview-content'); assert.match(await text(page,'overview-content-reader-status'),/HTTP 503/);
  feeds['/api/dashboard/overview']=base['/api/dashboard/overview'];
  await page.click('#overview-content-reader-status button'); await settled(page,'overview-content');
  feeds['/api/dashboard/track/a1']={raw:'{"modules":'};
  await page.click('.treemap-cell'); await settled(page,'track-detail');
  assert.match(await text(page,'track-detail-reader-status'),/Parse failure/); assert.match(await text(page,'overview-content'),/A1/);
  feeds['/api/dashboard/track/a1']=base['/api/dashboard/track/a1'];
  await page.click('#track-detail-reader-status button'); await settled(page,'track-detail');
  feeds['/api/dashboard/module/a1/one']={http:500}; await page.click('.module-select'); await settled(page,'right-panel');
  assert.match(await text(page,'right-panel-reader-status'),/HTTP 500/); assert.match(await text(page,'track-detail'),/one/);
  feeds['/api/dashboard/module/a1/one']=base['/api/dashboard/module/a1/one'];
  await page.click('#right-panel-reader-status button'); await settled(page,'right-panel');
  assert.match(await text(page,'right-panel'),/Research dimensions/); assert.ok((await text(page,'right-panel')).includes(attack));
  assert.match(await text(page,'right-panel-reader-status'),/Source age unknown/); await inert(page); await finish(ctx);
});
test('R05 reversed track/module responses and track clear cannot replace current selection', async () => {
  const slowTrack=deferred(), slowModule=deferred();
  const ctx=await open('curriculum-dashboard',{'/api/dashboard/track/a1':()=>slowTrack.promise}), {page,feeds}=ctx;
  await settled(page,'overview-content'); await page.click('.treemap-cell');
  await page.evaluate(()=>selectTrack('a2')); await settled(page,'track-detail');
  slowTrack.resolve(base['/api/dashboard/track/a1']); await page.waitForNetworkIdle({idleTime:50});
  await page.waitForFunction(()=>!readerStates.get('track-detail').pending);
  assert.match(await text(page,'track-detail'),/second-track/); assert.doesNotMatch(await text(page,'track-detail'),/\bone\b/);
  feeds['/api/dashboard/track/a1']=base['/api/dashboard/track/a1']; await page.evaluate(()=>selectTrack('a1')); await settled(page,'track-detail');
  feeds['/api/dashboard/module/a1/one']=()=>slowModule.promise;
  await page.click('.module-select'); await page.evaluate(()=>loadModuleDetail('a1','two')); await settled(page,'right-panel');
  slowModule.resolve(moduleDetail('one')); await page.waitForNetworkIdle({idleTime:50}); await page.waitForFunction(()=>document.querySelector('#right-panel h2')?.textContent==='two');
  feeds['/api/dashboard/overview']={tracks:[]}; await page.evaluate(()=>fetchOverview()); await settled(page,'overview-content');
  assert.doesNotMatch(await text(page,'right-panel'),/Research dimensions/); assert.match(await text(page,'overview-content'),/No operational tracks/);
  await finish(ctx);
});
test('R13 progress keeps overview on track/build-source failure and safely exposes keyboard tooltips', async () => {
  const ctx=await open('progress',{'/api/state/pipeline-versions':{http:503},'/api/state/pipeline/a1':{http:500}}),{page,feeds}=ctx;
  await settled(page,'tracks-container'); await settled(page,'build-counts-content');
  assert.equal(await text(page,'total-modules'),'4'); assert.equal(await text(page,'total-rebuild'),'unknown');
  assert.match(await text(page,'tracks-container-reader-status'),/Stale/);
  assert.match(await text(page,'tracks-container-reader-status'),/Snapshot generated/);
  assert.match(await text(page,'tracks-container-reader-status'),/Cache age/);
  await page.click('[data-track="a1"]'); await settled(page,'panel-a1'); assert.match(await text(page,'panel-a1-reader-status'),/HTTP 500/);
  assert.equal(await text(page,'total-modules'),'4');
  feeds['/api/state/pipeline/a1']=base['/api/state/pipeline/a1']; await page.click('#panel-a1-reader-status button'); await settled(page,'panel-a1');
  await page.focus('.module-chip'); assert.ok((await text(page,'tooltip')).includes(attack));
  assert.ok((await page.$eval('.module-chip',n=>n.getAttribute('data-tip'))).includes(attack));
  feeds['/api/state/pipeline-versions']=base['/api/state/pipeline-versions']; await page.click('#build-counts-content-reader-status button'); await settled(page,'build-counts-content');
  assert.equal(await text(page,'total-rebuild'),'1'); assert.equal(await text(page,'total-current-builds'),'3');
  await inert(page); await finish(ctx);
});
test('R13 malformed summary is not zero; missing per-track build fields are unknown; valid zero is retained', async () => {
  const ctx=await open('progress',{'/api/state/summary':{},'/api/state/pipeline-versions':{per_track:{a1:{v6:0}}}}),{page,feeds}=ctx;
  await settled(page,'tracks-container'); assert.match(await text(page,'tracks-container-reader-status'),/Malformed success/);
  feeds['/api/state/summary']={tracks:{a1:track({total:0})}}; await page.click('#tracks-container-reader-status button'); await settled(page,'tracks-container');
  assert.equal(await text(page,'total-modules'),'0');
  feeds['/api/state/summary']={tracks:{a1:track()}}; await page.evaluate(()=>load()); await settled(page,'build-counts-content');
  assert.match(await text(page,'build-counts-content'),/coverage unknown/); assert.equal(await text(page,'total-current-builds'),'—');
  await finish(ctx);
});
test('R14 quality populated-to-empty-to-populated uses one results container, safe metadata and stable filters', async () => {
  const ctx=await open('quality'),{page,feeds}=ctx;
  for(const id of ['research-content','reviews-content','issues-content','weak-content','scores-content']) await settled(page,id);
  assert.ok((await text(page,'research-content')).includes(attack));
  await page.click('[data-tab="weak"]'); assert.equal(await page.$eval('[data-tab="weak"]',n=>n.getAttribute('aria-selected')),'true');
  await page.evaluate(()=>{const s=document.getElementById('weak-track-filter');s.append(new Option('empty','empty'));s.value='empty';s.dispatchEvent(new Event('change'));});
  assert.match(await text(page,'weak-results'),/No weak modules returned/); assert.equal(await page.$$eval('#weak-results tbody tr',n=>n.length),0);
  await page.select('#weak-track-filter',''); assert.equal(await page.$$eval('#weak-results tbody tr',n=>n.length),1);
  feeds['/api/state/weak-points']={modules:[],count:0}; await page.evaluate(()=>loadWeak()); await settled(page,'weak-content');
  assert.match(await text(page,'weak-results'),/No weak modules returned/);
  feeds['/api/state/weak-points']=base['/api/state/weak-points']; await page.evaluate(()=>loadWeak()); await settled(page,'weak-content');
  assert.equal(await page.$$eval('#weak-results',n=>n.length),1); assert.equal(await page.$$eval('#weak-stats',n=>n.length),1);
  await page.click('[data-tab="issues"]'); await page.focus('.issue-card'); await page.keyboard.press('Enter');
  assert.equal(await page.$eval('.issue-card',n=>n.getAttribute('aria-expanded')),'true');
  await inert(page); await finish(ctx);
});
test('R14 one failed feed does not erase siblings; score filter races and empty values stay honest', async () => {
  const old=deferred(); const ctx=await open('quality',{'/api/state/research-coverage':{http:503},'/api/state/scores/folk':()=>old.promise}),{page,feeds}=ctx;
  await settled(page,'research-content'); await settled(page,'reviews-content');
  assert.match(await text(page,'research-content-reader-status'),/HTTP 503/); assert.ok((await text(page,'reviews-content')).includes(attack));
  await page.click('[data-tab="scores"]'); await page.select('#scores-track-filter','a1'); await settled(page,'scores-content');
  old.resolve(score()); await page.waitForNetworkIdle({idleTime:50}); assert.match(await text(page,'scores-content'),/track a1/);
  feeds['/api/state/scores/a1']={track:'a1',modules:[],count:0,scored:0}; await page.evaluate(()=>loadScores()); await settled(page,'scores-content');
  assert.match(await text(page,'scores-content'),/0\/0/); assert.equal(await page.$$eval('#scores-content tbody tr',n=>n.length),0);
  feeds['/api/state/issues']={issues:[issue(),null]}; await page.evaluate(()=>loadIssues()); await settled(page,'issues-content');
  assert.match(await text(page,'issues-content-reader-status'),/Partial/);
  feeds['/api/state/issues']={}; await page.evaluate(()=>loadIssues()); await settled(page,'issues-content');
  assert.match(await text(page,'issues-content-reader-status'),/Malformed success.*Historical/);
  await inert(page); await finish(ctx);
});
test('R03 active/recent malformed success differs from empty, valid zero and unknown fields', async () => {
  const ctx=await open('build-events',{'/api/build/events/active':{},'/api/build/events/recent':{raw:'<html>not JSON</html>'}}),{page,feeds}=ctx;
  await settled(page,'active-content'); await settled(page,'recent-content');
  assert.match(await text(page,'active-content-reader-status'),/Malformed success/); assert.match(await text(page,'recent-content-reader-status'),/Parse failure/);
  feeds['/api/build/events/active']={active:[]}; feeds['/api/build/events/recent']={events:[]};
  await page.click('#active-content-reader-status button'); await page.click('#recent-content-reader-status button'); await settled(page,'active-content'); await settled(page,'recent-content');
  assert.match(await text(page,'active-content'),/No active build rows returned/); assert.match(await text(page,'recent-content'),/No recent build events returned/);
  feeds['/api/build/events/active']={active:[{level:'a1',slug:attack,age_s:0},null]};
  feeds['/api/build/events/recent']=base['/api/build/events/recent']; await page.evaluate(()=>refreshAll()); await settled(page,'active-content'); await settled(page,'recent-content');
  assert.match(await text(page,'active-content-reader-status'),/Partial/); assert.match(await text(page,'active-content'),/0.0s/);
  assert.match(await text(page,'recent-content'),/unknown event time/); assert.match(await text(page,'recent-content'),/unknown/);
  await inert(page); await finish(ctx);
});
test('R03 late filter success/failure cannot overwrite newer results; failure retains original fetch time', async () => {
  const old=deferred(); const ctx=await open('build-events'),{page,feeds}=ctx;
  await settled(page,'active-content'); await settled(page,'recent-content');
  feeds['/api/build/events/recent']=url=>url.searchParams.get('slug')==='old'?old.promise:{events:[{level:'a1',slug:'new',ok:true,ts:'2000-01-01',duration_s:90}]};
  await page.evaluate(()=>{document.getElementById('slug-filter').value='old';refreshRecent();});
  await page.evaluate(()=>{document.getElementById('slug-filter').value='new';refreshRecent();}); await settled(page,'recent-content');
  old.resolve({http:503}); await page.waitForNetworkIdle({idleTime:50}); await page.waitForFunction(()=>document.getElementById('recent-content').textContent.includes('new'));
  const previous=await page.$eval('#recent-content-reader-status .reader-clock',n=>n.textContent);
  feeds['/api/build/events/recent']={http:500}; await page.evaluate(()=>refreshRecent()); await settled(page,'recent-content');
  assert.match(await text(page,'recent-content-reader-status'),/Historical values retained/); assert.match(await text(page,'recent-content'),/new/);
  assert.equal(await page.$eval('#recent-content-reader-status .reader-clock',n=>n.textContent),previous);
  await finish(ctx);
});
test('R16 wiki gates fail independently, malformed successes cannot become no issues or empty logs', async () => {
  const ctx=await open('wiki',{'/api/wiki/quality-gate/a1':{http:503},'/api/wiki/build-log':{}}),{page,feeds}=ctx;
  await settled(page,'progress-content'); await settled(page,'summary-content'); await settled(page,'detail-content'); await settled(page,'gate-content'); await settled(page,'log-content');
  assert.match(await text(page,'detail-content'),/Gate unknown/); assert.match(await text(page,'detail-content'),/compiled/);
  assert.match(await text(page,'gate-content-reader-status'),/HTTP 503/); assert.match(await text(page,'log-content-reader-status'),/Malformed success/);
  feeds['/api/wiki/quality-gate/a1']=base['/api/wiki/quality-gate/a1']; await page.click('#gate-content-reader-status button'); await settled(page,'gate-content');
  assert.ok((await text(page,'detail-content')).includes(attack));
  feeds['/api/wiki/build-log']={events:[]}; await page.click('#log-content-reader-status button'); await settled(page,'log-content');
  assert.match(await text(page,'log-content'),/No build log events returned/);
  feeds['/api/wiki/status/a1']={modules:[]}; await page.evaluate(()=>loadTrackDetail()); await settled(page,'detail-content');
  assert.match(await text(page,'detail-content-reader-status'),/Malformed success/);
  await inert(page); await finish(ctx);
});
test('R16 selection/filter persists through refresh, reversed responses and explicit clear remain respected', async () => {
  const slow=deferred(); const ctx=await open('wiki'),{page,feeds}=ctx;
  await settled(page,'summary-content'); await settled(page,'progress-content'); await settled(page,'detail-content'); await settled(page,'log-content');
  await page.select('#log-track-filter','a2');
  await page.evaluate(()=>loadProgress()); await settled(page,'summary-content'); await settled(page,'progress-content');
  assert.equal(await page.$eval('#log-track-filter',n=>n.value),'a2');
  feeds['/api/wiki/status/a1']=()=>slow.promise;
  await page.evaluate(()=>{selectTrack('a1');}); await page.evaluate(()=>selectTrack('a2')); await settled(page,'detail-content');
  slow.resolve([wikiModule('old-track')]); await page.waitForNetworkIdle({idleTime:50}); assert.match(await text(page,'detail-content'),/second-track/);
  await page.click('button[onclick="selectTrack(null)"]'); await page.evaluate(()=>loadProgress()); await settled(page,'progress-content');
  assert.match(await text(page,'detail-content'),/Select a track/); assert.equal(await text(page,'gate-content'),'');
  feeds['/api/wiki/build-log']={events:[{track:'a2',slug:'new-log',event:attack,ts:'invalid',summary:attack}]};
  await page.evaluate(()=>loadBuildLog()); await settled(page,'log-content'); assert.match(await text(page,'log-content'),/new-log/);
  await inert(page); await finish(ctx);
});
test('R16 malformed summary is separate from valid wiki status; empty operational set is valid', async () => {
  const ctx=await open('wiki',{'/api/state/summary':{},'/api/wiki/status':{tracks:[wikiTrack(),null]}}),{page,feeds}=ctx;
  await settled(page,'summary-content'); await settled(page,'progress-content');
  assert.match(await text(page,'summary-content-reader-status'),/Malformed success/);
  assert.match(await text(page,'progress-content-reader-status'),/Partial/); assert.match(await text(page,'progress-content'),/a1/);
  feeds['/api/state/summary']={tracks:{}}; await page.click('#summary-content-reader-status button'); await settled(page,'summary-content');
  assert.match(await text(page,'progress-content'),/No operational wiki tracks returned/);
  await finish(ctx);
});

test('reader clocks advance cached ages, retain upstream stale and never invent partial-first last-good time', async () => {
  const ctx=await open('build-events',{'/api/build/events/active':{active:[{level:'a1',slug:'one',age_s:5},null],meta:{generated_at:'2999-01-01',age_s:7,stale_after_s:10}}}),{page}=ctx;
  await settled(page,'active-content');
  const initial=await text(page,'active-content-reader-status');
  assert.match(initial,/Last partial fetch/); assert.doesNotMatch(initial,/Last successful fetch|Snapshot generated/);
  const advanced=await page.evaluate(()=>{const now=Date.now(); Date.now=()=>now+20000; return readerClock(readerStates.get('active-content'));});
  assert.match(advanced,/Cache age 27s/); assert.match(advanced,/Stale snapshot cache/);
  assert.match(advanced,/Source age unknown/); await finish(ctx);
});
test('real focus and reduced-motion/narrow layout survive refreshed curriculum and progress rows', async () => {
  for (const name of ['curriculum-dashboard','progress']) {
    const ctx=await open(name),{page}=ctx;
    await page.setViewport({width:375,height:800}); await page.emulateMediaFeatures([{name:'prefers-reduced-motion',value:'reduce'}]);
    if (name==='curriculum-dashboard') {
      await settled(page,'overview-content'); await page.focus('.treemap-cell');
      await page.evaluate(()=>fetchOverview()); await settled(page,'overview-content');
      assert.equal(await page.evaluate(()=>document.activeElement.dataset.readerKey),'a1');
      await page.keyboard.press('Enter'); await settled(page,'track-detail');
      await page.focus('.module-select'); await page.evaluate(()=>loadTrackDetail('a1')); await settled(page,'track-detail');
      assert.equal(await page.evaluate(()=>document.activeElement.dataset.readerKey),'one');
    } else {
      await settled(page,'tracks-container'); await page.focus('[data-track="a1"]'); await page.keyboard.press('Enter'); await settled(page,'panel-a1');
      await page.focus('.module-chip'); await page.evaluate(()=>load()); await settled(page,'tracks-container');
      assert.equal(await page.evaluate(()=>document.activeElement.dataset.readerKey),attack);
    }
    assert.equal(await page.evaluate(()=>matchMedia('(prefers-reduced-motion: reduce)').matches),true);
    assert.ok(await page.evaluate(()=>document.getElementById('reader-main').getBoundingClientRect().width<=375));
    await inert(page); await finish(ctx);
  }
});
test('all scoped validators reject wholly malformed rows; optional values stay unknown', async () => {
  for (const [name,id,endpoint,bad,good,invoke] of [
    ['curriculum-dashboard','overview-content','/api/dashboard/overview',{tracks:[null]}, {tracks:[]},'fetchOverview()'],
    ['progress','tracks-container','/api/state/summary',{tracks:{a1:null}},{tracks:{}},'load()'],
    ['quality','weak-content','/api/state/weak-points',{modules:[{track:'a1',slug:'one',issues:'broken'}]},{modules:[],count:0},'loadWeak()'],
    ['wiki','progress-content','/api/wiki/status',{tracks:[{track:'a1',total:2,pct:'bad'}]},{tracks:[]},'loadProgress()'],
  ]) {
    const ctx=await open(name,{[endpoint]:bad}),{page,feeds}=ctx; await settled(page,id);
    assert.match(await text(page,id+'-reader-status'),/Malformed success/);
    feeds[endpoint]=good; await page.evaluate(invoke); await settled(page,id);
    assert.doesNotMatch(await text(page,id+'-reader-status'),/Malformed success/); await finish(ctx);
  }
});

test('bounded polling, edit debounce and visibility recovery run the shipped event handlers', async () => {
  const contexts=[];
  try {
    for (const name of ['curriculum-dashboard','progress','quality','build-events','wiki']) contexts.push(await open(name));
    for (const ctx of contexts) {
      await ctx.page.waitForNetworkIdle({idleTime:50});
      await ctx.page.evaluate(() => {
        Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});
        document.dispatchEvent(new Event('visibilitychange'));
        Object.defineProperty(document,'hidden',{configurable:true,get:()=>false});
        document.dispatchEvent(new Event('visibilitychange'));
      });
    }
    const events=contexts[3]; await events.page.bringToFront(); await events.page.type('#slug-filter','edited');
    await events.page.waitForNetworkIdle({idleTime:500});
    const editState=await events.page.evaluate(()=>({value:document.getElementById('slug-filter').value,scope:readerStates.get('recent-content')?.scope,pending:Boolean(readerStates.get('recent-content')?.pending)}));
    assert.deepEqual(editState,{value:'edited',scope:'/api/build/events/recent?limit=100&slug=edited',pending:false},JSON.stringify({editState,errors:events.errors,calls:events.calls}));
    // Let the real bounded clock/poll interval fire while all five pages are open.
    await contexts[0].page.waitForFunction(()=>readerStates.get('overview-content')?.fetchedAt && Date.now()-readerStates.get('overview-content').fetchedAt>=10500,{polling:100,timeout:15000});
    assert.ok(events.calls.some(c=>c.includes('slug=edited')));
    for (const ctx of contexts) await finish(ctx);
  } finally {
    for (const ctx of contexts) if (!ctx.page.isClosed()) await ctx.page.close();
  }
});

test('partial overview/status cannot clear a selected track absent from the incomplete list', async () => {
  for (const name of ['curriculum-dashboard','wiki']) {
    const ctx=await open(name), {page,feeds}=ctx;
    const curriculum=name==='curriculum-dashboard';
    await settled(page,curriculum?'overview-content':'progress-content');
    if (!curriculum) await settled(page,'summary-content');
    await page.evaluate(()=>selectTrack('a1')); await settled(page,curriculum?'track-detail':'detail-content');
    feeds[curriculum?'/api/dashboard/overview':'/api/wiki/status']={tracks:[curriculum?overviewTrack('a2'):wikiTrack('a2'),null]};
    await page.evaluate(curriculum?'fetchOverview()':'loadProgress()');
    await settled(page,curriculum?'overview-content':'progress-content');
    assert.equal(await page.evaluate(()=>selectedTrack),'a1');
    assert.match(await text(page,curriculum?'overview-content-reader-status':'progress-content-reader-status'),/Partial/);
    await finish(ctx);
  }
});

test('B3C partial/error track refresh and repeated click preserve selected module detail and Retry', async () => {
  const ctx=await open('curriculum-dashboard'), {page,feeds}=ctx;
  await settled(page,'overview-content');
  await page.evaluate(()=>selectTrack('a1')); await settled(page,'track-detail');
  await page.click('.module-select'); await settled(page,'right-panel');
  const original=await page.$eval('#right-panel',n=>n.innerHTML);
  const generation=await page.evaluate(()=>readerStates.get('right-panel').generation);
  for (const payload of [
    {track_id:'a1',modules:[moduleRow('two'),null]},
    {track_id:'a1',partial:true,modules:[moduleRow('two')]},
    {track_id:'a1',modules:[moduleRow('two')],meta:{error:'synthetic unavailable'}},
  ]) {
    feeds['/api/dashboard/track/a1']=payload;
    await page.evaluate(()=>fetchOverview()); await settled(page,'overview-content'); await settled(page,'track-detail');
    await page.evaluate(()=>selectTrack('a1')); await settled(page,'track-detail');
    assert.equal(await page.evaluate(()=>selectedModule),'one');
    assert.equal(await page.$eval('#right-panel',n=>n.innerHTML),original);
    assert.equal(await page.evaluate(()=>readerStates.get('right-panel').generation),generation);
    assert.equal(await page.$$eval('#right-panel-reader-status button',n=>n.length),1);
    assert.match(await text(page,'track-detail-reader-status'),/Partial|Source unavailable/);
  }
  await page.click('#right-panel-reader-status button'); await settled(page,'right-panel');
  assert.equal(await page.$eval('#right-panel h2',n=>n.textContent),'one');
  const slow=deferred(); feeds['/api/dashboard/track/a1']=()=>slow.promise;
  await page.evaluate(()=>{loadTrackDetail('a1');});
  await page.evaluate(()=>selectTrack('a2')); await settled(page,'track-detail');
  slow.resolve({track_id:'a1',modules:[]}); await page.waitForNetworkIdle({idleTime:50});
  assert.equal(await page.evaluate(()=>selectedTrack),'a2');
  assert.match(await text(page,'track-detail'),/second-track/);
  feeds['/api/dashboard/track/a1']=base['/api/dashboard/track/a1'];
  await page.evaluate(()=>selectTrack('a1')); await settled(page,'track-detail');
  await page.evaluate(()=>loadModuleDetail('a1','one')); await settled(page,'right-panel');
  feeds['/api/dashboard/track/a1']={track_id:'a1',modules:[moduleRow('two')]};
  await page.evaluate(()=>loadTrackDetail('a1')); await settled(page,'track-detail');
  assert.equal(await page.evaluate(()=>selectedModule),null);
  assert.equal(await page.$$eval('#right-panel-reader-status',n=>n.length),0);
  await page.evaluate(()=>loadModuleDetail('a1','two')); await settled(page,'right-panel');
  const detail=deferred(); feeds['/api/dashboard/module/a1/two']=()=>detail.promise;
  await page.evaluate(()=>{loadModuleDetail('a1','two');clearDetail();});
  detail.resolve(moduleDetail('two')); await page.waitForNetworkIdle({idleTime:50});
  assert.equal(await page.evaluate(()=>selectedModule),null);
  assert.match(await text(page,'right-panel'),/Select a module/);
  await finish(ctx);
});

test('B3C quality text and color agree for absent, invalid, zero and measured metrics', async () => {
  const ctx=await open('quality'), {page,feeds}=ctx;
  await settled(page,'reviews-content'); await settled(page,'weak-content');
  const values=[undefined,null,'0.95',false,-1,5,0,0.5,0.9,1];
  feeds['/api/state/review-coverage']={tracks:Object.fromEntries(values.map((value,i)=>['case'+i,{total_built:1,pass_rate:value}]))};
  await page.evaluate(()=>loadReviews()); await settled(page,'reviews-content');
  assert.deepEqual(await page.$$eval('#reviews-content tbody tr',rows=>rows.map(r=>({text:r.cells[5].textContent,color:r.cells[5].style.color}))),[
    ...Array.from({length:6},()=>({text:'—',color:'var(--text3)'})),
    {text:'0%',color:'var(--red)'},{text:'50%',color:'var(--red)'},
    {text:'90%',color:'var(--green)'},{text:'100%',color:'var(--green)'},
  ]);
  const counts=[undefined,null,'10',false,-1,0,10,16,20];
  feeds['/api/state/weak-points']={modules:counts.map((value,i)=>({...weak('a1','case'+i),word_count:value}))};
  await page.evaluate(()=>loadWeak()); await settled(page,'weak-content');
  assert.deepEqual(await page.$$eval('#weak-results tbody tr',rows=>rows.map(r=>({text:r.cells[4].textContent,color:r.cells[4].style.color}))),[
    ...Array.from({length:5},()=>({text:'unknown/20',color:'var(--text2)'})),
    {text:'0/20',color:'var(--red)'},{text:'10/20',color:'var(--red)'},
    {text:'16/20',color:'var(--text2)'},{text:'20/20',color:'var(--text2)'},
  ]);
  // Count and target fields use the same nonnegative finite contract as their text.
  feeds['/api/state/weak-points']={modules:[{...weak('a1','bad-target'),word_count:0,word_target:'20'}]};
  feeds['/api/state/review-coverage']={tracks:{a1:{total_built:1,plan_pass:'1',plan_fail:'1',plan_needs_fixes:'1',total_issues_found:'1'}}};
  feeds['/api/state/research-coverage']={tracks:{a1:{total_modules:1,needs_upgrade:'1'}}};
  await page.evaluate(()=>Promise.all([loadWeak(),loadReviews(),loadResearch()]));
  assert.deepEqual(await page.$$eval('#reviews-content tbody tr td',cells=>[6,8,9,10].map(i=>({text:cells[i].textContent,color:cells[i].style.color}))),Array.from({length:4},()=>({text:'unknown',color:'var(--text3)'})));
  assert.equal(await page.$eval('#research-content tbody tr td:last-child',n=>n.style.color),'var(--text3)');
  assert.deepEqual(await page.$eval('#weak-results tbody tr td:nth-child(5)',n=>({text:n.textContent,color:n.style.color})),{text:'0',color:'var(--text2)'});
  await finish(ctx);
});

test('B3C direct shipped quality renderer rejects non-finite and coercible word measurements', () => {
  const vm=require('node:vm');
  const html=fs.readFileSync(path.join(root,'dashboards/quality.html'),'utf8');
  const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
  const results={innerHTML:''}, filter={value:''};
  const context=vm.createContext({setInterval:()=>{},document:{getElementById:id=>id==='weak-results'?results:filter}});
  vm.runInContext(script.slice(0,script.indexOf('// ---- Init ----')),context);
  for (const value of [undefined,null,'10',false,-1,NaN,Infinity,0,10,16,20]) {
    context.rows=[{...weak('a1','one'),word_count:value}];
    vm.runInContext('allWeak=rows;filterWeak()',context);
    const cell=results.innerHTML.match(/<td style="color:([^\"]+)">([^<]*\/20)<\/td>/);
    const known=typeof value==='number' && Number.isFinite(value) && value>=0;
    assert.ok(cell,results.innerHTML);
    assert.equal(cell[1],known && value<16?'var(--red)':'var(--text2)',String(value));
    assert.equal(cell[2],known?`${value}/20`:'unknown/20',String(value));
  }
});
