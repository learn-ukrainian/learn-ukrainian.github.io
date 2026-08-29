/**
 * Practice Hub §10.1 sync contract — client-side, no backend.
 *
 * Spec (`docs/poc/word-atlas/PRACTICE-HUB-SPEC.md` §10.1, ⟦codex v4⟧ items):
 * sync the append-only review-event log, never derived FSRS state. Upload is
 * an idempotent push ACKed per `eventId`; download pages by the
 * server-assigned monotonic `serverSeq` cursor (never a `reviewedAt` cursor,
 * which would lose late-arriving offline events). Client clocks are validated,
 * not trusted: a `reviewedAt` in the future of `serverReceivedAt` (beyond a
 * skew window) or absurdly old is clamped, and every device folds the clamped
 * events ordered by `(clampedReviewedAt, eventId)`.
 *
 * The `ReviewEventSyncAdapter` interface is the seam a future backend (Pocket
 * Base, Drive, …) implements; its ingest stamping must match
 * `toServerReviewEvent`. No adapter ships here — offline today, no auth, host,
 * or vendor. `importReviewEventExport` is the client half of the §10.2 export
 * + documented-restore contract.
 */

import {
  REVIEW_EVENTS_SCHEMA,
  REVIEW_EVENTS_STORAGE_KEY,
  loadReviewEventLog,
  normalizeReviewEvent,
  type ReviewEvent,
  type ReviewEventStorageLike,
} from './review-events';

export const REVIEW_EVENT_SYNC_STORAGE_KEY = 'lu-practice-review-events-sync';
export const REVIEW_EVENT_SYNC_SCHEMA = 'practice-hub.review-events-sync.v1';
export const REVIEW_EVENT_SYNC_SCHEMA_VERSION = 1;

/** ⟦codex v4⟧ clock policy — how far a client `reviewedAt` may deviate. */
export interface ReviewEventClockPolicy {
  /** `reviewedAt` above `serverReceivedAt + futureSkewMs` is clamped. */
  futureSkewMs: number;
  /** `reviewedAt` below `serverReceivedAt - maxAgeMs` is "absurdly old", clamped. */
  maxAgeMs: number;
}

export const DEFAULT_REVIEW_EVENT_CLOCK_POLICY: ReviewEventClockPolicy = {
  futureSkewMs: 5 * 60 * 1000,
  maxAgeMs: 366 * 24 * 60 * 60 * 1000,
};

/** A `ReviewEvent` as stamped by the server at ingest: clamped + sequenced. */
export interface ServerReviewEvent extends ReviewEvent {
  /** Server-assigned monotonic ingest sequence — the pull cursor. */
  serverSeq: number;
  /** Server ingest time — the clamp reference. */
  serverReceivedAt: number;
}

export interface ReviewEventPushAck {
  ackedEventIds: readonly string[];
}

export interface ReviewEventPullPage {
  events: readonly ServerReviewEvent[];
  /** Highest `serverSeq` covered by this page; the cursor advances to it. */
  upToServerSeq: number;
  hasMore: boolean;
}

/**
 * Backend-adapter contract (§10.2: the event log is portable; auth/rules/admin
 * are not). `push` upserts per `eventId` (idempotent) and ACKs what the server
 * holds; `pull` returns events with `serverSeq` strictly greater than the
 * cursor, oldest first.
 */
export interface ReviewEventSyncAdapter {
  push(events: readonly ReviewEvent[]): Promise<ReviewEventPushAck>;
  pull(sinceServerSeq: number): Promise<ReviewEventPullPage>;
}

export interface ReviewEventSyncState {
  schema: typeof REVIEW_EVENT_SYNC_SCHEMA;
  schemaVersion: typeof REVIEW_EVENT_SYNC_SCHEMA_VERSION;
  lastServerSeq: number;
  /** Push backlog: local eventIds the server has not ACKed yet. */
  pendingEventIds: string[];
  lastSyncedAt?: number;
}

