# DECISION — Restore student-aware lesson building in V7 + replace flat-% immersion with ULP-derived cumulative-vocab-aware model (ACCEPTED)

**Status:** ACCEPTED 2026-05-13
**Decided:** Approve as recommended — all 5 sub-points: (Q1) option (a) unified plan-schema (`plan.targets` block subsumes #1916 Gate 4 schema work); (Q2) `unknown_vocabulary` audit-gate severity WARN m01-m03 / HARD m04+; (Q3) recycle-cadence default values deferred to Phase 4 calibration replay; (Q4) `learner_state.py` stays in `scripts/pipeline/` (cross-cuts pipeline + audit); (Q5) A1 backfill targeted for immediate pilot, lazy mechanical-dispatch for remaining 54 modules after schema-shape validation. PR1 (learner-state V7 wiring) dispatches immediately to Codex.
**Decided on:** 2026-05-13 (user signoff via cold-start AskUserQuestion — "Approve as recommended")
**Surfaced:** 2026-05-13 (orchestrator handoff `docs/session-state/2026-05-14-v7-mdx-assembler-shipped-brief.md` — "Architectural Finding" section)
**Source:** Empirical audit of `scripts/build/` confirming `learner_state.py` is unwired in V7; user directive at the end of the 2026-05-14 session — *"do not use flat-% immersion; use what we learned from ULP."* User explicitly redirected the next session to A1 focus and named this as the biggest leverage on A1 pedagogy.
**Scope:** V7 pipeline writer-prompt + audit gate layer + immersion policy generation + plan schema (vocabulary signals only). **Does NOT touch:** writer choice (claude-tools per `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md` REVISED 2026-05-12 night); reviewer phase (Codex `codex-tools` per `2026-04-26-reboot-agent-responsibilities.md` §2); decolonization rules; structural immersion sub-gates (tab-aware Gates 1–3 from `2026-05-13-immersion-gate-tab-aware-structural.md`, already ACCEPTED + Phase A landed); B1+ Latin-character ratio rule.
**Predecessor + companions:**
- `docs/decisions/2026-05-13-immersion-gate-tab-aware-structural.md` (ACCEPTED) — Gate 1/2/3 (tab-aware structural). Phase A landed; Phase B calibration is #1918.
- `docs/decisions/pending/2026-05-13-writer-split-by-tab.md` — DEFERRED until Phase B replay clarifies need. **Independent of this card.**
- `#1916` — Phase A follow-up: Gate 4 (Progressive Challenge) needs `plan.targets` schema. **Coupled to PR2.** This card proposes a unified plan-schema-extension that subsumes #1916.

---

## What's being proposed

V7 currently builds modules in isolation: the writer prompt has no `{LEARNER_STATE}` placeholder; no audit gate checks that introduced UK words come from the cumulative-vocab set or the plan's new-vocab declaration; the immersion bands in `scripts/config.py:IMMERSION_POLICIES` are static module-number ranges (e.g. `a1-m01-03`, `a1-m04-06`) that ignore *what the learner has actually seen*. This card proposes a **two-PR split** to close that gap:

### PR1 — Restore learner-state V7 wiring

Wire the existing `scripts/pipeline/learner_state.py` (v6 code, intact and well-documented) into V7's prompt assembly + audit pipeline.

- **Path fix.** `learner_state.py:28` reads `curriculum/l2-uk-en/{track}/vocabulary/{slug}.yaml` (v6 layout); V7 stores at `curriculum/l2-uk-en/{level}/{slug}/vocabulary.yaml`. Update `_load_vocab()` to V7 layout; keep v6 path as a fallback only if needed for legacy plans.
- **Prompt placeholder.** Add `{LEARNER_STATE}` to `scripts/build/phases/linear-write.md` (logical placement: after `## Module Context` block at line 228, before `## Immersion Rule` at line 230). Wire `format_learner_state(build_learner_state(track, module_num))` into `prompt_builder.py` substitutions.
- **New audit gate.** Add `scripts/audit/checks/learner_state.py` with two HARD checks:
  1. `unknown_vocabulary` — any UK lemma in `module.md` body that is NOT in `cumulative_vocabulary` AND NOT declared as new in this module's `vocabulary.yaml` is a violation. Tolerance: `max_unsupported_uk_words` from the existing structural band (re-use, don't add a new threshold).
  2. `known_grammar_re_explanation` — flag if `module.md` re-explains a grammar topic from `known_grammar` (heuristic: section header containing a topic substring; severity WARN at A1, HARD at B1+).
- **Restored capability.** The format-string mechanic in `learner_state.py:151-190` already produces the right prompt injection: rule-set + foreshadowing + cumulative-vocab list + previously-taught grammar list. PR1 is a wiring restoration, not a redesign.

