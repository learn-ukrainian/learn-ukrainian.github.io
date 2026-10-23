import { expect, test as base, type Locator } from '@playwright/test';
import { AxeBuilder } from '@axe-core/playwright';
import { readFileSync, writeFileSync, mkdtempSync, existsSync, readdirSync, mkdirSync, copyFileSync, rmSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { createServer, type Server } from 'node:http';
import { connect } from 'node:net';
import { once } from 'node:events';
import { basename, join, resolve, sep } from 'node:path';
import { tmpdir } from 'node:os';
import snapshot from '../tests/fixtures/word-card-preview/current';
import { revisionCases, relationCases, record } from '../tests/fixtures/word-card-preview/inputs';
import { buildPreview, releaseControls, candidateId, certifiedId, pins, fidelityControls, fidelityRefusals, semanticCases, semanticControls, noticeCases, noticeControls } from '../tests/fixtures/word-card-preview/release-controls';
import { expectCurrentAtlasArticle, foldUkrainian, inspectCurrentAtlasArticle, inspectHeteronymTab } from '../tests/helpers/c37-search-proof';

// Historical controls require an explicit test build; public builds omit this flag.
process.env.PUBLIC_ATLAS_WORD_CARD_PREVIEW_CONTROLS = '1';

async function withScratch(prefix: string, logs: string, use: (scratch: string) => Promise<void>): Promise<void> {
  const scratch = mkdtempSync(join(process.env.TMPDIR || tmpdir(), prefix));
  try {
    await use(scratch);
  } finally {
    // Copy only diagnostic files, never the builds or their symlinked dependencies.
    // If preservation fails, retain scratch and fail teardown rather than lose logs.
    for (const entry of readdirSync(scratch, { withFileTypes: true })) if (entry.isDirectory()) {
      for (const name of ['build.log', 'astro.config.mjs']) {
        const source = join(scratch, entry.name, name);
        if (!existsSync(source)) continue;
        const destination = join(logs, basename(scratch), entry.name);
        mkdirSync(destination, { recursive: true });
        copyFileSync(source, join(destination, name));
      }
    }
    rmSync(scratch, { recursive: true });
  }
}

const test = base.extend<{ fidelityScratch: string }, { releaseScratch: string }>({
  fidelityScratch: async ({ page }, use, info) => {
    void page;
    await withScratch('fidelity-browser-', info.outputPath('build-logs'), use);
  },
  releaseScratch: [async ({ browser }, use, info) => {
    void browser;
    await withScratch('release-browser-', join(info.project.outputDir, `release-build-logs-${info.workerIndex}`), use);
  }, { scope: 'worker' }],
});

// Actual-release proof is an explicit local configuration; CI controls remain offline.
if (process.env.ATLAS_WORD_CARD_PUBLIC_PROOF_PATH) test('public pinned release: all routes, frozen literals and fixture isolation', async ({ page }, info) => {
  test.setTimeout(1_500_000);
  await page.route('**/*', route => new URL(route.request().url()).hostname === '127.0.0.1' ? route.continue() : route.abort('blockedbyclient'));
  const artifactPath = process.env.ATLAS_WORD_CARD_PUBLIC_PROOF_PATH;
  const expectationsPath = process.env.ATLAS_WORD_CARD_EXPECTATIONS_PATH;
  if (!artifactPath || !expectationsPath) throw Error('Public proof requires frozen expectations');
  const sha = (bytes: string | Buffer) => createHash('sha256').update(bytes).digest('hex');
  const canonical = (value: unknown): string => {
    if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
    if (value !== null && typeof value === 'object') return `{${Object.entries(value).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0).map(([k, v]) => `${JSON.stringify(k)}:${canonical(v)}`).join(',')}}`;
    return JSON.stringify(value);
  };
  const bytes = readFileSync(join(artifactPath, 'word-cards.jsonl'));
  expect(sha(bytes)).toBe('45bd9c9325a3b4221c86d1663d784e96a7edc096674415445d37113f793189e6');
  expect(sha(readFileSync(join(artifactPath, 'manifest.json')))).toBe('ca182bf5829f3ed4daa80c2394eb87e28879c3f1dc5088eef689f495b97e4f75');
  const frozenBytes = readFileSync(expectationsPath);
  expect(sha(frozenBytes)).toBe('1e86726fb4244c2e31b7a2f67ef7d52fc78ef3fc1de3d1659d1c9b06c8d7a68a');
  const frozen = record(JSON.parse(frozenBytes.toString()));
  if (!Array.isArray(frozen.assertions)) throw Error('Missing frozen assertions');
  const baselinePath = process.env.ATLAS_WORD_CARD_SOURCE_BASELINES_PATH;
  if (!baselinePath) throw Error('Public proof requires independently frozen source baselines');
  const assertionBytes = readFileSync(join(baselinePath, 'assertion-baseline.json'));
  const routeBytes = readFileSync(join(baselinePath, 'route-baseline.json'));
  expect(sha(assertionBytes)).toBe('a4d8b7e59e999ea7de555aef12ec809852eb9a8c4e3906423c60ed31c8d94936');
  expect(sha(routeBytes)).toBe('6bec84b945e9d323a06e8a14e90b418f2fe75f16d8910e2db3336f78a525ece0');
  const baseline = record(JSON.parse(assertionBytes.toString()));
  if (!Array.isArray(baseline.assertions)) throw Error('Missing source baseline assertions');
  const sourceExpected = new Map(baseline.assertions.map(value => { const a = record(value); return [`${a.card_id}/${a.assertion_id}`, a]; }));
  expect(sourceExpected.size).toBe(2978);
  const expected = new Map(frozen.assertions.map(value => { const a = record(value); return [`${a.card_id}/${a.assertion_id}`, a]; }));
  type Row = { card_id: string; card_kind: string; card_version: string;
    fields: { assertion_id: string; field: string; value: unknown; subject: { kind: string; id: string }; citation: Record<string, unknown> }[] };
  const rows: Row[] = bytes.toString().trimEnd().split('\n').map(line => JSON.parse(line));
  // Independent page model: one lowercased card-subject spelling (mwe_form for MWE); common entries first, proper names last.
  const keyOf = (row: Row) => {
    const field = row.card_kind === 'mwe' ? 'mwe_form' : 'spelling';
    const values = new Set(row.fields.filter(f => f.field === field && f.subject.kind === 'card' && f.subject.id === row.card_id).map(f => String(f.value).toLowerCase()));
    if (values.size !== 1) throw Error(`Ambiguous page key ${row.card_id}`);
    return [...values][0] || '';
  };
  const grouped = new Map<string, Row[]>();
  for (const row of rows) grouped.set(keyOf(row), [...grouped.get(keyOf(row)) ?? [], row]);
  const isProper = (row: Row) => row.card_kind === 'proper_name';
  const learner = [...grouped].filter(([, group]) => group.some(row => !isProper(row)))
    .map(([key, group]) => [key, [...group.filter(row => !isProper(row)), ...group.filter(isProper)]] as const);
  const unlisted = rows.filter(row => !learner.some(([, entries]) => entries.includes(row)));
  expect([grouped.size, learner.length, learner.flatMap(([, e]) => e).length, unlisted.map(r => r.card_id)]).toEqual([136, 134, 148, ['wc_bz5ypsm3wyj7', 'wc_sye0ppkx0dwh']]);
  const display = (row: Row) => String(row.fields.find(f => f.field === (row.card_kind === 'mwe' ? 'mwe_form' : 'spelling') && f.subject.kind === 'card')?.value);
  const root = mkdtempSync(join(process.env.TMPDIR || tmpdir(), 'public-release-proof-'));
  const controls = readdirSync('../docs/atlas/word-cards/examples').filter(name => name.endsWith('.json')).flatMap(name => {
    const input = readFileSync(join('../docs/atlas/word-cards/examples', name));
    return [String(record(JSON.parse(input.toString())).card_id), sha(input)];
  });
  const sentinels = [...new Set([...controls, candidateId, certifiedId, ...Object.values(pins).flatMap(pin => [pin.dataset_sha256, pin.manifest_sha256]),
    sha(readFileSync('tests/fixtures/word-card-preview/current.ts')), sha(JSON.stringify(snapshot)), 'CONTROL_RAW', 'CONTROL_NORM', 'EXAMPLE_RAW', 'fixture-head', 'synthetic-candidate-1'])];
  const overlap = sentinels.filter(marker => bytes.includes(marker));
  writeFileSync(join(root, 'sentinels-before-build.json'), JSON.stringify({ sentinels, overlap }, null, 2));
  // Keep the real home page so sitemap exclusion has a positive ordinary-route control.
  mkdirSync(join(root, 'public/src/pages'), { recursive: true });
  copyFileSync('src/pages/index.astro', join(root, 'public/src/pages/index.astro'));
  mkdirSync(join(root, 'public/public'), { recursive: true });
  copyFileSync('public/count.js', join(root, 'public/public/count.js'));
  process.env.PUBLIC_ATLAS_WORD_CARD_PREVIEW_CONTROLS = '';
  let output: string;
  try { output = process.env.ATLAS_WORD_CARD_PUBLIC_BUILT_ROOT || buildPreview(join(root, 'public'), { enabled: true, artifactPath }); }
  finally { process.env.PUBLIC_ATLAS_WORD_CARD_PREVIEW_CONTROLS = '1'; }
  // The isolated preview build omits ordinary Atlas routes. Package their real
  // generated search assets using the existing pure generator, without a database.
  const interpreter = process.env.PYTHON;
  if (!interpreter) throw Error('Public proof requires the task-prescribed PYTHON interpreter');
  execFileSync(interpreter, ['-c', `
import json, sys
from pathlib import Path
from scripts.audit.generate_search_index import build_search_shards, write_search_shards
source, target = map(Path, sys.argv[1:])
rows = json.loads((source / 'lexicon-search-index.json').read_bytes())
manifest, shards = build_search_shards(rows)
expected = json.loads((source / 'lexicon-search-shards.json').read_bytes())
assert manifest == expected, 'Search inputs do not match their generated manifest'
write_search_shards(manifest, shards, target / 'search-shards.json', target / 'search')
`, resolve('src/data'), join(output, 'lexicon')], { cwd: resolve('..') });
  for (const name of ['index', 'aliases']) copyFileSync(`src/data/lexicon-search-${name}.json`, join(output, `lexicon/search-${name}.json`));
  const files = readdirSync(output, { recursive: true }).filter((name): name is string => typeof name === 'string');
  const routes = files.filter(name => name.startsWith('lexicon-v2/') && name.endsWith('/index.html'));
  expect(routes).toHaveLength(570);
  expect(routes.sort()).toEqual(['lexicon-v2/release/index.html', 'lexicon-v2/compare/release/index.html', ...rows.flatMap(row =>
    ['', 'compare/'].map(prefix => `lexicon-v2/${prefix}release/${row.card_id}/index.html`)), ...learner.flatMap(([key]) =>
    ['', 'compare/'].map(prefix => `lexicon-v2/${prefix}word/${key}/index.html`))].sort());
  expect(routes.map(name => `/${name.slice(0, -'index.html'.length)}`).sort()).toEqual(record(JSON.parse(routeBytes.toString())).routes);
  // The committed route inventory names exactly the routes this public build emitted, for these pinned bytes.
  const routeInventory = JSON.parse(readFileSync('src/lib/lexicon/word-card-preview-route-inventory.json', 'utf8')) as { release: unknown; routes: { path: string }[] };
  expect(routeInventory.release).toMatchObject({ dataset_sha256: sha(bytes), dataset_bytes: bytes.length });
  // Sorted equality fails on an omitted, unexpected or duplicated route.
  expect(routes.map(name => `/${name.slice(0, -'index.html'.length)}`).sort()).toEqual(routeInventory.routes.map(r => r.path).sort());
  const scanned = files.filter(name => /\.(html|js|xml)$/.test(name));
  expect(files).toEqual(expect.arrayContaining(['sitemap-index.xml', 'sitemap-0.xml']));
  expect(readFileSync(join(output, 'sitemap-0.xml'), 'utf8')).toContain('<loc>https://learn-ukrainian.github.io/</loc>');
  for (const file of scanned) {
    const text = readFileSync(join(output, file), 'utf8');
    for (const marker of sentinels.filter(marker => !overlap.includes(marker))) expect(text, `${file}: ${marker}`).not.toContain(marker);
    if (file.endsWith('.xml')) expect(text).not.toContain('/lexicon-v2/');
  }
  const server = createServer((req, res) => {
    const path = decodeURIComponent(new URL(req.url || '/', 'http://localhost').pathname);
    const file = resolve(output, '.' + (path.endsWith('/') ? path + 'index.html' : path));
    if (!file.startsWith(output + sep) || !existsSync(file)) { res.writeHead(404).end(); return; }
    res.setHeader('Content-Type', file.endsWith('.css') ? 'text/css' : file.endsWith('.js') ? 'text/javascript' : file.endsWith('.json') ? 'application/json' : 'text/html');
    res.end(readFileSync(file));
  });
  await new Promise<void>(done => server.listen(0, '127.0.0.1', done));
  const address = server.address();
  if (!address || typeof address === 'string') throw Error('No public proof port');
  let checked = 0;
  // Every raw assertion keeps its exact value, citation, attribution, allowlisted links, gap marker and report body.
  const checkAssertions = async (scope: Locator, row: Row, learnerPage = false) => {
    if (learnerPage) {
      const bindings = await scope.locator('[data-release-assertion]').evaluateAll(nodes => nodes.map(node => ({
        id: node.getAttribute('data-release-assertion'), field: node.querySelector('h4')?.textContent,
        subject: node.querySelector('p')?.textContent, value: node.querySelector('[data-raw-value]')?.textContent,
        source: node.querySelector('[data-assertion-source]')?.textContent,
        snapshot: node.querySelector('[data-assertion-snapshot]')?.textContent,
        locator: node.querySelector('[data-assertion-locator]')?.textContent,
        raw: node.querySelector('[data-raw-diagnostic]')?.getAttribute('href'),
        report: node.querySelector('[data-report-action]')?.getAttribute('href'),
      })));
      expect(bindings).toEqual(row.fields.map(source => ({
        id: source.assertion_id, field: source.field, subject: `${source.subject.kind}: ${source.subject.id}`,
        value: typeof source.value === 'string' ? source.value : JSON.stringify(source.value, null, 2),
        source: source.citation.source_id, snapshot: source.citation.snapshot_id, locator: source.citation.locator,
        raw: `/lexicon-v2/release/${row.card_id}/#assertion-${source.assertion_id}`,
        report: `https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/new?body=${encodeURIComponent(JSON.stringify(sourceExpected.get(`${row.card_id}/${source.assertion_id}`)?.report_body, null, 2))}`,
      })));
      await expect(scope.locator('[data-release-citation], [data-source-attribution], [data-attribution-gap]')).toHaveCount(0);
    }
    const rawResponse = learnerPage ? await page.request.get(`http://127.0.0.1:${address.port}/lexicon-v2/release/${row.card_id}/`) : null;
    if (rawResponse) expect(rawResponse.status()).toBe(200);
    const rawHtml = rawResponse ? await rawResponse.text() : null;
    const displayed = await scope.evaluate((element, html) => {
      const root = html === null ? element : new DOMParser().parseFromString(html, 'text/html');
      return Array.from(root.querySelectorAll('[data-release-assertion]')).map(node => ({
      target: node.id, id: node.getAttribute('data-release-assertion'), value: node.querySelector('[data-raw-value]')?.textContent,
      citation: node.querySelector('[data-release-citation]')?.textContent, attribution: node.querySelector('[data-source-attribution]')?.textContent,
      field: node.querySelector('h4')?.textContent, subject: node.querySelector('p')?.textContent,
      links: Array.from(node.querySelectorAll('[data-source-link]')).map(link => link.getAttribute('href')),
      report: node.querySelector('[data-report-action]')?.getAttribute('href'), gap: node.querySelector('[data-attribution-gap]')?.getAttribute('data-attribution-gap'),
    }));
    }, rawHtml);
    // One comparison per card keeps every field check while avoiding ~110k individual expect() calls.
    const frozenMismatches = row.fields.filter(source => { const frozen = expected.get(`${row.card_id}/${source.assertion_id}`);
      const baseline = sourceExpected.get(`${row.card_id}/${source.assertion_id}`);
      return !frozen || !baseline || sha(canonical(source.value)) !== frozen.value_sha256 || sha(canonical(source.citation)) !== frozen.citation_sha256 || frozen.field !== source.field ||
        sha(canonical(source.value)) !== baseline.value_sha256 || sha(canonical(source.citation)) !== baseline.citation_sha256 || baseline.field !== source.field ||
        canonical(baseline.subject) !== canonical(source.subject) || baseline.card_version !== row.card_version ||
        canonical(baseline.report_body) !== canonical({ release_version: 'v0.1.0-pilot', dataset_sha256: sha(bytes), card_id: row.card_id,
          card_version: row.card_version, assertion_id: source.assertion_id, field: source.field }); });
    expect(frozenMismatches.map(source => source.assertion_id), row.card_id).toEqual([]);
    const shape = (item: typeof displayed[number]) => ({ ...item, citation: item.citation ? sha(canonical(JSON.parse(item.citation))) : null,
      report: item.report ? JSON.parse(new URL(item.report).searchParams.get('body') || '') : null, gap: item.gap ?? null });
    expect(displayed.map(shape), row.card_id).toEqual(row.fields.map(source => {
      const sourceId = source.citation.source_id;
      return { target: `assertion-${source.assertion_id}`, id: source.assertion_id, value: typeof source.value === 'string' ? source.value : JSON.stringify(source.value, null, 2),
        citation: expected.get(`${row.card_id}/${source.assertion_id}`)?.citation_sha256, attribution: source.citation.attribution,
        field: source.field, subject: `${source.subject.kind}: ${source.subject.id}`,
        links: sourceId === 'ulif' ? ['https://lcorp.ulif.org.ua/dictua/'] : sourceId === 'vesum' ? ['https://vesum.nlp.net.ua/'] : [],
        report: { release_version: 'v0.1.0-pilot', dataset_sha256: sha(bytes), card_id: row.card_id, card_version: row.card_version,
          assertion_id: source.assertion_id, field: source.field },
        gap: sourceId === 'puls' ? 'puls_reference_placeholder' : sourceId === 'vesum' ? 'vesum_version_placeholder' : null };
    }));
    checked += row.fields.length;
  };
  try {
    for (const prefix of ['', 'compare/']) {
      for (const row of rows) {
        await page.goto(`http://127.0.0.1:${address.port}/lexicon-v2/${prefix}release/${row.card_id}/`);
        await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', 'noindex, nofollow');
        await expect(page.locator('[data-preview-banner]')).toBeVisible();
        await expect(page.locator('[data-release-status]')).toHaveText('CANDIDATE');
        await expect(page.locator('[data-card-version]')).toHaveText(`Card version ${row.card_version}`);
        await expect(page.locator('[data-release-version]')).toHaveText('Release v0.1.0-pilot');
        await expect(page.getByRole('region', { name: 'Known gaps', exact: true })).toContainText('No declared gaps');
        await checkAssertions(page.locator('[data-release-card]'), row);
        await expect(page.locator('[data-comparison], [data-word-atlas], [data-result]')).toHaveCount(0);
        if (prefix) await expect(page.getByRole('region', { name: 'Field comparison', exact: true })).toContainText('Unresolved pairing');
      }
      for (const [key, entries] of learner) {
        await page.goto(`http://127.0.0.1:${address.port}/lexicon-v2/${prefix}word/${encodeURIComponent(key)}/`);
        await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', 'noindex, nofollow');
        await expect(page.locator('[data-preview-banner]')).toContainText('CANDIDATE preview, not certified learner cards');
        await expect(page.locator('h1')).toHaveText([...new Set(entries.filter(row => !isProper(row)).map(display))].join(' / '));
        expect(await page.locator('[data-entry]').evaluateAll(nodes => nodes.map(n => [n.getAttribute('data-entry'), n.getAttribute('data-entry-kind')])))
          .toEqual(entries.map(row => [row.card_id, row.card_kind]));
        await expect(page.locator('details[open]')).toHaveCount(0);
        for (const [i, row] of entries.entries()) {
          const entry = page.locator(`[data-entry="${row.card_id}"]`);
          await expect(entry.locator('h2')).toContainText(`${i + 1}.`);
          if (isProper(row)) await expect(entry.locator('[data-entry-label]')).toContainText('Proper name');
          // The readable layer cites exactly this card's assertions, each once; audit details keep every raw record.
          const readable = await entry.evaluate(node => Array.from(node.querySelectorAll('[data-assertions]')).filter(e => !e.closest('details'))
            .flatMap(e => (e.getAttribute('data-assertions') || '').split(' ')));
          expect(readable.sort(), row.card_id).toEqual(row.fields.map(f => f.assertion_id).sort());
          await checkAssertions(page.locator(`[data-entry-audit="${row.card_id}"]`), row, true);
        }
        await expect(page.locator('[data-comparison], [data-word-atlas], [data-result]')).toHaveCount(0);
        if (prefix) await expect(page.getByRole('region', { name: 'Field comparison', exact: true })).toContainText('0 actual comparisons');
      }
      await page.goto(`http://127.0.0.1:${address.port}/lexicon-v2/${prefix}release/`);
      await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', 'noindex, nofollow');
      expect((await page.locator('[data-page-link]').evaluateAll(n => n.map(a => a.getAttribute('href')))).sort())
        .toEqual(learner.map(([key]) => `/lexicon-v2/word/${encodeURIComponent(key)}/`).sort());
      await expect(page.locator('[data-compare-link]')).toHaveCount(134);
      await expect(page.locator('[data-page-count]')).toHaveText('134 word pages with 148 numbered entries. 2 source cards have no learner page; they stay in the audit details.');
      // Every source row keeps one audit record and one disposition; only the two proper-only cards are unlisted.
      await expect(page.locator('[data-card-link]')).toHaveCount(150);
      expect(await page.locator('[data-disposition]').evaluateAll(n => n.map(r => [r.getAttribute('data-disposition'), r.getAttribute('data-listed')])))
        .toEqual(rows.map(row => [row.card_id, String(!unlisted.includes(row))]));
      const stats = JSON.parse(await page.locator('[data-release-accounting]').textContent() || '');
      expect(stats).toMatchObject({ cards: 150, citations: 2978, statuses: { CANDIDATE: 150 }, declaredGaps: 0,
        sources: frozen.source_counts, attributionGaps: frozen.attribution_gap_counts });
      expect(stats.absentFieldClasses).toEqual(expect.arrayContaining(['definition_uk', 'examples']));
      expect(JSON.parse(await page.locator('[data-filtered-assertions]').textContent() || '')).toMatchObject({ puls: { filtered_assertions: 29 }, ulif: { filtered_assertions: 156 } });
      await expect(page.locator('[data-pairing-count]')).toHaveText('0/150 paired; 150/150 explicitly unpaired. 0 actual comparisons.');
      await info.attach(`public-summary-${prefix ? 'comparison' : 'normal'}`, { body: await page.screenshot(), contentType: 'image/png' });
    }
    expect(checked).toBe(2 * (2978 + 2978 - unlisted.reduce((n, row) => n + row.fields.length, 0)));
    const regressionResults = await readability(page, `http://127.0.0.1:${address.port}`, join(root, 'screens'), info, output);
    await page.goto(`http://127.0.0.1:${address.port}/lexicon-v2/release/${rows[0]?.card_id}/`);
    const requests: string[] = [];
    await page.route('https://github.com/**', route => { requests.push(route.request().url()); return route.abort('blockedbyclient'); });
    const report = page.locator('[data-report-action]').first(), href = await report.getAttribute('href');
    expect(requests).toEqual([]);
    await report.focus(); await expect(report).toBeFocused();
    const failedNavigation = page.waitForEvent('requestfailed', request => request.url() === href);
    await page.keyboard.press('Enter');
    const attempted = await failedNavigation;
    expect(requests).toEqual([href]);
    await info.attach('report-keyboard-navigation', { body: JSON.stringify({ href, method: attempted.method(),
      isNavigationRequest: attempted.isNavigationRequest(), failure: attempted.failure(),
      interaction: ['focus', 'Enter'], disposition: 'External navigation intercepted locally; no issue submitted' }), contentType: 'application/json' });
    expect(attempted.method()).toBe('GET'); expect(attempted.isNavigationRequest()).toBe(true);
    writeFileSync(join(root, 'proof.json'), JSON.stringify({ routes, scanned, overlap, checked, expectedAssertions: expected.size, regressionResults, sourceBaseline: sha(assertionBytes), routeBaseline: sha(routeBytes),
      pages: learner.map(([key, entries]) => [key, entries.map(row => row.card_id)]), unlisted: unlisted.map(row => row.card_id),
      dataset: sha(bytes), expectations: sha(frozenBytes), paired: 0, unpaired: 150, currentBaseline: null,
      residualOwners: { pairing: 'Data/Atlas', attribution: 'Data', publication: 'Delivery', landing: 'Atlas' } }, null, 2));
    await info.attach('public-proof-path', { body: root, contentType: 'text/plain' });
  } finally { await closePreview(server); }
});

test('public configuration refuses synthetic, missing, tampered and malformed inputs; flag-off stays empty', async ({ fidelityScratch: scratch }) => {
  test.setTimeout(180_000);
  const controls = releaseControls(join(scratch, 'public-refusals'));
  const reasons = { base: 'Synthetic provenance forbidden in public preview', missing: 'Missing artifact',
    bytes: 'Dataset integrity mismatch', tamper: 'Manifest pin mismatch', status: 'Unknown card status', citation: 'Missing or malformed field citation' };
  process.env.PUBLIC_ATLAS_WORD_CARD_PREVIEW_CONTROLS = '';
  try {
    for (const [name, reason] of Object.entries(reasons)) {
      const config = controls[name];
      if (!config?.pin) throw Error('Missing public refusal control');
      const pin = name === 'base' ? config.pin : JSON.stringify({ ...JSON.parse(config.pin), provenance: 'producer-declared' });
      const output = buildPreview(join(scratch, `public-${name}`), { ...config, pin });
      const html = readFileSync(join(output, 'lexicon-v2/release/index.html'), 'utf8');
      expect(html.replaceAll('<!-- -->', '')).toContain(`Unavailable: ${reason}`);
      expect(html).not.toContain('data-release-card=');
      expect(readdirSync(join(output, 'lexicon-v2/release'))).toEqual(['index.html']);
      expect(existsSync(join(output, 'lexicon-v2/word'))).toBe(false);
    }
    const output = buildPreview(join(scratch, 'public-off'), { ...controls.base, enabled: false });
    expect(existsSync(join(output, 'lexicon-v2'))).toBe(false);
    for (const name of readdirSync(output, { recursive: true })) if (typeof name === 'string' && /\.(html|js|xml)$/.test(name)) {
      expect(readFileSync(join(output, name), 'utf8')).not.toMatch(/fixture-head|synthetic-candidate-1|wc_0123456789a[bc]/);
    }
  } finally { process.env.PUBLIC_ATLAS_WORD_CARD_PREVIEW_CONTROLS = '1'; }
});


for (const prefix of ['fidelity-browser-', 'release-browser-']) test(`releases ${prefix}scratch after success and failure`, async ({ page }, info) => {
  void page;
  for (const fail of [false, true]) {
    let allocated = '';
    const logs = info.outputPath(fail ? 'failure' : 'success');
    const run = withScratch(prefix, logs, async scratch => {
      allocated = scratch;
      mkdirSync(join(scratch, 'control'));
      writeFileSync(join(scratch, 'control', 'build.log'), 'literal build diagnostic');
      writeFileSync(join(scratch, 'control', 'astro.config.mjs'), 'literal config');
      if (fail) throw Error('controlled consumer failure');
    });
    if (fail) await expect(run).rejects.toThrow('controlled consumer failure');
    else await run;
    expect(existsSync(allocated)).toBe(false);
    const saved = join(logs, basename(allocated), 'control');
    expect(readFileSync(join(saved, 'build.log'), 'utf8')).toBe('literal build diagnostic');
    expect(readFileSync(join(saved, 'astro.config.mjs'), 'utf8')).toBe('literal config');
  }
});

// Public regression page classes: first-screen readability, per-fact credits, collapsed JSON, keyboard disclosure and axe on desktop and phone.
const HELD_OUT: [string, string][] = [['замок', 'homonyms, one without paradigm'], ['баран', 'common and proper name'], ['різати правду-матку', 'MWE'],
  ['вряди-годи', 'conflicting stress'], ['шапка', 'PULS and VESUM attribution gaps'], ['батьківщина', 'capitalized common and proper'],
  ['ключ', 'homonyms with senses and synonyms'], ['читати', 'verb forms'], ['новий', 'adjective and proper name']];
async function readability(page: import('@playwright/test').Page, origin: string, screens: string, info: import('@playwright/test').TestInfo, output: string) {
  mkdirSync(screens, { recursive: true });
  const results: Record<string, unknown>[] = [];
  const captures: (Record<string, unknown> & { initial: { path: string; sha256: string }; creditsOpened: { path: string; sha256: string } })[] = [];
  const sha = (bytes: string | Buffer) => createHash('sha256').update(bytes).digest('hex');
  const errors: string[] = [], failedRequests: string[] = [], consoleErrors: string[] = [];
  const http: { url: string; status: number; method: string }[] = [];
  const navigation: Record<string, unknown>[] = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('requestfailed', request => failedRequests.push(request.url()));
  page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });
  page.on('response', response => http.push({ url: response.url(), status: response.status(), method: response.request().method() }));
  const originals = new Set(['шапка', 'замок', 'баран', 'вряди-годи', 'різати правду-матку']);
  // Literal notices from the frozen public inputs and their manifest-pinned register.
  // These are public author regression expectations, not private acceptance answers.
  const notices: Record<string, string[]> = {
    ulif: ['«Словники України online», Український мовно-інформаційний фонд НАН України, https://lcorp.ulif.org.ua/dictua/'],
    vesum: ['Рисін А., Старко В. Великий електронний словник української мови (ВЕСУМ). 2005-2026. URL: https://vesum.nlp.net.ua/ — licence CC BY-NC-SA 4.0, changes indicated.'],
    puls: ['Просимо посилатися на ПУЛЬС: Профіль української лексики (ПУЛЬС) / О. Синчак, В. Старко, М. Бурак, М. Свистун та ін. Львів: Школа української мови та культури УКУ, 2026. — puls.peremova.org'],
    frazeolohichnyi: ['Словник фразеологізмів української мови / уклад. В. М. Білоноженко та ін.; відп. ред. В. О. Винник. Київ: Наукова думка, 2003. ISBN 966-00-0797-3.'],
    ukrainian_word_stress: ['ULIF «Словники України» stress data, via ukrainian-word-stress / ukrainian-word-stress-dictionary (lang-uk); MIT notice for the code only.'],
  };
  const serious = async () => (await new AxeBuilder({ page }).analyze()).violations.filter(v => ['serious', 'critical'].includes(v.impact ?? ''))
    .map(v => `${v.id}: ${v.nodes.map(node => node.target.join(' ')).join(', ')}`);
  const ready = async () => page.evaluate(async () => {
    await document.fonts.ready;
    await new Promise<void>(done => requestAnimationFrame(() => requestAnimationFrame(() => done())));
    return document.fonts.status;
  });
  const noPlaceholders = async () => {
    const content = await page.locator('[data-release-page]').evaluate(node => node.textContent + Array.from(node.querySelectorAll('*'))
      .flatMap(e => Array.from(e.attributes).map(a => a.value)).join(' '));
    expect(content).not.toMatch(/PULS citation above\.|<used version>|entry reference and retrieval date per field|puls_reference_placeholder|vesum_version_placeholder|attribution incomplete/);
  };
  const noOverflow = async () => expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  for (const [name, viewport] of [['desktop', { width: 1280, height: 800 }], ['phone', { width: 390, height: 844 }]] as const) {
    await page.setViewportSize(viewport);
    for (const [key, kind] of HELD_OUT) {
      const route = `/lexicon-v2/word/${encodeURIComponent(key)}/`;
      const response = await page.goto(origin + route);
      if (!response) throw Error('Missing navigation response');
      expect(response.status()).toBe(200);
      const htmlHash = sha(await response.body());
      expect(htmlHash).toBe(sha(readFileSync(join(output, 'lexicon-v2/word', key, 'index.html'))));
      await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', 'noindex, nofollow');
      await expect(page.locator('[data-preview-banner]')).toContainText('CANDIDATE preview, not certified learner cards');
      await expect(page.locator('[data-release-page]')).toHaveAttribute('data-release-page', key);
      await expect(page.locator('[data-local-artifact-version]')).toHaveText('Local candidate renderer v0.1.1');
      await expect(page.locator('details[open]')).toHaveCount(0);
      const fonts = await ready();
      await page.evaluate(() => window.scrollTo(0, 0));
      const first = page.locator('[data-entry]').first();
      for (const target of [page.locator('h1'), first.locator('h2'), first.locator('[data-entry-label]'), first.locator(':scope > .wc-facts dd').last()]) await expect(target).toBeInViewport();
      await expect(page.locator('pre:visible')).toHaveCount(0);
      await expect(page.locator('[data-credit-attribution]:visible')).toHaveCount(0);
      await noPlaceholders(); await noOverflow();
      const facts = await page.locator('[data-fact] dd:not([data-sources-differ])').count();
      await expect(page.locator('[data-fact] dd:not([data-sources-differ]) [data-credits]')).toHaveCount(facts);
      expect(await page.locator('[data-credit-ref]').evaluateAll(nodes => nodes.every(link => document.getElementById((link.getAttribute('href') || '').slice(1))))).toBe(true);
      const closed = await serious();
      const shot = await page.screenshot();
      const initialPath = join(screens, `${name}-${key}.png`);
      writeFileSync(initialPath, shot);
      await info.attach(`${name}-${key}`, { body: shot, contentType: 'image/png' });
      const disclosure = page.locator('details[data-page-audit]'), summary = disclosure.locator(':scope > summary');
      const marker = first.locator('[data-credit-ref]').first();
      const markerHref = await marker.getAttribute('href');
      await marker.focus(); await expect(marker).toBeFocused(); await page.keyboard.press('Enter');
      await expect(disclosure).toHaveAttribute('open', '');
      expect(new URL(page.url()).hash).toBe(markerHref);
      const target = page.locator(`[id="${markerHref?.slice(1)}"]`);
      await expect(target).toBeVisible(); await expect(target).toBeInViewport();
      navigation.push({ viewport: name, key, kind: 'source-marker', href: markerHref, interaction: ['focus', 'Enter'],
        disclosureOpened: true, targetVisible: true, url: page.url() });
      await summary.focus(); await page.keyboard.press('Enter'); await expect(disclosure).not.toHaveAttribute('open', '');
      const before = await disclosure.getAttribute('open');
      await summary.scrollIntoViewIfNeeded(); await summary.focus(); await expect(summary).toBeFocused();
      const focused = await summary.evaluate(node => ({ tag: document.activeElement?.tagName, label: node.textContent }));
      await page.keyboard.press('Enter'); await expect(disclosure).toHaveAttribute('open', '');
      if (name === 'phone') {
        await summary.click(); await expect(disclosure).not.toHaveAttribute('open', '');
        await summary.click(); await expect(disclosure).toHaveAttribute('open', '');
      }
      const credits = disclosure.locator('[data-source-credit]');
      const visibleCredits = await credits.evaluateAll(nodes => nodes.map(node => ({
        source: node.getAttribute('data-source-credit') || '',
        attributions: Array.from(node.querySelectorAll('[data-credit-attribution]')).map(p => p.textContent),
        licences: Array.from(node.querySelectorAll('[data-credit-licence]')).map(p => p.textContent),
        links: Array.from(node.querySelectorAll('[data-credit-link]')).map(a => a.getAttribute('href')),
      })));
      const suppliedSources = await page.locator('[data-assertion-source]').allTextContents();
      expect(visibleCredits.map(c => c.source).sort()).toEqual([...new Set(suppliedSources)].sort());
      for (const credit of visibleCredits) {
        expect(credit.attributions).toEqual(notices[credit.source]);
        if (credit.source === 'puls') expect(credit.links).toEqual(['https://puls.peremova.org/']);
        expect(new Set(credit.licences).size).toBe(credit.licences.length);
        expect(new Set(credit.links).size).toBe(credit.links.length);
        await expect(disclosure.locator(`[data-source-credit="${credit.source}"]`)).toBeVisible();
      }
      const creditBody = credits.first();
      await creditBody.scrollIntoViewIfNeeded(); await expect(creditBody).toBeInViewport();
      await noPlaceholders(); await noOverflow();
      expect(await ready()).toBe('loaded');
      const creditsOpenedAxe = await serious();
      const openedShot = await page.screenshot(), openedPath = join(screens, `${name}-${key}-credits-opened.png`);
      if (originals.has(key)) {
        expect(sha(openedShot)).not.toBe(sha(shot));
        writeFileSync(openedPath, openedShot);
        await info.attach(`${name}-${key}-credits-opened`, { body: openedShot, contentType: 'image/png' });
        captures.push({ key, route, sourceHead: process.env.ATLAS_WORD_CARD_SOURCE_HEAD, htmlHash, viewport, control: 'details[data-page-audit] > summary',
          focused, interaction: name === 'phone' ? ['focus', 'Enter', 'click-close', 'click-reopen'] : ['focus', 'Enter'],
          before, after: await disclosure.getAttribute('open'), fonts, visibleCredits, firstCreditInViewport: true,
          initial: { path: initialPath, sha256: sha(shot) }, creditsOpened: { path: openedPath, sha256: sha(openedShot) },
          pageErrors: [...errors], failedRequests: [...failedRequests], axeSeriousClosed: closed, axeSeriousCreditsOpened: creditsOpenedAxe });
      }
      await summary.scrollIntoViewIfNeeded(); await summary.focus(); await expect(summary).toBeFocused();
      await page.keyboard.press('Enter'); await expect(disclosure).not.toHaveAttribute('open', '');
      const entrySummary = first.locator('[data-entry-audit] > summary');
      await entrySummary.focus(); await page.keyboard.press('Enter');
      await expect(first.locator('[data-entry-audit]')).toHaveAttribute('open', '');
      await expect(first.locator('[data-entry-audit] [data-release-assertion] pre').first()).toBeVisible();
      await page.keyboard.press('Enter'); await expect(first.locator('[data-entry-audit]')).not.toHaveAttribute('open', '');
      // Additional exhaustive axe coverage only. The source captures above used native interactions.
      await page.locator('details').evaluateAll(nodes => nodes.forEach(n => n.setAttribute('open', '')));
      await noPlaceholders(); await noOverflow();
      const opened = await serious();
      expect([closed, creditsOpenedAxe, opened], `${name} ${key}`).toEqual([[], [], []]);
      if (key === 'замок') {
        await expect(page.locator('[data-entry="wc_bgr5q9c06wxg"] [data-missing-paradigm]')).toBeVisible();
        await expect(page.locator('[data-entry="wc_cvkw5nzdg00n"] [data-paradigm-source="ulif"] th').first()).toHaveText('Відмінок');
      }
      if (key === 'баран') await expect(page.locator('[data-entry]').last().locator('[data-entry-label]')).toContainText('Proper name — річка в Україні');
      if (key === 'вряди-годи') {
        expect((await page.locator('[data-fact="stress"] dd[data-assertions]').evaluateAll(n => n.map(dd => [dd.querySelector('[data-fact-value]')?.textContent,
          Array.from(dd.querySelectorAll('[data-credit-ref]')).map(c => c.textContent).join()]))).sort())
          .toEqual([['вряди́-го́ди', 'ukrainian_word_stress'], ['вряди́-годи́', 'ulif']]);
        await expect(page.locator('[data-fact="stress"] [data-sources-differ]')).toBeVisible();
      }
      if (key === 'шапка') {
        expect(visibleCredits.map(c => c.source).sort()).toEqual(['puls', 'ulif', 'vesum']);
        await expect(page.locator('[data-paradigm-source]')).toHaveCount(2);
      }
      const search = page.locator('#atlas-candidate-search-input');
      await search.fill('чит');
      const option = page.locator('#atlas-candidate-search-list [role="option"][data-slug]').first();
      await expect(option).toBeVisible();
      const slug = await option.getAttribute('data-slug');
      expect(c37SearchSlugs.has(slug || '')).toBe(true);
      await search.press('ArrowDown'); await expect(option).toHaveAttribute('aria-selected', 'true');
      navigation.push({ viewport: name, key, kind: 'search-selection', query: 'чит', slug,
        text: await option.textContent(), interaction: ['fill', 'ArrowDown', 'Escape'], destinationNavigation: 'not exercised' });
      await search.press('Escape');
      const raw = first.locator('[data-raw-diagnostic]').first(), rawHref = await raw.getAttribute('href');
      await raw.focus(); await expect(raw).toBeFocused();
      await Promise.all([page.waitForURL(url => url.pathname + url.hash === rawHref), page.keyboard.press('Enter')]);
      const rawTarget = page.locator(`[id="${new URL(page.url()).hash.slice(1)}"]`);
      await expect(rawTarget).toBeVisible();
      await expect(rawTarget.locator('[data-release-citation]')).toBeVisible();
      navigation.push({ viewport: name, key, kind: 'raw-citation', href: rawHref, interaction: ['focus', 'Enter'],
        url: page.url(), citationVisible: true });
      results.push({ viewport: name, key, kind, axeSeriousClosed: closed, axeSeriousOpened: opened, axeSeriousCreditsOpened: creditsOpenedAxe, creditedFacts: facts });
    }
    await page.goto(`${origin}/lexicon-v2/release/`);
    const summaryClosed = await serious();
    await page.locator('details').evaluateAll(nodes => nodes.forEach(n => n.setAttribute('open', '')));
    expect([summaryClosed, await serious()], `${name} summary`).toEqual([[], []]);
    await noOverflow();
    results.push({ viewport: name, key: 'release summary', axeSeriousClosed: summaryClosed, axeSeriousOpened: [] });
  }
  expect(results).toHaveLength(20); expect(captures).toHaveLength(10);
  expect(errors).toEqual([]); expect(failedRequests).toEqual([]); expect(consoleErrors).toEqual([]);
  expect(http.filter(response => response.status >= 400)).toEqual([]);
  expect(http.some(response => response.url.endsWith('/lexicon/search-shards.json') && response.status === 200)).toBe(true);
  writeFileSync(join(screens, 'operator-captures.json'), JSON.stringify({ captures, screenshotCount: captures.length * 2,
    unequalPairs: captures.filter(c => c.initial.sha256 !== c.creditsOpened.sha256).length, errors, failedRequests, consoleErrors, http, navigation }, null, 2));
  await info.attach('operator-captures', { path: join(screens, 'operator-captures.json'), contentType: 'application/json' });
  return results;
}

