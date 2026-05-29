# Decolonization Terminal Gate Scope

**Status:** ACCEPTED 2026-05-29 by project-owner direction.
**Expiry:** 2026-08-29, after enough core and seminar V7 builds exist to compare LLM-QG decolonization judgments against deterministic gates and human review.
**Scope:** V7 LLM-QG aggregation and build gating. Does not change deterministic gates, per-dimension floor values, or the full human-review verdict.
**Amends:** `docs/decisions/2026-04-26-llm-qg-per-dim-thresholds.md` and `docs/session-state/2026-05-23-architectural-reset-strip-v7-llm-demote.md`.

## Decision

On CORE levels, LLM-QG `decolonization` is warning-only for build gating. A low decolonization score still appears in the full aggregate `verdict`, `failing_dims`, and `rejected_dims`, but it does not make `terminal_verdict` fail.

On SEMINAR tracks, LLM-QG `decolonization` remains terminal exactly as before. Seminar tracks include history, biography, literature, OES, Ruthenian, and related decolonization-focused tracks.

The implementation keys off the curriculum profile from `curriculum/l2-uk-en/curriculum.yaml`, not off CEFR-looking level codes. The current manifest spells seminar tracks as `type: track`; pipeline code normalizes that to the seminar profile. Unknown or missing profiles fail closed to the seminar terminal set.

## Rationale

Core A1-C2 lessons teach clean literary Ukrainian. Clean-Ukrainian correctness is enforced by deterministic gates such as VESUM, russianisms, wiki coverage, Python QG, scaffolding, and L2 exposure, plus pedagogy review.

The LLM-QG `decolonization` score is a subjective reviewer judgment. On core grammar and vocabulary modules it must not hard-block a build when deterministic language-safety gates pass. It remains visible for human review as a warning.

Seminar tracks are different: decolonization is often the subject matter. There the subjective decolonization reviewer remains a terminal guardrail because imperial framing, source treatment, and historical stance are core learning outcomes.

## Required Semantics

- `profile="core"`: terminal LLM-QG dimensions are empty. Any failing LLM-QG dimension, including `decolonization`, is warning-only for build gating.
- `profile="seminar"` or `profile=None`: terminal dimensions are `{"decolonization"}`. This preserves the stricter default for callers that have not threaded a profile.
- Full `verdict` is unchanged for all profiles. Only `terminal_verdict` and terminal-vs-warning classification vary by profile.

## Review Trigger

Revisit this decision before 2026-08-29 or sooner if deterministic gates allow a core module with authentic-language regressions that only the LLM-QG decolonization score caught.
