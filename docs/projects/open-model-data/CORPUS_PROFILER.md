# Ukrainian Data Foundry corpus profiler

The v1 profiler is the first executable layer of the Ukrainian Data Foundry.
It measures the complete configured public/external corpus and produces
unresolved lexical review candidates. It does not correct text, admit records
to training, create preference data, export a dataset, or claim to evaluate
sentence-level Ukrainian quality.

## Interfaces

The input is an explicit `corpus_profile_config_v1` document. Each source maps
an existing inventory asset to a read-only SQLite table, stable record and
locator columns, linguistic dimensions, evidence states, and an expected
row/word denominator. Paths are portable and resolve below `--input-root`; the
configuration never assumes a developer's absolute database path.

The profiler:

1. opens source databases with SQLite `mode=ro` and `query_only`;
2. streams records in bounded batches and tokenizes with the inventory's
   existing lexical-word expression;
3. normalizes stress and apostrophe variants, then calls the pinned
   `scripts.verification.vesum.verify_words` batch interface;
4. writes one unresolved candidate per unknown normalized form per source
   record, using only a non-published locator rather than surrounding text;
5. writes a content-free aggregate receipt with coverage, distributions,
   VESUM/lemma/POS/usage-marker counts, unknown-form frequency, output hashes,
   and explicit inaccessible sources.

Every candidate's data-dependent fields are checked before emission, and each
source/category shape is validated against `review_candidate_v1`. The aggregate
receipt is fully schema-validated in memory before it can replace an existing
receipt on disk.

Candidate categories are triage labels, not error verdicts. A VESUM-unknown
historical, dialectal, proper-name, or foreign-language form remains an
unresolved protected/contextual candidate with `automatic_error_label=false`.
The fixture contract proves that `звучит` is raised for review while
`звучить` is accepted by VESUM.

## Full-corpus run

Run from a task worktree while pointing `--input-root` at the local checkout
that owns the ignored databases:

```bash
.venv/bin/python scripts/projects/open_model_data/profile_corpus.py \
  --config data/projects/open_model_data/profiles/public_external_full_corpus_v1.json \
  --input-root /absolute/path/to/learn-ukrainian \
  --summary-output data/projects/open_model_data/profiles/full_corpus_profile_v1.json \
  --candidates-output batch_state/open_model_data/full-corpus-review-candidates-v1.jsonl
```

The checked-in configuration freezes the current denominator at 189,150 rows
and 50,298,925 lexical words across literary texts, public/external textbooks,
external articles/transcripts, and Wikipedia. The eight known private
textbook sources are explicitly excluded. A missing database/table/column or a
count mismatch makes `coverage.complete=false`; the CLI exits non-zero after
writing the exact accessible and inaccessible counts.

All four current source families remain `provenance_investigation`. Their
provenance is partial, rights have not been reconstructed, human authorship is
inventory-classified rather than source-record verified, and contamination
has not been cleared. The admission gate therefore excludes every processed
row and word even though diagnostic profiling is complete.

## Determinism and data boundary

Both outputs use canonical UTF-8 JSON with sorted keys and LF endings. Source
order, record order, normalized-form order, and VESUM primary-analysis choice
are explicit; timestamps and absolute paths are omitted. Repeated runs against
unchanged inputs are byte-identical.

Only the bounded aggregate receipt is committed. Candidate JSONL remains
ignored local runtime state. It contains surface tokens and locators but no
record body or context excerpt. The profiler does not read private textbook
rows, evaluation artifacts, generated Ukrainian, or project-internal wiki
content.

## Downstream layers

Issue #6121 consumes the candidate stream for contextual review and qualified
human adjudication. Issue #6122 consumes adjudicated records and complete
source evidence to build mechanically disjoint correction, preference,
quality-filter, training, and evaluation views plus reproducible recipes.
Issue #6123 validates those layers end to end against frozen references.

VESUM coverage alone cannot establish grammaticality or naturalness. Case,
agreement, government, syntax, collocation, semantic calques, and discourse
quality remain responsibilities of the later correction and adjudication
layers.
