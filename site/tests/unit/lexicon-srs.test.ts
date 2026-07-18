import { beforeEach, describe, expect, test } from 'vitest';
import { State } from 'ts-fsrs';
import {
  DAILY_PRACTICE_DECK_KEY,
  DAILY_PRACTICE_DECK_SIZE,
  PRACTICE_MODE_DECK_VERSION,
  PRACTICE_MODES,
  PUBLISHED_PRACTICE_LEVELS,
  MAX_RAW_REVIEW_LOG_ENTRIES,
  SRS_BACKUP_KEY,
  SRS_SETTINGS_KEY,
  SRS_STORAGE_KEY,
  buildDailyPracticeDeckSnapshot,
  cardKey,
  countDailyPracticeDone,
  deriveDailyPracticeRows,
  detectClockJump,
  getDueQueue,
  isPracticeMode,
  loadState,
  masteredCount,
  parseCardKey,
  rateCard,
  readDailyPracticeDeckSnapshot,
  refillDailyPracticeDeckSnapshot,
  saveState,
  selectDailyPracticeDeckItems,
  selectNextPracticeItem,
  seededAnswerIndex,
  uaPlural,
  validateClozeOptions,
  writeDailyPracticeDeckSnapshot,
  type CardState,
  type PracticeClozeItem,
  type PracticeDeckData,
  type PracticeHeritageItem,
  type PracticeIndexItem,
  type PracticeLexeme,
  type PracticeMode,
  type PracticeSelection,
  type ReviewLogEntry,
  type SelectionHistoryItem,
} from '@site/src/lib/lexicon/srs';

const NOW = new Date('2026-06-23T12:00:00.000Z');
const HOUR_MS = 60 * 60 * 1000;
const DAY_MS = 24 * 60 * 60 * 1000;

function stateCard(overrides: Partial<ReturnType<typeof rateCard>> = {}) {
  return {
    due: NOW.getTime(),
    stability: 5,
    difficulty: 4,
    elapsed_days: 0,
    scheduled_days: 1,
    learning_steps: 0,
    reps: 2,
    lapses: 0,
    state: 2,
    ...overrides,
  };
}

function reviewEntry(index: number, card = 'alpha'): ReviewLogEntry {
  const reviewedAt = NOW.getTime() + index * 60_000;
  return {
    cardKey: cardKey(card, 'flashcards'),
    lemmaId: card,
    mode: 'flashcards',
    rating: index % 2 === 0 ? 'good' : 'again',
    state: State.Review,
    due: reviewedAt + DAY_MS,
    stability: 5,
    difficulty: 4,
    elapsed_days: 1,
    last_elapsed_days: 1,
    scheduled_days: 1,
    learning_steps: 0,
    review: reviewedAt,
  };
}

class SizeLimitedStorage {
  readonly values = new Map<string, string>();
  readonly writes: string[] = [];
  readonly removals: string[] = [];

  constructor(private readonly maximumBytes: number, seed: Record<string, string> = {}) {
    for (const [key, value] of Object.entries(seed)) this.values.set(key, value);
  }

  getItem(key: string): string | null {
    return this.values.get(key) ?? null;
  }

  setItem(key: string, value: string): void {
    this.writes.push(key);
    const previous = this.values.get(key)?.length ?? 0;
    const nextTotal = [...this.values.values()].reduce((total, stored) => total + stored.length, 0) - previous + value.length;
    if (nextTotal > this.maximumBytes) {
      const error = new Error('storage quota exceeded');
      error.name = 'QuotaExceededError';
      throw error;
    }
    this.values.set(key, value);
  }

  removeItem(key: string): void {
    this.removals.push(key);
    this.values.delete(key);
  }
}

class BackupFailingStorage extends SizeLimitedStorage {
  setItem(key: string, value: string): void {
    if (key === SRS_BACKUP_KEY) {
      const error = new Error('backup unavailable');
      error.name = 'QuotaExceededError';
      throw error;
    }
    super.setItem(key, value);
  }
}

function lexeme(
  lemmaId: string,
  lemma = lemmaId,
  gloss = `${lemmaId} gloss`,
  cefr = 'A1',
): PracticeLexeme {
  return {
    lemmaId,
    lemma,
    lemmaPlain: lemma,
    gloss,
    ipa: null,
    pos: 'noun',
    cefr,
    heritage: null,
    severity: null,
    paradigm: {
      cases: {
        nominative: { singular: lemma },
        accusative: { singular: `${lemma}у` },
        locative: { singular: `${lemma}і` },
      },
    },
  };
}

function deck(ids: string[]): PracticeLexeme[] {
  return ids.map((id) => lexeme(id));
}

function cloze(
  lemmaId: string,
  clozeId: string,
  blankCase: string,
  form: string,
  frame = `${clozeId}-frame`,
): PracticeClozeItem {
  return {
    clozeId,
    lemmaId,
    sentenceFrameId: frame,
    sentence: 'Я бачу ___.',
    blankCase,
    form,
    clozeEn: 'I see it.',
    caseRule: {
      ruleId: `${blankCase}-rule`,
      case: blankCase,
      caseLabel: blankCase,
      trigger: 'trigger',
      triggerLabel: 'trigger',
      feedback: `trigger -> ${blankCase}`,
    },
    options: [
      { optionId: `${clozeId}:a`, label: form, lemmaId, kind: 'answer', case: blankCase },
      { optionId: `${clozeId}:b`, label: lemmaId, lemmaId, kind: 'same-root-lemma', case: 'nominative' },
      {
        optionId: `${clozeId}:c`,
        label: `${lemmaId}-decoy`,
        lemmaId: `${lemmaId}-decoy`,
        kind: 'decoy-lemma',
        case: 'nominative',
      },
      {
        optionId: `${clozeId}:d`,
        label: `${lemmaId}-decoyu`,
        lemmaId: `${lemmaId}-decoy`,
        kind: 'decoy-oblique',
        case: blankCase,
      },
    ],
  };
}

function heritageItem(lemmaId: string, heritageId = `${lemmaId}:heritage:1`): PracticeHeritageItem {
  return {
    heritageId,
    lemmaId,
    srsKey: cardKey(lemmaId, 'heritage'),
    lemma: lemmaId,
    nativeLemma: lemmaId,
    calqueLabel: `${lemmaId}-calque`,
    kind: 'lexical',
    prompt: 'Я бачу ___ щодня.',
    answer: lemmaId,
    calque: `${lemmaId}-calque`,
    origin: 'fixture',
    frameIndex: 1,
    cefr: 'A1',
    options: [
      { label: lemmaId },
      { label: `${lemmaId}-calque` },
      { label: `${lemmaId}-d1` },
      { label: `${lemmaId}-d2` },
    ],
    rationale: 'fixture rationale',
    citations: ['fixture citation'],
    corrections: [lemmaId],
    sourceFamily: 'fixture',
  };
}

