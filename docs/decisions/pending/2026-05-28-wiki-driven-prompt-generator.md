# PENDING — Wiki-driven prompt generator (V7.1 evolution, NOT V8 greenfield)

**Status:** PENDING — awaiting user approval. Synthesizes the 2026-05-28 codex + cursor + gemini consultation on channel `wiki-driven-prompt-generation-2026-05-28`, thread `1241c73bf87c4e29bea394fd5998506a`. **Unanimous Vote A** (3-for-A, 0-for-B/C/D) with convergent refinements on (Q1) clean universal/wiki/RAG split + composition rules, (Q2) hybrid reviewer rubric, (Q3) pure Python implementation, (Q4) ~1 week A1/A2 pilot.

**Surfaced:** 2026-05-28 (Pt 14) — user audit caught m20-specific lesson content baked into the static writer prompt template (5 `прокидаюся` mentions, 3 `Захарійчук` mentions, an entire paragraph citing "m20 round #12, codex-tools, a1-my-morning-20260526-204640, PR #2358, decolonization 8.7 score" as build-history-as-prompt-content, m20's chunk_id `1-klas-bukvar-zaharijchuk-2025-1_s0024` as the canonical citation example). User framing: *"we should use the wiki to generate the writer and review prompt. for both the prose and the practices."* Refined after my over-engineered 3-layer proposal: *"we have universal rules plus the wiki of the module, plus the related rag content and we could use those to generate the writer and reviewer prompt."*

**Predecessor ADR:** [`2026-05-27-v7.1-wiki-driven-writer.md`](2026-05-27-v7.1-wiki-driven-writer.md) — V7.1 introduced the "render the wiki" charter at the prompt-content level. This ADR completes the move V7.1 deferred: move composition itself off the static template and onto a deterministic generator.

**Scope (BLOCKING):** A1/A2 module builds (pilot on m21+m22 after generator lands). Does NOT block tech-debt PRs.

---

## TL;DR

Replace the 550-line static writer prompt template (`scripts/build/phases/linear-write.md`) with a **deterministic Python generator** that assembles per-lesson writer + reviewer prompts at build time from three inputs:

```
INPUTS:
  - universal_rules/        — fragments keyed by #R-* IDs with level/track predicates
                              (VESUM ban, Russianism check, schema invariants,
                               voice/register rules, gate definitions, level metalanguage)
  - wiki/pedagogy/{level}/{slug}.md
                            — per-lesson teaching brief (methodology, sequence steps,
                               L2 errors, decolonization pairs, vocabulary minimum)
  - plan.references + RAG    — textbook chunks, dictionary entries, source materials

GENERATOR (pure Python, no LLM):
  - select universal fragments by level/track/activity-profile metadata
  - inline wiki teaching brief
  - inline RAG content with per-chunk verification obligations
  - emit ONE obligation checklist consumed by writer prompt + reviewer prompt + gate parser

OUTPUTS:
  - writer_prompt.md  (per-lesson, no static-template contamination surface)
  - reviewer_prompt.md (per-lesson rubric tied to wiki obligations + RAG chunks the writer cited)
```

**Critical reframing (cursor r1, codex r2 concurred):** This is **NOT V8 greenfield.** The pieces already exist:
- `render_phase_prompt()` at `scripts/build/linear_pipeline.py:1747` already does deterministic placeholder rendering
- `writer_context()` at `scripts/build/linear_pipeline.py:2881` already injects plan/knowledge/wiki/implementation-map
- `scripts/build/phases/wiki_manifest.py:147` already extracts typed obligations
- `#R-*` rule_id markers already wire prompt rules to gate telemetry

The work is: **evolve** these into a rule registry + composition layer. Not rewrite.

**Cost:** ~1 week A1/A2 pilot (m21+m22), ~1.5-2 weeks full parity across correction prompts + grok writer variant.

---

## Why now

1. **Empirical contamination demonstrated.** Today's audit named 10+ m20-specific tokens hardcoded in `linear-write.md`. The contamination is structural — any static-template + iterative-tuning system accumulates per-instance bias.
2. **Gate-vs-prompt drift pattern cited 5 times in 1 session.** Today's V7.1+codex build at `.worktrees/builds/a1-my-morning-20260528-122552/` produced clean 1505w A1 output, 25 tool calls / 12 distinct MCP tools, all python_qg PASS, wiki_completeness PASS — halted at `wiki_coverage_gate` because the gate parser expects nested `<implementation_map><row .../></implementation_map>` while the V7.1 writer emits self-closing `<implementation_map ... />` inline tags. Three hand-maintained descriptions of the same contract (writer prompt rule, gate parser regex, reviewer template wording) drift apart on every prompt iteration.
3. **Codex's high-leverage finding (r2):** `review_context()` at `linear_pipeline.py:3687` passes plan/content/dim to the reviewer but **NOT** `wiki_manifest` or `implementation_map_contract`. The reviewer is structurally blind to what the writer was asked to do. This single missing pass-through is the reviewer drift surface.
4. **Cursor's killer observation:** today's m20 blocker is exactly the bug the generator prevents — single-source emission from the same registry across writer + reviewer + gate parser eliminates the drift class.
5. **V7.1 charter already won the writer-behavior question** (today's build: 25 tool calls / 12 distinct tools, all python_qg gates pass, wiki_completeness PASS). The remaining blockers are operational (gate format compatibility, reviewer pass-through) — exactly what wiki-driven prompt generation eliminates.

---

## Architecture

### Three-layer composition (user's framing)

| Layer | Owns | Examples |
|---|---|---|
| **Universal rules** | Invariants + level/track-conditional gates | VESUM-all-words, Russianism ban, bad-form marker syntax, schema invariants, S1-S6 scaffolding *requirement* (A1/A2-conditional), single-voice rule, AI-slop ban |
| **Wiki of the module** | Lesson substance | The 5 sequence steps, L2 error table, decolonization contrast pairs FOR THIS lesson's domain, vocabulary minimum, methodology |
| **Plan references + RAG** | Grounding targets | Textbook chunk_ids to fetch + verify, page citations for `resources.yaml`, dictionary entries supporting wiki claims |

### Composition rules (the explicit junctions, not a 3rd bucket)

1. **Universal policy + wiki payload** — universal says "include ≥1 bad-form contrast pair when applicable"; wiki supplies the pair (`<!-- bad -->завтрак<!-- /bad -->` vs `сніданок` for routine-domain m20; different pair for other lessons).
2. **Universal protocol + plan payload** — universal says "use chunk_id-first citation"; plan supplies the actual chunk_id from `plan.references[*].notes` (generated example per-lesson, never another module's `_s0024`).
3. **Universal rule mirrored in reviewer** — today `linear-review-dim.md` manually duplicates writer rules ("Mirrors `#R-NO-CHILDREN-PRIMARY-QUOTES`"). That duplication is the drift vector. Single-source from rule registry.

The codebase **already has the registry hook**: `#R-*` IDs (`#R-VESUM-ALL-WORDS`, `#R-CITE-HONEST`, etc.) wired to gate telemetry in `linear_pipeline.py`. The generator treats those IDs as the single registry; no parallel taxonomy.

### Implementation shape

```
scripts/build/
  universal_rules/                  # fragments keyed by #R-* IDs + level/track predicates
    R-VESUM-ALL-WORDS.md
    R-CITE-HONEST.md
    R-NO-CHILDREN-PRIMARY-QUOTES.md  # level:[a1,a2] predicate
    R-SINGLE-VOICE-A1.md             # level:[a1,a2] predicate
    R-CLEAN-TABLES.md
    ... (~20-30 fragments)
  prompt_generator.py               # NEW — composition logic + obligation checklist emit
  phases/
    linear-write.md                 # SHRINKS — keep slot markers + composition directives only
    linear-review-dim.md            # SHRINKS — same shrinkage
```

The generator:
1. Loads rule fragments matching `(level, track, activity_profile)` predicates
2. Inlines wiki teaching brief from `wiki_manifest.py:147` typed extraction
3. Inlines RAG chunks from `plan.references` with per-chunk verification obligations
4. Emits **one Obligation Checklist block** consumed identically by writer prompt + reviewer prompt + `wiki_coverage_gate` parser

**Key invariant:** any text in the rendered writer prompt that names a specific Ukrainian word, textbook author, chunk_id, or PR number MUST be derivable from `(wiki ∪ plan.references ∪ lesson_slug)`. Anything else is contamination and the leakage sentinel test fails the build.

### Reviewer rubric — hybrid (Q2)

- **Universal subjective dimensions** (existing) for prose quality: pedagogical, naturalness, engagement, tone, decolonization, register_consistency, etc.
- **Wiki/plan-derived deterministic checks** (new) for content coverage: did the writer cover all 5 sequence steps from the wiki? Did the writer cite each chunk_id from plan.references? Did the writer include the wiki's decolonization contrast pair?

The deterministic-checks layer is generated from the **same Obligation Checklist** the writer saw. Zero drift between "what was asked" and "what's evaluated."

---

## Decision points settled in the multi-agent discussion

| Question | Answer | Rationale |
|---|---|---|
| Q1 — Universal/wiki/RAG boundary | Clean split + explicit composition rules at 3 junctions | All three agents agreed; cursor enumerated the junctions concretely |
| Q2 — Reviewer rubric | **Hybrid (c)** — keep universal subjective dims, add wiki-derived deterministic checks | All three agents agreed; option (b) would regress prose quality |
| Q3 — Generator implementation | **Pure Python (a)** | All three strongly agreed; LLM-driven (b) reintroduces drift one layer earlier; hybrid (c) solves wrong problem |
| Q4 — Cost | ~1 week A1/A2 pilot, ~2 weeks full parity | Codex + cursor + gemini converged |
| Riskiest sub-task | Single-source-of-truth parity across writer prompt ↔ gate parser ↔ reviewer prompt for `implementation_map` shape | Cursor named this explicitly; exactly today's m20 blocker class |

---

## Sequencing (cursor's refined-A, codex r2 concurred)

1. **`linear-write.md` contamination cleanup PR** (~2 hours, codex or claude-headless): purge m20 literals — `прокидаюся`, `Захарійчук`, `сніданок`, the build-history paragraph, the chunk_id example, the JSON answer example. Add leakage regression test (option C's idea, but as guardrail not whole solution). **Stops the bleeding immediately.**
2. **`review_context()` wiki/manifest pass-through PR** (~30 LOC, codex): `scripts/build/linear_pipeline.py:3687` — pass `wiki_manifest` + `implementation_map_contract` into reviewer context. Independent of generator; eliminates a known drift surface today.
3. **`wiki_coverage_gate` V7.1 inline tag support PR** (~30-50 LOC, codex or gemini): `parse_implementation_map` accepts self-closing inline `<implementation_map obligation_id="..." artifact="..." location="..." treatment="..." />` shape alongside nested form. Unblocks any V7.1 build at the gate level.
4. **Rule registry scaffold PR** (~1-2 days, **claude-headless** — architectural judgment): design `scripts/build/universal_rules/` fragment schema + predicates + extraction from current `linear-write.md`. Includes mechanical fragment extraction + level/track predicates + registry index. Outputs a working registry but generator not yet wired.
5. **Prompt generator implementation PR** (~2-3 days, **claude-headless** or codex): `scripts/build/prompt_generator.py` — composition logic + obligation checklist emission. Wire into `writer_context()` + `review_context()`. Backward-compatible (legacy template path still functions during migration).
6. **Reviewer obligation emission from same registry PR** (~1 day, codex): emit deterministic-check block in reviewer prompt from registry. Update `wiki_coverage_gate.py` + reviewer-side rendering to consume the same Obligation Checklist.
7. **m20 rebuild under clean pipeline PR** (orchestrator inline): fire V7.1+codex+generator build on a1/my-morning. Verify acceptance criteria. Promote as proper m20 anchor (single ship event).
8. **m21 + m22 pilot PR** (orchestrator + codex): fire V7.1+codex+generator on a1/m21 and a1/m22. Acceptance: zero cross-lesson tokens in rendered prompts AND wiki_coverage_gate passes without format-drift corrections.

---

## Risks + mitigations

| Risk | Mitigation |
|---|---|
| Registry design wrong on first try | Step 4 as separate PR before step 5; iterate the registry shape on a single lesson's prompt before wiring |
| Backward compatibility breaks during migration | Step 5 keeps legacy template path; generator opt-in via flag until pilot passes |
| Single-source emission contract slips again | Step 6 ships acceptance test: assert identical Obligation Checklist text in writer_prompt.md + reviewer_prompt.md + parsed by wiki_coverage_gate |
| Wiki author burden inflates | This proposal DOES NOT change the wiki schema. Wiki stays a teaching brief. Pedagogical practices stay in universal rules. Cursor + codex confirmed |
| Quota — Claude headless usage | User direction 2026-05-28: "use more claude headless agents." Steps 4-5 dispatched to claude headless. Steps 1-3, 6 use codex (cheaper, faster on mechanical work) |

---

## What this ADR is NOT

- NOT a new pipeline phase. The V7 pipeline structure (writer → python_qg → wiki_coverage → llm_qg → MDX → promote) stays exactly the same.
- NOT a wiki schema change. Wikis stay as they are.
- NOT a writer change. The writer (codex-tools default) continues to render the wiki. Just with a non-contaminated, lesson-aware prompt.
- NOT a reviewer rubric replacement. Universal subjective dims stay; we add wiki-derived deterministic checks alongside.
- NOT urgent. m20 stays unshipped under the contaminated template. m20 rebuilds + ships under the clean pipeline (step 7) as the anchor of record. One ship event, not two.

---

## Appendix: full discussion thread

- **Channel:** `wiki-driven-prompt-generation-2026-05-28`
- **Thread:** `1241c73bf87c4e29bea394fd5998506a` (in `.mcp/servers/message-broker/messages.db`)
- **Question doc:** `audit/2026-05-28-wiki-driven-prompt-generation/question.md`
- **Participants:** codex (r1+r2), cursor (r1+r2), gemini (r1 failed-session, r2 substantive)
- **Outcome:** unanimous **Vote A** with convergent refinement
- **Key sub-finding (codex r2):** `review_context()` at `linear_pipeline.py:3687` doesn't pass `wiki_manifest` or `implementation_map_contract` → reviewer drift surface; single-line fix
- **Key sub-finding (cursor r1):** today's m20 wiki_coverage_gate failure IS the drift class this generator eliminates; three hand-maintained descriptions of the same `implementation_map` contract
