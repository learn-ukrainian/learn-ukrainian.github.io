# Session Handoff — 2026-04-22 afternoon: ops + infra pass, #1370 dispatched

> **Status:** LANDED — all work committed/dispatched, session ending at 14:00 CET for peak window.

## TL;DR

Between the morning Phase 3 pre-flight handoff (`2026-04-22-merges-landed-phase-3-pre-flight.md`) and the 14:00 CET peak-window stop, this session did **zero content work** and instead landed a comprehensive ops + infra pass: Claude Code 1.117 practice adjustments, context discipline hard rules, git hygiene, effort-wiring across adapters, and the Phase 3 blocker dispatch (#1370 writer-prompt hardening, running at `--effort xhigh` in background).

Main at **`58b1ea1c9`** (post `feat: --effort wiring for claude/codex dispatch (#1396) (#1397)`), pushed to origin.

## Prior session chain (navigation only, content not restated)

| Session | File |
|---|---|
| Overnight autonomous | `2026-04-22-overnight-bakeoff-and-124-plan-forks.md` |
| Morning decisions | `2026-04-22-decisions-locked-and-merge-prep.md` |
| Pre-flight Phase 3 | `2026-04-22-merges-landed-phase-3-pre-flight.md` |
| **This** | `2026-04-22-afternoon-ops-infra-pass.md` |

## What landed in this session

### 1. Claude Code 1.117 practice adjustments

- Verified launcher: `start-claude.sh` → `npx @anthropic-ai/claude-code@latest`, resolved to **2.1.117** at start time, `CLAUDE_CODE_AUTO_COMPACT_WINDOW=750000`, `--chrome --permission-mode bypassPermissions`.
- Sources MCP verified live (12 collections); `verify_lemma` returns full VESUM morphology.
- npm-installed build intentional per user (native had a cache bug) — `bfs`/`ugrep` native-build replacements do NOT apply.

### 2. Context discipline — HARD RULES (MEMORY #2 rewritten)

- **Cap 750K.** Handoff trigger: 300K early signal → 400K handoff zone → 450K past target.
- **NEVER use `/compact` or `--resume`.** 1.117 auto-summarizes stale sessions — resume is now more expensive, not less.
- **Diary handoff files confirmed correct** (multiple per day is the right granularity; each reads one file, not chain).
- **Self-check ctx via Bash** (one-liner in MEMORY) — I can read my own token count, don't need to estimate.
- **Calibration lesson:** my self-estimates run ~1.8× high. When I felt 350K, actual was 191K. Bias toward running the check.

### 3. Time-of-day + overnight discipline (MEMORY #2)

- **14:00–20:00 CET PEAK:** MINIMAL work. Triggered this session's stop.
- **Overnight (user sleeping):** main session = orchestrator ONLY. ALL execution dispatched. Claude-needed work → `delegate.py dispatch --agent claude`.

### 4. Statusline + Stop-hook

- `~/.claude/statusline.sh` — aligned thresholds (300/400/450) + rate-limit segments (5h, 7d) when elevated.
- `~/.claude/context-check.sh` — Stop hook; colored warning + terminal bells on threshold crossings only, silent on repeat-same-bucket.
- `settings.json`: `cleanupPeriodDays: 14` + Stop-hook registered.

### 5. Git hygiene (#1394 closed)

- `fetch.prune` + `fetch.pruneTags` on.
- Aliases: `git cleanup-gone`, `git pr-done`.
- Post-merge hook: auto-prunes gone-upstream branches when merging TO main.
- **170 → 18 local branches, 15 → 5 worktrees** (Phase 1+2 complete).

### 6. Effort wiring (#1396 closed, PR #1397 merged)

- `delegate.py dispatch --effort {low|medium|high|xhigh|max}` now wired through to Claude + Codex adapters.
- First-class kwarg (not `tool_config` cargo) per Codex adversarial review.
- Version-gated on Claude side via `scripts/utils/claude_version.py`.
- 20 new tests (`tests/test_agent_runtime_effort.py`), 144 existing tests pass.
- Follow-up issue **#1398** filed for Gemini effort (blocked on gemini-cli exposing a flag).

### 7. Writer-prompt hardening DISPATCHED (#1370)

**In flight as of 14:00 CET stop** — will complete during peak window. Progress at stop: 3 commits already on branch (AC-A done, AC-D re-test fired, mid AC-F adversarial review). ~42 min elapsed of ~2h budget.

- Task ID: `claude-1370-writer-harden`
- Worktree: `.worktrees/claude-1370-writer-harden`
- Branch: `claude/claude-1370-writer-harden`
- Model: **Opus 4.7, `--effort xhigh`** (first production use of the newly-merged wiring)
- Hard-timeout: 2h
- PID: 30691 (at dispatch time)
- Brief: `.worktree-briefs/1370-writer-prompt-harden.md`

**Expected output:**
- Hardened `scripts/build/phases/v6-write.md` (activity-count contract + Ukrainian-brief metalanguage guard)
- Maybe `scripts/audit/checks/metalanguage_containment.py` (if prompt-only fix insufficient)
- Re-test on A1 M03 `special-signs` — target 8.0+ mean and at least 1 PASS vs. bakeoff baseline 7.80/0-PASS
- Codex adversarial review before PR open
- PR opening → main when done

Background wait is running (`delegate.py wait claude-1370-writer-harden`). Notification will fire when it lands.

## Open issues filed this session

| # | State | Topic |
|---|---|---|
| 1394 | CLOSED | Git hygiene (aliases + hook) — done |
| 1395 | OPEN (deferred) | `/api/git/cleanup` endpoint |
| 1396 | CLOSED | Effort wiring — PR #1397 merged |
| 1397 | MERGED | The PR for #1396 |
| 1398 | OPEN | Gemini effort wiring (awaits gemini-cli support) |
| 1399 | OPEN | Phase 3 branch triage (19 remaining branches) |

## What is NOT done

- **#1370 PR not yet open** — dispatch still running at stop time.
- **Phase 3 branch triage (#1399)** — 18 branches still in triage queue. Group A (bakeoff forks) and Group B (writer-bakeoff outputs) are near-safe-deletes once verified.
- **Agent frontmatter `mcpServers` scoping** (queued earlier) — not touched.
- **#1395 `/api/git/cleanup` endpoint** — still deferred per plan.

## Peak-window dispatches (14:00 onward — three agents working concurrently)

User correction at 14:03 CET: stopping Claude at 14:00 without firing dispatches to the CHEAPER agents is a waste of the peak window. Fired two parallel dispatches so the window is productive:

| Agent | Task ID | Scope |
|---|---|---|
| Codex | `codex-peak-ci-red-and-force-audit` | Fix pre-existing CI red on main (1 ruff error + no-new-root-scripts + gitleaks-license decision) + `--force` audit from deferred #1394 AC |
| Gemini | `gemini-peak-bakeoff-patterns` | Analysis across all 20 bakeoff review YAMLs — rank systemic gaps BEYOND activity-count → `docs/experiments/2026-04-22-writer-bakeoff-patterns.md` |

Plus Claude already running: `claude-1370-writer-harden`. Three concurrent worktrees. All fire-and-forget, background `delegate.py wait` will notify on each completion. Expected three PRs waiting at 20:00 CET.

Briefs at:
- `.worktree-briefs/codex-peak-ci-red-plus-force-audit.md`
- `.worktree-briefs/gemini-peak-bakeoff-pattern-analysis.md`
- `.worktree-briefs/1370-writer-prompt-harden.md` (from earlier)

## What to do when resuming (afternoon/next session)

1. **Cold-start via Monitor API** per `workflow.md` (not direct file reads).
2. **Check #1370 landing:**
   ```bash
   .venv/bin/python scripts/delegate.py status claude-1370-writer-harden | jq '{status, duration_s, returncode}'
   cat batch_state/tasks/claude-1370-writer-harden.result | head -40   # final response
   gh pr list --state open --search 1370
   ```
3. **If #1370 PR is open:** review diff, run local ruff, check adversarial review comments, merge (squash, delete branch, `git pr-done .worktrees/claude-1370-writer-harden`).
4. **Then:** single-slug A1/M03 re-test against the hardened prompt (AC-D in the brief). Numbers vs. bakeoff baseline determine whether Phase 3's 124-module batch is green-lit.
5. **Phase 3 fire decision** — if hardened re-test PASSes, you fire the 124-module build. Infrastructure (effort wiring, git hygiene, dispatch briefs) is now ready.

## Operational notes

- Main at `58b1ea1c9`, clean, pushed.
- Active worktrees: `main`, `.worktrees/claude-1370-writer-harden` (running), `.worktrees/codex-1392-plan-latin-fix` (open issue), 3 bakeoff fork worktrees (Phase 3 triage queue).
- Disk: not rechecked this session; previous handoff said 34 GB free.
- Background `delegate.py wait` process will fire a notification on #1370 completion. Do NOT kill it manually.
- CI red on main is pre-existing (same failures before #1397 landed). Not a blocker for future merges but should get its own cleanup issue.

## Key commits (this session)

```
58b1ea1c9 feat: --effort wiring for claude/codex dispatch (#1396) (#1397)
4aa9305a7 chore(session): land 2026-04-22 handoff + dispatch briefs for #1370 + #1396
90f49b629 [prior session root]
```

Plus the 4 commits squashed into 58b1ea1c9 from #1397 (implementation + tests + docs + gemma-local fix).

---

**Handoff complete.** Stopping per 14:00 CET peak-window discipline. #1370 dispatch will land autonomously; background wait will notify.
