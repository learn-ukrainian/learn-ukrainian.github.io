# Current - Claude Thread Handoff (2026-06-06)

> Read `docs/session-state/current.md` (router) first, then this file.
> origin/main at handoff: `61058d58c4` (local synced). FF first thing anyway.

## ✅ #1863 Phase 2 DONE THIS SESSION (2026-06-06)
Ran `find_dead_code.py`; **first finding was a tool bug** — it walked `.worktrees/` (11 live
worktrees = full repo copies), making **77% of the report noise** (2460/3202 hits) + 6m16s runtime.
- **Fixed + merged #2746**: centralized `EXCLUDE_DIR_NAMES` + `_is_excluded()`/`_ugrep_exclude_flags()`/
  `_vulture_exclude_glob()`; added `.worktrees` + `archive`. 3187→712 hits, runtime 6m16s→1m03s (6×).
  3 regression tests; tests/audit green (471). Only A/B/F walk from root — C/D/E/G/H/I/J already scoped safe.
- **Triaged the clean 712-hit report** (PASS/REVIEW/KEEP) — key false-positive carve-outs: B's ~129
  `tests/` hits are pytest fixtures (vulture flags injection params); A self-matches its own `"OBSOLETE"`
  search string; F's `scripts/orchestration`/`folk/orchestration` are live; G mixes legit per-package
  names (`config.py` etc.) with real root-level rename-leftovers.
- **Filed 9 sub-issues** under #1863 (H=0 hits): A #2747, B #2748, C #2749, D #2750, E #2751,
  F #2752, G #2753, I #2754, J #2755. Epic body + checklist updated; triage = #1863 comments.
- **Phase 3 is PARKED** — plan requires a 1-2 day window with NO concurrent feature work (A1/B1/bio/folk
  active). At Phase-3 start: re-run the tool for a fresh list, then dispatch per the routes in each issue.

## ▶ NEXT SESSION: continue TECH DEBT (user direction 2026-06-05)
Keep agy working the tech-debt backlog, **Flash 3.5 High for coding** (routing below).
Candidates: dispatch agy-Flash on a bounded coding task (**#2739** wrapper-finalize — bounded but
**infra-sensitive** delegate/runner, scope carefully), or other bounded open issues.
AVOID #2378 / EPICs / A1-A2 (Codex) / bio (Claude). Cleanup Phase 3 (#2747-2755) waits for a quiet window.

