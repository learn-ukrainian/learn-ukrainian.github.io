---
name: curriculum-lifecycle
description: Run or resume the manifest-derived curriculum lifecycle for one active track, using the coordinator for ordered waves and routing each acquired module through the canonical preparation or track-completion owner.
---

# Curriculum lifecycle

Keep the operator request short:

```text
Use $curriculum-lifecycle for folk.
Use $curriculum-lifecycle for c1, scope unbuilt.
Resume $curriculum-lifecycle for bio.
```

This skill is the track-level entry point. It composes the deterministic
coordinator with `$curriculum-preparation` and `$track-completion`; it does not
reimplement readiness, preparation, building, certification, review,
integration, or publication policy. Derive active tracks and order only from
`curriculum/l2-uk-en/curriculum.yaml`.
For a normal BIO request, this is one serial workflow: the coordinator owns
manifest order, prerequisites, acquisition, deterministic resume, and the
hash-bound receipt; the acquired module's `$track-completion` ledger is the
only bounded-completion authority.

## Start or resume

1. Satisfy the repository issue, stream, worktree, research-classification,
   pending-decision, and quota/health preflight before mutation. Learner changes
   belong to the target track's stream epic, not the shared infrastructure epic.
2. For a new run, map the requested selector to one of `all`, `built`,
   `unbuilt`, `stale`, or `one`, then start exactly one manifest-backed run:

   ```bash
   .venv/bin/python scripts/orchestration/curriculum_coordinator.py start \
     --track <track> --owner <agent/task> --scope <scope> \
     --terminal-goal <merge|certify|deploy> \
     [--module <slug>] [--start <slug-or-position>] \
     [--end <slug-or-position>] [--wave-size <n>]
   ```

   Preserve the returned `run_id` and ledger path. Do not create a replacement
   run to bypass a lease, health pause, or manifest drift.
   The goal is immutable authority, not a progress label. A legacy run without
   one must use `migrate-terminal-goal` on its exact run id; never infer intent
   from `complete` or `PBR_PASS_QG_PENDING` history.
3. Resume only the exact recorded run:

   ```bash
   .venv/bin/python scripts/orchestration/curriculum_coordinator.py resume \
     --run-id <run-id> --owner <agent/task>
   ```

   If manifest authority changed, stop and use the coordinator's explicit
   adjudication path before starting a fresh run. Never migrate old state by
   hand.

   The coordinator status includes this exact `resume_command`; use it rather
   than reconstructing or replacing the run.

## Process one acquired module

1. Acquire the next prerequisite-safe module. The coordinator pauses without
   mutation when its fresh health/capability gate is unavailable:

   ```bash
   .venv/bin/python scripts/orchestration/curriculum_coordinator.py acquire-next \
     --run-id <run-id> --owner <agent/task>
   ```

2. Read the canonical readiness routing snapshot from the latest matching
   `MODULE_ACQUIRED` event in the returned ledger. Bind it to that event's
   track, slug, and attempt. Route its exact `next_action` uniformly for CORE,
   seminar, and BIO targets:

   | `next_action` | Exact next owner |
   | --- | --- |
   | `plan` | `$curriculum-preparation` |
   | `prepare` | Requirement- and identity-sensitive; resolve from the full result |
   | `build` | `$track-completion` |
   | `certify` | `$track-completion` |
   | `stop` | State- and owner-sensitive; reviewed HOLD or partial recovery |

   For `plan` or `prepare`, run the canonical evaluator once for the exact
   acquired target and use its full typed result to resolve ownership. If any
   current failed requirement is owned by `plan` or `preparation`, route those
   cells through `$curriculum-preparation`; accept its returned typed result
   without calling lifecycle recursively.

   When every current requirement passes but a built result remains `prepare`
   solely because of `PREPARATION_IDENTITY_MISSING` or
   `PREPARATION_IDENTITY_DRIFT`, hand the exact target to `$track-completion`.
   Its authoritative ledger reruns readiness with the consumed identity from
   `BUILD_RECORDED`, then either certifies or takes its existing explicit rebuild
   transition. Do not reacquire, repeat the evaluator, or loop through
   preparation. Fail closed on mixed or unknown combinations.

   For `stop`, run the canonical evaluator once to validate the full typed
   result. `PREPARATION_HOLD_ACTIVE` without a partial-bundle finding is a
   terminal reviewed HOLD: preserve its evidence, leave the acquisition in
   place, report the hold, and do not record module completion or reacquire. A
   result whose state is `partial-bundle`, contains `PARTIAL_LEARNER_BUNDLE`
   owned by `built_artifact`, and has no active HOLD goes once to
   `$track-completion` for its existing forensic recovery. Do not reacquire.
   Reject a result containing both routes, or any unknown stop combination,
   without mutation or an evaluation loop.
3. For `build`, `certify`, an identity-only `prepare` exception, or the exact
   partial-bundle `stop` exception, resolve the acquired track's registered
   semantic profile from the manifest. Put the typed context in a gitignored
   runtime JSON file; never add free-form prompt prose to a profile:

   ```bash
   .venv/bin/python scripts/orchestration/prompt_contracts.py resolve-track \
     --track <track> --context <runtime-context.json>
   ```

   Preserve the returned prompt/source identity with the phase evidence. A
   retired or unknown track, stale selector, family mismatch, missing fragment,
   or unresolved input is a fail-closed configuration defect.
4. Follow `$track-completion` completely for the acquired `track/slug`. Reuse
   its exact ledger on resume. It owns plan review, build/recovery, read-only
   `$post-build-review`, repair routing, reviewer-instability handling,
   independent review, PR/CI/merge, publication evidence, and cleanup.
5. Record the module result from its authoritative ledger. A publishable result
   is accepted only after `$track-completion` reaches `COMPLETE` for the
   coordinator's exact goal; a terminal bounded-budget blocker is recorded as
   blocked rather than left stale:

   ```bash
   .venv/bin/python scripts/orchestration/curriculum_coordinator.py record-module \
     --run-id <run-id> --owner <agent/task> --module <slug> \
     --track-ledger <track-completion-ledger> --track-run-id <module-run-id>
   ```

   Do not supply a coordinator disposition or repeat PR/worktree/cleanup
   policy. The coordinator validates the bounded run, rejects semantic evidence
   outside its model-call count, hashes the module ledger, and derives a concise
   result with elapsed time, model-call count, repair count, disposition,
   blocker, and next action. An incomplete module ledger cannot complete the
   coordinator. A migrated historical module is reacquired until its exact goal
   is proven.
6. Repeat acquisition serially until the coordinator reports `complete`.
   Module-at-a-time mutation remains mandatory; a wave groups health and review
   capacity but does not authorize concurrent learner writes.

## Legacy boundary

Files under `docs/prompts/orchestrators` are hash-frozen evaluation or reference
material, not completion authority. Their migration registry points to this
skill and the code/config/prompt/policy owners. Do not paste an old suite into a
production run, delete a retained oracle, or restore a retired track list.
