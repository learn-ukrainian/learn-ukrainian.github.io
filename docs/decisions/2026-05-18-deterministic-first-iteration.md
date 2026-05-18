# SYNTHESIS — Deterministic-first iteration as the V7 correction pattern

**Status:** SYNTHESIS — not a new decision card. Composes existing accepted decisions into a single pattern description.
**Date:** 2026-05-18
**Surfaced by:** `audit/2026-05-18-docs-gaps-and-reorganization/REPORT.md` §1.5 — the "what to do INSTEAD of the broken review-fix loop" had no documented shape, even though the pieces were all locked in prior decision cards. This file is the missing map.
**Audience:** any agent (or human) trying to understand "what pattern do V7 corrections follow, end-to-end?" without re-reading four decision cards.
**Scope:** V7 pipeline correction behavior — applies to writer phase, Python QG, LLM QG, wiki coverage gate, and per-obligation correction loops. Does NOT apply to plan generation, research phase, or wiki compilation (those have their own contracts).

---

## TL;DR

The V7 pipeline's correction behavior is **deterministic-first**: every correction surface is constrained to the cheapest mechanism that still solves the failure class. LLM regeneration is reserved as the last-resort for the truly open question ("is this pedagogically sound?"), and even then it operates under tight `<fixes>`-only contracts.

This is NOT a new decision. It is a SYNTHESIS of four already-accepted decisions that, read together, form a single pattern:

| Layer | Mechanism | Decision card |
|---|---|---|
| **L1. Pre-write skeleton** | Deterministic seeder pre-fills the implementation map from the manifest. Writer fills slots, doesn't invent structure. | [Path 3 / 2026-05-17-path3-per-obligation-review-loop.md](2026-05-17-path3-per-obligation-review-loop.md) — Phase 0 |
| **L2. Post-write gates** | Deterministic Python QG enforces structural / lexical / immersion contracts. Gate verdicts are structured outputs (`fix_proposals`, not prose). | ADR-007 + ADR-008 |
| **L3. Per-gate correction** | Per-gate correction path with four hard constraints: patch-bounded, full revalidation, pipeline-assisted dictionary, one attempt per gate. Writer redispatch is **append/insert-only**. | ADR-008 / [2026-04-28-targeted-gate-correction-paths.md](2026-04-28-targeted-gate-correction-paths.md) |
| **L4. Reviewer as fixer** | Reviewer emits `<fixes>` find/replace blocks ONLY — no regeneration, no rewriting. Max 2 fix rounds. Score must monotonically increase. | dec-001 (2026-03-24) + ADR-007 / [2026-04-23-rewrite-strategies-kill-or-revert.md](2026-04-23-rewrite-strategies-kill-or-revert.md) |
| **L5. Per-obligation loop** | If wiki_coverage_gate fails: batched correction pass first → narrow per-obligation pass → cap at 2 iterations per obligation → `plan_revision_request` terminal if cap hit. Each `<fixes>` size-capped. | Path 3 Phases 3-4 |
| **L6. Goodhart sentinel** | After deterministic gates converge, a cross-family semantic reviewer judges whether obligations are *substantively* woven into prose or merely keyword-stuffed. Cross-family routing required (Codex reviewer for Claude writer, etc.). | Path 3 Phase 5 |
| **L7. Plan revision terminal** | When the above ladder doesn't converge, the pipeline emits `plan_revision_request` — an honest signal that the plan or the writer is under-specified — instead of further LLM thrashing. | ADR-007 (`tier-5 terminal`) + ADR-008 (`previously_passed_regression` meta-gate) |

The pattern's discipline: **never use an LLM where deterministic logic suffices, never regenerate where a patch suffices, never thrash where a terminal is more honest.**

---

## Why this pattern (the empirical justification chain)

The pattern is anchored in three empirical observations from V5/V6:

