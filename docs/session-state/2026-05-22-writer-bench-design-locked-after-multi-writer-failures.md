---
date: 2026-05-22
session: "9 PRs merged (reviewer-prompt rebuild + activities-schema fix + Word Atlas v1 + codeql + 5 dependabot/curriculum + agy-merged dependabot) but a1/my-morning still has no successful end-to-end build; writer bench design v0 locked"
status: green-pipeline-fixes-landed-but-m20-not-promoted-anchor-writer-pending
main_sha: ae317980b9
main_green: clean (review/review advisory persists — needs GEMINI_API_KEY in repo secrets per Claude dispatch findings)
working_tree_dirty: pre-existing carry-overs + new untracked dispatch briefs
prs_merged_this_session:
  - "#2215 feat(reviewer-prompt): mirror V7 writer audit contracts (Codex output + orchestrator LEARNER_STATE/IMMERSION_RULE wiring fix)"
  - "#2218 fix(activities_schema): make `id` optional to align with V7 INLINE/WORKBOOK split"
  - "#2217 feat(lexicon): v1 scaffold — per-lemma route + A-Я hub for 63 A1 lemmas (Word Atlas)"
  - "#2168 fix(curriculum): backfill seminar references[].title (Claude fix for Curriculum Plans CI red)"
  - "#2216 chore(dependabot): cooldown blocks to silence zizmor #209-#211"
  - "#2189 deps: click 8.3.1 → 8.4.0"
  - "#2188 deps: flask 3.1.2 → 3.1.3"
  - "#2190 deps: accelerate 1.12.0 → 1.13.0"
  - "#2191 deps: astro 6.3.1 → 6.3.3 (starlight)"
  # Earlier in session, Agy merged: #2139 virtualenv, #2192 actions/setup-node, #2142 onnxruntime
prs_wip_unmerged:
  - "#2219 fix(starlight): migrate sidebar config to 0.39.2 union-schema (supersedes #1873) — CONFLICTING/DIRTY after #2191 astro bump, needs rebase"
active_dispatches: []
active_builds: []
builds_completed_this_session:
  - "a1/my-morning-20260522-155019 with claude-tools: writer phase ✓; activities.yaml schema FAILED → unblocked by #2218"
  - "a1/my-morning-20260522-162051 with claude-tools (post #2218): writer crashed silently mid-stream (transient, returncode=1, no telemetry); retry succeeded writer phase but python_qg failed 3 gates"
  - "a1/my-morning-20260522-162855 with claude-tools (retry of above): python_qg FAILED — vesum_verified (1 word `йдемося`), resources_search_attempted (HARD: search_attempt_count=0, writer never called query_wikipedia/search_external), engagement_floor (1 phrase `in this section`)"
  - "a1/my-morning-20260522-181103 with codex-tools (gpt-5.5 xhigh): writer phase ✓ (4/4 CoT, 7 valid mcp__sources__* calls including search_external × 2!), BUT writer_trace_isolation gate FAILED — codex called `exec_command` 18× (Codex's general shell tool, classified as wrong_tool_family)"
headline_finding: "Codex (gpt-5.5) shows the most promising V7 writer behavior of any tested model — aggressively used the corpus (search_external, search_style_guide, query_cefr_level, search_ua_gec_errors, verify_source_attribution, check_russian_shadow), directly addressing the `resources_search_attempted` HARD gate that claude-tools never invokes. The only blocker is a CLI sandbox config issue: codex's `exec_command` shell tool must be disabled at writer invocation time so it can only call MCP tools (same sandbox model claude-tools / gemini-tools / all other writers run under). 5-10 minute fix. Once landed, codex-tools is the likely V7 writer default by margin. Writer-bench v0 design is locked (6 writers × 5 modules in 3+3 waves) but explicitly conditional on having ONE writer pass end-to-end on a1/my-morning — that's the bench's ground truth anchor. No bench dispatch until anchor is established."
next_session_first_item: "1) Rebase + merge #2219 (starlight 0.39.2 migration) since #2191 astro bump landed and resolves the package.json overlap. 2) Fix codex-tools sandbox in v7_build.py → scripts/agent_runtime/adapters/codex.py to pass --sandbox read-only OR explicit tool-disable for `exec_command`. 3) Re-fire `a1/my-morning --writer codex-tools --model gpt-5.5 --effort xhigh --worktree` — expected outcome: full pipeline pass since codex already hit search_external organically. 4) If passing: this is the bench ANCHOR. Implement `scripts/bench/writer_matrix.py` (≤250 LOC) + HTML report renderer per design captured in this handoff. 5) Fire bench overnight: 6 writers × 5 modules in 3+3 waves."
---

