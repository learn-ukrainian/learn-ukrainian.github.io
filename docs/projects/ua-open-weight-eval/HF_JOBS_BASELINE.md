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

No paid retry is automatic. A failed or unparseable launch response is
reconciled through the unique job labels before another attempt is considered.
A paid vLLM compatibility failure is preserved and requires new approval before
a llama.cpp fallback attempt.

## Durable and private progress

Hugging Face Jobs deletes its ephemeral filesystem at termination. The worker
therefore writes an exact-prefix append-only checkpoint to a private mounted
Hugging Face Bucket after every completed request. Its header binds the suite,
request selection, model and tokenizer revisions, artifact hash, runner hash,
runtime versions, and decoding settings. A resume is accepted only when all
bindings match and the checkpoint rows are the exact expected request-order
prefix.

The bucket mount is authorized when the Job is created, so no token is passed
to the Job. The public model is downloaded without a token. See the official
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
The complete ignored job bundle has SHA-256
`c7efff840695dc0d9e8c7de236f0f787e30ae41c5a60d246f61202436bcf24f5`.

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
