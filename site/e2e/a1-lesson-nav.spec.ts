import { expect, test, type Page } from '@playwright/test';
import { mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

/**
 * Learner-path QA for the A1 upgrade edition.
 * Encodes the operator's sidebar contract:
 * - /a1/ lists modules in the left bar
 * - a module landing and its lessons list only that module's lessons (not the module as item 08)
 */

const SHOT_DIR = join(dirname(fileURLToPath(import.meta.url)), '../../test-results/a1-qa');

async function setTheme(page: Page, theme: 'light' | 'dark') {
  await page.addInitScript((t) => {
    window.localStorage.setItem('lu-theme', t);
    document.documentElement.setAttribute('data-theme', t);
  }, theme);
}

test.describe('A1 upgrade nav', () => {
  test('/a1/ left bar lists modules, not nested lessons', async ({ page }) => {
    await page.goto('/a1/');
    const sidebar = page.locator('.lu-sidebar-nav');
    await expect(sidebar).toBeVisible();
    const labels = await sidebar.locator('.lu-sidebar-text').allTextContents();
    expect(labels.some((label) => label.includes('Речі мають рід'))).toBe(true);
    expect(labels.some((label) => label.includes('Він, вона, воно'))).toBe(false);
    await expect(page.locator('.lu-sidebar-link.active')).toHaveCount(0);
  });

  test('module landing left bar is the three lessons, not the module as 08', async ({ page }) => {
    await page.goto('/a1/things-have-gender/');
    const nums = await page.locator('.lu-sidebar-num').allTextContents();
    expect(nums).toEqual(['01', '02', '03']);
    const labels = await page.locator('.lu-sidebar-text').allTextContents();
    expect(labels).toHaveLength(3);
    expect(labels.some((label) => label === 'Речі мають рід')).toBe(false);
    await expect(page.locator('.lu-sidebar-link.active')).toHaveCount(0);
    await expect(page.locator('.lu-sidebar-back')).toHaveAttribute('href', '/a1/');
  });

  test('lesson page left bar highlights that lesson only', async ({ page }) => {
    await page.goto('/a1/things-have-gender/2/');
    const nums = await page.locator('.lu-sidebar-num').allTextContents();
    expect(nums).toEqual(['01', '02', '03']);
    await expect(page.locator('.lu-sidebar-link.active .lu-sidebar-num')).toHaveText('02');
  });

  test('A1 landing lists both upgraded modules', async ({ page }) => {
    await page.goto('/a1/');
    const labels = await page.locator('.lu-sidebar-text').allTextContents();
    expect(labels).toEqual(expect.arrayContaining(['Речі мають рід', 'Який він?']));
  });

  test('last gender lesson next goes to the next module landing', async ({ page }) => {
    await page.goto('/a1/things-have-gender/3/');
    await expect(page.locator('.lesson-next-prev a').last()).toHaveAttribute('href', '/a1/what-is-it-like/');
    await page.locator('.lesson-next-prev a').last().click();
    await expect(page).toHaveURL(/\/a1\/what-is-it-like\/$/);
    await expect(page.locator('.lu-sidebar-text')).toHaveText(['Який? Яка? Яке?', 'Прикметники', 'Підсумок']);
  });

  test('lesson prev/next hrefs are real paths, not /a1//a1/', async ({ page }) => {
    await page.goto('/a1/things-have-gender/1/');
    const prev = page.locator('.lesson-next-prev a').first();
    const next = page.locator('.lesson-next-prev a').last();
    await expect(prev).toHaveAttribute('href', '/a1/things-have-gender/');
    await expect(next).toHaveAttribute('href', '/a1/things-have-gender/2/');
    await next.click();
    await expect(page).toHaveURL(/\/a1\/things-have-gender\/2\/$/);
    await expect(page.locator('.lesson-next-prev a').first()).toHaveAttribute('href', '/a1/things-have-gender/1/');
    await expect(page.locator('.lesson-next-prev a').last()).toHaveAttribute('href', '/a1/things-have-gender/3/');
  });
});

test.describe('A1 upgrade screenshots', () => {
  for (const theme of ['light', 'dark'] as const) {
    for (const path of [
      '/a1/',
      '/a1/things-have-gender/',
      '/a1/things-have-gender/1/',
      '/a1/things-have-gender/2/',
      '/a1/things-have-gender/3/',
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
