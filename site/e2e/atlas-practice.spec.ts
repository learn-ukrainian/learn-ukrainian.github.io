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

/**
 * Opus P0-1 folded Drive sync + deck filter behind a `<details>` disclosure
 * (`data-testid="practice-secondary-tools"`), below the mode grid. Deck chips,
 * the "Manage Decks" action, and the switch-session-offer it can surface all
 * live inside that fold — open it before touching any of them. Idempotent: a
 * caller can invoke it repeatedly across deck switches within one test.
 */
async function openSecondaryTools(page: Page): Promise<void> {
  const panel = page.getByTestId('practice-secondary-tools');
  await expect(panel).toBeVisible();
  const open = await panel.getAttribute('open');
  if (open === null) {
    await panel.locator('summary').click();
  }
  await expect(panel).toHaveAttribute('open', '');
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

test('Atlas shell hides the 404 hero only for rendered word pages', async ({ page }) => {
  await page.goto('/lexicon/прапор/');
  await expect(page.locator('h1.word-title')).toBeVisible();
  await expect(page.locator('.lu-hero:visible').filter({ hasText: 'Page Not Found' })).toHaveCount(0);

  await page.goto('/definitely-not-a-real-page/');
  await expect(page.locator('.lu-hero:visible').filter({ hasText: 'Page Not Found' })).toHaveCount(1);
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

/**
 * #6544: the active deck must be discoverable above the fold without expanding
 * the folded Sync & decks panel (#6336 HARD-1/HARD-2 layout). Does not touch
 * mode-count assertions (those are owned by in-flight #6533).
 */
test('A4d: active-deck chip is visible above the fold without opening Sync & decks', async ({ page, context }) => {
  await context.clearCookies();
  await page.addInitScript(() => window.localStorage.setItem('lu-chrome-locale', 'en'));
  await page.setViewportSize({ width: 1366, height: 768 });
  await page.goto('/words-of-the-day/practice/');
  await page.waitForLoadState('networkidle');
  await page.evaluate(() => window.scrollTo(0, 0));

  const chip = page.getByTestId('practice-active-deck');
  await expect(chip).toBeVisible();
  await expect(page.getByTestId('practice-active-deck-chip')).toContainText(/All Words|Всі слова/);

  const secondary = page.getByTestId('practice-secondary-tools');
  await expect(secondary).toBeVisible();
  await expect(secondary).not.toHaveAttribute('open');

  const box = await chip.boundingBox();
  expect(box).not.toBeNull();
  expect(box!.y).toBeGreaterThanOrEqual(0);
  expect(box!.y + box!.height).toBeLessThanOrEqual(768);

  await page.getByTestId('practice-active-deck-chip').click();
  await expect(page.getByTestId('practice-active-deck-menu')).toBeVisible();
  await page.getByTestId('practice-deck-option-virtual_teacher_lesson').click();
  await expect(page.getByTestId('practice-active-deck-chip')).toContainText(/Curated Deck|Відібрана добірка/);
  await expect(page.getByTestId('practice-daily-deck-title')).toContainText('Curated Deck');
  // Switching via the above-fold menu must not force-open the bottom panel.
  await expect(secondary).not.toHaveAttribute('open');
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

test('Stress mode and ZNO decks remain available after choosing A2', async ({ page, context }) => {
  await context.clearCookies();
  await page.goto('/words-of-the-day/practice/');

  await page.getByRole('button', { name: 'A2' }).click();
  await expect(page.locator('button[data-mode="stress"]')).toBeVisible();
  await expect(page.locator('button[data-zno-deck="true"]')).toHaveCount(4);
  await expect(page.locator('button[data-mode]')).toHaveCount(15);
  await page.locator('button[data-mode="zno-orthography"]').click();
  await expect(page.getByTestId('practice-zno-session')).toBeVisible();
  await expect(page.getByTestId('zno-practice-item')).toBeVisible();
  await page.getByTestId('zno-practice-item').getByRole('button').first().click();
  await expect(page.getByTestId('zno-practice-verdict')).toBeVisible();
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

test('A1b: the Words-of-the-Day preview card renders a real word and gloss on real data, not "—" (#5852)', async ({ page, context }) => {
  await context.clearCookies();

  await page.addInitScript(() => window.localStorage.setItem('lu-learner-level', 'A1'));

  await page.goto('/words-of-the-day/practice/');

  const card = page.locator('.daily-preview-card');
  await expect(card).toBeVisible();
  const front = card.locator('.flashcard-front .flashcard-word');
  await expect(front).toBeVisible();
  await expect(front).not.toHaveText('—');
  expect(((await front.textContent()) ?? '').trim().length).toBeGreaterThan(0);

  await card.click();
  await expect(card).toHaveAttribute('data-flipped', 'true');
  const back = card.locator('.flashcard-back .flashcard-word');
  await expect(back).not.toHaveText('—');
  expect(((await back.textContent()) ?? '').trim().length).toBeGreaterThan(0);
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

/**
 * F1/F2 (PR #5837 review): route disjoint, single-item fixture decks for the A1/A2 core
 * shards so "the accepted level drives the session" is provable from ITEM CONTENT, not
 * merely from a request having fired for the right URL — a same-tick closure bug could
 * silently replay the stale level's pool while the request log still looks correct.
 * `depleteLowerLevel` is called right before the level switch so the (real, harmless)
 * background lower-level merge a higher level kicks off can never dilute the accepted
 * level's pool back into ambiguous territory.
 */
async function mockDisjointLevelFixtures(page: Page): Promise<{ depleteLowerLevel(level: 'A1' | 'A2'): void }> {
  const depleted = new Set<'A1' | 'A2'>();
  const fixtureItem = (level: 'A1' | 'A2') => ({
    lemmaId: `e2eFixture${level}`,
    lemma: `e2eFixture${level}`,
    cefr: level,
    modes: ['flashcards'] as const,
    hasCloze: false,
    clozeIds: [] as string[],
    newOrder: 0,
  });
  const fixtureLexeme = (level: 'A1' | 'A2') => ({
    lemmaId: `e2eFixture${level}`,
    lemma: `e2eFixture${level}`,
    lemmaPlain: `e2eFixture${level}`,
    ipa: null,
    gloss: `e2eFixture${level}`,
    pos: 'noun',
    cefr: level,
    heritage: null,
    severity: null,
    paradigm: { cases: {} },
  });
  for (const level of ['A1', 'A2'] as const) {
    await page.route(`**/lexicon/practice-index.${level}.json`, (route) =>
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          deckVersion: `e2e-fixture-${level}`,
          level,
          items: depleted.has(level) ? [] : [fixtureItem(level)],
        }),
      }),
    );
    await page.route(`**/lexicon/practice-lexemes.${level}.json`, (route) =>
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          deckVersion: `e2e-fixture-${level}`,
          level,
          lexemes: depleted.has(level) ? [] : [fixtureLexeme(level)],
        }),
      }),
    );
  }
  return { depleteLowerLevel: (level) => depleted.add(level) };
}

async function readMixedSessionSnapshot(
  page: Page,
): Promise<{ level?: string; deckId?: string; dateSeed?: number } | null> {
  return page.evaluate(() => {
    const raw = window.localStorage.getItem('lu-practice-session');
    return raw ? JSON.parse(raw).byMode?.mixed ?? null : null;
  });
}

test('A5: switching level with a session in progress offers a fresh session; accepting starts one from the chosen set', async ({ page, context }) => {
  await context.clearCookies();
  const fixtures = await mockDisjointLevelFixtures(page);
  await prepareResumableMixedSession(page);
  // The A1 setup session is over; deplete A1 so A2's background lower-level merge (which
  // always fetches A1 as a lower level) cannot reintroduce it into the accepted pool.
  fixtures.depleteLowerLevel('A1');
  // #6544: the switch-session offer lives above the fold next to the active-deck chip
  // (no longer buried inside practice-secondary-tools).

  await page.getByRole('button', { name: 'A2' }).click();

  const offer = page.getByTestId('practice-switch-session-offer');
  await expect(offer).toBeVisible();

  await page.getByTestId('practice-switch-session-accept').click();

  await expect(page.locator('.lexicon-practice-stage')).toBeVisible();
  await expect(page.getByTestId('practice-session-progress')).toContainText('0/');

  // F1/F2: the persisted snapshot must record the ACCEPTED level, and the first
  // presented item must be drawn from the ACCEPTED (A2) pool — not the stale A1 one.
  const snapshot = await readMixedSessionSnapshot(page);
  expect(snapshot?.level).toBe('A2');
  await expect(page.locator('.flashcard-word').first()).toContainText('e2eFixtureA2');
});

test('A5c: choosing a deck from the custom-deck manager while a session is active also offers a fresh session (finding 2 bypass)', async ({ page, context }) => {
  await context.clearCookies();
  await page.addInitScript(() => {
    window.localStorage.setItem(
      'learn_ukrainian_custom_sets_v1',
      JSON.stringify([
        {
          id: 'e2e-custom-deck',
          title: 'E2E Custom Deck',
          description: '',
          lemma_keys: ['e2eCustomDeckWord'],
          created_at: '2026-01-01T00:00:00.000Z',
          updated_at: '2026-01-01T00:00:00.000Z',
          device_id: 'e2e-device',
          revision: 1,
        },
      ]),
    );
  });
  await prepareResumableMixedSession(page);
  await openSecondaryTools(page);

  await page.getByRole('button', { name: /Manage Decks|Менеджер колод/ }).click();
  await page.getByRole('button', { name: /Practice|Практика/ }).first().click();

  // The custom-deck manager's own "Practice" action must route through the SAME guarded
  // switch flow as the level/deck chips — it must not silently swap the active deck out
  // from under the in-progress session (finding 2's bypass).
  const offer = page.getByTestId('practice-switch-session-offer');
  await expect(offer).toBeVisible();

  await page.getByTestId('practice-switch-session-accept').click();

  await expect(page.locator('.lexicon-practice-stage')).toBeVisible();
  // The custom deck has exactly one word that resolves to no Atlas/cloze content, so the
  // P0-3 mode-claim honesty fix in `ensureDeckCustomSetCoverage` only claims the one mode it
  // can actually deliver (flashcards) rather than promising modes with nothing behind them.
  // A mixed-mode session over ONE such word plans exactly 1 mode-card — wildly different from
  // a full-level session (hundreds of due/new cards) — proof the pool is the accepted deck,
  // not the full corpus.
  await expect(page.getByTestId('practice-session-progress')).toContainText('0/1');

  const snapshot = await readMixedSessionSnapshot(page);
  expect(snapshot?.deckId).toBe('e2e-custom-deck');
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

test('A6b: dashboard session estimate narrows to the selected custom deck before any session starts (PR #5837 fix-round-2)', async ({
  page,
  context,
}) => {
  await context.clearCookies();

  // Soft CEFR makes every published level eligible, so mock every index shard to keep the
  // full-level estimate deterministic: eight controlled A1 cards, no background-level drift.
  await page.route('**/lexicon/practice-index.*.json', (route) => {
    const { pathname } = new URL(route.request().url());
    const level = pathname.match(/practice-index\.([A-Z0-9]+)\.json$/)?.[1] ?? 'A1';
    const items = level === 'A1'
      ? ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'].map((suffix) => ({
          lemmaId: `e2eScope${suffix}`,
          lemma: `e2eScope${suffix}`,
          cefr: 'A1',
          modes: ['flashcards'],
          hasCloze: false,
          clozeIds: [],
          newOrder: 0,
        }))
      : [];
    return route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({ deckVersion: 'e2e-scope-fixture', level, items }),
    });
  });
  await page.addInitScript(() => {
    window.localStorage.setItem(
      'learn_ukrainian_custom_sets_v1',
      JSON.stringify([
        {
          id: 'e2e-scope-deck',
          title: 'E2E Scope Deck',
          description: '',
          lemma_keys: ['e2eScopea'],
          created_at: '2026-01-01T00:00:00.000Z',
          updated_at: '2026-01-01T00:00:00.000Z',
          device_id: 'e2e-device',
          revision: 1,
        },
      ]),
    );
  });

  await page.goto('/words-of-the-day/practice/');

  const estimate = page.getByTestId('practice-session-scope');
  // Before selecting the custom deck, the estimate reports the full-level soft-CEFR scope.
  await expect(estimate).toContainText('8 нових');

  await openSecondaryTools(page);
  await page.getByRole('button', { name: /E2E Scope Deck/ }).click();

  // F1-F3 (PR #5837) scoped the two SESSION-start paths to the chosen deck via
  // filterIndexByDeckFilter; the dashboard estimate — visible before a session even
  // starts — must narrow the same way, not keep describing the unfiltered level.
  await expect(estimate).toContainText('1 нов');
});

