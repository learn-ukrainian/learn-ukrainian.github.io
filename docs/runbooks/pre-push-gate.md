# Pre-push gate (#10033)

`.githooks/pre-push` runs `.githooks/pre_push_gate.py` on the exact outgoing commit before any push
leaves a checkout. Worker `git push` and the auto-finalize push (`scripts/delegate.py`) both go through
it. Install and repair the hook chain with `scripts/install_git_hooks.sh`.

## What it checks

For each pushed branch (deletes and tags are skipped), with `HEAD` equal to the pushed commit and no
tracked changes:

1. `pre-commit run --hook-stage pre-push --from-ref <base> --to-ref <head>` over the outgoing range.
   `<base>` is the remote tip when it is an ancestor, else the merge-base with `origin/main`.
   The same bounded stage then always runs `lint_opsec_leaks.py --commit-range <base>..<head>`.
   It reads each commit's version of its touched files, including values later reverted or files
   later deleted. Missing selected blobs refuse the push; diagnostics omit matched values.
   It also runs the existing `check-no-internal-ids` hook explicitly with `--hook-stage pre-commit`
   and the same `--from-ref`/`--to-ref` pair. This preserves that hook's exact learner-surface
   file filter and detection rules while enforcing it during the push gate.
2. The invariant registry: `KNOWN_REPO_WIDE_MODULES` and `KNOWN_REPO_WIDE_FUNCTIONS` in
   `tests/test_repo_wide_marker_invariant.py`, read by AST and deduplicated (a function id is dropped
   when its whole file is selected). Its version is a digest of the gate version and the ids.
3. Test files the range adds or changes (`tests/**/test_*.py`).

Stages 2 and 3 run as one pytest process. Importer-closure selection
(`scripts/ci/pre_push_shadow.py`) runs beside them in shadow: recorded, never blocking.

## Outcomes

| Outcome | Exit | Meaning |
| --- | --- | --- |
| green | 0 | Push proceeds; a receipt is written. |
| `pre_commit_failed`, `tests_failed` | 1 | Push refused; failing hook names or pytest node ids are listed. |
| `tree_mismatch`, `dirty_tree`, `range_unresolved`, `invalid_ref_updates` | 1 | The exact commit cannot be validated as pushed. |
| `untracked_inputs` | 1 | Untracked or ignored `*.py`, `*.pth` or pytest/tox/setup/pyproject config files exist; they could change the run but not the receipt. Commit or remove them. |
| `validation_incomplete` | 75 | Not validated and not green: `invalid_configuration`, `admission_timeout`, `timeout`, `registry_unavailable`, `pytest_error` (pytest exited without a verdict), `changed_tests_unmaterialized` (a test file the range changes is absent from a sparse worktree; `git sparse-checkout add tests`). The branch is preserved; return to the driver. Never retry blindly. |

The last stderr line before the bypass hint is machine-readable: `{"pre_push_gate": {...}}`.

## Bounds

Admission defaults to one gate per repository (lock under the Git common dir). The admission wait and one run
budget are shared by every ref update of the push; their limits are the constants in `.githooks/pre_push_gate.py`.
Each update is validated with its own base. Command output goes to a file, and after every command the gate
kills any descendant that inherited its run token within a short cleanup bound, so a detached child cannot
stall or outlive the gate. `LU_PRE_PUSH_GATE_ADMISSION_WAIT_S` and `LU_PRE_PUSH_GATE_RUN_BUDGET_S` can only
shorten these.

Before joining the global queue, a caller joins a FIFO queue for its immutable outgoing head under
`<git-common-dir>/lu-pre-push-gate/heads/<head>/`. Only that head's holder registers a global ticket.
Followers wait outside the global queue, rebuild their inputs after waiting, and reuse only a fresh
green receipt matching the complete existing receipt key. The head groups serialization; different
bases, registry versions, selected nodes or other key fields still require their own checks.
Both waits share the original admission start time and hard ceiling. While blocked, a head follower's
allowance grows with its head predecessors plus the flock-live global queue depth, so it accounts
for the holder's global wait and validation. Stale or unsafe global tickets do not grow this allowance.
The allowance never shrinks as tickets leave. If no reusable green receipt exists after coalescing,
the global queue's position-based allowance starts at that transition; elapsed coalescing time still
counts toward the original total hard ceiling. Execution starts after global admission; waiting does
not consume the shared run budget.

Live tickets in either queue are locked before atomic publication. Their JSON contains exactly
`head` (the outgoing SHA from Git's update), `branch` (its frozen local ref), and `task_owner` (the explicit
`LEARN_UKRAINIAN_DISPATCH_TASK_ID`, captured before waiting). The task label must be 1–128 ASCII
letters, digits, underscores, dots or hyphens and start with a letter or digit. Missing or invalid
labels become `unknown`. No other environment fields or remote identity are written.
For native `git push -u origin HEAD`, Git can supply literal `HEAD` as the local ref. Before either
queue wait, the gate resolves it with `git symbolic-ref --quiet HEAD` and verifies that the exact
`refs/heads/...` ref names the outgoing SHA with `git show-ref --verify --hash`. A detached,
unresolvable or SHA-mismatched `HEAD` records `branch: unknown`; another branch at the same SHA
does not establish ownership. Direct refs and other literal revision expressions remain unchanged.
The same frozen metadata passes from the head queue to the global queue even if the checkout moves.
This observation never authorizes validation: the existing exact-SHA and input checks after both
waits still refuse changed validation inputs.
Ticket contents never prove liveness: flock remains the authority, including for legacy empty
tickets and older holders with no ticket metadata.

