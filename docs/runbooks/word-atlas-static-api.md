# Word Atlas Static API Contract

The learner site is GitHub Pages/static-first. Atlas runtime data is exposed
as static JSON, not as a live backend service.

## Canonical Endpoints

Learner-facing artifacts use the `/lexicon/…` prefix (what Practice, Atlas
typeahead, and Daily Words actually `fetch`). Meta/status stay under
`/api/lexicon/…`.

- `/api/lexicon/status.json` — status counts across Atlas search/browse,
  manifest hydration, Daily Word, Practice, cloze, and source-inventory
  admission.
- `/api/lexicon/contract.json` — machine-readable surface contract.
- `/lexicon/search-index.json` — compact approved-article typeahead rows.
- `/lexicon/search-aliases.json` — public alias resolvers; every row
  targets an approved article slug and is not an Atlas entry itself.
- `/lexicon/search-shards.json` — search shard map for typeahead paging.
- `/lexicon/daily-pool.json` — Daily Word pool.
- `/lexicon/practice-index.{level}.json` — per-level Practice index.
- `/lexicon/practice-lexemes.{level}.json` — per-level Practice lexeme deck.
- `/lexicon/practice-cloze.{level}.json` — per-level reviewed cloze deck.

### Compatibility aliases (`/api/lexicon/…`)

These URLs remain published so existing bookmarks and older contract links keep
working. They are thin twins of the canonical `/lexicon/…` artifacts, not a
second source of truth:

- `/api/lexicon/search-index.json` — re-exports `/lexicon/search-index.json`
- `/api/lexicon/daily-pool.json` — re-exports `/lexicon/daily-pool.json`
- `/api/lexicon/practice-index.{level}.json` (and lexemes/cloze) — hydrate
  copies of `public/lexicon/*.json` into `public/api/lexicon/`

Do not delete a public `/api/lexicon/…` URL without operator authorization.

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

`npm --prefix site run hydrate` builds `data/atlas.db`, then generates search,
alias and browse artifacts from the configured immutable `ATLAS_TREE_ASSET_ID`
and `ATLAS_TREE_SHA256` runtime pin. The generator reuses the vendor's verified
runtime reader, including its article membership and alias-target checks, before
Astro embeds browse metadata. Pages prepares the verified tree in a separate
step, then passes `ATLAS_SEARCH_RUNTIME_TREE` to the build without credentials.
Preparation requires both pin values. The independent post-build vendor check
still validates every advertisement, including separately pinned Practice and
Daily Word artifacts.

