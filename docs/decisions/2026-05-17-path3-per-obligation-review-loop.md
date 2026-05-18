# DECISION REQUIRED — Path 3 architecture: per-obligation review loop for V7 writer

**Status:** PROPOSED — awaiting user sign-off (4-agent consensus on direction + refinements; specific architecture below)
**Surfaced:** 2026-05-17 after m20 build #20 hit wiki_coverage 44% asymptote and PR #2105 regression
**Decision driver:** morning handoff `docs/session-state/2026-05-17-morning-m20-five-fixes-plus-dagger-cleanup.md` named Path 1/2/3; today proved Path 1 prompt-hardening asymptotes at ~50% on strict 18-item manifests; Path 2 violates #1 "no lowering thresholds"; Path 3 is the remaining architectural fix.

---

## TL;DR

All 4 agents voted **NEEDS-REFINEMENT** on the naive Path 3 proposal. Convergent refinements collapse into a single architecture: **deterministic skeleton seeding + `<fixes>`-only reviewer loop with secondary-signal Goodhart mitigation**.

**Recommendation: adopt the refined Path 3 below.** ~4 PRs, 3-5 days focused engineering. The 4-vote consensus makes this a high-confidence architectural call.

---

## Why now

Today's m20 cascade landed 8 PRs (#2094, #2095, #2096, #2097, #2098, #2103, #2104, #2105-reverted) covering every gate-scope and prompt-obedience bug in the V7 single-pass writer. The result:

- python_qg phase passes cleanly (all 20 gates)
- wiki_coverage_gate at **44% (8/18)** — single-pass asymptote
- PR #2105 attempted to push past via stronger prompt — regressed (writer dropped `<plan_reasoning>` blocks under audit overload; reverted on main)

The writer can do the content work. The architecture can't enforce 18-obligation coverage in one pass. Every future module hits the same wall without Path 3.

---

## Cross-agent votes

| Agent | Vote | Distinctive contribution |
|---|---|---|
| Codex | NEEDS-REFINEMENT | `implementation_map.json` MUST become a first-class mutable sidecar. Multi-artifact patch protocol (module.md ≠ activities.yaml patching shape). Staged: batched correction pass first → per-obligation fallback. Long-term: seed deterministic skeletons BEFORE writer ("writer fills slots"). |
| Gemini | NEEDS-REFINEMENT | "Frankenstein patchwork" risk: 10 sequential targeted fixes destroy narrative coherence. Mitigation: "Contextual Integrity Gate" inspects ±5 lines of patch site + adversarial "Pedagogical Substance" check. Alternative proposal: **Path 1.5 Allocation-First** (writer emits allocation manifest BEFORE prose; pipeline validates mapping; writer then executes filled-in slots). Path 3 only as Secondary Rescue if Path 1.5 fails after 2 iterations. |
| Grok | NEEDS-REFINEMENT | **ADR-007 reopens rewrite surface** — "targeted reviewer LLM call" language ambiguous on whether it stays inside `<fixes>`-only contract or slips into section-level synthesis. Must explicitly enforce `<fixes>`-only. Goodhart mitigation: trigger reviewer only when naturalness/citation also drops; cap 2 iterations per obligation; log before/after scores + human-readable rationale in review artifact. Alternative: exhaust Path 1 + two-pass writer with full gate failure report in second invocation. |
| Claude (me, inline) | AGREE-with-refinement | PR #2105 attempt failed because audit requirements crowded out content work in writer prompt. Lesson: per-obligation loop MUST NOT add to writer prompt complexity. Must run AFTER writer phase as a separate pipeline stage. Reviewer model: per Codex's cross-family rule (Claude writer → Gemini reviewer). |

---

## Convergent architecture (synthesis)

### Phase 0 — Deterministic skeleton seeding (Codex + Gemini-Allocation-First)

BEFORE the writer runs, the pipeline:

