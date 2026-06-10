# Current — Claude Session Handoff (2026-06-10)

> Router: read `docs/session-state/current.md` first.
> **Latest detailed handoff: `docs/session-state/2026-06-10-claude-continuation-pr-sweep-deploy-fix.md`** — read it top-to-bottom.
> Prior detailed handoff (Word Atlas/heritage/hook): `docs/session-state/2026-06-10-claude-word-atlas-heritage-hookfix.md`.

## ⏳ RESUME HERE
1. **Confirm `npm run agents:deploy` stays clean** — deploy-drift root cause fixed this session (two
   undeclared `.agent/` orphans: `prompts` #2935, `tmp` #2936). Preflight now passes end-to-end.
2. **`poc-site-design.html` is the one real POC-split candidate** (Homepage + 404 + lesson-shell via a
   PAGE SWITCHER). The other 3 POCs are already single-design. Confirm intent (view-split vs
   folder-convention-normalize) before dispatching — marginal value.
3. **Word Atlas feature roadmap** (the real next work) — render heritage badges in `[lemma].astro` from
   `classify_lemma()`; etymology = Горох + Wiktionary; idioms; curated attestations (dep #2901). Full
   roadmap in both detailed handoffs.

## ✅ Done this session (continuation thread)
Merged #2923, #2929, #2925, #2933 (recovered stalled A2 content), #2935, #2936. Closed #2895
(superseded), #2932 (handoff — see autopsy note in the detailed handoff). Reaped 6 worktrees.
Root-caused + fixed deploy drift. Finalized prior session's session_start.sh worktree auto-reap.

## ⚠️ Watch-outs
- **GitHub graphql API was 401'ing intermittently** (secondary rate-limit). `gh pr create` failed →
  use `gh api -X POST repos/.../pulls` (REST). Non-required checks (zizmor/submit-pypi/CodeQL Analyze)
  failed only on API status-report steps; **only required check is `Test (pytest)`**.
- Folk lane is progressing in its own track (kalendarna building with the heritage gate). Awareness-only.

## Restart
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin -q && git merge --ff-only origin/main
gh pr list --state open --json number,title,isDraft   # #2892/#2854/#2601 = track-owned/draft/stale
npm run agents:deploy                                  # should stay clean
```