function practiceDeck(): PracticeDeckData {
  const lexemes = [lexeme('alpha'), lexeme('beta'), lexeme('gamma'), lexeme('delta')];
  const clozeItems = [
    cloze('alpha', 'alpha-cloze', 'accusative', 'alphaу'),
    cloze('beta', 'beta-cloze', 'locative', 'betaі'),
    cloze('gamma', 'gamma-cloze', 'dative', 'gammaові'),
  ];
  return {
    deckVersion: 'test',
    level: 'A1',
    lexemes,
    cloze: clozeItems,
    index: lexemes.map((entry, index) => ({
      lemmaId: entry.lemmaId,
      lemma: entry.lemma,
      cefr: 'A1',
      modes: ['flashcards', 'matching', 'choice', ...(index < 3 ? ['cloze' as const] : [])],
      hasCloze: index < 3,
      clozeIds: index < 3 ? [clozeItems[index].clozeId] : [],
      newOrder: index,
    })),
  };
}

function modeDeck(rows: { id: string; modes: PracticeMode[] }[]): PracticeDeckData {
  const lexemes = rows.map((row) => lexeme(row.id));
  return {
    deckVersion: 'test',
    level: 'A1',
    lexemes,
    cloze: [],
    stress: rows
      .filter((row) => row.modes.includes('stress'))
      .map((row) => ({
        stressId: `${row.id}:stress`,
        lemmaId: row.id,
        lemma: row.id,
        stressed: `${row.id}́`,
        unstressed: row.id,
        stressIndex: 0,
        nuclei: [{ index: 0, label: row.id[0] ?? 'а' }, { index: 1, label: 'а' }],
        source: 'fixture',
      })),
    classify: rows
      .filter((row) => row.modes.includes('classify'))
      .map((row) => ({
        classifyId: `${row.id}:classify`,
        lemmaId: row.id,
        lemma: row.id,
        source: 'fixture',
        sets: [
          {
            setId: 'gender',
            setLabelUk: 'рід',
            answer: 'masculine',
            answerLabelUk: 'чоловічий',
            options: [
              { value: 'masculine', labelUk: 'чоловічий' },
              { value: 'feminine', labelUk: 'жіночий' },
              { value: 'neuter', labelUk: 'середній' },
            ],
          },
          {
            setId: 'pos',
            setLabelUk: 'частина мови',
            answer: 'noun',
            answerLabelUk: 'іменник',
            options: [
              { value: 'noun', labelUk: 'іменник' },
              { value: 'verb', labelUk: 'дієслово' },
              { value: 'adjective', labelUk: 'прикметник' },
            ],
          },
        ],
      })),
    paradigm: rows
      .filter((row) => row.modes.includes('paradigm'))
      .map((row) => ({
        paradigmId: `${row.id}:paradigm:1`,
        lemmaId: row.id,
        lemma: row.id,
        slot: { case: 'знахідний', number: 'singular', labelUk: 'знахідний відмінок, однина' },
        form: `${row.id}у`,
        options: [
          { label: `${row.id}у`, kind: 'answer' },
          { label: row.id, kind: 'same-paradigm' },
          { label: `${row.id}і`, kind: 'same-paradigm' },
          { label: `${row.id}ом`, kind: 'same-paradigm' },
        ],
      })),
    synonym: rows
      .filter((row) => row.modes.includes('synonym'))
      .map((row) => ({
        synonymId: `${row.id}:synonym`,
        lemmaId: row.id,
        targetLemmaId: `${row.id}-target`,
        polarity: 'synonym' as const,
        prompt: row.id,
        answer: `${row.id}-answer`,
        source: 'fixture',
        options: [
          { label: `${row.id}-answer`, lemmaId: `${row.id}-target`, kind: 'answer' },
          { label: `${row.id}-d1`, lemmaId: `${row.id}-d1`, kind: 'distractor' },
          { label: `${row.id}-d2`, lemmaId: `${row.id}-d2`, kind: 'distractor' },
          { label: `${row.id}-d3`, lemmaId: `${row.id}-d3`, kind: 'distractor' },
        ],
      })),
    heritage: rows
      .filter((row) => row.modes.includes('heritage'))
      .map((row) => heritageItem(row.id)),
    index: rows.map((row, index) => ({
      lemmaId: row.id,
      lemma: row.id,
      cefr: 'A1',
      modes: row.modes,
      hasCloze: false,
      clozeIds: [],
      newOrder: index,
    })),
  };
}

function flashcardDeck(
  rows: { id: string; cefr?: string }[],
  level = 'A1',
  deckVersion = 'test',
): PracticeDeckData {
  const lexemes = rows.map((row) => lexeme(row.id, row.id, `${row.id} gloss`, row.cefr ?? 'A1'));
  return {
    deckVersion,
    level,
    lexemes,
    cloze: [],
    stress: [],
    classify: [],
    paradigm: [],
    synonym: [],
    heritage: [],
    index: lexemes.map((entry, index) => ({
      lemmaId: entry.lemmaId,
      lemma: entry.lemma,
      cefr: entry.cefr ?? 'A1',
      modes: ['flashcards'],
      hasCloze: false,
      clozeIds: [],
      newOrder: index,
    })),
  };
}

function selectionHistory(selection: PracticeSelection): SelectionHistoryItem {
  return {
    itemId: selection.itemId,
    lemmaId: selection.lemma.lemmaId,
    mode: selection.mode,
    clozeId: selection.cloze?.clozeId,
    sentenceFrameId: selection.cloze?.sentenceFrameId,
    blankCase: selection.cloze?.blankCase,
    classifySetId: selection.classifySetId,
    recallDirection: selection.recallDirection,
    choicePolarity: selection.choicePolarity,
    lapsed: selection.lapsed,
  };
}

function newCardSequence(testDeck: PracticeDeckData, seed: number, count: number): PracticeSelection[] {
  const history: SelectionHistoryItem[] = [];
  const selections: PracticeSelection[] = [];
  for (let index = 0; index < count; index += 1) {
    const selection = selectNextPracticeItem(testDeck, {
      now: NOW,
      modeFilter: 'flashcards',
      history,
      sessionSeed: seed,
    });
    if (!selection) throw new Error(`expected selection ${index}`);
    selections.push(selection);
    history.push(selectionHistory(selection));
  }
  return selections;
}

function dailyIndex(ids: string[], cefr = 'A1'): PracticeIndexItem[] {
  return ids.map((id, index) => ({
    lemmaId: id,
    lemma: id,
    cefr,
    modes: ['flashcards', 'matching'],
    hasCloze: false,
    clozeIds: [],
    newOrder: index,
  }));
}

function makeCards(records: Record<string, Partial<CardState>>): Map<string, CardState> {
  const map = new Map<string, CardState>();
  for (const [key, overrides] of Object.entries(records)) {
    map.set(key, stateCard(overrides));
  }
  return map;
}

