# Session Handoff — 2026-04-22 night: overnight orchestration, 4 Codex dispatches in flight

> **Status:** ACTIVE — main session continues as orchestrator. 4 Codex dispatches firing concurrently. Estimated landing window: 21:30 CEST through ~01:00 CEST.

## TL;DR

After resolving the terminal-crash mess (171 → 1 branches, 2 PRs merged, 3 incident issues filed), bumped #1384 to closed (Phase 1 already on main — verified live), traced the actual Gemini API-billing leak to `scripts/batch_gemini_runner/execution.py` (raw `subprocess.run` bypassing the adapter), filed #1406 to fix it. Then fired 4 parallel Codex dispatches covering: the Gemini leak fix, two infra bugs, and the next Track A roadmap blocker.

Main at **`2a119fa935`** (post `Fix Latin M## refs in Ukrainian plans (#1392) (#1393)`), pushed to origin.

## What landed earlier today

See chain:
- `2026-04-22-overnight-bakeoff-and-124-plan-forks.md` (overnight autonomous)
- `2026-04-22-decisions-locked-and-merge-prep.md` (morning)
- `2026-04-22-merges-landed-phase-3-pre-flight.md` (pre-peak)
- `2026-04-22-afternoon-ops-infra-pass.md` (peak-window stop)
- **This** (`2026-04-22-night-overnight-dispatches.md`)

Today's evening already shipped (post-terminal-crash recovery):
- PR #1402 — sentence-transformers 5.4.1 deps refresh (admin merge — pre-existing CI red)
- PR #1393 — Latin M## plan fixes (rebased clean from 175 commits behind, scope shrunk 300+ files → 4)
- 171 → 1 local/active branches; 122 stale `fork-1c-*` remote branches deleted
- Issues filed: **#1403** Codex auto-merge incident, **#1404** delegate.py rate-limit misclassification, **#1405** CI infrastructure red, **#1406** batch_gemini unify
- Issues closed: #1370 (shipped via #1401), #1384 (Phase 1 verified on main), #1396 (shipped via #1397), #1399 (overshot — 171→1)

## Active dispatches (overnight, fire-and-forget)

All on **Codex `--mode danger`**. Each has its own worktree + brief. Each brief explicitly bans `gh pr merge` / `--admin` per the #1403 lesson.

| Task ID | Issue | Worktree | Hard timeout | Brief |
|---|---|---|---|---|
| `codex-1404-rate-limit-bug` | #1404 | `.worktrees/codex-1404-rate-limit-bug` | 3600s | `.worktree-briefs/1404-rate-limit-misclassification.md` |
| `codex-1405-ci-red` | #1405 | `.worktrees/codex-1405-ci-red` | 5400s | `.worktree-briefs/1405-ci-red-fix.md` |
| `codex-1406-batch-gemini-unify` | #1406 | `.worktrees/codex-1406-batch-gemini-unify` | 5400s | `.worktree-briefs/1406-batch-gemini-unify.md` |
| `codex-1373-wiki-ingest` | #1373 | `.worktrees/codex-1373-wiki-ingest` | 7200s | `.worktree-briefs/1373-a6-wiki-ingest.md` |

All started ~20:34 UTC (22:34 CEST). Earliest expected completion: ~21:00 UTC for #1404. Latest: ~22:30 UTC for #1373.

### Brief summaries

- **#1404** — `delegate.py` misclassifies completed dispatches as `rate_limited` when output text contains substring "rate limit" (caught the #1370 dispatch incorrectly). Replace substring-match with exit-code or stderr-only signal. 7 unit tests + reclassify script for historical state.
- **#1405** — Pre-existing CI red on main (jsonschema missing in CI install, gitleaks license expired, `.pre-commit-config.yaml` yamllint errors, radon thresholds). Two PRs today (#1402, #1393) needed `--admin` to merge purely because of this. Fix means future merges don't need bypasses.
- **#1406** — Real Gemini API-billing leak. `scripts/batch_gemini_runner/execution.py:191, 357` calls `subprocess.run(cmd, ...)` with no `env=` kwarg, inheriting parent env including `GEMINI_API_KEY`. Two-path decision: route through adapter (preferred) OR deprecate v5 batch dispatcher entirely. Codex picks based on activity comparison.
- **#1373** — Track A roadmap blocker. Ingest 55 A1 wikis (`wiki/pedagogy/a1/*.md`) into `sources.db.ukrainian_wiki` (table already scaffolded by #1368). 5 ACs: segmentation, FTS5, source-weighting, admission gate, tests. Once landed, A.7 (canary A1 module against enriched corpus) becomes next dispatch.

