# Ukrainian Data Foundry Reference Build

> **Owner:** [#6123](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6123)
> under [#6056](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6056)
> **Boundary:** interface validation and frozen measurement, not training,
> publication, redistribution, upload, outreach, private-data use, or OCR

## What the reference build proves

The reference build is the executable integration proof for the first Foundry
chain. One command joins the already versioned interfaces for:

1. source admission and content lineage;
2. normalization and gap-free language-span review;
3. unresolved VESUM review-candidate routing;
4. Russian-interference evidence and correction intake;
5. qualified-review mechanics through explicitly synthetic reviewers;
6. five separate consumer views and five non-authorizing recipes;
7. complete-corpus morphology profiling; and
8. source-only frozen benchmark requests and saved-response scoring.

The committed manifest is
`data/projects/open_model_data/reference/reference_build_manifest_v1.json`.
It contains hashes, counts, schema versions, lineage IDs, the research
question, decision rule, measurements, limitations, and negative safety
assertions. The separate runtime observation records the fresh run's wall time,
maximum resident memory, manifest hash, and temporary-candidate deletion state.

Local view artifacts remain uncommitted. The manifest is useful after a model
release because it validates data interfaces and frozen measurements, not one
model's weights.

## Russian-interference integration fixture

The source fixture preserves the observed sentence:

```text
Фраза «Я не мав на меті тебе образити» звучит значно вишуканіше.
```

The reference chain does not declare every VESUM-unknown form an error. It
models this particular occurrence as a bounded candidate because the source is
modern machine-generated Ukrainian narration and the evidence packet records:

- VESUM: `звучит` not found;
- Russian morphology: form attested;
- `r2u`: Russian lexical evidence attested;
- ULIF `dictua`, a heritage source, and the `sum20` dictionary exposed through
  `slovnyk.me`: source-specific Ukrainian escalation results;
- Ukrainian corpus evidence: context only; and
- two agreeing synthetic review projections accepting `звучить`.

The synthetic reviewers exercise the contract only. They are never qualified
human evidence or training gold. The resulting correction record therefore
retains `test_fixture_reviewer` as its blocker, and every non-evaluation output
has `model_training_eligible: false`.

The modern continued-pretraining view keeps the original source bytes but masks
the six-character `звучит` span from loss. The correction, preference, and
quality-filter views use separate schemas and destinations. Russian quotation,
dialogue, historical material, dialect, and other protected variation continue
to follow their context-specific preservation rules; this fixture does not
authorize global replacement.

## Fresh full-corpus result

The reference run reproduced the committed profiler evidence byte for byte:

| Measurement | Result |
| --- | ---: |
| Records | 189,150 / 189,150 |
| Lexical words | 50,298,925 / 50,298,925 |
| VESUM-attested tokens | 41,006,903 |
| VESUM-unknown tokens | 9,292,022 |
| Distinct VESUM-unknown normalized forms | 1,091,066 |
| Distinct observed lemmas | 143,464 |
| Unresolved candidate rows | 6,646,916 |
| Candidate bytes | 4,071,484,629 |
| Inaccessible sources | 0 |
| Training-admitted records | 0 |

The fresh candidate SHA-256 is
`31dac31ec690a7285a334145fe18d2aa003d82ee34c99ba4748b3d0275b9eb60`.
The aggregate receipt SHA-256 is
`f2ee9e700685458d6a55c386bdb9c8380327493e4e2197ab99a8586b781ed4d6`.

The run took 445.383572 seconds and observed 431,194,112 bytes maximum RSS on
the reference machine. The 4.07 GB candidate artifact was hashed inside a
temporary directory and deleted before the command returned. Runtime and
memory are observations, not byte-stable outputs.

Tokenizer diagnostics remain explicitly `not_run`; no separately approved,
pinned tokenizer interface exists for this build. This is an explicit unknown,
not a successful tokenizer result.

## View-separation result

The run emitted five local artifacts:

| View | Rows | Training eligible | Fixture rows |
| --- | ---: | ---: | ---: |
| Continued pretraining | 1 | 0 | 1 |
| Correction/instruction | 1 | 0 | 1 |
| Preference | 1 | 0 | 1 |
| Quality filter | 1 | 0 | 1 |
| Held-out evaluation | 691 | 0 | 0 |

All five artifacts are schema-homogeneous, have pairwise-disjoint record IDs,
distinct artifact hashes, and exactly one permitted destination. Nine emitted
non-evaluation text fields were rechecked against the frozen exact and
near-duplicate evaluation registry; zero matched. Evaluation gold entered no
non-evaluation view.

The correction-family views intentionally share source lineage and some source
text. Disjoint means separate schemas, record identities, destinations,
receipts, and contamination rules—not that related views must erase their
common source provenance.

## Frozen baseline result

The predeclared question was:

> Does the frozen Gemma 4 reference run outperform the no-op identity baseline
> on the frozen 677-item targeted Ukrainian grammar-and-calque set?

The decision rule required exact reproduction of the source-only request,
saved-response, and score interfaces, plus strict improvement in edit F0.5,
headline-calque recall, and exact-sentence accuracy.

| Metric | Identity | Frozen Gemma 4 31B IT |
| --- | ---: | ---: |
| Edit precision | 0 | 0.2451612903 |
| Edit recall | 0 | 0.1047794118 |
| Edit F0.5 | 0 | 0.1933514247 |
| Headline-calque recall | 0 | 0.0952380952 |
| Exact-sentence accuracy | 0 | 0.1078286558 |

The result is `measurement_interface_validated`. It means the saved Gemma run
does more than copying the source and the harness can reproduce that
measurement. It does **not** mean the Foundry improved Gemma: no Foundry data
was used to train either arm. It also does not rank general Ukrainian fluency;
677 targeted sentences do not measure the full language.

Generation requests contain only `item_id`, source text, source hash, and
prompt hash. Gold fields are empty. The build imports previously saved Gemma
outputs and performs no model generation.

The frozen identity header records the runner source hash that created it.
Today's runner source hash differs because the scorer evolved. The build
therefore regenerates and checks all 677 identity response rows, verifies that
the only header difference is the runner source hash, preserves the frozen
header provenance, and then proves the final saved artifact byte-identical.

## Run the build

Fast validation reuses the committed full-corpus receipt while rebuilding all
fixture views, recipes, and benchmark evidence:

```bash
.venv/bin/python -m scripts.projects.open_model_data.reference_build \
  --profile-evidence committed \
  --output-dir batch_state/foundry-reference \
  --manifest-output batch_state/foundry-reference/manifest.json
```

The evidence-bearing run must point at a checkout containing the ignored
`data/sources.db` and `data/vesum.db` files:

```bash
.venv/bin/python -m scripts.projects.open_model_data.reference_build \
  --profile-evidence fresh \
  --input-root /absolute/path/to/learn-ukrainian \
  --output-dir batch_state/foundry-reference-fresh \
  --manifest-output batch_state/foundry-reference-fresh/manifest.json \
  --observation-output batch_state/foundry-reference-fresh/observation.json
```

`--profile-evidence fresh` fails without an explicit input root. The databases
are opened read-only. Candidate output is temporary. Nothing is uploaded or
published.

## Failure boundaries

The command fails closed if any of these conditions changes:

- a config, schema, source record, correction packet, view, recipe, profile,
  request packet, saved response, or score no longer validates;
- the complete-corpus denominator, candidate hash, or aggregate receipt drifts;
- source-only requests contain a gold field;
- any non-evaluation text matches the exact or near-duplicate evaluation
  registry;
- view record IDs overlap, a view mixes schemas or destinations, or a fixture
  becomes training eligible;
- a recipe authorizes or performs training or a model call; or
- the temporary full-corpus candidate stream remains after verification.

Passing this build proves the interfaces join and the frozen evidence
reproduces. It does not admit a real record, substitute for qualified Ukrainian
human review, or authorize a release or training run.