## ✅ NO LIVE DISPATCHES. Clean stopping point.
0 active delegates. Only open PR is **#2601** (B1 pilot, draft, **codex-owned — awareness only**).
Security: dependabot **1** (idna `.dagger/uv.lock`, tracked #2732 Part 2), code-scanning **0**.

## ⚠ OPEN: CodeQL "config problem" (user flagged, awaiting their exact symptom)
Investigated 2026-06-05: CodeQL is **functionally green** — default setup, 3 analyses
(`actions`, `javascript-typescript`, `python`) all success, **no errors**, 0 alerts, NOT blocking
(branch protection = only `Test (pytest)`). **The one concrete defect:** default-setup `languages`
lists **5** (`actions, javascript, javascript-typescript, python, typescript`) but only **3** run —
`javascript`+`typescript` are **stale/redundant** (superseded by `javascript-typescript`). Likely the
"needs attention" warning in Settings → Code security. **Fix (unconfirmed it's the right symptom):**
`gh api -X PATCH repos/learn-ukrainian/learn-ukrainian.github.io/code-scanning/default-setup` with
`languages=[actions,javascript-typescript,python]`. User hadn't confirmed whether that's what they see
vs a different banner — get the exact symptom before PATCHing their security config.

## 🧹 Git + issue hygiene (done 2026-06-05)
- Git: main synced; `git remote prune` clean; my worktrees removed. **11 dispatch worktrees REMAIN —
  all other lanes** (Codex A1/B1/C1 with uncommitted work, Cursor, `fix/ulp-stress-advisory`) — left
  per track-ownership + #M-10 (don't delete worktrees with uncommitted/unpushed work). Local dirty:
  only `current.{claude,codex}.md` (intentional handoff working docs).
- Issues: **#2739 retitled** (intermittent finalize + trailer bug) + updated with findings;
  **#2732 labeled** `tech-debt`. No issue was directly closed by this session's PRs.

## 🔑 BIGGEST THING THIS THREAD: agy `--model` WORKS (#2742 merged)
The long-standing "NEVER pass `--model` to agy / it downgrades to CCPA" rule was a **MISDIAGNOSIS**.
- Root cause: #2731 passed the **slug** `gemini-3.1-pro-high`, which agy's `--model` flag rejects.
  agy wants the **display label** (`"Gemini 3.1 Pro (High)"`, from `agy models`). The #2735 revert
  then misread a **benign** `resolver.go … defaulting to CCPA` log line as "the label fails too."
- **Empirically disproven** (probe + e2e through the adapter): `agy -p --model "Gemini 3.5 Flash (High)"`
  with the TUI on Pro logged `Propagating selected model override to backend: label="Gemini 3.5 Flash
  (High)"` and ran Flash. **`--model` OVERRIDES the TUI selection.**
- Fix (ports `kubedojo/scripts/agent_runtime/adapters/agy.py`, PR #2742): adapter `_normalize_model`
  collapses slug↔label, `_resolve_model_flag` maps either to the canonical label, and passes
  `--model "<label>"`. Unknown/empty → `default_model`; unmappable → flag omitted. 8 adapter tests.
- **Bonus:** passing `--model` makes telemetry record the REAL model (was a hardcoded
  `LEARN_UK_AGY_MODEL` default — do not trust the model field on no-`--model` runs).
- **Dispatch now:** `delegate.py dispatch --agent agy --model "Gemini 3.5 Flash (High)" --task-id <id>
  --mode danger --worktree --base main --prompt-file <brief>` (slug OR label both accepted).
- kubedojo is at `/Users/krisztiankoos/projects/kubedojo` — useful reference repo (it had fixed this).

## 🔑 MODEL ROUTING DEFAULT (user direction 2026-06-05)
- **agy CODING → `Gemini 3.5 Flash (High)`.** **agy CONTENT/creative writing → `Gemini 3.1 Pro (High)`.**
- Basis: a controlled bakeoff (below) where **Flash beat Pro on coding (N=1)**. Creative→Pro is the
  user's prior, **untested** — validate it next time we do agy content work (agy is a pending
  seminar-track writer candidate; that's the place to test Pro-for-writing). Keep scoring; not dogma.

## ✅ #1863 Phase 1 DONE — dead-code inventory tool merged (#2741)
`scripts/audit/find_dead_code.py` (report-only, categories A–J) + `tests/audit/test_find_dead_code.py`
on main. agy authored (3.1 Pro run); DeepSeek+Claude review (REQUEST-CHANGES) → I fixed (category-D
`git ls-files -i` needed `-c`; vulture `--exclude`; G/J renamed; deterministic sort; report git-ignored;
trailer) → merged. **NEXT: #1863 Phase 2** = run the merged tool, triage the report, file the 10
category sub-issues (orchestrator work, ~1hr; see `docs/cleanup-plan-2026-q2.md`). Cleanup PRs are
strict: one-category-per-PR, adversarial-review-mandatory, archive-before-delete, NEVER touch curriculum.

## Pro vs Flash bakeoff (N=1, same #1863 brief)
| | Pro 3.1 High (#2741 raw) | Flash 3.5 High (preserved: `origin/agy/deadcode-tool-1863-flash`) |
|---|---|---|
| Category D `git ls-files -i` | ❌ missing `-c` (real bug) | ✅ `-i -c` + try/except |
| Tests | 6 | 11 |
| size / ruff / runs | 295 ln / ✅ / ✅ | 595 ln / ✅ / ✅ |
| X-Agent trailer | ❌ `agy` | ❌ `agy` |
Flash won. Flash artifact NOT merged (would conflict + needs own full review); fold its try/except
robustness into a follow-up if wanted.

## agy lane — operating notes (UPDATED; supersedes the old "never --model" rule)
- **`--model` works — pass the label or slug** (see above). Model is now a per-dispatch choice.
- **X-Agent trailer:** agy stamps `X-Agent: agy`, which FAILS `lint_agent_trailer.py` (`agy` is not a
  valid agent in the regex — valid: claude/codex/gemini/grok/deepseek-v4-pro/cursor/dependabot/claude-inline).
  **Future agy briefs MUST instruct `X-Agent: gemini/<task-id>`** (agy is Gemini-backed). Alternatively a
  1-line linter change could add `agy` — open choice, not yet done. I amended #2741's commit to `gemini/`.
- **needs_finalize is INTERMITTENT** (not always, #2739): the #1905 run timed out before commit
  (recover: review dirty worktree → commit `X-Agent: gemini/<id>` → push → PR); but the #1863 and the
  Flash runs committed + opened PRs cleanly. Mixed.
- Auth: headless works via macOS keyring after an interactive `agy login` (cmd not in `--help`).

## Earlier this session (already landed)
- **curl_cffi HIGH CVE fixed** (#2740): 1-line `--no-deps` lock bump; alert #119 auto-closed. The lock
  is systemically un-clean-resolvable (#1634-class: inscriptis/lxml + pillow/marker-pdf) → #2732
  re-scoped to lock-health. idna `.dagger` = #2732 Part 2 (needs dagger SDK env).
- **Dependabot drain: 8/8** (#2719-2726). **Code-scanning 2→0** (path-injection dismissed as documented
  CodeQL false-positives — #2733's realpath sanitizer is sound; scan still flags it).
- **Filed:** #2738 (MC distractor VESUM design Q), #2739 (agy needs_finalize). Both still open.

## Pending agy tech-debt work (user: "keep him working" on tech-debt, Flash for coding)
Bounded coding candidates scanned from open issues (most others are Codex/Claude-lane):
- **#2739** agy wrapper auto-finalize (option 2: returncode 0 + dirty + 0 commits → auto-commit/push/PR).
  Bounded + valuable but infra-sensitive (delegate/runner) — review carefully.
- **#1863 Phase 2** (mine, not agy): run tool → triage → file sub-issues. Natural next step.
- AVOID handing agy: #2378 (load-bearing linear-write.md trim, #M-11), EPICs, A1/A2 (Codex), bio (Claude).

## Restart
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin main && git merge --ff-only origin/main && git rev-parse --short HEAD
curl -s http://localhost:8765/api/delegate/active
gh pr list --state open --json number,title,isDraft
.venv/bin/python scripts/audit/find_dead_code.py --root . --output /tmp/inv.md  # Phase 2 starts here
```
