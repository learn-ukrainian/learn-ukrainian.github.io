import { beforeEach, describe, expect, test } from 'vitest';
import { Rating, fsrs, createEmptyCard } from 'ts-fsrs';
import {
  DEFAULT_NEW_PER_DAY,
  DEFAULT_NEW_PER_SESSION,
  PRACTICE_NEW_CARDS_KEY,
  PRACTICE_SESSION_STORAGE_KEY,
  SRS_STORAGE_KEY,
  buildSessionPoolConstraintState,
  cardKey,
  computeSessionScope,
  computeTodayRingDenominator,
  countAvailableNewCards,
  countDueReviewCards,
  formatFsrsIntervalUk,
  isPracticeNewCard,
  isPracticeSessionResumable,
  loadState,
  previewRatingIntervals,
  readNewCardsDailyState,
  readPracticeSessionSnapshot,
  resolveSessionCompletion,
  saveState,
  selectNextPracticeItem,
  sessionPoolAllowsCandidate,
  writeNewCardsDailyState,
  writePracticeSessionSnapshot,
  type PracticeDeckData,
  type PracticeIndexItem,
  type PracticeLexeme,
  type SelectionHistoryItem,
} from '@site/src/lib/lexicon/srs';

const NOW = new Date('2026-06-23T12:00:00.000Z');

function lexeme(lemmaId: string, lemma = lemmaId): PracticeLexeme {
  return {
    lemmaId,
    lemma,
    lemmaPlain: lemma,
    gloss: `${lemma} gloss`,
    ipa: null,
    pos: 'noun',
    cefr: 'A1',
    heritage: null,
    severity: null,
    paradigm: { cases: { nominative: { singular: lemma } } },
  };
}

function indexItem(lemmaId: string, order: number): PracticeIndexItem {
  return {
    lemmaId,
    lemma: lemmaId,
    cefr: 'A1',
    modes: ['flashcards'],
    hasCloze: false,
    clozeIds: [],
    newOrder: order,
  };
}

function deckFromIds(ids: string[]): PracticeDeckData {
  const lexemes = ids.map((id) => lexeme(id));
  return {
    deckVersion: 'session-test',
    level: 'A1',
    lexemes,
    cloze: [],
    index: ids.map((id, order) => indexItem(id, order)),
  };
}

function dueCard(lemmaId: string) {
  return {
    due: NOW.getTime() - 60_000,
    stability: 4,
    difficulty: 4,
    elapsed_days: 1,
    scheduled_days: 1,
    learning_steps: 0,
    reps: 2,
    lapses: 0,
    state: 2,
  };
}

beforeEach(() => {
  localStorage.clear();
  loadState(localStorage, NOW);
});

