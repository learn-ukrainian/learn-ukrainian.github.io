import { beforeEach, describe, expect, test } from 'vitest';
import {
  PRACTICE_MODE_DECK_VERSION,
  cardKey,
  loadState,
  rateCard,
} from '@site/src/lib/lexicon/srs';
import {
  FSRS_PARAMS_VERSION,
  REVIEW_EVENTS_SCHEMA,
  REVIEW_EVENTS_STORAGE_KEY,
  REVIEW_EVENTS_IDB_MIGRATED_KEY,
  REVIEW_EVENTS_MAX_RETAINED,
  appendReviewEvent,
  canonicalReplayOrder,
  createMemoryReviewEventIdbDriver,
  ensureReviewEventLogReady,
  exportReviewEventLog,
  foldReviewEventsToCards,
  loadReviewEventLog,
  migrateReviewEventsLocalStorageToIdb,
  mintDeterministicUlid,
  mintUlid,
  persistReviewEventLogWithOverflow,
  recordCardReviewEvent,
  resetReviewEventDurableStateForTests,
  resetReviewEventEntropy,
  reviewEventCardKey,
  setReviewEventIdbDriverForTests,
  trimReviewEventLog,
  upsertReviewEvents,
  type ReviewEvent,
} from '@site/src/lib/lexicon/review-events';

const NOW = new Date('2026-06-23T12:00:00.000Z');
const LATER = new Date('2026-06-23T12:10:00.000Z');

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

class EventWriteFailingStorage extends MemoryStorage {
  setItem(key: string, value: string): void {
    if (key === REVIEW_EVENTS_STORAGE_KEY) {
      throw new Error('event log unavailable');
    }
    super.setItem(key, value);
  }
}

beforeEach(() => {
  localStorage.clear();
  resetReviewEventEntropy();
  resetReviewEventDurableStateForTests();
  setReviewEventIdbDriverForTests(null);
  loadState(localStorage, NOW);
});

describe('mintUlid', () => {
  test('is 26 Crockford characters and sorts by time', () => {
    const earlier = mintUlid(NOW.getTime(), () => 0.1);
    resetReviewEventEntropy();
    const later = mintUlid(NOW.getTime() + 1, () => 0.1);
    expect(earlier).toMatch(/^[0-9A-HJKMNP-TV-Z]{26}$/);
    expect(later).toMatch(/^[0-9A-HJKMNP-TV-Z]{26}$/);
    expect(earlier < later).toBe(true);
  });

  test('stays unique and ordered within the same millisecond', () => {
    const first = mintUlid(NOW.getTime(), () => 0.2);
    const second = mintUlid(NOW.getTime(), () => 0.9);
    expect(first).not.toBe(second);
    expect(first < second).toBe(true);
  });
});

describe('mintDeterministicUlid', () => {
  test('is stable for the same fingerprint and sorts by time', () => {
    const first = mintDeterministicUlid(NOW.getTime(), 'alpha\\0flashcards\\0good\\0' + NOW.getTime());
    const again = mintDeterministicUlid(NOW.getTime(), 'alpha\\0flashcards\\0good\\0' + NOW.getTime());
    const later = mintDeterministicUlid(LATER.getTime(), 'alpha\\0flashcards\\0good\\0' + LATER.getTime());
    expect(first).toMatch(/^[0-9A-HJKMNP-TV-Z]{26}$/);
    expect(first).toBe(again);
    expect(first < later).toBe(true);
  });
});

describe('review-event log', () => {
  test('appends locally without a backend and exports no user identity', () => {
    const storage = new MemoryStorage();
    const recorded = recordCardReviewEvent(
      {
        lemmaId: 'книга',
        mode: 'cloze',
        rating: 'again',
        reviewedAt: NOW,
        deckVersion: PRACTICE_MODE_DECK_VERSION,
        presentation: { clozeId: 'knyha-acc', polarity: 'word-to-meaning' },
      },
      storage,
    );

    expect(recorded?.eventId).toMatch(/^[0-9A-HJKMNP-TV-Z]{26}$/);
    expect(recorded?.clientId).toBeTruthy();
    expect(recorded?.presentation).toEqual({ clozeId: 'knyha-acc', polarity: 'word-to-meaning' });

    const exported = exportReviewEventLog(storage, NOW.getTime());
    expect(exported.schema).toBe(REVIEW_EVENTS_SCHEMA);
    expect(exported.events).toHaveLength(1);
    expect(exported).not.toHaveProperty('userId');
    expect(JSON.stringify(exported)).not.toMatch(/userId|email|oauth|pocketbase|supabase/i);
  });

  test('upsert is idempotent on eventId', () => {
    const storage = new MemoryStorage();
    const first = event({ eventId: mintUlid(NOW.getTime()), reviewedAt: NOW.getTime() });
    expect(upsertReviewEvents([first], storage).added).toBe(1);
    expect(upsertReviewEvents([first, first], storage).added).toBe(0);
    expect(loadReviewEventLog(storage).events).toHaveLength(1);
  });

  test('replay order is reviewedAt then eventId, not insert order', () => {
    const laterId = mintUlid(LATER.getTime());
    const earlierId = mintUlid(NOW.getTime());
    const inserted = [
      event({ eventId: laterId, reviewedAt: LATER.getTime(), rating: 'easy', lemmaId: 'beta' }),
      event({ eventId: earlierId, reviewedAt: NOW.getTime(), rating: 'good', lemmaId: 'alpha' }),
    ];
    const ordered = canonicalReplayOrder(inserted);
    expect(ordered.map((item) => item.lemmaId)).toEqual(['alpha', 'beta']);
  });

  test('rejects malformed events instead of poisoning the log', () => {
    const storage = new MemoryStorage();
    const valid = event({ eventId: mintUlid(NOW.getTime()), reviewedAt: NOW.getTime() });
    expect(appendReviewEvent({ ...valid, eventId: 'not-a-ulid' }, storage)).toBeNull();
    expect(appendReviewEvent(valid, storage)?.eventId).toBe(valid.eventId);
    expect(loadReviewEventLog(storage).events).toHaveLength(1);
  });
});

