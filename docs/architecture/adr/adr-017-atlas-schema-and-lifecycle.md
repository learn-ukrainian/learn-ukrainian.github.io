# ADR-017: Atlas projection schema and lifecycle

**Status**: Accepted
**Date**: 2026-07-26
**Deciders**: Operator (2026-07-25 decision cards); Gemini 3.1 Pro, Sol
(`gpt-5.6-sol`), and Claude Opus 5 (advisory reviews recorded in the plan of
record)
**Related**: [#4387](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4387),
[#5788](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5788),
[#5789](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5789),
[Atlas open lexical-layer plan](../../plans/2026-07-25-atlas-open-lexical-layer.md),
[inventory and migration matrix](../../plans/2026-07-25-atlas-lexical-inventory-matrix.md),
[Word Atlas entry model](../../runbooks/word-atlas-entry-model.md)

## Context

Word Atlas currently has a useful SQLite entry-model projection, but its
source boundary is not yet sufficient for the Open Lexical Layer. The next
phase adds sourced senses, licensed attestations, and practice decks without
turning a generated database or a release artifact into editorial truth. The
existing v1 migrator rebuilds `data/atlas.db` from the manifest; that is a
projection pattern, not a licence to hand-edit the database or to delete
unrecognised local state.

The Phase 0a inventory also found legacy data whose normalized destination is
not yet approved. A migration that silently replaces those fields would create
a parallel truth or lose learner-facing data. In particular, a sentence search
hit is only a candidate until it has a source locator, a rights decision, span
boundaries, and review admission.

## Decision

Atlas uses external, versioned source files as canonical source of truth
(SSOT). `data/atlas.db` is a disposable, deterministic SQLite query projection
of those inputs; it is never an editorial write target or the owner of user
state.

### Source and projection boundary

The builder reads declared source inputs, validates them, and writes a fresh
projection with `PRAGMA foreign_keys = ON`. Inputs include curriculum YAML,
wiki articles, reviewed files under `data/lexicon/`, and explicitly admitted
curated evidence files, for example
`plans/alona-truth/v3-curated-with-provenance.jsonl`. A source file records its
own revision, provenance, and admission state; a release manifest may be an
input or compatibility export, but is not a replacement SSOT for newly
accepted editorial records.

The build/re-ingest lifecycle is:

1. Resolve the declared source set and verify file hashes, schema versions, and
   rights metadata.
2. Validate identifiers, source locators, licence policy, and foreign-key
   closure before publishing a candidate projection.
3. Build a new SQLite file in a temporary path, run integrity and static-shard
   parity checks, then atomically replace the prior `atlas.db`.
4. Export static search and Practice shards from that verified projection.

The result is idempotent: the same source revision and builder version produce
the same logical rows and public shards. Re-ingest may replace `atlas.db`; it
must not modify its source inputs. This differs from a runtime release
*hydrate*: hydration may fetch or verify a pinned derived artifact, but it
cannot promote candidate evidence, rewrite SSOT files, or alter user-local
state.

### Logical schema and stable identifiers

The normalized v2 projection has these ownership boundaries. Names describe
logical tables; implementation may add compatibility views while the v1
`articles`, `enrichment`, `related_entries`, and `article_provenance` readers
are dual-read.

| Record | Stable key and foreign keys | Purpose |
| --- | --- | --- |
| `lemma_entries` | `entry_slug` PK | One lexical entry/article identity, including entry type and public route metadata. |
| `senses` | `sense_slug` PK; `entry_slug` FK | One reviewed lexical sense under one entry. |
| `sources` / rights registry | `source_id` PK | Work, repository, or dataset rights and attribution record. |
| `attestations` | `attestation_id` PK; `sense_slug`, `source_id` FKs | A span-bound, rights-resolved use of a sense; it is not an authored example. |
| `practice_decks` | `deck_slug` PK | Versioned deck identity and scope. |
| `practice_deck_items` | `deck_slug`, `sense_slug` FKs | A deck's intentional link to a reviewed sense, optionally with an attestation FK. |

Foreign keys use these stable slugs/IDs, never a rowid, an FTS rank, a display
head, or a generated file position. Slugs are NFC-normalized, case-folded only
where the existing route/search policy requires it, and are immutable after
publication. A renamed route keeps its old slug as an alias or explicit
redirect; it does not retarget existing foreign keys.

For an unambiguous headword, `entry_slug` can be the route slug, such as
`прапор`. Homographs receive separate `lemma_entries` before sense, SRS, or
export IDs are frozen. The required disambiguator is stable and meaningful, for
example `замок#castle` and `замок#lock`; ordinal suffixes such as `замок#1`
and `замок#2` are permitted only when assigned once and must never be
renumbered. Each `sense_slug` appends an immutable local key, for example
`замок#castle:core`. This prevents a search alias for `замок` from collapsing
two lexical entries while allowing it to return both candidates.

`attestation_id` is a deterministic composite of a stable `source_id`,
`chunk_id`, and character `span_start`/`span_end`. `deck_slug` is a
human-readable, versioned deck key (for example `example-test-a1-v1`); a deck
item references `sense_slug`, never an ambiguous spelling. Card-template or
scheduling variants are separate fields, not replacements for the deck or
sense identity.

### Rights registry and attribution

Every source-backed claim has a provenance record. The rights registry stores,
at minimum:

| Field | Meaning |
| --- | --- |
| `source_id`, `source_work`, `author`, `author_uk` | Stable source identity and required attribution names. |
| `canonical_url`, `file_path`, `source_revision` | Retrieval identity; `file_path` is internal-only unless separately cleared. |
| `language_period`, `grade` | Linguistic and educational context when known. |
| `license_type`, `attribution_type`, `rights_status` | Licence, required credit form, and disposition: redistributable, pointer-only, local-only, or rejected. |
| `chunk_id`, `span_start`, `span_end` | Exact source span for an attestation or pointer. |
| `extraction_mode`, `review_state`, `reviewed_at` | How the record entered the projection and whether it is admitted. |

An exportable sentence must carry all of `source_work`, `author_uk` where
applicable, `grade` where applicable, `chunk_id`, `span_start`, and `span_end`.
For a non-redistributable source, public output is a structured pointer or a
rights-permitted short quotation with attribution; it is never an unbounded
text copy. Local-only evidence and private file paths remain out of public
shards, search aliases, and status reports.

### Migration and hydration policy

Phase 0b preserves a single editorial truth during transition. A reader uses a
valid normalized record first, otherwise the legacy record; it must not merge
both representations into duplicate learner-visible content. If both forms are
present but produce different canonical static output, the build fails. Fields
marked **UNMAPPED** in the inventory remain legacy-only until an approved target
and parity migration exist. Deletion requires the inventory's dual-read,
parity, divergent-fixture, and consumer-removal gates.

Projection rebuilds own only projection tables. User-local data, custom deck
migrations, schedules, and progress live in a separate user-state database or
explicitly versioned user-state store. Hydration must not run broad `DROP TABLE`
or unlink logic against a database containing unrecognised user tables. Before
an implementation replaces the current v1 file, it must either preserve a
known user table through a transactional migration to user state or fail
closed with an actionable migration requirement. An orphan table is evidence to
preserve, not permission to wipe it.

## Alternatives considered

- **Make `atlas.db` the writable SSOT**: rejected because a local SQLite file
  is hard to review, reconcile, version, audit for rights, and reproduce from
  a clean checkout.
- **Use one lemma slug for every identical spelling**: rejected because it
  conflates homographs, causes ambiguous practice references, and makes later
  sense separation an identifier-breaking migration.
- **Store attestations as text inside enrichment or deck rows**: rejected
  because source spans, licence decisions, and provenance cannot then be
  independently validated or filtered for public export.
- **Rebuild in place and discard unknown tables**: rejected because it can
  erase custom decks or user migrations and violates the static-projection /
  user-state boundary.

## Consequences

**Positive**:

- Editorial changes remain reviewable in files and can rebuild the same Atlas
  projection and static shards.
- Rights filtering is enforceable at the source/span level rather than inferred
  after sentence text has reached a public deck.
- Homograph-safe keys let dictionary pages, senses, attestations, and practice
  decks refer to the same lexical target without display-text joins.

**Negative / risks**:

- Every imported source needs complete provenance and a rights decision before
  its text can become public, which will quarantine some attractive candidates.
- The v1-to-v2 transition needs dual-read parity work and user-state detection;
  the current destructive v1 rebuild is not a compliant v2 hydration strategy.
- Stable IDs make editorial renames deliberate migrations rather than casual
  data cleanup.

**Neutral / follow-ups**:

- #5791 implements the builder schema, round-trip fixture, foreign-key checks,
  and normalized/legacy shard-parity fixtures.
- #5790 resolves Alona seed and sentence rights before any candidate is
  admitted as an attestation or public Practice content.
- The inventory's unmapped form, morphology, pronunciation, and prescription
  data requires separately approved target models before legacy removal.

## Verification

- A round-trip fixture rebuilds the projection from declared SSOT files and
  verifies logical row and shard determinism.
- Foreign-key, slug uniqueness, homograph, locator completeness, rights-filter,
  and public-path privacy tests fail closed.
- Legacy-only and normalized-only fixtures produce identical canonical shards;
  a both-present divergent fixture fails.
- A hydration fixture with an unknown user table and custom deck migration
  proves preservation or a fail-closed migration error, never deletion.
- Run `.venv/bin/python scripts/audit/check_adrs.py` after regenerating the ADR
  index.
