# Queue, issue ownership, no idle lanes (drive-epic §2, §2-epic, §2a, §2b, §2c)

Read when picking the next action, disposing the epic's open issues, or deciding
whether a free lane may stay idle.

## §2. Pick the next unblocked action

Source of next work: your epic's stream tail / handoff, open GH issues for the epic, the
build/review queue, the Work API projection's ranked attention list (§0), and
`GET /api/work/v1/next?stream=<your-stream>` — cross-check against them before committing to
an action. **Step 0 of any dispatch:** `gh pr list --state all
--search "<issue-nr>"` by issue reference (an open issue ≠ unfixed; a sibling PR may already
carry it). If nothing genuinely fits a free lane, record the §2c `no_ready_work`
disposition and leave it idle — never manufacture busywork (quality > utilization).

## §2-epic. Epic issue ownership cycle (binding — operator 2026-08-28)

You are an **epic orchestrator**, not a clerk waiting on one PR. Every cycle must advance
the epic's open issue set:

1. **Inventory** — open GitHub issues for this epic/stream (plus Work API `/next` +
   grok-bot QA issues per §2b). Quote the count.
2. **Disposition each item** — for every open issue, exactly one of:
   - **in_flight** (named PR/task id + head),
   - **dispatch now** (ROUTING_CARD + `capacity_pick` / `/api/state/routing-budget` +
     `--check-budget`),
   - **named hold** with one §2c hold code.
3. **Silence is a defect** — an open epic issue with no disposition is a driver failure.
4. **Closeout** — merge alone is not done; the post-merge issue disposition and cleanup
   are the core `SKILL.md` Definition of done.

**Anti-passive (all seats, Cursor especially):** while CF or CI runs on unit N, you
**must** either dispatch the next ready epic child or emit a §2c disposition code in the
same turn. Ending a turn with only "waiting on review/CI" and no fill/disposition is
forbidden. Overnight/session gaps do not excuse an unfinished CLEAN/MERGEABLE PR —
re-read checks and finish merge/hygiene on the next live turn.

## §2a. NO FABRICATED DONE (binding all epic drivers)

- Never invent acceptance thresholds the operator, issue, or epic goal did not set.
- Never declare a goal done while measured residual remains in the same mandate unless
  tools prove it impossible or the operator accepted it on the issue.
- Never end with "when you want" or an "optional next" for in-scope residual — dispatch it.
- Never relabel unfinished work as an intentional skip without issue text or tool proof.
- Before "done" or handback, quote the tool residual count; `residual > 0` requires a
  next dispatch in the same session.

## §2b. Grok-bot QA findings — queue input, not a fleet seat

Grok Bot (`app/cursor`) is an **external QA observer** — it reads CI/site signals and files
labeled GitHub issues; drivers consume those issues through the normal loop like any
other open issue. It is **never** a dispatch target: no `--agent grok-bot`, no `ask-grok-bot`,
no fleet-comms seat. If Grok Bot ever authors a PR, same-family Grok must not CF it — route to
an outside-family reviewer per §6. Full contract: `docs/runbooks/grok-bot-qa-observer.md`.

## §2c. No idle lanes — subscription min-max (binding, all driver seats)

Idle paid lanes are direct financial loss (operator 2026-08-17). This generalizes the
Grok-seat fleet-first *utilization* rule to **every** driver seat.

**Definitions.** *Free lane* — healthy, budget-eligible seat with no live assignment.
*Ready item* — queued work that is valuable, unblocked, and has an integration path.
*Compatible / independent* — the item fits the free lane and does not collide with
in-flight units (paths, review identity, or a hard dependency). *Settle event* — any
dispatch/review/CI terminal or decision point. *Grace period* — the short fill window
after a settle event before a hold is allowed. *Epic done* — operator goal met with
tool-backed residual 0, or operator-accepted residual on the issue.

**Precedence (strict):** correctness/quality → safety/resource bounds →
dependency/critical-path → utilization. Later items never override earlier ones.

1. **Waits are dispatch windows.** After any dispatch or review ask, **before** holding,
   fill every free lane with a compatible ready item (unblocked work, banked follow-ups,
   or prep the next program child whose dependency allows it). Idle free lane + ready
   item = utilization failure.
2. **Authorized idle is not a utilization failure.** A settle-hold must name one code:
   `dependency_blocked | authoring_wip_cap | review_wip_cap | ci_capacity |
   worktree_wip_cap | disk_capacity | integration_wip_cap | human_decision |
   no_ready_work`. Silence is not a disposition. A free lane with nothing compatible
   is `no_ready_work`; `dependency_blocked` names a real blocker, never a mismatch.
3. **Pipeline with a depth limit.** While CF/CI runs on unit N, author N+1 only up to
   the WIP/resource cap. Unit N **regains priority** the moment review feedback returns.
   Never serialize implement → review → delta with idle gaps.
4. **Ready-work forecast.** An unfinished epic needs a current ready-work forecast. An
   empty ready queue requires an explicit disposition, not silence. File banked
   follow-ups as GitHub issues when identified. Empty stream `/next` is a driver defect
   unless the epic is done or a disposition applies.
5. **Anti-gaming.** No placeholder agents, artificial task splitting, premature PRs, or
   speculative work without an integration path. §2 still binds: never manufacture
   busywork (quality > utilization). Disk wins every conflict (#M-14 — `df` + `du` of
   `.worktrees` before fan-out; reap first).

Mechanical reminder + disposition telemetry (#6976/#6998). At every
dispatch/review settle, evaluate eligible ready items and first-class admission
WIP limits (authoring / review / CI / worktrees / disk / integration) plus
queue readiness. The reminder fires only when something is eligible; then
dispatch or pass a structured code. Unknown codes are rejected. Do not add a
raw idle-time threshold. Guardrail-authorized idle is not a failure.
`driver_breadth_report --enforce` (§3-routing) fails the breadth floor (unless
NOTE-waived) and MISSING/DISHONEST idle dispositions — never opportunity-seconds.

```bash
.venv/bin/python -m scripts.orchestration.dispatch_settle task --task-id <id> \
  --idle-snapshot-json <snap.json> [--dispatched | --disposition <code>]
.venv/bin/python -m scripts.fleet.idle_settle evaluate \
  --snapshot-json <snap.json> --kind dispatch --task-id <id> \
  [--dispatched | --disposition <code>]
.venv/bin/python -m scripts.fleet.idle_settle report
.venv/bin/python -m scripts.fleet.idle_settle admission --snapshot-json <snap.json>
```
