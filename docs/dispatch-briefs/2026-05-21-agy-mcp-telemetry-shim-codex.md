# Dispatch brief — agy MCP telemetry shim (run_command-curl → named-tool entries)

**Agent**: codex (gpt-5.5, xhigh)
**Mode**: danger
**Worktree**: `.worktrees/codex-agy-mcp-shim-2026-05-21`
**Task ID**: `agy-mcp-shim-2026-05-21`
**Created**: 2026-05-21

## Why

`agy` (Gemini Antigravity CLI 1.0.0) **does not load MCP servers as native plugins** despite our docs claiming otherwise. The morning 2026-05-21 handoff's claim that "agy + MCP works end-to-end via global mcp_config.json" was a **false positive** — the manual probe asked agy to introspect its capabilities ("call mcp_sources_verify_word"), and agy responded with plausible-looking text (correct VESUM tags for `стіл` from priors) without invoking any tool. `agy plugin list` still returns "No imported plugins"; `agy -p` introspection prompts produce verbose hallucinated content.

The **actually working** mechanism is `run_command` + `curl` against the MCP HTTP endpoint. The user verified this live with:

> Prompt: `Call mcp_sources_verify_word with word='ранок' and return ONLY the raw JSON response from the tool.`
> agy stdout (real):
> ```
> ● Bash(curl -s -X POST -H "Content-Type: application/json" \
>     -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "verify_word", "arguments": {"word": "ранок"}}}' \
>     http://127.0.0.1:8766/mcp)
>   ⎿  {"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"'ранок' — 3 match(es) in VESUM:..."}],"isError":false}}
> ```

So agy CAN invoke MCP, just via the `run_command` (Bash) primitive against the HTTP endpoint, not as a native MCP plugin tool call.

**The V7 integration gap.** The pipeline records `writer_tool_calls.json` by named tool. agy's curl-via-Bash invocation registers as a single `run_command` entry (if at all), not as `verify_word`, `search_text`, or `get_chunk_context`. Gates that depend on named-MCP-method evidence (`vesum_verified`, `textbook_grounding`, `mcp_tools_never_invoked`, the `tool_calls_total` runtime gate) therefore won't see agy's MCP activity even when it's happening. This is why the 2026-05-21 morning agy-tools build (a1/my-morning, branch `build/a1/my-morning-20260521-100244`) failed `mcp_tools_never_invoked` HARD — telemetry was blind to agy's actual tool usage.

User direction 2026-05-21: agy stays in V7 writer scope (Google AI Ultra account active for the project, unmetered Gemini quota). We need an adapter shim that bridges the curl-via-Bash → named-tool-telemetry gap.

## What

Build the shim in two coordinated layers:

### Layer 1 — Telemetry parser (agy adapter side)

Parse agy's `-p` stdout for the canonical Bash-tool-call markers and synthesize equivalent named-MCP-tool-call entries the pipeline will treat exactly like a native MCP call.

**Parsing surface** (verified shape from live agy output):
- Opening line: `● Bash(<command body, may span multiple lines>)` — `●` is U+25CF; the closing paren of the command is on either the same line or after a backslash-continuation
- Result line: `  ⎿  <stdout of the command>` — `⎿` is U+23BF; the result body MAY be multiple lines until the next blank line or next `●`
- Detection condition: the command body contains `curl` AND a URL matching `https?://(127\.0\.0\.1|localhost):8766/mcp\b`

