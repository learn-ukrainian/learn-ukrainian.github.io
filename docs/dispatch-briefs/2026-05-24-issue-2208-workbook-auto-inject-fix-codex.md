# Issue #2208 — fix writer-prompt forcing workbook activities inline

**Date**: 2026-05-24
**Agent**: codex
**Mode**: danger
**Effort**: medium
**Wall budget**: 40 min

## Why

`scripts/build/phases/linear-write.md` currently instructs the writer that EVERY activity in `activities.yaml` MUST be inline-referenced in `module.md` via `<!-- INJECT_ACTIVITY: ... -->` markers. This:

- Forces all activities into the inline tab → empty Activities tab (workbook section).
- Caused the m20 a1/my-morning revert at commit `944f4200e4` (Activities tab empty, 10/10 inline split).
- Blocks the m20 anchor ship even after today's 5 merged PRs (#2256-#2260).

The V7 design contract per `docs/best-practices/v7-design-and-corpus.md` Section 1.4 is:
- A1: ~10 activities total, **~4-6 inline** + **~6-9 workbook**.
- Inline = sparse lesson interruptions woven into prose.
- Workbook = the majority of practice; lives in Activities tab.
- ONLY inline activities require `<!-- INJECT_ACTIVITY -->` markers.

## Read first

1. `gh issue view 2208` (acceptance criteria)
2. `docs/best-practices/v7-design-and-corpus.md` (Section 1.4 — INLINE vs WORKBOOK contract)
3. `scripts/build/phases/linear-write.md` — find the section saying "every activity must be inline-referenced" or equivalent. Likely in the activities-emission contract block.
4. `tests/build/test_writer_pre_emit_checklist.py` + `tests/test_prompt_cot_tier1_scaffolding.py` — these have literal-string assertions that must keep passing.
5. `audit/2026-05-24-writer-prompt-competing-rules.md` — context on the writer-prompt audit pattern.
6. `.worktrees/builds/a1-my-morning-20260524-162518/curriculum/l2-uk-en/a1/my-morning/activities.yaml` — empirical evidence: composer-2.5 produced 4 inline / 0 workbook (under-production AND no workbook). Different anti-pattern but informs the fix.

## What to do

1. Locate the writer-prompt section that currently says "every activity must be inline-injected" (or equivalent wording forcing inline-only).
2. Rewrite per the V7 design contract:
   - State the **INLINE / WORKBOOK split intent** explicitly: A1 target ~10 activities, ~4-6 inline + ~6-9 workbook. Include the per-level breakdown if the prompt addresses multiple levels (B1 / C1 / etc. — check `ACTIVITY_CONFIGS` in `scripts/build/linear_pipeline.py` for the floor/ceiling values).
   - Make clear: **ONLY inline activities** require `<!-- INJECT_ACTIVITY: act-N -->` markers in `module.md`.
   - **Workbook activities omit `id`** (per `WRITER_JSON_SCHEMAS["activities.yaml"]` post-PR-#2218 — `id` is optional for workbook entries).
   - Pedagogical framing: inline = sparse lesson interruptions woven into prose; workbook = the majority of practice, lives in Activities tab (Tab 3).
3. Do NOT remove the `INJECT_ACTIVITY` mechanism — it's needed for inline activities. Just stop the prompt from instructing the writer to inject ALL activities.
4. Verify the post-PR-#2260 structural markers stay intact (the 7-test regression we just fixed). Run:
   ```
   .venv/bin/pytest tests/test_linear_pipeline_wiki_coverage.py tests/test_prompt_cot_tier1_scaffolding.py tests/build/test_writer_pre_emit_checklist.py tests/build/test_linear_pipeline.py -v 2>&1 | tail -20
   ```
   All must pass.
5. Run prompt size check: `.venv/bin/python scripts/audit/check_writer_prompt_size.py 2>&1 | tail -3`. Must stay under 130KB ceiling. This fix likely ADDS some explanatory text — if size goes over, compress something else (NOT the Option B fixes or the structural markers — those are load-bearing).
6. Verify the change doesn't undo:
   - PR #2260 Option B fixes (citation-authority hierarchy, chunk_id-first protocol, resources.yaml plan-only rule)
   - PR #2257 plan_reference_match gate wiring
   - Activities schema (id optional for workbook per PR #2218 / merged in citation_matcher work)

## REQUIRED steps (numbered)

1. From project root: `git fetch origin && git worktree add -b fix/issue-2208-workbook-auto-inject .worktrees/dispatch/codex/issue-2208-2026-05-24 origin/main`
2. `cd .worktrees/dispatch/codex/issue-2208-2026-05-24 && ln -s ../../../../.venv .venv` (# venv symlinked)
3. Read the 6 files in "Read first" list.
4. Apply the fix to `scripts/build/phases/linear-write.md`. After edit, `git diff scripts/build/phases/linear-write.md | head -80` and verify visually.
5. Run prompt tests (step 4 in "What to do" above). Must pass.
6. Run prompt size check. Must be under 130KB.
7. Commit with conventional message: `fix(writer-prompt): inline-only INJECT_ACTIVITY contract; workbook activities stay in Activities tab (closes #2208)`.
8. `git push -u origin fix/issue-2208-workbook-auto-inject`
9. `gh pr create --base main --title "fix(writer-prompt): INLINE/WORKBOOK split — close auto-inject anti-pattern (#2208)" --body "..."`
10. `gh pr checks <NEW_PR> --watch --interval 15` until green.
11. Report final state. NO auto-merge.

## Verifiable claims

| Claim | Evidence |
|---|---|
| "Prompt no longer forces all activities inline" | `git diff scripts/build/phases/linear-write.md` showing the contract rewrite |
| "Tests pass" | pytest final line raw |
| "Prompt size under 130KB" | `check_writer_prompt_size.py` raw |
| "PR opened" | `gh pr view --json url` raw |
| "CI green" | `gh pr checks <N> --json bucket` showing all pass (modulo F7 advisory) |

## Anti-fabrication (#M-4)

Every claim tool-backed. Quote raw outputs. Don't paraphrase the writer-prompt rewrite — show the diff hunk.

## After this lands

The next step is to fire m20 build with claude-tools writer (user-OK'd for the anchor). Issue #2208 fix is the prerequisite — claude-tools previously hit the same auto-promote pattern, so fixing #2208 unblocks claude-tools from regressing on the Activities-tab-empty failure mode.