describe('rateCard records the §10.1 log', () => {
  test('each rating appends an event that folds back to the same card', () => {
    const first = rateCard('alpha', 'flashcards', 'good', NOW);
    const second = rateCard('alpha', 'flashcards', 'hard', LATER);
    const log = loadReviewEventLog(localStorage);

    expect(log.events).toHaveLength(2);
    expect(log.events[0]).toMatchObject({
      lemmaId: 'alpha',
      mode: 'flashcards',
      rating: 'good',
      reviewedAt: NOW.getTime(),
      deckVersion: PRACTICE_MODE_DECK_VERSION,
    });
    expect(log.events[1]).toMatchObject({
      lemmaId: 'alpha',
      rating: 'hard',
      reviewedAt: LATER.getTime(),
    });

    const folded = foldReviewEventsToCards(log.events, loadState(localStorage, LATER).settings.params);
    expect(folded.get(reviewEventCardKey('alpha', 'flashcards'))).toEqual(second);
    expect(folded.get(cardKey('alpha', 'flashcards'))).toEqual(second);
    expect(first.reps).toBe(1);
    expect(second.reps).toBe(2);
  });

  test('stores presentation metadata when the caller supplies it', () => {
    rateCard('дім', 'cloze', 'good', NOW, {
      blankCase: 'locative',
      clozeId: 'dim-loc',
      polarity: 'word-to-meaning',
      optionSetId: 'gender',
      slotId: 'dim:paradigm:1',
    });
    expect(loadReviewEventLog(localStorage).events[0]?.presentation).toEqual({
      slotId: 'dim:paradigm:1',
      clozeId: 'dim-loc',
      polarity: 'word-to-meaning',
      optionSetId: 'gender',
    });
  });

  test('keeps derived SRS state when the event log cannot persist', () => {
    const storage = new EventWriteFailingStorage();
    loadState(storage, NOW);
    const card = rateCard('alpha', 'good', NOW);
    expect(card.reps).toBe(1);
    expect(loadReviewEventLog(storage).events).toHaveLength(0);
    expect(JSON.parse(storage.getItem('lu-lexicon-srs') ?? '{}').cards[cardKey('alpha', 'flashcards')].reps).toBe(1);
  });
});

