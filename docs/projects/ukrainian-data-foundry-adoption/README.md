# Ukrainian Data Foundry community-use and handoff kit

This kit turns the shipped Foundry and open-weight evaluation artifacts into a
small local trial and concrete Lapa or lang-uk handoff packages. It needs no
API key and performs no download, training, optimizer run, weight-adapter
creation, upload, or external submission.

The name of the directory is historical. Generating a trial or handoff package
does not prove adoption, and adoption is not the goal of the prepared-data
program. The kit demonstrates a local interface only. Community-useful,
rights-classified prepared data is tracked under
[#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321).

## Install without an API

Use Python 3.12.8 and the repository's pinned dependency file:

```bash
git clone https://github.com/learn-ukrainian/learn-ukrainian.github.io.git
cd learn-ukrainian.github.io
pyenv local 3.12.8
pyenv exec python -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
```

No provider credential is read. The commands below operate on local JSON or
JSONL only. Teams that already have the repository environment can start with
the trial.

## Ten-minute consumer-owned trial

The default input is the eight-row, project-authored MIT example. Replace it
with a consumer-owned JSONL that satisfies the portable corpus schema when
ready.

```bash
.venv/bin/python -m scripts.projects.open_model_data.adoption_cli trial \
  --output batch_state/foundry-adoption-trial
```

The output contains verified deterministic Foundry views, tokenizer/cost and
recipe receipts, and a source-only 4,000-case evaluation request packet. It
does not invoke a model. Score saved local-model output with the evaluation
command documented in the
[evaluation guide](../ua-open-weight-eval/README.md).

## Lapa data adapter

The pinned integration target is Lapa commit
`7e695c2bb9deaa214421a657ae23c85968947305`, file
`training/lapa-12b-pt-template.yml`, in
[`lapa-llm/lapa-llm`](https://github.com/lapa-llm/lapa-llm). Generate the
handoff:

```bash
.venv/bin/python -m scripts.projects.open_model_data.adoption_cli lapa \
  --foundry-run batch_state/foundry-adoption-trial/foundry \
  --output batch_state/lapa-foundry-handoff
```

`foundry-pretraining.jsonl` uses Lapa's one-field `{"text": ...}` continued
pretraining shape. The adapter accepts only the verified faithful-source view,
requires an empty mask list, and emits separate lineage. It never flattens a
masked modern-learning row, exports a benchmark case, or creates a LoRA or
other weight adapter. The receipt pins the upstream commit and intended YAML
target, so a Lapa maintainer can add the generated file to that template with
reviewable provenance instead of receiving an empty outreach request.

## lang-uk result adapter

The pinned target is the Ukrainian LLM leaderboard commit
`bd3d8431e97b3ff86e4f25381ac6b5ecccadad5f`, with result-dataset revision
`3da506d82b7f960275ed90716da8a8c5c6299f42`. Start with an authentic saved
lm-eval result containing top-level `model_name`, a per-task `n-shot` mapping,
and task dictionaries under `results`. Each task may carry its string `alias`
but must include numeric metrics. Use the upstream filename and destination
`aggregated/results_<created_at>.json`, plus a complete Foundry broad-evaluation
report:

```bash
.venv/bin/python -m scripts.projects.open_model_data.adoption_cli lang-uk \
  --results batch_state/results_2026-08-02T00-00-00.json \
  --broad-report batch_state/ua-open-weight-eval/report.json \
  --foundry-run batch_state/foundry-adoption-trial/foundry \
  --output batch_state/lang-uk-foundry-handoff
```

The standard result file is copied byte-for-byte. Its adjacent, non-consumed
Foundry sidecar
binds the model name, result hash, Foundry run, broad-suite release and case
hashes, all fourteen tracks, and the pinned upstream revisions. Packaging does
not submit anything; maintainers receive a complete artifact pair they can
review and upload through their normal process.

## Українською

Цей комплект перетворює перевірені результати Foundry на малий локальний
дослід і конкретні пакети для Lapa та lang-uk. Ключі API не потрібні. Команди
не завантажують моделі, не навчають їх, не запускають оптимізатор, не створюють
вагові адаптери й нічого не публікують.

Команда `trial` готує представлення Foundry та пакет оцінювання без правильних
відповідей. Команда `lapa` бере лише незамасковані рядки вірного відтворення
джерела й додає окрему історію походження. Команда `lang-uk` перевіряє
збережені числові результати та додає супровідний файл із хешами Foundry й
окремими результатами всіх чотирнадцяти напрямів. Єдиного бала «якості
української» пакет не створює.

## Submission checklist

- Re-run Foundry `verify` and open-weight-evaluation `verify`.
- Keep the upstream commit and result-dataset revision from
  `upstream-locks.json` in the proposed change.
- Attach the generated receipt and lineage/sidecar; do not attach evaluation
  text to a training-data change.
- Report every broad-evaluation track separately, including preservation and
  unresolved cases.
- Let the upstream maintainer perform the actual submission or merge.
