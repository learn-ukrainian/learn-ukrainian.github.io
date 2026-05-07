# Session Handoff — 2026-05-06 evening (Path A: unblock + bakeoff)

> **Predecessor:** `docs/session-state/2026-05-06-runbook-strand-1-and-bakeoff-validation.md` (the runbook this session is executing)
> **Goal:** unblock Claude headless dispatch (#1754), ship strand-1 (#1720), re-run bakeoff, propose writer-selection. Then A1 building unlocks for next session.
> **User context:** "i can not be always here, you need to be able to work without me." Operate autonomously. Don't ask permission for in-plan execution.
>
> **Anthropic peak-limit removed (2026-05-06 evening).** Headless Claude dispatches are no longer billing-constrained. Once #1754 lands, use Claude dispatches freely for adversarial reviews + parallel analyses. The 2-Claude-in-flight cap from #M0 stays as a *quality* choice (parallel review fan-out is hard to absorb), not a billing one. Raise only on explicit user request.

---

## State at handoff write time (~23:50 UTC 2026-05-06)

### Two Codex dispatches in flight

| task_id | issue | worktree | hard_timeout | started | ETA |
|---|---|---|---|---|---|
| `1754-keychain-user-env` | #1754 (Claude headless OAuth — USER env var) | `.worktrees/dispatch/codex/1754-keychain-user-env` | 1800s | 23:47 UTC | ~30 min from start |
| `1720-strand-1` | #1720 (tool-theatre detection) | `.worktrees/dispatch/codex/1720-strand-1` | 5400s | ~23:50 UTC | ~90 min from start |

**Monitor armed:** task `bxvdn232a` watches `batch_state/tasks/dispatch_events.jsonl` and emits one notification per terminal event (started/done/failed/timeout) for both task IDs.

### Root cause already diagnosed for #1754

Empirically validated by orchestrator (no need to re-investigate):

```bash
# FAILS:
env -i HOME=$HOME PATH=$PATH claude -p "say PONG"  →  "Not logged in"

# WORKS:
env -i HOME=$HOME PATH=$PATH USER=$USER claude -p "say PONG"  →  "PONG"
```

macOS keychain access requires `$USER`. The Codex brief at `docs/dispatch-briefs/2026-05-06-1754-claude-keychain-user-env.md` instructs the 2-line allowlist add + tests + docs.

### Pre-existing strand-1 brief

`docs/dispatch-briefs/2026-05-06-1720-strand-1-tool-theatre.md` — written by an earlier session, reviewed and used for the dispatch. Don't rewrite.

---

## Action plan when each dispatch lands

### When Monitor reports `1754-keychain-user-env` terminal:

1. **If `done`:** check `gh pr list --head codex/1754-keychain-user-env --json number`. Read the PR diff. Verify it adds `USER` + `LOGNAME` to `_SAFE_NAME_ALLOWLIST` in `scripts/agent_runtime/env_sanitize.py` and includes tests. Smoke-test the fix from this checkout:
   ```bash
   .venv/bin/python scripts/delegate.py dispatch \
       --agent claude --model claude-haiku-4-5 --mode read-only \
       --task-id smoke-1754-postfix --hard-timeout 90 \
       --prompt "say only PONG"
   ```
   Expect status `done` and stdout containing PONG. If yes → squash-merge PR, delete branch, remove worktree, `git pull` main. Close #1754.

2. **If `failed` or `timeout`:** read the dispatch output file at `/tmp/claude-501/-Users-krisztiankoos-projects-learn-ukrainian/<session>/tasks/<task-id>.output`. Diagnose. The fix is genuinely 2 lines, so failure mode is most likely (a) Codex couldn't find the file, (b) tests broke something else, (c) sandbox refused a syscall. Re-dispatch with corrections.

### When Monitor reports `1720-strand-1` terminal:

1. **If `done`:** PR opens. **Do BOTH reviews per workflow rule:**
   - (a) Inline orchestrator review of the diff. Focus on the 5 risk areas in the brief: citation extraction scope, tool-family normalization, correction-pass binary choice, telemetry shape, prompt scaffolding test.
   - (b) Headless adversarial Claude review (this UNBLOCKS once #1754 fix lands — peak-limit is now removed so this is the preferred path, saves orchestrator context):
     ```bash
     .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-claude \
       "Adversarial review for #1720 strand 1. Read /tmp/strand-1-pr-diff.txt." \
       --task-id 1720-strand-1-postpr-review
     ```
   - Findings → comment on PR. Clean → squash-merge, delete branch, pull main.

2. **If `failed`/`timeout`:** if it timed out at 5400s the work is likely non-trivial. Read `.worktrees/dispatch/codex/1720-strand-1/` to see what landed; if substantial work is committed, push to a draft PR and finish the rest in a follow-up dispatch. If nothing committed, re-dispatch with a tighter scope (just the detection function + tests, defer prompt+correction-pass to a follow-up).

---

## After both fixes land — fire the bakeoff

The bakeoff brief at `docs/dispatch-briefs/2026-05-05-bakeoff-full-execute.md` is unchanged and still valid. Fire:

```bash
.venv/bin/python scripts/delegate.py dispatch \
    --agent codex \
    --task-id bakeoff-validation-2026-05-06 \
    --worktree .worktrees/dispatch/codex/bakeoff-validation-2026-05-06 \
    --base main \
    --mode danger \
    --effort medium \
    --hard-timeout 7200 \
    --prompt-file docs/dispatch-briefs/2026-05-05-bakeoff-full-execute.md
```

Expected runtime: 25–90 min. Monitor will fire on terminal event (re-arm with task_id `bakeoff-validation-2026-05-06`).

---

## When bakeoff finishes — interpret REPORT.md

Per Step 4 of the runbook (`2026-05-06-runbook-strand-1-and-bakeoff-validation.md`):

1. **Strand fixes hold?** Per-writer `phase_writer_summary` events:
   - Strand 2 (end_gate present), Strand 3 (writer publishes module.md), Strand 1 (`tool_theatre_violations: []` AND `tool_calls_total > 0`).
   - If ALL green for ≥1 writer → proceed to step 2.
   - If strand 1 still red → diagnose with JSONL, file follow-up issue.

2. **Cross-reviews scored?** Each `*-*.review.jsonl` should have `score`, `evidence_quotes` (3+), `rubric_mapping`, `verdict`. No `reviewer_fixes_unparseable` events.

3. **Per-writer winner?** Look at `audit/bakeoff-2026-05-05/REPORT.md` aggregator output:
   - Winner = `min_dim ≥ 8` AND `weighted_score ≥ 8.5` AND `tool_call_density > 0.5/100w`.

---

## When a winner emerges — propose writer-selection to user

This is the only thing requiring user sign-off. Draft the proposal as a comment on EPIC #1577:

> **Writer selection per `docs/decisions/2026-04-26-reboot-agent-responsibilities.md` §3:**
> Bakeoff at `audit/bakeoff-2026-05-05/REPORT.md` (run X, validated end-to-end with strands 1+2+3 active) shows {WINNER} as best on min_dim={X}, weighted={Y}, tool_call_density={Z}/100w. Recommend locking {WINNER} as V7 module writer. Update `pipeline.md` rule + `memory/MEMORY.md` after sign-off. **A1 building unlocks on user `go`.**

Stop and wait for sign-off. Per ADR + runbook line 331: do not start A1 module building before user signs off on the writer choice.

---

## Side cleanup that's safe to do autonomously

- **Stale worktree** `.worktrees/codex-interactive` (detached HEAD, dirty, from 2026-04-06). Safe to nuke if user hasn't asked to rescue: `git worktree remove .worktrees/codex-interactive --force`. Do this only after confirming no active work — check with `git -C .worktrees/codex-interactive status`.
- **Inbox message** `d7f11607...` — body "hello its a me", looks like a test ping. Mark as read: `ab inbox ack d7f11607...` (or equivalent).

---

## Things NOT to do tonight

- **Do not start A1 module building.** The runbook explicitly forbids it before writer-selection sign-off. The whole point of Path A is to make A1 building trustworthy.
- **Do not modify the strand-1 brief.** It was written carefully by an earlier session.
- **Do not change the branch in the main checkout.** Worktree rule. Both dispatches are isolated.
- **Do not poll dispatches manually.** Monitor `bxvdn232a` is armed — wait for notifications.
- **Do not skip the headless-Claude post-fix review of strand-1.** Two-agent gate is a hard rule. If #1754 still pending when strand-1 lands, do inline-only review and note it in the PR.

---

## Failure paths

- **Both dispatches fail:** diagnose, re-dispatch with corrections. Don't escalate to the user unless re-dispatches also fail or the failure mode is novel.
- **Bakeoff still doesn't validate after strands 1+2+3:** the runbook's Failure Budget section (line 312) says: don't change the writer-bakeoff approach until at least one fair bakeoff has run. We've never had one, so this run is the gate.
- **Monitor stops emitting:** check with `curl -s http://localhost:8765/api/orient | jq .delegate`. If dispatches are still alive, Monitor probably crashed; re-arm.

---

## Emergency stop conditions (escalate to user)

- Worktree rule violated (main checkout HEAD ≠ main).
- Anthropic budget alarm in #M0 ("claude usage is hot" signal).
- Bakeoff produces structurally broken output (no per-writer dirs, no REPORT.md) — this would be a #1577 EPIC regression.
- Any dispatch crashes with an uncaught exception that mentions credentials or token leakage.
