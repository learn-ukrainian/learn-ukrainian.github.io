# Current — Claude Session Handoff (2026-06-10)

> Router: read `docs/session-state/current.md` first.
> **Latest detailed handoff: `docs/session-state/2026-06-10-claude-word-atlas-heritage-etymology.md`** — read top-to-bottom.

## ⏳ RESUME HERE — Word Atlas B phase 2 (Wiktionary etymology fallback)
Cover the ~21 lemmas Goroh doesn't (etymology is 42/63 on main). **Dispatch to Codex**, modeled on the
just-merged `scripts/ingest/goroh_etymology_ingest.py`. Colleague-vetted approach (in the detailed handoff):
- Use the **real `ukwiktionary` XML dump** (pinned by date/checksum) — **NOT Kaikki** (Codex: Kaikki "uk"
  = English Wiktionary's Ukrainian entries).
- Extract `== Етимологія ==` offline (mwparserfromhell / conservative template stripper), ingest into a
  `wiktionary_etymology` table, wire `_etymology()` precedence **Goroh → Wiktionary → ЕСУМ**.

## ✅ Done this session
Merged #2923/#2929/#2925/#2933 (resume sweep), #2935/#2936 (deploy fix + worktree auto-reap),
#2937 (docs), **#2955 (Word Atlas heritage badges)**, **#2957 (security: idna + bad-tag-filter)**,
**#2958 (Goroh etymology, 19→42/63)**. Worktree disk 11.6 GB → 472 MB. Main clean at `5c08eb4318`.

## ⚠️ Watch-outs
- **GitHub graphql 401'd intermittently** — use REST (`gh api -X POST/PUT .../pulls`) when `gh pr create/merge`
  fails. Non-required CI (zizmor/submit-pypi/CodeQL Analyze) flaked on API status-report, not real. Only
  required check = `Test (pytest)`.
- **A2 beta (#2888) is Codex's active lane** — leave `codex/2888-a2-*` PRs/worktrees alone (#2956 open + 3 worktrees).
- Word Atlas heritage badges are render-complete but only VISIBLE once vocab broadens past the 63 all-`standard`/`unknown` A1 lemmas (roadmap E).

## Restart
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin -q && git merge --ff-only origin/main
gh pr list --state open --json number,title,isDraft   # #2956/#2954/#2854/#2601 = other lanes
npm run agents:deploy                                  # should stay clean
```
