---
date: 2026-05-13
session: "Midday — pipeline gate fixes after #1901 fix re-eval surfaced 3 more gate/telemetry/adapter bugs + #1900 investigation revealed codex was working all along"
status: ok
detail: 2026-05-13-midday-pipeline-gate-fixes.html
main_sha: ae82644c1c
main_green: true
open_prs: [1904]
active_dispatches: [writer-telemetry-result-summary, 1903-rollout-matcher-fix]
merged_today: [1902]
closed_today: [1900, 1901]
filed_today: [1903, 1905]
in_flight: [writer-telemetry-result-summary, 1903-rollout-matcher-fix]
blocked: ["a1/my-morning publication — waiting on 3 fix dispatches + post-fix re-eval"]
agents: [claude, codex]
worktrees_open: 3
ci_notes: |
  PR #1904 (vesum-gate-distractor-awareness) is open with all blocking checks green EXCEPT Secret Scanning (gitleaks) which failed on a TRANSIENT Docker GHCR timeout (`Client.Timeout exceeded while awaiting headers`, exit 125 pulling trufflehog image). NOT a real secret leak; PR diff has zero credential-like content. Needs re-run via UI or empty-commit push (orchestrator token lacks `gh run rerun` permission).
incidents: []
---

# Brief — 2026-05-13 midday — pipeline gate fixes

> Machine-readable companion to `2026-05-13-midday-pipeline-gate-fixes.html`.
> Predecessor: `2026-05-13-morning-actual-outcomes-brief.md`.

## TL;DR

