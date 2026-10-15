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
  slots at once. The next waiter reaps the inert files it leaves behind.
- Descendants of a holder run inside its slots and never queue themselves. Examples are xdist workers,
  pytest runs started by tests and the gate's pytest children. The holder marks them with
  `LU_TEST_SLOTS_HOLDER`. A marker whose holder is dead is ignored.

## Who uses it

| Caller | How |
| --- | --- |
| Dispatch-worker pytest runs | The `ci.pytest_dispatch_cap` plugin holds slots when `LEARN_UKRAINIAN_DISPATCH_TASK_ID` is set. This covers every documented command, such as `.venv/bin/python -m pytest -n 2 -q <files>`, the pre-commit pytest hooks and `scripts/ci/components.py`. It skips `--collect-only`, `--help` and nested runs. A wait timeout is a pytest usage error (exit 4) naming `test_slots_wait_timeout`. |
| Pre-push gate | The pytest stage holds slots and passes `-n` equal to the slots held. The wait is bounded by `TEST_SLOT_WAIT_S` (600 s) and recorded as `slot_wait_s`. It spends neither the stage allowance nor the run budget. See `docs/runbooks/pre-push-gate.md`. |
| Any other test command | `.venv/bin/python -m scripts.common.test_slots run -- <command>` waits for slots, rewrites a visible `-n`/`--numprocesses` (including `auto`) to the slots held, caps a hidden `-n auto` through `PYTEST_XDIST_AUTO_NUM_WORKERS`, and execs the command, so the command itself holds the slots until it exits. |
| Dispatch admission | `delegate.py dispatch` refuses a new write worker while more than `DISPATCH_MAX_TEST_SLOT_QUEUE` runs (default 4) wait for slots. The refusal uses the usual admission message and exit 3. |

Operator shells and CI are unchanged: the plugin acts only for dispatch workers, and a true `CI`
variable turns the pool off unless `LU_TEST_SLOTS=on` is set explicitly.

## Settings

| Variable | Default | Meaning |
| --- | --- | --- |
| `LU_TEST_SLOTS` | on (off when `CI` is true) | `off` restores the previous behaviour everywhere: no waits, no `-n` changes and no admission check. |
| `LU_TEST_SLOTS_COUNT` | CPU count minus 2, at least 2 | Pool size. Every participant on the host must use the same value. |
| `LU_TEST_SLOTS_WAIT_S` | 3600 | Longest wait before a typed refusal. The gate never waits longer than 600 s. |
| `LU_TEST_SLOTS_DIR` | `<fleet scratch root>/learn-ukrainian/test-slots-<uid>` | Absolute pool directory, for tests and experiments. The default root is `LU_SCRATCH_ROOT` or `/var/tmp/lu`. |

The pool directory is mode 0700 and owned by the current user. A pool directory that is a symlink,
belongs to someone else, or lies inside a Git checkout or Git directory is refused with
`test_slots_pool_unavailable`. The pool never falls back to a per-process temp directory, because
that would split it.

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