**Synthesis:**
1. Extract the `-d` payload from the curl command. Tolerate both `-d '<json>'` and `--data <json>`; tolerate `-d @file` (rare; treat as a non-synthesizable entry and log a debug skip).
2. Parse the JSON-RPC envelope. Honor only `method == "tools/call"` for synthesis; ignore `initialize` / `tools/list` / `notifications/*` (those aren't writer-evidence calls).
3. Pull `params.name` (e.g. `verify_word`, `search_text`, `get_chunk_context`, `verify_words`, etc.) and `params.arguments` (the kwargs dict).
4. Pull the response JSON from the `⎿` result body. Honor `result.content[*].text` for the response body; tolerate `isError: true` and record as an error-result entry, do not skip.
5. Emit a `writer_tool_calls.json` entry matching the existing schema produced by other adapters — same keys, same types. Match against the gemini-tools / claude-tools entry shape exactly so downstream gates don't have to special-case.

Do NOT silently drop unparseable entries — emit a structured warning to stderr that the build wrapper can surface as `writer_correction_unparseable`-adjacent telemetry. Better to fail loudly than to under-count tool calls.

### Layer 2 — Writer-prompt directive (linear-write.md side)

agy needs explicit "use curl-MCP" instructions to trigger the right tool calls (the directive-prompt pattern that works; introspection-prompt pattern that fails). Add a writer-specific section to `scripts/build/phases/linear-write.md` that activates ONLY when the writer is `agy-tools`:

- Gate the section by writer kind (existing prompt template has `{WRITER_NAME}` or similar; if not, add the conditional block scaffolding in `linear_pipeline.py` where the prompt is assembled).
- Section content: explain that agy invokes MCP via curl, give the exact JSON-RPC envelope template, name each MCP method agy must call (one per the existing Pre-emit verification checklist at lines 618-645 of linear-write.md), and require agy to issue the curl via `run_command` (not via prose).
- Worked example using `verify_words` with two Ukrainian forms (covers the batched-call shape the gate expects).
- Forbid agy from generating "tool call" text that isn't an actual `run_command` Bash invocation — the parser only sees real bash invocations.

If the prompt template doesn't currently support per-writer conditional sections, add the minimum scaffolding (a `{WRITER_SPECIFIC_DIRECTIVES}` placeholder that the pipeline substitutes with the right block; defaults to empty for other writers).

### Touch points

1. **`scripts/agent_runtime/adapters/agy.py`**:
   - Extend `parse_response` to also produce `tool_calls` data alongside `response`. The current `ParseResult` may need an additional field (or use an existing one — check `ParseResult` shape in `scripts/agent_runtime/result.py`).
   - Add the bash-tool-call parser as a private helper (or extract to `scripts/agent_runtime/_agy_telemetry.py` if it's >50 LOC).

2. **`scripts/build/linear_pipeline.py`**:
   - Wherever `writer_tool_calls.json` is assembled, accept the agy adapter's synthesized entries.
   - If the prompt template doesn't already support per-writer sections, add minimal scaffolding.

3. **`scripts/build/phases/linear-write.md`**:
   - Add the `{WRITER_SPECIFIC_DIRECTIVES}` placeholder + the agy-specific directive block (only emitted when writer is `agy-tools`).

4. **Tests** (`tests/`):
   - Unit test the parser on a small fixture file containing the live-verified agy output shape (use the user's `ранок` example as canonical fixture, plus a `verify_words` batched example, plus an isError result, plus a malformed payload that should warn).
   - Integration test: feed a synthetic agy-tools stdout through the agent_runtime pipeline and assert `writer_tool_calls.json` ends up with the synthesized named entries.

## Don't

- Don't try to make agy load MCP as a native plugin. That requires upstream work from kubedojo / Antigravity team; out of scope.
- Don't synthesize tool calls from agy's prose-only output. Only `● Bash(...)` invocations against `127.0.0.1:8766/mcp` count.
- Don't widen the parser to capture non-MCP curls. The MCP endpoint URL is the qualifying signal.
- Don't change other adapters (claude.py, codex.py, gemini.py, hermes_*.py).

## Verification before commit

```
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/ruff check scripts/agent_runtime/ scripts/build/
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python -m pytest tests/ -k 'agy or agent_runtime or linear_pipeline' -v --tb=short
```

All green required before commit.

## Commit + PR shape

- **Branch**: `feat/agy-mcp-telemetry-shim-2026-05-21`
- **Single commit**: `feat(agy-adapter): synthesize named-MCP tool calls from run_command(curl) invocations`
- **PR title**: `feat(agy-adapter): bridge curl-via-Bash MCP usage to named-tool telemetry`
- **PR body**: explain the user-verified mechanism (curl marker shape), the V7 integration gap, the two-layer shim, link this brief and `build/a1/my-morning-20260521-100244` as the witness build.
- **Do NOT auto-merge.** Orchestrator (Claude) reviews and merges after `gh pr checks {N} --watch` passes.

## Steps (mandatory)

1. `git worktree add -B feat/agy-mcp-telemetry-shim-2026-05-21 .worktrees/codex-agy-mcp-shim-2026-05-21 origin/main`
2. Read the live agy probe evidence in this brief carefully. Verify the marker characters (`●` U+25CF, `⎿` U+23BF) parse correctly in your environment before writing the regex.
3. Implement Layer 1 (telemetry parser) and Layer 2 (writer-prompt directive) per the spec above.
4. Run verification commands.
5. Single conventional commit.
6. `git push -u origin feat/agy-mcp-telemetry-shim-2026-05-21`
7. `gh pr create --title ... --body ...` (NO auto-merge).
8. Report task done.

## Anti-fabrication (per #M-4)

Every claim of "tests pass" / "ruff clean" / "PR opened" in the final report MUST be backed by literal command output (cmd + cwd + raw last lines). A bare "all green" with no transcript is invalid. Also: if the parser cannot reliably extract the marker characters (`●`, `⎿`) under the project's terminal encoding, surface that as a blocker in the report rather than hand-waving past it — the whole shim depends on those markers being detectable.

## Open questions for the implementer

These are NOT blockers — pick a reasonable default, document the decision in the PR body:

1. **Multi-line curl bodies.** agy occasionally wraps long curl commands with backslash continuation across multiple lines. Decision needed: single-line regex with `re.DOTALL` over the `Bash(...)` block, or a small state machine. Either is fine; the single-line approach is simpler and works for the verified shape.
2. **Argument schema.** Should the synthesized `args` field hold the JSON-RPC `params.arguments` dict directly, or wrap it in a shape that matches what other adapters emit (e.g. claude.py records `{"count": 38}` for batched verify_words)? Pick the shape that minimizes downstream gate special-casing — look at the existing entries in `build/a1/my-morning-20260521-101042` (claude-tools build) for the canonical reference.
3. **Per-writer prompt section scaffolding.** If `linear_pipeline.py` already has a writer-name substitution path, reuse it. If not, the minimal scaffolding is a `{WRITER_SPECIFIC_DIRECTIVES}` placeholder with a Python dict mapping writer name → directive block; empty string for writers without a custom block. Document in the PR which path you chose.
