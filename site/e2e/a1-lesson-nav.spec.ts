import type { Page } from '@playwright/test';
import { test } from './support/hardened-browser.mjs';
import { mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const SHOT_DIR = join(dirname(fileURLToPath(import.meta.url)), '../../test-results/a1-qa');

async function setTheme(page: Page, theme: 'light' | 'dark') {
  await page.addInitScript((t) => {
    window.localStorage.setItem('lu-theme', t);
    document.documentElement.setAttribute('data-theme', t);
  }, theme);
}

test.describe('A1 upgrade screenshots', () => {
  for (const theme of ['light', 'dark'] as const) {
    for (const path of [
      '/a1/',
      '/a1/things-have-gender/',
    ]) {
      test(`${theme} ${path}`, async ({ page }) => {
        await setTheme(page, theme);
        await page.goto(path);
        await page.evaluate((t) => document.documentElement.setAttribute('data-theme', t), theme);
        mkdirSync(SHOT_DIR, { recursive: true });
        const slug = path.replace(/\//g, '_').replace(/^_|_$/g, '') || 'home';
        await page.screenshot({
          path: join(SHOT_DIR, `${theme}-${slug}.png`),
          fullPage: true,
        });
      });
    }
  }
});
