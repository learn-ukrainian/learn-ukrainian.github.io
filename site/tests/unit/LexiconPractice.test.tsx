import { beforeEach, describe, expect, test, vi } from 'vitest';
import { State } from 'ts-fsrs';
import { act, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LexiconPractice from '@site/src/components/LexiconPractice';
import {
  SRS_STORAGE_KEY,
  cardKey,
  loadState,
  saveState,
  type PracticeDeckData,
  type PracticeHeritageItem,
  type PracticeLexeme,
  type PracticeMode,
  type PracticeRating,
  type ReviewLogEntry,
} from '@site/src/lib/lexicon/srs';
import { LEARNER_LEVEL_STORAGE_KEY, type CefrLevel } from '@site/src/lib/lexicon/levels';

const NOW = new Date('2026-06-23T12:00:00.000Z');

function okJson(body: unknown): Response {
  return { ok: true, json: async () => body } as unknown as Response;
}

function notFoundResponse(): Response {
  return { ok: false, json: async () => ({}) } as unknown as Response;
}

/** Mock fetch for the level-sharded practice deck; `counts` lists which levels are published. */
function mockShardFetch(counts: Partial<Record<CefrLevel, number>>) {
  const requested: string[] = [];
  const fn = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    requested.push(url);
    const match = url.match(
      /practice-(index|lexemes|cloze|stress|classify|paradigm|synonym|heritage)\.([ABC][12])\.json/,
    );
    if (!match) return notFoundResponse();
    const kind = match[1] as
      | 'index'
      | 'lexemes'
      | 'cloze'
      | 'stress'
      | 'classify'
      | 'paradigm'
      | 'synonym'
      | 'heritage';
    const level = match[2] as CefrLevel;
    const n = counts[level];
    if (n === undefined) return notFoundResponse(); // shard not published (e.g. C2)
    if (kind !== 'index' && kind !== 'lexemes') return okJson({ [kind]: [] });
    const lexemes = Array.from({ length: n }, (_unused, i) =>
      lexeme(
        `${level}-${i}`,
        `слово-${level}-${i}`,
        `gloss ${level} ${i}`,
        {
          nominative: `слово-${level}-${i}`,
          accusative: `слово-${level}-${i}`,
          locative: `слово-${level}-${i}`,
        },
        { cefr: level },
      ),
    );
    if (kind === 'index') {
      return okJson({
        deckVersion: `v-${level}`,
        level,
        items: lexemes.map((lex, order) => ({
          lemmaId: lex.lemmaId,
          lemma: lex.lemma,
          cefr: level,
          modes: ['flashcards', 'matching', 'choice'],
          hasCloze: false,
          clozeIds: [],
          newOrder: order,
        })),
      });
    }
    return okJson({ deckVersion: `v-${level}`, level, lexemes });
  });
  return { fn, requested };
}

