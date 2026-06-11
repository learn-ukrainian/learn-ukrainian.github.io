# Current — Claude Session Handoff (2026-06-11)

> Router: read `docs/session-state/current.md` first.
> **Latest detailed handoff: `docs/session-state/2026-06-11-claude-word-atlas-conformance-paradigm-gates.md`** — read top-to-bottom.

## ⏳ RESUME HERE — continue Word Atlas backlog (EPIC #2985), easiest-first
Next item: **#2985 item 3 — derivational-base etymology (#2971)**. Reduce ~10 derived A1 lemmas to
their ЕСУМ base, then reuse `_etymology()` (Goroh→ЕСУМ→Wiktionary) on the base. ~7 resolve, ~3 stay
blank (don't fabricate). Dispatch to Codex. Details + reduction table in the detailed handoff.

After #3: reassess #7 (scale to A1+A2+B1 vocab — the big lever that makes the decolonization moat
visible). #5 synonyms BLOCKED on #1657. #4 corpus sections need a relevance layer.

## ✅ Done this session
7 PRs merged (#2854 folk scraper salvage · #2969 v7_build primary-checkout guard [#2884 closed] ·
#2970 Wiktionary etymology+gate · #2980 Atlas conformance fixes · #2981 paradigm table ·
#2986 hub search full corpus · #2988 §8 conformance gates enforced in CI). Filed #2971 + EPIC #2985.
Git/GitHub hygiene done (orphan worktrees/branches cleaned; active A2/folk/b1 lanes preserved).

## ⚠️ Watch-outs
- **#M-11**: verify the ARTIFACT (render it / read the data), not just green gates — bit us 3× this session.
- **CI lacks `data/vesum.db`** — tests using it must degrade gracefully (`vesum=None` path).
- **gitleaks 502 flake** = ghcr.io image-pull, not a real leak → `gh run rerun <id> --failed`.
- **DO NOT TOUCH** `codex/2888-a2-*` (A2), `codex/folk-*` + `build/folk/*` (folk), `codex/b1-v72-*` (b1) — other lanes.
- `start-claude.sh` locally modified (pre-existing, not mine) — leave it; Codex PRs sometimes open as draft (`gh pr ready N`).

## Restart
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin -q && git merge --ff-only origin/main
gh issue view 2985   # Atlas backlog EPIC; next = item 3 (#2971)
```
