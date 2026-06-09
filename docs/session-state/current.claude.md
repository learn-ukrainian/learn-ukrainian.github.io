# Current — Claude Thread Handoff (2026-06-10)

> Router: read `docs/session-state/current.md` first.
> **Latest detailed handoff: `docs/session-state/2026-06-10-claude-a1-atlas-design-pilot.md`** — read it.

## ⏳ RESUME HERE — A1 POC lesson pilot in flight
`codex/a1-poc-lesson-pilot` dispatch RUNNING (B-pilot Step A: POC lesson component framework +
`things-have-gender.mdx` reference module, **LOCAL ONLY — no deploy, no writer-prompt change**).
On land: review PR (don't merge), verify `/a1/things-have-gender/` locally vs `docs/poc/poc-lesson-design.html`,
hand the URL to the user for sign-off. Then Step B (writer-prompt + batch regen, verify-local-before-deploy).

## Decisions locked
- **Design = B** (regenerate to POC structure) with "verify locally before rollout" — A1 lessons + Word Atlas.
- **Etymology = Горох + Wiktionary** (NOT v2 ESUM — cognates OCR-garbled; NOT the DjVu scan). Tear down the 36K OCR `etymology-manifest.json` surface.

## Shipped + live this session
A1 `:::` admonitions fixed + dev jsxDEV hardened (**#2887**, deployed live). Worktree reaper shipped
(**#2883**, `scripts/orchestration/reap_worktrees.py`). A1 + Word Atlas rolled out live. PR queue drained
(#2880 merged, #2850 closed). #2884 filed (build-pollutes-main; forensics on `salvage/main-pollution-a2792`).

## Key gotchas
- Deploy = manual: `gh workflow run deploy-pages.yml --ref main` (~2-3min). NOT auto.
- Local dev empty islands / `jsxDEV is not a function` → `rm -rf starlight/node_modules/.vite && ./services.sh restart astro`.
- Reaper on main: `scripts/orchestration/reap_worktrees.py --dry-run|--apply`.

## Restart
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin -q && git merge --ff-only origin/main
curl -s http://localhost:8765/api/delegate/active   # a1-poc-lesson-pilot done?
gh pr list --state open --json number,title,headRefName
```
