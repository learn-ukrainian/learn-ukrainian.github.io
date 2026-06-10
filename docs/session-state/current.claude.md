# Current — Claude Session Handoff (2026-06-10)

> Router: read `docs/session-state/current.md` first.
> **Latest detailed handoff: `docs/session-state/2026-06-10-claude-word-atlas-heritage-hookfix.md`** — read it top-to-bottom.

## ⏳ RESUME HERE
1. **`landings-unify` dispatch (Codex) was RUNNING at handoff** — branch `codex/landings-unify`. Check
   `/api/delegate/active`; on land, review per-track both-mode screenshots + the conformance test, merge when green.
   Migrates A1/folk landings onto the **A2/`LevelLanding` pattern** (A2 is the reference; A1/folk were on an old layout).
2. **PR #2925 (Word Atlas POC split) — review + TRIM before merge.** Good: 3 per-view HTML
   (landing/detail/heritage-defense) + README design→route map. **Strip the scope creep:** it edited two
   `session-state/` handoff files + created unrequested arch docs — revert those, then merge.
3. **PR #2923 (context-monitor hook fix)** — merge when CI green.
4. **USER DIRECTIVE:** split **ALL** POC files one-design-per-HTML (lesson/folk-lesson/lit/site), not just the Atlas.

## Folk lane: UNBLOCKED
Heritage engine merged (#2912, `scripts/lexicon/heritage_classifier.py` on main). Unblock posted to #2882 —
folk wires `classify_surface_form()` into `_vesum_gate` and resumes kalendarna. Confirm they picked it up.

## Word Atlas next (after landings/POC): render heritage badges in `[lemma].astro`, etymology (Горох/Wiktionary),
idioms, attestations (#2901 dep), label-axis badges. Full roadmap in the detailed handoff.

## Decisions locked
- **Dual-mode token authority is SSOT** — `docs/best-practices/dual-mode-design-tokens.md`. Every surface light+dark
  via `--lu-*`; no hardcoded color; yellow-on-accent text dark in both modes; POCs must be dual-mode.
- **Etymology = Горох + Wiktionary** (NOT ESUM — OCR-garbled).
- **Context-monitor hook is honest now (#2923)** — earlier "auto-compact EMERGENCY" spam was false. Claude handoff =
  this session-state doc, NOT the Codex `thread_handoff.py` bootstrap flow.

## Restart
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin -q && git merge --ff-only origin/main
curl -s http://localhost:8765/api/delegate/active        # landings-unify done?
gh pr list --state open --json number,title,headRefName  # #2925, #2923, landings PR
# Word Atlas live check: rm -rf starlight/node_modules/.vite && ./services.sh restart astro
```
