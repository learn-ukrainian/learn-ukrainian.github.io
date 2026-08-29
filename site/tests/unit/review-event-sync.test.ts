import { beforeEach, describe, expect, test } from 'vitest';
import { PRACTICE_MODE_DECK_VERSION } from '@site/src/lib/lexicon/srs';
import {
  FSRS_PARAMS_VERSION,
  REVIEW_EVENTS_SCHEMA,
  canonicalReplayOrder,
  exportReviewEventLog,
  foldReviewEventsToCards,
  loadReviewEventLog,
  recordCardReviewEvent,
  resetReviewEventEntropy,
  type ReviewEvent,
} from '@site/src/lib/lexicon/review-events';
import {
  DEFAULT_REVIEW_EVENT_CLOCK_POLICY,
  REVIEW_EVENT_SYNC_SCHEMA,
  REVIEW_EVENT_SYNC_STORAGE_KEY,
  clampReviewEventTime,
  importReviewEventExport,
  loadReviewEventSyncState,
  mergeServerReviewEvents,
  runReviewEventSync,
  toServerReviewEvent,
  uniformFsrsParamsVersion,
  type ReviewEventPullPage,
  type ReviewEventPushAck,
  type ReviewEventSyncAdapter,
  type ServerReviewEvent,
} from '@site/src/lib/lexicon/review-event-sync';

const SERVER_NOW = Date.parse('2026-06-23T12:00:00.000Z');
const DAY = 24 * 60 * 60 * 1000;

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

/**
 * In-memory stand-in for the future backend: idempotent upsert per `eventId`
 * (first ingest fixes `serverSeq`/`serverReceivedAt`), monotonic `serverSeq`,
 * paged pull past the cursor. Its ingest stamping goes through
 * `toServerReviewEvent`, the same contract a PocketBase/Drive adapter must
 * reproduce.
 */
class FakeReviewEventServer implements ReviewEventSyncAdapter {
  readonly rows = new Map<string, ServerReviewEvent>();
  readonly pullCursors: number[] = [];
  private nextSeq = 1;

  constructor(
    private readonly pageSize = 2,
    private readonly clock: () => number = () => SERVER_NOW,
  ) {}

  async push(events: readonly ReviewEvent[]): Promise<ReviewEventPushAck> {
    const receivedAt = this.clock();
    const ackedEventIds: string[] = [];
    for (const event of events) {
      if (this.rows.has(event.eventId)) {
        ackedEventIds.push(event.eventId);
        continue;
      }
      const stamped = toServerReviewEvent(event, this.nextSeq, receivedAt);
      if (!stamped) continue;
      this.nextSeq += 1;
      this.rows.set(stamped.eventId, stamped);
      ackedEventIds.push(stamped.eventId);
    }
    return { ackedEventIds };
  }

  async pull(sinceServerSeq: number): Promise<ReviewEventPullPage> {
    this.pullCursors.push(sinceServerSeq);
    const due = [...this.rows.values()]
      .filter((row) => row.serverSeq > sinceServerSeq)
      .sort((left, right) => left.serverSeq - right.serverSeq);
    const page = due.slice(0, this.pageSize);
    const upToServerSeq = page.length > 0 ? page[page.length - 1].serverSeq : sinceServerSeq;
    return { events: page, upToServerSeq, hasMore: due.length > page.length };
  }
}

/** A push that loses everything (offline-shaped failure: nothing ACKed). */
class DroppingAdapter implements ReviewEventSyncAdapter {
  readonly pushes: number[][] = [];

  async push(events: readonly ReviewEvent[]): Promise<ReviewEventPushAck> {
    this.pushes.push(events.map((event) => event.reviewedAt));
    return { ackedEventIds: [] };
  }

  async pull(): Promise<ReviewEventPullPage> {
    return { events: [], upToServerSeq: 0, hasMore: false };
  }
}

function record(
  storage: MemoryStorage,
  lemmaId: string,
  mode: 'flashcards' | 'matching' | 'cloze',
  rating: 'again' | 'hard' | 'good' | 'easy',
  reviewedAt: number,
  clientId?: string,
): void {
  const event = recordCardReviewEvent(
    {
      lemmaId,
      mode,
      rating,
      reviewedAt,
      deckVersion: PRACTICE_MODE_DECK_VERSION,
      ...(clientId ? { clientId } : {}),
    },
    storage,
  );
  expect(event).not.toBeNull();
}

function logEvents(storage: MemoryStorage) {
  return canonicalReplayOrder(loadReviewEventLog(storage).events);
}

