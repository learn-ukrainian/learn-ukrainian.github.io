# Smoke build — a1/colors — post convergence-budget fix — 2026-04-23

> Re-run of the a1/colors smoke build after landing the
> convergence-budget-collapse fix
> ([commit f82c7fa5ec](https://github.com/learn-ukrainian/learn-ukrainian.github.io/commit/f82c7fa5ec)).

## Headline

- **Pipeline fix validated.** Convergence loop ran **three** escalations
  (tier 3 full_rewrite → tier 4 writer_swap → tier 5 plan_revision_request)
  instead of collapsing at attempt 2 as it did on the prior smoke
  (PR #1429).
- **Terminal: `plan_revision_request`.** Not `budget_exhausted`. The
  escalation chain reached an honest plan-level decision rather than
  short-circuiting on an exception.
- **Content not published.** Genuine writer/plan-quality issue —
  described below. `colors.mdx` restored from HEAD defensively.

## Escalation trace

Source: `curriculum/l2-uk-en/a1/orchestration/colors/plan_revision_request.yaml`

| Attempt | Tier | Strategy | Reason | Stall signals | Writer |
|---:|---:|---|---|---|---|
| 1 | 3 | full_rewrite | cross-section findings require full module regeneration | — | gemini-tools |
| 2 | 4 | writer_swap | stall detected (content_hash_repeat) | content_hash_repeat | claude-tools |
| 3 | 5 | plan_revision_request | stall detected (top3_overlap, content_hash_repeat) | top3_overlap, content_hash_repeat | — |

Total wall clock: ~31 min for the convergence loop on top of the ~15 min initial write.

## Round 1 review scores (codex-tools)

Source: `curriculum/l2-uk-en/a1/orchestration/colors/review-structured-r1.yaml`

| Dim | Score | Short evidence |
|---|---:|---|
| Plan adherence | 5 | Section promises twelve colors, explicitly teaches six + блакитний |
| Linguistic accuracy | 8 | First sentence capitalises `Діалог` as proper noun |
| Pedagogical quality | 4 | English meta-exposition dominates Ukrainian-first flow |
| Vocabulary coverage | 7 | Core targets land in prose; two contract targets miss |
| Exercise quality | 8 | Activity order mismatches `activity_obligations` |
| Engagement & tone | 3 | Formulaic meta openers recur across sections |
| Structural integrity | 8 | Sections present and ordered; section-level bloat |
| Cultural accuracy | 9 | `синій` / `блакитний` contrast on Ukrainian terms |
| Dialogue & conversation quality | 5 | Second scene narrated in English; stilted reply |

Overall: 6.1. MIN: 3 (Engagement & tone). Verdict: REVISE (below 8.0 threshold).

## Why escalation terminated at plan_revision_request

The persistent finding across attempts 2 and 3 is `activity_order`:

> Activity order mismatch at position 1 (expected type `quiz`, found
> `group-sort-hard-soft`) and position 2 (expected type `fill-in`, found
> `quiz-what-color`) and position 3 (expected type `quiz`, found
> `fill-in-agreement`) and position 4 (expected type `match-up`, found
> `quiz-blue-shades`) and position 5 (expected type `group-sort`, found
> `match-up-appearance`)

Neither `gemini-tools` (attempt 1) nor `claude-tools` (attempt 2) produced
activities in the order `activity_obligations` requires (quiz, fill-in,
quiz, match-up, group-sort). Both writers substituted semantically
qualified names (`group-sort-hard-soft`, `quiz-what-color`, …) and/or
permuted the ordering.

Attempt 2 (writer_swap) added a **new** persistent finding: missing
contract vocabulary `чорний (black)` and `колір (color, m)`. Both
writers dropped those two items from the vocabulary sidecar.

## Root-cause classification — plan-quality and writer-prompt-quality mix

This is not a single-axis failure. Evidence:

- **Writer-prompt adherence (both gemini-tools and claude-tools miss it):**
  the writer produces activity stubs with qualified names that the
  validator, checking `type` exact-equality, rejects. Either the prompt
  isn't surfacing `activity_obligations` as a strict ordered contract, or
  the writer's skeleton-to-flesh step drops the contract.
- **Vocabulary dropout (same direction):** `чорний` (one of the eleven
  basic Ukrainian colors) and `колір` (the word "colour" itself) both
  got dropped by both writers. For a colors module this is structurally
  wrong. Either the writer prompt isn't gating on required vocabulary,
  or the vocabulary_hints structure is being ignored.
- **Plan specificity (possible contributor):** if `activity_obligations`
  in the plan lists bare type names without a short description of the
  intended exercise purpose per slot, writers may be improvising
  semantic names instead of reading the contract as an ordered
  type-template. This is a plan-authoring convention question.

## Fix handoff

The right next step is **not** another smoke of colors. The same two
writers failing on the same two axes indicates a systemic prompt or
plan-convention issue. Options, in order of cheapness:

1. **Investigate writer prompt output** (`orchestration/colors/v6-chunk-XX-prompt.md`)
   — is `activity_obligations` rendered verbatim with positional labels?
   Is required vocabulary rendered as a hard gate?
2. **Review the plan** (`curriculum/l2-uk-en/plans/a1/colors.yaml`) for
   clarity of `activity_obligations` + `vocabulary_hints.required`.
3. **Only after those two:** consider a plan revision pass or a
   writer-prompt hardening (workstream #1370 is in flight and targets
   exactly this class of drift).

## Build artifacts committed on this branch

All under `curriculum/l2-uk-en/a1/`:

- `orchestration/colors/` — full convergence trail including
  `plan_revision_request.yaml`, three correction attempts, prompts,
  review-structured YAML, module-memory with per-attempt history
- `colors.md` — round-3 prose (unpublished; starlight mdx restored from HEAD)
- `activities/colors.yaml`, `vocabulary/colors.yaml` — sidecars from
  round 3 (do not merge as-is)
- `research/colors-knowledge-packet.md` — updated packet
- `review/colors-review-r1.md`, `review/colors-review.md` — reviewer outputs
- `build-stats.jsonl`, `stuck-modules.yaml`,
  `scripts/build/finding-normalizer-growth.yaml` — pipeline metadata

## Status vs acceptance criteria (from the dispatch brief)

- [x] Convergence loop pytest additions pass locally (16 pass)
- [x] Full `test_convergence_*` + `test_v6_*` green (180 pass)
- [x] Smoke build of a1/colors runs through the pipeline with all 5
      escalation rounds available — **3 of 5 were fired before the
      stall detector legitimately bumped to tier 5**
- [ ] Smoke PASS with min per-dim ≥ 8 — **did not pass**. Genuine
      plan/writer-prompt-quality terminal (see classification above).
      PR body has per-dim table + classification + next-step
      recommendation as required.
