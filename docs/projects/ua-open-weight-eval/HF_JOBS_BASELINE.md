# Invalid Gemma 4 HF Jobs run — incident record

> **Disposition (2026-08-03): INVALID — DO NOT USE AS A MODEL BASELINE.** The
> provider jobs completed and the files were structurally valid, but the saved
> responses were runtime-corrupted. All 100 canary rows and all 4,000 full-run
> rows introduced reserved model markers. Of the preserve/abstain rows, 98/98
> in the canary and 3,961/3,961 in the full run failed the exact-copy contract.
> This run says nothing reliable about Gemma 4's Ukrainian ability. Its bytes
> remain available only as a transparent runtime-failure receipt. No rerun is
> authorized.

Issue [#6273](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6273)
authorized one evaluation-only attempt on Hugging Face Jobs. It did not train,
fine-tune, optimize, or publish a model. The attempt is closed as invalid.

## Historical frozen execution contract

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

The canary had a hard 20-minute timeout and a maximum possible charge of USD
0.60 at the recorded price. The old gate recorded model-download time,
generation time, throughput, shape, and hashes, but it did not inspect whether
the actual responses satisfied the evaluation contract. That omission is the
incident's root cause. Current code requires a source-aware response-integrity
receipt with zero violations before any full-run projection can pass.

The earlier retry authorization is superseded by the committed invalid-run
disposition. The launcher now rejects provider execution. Any future attempt
requires a fresh operator-approved issue and a new canary that inspects the
saved semantic output before a full run.

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
but job `6a6fd2686b79c09949c1fb57` then found the same missing alias in the
transport-to-worker handoff after verifying the bundle and installing the
plugin. Its one billed minute cost USD 0.030000. Every L40S interpreter handoff
now invokes `python3` directly, and the cumulative USD 0.090167 is bound into
the next operator gate. Job `6a6fd445a00abefd4b28e088` then proved that the
provider reserves the generic `ACCELERATOR` environment name: the provider
inspection reported the authorized `l40sx1` flavor, but the runtime value was
overwritten before the worker gate. The launch now uses the collision-resistant
`UA_EVAL_HARDWARE_FLAVOR=l40sx1` binding while provider reconciliation remains
the source of truth for actual hardware. That attempt's one billed minute cost
USD 0.030000, so the cumulative USD 0.120167 remains
in every subsequent aggregate budget calculation. Job
`6a6fd5aa6b79c09949c1fbc9` verified the model and tokenizer hashes and reached
vLLM model initialization, where the generic multimodal configuration made the
pinned GGUF plugin demand unused vision-tower parameters. After verification,
the worker now derives and records the hash of a local `Gemma4ForCausalLM`
runtime config from the official `text_config`. The original files and model
bytes remain unchanged; vision tensors are skipped because this evaluation
prohibits use of the multimodal projector. That attempt's three billed minutes
cost USD 0.090000, so cumulative cost is USD 0.210167.
Job `6a6fd8236b79c09949c1fc35` resolved the text-only architecture but emitted
the upstream tokenizer warning requiring `fix_mistral_regex=True`; it was
canceled before generation. The derived runtime tokenizer config now binds
that flag, and the worker passes it explicitly to its renderer. The provider
omitted terminal duration fields for the canceled job, so budget accounting
conservatively reserves three billed minutes (USD 0.090000), raising cumulative
accounted cost to USD 0.300167.
Job `6a6fdeaaa00abefd4b28e281` confirmed the corrected tokenizer path and
`Gemma4ForCausalLM` selection, then exposed a naming gap between Transformers'
`gemma4_text` config and the pinned plugin's existing `gemma4` GGUF architecture
map. The worker now binds that existing map to the text-only config name before
model loading, recording the compatibility alias in its version provenance.
The pinned plugin and checkpoint bytes remain unchanged. Four billed minutes
cost USD 0.120000, raising cumulative cost to USD 0.420167.
Job `6a6fe1ba6b79c09949c1fe21` then verified the complete bundle, loaded the
official GGUF as `Gemma4ForCausalLM` on the L40S, and reached generation. Its
first case exhausted the prompt-only JSON parse retries without producing one
valid response object. The worker now uses the pinned vLLM 0.26.0 structured
output interface with an exact JSON schema for `action` and `output_text`, while
retaining the strict parser as a post-generation validator. This constrains
syntax only and does not expose gold labels, mutate the suite, or weaken
response validation. Five billed minutes cost USD 0.150000, raising cumulative
cost to USD 0.570167.
Job `6a6fe50b6b79c09949c1fe42` confirmed that the pinned vLLM accepted the
structured-output schema, but its first response still did not complete as one
parseable object within the unchanged 160-token limit. To avoid another blind
execution change, a failed response now records its raw attempts and hashes
only inside the authenticated private failure receipt; the provider log keeps
only the redacted error summary. Five billed minutes cost USD 0.150000, raising
cumulative cost to USD 0.720167.
The authenticated private receipt from diagnostic job
`6a6fe7676b79c09949c1fe54` showed that all three attempts consumed the full
160-token allowance on schema-permitted whitespace after `{` or `{"action":`.
Job `6a6fe9a26b79c09949c1fe68` proved that vLLM 0.26.0 ignores the identically
named request-level flag: its engine log retained
`disable_any_whitespace=False`, and the authenticated private receipt showed
the same whitespace-only exhaustion. The pinned xgrammar backend reads this
setting from the engine's `StructuredOutputsConfig`, so the worker now passes
`backend=xgrammar` and `disable_any_whitespace=True` to the `LLM` constructor.
The request still carries the same JSON schema, and the unchanged strict parser
still validates every completed object. Six billed minutes cost USD 0.180000,
raising cumulative cost to USD 1.050167.
Job `6a6fed30a00abefd4b28e51c` proved that engine-scoped whitespace suppression
worked, but its first response entered the documented Gemma 4 repetition defect
inside the schema's otherwise unbounded `output_text` string. One attempt
stopped early at 60 tokens with an open string; two deterministic retries
reached 160 tokens with the same open, highly repetitive string. The worker now
ignores EOS only until the structured object is complete and constrains
`output_text` to 768 characters. That bound exceeds the frozen suite's longest
703-character source, keeps all expected preserve/abstain outputs representable,
and forces xgrammar to close a degenerate string without changing the model,
suite, prompt, temperature, seed, or strict post-generation validation. See the
[upstream Gemma 4 report](https://github.com/vllm-project/vllm/issues/40080).
Five billed minutes cost USD 0.150000, raising cumulative cost to USD 1.200167.
Job `6a6ff094a00abefd4b28e630` showed a decoded NUL or SOH control token before
the final string quote. The subsequent attempt to normalize this corruption
instead of treating it as a terminal semantic failure was incorrect. Five
billed minutes cost USD 0.150000, raising cumulative cost to USD 1.350167.
Job `6a6ff31d6b79c09949c2000b` advanced farther through the first atomic batch,
then exposed the same transport artifact as a short terminal run containing
codes 1, 6, and 21, once followed by trailing markup. That bundle's
normalization accepted non-whitespace C0 controls instead of stopping the run.
That was not valid evidence of a working evaluator. Six billed minutes cost USD
0.180000, raising cumulative cost to USD 1.530167.
Job `6a6ffedca00abefd4b28e89d` showed that the GGUF decoder can place the same
raw C0 bytes before additional decoded Unicode characters. Converting those
bytes into JSON escapes made the transport parseable but preserved corrupted
model output and allowed the run to continue. The current worker rejects raw
control bytes and rejects any new non-whitespace C0 characters relative to the
source. Seven billed minutes cost USD 0.210000, raising cumulative cost to USD
1.740167.
Job `6a7004b06b79c09949c20218` then completed the 100-case canary in 344
RUNNING seconds. Its six billed minutes cost USD 0.180000. All 100 response
records, item identities, required fields, and checkpoint/response hashes
validated against the worker receipt. The 25%-buffered full projection was
3,810 seconds and USD 1.920000, for a projected aggregate of USD 3.840167.

Those checks proved transport and structure only. Replaying the saved canary
through the corrected gate finds 100/100 invalid rows: 98 exact-copy failures,
100 rows with newly introduced reserved model markers, and 49 rows with newly
introduced non-whitespace C0 controls. The full run therefore should never
have launched.

The 4,000-case run resumed only from private direct-upload checkpoints. Job
`6a7007246b79c09949c20228` persisted 2,375 cases before an HF dataset-commit
502; 30 billed minutes cost USD 0.900000. Job
`6a700e66a00abefd4b28e9b9` advanced to 2,950 before the account's rolling
128-commit/hour limit returned 429; ten billed minutes cost USD 0.300000. After
the private write path reopened, job `6a7013d96b79c09949c2029b` advanced to
3,125 before consuming the newly available rolling slots; seven billed minutes
cost USD 0.210000. GPUs stayed idle during the next verified cooldown. Final
job `6a701872a00abefd4b28ea7f` resumed all 3,125 durable records and completed
4,000/4,000 in 803 RUNNING seconds; 14 billed minutes cost USD 0.420000.
Aggregate provider cost for the phase is USD 3.750167, leaving USD 2.249833
under the approved USD 6.000000 ceiling.

Replaying the saved full output finds 4,000/4,000 invalid rows: 3,961 exact-copy
failures, 4,000 rows with newly introduced reserved model markers, and 1,830
rows with newly introduced non-whitespace C0 controls. These counts are
source-aware: a marker or control already present in a frozen source is not
itself treated as introduced corruption. The run is not scoreable and its old
track metrics must not be cited as Gemma results.

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

## Invalid public artifact boundary

The retained public dataset contains the historical bytes listed below, but its
current card labels them an invalid runtime-failure receipt:

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
The original revision remains immutable evidence. The corrective card revision
is verified by a fresh anonymous, token-free download; every non-card payload
file must retain its original hash.

## Українською

**Цей запуск недійсний як оцінювання моделі.** Завдання провайдера завершилися,
але всі 100 відповідей canary і всі 4 000 відповідей повного запуску містять
нові службові маркери моделі. Майже всі відповіді `preserve`/`abstain` також не
відтворили джерело дослівно. Тому опубліковані метрики нічого надійного не
говорять про якість української мови Gemma 4. Дані збережено лише як прозору
квитанцію про помилку середовища виконання; повторний запуск не дозволено.

Підсумок містить окремі звіти за чотирнадцятьма напрямами. Єдиного показника
«якості української» немає. Повні розібрані відповіді публікуються для
відтворюваності, але сирі генерації, приватні контрольні точки, журнали
провайдера та ваги моделі не публікуються.