A refused attempt terminates. Incomplete or interrupted callers release their queue resources;
abandoned tickets are reaped through the existing flock checks. An explicit owner resubmission gets
a new tail ticket. The gate never retries an attempt automatically. Stable lock files remain for
safe rendezvous; each run releases its own tickets and private test directory. Shared or scoped runs,
and runs without proven exclusivity, preserve other runs' directories, including those left by a killed caller.

`LU_PRE_PUSH_GATE_MAX_TEST_PROCESSES` sets the test process ceiling as a positive integer.
The default is 4, so callers get bounded parallel validation without an override. Serial validation
consumed the shared run budget. A nonblank `LEARN_UKRAINIAN_DISPATCH_TASK_ID` caps the invocation
at 2 processes, matching the existing dispatch pytest plugin. An explicit positive integer override
is still supported; invalid values refuse validation, including receipt reuse. Parallel execution
requires xdist. Without xdist, execution is serial.

The pytest stage runs the planned node ids in two pytest invocations that share the stage deadline
(#10610). Changed test files run first with `--dist worksteal`, as CI runs them, so one slow changed
file is spread over the workers instead of setting a one-worker floor. The registered invariant nodes
then run with `--dist loadfile`, which keeps their files whole. Each invocation gets its own private
base temp. The first refusal ends the stage, and a green stage and receipt require both invocations to
pass. One invocation collecting no tests is accepted only when the other ran tests. The receipt keeps
the single plan node list, which covers both invocations.

## Experimental concurrent admission (#10555)

`LU_PRE_PUSH_GATE_MAX_CONCURRENT_RUNS` accepts exactly `1` or `2`. Unset means `1`.
Other values produce `invalid_configuration`, including when a receipt could be reused.
The experiment is opt-in and does not enable a permanent rollout.

The second reservation requires fresh admission observations: `load_1m < 12` and
`mem_available_bytes >= 8589934592`. Missing, nonnumeric, or inadequate observations retain serial
admission. The concurrent mode also requires an effective per-run test process count at most 4.
It preserves the configured count and the ordinary dispatch clamp described above.

The gate starts its own `systemd-run --user --scope` executor with `MemoryMax=6G` and verifies the
actual cgroup-v2 memory limit and peak interface before starting any check. The executor inherits
the head and global flock descriptors. These reservations remain held if the launching gate exits
while scoped validation continues. Every blocking stage and the shadow run execute inside that scope.
No check runs during scope setup. A missing user bus or refused setup falls back to the complete
serial path. Failure after checks start is incomplete, with no repeated stage or automatic retry.
Cleanup addresses only the run's generated unit and descendants. Scoped receipt publication follows
verified cleanup. If descendants cannot be verified as settled, the executor retains its inherited
reservations for own-unit cleanup and driver disposition; it never promotes an orphaned owner.

The serial pytest stage restores the stale `pytest-*` sweep only while its run holds the exclusive
Git-common admission lock. That lock excludes live shared holders and any surviving scoped executor.
A later exclusive serial run may reap directories left by a dead run.
Shared/scoped execution or unknown exclusivity skips the sweep and records
`stale_pytest_cleanup=skipped_shared_or_unknown` in stage diagnostics. Every run still removes its
own pytest temporary directory. Sweep failures refuse the push as incomplete.

Tests that assert the exclusive sweep or inject failures into in-process serial stages pin
`LU_PRE_PUSH_GATE_MAX_CONCURRENT_RUNS=1` with `monkeypatch`. This keeps their assertions valid
when the invoking push uses two slots. Startup I/O fault injection and the non-green leader/follower
test also pin serial admission, where interrupting the leader ends its validation stages before
the follower checks for a reusable receipt. The existing shared-mode stale-sweep test still verifies
that shared execution preserves other runs' temporary directories.

Scoped executors share the existing `admission.lock`; legacy and default callers keep its exclusive
flock. A flock-live ticket, a separate launcher flock, and verified scoped-holder proof permit sharing.
The launcher flock is never inherited by the executor. A dead launcher therefore prevents a second
reservation while its scoped work retains the head and global locks. Empty, legacy, default,
unscoped, or unknown predecessors prevent a second reservation. The queue remains FIFO: a serial
waiter cannot be skipped. The gate checks the kernel lock inventory for an earlier ticketless
exclusive waiter before sharing. Missing or incompatible inode-backed lock evidence retains exclusive
admission. The separate `sharing.lock` serializes scoped admission transitions under
the same Git-common authority. It adds no stream lease or external coordination service.

## Receipts

`<git-common-dir>/lu-pre-push-gate/receipts/<head>-<base>.json` lets a retry of the same commit skip the run. It is
bound to the commit, tree, base, registry version, selected ids and gate version, expires after one hour, and
is ignored when any of them differ or the tree is dirty.
Rebuilding the plan also rejects untracked validation inputs after either wait. A missing or unsafe
immutable identity cannot authorize reuse.

## Measurement (AC-05)

Each attempt appends a durable `BEGIN` row before validation and a `TERMINAL` row for its typed outcome to `<git-common-dir>/lu-pre-push-gate/measurements.jsonl`: outcome, reason, failing
ids, admission wait, duration, registry version and the shadow selection. Join with first-attempt CI outcome
per PR head for the before/after report.
`admission_wait_s` includes both waits; `coalescing_wait_s` records the head queue wait separately.
`queue_depth` and `queue_position` describe the global queue only. A follower that reuses a receipt
before global admission records zero for both, with detail `valid receipt after coalescing`.
Both rows carry a generated `attempt_id`, `measurement_schema` independent of the validation receipt
version, and SHA-256 fingerprints of the source, registry, selector, launcher, configuration, and stdin.
Missing fingerprint inputs are null, never inferred. The terminal row adds the complete validation-plan
fingerprint when available. Attribution uses the attempt identity and immutable inputs; a missing task
owner remains `unknown` and does not set a dispatch marker.

Catchable SIGINT and SIGTERM produce incomplete terminal rows after cleanup. SIGKILL or a crash can
leave an unpaired BEGIN. That attempt stays incomplete/unknown in the denominator; absence never
proves green. Appends hold an exclusive journal flock through complete writes and file/directory
fsync. Catchable signals are deferred through each complete durable append. A signal at terminal
publication can follow an already committed terminal row; a final incomplete row preserves the
interruption with `measurement_unknown_reason: interrupted_terminal_append`. Multiple terminal rows
for one attempt invalidate comparison evidence and never count as a green sample. A failed write emits `measurement_unavailable`; durability is unknown and the attempt cannot
supply accepted comparison evidence. Failure to persist BEGIN refuses validation before any check.
Failure to persist a green terminal observation returns incomplete; existing negative validation
verdicts remain negative. These storage failures never invent a durable observation.

The row's `stages` object contains `pre_commit` and `pytest` only when each stage is entered.
`queue_wait_s` excludes the run's `scope_setup_s` from total admission time. `execution_s` records
attempt time excluding admission; the existing `duration_s` remains the total push observation.
`resources_at_admission` contains fresh admission observations or explicit nulls.
The top-level requested/effective test process fields remain null when no count was observed.
`peak_memory_bytes` comes from the scope's `memory.peak`, read by the scoped executor before it exits.
It covers the scope and its descendants, never a point sample. Serial runs and failed peak reads
record null and `peak_memory_unknown_reason`. Unknown measurements do not establish resource bounds,
valid comparison evidence, or a throughput improvement. Supported-bus production-entry evidence
and independent held-out review remain necessary; injected scope tests do not certify the runtime.

Each entry records `elapsed_s` from a monotonic clock, `outcome` and `reason`. Stage time includes
stage setup, command execution and cleanup; admission wait remains in `admission_wait_s`.
An earlier successful entry survives a later failure. Receipt reuse creates no stage entries.

The pytest stage records `requested_test_processes` (the configured ceiling) and
`effective_test_processes` (the count passed to pytest after the dispatch cap or serial fallback).
The effective count is 1 for serial execution. These fields describe the invocation; the child status
fields below distinguish a command that starts from one that never starts. They remain in the
measurement row on failure or timeout. Receipt reuse has no new process-count observation.

Each stage also records the observed signed child `returncode`, its positive `signal` when terminated
by a signal, and `output_tail`. The tail contains at most the last 40 lines from the final 8192 output
bytes, decoded as UTF-8 with replacement. Timeout cleanup captures these fields before closing the
output file. A child that never starts or whose exit cannot be observed has null status fields and a
`child_unavailable_reason`, such as `budget_exhausted_before_start`, `spawn_error` or `exit_unobserved`.
A stage that does not start a command records `stage_did_not_start_child`. An unavailable output file
leaves `output_tail` null; a failed tail read adds `output_unavailable_reason`.

These measurements are private diagnostics and may contain sensitive command output. Keep raw rows
in ignored local state; use synthetic output for public examples and tests. Diagnostic write or
serialization failures cannot authorize a refused or incomplete push. Stage evidence does not change
test selection, gate outcomes, execution bounds or receipt validity.

## Merge-main rule

Merge `origin/main` into a worker branch only when `git merge-tree` against a freshly fetched main SHA reports
a conflict, when the driver disposes on base/head/combined-tree evidence that the branch is incompatible with
the base, or on driver order. A merge-tree error is unknown, not a conflict. Every new head needs renewed
approval and CI; merge-group CI stays the authority for semantic combinations.

## Bypass

`git push --no-verify` is the explicit operator bypass; the rescue path in `scripts/delegate.py` uses it
deliberately. Agent sessions must not.
