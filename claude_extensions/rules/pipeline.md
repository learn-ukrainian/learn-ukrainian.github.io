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

**Two pipelines coexist during the reboot transition:**

- **Reboot pipeline** (`scripts/build/linear_pipeline.py`, EPIC #1577) — fail-fast linear runner. Phase 4 exemplar in flight (PR #1594 draft). Will become the only pipeline once A1+A2+B1 ship through it.
- **Pipeline V6** (`scripts/build/v6_build.py`) — LEGACY. The reboot replaces it. Don't add features; don't extend. Only relevant when re-running historical builds.
- **v5, v4, v3 are RETIRED.** Do not use `build_module_v5.py` or `build_module.py`.

## Reboot policy authority

- **Module writer in the reboot: NOT YET DECIDED.** See [`docs/decisions/2026-04-26-reboot-agent-responsibilities.md`](../../docs/decisions/2026-04-26-reboot-agent-responsibilities.md) §3. Phase 0 (North Star + Lesson Contract) is silent on writer agent by design — it specifies what the writer must do, not who it is. The choice will be made at Phase 5+ approach via a strict bakeoff.
- **Wiki writer: Gemini, always.** [`docs/decisions/2026-04-26-reboot-agent-responsibilities.md`](../../docs/decisions/2026-04-26-reboot-agent-responsibilities.md) §1. `scripts/wiki/compile.py` defaults to `--writer gemini`; never pass `--writer=claude` for wiki rebuilds.
- **Pipeline reviewer: Codex** (`codex-tools`) for the per-dim LLM QG; cross-agent, no self-review (`SELF_REVIEW_DETECTED` audit gate enforces). Claude reserved for cultural/creative nuance dimensions when those reviewers need a different voice. See [`docs/decisions/2026-04-26-reboot-agent-responsibilities.md`](../../docs/decisions/2026-04-26-reboot-agent-responsibilities.md) §2.
- **Reviewer-as-fixer policy: NO LLM regeneration during review.** Reviewer outputs `<fixes>` find/replace pairs, pipeline applies deterministically. Enforced by ADR-007 (`docs/decisions/2026-04-23-rewrite-strategies-kill-or-revert.md`) and the structural invariant test `tests/test_no_rewrite_contract.py`. The reboot's REVISE/REJECT path is fail-fast, no scoped regen — see [Phase 4 brief](../../.worktree-briefs/codex-phase-4-a1-20-exemplar.md).
- **Plans**: DRAFT → REVIEWED → LOCKED lifecycle. Review plan before content build.

## V6 (legacy) reference

V6 still ships in tree for historical re-runs:
- Build: `.venv/bin/python scripts/build/v6_build.py {level} {num} [--step {step}] [--writer {gemini|claude|gemini-tools|claude-tools}]`
- V6's hardcoded `claude-tools` writer default (`scripts/build/v6_build.py:29` + `:10706-10707`) is **legacy V6 behavior**, not reboot policy. Do not propagate it to reboot code paths.

**An LLM must NEVER review its own work.** Reboot: writer-of-the-moment builds → non-writer reviews (usually Codex). V6 legacy: same constraint, enforced by `SELF_REVIEW_DETECTED` audit gate.

</critical>
