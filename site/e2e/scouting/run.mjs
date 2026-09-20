#!/usr/bin/env node
// Practice Hub scouting harness (#8317). Standalone: NOT a Playwright test
// (no *.spec.ts), so `playwright test` never picks it up.
import { chromium, webkit, devices } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';

const LIVE_URL = 'https://learn-ukrainian.github.io';
const LOCAL_URL = 'http://127.0.0.1:4321';
const PRACTICE = '/words-of-the-day/practice/';
const SLICES = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8'];
const PROFILES = {
  desktop: { label: 'Desktop Chrome', options: { ...devices['Desktop Chrome'] } },
  phone: { label: 'iPhone 14 (Chromium emulation)', options: { ...devices['iPhone 14'], hasTouch: true }, engine: 'chromium' },
  android: { label: 'Pixel 7', options: { ...devices['Pixel 7'], hasTouch: true } },
  fast: { label: 'Fast desktop (1440x900, no throttle)', options: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
  explorer: { label: 'Explorer (Desktop, prefers-reduced-motion)', options: { ...devices['Desktop Chrome'], reducedMotion: 'reduce' } },
};
const DEFAULT_PROFILES = ['desktop', 'phone', 'android'];

const HELP = `Practice Hub scouting harness (#8317)

Usage: node e2e/scouting/run.mjs --slice <id> --out <dir> [options]

  --help                  Show this help
  --slice <id>            Slice id: ${SLICES.join(', ')} (only C1 is implemented; C2-C8 are stubs)
  --out <dir>             Output directory for report.json, report.md and trace-*.zip
  --profile <name>        desktop | phone | android | fast | explorer  (default: desktop,phone,android;
                          comma-separated list allowed)
  --live                  Target ${LIVE_URL} (default: ${LOCAL_URL}, run \`npm run preview\` first)
  --base <url>            Override the base URL

Phone profiles are Playwright device emulation, not real hardware.
`;

function parseArgs(argv) {
  const a = { profiles: null, live: false };
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i];
    if (k === '--help' || k === '-h') a.help = true;
    else if (k === '--live') a.live = true;
    else if (['--slice', '--out', '--profile', '--base'].includes(k)) {
      const v = argv[++i];
      if (v === undefined || v.startsWith('--')) throw new Error(`${k} needs a value`);
      a[k.slice(2)] = v;
    } else throw new Error(`Unknown argument: ${k}`);
  }
  return a;
}

const now = () => performance.now();
const round = (n) => (n == null ? null : Math.round(n));

async function withJourney(browser, profileName, slice, name, base, out, fn) {
  const prof = PROFILES[profileName];
  const { defaultBrowserType, ...ctxOptions } = prof.options; // fresh context = clean storage
  const context = await browser.newContext({ ...ctxOptions, baseURL: base, serviceWorkers: 'block' });
  await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  page.on('console', (m) => m.type() === 'error' && errors.push(m.text()));
  let result;
  try {
    result = await fn(page);
  } catch (e) {
    result = { error: String(e).split('\n')[0] };
  }
  const tracePath = join(out, `trace-${slice.toLowerCase()}-${profileName}-${name}.zip`);
  await context.tracing.stop({ path: tracePath });
  await context.close();
  return { journey: name, profile: profileName, trace: tracePath, consoleErrors: errors.slice(0, 5), ...result };
}

// Visible practice-ish entry points on the current page.
const PRACTICE_RE = /practi[cs]e|drill|exercise|quiz|практик|вправ/i;
async function findPracticeLinks(page) {
  return page.evaluate((src) => {
    const re = new RegExp(src, 'i');
    const vis = (el) => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden'; };
    return [...document.querySelectorAll('a[href], button, summary')]
      .filter((el) => re.test((el.textContent || '') + ' ' + (el.getAttribute('href') || '')))
      .map((el) => ({ text: (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 60), href: el.getAttribute('href'), visible: vis(el), inNav: !!el.closest('nav,header') }));
  }, PRACTICE_RE.source);
}