# 2026-05-22 writer-bench design locked after multi-writer m20 failures

## TL;DR — what changed in this session

| # | Action | State |
|---|---|---|
| 1 | PR #2215 reviewer-prompt rebuild (LEARNER_STATE wiring) | merged `589cefe74b` |
| 2 | PR #2218 activities_schema id-optional | merged `fb9d1b811b` |
| 3 | PR #2217 Lexicon v1 scaffold (63 lemmas, A-Я hub, `/lexicon/`) | merged `08f52c11f2` |
| 4 | Claude dispatch `codeql-security-prs-2026-05-23` outcome | DONE → 5 PRs (#2216, #2168 fix-pushed, #2188/#2189/#2190/#2191 ready) + #2219 starlight migration opened + #2220 broken amelina plan filed |
| 5 | Manual merges of 6 ready PRs (#2168, #2216, #2188, #2189, #2190, #2191) | all merged |
| 6 | a1/my-morning refire attempts: claude-tools, codex-tools | neither completes end-to-end yet — diagnosed (see §3) |
| 7 | Writer-bench v0 design locked | NOT YET dispatched (waiting on anchor) |

## Section 1 — Why a1/my-morning still isn't promoted

Three different runs, three different failure modes — each is informative:

### 1.1 claude-tools (post #2218 schema fix)
- Writer phase: ✓ (4/4 sections, full CoT, 19 tool calls, end_gate fired, 0 tool theatre)
- python_qg: ✗ 3 gates fail
  - **`vesum_verified`**: 1 unverified form `йдемося` (invented 1pl reflexive of "go"; valid form is `йдемо` non-reflexive)
  - **`resources_search_attempted`**: HARD — `search_attempt_count=0`. Writer called `search_text` (textbook) but never `query_wikipedia` / `search_external`. The new corpus matrix in linear-write.md surfaces the 8 external collections + Wikipedia but doesn't make the call a hard obligation; claude interprets textbook-only as sufficient.
  - **`engagement_floor`**: 1 meta-narration phrase `"in this section"` (persona break)

### 1.2 codex-tools (gpt-5.5, xhigh)
- Writer phase: ✓ (4/4 sections, full CoT, 7 tool calls + 18 `exec_command` calls)
- python_qg: NEVER REACHED — writer_trace_isolation gate fires first
- **Failure**: `WRITER_RUNTIME_GATE_FAILED: infra_context_contamination:wrong_tool_family` — codex called its built-in shell tool 18×
- **CRITICAL POSITIVE**: codex *did* invoke `search_external` × 2 — the exact MCP tool claude-tools doesn't use — plus search_style_guide, query_cefr_level, search_ua_gec_errors, verify_source_attribution, check_russian_shadow, get_chunk_context. Wide, aggressive corpus use. The codex sandbox just needs `exec_command` disabled at CLI invocation time (the equivalent of preventing claude from using Bash mid-write).

### 1.3 gemini-tools — not retried this session
Last known passing: 2026-05-21 night handoff captured a successful gemini-tools writer run with `update_topic` allowlisted. Worth re-verifying as a fallback anchor candidate if codex sandbox fix takes longer than 30 minutes.

## Section 2 — Writer-bench v0 (DESIGN LOCKED, not yet dispatched)

### 2.1 Prerequisite
**One writer must clear all `python_qg` gates on `a1/my-morning` BEFORE the bench fires.** Without an anchor, every cell scores low and we learn nothing about prompt-adherence variance between writers. With an anchor, we measure how reproducible the pass is across writers.

Most likely path to anchor: **codex sandbox fix → re-fire codex-tools** (5-10 min for the fix + 15-20 min for the build). If codex fails for non-sandbox reasons, fall back to gemini-tools.

### 2.2 Lane shape — runs in `learn-ukrainian`, NOT kubedojo

Decision: keep the bench in this repo. We already have:
- `v7_build.py` as the runner
- `python_qg.json` as the deterministic judge output
- per-writer adapters in `scripts/agent_runtime/adapters/{claude,codex,gemini,deepseek,qwen,agy}.py`

No need for kubedojo's lane-runner abstraction — that's built for many-LLM-across-many-tasks; we have one task. ~250 LOC for the bench script + HTML report. Optional future: export JSONL to feed kubedojo's report renderer.

### 2.3 Locked matrix (6 writers × 5 modules = 30 cells)

| Writer | --writer | --model | --effort | Adapter status |
|---|---|---|---|---|
| Claude | `claude-tools` | `claude-sonnet-4-6` | `high` (NOT opus — opus is current default; sonnet is a faster comparison) | known working |
| Gemini | `gemini-tools` | `gemini-3.1-pro-preview` | `high` (if adapter respects) | known working 2026-05-21 |
| Codex | `codex-tools` | `gpt-5.5` | `xhigh` | NEEDS sandbox fix first |
| DeepSeek | `deepseek-tools` | `deepseek-v4-pro` | default | untested in V7 |
| Qwen | `qwen-tools` | `qwen3.6-plus` | default | untested in V7 |
| Agy | `agy-tools` | `gemini-3.5-flash-high` | default | untested in V7 |

**Module set (5 cells × 6 writers = 30 builds):**
1. `a1/sounds-letters-and-hello` (m1, letter-module)
2. `a1/things-have-gender` (m08, grammar)
3. `a1/my-morning` (m20, milestone — anchor)
4. `a2/checkpoint-first-contact` (A2 entry checkpoint)
5. `a2/at-the-cafe` (A2 functional)

### 2.4 Execution policy
- **Sequential execution — NO fanout.** User correction 2026-05-22: the MCP sources server at port 8766 doesn't support concurrent writer clients today (Python-wrapper-level serialization, not a SQLite FTS5 limit). 30 cells × ~10-15 min/cell = **~5-7.5 hours wall-clock overnight**. Per #M-9 anyway (laptop crash protection). Wave-based fanout reconsidered briefly but ruled out — the right fix is multi-instance MCP servers (lighter than Qdrant migration), both out of scope for v0 bench.
- **Support budget per writer: 30 min max** to reach `python_qg`. If a writer can't be brought to QG within that window (config / tool-family / adapter bug), record `phase_reached=writer_trace_isolation` (or whatever) as the bench result. Don't sink hours per writer in v0.
- **N=1 single-shot per cell** — no variance measurement in v0. Escalate to N=3 only on cells too close to call.
- **Effort: each writer's V7 default** — no override. Bench measures production behavior, not theoretical ceiling.
- **Order: outer loop modules, inner loop writers** — so each module gets all 6 writers attempted in sequence before moving to the next module. Reason: a flaky writer poisoning ALL its later cells (its retry needs cooldown) hurts less than ALL 6 writers' first cell being on the same module.

### 2.5 Per-cell record schema
```json
{
  "writer": "codex-tools",
  "model": "gpt-5.5",
  "effort": "xhigh",
  "level": "a1",
  "slug": "my-morning",
  "wall_clock_s": 423.5,
  "phase_reached": "python_qg",
  "writer_passed": true,
  "python_qg_passed": false,
  "gates_passed": ["activity_schema", "word_count", ...],
  "gates_failed": ["resources_search_attempted"],
  "failure_class": "python_qg_fail",
  "failure_detail": {"resources_search_attempted": {"search_attempt_count": 0, ...}}
}
```

HTML report: rows=writers, cols=modules, cells=color-coded gate-pass-count + composite, drill-down to per-gate detail.

## Section 3 — Codex sandbox fix (the unblock)

Quick investigation:

```
$ grep -rn "exec_command\|sandbox" scripts/agent_runtime/adapters/codex.py | head -10
$ codex --help 2>&1 | grep -E "sandbox|tools"
```

Likely fix is a single flag at the codex CLI invocation. The gate's design intent (linear_pipeline.py:285-303) is clear: writers can only use `mcp__sources__*` + harmless annotation tools. `exec_command` is exec-capable and intentionally NOT in the allowlist. The fix is in the codex adapter to invoke codex with `--sandbox read-only` (or equivalent flag) so `exec_command` isn't surfaced to the writer.

If a sandbox flag isn't sufficient: explicit `--disable-tool exec_command` if codex CLI supports it. If neither: fall back to gemini-tools as the anchor.

## Section 4 — Other landed work + follow-ups from Claude dispatch

### Landed via Claude dispatch
- **#2216** CodeQL `dependabot-cooldown` #209-#211 closed — added 7-day cooldown blocks to `.github/dependabot.yml`
- **#2168** seminar references[].title backfill — fix for `Curriculum Plans` CI red
- **#2219** starlight 0.39.2 sidebar-schema migration — supersedes #1873 — **CONFLICTING/DIRTY after #2191; needs rebase next session**
- **5 dependabot PRs unblocked** by orchestrator merges (#2188 flask, #2189 click, #2190 accelerate, #2191 astro)

### Filed by Claude dispatch — open follow-ups
- **Issue #2220** — broken plan `amelina-women-looking-at-war.yaml` (missing `module/title/objectives/version`). Pre-existing latent issue from `1d10dc6a0b`, exposed by the #2168 backfill. Plan needs scaffolding before any build of that slug.
- **CI infra red** — every PR shows `review / review` failure (missing `GEMINI_API_KEY` or `GOOGLE_GENAI_USE_VERTEXAI`/`GOOGLE_GENAI_USE_GCA` in repo secrets). Advisory check; not blocking. Worth a follow-up issue if not already filed.

## Section 5 — Word Atlas (Лексикон) v1 LIVE on main

`/lexicon/` + `/lexicon/<lemma>/` pages now ship on main:
- 63 lemmas across `a1/my-morning` (built) + `a1/sounds-letters-and-hello` (plan-only) + `a1/things-have-gender` (plan-only)
- A-Я alphabetical hub with letter-jump nav
- §1 Шапка + §12 Курсові посилання rendered; §2-§11 + §13-§15 stubbed per design §4
- Sidebar nav entry "Лексикон (Word Atlas)" parallel to A1-C2/seminars

**Follow-up (F8): v1.1 VESUM enrichment** — populate POS/gender/stress/paradigm in the manifest by joining against `data/vesum.db` at build time. Optional gates: `provenance_per_section`, `lemma_in_vesum`. Lives behind the existing route.

## Section 6 — Active state at handoff

- **Active dispatches**: 0
- **Active builds**: 0 (last attempt: a1/my-morning-20260522-181103 codex-tools → writer_trace_isolation FAIL)
- **Open PRs**: 1 (#2219 starlight migration — needs rebase)
- **Origin/main**: `ae317980b9` — clean, ahead-of-local=0 after pull
- **Build worktrees preserved per #M-10**: all a1-my-morning timestamps still intact
- **Starlight dev server**: up at http://localhost:4321 — now serves `/lexicon/` pages
- **Monitor API**: up at localhost:8765
- **Sources MCP**: up at localhost:8766
- **Kubedojo bench server**: up at http://127.0.0.1:8768 (content-writing-long English-only bench — informative but not equivalent to UA prompt-adherence; that's the proposed v0 bench)
- **Inbox**: empty
- **MEMORY.md**: 143/150 lines (approaching budget; do not add entries this session unless critical)

## Section 7 — How next-session orchestrator should open

1. Read this handoff (you're doing it now)
2. Verify state: `git log --oneline -5 origin/main` shows `ae317980b9` on top
3. Poll any leftover dispatches: `/api/delegate/active` — should be empty
4. **First merge**: rebase #2219 against main (after #2191 astro bump), then merge. Closes #1873.
5. **Then unblock codex**: read `scripts/agent_runtime/adapters/codex.py` to find where the Codex CLI is invoked. Add `--sandbox read-only` or equivalent flag to suppress `exec_command`. Test with a quick `a1/my-morning` refire — expected PASS based on this session's evidence.
6. **If codex passes**: that's the bench anchor. Implement `scripts/bench/writer_matrix.py` per Section 2 design. Fire the 6×5 matrix in 3+3 waves overnight.
7. **If codex fails for non-sandbox reasons**: refire `a1/my-morning --writer gemini-tools` to re-establish gemini as anchor (last known passing 2026-05-21).
8. **Do NOT promote any module** until visual MDX verification against `docs/poc/poc-lesson-design.html` passes — that's the #M-11 SSOT discipline that prevented the 2026-05-23 m20 mis-promote.

## Section 8 — Open follow-ups (cumulative across sessions)

| # | Item | Priority | Notes |
|---|---|---|---|
| F1 | Rebase + merge #2219 starlight 0.39.2 migration | **P0** | Resolves #1873 via supersession |
| F2 | Codex sandbox fix (`exec_command` disable) | **P0** | 5-10 min, unblocks bench anchor + V7 codex default |
| F3 | Establish bench anchor — one writer clearing all gates on a1/my-morning | **P0** | Codex (post F2) or gemini-tools fallback |
| F4 | Implement `scripts/bench/writer_matrix.py` + HTML report | **P0** | After F3 succeeds; ~250 LOC, design in §2 |
| F5 | Fire writer-bench v0 (6 × 5, 3+3 waves) overnight | **P0** | After F4 lands |
| F6 | Issue #2220 — scaffold `amelina-women-looking-at-war.yaml` plan | P2 | Per Claude dispatch report; blocks any LIT seminar build of that slug |
| F7 | File `review / review` CI infra issue (missing GEMINI_API_KEY) | P3 | Cosmetic — only `review/review` advisory affected, no blocking impact |
| F8 | Word Atlas v1.1 — VESUM enrichment (POS/gender/stress/paradigm) | P2 | Compounds writer-prompt simplification per design §7 |
| F9 | Curated literary filter layer (`tag:a1-curated`) on `search_literary` | P1 | A1/A2 advisory; mentioned in prior handoff |
| F10 | Ingest peer-reviewed UA academic scholarship | P2 | C1+ + all seminar builds |
| F11 | Ingest Ruthenian Baroque corpus | P2 | All seminar builds |
| F12 | Ingest OES manuscripts | P2 | All seminar builds |
| F13 | Ingest decolonization corpus (Plokhy, Snyder, Magocsi, Subtelny) | P2 | All seminar builds |
| F14 | Reviewer-prompt rebuild dispatch — mirror per-level matrix on audit side | P1 | Quality bar for any rebuilt module |
| F15 | Plan-allocation review — verify A1 m1-m19 plans collectively teach enough vocab to land m20 in a later band than `a1-m07-14` | P3 | Quality refinement |
| F16 | Kubedojo lane for UA prompt-adherence (if learn-ukrainian v0 bench shows signal) | P3 | After F5 results inform |
| F17 | Repo-wide plan-schema sweep (catch other broken plans like amelina) | P2 | Per Claude dispatch report §5 |

## Section 9 — User's exact words this session (for context preservation)

1. *"please tell agy to handle the dependabot prs"* → Agy dispatched, 3 merged + 4 pinged-for-rebase + 1 escalated (#1873 → led to #2219)
2. *"please assign a claude agent to handle codeql error and the security issues, and the prs which are awaiting"* → Claude dispatch `codeql-security-prs-2026-05-23`, completed at 16:37, opened 2 PRs + fixed 1 + filed 1 issue + cleared 4 dependabot
3. *"i would like to try agy-tools, eith gemini 3.5 flash high or gemini-too.ts with geminie 3.1 pro. what is your take about this ? we have this benchamrk about content writing but now about following our prompt maybe we should do a benchmark like this in the kubedojo project"* → led to bench design discussion
4. *"but listen that is english long text"* → correctly flagged that kubedojo's content-writing-long is English; UA prompt-adherence is a different skill
5. *"what if we try gpt-5.5 ?"* → fired codex-tools (gpt-5.5 xhigh) build → exec_command sandbox issue surfaced
6. *"so either you implement it or you write a prompt and design doc for kubedojo agent. but how will it be successfull ? we still cannot make successfull build here ?"* → led to "no bench dispatch until anchor" discipline
7. *"i am ok with waves. lets do a session handoff"* → this handoff
8. **Locked bench writers**: *"sonnet 4.6 high for claude, gemini 3.1.pro high, gpt-5.5 xhigh, deepseek v4 pro, qwen 3.6 plus, agy gemini 3.5-flash high"* → encoded as Section 2.3 locked matrix
