# Codex dispatch — writer telemetry: capture search_text textbook hits in `result_summary`

**Trigger:** Re-eval of `audit/bakeoff-2026-05-12-night` claude-tools artifact against `textbook_grounding` gate (post-#1901 fix) shows `textbook_result_hits=0` despite the writer making 2 `search_text` calls. Root cause: the writer-side telemetry emits `result_summary={}` for `search_text` (and no `result_excerpt`), so the gate has nothing to match blockquotes against.
**File:** `scripts/build/linear_pipeline.py`
**Functions:** `_summarize_generic_tool_result` (line 1520), `_summarize_tool_result` (line 1542), `_bounded_result_excerpt` (line 1548), `emit_writer_response_telemetry` (line 1569), `_load_writer_tool_calls` (line 4147), `_textbook_grounding_gate` (line 4289).
**Estimated effort:** 90-120 min (diagnose capture-vs-summarize, fix accordingly, regression test).

## The bug, with evidence

The bakeoff's writer telemetry JSONL (`audit/bakeoff-2026-05-12-night/claude.write.jsonl`) has 2 `writer_tool_call` events with `tool=search_text`:

```
CALL 1: args_summary={'query_chars': 60} result_summary={} duration_ms=...
CALL 2: args_summary={'query_chars': 49} result_summary={} duration_ms=...
```

`result_summary` is empty. `result_excerpt` field is **absent entirely** (only these keys exist: ts, writer, module, section, tool, args_summary, result_summary, duration_ms).

Per `_summarize_generic_tool_result` (line 1520-1539), an empty `result_summary={}` happens when:
- `result` is `None` → returns `{}` (line 1537-1538), OR
- `result` is a Mapping with no recognized keys and no `keys()` (would return `{"keys": []}` not `{}`)

Per the writer-tool-call emit site (line 1605-1622), `result_excerpt` is added ONLY for `tool == "search_text"` AND ONLY if `_bounded_result_excerpt(result)` is non-empty. Since `result_excerpt` is absent, `_bounded_result_excerpt(result)` returned empty — meaning result has no text/content/excerpt/snippet/quote/body strings to walk.

Both observations together: **the `result` value passed in for the `search_text` calls is either `None` or an empty/non-walkable structure** by the time `emit_writer_response_telemetry` sees it.

The gate at line 4289 (`_textbook_grounding_gate`) then can't find any items to check against blockquotes, so `textbook_result_hits=0` and the HARD gate fails. This is structural: even when the writer DID retrieve textbook content correctly via MCP, the telemetry drops the evidence.

## Investigation phase (mandatory first step)

**Hypothesis A — capture-side**: The writer-side adapter (Claude or Codex agent runtime) doesn't propagate MCP tool results back into the `tool_calls` list that `emit_writer_response_telemetry` consumes. The summary is empty because the input is empty.

**Hypothesis B — summarizer-side**: The result IS reaching the summarizer, but `_summarize_generic_tool_result` doesn't know how to extract `search_text` hits (it's tuned for `verify_words`-style results). Items get dropped silently.

**Hypothesis C — both**: Capture works partially, summarizer is too generic.

Diagnose first. Required commands (quote raw output in PR body):

```bash
# Where are tool_calls populated for the writer? Find the call site that
# passes tool_calls into emit_writer_response_telemetry.
grep -n "emit_writer_response_telemetry" scripts/build/linear_pipeline.py scripts/agent_runtime/*.py

# What does the adapter (Claude / Codex) actually pass for `result`?
grep -n "tool_calls" scripts/agent_runtime/claude_*.py scripts/agent_runtime/codex_*.py | head -20

# Trace: read the file at each call site; check whether `result` is populated
# from the agent CLI's tool-use response or left as None.
```

Quote the relevant code snippets (10-20 lines around each) in the PR body so the diagnosis is auditable. Only after confirming whether it's A, B, or C, apply the fix.

## Fix design

### If Hypothesis A (capture-side):
- Update the writer-side adapter (`scripts/agent_runtime/claude_*.py` and `scripts/agent_runtime/codex_*.py`) to capture tool-call results and include them in the `tool_calls` list passed to `emit_writer_response_telemetry`.
- The adapter must populate `call["result"]` with the raw MCP response (list of search hit dicts for `search_text`).
- Verify by re-emitting telemetry against a fresh writer run (or a synthetic test fixture) and confirming `result_summary` and `result_excerpt` are non-empty for `search_text`.

### If Hypothesis B (summarizer-side):
- Add a `_summarize_search_text_result(result)` specialization. Should preserve enough structure for the `textbook_grounding` gate to match:
  - List of items with `{source_type, author, grade, page, text}` (or whatever the actual MCP response shape uses — confirm by inspecting `scripts/wiki/sources_db.py:search_sources` return value).
  - Bound each item's text to e.g. 500 chars to keep JSONL size reasonable.
- Dispatch in `_summarize_tool_result` based on `tool == "search_text"`.
- The gate-side `_result_items_from_call` (find via grep) must continue to iterate the items correctly. If the gate reads from `result_summary` (not the bare `result`), make sure the new summary preserves the list structure the gate expects.

