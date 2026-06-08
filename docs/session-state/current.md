# Current Session Restart Handoff

Generated-At: 2026-06-08 (Claude orchestrator, overnight autonomous #2823 run)

> NOTE: this file was pure-deleted by `7c6170337b` (PR #2853 reorg) mid-session and
> RESTORED here. It is the cold-start router — do not delete. See the overnight
> handoff for the regression detail.

## Latest Brief (2026-06-08 overnight — Claude autonomous #2823 slices)

Drove **#2823 lightweight UI** slices autonomously (user asleep, "keep working auto").
Folk owned by another agent (hands-off). Live site untouched. Shipped + pushed to
origin/main, each verified (astro build 144pp + vitest 340/340 + dev-server DOM):
- `0cfe59e9bf` **lexicon badge token-leak fix** (3 machine tokens → Ukrainian labels;
  the "unusable" symptom the prior handoff flagged).
- `9cd2e0c557` **slice 1: deleted 5 dead Starlight override components** (site already
  off the starlight integration; zero real `@astrojs/starlight` imports remain).
- `b749828a6f` **slice 3: localized A1 lesson tab chrome to Ukrainian**
  (Урок/Словник/Зошит/Ресурси) via the `starlight-compat` shim — matches POC + folk,
  parity-safe (no MDX edit, no regen).

**Full detail (READ THIS):** `docs/session-state/2026-06-08-claude-overnight-2823-slices.md`

## ⚠️ Hazards
1. **Shared main checkout:** Codex runs git in the SAME checkout; origin moved under me
   mid-session (PR #2853). Commits stacked clean but the index.lock/branch-switch hazard
   is unresolved. **Get Codex on a worktree.**
2. **Reorg deleted load-bearing files:** PR #2853 pure-deleted `current.md` (restored).
   Codex should audit the reorg for other unintended session-state/doc deletions.

## Top next actions (remaining #2823 = USER-JUDGMENT)
1. **POC visual fidelity polish** — needs your eye + browser pass vs the 5 POC HTMLs.
   Structure present; refinement is subjective. (slices: shell/landing/lesson/seminar/QA)
2. **Word Atlas enrichment pipeline** — per your direction, build at the Atlas slice
   (slice 5); RAG-verified, no fabrication. `docs/best-practices/word-atlas-design.md §4`.
3. **Site-level Ohoiko/teacher IP-safe copy** — present in content, missing as a
   site-level block; IP-sensitive wording + placement = your call.
4. Drop `stash@{0}` (old blocked slice-1, now superseded). Codex→worktree.

## Context policy (autocompact OFF)
Handoff is the ONLY guard. Monitor rot with `scripts/context_canary.py` (mint anchors at
low context, score from memory; drift → hand off). Log: `batch_state/canary/canary_log.csv`.

## Hands-off (parallel agents)
Folk track; #2832 ledger; #2824 A1 Ohoiko audit; the agents_extensions reorg (Codex).

## Git
- Root branch: `main` | origin/main HEAD: `b749828a6f` (fix(ui): localize A1 tab chrome) —
  this handoff commit sits on top.

## Restart commands
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin -q && git log origin/main --oneline -8
curl -sS http://127.0.0.1:8765/api/orient
gh issue view 2823 --comments
cat docs/session-state/2026-06-08-claude-overnight-2823-slices.md
./services.sh status
```
