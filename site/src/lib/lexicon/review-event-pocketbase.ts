/**
 * Practice Hub §10.2 PocketBase adapter — the concrete `ReviewEventSyncAdapter`.
 *
 * Spec (`docs/poc/word-atlas/PRACTICE-HUB-SPEC.md` §10.1/§10.2/§10.3): the
 * event log is portable; auth/rules/admin are not. This adapter speaks the
 * PocketBase REST API with plain `fetch` (no SDK dependency, no auth vendor
 * lock-in beyond the spec's PocketBase choice). The server-side half lives in
 * `pocketbase/` (collection migration + `pb_hooks/review_events.pb.js`) and
 * reproduces `toServerReviewEvent` at ingest: per-user `serverSeq`,
 * `serverReceivedAt`, clock clamp, and the account-level `fsrsParamsVersion`
 * pin. Events carry NO client-side `userId` — the server scopes rows by the
 * authenticated session (§10.3 ⟦agy v4⟧).
 *
 * Push is idempotent by `eventId`: a duplicate create comes back as a 400
 * unique-constraint violation and is treated as already-held (ACKed), exactly
 * like `FakeReviewEventServer` in `review-event-sync.test.ts`. Pull pages by
 * the `serverSeq` cursor, oldest first. `exportUserEventsJson` is the server
 * half of the §10.2 export contract; the restore half is the existing
 * `importReviewEventExport` in `review-event-sync.ts`.
 *
 * Offline stays the default: nothing constructs this adapter unless a base URL
 * and auth token are configured (`pocketBaseAdapterFromEnv` returns `null`
 * otherwise), so the GitHub Pages static path is unchanged.
 */

import {
  FSRS_PARAMS_VERSION,
  REVIEW_EVENTS_SCHEMA,
  canonicalReplayOrder,
  normalizeReviewEvent,
  type ReviewEvent,
  type ReviewEventExport,
} from './review-events';
import {
  uniformFsrsParamsVersion,
  type ReviewEventPullPage,
  type ReviewEventPushAck,
  type ReviewEventSyncAdapter,
  type ServerReviewEvent,
} from './review-event-sync';

export const POCKETBASE_REVIEW_EVENTS_COLLECTION = 'review_events';
export const POCKETBASE_DEFAULT_PULL_PAGE_SIZE = 200;
/** Env var that points the app at a sync host. Unset ⇒ offline static path. */
export const POCKETBASE_BASE_URL_ENV = 'PUBLIC_PRACTICE_SYNC_URL';
export const POCKETBASE_EXPORT_CLIENT_ID = 'pocketbase-server';

/** Minimal transport surface so tests can drive the adapter without HTTP. */
export interface PocketBaseTransportResponse {
  status: number;
  body: unknown;
}

export type PocketBaseFetchLike = (
  url: string,
  init: { method: string; headers: Record<string, string>; body?: string },
) => Promise<PocketBaseTransportResponse>;

export interface PocketBaseAdapterConfig {
  /** e.g. `http://127.0.0.1:8090` — trailing slashes are stripped. */
  baseUrl: string;
  /** PocketBase record auth token; the server scopes rows by it. */
  authToken: string;
  /** Injectable transport; defaults to `globalThis.fetch`. */
  fetch?: PocketBaseFetchLike;
  /** Pull page size (PocketBase `perPage`). */
  pageSize?: number;
}

const defaultFetch: PocketBaseFetchLike = async (url, init) => {
  const response = await globalThis.fetch(url, init);
  const text = await response.text();
  let body: unknown = null;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    body = null;
  }
  return { status: response.status, body };
};

function clientPayload(event: ReviewEvent): Record<string, unknown> {
  // §10.3 ⟦agy v4⟧: no user, no serverSeq/serverReceivedAt — the server stamps
  // and scopes at ingest. `presentation` rides along when present.
  const payload: Record<string, unknown> = {
    eventId: event.eventId,
    lemmaId: event.lemmaId,
    mode: event.mode,
    rating: event.rating,
    reviewedAt: event.reviewedAt,
    deckVersion: event.deckVersion,
    clientId: event.clientId,
    fsrsParamsVersion: event.fsrsParamsVersion,
  };
  if (event.presentation) payload.presentation = event.presentation;
  return payload;
}

