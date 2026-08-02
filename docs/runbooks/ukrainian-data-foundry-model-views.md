# Ukrainian Data Foundry Model Views and Recipes

> **Owner:** [#6169](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6169)
> under [#6164](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6164),
> extending the completed #6122 contract boundary
> **Boundary:** local view construction and reproducible manifests, not training
> or publication

> **Phase 2–4 status:** admitted-source continued pretraining is independent of
> qualified correction review and may proceed as soon as its source/payload,
> rights, privacy, origin, destination, and contamination gates pass. The
> implemented correction-family path below accepts qualified-human records.
> [#6168](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6168)
> now provides the distinct, explicitly non-human silver record and receipt;
> [#6169](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6169)
> owns the separate destination-specific exporter for those records. Until that
> exporter passes, silver records remain investigation-only and cannot enter an
> existing human-gold or continued-pretraining view.

## What this component does

The model-view exporter turns already governed Foundry inputs into five
mechanically separate local artifacts:

| View | Schema | Only permitted destination |
| --- | --- | --- |
| Continued pretraining | `continued_pretraining_view_v1.schema.json` | `continued_pretraining` |
| Correction/instruction | `correction_instruction_view_v1.schema.json` | `supervised_correction` |
| Preference | `preference_view_v1.schema.json` | `pairwise_preference` |
| Quality filter | `quality_filter_view_v1.schema.json` | `quality_filter` |
| Held-out evaluation | `heldout_evaluation_view_v1.schema.json` | `heldout_evaluation` |

Each command validates and writes only one schema. There is no mixed export to
filter or rename later. Every non-evaluation row carries its source-record
lineage, destination, origin class, and eligibility decision. The evaluation
schema denies every training destination.

Before a non-evaluation row is written, the exporter applies destination-aware
deduplication. Continued-pretraining compares source text. Correction-family
views first group rows by an exact semantic signature—the corrected/rejected
span, accepted form, alternatives, offsets, or label as applicable—and only
then compare their plain-text contexts for exact or near duplication. Shared
context alone therefore cannot erase two distinct corrections. Exclusions are
counted and never cross separate origin artifacts.

The CLI writes local artifacts. It does not upload, publish, redistribute, call
a model, or run training.

## Phase 3 real production result

The first real production instantiation uses the operator-accepted Ukrainian
Wikipedia continued-pretraining family. It is the frozen v1 implementation,
not the current program limit. The later #6248 usability decision approves the
retained literary, textbook, historical, and external-article corpus for local
model learning after required preprocessing. #6171 must still separate that
local capability from raw redistribution and publication, restore retained
locators, and export the larger faithful and modern-learning views.

`model_ready_view_production.py prepare-payloads` joins all 1,029 admitted
source records to their exact `sources.db` content hashes and the complete
issue #6167 detector and issue #6168 silver outputs. It produces a local payload artifact
with a gap-free character partition for every article. The committed receipt
contains no text. The measured partition contains:

- 21,306 detector/silver spans across 982 articles;
- 21,665,057 retained characters;
- 564,381 characters masked from modern-Ukrainian loss; and
- zero excluded source records or human-gold claims at payload preparation.

Both continued-pretraining exporters process the complete admitted scope. One
long near-duplicate is excluded from each arm, leaving 1,028 real,
model-training-eligible records. The faithful artifact preserves all accepted
source text with no character masks. The modern artifact preserves the same
source bytes and projects the operational detector/silver spans to zero-loss
character masks. Neither arm contains a frozen evaluation match.

The diagnostic tokenizer is the official `google/gemma-4-31B` tokenizer at
revision `5bbc2fb1c1b2c611d06e3d9f23c170ba21659d89`; its `tokenizer.json`
SHA-256 is
`12bac982b793c44b03d52a250a9f0d0b666813da566b910c24a6da0695fd11e6`.
It is a diagnostic consumer pin, not a training authorization. On the 1,028
records it produces:

- 7,696,734 non-special model tokens;
- 2,778,111 Ukrainian lexical-word occurrences;
- mean lexical fertility of 2.145 pieces per lexical word (p50 2, p90 4,
  p99 5);
- 299 byte-fallback tokens, or 0.0039% of non-special tokens;
- 2,448,405 VESUM-attested lexical words, or 88.13%; and
- 183,640 modern-view tokens projected to zero loss, or 2.386% of
  non-special tokens, with zero projection failures.

VESUM attestation and the recorded paradigm-fragmentation values are lexical
and inflectional proxies. They are not morpheme segmentation and do not prove
that the model generates correct Ukrainian.

The correction, preference, and quality-filter silver views are explicitly
blocked and empty in this production receipt because #6168 yielded zero
destination-eligible correction-grade records. The 739,503 silver records stay
available as protected or unresolved evidence; none is relabeled as human gold.
This is an evidence-grade result, not a reviewer-staffing dependency.

The production receipt keeps two scopes explicit. `evidence_grade` reports the
linked full-corpus silver inventory (116,647 protected and 622,856 unresolved
records). `protected_unresolved` reports candidate-bearing records in the
admitted Wikipedia payload scope (423 protected and 978 unresolved); these
payload categories overlap because one article can contain both kinds of span.
They are not interchangeable counts.

The historical phase-3 feasibility verdict is `REVISE`: real control and
loss-masked continued-pretraining inputs, evaluation isolation, protected/no-
change inventory, recipes, and tokenizer diagnostics exist, but an exact
treatment preregistration and operator compute ceiling do not. #6170 is now
parked optional validation and may reopen only after those two present-tense
gates are frozen. The current recipe manifests retain
`training_authorized: false` and `execution_state: not_run`. Projected training
runtime and cost remain null—not zero—until an exact local or rented runner
pins the hardware, treatment, and ceiling; local artifact storage is measured
exactly.

## Required inputs

### Continued-pretraining source payloads

`foundry_source_payload_v1.schema.json` is a local, uncommitted content
envelope. It binds a prepared text segment to an admitted
`source_record_v1` parent through:

- source record ID and parent content SHA-256;
- explicit full-source or character-span derivation and receipt;
- segment text and segment SHA-256;
- explicit human, generated, translated, or human-revised-synthetic origin
  with a verification method and receipt;
- private-data disposition with a completed screening method and receipt;
- normalization version and receipt;
- complete language-span review and receipt; and
- a gap-free, full-text partition of classified character spans with
  modern-loss actions.

Normalization applies to the full source before segmentation. A payload can
then be a deterministic character span of that normalized source; its declared
span width must exactly equal the emitted segment length. The parent hash,
normalized-source character bounds, and derivation, normalization, and span
receipts preserve that chain without requiring the source record to duplicate
copyrighted content. Full-source payloads explicitly use null source bounds.

A modern-literary-Ukrainian view keeps the original text bytes and emits
tokenizer-independent `start_char`/`end_char` mask ranges. Russian quotation,
mixed-language material, Ukrainian-phonetic Russian, historical orthography,
dialectal or regional material, marked register, and uncertain spans cannot be
silently retained in modern-Ukrainian loss. An `exclude_record` decision omits
the whole payload and increments an explicit receipt count. The faithful view
retains the original text and emits no loss masks.

Each artifact is homogeneous by origin. Machine-generated, translated,
human-revised-synthetic, and human-authored material must be exported in
separate invocations.

### Qualified-gold correction, preference, and quality-filter inputs

These commands consume the canonical `correction_record_v1` handoff plus the
exact admitted `source_record_v1` join. The #6121 field
`model_training_or_export_eligible` intentionally remains `false`; #6122 never
expects or mutates it. Instead, the correction and preference exporters
recompute the canonical handoff and require:

- `qualified_correction_intake: true`;
- `handoff: correction_intake_ready`;
- `owner_issue: 6122`;
- no safety blockers;
- a resolved correction with an accepted form;
- an admitted source record with all required rights granted; and
- clear private-data, origin, and contamination states.

The correction view reconstructs the corrected context from the preserved
span offsets. The preference view keeps the context as the prompt and the
accepted/original span as the chosen/rejected pair. Every emitted text field,
including alternatives and reconstructed targets, is checked again for
evaluation contamination.

The quality-filter view accepts only resolved `correction` or
`acceptable_as_is` decisions after the same independent safety checks.
Protected, quoted, multilingual, unresolved, contaminated, or rights-unclear
records do not become quality labels.

Correction-family exporters preserve canonical upstream packet order and
require unique correction-record IDs. They do not sort or require lexical
ordering of the hash-derived correction IDs. Continued-pretraining payloads,
by contrast, require caller-assigned payload IDs in strictly ascending order.
The receipt records the ordering rule actually applied.

## Evaluation exclusion registry

Every non-evaluation invocation rebuilds an in-memory exclusion registry from:

- the frozen v0.1.1 held-out manifest;
- the frozen v0.2 review inventory;
- `evalset_v1.jsonl`;
- v0.1.1 item-level evidence;
- scoring dispositions;
- the evaluation taxonomy; and
- the frozen minimal-edit prompt.

Additional evaluation-only or derived-rule artifacts may be supplied with a
repeatable `--extra-evaluation-artifact` argument. Missing or unreadable
artifacts fail closed.

The frozen algorithm combines normalized exact hashes, 32-character
containment, character-sequence comparison, and three-token shingle Jaccard at
`0.90`. Character-sequence matching is exact with `autojunk=False` through
4,096 characters. Longer texts use a deterministic multiset overlap ladder:
2-grams at `0.80`, 3-grams at `0.70`, 4-grams at `0.60`, and 5-grams at `0.50`.
Those bounds preserve a 10% distributed-edit candidate without invoking
`difflib`'s unbounded long-text path, which was measured taking more than ten
minutes on a single pair of ordinary 48–50k-character Ukrainian articles.
Tests cover the boundary, repetitive distributed edits, realistic long-text
insertions and deletions, clustered edits, frequency-matched non-duplicates,
containment, and exhaustive short binary strings. The long-text ladder is an
operational detector around the declared edit boundary, not a formal claim of
equivalence to every adversarial `difflib` alignment.

Each text contributes at most 64 deterministic, evenly spaced eight-character
anchors (including both endpoints) to the character candidate index. This
keeps index growth bounded by record count rather than total character count;
exact hashes and three-token shingles provide the primary exact and near-
duplicate candidate paths. Raw evaluation text remains in memory only.
Receipts record logical artifact paths, artifact hashes, algorithm version,
thresholds, the anchor cap, and fingerprint counts—not evaluation content or
private filesystem paths.

The same matching primitives power a separate intra-view deduplication gate.
The export receipt distinguishes that gate from evaluation contamination and
records whether it ran, its frozen algorithm and thresholds, and the number of
accepted fingerprints. It also records the recomputed source-contract totals:
admitted, denied, and total source records. Evaluation-only exports mark both
source admission and intra-view deduplication as not applicable.

The view and receipt are prepared in temporary files. Existing outputs are
moved atomically over still-reserved same-directory backup files, so another
process cannot claim a released backup pathname. If either final rename fails,
the exporter restores both previous files (or removes both new files) and
deletes rollback temporaries before propagating the failure. A successful
return therefore cannot leave a newly written view paired with a stale receipt.

## Build one view

Run from the worktree root. Inputs and outputs shown below are local paths and
must not be committed merely because the command succeeds.

```bash
.venv/bin/python -m scripts.projects.open_model_data.model_view_exporter \
  continued-pretraining \
  --source-records /local/source-records.jsonl \
  --payloads /local/source-payloads.jsonl \
  --origin human_authored \
  --representation-view modern_literary_ukrainian \
  --output /local/modern-pretraining.jsonl \
  --receipt-output /local/modern-pretraining.receipt.json
```

```bash
.venv/bin/python -m scripts.projects.open_model_data.model_view_exporter \
  correction \
  --source-records /local/source-records.jsonl \
  --correction-records /local/correction-records.jsonl \
  --origin human_authored \
  --output /local/correction-view.jsonl \
  --receipt-output /local/correction-view.receipt.json
```

Replace `correction` with `preference` or `quality-filter` to build those
separate schemas. The same input cannot create a mixed artifact.

The held-out view has its own command and schema:

```bash
.venv/bin/python -m scripts.projects.open_model_data.model_view_exporter \
  evaluation \
  --release all \
  --output /local/heldout-evaluation.jsonl \
  --receipt-output /local/heldout-evaluation.receipt.json
```

This copies frozen evaluation inputs into a local evaluation-only interface. It
does not make the v0.2 review inventory a public release.

## Build a reproducible recipe manifest

`training_recipe_config_v1.schema.json` requires immutable base-model,
tokenizer, code, dependency, framework, seed, precision, and hyperparameter
pins. Its objective must match the view. A moving revision such as `main` is
invalid. Learning rate and epochs must be greater than zero; weight decay must
not be negative.

The config also embeds the exact record-rendering template and its SHA-256,
the destination-specific loss policy, and the data split rule. Training views
use a named SHA-256 record-ID modulo partition with a fixed modulus and number
of validation buckets. Evaluation recipes instead preserve the frozen release
and cannot declare training partitions or loss.

```bash
.venv/bin/python -m scripts.projects.open_model_data.model_view_exporter \
  recipe \
  --config /local/recipe-config.json \
  --view-artifact /local/modern-pretraining.jsonl \
  --view-receipt /local/modern-pretraining.receipt.json \
  --output /local/modern-pretraining.recipe.json
```

The manifest revalidates every view row, verifies the receipt's record count,
byte count, and SHA-256, and binds both exact artifact digests. It freezes
destination-specific preparation and deterministic shuffle rules. Character
mask projection applies only to continued pretraining; other views record it
as not applicable. Held-out evaluation preserves its artifact order and is
never shuffled. Every manifest records:

```json
{
  "execution_state": "not_run",
  "model_call_performed": false,
  "training_authorized": false,
  "training_performed": false
}
```

Recipes do not authorize a training run. A future run needs a named research
question, a decision the run can change, and separate present-tense operator
authorization.

## Fixture boundary

Synthetic fixtures are rejected unless `--allow-test-fixtures` is explicit.
Fixture mode exercises schema, join, reconstruction, contamination, receipt,
and recipe behavior while forcing every non-evaluation row to
`model_training_eligible: false`. Fixture and genuinely eligible records cannot
share a recipe-bound view.

No qualified human correction has been admitted by this implementation. The
operator has separately admitted 1,029 Ukrainian Wikipedia source records for
one declared continued-pretraining destination; that admission does not create
correction labels or grant any other destination. The exporter makes missing
evidence executable and auditable rather than converting unresolved inventory
or silver evidence into human gold.

## Verification

```bash
.venv/bin/python -m pytest -q \
  tests/test_open_model_view_exporter.py \
  tests/test_open_model_correction_factory.py \
  tests/test_open_model_source_record_contract.py

.venv/bin/ruff check \
  scripts/projects/open_model_data/model_view_exporter.py \
  scripts/projects/open_model_data/correction_factory.py \
  tests/test_open_model_view_exporter.py
```
