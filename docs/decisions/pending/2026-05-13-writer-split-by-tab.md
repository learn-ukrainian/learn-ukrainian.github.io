# DECISION REQUIRED — Should we move V7 writer phase to per-tab /goal-driven write-fix-loop, with Gemini reduced to deterministic-tool role?

**Status:** PROPOSED — REVISED 2026-05-13 (orchestrator-rewritten in same conversation after user clarifications)
**Surfaced:** 2026-05-13 evening, user-proposed: *"or we could give diff tabs to diff agents whichever is stronger in that?"* — then refined later same day: *"i wonder if /goal we should use for claude and codex agents? ... after 6 months of struggling i would like to try to goal driven write-fix-loop"*
**Source:** User-stated direction; consistent with existing project patterns (cross-agent split, no self-review, 3:3:3 dispatch by fit); cross-references the empirically-shipped /goal rule (`claude_extensions/rules/goal-driven-runs.md`, codified per #1884, design origin 2026-05-07 OpenAI Codex consult, deployed via Claude Code v2.1.139 native UX 2026-05-11)
**Scope:** V7 pipeline writer phase (`scripts/build/v7_build.py` + `linear_pipeline.py` writer dispatch shape) + reviewer phase becomes LIGHT verification + Tab 4 builder becomes deterministic Python with Gemini-as-lookup-tool. **Does NOT touch:** gate logic (separate accepted card `2026-05-13-immersion-gate-tab-aware-structural.md`), plan schema, MDX assembler. **DOES challenge:** dec-001 / ADR-007 — see §"ADR-007 collision and how this experiment respects it" below.

---

## What's being proposed

Replace V7's monolithic writer-then-reviewer-fix pipeline with **per-tab agents driving their own /goal write-fix-loops**, with the reviewer reduced to a final lightweight verification pass.

| Tab | Artifact | Writer | Mechanism | Why |
|---|---|---|---|---|
| Tab 1 — **Урок** | `module.md` | **Claude** | `claude -p "/goal ..."` headless write-fix-loop | Narrative voice, decolonized framing, MCP verification; /goal-headless native in Claude Code v2.1.139 |
| Tab 2 — **Словник** | `vocabulary.yaml` | **Codex** | Codex /goal write-fix-loop (TUI-driven for PoC; `codex exec` multi-call wrapper once headless surface ships) | Strict YAML schema, VESUM verification, no creative bleed; Codex /goal is the **reference implementation** (origin: 2026-05-07 Codex consult). Tooling gap: no `-p` headless surface yet — TUI/operator-attended for PoC |
| Tab 3 — **Вправи** | `activities.yaml` | **Codex** | Same Codex /goal session as Tab 2 if practical; else separate session | Mechanical type-schema correctness; vocab from Tab 2 informs activity grammar targets — same-session execution captures coherence cheaply |
| Tab 4 — **Ресурси** | `resources.yaml` | **Deterministic Python builder** (NOT an LLM writer) | `scripts/build/tab4_resources_builder.py` (new) — resolves plan refs against project corpus first; falls back to Gemini for URL/source validity check and PD-asset lookup when project-corpus lookup fails | Tab 4 is structured metadata, not creative writing. Gemini becomes a TOOL the builder calls, not a writer of YAML. Reduces cross-agent dispatch count and removes one LLM call per module for routine cases |
| Reviewer | (no longer per-dim LLM emitter) | **Codex** (non-writer) | LIGHT verification — single pass; samples 2-3 of the writer's claimed gate-passes; emits no `<fixes>` block | If reviewer disagrees, /goal session reopens with reviewer's evidence as a new turn — no fix-block, no deterministic application step. The writer fixes its own draft using reviewer evidence. |

The structural shift: **the fix loop moves INSIDE the writer's session**, instead of bouncing artifact-by-artifact across writer→reviewer→fix-applier→re-gate dispatches.

---

## Why this matters NOW

User framing (2026-05-13 evening): *"after 6 months of struggling i would like to try to goal driven write-fix-loop."*

Concrete signals motivating the experiment:

1. **V7's writer-reviewer-fix loop burns quota.** Up to 4 reviewer rounds + 1 writer call per module. On A1 alone (55 modules), that's potentially 275 LLM-calls of reviewer work, much of which iterates on the same dimensions.
2. **The fix-application layer has been a recurring source of bugs.** The 2026-05-13 afternoon "pipeline gate trio" (PR #1913: vesum sentence-exclusion, textbook_grounding parser, immersion display) all lived in the path between reviewer evidence and gate verdict. A pipeline that puts the fix-author in the same context as the original write removes that parser/applier layer's failure surface.
3. **Cross-tab coherence under the original Card 2 framing was a NAMED risk.** Tab 2 vocab must align with Tab 1 prose vocab; Tab 3 activities must exercise Tab 1 grammar. Per-tab same-agent /goal sessions keep coherence implicit within one process.
4. **Reviewer's role mismatched its strength.** Today the reviewer must (a) judge quality AND (b) emit machine-parseable fix blocks. The fix-block requirement is mechanical busywork that throttles the reviewer's judgment quality. Splitting "judge" from "fix" lets the reviewer focus on judgment.

---

## ADR-007 collision and how this experiment respects it

**This proposal directly challenges ADR-007 / dec-001's framing.** That has to be surfaced honestly.

Original ADR-007 rule: "NO LLM regeneration during review. Reviewer outputs `<fixes>` find/replace pairs; pipeline applies deterministically." Empirical basis: Gemini-driven full-rewrites degraded content 9.6 → 8.4 across rounds (a1/colors smoke 2026-04-23 reproduced this).

But ADR-007's empirical evidence is specifically about **REVIEWER-driven FROM-SCRATCH and SECTION rewrites** — a different agent re-authoring text it didn't write. That pattern degraded.

**What hasn't been tested:** writer applying **surgical fixes to its OWN draft** within a single /goal session. Three distinguishing properties:
- **Same agent:** no ghostwriter-rewrites-someone-else's-chapter dynamic; the writer remembers why each choice was made.
- **Surgical edits only:** /goal prompt forbids full-section rewrites; max-words-changed-per-turn cap; writer must emit a `<fix-diff>` block showing exactly what changed.
- **Predicate-driven termination:** loop ends at `GOAL_DONE` (all HARD gates green) or `GOAL_ABORT` (degradation signal, turn cap, or quality regression).

**Experiment hypothesis:** writer-driven surgical self-fix is **a different population than reviewer-driven rewrite**. ADR-007 forbids the latter. Whether it should also forbid the former is what the experiment will tell us.

**Failure clauses:**
- If the experiment shows degradation (score regression between fix-turns, OR worse final score than today's writer-then-reviewer pipeline on the same plan), **ADR-007 stays as-is** and we shelve /goal-driven writers. The struggle continues; no harm done.
- If the experiment validates, **ADR-007 gets refined** with an explicit clause: "writer-driven surgical fixes within a single /goal session are permitted; reviewer-driven full-section and FROM-SCRATCH rewrites remain forbidden." dec-001 stands; the rule's empirical evidence informs but doesn't extrapolate beyond its tested population.

This is not a request to retire ADR-007. It's a request to **measure whether a related-but-untested pattern is also degrading.**

---

## Anti-degradation guardrails baked into the /goal writer prompt

These are LOAD-BEARING. Without them, /goal-driven-writer is just the dec-001 pattern wearing a new hat.

1. **`<fix-diff>` mandatory on every fix turn** — find/replace pairs, same shape the reviewer used to emit pre-ADR-007. No "I rewrote the section to address the gate." The diff is the proof of surgical edit.
2. **Max edit size per turn capped** — e.g. 200 words changed (delete + insert combined) per turn. Larger edits trigger `GOAL_ABORT reason="edit_exceeds_surgical_cap"`. The cap value lives in `scripts/config.py` SSOT, not in the card.
3. **Writer must cite the gate-output line driving each fix.** No "I think this paragraph could be better." Every fix turn references which gate's failure justified it.
4. **`GOAL_STATUS` status line per turn includes** `fix_diff_size=W gate_progress="vesum_verified:pass long_uk_ceiling:fail ..."` so degradation is grep-able and the loop's progress is auditable post-hoc.
5. **Pre-fix score capture** — every fix turn captures the score on the dim it's trying to fix BEFORE editing. If score on ANOTHER dim drops after the fix, `GOAL_ABORT reason="cross_dim_regression"`. Catches the dec-001 pattern (fixing X breaks Y).
6. **Turn cap N=5** — generous but bounded. If the writer can't close all HARD gates in 5 fix turns, `GOAL_ABORT reason="convergence_failure"` and the orchestrator escalates (today's dispatch-and-review path).
7. **Sandbox first.** PoC runs on `a1/my-morning` (today's bakeoff target) in a worktree-isolated branch, NOT on main. Comparison: same plan, same writer model, /goal-loop output vs today's writer-then-reviewer output. Side-by-side judgment by Gemini-as-judge (non-participant) + manual inspection of decolonization-sensitive sections.

These guardrails make the experiment **fail-safe by construction**. The worst that happens is `GOAL_ABORT` early and we waste a few LLM calls.

---

## Architecture detail

### Tab 1 — Claude /goal write-fix-loop

```
claude -p "/goal write a1/my-morning module.md until all HARD gates pass" \
  --max-turns 5 \
  --abort-on cross_dim_regression \
  --status-line-required
```

Writer turn 1: read plan, write module.md, run gates via subprocess (deterministic Python; this IS allowed inside /goal because gates are not LLM-regen, they're verification scripts).

Writer turn 2 (only if gates failed): read gate output, emit `<fix-diff>` block, apply diff, re-run gates, emit `GOAL_STATUS`.

Repeat. Cap 5 turns. `GOAL_DONE` if all HARD green; `GOAL_ABORT` per the guardrails.

### Tab 2 + Tab 3 — Codex /goal write-fix-loop (sequential same-session)

For the PoC, Codex /goal runs in **TUI / operator-attended mode** because `codex exec --headless-goal` doesn't exist on codex-cli 0.130.0 (`codex /goal --help` only hits top-level help; `-p` means `--profile`, not prompt). Acceptable cost for first PoC; you sit at the terminal once. Headless-Codex-/goal wrapper is a follow-up issue if PoC validates.

Tab 2 first (vocab informs Tab 3 grammar targets), Tab 3 in the same session if turn budget permits.

### Tab 4 — Deterministic Python builder

`scripts/build/tab4_resources_builder.py` (new file):

```python
def build_resources_yaml(plan: dict, level: str, slug: str) -> dict:
    refs = plan["references"]
    resources = []
    for ref in refs:
        # 1. Try project corpus first (deterministic resolution)
        if local_path := corpus_lookup(ref):
            resources.append({"ref": ref, "source": "project_corpus", "path": local_path})
            continue
        # 2. Fall back to Gemini (validity check + PD-asset lookup)
        if gemini_result := gemini_validate(ref):
            resources.append({"ref": ref, **gemini_result})
            continue
        # 3. Unresolved — mark for human triage
        resources.append({"ref": ref, "status": "unresolved", "reason": "..."})
    return {"resources": resources, "level": level, "slug": slug}
```

Gemini calls happen ONLY when corpus lookup fails. For modules with all-corpus-resolvable refs (most A1), Tab 4 is 100% deterministic — zero LLM cost.

### Reviewer — LIGHT verification (Codex, non-writer)

Single pass after writer's `GOAL_DONE`. Reviewer:
- Reads writer's `GOAL_STATUS` history
- Samples 2-3 of the writer's claimed gate-passes (e.g. re-runs textbook_grounding on the final module.md to verify the writer's last reported `passed=true` is honest)
- Emits a verdict (`HONEST` or `DISAGREE` with evidence pointer)

If `DISAGREE`: the /goal session reopens with reviewer's evidence as a new turn. NO fix-block. Writer fixes its own draft with that evidence. (This is the only path where a /goal-driven writer can run past 5 turns — reopened by reviewer evidence.)

---

## Cost math (per module, typical)

| Path | LLM calls | When cheaper |
|---|---|---|
| V7 today | 1 writer + 1-4 reviewer rounds (avg ~2 typically) = **2-5 calls** | Baseline |
| /goal-driven writer + light reviewer | K writer turns (1-5) + 1 reviewer = **2-6 calls** | If `K=1` (first-write passes all gates) — cheaper. If `K=5` (writer flails) — comparable or worse. |

Plausibly cheaper because: same-agent same-context fix-application converges faster than cross-agent round-trips. Plausibly worse because: writer's defensive bias means it under-recognizes its own failures. **Experiment tells us which.**

Bonus: today's path requires reviewer-emitted-fix to be PARSEABLE by deterministic applier. Parse failures (`reviewer_fixes_unparseable`, `reviewer_fixes_anchor_unmatched`) waste a whole reviewer round. /goal-driven path eliminates this failure surface entirely — the writer's surgical edit either applies or it errors immediately in the same turn.

---

## Risks

1. **ADR-007 collision.** Mitigated by the guardrails above + scoped PoC + explicit rollback to today's pipeline.
2. **Codex headless /goal gap.** Today's Codex /goal is TUI-only. PoC runs operator-attended; production rollout needs a headless wrapper OR a Codex CLI feature addition. File follow-up issue.
3. **Tab 4 builder is new code.** ~200-400 LOC; pilot before A1 batch; deterministic so testable.
4. **Reviewer's role change.** Today reviewer emits fix-blocks. Tomorrow reviewer judges only. Existing reviewer prompts in `scripts/build/phases/linear-review-dim.md` need rewrite. ~half-day Codex dispatch.
5. **Writer-defensive bias risk.** A writer reviewing its own draft might rationalize failures rather than fix them. Guardrail #5 (cross-dim regression abort) catches the worst case; the empirical bakeoff against today's pipeline is the broader check.
6. **Existing infrastructure assumes writer-reviewer-fix shape.** Status JSON schema, audit JSON shape, prompt templates, gate parsers — all written for the old shape. Card 2-REVISED implementation is a structural pipeline change, ~2-3 days of focused dispatch work, NOT a tweak.

---

## Implementation paths

### PoC first (recommended start)

**Wall-clock budget:** ~2 hours operator-attended + ~10 LLM calls total.

1. Pick target: `a1/my-morning` (matches today's bakeoff for direct comparison).
2. Pre-write the /goal prompt for Tab 1 (Claude) including all guardrails.
3. Run `claude -p "/goal ..."` once; capture full transcript + `GOAL_STATUS` lines + final module.md.
4. Open Codex TUI; run /goal for Tab 2 + Tab 3 sequentially in one session.
5. Run deterministic Tab 4 builder (write it first if it doesn't exist yet; ~half-day Codex dispatch beforehand).
6. Light reviewer pass via Codex.
7. **Compare** side-by-side to today's monolithic claude bakeoff output (`audit/bakeoff-2026-05-13-midday/claude/`):
   - Gemini-as-judge writes a comparison report
   - Manual inspection of decolonization-sensitive sections
   - Score deltas per dim
   - Total LLM-call count
8. Verdict:
   - **Equal-or-better quality + lower-or-equal cost** → ADR-007 refinement card filed; invest in headless Codex wrapper + reviewer prompt rewrite + pipeline orchestration changes
   - **Worse quality OR higher cost** → shelve; ADR-007 stays; per-tab split with monolithic agents falls back to Path A from original Card 2

### If PoC validates: production rollout

Phase 1 — ADR-007 refinement card (proposed amendment text in PoC verdict)
Phase 2 — Headless Codex /goal wrapper (or upstream feature request to Codex CLI team)
Phase 3 — Tab 4 deterministic builder (production version)
Phase 4 — Reviewer prompt rewrite (judge-only, no fix-block)
Phase 5 — Pipeline orchestration changes in `v7_build.py` + `linear_pipeline.py`
Phase 6 — Single-module validation bakeoff under new pipeline
Phase 7 — A1 batch build

Total: ~1-2 weeks of focused dispatch work after PoC verdict.

---

## What this DOES NOT change

- **Gate logic** — Card 1 (immersion-gate-tab-aware-structural) phases A/B/C/D/E proceed independently.
- **Plan schema** — orthogonal.
- **MDX assembler** — orthogonal.
- **Cross-agent self-review prohibition** — strictly preserved. Reviewer is still Codex (non-writer for Tab 1) for the LIGHT pass.
- **VESUM verification gate** — non-negotiable; the writer's /goal loop runs it as one of the HARD gates.
- **Decolonization rules** (Lesson Contract §4.7) — orthogonal; writer prompt includes them.

---

## Open questions for the decider

1. **Acceptable to run PoC operator-attended?** Codex /goal headless surface is missing; PoC requires you sitting at a terminal for Tab 2/3. Recommend: **yes for PoC**, file headless surface as production-rollout prerequisite.
2. **Gemini deterministic-first OR Gemini-on-every-resource for Tab 4?** Default in this card: **deterministic-first, Gemini-as-fallback** — corpus lookup tried first, Gemini called only on unresolved refs. Reason: most A1 references are project-corpus resolvable; calling Gemini on every ref wastes calls. Override if you want uniform Gemini-on-each.
3. **Should the reviewer also be /goal-driven?** Card defaults to **NO** for the PoC — keep reviewer as a single non-iterating pass. Adding /goal-driven reviewer would compound experimental variables. Revisit after writer /goal validates.
4. **PoC scope — one module or multiple?** Recommend **one module first** (`a1/my-morning`). If signal is mixed, run a second on a structurally different module (e.g. `a1/sounds-letters-and-hello` is foundational; `a1/when-and-where` is m45 complex sentences). Don't bulk-PoC.
5. **Comparison baseline:** today's `audit/bakeoff-2026-05-13-midday/claude/` (monolithic claude bakeoff). Or do we want a fresh comparison run under today's pipeline as the control? Recommend: **use the existing bakeoff as control** — saves an LLM call; the artifact is already audited.

## Recommended path forward

1. **Accept this revised Card 2** — promotes to ACCEPTED in `docs/decisions/2026-05-13-writer-split-by-tab.md`.
2. **Defer PoC until Phase B (Card 1) replay results land.** Phase B's verdict on "is V7 rebuild for A1 even needed?" changes what we'd PoC. If Phase B says "deployed A1 passes new gates" → PoC scope narrows to A2 + future levels. If Phase B says "deployed A1 fails new gates" → PoC stays on A1.
3. **Pre-PoC prep work** (parallel-able with Phase B replay): draft the /goal writer prompt with guardrails + draft the Tab 4 deterministic builder spec. Both are LLM-quota-free.
4. **PoC execution** (operator-attended, ~2 hours): runs after Phase B verdict + pre-PoC prep.
5. **PoC verdict drives** either ADR-007 refinement + production rollout (8-12 work-days) OR shelve + fall back to original Card 2 Path A.

Total commitment for ACCEPTING today: ~0 immediate dispatch work; ~2 hours of operator-attended PoC after Phase B; pre-PoC prep can happen in parallel with Phase B and is dispatchable.

---

## Related

- Companion card (ACCEPTED today): `docs/decisions/2026-05-13-immersion-gate-tab-aware-structural.md`
- Predecessor session-state: `docs/session-state/2026-05-13-evening-immersion-reframe-and-writer-split-brief.md`
- Original Card 2 framing (now superseded by this revision; git history): commit `55823800ce` first version of this file
- ADR being challenged: `docs/decisions/2026-04-23-rewrite-strategies-kill-or-revert.md` (ADR-007) + `decisions.yaml` dec-001
- /goal rule: `claude_extensions/rules/goal-driven-runs.md` (origin: 2026-05-07 Codex consult; codified #1884)
- Existing writer-selection card (will need REVISED-AGAIN after PoC verdict): `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md`
- Bakeoff control for PoC comparison: `audit/bakeoff-2026-05-13-midday/claude/`
- Holding pattern PR #1909 (writer-prompt-tune): under THIS proposal, the writer prompt changes more radically than #1909's edits; either rebase #1909 onto the new prompt OR drop it. Likely DROP if PoC validates; the new prompt incorporates the durable parts (citation parity, section budget, long-sentence rule) by design
- Holding pattern PR #1915 (Track B): the two-pass workflow it tested is structurally similar to /goal-driven multi-pass; its YELLOW verdict gets re-evaluated under the new framing — possibly REVIVE if /goal-driven validates
