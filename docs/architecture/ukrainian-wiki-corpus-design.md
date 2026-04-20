# Ukrainian Wiki Corpus Design

## Scope

Issue pair `#1367` + `#1368` adds a new compile-layer corpus, `ukrainian_wiki`, to `data/sources.db` and `data/embeddings/manifest.db`.

This is an additive sixth corpus beside the existing five-corpus retrieval stack from ADR-006/007:

- `textbook_sections`
- `modern_literary`
- `archaic_literary`
- `external`
- `wikipedia`
- `ukrainian_wiki` (new)

It is explicitly **not** an `l1-uk` publishing path and **not** an A1/A2 module-generation step. The corpus is bootstrap retrieval infrastructure for English-speaker A1/A2 modules.

## Ingestion Unit

### Decision

Use **passage-level ingestion**, not sentence atomization.

### Why this wins

- The compile layer already retrieves and expands contextual units, not isolated atoms. `search_sources()` expands neighbor context for literary and Wikipedia results, and textbook retrieval is section-first rather than sentence-first.
- `scripts/wiki/dense_rerank.py` already chunks long Wikipedia articles into medium-size dense units (`chunk_wikipedia_article`) rather than sentence rows.
- The V6 write phase synthesizes from retrieved briefs and passages. It does not assemble pedagogy from sentence cards. Sentence-only rows would maximize provenance granularity while breaking discourse cues the writer actually needs.

That is the concrete evidence for revising the earlier sentence-level position: the repo’s current retrieval and writer contracts are passage-oriented end to end.

### Boundary Rule

Primary boundary: **Markdown prose paragraph**.

Normalization rules:

1. Strip YAML frontmatter, HTML comments, code fences, tables, blockquotes, and list items from the article before passage segmentation.
2. Preserve the current heading path (`H1 > H2 > H3`) as metadata, but do not cross a heading boundary when merging.
3. Treat consecutive non-empty prose lines as one paragraph.
4. If a paragraph is shorter than `40` words, merge forward with the next prose paragraph under the same heading path until it reaches `>= 40` words or would exceed the char cap.
5. Hard cap each stored passage at `900` characters. If a single paragraph exceeds that cap, split at the nearest sentence break at or below the cap; only fall back to a hard character split if no sentence punctuation exists.

Result: the stored unit is still a passage, but bounded tightly enough for A1/A2 retrieval and dense shard stability.

## `sources.db` Schema

Regular table: `ukrainian_wiki`

Columns:

- `id INTEGER PRIMARY KEY`
- `passage_id TEXT NOT NULL UNIQUE`
- `article_slug TEXT NOT NULL`
- `article_title TEXT NOT NULL DEFAULT ''`
- `article_path TEXT NOT NULL DEFAULT ''`
- `section_path TEXT NOT NULL DEFAULT ''`
- `paragraph_start INTEGER NOT NULL DEFAULT 0`
- `paragraph_end INTEGER NOT NULL DEFAULT 0`
- `word_count INTEGER NOT NULL DEFAULT 0`
- `char_count INTEGER NOT NULL DEFAULT 0`
- `text TEXT NOT NULL DEFAULT ''`
- `source_registry_path TEXT NOT NULL DEFAULT ''`
- `gate_report_json TEXT NOT NULL DEFAULT ''`
- `inserted_at TEXT NOT NULL DEFAULT ''`

FTS5 virtual table: `ukrainian_wiki_fts`

- External-content FTS5 table over `article_title`, `section_path`, and `text`
- `content='ukrainian_wiki'`
- `content_rowid='id'`
- Trigger-maintained, same pattern as `wikipedia_fts` and `literary_fts`

Primary key: `id`

Stable retrieval key: `passage_id`

Provenance rule:

- `passage_id = "{article_slug}:p{paragraph_start}-{paragraph_end}"`
- No joins to `wikipedia`, `external_articles`, or other corpus tables
- Cross-corpus fusion happens only at `search_sources()` merge time, after each corpus has been searched independently

## Dense Retrieval Storage

Dense corpus name: `ukrainian_wiki`

Manifest database: `data/embeddings/manifest.db`

Storage rules:

