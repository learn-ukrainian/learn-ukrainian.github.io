/**
 * Practice Hub §10.1 review-event log — client-side, no backend.
 *
 * Spec (`docs/poc/word-atlas/PRACTICE-HUB-SPEC.md` §10.1): do not sync derived
 * FSRS card state. Append `ReviewEvent`s locally so a later account can
 * backfill; fold the log to recover scheduler state. Offline-only today —
 * no auth, host, or vendor.
 */

import {
  createEmptyCard,
  fsrs,
  Rating,
  type Card as FsrsCard,
  type FSRSParameters,
  type Grade,
} from 'ts-fsrs';
import type { PracticeMode, PracticeRating } from './srs';

export const REVIEW_EVENTS_STORAGE_KEY = 'lu-practice-review-events';
export const REVIEW_EVENTS_SCHEMA = 'practice-hub.review-events.v1';
export const REVIEW_EVENTS_SCHEMA_VERSION = 1;
/** Pins replay to the same FSRS parameter generation as `SrsSettings.version`. */
export const FSRS_PARAMS_VERSION = 1;
/** Shared with custom-decks `DEVICE_ID_KEY` so one browser has one client id. */
export const REVIEW_EVENT_CLIENT_ID_KEY = 'learn_ukrainian_device_id';

const ULID_ALPHABET = '0123456789ABCDEFGHJKMNPQRSTVWXYZ';
const ULID_PATTERN = /^[0-9A-HJKMNP-TV-Z]{26}$/;
const RATINGS = new Set<PracticeRating>(['again', 'hard', 'good', 'easy']);
const RATING_TO_FSRS: Record<PracticeRating, Grade> = {
  again: Rating.Again,
  hard: Rating.Hard,
  good: Rating.Good,
  easy: Rating.Easy,
};

export interface ReviewEventPresentation {
  slotId?: string;
  clozeId?: string;
  polarity?: string;
  optionSetId?: string;
}

export interface ReviewEvent {
  eventId: string;
  lemmaId: string;
  mode: PracticeMode;
  rating: PracticeRating;
  reviewedAt: number;
  deckVersion: number;
  clientId: string;
  fsrsParamsVersion: number;
  presentation?: ReviewEventPresentation;
}

export interface ReviewEventLog {
  schema: typeof REVIEW_EVENTS_SCHEMA;
  schemaVersion: typeof REVIEW_EVENTS_SCHEMA_VERSION;
  clientId: string;
  fsrsParamsVersion: number;
  events: ReviewEvent[];
}

export interface ReviewEventExport {
  schema: typeof REVIEW_EVENTS_SCHEMA;
  exportedAt: number;
  clientId: string;
  fsrsParamsVersion: number;
  events: ReviewEvent[];
}

export interface ReviewEventStorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

export interface FoldedCardState {
  due: number;
  stability: number;
  difficulty: number;
  elapsed_days: number;
  scheduled_days: number;
  learning_steps: number;
  reps: number;
  lapses: number;
  state: number;
  last_review?: number;
}

