# Session Handoff — 2026-04-18 AM

## TL;DR — state of the project at handoff

**Tonight shipped 30+ commits across 4 issues (#1322, #1323, #1324, wiki-quality fixes).** All work on `main`, unmerged (local ahead of `origin/main`). **User is away and has explicitly cleared context.** Incoming session is COLD — read this file first, then dispatch the 4 briefs at `/tmp/` per the "What to dispatch immediately" section below. Run autonomously, report back to `docs/session-state/current.md` when phases complete or something needs user's call.

**Critical behavioral note for this cold-start session:**
- Pragmatic review (spot-check Codex output; don't review every file)
- Delegate liberally: Codex has 10x quota + different cost profile; use for all execution work
- Silence from me unless something ships to main, goes sideways, or needs user's call
- NEVER push to origin without user approval
- NEVER flip `CONVERGENCE_MATRIX_ENFORCED` flag
- Module builds dispatched through Codex are OK (user explicitly approved); single-module only, never `--range`

## What shipped tonight (in order)

### Wiki quality fixes (4 commits, ship-ready)
- `35bf6bdf5` parser fix (`--stdout-only`) + meta strip before review — cured the "7.0/10 with all 0.0 subscores" false-fail
- `75889eaae` `WIKI_CONTEXT_BUDGET` 30K → 100K uniform
- `6099eda87` per-dim review floor ≥ 8.0 (adds specific failing-dim list to fail logs)
- `17c6822d5` overall pass 9.0 → 8.0 (aligned with dim floor + non-negotiable-rules.md §2)

### #1322 Convergent pipeline (8 commits, Gemini-approved w/ patches)
- 5 impl commits (`ebd063080` → `72f2a4faf`): module_memory, finding_normalizer, finding_topology, convergence_loop, track_constraints + v6_build.py integration
- Gemini review (msg #346): verdict "merge with patches", 12/12 spec points conformant
- 3 patch commits (`cb7eb783b`, `a0bed1c56`, `3c91c50cb`): history audit-trail, prompt_hash bug, ladder exception guard
- A1/M1 end-to-end test: converged to `plan_revision_request` in 2 attempts (NOT `budget_exhausted`) — design intent verified
- 161 v6 tests + 194 convergence tests green
- **Ready to merge, pending your approval**

### #1323 Wiki sources refactor (11 commits, Gemini-blocked → patched)
- 8 Codex commits migrating 558 articles to sibling `.sources.yaml` + `[SN]` citations
- `b09aa035d` afhanistan recovery from bridge msg #335 (3 articles lost registry mappings mid-work; only afhanistan was recoverable)
- `86e84b203` wiki clean slate — all 558 articles deleted because user is regenerating against the improved pipeline
- Gemini review (msg #348): verdict "block merge" — 3 critical bugs found
- My 3 patches: `f4c03c12d` (strip_meta greedy-cross-comment), `49fab3ee9` (migration rerun hijack-guard), `74371b51e` (seminar registry injection)
- **Pending Gemini re-review to confirm patches are sound**

### #1324 External corpus (8 commits, ship-ready, pending review)
- Re-chunked 1199 whole-video blobs → 6476 chunks (avg 1942 chars, target was 2K)
- Enriched schema: channel_id, speaker, register_tag, decolonization_tag, quality_tier, publish_date, duration_s, chunk_start_ts, chunk_end_ts, video_id
- MCP tool `mcp__sources__search_external` exposed, with filter params
- Per-track ranking via `channels.yaml` affinity matrix
- 32 tests passing (15 + 17 MCP suite)
- `data/sources.db` is gitignored — migration runs local-only; on fresh machine, re-run `scripts/wiki/migrate_external_chunks.py`
- Channel registry has `# REVIEW` markers on imtgsh/istoria_movy/komik_istoryk/other_blogs — low-priority user validation
- **Pending Gemini adversarial review**

### Supporting commits
- `ead892faf` convergent pipeline spec committed
- `e0b90c65a` external corpus spec committed
- `bc529e59a` WIP refactor (per-track `SOURCE_CHAR_CAPS`, `_SOURCE_TYPE_PRIORITY`, dedupe, prefix stripping) — this was untracked WIP from a previous session, user said "commit + focus on code", shipped
- `86e84b203` wiki clean slate (558 articles wiped for fresh regen)

## What to dispatch immediately on cold start

**Briefs are pre-written at `/tmp/`; dispatch these four in the order shown, in parallel where independent.**

**1. Phase A — Codex: test-run wiki compile pipeline (9 slugs).** Brief: `/tmp/codex-phase-a-wiki-compile.md`. Serial dispatch inside Codex (not 9 parallel), --review on each. Slugs: a1 sounds-letters-and-hello + reading-ukrainian + special-signs; a2 aspect-concept; b1 people-and-relationships; hist trypillian-civilization; bio knyahynia-olha; lit introduction-to-kotliarevsky; oes walls-speak-intro. Codex writes `/tmp/phase-a-wiki-compile-results.md` + one-line summary on completion.

Dispatch command:
```bash
.venv/bin/python scripts/delegate.py dispatch \
  --agent codex --task-id phase-a-wiki-compile-test \
  --prompt-file /tmp/codex-phase-a-wiki-compile.md \
  --mode danger --hard-timeout 7200
```

**2. Phase B — Codex: module builds (GATED on Phase A health).** After Phase A completes and its report shows healthy pass/fail mix (NOT all-0.0 parser failures, NOT 9/9 failures), write brief at `/tmp/codex-phase-b-module-builds.md` and dispatch. Canary = A1 M1 sounds-letters-and-hello; if it converges to `pass` or `plan_revision_request` (NOT `budget_exhausted`), proceed with the other 8 builds in sequence (a1 1/2/3, a2 2, b1 3, hist 1, bio 1, lit 1, oes 1).

**3. Phase C — Codex: Google Drive backup setup.** Brief: `/tmp/codex-phase-c-gdrive-backup.md`. Independent of Phase A/B, dispatch in parallel.

Dispatch command:
```bash
.venv/bin/python scripts/delegate.py dispatch \
  --agent codex --task-id phase-c-gdrive-backup \
  --prompt-file /tmp/codex-phase-c-gdrive-backup.md \
  --mode danger --hard-timeout 1800
```

**4. Gemini reviews (parallel with Phase A).** Re-verify #1323 3-patch block-merge resolution + adversarial review of #1324 external corpus.

Dispatch commands:
```bash
unset GEMINI_API_KEY GOOGLE_API_KEY && .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini - \
  --task-id sources-refactor-review-1323-v2 \
  --model gemini-3.1-pro-preview --from claude < /tmp/gemini-1323-reverify-patches.md

unset GEMINI_API_KEY GOOGLE_API_KEY && .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini - \
  --task-id external-corpus-review-1324 \
  --model gemini-3.1-pro-preview --from claude < /tmp/gemini-1324-review.md
```

Both run in background; monitor task states via Bash `run_in_background=true`, plus a combined `Monitor` tool watch on the `batch_state/tasks/*.json` files and `git rev-parse HEAD` for new commits.

## Open decisions awaiting user (none blocking autonomous work)

These are quality-tuning knobs. Current defaults are reasonable; user will make calls on return.

1. **`SOURCE_CHAR_CAPS` (enrichment.py)** — currently progressive A1=45K → C2=120K, seminar=110K default. My recommendation: keep progressive (user's "rich wiki, not rich sources" intuition confirms this direction).
2. **Wiki word-target minimums** — currently pedagogy 1000 / grammar 1500 / seminar 1500 / academic 2000. Raising +50% is optional; testing with current floors first to see if actual output already exceeds.
3. **`CONVERGENCE_MATRIX_ENFORCED` feature flag** — default OFF. Flip ON when Claude+Codex review capacity returns (per current MEMORY: Gemini-only self-review is accepted capacity workaround).
4. **Merge readiness** — all work on main, unmerged. User reviews at leisure, decides merge order.

## Cold-start reading list (if session rolls over)

1. This file — state summary
2. `docs/architecture/convergent-pipeline-spec.md` — #1322 spec
3. `docs/architecture/external-corpus-spec.md` — #1324 spec
4. `git log --oneline -40` — commit chronology
5. `batch_state/tasks/*.json` — Codex worker states
6. `curl -s http://localhost:8765/api/state/manifest` — live project state (Monitor API)

## Agents & tasks to check on return

```
# Codex workers
cat batch_state/tasks/phase-a-wiki-compile-test.json     # Stage 1 wiki compiles
cat batch_state/tasks/phase-a-wiki-compile-test.result   # completion summary
cat batch_state/tasks/phase-b-module-builds.json         # Stage 2 module builds
cat batch_state/tasks/phase-c-gdrive-backup.json         # Google Drive backup setup

# Gemini responses (via ab bridge)
.venv/bin/python scripts/ai_agent_bridge/__main__.py inbox show claude
```

## Cross-agent review matrix (established tonight)

| Work type | Owner | Reviewer |
|---|---|---|
| Architecture / spec | Claude | Gemini or Codex |
| Code implementation | Codex | Claude or Gemini |
| Content writing | Gemini | Claude or Gemini (other model) |
| Content review | Gemini | — |
| Pure execution (tests, migrations, scripts) | Codex | self-verify + Claude spot-check |

**Fallback when Gemini is unstable:** Claude ↔ Codex bidirectional cross-review (both cross-family, preserves ADR-001:35 invariant).

## Critical behavioral notes

- User is a senior dev, time-poor, budget-sensitive, explicitly wants pushback over rubber-stamping
- `Monitor` tool streams events → use it instead of polling task states
- Codex has 10x usage quota through May 17 — delegate liberally when user is away
- Peak window 14-20 CET = Claude doubled; offload to Codex/Gemini
- Never run `v6_build.py --range` batch commands — only single-module test builds
- All work on `main`; no branches; `git worktree` for isolation if needed

## Commit ahead of origin/main

36 commits local-ahead. Do NOT push to origin until user confirms — merge decision is theirs.
