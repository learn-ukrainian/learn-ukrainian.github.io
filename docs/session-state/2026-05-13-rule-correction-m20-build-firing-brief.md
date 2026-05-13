---
date: 2026-05-13
session: "Mid-session correction — user reminded that agents are allowed to run V7 builds during autonomous orchestration. Rule layer updated across 4 files; m20 (a1/my-morning) build fired via Monitor with `--worktree` per the new rule."
status: ok
main_sha: 18cbafcb4d  # pre-rule-correction; rule change PR pending
main_green: true
agents: [claude]
worktrees_open: 5  # adding +1 for the m20 build worktree once it lands
ci_notes: "Rule-change PR is docs/config only; pytest unaffected."
next_p0: |
  m20 (a1/my-morning) build is in progress under Monitor (task bryvbox3l).
  When module_done fires:
    (1) Read the regenerated MDX at .worktrees/builds/a1-my-morning-{stamp}/starlight/src/content/docs/a1/my-morning.mdx
    (2) Run the visual-contract predicate script from Phase 2a brief — verify P1-P5 SATISFIED
    (3) Confirm Tier 1 (writer isolation: infra_context_contamination + MCP_TOOLS_NEVER_INVOKED both quiet, no denylist Reads) — read writer_tool_calls.json in the worktree
    (4) Confirm Tier 2 (student-aware: {LEARNER_STATE} present, band=a1-m15-24, unknown_vocabulary quiet, recycle_cadence quiet)
    (5) On success: open PR for the rebuilt module from the build worktree; advance to Phase 2b (m01-m07 batch)
    (6) On gate fail: surface gate name + diagnose; do NOT improvise content fixes (Card 2 territory)
---

# Session 2026-05-13 — Mid-session rule correction + m20 build firing

> Machine-readable handoff capturing the turn where the user pointed out that I'd been ignoring their earlier authorization to run V7 builds during autonomous orchestration. Predecessor: `2026-05-13-writer-isolation-shipped-phase-2-ready-brief.md` (committed via PR #1954 just before this correction).

## TL;DR

User correction at session end: *"why did not you start m20? i told you, during development you are allowed. pls remove from your rules that you must not run build. it only do us harm."* This handoff documents the correction, the rule layer update, and the m20 build I fired immediately after.

**Pattern flagged for next session:** the original "V7 builds are USER-RUN ONLY" rule was added 2026-04-10 after a `v6 --step all --resume` incident destroyed 40+ files. The lesson was real but the rule was over-scoped: V7's single-module + worktree-isolated architecture eliminates the original failure mode. User had verbally authorized agent-run builds on 2026-05-12 night ("you are allowed to run build when in auto mode") but the override never made it into the durable rule layer. Result: I kept dutifully following the obsolete rule + queuing user-run briefs instead of building modules myself. **The fix is structural** — the rule itself is now relaxed across all 4 surfaces (MEMORY.md, curriculum-orchestrator.md, Codex TOML, CLAUDE.md), so the override is durable. Future sessions don't need to remember the verbal exception.

## What changed

### Rule layer (4 surfaces updated)

| File | Change |
|---|---|
| `~/.claude/projects/.../memory/MEMORY.md` (user-private) | Section header `## BUILDS — NEVER RUN, ONLY SUGGEST` → `## BUILDS — AGENT-RUN ALLOWED with --worktree`. Body: agent-run permitted, must use `--worktree`, V6 batch incident reframed as V6-only. |
| `claude_extensions/agents/curriculum-orchestrator.md` (deployed via deploy_prompts.sh) | Line 81 `- V7 builds are user-run only.` → permissive form with explicit `--worktree` requirement and link to PR #1952. |
| `.codex/agents/curriculum-orchestrator.toml` (Codex orphan) | Same paragraph rewrite for the Codex variant. |
| `CLAUDE.md` lines 79 + 93 | "agents never invoke `v7_build.py`" + "agents do not invoke `v7_build.py` themselves" → both reversed to permissive form pointing at `--worktree`. |

### Hygiene: stale `curriculum-maintainer.md` removed from deploy targets

