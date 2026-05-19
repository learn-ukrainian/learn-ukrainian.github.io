# RESOLVED — Wiki obligation emission contract for V7 writer (#2148)

**Status:** RESOLVED 2026-05-19 — User approved γ + bridge A. Implementation shipped via PR #2153 (`5ac671a1b5`). m20 build #8 follows under the new contract.
**Original status:** DRAFT — awaiting user sign-off (3 fix shapes scoped; γ recommended after codex consultation)
**Surfaced:** 2026-05-18 — m20 build #7 reached wiki_coverage_gate at **22.22% (4 / 18 obligations)**, hard-failed at `min_pct=80%` after batched + narrow correction passes converged (one regression to 5.56% before recovering to 22%)
**Scope (BLOCKING):** A1 m20 ship + every future module build with a wiki manifest. Does NOT block tech-debt PRs that don't touch the writer prompt or the obligation emission path.
**Issue:** #2148 (HIGH severity, architectural)

---

## TL;DR

The Path 3 architecture (#2117 / #2123-2125) added **gate-side per-type validation** of wiki obligations but never gave the writer a corresponding **emission-side contract**. The writer prompt enforces a *manifest-listing* requirement ("list every `obligation_id` in `<implementation_map>`") at the metadata layer; the gate enforces an *artifact-emission* requirement (the `<sequence_claim>` marker, the `contrast_pair` item in `activities.yaml`, the banned-word replacement in module prose) at the artifact layer. The writer satisfies the metadata but not the artifact contract.

Three fix shapes on the table. **Recommend γ** — render the existing deterministic `seed_implementation_map` into the writer prompt as `IMPLEMENTATION_MAP_CONTRACT`. Cheapest correct fix; reuses infrastructure already shipped in #2108.

---

## Why now

m20 has been the proof-of-pipeline module since 2026-05-12. Today's cascade landed 4 tech-debt fixes (#2128 vesum bad-marker, #1969 multimedia pre-emit, #2127 corrector fix-shape, #2137 corrector insert_after). All passed. python_qg passes 21 / 23 gates clean — writer phase emits 19 tool calls, 0 theatre violations, 4 / 4 sections with CoT.

The remaining gap is structural and reproduces on **every** module build. Every module has 10-20+ obligations from its wiki_manifest. Without a writer-side emission contract the asymptote stays at ~20-50% for any module the manifest pushes past trivial cases.

This is the next architectural gap behind Path 3.

---

## The diagnostic, by obligation type (from m20 build #7)

| Obligation type | Count | Pass / fail | Failure reason |
|---|---|---|---|
| `sequence_step` | 5 | 1 / 4 | `sequence_claim_missing` — writer doesn't emit `<sequence_claim id="step-N" artifact="module.md" location="..." treatment="..." />` for steps 1, 2, 4, 5 |
| `phonetic_rule` | 3 | 3 / 0 | (passes — IPA convention is in writer prompt) |
| `l2_error` | 6 | 0 / 6 | 3× `unknown_artifact` + 3× `contrast_pair_not_in_activity` — writer doesn't include error-correction activities with the predefined contrast pairs |
| `decolonization_ban` | 4 | 0 / 4 | `ban_substance_missing` — writer doesn't replace the 4 Russian-borrowed words with their canonical Ukrainian replacements |

Only `phonetic_rule` passes — because the writer prompt already has explicit IPA-notation guidance (#1924 fix). The other three types have **no per-type emission rule** in the writer prompt.

Build artifacts preserved at `.worktrees/builds/a1-my-morning-20260518-084111/`:

- `wiki_coverage_gate.json` — full gate report with 14 `fix_proposals`
- `writer_prompt.md` — current writer prompt (with obligation directives)
- `writer_output.raw.md` — what the writer produced
- `wiki_manifest.json` — the 18 obligations the writer should have satisfied

---

## Three fix shapes

### α — Manifest builder injects `required_tokens` + `expected_artifact` (upstream)

`scripts/build/phases/wiki_manifest.py` already emits per-obligation rows. Extend each row with two new fields:

- `required_tokens: [<token1>, <token2>, ...]` — verbatim strings that MUST appear in the artifact (e.g., the canonical replacement word for `decolonization_ban`, the contrast pair's `error` + `correction` for `l2_error`)
- `expected_artifact: <path>` — deterministic per type (`activities.yaml` for `l2_error`, `module.md` for `sequence_step` / `decolonization_ban`)

Then the writer prompt instructs: *"For each obligation in the manifest, copy its `required_tokens` into the `expected_artifact` location."*

**Pros:** moves the contract upstream where it can be programmatically verified before the writer even runs. Tightest coupling between manifest semantics and writer instructions.

**Cons:**
- Requires schema migration on `wiki_manifest.json` (existing modules with materialized manifests need re-generation)
- The "verbatim token" model breaks down for sequence_step where the writer needs to construct a `<sequence_claim>` marker with `id` / `artifact` / `location` / `treatment` attributes — those aren't a free-form token list
- Most invasive change of the three; highest blast radius if the new schema interacts poorly with reviewers / correctors / Goodhart sentinel

---

### β — Per-type emission templates in writer prompt (downstream)

Update `scripts/build/phases/linear-write.md` with worked-example emission templates per obligation type. The issue #2148 body has the exact templates:

```
sequence_step → <sequence_claim id="step-N" artifact="module.md" location="§<section> ¶<para>" treatment="<summary>" />
l2_error      → activities.yaml entry: error-correction items with sentence/error/correction matching the obligation contrast_pair
decolonization_ban → "Use **<canonical UA word>** (not the Russian-borrowed <banned word>)." with banned word in <!-- bad -->...<!-- /bad --> markers per #2128
```

Add a "Pre-emit obligation check" near end of prompt mirroring #1969's checklist: *"For each obligation in the manifest, confirm the required marker / item / replacement is present in your output."*

**Pros:** simplest change. Touches one file (`linear-write.md`). No schema migration. Worked examples are concrete and learnable.

**Cons:**
- Adds 60-120 LOC to the writer prompt at a time when prompt complexity is already near the threshold that caused PR #2105 regression
- Static templates — every obligation looks the same to the writer; no manifest-specific guidance per row
- Writer still has to *read* the manifest and *translate* each obligation to the right template by type. Translation step is the failure point we're trying to remove.

---

### γ — Render existing `seed_implementation_map` into prompt (middle) — RECOMMENDED

The `implementation_map.json` sidecar already exists (PR #2108, 2026-05-17). The seeder writes one row per obligation with `obligation_id`, `artifact`, `location_hint`, `treatment_template`. Right now this sidecar is **consumed by the gate** (`wiki_coverage_gate.py`) but **not surfaced to the writer**.

The fix: render the seeded `implementation_map.json` into the writer prompt as a literal block — `IMPLEMENTATION_MAP_CONTRACT` — with the directive *"emit each row's required artifact element at the row's `location_hint`, populated with the row's `treatment_template`."* The writer no longer translates obligation → artifact emission; the contract is pre-resolved by the seeder.

**Pros:**
- Reuses infrastructure shipped 24 hours ago (PR #2108) — zero new schema, zero migration
- Per-obligation guidance is *manifest-specific*, not template-generic — each row already has its `treatment_template` filled in
- Writer's job collapses to *"fill in the rendered contract"* — eliminates the translation step that fails today
- Smallest prompt growth — one rendered block, no per-type template explosion
- Aligns with the Path 3 design principle: *"writer fills slots, doesn't invent coverage structure"* (per `docs/decisions/2026-05-17-path3-per-obligation-review-loop.md` Phase 0)

**Cons:**
- Relies on the seeder being correct per type — any seeder bug propagates to every module build until caught
- The `treatment_template` strings have to be human-readable enough that the writer can fill them sensibly (no opaque schema-strings)

---

## Comparison table

| Dimension | α — manifest upstream | β — prompt downstream | γ — render seed (rec.) |
|---|---|---|---|
| Files touched | `wiki_manifest.py`, schema, every existing manifest, writer prompt | `linear-write.md` only | `linear-write.md` + `linear_pipeline.py` (render hook) |
| Schema migration | Yes — re-generate every manifest | No | No |
| LOC added | ~150 (schema + serializer + prompt) | ~80 (prompt only) | ~25 (render hook + prompt section) |
| Prompt growth | Medium | Large (60-120 LOC) | Small (one rendered block) |
| Per-row specificity | High (verbatim tokens) | Low (static templates) | High (treatment_template per row) |
| Failure mode if writer mis-renders | Token absent → gate fail (deterministic catch) | Template incomplete → silent gap | Slot empty → gate fail (deterministic catch) |
| Infrastructure reuse | No (new fields) | No (new prompt sections) | **Yes (PR #2108 sidecar already shipped)** |
| Estimated effort | 4-6 h Codex | 1-2 h Codex | 1-2 h Codex |
| Estimated risk | High (schema migration touches every prior build) | Medium (prompt complexity, PR #2105 lesson) | Low (sidecar already validated in gate) |

---

## Recommendation: γ

The seeder side of γ is **already on main** (`scripts/build/phases/seed_implementation_map.py`, PR #2108 / `15834d642c`). The gate consumes it. The missing piece is a 25-LOC render hook that pipes the same JSON into the writer prompt at build time.

This is the architectural pattern Path 3 was designed around: *deterministic skeleton → writer fills slots → gate verifies*. The skeleton exists; the writer just isn't seeing it.

### Concrete implementation sketch (sized for dispatch brief)

1. **`scripts/build/linear_pipeline.py`** — in the writer phase setup, read `curriculum/l2-uk-en/{level}/{slug}/implementation_map.json` and substitute it into the writer prompt under a new placeholder `{IMPLEMENTATION_MAP_CONTRACT}`. ~10 LOC.

2. **`scripts/build/phases/linear-write.md`** — add a new top-level section (near the existing `## Obligation handling` block, ~line 915):

   > ## Implementation Map Contract
   >
   > The pipeline has pre-resolved every wiki obligation to (`obligation_id`, `artifact`, `location_hint`, `treatment_template`). Your job: emit each row's required element at its `location_hint`, populated with its `treatment_template`. Do NOT invent new obligations, do NOT skip rows. The gate verifies row-by-row against this contract.
   >
   > {IMPLEMENTATION_MAP_CONTRACT}

   ~15 LOC.

3. **Contract test** — `tests/test_implementation_map_render.py`: assert that the rendered prompt contains the contract block, that every manifest row appears in the rendered prompt, that the placeholder is fully replaced.

4. **m20 replay** — rebuild a1/my-morning, verify `wiki_coverage_gate` `coverage_pct ≥ 80%` (target: 15+ / 18 obligations) and `wiki_coverage_correction_pass` iterations reduced to 0-1.

**Estimated effort:** 1-2 h Codex (`gpt-5.5`, `xhigh`, single PR). Mirrors the shape of #1969 (writer-prompt pre-emit checklist).

---

## What this gets us

| Metric | Today (no contract render) | After γ |
|---|---|---|
| m20 wiki_coverage | 22.2% (4 / 18) | ≥80% expected (15+ / 18) |
| Writer prompt growth | n/a | +~25 LOC (one rendered block) |
| Per-type writer translation step | Required → fails on 3 of 4 types | Eliminated — contract is pre-resolved |
| Correction-pass iterations | 1 batched + N narrow + 1 regression | 0-1 expected |
| Reusable across modules | Yes (manifest is per-module) | Yes (sidecar is already per-module) |
| Reusable across tracks | Yes | Yes |

---

## Risks (γ specifically)

1. **Seeder bug propagates.** If `seed_implementation_map.py` mis-categorizes an obligation, the writer fills a wrong slot. Mitigation: PR #2108 already includes the seeder contract test; extend with one round-trip test per obligation type (sequence_step → module.md, l2_error → activities.yaml, decolonization_ban → module.md prose).
2. **`treatment_template` quality.** If the seeder's templates are too terse, the writer doesn't have enough to fill the slot pedagogically. Mitigation: m20 replay surfaces this immediately; iterate on the templates from observed writer output.
3. **Prompt token budget.** A manifest with 30+ obligations would render a large contract block. Mitigation: 30+ obligations is a curriculum-plan signal that the module is too dense — fix at the plan layer, not the contract layer. Cap at 25 obligations per module as a separate plan-review gate.

---

## Bridge for m20 (the immediate problem)

m20 has now been stuck at the wiki_coverage_gate for 4+ build attempts. Options:

| Option | Effort | Trade-off |
|---|---|---|
| **A. Ship γ first, then m20 build #8 under γ** | 1-2 h Codex + 1 build cycle | Cleanest. m20 becomes the first-ever ship under the full Path 3 contract. **Recommended.** |
| B. Manual content patch on m20 build #7 artifacts | ~1 h | Violates "stop manually editing writer output" direction. Carries m20 forward but doesn't validate the contract path for any other module. Not recommended. |
| C. Plan revision: shrink m20 manifest from 18 to ~10 obligations | ~2 h | Lowers ambition; sets bad precedent. Already declined for Path 3 (option C in `2026-05-17-path3-per-obligation-review-loop.md`). Not recommended. |
| D. Accept 22% coverage as one-off | 0 | Violates `#1 quality above all`. Strongly advised against. |

---

## Implementation plan (1 PR if γ accepted)

| Step | Scope | Estimated effort |
|---|---|---|
| 1 | `linear_pipeline.py` render hook + placeholder substitution | 30-45 min |
| 2 | `linear-write.md` contract section + directive | 15-30 min |
| 3 | `tests/test_implementation_map_render.py` contract tests | 20-30 min |
| 4 | m20 build #8 replay + verify ≥80% coverage | 10-15 min wall |

Total: **1-2 hours focused Codex dispatch** (single PR). Mirrors the shape and risk profile of #1969.

---

## Open questions for user sign-off

1. **Pick a shape: α / β / γ?** Default is γ per analysis above.
2. **m20 bridge option:** A (ship γ first, recommended), B (manual patch — discouraged), C (plan revision — discouraged), D (accept 22% — strongly discouraged)?
3. **Reviewer routing for the implementation PR:** Codex (recommended — `xhigh`, mirrors #2127 path) or different agent?
4. **Order in queue:** dispatch γ now (unblocks m20 ship), or wait until the 5 deliverable docs from the gap audit are written first (handoff §1.4 sits in that batch)?

---

## Default if no decision

Per the pending-decision convention: orchestrator re-raises rather than acts on a default. **Do NOT silently start implementation.** m20 stays at 22% coverage until you sign off the shape and bridge option.

---

## Cross-links

- m20 build #7 forensics: issue #2148
- Path 3 architecture (parent): `docs/decisions/2026-05-17-path3-per-obligation-review-loop.md`
- Seeder PR that shipped Path 3 Phase 0 (`seed_implementation_map`): PR #2108 (`15834d642c`)
- Wiki coverage gate (consumer of seed): `scripts/build/phases/wiki_coverage_gate.py`
- Current writer prompt: `scripts/build/phases/linear-write.md` (~2431 lines)
- Documentation gap audit that surfaced the need for this card: `audit/2026-05-18-docs-gaps-and-reorganization/REPORT.md` §1.4
- m20 ship cascade context: `docs/session-state/2026-05-19-handoff-gap-audit-and-qwen-integration.md`
