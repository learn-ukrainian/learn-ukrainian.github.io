# Codex fix-up brief — PR #1802 missed callers + test breakage

**Issue:** https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1798
**PR:** https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/1802
**Why this matters now:** PR #1802 changed `build_mcp_tool_config` signature from `dict | None` to `tuple[dict | None, dict[str, Any]]` and updated 2 callers but missed a third (`scripts/build/dispatch.py`). Also added a fail-fast `LinearPipelineError` pre-flight that breaks 2 pre-existing tests in `tests/test_textbook_grounding_gate.py` whose fixtures don't set up MCP. CI is RED. Five test failures, all mechanical to fix.

The original brief explicitly asked you to grep ALL callers — that step was skipped. Don't skip it again.

## Worktree (already prepared by dispatcher)

The dispatcher has created a worktree at `.worktrees/dispatch/codex/1798-fix-up-callers/` on a new branch `codex/1798-fix-up-callers`, branched from `origin/codex/1798-mcp-observability` (NOT origin/main — this PR's branch). You start inside it. The PR's existing 8 changes are already in your tree.

When you finish, you will **force-push back to `codex/1798-mcp-observability`** (the PR's branch) — see step 9. This updates the existing PR in place rather than creating a second PR.

## What pytest told us — five failing tests

```
FAILED tests/test_dispatch.py::TestDispatchAgent::test_gemini_dispatch_rate_limit_falls_through_to_oauth
   ValueError: dictionary update sequence element #0 has length 1; 2 is required
FAILED tests/test_dispatch.py::TestDispatchAgent::test_claude_tools_dispatch
   AssertionError: assert 'mcp_config_path' in (..., {'requested_servers': [], ...})
FAILED tests/test_dispatch.py::TestDispatchAgent::test_gemini_dispatch_honors_custom_per_call_cap
   ValueError: dictionary update sequence element #0 has length 1; 2 is required
FAILED tests/test_textbook_grounding_gate.py::test_invoke_writer_persists_tool_trace
   LinearPipelineError: Writer 'codex-tools' requested MCP servers ['sources'] but resolver returned none
FAILED tests/test_textbook_grounding_gate.py::test_invoke_writer_appends_tool_trace
   LinearPipelineError: same as above
```

## Root causes

**Failure A — `scripts/build/dispatch.py` is the third caller.** Lines 477 (claude path) and 591 (gemini path) call `build_mcp_tool_config()` and assign the result directly to `tool_config`. After the signature change, `tool_config` is now a 2-tuple, not a dict — downstream `.update()` and membership checks blow up.

```python
# Line 477:
tool_config = (
    build_mcp_tool_config("claude", allowed_tools=allowed_tools)
    if mcp_tools and allowed_tools
    else None
)

# Line 591:
tool_config = (
    build_mcp_tool_config("gemini", mcp_servers=["rag"])
    if mcp_tools
    else None
)
```

**Failure B — pre-existing tests now hit the new pre-flight.** `tests/test_textbook_grounding_gate.py:142` (`test_invoke_writer_persists_tool_trace`) and `tests/test_textbook_grounding_gate.py:331` (`test_invoke_writer_appends_tool_trace`) call `linear_pipeline.invoke_writer(..., "codex-tools", cwd=tmp_path, invoker=mock_invoker, ...)`. `tmp_path` has no `.mcp.json` → resolver returns `config_missing` → new pre-flight raises `LinearPipelineError` BEFORE the mock invoker runs.

## Fix plan — 4 changes, ~25 LOC total

### Change 1: `scripts/build/dispatch.py:477` (claude branch)

Unpack the tuple. The diagnostics dict is currently unused for this path (no event_sink threaded yet — file as a follow-up but DO NOT add observability here).

```python
tool_config_result = (
    build_mcp_tool_config("claude", allowed_tools=allowed_tools)
    if mcp_tools and allowed_tools
    else None
)
tool_config = tool_config_result[0] if tool_config_result else None
```

OR cleaner if you prefer destructuring:

```python
if mcp_tools and allowed_tools:
    tool_config, _diagnostics = build_mcp_tool_config(
        "claude",
        allowed_tools=allowed_tools,
    )
else:
    tool_config = None
```

Use whichever style matches the surrounding code's idiom — read 50 lines of context first.

### Change 2: `scripts/build/dispatch.py:591` (gemini branch)

Same pattern. NOTE: this caller passes `mcp_servers=["rag"]`. The MCP server was renamed `rag → sources` per `.claude/rules/mcp-sources-and-dictionaries.md`. **Do NOT fix the rename here** (out of scope for #1798). Leave the stale name and add an inline `# TODO(#issue-NEW): rename rag → sources, see .claude/rules/mcp-sources-and-dictionaries.md`. Then file a tracking issue at the end (step 10).

```python
if is_gemini:
    runtime_mode = "workspace-write"
    if mcp_tools:
        # TODO(#NEW): rename "rag" → "sources" per mcp-sources-and-dictionaries.md
        tool_config, _diagnostics = build_mcp_tool_config("gemini", mcp_servers=["rag"])
    else:
        tool_config = None
```

### Change 3: `tests/test_textbook_grounding_gate.py` — fix `test_invoke_writer_persists_tool_trace` (line 142)

The cleanest fix is to write a valid `.mcp.json` inside `tmp_path` and monkeypatch the resolver to use it. The mock invoker doesn't actually call out to MCP, so the URL doesn't need to be reachable.

Add a helper at the top of the file (or near the test):

```python
def _seed_mcp_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Seed a minimal valid .mcp.json so the new pre-flight passes for codex-tools."""
    config_path = tmp_path / ".mcp.json"
    config_path.write_text(json.dumps({
        "mcpServers": {
            "sources": {"type": "streamable-http", "url": "http://127.0.0.1:8766/mcp"}
        }
    }), encoding="utf-8")
    from scripts.agent_runtime import tool_config as tc_mod
    monkeypatch.setattr(tc_mod, "_DEFAULT_MCP_CONFIG_PATH", config_path)
    tc_mod._load_mcp_config.cache_clear()
```

Then update the two failing tests to accept `monkeypatch` and call the helper:

```python
def test_invoke_writer_persists_tool_trace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_mcp_config(tmp_path, monkeypatch)
    # ... rest unchanged
```

You'll need `import json` and `import pytest` at the top if not already present.

### Change 4: `tests/test_textbook_grounding_gate.py` — fix `test_invoke_writer_appends_tool_trace` (line 331)

Same monkeypatch pattern. Use the same `_seed_mcp_config` helper.

## Numbered execution steps

1. **Verify worktree** — `git rev-parse --abbrev-ref HEAD` must print `codex/1798-fix-up-callers`. `pwd` must end with `.worktrees/dispatch/codex/1798-fix-up-callers`. If not, STOP — do not proceed.

2. **Sanity-check the base** — `git log --oneline -5` should show `feat(observability): instrument MCP init in writer dispatch (#1798)` as the most recent commit. If not, the branch base is wrong; STOP.

3. **Grep ALL callers of `build_mcp_tool_config`** — `git grep "build_mcp_tool_config" -- '*.py'`. Confirm 4 caller sites (linear_pipeline.py:1731, dispatch.py:477, dispatch.py:591, wiki/review.py:258). If you find a 5th caller this brief missed, fix it too.

4. **Read context** — `scripts/build/dispatch.py` lines 460-620, `tests/test_textbook_grounding_gate.py` lines 130-380. Read enough surrounding code to choose the idiomatic destructuring style for each call site.

5. **Apply Change 1** (dispatch.py:477).

6. **Apply Change 2** (dispatch.py:591). Include the `# TODO(#NEW)` inline comment.

7. **Apply Changes 3 + 4** (test_textbook_grounding_gate.py). Add the `_seed_mcp_config` helper once and reuse it in both tests.

8. **Run pytest locally** to verify all 5 previously-failing tests pass + nothing else broke:
   ```
   .venv/bin/pytest tests/test_dispatch.py tests/test_textbook_grounding_gate.py tests/test_mcp_init_observability.py tests/test_agent_runtime_tool_config.py tests/test_v7_writer_dispatch.py -v
   ```
   All must pass. If anything else regresses, fix it.

9. **Lint** — `.venv/bin/ruff check scripts/ tests/`.

10. **File the rename follow-up issue** — `gh issue create --title "[refactor] dispatch.py:591 still passes mcp_servers=['rag']; rename to 'sources'" --body "..."`. Reference `.claude/rules/mcp-sources-and-dictionaries.md`. This is the issue number you put in the `# TODO(#NEW)` comment from Change 2 — go back and replace `#NEW` with the actual issue number you just got.

11. **Commit** — single conventional commit:
    ```
    fix(observability): unpack tuple at all build_mcp_tool_config callers (#1798)

    PR #1802 missed the third caller in scripts/build/dispatch.py and the
    pre-flight assertion broke 2 pre-existing tests that don't set up MCP
    fixtures. Pytest was red for 5 tests; this restores green.

    - dispatch.py: 2 call sites unpack the new (config, diagnostics) tuple
    - test_textbook_grounding_gate.py: 2 tests now seed a .mcp.json fixture
      so the new pre-flight resolves cleanly

    Tracking the dispatch.py:591 stale "rag"/"sources" rename in #NNNN.

    Refs #1798
    ```

12. **Force-push back to the PR branch** — this updates PR #1802 in place:
    ```
    git push --force-with-lease origin codex/1798-fix-up-callers:codex/1798-mcp-observability
    ```
    `--force-with-lease` (NOT `--force`) protects against losing concurrent commits. If the lease check fails, STOP and report — do not blindly retry.

13. **Verify** — `gh pr view 1802 --json statusCheckRollup --jq '.statusCheckRollup[] | "\(.name): \(.status)"'` should show CI restarting. Don't wait for it; the orchestrator will watch.

## What NOT to do

- Do NOT fix the `rag` → `sources` rename inline (out of scope; tracked separately).
- Do NOT add `mcp_config_resolved` event emission to dispatch.py — that's a follow-up enhancement, not in scope for this fix-up.
- Do NOT create a second PR. Force-push to the existing branch updates PR #1802.
- Do NOT use `--force` (without `-with-lease`) — risks losing concurrent commits.
- Do NOT enable auto-merge.
- Do NOT change anything in `scripts/agent_runtime/` or `scripts/build/linear_pipeline.py` — those are correct as-is in PR #1802.

## Output expected

PR #1802 updated with one additional commit. CI should turn green within ~5 minutes after force-push.
