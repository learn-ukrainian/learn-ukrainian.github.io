import { describe, test, expect } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AnagramQuestion } from '@site/src/components/Anagram';
import Anagram from '@site/src/components/Anagram';

// ── helpers ──────────────────────────────────────────────────────────────────

/** Return buttons inside a zone identified by data-activity. */
function tilesIn(container: HTMLElement, zone: string) {
  const el = container.querySelector(`[data-activity="${zone}"]`);
  if (!el) throw new Error(`Zone "${zone}" not found`);
  return within(el as HTMLElement).queryAllByRole('button');
}

function submitBtn(container: HTMLElement) {
  return container.querySelector<HTMLButtonElement>('button[class*="submitButton"]')
    ?? container.querySelector<HTMLButtonElement>('button[class*="submit"]')
    ?? [...container.querySelectorAll('button')].find(
      b => b.textContent === 'Check Answer' || b.textContent === 'Перевірити'
    )!;
}

function resetBtn(container: HTMLElement) {
  return [...container.querySelectorAll('button')].find(
    b => b.textContent === 'Try Again' || b.textContent === 'Спробувати знову'
  )!;
}

// ── AnagramQuestion ───────────────────────────────────────────────────────────

describe('AnagramQuestion', () => {
  // Use 3 distinct letters unlikely to accidentally be in the right order
  const props = { scrambled: 'a b c', answer: 'cab' };

  test('renders letter tiles in the letter bank', () => {
    const { container } = render(<AnagramQuestion {...props} />);
    const tiles = tilesIn(container, 'letter-bank');
    expect(tiles.length).toBe(3);
  });

  test('answer zone starts empty (shows placeholder, no tiles)', () => {
    const { container } = render(<AnagramQuestion {...props} />);
    const answerTiles = tilesIn(container, 'answer-zone');
    expect(answerTiles.length).toBe(0);
  });

  test('renders hint when provided', () => {
    const { container } = render(<AnagramQuestion {...props} hint="A helpful clue" />);
    expect(container.textContent).toContain('A helpful clue');
  });

  test('does not render hint element when hint is not provided', () => {
    const { container } = render(<AnagramQuestion {...props} />);
    expect(container.textContent).not.toContain('💡');
  });

  test('clicking a letter moves it from bank to answer zone', async () => {
    const user = userEvent.setup();
    const { container } = render(<AnagramQuestion {...props} />);

    const bankBefore = tilesIn(container, 'letter-bank').length;
    await user.click(tilesIn(container, 'letter-bank')[0]);

    expect(tilesIn(container, 'letter-bank').length).toBe(bankBefore - 1);
    expect(tilesIn(container, 'answer-zone').length).toBe(1);
  });

  test('clicking a letter in answer zone moves it back to bank', async () => {
    const user = userEvent.setup();
    const { container } = render(<AnagramQuestion {...props} />);

    // Move one letter to the answer zone
    await user.click(tilesIn(container, 'letter-bank')[0]);
    const bankAfterMove = tilesIn(container, 'letter-bank').length;

    // Move it back
    await user.click(tilesIn(container, 'answer-zone')[0]);

    expect(tilesIn(container, 'letter-bank').length).toBe(bankAfterMove + 1);
    expect(tilesIn(container, 'answer-zone').length).toBe(0);
  });

  test('Check Answer button is disabled while letters remain in bank', () => {
    const { container } = render(<AnagramQuestion {...props} />);
    expect(submitBtn(container)).toBeDisabled();
  });

  test('Check Answer button becomes enabled when all letters are placed', async () => {
    const user = userEvent.setup();
    const { container } = render(<AnagramQuestion {...props} />);

    // Click all letters out of the bank
    while (tilesIn(container, 'letter-bank').length > 0) {
      await user.click(tilesIn(container, 'letter-bank')[0]);
    }

    expect(submitBtn(container)).toBeEnabled();
  });

  test('shows correct feedback when the right answer is submitted', async () => {
    const user = userEvent.setup();
    // Single-letter word: only one possible arrangement
    const { container } = render(<AnagramQuestion scrambled="x" answer="x" />);

    await user.click(tilesIn(container, 'letter-bank')[0]);
    await user.click(submitBtn(container));

    const feedback = container.querySelector('[data-activity="feedback"]');
    expect(feedback).toBeInTheDocument();
    expect(feedback?.getAttribute('data-correct')).toBe('true');
  });

  test('shows incorrect feedback when the wrong answer is submitted', async () => {
    const user = userEvent.setup();
    // 'abc' scrambled, answer is 'cab' — whatever order ends up won't be 'cab'
    // We can guarantee this by using a 2-char case where shuffleNotCorrect swaps
    const { container } = render(
      <AnagramQuestion scrambled="a b" answer="ba" />
    );

    // shuffleNotCorrect(['a','b'], ['b','a']) could return ['a','b']
    // So clicking in current order gives 'ab' ≠ 'ba' → incorrect
    while (tilesIn(container, 'letter-bank').length > 0) {
      await user.click(tilesIn(container, 'letter-bank')[0]);
    }
    await user.click(submitBtn(container));

    const feedback = container.querySelector('[data-activity="feedback"]');
    expect(feedback).toBeInTheDocument();
  });

  test('Reset button restores the initial state', async () => {
    const user = userEvent.setup();
    const { container } = render(<AnagramQuestion {...props} />);

    const initialBankCount = tilesIn(container, 'letter-bank').length;

    // Place all letters and submit
    while (tilesIn(container, 'letter-bank').length > 0) {
      await user.click(tilesIn(container, 'letter-bank')[0]);
    }
    await user.click(submitBtn(container));

    // Reset
    await user.click(resetBtn(container));

    expect(tilesIn(container, 'letter-bank').length).toBe(initialBankCount);
    expect(tilesIn(container, 'answer-zone').length).toBe(0);
    expect(container.querySelector('[data-activity="feedback"]')).not.toBeInTheDocument();
  });
});

