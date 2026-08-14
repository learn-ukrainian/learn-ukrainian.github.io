import { AxeBuilder } from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

/**
 * #5376 check 4 — axe-core accessibility scan.
 *
 * Policy: the practice and Atlas surfaces must have ZERO axe violations at
 * impact serious or critical, in both color themes. Moderate/minor findings
 * are logged but do not fail the gate.
 *
 * This gate is fail-closed on every axe rule: the two pre-existing
 * suppressions (color-contrast on the practice dashboard, definition-list on
 * /lexicon/) were removed when the product fixes for #6814 and #6815 landed.
 * Do not re-add rule disables or selector exclusions — fix the artifact.
 */

const SURFACES = [
  { path: '/words-of-the-day/practice/', waitForPractice: true },
  { path: '/lexicon/', waitForPractice: false },
];

const FAIL_IMPACTS = new Set(['serious', 'critical']);

for (const surface of SURFACES) {
  for (const theme of ['light', 'dark'] as const) {
    test(`axe: ${surface.path} [${theme}] has no serious/critical violations`, async ({ page }) => {
      await page.addInitScript((t) => {
        window.localStorage.setItem('lu-theme', t);
        document.documentElement.setAttribute('data-theme', t);
      }, theme);
      await page.goto(surface.path);
      if (surface.waitForPractice) {
        await expect(page.locator('#lexicon-practice-mount .lexicon-practice')).toBeVisible();
      }
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
      expect(failing.length, `axe serious/critical violations on ${surface.path} [${theme}]:\n${message}`).toBe(0);
    });
  }
}