## What main session is doing

- Orchestrator role per MEMORY #2: "Overnight (user sleeping): main session = orchestrator ONLY. ALL execution dispatched."
- Periodic dispatch progress checks via `ScheduleWakeup` (~20-30 min cadence per warm-cache discipline).
- Will review each PR as it lands. **Will NOT merge** without explicit user authorization (per #1403 lesson + the briefs themselves prohibit agent-side merges).
- If a dispatch fails (rate-limited for real, hard timeout, crash), notes the failure on the issue and triages whether to refire / split / defer.

## When you (next session or returning user) resume

1. **Cold-start via Monitor API** per `workflow.md` (NOT direct file reads).
2. **Check all 4 dispatches:**
   ```bash
   for tid in codex-1404-rate-limit-bug codex-1405-ci-red codex-1406-batch-gemini-unify codex-1373-wiki-ingest; do
       .venv/bin/python scripts/delegate.py status $tid | jq '{task_id, status, duration_s, returncode}'
   done
   ```
3. **List open PRs:** `gh pr list --state open` — should be 0–4 PRs depending on what landed.
4. **For each open PR:**
   - Review the diff against the brief's ACs
   - Check CI status (if green, safe to merge; if red because of #1405-not-yet-landed pre-existing red, may need admin)
   - Merge if ACs verified + adversarial review passed
   - Run `git pr-done .worktrees/<name>` (per #1394 alias) or manually remove worktree + branch

5. **Roadmap continues:** EPIC #1365.
   - Track A: After #1373 lands, **A.7** = canary A1 module build against the now-enriched corpus. Likely the next Codex dispatch in the morning.
   - Track B+: **#1344** (replace 4 Phase A canary wikis with dim-reviewed rebuilds) is still open. Could be the next claude/gemini dispatch — probably gemini if the rebuild pipeline is LLM-heavy.

## Known issues / risks

- **CI red still on main.** Until #1405 lands, future PRs (including the 4 in flight tonight) will require `--admin` to merge. This is a process risk — track in issue #1403 (sandboxing plan).
- **Batch_gemini_runner leak still active until #1406 lands.** Don't run any v5 batch dispatcher overnight (`scripts/batch/batch_dispatcher.py`) — it'll silently bill API.
- **#1373 (wiki ingest) is the largest job.** May hit the 7200s timeout if Codex over-engineers. If it does, refire with a tighter brief (split AC-2 + AC-5 into a follow-up).
- **`delegate.py` rate-limit false positives** still possible until #1404 lands. Don't trust `rate_limited` status without checking the result file + branch state, like we did this evening for #1370/PR#1401.

## Cleanup state going into the night

- 1 local branch: `main`
- 4 active worktree branches: `codex/codex-{1404,1405,1406,1373}-*`
- 5 worktrees total (main + 4 dispatch worktrees)
- 0 open PRs (4 will appear over next ~2h as dispatches land)
- 7 open issues: #1373 (in flight), #1377 (user-executed), #1395 (deferred), #1398 (blocked on gemini-cli), #1404+#1405+#1406 (in flight), #1403 (governance), #1334 (parked), and various older items in queue

## Operational notes

- All 4 Codex PIDs registered in `batch_state/tasks/codex-*.json`.
- No background `delegate.py wait` processes running — main session polls via `ScheduleWakeup` instead (avoids zombie wait processes if main session restarts).
- Disk: not rechecked tonight; previous handoff said 34 GB free.
- Main checkout clean, on `2a119fa935`, pushed.

---

**Active overnight orchestration.** Next periodic check scheduled. User can interrupt anytime.
