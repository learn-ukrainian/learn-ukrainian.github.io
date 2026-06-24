import { beforeEach, describe, expect, test } from 'vitest';
import {
  SRS_BACKUP_KEY,
  SRS_STORAGE_KEY,
  cardKey,
  detectClockJump,
  getDueQueue,
  loadState,
  masteredCount,
  rateCard,
  saveState,
  selectNextPracticeItem,
  uaPlural,
  validateClozeOptions,
  type PracticeClozeItem,
  type PracticeDeckData,
  type PracticeLexeme,
  type PracticeMode,
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

function lexeme(lemmaId: string, lemma = lemmaId, gloss = `${lemmaId} gloss`): PracticeLexeme {
  return {
    lemmaId,
    lemma,
    lemmaPlain: lemma,
    gloss,
    ipa: null,
    pos: 'noun',
    cefr: 'A1',
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

function historyFromSelection(selection: NonNullable<ReturnType<typeof selectNextPracticeItem>>) {
  return {
    itemId: selection.itemId,
    lemmaId: selection.lemma.lemmaId,
    mode: selection.mode,
    clozeId: selection.cloze?.clozeId,
    sentenceFrameId: selection.cloze?.sentenceFrameId,
    blankCase: selection.cloze?.blankCase,
    recallDirection: selection.recallDirection,
    choicePolarity: selection.choicePolarity,
    lapsed: selection.lapsed,
  } satisfies SelectionHistoryItem;
}

beforeEach(() => {
  localStorage.clear();
  loadState(localStorage, NOW);
});

describe('lexicon SRS facade', () => {
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
