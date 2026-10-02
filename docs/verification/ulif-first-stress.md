# ULIF-first stress oracle

`scripts.verification.stress` implements #8398 part B and #8400 rule 3.
Exact-form overrides precede both dictionaries. Pending override entries stay
unaccented. Otherwise the oracle reads `ulif_forms` through the read-only
Sources DB connection and accepts only rows joined to an entry with
`homonym_checked = 1`, from a complete current-parser build with a source
fingerprint. It neither creates tables nor migrates the database.

`scoped_overrides` in `scripts/data/stress_overrides.yaml` require a positive
VESUM lemma, POS and case match before replacing a dictionary reading. The
`хто` entries record СУМ-20, the orthoepic dictionary and Holoskevych citations:
dative `кому́`, locative `ко́му`, genitive/accusative `кого́`. Bare pronoun `кому`
keeps both case readings; other noun lemmas retain their dictionary readings.
Every scoped match carries its source citations and matched VESUM analyses.
An agreeing scoped/ULIF choice is returned once, labelled `ulif` because
dictionary evidence is needed for the other analysis. `supporting_readings`
retains both original source envelopes and their separate lemma/case witnesses;
the scoped override is never extended to the noun analysis.

Each ULIF row must also join a VESUM analysis of the form by its entry-key
lemma (without the homonym suffix), POS and compatible morphology. Pronouns
retain their pronoun POS; NOUN and PROPN are distinct. Capitalized input also
loads lowercase VESUM analyses and ULIF rows, so sentence-initial words do not
inherit a proper-name reading. Apostrophes `’`, `ʼ` and straight apostrophes
normalize identically for the dictionary join while output preserves spelling.
Unknown POS or absent VESUM evidence cannot admit a ULIF row. Thus the noun
`вон#1` never supplies stress for the personal pronouns `вона` or `вони`.

All agreeing joined stress choices collapse into one reading while retaining every
supporting form-row id, entry id, source fingerprint and grammatical tag set.
Different choices remain ambiguous. Optional `lemma`, `pos` and `tags` narrow
the source readings; `tags` accepts UD features or VESUM atoms. A source-stressed
lemma can distinguish lexical homographs. A bare lemma or POS cannot choose
between indistinguishable meanings. Context selects VESUM analyses first.
Unmatched supplied context returns pending; it never borrows another lemma.
Source capitalization is normalized onto the requested form before comparing
teaching choices; the same accent in different capitalization is agreement.

Repeated feature keys represent sets of allowed values, including VESUM's
interrogative/relative `PronType=Int` and `PronType=Rel` analyses. Shared feature
sets must intersect; missing features do not establish a conflict.

Dual readings retain `vowel_indices` and both `variants`. The legacy
`ulif_forms.pedagogical_stressed_form` field is the parser's last-accent heuristic,
not a dictionary choice, and is ignored by the oracle. `teaching_stress` reads
explicitly attributed Pohribnyi `orthoepy` entries from the dictionary mirror.
Only the first-listed, exactly matching, singly accented form on an allowed
vowel can supply `pedagogical_stressed_form`, with `pedagogical_source` row, URL
and text digest. Conflicting entries, lost OCR accents and different inflections
cannot supply a choice. The 1992 pronunciation booklet ingested into `textbooks`
is prose, not this dictionary's variant table.

A valid existing single mark on either allowed position is preserved. Without
an attested teaching choice, learner text retains both source accents and spoken
selection is pending. Compound forms retain their source marks.

ULIF settles a form only when joined readings cover every selected VESUM
analysis. Uncovered analyses use compatible readings from the packed
`ukrainian-word-stress` trie, labelled `source: trie`; trie readings incompatible
with those analyses are excluded. Distinct stress choices across both sources
remain ambiguous. If an analysis has neither source, proven readings remain `ambiguous`, with
`uncovered_vesum_analyses` recording the gap. Only an empty set of proven readings
is `pending`; caller context can still resolve a covered analysis.
With VESUM unavailable, only the labelled trie fallback is eligible.
An agreeing ULIF/trie choice is returned once with `source: trie`, since trie
evidence is needed to cover the missing analysis. Its `supporting_readings`
retain each authority's original evidence. An unlabelled packed trie reading
cannot inherit a covered lemma's teaching choice; annotation stays withheld.
Capitalized forms retain both proper and lowercase analyses unless caller
context selects a POS or lemma. Declared proper names require proper-name context.

## API and provenance

The single-word response retains its legacy `source` provenance object.
`stress_source` names the selected authority (`ulif`, `trie`, `override` or
`pending`, or `mixed` when multiple authorities supply the readings), and every
reading has a `source` label. Batch rows use `source` for
that label and share one provenance envelope per batch. Both MCP tools accept
optional contextual selectors.