test('A7: word cards render the level exactly once', async ({ page, context }) => {
  await context.clearCookies();
  await page.addInitScript(() => window.localStorage.setItem('lu-learner-level', 'A1'));
  // Learner level is soft guidance: the real date-seeded pool may legitimately
  // put an A2+ word first. Freeze this assertion's input so it tests duplicate
  // CEFR rendering rather than today's selection order.
  await page.route('**/lexicon/daily-pool.json', (route) =>
    route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify([
        { lemma: 'слово', slug: 'a7-level-once', gloss: 'word', cefr: 'A1' },
      ]),
    }),
  );
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

// --- D10 (design delta amendment, 2026-07-27): deck-scoped daily picks ---

function customSetFixture(id: string, title: string, lemmaKeys: string[]) {
  return {
    id,
    title,
    description: '',
    lemma_keys: lemmaKeys,
    created_at: '2026-01-01T00:00:00.000Z',
    updated_at: '2026-01-01T00:00:00.000Z',
    device_id: 'e2e-device',
    revision: 1,
  };
}

test('A8a: an Atlas-only custom-deck key gets its gloss and route while a true orphan stays unlinked', async ({
  page,
  context,
}) => {
  await context.clearCookies();
  const catDeck = customSetFixture('e2e-d10-cat', 'E2E D10 Cat Deck', ['кіт']);
  const orphanDeck = customSetFixture('e2e-d10-orphan', 'E2E D10 Orphan Deck', ['вигаданий термін']);
  await page.route(/\/lexicon\/practice-(index|lexemes|cloze)\.(A1|A2|B1|B2|C1)\.json$/, async (route) => {
    const { pathname } = new URL(route.request().url());
    if (pathname.endsWith('practice-index.A1.json')) {
      await route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          deckVersion: 'e2e-d10',
          level: 'A1',
          items: [],
        }),
      });
      return;
    }
    if (pathname.endsWith('practice-lexemes.A1.json')) {
      await route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({ deckVersion: 'e2e-d10', level: 'A1', lexemes: [] }),
      });
      return;
    }
    if (pathname.endsWith('practice-cloze.A1.json')) {
      await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ cloze: [] }) });
      return;
    }
    await route.fulfill({ status: 404, contentType: 'application/json', body: '{}' });
  });
  await page.route('**/lexicon/search-shards.json', (route) =>
    route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        schema: 'atlas-search-shards',
        schemaVersion: 1,
        total: 1,
        shardCount: 1,
        fullIndex: { path: '/lexicon/search-index.json', count: 1, bytes: 1, sha256: 'full' },
        prefixMap: { к: 'u043a' },
        shards: { u043a: { path: '/lexicon/search/u043a.json', count: 1, bytes: 1, sha256: 'cat' } },
      }),
    }),
  );
  await page.route('**/lexicon/search/u043a.json', (route) =>
    route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify([{ l: 'кіт', s: 'кіт', g: 'cat', t: 'lemma', c: 'A1' }]),
    }),
  );
  await page.addInitScript(([catSet, orphanSet]) => {
    window.localStorage.setItem('lu-learner-level', 'A1');
    window.localStorage.setItem('learn_ukrainian_custom_sets_v1', JSON.stringify([catSet, orphanSet]));
  }, [catDeck, orphanDeck] as const);

  await page.goto('/words-of-the-day/practice/');
  await openSecondaryTools(page);

  await page.getByRole('button', { name: /E2E D10 Cat Deck/ }).click();
  await expect(page.getByTestId('practice-daily-deck-title')).toContainText('E2E D10 Cat Deck');
  const catCard = page.locator('.daily-preview-card');
  await expect(catCard).toContainText('кіт');
  await expect(page.getByTestId('practice-preview-atlas-link')).toHaveAttribute(
    'href',
    '/lexicon/%D0%BA%D1%96%D1%82/',
  );
  await catCard.click();
  await expect(catCard).toContainText('cat');
  await expect(catCard).not.toContainText('noun');

  await page.getByRole('button', { name: /E2E D10 Orphan Deck/ }).click();
  await expect(page.getByTestId('practice-daily-deck-title')).toContainText('E2E D10 Orphan Deck');
  await expect(page.locator('.daily-preview-card')).toContainText('вигаданий термін');
  await expect(page.getByTestId('practice-preview-atlas-link')).toHaveCount(0);

  await page.getByRole('button', { name: /E2E D10 Cat Deck/ }).click();
  // The daily card is only the preview path. Start a real flashcard session
  // and reveal its back so the deck's committed lexeme, not preview state,
  // proves the Atlas shard enrichment reached `cardData()`.
  await page.locator('button[data-mode="flashcards"]').click();
  const sessionCard = page.locator('[data-activity="flashcard"]');
  await expect(sessionCard).toBeVisible();
  await sessionCard.click();
  await expect(sessionCard.locator('.flashcard-back .flashcard-word')).toHaveText('cat');
  await expect(sessionCard.locator('.flashcard-subtitle')).toHaveCount(0);
});

