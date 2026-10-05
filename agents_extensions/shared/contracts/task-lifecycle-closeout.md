# Task lifecycle and GitHub closeout contract

`task-lifecycle.v1` is the fleet-wide, provider-neutral state and evidence
contract for non-trivial coding work. It wraps the canonical
`task-identity.v1` envelope; it never replaces or weakens that identity.

The implementation is `scripts/orchestration/task_lifecycle.py`. The operator
entry point is:

```bash
.venv/bin/python -m scripts.orchestration.task_closeout --help
```

## Authority and storage

- GitHub is authoritative for repository, issue, native parent epic, PR,
  reviews, requested changes, checks, merge, deployments, comments, and issue
  state.
- Git and the filesystem are authoritative for the primary checkout,
  dispatch worktree, commits, trailers, changed paths, branches, and cleanup.
- The lifecycle ledger is an append-only projection of those observations. It
  cannot overwrite contradictory authority facts.
- Runtime ledgers live below the primary checkout's shared Git directory at
  `.agent/task-lifecycle/<repository-digest>/issue-<number>.json`. The exact
  `task-identity.v1` repository and issue deterministically locate the same
  ledger after delegation, worktree changes, process crashes, or rollover.
- Writes are locked and atomic. Replaying an identical observation returns the
  existing receipt and performs no mutation.

## States and terminal goals

The lifecycle projection uses these typed states:

`ISSUE_LINKED` → `ACS_FINALIZED` → `IMPLEMENTATION_READY` → `PR_OPEN` →
`REVIEW_REQUESTED` / `CHANGES_REQUESTED` → `REVIEW_PASSED` → `CI_PASSED` →
`MERGED` → optional `DEPLOYED` → optional `CERTIFIED` → `ISSUE_CLOSED` →
`CLEANED_UP`.

`BLOCKED_WITH_RECEIPT` is a recoverable fail-closed disposition for a material
identity, evidence, review, check, scope, mutation, or cleanup failure. Every
new observation receipt names the author-family owner and next action. Ordinary
review/check waiting remains an actionable nonterminal state and is not called
blocked.

Terminal goals remain distinct:

- `merge` requires verified merge, issue closure, and cleanup;
- `deploy` additionally requires a successful deployment bound to the merge;
- `certify` additionally requires typed certification evidence bound to the
  deployment/merge.

## Acceptance criteria and evidence

Issue acceptance criteria use stable operator-visible IDs:

```markdown
- [ ] **AC-01** — A concrete, verifiable requirement.
```

Initialization snapshots the ID, canonical text, applicability, due state,
and required typed evidence. A SHA-256 hash covers the ordered canonical
snapshot. Reconciliation fails closed for missing, duplicate, reordered,
removed, or text-drifted criteria. A checked box is a display projection, not
proof.

Every evidence record binds to the exact repository, issue, PR, and current PR
head. Its type, summary, URL (when applicable), digest, timestamp, and optional
details remain immutable. Review evidence additionally records author family,
outside reviewer family, verdict, and reviewed commit. The referenced review
receipt must exist in either the authoritative PR conversation comments or the
native pull-request reviews endpoint, and requested changes must be absent on
the current head.

A replacement evidence row may declare `details.supersedes_evidence_ids` with
exact prior evidence IDs. Each ID must already exist and bind to the same AC,
kind, repository, issue and PR. The old rows remain immutable. Reconciliation
suppresses their blockers only when the replacement itself passes all validators
on the current PR head. A moved head, invalid replacement, cross-AC/kind link,
or unsuperseded old row still refuses; a newer timestamp alone replaces nothing.

An AC policy marks a user-visible criterion with
`behavior_proof_required: true` and includes the typed `behavior_proof`
evidence requirement. That evidence never copies a prose status. Its
`details.behavior_proof_receipt` references the canonical #5302
`code-review-receipt.v1` JSON by absolute path and SHA-256 digest, records the
receipt's target-input fingerprint, and binds the receipt's exact target SHA to
the evidence subject/current PR head. Reconciliation reads the receipt and
requires a clean outside-family closeout plus its target-bound
`behavior-proof.v1` source-aware/source-blind surfaces. Prefer a shared
`.agent/review-closeout/` receipt path so rollover and worktree cleanup do not
discard the proof.

An eligible quick fix (`workflow.md` § Quick-fix path) records typed
`quick_fix` evidence instead of a model review. Its
`details.quick_fix_receipt` has the same four-field reference shape and points
to a `quick-fix-receipt.v1` written by `scripts.review.quick_fix record`; its
URL names the PR comment declaring the quick fix with the receipt digest and
head SHA. Reconciliation rereads the receipt and refuses a moved head, digest
or changed-path drift, a missing declaration, a passing reproduction, a failing
regression, an author acting as driver, an incomplete exclusion set, an
authority path, or a security-sensitive path without the driver's rationale.
A valid `quick_fix` record satisfies that criterion's `review` and
`behavior_proof` requirements only; CI and every other evidence type still bind.

