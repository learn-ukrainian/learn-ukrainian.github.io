import { describe, test, expect, beforeEach, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UnjumbleQuestion, normalizeUnjumbleAnswer } from '@site/src/components/Unjumble';
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
  beforeEach(() => {
    document.documentElement.dataset.chromeLocale = 'en';
  });

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

  test('reports completion to a practice host after checking', async () => {
    const onComplete = vi.fn();
    const user = userEvent.setup();
    const { container } = render(
      <UnjumbleQuestion words="the / dog / runs" answer="the dog runs" onComplete={onComplete} />,
    );

    for (const word of ['the', 'dog', 'runs']) {
      await user.click(within(container.querySelector('[data-activity="word-bank"]')!).getByRole('button', { name: word }));
    }
    await user.click(submitBtn(container));

    expect(onComplete).toHaveBeenCalledOnce();
    expect(onComplete).toHaveBeenCalledWith(true);
  });

  test('letter tiles grade as a word when the answer has no spaces', async () => {
    const onComplete = vi.fn();
    const user = userEvent.setup();
    const { container } = render(
      <UnjumbleQuestion words="д / і / м" answer="дім" onComplete={onComplete} />,
    );

    for (const letter of ['д', 'і', 'м']) {
      await user.click(within(container.querySelector('[data-activity="word-bank"]')!).getByRole('button', { name: letter }));
    }
    await user.click(submitBtn(container));

    expect(onComplete).toHaveBeenCalledWith(true);
    expect(container.querySelector('[data-correct="true"]')).toBeInTheDocument();
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

  test('preserves punctuation inside already-jumbled tokens during round-trip', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <UnjumbleQuestion
        words="дім, / який / ..."
        answer="дім, який ..."
        wordsAreJumbled
      />
    );

    for (const word of ['дім,', 'який', '...']) {
      const wordBank = within(container.querySelector('[data-activity="word-bank"]')!);
      await user.click(wordBank.getByRole('button', { name: word }));
    }
    await user.click(submitBtn(container));

    expect(container.querySelector('[data-activity="feedback"]')).toHaveAttribute('data-correct', 'true');
  });

  // Tiles never carry punctuation, but the YAML `answer` field can (see #7994:
  // Gemini audit of things-have-gender act-104/act-205/act-305).
  describe('grading tolerates punctuation absent from the tiles', () => {
  beforeEach(() => {
    document.documentElement.dataset.chromeLocale = 'en';
  });

    // Tiles shuffle to a guaranteed-wrong order, so placing them correctly
    // means clicking each tile by name in the intended sentence order.
    async function placeInOrderAndCheck(
      container: HTMLElement,
      user: ReturnType<typeof userEvent.setup>,
      orderedWords: string[]
    ) {
      for (const word of orderedWords) {
        const wordBank = within(container.querySelector('[data-activity="word-bank"]')!);
        await user.click(wordBank.getByRole('button', { name: word }));
      }
      await user.click(submitBtn(container));
    }

    test('answer with a terminal period grades correct', async () => {
      const user = userEvent.setup();
      const { container } = render(
        <UnjumbleQuestion words="Це / моя / книга" answer="Це моя книга." />
      );
      await placeInOrderAndCheck(container, user, ['Це', 'моя', 'книга']);
      expect(container.querySelector('[data-correct="true"]')).toBeInTheDocument();
    });

    test('answer with a terminal question mark grades correct', async () => {
      const user = userEvent.setup();
      const { container } = render(
        <UnjumbleQuestion words="Ти / йдеш" answer="Ти йдеш?" />
      );
      await placeInOrderAndCheck(container, user, ['Ти', 'йдеш']);
      expect(container.querySelector('[data-correct="true"]')).toBeInTheDocument();
    });

    test('answer with an internal clause comma grades correct', async () => {
      const user = userEvent.setup();
      const { container } = render(
        <UnjumbleQuestion words="Привіт / як / справи" answer="Привіт, як справи" />
      );
      await placeInOrderAndCheck(container, user, ['Привіт', 'як', 'справи']);
      expect(container.querySelector('[data-correct="true"]')).toBeInTheDocument();
    });

    test('an exact already-matching answer still grades correct (no false positive removed)', async () => {
      const user = userEvent.setup();
      const { container } = render(
        <UnjumbleQuestion words="the / dog / runs" answer="the dog runs" />
      );
      await placeInOrderAndCheck(container, user, ['the', 'dog', 'runs']);
      expect(container.querySelector('[data-correct="true"]')).toBeInTheDocument();
    });

    test('a genuinely wrong order still grades incorrect', async () => {
      const user = userEvent.setup();
      const { container } = render(
        <UnjumbleQuestion words="Це / моя / книга" answer="Це моя книга." />
      );
      // Place in reverse order instead of the correct order.
      const bank = () => container.querySelector<HTMLElement>('[data-activity="word-bank"]')!;
      for (const word of ['книга', 'моя', 'Це']) {
        await user.click(within(bank()).getByRole('button', { name: word }));
      }
      await user.click(submitBtn(container));
      expect(container.querySelector('[data-correct="false"]')).toBeInTheDocument();
    });
  });
});

