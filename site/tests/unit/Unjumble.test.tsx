import { describe, test, expect } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UnjumbleQuestion } from '@site/src/components/Unjumble';
import Unjumble from '@site/src/components/Unjumble';

// ── helpers ──────────────────────────────────────────────────────────────────

function tilesIn(container: HTMLElement, zone: string) {
  const el = container.querySelector(`[data-activity="${zone}"]`);
  if (!el) throw new Error(`Zone "${zone}" not found`);
  return within(el as HTMLElement).queryAllByRole('button');
}

function submitBtn(container: HTMLElement) {
  return [...container.querySelectorAll('button')].find(
    b => b.textContent === 'Check Answer' || b.textContent === 'Перевірити'
  )!;
}

function resetBtn(container: HTMLElement) {
  return [...container.querySelectorAll('button')].find(
    b => b.textContent === 'Try Again' || b.textContent === 'Спробувати знову'
  )!;
}

// ── UnjumbleQuestion ──────────────────────────────────────────────────────────

describe('UnjumbleQuestion', () => {
  const props = { words: 'dog / the / runs', answer: 'the dog runs' };

  test('renders word tiles in the word bank', () => {
    const { container } = render(<UnjumbleQuestion {...props} />);
    expect(tilesIn(container, 'word-bank').length).toBe(3);
  });

  test('sentence builder starts empty', () => {
    const { container } = render(<UnjumbleQuestion {...props} />);
    expect(tilesIn(container, 'sentence-builder').length).toBe(0);
  });

  test('renders hint when provided', () => {
    const { container } = render(<UnjumbleQuestion {...props} hint="An animal sentence" />);
    expect(container.textContent).toContain('An animal sentence');
  });

  test('does not render hint when not provided', () => {
    const { container } = render(<UnjumbleQuestion {...props} />);
    expect(container.textContent).not.toContain('💡');
  });

  test('clicking a word moves it from bank to builder', async () => {
    const user = userEvent.setup();
    const { container } = render(<UnjumbleQuestion {...props} />);

    const bankBefore = tilesIn(container, 'word-bank').length;
    await user.click(tilesIn(container, 'word-bank')[0]);

    expect(tilesIn(container, 'word-bank').length).toBe(bankBefore - 1);
    expect(tilesIn(container, 'sentence-builder').length).toBe(1);
  });

  test('clicking a word in builder moves it back to bank', async () => {
    const user = userEvent.setup();
    const { container } = render(<UnjumbleQuestion {...props} />);

    await user.click(tilesIn(container, 'word-bank')[0]);
    const bankCount = tilesIn(container, 'word-bank').length;

    await user.click(tilesIn(container, 'sentence-builder')[0]);

    expect(tilesIn(container, 'word-bank').length).toBe(bankCount + 1);
    expect(tilesIn(container, 'sentence-builder').length).toBe(0);
  });

  test('Check Answer is disabled while words remain in bank', () => {
    const { container } = render(<UnjumbleQuestion {...props} />);
    expect(submitBtn(container)).toBeDisabled();
  });

  test('Check Answer becomes enabled when all words are placed', async () => {
    const user = userEvent.setup();
    const { container } = render(<UnjumbleQuestion {...props} />);

    while (tilesIn(container, 'word-bank').length > 0) {
      await user.click(tilesIn(container, 'word-bank')[0]);
    }

    expect(submitBtn(container)).toBeEnabled();
  });

  test('feedback appears after submission', async () => {
    const user = userEvent.setup();
    const { container } = render(<UnjumbleQuestion {...props} />);

    while (tilesIn(container, 'word-bank').length > 0) {
      await user.click(tilesIn(container, 'word-bank')[0]);
    }
    await user.click(submitBtn(container));

    expect(container.querySelector('[data-activity="feedback"]')).toBeInTheDocument();
  });

  test('reset restores initial state', async () => {
    const user = userEvent.setup();
    const { container } = render(<UnjumbleQuestion {...props} />);

    const initialCount = tilesIn(container, 'word-bank').length;

    while (tilesIn(container, 'word-bank').length > 0) {
      await user.click(tilesIn(container, 'word-bank')[0]);
    }
    await user.click(submitBtn(container));
    await user.click(resetBtn(container));

    expect(tilesIn(container, 'word-bank').length).toBe(initialCount);
    expect(tilesIn(container, 'sentence-builder').length).toBe(0);
    expect(container.querySelector('[data-activity="feedback"]')).not.toBeInTheDocument();
  });

  test('accepts pipe-separated words', () => {
    const { container } = render(
      <UnjumbleQuestion words="one | two | three" answer="one two three" />
    );
    expect(tilesIn(container, 'word-bank').length).toBe(3);
  });

  test('accepts comma-separated words', () => {
    const { container } = render(
      <UnjumbleQuestion words="one, two, three" answer="one two three" />
    );
    expect(tilesIn(container, 'word-bank').length).toBe(3);
  });

  test('accepts jumbled field via the Unjumble wrapper', () => {
    // The `jumbled` alias is resolved in the Unjumble wrapper, not UnjumbleQuestion.
    const { container } = render(
      <Unjumble items={[{ jumbled: 'a / b / c', answer: 'a b c' }]} />
    );
    expect(tilesIn(container, 'word-bank').length).toBe(3);
  });
});

// ── Unjumble wrapper ──────────────────────────────────────────────────────────

describe('Unjumble wrapper', () => {
  test('renders one UnjumbleQuestion per item', () => {
    const { container } = render(
      <Unjumble
        items={[
          { words: 'a / b', answer: 'a b' },
          { words: 'x / y / z', answer: 'x y z' },
        ]}
      />
    );
    expect(
      container.querySelectorAll('[data-activity="unjumble-question"]')
    ).toHaveLength(2);
  });

  test('renders instruction text', () => {
    render(
      <Unjumble
        items={[{ words: 'a / b', answer: 'a b' }]}
        instruction="Put them in order"
      />
    );
    expect(screen.getByText('Put them in order')).toBeInTheDocument();
  });

  test('renders English header by default', () => {
    render(<Unjumble items={[{ words: 'a / b', answer: 'a b' }]} />);
    expect(screen.getByText('Build the Sentence')).toBeInTheDocument();
  });

  test('renders Ukrainian header when isUkrainian=true', () => {
    render(<Unjumble items={[{ words: 'a / b', answer: 'a b' }]} isUkrainian={true} />);
    expect(screen.getByText('Складіть речення')).toBeInTheDocument();
  });

  test('first question is the first child of its container (CSS :first-child rule applies)', () => {
    // happy-dom doesn't evaluate CSS module rules so we verify DOM structure.
    const { container } = render(
      <Unjumble
        items={[
          { words: 'a / b', answer: 'a b' },
          { words: 'x / y', answer: 'x y' },
        ]}
      />
    );
    const first = container.querySelector('[data-activity="unjumble-question"]') as HTMLElement;
    expect(first.parentElement!.firstElementChild).toBe(first);
  });
});
