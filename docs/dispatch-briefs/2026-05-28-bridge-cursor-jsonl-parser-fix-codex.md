# Fix `ab discuss` cursor JSONL response parsing

**Agent:** codex (gpt-5.5, xhigh, danger)
**Task ID:** `bridge-cursor-jsonl-parser-fix-2026-05-28`
**Base:** `origin/main` (`bc24fb31bd`)
**Branch:** `codex/bridge-cursor-jsonl-parser-fix-2026-05-28`
**Worktree:** `.worktrees/dispatch/codex/bridge-cursor-jsonl-parser-fix-2026-05-28`

## Why

`ab discuss --with cursor` consistently fails to capture cursor-agent's response. The bridge stores 510 chars of `[failed: {...stream init + user-echo...}]` while the actual cursor session transcript at `~/.cursor/projects/.../agent-transcripts/<session_id>/<session_id>.jsonl` has the full assistant response.

Empirical: on 2026-05-28 the `v7.1-empirical-direction-2026-05-28` channel discussion captured cursor as `[failed]` in both rounds, but the session transcript at `~/.cursor/projects/Users-krisztiankoos-projects-learn-ukrainian/agent-transcripts/656c0b63-d5b4-4bdf-89cf-e936d00e6b09/656c0b63-d5b4-4bdf-89cf-e936d00e6b09.jsonl` contains substantive r1 + r2 replies with explicit `[VOTE: D]`. The bridge's parser silently dropped them.

User flagged this 2026-05-28 morning: *"fix the ab so it can handle cursor communications etc, he is to valuable to be missed."*

## #M-4 deterministic-claim preamble

Every claim about the parser fix MUST be tool-backed in your final report:
- "Parser now extracts cursor responses" → quote raw test output `pytest tests/agent_runtime/adapters/test_cursor_adapter.py -k parse_response` final line
- "Tested against real cursor transcript" → quote your test that loads the actual `656c0b63...jsonl` file (committed as a fixture) + asserts response is non-empty + contains `[VOTE: D]`
- "ab discuss with cursor now works end-to-end" → quote a live `ab ask-cursor` invocation's bridge return value with raw `Response received from cursor` line
- "PR opened" → quote `gh pr view <N> --json url` raw URL line

Do NOT claim "should work" or "expected to work" without a tool-backed test.

## Required reads

1. **`scripts/agent_runtime/adapters/cursor.py:234-317`** — `CursorAdapter.parse_response()`. Lines 287-301 contain the bug:
   ```python
   for event in events:
       if event.get("type") == "text":           # ← cursor-agent doesn't emit this shape
           response += event.get("content", "")
       elif event.get("type") == "message" and event.get("role") == "assistant":  # ← nor this
           ...
   ```
2. **`/Users/krisztiankoos/.cursor/projects/Users-krisztiankoos-projects-learn-ukrainian/agent-transcripts/656c0b63-d5b4-4bdf-89cf-e936d00e6b09/656c0b63-d5b4-4bdf-89cf-e936d00e6b09.jsonl`** — actual cursor-agent JSONL output. Inspect line structure: each line is `{"role": "user"|"assistant", "message": {"role": "...", "content": [{"type": "text"|"tool_use", ...}, ...]}}`. Save a sanitized copy as a test fixture (see Deliverable 3).
3. **`scripts/agent_runtime/parse.py`** (or wherever `parse_json_events` and `normalize_tool_calls` live) — verify whether those helpers already extract anything from the new event shape, or if all the work happens in `parse_response` itself.
4. **`scripts/ai_agent_bridge/_cursor.py:90-110`** — the `ask-cursor` path uses `--output-format text` (line 96) and works fine. Compare with `adapters/cursor.py:122` which defaults to `--output-format stream-json`. The two paths take different output formats; only the stream-json path is broken.
5. **`tests/agent_runtime/adapters/test_cursor_adapter.py`** — existing test layout. Match its shape for the new tests.
6. **Pt 13 handoff** `docs/session-state/2026-05-28-pt13-*.md` (will be written by orchestrator in parallel) — full context on why cursor's vote mattered tonight.

## Deliverables (single PR)

### Deliverable 1 — fix `parse_response` for the actual cursor-agent v2026.05.27 event shape

Add a case to the response-extraction loop in `parse_response` that handles cursor-agent's actual output shape:

```python
# Cursor Agent v2026.05.27+: events have {role: assistant, message: {content: [...]}}
elif event.get("role") == "assistant" and isinstance(event.get("message"), dict):
    content = event["message"].get("content")
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                response += part.get("text", "")
    elif isinstance(content, str):
        response += content
```

Place it alongside the existing two cases. Keep the existing cases — older cursor-agent versions may still emit them.

**Accumulation strategy**: cursor-agent emits MULTIPLE assistant messages per turn (thinking, tool_use intent, more thinking, final response). The empirical session transcript at `656c0b63...jsonl` has 8 assistant lines in r1 (lines 1-8) plus 2 in r2 (lines 10-11), with `tool_use` blocks interspersed. The final substantive `[VOTE: D]` text is in the LAST assistant message of the round.

Two strategies:
- (a) Accumulate ALL text blocks across ALL assistant events → captures the model's full reasoning + final answer
- (b) Keep only the LAST assistant message's text → captures just the final answer

Pick (a) by default — fidelity > noise — but join consecutive text blocks with `\n\n` so they read cleanly. Sample target output for the 656c0b63 r2 line 11: the full final `## Round 2 — after reading Codex and Gemini` markdown including the `[VOTE: D]` line.

**Optional bonus**: detect when consecutive text blocks belong to the same assistant message and merge them without separator; only add `\n\n` between separate assistant messages. Cleaner output for downstream readers.

