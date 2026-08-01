# Ukrainian Data Foundry: Language-Contact Detector

> **Status:** Production detector and full-corpus evidence receipt
> **Owner:** [#6167](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6167)
> under [Foundry Phase 2–4 #6164](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6164)
> **Recorded:** 2026-08-01
> **Does not authorize:** source admission, correction gold, model training,
> publication, dictionary redistribution, or automatic source rewriting

## Outcome

The detector streams the frozen 189,150-record / 50,298,925-lexical-word
inventory and emits exact-offset, bounded review candidates. It does not emit a
row for ordinary Ukrainian merely because the record was processed or a token
was present in VESUM. A protected row exists only after a positive suspicion is
rescued by exact local Ukrainian dictionary evidence.

The implementation separates:

- Russian quotation and dash dialogue from modern narration interference;
- Ukrainian-phonetic Russian from standard orthography;
- historical and register-sensitive uncertainty from modern candidates;
- exact Ukrainian heritage rescues from uncorroborated morphology hits;
- other-language, proper-name, and OCR/encoding routes;
- vetted valid-word calque, collocation, government, and sense-transfer routes.

Every emitted row retains `automatic_error_label: false` and
`review_state: unresolved`. The aggregate receipt explicitly records that no
gold, precision/recall claim, admission change, training, or publication was
performed.

## Bounded-span contract

The profiler tokenizer is reused with exact record-relative token offsets.
Structure is segmented before lexical judgment, including paired/nested and
paragraph-bounded imbalanced quotes, guillemets, dash dialogue, metalinguistic
markers, titles, epigraphs, citations/documents, sentences, and paragraphs.

Suspicious tokens are clustered only within a common discourse role and a
configurable token gap. The committed configuration caps every original span
at 240 Unicode characters and retains separate core and context offsets. A
full-record hash allows reconstruction against the private source database;
candidate JSONL never embeds an unbounded record.

## Evidence routing

The local prefilter runs before expensive evidence. VESUM misses route analysis
but do not create a verdict. Russian morphology is queried only for configured
Russian anchors, Russian-specific orthography, adjacent substantive unknown
forms, potential exact heritage hits, or bounded R2U-cache surfaces.
One morphology hit without corroboration emits no candidate.

One-character and hyphen fragments cannot become heritage rescues. Two- and
three-character forms remain eligible because Ukrainian heritage evidence is
linguistically meaningful at that length: local Грінченко/СУМ evidence protects
`шо`, `да`, and `мой` even though VESUM misses them and Russian morphology
recognizes them. An uncorroborated pair of Russian-morphology hits routes to
`uncertain`; it is not promoted to Russian interference merely by adjacency.
The protected route is itself unresolved evidence, not a claim that every
context is authentic. In particular, human calibration must distinguish the
attested dialectal/folkloric particle pattern `да й` from a modern affirmative
`да` used instead of `так`; exact headword attestation alone cannot resolve
that contextual question.

Evidence adapters are truthful and fail closed:

- VESUM uses `scripts.verification.vesum.verify_words` and the pinned
  `dict-uk-v6.8.0-e33803783ac1` snapshot.
- Russian shadow evidence uses
  `scripts.verification.check_ru_morph.get_ru_confidence`.
- Heritage evidence reuses the exact-headword semantics of
  `RelationHeritageLookup`. It builds one bounded read-only index over local
  Грінченко, ЕСУМ, and СУМ-11 tables, then records the exact dictionary identity
  that matched.
- The R2U file contains only 13 bounded regression queries with
  headword-match states, result counts, and response hashes produced by
  `r2u_translate`; it contains no definitions or corpus passages. Full passes
  perform no network calls. A candidate-level R2U `miss` therefore means only
  that the surface has no approved match in this tiny frozen cache. It is not
  a negative lookup against the R2U dictionary and must not be presented as
  such.
- ULIF and `slovnyk.me` remain `not_queried` or `lookup_pending`. A
  `slovnyk.me` pending row does not invent an underlying dictionary identity.

Phonetic reconstruction uses only committed research-regression mappings. It
runs inside an already suspicious bounded cluster, retains the original token
and configured transformation path, and requires both Russian morphology and a
real R2U-cache headword match. The detector never applies global substitutions.

## Full-corpus receipt

The deterministic aggregate is
`data/projects/open_model_data/detector/language_contact_receipt_v1.json`.
Candidate JSONL remains ignored local state under `batch_state/6167/`.

Pass 1 covered all configured sources with zero dropped records and zero
dropped lexical words:

| Measurement | Value |
| --- | ---: |
| Processed records | 189,150 |
| Processed lexical words | 50,298,925 |
| Total bounded candidates | 739,564 |
| Unresolved review queue | 304,951 |
| Protected rescues | 297,791 |
| Quoted Russian | 21,885 |
| Modern-interference candidates | 37,875 |
| Other retained-language routes | 77,062 |
| Candidate bytes | 2,172,971,624 |
| Candidate SHA-256 | `5aaf0c4f511a51a0db41098ab11eab94946fc35be9098bcdbdfbeb1b38131f48` |
| Receipt SHA-256 | `5cf5c8b16f04ded15deb84f387b53735e62b4af1fa17a47132358c39177b50c0` |

The high historical yield is explicit rather than collapsed into a modern
error label: 195,722 rows are `historical_unresolved`; the run retained
177,070 `middle_ukrainian` and 121,168 `old_east_slavic` candidates as real
period dimensions. The broad corpus label `modern` also includes older
modern-literary authors and must not be treated as a claim of contemporary
standard usage. Phase 3 must retain source, author, period, genre, and register
context when those fields are available.

All receipt partitions reconcile exactly: category, queue route, source
family, period, and register each sum to 739,564 candidates. The prefilter
accounts for all 189,150 records, including 37 zero-token records in the
no-signal bucket. This arithmetic is a fail-closed invariant, not a quality
estimate. No precision or correctness claim follows from these counts; they
are review-routing measurements.

Runtime observations are deliberately outside the deterministic receipt.
Pass 1 took 2,039.92 seconds and reached 615,596,032 bytes maximum resident
set according to macOS `/usr/bin/time -l`. An independent repeat produced
byte-identical candidate and receipt artifacts.

## Phase 3 evidence boundary

The full candidate stream is a deterministic sampling frame, not review gold.
Phase 3 selects a frozen, source-aware calibration sample without loading this
2.17 GB JSONL into memory. Only selected rows may receive bounded R2U and ULIF
lookups or an identified underlying dictionary result from `slovnyk.me`.
Receipts may retain response hashes and headword-match states; bulk crawling
and raw dictionary redistribution remain prohibited.

The blind first pass must hide detector categories, confidence, queue routes,
and other model/rule votes while showing the bounded original context and the
period/source metadata needed to protect historical, dialectal, regional,
quoted, and multilingual language. Two independent qualified Ukrainian humans
review separate salted orders; disagreements require a distinct third human.
The sample capacity and statistical stopping rule are frozen by an approved
review plan, never invented by this detector.

## Reproduction

Run focused tests and the frozen short fixture:

```bash
.venv/bin/pytest tests/test_open_model_language_contact_detector.py
.venv/bin/python \
  scripts/projects/open_model_data/language_contact_detector.py \
  --regression-test \
  --input-root .
```

Run a complete pass with local, uncommitted candidates:

```bash
/usr/bin/time -l .venv/bin/python \
  scripts/projects/open_model_data/language_contact_detector.py \
  --config \
  data/projects/open_model_data/detector/language_contact_config_v1.json \
  --input-root . \
  --summary-output batch_state/6167/receipt-pass-1.json \
  --candidates-output batch_state/6167/candidates-pass-1.jsonl
```

Repeat with `pass-2` paths, then require both comparisons to be silent:

```bash
cmp batch_state/6167/candidates-pass-1.jsonl \
  batch_state/6167/candidates-pass-2.jsonl
cmp batch_state/6167/receipt-pass-1.json \
  batch_state/6167/receipt-pass-2.json
```

Validate the maximum-span invariant without retaining source records in memory:

```bash
jq -r '.span.original_text | length' \
  batch_state/6167/candidates-pass-1.jsonl | sort -nr | head -1
```

The expected maximum is `240`.
