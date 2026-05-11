---
date: 2026-05-12
session: "Late night — cold-start rule dedupe + act local CI + Codex resume queued"
status: ok
detail: 2026-05-12-cold-start-followups.html
main_sha: e76c152f36
main_green: true
open_prs: 0
active_dispatches: 0
merged_today: [1889, 1890, 1892, 1893]
rejected_today: []
filed_today: [1888, 1891, 1894]
closed_today: [1887, 1888, 1891]
in_flight: []
blocked: []
next_p0: "Dispatch #1894 (Codex bridge resume — mirror #1887/#1889 Gemini pattern)"
agents: [claude, codex]
worktrees_open: 0
ci_notes: |
  `review/review` continues to be advisory Gemini-Dispatch failure (no auth in CI runner) on every PR — pattern stable; admin-merge justified per #M-0.5 + handoff disclosure.
incidents:
  - "Codex dispatch #1888 died silently with 0-byte logs. Orchestrator rescued by committing uncommitted worktree work with X-Agent: claude-inline/1888-rescue. Codex's actual code was high quality (went beyond brief on test coverage). Logging path bug confirmed — adds evidence to #1885."
  - "Pytest verification via act surfaced 7 known-failure-mode tests under act runner: 4× rsync missing in catthehacker/ubuntu:act-latest image; 3× perf budgets violated under QEMU amd64 emulation on Apple Silicon. Documented as `act` gotchas in docs/best-practices/local-ci-replay.md."
---

# Brief — 2026-05-12 late night (cold-start dedupe + act setup + Codex resume queued)

> Machine-readable companion to `2026-05-12-cold-start-followups.html`.

## TL;DR

