# Codex Thread Handoff Runbook

This runbook covers replacement-thread rollover when a Codex, Claude, Gemini,
or orchestrator heartbeat thread approaches the auto-compaction zone.

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
prompt, scoped by agent name:

- Lease state: `.agent/<agent>-thread-lease.json` (gitignored)
- Bootstrap prompt: `.agent/<agent>-thread-bootstrap.md` (gitignored)
- Tracked agent handoff: `docs/session-state/current.<agent>.md`
- Compatibility router: `docs/session-state/current.md`
- Script: `scripts/orchestration/thread_handoff.py`

Agent names are lower-case slugs matching `[a-z][a-z0-9-]*`. The standard
agents are `orchestrator`, `codex`, `claude`, and `gemini`; additional agents
can use the same naming rule.

`docs/session-state/current.md` is intentionally small. It is a router with a
stable `Latest-Brief: docs/session-state/current.orchestrator.md` marker for
legacy cold-start hooks plus an `Agent-Handoff:` mapping for each agent. Do not
put detailed state in the router.

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

## Standard Orchestrator Rollover

Run this from the repo root when the heartbeat thread enters the rollover
zone:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py prepare \
  --agent orchestrator \
  --write-current \
  --context-percent 86
```

If the active thread id or automation id is known, include them:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py prepare \
  --agent orchestrator \
  --write-current \
  --active-thread-id <current-thread-id> \
  --active-automation-id <old-heartbeat-automation-id> \
  --context-percent 86
```

This writes:

- `.agent/orchestrator-thread-lease.json`
- `.agent/orchestrator-thread-bootstrap.md`
- `docs/session-state/current.orchestrator.md`
- `docs/session-state/current.md` router only when `--write-current` is present

The generated prompt is the exact replacement-thread bootstrap. If the Codex
app `create_thread` tool is available to the current agent, use it with that
prompt. If it is not available, create one new Codex UI thread manually and
paste the generated prompt. That is the only unavoidable UI action.

After the replacement thread is visibly running, confirm it:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py confirm-started \
  --agent orchestrator \
  --new-thread-id <replacement-thread-id>
```

Only if the output shows `"old_automation_ready_to_delete": true` may the old
heartbeat automation be deleted or paused through the Codex app
`automation_update` tool.

## Non-Orchestrator Agent Rollover

Agents other than the orchestrator write only their own handoff by default:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py prepare \
  --agent codex \
  --context-percent 86
```

That writes `.agent/codex-thread-lease.json`,
`.agent/codex-thread-bootstrap.md`, and
`docs/session-state/current.codex.md`. It does not modify
`docs/session-state/current.md` and does not touch
`docs/session-state/current.orchestrator.md`.

Only pass `--write-current` for a non-orchestrator agent when the task
explicitly authorizes a router update. The router must stay tiny and must keep
`Latest-Brief:` plus the `Agent-Handoff:` mapping.

Confirm the replacement with the same agent name:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py confirm-started \
  --agent codex \
  --new-thread-id <replacement-thread-id>
```

## Safety Checks

Check the lease at any time:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py check --agent orchestrator
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
  --agent orchestrator \
  --force-reset-state \
  --write-current \
  --context-percent 86
```

Dry-run without writing files:

```bash
.venv/bin/python scripts/orchestration/thread_handoff.py prepare --agent codex --dry-run
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
replacement thread for the orchestrator. Other agents run `prepare --agent
<name>` without `--write-current` unless explicitly asked to update the shared
router. Keep the old heartbeat active until `confirm-started --agent <name>`
records the replacement thread id.

At 90 percent context or higher, stop non-handoff work. The current thread
should only write the handoff packet, start or prompt for the replacement
thread, and preserve the old automation until confirmation.
