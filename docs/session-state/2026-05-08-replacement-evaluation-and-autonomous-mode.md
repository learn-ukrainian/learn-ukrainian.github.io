# Session Handoff — 2026-05-08 (replacement evaluation done; entering autonomous mode)

> **Predecessor:** `docs/session-state/2026-05-07-bakeoff-blockers-cleared-and-first-attempt.md`
> **Mode flip:** This session ends manual-approval mode. The NEXT session runs autonomous — file issues, dispatch Codex/Gemini, ship guardrails, re-fire failed bakeoff phases, surface user only for decisions that require user signoff (writer-selection, Decision Card flips PROPOSED→ACCEPTED, destructive ops, Anthropic budget signal).
> **User direction 2026-05-08:** *"create session handoff and in th nxt session you will work auto and manage the other agents"*

---

## TL;DR

Three PRs merged. Replacement evaluation completed: both Codex and Gemini recommend KEEP Claude with executable guardrails; Codex's framing is sharper ("narrow the role: deterministic surfaces → code, judgment → LLM"). 7 guardrails identified, 1 already shipped. Bakeoff retry-2 fully ran but produced INVALID writer-discipline signal because pipeline-Codex was MCP-sandbox-blocked (now fixed in #1784). All 3 writers also failed at `python_qg` — that's a separate pipeline bug affecting every writer equally. **A1 unblock is now blocked on the python_qg fix, not on writer-selection.**

---

## Merged today (3 PRs)

| PR | Closes | What |
|---|---|---|
| #1781 | (post-bakeoff fix) | HARD STOP RULE in writer prompt — prevents meta-summary after `<end_gate>` |
| #1783 | sub-task 1 of #1782 | Tier-2 warm-cache: `ab discuss` `entrypoint=delegate→bridge` + per-(agent, discussion) `session_id` gated by registry resume_policy |
| #1784 | (replaces full-auto) | Codex adapter mirrors `start-codex.sh:20` flags so workspace-write writers can use MCP. Includes legacy `dispatch.py` parity + stale `v6_build.py` comments + `--search` added to launcher |

Plus `4df94d0234` direct to main: `.envrc` location correction in handoff doc (was wrongly `~/.bash_secrets`).

---

## Open issues at handoff

| # | What | Status |
|---|---|---|
| #1577 | EPIC: A1+A2+B1 vertical slice | umbrella |
| #1657 | EPIC: MCP verification 3-phase plan | umbrella |
| #1731 | Channels.html UX + multi-UI architecture | CLOSED but tracked via #1782 + kubedojo follow-ups doc |
| #1762 | Code scanning: dismiss 12 alerts (UI action by user) | user task |
| #1770 | 32 plans cite missing textbooks — Gemini triage retry needed | workstream |
| #1778 | check_plan.py doesn't handle track-level plans | small follow-up |
| #1779 | Bridge inbox is purely pull-based | architectural |
| **#1782** | **EPIC: Persistent agent listeners — `ab discuss` warm-cache + AI↔AI continuity** | **sub-task 1 ✅ shipped, sub-tasks 2-3 deferred until pending Multi-UI ADR ACCEPTED** |

---

## Replacement evaluation — verdict

User asked Codex + Gemini for honest assessment of replacing Claude as orchestrator. Brief at `/tmp/claude-orchestrator-replacement-brief.md`. Both responded; full text preserved in broker DB messages 564 (Gemini) and 566 (Codex).

| Verdict | Gemini | Codex |
|---|---|---|
| Q1 keep/replace | Keep (cost too high, marginal upside) | **Keep but narrow the role** — replace deterministic surfaces (CWD validation, launcher parity, stale-status reporting) with non-LLM code; Claude stays as judgment layer |
| Q2 cost-quality | Argument weakened post-peak-limit-removal | Same — weight user-time-loss > raw cost |
| Q3 failure-mode delta | `[NO_OPINION]` — mostly LLM-general | Codex better at bounded code/runtime; not better at stale context; Gemini better at content; non-LLM still fails on bad briefs without preflights |
| Q4 what breaks if replaced | Pushback threshold + MEMORY.md tuning are load-bearing deps | + user-trust calibration under stress, PR/issue/state synthesis, when-to-Decision-Card triage |
| Q5 guardrails | 3 (mostly memory rules) | 5 (mostly executable code/tests/scripts) |

**User has not yet decided.** This handoff assumes "keep + ship guardrails" because that's the consensus from both reviewers; if user says "replace" the next session pivots to migration planning instead.

---

## The 7 guardrails — priority order