`source_info()` contains the trie digest, the full `ulif_forms_build` receipt
and its canonical JSON digest, the teaching dictionary identity, the override
data digest, and a combined `digest`. Existing consumers of
`source["digest"]` therefore invalidate when dictionary evidence or override data changes. The trie
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
An attested pronunciation dictionary dual teaching choice can be stored as one learner accent;
unsupported packed choices stay pending.
Pending candidates retain the v1 reading fields and every distinct stress
choice with its tags. The source identities remain in `built_with`; extended
per-form evidence is available through the oracle. This keeps existing v1
consumers usable without a schema migration or a selected ambiguous reading.

A rebuild can change its content hash because a form gains checked ULIF
provenance, becomes unresolved for the requested lemma, receives a source-backed
teaching choice, or has a previously bypassed override applied. The ULIF build
digest also changes the build identity. Existing allocations remain append-only;
carried word records and previously promoted packs are not rewritten by this
change. Rebuilding and promoting a pack requires matching verifier identity and
fresh exact-head review. A changed dictionary or oracle must invalidate its
prior stress proof; it is not an unexplained rewrite of a promoted artifact.

The word-store verifier uses the same per-form oracle, lemma and VESUM tags
as the builder, within the Sources instance's pinned read-only snapshot. It
compares the trie digest with `built_with.trie` and the ULIF digest with
`built_with.ulif_forms`, and checks override identity and flags separately.
Changed source identities require fresh proof even when learner text agrees;
unchanged identities do not turn corrupted values into drift warnings. Raw
paradigm sections never bypass this oracle during verification.

Both audio callers provide the deck lemma and POS to the oracle and accept
one resolved reading. For packed dual stress, `spoken_stressed_form()` uses
the attested pronunciation dictionary teaching choice only if it marks one allowed position of
the same word. Missing or conflicting choices, homographs and pending
readings are excluded. Trie packed duals stay excluded without an override;
compound source marks and explicit overrides are preserved. Audio selection
tests certify the synthesis input, not the pronunciation of generated audio.

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

The comparator decodes the trie directly and joins checked ULIF rows to VESUM
identity without calling the stress oracle. Unjoined rows remain under
`unjoined_ulif`, with missing coverage listed in `uncovered_vesum`. This compares
eligible ULIF evidence with raw trie readings, excluding overrides and selection.
Every record also contains the actual oracle result and `status`.
`status_counts` partitions the denominator by what callers receive; `ambiguous`
and `dual` counts use the returned oracle readings. Raw source categories remain
diagnostic and never stand in for oracle status or language adjudication.
`sourced_dual_forms` counts dual forms with an attributed teaching choice. `agree`, `disagree`,
`ulif_only`, `trie_only` and `neither` partition the denominator. `ambiguous` and
`dual` overlap those categories. Reports preserve raw readings and VESUM analyses
without choosing a winner. If fewer than 60 disagreements exist, the sample
contains every disagreement and reports the smaller size.

Outputs stay in ignored `batch_state/stress-ulif-vs-trie/`: `comparison.jsonl`,
`disagreements.jsonl`, `sample-60.jsonl`, and `summary.json`. They require separate
language adjudication; counts and transport success do not establish linguistic
acceptance.

In a linked worktree, pass `--out` pointing to the durable ignored report
directory provided by the dispatch. Worktree-local ignored reports disappear
when the worktree is reaped. Keep the comparison and sample outside that tree.

Use `--forms-file <previous-comparison.jsonl>` to replay an unchanged denominator
when word-store inputs move. The receipt includes the replay file digest and
current corpus input hashes; newly added corpus forms are outside that replay.
Archive the previous report before regenerating it. A dry-run comparison of A1
store values uses the builder's lemma, tags and packed-accent policy; it reports
every old/new stress value without rebuilding or promoting the store.

The imperative deck retains bare VESUM-attested forms when stress is pending,
continues withholding ambiguous stresses, and compares normalized distractors
against every accepted answer. IPA generation uses this same oracle and spoken
selector; it never invokes a separate trie's first reading.

Stress unit tests isolate the ambient Sources store. Tests asserting ULIF
authority opt into `ulif_stress_db`, which builds a read-only temporary SQLite
snapshot from `tests/fixtures/stress-ci.json`; the capture retains source row
and entry identities, build fingerprint and VESUM analyses. Trie tests retain
an explicitly unavailable ULIF store and assert fallback labelling. Evidence
wrapper tests pin their existing synthetic Sources snapshots, while MCP
transport tests provide fixture bytes for the backend version hash.

The offline imperative coverage gate retains 3,138 cards across 1,050 lemmas.
Without the ULIF identity join, `перейняти:1pl` lacks its third distractor:
the future form `переймемо` has competing trie stress readings, so the
`WRONG_MOOD` option is withheld. The two other-person options are insufficient
for a four-option card, reducing B1 from 1,090 to 1,089 and the total to 3,137.
The test capture supplies the attested lemma-specific future reading and
preserves the original count and collision checks; it does not lower the gate.
