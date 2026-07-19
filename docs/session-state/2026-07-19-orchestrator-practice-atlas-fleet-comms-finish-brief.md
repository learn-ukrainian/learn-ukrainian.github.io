---
date: 2026-07-19
session: "Grok orchestrator: practice chrome + paronyms + sentence inventory + textbook atlas promote + fleet-comms Sol phases 0–5 finish + warn-not-reject PR CF policy. Session ended clean; durable handoff written after chat wrap-up."
status: finish-wave-closed-session-handoff
main_sha: b845eb95b5
main_green: yes (wave PRs merged with CF review + CI)
working_tree_dirty: no (this brief ships via PR)
session_close: 2026-07-19
driver: grok (orchestrator seat)
---

# 2026-07-19 — Practice + atlas + fleet-comms finish wave

**THE ONE NEXT ACTION:** resume product queue on practice/atlas depth — do **not** re-open closed finish work. Preferred order: (1) spot-check live daily examples after #5487 inventory, (2) #5478 textbook re-enrich backlog when product capacity returns, (3) standing atlas/practice epics #4387 / #4700 / #4707, (4) deeper multi-surface sentences (#3797) only if daily still thin.

## TL;DR

This session closed a coordinated **finish wave** across practice UI, atlas textbook promotion, shared sentence inventory for daily practice, and fleet-comms isolation (Sol phases 0–5 + policy fix). User priority: activity/practice over textbook re-enrich; finish everything; always run cross-family `review-pr` before merge; end session with a durable handoff (this file — chat wrap-up alone was not enough).

## ✅ Merged this session (finish wave)

| PR | What landed |
| --- | --- |
| **#5474 / #5475** | Fleet doctrine + living role scorecard; Haiku recon seat documented |
| **#5477** | Textbook-curated bulk promote (#3934): promote then prune unenriched so richness floor stays ≥40% (~17.7k published / ~42% enrichment). Unenriched held heads → backlog **#5478** |
| **#5479** | Practice full-locale session chrome residuals (#5355): dual chrome (`data-chrome-locale`), A1 bilingual vs full EN/UK switch, ChromeText / PracticeChromeLabel |
| **#5480 / #5489** | Paronym pairs expanded (#4506) 7→20; Ukrainian apostrophe fix `пам’ятка` (not `пам-ятка`) |
| **#5487** | Source-backed sentence inventory for daily practice — generator + `lexicon-sentence-inventory.json`; corpus/ULP/textbook-first (not Clozemaster import); ~287/300 example coverage on daily pool overlay |
| **#5488** | Fleet-comms Phase 4–5 residuals: formal PR CF review requires `review-pr` / target (#5485/#5486) |
| **#5491** | Policy fix: fat formal PR CF ask without `review-pr` target is **warn-not-reject** (size caps still fail-closed) |

Also on main near session close (adjacent lanes / prep track, not this driver’s exclusive work): #5463 track-completion bound repair, #5464 practice CTA, #5465 thin review verdicts, #5466 daily example sentences UI, #5473/#5476/#5481/#5482/#5490 curriculum preparation / readiness stack.

## ✅ Issues closed this session

- **#5483** — sentence inventory ASAP task (shipped via #5487)
- **#5484** — [EPIC] fleet-comms isolation & thin-review program Sol phases 0–5 (CLOSED)
- **#5485 / #5486** — formal PR CF + review-pr residuals (shipped #5488)
- **#4506** — paronym expansion (shipped #5480 + apostrophe #5489)

## Product / architecture decisions (carry forward)

1. **Sentences:** multi-surface inventory, not Clozemaster product import. Prefer textbooks, ULP, Tatoeba/corpus already in repo. Daily practice consumes `example` / `exampleEn` from inventory overlay.
2. **Textbook atlas:** publish only enrichment-safe slice; never lower richness floor. Re-enrich is a separate tracked backlog (#5478), not a silent republish of thin heads.
3. **Practice chrome:** A1 keeps English scaffolding by design; full-locale switch must not double-English or leave residual EN chrome.
4. **Fleet-comms:** pointer-only / caps / `review-pr` / `publish-review-verdict` path. Formal PR CF asks that skip `review-pr` **warn** (steer agents) rather than hard-reject wasteful work; absolute size caps remain hard fail-closed.
5. **Reviews:** discussion/panels do **not** satisfy the merge gate. Cross-family `review-pr` every merge. Arm auto-merge after CF gate pass.
6. **Orchestrator posture:** drive, don’t babysit; ask only when blocked; prefer activity/practice product work over textbook re-enrich unless user reprioritizes.

## Key paths (if resuming code)

| Area | Paths |
| --- | --- |
| Practice chrome | `src/…/LexiconPractice.tsx`, practice chrome helpers (`chrome.ts` / labels) |
| Sentence inventory | `scripts/…/generate_sentence_inventory.py`, published `lexicon-sentence-inventory.json` (or site data path from #5487) |
| Paronyms | `paronym_pairs.yaml` (apostrophe-correct slugs) |
| Fleet review safety | `scripts/ai_agent_bridge/_review_safety.py`, `_review_pr.py`, `_review_verdict.py` |
| Fleet docs | `docs/…/fleet-shared-doctrine.md`, role scorecard |
| Textbook promote | atlas promote + prune-to-floor pattern from #5477 |

Exact filenames: verify on main with `git show` / PR files if paths drifted — do not invent.

## ▶ NEXT QUEUE

### Do soon (product)

1. **Live spot-check** daily practice examples after #5487 inventory (UI already takes examples; confirm variety/quality on a few heads).
2. **#5478** — re-enrich ~10.7k held textbook heads when enrichment capacity is intentional (do not rush into another bulk promote).
3. **Atlas/practice depth** — #4387 practice hub, #4700 / #4707 standing epics; #5411 needs_review glosses (838) via enrich/anchor-fill, not raw inject.
4. **#3797** — deeper Tatoeba / multi-surface only if daily still under-served after inventory.

### Infra / fleet (when free, not session-critical)

- #5392 large ask reply truncation (file-side channel)
- #5400 worktree base_sha race
- #5366 rollover exact-selector CI flake
- #5326 Kimi lane onboard (if still open)
- Curriculum preparation residual: #5472 prove bounded packets / hash reuse / no singleton review loops

### Hygiene

- Leftover dispatch worktrees from finish wave (k3 design, etc.) — reap when idle
- No open finish-wave PRs expected; if any draft limbo appears, close or finish — do not leave limbo

## Operating rules (unchanged, re-asserted)

- Implementation only in `.worktrees/dispatch/<agent>/<task>/`
- `.venv/bin/python`; never `sys.executable`
- No `.python-version` / linter config edits; no status/audit artifact dumps in code PRs
- `X-Agent` trailer on every commit
- CF review before merge; auto-merge arm after gate

## Handoff layers

| Layer | Path | Notes |
| --- | --- | --- |
| **This brief** | `docs/session-state/2026-07-19-orchestrator-practice-atlas-fleet-comms-finish-brief.md` | Durable cross-agent record (MD only) |
| **Codex orchestrator pointer** | `docs/session-state/codex-orchestrator-handoff.md` | Updated to point here + next focus |
| **Thin pointer** | `docs/session-state/current.orchestrator.md` | Still points at codex-orchestrator-handoff.md |
| **Local machine state** | `.agent/*-thread-handoff.md` | Gitignored; not authoritative across machines |

## Session close note

User asked to end the session; first reply was chat-only wrap-up. User correctly asked whether the durable handoff was written — it was **not**. This brief + orchestrator pointer update close that gap.
