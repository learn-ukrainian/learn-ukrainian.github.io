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
  await page.goto('/practice/');

  await page.locator('button[data-mode="cloze"]').click();
  // Cloze is fail-closed until reviewed sentences are authored (#3797). The mode must show a
  // real cloze card OR a clear "being prepared" message — never the ambiguous "all done"
  // dead-end the user reported. This invariant holds before AND after cloze content lands.
  const clozeCard = page.locator('[data-testid="practice-cloze"]');
  const clozeEmpty = page.locator('[data-testid="practice-cloze-empty"]');
  await expect(clozeCard.or(clozeEmpty)).toBeVisible();
});

test('practice matching renders a real round (>=3 pairs) for a fresh learner', async ({ page }) => {
  await page.goto('/practice/');

  await page.locator('button[data-mode="matching"]').click();
  await expect(page.locator('[data-testid="practice-matching"]')).toBeVisible();
  await expect.poll(() => page.locator('[data-activity="match-left-tile"]').count()).toBeGreaterThanOrEqual(3);
});

test('practice mode switch starts the selected mode without inheriting the unfinished one', async ({ page }) => {
  await page.goto('/practice/');

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
  ['/practice/', 'plain practice page'],
  ['/practice/?lemmaId=%D0%BA%D0%B0%D0%B2%D0%B0', 'deep-link practice page'],
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

  await page.goto('/practice/');

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
  await page.goto('/practice/');
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
  await page.goto('/practice/');
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
  await page.goto('/practice/');
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
  await page.goto('/practice/');
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
  await page.goto('/practice/');

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
  await page.goto('/practice/');

  await page.getByRole('button', { name: 'A2' }).click();
  await expect(page.locator('button[data-mode="stress"]')).toBeVisible();
  // ZNO deck count tracks ZNO_PRACTICE_DECK_META (site/src/components/ZnoPractice.tsx);
  // update both counts together when decks are added/removed.
  await expect(page.locator('button[data-zno-deck="true"]')).toHaveCount(9);
  await expect(page.locator('button[data-mode]')).toHaveCount(20);
  await page.locator('button[data-mode="zno-orthography"]').click();
  await expect(page.getByTestId('practice-zno-session')).toBeVisible();
  await expect(page.getByTestId('zno-practice-item')).toBeVisible();
  await page.getByTestId('zno-practice-item').getByRole('button').first().click();
  await expect(page.getByTestId('zno-practice-verdict')).toBeVisible();
});

test('practice flashcard rating locks the card and waits for explicit next', async ({ page, context }) => {
  await context.clearCookies();
  await page.goto('/practice/');

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
  await page.goto('/practice/');
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

  await page.goto('/practice/');
  await page.getByTestId('practice-daily-summary').click();
  const practiceLemmas = await page.locator('.daily-deck-row .row-lemma').allTextContents();

  expect(practiceLemmas.length).toBe(atlasLemmas.length);
  expect(new Set(practiceLemmas)).toEqual(new Set(atlasLemmas));
});

test('A1b: the Words-of-the-Day preview card renders a real word and gloss on real data, not "—" (#5852)', async ({ page, context }) => {
  await context.clearCookies();

  await page.addInitScript(() => window.localStorage.setItem('lu-learner-level', 'A1'));

  await page.goto('/practice/');

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
    await page.goto('/practice/');
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
  await page.goto('/practice/');

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
    await page.goto('/practice/');

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

  await page.goto('/practice/');

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
  await page.goto('/practice/');

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

  await page.goto('/practice/');
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

  await page.goto('/practice/');
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
    await page.goto('/practice/');
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
    await page.goto('/practice/');
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
      await page.goto('/practice/');

      const front = page.locator('.daily-preview-card .flashcard-front');
      await expect(page.getByTestId('practice-daily-deck')).toBeVisible();
      await expect(front).toContainText(expectedWord);
      await expect(front).not.toHaveText('—');
    }
  });
});

test('practice hub renders 3-track layout, launches 10 POS mechanics drill, and toggles settings drawer', async ({ page }) => {
  await page.goto('/practice/');

  // 1. Verify Track 2 & 10 POS Mechanics grid
  const grammarTrack = page.getByTestId('practice-track-grammar');
  await expect(grammarTrack).toBeVisible();

  const nounCard = page.getByTestId('practice-card-mechanics-noun');
  await expect(nounCard).toBeVisible();

  // 2. Launch noun mechanics drill
  await nounCard.click();
  const session = page.getByTestId('practice-mechanics-session');
  await expect(session).toBeVisible();
  await expect(page.getByTestId('practice-mechanics-prompt')).toBeVisible();

  // Return back to tracks
  await page.getByTestId('practice-mechanics-back-button').click();
  await expect(session).toHaveCount(0);
  await expect(grammarTrack).toBeVisible();

  // 3. Settings drawer toggle
  const settingsToggle = page.getByTestId('practice-settings-toggle');
  await expect(settingsToggle).toBeVisible();
  await settingsToggle.click();

  const drawer = page.getByTestId('practice-settings-drawer');
  await expect(drawer).toHaveClass(/open/);
  await expect(page.getByTestId('practice-settings-backdrop')).toBeVisible();

  // Close drawer
  await page.getByTestId('settings-drawer-close').click();
  await expect(drawer).not.toHaveClass(/open/);
  await expect(page.getByTestId('practice-settings-backdrop')).toHaveCount(0);
});

test('seeded localStorage progress survives the move to /practice/ (#8328)', async ({ page }) => {
  const today = new Date();
  const lastPracticeDate = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
  await page.addInitScript((date) => {
    window.localStorage.setItem('lu-learner-level', 'B1');
    window.localStorage.setItem(
      'lu-lexicon-practice-streak',
      JSON.stringify({ version: 1, current: 5, lastPracticeDate: date }),
    );
  }, lastPracticeDate);

  await page.goto('/practice/');

  await expect(page.locator('.k3-levels button[aria-pressed="true"]')).toHaveText(/B1/);
  await expect(page.locator('.k3-stat-value', { hasText: '🔥' })).toHaveText('🔥 5');
  expect(await page.evaluate(() => window.localStorage.getItem('lu-learner-level'))).toBe('B1');
});

for (const oldPath of ['/words-of-the-day/practice/', '/lexicon/practice/']) {
  test(`legacy URL ${oldPath} redirects to /practice/ (#8328)`, async ({ page }) => {
    await page.goto(oldPath);
    await page.waitForURL((url) => url.pathname === '/practice/');
    expect(new URL(page.url()).pathname).toBe('/practice/');
  });
}

