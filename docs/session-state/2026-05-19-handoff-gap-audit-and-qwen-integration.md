---
date: 2026-05-19
session: "Documentation gap audit + V7 orchestration restoration design + Qwen-3.6 integration + multi-writer strategy (12+ hour single session)."
status: amber
main_sha: 47c09153e4
main_green: true
working_tree_dirty: true  # 7 modified files + 11 untracked — handoff documents the state, next session decides commit grouping
shipped_this_session_to_disk: ["claude_extensions/rules/pipeline.md (codex retraction)", "scripts/agent_runtime/adapters/hermes_qwen.py", "scripts/agent_runtime/{adapters/__init__.py, registry.py} (qwen wired)", "scripts/ai_agent_bridge/{_channels.py, _channels_cli.py} (qwen + cap→6)", "scripts/delegate.py (qwen agent choice)", "docs/README.md (AI-agent entry point)", "docs/archive/damage-report-*.md (8 files moved)", "audit/2026-05-18-docs-gaps-and-reorganization/REPORT.md", "docs/best-practices/agent-activity-matrix.md (v1.2 with §8 ranking-by-role + Chinese-models)"]
prs_merged_this_session: []  # all work uncommitted on main local
active_dispatches: []
---

# Handoff — Documentation gap audit + Qwen integration + multi-writer strategy

## TL;DR

12+ hour session. Started as m20 ship debug, pivoted to documentation hygiene + architecture design after the diagnostic surfaced systemic spec gaps. **No code committed yet** — 7 modified files + 11 untracked sitting on local main. Next session must decide commit grouping or roll forward.

**The one orchestrator failure pattern this session:** 4× confidently wrong by citing written context without verifying current state. Each caught by user. Most damaging: claimed codex-tools is broken (the stale `tool_calls_total=0` rule) for 3+ hours before doing the consultation that retracted it. Pattern is **trusting written knowledge that has been superseded**. Mitigation proposed: source/deploy drift CI check (locked, see §1.7 below).

## State at handoff

| Item | State |
|---|---|
| Main SHA | `47c09153e4` (unchanged from session start) |
| Working tree | DIRTY: 7 modified files, 11 untracked. Documented below. |
| Active dispatches | 0 |
| Bridge channel state | 3 channels created this session: `m20-doability-triangulation-2026-05-18`, `v7-orchestration-restore-2026-05-18`, `codex-writer-friction-2026-05-18`. All discussions done. |
| Time-pressing constraint | 2026-06-15 Claude-dispatch sunset — ~4 weeks |
| m20 ship blocker | Issue #2148 (wiki obligation emission contract) — fix shape decided, needs decision card + implementation |

## What shipped TO DISK this session (uncommitted, on local main)

### Code changes (7 modified, 1 new file)

1. **`claude_extensions/rules/pipeline.md`** — codex `tool_calls_total=0` retraction synced. Deployed to all 4 targets via `scripts/deploy_prompts.sh`.
2. **`scripts/agent_runtime/adapters/hermes_qwen.py`** — NEW. 193 LOC. Wraps `hermes -z PROMPT -m qwen/qwen3.6-plus`. Mirrors deepseek/grok pattern.
3. **`scripts/agent_runtime/adapters/__init__.py`** — exports `HermesQwenAdapter`.
4. **`scripts/agent_runtime/registry.py`** — qwen agent entry registered. Default model `qwen/qwen3.6-plus`. Cost tier "low".
5. **`scripts/ai_agent_bridge/_channels.py`** — `qwen` added to `VALID_AGENTS`.
6. **`scripts/ai_agent_bridge/_channels_cli.py`** — `discuss` cap lifted 4 → 6.
7. **`scripts/delegate.py`** — `--agent` choices include `qwen`.

End-to-end qwen smoke test passed: `delegate.py dispatch --agent qwen --task-id qwen-smoke-20260518` returned `Model qwen/qwen3.6-plus; I can see the prompt.` in 5.045s, returncode 0.

### Documentation changes

1. **`docs/README.md`** — NEW. AI-agent entry point. Includes the V5/V6 cascade-baseline note (per user correction). 80 lines.
2. **`docs/archive/damage-report-*.md`** — 8 files moved from `docs/` top-level. Untracked moves (mv only).
3. **`docs/best-practices/agent-activity-matrix.md`** — bumped to v1.2. Added §8 ranking-by-role with quality+cost view. Added §8.10 Chinese-models section. Qwen-3.6 added to §2 roster. Codex retraction synced in §4.1.
4. **`audit/2026-05-18-docs-gaps-and-reorganization/REPORT.md`** — NEW. 12 KB structured gap audit + reorganization plan.

