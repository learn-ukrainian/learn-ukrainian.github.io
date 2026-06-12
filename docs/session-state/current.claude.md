# Current — Claude Session Handoff (2026-06-12)

> Router: read `docs/session-state/current.md` first.
> **Latest detailed handoff: `docs/session-state/2026-06-12-claude-word-atlas-production-rollout.md`** — read top-to-bottom.
> **🚨 PRODUCTION: real learners are on A1 now.** Word Atlas was rebuilt to full vocab (~2,045 words) +
> decolonization fixes; the `atlas-finalize-all` dispatch is finishing — RESUME = verify it, merge,
> inject `PUBLIC_GOATCOUNTER_CODE=learn-ukrainian` into `deploy-pages.yml`, deploy, verify LIVE. Folk nav
> hidden + GoatCounter wired (#3027) and services self-heal (#3026) already on main but NOT deployed.
> The sections below are from the 2026-06-11 session and are superseded by the 06-12 handoff above.

## 🚨 CRITICAL — GitHub Pages auto-deploy is DISABLED (workflow_dispatch only)
Merging to main does NOT update the live site. This is why the user saw "Word Atlas not following the
design" — all Atlas work (#2980/#2981/#2986/#2988) merged 06-11 but live was frozen at 06-10. **After any
user-facing (`starlight/`) merge: `gh workflow run deploy-pages.yml --ref main`, watch it, verify the LIVE
site, not just localhost.** Deploy triggered this session (run 27368018028).

## ⏳ RESUME HERE
1. **Verify deploy 27368018028 landed** + live Atlas correct (`gh run list --workflow=deploy-pages.yml`).
2. **Synthesize UA-dictionary source research** (IN FLIGHT): asks `ua-dict-research-codex` + `-agy` running
   (hermes/qwen failed — skip; qwen excluded). Goal: AUTHENTIC Ukrainian synonym/antonym/idiom dictionaries,
   **NO Russian, NO English-auto-translated** (ukrajinet WordNet unusable). Brief:
   `docs/dispatch-briefs/2026-06-11-ua-lexicon-source-research.md`. Collect answers → ranked sourcing table
   on #2985 → best path to a clean UA synonym dataset.
3. Continue backlog EPIC #2985 (reprioritized: #3 derivational etym → **#7 scale (promote)** → #6 Антоненко
   → #4 relevance layer → #5 synonyms after sourcing).

## ✅ Done this session
7 PRs merged (#2854·#2969[#2884 closed]·#2970·#2980·#2981·#2986·#2988). Filed #2971 + EPIC #2985.
Researched blocked parts (#2985 comment): synonyms genuinely blocked; scale (#7) high-value+feasible,
activates the decolonization moat (~200+ sovietization-flagged pages at scale). Git/GitHub hygiene done.

## ⚠️ Watch-outs
- **Verify the LIVE site, not localhost** (deploy is manual). #M-11 + deploy miss bit 4× this session.
- **CI lacks `data/vesum.db`** → tests degrade gracefully (`vesum=None`).
- **Push docs via a clean worktree off origin/main** — main checkout has folk untracked files + `start-claude.sh`
  local mod that block rebase. Do NOT `reset --hard` (loses folk's work).
- **DO NOT TOUCH** `codex/2888-a2-*`, `codex/folk-*`/`build/folk/*`, `codex/b1-v72-*` (other lanes).
- gitleaks 502 = ghcr.io flake → rerun. Codex PRs sometimes draft → `gh pr ready N`. qwen excluded.

## Restart
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin -q
gh run list --workflow=deploy-pages.yml --limit 2   # deploy landed? live Atlas current?
gh issue view 2985                                  # backlog EPIC + research
```
