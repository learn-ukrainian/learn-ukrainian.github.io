# Anthropic April 23 Postmortem — Impact on `learn-ukrainian` Pipeline

**Author:** curriculum-maintainer (Opus research session)
**Source:** https://www.anthropic.com/engineering/april-23-postmortem
**Scope:** read-only research; no code changes in this session

---

## 1. What the postmortem actually says

Anthropic's April 23 postmortem covers **three independent quality regressions** in Claude Code, the Claude Agent SDK, and Claude Cowork between early March and April 20. The raw Anthropic API was **not** affected — the postmortem is explicit: *"The API was not impacted."* That distinction matters for us: every one of our pipeline paths goes through the Claude Code CLI (`npx @anthropic-ai/claude-code@latest -p`), so we sit squarely in the affected blast radius.

The three issues:

- **Issue #1 — reasoning-effort default silently dropped (Mar 4 – Apr 7)**, affecting Sonnet 4.6 and Opus 4.6. Anthropic flipped the default reasoning effort from `high` to `medium` because *"in our internal evals and testing, medium effort achieved slightly lower intelligence with significantly less latency for the majority of tasks."* Customers rejected the trade-off. Reverted on April 7; Opus 4.7 now defaults to `xhigh`.
- **Issue #2 — prompt-cache "clear thinking" bug (Mar 26 – Apr 10)**, affecting Sonnet 4.6 and Opus 4.6. Intent: *"if a session has been idle for more than an hour, we could reduce users' cost of resuming that session by clearing old thinking sections."* Actual behavior: the `clear_thinking_20251015` API header with `keep:1` flag *"executed on every turn thereafter, not once."* Result: *"each request for the rest of that process told the API to keep only the most recent block of reasoning and discard everything before it."* Symptoms: forgetfulness, repetition, odd tool choices, faster usage-limit drain (cache misses). Fixed in v2.1.101.
- **Issue #3 — length-limit system prompt (Apr 16 – Apr 20)**, affecting Sonnet 4.6, Opus 4.6, **and Opus 4.7**. Anthropic added the line *"Length limits: keep text between tool calls to ≤25 words. Keep final responses to ≤100 words unless the task requires more detail."* to the Claude Code system prompt. Ablation showed *"a 3% drop for both Opus 4.6 and 4.7."* Reverted in v2.1.116.

Residual behavior change shipping as a result: **Opus 4.7 default effort is now `xhigh`** (not `high`), and **Sonnet 4.6+ default is `high`**. Usage limits were reset for all subscribers on April 23. Anthropic also notes *"Two unrelated experiments made it challenging for us to reproduce the issue at first"* — i.e. the regression took weeks to triage because two changes interacted.

---

## 2. Our exposure during the incident window

Every Claude call in this repo flows through `scripts/agent_runtime/adapters/claude.py`, which exec's `npx @anthropic-ai/claude-code@latest` (or a local `claude` binary) in `-p` print mode. Three call paths:

| Path | File | Session? | Effort flag? | Affected by |
|---|---|---|---|---|
| Pipeline writer/reviewer | `scripts/build/dispatch.py:_dispatch_claude_via_runtime` | **No** (`session_id=None`, fresh per call) | **No** (`effort` not passed) | #1 (Mar 4 – Apr 7), #3 (Apr 16 – Apr 20) |
| Inter-agent bridge | `scripts/ai_agent_bridge/_claude.py:_run_claude_sync_via_runtime` | **Yes** (`--resume` for cache warmth) | **No** | #1, **#2 worst-case**, #3 |
| `delegate.py` headless dispatches | `scripts/delegate.py` | No (worktree-scoped, fresh) | Optional `--effort` arg | #1, #3 |
| Interactive session (this one) | `claude_extensions/settings.json` `effortLevel: "high"` | n/a | Hardcoded `high` (not `xhigh`) | #1, #3 |

Concrete consequences:

**a. Five-week window of degraded writer/reviewer reasoning (Mar 4 – Apr 7).** `dispatch.py` builds the Claude invocation with `model=CLAUDE_MODEL_CORE_CONTENT` (which resolves to `claude-opus-4-6` per `scripts/batch/batch_gemini_config.py:84`) and **never sets `effort`**. The adapter only forwards `--effort` when the caller passes it — so during the incident our writer/reviewer phases inherited Anthropic's silently-flipped `medium` default. Every module built in that window — and every reviewer pass — ran below the intended reasoning floor. This is consistent with otherwise inexplicable score variability we saw in late March.

