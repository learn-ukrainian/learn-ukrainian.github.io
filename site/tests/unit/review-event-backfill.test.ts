import { State } from 'ts-fsrs';
import { beforeEach, describe, expect, test } from 'vitest';
import {
  PRACTICE_MODE_DECK_VERSION,
  cardKey,
  loadState,
  rateCard,
  restoreSrsFromReviewEventExport,
  saveState,
  type CardState,
  type ReviewLogEntry,
} from '@site/src/lib/lexicon/srs';
import {
  FSRS_PARAMS_VERSION,
  REVIEW_EVENTS_SCHEMA,
  REVIEW_EVENTS_STORAGE_KEY,
  exportReviewEventLog,
  foldReviewEventsToCards,
  loadReviewEventLog,
  mintUlid,
  resetReviewEventEntropy,
  reviewEventCardKey,
  type ReviewEvent,
} from '@site/src/lib/lexicon/review-events';
import {
  REVIEW_EVENT_CLOCK_SKEW_MS,
  REVIEW_EVENT_MAX_AGE_MS,
  backfillReviewEventsFromSrsReviews,
  clampReviewedAt,
  exportBackfilledReviewEventLog,
  foldImportedReviewEvents,
  importReviewEventExport,
  parseReviewEventExport,
} from '@site/src/lib/lexicon/review-event-backfill';

const NOW = new Date('2026-06-23T12:00:00.000Z');
const LATER = new Date('2026-06-23T12:10:00.000Z');
const DAY_MS = 24 * 60 * 60 * 1000;

