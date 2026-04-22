# Hardened retest — results summary

**Date:** 2026-04-22
**Fixture:** A1 M03 `special-signs` (l1-uk track)
**Writer:** Claude Opus 4.7 (`claude-opus-4-7`), effort=high
**Reviewers:** 2× Codex (GPT-5.x), effort=high
**Prompt under test:** v1 hardening (commit `97f2d488b`) — AC-A markers-only + AC-B metalanguage + AC-C honesty

## Writer output

- **File:** `experiments/writer-bakeoff-2026-04-22/hardened-retest/opus/special-signs.md` (committed on `claude/hardened-retest-opus-writer`, merged into `claude/claude-1370-writer-harden`)
- **Duration:** 230s (3m50s) vs bakeoff Opus ~30-60 min
- **Word count:** 1543 (target ≥1200)
- **Marker coverage:** 7/7 `<!-- INJECT_ACTIVITY -->` markers placed inline after their teaching sections
- **Structural failures from the bakeoff (ELIMINATED):**
  - Zero «Вправа N.» headers (baseline Opus had «Вправа 1» through «Вправа 7»)
  - Zero fill-in slot tokens in prose (baseline had `сім_я → сім'я`, `ден_ → день`, `п_ять → п'ять`)
  - Zero item-with-answer arrows (baseline had `«сіль» → Ь`, `«м'яч» → апостроф`)
  - Zero numbered exercise lists (baseline had «Вправа 4. Розподіл слів на три колонки. Вісімнадцять слів...»)

## Reviewer scores

### Codex-1 (hardened retest)

| Axis | Score | Baseline Opus (bakeoff mean) | Δ |
|---|---|---|---|
| linguistic_correctness | 8 | 8.0 | ±0 |
| pedagogical_accuracy | 7 | 7.75 | −0.75 |
| decodability_a1 | 4 | 7.75 | **−3.75** |
| plan_adherence | 4 | 8.0 | **−4.0** |
| register_naturalness | 6 | 8.5 | −2.5 |
| honesty | 2 | 6.75 | **−4.75** |
| **overall** | **5.2 FAIL** | **7.80 REVISE** | −2.60 |

### Codex-2 (hardened retest)

| Axis | Score | Baseline Opus (bakeoff mean) | Δ |
|---|---|---|---|
| linguistic_correctness | 6 | 8.0 | −2.0 |
| pedagogical_accuracy | 5 | 7.75 | −2.75 |
| decodability_a1 | 4 | 7.75 | **−3.75** |
| plan_adherence | 5 | 8.0 | **−3.0** |
| register_naturalness | 6 | 8.5 | −2.5 |
| honesty | 3 | 6.75 | **−3.75** |
| **overall** | **4.8 FAIL** | **7.80 REVISE** | −3.00 |

### Mean of the 2 hardened-retest reviews

| Axis | Hardened mean | Baseline Opus mean | Δ |
|---|---|---|---|
| linguistic_correctness | 7.0 | 8.0 | −1.0 |
| pedagogical_accuracy | 6.0 | 7.75 | −1.75 |
| decodability_a1 | 4.0 | 7.75 | **−3.75** |
| plan_adherence | 4.5 | 8.0 | **−3.5** |
| register_naturalness | 6.0 | 8.5 | −2.5 |
| honesty | 2.5 | 6.75 | **−4.25** |
| **overall** | **5.0 FAIL** | **7.80 REVISE** | **−2.80** |

## Interpretation

The retest did **NOT** improve the headline score — overall mean dropped from 7.80 to 5.0 (2× FAIL verdicts). Two things to disentangle:

### The hardening HIT its primary target

The bakeoff's dominant failure mode — inline exercise authoring with under-spec item counts (plan says 18, writer shows 3) — was **eliminated**:
- Zero «Вправа N.» headers in the hardened output
- Zero fill-in slot tokens
- Zero item-with-answer arrows
- All 7 `<!-- INJECT_ACTIVITY -->` markers placed correctly

Both Codex reviewers confirmed marker coverage: `present_count: 7`, `missing_hints: []`.

