# Recipes and tool quirks

Ways of working earlier CTO sessions settled on. Merge policy, recovery and cleanup stay
authoritative in `agents_extensions/shared/rules/workflow.md` and `docs/runbooks/ci-gate.md`.

## Writes and merging

- The primary checkout is read-only; write in a dispatch worktree or the session scratchpad.
- Publish GitHub writes with `.venv/bin/python -m scripts.publish`; raw `gh` is for reads.
  Prefer `--body-file` for anything with quotes or markdown.
- Enqueue with `.venv/bin/python -m scripts.publish pr-merge --number <N> --match-head <sha>`
  only after exact-head cross-family APPROVE and green CI on that head. The merge-queue
  keeper usually enqueues on its own; check its log before enqueueing by hand.
- An unrelated CI failure gets one evidenced rerun, never an issue or fix task (core.md P4,
  `docs/runbooks/ci-gate.md`).

## Reviews

Resolve code and infra reviewers with `.venv/bin/python -m scripts.review.closeout_cli
--state-file <scratch>/review-<pr>.json resolve-reviewer --author-model <model>
--review-profile code --risk <risk>` (`--state-file` precedes the subcommand) and run the
invocation it returns. Near a budget cap, take the next eligible candidate it returns.
For branch-pinned reviews, publish the verdict after the reviewer exits with
`.venv/bin/python -m scripts.review.record_cf_verdict --task-id <id> --pr <n>`.

## Reap before re-dispatch

A finished task holds its worktree and branch lease. Before dispatching the same branch
again, reap it:

```bash
.venv/bin/python -m scripts.fleet.post_task_reap --task-id <id>          # dry run, read the receipt
.venv/bin/python -m scripts.fleet.post_task_reap --task-id <id> --apply
```

A SKIPPED row is not a disposition: find the reason (live process, unpushed work) and
resolve it safely; never force.

## Dispatch helpers

Repeated dispatches belong in a scratch Python script that builds each
`delegate.py dispatch` argv from a table and logs stdout and stderr per task; grep the log
for `run_nonce=`, `SUBSTITUTE` and `queued behind`. Classify research dimensions for every
dispatch (`--research-role`, `--research-task-family`, `--research-owned-path`; CLAUDE.md).
An `--owned-path` overlapping a live worker's waits for its release; give exact file paths
so unrelated jobs do not serialize.
