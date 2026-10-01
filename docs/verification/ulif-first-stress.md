# ULIF-first stress oracle

`scripts.verification.stress` implements #8398 part B and #8400 rule 3.
Exact-form overrides precede both dictionaries. Pending override entries stay
unaccented. Otherwise the oracle reads `ulif_forms` through the read-only
Sources DB connection and accepts only rows joined to an entry with
`homonym_checked = 1`, from a complete current-parser build with a source
fingerprint. It neither creates tables nor migrates the database.

All agreeing stress choices collapse into one reading while retaining every
supporting form-row id, entry id, source fingerprint and grammatical tag set.
Different choices remain ambiguous. Optional `lemma`, `pos` and `tags` narrow
the source readings; `tags` accepts UD features or VESUM atoms. A source-stressed
lemma can distinguish lexical homographs. A bare lemma or POS cannot choose
between indistinguishable meanings. Unmatched supplied context returns pending;
it does not silently borrow another reading or switch dictionaries.

Dual readings retain `vowel_indices`, both `variants`, and the source's
`pedagogical_stressed_form`. A valid existing single mark on either allowed
position is preserved. Without an attested teaching choice, the annotator does
not invent one. Compound forms retain their source marks.

When the form has no trusted ULIF rows, the packed `ukrainian-word-stress` trie
is the labelled fallback. If neither dictionary has a reading, the result is
`pending`. Exact case is checked before spelling variants, since proper-name
and lowercase forms can have different readings.

## API and provenance

The single-word response retains its legacy `source` provenance object.
`stress_source` names the selected authority (`ulif`, `trie`, `override` or
`pending`), and every reading has a `source` label. Batch rows use `source` for
that label and share one provenance envelope per batch. Both MCP tools accept
optional contextual selectors.

`source_info()` contains the trie digest, the full `ulif_forms_build` receipt
and its canonical JSON digest, and a combined `digest`. Existing consumers of
`source["digest"]` therefore invalidate when either source changes. The trie
loader and digest cache are keyed by the file snapshot so a running MCP process
also observes a replacement. ULIF readings cite row and entry fingerprints;
the dictionaries are never modified by lookups.

The deterministic annotator uses Stanza only for lemma and morphology, then
queries this same oracle. It loads installed context models offline. Missing
context, ambiguous meaning and incompatible lexical evidence leave a form
bare. It strips accents for parsing and maps offsets back to the original text,
so repeating the pass is idempotent. A sole dictionary reading belonging to
another VESUM lemma is not transferred to a learner word without context.

## Evidence word stores and cache changes

New word-store builds use the oracle with the requested lemma and VESUM tags,
and record separate `built_with.trie` and `built_with.ulif_forms` digests. The
existing v1 override flag remains the representation for exact-form patches.
An attested ULIF dual teaching choice can be stored as one learner accent;
unsupported packed choices stay pending.

A rebuild can change its content hash because a form gains checked ULIF
provenance, becomes unresolved for the requested lemma, receives a source-backed
teaching choice, or has a previously bypassed override applied. The ULIF build
digest also changes the build identity. Existing allocations remain append-only;
carried word records and previously promoted packs are not rewritten by this
change. Rebuilding and promoting a pack requires matching verifier identity and
fresh exact-head review. A changed dictionary or oracle must invalidate its
prior stress proof; it is not an unexplained rewrite of a promoted artifact.

## Measurement

Run from the repository/worktree root with the project's prescribed interpreter:

```bash
.venv/bin/python -m scripts.verification.stress_comparison --seed 8398
```

`--help` documents root and output overrides. The corpus is the union of every
word-store form in `curriculum/l2-uk-en/evidence/*/_words.yaml` and every Ukrainian
token in public `site/src/content/docs/a1/**/*.mdx` and
`site/src/content/docs/a1-v1/**/*.mdx`. Case is preserved; accents are stripped.
The receipt records every input path and SHA-256, both dictionary identities,
the denominator, categories, sample seed and actual sample size.

The comparator decodes the trie directly and queries checked ULIF rows directly.
Comparing against the ULIF-first oracle would be circular. `agree`, `disagree`,
`ulif_only`, `trie_only` and `neither` partition the denominator. `ambiguous` and
`dual` overlap those categories. Reports preserve raw readings and VESUM analyses
without choosing a winner. If fewer than 60 disagreements exist, the sample
contains every disagreement and reports the smaller size.

Outputs stay in ignored `batch_state/stress-ulif-vs-trie/`: `comparison.jsonl`,
`disagreements.jsonl`, `sample-60.jsonl`, and `summary.json`. They require separate
language adjudication; counts and transport success do not establish linguistic
acceptance.
