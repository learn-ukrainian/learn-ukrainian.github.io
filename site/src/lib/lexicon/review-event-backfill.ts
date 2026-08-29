/**
 * Practice Hub §10.1 / §10.2 — local FSRS backfill + export restore.
 *
 * #7396 already appends ReviewEvents on `rateCard`. This slice lifts the
 * remaining raw SRS review window into that log and implements the documented
 * JSON import/restore path so a later account can upload pre-login history.
 *
 * No auth, host, PocketBase, Drive, or analytics vendor. Compacted
 * `reviewAggregates` are not invented as events — they are not a replayable
 * history. Cards with no events stay on today's derived SRS state.
 */

import type { FSRSParameters } from 'ts-fsrs';
import type { CardState, PracticeMode, PracticeRating, ReviewLogAggregate, ReviewLogEntry } from './srs';
import {
  FSRS_PARAMS_VERSION,
  REVIEW_EVENTS_SCHEMA,
  canonicalReplayOrder,
  exportReviewEventLog,
  foldReviewEventsToCards,
  getReviewEventClientId,
  loadReviewEventLog,
  mintDeterministicUlid,
  normalizeReviewEvent,
  upsertReviewEvents,
  type FoldedCardState,
  type ReviewEvent,
  type ReviewEventExport,
  type ReviewEventStorageLike,
} from './review-events';

/** §10.1 client-clock skew window (no serverReceivedAt yet). */
export const REVIEW_EVENT_CLOCK_SKEW_MS = 5 * 60 * 1000;
/** §10.1 "absurdly old" clamp — ten years before the receive stamp. */
export const REVIEW_EVENT_MAX_AGE_MS = 10 * 365.25 * 24 * 60 * 60 * 1000;

export interface BackfillFromSrsOptions {
  deckVersion: number;
  fsrsParamsVersion?: number;
  clientId?: string;
}

export interface BackfillFromSrsResult {
  added: number;
  skippedExisting: number;
  skippedAggregateOnly: number;
}

export interface ImportReviewEventExportResult {
  ok: true;
  added: number;
  events: ReviewEvent[];
  export: ReviewEventExport;
}

export interface ImportReviewEventExportError {
  ok: false;
  error: string;
}

export function reviewEventContentKey(
  lemmaId: string,
  mode: PracticeMode,
  rating: PracticeRating,
  reviewedAt: number,
  occurrence: number,
): string {
  return `${lemmaId}\0${mode}\0${rating}\0${reviewedAt}\0${occurrence}`;
}

export function clampReviewedAt(reviewedAt: number, receivedAt: number): number {
  if (!Number.isFinite(reviewedAt) || !Number.isFinite(receivedAt)) return receivedAt;
  if (reviewedAt > receivedAt + REVIEW_EVENT_CLOCK_SKEW_MS) return receivedAt;
  if (reviewedAt < receivedAt - REVIEW_EVENT_MAX_AGE_MS) return receivedAt;
  return reviewedAt;
}

/** Ephemeral copies for fold only — the stored log stays append-only. */
export function eventsWithClampedReviewedAt(
  events: readonly ReviewEvent[],
  receivedAt: number,
): ReviewEvent[] {
  return events.map((event) => {
    const reviewedAt = clampReviewedAt(event.reviewedAt, receivedAt);
    return reviewedAt === event.reviewedAt ? event : { ...event, reviewedAt };
  });
}

function contentKeyWithoutOccurrence(
  lemmaId: string,
  mode: PracticeMode,
  rating: PracticeRating,
  reviewedAt: number,
): string {
  return `${lemmaId}\0${mode}\0${rating}\0${reviewedAt}`;
}

/**
 * Lift raw SRS reviews into the §10.1 log. Idempotent: existing `rateCard`
 * events match by (lemmaId, mode, rating, reviewedAt, occurrence). Deterministic
 * eventIds make a second run a no-op even across storage reloads.
 *
 * `reviewAggregates` are counted, never synthesized — compacted history is not
 * a faithful FSRS sequence.
 */
