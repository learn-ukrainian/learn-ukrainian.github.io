# Review budget, ledger and severity (single source)

This file is the only copy of the review budget, as set by operator order C-2902
(2026-10-27), which replaced the earlier one-full-plus-delta budget. Rules and skills that
mention the budget point here; do not restate it.

## Budget

A round is one reviewer dispatch at one exact head: round 1 is the full review, later
rounds are deltas. A round is spent when its reviewer is dispatched, whether or not its
verdict is ever recorded; more seats or a retry at a head already dispatched open no round.

- **Default: three rounds** (`budget_tier: default` in the hand-off record).
- **Up to five rounds** for a change to security, permissions, authentication, data loss, or
  state and concurrency, and only while an evidenced blocker on it stays open, or when the
  operator asks for it (`budget_tier: elevated`). Each round past the third cites the open
  finding id that justifies it. The author never raises the limit alone.
- **How the recorder grants the elevated tier.** Security-sensitive changed paths give a PR
  five rounds on their own. Any other change gets rounds four and five only through a sealed
  designated grant (`scripts/review/budget_grant.py`): the CTO's typed ruling, issued as
  `claude-cto` and bound to the repository, the PR, its head branch, the changed paths it
  covers, the blocker class and the open finding id, plus a sealed APPROVE of that ruling from
  the designated advisor outside the issuer's family. Print the ruling's digest with
  `record_cf_verdict.py budget-grant digest <ruling.json>`, then dispatch the advisor
  read-only with `--advisory-role review_budget_elevation --advisory-binding <digest>
  --initiator claude-cto`. Each granted round needs the latest recorded verdict to be a
  rejection that lists the granted finding at P0 or P1 and keeps it open in plain words
  (`still open: <reason>`, or a newly raised finding); any closing word in that entry, such as
  `resolved`, `fixed` or `declined`, refuses the round. A grant never
  resets the rounds already counted, never covers a path outside its scope, and five rounds
  stay the total.
- **Withheld-capability recovery.** A sealed grant with `blocker_class: withheld-capability`
  uses the same ruling and approval machinery and names the finding awaiting verification,
  at any severity. Its `withheld_capability` object names the missing `capability`, cites
  `runs` by `task_id`, `run_nonce`, `reviewed_sha` and `reply_sha256`, and includes each
  run's complete `verification_only_evidence` finding excerpt. The designated advisor must
  confirm that these excerpts establish the defect is corrected and only verification is
  missing. Every cited run must have an intact trusted BLOCKED publication naming the missing
  capability, matching its recorded reply and lineage, with no new P0/P1 or substantive blocker.
  The latest rejection must remain one of these capability-only runs, with no substantive or
  unknown review intervening. `retry_probe` seals the same run identifiers plus a literal
  `capability_evidence` excerpt demonstrating the capability on the retry route at the new
  head; the recorder refuses a retry on a different route. Other classes set
  `withheld_capability` to null; their existing sealed grants remain valid. Credits count
  distinct already charged heads, deduplicated
  across runs, retries and grants: each grant permits at most `min(5, 3 + qualifying_heads)`
  total rounds. It never resets spent rounds, reclassifies a capability failure, or clears a
  security FAIL; a fresh probe-backed review must clear the rejection.
- **Stop early when only nits remain:** no open blocker means no further round beyond the verification review that a fixed blocker or a new head still requires. Remaining
  follow-ups never hold the merge.
- **One reviewer of record per round, and no sub-reviewers.** The reviewer does not fan the
  review out to helper agents. Learner-facing Ukrainian is the exception: its profile seats the
  independent reviewers named in `references/ukrainian.md`, § Seats. The advisory second reader in `review-loop` is not a reviewer
  and adds no round.
- **Optional DeepSeek pre-check is not a review.** The optional DeepSeek author pre-check
  (DS-PRECHECK-1101) is never a review of record, opens no round, and never satisfies or waives
  the cross-family review gate; no round budget, risk floor, or reviewer selection changes.
- **The end of the budget is never approval.** The author splits the PR, changes the
  approach, or escalates to the CTO and the advisors (rules core P6).
