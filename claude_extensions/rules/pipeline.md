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

- **Module writer in V7: Claude / claude-tools (REVISED 2026-05-12 night).** Decision card: [`docs/decisions/2026-05-06-writer-selection-codex-gpt55.md`](../../docs/decisions/2026-05-06-writer-selection-codex-gpt55.md). Reversal from codex-tools after 3rd bakeoff (`audit/bakeoff-2026-05-12-night/REPORT.md`) confirmed empirical pattern: codex-tools `tool_calls_total=0` (MCP tools not invoked despite prompt-rewrite at `28417cc3cb`); claude-tools produced a 1224-word module with 4 MCP tool calls + `vesum_verified` pass (159/159 forms, 0 invented `-ся`). Default V7 writer "until next bakeoff signal indicates otherwise" — repeatable per ADR §3. Hard guardrails unchanged: VESUM gate non-negotiable; rollback triggers (invented `-ся` forms / wiki-path miscites / immersion >35%) documented in the decision card. **A1/A2/B1 batch build is blocked on #1901** (textbook_grounding HARD gate root cause, currently in dispatch).
- **Wiki writer: Gemini, always.** [`docs/decisions/2026-04-26-reboot-agent-responsibilities.md`](../../docs/decisions/2026-04-26-reboot-agent-responsibilities.md) §1. `scripts/wiki/compile.py` defaults to `--writer gemini`; never pass `--writer=claude` for wiki rebuilds.
- **Pipeline reviewer: Codex** (`codex-tools`) for the per-dim LLM QG; cross-agent, no self-review (`SELF_REVIEW_DETECTED` audit gate enforces). Claude reserved for cultural/creative nuance dimensions when those reviewers need a different voice. See [`docs/decisions/2026-04-26-reboot-agent-responsibilities.md`](../../docs/decisions/2026-04-26-reboot-agent-responsibilities.md) §2.
- **Reviewer-as-fixer policy: NO LLM regeneration during review.** Reviewer outputs `<fixes>` find/replace pairs, pipeline applies deterministically. Enforced by ADR-007 (`docs/decisions/2026-04-23-rewrite-strategies-kill-or-revert.md`) and the structural invariant test `tests/test_no_rewrite_contract.py`. V7's REVISE/REJECT path is fail-fast, no scoped regen — see [Phase 4 brief](../../.worktree-briefs/codex-phase-4-a1-20-exemplar.md).
- **Plans**: DRAFT → REVIEWED → LOCKED lifecycle. Review plan before content build.

**An LLM must NEVER review its own work.** V7 writer-of-the-moment builds → non-writer reviews (usually Codex), enforced by `SELF_REVIEW_DETECTED` audit gate.

</critical>
