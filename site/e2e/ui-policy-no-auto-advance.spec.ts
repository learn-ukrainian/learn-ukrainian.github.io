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
  await page.goto('/practice/');

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
  await page.goto('/practice/');

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

/**
 * #8732 — the queue boundary. Rating a card synchronously updates session
 * bookkeeping (reviews completed, new cards introduced) before the learner
 * ever presses «Далі», and once `DEFAULT_NEW_PER_SESSION` (8) is crossed the
 * pool the display is pinned against can legitimately re-rank — but the
 * currently shown card must still never change until «Далі» is pressed, and
 * the session must still resolve predictably afterward (a further card or the
 * summary), not a dead card / frozen progress.
 */
test('flashcards: no card change across the queue boundary (8 new cards), then a predictable next step', async ({
  page,
  context,
}) => {
  await context.clearCookies();
  await page.goto('/practice/');

  await page.locator('button[data-mode="flashcards"]').click();
  const card = page.locator('[data-activity="flashcard"]');
  const advance = page.getByTestId('practice-advance-button');
  const progress = page.getByTestId('practice-session-progress');

  const rateVisibleCard = async (): Promise<string> => {
    await expect(card).toBeVisible();
    const front = (await card.locator('.flashcard-front .flashcard-word').textContent()) ?? '';
    await card.click();
    await expect(card).toHaveAttribute('data-flipped', 'true');
    await page.locator('[data-rate="good"]').click();
    return front;
  };

  // Serve and explicitly advance through the first 7 cards normally.
  for (let served = 0; served < 7; served += 1) {
    await rateVisibleCard();
    await expect(advance).toBeVisible();
    await advance.click();
    await expect(advance).toBeHidden();
  }

  // The 8th rating crosses DEFAULT_NEW_PER_SESSION.
  const eighthFront = await rateVisibleCard();

  // Dwell: the rating alone (no «Далі» yet) must never change the displayed card.
  await expect(advance, 'the advance control must stay offered while dwelling').toBeVisible();
  await expect(
    card.locator('.flashcard-front .flashcard-word'),
    'the card changed before «Далі» was pressed',
  ).toHaveText(eighthFront);

  // Positive path: «Далі» still resolves the session predictably — either a
  // further (different) card, or the summary. Never a frozen/dead state.
  await advance.click();
  await expect(advance).toBeHidden();
  await expect
    .poll(async () => {
      const summaryVisible = await page.getByTestId('practice-session-summary').isVisible().catch(() => false);
      if (summaryVisible) return 'summary';
      const nextFront = await card
        .locator('.flashcard-front .flashcard-word')
        .textContent()
        .catch(() => null);
      return nextFront && nextFront !== eighthFront ? 'advanced' : null;
    }, { message: 'session must reach the summary or serve a genuinely different card' })
    .not.toBeNull();
  await expect(progress).not.toContainText('NaN');
});
