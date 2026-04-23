# #1286 — Stabilize codex-tools review transport

Read `gh issue view 1286` for full context + ACs.

## Summary of the bug

`codex-tools` review-style dispatch can leave `/var/.../codex-runtime-
review-style-*.txt` files at size 0 while the Codex subprocess stays
alive. Old reviewer subprocesses accumulate instead of terminating
cleanly. Blocks canonical v6 quality gate because the reviewer lane
isn't reliably returning parsed payloads.

## Scope

Find the dispatch plumbing for `codex-tools` in the reviewer lane —
probably lives in `scripts/ai_agent_bridge/_codex.py` or
`scripts/agent_runtime/` or `scripts/build/dispatch.py`. Trace from
"writer-emits-prose → reviewer is invoked" path.

Fixes to land:
1. **Dispatch timeout + process lifecycle**: detect when the output
   file is 0 bytes + the subprocess is idle (0% CPU for > N seconds)
   and terminate the subprocess cleanly + mark the dispatch as failed.
2. **Reaper for stale reviewer subprocesses**: on dispatch start,
   clean up any orphaned `codex exec ... codex-runtime-review-style-*`
   processes from previous runs (by PID lineage or file pattern).
3. **Empty-output handling**: treat a 0-byte output after dispatch
   completion as an error, not a silent pass. Retry once per the
   fallback ladder; if second attempt also empty, fail with a specific
   error code the audit gate can catch.

## Acceptance criteria (per #1286)

- [ ] Canonical `codex-tools` review-style dispatch returns or fails
      deterministically — no lingering subprocesses
- [ ] Empty output files don't leave live reviewer processes behind
- [ ] Stale reviewer subprocesses are reaped safely at dispatch start
- [ ] Direct `codex-tools` review-style dispatch for `a1/M18` returns
      a parsed review payload
- [ ] One clean E2E `a1/M18` run using canonical reviewer lane
- [ ] pytest green

## Worktree

```
git worktree add -b codex/1286-review-transport .worktrees/codex-1286-review-transport
```

Do NOT auto-merge.

## Hard timeout

3600s (1h).
