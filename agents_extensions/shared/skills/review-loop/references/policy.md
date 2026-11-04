# Review budget, ledger and severity (single source)

This file is the only copy of the review budget, as set by operator order C-2902
(2026-10-27), which replaced the earlier one-full-plus-delta budget. Rules and skills that
mention the budget point here; do not restate it.

## Budget

A round is one reviewer dispatch at one exact head: round 1 is the full review, later
rounds are deltas. A round is spent when its reviewer is dispatched, whether or not its
verdict is ever recorded; more seats or a retry at a head already dispatched open no round.
For the Anthropic/OpenAI pair below, both seat dispatches at that head count as one round.

- **Default: three rounds** (`budget_tier: default` in the hand-off record). A target repository whose own review policy sets a different automatic budget declares it as `review_rounds` under `repositories` in `scripts/config/review_budget_policy.yaml` (kube-dojo: five), and the recorder applies that budget to its PRs.
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
  `resolved`, `fixed` or `declined`, refuses the round unless it is inside a hyphenated
  compound such as `fail-closed` and the entry has an explicit open phrase. Without an
  open phrase, a closing word inside a compound still refuses the round. A grant never
  resets the rounds already counted, never covers a path outside its scope, and five rounds
  stay the total except under an owner request.
- **Owner request** (#12551). A sealed grant with `blocker_class: owner-request` names in its
  `owner_request` object the `tracker_item` recording the project owner's request for that one
  PR and the `rounds` it records (other classes set it to null); while the latest recorded
  rejection lists the cited finding, it admits the PR's own budget plus exactly that count,
  past five when the budget is already five, and never resets spent rounds. A rejection recorded
  with its findings withheld lists what the sealed reply of the one review run its marker names
  lists, when that run's digest, head, verdict, reviewer and finding count match the comment and
  its reply is not truncated; otherwise it lists nothing (#12585).
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
  A reissued and resealed grant may name one `admission_exclusion` per PR across all grants, binding its task, nonce, head and reply digest to the repository and lineage, with the advisor's sealed `admission_exclusion_attestation` that the complete structured empty-findings BLOCKED reply contains only an execution obstruction, no substantive defect and no security FAIL, validated before dispatch and again against the exact later same-seat, same-head replacement at recording and naming both runs in the receipt; the excluded head stays charged, existing findings stay open, the distinct-head allowance is unchanged, and a failed replacement cannot become another exclusion.
- **One P2 fix-verification round per work lineage** (#12548). A sealed grant with
  `blocker_class: p2-fix-verification` uses the same ruling and approval machinery; its
  `p2_fix_verification` object seals the `rejected_head`, the `candidate_head`, the
  `delta_sha256` of `git diff --binary --full-index <rejected> <candidate>` and the sorted
  `finding_ids` (`finding_id` among them); other classes set it to null. The recorder and the
  dispatcher admit it only when, across the PR's whole ledger: the default three rounds are
  spent; the latest recorded verdict is a trusted REJECT at the rejected head whose open
  findings are exactly the sealed ids, nonempty and all P2; every earlier P0/P1 finding was
  closed by a later structured findings object (bare, fenced or in a `VERDICT`/`SCORE`
  envelope, with no repeated key) that no longer lists it, since a prose entry never closes a
  finding; no verdict is BLOCKED, carries a security FAIL, or is edited or unreadable (a verdict
  recorded withheld is read, security verdict included, from its sealed review run as under the
  owner request, and is unreadable without it);
  and every other review run of the PR, at the candidate head too, is terminal with its verdict
  published, so pushing before a verdict is recorded earns no credit, except that a run its
  seat superseded ([below](#an-unpublished-verdict-that-its-seat-superseded)) stops refusing
  while its BLOCKED or security FAIL still counts, and its findings stay open (and count in
  the all-P2 and sealed-id checks) until a later structured verdict that started after that run
  omits them. A lineage whose closing
  issues are linked to any other PR, open or closed, is refused, because earlier PRs' ledgers
  are not read. It permits round 4 only, never round 5. The dispatcher spends it when it admits
  the reviewer, and the recorder again before posting, in a durable receipt under the PR, its
  head branch and every issue it closes; a failed verification, a reissued grant, another
  reviewer, a replacement PR or a new branch never replenishes it. The reviewer covers the
  [delta scope](#delta-scope) and only the changes needed to correct the named findings,
  including their tests. An APPROVE at that head from any seat, or a P3-only reply that would
  become one, must be a structured reply whose `overall.explanation` begins with the line
  `P2_FIX_DELTA: <delta_sha256> VERIFIED`, which mentions `P2_FIX_DELTA` nowhere else and lists
  no sealed finding; prose cannot attest. Otherwise the recorder refuses the APPROVE: a false or
  unverifiable delta claim is a rejection, and no other seat can approve that head. Security
  failures and the breakers still apply.
- **One full pass, then deltas; depth follows risk.** A change gets one independent
  cross-family full pass (round 1), then only the exact-head delta verification that a fixed
  blocker or a new head still requires, inside the budget above. Qualified deep review stays
  for high and critical risk, security changes and Ukrainian semantics.
- **Stop early when only advisory items remain:** no open blocker means no further round beyond
  the verification review that a fixed blocker or a new head still requires. Remaining
  follow-ups never hold the merge.
- **One reviewer of record per round, or the mixed-family pair below, and no sub-reviewers.** The reviewer does not fan the
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
- **A review that could not happen charges no round, once per lineage** (#12717). The
  lineage's one uncharged capability failure is the earliest-started run that either carries a
  capability-failure event ([below](#a-blocked-that-only-lacked-a-capability)) or, when its
  BLOCKED verdict is already published, a sealed capability-charge adjustment (below). That run
  opens no round, and its published verdict, if any, does not make its head a reviewed head. It
  admits exactly one replacement: the next round, spent like any other when its reviewer is
  dispatched, failed or not. When only the exemption admits that round, the recorder accepts it
  only from the exempt run's seat (family and review profile). Every later capability failure,
  the failed replacement included, stays charged, so retries, concurrent dispatches or claims,
  another reviewer and a moved head never add a second. The dispatcher and the recorder apply
  the same count; `budget-check` names the exempt run under `uncharged_capability_failure` and
  any refused adjustment under `capability_charge_refusals`.
- **Capability-charge adjustment for a published BLOCKED.** A published verdict and its reply
  are never changed or reclassified. The CTO issues a sealed ruling with `blocker_class:
  capability-charge`, `finding_id: null`, null `p2_fix_verification` and `owner_request`, and a
  `withheld_capability` object naming the missing `capability` and the `uncharged_run` by
  `task_id`, `run_nonce`, `reviewed_sha` and `reply_sha256`, bound to the repository, PR,
  lineage and changed paths like any grant. The designated advisor's sealed APPROVE carries an
  `admission_exclusion_attestation` of exactly `{complete_reply_capability_obstruction_only,
  no_substantive_defect, no_unresolved_material_uncertainty, no_security_fail}`, each true, after
  reading the complete published reply. The recorder also requires that the run's intact,
  verbatim publication is a structured BLOCKED with `findings: []`, no severity and no non-PASS
  security verdict in any decoded string, and that a reply declaring `missing_capabilities`
  declares the ruled one. A reply declaring none is a legacy reply: nothing is inferred from its
  prose, and only this attestation adjusts its charge. The ruling admits no round itself and must
  be issued after the run. The BLOCKED stays until an APPROVE at a new head
  ([clearing](#clearing-a-recorded-rejection)); the capability failure gives no security
  sign-off and fills no seat.
- **The replacement carries the missing evidence inline.** Its brief answers the question the
  failed run could not: for `ci-logs`, the exact head SHA, the CI run and job ids, their
  conclusions, and the relevant test output or log excerpts. Conclusions alone are not enough
  when the review needed the logs. A replacement that is again blocked for the same reason is
  charged.
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

Resolve `PRIMARY_REPO` and `PY` as in the [review-loop setup](../SKILL.md#review-loop).
Use the primary recorder so the caller's branch age cannot select its rules.

```bash
"$PY" "$PRIMARY_REPO/scripts/review/record_cf_verdict.py" capability-failure --task-id "$REVIEW_TASK" --pr "$PR" \
  --capability <sources-mcp|test-execution|shell|browser|checkout-data|ci-logs> --authority claude-cto
```

- It qualifies only when the reply is `BLOCKED` with a known count of zero findings, which only a
  structured `code-review-findings.v1` reply proves, and the missing capability is evidenced:
  `sources-mcp` by the run's recorded count of zero Sources MCP calls on the Ukrainian profile,
  any other capability by the reply's `missing_capabilities` list beside its findings. `ci-logs`
  means the reviewer could not read the CI or execution logs its review needed. A prose
  reply, any finding (P3 included), a severity or a non-PASS security verdict in any decoded
  string, or "no in-scope blocker" does not qualify, and that BLOCKED is handled as today.
- The event is bound to the run, its reviewed head and its reply digest; the reply stays as it is.
  It is not a verdict: it approves nothing, rejects nothing and fills no seat, so every required
  review still has to happen. Only the lineage's first capability failure opens no round
  ([budget](#budget)). A run with a published verdict cannot be reclassified, and a classified
  run's verdict cannot be published; a published capability-only BLOCKED uses the
  capability-charge adjustment instead.

## Before the review: frozen scope and cheap checks first

Cheap deterministic checks run before any model review, and the reviewer's budget is not spent
on what they already report.

- **Frozen scope.** The frozen brief ([review-loop](../SKILL.md#steps) step 1, [brief](brief.md))
  also names the applicable contracts, not only the outcome, acceptance criteria and non-goals.
- **Author evidence at the exact head.** Before round 1 and before every delta round the
  author supplies the results of the affected static checks (ruff, the repository's custom
  lints under `scripts/hygiene`, `scripts/audit` and `scripts/lint`, and type checking where
  it runs), the affected tests, the behaviour evidence the change needs and any required
  canaries, as the brief's checks-already-run list. Reuse the same-head CI results instead of
  re-running them.
- **The reviewer spends no finding on what those checks report.** A defect a supplied check
  already reports is the author's to fix before the round. The reviewer's own independent
  held-out checks stay the reviewer's; the author's results do not replace them.

## Ledger and stable finding ids

- Every finding gets a stable id (`F1`, `F2`, …) that keeps its number across rounds.
- Findings are collected by defect class: a round reports every instance of a class under one
  id, not one instance per round.
- The ledger records, per id: severity, defect class, evidence mode (probe or test output,
  code-path proof, or source evidence), disposition (`in_scope_blocker`, `follow_up`,
  `stop_and_escalate`), the round that raised it, its state (open, fixed with evidence,
  declined with evidence, escalated) and its owner.
- Before a PR exists the ledger lives in the task result with the review evidence. Once the PR
  exists it goes in the PR body (public-safe fields only, see
  [delivery](../../full-send/references/delivery.md)).

## Delta scope

- A delta review covers the open finding ids, the hunks changed since the last reviewed head,
  the callers and invariants those hunks affect, and weakened or deleted tests in the fix diff.
  It does not re-review code that already passed.
- A finding the author fixed is reopened only with new evidence ([blocker
  evidence](#severity)). A new blocker in code that already passed review needs a concrete
  trigger: a P0, P1 or P2 failure the fix diff introduced or exposed, shown with file:line, a
  test or probe output. A pre-existing defect the change did not introduce or expose is a
  follow-up ([scope of blocking](#severity)).

## Severity

Severity follows impact on behaviour or readers, ranked by impact and likelihood.

**Blocker evidence.** Every blocking finding states its severity, a reachable trigger, the
expected and the actual behavior, the impact and its evidence. The evidence is observed probe
or test output, a complete code-path proof from the trigger to the failure (file:line at each
step), or authoritative source evidence that demonstrates the contradiction; a citation alone
is not enough. Credible uncertainty about a material failure gets a bounded verification or an
escalation. A capability the reviewer lacked is never approval.

**Scope of blocking.** Items 1 to 3 below apply to a defect the change introduces, exposes or
materially needs fixed. A defect at any priority that the change did not introduce or expose
is tracked as a follow-up, unless the change materially needs it fixed. `SECURITY_VERDICT
FAIL` always blocks, whatever introduced it.

1. P0, P1, and credible uncertainty about a material failure keep blocking until verification
   or escalation settles them.
2. A demonstrated, unintended loss of previously correct behavior or of an existing refusal guarantee introduced by the PR blocks when its priority is P0, P1, or P2. Cite the pinned base and head, the same triggering inputs and preconditions and the contract violated, with the blocker evidence above. An intentionally approved contract change, preference, or speculative difference is not a regression. An omitted or bounded trigger does not exempt a demonstrated P0, P1, or P2 regression. Disputed material contract applicability escalates. A P3 regression does not block.
3. Every other confirmed P2 defect is fixed in the PR or tracked before enqueue on an OPEN issue covering that finding. The worker or driver reports it through Fleet Comms; the CTO searches for and updates a matching open issue, or creates one under Work intake. The enqueue owner verifies its open state and coverage, and records the issue link, stable finding ID and owner in the ledger. A report awaiting CTO disposition is insufficient. Tracking alone requires no additional review round.
4. P3 findings, including a P3 regression, nits, style and preferences, speculative future requirements and score-only shortfalls are advisory: they never block and never open a review round or widen the scope. They are recorded once, as residuals on an open issue. A P3 defect class seen in two reviews is not raised again: it becomes a check ([review yield](#review-yield)). A factual language error in teaching content is not P3 (item 5). A new contract or design decision escalates before implementation ([breakers](#breakers-that-still-apply)). A reply whose verdict is REQUEST_CHANGES and whose open findings are all P3 is recorded as an approval with those residuals listed: the findings stay verbatim and visible, and the `fleet/cross-family-review` status is success. The recorder reads the priority the reply already carries.
5. Ukrainian and teaching content: a factual language error in added or edited text is never P3 and blocks at P2 or higher. That covers a wrong meaning, stress, form or grammar, a Russianism or calque, an unsupported claim, and a Soviet-normative source used as the modern norm. Wording, flow and polish findings in teaching content are P3 and go to a later polish pass. The Ukrainian profile ([ukrainian](ukrainian.md)) keeps its own seats and verification.

Review budgets, seats, ladders, and exact-head binding are unchanged. A P0, P1, or P2 finding, and a demonstrated regression at those priorities, keeps the handling in items 1 to 3 and 5. Round exhaustion does not turn that rejection into approval and grants no extra round. Reviewers keep the priority the impact supports: they do not raise a P3 to force another round, and they do not lower a P0, P1, or P2 to clear it. Filing or linking the residual issue consumes no review round.

- `SECURITY_VERDICT FAIL` always blocks and is never downgraded to a follow-up or a residual. A security verdict whose value is not exactly pass is the same refusal, including a conditional pass. A reply that does not fit in the record stays a rejection. A repair round whose reply does not attest that the delta is only the repair stays a rejection, including a marker posted earlier on that head.
- INCONCLUSIVE (`BLOCKED` on the verdict line, naming the missing capability), a timeout, an
  error, a malformed findings block, or no reply is never approval.
  A capability-only BLOCKED may be recorded as a capability failure
  ([above](#a-blocked-that-only-lacked-a-capability)).

## Gate of record

- The independent cross-family review at the exact pushed SHA is the gate of record. The
  reviewer always comes from the live resolver with every author and subject exclusion, never
  a fixed model.
- **Anthropic/OpenAI mixed authorship (#10712, approved 2026-11-03).** For code and infra
  branches authored by exactly these two families, `resolve-reviewer` returns two `quorum`
  seats. Each seat's `scope` names the other author family, its commit SHAs, and the exact
  `context_head`. Give each reviewer that scope and the whole PR diff as context. Resolve
  one qualified Anthropic seat and one qualified OpenAI seat through the existing catalog;
  risk floors, security sign-off roles, subject exclusions and `SELF_REVIEW_DETECTED` apply
  per seat. Record both verdicts. Enqueue requires both APPROVEs at the same exact head;
  either rejection blocks, and a moved head voids both. One pair counts as one round.
  Verified app-bot commits have no model family and remain part of the whole-diff context.
  A commit carrying both families' trailers cannot be partitioned without assigning a
  reviewer its own family's work and fails closed. Single-family, red-team and zero-trailer
  plans remain unchanged. This rule adds no reviewer seat or override.
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

## Review yield

- **Where it is recorded.** The PR-body ledger holds each finding, structured or prose, with
  its evidence mode, severity and validated disposition; a prose observation is recorded even
  when the findings array is empty. The round report of `review-loop` (its Stop and report
  section, which already names reviewer model, family and harness) also records the unique
  verified catches, false positives, escaped defects (found after approval), review and
  repair tokens and elapsed time, with the risk and task family. A unique verified catch is a
  stable finding id counted once across all rounds, confirmed by its evidence mode and not a
  false positive. Per-model yield is aggregated from those records.
- Usage that was not reported stays `unknown`, never estimated. A small or confounded sample
  does not justify a change of tier or seat.
- **Recurring findings become checks.** A defect class that review catches a second time is
  turned into a lint rule or a test, so review stops paying for it; this includes a P3 class seen in two reviews, which is filed instead of raised again. The worker or driver
  reports the class to the CTO through Fleet Comms as an issue proposal for that check; the
  CTO files it. This is not a new round and does not hold the merge.
