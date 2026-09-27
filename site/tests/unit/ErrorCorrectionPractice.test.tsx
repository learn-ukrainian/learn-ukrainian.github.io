import { beforeEach, describe, expect, test } from 'vitest';
import { act, render, renderHook, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ErrorCorrectionPractice, {
  nextDueErrorCorrectionItem,
  type ErrorCorrectionDrill,
} from '@site/src/components/ErrorCorrectionPractice';
import {
  loadErrorCorrectionDeck,
  useErrorCorrectionPracticeOverlay,
} from '@site/src/components/useErrorCorrectionPracticeOverlay';
import {
  isAcceptedTypedCorrection,
  normalizeTypedCorrection,
} from '@site/src/components/ErrorCorrection';
import { SRS_STORAGE_KEY, cardKey, loadState, rateCard } from '@site/src/lib/lexicon/srs';
import cultureDeck from '@site/src/data/practice-error-corrections.json';

// Real deck shapes (#8723): options are only the two forms the source contrasts,
// and `answers` lists every correction a learner may type.
const mockDrills: ErrorCorrectionDrill[] = [
  {
    id: 'err_0006',
    sentence: 'Уважно прочитайте: «приймати участь» — тут допущено помилку.',
    errorWord: 'приймати участь',
    correctForm: 'брати (узяти) участь',
    options: ['брати (узяти) участь', 'приймати участь'],
    answers: ['брати (узяти) участь', 'брати участь', 'узяти участь'],
    explanation: 'Правильно вживати «брати (узяти) участь» замість помилкового «приймати участь».',
    isUkrainian: true,
    source: 'Textbook Gr 10 (glazova)',
  },
  {
    id: 'err_0063',
    sentence: 'Уважно прочитайте: «по п’ятницям» — тут допущено помилку.',
    errorWord: 'по п’ятницям',
    correctForm: 'по п’ятницях, щоп’ятниці',
    options: ['по п’ятницям', 'по п’ятницях, щоп’ятниці'],
    answers: ['по п’ятницях, щоп’ятниці', 'по п’ятницях', 'щоп’ятниці'],
    explanation: 'Правильно вживати «по п’ятницях, щоп’ятниці» замість помилкового «по п’ятницям».',
    isUkrainian: true,
    source: 'Textbook Gr 11 (avramenko)',
  },
];

describe('ErrorCorrectionPractice', () => {
  beforeEach(() => {
    localStorage.clear();
    loadState(localStorage);
  });

  test('loads production error-correction dataset with valid schema and non-empty drills', async () => {
    const drills = await loadErrorCorrectionDeck();
    expect(drills.length).toBe(cultureDeck.totalDrills);
    expect(drills.length).toBeGreaterThan(0);
    for (const drill of drills) {
      expect(drill.id).toMatch(/^err_\d{4}$/);
      expect(drill.sentence.length).toBeGreaterThan(0);
      expect(drill.errorWord.length).toBeGreaterThan(0);
      expect(drill.correctForm.length).toBeGreaterThan(0);
      expect(drill.options.length).toBeGreaterThanOrEqual(2);
      expect(drill.options).toContain(drill.correctForm);
      expect(drill.sentence).toContain(drill.errorWord);
      // #8723: options are the two forms the source contrasts, never generated
      // "(розм.)" / "(застаріле)" register-label copies.
      expect([...drill.options].sort()).toEqual([drill.correctForm, drill.errorWord].sort());
      // Step 2 is typed; the source correction is always an accepted answer.
      expect(drill.answers?.[0]).toBe(drill.correctForm);
    }
  });

  test('nextDueErrorCorrectionItem prioritizes due cards over future cards', () => {
    rateCard('err_0006', 'choice', 'good', new Date(Date.now() + 86400000));
    rateCard('err_0063', 'choice', 'again', new Date(Date.now() - 1000));

    const next = nextDueErrorCorrectionItem(mockDrills, null);
    expect(next?.id).toBe('err_0063');
  });

  test('step 2 is a typed correction, not a chip that gives the answer away', async () => {
    const user = userEvent.setup();
    render(<ErrorCorrectionPractice items={mockDrills} onBackToDecks={() => {}} chromeLocale="uk" />);

    expect(screen.getByTestId('drill-source-badge')).toHaveTextContent('📚 Textbook Gr 10 (glazova)');
    expect(screen.getByTestId('drill-counter-badge')).toHaveTextContent('Виконано: 0 (правильно: 0)');

    // Step 1: click a word of the error phrase.
    await user.click(screen.getByText('приймати'));

    // Step 2: a text field, focused; the correction is not offered as a chip.
    const input = screen.getByRole('textbox', { name: 'Ваше виправлення' });
    expect(input).toHaveFocus();
    expect(screen.queryByRole('button', { name: 'брати (узяти) участь' })).toBeNull();
    expect(screen.getByRole('button', { name: 'Перевірити' })).toBeDisabled();

    // A listed variant counts, whatever its case and spacing.
    await user.type(input, '  Узяти   участь {Enter}');

    expect(screen.getByText(/✓ Правильно!/)).toBeInTheDocument();
    expect(screen.getByText(/Правильно вживати «брати \(узяти\) участь»/)).toBeInTheDocument();
    expect(screen.getByTestId('drill-counter-badge')).toHaveTextContent('Виконано: 1 (правильно: 1)');
    expect(localStorage.getItem(SRS_STORAGE_KEY)).not.toBeNull();
    expect(loadState().cards.get(cardKey('err_0006', 'choice'))?.reps).toBeGreaterThan(0);

    await user.click(screen.getByTestId('error-correction-next-btn'));
    expect(screen.getByText('п’ятницям')).toBeInTheDocument();
  });

  test('a wrong typed correction is marked incorrect and shows the answer', async () => {
    const user = userEvent.setup();
    render(<ErrorCorrectionPractice items={mockDrills} onBackToDecks={() => {}} chromeLocale="uk" />);

    await user.click(screen.getByText('участь'));
    await user.type(screen.getByRole('textbox', { name: 'Ваше виправлення' }), 'приймати участь');
    await user.click(screen.getByRole('button', { name: 'Перевірити' }));

    const feedback = document.querySelector('[data-activity="error-correction-feedback"]');
    expect(feedback).toHaveAttribute('data-correct', 'false');
    expect(feedback).toHaveTextContent('Ваша відповідь: "приймати участь"');
    expect(feedback).toHaveTextContent('✗ Правильна відповідь: "приймати участь" → "брати (узяти) участь"');
    expect(screen.getByTestId('drill-counter-badge')).toHaveTextContent('Виконано: 1 (правильно: 0)');
  });

  test('"Show correction" reveals the answer and records a miss', async () => {
    const user = userEvent.setup();
    render(<ErrorCorrectionPractice items={mockDrills} onBackToDecks={() => {}} chromeLocale="uk" />);

    await user.click(screen.getByText('приймати'));
    await user.click(screen.getByRole('button', { name: 'Показати виправлення' }));

    expect(screen.getByText('✓ Виправлення: "приймати участь" → "брати (узяти) участь"')).toBeInTheDocument();
    expect(screen.getByTestId('drill-counter-badge')).toHaveTextContent('Виконано: 1 (правильно: 0)');
  });

  test('typed step is keyboard-only: Enter spots, types, checks and advances', async () => {
    const user = userEvent.setup();
    render(<ErrorCorrectionPractice items={[mockDrills[1], mockDrills[0]]} onBackToDecks={() => {}} chromeLocale="uk" />);

    screen.getByText('п’ятницям').focus();
    await user.keyboard('{Enter}');

    // ASCII apostrophe and a stress mark still match «щоп’ятниці».
    await user.keyboard("щоп'я\u0301тниці{Enter}");
    expect(screen.getByText(/✓ Правильно!/)).toBeInTheDocument();

    await user.keyboard('{Enter}');
    expect(screen.getByText('приймати')).toBeInTheDocument();
    expect(screen.getByTestId('drill-counter-badge')).toHaveTextContent('Виконано: 1 (правильно: 1)');
  });

  test('typed answers tolerate case, apostrophes, stress marks and surrounding spaces only', () => {
    expect(normalizeTypedCorrection('  Щоп\'я́тниці. ')).toBe('щоп’ятниці');
    expect(normalizeTypedCorrection('по п’ятницях ,  щоп’ятниці')).toBe('по п’ятницях, щоп’ятниці');
    // й / ї survive stress stripping (NFD splits them too).
    expect(normalizeTypedCorrection('Її  край')).toBe('її край');
    expect(isAcceptedTypedCorrection('УЗЯТИ УЧАСТЬ', mockDrills[0].answers!)).toBe(true);
    expect(isAcceptedTypedCorrection('узяти', mockDrills[0].answers!)).toBe(false);
    expect(isAcceptedTypedCorrection('   ', ['а'])).toBe(false);
  });

  test('useErrorCorrectionPracticeOverlay manages state transitions', async () => {
    const { result } = renderHook(() => useErrorCorrectionPracticeOverlay());
    expect(result.current.activeCulturePractice).toBe(false);
    expect(result.current.cultureDrills).toBeNull();

    act(() => {
      result.current.setActiveCulturePractice(true);
    });

    await waitFor(() => expect(result.current.cultureDrills).not.toBeNull());
    expect(result.current.cultureDrills?.length).toBe(cultureDeck.totalDrills);
    expect(result.current.cultureLoading).toBe(false);

    act(() => {
      result.current.setActiveCulturePractice(false);
    });
    expect(result.current.activeCulturePractice).toBe(false);
  });

  test('nextDueErrorCorrectionItem shuffles tasks across seeds and respects excludedIds', () => {
    const drills: ErrorCorrectionDrill[] = Array.from({ length: 10 }, (_, i) => ({
      id: `err_${String(i).padStart(4, '0')}`,
      sentence: `Речення ${i}`,
      errorWord: `помилка_${i}`,
      correctForm: `норма_${i}`,
      options: [`помилка_${i}`, `норма_${i}`],
      explanation: `Пояснення ${i}`,
      isUkrainian: true,
      source: 'Джерело',
    }));

    const firstPicks = new Set<string>();
    for (let s = 1; s <= 10; s += 1) {
      const pick = nextDueErrorCorrectionItem(drills, null, s * 9973);
      if (pick) firstPicks.add(pick.id);
    }
    expect(firstPicks.size).toBeGreaterThanOrEqual(3);

    const excluded = new Set(['err_0000', 'err_0001', 'err_0002']);
    const pickWithExclusion = nextDueErrorCorrectionItem(drills, null, 12345, excluded);
    expect(excluded.has(pickWithExclusion!.id)).toBe(false);
  });
});
