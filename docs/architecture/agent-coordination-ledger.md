# Parallel Agent Coordination Ledger

## Problem

Shared `docs/session-state/*` files are not a safe coordination mechanism for
parallel work. An orchestrator thread, worker threads, subagents, and external
agent fleet runs can overwrite the same file or read stale state. That failure
mode already caused confusion between UI work, A1 content work, and handoff
state.

## Decision

Use an append-friendly runtime ledger as the operational source of truth.
Markdown can be generated for humans, but workers must not write shared
session-state files as their reporting channel.

The first implementation slice stores task records in ignored runtime state:

```text
batch_state/agent-ledger/tasks/<task-id>.json
```

The ledger integrates with, but does not replace, `scripts/delegate.py`.
`delegate.py` owns process lifecycle and worktree setup. The coordination
ledger owns the orchestrator view: who is working, where, on what paths, with
which issue/thread/branch, and with which validation/review state.

## Task Record

Each active or completed task records:

- `task_id`
- `issue`
- `lane`
- `module_family`
- `task_family`
- `agent`
- `model`
- `thread_id`
- `branch`
- `worktree`
- `owned_paths`
- `status`
- `heartbeat_at`
- `validation`
- `review`
- `ci`
- `pr_url`
- append-only `events`

## Task Families

Telemetry should be measured at least across:

- `architecture`
- `coding`
- `code_review`
- `design`
- `documentation`
- `refactoring`
- `content_writing`
- `creative_writing`
- `translation_localization`
- `operations_release`
- `pedagogy_review`
- `research_verification`

These families let the orchestrator compare agents by real task type instead
of one vague "best model" ranking.

## Ownership

Workers must declare `owned_paths`. The ledger blocks overlapping active path
ownership unless the orchestrator explicitly allows conflicts. This supports
parallel module families such as A1, A2, Folk, UI, BIO, infra, and review lanes
without pretending they are one serial session.

Examples:

```bash
.venv/bin/python scripts/orchestration/agent_ledger.py upsert-task \
  --task-id 2823-ui-worker \
  --agent codex \
  --status running \
  --issue 2823 \
  --lane ui \
  --module-family site \
  --task-family design \
  --thread-id 019ea418-d223-7120-8705-ba5988321e92 \
  --branch codex/2823-lightweight-ui \
  --worktree .worktrees/dispatch/codex/2823-lightweight-ui \
  --owned-path starlight/src/pages \
  --owned-path starlight/src/styles

.venv/bin/python scripts/orchestration/agent_ledger.py heartbeat \
  --task-id 2823-ui-worker \
  --actor codex \
  --message "browser QA passed; awaiting independent review"
```

## Monitor API

The first read-only API endpoints are:

- `/api/coordination/summary`
- `/api/coordination/active`
- `/api/coordination/tasks/{task_id}`

Future slices should add write endpoints only if authentication and local-use
constraints are clear. Until then, workers write via the local CLI.

## Rules

- Workers report through the ledger, their Codex thread, and their owned
  GitHub issue or PR.
- Workers must not write `docs/session-state/current.md`,
  `docs/session-state/current.orchestrator.md`, or any shared session-state file.
- The orchestrator remains responsible for review routing, merge decisions,
  issue hygiene, PR queue hygiene, and final summaries.
- Independent review remains mandatory before merge.