/** PocketBase validation-error shape for a violated unique `eventId`. */
function isDuplicateEventId(body: unknown): boolean {
  if (!body || typeof body !== 'object') return false;
  const data = (body as { data?: unknown }).data;
  if (!data || typeof data !== 'object') return false;
  const field = (data as { eventId?: unknown }).eventId;
  if (!field || typeof field !== 'object') return false;
  return (field as { code?: unknown }).code === 'validation_not_unique';
}

/** Fail-closed mapping of a server row to a stamped event; `null` on junk. */
function toServerEvent(raw: unknown): ServerReviewEvent | null {
  if (!raw || typeof raw !== 'object') return null;
  const source = raw as Record<string, unknown>;
  const event = normalizeReviewEvent(source);
  if (!event) return null;
  const { serverSeq, serverReceivedAt } = source;
  if (
    typeof serverSeq !== 'number' ||
    !Number.isFinite(serverSeq) ||
    serverSeq < 1 ||
    typeof serverReceivedAt !== 'number' ||
    !Number.isFinite(serverReceivedAt)
  ) {
    return null;
  }
  return { ...event, serverSeq, serverReceivedAt };
}

export class PocketBaseReviewEventAdapter implements ReviewEventSyncAdapter {
  private readonly baseUrl: string;
  private readonly authToken: string;
  private readonly transport: PocketBaseFetchLike;
  private readonly pageSize: number;

  constructor(config: PocketBaseAdapterConfig) {
    this.baseUrl = config.baseUrl.replace(/\/+$/, '');
    this.authToken = config.authToken;
    this.transport = config.fetch ?? defaultFetch;
    this.pageSize = config.pageSize ?? POCKETBASE_DEFAULT_PULL_PAGE_SIZE;
  }

  private request(
    method: 'GET' | 'POST',
    path: string,
    body?: Record<string, unknown>,
  ): Promise<PocketBaseTransportResponse> {
    return this.transport(`${this.baseUrl}${path}`, {
      method,
      headers: {
        Authorization: this.authToken,
        ...(body ? { 'Content-Type': 'application/json' } : {}),
      },
      ...(body ? { body: JSON.stringify(body) } : {}),
    });
  }

  /**
   * Idempotent per-`eventId` upsert. A unique-constraint 400 means the server
   * already holds the event — it is ACKed, never re-written (append-only).
   * Any other failure throws so the sync engine keeps the unACKed backlog and
   * re-pushes next round.
   */
  async push(events: readonly ReviewEvent[]): Promise<ReviewEventPushAck> {
    const ackedEventIds: string[] = [];
    for (const event of events) {
      const response = await this.request(
        'POST',
        `/api/collections/${POCKETBASE_REVIEW_EVENTS_COLLECTION}/records`,
        clientPayload(event),
      );
      if (response.status >= 200 && response.status < 300) {
        ackedEventIds.push(event.eventId);
        continue;
      }
      if (response.status === 400 && isDuplicateEventId(response.body)) {
        ackedEventIds.push(event.eventId);
        continue;
      }
      throw new Error(
        `review_events push failed for ${event.eventId}: HTTP ${response.status}`,
      );
    }
    return { ackedEventIds };
  }

