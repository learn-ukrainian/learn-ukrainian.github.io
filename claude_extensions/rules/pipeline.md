---
paths:
  - "scripts/build/**"
  - "scripts/pipeline/**"
  - "scripts/audit/**"
  - "scripts/validate/**"
  - "curriculum/**/orchestration/**"
---

# Pipeline Architecture

<critical>

**V7 is the only live build pipeline** (`scripts/build/v7_build.py` driving `scripts/build/linear_pipeline.py`). v5/v6/v4/v3 files may remain on disk for forensic reference, but they must not be invoked, extended, or referenced as live policy.

## Pipeline policy authority

- **Module writer in V7: Codex / GPT-5.5 / codex-tools (ACCEPTED 2026-05-06).** Decision card: [`docs/decisions/2026-05-06-writer-selection-codex-gpt55.md`](../../docs/decisions/2026-05-06-writer-selection-codex-gpt55.md). Default V7 writer "until next bakeoff signal indicates otherwise" — repeatable per ADR §3. **Acceptance is conditional on #1731 Part B**: (1) agents can communicate (✅ met as of PR #1732/#1733) AND (2) Codex Desktop can join in as visual-aid preproduction layer (❌ pending PR #1735 round-3 + Strand 0 bakeoff). A1/A2/B1 batch build does NOT start until both conditions hold. Hard guardrails: VESUM gate non-negotiable; rollback triggers (invented `-ся` forms / wiki-path miscites / immersion >35%) documented in the decision card.
- **Wiki writer: Gemini, always.** [`docs/decisions/2026-04-26-reboot-agent-responsibilities.md`](../../docs/decisions/2026-04-26-reboot-agent-responsibilities.md) §1. `scripts/wiki/compile.py` defaults to `--writer gemini`; never pass `--writer=claude` for wiki rebuilds.
- **Pipeline reviewer: Codex** (`codex-tools`) for the per-dim LLM QG; cross-agent, no self-review (`SELF_REVIEW_DETECTED` audit gate enforces). Claude reserved for cultural/creative nuance dimensions when those reviewers need a different voice. See [`docs/decisions/2026-04-26-reboot-agent-responsibilities.md`](../../docs/decisions/2026-04-26-reboot-agent-responsibilities.md) §2.
- **Reviewer-as-fixer policy: NO LLM regeneration during review.** Reviewer outputs `<fixes>` find/replace pairs, pipeline applies deterministically. Enforced by ADR-007 (`docs/decisions/2026-04-23-rewrite-strategies-kill-or-revert.md`) and the structural invariant test `tests/test_no_rewrite_contract.py`. V7's REVISE/REJECT path is fail-fast, no scoped regen — see [Phase 4 brief](../../.worktree-briefs/codex-phase-4-a1-20-exemplar.md).
- **Plans**: DRAFT → REVIEWED → LOCKED lifecycle. Review plan before content build.

**An LLM must NEVER review its own work.** V7 writer-of-the-moment builds → non-writer reviews (usually Codex), enforced by `SELF_REVIEW_DETECTED` audit gate.

</critical>