describe('practice session helpers', () => {
  test('today-ring denominator excludes uncapped deck size', () => {
    const index = Array.from({ length: 50 }, (_, i) => indexItem(`w${i}`, i));
    const denominator = computeTodayRingDenominator(index, {
      now: NOW,
      dailyNewCount: 0,
      newPerDay: DEFAULT_NEW_PER_DAY,
    });
    expect(denominator).toBe(DEFAULT_NEW_PER_DAY);
    expect(denominator).toBeLessThan(index.length);
  });

  test('session scope prioritizes reviews then caps new cards', () => {
    const index = Array.from({ length: 30 }, (_, i) => indexItem(`w${i}`, i));
    const state = loadState(localStorage, NOW);
    state.cards.set(cardKey('w0', 'flashcards'), dueCard('w0'));
    state.cards.set(cardKey('w1', 'flashcards'), dueCard('w1'));
    saveState(state, localStorage, NOW.getTime());
    const scope = computeSessionScope(index, 20, {
      now: NOW,
      newPerSession: DEFAULT_NEW_PER_SESSION,
      newPerDay: DEFAULT_NEW_PER_DAY,
      dailyNewCount: 0,
    });
    expect(scope.dueReviews).toBe(2);
    expect(scope.plannedNew).toBe(8);
    expect(scope.plannedTotal).toBe(10);
  });

  test('daily new allowance gates session scope', () => {
    const index = Array.from({ length: 10 }, (_, i) => indexItem(`w${i}`, i));
    const scope = computeSessionScope(index, 20, {
      now: NOW,
      dailyNewCount: 18,
      newPerDay: DEFAULT_NEW_PER_DAY,
    });
    expect(scope.plannedNew).toBe(2);
  });

  test('session pool blocks new cards until review quota is satisfied', () => {
    const candidate = {
      itemId: 'new-1',
      lemma: lexeme('new-1'),
      indexItem: indexItem('new-1', 0),
      mode: 'flashcards' as const,
      cardKey: cardKey('new-1', 'flashcards'),
      cardState: null,
      due: 0,
      lapsed: false,
      recallDirection: 'uk-to-meaning' as const,
      choicePolarity: 'word-to-meaning' as const,
    };
    const blocked = buildSessionPoolConstraintState({
      plannedReviews: 5,
      reviewsCompleted: 2,
      sessionNewIntroduced: 0,
      dailyNewCount: 0,
    });
    const allowed = buildSessionPoolConstraintState({
      plannedReviews: 5,
      reviewsCompleted: 5,
      sessionNewIntroduced: 0,
      dailyNewCount: 0,
    });
    expect(sessionPoolAllowsCandidate(candidate, blocked)).toBe(false);
    expect(sessionPoolAllowsCandidate(candidate, allowed)).toBe(true);
  });

  test('session pool enforces new-per-session and daily caps', () => {
    const candidate = {
      itemId: 'new-2',
      lemma: lexeme('new-2'),
      indexItem: indexItem('new-2', 1),
      mode: 'flashcards' as const,
      cardKey: cardKey('new-2', 'flashcards'),
      cardState: null,
      due: 0,
      lapsed: false,
      recallDirection: 'uk-to-meaning' as const,
      choicePolarity: 'word-to-meaning' as const,
    };
    const sessionCap = buildSessionPoolConstraintState({
      plannedReviews: 0,
      reviewsCompleted: 0,
      sessionNewIntroduced: DEFAULT_NEW_PER_SESSION,
      dailyNewCount: 0,
    });
    const dailyCap = buildSessionPoolConstraintState({
      plannedReviews: 0,
      reviewsCompleted: 0,
      sessionNewIntroduced: 0,
      dailyNewCount: DEFAULT_NEW_PER_DAY,
    });
    expect(sessionPoolAllowsCandidate(candidate, sessionCap)).toBe(false);
    expect(sessionPoolAllowsCandidate(candidate, dailyCap)).toBe(false);
  });

  test('pool filter leaves §6 ordering precedence intact for due reviews', () => {
    const state = loadState(localStorage, NOW);
    state.cards.set(cardKey('due-a', 'flashcards'), dueCard('due-a'));
    state.cards.set(cardKey('due-b', 'flashcards'), {
      ...dueCard('due-b'),
      due: NOW.getTime() - 120_000,
    });
    saveState(state, localStorage, NOW.getTime());
    const testDeck = deckFromIds(['due-a', 'due-b', 'fresh-c']);
    const constraints = buildSessionPoolConstraintState({
      plannedReviews: 2,
      reviewsCompleted: 0,
      sessionNewIntroduced: 0,
      dailyNewCount: 0,
    });
    const selection = selectNextPracticeItem(testDeck, {
      now: NOW,
      modeFilter: 'flashcards',
      poolFilter: (candidate) => sessionPoolAllowsCandidate(candidate, constraints),
    });
    expect(selection?.lemma.lemmaId).toBe('due-b');
  });

  test('snapshot round-trip restores seed history budget and recomputes live selection', () => {
    const testDeck = deckFromIds(['alpha', 'beta']);
    const history: SelectionHistoryItem[] = [
      { itemId: 'alpha:flashcards', lemmaId: 'alpha', mode: 'flashcards' },
    ];
    writePracticeSessionSnapshot('flashcards', {
      sessionSeed: 424242,
      history,
      budget: 10,
      completed: 1,
      modeFilter: 'flashcards',
      level: 'A1',
      startedAt: NOW.getTime(),
      plannedReviews: 2,
      plannedNew: 2,
      plannedTotal: 4,
      reviewsCompleted: 1,
      sessionNewIntroduced: 0,
      extensionUsed: 0,
      unresolvedCardKeys: [],
    });
    const snapshot = readPracticeSessionSnapshot('flashcards');
    expect(snapshot).toMatchObject({
      sessionSeed: 424242,
      history,
      budget: 10,
      completed: 1,
    });
    expect(isPracticeSessionResumable(snapshot, NOW)).toBe(true);
    const live = selectNextPracticeItem(testDeck, {
      now: NOW,
      modeFilter: 'flashcards',
      history: snapshot?.history ?? [],
      sessionSeed: snapshot?.sessionSeed,
    });
    expect(live?.lemma.lemmaId).toBeTruthy();
  });

  test('interval labels match ts-fsrs repeat preview output', () => {
    const previews = previewRatingIntervals('alpha', 'flashcards', NOW);
    const scheduler = fsrs(loadState(localStorage, NOW).settings.params);
    const records = scheduler.repeat(createEmptyCard(NOW), NOW);
    expect(previews.good).toBe(formatFsrsIntervalUk(NOW, records[Rating.Good].card.due));
    expect(previews.again).toBe(formatFsrsIntervalUk(NOW, records[Rating.Again].card.due));
  });

  test('formatFsrsIntervalUk uses minutes days and months buckets', () => {
    expect(formatFsrsIntervalUk(NOW, new Date(NOW.getTime() + 10 * 60_000))).toBe('10 хв');
    expect(formatFsrsIntervalUk(NOW, new Date(NOW.getTime() + 3 * 24 * 60 * 60_000))).toBe('3 д');
    expect(formatFsrsIntervalUk(NOW, new Date(NOW.getTime() + 90 * 24 * 60 * 60_000))).toBe('3 міс');
  });

  test('new cards daily state resets on a new day', () => {
    writeNewCardsDailyState({ date: '2026-06-22', count: 12 });
    expect(readNewCardsDailyState(localStorage, '2026-06-23').count).toBe(0);
    localStorage.setItem(
      PRACTICE_NEW_CARDS_KEY,
      JSON.stringify({ date: '2026-06-23', count: 4 }),
    );
    expect(readNewCardsDailyState(localStorage, '2026-06-23').count).toBe(4);
  });

  test('due and available counts distinguish reviews from new cards', () => {
    const index = [indexItem('review-me', 0), indexItem('brand-new', 1)];
    const state = loadState(localStorage, NOW);
    state.cards.set(cardKey('review-me', 'flashcards'), dueCard('review-me'));
    saveState(state, localStorage, NOW.getTime());
    expect(countDueReviewCards(index, NOW)).toBe(1);
    expect(countAvailableNewCards(index, NOW)).toBe(1);
    expect(isPracticeNewCard(null)).toBe(true);
  });

  test('expired snapshot is not resumable', () => {
    writePracticeSessionSnapshot('mixed', {
      sessionSeed: 1,
      history: [],
      budget: 10,
      completed: 2,
      modeFilter: 'mixed',
      level: 'A1',
      startedAt: NOW.getTime() - 7 * 60 * 60_000,
      plannedTotal: 10,
    });
    expect(isPracticeSessionResumable(readPracticeSessionSnapshot('mixed'), NOW)).toBe(false);
    localStorage.removeItem(PRACTICE_SESSION_STORAGE_KEY);
    localStorage.removeItem(SRS_STORAGE_KEY);
  });

  test('failed-card closure extends up to five items then defers leftovers', () => {
    expect(
      resolveSessionCompletion({
        completed: 10,
        plannedTotal: 10,
        extensionUsed: 0,
        unresolvedCount: 2,
      }),
    ).toBe('extend');
    expect(
      resolveSessionCompletion({
        completed: 15,
        plannedTotal: 10,
        extensionUsed: 5,
        unresolvedCount: 1,
      }),
    ).toBe('summary-with-deferred');
    expect(
      resolveSessionCompletion({
        completed: 10,
        plannedTotal: 10,
        extensionUsed: 0,
        unresolvedCount: 0,
      }),
    ).toBe('summary');
  });
});
