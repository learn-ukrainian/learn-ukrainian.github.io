# Session Handoff — 2026-04-23 evening (Codex takes over; Claude resumes tonight)

> **Transition reason:** Claude weekly limit approaching. Codex handles
> the PR queue + EPIC #1451 dispatches tonight. User's Claude limit
> resets tonight — Claude takes lead back at that point.

---

## State of the merge queue

| PR | Title | State | Next action |
|---|---|---|---|
| **#1448** | tokenizer й/ї fix | ✅ merged by Claude | — |
| **#1447** | canonical-anchor registry + discipline | ✅ merged by Claude | — |
| **#1442** | strip Gemini MCP warning + idempotent generated_by_model | ⚠️ merge conflict post-#1447 | Codex: `gh pr checkout 1442 && git fetch origin main && git merge origin/main`, resolve conflict on `scripts/wiki/compile.py`, push, merge |
| **#1445** | Backfill wiki source attribution (227 files) | ⚠️ **2× `Test (pytest)` FAILURE on CI** | Codex: investigate + fix. Likely the backfill changes interact with tests that ran before #1447 landed (attribution resolver interface). Rebase on current main first. |
| **#1443** | review-and-lock `things-have-gender` | ⏸ ready, only Gemini-Dispatch advisory failing | Codex: merge after #1442 lands (no interdependency but orderly queue) |
| **#1444** | review-and-lock `what-is-it-like` | ⏸ ready, only advisory failing | Codex: merge |
| **#1446** | review-and-lock `how-many` | ⏸ ready, only advisory failing | Codex: merge |
| **#1449** | diagnostic report — a1/colors dim root cause | ⏸ review-only PR | Codex: merge (diagnostic report, already approved by EPIC #1451) |
| **#1450** | diagnostic report — Gemini wiki writer | ⏸ review-only PR | Codex: merge (diagnostic report, already approved by EPIC #1451) |

### Merge convention
Squash-merge with `(#NNNN)` suffix in the title. Matches last ~10 commits.

### `#1403` safety shim notes
Per `fix(safety): block agent auto-merge + main-branch push via subprocess shims (#1403)`:
- The shim blocks *non-interactive subprocess* `gh pr merge` + `git push origin main`.
- Interactive Codex sessions may have a path through (user reports so).
- If Codex hits the shim, the fallback is user-merges-directly via the GitHub UI — that's fine; each merge takes 30 seconds manually.

---

## EPIC #1451 — Alignment-Pipeline Runtime Contracts

Full context in:
- `docs/architecture/2026-04-23-alignment-pipeline-audit.md`
- `docs/epics/2026-04-23-alignment-pipeline-runtime-contracts.md`
- `docs/reports/2026-04-23-a1-colors-rebuild-plan.md`
- `docs/bug-autopsies/alignment-contracts.md`

### Children ready for Codex dispatch (in order of leverage)

| Issue | Title | Agent | Dependency |
|---|---|---|---|
| **#1434** | Fix `_search_sections_fts5` missing `corpus` key (#1450 Fix 1) | Codex | — (trivial 1-line fix + test) |
| **#1459** (P3-C) | `compiler._format_sources` — strip S-prefix (#1450 Fix 2a) | Codex | — |
| **#1457** (P3-A) | Fix `_extract_terms` + Teacher-voice anchor (#1449 §5.1) | Codex | — |
| #1453 (P1-B) | Sidecar freshness invariant | Codex | #1452 |
| #1452 (P1-A) | Alignment manifest hash contract | Codex | — |
| #1454 (P2-A) | Unify thresholds single table | Codex | — |
| #1455 (P2-B) | Wiki review → per-dim + MIN | Codex | — |
| #1460 (P4-A) | Citation resolution invariant | Codex | — |
| #1461 (P4-B) | Unicode round-trip golden corpus | Codex | — |
| #1462 (P4-C) | Post-processor mutation-class invariant | Codex | — |
| #1463 (P4-D) | Plan immutability pre-commit hook | Codex | — |
| #1464 (P4-E) | Rules deployment invariant | Codex | — |

### Claude-owned (wait for Claude tonight)