1. **2026-03-24 (dec-001):** Gemini measured 9.6 → 9.2 → 8.4 across three FROM-SCRATCH rewrite rounds on the same module. Rewrites *destroyed converged work*.
2. **2026-04-23 (ADR-007 trigger):** `a1/colors` regressed via `full_rewrite` after the `<fixes>` block had already corrected the flag-color hallucination. Live-fire validation of (1).
3. **2026-05-17 (Path 3 trigger):** m20 build #20 hit a 44% wiki_coverage asymptote under single-pass writer. PR #2105 attempted to push past via stronger prompt and *dropped `<plan_reasoning>` blocks under audit overload* — regressed and was reverted on main.

The trajectory across these three: every time we asked an LLM to *re-solve a problem the deterministic layer hadn't already framed*, the result was worse than the patch we had in hand. The pattern documents the corollary: framing has to happen deterministically; the LLM only fills in the residual.

---

## The pattern, end-to-end

### L1 — Pre-write skeleton seeding

**Source:** Path 3 Phase 0 (2026-05-17 decision card).

**Mechanism:** Before the writer phase runs, the pipeline:

1. Parses the wiki Obligations Manifest deterministically.
2. Generates `implementation_map.json` skeleton — one row per obligation with `obligation_id`, `artifact` (deterministic per type), `location_hint` (section name from plan), `treatment_template` (per-type schema).
3. Generates activity stubs in `activities.yaml` with placeholder fields for each `contrast_pair` obligation.

**Effect on the writer:** the writer's prompt no longer contains *"list every obligation_id in `<implementation_map>`"* (the metadata-only requirement that fails today on m20). Instead the writer fills in the deterministic skeleton's slots. The translation step *(obligation → emission)* is pre-resolved by the seeder, eliminating the failure point on m20 build #7.

**Status of implementation:** seeder shipped via PR #2108 (2026-05-17). The gate (L2) already consumes the sidecar. The missing piece is the *writer-side render hook* — that's the open question in [2026-05-18-wiki-obligation-emission-contract.md](pending/2026-05-18-wiki-obligation-emission-contract.md) (DRAFT). This synthesis doc is therefore *partially shipped*: L1 reads side done, L1 writer side pending γ-shape decision.

---

### L2 — Deterministic post-write gates

**Source:** ADR-007 + ADR-008. Implementation at `scripts/build/linear_pipeline.py` (Python QG phase).

**Mechanism:** After the writer phase completes, Python QG runs a fixed list of gates against the produced artifacts (`module.md`, `activities.yaml`, `vocabulary.yaml`, `resources.yaml`). All gates are deterministic; none call an LLM.

**Per-gate verdict shape:** structured output (`fix_proposals` with `obligation_id`, `current_artifact_state`, `expected_treatment`, `surgical_diff_hint`) — not prose. This shape is what L3 consumes.

**Categories of gate today:**

- **Structural:** `strict_json_parse`, `plan_sections`, `word_count`, `formatting_standards`, `mdx_render`, `component_props`, `inject_activity_ids`, `activity_schema`, `yaml_activities`
- **Lexical:** `vesum_verified`, `russianisms_clean`, `surzhyk_clean`, `calques_clean`, `paronym_clean`, `ai_slop_clean`
- **Citation:** `citations_resolve`, `textbook_grounding`
- **Wiki coverage:** `wiki_coverage_gate` (per-obligation row-by-row check against `implementation_map.json`)
- **Immersion:** `l2_exposure_floor_gate`, `long_uk_ceiling_gate`, `component_density_gate` (the Card 1 Phase A split — three structural sub-gates from the former monolithic `_immersion_gate`)
- **Regression:** `previously_passed_regression` (meta-gate; terminals if any prior-passing gate now fails after correction)

**Key discipline:** every gate that *can* be deterministic *must* be. Adding a gate that calls an LLM during Python QG is an architectural violation of this pattern.

---

### L3 — Per-gate correction with four hard constraints

