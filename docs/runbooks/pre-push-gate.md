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
   branches and divergent tips start at the merge-base. Either way the range, and so the selector's input
   (check 3), holds only the branch's own changes, never main's (#11207).
   When no single merge-base other than `<head>` can be proven, the base stays the previous one (the
   remote tip, or Git's single `merge-base` answer for a new or divergent tip) and the gate does not ask
   the selector: it blocks on the conservative set (changed test files plus the registry) and records the
   cause as `base_fallback` and as the selection's `reason`: `merge_base_unavailable` (no `origin/main`,
   a shallow clone, no common history or a Git error), `merge_base_ambiguous` (several merge-bases),
   `merge_base_unproven` (the `is-ancestor` check failed) or `merge_base_is_head` (`origin/main` already
   contains the head). The last still runs: the update moves the remote, so its checks run over
   `<remote>..<head>`, or over the registry alone for a new branch at a commit main already has, and it
   is never accepted as "no outgoing commits". Only a remote tip equal to the head has no outgoing
   commits. A new or divergent tip with no merge-base at all is `range_unresolved`.
   The same bounded stage then always runs `lint_opsec_leaks.py --commit-range <base>..<head>`.
   It reads each commit's version of its touched files, including values later reverted or files
   later deleted. Missing selected blobs refuse the push; diagnostics omit matched values.
   It also runs the existing `check-no-internal-ids` hook explicitly with `--hook-stage pre-commit`
   and the same `--from-ref`/`--to-ref` pair. This preserves that hook's exact learner-surface
   file filter and detection rules while enforcing it during the push gate.
2. Test files the range adds or changes (`tests/**/test_*.py`).
3. The test files those changes affect (#11207), from the importer-closure selector
   `scripts/ci/pre_push_shadow.py` (the name is historical; it ran in shadow before #11207).

Check 1 is the pre-commit stage; checks 2 and 3 form the pytest stage. **The pre-push gate blocks only
on tests affected by the pushed change. CI runs the full suite, the repository-wide invariant registry
included, and remains the merge gate.** A green pre-push is never evidence that unaffected tests pass.

### Affected-test selection

The selector starts beside the pre-commit stage, inside the same admission and scope, and must answer
within `SHADOW_BUDGET_S` before pytest starts. It scans the indexed tree with
`scripts/ci/components.py` (`scan_imports`) and follows only proven edges, in reverse: Python imports
with their parent packages, literal `importlib`/`runpy` loads, literal file reads and literal Python
subprocesses. A test file is affected when it reaches a changed path that way. A changed
`conftest.py` affects every test file under its directory. A change to a file pytest loads for every
test file affects every test file: the pytest configuration (`pyproject.toml`, `pytest.ini`,
`setup.cfg`, `tox.ini`), the root or `tests/conftest.py`, and the `-p` plugins in `addopts`.

**A range that deletes anything but documentation runs the registry, not the selector** (#11207,
`selection.reason: deleted_paths`). The gate lists the range without rename detection, so renaming a
path away deletes its old path too. Documentation is Markdown under `docs/` (`documentation_only`);
Markdown elsewhere is data that tests and scripts read (lessons, rules, fixtures, a script's README),
so deleting it counts like any other deletion. Why: a deleted path is gone from the tree the selector
scans, and the tests it breaks are the ones that still reach it. An earlier design found them through
the base commit's import graph, behind a text prefilter of the base files; the scanner also resolves
constant concatenation (`__import__('scripts.' + 'mod')`, `Path('scripts') / ('tab' + 'le.json')`), so
the prefilter dropped real dependencies and an unrelated changed test kept the too-small answer
non-empty. No static graph proves every way a test reaches a path, so the gate does not try: the
registry set is sound for a deletion by construction, and CI's full suite still runs the importers.
The row's `selection.deleted_paths` names the first `DELETED_PATHS_RECORDED` (20) such paths; the
receipt binds the whole deletion set. A range that deletes only documentation keeps the selection.

Two kinds of reach are deliberately not followed; CI covers them:

- edges the scanner cannot prove (computed paths, shell commands, `sys.path` edits). Treating each as
  "could read anything" selects nearly every test file on every push;
- modules reached only through what a conftest or a `-p` plugin imports. The root `tests/conftest.py`
  imports a chain that reaches most of `scripts/`, and any selected test already loads that conftest.

The answer (`pre-push-selection.v1`) lists the affected test files nearest first, by import hops.
The gate then:

- always runs the changed test files;
- defers to CI the selected modules whose tracked duration in `scripts/ci/pytest-file-durations.json`
  exceeds `HEAVY_MODULE_S`, as it does for registered modules;
- runs the rest nearest first until the estimated cost of the changed files plus the selected ones
  (tracked CI seconds, the median for an untracked file) would pass `SELECTION_COST_CAP_S`, and defers
  that file and every farther one to CI. Changed files run even when they alone pass the cap.

Both deferrals are recorded. A selection with no affected test files and no changed test file is
green with `pytest: "no tests selected"`, recorded as `selection.no_tests_affected`. That is the
expected result for a docs-only or data-only change, and only for one: when such a range adds or
changes a Python file, the gate falls back (`python_change_selects_nothing`, below) instead of
passing with zero tests.

### Fallback: the conservative set

When the selector fails or exits non-zero, times out, answers malformed or in another schema, or names
a path that is not a test file, when every test file is affected (a configuration change), or when it
selects nothing for a range that adds or changes Python files and changes no test file, the gate
blocks on the conservative
set instead: the changed test files plus the invariant registry,
`KNOWN_REPO_WIDE_MODULES` and `KNOWN_REPO_WIDE_FUNCTIONS` in `tests/test_repo_wide_marker_invariant.py`.
The registry is read by AST and deduplicated (a function id is dropped when its whole file is
selected), with the deferrals described in Bounds. Its version is a digest of the gate version and
the ids. The event records `selection.status: fallback` with a typed `selection.reason`:
`selector_unavailable`, `selector_failed`, `selector_timeout`, `selector_unparseable`,
`selector_invalid_output`, `selector_schema_mismatch`, `all_tests_affected` or
`python_change_selects_nothing`; or, skipping the selector, one of the `merge_base_*` reasons from
check 1 or `deleted_paths` (above) (#11207). The set is never
silently narrower and never green on an unknown selection. The registry is loaded, and its
materialization checked, on every push, because the fallback needs it.

When the pytest stage holds test slots, its children inherit the thread caps from
`scripts/common/test_thread_caps.py` (#10716): `OMP_NUM_THREADS`, `MKL_NUM_THREADS`,
`OPENBLAS_NUM_THREADS`, `NUMEXPR_NUM_THREADS`, `ORT_NUM_THREADS` and `RAYON_NUM_THREADS`
are capped at `1`, and `TOKENIZERS_PARALLELISM` is `false`.
Existing positive integers at or below `1`,
written as ASCII decimal digits, are preserved. Every other value is replaced with `1`, including zero,
negatives, fractions, padded or signed values, empty strings, `nan`, infinities, oversized integers and
nonnumeric tokens such as `8,4`, `true` and `0x10`. The stdlib-only gate copies the policy;
`tests/test_pre_push_gate.py` checks table and behavior parity with the helper.
`LU_TEST_THREAD_CAP=off` preserves the caller's thread environment while retaining slot accounting.
The governor's disabled and CI paths apply no thread caps. See `docs/runbooks/test-slots.md`.

## Outcomes

| Outcome | Exit | Meaning |
| --- | --- | --- |
| green | 0 | Push proceeds; a receipt is written. |
| `pre_commit_failed`, `tests_failed` | 1 | Push refused; failing hook names or pytest node ids are listed. A pytest run killed at its bound after it printed `FAILED`/`ERROR` ids is `tests_failed` with those ids (#11140); only complete output lines count. |
| `tree_mismatch`, `dirty_tree`, `range_unresolved`, `invalid_ref_updates` | 1 | The exact commit cannot be validated as pushed. |
| `untracked_inputs` | 1 | Untracked or ignored `*.py`, `*.pth` or pytest/tox/setup/pyproject config files exist; they could change the run but not the receipt. Commit or remove them. |
| `validation_incomplete` | 75 | Not validated and not green: `invalid_configuration`, `admission_timeout`, `timeout` and `timeout_under_load` (a stage reached its bound; see Bounds), `registry_unavailable`, `pytest_error` (pytest exited without a verdict), `pytest_temp_unavailable` (no private pytest base temp below a verified root outside every Git checkout and Git directory; see Bounds), `changed_tests_unmaterialized` (a test file the range changes is absent from a sparse worktree; `git sparse-checkout add tests`), `selected_tests_unmaterialized` (likewise for an affected test file the gate would run), `test_slots_wait_timeout`, `test_slots_pool_unavailable`, `test_slots_invalid_configuration`, `test_slots_unavailable` (host test slots, below), `scope_setup_unavailable` (the scoped executor was never set up or is already closed; no check ran). The branch is preserved; return to the driver. Never retry blindly. |

The last stderr line before the bypass hint is machine-readable: `{"pre_push_gate": {...}}`.
After a plan is built, every `validation_incomplete` detail ends with its selection (#10820), for example
`selection: base <sha>, 3 selected test files (1 changed by the range), 1 changed paths`. Selected test
files count the distinct files pytest blocks on when the run ends: once the selector has answered, the
changed tests plus the selection that ran (on the fallback set, plus the registered invariants), so a
timeout from an oversized range is recognisable and a selector-narrowed run is never reported with the
registry's count (#11207). The measurement row's `selected_test_files` records the same count; a
scoped run returns its selection with a refusal, so the caller reports it too.

## Bounds

Admission defaults to one gate per repository (lock under the Git common dir). Execution has two time
bounds (#10642), both constants in `.githooks/pre_push_gate.py`:

- Each blocking stage, pre-commit and then pytest, has its own allowance (`STAGE_BUDGET_S`) counted
  from that stage's start. Time pre-commit spends never shortens the pytest allowance.
- The run budget (`RUN_BUDGET_S`, the two allowances summed) caps total stage execution. It starts at
  global admission and is shared by every ref update of the push. A stage whose own allowance would
  outlast the remaining total stops at the total instead.

A command that reaches its stage's bound is killed with its descendants. The push is then
`validation_incomplete`, and no receipt is written. Each update is validated with its own base.
The reason is typed by the host load observed at the timeout, just before the kill (#11140), using the
admission caps (`CPU_SOME_AVG10_MAX`, `CPU_SOME_AVG60_MAX`, 8 GiB available memory):
`timeout_under_load` when the observation is above a cap, `timeout` when it is below every cap or
could not be read. The stage row records `load_at_timeout` (the three values and `load`:
`above_caps`, `below_caps` or `unknown`). High observed load is evidence, not proof of cause, and
neither reason is green or retried automatically.

The budget rule stays fixed (#11140): one `STAGE_BUDGET_S` allowance per stage, started after the
test-slot grant. In the last 50 terminal gate rows, every green pytest stage ended inside the allowance.
Every stage timeout came from a range that merged newer main into an older remote tip, so it also
selected main's own changed tests, with admission pressure below the caps. The correction was the base
rule above (#10820), not a longer allowance.
Command output goes to a file, and after every command the gate kills any descendant that inherited its run
token within a short cleanup bound, so a detached child cannot stall or outlive the gate.
`LU_PRE_PUSH_GATE_ADMISSION_WAIT_S`, `LU_PRE_PUSH_GATE_STAGE_BUDGET_S` and `LU_PRE_PUSH_GATE_RUN_BUDGET_S`
can only shorten these.

Before pytest starts, the gate takes host test slots from the pool worker pytest runs share
(`scripts/common/test_slots.py`, #10662; see `docs/runbooks/test-slots.md`). It asks for the process
count it would use, waits in the host's FIFO queue for at most `TEST_SLOT_WAIT_S` (one stage
allowance; `LU_TEST_SLOTS_WAIT_S` can only shorten it), and passes `-n` equal to the slots held. The wait is
recorded as `slot_wait_s` and in `test_slots` (status, requested, held, pool size, queue position).
It spends neither the pytest stage allowance nor the run budget, and `execution_s` excludes it. A
refusal is `validation_incomplete` with a `test_slots_*` reason before pytest starts. The gate loads the
governor from its own checkout and refuses (`test_slots_unavailable`) when it cannot. `LU_TEST_SLOTS=off`,
or a true `CI` variable, leaves the stage exactly as before.

One predecessor's admission allowance (`ADMISSION_WAIT_S`) covers one complete gate run: the run budget,
the longest test-slot wait, the selector and two cleanup bounds. The hard admission ceiling is ten of these.
The auto-finalize push timeout in `scripts/delegate.py` reads both values from the gate.

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
safe rendezvous; each run releases its own tickets and private test directory. Shared or scoped runs,
and runs without proven exclusivity, preserve other runs' directories, including those left by a killed caller.

`LU_PRE_PUSH_GATE_MAX_TEST_PROCESSES` sets the test process ceiling as a positive integer.
The default is 4, so callers get bounded parallel validation without an override. Serial validation
exhausted the time budget. A nonblank `LEARN_UKRAINIAN_DISPATCH_TASK_ID` caps the invocation
at 2 processes, matching the existing dispatch pytest plugin. An explicit positive integer override
is still supported; invalid values refuse validation, including receipt reuse. Parallel execution
requires xdist. Without xdist, execution is serial.

The pytest stage runs the planned node ids in two pytest invocations that share the pytest stage's
deadline (#10610). Changed test files run first with `--dist worksteal`, as CI runs them, so one slow changed
file is spread over the workers instead of setting a one-worker floor. The selected test files, or on
the fallback set the registered invariant nodes, then run with `--dist loadfile`, which keeps their
files whole. Each invocation gets its own private base temp. The first refusal ends the stage, and a
green stage and receipt require both invocations to pass. One invocation collecting no tests is
accepted only when the other ran tests. The receipt keeps the single plan node list, which covers
both invocations.

Base temps live outside every Git checkout and Git directory (#10654), as they do in CI, so tests
that require a scratch tree outside any checkout behave the same in the gate. The root follows the
fleet scratch convention of `scripts/common/scratch.py`: `LU_SCRATCH_ROOT` when set, else the
disk-backed default, else `<system temp>/lu-scratch` when the default cannot be created. Below it,
`pre-push-gate-<uid>/` holds one directory per Git common dir; both are created with mode 0700 and
must be real directories owned by the user with no group or other access. Admission, queue,
receipt and measurement files stay under `<git-common-dir>/lu-pre-push-gate/`.

Trust model: the gate trusts the pushing user and root, on a host the user controls. A process running
as the same user can already edit the hook, so same-user changes to the scratch tree are outside the
model. That includes renaming an ancestor while pytest runs: pytest receives the base as a path and
deletes and recreates it, so the gate cannot bind pytest to the directory it created. What the gate
guarantees is that no other user can redirect the base. Before it creates anything, it walks the root
from `/`. Every directory on the way must be owned by the user or root and must not be writable by
group or others unless it is sticky, as the system temp directories are (only an entry's owner can
rename an entry there). A link is followed only if the user or root owns it, and its target passes the
same checks. Missing components are then created with mode 0700.

Each of these refuses the push as `pytest_temp_unavailable`:

- a directory or link on the way that another user owns;
- a directory that group or others can write and that is not sticky;
- a link loop;
- a root inside a Git checkout or Git directory;
- a root that cannot be created;
- a gate directory that is not private.

The message names the kind of component at fault, never its path. An unsafe default root never falls
back to `<system temp>/lu-scratch`, and nothing falls back into the Git directory. To fix a refusal,
set `LU_SCRATCH_ROOT` to a private directory (owned by the user, mode 0700) whose ancestors only the
user or root can write. Alternatively, remove group and other write from the directory at fault. A
root created under umask 002 is group-writable, so it is refused.

Each invocation creates its own uniquely named base in the repository directory and removes only that
base when the invocation ends, green or not. The repository directory is opened once without
following links, and the base is created and removed relative to that descriptor, so the gate's own
create and remove never follow a replaced ancestor into another run's base. A cleanup failure refuses
the push as incomplete unless the run has already failed. Nothing sweeps this location. A base left by
a killed gate, including one a surviving pytest worker still uses, stays until host temp aging removes
it. On systemd hosts the stock `tmpfiles.d` rules age `/var/tmp` and `/tmp`, which hold the default
root and, unless `TMPDIR` points elsewhere, the fallback. A custom `LU_SCRATCH_ROOT` ages only if the
host has a rule for it.

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
while scoped validation continues. Every blocking stage and the selector execute inside that scope.
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

The serial pytest stage restores the stale `pytest-*` sweep only while its run holds the exclusive
Git-common admission lock. That lock excludes live shared holders and any surviving scoped executor.
A later exclusive serial run may reap directories left by a dead run. The sweep reaches only the gate
state directory, where only gates that predate #10654 create bases; it never touches the base temp
location described above. Known gap: the lock does not exclude a serial pytest worker that outlived
its SIGKILLed gate, because that worker holds no admission descriptor, so a later exclusive run can
reap the legacy base it still uses.
Shared/scoped execution or unknown exclusivity skips the sweep and records
`stale_pytest_cleanup=skipped_shared_or_unknown` in stage diagnostics. Every run still removes its
own pytest temporary directory. Sweep failures refuse the push as incomplete.

Tests that assert the exclusive sweep or inject failures into in-process serial stages pin
`LU_PRE_PUSH_GATE_MAX_CONCURRENT_RUNS=1` with `monkeypatch`. This keeps their assertions valid
when the invoking push uses two slots. Startup I/O fault injection and the non-green leader/follower
test also pin serial admission, where interrupting the leader ends its validation stages before
the follower checks for a reusable receipt. The existing shared-mode stale-sweep test still verifies
that shared execution preserves other runs' temporary directories. Gates the tests start as
subprocesses never inherit the invoking push's `LU_PRE_PUSH_GATE_MAX_CONCURRENT_RUNS` (#10820), and
neither do in-process gates: every gate test starts with the variable unset (#11207). On a quiet host
with a user bus, an inherited `2` sent an in-process `validate` into a real scope child, a fresh
process that the test's monkeypatches never reach. A test that needs two slots sets the value explicitly. Tests that expect the scope to be
attempted also clear `LU_PRE_PUSH_GATE_MAX_TEST_PROCESSES`, so a pushing caller's larger process
override cannot make the run ineligible for the scope.

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
bound to the commit, tree, base and its fallback reason, changed and deleted paths, registry version,
conservative node ids, gate version and `tools` (digests of the gate, launcher, pre-commit
configuration, selector and scanner files; the interpreter, pytest, pytest-xdist and pre-commit
versions; the selection schema). It records the selection that ran (`selection`: status, fallback
reason, digest of the selector's answer, the selected test files that ran) and the node ids it blocked
on (`blocking_node_ids`), and carries a `seal`, the SHA-256 of its key, outcome and time. It expires
after one hour.

Reuse requires every field (#11207): exactly the key, outcome, time and seal; a seal that matches;
a well-formed recorded selection (`selected` with a digest, sorted test files and no reason;
`fallback` with one of the fallback reasons above and no test files); and a key equal, field for field with no extra ones, to
the one the gate would write for the current plan with that recorded selection. `blocking_node_ids` is
therefore derived from the recorded selection, never taken from the file. A plan with a base fallback
or a `deleted_paths` fallback reuses only a receipt that ran that fallback, and a plan the selector
runs for never reuses a `merge_base_*` or `deleted_paths` receipt; the key binds the exact deletion
set, documentation deletions included. Receipts are checked before the selector runs, so the
bound inputs stand for the selection: the tree carries the selector, the import graph and the durations
table, `tools` the code and versions that run them, and the gate version the cap. A plan whose selection
is known reuses only a receipt that recorded the same selection. A missing, extra, altered or
inconsistent field refuses reuse and the gate runs. The seal makes any edit after writing visible; a
receipt rewritten and resealed as a whole is outside what a local receipt can prove, and before the
selector runs its recorded digest stands for the bound inputs (`git push --no-verify` is the bypass
anyway). A receipt validated on the fallback set records the
conservative verdict for exactly those inputs and is reused like any other.
Rebuilding the plan also rejects untracked validation inputs after either wait. A missing or unsafe
immutable identity cannot authorize reuse.

## Measurement (AC-05)

Each attempt appends a durable `BEGIN` row before validation and a `TERMINAL` row for its typed outcome to `<git-common-dir>/lu-pre-push-gate/measurements.jsonl`: outcome, reason, failing
ids, admission wait, duration, registry version and the selection (`selection`: status, reason,
scope, `selected_count`, `run_count`, `no_tests_affected`, `deferred_heavy`, `deferred_over_cap` with
`over_cap_digest`, `estimated_s`, `cost_cap_s`). `nodes` counts the node ids pytest blocked on, and
`deferred_to_ci` lists the deferrals of the set that ran (registry deferrals on the fallback set).
`invariant_serial_total_s` stays null when the selection, not the registry, ran. Join with first-attempt CI outcome
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
`execution_s` is not a budget reading. It also counts plan building and kill cleanup. Since #10642 it can
exceed one stage allowance when both stages run long. To see which budget a stage consumed, compare that
stage's `elapsed_s` with its `allowance_s`.
A row whose stages ran records the configured bounds as `stage_budget_s` and `run_budget_s`.
Gate version 5 introduced the separate stage allowances. Rows with `gate_version` 4 or lower used one
budget, the size of today's stage allowance, shared by both stages. Their pytest stage could use only
what pre-commit left of it.
Those fields were additive and changed no existing meaning, so they stayed in `pre-push-measurement.v1`.
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
`resources_at_admission` contains fresh admission observations or explicit nulls.
The top-level requested/effective test process fields remain null when no count was observed.
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
