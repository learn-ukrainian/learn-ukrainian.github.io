# Handoff

Keep working until the keeper's handoff prompt; reply `HANDOFF-DONE` with its exact token.
Claude uses that handoff; Codex compacts natively. Never stop early for a context percentage
or ask the operator to restart. Watchers, waits and wake timers die with the session;
the next one re-arms them from the tracker handoff.

1. Run a last [cycle](cycle.md) so every number is current.
2. Timestamp with `date -u +%Y-%m-%dT%H:%MZ`; never type a time.
3. Update the mistakes ledger ([learning](learning.md)): new entries, status changes and
   recurrence counts.
4. Reconcile `lu-driver-state render --lane cto` and `lu-driver-state check --lane cto`.
   Every open thing must have an item: orders, goals, commitments, in-flight work, blockers,
   parked work and next actions. Update existing items with `link`, `note`, `evidence` and
   `status`; never replace unfinished items with a new session summary.
5. Prepare the rollover with the `thread-rollover` skill. Add one `handoff_note` item with
   `lu-driver-state add --lane cto --kind handoff_note`, an owner and a done condition.
   Include the details below in its statement and cite the work item IDs it names.
6. List every background Bash task and Monitor stream you started, then use `TaskStop`
   on each before posting HANDOFF-DONE. A running task makes the TUI ask before exit.
   Delegate workers are separate processes and keep running.
7. Write the durable brief (core.md P7) and drain the inbox one last time.

The `handoff_note` contains:

- Timestamp, session ID and context percentage.
- Mode: CTO-only or lanes running, worker cap and reviewer defaults in force.
- Disk used and free, and what was cleaned this session.
- Every open PR touched: repository, number, head SHA, verdict at that head, CI and queue state.
- Every live worker: task ID, FULL run nonce, agent, deliverable and whether its wait is armed.
- Scorecard: PRs merged, median approved-to-merged time, rework rounds per PR, new mistakes
  and repeats by ledger item ID. A repeat of a verified correction names its next control step.
- Parked item IDs, locations, state and condition to resume, or none.
- The next three actions by item ID.
- Startup: record the keeper's launcher argv, exact lineage and rollover IDs to resume
  with `thread-rollover`, and the scratch helper path. The keeper restarts the seat.
- Watcher IDs and what each watched, so the next session can re-arm them.

Copy each worker's `run_nonce` whole: `scripts/dispatch.py wait <task-id> --run-nonce <nonce>` compares it exactly.
A shortened or changed nonce is refused.

Keep `.claude/epics-epic/DRIVER-STATE.md` under 4 KB (`wc -c`). Its only content is pinned
provider facts needed in every model call and instructions to run
`lu-driver-state render --lane cto` and `lu-driver-state check --lane cto` first.
Do not write a markdown handoff block or duplicate tracker state there.

Every line is tool-backed or says NOT CHECKED with its command. Public briefs follow
core.md P8; private detail stays in the driver-state database or the private infra repository.