1. Parses the wiki Obligations Manifest deterministically.
2. Generates an `implementation_map.json` skeleton with one row per obligation:
   - `obligation_id`
   - `artifact` (deterministically picked per type: contrast_pair→activities.yaml, ban→module.md prose, sequence_step→module.md prose, phonetic_rule→module.md prose)
   - `location_hint` (section name from plan)
   - `treatment_template` (per-type schema; for contrast_pair, expects `{sentence, error, correction}` matching manifest's `incorrect`/`correct`)
3. Generates activity stubs in `activities.yaml` with placeholder fields for each contrast_pair obligation.

The writer's job becomes: fill in the deterministic skeleton's slots with substantive prose + dialogue + verbatim manifest values. This is what Codex meant by "writer fills slots instead of inventing coverage structure" and what Gemini meant by Allocation-First.

**Removes from writer prompt:** the 3 audit lines, the IMPLEMENTATION SHAPE explanation, the per-obligation listing burden. Writer prompt shrinks back to ~original ~1500 lines.

### Phase 1 — Writer (unchanged interface)

Same V7 claude-tools writer. Same plan_reasoning protocol (#1673/#1661). Writer fills slots in the deterministic skeleton.

### Phase 2 — wiki_coverage_gate (extended)

Per Codex: gate already verifies per-obligation. Extend output to report **structured `<fix_proposals>`** when failing — each failure has `obligation_id`, `current_artifact_state`, `expected_treatment`, `surgical_diff_hint`. This is the input the Phase 3 reviewer consumes.

### Phase 3 — Batched correction pass (Codex's staged approach)

If wiki_coverage_gate fails:
1. Group failures by `(artifact, obligation_type)`.
2. Single reviewer call per group with all failures + the manifest specs + the current artifact text.
3. Reviewer emits **`<fixes>` block only** — strict ADR-007 contract enforcement (per Grok). NO regeneration. NO section-level synthesis.
4. Pipeline applies fixes deterministically (existing `_apply_writer_correction` infrastructure handles this).
5. Re-run wiki_coverage_gate.

### Phase 4 — Per-obligation fallback (if batched pass leaves failures)

For each remaining failed obligation:
1. Single narrow reviewer call: "obligation X at location Y requires treatment Z. Current state: ABC. Emit `<fixes>` block to satisfy." Strict ADR-007.
2. **Cap at 2 iterations per obligation** (Grok). After cap, emit `plan_revision_request` (defer to next plan iteration) rather than further LLM thrashing.
3. Each `<fixes>` diff capped in size (Grok); each accepted fix logged with before/after gate scores + rationale.

### Corrector contract enforcement

Issue #2127 hardens PR3's `<fixes>`-only contract in both prompt and pipeline
code. Wiki coverage correctors may now emit only local `find`/`replace` fixes
or `insert_after`/`text` insertions, and each replacement/insertion body is
capped at 6 lines and 240 characters. Oversize reviewer fixes are rejected with
`reviewer_fix_oversize_rejected` before any artifact write, which prevents
activity-block regeneration from entering the correction loop.

The artifact writer also validates YAML correction outputs before accepting
them. `activities.yaml`, `vocabulary.yaml`, and `resources.yaml` must remain
bare lists of mappings, required identity fields must stay non-empty strings,
activity `items` must remain lists of mappings, and YAML parser or round-trip
failures are normalized to `LinearPipelineError` so the correction rollback path
emits `wiki_coverage_correction_yaml_invalid` instead of a raw stacktrace.

### Phase 5 — Goodhart sentinel (Gemini + Grok merge)

After Phase 3+4 converge on the deterministic gate, run a **secondary semantic reviewer** (cross-family — Codex if writer was Claude, etc.) that judges "is this obligation woven into the prose, or just keyword-stuffed?" If the gate passes but the semantic reviewer flags "substance missing," fail the build with explicit signal.

### Reviewer model routing

Per existing "reviewer different from writer" rule + Codex/Gemini consensus:
- Phase 3 batched reviewer: **Codex at xhigh** (patch construction is structured editing; Codex's lane)
- Phase 4 per-obligation reviewer: **Codex at high** (same)
- Phase 5 Goodhart sentinel: **Gemini at high** (cross-family; cheaper; lower-stakes adversarial pass)
- Writer phase unchanged: claude-tools (per `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md`)

---

## What this gets us

| Metric | Today (single-pass) | After Path 3-refined |
|---|---|---|
| Single-module wiki_coverage on m20 | 44% asymptote | ≥80% expected (deterministic skeleton + corrective loop) |
| Writer prompt complexity | 2431 lines + 3 audit requirements (caused PR #2105 regression) | ~1500 lines, no audit lines |
| Per-module cost (LLM tokens) | 1× claude-tools writer | 1× claude writer + 1-3× codex reviewer (batched) + 1× gemini Goodhart |
| Reproducibility | Stochastic writer-roll variance | Deterministic skeleton + bounded loop = reproducible coverage |
| ADR-007 compliance | Honored | Honored more strictly (explicit `<fixes>`-only enforcement) |

---

## Risks

1. **Reviewer-loop divergence.** Despite the 2-iteration cap, edge-case modules might oscillate. Mitigation: per-iteration coverage_pct must monotonically improve; if regression, abort and emit `plan_revision_request`.
2. **Skeleton seeding errors.** If the deterministic skeleton mis-categorizes an obligation (e.g., writes a sequence_step to activities.yaml), the writer fills a wrong slot. Mitigation: skeleton seeding is short, deterministic, fully testable. Add a PR0 contract test.
3. **Goodhart sentinel false positives** (Gemini flags substance-missing on actually-substantive content). Mitigation: log Goodhart rejections separately; tune threshold over first 5 modules.
4. **Codex reviewer cost.** Each correction pass burns Codex tokens. Mitigation: most modules will need 0-2 batched calls. Worst-case ceiling: 1 module = ~5 reviewer calls = ~6% Codex 5h-rate-limit (from clawpatch eval data).
5. **m20 ship gap during refactor.** Path 3 takes 3-5 days. During that period m20 doesn't ship. Mitigation: see "Bridge for m20" below.

---

## Bridge for m20 (the immediate problem)

Path 3 takes 3-5 days. m20 has been stuck for 2 days. Options to ship m20 now:

| Option | Effort | Trade-off |
|---|---|---|
| A. **Wait for Path 3 — ship m20 first with Path 3 architecture in place** | 3-5 days delay | Cleanest. m20 becomes the first Path 3 ship. |
| B. **Manual content patch on the working build #20 artifacts** to add the missing 10 obligations | ~1 hour | Violates user's earlier "stop manually editing writer output" direction. NOT recommended. |
| C. **Plan revision: shrink m20's wiki manifest from 18 to ~10 obligations** that the single-pass writer can cover reliably | ~2 hours | Re-frames the goal to match what the writer can do. Honest if pedagogically defensible; risky if it sets a precedent of lowering ambition. |
| D. **Accept 44% coverage as a one-off + ship m20 with explicit note** | 0 hours | Violates #1 "no lowering thresholds" via the back door. Strongly advised against. |

**My recommendation: A.** m20 is the proof-of-pipeline module — better to ship it FIRST under Path 3 architecture (validates the whole stack) than to compromise it via B/C/D. The 3-5 day delay is a one-time investment that unblocks all 1700+ modules.

---

## Implementation plan (4 PRs)

| PR | Scope | Estimated effort |
|---|---|---|
| PR1 | `implementation_map.json` sidecar — schema, deterministic seeder from manifest, contract tests | 0.5-1 day |
| PR2 | wiki_coverage_gate extension to emit `<fix_proposals>` structured output | 0.5 day |
| PR3 | Phase 3 batched correction pass — pipeline wiring + Codex routing + max-iter cap + telemetry | 1-1.5 days |
| PR4 | Phase 5 Goodhart sentinel (Gemini cross-family pass) + before/after coverage logging + m20 replay validation | 1 day |
| (Implicit PR5 if needed) | Activity-skeleton stub generation for contrast_pair obligations | 0.5 day if PR1 doesn't cover it |

Total: **3-5 focused days** (matches Codex + Gemini independent estimates).

---

## Open questions for user sign-off

1. **Adopt this refined Path 3?** Or modify (which sections)?
2. **m20 bridge option:** A (wait for Path 3), B (manual patch — banned per earlier direction), C (plan revision), or D (accept 44%)?
3. **Reviewer routing:** Codex for batched fixes (recommended) or different agent? Gemini for Goodhart (recommended) or different?
4. **Order in queue:** Path 3 vs other backlog (5th-agent integration, clawpatch follow-ups #2099-2102 audit bugs, evidence-layer unification Decision Card)?

---

## Default if no decision

Per the original morning-handoff framing: orchestrator re-raises rather than acting on a default. **Do NOT silently start PR1.** m20 stays at 44% coverage until you sign off the architecture and the m20 bridge option.

---

## Cross-links

- m20 ship cascade: PRs #2094, #2095, #2096, #2097, #2098, #2103, #2104, (#2105 reverted on main)
- Original Path 1/2/3 framing: `docs/session-state/2026-05-17-morning-m20-five-fixes-plus-dagger-cleanup.md` § next_p0
- ADR-007 (reviewer-as-fixer, no regen): `docs/decisions/2026-04-23-rewrite-strategies-kill-or-revert.md`
- Writer selection: `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md`
- Concurrent Decision Card: `docs/decisions/pending/2026-05-17-unified-evidence-layer-DRAFT-synthesis.md` (independent)
- 4-agent vote records: bridge messages #1040 (Gemini), #1041 (Codex), `batch_state/tasks/2106-path3-vote-grok.result` (Grok)