export interface RecordReviewEventInput {
  lemmaId: string;
  mode: PracticeMode;
  rating: PracticeRating;
  reviewedAt: Date | number;
  deckVersion: number;
  presentation?: ReviewEventPresentation;
  eventId?: string;
  clientId?: string;
  fsrsParamsVersion?: number;
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

let lastUlidTime = -1;
let lastUlidRandom: Uint8Array | null = null;
let inMemoryClientId: string | null = null;

function resolveStorage(): ReviewEventStorageLike {
  if (typeof window === 'undefined') return memoryStorage;
  try {
    const storage = window.localStorage;
    void storage.getItem('__lu_review_events_probe__');
    return storage;
  } catch {
    return memoryStorage;
  }
}

function encodeCrockford(value: bigint, length: number): string {
  let remaining = value;
  let encoded = '';
  for (let index = 0; index < length; index += 1) {
    encoded = ULID_ALPHABET[Number(remaining & 31n)] + encoded;
    remaining >>= 5n;
  }
  return encoded;
}

function incrementBytes(bytes: Uint8Array): void {
  for (let index = bytes.length - 1; index >= 0; index -= 1) {
    const next = (bytes[index] + 1) & 0xff;
    bytes[index] = next;
    if (next !== 0) return;
  }
}

function fillRandomBytes(bytes: Uint8Array, random?: () => number): void {
  if (random) {
    for (let index = 0; index < bytes.length; index += 1) {
      bytes[index] = Math.floor(random() * 256) & 0xff;
    }
    return;
  }
  const cryptoRef = globalThis.crypto;
  if (cryptoRef && typeof cryptoRef.getRandomValues === 'function') {
    cryptoRef.getRandomValues(bytes);
    return;
  }
  for (let index = 0; index < bytes.length; index += 1) {
    bytes[index] = Math.floor(Math.random() * 256) & 0xff;
  }
}

/** Crockford ULID; monotonic within the same millisecond. */
export function mintUlid(nowMs: number, random?: () => number): string {
  const time = Math.max(0, Math.floor(nowMs));
  const entropy = new Uint8Array(10);
  if (time === lastUlidTime && lastUlidRandom) {
    entropy.set(lastUlidRandom);
    incrementBytes(entropy);
  } else {
    fillRandomBytes(entropy, random);
  }
  lastUlidTime = time;
  lastUlidRandom = entropy.slice();

  let randomValue = 0n;
  for (const byte of entropy) {
    randomValue = (randomValue << 8n) | BigInt(byte);
  }
  return `${encodeCrockford(BigInt(time), 10)}${encodeCrockford(randomValue, 16)}`;
}

export function resetReviewEventEntropy(): void {
  lastUlidTime = -1;
  lastUlidRandom = null;
}

function newClientId(): string {
  if (!inMemoryClientId) {
    inMemoryClientId = mintUlid(Date.now());
  }
  return inMemoryClientId;
}

export function getReviewEventClientId(storage: ReviewEventStorageLike = resolveStorage()): string {
  try {
    const stored = storage.getItem(REVIEW_EVENT_CLIENT_ID_KEY);
    if (stored && stored.trim()) return stored;
    const clientId = newClientId();
    storage.setItem(REVIEW_EVENT_CLIENT_ID_KEY, clientId);
    return clientId;
  } catch {
    return newClientId();
  }
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.length > 0;
}

function isPracticeRating(value: unknown): value is PracticeRating {
  return typeof value === 'string' && RATINGS.has(value as PracticeRating);
}

function normalizePresentation(raw: unknown): ReviewEventPresentation | undefined {
  if (!raw || typeof raw !== 'object') return undefined;
  const source = raw as Record<string, unknown>;
  const presentation: ReviewEventPresentation = {};
  if (isNonEmptyString(source.slotId)) presentation.slotId = source.slotId;
  if (isNonEmptyString(source.clozeId)) presentation.clozeId = source.clozeId;
  if (isNonEmptyString(source.polarity)) presentation.polarity = source.polarity;
  if (isNonEmptyString(source.optionSetId)) presentation.optionSetId = source.optionSetId;
  return presentation.slotId || presentation.clozeId || presentation.polarity || presentation.optionSetId
    ? presentation
    : undefined;
}

export function normalizeReviewEvent(raw: unknown): ReviewEvent | null {
  if (!raw || typeof raw !== 'object') return null;
  const source = raw as Record<string, unknown>;
  if (typeof source.eventId !== 'string' || !ULID_PATTERN.test(source.eventId)) return null;
  if (!isNonEmptyString(source.lemmaId) || !isNonEmptyString(source.mode)) return null;
  if (!isPracticeRating(source.rating)) return null;
  if (typeof source.reviewedAt !== 'number' || !Number.isFinite(source.reviewedAt)) return null;
  if (typeof source.deckVersion !== 'number' || !Number.isFinite(source.deckVersion)) return null;
  if (!isNonEmptyString(source.clientId)) return null;
  const fsrsParamsVersion =
    typeof source.fsrsParamsVersion === 'number' && Number.isFinite(source.fsrsParamsVersion)
      ? source.fsrsParamsVersion
      : FSRS_PARAMS_VERSION;
  const presentation = normalizePresentation(source.presentation);
  return {
    eventId: source.eventId,
    lemmaId: source.lemmaId,
    mode: source.mode as PracticeMode,
    rating: source.rating,
    reviewedAt: source.reviewedAt,
    deckVersion: source.deckVersion,
    clientId: source.clientId,
    fsrsParamsVersion,
    ...(presentation ? { presentation } : {}),
  };
}

function emptyLog(clientId: string): ReviewEventLog {
  return {
    schema: REVIEW_EVENTS_SCHEMA,
    schemaVersion: REVIEW_EVENTS_SCHEMA_VERSION,
    clientId,
    fsrsParamsVersion: FSRS_PARAMS_VERSION,
    events: [],
  };
}

export function loadReviewEventLog(
  storage: ReviewEventStorageLike = resolveStorage(),
): ReviewEventLog {
  const clientId = getReviewEventClientId(storage);
  let raw: string | null;
  try {
    raw = storage.getItem(REVIEW_EVENTS_STORAGE_KEY);
  } catch {
    return emptyLog(clientId);
  }
  if (!raw) return emptyLog(clientId);
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    if (!Array.isArray(parsed.events)) return emptyLog(clientId);
    const events: ReviewEvent[] = [];
    for (const item of parsed.events) {
      const event = normalizeReviewEvent(item);
      if (event) events.push(event);
    }
    return {
      schema: REVIEW_EVENTS_SCHEMA,
      schemaVersion: REVIEW_EVENTS_SCHEMA_VERSION,
      clientId: isNonEmptyString(parsed.clientId) ? parsed.clientId : clientId,
      fsrsParamsVersion:
        typeof parsed.fsrsParamsVersion === 'number' && Number.isFinite(parsed.fsrsParamsVersion)
          ? parsed.fsrsParamsVersion
          : FSRS_PARAMS_VERSION,
      events,
    };
  } catch {
    return emptyLog(clientId);
  }
}

function persistLog(log: ReviewEventLog, storage: ReviewEventStorageLike): boolean {
  try {
    storage.setItem(REVIEW_EVENTS_STORAGE_KEY, JSON.stringify(log));
    return true;
  } catch {
    return false;
  }
}

