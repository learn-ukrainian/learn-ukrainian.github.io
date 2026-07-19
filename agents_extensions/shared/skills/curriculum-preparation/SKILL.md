---
name: curriculum-preparation
description: Prepare, audit, or resume missing or stale prerequisite evidence for one manifest target, one track missing-only scan, or one bounded homogeneous packet by using the canonical curriculum readiness evaluator. Use for preparation-scoped work before a learner-module build or when curriculum-lifecycle explicitly delegates preparation. Do not use to build learner modules, coordinate a track, run post-build review, certify, publish, or deploy.
---

# Curriculum preparation

Use `scripts/orchestration/curriculum_readiness.py` as the only readiness
engine. Prepare prerequisite evidence only. Produce no learner module bundle and
never invoke `$curriculum-lifecycle`; that skill may call this one, and this one
returns its typed result to the caller.

## Accept one exact scope

Accept exactly one of these operator forms:

```text
Use $curriculum-preparation for <track>/<slug>.
Use $curriculum-preparation for <track> --missing-only.
Use $curriculum-preparation for packet <track>/<slug-1>,<track>/<slug-2> --limit <n>.
```

Treat a packet as bounded only when it has an explicit finite target list, a
positive limit, and no more targets than that limit. Evaluate every target
before mutation and require the same track, `profile_id`, `profile_version`, and
`family`; reject a mixed packet rather than splitting or expanding it.

For `--missing-only`, preserve active-manifest order. Resolve the roster through
`load_active_manifest()` and `load_manifest_track()` from
`scripts.orchestration/curriculum_readiness.py`; do not parse a plans directory,
dashboard, status cache, or legacy readiness source. Evaluate each manifest
target and admit only failed or stale preparation work. Never broaden the scan
to another track.

## Evaluate before acting

Run the canonical evaluator separately for every admitted target:

```bash
.venv/bin/python scripts/orchestration/curriculum_readiness.py \
  --track <track> --slug <slug> \
  [--consumed-preparation-identity <sha256>] \
  > <gitignored-preparation-result.json>
```

The command emits the schema-validated
`curriculum-preparation-result.v1` document. When called by
`$curriculum-lifecycle`, pass only its exact recorded consumed identity. For
standalone use, omit that option unless the operator supplied an authoritative
identity; never infer one.

Use the result cell by cell:

- Act only on a failed `requirements[]` item owned by `preparation`, or on a
  stale preparation identity whose exact `next_action` is `prepare`.
- Leave passing requirements unchanged. Treat an alternative option as
  complete as soon as the evaluator marks its requirement passed.
- Return `plan`, `build`, `certify`, or `stop` results without performing that
  work. A partial bundle, off-manifest target, or active hold is not preparation
  authority.
- Skip current cells during a missing-only scan. Do not rebuild or recertify a
  learner bundle from this skill.

Compare SHA-256 values, never timestamps or prose summaries. Reuse prior
evidence or review only when the target, profile, manifest hash, every relevant
source path and hash, and `preparation_identity` match exactly. Treat any
mismatch as stale and reevaluate; do not copy an identity into a new result.

## Prepare with a bounded review budget

Resolve failed cells with deterministic, local evidence and registered
validators before any model work. Reuse already passing artifacts by exact
hash. Use a model only for semantic synthesis or judgment that the failed cell
actually requires, and keep all work inside the admitted target or homogeneous
packet.

For model-assisted preparation, enforce one shared budget for the exact scope:

1. Consolidate the changed preparation evidence and run one semantic review.
2. If it fails, consolidate all findings into one correction pass and run at
   most one final semantic review.
3. If the final review fails, stop. Record an active reviewed `hold` through
   the existing promotion-evidence registry contract with `status: pass`,
   reviewer family, date, HTTP(S) evidence URL, reason, owner, checked evidence,
   and unblock condition. Do not start a third review, reset the budget, or run
   singleton review loops.

After a terminal HOLD, rerun the evaluator and require
`PREPARATION_HOLD_ACTIVE` with exact `next_action: stop`. Never represent a HOLD
with a new schema, sidecar, or free-form status.

## Return the canonical handoff

Rerun the evaluator after every preparation mutation and after recording a
HOLD. Return its validated result unchanged, including
`preparation_identity`, `consumed_preparation_identity`, `requirements`,
`findings`, `sources`, and the exact `next_action`. For a packet, return one
existing typed result per manifest-ordered target; do not invent a packet
result schema.

In standalone use, report the exact result and end at its `next_action`. When
called by `$curriculum-lifecycle`, return the same result and action to that
caller, which owns the next transition. Preparation never calls lifecycle in
either mode.

On resume, reuse the exact target scope, typed results, identities, hashes, and
remaining review budget. Run canonical readiness first, discard stale cells,
and continue only unfinished preparation-owned work. An exhausted review budget
resumes at reviewed HOLD, not at a fresh review.
