---
date: 2026-05-18
session: "Mid-night handoff after user surfaced the cascade-risk orchestration dilemma at 02:30: 'we need to correctly handle error-correction activity, it is a very important activity type. lets do a session handoff and you can continue driving the project plus resolving the tech debts, look at how many tech debts we have. and i fear that if we solve a tech debt too late it might have cascading effect on module writing. can you handle this orchestration dilemma?' This handoff is the answer to that question + the drive plan for the rest of the night."
status: green
main_sha: f2e7fd7f7f
main_green: true
total_open_issues: 33
prs_merged_this_overnight: [2120, 2121, 2122, 2123, 2124, 2125]  # see prior handoff
prs_open: [1873]  # dependabot starlight only — user-owned
active_dispatches:
  - 2128-vesum-bad-marker-20260518-024000: codex gpt-5.5 xhigh, 17s in at handoff, ETA 30-45 min. Fixes #2128 properly (writer prompt + gate-side safety net for negative-example pattern in TF statements). Highest cascade-risk fix tonight.
m20_status: NOT_SHIPPED. Two build attempts failed (build #1 PR3 corrector contract violation #2127, build #2 vesum_verified false-positive #2128 — being fixed now). Architecture (Path 3 PR1-4 + PTY fix) is in main and sound; writer-side + gate-whitelist fixes are the remaining blockers.
---

# Cascade-risk orchestration handoff — answer to the dilemma + drive plan

## RIGHT NOW (post-/clear cold-start — read this first)

Time at handoff: **2026-05-18 08:48 CEST** (user leaving for work; clearing context but NOT restarting — same session_id, fresh context).

**1 active dispatch — DO NOT KILL:**
- `2128-vesum-bad-marker-20260518-024000` — codex gpt-5.5 xhigh
- Started 08:40 CEST (06:40 UTC), 8 min in at handoff
- silence_timeout=3600s, hard_timeout=7200s
- ETA: 25-40 min from handoff (~09:15-09:30 CEST)
- Worktree: `.worktrees/dispatch/codex/2128-vesum-bad-marker-20260518-024000/`
- Brief: `docs/dispatch-briefs/2026-05-18-2128-vesum-bad-marker-convention.md`

**ScheduleWakeup pending** at 09:13 CEST. Will re-invoke and the cold-started session will pick up from there.

**Immediate cold-start sequence (when wakeup fires OR user re-engages):**

1. `curl -s http://localhost:8765/api/delegate/active` — confirm #2128 dispatch state (running / done / timeout).
2. `gh pr list --state open --json number,title,statusCheckRollup --limit 5` — check if `fix/2128-vesum-bad-marker-everywhere` PR opened.
3. **If PR opened + blocking CI green** (`review/review` advisory fail is OK — see #2126): squash-merge it.
4. **After #2128 merges**: write a #2127 brief modeled on `docs/dispatch-briefs/2026-05-18-2128-vesum-bad-marker-convention.md`. Fire to Codex with `--silence-timeout 3600 --worktree`. Don't fire while #2128 still in-flight — they merge-conflict on `linear_pipeline.py`.
5. **While #2127 runs**: re-fire `v7_build.py a1 my-morning --worktree` via `Monitor` tool to confirm #2128 fix unblocks the previously-stuck step. The two m20 build worktrees are preserved at `.worktrees/builds/a1-my-morning-20260517-234227/` and `.worktrees/builds/a1-my-morning-20260518-000636/` for diagnosis.
6. Continue per the **Tonight's drive plan** section below.

**If post-clear orchestrator wakes BEFORE the dispatch lands**: schedule another wakeup (1200s = 20 min) and end the turn. Do NOT poll — Monitor + Wakeup will fire on relevant events.

**Do NOT kill the active dispatch.** User direction explicit: "no need to kill active processes."

---

## TL;DR

1. **Cascade-risk framing is correct.** Of the 33 open issues, ~10 cascade directly to module writing — if not fixed, every future module ships with the same paper-cut OR fails outright. The other ~23 are bounded (single feature / single agent / data acquisition blocked on materials).
2. **Triaged into 4 tiers** (HIGH / MEDIUM / LOW cascade + EPIC). Drive HIGH first; that's exactly what I did in the prior overnight cascade. Tonight added #2128 (vesum whitelist) firing now.
3. **Queue order encoded explicitly below.** I can drive 3-4 cascading fixes per night using parallel dispatch capacity (2 Codex / 2 Gemini / 2 Claude pre-June-15 / 2 DeepSeek / Grok-discuss-only).
4. **Three escalation triggers** state when to wake the user rather than self-decide.

---

## Tech debt inventory — cascade-risk categorization (33 issues)

### HIGH CASCADE — every module hits this (FIX FIRST)

These directly break or degrade the module-build pipeline. If unfixed, m20 ship today implies fixing them after-the-fact for each subsequent module.

| Issue | What | Cascade scope | Status |
|---|---|---|---|
| **#2128** | vesum_verified false-positive on TF statements naming a wrong form (e.g. "X, а не Y") | Every module with `true-false` activities teaching a contrast — i.e. effectively every module | **FIRING NOW** (codex dispatch 02:40, ETA 03:10) |
| **#2127** | PR3 corrector violated `<fixes>`-only contract + YAML guard miss | Every module that fails wiki_coverage_gate (most A1/A2 modules with strict 18+ obligations) | NEXT (fire after #2128 lands to avoid linear_pipeline.py merge conflict) |
| **#1807** | codex-tools writer treats `<verification_trace>` blocks as prose, not metadata | Every module built with codex-tools writer (currently NOT default, but blocks any future codex-tools attempt) | LOW PRIORITY until/unless we switch writer |
| **#1969** | resources_search_attempted=0 regression — multimedia search obligation crowded out | Every module that has multimedia obligations (most) | MEDIUM priority — file a focused fix after #2127 |
| **#2036** | hermes/auth Claude-via-Hermes silently returns empty stdout | Blocks any claude-via-hermes dispatch path | MEDIUM — affects future runtime config, not immediate |
| **#2039** | grok-tools writer under-target word count (~52%) | Blocks grok-tools writer use | LOW — claude-tools default; revisit if Grok lane needed |
| **#2071** | Codex dispatch hangs with response_chars=0 (block-buffered stdout) | Was every long Codex dispatch — **FIXED tonight by PR #2124 (PTY)** | Issue stays open per #M-8 until a long Codex dispatch succeeds confirming the PTY fix in production. CLOSE when next 60+ min Codex dispatch ships clean. |
| **#1975** | build/m20 vesum_verified malformed forms (PREDATES #2128 — likely SAME root cause) | Subsumed by #2128. Close as duplicate when #2128 merges. | Close-with-fix on #2128 merge |
| **#2126** | review/review CI action failing 45s UNKNOWN STEP | Advisory not blocking, but noisy — clutters every PR's check status | LOW (advisory) — file API-key audit task for morning |

### MEDIUM CASCADE — blocks specific feature/agent, not every module

| Issue | What | Cascade scope |
|---|---|---|
| #2023 | bridge Claude --bare auth for OpenAI proxy | bridge users only |
| #1908 | layered-harness audit | observability/quality only |
| #1933 | /goal driver improvements (4 follow-ups) | /goal-driven autonomous runs only |
| #1916, #1918 | Phase A/B follow-ups | calibration only |
| #1960 | wiki-ingestion external articles stored as ext-article-N stubs | wiki-source quality only |
| #1782 | persistent agent listeners (decision-pending) | agent-comms only |
| #2116 | claude-i tmux wrapper research | post-June-15 dispatch lane only |
| #2072 | Grok integration extend (file edits / git ops) | unblocks grok writer-quality fix #2039 |

### LOW CASCADE — bounded bug / cleanup / data acquisition

| Issue | What |
|---|---|
| #2048, #2052, #2053, #2054 | Data acquisition (Karavansky, Holovashchuk, Paronyms, R2U) — **blocked on user-provided materials**; defer until user provides |
| #1794, #1799 | Guardrail follow-ups (small) |
| #1896 | Secret-leak prevention follow-ups (autopsy backlog — no recurrence since 2026-05-12) |
| #1905 | Pipeline replay-mode regression suite (nice-to-have for cost reduction) |
| #1914, #1940 | Curriculum schema follow-ups |

### EPICs — multi-month work

| Issue | What |
|---|---|
| #1577 | Curriculum reboot vertical slice (A1+A2+B1) |
| #1657 | MCP verification-layer improvements (3-phase plan) |
| #1814 | HTML artifact serving + navigation UI |
| #1863 | Repo cleanup sprint (Q2) |
| #1865 | Context budget optimization (subscription-tier quota burn) |

---

## Answer to the orchestration dilemma

**Yes — the dilemma is real and solvable with explicit prioritization.**

### Recognize the asymmetry

- HIGH-cascade tech debt: every day you delay multiplies the cost across N modules. Cost of late fix = N × per-module-friction.
- LOW-cascade tech debt: cost is constant. Delay is free until you touch that surface.
- Module shipping itself: each shipped module reveals new HIGH-cascade gaps you couldn't predict (today's m20 → discovered the TF-statement whitelist gap that no prior module exposed).

### Heuristic for queueing

Per "drive" turn (or autonomous overnight cycle):

1. **Discover** — Build the next failing module. The failure surface IS the diagnostic for which HIGH-cascade debt actually matters.
2. **Triage** — Classify each failure: is this writer-side (writer can fix in next iteration), gate-side (cascades to every future module), or one-off (only this module).
3. **Fire ONE HIGH-cascade fix per cycle** to a dispatched agent with a tight brief. Don't queue 5 simultaneously — they conflict in `linear_pipeline.py` and pile reviewer load.
4. **In parallel**: rebuild the same module after the fix lands to confirm + advance.
5. **Loop**: each iteration either ships the module OR discovers the next HIGH-cascade debt.

This is what tonight's pattern was: built m20 → discovered #2127 → built m20 again → discovered #2128 → firing #2128. Each iteration reduced the surface of unknown cascading bugs.

### What NOT to do

- Don't pre-fix LOW-cascade debt during ship-drive overnight cycles. Cost is constant; bias attention to HIGH-cascade.
- Don't fire multiple HIGH-cascade dispatches touching `linear_pipeline.py` concurrently. They merge-conflict; reviewer load multiplies.
- Don't keep retrying the build with the same prompt + same gates after 2 distinct failure modes. The third failure mode might be a writer change you didn't make — but the user's #1 rule forbids lowering thresholds to ship, so stop and dispatch the fix.

### Explicit decision boundaries (when to escalate)

ESCALATE to user (wake up / pause autonomous drive) when:

1. **Quality threshold question**: "Should we ship m20 at 78% coverage instead of 80%?" — user policy #1 says no, but explicit case asks for review.
2. **Architectural change required to fix cascading debt**: e.g. "vesum_verified needs a new schema field on every plan" — schema changes need user sign-off.
3. **Budget burn**: when 3+ Codex/Claude dispatches in a row don't ship a working PR, stop and ask before firing more.

DON'T escalate (just drive) when:

- HIGH-cascade fix is well-scoped with clear acceptance criteria (e.g. tonight's #2128 brief).
- Next module-build attempt would expose a different cascading bug.
- A specific dispatch failed but the diagnosis is clear (write a brief, re-fire, don't ask permission).

---

## Tonight's drive plan (continuing past this handoff)

### In flight
1. **#2128 vesum fix** — codex dispatch 02:40 → ETA 03:10 → on merge, re-fire m20 v7_build → expected: passes vesum_verified, may still hit `l2_exposure_floor` (13 vs 14) and `inject_activity_ids` (4 unused).

### Queue (in order, fire after preceding lands)
2. **#2127 PR3 corrector contract** — fire after #2128 lands (avoid linear_pipeline.py conflict). Tighten correction prompt template with anti-pattern callout + per-fix size cap + YAML round-trip-and-rollback validator. Brief similar shape to #2128.
3. **m20 v7_build retry** — after both #2128 + #2127 land. If it still hits `l2_exposure_floor` / `inject_activity_ids`, file as #2129 (writer-side, not cascading) and either inline-patch the writer output for one-time ship or write a small writer-prompt patch.
4. **Close #2071 + #1975** once #2128 lands and a long Codex dispatch confirms PTY in production.

### After m20 ships
5. **Build m15-m19** (other A1 modules) using the same pipeline. Each will expose its own cascading gaps; iterate.
6. **Address #2126** (advisory CI fail) — small, but reduces PR-review noise.

---

## What's NOT in scope without user input

- **Decision: switch default writer from claude-tools to codex-tools or gemini-tools.** Current decision lives at `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md`. Revisit only if the writer prompt fixes don't ship m20 within ~3 more attempts.
- **Lower any quality threshold** (`l2_exposure_floor` from 14 → 13 example sentences, `WIKI_COVERAGE_MIN_PCT_BY_LEVEL` from 80% → 70%, etc.). Project rule #1 forbids; if a threshold seems wrong, file as separate plan-revision discussion, don't silently lower.
- **Manual writer-output patch to ship m20 as one-off.** Sets a bad precedent. If we ship m20 by hand-correcting artifacts, every future module will tempt the same.

---

## Active state at handoff

- Main `f2e7fd7f7f` (post-PR3+PR4+PTY merges).
- 1 active dispatch: `2128-vesum-bad-marker-20260518-024000` (codex xhigh, silence_timeout=3600s, hard_timeout=7200s).
- Worktrees:
  - 2 m20 build worktrees preserved for diagnosis (`a1-my-morning-20260517-234227` build #1 + `a1-my-morning-20260518-000636` build #2)
  - 1 vesum-fix worktree active (`.worktrees/dispatch/codex/2128-vesum-bad-marker-20260518-024000`)
  - 1 unpushed gemini analysis worktree (`gemini/artifacts-workflow-analysis-20260517-215135` — pushed, but worktree still alive; safe to reap when slot needed)
- MEMORY.md at 150/150 hard limit. Don't add without trimming.
- Open issues: 33 (per inventory above).

## Cold-start checklist (when continuing after wakeup)

1. Read THIS doc + the predecessor `docs/session-state/2026-05-18-overnight-pty-fix-plus-m20-architecture-shipped.md` for prior context.
2. `curl -s http://localhost:8765/api/delegate/active` — check if #2128 dispatch still alive or done.
3. `gh pr list --state open` — if a `fix/2128-vesum-bad-marker-everywhere` PR opened, review + merge (advisory `review/review` failure ≠ blocking per #2126).
4. After #2128 merges: write #2127 brief (use #2128 brief as template), fire to Codex.
5. While #2127 runs: re-fire m20 v7_build via Monitor to see if `vesum_verified` now passes for `дивюся`.
6. Iterate per drive plan above.

## Cross-references

- Prior overnight handoff: `docs/session-state/2026-05-18-overnight-pty-fix-plus-m20-architecture-shipped.md`
- Path 3 Decision Card: `docs/decisions/2026-05-17-path3-per-obligation-review-loop.md`
- Active dispatch brief: `docs/dispatch-briefs/2026-05-18-2128-vesum-bad-marker-convention.md`
- Open issues affecting cascade: #2127 (corrector), #2128 (vesum), #1975 (vesum predecessor), #1807 (codex writer), #1969 (multimedia search), #2036 (hermes auth), #2039 (grok writer), #2071 (codex hang → fixed tonight)
