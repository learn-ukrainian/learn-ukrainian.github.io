# Session Handoff — 2026-04-23 late evening: Claude-heavy dispatch wave

> **TL;DR** Session 21:00–23:30 CET. Five PRs merged on main. ADR-007
> signed Y/Y/Y; its PR wave is in flight (5 dispatches running at handoff).
> User directive: shift load to Claude until at least Monday — reversing
> earlier Codex-heavy posture. Effective caps now 3+ Claude / 2 Codex
> concurrent. Colors pilot is still blocked (same gates as the 20:30
> handoff: ADR-007 PR-A/B/C/D/F + #1462 + #1455 + PR-E must merge before
> fire). Main session caught two CI bugs inline during PR review (xdist
> determinism on #1495, DB-availability guard on #1497) rather than
> bouncing them back to dispatchers. Working tree cleaned 96→~20 items.
> 32 stale remote branches + 22 stale local branches pruned. Context
> ~300K / 750K ceiling — comfortable, no early handoff required.
>
> **Read this whole file before dispatching anything. ADR-007 PRs land
> overnight; first morning work is reconciling what actually merged.**

---

## What landed this session (merged to main, newest first)

| PR | Issue | What | Impact |
|---|---|---|---|
| #1498 | #1454 | **threshold source of truth** — unify writer/reviewer/audit/plan-contract thresholds into a single exported table | ✅ **unblocks EPIC #1451 Phase 5 gate** and ADR-007 PR-E |
| #1497 | #1460 | **citation resolution invariant** — every published `[S#]` must resolve to `sources.db`; CI-skipped when DB absent | ✅ Phase 4-A done (with KNOWN_DRIFT xfail for 7 already-filed orphans — see #1488–#1494) |
| #1496 | — | session docs + colors smoke evidence commit | tree hygiene; captured pre-ADR colors R1 artifacts |
| #1495 | #1461 | **Unicode round-trip golden-corpus invariant** — й/ї/ь preservation through tokenize → render cycle | ✅ Phase 4-B done (locks in #1448 tokenizer fix) |
| #1484 | — | starlight subtitle polish + **ADR-007 sign-off** (Y/Y/Y on all three open questions) | ADR-007 approved; flips to ACCEPTED when the PR wave lands |

**Governance / infra:** no branch-protection or workflow changes this
session. ADR-007 codification is entirely dispatch-driven and produces
the code-level follow-through from the design decisions the 20:30 session
closed.

---

## Main session bug fixes caught inline (don't bounce these back)

Two CI-surface bugs were caught during PR review and repaired in the PR's
own worktree rather than being reopened as new dispatch work. This is the
pattern to keep — Claude inline on 20–30 LOC bug repairs during review,
rather than round-tripping a new Codex dispatch.

1. **#1495 — frozenset iteration order non-deterministic across pytest-xdist workers.**
   Symptom: the new Unicode golden test passed sequentially but failed
   intermittently under `-n auto` (#1482's parallelization). Root cause:
   `path.case_ids` was a frozenset; iteration order in the golden-corpus
   builder differed per worker. Fix: `sorted(path.case_ids)` at the
   iteration site. **Commit: `4622321af1`** on the PR branch.
2. **#1497 — test required populated `sources.db` that CI doesn't ship.**
   Symptom: full red CI on the PR, green locally. Root cause: the
   citation invariant resolves against `data/sources.db`, which is a
   >100MB generated index *not* committed. Fix: module-level
   `pytest.skip(..., allow_module_level=True)` guard that tests for the
   `textbook_sections` table's presence before collecting any tests.
   This preserves strict enforcement on developer checkouts while
   keeping CI green. **Commit: `107840d6fa`** on the PR branch.

**Both fixes are in the merged version on main** — do not re-open them.

---

## In-flight dispatches at handoff (5 total, 4 Claude + 1 Codex)

| # | Agent | Worktree / branch | Issue / purpose |
|---|---|---|---|
| 1 | Codex `danger` | `.worktrees/codex-adr007-pra-kill-tiers` | ADR-007 **PR-A** — remove `section_rewrite` / `full_rewrite` / `writer_swap` tiers (M1/M2/M3 from the ADR inventory) |
| 2 | Codex `danger` | `.worktrees/codex-adr007-prb-kill-rewrite-block` | ADR-007 **PR-B** — remove reviewer `<rewrite-block>` protocol (M4) + parser + applier |
| 3 | Claude `xhigh` | `.worktrees/claude-adr007-prc-kill-word-budget-heal` | ADR-007 **PR-C** — remove `WORD_BUDGET` auto-heal (M5); terminal becomes `plan_revision_request` / `budget_exhausted` |
| 4 | Claude `xhigh` | `.worktrees/claude-1462-post-processor-mutation-invariant` | **#1462 P4-C** — post-processor mutation-class invariant: assert no auto-LLM mutation after `step_write` |
| 5 | Claude `xhigh` | `.worktrees/claude-1455-wiki-review-per-dim-min` | **#1455 P2-B** — wiki review aggregation: switch to per-dim + MIN (not weighted-average) |
| 6 | Claude `xhigh` | `.worktrees/claude-1485-gemini-review-prompt-upgrade` | **#1485** — upgrade `gemini-review.toml` prompt with project-specific discipline (CLAUDE.md, ADRs, non-negotiables) |
| 7 | Claude (this) | `.worktrees/claude-meta-housekeeping-2026-04-23-evening` | **this PR** — session handoff + 3 dispatch briefs |

Cap math at handoff: **4 Claude + 2 Codex** — exceeds the pre-directive
cap (3 Claude + 2 Codex) but user explicitly raised the Claude ceiling
for this wave.

---

## Critical corrections to earlier session framing

### 1. "Colors rebuild unblocked" is STILL wrong

The 20:30 handoff already corrected this. Reaffirming: **do not fire
`v6_build.py a1 10` until every gate in `.worktree-briefs/colors-pilot-post-adr007.md`
is ticked.** Specifically, the ADR-007 PR wave has to land first — any
rewrite-tier or `<rewrite-block>` code still live means the pilot is
testing the *old* pipeline. All `full_rewrite` / `section_rewrite` /
`writer_swap` / `<rewrite-block` grep matches must return zero before
the pilot fires (PR-F invariant in ADR-007 Phase 3).

Additionally: even if all ADR PRs merge, **#1462 (post-processor
mutation invariant) and #1455 (wiki review per-dim MIN) are cofactors.**
Without #1462 a silent post-processor LLM path could undo the ADR at
runtime. Without #1455 a bad wiki review dim score would average out
instead of blocking, letting thin-source articles into the pilot's
chunk assembly.

### 2. The session did NOT revisit colors framing

Earlier sessions had one or two "maybe we can fire colors early"
moments. This session added no new evidence either way. The gate list
is unchanged. Do not let a different framing of the same evidence
resurrect earlier false-starts.

### 3. Claude usage rebalance (new directive, supersedes 6:4)

User's 2026-04-23 PM "6:4 Codex:Claude split" directive is revised.
For the late-evening wave and continuing **through at least Monday
2026-04-27**, Claude is the preferred dispatcher for coding work.
Reason: Anthropic capacity is healthy, and ADR-007 PR-C / #1462 /
#1455 / #1485 all involve judgment-heavy work where Claude Opus 4.7 at
xhigh is the right tool. Do NOT auto-fan-out to Codex for these
classes.

Operationally: if a task could go to either agent and you're unsure,
pick Claude until the user says otherwise. User will signal if
Anthropic usage turns hot.

### 4. User has explicitly stated "merging is your job"

Reaffirmed this session. Corollary: after the ADR-007 PRs land their
CI, main session (or first-morning Claude) reviews each, merges if
clean, and reports. Do not ask. The Gemini-Dispatch `FAIL` signal is
advisory-only, not blocking.

---

## Open decisions for Krisztian (you)

1. **ADR-007 PR-E gate ordering.** PR-E migrates callers of the
   removed tiers to the `plan_revision_request` terminal. Once PR-A/B/C
   merge, PR-E's dependencies are green. Decide: land PR-E on the same
   day as A/B/C, or hold 24h for a stability window?
2. **Colors pilot timing.** Once gates green, the pilot is ~45min wall
   time. Fire same-day as green, or wait for user-awake window?
   (Recommendation: fire same-day; user wants colors green as the
   EPIC #1451 closing signal.)
3. **72 untracked B2 wiki articles.** The working tree still carries
   ~72 uncommitted B2 wiki articles from the overnight wiki-bootstrap
   run. They are valid output. Decide: commit as-is, or run them through
   the #1455 per-dim review after merge first?
4. **Post-ADR-007 cleanup sweep.** After the PR wave merges, `scripts/build/v6_build.py`
   will shrink by ~600 LOC. A follow-up cleanup pass (unused imports,
   dead helpers, orphan tests) is warranted. Claude `xhigh` or Codex
   `danger`?

---

## Roadmap snapshot at handoff

### EPIC #1451

| Phase | Status |
|---|---|
| Phase 0 — merge queue | ✅ |
| Phase 1 — runtime alignment (P1-A #1452 + P1-B #1453) | ✅ (closed 20:30 session) |
| **Phase 2-A #1454 threshold unify** | ✅ **CLOSED THIS SESSION (#1498)** |
| Phase 2-B #1455 wiki review per-dim MIN (Claude) | 🚀 in flight |
| Phase 2-C #1456 ADR sign-off | ✅ (signed Y/Y/Y via #1484) |
| Phase 2-C ADR-007 PR wave (A/B/C/D/F + PR-E) | 🚀 PR-A/B/C in flight; PR-D/E/F queued |
| Phase 3 — pipeline + plan fixes | ✅ |
| **Phase 4-A #1460 citation invariant** | ✅ **CLOSED THIS SESSION (#1497)** |
| **Phase 4-B #1461 Unicode round-trip** | ✅ **CLOSED THIS SESSION (#1495)** |
| **Phase 4-C #1462 post-processor mutation** | 🚀 in flight |
| Phase 4-D #1463 plan immutability hook (Codex) | ⏳ not started |
| Phase 4-E #1464 rules deployment invariant (Codex) | ⏳ not started |
| Phase 5 — colors pilot | 🔒 BLOCKED on Phase 2-C PR wave + #1462 + #1455 |

### Session-scope follow-ups (non-EPIC, opened by Codex during the wave)

| Issue | Source | What |
|---|---|---|
| #1487 | #1461 followup | Unicode helpers decompose й/ї in specific normalization paths |
| #1488 | #1460 followup | Citation drift: `wiki/pedagogy/a1/food-and-drink.md` (`S12` → `ext-article-1`) |
| #1489 | #1460 followup | Citation drift: `wiki/pedagogy/a1/hey-friend.md` (4 orphans) |
| #1490 | #1460 followup | Citation drift: `wiki/pedagogy/a1/my-family.md` (3 orphans) |
| #1491 | #1460 followup | Citation drift: `wiki/pedagogy/a1/reading-ukrainian.md` (`S12` → `ext-article-1`) |
| #1492 | #1460 followup | Citation drift: `wiki/pedagogy/a1/stress-and-melody.md` (4 orphans) |
| #1493 | #1460 followup | Citation drift: `wiki/pedagogy/a1/things-have-gender.md` (malformed registry) |
| #1494 | #1460 followup | Citation drift: `wiki/pedagogy/a1/who-am-i.md` (2 dictionary orphans) |

Brief for the #1488–#1494 batch-fix is at
`.worktree-briefs/claude-citation-drift-batch-1488-1494.md` (this PR).

---

## Next session — recommended order

### PRE-PICK: reconcile the PR wave
1. `gh pr list --state merged --search 'merged:>2026-04-24T00:00'` — see
   which of ADR-007 PR-A/B/C, #1462, #1455, #1485 actually landed.
2. `git worktree list` — prune any worktrees whose PRs merged.
3. Read each merged PR body + Gemini-Dispatch comment. Do not skip.

### PICK 1 — Whatever ADR-007 PR-A/B/C/D/F is still open → review + merge
- **Why first**: every one of them is on the critical path to colors.
- **Review checklist**: PR removes LOC cleanly (no stubs), tests green,
  grep for old tier name returns zero.

### PICK 2 — Colors pilot (if all gates green) → single v6_build.py run
- **Pre-flight**: use `.worktree-briefs/colors-pilot-post-adr007.md`
  as the runbook. Every gate check is copy-pasteable.
- **Command**: `.venv/bin/python scripts/build/v6_build.py a1 10 \
  --writer claude-tools --reviewer codex-tools --force`
- **Monitor** per MEMORY #0B.

### PICK 3 — Citation drift batch (#1488–#1494) → Claude xhigh dispatch
- **Brief**: `.worktree-briefs/claude-citation-drift-batch-1488-1494.md`
- **Why**: clears KNOWN_DRIFT dict, flips the new citation invariant
  from xfail to strict. Also demonstrates the invariant's value.
- **Gate**: no explicit gate — can fire any time post-handoff.

### PICK 4 — #1344 canary article replacement → Claude xhigh dispatch
- **Brief**: `.worktree-briefs/claude-1344-replace-phase-a-canary-articles.md`
- **Gate**: MUST wait on #1455 (per-dim MIN wiki review) to merge,
  otherwise the replacement articles use the old weighted-average path.
- **Why not first**: lower critical-path priority than colors; also a
  content rebuild, will take longer than the batch-fix.

### DO NOT PICK (yet)
- **#1463 P4-D plan immutability hook** — lower priority; wait for colors green.
- **#1464 P4-E rules deployment invariant** — lower priority.
- **B2 wiki article commit** — pending user decision (Open decision 3).

### With revised parallelism cap (3+ Claude + 2 Codex through Monday)
- Claude: colors pilot (1 slot) + citation batch (1 slot) + #1344 (1 slot)
- Codex: ADR-007 PR-D + PR-F (if not yet in flight) — otherwise free
- Gemini: available for B2 wiki work if user greenlights

---

## Context budget + session metrics

- **Main-session context at handoff:** ~300K / 750K. Comfortable.
  Handoff zone is 400K; did not hit early-signal zone. Calibration
  lesson held (my self-estimates overshoot ~1.8× — ran the tail-200
  jq check before writing this section).
- **5 PRs merged**, **2 inline bug fixes caught during review**,
  **8 follow-up issues filed** (#1487 + #1488–#1494 citation drifts),
  **6 concurrent dispatches at handoff** (1 over revised Claude cap,
  user-approved).
- **Hygiene:** working tree 96→20 items, 32 stale remote branches
  pruned, 22 stale local branches pruned. No lost work; all pruned
  branches either merged or were stale dispatch residue.
- **Wall time:** ~2.5h session. CI now 4m30s (#1482 still holding
  post-merge). Context conservation via dispatch offload worked —
  main session did zero heavy inline work this session.

---

## MEMORY policy unchanged this session

No new entries. Existing #0 (role), #0A (pushback), #0B (Monitor),
#0C (cold-start), #0D (L1 corpus framing), #0E (grades≠CEFR), #0F
(reviewer-dim → pipeline code), #0G (branch verification), #0H
(merging is your job), REVIEWER POLICY, PR CI MONITOR, CODEX
BRANCH-BASE, DISPATCH-BRIEF CHECKLIST, GPT-5.5, PROMPT-ABLATION,
BATCH COMMANDS blocks remain current.

Operationally-relevant reminders for next session's Claude:
- **#0H** — after ADR-007 PR CI goes green, you merge. Do not ask.
- **#0B** — colors pilot uses the Monitor tool, not ScheduleWakeup polling.
- **Dispatch-brief checklist** — PR creation is step 7, not a footer.

---

## Commands for cold-start

```bash
# State snapshot (single curl each)
curl -s http://localhost:8765/api/state/manifest
curl -s http://localhost:8765/api/orient

# What merged overnight
gh pr list --state merged --search 'merged:>2026-04-24T00:00' --limit 20

# Worktree reconciliation
git worktree list
gh issue list --state open --label 'agent:claude,agent:codex' --limit 20

# Dispatch briefs ready to fire
ls -lt .worktree-briefs/*.md | head -10

# Latest handoff chain (read the newest 2–3)
ls -lt docs/session-state/*.md | head -5

# Colors pilot gate check (once ADR-007 wave merges)
.venv/bin/python scripts/check_decisions.py
grep -RE 'section_rewrite|full_rewrite|writer_swap|<rewrite-block' scripts/build/
# Above grep MUST return zero lines before colors pilot fires.

# Then read THIS file end-to-end.
```

---

*Generated 2026-04-23 23:30 UTC, main session ~300K / 750K, from the*
*meta-housekeeping worktree. 5 merged + 6 in-flight + ADR-007 approved.*
*Colors pilot still 6 merges away.*