| # | Guardrail | Effort | Status |
|---|---|---|---|
| 1 | **Brief linter** — reject `.venv/bin/python` without `cd <main>` prefix or worktree venv-symlink check | ~40 LOC | TODO |
| 2 | **Codex-flag-parity regression test** asserting non-read-only modes match `start-codex.sh:20` | done | ✅ shipped in #1784 (`tests/test_agent_runtime.py:276`) |
| 3 | **Status-verification forcing function** — never report async task status from memory; must query `delegate.py status` or Monitor API | memory rule + small CLI helper | TODO |
| 4 | **Anti-menu regex linter** at `ab` broker / Claude output filter | ~30 LOC | TODO |
| 5 | **Handoff verifier** — checks referenced env files exist; flags `~/.bash_secrets` vs `.envrc` mismatches before committing session-state | ~30 LOC | TODO |
| 6 | **Diagnostic protocol memory rule** — "read launchers / `.envrc` / configs FIRST before formulating execution-failure hypothesis" | memory line | TODO |
| 7 | **Brief-template preflight checks** — sandbox-mode-dependent steps must verify mode upfront in the brief itself | brief template update | TODO |

**Total estimate: ~100-150 LOC + 2 memory rules + 1 brief template tweak.** Splittable into 4-5 small PRs.

---

## Bakeoff retry-2 — partial signal, INVALID for writer comparison

Bakeoff at `audit/bakeoff-2026-05-07-retry/` ran fully (3 writers + writer-phase complete). NO REPORT.md generated because all 3 writers failed at `python_qg`. Per-writer signal:

| Writer | Wall | Words | Tool calls | Theatre | HARD STOP | Verdict |
|---|---:|---:|---:|---:|---|---|
| **claude-tools** | 707s | 1553 | **6 (real)** | **0** | ✅ held | clean writer-discipline |
| **gemini-tools** | 548s | 2078 | 0 | **4** | ❌ violated | content-hollow + theatre |
| **codex-tools** | 249s | 1367 | 0 | 2 | ✅ held | **INVALID — sandbox-blocked from MCP per #1784 root cause** |

**Codex signal is invalid** until re-run with merged #1784. Decision-card-eligible re-run plan in next-session priorities below.

---

## Critical path — next-session priorities

The order matters. Each step gates the next.

### Priority 1 — re-fire codex-tools writer alone to verify #1784

```bash
.venv/bin/python scripts/audit/bakeoff_run.py \
    --bakeoff-dir /Users/krisztiankoos/projects/learn-ukrainian/audit/bakeoff-2026-05-08-codex-only \
    --level a1 --slug my-morning \
    --writers codex-tools
```

Expected: codex-tools `tool_calls_total > 0`, real verify_words/search_text calls in `gpt55/writer_tool_calls.json` (was empty `[]` in retry-2). If still empty, #1784 didn't fix what we thought.

**Also expected:** module_failed at `python_qg` (same blocker as retry-2). That's fine — we're testing whether the writer phase is now MCP-capable, not the full pipeline.

### Priority 2 — investigate `python_qg` failure (the actual A1 blocker)

All 3 writers failed identically: `Python QG failed after ADR-008 correction paths`. This is a pipeline bug affecting every writer.