function folded(storage: MemoryStorage) {
  return Object.fromEntries([...foldReviewEventsToCards(loadReviewEventLog(storage).events)]);
}

beforeEach(() => {
  localStorage.clear();
  resetReviewEventEntropy();
});

describe('clampReviewEventTime', () => {
  test('passes a client clock within the skew window', () => {
    const within = SERVER_NOW + DEFAULT_REVIEW_EVENT_CLOCK_POLICY.futureSkewMs;
    expect(clampReviewEventTime(within, SERVER_NOW)).toBe(within);
  });

  test('clamps a future-clock event to serverReceivedAt', () => {
    expect(clampReviewEventTime(SERVER_NOW + 6 * 60 * 1000, SERVER_NOW)).toBe(SERVER_NOW);
  });

  test('clamps an absurdly old event to serverReceivedAt', () => {
    expect(clampReviewEventTime(SERVER_NOW - 400 * DAY, SERVER_NOW)).toBe(SERVER_NOW);
  });

  test('keeps a plausible old review and repairs non-finite input', () => {
    expect(clampReviewEventTime(SERVER_NOW - 30 * DAY, SERVER_NOW)).toBe(SERVER_NOW - 30 * DAY);
    expect(clampReviewEventTime(Number.NaN, SERVER_NOW)).toBe(SERVER_NOW);
  });
});

describe('toServerReviewEvent', () => {
  test('stamps serverSeq and serverReceivedAt and clamps the client clock', () => {
    const stamped = toServerReviewEvent(
      {
        eventId: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
        lemmaId: 'книга',
        mode: 'cloze',
        rating: 'good',
        reviewedAt: SERVER_NOW + DAY,
        deckVersion: PRACTICE_MODE_DECK_VERSION,
        clientId: 'client-a',
      },
      7,
      SERVER_NOW,
    );
    expect(stamped).toMatchObject({ serverSeq: 7, serverReceivedAt: SERVER_NOW, reviewedAt: SERVER_NOW });
  });

  test('fails closed on an invalid event or invalid stamps', () => {
    const valid = {
      eventId: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
      lemmaId: 'книга',
      mode: 'cloze',
      rating: 'good',
      reviewedAt: SERVER_NOW,
      deckVersion: PRACTICE_MODE_DECK_VERSION,
      clientId: 'client-a',
    };
    expect(toServerReviewEvent({ ...valid, rating: 'perfect' }, 1, SERVER_NOW)).toBeNull();
    expect(toServerReviewEvent(valid, -1, SERVER_NOW)).toBeNull();
    expect(toServerReviewEvent(valid, 1, Number.NaN)).toBeNull();
  });
});

describe('mergeServerReviewEvents', () => {
  test('adds unknown events and skips invalid ones', () => {
    const storage = new MemoryStorage();
    const stamped = toServerReviewEvent(
      {
        eventId: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
        lemmaId: 'книга',
        mode: 'cloze',
        rating: 'good',
        reviewedAt: SERVER_NOW,
        deckVersion: PRACTICE_MODE_DECK_VERSION,
        clientId: 'client-b',
      },
      1,
      SERVER_NOW,
    );
    expect(stamped).not.toBeNull();
    if (!stamped) throw new Error('stamping failed');
    const merged = mergeServerReviewEvents([stamped, { ...stamped, eventId: 'not-a-ulid' }], storage);
    expect(merged).toEqual({ added: 1, replaced: 0 });
    expect(loadReviewEventLog(storage).events).toHaveLength(1);
  });

  test('replaces the local copy when the server-clamped fields differ, and is a no-op when identical', () => {
    const storage = new MemoryStorage();
    record(storage, 'книга', 'cloze', 'good', SERVER_NOW + DAY); // future clock
    const local = loadReviewEventLog(storage).events[0];
    const clamped = toServerReviewEvent(local, 3, SERVER_NOW);
    expect(clamped).not.toBeNull();
    if (!clamped) throw new Error('stamping failed');

    const first = mergeServerReviewEvents([clamped], storage);
    expect(first).toEqual({ added: 0, replaced: 1 });
    expect(loadReviewEventLog(storage).events[0].reviewedAt).toBe(SERVER_NOW);

    const second = mergeServerReviewEvents([clamped], storage);
    expect(second).toEqual({ added: 0, replaced: 0 });
  });
});