/** Opens the daily-zone disclosure (idempotent — `PracticeDailyDeck` can remount and
 * reset `detailsOpen` across a deck switch) and reads the full featured word list. */
async function readDailyDeckWords(page: Page): Promise<string[]> {
  await expect(page.getByTestId('practice-daily-deck')).toBeVisible();
  const summary = page.getByTestId('practice-daily-summary');
  if ((await summary.getAttribute('aria-expanded')) !== 'true') {
    await summary.click();
  }
  const rows = page.locator('.daily-deck-row .row-lemma');
  await expect(rows.first()).toBeVisible();
  return rows.allTextContents();
}

test('A8: two different custom decks show different daily-zone sets, each drawn from its own deck', async ({
  page,
  context,
}) => {
  await context.clearCookies();
  const deckAlpha = customSetFixture('e2e-d10-alpha', 'E2E D10 Alpha Deck', [
    'e2eD10Alpha1',
    'e2eD10Alpha2',
    'e2eD10Alpha3',
  ]);
  const deckBeta = customSetFixture('e2e-d10-beta', 'E2E D10 Beta Deck', [
    'e2eD10Beta1',
    'e2eD10Beta2',
    'e2eD10Beta3',
  ]);
  await page.addInitScript(
    ([alpha, beta]) => {
      window.localStorage.setItem('learn_ukrainian_custom_sets_v1', JSON.stringify([alpha, beta]));
    },
    [deckAlpha, deckBeta] as const,
  );

  await page.goto('/words-of-the-day/practice/');
  await openSecondaryTools(page);

  await page.getByRole('button', { name: /E2E D10 Alpha Deck/ }).click();
  await expect(page.getByTestId('practice-daily-deck-title')).toContainText('E2E D10 Alpha Deck');
  const alphaWords = await readDailyDeckWords(page);
  // Both fixture decks have fewer than 12 words — the zone shows all of them (D10 edge case).
  expect(new Set(alphaWords)).toEqual(new Set(deckAlpha.lemma_keys));

  await page.getByRole('button', { name: /E2E D10 Beta Deck/ }).click();
  await expect(page.getByTestId('practice-daily-deck-title')).toContainText('E2E D10 Beta Deck');
  const betaWords = await readDailyDeckWords(page);
  expect(new Set(betaWords)).toEqual(new Set(deckBeta.lemma_keys));

  expect(alphaWords.some((word) => betaWords.includes(word))).toBe(false);
});

