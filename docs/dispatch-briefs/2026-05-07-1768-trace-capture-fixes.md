# Codex dispatch brief — #1768 trace-capture HIGH-RISK fixes (bakeoff blocker)

> **Worktree:** `.worktrees/dispatch/codex/1768-trace-fixes`
> **Branch:** `codex/1768-trace-fixes`
> **Base:** `main`
> **Mode:** danger
> **Effort:** medium
> **Hard timeout:** 5400s
> **Silence timeout:** 1800s

## Worktree setup

```bash
git worktree add -b codex/1768-trace-fixes .worktrees/dispatch/codex/1768-trace-fixes
cd .worktrees/dispatch/codex/1768-trace-fixes
```

## Goal

Closes #1768. Pre-bakeoff Claude Opus xhigh validation found 3 HIGH-RISK trace-capture bugs that would systematically taint bakeoff signal in opposite directions on different writers. Fix all 3 now so the next bakeoff produces fair comparable signal.

Full diagnosis is in issue #1768 — read it first.

## HIGH-RISK 1 — Gemini cross-contamination

**File:** `scripts/agent_runtime/adapters/gemini.py:548-571`

Problem: `_read_latest_session_trace` picks newest `~/.gemini/tmp/<cwd.name>/chats/session-*.json` within a 2-hour window. No per-plan binding. Bakeoff runs same writer multiple times → traces leak between invocations.

Fix (per reviewer): Snapshot pre-existing session files in `build_invocation` (capture the set of session-*.json paths that exist BEFORE the dispatch), then in `_read_latest_session_trace` pick the newest session file NOT in that snapshot. Also validate that the picked file's content references the current plan (echo `plan.stdin_payload` first/last char or hash into the comparison) — mirror the `_rollout_matches_plan` pattern from `codex.py:664-715`.

## HIGH-RISK 2 — Codex prompt-echo absorption

**File:** `scripts/agent_runtime/adapters/codex.py:374-381`

Problem: `parse_json_events` is fed `stdout + stderr + rollout_trace` raw. Codex echoes user prompts to stderr. Writer prompts contain JSON tool-use examples (to teach the model the format). Those parse cleanly via `_looks_like_tool_line` and land in `Result.tool_calls` as if they were real calls. Systematic false negatives for codex-tools.

Fix (per reviewer, two options — prefer simpler):
- **Simpler (recommended):** only feed `rollout_trace` to `parse_json_events` for tool calls. The rollout file is authoritative and prompt-echo-free for tool_use events. Stderr/stdout still useful for rate-limit detection but should not contribute to tool_calls.
- **Alternative:** strip the prompt echo from stderr (limit stderr parsing to the post-last-divider region) before `parse_json_events`.

Pick the simpler one and document why.

## HIGH-RISK 3 — Claude format-fragility

**Files:** `scripts/build/linear_pipeline.py:1719-1727` × `scripts/agent_runtime/adapters/claude.py:265-268,332`

Problem: `_runtime_tool_config` forces `output_format=stream-json` today, but `parse_response` silently returns `tool_calls=[]` if events fail to parse and falls back to `effective_stdout = stdout.strip()`. If anything flips output to `text`, every cited tool becomes a theatre violation — wholesale false positives for claude-tools.

Fix (per reviewer): in `parse_response`, when the requested format was `stream-json` and events are empty but stdout is non-empty, log a loud warning and FAIL CLOSED (raise an explicit error). Or assert in `_runtime_tool_config` that the format isn't overridden away. Pick the assert (simpler, fails earlier).

## Tests (regression — reviewer recommended)

`tests/test_trace_capture_no_contamination.py` (NEW):

- `test_gemini_session_does_not_leak_across_invocations`: simulate a previous Gemini session file in `~/.gemini/tmp/<cwd.name>/chats/`. Run `build_invocation` + `_read_latest_session_trace`. Assert the previous file is NOT picked up.
- `test_codex_prompt_echo_does_not_appear_in_tool_calls`: feed a stderr fixture containing a JSON tool-use example (mimicking Codex's prompt echo). Assert `Result.tool_calls` does not include those echoed names.
- `test_claude_text_output_fails_closed`: invoke claude adapter with `output_format=text`. Assert it raises (or assert that `_runtime_tool_config` rejects the override at config time).

## Validation

```bash
.venv/bin/pytest tests/test_trace_capture_no_contamination.py -v
.venv/bin/pytest tests/test_runner_tool_calls.py tests/test_detect_tool_theatre_integration.py -v  # regression
.venv/bin/ruff check scripts/agent_runtime/
.venv/bin/python scripts/build/v7_build.py a1 my-morning --writer claude-tools --dry-run  # smoke
```

## PR

Title: `fix(trace-capture): Gemini contamination + Codex prompt-echo + Claude format-fragility (#1768)`

PR body must include:
- Brief recap of all 3 HIGH-RISK findings + fix applied
- Confirmation that the new regression tests assert the bugs cannot return
- `Closes #1768`

**NO auto-merge.** Orchestrator (Claude) reviews + merges after a follow-up adversarial Claude review on the diff.

## Get adversarial review

```bash
git diff origin/main..HEAD > /tmp/1768-diff.txt
.venv/bin/python scripts/delegate.py dispatch \
    --agent claude --model claude-opus-4-7 --effort xhigh --mode read-only \
    --task-id 1768-fix-review --hard-timeout 600 \
    --prompt "Review fix for #1768 (3 HIGH-RISK trace-capture bugs). Read /tmp/1768-diff.txt. Verify each of the 3 fixes lands correctly: (1) Gemini snapshot-based session selection prevents cross-contamination, (2) Codex tool-call extraction reads rollout-only or strips prompt echo, (3) Claude fails closed on format mismatch. Test each via the new regression tests in tests/test_trace_capture_no_contamination.py. Tag findings BLOCK / NIT / OK. <500 words."
```

Apply feedback. Commit with `Reviewed-By: claude-opus-4-7 (1768-fix-review)` trailer.
