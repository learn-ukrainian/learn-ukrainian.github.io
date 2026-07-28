# Ukrainian calque + grammar evaluation

> **Canonical tracker:** [GitHub epic #2156](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/2156)
>
> **Verified status (2026-07-28):** the committed 52 rows and mock evaluator are
> development fixtures. They are not a held-out public benchmark, standard GEC
> scorer, real-model baseline, or leaderboard.

## Mission

Build a reproducible public minimal-edit correction evaluation for Ukrainian
calques and grammar from UA-GEC. The final package must provide deterministic
gold extraction, standard edit scoring, version-pinned baselines, and a
stranger-runnable release without private product data or provider secrets.

Oleksiy's direction for the project is:

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
- `evaluate_model.py` implements only `mock`; every real model name raises
  `NotImplementedError`;
- current metrics use normalized exact sentence matching and custom
  source/target substring checks, not standard edit alignment or F0.5.

The mock path receives oracle data and is test-only. Its score must never be
reported as a model baseline. The 52 rows may be used for parser/scorer
development and regression only.

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
