---
date: 2026-05-13
session: "Continued m20 (a1/my-morning) V7 rebuild arc. 3 builds, 2 PRs merged. m20 advanced from 'halted at parser bug' (start of session) → 'halted at python_qg content-gate cluster after ADR-008 correction'. Tier 1 writer-isolation continues GREEN; Card 1 boundary holds. Remaining 4 gate failures are content/calibration issues, not pipeline/infra bugs."
status: in_progress_content_gates
main_sha: 64007d9cb5  # after PR #1957 (parser fix) + PR #1961 (writer-prompt schema-alignment)
main_green: true
agents: [claude, codex]
worktrees_open: 6  # main + 3 m20 failed-build worktrees (122043 + 161726 + 164953) + 2 inherited dispatch held-PR worktrees
ci_notes: "Both shipped PRs (#1957, #1961) passed all blocking checks; only advisory Gemini review/review failed (non-blocking)."
m20_build_progress: |
  Build #1 (122043): halted at writer-output parser (#1956, fixed in #1957).
  Build #2 (161726): halted at resources.yaml schema (#1959, fixed in #1961).
  Build #3 (164953): halted at python_qg vesum_verified after ADR-008 correction (#1962, 4 gates).
next_p0: |
  m20 build #3 cleared writer phase + ADR-008 correction. 14 gates passed:
  word_count (1226), plan_sections (all 4 budgeted sections in range), formatting,
  textbook_grounding (WARN — corpus_missing, known issue), resources_search_attempted,
  immersion_advisory (37.98% in policy a1-m15-24 advisory band), component_density,
  inject_activity_ids (4 used, 6 unused — non-blocking), activity_types (10 types
  valid), ai_slop_clean, component_props, russianisms/surzhyk/calques/paronym all clean.

  4 gates FAILED, surfacing distinct content-class gaps tracked in #1962:

  1. vesum_verified (TERMINAL): 11 "missing" forms are activity DISTRACTORS,
     anti-Russianism quoted contrasts, and English meta-linguistic notes —
     not Ukrainian-word assertions. Gate scope is too broad across artifacts.
     Easiest standalone fix; can dispatch independently.

  2. citations_resolve: writer cited 3 textbooks with author-initials + та ін.
     + page-shifts that don't match plan_references' condensed "Author Grade pN"
     form. Plus 1 textbook (Аврамченко) not in plan. Writer drift vs plan.

  3. l2_exposure_floor: writer produced 5 UK dialogue lines, band a1-m15-24
     requires 14. Writer wrote 2 short dialogues; Phase B floor may be miscalibrated
     OR writer prompt needs to pass the floor through. Joint calibration issue.

  4. long_uk_ceiling: 4 offending UK runs >28 words without close gloss.
     2 are dialogue blocks (writer glossed at block-bottom instead of inline),
     2 are verbatim textbook blockquotes (sources, not learner-target prose).

  Recommended next session:
    (1) Open Decision Card / multi-agent discussion: "a1-m15-24 module shape contract"
        — joint thinking on dialogue-line floor, gloss strategy, citation discipline,
        and what counts as Ukrainian-word for vesum verification. The 4 gates interact.
    (2) Dispatch independent fix for #1962 gate 1 (vesum-distractor-blindness) —
        mechanical-ish, scope-aware extraction across module.md prose vs
        activities.yaml distractors vs vocabulary.yaml translation field.
    (3) After Decision Card lands: dispatch gates 2-4 fixes in sequence or batch.
    (4) Re-run m20 build #4 after each fix lands.

  Build worktree at .worktrees/builds/a1-my-morning-20260513-164953/ preserved
  as primary evidence. python_qg.json holds all gate observations.
---

# Session 2026-05-13 — m20 build iteration arc (3 attempts, 2 PRs merged, 4 content gates surface)

