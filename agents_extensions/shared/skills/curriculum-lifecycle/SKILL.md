---
name: curriculum-lifecycle
description: Run or resume the manifest-derived curriculum lifecycle for one active track, using the coordinator for ordered waves and the canonical track-completion engine for exactly one acquired module at a time.
---

# Curriculum lifecycle

Keep the operator request short:

```text
Use $curriculum-lifecycle for folk.
Use $curriculum-lifecycle for c1, scope unbuilt.
Resume $curriculum-lifecycle for bio.
```

This skill is the track-level entry point. It composes the deterministic
coordinator with `$track-completion`; it does not reimplement readiness,
building, certification, review, integration, or publication policy. Derive
active tracks and order only from `curriculum/l2-uk-en/curriculum.yaml`.

## Start or resume

1. Satisfy the repository issue, stream, worktree, research-classification,
   pending-decision, and quota/health preflight before mutation. Learner changes
   belong to the target track's stream epic, not the shared infrastructure epic.
2. For a new run, map the requested selector to one of `all`, `built`,
   `unbuilt`, `stale`, or `one`, then start exactly one manifest-backed run:

   ```bash
   .venv/bin/python scripts/orchestration/curriculum_coordinator.py start \
     --track <track> --owner <agent/task> --scope <scope> \
     [--module <slug>] [--start <slug-or-position>] \
     [--end <slug-or-position>] [--wave-size <n>]
   ```

   Preserve the returned `run_id` and ledger path. Do not create a replacement
   run to bypass a lease, health pause, or manifest drift.
3. Resume only the exact recorded run:

   ```bash
   .venv/bin/python scripts/orchestration/curriculum_coordinator.py resume \
     --run-id <run-id> --owner <agent/task>
   ```

   If manifest authority changed, stop and use the coordinator's explicit
   adjudication path before starting a fresh run. Never migrate old state by
   hand.

## Process one acquired module

1. Acquire the next prerequisite-safe module. The coordinator pauses without
   mutation when its fresh health/capability gate is unavailable:

   ```bash
   .venv/bin/python scripts/orchestration/curriculum_coordinator.py acquire-next \
     --run-id <run-id> --owner <agent/task>
   ```

2. Resolve the acquired track's exact registered semantic profile from the
   manifest. Put the typed context in a gitignored runtime JSON file; never add
   free-form prompt prose to a profile:

   ```bash
   .venv/bin/python scripts/orchestration/prompt_contracts.py resolve-track \
     --track <track> --context <runtime-context.json>
   ```

   Preserve the returned prompt/source identity with the phase evidence. A
   retired or unknown track, stale selector, family mismatch, missing fragment,
   or unresolved input is a fail-closed configuration defect.
3. Follow `$track-completion` completely for the acquired `track/slug`. Reuse
   its exact ledger on resume. It owns plan review, build/recovery, read-only
   `$post-build-review`, repair routing, reviewer-instability handling,
   independent review, PR/CI/merge, publication evidence, and cleanup.
4. Record the module outcome only after `$track-completion` reaches a proven
   terminal disposition:

   ```bash
   .venv/bin/python scripts/orchestration/curriculum_coordinator.py record-module \
     --run-id <run-id> --owner <agent/task> --module <slug> \
     --disposition <complete|no-change|blocked> \
     --integration-json '<canonical integration evidence JSON>'
   ```

   `complete` requires issue, aligned dispatch worktree/branch, PR, merge SHA,
   review/CI evidence, and completed cleanup. `no-change` must not fabricate an
   issue or PR. `blocked` must record the genuine owner and next action.
5. Repeat acquisition serially until the coordinator reports `complete`.
   Module-at-a-time mutation remains mandatory; a wave groups health and review
   capacity but does not authorize concurrent learner writes.

## Legacy boundary

Files under `docs/prompts/orchestrators` are hash-frozen evaluation or reference
material, not completion authority. Their migration registry points to this
skill and the code/config/prompt/policy owners. Do not paste an old suite into a
production run, delete a retained oracle, or restore a retired track list.