export interface ReviewEventSyncResult {
  pushed: number;
  acked: number;
  pulled: number;
  mergedAdded: number;
  mergedReplaced: number;
  lastServerSeq: number;
}

export interface ReviewEventMergeResult {
  added: number;
  replaced: number;
}

export interface ReviewEventImportResult {
  added: number;
  replaced: number;
  skipped: number;
}

const memoryStore = new Map<string, string>();
const memoryStorage: ReviewEventStorageLike = {
  getItem: (key) => memoryStore.get(key) ?? null,
  setItem: (key, value) => {
    memoryStore.set(key, value);
  },
  removeItem: (key) => {
    memoryStore.delete(key);
  },
};

function resolveStorage(): ReviewEventStorageLike {
  if (typeof window === 'undefined') return memoryStorage;
  try {
    const storage = window.localStorage;
    void storage.getItem('__lu_review_event_sync_probe__');
    return storage;
  } catch {
    return memoryStorage;
  }
}

/** Clamp a client `reviewedAt` against the server ingest time (⟦codex v4⟧). */
export function clampReviewEventTime(
  reviewedAt: number,
  serverReceivedAt: number,
  policy: ReviewEventClockPolicy = DEFAULT_REVIEW_EVENT_CLOCK_POLICY,
): number {
  if (!Number.isFinite(reviewedAt) || !Number.isFinite(serverReceivedAt)) {
    return serverReceivedAt;
  }
  if (reviewedAt > serverReceivedAt + policy.futureSkewMs) return serverReceivedAt;
  if (reviewedAt < serverReceivedAt - policy.maxAgeMs) return serverReceivedAt;
  return reviewedAt;
}

/**
 * Ingest stamping every adapter must reproduce: normalize, clamp the client
 * clock, stamp `serverSeq` + `serverReceivedAt`. Returns `null` when the event
 * (or its stamps) fail validation — fail-closed, never emitted.
 */
export function toServerReviewEvent(
  event: unknown,
  serverSeq: number,
  serverReceivedAt: number,
  policy: ReviewEventClockPolicy = DEFAULT_REVIEW_EVENT_CLOCK_POLICY,
): ServerReviewEvent | null {
  const normalized = normalizeReviewEvent(event);
  if (!normalized) return null;
  if (!Number.isFinite(serverSeq) || serverSeq < 0) return null;
  if (!Number.isFinite(serverReceivedAt)) return null;
  return {
    ...normalized,
    reviewedAt: clampReviewEventTime(normalized.reviewedAt, serverReceivedAt, policy),
    serverSeq,
    serverReceivedAt,
  };
}

function samePresentation(
  left: ReviewEvent['presentation'],
  right: ReviewEvent['presentation'],
): boolean {
  if (!left || !right) return !left && !right;
  return (
    left.slotId === right.slotId &&
    left.clozeId === right.clozeId &&
    left.polarity === right.polarity &&
    left.optionSetId === right.optionSetId
  );
}

function sameReviewEvent(left: ReviewEvent, right: ReviewEvent): boolean {
  return (
    left.lemmaId === right.lemmaId &&
    left.mode === right.mode &&
    left.rating === right.rating &&
    left.reviewedAt === right.reviewedAt &&
    left.deckVersion === right.deckVersion &&
    left.clientId === right.clientId &&
    left.fsrsParamsVersion === right.fsrsParamsVersion &&
    samePresentation(left.presentation, right.presentation)
  );
}

/**
 * Merge server-canonical events into the local log. Set-union on `eventId`;
 * when the same id carries different fields locally, the server copy wins —
 * the clamped/stamped copy is the replay authority (§10.1), so every device
 * converges on identical bytes.
 */