function closePreview(server: Server): Promise<void> {
  return new Promise((done, reject) => {
    server.close(error => error ? reject(error) : done());
    server.closeAllConnections();
  });
}

// This spec drives an explicitly flag-enabled local build. No data certification.
const names = ['bronia-armour', 'bronia-reservation', 'idiom-buduvaty-povitriani-zamky', 'kliuch-1', 'vriady-hody-conflict', 'vybihaty-imperf', 'vybihty-perf', 'zamok-castle', 'zamok-legacy-split', 'zamok-lock', 'zamok-settlement',
  'control-complete', 'control-conflict', 'control-unverified', 'control-missing', 'control-suppressed', 'control-redirected', 'control-malformed', 'control-mismatched', 'control-internal', 'control-sum11', 'control-untrusted', 'real-data'];
for (const prefix of ['', 'compare/']) {
  for (const name of names) test(`${prefix}${name}`, async ({ page }, testInfo) => {
    await page.goto(`/lexicon-v2/${prefix}${name}/`);
    await expect(page.locator('[data-preview-banner]')).toContainText('not certified learner cards');
    await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', 'noindex, nofollow');
    await expect(page.locator('[data-input-hash]')).toHaveText(/^[a-f0-9]{64}$/);
    const candidate = page.getByRole('region', { name:'Candidate presentation', exact:true });
    const refused = ['control-suppressed','control-redirected','control-malformed','control-mismatched','real-data','zamok-legacy-split'].includes(name);
    if (refused) await expect(candidate.locator('[data-raw-value]')).toHaveCount(0);
    else for (const group of ['forms', 'stress', 'senses', 'examples', 'citations']) await expect(candidate.getByRole('region',{name:group,exact:true})).toBeVisible();
    if (name === 'control-complete') await expect(candidate.getByText('EXAMPLE_RAW',{exact:true})).toBeVisible();
    if (name === 'control-conflict') await expect(candidate.getByRole('region',{name:'stress',exact:true}).locator('[data-raw-value]')).toHaveCount(0);
    if (name === 'control-unverified') await expect(candidate.getByRole('region',{name:'stress',exact:true}).locator('[data-field-state]')).toHaveText('unverified');
    if (['control-internal','control-sum11'].includes(name)) await expect(candidate.getByRole('region',{name:'stress',exact:true})).toContainText('Source unavailable');
    if (name === 'control-mismatched') await expect(candidate).toContainText('Mismatched selected assertion binding');
    if (name === 'control-untrusted') {
      expect(await candidate.getByRole('region',{name:'stress',exact:true}).locator('[data-raw-value]').textContent()).toBe('<script>globalThis.previewInjected=1</script> RAW  A');
      expect(await page.evaluate(() => Object.hasOwn(globalThis,'previewInjected'))).toBe(false);
    }
    if (name === 'real-data') await expect(candidate).toContainText('Certified real-card export unavailable');
    if (name === 'zamok-castle' || name === 'zamok-lock') {
      await expect(candidate.locator('[data-preview-card]')).toHaveAttribute('data-preview-card',name === 'zamok-castle' ? 'wc_7k3m9q2xw4pd' : 'wc_c2v8n5rt6yhq');
      if (prefix) await expect(candidate).toContainText('Unresolved pairing');
    }
    if (prefix && !refused) {
      await expect(candidate).toContainText('Better/worse unavailable');
      await expect(candidate.locator('[data-result="better"], [data-result="worse"]')).toHaveCount(0);
    }
    if (prefix && name === 'kliuch-1') {
      await expect(page.getByRole('region',{name:'Current presentation',exact:true}).locator('[data-word-atlas]')).toBeVisible();
      const current = snapshot.records[1];
      if (!current) throw Error('Missing current snapshot');
      for (const [key,value] of Object.entries(current.record.entry)) {
        const cell = candidate.locator(`[data-comparison="entry.${key}"] td`).first();
        expect(await cell.textContent()).toBe(typeof value==='string' ? value : JSON.stringify(value,null,2));
      }
    }
    if (name === 'zamok-castle') {
      const bytes=readFileSync(new URL('../../docs/atlas/word-cards/examples/zamok-castle.json',import.meta.url));
      const source: unknown=JSON.parse(bytes.toString());
      if (!source || typeof source!=='object' || !('assertions' in source) || !Array.isArray(source.assertions)) throw Error('Source missing');
      const assertion=source.assertions.find((a: unknown) => a && typeof a==='object' && 'assertion_id' in a && a.assertion_id==='wa_5888b96f6142b2da61ca2973');
      if (!assertion || typeof assertion!=='object' || !('value' in assertion) || typeof assertion.value!=='string') throw Error('Raw source missing');
      expect(await candidate.getByRole('region',{name:'stress',exact:true}).locator('[data-raw-value]').textContent()).toBe(assertion.value);
      await testInfo.attach('source-sha256',{body:createHash('sha256').update(bytes).digest('hex'),contentType:'text/plain'});
    }
    await testInfo.attach('page',{body:await page.screenshot({fullPage:true}),contentType:'image/png'});
  });
}

