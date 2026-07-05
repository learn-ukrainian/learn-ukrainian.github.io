# QG Corpus Report

Issue: [#4311](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4311)

`scripts/audit/qg_corpus_report.py` aggregates stored QG evidence without live
LLM calls. It reads `llm_qg_runs` plus optional saved
`qg_workflow.py --format json` outputs.

## Command

```bash
.venv/bin/python scripts/audit/qg_corpus_report.py \
  --db data/telemetry/llm_qg.db \
  --curriculum-root curriculum/l2-uk-en \
  --format json \
  --output /tmp/qg-corpus-report.json
```

The DB is local telemetry state and must not be committed.

## Idempotency Rule

Reports dedupe DB rows by the latest full composite identity:

```text
level + slug + content_sha + gate_version + prompt_hash
+ checker_version + level_policy_family + reviewer_model
```

Repeated `record_llm_qg()` calls grow rows because every run gets a new
`run_id`; row count is not cache state. Cache hit/stale/miss is computed by
looking for the latest exact composite for each target module.

## Output Schema

Top-level schema version: `qg_corpus_report.v1`.

Required aggregate blocks:

- `selection`: raw DB rows, latest composite rows, dedupe key, load errors.
- `cache`: hit/stale/miss counts overall and by level.
- `defect_rates`: overall, per-level, and per-policy-family defect rates.
- `gold_metrics`: calque and grammar precision/recall/F1 when explicit gold
  comparison metadata exists.
- `gold_metrics.calque.with_contested` and
  `gold_metrics.calque.without_contested`: contested-gold comparison.
- `gold_metrics.calque.contested_delta`: with-contested minus
  without-contested precision/recall/F1.
- `gold_metrics.per_model_calque_f1`: per-reviewer-model calque F1.
- `completion`: `SKIPPED_BUDGET`, `INCOMPLETE`, provider-error, and
  parse/schema-failure counts.
- `spend`: observed/estimated spend per accepted evidence record when stored
  workflow outputs contain cost metadata.
- `unlp_metric_schema`: `unlp_qg_aggregate_metrics.v1`, the #4312 input
  contract.

Contested gold is excluded from pass/fail defect rates and the
`without_contested` metric variant. The `with_contested` variant remains visible
so #4364 can quantify how contested rows move the calque aggregate.
