# Ukrainian Data Foundry Model Views and Recipes

> **Owner:** [#6122](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6122)
> under [#6056](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6056)
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
`0.90`. Each text contributes at most 64 deterministic, evenly spaced
eight-character anchors (including both endpoints) to the character candidate
index. This keeps index growth bounded by record count rather than total
character count; exact hashes and three-token shingles provide the primary
exact and near-duplicate candidate paths. Raw evaluation text remains in memory
only. Receipts record logical artifact paths, artifact hashes, algorithm
version, thresholds, the anchor cap, and fingerprint counts—not evaluation
content or private filesystem paths.

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
