# Dictionary Pipeline Status

> Updated: 2026-09-30 (ULIF headword repair review fixes, #9338)

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
register `stressed_headword` exactly, including stress and capitalization.
Both walk-time ingest and offline parsing use this rule; recovery without
register identity fails closed. Source spellings are never inferred from the
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
stressed headword, that unanimous identity recovered 5 empty rows in 5 groups.
The remaining 18 rows in 11 groups became `parse_error`: register headwords
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
Definitions and metadata cannot bind. VESUM lookups use indexed exact
candidates (given, casefolded, upper, title,
capitalised and per-hyphen-part capitalised), followed by normalized filtering;
1,490 VESUM forms and 297 lemmas remain unreachable by those candidates and
fail closed. A folded, indexed store is a separate follow-up; the builder and
source lock remain unchanged here to preserve the frozen evaluation release.
Text kinds (`pravopys`, `textbook`)
require a whole-word match of the option or any attested VESUM paradigm form
of its lemmas. Soft hyphens (U+00AD), including a following line break, are
removed before matching; fragments after them cannot bind (`Фор­мат` never
witnesses `мат`). Non-breaking hyphens (U+2011) fold to `-`. Line-end hyphens
inside words are tried both joined and kept (`червиво-\nго` witnesses
`червивого`, never the fragment `го`; `будь-\nякий` witnesses `будь-який`). Standalone
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
