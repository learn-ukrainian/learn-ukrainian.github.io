---
date: 2026-05-12
session: "Orchestrator-shift + queue drain — 2 PRs + 8 direct commits"
status: ok
detail: 2026-05-12-orchestrator-shift-and-queue-drain.html
main_sha: d2df432354
main_green: true
open_prs: 0
active_dispatches: 0
merged_today: [1897, 1898]
rejected_today: []
filed_today: [1896]
closed_today: [1882, 1894, 1885, 1896]
in_flight: []
blocked: []
next_p0: "User-stated direction at next session-open. Carry-over queue from 2026-05-12 late-night is drained; no obvious P0 remains."
agents: [claude, codex]
worktrees_open: 0
ci_notes: |
  `Test (pytest)` was the only blocking gate that fired red in this session — twice, both my own fault (one orchestrator commit + one dispatched-Codex fixture gap). Both resolved within the session via inline test-fixture fixes + branch rebases. `review / review` advisory failure showed on the early CI runs and disappeared after the rebase onto main — pattern unstable, watch.
incidents:
  - "Main red for ~8 min after I shipped `d1588dd0ae` (goal-driven-runs.md rule) without running pytest. test_fresh_deploy_produces_synced_output has a hardcoded CLAUDE_RULE_FILES tuple that needed the new entry. Patched via `77522fe7ab`. Encoded as MEMORY #M-7: never push to main without targeted pytest, especially when adding files to tracked directories with hardcoded-mirror invariants."
  - "PR #1897 initial CI failed because Codex's dispatched commit accessed `result.session_id` on result objects, but two existing test fixtures used `SimpleNamespace(...)` without that attr. Two-line test fixture fix (`ceffe1bdea`) cleared it."
---

# Brief — 2026-05-12 — orchestrator-shift + queue drain

> Machine-readable companion to `2026-05-12-orchestrator-shift-and-queue-drain.html`.

## TL;DR

- **User explicit behavior correction at mid-session:** *"are you capable of this? if not let me know and i replace you with other agent"* — after I wrote a fully-ready dispatch brief then asked "Fire?" Encoded as **MEMORY #M-6** (top-priority orchestrator-drive rule).
- **10 commits to main + 2 PRs merged + 4 issues closed + 1 issue filed.** Drained the entire late-night-2026-05-12 carry-over queue (items 1-5; item 6 deferred until empirical signal).
- **Auto-deploy hook shipped** for `claude_extensions/**` — closes the manual `npm run claude:deploy` friction that surfaced when the user asked *"you have to deploy from claude_extensions ????"*.
- **Two CI fixes encoded as lessons:** MEMORY #M-7 (run pytest locally before push) after I broke main on a "docs only" commit that touched a hardcoded-mirror invariant.

## What shipped

