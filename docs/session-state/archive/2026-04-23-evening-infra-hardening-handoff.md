# Session Handoff — 2026-04-23 evening: infrastructure hardening + postmortem response

> **TL;DR** Phase 1 of EPIC #1451 is closed. Anthropic April-23 postmortem
> response landed. Three infrastructure wins merged: branch protection on
> main, `delegate.py` hardening (stale-base bug class fixed), CI speedup
> (9-10 min → 4m30s on pytest). Next session should clear three things
> before touching anything new: ADR #1456 sign-off, #1454 P2-A dispatch,
> and the 2 Codex invariant-test parallelizable issues. Colors rebuild
> is **NOT** ready to fire — 4 merges + ADR + pilot away.
>
> **Read this whole file before dispatching anything.**

---

## What landed this session (merged to main, newest first)

| PR | Issue | What | Impact |
|---|---|---|---|
| #1477 | #1475 | dispatch telemetry — log `agent`/`model`/`effort`/`cli_version` | observability before GPT-5.5 rollout; correlate quality vs model switch |
| #1483 | — | `sys.executable` → `.venv/bin/python` across 8 scripts | explicit interpreter contract; unblocked #1477 CI |
| #1482 | #1479 | CI speedup bundle (pytest-xdist `-n auto` + pip cache + skip coverage on PRs) | pytest 9-10 min → **4m30s** (validated on #1477 post-rebase CI) |
| #1478 | #1476 | `delegate.py` dispatch hardening — fetch-first + branch normalize + reuse validation + `dispatch/` subtree | kills stale-base bug class; no more `codex/codex-*` doubled prefixes |
| #1473 | #1453 | **P1-B sidecar freshness invariant** + PEP 562 lazy path constants | ✅ **closes EPIC #1451 Phase 1** |
| #1474 | #1472 | Postmortem must-change: model → `claude-opus-4-7`, pin `--effort=xhigh`, CLI ≥ 2.1.116 gate, route `supports_effort` via helper | silent-default inheritance path closed |
| #1468 | #1452 | **P1-A alignment manifest hash contract** + 4 gemini-review nits | Phase 1 half |
| #1470 | #1469 | test-fixture schema init for `test_unresolvable_entries_are_logged_to_stderr` | unblocked red main |

**Governance:** branch protection on `main` applied. `Test (pytest)` required, force-push + delete disabled, `enforce_admins=false` so user can hotfix.