describe('runReviewEventSync', () => {
  test('first sync pushes the whole local backlog, pages the pull, and advances the cursor once', async () => {
    const device = new MemoryStorage();
    for (let index = 0; index < 5; index += 1) {
      record(device, `lemma-${index}`, 'flashcards', 'good', SERVER_NOW - (5 - index) * 60 * 1000);
    }
    const server = new FakeReviewEventServer(/* pageSize */ 2);

    const first = await runReviewEventSync(server, device, { now: () => SERVER_NOW });
    expect(first).toMatchObject({ pushed: 5, acked: 5, pulled: 5, mergedAdded: 0, mergedReplaced: 0, lastServerSeq: 5 });
    expect([...server.rows]).toHaveLength(5);

    const state = loadReviewEventSyncState(device);
    expect(state).toMatchObject({ schema: REVIEW_EVENT_SYNC_SCHEMA, lastServerSeq: 5, pendingEventIds: [] });
    expect(state.lastSyncedAt).toBe(SERVER_NOW);

    const second = await runReviewEventSync(server, device, { now: () => SERVER_NOW });
    expect(second).toMatchObject({ pushed: 0, acked: 0, pulled: 0, mergedAdded: 0, lastServerSeq: 5 });
    expect(server.pullCursors.at(-1)).toBe(5);
  });

  test('a failed push keeps the backlog and re-pushes idempotently next round', async () => {
    const device = new MemoryStorage();
    record(device, 'книга', 'flashcards', 'good', SERVER_NOW - 60 * 1000);
    record(device, 'мир', 'matching', 'easy', SERVER_NOW - 30 * 1000);
    const dropping = new DroppingAdapter();

    const failed = await runReviewEventSync(dropping, device, { now: () => SERVER_NOW });
    expect(failed).toMatchObject({ pushed: 2, acked: 0 });
    const afterFailure = loadReviewEventSyncState(device);
    expect(afterFailure.pendingEventIds).toHaveLength(2);

    const server = new FakeReviewEventServer();
    const retry = await runReviewEventSync(server, device, { now: () => SERVER_NOW });
    expect(retry).toMatchObject({ pushed: 2, acked: 2, lastServerSeq: 2 });
    expect(loadReviewEventSyncState(device).pendingEventIds).toEqual([]);

    // Idempotent upsert: re-pushing the same events ACKs without adding rows.
    const rePush = await server.push(loadReviewEventLog(device).events);
    expect(rePush.ackedEventIds).toHaveLength(2);
    expect([...server.rows]).toHaveLength(2);
  });

  test('two offline devices converge on one log and one FSRS fold, including a same-card conflict and a fast clock', async () => {
    const deviceA = new MemoryStorage();
    const deviceB = new MemoryStorage();
    // Both devices reviewed offline — same card on both (the LWW-on-state trap
    // §10.1 exists to avoid) plus device-only cards; B's clock runs 1h fast.
    record(deviceA, 'книга', 'flashcards', 'good', SERVER_NOW - 3 * 60 * 1000, 'client-device-a');
    record(deviceA, 'книга', 'cloze', 'again', SERVER_NOW - 2 * 60 * 1000, 'client-device-a');
    record(deviceA, 'слово', 'flashcards', 'hard', SERVER_NOW - 60 * 1000, 'client-device-a');
    record(deviceB, 'книга', 'flashcards', 'hard', SERVER_NOW + 60 * 60 * 1000 - 45 * 60 * 1000, 'client-device-b');
    record(deviceB, 'місто', 'matching', 'easy', SERVER_NOW + 60 * 60 * 1000, 'client-device-b');
    expect(loadReviewEventLog(deviceA).events.map((event) => event.clientId)).not.toContain(
      loadReviewEventLog(deviceB).events[0].clientId,
    );

    const server = new FakeReviewEventServer();
    await runReviewEventSync(server, deviceA, { now: () => SERVER_NOW });
    const bFirst = await runReviewEventSync(server, deviceB, { now: () => SERVER_NOW });
    // B's first pull carries A's history in AND the server-clamped copies of
    // B's own fast-clock events (which replace the local unclamped twins).
    expect(bFirst.mergedAdded).toBe(3);
    expect(bFirst.mergedReplaced).toBe(2);
    const aSecond = await runReviewEventSync(server, deviceA, { now: () => SERVER_NOW });
    await runReviewEventSync(server, deviceB, { now: () => SERVER_NOW });

    expect(aSecond.mergedAdded).toBe(2); // B's events merged into A
    expect(aSecond.mergedReplaced).toBe(0);
    const eventsA = logEvents(deviceA);
    const eventsB = logEvents(deviceB);
    expect(eventsA).toEqual(eventsB);
    expect(eventsA).toHaveLength(5);
    // B's fast-clock event was clamped to the server ingest time on BOTH devices.
    const clampedEvent = eventsA.find((event) => event.lemmaId === 'місто');
    expect(clampedEvent?.reviewedAt).toBe(SERVER_NOW);

    expect(uniformFsrsParamsVersion(eventsA)).toBe(FSRS_PARAMS_VERSION);
    expect(folded(deviceA)).toEqual(folded(deviceB));
    // …and the fold equals a single-device fold of the raw union (no fork).
    const unionFold = Object.fromEntries([
      ...foldReviewEventsToCards(canonicalReplayOrder([...eventsA])),
    ]);
    expect(folded(deviceA)).toEqual(unionFold);
  });
});

