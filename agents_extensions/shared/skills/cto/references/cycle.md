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
   Before recording an account or credential blocker from a refusal code, read that
   account's own meter through the account-bound probe
   (`scripts/api/claude_account_usage.py`, OAuth source only, served by the Monitor API;
   host paths stay in the private operations doc) and check its token expiry. A lapsed
   access token with a valid refresh token needs a refresh, not an operator re-login.
3. **Disk and load.** `df -h .`, `uptime`, `git worktree list | wc -l`. When disk climbs,
   run the reaper and retention tools before admitting write workers; never delete bulk
   corpus or data without a separate operator-authorized task (core.md P6).
4. **Open PRs**, from the scorecard metrics when present, in every repository the fleet
   lands in, with `number`, `headRefOid`, `mergeable`, `mergeStateStatus`, `isDraft`,
   `reviewDecision`. Per PR: a review of record at the current `headRefOid` (verdict,
   reviewer model), a CI Gate run for that head and green CI; an older-head verdict is stale.
   A conflicting PR or missing current-head CI Gate run is an attention item. A background
   watcher with a deadline checks both as well as failing checks, replacing polling.
   An approved green PR not enqueued gets its reason from the merge-queue keeper's log,
   not a guess.
5. **Live workers.** Active dispatches from the Monitor API, then
   `.venv/bin/python scripts/delegate.py status <task-id> --run-nonce <nonce>` for each task
   the handoff or the view names; task files outrank a partial view. Every running worker
   has an armed background `delegate.py wait`. Any terminal status but `done` is an
   attention item; before calling a dispatch dead check open PRs and its worktree for
   unpushed work; reap after terminal status ([recipes](recipes.md#reap-before-re-dispatch)).
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
