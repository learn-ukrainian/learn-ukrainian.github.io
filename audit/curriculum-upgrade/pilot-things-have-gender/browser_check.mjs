// Browser proof for the rendered pilot page. Run from the worktree root:
//   node audit/curriculum-upgrade/pilot-things-have-gender/browser_check.mjs
// Uses site/node_modules/playwright. If chromium is missing: npx --prefix site playwright install chromium
// Asserts (not discovers): screens module + l1 + l2 + l3; each lesson screen has exactly four tabs;
// clicking a tab shows exactly that panel; every panel has >= 40 words at 1200px and no horizontal
// overflow at 400px; no page or console errors. Screenshots go to an UNTRACKED folder.
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import fs from 'node:fs';
import path from 'node:path';

const require = createRequire(path.resolve('site/package.json'));
const { chromium } = require('playwright');

const file = path.resolve('docs/poc/poc-lesson-split-things-have-gender.html');
const outDir = path.resolve('audit/curriculum-upgrade/pilot-things-have-gender/screens');
fs.mkdirSync(outDir, { recursive: true });

const REQUIRED_SCREENS = ['module', 'l1', 'l2', 'l3'];
const failures = [];
const errors = [];
const results = [];

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1200, height: 900 } });
page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`));
page.on('console', (m) => { if (m.type() === 'error') errors.push(`console: ${m.text()}`); });
await page.goto(pathToFileURL(file).href);

async function overflow() {
  return page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
}

async function checkScreen(s, mode) {
  const btn = page.locator(`.switch [data-screen="${s}"]`);
  if ((await btn.count()) !== 1) { failures.push(`${mode}: screen button ${s} missing`); return; }
  await btn.click();
  const section = page.locator(`#s-${s}`);
  if (!(await section.isVisible())) { failures.push(`${mode}: screen ${s} not visible after click`); return; }
  const tabs = section.locator('.tab[data-tab]');
  const n = await tabs.count();
  if (s === 'module') {
    const words = (await section.innerText()).split(/\s+/).filter(Boolean).length;
    results.push({ mode, screen: s, tab: '-', words, overflow: await overflow() });
    if (mode === 'desktop' && words < 40) failures.push(`${mode}: module screen thin (${words} words)`);
    if (mode === 'phone' && (await overflow())) failures.push(`${mode}: module screen overflows horizontally`);
    await page.screenshot({ path: path.join(outDir, `${mode}-${s}.png`), fullPage: true });
    return;
  }
  const expected = ['urok', 'slovnyk', 'vpravy', 'resursy'].map((t) => `${s}-${t}`);
  const ids = [];
  for (let i = 0; i < n; i++) ids.push(await tabs.nth(i).getAttribute('data-tab'));
  if (JSON.stringify(ids) !== JSON.stringify(expected)) failures.push(`${mode}: screen ${s} tabs ${JSON.stringify(ids)} != expected ${JSON.stringify(expected)}`);
  for (const id of expected) {
    const t = section.locator(`.tab[data-tab="${id}"]`);
    if ((await t.count()) !== 1) { failures.push(`${mode}: ${s} tab button ${id} missing`); continue; }
    await t.click();
    const panel = page.locator(`#${id}`);
    if ((await panel.count()) !== 1) { failures.push(`${mode}: ${s} panel #${id} missing`); continue; }
    const visible = await panel.isVisible();
    const visiblePanels = await section.locator('.tabc:visible').count();
    const visibleIds = await section.locator('.tabc:visible').evaluateAll((els) => els.map((e) => e.id));
    const words = visible ? (await panel.innerText()).split(/\s+/).filter(Boolean).length : 0;
    const activities = visible ? await panel.locator('.exercise').count() : 0;
    const ov = await overflow();
    results.push({ mode, screen: s, tab: id, visible, visiblePanels, words, activities, overflow: ov });
    if (!visible) failures.push(`${mode}: ${s}/${id} panel not visible after click`);
    if (visiblePanels !== 1 || visibleIds[0] !== id) failures.push(`${mode}: ${s}/${id} — visible panels ${JSON.stringify(visibleIds)}, expected [${id}]`);
    if (mode === 'desktop' && words < 40) failures.push(`${mode}: ${s}/${id} thin (${words} words)`);
    if (mode === 'phone' && ov) failures.push(`${mode}: ${s}/${id} overflows horizontally at 400px`);
    await page.screenshot({ path: path.join(outDir, `${mode}-${s}-${id}.png`), fullPage: true });
  }
}

for (const s of REQUIRED_SCREENS) await checkScreen(s, 'desktop');
await page.setViewportSize({ width: 400, height: 800 });
const phoneBtn = page.locator('#phoneBtn');
if ((await phoneBtn.count()) === 1) await phoneBtn.click();
for (const s of REQUIRED_SCREENS) await checkScreen(s, 'phone');
await browser.close();

console.log(JSON.stringify({ results, errors, failures }, null, 2));
const ok = errors.length === 0 && failures.length === 0;
console.log(`BROWSER_CHECK: ${ok ? 'PASS' : 'FAIL'} (errors=${errors.length}, failures=${failures.length})`);
process.exit(ok ? 0 : 1);
