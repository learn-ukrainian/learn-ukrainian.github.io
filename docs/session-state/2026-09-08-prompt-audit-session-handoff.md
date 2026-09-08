# Session handoff — prompt audit for Fable 5.1 and follow-ups (2026-09-07 → 2026-09-08)

Orchestrator lane `claude/prompt-audit-2026-09-07` (Claude Fable 5.1, native Claude Code). Operator orders in this session: run `/claude-api prompt-audit`, apply all of it, keep `agents_extensions/` as the git source, improve CI if evidence supports it, report frictions. Thread rollover packet (continuity, exact next steps): `.agent/thread-rollovers/claude/lineage-b4576db364702f06a8c5eeac/generation-0001/rollover-3c838b57e66e44a485767493664a241c/handoff.md` (gitignored; bootstrap prompt beside it).

## Landed

| What | Where | Proof |
| --- | --- | --- |
| Prompt audit for Fable 5.1: 11 high / 21 medium findings applied — rules, memory, review prompts and writer templates corrected against `config.py` and live code; 16 fossil files removed; dead raw-SDK path removed | PR #7809, merged `000b39ad73` | cross-family REQUEST CHANGES → APPROVE at `f0bdb11fd7` (codex seat), CI Gate 17/17 |
| QG reviewer findings schema through the harness (audit finding M19) | issue #7810 (closed), PR #7818, merged `b72e7b95cf` | review of record (Claude seat, no BLOCKING) + executed HELD-OUT PASS at `26785541f5`; exact-head re-review APPROVE at `2778fb0be9`; CI 17/17 |
| Primary checkout repaired after another lane's read-only review detached it at `c7fd04d6` | `check_primary_integrity.py --fix` at 01:00Z | `git status` on main; deploy parity re-verified twice (last at `b72e7b95cf`) |
| Stale thread lease (owner gone 9 days) released; friction, lane-outage and CI issues filed | #7812 (ACP lanes), #7814 (39 frictions), #7816 (CI evidence + frozen brief) | issue bodies carry verbatim tool output |

## In flight — the only open lane

**PR #7819** (`claude/ci-shard-balance-2026-09-07`): CI pytest gate on all 4 runner vCPUs (`-n logical`; `-n auto` gave 2 workers via psutil physical cores), single-initial-path collection with an allowlist hook (64–67 s → 8.1 s measured), duration-balanced shards from a committed CI-derived snapshot, `--durations=25`, per-shard JUnit artifacts; shard count kept at 4 (decision 2026-07-22 unchanged).
- Review of record (Grok seat) at `d7fdbcb01f`: REQUEST CHANGES — B1 shard-2 red on the first 4-worker run; B2–B4 = criterion-6 evidence the reviewer could not execute (coverage identity, two-run timings, `created: 4/4 workers`, peak memory). First-run steps already 291/356/336/349 s vs baseline 423–565 s.
- Fix worker (claude lane, task `ci-shard-balance-2026-09-07` run 6) pushed `59d2b58c84` ("retry the wake-process lifecycle test's timed-out attempts under contention") and is still gathering criterion-6 evidence in its worktree.
- Next: when it posts the head + evidence → `ask-grok - --type review --pr 7819` with the criterion-6 mandate (reviewer executes it) → post verdict verbatim if the sandbox cannot → CI Gate green at that head → enqueue (squash; merge queue) → reap `.worktrees/dispatch/claude/ci-shard-balance-2026-09-07` + branch → `npm run agents:deploy` if agent files changed → close #7816 with evidence.

## Operator decisions still open

1. Merge-queue "maximum pull requests to build": landed-PR queue wait is median 12.5 min, p95 47 min, runner wait 0 — the queue's serialization, not the tests, dominates; repository setting.
2. Shard count > 4 once the post-#7819 numbers exist (decision-record addendum).
3. #7812: the whole ACP `ask-*` surface (agy, deepseek, kimi, cursor, plain codex) refuses to spawn (acpx 0.15.0 capability mismatch); only `--type review` (headless native dispatch) works.
4. #7814: 39 frictions; the costliest are the ACP outage, the read-only review sandbox that can neither post nor read via `gh`, headless Claude workers without write permission under `workspace-write`, and the guard hook's blindness to shell variables.

## Hazards for the next session

- Never run pytest above `-n 4` on the primary host (8 workers exhausted memory and got harness background tasks killed; host-courtesy rule is in both briefs).
- Harness background waiters get killed under its memory heuristic; `Monitor` tasks survive — use them, or foreground checks of `batch_state/tasks/*.json`.
- Literal absolute paths only in shell commands (the guard cannot resolve `$VAR` or an in-command `cd`).
- `--dry-run` records block re-dispatch under the same task id (`--force-new`); dirty worktrees cannot be re-attached (commit WIP first); headless Claude needs `--mode danger` to write; `batch_state/` inputs are per-worktree — give absolute primary-host paths.
- GitHub API budget (5,000/h shared) was exhausted three times; batch `gh` calls and avoid `gh run view --log` bursts.

## Briefs and evidence (gitignored, primary host)

`batch_state/briefs/qg-reviewer-schema-7810.md` (rev 3.4), `batch_state/briefs/ci-shard-balance-2026-09-07.md` (rev 3.3), `batch_state/briefs/heldout-7818.md`; CI evidence and derivation script under `batch_state/ci-shard-balance/`; review results under `batch_state/tasks/review-781{8,9}*.result`, `heldout-7818.result`.
