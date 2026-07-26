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

test('practice cloze mode never dead-ends for a fresh learner', async ({ page }) => {
  await page.goto('/words-of-the-day/practice/');

  await page.locator('button[data-mode="cloze"]').click();
  // Cloze is fail-closed until reviewed sentences are authored (#3797). The mode must show a
  // real cloze card OR a clear "being prepared" message — never the ambiguous "all done"
  // dead-end the user reported. This invariant holds before AND after cloze content lands.
  const clozeCard = page.locator('[data-testid="practice-cloze"]');
  const clozeEmpty = page.locator('[data-testid="practice-cloze-empty"]');
  await expect(clozeCard.or(clozeEmpty)).toBeVisible();
});

test('practice matching renders a real round (>=3 pairs) for a fresh learner', async ({ page }) => {
  await page.goto('/words-of-the-day/practice/');

  await page.locator('button[data-mode="matching"]').click();
  await expect(page.locator('[data-testid="practice-matching"]')).toBeVisible();
  await expect.poll(() => page.locator('[data-activity="match-left-tile"]').count()).toBeGreaterThanOrEqual(3);
});

test('practice mode switch starts the selected mode without inheriting the unfinished one', async ({ page }) => {
  await page.goto('/words-of-the-day/practice/');

  await page.locator('button[data-mode="matching"]').click();
  await expect(page.locator('[data-testid="practice-matching"]')).toBeVisible();
  await page.getByRole('button', { name: /Додому|Home/ }).click();

  // The K3 dashboard preserves mode snapshots but exposes only the primary mixed resume CTA.
  // Switching to a different mode starts fresh instead of inheriting the unfinished session.
  await page.locator('button[data-mode="flashcards"]').click();

  await expect(page.locator('[data-activity="flashcard"]')).toBeVisible();
  await expect(page.locator('[data-testid="practice-matching"]')).toBeHidden();
  await expect(page.locator('[data-testid="practice-session-progress"]')).toContainText('0/');
});

for (const [path, label] of [
  ['/words-of-the-day/practice/', 'plain practice page'],
  ['/words-of-the-day/practice/?lemmaId=%D0%BA%D0%B0%D0%B2%D0%B0', 'deep-link practice page'],
] as const) {
  test(`${label} hides the static error fallback after practice loads (#4984, #4946)`, async ({ page }) => {
    await page.goto(path);

    await expect(page.locator('#lexicon-practice-mount .lexicon-practice')).toBeVisible();
    await expect(page.locator('#lexicon-practice-fallback')).toBeHidden();
  });
}

test('all СУМ-11 definition cards are hidden from word pages (Soviet dictionary)', async ({ page }) => {
  // прапор carries a *flagged* (sovietization_risk>0) СУМ-11 definition card. Assert
  // BOTH the flagged and clean СУМ-11 classes are absent, so a regression that rendered
  // the flagged card as a clean `.sum11` card can't sneak through (agy review 2026-06-26).
  await page.goto('/lexicon/прапор/');
  await expect(page.locator('h1.word-title')).toContainText('прапор');
  await expect(page.locator('.def-card.sum11, .def-card.sum11-flagged')).toHaveCount(0);

  // вареник carries a *clean* (risk==0) СУМ-11 card. Hide-all (2026-06-25) drops it too;
  // the meaning block (rendered as a СУМ-20 card) still gives the learner a definition, so
  // the page is never left definition-less.
  await page.goto('/lexicon/вареник/');
  await expect(page.locator('h1.word-title')).toContainText('вареник');
  await expect(page.locator('.def-card.sum11, .def-card.sum11-flagged')).toHaveCount(0);
  await expect(page.locator('.def-card.sum20')).toHaveCount(1);
});

for (const path of ['/lexicon/', '/words-of-the-day/', '/lexicon/browse/']) {
  test(`${path} loads without console errors`, async ({ page }) => {
    const consoleErrors = trackConsoleErrors(page);

    await page.goto(path);
    await expect(page.locator('body')).toBeVisible();

    expect(consoleErrors).toEqual([]);
  });
}

