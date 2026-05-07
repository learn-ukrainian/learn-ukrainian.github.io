# Session Handoff — 2026-05-07 (bakeoff blockers cleared, first attempt failed, prompt fix in flight)

> **Predecessor:** `docs/session-state/2026-05-06-tonight-path-a-orchestration.md`
> **Mode:** Long arc. Started ~08:30 CET diagnosing the keychain auth bug. Closed ~18:00 CET after first bakeoff attempt failed and prompt-fix PR is awaiting CI.

---

## TL;DR

**10 PRs merged, 6 follow-up issues filed, 1 bakeoff attempt failed.** The bakeoff infrastructure is now mature; the first-attempt failure was a prompt-discipline bug (Claude wrote a meta-summary instead of artifact fences), not infrastructure. PR #1781 (HARD STOP RULE) is the fix. After it merges, retry the bakeoff with `--silence-timeout 3600`.

---

## Merged today (10 PRs)

| PR | Closes | What |
|---|---|---|
| #1763 | #1758 | `delegate.py --silence-timeout` default 600s → 1800s |
| #1766 | #1764 | Crawler: drop CC-only filter + title-pattern discovery |
| #1767 | #1761 | `Result.tool_calls` exposed; 3-adapter trace capture |
| #1757 | #1725 | Verbatim textbook quoting gate (with WARN→REJECT revert per Gemini's BLOCK_PEDAGOGY) |
| #1769 | #1765 | Plan-review-time corpus-availability check |
| #1772 | #1661 #1673 | Structured CoT + grammar-claim grounding + verification_trace + end_gate |
| #1775 | #1768 | Trace-capture contamination fixes (Gemini cross-contam, Codex prompt-echo, Claude format-fragility) |
| #1776 | #1773 | Bakeoff aggregator: theatre-aware winner gate (min(dim) not weighted) |
| #1777 | #1771 | ruth.yaml YAML parse error fix |
| #1780 | #1774 | A1 resource backfill (Anna's videos + 11-module index sync) |
| #1760 | #1754 | Earlier this morning — env_sanitize keychain USER+LOGNAME |

---

## Open at handoff

### 1 PR open

| PR | Branch | Status | Action |
|---|---|---|---|
| **#1781** | `codex/bakeoff-prompt-fix` | OPEN, 8 pending CI | Wait for CI → merge → re-fire bakeoff |

### 6 issues open

| # | What | Status |
|---|---|---|
| #1577 | EPIC: A1+A2+B1 vertical slice | umbrella, closes when A1+A2+B1 ship |
| #1657 | EPIC: MCP verification 3-phase plan | umbrella, multi-phase |
| #1762 | Code scanning: dismiss 12 alerts | **YOUR UI action** — pre-written rationales |
| #1770 | 32 plans cite missing textbooks | workstream — Gemini triage attempt failed at 0 chars; retry needed |
| #1778 | check_plan.py doesn't handle track-level plans | small follow-up |
| #1779 | Bridge inbox is purely pull-based | architectural — TTL + orient surfacing + wake-on-dispatch |

---

## Bakeoff attempt #1 — what failed

`audit/bakeoff-2026-05-07/` (committed as evidence in `ff4dda023d`):

- **Claude:** wrote a 474-byte meta-summary ("Module a1-020 drafted under Phase 4 protocol... Four `<plan_reasoning>` blocks, four artifact fences, and one `<end_gate>` block emitted...") **instead of** the 4 required artifact fences. Trace-capture worked perfectly (9 tool calls, 5 verify_words, 0 theatre violations). The new structured CoT scaffolding from #1772 + 117KB prompt size lost output focus.
- **Gemini:** only emitted plan + knowledge_packet phase_done events. Likely stalled on slow CLI startup; probably would have produced same meta-summary failure.
- **Codex:** never ran — serial execution killed by silence-timeout before its turn.
- **Dispatch killed at 1801s** — silence-timeout default fired after Claude's failure cascade + Gemini's slow startup.

