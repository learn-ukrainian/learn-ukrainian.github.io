# Session Handoff — 2026-04-26 autonomous orchestration

> **Predecessor:** `2026-04-26-overnight-claude.md`
> **Mode:** Autonomous orchestration while user is away. User said 12:01 CET: "i will be back later, work auto pls". Continuing the reboot work per the policy clarified earlier (Gemini for wiki, Claude+Codex for coding/architecture/organizing, module writer TBD).

---

## TL;DR for the user when you return

1. **Wiki rebuild a1+a2+b1 committed** (`b7db136b1d`) with 0/218 orphan-citation verification. Pushed to main.
2. **Reboot agent-responsibilities ADR landed** (`b532271f3d`) — `docs/decisions/2026-04-26-reboot-agent-responsibilities.md`, plus inline cleanups to `pipeline.md`, `ARCHITECTURE.md`, `v6_build.py` legacy markers.
3. **Two Codex refactor dispatches in flight** (max 2 cap = exactly fits). Both follow directly from the ADR.
4. **Phase 4 round-2 brief drafted and parked** — dispatchable as soon as both Codex refactors merge + PR #1594 merges.
5. **Bio/hist/lit + b2 Gemini wiki rebuilds still running** — slow (~10-15% in 1.5h); not blocking anything.

---

## What landed (commits since session start)

```
b532271f3d  docs(reboot): ADR for agent responsibilities + V5/V6 legacy markers (#1577)  ← THIS SESSION
b7db136b1d  chore(wiki): rebuild a1+a2+b1 post citation-shift fix (#1591, #1592)        ← THIS SESSION
d102a79887  feat(thresholds): per-level per-dim LLM QG floors (#1586) (#1593)           ← overnight
04aae723ab  fix(wiki): dedup sources before prompt to align body citations with registry (#1591) (#1592)  ← overnight
d79457e5e9  phase-3: lesson schema and prompt substitution (#1590)
67741940dd  feat(wiki): multi-agent writer support for compile.py (#1569) (#1589)
```

