---
name: curriculum-preparation
description: Prepare, audit, or resume missing or stale prerequisite evidence for one manifest target, one track missing-only scan, or one bounded homogeneous packet by using the canonical curriculum readiness evaluator. Use for preparation-scoped work before a learner-module build or when curriculum-lifecycle explicitly delegates preparation. Do not use to build learner modules, coordinate a track, run post-build review, certify, publish, or deploy.
---

# Curriculum preparation

Use `scripts/orchestration/curriculum_readiness.py` as the only readiness
engine. Prepare prerequisite evidence only. Produce no learner module bundle and
never invoke `$curriculum-lifecycle`; that skill may call this one, and this one
returns its typed result to the caller.

When `$curriculum-lifecycle` delegates an acquired target whose canonical
`next_action` is `plan` or `prepare`, accept its exact target and acquisition
binding, run canonical readiness before mutation, and remain inside this
preparation scope. Never start, resume, or reacquire lifecycle. Rerun canonical
readiness after each preparation mutation, then return the first fresh `build`,
`certify`, or reviewed `stop` result to the caller.
This lets a standalone preparation campaign stop with a build-authorized queue
without starting lifecycle or building learner modules.

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

Treat `--missing-only` as deterministic, read-only inventory only. Resolve the
roster with `load_active_manifest()` and `load_manifest_track()` from
`scripts.orchestration.curriculum_readiness`, evaluate the whole active track
locally, and return failed or stale candidates in manifest order. Do not mutate,
call a model, silently select an unbounded work scope, or scan another track.
Stop after the inventory; actual preparation requires a new explicit one-target
invocation or finite homogeneous packet with `--limit`.

## Evaluate before acting

Run the canonical evaluator separately for every target:

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

Use the result cell by cell. `plan` and `prepare` are both preparation-scope
actions, but each failed requirement keeps its declared owner:

- Route a failed `plan` requirement through the registered plan owner,
  then resume this exact preparation scope; do not absorb or duplicate its
  plan-review and approval policy.
- Act directly only on a failed `requirements[]` item owned by `preparation`, or
  on the preparation-owned `PREPARATION_IDENTITY_DRIFT` finding.
- When a built result has `next_action: prepare` only because
  `PREPARATION_IDENTITY_MISSING` is owned by `audit_tooling`, return the typed
  result unchanged. Do not regenerate preparation evidence.
- Leave passing requirements unchanged. Treat an alternative option as
  complete as soon as the evaluator marks its requirement passed.
- Return `build`, `certify`, or `stop` results without performing that work. A
  partial bundle, off-manifest target, or active hold is not preparation
  authority.
- Skip current cells during a missing-only scan. Do not rebuild or recertify a
  learner bundle from this skill.

Compare SHA-256 values, never timestamps or prose summaries. Reuse prior
evidence or review only when the target, profile, manifest hash, every relevant
source path and hash, and `preparation_identity` match exactly. Treat any
mismatch as stale and reevaluate; do not copy an identity into a new result.

## Prepare with a durable review budget

Resolve failed cells with deterministic, local evidence and registered
validators before any model work. Reuse already passing artifacts by exact
hash. Use a model only for semantic synthesis or judgment that the failed cell
actually requires, and keep all work inside the admitted target or homogeneous
packet.

For model-assisted preparation, enforce one shared budget for the exact scope:

1. Before every review dispatch, persist conservative budget evidence in the
   invoking task or controller's existing durable progress ledger or issue
   receipt. Key it to the ordered exact scope and current
   `preparation_identity` values; record calls already spent, count the pending
   dispatch as spent, and set its verdict to pending before dispatch. Update the
   same receipt with the returned verdict.
2. Consolidate the changed preparation evidence and run one semantic review.
   If it fails, consolidate all findings into one correction pass and run at
   most one final semantic review. Preserve the call count when identities
   change after correction; a new context, task, provider, or model never resets
   the scope budget.
3. On resume, load that receipt before model work. If prior model work is
   indicated but the receipt is missing or ambiguous, fail closed to reviewed
   HOLD for every affected still-failing target instead of restarting review 1.
   Never start a third review or singleton review loop.

Record each active reviewed HOLD at
`curriculum/l2-uk-en/<track>/promotion-evidence.yaml` under the target slug's
`hold` entry. Require `status: pass`, `active: true`, `reviewer_family`, `date`,
`evidence_url` with HTTP(S), `reason`, `owner`, `checked_evidence`, and
`unblock_condition`. When a packet exhausts its final review, write the HOLD for
every still-failing admitted target in manifest order, then rerun readiness for
each. Require `PREPARATION_HOLD_ACTIVE` and exact `next_action: stop`; otherwise
fail closed. Never represent a HOLD with a new schema, sidecar, or free-form
status.

## Return the canonical handoff

Rerun the evaluator after every preparation mutation and after recording a
HOLD. Return its validated result unchanged, including
`preparation_identity`, `consumed_preparation_identity`, `requirements`,
`findings`, `sources`, and the exact `next_action`. For a packet, return one
existing typed result per manifest-ordered target; do not invent a packet
result schema.

In standalone use, report the exact result and end at its `next_action`. When
called by `$curriculum-lifecycle`, return the same result and action to that
caller, which owns the next transition without reacquisition. Preparation never
calls lifecycle in either mode.

On resume, reuse the exact target scope, typed results, identities, hashes, and
durable review receipt. Run canonical readiness first, discard stale cells, and
continue only unfinished preparation-owned work. Treat every active-hold target
as exhausted and never re-reviewable; an exhausted scope resumes at reviewed
HOLD, not at a fresh review.
