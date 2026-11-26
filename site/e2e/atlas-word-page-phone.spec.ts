import { expect, test } from './support/hardened-browser.mjs';

/**
 * Eggbot word-card QA: a long Wikipedia URL must stay inside a 390px screen,
 * and a Ukrainian page must name the pronunciation control with the Ukrainian
 * string the player map already holds (Послухати вимову).
 *
 * Route: програміст, an A1 article whose Wikipedia href is a percent-encoded
 * URL wider than 390px when shown raw.
 */
const ROUTE = '/lexicon/програміст/';
const UK_PLAY = 'Послухати вимову';

test.use({
  viewport: { width: 390, height: 844 },
  isMobile: true,
  hasTouch: true,
  locale: 'uk-UA',
});

test('word page at 390x844 wraps the Wikipedia link and uses the Ukrainian pronunciation name', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('lu-chrome-locale', 'uk');
  });
  const response = await page.goto(ROUTE);
  expect(response, 'word page response').not.toBeNull();
  const article = page.locator('[data-word-atlas]');
  await expect(article).toBeVisible();
  await expect(page.locator('html')).toHaveAttribute('data-chrome-locale', 'uk');

  const button = article.locator('[data-pronunciation-lemma] button');
  await expect(button).toBeVisible();
  await expect(button).toHaveAccessibleName(UK_PLAY);

  const wiki = article.locator('.wiki-source a[href*="wikipedia.org"]');
  await expect(wiki).toBeVisible();
  await expect(wiki).toHaveAccessibleName('Вікіпедія (нова вкладка)');

  const unavailable = article.getByTestId('atlas-practice-cta-unavailable');
  await expect(unavailable).toHaveAccessibleName('Ще немає в наборі практики');

  const wider = await page.evaluate(() => {
    const viewport = document.documentElement.clientWidth;
    const offenders: string[] = [];
    for (const el of document.querySelectorAll('body *')) {
      const width = el.getBoundingClientRect().width;
      if (width > viewport + 1) {
        const cls = typeof el.className === 'string' ? el.className.slice(0, 60) : '';
        offenders.push(`${el.tagName}${cls ? '.' + cls : ''} ${Math.round(width)}px`);
      }
    }
    return offenders;
  });
  expect(wider).toEqual([]);
});
