# Recipes and tool quirks

Each entry is a way of working an earlier CTO session settled on. Rules that govern the same
ground (merge policy, recovery, cleanup) stay authoritative in
`agents_extensions/shared/rules/workflow.md` and `docs/runbooks/ci-gate.md`. Operational
recipes for the CTO seat are kept in the private infra repository (docs/cto/operations.md).

## Primary checkout

The primary checkout is read-only. Write work happens in a dispatch worktree or the session
scratchpad.

## GitHub writes

Publish GitHub writes with `.venv/bin/python -m scripts.publish` (workflow.md); raw `gh` is
for reads. Prefer `--body-file` over `--body` for anything with quotes or markdown.

## Merging

Enqueue with `.venv/bin/python -m scripts.publish pr-merge --number <N> --match-head <sha>`
only after exact-head cross-family APPROVE and green CI on that head (workflow.md § Merge
policy). The merge-queue keeper usually enqueues approved green PRs on its own; check its
log before enqueueing by hand.

## Recording reviews

For branch-pinned reviews in this repo, publish the verdict with
`.venv/bin/python -m scripts.review.record_cf_verdict --task-id <id> --pr <n>` after the
reviewer exits.

## Reviewer seating

Resolve code and infra reviewers with `.venv/bin/python -m scripts.review.closeout_cli
resolve-reviewer --author-model <model> --review-profile code --risk <risk>` and run the
invocation it returns. When a seat is near its budget cap, take the next eligible candidate
the resolver returns. Never park work waiting for a quota reset.

## CI failure on an unrelated diff

One failure on a run whose diff does not touch the failing code is a service or environment
problem: one rerun with recorded evidence, never an issue or a fix task (core.md P4). The
procedure is in `docs/runbooks/ci-gate.md`.

## Reap before re-dispatch

A finished task still holds its worktree and branch lease. Before dispatching the same
branch again (a fix round), reap it:

```bash
.venv/bin/python -m scripts.fleet.post_task_reap --task-id <id>          # dry run, read the receipt
.venv/bin/python -m scripts.fleet.post_task_reap --task-id <id> --apply
```

A SKIPPED row is not a disposition: find the reason (live process, unpushed work) and
resolve it safely; never force.

## Claude headless calls

`claude -p --bare` skips OAuth and the keychain and authenticates only with an API key; on a
subscription login it fails with "Not logged in". For subscription seats use the fleet
adapter (`delegate.py dispatch --agent claude`) or plain `claude -p`. Reserve `--bare` for
explicit API-key runs.

## Dispatch helpers

Repeated dispatches (a review per PR, a fix round per PR) belong in a scratch Python script
that builds each `delegate.py dispatch` argv from a table and logs stdout and stderr per
task; grep the log for `run_nonce=`, `SUBSTITUTE` and `queued behind` to learn the nonce,
any seat substitution, and queueing. Classify research dimensions for every dispatch
(`--research-role`, `--research-task-family`, `--research-owned-path`) per the
CLAUDE.md research-registry duty. A dispatch whose `--owned-path` overlaps a live worker's
owned path waits until that worker releases it; give exact file paths to avoid serializing
unrelated jobs.
