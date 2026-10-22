# Handoff

Hand off at about 65 percent context or session end; never `/compact`. Watchers, waits and
wake timers die with this session; the next one re-arms them from the file handoff.

1. Run a last [cycle](cycle.md) so every number is current.
2. Timestamp with `date -u +%Y-%m-%dT%H:%MZ`; never type a time.
3. Update the mistakes ledger ([learning](learning.md)): new entries, status changes and
   recurrence counts.
4. Prepend a `HANDOFF FINAL` block to `.claude/epics-epic/DRIVER-STATE.md` above older
   ones. Then move superseded handoff blocks and session logs to
   `.claude/epics-epic/archive/`, so the state file stays under 40 KB (`wc -c`) and the next
   startup can read it in one step. Keep the newest handoff, the blocks it names and the
   mistakes ledger.
5. Prepare the rollover with the `thread-rollover` skill; put its lineage and rollover IDs
   in the STARTUP line.
6. Write the durable brief (core.md P7) and drain the inbox one last time.

```markdown
## HANDOFF FINAL <date -u> (session <session id>, context <percent>) - READ FIRST
- MODE: <CTO-only or lanes running; worker cap; reviewer defaults in force>
- DISK: <percent used, free> and what was cleaned this session
- PRs: <repo#number head <sha8> state: verdict@head, CI, queue> for every open PR touched
- WORKERS: <task-id nonce <nonce> agent, deliverable, wait armed?> for every live worker
- SCORECARD: <PRs merged, median approved-to-merged time, rework rounds per PR,
  new mistakes / repeats (ledger IDs; a repeat of a verified entry names its next control step)>
- PARKED: <each item stopped mid-way (uncommitted edits, cancelled workers, half-run
  procedures): location, state, condition to resume> or none
- NEXT 3: (1) ... (2) ... (3) ...
- STARTUP: launch with the CTO launcher (see the private operations doc); resume ONLY
  <lineage-id> / <rollover-id> with the thread-rollover skill; scratch helpers in <scratch>
- WATCHERS in this session die with it: <ids and what each watched>. Re-arm.
```

Every line is tool-backed or says NOT CHECKED with its command. Public briefs follow
core.md P8; private detail stays in the gitignored state file or the private infra repository.
