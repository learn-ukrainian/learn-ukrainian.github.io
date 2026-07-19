import { beforeEach, describe, expect, test, vi } from 'vitest';
import { State } from 'ts-fsrs';
import { act, render, screen, waitFor, within, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LexiconPractice, { addDailyExamples } from '@site/src/components/LexiconPractice';
import PracticeDailyDeck from '@site/src/components/PracticeDailyDeck';
import PracticeSessionSummary, { type SessionSummaryStats } from '@site/src/components/PracticeSessionSummary';
import PracticeErrorBoundary from '@site/src/components/PracticeErrorBoundary';
import {
  SRS_STORAGE_KEY,
  cardKey,
  loadState,
  saveState,
  type PracticeDeckData,
  type DailyPracticeDeckSnapshot,
  type DailyPracticeRowState,
  type PracticeHeritageItem,
  type PracticeParonymItem,
  type PracticeLexeme,
  type PracticeMode,
  type PracticeRating,
  type ReviewLogEntry,
} from '@site/src/lib/lexicon/srs';
import { LEARNER_LEVEL_STORAGE_KEY, type CefrLevel } from '@site/src/lib/lexicon/levels';

const NOW = new Date('2026-06-23T12:00:00.000Z');

function ThrowPracticeError(): never {
  throw new Error('practice render failed');
}

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
      /practice-(index|lexemes|cloze|stress|classify|paradigm|synonym|paronym|heritage)\.([ABC][12])\.json/,
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
      | 'paronym'
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

/** Progressive mock: selected level (highest) resolves immediately; lower levels return held promises
 * so tests can assert first item renders before lowers resolve, and growth after explicit release.
 */
function mockProgressiveFetch(counts: Partial<Record<CefrLevel, number>>) {
  const requested: string[] = [];
  const pending: Array<() => void> = [];
  const fn = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    requested.push(url);
    const match = url.match(
      /practice-(index|lexemes|cloze|stress|classify|paradigm|synonym|paronym|heritage)\.([ABC][12])\.json/,
    );
    if (!match) return notFoundResponse();
    const kind = match[1] as any;
    const level = match[2] as CefrLevel;
    const n = counts[level];
    if (n === undefined) return notFoundResponse();
    const isSelected = level === 'B1' || Object.keys(counts).filter((k) => counts[k as CefrLevel]! > 0).slice(-1)[0] === level; // simplistic: assume B1 target in tests
    const makeLex = (lvl: CefrLevel, cnt: number) =>
      Array.from({ length: cnt }, (_u, i) =>
        lexeme(
          `${lvl}-${i}`,
          `слово-${lvl}-${i}`,
          `gloss ${lvl} ${i}`,
          { nominative: `слово-${lvl}-${i}`, accusative: `слово-${lvl}-${i}`, locative: `слово-${lvl}-${i}` },
          { cefr: lvl },
        ),
      );
    const lexemes = makeLex(level, n);
    const bodyFor = () => {
      if (kind === 'index') {
        return {
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
        };
      }
      if (kind === 'lexemes') return { deckVersion: `v-${level}`, level, lexemes };
      return { [kind]: [] };
    };
    if (level === 'B1') {
      return okJson(bodyFor());
    }
    // lower held until released
    return new Promise<Response>((resolve) => {
      pending.push(() => resolve(okJson(bodyFor())));
    });
  });
  return {
    fn,
    requested,
    releaseLowers: () => {
      pending.forEach((r) => r());
      pending.length = 0;
    },
    pendingCount: () => pending.length,
  };
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

