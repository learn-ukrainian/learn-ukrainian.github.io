# Stale-PR triage — 4 open PRs

**Date**: 2026-05-24
**Agent**: codex
**Mode**: danger
**Effort**: high
**Wall budget**: 60 min

## Why

4 PRs have been sitting open across recent days, blocked by stale conflicts or unaddressed CI failures. They're cluttering the queue and the orchestrator hasn't had cycles. Your job: triage each one, take the appropriate action (rebase+merge, close, or report unmergeable), and report final state.

`review/review` failures on these PRs are the persistent F7 GEMINI_API_KEY advisory — treat as advisory, never block on it.

## The 4 PRs (in your decision order)

### PR #2236 — docs(session-state) 2026-05-23 handoff (DIRTY)

```
gh pr view 2236
```

Probable action: **CLOSE** with explanation. Reason: this handoff has been superseded by today's session-state files (2026-05-24-overnight-cursor-end-to-end-m20-stuck-on-writer-protocol.md and the chain of PRs merged today: #2256, #2257, #2258, #2259, #2260). Session-state handoff PRs are non-load-bearing — they're for human historical context and become irrelevant once superseded.

Before closing: skim the diff. If it captures anything not in today's handoff (e.g. an autopsy or lesson), extract that piece into `docs/orchestrator-frictions.md` or `memory/MEMORY.md` first, THEN close.

If the content is unique and worth preserving as a standalone, rebase onto main + push + verify CI + merge.

Close with `gh pr close 2236 --comment "Superseded by docs/session-state/2026-05-24-* and the PR chain merged 2026-05-24 (#2256, #2257, #2258, #2259, #2260)."`

### PR #2235 — fix(parsers): correlate codex function_call_output + unwrap Wall-time envelope (UNSTABLE)

```
gh pr view 2235
gh pr diff 2235
```

Small fix (126/2, 4 files). Only failure is F7 advisory (treat as pass). Path:

1. Rebase onto main: `git fetch origin && git rebase origin/main` (in a fresh worktree off this branch).
2. Resolve any conflicts (likely minor in parsers).
3. Run targeted tests on the changed paths: `.venv/bin/pytest tests/agent_runtime/ -v` (or whatever the diff suggests).
4. Push: `git push --force-with-lease`
5. Watch CI: `gh pr checks 2235 --watch --interval 15`
6. If green (modulo F7): `gh pr merge 2235 --squash --delete-branch`. If any real failure: open new fixup commit OR report.

### PR #2229 — feat(bench): writer-bench v0 (DRAFT, DIRTY, 932 LOC)

```
gh pr view 2229
gh pr diff 2229
```

Judgment call. Context: writer-bench was designed for "6 writers × 5 modules matrix" benchmarking but was put on hold pending the m20 anchor ship. Today's session merged PR #2255 (cursor-tools wiring), #2258 (cursor adapter fix), #2260 (writer-prompt Option B fixes). The m20 anchor is STILL not shipping — but the benchmark itself is independent infrastructure.

**Decision criteria**:
- If the bench code is sound + independent of m20 status → rebase, un-draft, ship. Useful regardless of m20.
- If the bench depends on assumptions broken by today's merges (e.g. it hardcodes the old `# fmt` shape from PR #2260 or assumes Knowledge Packet anchors are stable) → close, file a new issue noting the new requirements.
- If you can't tell from the diff → leave it as draft, post a comment summarizing what would need to change to ship, return to orchestrator.

If shipping: `git fetch origin && git rebase origin/main` (in worktree), resolve conflicts, run full pytest on bench tests, push, mark ready-for-review, watch CI, merge.

If closing: `gh pr close 2229 --comment "Closing — <reason>. File a new issue if writer-bench infrastructure is still wanted."`

### PR #2226 — deps: bump torchvision from 0.26.0 to 0.27.0 (BLOCKED)

```
gh pr view 2226
gh pr checks 2226 --json name,bucket,link
gh run view <pytest-run-id> --log-failed | head -50
gh run view <codeql-run-id> --log-failed | head -50
```

Real failures (pytest + CodeQL). Investigate:
1. What pytest test failed? Is the failure related to torchvision API changes 0.26→0.27?
2. What CodeQL alert is new? Is it from the bump or pre-existing on this branch?

Decision tree:
- If failures are unrelated to torchvision (flake / pre-existing on main): re-run CI, merge if subsequently green.
- If failures are real torchvision compat breaks: file an issue describing the break, post a PR comment naming what would need to change in our code, close the PR (dependabot will reopen when 0.27.1 / 0.28 releases or we adapt). Use `gh pr close 2226 --comment "..."`.
- If you can quickly fix our code to be compatible with 0.27 (e.g. a deprecated API call): push a fixup commit, watch CI, merge.

## REQUIRED steps

1. Use ONE worktree at `.worktrees/dispatch/codex/pr-triage-2026-05-24` (the dispatch system will create it).
2. From the worktree, handle each PR in order (#2236 → #2235 → #2229 → #2226). For PRs requiring rebase/push, switch to per-PR worktrees as needed via `git worktree add`.
3. For each PR, document the action taken in your response (CLOSE / MERGE / REPORT_BLOCKER + reason).
4. NO auto-merge on PRs that have real failures.
5. NO admin-bypass on any blocking CI (per #M-0.5).

## Output format

End your response with a structured summary:

```
PR_TRIAGE_RESULT:
- #2236: <CLOSED|MERGED|HELD> — <one-line reason>
- #2235: <CLOSED|MERGED|HELD> — <one-line reason>
- #2229: <CLOSED|MERGED|HELD> — <one-line reason>
- #2226: <CLOSED|MERGED|HELD> — <one-line reason>
```

## Verifiable claims

| Claim | Evidence |
|---|---|
| "PR #X merged" | `gh pr view X --json state,mergedAt` raw |
| "PR #X closed" | `gh pr view X --json state,closedAt` raw |
| "Tests pass on rebased branch" | `pytest` final line raw |
| "CI green after fixup" | `gh pr checks X --json bucket` showing all pass (modulo F7) |
| "Conflict resolution" | `git diff --stat HEAD~1..HEAD` after rebase |

## Anti-fabrication (#M-4)

Every claim tool-backed. Don't paraphrase test output or PR state.

## Time budget

60 min wall. Allocate roughly: 15 min #2236 (likely close), 15 min #2235 (likely merge), 20 min #2229 (judgment), 10 min #2226 (likely close + file issue). If a PR runs over, document and move on.
