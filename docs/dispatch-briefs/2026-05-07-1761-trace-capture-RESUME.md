# Codex dispatch RESUME brief — #1761 trace-capture (continue from timeout)

> **Worktree:** `.worktrees/dispatch/codex/1761-trace-capture` (REUSE — your previous work is here)
> **Branch:** `codex/1761-trace-capture` (already exists)
> **Mode:** danger
> **Effort:** medium
> **Hard timeout:** 7200s (2h)
> **Silence timeout:** 1800s (30 min — overrides the buggy 600s default that killed your previous run)

## Why this is a resume

Your previous dispatch on this task (id `1761-trace-capture`, ran 600s) was killed by the `--silence-timeout` default bug (#1758). You had committed nothing yet but had **substantial work in flight**. The orchestrator preserved the worktree state.

## What's already in your worktree (DO NOT redo)

`git status -s` shows:
```
 M scripts/agent_runtime/adapters/claude.py
 M scripts/agent_runtime/adapters/codex.py
 M scripts/agent_runtime/adapters/gemini.py
 M scripts/agent_runtime/result.py
 M scripts/agent_runtime/runner.py
 A scripts/agent_runtime/tool_calls.py
 M scripts/build/linear_pipeline.py
 M scripts/build/v7_build.py
 A tests/test_detect_tool_theatre_integration.py
 A tests/test_runner_tool_calls.py
 M tests/test_v7_writer_dispatch.py
```

This is most of the implementation. **Inspect it first**, then finish the remaining gaps.

## Steps

1. `cd .worktrees/dispatch/codex/1761-trace-capture && git status -s` — confirm dirty tree matches above.
2. `git diff` (or per-file) to understand what was done. Look for incomplete sections, TODO markers, missing imports, half-implemented adapter methods.
3. Run tests to see what passes / fails:
   ```bash
   .venv/bin/pytest tests/test_runner_tool_calls.py tests/test_detect_tool_theatre_integration.py tests/test_v7_writer_dispatch.py -v
   ```
4. Finish whatever is incomplete. Apply the original brief at `docs/dispatch-briefs/2026-05-07-1761-trace-capture-plumbing.md` for any acceptance criteria that aren't met yet.
5. Validate per the original brief's "Validation before opening PR" section.
6. **Commit early and often** to avoid losing work to any future timeout. After each logical phase: `git add -p && git commit -m "..."`.
7. `git push -u origin codex/1761-trace-capture`
8. Open PR per the original brief's PR section. NO auto-merge.

## Critical reminders

- **Per #1726, the `detect_tool_theatre` function already exists on main.** You're populating its INPUT (the `tool_calls` field), not the function itself.
- **Tool output summaries must be ≤500 chars** (truncate with `[...truncated]`). Never store raw tool output in telemetry — leak risk.
- **Adversarial Claude review IS NOW UNBLOCKED** (#1754 fixed via #1760, merged at `cb231e001f`). Run it per the original brief.
- **Reviewer flag note:** the brief's `--model claude-opus-4-7` flag is `--to-model claude-opus-4-7` for the local `ask-claude`. Use the latter.

## Goal reminder

This is the bakeoff blocker. Without trace-capture, `detect_tool_theatre` false-positives every honest writer. Without that fixed, the bakeoff produces useless signal. Without bakeoff signal, writer-selection can't proceed. Without writer-selection, A1 module building stays blocked. **A1 modules are the project's next concrete deliverable** (a Ukrainian language curriculum for English speakers). Finish this fast and well.
