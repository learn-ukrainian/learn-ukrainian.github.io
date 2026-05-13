---
date: 2026-05-13
target: USER-RUN (V7 builds are USER-RUN ONLY per CLAUDE.md)
phase: 2b — A1 first-checkpoint warm-up batch
modules: a1/sounds-letters-and-hello (m01) → a1/reading-ukrainian (m02) → a1/special-signs (m03) → a1/stress-and-melody (m04) → a1/who-am-i (m05) → a1/my-family (m06) → a1/checkpoint-first-contact (m07)
prerequisites:
  - Phase 2a passed — a1/my-morning rebuilt successfully with all Tier 1 + Tier 2 + Tier 3 predicates green
  - Card 1 merged (curriculum-writer agent live, infra_context_contamination gate live)
  - All other prerequisites from Phase 2a remain (PR #1939, #1943, #1950, #1952, #1953 all merged)
---

# Phase 2b — A1 m01-m07 warm-up batch (first-checkpoint deliverable)

## Why this batch

After Phase 2a validates the student-aware pipeline on the hardest case (m20 knee transition), Phase 2b builds the **first 7 A1 modules in order**. This is the A1 first-checkpoint deliverable — m07 (`checkpoint-first-contact`) is the first checkpoint module per the curriculum design.

This batch tests:

1. **Band progression through 2 knees** — m01-m03 → `a1-m01-03` band (5-25%), m04-m06 → `a1-m04-06` (8-30%) at the cumulative_vocab=140 knee, m07 → `a1-m07-14` (10-38%) at the cumulative_vocab=242 knee. The ULP-derived `compute_immersion_band()` should land each module in the correct band.
2. **Learner-state warm-up** — m01 has cumulative_vocab=0 (no prior vocab); by m07, ~242 lemmas + several grammar topics. Tests the empty-state and growing-state behavior of `learner_state.py` + the `{LEARNER_STATE}` writer-prompt injection.
3. **Writer isolation at scale** — 7 sequential dispatches, none should contaminate. If even one trips `infra_context_contamination`, that's a real regression worth diagnosing.
4. **Recycle cadence under low-vocab** — at m01-m03, recycle cadence isn't really applicable (warm-up; few lemmas to revisit). Gate should stay quiet at WARN severity.

## Recommended execution: sequential, one-at-a-time

Don't parallelize this batch. Each module's `LEARNER_STATE` depends on PRIOR modules' merged outputs being on `main`. If you parallelize, each worker sees an outdated learner state.

Sequential pattern: build m01 → audit → commit + merge to main → build m02 → audit → commit + merge → ... → build m07.

### Per-module invocation

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
.venv/bin/python scripts/build/v7_build.py a1 {slug} --worktree
```

where `{slug}` cycles through:

| # | slug | Expected band | Cumulative_vocab at start |
|---|---|---|---|
| m01 | `sounds-letters-and-hello` | `a1-m01-03` (5-25%) | 0 |
| m02 | `reading-ukrainian` | `a1-m01-03` (5-25%) | ~40-50 |
| m03 | `special-signs` | `a1-m01-03` (5-25%) | ~85-105 |
| m04 | `stress-and-melody` | `a1-m04-06` (8-30%) — KNEE 1 (cumulative_vocab=140) | ~140 |
| m05 | `who-am-i` | `a1-m04-06` (8-30%) | ~180-200 |
| m06 | `my-family` | `a1-m04-06` (8-30%) | ~210-230 |
| m07 | `checkpoint-first-contact` | `a1-m07-14` (10-38%) — KNEE 2 (cumulative_vocab=242) | ~242+ |

(Cumulative_vocab estimates derived from the ULP S1 lesson-1-through-7 raw.jsonl entries in `audit/ulp-calibration-2026-05-13/raw.jsonl`. Actual numbers depend on what each plan declares as new vocabulary.)

### Per-module acceptance predicates

Same Tier 1 / Tier 2 / Tier 3 predicate set as Phase 2a (see `docs/dispatch-briefs/2026-05-13-phase-2a-m20-my-morning-rebuild.md`). Special attention per module:

- **m01**: cumulative_vocab=0 — learner-state should report empty/initial state. Writer prompt's `{LEARNER_STATE}` should still render cleanly (graceful empty-state, not crash).
- **m03 → m04 transition**: writer prompt for m04 should show cumulative_vocab ~140 and use the `a1-m04-06` band, NOT `a1-m01-03`. If it lands in the wrong band, the ULP knee-fitting may be off-by-one.
- **m06 → m07 transition**: same check at cumulative_vocab ~242. m07 is also a checkpoint module — verify the writer treats it appropriately (review-style, no new core vocab dump).

### Between-module workflow

After each module's build:

1. **Inspect the worktree** at `.worktrees/builds/a1-{slug}-{stamp}/`.
2. **Verify the predicates** (Tier 1-3 from Phase 2a brief).
3. **If green**: commit + push + PR + merge. The next module's learner-state depends on this one's vocab being on `main`.
4. **If red**: stop the batch, surface the failure, do NOT continue. Diagnose before resuming.

## Batch-completion success criteria

- [ ] All 7 modules built green with no `infra_context_contamination` halts
- [ ] All 7 modules committed + merged to main
- [ ] m04 and m07 demonstrably landed in their correct post-knee bands (verifies the calibration)
- [ ] m07 (checkpoint) renders correctly with checkpoint-appropriate content (review of m01-m06, no new heavy vocab)
- [ ] Total batch time tracked (data point for Phase 3 dispatch sizing)

## On batch completion

1. **Update session-state index** at `docs/session-state/current.md` with the A1 first-checkpoint progression.
2. **Optionally rebuild m20 (`a1/my-morning`) again** — now that m01-m07 are on `main`, the learner-state for m20 has FULL fidelity (not synthesized from prior-session vocab estimates). The output should be substantively the same as Phase 2a, but with cleaner provenance.
3. **Phase 3** — resume the broader A1 build queue (modules m08 onward). Decision Card § Phase 5 — "second A1 pilot" was originally `around-the-city` (m23) but the natural sequence after the checkpoint is m08 (`numbers-1-10` or whatever m08 actually is — check `curriculum.yaml`).

## Recovery scenarios

| Scenario | Response |
|---|---|
| m01 fails on `MCP_TOOLS_NEVER_INVOKED` (writer made zero source lookups on the simplest module) | Card 1's writer agent may be over-restricted. Read writer's stdout. The first module is the hardest UX challenge for a tool-restricted writer — if it can't source on m01, it can't source anywhere. |
| Band landing is off-by-one (e.g., m04 lands in `a1-m01-03` instead of `a1-m04-06`) | ULP knee constant in `scripts/config.py:_ULP_VOCAB_KNEE_PER_BAND['a1']` was calibrated against S1 lesson 4 = 140 cumulative_vocab. If m04's actual cumulative_vocab is <140 (because plans declare fewer new words than ULP S1's lesson 4), the knee won't trigger. Either recalibrate the knee (likely Phase 4 follow-up) or expand the m01-m03 plans' new_vocabulary declarations. |
| m07 checkpoint comes out content-heavy (full new vocab dump instead of review) | Writer prompt + checkpoint plan should both signal "review module, no new vocab unless declared." If they don't, this is a prompt-engineering follow-up, not a system regression. |
| Tier 3 visual contract fails on ANY module | MDX assembler issue. Recently overhauled in #1930. Investigate the assembler logs, not the writer output. |

## Why sequential, not parallel

Even though each module has its own worktree (per #1952 `--worktree` flag), parallelizing the BATCH leads to stale learner-state. A worker building m04 in parallel with m02 won't see m02's merged vocab in its base SHA. The merged-main snapshot model only works when each next worker branches off AFTER the previous lands.

If parallelism becomes attractive later (Phase 3 with 20+ modules), the right architecture is a parallel-aware learner-state cache that merges per-module vocab additions in a known order — out of scope for Phase 2b. Sequential is fine for 7 modules.
