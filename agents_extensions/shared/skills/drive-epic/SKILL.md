---
name: drive-epic
description: Drive one explicitly assigned epic or track through Fleet Comms. For the core fresh lesson-based build (#7994) see §0d. Use track-completion for a single V7 module on a track that still uses V7.
effort: xhigh
---

# Drive an epic lane

For GPT-6.1 Sol (`gpt-6.1-sol`), use `high`, including advisory and
escalation turns. This overrides the shared effort above for Sol only;
other providers retain their effort rules and explicit overrides.

You drive **one epic or track lane** (`SESSION_EPIC` is set). You are **not** the main
orchestrator. You own the lane's judgment: what is wrong, what is next, which model and
harness should do it, whether the artifact actually worked, and what residual remains.
Dispatch lets the fleet do the volume; it is not a substitute for thinking. Use
established best practice (`docs/best-practices/`), fix the root cause, and decide
in-scope calls yourself. You are not a designated approver and not the cross-family
(CF) reviewer of record for work you drove, but you read the review and the diff before
you merge. Unused paid quota is waste (§2c); manufactured work is a defect. Judgment is
not implementation: seat no-solo rules still bind.

This skill teaches the method, never the roster. Who sits in which lane, which model fits
which task, and the current width are live data. Read them fresh, never from memory:
`GET http://127.0.0.1:8765/api/rules` (routing, review seats, cross-family pairing),
`scripts/config/model_catalog.yaml` (quality floors, peer tiers), and
`docs/best-practices/agent-activity-matrix.md` §2/§2b. Every claim you make (a lane, a cap,
a Ukrainian word, stress or morphology fact, a gate status, a count, a worker's state)
comes from tool output in this turn; if it does not, stop and run the tool.

**Issue filing belongs to the CTO.** You do not open GitHub issues. Report findings to
the CTO through Fleet Comms; the CTO opens, folds or drops them. Add no test file or test
case unless the CTO approves that specific test, and never brief a worker for a reproducer,
a regression test or repeated runs.

**Evidence hygiene.** Every timestamp in reports, issue comments, receipts, and
handoffs comes from `date -u`, never from memory or a clock guess.

## Definition of done — check this before any status sentence

A dispatch, a branch, an open PR, green CI, or "Next:" is **not** done. The driver merges
its own lane's PRs; never ask the operator to merge. Source: `/api/rules` →
`operator-expectations.md` §3a.

**Deliver every change with the delivery skills:** `full-send` (you, to MERGED and closeout),
`full-stop` (workers, or ready-to-merge for another driver), `review-loop` (review rounds and
the budget), entered through `takeover` or `modernize` when the work is inherited or old.
Per PR, `full-send` is the ordered checklist and `workflow.md` § Merge policy holds the gates.
A PR may open before approval so CI runs; it is done only at `MERGED` with a clean
`merge_closeout` receipt and every linked issue disposed of.

Per turn and at session end:

- [ ] No worktree of a settled dispatch remains:
      `.venv/bin/python -m scripts.orchestration.reap_worktrees apply --terminal-dispatches --merged --preserve-then-reap`.
- [ ] `.venv/bin/python -m scripts.hygiene.branch_sweep --json` reviewed and its
      proven-safe deletions applied (`--apply`), then `git fetch --prune`.
- [ ] Every SKIPPED row from the reaper or `branch_sweep` gets a decision: remove it
      safely or record a verified reason to keep it (a live process, a running task,
      unpushed or unique work). Exit 0 with skips is not done. Never force removal.
- [ ] Remove a review worktree as soon as its verdict is posted and the reviewer process
      has exited; superseded review checkouts never wait for merge.
- [ ] No issue in the lane has a merged PR and no disposition.
- [ ] Every live worker has an armed wait, and no finished worker is waiting for the
      operator to ask about it.
- [ ] The residual count is quoted from a tool; a residual above zero has a next
      dispatch this session (§2a).

An issue is never kept open as a running log; put logs in the CTO's issue.

Git hygiene always holds: the primary checkout stays on `main` and is read-only; edits,
commits, and PRs happen only in `.worktrees/dispatch/<agent>/<task>/`; every commit has an
`X-Agent` trailer; never push to `main`.

## The loop — run it every cycle

**Inbox drain** (at §0a, §4a, §5a, and §8a below). The live loop itself — never a
detached `process-*` or `ask-*` worker — reads and applies every message marked `unread`
or `read-but-not-live-consumed`, then records that consumption:

```bash
.venv/bin/python -m scripts.ai_agent_bridge inbox --for "$SESSION_HANDOFF_AGENT"
.venv/bin/python -m scripts.ai_agent_bridge ack --consumed-by-live-driver <message-id> [<message-id> ...]
```

Never use a plain `ack` for these: it also records one-shot or headless processing and is
not delivery proof for the live driver.

Record every order, in-flight task with its full run nonce, blocker, decision and
next action as a lane tracker item throughout the cycle. Use `add`, `note`,
`evidence` and `status`; never delete items. Done requires evidence, and dropped
requires an operator reference. The item lifecycle is in
[handoff](references/handoff.md#record-work-throughout-the-cycle).

1. **§0 Orient.** Run the cold-start board, lean orient, the Work API projection and your
   stream's `next` list, and `.venv/bin/python -m scripts.fleet_comms plane-status`. The launcher already holds your lease; never
   claim it. Read open lane work with `lu-driver-state render --lane <lane>` and
   `lu-driver-state check --lane <lane>`. The database is the lane's handoff;
   `DRIVER-STATE.md` is only a pointer. Detail and the optional §0b inbox watcher:
   [orient](references/orient.md).
2. **§0a Inbox drain — cycle start.** A CTO demand (an URGENT delivery order or a
   blocker-report request) outranks all other lane work. Answer within its deadline, by
   default 10 minutes, with one blocker line per named deliverable
   ([lane-report](references/lane-report.md)). Then work the named
   deliverables and their blockers first, until they land or the CTO releases them. Fix
   any blocker you can fix; name the owner of any you cannot. Other ready work may fill
   only the worker slots the demanded deliverables cannot use. Report again on every
   change.
3. **§0c / §0d Epic-specific rules.** Hramatka (#4542) and the core fresh build (#7994)
   add binding rules; read [epic-specific](references/epic-specific.md) before acting on
   those epics.
4. **§1 Topology and metrics.** Query `fleet_comms metrics`, `backlog`, and
   `dead-letters`; never hold fleet state in context (orient.md).
5. **§2 Pick the next action and dispose every open issue** (§2-epic): each one is in
   flight, dispatched now, or on a named §2c hold. Silence is a defect. Before dispatching
   for an issue, look for a sibling PR (`gh pr list --state all --search "<issue>"`). No
   fabricated done (§2a); no idle paid lane while ready work exists (§2c). While CF or CI
   runs, dispatch the next ready item or record a §2c code in the same turn:
   [queue-and-capacity](references/queue-and-capacity.md).
6. **§3 Route** by model and harness fit from live capacity (`routing-budget`,
   `capacity_pick`, usage pace). Write a ROUTING_CARD_V1 before every implement dispatch;
   no card, no dispatch (§3-routing). Substantive phase or epic prompts first pass §3a
   pre-dispatch outcome adequacy: [routing-and-dispatch](references/routing-and-dispatch.md).
7. **§4a Inbox drain — immediately before dispatch.** Apply every message before the
   launch.
8. **§4 Dispatch** only when the task card and dispatch preflight are both green; chat
   "ready" is not DoR. Use explicit provider/model selection, research metadata, and `--owned-path`.
9. **§5 Settle.** Arm `dispatch.py wait <task-id>` (or the Monitor tool) in the same turn
   as the dispatch. State a worker's status only after `dispatch.py status <task-id>` in
   this turn, and record its task ID, full run nonce, status, and branch head in its
   tracker item. When the wait returns, act on the result. After a terminal status,
   run `post_task_reap`.
10. **§5a Inbox drain — after settle.**
11. **§6 Cross-family review, §7 merge, §7a closeout, §7-rollout proof** — through the
    delivery skills named in the Definition of done above. The mechanics (review commands,
    merge-queue status, queue kicks, red main, junit diagnosis, launcher tests, rollout
    authority):
    [review-merge-cleanup](references/review-merge-cleanup.md).
12. **§8a Inbox drain — before handoff.**
13. **§8 Handoff.** Reconcile the lane tracker and add one `handoff_note` item.
    Keep `DRIVER-STATE.md` under 4 KB as a pointer with pinned provider facts and the
    render/check instructions. Preserve the Entire dual-write and Fleet receipt:
    [handoff](references/handoff.md).

Write the brief for a new multi-PR outcome as a [decision report](references/decision-report.md).

Report to the CTO hourly, and every 30 minutes while an operator-priority outcome is open, in the [lane-report](references/lane-report.md) format.

Seat-specific adjustments for your model and for the seats you route to:
[model-deltas](references/model-deltas.md).
Sol drivers follow its Sol driver row for plain messages, bounded reads and output, and launcher-held authority with current hydration.

## Escalate — do NOT decide these solo

Seek **Opus 5.5 / Sol 6.1** for review, critique and design input. Route the decisions
below for approval to the **operator**, or to **designated approval**: `claude-opus-5-5` and
`gpt-6.1-sol` agree; when one of them authored the proposal, the other's approval completes
it, and a proposal by any other agent needs both; if they disagree, the operator decides
(#9583, #9616). Never resolve them from the loop:

1. Any **architecture, layout, or process** change.
2. A **contested CF verdict** (reviewer and author disagree, or two reviewers split).
3. A **fragile fix**: challenge the premise and root-cause it, then escalate the design if
   the right layer is unclear.
4. A **high-risk route** that would trip `risk_quality_floor` in `model_catalog.yaml`.
5. A **repo-wide safety** interruption of another lane (generated artifacts, linter or
   Python-version bumps, cross-track architecture conflict).
6. A **production, Pages, or public cutover** without a present-tense operator GO; HA,
   Patroni, new-VPS, or fenced cutovers; host access and security configuration
   (§7-rollout).

Enforce the risk floor on yourself, not only on the work you dispatch. Passing gates is
necessary, not sufficient: verify the real artifact renders or runs before "ready".

## This skill is NOT

- A replacement for the served rules (`/api/rules`); it points to them and never restates
  the live roster.
- The main-orchestrator cold start (that has its own SessionStart hook and handoff chain).
- A single-module writer (V7 module: `$track-completion`; core fresh build: §0d).
- A second curriculum orchestrator skill; do not fork it.
- Authority to flip the fleet-comms plane, self-merge a fleet-wide process change, or
  self-review work you dispatched.
