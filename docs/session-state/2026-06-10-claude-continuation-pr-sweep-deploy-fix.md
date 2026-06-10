# Claude session handoff — 2026-06-10 (continuation: PR sweep + A2 content recovery + deploy-drift root fix)

> Router: `docs/session-state/current.md` → `current.claude.md` → this is the latest detailed Claude handoff.
> Continuation of `2026-06-10-claude-word-atlas-heritage-hookfix.md` (prior thread rolled over at 98% ctx).

## ⚡ TL;DR
Cleared the entire prior-session RESUME queue, recovered a stalled A2 dispatch's content, and
root-caused + fixed the recurring deploy-drift warning (two undeclared `.agent/` orphans, not "1 file").
Also finalized the prior session's uncommitted worktree-auto-reap feature.

## ✅ MERGED to main this session
| PR | What |
|---|---|
| **#2923** | context-monitor hook fix (was on resume list; all CI green) |
| **#2929** | landings unified onto A2 `LevelLanding` pattern. Verified beyond the conformance test: custom.css defines `--lu-id-*` for **all 19 landing tracks** — no dangling `var()` (the gap the test didn't cover) |
| **#2925** | Word Atlas POC split. Handoff-flagged "scope creep" was actually **legit reference updates** for the now-stubbed `poc-word-atlas-design.html` (reverting → dangling links). Merged as-is, overriding the stale instruction on evidence |
| **#2933** | **Recovered stalled A2 content.** `2888-a2-m01-m03-final-fix` Codex dispatch hit the 900s silence timeout, killed with `commits_ahead=0` + uncommitted work (a2-bridge stress/дж-дз phonetics + aspect drills). Verified sound, committed/rebased/PR'd/merged (#M-10) |
| **#2935** | deploy: declare `.agent/prompts` orphan + `start-claude.sh` native-binary self-heal |
| **#2936** | deploy: declare `.agent/tmp` orphan (2nd blocker) + **session_start.sh worktree auto-reap** (recovered prior-session feature) — *MERGE STATE: confirm landed* |

## ❌ Closed
- **#2895** — superseded by merged #2906 (sense-correct synonyms).
- **#2932** — handoff doc. ⚠️ **I initially closed this calling it "identical to main" — that was WRONG** (the detailed handoff was *absent* from main; I misread a diff). No content lost (file was local). The prior detailed handoff `2026-06-10-claude-word-atlas-heritage-hookfix.md` is being landed with this session's docs.

## 🔧 Deploy-drift ROOT CAUSE (now fixed)
Session-start hook said "1 file differs" but `npm run agents:deploy` actually aborted on **undeclared
`.agent/` orphans** that `rsync --delete` would wipe. Enumerated ALL targets: only two were undeclared —
`prompts` (#2935) and `tmp` (#2936). Both are runtime-only (`prompts/` = per-dispatch prompt files;
`tmp/` = issue/PR draft scratch). After #2936 the deploy preflight passes end-to-end. **Re-run
`npm run agents:deploy` after #2936 lands** to sync the original `.claude/` content drift (couldn't run
before because the orphan abort blocked it).

## 🧹 Hygiene done
- Reaped 6 stale worktrees total (merged/closed branches) across the session.
- Cleared `needs_finalize` flag on `2888-a2-m01-m03-final-fix` (shipped via #2933).

## 📌 POC-split directive — reconciled
User directive "split ALL POC files one-design-per-HTML" is **already satisfied for 3 of 4**:
`poc-lesson-design.html` (1545 lines, ONE lesson design), `poc-folk-lesson-design.html`,
`poc-lit-lesson-design.html` are each a single design. **Only `poc-site-design.html` is genuinely
multi-page** (Homepage + 404 + lesson-shell via a PAGE SWITCHER — like the Atlas was). That's the one
real split candidate; queued, not auto-dispatched (marginal value; confirm intent first — view-split vs
folder-convention-normalize).

## ⚠️ GitHub API auth degradation (during session)
graphql endpoint was intermittently 401'ing (`gh pr checks`/`gh pr create`; `gh api graphql '{viewer}'`
worked but repo-PR queries 401'd → looked like secondary rate-limiting). Surfaced as the ONLY "failures"
on PRs: `zizmor`/`submit-pypi`/`Analyze (CodeQL)` all **passed their actual work** and failed only on the
API status-report/SARIF-upload step. **Only required check is `Test (pytest)`.** Workaround for PR create:
`gh api -X POST repos/.../pulls` (REST) bypasses the graphql check. If still flaky next session, prefer REST.

## 🗺 Next (Word Atlas roadmap — the real feature work)
Resume the Word Atlas completion roadmap from the prior handoff:
- **A:** render heritage "Походження + статус" badges in `[lemma].astro` from `classify_lemma()` (engine on main).
- **B:** etymology = Горох + Wiktionary (NOT ESUM); idioms; register/temporal badges from SUM ремарки.
- **C:** curated attestations (depends on #2901 literary `source_url` fix).
- **E:** all POCs dual-mode; broaden beyond 63 A1 lemmas; deploy live.

## Restart
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin -q && git merge --ff-only origin/main
gh pr view 2936 --json state,mergedAt              # confirm landed
npm run agents:deploy                              # should pass preflight now; syncs .claude drift
gh pr list --state open --json number,title,isDraft # #2892/#2854/#2601 are track-owned/draft/stale
```