/** Set-union on `eventId`. Existing ids are left unchanged (append-only). */
export function upsertReviewEvents(
  incoming: readonly ReviewEvent[],
  storage: ReviewEventStorageLike = resolveStorage(),
): { added: number; log: ReviewEventLog } {
  const log = loadReviewEventLog(storage);
  const seen = new Set(log.events.map((event) => event.eventId));
  let added = 0;
  for (const raw of incoming) {
    const event = normalizeReviewEvent(raw);
    if (!event || seen.has(event.eventId)) continue;
    log.events.push(event);
    seen.add(event.eventId);
    added += 1;
  }
  persistLog(log, storage);
  return { added, log };
}

export function appendReviewEvent(
  event: ReviewEvent,
  storage: ReviewEventStorageLike = resolveStorage(),
): ReviewEvent | null {
  const normalized = normalizeReviewEvent(event);
  if (!normalized) return null;
  upsertReviewEvents([normalized], storage);
  return normalized;
}

export function recordCardReviewEvent(
  input: RecordReviewEventInput,
  storage: ReviewEventStorageLike = resolveStorage(),
): ReviewEvent | null {
  const reviewedAt =
    input.reviewedAt instanceof Date ? input.reviewedAt.getTime() : input.reviewedAt;
  if (!Number.isFinite(reviewedAt)) return null;
  const event: ReviewEvent = {
    eventId: input.eventId ?? mintUlid(reviewedAt),
    lemmaId: input.lemmaId,
    mode: input.mode,
    rating: input.rating,
    reviewedAt,
    deckVersion: input.deckVersion,
    clientId: input.clientId ?? getReviewEventClientId(storage),
    fsrsParamsVersion: input.fsrsParamsVersion ?? FSRS_PARAMS_VERSION,
    ...(input.presentation ? { presentation: input.presentation } : {}),
  };
  return appendReviewEvent(event, storage);
}

export function exportReviewEventLog(
  storage: ReviewEventStorageLike = resolveStorage(),
  exportedAt: number = Date.now(),
): ReviewEventExport {
  const log = loadReviewEventLog(storage);
  return {
    schema: REVIEW_EVENTS_SCHEMA,
    exportedAt,
    clientId: log.clientId,
    fsrsParamsVersion: log.fsrsParamsVersion,
    events: canonicalReplayOrder(log.events),
  };
}

/** Local replay order: `(reviewedAt, eventId)`. Server clamp is a later slice. */
export function canonicalReplayOrder(events: readonly ReviewEvent[]): ReviewEvent[] {
  return [...events].sort((left, right) => {
    if (left.reviewedAt !== right.reviewedAt) return left.reviewedAt - right.reviewedAt;
    return left.eventId < right.eventId ? -1 : left.eventId > right.eventId ? 1 : 0;
  });
}

export function reviewEventCardKey(lemmaId: string, mode: PracticeMode): string {
  return `${lemmaId}::${mode}`;
}

function cardFromFsrs(card: FsrsCard): FoldedCardState {
  return {
    due: card.due.getTime(),
    stability: card.stability,
    difficulty: card.difficulty,
    elapsed_days: card.elapsed_days,
    scheduled_days: card.scheduled_days,
    learning_steps: card.learning_steps,
    reps: card.reps,
    lapses: card.lapses,
    state: card.state,
    ...(card.last_review ? { last_review: card.last_review.getTime() } : {}),
  };
}

function fsrsFromFolded(card: FoldedCardState): FsrsCard {
  return {
    due: new Date(card.due),
    stability: card.stability,
    difficulty: card.difficulty,
    elapsed_days: card.elapsed_days,
    scheduled_days: card.scheduled_days,
    learning_steps: card.learning_steps,
    reps: card.reps,
    lapses: card.lapses,
    state: card.state,
    ...(card.last_review === undefined ? {} : { last_review: new Date(card.last_review) }),
  };
}

/**
 * Deterministic FSRS-6 fold. Same log + same params → same cards on every device.
 */
export function foldReviewEventsToCards(
  events: readonly ReviewEvent[],
  params?: FSRSParameters,
): Map<string, FoldedCardState> {
  const scheduler = params ? fsrs(params) : fsrs();
  const cards = new Map<string, FoldedCardState>();
  for (const event of canonicalReplayOrder(events)) {
    const key = reviewEventCardKey(event.lemmaId, event.mode);
    const reviewDate = new Date(event.reviewedAt);
    const current = cards.get(key);
    const fsrsCard = current ? fsrsFromFolded(current) : createEmptyCard(reviewDate);
    const record = scheduler.next(fsrsCard, reviewDate, RATING_TO_FSRS[event.rating]);
    cards.set(key, cardFromFsrs(record.card));
  }
  return cards;
}

export function clearReviewEventLog(storage: ReviewEventStorageLike = resolveStorage()): void {
  try {
    storage.removeItem(REVIEW_EVENTS_STORAGE_KEY);
  } catch {
    // Best-effort: the next load treats missing/unreadable storage as empty.
  }
}
