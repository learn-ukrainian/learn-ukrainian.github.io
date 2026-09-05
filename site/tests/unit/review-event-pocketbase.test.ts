import { beforeEach, describe, expect, test } from 'vitest';
import { PRACTICE_MODE_DECK_VERSION } from '@site/src/lib/lexicon/srs';
import {
  REVIEW_EVENTS_SCHEMA,
  canonicalReplayOrder,
  foldReviewEventsToCards,
  loadReviewEventLog,
  recordCardReviewEvent,
  resetReviewEventEntropy,
  type ReviewEvent,
} from '@site/src/lib/lexicon/review-events';
import {
  importReviewEventExport,
  runReviewEventSync,
  toServerReviewEvent,
  uniformFsrsParamsVersion,
  type ServerReviewEvent,
} from '@site/src/lib/lexicon/review-event-sync';
import {
  POCKETBASE_BASE_URL_ENV,
  POCKETBASE_EXPORT_CLIENT_ID,
  PocketBaseReviewEventAdapter,
  pocketBaseAdapterFromEnv,
  type PocketBaseFetchLike,
} from '@site/src/lib/lexicon/review-event-pocketbase';

const SERVER_NOW = Date.parse('2026-06-23T12:00:00.000Z');

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

interface FakeRequest {
  method: string;
  path: string;
  query: URLSearchParams;
  headers: Record<string, string>;
  body?: Record<string, unknown>;
}

/**
 * In-memory stand-in for PocketBase + `pb_hooks/review_events.pb.js`. Replays
 * the adapter-visible contract: the hook stamps ingest through the same
 * `toServerReviewEvent` (per-user monotonic `serverSeq`, `serverReceivedAt`,
 * clock clamp), the unique `eventId` index answers duplicates with the 400
 * `validation_not_unique` shape, and list requests filter/sort/page by
 * `serverSeq`. Rows are scoped by the Authorization token — the client never
 * sends a userId (§10.3 ⟦agy v4⟧).
 */
class FakePocketBase {
  readonly requests: FakeRequest[] = [];
  private readonly users = new Map<string, string>(); // token → userId
  private readonly rows = new Map<string, ServerReviewEvent & { user: string }>();
  private readonly nextSeq = new Map<string, number>();

  registerUser(token: string, userId: string): void {
    this.users.set(token, userId);
  }

  get rowCount(): number {
    return this.rows.size;
  }

  rowsFor(userId: string) {
    return [...this.rows.values()].filter((row) => row.user === userId);
  }

  readonly fetch: PocketBaseFetchLike = async (url, init) => {
    const parsed = new URL(url);
    const request: FakeRequest = {
      method: init.method,
      path: parsed.pathname,
      query: parsed.searchParams,
      headers: init.headers,
      ...(init.body ? { body: JSON.parse(init.body) as Record<string, unknown> } : {}),
    };
    this.requests.push(request);

    const userId = this.users.get(init.headers.Authorization ?? '');
    if (!userId) return { status: 401, body: { code: 401, message: 'unauthorized', data: {} } };

    if (request.method === 'POST' && request.path === '/api/collections/review_events/records') {
      return this.createRecord(userId, request.body ?? {});
    }
    if (request.method === 'GET' && request.path === '/api/collections/review_events/records') {
      return this.listRecords(userId, request.query);
    }
    return { status: 404, body: { code: 404, message: 'not found', data: {} } };
  };

  private createRecord(userId: string, body: Record<string, unknown>) {
    // The hook overwrites client-sent user/serverSeq/serverReceivedAt; a client
    // that smuggles one in gets the server stamp regardless.
    const eventId = typeof body.eventId === 'string' ? body.eventId : '';
    if (this.rows.has(eventId)) {
      return {
        status: 400,
        body: {
          code: 400,
          message: 'Failed to create record.',
          data: { eventId: { code: 'validation_not_unique', message: 'Value must be unique.' } },
        },
      };
    }
    const serverSeq = this.nextSeq.get(userId) ?? 1;
    const stamped = toServerReviewEvent(body, serverSeq, SERVER_NOW);
    if (!stamped) {
      return { status: 400, body: { code: 400, message: 'Failed to create record.', data: {} } };
    }
    this.nextSeq.set(userId, serverSeq + 1);
    this.rows.set(stamped.eventId, { ...stamped, user: userId });
    return { status: 200, body: this.rows.get(stamped.eventId) };
  }

