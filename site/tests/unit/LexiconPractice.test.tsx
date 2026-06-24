import { beforeEach, describe, expect, test, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LexiconPractice from '@site/src/components/LexiconPractice';
import {
  SRS_STORAGE_KEY,
  cardKey,
  loadState,
  saveState,
  type PracticeDeckData,
  type PracticeLexeme,
} from '@site/src/lib/lexicon/srs';

const NOW = new Date('2026-06-23T12:00:00.000Z');

function lexeme(
  lemmaId: string,
  lemma: string,
  gloss: string,
  forms: { nominative: string; accusative: string; locative: string },
): PracticeLexeme {
  return {
    lemmaId,
    lemma,
    lemmaPlain: lemma,
    gloss,
    ipa: null,
    pos: 'noun',
    cefr: 'A1',
    heritage: 'native',
    severity: 'standard',
    paradigm: {
      cases: {
        nominative: { singular: forms.nominative },
        accusative: { singular: forms.accusative },
        locative: { singular: forms.locative },
      },
    },
  };
}

function sampleDeck(): PracticeDeckData {
  const lexemes = [
    lexeme('knyha', 'книга', 'book', {
      nominative: 'книга',
      accusative: 'книгу',
      locative: 'книзі',
    }),
    lexeme('robota', 'робота', 'work', {
      nominative: 'робота',
      accusative: 'роботу',
      locative: 'роботі',
    }),
    lexeme('misto', 'місто', 'city', {
      nominative: 'місто',
      accusative: 'місто',
      locative: 'місті',
    }),
    lexeme('shkola', 'школа', 'school', {
      nominative: 'школа',
      accusative: 'школу',
      locative: 'школі',
    }),
  ];
  return {
    deckVersion: 'test',
    level: 'A1',
    lexemes,
    index: lexemes.map((entry, index) => ({
      lemmaId: entry.lemmaId,
      lemma: entry.lemma,
      cefr: 'A1',
      modes: ['flashcards', 'matching', 'choice', ...(entry.lemmaId === 'knyha' ? ['cloze' as const] : [])],
      hasCloze: entry.lemmaId === 'knyha',
      clozeIds: entry.lemmaId === 'knyha' ? ['knyha-cloze-1'] : [],
      newOrder: index,
    })),
    cloze: [
      {
        clozeId: 'knyha-cloze-1',
        lemmaId: 'knyha',
        sentenceFrameId: 'reading-knyha-frame',
        sentence: 'Я читаю ___.',
        blankCase: 'accusative',
        form: 'книгу',
        clozeEn: 'I am reading a book.',
        caseRule: {
          ruleId: 'accusative_direct_object',
          case: 'accusative',
          caseLabel: 'знахідний',
          trigger: 'direct-object',
          triggerLabel: 'прямий додаток',
          feedback: 'читати + знахідний (книга -> книгу)',
        },
        options: [
          {
            optionId: 'knyha-cloze-1:answer',
            label: 'книгу',
            lemmaId: 'knyha',
            kind: 'answer',
            case: 'accusative',
          },
          {
            optionId: 'knyha-cloze-1:lemma',
            label: 'книга',
            lemmaId: 'knyha',
            kind: 'same-root-lemma',
            case: 'nominative',
          },
          {
            optionId: 'knyha-cloze-1:decoy-lemma',
            label: 'робота',
            lemmaId: 'robota',
            kind: 'decoy-lemma',
            case: 'nominative',
          },
          {
            optionId: 'knyha-cloze-1:decoy-oblique',
            label: 'роботу',
            lemmaId: 'robota',
            kind: 'decoy-oblique',
            case: 'accusative',
          },
        ],
      },
    ],
  };
}

function storedState() {
  return JSON.parse(localStorage.getItem(SRS_STORAGE_KEY) ?? '{}');
}

function seedRecognitionMastery(lemmaId: string) {
  const state = loadState(localStorage, NOW);
  state.cards.set(cardKey(lemmaId, 'flashcards'), {
    due: NOW.getTime(),
    stability: 6,
    difficulty: 4,
    elapsed_days: 0,
    scheduled_days: 3,
    learning_steps: 0,
    reps: 3,
    lapses: 0,
    state: 2,
  });
  saveState(state, localStorage, NOW.getTime());
}

beforeEach(() => {
  localStorage.clear();
  loadState(localStorage, NOW);
  vi.restoreAllMocks();
});

describe('LexiconPractice', () => {
  test('does not fetch deck before start mode action', () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch');

    render(<LexiconPractice />);

    expect(fetchSpy).not.toHaveBeenCalled();
  });

  test('flashcard rating persists mode-specific SRS progress', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <LexiconPractice initialDeck={sampleDeck()} autoStart initialMode="flashcards" />,
    );

    const flashcard = container.querySelector<HTMLElement>('[data-activity="flashcard"]');
    expect(flashcard).toBeInTheDocument();
    await user.click(flashcard!);
    expect(flashcard).toHaveAttribute('data-flipped', 'true');

    await user.click(screen.getByRole('button', { name: 'Good' }));

    await waitFor(() => {
      expect(storedState().cards[cardKey('knyha', 'flashcards')]).toBeTruthy();
    });
  });

  test('choice mode records result and advances through selector', async () => {
    const user = userEvent.setup();
    render(<LexiconPractice initialDeck={sampleDeck()} autoStart initialMode="choice" />);

    const choice = screen.getByTestId('practice-choice');
    expect(choice).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'книга' }));

    await waitFor(() => {
      const state = storedState();
      expect(state.reviews[0]).toMatchObject({
        lemmaId: 'knyha',
        mode: 'choice',
        rating: 'good',
      });
    });
  });

  test('cloze wrong-case answer records one case miss and leaves blank open', async () => {
    seedRecognitionMastery('knyha');
    const user = userEvent.setup();
    render(<LexiconPractice initialDeck={sampleDeck()} autoStart initialMode="cloze" />);

    expect(screen.getByTestId('practice-cloze')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'книга' }));

    const status = screen.getByRole('status');
    expect(status).toHaveTextContent('Правильне слово');
    expect(status).toHaveClass('case-miss');
    expect(screen.getByLabelText('Answer in знахідний')).toHaveValue('');
    expect(screen.getByRole('button', { name: 'книгу' })).not.toBeDisabled();

    await waitFor(() => {
      const state = storedState();
      expect(state.reviews).toHaveLength(1);
      expect(state.reviews[0]).toMatchObject({
        lemmaId: 'knyha',
        mode: 'cloze',
        rating: 'hard',
      });
    });

    await user.click(screen.getByRole('button', { name: 'книгу' }));

    await waitFor(() => {
      expect(storedState().reviews).toHaveLength(1);
    });
  });
});
