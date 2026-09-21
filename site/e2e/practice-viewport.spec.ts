import { expect, test } from '@playwright/test';

test.describe.configure({ mode: 'serial' });

test.describe('mobile viewport', () => {
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
    await page.goto('/practice/?lemmaId=%D0%B2%D0%BE%D0%B4%D0%B0');
    const stage = page.locator('.lexicon-practice-stage');
    const answer = stage.locator('.stress-vowel').first();
    await expect(answer).toBeVisible();
    await answer.scrollIntoViewIfNeeded();
    const before = await stage.boundingBox();
    const scrollBefore = await page.evaluate(() => window.scrollY);
    await answer.click();

    const advance = page.getByTestId('practice-advance-button');
    await expect(advance).toBeFocused();
    expect(new URL(page.url()).pathname).toBe('/practice/');
    const after = await stage.boundingBox();
    expect(after!.y).toBe(before!.y);
    expect(await page.evaluate(() => window.scrollY)).toBe(scrollBefore);
    await advance.press('Enter');
    await expect(advance).toHaveCount(0);
  });
});

test.describe('desktop practice active session viewport constraints (#8377)', () => {
  const desktopViewports = [
    { name: 'standard desktop (1280x720)', viewport: { width: 1280, height: 720 } },
    { name: 'compact laptop (1024x768)', viewport: { width: 1024, height: 768 } },
  ];

  for (const { name, viewport } of desktopViewports) {
    test.describe(name, () => {
      test.use({ viewport });

      for (const locale of ['en', 'uk'] as const) {
        test(`active flashcard session has zero overflow and visible controls (${locale})`, async ({ page }) => {
          await page.goto('/practice/', { waitUntil: 'load' });
          await page.evaluate((loc) => {
            document.documentElement.dataset.chromeLocale = loc;
          }, locale);

          // Select A1 level to ensure deck has practice items
          const a1Btn = page.locator('.k3-levels button', { hasText: /^A1$/ });
          await expect(a1Btn).toBeVisible({ timeout: 20000 });
          await a1Btn.click();

          const flashcardMode = page.locator('button[data-mode="flashcards"]');
          await expect(flashcardMode).toBeVisible({ timeout: 10000 });
          await flashcardMode.click();

          // Wait for active flashcard session card to mount
          const card = page.locator('[data-activity="flashcard"]');
          await expect(card).toBeVisible({ timeout: 15000 });

          // Verify document has zero horizontal overflow during active exercise
          const overflow = await page.evaluate(() => {
            const doc = document.documentElement;
            const body = document.body;
            return doc.scrollWidth > window.innerWidth || body.scrollWidth > window.innerWidth;
          });
          expect(overflow, `active flashcard session produced horizontal overflow at ${name} (${locale})`).toBe(false);

          // Verify card elements are fully within the viewport bounds
          const cardBox = await card.boundingBox();
          expect(cardBox).not.toBeNull();
          if (cardBox) {
            expect(cardBox.x).toBeGreaterThanOrEqual(0);
            expect(cardBox.x + cardBox.width).toBeLessThanOrEqual(viewport.width);
          }
        });

        test(`active direct lemma session has zero overflow and visible controls (${locale})`, async ({ page }) => {
          await page.goto('/practice/?lemmaId=%D0%B2%D0%BE%D0%B4%D0%B0', { waitUntil: 'load' });
          await page.evaluate((loc) => {
            document.documentElement.dataset.chromeLocale = loc;
          }, locale);

          const stage = page.locator('.lexicon-practice-stage');
          await expect(stage).toBeVisible({ timeout: 20000 });

          const overflow = await page.evaluate(() => {
            const doc = document.documentElement;
            const body = document.body;
            return doc.scrollWidth > window.innerWidth || body.scrollWidth > window.innerWidth;
          });
          expect(overflow, `direct lemma session produced horizontal overflow at ${name} (${locale})`).toBe(false);

          const stageBox = await stage.boundingBox();
          expect(stageBox).not.toBeNull();
          if (stageBox) {
            expect(stageBox.x).toBeGreaterThanOrEqual(0);
            expect(stageBox.x + stageBox.width).toBeLessThanOrEqual(viewport.width);
          }
        });
      }
    });
  }
});
