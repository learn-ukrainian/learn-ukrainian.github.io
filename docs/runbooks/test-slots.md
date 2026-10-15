# Host test slots

The host runs at most as many test processes as it has CPUs for (#10662). Worker pytest runs and the
pre-push gate take slots from one pool before they start their processes. A run that cannot get slots
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
  `LU_TEST_SLOTS_HOLDER`. A marker whose holder is dead is ignored.
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
| Dispatch admission | `delegate.py dispatch` refuses a new write worker while more than `DISPATCH_MAX_TEST_SLOT_QUEUE` runs (default 4) wait for slots. The refusal uses the usual admission message and exit 3. |

Operator shells and CI are unchanged: the plugin takes slots only for dispatch workers, it caps
workers only for runs below a live holder, and a true `CI` variable turns the pool off unless
`LU_TEST_SLOTS=on` is set explicitly.

## Settings

| Variable | Default | Meaning |
| --- | --- | --- |
| `LU_TEST_SLOTS` | on (off when `CI` is true) | `off` restores the previous behaviour everywhere: no waits, no `-n` changes and no admission check. |
| `LU_TEST_SLOTS_COUNT` | CPU count minus 2, at least 2 | Pool size. Every participant on the host must use the same value. |
| `LU_TEST_SLOTS_WAIT_S` | 3600 | Longest wait before a typed refusal. The gate never waits longer than 600 s. |
| `LU_TEST_SLOTS_DIR` | `<fleet scratch root>/test-slots-<uid>` | Absolute pool directory, for tests and experiments. The default root is `LU_SCRATCH_ROOT` or `/var/tmp/lu`; the pool sits beside the pre-push gate's `pre-push-gate-<uid>`. |

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