function lexeme(
  lemmaId: string,
  lemma: string,
  gloss: string,
  forms: { nominative: string; accusative: string; locative: string },
  overrides: Partial<PracticeLexeme> = {},
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
    ...overrides,
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

function heritagePracticeItem(): PracticeHeritageItem {
  return {
    heritageId: 'her-dim-fixture',
    lemmaId: 'dim',
    srsKey: cardKey('dim', 'heritage'),
    lemma: 'дім',
    nativeLemma: 'дім',
    calqueLabel: 'дом',
    kind: 'lexical',
    prompt: 'Я бачу ___ щодня.',
    answer: 'дім',
    calque: 'дом',
    origin: 'fixture',
    frameIndex: 1,
    cefr: 'A2',
    options: [
      { label: 'дім' },
      { label: 'дом' },
      { label: 'хата' },
      { label: 'місто' },
    ],
    rationale: 'у цьому значенні потрібне питоме слово',
    rationaleUk: 'у цьому значенні потрібне питоме слово',
    citations: ['Антоненко-Давидович: fixture'],
    corrections: ['дім'],
    sourceFamily: 'fixture',
  };
}

function heritageDeck({ includeItems = true } = {}): PracticeDeckData {
  const entry = lexeme(
    'dim',
    'дім',
    'home',
    {
      nominative: 'дім',
      accusative: 'дім',
      locative: 'домі',
    },
    { cefr: 'A2', heritage: 'native' },
  );
  return {
    deckVersion: 'test-heritage',
    level: 'A2',
    lexemes: [entry],
    index: [
      {
        lemmaId: entry.lemmaId,
        lemma: entry.lemma,
        cefr: 'A2',
        modes: ['heritage'],
        hasCloze: false,
        clozeIds: [],
        newOrder: 0,
      },
    ],
    cloze: [],
    stress: [],
    classify: [],
    paradigm: [],
    synonym: [],
    heritage: includeItems ? [heritagePracticeItem()] : [],
  };
}

function sampleDeckWithOnlyMode(lemmaId: string, mode: PracticeMode): PracticeDeckData {
  const baseDeck = sampleDeck();
  return {
    ...baseDeck,
    index: baseDeck.index.map((item) => ({
      ...item,
      modes: item.lemmaId === lemmaId ? [mode] : [],
      hasCloze: false,
      clozeIds: [],
    })),
    cloze: [],
  };
}

function wordToMeaningDeck(): PracticeDeckData {
  const lexemes = [
    lexeme('sady', 'сад', 'garden', {
      nominative: 'сад',
      accusative: 'сад',
      locative: 'саду',
    }),
    lexeme('dimy', 'дім', 'house', {
      nominative: 'дім',
      accusative: 'дім',
      locative: 'домі',
    }),
    lexeme('lisy', 'ліс', 'forest', {
      nominative: 'ліс',
      accusative: 'ліс',
      locative: 'лісі',
    }),
    lexeme('rich', 'річка', 'river', {
      nominative: 'річка',
      accusative: 'річку',
      locative: 'річці',
    }),
    lexeme(
      'taxy',
      'та',
      'and; but; while',
      {
        nominative: 'та',
        accusative: 'та',
        locative: 'та',
      },
      { glossClean: 'and', meaningMcEligible: false, pos: 'conj' },
    ),
    lexeme(
      'ityx',
      'іти',
      'to go',
      {
        nominative: 'іти',
        accusative: 'іти',
        locative: 'іти',
      },
      { pos: 'verb' },
    ),
  ];
  return {
    deckVersion: 'test-choice-clean-glosses',
    level: 'A1',
    lexemes,
    index: lexemes.map((entry, index) => ({
      lemmaId: entry.lemmaId,
      lemma: entry.lemma,
      cefr: 'A1',
      modes:
        entry.meaningMcEligible === false || entry.lemmaId === 'ityx'
          ? ['flashcards']
          : ['flashcards', 'matching', 'choice'],
      hasCloze: false,
      clozeIds: [],
      newOrder: index,
    })),
    cloze: [],
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

/** Seed the SRS review log with `total` cloze reviews of `caseKey`, `misses` failed. */
function seedWeakCaseLog(caseKey: string, total: number, misses: number) {
  const state = loadState(localStorage, NOW);
  for (let index = 0; index < total; index += 1) {
    const rating: PracticeRating = index < misses ? 'again' : 'good';
    const review: ReviewLogEntry = {
      cardKey: cardKey(`${caseKey}-${index}`, 'cloze'),
      lemmaId: `${caseKey}-${index}`,
      mode: 'cloze',
      rating,
      state: State.Review,
      due: NOW.getTime() + index * 1000,
      stability: 4,
      difficulty: 5,
      elapsed_days: 1,
      last_elapsed_days: 1,
      scheduled_days: 1,
      learning_steps: 0,
      review: NOW.getTime() + index * 1000,
      blankCase: caseKey,
    };
    state.reviews.push(review);
  }
  saveState(state, localStorage, NOW.getTime());
}

beforeEach(() => {
  localStorage.clear();
  loadState(localStorage, NOW);
  vi.restoreAllMocks();
});

describe('LexiconPractice', () => {
  test('eager-loads only the index (not lexemes/cloze) before a mode starts', async () => {
    const { fn, requested } = mockShardFetch({ A1: 2 });
    vi.spyOn(globalThis, 'fetch').mockImplementation(fn);

    render(<LexiconPractice />);

    // The due-count tile eager-loads the lightweight index on mount so a returning
    // learner sees their SRS due-count immediately...
    await waitFor(() =>
      expect(requested.some((u) => u.includes('practice-index.A1'))).toBe(true),
    );
    // ...while the heavy lexeme/cloze shards stay lazy until a mode actually starts.
    expect(requested.some((u) => u.includes('practice-lexemes'))).toBe(false);
    expect(requested.some((u) => u.includes('practice-cloze'))).toBe(false);
  });

  test('shows due review count on the home before any session starts', async () => {
    const { fn } = mockShardFetch({ A1: 3 });
    vi.spyOn(globalThis, 'fetch').mockImplementation(fn);
    const state = loadState(localStorage, NOW);
    state.cards.set(cardKey('A1-0', 'flashcards'), {
      due: NOW.getTime() - 60_000,
      stability: 4,
      difficulty: 4,
      elapsed_days: 1,
      scheduled_days: 1,
      learning_steps: 0,
      reps: 2,
      lapses: 0,
      state: 2,
    });
    saveState(state, localStorage, NOW.getTime());

    render(<LexiconPractice />);

    await waitFor(() =>
      expect(screen.getByLabelText('1 до повторення')).toBeInTheDocument(),
    );
  });

  test('caps the practice pool at the learner level (cumulative, never higher levels)', async () => {
    localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, 'B1');
    const { fn, requested } = mockShardFetch({ A1: 2, A2: 1, B1: 3, B2: 5, C1: 4 });
    vi.spyOn(globalThis, 'fetch').mockImplementation(fn);
    const user = userEvent.setup();
    const { container } = render(<LexiconPractice />);

    await user.click(container.querySelector<HTMLButtonElement>('[data-mode="flashcards"]')!);

    // A1+A2+B1 load (cumulative); B2/C1 are above the learner level and must never be fetched.
    await waitFor(() =>
      expect(requested.some((u) => u.includes('practice-index.B1'))).toBe(true),
    );
    expect(requested.some((u) => u.includes('practice-index.A1'))).toBe(true);
    expect(requested.some((u) => u.includes('practice-index.A2'))).toBe(true);
    expect(requested.some((u) => u.includes('practice-index.B1'))).toBe(true);
    expect(requested.some((u) => u.includes('practice-index.B2'))).toBe(false);
    expect(requested.some((u) => u.includes('practice-index.C1'))).toBe(false);
  });

  test('level selector re-caps the pool and persists the shared learner-level key', async () => {
    localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, 'A1');
    const { fn, requested } = mockShardFetch({ A1: 2, A2: 1, B1: 3 });
    vi.spyOn(globalThis, 'fetch').mockImplementation(fn);
    const user = userEvent.setup();
    const { container } = render(<LexiconPractice />);

    await user.click(screen.getByRole('button', { name: 'B1' }));
    expect(localStorage.getItem(LEARNER_LEVEL_STORAGE_KEY)).toBe('B1');

    await user.click(container.querySelector<HTMLButtonElement>('[data-mode="flashcards"]')!);
    await waitFor(() =>
      expect(requested.some((u) => u.includes('practice-index.B1'))).toBe(true),
    );
    expect(requested.some((u) => u.includes('practice-index.A1'))).toBe(true);
    expect(requested.some((u) => u.includes('practice-index.A2'))).toBe(true);
    expect(requested.some((u) => u.includes('practice-index.B2'))).toBe(false);
  });

  test('flashcard rating persists mode-specific SRS progress', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <LexiconPractice initialDeck={sampleDeckWithOnlyMode('knyha', 'flashcards')} autoStart initialMode="flashcards" />,
    );

    const flashcard = container.querySelector<HTMLElement>('[data-activity="flashcard"]');
    expect(flashcard).toBeInTheDocument();
    const goodButton = container.querySelector<HTMLButtonElement>('[data-rate="good"]')!;
    expect(goodButton).toBeDisabled();

    await user.click(flashcard!);
    expect(flashcard).toHaveAttribute('data-flipped', 'true');
    expect(goodButton).not.toBeDisabled();

    await user.click(goodButton);

    await waitFor(() => {
      expect(storedState().cards[cardKey('knyha', 'flashcards')]).toBeTruthy();
    });
  });

  test('choice mode records result and advances through selector', async () => {
    const user = userEvent.setup();
    render(<LexiconPractice initialDeck={sampleDeckWithOnlyMode('knyha', 'choice')} autoStart initialMode="choice" />);

    const choice = screen.getByTestId('practice-choice');
    expect(choice).toBeInTheDocument();
    // Option buttons now carry a "1-4" key span, so the accessible name is e.g. "1 книга".
    await user.click(screen.getByRole('button', { name: /книга/ }));

    await waitFor(() => {
      const state = storedState();
      expect(state.reviews[0]).toMatchObject({
        lemmaId: 'knyha',
        mode: 'choice',
        rating: 'good',
      });
    });
  });

  test('choice mode shows only clean same-pos meaning labels', () => {
    render(<LexiconPractice initialDeck={wordToMeaningDeck()} autoStart initialMode="choice" />);
    const choice = screen.getByTestId('practice-choice');

    expect(screen.getByText(/^Що означає «(сад|дім|ліс|річка)»\?$/)).toBeInTheDocument();
    // The option label lives in its own span next to the "1-4" key span; read just the label.
    const labels = within(choice)
      .getAllByRole('button')
      .map((button) => button.querySelector('span:not(.mc-key)')?.textContent ?? '');

    expect(new Set(labels)).toEqual(new Set(['garden', 'house', 'forest', 'river']));
    expect(labels).not.toContain('and');
    expect(labels).not.toContain('and; but; while');
    expect(labels).not.toContain('to go');
    for (const label of labels) {
      expect(label).not.toMatch(/[?(]/);
      expect(label.trim().split(/\s+/)).toHaveLength(1);
    }
  });

  test('choice backfills distractors across POS when same-POS pool is too small', () => {
    // The answer (a verb) has only ONE same-POS peer, but four other eligible words
    // exist. The old strict-subset logic discarded the cross-POS pool and starved the
    // distractor list (<3) -> the card could not render. It must now backfill to a
    // full 4-option card.
    const lexemes = [
      lexeme('bachyty', 'бачити', 'to see', { nominative: 'бачити', accusative: 'бачити', locative: 'бачити' }, { pos: 'verb' }),
      lexeme('ity', 'іти', 'to go', { nominative: 'іти', accusative: 'іти', locative: 'іти' }, { pos: 'verb' }),
      lexeme('sad', 'сад', 'garden', { nominative: 'сад', accusative: 'сад', locative: 'саду' }),
      lexeme('dim', 'дім', 'house', { nominative: 'дім', accusative: 'дім', locative: 'домі' }),
      lexeme('lis', 'ліс', 'forest', { nominative: 'ліс', accusative: 'ліс', locative: 'лісі' }),
    ];
    const deck: PracticeDeckData = {
      deckVersion: 'test-small-pos-pool',
      level: 'A1',
      lexemes,
      index: lexemes.map((entry, index) => ({
        lemmaId: entry.lemmaId,
        lemma: entry.lemma,
        cefr: 'A1',
        modes: entry.lemmaId === 'bachyty' ? ['choice'] : ['flashcards'],
        hasCloze: false,
        clozeIds: [],
        newOrder: index,
      })),
      cloze: [],
    };
    render(<LexiconPractice initialDeck={deck} autoStart initialMode="choice" />);
    const choice = screen.getByTestId('practice-choice');
    const labels = within(choice)
      .getAllByRole('button')
      .map((button) => button.querySelector('span:not(.mc-key)')?.textContent ?? '');
    // The only selectable choice card is the small-POS verb. Without cross-POS backfill it
    // would starve (<3 distractors) and not render; it must show a full 4-option set.
    expect(labels).toHaveLength(4);
    // The verb answer is present whichever polarity the selector picked.
    expect(labels.some((label) => label === 'бачити' || label === 'to see')).toBe(true);
  });

  test('heritage renders in mixed sessions and heritage focus mode', async () => {
    const user = userEvent.setup();
    const mixedRender = render(
      <LexiconPractice
        initialDeck={heritageDeck()}
        autoStart
        initialMode="mixed"
        advanceDelayMs={10_000}
      />,
    );

    expect(screen.getByTestId('practice-heritage')).toBeInTheDocument();
    expect(screen.getByText('Оберіть питоме українське слово.')).toBeInTheDocument();
    expect(screen.getByText(/Я бачу/)).toBeInTheDocument();

    mixedRender.unmount();
    const { container } = render(<LexiconPractice initialDeck={heritageDeck()} advanceDelayMs={10_000} />);
    expect(screen.getByText('Спадщина')).toBeInTheDocument();

    await user.click(container.querySelector<HTMLButtonElement>('[data-mode="heritage"]')!);

    expect(await screen.findByTestId('practice-heritage')).toBeInTheDocument();
  });

  test('heritage calque miss scores again and shows cited correction', async () => {
    const user = userEvent.setup();
    render(
      <LexiconPractice
        initialDeck={heritageDeck()}
        autoStart
        initialMode="heritage"
        advanceDelayMs={10_000}
      />,
    );

    await user.click(
      within(screen.getByTestId('practice-heritage')).getByRole('button', { name: /дом/ }),
    );

    const feedback = screen.getByTestId('practice-heritage-feedback');
    expect(feedback).toHaveTextContent('⚠️ калька; у цьому значенні потрібне питоме слово');
    expect(feedback).toHaveTextContent('Джерело: Антоненко-Давидович: fixture');
    await waitFor(() => {
      expect(storedState().reviews[0]).toMatchObject({
        lemmaId: 'dim',
        mode: 'heritage',
        rating: 'again',
        cardKey: cardKey('dim', 'heritage'),
      });
    });
  });

  test('heritage plain distractor miss does not leak calque correction feedback', async () => {
    const user = userEvent.setup();
    render(
      <LexiconPractice
        initialDeck={heritageDeck()}
        autoStart
        initialMode="heritage"
        advanceDelayMs={10_000}
      />,
    );

    await user.click(
      within(screen.getByTestId('practice-heritage')).getByRole('button', { name: /місто/ }),
    );

    const feedback = screen.getByTestId('practice-heritage-feedback');
    expect(feedback).toHaveTextContent('Ще раз');
    expect(feedback).not.toHaveTextContent('калька');
    expect(feedback).not.toHaveTextContent('у цьому значенні потрібне питоме слово');
    expect(feedback).not.toHaveTextContent('Антоненко-Давидович');
    await waitFor(() => {
      expect(storedState().reviews[0]).toMatchObject({
        lemmaId: 'dim',
        mode: 'heritage',
        rating: 'again',
      });
    });
  });

  test('heritage correct answer scores good', async () => {
    const user = userEvent.setup();
    render(
      <LexiconPractice
        initialDeck={heritageDeck()}
        autoStart
        initialMode="heritage"
        advanceDelayMs={10_000}
      />,
    );

    await user.click(
      within(screen.getByTestId('practice-heritage')).getByRole('button', { name: /дім/ }),
    );

    expect(screen.getByTestId('practice-heritage-feedback')).toHaveTextContent('Правильно');
    await waitFor(() => {
      expect(storedState().reviews[0]).toMatchObject({
        lemmaId: 'dim',
        mode: 'heritage',
        rating: 'good',
        cardKey: cardKey('dim', 'heritage'),
      });
    });
  });

  test('hides heritage mode card when the loaded deck has no heritage items', () => {
    render(<LexiconPractice initialDeck={heritageDeck({ includeItems: false })} />);

    expect(screen.queryByText('Спадщина')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Спадщина/ })).not.toBeInTheDocument();
  });

  test('heritage feedback renders rationaleUk when present and OMITS the detail line when absent', async () => {
    const user = userEvent.setup();

    // 1. With rationaleUk present
    const itemWithRationale = heritagePracticeItem();
    itemWithRationale.rationaleUk = 'питоме слово замість кальки';
    itemWithRationale.rationale = 'some english detail';
    const deckWithRationale = heritageDeck();
    deckWithRationale.heritage = [itemWithRationale];

    const { unmount } = render(
      <LexiconPractice
        initialDeck={deckWithRationale}
        autoStart
        initialMode="heritage"
        advanceDelayMs={10_000}
      />,
    );

    await user.click(
      within(screen.getByTestId('practice-heritage')).getByRole('button', { name: /дом/ }),
    );

    const feedbackText = screen.getByTestId('practice-heritage-feedback').textContent;
    expect(feedbackText).toContain('питоме слово замість кальки');
    expect(feedbackText).not.toContain('some english detail');

    unmount();

    // 2. With rationaleUk absent
    const itemWithoutRationale = heritagePracticeItem();
    itemWithoutRationale.rationaleUk = undefined;
    itemWithoutRationale.rationale = 'english explanation';
    itemWithoutRationale.citations = []; // clear citations so they don't render
    const deckWithoutRationale = heritageDeck();
    deckWithoutRationale.heritage = [itemWithoutRationale];

    render(
      <LexiconPractice
        initialDeck={deckWithoutRationale}
        autoStart
        initialMode="heritage"
        advanceDelayMs={10_000}
      />,
    );

    await user.click(
      within(screen.getByTestId('practice-heritage')).getByRole('button', { name: /дом/ }),
    );

    const feedbackTextWithout = screen.getByTestId('practice-heritage-feedback').textContent;
    expect(feedbackTextWithout).toBe('⚠️ калькаВідкрити в Атласі →');
    expect(feedbackTextWithout).not.toContain('english explanation');
  });

  test('«Відкрити в Атласі →» link present in heritage feedback with correct href', async () => {
    const user = userEvent.setup();
    render(
      <LexiconPractice
        initialDeck={heritageDeck()}
        autoStart
        initialMode="heritage"
        advanceDelayMs={10_000}
      />,
    );

    await user.click(
      within(screen.getByTestId('practice-heritage')).getByRole('button', { name: /дом/ }),
    );

    const link = screen.getByRole('link', { name: 'Відкрити в Атласі →' });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/lexicon/dim/');
  });

  test('focus deep-link: deck filtered to the lemma, no double session start', async () => {
    const originalSearch = window.location.search;
    delete (window as any).location;
    window.location = new URL('http://localhost/lexicon/practice/?lemmaId=dim') as any;

    try {
      const setItemSpy = vi.spyOn(localStorage, 'setItem');
      const removeItemSpy = vi.spyOn(localStorage, 'removeItem');
      const { fn } = mockShardFetch({ A1: 2, A2: 2 });
      vi.spyOn(globalThis, 'fetch').mockImplementation(fn);

      const sampleDeck = heritageDeck();
      const multiLemmaDeck: PracticeDeckData = {
        ...sampleDeck,
        index: [
          { lemmaId: 'dim', lemma: 'дім', cefr: 'A2', modes: ['heritage'], hasCloze: false, clozeIds: [], newOrder: 0 },
          { lemmaId: 'knyha', lemma: 'книга', cefr: 'A1', modes: ['flashcards'], hasCloze: false, clozeIds: [], newOrder: 1 },
        ],
      };

      render(<LexiconPractice initialDeck={multiLemmaDeck} autoStart={false} />);

      await waitFor(() => {
        expect(screen.getByTestId('practice-heritage')).toBeInTheDocument();
      });
      expect(screen.queryByTestId('practice-flashcards')).not.toBeInTheDocument();

      const snapshotWrites = setItemSpy.mock.calls.filter(([key]) => key === 'lu-practice-session');
      const snapshotRemoves = removeItemSpy.mock.calls.filter(([key]) => key === 'lu-practice-session');
      expect(snapshotRemoves.length).toBe(1);
      expect(snapshotWrites.length).toBe(1);

      const startedSnapshot = JSON.parse(snapshotWrites[0][1]);
      expect(startedSnapshot).not.toBeNull();
      expect(startedSnapshot.modeFilter).toBe('mixed');
      expect(startedSnapshot.budget).toBe(10);
    } finally {
      window.location = new URL('http://localhost/') as any;
      vi.restoreAllMocks();
    }
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
    expect(screen.getByLabelText('Відповідь у знахідний')).toHaveValue('');
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

  test('cloze renders Tatoeba attribution when present', () => {
    seedRecognitionMastery('knyha');
    const deck = sampleDeck();
    deck.cloze[0] = {
      ...deck.cloze[0],
      attribution: {
        source: 'Tatoeba',
        sourceUrl: 'https://tatoeba.org/en/sentences/show/101',
        uk: { sentenceId: 101, author: 'uk-author', license: 'CC-BY 2.0 FR' },
        en: { sentenceId: 202, author: 'en-author', license: 'CC-BY 2.0 FR' },
      },
    };

    render(<LexiconPractice initialDeck={deck} autoStart initialMode="cloze" />);

    expect(screen.getByRole('link', { name: 'Tatoeba' })).toHaveAttribute(
      'href',
      'https://tatoeba.org/en/sentences/show/101',
    );
    expect(screen.getByText(/uk-author/)).toHaveTextContent('en-author');
    expect(screen.getByText(/CC-BY 2.0 FR/)).toBeInTheDocument();
  });

  test('today ring uses review + capped-new denominator, not whole deck', async () => {
    const { fn } = mockShardFetch({ A1: 1150 });
    vi.spyOn(globalThis, 'fetch').mockImplementation(fn);
    render(<LexiconPractice />);
    await waitFor(() => expect(screen.getByTestId('practice-today-ring')).toBeInTheDocument());
    const ring = screen.getByTestId('practice-today-ring');
    expect(ring.textContent).toMatch(/0\/\d+/);
    const denominator = Number(ring.textContent?.split('/')[1]);
    expect(denominator).toBeLessThan(1150);
  });

  test('A1 renders English subtitles on session labels; A2 does not', async () => {
    localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, 'A1');
    const { unmount } = render(<LexiconPractice />);
    expect(screen.getByText('Start session')).toBeInTheDocument();
    unmount();

    localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, 'A2');
    render(<LexiconPractice />);
    expect(screen.queryByText('Start session')).not.toBeInTheDocument();
  });

  test('unpublished C2 level button is disabled with «скоро»', () => {
    render(<LexiconPractice />);
    const c2 = screen.getByRole('button', { name: /C2/ });
    expect(c2).toBeDisabled();
    expect(c2).toHaveTextContent('скоро');
  });

  test('flashcard rating keys are inert before reveal', async () => {
    const user = userEvent.setup();
    render(
      <LexiconPractice initialDeck={sampleDeckWithOnlyMode('knyha', 'flashcards')} autoStart initialMode="flashcards" />,
    );
    await user.keyboard('3');
    expect(storedState().reviews ?? []).toHaveLength(0);
    const flashcard = document.querySelector('[data-activity="flashcard"]')!;
    await user.click(flashcard);
    await user.keyboard('3');
    await waitFor(() => expect(storedState().reviews?.length).toBe(1));
  });

  test('post-flip rating buttons show FSRS interval previews', async () => {
    const user = userEvent.setup();
    const { container } = render(
      <LexiconPractice initialDeck={sampleDeckWithOnlyMode('knyha', 'flashcards')} autoStart initialMode="flashcards" />,
    );
    await user.click(container.querySelector('[data-activity="flashcard"]')!);
    const good = container.querySelector('[data-rate="good"] .ri');
    expect(good?.textContent).toMatch(/‹.+›/);
  });

  test('wrong answer dwells: feedback stays and it never auto-advances past 650ms', async () => {
    const user = userEvent.setup();
    // Default 650ms auto-advance window; a wrong answer must ignore it entirely.
    render(<LexiconPractice initialDeck={heritageDeck()} autoStart initialMode="heritage" />);

    await user.click(
      within(screen.getByTestId('practice-heritage')).getByRole('button', { name: /дом/ }),
    );

    // A wrong (calque) pick parks in a dwell state with an explicit advance control.
    expect(screen.getByTestId('practice-advance-button')).toBeInTheDocument();
    expect(screen.getByTestId('practice-heritage-feedback')).toHaveTextContent('калька');

    // Wait well past the 650ms correct-answer window — the item must still be here.
    await new Promise((resolve) => setTimeout(resolve, 750));
    expect(screen.getByTestId('practice-advance-button')).toBeInTheDocument();
    expect(screen.getByTestId('practice-heritage-feedback')).toHaveTextContent('калька');
  });

  test('wrong answer advances on «Далі» click and on Enter', async () => {
    const clickUser = userEvent.setup();
    const clicked = render(
      <LexiconPractice initialDeck={heritageDeck()} autoStart initialMode="heritage" advanceDelayMs={20} />,
    );
    await clickUser.click(
      within(screen.getByTestId('practice-heritage')).getByRole('button', { name: /дом/ }),
    );
    expect(screen.getByTestId('practice-advance-button')).toBeInTheDocument();
    await clickUser.click(screen.getByTestId('practice-advance-button'));
    await waitFor(() =>
      expect(screen.queryByTestId('practice-advance-button')).not.toBeInTheDocument(),
    );
    clicked.unmount();

    const enterUser = userEvent.setup();
    render(
      <LexiconPractice initialDeck={heritageDeck()} autoStart initialMode="heritage" advanceDelayMs={20} />,
    );
    await enterUser.click(
      within(screen.getByTestId('practice-heritage')).getByRole('button', { name: /дом/ }),
    );
    expect(screen.getByTestId('practice-advance-button')).toBeInTheDocument();
    await enterUser.keyboard('{Enter}');
    await waitFor(() =>
      expect(screen.queryByTestId('practice-advance-button')).not.toBeInTheDocument(),
    );
  });

  test('correct answer still auto-advances (never enters dwell)', async () => {
    const user = userEvent.setup();
    render(<LexiconPractice initialDeck={heritageDeck()} autoStart initialMode="heritage" advanceDelayMs={20} />);

    await user.click(
      within(screen.getByTestId('practice-heritage')).getByRole('button', { name: 'дім' }),
    );

    // Correct answers keep the snappy auto-advance: no dwell control ever appears.
    expect(screen.queryByTestId('practice-advance-button')).not.toBeInTheDocument();
    expect(screen.getByTestId('practice-heritage-feedback')).toHaveTextContent('Правильно');

    // The snappy timer fires and moves off the item on its own — no «Далі» needed.
    await waitFor(() =>
      expect(screen.queryByTestId('practice-heritage-feedback')).not.toBeInTheDocument(),
    );
  });

  test('heritage calque citation stays visible until «Далі»', async () => {
    const user = userEvent.setup();
    // Tiny auto-advance window — the cited correction must still outlast it.
    render(<LexiconPractice initialDeck={heritageDeck()} autoStart initialMode="heritage" advanceDelayMs={20} />);

    await user.click(
      within(screen.getByTestId('practice-heritage')).getByRole('button', { name: /дом/ }),
    );

    expect(screen.getByTestId('practice-heritage-feedback')).toHaveTextContent(
      'Джерело: Антоненко-Давидович: fixture',
    );

    // The cited §9.5 correction is the teaching moment — the 20ms timer must not erase it.
    await new Promise((resolve) => setTimeout(resolve, 200));
    expect(screen.getByTestId('practice-heritage-feedback')).toHaveTextContent(
      'Джерело: Антоненко-Давидович: fixture',
    );

    await user.click(screen.getByTestId('practice-advance-button'));
    await waitFor(() =>
      expect(screen.queryByTestId('practice-advance-button')).not.toBeInTheDocument(),
    );
  });

  test('cloze wrong chip dwells (no auto-advance past 650ms) and «Далі» resets to a clean item', async () => {
    seedRecognitionMastery('knyha');
    const user = userEvent.setup();
    // Default 650ms auto-advance window; a wrong chip pick must ignore it entirely.
    render(<LexiconPractice initialDeck={sampleDeck()} autoStart initialMode="cloze" />);

    expect(screen.getByTestId('practice-cloze')).toBeInTheDocument();

    // A wrong CHIP pick (a different lemma — not a case-miss, not correct) parks in a
    // dwell state with an explicit advance control instead of auto-advancing.
    await user.click(screen.getByRole('button', { name: 'робота' }));
    expect(screen.getByTestId('practice-advance-button')).toBeInTheDocument();
    expect(screen.getByText('✗ Не те слово')).toBeInTheDocument();

    // Wait well past the 650ms correct-answer window — the wrong chip must still dwell.
    await new Promise((resolve) => setTimeout(resolve, 750));
    expect(screen.getByTestId('practice-advance-button')).toBeInTheDocument();
    expect(screen.getByText('✗ Не те слово')).toBeInTheDocument();

    // «Далі» advances. The lapsed card re-surfaces with the SAME itemId (so the
    // selection-change effect does not re-fire) — it must still start clean: unlocked
    // chips, empty input, no stale wrong-word feedback.
    await user.click(screen.getByTestId('practice-advance-button'));
    await waitFor(() =>
      expect(screen.queryByTestId('practice-advance-button')).not.toBeInTheDocument(),
    );
    expect(screen.getByTestId('practice-cloze')).toBeInTheDocument();
    expect(screen.getByLabelText('Відповідь у знахідний')).toHaveValue('');
    expect(screen.getByRole('button', { name: 'книгу' })).not.toBeDisabled();
    expect(screen.queryByText('✗ Не те слово')).not.toBeInTheDocument();
  });

  test('weak-area chips: renders a UA case chip from a weak review log', async () => {
    // 24 accusative cloze reviews, 15 failed (0.63 miss) → a clear weak case.
    seedWeakCaseLog('accusative', 24, 15);
    render(<LexiconPractice initialDeck={sampleDeck()} />);

    await waitFor(() =>
      expect(screen.getByTestId('practice-weak-areas')).toBeInTheDocument(),
    );
    expect(screen.getByText('Ваші слабкі відмінки')).toBeInTheDocument();
    // Chips use Ukrainian case names only — знахідний for accusative.
    expect(screen.getByTestId('practice-weak-chip-accusative')).toHaveTextContent('знахідний');
  });

  test('weak-area chips: hidden below the minimum-data threshold', async () => {
    // Only 6 reviews — far below the threshold; no chips for a new learner.
    seedWeakCaseLog('accusative', 6, 6);
    render(<LexiconPractice initialDeck={sampleDeck()} />);

    await waitFor(() => expect(screen.getByTestId('practice-start-session')).toBeInTheDocument());
    expect(screen.queryByTestId('practice-weak-areas')).not.toBeInTheDocument();
  });

  test('weak-area chip tap starts a focus session filtered to that weakness', async () => {
    // The only cloze in sampleDeck() is knyha/accusative; seed an accusative weakness so
    // the tapped focus session's pool resolves to exactly that matching cloze item.
    seedWeakCaseLog('accusative', 24, 15);
    seedRecognitionMastery('knyha');
    const user = userEvent.setup();
    render(<LexiconPractice initialDeck={sampleDeck()} />);

    const chip = await screen.findByTestId('practice-weak-chip-accusative');
    await user.click(chip);

    // Focus session is active and serving the accusative cloze — no other case leaks in.
    const cloze = await screen.findByTestId('practice-cloze');
    expect(cloze).toBeInTheDocument();
    expect(screen.getByLabelText('Відповідь у знахідний')).toBeInTheDocument();
  });

  test('weak-area chip whose weakness yields no items shows a UA notice, clears focus, and never strands the learner', async () => {
    // The learner is weak on the GENITIVE, but sampleDeck() only carries an ACCUSATIVE
    // cloze — so the tapped focus pool resolves to zero items under the combined filter.
    // The learner must not be stranded in an itemless «active» session.
    seedWeakCaseLog('genitive', 24, 15);
    const user = userEvent.setup();
    render(<LexiconPractice initialDeck={sampleDeck()} />);

    const chip = await screen.findByTestId('practice-weak-chip-genitive');
    await user.click(chip);

    // A UA idle notice is surfaced instead of opening an empty session.
    expect(
      await screen.findByText('Немає вправ для цього фокуса — колода оновиться після практики'),
    ).toBeInTheDocument();

    // No session opened: the idle home (start button + the chip) is still here, and no
    // active cloze stage was rendered — the focus was cleared, not left active-but-empty.
    expect(screen.getByTestId('practice-start-session')).toBeInTheDocument();
    expect(screen.getByTestId('practice-weak-chip-genitive')).toBeInTheDocument();
    expect(screen.queryByTestId('practice-cloze')).not.toBeInTheDocument();

    // No resumable snapshot was written for the aborted focus attempt.
    expect(localStorage.getItem('lu-practice-session')).toBeNull();
  });

  test('focus weakness is session-transient: it is never persisted, so a resumed session drops it', async () => {
    // Tapping a chip starts a focus session AND writes a resume snapshot. The focus must
    // NOT be encoded in that snapshot, so resuming can never re-apply the weakness filter.
    seedWeakCaseLog('accusative', 24, 15);
    seedRecognitionMastery('knyha');
    const user = userEvent.setup();
    const first = render(<LexiconPractice initialDeck={sampleDeck()} />);

    await user.click(await screen.findByTestId('practice-weak-chip-accusative'));
    await screen.findByTestId('practice-cloze');

    // The persisted snapshot carries the mode but no focus weakness — transiency by design.
    const raw = localStorage.getItem('lu-practice-session');
    expect(raw).not.toBeNull();
    const snapshot = JSON.parse(raw as string);
    expect(snapshot.modeFilter).toBe('cloze');
    expect(snapshot).not.toHaveProperty('focusWeakness');
    expect(raw).not.toContain('focus');

    // Remount from the same storage: the resume path re-enters the session with focus
    // cleared (beginSession(..., focus=null)), so it starts a working session, not a
    // stranded focus-filtered one.
    first.unmount();
    render(<LexiconPractice initialDeck={sampleDeck()} />);
    await user.click(await screen.findByTestId('practice-resume-session'));
    expect(await screen.findByTestId('practice-cloze')).toBeInTheDocument();
  });

  test('double-Enter during dwell advances exactly once (no double completion)', async () => {
    const { fn } = mockShardFetch({});
    vi.spyOn(globalThis, 'fetch').mockImplementation(fn);
    const user = userEvent.setup();
    render(<LexiconPractice initialDeck={heritageDeck()} autoStart initialMode="heritage" advanceDelayMs={20} />);

    // Wrong (calque) pick parks in a dwell state with an explicit advance control.
    await user.click(
      within(screen.getByTestId('practice-heritage')).getByRole('button', { name: /дом/ }),
    );
    expect(screen.getByTestId('practice-advance-button')).toBeInTheDocument();

    // Fire TWO Enter keydowns within a single tick, before React re-renders — the real
    // double-advance race. Only the first may consume the parked outcome; the second must
    // no-op. A single completion increments the today counter by exactly one.
    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
      window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
    });

    await waitFor(() =>
      expect(screen.queryByTestId('practice-advance-button')).not.toBeInTheDocument(),
    );

    // Return home to read the today counter (only surfaced on the idle home ring).
    await user.click(screen.getByRole('button', { name: /Додому/ }));
    const ring = await screen.findByTestId('practice-today-ring');
    // Exactly one completion — a double-advance would have recorded two.
    expect(Number(ring.textContent?.split('/')[0])).toBe(1);
  });
});
