---
date: 2026-05-13
session: "Morning continuation after overnight halt (#1944). Multi-agent discussion converged 3-way [AGREE] at round 2 on V7 e2e workflow architecture. Card 1 (curriculum-writer isolation + #1944 fix) drafted, PENDING signoff. Card 2 (rollout failure taxonomy) deferred. Session ending at ~513K context per #M-2 handoff-zone threshold."
status: handoff-ready
mode: handoff-required
authority:
  - "user direction 2026-05-13 morning: context approaching 750K auto-compact danger; switch to handoff before pushing implementation"
predecessor: "docs/session-state/2026-05-13-overnight-orchestration-brief.md"
---

# Morning Brief — V7 Architecture Converged + Card 1 Ready

> Live successor to the overnight orchestration brief. Read THAT first for the overnight state (5 prep PRs shipped, build queue halted on #1944), then this for what changed this morning.

## TL;DR

Multi-agent discussion (Claude + Codex + Gemini) converged `[AGREE]` at round 2 on a writer-isolation architecture that unblocks #1944. **Card 1 is drafted at `docs/decisions/pending/2026-05-13-curriculum-writer-isolation.md` — awaiting user signoff before implementation.** Card 2 (broader rollout failure taxonomy + quarantine) deferred until Card 1 ships and we have telemetry to ground the policy.

## What converged

| Topic | Decision |
|---|---|
| Architecture | Option F+ — `curriculum-writer` agent (lean, MCP-sources-only) + runtime trace isolation gate + raw `writer_tool_calls.json` classifier (not just normalized counter) |
| Agent split | Rename `curriculum-maintainer` → `curriculum-orchestrator`; add new `curriculum-writer` for v7_build writer phase |
| Tab specialization (Option B) | DEFERRED — both Codex (architectural) and Gemini (pedagogical-coherence) push back. Don't ship until failure-distribution data justifies. |
| Reviewer fix-loop | NO — single pass + atomic find/replace + re-audit. ADR-007 preserved. |
| Writer fix-loop | YES (Card 2): distinct-gate iteration + atomic fixes + cap N (dev=3/rollout=5). Same-gate retry forbidden. |
| Iteration caps | dev=3, rollout=5; after exhaustion → quarantine, queue continues |
| HARD gates | absolute, conjunctive, no "9 of 10 → ship" thresholds |
| Quarantine schema | `orchestration/quarantine/v7-build.jsonl` (NOT `status/` which auto-generates) |
| `infra_context_contamination` gate | TERMINAL class — operates on RAW `writer_tool_calls.json`, catches non-`mcp__sources__*` tools AND reads of orchestrator/handoff paths |
| Card structure | SPLIT — Card 1 (immediate blocker, this card) + Card 2 (broader rollout policy, deferred) |

Discussion threads in channel `v7-e2e-rollout-design-2026-05-13`:
- Round 1 (initial positions): `5a36c61bf09443caa763a70c79dc7dc0`
- Round 2 (convergence): `88ca87e57d064c99bca196442e46f027`

## Card 1 — what to sign off on

`docs/decisions/pending/2026-05-13-curriculum-writer-isolation.md` covers:

1. New `curriculum-writer` agent (~60 lines, lean prompt, strips generic capabilities per Gemini)
2. Spawn-layer isolation verification + argv unit assertion (`--allowedTools mcp__sources__*` actually passed)
3. Failure-class taxonomy skeleton at `scripts/audit/failure_classes.py` (before isolation gate per Codex — avoid stringly-typed debt)
4. `infra_context_contamination` HARD gate (raw `writer_tool_calls.json` classifier, terminal)
5. #1944 replay regression test in `tests/test_writer_isolation.py`
6. `curriculum-maintainer` → `curriculum-orchestrator` rename
7. (deferred to Card 2) Quarantine JSONL writer
8. Smoke build `a1/sounds-letters-and-hello`

Estimated ~340 LOC, one dispatch PR.

### Card 1 open questions (orchestrator defaults — user can override)

1. **Rename in same PR as new agent + isolation gate?** Default: YES (atomicity).
2. **Mirror `curriculum-writer` across all 4 agent dirs (`claude_extensions/`, `.claude/`, `.codex/`, `.agent/`)?** Default: YES (mirror existing convention).
3. **Bloat trim on the renamed orchestrator (remove auto-loaded-elsewhere content) in same PR?** Default: YES (natural cover for the rename).
4. **Argv assertion: dry-run CLI vs mock subprocess?** Default: MOCK (catches config drift cheaply).

## Card 2 — outline only, NOT drafted

To draft after Card 1 ships + isolation telemetry validates the class boundary. Scope:

- Failure-class taxonomy formalization (full enum: `mcp_tools_never_invoked`, `strict_json_parse`, `formatting_standards`, `word_count`, `plan_sections`, `mdx_render`, `vesum_unknown`, `russianism_detected`, `calque_detected`, `paronym_detected`, `citation_unresolved`, `unknown_vocab`, `missing_ipa`, `resources_search_attempted`, `naturalness_flag`, `decolonization_flag`)
- Quarantine schema: `orchestration/quarantine/v7-build.jsonl` with full field list (per Codex's Round 1)
- Writer fix-loop: distinct-gate iteration, atomic fixes, cap N=3 dev / N=5 rollout, same-gate retry forbidden (ADR-007)
- Phase-aware caps + queue-continuation semantics ("rollout failures self-recover or self-quarantine, never escalate to human at scale")
- Telemetry events: `gate_failure` with `failure_class`, `recovery_action`, `terminal_bool`
- Test fixture coverage for each failure class
- `test_no_rewrite_contract.py` extension to enforce the no-same-gate-retry invariant in the fix-loop

## Build queue state

| Module | State | Plan-review verdict (#1938) |
|---|---|---|
| sounds-letters-and-hello | ❌ HALTED on #1944 contamination | NEEDS_FIX (2 MEDIUM) |
| reading-ukrainian | ⏸ blocked | PASS |
| special-signs | ⏸ blocked | PASS |
| stress-and-melody | ⏸ blocked | PASS (1 MEDIUM forward-ref) |
| who-am-i | ⏸ blocked | NEEDS_FIX (1 HIGH zero-words section, 3 MEDIUM frozen-chunks) |
| my-family | ⏸ blocked | PASS borderline (1 MEDIUM register edge) |
| checkpoint-first-contact | ⏸ blocked | NEEDS_FIX (1 HIGH Surzhyk row, 1 MEDIUM word_target) |

All 7 plans are `lifecycle: locked` from 2026-04-23 review. NEEDS_FIX items are 1-line YAML edits but require version-bump + changelog per locked-lifecycle protocol — deferred.

## Issues currently open

| # | Title | Priority |
|---|---|---|
| **#1944** | [BLOCKER] writer subprocess behaves as orchestrator — Card 1 resolves | **P0** |
| #1940 | [curriculum] Add 'pedagogical_deviations_from_standard:' plan field | P1 (tie to PR2 schema work in future) |
| #1941 | [curriculum] A1-checkpoint word_target inconsistency: 5/7 at 1200 vs 2/7 at 1000 | P2 |
| #1942 | [harness] Forbid `pytest -x` in final pre-push verification | P2 |

## Recommended next-session opening sequence

1. **Cold-start orient** via Monitor API per `claude_extensions/rules/workflow.md`. Read `docs/session-state/current.md` for index; this brief is the top entry.
2. **Read Card 1** — `docs/decisions/pending/2026-05-13-curriculum-writer-isolation.md`. Decide on the 4 open questions (defaults are sensible).
3. **Move Card 1 from `pending/` to `docs/decisions/2026-05-13-curriculum-writer-isolation.md`** with `**Decided:**` line; commit via worktree-PR.
4. **Dispatch Card 1 implementation** to Codex with the 8-step order (writer agent file → spawn-layer verification → taxonomy skeleton → isolation gate → replay test → rename → trim → smoke build prep). Brief should explicitly cite the file:line anchors Codex surfaced in convergence (`linear_pipeline.py:1995-2010`, `claude.py:285-289`, etc.).
5. **Review + merge Card 1 PR** when CI green. Mind the #1942 lesson: full pytest suite (no `-x`) before push.
6. **Smoke-build `a1/sounds-letters-and-hello`** via Monitor tool to confirm:
   - `infra_context_contamination` gate is quiet (writer doesn't make non-MCP calls)
   - `MCP_TOOLS_NEVER_INVOKED` gate is quiet (writer makes ≥1 `mcp__sources__verify_word`)
   - Module builds to completion OR fails on a content-class HARD gate (which Card 2 will address)
7. **If smoke passes:** resume the 7-module queue via `/tmp/build-queue-a1-first-7.sh` (Plan A override remains active for this verification batch).
8. **If smoke fails on content class:** start Card 2 draft; do not improvise content-class fixes inline.
9. **Begin Card 2 draft** in parallel with smoke build (it's the next architectural piece).

## Working-tree state at handoff

- Local main = origin/main = `fe508afea8` (post-#1945)
- Stash `pre-build-queue-2026-05-13` PRESERVED — contains a1/my-morning V7 source artifacts from prior session, user-decision-pending per Decision Card `2026-05-13-ulp-derived-student-aware-immersion.md` Phase 5
- 5 dispatch worktrees from PRIOR sessions still mounted (not session-2026-05-13's to clean up): `bakeoff-2026-05-12-night`, `writer-prompt-tune-2026-05-13`, `assembler-tab3-dedupe-2026-05-14`, `pass2-only-contract-test-2026-05-13`, `codex-interactive` (detached HEAD)
- This session's worktree (`session-handoff-2026-05-13`) cleans up automatically when its PR merges

## Inline orchestrator stats this session

| Metric | Value |
|---|---|
| PRs merged | 6 (#1936, #1937, #1938, #1939, #1943, #1945) |
| Dispatches fired | 5 (PR1 v1 abort, PR1 v2, plan-review, multimedia, PR2) |
| Inline fixups by orchestrator | 4 (urlparse security, dict-grammar, lazy-import, lesson-schema-yaml regen) |
| Issues filed | 4 (#1940, #1941, #1942, #1944) |
| Multi-agent discussions | 1 (3-way [AGREE] at round 2) |
| Decision Cards drafted | 1 (Card 1, this session) + 1 outlined (Card 2, deferred) |
| Build queue progress | 0/7 — halted on module 1 by #1944, queue intact for resume |

## Carry-over from overnight handoff (still pending)

- **#1873 starlight 0.39, #1874 react 19.2.6** — real Frontend CI failures, need investigation
- **Dependabot majors:** #1866 lxml 5→6, #1868 attrs 25→26 — conservative bias
- **Dependabot big-minor:** #1871 mcp-memory-service — conservative bias
- **52 remaining A1 plans** need `plan.targets` migration (PR2 only did 3 as proof-of-shape)
- **Phase 4 calibration** to flip `USE_ULP_IMMERSION_DERIVATION` False → True
- **A1/my-morning Phase 5 rebuild** (per ULP Decision Card)
- **Pending Decision Cards still:** `2026-05-06-multi-ui-channel-participation.md`, `2026-05-09-decision-graph-view`, `2026-05-12-autonomous-codex-dispatch-narrow-class.md`, `2026-05-13-writer-split-by-tab.md`

## Why end the session here

Context at ~513K. Per MEMORY.md #2: 500K+ is handoff zone, 750K is auto-compact (destructive). Pushing Card 1 implementation inline would consume context proving the actual cost (worktree setup × Codex dispatch wait × smoke build wait × debugging surprises). Codex dispatch + smoke build is ~2-4 hr — that fits a fresh session at 0K context, not the tail of a 513K one.

Cleanly handing off here means next-session orchestrator opens at ~778-byte warm-cache (per Monitor API hash routing), reads this brief + Card 1 + the predecessor brief, and starts dispatch with full fidelity. The discipline is the cost-amortization #M-2 anchored.

---

*Predecessor: `docs/session-state/2026-05-13-overnight-orchestration-brief.md`. Discussion convergence transcript: `ab channel tail v7-e2e-rollout-design-2026-05-13 --thread 88ca87e57d064c99bca196442e46f027`.*
