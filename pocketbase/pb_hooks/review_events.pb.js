/// <reference path="../pb_data/types.d.ts" />
/**
 * Practice Hub §10.1 ingest stamping for review_events (GH #4384/#4920).
 *
 * Server-side half of the sync contract — mirrors
 * site/src/lib/lexicon/review-event-sync.ts (`toServerReviewEvent` +
 * `DEFAULT_REVIEW_EVENT_CLOCK_POLICY`). KEEP THE CONSTANTS IN SYNC with that
 * file; the client tests pin the same numbers.
 *
 * On create the server (never the client):
 * - scopes the row to the authenticated session (§10.3 ⟦agy v4⟧ — events
 *   carry NO client-side userId; any client-sent `user` is overwritten),
 * - stamps `serverReceivedAt` and clamps a future-skewed or absurdly-old
 *   client `reviewedAt` to it (⟦codex v4⟧ clock policy),
 * - assigns the per-user monotonic `serverSeq` pull cursor (unique index
 *   `idx_review_events_user_server_seq` makes a concurrent double-assign a
 *   rejected write; the client's idempotent push simply retries),
 * - enforces the account-level `fsrsParamsVersion` pin so no device folds the
 *   same log under different parameters,
 * - rejects appends that would mix versions with the account's existing
 *   history (uniform log is a replay contract; the pin alone is not enough if
 *   the pin were ever changed out of band).
 *
 * Ordinary clients also cannot PATCH `users.fsrsParamsVersion` (migration
 * updateRule + the users update hook below); superusers still manage via admin.
 */
onRecordUpdateRequest((e) => {
  if (e.hasSuperuserAuth()) {
    return e.next();
  }
  const original = e.record.original();
  if (
    Number(e.record.get("fsrsParamsVersion")) !==
    Number(original.get("fsrsParamsVersion"))
  ) {
    throw new BadRequestError(
      "fsrsParamsVersion is account-pinned and not client-mutable",
    );
  }
  e.next();
}, "users");

onRecordCreateRequest((e) => {
  const auth = e.requestInfo().auth;
  if (!auth || !auth.id) {
    throw new ForbiddenError("review_events require an authenticated user");
  }
  const record = e.record;
  const now = Date.now();

  record.set("user", auth.id);
  record.set("serverReceivedAt", now);

  // ⟦codex v4⟧ clock policy — must match DEFAULT_REVIEW_EVENT_CLOCK_POLICY.
  const FUTURE_SKEW_MS = 5 * 60 * 1000;
  const MAX_AGE_MS = 366 * 24 * 60 * 60 * 1000;
  const reviewedAt = record.get("reviewedAt");
  if (
    typeof reviewedAt !== "number" ||
    !isFinite(reviewedAt) ||
    reviewedAt > now + FUTURE_SKEW_MS ||
    reviewedAt < now - MAX_AGE_MS
  ) {
    record.set("reviewedAt", now);
  }

  const eventVersion = Number(record.get("fsrsParamsVersion"));

  // ⟦codex v4⟧ fsrsParamsVersion pin — the account record is the authority.
  const pinned = Number(auth.get("fsrsParamsVersion"));
  if (pinned > 0 && eventVersion !== pinned) {
    throw new BadRequestError(
      "fsrsParamsVersion does not match the account pin " + pinned,
    );
  }

  // Uniform append-only log: reject mixed-version history even if the account
  // pin was changed out of band (superuser / bug). Oldest row is enough —
  // prior writes already enforced uniformity.
  const prior = $app.findRecordsByFilter(
    "review_events",
    "user = {:user}",
    "serverSeq",
    1,
    0,
    { user: auth.id },
  );
  if (prior.length > 0) {
    const logVersion = Number(prior[0].get("fsrsParamsVersion"));
    if (eventVersion !== logVersion) {
      throw new BadRequestError(
        "fsrsParamsVersion does not match existing log version " + logVersion,
      );
    }
  }

  // Server-assigned per-user monotonic ingest sequence (the pull cursor).
  let nextSeq = 1;
  const latest = $app.findRecordsByFilter(
    "review_events",
    "user = {:user}",
    "-serverSeq",
    1,
    0,
    { user: auth.id },
  );
  if (latest.length > 0) {
    nextSeq = Number(latest[0].get("serverSeq")) + 1;
  }
  record.set("serverSeq", nextSeq);

  e.next();
}, "review_events");
