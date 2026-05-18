# Agent activity matrix

> **Status:** v1.2 — updated 2026-05-18 by orchestrator (Claude). Evidence index at `audit/INDEX-bakeoff-evidence.md`. **v1.2 adds §8 quality-vs-cost ranking view + Qwen-3.6 integration + codex retraction sync.** See §10 Provenance for version history.
> **Purpose:** one canonical place where a task type maps to *primary agent* + *runner-ups* + *eval metric* + *last verified* + *known weakness* + *known strength*. Replaces gut-routing.
> **Audience:** dual — agents read the JSON projection at `/api/activity-matrix` (future endpoint), humans read this markdown.
> **Cadence:** every cell has a `last_verified` date. If older than 30 days, the cell is stale and a re-bakeoff should be scheduled before relying on it.

---

## 1. How to read this matrix

A task type has ONE **primary** agent (the default route) and zero-or-more **runner-ups** (acceptable fallbacks documented for load-balancing, cost shifts, or when primary is unavailable). Runner-ups are listed in score order, NOT alphabetic.

Each cell carries:
- **Score** — last bakeoff result (specific metric, not a vibe).
- **Last verified** — date of the bakeoff that produced the score.
- **Evidence** — relative path into `audit/` or `docs/decisions/`.
- **Known weakness** — failure mode we've observed.
- **Known strength** — what they do uniquely well.

**Best ≠ primary.** Best = highest eval score. Primary = best after factoring quota, cost, latency, and parallel-load. Example: Opus 4.7 might be the *best* adversarial reviewer, but Codex is *primary* for routine reviews because the $200/mo Claude programmatic pool (post-2026-06-15) is reserved for the user's own cold-start sessions, not orchestrator dispatch.

---

## 2. Agent roster

