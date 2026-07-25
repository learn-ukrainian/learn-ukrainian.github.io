# Atlas lexical-layer inventory and migration matrix

**Issue:** #5788
**Umbrella:** #4387
**Status:** Phase 0a inventory only; no database, schema, migration-script, or `scripts/lexicon/` change is proposed here.

## Decision boundary and failure modes

This is an inventory of the public manifest pinned by the current checkout and
the exact Atlas projection rules. `data/atlas.db` is intentionally ignored and
was absent in this worktree, so a direct query of a hydrated file is
**UNKNOWN — not measurable because the real ignored projection file is not
present**. The counts below are instead from a no-file-write, in-memory SQLite
projection of the release-pinned public manifest using the current
`scripts.atlas.atlas_db.migrate_manifest` rules. This does not create, modify,
copy, migrate, or clean up `data/atlas.db`.

The important failure mode is a false claim that an empty local database is the
live dataset. The other failure mode is silently treating an absent target
bucket as a safe deletion. Every such field is marked **UNMAPPED** below and
must remain dual-readable until a separately approved target exists.

The plan of record was read before this inventory from PR #5794's retained
head. The original remote branch had been deleted; the deterministic recovery
was `git fetch origin refs/pull/5794/head:refs/remotes/origin/grok/4387-atlas-lexicon-plan-docs`,
followed by the two required `git show` commands. The raw, non-private excerpt
is in [Evidence E-1](#e-1-plan-of-record). It requires this matrix and says
that the Phase 0b shard exporter must dual-read legacy enrichment and normalized
tables with shard-parity coverage.

## Evidence protocol

Every field name, SQL type, and count in this document comes from the raw
output quoted in this section, not from the plan. `E-3` used a temporary public
release download and an in-memory SQLite connection; it printed no lexeme,
sentence, teacher, or other private-curation content.

### E-1: plan of record

**Deterministic tool and command:** `git` in this worktree.

```sh
git fetch origin refs/pull/5794/head:refs/remotes/origin/grok/4387-atlas-lexicon-plan-docs
git show origin/grok/4387-atlas-lexicon-plan-docs:docs/plans/2026-07-25-atlas-open-lexical-layer.md
git show origin/grok/4387-atlas-lexicon-plan-docs:docs/plans/2026-07-25-atlas-open-lexical-layer-ADVISORY-SYNTHESIS.md
```

**Raw output excerpt:**

```text
# Plan of record: Atlas open lexical layer (humans + machines)
...
4. **Migration matrix required** before new tables: map existing `enrichment` sections, `related_entries`, `article_provenance` → target model (no parallel-truth fork).
...
| **0b** | Schema v2 ADR + builder SCHEMA + external source files | Round-trip fixture; FK integrity with `foreign_keys=ON`; **`scripts/atlas/export_runtime_shards.py` dual-reads** legacy `enrichment` sections **and** new normalized tables, proven by a shard-parity test (no lexeme payload may disappear from static Practice shards); ... |
```

### E-2: storage resolution

**Deterministic tools and commands:** `ls`, `git check-ignore`, and `rg` in
this worktree.

```sh
ls -l data/atlas.db
git check-ignore -v data/atlas.db
rg -n -C 4 'CREATE TABLE|article_provenance|related_entries|enrichment' scripts/atlas/atlas_db.py
sed -n '1,110p' site/src/data/lexicon-manifest.pointer.json
```

**Raw output:**

```text
ls: cannot access 'data/atlas.db': No such file or directory
.gitignore:100:*.db  data/atlas.db
DEFAULT_DB = ROOT / "data" / "atlas.db"
CREATE TABLE IF NOT EXISTS article_provenance (
CREATE TABLE IF NOT EXISTS related_entries (
CREATE TABLE IF NOT EXISTS enrichment (
"asset_url": "https://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/download/atlas-manifest/lexicon-manifest-e115e18a453e.json.gz",
"generated_at": "2026-07-19T12:47:14+00:00",
"gz_sha256": "568b7938dd23b6a5addcac3da5885fefc6ab1049f6055dc4b98e6378de2ee81a",
"json_sha256": "e115e18a453e3fdeef0beab6b75e6389fff9c978015048a31ab87a45abce6eb7"
```

### E-3: public-release projection inventory

**Deterministic tools and commands:** `curl`, `gzip`, `shasum`, and
`.venv/bin/python` with the stdlib `sqlite3` module. The command downloaded the
E-2 asset to a `mktemp -d` directory, verified both hashes, decompressed it
there, then called `scripts.atlas.atlas_db.migrate_manifest` against
`Path(':memory:')`. A no-close in-memory connection was used only to run
`PRAGMA table_info` and `SELECT COUNT(...)`; no `data/atlas.db` path was opened.

```sh
curl --fail --silent --show-error --location \
  'https://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/download/atlas-manifest/lexicon-manifest-e115e18a453e.json.gz' \
  --output "$INV_TMP/lexicon-manifest.json.gz"
shasum -a 256 "$INV_TMP/lexicon-manifest.json.gz"
gzip -dc "$INV_TMP/lexicon-manifest.json.gz" > "$INV_TMP/lexicon-manifest.json"
shasum -a 256 "$INV_TMP/lexicon-manifest.json"
INVENTORY_MANIFEST="$INV_TMP/lexicon-manifest.json" .venv/bin/python -
```

The Python stdin program imported `scripts.atlas.atlas_db`, invoked its current
`migrate_manifest` with `Path(':memory:')`, then ran `PRAGMA table_info` and
`COUNT(column)` for the three tables, plus grouped section and top-level payload
field counts. Its raw output is quoted below in full. `COUNT(column)` is the
populated count; `NULL` is `COUNT(*) - COUNT(column)`; `ABSENT` is the number
of section rows without that JSON key.

```text
GZ_SHA256 568b7938dd23b6a5addcac3da5885fefc6ab1049f6055dc4b98e6378de2ee81a
JSON_SHA256 e115e18a453e3fdeef0beab6b75e6389fff9c978015048a31ab87a45abce6eb7
MANIFEST_ENTRIES 17707
PROJECTION_SUMMARY {"aliases": 17698, "articles": 17371, "by_type": {"lemma": 17196, "multiword_term": 175}, "enrichment": 81691, "form_aliases": 336, "payloads": 17706, "provenance": 17397, "related_entries": 1022, "verified_synonym_pairs": 520, "verified_synonym_pairs_unresolved": 0, "verified_synonym_self_pairs_skipped": 0}
TABLE enrichment ROWS 81691
COLUMN enrichment.slug SQL_TYPE=TEXT POPULATED=81691 NULL=0 NOT_NULL=1 PK=0
COLUMN enrichment.section SQL_TYPE=TEXT POPULATED=81691 NULL=0 NOT_NULL=1 PK=0
COLUMN enrichment.payload_json SQL_TYPE=TEXT POPULATED=81691 NULL=0 NOT_NULL=1 PK=0
COLUMN enrichment.source SQL_TYPE=TEXT POPULATED=57515 NULL=24176 NOT_NULL=0 PK=0
COLUMN enrichment.filled_at SQL_TYPE=TEXT POPULATED=0 NULL=81691 NOT_NULL=0 PK=0
COLUMN enrichment.phase SQL_TYPE=TEXT POPULATED=81691 NULL=0 NOT_NULL=0 PK=0
TABLE related_entries ROWS 1022
COLUMN related_entries.slug SQL_TYPE=TEXT POPULATED=1022 NULL=0 NOT_NULL=1 PK=0
COLUMN related_entries.related_slug SQL_TYPE=TEXT POPULATED=1022 NULL=0 NOT_NULL=1 PK=0
COLUMN related_entries.entry_type SQL_TYPE=TEXT POPULATED=0 NULL=1022 NOT_NULL=0 PK=0
COLUMN related_entries.relation SQL_TYPE=TEXT POPULATED=1022 NULL=0 NOT_NULL=1 PK=0
COLUMN related_entries.component_role SQL_TYPE=TEXT POPULATED=0 NULL=1022 NOT_NULL=0 PK=0
COLUMN related_entries.provenance SQL_TYPE=TEXT POPULATED=1022 NULL=0 NOT_NULL=1 PK=0
TABLE article_provenance ROWS 17397
COLUMN article_provenance.slug SQL_TYPE=TEXT POPULATED=17397 NULL=0 NOT_NULL=1 PK=0
COLUMN article_provenance.source_family SQL_TYPE=TEXT POPULATED=17397 NULL=0 NOT_NULL=0 PK=0
COLUMN article_provenance.source_locator SQL_TYPE=TEXT POPULATED=10949 NULL=6448 NOT_NULL=0 PK=0
COLUMN article_provenance.extraction_mode SQL_TYPE=TEXT POPULATED=10949 NULL=6448 NOT_NULL=0 PK=0
ENRICHMENT_SECTIONS
SECTION antonyms ROWS=442
SECTION cefr ROWS=7008
SECTION definition_cards ROWS=6512
SECTION etymology ROWS=5291
SECTION heritage_status ROWS=17371
SECTION idioms ROWS=1882
SECTION literary_attestation ROWS=6507
SECTION meaning ROWS=5654
SECTION morphology ROWS=6747
SECTION pronunciation ROWS=5607
SECTION stress ROWS=6870
SECTION synonyms ROWS=4940
SECTION translation ROWS=6567
SECTION wiki_reference ROWS=293
ENRICHMENT_PAYLOAD_TOP_LEVEL_FIELDS
PAYLOAD antonyms.items TYPES=list:442 POPULATED=442 NULL=0 ABSENT=0
PAYLOAD antonyms.source TYPES=str:442 POPULATED=442 NULL=0 ABSENT=0
PAYLOAD antonyms.source_urls TYPES=list:438 POPULATED=438 NULL=0 ABSENT=4
PAYLOAD cefr.level TYPES=str:7008 POPULATED=7008 NULL=0 ABSENT=0
PAYLOAD cefr.pos TYPES=str:3177 POPULATED=3177 NULL=0 ABSENT=3831
PAYLOAD cefr.source TYPES=str:7008 POPULATED=7008 NULL=0 ABSENT=0
PAYLOAD cefr.text TYPES=str:7008 POPULATED=7008 NULL=0 ABSENT=0
PAYLOAD definition_cards.<payload> TYPES=list:6512 POPULATED=6512 NULL=0 ABSENT=0
PAYLOAD etymology.source TYPES=str:5291 POPULATED=5291 NULL=0 ABSENT=0
PAYLOAD etymology.source_url TYPES=str:77 POPULATED=77 NULL=0 ABSENT=5214
PAYLOAD etymology.text TYPES=str:5291 POPULATED=5291 NULL=0 ABSENT=0
PAYLOAD heritage_status.attestations TYPES=list:17371 POPULATED=17371 NULL=0 ABSENT=0
PAYLOAD heritage_status.calque_warning TYPES=dict:24 POPULATED=24 NULL=17347 ABSENT=0
PAYLOAD heritage_status.classification TYPES=str:17371 POPULATED=17371 NULL=0 ABSENT=0
PAYLOAD heritage_status.curated_calque TYPES=dict:5 POPULATED=5 NULL=0 ABSENT=17366
PAYLOAD heritage_status.is_russianism TYPES=bool:17371 POPULATED=17371 NULL=0 ABSENT=0
PAYLOAD heritage_status.reverse_calques TYPES=list:45 POPULATED=45 NULL=0 ABSENT=17326
PAYLOAD heritage_status.russian_shadow TYPES=bool:17371 POPULATED=17371 NULL=0 ABSENT=0
PAYLOAD heritage_status.vesum_attested TYPES=bool:17371 POPULATED=17371 NULL=0 ABSENT=0
PAYLOAD heritage_status.warning_severity TYPES=str:17371 POPULATED=17371 NULL=0 ABSENT=0
PAYLOAD heritage_status.§6_note TYPES=dict:5 POPULATED=5 NULL=0 ABSENT=17366
PAYLOAD idioms.items TYPES=list:1882 POPULATED=1882 NULL=0 ABSENT=0
PAYLOAD idioms.source TYPES=str:1882 POPULATED=1882 NULL=0 ABSENT=0
PAYLOAD idioms.source_urls TYPES=list:1882 POPULATED=1882 NULL=0 ABSENT=0
PAYLOAD literary_attestation.chunk_id TYPES=str:6507 POPULATED=6507 NULL=0 ABSENT=0
PAYLOAD literary_attestation.source TYPES=str:6507 POPULATED=6507 NULL=0 ABSENT=0
PAYLOAD literary_attestation.source_label TYPES=str:6507 POPULATED=6507 NULL=0 ABSENT=0
PAYLOAD literary_attestation.source_url TYPES=str:6507 POPULATED=6507 NULL=0 ABSENT=0
PAYLOAD literary_attestation.text TYPES=str:6507 POPULATED=6507 NULL=0 ABSENT=0
PAYLOAD meaning.definitions TYPES=list:5654 POPULATED=5654 NULL=0 ABSENT=0
PAYLOAD meaning.note TYPES=str:3849 POPULATED=3849 NULL=0 ABSENT=1805
PAYLOAD meaning.source TYPES=str:5654 POPULATED=5654 NULL=0 ABSENT=0
PAYLOAD meaning.synonyms TYPES=list:9 POPULATED=9 NULL=0 ABSENT=5645
PAYLOAD morphology.form_count TYPES=int:6747 POPULATED=6747 NULL=0 ABSENT=0
PAYLOAD morphology.forms TYPES=list:6747 POPULATED=6747 NULL=0 ABSENT=0
PAYLOAD morphology.marked_form_count TYPES=int:2526 POPULATED=2526 NULL=0 ABSENT=4221
PAYLOAD morphology.marked_forms TYPES=list:2526 POPULATED=2526 NULL=0 ABSENT=4221
PAYLOAD morphology.paradigm TYPES=dict:3672 POPULATED=3672 NULL=0 ABSENT=3075
PAYLOAD morphology.pos TYPES=str:6747 POPULATED=6747 NULL=0 ABSENT=0
PAYLOAD morphology.source TYPES=str:6747 POPULATED=6747 NULL=0 ABSENT=0
PAYLOAD morphology.stress TYPES=dict:6517 POPULATED=6517 NULL=0 ABSENT=230
PAYLOAD pronunciation.ipa TYPES=str:5607 POPULATED=5607 NULL=0 ABSENT=0
PAYLOAD pronunciation.source TYPES=str:5607 POPULATED=5607 NULL=0 ABSENT=0
PAYLOAD stress.form TYPES=str:6870 POPULATED=6870 NULL=0 ABSENT=0
PAYLOAD stress.ipa TYPES=str:495 POPULATED=495 NULL=0 ABSENT=6375
PAYLOAD stress.source TYPES=str:6870 POPULATED=6870 NULL=0 ABSENT=0
PAYLOAD synonyms.items TYPES=list:4940 POPULATED=4940 NULL=0 ABSENT=0
PAYLOAD synonyms.source TYPES=str:4940 POPULATED=4940 NULL=0 ABSENT=0
PAYLOAD synonyms.source_urls TYPES=list:4035 POPULATED=4035 NULL=0 ABSENT=905
PAYLOAD translation.en TYPES=list:6567 POPULATED=6567 NULL=0 ABSENT=0
PAYLOAD translation.note TYPES=str:84 POPULATED=84 NULL=0 ABSENT=6483
PAYLOAD translation.pos TYPES=str:5572 POPULATED=5572 NULL=0 ABSENT=995
PAYLOAD translation.source TYPES=str:6567 POPULATED=6567 NULL=0 ABSENT=0
PAYLOAD translation.source_url TYPES=str:409 POPULATED=409 NULL=0 ABSENT=6158
PAYLOAD wiki_reference.attribution TYPES=str:293 POPULATED=293 NULL=0 ABSENT=0
PAYLOAD wiki_reference.wikipedia TYPES=dict:293 POPULATED=293 NULL=0 ABSENT=0
PAYLOAD wiki_reference.wikisource_url TYPES=str:271 POPULATED=271 NULL=22 ABSENT=0
PAYLOAD wiki_reference.wiktionary_url TYPES=str:293 POPULATED=293 NULL=0 ABSENT=0
```

## Current storage inventory

The table fields and their live projected counts are exactly the E-3 `COLUMN`
rows. They describe the manifest-projected structure generated by
`scripts.atlas.atlas_db.migrate_manifest`, not a pre-existing disk database
file. `related_entries.entry_type` and `related_entries.component_role` are the
only all-null relation fields; `enrichment.filled_at` is the only all-null
enrichment field. The current public release contains 14 live enrichment
sections. `calque_note` is the fifteenth: it is accepted by the current code's
section enum (`ENRICHMENT_SECTIONS` in `scripts/atlas/atlas_db.py`, and the
`CHECK (section IN (...))` constraint on the `enrichment` table) but has **0**
live rows in E-3.

Zero rows is a live count, not an absence. The section is part of the current
projection's accepted shape, so it carries a matrix disposition below like
every other field; leaving it out would let a later migration introduce or
delete it with no declared policy — which is precisely what this matrix exists
to prevent. (Raised by cross-family review of this PR.)

| Storage field | SQL type | Populated | Null | Evidence |
| --- | --- | ---: | ---: | --- |
| `enrichment.slug` | `TEXT` | 81,691 | 0 | E-3 |
| `enrichment.section` | `TEXT` | 81,691 | 0 | E-3 |
| `enrichment.payload_json` | `TEXT` | 81,691 | 0 | E-3 |
| `enrichment.source` | `TEXT` | 57,515 | 24,176 | E-3 |
| `enrichment.filled_at` | `TEXT` | 0 | 81,691 | E-3 |
| `enrichment.phase` | `TEXT` | 81,691 | 0 | E-3 |
| `related_entries.slug` | `TEXT` | 1,022 | 0 | E-3 |
| `related_entries.related_slug` | `TEXT` | 1,022 | 0 | E-3 |
| `related_entries.entry_type` | `TEXT` | 0 | 1,022 | E-3 |
| `related_entries.relation` | `TEXT` | 1,022 | 0 | E-3 |
| `related_entries.component_role` | `TEXT` | 0 | 1,022 | E-3 |
| `related_entries.provenance` | `TEXT` | 1,022 | 0 | E-3 |
| `article_provenance.slug` | `TEXT` | 17,397 | 0 | E-3 |
| `article_provenance.source_family` | `TEXT` | 17,397 | 0 | E-3 |
| `article_provenance.source_locator` | `TEXT` | 10,949 | 6,448 | E-3 |
| `article_provenance.extraction_mode` | `TEXT` | 10,949 | 6,448 | E-3 |

| Live enrichment section | Rows | Evidence |
| --- | ---: | --- |
| `antonyms` | 442 | E-3 |
| `cefr` | 7,008 | E-3 |
| `definition_cards` | 6,512 | E-3 |
| `etymology` | 5,291 | E-3 |
| `heritage_status` | 17,371 | E-3 |
| `idioms` | 1,882 | E-3 |
| `literary_attestation` | 6,507 | E-3 |
| `meaning` | 5,654 | E-3 |
| `morphology` | 6,747 | E-3 |
| `pronunciation` | 5,607 | E-3 |
| `stress` | 6,870 | E-3 |
| `synonyms` | 4,940 | E-3 |
| `translation` | 6,567 | E-3 |
| `wiki_reference` | 293 | E-3 |

The full top-level JSON field inventory, including mixed types, nulls, and
absent-key counts, is the `PAYLOAD` block in E-3. It is repeated as matrix
inputs below so that each actual current field has exactly one disposition.

## Migration matrix

`Current field` is a unique storage selector. Array and object values are
atomic current fields because the existing database stores an opaque
`payload_json`; their untyped internal members are values, not separately
stored fields. `Populated / null / absent` is copied verbatim from E-3. The
action is one of **KEEP**, **MOVE**, **SPLIT**, **DROP**, or **UNMAPPED**.

### Enrichment envelope

| Current field | Populated / null / absent | Target bucket | Action | Rationale |
| --- | --- | --- | --- | --- |
| `enrichment.slug` | 81,691 / 0 / — | **UNMAPPED** | **UNMAPPED** | The target-bucket list has no lemma/entry owner key; do not discard the link. |
| `enrichment.section` | 81,691 / 0 / — | — | **DROP** | Remove only after the decoded field rows below are materialized and parity-tested. |
| `enrichment.payload_json` | 81,691 / 0 / — | — | **DROP** | Opaque envelope; its live child fields receive their own rows below. |
| `enrichment.source` | 57,515 / 24,176 / — | provenance | **MOVE** | Section source labels become claim provenance. |
| `enrichment.filled_at` | 0 / 81,691 / — | — | **DROP** | All values are null; preserve no invented timestamp. |
| `enrichment.phase` | 81,691 / 0 / — | provenance | **MOVE** | Retain ingestion-stage evidence with the migrated claim. |

### Senses and related claim data

| Current field | Populated / null / absent | Target bucket | Action | Rationale |
| --- | --- | --- | --- | --- |
| `meaning.definitions` | 5,654 / 0 / 0 | senses | **SPLIT** | A list must become individually addressable teaching senses. |
| `meaning.note` | 3,849 / 0 / 1,805 | senses | **MOVE** | It qualifies the meaning claim. |
| `meaning.source` | 5,654 / 0 / 0 | provenance | **MOVE** | It attributes the meaning claim. |
| `meaning.synonyms` | 9 / 0 / 5,645 | relations | **MOVE** | Explicit synonym values are lexical links, not definitions. |
| `definition_cards.<payload>` | 6,512 / 0 / 0 | senses | **SPLIT** | Each legacy card must be evaluated as a separately sourced sense claim. |
| `translation.en` | 6,567 / 0 / 0 | senses | **SPLIT** | Multiple English labels may distinguish senses. |
| `translation.note` | 84 / 0 / 6,483 | senses | **MOVE** | It qualifies the translation claim. |
| `translation.pos` | 5,572 / 0 / 995 | **UNMAPPED** | **UNMAPPED** | Part-of-speech is entry/form metadata; none of the five buckets owns it. |
| `translation.source` | 6,567 / 0 / 0 | provenance | **MOVE** | It attributes the translation claim. |
| `translation.source_url` | 409 / 0 / 6,158 | provenance | **MOVE** | It is a source locator. |
| `etymology.text` | 5,291 / 0 / 0 | **UNMAPPED** | **UNMAPPED** | Etymological assertion has no target bucket; it is neither a source locator nor a teaching sense by default. |
| `etymology.source` | 5,291 / 0 / 0 | provenance | **MOVE** | It attributes the etymological assertion. |
| `etymology.source_url` | 77 / 0 / 5,214 | provenance | **MOVE** | It is a source locator. |
| `cefr.level` | 7,008 / 0 / 0 | **UNMAPPED** | **UNMAPPED** | Pedagogical level needs an approved entry/sense pedagogy owner. |
| `cefr.pos` | 3,177 / 0 / 3,831 | **UNMAPPED** | **UNMAPPED** | Grammatical metadata has no target bucket. |
| `cefr.source` | 7,008 / 0 / 0 | provenance | **MOVE** | It attributes the CEFR claim. |
| `cefr.text` | 7,008 / 0 / 0 | **UNMAPPED** | **UNMAPPED** | Current free text needs a defined pedagogical claim model. |

### Relations

| Current field | Populated / null / absent | Target bucket | Action | Rationale |
| --- | --- | --- | --- | --- |
| `synonyms.items` | 4,940 / 0 / 0 | relations | **MOVE** | Values become relation-edge targets after endpoint resolution. |
| `synonyms.source` | 4,940 / 0 / 0 | provenance | **MOVE** | It attributes the synonym claim. |
| `synonyms.source_urls` | 4,035 / 0 / 905 | provenance | **MOVE** | It supplies source locators. |
| `antonyms.items` | 442 / 0 / 0 | relations | **MOVE** | Values become antonym-edge targets after endpoint resolution. |
| `antonyms.source` | 442 / 0 / 0 | provenance | **MOVE** | It attributes the antonym claim. |
| `antonyms.source_urls` | 438 / 0 / 4 | provenance | **MOVE** | It supplies source locators. |
| `idioms.items` | 1,882 / 0 / 0 | relations | **SPLIT** | An idiom list can contain both a link and an independently publishable lexical entry. |
| `idioms.source` | 1,882 / 0 / 0 | provenance | **MOVE** | It attributes the idiom relation or entry claim. |
| `idioms.source_urls` | 1,882 / 0 / 0 | provenance | **MOVE** | It supplies source locators. |
| `related_entries.slug` | 1,022 / 0 / — | relations | **MOVE** | Preserve the relation's source endpoint. |
| `related_entries.related_slug` | 1,022 / 0 / — | relations | **MOVE** | Preserve the relation's target endpoint. |
| `related_entries.entry_type` | 0 / 1,022 / — | relations | **MOVE** | Move the nullable endpoint-type qualifier into the normalized edge. |
| `related_entries.relation` | 1,022 / 0 / — | relations | **MOVE** | Move the existing edge predicate into the normalized edge. |
| `related_entries.component_role` | 0 / 1,022 / — | relations | **MOVE** | Move the nullable component-role qualifier into the normalized edge. |
| `related_entries.provenance` | 1,022 / 0 / — | provenance | **MOVE** | Move the edge verification state to its provenance record. |

### Attestations

| Current field | Populated / null / absent | Target bucket | Action | Rationale |
| --- | --- | --- | --- | --- |
| `literary_attestation.text` | 6,507 / 0 / 0 | attestations | **SPLIT** | Admit only a rights-resolved attestation record; the current text alone is insufficient. |
| `literary_attestation.chunk_id` | 6,507 / 0 / 0 | provenance | **MOVE** | It is the current locator component for the attestation record. |
| `literary_attestation.source` | 6,507 / 0 / 0 | provenance | **MOVE** | It attributes the candidate attestation. |
| `literary_attestation.source_label` | 6,507 / 0 / 0 | provenance | **MOVE** | It identifies the source label. |
| `literary_attestation.source_url` | 6,507 / 0 / 0 | provenance | **MOVE** | It is a source locator. |
| `heritage_status.attestations` | 17,371 / 0 / 0 | attestations | **SPLIT** | Legacy aggregate values require individual locator, rights, and review admission. |

### Prescriptions

| Current field | Populated / null / absent | Target bucket | Action | Rationale |
| --- | --- | --- | --- | --- |
| `heritage_status.calque_warning` | 24 / 17,347 / 0 | prescriptions | **SPLIT** | A warning must become a sourced stance plus editorial strength. |
| `heritage_status.classification` | 17,371 / 0 / 0 | prescriptions | **SPLIT** | Classification requires an authority-specific stance rather than one project label. |
| `heritage_status.curated_calque` | 5 / 0 / 17,366 | prescriptions | **SPLIT** | Curated object needs source evidence, stance, and editorial strength. |
| `heritage_status.is_russianism` | 17,371 / 0 / 0 | **UNMAPPED** | **UNMAPPED** | A boolean is explicitly incompatible with the plan's multi-authority prescription model. |
| `heritage_status.reverse_calques` | 45 / 0 / 17,326 | prescriptions | **SPLIT** | Each candidate needs a separately sourced stance. |
| `heritage_status.russian_shadow` | 17,371 / 0 / 0 | **UNMAPPED** | **UNMAPPED** | Boolean classifier evidence has no authority/frequency target record. |
| `heritage_status.warning_severity` | 17,371 / 0 / 0 | prescriptions | **SPLIT** | Editorial severity must be tied to an explicit policy and stance. |
| `heritage_status.§6_note` | 5 / 0 / 17,366 | prescriptions | **SPLIT** | The legacy note needs a defined editorial-stance representation. |

### Provenance and unsupported form metadata

| Current field | Populated / null / absent | Target bucket | Action | Rationale |
| --- | --- | --- | --- | --- |
| `article_provenance.slug` | 17,397 / 0 / — | **UNMAPPED** | **UNMAPPED** | It is the same missing lemma/entry owner key as `enrichment.slug`; do not discard the link. |
| `article_provenance.source_family` | 17,397 / 0 / — | provenance | **KEEP** | It is already source-family provenance. |
| `article_provenance.source_locator` | 10,949 / 6,448 / — | provenance | **SPLIT** | Generic locator must expand to the plan's structured, rights-safe locator fields where applicable. |
| `article_provenance.extraction_mode` | 10,949 / 6,448 / — | provenance | **KEEP** | It records the ingestion method. |
| `wiki_reference.attribution` | 293 / 0 / 0 | provenance | **MOVE** | It is attribution metadata. |
| `wiki_reference.wikipedia` | 293 / 0 / 0 | provenance | **SPLIT** | Keep reference identity in provenance; route any extracted gloss or definition only after explicit sense admission. |
| `wiki_reference.wikisource_url` | 271 / 22 / 0 | provenance | **MOVE** | It is a source locator. |
| `wiki_reference.wiktionary_url` | 293 / 0 / 0 | provenance | **MOVE** | It is a source locator. |
| `heritage_status.vesum_attested` | 17,371 / 0 / 0 | **UNMAPPED** | **UNMAPPED** | Morphological-attestation evidence has no target bucket. |
| `morphology.form_count` | 6,747 / 0 / 0 | **UNMAPPED** | **UNMAPPED** | Inflection inventory needs an approved lexeme/form layer. |
| `morphology.forms` | 6,747 / 0 / 0 | **UNMAPPED** | **UNMAPPED** | Inflected forms have no target bucket. |
| `morphology.marked_form_count` | 2,526 / 0 / 4,221 | **UNMAPPED** | **UNMAPPED** | Marked-form aggregate needs an approved lexeme/form layer. |
| `morphology.marked_forms` | 2,526 / 0 / 4,221 | **UNMAPPED** | **UNMAPPED** | Marked inflections have no target bucket. |
| `morphology.paradigm` | 3,672 / 0 / 3,075 | **UNMAPPED** | **UNMAPPED** | Paradigm structure has no target bucket. |
| `morphology.pos` | 6,747 / 0 / 0 | **UNMAPPED** | **UNMAPPED** | Part-of-speech is entry/form metadata, not a target bucket. |
| `morphology.source` | 6,747 / 0 / 0 | provenance | **MOVE** | It attributes the unsupported morphology claim pending its target model. |
| `morphology.stress` | 6,517 / 0 / 230 | **UNMAPPED** | **UNMAPPED** | Stress pattern data needs a lexeme/form owner. |
| `pronunciation.ipa` | 5,607 / 0 / 0 | **UNMAPPED** | **UNMAPPED** | Pronunciation is lexical-form data, not a target bucket. |
| `pronunciation.source` | 5,607 / 0 / 0 | provenance | **MOVE** | It attributes the pronunciation claim. |
| `stress.form` | 6,870 / 0 / 0 | **UNMAPPED** | **UNMAPPED** | Stressed spelling needs a lexeme/form owner. |
| `stress.ipa` | 495 / 0 / 6,375 | **UNMAPPED** | **UNMAPPED** | Stress-specific pronunciation needs a lexeme/form owner. |
| `stress.source` | 6,870 / 0 / 0 | provenance | **MOVE** | It attributes the stress claim. |

### Schema-accepted section with no live rows

| Current field | Populated / null / absent | Target bucket | Action | Rationale |
| --- | --- | --- | --- | --- |
| `calque_note.<payload>` | 0 / 0 / 0 | **UNMAPPED** | **UNMAPPED** | Accepted by `ENRICHMENT_SECTIONS` and by the `enrichment.section` CHECK constraint, but unpopulated in the pinned release, so its payload shape is unobserved and cannot be mapped from evidence. A prescription-style target is plausible — a calque note is a normative claim — but DC-C requires multi-authority stances, and guessing a bucket from an empty section is exactly the invented-truth this matrix forbids. Disposition required before any migration touches the section enum. |

## UNMAPPED design gaps — blocking for legacy deletion

The following are deliberately not forced into a misleading bucket. Their
current live counts are E-3 evidence. They require an approved lemma/entry,
form, etymology, or pedagogy projection before migration code can delete the
legacy shape.

| Gap | Current field(s) | E-3 live count |
| --- | --- | --- |
| Owner identity | `enrichment.slug`, `article_provenance.slug` | 81,691; 17,397 populated |
| Pedagogy | `cefr.level`, `cefr.pos`, `cefr.text` | 7,008; 3,177; 7,008 populated |
| Etymological assertion | `etymology.text` | 5,291 populated |
| Boolean prescription/classifier state | `heritage_status.is_russianism`, `heritage_status.russian_shadow` | 17,371 each populated |
| Morphological evidence flag | `heritage_status.vesum_attested` | 17,371 populated |
| Form and morphology layer | `morphology.form_count`, `morphology.forms`, `morphology.marked_form_count`, `morphology.marked_forms`, `morphology.paradigm`, `morphology.pos`, `morphology.stress` | 6,747; 6,747; 2,526; 2,526; 3,672; 6,747; 6,517 populated |
| Pronunciation and stress form layer | `pronunciation.ipa`, `stress.form`, `stress.ipa` | 5,607; 6,870; 495 populated |
| Translation grammar label | `translation.pos` | 5,572 populated |
| Unobserved accepted section | `calque_note` | 0 rows (schema-accepted) |

## Dual-read and deprecation policy

### Reader resolution

For every matrix row with a non-**UNMAPPED** destination:

1. Read the normalized target record first, but only when it passes that
   target's required shape and provenance validation.
2. If no valid normalized record exists, read the legacy enrichment/table
   value. This is fallback, not a merge: a reader must not concatenate old and
   new values and duplicate learner-visible content.
3. If both valid representations exist, emit the normalized one and compare
   canonical shard output. A mismatch is a test failure; freshness, timestamp,
   or arbitrary source preference must not resolve it.
4. **UNMAPPED** fields remain legacy-only. No reader may synthesize, coerce, or
   delete them merely to make the normalized view look complete.

### Dual-read duration and deletion gate

The plan supplies a condition but no calendar duration. Therefore duration is
**UNKNOWN — not measurable because the plan records no time-based retention
period**. Both shapes are served from the first Phase 0b dual-read release
through the first release after all of these conditions hold:

1. Every matrix row is either parity-migrated or remains explicitly
   **UNMAPPED**; none is silently dropped.
2. All **UNMAPPED** rows have a separately approved target disposition. This
   is required before deleting their legacy values.
3. Legacy-only and normalized-only input produce byte-identical canonical
   static Practice shards for the migrated fields, with no missing payload.
4. A both-present, intentionally divergent fixture fails closed rather than
   choosing one representation silently.
5. A reader inventory finds no remaining production consumer of the legacy
   field after the fallback branch is removed.

The old shape is safe to delete only in the release after all five gates pass.
In particular, the all-null `enrichment.filled_at` is safe to drop only as an
empty datum; it is not permission to manufacture a replacement timestamp.

### Required transition test

E-4 below establishes that
`tests/test_export_runtime_shards.py::test_exported_entry_records_match_sqlite_projection`
is the existing shard/SQLite parity test. The Phase 0b implementation must
extend that exact test with three fixtures: legacy-only, normalized-only, and
both-present-divergent. The first two must compare canonical emitted shard
bytes; the divergent fixture must raise a deterministic error. That expanded
test is the named guard that catches a broken dual-read transition.

**Current test-coverage caveat:** no exact dual-read test function exists yet,
so a claim that the present suite already proves dual-read would be false. E-4
names the real current test and its current scope; this policy makes its
extension an implementation acceptance gate rather than inventing a test that
does not exist.

### E-4: existing test location and scope

**Deterministic tool and command:** `rg` in this worktree.

```sh
rg -n -C 3 'parity|dual.read|enrichment|legacy|normalized' \
  tests/test_export_runtime_shards.py scripts/atlas/export_runtime_shards.py
```

**Raw output excerpt:**

```text
tests/test_export_runtime_shards.py:313:def test_exported_entry_records_match_sqlite_projection(fixture_db: Path, tmp_path: Path) -> None:
tests/test_export_runtime_shards.py-314-    """Export records must match the Sqlite data-source projection (parity input)."""
tests/test_export_runtime_shards.py-315-    out = tmp_path / "out"
...
docs/plans/2026-07-25-atlas-open-lexical-layer.md:69:... `scripts/atlas/export_runtime_shards.py` dual-reads legacy `enrichment` sections and new normalized tables, proven by a shard-parity test ...
```

## Scope verification

This file is documentation only. The required implementation work remains
outside this issue: no `atlas.db` hydration, schema change, migration script,
or `scripts/lexicon/` edit was made. The evidence commands above use only the
public release asset pinned by the tracked pointer and print aggregate shape
data, never curated rows or sentence text.
