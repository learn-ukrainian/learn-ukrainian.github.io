# Ukrainian Open-Weight Evaluation 0.1.0

This is a broad, deterministic companion to the immutable human-gold
[UA Eval 0.1.1](../ua-eval-harness/README.md). It does not replace or modify
that release, and it does not resume the parked human-review-dependent v0.2
proposal. It needs no paid annotator, closed API, or model judge.

## Release and adoption status

> **Gemma 4 HF result correction (updated 2026-08-04):** the HF Jobs output is
> invalid runtime evidence, not a model baseline. All canary and full-run rows
> fail the corrected source-aware integrity gate. Its Hugging Face result
> repository is retained privately, while the incident explanation and hashes
> remain public on GitHub. Do not cite its metrics as Gemma 4 Ukrainian
> results. This does not invalidate the frozen evaluation suite itself; it
> invalidates only that runner/output pairing. See the
> [incident record](HF_JOBS_BASELINE.md).

The repository implementation shipped in PR #6268. The public package uses the
non-colliding tag `ua-open-weight-eval-v0.1.0`; its generated
`PUBLICATION_MANIFEST.json` and `SHA256SUMS` define the canonical released
bytes. The GitHub release remains public. The attempted Gemma 4 QAT Q4_0 HF
Jobs run is retained privately as an invalid failure receipt tracked in
issue #6273. Independent external adoption remains a separate, currently
unproven fact.
The exact bounded execution contract is in the
[HF Jobs baseline runbook](HF_JOBS_BASELINE.md). An adapter, local fixture, or
our own completed run does not demonstrate independent adoption.

## What ships

The release contains 4,000 evaluation-only cases, balanced equally across
error, correct-control, protected, and unresolved categories. Every case has a
retained source locator, an evidence grade, a deterministic content hash, and
one or more named tracks:

- grammar, morphology, calques, and Russian interference;
- quoted Russian, surzhyk, historical or archaic language, and regional or
  dialectal language;
- register, OCR, proper names, ambiguity, overcorrection, and protected text.

The 1,000 error cases retain UA Eval 0.1.1 human gold. The 1,000 correct
controls are deterministic derivatives of accepted human-gold targets.
Protected and unresolved tracks use visibly labelled source-backed or
controlled silver seeds. Context wrappers increase controlled coverage, not
lexical diversity: the 4,000 cases are not 4,000 independent linguistic
judgments. The release claims 1,000 independent human-gold anchors and reports
every other evidence grade explicitly.

The byte-level licensing and attribution boundary is in
[Third-party notices](THIRD_PARTY_NOTICES.md). The separate
[contamination policy](CONTAMINATION_POLICY.md) forbids evaluation cases and
derivatives from every Foundry learning view.

## Ten-minute, zero-API trial

The commands below only build files. They never download or invoke a model.

```bash
.venv/bin/python -m scripts.projects.ua_open_weight_eval.suite_cli verify
.venv/bin/python -m scripts.projects.ua_open_weight_eval.suite_cli prepare \
  --output batch_state/ua-open-weight-eval/requests.jsonl
```

Run that source-only request packet with a model already present on your own
machine. Request identifiers are opaque sequence IDs; internal case IDs and
their category labels are not exposed. Save one JSON object per case using
`saved_response.schema.json`. Verify source-aware response integrity before
scoring it without a judge:

```bash
.venv/bin/python -m scripts.projects.ua_open_weight_eval.response_integrity \
  --responses batch_state/ua-open-weight-eval/responses.jsonl \
  --requests batch_state/ua-open-weight-eval/requests.jsonl
.venv/bin/python -m scripts.projects.ua_open_weight_eval.suite_cli score \
  --responses batch_state/ua-open-weight-eval/responses.jsonl \
  --output batch_state/ua-open-weight-eval/report.json
```

The v0.1.0 suite CLI remains byte-frozen, so the adjacent integrity command is
the required pre-scoring gate for provider/model outputs. It rejects newly
introduced reserved model markers and non-whitespace C0 controls, and it
requires `preserve`/`abstain` output to equal the exact source. It does not try
to classify quoted Russian, surzhyk, historical language, or other source text.

