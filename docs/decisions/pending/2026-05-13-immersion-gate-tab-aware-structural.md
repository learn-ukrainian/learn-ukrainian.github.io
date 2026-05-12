# DECISION REQUIRED — Should we replace the global-% immersion gate with tab-aware structural gates?

**Status:** PROPOSED (orchestrator-surfaced, awaiting user signoff)
**Surfaced:** 2026-05-13 evening, after a session-long conversation that walked the framing from "tune the immersion %" → "ramp the immersion %" → "structural failure modes, not %" → empirical validation against all 6 ULP seasons + 5 deployed A1 modules + the new 4-tab Lesson Contract format
**Source:** User's pushback on the immersion gate as misshapen ("pedagogy is more important than immersion"); multi-agent discussion `immersion-reframe-2026-05-13` (Codex + Gemini converged at round 2, both `[AGREE]`); empirical reading of `_archive/a1-backup-2026-04-08/content/` + ULP S1-S6 lesson notes
**Scope:** V7 pipeline gate logic (`scripts/build/linear_pipeline.py:4582-4624`) + immersion policy config (`scripts/config.py:152+`) + Lesson Contract §4.6 amendment. **Does NOT touch:** writer-choice (separate proposal), reviewer phase, plan schema, decolonization rules, B1+ Latin-character ratio rule (already structural, correct)

---

## What's being proposed

Replace the current `_immersion_gate()` hard-pass/fail-on-percentage check at A1/A2 with **four failure-mode-targeted gates**, tab-aware and component-aware. Demote the global percentage to **advisory telemetry** (Codex's "Option A as destination, Option C as migration path" framing — don't blind-cut the metric until replay validates the new gates).

The four gates:

1. **L2 Exposure Floor** — catches "essay about Ukrainian, not Ukrainian content." Enforces minimum UK dialogue lines, vocab entries, example sentences, and tab-3 UK activities per module, scaled by sublevel band. Below the floor = FAIL.
2. **Long-UK-Without-Gloss Ceiling** — catches "wall of Ukrainian at A1." Enforces a maximum UK-only run length in Tab 1 prose before English support (parenthetical gloss, English sentence, English heading) is required. Gemini's "gloss proximity" insight: at A1 early, the support proximity is sentence-level interleaving — a 30-word UK block followed by a 30-word EN block is still a wall to a beginner. Scaled by sublevel.
3. **Component-Aware Language Density** — catches "wrong language for the wrong purpose." Different components have different UK density expectations: `DialogueBox` ≥95% UK; `RuleBox` EN-dominant explanation at A1 early; `VocabCard` UK lemma + UK example + EN translation column; Tab 3 activity instructions EN-acceptable at A1, UK-required at B1+ per existing `ACTIVITY_CONFIGS` matrix.
4. **Progressive Challenge** — catches "floor-gaming with dull repetitive padding." New UK examples must exercise the module's target grammar/vocab (from `plan.targets`), not arbitrary content. Codex's insight; requires `plan.targets.grammar` / `plan.targets.vocabulary` fields which may need plan-schema addition.

## Where the numbers live (SSOT)

Per `docs/best-practices/module-content-quality.md`: "For technical validation thresholds, `scripts/audit/config.py` is authoritative." This Decision Card describes the gate LOGIC; the actual numbers live in code:

- **`scripts/config.py:IMMERSION_POLICIES`** — extend each band record (e.g. `a1-m15-24`) with new structural fields: `min_uk_dialogue_lines`, `min_vocab_entries`, `min_uk_example_sentences`, `min_uk_tab3_activities`, `max_unsupported_uk_words`, `support_proximity`, `required_components`, `min_target_grammar_coverage_pct`, `min_target_vocab_coverage_pct`, `advisory_pct_range` (renamed from `min_pct/max_pct`, demoted)
- **`scripts/audit/config.py:AUDIT_THRESHOLDS`** — add severity/tolerance keys: `exposure_floor_warn_pct`, `long_uk_warn_words_over`, `long_uk_fail_words_over`
- **No numbers in this Decision Card or in any contract doc.** Calibration is Phase B work, lands as separate PR

## Why this might be worth doing