describe('importReviewEventExport', () => {
  test('restores an export into a fresh device with fold parity', () => {
    const source = new MemoryStorage();
    record(source, 'книга', 'flashcards', 'good', SERVER_NOW - 3 * 60 * 1000);
    record(source, 'книга', 'cloze', 'again', SERVER_NOW - 2 * 60 * 1000);
    const exported = JSON.parse(JSON.stringify(exportReviewEventLog(source, SERVER_NOW))) as unknown;
    expect((exported as { schema: string }).schema).toBe(REVIEW_EVENTS_SCHEMA);

    const target = new MemoryStorage();
    const result = importReviewEventExport(exported, target);
    expect(result).toEqual({ added: 2, replaced: 0, skipped: 0 });
    expect(logEvents(target)).toEqual(logEvents(source));
    expect(folded(target)).toEqual(folded(source));
  });

  test('clamps an export event whose reviewedAt is beyond exportedAt, and counts junk as skipped', () => {
    const exported = {
      schema: REVIEW_EVENTS_SCHEMA,
      exportedAt: SERVER_NOW,
      clientId: 'client-a',
      fsrsParamsVersion: FSRS_PARAMS_VERSION,
      events: [
        {
          eventId: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
          lemmaId: 'книга',
          mode: 'flashcards',
          rating: 'good',
          reviewedAt: SERVER_NOW + DAY, // newer than its own export → clamped
          deckVersion: PRACTICE_MODE_DECK_VERSION,
          clientId: 'client-a',
        },
        { eventId: 'junk' },
      ],
    };
    const target = new MemoryStorage();
    const result = importReviewEventExport(exported, target);
    expect(result).toEqual({ added: 1, replaced: 0, skipped: 1 });
    expect(loadReviewEventLog(target).events[0].reviewedAt).toBe(SERVER_NOW);
  });

  test('rejects a foreign or malformed export document', () => {
    const storage = new MemoryStorage();
    expect(importReviewEventExport(null, storage)).toBeNull();
    expect(importReviewEventExport({ schema: 'other.v1', events: [] }, storage)).toBeNull();
    expect(importReviewEventExport({ schema: REVIEW_EVENTS_SCHEMA, events: [] }, storage)).toBeNull();
    expect(
      importReviewEventExport({ schema: REVIEW_EVENTS_SCHEMA, events: [], exportedAt: SERVER_NOW }, storage),
    ).toEqual({ added: 0, replaced: 0, skipped: 0 });
  });
});

describe('uniformFsrsParamsVersion', () => {
  test('is null for empty or mixed logs and the shared version otherwise', () => {
    expect(uniformFsrsParamsVersion([])).toBeNull();
    const base = {
      lemmaId: 'книга',
      mode: 'flashcards' as const,
      rating: 'good' as const,
      reviewedAt: SERVER_NOW,
      deckVersion: PRACTICE_MODE_DECK_VERSION,
      clientId: 'client-a',
    };
    const event = (id: string, fsrsParamsVersion: number) => ({
      eventId: id,
      ...base,
      fsrsParamsVersion,
    });
    expect(uniformFsrsParamsVersion([event('01ARZ3NDEKTSV4RRFFQ69G5FAV', 1)])).toBe(1);
    expect(
      uniformFsrsParamsVersion([
        event('01ARZ3NDEKTSV4RRFFQ69G5FAV', 1),
        event('01ARZ3NDEKTSV4RRFFQ69G5FAW', 2),
      ]),
    ).toBeNull();
  });
});

describe('sync state storage', () => {
  test('a fresh device starts at cursor zero and never touches the main SRS key', () => {
    const storage = new MemoryStorage();
    const state = loadReviewEventSyncState(storage);
    expect(state).toMatchObject({ lastServerSeq: 0, pendingEventIds: [] });
    expect(state.schema).toBe(REVIEW_EVENT_SYNC_SCHEMA);
    expect([...storage.values.keys()]).not.toContain(REVIEW_EVENT_SYNC_STORAGE_KEY);
  });
});
