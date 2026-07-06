# Word Atlas Static API Contract

The learner site is GitHub Pages/static-first. Atlas runtime data is exposed
as static JSON, not as a live backend service.

## Canonical Endpoints

- `/api/lexicon/status.json` — status counts across Atlas search/browse,
  manifest hydration, Daily Word, Practice, cloze, and source-inventory
  admission.
- `/api/lexicon/search-index.json` — compact typeahead/search rows.
- `/api/lexicon/daily-pool.json` — Daily Word pool.
- `/api/lexicon/practice-index.{level}.json` — per-level Practice index.
- `/api/lexicon/practice-lexemes.{level}.json` — per-level Practice lexeme deck.
- `/api/lexicon/practice-cloze.{level}.json` — per-level reviewed cloze deck.

## Current Snapshot

As of 2026-07-03, the static contract should expose this board state:

- Atlas manifest: 5,415 entries, including 336 `form_of` records.
- Public search/browse: 5,405 entries, 61 search shards, 31 browse shards.
- Daily Word: 300 entries.
- Practice deck: 4,484 lexemes and 22 reviewed A1 cloze items.
- Source-inventory seeds: 300 rows total: 80 textbook, 167 private
  teacher-lesson, 33 Ohoiko/ULP, and 20 curriculum sample rows.

Open Atlas/Lexicon board items are #3936, #4160, #3933, #3934, and #3797.
Closed items that should not reappear as
active backlog are #3932, #3796, #3449, #3450, #3406, and #3675.

The status payload also points to existing static browse assets:

- `/lexicon/browse/{letter}.json`

## Contract Checks

Consumers should treat `status: "ok"` as the normal state. `warning` means at
least one public surface drifted, search/browse counts disagree, practice deck
versions split, Daily Word became empty, or the hydrated manifest no longer
matches the public Atlas count.

`sourceInventory` counts only become non-null when the build has a hydrated
release manifest. Missing `surface_admission` remains false; source-inventory
growth is Atlas browse/search only until a reviewed decision admits Daily Word,
Practice, or cloze.

## Deployment Rule

Do not add FastAPI routes for public Atlas learner data unless the deployment
target changes away from GitHub Pages or the route is explicitly local/admin
only. Public learner data must stay available as static JSON.

Practice and search shard JSON under `public/api/lexicon/` and
`public/lexicon/search/` is materialized by `hydrate-lexicon-api-shards.ts`
during `npm run hydrate`. GitHub Pages serves these as static files (default
cache headers); the `search-api-shard` / `practice-api-shard` helpers document
the intended `Cache-Control: public, max-age=3600` contract for tests and any
future CDN `_headers` wiring.