1. **The current gate catches the wrong things and misses the right things.** Today's claude bakeoff failed the `immersion` gate at `pct=25.4%` with policy cap 24%. The actual problem was 3 long UK teaching-prose sentences without inline gloss (a Gate 2 failure under the new model). The percentage was a downstream symptom; the root cause was structural.
2. **Empirically validated by ULP across 6 seasons.** Anna Ohoiko doesn't write to a percentage target. Her structural transformations across S1-S6 (metalanguage shift at S1→S2 boundary; translation-density flip at S3→S4) are measurable structural events. The deployed A1 modules already follow the equivalent principles in our format (bilingual headers, pure-UK dialogues with parenthetical gloss, EN-dominant teaching prose, bilingual vocab tables).
3. **Aligned with how instruction-tuned LLMs actually behave.** Per Gemini's read: "Write a 6-turn dialogue with line-by-line English glosses, followed by a 150-word grammar explanation in English" is far more reliable than "target 22% Ukrainian." Structural constraints beat ratio constraints for LLM writers.
4. **Tab-aware is more honest than monolithic.** The 4-tab structure (Урок / Словник / Вправи / Ресурси) has fundamentally different language-density expectations per tab. Tab 2 is bilingual by design (vocabulary translations); Tab 3 activities have type-specific UK density per `ACTIVITY_CONFIGS`; Tab 4 carries citations. Measuring all four against one global % is the architecture conflating the artifacts.
5. **The new gate model rehabilitates the deployed A1.** Replay shows the deployed modules pass the structural gates while failing the current %-gate (false negatives today). That settles the "is the V7 rebuild even needed for A1" question empirically.
6. **B1+ proves the pattern works.** The Lesson Contract already has a structural gate at B1+ (Latin-character ratio ≤1% in body tabs). That gate works and is well-shaped. This proposal extends the same architectural pattern down to A1/A2.

## Why this might NOT be worth doing

1. **Implementation churn.** Splitting `_immersion_gate()` into four functions, extending `IMMERSION_POLICIES` schema, calibrating new thresholds — that's ~1-2 days of focused Codex dispatch work plus a Phase B replay session. Not free.
2. **Threshold calibration risk.** New numeric values must be calibrated empirically. Wrong numbers = either too-permissive (lets bad content through) or too-strict (false-fails good content). Phase B replay against deployed modules + bakeoff artifacts is critical to get values right.
3. **Plan schema change for Gate 4.** Progressive Challenge requires `plan.targets.grammar` / `plan.targets.vocabulary` fields that may not exist in current plan schema. Either accept Gate 4 ships later (Phase A without it) or pay the schema-evolution cost upfront.
4. **Writer prompt rewrite required.** The `rule:` strings in `IMMERSION_POLICIES` are passed to the writer prompt. Under new gates, those strings must change ("TARGET: 15-35% Ukrainian" no longer makes sense). That's Phase C work — a writer-prompt rewrite + likely one new bakeoff to verify the new prompt produces gate-passing content.
5. **Risk of over-engineering.** Four gates is more knobs than one gate. If the new gates are misshapen in different ways than the old one, we might trade one problem for several. The hedge: keep `pct` as advisory telemetry; we can see at any moment whether the new gates and the old metric agree.
6. **Could be subsumed by the writer-split proposal.** The companion proposal `2026-05-13-writer-split-by-tab.md` makes each tab the responsibility of a different agent. If that ships, per-tab gating becomes natural without the unified-gate redesign. The two are independent decisions but the dependency is worth surfacing.

---

## Implementation phases

**Phase A — gate code split + config schema extension** (~half-day Codex dispatch)