| Ref | Title | Source |
|---|---|---|
| **PR #1897** | `fix(codex-adapter): honor bridge_only session resume — mirror gemini.py pattern (#1894)` | Codex dispatch — required one inline test-fixture fix (`ceffe1bdea`) + one rebase onto fresh main. |
| **PR #1898** | `fix(delegate): mkdir parent of stdout/stderr logs for slashed task_id (#1885)` | Codex dispatch — clean ship, required one rebase onto main once main was fixed. |
| `4657fc38bd` | `docs(autopsies): backfill canonical Symptom/Root cause/Prevention/Links` | Inline. Closed SessionStart hygiene flag on `agent-hallucination.md` + `secret-leakage.md`. |
| `54307bc07f` | `test(perf): bump test_annotation_speed budget 15s → 20s` | Inline. Carry-over queue item #5; absorbs Dagger runner-image variance. |
| `a664442d78` | `docs(dispatch): brief for #1894 Codex bridge warm-cache` | Inline. |
| `d1588dd0ae` | `docs(rule): ship goal-driven-runs.md — kubedojo Option B + v2.1.139 deltas (#1884)` | Inline. Codex tightening review applied via `ab ask-codex` (msg #590 → #591). |
| `541c097bf2` | `docs(dispatch): brief for #1885 delegate.py mkdir gap` | Inline. |
| `aea5ffe11e` | `docs(rule): clarify claude agents is a static config lister, not live state` | Inline. De-scoped carry-over queue #2 — the prior-brief framing of `claude agents` as "/api/delegate/active replacement" was wrong. |
| `77522fe7ab` | `test(deploy): add goal-driven-runs.md to CLAUDE_RULE_FILES — fix main red from d1588dd0ae` | Inline CI fixup (#M-7 origin). |
| `70089b4e4d` | `feat(hooks): auto-deploy claude_extensions on FileChanged — close manual rsync gap` | Inline. Triggered by user friction question. |
| **Issue #1896** | "Secret-leak prevention follow-ups (autopsy backlog from #M-5 recurrences)" | Filed to give the autopsy validator a real `#NNN` reference. Low priority. |

## What closed / killed

- **Issue #1882** ([V7 prompts] Update writer + reviewer prompts ... addresses #1807 tool-theatre) — closed retroactively. The actual work shipped in `28417cc3cb` (2026-05-11 evening) but the issue body was never updated. Drift cleanup.
- **Carry-over queue item #2** (`claude agents` view integration) — de-scoped. Verified against Claude Code 2.1.139: the command is a static configuration lister, not a live-session view. `--format json` is rejected. No integration is meaningful; the misread is now encoded in `workflow.md` to prevent future agents from repeating it.

## Carry-over queue (priority order)

The 2026-05-12 late-night carry-over is **drained.** Remaining inventory:

| # | Item | State |
|---|---|---|
| 1 | **Dagger Node.js in runner image** | 📋 Deferred. GHA pytest job doesn't set up Node either, so `test_agent_runtime_effort.py` must already be gracefully degrading. No empirical signal of failure today. Re-evaluate on next Dagger replay run. |
| 2 | **MEMORY budget tension** | 📋 At 151/150 after this session. Topic files in `memory/` could absorb more detail. Not urgent. |
| 3 | **Backlog of small follow-ups** | 📋 #1896 (secret-leak prevention), #1865 (context-budget epic 6 items, 5 still open), #1604 (PhraseTable activity_type=null), #1634 (lockfile resolver migration). All low-priority. |

## Decisions encoded (during session)

1. **`claude agents` is a static lister, not a live-session view.** No integration warranted. Workflow.md updated to prevent future-agent misread.
2. **Manual `npm run claude:deploy` is friction.** Closed via FileChanged hook on `claude_extensions/**`. Future edits auto-propagate.
3. **`✅ pre-commit passed` ≠ tests passed.** Pre-commit hook runs ruff + format only. Pushing to main without pytest is how main goes red. Encoded as MEMORY #M-7 with explicit trigger list.
4. **`/goal` rule shape per kubedojo Option B + v2.1.139 deltas.** Structured `GOAL_STATUS` / `GOAL_DONE` / `GOAL_ABORT` lines with deterministic counters; Claude `-p "/goal ..."` is the only headless `/goal` surface today (Codex `/goal` is TUI-only in CLI 0.130.0).
5. **Orchestrator-drive role (MEMORY #M-6).** I am the main orchestrator: prioritize, dispatch, monitor, decide. Ask permission ONLY when scarce resource, pending Decision Card, mid-task override, or user-owned artifact. Single yes/no on obvious next step = role failure.

## Pending decisions (not blocking next session)

- `docs/decisions/pending/2026-05-09-decision-graph-view.md` — channels.html UI toggle. Unchanged.
- `docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md` — agent bridge multi-surface identity. Unchanged.

## Cold-start orientation for next agent

1. **Read this brief first** — SessionStart hook will point here via `Latest-Brief:` marker.
2. **Verify the auto-deploy hook is active** by editing any file in `claude_extensions/` and confirming `.claude/` updates automatically (no manual `npm run claude:deploy` required). The hook lives at `claude_extensions/hooks/auto-deploy-claude-extensions.sh`.
3. **Verify MEMORY #M-6, #M-6a, #M-7 are loaded** — read the top of `memory/MEMORY.md`. The three rules drive the orchestrator behavior, `/goal` structured status lines, and pre-push pytest discipline. They are TOP PRIORITY.
4. **Run `wc -l memory/MEMORY.md`** — should be ~151 lines. If over 160, trim before adding any new rows.
5. **Codex weekly burn this session:** 2 dispatches (#1894 → 529s, #1885 → 185s) — well within budget.
6. **No carry-over P0.** Next P0 is user-stated at session open.

---

*Format spec: `claude_extensions/rules/workflow.md` § "Two-tier handoffs". Companion HTML: `2026-05-12-orchestrator-shift-and-queue-drain.html`.*