**b. Bridge sessions hit Issue #2 directly.** `_run_claude_sync_via_runtime` deliberately uses `--resume <uuid>` to keep the prompt cache warm across turns (project policy in `agent-runtime-guide.md`: *"Cache economics — 95% of our tokens are cache reads. Dropping resume here would reproduce the 2026-03-21 cost fiasco"*). That is exactly the surface area Issue #2 corrupted — a session idle >1h would, on every subsequent turn, discard prior reasoning blocks. Symptoms in the postmortem (*forgetfulness, repetition, odd tool choices*) match anecdotes from `ab discuss` and `ab channel` long threads in early April.

**c. Pipeline calls were partially insulated from Issue #2** because `dispatch.py` passes `session_id=None` (each pipeline call is fresh, no `--resume`). The cache-clearing bug needed a session that had thinking history to clear. So core builds were less hit than bridge conversations.

**d. April 16–20 length-limit instruction affected ALL three paths** including Opus 4.7. The instruction lived in Claude Code's *internal* system prompt; our `--bare` flag (auto-enabled when stateless + `ANTHROPIC_API_KEY` set, per `claude.py:139`) skips hooks/LSP/plugins but does **not**, per the CLI docs, strip Claude Code's own system prompt. So we ate the 3% drop on writer + reviewer + bridge during that window.

**e. Silent masking in our retry logic.** `_RATE_LIMIT_PATTERNS` in both `dispatch.py` and `claude.py` only catches stderr containing `429`, `rate limit`, `quota exceeded`, etc. The cache-clearing bug emitted **no error signal** — degraded outputs returned `returncode=0` with `result.ok=True`. Our pipeline happily wrote them to disk and ran the reviewer (also degraded) over them. There is no fingerprint in our telemetry that would let us identify which artifacts were produced under the bug.

---

## 3. Required changes (priority-ranked)

### Must change before next build run

| # | What | Why | Effort | Owner | Blocker? |
|---|---|---|---|---|---|
| 1 | **Pin `effort="xhigh"` explicitly in `_dispatch_claude_via_runtime`** for writer/reviewer calls. Add a parameter `effort: str | None` to `dispatch_agent` that defaults to `"xhigh"` for `claude-tools` writer and `"high"` for cheaper reviewer modes. Pass it through to `runtime_invoke(..., effort=effort)`. The runtime + adapter already support it (`adapters/claude.py:97-177` is wired and version-gated via `utils.claude_version.supports_effort`). | Prevents recurrence of Issue #1 (silent default flip). Quote: *"Default reasoning effort changed from `high` to `medium` to reduce latency."* Our pipeline must never inherit a default we don't control. | S | claude/codex | **YES** — every build until this lands could re-degrade if Anthropic flips defaults again |
| 2 | **Bump `CLAUDE_OPUS = "claude-opus-4-7"`** in `scripts/batch/batch_gemini_config.py:84`, and the corresponding `default_model` in `scripts/agent_runtime/adapters/claude.py:84` and `scripts/agent_runtime/registry.py:53`. Add `claude-sonnet-4-6` → `claude-sonnet-4-7` if/when available. The pipeline rule (`.claude/rules/pipeline.md`) already documents `claude-opus-4-7 @ xhigh` as the default — config has not caught up. | Opus 4-6 is the model the postmortem says was hit by all three issues; Opus 4-7 was hit only by Issue #3 (now fixed). MEMORY.md says *"use `xhigh` where we previously used `high`"* — implies 4-7. | S | claude | **YES** — drift between rule docs and config is a known landmine (#1456 supersede pattern) |
| 3 | **Update `.claude/settings.json` (and `claude_extensions/settings.json`) `effortLevel: "high"` → `"xhigh"`.** | MEMORY.md explicitly states *"Anthropic notes Opus 4.7 at `high` is weaker than prior versions, so use `xhigh` where we previously used `high`."* Settings.json never followed. Today's session is running at `high` while reviewing this very postmortem. | S | claude | **YES** — affects every interactive curriculum-maintainer session |
| 4 | **Add a Claude CLI minimum-version gate** in `agent_runtime/runner.py` that raises `AgentUnavailableError` if `--version` < `2.1.116`. Reuse `utils.claude_version` infrastructure that already probes the binary; add a new `supports_postmortem_fixes()` helper with `_MIN_VERSION = (2, 1, 116)`. Block pipeline + bridge if violated; warn on `delegate.py`. | The version that closed all three bugs. Running an older CLI silently regresses us. Quote: *"April 20 (v2.1.116): Reverted system prompt instruction."* | S | claude | **YES** — five minutes of work, prevents stale-binary regression |

