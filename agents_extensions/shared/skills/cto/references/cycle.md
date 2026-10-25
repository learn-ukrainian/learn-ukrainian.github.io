# Cycle checklist

Run every cycle while work is in flight, and before any routing, budget or status report.
Every line of a cycle report is tool output from this cycle; anything not read is unknown,
never fine.

0. **Monitoring first.** Read the firing alerts and the CTO scorecard metrics from the
   monitoring stack: Prometheus `ALERTS{alertstate="firing"}` and the `lu_cto_*` series (the
   private operations doc names the endpoints). A source reported down
   (`lu_cto_source_ok == 0`) is an attention item. Use hand-run commands (`gh`, usage
   meters) only for what no metric covers; a missing or wrong metric is a monitoring task,
   not a reason to keep measuring by hand.
1. **Inbox.** Drain the four recipients ([startup](startup.md#4-identity-and-inbox)) at
   cycle start, after workers settle and before handoff.
2. **Every pool's usage**, from the scorecard metrics when present, including unused ones:
   each Claude pool, Codex, Grok and Cursor, AGY and any other catalog pool. A pool with no
   metric gets a hand-read meter, and the gap is logged as a monitoring task. Grok and Cursor
   share one meter, never two pools of headroom. Keep readings in a scratch log for trends.
   Read each pool's CodexBar pace line: used minus expected and whether it will last to reset.
   Restrict routing for scarcity only when projected exhaustion precedes reset
   ([OO-99 pacing](decisions.md#tactical-layer-per-cycle)). Unknown pace is not scarcity.
   Read Opus task-hours per lane over the last 12 hours from task records. Flag a lane
   when the Claude pool's pace line shows it running out before reset, or for unauthorized
   use. Apply the same scarcity rule before changing routing.
   Before recording an account or credential blocker from a refusal code, check whether
   the account's access token has merely expired while its refresh token remains. Then the
   blocker is a token refresh, done through the supported refresh path in the private
   operations doc, not an operator re-login.
3. **Disk and load.** `df -h .`, `uptime`, `git worktree list | wc -l`. When disk climbs,
   run the reaper and retention tools before admitting write workers; never delete bulk
   corpus or data without a separate operator-authorized task (core.md P6).
   **Lane machinery.** Read the latest tick result of the host driver keeper and its lane
   wake. They are host-local code, not in this repository; their units and log location
   belong in the private operations doc. A tick must report no errors and must list
   every running lane pane. An error, or no lane panes, means no lane gets nudged; fix it
   this cycle. After a keeper config edit, verify one tick before nudging lanes.
   Read the keeper's per-CLI context flow: Claude waits for the keeper's tokened handoff
   prompt. Codex compacts natively, but a Codex driver hands off to a fresh session after
   its 4th compaction and before its 8th (operator 2026-10-25). Count each live Codex
   driver thread's compactions from its rollout file under `$CODEX_HOME/sessions`
   (`"type":"compacted"` events). At 4 or more, order the handoff that cycle; at 7, restart
   the lane yourself once it shows HANDOFF-DONE. When you record a new lane rule, measure
   every lane against it in the same cycle and name the control that will enforce it.
4. **Open PRs**, from the scorecard metrics when present, in every repository the fleet
   lands in, with `number`, `headRefOid`, `mergeable`, `mergeStateStatus`, `isDraft`,
   `reviewDecision`. Per PR: a review of record at the current `headRefOid` (verdict,
   reviewer model), a CI Gate run for that head and green CI; an older-head verdict is stale.
   A conflicting PR or missing current-head CI Gate run is an attention item. A background
   watcher with a deadline checks both as well as failing checks, replacing polling.
   Check main-branch CI in both public and private repositories. Give each open PR one
   blocker line with its age, next action and owner; flag ages over the one-hour target.
   Read keeper reasons for approved green PRs not enqueued. List every `hold` with its
   owning tracker item and removal condition; clear it when that condition is met.
   Measure stage time across dispatch, review, PR admission CI, queue CI, merge and reap
   in both repositories. Act on the slowest stage this cycle, with an owner and next check.
5. **Live workers.** Active dispatches from the Monitor API, then
   `.venv/bin/python scripts/delegate.py status <task-id> --run-nonce <nonce>` for each task
   the handoff or the view names; task files outrank a partial view. Every running worker
   has an armed background `delegate.py wait`. Any terminal status but `done` is an
   attention item; before calling a dispatch dead check open PRs and its worktree for
   unpushed work; reap after terminal status ([recipes](recipes.md#reap-before-re-dispatch)).
   List every task result or lane message awaiting a CTO grant or approval, with its age.
   Before any reply, compare running workers per pool with current authorized targets;
   fill a deficit with ready reserve-pool work, or name the blocker. Sent orders are not starts.
6. **Residuals.** Quote open-issue and residual counts from `gh`. A free slot with a ready
   item gets a dispatch; a residual above zero gets a next dispatch this session.
7. **Record tracker changes.** Use `lu-driver-state add --lane cto` for new orders,
   commitments and in-flight work, with the matching kind, owner and done condition.
   Record goals under their program's `operator_order` with `--parent <id>`; record
   blockers as items too. Attach references with `link`, progress with `note`, and proof
   with `evidence`. Use `status <id> done --reason <reason>` only after evidence supports
   the done condition. Cite item IDs in each cycle report so unfinished work stays visible.
8. **Decide.** Rank PRs by leverage, audit drift, look ahead, choose by the binding
   constraint ([decisions](decisions.md#tactical-layer-per-cycle)); log any mistake found
   in the ledger ([learning](learning.md)).
   Before restarting a lane or ordering an item, check its latest state and linked PR or
   issue state. Honor stops; send stale-open items with merged PRs to the tracker owner.
9. **Chase delivery.** Lanes deliver; the CTO does not take over their work. For each
   priority deliverable, the owning lane reports one line every cycle:
   state | exact blocker | who fixes it | next step | ETA. Treat any of these as
   foot-dragging: no report by the deadline, a passed ETA, the same blocker in two
   cycles, an idle lane, or a lane on other work while a priority deliverable is open.
   Escalate one step per cycle until the result lands:
   1. Demand: a Fleet order marked URGENT with a 10-minute report deadline, plus a
      keeper nudge if the pane is idle.
   2. Focus order: name the missed deadline or ETA, and order the lane to work only the
      deliverable and its blockers until it lands. Other ready work may fill only the
      worker slots the deliverable cannot use.
   3. Unblock: the CTO removes the blocker itself (a decision, a test grant, a missing
      review seat, or rerouting the blocker to another lane). It then reports the facts
      to the operator, including the lane's missed deadlines.
   Record each demand and each report in the deliverable's tracker item. A blocker the
   lane can fix itself is not a wait: order the fix.
