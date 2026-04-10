# ADR-001: V6 pipeline architecture — skeleton → write → review loop

**Status**: Accepted
**Date**: 2026-03-24 (first implemented) / 2026-04-11 (recorded)
**Related**: #1185 (self-healing repair), #1161 (compile prompts), `dec-001` (decision journal entry "V6 uses reviewer-as-fixer")

## Context

Pipelines v2 through v5 all tried to build module content in one pass: send a huge prompt to the writer, get content back, score it, regenerate from scratch if it failed. Three problems compounded:

1. **Single-pass writes on 2000+ word modules produced inconsistent quality.** The writer would start strong and degrade by the end of a module, or miss requirements buried mid-prompt.
2. **"Full rewrite on failure" destroyed good content.** Gemini's rewrite attempts consistently produced worse output than the original — observed as 9.6 → 9.2 → 8.4 score trajectories on retries.
3. **Writer feedback loops were ad-hoc.** When the writer produced an error we had no systematic way to tell it exactly what to fix; we just re-ran the whole prompt with a "try harder" appendix.

The v6 pipeline was designed to fix all three.

## Decision

V6 uses a **skeleton → chunked write → reviewer-as-fixer** loop with 17 ordered phases:

```
check → research → skeleton → pre-verify → write → exercises →
activities → repair → verify-exercises → annotate → vocab →
enrich → verify → review → stress → publish → audit
```

The canonical phase list lives at `scripts/build/v6_build.py::PHASES`.

Three architectural choices are the defining features:

1. **Skeleton first, then prose.** The `skeleton` phase produces the section structure + per-paragraph word budgets + injection markers for activities. The `write` phase then fills in each section one at a time with rolling context (previous sections summarized). This prevents the end-of-module degradation we saw in one-shot writes.

2. **Reviewer-as-fixer, NOT rewriter.** The `review` phase reads the prose and emits `<fixes>` blocks with exact find/replace pairs. The pipeline applies those fixes deterministically — no LLM regeneration. The reviewer's job is to find problems; fixing is mechanical substitution. Max 2 fix rounds, then publish or fail.

3. **Cross-agent review is mandatory.** An LLM never reviews its own work. Gemini writes → Claude reviews, or vice versa. Enforced by the `SELF_REVIEW_DETECTED` audit gate, which blocks publish when writer and reviewer are the same agent.

Chunked write is the mechanism that makes long-form immersion content (2000-5000 words) reliable. Each section is a separate LLM call with the skeleton, the plan, the knowledge packet, and a summary of previously written sections as context. See `step_write_chunked` in `v6_build.py`.

## Alternatives considered

- **Continue with v5 single-pass writes** → rejected: empirically produced degrading quality on long modules and destroyed content on retries (see context above).
- **LLM-driven section-by-section rewrites** instead of deterministic find/replace → rejected: Gemini's rewrites were monotonically worse in our data (0/5 rewrites improved scores in the #1169 incident). The hypothesis that "better prompting will fix it" was falsified over multiple attempts.
- **Same-agent review** (Gemini writes AND reviews) → rejected: self-review has a known confirmation bias and our tests confirmed it. Forcing cross-agent review adds one dispatch per module but catches issues an LLM misses in its own output.
- **Fewer phases, larger steps** → rejected: each phase here exists because it was added in response to a real failure mode we could test for. Collapsing phases would reintroduce those failure modes.

## Consequences

**Positive**:
- Long-form content quality is dramatically more reliable. A1 modules consistently hit 9+ review scores without manual intervention.
- The reviewer-as-fixer loop lets us cap iterations at 2 rounds and still ship quality content, because each round is a small deterministic patch instead of a full regeneration.
- Cross-agent review catches agent-specific blind spots (Gemini calques, Claude over-confidence) that same-agent review misses.

**Negative / risks**:
- Build is slower — 17 phases means 17 dispatch boundaries, and the full pipeline on a single module takes 5-15 minutes depending on wiki packet size.
- Chunked writes can produce section-boundary drift if the per-section skeleton is inaccurate. Mitigated by the `pre-verify` phase that checks skeleton quality before write.
- Cross-agent review doubles the dispatch cost per module vs. same-agent. Accepted trade-off for the quality delta.

**Neutral / follow-ups**:
- The `activities`, `repair`, and `verify-exercises` phases were added post-v6-MVP to close specific failure modes. The pipeline evolves phase-by-phase; any new persistent class of failure gets a new phase (with a tracking issue and this ADR being a pointer to the overall shape, not an exhaustive spec).

## Verification

- `tests/test_v6_build_events.py` — confirms pipeline emits expected event stream
- `scripts/build/v6_build.py --range` exit codes — green across A1 (#1122) after repair phase landed
- Cross-agent enforcement: `SELF_REVIEW_DETECTED` audit gate has a test in `tests/test_audit_module.py`
- `docs/archive/analysis/V5-VS-V6-ANALYSIS.md` documents the v5→v6 score delta on real modules