### The hardening OVER-TRIGGERED on teaching examples

Both reviewers flagged the same 3-4 "inline exercise authoring" violations — but all of them are **teaching-example patterns drawn verbatim from the plan's `content_outline` points**:

| Violation flagged by Codex | Source in plan YAML |
|---|---|
| "Практика читання: **п'ять**, **дев'ять**, **м'який**, **м'яч**, **об'єкт**." | `content_outline[1].points[1]` verbatim |
| "Потренуйте слух на мінімальних парах — **балка** / **палка**, **коза** / **коса**." | `content_outline[2].points[2]` paraphrased |
| "Мінімальні пари для тренування слуху: бик/бік, дим/дім, лист/ліс, кит/кіт." | `content_outline[3].points[0]` verbatim |
| "Потренуйтеся зі словами: **рука**, **робота**, **ранок**, **риба**." | `content_outline[3].points[2]` verbatim |

These are **teaching demonstrations** (minimal pairs, pronunciation anchors), not exercise authoring. The writer followed the plan's teaching content. The reviewer applied the STOP test literally.

**Root cause:** v1 STOP test rule 2 banned "any task-instruction verb («...прочитай уголос...») followed by task description + items." The plan's teaching content uses exactly this pattern — it is standard Ukrainian textbook pedagogy.

### Collateral score drops

- **`decodability_a1` dropped −3.75** — this is NOT a hardening effect. Both reviewers flagged specific A1-inappropriate abstractions («подвійну природу йотованих голосних», «палаталізований», «фонетична ідентичність мови»). This is a register/calibration issue in the writer output, not in the hardening. L1-UK A1 target audience is a Ukrainian first-grader; the writer wrote at adult-textbook register.

- **`honesty` dropped −4.25** — zero `<!-- VERIFY -->` markers in the hardened output, despite the prompt rule #11 calling them out as positive signal. The writer treated the plan as authoritative and did not flag two real ambiguities: the plan's simplified apostrophe rule (ignoring «свято»/«морквяний» exceptions per Правопис 2019) and the internal contradiction in `grammar[3]` about sonorants. Both reviewers flagged these as `plan_issues` but the writer did not. This is a partial signal — rule #11 is there but not sticky enough.

## Decision

The v1 hardening has a measurable primary-target hit (markers placed, no «Вправа N.»), but two gaps need addressing before Phase 3:

1. **v2 refinement applied in commit `<next>`:** the STOP test now distinguishes teaching examples from exercise authoring. v1 banned "any task-instruction verb" verbs; v2 bans only answer-demanding verbs + items-that-demand-answers + fill-in tokens + word banks ≥6 items. Teaching examples (minimal pairs, pronunciation anchor lists, plan-mandated practice words) are explicitly carved out as ALLOWED with 4 concrete RIGHT examples.

2. **Rule #11 honesty framing is in the prompt but needs a second retest** after the v2 STOP refinement, to see if the over-trigger removal frees the writer to also apply rule #11. A writer under constraint-pressure may drop `<!-- VERIFY -->` because it's still resolving the STOP test.

## Gemini adversarial review (AC-F)

**Status:** DEFERRED. Gemini API hit a 429 rate-limit; cooldown expires at ~2026-04-22 14:52 CET (1776863563 unix). The dispatched task ran 18m with empty logs before SIGTERM. Codex-as-adversarial-reviewer dispatched as fallback on the refined v6-write.md hardening (see next commit).

## Artifacts

- `opus/special-signs.md` — writer output
- `reviews/codex-1.yaml` — reviewer 1 YAML
- `reviews/codex-2.yaml` — reviewer 2 YAML
- `reviews/reviewer-codex-{1,2}-prompt.md` — substituted reviewer prompts (for reproducibility)
- `writer-prompt.md` — hardened retest writer prompt (v1)
- `reviewer-prompt.md` — hardened retest reviewer prompt (grades marker coverage, not item count)
- `gemini-adversarial-review-prompt.md` — Gemini adversarial review prompt (dispatched but blocked by API rate limit)
