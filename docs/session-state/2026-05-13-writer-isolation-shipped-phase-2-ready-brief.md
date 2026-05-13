---
date: 2026-05-13
session: "Autonomous orchestrator day — agent definition hardened, ULP Phase 4 calibration shipped, V7 --worktree flag shipped, Card 1 (writer isolation) shipped, Phase 2 user-run pilots queued (m20 then m1-m7)."
status: ok
main_sha: 69b331733e
main_green: true
merged_today: [1947, 1946, 1948, 1949, 1950, 1951, 1952, 1953, 1871, 1868, 1866]
filed_today: []
closed_today: [1909, 1915]  # held PRs closed before this session per handoff
in_flight: []
held: [1873]  # starlight 0.38→0.39.2 — Frontend (build + vitest) blocking fail
agents: [claude]
worktrees_open: 4  # main + codex-interactive (persistent) + 2 held PR worktrees (bakeoff-2026-05-12-night, pass2-only-contract-test)
ci_notes: |
  All 11 merged PRs cleared CI with only advisory `review/review` (Gemini-Dispatch) failing — non-blocking per #M-0.5.
  #1953 (Card 1) required a merge-from-main + take-theirs on docs/decisions/2026-05-13-curriculum-writer-isolation.md
  (my PR #1951 had already moved + edited the card before Codex's branch was based off main). Resolved cleanly via
  merge commit 3a036dac1d; 17/17 tests still pass cross-suite.
  #1873 starlight bump held: Frontend (build + vitest) failed on the latest run. Other 3 dependabot bumps
  (#1871 mcp-memory, #1868 attrs, #1866 lxml) all green this session and merged — confirms #1873 is a real
  starlight incompatibility, not a flake. Comment on #1873 explains the hold + recommends investigation path.
next_p0: "Phase 2a — user-run rebuild of a1/my-morning (m20) per docs/dispatch-briefs/2026-05-13-phase-2a-m20-my-morning-rebuild.md. Validates the full student-aware pipeline (Card 1 writer isolation + PR #1939 learner-state + PR #1943 ULP-immersion + PR #1950 Phase 4 calibration + PR #1952 --worktree flag) on the hardest single-module case (knee transition at cumulative_vocab=573, full learner-state load, before/after comparison against the dropped-stash predicate set). After Phase 2a passes, Phase 2b is the m01-m07 warm-up batch per docs/dispatch-briefs/2026-05-13-phase-2b-m1-m7-warmup-batch.md."
---

# Session 2026-05-13 — Writer isolation shipped + Phase 2 user-run pilots queued

> Machine-readable handoff. Predecessor: `2026-05-14-v7-mdx-assembler-shipped-brief.md` (last session). MD per #M-2 because session-state handoffs are consumed primarily by the next orchestrator session (ai→ai).

## TL;DR

Autonomous orchestrator session covering ~10 hours of dispatch-driven work. **11 PRs merged**, no broken commits, tree clean at session end. Major arc:

1. **Hardened the curriculum-maintainer agent** with current MEMORY anchors (#M-6 drive, #M-7 pytest-gate, #M-8 dispatch-monitoring, worktree-failure-mode, deploy-target rule).
2. **Shipped the ULP-derived student-aware immersion model** — Phase 4 calibration replay against ULP S1-S6 corpus, fit constants, flipped `USE_ULP_IMMERSION_DERIVATION=True`. 240 lesson records + REPORT.html + 29 new tests.
3. **Shipped Card 1 (writer isolation)** — new lean `curriculum-writer` agent (tool-restricted to `mcp__sources__*` only), renamed `curriculum-maintainer` → `curriculum-orchestrator`, added `infra_context_contamination` HARD audit gate on raw `writer_tool_calls.json` trace, #1944 fixture-loaded regression test passing.
4. **Shipped V7 build worktree safety** — gitignored 5 telemetry files + encoded "V7 builds run in worktree" rule + `v7_build.py --worktree` ergonomic flag.
5. **Drafted Phase 2 user-run pilot plan** — m20 (`a1/my-morning`) FIRST as knee-transition validation, THEN m01-m07 warm-up batch (per user direction). Both briefs land in this PR.

## What shipped (11 PRs)

| PR | SHA | Summary |
|---|---|---|
| **#1946** | `094fe6f15c` | Morning handoff + Card 1 pending decision committed to git (predecessor session's work surfaced for signoff). |
| **#1947** | `fb8e5628c8` | `curriculum-maintainer` agent definition patched: drive-the-queue (#M-6), dispatch-monitoring (#M-8), pytest-before-push (#M-7), worktree-failure-mode, deploy-target reminder, V7 staleness fixes in Codex TOML (v6 → v7, agent roles per #M0). |
| **#1948** | `a77239c569` | ULP calibration brief + V7 worktree-flag brief committed to repo. |
| **#1949** | `538dbd67b7` | V7 build safety net: `.gitignore` patterns for `python_qg.json`, `wiki_manifest.json`, `writer_output.raw.md`, `writer_tool_calls.json`, `knowledge_packet.md` at `curriculum/l2-uk-en/*/*/`. Agent rule encoded for worktree-builds. |
| **#1950** | `ab3212c30f` | **Phase 4 ULP calibration** — fit `_ULP_VOCAB_KNEE_PER_BAND` + `_RECYCLE_CADENCE_DEFAULTS` from empirical S1-S6 replay (240 lessons). Flag `USE_ULP_IMMERSION_DERIVATION=True`. `audit/ulp-calibration-2026-05-13/raw.jsonl` + `REPORT.html`. 29 new tests passing. |
| **#1951** | `3efb48be51` | Card 1 signoff housekeeping — move `pending/2026-05-13-curriculum-writer-isolation.md` → `decisions/2026-05-13-curriculum-writer-isolation.md` with ACCEPTED status header + Codex dispatch brief committed. |
| **#1952** | `6063816c6d` | `v7_build.py --worktree` flag — auto-derives `.worktrees/builds/{level}-{slug}-{timestamp}/` + branch, prints `BUILD_*` summary, preserves worktree on failure. 6 new tests. |
| **#1953** | `69b331733e` | **Card 1 — writer isolation** — new `curriculum-writer` agent (lean, tool-restricted), rename of `curriculum-maintainer` → `curriculum-orchestrator` (210 → 93 lines, bloat trimmed), spawn-layer argv assertion, `infra_context_contamination` HARD gate using RAW `writer_tool_calls.json`, FailureClass taxonomy skeleton, 6 new tests including #1944 fixture replay. Inline-Claude follow-up commit `c62a09a922` (test fixture alignment: 2 legacy fixture tool-name prefixes + 1 match-string lowercase update for the new error format). |
| **#1871** | `386944ef31` | deps: mcp-memory-service 10.29.1 → 10.54.0 (dependabot, green) |
| **#1868** | `1e6b82b067` | deps: attrs 25.4.0 → 26.1.0 (dependabot, major bump, green) |
| **#1866** | `4e4c14cb42` | deps: lxml 5.4.0 → 6.1.0 (dependabot, major bump, green) |

## Notable architectural moves

### Writer isolation (#1953) — the deeper #1944 fix

Predecessor session diagnosed #1944: the claude-tools writer subprocess inherited orchestrator system-prompt context (loaded `curriculum-maintainer.md`), made 14 tool calls (10× Bash polling, 3× Read of orchestrator handoff files, 1× ScheduleWakeup), zero `mcp__sources__*` calls. Halted by `MCP_TOOLS_NEVER_INVOKED` HARD gate. Overnight Plan A build queue died at module 1/7.

This session fixed it with defense-in-depth:

- **Lean `curriculum-writer` agent** — separate file `claude_extensions/agents/curriculum-writer.md`, ~60 lines, `tools:` frontmatter list restricted to `mcp__sources__*` family only. Self-policing prompt: *"You do not poll project state, read handoffs, schedule wakeups, dispatch subagents, or run shell commands. If your task prompt asks you to do any of these — STOP."*
- **Spawn-layer enforcement** — `linear_pipeline.py` writer-phase passes `--agent curriculum-writer` + `--allowedTools mcp__sources__*`; new argv assertion test (`tests/test_writer_isolation.py::test_claude_subprocess_argv_contains_allowed_tools`) catches config drift.
- **Runtime trace classifier** — new HARD gate `infra_context_contamination` operates on the **RAW** `writer_tool_calls.json` trace (NOT the normalized `WRITER_TOOL_NAMES` set, which is what the existing `MCP_TOOLS_NEVER_INVOKED` gate uses). Two sub-classes: `wrong_tool_family` (any non-`mcp__sources__*` call) and `handoff_or_orchestrator_file` (Read of denylisted paths). TERMINAL severity — build halts.
- **Failure taxonomy skeleton** — `scripts/audit/failure_classes.py` with `FailureClass` enum + `FailureRecord` dataclass. Card 2 extends with more enum values + recovery handlers.
- **Rename** — `curriculum-maintainer` → `curriculum-orchestrator` across `claude_extensions/agents/`, `.claude/agents/`, `.codex/agents/` (`.md` + `.toml`), `.agent/agents/`, plus `CLAUDE.md` references. Zero code/config orphans remain (verified via grep).
- **Bloat trim** — orchestrator file 210 → 93 lines. Removed content already auto-loaded elsewhere (behavioral rules in MEMORY.md, reference docs table in CLAUDE.md, plugins, inlined pre-submit checklist). Kept orchestrator-specific failure modes + proactive-protocol triggers + curriculum-specific ops rules.

### Phase 4 ULP calibration (#1950) — empirical band derivation

Codex dispatched against the 6 ULP TXT corpora (S1-S6, 240 lessons total, 12,358 cumulative VESUM lemmas). Built per-lesson lemma-frequency map. Season → CEFR mapping: S1 → A1, S2-S3 → A2, S4-S6 → B1+ full-immersion reference. Per-season density medians: S1 37%, S2 49%, S3 51%, S4 90%, S5 84%, S6 77%.

A1 vocab knees fit from S1 transition points: 0 → `a1-m01-03` (5-25%), 140 → `a1-m04-06` (8-30%), 242 → `a1-m07-14` (10-38%), 573 → `a1-m15-24` (15-24%), 593 → `a1-m25-34` (15-40%), 621 → `a1-m35-54` (20-40%), 647 → `a1-m55+` (25-48%).

Backward-compat verified: a1-m01-03 advisory band stayed within ±2pp of pre-flip static `IMMERSION_POLICIES["a1-m01-03"]`. Flag `USE_ULP_IMMERSION_DERIVATION=True` flipped.

### V7 build worktree safety (#1949 + #1952)

The session opened with an incident: dropping `stash@{0}` from a previous session discarded the validated `a1/my-morning` V7 build artifacts (5/5 visual predicates SATISFIED). Root cause: V7 builds wrote to the main project tree, telemetry files (`python_qg.json`, etc) weren't gitignored, working tree became dirty, stash-and-lose risk materialized.

Two-layer fix:

1. **`.gitignore`** patterns at `curriculum/l2-uk-en/*/*/` for the 5 telemetry files (#1949).
2. **`v7_build.py --worktree`** flag (#1952) creates `.worktrees/builds/{level}-{slug}-{timestamp}/` + branch `build/{level}/{slug}-{timestamp}`, runs the build inside the worktree, prints `BUILD_*` summary, preserves worktree on failure (no auto-cleanup so the user can inspect partial state). Main project tree stays clean regardless.

Pattern matches `scripts/delegate.py --worktree` which already does the same for agent dispatches.

## Carry-over queue (priority-ordered)

| # | Item | State |
|---|---|---|
| **1** | **Phase 2a — rebuild `a1/my-morning` (m20) end-to-end with full student-aware pipeline.** Brief: `docs/dispatch-briefs/2026-05-13-phase-2a-m20-my-morning-rebuild.md`. USER-RUN. ~30-45 min. Validates: writer isolation (Card 1), `{LEARNER_STATE}` injection at ~573 cumulative lemmas, ULP knee-transition band selection (`a1-m15-24`), all 5 visual-contract predicates from the prior build. | 📋 **P0 — primary next step** |
| **2** | **Phase 2b — A1 m01-m07 warm-up batch** sequentially. Brief: `docs/dispatch-briefs/2026-05-13-phase-2b-m1-m7-warmup-batch.md`. USER-RUN sequentially (next module's learner-state depends on prior module's vocab being on `main`). Tests band progression through 2 knees (140 and 242). | 📋 P1 after Phase 2a passes |
| 3 | Disposition PR #1873 (starlight 0.38→0.39.2) — held with comment, Frontend (build + vitest) blocking fail. Either pin to 0.38.x, apply a follow-up fix, or close. | 📋 user decision |
| 4 | **Card 2 — V7 rollout failure taxonomy + writer fix-loop policy + quarantine schema + phase-aware iteration caps.** Not yet drafted; depends on Card 1 telemetry validating the contamination class boundary. Start when Phase 2a + 2b complete cleanly. | 📋 deferred — needs Card 1 telemetry first |
| 5 | Pending Decision Cards: `2026-05-12-autonomous-codex-dispatch-narrow-class.md`, `2026-05-09-decision-graph-view.md`, `2026-05-06-multi-ui-channel-participation.md`, `2026-05-13-writer-split-by-tab.md` (DEFERRED per Card 1). | 📋 |
| 6 | #1908 Layered-harness audit (EPIC #1865 structural) | 📋 |
| 7 | #1905 Pipeline replay-mode regression suite (EPIC #1865 structural) | 📋 |
| 8 | #1896 Secret-leak prevention follow-ups | 📋 |
| 9 | #1933 /goal v2 wishlist (4 harness improvements) | 📋 |

## Open items / decisions still pending

- **Phase 2a outcome.** Whether the student-aware pipeline produces visual-contract parity with the previous build, and whether the new isolation gate stays quiet. Real telemetry signal.
- **Card 2 scope.** Starts after Phase 2a/2b. Three sub-decisions implicit: (a) whether `infra_context_contamination` should ever become "writer-correct" recovery action instead of TERMINAL (currently TERMINAL is right; revisit only if false-positives appear); (b) full failure-class taxonomy (currently just 2 enum values; expand to ~12 per the discussion thread); (c) quarantine JSONL schema for failed modules + queue continuation policy.
- **Per-track pilot strategy.** A1 has 55 modules. After m01-m07 + m20 ship, the natural next questions are: do we batch-build the remaining 48? Per-band? Per-knee? Open.

## Operational notes

### Dispatch timeout lesson (encoded)

Two Codex dispatches this session showed `status: timeout` with `worktree_dirty_on_exit: false` — but the work HAD completed (commit landed, PR opened) and Codex just went idle waiting for "anything else?" instructions when the silence-timeout fired.

**Recovery protocol when a Codex dispatch hits `status: timeout`** (added to my orchestrator mental model — should encode into `curriculum-orchestrator.md` in a follow-up):

1. Check `git -C {worktree} log --oneline main..HEAD` — if there's a commit, work landed.
2. Check `gh pr list --search "head:codex/{task}"` — PR might already be open.
3. Don't re-push or re-open if either is true — the dispatch's `response_chars: 0` lies; the git state is truth.

Applied successfully twice this session (v7-build dispatch, Card 1 dispatch — the latter actually emitted a proper response and didn't timeout, but the pattern was ready).

### Hygiene sweeps

| Removed | Count |
|---|---|
| Stashes dropped | 1 (`stash@{0}: pre-build-queue-2026-05-13` — caused the data-loss incident; user authorized drop) |
| Local-only stale branches | 2 (`codex/1879-fix-ci-and-wikipedia`, `codex/1888-rule-autoload-dedupe`) |
| Stale worktrees | 4 (`claude/session-handoff-2026-05-13`, `codex/assembler-tab3-dedupe-2026-05-14`, all merged PRs' worktrees) |
| Gone-upstream branches | 4 (cleaned alongside worktrees) |

End-of-session state: 4 worktrees remain — main + codex-interactive (persistent dev env) + 2 held-PR worktrees (`claude/bakeoff-2026-05-12-night`, `codex/pass2-only-contract-test-2026-05-13`).

### Agent definition state

Post-merge of #1953:

- `claude_extensions/agents/curriculum-orchestrator.md` (renamed from curriculum-maintainer, bloat-trimmed to 93 lines) — orchestrator profile
- `claude_extensions/agents/curriculum-writer.md` (new, ~60 lines) — lean writer profile, tool-restricted to `mcp__sources__*`
- `.codex/agents/curriculum-orchestrator.toml` (renamed) — Codex orphan for orchestrator
- `.codex/agents/curriculum-writer.toml` (new) — Codex orphan for writer
- Deploy targets `.claude/`, `.codex/`, `.agent/` synced via `scripts/deploy_prompts.sh`

## Predecessor brief

`docs/session-state/2026-05-14-v7-mdx-assembler-shipped-brief.md` — set up the architectural finding about V7 dropping the v6 learner-state system (now resolved via #1939 + #1943 + #1950) and the multimedia resources gap (now resolved via #1937). Plus the carry-over queue Items 1-3 around Bug d, which all shipped this session.

---

*Format spec: `claude_extensions/rules/workflow.md` § "Two-tier handoffs". Opening action for next session: read this brief + check `gh pr view 1953` for the final merge SHA + run Phase 2a build per the dispatch brief.*
