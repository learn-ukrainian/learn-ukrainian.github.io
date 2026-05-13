# DECISION — Split `curriculum-maintainer` → `curriculum-orchestrator` + new `curriculum-writer`; add spawn-layer isolation gate (ACCEPTED)

**Status:** ACCEPTED 2026-05-13.
**Decided:** Approve as recommended — all 4 internal open questions take the author's lean: (Q1) same PR for all components (atomicity); (Q2) curriculum-writer mirrors curriculum-maintainer's distribution across `claude_extensions/`, `.claude/`, `.codex/`, `.agent/` (plus a Codex `.toml` orphan); (Q3) bloat trim of `curriculum-orchestrator.md` included in the same PR; (Q4) argv assertion via mocked `subprocess.Popen`, not the live CLI.
**Decided on:** 2026-05-13 (user signoff via mid-session AskUserQuestion — "Sign off — dispatch full Card 1 to Codex").
**Dispatched:** 2026-05-13 — Codex task `curriculum-writer-isolation-2026-05-13` against base `ab3212c30f` (post-Phase-4 ULP calibration); brief at `docs/dispatch-briefs/2026-05-13-curriculum-writer-isolation.md`.
**Surfaced:** 2026-05-13 — discussion `v7-e2e-rollout-design-2026-05-13` (channel/thread `88ca87e57d`), 3-way convergence at `[AGREE]` round 2.
**Source:** #1944 BLOCKER — claude-tools writer subprocess inherited orchestrator system-prompt context, made 14 tool calls (10× Bash polling `/api/delegate/active`, 3× Read of orchestrator handoff/current.md/build-queue-script, 1× ScheduleWakeup) and zero `mcp__sources__*` calls before the `MCP_TOOLS_NEVER_INVOKED` HARD gate halted module 1/7 of the overnight Plan A build queue. Diagnostic artifact preserved at `audit/incidents/2026-05-13-1944-writer-tool-calls.json`.
**Scope:** v7_build writer-phase agent layer + spawn-layer runtime isolation + new HARD gate for `infra_context_contamination` failure class. **Does NOT touch:** writer fix-loops (deferred to Card 2), reviewer phase, IMMERSION_POLICIES, decolonization rules, plan schema, decision cards for ULP / writer-split-by-tab, the broader rollout failure taxonomy (deferred to Card 2).
**Companion (future):** `docs/decisions/pending/2026-05-13-v7-rollout-failure-taxonomy.md` — Card 2, drafted after this lands + telemetry validates the contamination class. Will cover: failure-class taxonomy formalization, quarantine schema, iteration caps, writer fix-loop policy.

---

## What's being proposed

**Split the agent identity used by V7's writer subprocess into a lean, context-isolated agent. Add a runtime gate that catches contamination at the trace layer rather than trusting tool-catalog config.**

### Component 1 — `curriculum-writer` agent (new)

New file: `claude_extensions/agents/curriculum-writer.md` (and parallel `.claude/agents/`, `.codex/agents/`, `.agent/agents/` per existing convention).