for (const prefix of ['', 'compare/']) for (const c of revisionCases()) test(`${prefix}${c.name}`, async ({page}, info) => {
  await page.goto(`/lexicon-v2/${prefix}${c.name}/`);
  const candidate = page.getByRole('region',{name:'Candidate presentation',exact:true});
  await expect(page.locator('[data-input-hash]')).toHaveText(c.fingerprint);
  await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content','noindex, nofollow');
  await info.attach('page',{body:await page.screenshot({fullPage:true}),contentType:'image/png'});
  if (c.name.startsWith('f1-')) {
    if (c.name.endsWith('-predecessor')) {
      await expect(candidate.locator('[data-raw-value]')).toHaveCount(0);
      await expect(candidate).toContainText(c.name.includes('-suppressed-') ? 'Suppressed. No card body.' : 'Unavailable:');
    } else if (prefix) {
      await expect(candidate).toContainText('Unresolved pairing');
      await expect(candidate.locator('[data-comparison]')).toHaveCount(0);
      await expect(page.getByRole('region',{name:'Current presentation',exact:true}).locator('[data-word-atlas]')).toHaveCount(0);
    }
  } else {
    const stress = candidate.getByRole('region',{name:'stress',exact:true});
    const assertions = record(c.input).assertions;
    if (!Array.isArray(assertions)) throw Error('Missing source assertions');
    const a = record(assertions.find(a => record(a).assertion_id === record(record(record(c.input).fields).stress).selected));
    const citation = candidate.getByRole('region',{name:'citations',exact:true}).locator(`[data-field="${record(a.subject).id}/stress"]`);
    if (c.name.startsWith('f2-ulif-') || c.name.startsWith('f2-ulp_private-')) {
      expect(await stress.locator('[data-raw-value]').textContent()).toBe(a.value);
      await expect(stress).toContainText(`${a.assertion_id} | ${a.source_id} | ${a.snapshot_id} | ${a.locator}`);
      await expect(citation).toContainText(String(a.assertion_id));
    } else {
      await expect(stress.locator('[data-raw-value]')).toHaveCount(0);
      await expect(stress).toContainText('Source unavailable for this view');
      await expect(stress).not.toContainText(String(a.assertion_id));
      await expect(citation.locator('pre')).toHaveCount(0);
    }
  }
});

