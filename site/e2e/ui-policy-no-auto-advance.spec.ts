import { expect, test } from '@playwright/test';

/**
 * #5376 check 3 — no-auto-advance policy (behavioral, timers mocked).
 *
 * Policy: after ANY answer, the next item must NOT render until the learner
 * activates «Далі» / «Next» (`practice-advance-button`). Auto-advance on a
 * timer steals the learner's review moment. Timers are mocked (page.clock) and
 * fast-forwarded far past any conceivable delay: if a setTimeout/setInterval
 * drives advancement, the session moves and the check fails.
 */

test('flashcards: rating never auto-advances; only «Далі» moves the session', async ({ page, context }) => {
  await context.clearCookies();
  await page.clock.install();
  await page.goto('/words-of-the-day/practice/');

  await page.locator('button[data-mode="flashcards"]').click();
  const card = page.locator('[data-activity="flashcard"]');
  await expect(card).toBeVisible();

  await card.click();
  await expect(card).toHaveAttribute('data-flipped', 'true');
  const firstWord = (await card.locator('.flashcard-word').first().textContent()) ?? '';

  await page.locator('[data-rate="good"]').click();
  await expect(card).toHaveAttribute('data-rated', 'true');
  const progress = page.getByTestId('practice-session-progress');
  await expect(progress).toContainText('0/');

  // Fast-forward 60 virtual seconds — several orders of magnitude past any
  // legitimate UI timer. Nothing about the session may change on its own.
  await page.clock.runFor(60_000);

  await expect(progress, 'session advanced without «Далі»').toContainText('0/');
  await expect(card, 'card un-rated itself without «Далі»').toHaveAttribute('data-rated', 'true');
  expect(
    (await card.locator('.flashcard-word').first().textContent()) ?? '',
    'a different card rendered without «Далі»',
  ).toBe(firstWord);
  await expect(page.getByTestId('practice-advance-button')).toBeVisible();

  // Explicit activation is the ONLY path forward.
  await page.getByTestId('practice-advance-button').click();
  await expect(progress).toContainText('1/');
});

test('choice mode: answering never auto-advances; only «Далі» moves the session', async ({ page, context }) => {
  await context.clearCookies();
  await page.clock.install();
  await page.goto('/words-of-the-day/practice/');

  await page.locator('button[data-mode="choice"]').click();
  const option = page.locator('.mc-opt').first();
  await expect(option).toBeVisible();

  const progress = page.getByTestId('practice-session-progress');
  await expect(progress).toContainText('0/');

  await option.click();
  await expect(page.getByTestId('practice-advance-button')).toBeVisible();

  await page.clock.runFor(60_000);

  await expect(progress, 'session advanced without «Далі»').toContainText('0/');
  await expect(page.getByTestId('practice-advance-button')).toBeVisible();

  await page.getByTestId('practice-advance-button').click();
  await expect(progress).toContainText('1/');
});
