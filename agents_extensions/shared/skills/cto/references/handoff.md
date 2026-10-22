# Handoff

Hand off when context reaches about 65 percent, or at session end. Never use `/compact`.
Everything the next session needs goes in the file handoff; background watchers, waits and
wake timers die with this session and must be re-armed by the next one.

## Steps

1. Run a last [cycle](cycle.md) so every number in the block is current.
2. Take the timestamp with `date -u +%Y-%m-%dT%H:%MZ`; never type a time.
3. Prepend a `HANDOFF FINAL` block to the CTO state file
   (`.claude/epics-epic/DRIVER-STATE.md`), above older handoffs. Keep the state file to
   current state; archive superseded session logs under `.claude/epics-epic/archive/`.
4. Prepare the rollover with the `thread-rollover` skill and put the exact lineage and
   rollover IDs in the block's startup line.
5. Write the durable brief the core rules require (`docs/session-state/<date>-<slug>-brief.md`,
   P7) and drain the inbox one last time.

## Block shape

```markdown
## HANDOFF FINAL <date -u> (session <session id>, context <percent>) - READ FIRST
- MODE: <CTO-only or lanes running; worker cap; reviewer defaults in force>
- DISK: <percent used, free> and what was cleaned this session
- PRs: <repo#number head <sha8> state: verdict@head, CI, queue> for every open PR touched
- WORKERS: <task-id nonce <nonce> agent, what it delivers, wait armed?> for every live worker
- NEXT 3: (1) ... (2) ... (3) ...
- STARTUP: bind ONLY <lineage-id> / <rollover-id> (bind-replacement, bootstrap-replacement,
  fill semantic-snapshot, confirm-replacement x3); scratch helpers in <scratch>
- WATCHERS in this session die with it: <ids and what each watched>. Re-arm.
```

Every line is tool-backed. Anything not checked says NOT CHECKED and names the command.
Operator words, host details and credentials never go into a public brief (core.md P8);
private operational detail belongs only in the gitignored state file or the private infra
repository.
