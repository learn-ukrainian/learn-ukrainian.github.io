---
name: full-stop
description: Do the full-send work on a change but stop with the PR ready to merge, never merging it. Use when told "full stop", when a brief says to stop at ready-to-merge, or when the merge belongs to another driver.
argument-hint: "[pr <number> | issue <number> | branch <name>]"
---

# Full stop

Run the same work as [full-send](../full-send/SKILL.md) steps 1 to 7, then hand the PR over
ready to merge. Anyone may run this skill, including workers. Its terminal is `ready`, never
`merge`.

Recipes run with the primary checkout's interpreter, resolved once
([delivery](../full-send/references/delivery.md#interpreter)):

```bash
PY="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")/.venv/bin/python"
```

## Never merge

Never merge, enqueue, arm auto-merge, push to `main`, bypass protection, or ask another agent
to do any of these. You may commit, push and rebase this task's own branch, using
`--force-with-lease=<branch>:<observed head>` after a rebase.

Everything before the merge stays yours: a worker runs `review-loop` itself, and the resolver
picks its reviewer (rules core P1). Only the enqueue and what follows belong to the receiving
driver.

## Protect the PR before any work

On an existing PR, before the first edit:

```bash
"$PY" -m scripts.publish pr-edit --number "$PR" --add-labels hold
"$PY" -m scripts.publish pr-disarm --number "$PR"
gh pr view "$PR" --json id,labels,autoMergeRequest
"$PY" -m scripts.gh_merge_queue_status "$PR" --json
"$PY" -m scripts.publish pr-dequeue --node-id "$PR_NODE_ID"   # only if queued
```

`pr-dequeue` takes the PR's node id (`id` above), not its number. Verify each result: the
`hold` label is present, `autoMergeRequest` is null, and the PR is not queued. The merge-queue
keeper skips a PR with a `hold` label or a `[hold]` title. Re-check before every push and at
hand-off. If automatic landing cannot be prevented, stop with `BLOCKED` before doing any work.

A new PR has no labels at creation (`pr-create` takes none), so open it with a `[hold]` title,
then add the `hold` label and verify it before any approval is recorded:

```bash
"$PY" -m scripts.publish pr-create --title "[hold] $TITLE" --body-file "$BODY" \
  --base main --head "$BRANCH"
"$PY" -m scripts.publish pr-edit --number "$PR" --add-labels hold
```

## Stop at the gate

Check the gate in [delivery](../full-send/references/delivery.md#the-gate) on the live head.
Fetch the base, then read the live PR's state, head, base, checks, reviews and mergeability.
`READY_TO_MERGE` means all of these hold on the current head: a recorded exact-head APPROVE,
same-head green PR CI Gate (the full suite), proof complete, and protection verified. The future merge-group
CI is not yet proven; say so.

End in exactly one of these states, naming the receiving driver:

- `READY_TO_MERGE` — the gate passes; the PR is open, unmerged and protected.
- `WAITING_ON <named approval>` — only that approval remains; confirm it is the real blocker.
- `BLOCKED <reason>` — what blocks readiness, what you tried, and what is needed.
- `ALREADY_MERGED_EXTERNALLY` — someone else merged it; report the merge SHA.

Ready is never reported as delivered. The receiving driver removes the hold and lands it with
`full-send`. Closing a PR is a driver act. Closing an issue as duplicate, obsolete or not
planned is the CTO's (rules core P4).

## Report

The terminal state, PR, final head, protection state (label, auto-merge, queue), proof,
reviewer verdict with model, family and harness, the ledger, remaining risks, and the receiving
driver.

Learned from tstack's `full-stop` skill (MIT, Theo Browne); the text is our own.
