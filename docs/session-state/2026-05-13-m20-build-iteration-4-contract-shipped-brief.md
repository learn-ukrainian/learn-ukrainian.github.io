---
date: 2026-05-13
session: "Continuation of m20 build iteration arc. 4 PRs merged this session (parser, writer-prompt schema, vesum scope, a1-m15-24 shape contract). Multi-agent discussion converged on gates 2-4 contract; Decision Card PROPOSED + implemented same session. m20 build #4 advanced through writer phase but halted at python_qg with NEW failure class: gate-counter / DialogueBox-shape mismatch (#1965). Plus residual vesum suffix leaks, pre-existing textbook_grounding corpus_missing, and writer-behavior regression on resources search."
status: in_progress_gate_counter_alignment
main_sha: ae82d1ddc1  # after PR #1964 (a1-m15-24 contract bundle)
main_green: true
agents: [claude, codex, gemini]
worktrees_open: 7  # main + 4 m20 failed-build worktrees (122043, 161726, 164953, 193448) + 2 inherited held-PR worktrees
ci_notes: "All 4 shipped PRs (#1957, #1961, #1963, #1964) passed all blocking checks; advisory Gemini review/review failed each time (non-blocking)."
m20_build_progress: |
  Build #1 (122043): halted at writer-output parser bug → fixed #1957
  Build #2 (161726): halted at resources.yaml schema gap → fixed #1961
  Build #3 (164953): halted at python_qg vesum_verified after ADR-008 correction → fixed #1963 (gate 1) + Decision Card written for gates 2-4
  Build #4 (193448): halted at python_qg with NEW failure class:
    - vesum_verified: 6 of original 11 suffix forms still leak (different surface)
    - textbook_grounding: HARD REJECT corpus_missing (pre-existing #1901, hardened from WARN)
    - resources_search_attempted: writer made 0 multimedia search calls (vs 2 in build #3) — writer-prompt regression
    - l2_exposure_floor: writer used <DialogueBox uk=".." en=".." /> (correct per #1964 contract), but gate counter `_jsx_text_values` only extracts text= prop, missing uk= prop → counted 0 instead of 10 dialogue lines (#1965)
    - component_density: same uk=/en= prop pattern miscounted by `_component_language_text` (#1965)
next_p0: |
  m20 build #4 halted with 5 gate failures. Critical observation: the
  writer is now PRODUCING the right SHAPE (DialogueBox with uk=/en= props,
  correct dialogue structure, citation discipline followed) but the GATE
  COUNTERS don't recognize this V7 React component convention.

  Filed: #1965 — `_jsx_text_values` only extracts text= attribute; misses
  uk= (V7 DialogueBox convention) + component_density gate calculation
  conflates bilingual-prop-pair with low-immersion. **Highest-leverage
  single fix** — ~10-20 LOC change + tests, unblocks 2 gate failures.

  Other unfixed gate failures from build #4 (file follow-ups during next
  session diagnosis):

  1. vesum_verified residual leaks: 6 suffix forms still missing
     (`юся, ються, ємося, єтеся, ється, єшся`). Build #3's PR #1963 fixed
     the activity-distractor surface; these must be coming from a
     different surface — possibly the conjugation table cells in module.md
     or vocabulary.yaml. Need diagnosis: grep build worktree's
     `*.yaml` + `module.md` for these literal fragments.

  2. textbook_grounding corpus_missing HARD: PRE-EXISTING #1901, NOT caused
     by today's work. Build #3 was WARN (1 matched of 3); build #4 hardened
     to HARD (0 of 3 matched) — writer's specific quote attempts didn't
     match indexed corpus chunks. Either expand textbook corpus ingestion
     OR loosen plan_references to use textbooks present in corpus.

  3. resources_search_attempted = 0: writer made ZERO `query_wikipedia`/
     `search_external`/`search_images` calls in build #4. Build #3 had 2.
     Either the new contract directives crowded out the multimedia
     search obligation, OR the writer prompt's resources section needs
     reinforcement under the new shape contract.

  Recommended next-session sequence:
    (1) Fix #1965 (highest-leverage; 10-20 LOC parser tweak; mechanical
        codex dispatch).
    (2) Diagnose vesum residual: read build #4 worktree artifacts for the
        6 suffix fragments; file targeted issue for the surface; small
        scope-tightening fix.
    (3) Diagnose resources_search_attempted regression: read writer prompt
        + build #4 telemetry to understand why writer skipped multimedia
        search. May need prompt-priority reinforcement.
    (4) Decide on #1901 corpus_missing: either accept WARN-not-HARD for
        out-of-corpus textbook plan_refs OR re-ingest the missing pages.
    (5) Re-run m20 build #5 after all 4 fixes land. Realistic target:
        m20 GREEN within 1-2 more build cycles.

  After m20 GREEN: Phase 2b m01-m07 `/goal` batch per existing brief.

  Build worktree preserved at `.worktrees/builds/a1-my-morning-20260513-193448/`
  for #1965 + residual diagnosis.
---

# Session 2026-05-13 — m20 build iteration 4 + a1-m15-24 contract shipped

> Continuation of `docs/session-state/2026-05-13-m20-build-iteration-3-content-gates-brief.md`. This session shipped 2 more PRs (#1963 vesum scope + #1964 a1-m15-24 contract bundled) on top of the morning's #1957 + #1961. m20 build #4 ran cleanly through writer phase under the new contract, halted at python_qg with a different gate-counter alignment class. Handing off to a new session with #1965 filed as the highest-leverage next fix.

## TL;DR

The "process-correct writer behavior reveals upstream gap" pattern continued one layer deeper. Today's 4 PRs each surfaced and fixed a class of writer/parser/gate cooperation gap. Build #4's failure mode is the NEXT layer: gate counters calibrated against an older V7 component shape (`text=` prop) don't recognize the writer's natural shape under the new contract (`uk=` prop). One more bundled fix likely closes the loop.

Card 1 writer-isolation Tier 1 remains GREEN every build. The contract DID change writer behavior in measurable ways:

| Behavior | Build #3 | Build #4 |
|---|---|---|
| DialogueBox usage | 0 | 10 elements |
| Em-dash dialogue under `## Діалоги` | 14 lines | 0 (replaced by DialogueBox) |
| Citation form | Author + initials + та ін. (Ukrainian publishing convention) | Plan-references conformant (terse) |
| Pages referenced | p.112 (Кравцова), p.119-120 (Захарійчук), 6th grade Аврамченко | p.176 (Караман), p.113 (Кравцова), p.162 (Захарійчук) — match plan_references exactly |
| Multimedia search calls | 2 (query_wikipedia + search_text) | 0 |
| Total words | 1226 | unknown (didn't reach word_count gate fresh) |
| Tier 1 verification | GREEN | GREEN |

The contract worked. The gate just didn't keep up.

## What changed on main today (full 4-PR session arc)

| PR | Closes | Effect | Main SHA |
|---|---|---|---|
| #1957 | #1956 | Parser preceding-label tightening + 2 stale fixture unblocks | 7bed977983 |
| #1961 | #1959 | Writer-prompt resources.yaml schema-alignment | 64007d9cb5 |
| #1963 | #1962 gate 1 | VESUM gate scope across 4 leak surfaces | 44e6e9a964 |
| #1964 | #1962 gates 2-4 | a1-m15-24 shape contract (writer prompt + gate counter + matcher) | ae82d1ddc1 |

## Multi-agent design that shipped today

`ab channel tail a1-m15-24-shape-contract --thread 767f107789e241919a36f573be37d4ca` — Codex + Gemini converged on the shape contract in 2 rounds. Key insight (Codex r1, Gemini r2 [AGREE]):

> The l2_exposure_floor failure is NOT a calibration error. m20 HAS 14 dialogue turns. `_count_uk_dialogue_lines` only counts `> ` blockquote or `<DialogueBox>` text — em-dash convention misses the gate. Fix at writer prompt (mandate gate-readable form), not by lowering floor.

This was correct. The fix shipped. The build #4 surfaced the OTHER half of the same class: gate-counter doesn't recognize the WRITER's natural attribute shape either. #1965 catches this.

## Issues filed today

| Issue | Subject | Status |
|---|---|---|
| #1958 | 2 pre-existing red tests on main (stale assertion drift) | Open, queued |
| #1960 | Wiki ingestion gap (`ext-article-N` placeholder stubs) | Open, deferred systemic |
| #1962 | 4 content-class gate gaps from build #3 | Closed (gates 1-4 all addressed in #1963 + #1964) |
| #1965 | `_jsx_text_values` only extracts `text=` not `uk=` (DialogueBox uk= prop convention) | **Open, P0 next session** |

## Decision Cards

`docs/decisions/pending/2026-05-13-a1-m15-24-shape-contract.md` — PROPOSED. Defaults were used to ship PR #1964. Card can move to `docs/decisions/2026-05-13-...` ACCEPTED state after verifying m20 advances to module_done with #1965 fix landed.

## Build worktrees preserved

| Path | Halt | Status |
|---|---|---|
| `122043` | Parser bug | Resolved by #1957; keep for archive comparison |
| `161726` | resources schema | Resolved by #1961; keep for archive comparison |
| `164953` | python_qg vesum + 3 others | Resolved by #1963 + #1964; keep for archive comparison |
| `193448` | python_qg, 5 gate failures incl. #1965 | **Active evidence for #1965 + residual vesum diagnosis** |

## Dispatches this session

| Task ID | Agent | Duration | Result |
|---|---|---|---|
| `parser-label-tightening-2026-05-13` | codex/high | 279s | done; orchestrator-rescued |
| `writer-prompt-resources-schema-2026-05-13` | codex/high | 195s | clean exit, PR #1961 |
| `vesum-gate-scope-2026-05-13` | codex/high | 335s | clean exit, PR #1963 |
| `a1-shape-contract-2026-05-13` | codex/high | 350s | clean exit, PR #1964 |

Plus 1 multi-agent discussion (`ab discuss a1-m15-24-shape-contract`, codex+gemini, 2 rounds, gemini round-2 [AGREE]).

Codex weekly quota burn this session: ~4 dispatches × 5min ≈ 20 min of Codex high-effort time. Well within budget.

## Recurring pattern (theme of the day)

**Every fix today was "writer behaved correctly per its prompt; the upstream parser/gate/schema wasn't ready for the writer's natural shape."** Card 1's writer-isolation cleanly separates writer correctness from infra correctness, letting us see this class clearly:

| Build | Writer shape (correct per prompt) | Upstream gap |
|---|---|---|
| #1 | Fence-info-string label form | Parser scraped preceding-label from CoT prose |
| #2 | Kept podcast reference as wiki cited it | Schema required url for non-textbook role |
| #3 | Fill-in distractors + anti-Russianism quotes | VESUM gate over-extracted from non-Ukrainian-assertion surfaces |
| #4 | DialogueBox with uk=/en= props | Gate counter only extracts text= prop |

The pattern: writer prompts emit clearer expectations than gate counters parse. Aligning the two is mechanical work. Each fix moved m20 one halt-class forward.

## Phase 2 status (per `2026-05-13-ulp-derived-student-aware-immersion.md`)

- **Phase 2a** (m20 rebuild as student-aware first A1 module): **in progress, 4 builds attempted, contract shipped, ~1 more fix cycle estimated**.
- **Phase 2b** (m01-m07 warm-up batch): **queued behind m20 GREEN**. Brief at `docs/dispatch-briefs/2026-05-13-phase-2b-m1-m7-warmup-batch.md`. Candidate `/goal` invocation per `goal-driven-runs.md` predicate-bounded batch shape.

## Open queue (P0 → Pn)

- **P0:** #1965 — gate counter `_jsx_text_values` doesn't extract `uk=` attribute (highest-leverage; unblocks 2 m20 gates).
- **P0 paired:** diagnose + file residual vesum surface for the 6 remaining suffix leaks.
- **P0 paired:** diagnose + file resources_search_attempted writer-behavior regression.
- **P1:** #1901 textbook_grounding corpus_missing decision (accept WARN or re-ingest pages).
- **P1:** #1958 stale-assertion test drift on main.
- **P1:** #1960 wiki ingestion gap (`ext-article-N` placeholder stubs — deeper systemic).
- **P2 background:** #1942 (forbid pytest -x in dispatch briefs), #1941 (A1-checkpoint word_target inconsistency), #1940 (pedagogical_deviations plan field), #1933 (/goal v2 wishlist).

## Predecessor brief

`docs/session-state/2026-05-13-m20-build-iteration-3-content-gates-brief.md` — close of previous mid-session checkpoint (after 2 PRs, before the contract Decision Card / discussion / implementation).

## Next session opening action

1. Read this brief.
2. `curl -s 'http://localhost:8765/api/orient'` — confirm main at `ae82d1ddc1` (or newer if more PRs landed).
3. Read #1965 — fix design is in the issue body.
4. Dispatch `_jsx_text_values` + `_component_language_text` fix (small bundled PR).
5. Diagnose + file build #4's residual vesum surface (read build worktree's activities.yaml, vocabulary.yaml, module.md tables for the 6 suffix fragments).
6. Decide on #1901 corpus_missing approach.
7. After both fixes land: m20 build #5. Realistic GREEN target.

---

*Format spec: `claude_extensions/rules/workflow.md` § "Two-tier handoffs". MD-only per #M-2 ai→ai for orchestrator-loadable content; HTML companion deferred.*
