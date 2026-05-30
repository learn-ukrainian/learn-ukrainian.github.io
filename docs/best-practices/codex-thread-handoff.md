# Codex Thread Handoff Runbook

This runbook covers overnight orchestrator rollover when a Codex heartbeat
thread approaches the auto-compaction zone.

## Verified Capabilities

Verified locally on 2026-05-30:

- Codex app tools are exposed in this environment for `create_thread`,
  `list_threads`, `read_thread`, `send_message_to_thread`,
  `set_thread_title`, `set_thread_pinned`, `set_thread_archived`, and
  `automation_update`.
- Those app tools are not callable from a repo-local Python subprocess.
  Local automation must therefore generate state, prompts, and guardrails
  without depending on them.
- `$CODEX_HOME/state_5.sqlite` contains a `threads` table plus related
  `thread_dynamic_tools` and job tables. `$CODEX_HOME/session_index.jsonl`
  is a compact local thread index.
- `$CODEX_HOME/automations/` existed but had no `automation.toml` files in
  this audit, only `.run-jitter-salt`.
- `scripts/ai_agent_bridge/_ui_codex.py` already supports sending messages
  to an existing Codex UI thread with `codex exec resume`; it does not create
  a new app thread.
- Monitor state for orchestration is available through `/api/orient`,
  `/api/delegate/active`, `/api/delegate/tasks`, and `/api/worktrees`.

## Architecture

The handoff system uses a local thread lease plus a generated bootstrap
prompt:

- Lease state: `.agent/orchestrator-thread-lease.json` (gitignored)
- Bootstrap prompt: `.agent/orchestrator-thread-bootstrap.md` (gitignored)
- Optional tracked handoff update: `docs/session-state/current.md`
- Script: `scripts/orchestration/thread_handoff.py`

The lease records:

- active orchestrator generation and thread id, when known
- active heartbeat automation id, when known
- replacement generation
- replacement status: `pending_start` or `started`
- bootstrap prompt path
- cleanup guard: `old_automation_ready_to_delete`

The cleanup guard is false after `prepare`. It becomes true only after
`confirm-started --new-thread-id ...` succeeds. This keeps the old heartbeat
alive if the replacement thread was not actually started.

## Standard Rollover

Run this from the repo root when the heartbeat thread enters the rollover
zone:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py prepare \
  --write-current \
  --context-percent 86
```

If the active thread id or automation id is known, include them:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py prepare \
  --write-current \
  --active-thread-id <current-thread-id> \
  --active-automation-id <old-heartbeat-automation-id> \
  --context-percent 86
```

This writes:

- `.agent/orchestrator-thread-lease.json`
- `.agent/orchestrator-thread-bootstrap.md`
- `docs/session-state/current.md` only when `--write-current` is present

The generated prompt is the exact replacement-thread bootstrap. If the Codex
app `create_thread` tool is available to the current agent, use it with that
prompt. If it is not available, create one new Codex UI thread manually and
paste the generated prompt. That is the only unavoidable UI action.

After the replacement thread is visibly running, confirm it:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py confirm-started \
  --new-thread-id <replacement-thread-id>
```

Only if the output shows `"old_automation_ready_to_delete": true` may the old
heartbeat automation be deleted or paused through the Codex app
`automation_update` tool.

## Safety Checks

Check the lease at any time:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py check
```

Warnings mean the old heartbeat automation should stay active. Common
warnings:

- replacement is still `pending_start`
- pending replacement is stale
- active generation has not been seen recently
- context estimate is at or above the threshold
- cleanup says ready but no replacement thread id is recorded
- lease state file is unreadable or corrupt

`prepare` and `confirm-started` refuse to overwrite an unreadable lease file.
Inspect or restore the file first. If the operator intentionally wants to
discard the corrupt lease and start a new one, run:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py prepare \
  --force-reset-state \
  --write-current \
  --context-percent 86
```

Dry-run without writing files:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py prepare --dry-run
```

Audit local Codex metadata:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py audit
```

Include live Monitor API state in the audit:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py audit --include-monitor
```

## Heartbeat Behavior

At 75 percent context, run `prepare --dry-run` to verify the packet renders.

At 82 percent context or higher, run `prepare --write-current` and start the
replacement thread. Keep the old heartbeat active until `confirm-started`
records the replacement thread id.

At 90 percent context or higher, stop non-handoff work. The current thread
should only write the handoff packet, start or prompt for the replacement
thread, and preserve the old automation until confirmation.