- **#1901 OSError fix merged** (`2c38ebd11c` via PR #1902, Codex dispatch). Closed.
- **#1900 (codex MCP visibility) investigation done** — Claude-headless adversarial dispatch returned a major finding: **codex was working all along**. The 3-bakeoff "codex tool_calls_total=0" pattern was OUR rollout-matcher bug rejecting codex's tool-call events. Codex's night-bakeoff rollout has 8 successful MCP calls (5× verify_words verifying 121 forms, 3× search_text retrieving textbook pages). It out-tool-called Claude (4) by 2×.
- **ADR-REVISED → claude-tools is based on false evidence** and needs reconsideration after fixes land.
- **3 follow-on fix dispatches fired**: vesum-gate-distractor-awareness (PR #1904 open, CI flaky), writer-telemetry-result-summary (in flight), 1903-rollout-matcher-fix (in flight).
- **New EPIC follow-up issue #1905 filed** — "Pipeline replay-mode regression suite" to prevent this class of bug from burning LLM quota in the future.
- **A1/my-morning publication still blocked.** Waiting on 3 fix dispatches + post-fix re-eval.

## What shipped (commits this session)

| Commit | What |
|---|---|
| `492d781dfd` | fix(hooks): session-setup.sh deploy-drift check matches deploy script excludes |
| `c6bb2faabb` | docs(rules): sync pipeline.md writer policy to REVISED ADR (claude-tools) |
| `30dfc4ab6b` | docs(dispatch-briefs): 2026-05-13 #1901 _prepare_query OSError fix |
| `2c38ebd11c` | fix(sources_db): bound Path(query).exists() probe to avoid OSError swallow (#1901) (#1902) ← Codex dispatch |
| `ae82644c1c` | docs(dispatch-briefs): 2026-05-13 vesum gate + writer telemetry fixes |

Main green at `ae82644c1c`. Predecessor session shipped 1 PR merge + 1 ADR revision + 2 follow-up issues (#1900, #1901); this session merged #1901 fix + filed 2 more (#1903, #1905) + fired 3 fix dispatches.

## In-flight dispatches (re-establish #M-8 monitoring on resume)

| task_id | agent / model | started | expected | status |
|---|---|---|---|---|
| `writer-telemetry-result-summary` | codex / gpt-5.5 high | 09:56:43Z | 60-120 min | running ~14 min in |
| `1903-rollout-matcher-fix` | codex / gpt-5.5 high | 10:06:55Z (approx) | 30-60 min | running, fresh |

#1900 Claude investigation already finished (737s, done) — deliverables: `audit/2026-05-13-codex-mcp-visibility-investigation.html` (29 KB report) + comment on #1900 + new issue #1903 with full reproducer + fix patch.

## PR awaiting attention

**PR #1904 — `fix(vesum_gate): MC distractor + pronunciation transcription awareness`** (vesum-gate-distractor-awareness dispatch, completed 511s).

CI status: **all blocking checks pass EXCEPT gitleaks transient infra fail**:
- ✅ Test (pytest) — 4m24s
- ✅ Lint (ruff)
- ✅ Quality Gates (radon)
- ✅ Frontend, Lesson Schema Drift, Lint Prompts, No new root scripts
- ✅ CodeQL ×3
- ❌ Secret Scanning (gitleaks) — `docker: Error response from daemon: Get "https://ghcr.io/v2/": net/http: request canceled (Client.Timeout exceeded while awaiting headers)` — exit 125. Transient Docker GHCR pull timeout, not a real secret detection.
- ❌ Gemini-Dispatch `review / review` — advisory, non-blocking per #M-0.5.

**Action needed on resume:** re-run the failed `Secret Scanning` job. Two options:
1. Re-run via GitHub UI (Actions → workflow run → re-run failed jobs).
2. Push an empty commit: `cd .worktrees/dispatch/codex/vesum-gate-distractor-awareness && git commit --allow-empty -m "ci: rerun gitleaks (transient ghcr timeout)" && git push`.

After re-run passes, merge with `gh pr merge 1904 --squash --delete-branch`.

## #1900 finding — codex was working all along

Full report: `audit/2026-05-13-codex-mcp-visibility-investigation.html`.

**Root cause:** `scripts/agent_runtime/adapters/codex.py::_rollout_matches_plan` (lines 666-717) uses fail-fast return-on-first-match logic. Codex CLI 0.130.0 emits an `AGENTS.md` + `<environment_context>` envelope as a `user`-role message BEFORE the user's actual prompt. The matcher trips on this envelope, sees text ≠ `plan.stdin_payload`, returns False, and stops scanning — never reaches the real prompt.

Result: `_select_rollout_for_plan` returns None → `_read_latest_rollout_trace` returns empty → `parse_response` returns `tool_calls=[]` → pipeline reports `tool_calls_total=0`. Has been happening since commit `a5f96a2d28` (2026-04-15), pre-dating all 3 bakeoffs (2026-05-06, 05-08, 05-12).

**Empirical evidence:** the codex night-bakeoff rollout at `~/.codex/sessions/2026/05/12/rollout-2026-05-12T02-24-04-019e1991-c63e-7a33-8641-b8c35c36fbc7.jsonl` contains 8 `response_item/function_call` events + 8 `event_msg/mcp_tool_call_end` events with successful results.

**Fix:** issue #1903 has the reproducer + fix patch — iterate-all instead of fail-fast. Codex dispatch in flight.

## Carry-over queue (priority-ordered)

| # | Item | State |
|---|---|---|
| 1 | Re-run gitleaks on PR #1904, merge if green | ⏸ Blocked on token permission; manual UI rerun or empty-commit push |
| 2 | Monitor + merge `writer-telemetry-result-summary` PR when CI green | 🔄 In flight |
| 3 | Monitor + merge `1903-rollout-matcher-fix` PR when CI green | 🔄 In flight |
| 4 | **After all 3 fixes merge:** re-eval night-bakeoff artifacts against fixed pipeline | 📋 P0 — unblocks publication path |
| 5 | Re-process codex rollout through fixed matcher (#1903 outcome) → see codex's 8 MCP calls counted | 📋 Then compare claude vs codex artifacts on equal footing |
| 6 | Update ADR `2026-05-06-writer-selection-codex-gpt55.md` with truthful state (REVISED was based on false evidence) | 📋 After both artifacts re-eval'd |
| 7 | **Decide a1/my-morning publication source** (claude artifact, codex artifact, or fresh rebuild) | 📋 Depends on #6 |
| 8 | Begin work on #1905 replay-mode regression suite | 📋 #1865 EPIC scope; structural fix to prevent this class of bug |
| 9 | Autonomous-dispatch decision card (`docs/decisions/pending/2026-05-12-autonomous-codex-dispatch-narrow-class.md`) | 📋 Still pending signoff |
| 10 | MEMORY budget at 148/150 (this session reduced from 160) | ✓ Within budget. Adjust handoff thresholds per user feedback this session — see "Handoff economics" below. |
| 11 | Worktree cleanup: 3 worktrees open (vesum-gate, writer-telemetry, 1903) | 📋 After PRs merge |

## Handoff economics — proposed MEMORY update

Per user feedback this session: handoffs cost ~20-35K tokens (write brief + cold-start next session + re-orient). When the next action is "monitor dispatches," ScheduleWakeup in the SAME session is zero-cost. Current MEMORY #2 thresholds (300K early signal, 400K handoff zone) are too aggressive.

**Proposed update to MEMORY #2:**
- Below 400K: stay in session; use ScheduleWakeup for monitoring; no handoff.
- 400-500K: handoff only at natural breaks (task complete, switching topics).
- 500K+: handoff zone (context heavy enough that fresh-start gains outweigh setup cost).
- Auto-compact at 750K still strictly forbidden (#2, destructive).

Encode this update in MEMORY.md on resume (or directly in this session before yielding).

## Decision cards still pending

| File | Status | Action needed |
|---|---|---|
| `2026-05-12-autonomous-codex-dispatch-narrow-class.md` | PROPOSED | Pick A/B/C/wait. |
| `2026-05-09-decision-graph-view.md` | PROPOSED | channels.html UI toggle. |
| `2026-05-06-multi-ui-channel-participation.md` | PROPOSED | Agent bridge multi-surface identity. |

## Open issues touched this session

- #1900 ✅ closed (codex MCP visibility, investigation complete)
- #1901 ✅ closed (OSError fix merged via #1902)
- #1903 📋 open — rollout-matcher fix (Codex dispatch in flight)
- #1905 📋 open — pipeline replay-mode regression suite (filed today)
- ADR `2026-05-06-writer-selection-codex-gpt55.md` — REVISED status needs reconsideration after fixes land

## Predecessor brief

`docs/session-state/2026-05-13-morning-actual-outcomes-brief.md` — morning session's pre-fix orientation. Read for the #M-8 (orchestrator-active) origin story.

---

*Format spec: `claude_extensions/rules/workflow.md` § "Two-tier handoffs". Companion HTML: `2026-05-13-midday-pipeline-gate-fixes.html`.*
