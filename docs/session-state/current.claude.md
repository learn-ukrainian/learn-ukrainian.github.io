# Current — Claude Session Handoff (2026-06-17 — Atlas mis-diagnosis caught + recovered; LLM-QG API shipped)

> **ROLE:** main orchestrator. User: grind the queue, results-focused, use the FLEET (#M-12), self-merge after review + CI-green, don't manufacture obstacles, don't idle. Quality non-negotiable.

> **TONE NOTE:** this session the user was (rightly) frustrated about Atlas. Trust on Atlas specifically is low after a real mis-diagnosis (below). Be rigorous and honest on anything Atlas-touching.

## 🔴 TOP PENDING — PR #3483 (atlas-3150 recovery) is GREEN + ready; NOT merged
Branch `codex/atlas-3150-autoexpand` @ `cbe83e6a90`. **mergeState CLEAN, all checks green.** Closes #3150.
- **What it is:** the `atlas-3150-autoexpand` dispatch's real work — a manifest-vocabulary-coverage gate + regenerated manifest (entries 2447→2891, wiki 657→761, heritage 100%) + the gate redesigned to **diff-scoped + advisory** (see below).
- **DO NEXT:** I deliberately did NOT self-merge (I mis-diagnosed this exact feature today — see lesson). Per #M-12: fire a **focused codex cross-review** on the LOGIC only — `scripts/lexicon/check_manifest_vocabulary_coverage.py` (diff-scope), the `.github/workflows/ci.yml` change, and the `лет` allowlist in `scripts/audit/validate_atlas_conformance.py` — NOT the 70K-line generated manifest blob. If clean + CI green → merge. (`ab ask-codex` or `delegate.py --agent deepseek` review lane.)
- **After merge:** clean up worktree `.worktrees/dispatch/codex/atlas-3150-autoexpand` (has `data/sources.db`/`vesum.db` symlinks → main; safe to `git worktree remove --force`).

## ⚠️ THE ATLAS MIS-DIAGNOSIS LESSON (encode into MEMORY next session)
I wrongly condemned a **successful** dispatch as a catastrophe via two forensics errors:
1. **Measured a mid-write working-tree file** (`wiki_reference=0` transient) instead of the COMMITTED blob (`git show HEAD:path` = 718). The codex process was still live-writing; file mtime advanced with no action from me — the tell I missed.
2. **Read `git diff origin/main..HEAD` (base-divergence) as a "deleted module"** — the branch predated 5 certifications on main, so everything main gained looked "deleted by HEAD." `git show HEAD --stat` proved the commit touched ZERO curriculum files.
→ Rules: **attribute changes via `git show <sha>` not `base..HEAD`**; **only measure committed artifacts** (`git show HEAD:`), check process liveness + mtime before trusting a dispatch-worktree read; **`status=failed` ≠ failed deliverable** (#2985 finalize-zombie — inspect the commit, run its gates, recover). Full autopsy: `docs/bug-autopsies/atlas-3150-misdiagnosis.md`.
- Record corrected this session: autopsy retitled (#3470 MERGED), **#3331 re-closed** (reopened on the false premise), **#3150 corrected** (recoverable, not blocked).

## 🟢 SHIPPED + MERGED this session
- **LLM-QG Monitor API (#3455 + #3458):** user's #1 priority — `/api/state/llm-qg/{track}` exposes per-module per-dimension LLM-QG scores (aggregate + dimensions, `?verbose` for evidence) + an `llm_qg` block on `/api/state/module/{track}/slug/{slug}`. **Live** (restarted `api` service). Real intel: of 6 scored folk modules only 1 (koliadky-shchedrivky) PASSES — rest REVISE/REJECT on `pedagogical` (5.8-7.1). Folk is track-owned — that orchestrator should act.
- **#M-13 immersion landmine CLOSED:** all 3 runtimes (`.claude/.codex/.agent`) carried STALE English-raising A2 prompts (45-75%, "English for theory") while committed source was already correct (85-100% "Ukrainian IN Ukrainian"). Synced 4 files (`skills/content-review/content-review-prompt.md`, `skills/plan-review/review-tiers/tier-1-beginner.md`, `quick-ref/a2.md`, `phases/calibration/a2.md`) into all runtimes (gitignored local — not a committed change).
- **#3470** (autopsy correction), 2 docs PRs (#3452/#3453) earlier.

## ⏭️ OPEN QUEUE / PARKED
1. **#3483 merge** (above) — fire codex review → merge.
2. **#3150 remaining (the real goal):** the vocab gate is now diff-scoped + advisory (interim). Blocking enforcement needs **auto/incremental re-enrich** so the manifest stays green by itself — BLOCKED on CI DB access (#2928, 1.6GB sources.db / 967MB vesum.db not in CI). Full `make atlas` regen = ~33 min; merge-train adds vocab every ~5-10 min → manual regen is a treadmill. Design note in #3483's comment.
3. **#3456** (filed): `agents:deploy` orphan-guard aborts whole deploy when a dispatch brief sits in `.agent/` → source prompt fixes silently never reach runtime (recurrence of #3039; convention-fix never enforced). Infra/my lane. This is WHY the #M-13 fix needed manual sync.
4. **DASHBOARD-PANEL AUDIT — user's ORIGINAL ask this session, NEVER DONE.** "We have lots of panels, some not working; ensure working panels and remove obsolete/unsupported-by-current-API ones." Initial recon: 20 dashboards in `dashboards/*.html`, 183 API routes (`/openapi.json`), served at `localhost:8765/` (`ukraine-ops`). Deterministic method: cross-ref each dashboard's `/api/...` refs vs OpenAPI route templates (normalize path params), classify fully-dead (remove page) / partially-dead (remove panel) / healthy; remove obsolete. Proper root-cause fix = a dashboard-endpoint conformance CI gate (prevent future rot).
5. **Enrichment-floor guard** — `git stash@{0}` ("wip: atlas enrichment guard"). Premised on the FALSE catastrophe, so NOT pushed. Optional proactive hardening only (cold-cache re-enrich risk is real per #3124/#3197). Drop or finish honestly if wanted.

## 🧹 HOUSEKEEPING
- **Main tree has NON-mine uncommitted changes** (do NOT commit): Headroom MCP integration — `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.mcp.json`, `.cursor/mcp.json`, `start-claude.sh` + untracked `uv.lock`. Environment/user-added; left untouched.
- **MEMORY.md over budget** (152 lines, soft 150) — trim before adding; the Atlas mis-diagnosis lesson should land there (tight one-liner + the autopsy link).
- Track-owned open PRs (awareness-only): #3495 (build --enhance), #3480/#3465 (folk drafts).
- `headroom` MCP now available (local `:8787`) for compressed handoffs — see CLAUDE.md § Headroom.

## Atlas SSOT: `docs/atlas-data-coverage-strategy.md`. Verify-before-promote: #M-11. Manifest regen = `make atlas` (needs data/ → run in main tree or symlink DBs into a worktree, per user 2026-06-17).
