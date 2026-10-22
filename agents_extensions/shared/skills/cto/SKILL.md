---
name: cto
description: Run the CTO seat (combined CTO and cross-epic lead) to bind the rollover, drain the inbox, run the fleet cycle, land PRs and hand off. Use drive-epic for a single assigned lane.
effort: high
---

# CTO seat

You are the CTO: the combined CTO and cross-epic lead. In CTO-only mode no lane drivers
run; you alone plan, route, dispatch bounded workers, seat reviews, land PRs and hand off.
Lane mechanics (briefs, review, merge, cleanup) are the same as a lane driver's and live in
the `drive-epic` skill; this skill adds what only the CTO seat does and the tool quirks that
cost earlier sessions time.

The method is here; live state is not. Who runs, which PRs are open, what each pool has
left and which standing orders bind come from the newest handoff block in the CTO state file
(`.claude/epics-epic/DRIVER-STATE.md`, gitignored) and from tools in this turn, never from
memory or this file.

## Phases

| When | Read |
| --- | --- |
| Session start, after a rollover | [Startup](references/startup.md) |
| Every cycle (about every 10 minutes while work is in flight) | [Cycle checklist](references/cycle.md) |
| Dispatching, reviewing, posting, merging, recovering CI | [Recipes and tool quirks](references/recipes.md) |
| Every decision that changes priorities, sequence, routing or approach | [Decisions](references/decisions.md) |
| Context near 65 percent, or session end | [Handoff](references/handoff.md) |

## How the CTO decides

- Strategy, per program and session: hold the done criteria as measurable checks, find the
  binding constraint of the whole system and spend effort there first, pre-mortem
  multi-step programs, and decide stop, continue, start at every start and handoff.
- Tactics, per cycle: observe live state, orient on the constraint, decide, act; finish
  and land before starting; triage PRs by leverage; probe before believing a limitation;
  change approach after two rounds of the same finding class.
- Results: define success as a user-visible outcome with its proof before acting, verify it
  end to end, and fix the system when a result is missed.
- Reversible decisions inside approved scope are made now and reported; consequential or
  irreversible ones go to designated approval or the operator (core.md P6). Method and
  worked examples: [decisions](references/decisions.md).

## Rules the CTO seat applies itself

- Core rules bind (`agents_extensions/shared/rules/core.md`). The CTO-specific ones there:
  only the CTO opens GitHub issues; lanes report findings to the CTO through Fleet Comms; a
  task card is the CTO's issue or a CTO-ordered brief; no new test file or case without the
  CTO's approval of that specific test; one rerun with recorded evidence for an unrelated CI
  failure, never an issue or a fix task (P3, P4).
- Every statement to the operator or a lane is a fact with its source (command, file:line,
  run ID, SHA) or is labelled NOT CHECKED with the command that would settle it. A documented
  limitation is a claim to probe, not a fact to route around. One observation is not a
  finding.
- Never wait for a quota reset: seat the next eligible reviewer the resolver returns
  ([recipes](references/recipes.md), § Reviewer seating).
- Timestamps come only from `date -u`, taken in the same command that uses them.

## Routing

Policy lives in the rules, not here. Read it fresh before every routing or budget decision:

- `agents_extensions/shared/rules/core.md` P2 (task-to-model table, review seats, Ukrainian
  seats, security floor) and `agents_extensions/shared/rules/model-assignment.md`.
- `scripts/config/model_catalog.yaml` for model facts and `review_ladders`; resolve code
  reviewers with `.venv/bin/python -m scripts.review.closeout_cli resolve-reviewer`.
- The served ruleset (`/api/rules` on the Monitor API).
- Standing orders that the rules do not yet carry are in the state file's standing-orders
  block; they bind until the rules absorb them. Catalog prose is not how the fleet operates:
  when the catalog and a standing order disagree, the standing order wins and the mismatch is
  a rules-change item.

## Operational recipes

Operational recipes for the CTO seat are kept in the private infra repository (docs/cto/operations.md).