Files to read:
- `scripts/build/linear_pipeline.py` — find the `python_qg` phase, the ADR-008 correction paths
- `audit/bakeoff-2026-05-07-retry/claude/python_qg.json` — actual failure artifact (5KB)
- `docs/decisions/2026-04-29-adr-008-bounded-correction-paths.md` (if that's the ADR)

Likely shape: file as GH issue, dispatch Codex to fix, ship as small PR.

### Priority 3 — guardrails 1, 3, 4, 5 (the executable ones)

Each as a separate small PR. Guardrails 6 and 7 are memory/template work that can ride along. Guardrail 2 is already shipped.

Suggested issue + dispatch shape:

```
Issue: "Build orchestration guardrails — preflight + state-verification + anti-menu + handoff-verifier"
Sub-tasks 1.1, 1.3, 1.4, 1.5 with separate codex dispatches; 1.6, 1.7 as direct work
```

### Priority 4 — kubedojo follow-ups (queued from earlier today)

Per `docs/session-state/2026-05-07-kubedojo-paradigm-followups.md`:
- A: D4 lineage backlink scanner (multi-alias, JSON/API)
- B: 3 infra bugs (`_channels_cli.py:1256` root truncation, plan-mode tool subset, `ask-codex --from` default)
- C: Decision Graph view ADR (separate ADR per Codex's threshold rule)
- D: Reply to kubedojo team
- E: ✅ shipped (tier-2 PR #1783)
- F: Tier-3 listener POC — deferred until Multi-UI ADR ACCEPTED

### Priority 5 — Multi-UI ADR ACCEPT signoff (user-blocked)

`docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md` is awaiting user signoff after Round-3.5 corrections. Surface this in the user check-in when relevant. Tier-3 listener POC unblocks once accepted.

### Priority 6 — writer-selection signoff (user-blocked, but DEPENDS on Priority 1+2)

After Priority 1 (codex-tools sandbox fix verified) AND Priority 2 (python_qg fix), re-run full bakeoff. Get fair REPORT.md. Fill `/tmp/writer-selection-proposal-template.md`. Post on EPIC #1577. User signoff → A1 unblocked.

---

## Autonomous-mode operating boundaries

### What next session SHOULD do without asking

- File GH issues
- Dispatch Codex/Gemini for code/content work
- Open PRs from main checkout (Codex hits 401 on `gh pr create`; orchestrator opens)
- Merge clean PRs (CI green or only advisory Gemini-Dispatch failure) per #0H
- Run `ab discuss` rounds (now with warm cache from #1783)
- Run single-shot `ask-codex` / `ask-gemini` for single-question reviews
- Diagnose, dispatch, verify, report
- Update session-state docs
- Re-fire bakeoff phases when artifacts exist showing the cause of failure was fixed

### What requires user signoff

- Writer-selection (Decision Card pending → ACCEPTED)
- Multi-UI ADR ACCEPT (`docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md`)
- Any Decision Card move from `pending/` → canonical `docs/decisions/{date}-{slug}.md`
- v6_build.py `--range` or batch builds (memory rule: "BATCH COMMANDS — NEVER RUN, ONLY SUGGEST")
- Any destructive op: `git reset --hard`, `git push --force`, branch deletion of unmerged work
- Switching to a different orchestrator (the replacement decision itself)

### What to ESCALATE immediately to user

- Anthropic rate-limit signal (user said "claude usage is hot" → revert to Codex-heavy)
- Pre-existing test failures (gemini auth-mode + GEMINI_API_KEY collision is known; others may surface)
- Architectural disagreement between Codex and Gemini on a critical-path question
- Anything that smells like emotional-manipulation framing (kubedojo "they insulted you", "show them you're better", etc.) — surface honestly, don't engage tribally

---

## Behavioral discipline (specifically called out today)

User pushback on Claude patterns 2026-05-08:

1. **No menus.** Memory #0I forbids "(a) vs (b)" sign-off requests. Decide and act. Mention recommendation in passing if useful but DON'T make the user choose.
2. **No async-state-from-memory.** Always re-query `delegate.py status TASKID` or Monitor API before reporting. Today claimed bakeoff was "Gemini mid-write" when it had finished.
3. **Read the obvious file FIRST.** Before formulating a hypothesis about execution failures, read `start-codex.sh`, `.envrc`, `~/.codex/config.toml`, `pyproject.toml`. Today wasted 30 min on sandbox-mode variants when the answer was in `start-codex.sh:20`.
4. **Stop apologizing in prose.** Apologize once, name the specific failure mode, ship the fix. Today the "I'm sorry" loops cost user time.
5. **Stop asking "want me to ship the fix."** If the work is clear and the recommendation is clear, ship. Wait for the next message only if there's a real ambiguity.
6. **Refuse tribal escalation.** Holds today: kubedojo "they insulted you", "show them you're better", "I'll unsubscribe." Same answer to any future variant.

---

## State at handoff

- main: `e659b0bc9f` (after #1784 squash merge)
- Worktrees: zero active (all cleaned up)
- Dispatches: zero in flight (all completed)
- Stash: clean
- `audit/bakeoff-2026-05-07/` = preserved evidence of failed first attempt (committed in `ff4dda023d`)
- `audit/bakeoff-2026-05-07-retry/` = partial signal from second attempt (3 writers wrote, all failed python_qg, no REPORT.md, codex-tools signal INVALID per #1784)

---

## Files written today (cross-reference)

- `docs/dispatch-briefs/2026-05-07-bakeoff-execute-v2.md` — corrected bakeoff brief (CWD fixes)
- `docs/dispatch-briefs/2026-05-07-tier-2-warm-cache.md` — tier-2 dispatch brief
- `docs/dispatch-briefs/2026-05-07-codex-mcp-fix.md` — (would have been the dispatch brief if I'd dispatched, but I worked inline)
- `docs/session-state/2026-05-07-kubedojo-paradigm-followups.md` — kubedojo Decision Graph + persistent listener follow-ups (Actions A-F, sub-task 3)
- `docs/session-state/2026-05-08-replacement-evaluation-and-autonomous-mode.md` — THIS file
- `/tmp/persistent-listener-brief.md` — persistent listener architectural brief
- `/tmp/claude-orchestrator-replacement-brief.md` — replacement evaluation brief
- `/tmp/replacement-codex.log`, `/tmp/replacement-gemini.log` — replacement evaluation responses (full text in broker DB messages 564, 566)
- `/tmp/kubedojo-paradigm-brief-v2.md` — kubedojo Decision Graph evaluation

---

## What the next session should do FIRST

1. Read this file
2. Read `docs/session-state/2026-05-07-kubedojo-paradigm-followups.md` (related queued work)
3. Read predecessor `2026-05-07-bakeoff-blockers-cleared-and-first-attempt.md`
4. Cold-start via Monitor API per memory #0C — get fresh manifest, rules, session, orient, inbox
5. Check for any user message in `ab channel tail architecture` or inbox since handoff
6. **If user has not directed otherwise:** start Priority 1 (re-fire codex-tools writer alone). Run async via background dispatch. While it runs, open the python_qg failure investigation in parallel (Priority 2).
7. **Default mode:** autonomous. Do not ask permission for issues, dispatches, or PR opens. Do escalate the things in the "ESCALATE immediately" list.