- Reuse the existing manifest-backed shard layout from ADR-006
- Reserve the corpus immediately via a zero-row shard so `manifest.db` lists `ukrainian_wiki` even before A.5/A.6 ingest real passages
- Shard directory: `data/embeddings/ukrainian_wiki/`
- Reserved shard path: `data/embeddings/ukrainian_wiki/shard-000001.npy`
- Future real shards append sequentially with the same `shard-%06d.npy` convention as the other corpora

This keeps the new corpus consistent with the current manifest model instead of introducing a separate registry mechanism.

## Track Priors

`ukrainian_wiki` gets a high prior only where the EPIC needs it: English-speaker A1/A2 bootstrap.

Proposed weights:

- `a1`: `0.95`
- `a2`: `0.90`
- `b1`: `0.05`
- `b2`: `0.02`
- `c1`: `0.02`
- `c2`: `0.02`
- `hist`: `0.02`
- `lit`: `0.02`
- `ruth`: `0.01`
- `oes`: `0.01`

Rationale:

- Keep `textbook` at `1.0` as the strongest pedagogical anchor already validated in the current stack.
- Put `ukrainian_wiki` just below textbook weight for `a1`/`a2` so it is strongly preferred over generic `wikipedia` and `external`, but cannot drown out textbook sections when both corpora hit well.
- Make `b1+` effectively opt-out without hard-excluding the corpus. This matches ADR-007: use soft priors, not hard source bans.

## Admission Gate

The ingestion helper does not re-implement validators. It delegates to existing modules in this order:

1. **Citation audit**
   - Delegate to `wiki.quality_gate.check_article()` and fail on source-registry issues (`MISSING_SOURCES_YAML`, orphan refs, malformed registry, unused registry drift).
2. **VESUM coverage**
   - Extract Ukrainian word forms with existing tokenization helpers.
   - Delegate word verification to `rag_batch_verify.vesum_batch_lookup()`.
   - Fail if coverage falls below the configured floor for a candidate passage batch.
3. **Surzhyk linter / Russicism scan (#912)**
   - Delegate to `audit.checks.russicism_detection.check_russicisms()`.
   - Any violation fails admission.
4. **Pravopys 2019 spot-check**
   - Derive orthography-sensitive query terms from article title / heading path.
   - Delegate lookup to `rag.source_query.pravopys_lookup()`.
   - Record evidence in the gate report; fail if a required lookup is configured and misses.
5. **Антоненко-Давидович style-guide spot-check**
   - Use suspect forms surfaced by the Russicism scan or explicit query terms.
   - Delegate to `wiki.sources_db.search_style_guide()`.
   - Record evidence in the gate report; fail when a flagged suspect term has no acceptable resolution.

For this issue, the helper lands the gate wiring and reporting contract. Tuning the exact thresholds and real corpus batches belongs to A.5/A.6.

## Retrieval Integration

The new corpus is additive and stays inside the existing `modern_dense_section` / `unified_dense` path:

- add `ukrainian_wiki` to `SUPPORTED_CORPORA`
- add an FTS candidate fetcher in `sources_db.py`
- add a dense unit loader in `dense_rerank.py`
- add prior mapping in `track_priors.yaml`
- keep merge-time ranking identical: `final_score = dense_score * prior_weight`

Empty-corpus behavior is required:

- reserved manifest shard with zero active units is valid
- `search_sources(track='a1', strategy='modern_dense_section')` returns `[]` cleanly when `ukrainian_wiki` has no rows

## Rollback Path

If A.8 canary shows the enriched-corpus arm is not helping, rollback is soft-first:

1. Set all `ukrainian_wiki` priors to near-zero in `track_priors.yaml`.
2. Stop running the ingestion helper in any bootstrap workflow.
3. Leave the schema in place; it is additive and isolated.
4. If a hard cleanup is required, delete `ukrainian_wiki` rows from `sources.db`, mark manifest units deleted, and remove orphaned `data/embeddings/ukrainian_wiki/` shards.

Reason: rollback should disable retrieval influence immediately without destabilizing the other five corpora or forcing a destructive `sources.db` rebuild.

## ADR Need

No new ADR is required for this issue.

Reason:

- retrieval architecture is unchanged
- dense storage architecture is unchanged
- corpus routing remains soft-prior-based per ADR-006/007

This is a new corpus plugged into the existing architecture, not a change to the architecture itself.