export function mergeServerReviewEvents(
  incoming: readonly ServerReviewEvent[],
  storage: ReviewEventStorageLike = resolveStorage(),
): ReviewEventMergeResult {
  const log = loadReviewEventLog(storage);
  const byId = new Map(log.events.map((event) => [event.eventId, event]));
  let added = 0;
  let replaced = 0;
  for (const raw of incoming) {
    const event = normalizeReviewEvent(raw);
    if (!event) continue;
    const existing = byId.get(event.eventId);
    if (!existing) {
      byId.set(event.eventId, event);
      log.events.push(event);
      added += 1;
    } else if (!sameReviewEvent(existing, event)) {
      byId.set(event.eventId, event);
      const index = log.events.findIndex((candidate) => candidate.eventId === event.eventId);
      log.events[index] = event;
      replaced += 1;
    }
  }
  if (added || replaced) {
    try {
      storage.setItem(REVIEW_EVENTS_STORAGE_KEY, JSON.stringify(log));
    } catch {
      // Storage unavailable: fold falls back to the previously persisted log.
    }
  }
  return { added, replaced };
}

function freshSyncState(): ReviewEventSyncState {
  return {
    schema: REVIEW_EVENT_SYNC_SCHEMA,
    schemaVersion: REVIEW_EVENT_SYNC_SCHEMA_VERSION,
    lastServerSeq: 0,
    pendingEventIds: [],
  };
}

/** Returns `null` when no persisted state exists (first sync — see §10.3 backfill). */
function readSyncState(storage: ReviewEventStorageLike): ReviewEventSyncState | null {
  let raw: string | null;
  try {
    raw = storage.getItem(REVIEW_EVENT_SYNC_STORAGE_KEY);
  } catch {
    return null;
  }
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    if (typeof parsed.lastServerSeq !== 'number' || !Number.isFinite(parsed.lastServerSeq) || parsed.lastServerSeq < 0) {
      return null;
    }
    if (!Array.isArray(parsed.pendingEventIds)) return null;
    const pendingEventIds = parsed.pendingEventIds.filter(
      (id): id is string => typeof id === 'string' && id.length > 0,
    );
    const state = freshSyncState();
    state.lastServerSeq = Math.floor(parsed.lastServerSeq);
    state.pendingEventIds = pendingEventIds;
    if (typeof parsed.lastSyncedAt === 'number' && Number.isFinite(parsed.lastSyncedAt)) {
      state.lastSyncedAt = parsed.lastSyncedAt;
    }
    return state;
  } catch {
    return null;
  }
}

export function loadReviewEventSyncState(
  storage: ReviewEventStorageLike = resolveStorage(),
): ReviewEventSyncState {
  return readSyncState(storage) ?? freshSyncState();
}

function persistSyncState(state: ReviewEventSyncState, storage: ReviewEventStorageLike): boolean {
  try {
    storage.setItem(REVIEW_EVENT_SYNC_STORAGE_KEY, JSON.stringify(state));
    return true;
  } catch {
    return false;
  }
}

export interface RunReviewEventSyncOptions {
  clockPolicy?: ReviewEventClockPolicy;
  /** Push chunk size — the first-sync backfill is chunked, not one request. */
  pushBatchSize?: number;
  /** Safety bound on pull pages per run. */
  maxPullPages?: number;
  /** Clock for `lastSyncedAt` bookkeeping only. */
  now?: () => number;
}

/**
 * One sync round: push the unACKed backlog, then pull everything past the
 * `serverSeq` cursor and merge it. Crash-safe by construction — the log merge
 * persists before the cursor, so an interrupted run re-pulls and re-merges
 * idempotently; a partial push persists nothing until ACKs arrive, so
 * unACKed events re-push.
 */