### What the failure proved
- Trace-capture infrastructure (#1761, #1768): WORKS perfectly
- Aggregator (#1773): never ran (no REPORT.md generated)
- Verbatim-quoting gate (#1725): never engaged (no artifact to gate)
- The pre-bakeoff Claude validation reviews caught the right things — they just couldn't predict prompt drift

### What the failure caused
- PR #1781 (HARD STOP RULE) — appends explicit "no summary, no status, no meta-commentary after `<end_gate>`" rule
- Future bakeoff dispatches need `--silence-timeout 3600` (1h) explicitly — bakeoff serial 3-writer execution legitimately has long silent stretches between writers

---

## Critical path to A1 (next session)

1. **Wait for #1781 CI** — should be MERGEABLE within minutes if not already.
2. **Merge #1781.** Cleanup worktree. Pull main.
3. **Re-fire bakeoff:**
   ```bash
   .venv/bin/python scripts/delegate.py dispatch \
       --agent codex \
       --task-id bakeoff-2026-05-07-retry \
       --worktree .worktrees/dispatch/codex/bakeoff-2026-05-07-retry \
       --base main \
       --mode danger \
       --effort medium \
       --hard-timeout 7200 \
       --silence-timeout 3600 \
       --prompt-file docs/dispatch-briefs/2026-05-07-bakeoff-execute.md
   ```
   **CRITICAL: pass `--silence-timeout 3600`** explicitly — the default 1800 killed the first attempt.
4. **Wait 60-90 min.** Bakeoff harness runs Claude → Gemini → Codex serially + 6 cross-reviews + aggregate.
5. **When REPORT.md lands** in `audit/bakeoff-2026-05-07-retry/`:
   - Verify the new aggregator sections per #1773: top-level "Winner ranking by tool-call density" + theatre-violation row in writer-prompt table + REVIEWER PROTOCOL BROKEN banner if any
   - Open the pre-crafted writer-selection proposal at `/tmp/writer-selection-proposal-template.md` (Claude crafted it earlier today)
   - Fill in the placeholders with REPORT.md data
   - Post as comment on EPIC #1577
6. **Wait for user signoff** on the writer choice.
7. **After signoff:** A1 module building unblocks. Update `pipeline.md` rule + `memory/MEMORY.md` per the proposal's "Conditions of acceptance" section.

---

## What did NOT work + lessons

### `ask-claude --model` flag
The local `ask-claude` accepts `--to-model`, NOT `--model`. The brief said `--model`. Codex caught this in its #1761 work. Future briefs must say `--to-model`.

### `gh` auth in dispatch subprocesses
Codex consistently couldn't open PRs (`HTTP 401: Bad credentials`). I had to open every PR inline from the orchestrator. Investigated in #1779 (bridge architecture issue partially covers this); proper fix is in the GH_TOKEN scope handling at dispatch time. Workaround: orchestrator opens PRs from main checkout where the broader-scope `.envrc` GH_TOKEN is available.

### Bridge inbox rot
4 channel deliveries pending, oldest 2.3 days. Pull-based architecture means messages rot until manually drained. Orchestrator drained via DB update; #1779 filed for proper fix (TTL + orient surfacing + wake-on-dispatch).

### Gemini silent failures
`1770-32-plan-triage` ran 1212s and emitted 0 chars. Likely token-limit or context overflow on the long prompt. Retry needed with shorter prompt.

### Silence-timeout for bakeoff
1800s default is fine for normal Codex dispatches but NOT for the bakeoff harness (which has serial-writer silent stretches). Always pass `--silence-timeout 3600` for bakeoff dispatches. Could codify as a per-task default in delegate.py.

---

## Pre-crafted artifacts (use these, don't recreate)

- `/tmp/writer-selection-proposal-template.md` — fill placeholders with REPORT.md data, post on EPIC #1577 for user signoff
- `docs/dispatch-briefs/2026-05-07-bakeoff-execute.md` — bakeoff dispatch brief (UPDATE: pass `--silence-timeout 3600` when re-firing)

---

## Cross-thread notes (still active)

- **Anthropic peak-limit removed (2026-05-06):** Headless Claude dispatches no longer billing-constrained. 2-Claude-in-flight cap from #M0 stays as a quality choice.
- **Stale `.worktrees/codex-interactive` removed** (was 1 month dirty/detached; safe-deleted today).
- **Stash entry dropped** — was 2 resource files with metadata that conflicted with #1774; merged conflict resolution preserved richer metadata in `ff4dda023d`.

---

## Repo state at handoff

- main: `ff4dda023d`
- Worktrees: 1 active (`bakeoff-prompt-fix` — PR #1781 will close it)
- 1 dispatch in flight: prompt-fix worker just landed; PR opened
- All Codex/Claude/Gemini slots free
- No stash, no uncommitted state

---

## What the next session should do FIRST

1. Read this file (you're doing it)
2. Check PR #1781 CI status: `gh pr view 1781 --json mergeable,statusCheckRollup`
3. If MERGEABLE: `gh pr merge 1781 --squash --delete-branch --admin`
4. Pull main, cleanup worktree
5. Fire bakeoff retry per the command in "Critical path to A1" step 3
6. Monitor with `Monitor` tool watching `bakeoff-2026-05-07-retry` task ID
7. When REPORT.md lands → fill template → propose to user
