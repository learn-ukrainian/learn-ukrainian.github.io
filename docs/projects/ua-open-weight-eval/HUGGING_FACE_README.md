---
annotations_creators:
  - expert-generated
  - other
configs:
  - config_name: default
    data_files:
      - path: cases.jsonl
        split: test
language:
  - uk
language_creators:
  - found
  - expert-generated
license:
  - cc-by-4.0
  - mit
multilinguality:
  - monolingual
pretty_name: Ukrainian Open-Weight Evaluation 0.1.0
size_categories:
  - 1K<n<10K
source_datasets:
  - extended
tags:
  - evaluation
  - open-weight
  - text
  - ukrainian
task_categories:
  - text-generation
  - text-classification
---

# Ukrainian Open-Weight Evaluation 0.1.0

A frozen, 4,000-case Ukrainian correction-and-preservation evaluation for local
open-weight models. It reports fourteen tracks separately, uses deterministic
saved-output scoring, and has no global Ukrainian-quality score or model judge.

The dataset has mixed row-level licensing: 2,000 UA-GEC-derived rows are CC BY
4.0, and 2,000 project-authored silver or unresolved rows are MIT. Read
`THIRD_PARTY_NOTICES.md` and the generated `PUBLICATION_MANIFEST.json` before
reuse.

## What the 4,000 cases mean

- 1,000 error cases derive from the immutable UA Eval 0.1.1 human-gold anchor.
- 1,000 correct controls derive from accepted human-gold targets.
- 1,000 protected cases and 1,000 unresolved cases derive from 28
  project-authored source-backed or controlled silver seeds.
- Deterministic context wrapping creates controlled cases, not 4,000
  independent linguistic judgments. The release claims 1,000 independent
  human-gold anchor judgments.

Evidence grades are embedded per row: `human_gold`,
`human_gold_derived_control`, `source_backed_silver`, `controlled_silver`, or
`unresolved`.

## English quickstart

Load the evaluation split without treating it as training data:

```python
from datasets import load_dataset

cases = load_dataset("OWNER/ua-open-weight-eval", split="test")
```

For the verified offline runner and scorer, clone the exact GitHub tag:

```bash
git clone --branch ua-open-weight-eval-v0.1.0 \
  https://github.com/learn-ukrainian/learn-ukrainian.github.io.git
cd learn-ukrainian.github.io
pyenv local 3.12.8
pyenv exec python -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m scripts.projects.ua_open_weight_eval.suite_cli verify
.venv/bin/python -m scripts.projects.ua_open_weight_eval.suite_cli prepare \
  --output batch_state/ua-open-weight-eval/requests.jsonl
```

Run the source-only requests with a model already present on your machine, save
one object per case using `saved_response.schema.json`, then score. Request IDs
are opaque and do not expose internal category labels:

```bash
.venv/bin/python -m scripts.projects.ua_open_weight_eval.suite_cli score \
  --responses batch_state/ua-open-weight-eval/responses.jsonl \
  --output batch_state/ua-open-weight-eval/report.json
```

Use `local_run_config.example.json`, `validate-run-config`, and `run-local` to
create an offline local-run receipt. The command refuses network providers and
does not download weights. The standalone `run_mlx_model.py` is a resumable MLX
runner for a model that is already present locally; install and select the
open-weight runtime separately under its own terms.

## Коротка інструкція українською

Це набір лише для оцінювання. Не додавайте приклади, відповіді, виправлення чи
похідні правила до навчальних даних.

```bash
.venv/bin/python -m scripts.projects.ua_open_weight_eval.suite_cli verify
.venv/bin/python -m scripts.projects.ua_open_weight_eval.suite_cli prepare \
  --output batch_state/ua-open-weight-eval/requests.jsonl
```

Запустіть пакет запитів уже наявною локальною моделлю, збережіть відповіді за
схемою `saved_response.schema.json`, а потім виконайте команду `score`.
Публікуйте результати окремо за всіма чотирнадцятьма напрямами разом із хешем
випуску, точною версією моделі й токенізатора, параметрами декодування та
локальною квитанцією запуску.

## Tracks and limitations

The tracks are grammar, morphology, calques, Russian interference, quoted
Russian, surzhyk, historical or archaic language, regional or dialectal
language, register, OCR, proper names, ambiguity, overcorrection, and protected
text.

Exact-match scoring misses valid alternatives outside the accepted set.
Silver cases reflect project-authored assumptions and limited lexical
diversity. Public benchmark exposure may contaminate pretrained models. A good
result on these tracks is not a claim of broad Ukrainian fluency.

See `DATA_CARD.md`, `CONTAMINATION_POLICY.md`, `THIRD_PARTY_NOTICES.md`,
`PUBLICATION_MANIFEST.json`, and `SHA256SUMS` for the complete evidence and
rights boundary.
