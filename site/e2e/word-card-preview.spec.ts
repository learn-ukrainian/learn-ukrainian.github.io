import { expect, test as base, type Locator } from '@playwright/test';
import { AxeBuilder } from '@axe-core/playwright';
import { readFileSync, writeFileSync, mkdtempSync, existsSync, readdirSync, mkdirSync, copyFileSync, rmSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { createServer, type Server } from 'node:http';
import { connect } from 'node:net';
import { once } from 'node:events';
import { basename, join, resolve, sep } from 'node:path';
import { tmpdir } from 'node:os';
import snapshot from '../tests/fixtures/word-card-preview/current';
import { revisionCases, relationCases, record } from '../tests/fixtures/word-card-preview/inputs';
import { buildPreview, releaseControls, candidateId, certifiedId, pins, fidelityControls, fidelityRefusals, semanticCases, semanticControls, noticeCases, noticeControls } from '../tests/fixtures/word-card-preview/release-controls';

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
  fidelityScratch: async ({}, use, info) => {
    await withScratch('fidelity-browser-', info.outputPath('build-logs'), use);
  },
  releaseScratch: [async ({}, use, info) => {
    await withScratch('release-browser-', join(info.project.outputDir, `release-build-logs-${info.workerIndex}`), use);
  }, { scope: 'worker' }],
});

