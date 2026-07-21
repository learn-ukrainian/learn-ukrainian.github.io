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
  const resume = page.locator('button[data-resume-mode="mixed"]');

  for (const control of [start, resume]) {
    await expect(control).toBeVisible();
    const box = await control.boundingBox();
    expect(box).not.toBeNull();
    const top = box!.y;
    const bottom = box!.y + box!.height;
    expect(top).toBeGreaterThanOrEqual(0);
    expect(bottom).toBeLessThanOrEqual(768);
  }

  // Accessible names must match the active chrome locale only (no slash duplicates).
  // With a resumable Mixed snapshot, the primary CTA reads "Resume session" and the
  // secondary control reads "Resume Mixed (N/M)" / "Продовжити «Мікс» (N/M)".
  if (locale === 'en') {
    await expect(page.getByRole('button', { name: 'Resume session' })).toBeVisible();
    await expect(page.getByRole('button', { name: /Resume "Mixed"/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Start session|Почати заняття|Продовжити «Мікс»/ })).toHaveCount(0);
  } else {
    await expect(page.getByRole('button', { name: 'Продовжити заняття' })).toBeVisible();
    await expect(page.getByRole('button', { name: /Продовжити «Мікс»/ })).toBeVisible();
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
