# Ukrainian Data Foundry Gemma 4 Treatment

> **Owner:** [#6170](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6170)
> under [#6164](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6164)
> **Current boundary:** Stage 0 is reproducible and no-cost. A separately
> bounded, non-treatment hardware validation is specified below but cannot
> launch: local Hugging Face authentication/model access is not configured and
> its exact probe authorization artifact is absent. Model-weight download and
> treatment training still require the exact operator authorization receipt.

## What this experiment can decide

The experiment answers one question: when the same admitted Ukrainian
Wikipedia text is used for continued pretraining, does suppressing loss on the
Foundry's detected non-modern, quoted, protected, and unresolved spans improve
the frozen minimal-edit task without increasing unwanted normalization?

The primary causal contrast is `modern_mask_cpt - faithful_cpt`. An untreated
checkpoint is evaluated as a descriptive anchor. It is not substituted for the
paired contrast. The historical OpenRouter Gemma result validates the
measurement interface only; its provider catalog version is not an immutable
weight revision and therefore cannot serve as the causal control.

The only decision this experiment can change is whether to retain the modern
loss-mask policy for this exact recipe. It cannot establish general Ukrainian
fluency, human acceptance of silver evidence, deployment readiness, or
leaderboard superiority.

## Frozen checkpoint and arms

All arms use `google/gemma-4-31B-it` at immutable Hugging Face revision
`842da3794eaa0b77d5f08bae87a17459d91ff475`. The three arms are:

| Arm | Training | Purpose |
| --- | --- | --- |
| `untreated_it` | none | Descriptive exact-checkpoint anchor |
| `faithful_cpt` | Adapter-only QLoRA over accepted source text | Control for continued-pretraining exposure |
| `modern_mask_cpt` | Identical QLoRA run with overlapping mask tokens set to loss `-100` | Test the sole Foundry intervention |

The official model card loads Gemma 4 through `AutoProcessor` and
`AutoModelForMultimodalLM`; the treatment does not reuse the old
`AutoModelForCausalLM` Literary Poltava script. The immutable snapshot manifest
binds nine required files, 62,578,656,403 bytes in total, including the two
weight shards. Only the small configuration and tokenizer files have been
downloaded. Weight download remains unperformed.

The IT tokenizer is not byte-identical to the base tokenizer used in Phase 3.
The exact IT tokenizer was therefore rerun over all 1,028 records. It reproduces
7,696,734 non-special tokens and 183,640 zero-loss tokens with zero projection
failures. That result is committed in
`gemma4_it_tokenizer_diagnostics_v1.json` rather than inferred from the base
tokenizer receipt.

## Common split and automated safety probes

Both trained arms use the same split key and namespace:

```text
SHA-256("gemma4-it-wikipedia-mask-ablation-v1" NUL source_payload_id)
modulo 1000
```

Buckets `0..199` are validation-only. This leaves 830 matched training records
and 6,187,314 IT-tokenizer tokens per full Stage 2 arm. The same 198 source
records are excluded from both arms.

The validation partition yielded a deterministic 300-item safety inventory:

- 120 no-change proxies from articles with no detector masks; and
- 180 protected-span probes sampled from 3,935 available protected spans.

These are automated non-human proxies, not Ukrainian linguistic gold. Absence
of a detector candidate does not prove that a sentence is error-free, and
substring preservation does not prove full contextual acceptability. Their
bounded job is to detect obvious new normalization damage without requiring an
unavailable reviewer panel. Modern can advance only with zero protected-span
failures and a no-change edit rate no higher than faithful.

The source-bearing probe JSONL stays in ignored local state. The committed
receipt binds its SHA-256, counts, source views, common split, limitations, and
no-training/no-publication state.

## Pre-Stage-1 hardware validation

This is a single, paid hardware-validation attempt only. It is not a treatment
run, does not consume corpus or evaluation data, and produces no causal or
quality claim. Passing it neither authorizes nor satisfies the frozen Stage 1
requirement for an A100 or H100.

The validation uses a [Hugging Face Job](https://huggingface.co/docs/huggingface_hub/guides/jobs)
with the `l40sx1` flavor. Hugging Face documents this flavor as one 48 GB
NVIDIA L40S with 8 vCPUs, 62 GB RAM, and 380 GB ephemeral storage at USD
0.03/minute; `timeout=3600` is mandatory and exact. Its maximum provider
compute charge is therefore USD 1.80, within the operator's EUR 3 ceiling.
Hugging Face is selected for this narrow probe because its Job timeout stops
the running job and its billing; this is a bounded-provider-control choice,
not a comparison of provider quality. See the official [Jobs pricing and
billing](https://huggingface.co/docs/hub/en/jobs-pricing) and [Job
configuration](https://huggingface.co/docs/hub/en/jobs-configuration) guidance
for hardware and timeout behavior.

The disposable job must use a deterministic synthetic fixture only, then run
the frozen 4-bit NF4/BF16 QLoRA configuration at its actual sequence length of
4,096 for exactly one optimizer step. It must save a disposable adapter
checkpoint, start a clean process, and reload/resume from that checkpoint. It
must not read any Foundry corpus, held-out evaluation, safety inventory, or
other evaluation data; it must not upload or publish any artifact. The required
evidence is hardware identity, peak VRAM, step/runtime timing, checkpoint
save/reload result, timeout setting, and final Job status.

Each child phase records an in-memory step fact immediately after
`optimizer.step()` and then atomically writes and fsyncs the same fact before
checkpoint work. The error channel preserves the in-memory fact if marker I/O
fails. A hard process kill in the instruction-scale interval between the
optimizer call returning and the Python flag assignment cannot be proven after
the fact; that residual is reported conservatively rather than inferred.

Launch remains impossible until both blockers are cleared: local Hugging Face
authentication and access to the exact model are not configured, and an exact
operator authorization artifact for this one-attempt probe does not exist.

Once that exact authorization exists, validate it without launching anything:

```bash
.venv/bin/python -m scripts.projects.open_model_data.gemma_hardware_probe \
  prepare \
  --authorization batch_state/6170/gemma-hardware-probe.authorization.json \
  --hf-cli .venv/bin/hf \
  --output batch_state/6170/hf-probe-preparation.json
```

The only paid entry point is the separate `launch` command. It creates one
detached Job with the frozen 3,600-second provider timeout and records the Job
ID immediately:

```bash
.venv/bin/python -m scripts.projects.open_model_data.gemma_hardware_probe \
  launch \
  --authorization batch_state/6170/gemma-hardware-probe.authorization.json \
  --hf-cli .venv/bin/hf
```

Before claiming the attempt, the launcher queries all provider Jobs for the
exact authorization hash and fails closed if any match exists. It then creates
both a host-global authorization-hash claim shared by local worktrees and
`batch_state/6170/hf-probe-launch.json`, queries the provider a second time, and
creates a private read-only upload snapshot whose bytes are verified against the
authorization immediately before the provider call. The HF CLI uploads that
snapshot, not the mutable working-tree script. If either claim or snapshot
already exists, launch fails closed. A launch failure still consumes this
one-attempt authorization, because the provider may have accepted a Job even
when its response was lost. Hugging Face Jobs does not expose an atomic
idempotency key, so this authorization is deliberately single-operator and must
not be launched concurrently from different hosts; sequential cross-host reuse
is rejected by the provider authorization-hash label.

After that Job reaches a terminal state, collect its logs, provider inspection,
resource-statistics observation, and completed-or-aborted worker receipt. The
collector rejects non-terminal state, flavor/label/endpoint drift, duration
over 3,600 seconds, a mismatched runner, or a server-derived compute charge over
USD 1.80. The receipt records the provider-derived charge from server-reported
running seconds; it leaves invoice-exact USD/EUR fields null because the Jobs
inspection API does not return the settled invoice:

```bash
.venv/bin/python -m scripts.projects.open_model_data.gemma_hardware_probe \
  collect \
  --job-id "$(jq -r .job_id batch_state/6170/hf-probe-launch.json)" \
  --authorization batch_state/6170/gemma-hardware-probe.authorization.json \
  --hf-cli .venv/bin/hf \
  --output-directory batch_state/6170/hf-probe-evidence
```

All three output locations are ignored runtime evidence. They are not dataset,
model, or evaluation artifacts and must not be committed.

## Economic ladder

Google documents that tuning needs substantially more compute and memory than
inference and recommends parameter-efficient methods such as LoRA when
resources are constrained. The Gemma 4 31B load itself is roughly 69.9 GB in
BF16 and 17.5 GB at 4-bit before tuning overhead, so the local 16 GB M4 is not a
training target. See the official [tuning guidance](https://ai.google.dev/gemma/docs/tune?hl=en),
[Gemma 4 overview](https://ai.google.dev/gemma/docs/core), and
[model card](https://huggingface.co/google/gemma-4-31B-it).

The frozen ceiling is USD 100 all-inclusive on an ephemeral 80 GB A100 or H100:

1. Stage 1 runs one 1,048,576-token faithful/modern paired smoke with seed
   `6170`, at most four GPU-hours per run and USD 10 total.
2. Stage 2 starts only if Stage 1 stays within USD 10, reloads its checkpoints,
   preserves paired invariants, trips no safety abort, and forecasts the whole
   program within USD 100. It runs seeds `6170`, `6171`, and `6172` over the
   exact 6,187,314-token common training partition for both arms. Stage 2 may
   spend at most the remaining USD 90 and nine GPU-hours per run.

Current [RunPod pricing](https://www.runpod.io/pricing) lists 80 GB A100s at
USD 1.39–1.49 per hour and 80 GB H100s at USD 2.89–2.99 per hour. Runtime is
still an estimate until Stage 1 measures this exact Gemma 4 QLoRA path. No
provider account, machine, or weight download is authorized merely by the
preregistration.

## Evaluation sensitivity boundary

The frozen 677-item evaluator already implements the preregistered 10,000-draw
paired sentence bootstrap. Its saved Gemma 4 baseline has edit F0.5 `0.19335`
and exact-sentence accuracy `73/677` (`10.78%`). The set can detect a useful
multi-point change; it cannot turn a small or null result into proof that the
treatment has no effect.

For exact-sentence accuracy, let `q` be the fraction of items on which only one
of the paired arms is exactly correct. The normal planning approximation for
80% power with a two-sided 95% rule is
`(1.96 + 0.842) × sqrt(q / 677)`. This gives:

| Assumed paired discordance | Approximate detectable difference | Net sentences |
| ---: | ---: | ---: |
| 5% | 2.41 percentage points | 17 |
| 10% | 3.40 percentage points | 24 |
| 15% | 4.17 percentage points | 29 |
| 20% | 4.82 percentage points | 33 |
| 30% | 5.90 percentage points | 40 |

For F0.5, the existing baseline and cross-model scale checks put the practical
sensitivity around 3–5 F0.5 points unless the two treatment arms are very
highly correlated. This is a planning bound, not a new acceptance threshold.
The L40S hardware validation is unaffected because it makes no efficacy claim.
Before any multi-seed paid efficacy program, the preregistration still needs a
seed-level aggregation rule and an explicit practical-effect interpretation so
seeds cannot be selected after scores are visible.

## Reproduce Stage 0

The Phase 3 source-bearing views must exist at the paths bound by the
preregistration. Build the source-bearing safety inventory:

```bash
.venv/bin/python -m scripts.projects.open_model_data.prepare_treatment \
  build-probes \
  --faithful-view batch_state/6170/phase3/wikipedia-faithful.jsonl \
  --modern-view batch_state/6170/phase3/wikipedia-modern.jsonl \
  --output batch_state/6170/treatment-safety-probes.jsonl \
  --receipt data/projects/open_model_data/treatments/gemma4_it_safety_probe_receipt_v1.json
```

Run the no-authorization preflight:

```bash
.venv/bin/python -m scripts.projects.open_model_data.prepare_treatment \
  preflight \
  --preregistration \
  data/projects/open_model_data/treatments/gemma4_it_wikipedia_mask_ablation_preregistration_v1.json \
  --output \
  data/projects/open_model_data/treatments/gemma4_it_stage0_preflight_v1.json
```

The committed result is deliberately `REVISE` with exactly two blockers:
`operator_authorization_pending` and `immutable_model_snapshot_pending`.
Everything that can be verified before spending money is already green.

After the operator approves the exact checkpoint, stages, and ceiling, create a
`treatment_authorization_v1` receipt bound to the preregistration SHA-256. On
the rented machine, download the immutable snapshot and rerun preflight with
both `--authorization` and `--model-directory`. Every one of the nine files
must match the frozen byte count and SHA-256 before `PROCEED` is possible.

## Evaluation commands

The primary paired comparison uses the same 677 item indices for every one of
10,000 bootstrap resamples:

```bash
.venv/bin/python -m scripts.projects.ua_eval_harness.compare_treatment_runs \
  paired \
  --control batch_state/6170/eval/faithful.responses.jsonl \
  --treatment batch_state/6170/eval/modern.responses.jsonl \
  --output batch_state/6170/eval/paired-contrast.json
```

The scorer rejects drift in the manifest, prompt, decoding, runner, coverage,
or item pairing. It reports the modern-minus-faithful F0.5 difference and
paired percentile 95% interval. A positive point estimate is insufficient: the
lower interval bound must exceed zero.

Safety responses are scored separately:

```bash
.venv/bin/python -m scripts.projects.ua_eval_harness.compare_treatment_runs \
  safety \
  --probes batch_state/6170/treatment-safety-probes.jsonl \
  --faithful batch_state/6170/eval/faithful-safety.responses.jsonl \
  --modern batch_state/6170/eval/modern-safety.responses.jsonl \
  --output batch_state/6170/eval/safety-contrast.json
```

Modern is retained only if both the primary statistical gate and this separate
safety gate pass. A null, mixed, negative, or unsafe result is a valid terminal
result and is reported without changing thresholds or selecting a checkpoint
after seeing scores.

## Immediate aborts

Execution stops on artifact or schema drift, evaluation contamination, an arm
difference beyond the preregistered loss policy, tokenizer or mask mismatch,
missing authorization, non-finite loss or gradients, out-of-memory,
checkpoint-reload failure, cost/runtime breach, safety regression, or any
upload/publication attempt. Execution receipts retain the actual runtime,
tokens, loss, cost, artifact hashes, checkpoint hashes, and abort reason.
