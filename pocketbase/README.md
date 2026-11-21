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

Pinned at PocketBase **v0.40.6** (hooks/migrations API: v0.23+). When updating
the version, update the release checksum and recheck the hook against the JSVM
docs.

```bash
curl -fL -o /tmp/pb.zip \
  https://github.com/pocketbase/pocketbase/releases/download/v0.40.6/pocketbase_0.40.6_linux_amd64.zip
printf '%s  %s\n' 0e1f609158ed945f809f8a02ae012aa0427129c66ebb63c1aee76f2c0309373f /tmp/pb.zip \
  | sha256sum -c -
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

The container runs as UID and GID `10001`. Docker initializes new named
volumes from the image. If you already have a `pb_data` volume from the
root-running image, stop PocketBase and run this once from this directory
before starting it again:

```bash
docker compose run --rm --build --no-deps --user 0:0 --entrypoint chown pocketbase \
  -hR 10001:10001 /pb_data
```

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