### Untracked files NOT mine

- `docs/dispatch-briefs/2026-05-18-bulk-ocr-repetition-hallucination-filter.md` — another agent's WIP
- `transcription.txt` — 145 KB ESUM dump at repo root, owner unknown, flagged but untouched

## Architecture decisions LOCKED this session

### V7 orchestration folder preservation (full plan)

**Path:** `curriculum/l2-uk-en/_orchestration/{level}/{slug}/runs/{stamp}/` (underscore prefix to keep out of `mcp__sources__*` retrieval namespace, per claude headless's Q5).

**Build flow:**
- Build runs in worktree (`.worktrees/builds/...`) — branch isolation preserved
- Wrapper (in main project dir, on main branch) copies orchestration dir from worktree to main on phase boundary + on terminal outcome
- Always merge to main (no preserved branches that accumulate over time)
- One commit per build (success OR failure)
- Worktree reaped on completion; branch dies with it

**Cleanup:** last N=10 runs per slug; older runs squashed/deleted via scheduled cron (defer details to month 3).

**state.json schema (V7):**
```json
{
  "mode": "v7",
  "track": "a1",
  "slug": "my-morning",
  "run_id": "20260519-HHMMSS",
  "parent_run_id": null | "<prior-run-id>",
  "started_at": "...",
  "finished_at": "...",
  "status": "complete | failed | partial",
  "failed_phase": "<phase>" | null,
  "failure_class": "<FailureClass enum>" | null,
  "agent": "claude-tools | codex-tools | gemini-tools | deepseek-tools | qwen-tools",
  "model": "<model id>",
  "effort": "low | medium | high | xhigh | max | unknown",
  "prompt_sha": "<sha of writer prompt template>",
  "phases": { ... per-phase status + timestamps + attempts ... }
}
```

**File naming convention:** hyphenated to avoid `.gitignore` collision (e.g., `v7-writer-prompt.md`, not `writer_prompt.md` — `*_PROMPT.md` is gitignored per codex's catch).

**MDX-on-failure:** ALWAYS assemble the MDX, regardless of gate pass/fail. Success → `starlight/src/content/docs/{level}/{slug}.mdx`. Failure → `_orchestration/.../runs/{stamp}/{slug}.mdx` with frontmatter `build_status: failed` + `failed_phase: <phase>`. NEVER modify the source `module.md` frontmatter (codex's argument: gate-consumed, parser risk).

**Auto-generated:** `commit_diff_summary.json` per build summarizing changes from `parent_run_id`. `git diff --stat` parsing, ~30 LOC.

**Correction iterations preserved:** `python_qg_correction_r{N}.json`, `wiki_coverage_correction_r{N}.json`. Currently swallowed; this is the actual prompt-engineering blind spot.

**Per-dim reviewer prompts:** preserved as separate files, not aggregated into `llm_qg.json`.

### Multi-writer strategy

**Roster (6 agents post-qwen integration):**
- claude-tools (Opus 4.7) — current V7 writer default; **lane sunsets 2026-06-15**
- codex-tools (gpt-5.5) — tool wiring CONFIRMED (11 MCP calls in fair retest); A1 register gap real
- gemini-tools (3.1-pro-preview) — primary for wiki; needs V7 module-writer re-bakeoff
- deepseek-tools — **NOT YET WIRED AS V7 WRITER** (only as reviewer); adapter exists; ~half-day Codex work to wire
- qwen-tools (3.6-plus default; 3.6-flash, 3.6-max-preview, 3.6-35b-a3b:thinking variants) — wired today; untested in any role
- grok-tools (4.3) — known weak as writer (#2039 token truncation)

**Strategy direction (user-corrected mid-session):**
- **Skip A1 entirely → REVERSED.** Finish A1 m20 first; slowly build A1 thereafter.
- A1 is the PRECISION test ("how precisely they follow the prompt"). Don't skip it for Chinese-model bakeoff.
- Parallel work: L2-uk-en B1+/seminars + L2-uk-direct + Kimi excluded
- DeepSeek-v4-pro as V7 writer is high priority (cheap + already-validated quality elsewhere)

**Immersion note (corrected by user):** flat-% immersion DROPPED. Student-aware ULP-derived model is LIVE (`USE_ULP_IMMERSION_DERIVATION=True` in `scripts/config.py:145`). `compute_immersion_band(track, module_num, learner_state)` derives bands from cumulative vocabulary. north-star.md still says "B1+ is 100% Ukrainian" which is the OLD model — north-star.md is stale.

### Bakeoff plan for next session

**Sequence:**
1. **Wire deepseek-tools as V7 writer** (~half-day Codex dispatch, ~$3-5 codex tokens)
2. **A1 m20 multi-writer bakeoff** — 6 writers same prompt same module, deterministic prompt-fidelity scoring
3. **Analyze + update matrix v1.3** with empirical data

**Cost reality check:** Earlier session estimates ($20-50 per round) were 5-10× too high. Actual:
- A1 m20 6-writer bakeoff: ~$6-15 total
- Plus DeepSeek wiring dispatch: ~$3-5
- **Total to answer "which writer for A1, including Chinese models" empirically: ~$10-20**

**Prompt-fidelity rubric (deterministic, no LLM judge):**
- Word count within ±50 of target
- All 4 sections in band
- Lands within derived immersion band (`compute_immersion_band()`)
- ≥4 MCP tool calls
- VESUM 100% (no invented forms)
- `unknown_vocabulary` gate: 0 violations
- `<!-- bad -->` marker discipline: 100%
- Implementation map completeness: 100%

## Gap audit interview results (10 gaps, all answered)

| Gap | Decision | Cascade-check note |
|---|---|---|
| §1.1 V7 orchestration folder | Plan locked (above). Write `docs/best-practices/pipeline/v7-build-preservation.md` | V6 had implementation pattern (2781 lines in `_archive/`) but never specced |
| §1.2 Bakeoff methodology | V7-delta doc inheriting from April 2026-04-22 baseline | ✓ Cascaded |
| §1.3 Per-level immersion | north-star.md update needed (ULP card supersedes) | User-corrected mid-session |
| §1.4 #2148 contract fix shape | Write decision card NOW (DRAFT). Three options on the table (α/β/γ); recommend γ (render existing `seed_implementation_map`) | V7-era, no V5/V6 cascade |
| §1.5 Deterministic-first iteration | **NOT a from-scratch decision card.** SYNTHESIS DOC pointing at ADR-001 §3 + ADR-007 + `2026-04-28-targeted-gate-correction-paths.md` + `2026-05-17-path3-per-obligation-review-loop.md` | **Cascade found 2026-05-19** — my original framing was wrong |
| §1.6 Codex retraction in pipeline rule | DONE 2026-05-18 | n/a |
| §1.7 Source/deploy drift detection | CI check that detects rule-citing-superseded-decision (stronger variant — parses decision-card status field) | V7-era, no V5/V6 cascade |
| §1.8 V7 phase architecture | Write `docs/architecture/v7-pipeline.md` documenting V6→V7 deltas; ARCHITECTURE.md stays as cascade baseline | V6 phase list at ADR-001 (17 phases); V7 at v7_build.py (8 phases). **V6→V7 rationale (why we dropped skeleton, chunked write, etc.) is undocumented** |
| §1.9 Claude dispatch sunset plan | Write `docs/plans/2026-06-15-claude-dispatch-sunset.md` now | V7-era, ~4 weeks pressing |
| §1.10 Multi-track writer routing | Add per-bucket sections to matrix §8 ("pending bakeoff" labels) | **Not yet verified** — `track-architecture.md` + `ROADMAP-two-track-build-plan.md` may have partial cascade; needs ~5 min read |

## Article applicability (Claude Code best-practices)

From `https://claude.com/blog/how-claude-code-works-in-large-codebases-best-practices-and-where-to-start`:

**3 patterns directly apply:**

1. **Hierarchical CLAUDE.md** — split current single 322-line root file into root + subdirectory files. Candidates: `scripts/build/CLAUDE.md` (V7 pipeline), `curriculum/l2-uk-en/CLAUDE.md` (content), `docs/CLAUDE.md` (docs).
2. **Repo-root README.md as TOC** — we made `docs/README.md` but article suggests one at repo root too, listing top-level folders one-line each. Helps fresh sub-agents that don't load CLAUDE.md.
3. **Stop hook proposing CLAUDE.md/MEMORY updates** — would have caught my "codex tool_calls_total=0 still stale" failure by flagging contradicted-claims from the session.

**Anti-pattern flagged:** "Using CLAUDE.md for reusable expertise that belongs in a skill." Some MEMORY.md rules might be better as skills. Audit candidate (not urgent).

## Open items NOT shipped this session

| Item | Effort | Why deferred |
|---|---|---|
| Verify §1.10 cascade (`track-architecture.md` + `ROADMAP`) | 5 min read | User chose handoff over verifying |
| Reframe §1.5 as synthesis doc (not from-scratch card) | 30 min write | Same |
| Write 5 documentation deliverables (orchestration spec, bakeoff methodology, contract DRAFT, deterministic synthesis, v7-pipeline.md, claude-sunset plan) | ~2-4 hr or dispatch to codex | Next session |
| Wire deepseek-v4-pro as V7 writer | ~half-day Codex dispatch | Next session |
| A1 m20 multi-writer bakeoff (6 writers) | ~30-45 min wall-clock, ~$6-15 | Next session |
| Decide commit grouping for the 7 modified + 11 untracked files | ~15 min | Next session |
| Update north-star.md (B1+ immersion → ULP-derived language) | ~10 min | Next session |
| Address `transcription.txt` at repo root (145 KB, untracked, owner unknown) | n/a | Flag, ask user |

## What the next session should do FIRST

**Cold-start sequence:**

1. Read this handoff doc verbatim
2. `curl -s http://localhost:8765/api/orient` — check live state
3. `git status --short` — verify the 7 modified + 11 untracked still match what's documented here
4. Read the failed §1.10 cascade items: `docs/best-practices/track-architecture.md` + `docs/architecture/ROADMAP-two-track-build-plan.md`
5. Decide commit grouping for this session's changes (suggested: 4-5 logical commits — qwen-integration, doc-readme, codex-rule-sync, matrix-v1.2, damage-archive-move)
6. Then start the bakeoff prep work OR the doc-writing pipeline

**Priorities (user-locked sequence):**

1. Commit this session's work (cleanup)
2. Verify §1.10 cascade
3. Reframe §1.5 as synthesis doc
4. Write the 5 deliverable docs (or dispatch to codex)
5. Wire deepseek-tools as V7 writer
6. A1 m20 6-writer bakeoff
7. Update north-star.md with ULP-derived language
8. Then back to m20 ship work (the #2148 implementation)

## Critical findings / corrections to stale beliefs

**Logged so the next session doesn't trip on them:**

1. **Codex-tools is NOT broken.** `tool_calls_total=0` was a measurement bug fixed in PR #1907. Codex made 11 MCP calls in fair retest. Real friction at A1 is content register (996/1200 words, 51% immersion vs 24% A1 cap before ULP — now derived).
2. **The live published `starlight/.../my-morning.mdx` is pre-V7 format.** It cannot be used as gate calibration reference (5/5 agents missed this in the doability triangulation; user caught it). The reference at `archive/experiments/reference/a1/1/` is the proper calibration target.
3. **ULP-derived student-aware immersion is LANDED + DEFAULT ON.** `USE_ULP_IMMERSION_DERIVATION=True` per `scripts/config.py:145`. The flat-% framing in `north-star.md` is stale.
4. **#2148 contract gap is the m20 ship blocker.** Three fix shapes; codex's γ (render existing `seed_implementation_map` into prompt) is the cheapest. Decision card pending.
5. **My 4× confidently-wrong pattern in this session:** cited stale written context without verifying current state. Same shape every time. Source/deploy drift CI (§1.7 locked) would catch the rule-deploy lag at least.

## Behavioral autopsy

Per `docs/bug-autopsies/`, file as `docs/bug-autopsies/2026-05-19-orchestrator-stale-context-pattern.md` next session. The pattern:

- Session begins; orchestrator loads CLAUDE.md + MEMORY + rules
- Rules cite decision cards; decision cards get revised
- Rules don't get re-deployed; orchestrator trusts the rule
- Orchestrator confidently states something the rule says
- User catches the contradiction; orchestrator looks; finds decision card has been revised
- Repeat
- **Fix:** Source/deploy drift CI + stop-hook reflection on session learnings + always grep the decision-cards directory for status:REVISED/SUPERSEDED when citing any rule.

## Provenance

- Session start: 2026-05-18 morning. Handoff written: 2026-05-19 (overnight rollover).
- Sessions referenced this turn: `docs/session-state/2026-05-18-morning-cascade-shipped-m20-arch-gap-surfaced.md` (predecessor).
- Bridge discussions consulted: `m20-doability-triangulation-2026-05-18` (5-agent, both rounds), `v7-orchestration-restore-2026-05-18` (5-agent), `codex-writer-friction-2026-05-18` (2-agent claude+codex).
- Decision cards reviewed: `2026-05-13-ulp-derived-student-aware-immersion.md`, `2026-05-06-writer-selection-codex-gpt55.md`, ADR-001, ADR-007.
- Article applied: `https://claude.com/blog/how-claude-code-works-in-large-codebases-best-practices-and-where-to-start`.