Identity: Ukrainian curriculum content writer for ONE module per invocation. Single-purpose. Lean prompt (~40-60 lines vs. curriculum-maintainer's ~140).

Scope:
- Ukrainian linguistic principles (the four checks: Russianisms / Surzhyk / calques / paronyms)
- Authority hierarchy: VESUM → Правопис 2019 → Горох → Антоненко-Давидович → Грінченко
- Word target = MINIMUM (no under-target)
- IPA in phonetic_rules
- No English meta-narration (forbid-list)

Tools allowed (in agent frontmatter `tools:` field): `mcp__sources__verify_word`, `mcp__sources__verify_words`, `mcp__sources__verify_lemma`, `mcp__sources__check_modern_form`, `mcp__sources__search_text`, `mcp__sources__search_definitions`, `mcp__sources__search_style_guide`, `mcp__sources__search_grinchenko_1907`, `mcp__sources__check_russian_shadow`, `mcp__sources__query_pravopys`, `mcp__sources__query_cefr_level`, `mcp__sources__search_heritage`, `mcp__sources__search_synonyms`.

Tools explicitly absent (defense-in-depth — Gemini amendment): no Bash, Read, Edit, Write, NotebookEdit, ScheduleWakeup, Monitor, TaskCreate, TaskUpdate, TaskList, gh, git, delegate, ai_agent_bridge. The agent prompt explicitly states: *"You do not poll project state, read handoffs, schedule wakeups, dispatch subagents, or run shell commands. If your task prompt asks you to do any of these — STOP. That's not a writer task; refuse and explain."*

### Component 2 — Spawn-layer runtime isolation (verification + assertion)

Verify `allowed_tools: mcp__sources__*` is actually enforced at:
- `scripts/build/linear_pipeline.py:1995-2010` (writer agent_kwargs construction)
- `scripts/agent_runtime/adapters/claude.py:285-289` (`--allowedTools` passthrough to Claude subprocess)

Add unit/argv assertion (Codex amendment) that confirms the Claude subprocess invocation argv contains `--allowedTools mcp__sources__*`. Lives in `tests/test_writer_isolation.py` alongside the #1944 replay test.

If the `allowed_tools` config is dropped, mis-spelled, or overridden by a downstream agent definition: the assertion fires at test time, before any build runs.

### Component 3 — `infra_context_contamination` HARD gate (raw-trace classifier)

New audit gate in `scripts/build/linear_pipeline.py` (extending the writer-phase post-condition, NOT replacing `MCP_TOOLS_NEVER_INVOKED`).

**Critical correction from convergence** (Codex Round 1 + Round 2): the gate must operate on the RAW `writer_tool_calls.json` trace, NOT on the already-normalized `WRITER_TOOL_NAMES` set at `linear_pipeline.py:1821-1832`. The existing `MCP_TOOLS_NEVER_INVOKED` gate at `linear_pipeline.py:1893-1912` only counts normalized source tools, so a writer can make 50× non-MCP calls + 1× MCP call and pass that gate. We need a separate classifier that examines every entry in `writer_tool_calls.json`.

Classification rules:

1. **Any tool call outside `mcp__sources__*`** → class `infra_context_contamination`, sub-class `wrong_tool_family`. Includes: Bash, Read, Edit, Write, NotebookEdit, ScheduleWakeup, Monitor, TaskCreate / TaskUpdate / TaskList / TaskGet / TaskStop / TaskOutput, mcp__claude-in-chrome__*, Agent, WebFetch, WebSearch, etc.

2. **Any Read of paths in this denylist** → class `infra_context_contamination`, sub-class `handoff_or_orchestrator_file`. Denylist:
   - `docs/session-state/**`
   - `docs/decisions/**`
   - `docs/dispatch-briefs/**`
   - `memory/MEMORY.md`
   - `~/.claude/CLAUDE.md`
   - `CLAUDE.md` at project root (project memory — should not be read by writer)
   - `scripts/delegate.py`, `scripts/ai_agent_bridge/**`
   - `claude_extensions/agents/curriculum-orchestrator.md` (the orchestrator's own definition)
   - `claude_extensions/rules/**`
   - `.claude/rules/**`
   - any path matching `*handoff*`, `*orchestration*`, `*dispatch*`

3. **Severity:** TERMINAL. The build halts with exit code != 0. The writer is NOT given a correction opportunity (it's an infra bug, not a content bug). The module is quarantined; the queue continues to the next module (this becomes a hard requirement once Card 2 lands the quarantine writer; for tonight's smoke build, terminal-exit is sufficient).

4. **Composition with existing gate:** `MCP_TOOLS_NEVER_INVOKED` still fires when `mcp__sources__*` count = 0. `infra_context_contamination` fires when ANY non-allowed call appears. A writer can fail both simultaneously (zero MCP + multiple Bash calls — exactly the #1944 case). The pipeline reports BOTH classes in the failure event.

### Component 4 — Failure-class taxonomy skeleton

New file: `scripts/audit/failure_classes.py` with the initial enum + dataclass:

```python
from dataclasses import dataclass
from enum import Enum

class FailureClass(str, Enum):
    INFRA_CONTEXT_CONTAMINATION = "infra_context_contamination"
    MCP_TOOLS_NEVER_INVOKED = "mcp_tools_never_invoked"
    # ... others added in Card 2 (Codex's full taxonomy)

@dataclass
class FailureRecord:
    failure_class: FailureClass
    sub_class: str | None
    gate: str
    severity: str  # "TERMINAL" | "HARD" | "WARN"
    recovery_action: str  # "none" | "atomic_fix" | "writer_correct" | "reviewer_fix"
    evidence: dict  # raw evidence (e.g. offending tool call entries)
    terminal: bool
```

Placed BEFORE the isolation gate implementation (Codex amendment) so the gate emits structured `failure_class` from the first commit, not stringly-typed errors that Card 2's telemetry layer would have to refactor.

### Component 5 — #1944 replay regression test

New file: `tests/test_writer_isolation.py`.

Test fixture: `audit/incidents/2026-05-13-1944-writer-tool-calls.json` (committed via #1945).

Test cases:
- `test_classify_1944_incident_as_infra_context_contamination` — load fixture, run classifier, assert `FailureClass.INFRA_CONTEXT_CONTAMINATION` returned with sub-classes including `wrong_tool_family` AND `handoff_or_orchestrator_file`.
- `test_pure_mcp_writer_passes_isolation` — synthetic fixture with only `mcp__sources__verify_word` calls passes.
- `test_mixed_writer_fails_isolation` — synthetic fixture with 1× `mcp__sources__verify_word` + 1× `Bash` fails (writer can NOT escape by mixing with valid calls).
- `test_claude_subprocess_argv_contains_allowed_tools` — argv-level assertion that `--allowedTools mcp__sources__*` is present (Codex amendment).
- `test_writer_reads_handoff_fails_isolation` — synthetic fixture with `Read` of `docs/session-state/<file>.md` fails with `handoff_or_orchestrator_file` sub-class.

### Component 6 — `curriculum-maintainer` → `curriculum-orchestrator` rename

Mechanical rename across:
- `claude_extensions/agents/curriculum-maintainer.md` → `curriculum-orchestrator.md`
- `.claude/agents/curriculum-maintainer.md` → `curriculum-orchestrator.md`
- `.codex/agents/curriculum-maintainer.{md,toml}` → `curriculum-orchestrator.{md,toml}`
- `.agent/agents/curriculum-maintainer.md` → `curriculum-orchestrator.md`
- CLAUDE.md: update `> **Default subagent**: ...curriculum-maintainer...` line to reference `curriculum-orchestrator`
- Any settings.json references (search needed)

**Bloat trim (optional, can be follow-up):** remove auto-loaded-elsewhere content from the orchestrator's agent file: behavioral rules (already in MEMORY.md), reference docs table (already in CLAUDE.md), plugins list (auto-loaded by harness), pre-submit checklist (already in AGENTS.md). Target: ~80 lines down from current ~140.

---

## What this card does NOT decide

- **Writer fix-loops** (distinct-gate iteration, atomic fixes, dev=3/rollout=5 caps) — deferred to Card 2 because the immediate need is "writer doesn't behave as orchestrator", not "writer self-corrects."
- **Full failure taxonomy** (mcp_tools_never_invoked, strict_json_parse, formatting_standards, word_count, plan_sections, vesum_unknown, russianism_detected, missing_ipa, resources_search_attempted, decolonization_flag, naturalness_flag, citation_unresolved, etc.) — Card 2.
- **Quarantine JSONL writer + schema** at `orchestration/quarantine/v7-build.jsonl` — Card 2. Tonight's terminal exit (no quarantine) is fine for the smoke build.
- **Phase-aware caps (dev=3, rollout=5)** — Card 2.
- **Tab specialization** (Option B from the discussion) — both Codex and Gemini said `[DISAGREE]` and deferred. Not in scope here.
- **Reviewer-loop** — both said no reviewer fix-loop; single pass + atomic fixes per ADR-007. Not changed.
- **A1 plan re-versions** for the NEEDS_FIX items in `#1938` summary — separate operational decision.
- **A1/my-morning Phase 5 rebuild** (per `2026-05-13-ulp-derived-student-aware-immersion.md`) — separate sequence.

## Implementation order (per convergence Q-conv-4)

| # | Component | Files touched | Estimated LOC |
|---|---|---|---|
| 1 | `curriculum-writer` agent file | `claude_extensions/agents/curriculum-writer.md` + parallel `.claude/`, `.codex/`, `.agent/` copies | ~60 |
| 2 | Spawn-layer isolation verification | inspect `linear_pipeline.py:1995-2010` + `claude.py:285-289`; ensure `--allowedTools mcp__sources__*` passthrough; add argv unit assertion | ~30 (mostly test) |
| 3 | Failure-class taxonomy skeleton | `scripts/audit/failure_classes.py` (new) | ~40 |
| 4 | `infra_context_contamination` isolation gate | extend `linear_pipeline.py` writer-phase post-condition; new function that classifies raw `writer_tool_calls.json` | ~80 |
| 5 | #1944 replay + isolation regression tests | `tests/test_writer_isolation.py` (new) | ~120 |
| 6 | `curriculum-maintainer` → `curriculum-orchestrator` rename | mechanical across `claude_extensions/`, `.claude/`, `.codex/`, `.agent/`, `CLAUDE.md`, settings | ~10 net (rename) |
| 7 | (deferred to Card 2) Quarantine JSONL writer | — | — |
| 8 | Smoke-test `a1/sounds-letters-and-hello` rebuild | manual: `v7_build a1 sounds-letters-and-hello` after PR merges; verify writer makes ≥1 MCP call, isolation gate quiet | — |
| 9 | (deferred) writer fix-loop | — | — |

Total Card 1 estimated: **~340 LOC** across ~9 files, single PR.

## Why this might be worth doing

1. **Unblocks the build queue.** #1944 is P0 BLOCKER. Until isolation lands, no V7 module can be built with claude-tools writer. Per the user's overnight Plan A: the cascade is poised to resume the moment isolation is verified.
2. **Discovered by the project's own audit framework.** `MCP_TOOLS_NEVER_INVOKED` correctly halted the build. The fix extends the same architectural pattern (post-condition gate over writer telemetry).
3. **3-way agent convergence at `[AGREE]`.** Codex independently surfaced file:line references throughout (#M-4 deterministic). Gemini independently surfaced the pedagogical-coherence argument. Claude synthesized. No irreducible disagreement after Round 2.
4. **Re-uses existing telemetry plumbing.** `emit_event()` + `--telemetry-out` at `linear_pipeline.py:1165-1196` + writer trace capture at `writer_tool_calls.json`. No new infra required for Card 1.
5. **Fixes the deeper "bloat" complaint.** User flagged `curriculum-maintainer` as bloated; the split forces a clean writer prompt (lean, single-purpose) and lets the orchestrator file be trimmed in a follow-up.
6. **Defense-in-depth.** Spawn-layer `allowed_tools` config (Codex's point 2) + agent-file capability stripping (Gemini's amendment) + runtime trace classifier (Codex's invariant). Three independent layers all catching the same violation class.

## Why this might NOT be worth doing

1. **`curriculum-maintainer` rename has ripple cost.** Every reference to it across docs / settings / scripts needs updating. Risk: missed reference leaves orphan pointer. Mitigation: ripgrep for `curriculum-maintainer` after the rename, fix any orphans.
2. **Argv-level assertion is invasive.** Testing the actual claude subprocess argv requires inspecting how `claude.py:adapter` constructs its command — adds test-time coupling to spawn internals. Mitigation: keep the assertion targeted (just check `--allowedTools` substring presence), accept the coupling for the safety it buys.
3. **Card 1 doesn't itself prove rollout-grade.** Without Card 2's failure taxonomy + quarantine + caps, Card 1 only converts #1944's failure mode from "bad content produced" to "build halts cleanly". That's a strict improvement but the queue still doesn't continue past the first contamination. Mitigation: Card 1 is the isolation hotfix; Card 2 ships the queue-continuation policy after Card 1 telemetry validates the class boundary.
4. **The `infra_context_contamination` raw-trace classifier could false-positive.** If a legitimate future writer needs `mcp__sources__search_external` (different prefix than `mcp__sources__verify_word`), the classifier's allow-pattern `mcp__sources__*` must cover all sources tools, not just verification ones. Mitigation: the allow-pattern is a glob (`mcp__sources__*`) — every sources tool starts with that prefix per the MCP server convention.
5. **Locked-plan handling not addressed.** A writer that hits `unknown_vocab` (used a word not in the plan's `vocabulary_hints.required` or learner_state's `cumulative_vocabulary`) would today HARD-fail. Card 2's recovery action for that class is "replace with cumulative vocab, atomic fix" but Card 1 doesn't enable that. Smoke build may still fail at this class; that's expected and documented for Card 2.

---

## Open questions (require user input before implementation)

1. **Rename in same PR or separate?** I lean: SAME PR for atomicity. CI runs once, all references consistent. Codex's earlier objection was about coupling architecture cards, not coupling refactor within the same architectural change.
2. **Should the `curriculum-writer` agent live ONLY in `claude_extensions/` or also in `.claude/agents/` / `.codex/agents/` / `.agent/agents/`?** Mirror `curriculum-maintainer`'s current distribution to keep symmetry.
3. **Bloat trim included in Card 1, or deferred?** I lean: SAME PR — the rename gives natural cover to also remove the "auto-loaded elsewhere" content. Saves a second pass over the same file.
4. **Argv assertion test invocation:** dry-run the actual claude CLI invocation (slow, requires CLI present), or mock at `subprocess.Popen` level (fast, fragile to adapter changes)? Lean: MOCK — Codex's intent was "catch config drift", not "verify CLI behavior."

## Implementation phases

**Phase 1 — components 1-6 above as a single PR.** Estimated 1-2 hr Codex dispatch + inline orchestrator review.

**Phase 2 — smoke build verification.** User-run `v7_build a1 sounds-letters-and-hello` (Plan A override still active for this verification). Assert: writer makes ≥1 `mcp__sources__*` call, isolation gate quiet, builds to completion OR fails on content-class HARD gate (which Card 2 handles). Expected ~15-25 min.

**Phase 3 — IF smoke passes:** resume the 7-module overnight queue via the same `/tmp/build-queue-a1-first-7.sh` wrapper (user-run). Expected ~3 hr.

**Phase 4 — IF smoke fails on a content-class gate:** that's Card 2 territory; do not improvise; surface gate name + failure to user.

## References

- `audit/incidents/2026-05-13-1944-writer-tool-calls.json` — primary diagnostic artifact (committed via #1945)
- `docs/session-state/2026-05-13-overnight-orchestration-brief.md` — full overnight context + halt diagnosis (committed via #1945)
- `scripts/build/linear_pipeline.py:182-202` — `WRITER_TOOL_NAMES` normalization set
- `scripts/build/linear_pipeline.py:1821-1832` — `writer_tool_calls` accumulation site
- `scripts/build/linear_pipeline.py:1893-1912` — existing `MCP_TOOLS_NEVER_INVOKED` gate
- `scripts/build/linear_pipeline.py:1995-2010` — claude-tools `allowed_tools` config (current, NOT enforced)
- `scripts/build/linear_pipeline.py:2938-2980` — `run_python_qg_with_corrections()` (Codex's anchor for distinct-gate iteration in Card 2)
- `scripts/agent_runtime/adapters/claude.py:285-289` — `--allowedTools` passthrough to subprocess
- `tests/test_no_rewrite_contract.py:1-12` — ADR-007 enforcement test (referenced for Card 2 invariant)
- Discussion thread: `ab channel tail v7-e2e-rollout-design-2026-05-13 --thread 88ca87e57d064c99bca196442e46f027` — full 3-way [AGREE] convergence
- Predecessor discussion thread: `ab channel tail v7-e2e-rollout-design-2026-05-13 --thread 5a36c61bf09443caa763a70c79dc7dc0` — Round 1 (codex+gemini first positions, both `[DISAGREE]` before convergence)
- #1944 GH issue — full diagnosis + recommended investigation paths
