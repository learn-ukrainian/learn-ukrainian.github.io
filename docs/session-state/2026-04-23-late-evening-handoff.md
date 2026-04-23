# Session Handoff — 2026-04-23 late evening

> **This session shipped a lot.** EPIC #1451 Phase 3 fully closed. Wiki-writer
> correctness fixes end-to-end on main. 10 PRs merged. 2 Codex Phase 1
> dispatches running now. Comprehensive alignment-pipeline audit + action plan
> documented.
>
> **Read this before doing anything else on return.**

---

## What landed on `main` this session (chronological, newest first)

| Commit | What |
|---|---|
| `4b5c80a329` | docs(briefs): Phase 1 alignment-manifest + sidecar-freshness dispatch briefs |
| `d9d60ec805` | feat(plan): `dialogue_situations[].turns:` convention + a1/colors turns (#1458) |
| `22dd27cfed` | Backfill wiki source attribution metadata (#1445) |
| `e737246836` | fix(wiki): route textbook_sections through attribution — close #1434 (#1450 Fix 1) (#1466) |
| `e0154d4fe3` | fix(pipeline): kill function-word `_extract_terms` + add Teacher-voice prompt anchor (#1457) (#1467) |
| `c1ba9e8a25` | fix(wiki): disambiguate chunk-ID label — strip S-prefix (#1465) |
| `136db11268` | fix(wiki): strip Gemini MCP warning + collapse duplicate generated_by_model (#1442) |
| `00eec72a8b` | docs(briefs): 4 dispatch briefs for EPIC #1451 Phase 3 (3× Codex, 1× Gemini) |
| `a03d30fff1` | feat(quality): review-and-lock `how-many` wiki + plan (#1446) |
| `4aa923c167` | feat(quality): review-and-lock `what-is-it-like` wiki + plan (#1444) |
| `03f30af7b0` | feat(quality): review-and-lock `things-have-gender` wiki + plan (#1443) |
| `e7d57180d3` | diagnostic: what Gemini needs to write wiki sources correctly (#1450) |
| `4c13d0a8c9` | diagnostic: a1/colors Opus R1 three-dim root cause (#1449) |
| `a8220a2b75` | feat(discipline): canonical-anchor registry + citation-bound prompts (#1447) |
| `b848b7aba1` | fix(build): preserve Cyrillic й/ї through NFKD (#1448) — load-bearing |
| `163273b8cd` | docs(alignment): audit + EPIC + colors rebuild plan (#1451) |

**14 PR merges + 2 in-session commits.** Zero open PRs.

## EPIC #1451 status

| Phase | Status |
|---|---|
| Phase 0 — Merge queue | ✅ complete |
| Phase 1 — Runtime alignment contract | 🔄 **2 Codex dispatches running** (#1452, #1453) |
| Phase 2 — Collapse split-brain config (#1454, #1455, #1456) | ⏳ not started |
| Phase 3 — Pipeline + plan mechanism fixes | ✅ **ALL 4 CLOSED** (#1434, #1457, #1458, #1459) |
| Phase 4 — Invariant tests (#1460–#1464) | ⏳ not started |
| Phase 5 — Colors rebuild | ⏳ **now unblocked** (awaiting Phase 1 optionally) |

## Currently running (DO NOT disrupt)

### Codex dispatches — Phase 1 of EPIC #1451

Both fired at 2026-04-23T15:35 UTC, parallel worktrees on `origin/main`.

| Task | Issue | Status | Worktree |
|---|---|---|---|
| `codex-1452-alignment-manifest` | #1452 P1-A | `running` | `.worktrees/codex-1452-alignment-manifest` |
| `codex-1453-sidecar-freshness` | #1453 P1-B | `running` | `.worktrees/codex-1453-sidecar-freshness` |

**Typical Codex dispatch lands a PR in 10-20 min.** Check status:

```bash
.venv/bin/python scripts/delegate.py list --status running
```

Briefs live in-tree:
- `.worktree-briefs/codex-1452-alignment-manifest.md`
- `.worktree-briefs/codex-1453-sidecar-freshness.md`

**Dependency note:** #1453 depends on #1452's manifest API. Brief contains stub-import fallback if #1453 lands first. After #1452 merges, rebase + un-stub #1453.

### User activity
User said "i will start the b2 wiki test with gemini" — test is running / about to run on their side. The full wiki fix stack is on main (attribution routing #1466, S-prefix strip #1465, MCP strip #1442, discipline #1447, tokenizer #1448, backfilled sidecars #1445, `_extract_terms` #1467, `turns:` #1458). Expect clean `type: textbook` + real filenames in new `.sources.yaml`.

## What to do on return (in order)

1. **Check the two Phase 1 dispatches:**
   ```bash
   .venv/bin/python scripts/delegate.py list --status running
   gh pr list --state open
   ```
2. **Review + merge #1452's PR first** (Codex tends to open PRs but not merge — #1403 shim). Squash-merge with `(#1452)` convention. Real CI only — ignore advisory `🔀 Gemini Dispatch / review`. Follow the same pattern used on #1466: run the failing tests locally if any, fix regressions, push.
3. **Rebase + merge #1453's PR** (may need manual rebase after #1452 lands to remove stub imports). Brief explains the pattern.
4. **Ask the user how B2 wiki test went.** Any `type: unknown` entries observed? (If yes: new bug class — run `_search_sections_fts5` in isolation on a real query.) Any other surprises?
5. **Either:**
   - **Option A:** Fire colors rebuild (`v6_build.py a1 10 --writer claude-tools` with Monitor tool) — tests Phase 3 fixes end-to-end. Per #1449 prediction: MIN 3→6, Overall 6.1→7.8. Still one R2 correction pass to publish.
   - **Option B:** Draft #1456 (P2-C) ADR — kill-or-revert the rewrite-strategy contradiction. Closes 4 supersede-pending issues (#1268, #1277, #1288, #1322). Requires user sign-off.
   - **Option C:** Continue Phase 2 + 4 dispatches (#1454 threshold unify, #1455 wiki review → MIN, #1460-#1464 invariant tests).

## Git state (as of handoff)

- **Local = origin/main** at `4b5c80a329`
- **Working tree has pre-existing dirty files** from prior `v6 colors` build runs:
  - `.claude/phases/gemini/*.md` (5 files)
  - `curriculum/l2-uk-en/a1/colors.md`, `activities/colors.yaml`, `build-stats.jsonl`
  - `curriculum/l2-uk-en/a1/orchestration/colors/*` (many chunk/dispatch/session-analysis files)
  - Various `.worktree-briefs/*` from earlier scale-lock work
- These were dirty when session started — NOT touched by Claude. Per code-editing-safety rule "git add only files YOU modified." Safe to regenerate via colors rebuild.

## Worktrees (4 total; down from 20+)

| Path | Branch | Purpose |
|---|---|---|
| `/Users/krisztiankoos/projects/learn-ukrainian` | `main` | Primary |
| `.worktrees/claude-fix-pytest-1421` | `claude-fix-pytest-1421-regressions` | **3 unpushed commits, no PR** — user decision needed |
| `.worktrees/codex-1286-review-transport` | `codex/codex-1286-review-transport` | **7 dirty files** — blocked on upstream Codex 0.122.0 per handoff |
| `.worktrees/codex-1452-alignment-manifest` | `codex/1452-alignment-manifest` | **Active Codex dispatch** |
| `.worktrees/codex-1453-sidecar-freshness` | `codex/1453-sidecar-freshness` | **Active Codex dispatch** |

## Key decisions + behavioral lessons from this session (MEMORY.md updated)

1. **#0H — Merging PRs after review is MY job, not user's.** User had to correct this twice today. Don't ask "should I merge?" — review + merge. Only the `--delete-branch` failure on worktree-pinned branches is expected cosmetic noise.
2. **#0G — Verify branch artifacts before inheriting failure-class claims.** The morning handoff claimed a "Vashulenko fabrication" on a1/colors that #1449's diagnostic found NOT PRESENT on the branch. I had repeated the claim as fact. Always re-verify.
3. **#0F — Trace reviewer dim failures to pipeline code first.** `_extract_terms` emitting function words as `required_terms` was invisible until Opus read `plan_contract.py` line-by-line. "Bad prompt" is often "bad pipeline heuristic the prompt has to compensate for."
4. **gemini-code-assist reviews in CI.** The `🔀 Gemini Dispatch / review` FAIL check is automated PR-review noise, NOT a blocking gate. Skip when real CI (Test/Lint/Frontend/Secret-Scanning) is green.

## Diagnostic + audit artifacts (now on main for future reference)

- `docs/architecture/2026-04-23-alignment-pipeline-audit.md` — 15-layer stack, 11 drift findings, Codex + Gemini integrated
- `docs/epics/2026-04-23-alignment-pipeline-runtime-contracts.md` — EPIC #1451 plan
- `docs/reports/2026-04-23-a1-colors-rebuild-plan.md` — 4-action sequence
- `docs/reports/2026-04-23-a1-colors-opus-r1-dim-diagnosis.md` — from #1449 diagnostic
- `docs/reports/2026-04-23-gemini-wiki-writer-diagnosis.md` — from #1450 diagnostic
- `docs/bug-autopsies/alignment-contracts.md` — 3 systemic bugs (sidecar freshness, sources_hash silent update, rule-after-incident governance)

## Services + environment

All healthy (confirmed at session start):
- api:8765 — Monitor API
- sources MCP:8766 — retrieval
- starlight:4321 — site render

Shell state:
- `GEMINI_AUTH_MODE=subscription`
- Writer default on main: `claude-tools`
- Codex effort/mode defaults unchanged

## Open risks

- **Gemini hard-timeout bug.** Gemini dispatch on #1458 (morning attempt) failed with `hard_timeout: gemini exceeded hard_timeout=3600s` at 951s duration — clock mismatch in the runtime. Worked around by doing #1458 inline. If re-dispatching Gemini: watch for the same symptom.
- **Uncommitted work in 2 preserved worktrees.** `claude-fix-pytest-1421` (3 unpushed commits) + `codex-1286-review-transport` (7 dirty files). User decision: PR or discard.
- **Colors orchestration working-tree dirt.** If the user runs colors rebuild, it regenerates those artifacts. If they don't and leave them dirty forever, git status stays noisy.

---

*Generated 2026-04-23 late evening. Next session: `state` skill + this file + GH issue/PR status check.*