| Agent | Sub-models in use | Auth lane | Cost lane | Status |
|---|---|---|---|---|
| **Claude** | Opus 4.7 (orchestrator inline + headless dispatch + Q&A); Sonnet 4.7 (mid-tier headless); Haiku (cheap Explore subagent grep/read) | Anthropic API (interactive, weekly cap $690 — doubled until mid-July 2026 promo); $200/mo agentic pool launches 2026-06-15 (RESERVED for user cold-start, NOT orchestrator) | Interactive cap shared with user sessions | **Pre-June-15: full dispatch.** Post-June-15: NO `delegate.py --agent claude`; inline-via-curriculum-writer subagent only. |
| **Codex** | gpt-5.5 (default); older versions deprecated | OpenAI via Codex CLI (codex-cli 0.130.0) | $1000/wk; current burn 0% | Primary novel-impl & mechanical-with-design-judgment dispatch lane |
| **Gemini** | gemini-3.0-flash-preview (routine, fast); gemini-3.1-pro-preview (deep) | Google AI Studio via gemini-cli 0.42.0 | $500/wk; current burn 0%; UNMETERED for routine | Default for routine: ingestion runs, fixtures, docs-near-code, tests/migrations |
| **DeepSeek** | deepseek-v4-pro (load-bearing content review w/ VESUM); deepseek-v4-flash (cheap PR code review) | Hermes adapter (deepseek 0.13.0) | Cheap; routing budget not currently capped | Primary code review + content review (with sources MCP) |
| **Grok** | grok-4.3 via Hermes (one-shot text only) | Hermes adapter (xai-oauth) | Cheap | Discuss-only — no file-edit capability yet (#2072) |
| **Qwen** | qwen/qwen3.6-plus (default); qwen/qwen3.6-flash (cheap); qwen/qwen3.6-max-preview (top tier); qwen/qwen3.6-35b-a3b:thinking (reasoning-augmented) | Hermes adapter via OpenRouter (`provider: openrouter`, base `https://openrouter.ai/api/v1`) | Cheap (OpenRouter routing) | **NEWLY WIRED 2026-05-18 — no role bakeoff yet.** Smoke-test passed (5s, returncode 0). Available for content/review/Q&A bakeoffs starting this session. Kimi explicitly deferred per user direction. |

**Sub-agents (children of the orchestrator session, not separate dispatches):**
- `Explore` (Haiku) — grep/file-read across the codebase.
- `Plan` — architectural plan drafting.
- `curriculum-writer` (Opus, single-module Ukrainian content writing) — proxy for V7 writer when claude-tools is unavailable post-June-15.
- `curriculum-orchestrator` (Opus) — full-tool orchestration sub-session.
- `general-purpose` — catch-all.

---

## 3. Task type taxonomy

Eleven canonical task types map onto the agent roster. Sub-rows are noted where the eval data differs (e.g. writing vs reviewing inside V7).

| # | Task type | Description |
|---|---|---|
| 1 | V7 module writing | Generate one curriculum/l2-uk-en/{level}/{slug}/ module per invocation. Loads writer prompt + plan + RAG context; emits module.md + activities.yaml + vocabulary.yaml + resources.yaml. |
| 2 | V7 module reviewing (per-dim) | LLM quality-gate per dimension. Cross-agent (writer ≠ reviewer). |
| 3 | Wiki article writing | Ukrainian wiki entries for the curriculum's reference corpus. |
| 4 | Adversarial review of design / ADR | Read-mostly review of a proposed architecture or decision card. |
| 5 | Code dispatch — mechanical refactor | Mass pattern application across files; clear before/after. |
| 6 | Code dispatch — novel implementation | New feature requiring design judgment within a clearly-scoped brief. |
| 7 | Code review (PR diff) | Read the diff, surface bugs/regressions/edge cases. |
| 8 | Content review (with VESUM verification) | Reviews module artifacts using `mcp__sources__*` tools to ground claims. |
| 9 | Q&A / single-shot consult | One-round question; no commit, no file edit. |
| 10 | Search / grep / locate | Find a symbol, pattern, or file across the codebase. |
| 11 | UI/browser testing | Drive `mcp__claude-in-chrome__*` against the live UI. |

---

## 4. The matrix proper

### 4.1 V7 module writing

| Slot | Agent | Score | Last verified | Evidence | Notes |
|---|---|---|---|---|---|
| **Primary** | Claude (claude-tools) | 4 MCP tool calls, vesum_verified=true (159/159), 1224-word module produced | 2026-05-12 | `audit/bakeoff-2026-05-12-night/REPORT.md` | "Default V7 writer until next bakeoff signal indicates otherwise" per decision card. |
| Runner-up 1 | Codex (codex-tools) | **11 MCP tool calls in fair retest** (2026-05-13); content-register gap at A1: 996/1200 words, 51.77% immersion vs 24% A1 cap, truncation artifacts | 2026-05-13 (post-PR-#1907) | `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md:120-141` | **2026-05-12 night `tool_calls_total=0` verdict RETRACTED** — was a rollout-matcher bug in `scripts/agent_runtime/adapters/codex.py::_rollout_matches_plan`, fixed PR #1907. Real codex friction at A1 is **content register**, not tool wiring. At B1+ (immersion inverts) codex's high-Ukrainian tendency may become a feature. |
| Runner-up 2 | Gemini (gemini-tools) | subprocess crash before writer phase | 2026-05-06 | `audit/bakeoff-2026-05-05/REPORT.md` | Adapter instability (#1708 writer subprocess timeout). Not a content-quality failure; infra. Re-bakeoff needed. |
| Open | Grok (grok-tools) | ~52% of word count target + token truncation | 2026-05-16 | issue #2039 | Grok lane was bounded probe; not ready to compete on writer. |
| Open | DeepSeek (deepseek-tools) | **not yet wired as V7 writer** (only as reviewer) — adapter exists PR #2107, write-mode validated PR #2112 | n/a | n/a | Highest leverage cost play if it passes quality. ~10× cheaper than Opus. Needs V7 writer wiring (~half-day) + bakeoff. |
| Open | Qwen (qwen-tools) | **just integrated 2026-05-18; smoke-passed; no writer bakeoff** | 2026-05-18 (smoke only) | this session | qwen/qwen3.6-plus via OpenRouter. Targeted for B1+ bakeoff per user direction. Also: qwen/qwen3.6-flash (cheaper), qwen/qwen3.6-max-preview (top tier), qwen/qwen3.6-35b-a3b:thinking. |

**Known weakness (claude-tools primary):** partial tool theatre on newly-introduced single-call verifiers (`verify_quote`, `verify_source_attribution` cited but uncalled). Strand-1 catches via `writer_tool_theatre`. Follow-up prompt-tightening, not a rollback trigger.

**Known strength (claude-tools primary):** stable across long-prompt + structured-output-contract conditions; doesn't shortcut to meta-narration the way Claude did at 2026-05-06 bakeoff. Reliable VESUM round-trip on 100+ form artifacts.

**Eval set (target re-bakeoff cadence: monthly):** `a1/my-morning` build with gate-pass-rate, tool_calls_total, vesum_verified.passed, word_count vs target, immersion%, hard-gate failures.

---

### 4.2 V7 module reviewing (per-dim)

| Slot | Agent | Score | Last verified | Evidence | Notes |
|---|---|---|---|---|---|
| **Primary** | Codex (codex-tools) | reviewer-as-fixer ADR-007 contract honored; baseline shipping | 2026-04-26 | `docs/decisions/2026-04-26-reboot-agent-responsibilities.md` §2 | "Cross-agent, no self-review" — `SELF_REVIEW_DETECTED` audit gate enforces. Used for per-dim LLM QG. |
| Runner-up 1 | Claude | reserved for cultural/creative nuance dims | 2026-04-26 | same | "When those reviewers need a different voice." |
| Runner-up 2 | Grok (4.3) | judge-calibration in progress | 2026-05-15 → 2026-05-17 | `audit/2026-05-15-grok-4.3-judge-calibration/`, `audit/2026-05-17-judge-calibration-*` | 4-axis calibration matrix (with-mcp / effort-high / effort-xhigh). Outcome: see audit dirs (full read pending in evidence sweep). |
| Open | DeepSeek | deepseek-v4-pro shipped 2026-05-17 (PR #2107); deepseek-v4-pro-hermes write-mode validated PR #2112 | 2026-05-17 | `MEMORY.md #M-0` row "Content Review with VESUM verification" | Hermes adapter wired; recently promoted to primary on content-review-with-VESUM lane (separate sub-row 4.8). |

**Known weakness:** Path 3 PR3 (#2123) showed the corrector can violate the `<fixes>`-only contract (regenerate instead of patch). Filed as #2127 — promotes the size-limit gate to enforce shape compliance, not just trust the prompt.

**Known strength (codex-tools):** ADR-007 honoring; emits structured fix proposals (`<fixes>` block) reliably; no LLM self-review drift.

#### 4.2.a — Sub-cell: Russianism / linguistic reviewer

New evidence from judge-calibration bakeoffs (per `audit/INDEX-bakeoff-evidence.md`):

| Slot | Agent | F1 / accuracy | Last verified | Evidence |
|---|---|---|---|---|
| **Primary** | Claude Opus 4.7 | **F1=86%, 100% case accuracy** on 12-case Russianism set | 2026-05-15 | `audit/2026-05-15-russianism-judge-calibration/REPORT.md` |
| Runner-up 1 | Gemini-3.1-pro-preview | F1=84% (greeting-FP issue) | 2026-05-15 | same; H2 won at 2026-05-17 — `audit/2026-05-17-judge-calibration-h2/COMPARISON.md` |
| Runner-up 2 | GPT-5.5 (Codex) | high precision, lower recall (conservative) | 2026-05-15 | same |
| Runner-up 3 | Grok-4.3 | F1=77% (middle of pack) | 2026-05-15 | `audit/2026-05-15-grok-4.3-judge-calibration/REPORT.md` |

**Note:** Russianism reviewer ≠ V7 module reviewer. Codex stays primary for full per-dim review per 4.2 above; Claude Opus is primary for the Russianism / linguistic dimension specifically when needed as a standalone judge. This sub-row replaces the previous "Runner-up 1 Claude — reserved for cultural/creative nuance dims" with empirical evidence.

**Promote-protocol round 1 result (2026-05-18, #2132):** DeepSeek-pro proposed splitting the reviewer prompt into Phase 1 (deterministic content-word verification: batch verify_words + query_cefr_level + check_russian_shadow + search_heritage) and Phase 2 (dim-by-dim judgment). Bakeoff queued: DeepSeek-pro vs Codex on `a1/my-morning` post-#2128/#2127 merge.

---

### 4.3 Wiki article writing

| Slot | Agent | Score | Last verified | Evidence | Notes |
|---|---|---|---|---|---|
| **Primary** | Gemini (always) | 100% wiki coverage across 22 tracks (1713 modules) | 2026-05-18 (live) | `/api/orient` `wiki.by_track` percentages | "Wiki writer: Gemini, always" per ADR. `scripts/wiki/compile.py` defaults to `--writer gemini`. |
| Forbidden | Claude | n/a | n/a | `docs/decisions/2026-04-26-reboot-agent-responsibilities.md` §1 | "Never pass `--writer=claude` for wiki rebuilds." |

**Known weakness (Gemini):** ext-article-N placeholder stubs without real URL/title (#1960). Wiki ingestion quality follow-up.

**Known strength (Gemini):** unmetered routine; fast; reliable on bounded structured prose.

---

### 4.4 Adversarial review of design / ADR

| Slot | Agent | Score | Last verified | Evidence | Notes |
|---|---|---|---|---|---|
| **Primary (pre-June-15)** | Claude headless Opus 4.7 xhigh | qualitative — caught the #2127 contract violation hypothesis before m20 build #1; flagged #1933 /goal driver gaps | 2026-05-12 / 2026-05-13 | `docs/dispatch-briefs/2026-05-08-night/1785-d4-decision-lineage.md`, multiple session-state files | Read-only mode; `delegate.py --agent claude --mode read-only --effort xhigh`. |
| **Primary (post-June-15)** | Codex (gpt-5.5 xhigh) | analogous role; novel architectural catches | 2026-05-09 | "E:A+ on `user_-1` sentinel" per MEMORY #M-0 | Substitution per `agent_fallback_substitutions.yaml`. |
| Runner-up | DeepSeek-pro hermes | recent addition; one shipped review | 2026-05-17 | PR #2107 adapter | Cheap second-opinion lane. |

**Known weakness:** Claude headless has occasional silent-stdout failure modes (#2071 fixed by PTY wrap PR #2124, monitor with #M-8 stdout-buffer-empty discipline).

**Known strength (Claude):** synthesis across long-context; multi-domain pattern recognition; orchestrator-aware framing.

---

### 4.5 Code dispatch — mechanical refactor

| Slot | Agent | Score | Last verified | Evidence | Notes |
|---|---|---|---|---|---|
| **Primary** | Gemini (gemini-3.0-flash-preview) | unmetered; routine pattern-application across multiple files | 2026-05-13 | MEMORY #M-0 reframe | "default for routine: running existing scripts, ingestion runs, tests/migrations/fixtures, docs-near-code" |
| Runner-up | Codex | tighter on edge-cases; better for high-uncertainty refactors | 2026-05-12 | various recent merges (#2121, #2123) | Costs Codex quota; reserve for cases where Gemini's pattern-match might miss. |

**Known weakness (Gemini for mechanical):** ambiguous cross-file architectural rewrites; security/concurrency bugs; GH/rebase/auth-heavy work; mass mechanical pattern-application that requires nuanced judgment. For those → Codex.

---

### 4.6 Code dispatch — novel implementation

| Slot | Agent | Score | Last verified | Evidence | Notes |
|---|---|---|---|---|---|
| **Primary** | Codex (gpt-5.5 xhigh) | recent PRs: #2121 healthz cache, #2122 silence-timeout bump, #2123 Path 3 PR3, #2124 PTY wrap, #2125 Path 3 PR4 | 2026-05-17 / 2026-05-18 | recent merge cascade | All required design judgment + tight scoping. |
| Runner-up | Claude headless (pre-June-15) | 2026-05-13 dispatched #1965 jsx-uk-attribute extraction | 2026-05-13 | dispatch brief | Use for architectural novel-impl where Codex's bug pattern is unclear. |
| Open | Gemini | not yet bakeoff'd for novel-impl | n/a | — | File a focused bakeoff to determine if Gemini can take pieces of this lane. |

---

### 4.7 Code review (PR diff)

| Slot | Agent | Score | Last verified | Evidence | Notes |
|---|---|---|---|---|---|
| **Primary** | DeepSeek-flash (deepseek-v4-flash) | "E:A+ 15s" — cheap second-opinion via `delegate.py dispatch --agent deepseek --model deepseek-v4-flash` | 2026-05-15 | MEMORY #M-0 | New primary as of 2026-05-13 routing update. |
| Runner-up 1 | Codex | architectural catches | 2026-05-09 | MEMORY #M-0 row reference | Reserve for novel-architectural cases. |
| Runner-up 2 | Claude inline (orchestrator) | when context-continuity matters | ongoing | this session | I review PRs before merging during my drive. |

**Known weakness (DeepSeek-flash):** new lane; long-tail of evaluation pending.
**Known strength:** 15-second turnaround; very low cost; surfaces obvious regressions.

---

### 4.8 Content review (with VESUM verification)

| Slot | Agent | Score | Last verified | Evidence | Notes |
|---|---|---|---|---|---|
| **Primary** | DeepSeek-pro hermes | uses `sources` MCP proactively (verify_words×N, query_cefr_level, russian_shadow); PR #2107 shipped, PR #2112 validated write-mode | 2026-05-17 | PRs #2107, #2112 | New primary as of 2026-05-17. |
| Runner-up 1 | Claude Opus xhigh | "fast pass" | ongoing | MEMORY #M-0 | Inline by orchestrator for ad-hoc verification. |
| Runner-up 2 | DeepSeek-flash | "cheap" pass | ongoing | MEMORY #M-0 | When budget is tight. |

---

### 4.9 Q&A / single-shot consult

| Slot | Agent | Score | Last verified | Evidence | Notes |
|---|---|---|---|---|---|
| **Primary (routine)** | Gemini-3.0-flash via `ab ask-gemini` | unmetered; fast | ongoing | `scripts/ai_agent_bridge/__main__.py` | Default for low-stakes one-shot. |
| **Primary (deep)** | Gemini-3.1-pro via `ab ask-gemini --model gemini-3.1-pro-preview` | qualitative | ongoing | same | When deep reasoning needed and Codex/Claude not on the question. |
| Runner-up 1 | Codex via `ab ask-codex` | high-judgment one-shot | ongoing | same | For implementation-y questions. |
| Runner-up 2 | Claude inline | when orchestrator IS Claude | ongoing | same | The Q&A is me; no round-trip. |

---

### 4.10 Search / grep / locate

| Slot | Agent | Score | Last verified | Evidence | Notes |
|---|---|---|---|---|---|
| **Primary** | `Agent(subagent_type="Explore", model="haiku")` | cheap, parallel, isolated | ongoing | `CLAUDE.md` "Agent Roster" | Use for "where is X" questions during this session. |
| Runner-up | `ugrep` inline | faster than `grep`; parallel; binary-safe | ongoing | MEMORY "TOOL SELECTION" | Use when I know roughly where to look. |

---

### 4.11 UI/browser testing

| Slot | Agent | Score | Last verified | Evidence | Notes |
|---|---|---|---|---|---|
| **Primary** | Claude inline (this session) with `mcp__claude-in-chrome__*` | qualitative | ongoing | MEMORY #0 "Role" | "Browser/UI testing... that IS mine." |
| Runner-up | Codex Desktop | has `@browser`/`@browser-use` per 2026-05-09 correction | not recently used | MEMORY #M-3 | Available for multi-shot UI flows; requires explicit polling. |
| Forbidden | Claude headless (`--bare`) | n/a | n/a | n/a | `--bare` is not authed for browser tools and not interactive. |

---

## 5. Routing recipes (canonical commands)

| Task | Command |
|---|---|
| V7 module writing | `.venv/bin/python scripts/build/v7_build.py {level} {slug} --worktree --writer claude-tools` (default writer omitted) |
| Wiki article writing | `.venv/bin/python scripts/wiki/compile.py --writer gemini` (default) |
| Code dispatch (mechanical) | `.venv/bin/python scripts/delegate.py dispatch --agent gemini --task-id X --mode danger --worktree --prompt-file BRIEF` |
| Code dispatch (novel) | `.venv/bin/python scripts/delegate.py dispatch --agent codex --model gpt-5.5 --effort xhigh --mode danger --worktree --silence-timeout 3600 --task-id X --prompt-file BRIEF` |
| Adversarial review (pre-June-15) | `.venv/bin/python scripts/delegate.py dispatch --agent claude --mode read-only --model claude-opus-4-7 --effort xhigh --task-id X --prompt-file BRIEF` |
| Adversarial review (post-June-15) | `.venv/bin/python scripts/delegate.py dispatch --agent codex --effort xhigh --mode read-only ...` per substitutions YAML |
| Code review (PR diff) | `.venv/bin/python scripts/delegate.py dispatch --agent deepseek --model deepseek-v4-flash --task-id review-{PR} --prompt-file ...` |
| Content review (load-bearing, VESUM) | `.venv/bin/python scripts/delegate.py dispatch --agent deepseek --model deepseek-v4-pro --task-id review-content-X --prompt-file ...` |
| Q&A (routine) | `.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini "PROMPT"` |
| Q&A (deep) | `.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini --model gemini-3.1-pro-preview "PROMPT"` |
| Discuss (multi-agent) | `.venv/bin/python scripts/ai_agent_bridge/__main__.py discuss CHANNEL "TOPIC" --with codex,claude,gemini` |
| Search / locate | `Agent(subagent_type="Explore", model="haiku", description="...", prompt="...")` |
| Status check (state) | `curl -s http://localhost:8765/api/state/...` |

---

## 6. Promote-protocol — challenge a primary

The matrix updates when bakeoff signal flips a champion. The protocol:

1. **Operator initiates** a challenge on one task-type cell. Says: *"Cell 4.X primary is currently $AGENT. We want to test whether $CHALLENGER can do better with $PROPOSED_CHANGES (prompt / context / harness)."*
2. **Challenger receives a structured request** via `ab discuss`:
   ```
   You are the candidate. The current primary on task type X is $PRIMARY with score $S, last verified $D. We are open to promoting you IF you can show > $S on the same eval set. You may propose ONE OF: (a) prompt change, (b) added context, (c) harness change. State your proposal in 5 lines max + the smallest viable bakeoff that would prove it. If you are not confident, respond DECLINE.
   ```
3. **Bakeoff harness runs** the proposal against the same eval. If new score > primary's score, primary flips. Update this matrix.
4. **Audit trail**: every promote attempt produces an `audit/bakeoff-{date}-{cell}/` directory with the challenge + the eval data + the verdict.

**Anti-fabrication discipline:** the challenger must propose a *change*, not just self-confidence. "I can do it better if you ask me nicely" is rejected; "I can do it better if the prompt's tool-section is reordered to put MCP search verbs in front of CoT directives" is testable.

---

## 7. Open evals (gaps where we lack good data)

Listed by priority for next-session fill:

| Gap | Why | Next step |
|---|---|---|
| Gemini for novel-impl (4.6 runner-up = OPEN) | Routing routinely defers to Codex; Gemini may take pieces of this lane | File bakeoff: same well-scoped novel-impl brief to both Gemini + Codex |
| DeepSeek for adversarial review (4.4 runner-up = limited) | Deepseek-pro only landed 2026-05-17; need more shipped reviews to score | Use it on next 2-3 design-review opportunities |
| Grok for V7 reviewing (4.2 runner-up = calibration-in-progress) | Multiple calibration matrices in audit/2026-05-15-* and 2026-05-17-* | Finalize aggregator report → promote or eliminate |
| Grok for code dispatch (4.5/4.6 = absent) | `HermesGrokAdapter` is one-shot text; can't ship commits today (#2072) | Implement file-edit wrapper per #2072 to unlock the lane |
| Codex Desktop for UI testing (4.11 runner-up = present but unused) | Has @browser tools we haven't exercised | Try Codex Desktop on next browser-test session |

---

## 8. Ranking by role — quality-first, cost-aware (added v1.2)

> **Purpose:** Answer the recurring question *"which model is best for which role, and is the cheap one good enough?"* in one table. Cost notation: $$$ = high (>$3/M input), $$ = medium ($0.50-$3), $ = low (<$0.50), 0$ = unmetered (within current weekly cap).
> **Validation legend:** ✅ = empirical bakeoff data on this role; ⚠️ = gut-routing or limited data; ❓ = no bakeoff, needs validation.

### 8.1 V7 module writer (A1 register-precision; B1+ register-relaxed)

| Rank @ A1 | Model | Cost | Quality status |
|---|---|---|---|
| 1 ✅ | Claude Opus 4.7 (claude-tools) | $$$ | Default. 1224 words / 4 MCP / VESUM 159/159. Lane ends 2026-06-15. |
| 2 ✅ | Codex GPT-5.5 (codex-tools) | $$ | Tools confirmed (11 calls). Content register gap: 996/1200, 51% immersion. Underperforms at A1. |
| 3 ⚠️ | Gemini-3.1-pro (gemini-tools) | 0$ | Last bakeoff: infra crash (#1708). Re-bakeoff needed. |
| 4 ⚠️ | Grok-4.3 (grok-tools) | $ | 52% word count + truncation per #2039. Probably out. |
| ❓ | DeepSeek-v4-pro (deepseek-tools — UNWIRED for V7) | $ | Adapter exists, write-mode validated PR #2112. ~half-day to wire as V7 writer. |
| ❓ | Qwen-3.6-plus (qwen-tools) | $ | Wired 2026-05-18, smoke OK. No writer bakeoff. |
| ❓ | Qwen-3.6-max-preview | $$ | Top-tier qwen, may close gap with Opus at higher cost. |

**At B1+ (immersion inverts to ~100% Ukrainian):** rankings probably shift — codex's high-Ukrainian bias becomes feature not bug. **A1 results do not transfer.** Per-level bakeoff needed.

### 8.2 V7 module reviewer (per-dim LLM QG)

| Rank | Model | Cost | Quality status |
|---|---|---|---|
| 1 ✅ | Codex GPT-5.5 (codex-tools) | $$ | Default per ADR. `<fixes>` contract honored. Bug surfaced #2127. |
| 2 ⚠️ | DeepSeek-v4-pro hermes | $ | New (2026-05-17). Promote-protocol round 1 proposed split-by-phase prompt. Bakeoff queued. |
| 3 ✅ | Claude Opus 4.7 | $$$ | Reserved for cultural/creative nuance. Best on Russianism (§4.2.a). |
| 4 ⚠️ | Grok-4.3 | $ | Judge-calibration in progress; not yet aggregated. |
| ❓ | Qwen-3.6-plus | $ | Untested as reviewer. |

### 8.2a Russianism / linguistic reviewer (empirical F1 ranking)

| Rank | Model | F1 | Cost | Notes |
|---|---|---|---|---|
| 1 ✅ | Claude Opus 4.7 | 86% (100% case accuracy on 12-case set) | $$$ | Primary. |
| 2 ✅ | Gemini-3.1-pro-preview | 84% | 0$ | Greeting-FP issue. |
| 3 ✅ | GPT-5.5 (Codex) | high precision, low recall | $$ | Conservative. |
| 4 ✅ | Grok-4.3 | 77% | $ | Middle of pack. |
| ❓ | DeepSeek-v4-pro | — | $ | No Russianism-judge bakeoff yet. Promising on content review. |
| ❓ | Qwen-3.6-plus | — | $ | Untested. |

### 8.3 Wiki article writing

| Rank | Model | Cost | Quality status |
|---|---|---|---|
| 1 ✅ | Gemini-3.0-flash-preview | 0$ | Primary always. 100% wiki coverage across 22 tracks. |
| FORBIDDEN | Claude | n/a | Per ADR — never pass `--writer=claude` for wiki. |

### 8.4 Adversarial review of design / ADR

| Rank pre-June-15 | Model | Cost | Quality status |
|---|---|---|---|
| 1 ✅ | Claude Opus 4.7 xhigh (read-only) | $$$ | Caught #2127, flagged #1933. Lane ends 2026-06-15. |
| 2 ⚠️ | Codex GPT-5.5 xhigh | $$ | Substitution per `agent_fallback_substitutions.yaml`. Becomes primary post-June-15. |
| 3 ⚠️ | DeepSeek-v4-pro | $ | One shipped (PR #2107). Promising cheap second-opinion. |
| ❓ | Qwen-3.6-max-preview | $$ | Top-tier reasoning candidate; untested. |

### 8.5 Code dispatch — mechanical refactor

| Rank | Model | Cost | Quality status |
|---|---|---|---|
| 1 ✅ | Gemini-3.0-flash-preview | 0$ | Default for routine. Unmetered. |
| 2 ✅ | Codex GPT-5.5 | $$ | Reserve for high-uncertainty / edge-case-heavy refactors. |

### 8.6 Code dispatch — novel implementation

| Rank | Model | Cost | Quality status |
|---|---|---|---|
| 1 ✅ | Codex GPT-5.5 xhigh | $$ | Recent: PRs #2121-#2125. Design judgment + tight scoping. |
| 2 ⚠️ | Claude Opus 4.7 (pre-June-15) | $$$ | When Codex's bug pattern unclear. |
| ❓ | Gemini-3.1-pro | 0$ | OPEN — runner-up bakeoff not run. |

### 8.7 Code review (PR diff)

| Rank | Model | Cost | Quality status |
|---|---|---|---|
| 1 ✅ | DeepSeek-v4-flash | $ | E:A+ 15s, zero false positives. Primary as of 2026-05-13. |
| 2 ✅ | Codex GPT-5.5 | $$ | Architectural catches. Reserve. |
| ❓ | Qwen-3.6-flash | $ | Cheap candidate; untested. |

### 8.8 Content review (with VESUM verification)

| Rank | Model | Cost | Quality status |
|---|---|---|---|
| 1 ✅ | DeepSeek-v4-pro hermes | $ | Primary 2026-05-17 (PR #2107/#2112). Proactive MCP use. |
| 2 ⚠️ | Claude Opus xhigh | $$$ | Inline fast pass. |
| 3 ⚠️ | DeepSeek-v4-flash | $ | Budget-tight option. |
| ❓ | Qwen-3.6-plus | $ | Untested. |

### 8.9 Q&A / single-shot consult

| Rank routine | Model | Cost |
|---|---|---|
| 1 ✅ | Gemini-3.0-flash (`ab ask-gemini`) | 0$ |
| 1 deep ✅ | Gemini-3.1-pro-preview | 0$ |
| 2 ✅ | Codex GPT-5.5 (`ab ask-codex`) | $$ |
| ❓ | Qwen-3.6-plus | $ |

### 8.10 The Chinese-model question (user-asked)

The user said: *"quality foremost, but if Chinese models bring quality we use them."* Status as of 2026-05-18:

| Model | Origin | Already primary in a role? | Validation status |
|---|---|---|---|
| DeepSeek-v4-pro | Chinese (DeepSeek AI) | **YES** — §8.8 content review with VESUM | ✅ Empirical bakeoff 2026-05-17 |
| DeepSeek-v4-flash | Chinese (DeepSeek AI) | **YES** — §8.7 code review | ✅ Empirical bakeoff 2026-05-15 |
| Qwen-3.6-plus | Chinese (Alibaba) | No (just wired) | ❓ Untested in any role |
| Qwen-3.6-max-preview | Chinese (Alibaba) | No | ❓ Untested |
| Qwen-3.6-flash | Chinese (Alibaba) | No | ❓ Untested |
| Kimi K2 | Chinese (Moonshot) | No | ⏸ EXCLUDED per user direction 2026-05-18 |

**Honest take:** DeepSeek has earned primary slots on quality, not just cost. Qwen integration just landed; needs role-specific bakeoffs to know if it earns slots or stays runner-up.

**Recommended next bakeoffs to answer "which Chinese model is good enough for which role" (priority order):**

1. **Qwen-3.6-plus as V7 module writer at B1+** (codex's tools+register issue at A1 may not exist at B1+ register; qwen plausibly fits well here at low cost) — cost ~$5-10/module
2. **Qwen-3.6-plus as Russianism judge** vs Claude Opus 86% F1 baseline — cost ~$2/case set
3. **Qwen-3.6-plus as content reviewer with VESUM** vs DeepSeek-pro current primary — cost ~$3-5/module
4. **Qwen-3.6-max-preview vs Claude Opus xhigh on adversarial review** (post-June-15 readiness) — cost ~$5/review
5. **Qwen-3.6-flash vs DeepSeek-flash on code review** — cost ~$0.50/PR

---

## 9. Maintenance

- Every cell's `last_verified` ages. Re-bakeoff cadence: **30 days** for primary cells, **60 days** for runner-ups.
- New agent added → add to §2 roster + audit every relevant cell.
- Decision card flipping a primary (e.g. 2026-05-12 night's writer reversal) → update the relevant cell's `last_verified` + `evidence` rows.
- `scripts/config/agent_fallback_substitutions.yaml` is the operational projection of this matrix's runner-ups. Keep them in sync.
- API endpoint `/api/activity-matrix?format={json,html}` (future) projects this matrix to agents (JSON) and humans (HTML). Until that endpoint ships, the markdown is the source of truth.

---

## 10. Provenance

- v1.2: 2026-05-18 by orchestrator (Claude inline). Added §8 Ranking-by-role with quality+cost view per user request. Added Qwen-3.6 row to §2 roster (newly wired). Updated §4.1 runner-ups to reflect the codex `tool_calls_total=0` retraction (PR #1907, 2026-05-13). Added DeepSeek + Qwen to writer Open slots pending bakeoff. Excluded Kimi K2 per user direction.
- v1.1: 2026-05-18 by orchestrator (Claude inline). Added §4.2.a Russianism judge sub-cell from new evidence in `audit/INDEX-bakeoff-evidence.md`. Added promote-protocol round 1 results pointer to #2132.
- v1: 2026-05-18 by orchestrator (Claude inline) per user direction.
- Sources:
  - `memory/MEMORY.md` #M-0 (per-task model assignment)
  - `scripts/config/agent_fallback_substitutions.yaml`
  - `docs/decisions/2026-04-26-reboot-agent-responsibilities.md` (writer + reviewer split)
  - `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md` (REVISED-AGAIN 2026-05-13)
  - `audit/bakeoff-2026-05-12-night/REPORT.md` (writer flip)
  - `audit/bakeoff-2026-05-13-midday/`
  - `audit/2026-05-17-agent-bakeoff-evening/` (multi-model probes — 65 files, summary pending evidence sweep)
  - `audit/2026-05-15-grok-4.3-judge-calibration/` + 3 variants
  - `audit/2026-05-17-judge-calibration-*` (h1, h2, matrix, matrix-smoke)
  - `/api/state/routing-budget` (live agent burn + recommendation)
  - `/api/orient` (wiki track health)
  - This session's dispatch experience (recent merges and #2128 in flight)