### Should change this week

| # | What | Why | Effort | Owner |
|---|---|---|---|---|
| 5 | **Telemetry: log `effort`, `model`, `claude_cli_version` per call** in `agent_runtime/usage.py` JSONL records and `build_stats.jsonl`. Today we record `agent`, `model`, `duration_s`, `tokens` — not `effort`, not CLI version. | Anthropic took weeks to triage their own bug because *"two unrelated experiments made it challenging for us to reproduce."* If we hit a quality regression, we cannot today say "all degraded modules were built with effort=medium under CLI 2.1.103." We need per-call provenance. | M | codex |
| 6 | **Add a stderr/stdout sanity check that flags anomalously short Claude responses** (e.g. <500 chars from a writer phase whose prompt asks for ≥4000-word output). Today we record `response_chars` in `_save_dispatch_log` but don't act on it. A length-limit-style regression in the future would manifest as truncated outputs. | Direct prevention against Issue #3 recurrence. The postmortem's instruction reduced response length AND reduced intelligence — we should fail fast on the length signal. | S | codex |
| 7 | **Tag modules built between 2026-03-04 and 2026-04-20 in `status/{slug}.json`** with an `incident_window: true` flag and a one-line note pointing to this report. | A1 has 31 audit-passing + 40 reviewed modules per the Monitor API; many were built during the window. The next batch-review pass should know which to re-score under stricter conditions. Doesn't force a re-run — just makes the metadata honest. | S | claude |
| 8 | **Bridge: drop `--resume` if the prior session's last activity is >55 minutes old** (just under the 1h trigger Anthropic cited). Mint a fresh session instead, re-prepend the channel `context.md`. Cost: one cache miss; benefit: avoids the exact Issue #2 trigger if it recurs. | Quote: *"if a session has been idle for more than an hour, we could reduce users' cost of resuming that session by clearing old thinking sections."* Even though Anthropic fixed the *bug* implementation, the *feature* is still alive — and idle-session resumption is the trigger. Forcing a fresh session at the cliff edge sidesteps the entire failure class. | M | claude |

### Nice to have

| # | What | Why | Effort | Owner |
|---|---|---|---|---|
| 9 | Document a "model & CLI pin" decision in `docs/decisions/` with a 6-month expiry. Forces a recurring re-evaluation of which Anthropic defaults we trust. | Decision-journal hygiene. Today there is no record of *why* we use 4-6 vs 4-7. | S | claude |
| 10 | Add a `npm run claude:doctor` script that prints CLI version, configured `effortLevel`, and a green/yellow/red verdict against this report's recommendations. | Operator UX. New contributors should see "your CLI is 2.1.103 — too old, please upgrade" without reading 2000 words of postmortem. | M | codex |
| 11 | Update `docs/SCRIPTS.md` and `docs/agent-runtime-guide.md` with an explicit "the `effort` parameter is REQUIRED, not optional" section. Today the guide treats it as one of many kwargs. | Onboarding correctness. Issue #1 will reappear in some other form; our defense is "we always pin effort, period." | S | human |

---

## 4. Behaviors we should ADOPT from the postmortem

