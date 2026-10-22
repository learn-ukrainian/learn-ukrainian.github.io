# Cycle checklist

Run every cycle while work is in flight, and before any routing, budget or status report.
Every line of a cycle report is tool output from this cycle; anything not read is reported
as unknown, never as fine.

## 1. Inbox

Drain the four recipients ([startup §4](startup.md#4-drain-the-inbox)) at cycle start,
after workers settle and before handoff.

## 2. Usage of all pools

Report every pool every cycle, including the ones you are not using: each Claude pool,
Codex, Grok and Cursor, AGY, and any other pool the catalog routes to. A pool with no
readable meter is reported as unknown. Grok and Cursor draw one meter: never count them as
two pools of headroom. Keep the readings in a scratch log so trends survive within the
session.

## 3. Disk and load

`df -h .`, `uptime`, and `git worktree list | wc -l`. Disk budgets are not a floor to relax
toward: when disk climbs, run the reaper and retention tools before admitting more write
workers. Never delete bulk corpus or data without a separate operator-authorized task
(core.md P6).

## 4. Open PRs

List the open PRs in every repository the fleet lands in, with `number`, `headRefOid`,
`mergeStateStatus`, `isDraft` and `reviewDecision`. For each PR: is there a review of record
whose SHA equals the current `headRefOid`, what is its verdict and reviewer model, and is CI
green on that same head? A verdict at an older head is stale. A background watcher with a
deadline saves manual polling.

An approved, green PR that has not been enqueued gets a reason from the merge-queue
keeper's log, not a guess.

## 5. Live workers

Read the active dispatches from the Monitor API, then
`.venv/bin/python scripts/delegate.py status <task-id> --run-nonce <nonce>` for each task
the handoff or the active view names; task files outrank a partial active view. Every
running worker has an armed background `delegate.py wait <task-id> --run-nonce <nonce>`. A
terminal status other than `done` is an attention item. Before calling a dispatch dead,
check open PRs and its worktree for finished but unpushed work. After a terminal status
reap it ([recipes](recipes.md#reap-before-re-dispatch)).

## 6. Residuals and next work

Quote open-issue and residual counts from `gh` this cycle. A free worker slot with a ready
item gets a dispatch; a residual above zero gets a next dispatch this session.

## 7. Decide

Rank the open PRs by leverage, run the drift audit and the look-ahead for the next failure,
then choose this cycle's actions by the binding constraint
([decisions](decisions.md#tactical-layer-per-cycle)).
