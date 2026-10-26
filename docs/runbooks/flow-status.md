# Flow status

Inspect the public repository's issue progress and proved resources:

```bash
.venv/bin/python -m scripts.flow status --issue 11689
.venv/bin/python -m scripts.flow status --lane devops
.venv/bin/python -m scripts.flow status --help
```

Choose exactly one selector. Lane names are the current registered stream keys,
such as `devops` or `infra-harness`. The command prints bounded JSON. Exit 0
means a report was produced, including any explicit unknowns. Exit 1 means a
source, selection, or output refusal prevented the report. Argument errors exit 2.
No selector has an implicit default.

The command reads existing native task records, the lifecycle ledger, Git,
GitHub, common-reaper journal, the registered membership cache, and local Work
API projections. It creates no inventory or state store. It never runs a
provider, changes issues, signals processes, resumes tasks, renews leases, or
invokes cleanup. GitHub reads use the existing client with an in-memory cache;
Git reads use the execution-safe inventory reader. Network requests are confined
to the canonical public repository's GitHub reads, GitHub's authenticated-user
identity read, and fixed loopback Monitor reads. GraphQL is restricted to the
existing queue-status query. No private-repository lookup is available.

## Reading the report

Each issue has a state, its evidence source, a source timestamp when available,
age, accountable lane driver, next actor/action, flags with reasons, current and
reviewed SHA, CI status, missing evidence, and six resource lists. `observed_at`
is the report observation time. It is never substituted for a transition time.
Issue creation time is never substituted for age in the current state.

| State | Affirmative evidence |
| --- | --- |
| Created | An initial GitHub issue observation with no later phase evidence; state age remains unknown |
| Ready | A native admitted dispatch is spawning and its recorded DoR verdict is PASS |
| In progress | An owned author is running with a matching process identity |
| In review | An owned reviewer is running against the current PR head |
| Fixing | Current-head material changes were requested |
| Testing | Current-head review passed and required same-head checks are pending |
| Queued | A current-head live merge queue entry exists |
| Merged | GitHub says the associated PRs merged |
| Cleaned | Terminal native attempts match common-reaper evidence and all inventoried branch, worktree and temp resources are proved absent |

An open PR alone does not identify the current phase. Conflicting simultaneous
phases yield `unknown` with the competing evidence named. Native `done` never
means delivered. Merged work with a running owned task explicitly reports that
conflict and retains the authoritative Merged observation.

Review of record uses the existing integration-sweep verifier, including its
shared-identity, unedited-comment and exact-head requirements. A moved head
invalidates the previous approval. A native GitHub review alone cannot certify
the independent review gate. Required checks come from the existing lifecycle
contract or the integration sweep's existing check list. Cancelled CI fails;
absent checks or an incomplete check listing are unknown.

An overdue flag uses only an outstanding acceptance item's existing recognized
post-merge owner and calendar deadline. Without that contract, overdue is
unknown and the report says why. A state without a transition timestamp has
unknown age. The command introduces no age-based SLA.

## Ownership and incomplete coverage

Task ownership requires a canonical public-repository identity and the native
DoR issue association or validated lifecycle carrier. A branch prefix, task-name
suffix, issue citation in a prompt, or an empty dashboard does not prove ownership.
The task list includes full run nonces, including archived attempts. Branch
references include stable opaque IDs; unsafe references are opaque throughout.
Local and live remote presence are separate.
Worktree and temp paths inside the repository are relative. Outside paths are
opaque resource IDs. Prompt/result bodies, issue text, review prose, raw errors,
process identifiers, account details and host paths never appear in output.

Per-class `coverage` explains missing inventories, unreadable records, missing
temp bindings, failed listings and output truncation. A foreign task is excluded;
unclassified or unlinked public records keep coverage incomplete. The command
does not claim unproved resources. It retains a dirty worktree and reports it.
Missing branch or worktree bindings also keep resource coverage incomplete.
The Work projection supplies bounded supplementary locators. Registered native
membership and task records take precedence over its omissions.

The existing reaper journal and merged-reuse proof must match the terminal task,
full nonce, worktree, branch, PR and head before Cleaned is possible. Branch
absence alone is insufficient. Missing receipt history or an unrecorded attempt
binding keeps cleanup unproved. Cleaned describes resource evidence; the driver
still owns the complete delivery denominator and merged behavior proof.

Output admits at most 50 issues and 50 rows per resource class, with a 128 KiB
final ceiling. Task/journal scans stop at 10,000 records. Individual remote
responses stop at 1 MiB and GitHub lists at ten pages. GitHub/Git reads share a
60-second budget. Every exhausted bound is reported as incomplete; a complete
empty inventory is never inferred from a partial list.

## Custody

This command implements the read-only piece of C2492. `codex-devops` owns its
independent held-out evaluation, exact-head non-OpenAI review, same-head CI,
normal merge queue, merged CLI proof and common cleanup. The author cannot
certify those gates. Any residual remains open with that driver.

C2480 pane wakes, the separate C2492 ten-minute zombie watcher, deployment and
timers, automated cleanup/closing, new persistent inventory, and rule changes
remain separate driver-owned work.

See [task quality](../best-practices/task-quality.md),
[worktree cleanup](worktree-cleanup.md), and
[the lifecycle closeout contract](../../agents_extensions/shared/contracts/task-lifecycle-closeout.md).