### Deliverable 2 — commit a sanitized fixture from the real transcript

Save a stripped copy of `656c0b63...jsonl` as `tests/agent_runtime/adapters/fixtures/cursor_v2026_05_27_session_transcript.jsonl`. Sanitization:
- Replace the `cwd` and any absolute paths with `/tmp/sanitized`
- Replace `session_id` with `<sanitized-session-id>`
- Replace `apiKeySource` with `<sanitized-apiKeySource>`
- Keep the actual assistant text content intact (this is what the parser must extract)

### Deliverable 3 — pytest covering the fix

Add to `tests/agent_runtime/adapters/test_cursor_adapter.py`:

```python
def test_cursor_adapter_parses_v2026_05_27_assistant_messages(adapter):
    """cursor-agent v2026.05.27 emits {role: assistant, message: {content: [...]}};
    parse_response must extract the text blocks accurately."""
    fixture = Path(__file__).parent / "fixtures" / "cursor_v2026_05_27_session_transcript.jsonl"
    stdout = fixture.read_text(encoding="utf-8")
    result = adapter.parse_response(
        stdout=stdout, stderr="", returncode=0, output_file=None,
    )
    assert result.ok, f"Expected ok=True, stderr_excerpt={result.stderr_excerpt!r}"
    assert result.response, "Response should not be empty"
    assert "[VOTE: D]" in result.response, "Final vote should be captured"
    assert "Round 2" in result.response, "r2 content should be present"
    # Sanity: tool_use blocks should NOT appear as text in the response
    assert "tool_use" not in result.response.split("\n")[0:5][0]
```

Plus a smaller positive test for a synthetic single-text-block event.

### Deliverable 4 — regression for the old event shapes

Keep the existing parser cases (`type: text` and `type: message, role: assistant`) intact and add tests that confirm they STILL work, in case older cursor-agent versions or other tools emit those shapes.

### Deliverable 5 — update the `[failed: ...]` channel storage to be less destructive

When `parse_response` returns `ok=False`, the discuss code path (likely in `scripts/ai_agent_bridge/_discussion.py` or `_cli.py`) saves `[failed: <stderr_excerpt>]` truncated to 500 chars. That's why the channel DB had only 510 chars even though the full transcript was on disk.

Add a fallback: when cursor's parse_response returns ok=False, the discuss path should look for the cursor session transcript on disk (the parser already finds `session_id`; use that to locate `~/.cursor/projects/<encoded-cwd>/agent-transcripts/<session_id>/<session_id>.jsonl`) and re-run the parser on the transcript content. If that yields a non-empty response, use IT for the channel storage.

This means future bridge bugs that miss the in-process stream still recover the response from the session log. Small, defensive, important per user direction "he is too valuable to be missed."

## Numbered steps

1. `cd /Users/krisztiankoos/projects/learn-ukrainian && git fetch origin main --quiet && git worktree add .worktrees/dispatch/codex/bridge-cursor-jsonl-parser-fix-2026-05-28 -b codex/bridge-cursor-jsonl-parser-fix-2026-05-28 origin/main`
2. `cd .worktrees/dispatch/codex/bridge-cursor-jsonl-parser-fix-2026-05-28`
3. Do all 6 required reads. Quote at least one raw line per read in your final report.
4. Implement Deliverables 1-4 in `scripts/agent_runtime/adapters/cursor.py` + test file + fixture. Run `pytest tests/agent_runtime/adapters/test_cursor_adapter.py -v` — must pass.
5. Implement Deliverable 5 in the discuss code path. Run targeted bridge tests if any exist; otherwise add one. Quote raw test output.
6. Run full agent_runtime suite: `.venv/bin/python -m pytest tests/agent_runtime/ -q --no-header 2>&1 | tail -10`. Quote raw final line.
7. Run ruff: `.venv/bin/ruff check scripts tests`. Quote raw final line.
8. Commit with conventional message + `X-Agent: codex/bridge-cursor-jsonl-parser-fix-2026-05-28` trailer.
9. `git push -u origin codex/bridge-cursor-jsonl-parser-fix-2026-05-28`. Quote raw push output.
10. `gh pr create` with title `fix(bridge): cursor-agent v2026.05.27 JSONL response parsing + session-log fallback` and body that explains the bug + fix + tests + cites the failed channel deliveries from `v7.1-empirical-direction-2026-05-28`.
11. **NO auto-merge**. Surface PR URL in final report.

## Out of scope

- The `_cursor.py::_invoke_cursor` `--output-format text` path (already works, don't touch).
- Cursor model default flip (already done in PR #2376; that's a separate orthogonal fix).
- Restoring cursor's actual reply to the `v7.1-empirical-direction-2026-05-28` channel — orchestrator will handle that separately if needed.
- Any unrelated bridge refactors.

## Verifiable-claim format for your final report

```
GOAL_DONE reason="Bridge cursor JSONL parser fix PR opened: <PR-URL>"

## Evidence
- pytest cursor adapter: <command> cwd=<dir> → <raw final line>
- full agent_runtime pytest: <command> cwd=<dir> → <raw final line>
- ruff: <command> cwd=<dir> → <raw final line>
- fixture committed: ls -la cwd=<dir> → <raw line showing fixture file>
- commit: <command> cwd=<dir> → <raw SHA + subject>
- push: <command> cwd=<dir> → <raw "* [new branch]" line>
- PR: <command> cwd=<dir> → <raw PR URL>
```

If you can't reach `GOAL_DONE`, emit `GOAL_ABORT reason="..." next_action="..." last_cmd="..." last_output="..."` per `claude_extensions/rules/goal-driven-runs.md`.
