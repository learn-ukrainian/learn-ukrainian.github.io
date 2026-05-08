# Codex dispatch brief — wire MCP for ALL writer dispatches (claude-tools, gemini-tools, codex-tools)

**Why this matters now:** PR #1802 instrumented MCP wiring for `codex-tools` and verified it end-to-end. The other two writers (`claude-tools`, `gemini-tools`) have NO MCP wiring path in `_runtime_tool_config`. Result: any bakeoff comparing them produces garbage signal — claude-tools sees zero tools (Claude Code requires explicit `--mcp-config`); gemini-tools falls back to a stale `.gemini/settings.json` with the OLD server name `rag` (renamed to `sources` per `.claude/rules/mcp-sources-and-dictionaries.md`) and an SSE endpoint that may or may not work.

The user explicitly stated: **"without [MCP wiring for all 3 agents] there is no point doing bakeoff."** This is the gating fix before the writer-prompt-theatre / writer-selection investigation can resume.

## Worktree (already prepared by dispatcher)

The dispatcher created your worktree at `.worktrees/dispatch/codex/1809-mcp-wiring-all-writers/` on branch `codex/1809-mcp-wiring-all-writers`, branched from `origin/main`. You start inside it. Do NOT `cd` out, do NOT create a new branch in the main checkout.

## Goal

Every writer dispatch must wire MCP correctly + emit `mcp_config_resolved` telemetry + fail-fast if the requested servers don't resolve.

After this lands, the per-writer smoke test (step 8 below) must show:

```
mcp_config_resolved: writer='claude-tools', resolved_servers=['sources'], status='ok'
mcp_config_resolved: writer='gemini-tools', resolved_servers=['sources'], status='ok'
mcp_config_resolved: writer='codex-tools', resolved_servers=['sources'], status='ok'   # already works
```

For ALL three, the pre-flight `LinearPipelineError` MUST NOT raise.

## Files to touch

### 1. `scripts/build/linear_pipeline.py` — `_runtime_tool_config` (lines ~1726-1755)

Currently:

```python
def _runtime_tool_config(agent_label: str, *, event_sink=None) -> dict[str, Any]:
    tool_config: dict[str, Any] = {"output_format": "stream-json"}
    if agent_label == "codex-tools":
        from scripts.agent_runtime.tool_config import build_mcp_tool_config
        codex_tools, diagnostics = build_mcp_tool_config("codex", mcp_servers=["sources"])
        _emit(event_sink, "mcp_config_resolved", writer=agent_label, **diagnostics)
        # ...pre-flight + tool_config.update...
```