Two projections of the five search/browse artifacts exist, and they never share
a path (#12527). The committed DB-derived snapshot stays tracked under
`site/src/data/lexicon-{search-index,search-aliases,search-shards,browse-meta,browse-flagged}.json`
and `site/public/lexicon/browse/`; Python tests, `npm run verify:artifacts` and
unpinned builds read it. When `ATLAS_SEARCH_RUNTIME_TREE` is set, the generator
writes the pinned projection to the ignored `site/.atlas-pinned/` (`data/` and
`public/lexicon/browse/`) and the site reads that set through the single module
`site/src/lib/lexicon/atlas-artifact-selection.mjs`: a Vite plugin redirects the
static JSON imports, the filesystem readers and the Node hydration script call
the same functions, and `astro:build:done` replaces the `*.json` shards in `dist/lexicon/browse/` with
the pinned shards (the prerendered browse page stays). A pinned build fails closed when the pinned set is missing, incomplete or carries a stale shard,
and when it does not match the runtime selected now. The generator writes `pinned-source.json`
(the runtime's data version and manifest digest, plus the SHA-256 of every canonical artifact and
browse shard) only when one run wrote every canonical output, and the shared gate recomputes the
digests, so any later write to the set (another run, an output override, an interrupted write) is
refused whatever wrote it. The digests are those of the exact bytes the generator wrote, and it refuses to certify a set
another writer changed meanwhile. The Node hydrate step derives `public/lexicon/search/` only from
inputs the marker certifies, then records the inputs and the digests of the shard bytes it wrote in
`.atlas-pinned/search-shards-source.json`; the gate checks them too. A pinned build never falls back
to the committed files.
The Frontend CI build record binds `site/.atlas-pinned/` and records the
selection, so a release build leaves `git status` empty and the worktree can be
removed with the guarded remover. Do not set `ATLAS_SEARCH_RUNTIME_TREE` for
`astro dev` or `astro preview`: pinned selection is a build-time feature, and the
committed browse shards in `public/` are what those servers publish.

Unpinned local builds retain the DB-backed generator and its
`article_vs_alias_count` and `alias_target_integrity` checks. For local preparation
from an already verified extracted archive, pass `--runtime-tree ./runtime-tree`
to `scripts/audit/generate_search_index.py`; the directory must contain
`atlas/current.json`. This mode uses only CURRENT's article and alias rows, so
runtime-only articles are preserved even when a newer manifest differs, subject to
the reviewed discovery holds in `registry/lexicon/atlas-discovery-exclusions.json`.
The generator and post-build vendor apply these holds after checking the complete
raw runtime membership. They withhold article listings and aliases targeting those
articles, while preserving aliases to retained targets. Each hold records its exact
headword, reason and Sources evidence; the six existing published-record holds are
carried forward by disposition ID. A changed headword fails the build until the hold
is reviewed; absent slugs are reported in `absentExclusions`. Runtime and projected
counts are reported separately. No runtime bytes or routes change, so direct article
URLs still require a future runtime-data disposition. The option
trusts prior archive verification. Public builds always prepare a fresh verified
tree and independently validate the built advertisements before publication.

## Runtime source freshness and release preparation

Pages should serve the reviewed discovery projection of immutable runtime
CURRENT, refreshed from the current committed manifest through a fresh Atlas
DB. Keep the asset-ID/SHA-256 pin for reproducible, digest-verified release
identity. The committed DB projection remains the unpinned build input; it is
also independent source evidence for the pinned projection, after applying the
same reviewed discovery holds. A historical article-count gap alone does not
establish either projection's present freshness.

`scripts/deploy/prepare_atlas_runtime_release.py` owns preparation and replay.
Hydrate the committed manifest and practice-deck pointers through
`site/scripts/hydrate-manifest.mjs` and `site/scripts/hydrate-practice-deck.mjs`
first. Acquire the exact prior archive separately. Use the project interpreter
and fresh managed scratch outside the worktree:

```bash
.venv/bin/python scripts/deploy/prepare_atlas_runtime_release.py prepare \
  --work "$TMPDIR/prepare-work" --out "$TMPDIR/prepare-out" \
  --prior-archive ./prior.zip --prior-sha256 <64hex>
.venv/bin/python scripts/deploy/prepare_atlas_runtime_release.py verify \
  --work "$TMPDIR/replay-work" --out "$TMPDIR/replay-out" \
  --prior-archive ./prior.zip --prior-sha256 <64hex>
```

`--manifest` and `--deck-dir` can select separately hydrated scratch copies;
their bytes must still match this checkout's committed pointers. Preparation
copies verified inputs into isolated scratch, builds a fresh DB with the
existing certification and alias checks, fully vendors the prior, and retains
exactly the prior's pointed CURRENT directory with its original name and bytes.
It calls the existing exporter and deterministic publication ZIP writer, then
fully vendors the candidate and checks complete raw article membership against
the fresh DB. The raw set is the disjoint union of projected and withheld
articles. It also writes and verifies the canonical search, alias, browse and
derived search artifacts in scratch. Certification, source, scale and distinct
logical PRIOR guards remain unchanged. Preparation performs no enrichment,
upload, pin update or deployment.

The product receipt `registry/lexicon/atlas-runtime-release.json` uses schema
`atlas-runtime-release.v1`. Its only bindings are the manifest pointer's JSON
SHA-256, consumed deck digests, holds digest, candidate archive digest and
CURRENT identity, exact prior archive/CURRENT identity and manifest URL, and
raw/projected article counts and membership digests. A membership digest hashes
a sorted, duplicate-free UTF-8 JSON slug array with compact separators and no
trailing LF. The receipt uses sorted keys, compact separators and a trailing LF;
it contains no timestamp or environment freshness condition.

`verify` reruns preparation with current validated inputs and the receipt's
exact prior, then requires identical archive SHA-256 and receipt bytes. Changed
inputs require a new prepare. Different archive bytes for unchanged inputs
refuse with `nondeterministic_export`. Run replay at the reviewed head and again
at the merged head before promotion. A holds-only change must leave archive
bytes identical while changing the projected membership and receipt.

After its existing fatal runtime/DB, browse and marker checks, search generation
emits one source-report JSON line and one workflow notice or warning. Reporting
reuses the selected rows and runtime parity, validates the hydrated source
against the pointers, and independently rebuilds source membership through a
fresh DB. It neither exports nor re-vendors. The receipt bridges source digest
and runtime identity; those different digests are never compared as equal.

- `current` requires every applicable binding, full membership and count to match.
- `stale` lists every applicable fixed reason: `manifest_changed`,
  `membership_diverged`, `count_diverged`, or `holds_changed`.
- `unknown` uses `receipt_missing`, `receipt_invalid`, or `report_error` when
  evidence is absent, invalid, contradictory or unavailable. It never means current.

Workflow commands contain only fixed status/reason enums and integer counts.
Only the added report call has an exception boundary. A report-only failure
warns `unknown/report_error` and preserves the existing artifact bytes, routes
and exit code; preexisting fatal checks still fail. Runtime and unpinned DB
modes both report evidence. Reporting does not authorize a release.

A release still requires current operator GO for upload, pin or Pages activation.
Bind deployed revision and archive digest to the merged implementation and
independently replayed receipt. Compare complete raw/projected membership and
counts. Prove selected content equality through the existing canonical/browse
digests from `pinned_set_digests` and the derived-search digest proof in
`atlas-artifact-selection.mjs`, compared with the deployed artifact bytes.
Include compatibility endpoints and embedded browse data. No per-article
payload parser, sampling or count-only closure replaces those full-artifact
bindings. Implementation, merge, deployment and issue completion are separate.

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

Practice shards under `public/lexicon/` (canonical) and the hydrate copy under
`public/api/lexicon/`, plus search shards under `public/lexicon/search/`, are
materialized by `hydrate-lexicon-api-shards.ts` during `npm run hydrate`.
GitHub Pages serves these as static files (default cache headers); the
`search-api-shard` / `practice-api-shard` helpers document the intended
`Cache-Control: public, max-age=3600` contract for tests and any future CDN
`_headers` wiring.