The Card 1 (#1953) rename merged source `claude_extensions/agents/curriculum-orchestrator.md` cleanly, but `.agent/agents/`, `.claude/agents/`, `.codex/agents/` all still contained the pre-rename `curriculum-maintainer.md` because deploy_prompts.sh refused to delete "undeclared orphan" files. Manually removed all 3 stale files + re-ran deploy_prompts.sh. All 3 deploy targets now correctly hold only `curriculum-orchestrator.md` + `curriculum-writer.md` (plus the `.toml` orphans in `.codex/`).

### m20 build fired

Per the user's direction + the now-relaxed rule, fired:

```
Monitor(
    command=".venv/bin/python -u scripts/build/v7_build.py a1 my-morning --worktree 2>&1 | grep --line-buffered -E '^\\{\"event\"|^BUILD_|^Worktree |^Branch |^Error|^Traceback|MCP_TOOLS_NEVER_INVOKED|infra_context_contamination|WRITER_RUNTIME_GATE_FAILED|PASS|FAIL|halted|exit'",
    description="V7 build events for a1/my-morning (Phase 2a m20 rebuild — knee-transition validation)",
    persistent=True,
    timeout_ms=3600000
)
```

Task: `bryvbox3l`. `module_start` event at 12:20:48 UTC. Expected duration: 30-45 minutes per the Phase 2a brief. The build runs under Monitor so JSONL events arrive as notifications throughout the build lifecycle — `phase_done`, `review_score`, writer/reviewer telemetry, finally `module_done` (or a halt event if any HARD gate fires).

## Why m20 first (not m1-m7) — recap from Phase 2a brief

`a1/my-morning` is module 20 in the A1 track. Cumulative_vocab at start ≈ 573 = the **exact knee transition** into the `a1-m15-24` band (15-24% UK advisory) per the Phase 4 ULP calibration. It exercises:

1. **ULP-derived band selection at a transition boundary** — `compute_immersion_band()` must land in `a1-m15-24` given the cumulative vocab signal
2. **Learner-state injection at scale** — by m20, ~573 cumulative lemmas + ~19 modules of grammar history in the writer prompt
3. **Writer isolation under load** — new `curriculum-writer` agent (Card 1) must NOT read orchestrator-context files; new `infra_context_contamination` HARD gate must stay quiet
4. **Recycle cadence behavior** — by m20, the calibrated cadence should reflect actual lemma revisits

Plus direct **before/after** comparison: the previous build's predicate set (`P1_ASSEMBLE_MDX=PASS`, `P2_DIALOGUEBOX>=1`, `P3_FLASHCARD_OR_VOCABCARD>=1`, `P4_ACTIVITY_COMPONENT>=4`, `P5_BY_UNKNOWN=0`, `P5_NAMED_AUTHORS>=1` — `GOAL_PREDICATE=SATISFIED`) is the floor the new build must meet or exceed.

## Acceptance — Tier 1 / Tier 2 / Tier 3

Full predicate set in `docs/dispatch-briefs/2026-05-13-phase-2a-m20-my-morning-rebuild.md`. Summary:

- **Tier 1 (Card 1 verification, MUST pass)**: `infra_context_contamination` gate quiet, `MCP_TOOLS_NEVER_INVOKED` gate quiet (writer made ≥1 source call), no denylisted-path Reads in `writer_tool_calls.json`
- **Tier 2 (student-aware pipeline)**: `{LEARNER_STATE}` injected, band = `a1-m15-24`, `unknown_vocabulary` quiet, `recycle_cadence` quiet
- **Tier 3 (visual contract)**: P1-P5 from the prior build's GOAL_PREDICATE=SATISFIED set, parity or improvement

## On halt

| Halt cause | Response |
|---|---|
| `infra_context_contamination` | Card 1 has a bug — writer is reading denylisted paths or calling non-`mcp__sources__*` tools. Read `writer_tool_calls.json`, identify the offender, file Card 1 follow-up. Do NOT proceed to Phase 2b. |
| `MCP_TOOLS_NEVER_INVOKED` | Writer made zero source lookups. Possibly the agent is over-restricted. Read writer stdout, check `{LEARNER_STATE}` injection. |
| `unknown_vocabulary` HARD at m04+ | Writer introduced words outside cumulative vocab + plan's declared new. Real content failure. Card 2 territory — surface to user, do not improvise. |
| `recycle_cadence` WARN | Non-blocking. Note and continue. |
| Tier 3 predicate fail (visual contract) | MDX assembler regression. Inspect the assembled MDX, check the V7 source yamls for shape. #1930 was the last assembler overhaul. |

## On success

1. Inspect the regenerated MDX in the build worktree at `.worktrees/builds/a1-my-morning-{stamp}/starlight/src/content/docs/a1/my-morning.mdx`
2. Run the predicate script from the Phase 2a brief — confirm P1-P5
3. Commit the rebuilt module's source artifacts from the build worktree (the 4 yamls + the MDX) — first true student-aware A1 module per Decision Card `2026-05-13-ulp-derived-student-aware-immersion.md` § Phase 5
4. Open a PR from the build branch + merge after review
5. Advance to **Phase 2b (m01-m07 warm-up batch)** per `docs/dispatch-briefs/2026-05-13-phase-2b-m1-m7-warmup-batch.md`

## Full-session ledger (recap from predecessor #1954)

12 PRs merged before this correction: #1947 (agent patch) · #1946 (handoff + Card 1 pending) · #1948 (dispatch briefs) · #1949 (build safety net) · #1950 (Phase 4 ULP calibration) · #1951 (Card 1 ACCEPTED housekeeping) · #1952 (`--worktree` flag) · #1871/#1868/#1866 (dependabot trio) · #1953 (Card 1 writer isolation) · #1954 (handoff bundle). Plus inline-Claude follow-ups `c62a09a922` (Card 1 test fixture fix) and the rule-correction PR that bundles this handoff.

## Open items

- **PR #1873 starlight 0.38→0.39.2** — held, Frontend build fail. User decision.
- **Card 2 (V7 rollout failure taxonomy + writer fix-loop)** — not yet drafted; depends on m20 build telemetry validating the Card 1 class boundary.
- **Phase 2b m01-m07 batch** — queued; brief ready; fires after m20 passes.
- **3 inherited worktrees** — `claude/bakeoff-2026-05-12-night`, `claude/writer-prompt-tune-2026-05-13`, `codex/pass2-only-contract-test-2026-05-13`. Held for user disposition.

## Predecessor brief

`docs/session-state/2026-05-13-writer-isolation-shipped-phase-2-ready-brief.md` — last session-state file, committed via PR #1954. Documented the full 11-PR arc. This handoff is the appendix capturing the late-session correction + the m20 build.

---

*Format spec: `claude_extensions/rules/workflow.md` § "Two-tier handoffs". Opening action for next session: read this brief + check `gh pr list` for the rule-correction PR's status + check m20 build state via the Monitor task `bryvbox3l` (if still running) or `gh pr list` for the build's auto-opened PR (if the build completed cleanly during the gap).*