test('saved learning progress (SRS reviews and in-progress session) survives legacy redirect to /practice/ (#8328)', async ({ page, context }) => {
  test.setTimeout(60000);
  await context.clearCookies();
  // 1. Prepare an active session with real progress and reviews
  await prepareResumableMixedSessionWithProgress(page);

  // Read stored session and SRS state before navigation
  const sessionBefore = await page.evaluate(() => window.localStorage.getItem('lu-practice-session'));
  const srsBefore = await page.evaluate(() => window.localStorage.getItem('lu-lexicon-srs'));
  expect(sessionBefore).not.toBeNull();
  expect(srsBefore).not.toBeNull();

  // Verify dashboard offers resume button
  const resumeBtn = page.getByRole('button', { name: /Продовжити|Resume/ });
  await expect(resumeBtn).toBeVisible();

  // 2. Navigate via legacy redirect URL (/words-of-the-day/practice/)
  await page.goto('/words-of-the-day/practice/');
  await page.waitForURL((url) => url.pathname === '/practice/');
  expect(new URL(page.url()).pathname).toBe('/practice/');

  // 3. Verify retained reviews and session progress
  const sessionAfter = await page.evaluate(() => window.localStorage.getItem('lu-practice-session'));
  const srsAfter = await page.evaluate(() => window.localStorage.getItem('lu-lexicon-srs'));
  expect(sessionAfter).toBe(sessionBefore);
  expect(srsAfter).toBe(srsBefore);

  // 4. Resume the session and verify progress was retained (1/, not 0/)
  const resumeAfterRedirect = page.getByRole('button', { name: /Продовжити|Resume/ });
  await expect(resumeAfterRedirect).toBeVisible();
  await resumeAfterRedirect.click();

  await expect(page.locator('.lexicon-practice-stage')).toBeVisible();
  await expect(page.getByTestId('practice-session-progress')).toContainText('1/');
});

