import { describe, test, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import OddOneOut, { shuffleOddOneOut } from '@site/src/components/OddOneOut';

// Stub rng: a fixed sequence, so the shuffle is not flaky.
function stubRng(values: number[]) {
  let i = 0;
  return () => values[i++ % values.length];
}

describe('shuffleOddOneOut', () => {
  const words = ['а', 'б', 'в', 'г'];

  test('moves the odd word off the last slot and remaps the index', () => {
    // Fisher-Yates from the end with rng 0 always swaps with index 0.
    const result = shuffleOddOneOut(words, 3, stubRng([0, 0, 0]));
    expect(result.words).toEqual(['б', 'в', 'г', 'а']);
    expect(result.correct).toBe(2);
    expect(result.words[result.correct]).toBe('г');
  });

  test('always keeps the correct word at the remapped index', () => {
    for (const rng of [stubRng([0]), stubRng([0.99]), stubRng([0.5, 0.2, 0.8]), stubRng([0.1, 0.9])]) {
      for (let correct = 0; correct < words.length; correct++) {
        const result = shuffleOddOneOut(words, correct, rng);
        expect(result.words[result.correct]).toBe(words[correct]);
        expect([...result.words].sort()).toEqual([...words].sort());
      }
    }
  });

  test('does not mutate its input', () => {
    const input = ['а', 'б', 'в', 'г'];
    shuffleOddOneOut(input, 3, stubRng([0]));
    expect(input).toEqual(['а', 'б', 'в', 'г']);
  });

  test('default rng is deterministic for the same words (no hydration mismatch)', () => {
    expect(shuffleOddOneOut(words, 3)).toEqual(shuffleOddOneOut(words, 3));
  });
});

describe('OddOneOut component', () => {
  beforeEach(() => {
    document.documentElement.dataset.chromeLocale = 'en';
  });

  const items = [
    { words: ['день', 'ніч', 'вечір', 'стіл'], correct: 3, explanation: 'Стіл — не час доби.' },
    { words: ['кіт', 'пес', 'риба', 'ліс'], correct: 3, explanation: 'Ліс — не тварина.' },
    { words: ['мама', 'тато', 'брат', 'вікно'], correct: 3, explanation: 'Вікно — не родич.' },
  ];

  test('not every answer stays on the last button with the default rng', () => {
    const positions = items.map((item) => shuffleOddOneOut(item.words, item.correct).correct);
    expect(positions.some((position) => position !== 3)).toBe(true);
  });

  test('picking the odd word still grades correct after the shuffle', async () => {
    const user = userEvent.setup();
    render(<OddOneOut items={items} />);

    await user.click(screen.getByRole('button', { name: 'стіл' }));

    expect(screen.getByText('✅ Правильно!')).toBeInTheDocument();
  });

  test('picking a different word grades wrong', async () => {
    const user = userEvent.setup();
    render(<OddOneOut items={items} />);

    await user.click(screen.getByRole('button', { name: 'день' }));

    expect(screen.getByText('❌ Неправильно')).toBeInTheDocument();
  });
});

// ── shuffleOddOneOut optionWhy permutation ───────────────────────────────────

describe('shuffleOddOneOut with optionWhy', () => {
  const words = ['а', 'б', 'в', 'г'];
  const why = ['why-а', 'why-б', 'why-в', 'why-г'];

  test('optionWhy is permuted the same way as words', () => {
    const result = shuffleOddOneOut(words, 3, stubRng([0, 0, 0]), why);
    expect(result.words).toEqual(['б', 'в', 'г', 'а']);
    expect(result.optionWhy).toEqual(['why-б', 'why-в', 'why-г', 'why-а']);
    // Each word still lines up with its own why after the shuffle.
    result.words.forEach((word, i) => {
      const origIndex = words.indexOf(word);
      expect(result.optionWhy![i]).toBe(why[origIndex]);
    });
  });

  test('optionWhy is undefined when not provided (unchanged signature)', () => {
    const result = shuffleOddOneOut(words, 3, stubRng([0]));
    expect(result.optionWhy).toBeUndefined();
  });
});

// ── per-option feedback on the page (#8889 A1-P3) ────────────────────────────

describe('OddOneOut optionWhy', () => {
  beforeEach(() => {
    document.documentElement.dataset.chromeLocale = 'en';
  });

  const itemsWithWhy = [
    {
      words: ['день', 'ніч', 'вечір', 'стіл'],
      correct: 3,
      explanation: 'Стіл — не час доби.',
      optionWhy: ['день is a time of day.', 'ніч is a time of day.', 'вечір is a time of day.', 'стіл is furniture.'],
    },
  ];

  test('feedback region is announced (role=status, aria-live=polite)', async () => {
    const user = userEvent.setup();
    const { container } = render(<OddOneOut items={itemsWithWhy} />);
    await user.click(screen.getByRole('button', { name: 'стіл' }));

    const fb = container.querySelector('[data-activity="odd-one-out-feedback"]');
    expect(fb).toHaveAttribute('role', 'status');
    expect(fb).toHaveAttribute('aria-live', 'polite');
  });

  test('a correct pick shows only that word\'s why', async () => {
    const user = userEvent.setup();
    const { container } = render(<OddOneOut items={itemsWithWhy} />);
    await user.click(screen.getByRole('button', { name: 'стіл' }));

    expect(container.querySelector('[data-activity="odd-one-out-option-why"]')?.textContent).toBe(
      'стіл is furniture.',
    );
    expect(container.querySelector('[data-activity="odd-one-out-correct-why"]')).not.toBeInTheDocument();
  });

  test('a wrong pick shows the chosen word why, then the correct word why', async () => {
    const user = userEvent.setup();
    const { container } = render(<OddOneOut items={itemsWithWhy} />);
    await user.click(screen.getByRole('button', { name: 'день' }));

    expect(container.querySelector('[data-activity="odd-one-out-option-why"]')?.textContent).toBe(
      'день is a time of day.',
    );
    expect(container.querySelector('[data-activity="odd-one-out-correct-why"]')?.textContent).toBe(
      'стіл is furniture.',
    );
  });

  test('without optionWhy, falls back to the single explanation (V7 content)', async () => {
    const user = userEvent.setup();
    const legacyItems = [
      { words: ['день', 'ніч', 'вечір', 'стіл'], correct: 3, explanation: 'Стіл — не час доби.' },
    ];
    const { container } = render(<OddOneOut items={legacyItems} />);
    await user.click(screen.getByRole('button', { name: 'стіл' }));

    expect(screen.getByText('Стіл — не час доби.')).toBeInTheDocument();
    expect(container.querySelector('[data-activity="odd-one-out-option-why"]')).not.toBeInTheDocument();
  });
});
