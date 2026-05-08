# Codex dispatch brief — #1798 MCP init observability

**Issue:** https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1798
**Why this matters now:** A1 bakeoff blocked. `.mcp.json` was misconfigured (`/sse` instead of `/mcp`). Writer dispatch swallowed the failure → 4-minute writer pass produced 0 tool calls + fabricated citations. A second bakeoff was wasted to discover this. Without observability instrumentation, the next silent MCP failure costs another bakeoff cycle to diagnose.

## Worktree (already prepared by dispatcher)

The dispatcher has already created your worktree at `.worktrees/dispatch/codex/1798-mcp-observability/` on branch `codex/1798-mcp-observability`, branched from `origin/main`. You start inside it. Do NOT `cd` out, do NOT create a new branch in the main checkout.

## Goal

Make MCP wiring failures **loud and immediate** in the writer dispatch path:

1. Add a `mcp_config_resolved` event when the dispatch resolves which MCP servers will be wired (success path AND empty-resolution path).
2. Add a `mcp_runtime_init` event when codex's stdout/stderr reveals MCP server init outcomes at runtime.
3. Add a pre-flight assertion: if a writer has the `-tools` suffix (declaring MCP intent) and the resolver returns no servers, raise `LinearPipelineError` BEFORE invoking codex.

Net effect: a future `.mcp.json` typo or unreachable server surfaces as a hard fail-fast with a structured event, not a silent 4-minute writer pass producing zero tool calls.

## Files to touch

### 1. `scripts/agent_runtime/tool_config.py`

`build_mcp_tool_config()` (lines 63-95) currently returns `None` silently in three failure modes:
- `.mcp.json` unreadable → `_load_mcp_config` returns None → return None
- `mcpServers` missing/empty → return None
- Requested server names not present in `mcpServers` → return None (selected dict is empty)

Refactor to return a `(config_dict, diagnostics)` tuple instead. `diagnostics` is a dict: `{"requested_servers": [...], "resolved_servers": [...], "config_path": "...", "resolution_status": "ok" | "config_missing" | "config_empty" | "servers_not_found", "missing_server_names": [...]}`. The current callers must adapt.

Backwards-compat note: this is internal to the agent_runtime layer. The only external caller is `linear_pipeline._runtime_tool_config`. Do NOT change the dict-shape returned to codex itself; only change the function's Python return signature.

### 2. `scripts/build/linear_pipeline.py`

`_runtime_tool_config()` (lines 1726-1738) currently:
```python
if agent_label == "codex-tools":
    codex_tools = build_mcp_tool_config("codex", mcp_servers=["sources"])
    if codex_tools:
        tool_config.update(codex_tools)
```

Change to:
- Receive an `event_sink` parameter (already plumbed through `invoke_writer`).
- After calling `build_mcp_tool_config`, emit `mcp_config_resolved` event with the diagnostics dict from change 1.
- If the writer name ends with `-tools` AND `diagnostics["resolved_servers"]` is empty AND `diagnostics["requested_servers"]` is non-empty → raise `LinearPipelineError(f"Writer {agent_label!r} requested MCP servers {requested!r} but resolver returned none ({status}). Refusing to dispatch tool-less.")`.

Then update `invoke_writer()` (line 1741) to thread `event_sink` into `_runtime_tool_config`.

The `event_sink` callable is already used elsewhere in this file (search for `event_sink(` to see the call signature: `event_sink(event_name, **kwargs)`).

### 3. `scripts/agent_runtime/runner.py`

The runner's `invoke()` function spawns the codex subprocess and captures its stdout. Today, MCP-init log lines from codex (e.g. `mcp: sources/verify_words started`) flow through but no `mcp_runtime_init` events get emitted on the writer JSONL.

Two patterns to detect from codex output:
- **Success:** `mcp: <server>/<tool> started` and `mcp: <server>/<tool> (completed)` — these confirm MCP is reachable. Aggregate the first occurrence per server: emit one `mcp_runtime_init` event with `status: "ready"` per server seen.
- **Failure:** look at codex's actual error output for failed MCP init. **You will need to run an experiment** to capture what codex emits when it can't reach an MCP server. Try this from your worktree (after worktree setup):
  ```bash
  # Briefly point .mcp.json at an unreachable URL (in worktree only)
  jq '.mcpServers.sources.url = "http://127.0.0.1:9999/sse"' .mcp.json > /tmp/broken.mcp.json
  cp /tmp/broken.mcp.json .mcp.json
  echo 'Hello' | codex exec --dangerously-bypass-approvals-and-sandbox --enable multi_agent -C "$PWD" - 2>&1 | head -100
  git checkout .mcp.json
  ```
  Capture the error pattern codex emits and grep for it in the runner's stdout parser. Document what you found in the commit message.

If codex's error format is too noisy or unpredictable, fall back to a TIMEOUT-based heuristic: if no `mcp: <server>/...started` line appears within N seconds of subprocess spawn while MCP servers were configured, emit `mcp_runtime_init` with `status: "timeout"`. Document the chosen strategy.

### 4. Tests — `tests/test_mcp_init_observability.py` (new file)