> Continuation of `docs/session-state/2026-05-13-rule-correction-m20-build-firing-brief.md`. The predecessor handed off a failed m20 build with primary evidence at `.worktrees/builds/a1-my-morning-20260513-122043/`. This session ran the parser-fix → re-run → writer-prompt-fix → re-run → content-gate cluster loop and is handing off to a new session with the 4 remaining issues consolidated in #1962.

## TL;DR

Three iterative m20 build attempts, each halted at a successively deeper gate, each producing a clean PR fix that unblocked the next. Card 1 writer-isolation continues to validate (Tier 1 always green, all writer tool calls in `mcp__sources__*` family). The two PRs shipped today were **process-correct writer behaviors revealing upstream prompt/parser gaps** — same shape as the Card 1 class boundary predicted. The 4 remaining gates are a different class: content quality, calibration, and gate-scope. They merit joint design thinking before independent fixes.

## What changed on main today

| PR | Closes | Effect |
|---|---|---|
| #1957 | #1956 | Parser preceding-label-line tightening + 2 stale fixtures unblocked |
| #1961 | #1959 | Writer prompt schema-alignment: non-textbook role REQUIRES url, OMIT if no verified URL |

Plus follow-up issues filed:

| Issue | Subject | Status |
|---|---|---|
| #1958 | 2 pre-existing red tests on main from schema/template drift | Open, queued |
| #1960 | Wiki ingestion gap: `ext-article-N` placeholder stubs in `wiki/pedagogy/*.sources.yaml` | Open, systemic deeper fix |
| #1962 | 4 content-class gate gaps surfaced by m20 build #3 | Open, today's primary handoff |

## Card 1 validation (continued from predecessor)

Across 3 builds, the `curriculum-writer` agent's Tier 1 verification stayed GREEN every time:

| Build | tool_calls_total | verify_words_calls | tool_theatre_violations | end_gate_fired | infra_context_contamination |
|---|---|---|---|---|---|
| #1 (122043) | 12 | 5 | [] | true | quiet |
| #2 (161726) | 13 | 5 | [] | true | quiet |
| #3 (164953) | (eventually rolled into phase_done writer 397s) | — | [] (writer phase clean) | true | quiet |

Build #3's `phase_done writer 397.159s` event is the first time we've seen the writer cleanly complete on m20. Card 1's class boundary is real: writer-isolation prevents context contamination AND lets us see upstream prompt/parser/gate issues clearly without false-flags from Bash/Read leak.

## The 4 remaining gates (consolidated in #1962)

### Gate 1 — vesum_verified TERMINAL (easiest standalone fix)

11 "missing" forms are gate scope errors: gate extracts tokens from activity DISTRACTORS in `activities.yaml` (suffix fragments `юся`, `єшся`, `ється` etc. are intentional fill-in options), from anti-Russianism quoted contrasts in `vocabulary.yaml` (`«завтрак»` is the wrong-Russian-form learners must NOT use), and from English meta-linguistic notes (`(стем + -л-...)` where "стем" is English "stem"). The fix is scope-aware extraction per artifact.

### Gate 2 — citations_resolve

Writer used Ukrainian-publishing-convention citation strings (`Кравцова Н. М. та ін. Українська мова, 4 клас, с. 112`) while plan_references uses condensed form (`Кравцова Grade 4, p.113`). Writer also added a textbook (Аврамченко 6 клас) not in plan. Three fix paths in #1962 (tighten prompt vs loosen matcher vs allow additive).

### Gate 3 — l2_exposure_floor

`a1-m15-24` band requires 14 UK dialogue lines; writer produced 5 across 2 short dialogues. Either the writer prompt needs to surface the band-required floor explicitly, or Phase B calibration of `uk_dialogue_lines: 14` is too strict for short-dialogue module shapes.

### Gate 4 — long_uk_ceiling

