# Review budget, ledger and severity (single source)

This file is the only copy of the review budget, as set by operator order C-2902
(2026-10-27), which replaced the earlier one-full-plus-delta budget. Rules and skills that
mention the budget point here; do not restate it.

## Budget

A round is one reviewer dispatch at one exact head: round 1 is the full review, later
rounds are deltas.

- **Default: three rounds** (`budget_tier: default` in the hand-off record).
- **Up to five rounds** for a change to security, permissions, authentication, data loss, or
  state and concurrency, and only while an evidenced blocker on it stays open, or when the
  operator asks for it (`budget_tier: elevated`). Each round past the third cites the open
  finding id that justifies it. The author never raises the limit alone.
- **Stop early when only nits remain:** no open blocker means no further round. Remaining
  follow-ups never hold the merge.
- **One reviewer of record per round, and no sub-reviewers.** The reviewer does not fan the
  review out to helper agents. Learner-facing Ukrainian is the exception: its profile seats two
  independent reviewers (`references/ukrainian.md`, § Seats). The advisory second reader in `review-loop` is not a reviewer
  and adds no round.
- **The end of the budget is never approval.** The author splits the PR, changes the
  approach, or escalates to the CTO and the advisors (rules core P6).
- **The verdict recorder refuses a round beyond the budget**, so an over-budget verdict is
  never recorded.
- The budget and the ledger follow the work (issue and branch lineage). A new reviewer, a
  replacement PR or a new session does not reset them.

## Clearing a recorded rejection

A recorded `CHANGES_REQUESTED` or `BLOCKED` is cleared only by an APPROVE at a **new** head;
the recorder refuses a same-head APPROVE after it. So an escalation ruling on a recorded
rejection is followed by a head move (the fix, or a base update with
`"$PY" -m scripts.publish pr-update-branch --number "$PR"`) and one more round at that head.

## Ledger and stable finding ids

- Every finding gets a stable id (`F1`, `F2`, …) that keeps its number across rounds.
- The ledger records, per id: severity, disposition (`in_scope_blocker`, `follow_up`,
  `stop_and_escalate`), the round that raised it, its state (open, fixed with evidence,
  declined with evidence, escalated) and its owner.
- Before a PR exists the ledger lives in the task result with the review evidence. Once the PR
  exists it goes in the PR body (public-safe fields only, see
  [delivery](../../full-send/references/delivery.md)).

## Delta scope

- A delta review covers the open finding ids, the hunks changed since the last reviewed head,
  and the callers those hunks affect, including weakened or deleted tests in the fix diff.
- A new blocker in code that already passed review needs a concrete trigger: a failure the fix
  diff introduced or exposed, shown with file:line or a test. Otherwise it is a follow-up.

## Severity

- Severity follows impact on behaviour or readers, ranked by impact and likelihood.
  P0 and P1 block (`in_scope_blocker`). Uncertainty about a material failure also blocks.
- Speculative or bounded edge cases, pre-existing defects off the changed paths, wording and
  P2/P3 findings are follow-ups. The driver sends follow-ups to the CTO through Fleet Comms
  (only the CTO opens issues). A follow-up with the same outcome may be tracked on the parent
  issue instead (`workflow.md` § Work intake). A non-blocking follow-up never holds the merge.
- `SECURITY_VERDICT FAIL` always blocks and is never downgraded to a follow-up.
- INCONCLUSIVE (`BLOCKED` on the verdict line, naming the missing capability), a timeout, an
  error or no reply is never approval.

## Gate of record

- The independent cross-family review at the exact pushed SHA is the gate of record. The
  reviewer always comes from the live resolver with every author and subject exclusion, never
  a fixed model.
- A moved head needs a delta review and a fresh exact-head approval before enqueue.
- The red-team exception in `workflow.md` § Merge policy is unchanged and is labelled
  `review_mode=red_team`, never cross-family.

## Declines and disputes

- An author may decline a finding with file:line or test evidence.
- A dispute still unresolved after two replies on the same finding goes to the operator.
- A decline never clears a blocking verdict; only an APPROVE at a new head does.

## Breakers that still apply

The `local-code-review` checklist Step 6 breakers apply in every round, even when the open
finding count shrinks: the 2x scope-expansion breaker, the two-cycle convergence breaker, a
contract or owner-boundary change, and a needed design decision. A contested verdict escalates
(rules core P6).