- **`.claude/rules/` static load dropped 47.5 KB → 17.4 KB** (verified post-deploy) — ~7.5K tokens off Claude cold-start. PR #1890 / Issue #1888.
- **`act` local CI replay shipped + documented** (PR #1892). Pivoted from "we urgently need Dagger" after orchestrator pushback — Dagger requires rewriting all pipelines as Python/Go/TS code (months); act replays existing `.github/workflows/*.yml` unchanged. PR #1893 followed up with real pytest timings + known-act-failure catalog.
- **Codex bridge warm-cache queued** (#1894) — user confirmed `codex resume <SESSION_ID>` works. Mirror of Gemini #1887/#1889 pattern. Dispatch deferred to next session due to clock; design is captured in the issue body.
- Four PRs shipped (#1889, #1890, #1892, #1893). Main at `e76c152f36`, green.

## What shipped

| Ref | Title | Source |
|---|---|---|
| **PR #1889** | `fix(gemini-adapter): honor bridge_only session resume` | Codex dispatch from prior session, completed mid-session here, merged. Closed #1887. |
| **PR #1890** | `fix(rules): dedupe Claude .claude/rules/ autoload, serve via /api/rules` | Codex dispatch in this session; **process died without committing**; orchestrator rescued the uncommitted work. Codex's code was high quality (deploy idempotency test + sister-script lockstep updates went beyond brief). Closed #1888. |
| **PR #1892** | `feat(local-ci): add act-based local CI replay` | Orchestrator-inline. `.actrc`, `.github/act-event-push.json`, `scripts/local-ci.sh` wrapper, `docs/best-practices/local-ci-replay.md`. |
| **PR #1893** | `docs(local-ci): pytest verification — real timings + known act failure modes` | Orchestrator-inline doc follow-up after pytest first-run completed in background. |
| **Issue #1894** | "Codex bridge warm-cache — mirror Gemini #1887 pattern" | Filed; dispatch deferred. |

## What rejected / killed

- **Dagger** — orchestrator pushed back on user's "we urgently need Dagger" framing. Dagger requires rewriting pipelines as code; act replays existing YAML. User confirmed pivot with "ok if act is better do act." Dagger remains a possible future investment if we ever want one pipeline definition that runs identically on laptop + GHA + anywhere.

## Carry-over queue (priority order — UPDATED after this session)

| # | Item | State |
|---|---|---|
| 1 | **#1894 Codex bridge warm-cache** ⭐ **NEW P0** | 📋 Issue filed with design. Dispatch shape: mirror #1888 brief, target `bridge_only` resume in adapter + registry while keeping dispatch path's worktree-isolation `never` policy. ~50 LOC + tests. |
| 2 | **`claude agents` view integration** | 📋 v2.1.139 feature. Unchanged from prior brief. Adds workflow.md rule + likely Monitor API wrap. |
| 3 | **`goal-driven-runs.md` rule (#1884)** | 📋 Unchanged. Draft from kubedojo Option B + v2.1.139 native `/goal` deltas; one tightening review → ship. |
| 4 | **#1885 `delegate.py` mkdir gap** | 📋 More evidence accumulated this session — Codex #1888 dispatch logs landed at `batch_state/tasks/logs/{task_id}.log` instead of `batch_state/tasks/logs/codex/{task_id}.log` (0-byte files because something opened them at the parent dir). Combined with the silent dispatch death, this contributed to needing the rescue commit. Worth a small Codex dispatch. |
| 5 | **`act` follow-ups (newly opened)** | 📋 Two clean wins: (a) install rsync in a custom act runner image (or switch to `:full-22.04`), unblocks the 4 `test_deploy_script_idempotency` failures; (b) tag the 3 perf tests so they auto-skip under `ACT_LOCAL_REPLAY=1` env. |
| 6 | **Dagger** | 📋 De-prioritized — separate, larger initiative. Only revisit if the act pattern hits a real limit we can't fix. |

## Decisions encoded

1. **Cold-start budget breakdown is now understood.** PR #1886 trimmed the SessionStart-hook block (30 KB → 1.6 KB). PR #1890 trimmed `.claude/rules/` static autoload (47.5 KB → 17.4 KB) by adding the 3 missing files to `/api/rules?format=markdown` and excluding the 6 unscoped rule files from the Claude deploy target only. Remaining bloat lives in agent-def + MEMORY.md + tool schemas + skills list — out of scope for tonight. Total cold-start est. drop: ~7.5K tokens.
2. **act > Dagger for the named pain.** act replays existing GHA YAML unchanged; Dagger requires pipeline rewrites. Pushback was right; user agreed.
3. **act is SLOWER than GHA on heavy jobs.** First-run pytest: 7m45s vs ~4m17s on GHA. The value prop is no-queue-wait + local debug access, not raw speed. Doc reflects this explicitly.
4. **Codex CLI does support session resume.** User confirmed; we just weren't using it. Same pattern as Gemini #1887 — bridge-only, dispatch keeps `never`.
5. **Orchestrator-rescue pattern for dispatch silent-death.** When Codex dispatch exits without committing but leaves good work in the worktree: orchestrator verifies tests + ruff, then commits inline with `X-Agent: claude-inline/<task>-rescue` trailer and explicit authorship note in commit body. Used tonight for #1888 → PR #1890.

## Pending decisions (not blocking next P0)

- `docs/decisions/pending/2026-05-09-decision-graph-view.md` — channels.html UI toggle. Unchanged.
- `docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md` — agent bridge multi-surface identity. Unchanged.

## Cold-start orientation for next agent

1. **Read this brief first** — SessionStart hook will point here via `Latest-Brief:` marker.
2. **Verify the cold-start win** — run `wc -c .claude/rules/*.md` on a fresh checkout after `npm run claude:deploy`. Expected total: ~17.4 KB (was 47.5 KB). If you see 47.5 KB, deploy hasn't run on your checkout yet.
3. **Next P0 is #1894 dispatch.** Brief shape: mirror the #1888 dispatch brief (tool-grounded verification block, pre-submit checklist, explicit step-8 PR creation). The core code change is small: registry policy `never` → `bridge_only`, adapter honors `session_id` when bridge, dispatch path still ignores it. ~50 LOC + tests. **Read `scripts/agent_runtime/adapters/codex.py:1-30` first** for the design rationale (cross-worktree contamination footgun) — that rationale stays for dispatch.
4. **act tooling is in main.** `scripts/local-ci.sh -W .github/workflows/ci.yml -j lint` works. `--reuse` makes second run 38s. Pytest first run is 7m45s; ignore the 7 known-act-failures listed in `docs/best-practices/local-ci-replay.md`.
5. **Worktree state:** 0 open. All this session's worktrees cleaned up post-merge.
6. **Codex weekly burn unchanged from prior session estimate.** Used ~2 dispatches this session (#1887 completion + #1888); both succeeded (#1888 needed orchestrator rescue but Codex's actual code work was clean).

---

*Format spec: `claude_extensions/rules/workflow.md` § "Two-tier handoffs". Companion HTML: `2026-05-12-cold-start-followups.html`.*