test.describe('source fidelity refusals', () => {
  test.describe.configure({ timeout: 150_000 });
  async function serve(root: string): Promise<Server> {
    const server = createServer((req, res) => {
      const path = new URL(req.url || '/', 'http://localhost').pathname;
      const file = resolve(root, '.' + (path.endsWith('/') ? path + 'index.html' : path));
      if (!file.startsWith(root + sep) || !existsSync(file)) { res.writeHead(404).end(); return; }
      res.setHeader('Content-Type', file.endsWith('.css') ? 'text/css' : file.endsWith('.js') ? 'text/javascript' : 'text/html');
      res.end(readFileSync(file));
    });
    await new Promise<void>((done, reject) => server.once('error', reject).listen(0, '127.0.0.1', done));
    return server;
  }
  test('closes preview server with a pending browser preconnection', async ({ fidelityScratch: scratch }) => {
    const server = await serve(scratch);
    const address = server.address();
    if (!address || typeof address === 'string') throw Error('No local port');
    const socket = connect(address.port, '127.0.0.1');
    try {
      await once(socket, 'connect');
      const closed = once(socket, 'close');
      await closePreview(server);
      await closed;
      expect(server.listening).toBe(false);
      expect(socket.destroyed).toBe(true);
    } finally {
      socket.destroy();
      if (server.listening) await closePreview(server);
    }
  });
  for (const encoding of ['json', 'jsonl']) for (const c of semanticCases) test(`semantic ${encoding}-${c.name}`, async ({ page, fidelityScratch: scratch }, info) => {
    const controls = semanticControls(join(scratch, 'semantic'));
    const name = `${encoding}-${c.name}`;
    const config = controls[name];
    if (!config) throw Error('Missing semantic control');
    const server = await serve(buildPreview(join(scratch, name), config));
    try {
      const address = server.address();
      if (!address || typeof address === 'string') throw Error('No local port');
      const origin = `http://127.0.0.1:${address.port}`;
      for (const prefix of ['', 'compare/']) {
        await page.goto(`${origin}/lexicon-v2/${prefix}release/${candidateId}/`);
        await info.attach(`${name}-${prefix ? 'compare' : 'word'}-observed`, { body: await page.content(), contentType: 'text/html' });
        if (c.expected === 'refuse') {
          await expect(page.locator('[data-release-card]')).toHaveCount(0);
          await page.goto(`${origin}/lexicon-v2/${prefix}release/`);
          await expect(page.getByRole('status')).toHaveText('Unavailable: Unsupported release value');
          await expect(page.locator('[data-raw-value], [data-report-action]')).toHaveCount(0);
        } else {
          await expect(page.locator('[data-release-card]')).toHaveAttribute('data-release-card', candidateId);
          const raw = c.target.includes('value') ? page.locator('[data-raw-value]').nth(1) :
            page.getByRole('region', { name: 'Known gaps' }).locator('pre').first();
          expect(await raw.textContent()).toBe(c.displayed);
        }
      }
    } finally { await closePreview(server); }
  });
  for (const empty of [false, true]) for (const encoding of ['json', 'jsonl']) for (const [name, reason] of noticeCases) test(`${encoding} withdrawal notice ${name}${empty ? ' zero rows' : ''}`, async ({ page, fidelityScratch: scratch }, info) => {
    const config = noticeControls(join(scratch, 'notices'), empty)[`${encoding}-notice-${name}`];
    if (!config?.artifactPath) throw Error('Missing notice control');
    const root = buildPreview(join(scratch, 'preview'), config);
    const server = await serve(root);
    try {
      const address = server.address();
      if (!address || typeof address === 'string') throw Error('No local port');
      for (const prefix of ['', 'compare/']) {
        const origin = `http://127.0.0.1:${address.port}/lexicon-v2/${prefix}release/`;
        if (reason) {
          await page.goto(origin + certifiedId + '/');
          await expect(page.locator('[data-release-card]')).toHaveCount(0);
          await page.goto(origin);
          await expect(page.getByRole('status')).toHaveText(`Unavailable: ${reason}`);
          await expect(page.locator('[data-release-summary], [aria-label="Withdrawal notice"], [data-raw-value], [data-report-action]')).toHaveCount(0);
        } else for (const id of empty ? [''] : [certifiedId, candidateId]) {
          expect((await page.goto(origin + (id ? id + '/' : '')))?.status()).toBe(200);
          if (empty) {
            await expect(page.locator('[data-release-count]')).toHaveText('0 cards');
            await expect(page.locator('[data-release-card], [data-release-status], [data-card-version], [data-raw-value], [data-report-action]')).toHaveCount(0);
            expect(existsSync(join(root, 'lexicon-v2', prefix, 'release', certifiedId))).toBe(false);
            expect(existsSync(join(root, 'lexicon-v2', prefix, 'release', candidateId))).toBe(false);
            await expect(page.locator('[data-input-hash]')).toHaveText(JSON.parse(config.pin || '{}').dataset_sha256);
            await expect(page.locator('[data-release-version]')).toHaveText(`Release ${JSON.parse(config.pin || '{}').release_version}`);
          }
          await info.attach(`${prefix ? 'compare' : 'word'}-${id}`, { body: await page.content(), contentType: 'text/html' });
          const notice = page.getByRole('region', { name: 'Withdrawal notice', exact: true });
          if (name === 'absent') await expect(notice).toHaveCount(0);
          else {
            await expect(notice).toBeVisible();
            const expected = JSON.parse(readFileSync(join(config.artifactPath, 'withdrawal-notice.json'), 'utf8'));
            expect(await notice.locator('pre').textContent()).toBe(JSON.stringify(expected, null, 2));
            expect(await page.evaluate(() => Object.hasOwn(globalThis, 'noticeInjected'))).toBe(false);
          }
        }
      }
    } finally { await closePreview(server); }
  });
  for (const encoding of ['json', 'jsonl']) test(`${encoding} zero rows notice stays flag gated`, async ({ fidelityScratch: scratch }) => {
    const config = noticeControls(join(scratch, 'notices'), true)[`${encoding}-notice-valid`];
    if (!config) throw Error('Missing notice control');
    const root = buildPreview(join(scratch, 'disabled'), { ...config, enabled: false });
    expect(existsSync(join(root, 'lexicon-v2'))).toBe(false);
  });
  for (const [name, reason] of fidelityRefusals) test(`refuses ${name}`, async ({ page, fidelityScratch: scratch }, info) => {
    const controls = fidelityControls(join(scratch, 'inputs'));
    const config = controls[name];
    if (!config) throw Error('Missing fidelity control');
    const root = buildPreview(join(scratch, name), config);
    const server = await serve(root);
    try {
      const address = server.address();
      if (!address || typeof address === 'string') throw Error('No local port');
      const origin = `http://127.0.0.1:${address.port}`;
      // Capture the defect before asserting refusal, so failing reproductions retain actual DOM evidence.
      await page.goto(`${origin}/lexicon-v2/release/${candidateId}/`);
      await info.attach(`${name}-observed`, { body: await page.content(), contentType: 'text/html' });
      await info.attach(`${name}-page`, { body: await page.screenshot(), contentType: 'image/png' });
      expect(await page.locator('[data-release-card]').count()).toBe(0);
      for (const prefix of ['', 'compare/']) {
        await page.goto(`${origin}/lexicon-v2/${prefix}release/`);
        await expect(page.getByRole('status')).toHaveText(`Unavailable: ${reason}`);
        await expect(page.locator('[data-release-card], [data-raw-value], [data-report-action]')).toHaveCount(0);
        await info.attach(`${name}-${prefix ? 'compare' : 'word'}-refusal`, { body: await page.screenshot(), contentType: 'image/png' });
      }
    } finally { await closePreview(server); }
  });
  test('retains faithful values and safe citation metadata', async ({ page, fidelityScratch: scratch }) => {
    const controls = fidelityControls(join(scratch, 'inputs'));
    const config = controls.faithful;
    if (!config) throw Error('Missing faithful control');
    const server = await serve(buildPreview(join(scratch, 'faithful'), config));
    try {
      const address = server.address();
      if (!address || typeof address === 'string') throw Error('No local port');
      for (const prefix of ['', 'compare/']) {
        await page.goto(`http://127.0.0.1:${address.port}/lexicon-v2/${prefix}release/${candidateId}/`);
        await expect(page.locator('[data-release-status]')).toHaveText('CANDIDATE');
        const raw = await page.locator('[data-raw-value]').nth(1).textContent();
        expect(JSON.parse(raw || '')).toEqual({ nested: [null, true, false, 0, 9007199254740991, -9007199254740991, 1.25, 'A😀𐐀B', ' A\r\nB '] });
        const gaps = await page.getByRole('region', { name: 'Known gaps' }).locator('pre').allTextContents();
        expect(gaps.map(text => JSON.parse(text))).toEqual([{ nested: ['😀', 9007199254740991] }]);
        const citation = JSON.parse(await page.locator('[data-release-citation]').nth(1).textContent() || '');
        expect(citation.licence.extra).toEqual({ nested: ['𐐀', -9007199254740991, null] });
      }
    } finally { await closePreview(server); }
  });
});

