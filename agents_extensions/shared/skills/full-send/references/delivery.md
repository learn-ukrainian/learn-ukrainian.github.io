# Delivery: hand-off record, proof and the gate

Shared by `full-send` (terminal `merge`) and `full-stop` (terminal `ready`). The landing order
itself stays in `workflow.md` § Merge policy; this file defines what the delivery skills carry
and check.

## Interpreter

Linked dispatch worktrees have no `.venv` of their own. Resolve the primary checkout's
interpreter once per shell, as drive-epic §6 does
([review-merge-cleanup](../../drive-epic/references/review-merge-cleanup.md)), and run every
recipe in the delivery skills with `"$PY"`:

```bash
PRIMARY_REPO="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
PY="$PRIMARY_REPO/.venv/bin/python"
```

## Hand-off record

An entry skill (`takeover`, `modernize`) or a plain brief ends by writing one hand-off record
as a YAML block in its task result. It is the Definition of Ready written down (rules core P3);
it is not a new state store. If a field is missing, the delivery skill fills it from the task
record, issue or PR, or sends the work back to the entry stage. It never guesses a field.

```yaml
handoff:
  target: {kind: pr|branch|issue|task|area, id: "<id>"}
  repository: <owner/name>
  issue_or_brief: "<#N or ordered brief id>"
  authority: "<order or issue that authorizes the work>"
  driver: {name: "<accountable driver>", stream: "epic:<N>"}
  authoring: {task_id: "<id>", run_nonce: "<nonce>"}
  reviewers: [{task_id: "<id>", run_nonce: "<nonce>"}]
  terminal: merge|ready
  base: {ref: main, merge_base: "<sha>"}
  head: {ref: "<branch>", observed: "<sha>"}
  worktree: "<dispatch worktree>"
  scope:
    outcome: "<user-visible outcome>"
    owned_paths: ["<path>"]
    non_goals: ["<non-goal>"]
    denominator: "<what counts as all of it>"
    acceptance: ["<AC-ID>"]
    verify_commands: ["<command>"]
    held_out_proof: "<independent proof the author did not produce>"
  stop_conditions: ["<condition>"]
  residual_owner: "<owner or none>"
  authors: {models: ["<model>"], credit: ["<contributor>"]}
  review:
    catalog_risk: low|medium|high|critical
    profile: code|infra
    budget_tier: default|elevated
    tier_set_by: "<default, open finding id, or operator request>"
    rounds_used: {full: 0, delta: 0}
    ledger: []
  landing_state: {hold: false, queued: false, auto_merge: false}
```

The acceptance ids, typed evidence and behaviour proof live in the lifecycle ledger
(`workflow.md` § Mandatory task workflow, steps 3 to 5); the record names them, it does not
replace them.

**Public-safe subset.** Only these fields go into the PR body: target, acceptance ids and their
proof, catalog risk and budget tier, the finding ledger (including any optional DeepSeek
pre-check dispositions), and credit. Everything else, such as worktree paths, host details and
private task metadata, stays in the task result (rules core P8).

The ledger and budget follow the work: a replacement PR, a new reviewer, a new session or an
accepted successor (`pr_ownership accept`) carries them forward, along with the head's CI rerun
allowance. A handoff never resets a budget.

## Proof

Proof is evidence observed in this session: command output, a reproduction, a run id.

- Reproduce the original failure, apply the fix, then watch the same check pass.
- Run the checks CI runs for the touched area (Ruff, the existing test files that cover the
  changed files). Add no test unless the CTO approved that specific test.
- A user-visible API or UI change needs source-blind behaviour proof on the running artifact
  (`local-code-review` checklist Step 7, drive-epic §7-rollout). Green mocked tests are not
  behaviour proof.
- If the change cannot be proven, it is not ready. Say what is unverified.

## The gate

Every item must hold on the **current** head. A moved head voids the verdict and the CI.

1. Proof covers every change in the diff.
2. A recorded exact-head APPROVE from the reviewer of record (`review-loop`), with no open
   blocker in the ledger. The optional DeepSeek pre-check (DS-PRECHECK-1101) is never a review of
   record and never satisfies or waives this gate.
3. Same-head PR CI Gate green, which includes the affected tests and Frontend, not the full suite. It
   was green **before** the reviewed round started, and it is still green on the live head. PR CI
   never replaces the merge-group CI Gate on the real queue candidate (`workflow.md` § Merge policy).
4. Follow-ups sent to the CTO through Fleet Comms, or recorded on the parent issue when they
   share its outcome. A non-blocking follow-up never holds the merge.
5. The PR is open, not a draft, mergeable and not BEHIND or DIRTY against its base.

`full-send` enqueues after the gate. `full-stop` reports READY_TO_MERGE at the gate; the future
merge-group CI is not yet proven at that point.

## Terminal states

- `full-send`: `MERGED` with a clean closeout receipt, `BLOCKED <reason>`, or
  `QUEUED_UNDER_CUSTODY` after `pr_ownership queue-exit` released the owner. In that case the
  custodian owns `MERGED` and the closeout.
- `full-stop`: exactly one of `READY_TO_MERGE`, `WAITING_ON <named approval>`,
  `BLOCKED <reason>`, `ALREADY_MERGED_EXTERNALLY`, naming the receiving driver.
- Neither skill ends on "Next:". Ready is never reported as delivered.
