# Reference modules — golden targets for the new pipeline evaluator

This directory holds **manually-patched, quality-reference-grade** module
artifacts that the new (post-#1577 reboot) pipeline should aim to match
as it scales. They are NOT shipped curriculum; they are calibration
targets for evaluation.

## How to use

When the new pipeline generates a module, evaluators (Python QG + LLM
QG) compare it against the corresponding `testbed/reference/{level}/{n}/`
artifacts. The new module does not need to be byte-identical — it needs
to be at least as good on the dimensions that matter (correctness,
naturalness, decolonization, level-appropriate immersion).

## Provenance

These artifacts originate from V6-era pipeline output that was then
**manually patched** by the user (Krisztian) over multiple iterations to
reach a quality bar Krisztian considered shippable. The pipeline alone
was not able to produce content of this quality reliably — that's why
the curriculum-reboot EPIC #1577 exists.

## Currently quarantined

| Path | Source | Status |
|---|---|---|
| `a1/1/module.md` | `curriculum/l2-uk-en/a1/sounds-letters-and-hello.md` | Working-tree manual patches preserved 2026-04-25 evening, before bulk legacy discard (Phase 1 Q3 of #1577). |
| `a1/1/activities.yaml` | `curriculum/l2-uk-en/a1/activities/sounds-letters-and-hello.yaml` | Same. |

Add more `{level}/{n}/` subdirectories as the user identifies other
manually-patched modules with reference-grade quality. Per the consensus
discussion (round 2 corrections), the user's flagged exemplars for the
reboot fan-out are:

- A1 exemplar: a1/20 `my-morning` (mid-A1 steady-state, NOT a1/1)
- A2 exemplar: a2/30 `work-and-food` (50–80% UK band)
- B1 exemplar: b1/20 `pluralia-tantum` (~100% UK)

a1/1 is intentionally LAST in the build order (Phase 8 of #1577) —
the literacy-bootstrap special case. These patches exist as a
ground-truth reference, not an early build target.

## What this directory is NOT

- NOT a place for new pipeline output (that goes in
  `curriculum/l2-uk-en/{level}/`)
- NOT shipping content (the live site is `starlight/src/content/docs/`)
- NOT a substitute for the plan (`curriculum/l2-uk-en/plans/{level}/`)
