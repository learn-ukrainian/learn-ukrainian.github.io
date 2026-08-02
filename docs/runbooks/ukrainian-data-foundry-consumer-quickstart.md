# Ukrainian Data Foundry Consumer Quickstart

This is the bounded, no-training entry point for a consumer-owned corpus. It
requires no model, API key, accelerator, project-private database, or network
request. The command preserves original text and emits separate evidence and
model-consumer views; it does not “clean” the only copy.

## Ten-minute trial

Run from a checkout whose standard `.venv` is installed:

```bash
trial_dir="$(mktemp -d)"
.venv/bin/python -m scripts.projects.open_model_data.foundry_cli prepare \
  --input data/projects/open_model_data/examples/portable-corpus-v1.jsonl \
  --cost-config data/projects/open_model_data/examples/portable-cost-v1.json \
  --output-dir "$trial_dir/foundry-output"
.venv/bin/python -m scripts.projects.open_model_data.foundry_cli verify \
  --output-dir "$trial_dir/foundry-output"
```

The example has eight short, project-authored MIT-licensed records. Its rights
decisions apply only to those example bytes. They do not authorize release of
the recovered Foundry corpus, a consumer corpus, a dataset, an adapter, or
model weights.

Replace `--input` with a JSONL file that validates against
`portable_corpus_record_v1.schema.json`. Every record must state five decisions
independently:

- local model learning;
- raw-source redistribution;
- dataset publication;
- model publication; and
- public release.

An `allowed` decision requires its own retained evidence locator. An unknown or
denied publication decision does not erase an independently allowed local-
learning decision. Evaluation-only rows and exact or near benchmark matches
never enter learning views.

## Outputs

The output directory is published atomically and contains:

- canonical records with the unchanged original text and retained locators;
- contextual evidence with explicit tracks and no automatic error labels;
- faithful-source and modern-learning views;
- evidence-backed silver correction and preference views;
- a text-free quality-filter view;
- a held-out evaluation view;
- tokenizer, exact cost-arithmetic, non-authorizing recipe, limitation, and
  reproduction receipts.

The modern view uses character masks for candidate or unresolved spans. Quoted
Russian is preserved as quoted text. Historical, archaic, regional, dialectal,
conversational, and marked-register records stay in the faithful view and are
not silently flattened into the modern view.

An optional local tokenizer can be measured without downloading it:

```bash
.venv/bin/python -m scripts.projects.open_model_data.foundry_cli prepare \
  --input consumer-corpus.jsonl \
  --output-dir consumer-foundry-output \
  --tokenizer-path /local/read-only/tokenizer.json \
  --tokenizer-identifier consumer/model \
  --tokenizer-revision 40-character-immutable-revision
```

Cost rows are arithmetic scenarios, never provider quotes. Supply exact train
tokens, epochs, measured aggregate throughput, accelerator count, hourly rate,
storage, evaluation, and failed-run allowance. The emitted recipe always has
`training_authorized: false`.

## Короткий посібник українською

Це обмежений публічний інтерфейс для корпусу, яким володіє споживач. Він не
потребує моделі, ключа API, пришвидшувача, приватної бази проєкту чи мережевого
запиту. Команда зберігає первісний текст і створює окремі похідні представлення;
вона не переписує єдину копію джерела.

У кожному записі треба окремо вказати рішення щодо локального навчання моделі,
поширення сирого джерела, публікації набору даних, публікації моделі та
публічного випуску. Дозвіл без власного локатора доказу відхиляється. Невідомий
статус публікації не скасовує незалежно дозволене локальне використання.

Результати для граматики, морфології, кальок, російського втручання, цитованої
російської, суржику, історичної й архаїчної мови, регіональних і діалектних
форм, регістру, OCR, власних назв, неоднозначності, надмірного виправлення та
захищеного тексту залишаються окремими. Інструмент не обчислює оманливого
єдиного показника «якості української».

Перевірка `verify` повторно обчислює всі хеші без доступу до первісного корпусу.
Рецепт не дозволяє навчання, завантаження моделі, запуск оптимізатора, створення
адаптера чи публікацію ваг.
