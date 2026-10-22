# Decisions: strategy, tactics, results

Applies core.md P3, P6 and the unconditional invariants without restating them.
Practices used:

- **Theory of Constraints** (Goldratt): throughput is set by one binding constraint.
- **OODA loop** (Boyd): observe, orient, decide, act, on fresh observation.
- **One-way and two-way doors** (Bezos, 2015 letter): reversible fast, irreversible slow.
- **Pre-mortem** (Klein, HBR 2007): assume failure and list why, before starting.
- **WIP limits and Little's law**: finishing before starting is the cheapest speed-up.
- **DORA metrics**: measure lead time, failure and recovery, not activity.

## Strategic layer: per program and session

1. Hold the done criteria as tool-checkable statements (task card, lifecycle ledger);
   progress is the count passing with exact-head evidence.
2. Find the binding constraint (review capacity, CI, merge queue, disk, backups, an
   undeployed fix) and spend effort there first; the rest waits.
3. Sequence: unblock the constraint, probe the riskiest unknown early, then dependency order.
4. Pre-mortem every multi-step program; each credible cause becomes a check, stop
   condition or sequencing change.
5. At start and handoff decide what to stop, continue and start, in that order.
6. Journal contestable decisions in `docs/decisions/decisions.yaml`
   (`docs/best-practices/decision-journal.md`); the journal records approval, never grants it.

## Tactical layer: per cycle

- Orient on live [cycle](cycle.md) state and `lu-driver-state render --lane cto`, never on
  memory or the last handoff alone. Record priority, sequence, routing and approach changes
  with `lu-driver-state note <id> <text>` on the affected item.
- Finish and land before starting; a new dispatch needs a free slot and a reason.
- Triage PRs by leverage: land now; one action from landing; needs a fix round; needs a
  decision.
- Reversible and in scope: decide now and report; otherwise P6.
- Probe a claimed limit, outage or impossibility before routing around it.
- Diagnose from the failed-job log and the diff before the single recovery rerun.
- For review scope and repeated findings, apply the canonical
  [review stopping rule](../../drive-epic/references/review-merge-cleanup.md#review-stopping-rule).
- Never wait for a quota reset; reorder work to lanes with capacity.
- Scarce seats go to the critical path; first passes, recon and triage go to cheaper seats.
- Before seating a review, confirm that seat and path can satisfy the landing gate.
- When an external tool changed, read its changelog and run one canary first.
- Audit drift: installed tooling against merged source; a gap is a deploy task or reviewed
  PR, never a silent overwrite.
- Look ahead each cycle: disk trend, disabled timers, stale leases, paused reviewers,
  expiring approvals.

## Results

Define the user-visible outcome, denominator and proof before acting; verify end to end;
merged, deployed and certified are checked separately. Track outcome metrics: approved-to-
merged time, PRs without a next action, unrelated CI red rate, backup last verified, disk
headroom. When a result is missed, fix the rule, skill, tool or check that allowed it
([learning](learning.md)).

## Before posting

- [ ] File lists from `gh pr diff --name-only <N>` run now; counts match.
- [ ] Timestamps from `date -u` in the same command; states and SHAs from the API this step.
- [ ] The open mistakes-ledger entries checked as known traps.
- [ ] Anything not re-derived says NOT CHECKED with its command.
- [ ] To the operator: answer a direct question first and honestly, then the action; a
      choice uses the P6 format with one recommendation, never a menu of questions.

## Examples

- **Repeated finding.** Two rounds find unhandled parser inputs: write the input contract
  and return the fix to the author against it, no third patch.
- **Fix that never shipped.** A merged fix's failure recurs: the drift audit shows the
  installed copy predates the merge, so deploy and add a drift check.
- **Which PR first.** With review as the constraint: land the green one, post the missing
  evidence, seat the scarce reviewer on the critical-path PR, send the decision to advisors.

Escalate per P6 with one recommendation, the evidence and the rejected option.
