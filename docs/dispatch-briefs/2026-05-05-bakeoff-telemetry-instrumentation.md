# Codex dispatch — bakeoff telemetry instrumentation for V7 linear pipeline

## Context

The A1/20 bakeoff (`docs/dispatch-briefs/2026-05-05-a1-20-bakeoff-with-new-prompts.md`) needs deterministic prompt-adherence telemetry. Today the V7 linear pipeline emits build-coarse JSONL events (`module_start`, `phase_done`, etc.) but no fine-grained writer/reviewer-side events that let us measure whether the new V7 prompts (CoT scaffolding + Tier-1 verification per #1696) were actually FOLLOWED at runtime.

Without telemetry the bakeoff falls back to inferring prompt adherence from the writer's prose output — slower, noisier, easy to miss when an agent silently bypasses the CoT block but still produces decent content. Telemetry closes that gap.

This is a standalone PR (not a #1696 add-on) so it's reviewable as a self-contained instrumentation diff, and so all future bakeoffs benefit, not just A1/20.

## Goal

Add JSONL event emission at writer-side and reviewer-side hook points in the V7 linear pipeline. Events lend themselves to deterministic post-hoc scoring of prompt adherence and tool-usage density.

## Worktree

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin main
.venv/bin/python scripts/delegate.py dispatch ...  # invoked by parent
```

Worktree auto-derived at `.worktrees/dispatch/codex/bakeoff-telemetry/` via bare `--worktree`.

## Files in scope

Discovery first — read these before editing:

- `scripts/build/linear_pipeline.py` (V7 pipeline, this is where the work goes)
- `scripts/build/phases/linear-write.md` + `linear-review-dim.md` (the prompts being instrumented; do NOT edit these — they are #1696's domain)
- `scripts/build/v6_build.py` (the existing JSONL emitter — copy its event style for consistency)
- `docs/MONITOR-API.md` (where event schemas are documented; update if it covers JSONL events)

Likely edit targets:
- `scripts/build/linear_pipeline.py` — add event emission inside the writer-call wrapper + the per-dim reviewer-call wrapper + any MCP tool-invocation wrapper
- `tests/test_linear_pipeline_telemetry.py` (NEW) — fixture-based test that the events fire correctly given a stubbed writer/reviewer response

## Event schema (NEW events to add)

All events follow the existing `{"event": "<name>", "ts": "<iso8601>", ...}` JSONL line shape v6_build.py already emits. Add these:

### Writer-side

```json
{"event": "writer_cot_emit", "ts": "...", "writer": "claude-tools", "module": "a1/20", "section": "intro",
 "block_present": true, "block_chars": 432, "fields_filled": ["word_budget", "plan_vocab", "register", "teaching_sequence"]}
```
Emit when the writer's response contains a `<plan_reasoning>` (or equivalent) block per section. `fields_filled` lists which of the 4 CoT fields the writer actually populated. If `block_present=false`, the writer skipped CoT for that section.

```json
{"event": "writer_tool_call", "ts": "...", "writer": "claude-tools", "module": "a1/20", "section": "vocabulary",
 "tool": "verify_words", "args_summary": {"count": 8}, "result_summary": {"verified": 7, "failed": 1, "failed_words": ["взірець"]},
 "duration_ms": 421}
```
Emit for every MCP tool call the writer makes during a section. Capture `verify_words`, `verify_lemma`, `search_definitions`, `search_definitions_slovnyk`, `search_grinchenko_1907`, `search_literary`, `search_style_guide`, `search_idioms`, `query_pravopys`, `query_wikipedia`, `search_text`, `check_modern_form`. `args_summary` is bounded (no full payloads) to keep the JSONL line small.

```json
{"event": "writer_end_gate", "ts": "...", "writer": "claude-tools", "module": "a1/20",
 "gate_present": true, "gate_actions": ["rescanned_words", "rescanned_sources", "removed_unverified"],
 "removed_count": 1}
```
Emit when the writer's output contains an end-of-output gate (the Tier-1 self-review pass). Indicates whether the gate fired and what it caught.

### Reviewer-side

```json
{"event": "reviewer_dim_evidence", "ts": "...", "reviewer": "gemini-tools", "module": "a1/20",
 "writer_under_review": "claude-tools", "dim": "naturalness",
 "evidence_quotes": ["...", "...", "..."], "rubric_mapping": "<short>", "score": 8}
```
Emit per-dim. `evidence_quotes` is a list (≥2-3 entries per #1696's CoT discipline). `rubric_mapping` is a short text the reviewer wrote about how the quotes map to the rubric. `score` is the dim score.

```json
{"event": "reviewer_audit_call", "ts": "...", "reviewer": "gemini-tools", "module": "a1/20",
 "writer_under_review": "claude-tools", "dim": "decolonization",
 "audit_type": "source_attribution", "tool": "search_grinchenko_1907",
 "items_checked": 3, "items_failed": 0, "flags_raised": []}
```
Emit per audit call. `audit_type` ∈ {`source_attribution`, `quote_verification`, `sovietization_check`, `modern_form_check`}.

### Pipeline-side

```json
{"event": "phase_writer_summary", "ts": "...", "writer": "claude-tools", "module": "a1/20",
 "sections_total": 5, "sections_with_cot": 5, "tool_calls_total": 14, "verify_words_calls": 4,
 "end_gate_fired": true, "removed_via_gate": 1}
```
Emit once per writer phase as a roll-up summary. The bakeoff aggregator can read this directly without parsing every individual event.

```json
{"event": "phase_review_summary", "ts": "...", "reviewer": "gemini-tools", "module": "a1/20",
 "writer_under_review": "claude-tools", "dims_scored": 5, "dims_with_evidence": 5,
 "audit_calls_total": 8, "flags_raised_total": 0,
 "min_dim_score": 7, "weighted_score": 8.2}
```
Emit once per review phase as a roll-up summary.

## Numbered steps

1. **Verify branch base.** `git log --oneline HEAD..origin/main` empty.

2. **Read the V7 pipeline.** `scripts/build/linear_pipeline.py` end-to-end. Identify the writer-call hook (where the LLM response is received and parsed) and the per-dim reviewer-call hook. These are where events get emitted.

3. **Read v6_build.py's JSONL emitter** for the existing event style + helper. Reuse the helper if one exists; create a thin `emit_event(event_name, **fields)` wrapper if not.

4. **Implement writer-side instrumentation.**
   - Hook the writer's response parser. For each section in the response, parse for the CoT block (look for `<plan_reasoning>` opening tag OR `**Section reasoning:**` heading per #1696's prompt template; the prompt itself defines the marker — read it to know the exact form). Emit `writer_cot_emit` with the parse result.
   - Hook every MCP tool call the writer makes. For Claude/Gemini path: tool calls go through the harness's tool-use machinery; intercept there. For Codex/GPT-5.5 path: tool calls are shell-out invocations; wrap the shell-out helper to emit `writer_tool_call` per invocation.
   - Hook end-of-output gate detection. Same parser as CoT — look for the gate marker the prompt template defines.
   - Aggregate at the end of the writer phase into `phase_writer_summary`.

5. **Implement reviewer-side instrumentation.**
   - Hook per-dim reviewer call. For each dim, parse the reviewer's response for the CoT block (per-dim variant). Emit `reviewer_dim_evidence` with extracted quotes + rubric mapping + score.
   - Hook reviewer's MCP audit calls (the Tier-1 audits). Wrap the same way as writer's tool calls. Emit `reviewer_audit_call` per audit.
   - Aggregate at end of review phase into `phase_review_summary`.

6. **Schema discipline.** Keep events flat (no nested objects deeper than 2 levels). Bound array lengths (≤5 evidence quotes per event; if reviewer cites more, take first 5). Bound string lengths (`rubric_mapping` ≤ 500 chars).

7. **Test.** Add `tests/test_linear_pipeline_telemetry.py`:
   - Fixture: stub a writer response containing a CoT block + 3 tool calls + end-gate.
   - Fixture: stub a reviewer response with 5 dims, each with 2-3 evidence quotes, 8 audit calls total.
   - Run the pipeline against the fixtures.
   - Assert all expected events fire with expected schema (use `jsonschema` or hand-rolled assertions).
   - Assert `phase_writer_summary` + `phase_review_summary` aggregate counts match.

8. **Doc.** Update `docs/MONITOR-API.md` — add a "JSONL events" section listing each event with a one-line description + schema reference. Follow whatever format the doc already uses for events.

9. **Backwards compatibility.** Existing v6_build.py JSONL events MUST keep their current shape. New events ADD to the stream; do NOT modify existing `module_start` / `phase_done` / `review_score` shapes. Bakeoff aggregator + Monitor API reading state both depend on the existing shapes.

10. **Run tests.** `.venv/bin/python -m pytest tests/test_linear_pipeline_telemetry.py -x -v`.

11. **Run full pipeline tests** to verify nothing else broke. `.venv/bin/python -m pytest tests/test_linear_pipeline.py tests/test_v6_build_events.py -x -q` (whichever exists).

12. **Run ruff.** `.venv/bin/ruff check scripts/ tests/`

13. **Commit.**
    ```
    feat(telemetry): JSONL events for writer + reviewer prompt-adherence + tool calls
    ```
    Body lists each event added + the test path + the doc update.

14. **Push + open PR (NOT draft).**
    ```bash
    git push -u origin codex/bakeoff-telemetry
    gh pr create --title "feat(telemetry): JSONL events for writer + reviewer prompt-adherence + tool calls" --body "$(cat <<'EOF'
    ## Summary

    Adds fine-grained JSONL telemetry to the V7 linear pipeline so the
    A1/20 bakeoff (and all future bakeoffs) can score prompt adherence
    and tool usage deterministically.

    ## New events

    Writer: `writer_cot_emit`, `writer_tool_call`, `writer_end_gate`,
    `phase_writer_summary`. Reviewer: `reviewer_dim_evidence`,
    `reviewer_audit_call`, `phase_review_summary`. Existing events
    (`module_start`, `phase_done`, etc.) keep their current shapes —
    new events are additive.

    ## Tests

    `tests/test_linear_pipeline_telemetry.py` covers all 7 new events
    with fixture-stubbed writer/reviewer responses + schema assertions.

    ## Doc

    `docs/MONITOR-API.md` lists each new event with a one-line
    description.

    ## Why standalone (not part of #1696)

    Decoupled from the prompt diff so reviewers can evaluate
    instrumentation independently of prompt design. After this lands,
    #1696 should rebase to pick it up; the bakeoff runs from #1696's
    worktree with new prompts + telemetry combined.

    Refs: bakeoff brief at `docs/dispatch-briefs/2026-05-05-a1-20-bakeoff-with-new-prompts.md`.
    EOF
    )"
    ```

15. **Do NOT enable auto-merge.** Cross-review on instrumentation is light-stakes but still cross-review.

## Acceptance criteria

- All 7 new events fire correctly per fixture-stubbed inputs
- Existing JSONL event shapes unchanged
- New tests pass; existing tests pass
- ruff clean
- `docs/MONITOR-API.md` updated
- PR opened (not draft) on `codex/bakeoff-telemetry`

## Discipline reminders

- **Read `linear_pipeline.py` END-TO-END** before editing. Memory rule: "I already know how it works" is ALWAYS wrong.
- **Do NOT edit `scripts/build/phases/linear-write.md` or `linear-review-dim.md`** — those are #1696's domain. The instrumentation reads parse-side, doesn't change the prompt.
- **Bound event payloads.** No raw 5KB writer responses in the JSONL stream — keep events small so Monitor / aggregator stay fast.
- **Backwards compat.** Existing event shapes immutable.
- **No `--no-verify`.** Reference the bakeoff brief in the commit + PR.
- **Worktree cleanup post-merge** by next session.

## Why Codex

Mechanical instrumentation across an existing pipeline. Pattern-applying work. Codex strength.
