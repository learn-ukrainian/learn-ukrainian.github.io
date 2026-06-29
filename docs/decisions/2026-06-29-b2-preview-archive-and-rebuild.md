# ACCEPTED — B2 preview archive and rebuild

**Status:** ACCEPTED
**Decided on:** 2026-06-29
**Scope:** B2 production, B2 learner-facing modules, B2 score interpretation, future B2 rebuild orchestration.

## Decision

Current B2 M01-M68 is archived as a superseded preview generation. The existing module files remain in the repository for provenance, source mining, route stability, and comparison, but they are no longer treated as release-candidate lesson quality.

New B2 production is frozen until the rebuild program completes the following stages:

1. B2 rebuild decision record and current-status archival.
2. Prompt and deterministic gate hardening.
3. Source, plan, wiki, and research readiness audit for the rebuild.
4. One golden pilot rebuild reviewed against B1 teaching quality.
5. Wave rebuilds only after the pilot proves the new contract.

Current B2 LLM scores are retained as content-validity provenance only. They must not be cited as evidence that the learner-facing B2 lessons are ready for release or human review as lessons. Rebuilt modules require fresh teaching-quality scoring.

## Rationale

The failure is architectural, not a small copy-editing backlog. B1 and B2 differ sharply in lesson practice structure:

- B1: 94/94 modules have inline activity YAML; 92/94 have `INJECT_ACTIVITY` markers.
- B2: 7/68 modules have inline activity YAML; 8/68 have `INJECT_ACTIVITY` markers; 60/68 have no lesson activity injection markers.
- M64 and M65 contain lesson injection markers while their activity YAML has `inline: []`, proving at least one prompt/pipeline contract mismatch.
- Recent B2 vocabulary and grammar modules often read as correct reference articles rather than taught lessons.

Continuing M69+ production under the old prompt would multiply the same failure. Hand-patching the existing modules would also be expensive and likely misleading because the original artifact type is wrong.

## Archive Meaning

Archive does not mean delete. Archive means:

- Preserve current files and score reports for provenance.
- Stop using current B2 as the release candidate.
- Stop using current B2 scores as teaching-quality approval.
- Reuse useful vocabulary, examples, grammar facts, source references, and review findings only after the rebuild pipeline is fixed.
- Rebuild learner-facing lesson structure from source under the new teaching contract.

## Required Next Work

PR 2 must harden prompts and gates before any new B2 module build. At minimum it must fail or block B2 builds with:

- `inline: []` unless an explicit rebuild contract exemption exists.
- `INJECT_ACTIVITY` markers that reference activities outside `inline`.
- No in-lesson activity markers in normal B2 modules.
- Long exposition before practice.
- Grammar or lexical contrast taught only through prose when a table, contrast grid, or decision rule is required.
- Malformed callouts such as raw `[!note]` outside the accepted syntax.

PR 3 must audit B2 source readiness before rebuild. It should focus on B2 plans, source/wiki/research sufficiency, sequence coherence, and whether plan scaffolding encourages reference-style writing. It should not become a whole-repository curriculum audit unless evidence requires expanding scope.

PR 4 must rebuild one golden pilot module and compare it with B1 teaching rhythm before approving wave rebuilds.

## Supersedes

- B2 production-build prompt version 0.5 as an active production prompt.
- Current B2 M01-M68 score interpretation as release-candidate teaching quality.
