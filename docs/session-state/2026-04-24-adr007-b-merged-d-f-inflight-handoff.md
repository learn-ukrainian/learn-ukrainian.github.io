# Session Handoff — 2026-04-24 00:30 CET: ADR-007 PR-B merged, PR-D + PR-F in flight

> **TL;DR** ADR-007 KILL wave mostly complete. PR-A (#1500), PR-B (#1499),
> PR-C (#1506) all merged. PR-D (Codex) and PR-F (Claude) both dispatched
> and have committed locally — just need to push + open PRs + CI + merge.
> After those close, fire PR-E (policy PR, Claude xhigh, 0-code) to flip
> ADR-007 APPROVED → ACCEPTED and close #1456 + supersede #1268 #1277
> #1288 #1322.
>
> **Read evening handoff** (`2026-04-23-evening-infra-hardening-handoff.md`)
> **and final handoff** (`2026-04-23-final-claude-heavy-dispatch-wave.md`)
> **for deeper context. This file is the delta since 00:00 CET.**

---

## What landed this session (merged to main, newest first)

| PR | Subject | Note |
|---|---|---|
| #1506 | `refactor(contract): ADR-007 PR-C — kill WORD_BUDGET auto-heal` | CI clean, merged fast |
| #1500 | `refactor(convergence): ADR-007 PR-A — kill M1/M2/M3 rewrite tiers` | CI clean, merged fast |
| #1499 | `refactor(review): ADR-007 PR-B — kill <rewrite-block> protocol` | **Required 3-way conflict resolution + allowlist fix + re-push.** See §Rebase autopsy. |
| #1504 | `docs: session handoff + 3 runnable briefs (meta-housekeeping)` | Admin-merge (docs-only path filter) |
| #1503 | `refactor(wiki): per-dim + MIN review aggregation (#1455)` | Clean merge |
| #1501 | `feat(post-processors): mutation-class invariant (#1462)` | Clean merge |

**6 merges. Session wall-clock: ~1h. Most cost was on PR-B rebase.**

---

## In flight at handoff (awaiting PR open + CI)

### PR-D (Codex) — `codex-adr007-prd-kill-rewrite-infrastructure`
- **Branch**: `codex/adr007-prd-kill-rewrite-infrastructure`
- **Worktree**: `.worktrees/dispatch/codex/adr007-prd-kill-rewrite-infrastructure`
- **Commit landed locally**: `10b1d81897` — `refactor: delete rewrite-block infrastructure per ADR-007 PR-D`
- **Diff stat**: `4 files, +11 / -836` — clean cleanup of helpers per brief
- **Agent**: still running at handoff. Next step: push + `gh pr create`.
- **Brief**: `.worktree-briefs/codex-adr007-prd-kill-rewrite-infrastructure.md`

### PR-F (Claude xhigh) — `claude-adr007-prf-invariant-test`
- **Branch**: `claude/adr007-prf-invariant-test`
- **Worktree**: `.worktrees/dispatch/claude/adr007-prf-invariant-test`
- **Commit landed locally**: `c52cc9c87d` — `test(adr-007): structural invariant — forbidden rewrite symbols stay gone`
- **Diff stat**: `1 file, +165 / -0` — `tests/test_no_rewrite_contract.py`
- **Agent**: still running at handoff.
- **Brief**: `.worktree-briefs/claude-adr007-prf-invariant-test.md` (copy from codex-* brief, reassigned per Monday directive)

### Monitors armed (will NOT survive session boundary)
- `bihjpj44c` — PR-B/C CI state (both merged; will go silent, safe to ignore)
- `b9pvxunvg` — PR-D + PR-F commits + PR-open events. **Will be lost on session end — re-arm in next session** to catch `pr_opened` events.

---

## Next session — recommended order

### PRE-PICK: merge what's green
1. **Check if PR-D and PR-F pushed + opened PRs yet.**
   ```bash
   gh pr list --state open --limit 10
   # Expect: claude-adr007-prf-invariant-test, codex-adr007-prd-kill-rewrite-infrastructure
   ```
   If they haven't opened yet, tail the dispatch logs:
   - Claude: `~/.claude/projects/-Users-krisztiankoos-projects-learn-ukrainian--worktrees-dispatch-claude-adr007-prf-invariant-test/*.jsonl`
   - Codex: `~/.codex/sessions/2026/04/24/rollout-*.jsonl` (timestamp-keyed)
   - Running processes: `pgrep -fl "claude|codex"`

2. **When PRs open**: wait for pytest SUCCESS (per memory PR CI MONITOR pattern — wait for `seen_pending` before terminal), then `gh pr merge N --squash --delete-branch`.

3. **If PR-F or PR-D stalls**: the test code for PR-F is fully pre-written in the brief at `.worktree-briefs/claude-adr007-prf-invariant-test.md` STEP 1. Can finish inline if agent fails.

### PICK 1 — PR-E ADR journal flip → Claude xhigh
- **Gate**: ALL of A/B/C/D/F merged. A/B/C done; D/F above.
- **Brief**: `.worktree-briefs/claude-adr007-pre-decision-journal.md`
- **Scope**: 0-code policy PR — flip `docs/decisions/2026-04-23-rewrite-strategies-kill-or-revert.md` status APPROVED → ACCEPTED, add `dec-007` to `docs/decisions/decisions.yaml`, close #1268 #1277 #1288 #1322 #1456 with supersede comments, remove "live contradiction" warning from `claude_extensions/rules/pipeline.md` + redeploy.
- **Fire with**:
  ```bash
  .venv/bin/python scripts/delegate.py dispatch \
    --agent claude --effort xhigh --model claude-opus-4-7 \
    --task-id claude-adr007-pre-decision-journal \
    --worktree --mode danger \
    --prompt-file .worktree-briefs/claude-adr007-pre-decision-journal.md
  ```

### PICK 2 — Colors 1-module pilot (USER-FIRED, not Claude-fired)
- **Runbook**: `.worktree-briefs/colors-pilot-post-adr007.md`
- **Pre-flight gates**: A/B/C/D/E/F all merged + #1462 + #1455 (already done).
- **Command for user**:
  ```bash
  .venv/bin/python scripts/build/v6_build.py a1 10 \
    --writer claude-tools --reviewer codex-tools \
    --writer-model claude-opus-4-7 --writer-effort xhigh
  ```
- Success → next session queues A1 batch rebuild. Failure → re-diagnose before batch.

### DO NOT PICK (yet)
- **#1507 content-based allowlist refactor** — filed from PR-B rebase, low priority, wait for a slow day.
- **Citation drift #1488-#1494 batch** — brief at `.worktree-briefs/claude-citation-drift-batch-1488-1494.md`.
- **#1344 Replace Phase A canary wiki articles** — now unblocked by #1503 (per-dim MIN merged); scope for later.

---

## Rebase autopsy: PR-B's 3-conflict resolution

Logged because this exact class will hit again when PR-E fires.

### Problem
PR-B (#1499) was opened before PR-A and PR-C merged. When I tried to merge PR-B after A+C landed:
1. **`scripts/build/v6_build.py`** — `mutated_this_round = fixes_applied or rewrite_applied or word_budget_rewrite_applied` had both `rewrite_applied` (deleted by PR-A) and `word_budget_rewrite_applied` (deleted by PR-C) removed from different sides of the merge. Git couldn't 3-way.
2. **`tests/test_v6_contract_flow.py`** — PR-B wanted to delete `test_apply_review_rewrite_blocks_*` tests; PR-C wanted to delete `test_apply_contract_word_budget_rewrites_*`. Overlapping regions → conflict.
3. **`tests/test_v6_review_regression_guard.py`** — same class, smaller scope.

Plus a separate CI fail: `tests/test_threshold_source_of_truth.py::test_no_threshold_float_literals_in_threshold_context` — the brittle `_FLOAT_LITERAL_ALLOWLIST` uses hardcoded `(path, lineno)`, and PR-B's 172-line deletion shifted `v6_build.py:2767` → `2766`, breaking the allowlist.

### Resolution pattern (cookbook for future)
For merge conflicts where **both sides delete overlapping code**:
1. `git checkout --ours <file>` → take current main's version (the "both sides see") as base
2. Manually re-apply your branch's targeted deletions using `git show <yourbranch-commit> -- <file>` as the diff reference
3. For single-line deletions: Python regex substitution
4. For function-body deletions: `re.sub(r'\n\ndef <name>\(.*?\) -> None:\n(?:.*\n)*?(?=\n\ndef )', '\n', text)`
5. Always `ast.parse()` after each edit to catch accidental splits
6. Always run the actual tests after all conflicts resolved

**Do NOT** blindly strip everything between `<<<<<<<` and `>>>>>>>` markers — that cuts partial expressions (hit this: cut a `monkeypatch.setattr(` mid-call).

### Also: branch naming gotcha
#1476 delegate hardening normalized worktree branch names from `codex-<task>` → `codex/<task>`, but PRs opened via manual `gh pr create` before the hardening landed still use the hyphen form. `git push` from a hardened worktree goes to the slash-form branch (orphan) unless you use an explicit refspec:
```bash
git push origin codex/adr007-prb-kill-rewrite-block:codex-adr007-prb-kill-rewrite-block --force-with-lease
```
Hit this during PR-B rebase. Remember it.

---

## Open decisions for Krisztian

1. **Colors pilot fire** — user-owned. Runbook at `.worktree-briefs/colors-pilot-post-adr007.md`. Fire when you're ready to review output.
2. **#1507 content-based allowlist** — not urgent. 15-min refactor when convenient.
3. **Stale starlight uncommitted changes** — still resurfacing in every fresh worktree. Root cause: uncommitted changes in main checkout that `git worktree add` inherits. Two options: (a) commit the starlight subtitle polish + revert the `colors: locked → active` hunk; (b) `git stash` in the main checkout so worktrees start clean. Recommend (a).

---

## Session metrics

- **6 PRs merged**: #1501, #1503, #1504, #1500, #1506, #1499
- **2 dispatches fired + committing at handoff**: PR-D (Codex), PR-F (Claude)
- **1 inline rebase resolution**: 3-file 3-way conflict + allowlist fix
- **1 follow-up issue filed**: #1507
- **2 stale issues closed**: #1452, #1453
- **Context budget**: cold-started at fresh, handoff at ~260K. Under 300K early signal throughout — efficient session.
- **Wall time**: ~1h active.

---

## Commands for cold-start

```bash
# Monitor API bootstrap (per MEMORY #0C)
curl -s http://localhost:8765/api/state/manifest
curl -s http://localhost:8765/api/orient

# Pending PR state
gh pr list --state open --limit 15 --json number,title,headRefName -q '.[] | "\(.number)  \(.headRefName)  \(.title)"'

# In-flight dispatches (worktrees)
git worktree list

# Recent handoffs
ls -lt docs/session-state/*.md | head -5

# Then read THIS file + 2026-04-23 chain end-to-end.
```

---

*Generated 2026-04-24 ~00:35 CET, while PR-D and PR-F dispatches still finishing push+PR. Next session's Claude: merge PR-D + PR-F when green, fire PR-E, stay in Claude-heavy cadence.*
