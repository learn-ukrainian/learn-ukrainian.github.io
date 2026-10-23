import { AxeBuilder } from '@axe-core/playwright';
import { expect, test, type Page, type TestInfo } from '@playwright/test';

/**
 * #10180 — historical-context source label and warning pill stay readable.
 *
 * Renders real Atlas client-shell routes in Chromium (no injected DOM) and checks
 * the two affected text styles inside `.def-card.soviet-colonization-box`:
 *   1. the source label (`.def-source` text next to the pill), and
 *   2. the warning pill (`.src-pill`).
 * Ratios are WCAG 2.2 SC 1.4.3 contrast computed unrounded from the browser's
 * computed foreground and the effective (alpha-composited) background; the
 * threshold is 4.5:1 because both styles are small, non-bold-large text.
 *
 * Routes: `сапати` (the route in the R5-N1 finding) and `спірний`, picked as
 * index sha256("atlas-10180-second-route") mod 55 of the curated heteronym routes
 * that are public Atlas articles with historical context on every heteronym.
 * `вода` is the non-historical control. No axe rule is disabled or excluded; axe
 * is scoped to the affected box only.
 */

const MIN_RATIO = 4.5;
const HISTORICAL_ROUTES = ['сапати', 'спірний'];
const CONTROL_ROUTE = 'вода';
const THEMES = ['light', 'dark'] as const;
const VIEWPORTS = [
  { name: 'desktop', width: 1280, height: 800 },
  { name: 'phone', width: 390, height: 844 },
];
const BOX = '.def-card.soviet-colonization-box';

type Rgba = [number, number, number, number];

function parseColor(value: string): Rgba {
  const match = /^rgba?\(([^)]+)\)$/.exec(value.trim());
  if (!match) throw new Error(`unparseable computed color: ${value}`);
  const parts = match[1].split(/[\s,/]+/).filter(Boolean).map(Number);
  if (parts.length < 3 || parts.some(Number.isNaN)) throw new Error(`unparseable computed color: ${value}`);
  return [parts[0], parts[1], parts[2], parts[3] ?? 1];
}

function over(top: Rgba, bottom: Rgba): Rgba {
  const alpha = top[3] + bottom[3] * (1 - top[3]);
  if (alpha === 0) return [0, 0, 0, 0];
  const mix = (i: number) => (top[i] * top[3] + bottom[i] * bottom[3] * (1 - top[3])) / alpha;
  return [mix(0), mix(1), mix(2), alpha];
}

function luminance([r, g, b]: Rgba): number {
  const lin = (c: number) => {
    const s = c / 255;
    return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
}

function contrast(fg: Rgba, bg: Rgba): number {
  const a = luminance(over(fg, bg));
  const b = luminance(bg);
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}

/** Computed text color plus the alpha-composited backgrounds of the element's ancestor chain. */
async function readStyle(page: Page, selector: string) {
  const raw = await page.locator(selector).first().evaluate((el) => {
    const layers: string[] = [];
    for (let node: Element | null = el; node; node = node.parentElement) {
      layers.push(getComputedStyle(node).backgroundColor);
    }
    const style = getComputedStyle(el);
    return {
      color: style.color,
      layers,
      fontSize: style.fontSize,
      fontWeight: style.fontWeight,
      text: (el.textContent ?? '').trim(),
    };
  });
  let background: Rgba | null = null;
  for (const layer of raw.layers) {
    const color = parseColor(layer);
    background = background ? over(background, color) : color;
    if (color[3] === 1) break;
  }
  if (!background || background[3] !== 1) throw new Error(`no opaque background behind ${selector}`);
  const fg = parseColor(raw.color);
  return { ...raw, fg, background, ratio: contrast(fg, background) };
}

function watchErrors(page: Page, origin: string, routeUrl: string) {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(`pageerror: ${error.message}`));
  page.on('console', (msg) => {
    // Chromium also logs the expected 404 of the shell-carrier navigation document itself.
    if (msg.type() === 'error' && msg.location().url !== routeUrl) errors.push(`console.error: ${msg.text()} (${msg.location().url})`);
  });
  page.on('requestfailed', (request) => errors.push(`requestfailed: ${request.url()} ${request.failure()?.errorText}`));
  page.on('response', (response) => {
    const url = response.url();
    // `astro preview` answers an unprebuilt word route with 404.html (the client shell);
    // that single navigation document is the expected carrier, every other 4xx/5xx is not.
    if (response.status() >= 400 && !(url === routeUrl && response.request().isNavigationRequest())) {
      errors.push(`http ${response.status()}: ${url.replace(origin, '')}`);
    }
  });
  return errors;
}

async function openRoute(page: Page, slug: string, theme: string) {
  await page.addInitScript((t) => {
    window.localStorage.setItem('lu-theme', t);
    document.documentElement?.setAttribute('data-theme', t);
  }, theme);
  await page.goto(`/lexicon/${encodeURIComponent(slug)}/`);
  await expect(page.locator('.word-switch')).toBeVisible();
  await page.evaluate((t) => document.documentElement.setAttribute('data-theme', t), theme);
}

