# Codex dispatch brief — #1819 GeminiAdapter.parse_response misses tool_calls in JSONL

**Why this matters now:** PR #1818 (cwd fix) makes Gemini load `.gemini/settings.json` and start invoking `mcp__sources__*` tools. But if `GeminiAdapter.parse_response()` doesn't extract those calls from the session JSONL, `writer_tool_calls.json` stays `[]`, the runtime gate (`MCP_TOOLS_NEVER_INVOKED`) fires falsely, and **the bakeoff signal stays masked** — even though tools are actually being called.

This issue blocks the bakeoff verification path (5 shifts unverified per current handoff).

## Worktree (already prepared by dispatcher)

You start in `.worktrees/dispatch/codex/1819-gemini-telemetry-parser/` on branch `codex/1819-gemini-telemetry-parser`, branched from `origin/main`. Do NOT `cd` out, do NOT create a new branch in the main checkout.

## Goal

`GeminiAdapter.parse_response(...).tool_calls` must extract every `mcp__sources__*` tool call (and built-in tool calls like `read_file`, `list_directory`) from the Gemini CLI session JSONL. Today it returns `[]` even when the JSONL has real entries.

## Files to read (in order)

1. **`audit/gemini-tools-review-2026-05-09/REPORT.html`** — the audit that found this. Section **E9 "Telemetry parser misses Gemini JSONL tool calls"** has the evidence. Sections **E1, E4** point at actual session-file paths and shape. Read these BEFORE editing code.

2. **`scripts/agent_runtime/adapters/gemini.py`** lines 295-440 (`parse_response`) and lines 520+ (`_read_latest_session_trace`). Note: `parse_response` already calls `parse_json_events()` + `normalize_tool_calls()` — the bug is somewhere inside those two helpers' interaction with the actual Gemini JSONL shape, NOT in the adapter wiring.

3. **`scripts/agent_runtime/tool_calls.py`** — the helpers. Read the full file. Pay special attention to:
   - `_candidate_payloads()` recursively visits nested keys including `toolCalls` (line 146). So nested items ARE reached.
   - `_is_tool_use_payload()` accepts `tool_use`/`tool_call`/`function_call`/`mcp_tool_call` types, OR presence of `functionCall`/`toolCall` keys, OR the heuristic of name+args without "result" in type.
   - `_tool_name()` checks: `function.name` (Mapping), then `name`/`tool_name`/`toolName`/`function_name`/`server_tool_name`.
   - `_tool_arguments()` checks: `function.arguments` (Mapping), then `arguments`/`args`/`input`/`parameters`.

4. **Existing tests** — `tests/test_gemini_adapter_auth.py`, `tests/test_agent_runtime_tool_calls.py` (if exists). Search:
   ```
   grep -rln "normalize_tool_calls\|parse_json_events\|toolCalls" tests/ | head
   ```

## Diagnostic step (do this BEFORE editing)

Capture an actual Gemini JSONL session that contains `mcp__sources__*` tool calls. Two options:

a. **Find one in the audit's evidence files** — section E1/E4 of `REPORT.html` likely points at a real session file under `~/.gemini/tmp/<cwd-basename>/chats/` or `~/.gemini/sessions/`. Read 50-200 lines of that file and capture the actual shape of toolCalls entries.

b. **Run a fresh smoke** — from the worktree root:
   ```
   .venv/bin/python -c "
   from scripts.build.linear_pipeline import _runtime_tool_config
   cfg = _runtime_tool_config('gemini-tools')
   print(cfg)
   "
   # Confirm cfg includes mcp_server_names=['sources'].
   # Then invoke gemini-cli with a tool-using prompt:
   gemini --approval-mode=yolo --skip-trust --allowed-mcp-server-names sources \
       -p "Call mcp__sources__verify_words with words=['кіт', 'добре']" 2>&1 | head -60
   # Find the resulting session file:
   ls -lt ~/.gemini/tmp/*/chats/ 2>/dev/null | head
   # Or:
   find ~/.gemini -name "session-*.json*" -mmin -5 2>/dev/null
   ```

Capture the exact shape of `toolCalls` entries in `/tmp/gemini-jsonl-shape.txt`. **The shape determines the fix.** Reference this file in the commit message.

## Likely failure modes (test each before assuming)

The bug could be in any of:

1. **`parse_json_events()` discards lines** — Gemini's session file may NOT be JSONL (one JSON object per line); it might be a single big JSON object. If so, `parse_json_events()` returns `[]` because no line starts with `{`. Fix: detect "is this a single JSON object?" and parse it as one, then walk children.

2. **Toolcalls live inside a key that `_candidate_payloads()` doesn't visit** — possible but unlikely given `toolCalls` is in the visit list.

3. **Tool entries have a non-recognized shape** — e.g., name lives at `payload.functionCall.name` but `args` are at `payload.functionCall.args` (not `arguments`); or entries are wrapped in `{role:'model', parts:[{functionCall:{name:..., args:...}}]}`. Adapt `_tool_arguments()` / `_tool_name()` if so.

