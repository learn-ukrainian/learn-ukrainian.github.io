# Agent Fleet Tooling Guardrail

## Current Supported Routes

Use these project entry points for agent fleet work:

- `.venv/bin/python scripts/ai_agent_bridge/__main__.py ...` for bridge
  messages, channel posts, one-shot review requests, and discussion commands.
- `scripts/delegate.py dispatch ...` for worktree-isolated implementation,
  review, validation, and long-running delegated work.
- AGY is the current Gemini-family route. Use it through `ai_agent_bridge` for
  bridge work or through `scripts/delegate.py dispatch --agent agy ...` for
  dispatched work.

Gemini CLI and Gemini Code Assist are unsupported for this project. Do not
document them as current fallback, review, dispatch, or restoration paths.

## Stream Orchestration Model

Long-running curriculum streams should have one orchestrator thread per stream
and worker threads or dispatched worktrees per task. The orchestrator thread is
the source of queue state and merge decisions; worker threads are disposable,
scoped, and replaceable.

Minimum stream toolset expected inside Codex UI:

- View stream queue, current slug/module, active worker threads, open PRs, and
  paused/active monitor state.
- Spawn worker thread or delegated worktree with a narrow brief, target files,
  forbidden writes, validation commands, and required `X-Agent` trailer.
- Read worker result and PR/check status back into the orchestrator thread.
- Archive completed worker threads and preserve a compact handoff summary.
- Resume stream orchestration in a new thread from queue state when the old
  thread becomes unusable.

Until UI-level stream controls exist, encode stream state in heartbeat prompts,
PR bodies, handoff summaries, and branch/worktree names. Keep worker briefs
compact and source-heavy; avoid moving long logs or source dumps between
threads without Headroom compression.

## Fleet Role Routing

- **Codex:** orchestration, integration, deterministic validation, PR/merge
  control, scoped code/docs edits.
- **Claude:** independent read-only review for BIO narrative, source framing,
  leakage, and final merge gates.
- **AGY (Gemini-family via bridge):** adversarial factual/source checks,
  alternate-source search, and broad read-only sweeps through the project
  bridge.
- **DeepSeek/Hermes-style reviewers:** sensitive decolonization/framing review
  when available through the bridge.
- **Grok-build:** build/CI diagnostics and native build-tool checks when
  available through the bridge.
- **Cursor:** UI/front-end and larger code navigation/diff work when the route
  is active; do not block stream progress while the route needs renewal.

Use the full fleet when work is parallelizable or model specialization improves
quality. Do not fan out for a tiny single-file change when deterministic tools
and one independent review are cheaper and safer.

## Command Examples

```bash
printf '%s\n' "<review prompt>" | \
  .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-agy - \
    --task-id review-123 \
    --to-model gemini-3.1-pro-high \
    --review

scripts/delegate.py dispatch \
  --agent agy \
  --brief docs/dispatch-briefs/example.md \
  --worktree
```

Avoid bare `ab ...` examples. On the user's machine `ab` resolves to
ApacheBench (`/usr/sbin/ab`), so `ab ask-agy`, `ab ask-gemini`, `ab post`, and
`ab discuss` examples may run the wrong binary. If a local project wrapper is
ever reintroduced, documentation must prove it exists in the execution
environment before relying on it.

## AGY Model Names

Direct `agy --model` calls use display labels printed by `agy models`, for
example:

- `Gemini 3.1 Pro (High)`
- `Gemini 3.5 Flash (High)`

The project bridge and runtime may accept slugs such as
`gemini-3.1-pro-high` and map them to AGY display labels before invoking AGY.
Use slugs only in bridge/runtime examples, not in direct `agy --model`
examples.