// The Practice Hub itself (NOT other "practice" pages such as /b1/practice-exam/).
const TARGET = '/words-of-the-day/practice';
const isTarget = (href) => !!href && new URL(href, 'https://x.invalid/').pathname.replace(/\/$/, '') === TARGET;

// Click path to the hub: direct link on this page (1 click), else via a plausible parent (2 clicks).
async function clicksToPractice(page) {
  const direct = async () => (await findPracticeLinks(page)).find((l) => l.visible && isTarget(l.href));
  let hit = await direct();
  if (hit) {
    await page.locator(`a[href="${hit.href}"]:visible`).first().click();
    return { reached: true, clicks: 1, path: [`${hit.text} -> ${hit.href}`] };
  }
  const start = page.url();
  for (const parent of ['/words-of-the-day/', '/lexicon/']) {
    const link = page.locator(`a[href="${parent}"]:visible`).first();
    if (!(await link.count())) continue;
    await link.click();
    await page.waitForLoadState('domcontentloaded');
    hit = await direct();
    if (hit) {
      await page.locator(`a[href="${hit.href}"]:visible`).first().click();
      return { reached: true, clicks: 2, path: [`nav -> ${parent}`, `${hit.text} -> ${hit.href}`] };
    }
    await page.goto(start, { waitUntil: 'domcontentloaded' });
  }
  return { reached: false, clicks: null, path: [] };
}

async function slice1(browser, profileName, base, out) {
  const results = [];

  results.push(await withJourney(browser, profileName, 'C1', 'j1-home', base, out, async (page) => {
    await page.goto('/', { waitUntil: 'load' });
    const entryPoints = await findPracticeLinks(page);
    const nav = await page.evaluate(() => [...document.querySelectorAll('nav a')].filter((a) => a.getBoundingClientRect().width > 0).map((a) => a.getAttribute('href')));
    const found = await clicksToPractice(page);
    return { entryPointsOnHome: entryPoints, visibleNavLinks: nav, ...found };
  }));

  results.push(await withJourney(browser, profileName, 'C1', 'j2-word', base, out, async (page) => {
    await page.goto('/lexicon/browse/', { waitUntil: 'load' });
    const browsePractice = await findPracticeLinks(page);
    await page.locator('[data-index-search]').fill('офіс');
    const link = page.locator('.atlas-index-link', { hasText: 'офіс' }).first();
    await link.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
    const wordHref = await link.getAttribute('href').catch(() => null);
    if (!wordHref) return { note: 'no word link found via /lexicon/browse/ search', browsePractice };
    await page.goto(wordHref, { waitUntil: 'load' });
    const wordPagePractice = await findPracticeLinks(page);
    const found = await clicksToPractice(page);
    return { wordPage: wordHref, browsePractice, wordPagePractice, ...found };
  }));

  results.push(await withJourney(browser, profileName, 'C1', 'j3-direct', base, out, async (page) => {
    const t0 = now();
    await page.goto(PRACTICE, { waitUntil: 'commit' });
    const ctl = page.locator('main button:visible, main a[href]:visible, main input:visible, main select:visible, main summary:visible').first();
    await ctl.waitFor({ state: 'visible', timeout: 20000 });
    const ttfi = now() - t0;
    await page.waitForLoadState('load');
    const loadMs = now() - t0;
    const info = await page.evaluate(() => {
      const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
      const nav = performance.getEntriesByType('navigation')[0];
      return {
        h1: document.querySelector('h1')?.textContent?.trim() ?? null,
        modes: [...document.querySelectorAll('button[data-mode]')].filter(vis).map((b) => b.dataset.mode),
        trackCards: document.querySelectorAll('[data-testid*="track"], .practice-track, [class*="track-card"]').length,
        testids: [...new Set([...document.querySelectorAll('[data-testid]')].filter(vis).map((e) => e.dataset.testid))].slice(0, 25),
        dialogs: document.querySelectorAll('dialog[open], [role="dialog"]').length,
        buttonsVisible: [...document.querySelectorAll('main button')].filter(vis).length,
        horizontalOverflow: document.documentElement.scrollWidth > innerWidth + 1,
        smallTargets: [...document.querySelectorAll('main button, main a[href]')].filter(vis).filter((e) => { const r = e.getBoundingClientRect(); return r.width < 44 || r.height < 44; }).length,
        domContentLoadedMs: nav ? Math.round(nav.domContentLoadedEventEnd) : null,
      };
    });
    const firstControl = await ctl.evaluate((e) => (e.textContent || e.getAttribute('aria-label') || e.tagName).replace(/\s+/g, ' ').trim().slice(0, 60));
    await page.screenshot({ path: join(out, `shot-c1-${profileName}-landing.png`) });
    return { ttfiMs: round(ttfi), loadMs: round(loadMs), firstControl, ...info };
  }));

  return results;
}