**Worktree state at handoff:** only `codex-interactive` (user's live Codex), `codex-1286-review-transport` (preserved, blocked on upstream Codex 0.122.0), and `codex-ci-speedup` residue. Everything else cleaned.

---

## Critical corrections to earlier session framing

These are things the earlier handoff / my own words got wrong. **Next session's Claude: READ THIS, don't revert.**

### 1. Colors rebuild is NOT "ready to fire"
Earlier handoff said `Phase 5 — Colors rebuild | ⏳ unblocked, ready to fire`. User called bullshit. I agreed. **Real gate list:**

- [x] #1474 (postmortem: 4-7 + effort xhigh) — merged
- [x] #1473 (sidecar freshness) — merged
- [ ] **#1454 P2-A threshold unify** — not started; ADR explicitly gates colors rebuild on this
- [ ] **ADR #1456 sign-off** by user — drafted by Opus today, awaits decision
- [ ] **1-module pilot** before any batch

Do NOT fire `v6_build.py a1 10 --writer claude-tools --reviewer codex-tools` until all four are checked. The silent-default/split-brain would bite us the same way we just spent a day diagnosing.

### 2. The `🔀 Gemini Dispatch / review` bot is OURS, not Google's
Earlier framing: "disable the bot, we don't control it." Reality: it's `.github/workflows/gemini-review.yml` + `.github/commands/gemini-review.toml` — **our workflow file, our prompt.** The bot's generic "world-class autonomous code review agent" prompt is editable. We should UPGRADE it (inject project rules, CLAUDE.md, ADRs) not disable it. Open backlog: file issue to upgrade the gemini-review.toml prompt with project-specific discipline. Today it caught 4 real issues on PR #1468 — proven value when we actually read its comments.

### 3. Codex dispatch output IS observable
MEMORY said Codex is a black box. Wrong — there's a full rollout JSONL at `~/.codex/sessions/YYYY/MM/DD/rollout-<timestamp>-<uuid>.jsonl` per dispatch. Every `exec_command`, `reasoning`, `function_call_output` is captured. Use this to tail in-flight dispatches. Recipe in MEMORY.md under "CODEX DEBUG — SESSION HISTORY."

### 4. CI 9-10 min is NOT inherent; it's a choice
We ran full pytest sequentially with coverage on every PR. `-n auto` + pip cache + skip-cov-on-PR cut it to 4m30s. No rocket science. Next session: don't accept slow CI as "just how it is."

---

## Open decisions for Krisztian (you)

1. **ADR #1456 sign-off.** `docs/decisions/2026-04-23-rewrite-strategies-kill-or-revert.md` drafted by Opus. 3 questions await decision:
   - Delete writer-swap entirely vs. keep manual `--writer-override` CLI?
   - Accept WORD_BUDGET ERROR → terminal (no auto-recovery)?
   - Hold ADR ACCEPTED until #1454 P2-A lands? (Opus-recommended default: yes)
2. **Postmortem Q (noted but not blocking):** audit `--exclude-dynamic-system-prompt-sections` usage?
3. **Stale starlight content patch** at `.worktree-briefs/stale-starlight-content-changes-from-1473-worktree.patch` (60 lines). Not authored by Claude or Codex — surfaced from an earlier session. Tries to flip `a1/colors status: "locked" → "active"` which contradicts today's finding that colors is NOT ready. **Recommendation: discard that specific hunk; review the special-signs subtitle change.**
4. **`_run_review_heal_loop` verify** — Opus marked it `<!-- VERIFY -->` likely-dead-code in the ADR. 5-min code trace would confirm; closes a migration-plan simplification for the ADR.

---

## Roadmap snapshot at handoff

### EPIC #1451

| Phase | Status |
|---|---|
| Phase 0 — merge queue | ✅ |
| **Phase 1 — runtime alignment (P1-A #1452 + P1-B #1453)** | ✅ **CLOSED THIS SESSION** |
| Phase 2-A #1454 threshold unify (Claude) | ⏳ not started — **critical path to Phase 5** |
| Phase 2-B #1455 wiki review per-dim MIN (Claude) | ⏳ gated on ADR direction |
| Phase 2-C #1456 ADR kill-or-revert | 📝 drafted, awaits your sign-off |
| Phase 3 — pipeline + plan fixes | ✅ |
| Phase 4-A #1460 citation invariant (Codex) | ⏳ not started |
| Phase 4-B #1461 Unicode round-trip (Codex) | ⏳ not started |
| Phase 4-C #1462 post-processor mutation (Claude) | ⏳ not started |
| Phase 4-D #1463 plan immutability hook (Codex) | ⏳ not started |
| Phase 4-E #1464 rules deployment invariant (Codex) | ⏳ not started |
| Phase 5 — colors rebuild | 🔒 BLOCKED (see "Critical corrections #1") |

### Session-scope infrastructure (non-EPIC)

| Issue | Status |
|---|---|
| #1469 red-main bug | ✅ closed |
| #1471 branch protection | ✅ closed (applied) |
| #1472 postmortem must-change | ✅ merged via #1474 |
| #1475 dispatch telemetry | ✅ merged via #1477 |
| #1476 delegate hardening | ✅ merged via #1478 |
| #1479 CI speedup | ✅ merged via #1482 |
| #1480 local Docker-pytest | 📋 backlog |
| #1481 targeted test selection | 📋 backlog |

---

## Next session — recommended order

### PRE-PICK: clear session leftovers
1. Check `.worktrees/` list — anything stale? Cleanup.
2. Apply/discard the stale starlight patch file per user decision.

### PICK 1 — #1454 P2-A threshold unify → CLAUDE
- **Why first**: unblocks EPIC Phase 5 (colors rebuild). ADR explicitly gates on this.
- **Why Claude not Codex**: threshold semantics differ across (writer word target, reviewer pass floor, audit gate, plan-contract bound). Mechanical consolidation has bitten us before. Needs judgment.
- **Label already `agent:claude`**. Dispatch at `xhigh`.
- **Brief skeleton:** find every threshold constant (`config.py`, `v6_build.py`, `strict-reviewer-persona.md`, `non-negotiable-rules.md`), document semantics, propose single exported table, migrate callers.

### PICK 2 — #1460 P4-A citation resolution invariant → CODEX
- **Why**: mechanical invariant test. `[S\d+]` references must resolve to `sources.db`. Pure test-writing.
- **Parallel-safe** with #1454 (different code paths).
- **Label already `agent:codex`**. Dispatch at `high`.

### PICK 3 — #1461 P4-B Unicode round-trip golden corpus → CODEX
- **Why**: extends #1448 (Cyrillic й/ї tokenizer fix). Locks in the fix so no future regression. Mechanical — build golden corpus, assert preservation.
- **Parallel-safe** with #1454 and #1460.
- **Label already `agent:codex`**. Dispatch at `high`.

### DO NOT PICK (yet)
- **#1455 P2-B wiki review MIN** — waits on ADR #1456 direction.
- **#1456 ADR sign-off** — user decision, not dispatchable.
- **#1462 P4-C, #1463 P4-D, #1464 P4-E** — lower priority than #1454 path.

### With 2+2 parallelism cap
- Claude: #1454 (xhigh) + slot free
- Codex: #1460 + #1461 (parallel, different files)
- Gemini: available for content work if user fires

---

## MEMORY policy blocks added this session

All in `~/.claude/projects/.../memory/MEMORY.md`. Next session's Claude loads on boot.

1. **Dispatch parallelism cap (2+2)** — no more than 2 Claude + 2 Codex dispatches simultaneously.
2. **Codex branch-base verification** — fetch + verify `HEAD..origin/main` is empty before trusting dispatch output. (Obsolete after #1478 propagates to all dispatches, but keep for manual cases.)
3. **PR CI monitor — wait for pending before terminal** — avoid eager-terminal on old failed runs when new CI hasn't spawned yet.
4. **Prompt-ablation discipline** — pilot prompt changes on ≥3 fixtures before bulk (Anthropic postmortem lesson).
5. **GPT-5.5 rollout routing** — don't reflex-shift toward Codex when 5.5 lands in Codex CLI; 6:4 holds.
6. **Dispatch-brief checklist** — PR creation MUST be an explicit numbered step, not a footer.
7. **Codex debug — session history recipe** — `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` tail pattern.

Also updated:
- `#0` role block — 6:4 Codex:Claude rebalance; parallelism cap; usage monitoring
- REVIEWER POLICY — writer default model bumped to `claude-opus-4-7`, effort `xhigh`, CLI ≥ 2.1.116 gate

---

## Session metrics

- **7 PRs merged**: #1470, #1468, #1474, #1473, #1478, #1482, #1483, #1477
- **8 issues filed**: #1469, #1471, #1472, #1475, #1476, #1479, #1480, #1481
- **2 Claude research tasks delivered**: postmortem impact report (`docs/reports/2026-04-23-anthropic-postmortem-impact.md`, 17 KB) + ADR draft (`docs/decisions/2026-04-23-rewrite-strategies-kill-or-revert.md`, 23 KB)
- **2 Codex adversarial bridge consults** (telemetry rework + naming consult `msg #431`)
- **4 session-handoff corrections** (colors readiness, Gemini bot ownership, Codex observability, CI latency-is-a-choice)
- **1 new branch-protection rule** on `main`
- **~3 hours wall time, ~2 hours CI tax** — next session will feel ~40% faster due to #1479 landing

---

## Commands for cold-start

```bash
curl -s http://localhost:8765/api/state/manifest
curl -s http://localhost:8765/api/orient
gh issue list --state open --label 'agent:claude,agent:codex' --limit 20
ls -lt docs/session-state/*.md | head -5
# Then read THIS file end to end.
```

---

*Generated 2026-04-23 20:30 UTC, fresh-head post-merge of the last in-flight PR.*