for (const c of relationCases()) test(`compare/${c.name}`, async ({page}, info) => {
  await page.goto(`/lexicon-v2/compare/${c.name}/`);
  await expect(page.locator('[data-input-hash]')).toHaveText(c.fingerprint);
  const candidate = page.getByRole('region',{name:'Candidate presentation',exact:true});
  const current = page.getByRole('region',{name:'Current presentation',exact:true});
  await info.attach('page',{body:await page.screenshot({fullPage:true}),contentType:'image/png'});
  if (c.name === 'relation-valid') {
    await expect(current.locator('[data-word-atlas]')).toBeVisible();
    expect(await candidate.locator('[data-comparison]').count()).toBeGreaterThan(0);
  } else {
    await expect(candidate).toContainText('Unresolved pairing');
    await expect(candidate.locator('[data-comparison]')).toHaveCount(0);
    await expect(current.locator('[data-word-atlas]')).toHaveCount(0);
  }
});

test.describe('release controls R01-R16 and R10b', () => {
  test.describe.configure({ mode: 'serial', timeout: 300_000 });
  const outputs: Record<string, string> = {};
  let server: Server;
  let origin: string;
  test.beforeAll(async ({ releaseScratch: scratch }) => {
    const controls = releaseControls(join(scratch, 'inputs'));
    for (const name of ['base', 'json', 'replacement', 'absent', 'malformed', 'missing', 'bytes', 'tamper', 'status', 'citation', 'required', 'off']) {
      const config = controls[name];
      if (!config) throw Error('Missing control');
      outputs[name] = buildPreview(join(scratch, name), config);
    }
    server = createServer((req, res) => {
      const url = new URL(req.url || '/', 'http://localhost');
      const parts = url.pathname.split('/');
      const name = parts[1] === '__control__' ? parts[2] : 'base';
      const root = outputs[name || ''];
      const path = parts[1] === '__control__' ? '/' + parts.slice(3).join('/') : url.pathname;
      if (!root) { res.writeHead(404).end(); return; }
      const file = resolve(root, '.' + (path.endsWith('/') ? path + 'index.html' : path));
      if (!file.startsWith(root + sep) || !existsSync(file)) { res.writeHead(404).end('Absent'); return; }
      res.setHeader('Content-Type', file.endsWith('.css') ? 'text/css' : file.endsWith('.js') ? 'text/javascript' : 'text/html');
      res.end(readFileSync(file));
    });
    await new Promise<void>((done, reject) => server.once('error', reject).listen(0, '127.0.0.1', done));
    const address = server.address();
    if (!address || typeof address === 'string') throw Error('No local port');
    origin = `http://127.0.0.1:${address.port}`;
  });
  test.afterAll(async () => { if (server?.listening) await closePreview(server); });
  const url = (control: string, path: string) => `${origin}/__control__/${control}/lexicon-v2/${path}/`;

  test('R01 candidate literal values, citations and declared gaps', async ({ page }) => {
    await page.goto(url('base', `release/${candidateId}`));
    await expect(page.locator('[data-release-status]')).toHaveText('CANDIDATE');
    await expect(page.locator('[data-card-version]')).toHaveText('Card version synthetic-candidate-1');
    await expect(page.locator('[data-release-version]')).toHaveText('Release v0.1.0-synthetic');
    expect(await page.locator('[data-raw-value]').allTextContents()).toEqual([
      'fixture-head', '<img src=x onerror=globalThis.releaseInjected=1> RAW  A', 'parallel-definition',
    ]);
    expect(await page.getByRole('region', { name: 'Known gaps' }).locator('pre').allTextContents()).toEqual([
      'Independent linguistic review pending', '<script>globalThis.releaseInjected=1</script>',
    ]);
    await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', 'noindex, nofollow');
    await expect(page.locator('[data-preview-banner]')).toBeVisible();
    expect(await page.evaluate(() => Object.hasOwn(globalThis, 'releaseInjected'))).toBe(false);
    expect(await page.content()).not.toContain(process.env.TMPDIR || 'must-not-render-host-path');
  });
  test('R02 certified branch is explicitly synthetic', async ({ page }) => {
    await page.goto(url('base', `release/${certifiedId}`));
    await expect(page.locator('[data-release-status]')).toHaveText('CERTIFIED');
    await expect(page.locator('[data-card-version]')).toHaveText('Card version cv_fa34b32f0e93bece65b966e8');
    await expect(page.getByText('Synthetic fixture. CERTIFIED exercises the UI branch under test authority only. No linguistic or publication approval.', { exact: true })).toBeVisible();
    expect(await page.locator('[data-raw-value]').allTextContents()).toEqual(['fixture-head', 'permitted-definition', 'parallel-definition']);
  });
  test('R03 mixed statuses account for every card and all six citations', async ({ page }) => {
    let total = 0;
    for (const [id, status] of [[certifiedId, 'CERTIFIED'], [candidateId, 'CANDIDATE']]) {
      await page.goto(url('base', `release/${id}`));
      await expect(page.locator('[data-release-card]')).toHaveAttribute('data-release-card', id);
      await expect(page.locator('[data-release-status]')).toHaveText(status);
      total += await page.locator('[data-release-citation]').count();
      for (const text of await page.locator('[data-release-citation]').allTextContents()) {
        const citation = JSON.parse(text);
        expect(citation.snapshot_id).toBe('fixture-v1');
        expect(citation.attribution).toBe(`Synthetic ${citation.source_id} edition`);
        expect(citation.licence.name).toBe('Fixture terms');
        expect(citation.locator).toMatch(/^(vesum|ulif):row:/);
      }
    }
    expect(total).toBe(6);
  });
  test('R04 same spelling routes exclusively by separate card IDs', async ({ page }) => {
    for (const id of [candidateId, certifiedId]) {
      await page.goto(url('base', `release/${id}`));
      await expect(page.locator('[data-release-card]')).toHaveAttribute('data-release-card', id);
      await expect(page.locator('[data-raw-value]').first()).toHaveText('fixture-head');
    }
    expect((await page.goto(url('base', 'release/fixture-head')))?.status()).toBe(404);
    await page.goto(url('base', 'word/fixture-head'));
    expect(await page.locator('[data-entry]').evaluateAll(n => n.map(e => e.getAttribute('data-entry')))).toEqual([certifiedId, candidateId]);
    await expect(page.locator('[data-entry] h2')).toHaveText(['1. fixture-head', '2. fixture-head']);
    expect(await page.evaluate(() => Object.hasOwn(globalThis, 'releaseInjected'))).toBe(false);
  });
  test('R05 valid different release at configured location refuses unchanged old pin', async ({ page }) => {
    await page.goto(url('replacement', 'release'));
    await expect(page.getByRole('status')).toHaveText('Unavailable: Manifest pin mismatch');
    await expect(page.locator('[data-release-card]')).toHaveCount(0);
  });
  test('R06 producer JSON format renders the full population', async ({ page }) => {
    for (const id of [candidateId, certifiedId]) {
      await page.goto(url('json', `release/${id}`));
      await expect(page.locator('[data-release-card]')).toHaveAttribute('data-release-card', id);
      await expect(page.locator('[data-release-version]')).toHaveText('Release v0.1.1-synthetic');
      await expect(page.locator('[data-input-hash]')).toHaveText(pins.json.dataset_sha256);
      await expect(page.locator('[data-release-assertion]')).toHaveCount(3);
    }
  });
  for (const [id, control, reason] of [
    ['R07', 'absent', 'Release not configured'], ['R08', 'malformed', 'Malformed manifest'],
    ['R09', 'missing', 'Missing artifact'], ['R10', 'bytes', 'Dataset integrity mismatch'],
    ['R10b', 'tamper', 'Manifest pin mismatch'], ['R11', 'status', 'Unknown card status'],
    ['R12', 'citation', 'Missing or malformed field citation'], ['R13', 'required', 'Missing or malformed card field'],
  ]) test(`${id} ${control} refuses visibly at intended boundary`, async ({ page }, info) => {
    await page.goto(url(control, 'release'));
    await expect(page.getByRole('status')).toHaveText(`Unavailable: ${reason}`);
    await expect(page.locator('[data-release-card], [data-raw-value]')).toHaveCount(0);
    expect(await page.content()).not.toContain(process.env.TMPDIR || 'must-not-render-host-path');
    await info.attach(id, { body: await page.screenshot(), contentType: 'image/png' });
  });
  test('R14 report is user-clicked and contains only six allowed identifiers', async ({ page }) => {
    const requests: string[] = [];
    await page.route('https://github.com/**', route => { requests.push(route.request().url()); return route.fulfill({ body: 'Manual report draft, no submission' }); });
    await page.goto(url('base', `release/${candidateId}`));
    const link = page.locator('[data-report-action]').nth(1);
    const href = await link.getAttribute('href');
    if (!href) throw Error('No report link');
    const target = new URL(href);
    expect(target.origin + target.pathname).toBe('https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/new');
    expect(JSON.parse(target.searchParams.get('body') || '')).toEqual({
      release_version: 'v0.1.0-synthetic', dataset_sha256: pins.jsonl.dataset_sha256,
      card_id: candidateId, card_version: 'synthetic-candidate-1', assertion_id: 'wa_000000000000000000000065', field: 'definition_uk',
    });
    expect(requests).toEqual([]);
    await link.click();
    await expect(page.getByText('Manual report draft, no submission')).toBeVisible();
    expect(requests).toEqual([href]);
  });
  test('R15 assembled comparison baseline survives; release comparison has no invented pairing', async ({ page }) => {
    await page.goto(url('base', 'compare/kliuch-1'));
    await expect(page.locator('[data-word-atlas]')).toBeVisible();
    expect(await page.locator('[data-comparison]').count()).toBeGreaterThan(0);
    for (const id of [candidateId, certifiedId]) {
      await page.goto(url('base', `compare/release/${id}`));
      await expect(page.getByRole('region', { name: 'Field comparison', exact: true })).toContainText('Unresolved pairing');
      await expect(page.locator('[data-comparison], [data-result="better"], [data-result="worse"]')).toHaveCount(0);
      await expect(page.locator('[data-word-atlas]')).toHaveCount(0);
    }
  });
  test('R16 flag-off build excludes preview routes and fixture bytes with configuration set', async ({ page }) => {
    for (const path of [`release/${candidateId}`, 'control-complete', 'release']) expect((await page.goto(url('off', path)))?.status()).toBe(404);
    expect(existsSync(join(outputs.off || '', 'lexicon-v2'))).toBe(false);
    for (const file of readdirSync(outputs.off || '', { recursive: true })) if (typeof file === 'string' && /\.(html|js|json|xml)$/.test(file)) {
      expect(readFileSync(join(outputs.off || '', file), 'utf8')).not.toMatch(/lexicon-v2|fixture-head|permitted-definition|synthetic-candidate-1|wc_0123456789a[bc]/);
    }
  });
});