function toMarkdown(report) {
  const L = [`# Scouting report — slice ${report.slice}`, '', `- Target: ${report.base}${report.live ? ' (live)' : ' (local)'}`, `- Timestamp: ${report.timestamp}`, `- Commit: ${report.commit ?? 'unknown'}`, `- WebKit probe: ${report.webkit.available ? 'available' : 'unavailable'}${report.webkit.note ? ' — ' + report.webkit.note : ''}`, ''];
  L.push('## TTFI (journey 3, direct landing)', '', '| Profile | TTFI ms | Load ms | First control | Overflow-x | Targets <44px |', '|---|---|---|---|---|---|');
  for (const r of report.results.filter((r) => r.journey === 'j3-direct')) L.push(`| ${r.profile} | ${r.ttfiMs ?? 'ERR'} | ${r.loadMs ?? ''} | ${r.firstControl ?? r.error ?? ''} | ${r.horizontalOverflow ?? ''} | ${r.smallTargets ?? ''} |`);
  L.push('', '## Discoverability (journeys 1-2)', '', '| Profile | Journey | Reached practice | Clicks | Path |', '|---|---|---|---|---|');
  for (const r of report.results.filter((r) => r.journey !== 'j3-direct')) L.push(`| ${r.profile} | ${r.journey} | ${r.reached ?? 'ERR'} | ${r.clicks ?? ''} | ${(r.path ?? []).join(' → ') || r.error || r.note || '—'} |`);
  L.push('', '## Trace files', '', ...report.results.map((r) => `- ${r.trace}`), '');
  return L.join('\n');
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) return void process.stdout.write(HELP);
  if (!args.slice || !SLICES.includes(args.slice.toUpperCase())) throw new Error(`--slice required (${SLICES.join(', ')})`);
  if (!args.out) throw new Error('--out <dir> required');
  const slice = args.slice.toUpperCase();
  const out = resolve(args.out);
  await mkdir(out, { recursive: true });
  const base = args.base || (args.live ? LIVE_URL : LOCAL_URL);
  const names = args.profile ? args.profile.split(',') : DEFAULT_PROFILES;
  for (const n of names) if (!PROFILES[n]) throw new Error(`Unknown profile: ${n}`);

  if (slice !== 'C1') {
    await writeFile(join(out, `report-${slice.toLowerCase()}.md`), `# Slice ${slice}\n\nNot implemented yet (stub).\n`);
    console.log(`Slice ${slice} is a stub; wrote placeholder report.`);
    return;
  }

  const wk = { available: false };
  try { const b = await webkit.launch(); wk.available = true; await b.close(); } catch (e) { wk.note = String(e).split('\n')[0].slice(0, 160); }

  const browser = await chromium.launch();
  const results = [];
  try {
    for (const n of names) results.push(...(await slice1(browser, n, base, out)));
  } finally {
    await browser.close();
  }
  let commit = process.env.SCOUT_COMMIT || null;
  const report = { slice, base, live: !!args.live, timestamp: new Date().toISOString(), commit, webkit: wk, results };
  await writeFile(join(out, `report-${slice.toLowerCase()}.json`), JSON.stringify(report, null, 2));
  await writeFile(join(out, `report-${slice.toLowerCase()}.md`), toMarkdown(report));
  console.log(toMarkdown(report));
}

main().catch((e) => { console.error(e.message); process.exit(1); });
