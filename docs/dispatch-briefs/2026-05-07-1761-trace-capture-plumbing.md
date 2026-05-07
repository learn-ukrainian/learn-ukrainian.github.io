# Codex dispatch brief — #1761 trace-capture plumbing

> **Worktree:** `.worktrees/dispatch/codex/1761-trace-capture`
> **Branch:** `codex/1761-trace-capture`
> **Base:** `main`
> **Mode:** danger
> **Effort:** medium
> **Hard timeout:** 7200s (2h)
> **Reviewer:** Claude (headless adversarial — now unblocked since #1760 merged)

## Worktree instructions (mandatory)

```bash
git worktree add -b codex/1761-trace-capture .worktrees/dispatch/codex/1761-trace-capture
cd .worktrees/dispatch/codex/1761-trace-capture
```

Main checkout stays on `main`. Don't branch in main checkout — HARD project rule (`.claude/rules/delegate-must-use-worktree.md`).

## Goal

Make `_runtime_tool_calls()` actually return data. Currently it always returns `[]` because no adapter populates `tool_calls` / `mcp_tool_calls` on the Result. This breaks the `detect_tool_theatre()` gate (#1720 strand 1, PR #1726): every honest writer who calls tools gets false-flagged because the runtime never captured the calls.

This is a **bakeoff blocker.** Without trace-capture, the next bakeoff produces ambiguous signal and writer-selection can't proceed.

## Diagnosis (already done by orchestrator — don't re-investigate)

```bash
grep -n "tool_calls" scripts/agent_runtime/runner.py
# (empty — runner doesn't expose the field)

grep -rln "tool_calls" scripts/agent_runtime/adapters/
# (empty — no adapter populates the field)

grep -A 3 "_runtime_tool_calls" scripts/build/linear_pipeline.py
# Confirms: detect_tool_theatre always receives []
```

## Implementation

### Files to touch

- `scripts/agent_runtime/runner.py` — add a `tool_calls: list[dict[str, Any]]` field to the Result dataclass (or whatever shape it currently returns). Default `[]`.
- `scripts/agent_runtime/adapters/claude.py` — parse Claude CLI output for tool-use events (each `claude -p` invocation prints them as JSON when `--output-format stream-json` or similar). Populate `tool_calls`.
- `scripts/agent_runtime/adapters/gemini.py` — gemini-cli emits tool calls in its transcript. Parse and populate.
- `scripts/agent_runtime/adapters/codex.py` — codex CLI emits tool-call telemetry in its JSONL stream. Parse and populate.
- `tests/test_runner_tool_calls.py` (new) — unit tests per adapter with fixture CLI output.
- `tests/test_detect_tool_theatre_integration.py` (new) — integration test: dry-run a writer that calls `verify_words`, assert `phase_writer_summary.tool_calls_total > 0` and `tool_theatre_violations == []`.

### Result shape

Each entry in `tool_calls` MUST include:
```python
{
    "name": str,              # canonical tool name, e.g. "mcp__sources__verify_words"
    "arguments": dict,        # the arguments passed
    "output_summary": str,    # truncated to 500 chars; never the raw output (could be huge or contain user data)
    "timestamp": str,         # ISO 8601
}
```

**Critical security:** never store the full tool output in `tool_calls`. Only a 500-char summary. Tool outputs can contain user content, API keys, file contents — keeping them in telemetry would be a leak.

### Adapter parsing strategy

Each CLI emits tool calls in a different format. Approach:

1. **Claude:** invoke with `--output-format stream-json` (already used in some places — check `scripts/agent_runtime/adapters/claude.py`). Parse the JSON stream for `tool_use` events.
2. **Gemini:** gemini-cli `--debug` emits structured tool-call lines. Parse them.
3. **Codex:** codex CLI emits JSONL events. Parse for `tool_call` events.

If any CLI doesn't emit machine-readable tool-call telemetry, document the gap in the PR body and fall back to `tool_calls = []` with a clear warning event in the runner. Do NOT fake it.

### Risks to address

1. **Tool output size:** must be summarized, not full. If `output_summary > 500 chars`, truncate with `[...truncated]` suffix.
2. **PII in arguments:** arguments dict could contain user prompts. Store as-is (it's already in our pipeline) but note in the docstring that callers must treat `tool_calls` as PII-bearing.
3. **CLI version drift:** parser must tolerate minor schema changes. Wrap in try/except per-event and emit a warning event for unparseable lines instead of crashing.
4. **Performance:** parsing should be O(events), not O(events²). Use streaming JSON parser if the output is large.

### Tests

- `test_claude_adapter_parses_tool_use_events` — fixture: real Claude stream-json output with 2 tool_use events. Assert `result.tool_calls` has 2 entries with correct names + args.
- `test_gemini_adapter_parses_tool_calls` — same shape, gemini debug output fixture.
- `test_codex_adapter_parses_tool_calls` — same shape, codex JSONL fixture.
- `test_tool_call_output_summary_truncation` — feed a 10KB tool output, assert summary is 500 chars + `[...truncated]`.
- `test_unparseable_tool_event_emits_warning_not_crash` — feed malformed JSON, assert no exception + warning event emitted.
- `test_runtime_tool_calls_now_returns_real_data` — integration: dry-run V7 with a writer that calls `verify_words`, assert `_runtime_tool_calls(result)` returns ≥1 entry with name `verify_words` (or `mcp__sources__verify_words` after canonicalization).

### Validation before opening PR

```bash
.venv/bin/pytest tests/test_runner_tool_calls.py tests/test_detect_tool_theatre_integration.py -v
.venv/bin/pytest tests/test_writer_correction_no_op_diagnostic.py tests/test_prompt_cot_tier1_scaffolding.py -v  # regression
.venv/bin/ruff check scripts/agent_runtime/
.venv/bin/python scripts/build/v7_build.py a1 my-morning --writer claude-tools --dry-run  # smoke
```

The smoke test must show `phase_writer_summary` with non-empty `tool_calls_total` if the writer called any tools.

### Mandatory adversarial review

Now that #1754 keychain fix has merged (commit `cb231e001f`), headless Claude dispatch works. Run the cross-family review:

```bash
git -C .worktrees/dispatch/codex/1761-trace-capture diff origin/main..HEAD > /tmp/1761-diff.txt
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-claude \
  "Adversarial review for #1761. Read /tmp/1761-diff.txt. Focus: (A) is tool_call PII / output-leak handled? (B) does each adapter degrade gracefully on CLI version drift? (C) is the result shape stable enough that downstream consumers (detect_tool_theatre, future telemetry) don't need to change? (D) test gaps?" \
  --task-id 1761-trace-capture-review \
  --model claude-opus-4-7
```

Apply feedback. Commit with `Reviewed-By: claude-opus-4-7 (1761-trace-capture-review)` trailer.

### PR

Open as `feat(agent_runtime): expose tool_calls on runner Result for trace-capture (#1761)`.

PR body must include:
- Root-cause one-paragraph summary
- The 3-adapter parsing strategy
- Confirmation that tool outputs are summarized (not stored full)
- Smoke test output showing real tool_calls captured
- `Closes #1761`

**NO auto-merge.** Orchestrator (Claude) reviews CI + body, then merges.