**Refactor** to handle all three `-tools` writers via a single shared resolver-and-pre-flight block. Suggested shape (adapt to match the existing code's idiom — read 50 lines of context around it first):

```python
def _runtime_tool_config(agent_label: str, *, event_sink=None) -> dict[str, Any]:
    tool_config: dict[str, Any] = {"output_format": "stream-json"}
    if not agent_label.endswith("-tools"):
        # Non-MCP writer (e.g. plain "claude" / "gemini" / "codex" without
        # the -tools suffix) — no MCP wiring expected.
        return tool_config

    from scripts.agent_runtime.tool_config import build_mcp_tool_config

    if agent_label == "codex-tools":
        agent_kwargs = {"mcp_servers": ["sources"]}
    elif agent_label == "claude-tools":
        # Claude needs both mcp_config_path AND allowed_tools. The wildcard
        # exposes every mcp__sources__* tool the writer prompt may want.
        agent_kwargs = {
            "mcp_servers": ["sources"],
            "allowed_tools": "mcp__sources__*",
        }
    elif agent_label == "gemini-tools":
        agent_kwargs = {"mcp_servers": ["sources"]}
    else:
        raise LinearPipelineError(
            f"Unknown -tools writer {agent_label!r}; expected one of "
            f"codex-tools / claude-tools / gemini-tools."
        )

    canonical_agent = agent_label.split("-", 1)[0]
    mcp_dict, diagnostics = build_mcp_tool_config(canonical_agent, **agent_kwargs)
    _emit(event_sink, "mcp_config_resolved", writer=agent_label, **diagnostics)

    requested = diagnostics["requested_servers"]
    resolved = diagnostics["resolved_servers"]
    status = diagnostics["resolution_status"]
    if requested and not resolved:
        raise LinearPipelineError(
            f"Writer {agent_label!r} requested MCP servers {requested!r} "
            f"but resolver returned none ({status}). Refusing to dispatch tool-less."
        )
    if mcp_dict:
        tool_config.update(mcp_dict)

    assert tool_config.get("output_format") == "stream-json"
    return tool_config
```

Three things this does:
- Uses one shared diagnostics + pre-flight path for ALL three writers (no copy-paste drift).
- Drops the dead `endswith("-tools")` check inside the `==codex-tools` block (#1804 nit) — the early `return` at the top now makes it unnecessary.
- Adds an explicit unknown-writer LinearPipelineError so a future typo doesn't silently fall through to "tool-less but no error."

### 2. `.gemini/settings.json` — rename + transport check

Currently:

```json
{
  "mcpServers": {
    "rag": {
      "url": "http://127.0.0.1:8766/sse",
      "type": "sse"
    }
  }
}
```

**Two changes needed.** First, rename `rag → sources` (per `.claude/rules/mcp-sources-and-dictionaries.md` — the `rag` name was retired because the implementation isn't vector-RAG). Second, decide the transport.

**Run an empirical experiment** to decide transport. Codex headless cannot speak SSE (proven last night — that was the original #1790 bug). Gemini-cli's behavior is unknown to me. Test both:

```bash
# Test gemini-cli with streamable-http first
cat > /tmp/gemini-settings-http.json <<'EOF'
{"mcpServers": {"sources": {"url": "http://127.0.0.1:8766/mcp", "type": "streamable-http"}}}
EOF
mkdir -p /tmp/gemini-test-http && cp /tmp/gemini-settings-http.json /tmp/gemini-test-http/.gemini/settings.json 2>/dev/null || mkdir -p /tmp/gemini-test-http/.gemini && cp /tmp/gemini-settings-http.json /tmp/gemini-test-http/.gemini/settings.json
cd /tmp/gemini-test-http
gemini --approval-mode=yolo --skip-trust --allowed-mcp-server-names sources -p "Call mcp__sources__verify_words with words=['кіт']" 2>&1 | tail -20
```

Then test SSE the same way. **Whichever transport gemini-cli successfully invokes the tool with → use in `.gemini/settings.json`.** Capture which one worked in the PR description.

If BOTH work, prefer `streamable-http` for consistency with `.mcp.json`. If only SSE works, keep SSE — the MCP server preserves the `/sse` endpoint for backward compat per #1800.

### 3. `scripts/build/dispatch.py:591` — `rag → sources` rename (closes #1803)

Currently:

```python
tool_config, _diagnostics = build_mcp_tool_config("gemini", mcp_servers=["rag"])
```

Replace with:

```python
tool_config, _diagnostics = build_mcp_tool_config("gemini", mcp_servers=["sources"])
```

Drop the `# TODO(#1803)` comment that was added in the previous fix-up (since this PR closes it).

### 4. Tests — extend `tests/test_mcp_init_observability.py` to cover all three writers

The existing tests cover codex-tools. Add equivalents for claude-tools and gemini-tools:

- `test_runtime_tool_config_claude_tools_emits_resolution_event_success` — calls `_runtime_tool_config("claude-tools", event_sink=...)` with a seeded `.mcp.json`, asserts the event fires with `resolved_servers=['sources']` and the returned tool_config has `mcp_config_path` + `allowed_tools="mcp__sources__*"` keys.
- `test_runtime_tool_config_claude_tools_raises_when_unconfigured` — calls with empty `.mcp.json`, asserts `LinearPipelineError("...tool-less.")`.
- `test_runtime_tool_config_gemini_tools_emits_resolution_event_success` — analogous for gemini, asserts returned tool_config has `mcp_server_names=['sources']`.
- `test_runtime_tool_config_gemini_tools_raises_when_unconfigured` — analogous for gemini, asserts LinearPipelineError.
- `test_runtime_tool_config_unknown_tools_writer_raises` — calls with `"phantom-tools"`, asserts the new explicit-rejection LinearPipelineError fires.

Use the same `_seed_mcp_config` / monkeypatched `_DEFAULT_MCP_CONFIG_PATH` pattern from the existing tests.

Existing 8 tests must still pass.

### 5. `tests/test_v7_writer_dispatch.py` — extend smoke coverage

If this file has writer-dispatch happy-path tests for codex-tools, add parallel coverage for claude-tools and gemini-tools (same shape, different writer label). If not, skip.

## Acceptance criteria

- [ ] `_runtime_tool_config("claude-tools")` returns tool_config with `mcp_config_path` + `allowed_tools="mcp__sources__*"`, emits `mcp_config_resolved` event with `resolved_servers=['sources']`.
- [ ] `_runtime_tool_config("gemini-tools")` returns tool_config with `mcp_server_names=['sources']`, emits `mcp_config_resolved` event with `resolved_servers=['sources']`.
- [ ] `_runtime_tool_config("codex-tools")` still works unchanged.
- [ ] `.gemini/settings.json` updated: server renamed `rag → sources`, transport empirically validated.
- [ ] `scripts/build/dispatch.py:591` uses `mcp_servers=["sources"]`. Closes #1803.
- [ ] `tests/test_mcp_init_observability.py` covers all three writers (5 new tests per §4).
- [ ] All existing tests still pass.
- [ ] Smoke test (step 8) shows `mcp_config_resolved` for ALL three writers with `resolution_status: 'ok'`.

## Numbered execution steps

1. **Verify worktree** — `git rev-parse --abbrev-ref HEAD` must print `codex/1809-mcp-wiring-all-writers`. `pwd` must end with `.worktrees/dispatch/codex/1809-mcp-wiring-all-writers`. If not, STOP.

2. **Read context** — `scripts/build/linear_pipeline.py:1726-1800` (current `_runtime_tool_config` + `invoke_writer`); `scripts/agent_runtime/tool_config.py` (the resolver — already returns `(dict, diagnostics)`); `scripts/agent_runtime/adapters/claude.py:280-295` (the claude adapter's MCP wiring); `scripts/agent_runtime/adapters/gemini.py:215-235` (the gemini adapter's MCP wiring); `tests/test_mcp_init_observability.py` (existing test pattern).

3. **Run the gemini-transport experiment** described in §2 to decide which transport `.gemini/settings.json` should use. Capture exact output in a `/tmp/gemini-mcp-experiment.log` file you reference in the commit message.

4. **Implement §1** — refactor `_runtime_tool_config` per the suggested shape. Adapt to match existing code idioms.

5. **Implement §2** — update `.gemini/settings.json` based on the experiment outcome.

6. **Implement §3** — close out #1803 with the `rag → sources` rename.

7. **Implement §4 + §5** — add the 5 new tests in `test_mcp_init_observability.py` plus any parallel coverage in `test_v7_writer_dispatch.py`. Run them locally:
   ```
   .venv/bin/pytest tests/test_mcp_init_observability.py tests/test_v7_writer_dispatch.py tests/test_agent_runtime_tool_config.py tests/test_dispatch.py tests/test_textbook_grounding_gate.py -v
   ```
   ALL must pass. Fix any regression.

8. **Smoke test all three writers** — verify the resolver fires `mcp_config_resolved` for each writer label:
   ```
   .venv/bin/python -c "
   from scripts.agent_runtime.tool_config import _load_mcp_config
   from scripts.build.linear_pipeline import _runtime_tool_config
   _load_mcp_config.cache_clear()
   events = []
   for w in ['codex-tools', 'claude-tools', 'gemini-tools']:
       _load_mcp_config.cache_clear()
       events.clear()
       try:
           cfg = _runtime_tool_config(w, event_sink=lambda e, **f: events.append((e, f)))
           print(f'{w}: ok status={events[0][1][\"resolution_status\"]} resolved={events[0][1][\"resolved_servers\"]}')
       except Exception as exc:
           print(f'{w}: FAIL {exc}')
   "
   ```
   ALL three must print `ok status=ok resolved=['sources']`. If any prints `FAIL`, debug.

9. **Lint** — `.venv/bin/ruff check scripts/ tests/`.

10. **Commit** — single conventional commit:
    ```
    feat(mcp): wire MCP for claude-tools + gemini-tools writer dispatch (#1809)

    All three -tools writers (codex/claude/gemini) now go through one shared
    resolver-and-pre-flight block in _runtime_tool_config. Eliminates the
    silent tool-less paths for claude-tools and gemini-tools that were
    masking the writer-prompt-theatre signal.

    - linear_pipeline._runtime_tool_config: shared MCP resolver for all
      three writers + explicit unknown-writer LinearPipelineError + drop
      dead endswith("-tools") check (#1804 nit).
    - .gemini/settings.json: rename rag → sources + transport per
      empirical experiment (see commit body / experiment log).
    - dispatch.py:591: rag → sources (closes #1803).
    - test_mcp_init_observability.py: 5 new tests covering all three
      writer labels + unknown-writer rejection.

    Per-writer smoke verified: all three return resolution_status='ok'
    with resolved_servers=['sources'].

    Closes #1803, #1804
    Refs #1577 (curriculum reboot — unblocks bakeoff signal)
    ```

11. **Push** — `git push -u origin codex/1809-mcp-wiring-all-writers`.

12. **Create PR** — `gh pr create --title "feat(mcp): wire MCP for claude-tools + gemini-tools writer dispatch (#1809)" --body "..."` referencing this brief and the gating user requirement. Include the gemini-transport experiment outcome in the PR description. Do NOT enable auto-merge.

## What NOT to do

- Do NOT change `scripts/agent_runtime/tool_config.py` — the resolver is already correct (returns `(dict, diagnostics)` tuple, supports all three agents).
- Do NOT change `scripts/agent_runtime/adapters/*.py` — the adapters already accept the right tool_config keys; only the dispatch-side wiring is missing.
- Do NOT bump the MCP version or rename any tool prefixes — the rename `rag → sources` is for the SERVER NAME inside the MCP config, not the tool prefixes (`mcp__sources__*` was already correct).
- Do NOT enable auto-merge.

## Output expected

A single PR on branch `codex/1809-mcp-wiring-all-writers` ready for review. PR body must include the captured gemini-transport experiment results so the next developer knows why `.gemini/settings.json` uses whichever transport you chose.
