# Pre-push gate (#10033)

`.githooks/pre-push` runs `.githooks/pre_push_gate.py` on the exact outgoing commit before any push
leaves a checkout. Worker `git push` and the auto-finalize push (`scripts/delegate.py`) both go through
it. Install and repair the hook chain with `scripts/install_git_hooks.sh`.

## What it checks

For each pushed branch (deletes and tags are skipped), with `HEAD` equal to the pushed commit and no
tracked changes:

1. `pre-commit run --hook-stage pre-push --from-ref <base> --to-ref <head>` over the outgoing range.
   `<base>` is the remote tip when it is an ancestor, else the merge-base with `origin/main`.
   One exception applies to the ancestor case (#10820): when the head merged newer `origin/main` into an
   older remote tip, `<remote>..<head>` also carries main's own commits. The base is then the merge-base
   with `origin/main`, so the range is the change the pull request carries (`origin/main...<head>`). The
   rule narrows only on Git's positive answer: `git merge-base --all origin/main <head>` returns exactly
   one commit other than `<head>`, and `git merge-base --is-ancestor` exits 1 for it against the remote
   tip. A plain fast-forward keeps `<remote>..<head>`, which lies inside `<merge-base>..<head>`; new
   branches and divergent tips start at the merge-base. Either way the range holds only the branch's own
   commits, never main's (#11207).
   When no single merge-base other than `<head>` can be proven, the base stays the previous one (the
   remote tip, or Git's single `merge-base` answer for a new or divergent tip), so the scans cover the
   complete outgoing range, and the gate records the cause as `base_fallback`: `merge_base_unavailable`
   (no `origin/main`, a shallow clone, no common history or a Git error), `merge_base_ambiguous` (several
   merge-bases), `merge_base_unproven` (the `is-ancestor` check failed) or `merge_base_is_head`
   (`origin/main` already contains the head). The last still runs: the update moves the remote, so its
   checks run over `<remote>..<head>`, and it is never accepted as "no outgoing commits". Only a remote tip equal to the head has no outgoing
   commits. A new or divergent tip with no merge-base at all is `range_unresolved`.
   The same bounded stage then always runs `lint_opsec_leaks.py --commit-range <base>..<head>`.
   It reads each commit's version of its touched files, including values later reverted or files
   later deleted. Missing selected blobs refuse the push; diagnostics omit matched values.
   It also runs the existing `check-no-internal-ids` hook explicitly with `--hook-stage pre-commit`
   and the same `--from-ref`/`--to-ref` pair. This preserves that hook's exact learner-surface
   file filter and detection rules while enforcing it during the push gate.

Those are the gate's checks. Before them it refuses a dirty tracked tree and untracked or ignored files
that could change what the hooks import (`untracked_inputs`, below). The pre-commit stage runs every
hook `.pre-commit-config.yaml` places at the `pre-push` stage, unchanged, including the secret scans.

**The gate runs no tests of its own (#11276).** It has no pytest stage, takes no host test slots and
runs no affected-test selector. The pytest-based guard hooks the configuration places at the `pre-push`
stage are part of the pre-commit stage and are unchanged. CI Gate runs the full suite on every pull
request and again in the merge queue, and remains the merge gate; the nightly slow run stays advisory.
A green pre-push is never evidence that the suite passes. Run the tests your change touches yourself
before pushing, as the rules require.

## Outcomes

| Outcome | Exit | Meaning |
| --- | --- | --- |
| green | 0 | Push proceeds; a receipt is written. |
| `pre_commit_failed` | 1 | Push refused; the failing hook names are listed (`lint-opsec-leaks` for the per-commit OPSEC scan, `check-no-internal-ids` for the internal-ID scan). |
| `tree_mismatch`, `dirty_tree`, `range_unresolved`, `invalid_ref_updates` | 1 | The exact commit cannot be validated as pushed. |
| `untracked_inputs` | 1 | Untracked or ignored `*.py`, `*.pth` or pytest/tox/setup/pyproject config files exist; they could change what the hooks import, but not the receipt. Commit or remove them. |
| `validation_incomplete` | 75 | Not validated and not green: `invalid_configuration`, `admission_timeout`, `timeout` and `timeout_under_load` (a stage reached its bound; see Bounds), `receipt_unwritable`, `validation_error` (an I/O failure), `scope_setup_unavailable` (the scoped executor was never set up or is already closed; no check ran). The branch is preserved; return to the driver. Never retry blindly. |

The last stderr line before the bypass hint is machine-readable: `{"pre_push_gate": {...}}`.
After a plan is built, every `validation_incomplete` detail ends with the range it scanned (#10820), for
example `range: <base>..<head>`, or `range: <base> (merge_base_ambiguous)..<head>` with a base fallback,
so a timeout from an oversized range is recognisable.

## Bounds

Admission defaults to one gate per repository (lock under the Git common dir). Execution has two time
bounds (#10642), both constants in `.githooks/pre_push_gate.py`, unchanged by #11276:

- The blocking pre-commit stage has its own allowance (`STAGE_BUDGET_S`) counted from its start.
- The run budget (`RUN_BUDGET_S`, two allowances) caps total stage execution. It starts at global
  admission and is shared by every ref update of the push. A stage whose own allowance would outlast
  the remaining total stops at the total instead.

A command that reaches its stage's bound is killed with its descendants. The push is then
`validation_incomplete`, and no receipt is written. Each update is validated with its own base.
The reason is typed by the host load observed at the timeout, just before the kill (#11140), using the
admission caps (`CPU_SOME_AVG10_MAX`, `CPU_SOME_AVG60_MAX`, 8 GiB available memory):
`timeout_under_load` when the observation is above a cap, `timeout` when it is below every cap or
could not be read. The stage row records `load_at_timeout` (the three values and `load`:
`above_caps`, `below_caps` or `unknown`). High observed load is evidence, not proof of cause, and
neither reason is green or retried automatically.

Command output goes to a file, and after every command the gate kills any descendant that inherited its run
token within a short cleanup bound, so a detached child cannot stall or outlive the gate.
`LU_PRE_PUSH_GATE_ADMISSION_WAIT_S`, `LU_PRE_PUSH_GATE_STAGE_BUDGET_S` and `LU_PRE_PUSH_GATE_RUN_BUDGET_S`
can only shorten these.

One predecessor's admission allowance (`ADMISSION_WAIT_S`) covers one complete run of gate version 11,
which also waited for host test slots and its selector: checkouts that still run it share this queue
(one Git common directory), so the allowance keeps that length until none does (#11276). The hard
admission ceiling is ten of these. The auto-finalize push timeout in `scripts/delegate.py` reads both
values from the gate.

Before joining the global queue, a caller joins a FIFO queue for its immutable outgoing head under
`<git-common-dir>/lu-pre-push-gate/heads/<head>/`. Only that head's holder registers a global ticket.
Followers wait outside the global queue, rebuild their inputs after waiting, and reuse only a fresh
green receipt matching the complete existing receipt key. The head groups serialization; different
bases, tool versions or other key fields still require their own checks.
Both waits share the original admission start time and hard ceiling. While blocked, a head follower's
allowance grows with its head predecessors plus the flock-live global queue depth, so it accounts
for the holder's global wait and validation. Stale or unsafe global tickets do not grow this allowance.
The allowance never shrinks as tickets leave. If no reusable green receipt exists after coalescing,
the global queue's position-based allowance starts at that transition; elapsed coalescing time still
counts toward the original total hard ceiling. Execution starts after global admission; waiting consumes
neither a stage allowance nor the run budget.

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
safe rendezvous; each run releases its own tickets.

Admission, queue, receipt and measurement files stay under `<git-common-dir>/lu-pre-push-gate/`.

## Experimental concurrent admission (#10555)

`LU_PRE_PUSH_GATE_MAX_CONCURRENT_RUNS` accepts exactly `1` or `2`. Unset means `1`.
Other values produce `invalid_configuration`, including when a receipt could be reused.
The experiment is opt-in and does not enable a permanent rollout.

The second reservation requires fresh admission observations: `load_1m < 12` and
`mem_available_bytes >= 8589934592`. Missing, nonnumeric, or inadequate observations retain serial

The gate starts its own `systemd-run --user --scope` executor with `MemoryMax=6G` and verifies the
actual cgroup-v2 memory limit and peak interface before starting any check. The executor inherits
the head and global flock descriptors. These reservations remain held if the launching gate exits
while scoped validation continues. The blocking stage executes inside that scope.
No check runs during scope setup. A missing user bus or refused setup falls back to the complete
serial path. So does a sharing transition that cannot start the scope, for example because another
waiter holds `sharing.lock`: the caller takes the exclusive lock, drops the unstarted scope and records
`scope.reason=exclusive_admission_serial` (#10820). A scoped run whose executor is missing or closed
refuses as `validation_incomplete` (`scope_setup_unavailable`) before any check; it never asserts.
Failure after checks start is incomplete, with no repeated stage or automatic retry.
Cleanup addresses only the run's generated unit and descendants. Scoped receipt publication follows
verified cleanup. If descendants cannot be verified as settled, the executor retains its inherited
reservations for own-unit cleanup and driver disposition; it never promotes an orphaned owner.
When the launching gate cannot verify that cleanup, the incomplete refusal names the step that failed
(`unit kill`, `executor reap` or `descendant drain`), the error class, and whether the executor had
reported itself settled.

Tests that inject failures into in-process serial stages pin `LU_PRE_PUSH_GATE_MAX_CONCURRENT_RUNS=1`
with `monkeypatch`. This keeps their assertions valid when the invoking push uses two slots. Startup
I/O fault injection and the non-green leader/follower test also pin serial admission, where
interrupting the leader ends its validation stage before the follower checks for a reusable receipt.
Gates the tests start as subprocesses never inherit the invoking push's
`LU_PRE_PUSH_GATE_MAX_CONCURRENT_RUNS` (#10820), and neither do in-process gates: every gate test starts
with the variable unset (#11207). On a quiet host with a user bus, an inherited `2` sent an in-process
`validate` into a real scope child, a fresh process that the test's monkeypatches never reach. A test
that needs two slots sets the value explicitly. The scope proof keeps `effective_workers: 1`, so a
holder that runs an older gate still reads it as valid.

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

`<git-common-dir>/lu-pre-push-gate/receipts/<head>-<base>.json` lets a retry of the same commit skip the
run. It is bound to the commit, tree, base and its fallback reason, the gate version and `tools`
(digests of the gate, launcher and pre-commit configuration; the interpreter, pytest and pre-commit
versions, pytest being what the configuration's pytest-based `pre-push` hooks run under), and carries a
`seal`, the SHA-256 of its key, outcome and time. It expires after one hour.

Reuse requires every field (#11207): exactly the key, outcome, time and seal; a seal that matches; and
a key equal, field for field with no extra ones, to the one the gate would write for the current plan.
A missing, extra or altered field refuses reuse and the gate runs. The seal makes any edit after
writing visible; a receipt rewritten and resealed as a whole is outside what a local receipt can prove
(`git push --no-verify` is the bypass anyway). A receipt that gate version 11 or older wrote carries
another `gate_version` and the test selection it ran, so it never stands for a version 12 run: the gate
runs its stage and writes a new receipt (#11276). Rebuilding the plan also rejects untracked validation
inputs after either wait. A missing or unsafe immutable identity cannot authorize reuse.

## Measurement (AC-05)

Each attempt appends a durable `BEGIN` row before validation and a `TERMINAL` row for its typed outcome
to `<git-common-dir>/lu-pre-push-gate/measurements.jsonl`: outcome, reason, failing hooks, admission
wait and duration. Join with first-attempt CI outcome per PR head for the before/after report.
`admission_wait_s` includes both waits; `coalescing_wait_s` records the head queue wait separately.
`queue_depth` and `queue_position` describe the global queue only. A follower that reuses a receipt
before global admission records zero for both, with detail `valid receipt after coalescing`.
Both rows carry a generated `attempt_id`, `measurement_schema` independent of the validation receipt
version, and SHA-256 fingerprints of the source, launcher, configuration, and stdin.
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

The row's `stages` object contains `pre_commit` only when the stage is entered.
`queue_wait_s` excludes the run's `scope_setup_s` from total admission time. `execution_s` records
attempt time excluding admission; the existing `duration_s` remains the total push observation.
`execution_s` is not a budget reading. It also counts plan building and kill cleanup. To see which
budget a stage consumed, compare that stage's `elapsed_s` with its `allowance_s`.
A row whose stages ran records the configured bounds as `stage_budget_s` and `run_budget_s`.
Gate version 5 introduced the separate stage allowances. Rows with `gate_version` 4 or lower used one
budget, the size of today's stage allowance, shared by both stages. Their pytest stage could use only
what pre-commit left of it.
Those fields were additive and changed no existing meaning, so they stayed in `pre-push-measurement.v1`.
Gate versions 9 to 11 (#11207) also ran an affected-test selector and pytest; their rows describe them.
Gate version 9 (#11207) replaces the `shadow` record with `selection`, and `nodes` and
`deferred_to_ci` now describe the set that ran, so its rows are `pre-push-measurement.v2`.
Once a plan exists, the row also records `base`, `selected_test_files`, `changed_test_files` and
`changed_paths` (#10820), and `base_fallback` (null, or the `merge_base_*` reason; #11207), which the
receipt also binds.
Gate version 10 (#11207 review) adds `deleted_paths` to the row and the receipt, the `tools` and
`seal` receipt fields, and `selected_test_files` counted after the selector answered.
Gate version 11 (#11207 review) runs the registry for a range that deletes anything but documentation
(`selection.reason: deleted_paths`, with `selection.deleted_paths`) and drops the selector's base-graph
scan and the `selector_ignored_deleted_paths` reason.
From gate version 9 a stage timeout records `reason` `timeout` or `timeout_under_load` and its stage's
`load_at_timeout` (#11140); version 8 and older rows record `validation_incomplete` with `(timeout)` in
`detail`. Version 9 also applies the main-refresh base rule above to every row's `base`.
Gate version 12 (#11276) runs no tests, so its rows are `pre-push-measurement.v3`: they drop
`selection`, `nodes`, `selected_test_files`, `changed_test_files`, `changed_paths`, `deleted_paths`,
`registry_version`, `deferred_to_ci`, `slot_wait_s`, `test_slots`, the requested and effective test
process fields and `invariant_serial_total_s`, and the `pytest` stage entry. `base` and `base_fallback`
remain.
`resources_at_admission` contains fresh admission observations or explicit nulls.
`peak_memory_bytes` comes from the scope's `memory.peak`, read by the scoped executor before it exits.
It covers the scope and its descendants, never a point sample. Serial runs and failed peak reads
record null and `peak_memory_unknown_reason`. Unknown measurements do not establish resource bounds,
valid comparison evidence, or a throughput improvement. Supported-bus production-entry evidence
and independent held-out review remain necessary; injected scope tests do not certify the runtime.

Each entry records `elapsed_s` from a monotonic clock, `outcome` and `reason`. Stage time includes
stage setup, command execution and cleanup; admission wait remains in `admission_wait_s`.
`allowance_s` is the execution time the stage could use from its start. `allowance_limited_by` names the
bound that set it: `stage_budget` (the stage's own allowance) or `run_budget` (what remained of the push
total). After a kill, `elapsed_s` can exceed `allowance_s` by the kill cleanup, at most two cleanup bounds.
An earlier successful entry survives a later failure. Receipt reuse creates no stage entries.

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
gate outcomes, execution bounds or receipt validity.

## Merge-main rule

Merge `origin/main` into a worker branch only when `git merge-tree` against a freshly fetched main SHA reports
a conflict, when the driver disposes on base/head/combined-tree evidence that the branch is incompatible with
the base, or on driver order. A merge-tree error is unknown, not a conflict. Every new head needs renewed
approval and CI; merge-group CI stays the authority for semantic combinations.

## Bypass

`git push --no-verify` is the explicit operator bypass; the rescue path in `scripts/delegate.py` uses it
deliberately. Agent sessions must not.
