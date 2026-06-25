import { expect, test, type Page } from '@playwright/test';

function trackConsoleErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text());
  });
  page.on('pageerror', (error) => {
    errors.push(error.message);
  });
  return errors;
}

test('browse supports search, category, and letter entry points without dumping all cards', async ({ page }) => {
  await page.goto('/lexicon/browse/');

  const cards = page.locator('.atlas-index-item');
  await expect(cards).toHaveCount(0);
  await expect(page.getByText(/Оберіть літеру алфавіту/)).toBeVisible();

  const search = page.locator('[data-index-search]');
  await expect(search).toBeEnabled();
  await search.fill('офіс');
  await expect(page.locator('.atlas-index-link', { hasText: 'офіс' })).toBeVisible();
  expect(new URL(page.url()).searchParams.get('q')).toBe('офіс');

  await search.fill('');
  await expect(cards).toHaveCount(0);

  await page.getByRole('button', { name: 'русизм' }).click();
  await expect.poll(() => cards.count()).toBeGreaterThanOrEqual(1);
  expect(new URL(page.url()).searchParams.get('cls')).toBe('rus');
  await expect(page.getByRole('heading', { name: 'русизм' })).toBeVisible();

  await page.locator('[data-letter="Д"]').click();
  await expect.poll(() => cards.count()).toBeGreaterThanOrEqual(1);
  await expect(page.getByRole('heading', { name: 'Д', exact: true })).toBeVisible();
  expect(new URL(page.url()).searchParams.get('letter')).toBe('Д');
});

test('practice cloze and matching modes render real rounds for a fresh learner', async ({ page }) => {
  await page.goto('/words-of-the-day/practice/');

  await page.getByRole('button', { name: 'Cloze' }).click();
  await expect(page.locator('[data-testid="practice-cloze"]')).toBeVisible();
  await expect(page.locator('[data-testid="practice-cloze"] input')).toBeVisible();

  await page.getByRole('button', { name: 'Matching' }).click();
  await expect(page.locator('[data-testid="practice-matching"]')).toBeVisible();
  await expect.poll(() => page.locator('[data-activity="match-left-tile"]').count()).toBeGreaterThanOrEqual(3);
});

test('Sovietized SUM-11 definition cards are not rendered on word pages', async ({ page }) => {
  await page.goto('/lexicon/прапор/');

  await expect(page.locator('h1.word-title')).toContainText('прапор');
  await expect(page.locator('.def-card.sum11-flagged')).toHaveCount(0);
});

for (const path of ['/lexicon/', '/words-of-the-day/', '/lexicon/browse/']) {
  test(`${path} loads without console errors`, async ({ page }) => {
    const consoleErrors = trackConsoleErrors(page);

    await page.goto(path);
    await expect(page.locator('body')).toBeVisible();

    expect(consoleErrors).toEqual([]);
  });
}