function storedState(): { reviews: ReviewLogEntry[]; cards: Record<string, any> } {
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

function smallMatchingDeck(): PracticeDeckData {
  const lexemes = [
    lexeme('knyha', 'книга', 'book', { nominative: 'книга', accusative: 'книгу', locative: 'книзі' }),
    lexeme('robota', 'робота', 'work', { nominative: 'робота', accusative: 'роботу', locative: 'роботі' }),
    lexeme('misto', 'місто', 'city', { nominative: 'місто', accusative: 'місто', locative: 'місті' }),
  ];
  return {
    deckVersion: 'test-matching-small',
    level: 'A1',
    lexemes,
    index: lexemes.map((entry, index) => ({
      lemmaId: entry.lemmaId,
      lemma: entry.lemma,
      cefr: 'A1',
      modes: ['matching'],
      hasCloze: false,
      clozeIds: [],
      newOrder: index,
    })),
    cloze: [],
  };
}

function stressDeck(): PracticeDeckData {
  const entry = lexeme('kava', 'кава', 'coffee', {
    nominative: 'кава',
    accusative: 'каву',
    locative: 'каві',
  });
  return {
    deckVersion: 'test-stress',
    level: 'A1',
    lexemes: [entry],
    index: [{
      lemmaId: entry.lemmaId,
      lemma: entry.lemma,
      cefr: 'A1',
      modes: ['stress'],
      hasCloze: false,
      clozeIds: [],
      newOrder: 0,
    }],
    cloze: [],
    stress: [{
      stressId: 'kava-stress',
      lemmaId: 'kava',
      lemma: 'кава',
      stressed: 'ка́ва',
      unstressed: 'кава',
      stressIndex: 1,
      nuclei: [
        { index: 1, label: 'а' },
        { index: 3, label: 'а' },
      ],
      source: 'fixture',
    }],
    classify: [],
    paradigm: [],
    synonym: [],
  };
}

function classifyDeck(): PracticeDeckData {
  const entry = lexeme('kava', 'кава', 'coffee', {
    nominative: 'кава',
    accusative: 'каву',
    locative: 'каві',
  });
  return {
    deckVersion: 'test-classify',
    level: 'A1',
    lexemes: [entry],
    index: [{
      lemmaId: entry.lemmaId,
      lemma: entry.lemma,
      cefr: 'A1',
      modes: ['classify'],
      hasCloze: false,
      clozeIds: [],
      newOrder: 0,
    }],
    cloze: [],
    stress: [],
    classify: [{
      classifyId: 'kava-classify',
      lemmaId: 'kava',
      lemma: 'кава',
      sets: [{
        setId: 'gender',
        setLabelUk: 'рід',
        answer: 'feminine',
        answerLabelUk: 'жіночий',
        options: [
          { value: 'feminine', labelUk: 'жіночий' },
          { value: 'masculine', labelUk: 'чоловічий' },
        ],
      }],
      source: 'fixture',
    }],
    paradigm: [],
    synonym: [],
  };
}

function paradigmDeck(): PracticeDeckData {
  const entry = lexeme('kava', 'кава', 'coffee', {
    nominative: 'кава',
    accusative: 'каву',
    locative: 'каві',
  });
  return {
    deckVersion: 'test-paradigm',
    level: 'A1',
    lexemes: [entry],
    index: [{
      lemmaId: entry.lemmaId,
      lemma: entry.lemma,
      cefr: 'A1',
      modes: ['paradigm'],
      hasCloze: false,
      clozeIds: [],
      newOrder: 0,
    }],
    cloze: [],
    stress: [],
    classify: [],
    paradigm: [{
      paradigmId: 'kava-paradigm',
      lemmaId: 'kava',
      lemma: 'кава',
      slot: {
        case: 'genitive',
        number: 'singular',
        labelUk: 'родовий відмінок однини',
      },
      form: 'кави',
      options: [
        { label: 'кави', kind: 'answer' },
        { label: 'кава', kind: 'same-paradigm' },
      ],
    }],
    synonym: [],
  };
}

function synonymDeck(): PracticeDeckData {
  const entry = lexeme('kava', 'кава', 'coffee', {
    nominative: 'кава',
    accusative: 'каву',
    locative: 'каві',
  });
  return {
    deckVersion: 'test-synonym',
    level: 'A1',
    lexemes: [entry],
    index: [{
      lemmaId: entry.lemmaId,
      lemma: entry.lemma,
      cefr: 'A1',
      modes: ['synonym'],
      hasCloze: false,
      clozeIds: [],
      newOrder: 0,
    }],
    cloze: [],
    stress: [],
    classify: [],
    paradigm: [],
    synonym: [{
      synonymId: 'kava-syn',
      lemmaId: 'kava',
      targetLemmaId: 'kava',
      polarity: 'synonym',
      prompt: 'кава',
      answer: 'кава',
      options: [
        { label: 'кава', lemmaId: 'kava', kind: 'answer' },
        { label: 'чай', lemmaId: 'chay', kind: 'distractor' },
      ],
      source: 'fixture',
    }],
  };
}

beforeEach(() => {
  localStorage.clear();
  loadState(localStorage, NOW);
  vi.restoreAllMocks();
  // Preserve prior A2+/uk-only chrome expectations unless a test opts into EN.
  document.documentElement.dataset.chromeLocale = 'uk';
});

describe('LexiconPractice', () => {
  test('keeps the K3 setup DOM order and Stress mode visible after switching to A2', async () => {
    const { fn } = mockShardFetch({ A1: 4, A2: 4 });
    vi.spyOn(globalThis, 'fetch').mockImplementation(fn);
    const user = userEvent.setup();
    const { container } = render(<LexiconPractice initialDeck={sampleDeck()} />);

    await screen.findByTestId('practice-daily-deck');
    const dashboard = container.querySelector('.k3-practice-dashboard')!;
    expect(
      Array.from(dashboard.children).map((child) => child.getAttribute('data-testid')),
    ).toEqual([
      'practice-dashboard-hero',
      'practice-dashboard-stats',
      'practice-dashboard-words',
      'practice-dashboard-session',
      'practice-dashboard-secondary',
    ]);

    await user.click(screen.getByRole('button', { name: 'A2' }));
    await waitFor(() => expect(screen.getByRole('button', { name: /Наголос/ })).toBeInTheDocument());
    expect(dashboard.querySelectorAll('[data-mode]').length).toBe(11);
  });

  test('renders stress marks and daily examples only on A1 default surfaces', () => {
    const marked = lexeme('mama', 'ма́ма', 'mother', {
      nominative: 'ма́ма',
      accusative: 'ма́му',
      locative: 'ма́мі',
    }, { example: 'Мама читає.', exampleEn: 'Mother is reading.' });
    const snapshot: DailyPracticeDeckSnapshot = {
      version: 1,
      date: '2026-06-23',
      level: 'A1',
      deckVersion: 'test-daily-display',
      createdAt: NOW.getTime(),
      items: [{ lemmaId: marked.lemmaId, origin: 'due' }],
    };
    const rows: { pendingDue: DailyPracticeRowState[]; pendingNew: DailyPracticeRowState[]; done: DailyPracticeRowState[] } = {
      pendingDue: [{ item: snapshot.items[0]!, state: 'due', lastSeenAt: NOW.getTime() }],
      pendingNew: [],
      done: [],
    };
    const props = {
      snapshot,
      rows,
      lexemes: new Map([[marked.lemmaId, marked]]),
      atlasLemmaHref: (lemmaId: string) => `/lexicon/${lemmaId}/`,
      chromeLocale: 'uk' as const,
    };
    const { rerender } = render(<PracticeDailyDeck {...props} learnerLevel="A1" />);

    expect(screen.getAllByText('ма́ма').length).toBeGreaterThan(0);
    expect(screen.getByTestId('practice-daily-example')).toHaveTextContent('Мама читає.');
    expect(screen.getByTestId('practice-daily-example-en')).toHaveTextContent('Mother is reading.');
    expect(screen.getByTestId('practice-daily-why-mama')).toHaveTextContent('До повторення');

    rerender(<PracticeDailyDeck {...props} learnerLevel="A2" />);

    expect(screen.queryByText('ма́ма')).not.toBeInTheDocument();
    expect(screen.getAllByText('мама').length).toBeGreaterThan(0);
    expect(screen.queryByTestId('practice-daily-example-en')).not.toBeInTheDocument();
  });

  test('uses a lemma-matched cloze sentence only when a lexeme example is absent', () => {
    const deck = sampleDeck();
    const explicit = { ...deck.lexemes[1]!, example: 'Verified shipped example.' };
    const clozeOnly = { ...deck.lexemes[0]! };
    const enriched = addDailyExamples(
      new Map([
        [explicit.lemmaId, explicit],
        [clozeOnly.lemmaId, clozeOnly],
      ]),
      deck.cloze,
    );

    expect(enriched.get(explicit.lemmaId)?.example).toBe('Verified shipped example.');
    expect(enriched.get(clozeOnly.lemmaId)?.example).toBe('Я читаю книгу.');
    expect(enriched.get(clozeOnly.lemmaId)?.exampleEn).toBe('I am reading a book.');
  });

  test('practice render fallback dual-renders pure locale chrome (ChromeText/ChromeDual)', () => {
    vi.spyOn(console, 'error').mockImplementation(() => undefined);

    render(
      <PracticeErrorBoundary>
        <ThrowPracticeError />
      </PracticeErrorBoundary>,
    );

    const fallback = screen.getByTestId('practice-error-fallback');
    // Both locales in DOM; CSS on data-chrome-locale shows exactly one (#5503).
    expect(fallback).toHaveTextContent('Не вдалося завантажити практику. Спробуйте оновити сторінку.');
    expect(fallback).toHaveTextContent('We couldn’t load practice. Try reloading the page.');
    const retry = screen.getByRole('button', { name: /Try again|Спробувати ще раз/ });
    expect(retry).toBeInTheDocument();
    // No slash-dual button chrome.
    expect(retry.textContent ?? '').not.toMatch(/\/\s*Try again|\/\s*Спробувати/);
  });

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
      expect(screen.getByTestId('practice-session-scope')).toHaveTextContent(
        /1 до повторення/,
      ),
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

      />,
    );

    expect(screen.getByTestId('practice-heritage')).toBeInTheDocument();
    expect(screen.getByText('Оберіть питоме українське слово.')).toBeInTheDocument();
    expect(screen.getByText(/Я бачу/)).toBeInTheDocument();

    mixedRender.unmount();
    const { container } = render(<LexiconPractice initialDeck={heritageDeck()} />);
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

  test('heritage mode card is present in the K3 grid even when the deck has no heritage items', () => {
    render(<LexiconPractice initialDeck={heritageDeck({ includeItems: false })} />);

    expect(screen.getByRole('button', { name: /Спадщина/ })).toBeInTheDocument();
  });

  test('heritage feedback renders rationaleUk when present and OMITS the detail line when absent', async () => {
    localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, 'B1');
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

      />,
    );

    await user.click(
      within(screen.getByTestId('practice-heritage')).getByRole('button', { name: /дом/ }),
    );

    const feedbackTextWithout = screen.getByTestId('practice-heritage-feedback').textContent;
    expect(feedbackTextWithout).toContain('⚠️ калька');
    expect(feedbackTextWithout).toContain('Відкрити в Атласі →');
    expect(feedbackTextWithout).not.toContain('english explanation');
  });

  test('«Відкрити в Атласі →» link present in heritage feedback with correct href', async () => {
    const user = userEvent.setup();
    render(
      <LexiconPractice
        initialDeck={heritageDeck()}
        autoStart
        initialMode="heritage"

      />,
    );

    await user.click(
      within(screen.getByTestId('practice-heritage')).getByRole('button', { name: /дом/ }),
    );

    const link = screen.getByRole('link', { name: /Відкрити в Атласі/ });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/lexicon/dim/');
  });

  function paronymPracticeItem(): PracticeParonymItem {
    return {
      paronymId: 'par-test-fixture',
      lemmaId: 'bihate',
      srsKey: cardKey('bihate', 'paronym'),
      lemma: 'бігати',
      confusable: 'біжить',
      distinction_gloss_uk: 'бігати регулярно, бігти конкретно зараз',
      frameIndex: 1,
      cefr: 'A1',
      prompt: 'Вранці він ___ у парку.',
      answer: 'бігає',
      options: [
        { label: 'бігає' },
        { label: 'біжить' },
      ],
    };
  }

  function paronymDeck({ includeItems = true } = {}): PracticeDeckData {
    const entry = lexeme(
      'bihate',
      'бігати',
      'to run',
      {
        nominative: 'бігати',
        accusative: 'бігати',
        locative: 'бігати',
      },
      { cefr: 'A1' },
    );
    return {
      deckVersion: 'test-paronym',
      level: 'A1',
      lexemes: [entry],
      index: [
        {
          lemmaId: entry.lemmaId,
          lemma: entry.lemma,
          cefr: 'A1',
          modes: ['paronym'],
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
      paronym: includeItems ? [paronymPracticeItem()] : [],
    };
  }

  test('paronym renders in mixed sessions and paronym focus mode', async () => {
    const user = userEvent.setup();
    const mixedRender = render(
      <LexiconPractice
        initialDeck={paronymDeck()}
        autoStart
        initialMode="mixed"

      />,
    );

    expect(screen.getByTestId('practice-paronym')).toBeInTheDocument();
    expect(screen.getByText('Оберіть правильний паронім.')).toBeInTheDocument();
    expect(screen.getByText(/Вранці він/)).toBeInTheDocument();

    mixedRender.unmount();
    const { container } = render(<LexiconPractice initialDeck={paronymDeck()} />);
    expect(screen.getByText('Пароніми')).toBeInTheDocument();

    await user.click(container.querySelector<HTMLButtonElement>('[data-mode="paronym"]')!);

    expect(await screen.findByTestId('practice-paronym')).toBeInTheDocument();
  });

  test('paronym wrong choice scores again and shows explanation', async () => {
    const user = userEvent.setup();
    render(
      <LexiconPractice
        initialDeck={paronymDeck()}
        autoStart
        initialMode="paronym"

      />,
    );

    await user.click(
      within(screen.getByTestId('practice-paronym')).getByRole('button', { name: /біжить/ }),
    );

    const feedback = screen.getByTestId('practice-paronym-feedback');
    expect(feedback).toHaveTextContent('Неправильно. бігати регулярно, бігти конкретно зараз');
    await waitFor(() => {
      expect(storedState().reviews[0]).toMatchObject({
        lemmaId: 'bihate',
        mode: 'paronym',
        rating: 'again',
        cardKey: cardKey('bihate', 'paronym'),
      });
    });
  });

  test('paronym correct answer scores good', async () => {
    const user = userEvent.setup();
    render(
      <LexiconPractice
        initialDeck={paronymDeck()}
        autoStart
        initialMode="paronym"

      />,
    );

    await user.click(
      within(screen.getByTestId('practice-paronym')).getByRole('button', { name: /бігає/ }),
    );

    expect(screen.getByTestId('practice-paronym-feedback')).toHaveTextContent('Правильно! бігати регулярно, бігти конкретно зараз');
    await waitFor(() => {
      expect(storedState().reviews[0]).toMatchObject({
        lemmaId: 'bihate',
        mode: 'paronym',
        rating: 'good',
        cardKey: cardKey('bihate', 'paronym'),
      });
    });
  });

  test('paronym mode card is present in the K3 grid even when the deck has no paronym items', () => {
    render(<LexiconPractice initialDeck={paronymDeck({ includeItems: false })} />);

    expect(screen.getByRole('button', { name: /Пароніми/ })).toBeInTheDocument();
  });

  test('focus deep-link: a bare Atlas lemma resolves to its item with no double session start', async () => {
    const originalSearch = window.location.search;
    delete (window as any).location;
    window.location = new URL('http://localhost/lexicon/practice/?lemmaId=%D0%B4%D1%96%D0%BC') as any;

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
      expect(startedSnapshot.byMode.mixed.modeFilter).toBe('mixed');
      expect(startedSnapshot.byMode.mixed.budget).toBe(10);
    } finally {
      window.location = new URL('http://localhost/') as any;
      vi.restoreAllMocks();
    }
  });

  test('bare in-pool Atlas lemma opens that lemma’s practice', async () => {
    const originalSearch = window.location.search;
    delete (window as any).location;
    window.location = new URL('http://localhost/words-of-the-day/practice/?lemmaId=%D0%BA%D0%B0%D1%84%D0%B5') as any;

    try {
      const cafe = lexeme('kafe', 'кафе', 'cafe', {
        nominative: 'кафе',
        accusative: 'кафе',
        locative: 'кафе',
      });
      const book = lexeme('knyha', 'книга', 'book', {
        nominative: 'книга',
        accusative: 'книгу',
        locative: 'книзі',
      });
      const deck: PracticeDeckData = {
        deckVersion: 'test-atlas-lemma',
        level: 'A1',
        lexemes: [cafe, book],
        index: [cafe, book].map((entry, newOrder) => ({
          lemmaId: entry.lemmaId,
          lemma: entry.lemma,
          cefr: 'A1',
          modes: ['flashcards'],
          hasCloze: false,
          clozeIds: [],
          newOrder,
        })),
        cloze: [],
      };

      render(<LexiconPractice initialDeck={deck} autoStart={false} />);

      expect(
        await screen.findByRole('button', { name: /кафе.*натисніть, щоб перевернути/i }),
      ).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /книга.*натисніть, щоб перевернути/i })).not.toBeInTheDocument();
      expect(screen.queryByTestId('practice-fetch-error')).not.toBeInTheDocument();
    } finally {
      window.location = new URL(originalSearch ? `http://localhost${originalSearch}` : 'http://localhost/') as any;
    }
  });

  test('focused deep link clears a transient deck-load error after its retry renders the exercise', async () => {
    const originalSearch = window.location.search;
    delete (window as any).location;
    window.location = new URL('http://localhost/words-of-the-day/practice/?lemmaId=%D0%BA%D0%B0%D1%84%D0%B5') as any;

    try {
      const cafe = lexeme('kafe', 'кафе', 'cafe', {
        nominative: 'кафе',
        accusative: 'кафе',
        locative: 'кафе',
      });
      let failFirstLexemeRequest = true;
      const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        const match = url.match(
          /practice-(index|lexemes|cloze|stress|classify|paradigm|synonym|heritage)\.([ABC][12])\.json/,
        );
        if (!match || match[2] !== 'A1') return notFoundResponse();
        const kind = match[1];
        if (kind === 'index') {
          return okJson({
            deckVersion: 'v-A1',
            level: 'A1',
            items: [{
              lemmaId: cafe.lemmaId,
              lemma: cafe.lemma,
              cefr: 'A1',
              modes: ['flashcards'],
              hasCloze: false,
              clozeIds: [],
              newOrder: 0,
            }],
          });
        }
        if (kind === 'lexemes') {
          if (failFirstLexemeRequest) {
            failFirstLexemeRequest = false;
            throw new Error('transient lexeme failure');
          }
          return okJson({ deckVersion: 'v-A1', level: 'A1', lexemes: [cafe] });
        }
        return okJson({ [kind]: [] });
      });
      vi.spyOn(globalThis, 'fetch').mockImplementation(fetchMock);

      render(<LexiconPractice autoStart={false} />);

      expect(
        await screen.findByRole('button', { name: /кафе.*натисніть, щоб перевернути/i }),
      ).toBeInTheDocument();
      expect(screen.queryByTestId('practice-fetch-error')).not.toBeInTheDocument();
      expect(
        fetchMock.mock.calls.filter(([url]) => String(url).includes('practice-lexemes.A1.json')),
      ).toHaveLength(2);
    } finally {
      window.location = new URL(originalSearch ? `http://localhost${originalSearch}` : 'http://localhost/') as any;
      vi.restoreAllMocks();
    }
  });

  test('bare Atlas lemma outside the initial deck resolves from cumulative shards', async () => {
    const originalSearch = window.location.search;
    delete (window as any).location;
    window.location = new URL('http://localhost/words-of-the-day/practice/?lemmaId=%D0%BA%D0%B0%D1%84%D0%B5') as any;
    localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, 'B1');

    try {
      const cafe = lexeme('kafe', 'кафе', 'cafe', {
        nominative: 'кафе',
        accusative: 'кафе',
        locative: 'кафе',
      });
      const requested: string[] = [];
      const fn = vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        requested.push(url);
        const match = url.match(
          /practice-(index|lexemes|cloze|stress|classify|paradigm|synonym|heritage)\.([ABC][12])\.json/,
        );
        if (!match) return notFoundResponse();
        const kind = match[1];
        const level = match[2] as CefrLevel;
        if (kind === 'index') {
          return okJson({
            deckVersion: `v-${level}`,
            level,
            items: level === 'A1'
              ? [{ lemmaId: cafe.lemmaId, lemma: cafe.lemma, cefr: 'A1', modes: ['flashcards'], hasCloze: false, clozeIds: [], newOrder: 0 }]
              : [],
          });
        }
        if (kind === 'lexemes') {
          return okJson({ deckVersion: `v-${level}`, level, lexemes: level === 'A1' ? [cafe] : [] });
        }
        return okJson({ [kind]: [] });
      });
      vi.spyOn(globalThis, 'fetch').mockImplementation(fn);

      render(<LexiconPractice initialDeck={sampleDeck()} autoStart={false} />);

      expect(
        await screen.findByRole('button', { name: /кафе.*натисніть, щоб перевернути/i }),
      ).toBeInTheDocument();
      expect(screen.queryByTestId('practice-lemma-missing')).not.toBeInTheDocument();
      expect(screen.queryByTestId('practice-fetch-error')).not.toBeInTheDocument();
      expect(requested.filter((url) => url.includes('practice-index.A1.json'))).toHaveLength(1);
      expect(requested.filter((url) => url.includes('practice-lexemes.A1.json'))).toHaveLength(1);
    } finally {
      window.location = new URL(originalSearch ? `http://localhost${originalSearch}` : 'http://localhost/') as any;
      vi.restoreAllMocks();
    }
  });

  test('out-of-pool Atlas lemma keeps the hub usable without retrying its lookup', async () => {
    const originalSearch = window.location.search;
    delete (window as any).location;
    window.location = new URL('http://localhost/words-of-the-day/practice/?lemmaId=%D0%BF%D0%BE%D0%B7%D0%B0%D0%BF%D1%83%D0%BB%D0%BE%D0%BC') as any;

    try {
      const user = userEvent.setup();
      const { fn, requested } = mockShardFetch({ A1: 2 });
      vi.spyOn(globalThis, 'fetch').mockImplementation(fn);

      render(<LexiconPractice />);

      const notice = await screen.findByTestId('practice-lemma-missing');
      expect(notice).toHaveTextContent('Це слово ще не в тренажері.');
      expect(notice).toHaveTextContent('This word is not in the practice pool yet.');
      expect(screen.queryByTestId('practice-fetch-error')).not.toBeInTheDocument();
      await user.click(screen.getByTestId('practice-start-session'));
      expect(await screen.findByTestId('practice-session-progress')).toHaveTextContent('0/6');
      expect(screen.queryByTestId('practice-fetch-error')).not.toBeInTheDocument();
      expect(requested.filter((url) => url.includes('practice-index.A1.json'))).toHaveLength(1);
      expect(requested.filter((url) => url.includes('practice-lexemes.A1.json'))).toHaveLength(1);
    } finally {
      window.location = new URL(originalSearch ? `http://localhost${originalSearch}` : 'http://localhost/') as any;
      vi.restoreAllMocks();
    }
  });

  test('a real deep-link fetch failure renders pure dual-locale practice fallback', async () => {
    const originalSearch = window.location.search;
    delete (window as any).location;
    window.location = new URL('http://localhost/words-of-the-day/practice/?lemmaId=%D0%BA%D0%B0%D1%84%D0%B5') as any;

    try {
      vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('network offline'));

      render(<LexiconPractice />);

      const fallback = await screen.findByTestId('practice-fetch-error');
      // ChromeDual/ChromeText put both locales in DOM; CSS shows one (#5503).
      expect(fallback).toHaveTextContent('Не вдалося завантажити практику.');
      expect(fallback).toHaveTextContent('We couldn’t load practice.');
      const retry = screen.getByRole('button', { name: /Try again|Спробувати ще раз/ });
      expect(retry).toBeInTheDocument();
      expect(retry.textContent ?? '').not.toMatch(/\/\s*Try again|\/\s*Спробувати/);
    } finally {
      window.location = new URL(originalSearch ? `http://localhost${originalSearch}` : 'http://localhost/') as any;
      vi.restoreAllMocks();
    }
  });

  test('cloze wrong-case answer records one case miss and leaves blank open', async () => {
    seedRecognitionMastery('knyha');
    const user = userEvent.setup();
    render(<LexiconPractice initialDeck={sampleDeck()} autoStart initialMode="cloze" />);

    expect(screen.getByTestId('practice-cloze')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'книга' }));
    await user.click(screen.getByRole('button', { name: /Перевірити/ }));

    const status = within(screen.getByTestId('practice-cloze')).getByRole('status');
    expect(status).toHaveTextContent('Правильне слово');
    expect(status).toHaveClass('case-miss');
    expect(screen.getByLabelText(/Відповідь у знахідному відмінку/)).toHaveValue('');
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

  test('today scope uses review + capped-new denominator, not whole deck', async () => {
    const { fn } = mockShardFetch({ A1: 1150 });
    vi.spyOn(globalThis, 'fetch').mockImplementation(fn);
    render(<LexiconPractice />);
    await waitFor(() =>
      expect(screen.getByTestId('practice-session-scope')).toBeInTheDocument(),
    );
    const scope = screen.getByTestId('practice-session-scope');
    const match = scope.textContent?.match(/0 до повторення \+ (\d+) нових/);
    expect(match).toBeTruthy();
    const denominator = Number(match?.[1]);
    expect(denominator).toBeLessThan(1150);
  });

  test("A1 and A2 chrome aria-labels follow pure data-chrome-locale (no slash-dual)", async () => {
    document.documentElement.dataset.chromeLocale = "uk";
    localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, "A1");
    const { unmount } = render(<LexiconPractice />);
    // #5503: A1 chrome is pure UK when locale is uk — English only in item content.
    expect(screen.getByRole("region")).toHaveAttribute(
      "aria-label",
      "Практика слів дня",
    );
    unmount();

    localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, "A2");
    const { unmount: unmountA2 } = render(<LexiconPractice />);
    expect(screen.getByRole("region")).toHaveAttribute(
      "aria-label",
      "Практика слів дня",
    );
    unmountA2();

    document.documentElement.dataset.chromeLocale = "en";
    localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, "A1");
    render(<LexiconPractice />);
    expect(screen.getByRole("region")).toHaveAttribute(
      "aria-label",
      "Words of the Day Practice",
    );
  });

  test("A2 shows English chrome when data-chrome-locale is en", async () => {
    document.documentElement.dataset.chromeLocale = "en";
    localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, "A2");
    render(<LexiconPractice />);
    expect(screen.getByText("Start session")).toBeInTheDocument();
  });

  test("toggling data-chrome-locale updates practice chrome without remount", async () => {
    document.documentElement.dataset.chromeLocale = "uk";
    localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, "B1");
    render(<LexiconPractice />);
    expect(screen.getByText(/Чергуйте картки/)).toBeInTheDocument();

    await act(async () => {
      document.documentElement.dataset.chromeLocale = "en";
    });
    await waitFor(() => {
      expect(
        screen.getByText(/Rotate flashcards, matching, choice/),
      ).toBeInTheDocument();
    });
  });

  test("heritage empty state is dual-language when chrome locale is en", async () => {
    document.documentElement.dataset.chromeLocale = "en";
    localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, "A2");
    render(
      <LexiconPractice
        initialDeck={heritageDeck({ includeItems: false })}
        autoStart
        initialMode="heritage"
      />,
    );
    expect(await screen.findByTestId("practice-heritage-empty")).toHaveTextContent(
      /Heritage exercises for this level are still being prepared/,
    );
  });

  test("synonyms empty catch-all is dual-language when chrome locale is en", async () => {
    document.documentElement.dataset.chromeLocale = "en";
    localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, "A2");
    const deck = sampleDeckWithOnlyMode("knyha", "synonym");
    deck.synonym = [];
    render(<LexiconPractice initialDeck={deck} autoStart initialMode="synonym" />);
    await waitFor(() => {
      expect(screen.getByText(/All cards are reviewed for now/)).toBeInTheDocument();
    });
  });

  test("cloze placeholder is pure EN when chrome locale is en", async () => {
    document.documentElement.dataset.chromeLocale = "en";
    localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, "A2");
    const clozeDeck = sampleDeck();
    render(<LexiconPractice initialDeck={clozeDeck} autoStart initialMode="cloze" />);
    const input = await screen.findByRole("textbox");
    expect(input.getAttribute("placeholder")).toBe("type the word");
  });

  test("cloze placeholder is pure UK when chrome locale is uk (including A1)", async () => {
    document.documentElement.dataset.chromeLocale = "uk";
    localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, "A1");
    const clozeDeck = sampleDeck();
    render(<LexiconPractice initialDeck={clozeDeck} autoStart initialMode="cloze" />);
    const input = await screen.findByRole("textbox");
    expect(input.getAttribute("placeholder")).toBe("введіть слово");
  });

  test("atlas links announce new tab for screen readers in EN chrome", async () => {
    document.documentElement.dataset.chromeLocale = "en";
    const user = userEvent.setup();
    render(<LexiconPractice initialDeck={heritageDeck()} autoStart initialMode="heritage" />);
    await user.click(
      within(screen.getByTestId("practice-heritage")).getByRole("button", { name: /дом/ }),
    );
    // Full-switch chrome: EN locale uses English aria-label (owner #5355).
    const link = await screen.findByRole("link", { name: /new tab/i });
    expect(link).toHaveAttribute("target", "_blank");
  });

  test("atlas links announce нова вкладка for screen readers in UK chrome", async () => {
    document.documentElement.dataset.chromeLocale = "uk";
    const user = userEvent.setup();
    render(<LexiconPractice initialDeck={heritageDeck()} autoStart initialMode="heritage" />);
    await user.click(
      within(screen.getByTestId("practice-heritage")).getByRole("button", { name: /дом/ }),
    );
    const link = await screen.findByRole("link", { name: /нова вкладка/i });
    expect(link).toHaveAttribute("target", "_blank");
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

  test('wrong answer dwells: feedback stays and never auto-advances', async () => {
    const user = userEvent.setup();
    render(<LexiconPractice initialDeck={heritageDeck()} autoStart initialMode="heritage" />);

    await user.click(
      within(screen.getByTestId('practice-heritage')).getByRole('button', { name: /дом/ }),
    );

    // A wrong (calque) pick parks in a dwell state with an explicit advance control.
    expect(screen.getByTestId('practice-advance-button')).toBeInTheDocument();
    expect(screen.getByTestId('practice-heritage-feedback')).toHaveTextContent('калька');

    // Wait — the item must still be here with no timer-driven advance.
    await new Promise((resolve) => setTimeout(resolve, 750));
    expect(screen.getByTestId('practice-advance-button')).toBeInTheDocument();
    expect(screen.getByTestId('practice-heritage-feedback')).toHaveTextContent('калька');
  });

  test('wrong answer advances on «Далі» click and on Enter', async () => {
    const clickUser = userEvent.setup();
    const clicked = render(
      <LexiconPractice initialDeck={heritageDeck()} autoStart initialMode="heritage" />,
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
      <LexiconPractice initialDeck={heritageDeck()} autoStart initialMode="heritage" />,
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

  test('correct answer never auto-advances: next card waits for «Далі»', async () => {
    const user = userEvent.setup();
    render(<LexiconPractice initialDeck={heritageDeck()} autoStart initialMode="heritage" />);

    await user.click(
      within(screen.getByTestId('practice-heritage')).getByRole('button', { name: 'дім' }),
    );

    // Correct answers dwell identically to wrong ones — «Далі →» is required.
    expect(screen.getByTestId('practice-advance-button')).toBeInTheDocument();
    expect(screen.getByTestId('practice-heritage-feedback')).toHaveTextContent('Правильно');
    expect(document.activeElement).toBe(screen.getByTestId('practice-advance-button'));

    // Still on the same card after a dwell window — no timer advance.
    await new Promise((resolve) => setTimeout(resolve, 750));
    expect(screen.getByTestId('practice-heritage-feedback')).toHaveTextContent('Правильно');
    expect(screen.getByTestId('practice-advance-button')).toBeInTheDocument();

    await user.click(screen.getByTestId('practice-advance-button'));
    await waitFor(() =>
      expect(screen.queryByTestId('practice-heritage-feedback')).not.toBeInTheDocument(),
    );
  });

  test('heritage calque citation stays visible until «Далі»', async () => {
    const user = userEvent.setup();
    render(<LexiconPractice initialDeck={heritageDeck()} autoStart initialMode="heritage" />);

    await user.click(
      within(screen.getByTestId('practice-heritage')).getByRole('button', { name: /дом/ }),
    );

    expect(screen.getByTestId('practice-heritage-feedback')).toHaveTextContent(
      'Джерело: Антоненко-Давидович: fixture',
    );

    await new Promise((resolve) => setTimeout(resolve, 200));
    expect(screen.getByTestId('practice-heritage-feedback')).toHaveTextContent(
      'Джерело: Антоненко-Давидович: fixture',
    );

    await user.click(screen.getByTestId('practice-advance-button'));
    await waitFor(() =>
      expect(screen.queryByTestId('practice-advance-button')).not.toBeInTheDocument(),
    );
  });

  test('cloze wrong chip dwells (no auto-advance) and «Далі» resets to a clean item', async () => {
    seedRecognitionMastery('knyha');
    const user = userEvent.setup();
    render(<LexiconPractice initialDeck={sampleDeck()} autoStart initialMode="cloze" />);

    expect(screen.getByTestId('practice-cloze')).toBeInTheDocument();

    // A wrong CHIP pick (a different lemma — not a case-miss, not correct) populates
    // the input; only Check commits it and parks in a dwell state with an explicit
    // advance control instead of auto-advancing.
    await user.click(screen.getByRole('button', { name: 'робота' }));
    await user.click(screen.getByRole('button', { name: /Перевірити/ }));
    expect(screen.getByTestId('practice-advance-button')).toBeInTheDocument();
    expect(screen.getByText('✗ Не те слово')).toBeInTheDocument();

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
    expect(screen.getByLabelText(/Відповідь у знахідному відмінку/)).toHaveValue('');
    expect(screen.getByRole('button', { name: 'книгу' })).not.toBeDisabled();
    expect(screen.queryByText('✗ Не те слово')).not.toBeInTheDocument();
  });

  test('cloze correct answer also requires «Далі» before the next card', async () => {
    seedRecognitionMastery('knyha');
    const user = userEvent.setup();
    render(<LexiconPractice initialDeck={sampleDeck()} autoStart initialMode="cloze" />);

    await user.click(screen.getByRole('button', { name: 'книгу' }));
    await user.click(screen.getByRole('button', { name: /Перевірити/ }));
    expect(screen.getByTestId('practice-advance-button')).toBeInTheDocument();
    expect(within(screen.getByTestId('practice-cloze')).getByRole('status')).toHaveTextContent('книгу');

    await new Promise((resolve) => setTimeout(resolve, 750));
    expect(screen.getByTestId('practice-cloze')).toBeInTheDocument();
    expect(screen.getByTestId('practice-advance-button')).toBeInTheDocument();

    await user.click(screen.getByTestId('practice-advance-button'));
    await waitFor(() =>
      expect(screen.queryByTestId('practice-advance-button')).not.toBeInTheDocument(),
    );
  });

  test('session-size buttons expose aria-pressed and active class for the selection', async () => {
    const user = userEvent.setup();
    render(<LexiconPractice initialDeck={sampleDeck()} />);

    const twenty = screen.getByTestId('practice-session-budget-20');
    const ten = screen.getByTestId('practice-session-budget-10');
    expect(twenty).toHaveAttribute('aria-pressed', 'true');
    expect(twenty).toHaveClass('active');
    expect(ten).toHaveAttribute('aria-pressed', 'false');
    expect(ten).not.toHaveClass('active');

    await user.click(ten);
    expect(ten).toHaveAttribute('aria-pressed', 'true');
    expect(ten).toHaveClass('active');
    expect(twenty).toHaveAttribute('aria-pressed', 'false');
    expect(twenty).not.toHaveClass('active');
  });

  test('paradigm form question renders prompt + descriptor on one line', () => {
    const entry = lexeme('semantyka', 'семантика', 'semantics', {
      nominative: 'семантика',
      accusative: 'семантику',
      locative: 'семантиці',
    });
    const deck: PracticeDeckData = {
      deckVersion: 'test-paradigm-oneline',
      level: 'A1',
      lexemes: [entry],
      index: [
        {
          lemmaId: entry.lemmaId,
          lemma: entry.lemma,
          cefr: 'A1',
          modes: ['paradigm'],
          hasCloze: false,
          clozeIds: [],
          newOrder: 0,
        },
      ],
      cloze: [],
      paradigm: [
        {
          paradigmId: 'semantyka:paradigm:1',
          lemmaId: 'semantyka',
          lemma: 'семантика',
          slot: {
            case: 'орудний',
            number: 'singular',
            labelUk: 'орудний відмінок, однина',
            labelEn: 'instrumental case, singular',
          },
          form: 'семантикою',
          options: [
            { label: 'семантикою', kind: 'answer' },
            { label: 'семантика', kind: 'same-paradigm' },
            { label: 'семантиці', kind: 'same-paradigm' },
            { label: 'семантику', kind: 'same-paradigm' },
          ],
        },
      ],
    };

    render(<LexiconPractice initialDeck={deck} autoStart initialMode="paradigm" />);
    const prompt = screen.getByTestId('practice-form-prompt');
    expect(prompt).toHaveTextContent('Яка форма від «семантика»?');
    expect(prompt).toHaveTextContent('— орудний відмінок, однина');
    // One text-flow node — not a stacked mc-q + mc-sub pair.
    expect(prompt.querySelectorAll('p')).toHaveLength(0);
    expect(screen.queryByText('орудний відмінок, однина', { selector: '.mc-sub' })).not.toBeInTheDocument();
    expect(prompt).toMatchSnapshot();
  });

  test('weak-area chips: renders a UA case chip from a weak review log', async () => {
    // 24 accusative cloze reviews, 15 failed (0.63 miss) → a clear weak case.
    seedWeakCaseLog('accusative', 24, 15);
    render(<LexiconPractice initialDeck={sampleDeck()} />);

    await waitFor(() =>
      expect(screen.getByTestId('practice-weak-areas')).toBeInTheDocument(),
    );
    expect(screen.getByText('Фокус')).toBeInTheDocument();
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
    expect(screen.getByLabelText(/Відповідь у знахідному відмінку/)).toBeInTheDocument();
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

    // The mode-indexed snapshot carries the mode but no focus weakness — transiency by design.
    const raw = localStorage.getItem('lu-practice-session');
    expect(raw).not.toBeNull();
    const snapshot = JSON.parse(raw as string).byMode.cloze;
    expect(snapshot.modeFilter).toBe('cloze');
    expect(snapshot).not.toHaveProperty('focusWeakness');
    expect(raw).not.toContain('focus');

    // A fresh cloze session (via the mode card, since K3 only surfaces mixed resume)
    // starts with focus cleared, not a stranded focus-filtered one.
    first.unmount();
    const { container } = render(<LexiconPractice initialDeck={sampleDeck()} />);
    await user.click(container.querySelector<HTMLButtonElement>('[data-mode="cloze"]')!);
    expect(await screen.findByTestId('practice-cloze')).toBeInTheDocument();
  });

  test('switching modes starts a fresh selected session and preserves only its own continuation', async () => {
    const deck = sampleDeck();
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('practice-index.A1.json')) {
        return okJson({ deckVersion: deck.deckVersion, level: deck.level, items: deck.index });
      }
      if (url.includes('practice-lexemes.A1.json')) {
        return okJson({ deckVersion: deck.deckVersion, level: deck.level, lexemes: deck.lexemes });
      }
      return notFoundResponse();
    });
    const user = userEvent.setup();
    const { container } = render(<LexiconPractice initialDeck={deck} />);

    // Leave a matching session unfinished, then return to the hub exactly as a learner does.
    await user.click(container.querySelector<HTMLButtonElement>('[data-mode="matching"]')!);
    await screen.findByTestId('practice-matching');
    await user.click(screen.getByRole('button', { name: /Додому/ }));

    // The matching continuation belongs to matching; selecting a different mode card starts
    // a fresh session for that mode.
    await screen.findByTestId('practice-start-session');
    await user.click(container.querySelector<HTMLButtonElement>('[data-mode="flashcards"]')!);

    await waitFor(() =>
      expect(container.querySelector('[data-activity="flashcard"]')).toBeInTheDocument(),
    );
    expect(screen.queryByTestId('practice-matching')).not.toBeInTheDocument();
    expect(screen.getByTestId('practice-session-progress')).toHaveTextContent('0/');

    const snapshots = JSON.parse(localStorage.getItem('lu-practice-session')!);
    expect(snapshots.byMode.matching).toMatchObject({ modeFilter: 'matching', completed: 0 });
    expect(snapshots.byMode.flashcards).toMatchObject({
      modeFilter: 'flashcards',
      completed: 0,
      history: [],
    });
  });

  test('double-Enter during dwell advances exactly once (no double completion)', async () => {
    const { fn } = mockShardFetch({});
    vi.spyOn(globalThis, 'fetch').mockImplementation(fn);
    const user = userEvent.setup();
    render(<LexiconPractice initialDeck={heritageDeck()} autoStart initialMode="heritage" />);

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

    // Exactly one completion — a double-advance would have recorded two reviews.
    await waitFor(() => expect(storedState().reviews).toHaveLength(1));

    // Return home and confirm the idle dashboard is still usable.
    await user.click(screen.getByRole('button', { name: /Додому/ }));
    expect(await screen.findByTestId('practice-start-session')).toBeInTheDocument();
  });

  // --- Progressive shard loading tests for #4693 ---

  test('session starts after selected-level shards only (first item renders before lower-level fetches resolve)', async () => {
    localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, 'B1');
    const { fn, requested, releaseLowers, pendingCount } = mockProgressiveFetch({ A1: 2, A2: 1, B1: 2 });
    vi.spyOn(globalThis, 'fetch').mockImplementation(fn);
    const user = userEvent.setup();
    const { container } = render(<LexiconPractice />);

    await user.click(container.querySelector<HTMLButtonElement>('[data-mode="flashcards"]')!);

    // First item from B1 core must appear without the lower fetches having resolved.
    await waitFor(() => {
      expect(container.querySelector('[data-activity="flashcard"]')).toBeInTheDocument();
      expect(screen.getByText(/слово-B1-/)).toBeInTheDocument();
    });
    // Lowers were requested (bg started) but not resolved yet.
    expect(requested.some((u) => u.includes('practice-index.B1'))).toBe(true);
    expect(requested.some((u) => u.includes('practice-lexemes.B1'))).toBe(true);
    const lowerRequested = requested.filter((u) => /practice-(index|lexemes)\.A[12]/.test(u));
    expect(lowerRequested.length).toBeGreaterThan(0);
    expect(pendingCount()).toBeGreaterThan(0); // still held

    // session continues; release to clean
    releaseLowers();
  });

  test('pool grows when a background merge lands (item from a lower level becomes selectable)', async () => {
    localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, 'B1');
    const { fn, requested, releaseLowers } = mockProgressiveFetch({ A1: 1, B1: 2 });
    vi.spyOn(globalThis, 'fetch').mockImplementation(fn);
    const user = userEvent.setup();
    const { container } = render(<LexiconPractice />);

    await user.click(container.querySelector<HTMLButtonElement>('[data-mode="flashcards"]')!);

    await waitFor(() => expect(screen.getByText(/слово-B1-/)).toBeInTheDocument());

    // Before release, only B1 in pool. Advance one (if possible) or just release and verify a lower now fetchable by checking after.
    // Release the A1 shard.
    releaseLowers();

    // After merge, pool has grown. Complete current and check a lower-level lemma surfaces.
    // Rate the current to advance.
    const flash = container.querySelector<HTMLElement>('[data-activity="flashcard"]');
    if (flash) {
      await user.click(flash);
      const good = container.querySelector<HTMLButtonElement>('[data-rate="good"]');
      if (good && !good.disabled) await user.click(good);
    }

    await waitFor(() => {
      // Either the next card is A1 or at least an A1 fetch completed and merged.
      const hasA1 = requested.some((u) => u.includes('.A1.'));
      const showsA1 = screen.queryByText(/слово-A1-/);
      expect(hasA1 || !!showsA1).toBe(true);
    });
  });

  test('no double-fetch of the same shard; failed background shard degrades gracefully (session continues)', async () => {
    localStorage.setItem(LEARNER_LEVEL_STORAGE_KEY, 'B1');
    const requested: string[] = [];
    const fn = vi.fn(async (input: any) => {
      const url = String(input);
      requested.push(url);
      const m = url.match(/practice-(index|lexemes)\.(A1|A2|B1)\.json/);
      if (!m) return notFoundResponse();
      const kind = m[1];
      const lvl = m[2] as CefrLevel;
      if (lvl === 'A1') {
        // simulate fail for one background
        return notFoundResponse();
      }
      const n = lvl === 'B1' ? 2 : 1;
      const lexemes = Array.from({ length: n }, (_u, i) =>
        lexeme(`${lvl}-${i}`, `слово-${lvl}-${i}`, `g ${i}`, { nominative: 'x', accusative: 'x', locative: 'x' }, { cefr: lvl }),
      );
      if (kind === 'index') {
        return okJson({ deckVersion: `v-${lvl}`, level: lvl, items: lexemes.map((l, o) => ({ lemmaId: l.lemmaId, lemma: l.lemma, cefr: lvl, modes: ['flashcards'], hasCloze: false, clozeIds: [], newOrder: o })) });
      }
      return okJson({ deckVersion: `v-${lvl}`, level: lvl, lexemes });
    });
    vi.spyOn(globalThis, 'fetch').mockImplementation(fn);

    const user = userEvent.setup();
    const { container } = render(<LexiconPractice />);
    await user.click(container.querySelector<HTMLButtonElement>('[data-mode="flashcards"]')!);

    await waitFor(() => expect(container.querySelector('[data-activity="flashcard"]')).toBeInTheDocument());

    // No double-fetch for heavy lexeme shards (dedup via shardJsonCache); index may be 3
    // (eager due + daily snapshot deckVersion + core session) because the K3 dashboard
    // builds a versioned daily snapshot independently.
    const counts = requested.reduce<Record<string, number>>((acc, u) => { acc[u] = (acc[u] || 0) + 1; return acc; }, {});
    Object.entries(counts).forEach(([u, c]) => {
      if (u.includes('lexemes')) {
        expect(c).toBeLessThanOrEqual(1);
      } else {
        expect(c).toBeLessThanOrEqual(3);
      }
    });

    // A1 bg failed but session on B1 continues (no error banner, item visible)
    expect(screen.queryByText(/Не вдалося завантажити/)).not.toBeInTheDocument();
    expect(container.querySelector('[data-activity="flashcard"]')).toBeInTheDocument();
  });

  function matchingDeck(): PracticeDeckData {
    const lexemes = [
      lexeme('knyha', 'книга', 'book', { nominative: 'книга', accusative: 'книгу', locative: 'книзі' }),
      lexeme('robota', 'робота', 'work', { nominative: 'робота', accusative: 'роботу', locative: 'роботі' }),
      lexeme('misto', 'місто', 'city', { nominative: 'місто', accusative: 'місто', locative: 'місті' }),
      lexeme('shkola', 'школа', 'school', { nominative: 'школа', accusative: 'школу', locative: 'школі' }),
      lexeme('sady', 'сад', 'garden', { nominative: 'сад', accusative: 'сад', locative: 'саду' }),
      lexeme('dimy', 'дім', 'house', { nominative: 'дім', accusative: 'дім', locative: 'домі' }),
    ];
    return {
      deckVersion: 'test-matching',
      level: 'A1',
      lexemes,
      index: lexemes.map((entry, index) => ({
        lemmaId: entry.lemmaId,
        lemma: entry.lemma,
        cefr: 'A1',
        modes: ['matching'],
        hasCloze: false,
        clozeIds: [],
        newOrder: index,
      })),
      cloze: [],
    };
  }

  test('matching progress updates after each match', async () => {
    const user = userEvent.setup();
    const deck = matchingDeck();
    const { container } = render(<LexiconPractice initialDeck={deck} autoStart initialMode="matching" />);
    const leftColumn = container.querySelector('[data-activity="match-left-column"]');
    const rightColumn = container.querySelector('[data-activity="match-right-column"]');
    expect(leftColumn).toBeInTheDocument();
    expect(rightColumn).toBeInTheDocument();

    const pairs = within(leftColumn as HTMLElement).getAllByRole('button').map((button, index) => {
      const left = button.textContent?.trim() ?? '';
      const right = within(rightColumn as HTMLElement)
        .getAllByRole('button')
        .find((candidate) => candidate.getAttribute('data-original-index') === String(index));
      return { left, right };
    });

    const initialProgress = screen.getByText(/Доберіть пари/);
    expect(initialProgress).toHaveTextContent('0 з 6');

    await user.click(within(leftColumn as HTMLElement).getByRole('button', { name: pairs[0].left }));
    await user.click(pairs[0].right!);

    await waitFor(() => {
      expect(screen.getByText(/Доберіть пари/)).toHaveTextContent('1 з 6');
    });
  });

  test('matching practice opts into semantic-four pair coding', async () => {
    const user = userEvent.setup();
    const deck = matchingDeck();
    const { container } = render(<LexiconPractice initialDeck={deck} autoStart initialMode="matching" />);

    const leftCol = container.querySelector('[data-activity="match-left-column"]');
    const rightCol = container.querySelector('[data-activity="match-right-column"]');
    expect(leftCol).toBeInTheDocument();
    expect(rightCol).toBeInTheDocument();

    const findLeft = (text: string) => {
      const btn = within(leftCol as HTMLElement).getAllByRole('button').find((b) => {
        const tag = b.querySelector('.matchPairTag');
        const content = tag ? b.textContent?.replace(tag.textContent ?? '', '') : b.textContent;
        return content?.trim() === text;
      });
      if (!btn) throw new Error(`Left tile "${text}" not found`);
      return btn;
    };
    const findRight = (text: string) => {
      const btn = within(rightCol as HTMLElement).getAllByRole('button').find((b) => {
        const tag = b.querySelector('.matchPairTag');
        const content = tag ? b.textContent?.replace(tag.textContent ?? '', '') : b.textContent;
        return content?.trim() === text;
      });
      if (!btn) throw new Error(`Right tile "${text}" not found`);
      return btn;
    };

    const firstLeft = within(leftCol as HTMLElement).getAllByRole('button')[0];
    const selectedLemmaText = firstLeft?.textContent?.replace(firstLeft.querySelector('.matchPairTag')?.textContent ?? '', '').trim() ?? '';
    const textToGloss: Record<string, string> = {
      'книга': 'book',
      'робота': 'work',
      'місто': 'city',
      'школа': 'school',
      'сад': 'garden',
      'дім': 'house',
    };
    const selectedGloss = textToGloss[selectedLemmaText];

    // Match the first distractor and verify the semantic-four tag and token appear.
    const distractorWords = Object.keys(textToGloss).filter(w => w !== selectedLemmaText);
    await user.click(findLeft(distractorWords[0]));
    await user.click(findRight(textToGloss[distractorWords[0]]));

    const matchedLeft = findLeft(distractorWords[0]);
    const matchedRight = findRight(textToGloss[distractorWords[0]]);
    expect(matchedLeft).toHaveAttribute('data-pair-coding', 'semantic-four');
    expect(matchedRight).toHaveAttribute('data-pair-coding', 'semantic-four');
    expect(matchedLeft.querySelector('.matchPairTag')).toBeInTheDocument();
    expect(matchedRight.querySelector('.matchPairTag')).toBeInTheDocument();
    expect(matchedLeft.querySelector('.matchPairTag')).toHaveTextContent('①');
    expect(matchedRight.querySelector('.matchPairTag')).toHaveTextContent('①');

    // Matching the selected lemma produces the second tag.
    await user.click(findLeft(selectedLemmaText));
    await user.click(findRight(selectedGloss));
    await waitFor(() => {
      expect(findLeft(selectedLemmaText).querySelector('.matchPairTag')).toHaveTextContent('②');
    });
  });

  test('matching mode rates every matched pair with proper ratings', async () => {
    const user = userEvent.setup();
    const deck = matchingDeck();
    const { container } = render(<LexiconPractice initialDeck={deck} autoStart initialMode="matching" />);

    expect(screen.getByTestId('practice-matching')).toBeInTheDocument();

    const leftCol = container.querySelector('[data-activity="match-left-column"]');
    const rightCol = container.querySelector('[data-activity="match-right-column"]');
    expect(leftCol).toBeInTheDocument();
    expect(rightCol).toBeInTheDocument();

    const findLeft = (text: string) => {
      const btn = within(leftCol as HTMLElement).getAllByRole('button').find(b => b.textContent?.trim() === text);
      if (!btn) throw new Error(`Left tile "${text}" not found`);
      return btn;
    };
    const findRight = (text: string) => {
      const btn = within(rightCol as HTMLElement).getAllByRole('button').find(b => b.textContent?.trim() === text);
      if (!btn) throw new Error(`Right tile "${text}" not found`);
      return btn;
    };

    const selectedLemmaText = within(leftCol as HTMLElement).getAllByRole('button')[0]?.textContent?.trim() ?? '';

    const textToLemmaId: Record<string, string> = {
      'книга': 'knyha',
      'робота': 'robota',
      'місто': 'misto',
      'школа': 'shkola',
      'сад': 'sady',
      'дім': 'dimy',
    };
    const textToGloss: Record<string, string> = {
      'книга': 'book',
      'робота': 'work',
      'місто': 'city',
      'школа': 'school',
      'сад': 'garden',
      'дім': 'house',
    };

    const selectedLemmaId = textToLemmaId[selectedLemmaText];
    const selectedGloss = textToGloss[selectedLemmaText];
    const distractorWords = Object.keys(textToLemmaId).filter(w => w !== selectedLemmaText);

    // 1. Clean match for the first distractor -> good rating
    const dist0 = distractorWords[0];
    await user.click(findLeft(dist0));
    await user.click(findRight(textToGloss[dist0]));
    await waitFor(() => {
      const state = storedState();
      expect(state.reviews?.some(r => r.lemmaId === textToLemmaId[dist0] && r.rating === 'good')).toBe(true);
    });

    // 2. Match the second distractor with 1 miss -> hard rating
    const dist1 = distractorWords[1];
    await user.click(findLeft(dist1));
    await user.click(findRight(selectedGloss)); // wrong
    await new Promise(resolve => setTimeout(resolve, 900));
    await user.click(findLeft(dist1));
    await user.click(findRight(textToGloss[dist1]));
    await waitFor(() => {
      const state = storedState();
      expect(state.reviews?.some(r => r.lemmaId === textToLemmaId[dist1] && r.rating === 'hard')).toBe(true);
    });

    // 3. Match the third distractor with 2 misses -> again rating
    const dist2 = distractorWords[2];
    await user.click(findLeft(dist2));
    await user.click(findRight(textToGloss[distractorWords[3]])); // wrong 1
    await new Promise(resolve => setTimeout(resolve, 900));
    await user.click(findLeft(dist2));
    await user.click(findRight(textToGloss[distractorWords[4]])); // wrong 2
    await new Promise(resolve => setTimeout(resolve, 900));
    await user.click(findLeft(dist2));
    await user.click(findRight(textToGloss[dist2]));
    await waitFor(() => {
      const state = storedState();
      expect(state.reviews?.some(r => r.lemmaId === textToLemmaId[dist2] && r.rating === 'again')).toBe(true);
    });

    // Complete the remaining pairs cleanly
    const dist3 = distractorWords[3];
    await user.click(findLeft(dist3));
    await user.click(findRight(textToGloss[dist3]));
    await waitFor(() => {
      const state = storedState();
      expect(state.reviews?.some(r => r.lemmaId === textToLemmaId[dist3] && r.rating === 'good')).toBe(true);
    });

    const dist4 = distractorWords[4];
    await user.click(findLeft(dist4));
    await user.click(findRight(textToGloss[dist4]));
    await waitFor(() => {
      const state = storedState();
      expect(state.reviews?.some(r => r.lemmaId === textToLemmaId[dist4] && r.rating === 'good')).toBe(true);
    });

    // Finally, match the selected lemma cleanly
    await user.click(findLeft(selectedLemmaText));
    await user.click(findRight(selectedGloss));

    await waitFor(() => {
      const state = storedState();
      expect(state.reviews?.some(r => r.lemmaId === selectedLemmaId && r.rating === 'good')).toBe(true);
    });

    const state = storedState();
    expect(state.reviews?.length).toBe(6);
  });

  test('abort after 2 matches rates exactly those 2', async () => {
    const user = userEvent.setup();
    const deck = matchingDeck();
    const { container, unmount } = render(<LexiconPractice initialDeck={deck} autoStart initialMode="matching" />);

    const leftCol = container.querySelector('[data-activity="match-left-column"]');
    const rightCol = container.querySelector('[data-activity="match-right-column"]');
    expect(leftCol).toBeInTheDocument();
    expect(rightCol).toBeInTheDocument();

    const findLeft = (text: string) => {
      const btn = within(leftCol as HTMLElement).getAllByRole('button').find(b => b.textContent?.trim() === text);
      if (!btn) throw new Error(`Left tile "${text}" not found`);
      return btn;
    };
    const findRight = (text: string) => {
      const btn = within(rightCol as HTMLElement).getAllByRole('button').find(b => b.textContent?.trim() === text);
      if (!btn) throw new Error(`Right tile "${text}" not found`);
      return btn;
    };

    const selectedLemmaText = within(leftCol as HTMLElement).getAllByRole('button')[0]?.textContent?.trim() ?? '';

    const textToLemmaId: Record<string, string> = {
      'книга': 'knyha',
      'робота': 'robota',
      'місто': 'misto',
      'школа': 'shkola',
      'сад': 'sady',
      'дім': 'dimy',
    };
    const textToGloss: Record<string, string> = {
      'книга': 'book',
      'робота': 'work',
      'місто': 'city',
      'школа': 'school',
      'сад': 'garden',
      'дім': 'house',
    };

    const selectedLemmaId = textToLemmaId[selectedLemmaText];
    const selectedGloss = textToGloss[selectedLemmaText];
    const distractorWords = Object.keys(textToLemmaId).filter(w => w !== selectedLemmaText);

    // Match 1 distractor cleanly
    const dist0 = distractorWords[0];
    await user.click(findLeft(dist0));
    await user.click(findRight(textToGloss[dist0]));
    await waitFor(() => {
      const state = storedState();
      expect(state.reviews?.some(r => r.lemmaId === textToLemmaId[dist0] && r.rating === 'good')).toBe(true);
    });

    // Match selected lemma cleanly
    await user.click(findLeft(selectedLemmaText));
    await user.click(findRight(selectedGloss));
    {
      const state = storedState();
      expect(state.reviews?.some(r => r.lemmaId === selectedLemmaId)).toBe(false);
    }

    // Abort by unmounting
    unmount();

    const state = storedState();
    expect(state.reviews?.length).toBe(2);
    expect(state.reviews?.some(r => r.lemmaId === textToLemmaId[dist0] && r.rating === 'good')).toBe(true);
    expect(state.reviews?.some(r => r.lemmaId === selectedLemmaId && r.rating === 'good')).toBe(true);
  });

  test('attempt counting resets between boards', async () => {
    const user = userEvent.setup();
    const deck = matchingDeck();
    const { container } = render(<LexiconPractice initialDeck={deck} autoStart initialMode="matching" />);

    const leftCol = container.querySelector('[data-activity="match-left-column"]');
    const rightCol = container.querySelector('[data-activity="match-right-column"]');
    expect(leftCol).toBeInTheDocument();
    expect(rightCol).toBeInTheDocument();

    const findLeft = (text: string) => {
      const btn = within(leftCol as HTMLElement).getAllByRole('button').find(b => b.textContent?.trim() === text);
      if (!btn) throw new Error(`Left tile "${text}" not found`);
      return btn;
    };
    const findRight = (text: string) => {
      const btn = within(rightCol as HTMLElement).getAllByRole('button').find(b => b.textContent?.trim() === text);
      if (!btn) throw new Error(`Right tile "${text}" not found`);
      return btn;
    };

    const selectedLemmaText = within(leftCol as HTMLElement).getAllByRole('button')[0]?.textContent?.trim() ?? '';

    const textToLemmaId: Record<string, string> = {
      'книга': 'knyha',
      'робота': 'robota',
      'місто': 'misto',
      'школа': 'shkola',
      'сад': 'sady',
      'дім': 'dimy',
    };
    const textToGloss: Record<string, string> = {
      'книга': 'book',
      'робота': 'work',
      'місто': 'city',
      'школа': 'school',
      'сад': 'garden',
      'дім': 'house',
    };

    const selectedLemmaId = textToLemmaId[selectedLemmaText];
    const selectedGloss = textToGloss[selectedLemmaText];
    const distractorWords = Object.keys(textToLemmaId).filter(w => w !== selectedLemmaText);

    // Miss on the second distractor (dist1 - misto, which will still be a distractor on the next board)
    const dist1 = distractorWords[1];
    await user.click(findLeft(dist1));
    await user.click(findRight(selectedGloss)); // wrong
    await new Promise(resolve => setTimeout(resolve, 900));

    // Complete that distractor -> hard
    await user.click(findLeft(dist1));
    await user.click(findRight(textToGloss[dist1]));
    await waitFor(() => {
      expect(storedState().reviews?.some(r => r.lemmaId === textToLemmaId[dist1] && r.rating === 'hard')).toBe(true);
    });

    // Complete all other matches cleanly
    for (const dist of distractorWords.filter(w => w !== dist1)) {
      await user.click(findLeft(dist));
      await user.click(findRight(textToGloss[dist]));
    }
    await user.click(findLeft(selectedLemmaText));
    await user.click(findRight(selectedGloss));

    await waitFor(() => {
      expect(storedState().reviews?.length).toBe(6);
    });

    // The completed board dwells; advance explicitly to the next selection/board.
    await user.click(screen.getByTestId('practice-advance-button'));

    // Clean match on next board for that same distractor (should start with 0 misses, rate as good)
    const newLeftCol = container.querySelector('[data-activity="match-left-column"]');
    const newRightCol = container.querySelector('[data-activity="match-right-column"]');
    const findNewLeft = (text: string) => {
      const btn = within(newLeftCol as HTMLElement).getAllByRole('button').find(b => b.textContent?.trim() === text);
      if (!btn) throw new Error(`Left tile "${text}" not found`);
      return btn;
    };
    const findNewRight = (text: string) => {
      const btn = within(newRightCol as HTMLElement).getAllByRole('button').find(b => b.textContent?.trim() === text);
      if (!btn) throw new Error(`Right tile "${text}" not found`);
      return btn;
    };

    await user.click(findNewLeft(dist1));
    await user.click(findNewRight(textToGloss[dist1]));

    await waitFor(() => {
      const state = storedState();
      expect(state.reviews?.length).toBe(7);
      expect(state.reviews?.[6]).toMatchObject({
        lemmaId: textToLemmaId[dist1],
        mode: 'matching',
        rating: 'good',
      });
    });
  });

  test('rapid double-click on the same match → exactly ONE review recorded', async () => {
    const deck = matchingDeck();
    const { container } = render(<LexiconPractice initialDeck={deck} autoStart initialMode="matching" />);

    const leftCol = container.querySelector('[data-activity="match-left-column"]');
    const rightCol = container.querySelector('[data-activity="match-right-column"]');
    expect(leftCol).toBeInTheDocument();
    expect(rightCol).toBeInTheDocument();

    const findLeft = (text: string) => {
      const btn = within(leftCol as HTMLElement).getAllByRole('button').find(b => b.textContent?.trim() === text);
      if (!btn) throw new Error(`Left tile "${text}" not found`);
      return btn;
    };
    const findRight = (text: string) => {
      const btn = within(rightCol as HTMLElement).getAllByRole('button').find(b => b.textContent?.trim() === text);
      if (!btn) throw new Error(`Right tile "${text}" not found`);
      return btn;
    };

    const selectedLemmaText = within(leftCol as HTMLElement).getAllByRole('button')[0]?.textContent?.trim() ?? '';

    const textToLemmaId: Record<string, string> = {
      'книга': 'knyha',
      'робота': 'robota',
      'місто': 'misto',
      'школа': 'shkola',
      'сад': 'sady',
      'дім': 'dimy',
    };
    const textToGloss: Record<string, string> = {
      'книга': 'book',
      'робота': 'work',
      'місто': 'city',
      'школа': 'school',
      'сад': 'garden',
      'дім': 'house',
    };

    const distractorWords = Object.keys(textToLemmaId).filter(w => w !== selectedLemmaText);
    const dist0 = distractorWords[0];

    // Select left tile
    fireEvent.click(findLeft(dist0));

    // Rapid double click on the correct right tile using synchronous fireEvent
    const rightTile = findRight(textToGloss[dist0]);
    fireEvent.click(rightTile);
    fireEvent.click(rightTile);

    // Verify exactly one review is recorded for dist0
    await waitFor(() => {
      const state = storedState();
      const matchingReviews = state.reviews?.filter(r => r.lemmaId === textToLemmaId[dist0]);
      expect(matchingReviews?.length).toBe(1);
    });
  });

  test('deck object replaced mid-board (simulated background merge) → board pairs stay pinned and rate original lemma', async () => {
    const user = userEvent.setup();
    const deck = matchingDeck();
    const { container, rerender } = render(<LexiconPractice initialDeck={deck} autoStart initialMode="matching" />);

    const leftCol = container.querySelector('[data-activity="match-left-column"]');
    const rightCol = container.querySelector('[data-activity="match-right-column"]');
    expect(leftCol).toBeInTheDocument();
    expect(rightCol).toBeInTheDocument();

    const findLeft = (text: string) => {
      const btn = within(leftCol as HTMLElement).getAllByRole('button').find(b => b.textContent?.trim() === text);
      if (!btn) throw new Error(`Left tile "${text}" not found`);
      return btn;
    };
    const findRight = (text: string) => {
      const btn = within(rightCol as HTMLElement).getAllByRole('button').find(b => b.textContent?.trim() === text);
      if (!btn) throw new Error(`Right tile "${text}" not found`);
      return btn;
    };

    const selectedLemmaText = within(leftCol as HTMLElement).getAllByRole('button')[0]?.textContent?.trim() ?? '';

    const textToLemmaId: Record<string, string> = {
      'книга': 'knyha',
      'робота': 'robota',
      'місто': 'misto',
      'школа': 'shkola',
      'сад': 'sady',
      'дім': 'dimy',
    };
    const textToGloss: Record<string, string> = {
      'книга': 'book',
      'робота': 'work',
      'місто': 'city',
      'школа': 'school',
      'сад': 'garden',
      'дім': 'house',
    };

    const distractorWords = Object.keys(textToLemmaId).filter(w => w !== selectedLemmaText);
    const dist0 = distractorWords[0];

    // Re-render component with an updated deck object to simulate background merge
    const newDeck = {
      ...deck,
      deckVersion: 'test-matching-merged',
    };
    rerender(<LexiconPractice initialDeck={newDeck} autoStart initialMode="matching" />);

    // Match the distractor from the pinned board
    await user.click(findLeft(dist0));
    await user.click(findRight(textToGloss[dist0]));

    await waitFor(() => {
      const state = storedState();
      // It should rate the original lemma from the pinned board
      expect(state.reviews?.some(r => r.lemmaId === textToLemmaId[dist0] && r.rating === 'good')).toBe(true);
    });
  });

  describe('no-auto-advance dwell matrix (Chunk 3)', () => {
    async function solveMatchingBoard(user: ReturnType<typeof userEvent.setup>, container: HTMLElement) {
      const leftCol = container.querySelector('[data-activity="match-left-column"]');
      const rightCol = container.querySelector('[data-activity="match-right-column"]');
      if (!leftCol || !rightCol) throw new Error('Matching columns not found');
      const leftButtons = within(leftCol as HTMLElement).getAllByRole('button');
      const rightButtons = within(rightCol as HTMLElement).getAllByRole('button');
      for (const left of leftButtons as HTMLButtonElement[]) {
        if (left.disabled) continue;
        const originalIndex = leftButtons.indexOf(left);
        const right = (rightButtons as HTMLButtonElement[]).find(
          (button) => button.getAttribute('data-original-index') === String(originalIndex),
        );
        if (!right || right.disabled) continue;
        await user.click(left);
        await user.click(right);
      }
    }

    const cases: Array<{
      mode: string;
      deck: PracticeDeckData;
      answer: (user: ReturnType<typeof userEvent.setup>, container: HTMLElement) => Promise<void>;
    }> = [
      {
        mode: 'flashcards',
        deck: sampleDeckWithOnlyMode('knyha', 'flashcards'),
        answer: async (user, container) => {
          const card = container.querySelector<HTMLElement>('[data-activity="flashcard"]')!;
          await user.click(card);
          await user.click(container.querySelector<HTMLButtonElement>('[data-rate="good"]')!);
        },
      },
      {
        mode: 'matching',
        deck: smallMatchingDeck(),
        answer: async (user, container) => solveMatchingBoard(user, container),
      },
      {
        mode: 'choice',
        deck: sampleDeckWithOnlyMode('knyha', 'choice'),
        answer: async (user) => {
          await user.click(screen.getByRole('button', { name: /книга/ }));
        },
      },
      {
        mode: 'cloze',
        deck: sampleDeck(),
        answer: async (user) => {
          const input = screen.getByPlaceholderText(/введіть слово/);
          await user.type(input, 'книгу');
          await user.click(screen.getByRole('button', { name: /Перевірити/ }));
        },
      },
      {
        mode: 'stress',
        deck: stressDeck(),
        answer: async (user) => {
          const buttons = within(screen.getByTestId('practice-stress')).getAllByRole('button');
          const target = buttons.find((button) => button.dataset.position === '1');
          expect(target).toBeDefined();
          await user.click(target!);
        },
      },
      {
        mode: 'classify',
        deck: classifyDeck(),
        answer: async (user) => {
          await user.click(screen.getByRole('button', { name: /жіночий/ }));
        },
      },
      {
        mode: 'paradigm',
        deck: paradigmDeck(),
        answer: async (user) => {
          await user.click(screen.getByRole('button', { name: /кави/ }));
        },
      },
      {
        mode: 'synonym',
        deck: synonymDeck(),
        answer: async (user) => {
          await user.click(screen.getByRole('button', { name: /кава/ }));
        },
      },
      {
        mode: 'paronym',
        deck: paronymDeck(),
        answer: async (user) => {
          await user.click(screen.getByRole('button', { name: /бігає/ }));
        },
      },
      {
        mode: 'heritage',
        deck: heritageDeck(),
        answer: async (user) => {
          await user.click(within(screen.getByTestId('practice-heritage')).getByRole('button', { name: /дім/ }));
        },
      },
    ];

    test.each(cases)('$mode: answer records and parks until explicit next', async ({ mode, deck, answer }) => {
      const user = userEvent.setup();
      const { container } = render(
        <LexiconPractice initialDeck={deck} autoStart initialMode={mode as any} />,
      );

      await answer(user, container);

      const advance = await screen.findByTestId('practice-advance-button');
      expect(advance).toBeInTheDocument();
      expect(advance).toHaveFocus();

      await user.click(advance);

      await waitFor(() => {
        expect(screen.queryByTestId('practice-advance-button')).not.toBeInTheDocument();
      });
    });
  });

  describe('PracticeStress N-vowel generality', () => {
    function stressDeckWithNuclei(
      word: string,
      nuclei: { index: number; label: string }[],
      stressIndex: number,
    ): PracticeDeckData {
      const entry = lexeme('stress-fixture', word, 'fixture', {
        nominative: word,
        accusative: word,
        locative: word,
      });
      return {
        deckVersion: 'test-stress-n',
        level: 'A1',
        lexemes: [entry],
        index: [{
          lemmaId: entry.lemmaId,
          lemma: entry.lemma,
          cefr: 'A1',
          modes: ['stress'],
          hasCloze: false,
          clozeIds: [],
          newOrder: 0,
        }],
        cloze: [],
        stress: [{
          stressId: 'stress-n',
          lemmaId: 'stress-fixture',
          lemma: word,
          stressed: word,
          unstressed: word,
          stressIndex,
          nuclei,
          source: 'fixture',
        }],
        classify: [],
        paradigm: [],
        synonym: [],
      };
    }

    test.each([
      { count: 2, word: 'кава', nuclei: [{ index: 0, label: 'а' }, { index: 2, label: 'а' }], stressIndex: 2 },
      { count: 3, word: 'україна', nuclei: [{ index: 1, label: 'у' }, { index: 3, label: 'а' }, { index: 5, label: 'и' }], stressIndex: 5 },
      { count: 5, word: 'автентифікація', nuclei: [{ index: 0, label: 'а' }, { index: 2, label: 'е' }, { index: 5, label: 'і' }, { index: 8, label: 'а' }, { index: 11, label: 'і' }], stressIndex: 8 },
    ])('renders $count vowel buttons preserving code-point positions', async ({ word, nuclei, stressIndex }) => {
      const user = userEvent.setup();
      render(<LexiconPractice initialDeck={stressDeckWithNuclei(word, nuclei, stressIndex)} autoStart initialMode="stress" />);

      const buttons = within(screen.getByTestId('practice-stress')).getAllByRole('button');
      expect(buttons).toHaveLength(nuclei.length);

      const target = buttons.find((button) => button.dataset.position === String(stressIndex));
      expect(target).toBeDefined();
      await user.click(target!);

      expect(screen.getByTestId('practice-stress-verdict')).toHaveTextContent('✓');
      expect(screen.queryByTestId('practice-form-rail')).not.toBeInTheDocument();
    });

    test('selecting the wrong nucleus records a wrong verdict and keeps the selected vowel highlighted', async () => {
      const nuclei = [
        { index: 0, label: 'а' },
        { index: 2, label: 'а' },
      ];
      const user = userEvent.setup();
      render(<LexiconPractice initialDeck={stressDeckWithNuclei('кава', nuclei, 2)} autoStart initialMode="stress" />);

      const buttons = within(screen.getByTestId('practice-stress')).getAllByRole('button');
      await user.click(buttons[0]!);

      expect(screen.getByTestId('practice-stress-verdict')).toHaveTextContent('✗');
      expect(screen.queryByTestId('practice-form-rail')).not.toBeInTheDocument();
    });
  });

  describe('PracticeFormRail presence', () => {
    test.each([
      { mode: 'cloze', deck: sampleDeck(), expectRail: true, action: async (user: ReturnType<typeof userEvent.setup>) => { await user.click(screen.getByRole('button', { name: 'книгу' })); await user.click(screen.getByRole('button', { name: /Перевірити/ })); } },
      { mode: 'paradigm', deck: paradigmDeck(), expectRail: true, action: async (user: ReturnType<typeof userEvent.setup>) => { await user.click(screen.getByRole('button', { name: /кави/ })); } },
      { mode: 'paronym', deck: paronymDeck(), expectRail: true, action: async (user: ReturnType<typeof userEvent.setup>) => { await user.click(screen.getByRole('button', { name: /бігає/ })); } },
      { mode: 'heritage', deck: heritageDeck(), expectRail: true, action: async (user: ReturnType<typeof userEvent.setup>) => { await user.click(within(screen.getByTestId('practice-heritage')).getByRole('button', { name: /дім/ })); } },
      { mode: 'flashcards', deck: sampleDeckWithOnlyMode('knyha', 'flashcards'), expectRail: false, action: async (user: ReturnType<typeof userEvent.setup>, container: HTMLElement) => { const card = container.querySelector<HTMLElement>('[data-activity="flashcard"]')!; await user.click(card); await user.click(container.querySelector<HTMLButtonElement>('[data-rate="good"]')!); } },
      { mode: 'matching', deck: smallMatchingDeck(), expectRail: false, action: async (user: ReturnType<typeof userEvent.setup>, container: HTMLElement) => {
        const leftCol = container.querySelector('[data-activity="match-left-column"]');
        const rightCol = container.querySelector('[data-activity="match-right-column"]');
        if (!leftCol || !rightCol) throw new Error('Matching columns not found');
        const leftTiles = Array.from(leftCol.querySelectorAll('[data-activity="match-left-tile"]'));
        const rightTiles = Array.from(rightCol.querySelectorAll('[data-activity="match-right-tile"]'));
        for (const left of leftTiles) {
          const pairId = left.getAttribute('data-pair-id');
          const right = rightTiles.find((t) => t.getAttribute('data-pair-id') === pairId);
          if (right) {
            await user.click(left);
            await user.click(right);
          }
        }
      } },
      { mode: 'choice', deck: sampleDeckWithOnlyMode('knyha', 'choice'), expectRail: false, action: async (user: ReturnType<typeof userEvent.setup>) => { await user.click(screen.getByRole('button', { name: /книга/ })); } },
      { mode: 'stress', deck: stressDeck(), expectRail: false, action: async (user: ReturnType<typeof userEvent.setup>) => { const buttons = within(screen.getByTestId('practice-stress')).getAllByRole('button'); const target = buttons.find((button) => button.dataset.position === '1'); expect(target).toBeDefined(); await user.click(target!); } },
      { mode: 'classify', deck: classifyDeck(), expectRail: false, action: async (user: ReturnType<typeof userEvent.setup>) => { await user.click(screen.getByRole('button', { name: /жіночий/ })); } },
      { mode: 'synonym', deck: synonymDeck(), expectRail: false, action: async (user: ReturnType<typeof userEvent.setup>) => { await user.click(screen.getByRole('button', { name: /кава/ })); } },
    ])('$mode: rail is $expectRail', async ({ mode, deck, expectRail, action }) => {
      const user = userEvent.setup();
      const { container } = render(<LexiconPractice initialDeck={deck} autoStart initialMode={mode as any} />);

      await action(user, container);

      if (expectRail) {
        expect(screen.getByTestId('practice-form-rail')).toBeInTheDocument();
      } else {
        expect(screen.queryByTestId('practice-form-rail')).not.toBeInTheDocument();
      }
    });
  });

  test('heritage rail preserves source "день" and rail form "днями" while sentence keeps "Днями"', async () => {
    const item: PracticeHeritageItem = {
      ...heritagePracticeItem(),
      heritageId: 'her-den-fixture',
      lemmaId: 'den',
      srsKey: cardKey('den', 'heritage'),
      lemma: 'день',
      nativeLemma: 'день',
      calqueLabel: 'дом',
      prompt: '___ я був у місті.',
      answer: 'днями',
      options: [
        { label: 'Днями' },
        { label: 'домами' },
      ],
      rationaleUk: 'питоме українське слово',
    };
    const deck: PracticeDeckData = {
      ...heritageDeck(),
      lexemes: [lexeme('den', 'день', 'day', { nominative: 'день', accusative: 'день', locative: 'дні' })],
      index: [{
        lemmaId: 'den',
        lemma: 'день',
        cefr: 'A2',
        modes: ['heritage'],
        hasCloze: false,
        clozeIds: [],
        newOrder: 0,
      }],
      heritage: [item],
    };
    const user = userEvent.setup();
    render(<LexiconPractice initialDeck={deck} autoStart initialMode="heritage" />);

    await user.click(within(screen.getByTestId('practice-heritage')).getByRole('button', { name: /Днями/ }));

    const rail = screen.getByTestId('practice-form-rail');
    expect(rail).toHaveTextContent('день');
    expect(rail).toHaveTextContent('днями');
    expect(rail).not.toHaveTextContent('Днями');

    const sentence = within(screen.getByTestId('practice-heritage')).getByText((_, element) =>
      element?.classList.contains('heritage-slot') ?? false,
    );
    expect(sentence).toHaveTextContent('Днями');
  });

  test('summary renders score ratio and Ukrainian proverb', () => {
    const stats: SessionSummaryStats = {
      correct: 18,
      lapsed: 2,
      advancedToReview: [],
      streak: 5,
      nextDueLabel: null,
      deferredLemmas: [],
    };
    const { container } = render(
      <PracticeSessionSummary
        stats={stats}
        chromeLocale="uk"
        onAnotherSession={() => undefined}
        onDone={() => undefined}
      />,
    );

    expect(screen.getByTestId('practice-session-summary')).toHaveTextContent('18/20');
    expect(container.querySelector('blockquote')).toHaveTextContent('Терпи, козаче — отаманом будеш.');
    expect(container.querySelector('figcaption')).toHaveTextContent("Українське прислів'я");
  });
});
