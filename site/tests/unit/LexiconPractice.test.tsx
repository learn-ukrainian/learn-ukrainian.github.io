import { beforeEach, describe, expect, test, vi } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LexiconPractice from '@site/src/components/LexiconPractice';
import { SRS_STORAGE_KEY, loadState, type PracticeDeckEntry } from '@site/src/lib/lexicon/srs';

function card(slug: string, gloss: string, cefr = 'A1'): PracticeDeckEntry {
  return {
    lemma: slug,
    slug,
    gloss,
    ipa: null,
    pos: 'noun',
    cefr,
    heritage: 'native',
    example: `${slug} example`,
    audioKey: null,
  };
}

function sampleDeck(): PracticeDeckEntry[] {
  return [
    card('word1', 'first'),
    card('word2', 'second'),
    card('word3', 'third'),
    card('word4', 'fourth'),
    card('word5', 'fifth', 'B1'),
  ];
}

function storedState() {
  return JSON.parse(localStorage.getItem(SRS_STORAGE_KEY) ?? '{}');
}

beforeEach(() => {
  localStorage.clear();
  loadState(localStorage, new Date('2026-06-23T12:00:00.000Z'));
  vi.restoreAllMocks();
});

describe('LexiconPractice', () => {
  test('does not fetch the deck before a start or mode action', () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch');

    render(<LexiconPractice />);

    expect(fetchSpy).not.toHaveBeenCalled();
  });

  test('flip and rating persist SRS progress', async () => {
    const user = userEvent.setup();
    const { container } = render(<LexiconPractice initialDeck={sampleDeck()} autoStart />);

    const flashcard = container.querySelector<HTMLElement>('[data-activity="flashcard"]');
    expect(flashcard).toBeInTheDocument();
    await user.click(flashcard!);
    expect(flashcard).toHaveAttribute('data-flipped', 'true');

    await user.click(screen.getByRole('button', { name: 'Good' }));

    await waitFor(() => expect(storedState().cards.word1.reps).toBe(1));
    expect(storedState().reviews[0].rating).toBe('good');
  });

  test('quiz records the result and advances', async () => {
    const user = userEvent.setup();
    render(
      <LexiconPractice initialDeck={sampleDeck()} autoStart initialMode="quiz" advanceDelayMs={0} />,
    );
    const quiz = screen.getByTestId('practice-quiz');
    const options = quiz.querySelector('[data-activity="quiz-options"]');
    expect(options).toBeInTheDocument();

    await user.click(within(options as HTMLElement).getByRole('button', { name: 'first' }));

    await waitFor(() => expect(storedState().reviews[0].rating).toBe('good'));
    await waitFor(() => expect(screen.getByText('What does word2 mean?')).toBeInTheDocument());
  });

  test('quiz distractors come from the same CEFR band in the deck', () => {
    render(
      <LexiconPractice initialDeck={sampleDeck()} autoStart initialMode="quiz" advanceDelayMs={0} />,
    );
    const quiz = screen.getByTestId('practice-quiz');
    const options = within(quiz.querySelector('[data-activity="quiz-options"]') as HTMLElement)
      .getAllByRole('button')
      .map((button) => button.textContent?.trim());

    expect(new Set(options)).toEqual(new Set(['first', 'second', 'third', 'fourth']));
    expect(options).not.toContain('fifth');
  });
});
