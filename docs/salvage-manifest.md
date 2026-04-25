# Salvage Manifest — Curriculum Reboot (#1577)

> **Status: DRAFT — written 2026-04-25, awaiting user + 3-agent confirmation.**
> Phase 1 of EPIC #1577. This doc inventories every artifact in the repo
> and every open GitHub issue with its disposition under the reboot.
>
> Three buckets for artifacts: `keep` / `source-only` / `discard`.
> Four buckets for issues: `reboot-blocker` / `mvp-deferred` / `backlog` / `close-stale`.

---

## 1. Repository artifact inventory

### KEEP (preserved as-is, do not redo)

| Artifact | Why preserved |
|---|---|
| `curriculum/l2-uk-en/plans/` (all 218: 55 A1, 69 A2, 94 B1) | State Standard 2024 grounded; carefully designed; encodes A2→B1 immersion ramp deliberately. Per 3-agent consensus: plans are sacred, no redesign. |
| `curriculum/l2-uk-en/curriculum.yaml` (module manifest) | Source of truth for module ordering and slug mapping. |
| `data/sources.db` + VESUM (`data/vesum.db`) + dictionaries (СУМ-11, Грінченко, Балла, Антоненко-Давидович, Фразеологічний) | 24K textbook chunks + 409K lemmas + 6.7M forms. Foundational. |
| `data/canonical_anchors.yaml` | Decolonization-critical fact registry. |
| `wiki/` (existing locked review files in `wiki/.reviews/`) | Already-vetted output. Per Codex: "salvage what's locked." |
| `starlight/` site components | The site IS the source of truth for lesson structure (theory + vocab/flashcards + workbook + resources/citations). |
| `docs/decisions/` ADRs + decision journal | Architectural decisions with their expiry dates. Living governance. |
| `docs/best-practices/` (selected — see review in Phase 2) | Most still relevant; a few will be amended for new pipeline. |
| `scripts/audit/config.py` (level configs, immersion rules, word targets) | Encodes the level→config mapping. Plan-driven immersion lives here. |
| `scripts/build/contracts/module-contract.md` | Contract framework still valid; specific contract content gets refreshed. |
| `scripts/ai_agent_bridge/` (the bridge + channel system) | Multi-agent infrastructure. Critical for the new consultation rule. |
| `scripts/agent_runtime/` | Universal adapter layer for agent CLI invocations. |
| `scripts/monitor_client.py` + Monitor API server | State + scoped queries. |
| `tests/` framework | pytest setup, fixtures, golden corpus structure. |
| `memory/MEMORY.md` + topic files | Personal context for me; private. NOT redone. |
| `.mcp/servers/sources/` MCP server | sources.db query layer. |

### SOURCE-ONLY (kept as reference, NOT injected into new pipeline as-is)

| Artifact | Why source-only |
|---|---|
| `scripts/build/v6_build.py` | Reference for what the V6 pipeline DID. Not the implementation that ships. New pipeline borrows working pieces (notably the `{IMMERSION_RULE}` injection at writer + reviewer, lines 4695 / 7996). |
| `scripts/build/phases/v6-write.md` | Reference for what NOT to do (latent кіт example, missing North Star preamble, mixing structural + pedagogical rules). New writer prompt re-authored from scratch with North Star preamble. |
| `scripts/build/phases/v6-activities.md` | Same — reference for what to avoid. New activity prompt: stripped, lemma-whitelist constrained. |
| `scripts/build/phases/v6-review/*.md` | Reference for the 9-dim breakdown. New reviewer architecture: tiered (Python QG + LLM QG with no overlap). |
| Existing curriculum `*.md` modules in `curriculum/l2-uk-en/{level}/` | Reference for the published-style output. Re-generated through new pipeline. User's manual a1/1 patches preserved as quality reference. |
| `docs/archive/pipeline-v6-design.md` | Historical design doc. |
| Bug autopsies in `docs/bug-autopsies/` | Lessons learned. Read before similar bugs. |

### DISCARD (rotten architectural layers — replaced wholesale)

| Artifact | Why discarded |
|---|---|
| V6 convergence loop (the patch / scoped-rewrite / human-review tier system) | Autonomous patching has empirically failed to converge. New pipeline is linear: deterministic check → if Python can't auto-fix, fail fast → if LLM review fails, scoped regen of THAT section OR human review. NO infinite repair. |
| 9-dim weighted reviewer architecture (with binary `min(dim) ≥ 8` gate) | One LLM call per dim, weighted average; allows score bleed and compensation. Replaced by Python QG (objective, deterministic) + LLM QG (pedagogical only, no overlap). |
| The reviewer-as-fixer `<fixes>` find/replace contract | Architecturally correct intent; in practice, the `<fixes>` only handled trivial cases and the bouncebacks killed convergence. New pipeline: reviewer can rewrite tier-2 prose directly when it has full module loaded. |
| The "every dim < 8 blocks release" gate semantics | Replaced by tiered gates: tier-1 wrong-teach blocks; tier-2 ships annotated; tier-3 logged. (The user articulated this; both Codex and Gemini endorsed.) |

### Personal-context items NOT to commit (security)

