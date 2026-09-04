import { expect, test } from '@playwright/test';

test.use({ viewport: { width: 390, height: 400 } });

test('answer preserves the toolbar and exercise position in a short viewport', async ({ page }) => {
  // Keep the mixed, lemma-focused toolbar while making the exercise deterministic.
  // Reuse the published item; only restrict its available modes for this UI test.
  await page.route('**/lexicon/practice-index.*.json', async (route) => {
    const response = await route.fetch();
    if (!response.ok()) return route.fulfill({ response });
    const index = await response.json();
    index.items = index.items.filter((item: { lemmaId: string }) => item.lemmaId === 'вода')
      .map((item: object) => ({ ...item, modes: ['stress'], hasCloze: false, clozeIds: [] }));
    await route.fulfill({ response, json: index });
  });
  await page.goto('/words-of-the-day/practice/?lemmaId=%D0%B2%D0%BE%D0%B4%D0%B0');
  const stage = page.locator('.lexicon-practice-stage');
  const answer = stage.locator('.stress-vowel').first();
  await expect(answer).toBeVisible();
  await answer.scrollIntoViewIfNeeded();
  const before = await stage.boundingBox();
  const scrollBefore = await page.evaluate(() => window.scrollY);
  await answer.click();

  const advance = page.getByTestId('practice-advance-button');
  await expect(advance).toBeFocused();
  expect(new URL(page.url()).pathname).toBe('/words-of-the-day/practice/');
  const after = await stage.boundingBox();
  expect(after!.y).toBe(before!.y);
  expect(await page.evaluate(() => window.scrollY)).toBe(scrollBefore);
  await advance.press('Enter');
  await expect(advance).toHaveCount(0);
});
