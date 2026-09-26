# Systemd unit templates (loopback services & scheduled maintenance)

Templates only — do not commit machine-specific paths. Copy a unit into
`~/.config/systemd/user/` (linger enabled via `loginctl enable-linger $USER`) or
`/etc/systemd/system/`, replace `@REPO_ROOT@` / `@PRIVATE_ROOT@`, run
`systemctl --user daemon-reload`, then enable/start.

## Dispatch worker slice (`lu-dispatch.slice`)

One slice for every detached worker `scripts/delegate.py` launches (#8645). The
driver stays outside it. A runaway worker is killed inside the slice; the driver
and the host services are not in that cgroup.

`MemoryHigh=10G` is the throttling line and `MemoryMax=11G` is the last line of
defense. `systemd.resource-control(5)` (this host's systemd 259 man page) says to
use `MemoryHigh=` as the main control and `MemoryMax=` only as the last line of
defense, so `MemoryHigh` sits just under `MemoryMax` (10GiB / 11GiB). `MemoryMax=`
does not cap swap — the 2026-09-24 scope used 6.3GiB of swap — so the unit also
sets `MemorySwapMax=1G`. The limits are the unit file. There is no environment
override.

Running without the slice is supported. Dispatch then prints one warning and
starts the worker with plain `Popen`, and the task record's `launch_mode` is
`popen-fallback`. `LU_DISPATCH_ISOLATION=fallback` forces that path.

### Prerequisites

All of these have to hold or dispatch will not use the slice:

- Linger is on: `loginctl show-user "$USER" -p Linger` prints `Linger=yes`.
  Without linger the user manager, and every scoped worker, die when the
  session ends (`loginctl enable-linger "$USER"`).
- `/sys/fs/cgroup` is cgroup v2: `stat -f -c %T /sys/fs/cgroup` prints `cgroup2fs`.
- The user manager has the memory controller:
  `/sys/fs/cgroup/user.slice/user-$(id -u).slice/user@$(id -u).service/cgroup.subtree_control`
  contains `memory`.
- After install, `systemctl --user show -p MemoryMax,MemorySwapMax lu-dispatch.slice`
  prints `MemoryMax=11811160064` and `MemorySwapMax=1073741824` (11GiB and 1GiB,
  base 1024). A slice name systemd synthesized with `MemoryMax=infinity` does
  not count.

### Install

Do not commit a machine path. From a checkout:

```bash
mkdir -p ~/.config/systemd/user
cp packaging/systemd/lu-dispatch.slice ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user show -p LoadState,MemoryHigh,MemoryMax,MemorySwapMax lu-dispatch.slice
```

No `enable` is required. The slice is started when a worker scope is placed in
it. Confirm a live worker with `systemctl --user status <launch_unit>.scope`
or `/proc/<pid>/cgroup`. `--collect` drops the scope unit after the worker
exits.

## Loopback Services

Services bind `127.0.0.1` only. Reach them from another machine with an SSH
tunnel; set `MONITOR_INSTANCE_ID` in the environment so `/api/health`
distinguishes hosts. For `GET /api/occupancy`, an empty map makes the API
process fill the production glance row `host-teacher` in-process (plus
observer-only `mac-operator`). Optional `MONITOR_OCCUPANCY_HOST_IDS` adds
`canonical=opaque-id` pairs (opaque values only). Optional local seats:
`ATLAS_JOB_SELF_HOST` or `MONITOR_OCCUPANCY_DRIVER_HOST_ID` attaches
session-stream driver leases; `MONITOR_OCCUPANCY_MARKERS` publishes
Foundry/compiler heartbeats. Do not put addresses or SSH hostnames in the
occupancy JSON. `host-job` is not a default glance row.

Units are **Linux-native `Type=simple`** processes. Do not wrap
`./services.sh start` in `Type=oneshot RemainAfterExit=yes`: that is
launchd-shaped and does not supervise the listener on Linux. macOS still
uses `./services.sh supervise api` / launchd.

Public fixtures use opaque ids `host-teacher` (and mapped `host-job` only when needed).

Available service templates:
- `learn-ukrainian-api.service`: Monitor API service (`scripts/api/main.py`).
- `learn-ukrainian-astro.service`: Astro frontend UI.
- `learn-ukrainian-sources.service`: Sources lookup service.
- `learn-ukrainian-work.service`: Work projection adapter.
- `learn-ukrainian-loopback.target`: Target grouping loopback services.

## Scheduled Maintenance Timers

User timers run background reconciliation, garbage collection, and state
reporting. Target hosts: **any host with a checkout + `batch_state/`** (worker,
runner, and orchestrator hosts).

### 1. Reconciliation Sweep (`learn-ukrainian-reconcile.service` + `.timer`)

- **Frequency**: Every 5 minutes (`OnBootSec=2min`, `OnUnitActiveSec=5min`, `AccuracySec=30s`), so a worker killed by the OOM killer or SIGKILL stops reading `running` within one interval (#8645). Dispatch admission also sweeps dead pids before it counts write workers.
- **What it does**: Runs `scripts/orchestration/reconcile_sweep.py --apply` which:
  1. Releases write-ownership claims for inactive tasks via `dispatch_settle release-stale` (the same reconciliation every dispatch runs at admission).
  2. Marks running/spawning task records whose pid is dead as `crashed` via the existing lazy heal path (`scripts/delegate.py status`). The mark re-checks status, pid, run nonce and liveness under the task's writer lock, so it cannot overwrite a worker's own terminal write; a pid owned by another user, or reused, counts as alive.
  3. Logs a one-line summary count (`scanned_tasks`, `zombies_crashed`, `stale_claims_released`) to stdout/journal.
- **Default mode**: Apply. Run `.venv/bin/python -m scripts.orchestration.reconcile_sweep` by hand (no `--apply`) for a report-only dry run. To make the timer report-only, drop `--apply` from `~/.config/systemd/user/learn-ukrainian-reconcile.service`.
- **Enable or update** (the unit files are templates; install them with `@REPO_ROOT@` replaced):
  ```bash
  systemctl --user daemon-reload
  systemctl --user enable --now learn-ukrainian-reconcile.timer
  ```

### 2. Worktree Garbage Collection (`learn-ukrainian-worktree-gc.service` + `.timer`)

- **Frequency**: Every 4 hours (`OnBootSec=15min`, `OnUnitActiveSec=4h`, `RandomizedDelaySec=1800`, `Persistent=true`) — matches the macOS launchd cadence.
- **What it does**: Runs `scripts/orchestration/run_scheduled_worktree_cleanup.sh` to prune stale worktree registrations, clean up merged/closed PR branches, and run automatic git maintenance with receipt logging.
- **Default mode**: Apply. The shipped unit passes `--apply`, matching macOS launchd. The reaper stays fail-closed for OPEN PRs, live working directories, dirty worktrees, and unreadable GitHub state — this denser cadence does not loosen any of those guards, it only shrinks the backlog between runs.
- **Disable automatic reaping**: Set `LU_REAPER_DISABLED=1` in the user unit environment to stop automatic reaps, or `LU_REAPER_TERMINAL_DISPATCHES=0` to disable only the optional terminal-dispatch class. Reload systemd after changing the unit:
  ```bash
  systemctl --user daemon-reload
  ```
- **Enable command**:
  ```bash
  systemctl --user enable --now learn-ukrainian-worktree-gc.timer
  ```

### 3. Project State Reporter (`learn-ukrainian-project-state-reporter.service` + `.timer`)

- **Frequency**: Every 5 minutes (`OnUnitActiveSec=5min`, `OnBootSec=2min`).
- **What it does**: Runs `scripts/orchestration/run_project_state_reporter.sh` to report periodic host project state.
- **Enable command**:
  ```bash
  systemctl --user enable --now learn-ukrainian-project-state-reporter.timer
  ```
