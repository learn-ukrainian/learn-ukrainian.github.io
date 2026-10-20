import { expect, test as base } from '@playwright/test';
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
    if (c.name.startsWith('f2-ulif-')) {
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
