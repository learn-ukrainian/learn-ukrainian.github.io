# Practice Hub backend — PocketBase (local dev only)

Repo-side half of the Practice Hub §10 backend
(`docs/poc/word-atlas/PRACTICE-HUB-SPEC.md` §10.1–§10.3, GH #4384/#4920):
the collection schema (migration), the `review_events` ingest hook, and a
localhost-only way to run it. **There is no production host** — the static
GitHub Pages path stays authoritative and unchanged when no adapter is
configured (`pocketBaseAdapterFromEnv` returns `null` without a base URL).

## Files

- `pb_migrations/20260905000000_practice_hub_collections.js` — §10.3 schema:
  extends the native `users` auth collection with the account-level
  `fsrsParamsVersion` pin (ordinary clients cannot PATCH it; superusers still
  manage via admin); creates `review_events` (append-only:
  `updateRule`/`deleteRule` null; unique `eventId`; unique per-user
  `(user, serverSeq)` pull cursor; `(user, reviewedAt)` analytics index;
  `cascadeDelete` on the user relation so account deletion hard-deletes
  events at the DB layer) and `snapshots` (`(user, schemaVersion, blob)` —
  fast-restore cache, never authority).
- `pb_hooks/review_events.pb.js` — §10.1 ingest stamping, mirroring
  `site/src/lib/lexicon/review-event-sync.ts` (`toServerReviewEvent` +
  `DEFAULT_REVIEW_EVENT_CLOCK_POLICY`): scopes rows to the authenticated
  session (clients never send a userId), clamps future/absurdly-old client
  clocks to `serverReceivedAt`, assigns the per-user monotonic `serverSeq`,
  rejects events that break the account's `fsrsParamsVersion` pin or that
  would mix versions with existing history; also blocks ordinary clients
  from mutating `users.fsrsParamsVersion`.

## Run it (binary)

Pinned at PocketBase **v0.40.2** (hooks/migrations API: v0.23+). Bump
deliberately, then re-check the hook against the JSVM docs.

```bash
curl -L -o /tmp/pb.zip \
  https://github.com/pocketbase/pocketbase/releases/download/v0.40.2/pocketbase_0.40.2_linux_amd64.zip
unzip /tmp/pb.zip -d /tmp/pb-bin
/tmp/pb-bin/pocketbase serve \
  --http 127.0.0.1:8090 \
  --dir "$(pwd)/pb_data" \
  --migrationsDir "$(pwd)/pb_migrations" \
  --hooksDir "$(pwd)/pb_hooks"
```

`pb_data/` is local state — never commit it. Create a local superuser for the
admin UI at <http://127.0.0.1:8090/_/> (first run prints a one-time link), and
a dev user via the admin UI or `POST /api/collections/users/records`.

## Run it (compose)

```bash
docker compose up --build
```

Same result: PocketBase on `127.0.0.1:8090`, repo migration + hook mounted
read-only, state in the `pb_data` volume.

## Point the client at it

The app stays fully offline without these. For local sync dev only:

```bash
PUBLIC_PRACTICE_SYNC_URL=http://127.0.0.1:8090 npm run dev   # from site/
```

plus a record auth token from the (later-slice) login flow; for manual
experiments `POST /api/collections/users/auth-with-password` returns one.
Sync itself runs through `runReviewEventSync` with
`PocketBaseReviewEventAdapter` (`site/src/lib/lexicon/review-event-pocketbase.ts`).

## Export / restore (§10.2)

`adapter.exportUserEventsJson()` pages the whole per-user log into one JSON
document; a fresh device (or a future stack — the log is portable, auth is
not) restores it with `importReviewEventExport` and re-folds to identical
FSRS state. Both directions are covered by
`site/tests/unit/review-event-pocketbase.test.ts`.

## Out of scope here (per spec/dispatch)

No public DNS, no TLS termination, no hosted deploy, no analytics jobs, no
auth-flow UI. Backups/analytics land with a later hosted slice.