// Actual-release proof is an explicit local configuration; CI controls remain offline.
if (process.env.ATLAS_WORD_CARD_PUBLIC_PROOF_PATH) test('public pinned release: all routes, frozen literals and fixture isolation', async ({ page }, info) => {
  test.setTimeout(1_500_000);
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
  process.env.PUBLIC_ATLAS_WORD_CARD_PREVIEW_CONTROLS = '';
  let output: string;
  try { output = buildPreview(join(root, 'public'), { enabled: true, artifactPath }); }
  finally { process.env.PUBLIC_ATLAS_WORD_CARD_PREVIEW_CONTROLS = '1'; }
  const files = readdirSync(output, { recursive: true }).filter((name): name is string => typeof name === 'string');
  const routes = files.filter(name => name.startsWith('lexicon-v2/') && name.endsWith('/index.html'));
  expect(routes).toHaveLength(570);
  expect(routes.sort()).toEqual(['lexicon-v2/release/index.html', 'lexicon-v2/compare/release/index.html', ...rows.flatMap(row =>
    ['', 'compare/'].map(prefix => `lexicon-v2/${prefix}release/${row.card_id}/index.html`)), ...learner.flatMap(([key]) =>
    ['', 'compare/'].map(prefix => `lexicon-v2/${prefix}word/${key}/index.html`))].sort());
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
    res.setHeader('Content-Type', file.endsWith('.css') ? 'text/css' : file.endsWith('.js') ? 'text/javascript' : 'text/html');
    res.end(readFileSync(file));
  });
  await new Promise<void>(done => server.listen(0, '127.0.0.1', done));
  const address = server.address();
  if (!address || typeof address === 'string') throw Error('No public proof port');
  let checked = 0;
  // Every raw assertion keeps its exact value, citation, attribution, allowlisted links, gap marker and report body.
  const checkAssertions = async (scope: Locator, row: Row) => {
    const displayed = await scope.locator('[data-release-assertion]').evaluateAll(nodes => nodes.map(node => ({
      id: node.getAttribute('data-release-assertion'), value: node.querySelector('[data-raw-value]')?.textContent,
      citation: node.querySelector('[data-release-citation]')?.textContent, attribution: node.querySelector('[data-source-attribution]')?.textContent,
      field: node.querySelector('h4')?.textContent, subject: node.querySelector('p')?.textContent,
      links: Array.from(node.querySelectorAll('[data-source-link]')).map(link => link.getAttribute('href')),
      report: node.querySelector('[data-report-action]')?.getAttribute('href'), gap: node.querySelector('[data-attribution-gap]')?.getAttribute('data-attribution-gap'),
    })));
    // One comparison per card keeps every field check while avoiding ~110k individual expect() calls.
    const frozenMismatches = row.fields.filter(source => { const frozen = expected.get(`${row.card_id}/${source.assertion_id}`);
      return !frozen || sha(canonical(source.value)) !== frozen.value_sha256 || sha(canonical(source.citation)) !== frozen.citation_sha256 || frozen.field !== source.field; });
    expect(frozenMismatches.map(source => source.assertion_id), row.card_id).toEqual([]);
    const shape = (item: typeof displayed[number]) => ({ ...item, citation: item.citation ? sha(canonical(JSON.parse(item.citation))) : null,
      report: item.report ? JSON.parse(new URL(item.report).searchParams.get('body') || '') : null, gap: item.gap ?? null });
    expect(displayed.map(shape), row.card_id).toEqual(row.fields.map(source => {
      const sourceId = source.citation.source_id;
      return { id: source.assertion_id, value: typeof source.value === 'string' ? source.value : JSON.stringify(source.value, null, 2),
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
          await checkAssertions(page.locator(`[data-entry-audit="${row.card_id}"]`), row);
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
    const heldOut = await readability(page, `http://127.0.0.1:${address.port}`, join(root, 'screens'), info);
    await page.goto(`http://127.0.0.1:${address.port}/lexicon-v2/release/${rows[0]?.card_id}/`);
    const requests: string[] = [];
    await page.route('https://github.com/**', route => { requests.push(route.request().url()); return route.fulfill({ body: 'Manual public report draft' }); });
    const report = page.locator('[data-report-action]').first(), href = await report.getAttribute('href');
    expect(requests).toEqual([]);
    await report.click();
    await expect(page.getByText('Manual public report draft')).toBeVisible();
    expect(requests).toEqual([href]);
    writeFileSync(join(root, 'proof.json'), JSON.stringify({ routes, scanned, overlap, checked, expectedAssertions: expected.size, heldOut,
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


for (const prefix of ['fidelity-browser-', 'release-browser-']) test(`releases ${prefix}scratch after success and failure`, async ({}, info) => {
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

// Held-out page classes: first-screen readability, per-fact credits, collapsed JSON, keyboard disclosure and axe on desktop and phone.
const HELD_OUT: [string, string][] = [['замок', 'homonyms, one without paradigm'], ['баран', 'common and proper name'], ['різати правду-матку', 'MWE'],
  ['вряди-годи', 'conflicting stress'], ['шапка', 'PULS and VESUM attribution gaps'], ['батьківщина', 'capitalized common and proper'],
  ['ключ', 'homonyms with senses and synonyms'], ['читати', 'verb forms'], ['новий', 'adjective and proper name']];
async function readability(page: import('@playwright/test').Page, origin: string, screens: string, info: import('@playwright/test').TestInfo) {
  mkdirSync(screens, { recursive: true });
  const results: Record<string, unknown>[] = [];
  const serious = async () => (await new AxeBuilder({ page }).analyze()).violations.filter(v => ['serious', 'critical'].includes(v.impact ?? ''))
    .map(v => `${v.id}: ${v.nodes.map(node => node.target.join(' ')).join(', ')}`);
  for (const [name, viewport] of [['desktop', { width: 1280, height: 800 }], ['phone', { width: 390, height: 844 }]] as const) {
    await page.setViewportSize(viewport);
    for (const [key, kind] of HELD_OUT) {
      await page.goto(`${origin}/lexicon-v2/word/${encodeURIComponent(key)}/`);
      const first = page.locator('[data-entry]').first();
      for (const target of [page.locator('h1'), first.locator('h2'), first.locator('[data-entry-label]'), first.locator(':scope > .wc-facts dd').last()]) await expect(target).toBeInViewport();
      await expect(page.locator('pre:visible')).toHaveCount(0);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), `${name} ${key} horizontal overflow`).toBe(true);
      const facts = await page.locator('[data-fact] dd:not([data-sources-differ])').count();
      await expect(page.locator('[data-fact] dd:not([data-sources-differ]) [data-credits]')).toHaveCount(facts);
      const closed = await serious();
      const shot = await page.screenshot();
      writeFileSync(join(screens, `${name}-${key}.png`), shot);
      await info.attach(`${name}-${key}`, { body: shot, contentType: 'image/png' });
      const summary = first.locator('[data-entry-audit] > summary');
      await summary.focus();
      await page.keyboard.press('Enter');
      await expect(first.locator('[data-entry-audit]')).toHaveAttribute('open', '');
      await expect(first.locator('[data-entry-audit] [data-release-assertion] pre').first()).toBeVisible();
      await page.keyboard.press('Enter');
      await expect(first.locator('[data-entry-audit]')).not.toHaveAttribute('open', '');
      await page.locator('details').evaluateAll(nodes => nodes.forEach(n => n.setAttribute('open', '')));
      const opened = await serious();
      expect([closed, opened], `${name} ${key}`).toEqual([[], []]);
      if (key === 'замок') {
        await expect(page.locator('[data-entry="wc_bgr5q9c06wxg"] [data-missing-paradigm]')).toBeVisible();
        await expect(page.locator('[data-entry="wc_cvkw5nzdg00n"] [data-paradigm-source="ulif"] th').first()).toHaveText('Відмінок');
      }
      if (key === 'баран') await expect(page.locator('[data-entry]').last().locator('[data-entry-label]')).toContainText('Proper name — річка в Україні');
      if (key === 'вряди-годи') {
        expect((await page.locator('[data-fact="stress"] dd[data-assertions]').evaluateAll(n => n.map(dd => [dd.querySelector('[data-fact-value]')?.textContent,
          Array.from(dd.querySelectorAll('[data-credits] a, [data-credits] span[title]')).map(c => c.textContent).join()]))).sort())
          .toEqual([['вряди́-го́ди', 'ukrainian_word_stress'], ['вряди́-годи́', 'ulif']]);
        await expect(page.locator('[data-fact="stress"] [data-sources-differ]')).toBeVisible();
      }
      if (key === 'шапка') {
        for (const gap of ['puls_reference_placeholder', 'vesum_version_placeholder']) await expect(page.locator(`[data-credit-gap="${gap}"]`).first()).toBeVisible();
        await expect(page.locator('[data-paradigm-source]')).toHaveCount(2);
      }
      results.push({ viewport: name, key, kind, axeSeriousClosed: closed, axeSeriousOpened: opened, creditedFacts: facts });
    }
    await page.goto(`${origin}/lexicon-v2/release/`);
    const summaryClosed = await serious();
    await page.locator('details').evaluateAll(nodes => nodes.forEach(n => n.setAttribute('open', '')));
    expect([summaryClosed, await serious()], `${name} summary`).toEqual([[], []]);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), `${name} summary horizontal overflow`).toBe(true);
    results.push({ viewport: name, key: 'release summary', axeSeriousClosed: summaryClosed, axeSeriousOpened: [] });
  }
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
