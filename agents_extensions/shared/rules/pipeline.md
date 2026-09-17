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

- **Module writer in V7: Claude / claude-tools, Codex / codex-tools, or Cursor / cursor-tools — route by fit, not by a date-gate.** claude-tools is the current default on word-count and immersion adherence; the orchestrator-dispatched Claude lane (`delegate.py --agent claude` / `claude -p`) stays fully available. Decision card, fair-retest evidence and rollback triggers (invented `-ся` forms, wiki-path miscites, immersion >35%): [`docs/decisions/2026-05-06-writer-selection-codex-gpt55.md`](../../docs/decisions/2026-05-06-writer-selection-codex-gpt55.md). VESUM gate non-negotiable.
- **Wiki writer: Gemini, always.** [`docs/decisions/2026-04-26-reboot-agent-responsibilities.md`](../../docs/decisions/2026-04-26-reboot-agent-responsibilities.md) §1. `scripts/wiki/compile.py` defaults to `--writer gemini`; never pass `--writer=claude` for wiki rebuilds.
- **Pipeline reviewer: Codex** (`codex-tools`) for the per-dim LLM QG; cross-agent, no self-review (`SELF_REVIEW_DETECTED` audit gate enforces). Claude reserved for cultural/creative nuance dimensions when those reviewers need a different voice. See [`docs/decisions/2026-04-26-reboot-agent-responsibilities.md`](../../docs/decisions/2026-04-26-reboot-agent-responsibilities.md) §2.
- **Reviewer-as-fixer policy: NO LLM regeneration during review.** Reviewer outputs `<fixes>` find/replace pairs, pipeline applies deterministically. Enforced by ADR-007 (`docs/decisions/2026-04-23-rewrite-strategies-kill-or-revert.md`) and the structural invariant test `tests/test_no_rewrite_contract.py`. V7's REVISE/REJECT path is fail-fast, no scoped regen — see [Phase 4 brief](../../.worktree-briefs/codex-phase-4-a1-20-exemplar.md).
- **Plans**: DRAFT → REVIEWED → LOCKED lifecycle. Review plan before content build.
- **CF before build (all curriculum content — CORE, seminar, upgrade, repair):**
  Independent cross-family exact-head CF must be **clear** (APPROVE, or
  COMMENT-bound `VERDICT: APPROVE` when GitHub rejects own-PR reviews) on the
  prep that the build depends on — plan, machinery, prompts, or prior fix —
  **before** starting a paid content build (`v7_build` / `--upgrade` / writer
  run). CF feedback → fix that surface → re-CF; do **not** rebuild while CF is
  still REQUEST_CHANGES / open. After a clear CF, build; built artifacts get
  their own CF before merge. Gemini self-adjust is not this gate.
  **Enforced:** `scripts/build/cf_preflight.py` via `v7_build` (clearance file
  `cf_clearance.json` / `--cf-clearance`, or GitHub exact-head APPROVE). Escape
  only with `--allow-no-cf-preflight` (logs a NOTE).

**An LLM must NEVER review its own work.** V7 writer-of-the-moment builds → non-writer reviews (usually Codex), enforced by `SELF_REVIEW_DETECTED` audit gate.

</critical>