**Estimate.** ~150-250 LOC. Touches:
- `scripts/pipeline/learner_state.py` (path constant)
- `scripts/build/prompt_builder.py` (add substitution)
- `scripts/build/phases/linear-write.md` (add placeholder + 2-line directive)
- `scripts/audit/checks/learner_state.py` (new file)
- `scripts/audit/__init__.py` or registry (register new check)
- Test files: `tests/test_learner_state_v7_layout.py`, `tests/test_audit_learner_state.py`

### PR2 — ULP-derived cumulative-vocab-aware immersion model

Replace the static `IMMERSION_POLICIES` bands with a model that **derives** the immersion floor/ceiling for module N from cumulative-vocab-count + new-vocab-count + pattern-frequency, in the shape Anna Ohoiko's ULP S1–S6 corpus uses.

Three components:

1. **Cumulative-vocab-aware bands.** Replace fixed `(a1-m01-03, a1-m04-06, a1-m07-14, a1-m15-24, a1-m25-34)` with a function `compute_immersion_band(track, module_num, learner_state) -> dict`. Inputs include `learner_state.cumulative_vocabulary` count + this module's `plan.targets.new_vocabulary` declared count + the lemma-frequency map. The function is **deterministic and tested**; output mirrors today's band schema (advisory_pct_min/max + structural fields), so downstream gates don't change. The "ULP-derived" calibration constants live in `scripts/config.py` (one block), not in code paths.
2. **Pattern-frequency model.** New file `scripts/build/learner_immersion.py` builds a lemma-frequency map across all preceding modules (lemma → list of `(module_num, surface_form_count)`). Required by Progressive Challenge gate + by the cumulative-vocab-aware bands. Single source of truth — both PR2 gates and #1916 Gate 4 read from it.
3. **Recycle cadence gate.** New audit check (HARD at A1, WARN at A2+): every M modules, the module under build must surface at least N earlier-introduced lemmas (default initial values land as code constants, calibrated in a follow-up replay session). Prevents A1 modules from front-loading without consolidation.

**Estimate.** ~300-450 LOC across `scripts/build/learner_immersion.py` (new), `scripts/config.py` (replace `IMMERSION_POLICIES` static dict with derivation function + calibration constants), `scripts/audit/checks/` (new recycle-cadence check), `tests/`. Plus plan-schema extension if Gate 4 / #1916 lands inside this PR.

