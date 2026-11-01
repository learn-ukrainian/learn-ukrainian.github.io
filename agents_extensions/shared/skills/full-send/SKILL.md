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
   An approved extra path uses the request-and-grant exchange below, in the same task and worktree.
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
   record, issue or PR, or send the work back to the entry stage. Never guess. A successor to
   an existing PR first accepts it with `pr_ownership accept`; a refusal means another task may
   still own it, so stop ([pr-watch](references/pr-watch.md#owner-changes)).
2. **Make the smallest change that achieves the outcome**, in a dispatch worktree on a branch,
   never on `main`. Implementation and fixes go to the authoring lane: a worker makes them
   itself, a driver dispatches them (rules core P1). Fix the case that happened, not every case
   that could.
3. **Prove it** ([delivery](references/delivery.md#proof)): reproduce, fix, the same check
   passes; behaviour proof for a user-visible surface. Add a test only with the CTO's approval
   of that specific test.
4. **Open or update the PR and get green CI first** ([pr-body](references/pr-body.md)).
   Push the branch and open a non-draft PR so CI runs on the exact head. PR CI runs
   Frontend and the affected tests (changed tests, tests that import or read changed files,
   the guards and the repository invariants); the full pytest suite runs only in merge-group,
   nightly and manual runs, so a failure in the merge group can still eject the PR. An open PR is not approval.

   ```bash
   "$PY" -m scripts.publish pr-create --title "$TITLE" --body-file "$BODY" \
     --base main --head "$BRANCH"
   ```

   Wait for the `CI Gate` check on that head to finish (`gh pr checks "$PR"`; see
   [pr-watch](references/pr-watch.md)). Fix a red gate through the authoring lane first;
   every fix is a new head and restarts the wait. **No budgeted review round starts until
   the `CI Gate` is green on the head to be reviewed**: a round spent on a head that then
   changes for a CI failure is wasted budget.
   Before step 5, the author may optionally run the DeepSeek author pre-check
   ([below](#optional-deepseek-author-pre-check-ds-precheck-1101)) on the pinned green head.
5. **Review with `review-loop`**, which you run yourself, at that green head. It resolves
   the reviewer live (never from a family that authored the branch), dispatches it at the
   exact pushed head, keeps the budget and the ledger, and records the verdict. A fix that
   moves the head returns to step 4 for green CI before the next round.
   Include the author task's `owned_path_grants` and `owned_path_grants_used` entries in the
   review-of-record brief, reading the current task record even when the author is still
   running. The reviewer checks each grant's paths against its reason and approval reference;
   a running author has no settlement usage list yet, so include all grants.
6. **Watch it** ([pr-watch](references/pr-watch.md)): fix real findings and CI failures
   through the authoring lane, prove each fix, and run a `review-loop` delta for every new
   head once its CI Gate is green. One evidenced rerun for an unrelated CI failure, never more.
7. **Check the gate on the live head** ([delivery](references/delivery.md#the-gate)):

   ```bash
   gh pr view "$PR" --json state,isDraft,headRefOid,mergeable,mergeStateStatus,autoMergeRequest
   ```

   `headRefOid` must equal the head of the recorded APPROVE and of the green PR CI Gate.
   Send follow-ups to the CTO through Fleet Comms
   (`"$PY" -m scripts.fleet_comms channel publish … --recipient claude-cto`; the CTO's one durable recipient, never a `claude-cto-<id>` name).
8. **Drain the inbox, then enqueue** at the approved head. The merge-queue keeper may already
   have queued it: check `"$PY" -m scripts.gh_merge_queue_status "$PR" --json` first.

   ```bash
   "$PY" -m scripts.publish pr-merge --number "$PR" --match-head "$HEAD_SHA"
   ```

   Never `--auto`, `--delete-branch` or `--admin`. Queued is not merged. A PR the CTO
   labelled `merge-priority` after its exact-head approval enqueues at the front of the
   queue on its own (`workflow.md` § Merge policy, priority line); never apply that label yourself.
9. **Confirm `MERGED`** and the merge SHA: `gh pr view "$PR" --json state,mergeCommit`. If the
   queue ejects the PR, follow the kick recipe in [pr-watch](references/pr-watch.md). If
   waiting in the queue is the only step left and the integration owner has accepted queue
   custody, `pr_ownership queue-exit` may release you. Then report `QUEUED_UNDER_CUSTODY`, and
   the custodian does steps 9 to 11 ([pr-watch](references/pr-watch.md#queue-custody)).
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

## Optional DeepSeek author pre-check (DS-PRECHECK-1101)

An optional, explicitly chosen, read-only DeepSeek pre-check may be run by the author before the
first review of record, at most **one per PR lineage**.

- **Scope:** only for low or medium risk **public** code. Never on private repositories, high or
  critical risk, security-class paths, or Ukrainian content. Everything sent to it must be public
  and free of secrets.
- **Trigger:** nothing invokes it automatically, it has no retries, and it does not repeat after
  the head changes. It runs on a pinned pushed head before the first review of record.
- **Credit check:** execution is skipped when remaining DeepSeek credit is unknown or exhausted.
  Query the Monitor routing-budget endpoint (`http://127.0.0.1:8765/api/state/routing-budget`,
  field `api_accounts.deepseek.total_balance`); skip when the field is missing or below the
  credit floor of $0.10.
- **Execution:** run with a hard timeout of 900 seconds:

  ```bash
  "$PY" scripts/dispatch.py dispatch \
    --agent opencode --model deepseek-v4.1-flash --mode read-only \
    --hard-timeout 900 --worktree --task-id "$PRECHECK_TASK" \
    --prompt-file "$PRECHECK_PROMPT" --branch "$BRANCH" --pinned-head "$HEAD_SHA" --pr "$PR"
  ```

- **Findings and status:** findings go only to the author. A failed run never blocks review. Any
  usable findings it returned need a disposition in the PR body (fixed, or rejected with a reason),
  and confirmed defects follow the existing review-loop severity policy.
- **Non-record status:** it is never a review of record and never satisfies or waives the
  cross-family gate. No change to reviewer choice, risk floors, or round budgets.

## Stop and escalate

Stop, and report `BLOCKED <reason>`, when: the proof cannot be obtained; the recorder's
`budget-check` refuses the next review round, or a dispute is unresolved after two replies
(`review-loop`; a base merge, a CI fix or a conflict resolution after approval is not a stop
while `budget-check` admits it); a breaker trips; ownership
or stream membership is lost; the change's own checks fail a second time, or CI fails for an
unclear reason (an evidenced infrastructure failure uses the head's one rerun and then escalates,
[pr-watch](references/pr-watch.md#failing-ci)); another PR makes
this one obsolete; or the next step is outside your authority or your brief. Escalate to the
CTO and, for decisions in rules core P6, to the advisors. Reach the operator only for the
operator-only list and for a review dispute unresolved after two replies.

## Ask the CTO and wait for the answer

For an approved edit outside the original owned paths, send the exact repository-relative
paths, task id, run nonce, reason and approval reference to `claude-cto` through this exchange.
The coordinator records the grant, then replies to the task-ID recipient with the JSON receipt:

```bash
/abs/path/.venv/bin/python scripts/dispatch.py grant-paths TASK --run-nonce NONCE \
  --owned-path tests/fixture.py --reason 'Approved fixture change' --approval-ref message-id
```

After claiming, reading and acknowledging the reply, confirm that its grant id, task id and
nonce match the durable task record, then retry the commit or push in the same session.
A Fleet reply alone grants no scope. Identical requests return the same grant id. Grants
are refused for self/descendant callers, sealed envelopes, read-only, terminal or settling
tasks, invalid paths and sparse-excluded trees. Request a successor from the coordinator
when a grant is refused; never widen the record yourself or bypass a hook.

A dispatched worker's Fleet recipient is its task id, `$LEARN_UKRAINIAN_DISPATCH_TASK_ID`; the
coordinator publishes the reply there, and claiming needs no registered seat. Use it as the
`--worker-id` too. Put the question and that recipient name in the message to `claude-cto`
(literal interpreter path, as above):

```bash
printf '%s\n' "question: <one decision, the options, your recommendation>; reply to: $LEARN_UKRAINIAN_DISPATCH_TASK_ID" |
  /abs/path/.venv/bin/python -m scripts.fleet_comms channel publish cto - \
    --sender "$LEARN_UKRAINIAN_DISPATCH_TASK_ID" --source cto --recipient claude-cto \
    --idempotency-key "ask-$LEARN_UKRAINIAN_DISPATCH_TASK_ID-<n>"
```

Then wait, for at most 30 minutes, one Bash call per minute (`sleep 60`, then claim). Exit 1 means no
reply yet:

```bash
/abs/path/.venv/bin/python -m scripts.fleet_comms deliveries claim \
  --recipient "$LEARN_UKRAINIAN_DISPATCH_TASK_ID" --worker-id "$LEARN_UKRAINIAN_DISPATCH_TASK_ID"
```

On a claim, read the reply with its `delivery_id` and `fence_token`, apply it, then acknowledge:

```bash
/abs/path/.venv/bin/python -m scripts.fleet_comms deliveries read "<delivery_id>" \
  --worker-id "$LEARN_UKRAINIAN_DISPATCH_TASK_ID" --fence-token "<fence_token>"
/abs/path/.venv/bin/python -m scripts.fleet_comms deliveries ack "<delivery_id>" \
  --worker-id "$LEARN_UKRAINIAN_DISPATCH_TASK_ID" --fence-token "<fence_token>"
```

If a lease expires before you finish, claim again. If nothing arrives in time, end with
`BLOCKED waiting on <the open question>` and a hand-off record ([delivery](references/delivery.md#hand-off-record))
that states the question, the branch and head, and what is done, so a successor can resume.

## Report

Lead with the outcome. Then: PR, merge SHA, the proof (commands and run ids), review rounds
against the tier with reviewer model, family and harness, the decisions you made, follow-ups
with owners, how each linked issue was disposed of, the closeout receipt, and the residual
owner or "none".

Learned from tstack's `full-send`, `babysit-pr` and `file-pr` skills (MIT, Theo Browne); the
text is our own.