### If Hypothesis C (both):
- Apply both fixes. Capture-side fix first, then summarizer enhancement.

The point of the investigation is to **avoid making both fixes when only one is needed.** Pick parsimoniously.

## Regression test

Add `tests/test_writer_telemetry_search_text.py`. Use a synthetic `tool_calls` fixture mimicking what a working capture would produce, then verify the emitted JSONL event preserves enough structure for `_textbook_grounding_gate` to match. Sketch:

```python
"""Regression test for writer telemetry capture of search_text results.

Bug context: the textbook_grounding gate couldn't find any textbook hits
in the bakeoff JSONL because result_summary was empty for every search_text
call. Whatever the root cause (capture vs summarize), the contract is:
after this fix, a search_text call with non-empty MCP results MUST produce
a writer_tool_call event whose stored summary preserves textbook-hit
attribution (author/grade/page) AND raw text fragment.
"""

from scripts.build.linear_pipeline import emit_writer_response_telemetry

def test_search_text_results_preserved_in_telemetry():
    fake_search_result = [
        {
            "source_type": "textbook",
            "author": "karaman",
            "grade": "10",
            "page": "176",
            "title": "Сторінка 176",
            "text": "Дієслова із суфіксом -ся(-сь)...",
        }
    ]
    tool_calls = [{
        "tool": "search_text",
        "args": {"query": "дієслова -ся"},
        "result": fake_search_result,
        "section": "Дієслова на -ся",
    }]
    events = []
    def sink(event_name, **fields):
        events.append({"event": event_name, **fields})
    emit_writer_response_telemetry(
        output="(writer output)",
        writer="claude-tools",
        module="a1/my-morning",
        sections=["Дієслова на -ся"],
        tool_calls=tool_calls,
        event_sink=sink,
    )
    tool_call_events = [e for e in events if e["event"] == "writer_tool_call"]
    assert len(tool_call_events) == 1
    event = tool_call_events[0]
    # Summary must preserve textbook attribution.
    assert event["result_summary"]  # not empty
    # Either as direct items in result_summary OR via result_excerpt.
    summary_or_excerpt = str(event.get("result_summary")) + str(event.get("result_excerpt", ""))
    assert "karaman" in summary_or_excerpt or "Караман" in summary_or_excerpt
    assert "176" in summary_or_excerpt
    # The gate-side reader (_result_items_from_call or similar) must be
    # able to extract structured items for matching. Verify by calling it:
    from scripts.build.linear_pipeline import _result_items_from_call
    items = list(_result_items_from_call(event))
    textbook_items = [i for i in items if str(i.get("source_type") or i.get("corpus") or "").startswith("textbook")]
    assert len(textbook_items) >= 1, "gate cannot extract textbook items from telemetry"
```

Adapt to the actual `emit_writer_response_telemetry` signature; the load-bearing contract is: structured textbook hits passed in → structured items extractable on the gate side.

## Verifiable claims this dispatch will produce (per #M-4)

| Claim | Tool | Output |
|---|---|---|
| Diagnosis: which hypothesis (A/B/C) | `grep` + code-read commands above | Quoted code excerpts proving where the result drops out |
| Pre-fix: bakeoff JSONL has `result_summary={}` for search_text | `grep '"tool": "search_text"' audit/bakeoff-2026-05-12-night/claude.write.jsonl` | Raw quoted events |
| Post-fix: synthetic test fixture preserves structure | Test runs | `1 passed` for the new regression test |
| Existing tests pass | `pytest tests/test_linear_pipeline*.py tests/test_textbook_grounding*.py -v` | Raw summary |
| Ruff clean | `.venv/bin/ruff check` | Raw |

## Dispatch checklist

1. Worktree: `git worktree add .worktrees/dispatch/codex/writer-telemetry-result-summary -b codex/writer-telemetry-result-summary origin/main`
2. Investigation phase (grep + read) — document findings inline in PR body.
3. Implement chosen fix (A, B, or C).
4. Regression test.
5. Pytest + ruff. Quote outputs.
6. Commit: `fix(writer-telemetry): preserve search_text results in result_summary`
7. Push + open PR titled `fix(writer-telemetry): preserve search_text textbook hits`.
8. PR body MUST include: hypothesis verdict + supporting evidence + pre/post-fix repro + test output.
9. **DO NOT auto-merge.**

## Out-of-scope

- ❌ Don't touch `_vesum_gate` (separate dispatch).
- ❌ Don't touch `_prepare_query` (#1901 already fixed).
- ❌ Don't change the MCP server's response shape — `scripts/wiki/sources_db.py:search_sources` returns what it returns; the writer telemetry must adapt to it, not vice versa.
- ❌ Don't rerun the bakeoff. Use the existing JSONL as the pre-fix evidence base.
- ❌ Don't write new MCP wrappers or bridges — this is strictly a capture+summarize fix inside `linear_pipeline.py` (and possibly `scripts/agent_runtime/` if Hypothesis A).
