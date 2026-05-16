# Dispatch — fix #2039 H2 — grok-tools writer prompt eats budget on plan_reasoning

**Agent:** codex
**Model:** gpt-5.5
**Effort:** medium
**Mode:** danger (worktree)
**Base:** origin/main
**Issue:** #2039

## Problem (empirical, today's m20 A/B builds)

`--writer grok-tools` produces under-target `module.md`:

| Effort | writer_output.raw.md | module.md | Target | Result |
|---|---|---|---|---|
| medium | 1,423 w | 674 w | 1,200 w | FAIL (56% of target) |
| xhigh | 1,419 w | 276 w | 1,200 w | FAIL (23% of target, regressed) |

Root cause: Grok 4.3 self-limits total response to ~1,400 words. The current writer prompt (`scripts/build/phases/linear-write.md` line 46) caps each `<plan_reasoning>` block at 200 words × 4 sections = up to 800 words consumed by visible CoT. The assembler correctly strips plan_reasoning → only ~600 words remain for the 4 artifacts (`module.md`, `activities.yaml`, `vocabulary.yaml`, `resources.yaml`). Module.md alone needs 1,200.

Claude-tools doesn't hit this ceiling — its m20 build (PR #2038) goes GREEN with the same prompt. So the prompt is well-tuned for Claude; Grok needs a leaner variant.

## Goal

Add a **per-writer-family prompt variant** so `--writer grok-tools` uses a slimmed plan_reasoning while `--writer claude-tools` (default) keeps the existing rich CoT contract.

## Concrete plan

### Step 1 — git worktree

```bash
git worktree add -b codex/2039-grok-tools-writer-prompt-2026-05-16 \
  .worktrees/dispatch/codex/2039-grok-tools-writer-prompt-2026-05-16 origin/main
cd .worktrees/dispatch/codex/2039-grok-tools-writer-prompt-2026-05-16
```

### Step 2 — create the grok-specific writer prompt

Create `scripts/build/phases/linear-write-grok.md` based on `linear-write.md`. Two structural changes:

1. **Replace the 4 separate `<plan_reasoning section="...">` blocks** (200 words each, ~800 total) with **ONE consolidated `<plan_thinking>` block** at the top, cap **150 words total**. It must still contain a per-section breakdown but in compressed form:

   ```xml
   <plan_thinking>
   <sections>
   Діалоги: vocab=[прокидатися, вмиватися, ...]; refs=Захарійчук G1 p.52; budget=300w.
   Дієслова на -ся: vocab=[...]; refs=...; budget=300w.
   Мій ранок: ...
   Підсумок: ...
   </sections>
   <verification_trace>One line per tool call, e.g. mcp__sources__verify_words([..]) → all-OK; mcp__sources__search_text("Захарійчук 52") → matched.</verification_trace>
   </plan_thinking>
   ```

2. **Update every reference to plan_reasoning in the prompt body** to point at `<plan_thinking>` instead. There are several call-sites (search the file). The tool-citation-honesty section (lines ~121-125) must keep its cross-reference invariant: every tool name cited in `<plan_thinking verification_trace>` must match an actual tool call.

3. **Keep everything else identical.** Same 4 artifact fences (`module.md`, `activities.yaml`, `vocabulary.yaml`, `resources.yaml`), same `<end_gate>` block, same immersion rule, same heritage discipline.

### Step 3 — wire the writer selection

In `scripts/build/linear_pipeline.py`, find where `linear-write.md` is loaded (search for `linear-write.md` string literal). Add per-writer-family routing:

```python
PROMPT_BY_WRITER = {
    "grok-tools": "linear-write-grok.md",
    # default for claude-tools / gemini-tools / codex-tools is linear-write.md
}
prompt_filename = PROMPT_BY_WRITER.get(writer_family, "linear-write.md")
```

Use a path like `PROJECT_ROOT / "scripts" / "build" / "phases" / prompt_filename`.