test('practice page shows UA fallback when LexiconPractice island chunk fails to load (#4694)', async ({ page }) => {
  // Route-abort the island's dynamic chunk (identified by stem in filename, stable across
  // builds) to simulate the exact astro-island pre-React failure mode:
  // "Failed to fetch dynamically imported module". This fires the 'astro:hydration-error'
  // event (and/or watchdog) before any React code or its error boundary can run.
  //
  // Astro 7.1+ retries a failed island import once with `?astro-retry=<ts>` after 1s
  // (importWithRetry). A glob ending in `.js` misses that retry URL and the island
  // hydrates successfully — match on the LexiconPractice stem with or without query.
  await page.route(/LexiconPractice[^/]*\.js(?:\?|$)/, (route) => route.abort());

  await page.goto('/words-of-the-day/practice/');

  // Expect the static UA fallback (error listener path is fast; no reliance on 10s timeout).
  // Allow for Astro's 1s import retry before hydration-error fires.
  const fallback = page.locator('#lexicon-practice-fallback');
  await expect(fallback).toBeVisible({ timeout: 8000 });
  await expect(fallback).toContainText('Не вдалося завантажити практику');
  const retryBtn = page.getByRole('button', { name: 'Спробувати ще раз' });
  await expect(retryBtn).toBeVisible();

  // Mount wrapper is hidden on failure; fallback is swapped in.
  await expect(page.locator('#lexicon-practice-mount')).toHaveAttribute('hidden', '');
});

async function prepareResumableMixedSession(page: Page): Promise<void> {
  await page.goto('/words-of-the-day/practice/');
  // Wait for the idle dashboard to settle and the primary CTA to be actionable.
  await expect(page.getByTestId('practice-start-session')).toBeVisible();
  await page.getByTestId('practice-start-session').click();
  // Confirm the exercise stage rendered.
  await expect(page.locator('.lexicon-practice-stage')).toBeVisible();
  // Return home to persist a resumable mixed snapshot.
  await page.getByRole('button', { name: /Додому|Home/ }).click();
  await expect(page.getByTestId('practice-start-session')).toBeVisible();
}