For a reproducible shell-free local invocation, copy
`local_run_config.example.json`, pin the local model revision and SHA-256, and
use `validate-run-config` followed by `run-local`. The interface accepts only
local backends, requires a pre-existing model path, sets common offline flags,
content-hashes a model file or deterministic symlink-free model directory, and
records request, response, model, revision, and command receipts. Local
open-weight model names, including GPT-OSS, are allowed; service providers,
network URLs, API clients, unknown config fields, and inherited credential
variables are not. The interface does not install runtimes or fetch weights.

Reports contain category metrics under each named track. The global quality
score is deliberately `null`; comparing models requires examining the track
and category profile. In particular, correction accuracy must be read beside
correct-control and protected-text overcorrection rates.

## Build the publication package

From the exact reviewed release head, stage the GitHub/Hugging Face payload and
deterministic archive:

```bash
.venv/bin/python -m scripts.projects.ua_open_weight_eval.suite_cli \
  package-publication \
  --source-revision FULL_40_CHARACTER_GIT_SHA \
  --output batch_state/ua-open-weight-eval-publication \
  --archive batch_state/ua-open-weight-eval-v0.1.0.zip
.venv/bin/python -m scripts.projects.ua_open_weight_eval.suite_cli \
  verify-publication-package \
  --package batch_state/ua-open-weight-eval-publication
```

The command rejects missing or extra files and includes no model weights,
provider output, private corpus, VESUM data, literary/textbook corpus content,
or pending v0.2 material. The staged directory is the complete Hugging Face
dataset-repository payload; upload remains an explicit operator approval gate.

Result repositories have a separate fail-closed publication gate. Before any
future Hugging Face result repository is made public, run `verify-results` on
the exact staged result bytes:

```bash
.venv/bin/python -m scripts.projects.ua_open_weight_eval.hf_jobs_baseline \
  verify-results \
  --root batch_state/ua-open-weight-eval-results
```

Publication is eligible only when this command returns verification schema
`ua_open_weight_eval_results_verification.v2`, `status: passed`,
`publication_eligible: true`, and a `semantic_validation` receipt covering the
actual 4,000 saved responses with zero violations. Transport completion,
provider status, file shape, manifests, hashes, metrics, runtime, or cost are
not substitutes. A failure keeps the result repository private; GitHub retains
the public incident explanation and hashes. A verification exception or CLI
exit code `2` produces no v2 eligibility receipt and therefore means
publication is ineligible; it is not an infrastructure-only warning to ignore.

## Українською

Це широке детерміноване доповнення до незмінного набору з людською золотою
розміткою UA Eval 0.1.1. Воно не змінює цей випуск і не відновлює без змін
відкладений план v0.2, який потребував нової людської перевірки. Для роботи не
потрібні платні анотатори, закриті API чи модель-суддя.

У випуску є 4 000 прикладів лише для оцінювання: по 1 000 помилкових,
правильних контрольних, захищених і нерозв'язаних. Для кожного прикладу
збережено джерело, рівень доказовості та хеш. Результати подаються окремо за
всіма чотирнадцятьма напрямами; єдиного оманливого показника «якості
української» немає. Ці 4 000 прикладів не є 4 000 незалежних мовних суджень:
людською золотою основою є 1 000 помилкових прикладів, а решта містить
детерміновані контрольні похідні та явно позначені срібні або нерозв'язані
дані.

Команда `prepare` створює пакет без правильних відповідей і використовує
непрозорі послідовні ідентифікатори без міток категорій. Модель працює з ним
локально, а команда `score` детерміновано оцінює збережені відповіді. Набір і
його похідні заборонено додавати до навчальних представлень Foundry.

Перед оприлюдненням майбутнього репозиторію результатів Hugging Face виконайте
команду `verify-results` для точних підготовлених файлів. Оприлюднення дозволено
лише тоді, коли схема перевірки
`ua_open_weight_eval_results_verification.v2` повертає `status: passed`,
`publication_eligible: true` і квитанцію `semantic_validation` для всіх 4 000
фактично збережених відповідей без жодного порушення. Виняток перевірки або код
завершення `2` означає, що репозиторій результатів має залишатися приватним.

## Acceptance contract

A release is acceptable only when `verify` reproduces all 4,000 rows exactly,
the three frozen upstream hashes still match, every category has 1,000 cases,
all fourteen tracks are present, request rows contain no gold fields, and the
report has no aggregate quality score. The regression suite additionally
proves the reciprocal Foundry contamination firewall.
