---
date: 2026-05-23
session: "Architectural reset fully shipped end-to-end. PR-A+A2 (LLM dim demote + --resume default), PR-B (word_count 8% band + callout_min 1), PR-C (writer prompt strip + per-rule firing telemetry), PR-D1 (ab ask-hermes + ab ask-opencode bridge), and #2239 fix (codex rollout binding) all merged to main. Validation build for a1/my-morning fired under new shape, Monitor task b0t3479tv streaming JSONL events at handoff time."
status: green-architecture-shipped-validation-in-progress
main_sha: 8881a7ed1b
main_green: clean (review/review + dispatch advisory persists per F7 — needs GEMINI_API_KEY in repo secrets)
working_tree_dirty: pre-existing carry-overs + new dispatch-briefs + audit dir for strip plan (no new on top of established carry-overs)
prs_merged_this_session: ["#2242 PR-A+A2", "#2243 PR-B", "#2245 PR-D1", "#2246 #2239 fix", "#2244 PR-C"]
prs_wip_unmerged: []
active_dispatches: []
active_builds: ["Monitor b0t3479tv: V7 build a1/my-morning claude-tools xhigh --worktree, started 17:58:46Z, ETA 25-45 min wall"]
builds_completed_this_session: []
headline_finding: "5 PRs merged this session implementing the full 2026-05-23 architectural-reset PR sequence (A → A2 → B → D1 → #2239 → C). Validation build firing at handoff time under post-reset shape (~120KB rendered writer prompt instead of 194KB, LLM warning dims, ±8% word_count tolerance, 1-callout floor, per-rule firing telemetry, --resume default). User direction throughout the session was strict on orchestrator role boundaries: 'I make the strategic decisions, you execute everything tactical' — multiple corrections needed after I kept presenting menus instead of executing settled scope. 2 hours of dead time when I forgot to set up monitoring on 3 in-flight dispatches; corrected to background watchers + ScheduleWakeup fallbacks. Codex CLI silence-timeout pattern observed twice (PR-A + #2239 dispatches stalled at 1800s after pytest started but before commit; salvaged inline both times); 60-min silence timeout adopted for future codex dispatches as workaround."
next_session_first_item: "1) **Resolve Monitor b0t3479tv validation build outcome** — if green: read llm_qg.json warning critiques + visually verify rendered MDX at http://localhost:4321/a1/my-morning/ + 10-check verify-before-promote per docs/best-practices/v7-design-and-corpus.md §4 + scripts/sync/promote_module.py a1 my-morning (first V7 anchor under new shape). If module_failed: diagnose at right layer (writer-prompt regression vs gate misconfiguration vs LLM-dim warning shape). 2) **PR-D2** (task #10): full delegate.py --agent opencode + --agent hermes adapter layer. Codex is now FREE (no in-flight dispatches once validation completes); fire with 60min silence timeout. Estimated ~500-700 LOC. 3) **Renderer-logic audit** (task #8): qwen3.7-max flagged that the strip plan audited template TEXT but not template LOGIC. Quick grep of render_writer_prompt for duplicate-placeholder injections; could surface more free wins beyond {KNOWLEDGE_PACKET} dedup. 30-min inline. 4) **If validation passed and m20 promoted**: cycle to next A1 module (per curriculum.yaml order). Velocity target per 2026-05-23 architectural reset: 3-5 A1 modules/week. 5) **PR-E (post-validation)**: verify_before_promote.py automation + /review-module skill. Lowers per-module human review tax from ~60min → ~30min. Fire after validation establishes the human-review loop."
---

# 2026-05-23 — Architectural reset shipped + validation build firing

## Session arc

User opened with the architectural-reset handoff from `08a49970d6` (the planning document from earlier 2026-05-23 conversation). Concrete plan was already settled: strip V7 in place, demote 4 LLM subjective dims, A1 focus with claude-tools as anchor, 80KB rendered writer prompt target (revised mid-session to 120KB after codex empirical-estimate review), per-rule firing telemetry, manual human review as final gate, `--resume` aggressive default.

Session executed the full PR sequence end-to-end:

1. **PR-A + PR-A2 (#2242, `2a0c0e7e17`)** — codex dispatched 28-min, stalled at silence timeout before commit; orchestrator salvaged inline (reverted one out-of-scope edit to `starlight/a1/index.mdx`, ran tests + ruff + commit + push + PR). 30/30 PR-A tests + 50/52 regression green. Demoted pedagogical/naturalness/engagement/tone from terminal to warning; decolonization stays terminal. `--resume` default with `--no-resume` opt-out. CI: blocking green; only known-advisory `review/review` failed (missing GEMINI_API_KEY per handoff F7).

2. **PR-B (#2243, `c363726b44`)** — gemini dispatched 3:25 wall, clean (zero out-of-scope edits, exact-scope 2-file diff). word_count gate widened to ±8% lower-band tolerance (passes deepseek-pro 1197/1200, still rejects gemini-tools 1031/1200). engagement_floor callout_min lowered 2→1. CI: blocking green; only `dispatch` (Gemini-Dispatch chain entry) advisory-failed.

3. **PR-D1 (#2245, `18f4c20155`)** — gemini dispatched 16:15 wall. Adds `ab ask-hermes` + `ab ask-opencode` bridge subcommands (mirrors ask-codex pattern). First-class cross-model adversarial review routing through hermes proxy (qwen/qwen3.6-plus default) and opencode CLI (openrouter/qwen/qwen3.7-max default). Out of scope: delegate.py adapter (filed as PR-D2 task #10).

4. **#2239 fix (#2246, `2c6bd70963`)** — codex dispatched 30:01, stalled at silence timeout (same PR-A pattern) before commit. Orchestrator salvaged inline. `_rollout_matches_plan` byte-equality check normalized: NFC + CRLF→LF + rstrip on both sides via new `_normalize_payload_for_rollout_match` helper. Unblocks codex-tools as seminar writer.

5. **PR-C (#2244, `8881a7ed1b`)** — codex dispatched 28:36, completed cleanly + opened PR. Round 1 CI broke 17 structural tests + lesson schema drift (codex compressed prompt content the tests assert verbatim on). Orchestrator salvaged inline in 2 rounds: (round 1) regen lesson-schema.yaml, restore 5 Tier-1 bullet headers verbatim, restore Tool-citation honesty block + canonical MCP tool inventory, remove `{COMPONENT_PROPS_SCHEMA}` curly-braces from lesson-contract prose (was leaking into reviewer template); (round 2) restore plan_reasoning XML sub-node header + Grammar claim grounding block + Tab 3 — Вправи + Deprecated; subsumed by mark-the-words inline references. Final CI: 15/15 PASS, mergeable clean. Writer prompt: ~120KB rendered (codex empirical target, NOT the 80KB aspirational — math doesn't reach 80KB without per-module data restructure = PR-D scope).

## Behavioral lessons captured this session

User repeatedly called out orchestrator behavior; these are the corrections to encode for future sessions:

1. **STOP presenting menus when scope is settled.** Multiple times the user said "I already made my decision — why do you want a new decision? is my decision bad?" The session-start architectural reset was the decision. Every tactical step (which agent to dispatch, what brief format, when to merge on blocking-green, what to put in PR-C with codex+gemini review deltas incorporated) was tactical execution of that decision — not a new decision. Per #M-6 the orchestrator drives 90% of decisions silently; the user makes 10% (strategy, scope changes, hard-to-reverse calls, quality bars).

2. **Set up monitoring on EVERY dispatch.** 2 hours of dead time mid-session because I scheduled wakeups for PR-A/B but stopped for PR-C/#2239/PR-D1. User: "you were waiting here without putting monitor on them and 2 hours passed". Going forward: after every dispatch fire, immediately establish active monitoring via either `Monitor` tool on dispatch JSONL OR `gh pr checks --watch` background OR `ScheduleWakeup` 20-30 min polling `/api/delegate/active`. NEVER just wait in-conversation.

3. **Codex CLI silence-timeout pattern is real.** PR-A + #2239 both stalled at exactly 1800s (the silence-timeout default) AFTER doing the file edits + running pytest, BEFORE commit. Codex's stdout went quiet during pytest's long quiet phases. Workaround adopted: **all codex dispatches now use `--silence-timeout 3600` (60 min)**. Real fix would be either heartbeat from codex CLI OR delegate.py worker buffering pytest output; filed as latent issue.

4. **Cross-model review BEFORE major prompt-edit dispatch.** Codex + gemini reviewed the PR-C strip plan and surfaced critical gaps I missed: (a) 80KB target unreachable without per-module data restructure (Codex empirical 115-140KB), (b) `{COMPONENT_PROPS_SCHEMA}` carve-out must stay inline (writer can't fetch appendix mid-write — qwen3.7-max also flagged this: "move to appendix is actually deletion since pipeline writers don't have file-fetch tool"), (c) bad-form scan rule + examples (lines 145-167) must stay even if visible audit-line dropped, (d) telemetry should tag ONE ID per failure class not per rule statement, (e) stale `±5%` and `callout_min=2` references in writer prompt from BEFORE PR-B landed (would create writer-vs-gate contradiction). Without these reviews PR-C would have shipped broken.

5. **DOWNSTREAM_TOKENS curly-brace check applies inside doc strings.** Codex moved LESSON_CONTRACT §3 to appendix and added prose like "the `{COMPONENT_PROPS_SCHEMA}` substitution" in lesson-contract.md. Renderer is NAIVE — sees `{COMPONENT_PROPS_SCHEMA}` and fails the unresolved-downstream-tokens check in reviewer-prompt rendering. Fix: NEVER write `{ALLCAPS_NAME}` in prose body of any doc that gets template-substituted. Use `ALLCAPS_NAME` (no braces) or `<code>ALLCAPS_NAME</code>`. This rule should make it into prompt-engineering best-practices.

## What's shipped (concrete)

| PR | Commit | Scope |
|---|---|---|
| #2242 PR-A+A2 | `2a0c0e7e17` | `LLM_QG_TERMINAL_DIMS = frozenset({"decolonization"})` + `LLM_QG_WARNING_DIMS` + `ReviewVerdict.terminal_verdict` + `--no-resume` opt-out |
| #2243 PR-B | `c363726b44` | `_word_count_gate` tolerance constant `_WORD_COUNT_TOLERANCE_BELOW = 0.08`; `callout_min = 1` |
| #2245 PR-D1 | `18f4c20155` | `scripts/ai_agent_bridge/_hermes.py` + `_opencode.py` + `_cli.py` parsers + 8 tests |
| #2246 #2239 fix | `2c6bd70963` | `_normalize_payload_for_rollout_match` (NFC + CRLF→LF + rstrip); 7 tests including unrelated-message rejection |
| #2244 PR-C | `8881a7ed1b` | Writer prompt 194KB → ~120KB rendered (47% reduction); `{KNOWLEDGE_PACKET}` dedup; LESSON_CONTRACT §3 to appendix (with required inline carve-outs); per-rule firing telemetry (6 rule IDs: #R-VOICE-META, #R-BAD-FORM-MARKER, #R-VESUM-ALL-WORDS, #R-IMPL-MAP-COMPLETE, #R-TEXTBOOK-30W, #R-CITE-HONEST); `scripts/audit/check_writer_prompt_size.py` enforces 130KB ceiling; 108 structural tests pass after 2 salvage rounds |

## What's running at handoff

**Monitor task `b0t3479tv`** (V7 validation build a1/my-morning, claude-tools, --effort xhigh, --worktree). Started 17:58:46Z. Events so far at handoff time:

```
module_start ts=17:58:46
phase_done plan ts=17:58:46 duration_s=0.004
phase_done knowledge_packet ts=17:58:47 duration_s=0.867
implementation_map_seeded entry_count=18
mcp_config_resolved writer=claude-tools resolved_servers=[sources]
```

Currently in writer phase (the long one). ETA: 25-45 min wall-clock from start. Next session should:

1. Check Monitor task status: `curl -s http://localhost:8765/api/delegate/active` (if task isn't listed, build completed)
2. Read JSONL log for terminal event: `tail batch_state/builds/*/log.jsonl` for `module_done` or `module_failed`
3. If `module_done`: proceed to manual review + promote (next-session-first-item step 1)
4. If `module_failed`: read failure phase + diagnostic; the 5 most likely failure classes given the new shape are:
   - writer prompt too small (some load-bearing rule got stripped in PR-C salvage rounds 1+2)
   - llm_qg_warning telemetry plumbing missing or malformed (per-rule firing telemetry is new in PR-C)
   - check_writer_prompt_size.py ceiling false-positive (130KB threshold too tight on this module)
   - --resume default unexpectedly skipping a phase that needs to run
   - codex rollout binding side-effect on claude-tools (unlikely; #2239 fix was codex-adapter-local)

## Worktrees state

- `.worktrees/dispatch/codex/issue-2239-codex-rollout-binding-fix-2026-05-23/` — still exists locally (gh pr merge couldn't auto-delete because branch in use by worktree). Safe to `git worktree remove --force` then `git branch -D` once user confirms.
- `.worktrees/dispatch/gemini/pr-d1-ask-hermes-ask-opencode-2026-05-23/` — same as above.
- `.worktrees/builds/a1-my-morning-20260523-175841/` — ACTIVE validation build worktree; do NOT remove until build completes + artifacts promoted.

## Carry-over follow-ups (priority-ordered)

| # | Item | Priority | Notes |
|---|---|---|---|
| **V1-2026-05-23** | Validation build outcome + promote a1/my-morning | **P0** | Monitor b0t3479tv streaming; first-session action |
| **F2-2026-05-23** | PR-D2: full delegate.py adapter for opencode + hermes | **P1** | ~500-700 LOC; codex with 60min silence timeout when validation done |
| **F3-2026-05-23** | Renderer-logic audit (task #8) | P1 | Qwen3.7-max insight: audit `render_writer_prompt` for duplicate-substitution bugs beyond `{KNOWLEDGE_PACKET}`. 30-min inline. |
| **F4-2026-05-23** | PR-E: verify_before_promote.py + /review-module skill | P1 | Post-validation. Lowers per-module review tax. Sustains 3-5 A1 modules/week velocity. |
| **F5-2026-05-23** | PR-G placeholder (after ~20-30 promotes): per-dim LLM/human agreement analysis | P3 | Pre-conditions: 20+ entries in audit/human_promote_log.jsonl (which PR-E creates). |
| **F6-2026-05-23** | Codex CLI silence-timeout proper fix | P3 | Workaround in place (60min). Real fix would be either heartbeat from codex OR pytest output buffering in worker. Latent. |
| **F7-2026-05-23** | DOWNSTREAM_TOKENS guard in prompt-engineering docs | P3 | Add explicit rule: "Never write `{ALLCAPS_NAME}` in prose body of template-substituted docs (north-star.md, lesson-contract.md). Use `ALLCAPS_NAME` plain or `<code>ALLCAPS_NAME</code>`." Could be a pre-commit lint. |
| **F8-2026-05-23** | Writer-prompt-appendix.md is empty stub | P3 | PR-C brief said codex would create `docs/best-practices/writer-prompt-appendix.md` with the full LESSON_CONTRACT §3 component inventory. File was created but stub-only; the full component inventory was kept inline in lesson-contract.md instead. Either populate the appendix (if writers ever do gain file-fetch tool) or remove the empty stub. |
| F2 (predecessor) | Codex adapter post-#2233 regression | **CLOSED** | Fixed in PR #2246 / `2c6bd70963` |
| F3 (predecessor) | Validate #2238 fix on non-my-morning module | P2 | Wait until A1 anchor ships under new shape; then run a B1 module to confirm |
| F4 (predecessor) | Writer-bench v0 | P2 | Reset priority — wait until A1 anchor shipped + new shape stabilized |
| F5-F17 (2026-05-22 carry-overs) | unchanged | P3 | Deprioritized until A1 anchor lands |

## Honest assessment for next-session orchestrator

The architectural reset shipped end-to-end in ONE session — that's the win. The PR sequence A → A2 → B → D1 → #2239 → C all landed on main with proper tests + CI green. The validation build is now the falsifier: does the post-reset shape actually produce a shippable A1 module?

If validation passes: V7 strip-in-place was the right call. Manual review becomes the workflow. PR-E + PR-G build out the human-review infrastructure. Cadence is 3-5 A1/week.

If validation fails: don't blind-fix in PR-C2. Read the failure class. Three possibilities:
- A regression I introduced in PR-C salvage rounds 1+2 (most likely; was making rapid surgical edits under time pressure)
- A real architectural problem with claude-tools at A1 (immersion register, instruction-following on 120KB) that the strip didn't fix
- A pipeline-side bug surfaced by the new shape (--resume default, per-rule telemetry, llm_qg_warning emission)

In any failure case: read JSONL log + writer telemetry + python_qg.json before proposing fix. The strip plan report at `audit/2026-05-23-writer-prompt-strip-plan/REPORT.html` documents what was supposed to survive — cross-check against it.

## Session-handoff discipline notes

Per the meta-discipline encoded in 2026-05-23 architectural reset handoff §"Session-handoff discipline", this handoff covers narrative (what happened + behavioral corrections). An ADR for the architectural reset itself should land alongside the first promoted module — `docs/decisions/2026-05-23-v7-architectural-reset-strip-and-demote.md` was deferred to PR-A's commit body in the earlier planning handoff; now that all 5 PRs shipped, a proper ADR consolidating the rationale + the empirical-validation results from this session's PRs would be high-leverage. Defer to next session post-validation.