async function assertFirstViewportPracticeCTAs(page: Page, locale: 'en' | 'uk'): Promise<void> {
  const start = page.getByTestId('practice-start-session');
  const reset = page.locator('button[data-reset-mode="mixed"]');

  for (const control of [start, reset]) {
    await expect(control).toBeVisible();
    const box = await control.boundingBox();
    expect(box).not.toBeNull();
    const top = box!.y;
    const bottom = box!.y + box!.height;
    expect(top).toBeGreaterThanOrEqual(0);
    expect(bottom).toBeLessThanOrEqual(768);
  }

  // Accessible names must match the active chrome locale only (no slash duplicates).
  // With a resumable Mixed snapshot (D5), the primary CTA is the REAL resume action
  // ("Resume session" / "Продовжити заняття") and the secondary is the danger-outline
  // reset ("Start over" / "Почати наново").
  if (locale === 'en') {
    await expect(page.getByRole('button', { name: 'Resume session' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Start over' })).toBeVisible();
    await expect(page.getByRole('button', { name: /Start session|Почати заняття|Почати наново/ })).toHaveCount(0);
  } else {
    await expect(page.getByRole('button', { name: 'Продовжити заняття' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Почати наново' })).toBeVisible();
    await expect(page.getByRole('button', { name: /Start session|Resume session|Почати заняття/ })).toHaveCount(0);
  }

  // The words disclosure begins closed and the 3D preview remains visible.
  const details = page.getByTestId('practice-daily-details');
  await expect(details).not.toHaveAttribute('open');
  await expect(page.locator('.flashcard.daily-preview-card')).toBeVisible();

  // The one-column visual hierarchy is the actual DOM/tab order, not a CSS
  // placement trick that would make keyboard navigation disagree with the page.
  await expect.poll(async () =>
    page.locator('.k3-practice-dashboard > [data-testid]').evaluateAll(
      (elements) => elements.map((element) => element.getAttribute('data-testid')),
    ),
  ).toEqual([
    'practice-dashboard-hero',
    'practice-dashboard-stats',
    'practice-dashboard-words',
    'practice-dashboard-session',
    'practice-dashboard-secondary',
  ]);
}

test('HARD-1: English setup dashboard shows start and resume CTAs without scroll at 1366x768', async ({ page, context }) => {
  await context.clearCookies();
  await page.goto('/words-of-the-day/practice/');
  await page.evaluate(() => {
    window.localStorage.setItem('lu-chrome-locale', 'en');
    document.documentElement.setAttribute('data-theme', 'light');
  });
  await prepareResumableMixedSession(page);

  await page.setViewportSize({ width: 1366, height: 768 });
  await page.reload();
  await page.waitForLoadState('networkidle');

  const scrollY = await page.evaluate(() => window.scrollY);
  expect(scrollY).toBe(0);

  await assertFirstViewportPracticeCTAs(page, 'en');
});

test('HARD-2: Ukrainian setup dashboard shows start and resume CTAs without scroll at 1366x768', async ({ page, context }) => {
  await context.clearCookies();
  await page.goto('/words-of-the-day/practice/');
  await page.evaluate(() => {
    window.localStorage.setItem('lu-chrome-locale', 'uk');
    document.documentElement.setAttribute('data-theme', 'dark');
  });
  await prepareResumableMixedSession(page);

  await page.setViewportSize({ width: 1366, height: 768 });
  await page.reload();
  await page.waitForLoadState('networkidle');

  const scrollY = await page.evaluate(() => window.scrollY);
  expect(scrollY).toBe(0);

  await assertFirstViewportPracticeCTAs(page, 'uk');
});

test('practice stress mode renders word-shaped vowel buttons for an N-vowel word', async ({ page }) => {
  await page.goto('/words-of-the-day/practice/');

  await page.locator('button[data-mode="stress"]').click();
  const stress = page.locator('[data-testid="practice-stress"]');
  await expect(stress).toBeVisible();
  await expect.poll(() => stress.locator('.stress-vowel').count()).toBeGreaterThanOrEqual(2);

  // Selecting a vowel locks the control and shows a verdict marker.
  const firstVowel = stress.locator('.stress-vowel').first();
  await firstVowel.click();
  await expect(firstVowel).toBeDisabled();
  await expect(stress.locator('[data-testid="practice-stress-verdict"]')).toBeVisible();
});

test('Stress mode remains available after choosing A2', async ({ page, context }) => {
  await context.clearCookies();
  await page.goto('/words-of-the-day/practice/');

  await page.getByRole('button', { name: 'A2' }).click();
  await expect(page.locator('button[data-mode="stress"]')).toBeVisible();
  await expect(page.locator('button[data-mode]')).toHaveCount(11);
});

test('practice flashcard rating locks the card and waits for explicit next', async ({ page, context }) => {
  await context.clearCookies();
  await page.goto('/words-of-the-day/practice/');

  await page.locator('button[data-mode="flashcards"]').click();
  const card = page.locator('[data-activity="flashcard"]');
  await expect(card).toBeVisible();

  // Ratings are disabled before the card is flipped.
  const goodButton = page.locator('[data-rate="good"]');
  await expect(goodButton).toBeDisabled();

  await card.click();
  await expect(card).toHaveAttribute('data-flipped', 'true');
  await expect(goodButton).toBeEnabled();

  await goodButton.click();
  await expect(card).toHaveAttribute('data-rated', 'true');
  await expect(goodButton).toBeDisabled();
  await expect(page.getByTestId('practice-advance-button')).toBeVisible();
});

// --- Practice UX batch — design delta 2026-07-26 (A1-A7) ---

/** Complete one flashcard round (flip + rate) so the caller can advance or inspect progress. */
async function completeOneFlashcard(page: Page, rating: 'good' | 'easy' | 'hard' | 'again' = 'good'): Promise<void> {
  const card = page.locator('[data-activity="flashcard"]');
  await expect(card).toBeVisible();
  await card.click();
  await expect(card).toHaveAttribute('data-flipped', 'true');
  await page.locator(`[data-rate="${rating}"]`).click();
  await expect(page.getByTestId('practice-advance-button')).toBeVisible();
}

/**
 * `Mixed` mode opens on any of the 11 exercise types (D3: session-seeded, not fixed).
 * Flashcards and every "pick one option" mode (choice/classify/synonym/paradigm/
 * paronym/heritage) share simple, quick completions; the rest (matching/cloze/
 * stress) are not needed here, so retry with a fresh session-seeded draw instead
 * of teaching this helper all 11 interaction shapes.
 */
async function completeOneEasyMixedItem(page: Page): Promise<void> {
  for (let attempt = 0; attempt < 8; attempt += 1) {
    await expect(page.locator('.lexicon-practice-stage')).toBeVisible();
    const flashcard = page.locator('[data-activity="flashcard"]');
    const mcOption = page.locator('.mc-opt').first();
    if (await flashcard.isVisible().catch(() => false)) {
      await flashcard.click();
      await page.locator('[data-rate="good"]').click();
      await expect(page.getByTestId('practice-advance-button')).toBeVisible();
      return;
    }
    if (await mcOption.isVisible().catch(() => false)) {
      await mcOption.click();
      await expect(page.getByTestId('practice-advance-button')).toBeVisible();
      return;
    }
    // Going home without completing anything leaves a resumable snapshot, so the
    // primary CTA would now RESUME this exact (unhandled-type) session instead of
    // drawing fresh — use the reset control (D5) to force a genuinely new draw.
    await page.getByRole('button', { name: /Додому|Home/ }).click();
    const reset = page.locator('button[data-reset-mode="mixed"]');
    if (await reset.isVisible().catch(() => false)) {
      await reset.click();
    } else {
      await page.getByTestId('practice-start-session').click();
    }
  }
  throw new Error('Could not reach an easily-completable mixed-mode item after 8 tries');
}

async function prepareResumableMixedSessionWithProgress(page: Page): Promise<void> {
  await page.goto('/words-of-the-day/practice/');
  await expect(page.getByTestId('practice-start-session')).toBeVisible();
  await page.getByTestId('practice-start-session').click();
  await expect(page.locator('.lexicon-practice-stage')).toBeVisible();
  // Advance one item so the resumable snapshot carries real progress — this lets
  // A3 tell "resumed with prior progress" apart from "reset back to 0".
  await completeOneEasyMixedItem(page);
  await page.getByTestId('practice-advance-button').click();
  await page.getByRole('button', { name: /Додому|Home/ }).click();
  await expect(page.getByTestId('practice-start-session')).toBeVisible();
}

test('A1: the practice Words-of-the-Day zone shows the same 12 as /words-of-the-day/ for the same level and day', async ({ page, context }) => {
  await context.clearCookies();

  await page.addInitScript(() => window.localStorage.setItem('lu-learner-level', 'A1'));

  await page.goto('/words-of-the-day/');
  await expect(page.locator('.lexicon-daily-item')).not.toHaveCount(0);
  const atlasLemmas = await page.locator('.lexicon-daily-lemma').allTextContents();

  await page.goto('/words-of-the-day/practice/');
  await page.getByTestId('practice-daily-summary').click();
  const practiceLemmas = await page.locator('.daily-deck-row .row-lemma').allTextContents();

  expect(practiceLemmas.length).toBe(atlasLemmas.length);
  expect(new Set(practiceLemmas)).toEqual(new Set(atlasLemmas));
});

test('A2: starting two sessions back-to-back yields different item sequences', async ({ page, context }) => {
  await context.clearCookies();

  async function captureFirstThreeFlashcards(): Promise<string[]> {
    await page.goto('/words-of-the-day/practice/');
    await page.locator('button[data-mode="flashcards"]').click();
    const words: string[] = [];
    for (let i = 0; i < 3; i += 1) {
      const card = page.locator('[data-activity="flashcard"]');
      await expect(card).toBeVisible();
      words.push((await card.locator('.flashcard-word').first().textContent()) ?? '');
      await completeOneFlashcard(page);
      await page.getByTestId('practice-advance-button').click();
    }
    await page.getByRole('button', { name: /Додому|Home/ }).click();
    return words;
  }

  const first = await captureFirstThreeFlashcards();
  const second = await captureFirstThreeFlashcards();

  expect(second).not.toEqual(first);
});

test('A3: a stored in-progress session shows Продовжити + Почати наново; Почати наново clears it and starts fresh', async ({ page, context }) => {
  await context.clearCookies();
  await page.addInitScript(() => window.localStorage.setItem('lu-chrome-locale', 'uk'));
  await prepareResumableMixedSessionWithProgress(page);

  await expect(page.getByRole('button', { name: 'Продовжити заняття' })).toBeVisible();
  const resetBtn = page.getByRole('button', { name: 'Почати наново' });
  await expect(resetBtn).toBeVisible();

  await resetBtn.click();

  await expect(page.locator('.lexicon-practice-stage')).toBeVisible();
  await expect(page.getByTestId('practice-session-progress')).toContainText('0/');

  // The stored snapshot was discarded, not resumed-with-progress: going home again
  // reoffers the primary CTA as a fresh start-state pairing (no prior 1/N carried over).
  await page.getByRole('button', { name: /Додому|Home/ }).click();
  await expect(page.getByRole('button', { name: 'Продовжити заняття' })).toBeVisible();
});

test('A4: Далі sits in the top status row next to the counter and is clickable without scrolling at 1366x768', async ({ page, context }) => {
  await context.clearCookies();
  await page.setViewportSize({ width: 1366, height: 768 });
  await page.goto('/words-of-the-day/practice/');

  await page.locator('button[data-mode="flashcards"]').click();
  await completeOneFlashcard(page);

  // Exactly one Next control, living in the status bar next to the n/N pill.
  await expect(page.getByTestId('practice-advance-button')).toHaveCount(1);
  const statusBarNext = page.locator('.lexicon-practice-stage-bar').getByTestId('practice-advance-button');
  await expect(statusBarNext).toBeVisible();

  // The status bar (with Далі) sits at the very top of the exercise stage, so it is
  // reachable without scrolling. The scroll-to-top reset (on answering) settles
  // asynchronously (a browser reflow/scroll-anchoring tick after the result
  // renders), so poll rather than reading the geometry the instant the button
  // appears.
  await expect.poll(async () => (await statusBarNext.boundingBox())?.y).toBeGreaterThanOrEqual(0);
  const box = await statusBarNext.boundingBox();
  expect(box).not.toBeNull();
  expect(box!.y + box!.height).toBeLessThanOrEqual(768);

  // Enter also advances, per the existing key-handling contract.
  await page.keyboard.press('Enter');
  await expect(page.getByTestId('practice-session-progress')).toContainText('1/');
});

test('A5: switching level with a session in progress offers a fresh session; accepting starts one from the chosen set', async ({ page, context }) => {
  await context.clearCookies();
  await prepareResumableMixedSession(page);

  await page.getByRole('button', { name: 'A2' }).click();

  const offer = page.getByTestId('practice-switch-session-offer');
  await expect(offer).toBeVisible();

  await page.getByTestId('practice-switch-session-accept').click();

  await expect(page.locator('.lexicon-practice-stage')).toBeVisible();
  await expect(page.getByTestId('practice-session-progress')).toContainText('0/');
});

test('A5b: declining the switch offer reverts the selection and leaves the session untouched', async ({ page, context }) => {
  await context.clearCookies();
  await page.addInitScript(() => window.localStorage.setItem('lu-chrome-locale', 'uk'));
  await prepareResumableMixedSession(page);

  await page.getByRole('button', { name: 'A2' }).click();
  await expect(page.getByTestId('practice-switch-session-offer')).toBeVisible();

  await page.getByTestId('practice-switch-session-decline').click();

  await expect(page.getByTestId('practice-switch-session-offer')).toBeHidden();
  const levelA1 = page.getByTestId('practice-dashboard-hero').getByRole('button', { name: 'A1', exact: true });
  await expect(levelA1).toHaveClass(/active/);
  // The resumable Mixed snapshot from setup is untouched by the decline.
  await expect(page.getByRole('button', { name: 'Продовжити заняття' })).toBeVisible();
});

test('A6: the session-box estimate stays inside the card at 1366x768 and 390x844', async ({ page, context }) => {
  await context.clearCookies();

  for (const viewport of [{ width: 1366, height: 768 }, { width: 390, height: 844 }]) {
    await page.setViewportSize(viewport);
    await page.goto('/words-of-the-day/practice/');

    const card = page.getByTestId('practice-dashboard-session');
    const estimate = page.getByTestId('practice-session-scope');
    await expect(card).toBeVisible();

    const cardBox = await card.boundingBox();
    expect(cardBox).not.toBeNull();
    if ((await estimate.count()) > 0) {
      const estimateBox = await estimate.boundingBox();
      expect(estimateBox).not.toBeNull();
      expect(estimateBox!.x).toBeGreaterThanOrEqual(cardBox!.x - 1);
      expect(estimateBox!.x + estimateBox!.width).toBeLessThanOrEqual(cardBox!.x + cardBox!.width + 1);
      expect(estimateBox!.y + estimateBox!.height).toBeLessThanOrEqual(cardBox!.y + cardBox!.height + 1);
    }

    // The session-size pills (10 / 20 / until-clear) stay on one row at every width.
    const budgets = page.locator('.k3-session-budgets button');
    const firstTop = (await budgets.first().boundingBox())?.y;
    const lastTop = (await budgets.last().boundingBox())?.y;
    expect(firstTop).toBe(lastTop);
  }
});

test('A7: word cards render the level exactly once', async ({ page, context }) => {
  await context.clearCookies();
  await page.addInitScript(() => window.localStorage.setItem('lu-learner-level', 'A1'));
  await page.goto('/words-of-the-day/practice/');

  // Wait for the real daily deck (not the loading placeholder's bare "—" card).
  await expect(page.getByTestId('practice-daily-deck')).toBeVisible();
  const front = page.locator('.daily-preview-card .flashcard-front');
  await expect(front).toBeVisible();
  await expect(front).not.toHaveText('—');

  const occurrences = await front.evaluate(
    (node) => (node.textContent?.split('A1').length ?? 1) - 1,
  );
  expect(occurrences).toBe(1);
});