**Source:** ADR-008 (refines ADR-007 without superseding it).

**The four constraints** (ALL must hold for every correction surface):

1. **Patch-bounded.** Writer corrective redispatch is **append / insert-only**. The prompt template includes previously-passing prose verbatim. Forbidden phrases: "regenerate", "rewrite", "produce again", "start over".
2. **Full revalidation.** After ANY correction, ALL Python QG gates re-run — not just the failed one. The `previously_passed_regression` meta-gate terminals if any prior-passing gate now fails.
3. **Pipeline-assisted dictionary.** For lexical gates, the *pipeline* performs deterministic dictionary lookup against VESUM / Антоненко-Давидович / sources registry and proposes verified replacement candidates. The *reviewer* selects among proposed candidates and emits `<fixes>`. The reviewer does NOT invent replacements.
4. **One attempt per gate.** Each Python QG gate gets ONE correction attempt. If correction fails verification, the build terminals with a structured diagnostic. No tier escalation, no second-strategy fallback.

**Per-gate correction-path matrix** (see ADR-008 §"Per-gate correction paths" for the full table):

| Failure class | Mechanism | Cognition |
|---|---|---|
| `strict_json_parse`, `word_count`, `plan_sections`, `formatting_standards`, `mdx_render` | corrective writer redispatch with structured feedback | writer (append-only) |
| `vesum_verified`, russianisms / surzhyk / calques / paronyms | reviewer `<fixes>` + pipeline-proposed candidates | reviewer (selects only) |
| `citations_resolve` | reviewer `<fixes>` + pipeline-proposed from sources registry | reviewer (selects only) |
| `inject_activity_ids` | deterministic pipeline insert | **none** (no LLM call) |
| `component_props` | terminal (zero retry — schema-fault, not content-fault) | none |
| `previously_passed_regression` | terminal (regression guard) | none |

---

### L4 — Reviewer as fixer (LLM QG)

**Source:** dec-001 (2026-03-24) + ADR-007.

**Mechanism:** LLM QG is the only LLM-invoking layer in V7's correction path. It runs after L3 has converged and emits `<fixes>` find/replace blocks against the artifact. Strict ADR-007 contract:

