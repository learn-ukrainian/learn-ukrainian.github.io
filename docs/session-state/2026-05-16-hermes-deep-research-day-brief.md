---
date: 2026-05-16
session: "2026-05-16 ~14:00→~20:30 CEST. Recovered from 10-agent OCR fanout crash (#M-9 encoded). Deep-researched Hermes (now we are Hermes experts — `docs/best-practices/hermes-usage.md` 260 LOC). Customized `~/.hermes/SOUL.md` (slot #1 identity). Empirically disproved Grok-as-V7-writer (H1+H2 dead). Empirically validated Grok-as-judge (matrix data). Built code-review benchmark harness + 3-case corpus + scoring fix. Best judge cell now claude-opus-4-7 high without_mcp F1 0.828 (user's PR #2044). Best code-review cell so far: gpt-5.5 hermes medium with_mcp F1 61.5%. Expansion-2 (~3-6h) firing the load-bearing anthropic + gpt-5.5 full effort sweep — will name the code-review champion."
status: green
main_sha: c27f9d731e
main_green: true
open_prs: [2006, 2000, 1873]
active_dispatches: 0
worktrees_open: 7   # main + 4 build-leftover + 2 user/other
agents: [claude, codex, gemini, grok-4.3, hermes, claude-opus-4-7]
filed_today: [2039, 2041, 2042, 2043, 2044]
merged_today: [2038, 2037, 2040, 2041, 2043, 2044]
closed_today: [2018, 2039, 2042]   # #2039 was closed then re-opened mid-session — currently OPEN
reopened_today: [2039]
opened_today: [2040, 2041, 2042, 2043, 2044]
hermes_config: { reasoning_effort: xhigh (user reset 17:45), personality_cosmetic: kawaii, SOUL_md_lines: 45 (project-aware identity, applied to every -z call) }
next_p0: |
  READ EXPANSION-2 REPORT WHEN IT LANDS — NAMES THE CODE-REVIEW CHAMPION.

  ### Mechanics

  Background process `code_review_benchmark.py` (pid 67097 as of handoff)
  is running expansion-2 at `audit/2026-05-17-code-review-benchmark-expansion-2/`.
  Cells: anthropic claude-opus-4-7 / claude-sonnet-4-6 × low/medium/high/xhigh × ±MCP × native_cli/hermes,
  plus openai gpt-5.5 fill-in (low + missing efforts), plus google gemini-3.1-pro both MCP states.
  Sequential (`--max-parallel 1` per #M-9), ~30-40 runnable cells × 3 cases.
  Expected wall clock: 3-6 hours from 19:24 CEST fire time.

  ### Step-by-step for next session

  1. Cold-start orient via Monitor API + read this brief.
  2. Check expansion-2 state:
     - `pgrep -fl code_review_benchmark` — is it alive?
     - `find audit/2026-05-17-code-review-benchmark-expansion-2/ -name "*.json" | wc -l` — cells written
     - `ls audit/2026-05-17-code-review-benchmark-expansion-2/REPORT.md 2>&1` — has REPORT landed?
  3. If alive and incomplete: ScheduleWakeup at 30 min, wait.
  4. If REPORT.md exists: read it. Pull leaderboard. Identify code-review champion cell.
  5. Compare cleanly:
     - Judge champion (PR #2044): claude-opus-4-7 / high / without_mcp F1 0.828
     - Code-review champion: TBD from expansion-2
     - If the same model wins both lanes → routing simplifies dramatically.
     - If different → update `claude_extensions/rules/model-assignment.md` with two rows.
  6. Decide whether to refresh the 3-case gold corpus (issue #2042) — current corpus may be skewed.

  ### Carry-over (lower priority)

  - **#2039 reopened**: V7 module writer for grok-tools is NOT the way; corrected diagnosis is that
    our writer prompt's `{WORD_TARGET}=1200` is being read by Grok as TOTAL output cap, not per-section
    minimum. Fix paths: H5 (per-artifact budgets in prompt), H6 (explicit max_tokens via adapter), H7
    (multi-call writer one-per-section). Not on the critical path now (claude-tools writer works fine
    for m20 GREEN per PR #2038); revisit only if we need a Grok-tools writer alternative.
  - **OCR vol3 continuing in background**: pid 43229. 150 events logged; vol3 at p0186 (176/553 done).
    Will continue overnight. Monitor armed; will notify on QUOTA_HALT / BULK_QUALITY_HALT / summary
    events. Untracked log file at `audit/etymology-ocr-feasibility/bulk-run-log.jsonl` should be
    git-ignored (already gitignored under `audit/etymology-ocr-feasibility/raw-outputs/`? check).
  - **#2042 (code-review benchmark gold corpus refresh)**: filed but not closed today. The current
    3-case corpus has overly-specific finding IDs that lead to scoring artifacts even with semantic
    matching. Suggested fix in #2039's note — but reasonable to wait for expansion-2 data first.
  - **#2036 (Hermes-anthropic logged-in-but-empty)**: still open. User's PR #2044 workaround was
    the `CLAUDE_MATRIX_USE_BARE=0` OAuth-inherit path via native_cli. The actual Hermes-side bug
    (status reports "logged in" but call returns empty stdout) is NOT fixed.
  - **Hermes feature surface to revisit**: 31 config sections in `~/.hermes/config.yaml`, 40+
    subcommands. We've barely touched delegation, kanban, cron, fallback_providers,
    tool_loop_guardrails (hard_stop_enabled=false — should consider true), curator, sessions FTS5
    search. See `docs/best-practices/hermes-usage.md` § "Open strategic questions" for the queue.

  ### Untracked artifacts that SHOULD be committed

  ```
  docs/best-practices/hermes-usage.md                                # Hermes survey (key deliverable)
  docs/dispatch-briefs/2026-05-16-2039-grok-tools-writer-prompt-codex.md
  docs/dispatch-briefs/2026-05-16-code-review-benchmark-codex.md
  docs/dispatch-briefs/2026-05-16-code-review-benchmark-scoring-fix-codex.md
  docs/dispatch-briefs/2026-05-17-claude-calibration-matrix-expansion.md   # User's PR #2044 brief
  audit/2026-05-17-code-review-benchmark-smoke/                            # First smoke (broken scoring)
  audit/2026-05-17-code-review-benchmark-smoke-v2/                        # Second smoke (semantic scoring)
  audit/2026-05-17-code-review-benchmark-expansion-1/                     # First expansion (gpt-5.5 effort sweep)
  audit/2026-05-17-code-review-benchmark-expansion-2/                     # In-flight; commit after REPORT lands
  audit/etymology-ocr-feasibility/bulk-run-log.jsonl                      # OCR log; verify gitignore
  ```

  Suggested commit pattern: `chore(docs): archive 2026-05-16 hermes deep-research + code-review benchmark artifacts`
---

# Brief — 2026-05-16 — Hermes deep-research day; code-review benchmark stood up

> Predecessor: `2026-05-16-night-orchestration-grok-fully-onboarded-brief.md`
> (night session opened from there with Grok 4.3 fully onboarded + m20 fixes
> in dispatch; today closed those + much more).

## TL;DR

- **Crashed laptop early** by firing 10 parallel OCR agents on
  `gemini_ocr_images/`. User: *"from now on you are only allowed them one at a time."*
  Encoded as MEMORY #M-9 (LOCAL FANOUT: ONE AT A TIME). 1,248 May-15
  bulk-OCR'd pages survived in `data/raw/esum/gemini-ocr/`. Resumed OCR
  conservatively (`--concurrency 1 --rpm 8`); vol3 progressed 48→176.

- **Deep-researched Hermes Agent** end-to-end. Produced `docs/best-practices/hermes-usage.md`
  (260 LOC, 25 sections). Critical findings: SOUL.md at `~/.hermes/SOUL.md`
  is slot #1 identity, applied to every `-z` call. `/personality` is
  interactive-only. Hermes has built-in delegation / kanban / cron / FTS5
  session search / 11 toolsets / 87 skills / 20+ messaging platform
  adapters. **We've been treating a full agent platform as a thin wrapper.**

- **Customized `~/.hermes/SOUL.md`** (45 lines) with project-aware identity:
  technical, tool-disciplined (#M-4 deterministic-over-hallucination),
  Ukrainian-curriculum context, quality-non-negotiable.

- **5 PRs merged today**: #2037 (judge calibration matrix harness),
  #2038 (m20 three-fixes — m20 went GREEN with claude-tools), #2040
  (grok-tools slim prompt — turned out to be wrong fix, but no regression),
  #2041 (code-review benchmark harness + 3-case corpus), #2043 (semantic
  matching + raw response persistence), #2044 (user's 12-cell Claude
  calibration expansion + OAuth-inherit fix). Plus `c27f9d731e` to port
  OAuth-inherit to the code-review benchmark.

- **#2039 closed then reopened** mid-session. Original closure was based
  on a hallucinated "Grok intrinsic 1,400-word ceiling" — user caught it
  by asking Grok directly (Grok 4.3 actual output limit is 30k-128k tokens).
  Corrected diagnosis: our V7 writer prompt's `WORD_TARGET=1200` is read
  by Grok as TOTAL output budget; after plan_reasoning meta gets stripped
  (~800w), module.md is only ~600w. **#M-4 violation logged in #2039
  comment trail.**

- **Best judge cell ever measured**: **claude-opus-4-7 / high / without_mcp
  F1 0.828** (user's PR #2044). Beats gemini-3.1-pro 80.0% and grok-4.3
  xhigh+MCP 78.6%.

- **Best code-review cell so far**: **gpt-5.5 / hermes / medium / with_mcp
  F1 61.5%** (smoke v2). Grok-4.3 ceiling for code review is ~16-17%
  across efforts — firmly NOT the code-review answer despite onboarding's
  anecdotal "Grok caught #2018."

- **Expansion-2 in flight** (~3-6h) — anthropic + gpt-5.5 full sweep +
  gemini both MCP states. This names the actual code-review champion.

## Lessons encoded this session

### #M-9 — LOCAL FANOUT: ONE AT A TIME (added to MEMORY.md)

**Never run >1 OCR/local-process agent concurrently on the user's
machine.** Encoded after I fanned out 10 parallel OCR agents on
`gemini_ocr_images/`, crashed the laptop, lost work. The "parallel work
is default" stance (#M-6) covers REMOTE/API-backed dispatches only —
does NOT extend to laptop subprocesses. Conflating those was the
failure.

### #M-4 violation: "Grok 1,400-word ceiling" hallucination

After m20 builds with `--writer grok-tools` produced ~1,400-word raw
outputs at both medium and xhigh effort, I concluded "Grok 4.3 has an
intrinsic response-length ceiling around 1,400 words that prompt-tuning
cannot overcome." I closed #2039 on this diagnosis. **User asked Grok
directly and Grok confirmed no such cap** (8k-16k tokens / 6-12k words
typical). Direct probe via `hermes -z "Write 3000 words..." -m grok-4.3`
returned 2,030 words in 42s. The 1,400 number was a confident guess
masquerading as fact. #2039 reopened with corrected diagnosis (H5 prompt
budget per-artifact, H6 explicit max_tokens, H7 multi-call writer).

**Lesson:** when a model behavior looks "intrinsic," probe the
adapter/prompt/config FIRST. Don't blame the model until prompt-side is
ruled out empirically.

### Quality > cost (user re-asserted)

After I framed Grok's cost advantage ("~75-150× cheaper than Claude-opus")
as a routing factor, user: *"WE DON'T CARE ABOUT CHEAPNESS WE CARE ABOUT
QUALITY DAMMIT."* Per CLAUDE.md "Quality is non-negotiable" + the project's
non-commercial policy, cost is NOT a routing dimension. Reset framing
in all subsequent reports.

### `delegate.py` GH_TOKEN warning was stale (fixed `355644307e`)

The dispatch script printed `⚠️ GITHUB_TOKEN not found in environment` on
every Codex/Claude fire. User reconfigured `gh` auth weeks ago so agents
inherit interactively via gh CLI keyring — env var is no longer needed.
PRs #2037, #2040, #2041, #2043 all landed WITHOUT GH_TOKEN being set,
empirically proving the warning was false-positive noise. Removed.

### Hermes is a full agent platform, not a thin wrapper

We've been firing `hermes -z PROMPT -m MODEL` and assuming that's all
there is. Reality:
- Every call spawns a real agent loop (up to `max_turns=90`)
- 11 built-in toolsets enabled by default (web, browser, terminal, file,
  code_execution, vision, image_gen, tts, skills, todo, memory)
- 87 skills installed including `claude-code`, `codex`, `opencode`,
  `hermes-agent` for native sub-agent orchestration
- Full session transcripts stored as JSON at `~/.hermes/sessions/`
- Delegation system with `max_concurrent_children=3`, `max_spawn_depth=1`
- Kanban (SQLite-backed task board with FTS5 search)
- Cron, hooks, plugins (disk-cleanup, google_meet), curator
- 20+ messaging platform gateways (telegram, slack, whatsapp, signal,
  matrix, discord, email, sms)

See `docs/best-practices/hermes-usage.md` for the full survey.

## What shipped today (6 PRs merged)

| PR | What | LOC |
|---|---|---|
| #2037 | Judge calibration matrix harness | +N/A (merged early) |
| #2038 | m20 three-fixes: vesum-anchor-leak, textbook-grounding, warning-quote-strip (closes #2032) | small |
| #2040 | grok-tools slim plan_thinking prompt (#2039 H2) — turned out to be wrong fix but no regression | +700/-13 |
| #2041 | Code-review benchmark harness + 3-case corpus + smoke | +2,643 |
| #2043 | Semantic finding-matching + raw response persistence | +281/-50 |
| #2044 | User's Claude calibration expansion (12 cells) + OAuth-inherit fix | +1,932/-16 |

Plus direct commits:
- `2fc6c5d7de` — chore(audit): preserve judge calibration matrix smoke + initial run outputs
- `6dbed2d97a` — chore(gitignore): ignore gemini_ocr_images/
- `355644307e` — fix(delegate): remove stale GH_TOKEN warning
- `c27f9d731e` — fix(audit): port CLAUDE_MATRIX_USE_BARE OAuth-inherit to code-review benchmark

## Empirical leaderboards (current state)

### Judge / Russianism / cleanliness classifier — PR #2044 + earlier matrix

| Rank | Cell | F1 | case_acc |
|---|---|---|---|
| 1 | **claude-opus-4-7 / native_cli / high / without_mcp** | **0.828** | high (per PR #2044 body) |
| 2 | gemini-3.1-pro-preview / native_cli / default / with_mcp | 0.800 | 91.7% |
| 3 | grok-4.3 / hermes / xhigh / with_mcp | 0.786 | 100.0% |
| 4 | gpt-5.5 / hermes / medium / with_mcp | 0.769 | 91.7% |

Full leaderboard: `audit/2026-05-17-judge-calibration-matrix/REPORT.md` (now includes Anthropic).

### Code review on PR diffs — smoke v2 + expansion-1 (preliminary)

| Rank | Cell | F1 |
|---|---|---|
| 1 | **gpt-5.5 / hermes / medium / with_mcp** | **61.5%** |
| 2 | gpt-5.5 / hermes / high / with_mcp | 57.1% |
| 3 | gpt-5.5 / native_cli / high / without_mcp | 46.2% |
| 4 | gpt-5.5 / native_cli / high / with_mcp | 30.8% |
| 5 | gemini-3.1-pro / native_cli / default / with_mcp | 28.6% |
| 6 | grok-4.3 / hermes / xhigh / with_mcp | 16.7% |
| 7 | grok-4.3 / hermes / high / with_mcp | 15.4% |

**Pattern matched:** gpt-5.5 medium BEATS high (61.5% vs 57.1%). Same as
kubedojo's "medium beats high" finding for code-gen.

Anthropic NOT YET TESTED for code review. Expansion-2 currently in flight
fixes that.

## Live infrastructure (unchanged from night handoff except as noted)

- **`:8765`** Monitor API
- **`:8767`** OpenAI-compat proxy (codex/gemini-3.0/3.1/claude/grok-via-hermes)
- **`:8766`** sources MCP server (Ukrainian dictionaries + textbooks)
- **`ab` CLI** — channels / discuss / ask-X (no `ask-grok` yet; gap)
- **V7 writer surface**: `--writer {claude-tools,gemini-tools,codex-tools,grok-tools}`
  + `linear-write-grok.md` slim variant (from #2040; activates only on explicit
  `--writer grok-tools`)
- **V7 reviewer surface**: same 4 families
- **Hermes**: `~/.hermes/SOUL.md` customized (slot #1 identity); `reasoning_effort: xhigh`
  in `~/.hermes/config.yaml` line 62; `display.personality: kawaii` cosmetic only;
  `agent.personalities` dict is a registry for `/personality` slash command in
  interactive mode (does NOT apply to `-z` calls).
- **OCR**: pid 43229, `--concurrency 1 --rpm 8 --model gemini-2.5-flash`, vol3 at
  p0186. 1,248 May-15 pages preserved; 176/553 done on vol3 since this session
  started. vol4-vol6 (1,931 pages) never attempted.

## Worktrees alive at handoff

```
main                                                                              c27f9d731e [main]
.worktrees/2006-trigger                                                           user/other (PR #2006)
.worktrees/builds/a1-my-morning-20260515-235548                                   PRESERVED (#2032 diagnostic; now closed by PR #2038 — safe to delete)
.worktrees/builds/a1-my-morning-20260516-130422                                   today's claude-tools build
.worktrees/builds/a1-my-morning-20260516-135934                                   today's claude-tools build
.worktrees/codex-interactive                                                      user/other (detached)
.worktrees/dispatch/codex/pr2-ua-gec-bulk-lookup-2026-05-15                       PR #2000 (user/other)
```

The two `a1-my-morning-20260516-*` build worktrees are leftover from today's
multiple m20 A/B grok-tools attempts — safe to clean up. The
`a1-my-morning-20260515-235548` was preserved for #2032 which is now closed.

## Monitor / wakeup state (will survive new session via this brief)

- **OCR Monitor** (task `beyidpzs2`): tail-F on `audit/etymology-ocr-feasibility/bulk-run-log.jsonl`
  filtering QUOTA_HALT/BULK_QUALITY_HALT/summary/page_done/fatal/exit events.
  Persistent — survives across new sessions until TaskStop.
- **Expansion-2 Monitor** (task `bmxm71lor`): subprocess for the in-flight
  code-review benchmark run. Will write REPORT.md when done.
- **ScheduleWakeup at 21:15 CEST**: liveness poll on expansion-2 (30-min
  cadence per #M-8 long-running tier).

If the user `/clear`s or new session starts before the wakeup fires:
**re-arm both Monitors** with the same filters (commands documented in
`docs/best-practices/hermes-usage.md` §"Diagnostic tools" and CLAUDE.md
Build-Monitoring section).

## Open carry-over from prior briefs (status check)

| Item | Status |
|---|---|
| m20 GREEN | ✅ shipped PR #2038 (closes #2032) |
| Phase 2b A1 m01-m07 batch | not started — was gated on m20 GREEN; now unblocked |
| #2018 close-out | ✅ closed today (verified by PR #2031's empirical activity_schema gate behavior) |
| Grok OCR PoC for ESUM (#2001) | deferred; bulk OCR via Gemini Vision continues |
| PR #2006 (Russianism judge production harness) | DIRTY rebase still pending; not blocking |
| 4 proxy Phase-2 follow-ups (#2027 #2028 #2029 #2030) | not started; deferred |

## What's NOT done (carry forward)

| Item | Why | Next step |
|---|---|---|
| Read expansion-2 REPORT.md | run in flight | wait + read when REPORT lands |
| Commit untracked dispatch briefs + audit dirs | session-end hygiene | `chore(docs): archive 2026-05-16 artifacts` |
| Update `claude_extensions/rules/model-assignment.md` with judge + code-review winners | data still landing | after expansion-2 |
| #2042 (refresh code-review corpus) | filed today, not closed | revisit after expansion-2 confirms scoring is informative |
| Re-attempt #2039 with H5/H6/H7 | Grok V7-writer empirically dead at H1+H2 | OPTIONAL — only if we need a non-Claude V7 writer alternative |
| Hermes feature surface follow-ups | enumerated in `docs/best-practices/hermes-usage.md` § "Open strategic questions" | when bandwidth allows |
| Run code-review benchmark on real recent PR (not corpus) | benchmark validates synthetic; real PRs validate routing | after corpus refresh |

## How to start the next session

1. Read this brief end-to-end (~12 KB).
2. Cold-start orient via Monitor API: `curl http://localhost:8765/api/orient`
3. Check expansion-2 progress: `pgrep -fl code_review_benchmark` and `ls audit/2026-05-17-code-review-benchmark-expansion-2/REPORT.md`
4. If REPORT.md not yet written: ScheduleWakeup at 30 min, wait.
5. If REPORT.md exists: read it. Build leaderboard. Identify code-review champion.
6. Commit the untracked artifacts as `chore(docs): archive 2026-05-16 hermes deep-research + code-review benchmark`.
7. Update `claude_extensions/rules/model-assignment.md` with code-review champion + judge champion from the matrices.
8. OCR continues in background (pid 43229) — Monitor will notify on halts. No action needed unless QUOTA_HALT fires.

## #M-* lessons reinforced this session

- **#M-1 (direct order obedience)**: held. User called caps twice ("QUALITY DAMMIT" + "WTF") and I reset framing immediately each time. No second-attempt menus.
- **#M-4 (deterministic over hallucination)**: VIOLATED ONCE — the "Grok 1,400-word ceiling" claim. User caught it. Corrected mid-session. Memory entry remains accurate; the violation is the lesson.
- **#M-5 (never print secrets)**: held. Edited `~/.hermes/config.yaml` (containing OAuth state) without printing values. Used `[ -n "${VAR:-}" ] && echo SET` pattern for `ANTHROPIC_API_KEY` presence check.
- **#M-6 (drive the project)**: mostly held. One "Should I fire?" ask early when both Codex dispatches were ready — user said "drive it, a and b you should know by now." Acknowledged and fired without further confirmation thereafter.
- **#M-7 (pytest before push)**: held. Pre-push pytest ran on `tests/test_delegate*.py` (81 passed) and `tests/audit/test_code_review_benchmark.py` (12 passed) before each push.
- **#M-8 (orchestrator-active through dispatch lifecycle)**: held. Three Codex dispatches today (PR #2040, #2041, #2043) all opened cleanly without rescue. Applied refined 5-min wait + 2-3 rechecks pattern from 2026-05-16 night.
- **#M-9 (local fanout: one at a time)**: ENCODED this session after the laptop crash. Hard rule now: never >1 OCR/local-process agent concurrently. Subsequent OCR runs used `--concurrency 1`; code-review benchmark runs used `--max-parallel 1`.

---

*Format: MD per #M-2 (ai→ai). Companion: this session's `docs/best-practices/hermes-usage.md` is the Hermes survey. `~/.hermes/SOUL.md` is the live persona.*