`origin/main` is at `b532271f3d` (this session's HEAD).

---

## What's IN FLIGHT right now

### Codex dispatch 1 — Writer parameterization (ADR §1 cleanup)

- **Task ID:** `codex-phase4-writer-decouple`
- **Worktree:** `.worktrees/codex-phase4-writer-decouple`
- **Branch:** `codex/phase4-writer-decouple` branched from `origin/codex/phase-4-a1-20-exemplar` (PR #1594's branch)
- **PR target on completion:** stacked PR with base = `codex/phase-4-a1-20-exemplar` (NOT main)
- **Worker pid:** 55493 (`gpt-5.5`, effort `high`, hard-timeout 4h)
- **Brief:** `.worktree-briefs/codex-phase4-writer-decouple.md`
- **Watcher:** background task `b4qf8sj91`
- **What it does:** parameterizes `linear_pipeline.py:202-226` writer (currently hardcoded `claude-opus-4-7`); routes through `scripts.agent_runtime.runner.invoke` with a `WRITER_DEFAULTS` lookup dict for `claude-tools` and `gemini-tools`.

### Codex dispatch 2 — VESUM symlink in delegate.py (ADR §97 cleanup)

- **Task ID:** `codex-delegate-vesum-symlink`
- **Worktree:** `.worktrees/codex-delegate-vesum-symlink`
- **Branch:** `codex/delegate-vesum-symlink` branched from `origin/main`
- **PR target on completion:** new PR with base = `main`
- **Worker pid:** 46612 (`gpt-5.5`, effort `high`, hard-timeout 4h)
- **Brief:** `.worktree-briefs/codex-delegate-vesum-symlink.md`
- **Watcher:** background task `bye0gyzmd`
- **What it does:** adds `_provision_data_symlinks(...)` helper to `scripts/delegate.py` and wires it into `_ensure_worktree()` (lines 433-444 fresh path; reused-worktree path at 405-413 backfills via idempotency). Symlinks `data/vesum.db` (923 MB) + `data/sources.db` (1.5 GB) from main checkout into delegated worktrees. Adds `tests/test_delegate_data_symlinks.py`.

### Wiki rebuilds (user-launched at ~10:38-10:48 CET, all `--writer=gemini`)

| Track | PID | Progress (rebuilt-since-10:30 / total) | ETA |
|---|---|---|---|
| bio (`wiki/figures/`) | 6803 | 27 / 180 | ~8h more at current pace |
| hist periods (`wiki/periods/`) | 13629 | 16 / 140 | ~14h more |
| hist historiography (`wiki/historiography/`) | 13629 | 0 / 136 | runs after periods |
| lit (`wiki/literature/works/`) | 13598 | 18 / 232 | ~18h more |
| b2 (`wiki/grammar/b2/`) | 56100 | unknown / 89 | ~ |

These are slow. Not blocking anything reboot-related — Phase 4 only needs `wiki/pedagogy/a1/`, which is already done and committed (`b7db136b1d`).

---

## Phase 4 round-2 brief — drafted, parked, NOT dispatched yet

**File:** `.worktree-briefs/codex-phase4-round2-live-exemplar.md`

**Pre-conditions for dispatch (all 3 must be on main):**
1. PR #1594 merged (Phase 4 scaffold, currently draft)
2. The follow-up PR from `codex-phase4-writer-decouple` merged (writer parameterization)
3. The follow-up PR from `codex-delegate-vesum-symlink` merged (worktree provisioning)

**What round 2 does:**
- Live writer call (default: `gemini-tools`; orchestrator can override at dispatch time per the ADR §3 policy)
- Real Python QG with REAL VESUM (now via symlink)
- 5 INDEPENDENT per-dim Codex LLM QG calls, validated for completeness, aggregated via `aggregate_review`
- MDX assembly + Starlight smoke test
- Write the round-2 exemplar report at `docs/phase-4-exemplar-report.md`
- Open new PR `codex/phase4-round2-live-exemplar` against main

**Writer choice:** the round-2 brief defaults to `gemini-tools` for the exemplar (matches the wiki-writer-is-Gemini policy + preserves Claude budget). The bakeoff between `claude-tools` and `gemini-tools` happens later per the ADR §3 criteria; round 2 just establishes a working baseline. Orchestrator can override to `claude-tools` if you want to start with Claude.

---

## Reboot phase ledger (current)

| Phase | Status | Anchor |
|---|---|---|
| 0 — North Star + Lesson Contract | ✅ done | `de97c45572` |
| 1 — Salvage manifest | ✅ done | (multiple) |
| 2 — Config audit (#1583) | ✅ done | `f0635c70ad` |
| 3 — Lesson schema + substitution (#1584) | ✅ done | `d79457e5e9` |
| #1586 — Per-level per-dim QG floors | ✅ done | `d102a79887` |
| #1591/#1592 — Wiki citation-shift fix | ✅ done; verified at scale | `04aae723ab` |
| Wiki rebuild a1+a2+b1 | ✅ done; committed | `b7db136b1d` |
| Wiki rebuild bio/hist/lit/b2 | 🔄 in flight (Gemini, slow) | — |
| **Reboot agent-responsibilities ADR** | ✅ done | `b532271f3d` |
| **4 round 1** — A1/20 scaffold | 🟡 PR #1594 draft; CI green except advisory Gemini-Dispatch | `d313499332` |
| **ADR cleanup #1** — writer decouple | 🟡 Codex dispatched (pid 55493) | — |
| **ADR cleanup §97** — VESUM symlink | 🟡 Codex dispatched (pid 46612) | — |
| **4 round 2** — live exemplar | ⏸️ brief parked; gated on cleanups + #1594 merge | — |
| 5+ — Fan-out | ⏸️ gated on Phase 4 ship | — |

---

## What the user comes back to

- If both Codex dispatches succeeded with clean PRs: review them, merge in order (writer-decouple PR first since it's stacked on #1594; then vesum-symlink PR; then ready PR #1594 for review and merge if everything's green; then dispatch round-2).
- If either Codex dispatch failed/timed out: the watcher will have surfaced a task-notification. I'll read the result file, decide whether to commit the partial work as a draft (pattern from overnight) or re-dispatch with a tightened brief.
- If wiki rebuilds finished bio/hist/lit/b2: I'll commit those in a follow-up commit similar to `b7db136b1d`.

---

## Update — 2026-04-26 ~12:10 CET: Both Codex dispatches DONE + merged

Both Codex jobs returned clean (10 min wall each, exit 0, NO worktree-dirty-on-exit this time):

- **PR #1595 (`codex/delegate-vesum-symlink`)** — VESUM + sources symlink in `delegate.py` worktree provisioning. 56 tests pass. Reviewed by orchestrator; merged at `8eb43d31...` to main (squashed). Worktree + branch cleaned up.
- **PR #1596 (`codex/phase4-writer-decouple`)** — `linear_pipeline.py:202-226` parameterized via `WRITER_CHOICES = ("claude-tools", "gemini-tools")` and `WRITER_DEFAULTS` lookup; routes through `runner.invoke` with `agent_name = writer.split("-", 1)[0]`. 42 tests pass. Stacked on PR #1594; reviewed and squash-merged into `codex/phase-4-a1-20-exemplar`. Worktree + branch cleaned up.

Both merges were `--squash`; advisory `🔀 Gemini Dispatch / review` failure was ignored per MEMORY policy.

### PR #1594 now updated and READY FOR REVIEW

- Branch tip moved from `d313499332` → `1221447a4d` (scaffold + decouple)
- PR description rewritten to reflect the new state: "Phase 4 round-1 scaffold (round 2 = separate PR)"
- Marked ready-for-review (no longer draft)
- CI re-running on the new commits; watcher `b3lr8ns77` in background

When CI completes, orchestrator merges PR #1594 to main (per merge-is-my-job policy unless the user explicitly wants to review first). After merge, `main` has the full Phase 4 round-1 scaffold and is dispatch-ready for round 2.

### Phase 4 round-2 dispatch prerequisites

After PR #1594 merges to main:
- All 3 Phase 4 prereqs are on main (#1595, #1596 squash, #1594)
- Round-2 brief at `.worktree-briefs/codex-phase4-round2-live-exemplar.md` is dispatchable

The round-2 dispatch command is at the bottom of that brief. Default writer is `gemini-tools` per the reboot ADR; orchestrator can override to `claude-tools` at dispatch time if user direction warrants.

---

## Update — 2026-04-26 ~12:15 CET: PR #1594 merged + Round 2 DISPATCHED

PR #1594 merged at `c91ae3bbe1` to main. CI was fully GREEN (19/19 SUCCESS, 0 failures — even the advisory Gemini-Dispatch passed). Worktree + branch cleaned up.

Phase 4 round 2 dispatched per the parked brief:

- **Task ID:** `codex-phase4-round2-live-exemplar`
- **Worktree:** `.worktrees/codex-phase4-round2-live-exemplar` (fresh, off origin/main)
- **Branch:** `codex/phase4-round2-live-exemplar`
- **Worker pid:** 27716 (`gpt-5.5`, hard-timeout 4h)
- **Default writer:** `gemini-tools` (per ADR §3 — exemplar baseline; bakeoff between writers happens later)
- **Watcher:** background task fires `<task-notification>` on terminal status

**VESUM symlinks verified in the worktree:**
- `data/vesum.db` → `/Users/krisztiankoos/projects/learn-ukrainian/data/vesum.db`
- `data/sources.db` → `/Users/krisztiankoos/projects/learn-ukrainian/data/sources.db`

PR #1595's `_provision_data_symlinks()` is working as designed. Codex round 2 has real VESUM access.

### What round 2 should produce

If everything works end-to-end:
- Real `module.md` + `activities.yaml` + `vocabulary.yaml` + `resources.yaml` written by `gemini-tools` against the linear-write prompt
- Real Python QG report at `audit/a1/my-morning.json` with VESUM gates green
- Real LLM QG report at `review/a1/my-morning.json` with 5 separate Codex per-dim calls + aggregated `ReviewVerdict`
- Final verdict: PASS (every dim ≥ A1 floor — pedagogical/naturalness/decolonization=9.0, engagement/tone=8.0)
- Annotated MDX at `starlight/src/content/docs/a1/my-morning.mdx`
- Round-2 exemplar report at `docs/phase-4-exemplar-report.md`

**REVISE/REJECT verdict path is fail-fast** — no LLM regen, no scoped fix, just surface findings. If round 2 lands REVISE/REJECT, that's a writer-prompt or plan signal that needs orchestrator attention before re-dispatching.

### Updated reboot phase ledger

| Phase | Status | Anchor |
|---|---|---|
| 0–3 | ✅ done | (as before) |
| #1586 | ✅ done | `d102a79887` |
| #1591/#1592 | ✅ done | `04aae723ab` |
| Reboot agent-responsibilities ADR | ✅ done | `b532271f3d` |
| Wiki rebuild a1+a2+b1 | ✅ done; committed | `b7db136b1d` |
| ADR cleanup #1 (writer decouple) | ✅ done | folded into `c91ae3bbe1` |
| ADR cleanup §97 (VESUM symlink) | ✅ done | `0f03c6acd0` |
| **4 round 1** — A1/20 scaffold | ✅ done | `c91ae3bbe1` |
| **4 round 2** — A1/20 live exemplar | 🟡 partial; PR #1597 draft | `d4e55974b3` |
| **4 round 3** — actual live exemplar | ⏸️ awaiting writer-output decision | — |
| Wiki rebuild bio/hist/lit/b2 | 🔄 in flight (Gemini, slow) | — |
| 5+ — Fan-out | ⏸️ gated on round 3 ship | — |

---

## Update — 2026-04-26 ~12:35 CET: Round 2 PARTIAL, autonomous mode stopped

Round 2 ran for 15.7 min. Live `gemini-tools` writer call completed in 68s but **the output failed YAML parsing** — `resources.yaml` block contained `notes: Зворотні дієслова: суфікс -ся(-сь) ...`, an unescaped colon mid-Cyrillic broke the parser. Codex correctly fail-fast'd per the brief's REVISE/REJECT-terminal rule. No Python QG, LLM QG, MDX, commit, push, or PR ran.

**But Codex shipped substantial infra during the dispatch:**
- Strict writer-output parser + review-response helpers (+174 LOC in `linear_pipeline.py`)
- Tightened writer + reviewer prompt templates to demand machine-readable fenced blocks
- **Real `agent_runtime` bug fix**: nested `AGENT_REAL_GIT` could point back to the shim, hanging Gemini startup with recursive `git --version` calls
- Pre-existing test debt fixes (gpt-5.4 → gpt-5.5; `_TEST_PYTHON` → `sys.executable`)

Orchestrator (Claude) committed Codex's work + the test-debt fixes at `d4e55974b3`, pushed `codex/phase4-round2-live-exemplar`, opened **draft PR #1597**. 124 tests passing, ruff clean. EPIC #1577 commented with the result.

### Why I stopped here (autonomous mode end)

Round 3 depends on resolving the writer-output reliability question. Three paths:

1. **Force JSON-only structured output** — JSON's escape semantics handle Cyrillic colons cleanly
2. **Switch round 3 to `claude-tools` writer** — see if the failure is writer-specific or prompt-shape-specific
3. **Bakeoff both writers in round 3** — matches ADR §3 criteria; most informative; most expensive

This is exactly the kind of architectural decision the user said they want to make personally ("Claude+Codex on coding/architecture/organizing… we will continue with our reboot... if we decide that claude will be writing a1 thats fine, we will adjust"). I do not unilaterally pick path 1/2/3.

Round 3 dispatch is held. PR #1597 is draft. Bio/hist/lit/b2 Gemini wiki rebuilds still slow-grinding in background (no orchestrator action needed there).

### What's left for the user when they return

1. Read the EPIC comment (most recent on #1577) — full round-2 narrative
2. Pick path 1, 2, or 3 for round 3 (or propose path 4)
3. Optional: review PR #1597's infra changes; merge whenever (the changes are independent of round-3 path)
4. Optional: review and commit the in-flight bio/hist/lit/b2 Gemini wiki rebuilds when they finish (mirror the `b7db136b1d` pattern)

---

## Cold-start protocol if I drop context before Codex finishes

1. `gh pr list --search "codex-phase4 OR delegate-vesum-symlink"` — see if either Codex pushed a PR
2. `.venv/bin/python scripts/delegate.py status codex-phase4-writer-decouple` and `status codex-delegate-vesum-symlink` — current state
3. `git -C .worktrees/codex-phase4-writer-decouple log --oneline HEAD..origin/codex/phase-4-a1-20-exemplar` — what was committed (empty if dirty-on-exit)
4. `git -C .worktrees/codex-delegate-vesum-symlink log --oneline HEAD..origin/main` — same
5. If dirty-on-exit on either: read the result files at `batch_state/tasks/codex-phase4-*.result`; commit the work as a draft if substantial (overnight pattern)
6. If both PRs landed clean and merged: dispatch the round-2 brief at `.worktree-briefs/codex-phase4-round2-live-exemplar.md`

---

## Background watchers active at handoff time

- `b4qf8sj91` — `delegate.py wait codex-phase4-writer-decouple`
- `bye0gyzmd` — `delegate.py wait codex-delegate-vesum-symlink`

Both fire `<task-notification>` on terminal status (done / failed / timeout / cancelled).

---

## Worktrees at handoff write time

```
/Users/krisztiankoos/projects/learn-ukrainian                                      b532271f3d [main]
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/codex-interactive         3c8bc39bae (detached HEAD)
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/codex-phase-4-a1-20-exemplar     d313499332 [codex/phase-4-a1-20-exemplar]
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/codex-phase4-writer-decouple     (in flight) [codex/phase4-writer-decouple]
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/codex-delegate-vesum-symlink     (in flight) [codex/delegate-vesum-symlink]
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/verify-a1-1-phaseA-v5            ab3178fb64 [verify/a1-1-phaseA-v5]
```

`codex-interactive` and `verify-a1-1-phaseA-v5` are stale; safe to clean up later.

---

## Open architectural questions still pending user decision

1. **Module writer choice for Phase 5+ batch fan-out** — explicitly deferred per ADR §3; decide via strict bakeoff using the round-2 exemplar.
2. **PR #1594 merge timing** — should ideally merge AFTER the writer-decouple stacked PR is approved, since the stacked PR depends on PR #1594 existing as a base. Two viable orderings:
   - (a) Merge writer-decouple PR into the #1594 branch first (turns it into a single combined PR), then ready #1594 for review
   - (b) Keep them stacked, merge #1594 first (reviewing scaffold separate from refactor), then merge writer-decouple second
3. **Module writer round-2 default** — the round-2 brief defaults to `gemini-tools` per the wiki-writer-policy logic; orchestrator can override to `claude-tools` if you want to start with Claude. Either is defensible.