  /**
   * Page of stamped events with `serverSeq` strictly greater than the cursor,
   * oldest first. The sync engine advances the cursor between calls, so page 1
   * of each filtered list is always the next page to consume.
   */
  async pull(sinceServerSeq: number): Promise<ReviewEventPullPage> {
    const filter = encodeURIComponent(`serverSeq > ${Math.max(0, Math.floor(sinceServerSeq))}`);
    const path =
      `/api/collections/${POCKETBASE_REVIEW_EVENTS_COLLECTION}/records` +
      `?page=1&perPage=${this.pageSize}&filter=${filter}&sort=${encodeURIComponent('serverSeq')}`;
    const response = await this.request('GET', path);
    if (response.status < 200 || response.status >= 300) {
      throw new Error(`review_events pull failed: HTTP ${response.status}`);
    }
    const body = response.body as {
      page?: unknown;
      totalPages?: unknown;
      items?: unknown;
    } | null;
    const items = Array.isArray(body?.items) ? body.items : [];
    const events: ServerReviewEvent[] = [];
    for (const item of items) {
      const event = toServerEvent(item);
      if (event) events.push(event);
    }
    const totalPages =
      typeof body?.totalPages === 'number' && Number.isFinite(body.totalPages)
        ? body.totalPages
        : 1;
    const page = typeof body?.page === 'number' && Number.isFinite(body.page) ? body.page : 1;
    const last = events.length > 0 ? events[events.length - 1].serverSeq : 0;
    return {
      events,
      upToServerSeq: Math.max(Math.floor(sinceServerSeq), last),
      hasMore: page < totalPages,
    };
  }

  /**
   * Server half of the §10.2 export contract: the full per-user event log as
   * one JSON document, replayable through `importReviewEventExport`. The
   * exported copy carries the server-clamped `reviewedAt` (the replay
   * authority) and the pinned `fsrsParamsVersion`; mixed-version logs are
   * refused because replay could not pin a single parameter generation.
   */
  async exportUserEventsJson(exportedAt: number = Date.now()): Promise<ReviewEventExport> {
    const events: ServerReviewEvent[] = [];
    let cursor = 0;
    for (;;) {
      const page = await this.pull(cursor);
      events.push(...page.events);
      cursor = page.upToServerSeq;
      if (!page.hasMore) break;
    }
    const fsrsParamsVersion = uniformFsrsParamsVersion(events);
    if (fsrsParamsVersion === null && events.length > 0) {
      throw new Error('refusing to export a mixed-fsrsParamsVersion log');
    }
    // `canonicalReplayOrder` preserves identity; the cast keeps the server
    // stamps visible so they can be stripped from the exported copy.
    const ordered = canonicalReplayOrder(events) as ServerReviewEvent[];
    return {
      schema: REVIEW_EVENTS_SCHEMA,
      exportedAt,
      clientId: POCKETBASE_EXPORT_CLIENT_ID,
      fsrsParamsVersion: fsrsParamsVersion ?? FSRS_PARAMS_VERSION,
      events: ordered.map(({ serverSeq, serverReceivedAt, ...event }) => {
        void serverSeq;
        void serverReceivedAt;
        return event;
      }),
    };
  }
}

/**
 * Wiring seam for the app: returns an adapter only when a sync host AND a
 * token are configured. Unset ⇒ `null` ⇒ the static offline path (§10: "no
 * account = exactly today's offline behaviour").
 */
export function pocketBaseAdapterFromEnv(
  env: Record<string, string | undefined> | undefined,
  authToken?: string,
  overrides: Partial<Omit<PocketBaseAdapterConfig, 'baseUrl' | 'authToken'>> = {},
): PocketBaseReviewEventAdapter | null {
  const baseUrl = env?.[POCKETBASE_BASE_URL_ENV]?.trim() ?? '';
  const token = authToken?.trim() ?? '';
  if (!baseUrl || !token) return null;
  return new PocketBaseReviewEventAdapter({ baseUrl, authToken: token, ...overrides });
}

/** Astro-facing wrapper: reads `PUBLIC_PRACTICE_SYNC_URL` from `import.meta.env`. */
export function resolvePocketBaseAdapter(
  authToken?: string,
): PocketBaseReviewEventAdapter | null {
  const env =
    typeof import.meta !== 'undefined'
      ? (import.meta as { env?: Record<string, string | undefined> }).env
      : undefined;
  return pocketBaseAdapterFromEnv(env, authToken);
}