export function backfillReviewEventsFromSrsReviews(
  reviews: readonly ReviewLogEntry[],
  storage: ReviewEventStorageLike,
  options: BackfillFromSrsOptions,
  aggregates: Record<string, ReviewLogAggregate> = {},
): BackfillFromSrsResult {
  const log = loadReviewEventLog(storage);
  const clientId = options.clientId ?? getReviewEventClientId(storage);
  const fsrsParamsVersion = options.fsrsParamsVersion ?? FSRS_PARAMS_VERSION;
  const existingByBase = new Map<string, number>();
  for (const event of log.events) {
    const base = contentKeyWithoutOccurrence(event.lemmaId, event.mode, event.rating, event.reviewedAt);
    existingByBase.set(base, (existingByBase.get(base) ?? 0) + 1);
  }

  const usedByBase = new Map<string, number>();
  const incoming: ReviewEvent[] = [];
  let skippedExisting = 0;
  const ordered = [...reviews].sort((left, right) => {
    if (left.review !== right.review) return left.review - right.review;
    if (left.lemmaId !== right.lemmaId) return left.lemmaId < right.lemmaId ? -1 : 1;
    if (left.mode !== right.mode) return left.mode < right.mode ? -1 : 1;
    return left.rating < right.rating ? -1 : left.rating > right.rating ? 1 : 0;
  });

  for (const review of ordered) {
    const base = contentKeyWithoutOccurrence(review.lemmaId, review.mode, review.rating, review.review);
    const occurrence = usedByBase.get(base) ?? 0;
    usedByBase.set(base, occurrence + 1);
    const existing = existingByBase.get(base) ?? 0;
    if (occurrence < existing) {
      skippedExisting += 1;
      continue;
    }
    const fingerprint = reviewEventContentKey(
      review.lemmaId,
      review.mode,
      review.rating,
      review.review,
      occurrence,
    );
    incoming.push({
      eventId: mintDeterministicUlid(review.review, fingerprint),
      lemmaId: review.lemmaId,
      mode: review.mode,
      rating: review.rating,
      reviewedAt: review.review,
      deckVersion: options.deckVersion,
      clientId,
      fsrsParamsVersion,
    });
  }

  const skippedAggregateOnly = Object.values(aggregates).reduce(
    (total, aggregate) =>
      total +
      aggregate.ratings.again +
      aggregate.ratings.hard +
      aggregate.ratings.good +
      aggregate.ratings.easy,
    0,
  );

  if (incoming.length === 0) {
    return { added: 0, skippedExisting, skippedAggregateOnly };
  }
  const { added } = upsertReviewEvents(incoming, storage);
  return { added, skippedExisting, skippedAggregateOnly };
}

export function parseReviewEventExport(raw: unknown): ReviewEventExport | null {
  if (!raw || typeof raw !== 'object') return null;
  const source = raw as Record<string, unknown>;
  if (source.schema !== REVIEW_EVENTS_SCHEMA) return null;
  if (!Array.isArray(source.events)) return null;
  const events: ReviewEvent[] = [];
  for (const item of source.events) {
    const event = normalizeReviewEvent(item);
    if (!event) return null;
    events.push(event);
  }
  const exportedAt =
    typeof source.exportedAt === 'number' && Number.isFinite(source.exportedAt)
      ? source.exportedAt
      : 0;
  const clientId = typeof source.clientId === 'string' && source.clientId ? source.clientId : 'unknown';
  const fsrsParamsVersion =
    typeof source.fsrsParamsVersion === 'number' && Number.isFinite(source.fsrsParamsVersion)
      ? source.fsrsParamsVersion
      : FSRS_PARAMS_VERSION;
  return {
    schema: REVIEW_EVENTS_SCHEMA,
    exportedAt,
    clientId,
    fsrsParamsVersion,
    events,
  };
}

/**
 * Documented §10.2 restore ingest: validate the export contract, strip any
 * accidental identity fields by re-normalizing, then set-union on `eventId`.
 */
export function importReviewEventExport(
  raw: unknown,
  storage: ReviewEventStorageLike,
): ImportReviewEventExportResult | ImportReviewEventExportError {
  const parsed = parseReviewEventExport(raw);
  if (!parsed) {
    return { ok: false, error: 'invalid review-event export' };
  }
  const { added, log } = upsertReviewEvents(parsed.events, storage);
  return {
    ok: true,
    added,
    events: canonicalReplayOrder(log.events),
    export: exportReviewEventLog(storage, parsed.exportedAt),
  };
}

export function foldImportedReviewEvents(
  events: readonly ReviewEvent[],
  params?: FSRSParameters,
  receivedAt: number = Date.now(),
): Map<string, FoldedCardState> {
  return foldReviewEventsToCards(eventsWithClampedReviewedAt(events, receivedAt), params);
}

/**
 * Merge folded cards into existing SRS cards. Keys with no events are left
 * untouched so a partial log cannot wipe compacted-history cards.
 */
export function mergeFoldedCardsIntoSrs(
  cards: Map<string, CardState>,
  folded: Map<string, FoldedCardState>,
): { updated: number } {
  let updated = 0;
  for (const [key, card] of folded) {
    cards.set(key, {
      due: card.due,
      stability: card.stability,
      difficulty: card.difficulty,
      elapsed_days: card.elapsed_days,
      scheduled_days: card.scheduled_days,
      learning_steps: card.learning_steps,
      reps: card.reps,
      lapses: card.lapses,
      state: card.state,
      ...(card.last_review === undefined ? {} : { last_review: card.last_review }),
    });
    updated += 1;
  }
  return { updated };
}

export function exportBackfilledReviewEventLog(
  reviews: readonly ReviewLogEntry[],
  storage: ReviewEventStorageLike,
  options: BackfillFromSrsOptions,
  exportedAt: number = Date.now(),
  aggregates?: Record<string, ReviewLogAggregate>,
): ReviewEventExport {
  backfillReviewEventsFromSrsReviews(reviews, storage, options, aggregates);
  return exportReviewEventLog(storage, exportedAt);
}