function review(
  lemmaId: string,
  rating: ReviewLogEntry['rating'],
  reviewedAt: number,
  mode: PracticeMode = 'flashcards',
): ReviewLogEntry {
  return {
    cardKey: cardKey(lemmaId, mode),
    lemmaId,
    mode,
    rating,
    state: State.Review,
    due: reviewedAt + DAY_MS,
    stability: 5,
    difficulty: 4,
    elapsed_days: 1,
    last_elapsed_days: 1,
    scheduled_days: 1,
    learning_steps: 0,
    review: reviewedAt,
  };
}

beforeEach(() => {
  localStorage.clear();
  loadState(localStorage, NOW);
});

describe('lexicon SRS facade', () => {
  test('parses legacy no-separator card keys as flashcards', () => {
    expect(parseCardKey('alpha')).toEqual({
      lemmaId: 'alpha',
      mode: 'flashcards',
      quarantined: false,
    });
  });

  test('parses known card-key modes and schedules backed wave-1 drills', () => {
    for (const mode of PRACTICE_MODES) {
      expect(isPracticeMode(mode)).toBe(true);
      expect(parseCardKey(`alpha::${mode}`)).toEqual({
        lemmaId: 'alpha',
        mode,
        quarantined: false,
      });
    }

    for (const mode of ['paradigm', 'stress', 'classify', 'synonym', 'heritage'] as const) {
      const selection = selectNextPracticeItem(modeDeck([{ id: `${mode}-alpha`, modes: [mode] }]), {
        now: NOW,
      });
      expect(selection?.mode).toBe(mode);
    }
    expect(selectNextPracticeItem(modeDeck([{ id: 'paronym-alpha', modes: ['paronym'] }]), { now: NOW })).toBeNull();
  });

  test('emits heritage candidates from published items in mixed and focus modes', () => {
    const testDeck = modeDeck([{ id: 'heritage-alpha', modes: ['heritage'] }]);

    const mixed = selectNextPracticeItem(testDeck, { now: NOW, modeFilter: 'mixed' });
    const focused = selectNextPracticeItem(testDeck, { now: NOW, modeFilter: 'heritage' });

    expect(mixed?.mode).toBe('heritage');
    expect(mixed?.heritage?.heritageId).toBe('heritage-alpha:heritage:1');
    expect(mixed?.cardKey).toBe(cardKey('heritage-alpha', 'heritage'));
    expect(focused?.mode).toBe('heritage');
    expect(focused?.heritage?.heritageId).toBe('heritage-alpha:heritage:1');
    expect(focused?.cardKey).toBe(cardKey('heritage-alpha', 'heritage'));
  });

  test('classify rotates outcome sets while keeping one SRS card key', () => {
    const testDeck = modeDeck([{ id: 'classify-alpha', modes: ['classify'] }]);
    const first = selectNextPracticeItem(testDeck, { now: NOW, modeFilter: 'classify' });

    if (!first) throw new Error('expected classify selection');
    expect(first?.mode).toBe('classify');
    expect(first?.cardKey).toBe(cardKey('classify-alpha', 'classify'));
    expect(first?.classifySetId).toBe('gender');

    const history: SelectionHistoryItem[] = [
      {
        itemId: first.itemId,
        lemmaId: first.lemma.lemmaId,
        mode: first.mode,
        classifySetId: first.classifySetId,
      },
    ];
    const rotated = selectNextPracticeItem(testDeck, { now: NOW, modeFilter: 'classify', history });

    expect(rotated?.cardKey).toBe(first.cardKey);
    expect(rotated?.classifySetId).toBe('pos');
  });

  test('quarantines explicit unknown card-key modes without rewriting stored state', () => {
    const listeningCard = stateCard({ due: NOW.getTime() - HOUR_MS, stability: 99 });
    const garbageCard = stateCard({ due: NOW.getTime() - DAY_MS, stability: 88 });
    const raw = JSON.stringify({
      version: 3,
      cards: {
        'alpha::listening': listeningCard,
        'beta::garbage': garbageCard,
      },
      reviews: [],
      lastSavedAt: NOW.getTime(),
    });
    localStorage.setItem(SRS_STORAGE_KEY, raw);

    const state = loadState(localStorage, NOW);

    expect(parseCardKey('alpha::listening')).toEqual({
      lemmaId: 'alpha',
      mode: null,
      rawMode: 'listening',
      quarantined: true,
    });
    expect(parseCardKey('beta::garbage')).toEqual({
      lemmaId: 'beta',
      mode: null,
      rawMode: 'garbage',
      quarantined: true,
    });
    expect([...state.cards.keys()]).toEqual(['alpha::listening', 'beta::garbage']);
    expect(
      selectNextPracticeItem(modeDeck([{ id: 'alpha', modes: ['listening' as PracticeMode] }]), {
        now: NOW,
      }),
    ).toBeNull();

    expect(saveState(state, localStorage, NOW.getTime())).toEqual({ ok: true });
    const saved = JSON.parse(localStorage.getItem(SRS_STORAGE_KEY) ?? '{}');
    expect(saved.cards['alpha::listening']).toEqual(listeningCard);
    expect(saved.cards['beta::garbage']).toEqual(garbageCard);
  });

  test('stability counters and selector debt skip quarantined unknown-mode cards', () => {
    const state = loadState(localStorage, NOW);
    state.cards.set('alpha::garbage', stateCard({ stability: 99, due: NOW.getTime() - DAY_MS }));
    state.cards.set('beta::listening', stateCard({ stability: 99, due: NOW.getTime() - DAY_MS }));
    state.cards.set(
      cardKey('gamma', 'choice'),
      stateCard({ stability: 5, due: NOW.getTime() - HOUR_MS }),
    );

    expect(masteredCount(21)).toBe(0);
    expect(masteredCount(21, 'choice')).toBe(0);

    const selection = selectNextPracticeItem(
      modeDeck([
        { id: 'alpha', modes: ['garbage' as PracticeMode] },
        { id: 'gamma', modes: ['choice'] },
      ]),
      {
        now: NOW,
        history: [
          { itemId: 'choice-1', lemmaId: 'choice-1', mode: 'choice' },
          { itemId: 'choice-2', lemmaId: 'choice-2', mode: 'choice' },
        ],
      },
    );

    expect(selection?.lemma.lemmaId).toBe('gamma');
    expect(selection?.mode).toBe('choice');
  });

  test('practice mode set is coupled to the deck-version sentinel', () => {
    const versionByModeSet: Record<string, number> = {
      'flashcards|matching|choice|cloze|paradigm|stress|heritage|synonym|classify|paronym': 3,
    };

    expect(versionByModeSet[PRACTICE_MODES.join('|')]).toBe(PRACTICE_MODE_DECK_VERSION);
  });

  test('schedules deterministically with FSRS defaults', () => {
    const first = rateCard('alpha', 'good', NOW);
    localStorage.clear();
    loadState(localStorage, NOW);
    const second = rateCard('alpha', 'good', NOW);

    expect(second).toEqual(first);
    expect(first.reps).toBe(1);
    expect(first.due).toBe(new Date('2026-06-23T12:10:00.000Z').getTime());
  });

  test('keys cards by lemmaId and mode', () => {
    rateCard('alpha', 'choice', 'easy', NOW);
    const state = loadState(localStorage, NOW);

    expect(state.cards.has(cardKey('alpha', 'choice'))).toBe(true);
    expect(state.cards.has(cardKey('alpha', 'flashcards'))).toBe(false);
    expect(state.reviews[0]).toMatchObject({
      lemmaId: 'alpha',
      mode: 'choice',
      cardKey: cardKey('alpha', 'choice'),
    });
  });

  test('migrates legacy storage into flashcard card keys and writes backup', () => {
    const oldRaw = JSON.stringify({
      version: 1,
      cards: {
        alpha: {
          due: '2026-06-24T12:00:00.000Z',
          stability: 12,
          difficulty: 4,
          elapsed_days: 0,
          scheduled_days: 1,
          learning_steps: 2,
          lapses: 0,
          state: 2,
        },
      },
      reviews: [],
    });
    localStorage.setItem(SRS_STORAGE_KEY, oldRaw);

    const state = loadState(localStorage, NOW);

    expect(state.flags.migrated).toBe(true);
    expect(state.flags.backupWritten).toBe(true);
    expect(localStorage.getItem(SRS_BACKUP_KEY)).toBe(oldRaw);
    expect(state.cards.get(cardKey('alpha', 'flashcards'))?.due).toBe(
      new Date('2026-06-24T12:00:00.000Z').getTime(),
    );
  });

  test('backs up existing raw state before save overwrites', () => {
    rateCard('alpha', 'good', NOW);
    const before = localStorage.getItem(SRS_STORAGE_KEY);

    rateCard('alpha', 'hard', new Date('2026-06-23T12:10:00.000Z'));

    expect(localStorage.getItem(SRS_BACKUP_KEY)).toBe(before);
  });

  test('writes the primary state before the best-effort backup', () => {
    const storage = new SizeLimitedStorage(Number.MAX_SAFE_INTEGER);
    loadState(storage, NOW);
    rateCard('alpha', 'good', NOW);
    storage.writes.length = 0;

    rateCard('alpha', 'hard', new Date('2026-06-23T12:10:00.000Z'));

    expect(storage.writes.indexOf(SRS_STORAGE_KEY)).toBeLessThan(
      storage.writes.indexOf(SRS_BACKUP_KEY),
    );
  });

  test('keeps a successful primary state when the backup write fails', () => {
    const storage = new BackupFailingStorage(Number.MAX_SAFE_INTEGER);
    const state = loadState(storage, NOW);
    rateCard('alpha', 'good', NOW);

    rateCard('alpha', 'hard', new Date('2026-06-23T12:10:00.000Z'));

    const persisted = JSON.parse(storage.getItem(SRS_STORAGE_KEY) ?? '{}');
    expect(persisted.cards[cardKey('alpha', 'flashcards')].reps).toBe(2);
    expect(state.flags.backupWritten).toBe(false);
    expect(state.flags.storageWriteFailed).toBe(false);
  });

  test('recovers a rating by dropping the backup when it is the quota blocker', () => {
    const seedStorage = new SizeLimitedStorage(Number.MAX_SAFE_INTEGER);
    loadState(seedStorage, NOW);
    rateCard('alpha', 'good', NOW);
    const previousRaw = seedStorage.getItem(SRS_STORAGE_KEY);
    const settingsRaw = seedStorage.getItem(SRS_SETTINGS_KEY);
    if (!previousRaw) throw new Error('expected seeded SRS state');

    const probeStorage = new SizeLimitedStorage(Number.MAX_SAFE_INTEGER, {
      [SRS_STORAGE_KEY]: previousRaw,
      ...(settingsRaw ? { [SRS_SETTINGS_KEY]: settingsRaw } : {}),
    });
    loadState(probeStorage, NOW);
    rateCard('alpha', 'hard', new Date('2026-06-23T12:10:00.000Z'));
    const nextRaw = probeStorage.getItem(SRS_STORAGE_KEY);
    const nextSettingsRaw = probeStorage.getItem(SRS_SETTINGS_KEY);
    if (!nextRaw || !nextSettingsRaw) throw new Error('expected next persisted SRS state');

    const storage = new SizeLimitedStorage(nextRaw.length + nextSettingsRaw.length + 1, {
      [SRS_STORAGE_KEY]: previousRaw,
      [SRS_BACKUP_KEY]: previousRaw,
      [SRS_SETTINGS_KEY]: nextSettingsRaw,
    });
    loadState(storage, NOW);

    rateCard('alpha', 'hard', new Date('2026-06-23T12:10:00.000Z'));

    const persisted = JSON.parse(storage.getItem(SRS_STORAGE_KEY) ?? '{}');
    expect(persisted.cards[cardKey('alpha', 'flashcards')].reps).toBe(2);
    expect(storage.removals).toContain(SRS_BACKUP_KEY);
    expect(loadState(storage, NOW).flags.storageFull).toBe(false);
  });

  test('keeps the rating in memory and exposes a storage-full state after exhausted recovery', () => {
    const storage = new SizeLimitedStorage(1);
    loadState(storage, NOW);

    const card = rateCard('alpha', 'good', NOW);
    const state = loadState(storage, NOW);

    expect(state.cards.get(cardKey('alpha', 'flashcards'))).toEqual(card);
    expect(state.flags.storageFull).toBe(true);
  });

  test('migrates and compacts oversized review history without changing card schedules', () => {
    const cards = {
      [cardKey('alpha', 'flashcards')]: stateCard({ due: NOW.getTime() + DAY_MS, stability: 12 }),
      [cardKey('beta', 'choice')]: stateCard({ due: NOW.getTime() + 2 * DAY_MS, stability: 24 }),
    };
    const reviews = Array.from({ length: MAX_RAW_REVIEW_LOG_ENTRIES + 3 }, (_unused, index) =>
      reviewEntry(index, index % 2 === 0 ? 'alpha' : 'beta'),
    );
    const oldRaw = JSON.stringify({
      version: 3,
      cards,
      reviews,
      lastSavedAt: NOW.getTime(),
    });
    const storage = new SizeLimitedStorage(Number.MAX_SAFE_INTEGER, { [SRS_STORAGE_KEY]: oldRaw });

    const state = loadState(storage, NOW);
    const saved = JSON.parse(storage.getItem(SRS_STORAGE_KEY) ?? '{}');

    expect(state.flags.migrated).toBe(true);
    expect(JSON.stringify(saved.cards)).toBe(JSON.stringify(cards));
    expect(saved.reviews).toEqual(reviews.slice(-MAX_RAW_REVIEW_LOG_ENTRIES));
    expect(saved.reviewAggregates[cardKey('alpha', 'flashcards')]).toEqual({
      ratings: { again: 0, hard: 0, good: 2, easy: 0 },
      firstReview: reviews[0].review,
      lastReview: reviews[2].review,
    });
    expect(saved.reviewAggregates[cardKey('beta', 'flashcards')]).toEqual({
      ratings: { again: 1, hard: 0, good: 0, easy: 0 },
      firstReview: reviews[1].review,
      lastReview: reviews[1].review,
    });
  });

  test('bounds persisted review-state size across simulated long-term sessions', () => {
    const sessions = MAX_RAW_REVIEW_LOG_ENTRIES * 3;
    const reviews = Array.from({ length: sessions }, (_unused, index) =>
      reviewEntry(index, `card-${index % 4}`),
    );
    const oldRaw = JSON.stringify({ version: 3, cards: {}, reviews, lastSavedAt: NOW.getTime() });
    const storage = new SizeLimitedStorage(Number.MAX_SAFE_INTEGER, { [SRS_STORAGE_KEY]: oldRaw });

    const state = loadState(storage, NOW);
    const savedRaw = storage.getItem(SRS_STORAGE_KEY) ?? '';
    const aggregatedCount = Object.values(state.reviewAggregates).reduce(
      (total, aggregate) => total + Object.values(aggregate.ratings).reduce((sum, count) => sum + count, 0),
      0,
    );

    expect(state.reviews).toHaveLength(MAX_RAW_REVIEW_LOG_ENTRIES);
    expect(aggregatedCount).toBe(sessions - MAX_RAW_REVIEW_LOG_ENTRIES);
    expect(savedRaw.length).toBeLessThan(oldRaw.length / 2);
  });

  test('keeps corrupt storage and surfaces fallback flag', () => {
    localStorage.setItem(SRS_STORAGE_KEY, '{not json');

    const state = loadState(localStorage, NOW);
    const result = saveState(state, localStorage, NOW.getTime());

    expect(state.flags.corrupt).toBe(true);
    expect(result.ok).toBe(false);
    expect(localStorage.getItem(SRS_STORAGE_KEY)).toBe('{not json');
  });

  test('detects clock jumps beyond seven days', () => {
    expect(detectClockJump(NOW, new Date('2026-07-02T12:00:00.000Z'))).toEqual({
      direction: 'forward',
      deltaDays: 9,
    });
    expect(detectClockJump(NOW, new Date('2026-06-25T12:00:00.000Z'))).toBeNull();
  });

  test('due queue includes new cards and excludes future reviews per mode', () => {
    const entries = deck(['alpha', 'beta']);

    rateCard('alpha', 'flashcards', 'good', NOW);

    expect(getDueQueue(entries, NOW).map((entry) => entry.lemmaId)).toEqual(['beta']);
  });

  test('counts mastered cards for the requested mode', () => {
    const state = loadState(localStorage, NOW);
    state.cards.set(cardKey('alpha', 'flashcards'), stateCard({ stability: 30 }));
    state.cards.set(cardKey('alpha', 'choice'), stateCard({ stability: 30 }));
    state.cards.set(cardKey('beta', 'flashcards'), stateCard({ stability: 5 }));

    expect(masteredCount(21)).toBe(1);
    expect(masteredCount(21, 'choice')).toBe(1);
  });

  test('selector keeps lapsed cards ahead of hard variety drops', () => {
    const state = loadState(localStorage, NOW);
    state.cards.set(cardKey('alpha', 'choice'), stateCard({ lapses: 1, due: NOW.getTime() - 1000 }));
    const selection = selectNextPracticeItem(practiceDeck(), {
      now: NOW,
      modeFilter: 'choice',
      history: [
        {
          itemId: 'alpha:choice',
          lemmaId: 'alpha',
          mode: 'choice',
        },
      ],
    });

    expect(selection?.lemma.lemmaId).toBe('alpha');
    expect(selection?.lapsed).toBe(true);
  });

  test('selector applies soft variety across realistic due-time spread', () => {
    const state = loadState(localStorage, NOW);
    state.cards.set(cardKey('alpha', 'flashcards'), stateCard({ due: NOW.getTime() - 45 * 60 * 1000 }));
    state.cards.set(cardKey('beta', 'choice'), stateCard({ due: NOW.getTime() - 5 * 60 * 1000 }));
    const history: SelectionHistoryItem[] = [
      { itemId: 'old-flash-1', lemmaId: 'old-1', mode: 'flashcards' },
      { itemId: 'old-flash-2', lemmaId: 'old-2', mode: 'flashcards' },
      { itemId: 'old-flash-3', lemmaId: 'old-3', mode: 'flashcards' },
    ];

    const selection = selectNextPracticeItem(modeDeck([
      { id: 'alpha', modes: ['flashcards'] },
      { id: 'beta', modes: ['choice'] },
    ]), {
      now: NOW,
      history,
    });

    expect(selection?.mode).toBe('choice');
    expect(selection?.lemma.lemmaId).toBe('beta');
  });

  test('soft variety never overtakes a genuinely more-due card (no penalty leak across urgency buckets)', () => {
    const state = loadState(localStorage, NOW);
    // alpha is ~10h more overdue but in the recently-spammed mode (max variety penalty);
    // beta is only just due in a fresh mode. The more-due card MUST still win — the soft
    // penalty (tens) must never overtake hours of real urgency.
    state.cards.set(cardKey('alpha', 'flashcards'), stateCard({ due: NOW.getTime() - 10 * HOUR_MS }));
    state.cards.set(cardKey('beta', 'choice'), stateCard({ due: NOW.getTime() }));
    const history: SelectionHistoryItem[] = [
      { itemId: 'h1', lemmaId: 'h1', mode: 'flashcards' },
      { itemId: 'h2', lemmaId: 'h2', mode: 'flashcards' },
      { itemId: 'h3', lemmaId: 'h3', mode: 'flashcards' },
    ];

    const selection = selectNextPracticeItem(modeDeck([
      { id: 'alpha', modes: ['flashcards'] },
      { id: 'beta', modes: ['choice'] },
    ]), {
      now: NOW,
      history,
    });

    expect(selection?.lemma.lemmaId).toBe('alpha');
  });

  test('selector never borrows not-due cards while overdue cards exist', () => {
    const state = loadState(localStorage, NOW);
    state.cards.set(cardKey('alpha', 'flashcards'), stateCard({ due: NOW.getTime() - HOUR_MS }));
    state.cards.set(cardKey('beta', 'choice'), stateCard({ due: NOW.getTime() + DAY_MS }));

    const selection = selectNextPracticeItem(modeDeck([
      { id: 'alpha', modes: ['flashcards'] },
      { id: 'beta', modes: ['choice'] },
    ]), {
      now: NOW,
      history: [
        { itemId: 'choice-1', lemmaId: 'x1', mode: 'choice' },
        { itemId: 'choice-2', lemmaId: 'x2', mode: 'choice' },
        { itemId: 'choice-3', lemmaId: 'x3', mode: 'choice' },
      ],
    });

    expect(selection?.lemma.lemmaId).toBe('alpha');
    expect(selection?.due).toBeLessThanOrEqual(NOW.getTime());
  });

  test('selector widens the due window before borrowing farther not-due cards', () => {
    const state = loadState(localStorage, NOW);
    state.cards.set(cardKey('alpha', 'flashcards'), stateCard({ due: NOW.getTime() + 2 * HOUR_MS }));
    state.cards.set(cardKey('beta', 'flashcards'), stateCard({ due: NOW.getTime() + 2 * DAY_MS }));

    const selection = selectNextPracticeItem(modeDeck([
      { id: 'alpha', modes: ['flashcards'] },
      { id: 'beta', modes: ['flashcards'] },
    ]), {
      now: NOW,
      history: [{ itemId: 'recent-alpha', lemmaId: 'alpha', mode: 'flashcards' }],
    });

    expect(selection?.lemma.lemmaId).toBe('alpha');
  });

  test('selector mode debt surfaces a starved due mode', () => {
    const state = loadState(localStorage, NOW);
    state.cards.set(cardKey('alpha', 'flashcards'), stateCard({ due: NOW.getTime() - 10 * 60 * 1000 }));
    state.cards.set(cardKey('beta', 'choice'), stateCard({ due: NOW.getTime() - 10 * 60 * 1000 }));
    state.cards.set(cardKey('gamma', 'matching'), stateCard({ due: NOW.getTime() - 10 * 60 * 1000 }));

    const history: SelectionHistoryItem[] = [
      { itemId: 'f1', lemmaId: 'f1', mode: 'flashcards' },
      { itemId: 'f2', lemmaId: 'f2', mode: 'flashcards' },
      { itemId: 'c1', lemmaId: 'c1', mode: 'choice' },
      { itemId: 'c2', lemmaId: 'c2', mode: 'choice' },
    ];
    const selection = selectNextPracticeItem(modeDeck([
      { id: 'alpha', modes: ['flashcards'] },
      { id: 'beta', modes: ['choice'] },
      { id: 'gamma', modes: ['matching'] },
    ]), {
      now: NOW,
      history,
    });

    expect(selection?.mode).toBe('matching');
  });

  test('selector uses the session seed only as a stable tied-new-card tiebreak', () => {
    const testDeck = flashcardDeck(
      Array.from({ length: 30 }, (_, index) => ({ id: `seeded-${String(index).padStart(2, '0')}` })),
    );

    const firstRun = newCardSequence(testDeck, 12345, 10).map((selection) => selection.itemId);
    const secondRun = newCardSequence(testDeck, 12345, 10).map((selection) => selection.itemId);
    const differentSeedRun = newCardSequence(testDeck, 54321, 10).map((selection) => selection.itemId);

    expect(secondRun).toEqual(firstRun);
    expect(differentSeedRun).not.toEqual(firstRun);
  });

  test('selector returns immutable snapshots of cached candidates', () => {
    const testDeck = flashcardDeck([{ id: 'snapshot' }]);
    const first = selectNextPracticeItem(testDeck, {
      now: NOW,
      modeFilter: 'flashcards',
      sessionSeed: 12345,
    });
    if (!first) throw new Error('expected first selection');
    const firstPolarity = first.choicePolarity;

    selectNextPracticeItem(testDeck, {
      now: NOW,
      modeFilter: 'flashcards',
      history: [selectionHistory(first)],
      sessionSeed: 12345,
    });

    expect(first.choicePolarity).toBe(firstPolarity);
  });

  test('due and lapsed cards beat tied new cards regardless of seed', () => {
    const state = loadState(localStorage, NOW);
    state.cards.set(cardKey('due-review', 'flashcards'), stateCard({ due: NOW.getTime() }));
    const testDeck = flashcardDeck([
      { id: 'fresh-a' },
      { id: 'fresh-b' },
      { id: 'due-review' },
      { id: 'fresh-c' },
    ]);

    for (const seed of [1, 987654321]) {
      const selection = selectNextPracticeItem(testDeck, {
        now: NOW,
        modeFilter: 'flashcards',
        sessionSeed: seed,
      });
      expect(selection?.lemma.lemmaId).toBe('due-review');
      expect(selection?.cardState).toBeTruthy();
    }

    state.cards.set(cardKey('lapsed-review', 'flashcards'), stateCard({ lapses: 1, due: NOW.getTime() - HOUR_MS }));
    const lapsedDeck = flashcardDeck([
      { id: 'fresh-a' },
      { id: 'lapsed-review' },
      { id: 'fresh-b' },
    ]);
    for (const seed of [1, 987654321]) {
      const selection = selectNextPracticeItem(lapsedDeck, {
        now: NOW,
        modeFilter: 'flashcards',
        sessionSeed: seed,
      });
      expect(selection?.lemma.lemmaId).toBe('lapsed-review');
      expect(selection?.lapsed).toBe(true);
    }
  });

  test('B1 decks introduce B1 new cards before same-urgency lower-level cards', () => {
    const testDeck = flashcardDeck(
      [
        ...Array.from({ length: 10 }, (_, index) => ({ id: `a1-${index}`, cefr: 'A1' })),
        ...Array.from({ length: 10 }, (_, index) => ({ id: `a2-${index}`, cefr: 'A2' })),
        ...Array.from({ length: 10 }, (_, index) => ({ id: `b1-${index}`, cefr: 'B1' })),
      ],
      'B1',
    );

    const firstIntroductions = newCardSequence(testDeck, 20260706, 8);

    expect(firstIntroductions.map((selection) => selection.indexItem.cefr)).toEqual(
      Array.from({ length: 8 }, () => 'B1'),
    );
  });

  test('seeded answer placement varies correct-answer positions across a session', () => {
    const positions = new Set(
      Array.from({ length: 20 }, (_, index) =>
        seededAnswerIndex(20260706, `choice-fixture-${index}:choice`, 4),
      ),
    );

    expect(positions.size).toBeGreaterThanOrEqual(3);
    expect(seededAnswerIndex(111, 'choice-fixture-0:choice', 4)).not.toBe(
      seededAnswerIndex(222, 'choice-fixture-0:choice', 4),
    );
  });

  test('selector handles a warmed 18k-candidate transition under the perf budget', () => {
    const testDeck = flashcardDeck(
      Array.from({ length: 18_000 }, (_, index) => ({
        id: `bench-${String(index).padStart(5, '0')}`,
      })),
      'A1',
      'bench-optimized',
    );
    const history: SelectionHistoryItem[] = [
      { itemId: 'history-choice-1', lemmaId: 'history-choice-1', mode: 'choice' },
      { itemId: 'history-choice-2', lemmaId: 'history-choice-2', mode: 'choice' },
    ];

    selectNextPracticeItem(testDeck, { now: NOW, modeFilter: 'flashcards', sessionSeed: 123456789 });
    const start = performance.now();
    const selection = selectNextPracticeItem(testDeck, {
      now: NOW,
      modeFilter: 'flashcards',
      history,
      sessionSeed: 123456789,
    });
    const elapsed = performance.now() - start;

    console.info(
      `BENCH optimized selectNextPracticeItem 18000 candidates: ${elapsed.toFixed(2)}ms selected=${
        selection?.itemId ?? 'null'
      }`,
    );
    expect(selection).not.toBeNull();
    expect(elapsed).toBeLessThan(50);
  });

  test('explicit cloze mode reaches authored cloze before recognition mastery', () => {
    const selection = selectNextPracticeItem(practiceDeck(), {
      now: NOW,
      modeFilter: 'cloze',
    });

    expect(selection?.mode).toBe('cloze');
    expect(['alpha-cloze', 'beta-cloze', 'gamma-cloze']).toContain(selection?.cloze?.clozeId);
  });

  test('cloze soft cap yields to lapsed cloze pressure', () => {
    const state = loadState(localStorage, NOW);
    state.cards.set(cardKey('alpha', 'flashcards'), stateCard({ stability: 6 }));
    state.cards.set(cardKey('alpha', 'cloze'), stateCard({ lapses: 1, due: NOW.getTime() - DAY_MS }));
    const clozeHeavyHistory: SelectionHistoryItem[] = Array.from({ length: 8 }, (_, index) => ({
      itemId: `old-${index}`,
      lemmaId: 'alpha',
      mode: 'cloze',
    }));

    const selection = selectNextPracticeItem(practiceDeck(), {
      now: NOW,
      history: clozeHeavyHistory,
    });

    expect(selection?.mode).toBe('cloze');
    expect(selection?.lapsed).toBe(true);
  });

  test('cloze soft cap exempts overdue non-lapsed cloze', () => {
    const state = loadState(localStorage, NOW);
    state.cards.set(cardKey('alpha', 'flashcards'), stateCard({ stability: 6, due: NOW.getTime() + DAY_MS }));
    state.cards.set(cardKey('alpha', 'cloze'), stateCard({ due: NOW.getTime() - HOUR_MS, lapses: 0 }));
    state.cards.set(cardKey('beta', 'choice'), stateCard({ due: NOW.getTime() }));
    const baseDeck = practiceDeck();
    const testDeck: PracticeDeckData = {
      ...baseDeck,
      lexemes: baseDeck.lexemes.slice(0, 2),
      cloze: [baseDeck.cloze[0]],
      index: [
        { ...baseDeck.index[0], modes: ['cloze'], clozeIds: [baseDeck.cloze[0].clozeId], hasCloze: true },
        { ...baseDeck.index[1], modes: ['choice'], clozeIds: [], hasCloze: false },
      ],
    };
    const clozeHeavyHistory: SelectionHistoryItem[] = [
      ...Array.from({ length: 4 }, (_, index) => ({
        itemId: `old-cloze-${index}`,
        lemmaId: `old-cloze-${index}`,
        mode: 'cloze' as const,
      })),
      ...Array.from({ length: 4 }, (_, index) => ({
        itemId: `old-choice-${index}`,
        lemmaId: `old-choice-${index}`,
        mode: 'choice' as const,
      })),
    ];

    const selection = selectNextPracticeItem(testDeck, {
      now: NOW,
      history: clozeHeavyHistory,
    });

    expect(selection?.mode).toBe('cloze');
    expect(selection?.lapsed).toBe(false);
  });

  test('validates cloze option sets and Ukrainian plural forms', () => {
    expect(validateClozeOptions(cloze('alpha', 'alpha-cloze', 'accusative', 'alphaу'))).toEqual([]);
    expect(uaPlural(0)).toBe('правильних');
    expect(uaPlural(1)).toBe('правильна');
    expect(uaPlural(2)).toBe('правильні');
    expect(uaPlural(5)).toBe('правильних');
    expect(uaPlural(11)).toBe('правильних');
    expect(uaPlural(21)).toBe('правильна');
  });
});

