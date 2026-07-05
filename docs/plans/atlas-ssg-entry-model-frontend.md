# Word Atlas — entry-model v1 on the site: SSG from `atlas.db` (GH #4385)

- status: fleet-reviewed (codex msg 1892, 2026-07-05 — 3 blockers + 5 non-blockers, ALL folded, marked ⟦codex⟧)
- owner: fable (atlas/practice-hub track driver)
- date: 2026-07-05
- parent plan: `docs/plans/atlas-entry-model-v1-and-corpus-fill.md` (roadmap step 5)
- entry-model SSOT: `docs/runbooks/word-atlas-entry-model.md` (requirements §"POC And Schema
  Changes Required" + the 11 acceptance gates — this plan implements them, it does not restate them)
- route map: `docs/poc/word-atlas/README.md`

## 1. Data flow — Phase A now, Phase B at scale

**Phase A (this epic):** the site build gains one step and flips its read source:

```
hydrate manifest (pointer→asset, unchanged)          [existing]
  → python -m scripts.atlas.atlas_db  (manifest → data/atlas.db, ~seconds)   [existing, #4380]
  → Astro build reads atlas.db directly (better-sqlite3 in getStaticPaths /
    endpoint builders) — NO new 46 MB intermediate JSON                        [new]
```

- Zero new release infrastructure: the DB stays a derived, gitignored build artifact; the
  manifest release asset (+ #4411 content-addressed pointers) remains the transport.
- The migration materializes the entry-model fields (`entry_type`, `display_head`,
  `review_state`, `visibility`, aliases, related_entries). ⟦codex B1⟧ It does NOT yet project
  everything `WordAtlasArticle` renders (`primary_source`, `course_usage`, top-level
  `wiki_reference`, rich `textbooks`/`external_materials`, …) — PR-1 therefore ships a
  **DB→article compatibility projection** (full public article payload per slug) gated by
  **render-parity tests** (golden-page diff: DB-rendered vs manifest-rendered for a fixture set
  covering every entry_type + the прапор/файний POC pages).
- CI: the deploy job builds the DB after hydrate; `atlas_db` gate failures (entry_type violations)
  fail the build. ⟦codex B2⟧ The current builder only PARTIALLY checks alias targets (silently
  drops unresolved `form_of`) — PR-1 adds an explicit **post-build alias validation**: every
  public alias must join an approved+public article, with actionable per-alias failure output.
- ⟦codex NB4⟧ `site/package.json` gains `better-sqlite3`; the DB build runs after hydrate in BOTH
  local and deploy paths; any CI cache of the DB keys on pointer sha + `atlas_db.py`/schema hash.
- ⟦codex NB5⟧ PR-1 carries a **build-perf gate**: benchmark DB build + `getStaticPaths` at current
  size AND synthetic 50k/250k; the read layer is a shared preloaded row map (one DB pass), never
  per-page DB churn.

**Phase B (at ~250k, separate epic step):** publish `atlas.db` itself as the content-addressed
release asset (same `<sha12>` scheme as #4411) and drop the JSON manifest entirely; the manifest
becomes an export for tooling that still wants it. NOT in scope here — named so nobody designs
against the wrong horizon.

## 2. Routes and templates

| Route | Source file | Change |
|---|---|---|
| `/lexicon/{slug}` | `[lemma].astro` → **renamed `[slug].astro`** | param is an entry slug (runbook OD-4: rename YES — semantics first; one `git mv` + import fixes) |
| `/lexicon/` , `/lexicon/browse/` | unchanged | read counts/browse rows from DB |
| practice/WoD routes | unchanged | decks feed per PRACTICE-HUB-SPEC §9.7 (separate lane) |

**Article component branching (`WordAtlasArticle.astro`):** one dispatcher, per-`entry_type`
templates:

| entry_type | Template | Sections shown | Morphology |
|---|---|---|---|
| `lemma` | `LemmaArticle` (today's view) | full (значення/походження/наголос/парадигма/синоніми/фразеологізми/літ. засвідчення) | VESUM paradigm table |
| `multiword_term` | `TermArticle` | значення/походження/вжиток/компоненти | NO paradigm table; per-component links |
| `expression` / `phraseologism` / `proverb` | `ExpressionArticle` (new design source `expression-detail.html` FIRST — POC route map requires it before first-class support) | значення/вжиток/компоненти/варіанти | none; component-lemma backlinks with the queued-component suppression rule |
| `proper_name` | `LemmaArticle` variant flag | reduced (no синоніми section by default) | paradigm if VESUM-attested |

- Section labels and empty-state expectations branch by type — a proverb page never renders an
  empty «Парадигма» shell (the #3631 empty-Atlas lesson, applied per-section).
- **Component backlinks** render from `related_entries` (role=`component`); a component whose
  article is not yet approved+public renders as plain text, not a link (runbook OD-3: publishing
  is NOT blocked on components; broken public links are — the gate `component_cross_links`).

## 3. Search — articles and aliases split

- Build TWO artifacts from the DB (replacing today's single index):
  - `lexicon-search-index.json` — **article rows only** (slug, display_head, gloss, entry_type,
    cefr badge), counted as entries.
  - `lexicon-search-aliases.json` — alias rows (`alias`, `kind`, `target_slug`), deduplicated at
    build (`alias_deduplication` gate); consumed by the typeahead to RESOLVE to article slugs,
    never displayed as standalone results.
- Typeahead behavior ⟦codex NB6 — concrete result shape⟧: the client model carries
  `{matchedAlias, aliasKind, targetSlug, targetHead}`; an alias hit renders as
  «matchedAlias → display_head» so typing «Іване» visibly resolves rather than mysteriously
  showing «Іван». Direct article hits rank above alias resolutions; direct+alias duplicates
  dedupe to the direct hit.
- `alias_target_integrity` at artifact build ⟦codex NB7 — refined fail-closed⟧: aliases targeting
  queued/non-public articles are FILTERED before public emission (with counted diagnostics in the
  build log); the build FAILS only if a row already selected for the public artifact targets a
  non-public/missing article. Fail-closed on emission, not on the queue's existence.
- Runbook OD-1 resolved: `form_of` records live ONLY in the aliases artifact (and the DB `aliases`
  table) — they leave the manifest's entry stream entirely; they never increment totals.
- ⟦codex B3 — URL blast radius⟧ **336 `form_of` slugs are PUBLISHED ROUTES today** — removing them
  from the entry stream must not 404 them. PR-3 generates **redirect stubs** for every retired
  form-slug (Astro redirect/meta-refresh to the target article slug), excludes them from the
  sitemap, and adds **URL-parity tests** (every pre-migration public route resolves to 200-or-
  redirect post-migration).

## 4. Static status API — counts by type

`/lexicon/status.json` (or the existing status artifact) publishes exactly the runbook's aggregate
vocabulary:

```json
{
  "reviewed_entries_by_type": {"lemma": N, "multiword_term": N, "expression": N, ...},
  "total_reviewed_entries": N,
  "alias_records": N,
  "candidate_evidence_by_bucket": {...},
  "noise_rejected": N
}
```

Raw surface counts are never labeled "entries" (`static_api_counts_by_type` gate). The
browse/landing UI reads `total_reviewed_entries` — fixing today's inflated raw-count display.

## 5. CI gates

Wire the runbook's 11 acceptance gates as follows (no new gate concepts — placement only):

| Gate | Where it runs |
|---|---|
| `entry_type_enum`, `entry_type_shape`, `article_vs_alias_count`, `alias_target_integrity` | `atlas_db` builder (already enforced, #4380) → now on the deploy path via §1 |
| `alias_deduplication`, `component_cross_links` | search/article artifact builders (new, §2-3) |
| `provenance_by_type`, `privacy_boundary` | existing conformance validator, extended to the new artifacts |
| `static_api_counts_by_type` | status artifact builder test |
| `poc_route_map_alignment` | docs check: route map names every template §2 claims (extend the existing prompt-lint/docs CI family) |
| `scripts_documented` | `docs/SCRIPTS.md` entry for the new build step |

## 6. Open-decision resolutions (runbook §Open Decisions)

| # | Decision | Resolution |
|---|---|---|
| OD-1 | `form_of` in manifest vs separate artifact | **Separate aliases artifact** (§3); manifest entry stream = articles only |
| OD-2 | frequency threshold for standalone `expression` admission | **Advisory-only provisional: curriculum-target OR GRAC ≥ 1.0/million.** ⟦codex NB8⟧ This number must NOT silently become policy — it stays out of any CI/publish gate until a **Decision Card goes to the user** at the point the expression-admission gate is actually built. |
| OD-3 | components required before expression publish | **No** — publish allowed; un-approved component renders unlinked (§2); `component_cross_links` guards against broken links, not against publication |
| OD-4 | rename `[lemma].astro` | **Yes**, in the routes PR (§7 PR-2) |

## 7. Delivery — four PRs, in order

| PR | Scope | Est. |
|---|---|---|
| **PR-1** `ssg-db-read` | build step (hydrate→atlas_db in deploy), better-sqlite3 dep + shared preloaded read layer, **DB→article compatibility projection + render-parity tests** ⟦B1⟧, **post-build alias validation** ⟦B2⟧, **perf benchmark gate (50k/250k synthetic)** ⟦NB5⟧, CI wiring + cache keys ⟦NB4⟧ | M-L |
| **PR-2** `entry-type-templates` | `expression-detail.html` POC design source + route-map row (FIRST), then the §2 dispatcher + templates + rename | M-L |
| **PR-3** `search-alias-split` | §3 artifacts + typeahead resolution shape ⟦NB6⟧ + emission-scoped fail-closed ⟦NB7⟧ + **form-slug redirect stubs + URL-parity tests** ⟦B3⟧ | M-L |
| **PR-4** `status-counts` | §4 API + UI count fix + remaining gates | S |

Each PR: fleet-reviewed cross-family, browser-verified per #M-4a (article pages of each entry_type
rendered and read), CI green, no auto-merge. PR-2's design source goes through the same
design-page review shape as practice-hub v4 (#4413).

## 8. Out of scope (named)

Phase B DB-as-asset; practice deck builders (PRACTICE-HUB-SPEC §9.7 lane); Phase-2 enrichment
fill; any backend (#4384 — gated on user go); Ohoiko/textbook/curriculum intake epics.
