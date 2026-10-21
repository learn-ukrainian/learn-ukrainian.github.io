# Host test slots

The host defaults to a test pool of half its CPUs, rounded down, with at least 2 slots (#10715).
Worker pytest runs and the pre-push gate take slots from one pool before they start their processes. A run that cannot get slots
waits in a first-come-first-served queue and prints its position. It never starts and piles up.

Code: `scripts/common/test_slots.py`. Status: `.venv/bin/python -m scripts.common.test_slots status` or
`GET /api/ops/v1/test-slots`.

## How a run takes slots

- A run asks for its process count: its xdist worker count, or 1 for a serial run. The pool size caps
  the request, so every request can be met and none deadlocks.
- Only the head of the queue takes slots. A large request is never starved by smaller ones behind it.
  This is strict FIFO, so a free slot can stay idle while the head waits for enough.
- A run holds its slots for its whole session and starts no more processes than it holds.
- Each slot is a lock file, and each waiting or holding run keeps its ticket locked (`flock`). The
  kernel drops a lock when its process exits, including on SIGKILL. A crashed run therefore frees its
  slots at once. The next waiter reaps the inert files it leaves behind, however many there are: only
  live tickets count toward the limit of 1024. Until a waiter has reaped them, `status` reports
  `test_slots_pool_unavailable` while more than 1024 ticket files exist.
- Descendants of a holder run inside its slots and never queue themselves. Examples are xdist workers,
  pytest runs started by tests and the gate's pytest children. The holder marks them with
  `LU_TEST_SLOTS_HOLDER`. The marker is checked, never trusted. It counts only when all of these hold:
  - it names a ticket in the `holders` directory of the pool that environment selects;
  - the current user owns that ticket and a live process holds its lock;
  - the ticket's record holds exactly the marked count;
  - every slot the record claims is locked, and that slot's file names this ticket and the marker's nonce
    (`<count>:<nonce>:<ticket>`), which the pool minted when it issued the slots, never the ambient
    `LU_RUNTIME_RUN_NONCE`;
  - the run names no dispatch task other than the hold's.

  A marker that is dead, copied, inflated or carried into another task is ignored, and so is a
  hand-written ticket, whether it claims free slots, another run's slots or sits in a pool the caller
  made without holding its slots. A run that names no
  task stays inside its ancestor's slots, as tests do when the suite strips the agent's identity.
  `delegate.py` removes any marker from a dispatched worker's environment, so a worker never runs inside
  its dispatcher's slots.
- A pytest run below a live holder, dispatch run or not, starts at most the held count of xdist
  workers. Before the session starts, the `ci.pytest_dispatch_cap` plugin caps `-n` (`auto` included),
  cuts an explicit `--tx` list and lowers `PYTEST_XDIST_AUTO_NUM_WORKERS` for the run and its own
  descendants. The count is per run: it does not add up the runs that share one hold.
- The governor never raises an existing `PYTEST_XDIST_AUTO_NUM_WORKERS`, such as a driver scope's
  memory cap. A value of `0` keeps `-n auto` serial.

## Who uses it

| Caller | How |
| --- | --- |
| Dispatch-worker pytest runs | The `ci.pytest_dispatch_cap` plugin holds slots when `LEARN_UKRAINIAN_DISPATCH_TASK_ID` is set. This covers every documented command, such as `.venv/bin/python -m pytest -n 2 -q <files>`, the pre-commit pytest hooks and `scripts/ci/components.py`. It skips `--collect-only` and `--help`. A nested run queues for nothing and starts at most the inherited count of workers. A wait timeout is a pytest usage error (exit 4) naming `test_slots_wait_timeout`. |
| Pre-push gate | The pytest stage holds slots and passes `-n` equal to the slots held. The wait is bounded by `TEST_SLOT_WAIT_S` (600 s) and recorded as `slot_wait_s`. It spends neither the stage allowance nor the run budget. See `docs/runbooks/pre-push-gate.md`. |
| Any other test command | `.venv/bin/python -m scripts.common.test_slots run -- <command>` waits for slots, rewrites a visible `-n`/`--numprocesses` (including `auto`) to the slots held, caps a hidden `-n auto` through `PYTEST_XDIST_AUTO_NUM_WORKERS`, and execs the command, so the command itself holds the slots until it exits. A repo pytest the command starts with a hidden explicit `-n` is capped by the plugin above. |
| Codex read-only reviews | The dispatch worker holds 2 `review` slots before the CLI starts. See "Sandboxed reviews" below. |
| Dispatch admission | `delegate.py dispatch` refuses a new write worker while more than `DISPATCH_MAX_TEST_SLOT_QUEUE` runs (default 4) wait for slots. The refusal uses the usual admission message and exit 3. |

Operator shells and CI are unchanged: the plugin takes slots only for dispatch workers, it caps
workers only for runs below a live holder, and a true `CI` variable turns the pool off unless
`LU_TEST_SLOTS=on` is set explicitly.

## Sandboxed reviews

Codex runs a read-only review's commands in a user-namespace sandbox that maps only the current user.
There, root-owned ancestors of the pool, `/` included, show the kernel's overflow owner, and every path
is mounted read-only. The governor therefore refuses to prepare the pool there with
`test_slots_pool_unavailable` ("owned by another user"). That refusal is correct, because the sandbox
cannot prove who owns those ancestors, and it stays in place (#11230, #10744).

For a review-typed Codex dispatch in `read-only` mode, the dispatch worker takes the slots instead,
outside the sandbox, with the full ownership walk:

1. It queues in the host pool like any run and holds 2 `review` slots, the review bound of two test
   workers. The task record shows the result as `review_test_slots`: `held` (with the slot count and
   the wait), `refused` (with the reason) or `disabled`. A refused review still runs, and its governed
   test runs are refused with a typed reason.
2. The CLI receives the holder marker. Inside the sandbox, `test_slots run` and the dispatch pytest plugin
   only read the marked ticket and the slot files and check their locks, so they need no write access to
   the pool. A sandboxed process, one whose user namespace maps only part of the id range, cannot choose
   the pool: `LU_TEST_SLOTS_DIR` or `LU_SCRATCH_ROOT` there is refused with
   `test_slots_pool_override_refused`, and it may join only a `review` hold.
3. The review's governed test runs take turns on the hold's session lock, a `.session` file beside its
   ticket. Concurrent runs of one review therefore never add up past its 2 slots. The run that holds the
   turn passes `LU_TEST_SLOTS_SESSION` to its own descendants, such as a pytest a test starts or the
   command it execs. The value names the turn's process, its start time and the descriptor holding the
   session lock. A descendant joins without waiting only when the kernel shows that process is itself or
   an ancestor and holds the lock through that descriptor. A sibling that guesses the value or copies it
   is refused with `test_slots_session_unverified`.
4. Every run of a turn holds the hold's slot files and its `.turn` file shared until it ends. Slots
   therefore stay taken while any reviewer test run is alive, even after the worker that issued the
   hold has ended or was killed, and the next turn starts only when every run of the previous one has
   ended. `status` reports such slots as `slots_draining`.
5. The worker gives its own hold back when the runtime returns: on success, on failure, on a timeout and
   on cancellation. New runs are refused from then on, because the marker's holder is gone.

The slots stay reserved while the reviewer reads. The dispatch hard timeout bounds that time. Other
routes are unchanged: a Claude read-only seat has no OS sandbox and takes its own slots, and a write
worker takes slots for each test run.

Processes a reviewer test run starts without the governor (xdist workers, which take no slots, or other
commands a test starts) are not counted on their own. They run inside their governed run's slots and end
with it in the normal case. If their governed run is killed first, they can outlive it until they end or
`post_task_reap` stops the task's leftover processes.

## Settings

| Variable | Default | Meaning |
| --- | --- | --- |
| `LU_TEST_SLOTS` | on (off when `CI` is true) | `off` restores the previous behaviour everywhere: no waits, no `-n` changes and no admission check. |
| `LU_TEST_SLOTS_COUNT` | Half the CPU count, rounded down, at least 2 | Pool size. Every participant on the host must use the same value. |
| `LU_TEST_SLOTS_WAIT_S` | 3600 | Longest wait before a typed refusal. The gate never waits longer than 600 s. |
| `LU_TEST_SLOTS_DIR` | `<fleet scratch root>/test-slots-<uid>` | Absolute pool directory, for tests and experiments. The default root is `LU_SCRATCH_ROOT` or `/var/tmp/lu`; the pool sits beside the pre-push gate's `pre-push-gate-<uid>`. |
| `LU_TEST_THREAD_CAP` | on | `off` preserves the caller's thread environment for a run that needs threads. Slot accounting stays enabled. |

## Threads inside each worker

Governed runs also limit native library threads (#10716). Before xdist starts workers, the plugin sets
`OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `NUMEXPR_NUM_THREADS`,
`ORT_NUM_THREADS` and `RAYON_NUM_THREADS` to `1`, and `TOKENIZERS_PARALLELISM` to `false`.
The launcher and the pre-push gate's pytest stage apply the same policy. Children inherit the limits.
The policy preserves only positive integers at or below `1` for numeric settings, written as ASCII
decimal digits. It replaces every other value with `1`, including zero, negatives, fractions, padded
or signed values, empty strings, `nan`, infinities, oversized integers and nonnumeric tokens such as
`8,4`, `true` and `0x10`. Those values do not reliably limit native threads.
It disables tokenizer parallelism regardless of its previous setting. The caller's shell stays unchanged.

For a test that needs native parallelism, set `LU_TEST_THREAD_CAP=off` for that command and record
the test and its owner. This preserves the environment rather than removing limits inherited from an
ancestor. `LU_TEST_SLOTS=off` and the governor's CI exemption also disable application of thread caps.
Operator pytest runs outside a live holder stay unchanged. Libraries can ignore these environment
variables, so measure native thread counts before claiming a CPU bound. NumPy's
[threading documentation](https://numpy.org/doc/stable/reference/global_state.html#number-of-threads-used-for-linear-algebra)
describes its BLAS backend controls.

## Pool directory permissions

The pool directory is mode 0700 and owned by the current user. Its path follows the trust model of
the pre-push gate's base temp (#10654; see "Bounds" in `docs/runbooks/pre-push-gate.md`): only the
current user and root are trusted, and no other user may be able to redirect the path. Before anything
is created, the path is resolved from `/` one component at a time. Every directory on the way must be
owned by the user or root and must not be writable by group or others unless it is sticky, as the
system temp directories are. A link is followed only if the user or root owns it, and its target passes
the same checks. Missing components, the scratch root included, are created with mode 0700 whatever
the umask. A root created under umask 002 would be group-writable, and the gate would then refuse its
own base temp below the same root. `status` runs the same checks and creates nothing.

Each of these is refused with `test_slots_pool_unavailable`:

- a directory or link on the way that another user owns;
- a directory that group or others can write and that is not sticky;
- a link loop;
- a pool directory that is itself a link, or that belongs to someone else;
- a pool inside a Git checkout or Git directory.

The message names the kind of component at fault, never its path. To fix a refusal, set
`LU_SCRATCH_ROOT` to a private directory (owned by the user, mode 0700) whose ancestors only the user or
root can write, or remove group and other write from the directory at fault. The pool never falls back
to a per-process temp directory, because that would split it.

## Refusals

Every refusal is typed and the command does not run:

- `test_slots_wait_timeout`: no slots within the wait limit.
- `test_slots_pool_unavailable`: the pool directory is unusable.
- `test_slots_invalid_configuration`: a setting above is malformed.

The launcher exits 75 and prints a `{"test_slots": {"outcome": "refused", ...}}` line.

## When the queue is long

1. Run `.venv/bin/python -m scripts.common.test_slots status` to see the holders (task id, kind, slots
   held, how long held, pid) and the waiting runs in queue order.
2. A holder that should have finished is still running a test session. Look at its task, not at the
   pool. Never delete pool files to free slots: a live holder keeps its locks, and a deleted lock file
   lets a second run take the same slot.
3. As an emergency stop for one command, set `LU_TEST_SLOTS=off`. Report it, because that run is
   ungoverned.

## High-load attribution

The Monitor's existing periodic collector checks load on its refresh ticks, with a 15-second sleep
between ticks. A work projection refresh can delay the next tick. When the 1-minute load is
greater than `LU_LOAD_SAMPLE_THRESHOLD` (default `20`), it records at most one sample per 60 seconds,
including across Monitor workers and restarts. The threshold must be finite and non-negative.
Collection failures leave the work projection collector running and log only the exception type.

`GET /api/ops/v1/load-samples?limit=50` reads the latest samples in chronological order, with
`limit` from 1 to 500. The ignored runtime ring at `batch_state/load-samples/samples.jsonl` retains
the last 500 JSON lines. Reading the route never collects processes or creates files. A missing
ring returns an empty list; an unreadable ring returns `load_samples_unavailable`.

Each sample has a UTC timestamp, all three load averages, the top five processes by CPU usage,
their summed CPU percentage, and the governor's holder task IDs and slot counts. CPU usage is
measured over a shared 0.1-second interval; 100% means one CPU, so a multithreaded process can exceed
100%. Command names are the only process text collected. Arguments, executable paths, environments
and PIDs are never recorded; names containing path separators or other non-name characters become
`unknown`. An unavailable governor is recorded as an error, not as proof of an idle pool.

Sampling does not kill, throttle or admit processes and does not change which tests use the governor.
