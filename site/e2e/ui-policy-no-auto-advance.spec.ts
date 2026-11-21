import { expect, test } from './support/hardened-browser.mjs';

// Choice was withdrawn in 1c2a48a41f0; stress exercises the shared advance rule.
test('stress mode: answering never auto-advances; only «Далі» moves the session', async ({ page, context }) => {
  await context.clearCookies();
  await page.clock.install();
  await page.goto('/practice/');
  await page.locator('button[data-mode="stress"]').click();
  const option = page.locator('.stress-vowel').first();
  await expect(option).toBeVisible();
  const progress = page.getByTestId('practice-session-progress');
  await expect(progress).toContainText('0/');
  await option.click();
  await expect(page.getByTestId('practice-advance-button')).toBeVisible();
  const exercise = page.getByTestId('practice-stress');
  const answeredText = await exercise.textContent();
  await expect(progress).toContainText('1/');
  await page.clock.runFor(60_000);
  await expect(exercise, 'exercise changed without «Далі»').toHaveText(answeredText ?? '');
  await expect(progress).toContainText('1/');
  await expect(page.getByTestId('practice-advance-button')).toBeVisible();
  await page.getByTestId('practice-advance-button').click();
  await expect(page.getByTestId('practice-advance-button')).toBeHidden();
});
