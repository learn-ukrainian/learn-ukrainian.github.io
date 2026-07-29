# Release freeze and contamination policy

This policy applies to release `ua-gec-calque-grammar-public-v0`, semantic
version `0.1.0`. It does not authorize reuse of the evaluation set in products,
training corpora, or unrelated research tasks.

## Frozen release contents

The machine-readable release record is
`data/projects/ua_eval_harness/releases/v0.1.0/freeze_manifest.json`. It records
SHA-256 hashes for:

- the dataset configuration and manifest;
- the separate calque scoring-disposition manifest and its configuration;
- the task instruction, output schema, extractor, scorer, and optional
  provider runner;
- the VESUM source lock, marker parser, and scoring-disposition builder;
- the source-only request packet, saved responses, and aggregate reports for
  all three baselines;
- 52 training-derived examples that may be used only as development fixtures
  and do not contribute to held-out results.

Verification requires neither network access nor provider credentials:

```bash
.venv/bin/python scripts/projects/ua_eval_harness/verify_release_freeze.py
```

The verifier fails if it finds a mismatch in artifact bytes, run metadata,
prompt or scorer receipts, response coverage, or aggregate-report policy.

## Split integrity

The source is UA-GEC 2.0 at commit
`4757f72f192c4a41e4c8fb1d9690a948f87cf6d6`. The freeze records hashes for
`LICENSE`, `README.md`, `data/metadata.csv`, and
`data/gec-fluency/test/gec-fluency.test.m2`.

The extractor verifies that:

1. every document ID in the metadata is unique and belongs to exactly one
   partition;
2. the document set in the test M2 file exactly matches the metadata's test
   partition;
3. the training and test partitions have no authors in common;
4. all 2,690 test sentences have a disposition: 677 included and 2,013
   excluded.

The training and test partitions therefore have zero author overlap and zero
document overlap. The 52 development fixtures come from the training
partition and remain separate from the held-out evaluation.

## Upstream labels and benchmark dispositions

The release preserves `F/Calque` unchanged as an upstream UA-GEC
standardization label. The label alone does not assert that every original
form is a calque under this benchmark. A separate
`scoring_dispositions_v1.json` records the decision and reason for all 354
annotator-level edits.

The reproducible surface-form probe uses the pinned dict_uk/VESUM v6.8.0
release, which was the latest stable upstream release available when public v0
was frozen. Across 293 unique `F/Calque` spans, the probe finds 49 collisions
with style markers: 34 `bad`, 10 `slang`, 3 `arch`, and 2 `rare`. The source
does not provide a dedicated `dial` token. Its published `arch` semantics
cover obsolete and archaic usage and may also cover dialectal usage. The
benchmark therefore does not claim that there are zero dialect conflicts.

Headline calque recall includes 338 annotations. The remaining 16 are outside
the headline metric: 3 register-standardization cases, 2 heritage conflicts,
and 11 contested cases. Attestation or a style marker is evidence, not a
complete contextual decision. The release records separate regression
receipts for `тьоті`, `кришею`, `рижого`, `Спікери`, and the false
surface-form collision `була`. Issue #5092 tracks the complete marker-aware
contextual policy. The five-word prototype seed is not used.

## Known contact with evaluation data

- The public task instruction contains no examples.
- The deterministic literal-rule baseline derives rules only from the 52
  training-derived development fixtures. It is an intentionally weak
  diagnostic baseline, not training on the held-out set.
- Two source-only items were used for a transport check before the complete
  run. That check led only to a clarification that spaces and punctuation must
  be preserved. Gold responses, edits, and scores were not inspected.
- The real model was selected through the pre-existing operator routing policy,
  not in response to benchmark results.
- Generation requests contained only the item ID, source sentence, source
  hash, and prompt hash. They did not contain gold targets, references, edits,
  or scores.

## Prohibited reuse

Public source sentences, gold corrections, IDs, hashes, and derived rules from
this held-out set must not be added to:

- Daily Practice or any other learner-exercise inventory;
- training, fine-tuning, synthetic-data, preference-data, or DPO datasets;
- Hramatka, teacher-feedback data, or private regression and canary sets;
- Atlas or any other private product state.

A match discovered after the release freeze is a contamination incident. The
affected release must not be silently repaired. Resolution requires a recorded
incident, a new release version, a fresh extraction, new baselines, and a new
freeze manifest.

## Safe reporting

Public score reports contain only aggregates, support counts, uncertainty
estimates, and provenance. They must not contain item IDs, source or target
text, edit spans, raw responses, or content hashes. Saved model responses are
separate public artifacts that permit reproduction of the scores; aggregate
reports do not duplicate them.

## Versioning

Frozen bytes are never edited in place.

- `PATCH`: documentation or packaging corrections that do not change the
  dataset, task, scorer, or results.
- `MINOR`: backward-compatible additions to the task contract, scorer, runner,
  or baselines.
- `MAJOR`: changes to the dataset, eligibility rule, gold data, split, primary
  metric, or any incompatible contract change.

Each new release version receives its own freeze directory. Older freeze
manifests remain available and independently verifiable.
