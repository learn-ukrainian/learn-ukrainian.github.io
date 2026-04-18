# Session Handoff — 2026-04-18 noon (post-/clear)

You're starting cold. Boot via the API, not the filesystem:

```python
from ai_agent_bridge.monitor_client import MonitorClient
boot = MonitorClient().bootstrap()      # manifest + cached rules + this file
```

Then `curl /api/orient` for live state and `curl /api/comms/inbox?agent=claude` for unread messages. **Do not** read `CLAUDE.md` or `claude_extensions/rules/*.md` directly — they're served by `/api/rules` with hash-based 304s. See `docs/MONITOR-API.md` for the full endpoint table.

## Decisions waiting on you (the only reason this file isn't `git log`)

| # | Decision | Resolve by |
|---|---|---|
| 1 | **Phase B kickoff?** Different pipeline from Phase A; could proceed without re-verify, or run a 2-slug Phase A re-verify first. | Say "go Phase B" or "rerun Phase A". |
| 2 | **Merge #1323 + #1324 round-2 patches** as-is, or queue another Gemini re-verify? | Spot-check the regression tests; Gemini-quota-sensitive. |
| 3 | **`rclone config`** for Phase C activation. Backup scripts ready, no Drive remote yet. OAuth needs your browser. | `rclone config`, then install cron from `docs/ops/gdrive-backup.md`. |
| 4 | **Restore the agent-watcher LaunchAgent?** Unloaded this session; backup at `~/Library/LaunchAgents/com.learn-ukrainian.agent-watcher.plist.disabled-2026-04-18`. | Leave unloaded unless you want auto-broker draining back. |
| 5 | **Push the cold-start-handoff pattern further?** User explicitly parked these for after `/clear`. Three deltas: (a) `scripts/cold-start.sh` shell wrapper around `MonitorClient().bootstrap()` for symmetry with `scripts/ops/smoketest_bridge_stdout_only.sh`. (b) Wire the bridge smoketest into the pre-commit hook for any change touching `scripts/ai_agent_bridge/_gemini.py` or `_cli.py` so this regression class can't sneak back. (c) Audit other `docs/session-state/*.md` for the same bloat pattern (duplicating API-served state) and trim. | Pick one or all three when you resume. |

## Behavior changes future callers may trip on

These belong here (not in commit messages) because they change a contract callers may have memorized:

- **`scripts/wiki/state.py:is_compiled`** now AND-checks the on-disk `.md` file and self-purges stale rows. Don't add a redundant file-existence check at call sites.
- **`scripts/ai_agent_bridge` `--stdout-only`** now actually writes Gemini's response to stdout (was previously suppressing it AND polluting stdout with `[gemini] attempt N/M` preamble). Wiki review parser depends on this. Verify with `bash scripts/ops/smoketest_bridge_stdout_only.sh` after any bridge change.
- **`services.sh restart`** is serialized cross-process via `mkdir`-based lock at `.pids/.restart.lock.d/`. Stale lock auto-reclaims when holder PID is dead.

Everything else (commit log, PR/issue list, pipeline state, in-flight workers, recent handoffs, ahead-of-origin count) is one `gh`/`git`/`curl /api/orient` call away — don't snapshot it here.

## Archived

Earlier in-flight running-log handoff: `docs/session-state/2026-04-18-am-autonomous-handoff.md`.
