# ACCEPTED — B2 readiness policy gates

**Status:** ACCEPTED
**Decided on:** 2026-06-29
**Scope:** B2 PR 3 source readiness gates before PR 4 golden pilot.
**Review trigger:** Before PR 4 golden pilot starts, or on 2026-07-13,
whichever comes first.

## Decision

For B2 rebuild readiness, missing plan-level `phase` and `vocabulary_hints` are
legacy metadata gaps, not hard blockers by themselves. `check_plan.py` must keep
those fields required for other levels, but B2 should not fail readiness solely
because old preview-era plans omit them.

B2 discovery YAML is non-authoritative query-keyword scaffolding. Empty
`rag_chunks` and `rag_literary` do not require backfill before PR 4 when the
locked wiki article and `.sources.yaml` registry are the authoritative evidence
layer and pass their gates. Rebuild prompts and PR bodies must not cite discovery
YAML as evidence unless a later remediation PR explicitly backfills it.

## Rationale

The accepted B2 rebuild contract defines source readiness around locked plans,
wiki articles, source registries, and research sufficiency for taught-lesson
generation. It does not require B2 `phase` or `vocabulary_hints` to be present
before a module can enter the rebuild pipeline. Treating those fields as hard
blockers would force a 68+ plan metadata wave before the golden pilot without
improving the authoritative source layer.

Discovery files currently carry query terms derived from plans, not retrieved
evidence. Treating them as evidence would overstate their authority. The safer
policy is to allow PR 4 only when wiki/source-registry gates pass, while keeping
discovery backfill as a separate remediation path if an authoritative source
layer is missing.

## Validation Impact

- `scripts/audit/check_plan.py b2 --failing-only` should no longer report B2
  errors only for missing `phase` or `vocabulary_hints`.
- `scripts/validate_plans.py b2` remains the basic plan schema gate.
- `scripts/wiki/quality_gate.py --track b2` remains the authoritative wiki
  source-readiness gate for PR 4.