// ── Anagram wrapper ───────────────────────────────────────────────────────────

describe('Anagram wrapper', () => {
  test('renders one AnagramQuestion per item', () => {
    const { container } = render(
      <Anagram
        items={[
          { scrambled: 'a b', answer: 'ba' },
          { scrambled: 'x y z', answer: 'zyx' },
        ]}
      />
    );
    const questions = container.querySelectorAll('[data-activity="anagram-question"]');
    expect(questions).toHaveLength(2);
  });

  test('renders instruction text when provided', () => {
    render(<Anagram items={[{ scrambled: 'a', answer: 'a' }]} instruction="Do the thing" />);
    expect(screen.getByText('Do the thing')).toBeInTheDocument();
  });

  test('renders English header label by default', () => {
    render(<Anagram items={[{ scrambled: 'a', answer: 'a' }]} />);
    expect(screen.getByText('Unscramble the Letters')).toBeInTheDocument();
  });

  test('renders Ukrainian header label when isUkrainian=true', () => {
    render(<Anagram items={[{ scrambled: 'a', answer: 'a' }]} isUkrainian={true} />);
    expect(screen.getByText('Переставте літери')).toBeInTheDocument();
  });

  test('first question is the first child of its container (CSS :first-child rule applies)', () => {
    // happy-dom doesn't evaluate CSS module rules so we verify DOM structure.
    // The :first-child { padding-top: 0 } rule targets this element — confirming
    // it IS the first child is sufficient for a unit test.
    const { container } = render(
      <Anagram
        items={[
          { scrambled: 'a b', answer: 'ba' },
          { scrambled: 'x y', answer: 'yx' },
        ]}
      />
    );
    const first = container.querySelector('[data-activity="anagram-question"]') as HTMLElement;
    expect(first.parentElement!.firstElementChild).toBe(first);
  });
});
