# Writer-worker lifecycle

Normative SHA-256: `dca41dbb929094ab2b9782b3ade202e00c299fda3089916eacef3db2a7d93437`

Status: round-7 proposal, pending new-head independent review and designated approval. No implementation or cleanup is authorized by this document alone.
Issue: [#10559](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/10559).
Parent: [#7919](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/7919).
Round-6 source revision: `556d76795c8b63273ffad305d0cf44e8c59cd7e7` from freshly fetched `origin/main`.
Imported exact-r5 artifact: `276b53a4fa9f1e3114bb9def2bb1083815964804`, preserving both original commits' authorship.
Historical appendices retain their original source revisions.

The digest covers the exact UTF-8 bytes between the two normative markers, excluding the markers themselves.
It includes the newline immediately after the opening marker and the newline immediately before the closing marker.
Changing those bytes requires a new digest and review. Risks, critic traceability, and evidence are outside the digest.
Editorial changes there cannot alter the normative contract; changed requirements belong inside the markers.
`PROJECT_PYTHON` below denotes the task-prescribed absolute primary project interpreter, never a worktree environment.

```bash
"$PROJECT_PYTHON" - <<'PY'
from hashlib import sha256
from pathlib import Path
p = Path('docs/architecture/writer-worker-lifecycle.md')
b = p.read_bytes()
s = b.split(b'\n<!-- normative:start -->', 1)[1].split(b'<!-- normative:end -->\n', 1)[0]
print(sha256(s).hexdigest())
PY
```

<!-- normative:start -->

## Outcome and scope

Every dispatched writer has one outcome, one issue, one branch, and one canonical worktree.
Each settled writer handback is MERGED, PUSHED, or ABANDONED, with verified cleanup.
PUSHED keeps the lifecycle active until later MERGED or ABANDONED finality.
A process exit, timeout, rejected gate, or failed provider invocation is an attempt result, never a lifecycle disposition.
There is no local-only end state. New writer records cannot emit `needs_finalize`.
All active consumers distinguish lifecycle custody from attempt results. Historical evidence may retain the old literal as migration input.
Read-only and review tasks use the separate replacement contract below; they cannot claim a writer disposition.

The writer commits, passes the pre-push gate, pushes, requests independent cross-family review,
fixes findings in the same worktree, obtains a durable pre-PR exact-head approval receipt, opens the PR,
publishes and verifies the PR verdict projection, and waits for CI. Material findings require driver handback as defined below.
The writer never merges, enqueues, arms auto-merge, or approves its own work.
The review-request actor in that flow depends on the designated choice of Option A or Option B below.
The merge-queue keeper enqueues only with current exact-head review and green required CI.
The common reaper proves removal. The lane driver owns any interrupted or blocked lifecycle until disposition.

The issue denominator remains the original ten end shapes. Two additional recovery shapes extend evaluation to twelve.
Independent held-out evaluation covers all twelve,
plus refusal cases for dirty files, ignored output, a moved remote head, a failed gate, unknown probes,
a live claimant, and ambiguous reuse. Fixtures must come from a reviewer outside the implementation author's family.
Passing transport, record-shape checks, or unit tests alone does not prove cleanup.

This specification covers lifecycle evidence, bounded continuation, reuse, cleanup, and migration.
It does not implement any change, create implementation issues, or authorize host deletion.
Crash-rescue identity remains owned by #10537. Bulk corpus and other non-task payloads remain outside this scope.

## Dispositions and receipts

Each verified worker handback has exactly one of the following dispositions. Only MERGED and ABANDONED are lifecycle-final.
PUSHED releases local worktree custody while the lifecycle remains active for review, CI and landing.

| State | Required end shape | Transition owner | Required evidence | Receipt |
| --- | --- | --- | --- | --- |
| (a) MERGED | PR merged; local tree, local branch, and remote branch absent | Keeper lands; Infra/common reaper cleans; lane driver verifies | Exact PR head and merge SHA, successful reviewed-head relation to landed content, no active claimant or process, complete cleanup verification | `writer-lifecycle.v1` with `disposition: MERGED`, linked merge-closeout and removal receipts |
| (b) PUSHED | Exact gated head on GitHub; review or PR remains actionable; local tree absent | Writer publishes; common reaper removes after attempt exit; lane driver tracks review and CI | Passed exact-head pre-push gate, remote head equals local head, accounted-for tree contents, no active claimant or process, remote branch still present after removal | `writer-lifecycle.v1` with `disposition: PUSHED`, gate, remote-head, review or PR, and removal receipts |
| (c) ABANDONED | Issue holds a digest-matched public reason; local tree and every task branch ref absent | Lane driver authorizes abandonment; common reaper removes; lane driver verifies | Identity-checked driver decision and matching issue copy, exact content identity, no active claimant or process, authorized task-only removal | `writer-lifecycle.v1` with `disposition: ABANDONED`, decision digest, issue copy, and removal receipts |

PUSHED is a complete worker handback, not a completed product issue. The driver continues review, CI, and landing.
A later merge supersedes PUSHED with MERGED using the same lifecycle identity and append-only history.
A deliberate cancellation of pushed work supersedes it with ABANDONED after the issue record and branch cleanup.
A review or CI fix reactivates the same lifecycle and canonical tree. Previous receipts remain historical.
No process exit can manufacture one of these states without its evidence.

The `writer-lifecycle.v1` schema extends the existing `task-lifecycle.v1` ledger for worker custody.
It retains the canonical `task-identity.v1` envelope and authoritative Git/GitHub observations.
Task records link the existing ledger and its removal receipts; they store attempt telemetry, not a second lifecycle authority.
Required writer fields are:

- `lifecycle_id`, issue number, parent stream, driver identity, writer model/family/harness, and canonical worktree binding.
- Admission-index entry/digest, admission time, and immutable `activation_epoch` binding for post-activation lifecycles.
  Pre-activation lifecycles retain a null epoch and cannot acquire the new precondition retroactively through migration.
- Original creator task/run nonce, ordered attempt identities, actual branch at each checkpoint, and exact local head.
- Current phase, observed attempt result, bounded continuation counters, and next action with its accountable owner.
- Registered lane identity, `blocked_since`, immutable `blocked_deadline`, overdue flag, escalation receipt, and lane blocked count.
- Legacy inventory receipt/digest, immutable `legacy_clock_started_at`, cohort budget/membership, separate legacy counts,
  and any admission exemption's driver grant, dependency, owned paths and finite execution budget.
- Gate receipt path/digest, command outcome, gated SHA, remote branch, observed remote SHA, and observation time.
- Exact-head pre-removal local-readiness observation path/digest, commit/trailer inventory, publication and removal linkage.
- Original directory baseline plus ordered recreation-generation receipts binding predecessor removal, new inode and baseline digest.
- Canonical durable review-state path/digest, pre-PR verdict receipt and its later PR-publication binding.
- Review request reservation, resolver receipt/digest, fixed brief digest, driver retry decision if any, review task,
  verdict receipt/digest, reviewer provenance, reviewed SHA, PR identity, required CI receipts, and merge proof when applicable.
- Handback `disposition`, issue abandonment record when applicable, deletion authority, and common-reaper receipt path/digest.
- Append-only lifecycle rejection chain across all heads, stable finding IDs, successor brief carry-forward digest,
  and driver disposition receipts for every prior material finding; changing task, branch or PR cannot reset the chain.
- Cleanup observations for registered tree, directory, local refs, and remote refs, with UTC timestamps and typed unknowns.

Disposition receipts have no unknown required field. The existing
`agents_extensions/shared/schemas/task-lifecycle.v1.schema.json` gains an optional typed `writer` property
with `schema: writer-lifecycle.v1` and the fields above. Its absence preserves non-writer ledger validation.
Writer-aware readers require that property for governed writers; they cannot accept a free-form task-record status as evidence.
I-01 owns this schema and validator/closeout compatibility; I-04 owns the canonical contract documentation.
This extension preserves the existing product `current_state` and `terminal_goal`; worker PUSHED never maps to product MERGED.
Receipt writes use atomic replacement and immutable attempt history.
A removal receipt binds lifecycle, creator, every current claimant, run nonces, branch, head, proof digests,
removal action, post-removal Git registration and filesystem checks, remaining refs, and timestamp.
A `skipped`, `retained`, timeout, or error result never proves removal.
Public issue records omit host paths, credentials, transcripts, and private diagnostic bodies.

## End shapes

Evaluate MERGED evidence first. Next evaluate an explicit lane abandonment. Otherwise evaluate PUSHED evidence.
Recovery may change the observed shape before classification. The following table assigns exactly one disposition to each settled shape.
An inability to establish a row's evidence enters the bounded blocked-custody contract below, with a named driver.
Blocked custody never satisfies handback or completion.

| ID | Observed end shape | Assigned state | Transition owner and condition | Evidence and receipt |
| --- | --- | --- | --- | --- |
| D-01 | Pushed and PR open | (b) PUSHED | Writer publishes after approval; reaper removes when the attempt exits | Exact gated remote head, PR/review provenance, content accounting, absence probes, PUSHED removal receipt |
| D-02 | Pushed and awaiting review | (b) PUSHED | Writer requests review; reaper removes after the bounded active round ends | Exact gated remote head, durable review request with owner, PUSHED receipt |
| D-03 | Merged | (a) MERGED | Keeper lands; reaper removes any remaining tree and all branch refs | MERGED PR, reviewed-head landing relation, closeout absence checks, MERGED receipt |
| D-04 | Review REQUEST_CHANGES with fix rounds | (b) PUSHED | Writer fixes within bounded rounds; unresolved findings travel with a pushed head and named driver | Last exact gated remote head, findings and reviewer identity, remaining-round count, no dirty/unpushed fix residue, PUSHED receipt |
| D-05 | Gate refusal persists after bounded repair | (c) ABANDONED | Driver abandons when there is no actionable gated remote head; if one exists, delta discard first changes the shape to D-01/D-02/D-04 | Literal gate failure, exact rejected content, driver-attributed discard decision and issue copy; ABANDONED or the new shape's PUSHED receipt |
| D-06 | Session budget exhausted before push, bounded continuation cannot publish | (c) ABANDONED | Driver takes custody, records the exhausted budget and abandonment decision | Attempt/budget history, exact commit and dirty-content identities, attributed issue record, ABANDONED receipt |
| D-07 | Worker crash or timeout with commits, bounded continuation cannot publish | (c) ABANDONED | Driver records the failure and disposition; reaper waits for proven process absence | Attempt identity, local heads and remote-copy assessment, explicit discard authorization for unique work, ABANDONED receipt |
| D-08 | Worker crash with dirty files only, bounded continuation cannot publish | (c) ABANDONED | Driver records which content is discarded and why | Dirty-content manifest digest, tracked/untracked/ignored inventory, attribution, issue record, ABANDONED receipt |
| D-09 | Reused tree whose work is pushed, neither merged nor abandoned | (b) PUSHED | Driver settles the whole reuse cohort; reaper removes the canonical tree | Creator and all claimant identities, actual branch/head, gated remote head, cohort release proof, PUSHED receipt |
| D-10 | Abandoned by lane decision | (c) ABANDONED | Driver records the decision; reaper deletes only the described task scope | Read-back issue record, full content and ref inventory, absence proof, ABANDONED receipt |
| D-11 | PR closed unmerged by an external actor, without a lane cancellation | (b) PUSHED after authorized actionable recovery; otherwise blocked pending D-10 decision | Driver records authorized recovery or attributed abandonment; operator closure forbids automatic restore/replacement and needs operator direction before reopening | Closed-PR observation and closer or explicit UNKNOWN, live remote H, recorded driver decision, actionable review/next owner and removal receipt for PUSHED; D-10 requires its own abandonment and residual evidence |
| D-12 | Local branch ref remains after its remote branch was deleted, with no merge proof | (c) ABANDONED | Driver authorizes exact local-ref/content abandonment; reaper removes it after identity and process checks | Live remote-absence proof, exact local head and content manifest, attributed decision and matching issue copy, all-ref absence receipt |

For D-04, REQUEST_CHANGES is not approval. No new PR opens until the current head has APPROVE.
A PR already open before later findings remains blocked from enqueue until fresh approval and CI pass.
For D-05 through D-08, successful continuation changes the shape to D-01, D-02, or D-04.
The table does not authorize abandonment merely because a deadline or retry counter expired.
The lane driver must make and record that decision. If the driver cannot safely decide, the blocked deadline and escalation apply.
D-09 does not override D-03 or D-10. Reuse is a cleanup obligation, never a fourth disposition.
D-11 becomes D-10 only on a new attributed driver abandonment decision, never on the close event alone.
If its remote is absent, reconcile as D-12. D-11 retains the existing same-head reservation and verdict.
Replacement PR creation does not authorize another review. Unknown closure authority blocks restoration.
After operator closure the driver seeks operator direction before reopening or replacing the PR.
If reopening is declined, will not be pursued, or the closer remains UNKNOWN at triage, the driver may instead
record `writer-abandon.v1` with `reason_code: lane_cancelled`, the closure observation and explicit cancellation reason.
That decision must bind all content/refs, include non-empty `residual_issue` and `residual_owner` for unmet ACs,
and satisfy the same event attribution, public read-back and unique-content guards as D-10. Unknown closer is recorded,
not invented. Cancelling this lifecycle does not override an operator instruction to preserve its content.
While a decision is pending, keep the lifecycle blocked with its existing clock, owner and protected refs, even if the tree
was already removed under an earlier PUSHED receipt. A closed inactive PR alone cannot prove a new actionable PUSHED handback.
An attributed abandonment followed by verified task-only cleanup is the defined exit when restoration is unavailable.
D-12 with actual MERGED evidence is D-03. Proven authorized republication changes D-12 to a PUSHED shape.

## Bounded blocked custody

A **lane** is one registered owning stream epic and its accountable driver assignment/launcher-held lease.
It is not a model, provider, harness, task, or branch prefix. Every lifecycle binds that stream identity.
Unknown/conflicting stream membership refuses ordinary admission; changing drivers cannot reset debt.

For new lifecycles, the proposed maximum blocked interval is **24 hours**, frozen at first entry.
The proposed ordinary per-lane limit is **one blocked writer lifecycle**, including escalated and overdue custody.
The new-lifecycle clock begins at the first failed disposition or continuation prerequisite, not the driver's next visit.
Retries, restarts, reason changes and driver changes cannot reset it. Verified MERGED/ABANDONED ends the clock;
PUSHED clears undisputed local-custody blocking, subject to the material-dispute exception below.
Ordinary undisputed review/CI waiting after verified PUSHED tree removal does not consume this slot.
The material-finding dispute exception below keeps its attention clock/slot until adjudication or abandonment.
These limits and the exceptions below await designated approval under OD-02.

Legacy debt uses a separate clock and admission budget. Its clock starts at the first authorized migration inventory
receipt for the cohort, `legacy_clock_started_at`, not at historical failed disposition timestamps.
Read-only research inventories before authorized migration do not start that clock.
The receipt freezes membership and start time; re-inventory, restart and activation cannot reset it.
Each legacy deadline is that start plus 24 hours. Later discoveries need a separately authorized inventory cohort
with their first inventory time; existing debt cannot be reclassified or reset.
Legacy items count under `legacy_blocked_writer_count` and `legacy_overdue_writer_count`, never the ordinary slot.
The operator approves a finite cohort budget naming maximum unresolved legacy items and remaining execution allowance.
Unknown/exceeded budget refuses ordinary new outcomes. Legacy debt within budget does not consume the ordinary slot.

Authorized migration and necessary prerequisite dispatches are exempt from the ordinary slot and legacy-budget refusal.
The current driver records a bounded grant naming the cohort or blocked lifecycle, dependency, owned paths,
finite attempts/time and accountable owner. Migration also needs operator-approved cohort/scope; a prerequisite
must unblock that named disposition and cannot introduce an unrelated outcome. The exemption waives only this
debt-based refusal, never DoR, disk/capacity, review, custody, deletion or other hard gates. Exempt blocked work stays counted.
I-04 migration code must land before debt-based admission refusal switches on. Its writer can be dispatched before
activation; authorized recovery prerequisites remain dispatchable afterwards.

The existing Fleet plane/attention board and status output expose per lane `blocked_writer_count`, `overdue_writer_count`,
`legacy_blocked_writer_count`, `legacy_overdue_writer_count`, `blocked_nonwriter_count`, `overdue_nonwriter_count`,
cohort budget/remaining allowance, oldest blocked age,
deadline, next event and accountable driver. Missing fields or unavailable counts are UNKNOWN, never zero.
The driver quotes these live counts each cycle and before handback. The automated requirement is that status output
contains the count fields with explicit zero or UNKNOWN; it does not claim to test the driver's spoken quotation.
One new blocked lifecycle fills the ordinary slot until disposition. Separate legacy counting cannot hide debt.

At a new lifecycle's deadline the supervisor persists `blocked_deadline_exceeded` and sends an attributed escalation
through Fleet Comms to the operator and both designated advisors. Legacy deadline breaches persist per-item evidence
but send one cohort escalation with counts, owners and item references, not historical per-item message bursts.
Acknowledgement does not clear overdue custody; missing acknowledgement remains a visible blocker.
The requested decision is bounded recovery with demonstrated prerequisites, delta discard to actionable remote H,
or driver-attributed abandonment under OD-03. The driver cannot extend clocks, archive debt out of counts or rename states.
Expiry authorizes neither deletion nor publication of rejected work. Unsafe-to-dispose custody stays overdue and cannot
claim compliance/completion. Ordinary admission remains refused on a full slot or unknown/exceeded budget;
bounded migration/prerequisite exemptions remain available. I01-AC05/I04-AC07 test these rules without relaxing guards.

`blocked_nonwriter_count` counts unfinished read-only/review custody separately, including overdue records.
A non-zero or UNKNOWN count refuses ordinary new read-only/review dispatches in that lane. It does not by itself
consume the blocked-writer slot or refuse ordinary writers; the writer slot and legacy-budget rules still apply.
A read-only/review prerequisite needed to dispose a named blocked lifecycle may use the same bounded driver grant
and debt-only exemption described above. No unrestricted review exception or duplicate healthy review is allowed.
The board also exposes `overdue_nonwriter_count`; all count fields are explicit zero or UNKNOWN, never omitted.

A material-finding dispute sets phase `awaiting_operator_adjudication`, with finding IDs, rejection digest, current H,
operator decision awaited, driver owner and escalation receipt on the existing attention board. It blocks APPROVE,
PR creation and enqueue. Dispute attention persists even after a PUSHED tree release. Tree release ends only its
local-custody clock; the unresolved dispute keeps its original `blocked_since` and `blocked_deadline` and consumes
the one blocked-writer admission slot until attributed operator adjudication resolves it or verified abandonment ends it.
Ordinary undisputed review/CI waiting remains exempt from that slot. Entering a dispute starts the clock once;
restarts, successor heads and awaiting an operator response never pause or reset it. Deadline escalation does not
authorize retiering, approval, discard or extension. These admission/attention details remain part of proposed OD-02.

## Exact pushed proof and tree recreation

PUSHED requires all of the following at the final candidate head H:

1. The normal pre-push gate completed successfully for H. `validation_incomplete` and gate refusal are failures.
   A hook bypass, stale successful run, or remote branch presence alone is insufficient.
   At push time, freshness follows `.githooks/pre_push_gate.py:receipt_is_fresh`: the `{head}-{base}` receipt
   matches the bound `receipt_inputs(plan)` (since #11207 the key also records the affected-test selection
   that ran), outcome `green`, and age from zero through `RECEIPT_TTL_S`, currently 3600 seconds.
   The publication record copies that receipt's SHA-256 and key at successful push, with affected command/results evidence.
   Later expiry does not erase a historical gated publication. Removal validates that immutable publication record,
   not a new claim that an expired hook receipt is currently fresh. A new delta/head requires its own fresh gate and push.
2. A live `git ls-remote --exit-code origin "refs/heads/$BRANCH"` read returns H exactly.
   A cached tracking ref or ancestor relationship is insufficient for PUSHED.
3. The local `git rev-parse HEAD` remains H, and the actual checked-out branch equals the recorded branch.
   An authorized delta discard must first restore this exact checkpoint using the guarded transition below.
   Committed, tracked, untracked, and ignored task content is accounted for.
4. The worker has exited, every write/review-input claim is released, and process/open-file probes establish absence.
   Review runs against a separate remote snapshot, or completes its local-input claim before removal.
5. Before any removal, the supervisor appends a durable `writer-pushed-local.v1` observation to the canonical lifecycle
   ledger while the registered tree still exists. It uses `task_lifecycle.observe_local_git` at H to capture lifecycle/attempt,
   actual branch, worktree registration/path, creator/generation, complete commits and X-Agent trailers, changed paths,
   and local cleanliness/content-accounting results. It binds H, the immutable gated-publication digest and observation digest.
   This is preparation for PUSHED, not a premature disposition. Receipt write/read-back failure refuses removal.
   Each successor H' requires its own observation; the receipt at H cannot establish H' readiness.
6. The reaper revalidates local identity under the existing worktree lock and checks fresh remote evidence before deletion.
   A concurrently moved branch blocks removal. The receipt records the observed remote version and recheck result.
7. The reaper removes only the local tree through the shared guarded remover and verifies registration and directory absence.
   It checks again that the remote branch is H. Failure leaves an explicit repair obligation, never a false PUSHED receipt.

After removal, I-01 updates `task_lifecycle._latest_premerge_local`, `_local_readiness` and `evaluate` to accept
the durable local observation only when its lifecycle, branch and exact current reviewed head match, its gated publication
and successful removal receipts verify, and fresh remote observations still agree. A missing tree alone remains a blocker.
An old head, missing commit/trailer inventory, altered digest, incomplete removal or contradictory current facts refuses.
Pre-removal facts establish local implementation readiness only; current GitHub facts still decide PR identity, review, CI
and merge. The stale H observation cannot substitute for H' even if it is the latest receipt with `worktree_present: true`.
I-01 updates `task_closeout.GhGitHubAdapter.observe`, `cmd_reconcile` and mutation preconditions to consume that
same head-bound readiness path for reconcile, AC sync, enqueue checks and issue close. No mutation becomes authorized
by merely accepting local readiness. Lost callback recovery must durably capture/read back this observation before reaping.

There is no preserve-then-reap step, local backup branch, rescue ref, or archive copy in this writer path.
Durable task artifacts needed for continuation must be committed to the permitted branch or recorded in an already-authorized
canonical task store with stable identity. Non-publishable source work must not be pushed merely to satisfy cleanup.
Only proven disposable cache can be discarded without task-content abandonment authority.
Unknown ignored output, unrelated files, mounted corpus, or shared data blocks removal and stays with its owner.
The implementation must adapt the existing ignored-output guard for this writer path, not bypass it globally.

The PR-open prohibition concerns a settled end shape. An active, bounded writer fixing CI can hold the same canonical tree.
At every settled PR-open handback, that tree must be absent. Review/CI waiting consumes no paid writer session.
The local branch ref may remain for recreation while the remote branch exists. It must disappear on MERGED or ABANDONED.

The documented single-command recreation and continuation interface reuses the existing dispatch command:

```bash
"$PROJECT_PYTHON" scripts/delegate.py dispatch \
  --agent "$WRITER_AGENT" --task-id "$WRITER_TASK" \
  --branch "$BRANCH" --worktree "$WORKTREE" --mode danger \
  --prompt-file "$CONTINUATION_BRIEF"
```

`WRITER_TASK` and `WORKTREE` refer to the same lifecycle's original task and canonical dispatch path.
Across settled fix rounds, "same worktree" means the **same path recreated** from remote H after removal.
Within an active bounded round the existing tree remains in place. No second checkout or outcome is created.
The continuation brief is held in the canonical task store, not in the removed tree.
The implementation makes this invocation resume the existing lifecycle instead of refusing a terminal task ID,
superseding evidence, or creating another outcome. This behavior is proposed, not available today.
It fetches the exact branch, checks the receipt's remote head, recreates the tree and local ref if needed,
restores required sparse paths and supported runtime provisioning, and writes a new attempt under the same lifecycle.
It refuses another checkout of the branch, a path collision, moved remote head, unresolved claim, or ambiguous identity.
It never uses `--base origin/main` to replace the continuation branch.
A changed default branch does not silently rebase the writer. Deliberate synchronization follows existing exact-head rules.

Same-path recreation preserves exactly one original `worktree_reused: false` creator. Each new attempt is
`worktree_reused: true`. Under the existing lock and before worker spawn, I-02 calls the proposed I-03
`ignored_task_output.refresh_recreation_baseline` API with lifecycle/creator, current attempt, branch/H,
predecessor removal digest and new directory identity. It refreshes only after proving predecessor removal,
same lifecycle/branch/remote H, and newly created directory identity.
I-03 appends a recreation-generation receipt with original creator/run nonce, predecessor removal digest, current attempt
nonce, new `[st_dev, st_ino]`, and the newly captured `ignored-baseline.v1` inventory/digest. The original baseline stays
historical. The current cohort's effective baseline references this generation; it never adds a second creator.
`ignored_task_output.reused_worktree_creator` still requires the single original creator. `_classified_inventory` selects
the verified current generation rather than trusting an old inode or relabelling arbitrary ignored content as disposable.
An unexpected inode change on an existing tree, missing predecessor removal, ambiguous creator, stale generation or
unknown inventory refuses spawn/removal. A crash before baseline publication leaves held custody; bounded replay may
complete that same generation after revalidation, without inventing another creator or overwriting history.
I-01 owns the checkpoint reference, I-02 owns the caller, and I-03 owns capture/classification and shared claim integration.

## Review request authority and rejection history

The new reservation/rejection-chain publication and keeper preconditions in this section apply only to post-activation
lifecycles identified by the admission-index entry and matching lifecycle-ledger `activation_epoch` below.
Pre-activation PRs and agent-prefixed PRs with no dispatch retain existing review, publication and enqueue gates.

Two options require designated approval before implementation. The OD-04 approval record must name Option A
writer-requested review or Option B driver-requested review on the writer's behalf; an approval naming neither is invalid.
Option A delegates only the mechanical review request to the writer under this contract.
Option B keeps the lane driver as request actor on the writer's behalf and uses the same reservation and rejection checks.
Option B is recommended because it keeps review dispatch authority with the driver and grants no dispatch capability to the writer.
The issue's proposed writer-request flow is Option A, not implicit approval of that transfer.
Under either option, review judgment and finding disposition remain undelegated driver responsibilities.

For every writer review the supervisor chooses one durable state file at the primary canonical task-store root,
`batch_state/writer-review/<lifecycle_id>/<head>/closeout.json`, using the lifecycle digest component as a safe path segment.
It records the canonical path in the ledger and passes it explicitly as global `closeout_cli --state-file` before
`resolve-reviewer` and all target/finding/proof operations. This is the proposed writer default, not today's CLI behavior,
which requires `--state-file`. A writer-worktree `.agent/` or relative cwd fallback is refused for this flow.
Resolver/verdict/behavior receipts and continuation briefs must survive PUSHED removal; the ledger binds immutable
receipt digests, not just mutable state-file contents. Shared-store writes use existing locks and atomic replacement.

The actor runs `closeout_cli resolve-reviewer` with the exact author identity, profile, risk, and owned paths.
It may execute **only the returned reviewer invocation**, with no alternate model, harness, effort, or weakened constraints.
The immutable `writer-review-request.v1` brief template freezes the outcome/AC hash, target H,
owned paths and diff, author provenance, held-out verification, blocker/residual policy, exact verdict contract,
and prohibition on merge/enqueue. It carries the complete lifecycle rejection-chain digest and all unresolved prior
material finding IDs, original head/verdict/receipt, remediation claimed at H and any driver disposition receipts.
Only typed target values may be substituted. The expanded brief and resolver receipt are hashed.
Unknown or unavailable resolution records a blocker, not a writer-chosen reviewer or another provider call.

Before dispatch, the existing lifecycle ledger atomically reserves one review for repository, lifecycle, and H.
There is at most **one review request per head** by default, including across restart, tasks, and harnesses.
Concurrent duplicate requests, a different reviewer at the same H, and replacement after timeout/refusal are refused.
The actor continues the same request/nonce when a wait client expires. A new head opens a head-specific reservation
within the same lifecycle rejection chain. Cosmetic changes, new tasks, replacement PRs and branch changes cannot clear it.
The successor reviewer receives unresolved prior findings and assesses their remediation at the new exact head.
Exceptional retry of a failed request requires a driver-attributed decision bound to the original request and H.
A head with REQUEST_CHANGES, CHANGES_REQUESTED, or BLOCKED additionally requires a driver-recorded re-review decision.
The decision names the findings, why another review of unchanged content is justified, resolver receipt,
one allowed successor request, and the prior receipt digest. The writer has no policy authority to supply or edit that decision; same-user forgery remains the operator-only OD-12 residual.

The writer may fix H to H' in-session and attach claimed remediation evidence to the successor request.
It may not adjudicate, skip, re-tier or clear a prior material finding. The reviewer supplies an exact-head assessment;
only the lane driver records its attributed disposition after inspecting H' and that assessment.
If any prior material finding needs disposition, the bounded writer round hands back its gated H' as D-04 PUSHED
with `next_action: driver_finding_disposition`, unresolved finding IDs and a durable request/assessment pointer.
The writer does not wait indefinitely for driver intervention or attempt PR creation within that round.
The driver may mechanically request the reserved successor review under the approved option, record dispositions
and then finalize the local APPROVE receipt. A reviewer's candidate APPROVE awaiting those dispositions is stored
as an assessment with `approval_effective: false`, not published as APPROVE or consumed as permission.
Negative verdicts are recorded immediately. Once dispositions and the exact-head verdict validate, a subsequent
bounded continuation or the driver's mechanical publisher may open the PR; neither acquires review-judgment authority.

All negative history is lifecycle-scoped across heads and remains effective until a qualified successor has a toolful,
exact-head verdict and the driver records a disposition receipt for every prior material finding. Each receipt binds
finding ID, original rejection digest, current H, resolution evidence and driver identity/sequence under OD-03.
Unresolved material findings block; a dispute requires operator adjudication, never writer retiering or silent omission.
PR creation, APPROVE publication and the keeper require reservation, any exception decision, complete lifecycle rejection chain,
carry-forward brief digest, all prior material-finding dispositions and current verdict. A later timestamp is insufficient.
An unreserved approval, missing chain/disposition, edited brief or unresolved rejection blocks PR creation, APPROVE publication and enqueue
even if APPROVE at a successor H is the latest comment. REJECT at H followed by trivial H' and APPROVE at H'
without a driver disposition must be refused by APPROVE publication and the keeper.
Negative verdicts and findings are always recorded in the lifecycle chain; this approval gate cannot suppress rejection evidence.
I01-AC04 and I01-AC06 include negative tests at admission, verdict publication, and keeper consumption.

### Pre-PR verdict recording and publisher gate

I-01 extends `record_cf_verdict.record` with an explicit branch/head-scoped pre-PR mode, exposed as `--pre-pr`
and mutually exclusive with `--pr`. Inputs bind repository,
lifecycle, branch, exact H, frozen review base/commit set, reservation and completed review task. It uses
`collect_branch_review_facts` and the same model/family qualification, author exclusion, `SELF_REVIEW_DETECTED`,
reply/artifact validation and rejection checks as PR mode. It verifies live remote H, the base ref name and complete commit set;
it does not call `_pr` or require a PR number to derive author facts. UNKNOWN or MALFORMED writer provenance refuses approval.
The recorder durably appends `REQUEST_CHANGES`, `CHANGES_REQUESTED` or `BLOCKED` and findings without any PR.
APPROVE becomes a local effective receipt only after all required driver dispositions and chain bindings validate.
A qualified candidate APPROVE with pending dispositions is durably recorded as an ineffective assessment; replay after
disposition revalidates the same review task/H and appends the effective receipt, without a new review reservation.
The receipt binds repository/lifecycle/branch/H, base ref name and observed base SHA, frozen commit set, reservation nonce, review task/model/family/harness, verdict,
brief/resolver/artifact digests, rejection-chain digest and disposition digests. Its PR binding is initially null.
The ledger and immutable receipt survive removal. Existing PR mode continues to revalidate exact PR author facts.

`scripts/publish/github.py:publish` enforces the classified post-activation writer precondition for every `pr-create`,
including direct CLI, typed requests, shim routing, supervisor finalization and `--draft`. Before any GitHub write
it requires and read-backs the durable effective local APPROVE receipt, verifies its exact live remote H and
all reservation/chain/disposition bindings, and refuses UNKNOWN, missing, stale, conflicting or ineffective evidence.
Caller-supplied approval text is insufficient. Exempt pre-activation/non-writer PRs retain existing gates.
On creation it records the PR identity, rechecks its branch/H and base ref name against the frozen review facts,
and requires complete PR/local commit-set equality with the reviewed set, using `pr_review_facts`' enumeration and exclusions.
The observed base SHA is evidence, not an equality precondition. A moved `main` SHA alone cannot invalidate unchanged-H approval
when the base ref name and complete reviewed commit set remain equal. A changed ref name, commit set or H refuses projection;
an unchanged head cannot obtain another review merely because `main` moved.
After those checks it invokes the recorder's idempotent PR projection to post and verify the existing `<!-- cf-verdict v1 -->` marker
and normal review status. It links that read-back to the local receipt without changing its original reviewed target.
A timeout or failed read-back stores `publication_unconfirmed`, PR identity if known and next-action owner.
Replay looks up the same branch/H creation operation and reconciles the existing PR/comment; it cannot duplicate
the PR, fabricate publication, enqueue, or request another review. A moved head refuses approval projection.
The keeper still requires the exact-head GitHub verdict and CI plus the local governed-writer chain.
The pre-PR local receipt breaks the creation/recording dependency without weakening the before-PR review gate.

### Writer-PR classifier and keeper scope

I-01 adds `classify_writer_pr` in `scripts/orchestration/task_lifecycle.py`, consumed by the verdict recorder and keeper.
Inputs are repository, branch and exact H, PR number when available, complete hot/archive dispatch admission index/lifecycle bindings,
the activation-epoch record, registered dispatch-agent prefixes and complete branch/PR author-task/`X-Agent` provenance.
Admission records every post-activation writer branch in that ledger index, including explicit `--branch` overrides and
legacy switches, before publication. Each entry binds admission time, lifecycle identity and the exact activation epoch
also recorded in the lifecycle ledger. The index retains historical aliases after tree removal, task archival and replacement PR creation.
Default dispatch branches have `<agent>/<normalized-task>` shape from `scripts/delegate.py:_derive_worktree_branch`.
A matching prefix, indexed writer branch or writer dispatch provenance triggers classification, not the new precondition by itself.

Registered dispatch provenance means a validated hot/archive dispatch task record attributed to a branch commit,
or an actual/historical branch alias or attributed task identity matching a retained admission-index entry.
The classifier collects the complete branch facts with `collect_branch_review_facts` before PR creation and
`pr_review_facts` once a PR exists. Both use `scripts/review/record_cf_verdict.py:_attribute_commit`.
Only `source: task-record` or `task-record-archived` proves record-backed attribution, after repository and harness checks.
It joins the normalized `task_id` and `record_task_id` to the complete hot/archive/index lookup and validates the
dispatch identity, mode and any lifecycle/epoch binding. An indexed identity/alias remains registered if its task record is MISSING.

An ordinary mandatory `X-Agent` trailer is author attribution, not proof of registered dispatch.
`_attribute_commit` permits `trailer-model`, `single-family-harness` and `unresolved-author` when no task record exists.
Its `task_id` and `BranchReviewFacts.author_task_ids` can contain an unregistered slug.
Neither that slug, a `TASK_ID` pattern match, a model/family token nor a branch prefix proves registration.
For each commit the classifier first validates attribution, then looks up any attributed identities and branch aliases.
If complete consistent lookup finds no registered dispatch, ordinary model-attributed or no-dispatch trailers remain
eligible for EXEMPT no-dispatch. Manual/orchestrator publication retains today's author qualification and review gates.
This distinction grants no exemption on failed attribution, unreadable/incomplete lookup, or invalid/conflicting records.

Before verified activation, the new consumers retain existing gates with the new precondition disabled;
not-yet-created epoch/index records cannot block I-02 through I-04 delivery. They read I-01's proposed durable admission-index activation control before classification. I-01 initializes it
as DISABLED before installing consumers; the approved cutover atomically changes it to ACTIVATED with the epoch.
ACTIVATED is irreversible in this contract; restart or missing epoch cannot reset it. UNKNOWN control refuses activation-dependent mutations. Once activated, missing
global epoch/index stores are UNKNOWN and refuse; a missing store cannot imply disabled activation or undo it.
Individual entries after complete lookup use MISSING as defined below.

The activation-epoch record freezes repository, epoch ID/time, initial/delta inventory digests, pre-activation
open PR numbers and admitted non-final task/lifecycle IDs, including reaped PUSHED and legacy needs_finalize records.
I-02 through I-04 admissions before activation enter that frozen set; their later fix commits do not remove exemption.
A frozen PR/task identity remains pre-activation across head changes. The index retains historical branch aliases.
No record can acquire a post-activation epoch by migration or by changing its branch, task or PR.

Classification uses fresh complete hot/archive lookups, not a hot-directory-only scan. ENOENT for an individual
record is MISSING only after complete lookup proves no matching historical record. Permission/I/O failure, malformed
JSON/schema, unreadable directories or incomplete enumeration is UNKNOWN, not absence. Required epoch/index reads
must succeed before exemptions can be asserted. Existing malformed or conflicting lifecycle evidence is refused,
even for an otherwise exempt PR; an absent optional lifecycle binding alone does not invalidate an exemption.
After activation, these preliminary refusals take precedence over the classification table.
Evaluate the remaining rows from top to bottom and use the first established classification.

| Evidence after complete lookup | Classification and effect |
| --- | --- |
| Epoch, index, ledger or task lookup unreadable/incomplete or parse failure | UNKNOWN, refuse new writer publication/verdict approval and enqueue; record the source failure |
| Conflicting identity/epoch/index/ledger, or a readable invalid binding | MALFORMED, refuse; absence is not an invalid optional binding |
| PR number or attributed task/lifecycle identity is in the frozen pre-activation set | EXEMPT, retain existing exact-head review/publication/CI gates even after a later fix commit |
| Readable uniquely attributed task record proves `mode: read-only` and no conflicting writer binding | EXEMPT, retain existing gates |
| Post-activation admission has one matching task/index/ledger epoch for actual branch and H | GOVERNED, require reservation, effective local verdict, rejection chain and driver dispositions |
| Proven registered dispatch provenance outside the frozen set, not proven read-only, has a MISSING task record, index entry or writer lifecycle binding | MALFORMED, refuse; renamed/explicit branches and omitted trailers cannot erase retained index provenance |
| Readable writer record or indexed writer alias outside the frozen set lacks a consistent post-activation binding | MALFORMED, refuse; no timestamp heuristic grants exemption |
| Valid ordinary author attribution and complete consistent hot/archive/index lookup finds no registered dispatch | EXEMPT no-dispatch, including model-attributed or mandatory no-dispatch X-Agent trailers and an agent-prefixed branch; retain existing gates |
| No preceding row can be established with complete consistent evidence | UNKNOWN, refuse |

`classify_writer_pr` is consumed by the publisher before PR creation using branch/H, by the verdict recorder,
and by the keeper using PR identity/H. A prefix triggers complete lookup, never exemption or governance by itself.
Migration cannot retroactively change activation scope. This proposed classifier is not a current keeper capability.
I01-AC06 covers all rows, frozen I-02 through I-04/reaped tasks after successor commits, missing-versus-unreadable
records, renamed/explicit branches and unchanged no-dispatch/read-only fixtures. Include explicit model trailers,
manual/orchestrator slugs with no dispatch record, indexed branches with a MISSING record, malformed trailers and
conflicting/unreadable records. OD-09 binds this exact scope.

## Abandonment and deletion authority

The authoritative `writer-abandon.v1` decision is a driver-attributed, append-only lifecycle-ledger record.
The supervisor checks recorded lane assignment/session binding, lifecycle/run nonce, sequence, exact scope and content
digests against the recorded supervisor/Fleet event. Missing, expired, wrong-lane, writer-labelled or inconsistent evidence
is refused. Caller assertions or local JSON without a matching event are insufficient. The writer may propose a reason
and inventory; the driver has policy authority to record the decision. These attribution checks also apply to review
retries and material-finding dispositions.

**Trust boundary, pending operator-only OD-12 acceptance:** this design does not authenticate a submitting human or process against
another process running as the same OS user. `scripts/fleet_comms/message_plane.py:MessagePlane.open_ask` accepts caller-supplied
`sender`; shared lifecycle-ledger and Fleet-store access is not isolated from writer processes.
This proposal adds no writer sandbox denial, driver-held secret or cryptographic identity check.
A same-user writer can forge a consistent authoritative event, assignment and ledger receipt, not just local JSON.
Trailer/provenance omission is a separate evasion boundary beside same-user event/receipt forgery.
Today `_attribute_commit` refuses missing or malformed `X-Agent` with `author model unknown: missing explicit X-Agent model trailer`.
Its Git-proven clean-base-merge and admitted unknown-history exceptions retain their existing qualification rules.
The proposed classifier also refuses missing writer bindings when a validated dispatch record or retained index proves provenance.
A dispatched writer can use a valid non-task trailer form and publish from an unindexed ref without tampering with any record.
Existing code accepts `<agent>/<catalog-model>` without a task ID and exempts `<agent>/inline` in the trailer linter.
Publication to an unindexed remote ref need not change the local branch, so the finalizer's branch-switch blocker does not catch it.
With no attributed task identity or indexed branch alias, the classifier can return EXEMPT no-dispatch.
It does not compare branch/PR commits or H against ledger-recorded checkpoints, the gated SHA or the pre-removal commit inventory.
A mandatory trailer alone cannot distinguish that evasion from legitimate manual/orchestrator publication.
The lifecycle's unpublished-H blocked custody provides only indirect detection when the recorded branch lacks exact gated publication of H.
Cross-copy digests, retained index entries and the operator-visible log need not show any inconsistency because nothing was tampered with.
This residual includes accidental non-compliant publication. Proven registered dispatch provenance or conflicting evidence still refuses exemption.
Same-user forgery and this remaining trailer/provenance-omission evasion are explicit out-of-scope residuals owned by Harness, requiring operator-only risk acceptance under OD-12
before activation. Without acceptance this trust-boundary decision blocks activation.

Compensating controls are public-copy digest match, stable issue entry and an operator-visible decision log projected
through the existing Fleet attention/status path. The log includes lifecycle/issue, driver role, sequence, scope/content
digests and UTC time; deletion requires the entry and matching read-back first. These controls detect inconsistent/missing
evidence and support operator audit. They cannot prevent a same-user attacker forging every copy or editing accessible logs.
Public digests prove agreement of bytes, not who authorized them. Abandon authority therefore proves recorded policy
attribution, content binding and auditable cross-copy consistency, not unforgeable driver identity or same-user isolation.
Receipts state `authority_assurance: attributed_same_user`. I03-AC04 tests inconsistent forged authoritative events and
a fully consistent same-user forgery to make the limitation explicit.

The lane driver copies the privacy-safe decision payload and its canonical digest to the issue body.
The reaper reads the local decision and public copy back before deletion. Their public payload digests must match.
The public copy is a projection, never authority. Editing it, copying another lifecycle's decision, or inventing a digest fails closed.
Private session identifiers and attribution evidence remain local.
The issue uses one stable lifecycle entry and one final closing comment when closure is justified.
The entry has the following privacy-safe fields:

```yaml
schema: writer-abandon.v1
lifecycle_id: <stable-id>
issue: <number>
driver: <public-lane-role>
decision_sha256: <driver-attributed-local-decision-digest>
public_payload_sha256: <digest-of-public-fields-excluding-digest-fields>
decision_sequence: <monotone-lifecycle-sequence>
discard_mode: <whole_lifecycle|unpublished_delta>
recorded_at: <UTC-time>
reason_code: <gate_refused|budget_exhausted|worker_failed|lane_cancelled|other>
reason: <specific-public-reason>
branch: <task-branch>
heads: [<exact-commit-id>]
dirty_content_sha256: <manifest-digest-or-null>
remote_copy: <branch-and-head-or-none>
content_equivalence_receipt_sha256: <digest-or-null>
discard_unique_work: <true-or-false>
authorized_scope: <task-owned-content-and-refs>
retained_remote_head: <exact-H-for-delta-or-null>
discarded_commits: [<exact-commit-ids-after-H-or-empty>]
residual_issue: <number-or-none>
residual_owner: <lane-or-none>
```

Private receipts retain the detailed manifest and attribution. Public records contain only their digests.
For dirty-only work, `heads` may contain the unchanged base and `dirty_content_sha256` must be non-null.
An abandon decision identifies every task branch, including a branch switched during a legacy continuation.
An OPEN PR must be explicitly closed or transferred to another named outcome before deleting its branch.
Abandonment does not close unmet acceptance criteria. The issue remains open with a residual owner or transfers the residual.

Unpushed commits may be deleted only after the attributed decision and matching issue copy exist,
and at least one exact condition is proved:

- Each unique local commit is reachable from an identified live remote branch. Record the remote ref/head and containment proof.
- A recorded content-equivalence receipt binds the local content to a pushed branch.
  The verifier checks the full intended path set, file modes, blobs, deletions, and final tree identity.
  A commit message, status string, patch-id alone, or matching filenames is insufficient.
- The driver-attributed lane driver explicitly records a specific abandon reason and `discard_unique_work: true`
  for the exact local heads and dirty-content digest. This is the only path that can discard unique task source content.

None of these conditions permits deleting unrelated work, bulk payloads, secrets, or another lane's custody.
A remote copy without an abandonment entry is not authority to silently abandon an outcome.
Dirty task files require the same explicit accounting. Unknown content or identity blocks deletion.
The common reaper enforces these conditions. No ad hoc forced removal or task-history rewriting is allowed.

### Delta discard to PUSHED

If a gated, actionable remote H exists and later local work cannot pass publication, the driver may authorize
`discard_mode: unpublished_delta` under the same `writer-abandon.v1` attribution contract.
The scope is exactly the enumerated commits after H and the dirty-content manifest digest, never H,
its remote branch, an existing PR, its review evidence, or unrelated content. H must be an ancestor of the observed local head L.
Non-descendant heads require a separate whole-lifecycle decision or verified reconciliation, not an inferred delta.
The receipt binds H, L, the full ordered commit set `H..L`, tracked/untracked/ignored task-content manifest,
local ref's expected value, remote observation/version, and `discard_unique_work: true` when needed.
Unknown content or a changed local/remote identity refuses the transition.

After worker and claimant absence, the common guarded path revalidates the driver decision and content under
the existing lock, discards only the authorized unpublished delta, and restores the local checkpoint/ref to H.
It then applies exact PUSHED removal and post-removal remote checks. The PR and remote H remain actionable.
The record settles **PUSHED at H**, with both delta-discard and removal receipts, never whole-lifecycle ABANDONED.
An interrupted discard keeps active custody until idempotent replay proves H and removal. Partial actions are not success.
No source delta is silently cached, backed up, or pushed past a failed gate. I03-AC05 verifies this transition and its refusals.

## Resumable budget and failure handling

The smallest mechanism is another bounded invocation of the same logical writer in the same canonical tree and branch.
The lifecycle supervisor stores an explicit checkpoint before each boundary.
It uses the existing dispatch/worktree lock, task-record store, and runtime adapter; it adds no second lease or control plane.
The logical writer identity survives a process restart. Each attempt has a fresh nonce and observed process identity.

The checkpoint binds outcome/AC hash, owned paths, branch, head, dirty-content digest if present, current phase,
last gate/review/CI evidence, writer harness/session identity, and remaining budget.
The next invocation consumes that checkpoint and verifies its bindings before acting.
Native session resume is allowed only for that exact writer session, tree, branch, and lifecycle.
It must not select the newest transcript, resume a reviewer session, or carry context from another task.
For a stateless adapter, a fresh process consumes the same explicit checkpoint and remains the same logical writer.
Native warm resume from delegate requires a narrowly scoped change to today's bridge-only policy, marked for designated approval.

Each approved task card freezes positive per-attempt hard, silence, and startup timeouts,
a finite total attempt limit, cumulative execution limit, and a finalization allowance.
For a card lacking limits, the proposed baseline uses `scripts/delegate.py` defaults:
`DEFAULT_HARD_TIMEOUT_S = 7200`, `DEFAULT_SILENCE_TIMEOUT_S = 3600`, and
`DEFAULT_INITIAL_RESPONSE_TIMEOUT_S = 600`. Admission snapshots those values rather than reading mutable defaults later.
The proposed default total is **three attempts**, at most **21600 execution seconds** across them,
with the final **600 seconds of each attempt** reserved for checkpoint/publication within its 7200-second cap.
Time spent gating, repairing, or finalizing counts against both caps. It does not grant a fourth attempt.
These new total/allowance values need designated approval. A runtime unable to honor the snapshot refuses admission.
An approved card may freeze stricter limits or a separately approved bounded override before execution.
Where supported, it also records the provider spend cap and provider-native turn/token limits.
The task card must not equate a token context window, provider quota, or wait-client expiry with a session execution budget.
No unspecified or unlimited continuation is admitted. The total budget only decreases across attempts.
After two review/fix rounds, the driver records a stopping decision. Unresolved material findings remain blockers.
Further rounds require an explicit bounded driver decision within the approved total budget, never a new tree.

A soft checkpoint precedes the hard kill so the writer can commit and run the gate.
A hard kill can still interrupt a gate. The supervisor records `gate_incomplete`, and a later attempt re-runs that gate on H.
The gate is never skipped, shortened, or treated as passed because the budget is low.
At the end of a bounded round, an exact gated head can hand back as PUSHED with unresolved review or CI evidence and an owner.
Unpublished work continues in the same tree within the remaining budget, or the driver records ABANDONED.
The supervisor never records a terminal state while local-only work lacks such a decision.

On crash, timeout, cancellation, provider refusal, or unknown completion:

1. Persist `status: custody_held` and separate typed `attempt_result` before optional telemetry. Keep the lifecycle active
   with the lane driver as owner; never expose a released/final top-level attempt status while custody is held.
2. Establish worker/process absence and current content identity before another invocation or any removal.
3. Resume only the bound lifecycle and tree. Do not spawn another healthy writer or duplicate a review.
4. If publication succeeds, settle as PUSHED. If the driver explicitly abandons, settle as ABANDONED after cleanup.
5. If identity, custody, provider health, gate, or deletion authority remains unknown, record the blocker, owner,
   and concrete event needed for recovery under the 24-hour blocked contract. Do not relabel it as success or terminal `needs_finalize`.

Policy forbids a crashed writer from authorizing deletion of its own tree; the OD-12 same-user limitation still applies. Harness I-01 changes `scripts/delegate.py`'s supervisor exit path
to schedule and await the Infra I-03 common-reaper disposition path after process absence is proved.
The path accepts verified PUSHED/MERGED cohort receipts instead of requiring `done` with exit code zero
or refusing every reused tree. Attempt return code alone never licenses removal.
Infra I-03 changes scheduled cleanup to retry this same receipt-backed writer-tree rule, including OPEN PRs.
It preserves the OPEN-PR prohibition on remote-branch deletion and all non-writer retention guards.
Crash between publication and cleanup is recoverable from the shared receipt. I01-AC07 and I03-AC06 own this proof.
A reaper failure preserves the existing tree in place only as an active repair obligation.
It does not create a backup, terminal handback, or unowned retained outcome.
Issue #10537 supplies crash-rescue identity when that separate path is required. Its failure grants no alternate deletion authority.

## Custody release, lifecycle finality and branch protection

Attempt settlement, local worktree custody release and lifecycle finality are separate predicates.
New writer records remain `status: custody_held` until verified removal; a PUSHED handback projects
`status: writer_pushed`, `custody_released: true`, `lifecycle_final: false`. Continuation returns to
`custody_held` before recreating/spawning. Only complete MERGED/ABANDONED cleanup sets `lifecycle_final: true`
and a compatible final top-level status. Prior attempt results stay historical.
The compatible consumers distinguish custody-release eligibility from archive/final eligibility; a generic
`RELEASED_TASK_STATUSES` membership must never prove writer finality or branch discard authority.
`writer_pushed` may release a proven absent tree claim, but is not an archivable/final lifecycle status.

I-01 changes `stale_task_records.keep_hot_reason` and both selection/apply phases of `archive_terminal` to keep
every non-final writer record and its receipt sidecars hot, even when the tree is absent and age is zero.
I-03 changes `batch_state_retention._eligible` to exclude those same records/sidecars and binds archival eligibility
to verified MERGED/ABANDONED cleanup. Missing/unreadable/invalid finality evidence keeps records hot and refuses pruning.
The durable admission index and history are never pruned while referenced by an active lifecycle or frozen epoch.

I-03 changes `branch_sweep._active_tasks` to protect every non-final writer's current and historical task branch refs
from the index/ledger, regardless of top-level attempt status, absent tree, age or lack of an OPEN PR.
`scheduled_worktree_cleanup.cleanup_stale_origin_branches`,
`cleanup_gone_local_branches` and `cleanup_untracked_local_branches` apply the same protection before selection
and again immediately before deleting any local/remote ref. `_stale_ref_delete_reason` cannot override it with
main ancestry, a durable closed-PR head or another remote copy. UNKNOWN protection evidence refuses deletion.
The existing OPEN-PR protection remains. Scoped common-reaper MERGED cleanup requires verified landing;
scoped ABANDONED cleanup requires the exact attributed decision and public read-back. These authorized cleanup
transitions may remove their bound refs before finality is set; generic sweepers cannot infer that authority.
A whole-lifecycle abandon decision allows only its scoped cleanup
while finality is pending, never a generic sweeper bypass. Interrupted cleanup stays hot until all absences verify.
Thus D-02/D-04 before PR creation and D-11 after external closure retain branch refs until MERGED/ABANDONED.

## Read-only and review completion replacement

All new task records, writer or non-writer, persist top-level `status: custody_held` while local custody is unresolved.
`custody_held` is a distinct status outside every released/final/archivable status set; never add it to those sets.
Failure, timeout, crash, cancellation and provider refusal live only in `attempt_result`, never as top-level `failed`,
`timeout`, `crashed`, `cancelled` or another released status while custody is held. An unknown old reader therefore
retains the claim rather than recognizing a released attempt result. Upgraded release/reaper paths additionally require
validated lifecycle custody-release proof; process status or a missing ledger cannot license writer-tree release.
New read-only/review attempts replace `needs_finalize` with `status: custody_held`, typed `attempt_result` and reason
`completion_unconfirmed` for background jobs, unknown probes, missing report/verdict, finalize exceptions or interrupted completion.
The record carries `report_confirmed: false`, `custody_released: false`, an owner and next action.
Only verified custody disposition permits a compatible released top-level status, including `writer_pushed` above.
Custody release alone never permits writer archival or branch deletion. Historical attempt statuses stay in history.
Only a complete durable report or qualified review verdict plus absence proof can produce `done` and release custody.
A negative verdict can be a successfully delivered review, but never code approval.
A failed request keeps its review reservation; it does not authorize a new same-head review.
The supervisor applies the same blocked deadline/count to unfinished local custody, with separate
`blocked_nonwriter_count` and `overdue_nonwriter_count` on the board and the bounded-admission rule above.
It never maps these tasks to PUSHED or ABANDONED just to clear the board.
Clean read-only removal still uses the common reaper and verified claim/process absence.
Task-specific Atlas result evidence uses `completion_unconfirmed` with its own owner and manifest,
without claiming writer publication or releasing unfinished jobs. I01-AC08 tests these consumers.

## Reused trees and post-merge cleanup

A continuation records `worktree_reused: true` without changing the original creator's identity.
Creation ownership and current write authority are distinct. Cleanup verifies the complete current cohort.
The physical path or branch prefix does not establish ownership.
The finalizer reads the actual branch and head at exit. An unauthorized branch switch is a typed blocker.
For existing authorized legacy switches, migration binds both old and actual branch names and their exact heads.

The reaper must accept a settled cohort with MERGED or PUSHED evidence without requiring an obsolete `done` successor
or retention-release/preservation receipt. It must reject a live claimant, unknown process, dirty unique content,
remote mismatch, or ambiguous creator. Terminal process status alone does not release writer content custody.
Under the existing worktree lock, it re-reads cohort identities and local head before removal.
Network evidence is fetched outside the lock and identity/version is revalidated before applying it.

Post-merge, `merge_closeout` must handle both an existing reused tree and a tree already removed under PUSHED.
It proves the PR is MERGED, binds the reviewed head to the landed content, and verifies local/remote branch cleanup.
Squash merges require explicit landed-content proof; raw ancestry alone may be insufficient.
It returns failure if any matching tree, branch ref, or required receipt remains unresolved.
The merge-queue keeper's existing enqueue/landing authority remains separate from cleanup execution.
The accountable lane arranges the common-reaper closeout after observing MERGED. No claim is made that today's keeper calls it directly.

## Migration from needs_finalize

Migration is a separately approved, scoped Infra execution task. This design issue performs none of it.
The implementation first updates every writer status producer and consumer, including completion gates,
interrupt checkpoints, wait/status APIs, claim release, active views, settlement, archiving, and reaping.
Old readers must refuse unknown lifecycle schema/status rather than release claims or report `done`.
Active writers cannot start using the new schema until all load-bearing consumers can validate its receipts.
Historical records retain their original status and provenance in immutable history; no evidence is erased.

The migration inventories hot and archived records, registered worktrees, actual branches/heads,
creator/reuse cohorts, dirty/untracked/ignored content, remote branches, PRs, claims, and process activity.
`find_needs_finalize_worktrees` alone is insufficient because it derives one owner from each directory name.
Duplicate records resolve by complete lifecycle/run identity, never by newest timestamp alone.

For each existing tree or local-only record:

1. Assign the existing owning lane and reconcile the actual outcome and branch. Preserve original creator/run identity.
2. If MERGED evidence is complete, use common-reaper closeout and write MERGED after absence verification.
3. Otherwise resume the same logical writer/tree to publish through the gate, then remove only the tree and write PUSHED.
   If a good remote H already exists, an attributed delta discard can settle PUSHED without another paid invocation.
4. If publication cannot meet the task contract, require the driver's attributed decision and matching issue copy,
   remove only its authorized content/refs, and write ABANDONED.
5. If the record/tree/remote is missing or unreadable, record an active migration blocker with owner and next condition.
   Missing tree is not proof of publication or abandonment. Existing archives are inspected, never copied into new backups.

The migration report states inventoried denominator, disposition counts, unresolved count and owners,
and receipt digests. Zero unresolved items is the stopping condition for migration completion.
Existing `keep_worktree` or retention intent is not silently cleared. It requires a scoped custody decision.
New writer tasks cannot request `keep_worktree` retention. Necessary artifacts must have identifiable durable custody.
A migration grant names the task cohort and deletion scope. It cannot authorize a repository-wide sweep,
other lanes' active trees, bulk data deletion, retention eviction, or a crash-rescue identity workaround.

Before mutation, Infra creates or uses one registered **cohort tracking issue per owning lane** for legacy
records with no original issue. It records per-lifecycle membership and stable identity, not one anonymous abandon reason.
Each local decision and public copy bind that tracking issue and the specific lifecycle/content digest.
An issue-less record cannot be discarded before this linkage. Missing original ownership stays blocked.

"Same writer" means the same logical lifecycle, not a requirement to invoke a retired model.
If its original route is retired, unavailable, or unhealthy, the owning driver resolves an eligible replacement
from the live catalog and approved substitution table, records model/family/harness/reason and new attempt identity,
and checks risk floor, outside-family review independence, privacy, and current capacity before resuming.
No silent substitution, retired route, borrowed transcript, or identity rewrite is admitted.
If no qualified route exists, the bounded blocked/escalation contract applies.

A read-only inventory precedes any paid execution. The first authorized live canary is at most **three legacy lifecycles**:
one already merged, one with publishable local work, and one needing an explicit discard decision.
The canary allows at most **six paid writer invocations** and **43200 aggregate execution seconds**, within each
lifecycle's approved caps. Any unavailable shape must be reported, not replaced with an easier duplicate.
The independent evaluator checks semantic outcome against the frozen AC/path inventory, remote content,
attributed decisions, no unrelated deletion, and actual tree/ref absence, not just receipt syntax or exit status.
One incorrect disposition, lost unique content, missing authority, or exceeded budget stops the wave.
Changed migration logic, runtime, prompt, parser, or route invalidates affected canary proof.

Bulk resumption has no blanket authorization for the reported roughly hundred legacy writers.
Its separate approved card freezes the freshly inventoried cohort N, waves, route-specific capacity,
maximum invocations and aggregate execution seconds, provider spend caps where supported, and canary receipts.
The aggregate allowance cannot exceed the sum of the remaining per-lifecycle caps and never resets after a restart.
No bulk paid run starts with unknown health, usage, disk headroom, or an unfrozen aggregate allowance.
Already-proven MERGED/PUSHED or delta-discard cases use deterministic local disposition before paid recovery.

Disk pressure before I-01 through I-03 land is an **open residual owned by Infra**, coordinated with Harness.
This document provides no immediate space relief. Infra records fresh disk/headroom evidence, refuses new work
that cannot fit, and escalates required relief under existing authority. It cannot use this proposal to delete early.
Migration closeout requires all inventoried lifecycles disposed and this residual resolved or explicitly accepted by the operator.

## Implementation issue packets

These are issue drafts, not created issues or claimed DoR PASS results.
Each implementation issue must link #10559 and its registered owning stream before dispatch.
Harness work belongs to #7919. Infra work belongs to #10548 and the applicable registered Infra parent.
The driver resolves exact current stream membership and cross-family reviewer through the live catalog.
Existing #10548 is reused for its outcome rather than duplicated.
Every packet requires designated approval of this normative digest, a hashed stable AC ledger,
a qualified outside-family plan/PR review path, and live dispatch preflight.
Independent tests named below are future test additions unless an existing path is explicitly identified.
`PROJECT_PYTHON` is the shared project interpreter. No full-suite local collection is required.

### Packet ownership and delivery order

The manifests freeze owned paths, including new files and tests. Coverage is exhaustive for the `needs_finalize`
reference inventory at the source revision, verified by the command in the round-3 evidence appendix.
That bounded command proves literal-reference coverage, not every semantic importer or future status consumer.
No two packets own a path. A packet may run another packet's tests without editing them.
No wildcard, search result, or "required adapter" silently enlarges ownership.
An unlisted required change stops dispatch until the driver revises the manifest and obtains approval of the new digest.
Read-only importer analysis identifies additional explicit test commands in each card; it does not grant edit ownership.
Harness owns the delegate supervisor. Infra owns every common-reaper and scheduled-cleanup mutation.
The interface review happens first. Compatible consumers and I-04 migration code/instructions land before activation.
New producers and debt-based admission refusal stay disabled until I-01 through I-04 code lands and end-to-end
exit-path/status-release proof passes. I-04 development does not depend on activation or prior live migration.
After those gates and creation of the operator-authorized migration inventory/cohort budget, activation is a separate
approved step. The operator authorizes that step, including OD-12 risk acceptance; the accountable Harness driver sets
one immutable activation-epoch ID and UTC start time in the lifecycle ledger and admission index before enabling new
producers, writer publication/keeper preconditions and debt-based admission refusal.

Immediately before epoch publication, I-04 captures a bounded delta from its initial inventory through the cutover
boundary under the existing admission lock, with I-01 coordinating admission serialization and settling any in-flight
pre-activation admissions into the captured set before publishing the boundary. The approved activation
card freezes maximum delta records, capture duration and any additional legacy cohort allowance. It includes new
hot/archive admissions, changed non-final records, reaped PUSHED tasks and pre-activation open PR identities.
Initial members keep their original inventory-start clock; newly admitted debt joins a separately authorized delta
cohort with its first inventory timestamp, without resetting existing clocks. Excess allowance, incomplete lookup,
unknown ownership or unmapped debt stops activation with producers disabled. No automatic grant expands the cohort.

The cutover receipt binds the initial/delta digests, capture boundaries, complete frozen PR/task sets, membership
reconciliation and epoch/index/ledger digests. No admission crosses that boundary unclassified. An admitted writer
before the boundary is in the frozen set. A new lifecycle admitted after it binds the published epoch in both records.
A post-activation continuation of a frozen pre-activation lifecycle keeps its null epoch and exemption across fix heads,
task continuations and historical branch aliases; continuation cannot retroactively acquire the new epoch.
Publication is atomic/read-back verified under the existing lock. Crash or mismatched copies leaves activation disabled
until idempotent reconciliation proves the same boundary and immutable epoch. Landing I-01 alone never sets the epoch
or enables its new writer precondition. This defines proposed activation behavior, not permission to activate here.
The operator separately authorizes canary execution.
Live migration remains separately scoped. Authorized migration/prerequisite dispatches retain the debt-refusal exemption.

### I-01 Harness: lifecycle custody, constrained review, and supervisor exit

Owner: Harness, accountable driver of #7919. Outcome: each writer exit either proves a disposition or exposes bounded custody.
Harness owns the supervisor changes in `scripts/delegate.py`, including continuation admission, review reservation,
and the exit call to Infra's common reaper. It never adds a second remover.
Non-goals: implementing runtime resume or physical removal, new provider routes, and crash-rescue identity.
Dependencies: approved schema, frozen I-02 continuation API and I-03 removal-receipt API. Activation waits for both implementations.

Owned source and template paths:

- `scripts/delegate.py`
- `scripts/orchestration/task_record_store.py`
- `scripts/orchestration/dispatch_settle.py`
- `scripts/orchestration/task_lifecycle.py`
- `agents_extensions/shared/schemas/task-lifecycle.v1.schema.json`
- `scripts/orchestration/task_closeout.py`
- `scripts/orchestration/stale_task_records.py`
- `scripts/orchestration/orchestrator_control.py`
- `scripts/orchestration/dead_worker_state.py`
- `scripts/api/fleet_workers_collect.py`
- `scripts/api/lane_health.py`
- `scripts/api/occupancy.py`
- `scripts/api/delegate_router.py`
- `scripts/guardrails/delegate_ownership.py`
- `scripts/work/attention.py`
- `scripts/build/fresh/writer.py`
- `scripts/lexicon/runner/atlas_job.py`
- `scripts/eval/uk_preamble/dispatch.py`
- `scripts/fleet/hramatka_hygiene_check.py`
- `scripts/hygiene/tmp_sweep.py`
- `scripts/session_start.sh`
- `scripts/config/trails/decision-tables.v0.yaml`
- `scripts/config/trails/rb2-dispatch-loop.trail.yaml`
- `scripts/orchestration/integration_sweep.py`
- `scripts/orchestration/merge_queue_keeper.py`
- `scripts/review/record_cf_verdict.py`
- `scripts/review/closeout_cli.py`
- `scripts/publish/github.py`
- `docs/templates/writer-review-request.v1.md`, new fixed brief template.

Owned test paths:

- `tests/test_writer_lifecycle.py`, new disposition and supervisor integration tests.
- `tests/test_writer_lifecycle_consumers.py`, new parameterized producer/consumer and board tests.
- `tests/test_delegate.py`
- `tests/test_dispatch_settle.py`
- `tests/test_delegate_review_admission.py`
- `tests/test_delegate_review_rounds.py`
- `tests/test_delegate_timeouts.py`
- `tests/test_delegate_public_causes.py`
- `tests/test_delegate_ownership.py`
- `tests/test_delegate_ownership_dispatch.py`
- `tests/orchestration/test_task_record_store.py`
- `tests/orchestration/test_task_lifecycle.py`
- `tests/orchestration/test_task_closeout.py`
- `tests/orchestration/test_task_lifecycle_carriers.py`
- `tests/orchestration/test_stale_task_records.py`
- `tests/orchestration/test_orchestrator_control.py`
- `tests/orchestration/test_integration_sweep.py`
- `tests/orchestration/test_merge_queue_keeper.py`
- `tests/api/test_delegate_active.py`
- `tests/api/test_fleet_workers.py`
- `tests/api/test_lane_health.py`
- `tests/api/test_occupancy.py`
- `tests/build/test_fresh_writer.py`
- `tests/test_atlas_job_protocol.py`
- `tests/eval/test_uk_preamble_dispatch.py`
- `tests/test_fleet_hramatka_hygiene_check.py`
- `tests/test_tmp_sweep.py`
- `tests/test_trail_runner.py`
- `tests/test_record_cf_verdict.py`
- `tests/review/test_record_cf_verdict.py`
- `tests/test_review_closeout_cli.py`
- `tests/test_typed_github_publisher.py`
- `tests/test_publish_r5_regressions.py`
- `tests/test_publish_diagnostics.py`
- `tests/test_publish_hostname.py`
- `tests/publish/test_pr_merge_squash_scan.py`
- `tests/ai_agent_bridge/test_acp_execution.py`
- `tests/api/test_atlas_jobs_router.py`
- `tests/hygiene/test_tmp_sweep_scratch.py`
- `tests/orchestration/test_interrupted_caller_matrix.py`
- `tests/review/test_attempt_artifact_binding.py`
- `tests/test_delegate_admission.py`
- `tests/test_delegate_api.py`
- `tests/test_delegate_bounded_advisory.py`
- `tests/test_delegate_check_budget.py`
- `tests/test_dispatch_isolation.py`
- `tests/test_reconcile_sweep.py`
- `tests/test_remote_supervisor.py`
- `tests/test_sibling_git.py`
- `tests/test_work_contract.py`
- `tests/trails/test_rb2_rb5_v11.py`

| AC | Acceptance criterion | Verification |
| --- | --- | --- |
| I01-AC01 | Dirty, unpushed, unknown, background-leftover, finalize-exception, and interrupt exits persist typed attempt failures before telemetry with active custody; no new writer `needs_finalize` | `tests/test_writer_lifecycle.py`, D-05 through D-08 and interrupt cases |
| I01-AC02 | Terminal disposition requires exact receipts and survives atomic-write interruption; attribution, public-copy and operator-log checks enforce the OD-12 assurance boundary without claiming same-user authentication | Same file and `tests/orchestration/test_task_lifecycle.py`, missing/mismatched/stale receipt, wrong-session and assurance-field cases; forged-event boundary in I03-AC04 |
| I01-AC03 | Actual branch/head, wait/status, hot/archive, settlement, attention, and all enumerated status consumers remain fail-closed across mixed schemas | `tests/test_writer_lifecycle_consumers.py` covers the source manifest; existing consumer tests above |
| I01-AC04 | Only the resolver-returned invocation and fixed brief can request review; writer merge/enqueue/self-review remain refused and PR creation requires exact-head APPROVE | `tests/test_delegate_review_admission.py` and `tests/test_writer_lifecycle.py`, altered invocation/model/template and `SELF_REVIEW_DETECTED` negative cases |
| I01-AC05 | First new blocker freezes a 24-hour deadline without reset; one ordinary blocked writer refuses ordinary outcomes; status output contains all six explicit writer/legacy/nonwriter blocked/overdue count fields; bounded migration/prerequisite grants exempt only debt refusal; deadline breaches escalate | `tests/test_writer_lifecycle_consumers.py`, literal status-field/zero/UNKNOWN assertions; clock before/at deadline and after restart; full-slot exemption and unrelated-outcome refusal; missing escalation stays visible; no expiry-triggered deletion |
| I01-AC06 | Same-head duplicates and cross-head review shopping fail across task/harness/restart; successor briefs carry unresolved lifecycle findings; publication/keeper require driver dispositions only for post-activation admissions bound to the index and ledger epoch; malformed/conflicting lifecycle evidence refuses; pre-activation and no-dispatch gates are unchanged | `tests/test_delegate_review_admission.py`, `tests/test_record_cf_verdict.py`, `tests/orchestration/test_integration_sweep.py`, and `tests/orchestration/test_merge_queue_keeper.py`: REJECT at H, trivial H', APPROVE at H' without disposition refuses; missing/tampered chain/brief refuses; post-activation default/explicit/renamed writer branch missing binding refuses; a pre-activation open writer PR with exact-head APPROVE and green CI still enqueues after I-01 lands; include I-02 through I-04, an already-reaped tree and agent-prefixed no-dispatch PR; premature activation and conflicting/malformed epoch/index evidence refuse; non-writer/read-only fixtures preserve gates |
| I01-AC07 | Supervisor exit after gated publication invokes the common reaper and proves absence for new and reused trees, even with a failed attempt result; crash between push and cleanup retries the same receipt | `tests/test_writer_lifecycle.py`, real Git OPEN-PR fixture and process-exit/receipt integration; no fake reaper return as behavior proof |
| I01-AC08 | Read-only/review/Atlas unconfirmed completion uses top-level `custody_held` plus separate typed attempt failure; complete report/verdict plus absence is required for `done`; failed review cannot reset reservation | `tests/test_writer_lifecycle_consumers.py`, `tests/test_delegate_review_rounds.py`, and `tests/test_atlas_job_protocol.py`, missing report/verdict, background and unknown probe cases |
| I01-AC09 | Every status-keyed release/finality/archive/reaper consumer is enumerated and tested; none releases a custody-held tree for any attempt result; `custody_held` belongs to no released/final set | `tests/test_writer_lifecycle_consumers.py` enumerates status comparisons/sets across repository Python/shell/YAML consumers in an explicit consumer-to-test ledger, failing on an unclassified release site; failed/timeout/crashed/cancelled/refusal/background cases and old-reader unknown-status retention; I-03 real claim/removal tests prove no custody-held release |
| I01-AC10 | Before any PR exists, negative verdicts append to the durable chain; effective APPROVE requires the reserved exact-head review and driver dispositions; all publisher pr-create routes and drafts enforce that receipt, then reconcile the same PR/marker after timeout | `tests/test_record_cf_verdict.py`, `tests/review/test_record_cf_verdict.py`, `tests/test_typed_github_publisher.py` and `tests/test_publish_r5_regressions.py`, no-PR REQUEST_CHANGES/APPROVE, missing/ineffective receipt, moved H, altered branch facts, direct CLI/shim/typed/supervisor draft attempts and interrupted publication without a duplicate PR |
| I01-AC11 | Material-finding remediation is a writer claim; candidate approval stays ineffective until driver disposition; D-04 handback survives tree removal and the next continuation cannot approve itself | `tests/test_writer_lifecycle.py`, `tests/test_review_closeout_cli.py` and recorder tests, H to H' fixture, writer adjudication refusal and driver-attested transition |
| I01-AC12 | Schema validates writer/non-writer ledgers; pre-removal local readiness is durable at each H/H' and closeout consumes only the exact current head after removal | `tests/orchestration/test_task_lifecycle.py`, `tests/orchestration/test_task_closeout.py` and supervisor tests, real Git reaped-tree reconcile/AC-sync/review/CI fixtures; H evidence for H', absent/tampered observation and interrupted write all refuse |
| I01-AC13 | Writer resolver/closeout state uses the canonical durable path; nonwriter debt gates ordinary nonwriter dispatches, bounded prerequisites remain possible, and disputes preserve clocks/counts after PUSHED | `tests/test_review_closeout_cli.py`, `tests/test_delegate_review_admission.py` and `tests/test_writer_lifecycle_consumers.py`, state survives real removal, relative/worktree path refusal, zero/nonzero/UNKNOWN admission, prerequisite bounds and dispute deadline across restart/head/tree changes |

Verify with `"$PROJECT_PYTHON" -m pytest -n 2 -q tests/test_writer_lifecycle.py tests/test_writer_lifecycle_consumers.py tests/test_delegate.py tests/test_dispatch_settle.py tests/test_delegate_review_admission.py tests/test_record_cf_verdict.py tests/orchestration/test_integration_sweep.py tests/orchestration/test_merge_queue_keeper.py`.
Also verify with `"$PROJECT_PYTHON" -m pytest -n 2 -q tests/orchestration/test_task_lifecycle.py tests/orchestration/test_task_closeout.py tests/review/test_record_cf_verdict.py tests/test_review_closeout_cli.py tests/test_typed_github_publisher.py tests/test_publish_r5_regressions.py tests/test_publish_diagnostics.py tests/test_publish_hostname.py tests/publish/test_pr_merge_squash_scan.py`.
The card names the remaining owned test paths and any read-only importer tests explicitly in additional bounded commands.
Stop on a missing receipt accepted as terminal, review shopping, inconsistent discard attribution, or invisible overdue custody.
Residual owner: Harness.

### I-02 Harness: runtime continuation on the original lifecycle

Owner: Harness, same accountable driver. Outcome: bounded native or stateless continuation consumes the same checkpoint.
I-01 alone owns changes to the dispatch command and its caller in `scripts/delegate.py`.
I-02 supplies the continuation implementation through a frozen helper interface, so the packets cannot edit the same file.
Non-goals: new routes, broad transcript discovery, other adapter edits, and unbounded budgets. Dependency: I-01's approved interface.

Owned source paths:

- `scripts/orchestration/writer_continuation.py`, new helper.
- `scripts/agent_runtime/runner.py`
- `scripts/agent_runtime/registry.py`
- `scripts/agent_runtime/adapters/codex.py`
- `scripts/agent_runtime/adapters/claude.py`

Owned test paths:

- `tests/test_writer_continuation.py`, new runtime/real Git fixture tests.
- `tests/agent_runtime/test_runner_failover.py`
- `tests/agent_runtime/test_codex_adapter.py`
- `tests/agent_runtime/adapters/test_claude_adapter.py`

| AC | Acceptance criterion | Verification |
| --- | --- | --- |
| I02-AC01 | The documented command, wired by I-01, recreates the same absent path from exact remote H and appends an attempt without changing lifecycle identity | `tests/test_writer_continuation.py`, disposable Git remote and real I-01 caller integration |
| I02-AC02 | Soft checkpoint and hard-kill recovery preserve branch, dirty digest, budget, and nonce lineage; absent legacy limits snapshot the named defaults, three attempts, and 21600-second cumulative cap | Same file, deterministic watchdog fixtures for D-06/D-07/D-08 and final 600-second allowance inside the hard cap |
| I02-AC03 | Native resume accepts only the bound session/tree/lifecycle; stateless routes use the explicit checkpoint; other adapters and bridge restrictions remain unchanged | Same file and the enumerated Codex/Claude adapter tests, cross-task and reviewer-session refusal |
| I02-AC04 | Moved remote, live writer, path collision, exhausted budget, incomplete gate, unauthorized branch switch, and unsupported limits refuse continuation | Same file, negative cases with literal error assertions and no second checkout |
| I02-AC05 | Recreation invokes the I-03 baseline-generation API under the existing lock before spawn, keeping one creator and referencing the new inode/generation | `tests/test_writer_continuation.py` and read-only I-03 ignored-output tests, real remove/recreate at the same path, interrupted refresh and unexpected inode refusal |

Verify with `"$PROJECT_PYTHON" -m pytest -n 2 -q tests/test_writer_continuation.py tests/agent_runtime/test_runner_failover.py tests/agent_runtime/test_codex_adapter.py tests/agent_runtime/adapters/test_claude_adapter.py`.
Stop on another created path for one outcome or cross-task native resume. Residual owner: Harness.

### I-03 Infra: driver-attributed discard and automatic receipt-backed cleanup

Owner: Infra. Extend existing #10548 with this approved contract and a current DoR check.
Outcome: OPEN-PR PUSHED handbacks and merged reused trees leave no local tree, including automatic exit and scheduled recovery.
Harness I-01 owns the delegate exit caller. Infra owns the common guarded implementation and scheduled retry policy.
Non-goals: global retention eviction or crash-rescue identity. Dependency: I-01 schema and writer-specific guard approval.

Owned source paths:

- `scripts/orchestration/reap_worktrees.py`
- `scripts/orchestration/worktree_claims.py`
- `scripts/fleet/post_task_reap.py`
- `scripts/fleet/ignored_task_output.py`
- `scripts/orchestration/merge_closeout.py`
- `scripts/orchestration/reaper_lifecycle.py`
- `scripts/orchestration/scheduled_worktree_cleanup.py`
- `scripts/hygiene/branch_sweep.py`
- `scripts/maintenance/batch_state_retention.py`

Owned test paths:

- `tests/orchestration/test_writer_disposition_reap.py`, new disposition/delta/authority integration tests.
- `tests/test_continuation_worktree_reap.py`
- `tests/orchestration/test_reap_worktrees.py`
- `tests/orchestration/test_worktree_claims_cli.py`
- `tests/test_worktree_claims_lock_identity.py`
- `tests/test_fleet_post_task_reap.py`
- `tests/fleet/test_ignored_task_output.py`
- `tests/test_ignored_task_output.py`
- `tests/maintenance/test_batch_state_retention.py`
- `tests/hygiene/test_branch_sweep_evidence.py`
- `tests/orchestration/test_merge_closeout.py`
- `tests/orchestration/test_scheduled_worktree_cleanup.py`
- `tests/orchestration/task_family/test_executor.py`
- `tests/review/test_temp_lifecycle.py`
- `tests/test_branch_sweep.py`
- `tests/test_reused_worktree_retention.py`

| AC | Acceptance criterion | Verification |
| --- | --- | --- |
| I03-AC01 | Exact gated remote H and absent worker/claims remove an OPEN-PR or review-pending tree while retaining remote H and actionable review, without backup/rescue refs | `tests/orchestration/test_writer_disposition_reap.py`, D-01/D-02/D-04 real Git fixtures and complete ref inventory |
| I03-AC02 | Cross-family legacy creator, failed/needs_finalize successors, and authorized branch switch reach MERGED cleanup without a `done` successor | `tests/test_continuation_worktree_reap.py` and `tests/orchestration/test_merge_closeout.py`, #10548 fixture |
| I03-AC03 | Dirty/unpushed head without authority, unknown ignored output, live review inputs/process, UNKNOWN telemetry, ambiguous creator, and moved remote retain bounded custody | New disposition tests and `tests/orchestration/test_worktree_claims_cli.py`, negative/race cases |
| I03-AC04 | Unique-content deletion requires attributed decision, matching event/assignment, public-copy digest and operator-visible log; receipts expose same-user assurance under OD-12; MERGED closeout handles already-removed PUSHED trees | New disposition tests forge an authoritative Fleet/supervisor event: wrong binding or absent/mismatched public entry/log refuses even when local JSON matches; fully consistent same-user forgery demonstrates accepted lack of actor authentication and records `authority_assurance: attributed_same_user`; copied/stale/wrong-session decisions refuse; D-03/D-05 through D-12 and merge-closeout integration |
| I03-AC05 | Delta discard removes only exact commits after H and dirty task content, settles PUSHED at H, and preserves the remote branch, PR, and review; interrupted replay converges | New disposition tests, approved remote H plus gate-failed L; moved H/L, non-descendant L, unlisted content, digest drift, and unauthorized decision all refuse |
| I03-AC06 | Scheduled recovery calls the same writer receipt rule after exit, including OPEN PRs and reused cohorts; remote-branch deletion remains forbidden while OPEN; non-writer guards stay intact | `tests/orchestration/test_scheduled_worktree_cleanup.py` and new disposition tests, lost supervisor callback, interrupted receipt, and OPEN-PR branch-preservation cases |
| I03-AC07 | Claim/removal functions cannot release a custody-held tree on attempt status; release-site enumeration is complete and old-reader `custody_held` stays claimed | `tests/orchestration/test_worktree_claims_cli.py`, `tests/orchestration/test_reap_worktrees.py` and new disposition tests consume the I01-AC09 ledger, exercising each listed release path with held custody and every released attempt result |
| I03-AC08 | PUSHED releases only tree custody; non-final records/sidecars stay hot and branch refs stay protected before PR creation and after external closure, regardless of age or attempt status | `tests/test_branch_sweep.py`, `tests/hygiene/test_branch_sweep_evidence.py`, `tests/maintenance/test_batch_state_retention.py`, `tests/orchestration/test_scheduled_worktree_cleanup.py` and read-only `tests/orchestration/test_stale_task_records.py`, D-02/D-04/D-11 with absent tree, min-age zero, closed-PR durable head/main ancestry, UNKNOWN finality and selection/apply races; only verified final cleanup permits archival |
| I03-AC09 | New-inode recreation refreshes the effective ignored baseline by an append-only generation receipt without adding a creator or discarding unknown files | `tests/fleet/test_ignored_task_output.py`, `tests/test_ignored_task_output.py`, `tests/orchestration/test_worktree_claims_cli.py` and disposition tests, same-path new-inode baseline, stale/missing/ambiguous generation refusal and unchanged non-writer behavior |
| I03-AC10 | D-11 with no authorized actionable recovery stays blocked/protected until an attributed abandonment and residual entry permits D-10 cleanup | New disposition tests, unknown/external/operator closer, declined reopening, missing decision/public copy/residual owner and explicit preservation refusal; authorized decision preserves unmet issue ACs |

Verify with `"$PROJECT_PYTHON" -m pytest -n 2 -q tests/orchestration/test_writer_disposition_reap.py tests/test_continuation_worktree_reap.py tests/orchestration/test_reap_worktrees.py tests/orchestration/test_worktree_claims_cli.py tests/test_fleet_post_task_reap.py tests/orchestration/test_merge_closeout.py tests/orchestration/test_scheduled_worktree_cleanup.py`.
Also verify with `"$PROJECT_PYTHON" -m pytest -n 2 -q tests/test_branch_sweep.py tests/hygiene/test_branch_sweep_evidence.py tests/maintenance/test_batch_state_retention.py tests/fleet/test_ignored_task_output.py tests/test_ignored_task_output.py tests/orchestration/test_stale_task_records.py`.
Stop on silent unique-content loss, missing/inconsistent discard evidence, or weakened non-writer guards. The same-user forgery residual requires operator-only OD-12 acceptance. Residual owners: Infra and Harness.

### I-04 Infra: bounded migration and canonical instruction rollout

Owner: Infra for inventory, disposition, and integration. Harness supplies recovery through I-01/I-02 without editing their files here.
Outcome: every scoped legacy record has a verified disposition, no new backup pile, and truthful remaining debt.
Owned source and canonical documentation paths:

- `scripts/orchestration/writer_lifecycle_migration.py`, new migration command.
- `tests/orchestration/test_writer_lifecycle_migration.py`, new tests.
- `docs/runbooks/worktree-cleanup.md`
- `agents_extensions/shared/rules/critical-rules.md`
- `agents_extensions/shared/rules/delegate-must-use-worktree.md`
- `agents_extensions/shared/rules/workflow.md`
- `agents_extensions/shared/contracts/task-lifecycle-closeout.md`
- `agents_extensions/shared/rules/core.md`
- `agents_extensions/shared/agents/curriculum-track-orchestrator.md`
- `agents_extensions/shared/skills/drive-epic/references/routing-and-dispatch.md`
- `docs/runbooks/atlas-job-protocol.md`

Deploy changed agent-rule consumers with `npm run agents:deploy`; generated copies are deployment output, never hand-edited owned sources.
Non-goals: live host execution without an authorized cohort, unrelated trees, and #10537 repair.
Dependencies for code delivery: approved I-01 through I-03 interfaces/implementations and strict card plus current preflight PASS.
Code must land before activation. Live execution additionally requires operator-authorized cohort/budget and fresh preflight.

| AC | Acceptance criterion | Verification |
| --- | --- | --- |
| I04-AC01 | Read-only inventory covers hot/archive, missing issue/tree, directory-owner mismatch, dirty-only work, branch switches, and every claimant without mutation | `tests/orchestration/test_writer_lifecycle_migration.py`, full fixture inventory comparison |
| I04-AC02 | Apply is scoped and idempotent, binds a cohort issue before issue-less discard, validates local decisions and public digests, and refuses unresolved custody | Same file, issue-less, interrupted replay, wrong-identity, and out-of-scope negative cases |
| I04-AC03 | Independent fixtures cover all twelve shapes, each with one evidenced disposition, no new needs_finalize/backup/ref, and exact blocked/overdue owners and counts | Same file and evaluator-held fixture ledger, including D-11/D-12 and delta discard |
| I04-AC04 | Canonical instructions and deployed consumers match the approved contract; every implementation issue has parent membership and strict DoR PASS | Markdown lint, `npm run agents:deploy` plus deployment check, and `"$PROJECT_PYTHON" scripts/ci/check_issue_task_quality.py --issue <N> --strict --json` for each card |
| I04-AC05 | Retired/unavailable writers receive a recorded eligible substitution with fresh independence/capacity checks, or bounded escalation; no silently changed author identity | Migration tests, retired route and no eligible replacement negative cases |
| I04-AC06 | Three-shape canary observes real semantic and removal outcomes within six invocations/43200 seconds; bulk refuses missing canary, frozen aggregate allowance, or health/headroom proof | Migration tests, budget/canary refusal; separate authorized live canary receipts and held-out evaluator output before bulk |
| I04-AC07 | Legacy clock starts at authorized inventory, debt counts separately under operator-approved cohort budget, and authorized migration/prerequisite dispatches remain admissible when ordinary outcomes are refused; I-04 lands before refusal activation; disk-pressure residual stays visible | Migration tests and board projections with synthetic hundred-item historic cohort: no retroactive overdue burst, no restart reset, separate counts, one cohort escalation at deadline, missing/exceeded budget refusal, bounded exception/unrelated-outcome refusal, and activation-before-I-04 rejection; fresh disk proof before closeout |
| I04-AC08 | Activation delta capture is bounded, classifies every late pre-activation admission, preserves old clocks and freezes PR/task exemptions before enabling producers | Migration tests plus read-only I-01 admission/classifier tests, a writer admitted between initial inventory and epoch including late needs_finalize, fix commit after activation, archive/reaped task, capture/epoch crash and excess/UNKNOWN delta; no gap, duplicate cohort or silently reset clock |

Verify with `"$PROJECT_PYTHON" -m pytest -n 2 -q tests/orchestration/test_writer_lifecycle_migration.py` and `npx --no-install markdownlint-cli2 docs/runbooks/worktree-cleanup.md`.
A scoped live migration proves the inventoried denominator and zero unresolved receipts before closeout.
Stop on unknown ownership, exceeded budgets, or unrecorded deletion. Residual owners: Infra and each original owning lane.

All packets run Ruff on changed Python, the required explicit invariant tests before push,
and explicitly named tests of every changed shared-helper importer. They retain exact-head cross-family review and required CI.
Each card freezes its complete owned manifest, AC hash, stop policy, and reviewer invocation after live routing resolution.
No packet is DoR-ready until its issue exists, its strict card checker passes, and its current dispatch preflight passes.
Issue #10559 cannot close with draft packets alone. AC-03 remains owned by the accountable Harness driver with Infra.

## What this does not change

Merge authority remains with the existing merge-queue keeper and accountable integration/stream ownership.
Writers never merge or enqueue. Cleanup does not confer merge authority.
Review independence remains cross-family and outside the writer-of-the-moment, with attested model/family/harness.
Self-review is refused through `SELF_REVIEW_DETECTED`. Advice, designated approval, and formal review remain distinct.
Exact-head review and same-head required CI still bind; moved heads void old approval and CI.
No PR, including a draft, opens before exact-head APPROVE. No pending, cancelled, or failed required check permits enqueue.
This proposal introduces no new review exception, provider route, stream lease, or authority plane.
PUSHED and ABANDONED are worker custody dispositions. They do not satisfy product DoD or erase residual acceptance criteria.

## Open decisions requiring designated approval

Approval must bind the recomputed normative SHA-256. This authoring round grants none of these decisions.
The advisor pair is Opus 5.5 and Sol 6.1 under the designated-approval rule; the operator may also approve those rows.
OD-12 requires the operator alone. Actual live cohort, budgets, deletion grants and activation remain separately operator-authorized.
For OD-04, Option B is recommended because it retains review dispatch authority with the driver.

| ID | Decision awaiting approval | Approver |
| --- | --- | --- |
| OD-01 | Adopt lifecycle receipts, top-level `custody_held`/`writer_pushed`, exact-head durable local readiness and schema/closeout compatibility, separating attempt settlement, tree release and finality before activation | Advisor pair |
| OD-02 | Adopt the defined registered-stream lane, 24-hour new/inventory-start legacy clocks, one ordinary blocked-writer slot, separate operator-budgeted legacy debt, bounded migration/prerequisite exemptions, nonwriter admission refusal and dispute attention/clocks, and cohort escalation after I-04 lands | Advisor pair |
| OD-03 | Reserve discard, retry and finding-disposition policy authority to the attributed lane driver and permit scoped delta discard; same-user forgery risk acceptance is separate under OD-12 | Advisor pair |
| OD-04 | Name Option A writer-requested review or Option B driver-requested review on the writer's behalf, allow durable pre-PR/PR mechanical verdict recording without judgment authority and require material-finding driver handback, and adopt one review per head with driver-only timeout replacement and lifecycle-scoped finding disposition; approval naming neither option is invalid | Advisor pair |
| OD-05 | Approve writer-specific PUSHED tree removal while a PR is OPEN, including reused cohorts, and automatic supervisor/scheduled recovery without preservation; retain OPEN-PR remote-branch protection | Advisor pair |
| OD-06 | Approve same-path recreation with a verified baseline generation and one original creator across settled rounds, the continuation command, and narrowly scoped delegate-native session resume; no new outcome or transcript discovery | Advisor pair |
| OD-07 | Approve three-attempt/21600-second default cumulative execution and the final 600-second allowance inside each attempt; retain the named existing per-attempt defaults | Advisor pair |
| OD-08 | Approve cohort tracking issues, retired-route substitutions and the three-lifecycle/six-invocation/43200-second canary, keeping actual live cohort, debt/execution budgets and deletion grants separately operator-authorized | Advisor pair |
| OD-09 | Approve Harness keeper/verdict-recorder ownership and publisher/reservation/rejection-chain preconditions with bounded activation delta inventory and frozen exemption classification only for admissions bound to the post-activation index and lifecycle-ledger epoch; pre-activation and agent-prefixed no-dispatch PRs retain today's gates, with refusal for malformed/conflicting lifecycle evidence | Advisor pair |
| OD-10 | Ban `keep_worktree` for new writers while preserving legacy retention until a scoped custody decision | Advisor pair |
| OD-11 | Require evaluation fixtures from outside the implementation author's family | Advisor pair |
| OD-12 | Accept same-user authoritative-event/receipt forgery and omission evasion through a valid non-task trailer plus publication from an unindexed ref, requiring no tampering, as out-of-scope security-posture risks; today's missing-trailer refusal, retained-index classification, public-copy digests, issue entry and operator-visible log do not close the omission gap, for which unpublished-H blocked custody provides only indirect detection; activation remains blocked without operator acceptance | Operator |

<!-- normative:end -->

## Risks and outstanding proof

Remote equality races with another writer or remote deletion. Single-writer admission and repeated observation reduce
that window but do not create atomicity between GitHub and the host. Failed post-delete observation remains an owned repair incident.
Unknown session authority, content scope, ignored artifacts, branch switches, or #10537 recovery identity block mutation.
Owner: Infra for deletion proof, Harness for identity/admission, and the original lane for content custody.
Expiry cannot grant discard authority. Overdue custody remains counted; ordinary admission obeys the normative slot/budget
rules and bounded migration/prerequisite exemptions. Same-user forgery and omission evasion through a valid non-task trailer
plus publication from an unindexed ref remain proposed residuals under OD-12, owned by Harness and awaiting operator-only risk acceptance.
Omission needs no tampering and has only indirect detection through unpublished-H blocked custody.
Attribution and digest agreement do not prove actor authentication.
No approved digest can be claimed from this author's own checks.
Round 5 brings custody release versus finality, nonwriter admission, dispute attention, durable review state and
activation delta capture into the normative contract for B4/R1-R3. Their implementation and approval remain with
Harness and Infra; no authoring check proves them operational. No B1-B5 or R1-R3 item is silently deferred.

The supplied exact-r6 Opus CHANGES_REQUESTED identifies B-R6-1 at head
`cbfc6399a544a6eb8dfc3e8e402a49618fc8a1e7` and normative digest
`576db353d7c0a465bba29d2b06892a27580bb758da033bb7277a9509a6e0dfed`.
This bounded r7 correction takes remedy (a), accurately describing the omission residual without changing the classifier or packets.
The accountable driver owns serial publication, new-head independent review and decision routing.
The prior reviews and these authoring checks do not approve r7. Material correctness or missing proof blocks;
editorial nits remain advisory. #10559 AC-03 still requires actual implementation issues with parent links,
strict task-card PASS, and current dispatch preflight. This brief prohibits creating them.
Owners: accountable Harness driver and Infra. The pre-delivery disk-pressure residual remains Infra's responsibility.

## Round-7 reconciliation and current source evidence

This revision addresses only B-R6-1 from the supplied exact-r6 Opus CHANGES_REQUESTED.
It retains r5 B1-B5 and N1 as closed specification corrections. Advisory A1-A6 remain advisory evidence and add no scope.
All twelve end shapes, all four implementation packets and the classifier design are unchanged.
The trust-boundary paragraph and OD-12 now put the full omission residual to the operator for risk acceptance.

| Item | Correction and changed section | Tracked source evidence | Retained acceptance |
| --- | --- | --- | --- |
| B-R6-1 | Remedy (a): a valid non-task trailer plus publication from an unindexed ref can evade registered-provenance classification without tampering; only unpublished-H blocked custody gives indirect detection; OD-12 still requires operator acceptance before activation | `scripts/review/record_cf_verdict.py:_attribute_commit` at 370-377 permits `trailer-model`, and at 392-393 can leave task IDs absent; `scripts/audit/lint_agent_trailer.py:_is_exempt_trailer` at 173-183 exempts `<agent>/inline`; the proposed classifier joins identities/aliases, not ledger-recorded commit SHAs/H; the finalizer's branch-switch blocker does not detect remote-ref publication without a local branch switch | Unchanged I01-AC06 and all four packets, OD-12 |

Authoring validation recomputes the normative byte-range digest independently and compares the exact diff,
all twelve end-shape rows, all four packets and the classifier against the supplied r6 head.
These checks validate the document, not runtime behavior or independent approval.
The worker returns a clean local commit. Root owns publication and new-head independent review.
No implementation, new design, policy approval, migration, canary, activation or lease action is authorized by this correction.

## Round-6 reconciliation and source evidence, historical

This revision accepts exactly five corrections from the supplied r5 reviews. Opus's REQUEST_CHANGES is blocking
revision input despite Gemini's APPROVE. The source revision at the top supplies current-code evidence;
the classifier, publisher and activation requirements remain proposed behavior. B1-B5 and the other r5 requirements remain intact.

| Item | Correction and changed section | Current source evidence | Retained acceptance |
| --- | --- | --- | --- |
| N1 | Writer-PR classifier distinguishes proven registered dispatch/index provenance from ordinary mandatory or model-attributed trailers; valid manual/orchestrator no-dispatch publication retains existing gates; genuine UNKNOWN/MALFORMED refuses | `scripts/review/record_cf_verdict.py:_attribute_commit` at 304 validates hot/archive records and uses trailer/model or harness fallback without a record; `BranchReviewFacts.author_task_ids` at 500 retains even unregistered slugs; `collect_branch_review_facts` at 663 and `pr_review_facts` at 918 provide complete attribution/enumeration | I01-AC06, OD-09 |
| R-b | Abandonment trust boundary and OD-12 explicitly name trailer/provenance omission beside same-user event/receipt forgery, today's refusal and the remaining valid-trailer evasion boundary | `_attribute_commit` at 336-337 refuses missing/malformed trailers; at 343-387 record-backed attribution precedes no-record fallback; retained admission-index enforcement is proposed, not live proof | I01-AC02/06, I03-AC04, OD-12 |
| R-a nit | Writer-PR classifier says missing global epoch/index stores are UNKNOWN; individual records after complete lookup are MISSING | `_attribute_commit` at 343-387 distinguishes an existing hot/archive task record from no-record fallback; the proposed activation control and classifier table supply the store/entry distinction | I01-AC06, I04-AC08 |
| R-c nit | Packet delivery/cutover exempts continuations of frozen pre-activation lifecycles after activation, preserving null epoch | I-01/I-04's proposed immutable frozen set and index aliases distinguish a new lifecycle admission from continuation; no current producer is claimed to enforce this | I01-AC06, I04-AC08 |
| Base recheck nit | Pre-PR publisher checks base ref name and complete reviewed commit-set equality; a moved main SHA alone cannot force unchanged-head review | `pr_review_facts` at 937-970 validates base name and exact H, collects current facts, applies authorship exclusions and compares GitHub/local commit sets; observed base SHA remains evidence | I01-AC10, unchanged-head reservation rule |

Round-6 authoring recomputed its normative digest using the documented Python byte range and an independent Node crypto read.
Its document/cited-path, packet-ownership, Markdown, diff/trailer and four mandatory guard checks did not supply independent approval.
The subsequent supplied Opus recheck returned CHANGES_REQUESTED with B-R6-1, addressed in the round-7 reconciliation above.

## Round-5 reconciliation and source evidence, historical

All eight round-4 critic items are accepted as specification corrections. The round-5 source revision `78098ad5c632878feba755f234cfaa7951a4b6f4` is the
current-code evidence baseline, not a claim that these proposed gates already operate. The full supplied report
returned `VERDICT: REQUEST_CHANGES`; its B1-B5/R1-R3 findings are the only scope of this revision.
The r4 artifact was cherry-picked from `10bdf2ef1c62a430f6a85fb6a34e03d07a12e586`, preserving its author and trailer.

| Item | Correction and changed section | Current file/function evidence | Packet acceptance |
| --- | --- | --- | --- |
| B1 | Pre-PR verdict recording and publisher gate; I-01 manifest includes the publisher | `scripts/publish/github.py:publish` at line 403 scans/sends pr-create without the pr-merge readiness guard; `scripts/review/record_cf_verdict.py:_pr` at 1309 and `record` at 1507 require an open PR; `collect_branch_review_facts` at 663 provides the branch fact collector | I01-AC04/06/10 |
| B2 | Review request authority and rejection history distinguishes remediation claims, driver disposition and ineffective candidate approval; D-04 handback precedes approval publication | `scripts/review/closeout_cli.py:_cmd_finding` at 536 persists adjudication; `scripts/delegate.py:_create_auto_finalize_pr` at 7589 is a writer publication caller; neither establishes the proposed driver-only disposition handback | I01-AC11 |
| B3 | Dispositions/schema; Exact pushed proof and tree recreation; durable H/H' local readiness before reaping and inode-generation refresh | `scripts/orchestration/task_lifecycle.py:validate_lifecycle` at 746 uses the closed schema; `_latest_premerge_local` at 1380, `_local_readiness` at 1395 and `evaluate` at 1450 consume prior local facts; `scripts/orchestration/task_closeout.py:GhGitHubAdapter.observe` at 457 gathers them; `scripts/fleet/ignored_task_output.py:reused_worktree_creator` at 283 and `_classified_inventory` at 460 require one creator and matching baseline inode | I01-AC12, I02-AC05, I03-AC09 |
| B4 | Custody release, lifecycle finality and branch protection; explicit hot-record/ref guards and I-03 manifests | `scripts/orchestration/stale_task_records.py:keep_hot_reason` at 1065 and `archive_terminal` at 1292 depend on path/status; `scripts/maintenance/batch_state_retention.py:_eligible` at 370 checks released status/age; `scripts/hygiene/branch_sweep.py:_active_tasks` at 153 skips released tasks; `scripts/orchestration/scheduled_worktree_cleanup.py:_stale_ref_delete_reason` at 312 accepts durable CLOSED heads; cleanup passes at 490/629/781 need lifecycle protection | I01-AC03/09, I03-AC08 |
| B5 | Writer-PR classifier and keeper scope freezes exemptions and distinguishes MISSING from UNKNOWN; End shapes D-11 has an attributed D-10 exit with residual owner | `scripts/orchestration/merge_queue_keeper.py:run` inspects PR comments/checks at 766-825; `scripts/review/record_cf_verdict.py:pr_review_facts` at 918 and `record` at 1507 resolve exact-head author/task facts; no current classifier proves the proposed exemption boundary | I01-AC06, I03-AC10, I04-AC03/08 |
| R1 | Review request authority and rejection history pins the durable canonical writer state file explicitly | `scripts/review/closeout_cli.py:_build_parser` requires global --state-file at 689-697; resolver output merges into that file, with a worktree-relative example in the epilog | I01-AC13 |
| R2 | Packet ownership and delivery order captures bounded activation delta and freezes all pre-activation PR/task identities before enabling producers | `scripts/orchestration/task_record_store.py` is the existing shared task store; `scripts/delegate.py` admits tasks; activation/delta capture is a proposed I-04 helper plus I-01 admission integration, not an existing producer capability | I04-AC08, I01-AC06 |
| R3 | Bounded blocked custody defines nonwriter admission and dispute attention/clocks; Read-only and review completion replacement retains separate counts | `scripts/orchestration/worktree_claims.py:RELEASED_TASK_STATUSES` at 65 classifies attempt outcomes; `scripts/work/attention.py` is the existing attention consumer owned by I-01; neither proves the proposed debt/dispute policy | I01-AC05/13 |

Source evidence was read with bounded `sed` ranges and `rg -n` definition checks in the assigned worktree.
Existing source/schema/test paths and exclusive packet ownership are checked by the held authoring verifier.
Each implementation verification command names tests explicitly and uses at most two workers. Paths marked new
are implementation additions; their future behavior tests were not executed during this document revision.
Markdown lint, the existing normative digest recipe, an independent Node crypto computation, diff checks and the
four required static guards validate this artifact. They cannot establish implementation readiness or critic approval.
Ruff is inapplicable to the one-document change. Historical verification below is not this turn's evidence.
No Entire locator informed this revision; bounded intake returned an empty result set with no omitted results.
The committed artifact remains unpushed for the driver's serial publication lane, with disposition `needs_finalize`.
The CTO owns the ordered Opus-via-AGY and independent Gemini 4 exact-r5 critiques; Harness owns reconciliation
and publication, Infra owns implementation/migration residuals. No PR, activation, lease change or cleanup is performed here.

## Historical critic-item traceability, rounds 2 through 4

| Item | Resolving section and acceptance criterion |
| --- | --- |
| B1 | Bounded blocked custody; I01-AC05 and I04-AC07 |
| B2 | End shapes D-05/D-11/D-12; Delta discard to PUSHED; I03-AC04/I03-AC05 and I04-AC03 |
| B3 | Review request authority and rejection history; OD-04; I01-AC04/I01-AC06 |
| B4 | Resumable budget and failure handling; Packet ownership and delivery order; I01-AC07/I03-AC06 |
| B5 | Abandonment and deletion authority; OD-12 threat-model residual; I01-AC02/I03-AC04 |
| N1 | Driver-only abandon authority; OD-03 |
| N2 | Exact pushed proof and tree recreation; OD-06; I02-AC01 |
| N3 | Command-bounded literal inventory and disjoint manifests in I-01 through I-04; Packet ownership and delivery order |
| N4 | Read-only and review completion replacement; I01-AC08 |
| N5 | Migration from needs_finalize; I04-AC02/I04-AC05/I04-AC06/I04-AC07; OD-08 |
| N6 | Resumable budget and failure handling defaults; OD-07; I02-AC02/I02-AC04 |
| N7 | Exact pushed proof and tree recreation, receipt freshness and push-time digest |
| N8 | Implementation issue packets and Risks and outstanding proof; AC-03 remains open with Harness/Infra owners |
| R1 | Review request authority and rejection history; I01-AC06; OD-04/OD-09 |
| R2 | Writer-PR classifier and keeper scope; I01-AC06; OD-09 |
| R3 / N-c | Bounded blocked custody; Packet ownership and delivery order; I01-AC05/I04-AC07; OD-02 |
| R4 | Read-only and review completion replacement; I01-AC09/I03-AC07; OD-01 |
| R5 | Abandonment and deletion authority, explicit same-user residual; I03-AC04; OD-12 |
| N-a | I-01/I-03 test ownership, I-04 instruction ownership; round-3 inventory command |
| N-b | Open decisions OD-04, OD-09, OD-10 and OD-11 |
| N-d | End shapes D-11, operator-closure decision and no automatic restore |
| NB-1 | Writer-PR classifier and keeper scope; Packet ownership and delivery order; admission/ledger activation-epoch binding; I01-AC06; OD-09 |
| Round-4 OD-09 | Explicit post-activation scope and pre-activation/no-dispatch exemption in OD-09 |
| Round-4 OD-04 | Review request authority and rejection history; explicit A/B approval record, invalid unnamed choice and recommended Option B; OD-04 |
| Round-4 OD-03 / OD-12 | Driver authority and delta discard remain OD-03; operator-only same-user forgery risk acceptance is OD-12 |
| N-e | Bounded blocked custody status fields; I01-AC05 output assertions |
| N-f | Normative closing marker precedes Risks and outstanding proof and this table |

## Evidence from round-4 authoring

The bounded revision addresses NB-1, OD-09, OD-04 and the OD-03/OD-12 risk-acceptance split.
The supplied round-3 critic is input, not approval of this revised digest. Its lesser residuals retain their owners above.
The spec's digest command with the prescribed `PROJECT_PYTHON` printed:

```text
5d19cf956eff22829e3c1590ae121be0ec56cf08bb29fbdfebf69eb9db4bbe3c
```

`node_modules/.bin/markdownlint-cli2 docs/architecture/writer-worker-lifecycle.md` returned `Summary: 0 error(s)`.
`git diff --check` exited 0 with no output. These authoring checks do not prove implementation behavior or grant approval.
Round-3 and round-2 evidence below is historical; its OD-03 risk references predate the operator-only OD-12 split.

## Evidence from round-3 authoring

Commands in this section ran in the assigned round-3 dispatch worktree. The supplied critic contract was read first
with `cat` on its provided result path. Its raw terminal line was `VERDICT: REQUEST_CHANGES`.
Round 3 is limited to R1-R5 and the named cheap corrections. Any newly discovered class becomes an owned residual,
not a reopened full review. Independent revised-hash critic approval and designated decision approval remain with Harness.

`git cherry-pick c7ac6d7c49bd5391118c976935542902d96ec3e2` returned:

```text
[codex/spec-10559-writer-lifecycle-r3 46a7bf48a8] docs(harness): resolve writer lifecycle spec blockers (#10559)
 1 file changed, 937 insertions(+)
 create mode 100644 docs/architecture/writer-worker-lifecycle.md
```

`git merge-base HEAD origin/main` returned `4b4696291a613436725ad1e1c5aa5249f4bb3da5`.
`date -u` returned `Tue Oct 13 14:29:50 UTC 2026`.
The prescribed Entire `status` returned `"available": true`; its bounded
`search --query '10559 writer lifecycle'` returned `"results": [], "omitted": [], "scanned": 500`.
No recalled locator informed this revision.

The following command derives literal-reference coverage and unowned paths:

```bash
"$PROJECT_PYTHON" - <<'PY'
from pathlib import Path
import re
import subprocess
s = Path('docs/architecture/writer-worker-lifecycle.md').read_text()
owned = set(re.findall(r'^- `([^`]+)`', s, re.M))
for root in ['scripts', 'tests', 'agents_extensions', 'docs/runbooks']:
    r = subprocess.run(['rg', '-l', 'needs_finalize', root], capture_output=True, text=True)
    assert r.returncode in (0, 1), r.stderr
    hits = set(r.stdout.splitlines())
    missing = sorted(hits - owned)
    print(root, 'hits', len(hits), 'unowned', len(missing))
    if missing:
        print('\n'.join(missing))
PY
```

Before revision, raw counts were:

```text
scripts hits 24 unowned 0
tests hits 34 unowned 19
agents_extensions hits 4 unowned 3
docs/runbooks hits 2 unowned 1
```

All nineteen tests are now explicitly owned by I-01 or I-03; all four instruction docs by I-04.
Their paths are listed in those manifests. After revision the same command returned:

```text
scripts hits 24 unowned 0
tests hits 34 unowned 0
agents_extensions hits 4 unowned 0
docs/runbooks hits 2 unowned 0
```

`sed -n '48,85p' scripts/orchestration/worktree_claims.py` returned:

```text
RELEASED_TASK_STATUSES = frozenset(
    {
        "done",
        "failed",
        "no_deliverable",
        "timeout",
        "rate_limited",
        "cancelled",
        "crashed",
        "dry_run",
    }
)
```

`sed -n '2890,3005p' scripts/orchestration/reap_worktrees.py` returned:

```text
                    if task_status in ("done", "failed", "no_deliverable") and (
                        active_ids is not None and task_id not in active_ids
                    ):
                        task_settled = True
```

Known released/final attempt statuses justify a distinct top-level held-custody status and I01-AC09/I03-AC07.
Their future release-site evaluation is an implementation acceptance criterion, not completed testing here.

`sed -n '279,315p' scripts/fleet_comms/message_plane.py` returned:

```text
    def open_ask(
        self,
        *,
        recipient: str,
        body: str,
        sender: str = "message-plane",
```

Caller-supplied sender is attribution, not process authentication. This design asserts no sandbox or secret boundary.

`sed -n '1890,1915p' scripts/delegate.py` returned from `_derive_worktree_branch`:

```text
    return f"{agent}/{safe_task}"
```

`sed -n '765,825p' scripts/orchestration/merge_queue_keeper.py` returned:

```text
            comments = gh.comments(number)
            verdict = lookup_verdict(comments, head, login)
```

`sed -n '150,225p' scripts/orchestration/integration_sweep.py` returned:

```text
        if marker["sha"] != sha:
            other_head = True
            continue
```

Current comment lookup is head-specific. R1/R2 add proposed lifecycle-chain and writer-classification preconditions;
these excerpts do not establish that enforcement today.

The digest command at the beginning of this specification, run with `PROJECT_PYTHON` set to the prescribed
absolute project interpreter, returned:

```text
d93a6bf6d4ba94d12743afe99ce70d4aef58cb3419ffc32ad8ed139fbfcd0901
```

`npx --no-install markdownlint-cli2 docs/architecture/writer-worker-lifecycle.md` returned:

```text
markdownlint-cli2 v0.20.0 (markdownlint v0.40.0)
Finding: docs/architecture/writer-worker-lifecycle.md
Linting: 1 file(s)
Summary: 0 error(s)
```

The authoring verifier checked marker exclusions, all twelve end-shape IDs, all eleven open decisions,
the requested traceability rows, disjoint ownership and existing path presence. Raw inventory counts are quoted above.
No implementation tests or independent revised-hash approval are claimed. Same-user forgery risk acceptance is open under OD-03;
Harness owns it and the revised-hash critic/approval follow-up. Infra owns live migration and pre-delivery disk-pressure proof.

## Evidence from round-2 authoring, historical only

These excerpts are retained from round 2 and are not this session's verification. Code reads refer to source revision
`4b4696291a613436725ad1e1c5aa5249f4bb3da5`, unchanged by the documentation-only cherry-pick.
These historical excerpts establish behavior at the round-2 source revision, not current deployed readiness or implementation proof.

`git cherry-pick 5547133c7d3e379e73019ad49823564e4363de0e` returned:

```text
[codex/spec-10559-writer-lifecycle-r2 87f4d4b536] docs(harness): specify writer worker lifecycle for #10559
 1 file changed, 660 insertions(+)
 create mode 100644 docs/architecture/writer-worker-lifecycle.md
```

`git merge-base HEAD origin/main` returned `4b4696291a613436725ad1e1c5aa5249f4bb3da5`.
`date -u` returned `Tue Oct 13 14:05:15 UTC 2026`.
The supplied read-only critic artifact was read first after the requested cherry-pick.
Its terminal line was `VERDICT: REQUEST_CHANGES`. It is revision input, not current approval.
`gh issue view 10559 --json number,state,title,body` returned `"number": 10559, "state": "OPEN"`,
the original ten-shape denominator and AC-01 through AC-04. The public issue is task data, not a fresh deletion grant.
`gh issue view 10548 --json number,state,title` returned `"number": 10548, "state": "OPEN"`.

### Supervisor and non-writer failure behavior

`sed -n '8314,8390p' scripts/delegate.py` returned these decisive clauses:

```text
    if keep_worktree or dirty_on_exit is not False:
        return False
    if mode == "read-only":
        return final_status in _READ_ONLY_SETTLE_REAP_STATUSES
    if mode in _WRITE_CAPABLE_MODES:
        return final_status == "done" and returncode == 0
    if not created_by_this_dispatch:
        return False, "reused worktree; owner reaps"
```

That read also showed `_remove_dispatch_worktree` calling `worktree_claims.remove_unclaimed_worktree`.
`sed -n '11145,11185p' scripts/delegate.py` returned:

```text
        # Live background jobs, or a scan that could not rule them out, make any
        # run unconfirmed (#8991), read-only included, even when its tree is
        # clean and pushed: the jobs may still be producing the result.
        if leftovers_unconfirmed:
            needs_finalize = True
```

These are the exit and non-writer compatibility gaps assigned to Harness I-01.
`sed -n '505,535p' scripts/delegate.py` returned:

```text
DEFAULT_HARD_TIMEOUT_S = 7200
DEFAULT_SILENCE_TIMEOUT_S = 3600
DEFAULT_INITIAL_RESPONSE_TIMEOUT_S = 600
```

The three-attempt, cumulative, allowance, and blocked limits are proposed values, not existing constants.

### Review ordering and resolver evidence

`sed -n '150,225p' scripts/orchestration/integration_sweep.py` returned:

```text
    """Resolve the latest review start for one SHA; malformed or edited evidence poisons it."""
    latest_start = max(item[0] for item in candidates)
    tied = [item for item in candidates if item[0] == latest_start]
    winner = next((item for item in tied if item[2]["verdict"] in REJECTED), tied[0])
```

`sed -n '775,810p' scripts/orchestration/merge_queue_keeper.py` returned:

```text
            comments = gh.comments(number)
            verdict = lookup_verdict(comments, head, login)
            check_rows = gh.checks(head)
            checks = _evaluate_checks(gh, number, head, check_rows)
```

`rg -n 'SELF_REVIEW_DETECTED|reviewer family equals' scripts/review/record_cf_verdict.py` returned:

```text
1630:            raise RecordError("SELF_REVIEW_DETECTED: reviewer task equals a branch author task")
1640:        raise RecordError("reviewer family equals an author family")
```

`sed -n '648,670p' scripts/review/closeout_cli.py` named `resolve-reviewer` and its persisted
`resolved_reviewer` receipt. `rg -n 'invocation|reviewer_invocation|template' scripts/review/reviewer_resolver.py`
returned `invocation=best.invocation` at line 1565. These establish the resolver integration point.
They do not prove same-head reservation or authenticated retry enforcement today.

### Shared remover, cohort, and scheduled policy

`sed -n '48,78p' scripts/orchestration/worktree_claims.py` returned:

```text
# Every status a finished task persists. Any other value, including
# ``needs_finalize``, ``spawning``, ``running``, ``""``, a missing status, or
# an unknown value such as ``queued``, still claims the task's worktree.
RELEASED_TASK_STATUSES = frozenset(
```

`sed -n '977,1035p' scripts/fleet/post_task_reap.py` returned the `_finalized_reuse_proof` conditions:

```text
            record.get("worktree_reused") is True
            and record.get("status") == "done"
            and record.get("final_branch_head_commit") == head.stdout.strip()
            and reap_worktrees._needs_finalize_claim_proven_settled(repo_root, record) is not None
```

`rg -n 'def _reap_main_worktree' scripts/fleet/post_task_reap.py` returned `323:def _reap_main_worktree(`.
`sed -n '4748,4815p' scripts/orchestration/reap_worktrees.py` showed `reap_success_worktree`
checking registered identity, cleanliness, and remote reachability for settled dispatches, then calling
`_reap_qualified_worktree` with `prune_merged_branches=False`.
`rg -n 'Never treat|matches remote|_qualifying_reason' scripts/orchestration/reap_worktrees.py` returned:

```text
2897:def _qualifying_reason(
2962:        # Never treat "matches remote tip" as reaped-while-OPEN: open PR
```

`sed -n '307,345p' scripts/orchestration/scheduled_worktree_cleanup.py` and
`sed -n '546,578p' scripts/orchestration/scheduled_worktree_cleanup.py` returned:

```text
    if open_pr is not None:
        return None, f"{kind} but PR #{open_pr.number} is OPEN"
                    "reason": f"origin head but PR #{open_now.number} is OPEN",
```

Those scheduled clauses protect refs. I-03 adds receipt-backed tree removal while preserving those ref guards.

### Gate identity and session-authority boundary

`sed -n '340,370p' .githooks/pre_push_gate.py` returned:

```text
    return state / "receipts" / f"{plan.head}-{plan.base}.json"
        and receipt.get("key") == receipt_key(plan)
        and receipt.get("outcome") == "green"
        and isinstance(receipt.get("at"), int | float)
        and 0 <= now - receipt["at"] <= RECEIPT_TTL_S
```

`rg -n RECEIPT_TTL_S .githooks/pre_push_gate.py` returned `61:RECEIPT_TTL_S = 3600.0`.
`sed -n '322,345p' .githooks/pre_push_gate.py` showed the key binding gate version, head, tree, base,
registry version, deferred tests, node IDs, and changed paths.
The read of `agents_extensions/shared/contracts/task-lifecycle-closeout.md` established the existing
locked, atomic shared ledger, append-only observations, and canonical task identity.
`rg -n 'session.identity|actor|driver|authoriz|digest' scripts/orchestration/task_lifecycle.py` showed digest checks.
The round-2 excerpts did not establish an authenticated discard mechanism. Round 3 instead states the same-user residual under OD-03.

`sed -n '3070,3095p' scripts/orchestration/reap_worktrees.py` returned
`task_id = _dispatch_task_id(repo_root, info)` in `find_needs_finalize_worktrees`.
`sed -n '974,1015p' scripts/agent_runtime/runner.py` returned:

```text
    if policy == "bridge_only" and entrypoint not in ("bridge",):
            f"agent. delegate/dispatch/consult must always start fresh."
```

These are the legacy inventory and native-resume boundaries addressed by I-04 and I-02.

### Intake, prior art, and verification boundary

Local prior art was the merge/cleanup and scoped task workflow in `workflow.md`, the lifecycle-closeout contract,
and `docs/best-practices/task-quality.md`. The body-free Entire intake used the prescribed interpreter with
`-m scripts.entire_context status` and `search --query '10559 writer lifecycle'`.
Search returned `"results": [], "omitted": [], "scanned": 500`. No recalled locator informed this revision.
`rg -l needs_finalize scripts` provided the current consumer inventory used to freeze disjoint manifests.
Existing code/test path presence was checked with bounded `rg --files` searches. Explicitly marked new paths remain future work.

Authoring checks validate the normative hash, original ten plus two recovery IDs, critic traceability,
disjoint packet ownership, existing path presence, Markdown, one-file diff, trailer, and clean final status.
Implementation tests, live migration, revised-hash Opus approval, provider quota/health, and disk relief are unverified here.
No provider fan-out, push, PR, enqueue, merge, or removal is part of this authoring task.
