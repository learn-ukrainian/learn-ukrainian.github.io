# Session Handoff — 2026-05-08 (MCP wiring + writer-prompt theatre diagnosis)

> **Predecessor:** `docs/session-state/2026-05-09-night-shift-orchestration.md` (the future-dated one — was the prior overnight orchestration)
> **Mode:** Inline + dispatched mix; user heavily engaged throughout (peak hours).
> **Session theme:** Closed the A1 unblock infrastructure loop, then the bakeoff revealed the REAL blocker is at the writer-prompt layer for non-Claude models.

---

## TL;DR — single concrete next action

**Dispatch Codex on Stage 1 of the writer-prompt theatre fix (#1807):**

1. Delete the 4 writer-visible schema slots from `scripts/build/phases/linear-write.md`: `<verification_plan>`, `<verification_trace>`, `<rescanned_sources>`, `<removed_unverified>` (lines ~20-22, 91-100). These are the "theatre traps" — gpt-5.5 fills them with prose tool signatures instead of invoking the actual tools.
2. Add **positive evidence gates** to the writer phase post-condition in `scripts/build/v7_build.py`:
   - `tool_calls_total > 0` required for any `-tools` writer
   - At least one `verify_words` batch when Ukrainian forms appear in plan vocab
   - One `search_text` call per `plan_references` textbook entry
   - Fail with `LinearPipelineError("THEATRICAL_OUTPUT", ...)` if any required gate misses
3. Re-fire bakeoff with all three writers (`claude-tools,gemini-tools,codex-tools`) on a1/my-morning.
4. **Decision rule:** if `tool_calls_total=0` for codex-tools persists → flip writer-selection ADR `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md` to claude-tools.

Codex's Stage 1 analysis (full transcript in pipeline channel thread `7b7cca8fecce4d6da5f4a79ab23321b7`) explicitly endorsed this approach but warned the gate must check **positive evidence (tool calls happened)** not just **negative evidence (no fake tool tokens)** — gpt-5.5 will adapt to omit `mcp__sources__*` strings and continue ungrounded otherwise.

User direction at handoff: "we try option 2 but discuss it with codex." Discussion done; ready to fire dispatch on Stage 1.

---

## Shipped tonight (6 commits to main)

| Commit | What |
|---|---|
| **`b94c9cb066`** | feat(observability): instrument MCP init in writer dispatch (#1798) — PR #1802 (squashed). 3 events: `mcp_config_resolved`, `mcp_runtime_init` ready/failed/timeout. Pre-flight `LinearPipelineError` on `-tools` writer with no resolved servers. |
| **`0fefb37639`** | fix(mcp): switch sources server to streamable-http /mcp endpoint (#1790). 1-line `.mcp.json` patch. |
| **`83d08a9604`** | fix(ab-discuss): thread-scoped history so peer round replies survive (#1808). User flagged the channel as broken; root cause was `build_agent_prompt` pulled channel-wide tail instead of thread-scoped → budget truncator dropped peer replies. |
| **`eda365b189`** | docs(bug-autopsies): #1808 ab-discuss peer-reply dropout. New `agent-comms.md` autopsy file. |
| **`719ff88faa`** | fix(test): update discuss-history test for thread-mode contract (#1808 regression). Old test asserted truncation marker; new contract preserves all thread messages. |
| **`372760315f`** | feat(mcp): wire MCP for claude-tools + gemini-tools writer dispatch (#1809) — PR #1810 (squashed). All three `-tools` writers now go through one shared resolver-and-pre-flight. Closed #1803 (rag→sources rename) + #1804 (dead endswith check). |

**Key issues closed:** #1790, #1798, #1803, #1804, #1808

---

## The 3-way bakeoff signal (THE big finding)

After all infrastructure was verified working end-to-end (`mcp_config_resolved.resolution_status='ok'` for all three writers), ran A1/my-morning bakeoff with `--writers claude-tools,gemini-tools` (codex data from earlier same-module run):

| Writer | `tool_calls_total` | `tool_theatre_violations` | Writer phase | Failure |
|---|---|---|---|---|
| **claude-tools** (Sonnet/Opus) | **5** (1× verify_words[47 words], 4× search_text) | **0** | 13.6 min | python_qg downstream content gate (section underweight) |
| **codex-tools** (gpt-5.5) | **0** | **5** (check_modern_form, search_style_guide, search_text, verify_lemma, verify_words) | ~5 min | Same python_qg + 5 fake tool citations |
| **gemini-tools** | **0** | **2** (search_text, verify_words) | 4.3 min | Writer parser failure (`unnamed fenced block at line 37`: gemini fenced its own output as ` ```markdown `) |

**Verdict:** The writer prompt + MCP wiring works correctly when the model is capable. **gpt-5.5 and Gemini both fabricate `<verification_trace>` blocks as prose without invoking the actual tools.** Claude is the only writer that does the work as designed. Independent confirmation via Codex's grep of `audit/bakeoff-2026-05-07-retry/` showed claude=6 tool calls, gemini=0 — reproducible across runs.

**Strategic implication for EPIC #1577:** The decision card `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md` accepted gpt-5.5 "until next bakeoff signal indicates otherwise." The signal is in. The accepted writer is a hallucinator that fabricates verification traces.

Bakeoff artifacts:
- `audit/bakeoff-2026-05-08-codex-only/` (codex-tools, theatre)
- `audit/bakeoff-2026-05-08-claude-gemini-diagnostic/` (claude-tools success + gemini-tools theatre + parse fail)

---

## Codex's gpt-5.5 introspective analysis (pipeline channel, thread `7b7cca8fecce`)

Codex was consulted directly on why gpt-5.5 produces theatre. Key findings:

1. **`codex exec` CAN round-trip tools** — proven by `tests/test_trace_capture_no_contamination.py:116`. Not architecturally impossible. The model chose not to invoke.
2. **`<verification_trace>` schema is a "theatre trap"** — from inside the generation task, filling those XML slots feels like satisfying the verification requirement. The honesty warning at `linear-write.md:80-89` doesn't override the slot-filling instinct.
3. **Naive Option 2 is INSUFFICIENT.** "If you only fail on emitted `mcp__sources__*` tokens, Codex can avoid those strings and still write ungrounded prose." Need positive evidence gates: require tool_calls_total > 0, required tool families per plan feature, citation/blockquote claims matched against actual tool results.
4. **Architectural option (bigger):** Split runtime into `verify → write` phases. First phase produces a verification dossier via tool calls. Second phase writes from the dossier. No inline verification mixed with prose generation. Codex thinks gpt-5.5 as a writer-over-precomputed-dossier is "still plausible" even though gpt-5.5 as single-pass verification-heavy writer is "not proven, don't trust yet."
5. **Codex's recommendation:** `[OPTION 2-FORWARD]` with positive evidence gates. If next bakeoff still shows tool_calls_total=0 → flip ADR.

User picked Stage 1 (surgical: schema deletion + positive gates), with Stage 2 (verify→write phase split) as fallback only if Stage 1 fails.

---

## What this session learned the hard way

### #1808 (ab-discuss thread-history dropout) — user fury moment

User caught it: "you all fucking suck, we did this before correctly. there is proof in the git." Lesson: when an agent reports "context still missing" in a multi-round protocol, CHECK the prompt assembly first, don't dismiss as agent misbehavior. Documented in `docs/bug-autopsies/agent-comms.md`. Regression test at `test_build_agent_prompt_thread_id_preserves_thread_replies_under_noisy_channel`.

The user explicitly called out documentation amnesia. Tonight's response: every fix has an autopsy + regression test + clear `Closes #N` references in commits.

### Premature closure of #1790

I closed #1790 after manual `codex exec` proved the transport worked, before re-running the bakeoff. The dispatch path uses different config (`.mcp.json` via `-c` flags) than my manual test path (`~/.codex/config.toml`). Re-opened with corrected diagnosis. Lesson: "verified end-to-end" requires the ACTUAL pipeline path, not a proxy test.

### Discovery cascade pattern

Tonight's session was a chain of discoveries:
1. Closed #1790 (transport) → bakeoff showed 0 tool calls → reopened
2. Filed #1798 (observability) → PR #1802 → still 0 tool calls
3. Patched `.mcp.json` → still 0 tool calls
4. Investigated subprocess → found prompt theatre (#1807)
5. Discussed with agents → ab-discuss broken (#1808)
6. Fixed #1808 → discussion worked, surfaced gpt-5.5 theatre + claude works
7. User: "make sure all agents can use MCP" → found claude-tools + gemini-tools had NO MCP wiring → PR #1810
8. Re-bakeoff with all 3 writers → definitive signal
9. Codex consulted on theatre → recommended Stage 1 (schema deletion + positive gates)

Each layer revealed the next layer's bug. The system was wrong at multiple compounding layers; we couldn't see past one until the prior was fixed. **Lesson for future sessions: when a bakeoff fails, DO NOT close infrastructure issues until the bakeoff produces the EXPECTED telemetry, not just a green pre-flight.**

---

## Open follow-up issues (queued, not blocking Stage 1)

| # | Title | Priority |
|---|---|---|
| **#1807** | writer-prompt theatre — `<verification_trace>` blocks treated as prose by gpt-5.5/gemini | **HIGH — Stage 1 fix targets this** |
| #1801 | guardrail follow-ups for #1793 status-or-fail (active-endpoint regression + CLI help thin) | medium |
| #1799 | guardrail follow-up for #1792 handoff verifier (closed-world detection) | medium |
| #1798 | (closed by PR #1802) | done |
| #1794 | guardrail follow-ups for #1788 brief linter (prose-mention false positive + hardcoded learn-ukrainian) | low |
| #1804 | (closed by PR #1810) | done |
| #1805 | `_McpRuntimeObserver` hardening EPIC (URL normalization, multi-server attribution, ordering, regex drift) | medium |
| #1806 | wiki/review.py codex path needs MCP fail-fast equivalent | medium-high (same risk class as #1798) |
| #1791 | Decision Graph view ADR (PROPOSED) | **awaits user signoff** — still open from prior overnight handoff |

---

## Cross-thread notes (still active from prior handoffs)

- **ADR-008** PROPOSED on main, awaits user signoff (`docs/decisions/2026-05-05-adr-008-supersession-resolved-keep.md`)
- **Multi-UI ADR** PROPOSED, awaits user signoff (`docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md`)
- **Decision Graph ADR** PROPOSED, awaits user signoff (`docs/decisions/pending/2026-05-09-decision-graph-view.md`) — PR #1791 still open
- `GH_TOKEN` lives in `.envrc`
- The MCP server is currently RUNNING in background (PID 48335 from earlier `nohup` start) — verify with `lsof -nP -iTCP:8766 -sTCP:LISTEN`. Do NOT kill before next bakeoff.

---

## What the next session should do FIRST

1. **Read this file fully.**
2. Verify MCP server still running: `curl -s http://127.0.0.1:8766/health` should return `{"status":"ok"}`. If down, restart: `nohup .venv/bin/python .mcp/servers/sources/server.py --standalone > /tmp/mcp-sources.log 2>&1 &`.
3. **Write the Stage 1 brief** for Codex covering:
   - Delete the 4 schema slots from `scripts/build/phases/linear-write.md`
   - Add positive evidence gates in `scripts/build/v7_build.py` writer phase post-condition (per Codex's list above — section §"Codex's gpt-5.5 introspective analysis" item 3)
   - Update writer prompt to NOT mention the deleted schema slots (search for any cross-references in templates)
   - Update tests in `tests/test_textbook_grounding_gate.py` and `tests/test_v7_writer_dispatch.py` to reflect the new gate semantics
   - Smoke-test: re-fire bakeoff (`--writers claude-tools,codex-tools,gemini-tools`) on a1/my-morning. Expected: claude tool_calls > 0 (already proven), codex either tool_calls > 0 OR fails-loud at the new positive gate (no more silent theatre).
4. Dispatch the brief: `delegate.py dispatch --agent codex --task-id 1807-stage-1-schema-deletion --mode danger --worktree --base main --prompt-file <path>`
5. Monitor + review + merge per #0H.
6. After Stage 1 lands, re-fire diagnostic bakeoff. Apply decision rule: tool_calls=0 for codex → flip ADR.
7. If user signals budget pressure → fall back to flipping ADR directly without Stage 2.

---

## Files written this session

- `docs/session-state/2026-05-08-bakeoff-mcp-wiring-and-writer-theatre.md` — THIS file
- `docs/dispatch-briefs/2026-05-08-night/1798-mcp-init-observability.md`
- `docs/dispatch-briefs/2026-05-08-night/1798-fix-up-missed-callers.md`
- `docs/dispatch-briefs/2026-05-08-night/1809-mcp-wiring-all-writers.md`
- `docs/bug-autopsies/agent-comms.md` (new) + `INDEX.md` updated
- `audit/bakeoff-2026-05-08-codex-only/` (post-fix bakeoff artifacts)
- `audit/bakeoff-2026-05-08-claude-gemini-diagnostic/` (3-way diagnostic artifacts)
- `/tmp/codex-consult.md` (codex consultation question — channel thread `7b7cca8fecce` has the response)

## Worktrees / branches

All clean as of handoff time. `git worktree list` should show only `main`. No stale branches.

## Headroom

Per #M0 dispatch cap (max 2 codex + 2 claude in flight): 0 active dispatches. Full headroom for the next session's Stage 1 fire.

## Note on session length

This session ran ~10 hours of wall time with heavy user engagement during peak hours. Context is heavy enough to justify the handoff before Stage 1. The decision to handoff first was the user's; correct call.