describe('daily practice deck (K3 chunk 1)', () => {
  test('selects exactly 20 unique lemmas when enough data exists', () => {
    const ids = Array.from({ length: 30 }, (_, index) => `w${String(index).padStart(2, '0')}`);
    const index = dailyIndex(ids);
    const cards = makeCards({});
    const items = selectDailyPracticeDeckItems(index, cards, NOW);
    expect(items).toHaveLength(DAILY_PRACTICE_DECK_SIZE);
    const uniqueIds = new Set(items.map((item) => item.lemmaId));
    expect(uniqueIds.size).toBe(DAILY_PRACTICE_DECK_SIZE);
  });

  test('orders due before new and applies deterministic tie-breakers', () => {
    const index = dailyIndex(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']);
    const cards = makeCards({
      [cardKey('a', 'flashcards')]: { due: NOW.getTime() - 2 * HOUR_MS, reps: 1, state: State.Review },
      [cardKey('c', 'flashcards')]: { due: NOW.getTime() - HOUR_MS, reps: 1, state: State.Review },
      [cardKey('b', 'flashcards')]: { due: NOW.getTime() + HOUR_MS, reps: 1, state: State.Review },
    });
    const items = selectDailyPracticeDeckItems(index, cards, NOW);
    const ids = items.map((item) => item.lemmaId);
    expect(ids.slice(0, 2)).toEqual(['a', 'c']);
    expect(items[0]?.origin).toBe('due');
    expect(items[1]?.origin).toBe('due');
    // 'b' is reviewed but not due, so it is not eligible.
    expect(ids).not.toContain('b');
    for (const item of items.slice(2)) {
      expect(item.origin).toBe('new');
    }
  });

  test('multiple due modes for one lemma consume one daily slot', () => {
    const index = dailyIndex(['only']);
    const cards = makeCards({
      [cardKey('only', 'flashcards')]: { due: NOW.getTime() - HOUR_MS, reps: 1, state: State.Review },
      [cardKey('only', 'matching')]: { due: NOW.getTime() - 2 * HOUR_MS, reps: 1, state: State.Review },
    });
    const items = selectDailyPracticeDeckItems(index, cards, NOW);
    expect(items).toHaveLength(1);
    expect(items[0]?.lemmaId).toBe('only');
    expect(items[0]?.origin).toBe('due');
  });

  test('reviewed-but-not-due lemmas do not displace due or new candidates', () => {
    const index = dailyIndex(['due-one', 'reviewed-future', 'new-one']);
    const cards = makeCards({
      [cardKey('due-one', 'flashcards')]: { due: NOW.getTime() - HOUR_MS, reps: 1, state: State.Review },
      [cardKey('reviewed-future', 'flashcards')]: { due: NOW.getTime() + DAY_MS, reps: 1, state: State.Review },
    });
    const items = selectDailyPracticeDeckItems(index, cards, NOW);
    const ids = items.map((item) => item.lemmaId);
    expect(ids).toEqual(['due-one', 'new-one']);
  });

  test('uses the actual eligible count as denominator when fewer than 20 lemmas exist', () => {
    const index = dailyIndex(['a', 'b', 'c']);
    const cards = makeCards({});
    const items = selectDailyPracticeDeckItems(index, cards, NOW);
    expect(items).toHaveLength(3);
    expect(new Set(items.map((item) => item.lemmaId)).size).toBe(3);
  });

  test('published levels stay A1 through C1 and C2 is not added', () => {
    expect(PUBLISHED_PRACTICE_LEVELS).toEqual(['A1', 'A2', 'B1', 'B2', 'C1']);
  });

  test('a valid snapshot is stable after SRS mutations and page reload', () => {
    const index = dailyIndex(['a', 'b', 'c', 'd']);
    const cards = makeCards({});
    const snapshot = buildDailyPracticeDeckSnapshot(index, cards, {
      level: 'A1',
      deckVersion: 'v1',
      date: '2026-06-23',
      now: NOW,
    });
    writeDailyPracticeDeckSnapshot(snapshot, localStorage);

    rateCard('a', 'flashcards', 'good', NOW);

    const restored = readDailyPracticeDeckSnapshot(localStorage, '2026-06-23', 'A1', 'v1');
    expect(restored).toEqual(snapshot);
    expect(localStorage.getItem(DAILY_PRACTICE_DECK_KEY)).toContain('v1');
  });

  test('invalidates snapshot on date, level, or deckVersion mismatch', () => {
    const index = dailyIndex(['a']);
    const cards = makeCards({});
    const snapshot = buildDailyPracticeDeckSnapshot(index, cards, {
      level: 'A1',
      deckVersion: 'v1',
      date: '2026-06-23',
      now: NOW,
    });
    writeDailyPracticeDeckSnapshot(snapshot, localStorage);

    expect(readDailyPracticeDeckSnapshot(localStorage, '2026-06-24', 'A1', 'v1')).toBeNull();
    expect(readDailyPracticeDeckSnapshot(localStorage, '2026-06-23', 'A2', 'v1')).toBeNull();
    expect(readDailyPracticeDeckSnapshot(localStorage, '2026-06-23', 'A1', 'v2')).toBeNull();
  });

  test('corrupt JSON falls back to null without blocking', () => {
    localStorage.setItem(DAILY_PRACTICE_DECK_KEY, '{not json');
    expect(readDailyPracticeDeckSnapshot(localStorage, '2026-06-23', 'A1', 'v1')).toBeNull();
  });

  test('refill drops missing IDs and deterministically replaces them', () => {
    const index = dailyIndex(['keep', 'fill-a', 'fill-b', 'fill-c']);
    const cards = makeCards({});
    const saved = buildDailyPracticeDeckSnapshot(index, cards, {
      level: 'A1',
      deckVersion: 'v1',
      date: '2026-06-23',
      now: NOW,
    });
    const tampered = {
      ...saved,
      items: [
        { lemmaId: 'keep', origin: 'due' as const },
        { lemmaId: 'missing', origin: 'new' as const },
        { lemmaId: 'missing', origin: 'new' as const },
      ],
    };
    const refilled = refillDailyPracticeDeckSnapshot(tampered, index, cards, {
      date: '2026-06-23',
      level: 'A1',
      deckVersion: 'v1',
      now: NOW,
    });
    const ids = refilled.items.map((item) => item.lemmaId);
    expect(ids[0]).toBe('keep');
    expect(ids).not.toContain('missing');
    expect(new Set(ids).size).toBe(ids.length);
    expect(ids.length).toBeLessThanOrEqual(DAILY_PRACTICE_DECK_SIZE);
    expect(ids).toContain('fill-a');
  });

  test('refill reuses valid IDs when deck version changes', () => {
    const index = dailyIndex(['keep', 'fill-a', 'fill-b']);
    const cards = makeCards({});
    const saved = buildDailyPracticeDeckSnapshot(index, cards, {
      level: 'A1',
      deckVersion: 'v1',
      date: '2026-06-23',
      now: NOW,
    });
    const refilled = refillDailyPracticeDeckSnapshot(saved, index, cards, {
      date: '2026-06-23',
      level: 'A1',
      deckVersion: 'v2',
      now: NOW,
    });
    expect(refilled.deckVersion).toBe('v2');
    expect(refilled.items.map((item) => item.lemmaId)[0]).toBe('keep');
  });

  test('again moves a completed lemma back to pending due; success moves it back to done', () => {
    const index = dailyIndex(['a']);
    const cards = makeCards({
      [cardKey('a', 'flashcards')]: { due: NOW.getTime() - HOUR_MS, reps: 1, state: State.Review },
    });
    const snapshot = buildDailyPracticeDeckSnapshot(index, cards, {
      level: 'A1',
      deckVersion: 'v1',
      date: '2026-06-23',
      now: NOW,
    });

    const t1 = NOW.getTime() + 1 * 60_000;
    const t2 = NOW.getTime() + 2 * 60_000;
    const t3 = NOW.getTime() + 3 * 60_000;

    const afterGood = deriveDailyPracticeRows(snapshot, cards, [review('a', 'good', t1)], NOW);
    expect(afterGood.done).toHaveLength(1);
    expect(afterGood.pendingDue).toHaveLength(0);

    const afterAgain = deriveDailyPracticeRows(
      snapshot,
      cards,
      [review('a', 'good', t1), review('a', 'again', t2)],
      NOW,
    );
    expect(afterAgain.done).toHaveLength(0);
    expect(afterAgain.pendingDue).toHaveLength(1);

    const afterSuccess = deriveDailyPracticeRows(
      snapshot,
      cards,
      [review('a', 'good', t1), review('a', 'again', t2), review('a', 'hard', t3)],
      NOW,
    );
    expect(afterSuccess.done).toHaveLength(1);
    expect(afterSuccess.pendingDue).toHaveLength(0);
    expect(countDailyPracticeDone(snapshot, [review('a', 'hard', t3)], NOW)).toBe(1);
  });

  test('deriveDailyPracticeRows groups done rows after pending due and pending new', () => {
    const index = dailyIndex(['due-one', 'new-one', 'done-one']);
    const cards = makeCards({
      [cardKey('due-one', 'flashcards')]: { due: NOW.getTime() - HOUR_MS, reps: 1, state: State.Review },
    });
    const snapshot = buildDailyPracticeDeckSnapshot(index, cards, {
      level: 'A1',
      deckVersion: 'v1',
      date: '2026-06-23',
      now: NOW,
    });
    const reviewedAt = NOW.getTime() + 60_000;
    const rows = deriveDailyPracticeRows(snapshot, cards, [review('done-one', 'good', reviewedAt)], NOW);
    expect(rows.pendingDue.map((row) => row.item.lemmaId)).toEqual(['due-one']);
    expect(rows.pendingNew.map((row) => row.item.lemmaId)).toEqual(['new-one']);
    expect(rows.done.map((row) => row.item.lemmaId)).toEqual(['done-one']);
  });
});
