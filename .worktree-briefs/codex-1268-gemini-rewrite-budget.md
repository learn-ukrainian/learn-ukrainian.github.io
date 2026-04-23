# #1268 — Cap per-call Gemini runtime budget for rewrite blocks

Read `gh issue view 1268` for full context + ACs.

## Summary

Section-rewrite calls in v6 currently inherit `TIMEOUT_WRITE=900s` from
full-module write. When Gemini wedges mid-rewrite (process alive at 0%
CPU, session JSON frozen), pipeline sits idle 15 min before any
fallback is tried.

## Fix

1. Introduce a **separate `TIMEOUT_REWRITE_BLOCK`** constant (or env
   override), lower than `TIMEOUT_WRITE` — proposal: 300–450 seconds.
   Find the config site via `grep -rn "TIMEOUT_WRITE\|TIMEOUT_" scripts/`.

2. Wire the rewrite-block dispatch to use `TIMEOUT_REWRITE_BLOCK`
   specifically — NOT the write-phase budget. Path is probably
   `scripts/build/v6_build.py` rewrite-block dispatch OR `scripts/build/
   dispatch.py`.

3. Ensure the **overall rewrite-block budget leaves time for at least
   one fallback attempt**. If per-call cap is 300s and there are 2
   rungs in the ladder, overall budget needs to be >= 600s + slack.

4. **Full write / activities phases keep their existing budgets** —
   no regression there.

5. Tests:
   - Mock Gemini wedging past rewrite-block cap — assert dispatch
     terminates at the cap, not at the write budget
   - Assert write-phase dispatch still uses the full budget
   - Ladder fallback fires within overall rewrite-block budget

## Acceptance (per #1268)

- [ ] Rewrite-block dispatch uses smaller per-call cap than full-module
      write
- [ ] Overall rewrite-block budget still leaves fallback headroom
- [ ] Write / activities phases unchanged
- [ ] Automated test coverage
- [ ] `a1/M18` style-heal rerun reaches fallback or failure materially
      faster than the current 15+ min idle

## Worktree

```
git worktree add -b codex/1268-gemini-rewrite-budget .worktrees/codex-1268-gemini-rewrite-budget
```

Do NOT auto-merge.

## Hard timeout

2700s (45m). Narrow fix.
