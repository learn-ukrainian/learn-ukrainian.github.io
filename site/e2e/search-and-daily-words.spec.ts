import type { Page } from '@playwright/test';
import { expect, test } from './support/hardened-browser.mjs';

/**
 * #12984 — the outside QA run's four findings, re-checked at desktop and phone width.
 * Defect classes: site search misses Word Atlas articles, a Words of the Day level
 * chip stays unselected when its level is empty, Search is unreachable from the
 * site chrome, and stale search copy (retired Etymology page, test-lane Folk label).
 */
const VIEWPORTS = [
  { name: 'desktop 1366', viewport: { width: 1366, height: 900 } },
  { name: 'phone 390', viewport: { width: 390, height: 844 } },
];

async function expectSearchLinkInChrome(page: Page) {
  const header = page.getByRole('banner').getByRole('link', { name: /^(Search|Пошук)$/ });
  await expect(header).toHaveAttribute('href', '/search/');
  await expect(header).toBeInViewport({ ratio: 1 });
  const footerLink = page.locator('footer.lu-footer a[href="/search/"]');
  await footerLink.scrollIntoViewIfNeeded();
  await expect(footerLink).toBeVisible();
}

/** The primary nav scrolls with a hidden scrollbar: no course link may sit outside its visible box. */
async function clippedPrimaryLinks(page: Page): Promise<string[]> {
  return page.evaluate(() => {
    const nav = document.querySelector('nav[aria-label="Primary"]');
    if (!nav || nav.getBoundingClientRect().width === 0) return [];
    const right = nav.getBoundingClientRect().right + 0.5;
    return [...nav.querySelectorAll('a[href^="/"]')]
      .filter((a) => a.getBoundingClientRect().right > right)
      .map((a) => a.getAttribute('href') ?? '');
  });
}

for (const { name, viewport } of VIEWPORTS) {
  test.describe(name, () => {
    test.use({ viewport });

    for (const locale of ['en', 'uk'] as const) {
      test(`Search is linked from the site chrome (${locale})`, async ({ page }) => {
        await page.addInitScript((loc) => window.localStorage.setItem('lu-chrome-locale', loc), locale);
        await page.goto('/b1/');
        await expectSearchLinkInChrome(page);
        expect(await clippedPrimaryLinks(page)).toEqual([]);
      });
    }

    test('a Ukrainian lemma and its romanization find the Word Atlas article', async ({ page }) => {
      for (const query of ['офіс', 'ofis']) {
        await page.goto(`/search/?q=${encodeURIComponent(query)}`);
        const hit = page.locator(`[data-search-results] a[href="/lexicon/${encodeURIComponent('офіс')}/"]`);
        await expect(hit).toBeVisible();
        await expect(hit).toContainText('Word Atlas');
        await expect(page.locator('[data-search-empty]')).toBeHidden();
      }
    });

    test('the empty state names no retired page and Folk carries its track name', async ({ page }) => {
      await page.goto('/search/?q=xyzzyqqqnotaword');
      const empty = page.locator('[data-search-empty]');
      await expect(empty).toBeVisible();
      await expect(empty).not.toContainText(/etymolog/i);
      await page.goto('/search/');
      const folk = page.locator('[data-search-results] a[href="/folk/"]');
      await expect(folk).toContainText('Фольклор та усна традиція');
      await expect(page.locator('[data-search-results]')).not.toContainText(/test track/i);
    });

    test('every level chip shows as selected when clicked, including an empty level', async ({ page }) => {
      await page.goto('/words-of-the-day/');
      const chips = page.locator('[data-daily-level]');
      await expect(chips).toHaveCount(6);
      await expect(page.locator('[data-daily-words]')).toHaveAttribute('data-daily-ready', 'true');
      for (const level of ['C1', 'C2', 'A2']) {
        await page.locator(`[data-daily-level="${level}"]`).click();
        await expect(page.locator(`[data-daily-level="${level}"]`)).toHaveAttribute('aria-pressed', 'true');
        await expect(page.locator('[data-daily-level][aria-pressed="true"]')).toHaveCount(1);
      }
    });
  });
}