4 offending UK runs >28 words without close gloss support. Writer glossed dialogue blocks at block-bottom instead of inline (within 8 words). Verbatim textbook blockquotes have no English support at all (they're source material, not learner-target prose).

## Open architectural question for next session

These 4 gates interact. An "a1-m15-24 module shape contract" would name:
- dialogue-line floor + gloss-proximity convention
- citation discipline (verbatim plan_references vs additive vs fuzzy match)
- what counts as Ukrainian-word for vesum verification (prose-only vs all-artifacts)
- whether verbatim source blockquotes are exempt from gloss-proximity rules

Independent fixes risk regression: tightening the writer prompt for dialogue-lines may interact with long_uk_ceiling; loosening vesum scope may interact with russianisms_clean.

Recommended: Decision Card or `ab discuss a1-m15-24-shape-contract --with codex,gemini` to converge before dispatching individual gate fixes.

## Worktrees status

| Path | Purpose | Disposition |
|---|---|---|
| `.worktrees/builds/a1-my-morning-20260513-122043/` | m20 build #1 (parser-bug halt) | Now resolved; keep for comparison or remove |
| `.worktrees/builds/a1-my-morning-20260513-161726/` | m20 build #2 (resources schema halt) | Now resolved; keep for comparison or remove |
| `.worktrees/builds/a1-my-morning-20260513-164953/` | m20 build #3 (vesum_verified halt — current evidence) | **Preserve** — primary evidence for #1962 |
| `.worktrees/codex-interactive/` | Inherited | Held |
| `.worktrees/dispatch/claude/bakeoff-2026-05-12-night/` | Inherited held-PR | Held |
| `.worktrees/dispatch/claude/writer-prompt-tune-2026-05-13/` | Inherited held-PR | Held (SUPERSEDED by #1961 — recommend close) |
| `.worktrees/dispatch/codex/pass2-only-contract-test-2026-05-13/` | Inherited held-PR | Held |

## Session dispatches

| Task ID | Agent | Effort | Duration | Result |
|---|---|---|---|---|
| `parser-label-tightening-2026-05-13` | codex (gpt-5.5) | high | 279s | done; orchestrator-rescued commit+push (Codex halted on pre-existing main-red tests; verified pre-existing on main@d1a2d9b13d) |
| `writer-prompt-resources-schema-2026-05-13` | codex (gpt-5.5) | high | 195s | done; clean exit, PR #1961 opened directly |

## Predecessor brief

`docs/session-state/2026-05-13-rule-correction-m20-build-firing-brief.md` — handed off after build #1 halt with primary evidence at `.worktrees/builds/a1-my-morning-20260513-122043/` (PR #1955 carries this brief).

## Next session opening action

1. Read this brief.
2. `curl -s 'http://localhost:8765/api/orient'` — confirm main at `64007d9cb5` (or newer if more PRs landed overnight).
3. Inspect `.worktrees/builds/a1-my-morning-20260513-164953/curriculum/l2-uk-en/a1/my-morning/python_qg.json` for gate observations.
4. Decide approach for #1962:
   - Path A: open multi-agent discussion `a1-m15-24-shape-contract` joint design first.
   - Path B: ship vesum-distractor-blindness fix independently (gate 1, mechanical), defer joint-thinking.
   - Path C: write decision card for the contract, signoff with user, then dispatch.

## Open queue summary (P0 → Pn)

- **P0:** #1962 — 4 content-class gate gaps blocking m20 publication.
- **P1:** #1958 — 2 stale-assertion red tests on main.
- **P1:** #1960 — wiki ingestion gap (deeper systemic fix; out of m20 critical path).
- **P2 background:** #1942 (forbid pytest -x in dispatch briefs), #1941 (A1-checkpoint word_target inconsistency), #1940 (pedagogical_deviations plan field), #1933 (/goal v2 wishlist).
- **Phase 2b queued:** `docs/dispatch-briefs/2026-05-13-phase-2b-m1-m7-warmup-batch.md` — fires after m20 GREEN.

---

*Format spec: `claude_extensions/rules/workflow.md` § "Two-tier handoffs". HTML companion deferred (MD-only per #M-2 ai→ai for orchestrator-loadable content).*
