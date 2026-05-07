# Codex dispatch brief — #1773 bakeoff aggregator fixes (BAKEOFF BLOCKER)

> **Worktree:** `.worktrees/dispatch/codex/1773-aggregator-fixes`
> **Branch:** `codex/1773-aggregator-fixes`
> **Base:** `main`
> **Mode:** danger
> **Effort:** medium
> **Hard timeout:** 5400s
> **Silence timeout:** 1800s

## Worktree setup

```bash
git worktree add -b codex/1773-aggregator-fixes .worktrees/dispatch/codex/1773-aggregator-fixes
cd .worktrees/dispatch/codex/1773-aggregator-fixes
```

## Goal

Closes #1773. Pre-bakeoff Claude Opus xhigh validation found 4 BLOCK + 2 CONCERN issues in `scripts/audit/bakeoff_aggregate.py`. Without fixing them, the bakeoff REPORT.md misrepresents the data, picks winners by weighted-not-min, and silently passes theatre violations.

Read issue #1773 first for the full diagnosis.

## Files in scope

Primary: `scripts/audit/bakeoff_aggregate.py` (1171 LOC). Test: `tests/test_bakeoff_aggregate.py` (or create if missing) — add a `tests/test_bakeoff_aggregate_theatre.py` with the new fixture.

## BLOCK 1 — Theatre fields completely ignored

**Add a writer-prompt row** "Tool-theatre clean" — score 3 if `summary.tool_theatre_violation_count==0` AND no `writer_tool_theatre` events for that writer; score 0 if any. Wire into `writer_prompt_table` (around line 551) and into the winner gate.

## BLOCK 2 — `reviewer_fixes_unparseable` unhandled

In `read_jsonl` / `collect_bakeoff_data`, **flag any review run carrying `reviewer_fixes_unparseable`**. Surface as a top-of-report **REVIEWER PROTOCOL BROKEN** banner (h2 heading near the top of REPORT.md, before findings). Don't bury as a generic warning.

## BLOCK 3 — Suspicious-zero detection

`verify_density_score` (line 451) returns `(0, "0 calls")` for `tool_calls_total==0`. **Add detection:** when `telemetry_present` AND `summary.tool_calls_total==0` AND the writer's markdown contains tool-name strings (regex over `verify_words`, `search_definitions`, `mcp__sources__*`, etc.), raise a finding "writer cites tools but emitted zero calls — suspect cross-contamination/theatre." Use the same `_TOOL_CITATION_RE` from `linear_pipeline.py` if importable; otherwise mirror the regex.

## BLOCK 4 — Winner gate by min(dim), not weighted

Per `non-negotiable-rules.md` rule #5: `min(dim_scores) ≥ 8 to PASS`. The aggregator currently uses `content_weighted_scores` for winner selection (line 906-908).

**Fix:** Two-stage gate in `generated_findings`:
1. Drop any writer with `min_dim < 8` (cannot be winner)
2. Among survivors, rank by `tool_call_density × min_dim` (or just `min_dim` if density is tied)

Replace `weighted[writer] or -1` (line 909) with min-based key.

## CONCERN 5 — tool_call_density buried

User-stated winner criterion is currently buried in `tool_usage_table` (line 844-851). **Add a new top-level section** in REPORT.md generation: `## Winner ranking by tool-call density`, immediately after the header (before "Prompt adherence"). One row per writer: `density / theatre_violations / min_dim / verdict`.

Use `summary.tool_calls_total` (preferred) over `sum(writer_tool_counts(...))` (line 850) and warn on disagreement — disagreement signals a #1761/#1768 delivery bug.

## CONCERN 6 — `phase_writer_summary.tool_calls_total` shadowed

`event_summary()` (line 414) finds the right event but only `verify_words_calls` is read (line 456). The new `tool_calls_total` aggregate is silently shadowed by event-count recomputation at line 850.

**Fix:** Prefer summary value where present; cross-check against re-counted events; warn on drift.

## Tests

`tests/test_bakeoff_aggregate_theatre.py` (NEW):

- `test_writer_with_theatre_violations_excluded_from_winner`: synthetic JSONL fixture with `tool_theatre_violation_count=2`. Assert writer is excluded from "candidate winner" list.
- `test_winner_gate_uses_min_dim_not_weighted`: synthetic fixture with one writer at `min=4 weighted=9`, another at `min=8 weighted=7`. Assert the latter wins.
- `test_reviewer_fixes_unparseable_emits_protocol_broken_banner`: synthetic JSONL with the event. Assert REPORT.md contains "REVIEWER PROTOCOL BROKEN" heading.
- `test_suspicious_zero_calls_with_citations_flagged`: synthetic writer with `tool_calls_total=0` AND markdown containing `verify_words`. Assert finding raised.
- `test_winner_ranking_section_present`: assert REPORT.md has the new top-level section.

## Validation

```bash
.venv/bin/pytest tests/test_bakeoff_aggregate*.py -v
.venv/bin/ruff check scripts/audit/bakeoff_aggregate.py
.venv/bin/python scripts/audit/bakeoff_aggregate.py --bakeoff-dir audit/bakeoff-2026-05-05 --output /tmp/test-aggregate.md  # smoke against the prior bakeoff data
```

The smoke run should regenerate REPORT.md from the prior bakeoff data with the new sections + corrected winner-gate logic.

## PR

Title: `fix(bakeoff-aggregate): theatre awareness + min-dim winner gate + protocol-broken banner (#1773)`

PR body must include:
- Recap of the 4 BLOCKs + 2 CONCERNs
- Confirmation that the new tests cover all of them
- Sample output (paste a snippet of regenerated REPORT.md showing the new sections)
- `Closes #1773`

**NO auto-merge.** Orchestrator (Claude) reviews + merges after a follow-up adversarial review.

## Adversarial review

```bash
git diff origin/main..HEAD > /tmp/1773-diff.txt
.venv/bin/python scripts/delegate.py dispatch \
    --agent claude --model claude-opus-4-7 --effort xhigh --mode read-only \
    --task-id 1773-fix-review --hard-timeout 600 \
    --prompt "Adversarial review for #1773 (bakeoff aggregator fixes). Read /tmp/1773-diff.txt. Verify: (A) all 4 BLOCKs from issue body actually fixed, (B) winner-gate now uses min_dim with the 8-threshold rule, (C) regression tests would catch reintroduction of any BLOCK, (D) the new sections in REPORT.md don't break downstream consumers (e.g., gh issue automations). Tag BLOCK / NIT / OK. <500 words."
```

Apply feedback. Commit with `Reviewed-By: claude-opus-4-7 (1773-fix-review)` trailer.