| Item | Disposition |
|---|---|
| User's two private-contact teacher names | Stay in `memory/MEMORY.md` (private to me). MUST NOT appear in any committed curriculum file, wiki article, design doc, or session-state file. Phase 2 audit task: grep for these names across `curriculum/`, `wiki/`, `docs/`, plans, knowledge packets and replace personal references with role descriptions ("native-speaker reviewer", "school teacher"). Generic Ukrainian first-name uses in dialogues are fine — they're common names. |

---

## 2. GitHub issue triage (62 open as of 2026-04-25 ~19:30 UTC)

### `reboot-blocker` (19) — Phase 5+ depends on these

| # | Title (truncated) |
|---|---|
| 1573 | ingest_ukrainian_wiki.py: bulk-dir bypass citation_audit |
| 1571 | ukrainian_wiki: cross-track slug collisions silently drop |
| 1570 | ingest_ukrainian_wiki.py silently ingests nothing on top-level |
| 1569 | Multi-agent writer support in scripts/wiki/compile.py |
| 1567 | Hungarian-language contamination in textbooks corpus |
| 1563 | Restore + harden data/sources.db after Apr 25 wipe |
| 1553 | Wiki retrieval overhaul: chunked re-encode |
| 1377 | Wiki corpus expansion — B1, B2, C1, C2 + seminar |
| 1373 | A.6 — Ingest 55 Ukrainian-canonical A1 wikis |
| 1351 | Diagnostic: rank-order test for pedagogical-grade-appropriate retrieval |
| 1350 | Ingest Bright Kids Ukrainian Online School |
| 1333 | Corpus gap analysis + Ukrainian-source ingestion roadmap |
| 1201 | Release: v1.0 — A1+A2+B1 launch with 'What's New' |
| 1198 | Quality evaluation: human baselines + style guide for editors |
| 1149 | Site design: audit and align Starlight with POC specs |
| 1067 | EPIC: Frontend redesign — adopt POC lesson design |
| 1051 | Pedagogy Pattern Library — exercise patterns by grammar topic |
| 1012 | Design: Lesson page layout — 4 tabs, inline exercises, flashcards |
| 705 | T3.5: Vocabulary progression audit A1→C2 |

### `mvp-deferred` (36) — valid post-A1+A2+B1 ship

Seminar tracks (10):
**1141, 1140, 1139, 1137, 1135, 1134, 1133, 1132, 658, 497**

B2 / C1 / C2 (4):
**1199, 1200, 303, 1196**

PRO tracks (1): **429**

Domain (STEM/MED/IT) tracks (12):
**859, 860, 861, 862, 863, 864, 865, 866, 867, 868, 869, 870**

Other post-MVP enrichment (9):
**1242, 1197, 1195, 1008, 854, 715, 675, 676, 499**

### `backlog` (6) — real but no near-term plan

| # | Title |
|---|---|
| 1481 | Targeted test selection on PRs: pytest-testmon/picked |
| 1480 | Local Docker-pytest: CI-parity feedback loop |
| 1398 | Wire `--effort` for Gemini once gemini-cli exposes the flag |
| 1334 | [PARKED] Reviewer incentive inversion |
| 1082 | Coding: frontend test coverage — 4/50+ components |
| 634 | Monolingual Lexicon Builder |

### EPIC + sub-issues (3) — unlabeled, navigation-only

- #1577 — EPIC: Curriculum reboot
- #1578 — Phase 0: North Star + Lesson Contract
- #1579 — Phase 1: Salvage inventory + 62-issue triage

### `close-stale` (0)

No issues confidently classified as fully stale. The candidates I considered (705 vocab progression A1→C2, 676 monolingual toggle C1+, 1008 V6 visual QA) all turned out to map to real future work — relabeled rather than closed.

### Already closed in this session (13, V6-loop)

#1550, #1525, #1526, #1451, #1365, #1241, #1315, #1286, #1189, #1142, #1537, #1435, #1344 — all closed with comments pointing to #1577.

---

## 3. Open questions for 3-agent review (Phase 1 sign-off)

Before this manifest commits, Codex + Gemini should weigh in on:

1. **Are any of the `mvp-deferred` 36 actually `reboot-blocker`?** Likely candidates: #1196 (STEM A/B test framework — could the framework be needed earlier?); #1195 (seminar A/B — same).
2. **Are any of the `reboot-blocker` 19 actually `backlog`?** Likely candidates: #1051 (Pedagogy Pattern Library — could be Phase 7 prerequisite or later); #705 (vocab progression audit — could be Phase 8 or later).
3. **Is anything in `keep` actually `source-only` or `discard`?** Specifically: existing curriculum modules in `curriculum/l2-uk-en/{level}/` — keep as quality reference, or discard since they'll be regenerated?
4. **Personal-name audit task — is the scope right?** Should it be Phase 1 or later?

---

## 4. What this manifest does NOT cover

- Per-script audit of `scripts/build/` (Phase 2 work — config audit + pipeline plumbing review)
- Per-prompt audit of `scripts/build/phases/` (Phase 6 work — prompt re-authoring)
- Per-wiki audit of `wiki/` (Phase 5 work — slice for A1+A2+B1)
- Per-test audit of `tests/` (Phase 8 work — QG re-implementation)

These are intentionally deferred to their phase owners. Phase 1's job is the high-level disposition; the deep audits happen later.

---

**Next action:** user reads this; flags anything mis-bucketed; commits, OR requests a 3-agent consultation on the open questions in §3 before commit.
