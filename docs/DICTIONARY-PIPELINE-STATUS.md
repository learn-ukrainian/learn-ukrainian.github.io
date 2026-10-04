# Dictionary Pipeline Status

> Updated: 2026-09-30 (ULIF run-mode recovery and source dispositions, #9347)

## In RAG ✅

| Collection | Points | Source |
|-----------|--------|--------|
| sum11 | 127,069 | СУМ-11 — Ukrainian explanatory dictionary (11 volumes) |
| ukrajinet | 122,441 | Ukrajinet WordNet — 48K+ synonym groups |
| literary_texts | 125,316 | Literary texts — 3,257 works, 127 authors |
| balla_en_uk | 78,704 | Балла — English→Ukrainian dictionary |
| grinchenko_dict | 67,275 | Грінченко — Historical dictionary (1907) |
| wiktionary_uk | 50,278 | Вікісловник — definitions, synonyms, antonyms |
| dmklinger_uk_en | 30,111 | dmklinger — Ukrainian→English dictionary |
| frazeolohichnyi | 24,683 | Фразеологічний — Ukrainian idioms |
| textbook_chunks | 23,398 | Textbooks — Grades 1-11 |
| textbook_images | 14,119 | Textbook images |
| style_guide | 279 | Антоненко-Давидович — style guide |
| **TOTAL** | **663,673** | |

## Curated resource discovery (#9409)

The Sources MCP tool `search_resources` searches `resource_catalogue` and its
FTS5 index. Incremental ingestion reads all podcast/raw-list/module-mapping,
external-resource, ULP article, trusted-source, Dobra Forma, Talk Ukrainian and
Verba catalogues, including `docs/resources/ulp-alphabet.yaml`; no media or
premium content is downloaded. The `letters` and `letter_evidence` columns
preserve publisher-evidenced letter/video pairings; `access_evidence` records
the evidence required for `access: free`. Existing
`external_articles` text is linked by URL or ULP/FMU episode identity and indexed
for Ukrainian-word discovery, with chunk provenance and a `linked_resources` count.

```bash
<shared-project-python> -m scripts.ingest.resource_catalogue_ingest \
  --ingest --db data/sources-copy.db
```

`--ingest` enables the metadata ingestion; `--no-network` supports offline tests
and preserves prior link checks. Every file is reconciled by source-entry locator
and normalized URL. Unspecified access remains `unknown`; `free_only` needs a
recorded free resource or audio fact. ULP/FMU top-level access is `mixed`, with
free audio and premium notes recorded separately. `mode: text` is the default:
even one-letter words use full-text search. Only explicit `mode: letter` queries
use the evidenced letter index; curriculum curation selects it only for letter
requirements. Responses cap hits and
provenance without truncating stored catalogue entries; before ingest the tool
returns a typed `resource_catalogue_missing` error.
Databases missing the new columns also require re-ingestion before any resource
search; the driver backs up and re-ingests the live database immediately after merge.
HTTP status and UTC date track link availability. The full-corpus rebuild does
not create these rows: rerun this incremental ingest afterward. Rehearsal on a
local backup precedes independent review and merge; the accountable
driver activates and verifies the live database separately. See
[corpus inventory](corpus-inventory.md#curated-listening-and-reading-catalogues-9409)
for the denominator, access caveats and search interface.

## Owned private references (#9581)

| Ingestion tool | Enable / verify | Private artifacts | Corpus targets |
| --- | --- | --- | --- |
| `scripts.ingest.owned_books_ingest` | Explicit `--inventory`, `--out-dir`, `--db`; `--check` verifies installed state; `--force` replaces stale inputs | Per-work JSONL and digest receipts outside every checkout | `textbooks`, `textbooks_fts`, `textbook_sections` |

The private inventory supplies every row and typed skip. Per-file/page accounting
retains missing files, unreadable inputs and OCR gaps; available text does not hide
partial rows. Garbled PDF pages are withheld and counted separately for OCR;
clean pages remain ingestable. Directory inventories also support UTF-8 CSV
reference text and account for JPEG pages as OCR residuals. Existing works keep their identities; ULP premium
packs list the six already-ingested season identities, each validated against the
corpus and rights record. No sentence-overlap deduplication is used.
New works require matching inventory and registry rights before extraction or
cached JSONL reuse. Exact normalised whole-file duplicates and text wholly
contained in an earlier retained file are accounted as `duplicate_of` without
new chunks. Files whose non-empty normalised units all match units in a single
earlier retained file also add no chunks, regardless of unit order; one new unit
keeps the entire file. Empty files and partial overlaps retain their existing
accounting. Disk and archive metadata are ignored, and
owner-only password PDFs are extracted with restriction accounting.
`registry/sources/owned-rights.yaml` denies all owned quotes and denies citations
of private-permission material. See the [private-reference regeneration
recipe](corpus-inventory.md#private-reference-sources-textbooks). Apply to a local
backup first; the accountable driver applies and verifies the live Sources corpus.

## Need ingestion

| Dictionary | JSONL | Entries | Command |
|-----------|-------|---------|---------|
| PULS CEFR | `data/puls/entries.jsonl` | ~10K | `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0 .venv/bin/python scripts/rag/ingest_style_dictionaries.py --puls` |
| Literary (new) | Грушевський тт.4-10 + Орлика | ~610 chunks | `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0 .venv/bin/python scripts/rag/ingest.py --all-literary --batch-size 16` |

## Local databases (no RAG needed)

### ULIF cached headword recovery (#9338)

DictUA entry selections can open on a relation tab (synonyms or phraseology),
whose article has no `.word_style` headword. The ingest now recovers missing
identity from the separately cached paradigm tab, keeping any identity already
present on the entry page. A recovered paradigm headword must match its
register `stressed_headword` exactly, including stress and capitalization,
when that identity is known. Both walk-time ingest and offline walk parsing
use this rule. Targeted run ledgers have no stressed register identity; their
recovered headword must still match the normalized query spelling. Source
spellings are never inferred from the
query or relation terms.
An identity that cannot be recovered is stored as `parse_error`, not `ok`.

For a bounded, offline replay of affected groups, use the shared project
interpreter with the existing completed walk ledger and live database:

```bash
<shared-project-python> -m scripts.lexicon.runner.fetch_ulif_homonyms parse \
  --state-dir <completed-walk-state-dir> --db <sources.db> --empty-headwords-only
```

The repair snapshots groups containing `status='ok'` rows whose headword is
empty, requires stored ledger units or recorded printed-number-mismatch
residuals and unchanged register positions/homonym indexes, and upserts only
their missing identity. It preserves row IDs,
`homonym_checked`, sections, raw references and original fetch timestamps.
No pages are fetched and no corpus or cache files are removed. Without the
repair flag, `parse` retains its full replay behavior. Repair does not overwrite
the global `differing_content_hashes` meta or duplicate-content flags.

The first bounded cache replay on 2026-09-30 covered 12,687 spelling groups.
The review-fix replay then covered the remaining 23 rows in 16 mismatch groups:

| Measurement | Before | First replay | Review-fix replay |
|-------------|--------|--------------|-------------------|
| `ok` rows with an empty headword | 12,899 | 23 | 0 |
| Recovered headwords from that cohort | 0 | 12,817 | 12,822 |
| Unrecoverable cohort rows marked `parse_error` | 0 | 59 | 77 |
| Total entry rows | 269,262 | 269,262 | 269,262 |
| Section rows | 336,396 | 336,396 | 336,396 |
| Raw-cache objects | 943,308 | 943,308 | 943,308 |

The 16 groups still have printed homonym numbers that disagree with
register-order indexes. Where every register row in a group carries one exact
stressed headword, that unanimous identity recovered 5 empty rows in 4 groups.
The remaining 18 rows in 12 groups became `parse_error`: register headwords
differ in stress or capitalization. No homonym ordering was assigned. Their
ledger units remain `error`, with the original mismatch reason and a separate
headword-repair reason. Repeated repair excludes those units from the stored
group requirement, reports them as residuals, and makes no data or ledger
writes once no empty `ok` rows remain (regression-tested).

The other 59 empty rows still have no identity on any cached page of their
completed entry attempt; all were separately re-parsed during this round.
They remain unavailable as word witnesses. The curriculum-upgrade driver owns
the residuals: reconcile the 16 groups under #8400, and arrange
operator-authorized source recovery for the 59 empty articles. The final worker
report contains every affected residual group/row, its reason and page evidence;
this repair does not claim full ULIF completion. The 6,447 existing `not_found`
rows remain outside the empty-`ok` repair scope.

The review-fix replay preserved all 23 rows' IDs, spelling keys, homonym indexes,
register positions, trust flags, raw references, fetch timestamps, labels,
glosses and content hashes. Full fingerprints matched for all 269,180 rows
outside this round's 82-row evidence cohort and for all section contents. The
59 existing `parse_error` rows were unchanged. Global content meta remained
12,671 and all duplicate-content flags were unchanged.

All 12,899 cohort rows retained their IDs, spelling keys, homonym indexes,
register positions, trust flags, raw references and fetch timestamps. A
before/after fingerprint matched for the 256,363 rows outside the cohort.
A preselected sample of 20 recovered rows (the reported example plus 19
seeded samples) matched cached ULIF headwords in all 20 cases. The Sources
MCP `verify_words` VESUM check found 19/20: `безкінечно` was absent from VESUM,
while cache-only `query_ulif` attested `безкіне́чно` (`ulif:23553`). This is
reported as a dictionary coverage difference, not a judgement against the
source spelling. VESUM verifies morphology, not the retained ULIF stress.

### ULIF run-mode recovery and residual disposition (#9347)

The run-mode regression is fixed: the stress-exact check applies only when
`stressed_headword` is known. The normalized spelling check still binds in
run mode. Captured synonyms-plus-paradigm fixtures cover direct recovery,
wrong-spelling refusal, full run-mode replay and bounded identity repair;
walk-mode stress and capitalization checks remain covered.

On 2026-09-30, all 59 empty-article rows (57 spelling groups) were selected
once through the existing `HomonymFetcher`, with healthy sibling selections
filtered out. Fresh register membership and stressed headwords were compared
with the completed walk before accepting each selection. The standard runner
lock, one session, sequential requests, at least one second between requests,
back-off and immutable raw-cache storage were used. The bounded run made
270 HTTP requests; all 59 target selections completed with HTTP 200 between
19:08:24 and 19:12:55 UTC. Every selected entry and its paradigm tab still
lacked `.word_style`, an article panel and a paradigm table. The source thus
provided no lemma article to recover; relation-tab material was not used as
identity. No cache or corpus was deleted or moved.

The cached article/paradigm pages for all 49 register entries in the 16
mismatch groups were inspected. These are source observations, not permission
to renumber: every group's printed numbers still conflict with register order
under the governing [#8400 plan](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8400).
No group could be resolved from that evidence and no index was reassigned:

| Group | Register indexes | Printed numbers | Disposition |
|-------|------------------|-----------------|-------------|
| віскряк | 1 | 2 | Unresolved |
| глевтяк | 1 | 2 | Unresolved |
| любка | 1,2,3,4 | 1,2,1,2 | Unresolved |
| нориця | 1,2,3,4 | 1,2,1,2 | Unresolved |
| об'їздити | 1,2,3,4 | 1,2,1,2 | Unresolved |
| пара | 1,2,3,4,5 | 1,2,1,2,3 | Unresolved |
| підмет | 1,2 | 2,1 | Unresolved |
| розкидати | 1,2,3,4 | 1,2,1,2 | Unresolved |
| розкидатися | 1,2,3,4,5 | 1,2,1,2,3 | Unresolved |
| розсипатися | 1,2,3,4,5,6 | 1,2,3,1,2,3 | Unresolved |
| сп'янілий | 1 | 2 | Unresolved |
| сповнитися | 1,2 | 2,1 | Unresolved |
| співанка | 1,2 | 2,1 | Unresolved |
| спірний | 1,2 | 2,1 | Unresolved |
| чайка | 1,2,3,4 | 1,2,1,2 | Unresolved |
| ялівник | 1,2 | 2,3 | Unresolved |

There was no recoverable identity to apply. One bounded replay through the
fixed parser was a no-op. The per-row disposition table for all 77 residual
rows is posted on [issue #9347](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/9347#issuecomment-5918340705).
Source-response digests are recorded in that table; raw responses remain in
canonical ULIF cache objects with their `stored_at` times. Per-row request
digests were not retained.

| Measurement | Before | After |
|-------------|--------|-------|
| Total entry rows | 269,262 | 269,262 |
| `ok` | 262,738 | 262,738 |
| `parse_error` | 77 | 77 |
| `not_found` | 6,447 | 6,447 |
| `ok` rows with an empty headword | 0 | 0 |
| Section rows | 336,396 | 336,396 |
| Recovered from the 77-row cohort | 0 | 0 |

Before/after fingerprints cover all 269,185 out-of-cohort entries and all
336,396 sections; the 77 cohort rows are compared in full. The production
ledger's meta and spelling records are unchanged. The curriculum-upgrade
driver owns the remaining 77 unavailable identities and 16 numbering groups,
plus exact-head cross-family review and landing of this fix. This source
disposition does not claim recovery or completion of the full ULIF plan.

VTS receipt citations use bounded retained snapshots in
`sources.db:slovnyk_me_entries` (#9296). Import existing schema-v4 cache files
offline with `scripts/ingest/slovnyk_me_ingest.py --cache-dir
data/lexicon/slovnyk_cache --dict vts --db <sources.db>` using the project
interpreter. Add `--dry-run` to preview; optional positional words restrict
the import. This follows the [bounded per-word recipe](audits/slovnyk-me-ingestion-feasibility.md):
200-character text cap by default, original URL and fetch timestamp retained,
upsert without deleting cache or corpus. It is neither a bulk crawl nor a full
dictionary mirror. `vts:<id>` refers to the imported row's local SQLite id.

Receipt ids bind to the option's **word**, for `valid` and `invalid`
judgements alike; this proves source identity, never judgement correctness.
Canonical VESUM citations use the exact `vesum:N-M` source location. Legacy
bare integers bind if either entry-id or form-id namespace binds. Comparison
normalizes stress accents, apostrophe variants and Unicode casefolding;
whitespace and letters remain exact. Option lemmas come only from attested
VESUM analyses, never suffix rules or guessed lemmas. Dictionary kinds
(`vesum`, `sum20`, `ulif`, `grinchenko`, `vts`) require the row's
real witness fields to equal the option or one of those lemmas: VESUM
`word_form`/`lemma`, СУМ-20 `headword`/`stressed_headword`, Грінченко and VTS
`word`, ULIF `canonical_headword`. Only ULIF rows with `status='ok'` bind,
including for invalid options; a negative lookup is not a word witness.
Definitions and metadata cannot bind. VESUM store v2 adds indexed folded
`word_form`/`lemma` keys; receipt lookup uses them through the unchanged
marker-filtered four-column `forms` view. Source rows, canonical digest and
cited-row digests exclude these derived keys. The full-store census reaches
all 3,764,650 distinct compatible forms and
408,202 lemmas (0/0 unreachable), with the canonical digest unchanged. It
retains the pinned v6.8.0 asset and marker policy; older stores keep the exact
candidate
fallback and its 1,490-form / 297-lemma reachability gap until activation.
The frozen `ua_eval_harness` releases read the original lock and parser
copies under `data/projects/ua_eval_harness/releases/v0.1.1/`, recovered
from freeze commit `1497ad6a729ecdf97031bbd9d44059528a354608`. Their manifests,
lock hash and baseline results remain byte-identical as the live lock advances.
Build an explicit shadow with `scripts/rag/build_vesum_shadow.py`; activation
remains a separate driver operation after review and merge.
Text kinds (`pravopys`, `textbook`)
require a whole-word match of the option or any attested VESUM paradigm form
of its lemmas. Soft hyphens (U+00AD), including a following line break, are
removed in both witness and option before matching. Spaces after a soft hyphen
are preserved unless a line break follows; fragments after them cannot bind
(`Фор­мат` never
witnesses `мат`). Non-breaking hyphens (U+2011) fold to `-`. Line-end hyphens
inside words are tried both joined and kept (`червиво-\nго` witnesses
`червивого`, never the fragment `го`; `будь-\nякий` witnesses `будь-який`).
The kept interpretation also binds `червиво-го`; this is pinned string identity,
not evidence that the option is a valid lexical form. Standalone
one-letter options and paradigm witnesses are refused; witnesses need at least
two letters. Longer function words may bind by whole-word occurrence: this
proves word identity only, never contextual grammatical support. Multi-word
options require the exact phrase after whitespace runs (including newlines)
collapse to one space in both the option and source text; separate tokens or
paradigm variants cannot bind a phrase. Case correctness is checked by the
language judgement elsewhere.
Other existing rows refuse with `evidence_form_mismatch`. Live Pravopys
receipts use `pravopys-live-section-v1` identities.

| Resource | File | Size |
|---------|------|------|
| VESUM | `data/vesum.db` | 409K lemmas, 6.7M forms |
| UberText frequency | `data/ubertext-freq/frequency.db` | 12.4M rows (SQLite) |
| PULS CEFR | `data/puls/entries.jsonl` + `puls_cefr.csv` | ~10K words (A1-C1) |
| СУМ-11 registers | `data/sum11/registers.jsonl` | 25,565 labeled words |
| Stress dictionary | `ukrainian-word-stress` lib | 2.7M forms |
| Wikipedia cache | `data/wiki_cache.db` | Full UK Wiki |

## Deterministic text ingesters

`scripts/ingest/dictionary_ingest.py` adds deterministic, source-specific
plain-text ingestion for the private dictionary materials tracked by
issues #1663-#1666. The ingester creates one rich table plus one FTS5 table
per source:

| Source flag | Tables | Expected rows | Input shape |
|-----------|--------|---------------|-------------|
| `antonenko` | `style_antonenko`, `style_antonenko_fts` | ~500-700 | Paragraph usage notes from «Як ми говоримо» |
| `karavansky` | `karavansky_r2u`, `karavansky_r2u_fts` | ~5K | RU lemma → Ukrainian translations, one entry per line |
| `holovashchuk` | `style_holovashchuk`, `style_holovashchuk_fts` | ~3K-8K | Ukrainian lemma → usage/register notes |
| `paronyms` | `paronyms_full`, `paronyms_full_fts` | ~1.5K | Paronym pair → meanings/examples |

Run with:

```bash
.venv/bin/python -m scripts.ingest.dictionary_ingest --source <source> --input docs/references/private/<file>.txt
```

## Remaining gaps

| Gap | Severity | Notes |
|-----|----------|-------|
| Collocations | Medium (C1+) | Derive from UberText corpus later |
| C2 vocabulary | Low (last priority) | Derive from freq + literary chunks |

## Backup

```bash
./scripts/backup-data.sh backup
./scripts/backup-data.sh backup --execute
```