describe('IndexedDB durable store', () => {
  test('migrates localStorage log to IDB and stops growing localStorage', async () => {
    const driver = createMemoryReviewEventIdbDriver();
    setReviewEventIdbDriverForTests(driver);

    const first = event({ eventId: mintUlid(NOW.getTime()), reviewedAt: NOW.getTime(), lemmaId: 'книга' });
    const second = event({
      eventId: mintUlid(LATER.getTime()),
      reviewedAt: LATER.getTime(),
      lemmaId: 'дім',
      rating: 'hard',
    });
    localStorage.setItem(
      REVIEW_EVENTS_STORAGE_KEY,
      JSON.stringify({
        schema: REVIEW_EVENTS_SCHEMA,
        schemaVersion: 1,
        clientId: 'migrate-client',
        fsrsParamsVersion: FSRS_PARAMS_VERSION,
        events: [first, second],
      }),
    );

    const result = await migrateReviewEventsLocalStorageToIdb(localStorage);
    expect(result.migrated).toBe(2);
    expect(result.log.events).toHaveLength(2);
    expect(localStorage.getItem(REVIEW_EVENTS_STORAGE_KEY)).toBeNull();
    expect(localStorage.getItem(REVIEW_EVENTS_IDB_MIGRATED_KEY)).toBe('1');

    const raw = await driver.getRaw();
    expect(raw).toMatchObject({ clientId: 'migrate-client' });
    expect((raw as { events: unknown[] }).events).toHaveLength(2);

    // Second migrate is idempotent and does not revive the LS key.
    const again = await migrateReviewEventsLocalStorageToIdb(localStorage);
    expect(again.log.events).toHaveLength(2);
    expect(localStorage.getItem(REVIEW_EVENTS_STORAGE_KEY)).toBeNull();
  });

  test('reads and writes the log through the IDB driver', async () => {
    const driver = createMemoryReviewEventIdbDriver();
    setReviewEventIdbDriverForTests(driver);

    recordCardReviewEvent(
      {
        lemmaId: 'море',
        mode: 'flashcards',
        rating: 'good',
        reviewedAt: NOW,
        deckVersion: PRACTICE_MODE_DECK_VERSION,
      },
      localStorage,
    );
    await ensureReviewEventLogReady(localStorage);

    expect(driver.writes).toBeGreaterThan(0);
    expect(loadReviewEventLog(localStorage).events).toHaveLength(1);
    expect(localStorage.getItem(REVIEW_EVENTS_STORAGE_KEY)).toBeNull();

    resetReviewEventDurableStateForTests();
    const reloaded = await ensureReviewEventLogReady(localStorage);
    expect(reloaded.events).toHaveLength(1);
    expect(reloaded.events[0]?.lemmaId).toBe('море');
  });

  test('evicts oldest events on QuotaExceeded so persist stays best-effort', async () => {
    const driver = createMemoryReviewEventIdbDriver();
    driver.failNextWrites = 1;
    setReviewEventIdbDriverForTests(driver);

    const events = Array.from({ length: 8 }, (_, index) =>
      event({
        eventId: mintUlid(NOW.getTime() + index),
        reviewedAt: NOW.getTime() + index * 1000,
        lemmaId: `lemma-${index}`,
      }),
    );
    const log = {
      schema: REVIEW_EVENTS_SCHEMA,
      schemaVersion: 1 as const,
      clientId: 'overflow-client',
      fsrsParamsVersion: FSRS_PARAMS_VERSION,
      events,
    };

    const result = await persistReviewEventLogWithOverflow(log, driver, 8);
    expect(result.ok).toBe(true);
    expect(result.evicted).toBeGreaterThan(0);
    expect(result.log.events.length).toBeLessThan(8);
    // Newest events survive.
    expect(result.log.events.at(-1)?.lemmaId).toBe('lemma-7');
    expect(result.log.events.some((item) => item.lemmaId === 'lemma-0')).toBe(false);
  });

  test('trimReviewEventLog keeps newest N by replay order', () => {
    const events = [
      event({ eventId: mintUlid(LATER.getTime()), reviewedAt: LATER.getTime(), lemmaId: 'new' }),
      event({ eventId: mintUlid(NOW.getTime()), reviewedAt: NOW.getTime(), lemmaId: 'old' }),
    ];
    const trimmed = trimReviewEventLog(
      {
        schema: REVIEW_EVENTS_SCHEMA,
        schemaVersion: 1,
        clientId: 'trim',
        fsrsParamsVersion: FSRS_PARAMS_VERSION,
        events,
      },
      1,
    );
    expect(trimmed.events).toHaveLength(1);
    expect(trimmed.events[0]?.lemmaId).toBe('new');
    expect(REVIEW_EVENTS_MAX_RETAINED).toBeGreaterThan(1000);
  });

  test('export/import round-trips the remaining durable log without identity fields', async () => {
    const driver = createMemoryReviewEventIdbDriver();
    setReviewEventIdbDriverForTests(driver);

    upsertReviewEvents(
      [
        event({ eventId: mintUlid(NOW.getTime()), reviewedAt: NOW.getTime(), lemmaId: 'alpha' }),
        event({
          eventId: mintUlid(LATER.getTime()),
          reviewedAt: LATER.getTime(),
          lemmaId: 'beta',
          rating: 'easy',
        }),
      ],
      localStorage,
    );
    await ensureReviewEventLogReady(localStorage);

    const exported = exportReviewEventLog(localStorage, LATER.getTime());
    expect(exported.events.map((item) => item.lemmaId)).toEqual(['alpha', 'beta']);
    expect(exported).not.toHaveProperty('userId');
    expect(JSON.stringify(exported)).not.toMatch(/userId|email|oauth|pocketbase|supabase/i);

    const otherDriver = createMemoryReviewEventIdbDriver();
    setReviewEventIdbDriverForTests(otherDriver);
    resetReviewEventDurableStateForTests();
    localStorage.clear();

    const { importReviewEventExport } = await import('@site/src/lib/lexicon/review-event-sync');
    const imported = importReviewEventExport(exported, localStorage);
    expect(imported?.added).toBe(2);
    await ensureReviewEventLogReady(localStorage);
    expect(loadReviewEventLog(localStorage).events).toHaveLength(2);
    expect(JSON.stringify(exportReviewEventLog(localStorage, LATER.getTime()))).not.toMatch(
      /userId|email|oauth|pocketbase|supabase/i,
    );
  });
});