4. **Tool calls + tool results live in separate JSON files** — the audit may show that Gemini writes calls to one file and results to another, and our session-trace reader only reads one.

State which one (or which combination) fits your diagnosis in the PR description. Don't guess — fix what the actual JSONL shows.

## Implementation

Once you've identified the gap from real JSONL evidence:

- Fix in `scripts/agent_runtime/tool_calls.py` (preferred — keeps Gemini-specific shape handling close to the existing parser) OR in `gemini.py` `_read_latest_session_trace` (if the issue is at the file-read layer).
- Do NOT regress existing CLI providers' parsing — Codex CLI also uses these helpers.
- Add docstring noting the Gemini-specific shape with a 3-5 line example.

## Acceptance criteria (from issue body)

- [ ] **Adapter test:** synthetic Gemini JSONL fixture with at least one `toolCalls` entry containing `mcp__sources__verify_words`. Assert `GeminiAdapter.parse_response(...).tool_calls` extracts it with the right name + args.
- [ ] **Negative test:** empty session JSONL → `tool_calls=[]` (existing behavior preserved).
- [ ] **Mixed test:** session JSONL with both built-in tool calls (`list_directory`, `read_file`) AND `mcp__sources__*` calls → adapter returns ALL of them, not just one class.
- [ ] **Pipeline regression test:** run `linear_pipeline._writer_telemetry_postprocess(...)` end-to-end with the synthetic JSONL fixture; assert `writer_tool_calls.json` contains the MCP entries. (Find this function via `grep -n "_writer_telemetry_postprocess\|writer_tool_calls" scripts/build/linear_pipeline.py`.)
- [ ] **Runtime-gate compatibility:** confirm the positive runtime gate from PR #1813 still fires on genuinely-empty `writer_tool_calls.json`. Find the gate via `grep -rn "MCP_TOOLS_NEVER_INVOKED\|writer_tool_calls" scripts/build/`. The gate's contract should be unchanged — this fix only makes the input more accurate.
- [ ] **Existing tests still pass.**

## Numbered execution steps

1. **Verify worktree** — `git rev-parse --abbrev-ref HEAD` must print `codex/1819-gemini-telemetry-parser`. If not, STOP.

2. **Read the audit's E9 + E1 + E4 sections** in `audit/gemini-tools-review-2026-05-09/REPORT.html`. Capture: (a) the actual session-file path pattern Gemini writes, (b) the exact JSON shape of `toolCalls` entries.

3. **Capture a real JSONL** per "Diagnostic step" §a or §b above. Save to `/tmp/gemini-jsonl-shape.txt` and reference in commit.

4. **Read the parser code** — `scripts/agent_runtime/tool_calls.py` end-to-end + `gemini.py:295-440` + `gemini.py:520+`.

5. **Diagnose** which of the 4 likely failure modes (or a 5th) fits the actual JSONL. State the diagnosis clearly in the commit message.

6. **Implement the fix.** Minimal change. Do not refactor unrelated code.

7. **Add tests** per §AC. Five new tests minimum (adapter happy / empty / mixed / pipeline / gate-compat). Place them in:
   - Adapter tests → existing `tests/test_gemini_adapter_auth.py` or a new `tests/test_gemini_adapter_tool_calls.py`.
   - Pipeline test → existing `tests/test_linear_pipeline*.py` (find via grep).

8. **Run tests:**
   ```
   .venv/bin/pytest tests/test_gemini_adapter*.py tests/test_agent_runtime_tool_calls.py tests/test_linear_pipeline*.py -v
   ```
   ALL must pass.

9. **Lint** — `.venv/bin/ruff check scripts/agent_runtime/ scripts/build/ tests/`.

10. **Commit** — single conventional commit. Title:
    ```
    fix(telemetry): GeminiAdapter parses toolCalls from session JSONL (#1819)
    ```
    Body: state the diagnosis (which of the failure modes fit), the JSONL shape captured, the fix, and test count.

11. **Push** — `git push -u origin codex/1819-gemini-telemetry-parser`.

12. **Create PR** — `gh pr create --title "..." --body "..."`. Reference this brief + the audit's E9 evidence section. Do NOT enable auto-merge.

## What NOT to do

- Do NOT change the runtime gate's contract — this is a parser fix, not a gate fix.
- Do NOT touch `scripts/agent_runtime/adapters/codex.py` or `claude.py`. Those CLIs don't have this bug.
- Do NOT over-engineer — find the minimal change that makes the JSONL shape parse correctly.
- Do NOT enable auto-merge.
- Do NOT skip the diagnostic step. The parser already has multiple matchers; adding more matchers blindly can mask other bugs. Find the actual gap from real JSONL first.

## Output expected

A single PR on branch `codex/1819-gemini-telemetry-parser` ready for review. PR body must include:

- The captured Gemini JSONL shape (excerpt of an actual `toolCalls` entry from a real session).
- Which of the 4 failure modes (or a 5th) was the actual root cause.
- All 5 ACs verified.
- All existing tests still pass.