Add tests covering:
- `build_mcp_tool_config` returns correct diagnostics dict for each of: ok, config_missing, config_empty, servers_not_found
- `_runtime_tool_config` raises `LinearPipelineError` for `codex-tools` when no servers resolved
- `_runtime_tool_config` emits `mcp_config_resolved` event via the event_sink in success path
- Pre-flight refuses to dispatch tool-less when `-tools` writer is unconfigured

Use `tmp_path` + monkey-patched `_DEFAULT_MCP_CONFIG_PATH` to inject controlled `.mcp.json` fixtures. Do NOT touch the real `.mcp.json` from tests.

### 5. Doc note — `docs/best-practices/`

Add a short section to `docs/best-practices/agent-cooperation.md` (or create `docs/best-practices/mcp-observability.md` if cleaner) documenting:
- The two new events (`mcp_config_resolved`, `mcp_runtime_init`)
- The pre-flight assertion behavior
- How to debug "writer produced 0 tool calls" using these events

## Acceptance criteria (verbatim from the issue comment)

- [ ] Three events above are emitted on the writer JSONL stream (`mcp_config_resolved`, `mcp_runtime_init` ready, `mcp_runtime_init` failed/timeout)
- [ ] Pre-flight assertion fires when MCP is requested but unconfigured
- [ ] Test fixture exercises the failure path and asserts the `LinearPipelineError` + the `mcp_config_resolved` event
- [ ] No regression on existing bakeoff runs that DO have MCP wired correctly (smoke-test by running `.venv/bin/python scripts/audit/bakeoff_run.py --bakeoff-dir /tmp/bakeoff-smoke --level a1 --slug my-morning --writers codex-tools --writers-only` — expect it to FAIL on the same `.mcp.json` config we have today, but to fail FAST at pre-flight with the new error, NOT 4 minutes into a tool-less writer pass)
- [ ] Doc note added

## Numbered execution steps

1. **Verify worktree** — `git rev-parse --abbrev-ref HEAD` must print `codex/1798-mcp-observability`. `pwd` must end with `.worktrees/dispatch/codex/1798-mcp-observability`. If not, STOP — something is wrong, do not proceed.
2. **Read context** — `scripts/agent_runtime/tool_config.py`, `scripts/build/linear_pipeline.py:1726-1780`, `scripts/agent_runtime/runner.py`. Search the linear_pipeline for `event_sink(` to learn the call signature. Read `audit/bakeoff-2026-05-08-codex-only/gpt55.write.jsonl` for the JSONL event style.
3. **Run the broken-MCP experiment** described in §3 above to capture codex's failure log pattern. Document what you saw.
4. **Implement** the changes in §1, §2, §3 in that order.
5. **Add tests** per §4. Run `.venv/bin/pytest tests/test_mcp_init_observability.py -v` until green.
6. **Smoke-test** the negative path against the current real `.mcp.json` (which still points at `/sse`):
   ```bash
   .venv/bin/python scripts/audit/bakeoff_run.py \
     --bakeoff-dir /tmp/bakeoff-smoke-1798 \
     --level a1 --slug my-morning \
     --writers codex-tools --writers-only 2>&1 | head -40
   ```
   This should fail FAST (within ~5 seconds) at pre-flight with `LinearPipelineError`, NOT spend 4 minutes producing tool-less writer output. If it fails fast → success. If it spends minutes → pre-flight assertion didn't fire, debug.
7. **Lint** — `.venv/bin/ruff check scripts/ tests/` and fix any issues.
8. **Commit** — single conventional commit:
   ```
   feat(observability): instrument MCP init in writer dispatch (#1798)

   Three new events on writer JSONL: mcp_config_resolved, mcp_runtime_init,
   plus a pre-flight LinearPipelineError when -tools writers have no MCP
   servers resolved. Eliminates the 4-min silent tool-less writer pass that
   wasted today's A1 bakeoff retry.

   - tool_config.build_mcp_tool_config now returns (config, diagnostics)
   - linear_pipeline._runtime_tool_config emits events + asserts
   - runner parses codex stdout for mcp: <server>/... lines
   - Tests in tests/test_mcp_init_observability.py
   - Doc note in docs/best-practices/agent-cooperation.md

   Closes #1798
   ```
9. **Push** — `git push -u origin codex/1798-mcp-observability`
10. **Create PR** — `gh pr create --title "feat(observability): instrument MCP init in writer dispatch (#1798)" --body "..."` referencing this brief and the issue. Do NOT enable auto-merge.

## What NOT to do

- Do not change `.mcp.json` itself in this PR. The config fix is a separate, follow-up 1-line commit on main once this PR is merged + verified.
- Do not change the dict shape passed to codex's `--config` flag (the inner `mcpServers` JSON). Only change Python return signatures and add events.
- Do not regenerate `audit/bakeoff-2026-05-08-codex-only/` — that's main-branch artifact data, leave it alone.
- Do not rewrite the existing JSONL event-emission patterns. Match the existing style (see `writer_cot_emit`, `writer_end_gate`, `writer_tool_theatre` in linear_pipeline.py for examples of `ts: ISO`, `event: snake_case`, structured fields).
- Do not enable auto-merge on the PR. Claude will adversarial-review then merge manually.

## Output expected

A single PR on branch `codex/1798-mcp-observability` ready for adversarial review. PR description should include the captured codex error pattern from step 3 (so the next developer knows what failure modes the runtime parser handles).