// C37 candidate search on an actual Pages-style build. Configure
// ATLAS_WORD_CARD_C37_ROOT with the public release dist and, for the both-pane
// control, ATLAS_WORD_CARD_C37_CONTROLS_ROOT with the flag-enabled fixture dist.
// Run through playwright.word-card-search.config.ts; every other run skips this group.
const c37Root = process.env.ATLAS_WORD_CARD_C37_ROOT;
const c37ControlsRoot = process.env.ATLAS_WORD_CARD_C37_CONTROLS_ROOT;
const c37Inventory = JSON.parse(readFileSync(new URL('../src/lib/lexicon/word-card-preview-route-inventory.json', import.meta.url), 'utf8')) as {
  routes: { path: string; class: string }[];
};
const c37SearchSlugs = new Set((JSON.parse(readFileSync(new URL('../src/data/lexicon-search-index.json', import.meta.url), 'utf8')) as { s: string }[])
  .map(row => row.s));
const C37_WORD_CLASSES = ['card-diagnostic', 'compare-card-diagnostic', 'word-page', 'compare-word-page'];
const c37WordRoutes = c37Inventory.routes.filter(route => C37_WORD_CLASSES.includes(route.class));
type C37Server = { origin: string; close: () => Promise<void> };

async function c37Server(root: string): Promise<C37Server> {
  const module = await import(new URL('../scripts/serve-gh-pages-404.mjs', import.meta.url).href) as {
    createGhPages404Server: (options: { root: string; port: number; host: string }) => {
      server: { address: () => { port: number } | string | null }; listen: () => Promise<unknown>; close: () => Promise<void>;
    };
  };
  const app = module.createGhPages404Server({ root, port: 0, host: '127.0.0.1' });
  await app.listen();
  const address = app.server.address();
  if (!address || typeof address === 'string') throw Error('No C37 Pages-style port');
  return { origin: `http://127.0.0.1:${address.port}`, close: () => app.close() };
}

