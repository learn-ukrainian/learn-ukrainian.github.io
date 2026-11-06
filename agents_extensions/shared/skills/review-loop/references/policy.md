# Review budget, ledger and severity (single source)

This file is the only copy of the review budget, as set by operator order C-2902
(2026-10-27), which replaced the earlier one-full-plus-delta budget. Rules and skills that
mention the budget point here; do not restate it.

## Budget

A round is one review at one exact head: round 1 is the full review, later rounds are deltas.
A round is spent when its reviewer is dispatched, whether or not its verdict is ever recorded;
more seats or a retry at a head already dispatched open no round. For the Anthropic/OpenAI pair
below, both seat dispatches at that head count as one round.

- **Three completed rounds per lineage, for every change.** Round 1 is the full review. Round 2
  is a delta over every hunk changed since the last reviewed head, P2 fixes included. Round 3
  verifies any remaining demonstrated blocker, including an original one whose fix failed.
  Security, data-loss and other high-risk changes get the same three rounds
  ([where it stays strict](#where-review-stays-strict)). A target repository whose own review
  policy sets a different automatic budget declares it as `review_rounds` under `repositories`
  in `scripts/config/review_budget_policy.yaml` (kube-dojo: five), and the recorder applies
  that budget to its PRs.
- **Scope is frozen at round 1; new code goes in a new PR.** Later rounds review the fixes to
  the ledger's findings and the hunks those fixes change. New behaviour, or code that the
  findings do not need, goes in a new PR with its own lineage.
- **Nobody buys a round.** No ruling, request, grant or advisory decision adds a round, and a
  new reviewer, a replacement PR or a new session does not reset the count. **The end of the
  budget is never approval**: the author splits the PR or redesigns the approach, and escalates
  to the CTO and the advisors (rules core P6).
- **A failed review execution is not a completed round.** A timeout, an error, a malformed
  reply or a capability-only BLOCKED approves nothing. Rerun it once at the same head, which
  opens no new round; a second failure escalates to the CTO. Moving the head instead spends the
  failed head's round. A capability-only BLOCKED is also uncharged once per lineage (below).
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
  and adds no round. Rounds 2 and 3 go to the same reviewer of record
  ([routing](#which-model-reviews)).
- **Optional DeepSeek pre-check is not a review.** The optional DeepSeek author pre-check
  (DS-PRECHECK-1101) is never a review of record, opens no round, and never satisfies or waives
  the cross-family review gate; no round budget, risk floor, or reviewer selection changes.
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
  decision for the PR's current head (admitted, with any exemption or repair-round receipt, or
  the refusal that names what to escalate), lists each head reviewed without a recorded verdict
  under `unrecorded_rounds`, and writes nothing.
- **An unpublished verdict refuses later rounds** until its own seat (one reviewer family on
  one review profile) records a later verdict at another head (`review_lineage.superseded_runs`).
  The superseded run's head still counts against the budget, and its findings stay in the
  ledger until they are fixed, declined or escalated.
- **A review that could not happen charges no round, once per lineage** (#12717). The
  lineage's one uncharged capability failure is the earliest-started run that carries a
  capability-failure event ([below](#a-blocked-that-only-lacked-a-capability)). That run
  opens no round, and its published verdict, if any, does not make its head a reviewed head. It
  admits exactly one replacement: the next round, spent like any other when its reviewer is
  dispatched, failed or not. When only the exemption admits that round, the recorder accepts it
  only from the exempt run's seat (family and review profile). Every later capability failure,
  the failed replacement included, stays charged, so retries, concurrent dispatches or claims,
  another reviewer and a moved head never add a second. The dispatcher and the recorder apply
  the same count; `budget-check` names the exempt run under `uncharged_capability_failure`.
- **The replacement carries the missing evidence inline.** Its brief answers the question the
  failed run could not: for `ci-logs`, the exact head SHA, the CI run and job ids, their
  conclusions, and the relevant test output or log excerpts. Conclusions alone are not enough
  when the review needed the logs. A replacement that is again blocked for the same reason is
  charged.
- The budget and the ledger follow the work (issue and branch lineage); the recorder's receipts
  carry the count across replacement PRs on the same branch.

## Clearing a recorded rejection

A recorded `CHANGES_REQUESTED` or `BLOCKED` is cleared only by an APPROVE at a **new** head;
the recorder refuses a same-head APPROVE after it. So an escalation ruling on a recorded
rejection is followed by a head move (the fix, or a base update with
`"$PY" -m scripts.publish pr-update-branch --number "$PR"`) and one more round at that head.

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
  run's verdict cannot be published; a published capability-only BLOCKED stays charged.

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

Severity follows impact on behaviour or readers, ranked by impact and likelihood. Findings use
the `code-review-findings.v1` object with its wire priorities `P0` to `P3`.

**Reachability under the input contract.** Every P0–P2 finding carries `sources` that show its
trigger is reachable under the input contract the round-1 brief froze (what executes, on which
data, and who controls the input): path:line in the tree, a published-history entry, or a
reproduction the author can run. For a one-shot frozen execution, the frozen tree and its
invocation are the whole input, and a trigger absent from them is P3. For a reusable tool, any
input its contract admits counts. Unknown is not absent: a reviewer who cannot establish
reachability says so, and the author answers with a reproduction or a code-path proof.

**Applicability, not demotion.** The author may answer a P0–P2 finding with `not_applicable`
and its proof (command and output, or code path) in the ledger. The author never edits the
priority. The reviewer of record confirms or contests the claim in the delta round, and the
evidence settles a contested claim there, without a new round. A `not_applicable` that proves
wrong reopens the finding with the evidence, inside the same budget.

**Blocker evidence.** Every blocking finding states its severity, a reachable trigger, the
expected and the actual behavior, the impact and its evidence. The evidence is observed probe
or test output, a complete code-path proof from the trigger to the failure (file:line at each
step), or authoritative source evidence that demonstrates the contradiction; a citation alone
is not enough. Credible uncertainty about a reachable P0–P2 trigger gets a bounded verification
or an escalation. A capability the reviewer lacked is never approval.

**Approval rule.** Approve when no P0 or P1 finding with a reachable trigger is open, no
demonstrated P2 regression is open (item 2), and the security verdict is pass. Every other
confirmed P2 follows item 3, and P3 follows item 4.

**Scope of blocking.** Items 1 to 3 below apply to a defect the change introduces, exposes or
materially needs fixed. A defect at any priority that the change did not introduce or expose
is tracked as a follow-up, unless the change materially needs it fixed. `SECURITY_VERDICT
FAIL` always blocks, whatever introduced it.

1. P0 and P1 findings with a reachable trigger, and credible uncertainty about a reachable
   P0–P2 trigger, keep blocking until verification or escalation settles them.
2. A demonstrated, unintended loss of previously correct behavior or of an existing refusal guarantee introduced by the PR blocks when its priority is P0, P1, or P2. Cite the pinned base and head, the same triggering inputs and preconditions and the contract violated, with the blocker evidence above. An intentionally approved contract change, preference, or speculative difference is not a regression. An omitted or bounded trigger does not exempt a demonstrated P0, P1, or P2 regression. Disputed material contract applicability escalates. A P3 regression does not block.
3. Every other confirmed P2 defect is fixed in the PR when that is cheap and safe, otherwise tracked before enqueue on an OPEN issue covering that finding. The worker or driver reports it through Fleet Comms; the CTO searches for and updates a matching open issue, or creates one under Work intake. The enqueue owner verifies its open state and coverage, and records the issue link, stable finding ID and owner in the ledger. A report awaiting CTO disposition is insufficient. Tracking alone requires no additional review round.
4. P3 findings, including a P3 regression, nits, style and preferences, speculative future requirements and score-only shortfalls are advisory: they never block and never open a review round or widen the scope. They are recorded once, as residuals on an open issue. A P3 defect class seen in two reviews is not raised again: it becomes a check ([review yield](#review-yield)). A factual language error in teaching content is not P3 (item 5). A new contract or design decision escalates before implementation ([breakers](#breakers-that-still-apply)). A reply whose verdict is REQUEST_CHANGES and whose open findings are all P3 is recorded as an approval with those residuals listed: the findings stay verbatim and visible, and the `fleet/cross-family-review` status is success. The recorder reads the priority the reply already carries.
5. Ukrainian and teaching content: a factual language error in added or edited text is never P3 and blocks at P2 or higher. That covers a wrong meaning, stress, form or grammar, a Russianism or calque, an unsupported claim, and a Soviet-normative source used as the modern norm. Wording, flow and polish findings in teaching content are P3 and go to a later polish pass. The Ukrainian profile ([ukrainian](ukrainian.md)) keeps its own seats and verification.

A P0, P1, or P2 finding with a reachable trigger, and a demonstrated regression at those priorities, keeps the handling in items 1 to 3 and 5. Round exhaustion does not turn that rejection into approval and adds no round. Reviewers keep the priority the impact supports: they do not raise a P3 to force another round, and they do not lower a P0, P1, or P2 to clear it. Filing or linking the residual issue consumes no review round.

- `SECURITY_VERDICT FAIL` always blocks and is never downgraded to a follow-up or a residual. A security verdict whose value is not exactly pass is the same refusal, including a conditional pass. A reply that does not fit in the record stays a rejection. A repair round whose reply does not attest that the delta is only the repair stays a rejection, including a marker posted earlier on that head.
- INCONCLUSIVE (`BLOCKED` on the verdict line, naming the missing capability), a timeout, an
  error, a malformed findings block, or no reply is never approval.
  A capability-only BLOCKED may be recorded as a capability failure
  ([above](#a-blocked-that-only-lacked-a-capability)).

## Where review stays strict

- **Security and data loss** (hooks, launchers, credentials, admission, sandbox, guards,
  `sources.db`, VESUM, generations): a reachable trigger from an untrusted boundary is enough
  evidence, because the attacker chooses the input, and `not_applicable` needs a code-path
  proof that the reviewer confirms. The budget is the same three rounds.
- **Ukrainian content:** a factual language error blocks at P2 or higher (item 5 and the
  [Ukrainian profile](ukrainian.md)).
- **Publication:** the OPSEC scans and the public-history policy stay CI hard gates.

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

## Which model reviews

This table is the provisional routing default by risk and stage. The live resolver still
selects every reviewer ([gate of record](#gate-of-record)): until the resolver and the catalog's
suitability order adopt the table, a driver follows it only where the resolver returns that
seat. Cost is measured per approved PR; if Sonnet 5.5 rounds lead to more repair rounds than
Opus 5.5 rounds, the middle-tier default moves back.

| Risk and stage | Seat |
| --- | --- |
| Evidence: CI, `git grep`, reproductions, log triage, finding classification | Deterministic tools first; Haiku 5.5 or Luna for bounded triage. Never a verdict. |
| Low or medium risk, round 1, Codex or Grok author | Sonnet 5.5 (catalog role `strong_review`) |
| Low or medium risk, round 1, Claude author | Sol 6.1: the cross-family side has no middle tier, Terra is excluded from critique and approval, and Luna from formal review |
| Rounds 2 and 3, any risk | The same reviewer of record on the delta; no second reviewer |
| High or critical risk: security, data loss, concurrency, review-gate changes | Opus 5.5 or Sol 6.1 every round; the resolver already excludes Sonnet 5.5 at `--risk critical` |
| Ukrainian content | Unchanged: Gemini via AGY with Sources, per the [Ukrainian profile](ukrainian.md) seats |
| Designated approval and plan critique | Opus 5.5 and Sol 6.1, as the catalog records |

## Declines and disputes

- An author may decline a finding with file:line or test evidence, or answer it with
  `not_applicable` and its proof ([applicability](#severity)).
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