test('A9a: a deck-scoped daily set is stable within a day and rotates across days', async ({ page, context }) => {
  await context.clearCookies();
  const words = Array.from({ length: 20 }, (_, i) => `e2eD10Rot${i}`);
  const deck = customSetFixture('e2e-d10-rot', 'E2E D10 Rotation Deck', words);
  await page.addInitScript((set) => {
    window.localStorage.setItem('learn_ukrainian_custom_sets_v1', JSON.stringify([set]));
  }, deck);

  async function selectDeckAndReadWords(clockTime: string): Promise<string[]> {
    await page.clock.setFixedTime(new Date(clockTime));
    await page.goto('/words-of-the-day/practice/');
    await openSecondaryTools(page);
    await page.getByRole('button', { name: /E2E D10 Rotation Deck/ }).click();
    await expect(page.getByTestId('practice-daily-deck-title')).toContainText('E2E D10 Rotation Deck');
    return readDailyDeckWords(page);
  }

  await page.clock.install({ time: new Date('2026-07-20T12:00:00.000Z') });
  const day1First = await selectDeckAndReadWords('2026-07-20T12:00:00.000Z');
  expect(day1First.length).toBe(12);

  // Same calendar day, different time of day: stability.
  const day1Second = await selectDeckAndReadWords('2026-07-20T18:00:00.000Z');
  expect(new Set(day1Second)).toEqual(new Set(day1First));

  // A different calendar day: rotation (20-word pool makes a same-12 collision negligible).
  const day2 = await selectDeckAndReadWords('2026-07-21T12:00:00.000Z');
  expect(new Set(day2)).not.toEqual(new Set(day1First));
});

