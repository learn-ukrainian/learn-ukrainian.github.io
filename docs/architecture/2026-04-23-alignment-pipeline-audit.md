# Alignment-Pipeline Audit — 2026-04-23

> **Status:** adopted. Informs EPIC [`docs/epics/2026-04-23-alignment-pipeline-runtime-contracts.md`](../epics/2026-04-23-alignment-pipeline-runtime-contracts.md).
>
> **Inputs:** Claude (backbone), Codex (adversarial — bridge msg 429), Gemini (content-builder — bridge msg 428), diagnostic reports `docs/reports/2026-04-23-a1-colors-opus-r1-dim-diagnosis.md` (#1449) and `docs/reports/2026-04-23-gemini-wiki-writer-diagnosis.md` (#1450).

---

## 1. Thesis

The alignment pipeline has **no runtime contract**. The chain

```
config.py → curriculum.yaml → plans → Ukrainian wiki →
  writer prompts → reviewer prompts → v6_build.py → audit → publish
```

plus the unnamed layers the user and I added (rules + decisions, sources DB + MCP surface, shared contracts, tokenizer, reviewer personas, fix-loop contract, post-processors, pedagogy, issues + tests) — **15 layers in total** — is coupled only by convention. When an upstream layer changes, downstream artifacts do not automatically invalidate. Agents consume stale sidecars and produce results "consistent against yesterday's state of the world."

Every recent alignment bug (#1403 auto-merge, #1431 contract asymmetry, #1448 tokenizer mangling, ISTORIO 3500-vs-4000 word-target drift) is a specific instance of the same missing structural invariant.

---

## 2. The 15-layer stack

| # | Layer | Source of truth | Drift surface |
|---|---|---|---|
| 1 | Thresholds / targets | `scripts/audit/config.py` + `scripts/config.py` | Already split-brain (target-words in two files, review target 8.0 vs audit naturalness 9.0) |
| 2 | Module manifest | `curriculum/l2-uk-en/curriculum.yaml` | Slug ↔ filename drift |
| 3 | Plans (versioned) | `curriculum/l2-uk-en/plans/{level}/{slug}.yaml` | In-place modification without `.bak` + version bump |
| 4 | **Generated sidecars** (Codex #1) | `contract.yaml`, `wiki-excerpts.yaml`, `state.json`, `module-memory.yaml` | **No hash-check reuse** — `v6_build.py:3207` |
| 5 | Sources DB + MCP surface | `data/sources.db` + `mcp__sources__*` | Plans cite IDs absent from DB |
| 6 | Ukrainian wiki | `curriculum/*/wiki/`, compiled from layer 5 | **Legacy weighted-average review** while module uses MIN gate |
| 7 | Canonical-anchor registry | PR #1447 | Not yet cross-validated with plans |
| 8 | Shared module contract | PR #1431 v2 | Consumed as cache (see layer 4) |
| 9 | Tokenizer / encoding | `scripts/build/phases/wiki_compressor.py:72-80` | **Root NFKD hazard still present** — patched in one checker only (#1448) |
| 10 | Writer prompts (per phase) | `.claude/phases/` + `.gemini/phases/` | Placeholder + cross-phase contradiction drift |
| 11 | Reviewer persona prompts (9 dims) | Per-dim templates | Weighted-avg scoring text still lives in wiki path |
| 12 | Fix-loop contract | `<fixes>` find/replace protocol | **Live code contradicts the decision** — `convergence_loop.py:595-607` still has `section_rewrite`/`full_rewrite`/`writer_swap` |
| 13 | Post-processors | Stress annotator, enrichment | Unchecked mutation class |
| 14 | Rules + decisions + MEMORY | `claude_extensions/rules/`, `docs/decisions/`, `memory/MEMORY.md` | **Soft law** — `check_decisions.py` is advisory, not a hard gate |
| 15 | GH issues + tests | GitHub + `tests/` | Rule-after-incident pattern; tests compensate for root cause rather than preventing it |

**Verified during the audit:**
- Rule drift `claude_extensions/rules/` vs `.claude/rules/`: **CLEAN** (no diff).
- Decision journal: 5 active, 0 stale on surface — BUT decisions are advisory; Codex caught a "no-rewrite" decision contradicted by live convergence code.
- `min_activities=0` across levels: **intentional** per #969 (plan `activity_hints` guides count, not audit gate).
- `a1/colors` state: phase `verify` failed, R1 REJECT — the vertical evidence that alignment is leaking.

---

## 3. Where silent drift is hiding NOW

Ranked by blast radius × detection difficulty.

### Architectural (fix structurally)

**A1. Generated sidecars reuse without hash check.** `v6_build.py:3207` reloads `contract.yaml` + `wiki-excerpts.yaml` if they exist on disk — regardless of whether plan, wiki packet, templates, anchor registry, or tokenizer have changed. A "consistent" run can be consistent against stale artifacts. Single most dangerous surface in the repo.

**A2. `module_memory` silent-update on corpus change.** `module_memory.py:293-316` invalidates constraints only on `plan_hash` mismatch. `sources_hash` updates silently. Corpus, rule, or tokenizer changes land but old constraints persist — "why is the model still fighting yesterday's bug?"

**A3. Live code contradicts the stated architecture.**
- Decision says reviewer-as-fixer, no rewrite. Code still rewrites (`convergence_loop.py`).
- Pipeline rule says Gemini is the default writer. `main` switched to `claude-tools` yesterday (commit `5e2afbd092`).
- These are not drift edges — they are two different systems under one name.

### Live bugs (fix directly)

**B1. Wiki review is weighted-average; module review is MIN.** `scripts/wiki/compile.py:623-639` vs `v6_build.py:7689-7713`. Wikis with passing aggregate can have individual dims that fail the module gate downstream.

**B2. Threshold duplication.** Module review target 8.0 (`v6_build.py:112`); audit naturalness 9.0 (`audit/config.py:46-56`). Same bug class as the ISTORIO incident, live today.

**B3. Tokenizer NFKD hazard patched, not eliminated.** `wiki_compressor.py:72-80` still normalizes with NFKD + combining-mark strip. `tests/test_contract_compliance.py:546-587` catches at one site; any new consumer inherits the hazard.

**B4. Attribution-routing bug in `_search_sections_fts5`.** Missing `"corpus": "textbook_sections"` key on result rows produces 1,538 `type: unknown` + `file: S####` entries across 215 of 220 compiled wikis. **98% of all observed "phantom citations" are this bug, not writer fabrication.** (#1450 Fix 1.)

**B5. Chunk-ID leakage in prompt.** `compiler._format_sources:282-286` prints `Chunk ID: \`S3931\`` — writer reads `S`-prefix and emits `[S3931]` as inline citation. (#1450 Fix 2a.)

**B6. `_extract_terms` emits function words as `required_terms`.** `scripts/build/phases/plan_contract.py:42-51` takes first-8 Cyrillic tokens ≥3 chars. For `a1/colors` this surfaced `для, мові, активно, вчимо, пару, такий, поділених, типами` as writer requirements → the writer code-switches (`"follows the same правилами you practiced in модуль 9"`) to comply. **One heuristic drives two failing dims on colors.** (#1449 §5.1.)

**B7. `dialogue_situations[].setting:` rendered as narration.** Plan's English framing metadata is written as prose before dialogue turns, not as writer-only metadata. (#1449 §5.2.)

**B8. Ghost-citation schema trap.** Writer prompt + YAML schema require a citation ID; no legal `null` / `UNATTESTED` value. When retrieval misses, writer hallucinates plausible `[S2318]`. *Scope correction: Pattern A (B4 above) subsumes 98% of what we thought was this trap; the real residual is ~24 citations across 5 A1/A2 wikis, caused by B5.*

**B9. Narrative-vs-vocabulary trap.** Plans give sterile word lists with no connective-tissue budget. Writer either imports above-level connectives (fails vocab audit) or writes robotically (fails naturalness). Root cause of Opus R1 Naturalness 4.0 on colors, not writer skill.

**B10. Discipline layer repairs instead of failing fast.** `scripts/wiki/compile.py:395-470` strips invented citations and continues, hiding the evidence we need to debug.

**B11. Rule / MEMORY contradictions.** "Think in Ukrainian, explain in English" at A1 is contradictory at the prompt level; `<!-- VERIFY -->` breaks YAML parsers; legacy IPA rule conflicts with stress-only rule.

---

## 4. Root-cause map

```
     ┌────────────────────────────────────────────────┐
     │  NO RUNTIME ALIGNMENT CONTRACT (thesis)        │
     └───┬────────────────────────────────────────┬───┘
         │                                        │
         ▼                                        ▼
  Sidecars + memory reuse              Decisions + rules are
  without freshness proof              advisory, not executable
         │                                        │
         ▼                                        ▼
  A1 (contract.yaml)                     A3 (no-rewrite vs code)
  A2 (sources_hash)                      B1 (wiki weighted-avg)
                                         B2 (threshold split-brain)

         ┌─────────────────────────────────────────┐
         │  SPECIFIC PIPELINE HEURISTICS MISFIRE   │
         └───┬─────────────────────────────────────┘
             │
             ▼
     B4 (routing bug) ─────── 98% of ghost citations
     B5 (chunk-ID leak) ──── residual 2% ghost citations
     B6 (_extract_terms) ─── code-switching on colors
     B7 (dialogue setting) ─ stage directions as prose
     B3 (tokenizer NFKD) ─── й/ї mangling
```

---

## 5. Validated by ground truth

The `a1/colors` Opus R1 smoke produced:

| Dim | Score | Root cause |
|---|---:|---|
| Factual | 8 | OK (#1447 + corpus) |
| Language | 10 | OK |
| Decolonization | 10 | OK |
| Dialogue | 10 | OK |
| Completeness | 9 | OK |
| Plan adherence | 8.5 | OK |
| Pedagogical quality (Actionable) | **3-4** | B6 (`_extract_terms`) |
| Engagement & tone (Naturalness) | **3-4** | B6 + B9 |
| Dialogue & conversation quality (Honesty mapping) | **4-5** | B7 |

The diagnostic dispatch (#1449) traced each to a specific code/plan location. The ghost-citation class (Honesty in the original framing) was **not evidenced on this branch** — the one textbook citation is authentic. The "Vashulenko Grade 2 fabrication" referenced in the 2026-04-23 afternoon handoff must come from a different run; this is a behavioral lesson in its own right (see §8).

---

## 6. What Codex added

Codex's single most important finding, which I had not surfaced: **generated sidecars and module_memory are cached on disk with no hash check against inputs.** This is the architectural class of bug underneath A1 and A2. Codex also flagged:

- Wiki review still uses weighted-average scoring (B1) while modules use MIN — adjacent layers on incompatible reward functions.
- Threshold values are duplicated across three config files (B2).
- Tokenizer hazard is patched per consumer, not eliminated (B3).
- Discipline layer repairs silently, hiding evidence (B10).
- Rules/decisions/MEMORY are "soft law" — advisory, not CI-enforced.
- The governance pattern "incident → rule later" (seen on #1403, #1431, #1448) produces alignment bugs as production incidents rather than CI failures.

## 7. What Gemini added

Gemini's content-builder perspective gave the *causal mechanism* behind what I had described only as symptoms:

- The **narrative-vs-vocabulary trap** (B9) is not a writer-skill deficit — it is a plan-schema gap. A "connective-tissue budget" field would close it.
- **Code-switching** (part of B6) is triggered by two concrete conditions: (1) heavy Cyrillic context in the wiki teaching brief acting as attention pivot, (2) contradictory prompt instructions ("think in Ukrainian" + "explain in English").
- **Fabricated citations** (B8) are caused by the output schema rejecting `null` citation values — the parser forces a plausible-looking token when retrieval is sparse.
- **Live rule contradictions**: "admit uncertainty with `<!-- VERIFY -->`" is pedagogically correct but structurally broken (HTML comments inside YAML blocks break parsers).

## 8. Behavioral lessons for MEMORY.md

1. **Do not inherit a failure-class claim from a previous handoff without verifying it exists on the current branch.** The "Vashulenko Class 2 fabrication" framed as the Honesty-dim root cause was not evidenced on `a1/colors`. Always re-verify against the branch artifacts before designing a fix.

2. **When a reviewer dim score is low, trace to the specific pipeline code that is forcing the behavior before designing prompt or plan fixes.** `_extract_terms` (B6) would have remained invisible without Opus reading `plan_contract.py` line-by-line. The "bad prompt" hypothesis is often a "bad pipeline heuristic the prompt has to compensate for" hypothesis.

---

## 9. What changes in the action plan

Two of my original recommendations shrink significantly after the diagnostics:

- **Ghost-citation schema redesign** (originally a major Phase 3 item) collapses to "dispatch #1450 Fix 1 + Fix 2a" — two tiny code fixes. The residual after those is ≤5 invented citations across the next 100 wiki compiles.
- **Narrative-vs-vocabulary schema extension** narrows to "kill `_extract_terms`, source `required_terms` from `vocabulary_hints.required` already in the plan." The extension fields (`allowed_passive_connectives`, `pedagogical_bridge`) may not be needed; the existing fields just aren't being used.

**Unchanged and reinforced:** the alignment-manifest + sidecar-freshness recommendations (Phase 1). B4 showed the consequence when an informal contract (the `corpus` key) silently drifts: 1,538 corrupted downstream records. A hashed manifest would catch that class.

---

## 10. See also

- EPIC: [`docs/epics/2026-04-23-alignment-pipeline-runtime-contracts.md`](../epics/2026-04-23-alignment-pipeline-runtime-contracts.md)
- Colors rebuild: [`docs/reports/2026-04-23-a1-colors-rebuild-plan.md`](../reports/2026-04-23-a1-colors-rebuild-plan.md)
- Diagnostic: `docs/reports/2026-04-23-a1-colors-opus-r1-dim-diagnosis.md` (via PR for #1449)
- Diagnostic: `docs/reports/2026-04-23-gemini-wiki-writer-diagnosis.md` (via PR for #1450)
- Bug autopsies: [`docs/bug-autopsies/alignment-contracts.md`](../bug-autopsies/alignment-contracts.md)
