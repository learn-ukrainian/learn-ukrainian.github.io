# Current Session Restart Handoff

Generated-At: 2026-06-08 (Claude orchestrator, user-requested handoff at ~500K)

## Latest Brief (2026-06-08 PM — Claude UI session)

Driving **#2823 lightweight UI** (tech + design); folk owned by another agent. Shipped +
pushed to origin/main (verified in-browser on localhost:4321, NOT deployed — user wants
live site untouched): **dark-mode contrast root-cause fix** (`1ce28423d3` — footer was
white-on-white; added fixed on-color tokens; home 23→0 contrast failures, 340 tests pass);
A1 landing **M08 CTA fix** (`cf1c78fafe`); track-orchestrator→folk retarget (`497c51b09a`);
SCRIPTS.md services.sh doc (`cd4620834a`).

**Full detail (READ THIS):** `docs/session-state/2026-06-08-claude-ui-darkmode-slice1-lexicon.md`

## ⚠️ Hazard: Codex is sharing the main checkout (branch switch + recurring index.lock). Get Codex on a worktree.

## Top next actions
1. **Lexicon "unusable" (user-flagged)** — detail pages are empty v1 stubs by design; raw
   `plan_required` token leaks. DECIDE: build enrichment pipeline vs defer Word Atlas from
   nav (AC allows defer). Quick win: fix the token leak in `src/pages/lexicon/[lemma].astro`.
2. **#2823 slice 1 redo** — in `stash@{0}`, blocked by `check-mdx-source-parity`. Redo
   parity-safe: keep Vite alias, only fix generator + delete dead overrides/CSS + drop
   `template` field. Do NOT bulk-edit published MDX.
3. **#2823 slices 2-6** (shell/landing/lesson/seminar/word-atlas/QA). Design-QA already
   swept 7 page classes — all clean in dark mode.
4. (Older, still open) Agy wiki-lane §7 re-test; manual Pages deploy when user approves.

## Context policy (autocompact OFF)
Handoff is the ONLY guard. ~500K this phase, ~700K next. Monitor rot with
`scripts/context_canary.py` (mint immutable anchors at low context, score from memory at
checkpoints; drift → hand off). Log: `batch_state/canary/canary_log.csv`.

## Hands-off (parallel agents)
Session-handoff protocol; #2832 ledger; #2824 M8 MDX.

## Git
- Root branch: `main` | origin/main HEAD: `e4bf1398ee` (fix(ui): de-Sovietize main hero)

## Restart commands
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin -q && git log origin/main --oneline -8
curl -sS http://127.0.0.1:8765/api/orient
gh issue view 2823 --comments
cat docs/session-state/2026-06-08-claude-agy-context-policy-2823-takeover.md
.venv/bin/python scripts/context_canary.py --help
```
