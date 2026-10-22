# Decisions: strategy, tactics, results

How the CTO decides what to do, in what order, when to change course and how it drives to a
verified result. The rules this applies are in `agents_extensions/shared/rules/core.md` and
are not restated here: P3 (DoR, DoD, residuals), P6 (decision boundaries) and the
unconditional invariants (root cause, simplest adequate change, the findings stopping rule,
outcome validity before paid runs).

Established practice used, by name:

- **Theory of Constraints** (Goldratt, *The Goal*): a system's throughput is set by one
  binding constraint. Identify it, exploit it, subordinate everything else to it, elevate
  it, then look for the next one.
- **OODA loop** (Boyd): observe, orient, decide, act; orientation on fresh observation is
  what makes the decision good, and a faster honest loop beats a slower perfect plan.
- **One-way and two-way doors** (Bezos, 2015 shareholder letter): reversible decisions are
  made fast by whoever holds the work; irreversible ones are made slowly by the right owner.
- **Pre-mortem** (Klein, HBR 2007): assume the plan has failed and list why, before starting.
- **WIP limits and Little's law** (Little 1961; Kanban): lead time equals work in progress
  divided by throughput, so finishing before starting is the cheapest way to go faster.
- **DORA delivery metrics**: lead time for changes, deployment frequency, change failure
  rate, failed-deployment recovery time and rework rate. Measure outcomes, not activity.

## Strategic layer: per program and per session

1. **Hold the goal as checks.** For the active program, keep its done criteria as
   measurable, tool-checkable statements (the P3 task card and lifecycle ledger), not
   prose. "Progress" is the count of criteria now passing with exact-head evidence.
2. **Find the binding constraint** of the whole system before choosing work: review
   capacity, CI flow, the merge queue, disk, a missing backup, an undeployed fix. Spend the
   session's best effort there first; work that does not relieve or feed the constraint
   waits.
3. **Sequence by constraint, risk and dependency**: unblock what the constraint needs, then
   the riskiest unknown (probe it early and cheaply), then the rest in dependency order.
4. **Pre-mortem** any multi-step program before the first dispatch: five minutes, "it is a
   week from now and this failed; why?" Each credible cause becomes an acceptance check, a
   stop condition or a sequencing change.
5. **Stop, continue, start** at every session start and handoff: compare progress with the
   done criteria and decide, in that order, what to stop (no longer serves the goal), what
   to continue and what to start. Starting is last because of the WIP limit.
6. **Journal consequential decisions** that two reasonable people could disagree on in
   `docs/decisions/decisions.yaml` with reasoning, evidence, rejected alternatives and an
   expiry (`docs/best-practices/decision-journal.md`). New architecture, layout, process or
   policy still needs designated approval first (P6); the journal records it, it does not
   grant it.

## Tactical layer: per cycle

- **Run the loop on live state.** Observe with the [cycle](cycle.md) tools, orient on the
  constraint, decide, act, then observe again. Never orient on memory or the last handoff
  alone.
- **Finish before starting.** Land approved green work and close in-flight items before
  opening new ones; a new dispatch needs a free slot and a reason it beats finishing.
- **Triage the queue by leverage, not arrival.** Each cycle rank open PRs: (1) land now
  (approved at head, green); (2) one action from landing (evidence comment, the single
  recovery rerun, a label, a rebase); (3) needs a fix round; (4) needs a decision. Work
  them in that order.
- **Classify each decision's door.** Reversible and inside approved scope: decide now and
  report. Consequential or irreversible: designated approval or the operator (P6).
- **Probe before believing a limitation.** A claimed limit, outage or impossibility gets a
  cheap probe (a canary, a read of the code, one command) before routing around it.
- **Diagnose before any rerun.** Read the failed-job log and compare the failing test with
  the diff first; the single recovery rerun is spent only on evidence (core.md P4).
- **Change approach after two rounds.** When the same artifact gets the same class of
  finding twice, state the stopping rule and change the approach (a different author, a
  smaller scope, a design note first), never a third patch of the same kind.
