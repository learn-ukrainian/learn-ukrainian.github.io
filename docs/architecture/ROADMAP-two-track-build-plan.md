# Two-Track Build Roadmap — A1/A2 L1-UK Bootstrap + B1→C2 L2-UK-EN

**Date**: 2026-04-20
**Status**: Design agreed with user; tri-agent confirmation pending on bootstrap-framing specifics (#1349 discussion round 2)
**Related issues**: #1337 (schema), #1339 (grade filter), #1340 (re-validation), #1344 (canary rebuilds), #1348 (retrieval), #1349 (L1-UK pivot)

## Purpose of this doc

Single source of truth for the sequenced build plan that gets us from today's state (A1/A2 quality struggling, retrieval being rebuilt) to shipped wikis and modules across all tracks. Supersedes ad-hoc plans in session-state notes; referenced by issue bodies and handoffs.

## The key insight that drives this plan

**A1 and A2 have thin authoritative source grounding.** After grade-filtering to Grades 1-4, the textbook corpus drops from ~24K chunks to ~3-5K. Literary corpus is too hard for A1/A2 learners. The wiki compile layer has to synthesize heavily against thin source material → quality suffers.

B1 and up have rich source grounding (Grades 5-11 textbooks, literary corpus, archaic corpus, Wikipedia). Same pipeline, different corpus availability → different quality floor.

**Therefore**: two-track design. A1+A2 gets a corpus-bootstrap operation (L1-UK native authoring → those modules become new source material). B1→C2 + seminars ride on existing source abundance and ship on the current architecture.

## Parallel tracks

| Level | Source grounding today | Pipeline | Native-reviewer load |
|---|---|---|---|
| **A1, A2** (Track A) | Thin | L1-UK native authoring → corpus bootstrap → L2-UK-EN build retrieves against bootstrapped corpus | Canary (~6-8 h) + scale rubric (~4-6 h) + sampled audit (~2 h/week) |
| **B1, B2, C1, C2, Seminars** (Track B+) | Rich (already Ukrainian) | Current L2-UK-EN pipeline, post-#1348 retrieval | None — no L1-UK gate |

Tracks run in parallel after shared Phase 1 unblock. Track B+ ships first (weeks sooner) because it has no native-reviewer dependency.

---

## Phase 1 — Shared engineering unblock

**Both tracks depend on this. Nothing starts until Phase 1 is green.**

| # | Step | Owner | Est | Done-when |
|---|---|---|---|---|
| 1.1 | Fix **#1337** — add `textbook_sections` parent table + `parent_section_id` column + extraction pipeline into `scripts/wiki/build_sources_db.py` | Codex implements | 2–4 h | Commit lands, `PRAGMA table_info(textbooks)` shows `parent_section_id`; `textbook_sections` table exists |
| 1.2 | Rebuild `data/sources.db` with the new schema | User runs | 30 min | DB rebuilt, literary_texts + external + wikipedia row counts preserved |
| 1.3 | Fix **#1339** — A1 grade filter SQL bug (chunks leak Grade 5+ into A1 retrieval) | Codex | 1–2 h | Test: `search_sources(track="a1")` returns only Grade 1-4 chunks; regression test committed |
| 1.4 | Verify stage (c) of #1348 works against rebuilt DB | Claude | 30 min | `pytest tests/wiki/ -v` green after deleting v1 orphan tests; `search_sources(track="a1")` returns non-empty results on real DB |
| 1.5 | Dispatch **#1348 stage (d)** — stress test + fault injection + ADR-006 revision (prompt at `docs/session-state/pending-dispatches/1348-stage-d.md`) | Codex | 30–45 min | Commit `test(wiki): ... (#1348 stage-d)`; ADR-006 revised with 2026-04-20 block |
| 1.6 | Run **#1348 stage (e) cold encode** — `.venv/bin/python scripts/wiki/cold_encode.py --all-corpora` | User runs on their Mac, Claude monitors | 2.5–3 h | `data/embeddings/manifest.db` has ~157K unit rows; `.npy` shards across 5 corpus dirs |
| 1.7 | Run **#1340** re-validation — patch `scripts/wiki/diagnostics/retrieval_playback.py` to add `--strategy=unified_dense`, run on `a1/sounds-letters-and-hello` | Claude | 1–2 h | New comparison report shows **≥8/10 concepts** surfaced (baseline = 6/10) |

**Phase 1 decision gate**:
- ≥8/10 on #1340 → fork into Tracks A and B+ below
- 7/10 or lower → file embedder bakeoff follow-up (per #1340 AC4), park L1-UK pivot, reassess architecture

---

## Track B+ — B1, B2, C1, C2, Seminars

**Starts immediately after Phase 1 gate. No L1-UK dependency. No native-reviewer dependency.**

| # | Step | Owner | Est | Done-when |
|---|---|---|---|---|
| B+.1 | Rebuild canary wikis for 4 seminar/track representatives (hist, bio, lit, oes — 1 each) with post-#1348 retrieval | Claude drives `wiki/compile.py`, Gemini writes | 1 h each, parallelizable = ~4 h wall | 4 new `wiki/*.md` artifacts exist; 4-dim review PASS on each |
| B+.2 | Build 1 module per canary track using the rebuilt wikis | Claude drives, Gemini writes | ~30-60 min each, parallel | 9-dim review PASS on each |
| B+.3 | If B+.2 passes: batch-build priority B1+ tracks in user-driven order | User drives batches, Claude monitors via Monitor tool | Weeks, paced to user | Per-track audit gates GREEN at target percentages |
| B+.4 | Ship B+ tracks to public site | User | — | Wikis + modules live on `learn-ukrainian.github.io` |

**Track B+ is not gated by Track A**. Ships on its own timeline.

---

## Track A — A1 and A2 with L1-UK bootstrap

**Starts in parallel with Track B+ after Phase 1 gate. Native-reviewer engagement is the long-pole dependency.**

### Track A — Phase 2A: Control baseline

| # | Step | Owner | Est | Done-when |
|---|---|---|---|---|
| A.1 | Rebuild `a1/sounds-letters-and-hello` canary wiki with post-#1348 retrieval | Claude + Gemini | 1 h | 4-dim review PASS |
| A.2 | Build Arm A control module (A1/M01) — current English-scaffolded pipeline | Claude + Gemini | 30–60 min | 9-dim review PASS; this is the canary control |

**Gate**: A.2 must PASS 9-dim. If it doesn't, the pipeline is broken; fix before continuing.

### Track A — Phase 2B: Native-reviewer engagement

| # | Step | Owner | Est | Done-when |
|---|---|---|---|---|
| A.3 | Identify + engage paid native-speaker reviewer; define canary SOW (6–8 h scope, no pre-commitment to scaling phase) | User | 1–2 weeks calendar | Reviewer onboarded with written scope |
| A.4 | Register-protocol alignment session — operational definition of "decolonized register" for this project; Russianism canon; Antonenko-Davydovych framing targets | User + reviewer | 1.5–2 h their time | Shared working notes; ad-hoc rubric seeds if reviewer wants |

### Track A — Phase 2C: Canary A/B + bootstrap decision

| # | Step | Owner | Est | Done-when |
|---|---|---|---|---|
| A.5 | Reviewer authors Arm B Ukrainian-canonical compile brief for `a1/sounds-letters-and-hello` (Claude as scribe only, no pre-drafting) | Reviewer + Claude | 45 min–1 h their time | Ukrainian brief artifact committed |
| A.6 | Build Arm B module (A1/M01) — feed Ukrainian brief to UNCHANGED `v6-write.md` | Claude + Gemini | 30–60 min | Module output exists |
| A.7 | Mechanical metalanguage containment check (Codex writes the deterministic script) | Codex | 1 h | Script emits leak-count against `scripts/config.py:215` immersion contract |
| A.8 | Blinded side-by-side review — 9-dim downstream reviewer + native register reviewer, neither knowing which arm is which | Reviewer (1 h) + Claude orchestrates | 2 h total | A vs B verdict on both instruments; leak-count on Arm B |
| A.9 | Second-module confirmation — repeat A.5–A.8 on a different A1 module | Same | 2.5 h their time | Two-module agreement on arm-level verdict |

**Canary decision gate after A.9**:
- **B wins on 9-dim, no metalanguage leak, two-module agreement** → bootstrap viable → Phase 2D
- **B wins 9-dim but leaks** → justify Arm C (hardened writer) experiment → loop A.5–A.9 with hardened `v6-write.md`
- **B loses** → pivot fails → ship A1/A2 on current English-scaffolded pipeline (Track B+ style, but with the known thin-corpus constraint)
- **Tie / noise** → second confirmation with stricter rigor; if still tied, park pivot

### Track A — Phase 2D: L1-UK A1+A2 scale + corpus bootstrap

**Only runs if canary decision gate says pivot viable.**

| # | Step | Owner | Est | Done-when |
|---|---|---|---|---|
| A.10 | Reviewer authors register rubric (Russianism canon, syntactic preferences, decolonization framing canon) — one-time, paid separately from canary | Reviewer | 4–6 h their time | Rubric file committed to repo |
| A.11 | Corpus-integration engineering — add finalized L1-UK A1+A2 modules to `data/sources.db` as new corpus (table + FTS5 + manifest + track_priors entry). **Design TBD, pending tri-agent discussion round 2 (see Open Questions below).** | Codex | 2–4 h | New corpus ingestable; manifest + priors updated |
| A.12 | Build L1-UK A1 modules — batch, rubric self-check + ~30% sampled native review | User drives batches, Claude monitors, Gemini writes against Ukrainian briefs, Codex/Claude rubric-check, reviewer samples | Weeks (paced to reviewer availability, ~2 h/week sustainable) | All A1 modules PASS 9-dim + rubric compliance |
| A.13 | Ingest finalized L1-UK A1 modules into the bootstrap corpus | Codex | Automated per batch | Each module appears in the `ukrainian_native_a1a2` corpus with embeddings |
| A.14 | Build L2-UK-EN A1 modules — retrieve against bootstrapped corpus now available | User drives, same writer pipeline | Weeks | L2-UK-EN A1 modules PASS 9-dim, quality improvement over pre-bootstrap baseline measurable |
| A.15 | Repeat A.12–A.14 for A2 | Same | Weeks | A2 complete both tracks |

---

## Cross-track dependencies + convergence

- **Phase 1 is shared.** Nothing starts in either track until it's green.
- **Track B+ does NOT depend on Track A.** If A is blocked on native-reviewer availability or scaling issues, B+ keeps shipping.
- **Track A's L2-UK-EN output (A.14–A.15) depends on L1-UK output (A.12) being ingested first.** That's the bootstrap loop — can't skip it.
- **No cross-track convergence required for initial ship.** Each track can reach its own "modules published" endpoint independently.

## Realistic calendar

| Week | Phase 1 | Track B+ | Track A |
|---|---|---|---|
| 1 | Steps 1.1–1.7 complete | — | — |
| 2 | — | B+.1, B+.2 canaries | A.1, A.2 control baseline |
| 3 | — | **B+.3 batch builds shipping** | A.3 (reviewer engagement), A.4 (alignment session) |
| 4 | — | B+ shipping continues | A.5–A.8 canary A/B |
| 5 | — | — | A.9 second confirmation, canary decision |
| 6+ | — | — | A.10 rubric, A.11 corpus integration, A.12 first L1-UK batches |
| 10+ | — | — | A.13–A.14 bootstrap ingestion + L2-UK-EN A1 starts |
| 14+ | — | — | A.15 A2 begins |

Net: B+ wikis/modules ship ~week 3. A1 L1-UK ships ~week 8-10. A1 L2-UK-EN (post-bootstrap) ships ~week 12-14. A2 ~week 16+.

## Current position

**← BLOCKED at Phase 1 Step 1.1 (#1337 fix).** Stage (c) of #1348 landed but references `parent_section_id` column that doesn't exist. Morning decision: dispatch Codex on #1337 to actually ship the schema.

## Tri-agent discussion outcome (2026-04-20 01:55 local, thread `c5fb1e5512ae`)

Converged round 1, both `[AGREE]` on bootstrap framing. Key findings:

### Finding 1 — Textbook grounding IS the authority layer; native review is for residual register only

**Corrected after user pushback (correct pushback).** The A1-A4 textbook corpus is already native-authored, native-reviewed, published by Ukrainian educational publishers, used in real Ukrainian schools (Большакова, Вашуленко, etc.). If retrieval grounds hard on textbooks and citations trace back, the L1-UK modules inherit source authority — they're re-indexings of authoritative content, not net-new content.

The agents' initial "per-module native admission" framing was anchored on worst-case contamination scare, not actual residual risk after machine checks apply.

**Machine checks that run pre-ingestion (no human budget consumed)**:
- VESUM verification → invalid words / forms
- Semantic Surzhyk linter (#912) → known calques + Russianism vocabulary
- Антоненко-Давидович style guide match → known Russian-through-Ukrainian constructions
- Pravopys 2019 rule check → orthography
- Citation audit → fact misrepresentation (every claim traces to textbook source)
- Immersion contract check (`config.py:215`) → unintended code-switching

Together these catch an estimated 80–90% of what a native reviewer would flag.

**Residual slice where native review adds value (10–20%)**:
- Subtle semantic calques not in Surzhyk database
- Register-level inauthenticity (grammatically correct but "doesn't sound native")
- Decolonization-framing choices (pedagogy judgments, not linguistic errors)
- Topics where textbook grounding is thin or the curriculum plan specifies something textbooks don't cover

**Revised reviewer load (final)**:

| Stage | Human review | Time |
|---|---|---|
| Canary (1 module) | Full register review + blinded A/B — validates pipeline produces acceptable native register at all | 6–8 h |
| Seed batch (3-5 modules) | Full admission review, surfaces systematic issues machine checks miss | 2–3 h |
| Rubric authorship | Reviewer distills "what machine checks are missing" from canary + seed experience. After this, most residual risk is captured by the rubric feeding back into machine checks | 2–4 h |
| Scale batches | Opt-in review only — reviewer signals "want to look at this batch" OR pipeline flags low-confidence outputs for review (thin textbook grounding, ambiguous plan specs) | ad-hoc, no mandatory cadence |

**Total A1+A2 lifetime native-reviewer commitment**: **~12–15 h, all front-loaded.** No mandatory ongoing audit rhythm.

**Design principle locked**: textbook-grounded retrieval + machine checks + citation audit = corpus admission gate. Native review calibrates the gate; it doesn't BE the gate for every module.

### Finding 2 — Curriculum plans are the immutable shared contract
`curriculum/l2-uk-en/plans/{level}/{slug}.yaml` must remain source of truth for BOTH tracks. Track A cannot invent vocabulary / grammar targets; it executes the existing A1/A2 plan specs in Ukrainian-canonical form only. Medium changes; content contract does not. Otherwise A2→B1 learner transition fractures with unresolved forward-references.

### Finding 3 — Integration-path proposal: reuse existing, don't invent (CONTESTED)
Codex: use existing `l2-uk-direct` track infrastructure rather than creating a new `l1-uk/` tree. Build new corpus `direct_beginner_modules` from validated l2-uk-direct A1/A2 output; ingest into `sources.db` as new FTS5 table + manifest entry + `track_priors.yaml` column with high prior for a1/a2 tracks, near-zero for B1+.

**Status**: contested — contradicts earlier user instruction that `l2-uk-direct` is a separate parked project. Three resolution options pending user decision (see Open Decisions below).

### Finding 4 — Parallel tracks are safe if two contracts are honored
- Corpus-eligibility / promotion rules (admission gate)
- Retrieval-surface schema (what fields sources.db exposes)

If Track A adds beginner-native corpus with prior[track][corpus] tuned to high-for-a1a2 and near-zero-for-b1+, B1+ doesn't wait or leak. Precedent: `textbook_sections` addition is structurally similar.

### Finding 5 — Linting gate
Gemini: semantic Surzhyk linter (#912) must run strictly on every L1-UK output BEFORE ingestion. Other linguistic verification (VESUM, Pravopys 2019, Антоненко-Давидович) also required, not optional.

## Open decisions for user

### D1 — Integration path (resolves Finding 3)

Three options, pick one:

| Option | What | Trade-offs |
|---|---|---|
| **D1-A** | Unpark `l2-uk-direct`, use it as L1-UK foundation | Reuses infrastructure. Reverses earlier "don't touch l2-uk-direct" instruction. Requires aligning l2-uk-direct plans with l2-uk-en A1/A2 plans. |
| **D1-B** | Create new `l1-uk/` track | Respects earlier instruction. Duplicates infrastructure (module schemas, build pipeline, ingest). Clean provenance. |
| **D1-C** (Claude rec) | Build L1-UK as shadow-mode under `l2-uk-en/` | Same plans, same schemas. Marks modules `language_variant: uk_native`. No new track, no resurrection of l2-uk-direct. Simplest. |

### D2 — Reviewer commitment (FINAL)

Total native-speaker commitment for full A1+A2 scale: **~12–15 h, all front-loaded**. Breakdown:
- Canary (1 module, register + A/B): 6–8 h
- Seed batch (3–5 modules, admission review): 2–3 h
- Rubric authorship (after seed): 2–4 h
- Ongoing scale: opt-in only, no mandatory cadence

Before canary starts, confirm with reviewer:
- Hourly rate
- Availability for front-loaded ~12-15 h over ~3-4 weeks
- Willingness to be available for ad-hoc review if the pipeline flags low-confidence outputs later

**Rationale**: textbook corpus already provides native authority. Machine checks (VESUM + Surzhyk linter + style guide + citation audit + immersion contract) cover ~80-90% of what a native reviewer would catch. Native review is for pipeline calibration and the residual register/framing slice — not for every module.

**Do NOT propose per-module admission** or ongoing ~2 h/week audit rhythms. Earlier drafts of this doc carried those estimates; they were over-engineering anchored on agent conservatism, not first-principles risk analysis.

### D3 — Plan alignment audit

Before any L1-UK authoring starts: audit A1/A2 plans under `curriculum/l2-uk-en/plans/a1/` and `a2/` to confirm they're ready to be the immutable contract. If any plans are in draft / half-baked state, those need finalizing FIRST — otherwise L1-UK authoring either blocks or produces output that has to be rewritten when the plan changes.

## Public-repo name policy

- **Never** reference real people (project contributors, teachers, reviewers) by name in GH issues, commits, PRs, or any file tracked under `docs/` that lands on the public site.
- Session-state notes and memory files that are local-only (untracked) may use names for operational clarity.
- This roadmap intentionally uses generic terms ("native-speaker reviewer", "user") rather than identifying individuals.

## Change log

- **2026-04-20 initial**: two-track design agreed with user; corpus-bootstrap reframe of L1-UK pivot captured (user clarification supersedes earlier "pedagogy pivot only" framing); Phase 1 engineering blockers identified; tri-agent discussion round 2 fired for corpus-integration design.