test('A9b: the All-Words daily set is stable within a day and rotates across days', async ({ page, context }) => {
  await context.clearCookies();
  await page.addInitScript(() => window.localStorage.setItem('lu-learner-level', 'A1'));

  async function readAllWordsAt(clockTime: string): Promise<string[]> {
    await page.clock.setFixedTime(new Date(clockTime));
    await page.goto('/words-of-the-day/practice/');
    return readDailyDeckWords(page);
  }

  await page.clock.install({ time: new Date('2026-07-20T12:00:00.000Z') });
  const day1First = await readAllWordsAt('2026-07-20T12:00:00.000Z');
  expect(day1First.length).toBeGreaterThan(0);

  const day1Second = await readAllWordsAt('2026-07-20T18:00:00.000Z');
  expect(new Set(day1Second)).toEqual(new Set(day1First));

  const day2 = await readAllWordsAt('2026-07-21T12:00:00.000Z');
  expect(new Set(day2)).not.toEqual(new Set(day1First));
});

test.describe('daily preview UTC boundary', () => {
  test.use({ timezoneId: 'UTC' });

  test('keeps a displayable daily card on both sides of midnight when the pool has orphaned rows', async ({ page, context }) => {
    await context.clearCookies();
    const dailyPool = [
      { lemma: 'видиме-один', slug: 'visible-one', gloss: 'visible one', cefr: 'A1' },
      { lemma: 'видиме-два', slug: 'visible-two', gloss: 'visible two', cefr: 'A1' },
      { lemma: 'сирота', slug: 'orphaned-row', gloss: 'orphaned row', cefr: 'A1' },
    ];
    const lexemes = dailyPool.slice(0, 2).map((word) => ({
      lemmaId: word.slug,
      lemma: word.lemma,
      lemmaPlain: word.lemma,
      ipa: null,
      gloss: word.gloss,
      pos: 'noun',
      cefr: word.cefr,
      heritage: null,
      severity: null,
      paradigm: { cases: {} },
    }));

    await page.route('**/lexicon/daily-pool.json', (route) =>
      route.fulfill({ contentType: 'application/json', body: JSON.stringify(dailyPool) }),
    );
    await page.route('**/lexicon/practice-lexemes.A1.json', (route) =>
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({ deckVersion: 'daily-boundary-fixture', level: 'A1', lexemes }),
      }),
    );
    await page.clock.install({ time: new Date('2026-07-26T23:55:00.000Z') });
    await page.addInitScript(() => {
      window.localStorage.clear();
      window.localStorage.setItem('lu-learner-level', 'A1');
    });

    for (const { instant, expectedWord } of [
      { instant: '2026-07-26T23:55:00.000Z', expectedWord: 'видиме-два' },
      { instant: '2026-07-27T00:05:00.000Z', expectedWord: 'сирота' },
    ]) {
      await page.clock.setFixedTime(new Date(instant));
      await page.goto('/words-of-the-day/practice/');

      const front = page.locator('.daily-preview-card .flashcard-front');
      await expect(page.getByTestId('practice-daily-deck')).toBeVisible();
      await expect(front).toContainText(expectedWord);
      await expect(front).not.toHaveText('—');
    }
  });
});