- **One repair-verification round per lineage, outside the budget.** When a PR approved at its
  last reviewed head A needs a new head N only for a CI fix or a conflict resolution, the
  recorder admits one more round at N with no request PR (`scripts/review/repair_round.py`).
  It needs: the review lineage before N on record, with A's APPROVE the latest verdict of every
  seat; a CI fix tied to a failed run of the required CI workflow at A itself (a PR run) or of
  this PR's merge-queue candidate built from A; or a conflict resolution whose merge tree differs from Git's own merge of its pinned
  parents only in the paths Git reports conflicted. Any other change after approval, or a mix
  of the two, is unclassifiable and escalates to the CTO. The round's reviewer covers the
  whole repair delta (`git diff A N`), the callers it affects, the invariants it touches and any
  weakened or deleted tests ([delta scope](#delta-scope)), plus the failed run or the conflicted
  paths it names. An APPROVE in that round must carry the line
  `REPAIR_VERIFIED: <delta_sha256>` with the digest `budget-check` reports: the reviewer's
  statement that the complete delta is only the repair it names. Without it the recorder
  refuses the APPROVE; a rejection needs no such line. The recorder writes a durable receipt for the round under the PR, its head
  branch and every issue it closes, before it posts the verdict. That receipt is never removed:
  another approval, a replacement PR or a new session never replenishes the round.
- **A clean base merge consumes no round.** A head that descends from the last fully approved
  head only through conflict-free merges of the default branch, each proven by Git to add
  nothing beyond the merge, is reviewed without counting against the budget. It still needs
  its own exact-head review and CI: no approval carries forward, a recorded rejection stands,
  and verdict history is kept. A conflict, a manual edit inside a merge, any other commit, or
  a missing object or failed proof makes the head count as a normal round.
- **The verdict recorder refuses a round beyond the budget**, so an over-budget verdict is
  never recorded, and **the dispatcher refuses an over-budget review dispatch** with the same
  decision, naming the PR and the count. Both count every review run on record for the PR (its
  `pr` or head branch), recorded or not. **Ask before dispatching a reviewer:**
  `record_cf_verdict.py budget-check --repository <owner/name> --pr <N>` returns the same
  decision for the PR's current head (admitted, with any exemption, grant or repair-round
  receipt, or the refusal that names what to escalate), lists each head reviewed without a
  recorded verdict under `unrecorded_rounds`, and writes nothing.
- The budget and the ledger follow the work (issue and branch lineage). A new reviewer, a
  replacement PR or a new session does not reset them.

## Clearing a recorded rejection

A recorded `CHANGES_REQUESTED` or `BLOCKED` is cleared only by an APPROVE at a **new** head;
the recorder refuses a same-head APPROVE after it. So an escalation ruling on a recorded
rejection is followed by a head move (the fix, or a base update with
`"$PY" -m scripts.publish pr-update-branch --number "$PR"`) and one more round at that head.

## An unpublished verdict that its seat superseded

A finished review whose verdict is never published refuses every later round of its lineage,
unless its own seat recorded a later verdict at another head. A seat is one reviewer family on
one review profile (code or Ukrainian), and only its latest recorded verdict counts. That run
is then superseded and stops refusing (`review_lineage.superseded_runs`):

- The superseding run is a finished run of the same family and profile, started strictly
  later, at a different head, whose published verdict matches its own task record. A run at
  the same head or an earlier one, a run of another family or profile, a run at the candidate
  head of the round being recorded, and a damaged or unpublished run supersede nothing.
- The superseded run is listed, never dropped: the repair-round receipt that `budget-check`
  reports names its task id, pinned head, unpublished verdict and finding count, and the run
  that superseded it. Its head stays a reviewed head and still counts against the budget.
- A superseded rejection keeps its findings. They stay in the ledger until they are fixed,
  declined or escalated; supersession resolves none of them.
- A missing reply, an invalid reviewer identity, a digest mismatch, a run that is not `done`
  but carries a verdict, and an unpublished run that its seat never superseded still refuse.
  A superseded verdict is never published afterwards against a moved head.

## A BLOCKED that only lacked a capability

When the reviewer stopped only because a capability it needed was missing, the CTO may record a
capability failure for the run instead of a verdict
(`scripts/review/capability_failure.py`):

```bash
"$PY" scripts/review/record_cf_verdict.py capability-failure --task-id "$REVIEW_TASK" --pr "$PR" \
  --capability <sources-mcp|test-execution|shell|browser|checkout-data> --authority claude-cto
```

- It qualifies only when the reply is `BLOCKED` with a known count of zero findings, which only a
  structured `code-review-findings.v1` reply proves, and the missing capability is evidenced:
  `sources-mcp` by the run's recorded count of zero Sources MCP calls on the Ukrainian profile,
  any other capability by the reply's `missing_capabilities` list beside its findings. A prose
  reply, any finding (P3 included) or "no in-scope blocker" does not qualify, and that BLOCKED is
  handled as today.
- The event is bound to the run, its reviewed head and its reply digest; the reply stays as it is.
  It is not a verdict: it approves nothing, rejects nothing, opens no round and fills no seat, so
  every required review still has to happen. A run with a published verdict cannot be
  reclassified, and a classified run's verdict cannot be published.

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

Severity follows impact on behaviour or readers, ranked by impact and likelihood.

1. P0, P1, and uncertainty about a material failure keep blocking.
2. A demonstrated, unintended loss of previously correct behavior or of an existing refusal guarantee introduced by the PR blocks when its priority is P0, P1, or P2. Cite the pinned base and head, the same triggering inputs and preconditions, the contract violated, and a reproducer or complete code-path proof. An intentionally approved contract change, preference, or speculative difference is not a regression. An omitted or bounded trigger does not exempt a demonstrated P0, P1, or P2 regression. Disputed material contract applicability escalates. A P3 regression does not block.
3. Every other confirmed P2 defect is fixed in the PR or tracked before enqueue on an OPEN issue covering that finding. The worker or driver reports it through Fleet Comms; the CTO searches for and updates a matching open issue, or creates one under Work intake. The enqueue owner verifies its open state and coverage, and records the issue link, stable finding ID and owner in the ledger. A report awaiting CTO disposition is insufficient. Tracking alone requires no additional review round.
4. P3 findings, including a P3 regression, nits, and preferences, never block and never open a review round. They are recorded as residuals on an open issue. A reply whose verdict is REQUEST_CHANGES and whose open findings are all P3 is recorded as an approval with those residuals listed: the findings stay verbatim and visible, and the `fleet/cross-family-review` status is success. The recorder reads the priority the reply already carries.

Review budgets, seats, ladders, and exact-head binding are unchanged. A P0, P1, or P2 finding, and a demonstrated regression at those priorities, keeps the handling in items 1 to 3. Round exhaustion does not turn that rejection into approval and grants no extra round. Reviewers keep the priority the impact supports: they do not raise a P3 to force another round, and they do not lower a P0, P1, or P2 to clear it. Filing or linking the residual issue consumes no review round.

- `SECURITY_VERDICT FAIL` always blocks and is never downgraded to a follow-up or a residual. A security verdict whose value is not exactly pass is the same refusal, including a conditional pass. A reply that does not fit in the record stays a rejection. A repair round whose reply does not attest that the delta is only the repair stays a rejection, including a marker posted earlier on that head.
- INCONCLUSIVE (`BLOCKED` on the verdict line, naming the missing capability), a timeout, an
  error, a malformed findings block, or no reply is never approval.
  A capability-only BLOCKED may be recorded as a capability failure
  ([above](#a-blocked-that-only-lacked-a-capability)).

## Gate of record

- The independent cross-family review at the exact pushed SHA is the gate of record. The
  reviewer always comes from the live resolver with every author and subject exclusion, never
  a fixed model.
- A moved head needs a delta review and a fresh exact-head approval before enqueue.
- The red-team exception in `workflow.md` § Merge policy is unchanged and is labelled
  `review_mode=red_team`, never cross-family.
- The optional DeepSeek author pre-check (DS-PRECHECK-1101) is never a review of record and
  never satisfies or waives this gate.

## Declines and disputes

- An author may decline a finding with file:line or test evidence.
- A dispute still unresolved after two replies on the same finding goes to the operator.
- A decline never clears a blocking verdict; only an APPROVE at a new head does. A blocking
  verdict is a P0, P1, or P2 finding, a `SECURITY_VERDICT FAIL`, or `BLOCKED`. A P3-only
  REQUEST_CHANGES is not one: the recorder stores it as an approval with the residuals listed.

## Breakers that still apply

The `local-code-review` checklist Step 6 breakers apply in every round, even when the open
finding count shrinks: the 2x scope-expansion breaker, the two-cycle convergence breaker, a
contract or owner-boundary change, and a needed design decision. A contested verdict escalates
(rules core P6).
