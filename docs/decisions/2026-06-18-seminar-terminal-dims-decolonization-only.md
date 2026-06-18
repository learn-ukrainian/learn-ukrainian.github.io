# ADR: Seminar LLM-QG terminal dims stay decolonization-only until empirics justify re-promotion

- **Date:** 2026-06-18
- **Status:** Accepted
- **Tracks:** folk + all seminars (hist, bio, istorio, lit, oes, ruth)
- **Supersedes (in part):** the PR #3495 "seminar quality gate" promotion of
  pedagogical/engagement/beauty to terminal dims.
- **Expiry / revisit:** when ~20+ seminar modules have shipped with captured
  human/LLM agreement data per dimension (the project's own re-promotion bar).

## Context

The 2026-05-23 architectural reset (decision #2) demoted the subjective LLM-QG
dims (pedagogical, engagement, beauty, naturalness, tone) to **warning-only**
because they were stochastic and produced **zero shipped modules across 6 builds**
(2026-05-22→23). It set an explicit re-promotion bar: "~20+ shipped modules with
captured human decisions."

PR #3495 (the "seminar quality gate") re-promoted pedagogical/engagement/beauty to
**terminal** for seminar profiles — with **zero** shipped seminar modules, i.e.
ahead of that bar. Across ten sessions this produced zero converging folk modules.

The #3079 investigation (folk Sessions 49–52) found the root cause **deterministically**:
the per-dim reviewer (`invoke_reviewer_dim`) is non-deterministic. The SAME pristine
curated module (`folk/kalendarna-obriadovist-zvychai`) scored, across repeated runs of
identical content:

| dim | observed single-sample scores | spread |
|---|---|---|
| decolonization | 9.0, 8.4, 7.8, **9.2/9.2/8.3 (one ensemble run)** | ~1.4 |
| tone | 5.8, 8.2, 5.5 | 2.7 |
| pedagogical | 5.8, 7.1, 6.8 | 1.3 |
| engagement | 8.1, 7.0, 7.2 | 1.1 (pass↔fail flip) |

A terminal gate at floor 8.0 cannot reliably pass good content against a judge with
±2.4 variance. Even decolonization — the one hard-rule dim — dipped to 7.8 on a single
sample.

## Decision

1. **`SEMINAR_TERMINAL_DIMS = {decolonization}`** (revert to the validated
   2026-05-23 policy). Decolonization stays terminal because Russian-colonial
   framing leaking in is a hard rule, not a subjective judgment. The other dims
   are **warning-only** (`llm_qg_warning` telemetry, tracked per module).
2. **Floors are unchanged at 8.0.** This is a change to *which dims gate*
   (a structural scope decision), NOT a floor reduction. Every deterministic gate
   (python_qg, VESUM, wiki coverage, mdx render) still hard-blocks.
3. **De-noise the judge before any subjective dim can gate.** The median-of-N
   reviewer ensemble (#3079 / PR #3517, seminar N=3, core N=1) is merged to main.
   With median-of-3, decolonization on kalendarna stabilized to 9.2 (samples
   [9.2, 9.2, 8.3]).
4. **Re-promotion is earned, not assumed.** Subjective dims return to terminal only
   with the ~20+ shipped-module agreement empirics the reset already required —
   logged with the agreement-rate justification. This is the guard against a
   slippery slope in either direction.

## Consequences

- **First shipped folk module:** `folk/kalendarna-obriadovist-zvychai` now passes
  end-to-end — all deterministic gates green, MDX renders (17 island props),
  decolonization terminal 9.2 ≥ 8.0, and a corpus-hammer (#M-11) confirmed the
  embedded cosmogonic koliadka is the genuine Hrushevsky/Vahylevych variant
  (literary-corpus verbatim match), not fabricated.
- Subjective scores (pedagogical 6.8, engagement 7.2, beauty 7.6, …) are recorded
  as warnings and become the improvement backlog — quality is raised from a shipped
  baseline, not chased before anything ships.
- **PR #3495 disposition:** its terminal-dim promotion is withdrawn by this ADR.
  Its still-valuable parts (the `--enhance` curated-content entry point and the two
  `--enhance` python_qg telemetry-substitution fixes, #3079) should be extracted to
  main on their own; the beauty/pedagogical/engagement terminal promotion is dropped.