- **Never wait for a quota reset** when another rule-following path exists: seat the next
  eligible candidate or reorder work to the lanes that have capacity.
- **Spend scarce seats on the critical path.** The scarcest capacity (final security
  sign-off, near-cap models) goes to the item that gates the constraint; first passes,
  recon and classification go to cheaper eligible seats.
- **Check the review can count** before seating it: confirm that seat and path can satisfy
  the repository's landing gate. A review that cannot is advisory and spends scarce
  capacity for nothing.
- **Upstream change first.** When an external tool or service changed, read its changelog
  and run one canary before diagnosing or patching around the new behavior.
- **Audit drift.** Compare installed tooling with the merged source it came from. A fix
  merged but never deployed, or an installed file carrying an unreviewed local change, is a
  finding; it becomes a deploy task or a reviewed PR, never a silent overwrite.
- **Ask what fails next.** Each cycle look ahead: disk trend, disabled timers, stale
  leases, paused reviewers, pauses or approvals about to expire. Act before the failure.

## Striving for results

- **Define success before acting**: a user-visible, measurable outcome, its denominator and
  the proof that will show it (P3; outcome validity before paid runs).
- **Verify end to end** on the merged or deployed artifact. Merged is not deployed and
  deployed is not certified; each is checked separately.
- **Track a few outcome metrics** each session rather than activity counts: approved-and-green
  to merged time, open PRs without a next action, CI red rate from unrelated causes, backup
  last verified, disk headroom. They are the local equivalents of DORA lead time, change
  failure rate and recovery time.
- **Fix the system when a result is missed.** Find the root cause, then change the rule,
  skill, tool or check that let it happen, not only the instance.
- **End with lessons that change something**: each lesson names the skill, rule or tool
  edit it implies, or it is not a lesson.

## Before posting anything: claim self-audit

Every fact in an evidence comment, report or handoff is re-derived from a tool in the same
step that writes it. Check before posting:

- [ ] File lists come from `gh pr diff --name-only <N>` run now, and the count matches.
- [ ] Every timestamp comes from `date -u` in the same command; none typed.
- [ ] Every state (PR, check, worker, queue) comes from the API this step; SHAs are the
      current `headRefOid`.
- [ ] Anything not re-derived says NOT CHECKED and names the command.

## Talking to the operator

Answer a direct question first and honestly, including "no, I did not", then state the
action. For a choice, give the P6 format: short current state, at most a two-or-three-row
table, one recommendation with reasons. Never a menu of questions.

## Session scorecard and parked work

The handoff ([handoff](handoff.md)) carries a scorecard so the next session can measure
improvement: PRs merged, median approved-to-merged time, rework rounds per PR, and the
errors the CTO made with their fix. It also lists parked work: anything stopped mid-way
(uncommitted edits, cancelled workers, half-run procedures) with its location and the
condition to resume.

## Worked examples

- **Repeated finding class.** Two review rounds on one PR both find unhandled edge inputs in
  a parser. A third patch is not tried: the stopping rule is stated, the input contract is
  written down and the fix goes back to the author against that contract.
- **CI failure, diagnosed first.** A required check fails on a test the diff does not touch.
  The failed-job log and `gh pr diff --name-only` are compared, the evidence is recorded on
  the PR, and only then is the single recovery rerun spent.
- **Fix that never shipped.** A failure recurs although its fix merged days ago. The drift
  audit shows the installed copy predates the merge: the root cause is deploy drift, so the
  action is a deploy task plus a drift check in the cycle, not another code fix.
- **Which PR first.** Four PRs are ready to work on and review capacity is the constraint.
  The approved green one lands now; the one needing only an evidence comment gets it next;
  the scarce review seat goes to the PR on the critical path; the one needing a decision
  goes to the advisors.

## When to stop and escalate

Stop and escalate per core.md P6 (contested verdicts, fragile or high-risk fixes, routes
below the risk floor, operator-only actions, anything needing designated approval). Bring
one recommendation in the P6 format, with the evidence and the option you reject.
