# Cycle checklist

Run every cycle while work is in flight, and before any routing, budget or status report.
Every line of a cycle report is tool output from this cycle; anything not read is reported
as unknown, never as fine.

## 1. Inbox

Drain the four recipients ([startup §4](startup.md#4-drain-the-inbox)) at cycle start,
after workers settle and before handoff.

## 2. Usage of all pools

Report every pool every cycle, including the ones you are not using. A pool with no
readable meter is reported as unknown.

| Pool | Command | Fields |
| --- | --- | --- |
| Claude, account a | `CLAUDE_CONFIG_DIR=<account a config dir> codexbar usage --provider claude --json-only --no-credits` | `[0].usage.secondary.usedPercent` (weekly), `.primary.usedPercent` (5 h), `[0].pace.secondary.summary` |
| Claude, account b | same, with the account b config dir | same |
| Codex (Sol) | `codexbar usage --provider codex --json-only --no-credits` | weekly `secondary.usedPercent`, pace summary |
| Grok and Cursor (one meter) | `codexbar usage --provider grok --source auto --json-only --no-credits` | `[0].usage.primary.usedPercent`; flaky, retry once; fallback `/usage` inside `grok` or `cursor-agent` |
| AGY (Gemini) | `curl -s http://127.0.0.1:8765/api/state/routing-budget` | `.agents.gemini`: `burn_pct_7d`, `status`, `resets_at` (codexbar does not read AGY) |
| Muse | `codexbar usage --provider muse --json-only --no-credits` | weekly `secondary.usedPercent`, 5 h `primary.usedPercent`, `secondary.resetsAt` |
| DeepSeek | no readable meter | report unknown |

Grok and Cursor draw one meter: never count them as two pools of headroom. Wrap each
command in `timeout 90`; put the set in one scratch script that appends a timestamped line
per pool to a scratch log, so trends survive within the session.

## 3. Disk and load

`df -h .`, `uptime`, and `git worktree list | wc -l`. Disk budgets are not a floor to relax
toward: when disk climbs, run the reaper and retention tools before admitting more write
workers. Never delete bulk corpus or data without a separate operator-authorized task
(core.md P6).

## 4. Open PRs in both repos

```bash
gh pr list -R learn-ukrainian/learn-ukrainian.github.io --state open \
  --json number,headRefOid,headRefName,mergeStateStatus,isDraft,reviewDecision,title
gh pr list -R learn-ukrainian/learn-ukrainian-infra-private --state open --json <same fields>
```

For each PR: is there a `cf-verdict v1 sha=<head>` comment whose SHA equals the current
`headRefOid`, what is its `verdict=` and `model=`, and is CI green on that same head? A
verdict at an older head is stale. A watcher that loops `gh pr view <n> --json
headRefOid,comments,state` every two minutes and matches that marker against the head
saves manual polling; run it in the background with a deadline.

An approved, green PR the keeper has not enqueued gets a reason from the keeper journal
(next section), not a guess.

## 5. Merge-queue keeper and review trigger

```bash
journalctl --user -u learn-ukrainian-merge-queue-keeper.service --since "-30 min" --no-pager
journalctl --user -u lu-private-review-trigger.service --since "-30 min" --no-pager
```

The keeper enqueues approved green PRs and says why it skipped one (missing recovery
evidence, stale verdict, red check). The trigger seats automatic cross-family reviews and
writes a result file per PR attempt in its state directory:

- `NO_VERDICT`: the attempt produced no exact-head verdict.
- `REVIEW_INFRA_FAILURE`: the reviewer judged its evidence insufficient (often a diff cut
  at the prompt cap, an unreadable linked issue, or no checkout). It is not a code finding.

The trigger stops after two attempts per head. Either result on a large PR means it needs a
toolful seat, not a third trigger attempt ([recipes](recipes.md#private-prs-and-the-review-trigger)).
A journal line saying no alternate family is available means the CTO seats the review by
hand.

## 6. Live workers

`curl -s http://127.0.0.1:8765/api/delegate/active`, then
`.venv/bin/python scripts/delegate.py status <task-id> --run-nonce <nonce>` for each task
the handoff or the active view names; task files outrank a partial active view. Every running worker has an armed background
`delegate.py wait <task-id> --run-nonce <nonce>`. A terminal status other than `done` is an
attention item. Before calling a dispatch dead, check open PRs and its worktree for
finished but unpushed work. After a terminal status reap it
([recipes](recipes.md#reap-before-re-dispatch)).

## 7. Residuals and next work

Quote open-issue and residual counts from `gh` this cycle. A free worker slot with a ready
item gets a dispatch; a residual above zero gets a next dispatch this session.
