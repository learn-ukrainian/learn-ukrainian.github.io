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

- **Module writer in V7: Claude / claude-tools (current default, REVISED 2026-05-12 night).** Decision card: [`docs/decisions/2026-05-06-writer-selection-codex-gpt55.md`](../../docs/decisions/2026-05-06-writer-selection-codex-gpt55.md). The 2026-05-12 reversal from codex-tools was triggered by a `tool_calls_total=0` observation that **has since been retracted as a measurement artifact** (`docs/decisions/2026-05-06-writer-selection-codex-gpt55.md:120-141`): the zero-call verdict came from a rollout-matcher bug in `scripts/agent_runtime/adapters/codex.py::_rollout_matches_plan`, fixed in PR #1907 on 2026-05-13. The fair-env retest captured **11 successful MCP tool calls** by codex-tools in retry 1. Real codex friction at A1 is **content register adherence** (per fair retest: 996/1200 words, 51.77% immersion vs 24% A1 cap, truncation artifacts) — NOT tool wiring. Claude-tools remains current default by margin on word-count + immersion adherence, not by codex's tool capability. Default V7 writer "until next bakeoff signal indicates otherwise" — repeatable per ADR §3. **Forward-looking constraint:** after 2026-06-15 the orchestrator-dispatched Claude lane is sunset (MEMORY #M0); codex-tools, gemini-tools, deepseek-tools (when wired) become the practical default set. Hard guardrails unchanged: VESUM gate non-negotiable; rollback triggers (invented `-ся` forms / wiki-path miscites / immersion >35%) documented in the decision card.
- **Wiki writer: Gemini, always.** [`docs/decisions/2026-04-26-reboot-agent-responsibilities.md`](../../docs/decisions/2026-04-26-reboot-agent-responsibilities.md) §1. `scripts/wiki/compile.py` defaults to `--writer gemini`; never pass `--writer=claude` for wiki rebuilds.
- **Pipeline reviewer: Codex** (`codex-tools`) for the per-dim LLM QG; cross-agent, no self-review (`SELF_REVIEW_DETECTED` audit gate enforces). Claude reserved for cultural/creative nuance dimensions when those reviewers need a different voice. See [`docs/decisions/2026-04-26-reboot-agent-responsibilities.md`](../../docs/decisions/2026-04-26-reboot-agent-responsibilities.md) §2.
- **Reviewer-as-fixer policy: NO LLM regeneration during review.** Reviewer outputs `<fixes>` find/replace pairs, pipeline applies deterministically. Enforced by ADR-007 (`docs/decisions/2026-04-23-rewrite-strategies-kill-or-revert.md`) and the structural invariant test `tests/test_no_rewrite_contract.py`. V7's REVISE/REJECT path is fail-fast, no scoped regen — see [Phase 4 brief](../../.worktree-briefs/codex-phase-4-a1-20-exemplar.md).
- **Plans**: DRAFT → REVIEWED → LOCKED lifecycle. Review plan before content build.

**An LLM must NEVER review its own work.** V7 writer-of-the-moment builds → non-writer reviews (usually Codex), enforced by `SELF_REVIEW_DETECTED` audit gate.

</critical>
