import { AxeBuilder } from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

/**
 * #5376 check 4 / #8736 — axe-core accessibility scan.
 *
 * Policy: the representative public learner routes must have ZERO axe
 * violations at impact serious or critical, in both color themes and at a
 * desktop and a 390px mobile viewport. Moderate/minor findings are logged but
 * do not fail the gate.
 *
 * This gate is fail-closed on every axe rule: do not add rule disables or
 * selector exclusions — fix the artifact. `ready` waits for the component that
 * used to carry the violation (lesson fill-in selects, daily cards, ...) so a
 * route cannot pass because that component had not rendered yet.
 */

const SURFACES = [
  { path: '/', ready: 'main' },
  { path: '/a1/', ready: 'main' },
  { path: '/a1-v1/what-time/', ready: '[data-activity="fillin-row"] select' },
  { path: '/a2/dative-nouns/', ready: '[data-activity="fillin-row"] select' },
  { path: '/folk/charivni-kazky/', ready: 'main' },
  { path: '/readings/', ready: 'main' },
  { path: '/words-of-the-day/', ready: '[data-daily-card]' },
  { path: '/practice/', ready: '#lexicon-practice-mount .lexicon-practice' },
  { path: '/lexicon/', ready: 'main' },
  { path: '/lexicon/browse/', ready: 'main' },
];

const VIEWPORTS = {
  desktop: { width: 1280, height: 720 },
  mobile: { width: 390, height: 844 },
} as const;

const FAIL_IMPACTS = new Set(['serious', 'critical']);

for (const surface of SURFACES) {
  for (const [viewportName, viewport] of Object.entries(VIEWPORTS)) {
    for (const theme of ['light', 'dark'] as const) {
      test(`axe: ${surface.path} [${theme}, ${viewportName}] has no serious/critical violations`, async ({ page }) => {
        await page.setViewportSize(viewport);
        await page.addInitScript((t) => {
          window.localStorage.setItem('lu-theme', t);
          document.documentElement.setAttribute('data-theme', t);
        }, theme);
        await page.goto(surface.path);
        await expect(page.locator(surface.ready).first()).toBeVisible();
        await page.evaluate((t) => document.documentElement.setAttribute('data-theme', t), theme);

        const results = await new AxeBuilder({ page }).analyze();

        const failing = results.violations.filter((v) => FAIL_IMPACTS.has(v.impact ?? ''));
        const advisory = results.violations.filter((v) => !FAIL_IMPACTS.has(v.impact ?? ''));
        if (advisory.length > 0) {
          console.log(
            `axe advisory (moderate/minor, non-failing): ${advisory
              .map((v) => `${v.id}(${v.impact})×${v.nodes.length}`)
              .join(', ')}`,
          );
        }

        const message = failing
          .map(
            (v) =>
              `${v.id} [${v.impact}] ${v.help} — ${v.helpUrl}\n` +
              v.nodes.map((n) => `  ${n.target.join(' ')}: ${n.failureSummary?.split('\n')[0]}`).join('\n'),
          )
          .join('\n');
        expect(
          failing.length,
          `axe serious/critical violations on ${surface.path} [${theme}, ${viewportName}]:\n${message}`,
        ).toBe(0);
      });
    }
  }
}
