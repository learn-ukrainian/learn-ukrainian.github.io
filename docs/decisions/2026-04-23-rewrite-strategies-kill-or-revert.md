# ADR-007: Kill the rewrite strategies — enforce reviewer-as-fixer parity

**Status**: APPROVED 2026-04-23 by Krisztian K. (Y/Y/Y on Open Questions). Flips to ACCEPTED when P2-A (#1454) merges and PR-E lands per the Migration Plan gating.
**Date**: 2026-04-23
**Deciders**: Engineering (Krisztian K. — signed off 2026-04-23)
**Related**: EPIC #1451 (Phase 2-C), closer #1456, pipeline rule `claude_extensions/rules/pipeline.md`, decision `dec-001` (reviewer-as-fixer, active since 2026-03-24)
**Supersedes**: #1268, #1277, #1288, #1322

---

## Context

Decision `dec-001` (active in `docs/decisions/decisions.yaml:14-32`, logged 2026-03-24) records: *"V6 uses reviewer-as-fixer, not full rewrite. Reviewer outputs exact find/replace pairs in `<fixes>` block. Pipeline applies them deterministically. No LLM regeneration, no rewriting."* Supporting empirical evidence: Gemini showed FROM-SCRATCH rewrites degrade content across rounds (9.6 → 9.2 → 8.4).

Non-negotiable rule §4 (`claude_extensions/rules/non-negotiable-rules.md`) restates this as the project's authoritative stance, as does the pipeline rule, which flags the contradiction explicitly:

> ⚠️ Live contradiction (tracked as #1456): `scripts/build/convergence_loop.py:595-607` still has `section_rewrite` / `full_rewrite` / `writer_swap` strategies despite the no-rewrite decision.

The contradiction has been live for ~1 month. During the `a1/colors` AI-only smoke (2026-04-23, logged in `docs/decisions/2026-04-23-ai-only-build-infeasible.md`) the pipeline exercised exactly this path: R1 REJECT → `full_rewrite` → R2 REJECT with **the same flag-color hallucination reintroduced by the rewrite** after the `<fixes>` block had already corrected it. Rewrite-driven regression then burned the convergence budget and forced a `plan_revision_request` terminal. That run is both a live-fire validation of the empirical claim from `dec-001` and the immediate trigger for this ADR.

The alignment-pipeline audit (`docs/architecture/2026-04-23-alignment-pipeline-audit.md`, §2 layer 12 and §3 A3) classifies this as *the* canonical instance of decisions being advisory rather than executable — "two different systems under one name." Phase 2-C of the resulting EPIC #1451 is the remediation.

The question this ADR answers is narrow: **which of the two sides of the contradiction changes?** Either the code stops rewriting (ADR-007 KILL path) or the decision admits rewrites with documented constraints (REVERT path).

The evidence supports KILL. The REVERT path has no new data in its favour — the empirical degradation pattern that drove `dec-001` (9.6 → 8.4) reproduced on `a1/colors` this week.

---

## Decision

**Enforce `dec-001` at the code level. Kill every mechanism that lets an LLM regenerate content during review, contract, or style heal loops. Keep exactly one write path (the initial `step_write`) and exactly one fix path (the deterministic `<fixes>` find/replace loop).**

- All tiered rewrite strategies in the convergence loop — `section_rewrite`, `full_rewrite`, `writer_swap` — are removed.
- The reviewer-emitted `<rewrite-block section="...">` directive protocol is removed. Reviewers output `<fixes>` only.
- Auto-heal rewrites for `WORD_BUDGET` contract violations are removed. Word-budget shortfalls that the writer cannot repair via `<fixes>` `insert_after:` become a `plan_revision_request` or `budget_exhausted` terminal — an honest signal that the plan or the writer is under-specified.
- The fix-loop remains as designed: reviewer verdict REVISE emits `<fixes>`, pipeline applies find/replace, re-review. Max 2 fix rounds. Score should go up, never down.
- The convergence ladder collapses from five tiers to two: **tier 1 (patch)** and **tier 5 (plan_revision_request terminal)**. Tiers 2–4 are deleted, not stubbed — stubs invite revival.

This ADR does **not** change `dec-001`. It enforces it. `dec-001` remains the authoritative statement of the policy; this ADR is the implementation-parity pass.

---

## Rewrite-mechanism inventory

Brief framed this as "four overlapping strategies." The actual footprint is larger — **seven call sites across two loops and four supporting helper layers** — but they all reduce to the same class: *LLM regeneration triggered by a review verdict or contract violation.* The verdict for the whole class is the same: **KILL**.

| # | Name | Location | What it does | Why it contradicts dec-001 | Verdict | Closes |
|---|---|---|---|---|---|---|
| M1 | `section_rewrite` tier | `scripts/build/convergence_loop.py:233-234, 597-600`; directive builder `scripts/build/v6_build.py:9000-9013`; dispatch `scripts/build/v6_build.py:9115-9144` | Tier-2 escalation: groups findings by `scope.section_title` and regenerates each section via `_rewrite_block_section`. | LLM regenerates content on REVISE. | **KILL** | #1288 (partial) |
| M2 | `full_rewrite` tier | `scripts/build/convergence_loop.py:239-242, 601-605`; directive `scripts/build/v6_build.py:9016-9027`; dispatch `scripts/build/v6_build.py:9146-9170` | Tier-3 escalation: full `step_write` re-run with a `correction_directive` listing top-3 persistent findings. | Exactly the FROM-SCRATCH rewrite that `dec-001` rejected on empirical evidence. Re-demonstrated on `a1/colors` (2026-04-23). | **KILL** | #1322 |
| M3 | `writer_swap` tier | `scripts/build/convergence_loop.py:243-246, 606-641`; dispatch `scripts/build/v6_build.py:9172-9189` | Tier-4 escalation: rotates writer family (gemini → claude → codex) and invokes `_full_rewrite_round` under the new writer. Guarded by reviewer-matrix feature flag. | Uses M2 under the hood; inherits the same degradation class. Writer-swap by itself doesn't violate `dec-001`, but the only way it currently exercises is through a full rewrite. | **KILL** (see Open Question 1 on operational knob) | #1322 (partial) |
| M4 | Reviewer-emitted `<rewrite-block>` directive | Prompt contract `scripts/build/phases/v6-review.md:160, 169-173, 205-208`; parser `scripts/build/v6_build.py:8146-8173`; applier `scripts/build/v6_build.py:8682-8706`; invoker `scripts/build/v6_build.py:9302-9313` | Review prompt tells the reviewer: *"if a problem cannot be fixed safely with surface edits, emit one or more `<rewrite-block section="...">` directives so the pipeline can regenerate that section."* Runs inside the deprecated `_run_review_heal_loop`. | Gives the reviewer a second lever beyond `<fixes>` — specifically the lever `dec-001` forbids. | **KILL** | #1277 |
| M5 | `WORD_BUDGET` auto-heal rewrite | `scripts/build/v6_build.py:8825-8902`; invoker `scripts/build/v6_build.py:9328-9346` | When contract compliance flags ERROR-severity `WORD_BUDGET` violations, loops each offending section and triggers `_rewrite_block_section` to expand it. | LLM regeneration driven by a contract-violation signal. Exactly the heal-loop pattern #1322 set out to eliminate. | **KILL** | #1288 |
| M6 | Rewrite-block infrastructure (shared by M1, M4, M5) | `scripts/build/v6_build.py:8383-8464` (`_dispatch_rewrite_prompt`, `_rewrite_block_guardrails`, `_extract_rewrite_block_auxiliary_forbidden_literals`); `:8466-8542` (`_rewrite_block_prompt_manifest`, `_audit_rewrite_block_prompt`); `:8544-8679` (`_rewrite_block_section`) | Shared machinery: prompt assembly, deterministic prompt audit, dispatch, post-rewrite validation (word-ratio floor, H2 preservation, activity-type contract check). | Sole purpose is to serve M1/M4/M5. Zero legitimate consumers after those are removed. | **KILL** (removed with M1/M4/M5) | #1268 (per-call Gemini budget cap becomes moot), #1277 (prompt-audit guards become moot) |
| M7 | Style-review heal loop | `scripts/build/v6_build.py:9596-9642` | Historical rewrite loop. **Already reverted to advisory-only** (2026-04-23; comment at `:9608-9609`: *"Instead of looping (churn), we save advice to the contract for next time"*). Current behavior: run style review once, persist blocking issues as contract advice, continue. | Was a rewrite loop; is now compliant. | **KEEP AS-IS** (no change) | — |

### Cross-cutting observations

- **`_run_review_heal_loop` (`v6_build.py:9244-9594`) appears to be dead code.** <!-- VERIFY --> The main build path at `v6_build.py:11349` calls `_run_convergence_loop`, not `_run_review_heal_loop`. `_run_review_heal_loop` is where M4 and M5 are invoked. If it is truly unreachable in the production code path, M4 and M5 are already quiescent and the KILL is a removal of dead code rather than a behavioural change. Resolution: grep the repo for any remaining callers of `_run_review_heal_loop` and confirm. If genuinely dead, Phase 2-C gains a freebie — remove the loop and its rewrite callers in one commit with no runtime consequence. If a caller exists (resume path, test harness, CLI flag), the KILL has real blast radius and must be sequenced after users of that path are migrated.
- **`CONVERGENCE_MATRIX_ENFORCED` feature flag** (`v6_build.py:186, 5653, 9236`): governs whether writer_swap is reviewer-matrix-gated. Becomes irrelevant once M3 is removed; the flag can be retired in the same commit that removes the writer-swap code.
- **Orphan tests after the kill.** `tests/test_convergence_loop.py` contains ≥7 assertions on `section_rewrite` / `full_rewrite` / `writer_swap` tier firing. `tests/test_rewrite_safety.py` exercises `_rewrite_block_section` backup/restore. Both become orphans. The fix-loop tests in `tests/test_v6_contract_flow.py`, `tests/test_v6_review_regression_guard.py`, `tests/test_v6_insert_after_fix.py` remain live and continue to cover the retained `<fixes>` path.

### Scope framing — honest disagreement with the brief

The brief described "four rewrite strategies." I found seven mechanisms spread across two loops. The spirit of the framing is correct: there is one fundamental contradiction with `dec-001`, not four. But the remediation is wider than editing three lines of `convergence_loop.py` — it deletes the `<rewrite-block>` protocol from the reviewer prompt, the `WORD_BUDGET` auto-heal, and ~400 LOC of rewrite-block infrastructure. An implementer who scoped only to `convergence_loop.py:595-607` would leave half the contradiction in place.

---

## Consequences

### Positive

- **`dec-001` becomes executable.** The decision journal stops being advisory at this surface.
- **Empirical quality degradation path closes.** The 9.6 → 8.4 regression pattern that `dec-001` documented, re-demonstrated on `a1/colors` this week, has no remaining code path.
- **Fewer moving parts.** ~400 LOC of rewrite-block infrastructure, three tier strategies, one protocol extension in the reviewer prompt, and one feature flag are removed. Surface area for drift-class bugs (EPIC #1451's central concern) drops materially.
- **Terminal honesty.** Plan-level and writer-level failures flow to `plan_revision_request` or `budget_exhausted` instead of being masked by 2–3 automatic rewrite retries that often regress. This matches the convergent-pipeline spec's "honest human-dependent terminals" contract (#1322).
- **Closes four open issues** (#1268, #1277, #1288, #1322) without per-issue work. One architectural decision, four closures.

### Negative / risks

- **No more in-loop recovery for cross-section findings.** Before: a cross-section finding triggered M2 (full rewrite) and sometimes converged. After: same finding → `plan_revision_request` terminal, human fixes plan, re-fire module. Throughput on stuck modules drops; convergence budget is shorter.
- **`WORD_BUDGET` ERRORs become hard failures.** Writer that undershoots on a section must either be fixed by `<fixes>` `insert_after:` entries from the reviewer, or the module fails review. This is structurally correct (the plan's word budget is a contract) but operationally stricter than today. See Open Question 2.
- **Threshold split-brain amplifies the consequence.** Module review threshold is 8.0 (`v6_build.py:112`); audit naturalness threshold is 9.0 (`audit/config.py:46-56`). With rewrites killed, modules that sit in the 8.0–8.9 band more often hit `plan_revision_request` rather than getting auto-repaired. P2-A (unified threshold table) is therefore a **hard prerequisite** for ACCEPTED status — see Migration Plan. See Open Question 3.
- **Writer-model-variance resilience drops.** M3 (writer_swap) was the only mechanism that could react to a single-writer bad-sampling day. After KILL, a sampling-variance failure fails the module. The alternative mitigation is a small writer-side naturalness pre-check (already tracked as a follow-up in the AI-only brief) that runs BEFORE review rather than rewriting AFTER it.
- **~8 orphan tests to remove or re-purpose.** Quantified above. Non-trivial but bounded.

### Neutral / follow-ups

- Prompt-audit guards (#1277's deliverable) are preserved at the architectural level — they just won't guard rewrite prompts any more, because rewrite prompts cease to exist. If a future ADR revives a narrower rewrite mechanism, the prompt-audit pattern is still the correct way to govern it.
- `dec-001` stays live. This ADR is an *enforcement* event, not a supersession of the underlying policy.

---

## Migration plan

PRs land in this order. Each PR is independently revertable. No PR leaves the tree in a mixed state.

**PR-A — Remove M1, M2, M3 from the convergence loop.** Owner: Codex. Scope: `scripts/build/convergence_loop.py` (delete tier-2/3/4 branches in `select_strategy` and the corresponding `try:` arms in `run_convergence_loop`; simplify `ConvergenceContext` to drop `section_rewrite_round`, `full_rewrite_round`, `writer_swap_round`, `style_review_after_swap`, `reviewer_matrix_enforced`). `scripts/build/v6_build.py` (delete `_section_rewrite_round`, `_full_rewrite_round`, `_writer_swap_round`, `_build_section_rewrite_directive`, `_build_full_rewrite_directive`; simplify the `_run_convergence_loop` wiring). Tests: prune `tests/test_convergence_loop.py` to the patch + terminal cases; delete tier-2/3/4 assertions.

**PR-B — Remove M4 (reviewer `<rewrite-block>` protocol).** Owner: Codex. Scope: `scripts/build/phases/v6-review.md` (strike lines 160, 169-173, 205-208 — the "rewrite-block" emission contract). `scripts/build/v6_build.py` (delete `_parse_rewrite_blocks`, `_apply_review_rewrite_blocks`, and the call at `:9302-9313` inside `_run_review_heal_loop`). Regenerate any cached review-prompt fixtures.

**PR-C — Remove M5 (WORD_BUDGET auto-heal).** Owner: Codex. Scope: `scripts/build/v6_build.py` (delete `_apply_contract_word_budget_rewrites` and its invoker at `:9328-9346`). Move WORD_BUDGET ERROR handling into the standard contract-violation path: ERROR-severity WORD_BUDGET now surfaces as a review finding and can be addressed only via `<fixes>` `insert_after:` entries — if the reviewer can't emit a repair, the module fails.

**PR-D — Remove M6 (rewrite-block infrastructure) and dead code cleanup.** Owner: Codex. Scope: `scripts/build/v6_build.py` — after PRs A/B/C land, the rewrite-block helpers (`_rewrite_block_section`, `_rewrite_block_prompt_manifest`, `_audit_rewrite_block_prompt`, `_dispatch_rewrite_prompt`, `_rewrite_block_guardrails`, `_extract_rewrite_block_auxiliary_forbidden_literals`) have zero remaining callers. Delete them. Delete `CONVERGENCE_MATRIX_ENFORCED` feature flag and its test wiring. Delete `tests/test_rewrite_safety.py`. Verify `_run_review_heal_loop` callers (see Cross-cutting observation above) — if zero, delete the loop. Remove the `rewrite_blocks` field from the `per_dim_review` result tuple and any downstream consumers.

**PR-E — Supersede closure and decision-journal alignment.** Owner: Claude. Scope: comment on #1268, #1277, #1288, #1322 with pointers to this ADR + the merged PRs; close each with `superseded` label. Update `docs/decisions/INDEX.md` to add this ADR. Add a `dec-007` entry in `docs/decisions/decisions.yaml` that references dec-001 via `depends_on` and records the enforcement. Update `claude_extensions/rules/pipeline.md` — remove the "live contradiction" warning block; redeploy via `npm run claude:deploy`.

**PR-F — Invariant test (Phase 4-E precursor).** Owner: Codex. Scope: `tests/test_no_rewrite_contract.py` — fails CI if any of the deleted symbol names reappear in `scripts/build/` or if the string `<rewrite-block` reappears in a phase prompt. This is a structural guard against reintroduction and functions as the "validation" side of the ADR.

**Gating with P2-A (unified thresholds):** PRs A–D can land concurrently with P2-A but must NOT flip to ACCEPTED status until P2-A merges. Rationale: under today's 8.0-vs-9.0 split-brain thresholds, a KILLed rewrite ladder will fire `plan_revision_request` on modules that would have passed under unified thresholds. Sequencing: P2-A lands first, then PR-E (decision-journal flip) lands, then the ADR status moves PROPOSED → ACCEPTED.

---

## Validation

After the migration plan lands, the ADR's intent holds if and only if:

1. **Grep invariant:** `grep -RE 'section_rewrite|full_rewrite|writer_swap|_rewrite_block_section|<rewrite-block' scripts/build/ scripts/build/phases/` returns zero matches, with the single possible exception of comments explicitly referencing this ADR. Enforced by the PR-F test.
2. **Runtime invariant:** `scripts/build/convergence_loop.py:select_strategy` returns exactly two strategies across all inputs: `"patch"` and `"plan_revision_request"`. No test path should be able to coax it into another strategy. Enforced by pruning `tests/test_convergence_loop.py` down to those two cases plus error paths.
3. **Policy invariant:** `scripts/check_decisions.py` runs clean (no staleness on dec-001 or the new dec-007). The rules-deployment invariant (EPIC #1451 Phase 4-E) keeps `claude_extensions/rules/pipeline.md` and `.claude/rules/pipeline.md` in sync so the "live contradiction" warning doesn't silently reappear in `.claude/`.
4. **Observable behavior on `a1/colors` rebuild:** when Phase 5 re-fires the module (per #1451 Phase 5), the run produces either a single R1 PASS or at most 2 fix rounds (R1 REVISE → `<fixes>` → R2 PASS). No `full_rewrite` trace entries in `orchestration/colors/state.json`. A regression that reintroduces the flag-color hallucination (as in the 2026-04-23 smoke) now fails the module outright rather than being masked by a rewrite loop.
5. **Orphan-symbol check:** CI fails if any of the removed function names or the `<rewrite-block>` prompt string reappear in `scripts/build/` — the PR-F test.

---

## Supersedes

- **#1268** — Cap per-call Gemini runtime budget for section rewrite blocks → *obsolete*: section rewrites removed.
- **#1277** — Slim v6 rewrite-block prompts and add deterministic prompt-audit guards → *obsolete*: rewrite prompts removed; prompt-audit pattern preserved as architectural reference for any future ADR that narrows scope.
- **#1288** — Auto-heal review-loop WORD_BUDGET contract violations with section rewrites → *rejected*: WORD_BUDGET auto-heal directly contradicts dec-001; failures surface as terminals or require `<fixes>` `insert_after:` repairs.
- **#1322** — Convergent pipeline — replace heal loop, eliminate needs-human-review.yaml → *partially shipped, now tightened*: the "convergent pipeline" ships without the three rewrite tiers it originally proposed. Terminals (`pass`, `plan_revision_request`, `budget_exhausted`) and `stuck-modules.yaml` emission remain; the in-loop rewrite ladder does not.

## Related

- EPIC #1451 (Phase 2-C of Alignment-Pipeline Runtime Contracts)
- Closer issue #1456
- Active decision `dec-001` (reviewer-as-fixer, no rewrite)
- Non-negotiable rule §4 (`claude_extensions/rules/non-negotiable-rules.md`)
- Pipeline rule (`claude_extensions/rules/pipeline.md`) — carries the "live contradiction" warning that this ADR retires
- Alignment-pipeline audit `docs/architecture/2026-04-23-alignment-pipeline-audit.md` §2 layer 12, §3 A3
- AI-only decision brief `docs/decisions/2026-04-23-ai-only-build-infeasible.md` — live-fire evidence that `full_rewrite` regresses on content already corrected by `<fixes>`
- `docs/bug-autopsies/alignment-contracts.md` §3 (expected update after this ADR lands)

## Expiry

**Review by 2027-04-23** (12 months). The reason for a longer-than-default window: this ADR enforces a policy (dec-001) that has been re-validated twice already by independent empirical evidence (Gemini's original 9.6→8.4 data; the 2026-04-23 colors smoke). Short expiries invite premature revival on insufficient data. If someone proposes reintroducing any rewrite mechanism before 2027-04-23, the burden is new empirical evidence that FROM-SCRATCH rewrites do NOT degrade content in the project's current configuration — not a new theory about why they should work.

---

## Open questions — answered 2026-04-23

Signed off by Krisztian K. on 2026-04-23.

1. **Writer-swap as an operational knob — keep or delete?** → **Y (delete entirely).** No `--writer-override` CLI escape hatch. Manual re-fire under a different writer uses the existing `--writer` flag on a fresh module invocation, which is already a clean `step_write` path.

2. **WORD_BUDGET ERROR → terminal, OK?** → **Y.** Unrepairable WORD_BUDGET ERROR fails the module to `plan_revision_request`. The plan's budget is a contract; chronic undershoot is a plan or writer-prompt signal, not a thing to auto-heal over.

3. **Hold ACCEPTED status until P2-A (unified thresholds) merges?** → **Y.** PRs A–D can land concurrently with P2-A. PR-E (decision-journal flip + status transition to ACCEPTED) sequences AFTER P2-A merges. Rationale: under today's 8.0-vs-9.0 split-brain thresholds, KILLed rewrites would fire `plan_revision_request` on modules that would pass under unified thresholds.

**Implementation status at sign-off:** APPROVED. PRs A/B/C/D may be dispatched to Codex (tier deletion + prompt surgery + dead-code cleanup + invariant test). PR-E held until P2-A (#1454) lands and this ADR flips to ACCEPTED.
