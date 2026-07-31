# Existing Corpus Asset Recovery and Lineage Audit

> **Snapshot:** 2026-07-31
> **Issue:** [#6107](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6107)
> **Scope:** Existing assets only. No acquisition, OCR, scraping, ingestion,
> restoration, generation, model inference, training, upload, or publication.

## Outcome

The project still possesses a substantial Ukrainian-language asset base. The
invalid 5,000-record literary export did not invalidate the underlying corpus:
the live database retains 137,723 literary chunks, Google Drive retains 229
literary JSONL source files, and their filename-stem identities reconcile
229/229. The public/external human-authored text view contains 189,150 database
rows and 50,298,925 lexical words. A separate private-reference view contains
5,786 rows and 681,925 lexical words.

The material is not training-ready or redistribution-cleared. No collection has
a complete `source-record-v1` admission record in this audit, so the current
training-admission quantity is exactly zero. The durable result is a
metadata-only, schema-validated recovery ledger that keeps origin and boundary
classes separate and points to the evidence needed for later reconstruction.

## Definite, recoverable, and unresolved assets

| State | Verified result | Disposition |
| --- | --- | --- |
| Definite current corpus | 137,723 literary, 54,979 textbook, 1,205 external, 1,029 Wikipedia, and 22,385 project-wiki rows | Preserve; use as internal reference under current policy; reconstruct provenance before admission or redistribution |
| Definite raw literary sources | 229 literary JSONL files; 229 database source groups; no filename-stem mismatch | Best lineage starting point for existing literary material |
| Definite textbook raw/chunk assets | 170 PDFs plus one non-PDF in `textbooks/`; 158 chunk JSONLs; grades 1–11 represented | Preserve; public/private rights remain separate and unresolved for export |
| Definite current generated curriculum | 311 A1–B2 modules, 40 FOLK modules, five experimental BIO modules | Synthetic/unknown-origin research only; never merge with human-authored gold |
| Definite machine translation | 554 KubeDojo Ukrainian Markdown files | Translationese, calque, and error-analysis evidence only |
| Definite tracked archives | 12,347 files: 11,937 curriculum archive, 402 general archive, eight archived FOLK plans | Already preserved in current Git |
| Git-recoverable packages | Six historical FOLK package versions at two commits | Keep locators; do not restore automatically |
| Planned without build evidence | Six archived FOLK plans have no `module.md` evidence in Git | Say “not evidenced as built,” never “never existed” |
| Raw lineage unresolved | Two textbook source IDs are database-only or raw-chunk unresolved | Reconstruct from retained edition/catalogue evidence during a consumer-scoped audit |
| Unknown/potentially lost | Four orphan OCR text files, the exact unsatisfactory BIO subset, and anything never committed or retained | Preserve locators and uncertainty; Git cannot recover never-committed bytes |

At the ledger snapshot, the read-only
`git fsck --full --no-reflogs --unreachable` result was not empty: it found 254
commits, 843 trees, and 259 blobs. The collector path-screened all 254
unreachable commits and recorded the screen with the object counts; none
touched scoped `archive/**` or `curriculum/l2-uk-en/**` paths. This evidence
does not authorize repository-wide garbage collection. Counts can change when
Git refs or maintenance state change, so the ledger is the canonical snapshot.

No tracked filename under the scoped archive trees matched common model-weight
or adapter suffixes (`.safetensors`, `.gguf`, `.onnx`, `.bin`, `.pt`, `.pth`,
`.ckpt`, or `.adapter`). “Models” in older evidence cannot therefore be assumed
to mean retained model weights.

## Measurement contract

The collector opens SQLite with `mode=ro` and `PRAGMA query_only=ON`. It counts
stored text rather than trusting table `char_count` fields, which are stale in
some collections.

- **Content unit:** collection-specific row, file, work, form, task, or source
  group; the ledger never sums unlike unit labels into a misleading total.
- **Lexical word:** Python Unicode regex
  `[^\W\d_]+(?:[’'][^\W\d_]+)*`.
- **Whitespace token:** `str.split()`; reported only as a reproducible proxy.
- **Model token:** not measured. Tokenizer-specific counts remain pending and
  are not inferred from whitespace tokens.
- **Distinct-content view:** included in size totals.
- **Overlap/metadata view:** excluded from distinct-content size totals.

### Human-authored content and lexical resources

| Boundary/category | Units | Characters | Lexical words | Whitespace tokens |
| --- | ---: | ---: | ---: | ---: |
| Literary | 137,723 rows | 244,009,438 | 36,031,758 | 38,090,895 |
| Public/external textbooks | 49,193 rows | 69,190,017 | 9,564,143 | 10,368,039 |
| External articles/transcripts | 1,205 rows | 11,597,743 | 1,837,518 | 1,851,232 |
| Ukrainian Wikipedia | 1,029 rows | 22,229,438 | 2,865,506 | 3,060,307 |
| **Public/external human text total** | **189,150 rows** | **347,026,636** | **50,298,925** | **53,370,473** |
| Private curriculum references | 5,786 rows | 6,358,334 | 681,925 | 660,738 |
| **Human text including private references** | **194,936 rows** | **353,384,970** | **50,980,850** | **54,031,211** |

The literary collection represents 229 source groups and 3,307 distinct
`work_id` values. Other collections do not expose one comparable, deduplicated
work identity, so 3,307 is a literary-work count, not a claim about all corpus
works. Only 11,064 literary rows across 24 source groups currently carry a
`source_url`; 126,659 rows require another provenance locator.

Ten human-authored dictionary/morphology collections contribute 525,303
lexical rows plus 6,691,276 VESUM form rows. VESUM contains 408,974 distinct
lemmas and 3,817,098 distinct surface forms in this snapshot. These are lexical
or morphological records, not contextual training words. Ukrajinet's 122,441
largely machine-translated lexical rows and dmklinger's 30,111 unknown-origin
rows remain in their own origin classes.

### Period, genre, grade, subject, register, and region coverage

The literary period overlap views contain 107,436 modern rows (27,994,629
lexical words), 20,085 Middle Ukrainian rows (5,435,144 words), and 10,202 Old
East Slavic rows (2,601,985 words). These partition the literary table in the
current schema and are not added to the corpus total a second time.

The largest literary genres are scholarly (40,480), prose (33,186), chronicle
(18,777), poetry (14,184), encyclopedia (11,459), philosophy (2,954), polemic
(2,844), and biography (2,446). Standalone folk-primary genre labels remain
thin: 35 rows across historical song, duma, carol, harvest song, and spring
song.

Public textbook rows cover grades 1–11. Grade counts are 394, 746, 939, 986,
3,563, 3,588, 6,286, 6,939, 6,974, 8,984, and 9,597 respectively, plus 197
public lexicon rows with no grade. Major subjects include Ukrainian language
(10,940), Ukrainian literature (6,323), history (6,120), world history
(1,678), and a broad school-subject tail recorded in the ledger.

Register coverage is not yet adequate: 1,199 of 1,205 external rows have no
`register_tag`; six are `scripted`. Region is absent from the inventoried
content-table schemas. These dimensions are **unmeasured/unknown**, not zero.

## Raw-to-ingested lineage

### Literary

- Google Drive: 229 `literary_texts/*.jsonl` files.
- Database: 229 distinct `literary_texts.source_file` groups.
- Filename-stem reconciliation: 229 clean matches, zero raw-only, zero
  database-only.
- Limitation: per-file JSONL line equality and content hashes were not measured;
  clean names do not prove byte identity.

### Textbooks and private references

- Google Drive: 158 public textbook chunk JSONLs across grades 1–11.
- Database: 168 textbook source groups.
- All 158 public raw chunk source IDs are ingested.
- Eight database source groups are private Ohoiko/ULP references. All eight
  have retained raw JSONL artifacts under `private_curriculum/`.
- Two database source groups have no matching retained raw chunk in the
  configured chunk trees:
  `antonenko-davydovych-yak-my-hovorymo` (169 rows) and
  `pohribnyi-ukrainska-literaturna-vymova-1992` (28 rows).
- Three exact-content duplicate candidates deserve later source-level review:
  two Zabolotnyi title/version pairs share 401 and 268 rows; one grade-eight
  pair shares one row. This inventory does not delete or deduplicate them.

The live textbook total is 54,979 rows: 49,193 public/external and 5,786
private-reference. The private rows are 1,000 Ohoiko word entries, 500 Ohoiko
verb entries, and 4,286 ULP rows across six seasons. Their raw presence does not
weaken the private-reference boundary.

### Deferred OCR

Five PDFs remain in `textbooks/_deferred_scans`. Each has a same-grade/subject
alternative already ingested. None satisfies all prerequisites of no usable
equivalent, measured high-priority gap, established provenance, sufficient
expected extraction quality, and separate operator approval. Current qualifying
OCR candidates: **zero**. The four files in `raw/orphan-ocr` have generic names
and unresolved provenance; they are not OCR authority or admission evidence.

## Git and archive recovery

Six deleted FOLK package versions are recoverable:

| Historical package | Commit | Current state |
| --- | --- | --- |
| `dumy-nevilnytski-lytsarski` | `cd46eb9e829ba5e3f40723c62db85fa4b6546e5f` | Current rebuilt module also exists |
| `kalendarna-obriadovist-zvychai` | `cd46eb9e829ba5e3f40723c62db85fa4b6546e5f` | Current rebuilt module also exists |
| `koliadky-shchedrivky` | `cd46eb9e829ba5e3f40723c62db85fa4b6546e5f` | Current rebuilt module also exists |
| `narodna-kultura-yak-systema` | `cd46eb9e829ba5e3f40723c62db85fa4b6546e5f` | Current rebuilt module also exists |
| `narodni-viruvannia-mifolohiia-demonolohiia` | `5f9d1697b83e234466f8c61a5ac014d5c6cc4c1e` | Historical package absent from current active track |
| `zamovliannia-zaklynannia-prymovky` | `5f9d1697b83e234466f8c61a5ac014d5c6cc4c1e` | Historical package absent from current active track |

Six archived plans have no Git `module.md` evidence:
`bohatyri-illiya-dobrynia`, `bylyny-sotsialni`, `dumy-lytsarski`,
`pokhodzhennia-dum`, `rusalni-pisni`, and `zastavy-bohatyrski`. They are
classified as planned but not evidenced as built. Git has zero stashes and no
branch, tag, or relevant reflog evidence that improves these states.

## Synthetic, translated, private, and evaluation boundaries

| Collection | Origin class | Measured size/state | Permitted inventory use |
| --- | --- | --- | --- |
| A1–B2 current curriculum | Machine-generated direct Ukrainian | 311 modules; 6,741,140 characters; 898,815 lexical words | Synthetic research; future CEFR calibration after a separate protocol |
| Current FOLK | Machine-generated direct Ukrainian | 40 modules; 1,401,549 characters; 199,059 words; 40 automated PASS sidecars | Preserve unwanted-bloat examples for human-annotated error/preference research; PASS is not human gold |
| Current BIO | Unknown origin | Five modules; 122,844 characters; 16,213 words | Resolve writer/model lineage and operator-reported unsatisfactory subset |
| Hramatka pedagogy v1 | Machine-generated direct Ukrainian; private reference | Two B1 research rows | Synthetic research only; README fine-tuning prose is not admission evidence |
| KubeDojo Ukrainian | Machine-translated Ukrainian | 554 files; 20,722,962 characters; 2,585,416 words | Translationese/calque/error analysis only |
| Project wiki | Unknown origin | 22,385 rows; 1,451,765 words | Internal RAG reference; per-article generation lineage unresolved |
| UA-GEC held-out/eval data | Evaluation-only | 677 held-out sentences; 52 evalset JSONL rows; 8,937 database error pairs | Evaluation only; excluded from all training/preference views |
| ZNO task bank | Evaluation-only | 33 documents and 1,646 tasks | Evaluation only |

FOLK promotion metadata records writer models as GPT-5 (31), GPT-5 Codex (8),
and GPT-5.6 Sol (1), with 28 Anthropic-family and 12 Google-family reviews. The
operator's quality judgment overrides the inference that an automated PASS
makes these authentic human-authored gold. No evidenced human-revised synthetic
collection was found; that origin class remains present with a zero count.

The KubeDojo divergence snapshot covers 514 files and marks 171 stale. Of 554
Ukrainian files, 534 carry an English-commit locator, 330 carry an English-file
locator, and 20 lack `en_commit`. These signals are partial lineage, not human
revision evidence.

## Present eligibility views

Eligibility is expressed as asset records, never as permission to extract
their bodies. The aggregate summary contains the exact asset-ID lists.

| View | Current quantity | Meaning |
| --- | ---: | --- |
| Internal RAG/reference | 17 assets | Existing internal lookup remains allowed under current project boundaries |
| Further provenance investigation | 30 assets | Evidence is incomplete enough to merit bounded reconstruction |
| Potential training admission | **0 assets** | No `source-record-v1` admission evidence exists yet |
| Redistribution investigation | 17 assets | Public/external collections worth rights review; **zero are cleared** |
| Evaluation only | 3 assets | UA-GEC database/held-out and ZNO assets |
| Synthetic research only | 8 assets | Generated curriculum, historical generated FOLK, Hramatka, and KubeDojo translation |

The negative 5,000-record export is not in an eligible view. It may locate an
underlying work, but it cannot establish source, edition, acquisition lineage,
rights, or contamination status.

## Smallest useful source set for #6082

The smallest honest pilot is **one coherent existing source family**, not a
fixed row quota. After one real open-weight consumer documents a bounded need,
Issue #6082 should:

1. choose one retained literary JSONL/source family whose original catalogue,
   edition, website, archive, or acquisition artifact can be independently
   re-established;
2. reconstruct one canonical source record with rights, permitted-use,
   content-hash, translation-origin, and contamination evidence;
3. select only the minimum work/chunk subset that meets the consumer's named
   phenomenon and coverage need; and
4. emit a deterministic admission receipt and consumer-specific export view.

The same underlying text may be re-admitted after this reconstruction. The
5,000-record export may help find it but never supplies provenance. New text
acquisition remains out of sequence unless the pilot demonstrates a measured
gap or the consumer confirms a requirement that no represented original can
meet.

## Preserved CEFR research action

Create a separate linked issue, after operator approval, for a privacy-safe CEFR
case-study protocol. Do not contact the collaborator in this phase. The protocol
must compare generated A1–B2 lessons, operator-identified unsatisfactory FOLK
and BIO outputs, and KubeDojo machine translations as separate categories. It
should compare claimed CEFR, local syntactic-depth and lexical-diversity
measurements, VESUM/PULS evidence, the collaborator's complexity system when
available, and Ukrainian-teacher judgment. This belongs to evaluation/internal
quality infrastructure, not the human-written training corpus.

## Reproduction and limitations

The committed collector supports a live census and a source-blind fixture mode.
The live invocation resolves the Drive root through project configuration; it
must never commit a personal mount path:

```bash
.venv/bin/python scripts/projects/open_model_data/inventory_existing_assets.py \
  --snapshot-date 2026-07-31 \
  --database data/sources.db \
  --vesum-database data/vesum.db \
  --drive-root "$LU_GDRIVE_DATA" \
  --kubedojo-root ../kubedojo
```

The ledger emits no corpus or lesson bodies. Exact content hashes, per-file raw
line equality, normalized rights, editions, regions, most registers, model
tokens, and source-record admissions remain incomplete. Those unknowns are
explicit fields or limitations rather than implied permission.

## Requested-agent ledger

| Task name | Canonical path | Role | Task family / track | Owned paths | Expected result | Final status |
| --- | --- | --- | --- | --- | --- | --- |
| `archive_git_forensics` | `/root/archive_git_forensics` | Recovery forensics | Open-model-data asset inventory / #6056 | Scoped archives and Git refs/history | Counts, candidates, locators, uncertainties | COMPLETED; read-only, no edits |
| `gdrive_ingestion_reconcile` | `/root/gdrive_ingestion_reconcile` | Source-lineage reconciliation | Open-model-data asset inventory / #6056 | Logical Drive corpus, read-only DB, ingestion code | Raw/DB mappings, gaps, OCR evidence | COMPLETED; read-only, no edits |
| `synthetic_asset_map` | `/root/synthetic_asset_map` | Synthetic provenance mapping | Open-model-data asset inventory / #6056 | Current curriculum, Hramatka dataset, KubeDojo Ukrainian | Origin/review/use map and provenance gaps | COMPLETED; read-only, no edits |
| Root orchestrator | `/root` | Integration and disposition | Open-model-data asset inventory / #6056 | Issue, worktree, implementation, validation, review, merge | Durable ledger/report and terminal closeout | Accountable through merge and cleanup |

## North-star accounting

| Completed workstream | Existing asset preserved/recovered/measured | Durable artifact after model replacement | Boundary separation | Evidenced gap rather than assumed acquisition | Authentic-Ukrainian quality contribution |
| --- | --- | --- | --- | --- | --- |
| Git/archive forensics | 12,347 tracked archive files, six historical packages, six unevidenced plans | Commit/path recovery locators and state taxonomy | Historical generated modules remain synthetic/unknown | Finds actual recoverability and loss uncertainty; acquires nothing | Preserves failed/older Ukrainian outputs for later error comparison without calling them gold |
| Drive/DB reconciliation | Literary JSONL, textbook chunks/PDFs, private raw refs, live corpus rows | Logical raw-to-ingested map and unmatched IDs | Public, private, unresolved, and evaluation data remain distinct | Identifies two raw-lineage gaps and zero qualifying OCR candidates | Enables source-based quality/provenance work on existing Ukrainian text |
| Synthetic/translation map | A1–B2, FOLK, BIO, Hramatka, KubeDojo Ukrainian | Origin/review/use metadata independent of any model generation | Direct generation, translation, unknown, private, and evaluation boundaries are mechanical | Preserves bad outputs as evidence; requests no replacement text | Supports CEFR, bloat, translationese, calque, correction, and preference research under human review |
| Deterministic collector and ledger | All inventoried collections and candidates | Schema, live CLI, CI fixture mode, byte-stable ledger/summary | Origin and data-boundary enums plus zero-admission assertion | Measures current holdings before any acquisition proposal | Gives researchers auditable corpus size, coverage, limitations, and reusable evidence locators |
| #6082 sequencing | Existing original sources represented in the corpus | One-source-family reconstruction procedure | Evaluation and private material excluded; 5,000 export is locator only | Consumer need and measured gap precede any new acquisition | Focuses the first pilot on traceable, rights-reviewed Ukrainian evidence |
| CEFR continuity | Existing generated and translated Ukrainian outputs | Privacy-safe future study protocol | Study remains evaluation/internal quality, outside human training corpus | Uses existing categories before collecting anything | Pairs automated complexity measures with Ukrainian-teacher judgment |