Evidence due at `ISSUE_CLOSED` or `CLEANED_UP` may be derived from the
post-action authoritative observation. This permits truthful staged closeout
without pretending issue closure or cleanup happened before it did. The task is
not terminal until those post-action criteria are also evidenced and checked.

## Authoring provenance after cleanup

Current worktree presence remains a filesystem observation. For a merged PR
whose authoring tree has been reaped, reconciliation may verify the original
canonical dispatcher record and result sidecar using the existing hot/archive
record locator. It requires exact lifecycle identity, task, repository, owned
dispatch path and branch; terminal `done`, clean exit, no finalization/rescue
failure, positive commit count, and the dispatcher's clean common-reaper result.
The original result bytes must match the recorded SHA-256. Git must prove the
recorded base/author-head ancestry, commit count, owned paths and exact task
X-Agent trailers; authoritative publisher PR commits must include both the
recorded author head and current PR head. Result prose grants no authority.
Missing, contradictory or digest-mismatched artifacts refuse.

This observation exposes `dispatcher_provenance` with original record/result
paths and digests, task, author/current heads and original dispatch path. It
never changes `worktree_present` to true or backdates the observation. New
post-dispatch author changes require their own evidence; only verified unchanged
GitHub base updates may connect the recorded author head to the PR head.

A trailerless base update is exempt only with publisher commit data identifying
GitHub's `web-flow` committer, a valid verified signature matching the local
commit's signature/payload, the exact main-into-dispatch-branch message, and two
locally matching parents/tree. The existing isolated clean-base-merge verifier
must reproduce that tree without conflicts and prove the second parent belongs
to the authoritative PR base. The observation records source, commit digest,
parents and tree in `github_base_update`. Ordinary, edited, unsigned,
unverified or contradictory merge commits still require X-Agent attribution.
This provenance check grants no review clearance; standard independent review
and quick-fix qualification refusals remain binding.

## Reconciliation and mutation

`reconcile` is read-only. It observes GitHub and local Git, validates identity,
AC drift/evidence, stream membership, review independence, checks, terminal
goal, remaining scope, and cleanup, then emits a durable receipt plus a concise
disposition.

Remote mutation requires both an explicit action and `--authorize`. Supported
actions are deliberately narrow:

- `sync-acs`: check only criteria whose evidence is currently valid;
- `arm-auto-merge`: require current-head outside-family review, clean local
  readiness, and no material blocker before arming squash auto-merge;
- `close-issue`: require the terminal goal's remote result, no untransferred
  remaining scope, and every pre-close criterion evidenced and checked.

Each action persists an intent before the remote call and performs authoritative
readback afterward. If the process crashes after GitHub succeeds but before the
local result receipt, retry observes the desired remote state, records recovery,
and does not repeat the mutation. A missing `--authorize`, a rejected mutation
gate, or a failed remote call writes a durable `BLOCKED_WITH_RECEIPT` mutation
event with the actor, reason, and recovery instruction without broadening the
allowed mutation surface.

Auto-close keywords (`Fixes #N`) are intent only. They never count as proof.
Post-merge reconciliation reads the real issue state; premature or failed close
is `BLOCKED_WITH_RECEIPT` with an owner, reason, evidence, and next action.

## Remaining scope

`remaining_scope.status` is one of `none`, `open`, or `transferred`.

- `open` always blocks closure.
- `transferred` requires the follow-up issue, exactly one registered parent
  stream epic, explicit transferred scope/evidence, and reciprocal issue links.
- The original AC snapshot may change only through an explicit new snapshot
  version; prior hashes and receipts remain immutable.

## Git and review gates

Readiness requires a dispatch worktree, a clean primary checkout, valid
`X-Agent` trailers on every task commit, no protected/generated artifacts, a
current-head independent outside-author-family review (or a verified
`quick_fix` receipt for an eligible quick fix), no unresolved requested
changes, and passing required checks. Auto-merge must not predate the verified
review receipt and cannot be armed for a draft PR.

The claimed dispatch worktree must exist in `git worktree list --porcelain`,
must use the required dispatch subtree, and its Git-recorded branch must match
the expected PR head branch. A caller-provided path or branch string is never
accepted as proof by itself.

Completion requires the PR's terminal state, actual issue closure, removal of
the exact dispatch worktree, and absence of both local and remote task branches.
An open/draft PR is nonterminal unless a durable blocker names the owner and next
action.

## Fleet carriers

The validated carrier contains the full task identity and AC snapshot, terminal
goal, PR binding, remaining scope, current projection, ledger path, and latest
receipt digest. `delegate.py`, the agent ledger, and orchestrator run/inbox state
carry this exact projection. Monitor coordination endpoints expose agent-ledger
records unchanged.

Rollover does not copy or fork lifecycle truth. The replacement's
`task-identity.v1` envelope deterministically locates the same shared ledger,
then validates the carrier before resuming. Harnesses therefore share one
contract even when native title or task APIs differ.

Legacy lifecycle data is migrated to an explicit `migration` record without
rewriting evidence or receipt history. A legacy terminal goal of `unknown`
cannot enter implementation readiness.