describe('normalizeUnjumbleAnswer', () => {
  beforeEach(() => {
    document.documentElement.dataset.chromeLocale = 'en';
  });

  test('strips a terminal period', () => {
    expect(normalizeUnjumbleAnswer('Це моя книга.')).toBe('це моя книга');
  });

  test('strips a terminal question mark', () => {
    expect(normalizeUnjumbleAnswer('Ти йдеш?')).toBe('ти йдеш');
  });

  test('strips a terminal exclamation mark', () => {
    expect(normalizeUnjumbleAnswer('Привіт!')).toBe('привіт');
  });

  test('drops internal clause commas and collapses the resulting whitespace', () => {
    expect(normalizeUnjumbleAnswer('Привіт, як справи')).toBe('привіт як справи');
  });

  test('is a no-op (besides casefolding) for an answer with no punctuation', () => {
    expect(normalizeUnjumbleAnswer('the dog runs')).toBe('the dog runs');
  });

  test('ignores a combining stress mark (U+0301)', () => {
    expect(normalizeUnjumbleAnswer('буря\u0301к')).toBe('буряк');
    expect(normalizeUnjumbleAnswer('буря\u0301к')).toBe(normalizeUnjumbleAnswer('буряк'));
  });

  test('ignores precomposed stress marks too', () => {
    expect(normalizeUnjumbleAnswer('\u00E1')).toBe('a');
    expect(normalizeUnjumbleAnswer('Ма\u0301ма')).toBe('мама');
  });

  test('keeps й and ї intact when stripping stress', () => {
    expect(normalizeUnjumbleAnswer('Йой Їжа\u0301к')).toBe('йой їжак');
  });

  test('treats punctuated and unpunctuated forms of the same sentence as equal', () => {
    expect(normalizeUnjumbleAnswer('Привіт, як справи?')).toBe(
      normalizeUnjumbleAnswer('Привіт як справи')
    );
  });
});

describe('UnjumbleQuestion with a stressed answer', () => {
  beforeEach(() => {
    document.documentElement.dataset.chromeLocale = 'en';
  });

  test('letter tiles б/у/р/я/к are graded correct against буря́к', async () => {
    const user = userEvent.setup();
    const { container } = render(<UnjumbleQuestion words="к / я / б / р / у" answer={'буря\u0301к'} />);

    for (const letter of ['б', 'у', 'р', 'я', 'к']) {
      const tile = tilesIn(container, 'word-bank').find(t => t.textContent?.trim() === letter)!;
      await user.click(tile);
    }
    await user.click(submitBtn(container));

    expect(container.querySelector('[data-correct="true"]')).toBeInTheDocument();
    expect(container.querySelector('[data-correct="false"]')).not.toBeInTheDocument();
  });
});

// ── Unjumble wrapper ──────────────────────────────────────────────────────────

describe('Unjumble wrapper', () => {
  beforeEach(() => {
    document.documentElement.dataset.chromeLocale = 'en';
  });

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
    document.documentElement.dataset.chromeLocale = 'en';
    render(<Unjumble items={[{ words: 'a / b', answer: 'a b' }]} />);
    expect(screen.getByText('Build the Sentence')).toBeInTheDocument();
  });

  test('renders Ukrainian header when chrome locale is uk', () => {
    document.documentElement.dataset.chromeLocale = 'uk';
    render(<Unjumble items={[{ words: 'a / b', answer: 'a b' }]} isUkrainian={false} />);
    expect(screen.getByText('Складіть речення')).toBeInTheDocument();
  });

  test('letter-tile activities use Build the Word chrome', () => {
    document.documentElement.dataset.chromeLocale = 'en';
    render(<Unjumble items={[{ words: 'д / е / н / ь', answer: 'день' }]} />);
    expect(screen.getByText('Build the Word')).toBeInTheDocument();
    expect(screen.queryByText('Build the Sentence')).not.toBeInTheDocument();
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