// #10706 binds the WAV's declared або / або́ identity, not pronunciation quality.
const AUDIO_FILE = 'f451ecae99efb39c3af48fd70b23edfa00d22ce483cc9f0c525200f286f6b7fb.wav';
const AUDIO_FIXTURE = new URL('../../tests/fixtures/audio/pronunciation.wav', import.meta.url).pathname;
type AudioObservation = { element: HTMLMediaElement; events: string[]; promises: string[]; times: number[] };
declare global {
  interface Window {
    practiceAudioProbe: { media: AudioObservation[]; loop: boolean; speech: { lang: string; text: string; local: boolean; events: string[] }[] };
  }
}
async function observePracticeAudio(page: Page, loop = false): Promise<void> {
  await page.addInitScript(({ loop }) => {
    localStorage.setItem('lu-chrome-locale', 'en');
    localStorage.setItem('lu-learner-level', 'A1');
    window.practiceAudioProbe = { media: [], speech: [], loop };
    const nativePause = HTMLMediaElement.prototype.pause;
    HTMLMediaElement.prototype.pause = function () {
      window.practiceAudioProbe.media.find((entry) => entry.element === this)?.events.push('pause()');
      nativePause.call(this);
    };
    const nativePlay = HTMLMediaElement.prototype.play;
    HTMLMediaElement.prototype.play = function () {
      let record = window.practiceAudioProbe.media.find((entry) => entry.element === this);
      if (!record) {
        const observed = { element: this, events: [] as string[], promises: [] as string[], times: [] as number[] };
        record = observed;
        window.practiceAudioProbe.media.push(observed);
        for (const name of ['playing', 'pause', 'ended', 'error', 'timeupdate', 'emptied']) this.addEventListener(name, () => {
          observed.events.push(name);
          observed.times.push(this.currentTime);
        });
      }
      this.loop = window.practiceAudioProbe.loop;
      const observed = record;
      const promise = nativePlay.call(this);
      void promise.then(() => observed.promises.push('fulfilled'), (error: unknown) => observed.promises.push(error instanceof DOMException ? error.name : String(error)));
      return promise;
    };
    if (window.speechSynthesis) {
      const nativeSpeak = speechSynthesis.speak.bind(speechSynthesis);
      speechSynthesis.speak = (utterance) => {
        const record = { lang: utterance.lang, text: utterance.text, local: utterance.voice?.localService === true, events: [] as string[] };
        window.practiceAudioProbe.speech.push(record);
        if (!record.local) throw new Error('Remote speech is outside #10706 execution');
        for (const name of ['start', 'end', 'error']) utterance.addEventListener(name, () => record.events.push(name));
        nativeSpeak(utterance);
      };
    }
  }, { loop });
  // Specific fixture routes override this refusal before any navigation.
  await page.route('**/*', (route) => new URL(route.request().url()).hostname === '127.0.0.1' ? route.continue() : route.abort());
}
async function audioPracticeFixture(page: Page, second = false): Promise<void> {
  for (const level of ['A1', 'A2', 'B1', 'B2', 'C1']) {
    const lexemes = level === 'A1' ? [
      { lemmaId: 'або', lemma: 'або́', lemmaPlain: 'або', cefr: level, gloss: 'fixture identity', pos: 'conj', ipa: null, heritage: null, severity: null, paradigm: { cases: {} } },
    ] : level === 'A2' && second ? [
      { lemmaId: 'audio-next-control', lemma: 'audio-next-control', lemmaPlain: 'audio-next-control', cefr: level, gloss: 'next control', pos: 'noun', ipa: null, heritage: null, severity: null, paradigm: { cases: {} } },
    ] : [];
    await page.route(`**/lexicon/practice-index.${level}.json`, (route) => route.fulfill({ json: {
      deckVersion: '10706-audio-native-v1', level,
      items: lexemes.map((word, newOrder) => ({ lemmaId: word.lemmaId, lemma: word.lemma, cefr: level, modes: ['flashcards'], hasCloze: false, clozeIds: [], newOrder })),
    } }));
    await page.route(`**/lexicon/practice-lexemes.${level}.json`, (route) => route.fulfill({ json: { deckVersion: '10706-audio-native-v1', level, lexemes } }));
    await page.route(`**/lexicon/practice-cloze.${level}.json`, (route) => route.fulfill({ json: { cloze: [] } }));
  }
}
async function routeGoodAudio(page: Page): Promise<void> {
  await page.route('**/manifest.json', (route) => route.fulfill({ json: { schemaVersion: 1, entries: { 'або': { file: AUDIO_FILE } } } }));
  await page.route(`**/${AUDIO_FILE}`, (route) => route.fulfill({ path: AUDIO_FIXTURE, contentType: 'audio/wav', headers: { 'Cache-Control': 'no-store' } }));
}
async function openAudioPractice(page: Page, second = false): Promise<void> {
  await audioPracticeFixture(page, second);
  const manifest = page.waitForResponse((response) => response.url().endsWith('/manifest.json'));
  await page.goto('/practice/');
  await page.locator('button[data-mode="flashcards"]').click();
  await expect(page.locator('[data-pronunciation-lemma]')).toHaveAttribute('data-pronunciation-lemma', 'або́');
  await manifest;
  await page.evaluate(() => new Promise<void>((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
}
function audioButton(page: Page) { return page.locator('[data-pronunciation-lemma] button'); }
async function audioLearningState(page: Page) {
  return {
    flipped: await page.locator('[data-activity="flashcard"]').getAttribute('data-flipped'),
    rated: await page.locator('[data-activity="flashcard"]').getAttribute('data-rated'),
    progress: await page.getByTestId('practice-session-progress').textContent(),
    saved: await page.evaluate(() => ({ srs: localStorage.getItem('lu-lexicon-srs'), session: localStorage.getItem('lu-practice-session') })),
  };
}
async function nativePlaying(page: Page): Promise<void> {
  await expect.poll(() => page.evaluate(() => window.practiceAudioProbe.media.some((record) =>
    record.events.includes('playing') && record.promises.includes('fulfilled') && !record.element.paused && record.element.currentTime > 0,
  ))).toBe(true);
  await expect(audioButton(page)).toHaveText('Stop pronunciation');
  await expect(audioButton(page)).toHaveAttribute('aria-busy', 'false');
  await expect(page.locator('[data-pronunciation-lemma] [role="status"]')).toBeEmpty();
}
async function oldAudioStopped(page: Page): Promise<void> {
  await expect.poll(() => page.evaluate(() => {
    const record = window.practiceAudioProbe.media[0];
    return { paused: record.element.paused, time: record.element.currentTime, pauseCalled: record.events.includes('pause()') };
  })).toEqual({ paused: true, time: 0, pauseCalled: true });
}

async function observedAudioVoices(page: Page) {
  return page.evaluate(async () => {
    if (!window.speechSynthesis) return { supported: false, voices: [] };
    let previous = '';
    let stable = 0;
    for (let i = 0; i < 20; i++) {
      const inventory = speechSynthesis.getVoices().map((voice) => ({ lang: voice.lang, name: voice.name, local: voice.localService }));
      const fingerprint = JSON.stringify(inventory);
      stable = fingerprint === previous ? stable + 1 : 0;
      previous = fingerprint;
      if (stable >= 5) return { supported: true, voices: inventory };
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
    throw new Error('Native speech inventory kept changing during observation');
  });
}

async function assertNativeFallback(page: Page) {
  const inventory = await observedAudioVoices(page);
  await test.info().attach('native-voice-inventory.json', { body: JSON.stringify(inventory), contentType: 'application/json' });
  const localUkrainian = inventory.voices.some((voice) => voice.local && voice.lang.toLowerCase().startsWith('uk'));
  const before = await audioLearningState(page);
  await audioButton(page).click();
  if (localUkrainian) {
    await expect.poll(() => page.evaluate(() => window.practiceAudioProbe.speech.some((entry) => entry.local && entry.lang === 'uk-UA' && entry.events.includes('start')))).toBe(true);
  } else if (inventory.supported && inventory.voices.length === 0) {
    await expect(audioButton(page)).toHaveAccessibleName('Stop pronunciation');
    await expect(audioButton(page)).toHaveAttribute('aria-busy', 'true');
    await expect(page.locator('[data-pronunciation-lemma] [role="status"]')).toBeEmpty();
    expect(await page.evaluate(() => window.practiceAudioProbe.speech)).toEqual([]);
    test.info().annotations.push({ type: 'native-empty-catalog', description: 'UNKNOWN: the API cannot distinguish an empty catalog from one still loading; request stays cancellable' });
    await audioButton(page).click();
    await expect(audioButton(page)).toHaveText('Play pronunciation');
    await expect(audioButton(page)).toHaveAttribute('aria-busy', 'false');
  } else {
    await expect(page.locator('[data-pronunciation-lemma] [role="status"]')).toHaveText('Audio unavailable. Try again.');
    await expect(audioButton(page)).toHaveText('Play pronunciation');
    expect(await page.evaluate(() => window.practiceAudioProbe.speech)).toEqual([]);
  }
  expect(await audioLearningState(page)).toEqual(before);
  return inventory;
}

async function audioOverlappingLevel(page: Page, rawLemma = 'або́') {
  await page.route('**/lexicon/practice-index.A2.json', (route) => route.fulfill({ json: {
    deckVersion: '10706-overlap-v1', level: 'A2', items: [{ lemmaId: 'або', lemma: rawLemma, cefr: 'A2', modes: ['flashcards'], hasCloze: false, clozeIds: [], newOrder: 0 }],
  } }));
  await page.route('**/lexicon/practice-lexemes.A2.json', (route) => route.fulfill({ json: {
    deckVersion: '10706-overlap-v1', level: 'A2', lexemes: [{ lemmaId: 'або', lemma: rawLemma, lemmaPlain: 'або', cefr: 'A2', gloss: 'fixture identity', pos: 'conj', ipa: null, heritage: null, severity: null, paradigm: { cases: {} } }],
  } }));
}

async function audioAnimationFrame(page: Page) {
  await page.evaluate(() => new Promise<void>((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
}

async function lateNativeFailure(page: Page) {
  const previousErrors = await page.evaluate(() => window.practiceAudioProbe.media[0].events.filter((event) => event === 'error').length);
  await page.evaluate(async () => {
    const old = window.practiceAudioProbe.media[0].element;
    old.src = '/audio/pronunciation/prior-attempt-invalid.wav';
    old.load();
    await old.play().catch(() => {});
  });
  await expect.poll(() => page.evaluate(() => window.practiceAudioProbe.media[0].events.filter((event) => event === 'error').length)).toBe(previousErrors + 1);
  await expect.poll(() => page.evaluate(() => window.practiceAudioProbe.media[0].promises)).toContain('NotSupportedError');
  await nativePlaying(page);
}

test.describe('#10706 audio:', () => {
  test.afterEach(async ({ page }, info) => {
    const observation = await page.evaluate(() => ({
      url: location.pathname,
      media: window.practiceAudioProbe?.media.map((record) => ({
        events: record.events, promises: record.promises, times: record.times,
        src: record.element.currentSrc || record.element.src, paused: record.element.paused,
        time: record.element.currentTime, duration: record.element.duration, error: record.element.error?.code,
      })),
      speech: window.practiceAudioProbe?.speech,
    })).catch(() => ({ unavailable: true }));
    await info.attach('native-observation.json', { body: JSON.stringify(observation), contentType: 'application/json' });
  });

  for (const activation of ['pointer', 'Enter', 'Space'] as const) {
    test(`P01 playback and completion / ${activation}`, async ({ page }) => {
      await observePracticeAudio(page);
      await routeGoodAudio(page);
      await openAudioPractice(page);
      expect(await page.evaluate(() => window.practiceAudioProbe.media)).toEqual([]);
      const before = await audioLearningState(page);
      if (activation === 'pointer') await audioButton(page).click();
      else { await audioButton(page).focus(); await page.keyboard.press(activation); }
      await nativePlaying(page);
      const decoded = await page.evaluate(() => {
        const record = window.practiceAudioProbe.media[0];
        return { resource: new URL(record.element.currentSrc).pathname, duration: record.element.duration };
      });
      expect(decoded.resource).toBe(`/audio/pronunciation/${AUDIO_FILE}`);
      expect(decoded.duration).toBeCloseTo(9728 / 22050, 5);
      expect(await audioLearningState(page)).toEqual(before);
      await expect.poll(() => page.evaluate(() => window.practiceAudioProbe.media[0].events)).toContain('ended');
      await expect(audioButton(page)).toHaveText('Play pronunciation');
      expect(await audioLearningState(page)).toEqual(before);
    });
  }

  test('P02 explicit native stop resets playback', async ({ page }) => {
    await observePracticeAudio(page, true);
    await routeGoodAudio(page);
    await openAudioPractice(page);
    const before = await audioLearningState(page);
    await audioButton(page).click();
    await nativePlaying(page);
    await audioButton(page).click();
    await oldAudioStopped(page);
    await expect(audioButton(page)).toHaveText('Play pronunciation');
    expect(await audioLearningState(page)).toEqual(before);
  });

  test('P04 Home cancels and dashboard has the six active-stage switch N/A counterparts', async ({ page }) => {
    await observePracticeAudio(page, true);
    await routeGoodAudio(page);
    await openAudioPractice(page);
    await audioButton(page).click();
    await nativePlaying(page);
    expect(await page.locator('.lexicon-practice-stage').count()).toBe(1);
    expect(await page.locator('.k3-levels:visible').count()).toBe(0);
    expect(await page.getByTestId('practice-settings-toggle').count()).toBe(0);
    expect(await page.getByTestId('practice-active-deck').count()).toBe(0);
    await page.getByRole('button', { name: /Додому|Home/ }).click();
    await oldAudioStopped(page);
    await expect(page.getByTestId('practice-start-session')).toBeVisible();
    await expect(page.getByTestId('practice-settings-toggle')).toBeVisible();
    await expect(page.locator('.k3-levels')).toBeVisible();
    await test.info().attach('active-switch-applicability.json', { body: JSON.stringify({ activeStage: 1, deck: 0, level: 0, settings: 0, activeVariants: 'N/A, six dashboard counterparts remain mandatory' }), contentType: 'application/json' });
  });

  test('P04 real header locale rebind cancels without changing learner level or review', async ({ page }) => {
    await observePracticeAudio(page, true);
    await routeGoodAudio(page);
    await openAudioPractice(page);
    const before = await audioLearningState(page);
    await audioButton(page).click();
    await nativePlaying(page);
    await page.locator('#lu-locale-toggle').click();
    await oldAudioStopped(page);
    await expect(audioButton(page)).toHaveText('Послухати вимову');
    expect(await audioLearningState(page)).toEqual(before);
    expect(await page.evaluate(() => localStorage.getItem('lu-learner-level'))).toBe('A1');
  });

  for (const kind of ['deck', 'level'] as const) {
    for (const disposition of ['accept different item', 'accept reused item', 'decline'] as const) {
      test(`P04 Home then ${kind} switch / ${disposition}, resumable Mixed`, async ({ page }) => {
        const reused = disposition === 'accept reused item';
        await observePracticeAudio(page, true);
        await routeGoodAudio(page);
        await audioPracticeFixture(page, true);
        if (reused) await audioOverlappingLevel(page);
        await page.addInitScript(({ reused }) => {
          localStorage.setItem('learn_ukrainian_custom_sets_v1', JSON.stringify([{
            id: 'audio-switch-target', title: 'Audio switch fixture', description: '',
            lemma_keys: [reused ? 'або' : 'audio-next-control'],
            created_at: '2026-01-01T00:00:00.000Z', updated_at: '2026-01-01T00:00:00.000Z', device_id: 'audio-fixture', revision: 1,
          }]));
        }, { reused });
        await page.goto('/practice/');
        await page.getByTestId('practice-start-session').click();
        await expect(page.locator('[data-pronunciation-lemma]')).toHaveAttribute('data-pronunciation-lemma', 'або́');
        await audioAnimationFrame(page);
        const before = await audioLearningState(page);
        await audioButton(page).click();
        await nativePlaying(page);
        expect(await audioLearningState(page)).toEqual(before);
        await page.getByRole('button', { name: /Додому|Home/ }).click();
        await oldAudioStopped(page);
        const snapshot = await readMixedSessionSnapshot(page);
        expect(snapshot?.level).toBe('A1');
        expect(snapshot?.deckId).toBe('all');
        if (kind === 'deck') {
          await page.getByTestId('practice-active-deck-chip').click();
          await page.getByTestId('practice-deck-option-audio-switch-target').click();
        } else {
          await page.getByTestId('practice-dashboard-hero').getByRole('button', { name: 'A2', exact: true }).click();
        }
        await expect(page.getByTestId('practice-switch-session-offer')).toBeVisible();
        if (disposition === 'decline') {
          await page.getByTestId('practice-switch-session-decline').click();
          await expect(page.getByTestId('practice-switch-session-offer')).toHaveCount(0);
          expect(await readMixedSessionSnapshot(page)).toEqual(snapshot);
          expect(await page.evaluate(() => localStorage.getItem('lu-learner-level'))).toBe('A1');
          await expect(page.getByTestId('practice-active-deck-chip')).toContainText('All Words');
          await expect(page.getByTestId('practice-settings-toggle')).toBeFocused();
        } else {
          await page.getByTestId('practice-switch-session-accept').click();
          await expect(page.locator('[data-pronunciation-lemma]')).toHaveAttribute('data-pronunciation-lemma', reused ? 'або́' : 'audio-next-control');
          const committed = await readMixedSessionSnapshot(page);
          expect(committed?.deckId).toBe(kind === 'deck' ? 'audio-switch-target' : 'all');
          expect(committed?.level).toBe(kind === 'level' ? 'A2' : 'A1');
          expect(await page.evaluate(() => localStorage.getItem('lu-learner-level'))).toBe(kind === 'level' ? 'A2' : 'A1');
          await expect(audioButton(page)).toHaveText('Play pronunciation');
        }
        await audioAnimationFrame(page);
        await oldAudioStopped(page);
        expect(await page.evaluate(() => window.practiceAudioProbe.media.length)).toBe(1);
        expect(await page.evaluate(() => localStorage.getItem('lu-lexicon-srs'))).toBe(before.saved.srs);
      });
    }
  }

  test('P04 idle immediate switches, unchanged no-ops, unpublished-level refusal and unconfigured refresh', async ({ page }) => {
    await observePracticeAudio(page);
    await routeGoodAudio(page);
    await audioPracticeFixture(page, true);
    await page.goto('/practice/');
    await page.getByTestId('practice-active-deck-chip').click();
    await page.getByTestId('practice-deck-option-all').click();
    await page.getByTestId('practice-dashboard-hero').getByRole('button', { name: 'A1', exact: true }).click();
    await expect(page.getByTestId('practice-switch-session-offer')).toHaveCount(0);
    await expect(page.getByTestId('practice-dashboard-hero').getByRole('button', { name: /C2/, exact: false })).toBeDisabled();
    await page.getByTestId('practice-dashboard-hero').getByRole('button', { name: 'A2', exact: true }).click();
    expect(await page.evaluate(() => localStorage.getItem('lu-learner-level'))).toBe('A2');
    await expect(page.getByTestId('practice-switch-session-offer')).toHaveCount(0);
    await page.getByTestId('practice-active-deck-chip').click();
    await page.getByTestId('practice-deck-option-virtual_teacher_lesson').click();
    await expect(page.getByTestId('practice-active-deck-chip')).toContainText('Curated');
    await expect(page.getByTestId('practice-switch-session-offer')).toHaveCount(0);
    await page.getByTestId('practice-settings-toggle').click();
    await expect(page.getByTestId('practice-drive-sync-section')).toHaveCount(0);
    await test.info().attach('refresh-applicability.json', { body: JSON.stringify({ customSetRefresh: 'N/A in this unconfigured artifact: actual Drive sync control absent; no fabricated storage event', pendingRefreshStarted: false }), contentType: 'application/json' });
  });

  for (const replacement of [false, true]) {
    test(`P04 delayed shard arrival / ${replacement ? 'actual pronunciation rebind cancels' : 'same presentation keeps playback'}`, async ({ page }) => {
      await observePracticeAudio(page, true);
      await routeGoodAudio(page);
      await audioPracticeFixture(page, true);
      if (replacement) await audioOverlappingLevel(page, 'або');
      let release!: () => void;
      const held = new Promise<void>((resolve) => { release = resolve; });
      let arrived = 0;
      await page.route(/practice-(index|lexemes)\.A2\.json$/, async (route) => {
        await held;
        arrived++;
        await route.fallback();
      });
      await page.goto('/practice/');
      await page.locator('button[data-mode="flashcards"]').click();
      await expect(page.locator('[data-pronunciation-lemma]')).toHaveAttribute('data-pronunciation-lemma', 'або́');
      await audioAnimationFrame(page);
      await audioButton(page).click();
      await nativePlaying(page);
      const before = await audioLearningState(page);
      release();
      await expect.poll(() => arrived).toBeGreaterThanOrEqual(2);
      if (replacement) {
        await expect(page.locator('[data-pronunciation-lemma]')).toHaveAttribute('data-pronunciation-lemma', 'або');
        await oldAudioStopped(page);
        await expect(audioButton(page)).toHaveText('Play pronunciation');
      } else {
        await audioAnimationFrame(page);
        await nativePlaying(page);
        expect(await page.evaluate(() => window.practiceAudioProbe.media[0].events.includes('pause()'))).toBe(false);
      }
      expect(await audioLearningState(page)).toEqual(before);
    });
  }

  test('P04 delayed daily pool arrival preserves the current presentation and playback', async ({ page }) => {
    await observePracticeAudio(page, true);
    await routeGoodAudio(page);
    let release!: () => void;
    const held = new Promise<void>((resolve) => { release = resolve; });
    let delivered = false;
    await page.route('**/lexicon/daily-pool.json', async (route) => {
      await held;
      await route.fulfill({ json: [{ lemma: 'або', slug: 'або', gloss: 'fixture identity', cefr: 'A1' }] });
      delivered = true;
    });
    await openAudioPractice(page);
    await audioButton(page).click();
    await nativePlaying(page);
    const before = await audioLearningState(page);
    release();
    await expect.poll(() => delivered).toBe(true);
    await audioAnimationFrame(page);
    await nativePlaying(page);
    expect(await audioLearningState(page)).toEqual(before);
    expect(await page.evaluate(() => window.practiceAudioProbe.media[0].events.includes('pause()'))).toBe(false);
  });

  for (const fault of ['404', 'network', '500'] as const) {
    test(`P05 manifest ${fault} and subsequent-mount ${fault === '404' ? 'permanent cache' : 'retry'}`, async ({ page }) => {
      await observePracticeAudio(page, true);
      await routeGoodAudio(page);
      let requests = 0;
      await page.route('**/audio/pronunciation/manifest.json', (route) => {
        requests++;
        if (requests > 1) return route.fulfill({ json: { schemaVersion: 1, entries: { 'або': { file: AUDIO_FILE } } } });
        return fault === 'network' ? route.abort('failed') : route.fulfill({ status: Number(fault), body: '' });
      });
      // A failed request has no response; the mounted fallback itself is the settle oracle.
      await audioPracticeFixture(page);
      await page.goto('/practice/');
      await page.locator('button[data-mode="flashcards"]').click();
      await expect.poll(() => requests).toBe(1);
      await assertNativeFallback(page);
      await page.getByRole('button', { name: /Додому|Home/ }).click();
      await page.locator('button[data-mode="flashcards"]').click();
      if (fault === '404') {
        await assertNativeFallback(page);
        expect(requests).toBe(1);
      } else {
        await expect.poll(() => requests).toBe(2);
        await page.evaluate(() => new Promise<void>((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
        await audioButton(page).click();
        await nativePlaying(page);
      }
    });
  }

  for (const [parent, name, body] of [
    ['P06', 'malformed JSON', '{'],
    ['P06', 'invalid schema', JSON.stringify({ schemaVersion: 2, entries: {} })],
    ['P07', 'empty manifest', JSON.stringify({ schemaVersion: 1, entries: {} })],
    ['P07', 'uncovered manifest', JSON.stringify({ schemaVersion: 1, entries: { unrelated: { file: AUDIO_FILE } } })],
    ['P07', 'unsafe entry', JSON.stringify({ schemaVersion: 1, entries: { 'або': { file: '../unsafe.wav' } } })],
  ]) {
    test(`${parent} ${name} preserves truthful fallback and learning state`, async ({ page }) => {
      await observePracticeAudio(page);
      const mediaRequests: string[] = [];
      await page.route('**/audio/pronunciation/**', (route) => {
        if (route.request().url().endsWith('/manifest.json')) return route.fulfill({ body, contentType: 'application/json' });
        mediaRequests.push(route.request().url());
        return route.abort();
      });
      await openAudioPractice(page);
      await assertNativeFallback(page);
      expect(mediaRequests).toEqual([]);
      expect(await page.evaluate(() => window.practiceAudioProbe.media)).toEqual([]);
    });
  }

  for (const fault of ['P08 clip404', 'P09 undecodable bytes']) {
    test(`${fault} then SAME-mounted native retry ignores late old native failure`, async ({ page }) => {
      await observePracticeAudio(page, true);
      await routeGoodAudio(page);
      let requests = 0;
      await page.route(`**/${AUDIO_FILE}`, (route) => {
        requests++;
        if (requests === 1) return route.fulfill(fault.startsWith('P08')
          ? { status: 404, body: '' }
          : { status: 200, body: 'not a decodable WAV', contentType: 'audio/wav' });
        return route.fulfill({ path: AUDIO_FIXTURE, contentType: 'audio/wav', headers: { 'Cache-Control': 'no-store' } });
      });
      await page.route('**/prior-attempt-invalid.wav', (route) => route.fulfill({ body: 'invalid prior attempt', contentType: 'audio/wav' }));
      await openAudioPractice(page);
      const root = await page.locator('[data-pronunciation-lemma]').elementHandle();
      const before = await audioLearningState(page);
      await audioButton(page).click();
      await expect(page.locator('[data-pronunciation-lemma] [role="status"]')).toHaveText('Audio unavailable. Try again.');
      await expect.poll(() => page.evaluate(() => window.practiceAudioProbe.media[0].events)).toContain('error');
      expect(await audioLearningState(page)).toEqual(before);
      await audioButton(page).click();
      await nativePlaying(page);
      expect(await root!.evaluate((element) => element.isConnected)).toBe(true);
      await lateNativeFailure(page);
      await expect(page.locator('[data-pronunciation-lemma] [role="status"]')).toBeEmpty();
      expect(await audioLearningState(page)).toEqual(before);
      expect(requests).toBeGreaterThanOrEqual(2);
    });
  }

  test('P11 observed native inventory, language and controlled empty availability retry', async ({ page }) => {
    await observePracticeAudio(page);
    await page.route('**/audio/pronunciation/manifest.json', (route) => route.fulfill({ json: { schemaVersion: 1, entries: {} } }));
    await openAudioPractice(page);
    const nativeInventory = await assertNativeFallback(page);
    if (!nativeInventory.voices.some((voice) => voice.local && voice.lang.toLowerCase().startsWith('uk'))) {
      test.info().annotations.push({ type: 'native-local-positive', description: 'N/A: observed device inventory offers no local Ukrainian voice; empty catalog capability remains UNKNOWN; no remote speech requested' });
    }
    await page.evaluate(() => {
      const nativeGetVoices = speechSynthesis.getVoices.bind(speechSynthesis);
      Reflect.set(window, 'restoreNativeVoices', () => { speechSynthesis.getVoices = nativeGetVoices; });
      speechSynthesis.getVoices = () => [];
    });
    const before = await audioLearningState(page);
    await audioButton(page).click();
    await expect(audioButton(page)).toHaveAccessibleName('Stop pronunciation');
    await expect(audioButton(page)).toHaveAttribute('aria-busy', 'true');
    await expect(page.locator('[data-pronunciation-lemma] [role="status"]')).toBeEmpty();
    await page.evaluate(() => {
      Reflect.get(window, 'restoreNativeVoices')();
      speechSynthesis.dispatchEvent(new Event('voiceschanged'));
    });
    if (nativeInventory.voices.some((voice) => voice.local && voice.lang.toLowerCase().startsWith('uk'))) {
      await expect.poll(() => page.evaluate(() => window.practiceAudioProbe.speech.some((entry) => entry.events.includes('start')))).toBe(true);
      await audioButton(page).click();
    } else if (!nativeInventory.supported || nativeInventory.voices.length > 0) {
      await expect(page.locator('[data-pronunciation-lemma] [role="status"]')).toHaveText('Audio unavailable. Try again.');
    } else {
      await expect(audioButton(page)).toHaveAttribute('aria-busy', 'true');
      await audioButton(page).click();
    }
    await assertNativeFallback(page);
    expect(await audioLearningState(page)).toEqual(before);
  });

  test('P11 controlled non-Ukrainian inventory never substitutes a voice', async ({ page }) => {
    await observePracticeAudio(page);
    await page.addInitScript(() => {
      // A boundary fixture only; it makes no claim about device voice availability.
      speechSynthesis.getVoices = () => [{ lang: 'en-US', localService: true, name: 'boundary English' } as SpeechSynthesisVoice];
    });
    await page.route('**/audio/pronunciation/manifest.json', (route) => route.fulfill({ json: { schemaVersion: 1, entries: {} } }));
    await openAudioPractice(page);
    await assertNativeFallback(page);
    expect(await page.evaluate(() => window.practiceAudioProbe.speech)).toEqual([]);
  });

  for (const transition of ['Home', 'Next same item', 'locale'] as const) {
    test(`P04 held native play cancelled across ${transition}, late response cannot resurrect it`, async ({ page }) => {
      await observePracticeAudio(page, true);
      await routeGoodAudio(page);
      let release!: () => void;
      const held = new Promise<void>((resolve) => { release = resolve; });
      let requested = false;
      await page.route(`**/${AUDIO_FILE}`, async (route) => {
        requested = true;
        await held;
        await route.fulfill({ path: AUDIO_FIXTURE, contentType: 'audio/wav' });
      });
      await openAudioPractice(page);
      if (transition === 'Next same item') await completeOneFlashcard(page, 'again');
      const srs = (await audioLearningState(page)).saved.srs;
      await audioButton(page).click();
      await expect.poll(() => requested).toBe(true);
      await expect(audioButton(page)).toHaveAccessibleName('Stop pronunciation');
      await expect(audioButton(page)).toHaveAttribute('aria-busy', 'true');
      if (transition === 'Home') await page.getByRole('button', { name: /Додому|Home/ }).click();
      else if (transition === 'locale') await page.locator('#lu-locale-toggle').click();
      else await page.getByTestId('practice-advance-button').click();
      await oldAudioStopped(page);
      release();
      await expect.poll(() => page.evaluate(() => window.practiceAudioProbe.media[0].promises)).toContain('AbortError');
      await audioAnimationFrame(page);
      await oldAudioStopped(page);
      expect(await page.evaluate(() => localStorage.getItem('lu-lexicon-srs'))).toBe(srs);
      expect(await page.evaluate(() => window.practiceAudioProbe.media[0].events.includes('playing'))).toBe(false);
    });
  }

  test('P04 actual rendered route departure cancels native audio', async ({ page }) => {
    await observePracticeAudio(page, true);
    await routeGoodAudio(page);
    await openAudioPractice(page);
    await audioButton(page).click();
    await nativePlaying(page);
    await page.evaluate(() => {
      // Register after the real controller so its departure cleanup runs first.
      window.addEventListener('pagehide', () => {
        const record = window.practiceAudioProbe.media[0];
        sessionStorage.setItem('audio-departure', JSON.stringify({
          pauseCalled: record.events.includes('pause()'),
          paused: record.element.paused,
          time: record.element.currentTime,
        }));
      });
    });
    await page.locator('a[href="/lexicon/"]:visible').first().click();
    await expect(page).toHaveURL(/\/lexicon\/$/);
    const departure = await page.evaluate(() => JSON.parse(sessionStorage.getItem('audio-departure') ?? 'null'));
    await test.info().attach('departure.json', { body: JSON.stringify(departure), contentType: 'application/json' });
    expect(departure).toEqual({ pauseCalled: true, paused: true, time: 0 });
  });

  for (const same of [false, true]) {
    test(`P03 Next / ${same ? 'same-item re-presentation' : 'deterministic different selection'}`, async ({ page }) => {
      await observePracticeAudio(page, true);
      await routeGoodAudio(page);
      await openAudioPractice(page, !same);
      await completeOneFlashcard(page, 'again');
      const answered = await audioLearningState(page);
      expect(JSON.parse(answered.saved.srs!).reviews).toHaveLength(1);
      await audioButton(page).click();
      await nativePlaying(page);
      expect(await audioLearningState(page)).toEqual(answered);
      await page.getByTestId('practice-advance-button').click();
      await oldAudioStopped(page);
      await expect(page.locator('[data-pronunciation-lemma]')).toHaveAttribute('data-pronunciation-lemma', same ? 'або́' : 'audio-next-control');
      await expect(page.locator('[data-activity="flashcard"]')).toHaveAttribute('data-rated', 'false');
      await expect(page.getByTestId('practice-advance-button')).toHaveCount(0);
      await expect(page.getByTestId('practice-session-progress')).toContainText('1/');
      expect((await audioLearningState(page)).saved.srs).toBe(answered.saved.srs);
    });
  }
  for (const historyLength of [49, 50]) {
    test(`P03 resumed history ${historyLength} cancels native same-item audio through and beyond the cap`, async ({ page }) => {
      await observePracticeAudio(page, true);
      await routeGoodAudio(page);
      await openAudioPractice(page);
      await completeOneFlashcard(page, 'again');
      await page.getByRole('button', { name: /Додому|Home/ }).click();
      await page.evaluate((length) => {
        const stored = JSON.parse(localStorage.getItem('lu-practice-session')!);
        const snapshot = stored.byMode.flashcards;
        snapshot.history = Array.from({ length }, () => snapshot.history[0]);
        snapshot.completed = length;
        snapshot.plannedTotal = 100;
        snapshot.budget = 'until-zero';
        snapshot.modeFilter = 'mixed';
        localStorage.setItem('lu-practice-session', JSON.stringify({ version: 2, byMode: { mixed: snapshot } }));
      }, historyLength);
      await page.reload();
      await page.getByTestId('practice-start-session').click();
      for (let round = 0; round < 3; round++) {
        await completeOneFlashcard(page, 'again');
        const answered = await audioLearningState(page);
        expect(JSON.parse(answered.saved.srs!).reviews).toHaveLength(round + 2);
        await audioButton(page).click();
        await nativePlaying(page);
        const index = await page.evaluate(() => window.practiceAudioProbe.media.length - 1);
        await page.getByTestId('practice-advance-button').click();
        await expect.poll(() => page.evaluate((i) => {
          const record = window.practiceAudioProbe.media[i];
          return { paused: record.element.paused, time: record.element.currentTime, pauseCalled: record.events.includes('pause()') };
        }, index)).toEqual({ paused: true, time: 0, pauseCalled: true });
        await expect(page.locator('[data-activity="flashcard"]')).toHaveAttribute('data-rated', 'false');
        await expect(audioButton(page)).toHaveAccessibleName('Play pronunciation');
        await expect(page.getByTestId('practice-session-progress')).toContainText(`${historyLength + round + 1}/`);
        expect((await audioLearningState(page)).saved.srs).toBe(answered.saved.srs);
        expect(await page.evaluate(() => JSON.parse(localStorage.getItem('lu-practice-session')!).byMode.mixed.history.length)).toBe(50);
      }
    });
  }

  for (const transition of ['cancel', 'Home', 'Next same item']) {
    test(`P11 late native catalog observation after ${transition} cannot resurrect a cancelled request`, async ({ page }) => {
      await observePracticeAudio(page);
      await page.addInitScript(() => {
        const native = speechSynthesis.getVoices.bind(speechSynthesis);
        Reflect.set(window, 'restoreNativeVoices', () => { speechSynthesis.getVoices = native; });
        speechSynthesis.getVoices = () => [];
      });
      await page.route('**/manifest.json', (route) => route.fulfill({ json: { schemaVersion: 1, entries: {} } }));
      await openAudioPractice(page);
      if (transition === 'Next same item') await completeOneFlashcard(page, 'again');
      const before = await audioLearningState(page);
      await audioButton(page).click();
      await expect(audioButton(page)).toHaveAccessibleName('Stop pronunciation');
      await expect(audioButton(page)).toHaveAttribute('aria-busy', 'true');
      await expect(page.locator('[data-pronunciation-lemma] [role="status"]')).toBeEmpty();
      if (transition === 'cancel') await audioButton(page).click();
      else if (transition === 'Home') await page.getByRole('button', { name: /Додому|Home/ }).click();
      else await page.getByTestId('practice-advance-button').click();
      await page.evaluate(() => {
        Reflect.get(window, 'restoreNativeVoices')();
        speechSynthesis.dispatchEvent(new Event('voiceschanged'));
      });
      const inventory = await observedAudioVoices(page);
      await test.info().attach('late-native-catalog.json', { body: JSON.stringify(inventory), contentType: 'application/json' });
      expect(await page.evaluate(() => window.practiceAudioProbe.speech)).toEqual([]);
      expect(await page.evaluate(() => localStorage.getItem('lu-lexicon-srs'))).toBe(before.saved.srs);
      if (transition !== 'Home') {
        await expect(audioButton(page)).toHaveAccessibleName('Play pronunciation');
        await expect(audioButton(page)).toHaveAttribute('aria-busy', 'false');
      }
    });
  }

  test('P10 held native play / native abort then SAME-mounted retry', async ({ page }) => {
    await observePracticeAudio(page, true);
    await routeGoodAudio(page);
    await page.route('**/prior-attempt-invalid.wav', (route) => route.fulfill({ body: 'invalid prior attempt', contentType: 'audio/wav' }));
    let release!: () => void;
    const held = new Promise<void>((resolve) => { release = resolve; });
    let requests = 0;
    await page.route(`**/${AUDIO_FILE}`, async (route) => {
      requests++;
      if (requests === 1) await held;
      await route.fulfill({ path: AUDIO_FIXTURE, contentType: 'audio/wav', headers: { 'Cache-Control': 'no-store' } });
    });
    await openAudioPractice(page);
    const root = await page.locator('[data-pronunciation-lemma]').elementHandle();
    const before = await audioLearningState(page);
    await audioButton(page).click();
    await expect.poll(() => requests).toBe(1);
    await expect(audioButton(page)).toHaveAccessibleName('Stop pronunciation');
    await expect(audioButton(page)).toHaveAttribute('aria-busy', 'true');
    await page.evaluate(() => window.practiceAudioProbe.media[0].element.load());
    await expect.poll(() => page.evaluate(() => window.practiceAudioProbe.media[0].promises)).toContain('AbortError');
    await expect(page.locator('[data-pronunciation-lemma] [role="status"]')).toHaveText('Audio unavailable. Try again.');
    await audioButton(page).click();
    await nativePlaying(page);
    expect(await root!.evaluate((element) => element.isConnected)).toBe(true);
    release();
    await page.evaluate(() => new Promise<void>((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
    await nativePlaying(page);
    await lateNativeFailure(page);
    expect(await audioLearningState(page)).toEqual(before);
    await audioButton(page).click();
    await expect.poll(() => page.evaluate(() => {
      const current = window.practiceAudioProbe.media.at(-1)!;
      return { paused: current.element.paused, time: current.element.currentTime, pauseCalled: current.events.includes('pause()') };
    })).toEqual({ paused: true, time: 0, pauseCalled: true });
  });

  test('P01 Enter and Space on audio while an answer is pending preserve focus, one review and Next', async ({ page }) => {
    await observePracticeAudio(page, true);
    await routeGoodAudio(page);
    await openAudioPractice(page);
    await completeOneFlashcard(page, 'again');
    await expect(page.getByTestId('practice-advance-button')).toBeFocused();
    const answered = await audioLearningState(page);
    expect(JSON.parse(answered.saved.srs!).reviews).toHaveLength(1);
    await audioButton(page).focus();
    await page.keyboard.press('Enter');
    await nativePlaying(page);
    await expect(audioButton(page)).toBeFocused();
    expect(await audioLearningState(page)).toEqual(answered);
    await page.keyboard.press('Space');
    await oldAudioStopped(page);
    await expect(audioButton(page)).toBeFocused();
    await expect(page.getByTestId('practice-advance-button')).toBeVisible();
    expect(await audioLearningState(page)).toEqual(answered);
  });

  test('P10 held play / explicit pending stop and same-mounted retry', async ({ page }) => {
    await observePracticeAudio(page, true);
    await routeGoodAudio(page);
    let release!: () => void;
    const held = new Promise<void>((resolve) => { release = resolve; });
    let requests = 0;
    await page.route(`**/${AUDIO_FILE}`, async (route) => {
      if (++requests === 1) await held;
      await route.fulfill({ path: AUDIO_FIXTURE, contentType: 'audio/wav' });
    });
    await openAudioPractice(page);
    const root = await page.locator('[data-pronunciation-lemma]').elementHandle();
    const before = await audioLearningState(page);
    await audioButton(page).click();
    await expect.poll(() => requests).toBe(1);
    await expect(audioButton(page)).toHaveAccessibleName('Stop pronunciation');
    await expect(audioButton(page)).toHaveAttribute('aria-busy', 'true');
    await audioButton(page).click();
    await oldAudioStopped(page);
    await expect(audioButton(page)).toHaveAccessibleName('Play pronunciation');
    await expect(audioButton(page)).toHaveAttribute('aria-busy', 'false');
    await audioButton(page).click();
    await nativePlaying(page);
    release();
    await expect.poll(() => page.evaluate(() => window.practiceAudioProbe.media[0].promises)).toContain('AbortError');
    await nativePlaying(page);
    expect(await root!.evaluate((element) => element.isConnected)).toBe(true);
    expect(await audioLearningState(page)).toEqual(before);
  });
});