function reviewEntry(
  index: number,
  card = 'alpha',
  rating: ReviewLogEntry['rating'] = index % 2 === 0 ? 'good' : 'again',
): ReviewLogEntry {
  const reviewedAt = NOW.getTime() + index * 60_000;
  return {
    cardKey: cardKey(card, 'flashcards'),
    lemmaId: card,
    mode: 'flashcards',
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

function event(overrides: Partial<ReviewEvent> & Pick<ReviewEvent, 'eventId' | 'reviewedAt'>): ReviewEvent {
  return {
    lemmaId: 'alpha',
    mode: 'flashcards',
    rating: 'good',
    deckVersion: PRACTICE_MODE_DECK_VERSION,
    clientId: 'client-test',
    fsrsParamsVersion: FSRS_PARAMS_VERSION,
    ...overrides,
  };
}

class MemoryStorage {
  readonly values = new Map<string, string>();

  getItem(key: string): string | null {
    return this.values.get(key) ?? null;
  }

  setItem(key: string, value: string): void {
    this.values.set(key, value);
  }

  removeItem(key: string): void {
    this.values.delete(key);
  }
}

function orphanCard(overrides: Partial<CardState> = {}): CardState {
  return {
    due: NOW.getTime() + DAY_MS,
    stability: 12,
    difficulty: 3,
    elapsed_days: 4,
    scheduled_days: 6,
    learning_steps: 0,
    reps: 7,
    lapses: 1,
    state: State.Review,
    last_review: NOW.getTime() - DAY_MS,
    ...overrides,
  };
}

beforeEach(() => {
  localStorage.clear();
  resetReviewEventEntropy();
  loadState(localStorage, NOW);
});

describe('backfillReviewEventsFromSrsReviews', () => {
  test('lifts the raw SRS window with deterministic ids and is idempotent', () => {
    const storage = new MemoryStorage();
    const reviews = [reviewEntry(0, 'книга', 'good'), reviewEntry(1, 'книга', 'hard')];
    const first = backfillReviewEventsFromSrsReviews(reviews, storage, {
      deckVersion: PRACTICE_MODE_DECK_VERSION,
    });
    const second = backfillReviewEventsFromSrsReviews(reviews, storage, {
      deckVersion: PRACTICE_MODE_DECK_VERSION,
    });

    expect(first.added).toBe(2);
    expect(second.added).toBe(0);
    expect(second.skippedExisting).toBe(2);
    expect(loadReviewEventLog(storage).events).toHaveLength(2);
    expect(first).toEqual(
      backfillReviewEventsFromSrsReviews(reviews, new MemoryStorage(), {
        deckVersion: PRACTICE_MODE_DECK_VERSION,
      }),
    );
    expect(loadReviewEventLog(storage).events.map((item) => item.eventId)).toEqual(
      loadReviewEventLog(
        (() => {
          const other = new MemoryStorage();
          backfillReviewEventsFromSrsReviews(reviews, other, { deckVersion: PRACTICE_MODE_DECK_VERSION });
          return other;
        })(),
      ).events.map((item) => item.eventId),
    );
  });

  test('does not duplicate events already recorded by rateCard', () => {
    rateCard('alpha', 'flashcards', 'good', NOW);
    rateCard('alpha', 'flashcards', 'hard', LATER);
    const before = loadReviewEventLog(localStorage).events;
    expect(before).toHaveLength(2);

    const result = backfillReviewEventsFromSrsReviews(loadState(localStorage, LATER).reviews, localStorage, {
      deckVersion: PRACTICE_MODE_DECK_VERSION,
      fsrsParamsVersion: FSRS_PARAMS_VERSION,
    });
    expect(result.added).toBe(0);
    expect(result.skippedExisting).toBe(2);
    expect(loadReviewEventLog(localStorage).events).toHaveLength(2);
    expect(loadReviewEventLog(localStorage).events.map((item) => item.eventId)).toEqual(
      before.map((item) => item.eventId),
    );
  });

  test('does not invent events from compacted reviewAggregates', () => {
    const storage = new MemoryStorage();
    const result = backfillReviewEventsFromSrsReviews(
      [reviewEntry(0, 'beta', 'good')],
      storage,
      { deckVersion: PRACTICE_MODE_DECK_VERSION },
      {
        [cardKey('omega', 'flashcards')]: {
          ratings: { again: 3, hard: 1, good: 8, easy: 2 },
          firstReview: NOW.getTime() - 40 * DAY_MS,
          lastReview: NOW.getTime() - DAY_MS,
        },
      },
    );
    expect(result.added).toBe(1);
    expect(result.skippedAggregateOnly).toBe(14);
    expect(loadReviewEventLog(storage).events.map((item) => item.lemmaId)).toEqual(['beta']);
  });

  test('loadState backfills leftover raw reviews without a backend', () => {
    const storage = new MemoryStorage();
    loadState(storage, NOW);
    const state = loadState(storage, NOW);
    state.reviews.push(reviewEntry(0, 'дім', 'easy'));
    expect(saveState(state, storage, NOW.getTime()).ok).toBe(true);

    const reloaded = loadState(storage, NOW);
    expect(reloaded.reviews).toHaveLength(1);
    const log = loadReviewEventLog(storage);
    expect(log.events).toHaveLength(1);
    expect(log.events[0]).toMatchObject({
      lemmaId: 'дім',
      mode: 'flashcards',
      rating: 'easy',
      reviewedAt: NOW.getTime(),
      deckVersion: PRACTICE_MODE_DECK_VERSION,
    });
    expect(JSON.stringify(exportReviewEventLog(storage, NOW.getTime()))).not.toMatch(
      /userId|email|oauth|pocketbase|supabase|drive\.google/i,
    );
  });
});

describe('importReviewEventExport', () => {
  test('set-unions a valid export and rejects a poisoned payload', () => {
    const storage = new MemoryStorage();
    const exported = exportBackfilledReviewEventLog(
      [reviewEntry(0, 'книга', 'good')],
      storage,
      { deckVersion: PRACTICE_MODE_DECK_VERSION },
      NOW.getTime(),
    );
    expect(exported.schema).toBe(REVIEW_EVENTS_SCHEMA);
    expect(exported).not.toHaveProperty('userId');

    const other = new MemoryStorage();
    const first = importReviewEventExport(exported, other);
    const second = importReviewEventExport(exported, other);
    expect(first.ok).toBe(true);
    expect(first.ok && first.added).toBe(1);
    expect(second.ok && second.added).toBe(0);
    expect(loadReviewEventLog(other).events).toHaveLength(1);

    expect(parseReviewEventExport({ schema: 'nope', events: [] })).toBeNull();
    expect(importReviewEventExport({ schema: REVIEW_EVENTS_SCHEMA, events: [{ eventId: 'bad' }] }, other)).toEqual({
      ok: false,
      error: 'invalid review-event export',
    });
    expect(importReviewEventExport({ userId: 'learner@example.com', events: [] }, other).ok).toBe(false);
  });

  test('restore folds imported events onto SRS without dropping unrelated cards', () => {
    const storage = new MemoryStorage();
    loadState(storage, NOW);
    const first = rateCard('alpha', 'flashcards', 'good', NOW);
    rateCard('alpha', 'flashcards', 'hard', LATER);
    const exported = exportReviewEventLog(storage, LATER.getTime());

    const destination = new MemoryStorage();
    loadState(destination, NOW);
    const destinationState = loadState(destination, NOW);
    destinationState.cards.set(cardKey('orphan', 'cloze'), orphanCard());
    expect(saveState(destinationState, destination, NOW.getTime()).ok).toBe(true);

    const restored = restoreSrsFromReviewEventExport(exported, destination, LATER);
    expect(restored.ok).toBe(true);
    expect(restored.ok && restored.updated).toBe(1);
    expect(restored.ok && restored.persisted).toBe(true);

    const after = loadState(destination, LATER);
    expect(after.cards.get(cardKey('alpha', 'flashcards'))).toEqual(
      foldReviewEventsToCards(exported.events, after.settings.params).get(reviewEventCardKey('alpha', 'flashcards')),
    );
    expect(after.cards.get(cardKey('orphan', 'cloze'))).toEqual(orphanCard());
    expect(first.reps).toBe(1);
  });

  test('restore folds leftover local reviews together with the imported log', () => {
    const storage = new MemoryStorage();
    loadState(storage, NOW);
    const local = loadState(storage, NOW);
    local.reviews.push(reviewEntry(0, 'local', 'good'));
    expect(saveState(local, storage, NOW.getTime()).ok).toBe(true);

    const remote = new MemoryStorage();
    loadState(remote, NOW);
    rateCard('remote', 'flashcards', 'easy', LATER);
    const exported = exportReviewEventLog(remote, LATER.getTime());

    const restored = restoreSrsFromReviewEventExport(exported, storage, LATER);
    expect(restored.ok).toBe(true);
    expect(restored.ok && restored.updated).toBe(2);

    const after = loadState(storage, LATER);
    expect(after.cards.has(cardKey('local', 'flashcards'))).toBe(true);
    expect(after.cards.has(cardKey('remote', 'flashcards'))).toBe(true);
    expect(loadReviewEventLog(storage).events).toHaveLength(2);
  });

  test('clamps absurd client clocks at fold time without rewriting the log', () => {
    const receivedAt = LATER.getTime();
    const future = receivedAt + REVIEW_EVENT_CLOCK_SKEW_MS + 1;
    const ancient = receivedAt - REVIEW_EVENT_MAX_AGE_MS - 1;
    expect(clampReviewedAt(future, receivedAt)).toBe(receivedAt);
    expect(clampReviewedAt(ancient, receivedAt)).toBe(receivedAt);
    expect(clampReviewedAt(NOW.getTime(), receivedAt)).toBe(NOW.getTime());

    const storage = new MemoryStorage();
    const exported = {
      schema: REVIEW_EVENTS_SCHEMA,
      exportedAt: receivedAt,
      clientId: 'device-b',
      fsrsParamsVersion: FSRS_PARAMS_VERSION,
      events: [
        event({ eventId: mintUlid(future), reviewedAt: future, lemmaId: 'future', rating: 'easy' }),
      ],
    };
    const imported = importReviewEventExport(exported, storage);
    expect(imported.ok).toBe(true);
    expect(loadReviewEventLog(storage).events[0]?.reviewedAt).toBe(future);

    const folded = foldImportedReviewEvents(imported.ok ? imported.events : [], undefined, receivedAt);
    const unclamped = foldReviewEventsToCards(imported.ok ? imported.events : []);
    expect(folded.get(reviewEventCardKey('future', 'flashcards'))?.last_review).toBe(receivedAt);
    expect(unclamped.get(reviewEventCardKey('future', 'flashcards'))?.last_review).toBe(future);
  });
});