- Extend `IMMERSION_POLICIES` band record schema with the new structural fields (placeholder values; Phase B calibrates)
- Add new `AUDIT_THRESHOLDS` keys
- Split `_immersion_gate()` at `linear_pipeline.py:4582-4624` into four functions: `_l2_exposure_floor_gate()`, `_long_uk_ceiling_gate()`, `_component_density_gate()`, `_progressive_challenge_gate()` (latter behind a feature flag if plan.targets isn't ready)
- Keep old `_immersion_gate()` as `_advisory_immersion_pct()` — computes pct, emits telemetry event, never hard-fails
- Markdown heuristics for component detection (Gemini's read): blockquote = dialogue; `:::tip`/`:::note` = callout; bilingual table = vocab; etc.

**Phase B — empirical calibration** (~half-day Codex dispatch, no LLM cost)

- Run new gates against all 55 deployed A1 modules in `_archive/a1-backup-2026-04-08/content/`
- Run against today's bakeoff artifacts (claude + codex)
- Identify false positives / false negatives; tune thresholds in `IMMERSION_POLICIES` band records
- Output: a `audit/immersion-gate-calibration-2026-05-13/REPORT.md` with before/after pass/fail rates per band

**Phase C — writer prompt rewrite** (~half-day Claude-headless dispatch)

- Rewrite `rule:` strings in `IMMERSION_POLICIES` to drop percentage-as-primary-target; replace with structural directives ("≥N UK dialogue lines; no UK-only run >K words without gloss; ensure target grammar/vocab exercised in examples")
- Rewrite the immersion-related portions of `scripts/build/phases/linear-write.md`
- PR #1909's "aim for middle of band" line is reverted; long-sentence rule stays (it's the Gate 2 primitive)

**Phase D — one bakeoff to validate** (~1 hour, one module)

- Run V7 build on `a1/my-morning` with new writer prompt
- Verify new gates pass; verify content quality at least matches prior bakeoff
- If pass: ship. If fail: tune prompt; do not back out the gate change

**Phase E — Lesson Contract §4.6 amendment** (~30 min, doc-only PR)

- Update §4.6 A1/A2 clause to reference the new structural gates instead of "per-band ramp from IMMERSION_POLICIES across all four tabs"
- B1+ clause unchanged

---

## What this DOES NOT change

- **B1+ immersion rule.** Tab 1 / Tab 3 / Tab 4 body remains 100% Ukrainian (Latin-character ratio ≤1%); Tab 2 stays bilingual carve-out. Lesson Contract §4.6 B1+ clause untouched. The B1+ gate is already structural and well-shaped.
- **Decolonization rules** (Lesson Contract §4.7). Orthogonal.
- **VESUM verification.** Orthogonal.
- **Citation roundtrip enforcement.** Orthogonal.
- **Tab 3 activity allowlist** (`activity_repair.py`). Orthogonal.
- **The `MAX_SENTENCE_LENGTH = 25` constant in `scripts/config.py:426`.** Different concern (writer-side sentence-length cap by CEFR), not a gate.

## Open questions for the decider

1. **Should Phase D bakeoff include both claude-tools and codex-tools writers, or just claude-tools (current default)?** If the writer-split proposal is also accepted, this bakeoff becomes a Tab-1-only test (claude only), which is faster and more decisive.
2. **Phase B calibration tolerance — how much false-fail is acceptable?** Strict thresholds risk legitimate-content failures; loose thresholds let bad content through. Suggest: tune for zero false-fails on deployed A1 modules (the empirical baseline), with bakeoff failure mode as the "still-fails" check.
3. **Plan schema change for Gate 4?** Either ship Gate 4 later (after plan schema evolution) or pay the schema cost now. Suggest: ship gates 1-3 in Phase A; Gate 4 follows when plan schema gains `targets` fields.
4. **Should this Decision Card commit to Phase A→E sequencing, or just A→B as proof of concept?** Suggest: Phase A→B is the minimum proof-of-concept; commit to those, defer C→E pending B's results.

## Recommended path forward

1. **Accept this Decision Card** — promotes to ACCEPTED in `docs/decisions/2026-05-13-immersion-gate-tab-aware-structural.md` (out of pending)
2. **Fire Phase A dispatch** (Codex, ~half-day) — extends config + splits gate code
3. **Fire Phase B dispatch** (Codex, ~half-day, no LLM cost) — empirical calibration
4. **Read Phase B report; decide whether to proceed to C-E** in the following session

Total commitment for accepting today: ~1-1.5 days of Codex dispatch work, ~zero LLM-quota burn for the bulk of it (gates are deterministic; calibration is replay).

## Related

- Companion proposal: `2026-05-13-writer-split-by-tab.md` (independent decision; either can ship without the other but they compose well)
- Multi-agent convergence: channel `immersion-reframe-2026-05-13` (Codex + Gemini round 2, both `[AGREE]`)
- Predecessor session-state: `docs/session-state/2026-05-13-afternoon-bakeoff-and-twopass-brief.md`
- Lesson Contract authority: `docs/lesson-contract.md` §4.6
- Empirical grounding: 6 ULP seasons + 5 deployed A1 modules read in session 2026-05-13 evening
- Pipeline-bug companion: PR #1913 (merged, closed #1910/#1911/#1912) — pedagogy-neutral pipeline fixes; orthogonal to this proposal
- Held PR: #1909 (writer-prompt-tune) — should be rebased / partially reverted under this proposal (the "aim for middle of band" line dies; citation parity + section budget + long-sentence rule survive)
