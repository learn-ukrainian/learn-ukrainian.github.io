# Ukrainian calque + grammar evaluation

> **Canonical tracker:** [GitHub epic #2156](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/2156)
>
> **Verified status (2026-07-28):** the 52 train-derived rows remain development
> fixtures only. The public lane now has a 677-item held-out manifest, a
> source-only saved-response interface, exact edit P/R/F0.5 scoring, and
> reproducible baseline receipts. It is not a leaderboard.

## Mission

Build a reproducible public minimal-edit correction evaluation for Ukrainian
calques and grammar from UA-GEC. The final package must provide deterministic
gold extraction, standard edit scoring, version-pinned baselines, and a
stranger-runnable release without private product data or provider secrets.

The accepted project direction is:

- no dedicated Ukrainian calque harness is known;
- UA-GEC reuse is welcome;
- the evaluation set is the highest priority;
- a reproducible baseline harness is a close second.

The project does not create a broad Ukrainian leaderboard or composite
"Ukrainian quality" score.

## Verified capability truth

Repository inspection on 2026-07-28 established:

- `data/projects/ua_eval_harness/evalset_v1.jsonl` contains 52 rows:
  32 `F/Calque`, 12 `G/Case`, and 8 `G/Gender`;
- all 52 source items are from UA-GEC train partitions
  (`gec-fluency/train` or `gec-only/train`), not an upstream held-out split;
- `compile_evalset.py` reads a pre-curated local 52-item source and does not
  apply a frozen upstream eligibility, split, or exclusion predicate;
- heritage protection is a five-token hard-coded seed, not a versioned
  VESUM/heritage integration, and no current row exercises it;
- the former mock-only evaluator and custom substring metric were prototype
  behavior and have been replaced by the saved-response scorer described
  below.

The 52 rows may be used for parser/scorer development and regression only.
They are never included in held-out scores. The deterministic fixture-rule
baseline is the only v1 component that reads them, and its fixture-file hash is
recorded in the saved-run header.

The public held-out extraction manifest is separate:

- `heldout_manifest_config.json` pins UA-GEC commit
  `4757f72f192c4a41e4c8fb1d9690a948f87cf6d6`, CC BY 4.0 evidence,
  metadata, and the `gec-fluency/test` M2 file by SHA-256;
- `heldout_manifest_v1.json` accounts for all 2,690 upstream test sentences:
  677 included calque/grammar records and 2,013 exclusion receipts;
- all 166 test documents and 76 test authors are preserved, with zero author
  overlap against the upstream train split.

Historical receipts remain useful but bounded:

- [issue #5608](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5608)
  and [PR #5610](https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/5610)
  delivered the local compiler prototype;
- [PR #5633](https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/5633)
  delivered the mock-only evaluator prototype.

Their closed/merged states do not prove that a public benchmark or live
baseline harness exists.

## Frozen task direction

The target is minimal-edit Ukrainian sentence correction:

1. Model input contains the source sentence and versioned task instruction.
2. Gold targets and edit spans are never model inputs.
3. Model responses are saved before scoring.
4. A standard edit scorer reports precision, recall, and F0.5.
5. Exact corrected-sentence accuracy is a companion metric.
6. Results report per-tag support, uncertainty, unchanged output, and
   over-editing.

The public set is derived from the pinned UA-GEC `gec-fluency/test` split.
The frozen predicate includes every tokenized sentence with an `F/Calque` or
`G/*` edit and applies only those edits per annotator. Final size is an
observed result, not a quota. The manifest preserves upstream sentence
locators, writer/document splits, original tags, attribution,
source/reference hashes, and explicit inclusion/exclusion reasons.

`F/Calque` remains an unchanged **UA-GEC standardization label**, not a claim
that this benchmark independently adjudicated every source form as a calque.
The separate `scoring_dispositions_v1.json` records the benchmark decision for
all 354 annotator-level `F/Calque` edits (293 unique spans). Its hash-locked
dict_uk/VESUM v6.8.0 probe finds 49 unique spans with exact style-marker
collisions: 34 `bad`, 10 `slang`, 3 `arch`, and 2 `rare`. The release admits
338 annotations to headline calque recall and fails closed on 16:

- 3 are conversational/register standardizations;
- 2 are heritage conflicts;
- 11 remain contested.

Attestation or a style marker is evidence, not automatic contextual
adjudication. In particular, the shared surface `була` is not heritage-flagged:
the `arch` analysis belongs to adjective `булий`, while the sentence uses the
clean verb analysis `бути`. The committed receipts and tests cover that
morphological collision, the bounded `тьоті`, `кришею`, `рижого`, and
`Спікери` decisions, all 10 slang collisions, upstream-label preservation, and
fail-closed abstention. Full contextual marker activation remains tracked by
issue #5092; no five-token seed participates in public scoring.

Verify the committed artifact without an upstream checkout:

```bash
.venv/bin/python scripts/projects/ua_eval_harness/build_heldout_manifest.py \
  --verify-existing
```

Reproduce it from the exact pinned UA-GEC checkout:

```bash
.venv/bin/python scripts/projects/ua_eval_harness/build_heldout_manifest.py \
  --ua-gec-root /path/to/ua-gec \
  --check
```

## Saved-response runner and standard scoring

`evaluate_model.py` separates generation from scoring with two versioned JSONL
contracts:

- `ua_eval_generation_requests.v1` contains only item ID, source sentence,
  source hash, and prompt hash;
- `ua_eval_saved_responses.v1` retains raw response text plus prompt, model,
  provider, model version, decoding, runner, request, response, manifest, and
  source hashes.

Both contracts declare `gold_fields_supplied: []`. Validators reject missing
items, duplicate IDs, manifest drift, prompt drift, source drift, response
tampering, or any declared target/reference/edit input field.

Prepare the frozen source-only packet:

```bash
.venv/bin/python scripts/projects/ua_eval_harness/evaluate_model.py prepare \
  --output data/projects/ua_eval_harness/baselines/v1/generation_requests.jsonl
```

Generate and score the credential-free baselines:

```bash
.venv/bin/python scripts/projects/ua_eval_harness/evaluate_model.py baseline \
  --kind identity \
  --output data/projects/ua_eval_harness/baselines/v1/identity.responses.jsonl

.venv/bin/python scripts/projects/ua_eval_harness/evaluate_model.py baseline \
  --kind fixture-rules \
  --output data/projects/ua_eval_harness/baselines/v1/fixture-rules.responses.jsonl

.venv/bin/python scripts/projects/ua_eval_harness/evaluate_model.py score \
  --responses data/projects/ua_eval_harness/baselines/v1/identity.responses.jsonl \
  --output data/projects/ua_eval_harness/baselines/v1/identity.report.json
```

The optional real-model generator runs Codex CLI in an empty temporary
directory with a read-only sandbox and repository/user rules disabled. It
receives the source-only packet, never the manifest:

```bash
.venv/bin/python scripts/projects/ua_eval_harness/run_codex_baseline.py \
  --requests data/projects/ua_eval_harness/baselines/v1/generation_requests.jsonl \
  --model gpt-5.6-terra \
  --output /tmp/gpt-5.6-terra.raw.jsonl \
  --metadata-output /tmp/gpt-5.6-terra.metadata.json

.venv/bin/python scripts/projects/ua_eval_harness/evaluate_model.py import \
  --requests data/projects/ua_eval_harness/baselines/v1/generation_requests.jsonl \
  --model-output /tmp/gpt-5.6-terra.raw.jsonl \
  --metadata /tmp/gpt-5.6-terra.metadata.json \
  --output data/projects/ua_eval_harness/baselines/v1/gpt-5.6-terra.responses.jsonl
```

The primary metric is correction edit precision, recall, and F0.5 under exact
source-token-span plus replacement matching. This follows the
[official UNLP 2023 evaluation contract](https://github.com/asivokon/unlp-2023-shared-task/tree/fbff22905f8c9a3677c900d56599284151c029e6):
a true positive must exactly match the source span and correction of the
annotator selected for that sentence. V1 selects the best-F0.5 annotator per
sentence with a deterministic tie-break; every report states this reference
policy. Exact corrected-sentence accuracy is a companion metric. Reports also
contain unchanged-output and over-editing rates, stable corpus annotation
support, selected-reference support and Wilson recall intervals per tag, and
deterministic sentence-bootstrap intervals for F0.5 and exact accuracy.

The dependency-free v1 scorer uses a frozen Wagner-Fischer token aligner. It
implements the official metric semantics but does not claim byte-for-byte
ERRANT alignment parity for ambiguous alignments; the scorer ID, reference
commit, implementation note, and all input hashes are recorded in every
report.

The complete [v1 baseline receipts](../../../data/projects/ua_eval_harness/baselines/v1/README.md)
include identity, train-fixture literal rules, and a source-only
`gpt-5.6-terra` run. Across all retained UA-GEC standardization and grammar
labels, Terra scores 0.2439 edit F0.5 and 0.1610 exact-sentence accuracy. Its
heritage-safe headline calque recall is 0.1410 (33/234 selected-reference
annotations). The report retains all 677 raw responses and full run
provenance. Calque precision is intentionally `null`: untyped hypothesis-only
false positives cannot honestly be assigned to the calque tag.

## Immutable release freeze

Release `0.1.0` is pinned by one
[freeze manifest](../../../data/projects/ua_eval_harness/releases/v0.1.0/freeze_manifest.json).
It records the exact dataset, task, prompt, schema, scorer, runner, request,
saved-response, and report hashes together with split-integrity and generation
provenance. Verify every frozen byte and the aggregate-report privacy contract
offline:

```bash
.venv/bin/python scripts/projects/ua_eval_harness/verify_release_freeze.py
```

The Ukrainian-first
[contamination policy](contamination-policy.md) documents the complete leakage
disclosure, train-fixture separation, prohibited product/training reuse, and
semantic version-bump rules. Frozen bytes are never edited in place.

## Public v0

The stranger-runnable release is documented by the Ukrainian-first
[data card](DATA_CARD.uk.md), bilingual
[reproduction guide](REPRODUCING.md), and complete
[third-party notices](THIRD_PARTY_NOTICES.md). A clean checkout can reproduce
all frozen reports without provider credentials:

```bash
uv venv --python 3.12.8
.venv/bin/python scripts/projects/ua_eval_harness/smoke_public_v0.py
```

The smoke verifies the release freeze, validates each complete saved-response
run, re-scores all three baselines, and requires exact report-object equality.

## Ownership and data boundaries

Four lanes cooperate but retain separate ownership:

- **#2156 — public evaluation:** public UA-GEC-derived gold, standard scoring,
  baselines, freeze/versioning, documentation, and release.
- **#4913 — internal quality machinery:** QG schemas, finding envelopes,
  validators, internal gates, product adapters, and private calibration.
- **#4542 / #5254 — Hramatka:** teacher-facing product and private Hramatka
  regression calibration. Teachers are users, not annotators.
- **#4387 / #4700 — Atlas and Daily Practice:** provenance-aware
  lexical/heritage evidence and independently rights-cleared learner material.

These inventories remain separate:

- frozen public benchmark gold;
- private Hramatka regression cases;
- teacher feedback and lesson payloads;
- Atlas source sentences;
- Daily Practice exercise inventory;
- model responses and result metadata;
- any future training data.

Public gold must not enter Daily Practice or training. Product findings and
teacher feedback may inform private regressions but never automatically become
public gold. Atlas evidence may cause abstention or a contested-heritage
warning; it must not silently override UA-GEC gold.

Only thin infrastructure may be shared: stable schemas and upstream tags, span
normalization, scorer interfaces, validator/configuration versions,
VESUM/heritage evidence semantics, and provenance conventions.

## Ordered execution queue

1. [#5966 — reconcile capability truth and freeze the task/data contract](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5966)
2. [#5967 — build the deterministic held-out UA-GEC extraction manifest](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5967)
3. [#5636 — standard GEC scorer, saved-response adapter, and baselines](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5636)
4. [#4626 — freeze manifest, split integrity, and contamination policy](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4626)
5. [#4541 — stranger-runnable public v0, data card, and baseline report](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4541)

EleutherAI/lm-eval compatibility is optional after the saved-response runner
and standard scorer are proven. It is not a v0 prerequisite.

## Non-goals

- factuality, BIO, cultural-grounding, or seminar fact checking;
- synthetic corruption, DPO, fine-tuning, training, or training-data creation;
- Hramatka, Atlas, Daily Practice, curriculum, or dataset implementation in
  the governance cycle;
- Surzhyk, Polonism, or Anglicism expansion;
- a new leaderboard or arbitrary dataset-size target;
- teacher/community annotation, approval, or external-person dependency;
- treating heritage evidence as a boolean Russianism truth layer.

## Release gates

The epic remains open until:

1. the upstream eligibility predicate and held-out manifest are frozen;
2. every eligible record has attribution and an exclusion disposition;
3. a standard scorer accepts saved responses;
4. identity, deterministic, and one real version-pinned model baseline run;
5. per-tag support and uncertainty are reported;
6. the data card, license, limitations, and contamination policy exist;
7. clean-clone scoring is proven;
8. no private/product data has entered public gold; and
9. the package runs without Hramatka, teacher data, Atlas private state, or
   provider secrets.

## Related records

- [Ownership and data-boundary decision](../../decisions/2026-07-28-public-ua-eval-ownership-and-data-boundaries.md)
- [Internal QG epic #4913](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4913)
- [Hramatka epic #4542](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4542)
- [Atlas epic #4387](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4387)
- [Daily Practice epic #4700](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4700)
- [UA-GEC upstream repository](https://github.com/grammarly/ua-gec)
