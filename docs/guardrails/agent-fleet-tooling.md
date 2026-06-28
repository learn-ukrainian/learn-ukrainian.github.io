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
