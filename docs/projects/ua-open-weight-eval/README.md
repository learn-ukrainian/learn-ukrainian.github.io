# Ukrainian Open-Weight Evaluation 0.1.0

This is a broad, deterministic companion to the immutable human-gold
[UA Eval 0.1.1](../ua-eval-harness/README.md). It does not replace or modify
that release, and it does not resume the parked human-review-dependent v0.2
proposal. It needs no paid annotator, closed API, or model judge.

## What ships

The release contains 4,000 evaluation-only cases, balanced equally across
error, correct-control, protected, and unresolved categories. Every case has a
retained source locator, an evidence grade, a deterministic content hash, and
one or more named tracks:

- grammar, morphology, calques, and Russian interference;
- quoted Russian, surzhyk, historical or archaic language, and regional or
  dialectal language;
- register, OCR, proper names, ambiguity, overcorrection, and protected text.

The 1,000 error cases retain UA Eval 0.1.1 human gold. Correct controls are
deterministic derivatives of accepted human-gold targets. Protected and
unresolved tracks use visibly labelled source-backed or controlled silver
seeds. Context wrappers increase coverage, not lexical diversity; the receipt
reports evidence grades so consumers cannot mistake those cases for new human
annotations.

## Ten-minute, zero-API trial

The commands below only build files. They never download or invoke a model.

```bash
.venv/bin/python -m scripts.projects.ua_open_weight_eval.suite_cli verify
.venv/bin/python -m scripts.projects.ua_open_weight_eval.suite_cli prepare \
  --output batch_state/ua-open-weight-eval/requests.jsonl
```

Run that source-only request packet with a model already present on your own
machine. Save one JSON object per case using
`saved_response.schema.json`. Then score it without a judge:

```bash
.venv/bin/python -m scripts.projects.ua_open_weight_eval.suite_cli score \
  --responses batch_state/ua-open-weight-eval/responses.jsonl \
  --output batch_state/ua-open-weight-eval/report.json
```

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

## Українською

Це широке детерміноване доповнення до незмінного набору з людською золотою
розміткою UA Eval 0.1.1. Воно не змінює цей випуск і не відновлює без змін
відкладений план v0.2, який потребував нової людської перевірки. Для роботи не
потрібні платні анотатори, закриті API чи модель-суддя.

У випуску є 4 000 прикладів лише для оцінювання: по 1 000 помилкових,
правильних контрольних, захищених і нерозв'язаних. Для кожного прикладу
збережено джерело, рівень доказовості та хеш. Результати подаються окремо за
всіма чотирнадцятьма напрямами; єдиного оманливого показника «якості
української» немає.

Команда `prepare` створює пакет без правильних відповідей. Модель працює з ним
локально, а команда `score` детерміновано оцінює збережені відповіді. Набір і
його похідні заборонено додавати до навчальних представлень Foundry.

## Acceptance contract

A release is acceptable only when `verify` reproduces all 4,000 rows exactly,
the three frozen upstream hashes still match, every category has 1,000 cases,
all fourteen tracks are present, request rows contain no gold fields, and the
report has no aggregate quality score. The regression suite additionally
proves the reciprocal Foundry contamination firewall.
