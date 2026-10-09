# Route, dispatch, settle (drive-epic §3, §3-routing, §3a, §4, §5)

Read before every implement dispatch and while a worker runs. The §4a and §5a inbox
drains are stated once in the core `SKILL.md` loop.

## §3. Route by model × harness fit

Decide the lane from `/api/rules` + `model_catalog.yaml`, **never** from the provider
name. Respect the live caps (in-flight ceilings), the language-lane restriction
(UK authoring / linguistic / content review route only to the sanctioned language lanes
per the served rules), folk carve-outs (cross-family only), and the judge-seat rules.
On limit: note the substitution and reroute per the fallback table — never block on one lane.

### Live capacity (binding every implement dispatch and CF settle — operator 2026-08-12 / #4707)

Before picking a seat, read fresh tool output from all of these:

```bash
curl -sS --max-time 3 "http://127.0.0.1:8765/api/state/routing-budget"
.venv/bin/python -m scripts.fleet.capacity_pick
.venv/bin/python -m scripts.fleet.usage show     # pace (also the capacity_pick pace column)
```

Prefer cooler / higher-headroom seats from that data. Do **not** habit-route to a hot,
near_cap, or in-flight-saturated lane when a cooler eligible seat exists. A
`credit_balance_present` lane (#9518; credit balance present, draw not verified by the router) is
usable after the plan-backed seats, only with the models in its `credit` row, and only while no
`rate_limited` outcome in the last 60 minutes contradicts it (that reads `credit_use_unconfirmed`,
near_cap/AVOID). Dispatch admission is a separate gate: it refuses other models whenever the plan
window is at or below the threshold and a fresh positive balance exists (`credit_balance_present`,
`credit_use_unconfirmed`, or `credits_unverified` from unreadable usage records), even when the
router no longer recommends the lane. A **deficit**
lane is visible pace, projected to run out before reset, and more than 2 points ahead of
pace (near_cap ≥ 90% unchanged); it is not a dispatch target while a cool lane has
reserve. CodexBar is an **input to the API**, not a separate driver app workflow — if
both surfaces are empty/stale, probe and record that in the ROUTING_CARD
(`NOTE: routing_budget_empty`), then use `/api/rules` fallback tables. Never invent burn %
from memory.

## §3-routing. Mandatory ROUTING_CARD_V1 + breadth (operator GO 2026-08-06)

**Binding full text:** `agents_extensions/shared/rules/fleet-driver-routing.md` (served at
`/api/rules` after model-assignment).

Before **every** implement `delegate.py dispatch`:

1. Emit a **ROUTING_CARD_V1** (handoff / issue / `batch_state/` receipt) with:
   `tier` (authority|practical|heap) · `model_x_harness` · `why_this_tier` ·
   `advisor_packet` (required if tier=heap) · `owned_paths` · `acceptance_cmd` ·
   ≥2 `alternatives_considered` · `parallel_free_seats` · quoted
   `routing_budget_primary` + `capacity_pick_order` (tool evidence).
2. **No card = no dispatch.** Skipping the card is a process defect; do not launch the
   worker and "write the card later." The runtime runs the issue-card checker
   `--strict` for implementation briefs naming GitHub issues. A WARN refuses
   dispatch unless urgent in-flight work uses `--allow-dor-warn <reason>`;
   the task JSON records that reason. GitHub/API lookup and checker failures
   also refuse dispatch unless that override is supplied. PR references are
   skipped after API resolution. Briefs without issue references are not gated.
   Opening or editing an issue updates one advisory checker comment.
3. **Default eligible code worker:** Sol @ high, per the 2026-10-09 resource-policy order.
   Use Claude workers through the native Claude CLI as heavily as their subscription
   allows, within task fit and hard gates. Cursor Grok or Gemini routes are language-free
   overflow only, admitted by live catalog and capacity evidence. Explicit Luna and bounded
   Flash workers still require a Sol advisory **envelope** (`--advisory-role
   bounded_advisory_envelope`) bound through `--advisory-task`. There is no direct bounded dispatch
   (operator decision 2026-09-30, #9275): `delegate.py` refuses Luna, and Flash not classified
   Ukrainian authoring/review, without a complete envelope bound to that dispatch. See
   `fleet-driver-routing.md` §2.
4. **Advisory path:** Opus 5.5 / Sol 6.1; Fable holds no advisory role (#9583). Do not spend
   an advisory seat on lockfiles / pointer / smoke jobs.
5. After ≥3 implement dispatches this session, require ≥2 agents **and** ≥2 tiers **or** a
   written `NOTE: fleet_breadth` with tool-backed blockers.
6. Before handoff, run and attach:
   ```bash
   .venv/bin/python -m scripts.fleet.driver_breadth_report --initiator "$SESSION_HANDOFF_AGENT" --since-hours 24
   # optional hard check:
   .venv/bin/python -m scripts.fleet.driver_breadth_report --initiator grok --since-hours 24 --enforce
   ```

Fixation on one practical seat while free lanes sit idle = utilization failure
(§2c — all driver seats, not Grok-only).

## §3a. Pre-dispatch outcome adequacy (required before substantive phase/epic kickoff)

Freeze the exact prompt before presenting or routing it. Record its SHA-256, user-visible
outcome, real-world or source denominator, non-goals, role map, independent held-out evaluation,
stop/residual policy, and completion vocabulary. For high-stakes domain work, obtain a
domain-fit review and a distinct adversarial scope/circularity critique; for smaller
consequential work, obtain at least one fast critic. A genuinely trivial bounded prompt is
explicitly exempt. The prompt author counts as neither reviewer. Choose these roles from live
`model-assignment.md` routing, not a
permanent reviewer identity; collect explicit checklist verdicts/findings and reconcile them
before dispatch.

Re-review after a material change to outcome, scope, denominator, role map, acceptance
criteria, or independent evaluation. A non-goal that shrinks the actual mission needs
operator/advisor approval. Prompt review is pre-dispatch quality control only: it never
replaces exact-head implementation review or the cross-family PR review gate. Discovery,
seeds, prototypes, schemas, transport checks, and self-authored canaries may prove research or
engine readiness, never product completion. On handback, name the verified user-visible outcome,
denominator, held-out proof, and residual gap. For normative language evidence, establish the
source's pedagogical or evidential role before consuming an occurrence.

## §4. Dispatch

Dispatch only when the task card and the dispatch preflight are both green (DoR).
Chat "ready" is not DoR. Tables: `docs/best-practices/task-quality.md` and `/api/rules` →
`operator-expectations.md` §3b.

```bash
.venv/bin/python scripts/delegate.py dispatch --check-budget --agent <lane> --worktree ...
```

`--check-budget` (or `LU_DISPATCH_CHECK_BUDGET=1` in the launcher) hard-subs via
`dispatch_fallbacks` when mapped (e.g. `codex → cursor`); otherwise it exits non-zero
unless `--force-agent` + NOTE. Before claiming who authored work, read the
`🔄 HARD AUTO-SUBSTITUTE` line (stderr) and the task record's `agent`/`model` in
`batch_state/tasks/<id>.json` (2026-09-25). Never filter dispatch output down to the
base-SHA line or drop stderr; that hides the substitution.

Dispatch with a numbered brief
(worktree → work → tests → ruff → conventional commit → push → PR → **no auto-merge by
the worker**) and the `#M-4` evidence preamble (each claim + its deterministic tool +
quoted raw evidence). Classify the task and pass the research flags
(`--research-role/-task-family/-track/-owned-path`). For write dispatches also pass
repeatable `--owned-path <path>` for the paths the worker may commit: auto-finalize commits
only under them and commits nothing without them (#8991). Stagger same-lane spawns ~10s.

The brief's test step names only the test files that cover the changed files,
including tests of code that imports a changed shared helper; never
collect the whole `tests/` tree (`pytest tests`, `pytest tests -k …`) or use `-n auto`
or `-n` above 2, and run those tests in the foreground and wait. The full suite
runs in the PR's CI (and again in the merge queue on the merged tree) — that is
the proof; do not trigger extra full runs. Use `.venv/bin/python -m scripts.publish workflow-run --workflow ci.yml --ref <branch>`
only when the brief explicitly asks for it (a branch with no PR yet, a baseline
capture, or diagnosis).

## §5. Settle-loop (never poll by hand)

A dispatch returning is not a settle. Arm a wait in the same turn: `delegate.py
wait <task-id>` where the seat has no Monitor tool; otherwise watch the task's
`batch_state/tasks/<id>.json` `status` with the **Monitor** tool. Ending the turn with a
live worker and no wait is a driver defect. When the wait returns, read the result and
take the next action. This wait is a §2c fill window, not an idle period: fill free lanes
before holding.

Terminal vocab (match `scripts/delegate.py`): **`done` = SUCCESS** (NOT "completed");
other terminal/attention states: `failed | timeout | rate_limited | cancelled |
crashed | dry_run` (dry_run is terminal, not success) + `needs_finalize | no_deliverable`. Emit on any
status NOT in `{spawning, running, ""}`. The task file is truth; `/api/delegate/active`
can omit live tasks. **Before declaring a dispatch dead:** `gh pr list --state open`
first, then check the worktree for finished-but-unpushed work. **After terminal status,**
run `.venv/bin/python -m scripts.fleet.post_task_reap --task-id <id>` (dry-run by default;
pass `--apply` to reap the bound dispatch worktree). `post_task_reap` delegates removal to
the P0 reaper; do not substitute a direct Git removal path.

**Wait-loop hygiene (2026-09-24).** Before arming a wait on a tool's output, grep the
tool's source or one real output for the exact string — a loop on text the tool never
prints (`would ADMIT` vs `would admit now`) waits forever. Never `pkill -f` a pattern
that also appears in your own command line; it kills your shell.