**Plan-schema decision (open question — see below).** PR2 needs `plan.targets.new_vocabulary` and `plan.targets.grammar` to know what's *introduced* in this module vs what's *carried* from before. Today's `vocabulary_hints.required` is informal and not deterministically parsed. Either:
- (a) PR2 ships with a new `plan.targets` block (subsumes #1916 Gate 4 schema work);
- (b) PR2 reads `vocabulary_hints.required` (fragile, but no schema churn) and we land #1916 separately;
- (c) PR2 splits into PR2a (Gate-4-aware schema + Progressive Challenge gate) + PR2b (cumulative-vocab immersion derivation that depends on PR2a).

Recommended: **(a) — unify plan-schema work into PR2.** Two passes through the plan-schema deliberation costs more than one. #1916 is the natural integration point.

---

## Where the numbers live (SSOT)

Per `docs/best-practices/module-content-quality.md`: "For technical validation thresholds, `scripts/audit/config.py` is authoritative." This Decision Card describes derivation LOGIC; the calibration constants live in code:

- **`scripts/config.py`** — replace `IMMERSION_POLICIES` static dict with `compute_immersion_band()` derivation function + calibration constants (e.g. `_ULP_VOCAB_KNEE_PER_BAND`, `_RECYCLE_CADENCE_DEFAULTS`, `_PATTERN_FREQ_MASTERY_THRESHOLD`). All numeric values stay in this one file.
- **`scripts/audit/config.py`** — recycle-cadence severity thresholds + unknown-vocabulary tolerance (re-uses existing `max_unsupported_uk_words` from structural-gate decision).
- **No numbers in this Decision Card or in any contract doc.** Initial calibration is a follow-up replay session (estimate 1-2 hours of Codex telemetry analysis against the existing 5 deployed A1 modules + the validated `a1/my-morning` pilot).

---

## Why this might be worth doing

1. **Every A1 pilot we build today has the same flaw.** The handoff explicitly says `a1/my-morning` passes 5/5 visual contracts but is *pedagogically un-scaffolded against learner's prior knowledge.* This is the single biggest correctness gap in the V7 pipeline as deployed; structural gates can rate any individual module as well-formed while still letting it cite vocabulary the learner has never seen. PR1 closes that gap with code we already wrote (v6 `learner_state.py`).
2. **User explicit directive.** The 2026-05-14 handoff session ended with user redirection — *"do not use flat-% immersion; use what we learned from ULP."* That is the design constraint. Flat-band `IMMERSION_POLICIES` is a v6/early-V7 inheritance; ULP teaches by cumulative scaffolding, not by ratio target.
3. **ULP is the reference corpus we already have.** `docs/references/private/ULP {1–6}-00 Lesson Notes` (6 PDFs/TXT, all loaded), plus `1000 Ukrainian Words` + `500+ Ukrainian Verbs` companion materials, plus the `ohoiko-june-a1-book` PDF, give us a 6-season scaffold to extract the cumulative-vocab → immersion curve from. Anna Ohoiko's structural transformations across S1→S6 are the gold standard the handoff and the prior immersion-gate Decision Card both anchored on.
4. **Composability with the tab-aware structural gates.** The `2026-05-13-immersion-gate-tab-aware-structural.md` ACCEPTED gates (Gates 1–3) checked *form* (where UK appears in the page). Adding ULP-derived bands + Progressive Challenge + recycle cadence checks *content* (what UK appears, against prior knowledge). The two layers compose cleanly: structural gates measure the artifact; learner-state gates measure the artifact against the learner's history.
5. **Subsumes #1916 cleanly.** Gate 4 (Progressive Challenge) requires `plan.targets`; PR2 needs the same fields. One schema-evolution PR covers both.
6. **Re-uses v6 code.** PR1 is wiring restoration, not a clean-sheet rewrite. The behavior is already tested (in v6 against gemini-writer), already documented in the module file, and already produces the right prompt-injection text.
7. **Surfaces a real downstream test.** After PR1 lands and `a1/my-morning` is rebuilt with `{LEARNER_STATE}` injected, the second A1 module (`a1/around-the-city` or `a1/at-the-cafe`) becomes the first end-to-end test of *student-aware* lesson building in V7. That's an empirical signal worth ~30 min of Codex dispatch.

## Why this might NOT be worth doing

1. **Plan-schema churn.** Option (a) means a `plan.targets` block must be added to all A1 plans (55 modules) and likely all A2/B1 plans for forward compatibility. Migration script + a one-time mechanical pass. Estimate ~1-2 hours of dispatched work + one schema-evolution test. Not free.
2. **Calibration risk on PR2.** Cumulative-vocab → immersion-band derivation function has free parameters (the "ULP knee" — at what vocab-count the band changes shape). Wrong constants = either too-permissive immersion (lets confusing pilot modules through) or too-strict (false-fails real ULP-shaped modules). Mitigation: ship PR2 behind a feature flag, replay against the 5 deployed A1 modules + `a1/my-morning`, calibrate before flipping.
3. **Could be subsumed by the writer-split-by-tab pending card.** `docs/decisions/pending/2026-05-13-writer-split-by-tab.md` is DEFERRED but not closed. If that ships, per-tab writer agents would need their own learner-state slices (Tab 1 prose, Tab 2 vocab, Tab 3 activities). Hedge: the data layer (`learner_state.py` + lemma-frequency map) is the same in both worlds; only the *injection points* multiply. PR1's wiring is a no-regret move regardless of writer-split outcome.
4. **No regression net for ULP-fit.** Today, "does the module feel ULP-shaped" is a manual reviewer call. Codifying it as a deterministic gate is a strictly higher standard. Risk: we calibrate against ULP S1, ULP S2 happens to have a different vocab-density curve than S1, our constants are too narrow. Mitigation: replay against all 6 seasons before locking constants.
5. **`learner_state.py` `_load_grammar()` reads `plans/{track}/{slug}.yaml`.** That path is v6-layout-correct; V7 plans live at `curriculum/l2-uk-en/plans/a1/{slug}.yaml` which matches. Confirmed via `ls curriculum/l2-uk-en/plans/a1/`. So PR1's path fix is *only* the vocabulary load; the grammar load is already V7-compatible. Worth confirming before dispatching to avoid scope creep.
6. **Pattern-frequency map builds quadratically in module count.** For A1 (55 modules) this is negligible; for full curriculum (1803 modules across all tracks) it's still <10K lemma-entries and ~O(seconds) to rebuild from scratch. Cached on disk between runs. Not a real cost.

---

## Open questions (require user input before PR1 dispatch)

1. **Plan-schema option (a) vs (b) vs (c)?** Recommended: (a) — unify Gate 4 + ULP-immersion plan-schema into PR2. Alternative (c) splits into PR2a + PR2b for smaller diffs. (b) avoids schema churn but is fragile.
2. **PR1 audit-gate severity at A1.** `unknown_vocabulary` HARD vs WARN at A1-early modules (m01-06)? HARD seems right (no escape valve = forces plan accuracy) but blocks pilot builds until plans declare vocab correctly. Recommended: WARN for m01-m03 (warm-up grace), HARD m04+.
3. **Recycle-cadence default values.** Defer to follow-up replay session, or land placeholder values with PR2 (e.g. every 5 modules, surface ≥3 lemmas from preceding window)? Recommended: defer — calibration is its own task.
4. **`learner_state.py` ownership.** Currently in `scripts/pipeline/` (v6-era directory). Move to `scripts/build/learner_state.py` to match V7 location convention? Recommended: leave in place; cross-cuts pipeline + audit so neither home is "correct." Tag the file header with V7 status.
5. **A1 backfill obligation.** Once PR1 + PR2 land, do we backfill `plan.targets.new_vocabulary` for all 55 A1 plans before rebuilding any A1 pilot? Or only fill for the next pilot module (`around-the-city` or `at-the-cafe`) and migrate the rest lazily? Recommended: targeted fill for the immediate pilot, lazy backfill for the rest, mechanical-dispatch the bulk migration after we've validated the schema shape on one module.

---

## Implementation phases

**Phase 1 — PR1 (learner-state V7 wiring)** — dispatch after user signoff on Q1, Q2, Q4 above. Codex-tools, single worktree, conventional commit, PR, no auto-merge (pre-submit checklist mandatory). Expected to land in ~30-45 min of Codex dispatch time.

**Phase 2 — PR1 verification** — rebuild `a1/my-morning` with `{LEARNER_STATE}` injected (user runs `v7_build a1 my-morning`); confirm the writer prompt now contains a learner-state block; confirm audit reports `unknown_vocabulary` gate state. Inspect resulting `module.md` for behavioral change vs. pre-PR1 output.

**Phase 3 — PR2 (ULP-derived immersion model + Gate 4 + recycle cadence)** — dispatch after Phase 2 + signoff on Q3, Q5. ~1.5-2 hr Codex dispatch + schema-migration tooling. Behind feature flag (`USE_ULP_IMMERSION_DERIVATION=false` default; flip after replay validates).

**Phase 4 — Calibration replay** — Codex dispatch: rebuild lemma-frequency map across the 6 ULP seasons; tune `_ULP_VOCAB_KNEE_PER_BAND` constants so the derived bands match (within tolerance) the structural distribution observed in ULP S1→S6; emit a calibration report at `audit/ulp-calibration-{date}.md`. Flip feature flag.

**Phase 5 — Second A1 pilot** — pick `a1/around-the-city` (next A1 module per `curriculum.yaml`) and run end-to-end with student-aware pipeline live. First true validation that the system generalizes beyond `my-morning`.

---

## What this card does NOT decide

- Writer choice (claude-tools, already decided + REVISED 2026-05-12 night).
- Reviewer choice (Codex, decided 2026-04-26).
- Tab-aware structural Gate 1/2/3 calibration — that's #1918 Phase B replay, independent.
- Writer-split-by-tab — pending separately, not blocked by this card.
- A1 batch-build trigger — still blocked on textbook_grounding HARD gate (#1901, in dispatch).
- Whether to commit the 5 dirty V7 source artifacts at `curriculum/l2-uk-en/a1/my-morning/` — separate operational decision, surfaced in task tracker.

---

## References

- `scripts/pipeline/learner_state.py` — existing v6 code, V7-ready except `_load_vocab()` path.
- `scripts/build/phases/linear-write.md:228–232` — insertion point for `{LEARNER_STATE}` placeholder.
- `scripts/config.py:161–595` — `IMMERSION_POLICIES` static-bands definition (replaced by PR2).
- `scripts/build/linear_pipeline.py:4956+` — `_advisory_immersion_pct()` already demoted to telemetry per the prior immersion-gate card; PR2 does not re-promote it.
- `docs/references/private/ULP {1–6}-00 Lesson Notes (all in one file)` — calibration source corpus.
- `curriculum/l2-uk-en/plans/a1/my-morning.yaml` — example plan with `vocabulary_hints.required` field that PR2 formalizes as `plan.targets.new_vocabulary`.
- `docs/session-state/2026-05-14-v7-mdx-assembler-shipped-brief.md` § "Architectural Finding" — surface document for this card.
- `docs/decisions/2026-05-13-immersion-gate-tab-aware-structural.md` — predecessor, Gates 1–3 (ACCEPTED).
- `#1916` — Phase A follow-up: Gate 4 needs `plan.targets` schema (subsumed by PR2).
- `#1918` — Phase B calibration of tab-aware gates (independent, Phase B).