test.describe('C37 candidate in-page search', () => {
  test.skip(!c37Root, 'ATLAS_WORD_CARD_C37_ROOT is not set');
  let publicServer: C37Server;
  let controlsServer: C37Server | undefined;
  test.beforeAll(async () => {
    publicServer = await c37Server(c37Root!);
    if (c37ControlsRoot) controlsServer = await c37Server(c37ControlsRoot);
  });
  test.afterAll(async () => { await publicServer?.close(); await controlsServer?.close(); });

  test('C37 exposes bound search, Atlas return link and page label on every word and card route', async ({ page }, info) => {
    test.setTimeout(1_800_000);
    const tally = Object.fromEntries(C37_WORD_CLASSES.map(name => [name, { discovered: c37Inventory.routes.filter(r => r.class === name).length,
      run: 0, pass: 0, fail: [] as string[] }]));
    for (const route of c37WordRoutes) {
      const bucket = tally[route.class];
      bucket.run += 1;
      try {
        await page.goto(publicServer.origin + route.path, { waitUntil: 'domcontentloaded' });
        const candidate = page.getByRole('region', { name: 'Candidate presentation', exact: true });
        const widget = candidate.locator('[data-atlas-typeahead]');
        await expect(widget).toHaveCount(1);
        await expect(widget).toHaveAttribute('data-atlas-typeahead-ready', 'true', { timeout: 5000 });
        const input = page.locator('#atlas-candidate-search-input');
        await expect(input).toHaveCount(1);
        await expect(input).toHaveAttribute('role', 'combobox');
        await expect(input).toHaveAttribute('aria-controls', 'atlas-candidate-search-list');
        await expect(page.locator('#atlas-candidate-search-list')).toHaveCount(1);
        await expect(page.locator('#atlas-candidate-search-list')).toHaveAttribute('role', 'listbox');
        await expect(candidate.getByRole('link', { name: 'До Атласу', exact: true })).toHaveAttribute('href', '/lexicon/');
        await expect(candidate.getByText('Атлас слів (Лексикон)', { exact: true })).toBeVisible();
        bucket.pass += 1;
      } catch (error) {
        bucket.fail.push(`${route.path}: ${(error as Error).message.split('\n')[0]}`);
      }
      if (Object.values(tally).reduce((total, item) => total + item.fail.length, 0) >= 10) break;
    }
    await info.attach('c37-route-tally', { body: JSON.stringify(tally, null, 2), contentType: 'application/json' });
    expect(c37WordRoutes).toHaveLength(568);
    for (const name of C37_WORD_CLASSES) expect(tally[name].fail, name).toEqual([]);
  });

  for (const [viewport, size] of [['desktop', { width: 1440, height: 1000 }], ['phone', { width: 390, height: 844 }]] as const) {
    test(`C37 real index results, arrow selection and Enter navigate on ${viewport}`, async ({ page }, info) => {
      test.setTimeout(180_000);
      await page.setViewportSize(size);
      const seen: string[] = [];
      for (const name of C37_WORD_CLASSES) {
        const route = c37Inventory.routes.find(item => item.class === name)!;
        await page.goto(publicServer.origin + route.path);
        await expect(page.locator('[data-atlas-typeahead]')).toHaveAttribute('data-atlas-typeahead-ready', 'true', { timeout: 5000 });
        const input = page.locator('#atlas-candidate-search-input');
        await input.fill('чит');
        const options = page.locator('#atlas-candidate-search-list [role="option"][data-slug]');
        await expect(options.first()).toBeVisible();
        const slug = await options.first().getAttribute('data-slug');
        expect(slug && c37SearchSlugs.has(slug), `${route.class}: first result comes from the committed search index`).toBe(true);
        await input.press('ArrowDown');
        await expect(options.first()).toHaveAttribute('aria-selected', 'true');
        await input.press('Enter');
        await page.waitForURL(url => url.pathname === `/lexicon/${encodeURIComponent(slug!)}/`);
        const heading = await expectCurrentAtlasArticle(page, slug!, `${viewport} ${route.class} ${route.path}`);
        seen.push(`${viewport} ${route.class} ${route.path} -> ${slug} -> ${heading}`);
      }
      await info.attach(`c37-keyboard-${viewport}`, { body: seen.join('\n'), contentType: 'text/plain' });
    });
  }

  test('C37 URL-only navigation fails the article-arrival assertion (genuine negative control)', async ({ page }, info) => {
    test.setTimeout(120_000);
    if (!publicServer) throw Error('C37 public root is not configured');
    const route = c37Inventory.routes.find(item => item.class === 'word-page')!;
    await page.goto(publicServer.origin + route.path);
    await expect(page.locator('[data-atlas-typeahead]')).toHaveAttribute('data-atlas-typeahead-ready', 'true', { timeout: 5000 });
    const input = page.locator('#atlas-candidate-search-input');
    await input.fill('чит');
    const options = page.locator('#atlas-candidate-search-list [role="option"][data-slug]');
    await expect(options.first()).toBeVisible();
    const slug = await options.first().getAttribute('data-slug');
    if (!slug) throw Error('No search result slug');
    await input.press('ArrowDown');
    await input.press('Enter');
    await page.waitForURL(url => url.pathname === `/lexicon/${encodeURIComponent(slug)}/`);
    const heading = await expectCurrentAtlasArticle(page, slug, 'negative-control baseline');
    // A prefix-only URL spoof leaves the real article in place.
    const other = slug.slice(0, -1);
    expect(foldUkrainian(heading)).toContain(foldUkrainian(other));
    expect(foldUkrainian(heading)).not.toBe(foldUkrainian(other));
    await page.evaluate(path => window.history.pushState({}, '', path), `/lexicon/${encodeURIComponent(other)}/`);
    const legacyUrlOnly = new URL(page.url()).pathname === `/lexicon/${encodeURIComponent(other)}/`;
    expect(legacyUrlOnly, 'legacy URL-only check accepts the invalid state').toBe(true);
    const arrival = await inspectCurrentAtlasArticle(page, other);
    expect(arrival.ok, 'URL-only navigation must not count as article arrival').toBe(false);
    if (arrival.ok) throw Error('URL-only navigation was accepted as article arrival');
    expect(arrival.reason).toContain('does not match');
    // The committed positive assertion rejects that same state, so it cannot regress to a bare URL check.
    await expect(expectCurrentAtlasArticle(page, other, 'negative control', 2_000)).rejects.toThrow(/did not arrive/);
    expect(new URL(page.url()).pathname).toBe(`/lexicon/${encodeURIComponent(other)}/`);
    await info.attach('c37-url-only-negative-control', {
      body: JSON.stringify({ baselineSlug: slug, baselineHeading: heading, urlOnlySlug: other, rejection: arrival.reason }, null, 2),
      contentType: 'application/json',
    });
  });

  test('C37 tab-activation assertion rejects an inactive tab (genuine negative control)', async ({ page }, info) => {
    if (!publicServer) throw Error('C37 public root is not configured');
    await page.goto(publicServer.origin + '/lexicon/' + encodeURIComponent('замок') + '/');
    const tabs = page.getByRole('tab');
    await expect(tabs).toHaveCount(2);
    // Before any click tab 1 is inactive and its panel is hidden: the assertion must reject that state.
    const inactiveControls = await tabs.nth(1).getAttribute('aria-controls');
    expect(inactiveControls && await page.locator(`#${inactiveControls}`).count(), 'legacy panel-presence check accepts the inactive state').toBe(1);
    const inactive = await inspectHeteronymTab(page, 1);
    expect(inactive.ok, 'an inactive tab must not read as activated').toBe(false);
    await tabs.nth(1).click();
    const active = await inspectHeteronymTab(page, 1);
    expect(active.ok, active.reason).toBe(true);
    expect(active.title ?? '').toContain('замо́к');
    await info.attach('c37-tab-activation-control', {
      body: JSON.stringify({ inactiveReason: inactive.reason, activeTitle: active.title }, null, 2),
      contentType: 'application/json',
    });
  });

  test('C37 Atlas return link reaches the current Atlas', async ({ page }) => {
    const route = c37Inventory.routes.find(item => item.class === 'word-page')!;
    await page.goto(publicServer.origin + route.path);
    await page.getByRole('region', { name: 'Candidate presentation', exact: true })
      .getByRole('link', { name: 'До Атласу', exact: true }).click();
    await page.waitForURL(url => url.pathname === '/lexicon/');
    const landing = page.locator('[data-word-atlas]');
    await expect(landing).toBeVisible();
    await expect(landing.locator('#lexicon-landing-search-input')).toBeVisible();
  });

  test('C37 current and candidate controls stay unique and independent', async ({ page }) => {
    test.skip(!c37ControlsRoot, 'ATLAS_WORD_CARD_C37_CONTROLS_ROOT is not set');
    await page.goto(controlsServer!.origin + '/lexicon-v2/compare/kliuch-1/');
    const currentInput = page.locator('#atlas-article-search-input');
    const candidateInput = page.locator('#atlas-candidate-search-input');
    await expect(page.locator('[data-atlas-typeahead]')).toHaveCount(2);
    await expect(currentInput).toHaveAttribute('aria-controls', 'atlas-article-search-list');
    await expect(candidateInput).toHaveAttribute('aria-controls', 'atlas-candidate-search-list');
    for (const widget of await page.locator('[data-atlas-typeahead]').all())
      await expect(widget).toHaveAttribute('data-atlas-typeahead-ready', 'true', { timeout: 5000 });
    await candidateInput.fill('чит');
    const candidateOptions = page.locator('#atlas-candidate-search-list [role="option"][data-slug]');
    await expect(candidateOptions.first()).toBeVisible();
    const candidateCount = await candidateOptions.count();
    await currentInput.fill('чит');
    await expect(page.locator('#atlas-article-search-list [role="option"][data-slug]').first()).toBeVisible();
    await expect(candidateOptions).toHaveCount(candidateCount);
    await expect(candidateInput).toHaveValue('чит');
    await expect(currentInput).toHaveValue('чит');
    const slug = await candidateOptions.first().getAttribute('data-slug');
    await candidateInput.press('ArrowDown');
    await candidateInput.press('Enter');
    await page.waitForURL(url => url.pathname === `/lexicon/${encodeURIComponent(slug!)}/`);
  });

  test('C37 keeps the two release summaries free of candidate search', async ({ page }) => {
    for (const path of ['/lexicon-v2/release/', '/lexicon-v2/compare/release/']) {
      await page.goto(publicServer.origin + path);
      await expect(page.locator('[data-release-summary]')).toHaveCount(1);
      await expect(page.locator('[data-atlas-typeahead], #atlas-candidate-search-input')).toHaveCount(0);
    }
  });

  test.describe('C37 original action timeout reproduction', () => {
    test.use({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, locale: 'uk-UA', timezoneId: 'UTC', colorScheme: 'light' });
    test('C37 exercises the 14 original disclosure and tab targets', async ({ page }, info) => {
      test.setTimeout(300_000);
      const actions: { route: string; kind: 'disclosure' | 'tab'; index: number; candidate: boolean }[] = [
        { route: '/lexicon-v2/word/близько не пахне/', kind: 'disclosure', index: 1, candidate: true },
        { route: '/lexicon-v2/word/блигом світ/', kind: 'disclosure', index: 1, candidate: true },
        { route: "/lexicon-v2/word/гнат-безп'ятко/", kind: 'disclosure', index: 1, candidate: true },
        { route: '/lexicon-v2/word/боже помагай/', kind: 'disclosure', index: 1, candidate: true },
        { route: '/lexicon/замок/', kind: 'tab', index: 0, candidate: false },
        { route: '/lexicon/замок/', kind: 'tab', index: 1, candidate: false },
        { route: '/lexicon-v2/word/бог помилував/', kind: 'disclosure', index: 1, candidate: true },
        { route: '/lexicon-v2/word/блекоти наїлась/', kind: 'disclosure', index: 1, candidate: true },
        { route: '/lexicon/юридичний/', kind: 'disclosure', index: 1, candidate: false },
        { route: '/lexicon-v2/word/божий світ/', kind: 'disclosure', index: 1, candidate: true },
        { route: '/lexicon-v2/word/благородний жест/', kind: 'disclosure', index: 1, candidate: true },
        { route: '/lexicon-v2/word/валаамова ослиця/', kind: 'disclosure', index: 1, candidate: true },
        { route: '/lexicon-v2/word/блудний син/', kind: 'disclosure', index: 1, candidate: true },
        { route: '/lexicon-v2/word/бог зна що таке/', kind: 'disclosure', index: 1, candidate: true },
      ];
      const results: Record<string, unknown>[] = [];
      for (const item of actions) {
        await page.goto(publicServer.origin + encodeURI(item.route), { waitUntil: 'domcontentloaded' });
        await page.waitForFunction(() => document.querySelector('[data-word-atlas],[data-release-page],[data-release-card],[data-word-atlas-state="not_found"]'), {}, { timeout: 30000 });
        const article = page.locator(item.candidate ? '[data-release-page]' : '[data-word-atlas]');
        await expect(article).toHaveCount(1);
        const nodes = item.kind === 'disclosure' ? article.locator('details > summary') : article.getByRole('tab');
        const targetIndex = item.kind === 'disclosure' ? item.index - 1 : item.index;
        const record: Record<string, unknown> = { ...item, historicalGlobalIndex: item.index, articleIndex: targetIndex,
          historicalDisposition: 'original-timeout-cause-unverified', clicks: [] as number[], timeouts: [] as Record<string, unknown>[] };
        // The historical global disclosure ordinal included the mobile menu at zero.
        const order = [targetIndex];
        for (const i of order) {
          try { await nodes.nth(i).click({ timeout: 2000 }); (record.clicks as number[]).push(i); }
          catch (error) { (record.timeouts as Record<string, unknown>[]).push({ index: i, error: (error as Error).message }); }
        }
        const target = nodes.nth(targetIndex);
        record.targetLabel = (await target.textContent())?.trim();
        const historicalNodes = item.kind === 'disclosure' ? page.locator('details > summary') : page.getByRole('tab');
        expect(await target.evaluate((node, historical) => node === document.querySelectorAll(historical.selector)[historical.index],
          { selector: item.kind === 'disclosure' ? 'details > summary' : '[role=tab]', index: item.index })).toBe(true);
        record.historicalLabel = (await historicalNodes.nth(item.index).textContent())?.trim();
        if (item.kind === 'disclosure') {
          const opened = await target.locator('..').getAttribute('open') !== null;
          const revealed = await target.locator('..').locator(':scope > :not(summary)').first().isVisible().catch(() => false);
          record.targetVisible = await target.isVisible().catch(() => false);
          record.targetOpened = opened && revealed;
          // A timeout can mean the disclosure is present but covered: keep that distinction visible.
          if (!opened) record.classification = record.targetVisible
            ? 'unresolved-pointer-intercepted-on-current-page' : 'unresolved-not-visible-on-current-page';
        } else {
          const panel = await inspectHeteronymTab(page, item.index);
          record.targetOpened = panel.ok;
          record.panel = panel.title ?? null;
          if (!panel.ok) record.classification = panel.reason;
        }
        record.freshDisposition = record.targetOpened ? 'opened-and-revealed' : 'unresolved';
        results.push(record);
      }
      await info.attach('c37-original-action-timeouts', { body: JSON.stringify(results, null, 2), contentType: 'application/json' });
      expect(results).toHaveLength(14);
      // Every original word-content target must open through its direct action.
      expect(results.filter(item => !item.candidate).map(item => [item.route, item.kind, item.index, item.targetOpened]))
        .toEqual([['/lexicon/замок/', 'tab', 0, true], ['/lexicon/замок/', 'tab', 1, true], ['/lexicon/юридичний/', 'disclosure', 1, true]]);
      expect(results.filter(item => item.candidate).every(item => item.targetOpened === true)).toBe(true);
      // Tab success means the matching panel is exposed and owned by that tab, not just that the click returned.
      const currentTabs = results.filter(item => item.kind === 'tab');
      expect(currentTabs.map(item => typeof item.panel)).toEqual(['string', 'string']);
      for (const tab of currentTabs) expect(foldUkrainian(String(tab.panel))).toContain('замок');
      expect(new Set(currentTabs.map(item => item.panel)).size).toBe(2);
      // Fresh direct action does not establish the cause of any historical timeout.
      const currentDisclosure = results.find(item => item.route === '/lexicon/юридичний/');
      expect(currentDisclosure?.targetOpened).toBe(true);
      expect(currentDisclosure?.targetVisible).toBe(true);
      expect(results.every(item => item.historicalDisposition === 'original-timeout-cause-unverified')).toBe(true);
      // No sibling or site-menu clicks may manufacture a current word-article failure.
      const timeouts = results.flatMap(item => (item.timeouts as { index: number; error: string }[])
        .map(timeout => ({ route: item.route as string, index: timeout.index, error: timeout.error })));
      expect(timeouts.map(item => `${item.route}#${item.index}`)).toEqual([]);
    });
  });
});