- Output is `<fixes>` ONLY — no `<rewrite>`, no section regeneration, no synthesis
- Max 2 fix rounds per dim
- Per-iteration coverage_pct must monotonically improve; if regression, abort
- `<fixes>` find/replace bodies size-capped (per #2127: 6 lines, 240 characters)

**Reviewer dim model** (see [`docs/decisions/2026-04-26-llm-qg-per-dim-thresholds.md`](2026-04-26-llm-qg-per-dim-thresholds.md)): asymmetric per-dim review tools — only `naturalness` and `decolonization` get server-side retrieval bundles, the rest are score-only.

**Cross-family routing** is mandatory: if the writer was Claude, the reviewer is Codex (or vice-versa). Same-family writer ↔ reviewer is forbidden.

---

### L5 — Per-obligation loop (wiki coverage path)

**Source:** Path 3 Phases 3-4 (2026-05-17 decision card).

If `wiki_coverage_gate` fails, the loop is:

1. **Batched correction pass.** Group failures by `(artifact, obligation_type)`. Single reviewer call per group with all failures + manifest specs + current artifact text. Reviewer emits `<fixes>` ONLY (strict L4 contract). Pipeline applies fixes deterministically via existing `_apply_writer_correction`. Re-run wiki_coverage_gate.
2. **Per-obligation fallback** (if batched leaves failures). For each remaining failed obligation: single narrow reviewer call: *"obligation X at location Y requires treatment Z. Current state: ABC. Emit `<fixes>` to satisfy."* Cap at 2 iterations per obligation.
3. **Terminal escape.** After cap, emit `plan_revision_request` (defer to next plan iteration) rather than further LLM thrashing.

**Reviewer model routing for this path** (per Path 3 §"Reviewer model routing"):

- Phase 3 batched reviewer: Codex at xhigh (structured editing)
- Phase 4 per-obligation reviewer: Codex at high (same lane)
- Writer phase unchanged: claude-tools (per `2026-05-06-writer-selection-codex-gpt55.md`)

**Corrector contract enforcement** (PR #2117 + #2127):

- Wiki coverage correctors emit only local `find`/`replace` fixes or `insert_after`/`text` insertions
- Each replacement / insertion body capped at 6 lines, 240 characters
- Oversize fixes rejected with `reviewer_fix_oversize_rejected` BEFORE artifact write
- YAML correction outputs validated before acceptance — required identity fields stay non-empty, `items` remain lists of mappings, parser/round-trip failures normalize to `LinearPipelineError` so the rollback path emits `wiki_coverage_correction_yaml_invalid`

---

### L6 — Goodhart sentinel

**Source:** Path 3 Phase 5 (2026-05-17 decision card).

**Why:** the deterministic gate enforces row-by-row coverage, but rows can be satisfied by keyword-stuffing without pedagogical substance. The Goodhart sentinel is a secondary semantic reviewer (cross-family from the writer) that judges *"is this obligation woven into the prose, or just keyword-stuffed?"*

**Mechanism:** after L3+L5 converge on the deterministic gate, run the sentinel. If the gate passes but the sentinel flags "substance missing," fail the build with explicit signal.

**Routing:** Gemini at high — cross-family from the Claude writer, cheaper than Codex, lower-stakes adversarial pass.

**Status:** filed as Path 3 PR4. Implementation pending (as of 2026-05-18). NOT YET LIVE.

---

### L7 — Plan revision terminal

**Source:** ADR-007 (tier-5 terminal) + ADR-008 (`previously_passed_regression` meta-gate).

When the L1-L6 ladder doesn't converge, the pipeline emits a `plan_revision_request` terminal — an honest signal that the plan or the writer prompt is under-specified — instead of further LLM thrashing.

**Discipline:** *"plan_revision_request"* is not a failure of the pipeline. It's the pipeline correctly refusing to fake convergence. The mature response to a `plan_revision_request` is to fix the plan (or the writer prompt's per-obligation guidance), then rebuild. NOT to lower thresholds, NOT to revive a tier-2 rewrite strategy, NOT to admin-bypass the gate.

The 2026-04-23 `a1/colors` build is the canonical instance: when `full_rewrite` (a tier-2 strategy) was killed and the build terminated honestly, the lesson learned was "the writer prompt is under-specified for the colors plan," not "we need a rewrite ladder."

---

## What this pattern is NOT

This list exists because the pattern's discipline is *negative* — it forbids a lot. Re-reading these prevents drift back to V5/V6 patterns.

- **Not** "LLM reviewer for everything" — deterministic checks come first, LLM only for the residual.
- **Not** "tiered escalation" — every correction is a single targeted shot. Tiers were killed in ADR-007.
- **Not** "rewrite on REVISE" — `<fixes>` find/replace ONLY, ever. ADR-007 §4 forbids the alternative.
- **Not** "human triage" — the pattern is designed for autonomous correction in fan-out batches. The user has stated explicitly (2026-04-28): *"human triage is not feasible we have to be able to fix detected errors and mistakes."*
- **Not** "more LLM iterations until it passes" — iteration is capped (2 per gate, 2 per obligation, 2 per dim). Cap-hit emits a terminal, not another attempt.
- **Not** "lower the threshold" — quality bars are non-negotiable per `#1` and `non-negotiable-rules.md`. The mature failure mode is `plan_revision_request`, not threshold relaxation.

---

## Where to read more, by topic

| Question | Read |
|---|---|
| Why no FROM-SCRATCH rewrites? | `dec-001` (2026-03-24) — empirical 9.6 → 8.4 evidence |
| What exactly got killed in ADR-007? | [`2026-04-23-rewrite-strategies-kill-or-revert.md`](2026-04-23-rewrite-strategies-kill-or-revert.md) §"Rewrite-mechanism inventory" — 7 call sites in 2 loops |
| How does each gate get corrected? | [`2026-04-28-targeted-gate-correction-paths.md`](2026-04-28-targeted-gate-correction-paths.md) §"Per-gate correction paths" — full table |
| What are the four hard constraints? | ADR-008 §"Hard constraints" |
| How does the wiki coverage loop work? | [`2026-05-17-path3-per-obligation-review-loop.md`](2026-05-17-path3-per-obligation-review-loop.md) §"Convergent architecture" |
| What's the per-iteration coverage discipline? | Path 3 §"Risks" #1 — monotonic improvement; regression aborts |
| How does the writer get the implementation map today? | [PENDING] [`pending/2026-05-18-wiki-obligation-emission-contract.md`](pending/2026-05-18-wiki-obligation-emission-contract.md) — the γ-shape decision is the gap |
| When does the pipeline terminate honestly vs retry? | ADR-008 §"Per-gate correction paths" + ADR-007 §"Decision" |
| Per-dim LLM QG behavior? | [`2026-04-26-llm-qg-per-dim-thresholds.md`](2026-04-26-llm-qg-per-dim-thresholds.md) |
| Goodhart sentinel routing? | Path 3 Phase 5 + §"Reviewer model routing" |

---

## Implementation status checklist (as of 2026-05-18)

| Layer | Status | Notes |
|---|---|---|
| L1 — Pre-write skeleton seeder | **SHIPPED** (PR #2108) | Gate consumes sidecar. Writer doesn't see it yet. |
| L1 — Writer-side render hook for the seeded contract | **PENDING** | Open question γ in [`pending/2026-05-18-wiki-obligation-emission-contract.md`](pending/2026-05-18-wiki-obligation-emission-contract.md) |
| L2 — Deterministic Python QG | **SHIPPED** | 20+ gates across structural / lexical / citation / immersion / regression |
| L3 — Per-gate correction with 4 constraints | **SHIPPED** | ADR-008 implementation via PR #1636 |
| L4 — Reviewer as fixer (LLM QG) | **SHIPPED** | dec-001 + ADR-007 + #2127 corrector contract |
| L5 — Per-obligation loop (wiki_coverage) | **SHIPPED** | Path 3 PR1 #2108 + PR2 #2117 |
| L6 — Goodhart sentinel | **PENDING** | Filed as Path 3 PR4 |
| L7 — Plan revision terminal | **SHIPPED** | ADR-007 tier-5 + ADR-008 regression guard |

When all rows say SHIPPED, the deterministic-first pattern is fully realized in V7.

---

## Cross-links

- dec-001 (origin of reviewer-as-fixer): `docs/decisions/decisions.yaml:14-32`
- ADR-007 (kill the rewrite ladder): `docs/decisions/2026-04-23-rewrite-strategies-kill-or-revert.md`
- ADR-008 (per-gate correction paths): `docs/decisions/2026-04-28-targeted-gate-correction-paths.md`
- Path 3 (per-obligation review loop): `docs/decisions/2026-05-17-path3-per-obligation-review-loop.md`
- Immersion gate split (Card 1 Phase A): `docs/decisions/2026-05-13-immersion-gate-tab-aware-structural.md`
- LLM QG per-dim thresholds: `docs/decisions/2026-04-26-llm-qg-per-dim-thresholds.md`
- Wiki obligation emission contract (DRAFT γ): `docs/decisions/pending/2026-05-18-wiki-obligation-emission-contract.md`
- Documentation gap that surfaced this synthesis: `audit/2026-05-18-docs-gaps-and-reorganization/REPORT.md` §1.5
- Non-negotiable quality rules: `claude_extensions/rules/non-negotiable-rules.md`
- Pipeline rule: `claude_extensions/rules/pipeline.md`
