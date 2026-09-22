#!/usr/bin/env node
// Practice Hub scouting harness (#8317). Standalone: NOT a Playwright test
// (no *.spec.ts), so `playwright test` never picks it up.
import { chromium, webkit, devices } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { checkProgress, evaluateSession } from './invariants.mjs';

const LIVE_URL = 'https://learn-ukrainian.github.io';
const LOCAL_URL = 'http://127.0.0.1:4321';
const PRACTICE = '/practice/';
const SLICES = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8'];
const PROFILES = {
  desktop: { label: 'Desktop Chrome', options: { ...devices['Desktop Chrome'] } },
  phone: { label: 'iPhone 14 (Chromium emulation)', options: { ...devices['iPhone 14'], hasTouch: true }, engine: 'chromium' },
  android: { label: 'Pixel 7', options: { ...devices['Pixel 7'], hasTouch: true } },
  fast: { label: 'Fast desktop (1440x900, no throttle)', options: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
  explorer: { label: 'Explorer (Desktop, prefers-reduced-motion)', options: { ...devices['Desktop Chrome'], reducedMotion: 'reduce' } },
};
const DEFAULT_PROFILES = ['desktop', 'phone', 'android'];
const DETECT_BUDGETS = [10, 20];
const DEFAULT_DETECT_BUDGET = 20;

const HELP = `Practice Hub scouting harness (#8317)

Usage: node e2e/scouting/run.mjs --slice <id> --out <dir> [options]

  --help                  Show this help
  --slice <id>            Slice id: ${SLICES.join(', ')} (C1 discoverability+session+TTFI; C2-C8 scripted journeys)
  --detect                Detector (#8477): play one A1 Flashcards session and exit 1 when it breaks a rule
                          (progress string sequence, pageerror, pronunciation clip). Slices never set the exit code.
  --budget <n>            Session budget the detector clicks: ${DETECT_BUDGETS.join(' | ')} (default ${DEFAULT_DETECT_BUDGET}; --detect only)
  --out <dir>             Output directory for report, screenshots and timestamped trace zips
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
    else if (k === '--detect') a.detect = true;
    else if (['--slice', '--out', '--profile', '--base', '--budget'].includes(k)) {
      const v = argv[++i];
      if (v === undefined || v.startsWith('--')) throw new Error(`${k} needs a value`);
      a[k.slice(2)] = v;
    } else throw new Error(`Unknown argument: ${k}`);
  }
  return a;
}


const now = () => performance.now();
const round = (n) => (n == null ? null : Math.round(n));

// Immutable artifacts: every file carries the run timestamp, so reruns never overwrite.
const RUN_ID = new Date().toISOString().replace(/[:.]/g, '-');
const stem = (slice, profile, name) => `${RUN_ID}-${slice.toLowerCase()}-${profile}-${name}`;

async function withJourney(browser, profileName, slice, name, base, out, fn) {
  const prof = PROFILES[profileName];
  const { defaultBrowserType, ...ctxOptions } = prof.options; // fresh context = clean storage
  const context = await browser.newContext({ ...ctxOptions, baseURL: base, serviceWorkers: 'block' });
  await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
  const page = await context.newPage();
  const errors = [];
  const pageErrors = [];
  const failed = [];
  page.on('pageerror', (e) => { errors.push(String(e)); pageErrors.push(String(e)); });
  page.on('console', (m) => m.type() === 'error' && errors.push(m.text()));
  page.on('response', (r) => r.status() >= 400 && failed.push(`${r.status()} ${r.url()}`));
  const shot = async (label) => {
    const path = join(out, `${stem(slice, profileName, name)}-${label}.png`);
    await page.screenshot({ path });
    return path;
  };
  let result;
  try {
    result = await fn(page, shot);
  } catch (e) {
    result = { error: String(e).split('\n').slice(0, 3).join(' ').slice(0, 300) };
  }
  const tracePath = join(out, `${stem(slice, profileName, name)}.zip`);
  await context.tracing.stop({ path: tracePath });
  await context.close();
  return { journey: name, profile: profileName, trace: tracePath, consoleErrors: errors.slice(0, 5), pageErrors: pageErrors.slice(0, 5), failedRequests: [...new Set(failed)].slice(0, 8), ...result };
}

// Practice-ish links inside `scope` (a CSS selector, default whole document).
const PRACTICE_RE = /practi[cs]e|drill|exercise|quiz|практик|вправ/i;
async function findPracticeLinks(page, scope = 'body') {
  return page.evaluate(({ src, scope }) => {
    const re = new RegExp(src, 'i');
    const vis = (el) => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden'; };
    return [...document.querySelectorAll(scope)].flatMap((root) => [...root.querySelectorAll('a[href], button, summary')])
      .filter((el) => re.test((el.textContent || '') + ' ' + (el.getAttribute('href') || '')))
      .map((el) => ({ text: (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 60), href: el.getAttribute('href'), visible: vis(el) }));
  }, { src: PRACTICE_RE.source, scope });
}

// The Practice Hub itself (NOT other "practice" pages such as /b1/practice-exam/).
const TARGET = '/practice';
const isTarget = (href) => !!href && new URL(href, 'https://x.invalid/').pathname.replace(/\/$/, '') === TARGET;

// Click a link and wait until the browser has actually arrived, so the trace covers the hub.
async function clickAndArrive(page, locator, arrive) {
  await locator.click();
  await page.waitForURL((u) => arrive(u.pathname), { timeout: 15000 });
  await page.waitForLoadState('domcontentloaded');
}
const arrivedHub = (p) => p.replace(/\/$/, '') === TARGET;

// Click path to the hub starting inside `scope`: direct link (1 click), else via a parent page (2 clicks).
async function clicksToPractice(page, scope = 'body') {
  const direct = async (sc) => (await findPracticeLinks(page, sc)).find((l) => l.visible && isTarget(l.href));
  let hit = await direct(scope);
  if (hit) {
    await clickAndArrive(page, page.locator(`${scope} a[href="${hit.href}"]:visible`).first(), arrivedHub);
    return { reached: true, clicks: 1, path: [`${hit.text} -> ${hit.href}`] };
  }
  const start = page.url();
  for (const parent of ['/words-of-the-day/', '/lexicon/']) {
    const link = page.locator(`${scope} a[href="${parent}"]:visible`).first();
    if (!(await link.count())) continue;
    await clickAndArrive(page, link, (p) => p === parent);
    hit = await direct('body');
    if (hit) {
      await clickAndArrive(page, page.locator(`a[href="${hit.href}"]:visible`).first(), arrivedHub);
      return { reached: true, clicks: 2, path: [`${scope} -> ${parent}`, `${hit.text} -> ${hit.href}`] };
    }
    await page.goto(start, { waitUntil: 'domcontentloaded' });
  }
  return { reached: false, clicks: null, path: [] };
}

// --- C1 -------------------------------------------------------------------------------
async function entryJourney(page, url, scope, prep) {
  await page.goto(url, { waitUntil: 'load' });
  if (prep) { if (!(await prep(page))) return { reached: null, clicks: null, path: [], note: 'n/a: control not present at this viewport' }; }
  const links = await findPracticeLinks(page, scope);
  const found = await clicksToPractice(page, scope);
  return { start: url, scope, practiceLinksInScope: links.filter((l) => l.visible).length, ...found };
}

async function openHubReady(page) {
  await page.goto(PRACTICE, { waitUntil: 'load' });
  await page.locator('button[data-mode]').first().waitFor({ state: 'visible', timeout: 20000 });
}

// Pronunciation instrumentation (#8477): count browser-voice calls and clip plays in-page,
// and watch the network for the manifest and clip requests. Installed before navigation.
const AUDIO_PATH = '/audio/pronunciation/';
const AUDIO_INIT_SCRIPT = () => {
  const log = { speak: 0, plays: [] };
  window.__scoutAudio = log;
  const synth = window.SpeechSynthesis && window.SpeechSynthesis.prototype;
  if (synth && synth.speak) {
    const speak = synth.speak;
    synth.speak = function (u) { log.speak += 1; return speak.call(this, u); };
  }
  const play = HTMLMediaElement.prototype.play;
  HTMLMediaElement.prototype.play = function () {
    const entry = { src: this.currentSrc || this.src || '', rejected: null };
    log.plays.push(entry);
    const p = play.call(this);
    if (p && p.catch) p.then(() => { entry.rejected = false; }, (e) => { entry.rejected = String(e && e.name || e); });
    return p;
  };
};
async function watchPronunciation(page) {
  const net = { manifestStatus: null, clips: [] };
  const onResponse = (r) => {
    const url = new URL(r.url());
    if (!url.pathname.includes(AUDIO_PATH)) return;
    if (url.pathname.endsWith('/manifest.json')) net.manifestStatus = r.status();
    else net.clips.push({ path: url.pathname, status: r.status() });
  };
  const onFailed = (rq) => {
    const url = new URL(rq.url());
    if (url.pathname.includes(AUDIO_PATH) && !url.pathname.endsWith('/manifest.json')) net.clips.push({ path: url.pathname, status: 0 });
  };
  page.on('response', onResponse);
  page.on('requestfailed', onFailed);
  await page.addInitScript(AUDIO_INIT_SCRIPT);
  return net;
}

// Press the pronunciation control on the current flashcard once and report what spoke.
// 'absent' = the card has no control; 'hidden' = the control never became visible (no clip, `hide` fallback).
async function pressPronunciation(page, net) {
  const root = page.locator('[data-activity="flashcard"] [data-pronunciation-lemma], .flashcard-pronunciation [data-pronunciation-lemma]').first();
  const snapshot = async (control) => {
    const log = await page.evaluate(() => window.__scoutAudio ?? { speak: 0, plays: [] });
    const lemma = control === 'absent' ? null : await root.getAttribute('data-pronunciation-lemma').catch(() => null);
    return { control, lemma, manifestStatus: net.manifestStatus, clips: [...net.clips], speakCalls: log.speak, mediaPlays: log.plays };
  };
  if (!(await root.count())) return snapshot('absent');
  const button = root.locator('button');
  const visible = await button.waitFor({ state: 'visible', timeout: 8000 }).then(() => true, () => false);
  if (!visible) return snapshot('hidden');
  await button.click();
  // Give the clip request and play() a moment; nothing here waits on audio actually finishing.
  await page.waitForFunction(() => (window.__scoutAudio?.plays.length ?? 0) > 0 || (window.__scoutAudio?.speak ?? 0) > 0, null, { timeout: 3000 }).catch(() => {});
  await page.waitForTimeout(500);
  const result = await snapshot('pressed');
  result.statusText = ((await root.locator('[role="status"]').textContent().catch(() => '')) || '').trim();
  return result;
}

// Read the progress pill; when `previous` is given, wait (bounded) for it to change first.
const PROGRESS_SEL = '[data-testid="practice-session-progress"]';
async function readProgress(page, previous = null) {
  if (previous !== null) {
    await page.waitForFunction((prev) => (document.querySelector('[data-testid="practice-session-progress"]')?.textContent ?? '').trim() !== prev, previous, { timeout: 3000 }).catch(() => {});
  }
  const text = await page.locator(PROGRESS_SEL).textContent({ timeout: 2000 }).catch(() => null);
  return text === null ? null : text.trim();
}

// Full first session: A1, Flashcards, `budget` cards, end screen. Records EVERY progress
// reading (start + after each answer) and presses the pronunciation control once (#8477).
// Slices only record these; `--detect` turns them into the exit code.
async function flashcardSession(page, shot, budget = 10) {
  const net = await watchPronunciation(page);
  await openHubReady(page);
  await page.locator('.k3-levels button', { hasText: /^A1$/ }).click();
  await page.getByTestId(`practice-session-budget-${budget}`).click();
  await page.locator('button[data-mode="flashcards"]').click();
  const summary = page.getByTestId('practice-session-summary');
  const answered = [];
  const progressReadings = [];
  let pronunciation = null; // first card whose control could be pressed; else the last observation
  let cardsWithoutControl = 0;
  await page.locator(PROGRESS_SEL).waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
  let progress = await readProgress(page);
  if (progress !== null) progressReadings.push(progress);
  for (let i = 0; i < budget + 2 && !(await summary.isVisible()); i++) {
    const card = page.locator('[data-activity="flashcard"]');
    await card.waitFor({ state: 'visible', timeout: 10000 });
    answered.push(((await card.textContent()) || '').replace(/\s+/g, ' ').trim().slice(0, 30));
    if (pronunciation?.control !== 'pressed') {
      pronunciation = await pressPronunciation(page, net);
      if (pronunciation.control !== 'pressed') cardsWithoutControl += 1;
    }
    await card.click(); // flip
    await page.locator('.rate-btn[data-rate="good"]').click(); // "Знаю"-equivalent; the counter moves here
    progress = await readProgress(page, progress);
    if (progress !== null) progressReadings.push(progress);
    await page.getByTestId('practice-advance-button').click(); // no auto-advance: «Далі» is required
    await page.waitForTimeout(300);
  }
  await summary.waitFor({ state: 'visible', timeout: 15000 });
  const shotPath = await shot('end-screen');
  return {
    budget,
    progressAtStart: progressReadings[0] ?? null,
    progressReadings,
    progressCheck: checkProgress({ budget, readings: progressReadings }),
    pronunciation,
    cardsWithoutControl,
    cardsAnswered: answered.length,
    endScreen: true,
    summaryText: ((await summary.textContent()) || '').replace(/\s+/g, ' ').trim().slice(0, 200),
    continueLinks: await page.getByTestId('practice-session-continue-links').locator('a,button').count(),
    endScreenShot: shotPath,
  };
}

async function landingTtfi(page, shot) {
  const t0 = now();
  await page.goto(PRACTICE, { waitUntil: 'commit' });
  // Navigation committed: measure load on the new document, independent of the enablement wait below.
  const loadPromise = page.waitForLoadState('load').then(() => now() - t0);
  loadPromise.catch(() => {});
  const ctl = page.locator('main button:visible, main a[href]:visible, main input:visible, main select:visible, main summary:visible').first();
  await ctl.waitFor({ state: 'visible', timeout: 20000 });
  const ttfc = now() - t0;
  // Visible is not interactive: also require the control to be enabled and record when.
  // Bounded wait; a control that never enables reports null, not the elapsed time.
  let firstControlEnabled = false;
  let ttfcEnabled = null;
  try {
    const handle = await ctl.elementHandle({ timeout: 5000 });
    if (handle) {
      await page.waitForFunction(
        (el) => el.isConnected && !el.disabled && !el.hasAttribute('disabled') && el.getAttribute('aria-disabled') !== 'true',
        handle,
        { timeout: 5000 },
      );
      firstControlEnabled = true;
      ttfcEnabled = now() - t0;
    }
  } catch {
    firstControlEnabled = false;
    ttfcEnabled = null;
  }
  const loadMs = await loadPromise;
  const info = await page.evaluate(() => {
    const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    return {
      h1: document.querySelector('h1')?.textContent?.trim() ?? null,
      modes: [...document.querySelectorAll('button[data-mode]')].filter(vis).map((b) => b.dataset.mode),
      dialogs: document.querySelectorAll('dialog[open], [role="dialog"]').length,
      horizontalOverflow: document.documentElement.scrollWidth > innerWidth + 1,
      smallTargets: [...document.querySelectorAll('main button, main a[href]')].filter(vis).filter((e) => { const r = e.getBoundingClientRect(); return r.width < 44 || r.height < 44; }).length,
    };
  });
  const firstControl = await ctl.evaluate((e) => (e.textContent || e.getAttribute('aria-label') || e.tagName).replace(/\s+/g, ' ').trim().slice(0, 60));
  return { timeToFirstVisibleControlMs: round(ttfc), firstControlEnabled, timeToEnabledControlMs: ttfcEnabled === null ? null : round(ttfcEnabled), loadMs: round(loadMs), firstControl, landingShot: await shot('landing'), ...info };
}

async function directPractice404(page, shot) {
  const resp = await page.goto('/practice/', { waitUntil: 'load' });
  return { requested: '/practice/', httpStatus: resp?.status() ?? null, finalUrl: page.url(), h1: await page.locator('h1').first().textContent().catch(() => null), shot: await shot('direct-practice') };
}

async function slice1(browser, profileName, base, out) {
  const J = (name, fn) => withJourney(browser, profileName, 'C1', name, base, out, fn);
  const results = [];
  results.push(await J('e1-home', (p) => entryJourney(p, '/', 'main')));
  results.push(await J('e2-header-nav', (p) => entryJourney(p, '/', 'header nav.lu-nav')));
  results.push(await J('e3-phone-menu', (p) => entryJourney(p, '/', 'details.lu-mobile-menu nav', async (pg) => {
    const sum = pg.locator('details.lu-mobile-menu > summary');
    if (!(await sum.isVisible())) return false;
    await sum.click();
    return true;
  })));
  results.push(await J('e4-footer', (p) => entryJourney(p, '/', 'footer.lu-footer')));
  results.push(await J('e5-words-of-the-day', (p) => entryJourney(p, '/words-of-the-day/', 'main')));
  results.push(await J('e6-word-page', (p) => entryJourney(p, '/lexicon/%D0%B2%D0%BE%D0%B4%D0%B0/', 'main')));
  results.push(await J('e6b-word-page-control', (p) => entryJourney(p, '/lexicon/%D0%BE%D1%84%D1%96%D1%81/', 'main')));
  results.push(await J('e6c-word-via-browse', async (page) => {
    await page.goto('/lexicon/browse/', { waitUntil: 'load' });
    await page.locator('[data-index-search]').fill('вода');
    const link = page.locator('.atlas-index-link', { hasText: 'вода' }).first();
    await link.waitFor({ state: 'visible', timeout: 10000 });
    const href = await link.getAttribute('href');
    const resp = await page.goto(href, { waitUntil: 'load' });
    const links = await findPracticeLinks(page, 'main');
    return { wordHref: href, httpStatus: resp?.status() ?? null, h1: await page.locator('h1').first().textContent().catch(() => null), practiceLinksInScope: links.filter((l) => l.visible).length, ...(await clicksToPractice(page, 'main')) };
  }));
  results.push(await J('e7-direct-practice-url', directPractice404));
  results.push(await J('s1-flashcards-a1-10', flashcardSession));
  results.push(await J('t1-landing-ttfi', landingTtfi));
  return results;
}

// --- C2-C8: scripted journeys ---------------------------------------------------------
// Exercise a mode: open it, record what rendered, attempt one real interaction, screenshot.
async function exerciseMode(page, mode, shot) {
  await openHubReady(page);
  const btn = page.locator(`button[data-mode="${mode}"]`).first();
  if (!(await btn.count())) return { mode, note: 'no mode button' };
  await btn.scrollIntoViewIfNeeded();
  const clicked = await btn.click({ timeout: 8000 }).then(() => true, () => false);
  if (!clicked) return { mode, note: 'mode button present but not clickable', disabled: await btn.isDisabled(), shot: await shot(`mode-${mode}-blocked`) };
  await page.waitForTimeout(1500);
  const state = await page.evaluate(() => {
    const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    return {
      testids: [...new Set([...document.querySelectorAll('[data-testid^="practice-"]')].filter(vis).map((e) => e.dataset.testid))].slice(0, 12),
      empty: [...document.querySelectorAll('[data-testid*="empty"]')].filter(vis).length > 0,
      horizontalOverflow: document.documentElement.scrollWidth > innerWidth + 1,
    };
  });
  let interaction = 'none';
  let selectionChanged = null;
  const flash = page.locator('[data-activity="flashcard"]');
  if (await flash.isVisible().catch(() => false)) {
    await flash.click(); await page.locator('.rate-btn[data-rate="good"]').click(); interaction = 'flip+rate';
  } else {
    const opt = page.locator([
      'button.mc-opt', '.lexicon-option-list button', '[data-activity="choice-option"]',
      'button.match-tile', 'button[data-activity^="match-"]', 'button[data-activity*="tile"]',
      '[data-activity^="match-"] button:visible',
      '.cloze-input', 'input[data-activity]', 'input.cloze-blank',
      'main [role="option"]:visible', 'main [data-activity] button:visible', 'main [data-testid$="-options"] button:visible',
    ].join(', ')).first();
    if (await opt.count()) {
      const kind = await opt.evaluate((e) => (e.matches('input,textarea') ? 'input' : e.matches('.match-tile,[data-activity^="match-"] button,button[data-activity^="match-"],button[data-activity*="tile"]') ? 'tile' : 'option'));
      const stateOf = (el) => el.evaluate((e) => `${e.className}|${e.getAttribute('aria-pressed')}|${e.getAttribute('aria-checked')}|${e.disabled}|${e.value ?? ''}`);
      const before = await stateOf(opt).catch(() => '');
      try {
        if (kind === 'input') await opt.fill('а', { timeout: 5000 });
        else await opt.click({ timeout: 5000 });
        await page.waitForTimeout(300);
        const after = await stateOf(opt).catch(() => 'detached');
        interaction = `${kind}-${kind === 'input' ? 'fill' : 'click'}`;
        selectionChanged = after !== before;
      } catch (err) {
        interaction = `click-failed: ${String(err.message).split('\n')[0]}`;
      }
    }
  }
  await page.waitForTimeout(400);
  return { mode, ...state, interaction, selectionChanged, shot: await shot(`mode-${mode}`) };
}

const modeSlice = (tag, modes, tab) => async (browser, profileName, base, out) => {
  const results = [];
  for (const mode of modes) {
    results.push(await withJourney(browser, profileName, tag, `mode-${mode}`, base, out, async (page, shot) => {
      const r = await exerciseMode(page, mode, shot);
      return { ...r, tab };
    }));
  }
  return results;
};

async function settingsJourney(page, shot) {
  await openHubReady(page);
  await page.getByTestId('practice-settings-toggle').click();
  const drawer = page.getByTestId('practice-settings-drawer');
  await drawer.waitFor({ state: 'visible', timeout: 10000 });
  const opened = await shot('drawer-open');
  const tools = page.getByTestId('practice-secondary-tools');
  if (await tools.count()) await tools.locator('summary').click().catch(() => {});
  await page.keyboard.press('Escape');
  const closedByEsc = await drawer.waitFor({ state: 'hidden', timeout: 3000 }).then(() => true, () => false);
  if (!closedByEsc) await page.getByTestId('settings-drawer-close').click({ timeout: 5000 }).catch(() => {});
  await page.getByTestId('practice-active-deck-chip').click();
  const deckOptions = await page.getByTestId('practice-active-deck-menu').locator('[role="option"]').count();
  await page.locator('.k3-levels button:not([disabled])').nth(1).click();
  return { drawerOpened: true, closedByEsc, deckOptions, levelSwitched: true, shot: opened };
}

const slice7 = async (browser, profileName, base, out) => [await withJourney(browser, profileName, 'C7', 'settings-deck-level', base, out, settingsJourney)];

// Phone pass: the essentials at phone viewport (defaults to phone profiles).
const slice8 = async (browser, profileName, base, out) => {
  const J = (name, fn) => withJourney(browser, profileName, 'C8', name, base, out, fn);
  return [
    await J('phone-session-a1-10', flashcardSession),
    await J('phone-landing', landingTtfi),
    await J('phone-settings', settingsJourney),
    await J('phone-mode-matching', (p, s) => exerciseMode(p, 'matching', s)),
  ];
};

const SLICE_RUNNERS = {
  C1: slice1,
  C2: modeSlice('C2', ['mixed', 'flashcards', 'matching', 'choice'], 'vocab'),
  C3: modeSlice('C3', ['cloze', 'synonym', 'paronym', 'heritage'], 'vocab'),
  C4: modeSlice('C4', ['paradigm', 'imperative'], 'grammar'),
  C5: modeSlice('C5', ['stress', 'classify'], 'grammar'),
  C6: modeSlice('C6', ['zno-stress', 'zno-paronym', 'zno-lexical-norm', 'zno-morphological-norm', 'zno-syntactic-norm', 'zno-orthography', 'zno-morphology', 'zno-syntax', 'zno-phonetics', 'culture-error-correction'], 'courses'),
  C7: slice7,
  C8: slice8,
};

// --- Detector (#8477) ------------------------------------------------------------------
// Same player as C1/C8 `s1-flashcards-a1-10`; the recorded observations become the exit code.
async function detectRun(browser, profileName, base, out, budget) {
  const result = await withJourney(browser, profileName, 'DETECT', `d1-flashcards-a1-${budget}`, base, out, (page, shot) => flashcardSession(page, shot, budget));
  const verdict = evaluateSession({ budget, readings: result.progressReadings ?? [], pageErrors: result.pageErrors ?? [], pronunciation: result.pronunciation, error: result.error ?? null });
  return { ...result, verdict };
}

function toMarkdown(report) {
  const L = [`# Scouting report — ${report.slice === 'DETECT' ? 'detector' : 'slice ' + report.slice}`, '', `- Target: ${report.base}${report.live ? ' (live)' : ' (local)'}`, `- Timestamp: ${report.timestamp}`, `- Commit: ${report.commit ?? 'unknown'}`, `- WebKit probe: ${report.webkit.available ? 'available' : 'unavailable'}${report.webkit.note ? ' — ' + report.webkit.note : ''}`, ''];
  if (report.verdict) {
    L.push(`## Verdict: ${report.verdict.ok ? 'PASS' : 'FAIL'}`, '', ...(report.verdict.ok ? ['- every rule held'] : report.verdict.violations.map((v) => `- ${v}`)), '');
  }
  L.push('## Journeys', '', '| Profile | Journey | Outcome | Errors |', '|---|---|---|---|');
  const cell = (v) => String(v ?? '').replace(/\\/g, '\\\\').replace(/\|/g, '\\|');
  for (const r of report.results) {
    const { journey, profile, trace, consoleErrors, pageErrors, failedRequests, error, verdict, ...rest } = r;
    const outcome = error ? `ERROR: ${error}` : JSON.stringify(rest);
    L.push(`| ${profile} | ${journey} | ${cell(outcome)} | ${cell([...(consoleErrors ?? []), ...(failedRequests ?? [])].join('; '))} |`);
  }
  L.push('', '## Trace files', '', ...report.results.map((r) => `- ${r.trace}`), '');
  return L.join('\n');
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) return void process.stdout.write(HELP);
  if (args.detect && args.slice) throw new Error('--detect and --slice are exclusive');
  if (!args.detect && (!args.slice || !SLICES.includes(args.slice.toUpperCase()))) throw new Error(`--slice required (${SLICES.join(', ')}) or --detect`);
  if (!args.out) throw new Error('--out <dir> required');
  const budget = args.budget === undefined ? DEFAULT_DETECT_BUDGET : Number(args.budget);
  if (args.budget !== undefined && !args.detect) throw new Error('--budget only applies to --detect');
  if (!DETECT_BUDGETS.includes(budget)) throw new Error(`--budget must be one of ${DETECT_BUDGETS.join(', ')}`);
  const slice = args.detect ? 'DETECT' : args.slice.toUpperCase();
  const out = resolve(args.out);
  await mkdir(out, { recursive: true });
  const base = args.base || (args.live ? LIVE_URL : LOCAL_URL);
  const names = args.profile ? args.profile.split(',') : args.detect ? ['desktop'] : slice === 'C8' ? ['phone', 'android'] : DEFAULT_PROFILES;
  for (const n of names) if (!PROFILES[n]) throw new Error(`Unknown profile: ${n}`);

  const wk = { available: false };
  try { const b = await webkit.launch(); wk.available = true; await b.close(); } catch (e) { wk.note = String(e).split('\n')[0].slice(0, 160); }

  const browser = await chromium.launch();
  const results = [];
  try {
    for (const n of names) {
      if (args.detect) results.push(await detectRun(browser, n, base, out, budget));
      else results.push(...(await SLICE_RUNNERS[slice](browser, n, base, out)));
    }
  } finally {
    await browser.close();
  }
  let commit = process.env.SCOUT_COMMIT || null;
  // Detector: one verdict across profiles; any failing profile fails the process. Slices never do.
  const verdict = args.detect ? { ok: results.every((r) => r.verdict.ok), violations: results.flatMap((r) => r.verdict.violations.map((v) => `[${r.profile}] ${v}`)) } : undefined;
  const report = { slice, base, live: !!args.live, timestamp: new Date().toISOString(), commit, webkit: wk, ...(verdict ? { budget, verdict } : {}), results };
  await writeFile(join(out, `${RUN_ID}-report-${slice.toLowerCase()}.json`), JSON.stringify(report, null, 2));
  await writeFile(join(out, `${RUN_ID}-report-${slice.toLowerCase()}.md`), toMarkdown(report));
  console.log(toMarkdown(report));
  if (verdict && !verdict.ok) process.exitCode = 1;
}

main().catch((e) => { console.error(e.message); process.exit(1); });
