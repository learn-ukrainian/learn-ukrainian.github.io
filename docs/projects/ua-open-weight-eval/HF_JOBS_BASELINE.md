# Official Gemma 4 HF Jobs baseline

Issue [#6273](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6273)
authorizes one evaluation-only baseline on Hugging Face Jobs. This is not
training, fine-tuning, optimizer execution, or publication of a new model.

## Frozen execution contract

| Field | Value |
| --- | --- |
| Suite | `ua_open_weight_eval.v0.1.0` |
| Cases | 4,000; SHA-256 `2164d7ba31322bf3cfbed8045ad3a5b6e759395175b2c1ab11172b9c0f1237db` |
| Model | `google/gemma-4-31B-it-qat-q4_0-gguf` |
| Model revision | `59dde24573e7e61570dba08b18a2e1fe246955ed` |
| Text artifact | `gemma-4-31B_q4_0-it.gguf`; 17,651,001,568 bytes; SHA-256 `179cfb99212709597eae5929112cfca677e1bbf566178b479ae1da0c4772874b` |
| Tokenizer | `google/gemma-4-31B-it-qat-q4_0-unquantized` at `1e4d8beecacb8b7590c1d8bedd7335f687bf311f` |
| Backend | vLLM `0.26.0` plus `vllm-gguf-plugin==0.0.4` |
| Container | `vllm/vllm-openai@sha256:770fe65b2c73ee74a5c42165cf3433de4048cc2cd9c57a937ca4e35aba5aa87b` (Linux amd64) |
| Hardware | one HF Jobs `l40sx1`: Nvidia L40S, 48 GB GPU memory; no exposed ports or SSH |
| Decoding | temperature `0`, seed `0`, maximum 160 generated tokens, two parse retries |
| Context | text-only; maximum model length 8,192 tokens; no multimodal projector |
| Cost | USD 1.80/hour, retrieved 2026-08-02 from the [official Jobs price table](https://huggingface.co/docs/hub/jobs-pricing); USD 6.00 total ceiling |

The official GGUF repository is Apache-2.0. The run downloads the exact text
artifact inside the Job, verifies its SHA-256 before loading, and never uploads
the model or a derivative. The multimodal projector is neither downloaded nor
used.

## Canary gate

The canary contains exactly 100 deterministic source-only requests: 25 error,
25 correct-control, 25 protected, and 25 unresolved cases. Its greedy
track-balancing pass covers all fourteen tracks. The selection is bound to the
frozen cases hash and has SHA-256
`f1af486e06473828a5af18a5c87d617565238cf6649447343ce9f0decf4a5662`.

The canary has a hard 20-minute timeout and a maximum possible charge of USD
0.60 at the recorded price. It records model-download time separately from
generation time, generated-token throughput, and mean case latency. The full
run may launch only when both token-throughput and case-latency projections,
with a 25% safety margin, fit the remaining part of the USD 6.00 authorization.

The operator's 2026-08-03 superseding authorization permits retries for
recoverable execution defects while the cumulative USD 6.00 ceiling and the
buffered full-run projection continue to pass. A failed or unparseable launch
response is reconciled through the unique job labels before another attempt.
Changing the model, suite, hardware, privacy, or publication scope remains
prohibited without new approval.

CPU job `6a6fbf1b6b79c09949c1fa46` is the accepted no-volume transport gate. It
reached RUNNING, downloaded the complete pinned bundle, and verified every
hash. Its later deterministic worker-default failure occurred after those
facts and was fixed, tested, independently reviewed, and merged in PR #6294.
The operator explicitly superseded the receipt-upload requirement and prohibited
another CPU preflight. The accepted CPU charge is USD 0.000167 and is included
in the phase total. The first authorized L40S canary
`6a6fcc80a00abefd4b28dfb6` reached `RUNNING` but exited before model work because
the pinned image exposes `python3` without a `python` alias. Its two billed
minutes cost USD 0.060000. The replacement bootstrap invokes `python3` directly,
and the cumulative USD 0.060167 is bound into its operator gate and remains
in every subsequent aggregate budget calculation.

Historically, the five-minute CPU Basic contract required a complete receipt
before any GPU launch. Its maximum time-based charge was USD 0.000833 at USD
0.01/hour. That receipt requirement is superseded only for this accepted CPU
job and its reviewed post-#6294 execution replacement. A later authorization
outside this bounded phase must define its own transport gate; this document
does not silently waive one.

## Durable and private progress

Hugging Face Jobs deletes its ephemeral filesystem at termination. This launch
therefore has no repository or bucket mounts and passes zero `--volume`
arguments. After the container enters the provider runtime, a minimal bootstrap
downloads the exact reviewed transport from the private staging dataset at an
immutable commit, verifies its hash, and executes it. The transport then
downloads and verifies the frozen code, suite, configuration, and pinned plugin
before model execution.

The worker uploads its exact-prefix append-only checkpoint directly to the
private staging dataset through the authenticated Hub API after each 25-case
batch. Its header binds the suite, request selection, model and tokenizer
revisions, artifact hash, runner hash, runtime versions, decoding settings, and
private artifact prefix. A resume is accepted only when all bindings match and
the checkpoint rows are the exact expected request-order prefix. The prior
bucket-mount remedy is disproven and must not be retried. See the official
[Jobs persistence guidance](https://huggingface.co/docs/hub/en/jobs-manage).

Raw generations, parse failures, private checkpoints, and provider logs remain
private. The complete final parsed responses are public because they are needed
to reproduce all fourteen deterministic reports.

## Free preparation and verification

Run from the dedicated worktree while using the repository's Python 3.12.8
environment:

```bash
/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python \
  -m scripts.projects.ua_open_weight_eval.hf_jobs_baseline prepare-bundle \
  --output /Users/krisztiankoos/projects/learn-ukrainian/batch_state/issue-6273/hf-job-bundle-v4

/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python \
  -m scripts.projects.ua_open_weight_eval.hf_jobs_baseline verify-bundle \
  --bundle /Users/krisztiankoos/projects/learn-ukrainian/batch_state/issue-6273/hf-job-bundle-v4
```

The prepared source-only request packet has SHA-256
`9f624c54857ea8517162c555bc876f34f76a783e3f9feeaf9db4d6c91a9a18bd`.
The reviewed bundle is staged only after its exact Git head passes independent
review and CI. `stage-transport` creates or reuses the private
`krisztiankoos/ua-open-weight-eval-staging-6273` dataset, uploads the bundle
under `bundles/<bundle-sha256>`, and returns the immutable dataset commit used
by both the CPU preflight and any authorized GPU launch. `verify-transport`
then re-downloads the staged files and verifies their exact set, sizes, and
hashes before a provider job is submitted.

## Result publication boundary

After all 4,000 responses complete and deterministic scoring reproduces, the
results dataset contains exactly:

- `README.md` — Hugging Face card, limitations, and English/Ukrainian reproduction;
- `responses.jsonl` — complete parsed actions and output text, without raw generations;
- `metrics.jsonl` — fourteen tracks by four categories (56 rows);
- `report.json` — the deterministic scorer report with its global score `null`;
- `run_receipt.public.json` — model, tokenizer, runtime, job, timing, throughput, and cost bindings;
- `RESULTS_MANIFEST.json` and `SHA256SUMS`;
- `LICENSE-MIT.txt` and `THIRD_PARTY_NOTICES.md`.

The package excludes weights, model derivatives, source cases, source-only
request packets, raw generations, checkpoints, provider logs, failed-attempt
traces, private corpus material, and any aggregate Ukrainian-quality score.
It is verified once locally and once by anonymous download at the immutable
Hugging Face dataset commit.

## Українською

Цей запуск є лише оцінюванням офіційного текстового артефакту Gemma 4 QAT
Q4_0. Він не навчає й не донавчає модель, не виконує кроків оптимізатора та не
публікує ваги. Спершу запускається збалансована детермінована вибірка зі 100
прикладів. Повний запуск 4 000 прикладів дозволено лише тоді, коли прогноз із
25-відсотковим запасом разом із витратами на canary не перевищує 6 доларів США.

Підсумок містить окремі звіти за чотирнадцятьма напрямами. Єдиного показника
«якості української» немає. Повні розібрані відповіді публікуються для
відтворюваності, але сирі генерації, приватні контрольні точки, журнали
провайдера та ваги моделі не публікуються.