1. **Ablation testing for any system-prompt or template change.** Anthropic measured *"a 3% drop for both Opus 4.6 and 4.7"* from a one-line instruction. Our `colors` rebuild diagnostic (#1449) traced multi-point dim drops to a single `_extract_terms` heuristic — same pattern. Whenever we touch a phase template or a writer/reviewer prompt, run before/after on a held-out module and measure the dim deltas. Add this to the existing `prompt-template-review` skill workflow.

2. **Pin everything; treat upstream defaults as breaking changes.** The lesson Anthropic learned the expensive way is "users had calibrated expectations against `high`; flipping to `medium` violated those expectations even though it was technically a 'small' regression." Our equivalent: never inherit `--effort`, never inherit `--model`, never inherit `--output-format`. Always pass them explicitly, even when they match today's default.

3. **Per-call provenance in telemetry.** The postmortem's reproduction difficulty came down to "we couldn't tell which calls had which behavior." Our `batch_state/api_usage/*.jsonl` records should include `effort`, `model`, `cli_version`, `--bare?`, `--resume?` so that any future regression can be A/B-attributed against an exact configuration.

4. **Acknowledge that "low-cost optimizations" mutate cache semantics.** Anthropic's `clear_thinking_20251015` was a cost-optimization that turned into a quality bug. Our equivalent risk surface: `--exclude-dynamic-system-prompt-sections` (CC 2.1.98+, which we enable via version gate). Worth a brief audit to confirm it doesn't silently strip something we depend on. Tracked in section 6 below.

---

## 5. Behaviors we should NOT adopt

- **The `clear_thinking_20251015` API header itself.** That is internal Anthropic protocol used by Claude Code to talk to its backend. We are downstream of Claude Code; we do not — and should not — inject API headers into the conversation. Don't try to "manage" the cache from our side beyond what `--bare` / `--resume` already give us.
- **Anthropic's internal "two-week eval cycle"** before reverting Issue #1. We are smaller, faster, and our user is one person who can make a unilateral call within hours. We should not adopt a heavy formal eval gate before reverting our own bad changes.
- **The length-limit system instruction itself**, even paraphrased. Our writer prompts already have *minimum* word targets (1200 / 2000 / 4000 / 5000 per CEFR level). Adding "keep responses brief" anywhere in the writer/reviewer chain would be the exact antipattern the postmortem flagged. Existing project rule (NON-NEGOTIABLE-RULES.md #1) already enforces this; nothing to add.
- **Verbatim copy of Anthropic's "ablation = subtract one line and re-eval" workflow** as a hard gate. We should adopt the *spirit* (measure before/after) but not the *cost* (Anthropic ablated against an internal eval suite we don't have). Our equivalent is the strict-reviewer multi-dim score on a held-out module, which is cheaper.

---

## 6. Open questions for Krisztian

1. **Switch default `CLAUDE_OPUS` from `claude-opus-4-6` to `claude-opus-4-7`?** The postmortem confirms 4-7 is the path forward and was hit only by Issue #3 (now fixed). Effort-cost increases (xhigh > high), but quality is non-negotiable per project policy. Recommended: yes. Need your sign-off because it affects per-build quota burn.

2. **Re-review or re-build modules created Mar 4 – Apr 20?** Tagging them (Required Change #7) is cheap; actually re-running them is expensive. The 31 A1 audit-passing modules + 40 reviewed are the immediate question. Do we treat this window as a "trust but verify" tier (re-review only, no rebuild) or as a "rebuild from scratch" tier?

3. **Audit `--exclude-dynamic-system-prompt-sections` for our use case?** It's enabled today (CC 2.1.98+ gate). Anthropic's track record on cache-related optimizations is now explicitly mixed (Issue #2). Should I dispatch a Codex investigation to confirm it doesn't silently strip something we depend on (e.g. project-scoped CLAUDE.md sections)?

---

## Appendix — files touched (read-only)

```
scripts/agent_runtime/adapters/claude.py        (read)
scripts/agent_runtime/runner.py                 (grep)
scripts/utils/claude_version.py                 (read)
scripts/build/dispatch.py                       (read 1-120, 350-650)
scripts/build/v6_build.py                       (grep)
scripts/ai_agent_bridge/_claude.py              (read)
scripts/batch/batch_gemini_config.py            (grep)
.claude/settings.json                           (read)
claude_extensions/settings.json                 (read)
docs/agent-runtime-guide.md                     (read)
docs/session-state/2026-04-23-late-evening-handoff.md  (read)
```

No source code modified. No commits. No worktree. Active Codex dispatches on EPIC #1451 Phase 1 (worktrees `codex-1452-alignment-manifest`, `codex-1453-sidecar-freshness`) untouched.
