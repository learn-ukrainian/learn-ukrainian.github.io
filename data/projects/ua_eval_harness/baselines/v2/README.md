# Gemma 4 reference baseline

This directory contains the complete 677-item Gemma 4 reference run for UA
evaluation harness release 0.1.1. The model saw only item identifiers, source
sentences, and the frozen minimal-edit instruction. Held-out references and
scoring annotations were not supplied during generation.

## Results

| Baseline | Edit precision | Edit recall | Edit F0.5 | Headline-calque recall | Exact sentence |
| --- | ---: | ---: | ---: | ---: | ---: |
| Identity | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0/677 |
| Development-fixture rules | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0/677 |
| GPT-5.6 Terra | 0.3110 | 0.1309 | 0.2439 | 0.1410 | 109/677 |
| Gemma 4 31B IT | 0.2452 | 0.1048 | 0.1934 | 0.0952 | 73/677 |

The headline-calque metric is recall only. Saved response edits are untyped, so
calque-specific false positives and precision cannot be identified. The full
counts, per-tag results, diagnostic data, and uncertainty notes are in
`gemma-4-31b-it.report.json`.

## Files

Researchers ordinarily need:

- `gemma-4-31b-it.responses.jsonl`: the scorer-ready saved run with 677
  responses and its provenance header;
- `gemma-4-31b-it.report.json`: the reproduced score report;
- `gemma-4-31b-it.run-config.json`: exact provider, route, model, alias, tool,
  and decoding declarations.

The following evidence files are useful for auditing or independently repeating
generation, but are not needed to compare the published scores:

- `gemma-4-31b-it.model-output.jsonl`: normalized provider output before import;
- `gemma-4-31b-it.metadata.json`: generation hashes, all 34 batch receipts,
  retry counts, and gold-isolation declaration;
- `gemma-4-31b-it.raw-provider-output.jsonl`: unmodified successful OpenCode
  NDJSON output, one row per batch;
- `gemma-4-31b-it.failed-attempts.jsonl`: the two rejected first attempts,
  including raw output and receipt hashes.

## Model and route

- Requested route: `openrouter/google/gemma-4-31b-it`
- Resolved model: `google/gemma-4-31b-it`
- Model catalog revision: OpenRouter entry `created=1775148486`
- Invocation tool: OpenCode 1.17.13, `--pure`, chat agent, tools disabled
- Provider: OpenRouter paid route
- Batch transport: `tagged_text_blocks.v1`
- Batch size: 20; workers: 1; one retry after each first attempt

The model identity was checked against the
[Google Gemma API documentation](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api)
and the
[OpenRouter model page](https://openrouter.ai/google/gemma-4-31b-it) on
2026-07-30.

OpenCode did not expose temperature, top-p, top-k, seed, stop sequences, or an
explicit maximum-output setting for this route. No benchmark-specific safety
override was applied. These limitations are recorded as `not exposed` rather
than inferred values.

The accepted attempts used 119,875 input tokens and 56,144 output tokens. Their
recorded cost was USD 0.0392401. Two first attempts were rejected: batch 9 was
truncated before an end marker, and batch 27 returned the wrong response count.
Both retries succeeded without manual repair.

## Integrity

The source-only request packet contains 677 unique identifiers in the same order
as the saved responses. Its canonical packet SHA-256 is:

```text
77afe3da4ea590e060602af53b60ac8f350369f8a323521dee99f42100815fca
```

The frozen minimal-edit prompt SHA-256 is:

```text
f121546dcbaf602c58c7d85977ad792eb9be402dd1e01a6a556ba966dac2c96a
```

Artifact SHA-256 values:

| Artifact | SHA-256 |
| --- | --- |
| Failed attempts | `da0e9545321bc7506954ebeddd29e47161d09ebcd6c9d2df2ffba56bbbead9f1` |
| Metadata | `82d54ba3f669ac04509121537b4e3452d88861cacd0da2254cb923aba7e181e2` |
| Normalized model output | `8c24c21a10557f679f302fb5fcbe2387f3f7bd7086c908e523d37c5da51d9586` |
| Successful raw output | `99d373000acf73f5eb8c06bbee25dc8221e3484b73ad9403e6f6b29072d1041f` |
| Score report | `5c50e17373f17a8c844c35e68198fa32dafcd8ad022d308d45adf7773f8e32ea` |
| Saved responses | `f6e59c2ad31f1e6a74296f66d2d693117e30a9214e147e355a24fc2cd79a469f` |
| Run configuration | `b2630fa7d58b92c110582885ee5f13f42306c22c5b316405f1efd734a99ea911` |

## Reproduce import and scoring

From a clean repository root with the project environment installed:

```bash
.venv/bin/python scripts/projects/ua_eval_harness/evaluate_model.py import \
  --requests data/projects/ua_eval_harness/baselines/v1/generation_requests.jsonl \
  --model-output data/projects/ua_eval_harness/baselines/v2/gemma-4-31b-it.model-output.jsonl \
  --metadata data/projects/ua_eval_harness/baselines/v2/gemma-4-31b-it.metadata.json \
  --output data/projects/ua_eval_harness/baselines/v2/gemma-4-31b-it.responses.jsonl

.venv/bin/python scripts/projects/ua_eval_harness/evaluate_model.py score \
  --responses data/projects/ua_eval_harness/baselines/v2/gemma-4-31b-it.responses.jsonl \
  --output data/projects/ua_eval_harness/baselines/v2/gemma-4-31b-it.report.json
```

The immutable writer verifies that existing outputs are byte-identical. It
refuses to replace a different response or report.