| Issue | Title | Why Claude |
|---|---|---|
| **#1458** (P3-B) | `dialogue_situations[].turns:` convention + plan update | Plan-authoring + curriculum convention — requires judgment on dialogue shape per textbook pattern |
| **#1456** (P2-C) | Decision-vs-code parity — kill-or-revert rewrite strategies | Architectural decision — needs Claude to draft the ADR |

### Dispatch pattern (reminder for Codex)

Per `delegate-must-use-worktree.md` rule:

```bash
.venv/bin/python scripts/delegate.py dispatch \
    --agent codex --mode danger \
    --task-id codex-1434-attribution-routing \
    --worktree .worktrees/codex-1434-attribution-routing \
    --prompt-file .worktree-briefs/codex-1434-attribution-routing.md
```

Dispatch brief for #1434 is already written: `.worktree-briefs/1450-fix-attribution-and-chunkid-leak.md` in PR #1450's branch. Copy it to `.worktree-briefs/codex-1434-...md` before dispatch.

---

## What Claude did this session (already on main)

- Audit doc: `docs/architecture/2026-04-23-alignment-pipeline-audit.md` — 15-layer alignment stack, 11 drift findings, integrating Codex adversarial + Gemini content-builder perspectives.
- EPIC doc: `docs/epics/2026-04-23-alignment-pipeline-runtime-contracts.md` — 5-phase plan with dedup map.
- Colors rebuild doc: `docs/reports/2026-04-23-a1-colors-rebuild-plan.md` — 4-action sequence.
- Autopsies: `docs/bug-autopsies/alignment-contracts.md` + 3 INDEX entries.
- Pipeline rule drift fix: `claude_extensions/rules/pipeline.md` — writer default now `claude-tools`; rewrite-contradiction pointer.
- MEMORY.md: 2 behavioral lessons (#0F trace-to-code-first, #0G verify-branch-before-inheriting-failure-class).
- EPIC #1451 + 12 children (#1452–#1464).
- Supersede comments on #1268 / #1277 / #1288 / #1322.
- #1434 commented with #1450 Fix-1 dispatch brief.
- Diagnostic PRs #1449 + #1450 already open (diagnostic dispatches pushed them earlier).
- #1365 EPIC cross-linked as peer-gating.
- #1199 partially-superseded by P3-B.
- #1351 linked as Phase 4 candidate.
- Merged #1448 + #1447.

Commit on main: `163273b8cd docs(alignment): audit + EPIC + colors rebuild plan (#1451)`.

---

## What Claude will do on resume (tonight)

Order of priority:

1. **Sync with what Codex landed while Claude was out.** Read `git log origin/main ^163273b8cd` + any new PRs + any new issue comments.
2. **#1458 (P3-B) inline** — write the `dialogue_situations[].turns:` convention doc + update `plans/a1/colors.yaml`. ~2 h.
3. **#1456 (P2-C) ADR** — draft the kill-or-revert decision for the no-rewrite rule-vs-code contradiction. ~1 h.
4. **Colors rebuild (action 4)** — if P3-A (#1457) and P3-B (#1458) both landed, re-fire `v6_build.py a1 10 --writer claude-tools`. Monitor via Monitor tool, grep JSONL events.
5. **Worktree cleanup** — 20+ stale worktrees. Run `git worktree list`, remove merged ones.

## Open risks

- **#1442 merge conflict** — Codex or user resolves. If unresolved, #1443/#1444/#1446 stay blocked (they're ordered, not strictly dependent, but keep the queue clean).
- **#1445 test failures** — Codex diagnoses. If the failure is test-fixture drift from #1447 landing, rebase fixes it. If it's a real backfill bug, Codex writes the fix. Either way, backfill is cosmetic post-hoc attribution, not critical-path.
- **Phase 0 complete criterion:** all 7 queued PRs merged + diagnostic PRs #1449/#1450 merged. Only THEN is Phase 1 dispatch safe (otherwise sidecar-freshness work races against stale sidecar merges).

## Services + environment

All healthy (confirmed at session start):
- api:8765 — Monitor API
- sources MCP:8766 — retrieval
- starlight:4321 — site render

Shell state:
- `GEMINI_AUTH_MODE=subscription`
- Writer default on main: `claude-tools`

---

*Generated 2026-04-23 evening. Next session resumes with `state` skill + this handoff.*
