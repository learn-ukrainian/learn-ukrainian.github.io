# Session Handoff — 2026-04-26 (session close)

> **Predecessor (full detail):** `2026-04-26-round-3.5-shipped.md`
> **Mode:** Final state snapshot. All worktrees cleaned, all PRs merged.
> **Successor scope:** A1/20 re-run; round 3.5 success vs round 4 bakeoff decision.

This is a short post-merge addendum to the round-3.5 handoff. The substantive work (what shipped, why round 3.5 before round 4, decision table for next session, behavioral notes) lives in the predecessor file. Read that first.

---

## What this session ended up shipping

Two PRs squash-merged into `origin/main` after the predecessor handoff was written:

```
00a0b0115b  docs(session): handoff after round 3.5 shipped (#1602) (#1605)
9294dedbbe  feat(phase-4): round 3.5 writer prompt + whitelist tighten (#1602) (#1603)
```

Both gated by parallel Gemini-3.1-pro-preview + Codex-gpt-5.5 adversarial review per the corrected workflow added 2026-04-26. PR #1603 ran the full pattern (review → revisions → CI green → merge). PR #1605 is docs-only.

## Issues touched

- **#1602** — closed via PR #1603 (`closes #1602` keyword). AC verification posted as comment `learn-ukrainian/learn-ukrainian.github.io#1602#issuecomment-4322646320`.
- **#1604** (NEW) — schema-generator drift: `PhraseTable` and other vocabulary-tab activity components emit `activity_type: null` in `lesson-schema.yaml`, causing the round-3.5 renderer to fall back to a `# WARNING:` line. Root cause needs `scripts/build/generate_lesson_schema.py` to assign `phrase-table` to PhraseTable. ACs include a unit test that asserts every type in any track's `*_ALLOWED_TYPES` resolves to a real schema entry. Filed as Phase-5-stage follow-up; not Phase-4-blocking.

## Worktree state at close

```
/Users/krisztiankoos/projects/learn-ukrainian                              [main, b532271f3d — user WIP, behind origin/main 9 commits]
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/codex-interactive (stale, detached HEAD — pre-existing, NOT mine)
```

Both round-3.5 worktrees (`claude-1602-round-3.5-prompt-tighten` + `claude-1602-handoff-round-3.5`) and their branches removed post-merge. The user's main checkout HEAD `b532271f3d` is intentionally behind `origin/main` — that's their working tree with uncommitted edits from in-flight wiki rebuilds. Do **not** `git pull` from there.

## What's left for the next session

**One decision, one user action, then the path forks.** See the decision table in `2026-04-26-round-3.5-shipped.md` for full criteria.

```bash
# The user runs:
.venv/bin/python -m scripts.build.linear_pipeline a1 my-morning --writer gemini-tools

# Then the orchestrator inspects:
cat curriculum/l2-uk-en/a1/my-morning/module.md | head -40
cat audit/a1/my-morning.json | jq '.gates'
```

If gates green and module prose is meta-narration-free → round 3.5 is canonical, dispatch Phase 5 fan-out. If not → either iterate prompt-tighten (round 3.75) or fire round 4 bakeoff per the failure pattern.

## Carry-forward behavioral notes (from PR #1603 review cycle)

1. **Parallel adversarial review at PR open is cheap and load-bearing.** ~3-4 min wallclock for two reviews; on PR #1603 it caught 7 findings (3 BLOCKER) that would have either shipped silently or surfaced during build. Cheaper than silent-merge then bug-then-fix.
2. **Don't fail-loud when the failure mode is unrelated drift.** The `phrase-table` BLOCKER was tempting to fix with `raise LinearPipelineError`, but that would have blocked round 3.5 dispatch on a separate generator-side bug (#1604). Skip-and-warn + follow-up issue is the right scope when the immediate goal is unblocking the next experiment.
3. **Test sentinels need self-tests.** The JSX-object-literal test broke because `Ліна` got whitelisted; new sentinel `Маркіян` carries an `assert "Маркіян" not in PROPER_NAME_WHITELIST` so the next agent can't silently degrade it.
4. **Bot review failures are non-blocking; admin-merge once real CI is clean.** PR #1605 needed `gh pr merge --admin` because `review / review` (advisory Gemini-Dispatch bot) failed on docs-only changes — branch protection blocked. Per memory rule #0H this is the right call.

## Active background tasks at close

**None of mine.** All background watchers/dispatches completed and reported. 4 user-launched Gemini wiki rebuilds may still be running per the predecessor handoff; the orchestrator should commit them when `pgrep -f "compile.py.*--track"` empties (follow `b7db136b1d` pattern).

## Cold-start protocol for successor

```bash
# 1. Verify state
git -C /Users/krisztiankoos/projects/learn-ukrainian log --oneline origin/main -5
# Expect (top): 00a0b0115b docs(session) → 9294dedbbe round 3.5 → ab253e00f1 → ccfe0aaac0 → a6b9e7f417

curl -s 'http://localhost:8765/api/comms/inbox?agent=claude'   # expect empty
gh pr list --state open --limit 10                              # expect no Phase 4 PRs

# 2. Read this file + the round-3.5 predecessor (full detail)
ls -lt docs/session-state/2026-04-26*.md | head -5

# 3. If user has run the A1/20 re-test, decide round 3.5 vs round 4 per
#    the table in 2026-04-26-round-3.5-shipped.md.
```

## Final stats for the day's work (across the round-3.5 sessions)

- **3 PRs shipped** to `origin/main`: #1598 (strict-JSON), #1599 (QG bugfixes), #1603 (round 3.5)
- **2 docs PRs**: #1600 + #1605 (handoffs)
- **1 follow-up issue filed**: #1604 (schema-generator drift)
- **13 new regression tests** in `tests/build/test_linear_pipeline.py` from the round-3.5 PR alone
- **0 open Phase 4 PRs** at close
- **0 background tasks** owed
