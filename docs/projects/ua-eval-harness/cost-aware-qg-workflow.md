# Cost-Aware Curriculum QG Workflow

Issue: [#4310](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4310)

`scripts/audit/qg_workflow.py` composes the #4308 scorer adapters and the #4309
reviewer helpers into one canonical `ua_contact_quality_evidence.v1` record
per module. It is deliberately cost-aware: deterministic and lookup tiers run
first, and the LLM reviewer is never bulk-run by default.

## Tiers

| Tier | Source | Default behavior |
| --- | --- | --- |
| 0 | `DeterministicRuleAdapter` plus `run_structural_checks()` | Always runs. A hard `FAIL` short-circuits Tier 2 by default. |
| 1 | `UaGecGoldFixtureAdapter` | Cheap lookup. Dry-run reports `gold rows matched: N`, not "all modules hit Tier 1". |
| 2 | `llm_reviewer` prompt/parser | Eligible only for `policy_for_level(level).family` in `b1_plus` or `seminar`, or explicit `--force-llm` / calibration sample. |

The Tier-0 short-circuit intentionally overrides
`curriculum_qg_harness.llm_review.required` for cost. The harness still marks
non-`PASS` modules as LLM-required; this workflow skips the expensive tier on
hard deterministic failures unless `--llm-on-fail` or calibration sample mode
is used for richer diagnostics.

Seminar-family modules must be eligible for Tier 2 because factual,
decolonization, register, and living-subject risks are not fully covered by
Tier 0/1. Live Tier-2 dispatch remains flag-off until #4370 calibration lands;
callers must provide a precomputed reviewer response, reuse a cache hit, or run
with dry-run estimates only.

## Cost Controls

Use `--dry-run` before broad reviewer spend:

```bash
.venv/bin/python scripts/audit/qg_workflow.py \
  --target b1:aspect-in-imperatives:curriculum/l2-uk-en/b1/aspect-in-imperatives \
  --dry-run \
  --format json
```

Dry-run writes nothing. It reports per-tier module counts, Tier-1 gold-row
matches, and Tier-2 token/cost estimates bucketed by level-policy family. The
current estimator uses prompt size with profile-specific completion budgets;
future telemetry can replace the estimator without changing the evidence
contract.

Tier-2 budgets are checked before any reviewer call:

- `--max-llm-calls` is the primary per-run ceiling.
- `--max-cost-usd` caps the whole run.
- `--max-daily-cost-usd` is a local safety rail.
- `--max-module-cost-usd` blocks pathological prompts.

Budget exhaustion is explicit: the evidence carries
`workflow_verdict: SKIPPED_BUDGET` and `completion_status: INCOMPLETE`. Because
`qg_schema` only admits `PASS/WARN/FAIL`, incomplete LLM-required records stay
schema-valid by using top-level `verdict: FAIL` and `terminal_verdict: FAIL`
when fail-closed mode is active.

Broad Tier-2 batches require a passing canary result from
`scripts/audit/llm_qg_canaries.py` before reviewer spend. Dry-run does not need
the canary because it does not call the reviewer.

## Cache Key

The workflow reuses `scripts/audit/llm_qg_store.py`; it does not create a
parallel store. Current Tier-2 cache lookup is composite:

```text
content_sha
+ gate_version
+ prompt_hash
+ checker_version
+ level_policy.family
+ reviewer_model_id
```

The canonical content basis is `llm_qg_store.CONTENT_FILES`:

```text
module.md, activities.yaml, vocabulary.yaml, resources.yaml
```

Plan YAML is intentionally not part of this workflow cache hash. This differs
from `scripts/build/promote_quality_gate.py`, whose promotion sidecar hashes
the plan plus learner files. Workflow evidence records document the chosen
basis under `qg_workflow.content_hash_basis` and
`qg_workflow.content_files`, so cache invalidation is auditable.

`gate_version` and `prompt_hash` must bump when #4370 changes reviewer
calibration; stale LLM evidence then misses the composite cache automatically.

## Contested Gold

Tier 1 preserves #4364 contested-gold metadata. If a UA-GEC gold row is marked
contested, the workflow suppresses that lookup finding but keeps the module
eligible for Tier 2 in LLM-eligible families. This avoids a recall hole where a
noisy gold row hides a real b1-plus or seminar issue from reviewer judgment.
