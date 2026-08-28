# Decision: Atlas lane must not leave green PRs sitting

- **Date:** 2026-07-28
- **Status:** accepted (operator GO 2026-07-28; hard rule)
- **Scope:** Atlas lane drivers and all track drivers

## Decision

When a lane-owned pull request has a green CI Gate and is not a draft:

1. In the same session—or the next cycle while CI is settling—dispatch
   cross-family review via
   `.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-<lane> - --task-id review-<N> --type review`
   (shielded `review-pr` is RETIRED).
2. Wait for that review task to reach a terminal state. On packaging failure,
   re-fire or fix that day; do not abandon it. Post the verdict on the PR.
3. On **APPROVE** (or non-blocking nits only), immediately arm
   `gh pr merge --auto --squash`. Do **not** pass `--delete-branch` while this
   repo uses a merge queue (delete the remote branch only after `MERGED`).
   Green, reviewed PRs do not remain idle for later action.
4. A green, cross-family-passed PR that is not auto-merged for more than one
   hour is a utilization failure. Its owning lane must arm the merge or post a
   blocker naming an owner and ETA.
5. Grok never self-seals cross-family review, but it still owns driving the
   review path and arming the merge.
6. Holding a green PR for “advisor polish later” requires either a plan-draft
   merge with a follow-up issue for nits, or an explicit operator-hold comment
   on the PR. Silence is not a hold.

## Consequences

- Formal review, verdict publication, and auto-merge arming become one
  closeout sequence for eligible lane-owned PRs.
- A review transport failure is an active same-day delivery problem, not a
  reason to leave a green PR indefinitely unattended.
- The one-hour bound aligns the lane responsibility with the existing
  out-of-lane sweep threshold while preserving explicit ownership.

## Non-decisions

- This decision does not permit a worker to self-enable auto-merge; the owning
  lane still acts only after the cross-family review gate passes.
- It does not change the existing requirement that an explicit operator hold
  can pause merge activity.

## Evidence

- Operator GO, 2026-07-28.
- Existing merge policy and formal review workflow in
  [How We Work](../best-practices/agent-bridge.md).
