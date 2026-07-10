# Word Atlas Static API Contract

The learner site is GitHub Pages/static-first. Atlas runtime data is exposed
as static JSON, not as a live backend service.

## Canonical Endpoints

- `/api/lexicon/status.json` — status counts across Atlas search/browse,
  manifest hydration, Daily Word, Practice, cloze, and source-inventory
  admission.
- `/api/lexicon/search-index.json` — compact approved-article typeahead rows.
- `/lexicon/search-aliases.json` — public alias resolvers; every row
  targets an approved article slug and is not an Atlas entry itself.
- `/api/lexicon/daily-pool.json` — Daily Word pool.
- `/api/lexicon/practice-index.{level}.json` — per-level Practice index.
- `/api/lexicon/practice-lexemes.{level}.json` — per-level Practice lexeme deck.
- `/api/lexicon/practice-cloze.{level}.json` — per-level reviewed cloze deck.

## Entry-Model Snapshot

As of 2026-07-10, the DB-backed build exposes these public-safe aggregates:

- Reviewed public Atlas articles: 5,441 (`lemma`: 4,166;
  `multiword_term`: 1,275; all other entry types: 0).
- Public alias records: 7,186. They resolve during typeahead but do not
  increment `total_reviewed_entries`.
- Persisted candidate evidence: 0. Entry-model v1 does not yet have a
  candidate-evidence table, so the status API emits an explicit empty aggregate
  instead of repurposing legacy routes or aliases as evidence.
- Legacy public browse records: 5,777, including 336 compatibility `form_of`
  routes. This is a route-record total, never an entry total.
- Daily Word: 300 entries.
- Practice deck: 4,484 lexemes and 22 reviewed A1 cloze items.
- Source-inventory seeds: 300 rows total: 80 textbook, 167 private
  teacher-lesson, 33 Ohoiko/ULP, and 20 curriculum sample rows.

Open Atlas/Lexicon board items are #3936, #4160, #3933, #3934, and #3797.
Closed items that should not reappear as
active backlog are #3932, #3796, #3449, #3450, #3406, and #3675.

The status payload also points to existing static browse assets:

- `/lexicon/browse/{letter}.json`

`npm --prefix site run hydrate` builds `data/atlas.db`, then runs the DB-backed
search artifact builder. The site build therefore fails on both
`article_vs_alias_count` and `alias_target_integrity` before Astro can emit a
public search or status artifact.

## Contract Checks

Consumers should treat `status: "ok"` as the normal state. `warning` means the
approved article index no longer matches the DB-reviewed entry total, practice
deck versions split, Daily Word became empty, or another published surface is
incomplete. Browse route records are intentionally not compared with article
totals because they retain compatibility aliases.

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
