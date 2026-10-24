# Recipes and tool quirks

Ways of working earlier CTO sessions settled on. Each procedure lives with its owner; this
file only points there and adds what the CTO seat learned on top.

## Writes and merging

- Publishing and landing follow `agents_extensions/shared/rules/workflow.md` (§ Public
  GitHub publishing, § Merge policy); CI recovery follows `docs/runbooks/ci-gate.md`.
- The merge-queue keeper usually enqueues on its own; check its log before enqueueing by
  hand.

## Reviews

Seat, run and record every code or infra review with the `local-code-review` skill, which owns reviewer resolution.
Load that skill before seating a review; a copied dispatch command skips its steps. After the
reviewer exits, publish the verdict with `scripts/review/record_cf_verdict.py`. A review
dispatch alone publishes nothing, and the merge-queue keeper waits for the published verdict.

## Reap before re-dispatch

A finished task holds its worktree and branch lease, so reap it before dispatching the same
branch again (`workflow.md` § Post-merge cleanup, `docs/runbooks/worktree-cleanup.md`).

## Dispatch helpers

Record each new in-flight task with `lu-driver-state add --lane cto --kind inflight`, its
owner and done condition. Attach its task ID with `link <id> task <task-id>` and record the
FULL run nonce with `note <id> <text>` so the tracker handoff can re-arm its wait.

Repeated dispatches belong in a scratch Python script that builds each
`delegate.py dispatch` argv from a table and logs stdout and stderr per task; grep the log
for `run_nonce=`, `SUBSTITUTE` and `queued behind`. An `--owned-path` overlapping a live
worker's waits for its release; give exact file paths so unrelated jobs do not serialize.