async function auditBox(page: Page, testInfo: TestInfo, label: string, panel: string) {
  const box = page.locator(`${panel} ${BOX}`);
  await expect(box).toBeVisible();
  await box.scrollIntoViewIfNeeded();
  const shot = testInfo.outputPath(`${label}.png`);
  await box.screenshot({ path: shot });
  await testInfo.attach(`${label}.png`, { path: shot, contentType: 'image/png' });

  const labelStyle = await readStyle(page, `${panel} ${BOX} .def-source > span:not(.src-pill)`);
  const pillStyle = await readStyle(page, `${panel} ${BOX} .def-source .src-pill`);
  expect(pillStyle.text, 'warning pill text is preserved').toBe('Радянський окупаційний контекст');
  expect(labelStyle.text.length, 'source label text is preserved').toBeGreaterThan(0);

  const axe = await new AxeBuilder({ page }).include(`${panel} ${BOX}`).analyze();
  const blocking = axe.violations.filter((v) => ['serious', 'critical'].includes(v.impact ?? ''));

  const evidence = {
    label,
    sourceLabel: { text: labelStyle.text, fg: labelStyle.fg, bg: labelStyle.background, ratio: labelStyle.ratio },
    warningPill: { text: pillStyle.text, fg: pillStyle.fg, bg: pillStyle.background, ratio: pillStyle.ratio },
    axeViolations: axe.violations.map((v) => `${v.id}[${v.impact}]x${v.nodes.length}`),
  };
  console.log(`evidence ${JSON.stringify(evidence)}`);
  await testInfo.attach(`${label}.json`, { body: JSON.stringify(evidence, null, 2), contentType: 'application/json' });

  expect.soft(labelStyle.ratio, `source label contrast ${labelStyle.ratio} (${label})`).toBeGreaterThanOrEqual(MIN_RATIO);
  expect.soft(pillStyle.ratio, `warning pill contrast ${pillStyle.ratio} (${label})`).toBeGreaterThanOrEqual(MIN_RATIO);
  expect.soft(blocking.map((v) => v.id), `axe serious/critical in ${label}`).toEqual([]);
}

for (const slug of HISTORICAL_ROUTES) {
  for (const theme of THEMES) {
    for (const viewport of VIEWPORTS) {
      test(`historical context: ${slug} [${theme}, ${viewport.name} ${viewport.width}px]`, async ({ page, baseURL }, testInfo) => {
        await page.setViewportSize({ width: viewport.width, height: viewport.height });
        const routeUrl = `${baseURL}/lexicon/${encodeURIComponent(slug)}/`;
        const errors = watchErrors(page, baseURL ?? '', routeUrl);
        await openRoute(page, slug, theme);

        const tabs = page.locator('[role="tab"][data-heteronym-target]');
        await expect(tabs).toHaveCount(2);
        const name = `${slug}-${theme}-${viewport.name}`;

        await expect(page.locator('#heteronym-panel-0')).toBeVisible();
        await auditBox(page, testInfo, `${name}-panel0`, '#heteronym-panel-0');

        // Keyboard: ArrowRight moves selection + focus to the second heteronym panel, ArrowLeft returns.
        await tabs.first().focus();
        await page.keyboard.press('ArrowRight');
        await expect(tabs.nth(1)).toHaveAttribute('aria-selected', 'true');
        await expect(tabs.nth(1)).toBeFocused();
        await expect(page.locator('#heteronym-panel-1')).toBeVisible();
        await expect(page.locator('#heteronym-panel-0')).toBeHidden();
        await auditBox(page, testInfo, `${name}-panel1`, '#heteronym-panel-1');

        await page.keyboard.press('ArrowLeft');
        await expect(tabs.first()).toHaveAttribute('aria-selected', 'true');
        await expect(page.locator('#heteronym-panel-0')).toBeVisible();

        expect(errors, 'page/console/request errors').toEqual([]);
      });
    }
  }
}

for (const theme of THEMES) {
  for (const viewport of VIEWPORTS) {
    test(`control: ${CONTROL_ROUTE} [${theme}, ${viewport.name} ${viewport.width}px]`, async ({ page, baseURL }, testInfo) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      const routeUrl = `${baseURL}/lexicon/${encodeURIComponent(CONTROL_ROUTE)}/`;
      const errors = watchErrors(page, baseURL ?? '', routeUrl);
      await openRoute(page, CONTROL_ROUTE, theme);

      await expect(page.locator(BOX)).toHaveCount(0);
      const source = page.locator('.def-card:not(.soviet-colonization-box) .def-source').first();
      await expect(source).toBeVisible();
      // The shared `.def-source` style is untouched outside the historical box.
      const muted = await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--lu-text-muted').trim());
      const probe = await page.evaluate((value) => {
        const el = document.createElement('i');
        el.style.color = value;
        document.body.append(el);
        const color = getComputedStyle(el).color;
        el.remove();
        return color;
      }, muted);
      expect(await source.evaluate((el) => getComputedStyle(el).color)).toBe(probe);

      const style = await readStyle(page, '.def-card:not(.soviet-colonization-box) .def-source');
      const shot = testInfo.outputPath(`control-${theme}-${viewport.name}.png`);
      await source.screenshot({ path: shot });
      await testInfo.attach(`control-${theme}-${viewport.name}.png`, { path: shot, contentType: 'image/png' });
      console.log(`evidence control ${theme} ${viewport.name} ratio=${style.ratio}`);
      expect(style.ratio, `control .def-source contrast ${style.ratio}`).toBeGreaterThanOrEqual(MIN_RATIO);
      expect(errors, 'page/console/request errors').toEqual([]);
    });
  }
}