Also check the **correction prompt** at `scripts/build/phases/linear-writer-correction.md` — it also references plan_reasoning. If grok-tools writer hits a correction round, the correction prompt should reference `plan_thinking` for grok-tools. Either:
- (a) Create `linear-writer-correction-grok.md` with the same single-block substitution, OR
- (b) Make the correction prompt agnostic by accepting either tag.

Pick (a) for symmetry with the writer prompt.

### Step 4 — update telemetry consumers if needed

The `phase_writer_summary` event reports `sections_total` and `sections_with_cot`. Check `linear_pipeline.py` for the function that builds this event — it probably counts `<plan_reasoning>` blocks. For grok-tools (1 consolidated block), this counter should either:
- Return the count of `<sections>` lines inside `<plan_thinking>` (which is 4), OR
- Return `null` and a parallel `sections_with_thinking: True` flag.

Pick whichever preserves the existing test signal best. Confirm the writer_end_gate / tool_theatre logic still works for grok-tools.

### Step 5 — tests

Add `tests/build/test_linear_write_grok_prompt.py` covering:

1. `linear-write-grok.md` exists and is non-empty.
2. The grok-specific prompt contains `<plan_thinking>` and does NOT contain `<plan_reasoning section=` (regex assertion).
3. The grok-specific prompt's word count ≤ original linear-write.md word count (regression guard against accidental bloat).
4. `PROMPT_BY_WRITER["grok-tools"]` resolves to `linear-write-grok.md`; default falls through to `linear-write.md`.
5. The 4 artifact fences (`module.md`, `activities.yaml`, `vocabulary.yaml`, `resources.yaml`) still appear in the grok prompt.

### Step 6 — verify deterministically (#M-4 preamble)

The work produces these verifiable claims, each backed by a tool call you must include raw in the PR body:

| Claim | Tool + raw output to include |
|---|---|
| `linear-write-grok.md` exists | `ls -la scripts/build/phases/linear-write-grok.md` |
| Grok-specific prompt is shorter | `wc -w scripts/build/phases/linear-write-grok.md scripts/build/phases/linear-write.md` |
| Tests pass | `.venv/bin/pytest tests/build/test_linear_write_grok_prompt.py -v` final summary line |
| Lint clean | `.venv/bin/ruff check scripts/build/linear_pipeline.py tests/build/test_linear_write_grok_prompt.py` final line |
| Writer routing wired | `grep -n 'PROMPT_BY_WRITER\|linear-write-grok' scripts/build/linear_pipeline.py` |

DO NOT claim "I tested the m20 build" unless you actually ran it. The PR landing is the unblock for orchestrator to run the empirical A/B post-merge.

### Step 7 — commit, push, PR

```bash
git add scripts/build/phases/linear-write-grok.md \
        scripts/build/phases/linear-writer-correction-grok.md \
        scripts/build/linear_pipeline.py \
        tests/build/test_linear_write_grok_prompt.py
.venv/bin/ruff check scripts/build/linear_pipeline.py tests/build/test_linear_write_grok_prompt.py
.venv/bin/pytest tests/build/test_linear_write_grok_prompt.py -v
git commit -m "fix(writer): per-family writer prompt — slim plan_thinking for grok-tools (#2039 H2)"
git push -u origin codex/2039-grok-tools-writer-prompt-2026-05-16
gh pr create --title "fix(writer): grok-tools slim plan_thinking prompt (#2039 H2)" \
  --body "..."  # body must include the raw outputs from step 6
```

**DO NOT auto-merge.** Orchestrator will validate the empirical A/B build after merge.

## Out of scope

- Tuning the streaming-buffer truncation artifact (`він/о\n\nна` — separate hypothesis #2039 H3)
- Changing default `reasoning_effort` (orchestrator already reset to medium)
- Re-running the m20 A/B build (orchestrator does that post-merge)

## Reference

- Issue #2039 — full reproduction + hypotheses
- `scripts/build/phases/linear-write.md` — current writer prompt (read it before editing)
- `scripts/build/phases/linear-writer-correction.md` — current correction prompt
- `scripts/build/linear_pipeline.py` — pipeline that loads the writer prompt
- `docs/best-practices/hermes-usage.md` — Hermes survey (committed today)