export async function runReviewEventSync(
  adapter: ReviewEventSyncAdapter,
  storage: ReviewEventStorageLike = resolveStorage(),
  options: RunReviewEventSyncOptions = {},
): Promise<ReviewEventSyncResult> {
  const stored = readSyncState(storage);
  const log = loadReviewEventLog(storage);
  // First sync: the whole local history is the upload backlog (§10.3 backfill).
  const pending = new Set(stored ? stored.pendingEventIds : log.events.map((event) => event.eventId));

  let pushed = 0;
  let acked = 0;
  const batchSize = options.pushBatchSize ?? 500;
  let queue = log.events.filter((event) => pending.has(event.eventId));
  while (queue.length > 0) {
    const batch = queue.slice(0, batchSize);
    const ack = await adapter.push(batch);
    pushed += batch.length;
    for (const id of ack?.ackedEventIds ?? []) {
      if (pending.delete(id)) acked += 1;
    }
    const remaining = queue.filter((event) => pending.has(event.eventId));
    if (remaining.length === queue.length) break; // no progress this round — stop instead of spinning
    queue = remaining;
  }

  let lastServerSeq = stored ? stored.lastServerSeq : 0;
  let pulled = 0;
  let mergedAdded = 0;
  let mergedReplaced = 0;
  const maxPullPages = options.maxPullPages ?? 100;
  for (let page = 0; page < maxPullPages; page += 1) {
    const result = await adapter.pull(lastServerSeq);
    const upToServerSeq = result?.upToServerSeq;
    if (typeof upToServerSeq !== 'number' || !Number.isFinite(upToServerSeq)) break;
    if (result.events.length > 0) {
      const merged = mergeServerReviewEvents(result.events, storage);
      pulled += result.events.length;
      mergedAdded += merged.added;
      mergedReplaced += merged.replaced;
      // Events echoed back by the server are server-held — an implicit ACK.
      for (const event of result.events) {
        if (typeof event.eventId === 'string') pending.delete(event.eventId);
      }
    }
    lastServerSeq = Math.max(lastServerSeq, Math.floor(upToServerSeq));
    if (!result.hasMore) break;
  }

  const state = freshSyncState();
  state.lastServerSeq = lastServerSeq;
  state.pendingEventIds = [...pending];
  const now = options.now?.() ?? Date.now();
  if (Number.isFinite(now)) state.lastSyncedAt = now;
  persistSyncState(state, storage);

  return { pushed, acked, pulled, mergedAdded, mergedReplaced, lastServerSeq };
}

/**
 * Client half of the §10.2 export/restore contract: adopt a
 * `ReviewEventExport` (from `exportReviewEventLog`) into this device's log.
 * `exportedAt` is the trust anchor for the clock policy — a restored event can
 * be neither newer than its export nor absurdly older than the restore. On an
 * id collision the incoming (exported) copy wins, mirroring server merge.
 * Sync state is untouched: any later duplicate push is an idempotent no-op.
 */
export function importReviewEventExport(
  raw: unknown,
  storage: ReviewEventStorageLike = resolveStorage(),
  policy: ReviewEventClockPolicy = DEFAULT_REVIEW_EVENT_CLOCK_POLICY,
): ReviewEventImportResult | null {
  if (!raw || typeof raw !== 'object') return null;
  const source = raw as Record<string, unknown>;
  if (source.schema !== REVIEW_EVENTS_SCHEMA) return null;
  if (!Array.isArray(source.events)) return null;
  if (typeof source.exportedAt !== 'number' || !Number.isFinite(source.exportedAt)) return null;

  const incoming: ServerReviewEvent[] = [];
  let skipped = 0;
  for (const item of source.events) {
    const stamped = toServerReviewEvent(item, 0, source.exportedAt, policy);
    if (stamped) incoming.push(stamped);
    else skipped += 1;
  }
  const merged = mergeServerReviewEvents(incoming, storage);
  return { added: merged.added, replaced: merged.replaced, skipped };
}

/**
 * ⟦codex v4⟧ FSRS params are part of the sync contract: replay pins the
 * version, so a foldable log must be uniform. Returns the shared version, or
 * `null` when the log is empty or mixes versions (the caller must not fold).
 */
export function uniformFsrsParamsVersion(events: readonly ReviewEvent[]): number | null {
  let version: number | null = null;
  for (const event of events) {
    if (version === null) version = event.fsrsParamsVersion;
    else if (version !== event.fsrsParamsVersion) return null;
  }
  return version;
}