  private listRecords(userId: string, query: URLSearchParams) {
    const filter = query.get('filter') ?? '';
    const match = /^serverSeq > (\d+)$/.exec(filter);
    const since = match ? Number(match[1]) : 0;
    const perPage = Number(query.get('perPage') ?? '30');
    const due = this.rowsFor(userId)
      .filter((row) => row.serverSeq > since)
      .sort((left, right) => left.serverSeq - right.serverSeq);
    const items = due.slice(0, perPage);
    const totalPages = Math.max(1, Math.ceil(due.length / perPage));
    return { status: 200, body: { page: 1, perPage, totalItems: due.length, totalPages, items } };
  }
}

function makeAdapter(fake: FakePocketBase, token = 'token-user-a', pageSize = 2) {
  return new PocketBaseReviewEventAdapter({
    baseUrl: 'http://127.0.0.1:8090/',
    authToken: token,
    fetch: fake.fetch,
    pageSize,
  });
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

describe('PocketBaseReviewEventAdapter.push', () => {
  test('creates rows without a client-side userId and ACKs per eventId', async () => {
    const fake = new FakePocketBase();
    fake.registerUser('token-user-a', 'user-a');
    const device = new MemoryStorage();
    record(device, 'книга', 'flashcards', 'good', SERVER_NOW - 60 * 1000);
    const adapter = makeAdapter(fake);

    const events = loadReviewEventLog(device).events;
    const ack = await adapter.push(events);
    expect(ack.ackedEventIds).toEqual(events.map((event) => event.eventId));
    expect(fake.rowCount).toBe(1);

    const post = fake.requests.find((request) => request.method === 'POST');
    expect(post?.body).not.toHaveProperty('user');
    expect(post?.body).not.toHaveProperty('serverSeq');
    expect(post?.body).not.toHaveProperty('serverReceivedAt');
    // The server scopes by the auth token, not by anything the client sent.
    expect(fake.rowsFor('user-a')).toHaveLength(1);
  });

  test('a duplicate eventId is an idempotent ACK, not an error', async () => {
    const fake = new FakePocketBase();
    fake.registerUser('token-user-a', 'user-a');
    const adapter = makeAdapter(fake);
    const device = new MemoryStorage();
    record(device, 'книга', 'flashcards', 'good', SERVER_NOW - 60 * 1000);
    const events = loadReviewEventLog(device).events;

    await adapter.push(events);
    const again = await adapter.push(events);
    expect(again.ackedEventIds).toEqual(events.map((event) => event.eventId));
    expect(fake.rowCount).toBe(1);
    // First ingest fixed the stamps; the duplicate did not move them.
    expect(fake.rowsFor('user-a')[0]).toMatchObject({ serverSeq: 1, serverReceivedAt: SERVER_NOW });
  });

  test('a non-duplicate failure throws so the backlog survives to the next round', async () => {
    const fake = new FakePocketBase();
    fake.registerUser('token-user-a', 'user-a');
    const adapter = makeAdapter(fake);
    const bad = { eventId: 'not-a-ulid' } as unknown as ReviewEvent;
    await expect(adapter.push([bad])).rejects.toThrow('HTTP 400');
  });

  test('an unauthenticated adapter gets 401 and ACKs nothing', async () => {
    const fake = new FakePocketBase();
    const device = new MemoryStorage();
    record(device, 'книга', 'flashcards', 'good', SERVER_NOW - 60 * 1000);
    const adapter = makeAdapter(fake, 'token-unknown');
    await expect(adapter.push(loadReviewEventLog(device).events)).rejects.toThrow('HTTP 401');
  });
});

describe('PocketBaseReviewEventAdapter.pull', () => {
  test('pages strictly past the serverSeq cursor, oldest first', async () => {
    const fake = new FakePocketBase();
    fake.registerUser('token-user-a', 'user-a');
    const device = new MemoryStorage();
    for (let index = 0; index < 5; index += 1) {
      record(device, `lemma-${index}`, 'flashcards', 'good', SERVER_NOW - (5 - index) * 60 * 1000);
    }
    const adapter = makeAdapter(fake, 'token-user-a', /* pageSize */ 2);
    await adapter.push(loadReviewEventLog(device).events);

    const first = await adapter.pull(0);
    expect(first.events.map((event) => event.serverSeq)).toEqual([1, 2]);
    expect(first.upToServerSeq).toBe(2);
    expect(first.hasMore).toBe(true);

    const second = await adapter.pull(first.upToServerSeq);
    expect(second.events.map((event) => event.serverSeq)).toEqual([3, 4]);

    const third = await adapter.pull(second.upToServerSeq);
    expect(third.events.map((event) => event.serverSeq)).toEqual([5]);
    expect(third.hasMore).toBe(false);

    const exhausted = await adapter.pull(5);
    expect(exhausted).toMatchObject({ events: [], upToServerSeq: 5, hasMore: false });
    const filter = fake.requests.at(-1)?.query.get('filter');
    expect(filter).toBe('serverSeq > 5');
  });

  test('never returns another user’s rows', async () => {
    const fake = new FakePocketBase();
    fake.registerUser('token-user-a', 'user-a');
    fake.registerUser('token-user-b', 'user-b');
    const device = new MemoryStorage();
    record(device, 'книга', 'flashcards', 'good', SERVER_NOW - 60 * 1000);
    await makeAdapter(fake, 'token-user-a').push(loadReviewEventLog(device).events);

    const page = await makeAdapter(fake, 'token-user-b').pull(0);
    expect(page.events).toEqual([]);
    expect(page.hasMore).toBe(false);
  });
});

describe('two offline devices converge through the real adapter', () => {
  test('same-card conflict + fast clock → one log, one FSRS fold', async () => {
    // Same scenario shape as review-event-sync.test.ts: both devices reviewed
    // offline — same card on both plus device-only cards; B's clock runs 1h
    // fast and gets clamped by the server stamp.
    const deviceA = new MemoryStorage();
    const deviceB = new MemoryStorage();
    record(deviceA, 'книга', 'flashcards', 'good', SERVER_NOW - 3 * 60 * 1000, 'client-device-a');
    record(deviceA, 'книга', 'cloze', 'again', SERVER_NOW - 2 * 60 * 1000, 'client-device-a');
    record(deviceA, 'слово', 'flashcards', 'hard', SERVER_NOW - 60 * 1000, 'client-device-a');
    record(deviceB, 'книга', 'flashcards', 'hard', SERVER_NOW + 15 * 60 * 1000, 'client-device-b');
    record(deviceB, 'місто', 'matching', 'easy', SERVER_NOW + 60 * 60 * 1000, 'client-device-b');

    const fake = new FakePocketBase();
    fake.registerUser('token-user-a', 'user-a');
    const adapter = makeAdapter(fake);

    await runReviewEventSync(adapter, deviceA, { now: () => SERVER_NOW });
    const bFirst = await runReviewEventSync(adapter, deviceB, { now: () => SERVER_NOW });
    // B pulls A's 3 events in AND the server-clamped copies of its own 2.
    expect(bFirst.mergedAdded).toBe(3);
    expect(bFirst.mergedReplaced).toBe(2);
    const aSecond = await runReviewEventSync(adapter, deviceA, { now: () => SERVER_NOW });
    expect(aSecond.mergedAdded).toBe(2);
    await runReviewEventSync(adapter, deviceB, { now: () => SERVER_NOW });

    const eventsA = logEvents(deviceA);
    const eventsB = logEvents(deviceB);
    expect(eventsA).toEqual(eventsB);
    expect(eventsA).toHaveLength(5);
    // B's fast-clock event was clamped to the server ingest time on both devices.
    expect(eventsA.find((event) => event.lemmaId === 'місто')?.reviewedAt).toBe(SERVER_NOW);

    expect(uniformFsrsParamsVersion(eventsA)).not.toBeNull();
    expect(folded(deviceA)).toEqual(folded(deviceB));
    // …and equals a single-device fold of the union — no LWW fork.
    expect(folded(deviceA)).toEqual(
      Object.fromEntries([...foldReviewEventsToCards(canonicalReplayOrder([...eventsA]))]),
    );

    // Steady state: a fourth round moves nothing.
    const idle = await runReviewEventSync(adapter, deviceA, { now: () => SERVER_NOW });
    expect(idle).toMatchObject({ pushed: 0, acked: 0, pulled: 0, lastServerSeq: 5 });
  });
});

describe('exportUserEventsJson + importReviewEventExport (§10.2 export contract)', () => {
  test('the server log exports as one JSON document a fresh device restores with fold parity', async () => {
    const fake = new FakePocketBase();
    fake.registerUser('token-user-a', 'user-a');
    const adapter = makeAdapter(fake, 'token-user-a', /* pageSize */ 1); // force paging
    const source = new MemoryStorage();
    record(source, 'книга', 'flashcards', 'good', SERVER_NOW - 3 * 60 * 1000);
    record(source, 'книга', 'cloze', 'again', SERVER_NOW - 2 * 60 * 1000);
    record(source, 'мир', 'matching', 'easy', SERVER_NOW - 60 * 1000);
    await runReviewEventSync(adapter, source, { now: () => SERVER_NOW });

    const exported = JSON.parse(JSON.stringify(await adapter.exportUserEventsJson(SERVER_NOW))) as unknown;
    const doc = exported as { schema: string; clientId: string; fsrsParamsVersion: number };
    expect(doc.schema).toBe(REVIEW_EVENTS_SCHEMA);
    expect(doc.clientId).toBe(POCKETBASE_EXPORT_CLIENT_ID);
    expect(doc.fsrsParamsVersion).toBe(1);

    const target = new MemoryStorage();
    const result = importReviewEventExport(exported, target);
    expect(result).toEqual({ added: 3, replaced: 0, skipped: 0 });
    expect(logEvents(target)).toEqual(logEvents(source));
    expect(folded(target)).toEqual(folded(source));
  });
});

describe('adapter wiring (static path default)', () => {
  test('no base URL or no token ⇒ null ⇒ offline', () => {
    expect(pocketBaseAdapterFromEnv(undefined, 'token')).toBeNull();
    expect(pocketBaseAdapterFromEnv({}, 'token')).toBeNull();
    expect(pocketBaseAdapterFromEnv({ [POCKETBASE_BASE_URL_ENV]: 'http://127.0.0.1:8090' })).toBeNull();
    expect(pocketBaseAdapterFromEnv({ [POCKETBASE_BASE_URL_ENV]: '  ' }, 'token')).toBeNull();
  });

  test('configured env + token yields an adapter against the configured host', async () => {
    const fake = new FakePocketBase();
    fake.registerUser('token-user-a', 'user-a');
    const adapter = pocketBaseAdapterFromEnv(
      { [POCKETBASE_BASE_URL_ENV]: 'http://127.0.0.1:8090' },
      'token-user-a',
      { fetch: fake.fetch },
    );
    expect(adapter).not.toBeNull();
    if (!adapter) throw new Error('adapter missing');
    const page = await adapter.pull(0);
    expect(page).toMatchObject({ events: [], upToServerSeq: 0, hasMore: false });
    expect(fake.requests[0].path).toBe('/api/collections/review_events/records');
  });
});
