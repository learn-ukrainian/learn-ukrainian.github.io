# Execution Plan — Corpus Bootstrap (A1/A2) through Phase G

**Filed:** 2026-04-22
**Status:** DRAFT — review and approve before executing
**Supersedes:** nothing (first end-to-end execution plan since strategic audit)
**Related:** `docs/architecture/2026-04-21-pilot-readiness-audit.md`, `docs/architecture/ROADMAP-two-track-build-plan.md`, `docs/experiments/2026-04-21-writer-bakeoff-a1-m03.md`

## TL;DR

We are here:
- Bakeoff for UK-native writer running (5 agents on A1 M03)
- Plan fork for A1 M03 shipped (Codex's version, branch `codex/fork-l1uk-codex`)
- 48-item strategic audit identified P0-P2 problems across plans, wikis, review pipeline

We need to go here (end state):
- `l1-uk` A1 + A2 modules built, reviewed, ingested into corpus
- `l2-uk-en` A1 + A2 modules rebuilt retrieving from enriched corpus (Phase G)
- Plans clean, wikis clean, pipeline healthy

This doc sequences the work. Every phase has a decision gate. Nothing in a later phase starts until its predecessor gate passes.

---

## Phase 0 — Pick writer and reviewer

### 0A — UK-native writer bakeoff [IN FLIGHT]

- 5 writers × A1 M03 `special-signs` → 5 outputs
- Round-robin cross-review (20 reviews) on the 6-axis rubric
- Aggregate scores decide **F4 primary writer for l1-uk track**
- **Gate:** winner identified with margin ≥0.3 aggregate over rank 2, OR tiebreaker on A1 M02 runs

### 0B — Reviewer identification (derived from 0A data)

- No separate bakeoff needed. The 20 cross-reviews in 0A produce per-reviewer calibration data.
- Metrics: catch rate (fraction of real issues each reviewer flagged), false-authority rate (fabricated VESUM citations etc.), evidence specificity (quotes with line numbers vs generic praise)
- **Gate:** one or two reviewers emerge as clearly stronger. If none clearly wins, default to cross-agent pair (two highest-ranked by catch rate) for production.

### Bakeoff review vs production review — not the same thing

- **Bakeoff** (Phase 0A) uses **round-robin** review: every writer reviewed by every other writer, no self-review. 4 reviews per output × 5 outputs = 20 reviews. This is for MEASUREMENT.
- **Production** (Phases 3, 5, 6, 7, 8) uses **single cross-agent review**: one writer produces, one reviewer scores. Not round-robin. If we tried round-robin at production scale we'd multiply review cost by 4× for no measurement benefit.
- **Exception:** if Phase 0B can't identify a clear winning reviewer, production uses a **2-reviewer pair** (two highest-ranked models, no self-review on either). Aggregate = mean of 2 scores. Still 2× not 4× the cost of single reviewer.

### What if Phase 0A doesn't converge?

- No writer scores ≥ 7.5 aggregate → **plan or prompt is the problem, not the writers.** Escalate: re-audit plan with Gemini+Codex linguistic sweep, tighten system prompt, re-run bakeoff on a different A1 canary (M02 `reading-ukrainian` as tiebreaker fixture).
- Rank 1 and rank 2 within 0.3 → **tiebreaker run** on M02 with the two tied writers only (not all 5).
- All writers produce similar mid-range scores (6.0-7.5, no clear winner) → **the task is underspecified**, not the writer. Pause, revisit the Ukrainian Module Author prompt, bring user into a prompt-engineering pass.

### 0C — English-scaffolded writer bakeoff [FOLLOW-UP]

- Same 5 writers, different system prompt (English-scaffolded output), same fixture (M03) or a different canary slug
- Decides **F4 primary writer for l2-uk-en track**
- Runs after 0A completes and results analyzed
- **Gate:** winner for English track identified. May or may not match UK-native winner.

---

## Phase 1 — Plans audit + fork

Plans are the source of truth. Contaminated plans → contaminated modules forever. This phase cleans the plan contracts BEFORE any module build.

### 1A — Structural sweep (Codex)

- **D1** Latin M## cross-refs (`#1392` in flight on `codex/codex-1392-plan-latin-fix` — review + merge, or rescope if findings overlap with below)
- **D3** Homoglyph scan (Latin I in Ukrainian `ЗМI`, other invisible Latin-class intrusions)
- **D5** Structural duplicates (e.g. `a2-067` pulling from `a2-09`)
- **D7** Inconsistent M## replacement formatting (per PR #1393 comments: `модуль №48`, `у модулі 2`, `№15–20` — pick one)
- Output: clean plans on main branch

### 1B — Linguistic sweep (Gemini + Codex cross-review)

- **D2** Context-blind `ОБОВ'ЯЗКОВО` patterns across all 183 A1/A2/B1 plans (the `А у тебе?` class)
- **D4** Calque sweep (30-sample Gemini found 5; extrapolate to full corpus with tool-grounded verification)
- **D6** Russian contamination audit (MCP-tool-grounded: VESUM + Антоненко-Давидович + Правопис, not eyeballing)
- **D7 (content)** English-gloss leakage in Ukrainian prose (dark-horse finding from yesterday)
- Output: clean plans on main branch with Gemini-flagged, Codex-verified fixes

**Gate for Phase 1:** all 183 A1/A2/B1 plans pass a final automated scan (Latin-char regex, homoglyph, English-word counter, Russianism stoplist).

### 1C — Fork A1+A2 plans to l1-uk/ (batch)

- Extend the `special-signs` pattern to all 55 A1 + 69 A2 plans = **124 forks total**
- **Do NOT 3-way bakeoff each slug.** That was for measurement on one slug. Now we have data — use the winning fork agent directly.
  - Based on preview (Codex best on `special-signs`): Codex is default fork agent. Revise after Phase 0A if a different winner emerges for write-quality work.
- **Batch strategy:**
  - 1 brief file, templated with `{slug}` — one per dispatch, parallelized 10 at a time (respects Codex rate limits, each fork ~5 min → 10 parallel × 13 batches ≈ 2-3 hours total wall-clock)
  - Each dispatch: own worktree (`.worktrees/fork-{level}-{slug}/`), own branch, pushed to origin, no PR
  - Output: `curriculum/l1-uk/plans/{level}/{slug}.yaml` on the branch
- **Review:** 1 cross-agent reviewer per fork (Gemini reviewing Codex output, same brief as plan-fork review we already ran) — parallel, 10 at a time
- **Merge strategy:** after all 124 forks are reviewed and PASS, merge all 124 branches onto a single integration branch `integrate/l1uk-plans-a1a2` in one pass. Then cherry-pick to main.
- **Fallback:** any fork failing its review gets ONE retry via the same agent with reviewer's findings; second failure → escalate to user.

---

## Phase 2 — Wikis audit + selective rewrite (A1/A2 only)

B1+ and seminar wikis are NOT touched. Rich corpus grounding makes their current quality acceptable.

### 2A — Metadata retrofit (`#1398`)

- Add `generated_by_model` field to wiki frontmatter
- Backfill what we can from logs / commit history
- Flag Flash-written wikis for rebuild queue

### 2B — Quality audit of A1/A2 wikis

- Identify L2-English framing contamination (like the «Типові помилки L2 (англомовні учні)» section we found in `special-signs` wiki)
- Identify Flash-written wikis
- Identify wikis with pedagogical thinness (2-dim review below threshold)

### 2C — Selective rewrite

- Flagged wikis rewritten by Phase 0A winning writer
- Cross-agent review per new wiki
- Commit directly to main after review pass

**Gate for Phase 2:** A1/A2 wikis have zero L2-English framing, zero Flash-written flags, 2-dim review ≥8 on all.

---

## Phase 3 — l1-uk module build (A1 first, then A2)

### 3A — A1 batch (55 modules)

- Writer: Phase 0A winner
- Reviewer: Phase 0B winner (or round-robin if 0B inconclusive)
- Output destination: ADR-008 decision — Starlight collection `docs-native/a1/` OR equivalent
- Batch runs user-paced, monitored via Monitor tool

### 3B — A1 gate

- All 55 modules pass audit (word count, Russianism scan, citation audit, immersion contract)
- Spot-check review on random 10 modules against textbook grounding
- Optional: Alona opt-in review on interesting-case queue

### 3C — A2 batch (69 modules)

Same as 3A for A2.

### 3D — A2 gate

Same as 3B for A2.

---

## Phase 4 — Corpus integration

### 4A — Ingest l1-uk modules into sources.db

- New corpus table `ukrainian_native_a1a2` (per ROADMAP section 4a)
- FTS5 index + manifest + track_priors update (`a1`/`a2` prior high, `b1+` prior near-zero)
- Infrastructure work: Codex

### 4B — Retrieval validation

- Run retrieval playback on a sample of l2-uk-en A1/A2 slugs
- Confirm new corpus surfaces as expected in retrieval
- Concept recall on A1 test set improves (baseline = 6/10 per #1340)

**Gate for Phase 4:** retrieval playback shows ≥8/10 concept recall on A1 test set; new corpus discoverable from `search_sources`.

---

## Phase 5 — Phase G: deliver A1/A2 immersed + B1/B2 full Ukrainian (first shippable product)

**This is the first public-shippable delivery of the project.** Four levels land together as a coherent learner progression.

### 5A — Writers decided

- A1, A2 (immersed): Phase 0C English-scaffolded winner
- B1, B2 (full Ukrainian): Phase 0A UK-native winner (no English scaffolding at B1+; CEFR-appropriate)
- These may or may not be the same model

### 5B — Rebuild l2-uk-en A1 immersed (55 modules)

- Writer: Phase 0C winner
- Retrieval: textbooks + A1 wikis + l1-uk corpus (Phase 4 integration)
- Cross-agent review
- Destination: `starlight/src/content/docs/a1/*.mdx` (existing English-track path)
- "Immersed" = progressively heavier Ukrainian as the learner advances; English scaffolding present but shrinking

### 5C — Rebuild l2-uk-en A2 immersed (69 modules)

Same as 5B for A2.

### 5D — Build B1 full Ukrainian (94 modules)

- Writer: Phase 0A winner (Ukrainian-native prose — B1 learners can read it)
- Retrieval: textbooks + B1 wikis (rich grounding, no L1-UK corpus needed)
- Cross-agent review
- Destination: `starlight/src/content/docs/b1/*.mdx`

### 5E — Build B2 full Ukrainian (93 modules)

Same as 5D for B2.

### 5F — Ship to public site (incremental, recommended)

**Option I — incremental ship (recommended):**
1. Ship A1 first when 5B passes its gate → public can see the A1 immersed track
2. Ship A2 when 5C passes → A1→A2 learner path complete
3. Ship B1 when 5D passes → A1→A2→B1 path
4. Ship B2 when 5E passes → full Phase G

Advantage: each level's rollout is isolated, easier to diagnose site issues, user gets early-audience feedback. Disadvantage: 4 deploys instead of 1.

**Option II — big-bang ship:**
All 4 levels land together after 5E. Advantage: one coherent launch moment. Disadvantage: if anything breaks, 4-level scope to debug.

**Default: Option I.** Override if you want a launch moment.

**Gate for Phase 5 (Phase G):** four levels live on `learn-ukrainian.github.io`, audit gates all GREEN, A1→A2→B1→B2 progression tested end-to-end. **This is the project's first public shippable product.**

### What if Phase 4 retrieval validation fails?

- Baseline = 6/10 concept recall on A1 test set. Target = ≥8/10 after l1-uk corpus ingestion.
- If result is 6-7/10: l1-uk corpus didn't help. Investigate: is the new corpus's FTS5 index populated? Are `track_priors` tuned right? Retrieval playback should show the new corpus's chunks surfacing.
- If result is <6/10: l1-uk corpus may be HURTING retrieval (noise). Roll back the track_priors change until diagnosed.
- Do NOT proceed to Phase 5 until gate passes. Phase 5 depends on enriched retrieval.

---

## Phase 6 — C1 (full Ukrainian)

Starts after Phase G ships.

### 6A — C1 plan research + wiki compile

- 132 slugs, currently 0 researched
- Per-slug research → plan → wiki, same pipeline as B1/B2
- Phase 0A UK-native winner on wikis (B1+ already grounded in Ukrainian sources)

### 6B — C1 module build

- 132 modules, full Ukrainian
- Writer + reviewer: Phase 0A winners
- Ship to `/c1/*`

**Gate:** C1 live, audit green.

---

## Phase 7 — Seminars (all seminar tracks)

Tracks: HIST (140), ISTORIO (136), BIO (180), LIT (232), OES (102), RUTH (115), and 8 LIT sub-tracks (~228 combined). ~1133 total modules across seminar profile.

### 7A — Seminar writer bakeoff

- Seminars need different skill than core: cultural/historical nuance, literary register, decolonized framing of contested figures
- 5-writer bakeoff on one canary (e.g. one HIST on Kyivan Rus or one BIO of a Ukrainian figure)
- Decides seminar-track writer, may differ from Phase 0A/0C winner

### 7B — Seminar batch build

- Per-track batches, user-paced
- Fact-checking critical (see memory: Ukrainian canon guardrails — no Bulgakov-as-Ukrainian-canon, verify figures via Wikipedia/sources MCP)

### 7C — Seminar ship

- Per-track Starlight sections
- Incremental GH Pages deploys

**Gate:** all seminar tracks live, audit green.

---

## Phase 8 — C2 (full Ukrainian) — last

### 8A — C2 plan research + wiki compile

- 110 slugs
- Same pipeline as C1

### 8B — C2 module build

- 110 modules, full Ukrainian, C2 register
- Writer + reviewer: Phase 0A winners (or escalate to seminar-bakeoff winner if C2 shows similar cultural-nuance demand)

**Gate:** C2 live. Project reaches full A1→C2 + seminars coverage.

---

## Dependency graph (compressed)

```
Phase 0A (UK-native writer bakeoff) ──┬─→ Phase 0B (reviewer analysis, derived)
                                      ├─→ Phase 1C (plan fork needs writer)
                                      ├─→ Phase 2C (wiki rewrite needs writer)
                                      └─→ Phase 3 (l1-uk module build)
                                                   ↓
                                              Phase 4 (corpus integration)
                                                   ↓
                                              Phase 0C → Phase 5 (Phase G: A1/A2 immersed + B1/B2 full UK)
                                                                  ↓
                                                             Phase 6 (C1)
                                                                  ↓
                                                             Phase 7 (seminars, may need sub-bakeoff 7A)
                                                                  ↓
                                                             Phase 8 (C2, last)

Phase 1A, 1B ──→ Phase 1C ──→ Phase 3 (clean plans before build)
Phase 2A, 2B ──→ Phase 2C ──→ Phase 3 (clean wikis before build)
```

**Delivery order:** Phase G (A1+A2+B1+B2) is the first public shippable product.  
Then C1 → seminars → C2 in sequence. Project complete at Phase 8 gate.

---

## What runs in parallel right now (while Phase 0A bakeoff runs)

No bottleneck on waiting. Things we can do:

1. **Phase 1A** structural sweep (Codex) — scope tickets for D3 homoglyph, D5 structural-dupe, D7 format-inconsistency
2. **Phase 2A** metadata retrofit (Codex) — `#1398` infrastructure
3. **Phase 1B** dispatch Gemini on the D2/D4/D6 audit (parallel, doesn't need bakeoff winner)
4. **Draft Phase 1C brief** for "fork all A1/A2 plans" (template from `special-signs` fork)

What we should NOT do:
- Start any module build before Phase 0A gate passes
- Rewrite wikis before Phase 0A winner known
- File issues for Phase 3+ before dependencies resolve

---

## Ownership summary

| Phase | Owner |
|---|---|
| 0A, 0B, 0C | Claude (drafting briefs, firing dispatches, aggregating results) |
| 1A (structural plan sweep) | Codex |
| 1B (linguistic plan sweep) | Gemini + Codex cross-verify |
| 1C (plan fork) | Phase 0A winning writer |
| 2A (metadata retrofit) | Codex |
| 2B (wiki audit) | Gemini (linguistic) + Codex (L2-framing pattern match) |
| 2C (wiki rewrite) | Phase 0A winning writer |
| 3 (module build) | Phase 0A winning writer + Phase 0B winning reviewer |
| 4 (corpus integration) | Codex |
| 5 (Phase G rebuild) | Phase 0C winning writer + reviewer |
| P1, P2, P3 (B1+/seminars) | Phase 0A/0C winners (or separate seminar winner from P2) |

User: approves phase gates, opens Alona's opt-in queue, ships public site.
Claude: orchestrates, files no GH issues without approval, writes briefs, aggregates results.

---

## Open questions for approval

1. **Approve the sequence?** Any phase out of order?
2. **Parallel work right now (while 0A runs):** any of the 4 items above you want me to dispatch? (1A scope, 2A #1398 infrastructure, 1B Gemini audit, 1C brief draft)
3. **Cadence for decision gates:** do you want me to file GH issues at each gate, or keep it in this doc until end?
