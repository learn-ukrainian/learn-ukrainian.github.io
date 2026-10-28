---
name: full-send
description: Deliver one approved change end to end, through review, PR, merge and closeout, with no human stops. Use when a worker has received a brief, or when the accountable driver of the change's stream, the integration owner or the CTO is told "full send" or must land a change; use full-stop when the brief says so.
argument-hint: "[pr <number> | issue <number> | branch <name>]"
---

# Full send

Own one change from its current state to `MERGED` with a clean closeout receipt. Nobody is
watching: decide reversible in-scope questions yourself and list them in the report. This
skill never overrides repository rules or the operator-only list (rules core P6).

The landing order is `workflow.md` § Merge policy. The hand-off record, proof rules and the
gate are in [delivery](references/delivery.md).

Recipes run with the primary checkout's interpreter, resolved once
([delivery](references/delivery.md#interpreter)):

```bash
PY="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")/.venv/bin/python"
```

A dispatched worker runs under `--permission-mode dontAsk`, which denies any command its allowlist
cannot match (https://code.claude.com/docs/en/permissions, "Compound commands"). Write the command
word literally: the absolute interpreter path, no `PY=...; $PY` prefix and no `eval`. Use the
`scripts.publish` verbs for GitHub writes. Substitute the resolved path for `"$PY"` when you
dispatch. After one denial, retry once in a literal form before you stop; a second denial is
`BLOCKED`.

## Step 0 — who may run this (fail closed)

- **The worker that receives a brief runs its chain to the end** (rules core P1): this skill;
  or `takeover` or `modernize`, then this skill; or `full-stop` when the brief says so. It lands
  only the change its brief names, within the brief's owned paths. The CTO sets the issue,
  limits and routing and handles exceptions; the worker does the rest, from review to closeout.
- **Follow-up tasks stay inside the brief's cap.** A worker may dispatch follow-up tasks only up
  to the count and within the owned paths its brief sets. Anything outside the brief goes to the
  CTO as an issue proposal through Fleet Comms; the worker never opens issues (rules core P4).
- The accountable driver of the change's stream, the integration owner and the CTO may also run
  this skill.
- **A stream driver lands only its own stream** (`workflow.md` § Merge policy, stream-scoped
  sweeps). The PR's linked issue must resolve to exactly one stream epic, and it must be yours:
  `curl -s http://127.0.0.1:8765/api/issues/streams` (built by
  `scripts.orchestration.issue_stream_audit`). No link, several links, or not yet indexed means
  out of stream: stop. Branch prefixes are author lanes, never streams. A worker's stream is
  its brief's stream; its brief may name an ordered brief id instead of an issue.
- **The integration owner and the CTO are not limited to one stream.** The integration owner
  holds cross-stream merge judgment (rules core P1; `workflow.md` § Merge policy, the
  integration-owner role), and the CTO is the cross-epic lead who lands what no brief owns (`cto` skill).
- If the next step is on the operator-only list (production or public cutover, host access,
  credentials, paid plans), stop and escalate.

## Steps

1. **Take the hand-off record** from the entry skill or brief
   ([delivery](references/delivery.md#hand-off-record)). Fill a missing field from the task
   record, issue or PR, or send the work back to the entry stage. Never guess.
2. **Make the smallest change that achieves the outcome**, in a dispatch worktree on a branch,
   never on `main`. Implementation and fixes go to the authoring lane: a worker makes them
   itself, a driver dispatches them (rules core P1). Fix the case that happened, not every case
   that could.
3. **Prove it** ([delivery](references/delivery.md#proof)): reproduce, fix, the same check
   passes; behaviour proof for a user-visible surface. Add a test only with the CTO's approval
   of that specific test.
4. **Review with `review-loop`**, which you run yourself. It resolves the reviewer live
   (never from a family that authored the branch), dispatches it at the exact pushed head,
   keeps the budget and the ledger, and records the verdict.
5. **Open or update the PR** ([pr-body](references/pr-body.md)). The PR may open before
   approval so admission CI runs (`workflow.md:195`); an open PR or green CI is not approval.

   ```bash
   "$PY" -m scripts.publish pr-create --title "$TITLE" --body-file "$BODY" \
     --base main --head "$BRANCH"
   ```

6. **Watch it** ([pr-watch](references/pr-watch.md)): fix real findings and CI failures
   through the authoring lane, prove each fix, and run a `review-loop` delta for every new
   head. One evidenced rerun for an unrelated CI failure, never more.
7. **Check the gate on the live head** ([delivery](references/delivery.md#the-gate)):

   ```bash
   gh pr view "$PR" --json state,isDraft,headRefOid,mergeable,mergeStateStatus,autoMergeRequest
   ```

   `headRefOid` must equal the head of the recorded APPROVE and of the green admission CI.
   Send follow-ups to the CTO through Fleet Comms
   (`"$PY" -m scripts.fleet_comms channel publish … --recipient claude-cto`; the CTO's one durable recipient, never a `claude-cto-<id>` name).
8. **Drain the inbox, then enqueue** at the approved head. The merge-queue keeper may already
   have queued it: check `"$PY" -m scripts.gh_merge_queue_status "$PR" --json` first.

   ```bash
   "$PY" -m scripts.publish pr-merge --number "$PR" --match-head "$HEAD_SHA"
   ```

   Never `--auto`, `--delete-branch` or `--admin`. Queued is not merged.
9. **Confirm `MERGED`** and the merge SHA: `gh pr view "$PR" --json state,mergeCommit`. If the
   queue ejects the PR, follow the kick recipe in [pr-watch](references/pr-watch.md).
10. **Close out.** After every other worker and reviewer process on the PR's worktrees has
    exited:

    ```bash
    "$PY" -m scripts.orchestration.merge_closeout "$PR" --apply
    ```

    `merge_closeout` proves no worktree still holds the PR and that its branches are gone; it
    removes no worktree. Exit 0 with a residue-free receipt is required, with one expected
    interim case: a worker runs this from its own worktree, which is still in use, so the
    receipt reports that worktree and its local branch as the only residual and the tool exits
    1. The worker reports that receipt, disposes of the linked issues (step 11), and only then
    ends its run. When its task settles, the dispatcher removes both and records
    `worktree_disposition` in the task record. The driver reads that
    disposition: once it is `removed`, the driver re-runs the command above from outside the
    tree, and its exit 0 receipt is the verified final closeout; a `retained` or `error`
    worktree is removed only after confirming its content is published (`workflow.md` §
    Post-merge cleanup). Any other residual or non-zero exit means not done: record the
    evidence and owner and resolve it safely, never with `--force`.
11. **Dispose of the linked issues.** A worker does this before it ends its run. Close each named issue as completed with evidence on the
    merged SHA, or comment what remains, its owner and what it waits on (rules core P4).

## Stop and escalate

Stop, and report `BLOCKED <reason>`, when: the proof cannot be obtained; the review budget is
exhausted or a dispute is unresolved after two replies (`review-loop`); a breaker trips; ownership
or stream membership is lost; CI fails a second time or for an unclear reason; another PR makes
this one obsolete; or the next step is outside your authority or your brief. Escalate to the
CTO and, for decisions in rules core P6, to the advisors. Reach the operator only for the
operator-only list and for a review dispute unresolved after two replies.

## Report

Lead with the outcome. Then: PR, merge SHA, the proof (commands and run ids), review rounds
against the tier with reviewer model, family and harness, the decisions you made, follow-ups
with owners, how each linked issue was disposed of, the closeout receipt, and the residual
owner or "none".

Learned from tstack's `full-send`, `babysit-pr` and `file-pr` skills (MIT, Theo Browne); the
text is our own.
