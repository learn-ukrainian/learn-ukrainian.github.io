const { test, before, after, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const puppeteer = require('puppeteer');

const root = path.resolve(__dirname, '..');
const hostile = `sample'"><img src=x onerror="globalThis.injection=1">`;
const timestamp = '2020-01-01T00:00:00Z';
let browser;
const pages = [];
const coverage = new Map();
before(async () => {
  const configured = process.env.PUPPETEER_EXECUTABLE_PATH;
  const cachedShell = await puppeteer.executablePath({ headless: 'shell' }).catch(() => null);
  const executablePath = configured || [cachedShell, '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser'].find(candidate => candidate && fs.existsSync(candidate));
  assert.ok(executablePath && fs.existsSync(executablePath), 'A configured, cached or system Chromium executable is required');
  browser = await puppeteer.launch({ executablePath, headless: executablePath === cachedShell ? 'shell' : true, args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'] });
});
afterEach(async () => {
  for (const entry of pages.splice(0)) {
    const reports = await entry.page.coverage.stopJSCoverage();
    for (const report of reports) {
      if (!/\/(admin|artifacts|consultation|image-explorer)\.html$/.test(report.url)) continue;
      const existing = coverage.get(report.url) || { text: report.text, ranges: [], functions: new Map() };
      existing.ranges.push(...report.ranges);
      for (const func of report.rawScriptCoverage?.functions || []) {
        const range = func.ranges[0];
        if (!func.functionName || !range) continue;
        const key = `${func.functionName}:${range.startOffset}`;
        existing.functions.set(key, (existing.functions.get(key) || false) || range.count > 0);
      }
      coverage.set(report.url, existing);
    }
    await entry.page.close();
  }
});
after(async () => {
  await browser?.close();
  const summary = {};
  for (const [url, entry] of coverage) {
    const merged = [];
    for (const r of entry.ranges.sort((a, b) => a.start - b.start)) {
      if (merged.length && r.start <= merged.at(-1).end) merged.at(-1).end = Math.max(merged.at(-1).end, r.end);
      else merged.push({ ...r });
    }
    const covered = merged.reduce((sum, r) => sum + r.end - r.start, 0);
    summary[new URL(url).pathname] = {
      coveredBytes: covered, totalBytes: entry.text.length,
      bytePercent: Math.round(covered / entry.text.length * 1000) / 10,
      namedFunctions: entry.functions.size,
      coveredNamedFunctions: [...entry.functions.values()].filter(Boolean).length,
      uncovered: [...entry.functions].filter(([, hit]) => !hit).map(([name]) => name.split(':')[0]),
    };
  }
  console.log('Shipped script coverage:', JSON.stringify(summary));
  if (coverage.size === 4) for (const [name, result] of Object.entries(summary)) assert.ok(result.bytePercent >= 80, `${name} shipped-script coverage below 80%`);
  if (process.env.TMPDIR) fs.writeFileSync(path.join(process.env.TMPDIR, 'maintenance-pages-coverage.json'), JSON.stringify(summary, null, 2));
});

const goodStats = { total: 1, annotated: 1, unannotated: 0, bad_candidates: 0, pdfs_on_disk: 1, teaching_value: { high: 1 }, element_type: { photo: 1 }, per_grade: { 3: { total: 1, annotated: 1 } } };
const annotation = { image_id: hostile, image_path: `grade-03/${hostile}.png`, description_uk: hostile, teaching_value: 'high', element_type: 'photo' };
const annotations = items => ({ items, total: items.length, total_pages: 1, page: 0, per_page: 50 });
const proposal = (name = hostile) => ({ filename: name, source_module: hostile, confidence: hostile, change_count: 1, target_files: [hostile], root_cause_summary: hostile, queued_at: timestamp });
const detail = (name = hostile) => ({ status: 'pending', source_module: name, proposed_changes: [{ file: hostile, find: hostile, replace: hostile, rationale: hostile }], root_cause: hostile, confidence: hostile, queued_at: timestamp });
const metrics = { total: 1, pending_queue: 1, by_outcome: { applied: 1 }, by_track: { [hostile]: 1 }, by_confidence: { [hostile]: 1 }, by_scope: { [hostile]: 1 }, top_root_causes: [[hostile, 1]] };
const artifact = overrides => ({ title: hostile, path: 'reports/sample.html', url: '/artifacts/reports/sample.html', class: hostile, author: hostile, date: '2020-01-01', related_issues: [hostile], related_prs: [hostile], agents: [hostile], ...overrides });
const defaultRoutes = {
  '/api/admin/health': { status: 'ok', broker: { status: 'healthy', size_human: '1 KB' }, disk: { used_pct: 40, free: '2 GB' }, uptime_seconds: 1 },
  '/api/admin/disk-usage': { breakdown: { sample: { exists: true, size_bytes: 1024, size_human: '1 KB' } }, total_human: '1 KB' },
  '/api/admin/maintenance/embedding-cache-stats': { exists: true, cached_files: 0, source_files: 1, total_size_human: '0 B' },
  '/api/admin/maintenance/annotation-stats': { total_images: 0, annotated: 0, empty_descriptions: 0, garbled_encoding: 0, annotation_rate: 0, teaching_value_distribution: { high: 0 } },
  '/api/artifacts/html': { artifacts: [artifact()], generated_at: timestamp },
  '/api/config': { levels: [{ id: 'sample' }] },
  '/api/consultation/queue': { pending: [proposal()], count: 1 },
  '/api/consultation/history': { consultations: [{ track: hostile, slug: hostile, outcome: hostile, confidence: hostile, scope: hostile, changes_count: 0, ts: timestamp }], total: 1 },
  '/api/consultation/metrics': metrics,
  '/api/images/textbooks': [{ stem: hostile, page_count: 2, image_count: 1 }],
  '/api/images/annotations': annotations([annotation]),
  '/api/images/stats': goodStats,
};

async function open(name, overrides = {}, hash = '') {
  const page = await browser.newPage();
  await page.coverage.startJSCoverage({ includeRawScriptCoverage: true });
  const routes = { ...defaultRoutes, ...overrides };
  const errors = [], mutations = [], requests = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.setRequestInterception(true);
  page.on('request', async request => {
    const url = new URL(request.url());
    if (url.protocol === 'data:') return request.continue();
    requests.push(url.pathname + url.search);
    if (request.method() !== 'GET') mutations.push({ path: url.pathname, query: url.search, method: request.method(), body: request.postData() });
    if (url.pathname === `/${name}.html`) return request.respond({ status: 200, contentType: 'text/html', body: fs.readFileSync(path.join(root, 'dashboards', name + '.html'), 'utf8') });
    if (url.pathname === '/monitor.css') return request.respond({ status: 200, contentType: 'text/css', body: fs.readFileSync(path.join(root, 'dashboards/monitor.css'), 'utf8') });
    if (url.pathname.startsWith('/images/') || url.pathname.includes('/page_render/')) return request.respond({ status: 200, contentType: 'image/svg+xml', body: '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="300"><rect width="200" height="300" fill="white"/></svg>' });
    let data = routes[url.pathname];
    if (typeof data === 'function') data = await data({ url, request });
    const response = data && Object.hasOwn(data, '$status') ? data : { $status: data === undefined ? 404 : 200, data: data ?? { error: 'unavailable' } };
    await request.respond({ status: response.$status, contentType: 'application/json', body: response.raw ?? JSON.stringify(response.data) });
  });
  await page.goto(`http://maintenance.test/${name}.html${hash}`, { waitUntil: 'networkidle0' });
  const entry = { page, routes, errors, mutations, requests };
  pages.push(entry);
  return entry;
}
async function text(page, selector) { return page.$eval(selector, el => el.textContent); }
async function inert(page) {
  assert.equal(await page.evaluate(() => globalThis.injection), undefined);
  assert.equal(await page.$$eval('[onerror]', els => els.length), 0);
}
function deferred() {
  let resolve;
  const promise = new Promise(r => { resolve = r; });
  return { promise, resolve };
}

 test('admin legacy backup, unknown and absent section hashes are safe and back works', async () => {
  const { page, errors, mutations } = await open('admin', {}, '#backup');
  assert.match(await text(page, '.section.active'), /Backup and restore status/);
  assert.equal(await page.$eval('#section-backup a', a => a.getAttribute('href')), '/fleet-board.html#ops');
  await page.evaluate(() => { location.hash = 'unknown\'"]'; });
  await page.waitForFunction(() => document.getElementById('section-health').classList.contains('active'));
  await page.goBack();
  await page.waitForFunction(() => document.getElementById('section-backup').classList.contains('active'));
  await page.evaluate(() => { document.getElementById('section-stats').remove(); activateSection('stats'); });
  assert.equal(await page.$eval('.section.active', el => el.id), 'section-health');
  await page.click('[data-section="maintenance"]');
  await page.goBack();
  await page.waitForFunction(() => document.getElementById('section-health').classList.contains('active'));
  assert.deepEqual(errors, []); assert.deepEqual(mutations, []);
});

test('admin lazy statistics fail visibly and retry without hiding a successful sibling', async () => {
  const { page, routes } = await open('admin', {
    '/api/admin/maintenance/embedding-cache-stats': { $status: 503, data: {} },
  }, '#stats');
  assert.match(await text(page, '#embed-stats'), /Request failed/);
  assert.match(await text(page, '#annotation-stats'), /Total images: 0/);
  routes['/api/admin/maintenance/embedding-cache-stats'] = { exists: false };
  await page.click('#embed-stats button');
  await page.waitForFunction(() => document.getElementById('embed-stats').textContent.includes('no cache found'));
  routes['/api/admin/maintenance/annotation-stats'] = {};
  await page.evaluate(() => loadAnnotationStats());
  assert.match(await text(page, '#annotation-stats'), /Malformed successful response.*Historical/);
  assert.match(await text(page, '#annotation-stats'), /Source age unknown/);
});

test('admin metadata is text; maintenance mutations keep their existing methods', async () => {
  const { page, routes, mutations } = await open('admin', {
    '/api/admin/health': { status: hostile, broker: { status: hostile }, disk: { used_pct: null, free: hostile } },
    '/api/admin/disk-usage': { breakdown: { [hostile]: { exists: true, size_bytes: 1, size_human: hostile } } },
    '/api/admin/maintenance/vacuum-broker': { $status: 403, data: {} },
    '/api/admin/maintenance/clean-logs': { status: 'ok' },
  });
  await inert(page);
  assert.match(await text(page, '#health-grid'), /Unknown/);
  await page.evaluate(() => { showResult('logs-result', { message: '<tag>' }); });
  await page.evaluate(() => vacuumBroker());
  assert.match(await text(page, '#vacuum-result'), /error/);
  await page.evaluate(() => cleanLogs());
  assert.deepEqual(mutations.map(m => m.method), ['POST', 'POST']);
  assert.equal(mutations[1].query, '?max_age_days=30');
  routes['/api/admin/health'] = { $status: 500, data: {} };
  await page.evaluate(() => loadHealth());
  assert.match(await text(page, '#health-grid'), /Historical observation retained/);
  routes['/api/admin/disk-usage'] = { error: 'not found' };
  await page.evaluate(() => loadDisk());
  assert.match(await text(page, '#disk-bars'), /Source unavailable/);
});

test('artifact metadata cannot escape attributes and unsafe URLs are withheld', async () => {
  const { page, errors } = await open('artifacts', {
    '/api/artifacts/html': { artifacts: [artifact({ url: `javascript:globalThis.injection=1` }), artifact({ url: `https://outside.test/artifacts/file.html` }), artifact({ url: `/artifacts/reports/${hostile}.html` })] },
  });
  await inert(page);
  assert.equal(await page.$$eval('[data-unavailable]', els => els.length), 2);
  assert.equal(await page.$$eval('#class-filter option', els => els.length), 2);
  assert.equal(await page.$eval('#class-filter option:last-child', o => o.value), hostile);
  const href = await page.$eval('.artifact-card:last-child', a => a.href);
  assert.equal(new URL(href).origin, 'http://maintenance.test');
  assert.deepEqual(errors, []);
});

test('artifact failed refresh retains filters and original assembly and fetch clocks', async () => {
  const { page, routes } = await open('artifacts');
  await page.select('#class-filter', hostile);
  const originalFetch = await page.evaluate(() => state.fetchedAt);
  routes['/api/artifacts/html'] = { artifacts: {} };
  await page.click('#refresh-btn');
  await page.waitForFunction(() => !state.loading);
  assert.match(await text(page, '#refresh-info'), /Malformed successful response.*Historical observation retained/);
  assert.equal(await page.evaluate(() => state.fetchedAt), originalFetch);
  assert.equal(await page.$eval('#class-filter', el => el.value), hostile);
  assert.match(await text(page, '#refresh-info'), /Index assembled \d+s ago/);
  routes['/api/artifacts/html'] = { artifacts: [], generated_at: '2999-01-01' };
  await page.evaluate(() => loadArtifacts());
  assert.equal(await page.$eval('#class-filter', el => el.value), hostile);
  await page.click('#clear-filters');
  assert.match(await text(page, '#groups'), /No artifacts returned/);
  assert.match(await text(page, '#refresh-info'), /assembly time unknown/);
});

test('artifact initial parse failure is unknown and retry recovers; filters work', async () => {
  const { page, routes } = await open('artifacts', { '/api/artifacts/html': { $status: 200, raw: '{' } });
  assert.equal(await text(page, '#total-count'), 'Unknown');
  routes['/api/artifacts/html'] = { artifacts: [artifact({ status: 'ok', author: 'author', class: 'reports', title: 'Alpha', path: 'reports/alpha.md', url: '/artifacts/reports/alpha.md', kpi_summary: 'score' }), artifact({ status: 'warn', author: 'other', class: 'notes', title: 'Beta', path: 'notes/beta.html', url: '/artifacts/notes/beta.html' })] };
  await page.evaluate(() => loadArtifacts());
  await page.type('#search', 'Alpha');
  await page.waitForFunction(() => document.getElementById('total-count').textContent === '1');
  await page.select('#status-filter', 'ok');
  await page.select('#author-filter', 'author');
  await page.select('#type-filter', 'md');
  await page.$eval('#date-filter', el => { el.value = '2021-01-01'; el.dispatchEvent(new Event('change')); });
  assert.match(await text(page, '#groups'), /No artifacts match/);
  await page.click('#empty-clear');
  assert.equal(await text(page, '#total-count'), '2');
});

test('consultation metadata is inert in queue, details, history and metrics; filenames are encoded', async () => {
  const { page, routes, requests, errors } = await open('consultation');
  routes['/api/consultation/queue/' + encodeURIComponent(hostile)] = detail();
  await page.click('[data-detail]');
  await page.waitForSelector('#modal-content [data-action]');
  assert.ok(requests.some(url => url.includes(encodeURIComponent(hostile))));
  assert.match(await text(page, '#modal-content'), /Proposal:/);
  await inert(page);
  await page.keyboard.press('Escape');
  assert.equal(await page.$eval('[data-detail]', el => document.activeElement === el), true);
  assert.deepEqual(errors, []);
});

test('consultation queue failure and malformed success recover without losing siblings', async () => {
  const { page, routes } = await open('consultation', { '/api/consultation/queue': { pending: {} } });
  assert.match(await text(page, '#queue-list-status'), /Malformed successful response/);
  assert.match(await text(page, '#metrics-stats'), /Total: 1/);
  routes['/api/consultation/queue'] = { pending: [], count: 0 };
  await page.evaluate(() => loadQueue());
  assert.match(await text(page, '#queue-list'), /No proposals returned; source age and coverage unknown/);
  routes['/api/consultation/queue'] = { $status: 503, data: {} };
  await page.evaluate(() => loadQueue());
  assert.match(await text(page, '#queue-list-status'), /Historical observation retained/);
});

test('consultation detail failures have inline retry and closed or newer selection defeats late detail', async () => {
  const { page, routes } = await open('consultation');
  await page.evaluate(() => loadDetail('missing.yml'));
  assert.match(await text(page, '#modal-content'), /Failed to load proposal/);
  routes['/api/consultation/queue/missing.yml'] = detail('Recovered');
  await page.click('#modal-content button');
  await page.waitForFunction(() => document.getElementById('modal-content').textContent.includes('Recovered'));
  const held = deferred();
  routes['/api/consultation/queue/old.yml'] = () => held.promise;
  routes['/api/consultation/queue/new.yml'] = detail('New selection');
  await page.evaluate(() => { void loadDetail('old.yml'); });
  await page.evaluate(() => loadDetail('new.yml'));
  held.resolve(detail('Old selection'));
  await page.waitForNetworkIdle();
  assert.match(await text(page, '#modal-content'), /New selection/);
  const late = deferred(); routes['/api/consultation/queue/late.yml'] = () => late.promise;
  await page.evaluate(() => { void loadDetail('late.yml'); closeModal(); });
  late.resolve(detail('Late selection'));
  await page.waitForNetworkIdle();
  assert.equal(await page.$eval('#detail-modal', el => el.classList.contains('visible')), false);
});

test('proposal mutations retain authorization URL and confirmation; failure retains selection and retries', async () => {
  const { page, routes, mutations } = await open('consultation');
  routes['/api/consultation/queue/safe.yml'] = detail('Safe proposal');
  routes['/api/consultation/queue/safe.yml/approve'] = { $status: 403, data: {} };
  await page.evaluate(() => loadDetail('safe.yml'));
  await page.click('[data-action="approve"]');
  assert.equal(mutations.length, 0);
  await page.click('#confirm-action-btn');
  await page.waitForFunction(() => document.getElementById('action-error').textContent.includes('403'));
  assert.equal(await page.evaluate(() => currentDetail.filename), 'safe.yml');
  assert.equal(mutations[0].query, '?confirm=true');
  assert.equal(mutations[0].method, 'POST');
  await page.evaluate(() => closeConfirm());
  await page.click('[data-action="reject"]');
  await page.keyboard.press('Escape');
  assert.equal(await page.$eval('#detail-modal', el => el.classList.contains('visible')), true);
  await page.click('[data-action="approve"]');
  routes['/api/consultation/queue/safe.yml/approve'] = { status: 'approved' };
  await page.click('#confirm-action-btn');
  await page.waitForFunction(() => !document.getElementById('detail-modal').classList.contains('visible'));
});

test('consultation history ignores old filter responses and malformed metrics cannot erase history', async () => {
  const { page, routes } = await open('consultation');
  const held = deferred();
  routes['/api/consultation/history'] = ({ url }) => url.searchParams.get('outcome') === 'applied' ? held.promise : { consultations: [], total: 0 };
  await page.select('#filter-outcome', 'applied');
  await page.select('#filter-outcome', 'queued');
  await page.waitForFunction(() => document.getElementById('history-table').textContent.includes('No history rows'));
  held.resolve({ consultations: [{ slug: 'Old result' }], total: 1 });
  await page.waitForNetworkIdle();
  assert.doesNotMatch(await text(page, '#history-table'), /Old result/);
  routes['/api/consultation/metrics'] = {};
  await page.evaluate(() => loadMetrics());
  assert.match(await text(page, '#metrics-charts-status'), /Malformed successful response/);
  assert.match(await text(page, '#history-table'), /No history rows/);
  routes['/api/config'] = {};
  await page.evaluate(() => loadTrackFilter());
  assert.match(await text(page, '#config-status'), /Track options unavailable/);
  assert.equal(await page.evaluate(() => timeAgo('2999-01-01')), 'Unknown');
});

test('annotations render hostile IDs safely and explicit clears are sent; failed save preserves draft and selection', async () => {
  const { page, routes, mutations } = await open('image-explorer', {}, '#annotations');
  await inert(page);
  await page.click('.ann-row input[type="checkbox"]');
  await page.$$eval('.ann-row [data-field]', fields => fields.forEach(field => field.value = ''));
  const target = '/api/images/annotations/' + encodeURIComponent(hostile);
  routes[target] = { $status: 403, data: {} };
  await page.click('.save-btn');
  await page.waitForFunction(() => document.querySelector('.save-status').textContent.includes('Save failed'));
  assert.deepEqual(JSON.parse(mutations[0].body), { description_uk: '', teaching_value: '', element_type: '' });
  assert.equal(await page.$eval('.ann-row input[type="checkbox"]', el => el.checked), true);
  assert.equal(await page.$eval('[data-field="description_uk"]', el => el.value), '');
  routes[target] = { status: 'ok', image_id: hostile, updated_fields: ['description_uk', 'teaching_value', 'element_type'] };
  await page.click('.save-btn');
  await page.waitForFunction(() => document.querySelector('.save-status').textContent === 'Saved');
});

test('annotation populated-to-empty/error transition immediately clears hidden selection and guards late rows', async () => {
  const { page, routes, mutations } = await open('image-explorer', {}, '#annotations');
  await page.click('#select-all');
  assert.equal(await text(page, '#sel-count'), '1 selected');
  const held = deferred(); routes['/api/images/annotations'] = () => held.promise;
  await page.evaluate(() => { annFilters.tv = 'none'; void loadAnnotations(); });
  assert.equal(await text(page, '#sel-count'), '0 selected');
  assert.equal(await page.$eval('#select-all', el => el.checked), false);
  await page.evaluate(() => bulkSetTV());
  assert.equal(mutations.length, 0);
  routes['/api/images/annotations'] = annotations([]);
  await page.evaluate(() => { annFilters.tv = 'low'; return loadAnnotations(); });
  held.resolve(annotations([annotation]));
  await page.waitForNetworkIdle();
  assert.equal(await page.$$eval('.ann-row', els => els.length), 0);
  assert.match(await text(page, '#ann-list'), /No images returned/);
  routes['/api/images/annotations'] = { items: [] };
  await page.evaluate(() => loadAnnotations());
  assert.match(await text(page, '#ann-list-status'), /Malformed successful response/);
  assert.equal(await text(page, '#sel-count'), '0 selected');
});

test('annotation filters and description search use existing contract; bulk failure retains selection', async () => {
  const { page, routes, requests, mutations } = await open('image-explorer', {}, '#annotations');
  await page.click('[data-filter="grade"][data-value="3"]');
  await page.waitForNetworkIdle();
  assert.ok(requests.some(url => url.includes('grade=3')));
  await page.type('#annotation-query', 'sample');
  await page.keyboard.press('Enter');
  await page.waitForNetworkIdle();
  assert.ok(requests.some(url => url.includes('q=sample')));
  await page.click('#select-all');
  routes['/api/images/annotations/bulk'] = { $status: 403, data: {} };
  await page.evaluate(() => bulkSetTV());
  assert.equal(await text(page, '#sel-count'), '1 selected');
  routes['/api/images/annotations/bulk'] = { status: 'ok', updated_count: 0, missing: [hostile] };
  await page.evaluate(() => bulkSetTV());
  assert.equal(await text(page, '#sel-count'), '1 selected');
  routes['/api/images/annotations/bulk'] = { status: 'ok', updated_count: 1, missing: [] };
  await page.evaluate(() => bulkSetTV());
  assert.equal(await text(page, '#sel-count'), '0 selected');
  assert.equal(mutations[0].method, 'POST');
});

test('cleanup requires confirmation and uses existing cleanup contract without live requests', async () => {
  const { page, routes, mutations } = await open('image-explorer', {}, '#annotations');
  await page.click('#select-all');
  await page.evaluate(() => { window.confirm = () => false; });
  await page.evaluate(() => bulkDelete()); assert.equal(mutations.length, 0);
  await page.evaluate(() => { window.confirm = () => true; });
  routes['/api/images/cleanup'] = { $status: 403, data: {} };
  await page.evaluate(() => bulkDelete()); assert.equal(await text(page, '#sel-count'), '1 selected');
  routes['/api/images/cleanup'] = { status: 'ok', deleted_count: 1, not_found: [] };
  await page.evaluate(() => bulkDelete());
  assert.equal(mutations[1].path, '/api/images/cleanup');
  assert.equal(await text(page, '#sel-count'), '0 selected');
});

function pageData(stem, page, label = hostile) {
  return { pdf_stem: stem, page_num: page, scale: 1, images: [{ ...annotation, description_uk: label, teaching_value: hostile, element_type: hostile, bbox: [0, 0, 10, 10], width: 10, height: 10 }], text_blocks: [{ text: hostile, bbox: [1, 1, 5, 5] }] };
}
test('image page metadata, URLs and overlays are safe and selected page wins reversed responses', async () => {
  const { page, routes, errors } = await open('image-explorer');
  const stem = 'sample';
  routes['/api/images/textbooks'] = [{ stem, page_count: 2, image_count: 1 }];
  routes['/api/images/page/sample/1'] = pageData(stem, 1);
  routes['/api/images/page/sample/2'] = pageData(stem, 2, 'Second page');
  await page.evaluate(() => loadTextbooks());
  await page.select('#textbook-select', stem);
  await page.waitForSelector('#row-0');
  await inert(page);
  await page.hover('#bbox-0');
  assert.equal(await page.$eval('#row-0', el => el.classList.contains('highlighted')), true);
  await page.hover('#row-0');
  await page.click('#toggle-images');
  assert.equal(await page.$eval('#img-overlays', el => el.style.display), 'none');
  await page.click('#toggle-text');
  assert.equal(await page.$eval('#text-overlays', el => el.style.display), 'none');
  const held = deferred(); routes['/api/images/page/sample/1'] = () => held.promise;
  await page.evaluate(() => { void loadPage(); });
  await page.click('#next-btn');
  await page.waitForFunction(() => document.getElementById('page-sidebar').textContent.includes('Second page'));
  held.resolve(pageData(stem, 1, 'Old page'));
  await page.waitForNetworkIdle();
  assert.doesNotMatch(await text(page, '#page-sidebar'), /Old page/);
  await page.click('#row-0 button');
  await page.keyboard.press('Escape');
  assert.equal(await page.$eval('#lightbox', el => el.classList.contains('visible')), false);
  assert.equal(await page.evaluate(() => imageUrl('../sample.png')), '');
  assert.equal(await page.evaluate(() => imageUrl('https://outside.test/sample.png')), '');
  await page.select('#textbook-select', '');
  assert.match(await text(page, '#page-container'), /Select a textbook/);
  assert.deepEqual(errors, []);
});

test('page failure is recoverable; textbook failure is isolated from annotations and invalid geometry is rejected', async () => {
  const { page, routes } = await open('image-explorer', { '/api/images/textbooks': { $status: 503, data: {} } });
  assert.match(await text(page, '#textbook-select-status'), /Textbook request failed/);
  routes['/api/images/textbooks'] = [{ stem: 'sample', page_count: 2, image_count: 1 }];
  await page.evaluate(() => loadTextbooks());
  await page.select('#textbook-select', 'sample');
  await page.waitForFunction(() => document.getElementById('page-container-status').textContent.includes('Request failed'));
  routes['/api/images/page/sample/1'] = pageData('sample', 1);
  await page.evaluate(() => loadPage());
  assert.equal(await page.$$eval('#row-0', els => els.length), 1);
  routes['/api/images/page/sample/2'] = { ...pageData('sample', 2), scale: 'bad' };
  await page.$eval('#page-input', el => el.value = '2');
  await page.evaluate(() => goToPage()); await page.waitForNetworkIdle();
  assert.match(await text(page, '#page-container-status'), /Malformed successful response/);
  await page.evaluate(() => prevPage()); await page.waitForNetworkIdle();
  assert.equal(await page.$$eval('#row-0', els => els.length), 1);
});

test('default image search names D10 and text/literary results remain usable and inert', async () => {
  const { page, routes, errors } = await open('image-explorer', {}, '#search');
  await page.type('#search-input', 'sample');
  await page.click('#search-btn');
  await page.waitForFunction(() => !document.getElementById('search-btn').disabled);
  assert.match(await text(page, '#search-gallery'), /B0 D10 owner: Monitor API/);
  routes['/api/sources/search_text'] = [{ text: hostile, section_title: hostile, author: hostile, grade: hostile, score: 0.5 }];
  await page.click('[data-type="text"]');
  await page.click('#search-btn');
  await page.waitForFunction(() => document.querySelector('.text-result'));
  await inert(page);
  routes['/api/sources/search_literary'] = [{ text: hostile, work: hostile, genre: hostile, language_period: hostile, score: null }];
  await page.click('[data-type="literary"]');
  await page.click('#search-btn');
  await page.waitForFunction(() => document.querySelector('.text-result'));
  assert.match(await text(page, '#search-gallery'), /Score: Unknown/);
  await inert(page); assert.deepEqual(errors, []);
});

test('search selection invalidates old results; malformed-success and empty are distinct', async () => {
  const { page, routes } = await open('image-explorer', {}, '#search');
  const held = deferred(); routes['/api/sources/search_images'] = () => held.promise;
  await page.type('#search-input', 'sample');
  await page.click('#search-btn');
  await page.click('[data-type="text"]');
  routes['/api/sources/search_text'] = [];
  await page.click('#search-btn');
  await page.waitForFunction(() => document.getElementById('search-gallery').textContent.includes('No results returned'));
  held.resolve([{ image_path: 'grade-03/sample.png', image_id: 'old', score: 1 }]);
  await page.waitForNetworkIdle();
  assert.doesNotMatch(await text(page, '#search-gallery'), /old/);
  routes['/api/sources/search_text'] = {};
  await page.evaluate(() => doSearch());
  assert.match(await text(page, '#search-gallery-status'), /Malformed successful response/);
  routes['/api/sources/search_text'] = { $status: 503, data: {} };
  await page.evaluate(() => doSearch());
  assert.match(await text(page, '#search-gallery-status'), /503/);
  await page.click('[data-sgrade="3"]');
  assert.match(await text(page, '#search-gallery-status'), /selection changed/);
});

test('future image-search contract rendering stays safe; stats retain data and filters use text keys', async () => {
  const { page, routes } = await open('image-explorer', {}, '#search');
  routes['/api/sources/search_images'] = [{ ...annotation, grade: hostile, score: 0.4, width: 10, height: 10 }];
  await page.type('#search-input', 'sample'); await page.keyboard.press('Enter');
  await page.waitForSelector('.search-card'); await inert(page);
  const imageSrc = await page.$eval('.search-card img', el => el.src);
  await page.click('.search-card button');
  assert.equal(await page.$eval('#lightbox-img', el => el.src), imageSrc);
  assert.equal(await page.$eval('#lightbox', el => el.classList.contains('visible')), true);
  await page.keyboard.press('Tab'); await page.keyboard.press('Escape');
  routes['/api/images/stats'] = { ...goodStats, teaching_value: { [hostile]: 1 }, element_type: { [hostile]: 1 }, per_grade: { [hostile]: { total: 1, annotated: 0 } } };
  await page.click('[data-tab="stats"]');
  await page.waitForSelector('#stats-content .dist-legend button');
  await inert(page);
  routes['/api/images/stats'] = {};
  await page.evaluate(() => loadStats());
  assert.match(await text(page, '#stats-content-status'), /Malformed successful response.*historical/);
  await page.click('#stats-content .dist-legend button');
  await page.waitForFunction(() => document.getElementById('panel-annotations').classList.contains('active'));
  assert.equal(await page.evaluate(() => annFilters.tv), hostile);
});

test('all pages preserve keyboard access and narrow layouts without uncaught errors', async () => {
  for (const name of ['admin', 'artifacts', 'consultation', 'image-explorer']) {
    const { page, errors, mutations } = await open(name);
    await page.setViewport({ width: 390, height: 844 });
    await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(() => document.activeElement.className), 'skip-link');
    await page.keyboard.press('Enter');
    assert.equal(await page.evaluate(() => document.activeElement.id), 'page-main');
    assert.deepEqual(errors, [], name);
    assert.deepEqual(mutations, [], name);
  }
});

test('annotation pagination clears selection and keeps unknown annotation values until explicitly changed', async () => {
  const first = { ...annotation, image_id: 'first', teaching_value: 'source-value', element_type: 'source-type' };
  const { page, routes } = await open('image-explorer', { '/api/images/annotations': { ...annotations([first]), total: 51, total_pages: 2 } }, '#annotations');
  assert.equal(await page.$eval('[data-field="teaching_value"]', el => el.value), 'source-value');
  assert.equal(await page.$eval('[data-field="element_type"]', el => el.value), 'source-type');
  routes['/api/images/annotations'] = ({ url }) => ({ ...annotations([{ ...first, image_id: url.searchParams.get('page') === '1' ? 'second' : 'first' }]), total: 51, total_pages: 2 });
  await page.click('#select-all');
  await page.click('#ann-pagination button:nth-child(3)');
  await page.waitForFunction(() => document.querySelector('.ann-row')?.dataset.id === 'second');
  await page.waitForNetworkIdle();
  assert.equal(await text(page, '#sel-count'), '0 selected');
  await page.click('#ann-pagination button:first-child');
  await page.waitForFunction(() => document.querySelector('.ann-row')?.dataset.id === 'first');
  await page.evaluate(() => toggleSelect('hidden-id', true));
  assert.equal(await text(page, '#sel-count'), '0 selected');
});

test('proposal dialogs retain focus and failed read retries after malformed JSON', async () => {
  const { page, routes } = await open('consultation');
  routes['/api/consultation/queue/sample.yml'] = { $status: 200, raw: '{' };
  await page.evaluate(() => loadDetail('sample.yml'));
  assert.match(await text(page, '#modal-content'), /Malformed successful response/);
  routes['/api/consultation/queue/sample.yml'] = detail('Focus sample');
  await page.click('#modal-content button');
  await page.waitForSelector('#modal-content [data-action]');
  await page.focus('[data-action="reject"]');
  await page.keyboard.press('Tab');
  assert.equal(await page.$eval('.close-btn', el => document.activeElement === el), true);
  await page.keyboard.down('Shift'); await page.keyboard.press('Tab'); await page.keyboard.up('Shift');
  assert.equal(await page.$eval('[data-action="reject"]', el => document.activeElement === el), true);
  await page.click('[data-action="reject"]');
  await page.mouse.click(5, 5);
  assert.equal(await page.$eval('#confirm-modal', el => el.classList.contains('visible')), false);
  await page.mouse.click(5, 5);
  assert.equal(await page.$eval('#detail-modal', el => el.classList.contains('visible')), false);
});

test('in-flight proposal decisions survive dismiss and accept only the matching outcome', async () => {
  const { page, routes, requests } = await open('consultation');
  routes['/api/consultation/queue/safe.yml'] = detail('Safe proposal');
  const queueGets = () => requests.filter(url => url === '/api/consultation/queue').length;
  const held = deferred();
  routes['/api/consultation/queue/safe.yml/approve'] = () => held.promise;
  await page.evaluate(() => loadDetail('safe.yml'));
  await page.click('[data-action="approve"]');
  await page.click('#confirm-action-btn');
  await page.waitForFunction(() => document.getElementById('confirm-action-btn').disabled);
  await page.evaluate(() => closeConfirm());
  assert.equal(await page.$eval('#confirm-modal', el => el.classList.contains('visible')), false);
  assert.equal(await page.$eval('#detail-modal', el => el.classList.contains('visible')), true);
  const queued = queueGets();
  held.resolve({ $status: 403, data: {} });
  await page.waitForFunction(() => document.getElementById('detail-outcome').textContent.includes('403'));
  assert.equal(await page.$eval('#detail-modal', el => el.classList.contains('visible')), true);
  assert.equal(queueGets(), queued);

  const heldErrors = deferred();
  routes['/api/consultation/queue/safe.yml/approve'] = () => heldErrors.promise;
  await page.click('[data-action="approve"]');
  await page.click('#confirm-action-btn');
  await page.waitForFunction(() => document.getElementById('confirm-action-btn').disabled);
  await page.evaluate(() => closeConfirm());
  heldErrors.resolve({ status: 'approved', errors: ['patch failed'] });
  await page.waitForFunction(() => document.getElementById('detail-outcome').textContent.includes('patch failed'));
  assert.match(await text(page, '#detail-outcome'), /Outcome kept on screen: approved/);
  assert.equal(await page.$eval('#detail-modal', el => el.classList.contains('visible')), true);
  assert.equal(queueGets(), queued);

  const heldText = deferred();
  routes['/api/consultation/queue/safe.yml/approve'] = () => heldText.promise;
  await page.click('[data-action="approve"]');
  await page.click('#confirm-action-btn');
  await page.waitForFunction(() => document.getElementById('confirm-action-btn').disabled);
  heldText.resolve({ status: 'approved', errors: 'patch failed again' });
  await page.waitForFunction(() => document.getElementById('detail-outcome').textContent.includes('patch failed again'));
  assert.equal(await page.$eval('#detail-modal', el => el.classList.contains('visible')), true);
  assert.equal(queueGets(), queued);

  routes['/api/consultation/queue/safe.yml/approve'] = { status: 'rejected' };
  await page.click('#confirm-action-btn');
  await page.waitForFunction(() => document.getElementById('detail-outcome').textContent.includes('Mutation result unknown'));
  assert.equal(await page.$eval('#detail-modal', el => el.classList.contains('visible')), true);
  assert.match(await text(page, '#action-error'), /Mutation result unknown/);

  routes['/api/consultation/queue/safe.yml/approve'] = { status: 'already_applied', errors: '' };
  await page.click('#confirm-action-btn');
  await page.waitForFunction(() => !document.getElementById('detail-modal').classList.contains('visible'));
  await page.waitForNetworkIdle();
  assert.ok(queueGets() > queued);

  const heldReject = deferred();
  routes['/api/consultation/queue/safe.yml/reject'] = () => heldReject.promise;
  await page.evaluate(() => loadDetail('safe.yml'));
  await page.click('[data-action="reject"]');
  await page.click('#confirm-action-btn');
  await page.waitForFunction(() => document.getElementById('confirm-action-btn').disabled);
  await page.evaluate(() => closeConfirm());
  heldReject.resolve({ status: 'already_rejected' });
  await page.waitForFunction(() => !document.getElementById('detail-modal').classList.contains('visible'));

  await page.evaluate(() => loadDetail('safe.yml'));
  routes['/api/consultation/queue/safe.yml/reject'] = { status: 'approved' };
  await page.click('[data-action="reject"]');
  await page.click('#confirm-action-btn');
  await page.waitForFunction(() => document.getElementById('detail-outcome').textContent.includes('Mutation result unknown'));
  assert.equal(await page.$eval('#detail-modal', el => el.classList.contains('visible')), true);

  const heldStale = deferred();
  routes['/api/consultation/queue/safe.yml/reject'] = () => heldStale.promise;
  await page.click('#confirm-action-btn');
  await page.waitForFunction(() => document.getElementById('confirm-action-btn').disabled);
  const during = queueGets();
  await page.evaluate(() => { actionRequest = { token: {} }; });
  heldStale.resolve({ status: 'rejected' });
  await page.waitForNetworkIdle();
  assert.equal(await page.$eval('#detail-modal', el => el.classList.contains('visible')), true);
  assert.equal(queueGets(), during);
});

test('omitted annotation fields are a malformed list and are not sent as empty clears', async () => {
  const { page, routes, mutations } = await open('image-explorer', {}, '#annotations');
  const omitted = { ...annotation };
  delete omitted.teaching_value;
  routes['/api/images/annotations'] = annotations([omitted]);
  await page.evaluate(() => loadAnnotations());
  assert.match(await text(page, '#ann-list-status'), /Malformed successful response/);
  assert.equal(await page.$$eval('.save-btn', els => els.length), 0);
  assert.equal(mutations.length, 0);
  routes['/api/images/annotations'] = annotations([{ ...annotation, element_type: null }]);
  await page.evaluate(() => loadAnnotations());
  assert.match(await text(page, '#ann-list-status'), /Malformed successful response/);
  routes['/api/images/annotations'] = annotations([annotation]);
  await page.evaluate(() => loadAnnotations());
  await page.waitForSelector('.save-btn');
  await page.evaluate(() => document.querySelector('[data-field="description_uk"]').remove());
  await page.click('.save-btn');
  assert.equal(mutations.length, 0);
  assert.match(await text(page, '.save-status'), /omitted annotation field is malformed and was not sent/);
});

test('cleanup reload requires every selected id deleted and an empty not_found list', async () => {
  const { page, routes } = await open('image-explorer', {}, '#annotations');
  await page.click('#select-all');
  await page.evaluate(() => { window.confirm = () => true; });
  for (const body of [
    { status: 'ok', deleted_count: 0, not_found: [] },
    { status: 'ok', deleted_count: 2, not_found: [] },
    { status: 'ok', deleted_count: 1, not_found: [hostile] },
    { status: 'ok', deleted_count: 1 },
  ]) {
    routes['/api/images/cleanup'] = body;
    await page.evaluate(() => bulkDelete());
    assert.equal(await text(page, '#sel-count'), '1 selected', JSON.stringify(body));
    assert.match(await text(page, '#toast'), /Cleanup unconfirmed/);
  }
});

test('lightbox keys apply only while the preview is open', async () => {
  const { page, routes, requests } = await open('image-explorer');
  const stem = 'sample';
  routes['/api/images/textbooks'] = [{ stem, page_count: 2, image_count: 1 }];
  routes['/api/images/page/sample/1'] = pageData(stem, 1);
  routes['/api/images/page/sample/2'] = pageData(stem, 2, 'Second page');
  await page.evaluate(() => loadTextbooks());
  await page.select('#textbook-select', stem);
  await page.waitForSelector('#row-0');
  await page.click('#row-0 button');
  assert.equal(await page.$eval('#lightbox', el => el.classList.contains('visible')), true);
  const pageTwo = () => requests.filter(url => url.includes('/page/sample/2')).length;
  const before = pageTwo();
  await page.keyboard.press('ArrowRight');
  await page.keyboard.press('Tab');
  assert.equal(pageTwo(), before);
  assert.equal(await page.$eval('#page-input', el => el.value), '1');
  assert.equal(await page.evaluate(() => document.activeElement.id), 'lightbox');
  await page.keyboard.press('Escape');
  assert.equal(await page.$eval('#lightbox', el => el.classList.contains('visible')), false);
  await page.keyboard.press('ArrowRight');
  assert.equal(await page.$eval('#page-input', el => el.value), '2');
  await page.focus('#page-input');
  await page.keyboard.press('Escape');
  assert.equal(await page.evaluate(() => document.activeElement.id), 'page-input');
  await page.evaluate(() => closeLightbox());
  assert.equal(await page.evaluate(() => document.activeElement.id), 'page-input');
});

test('image distribution and per-grade controls preserve discovery filters', async () => {
  const { page } = await open('image-explorer', {}, '#stats');
  await page.click('#stats-content .dist-bar .seg');
  await page.waitForFunction(() => document.getElementById('panel-annotations').classList.contains('active'));
  assert.equal(await page.evaluate(() => annFilters.tv), 'high');
  await page.click('[data-tab="stats"]');
  await page.waitForFunction(() => document.getElementById('stats-content').getAttribute('aria-busy') === 'false');
  await page.click('#stats-content .grade-table button');
  await page.waitForFunction(() => document.getElementById('panel-annotations').classList.contains('active'));
  assert.equal(await page.evaluate(() => annFilters.grade), '3');
});
