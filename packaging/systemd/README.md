# Systemd unit templates (loopback services & scheduled maintenance)

Templates only — do not commit machine-specific paths. Copy a unit into
`~/.config/systemd/user/` (linger enabled via `loginctl enable-linger $USER`) or
`/etc/systemd/system/`, replace `@REPO_ROOT@` / `@PRIVATE_ROOT@`, run
`systemctl --user daemon-reload`, then enable/start.

## Dispatch worker slice (`lu-dispatch.slice`)

One slice for every detached worker `scripts/delegate.py` launches (#8645). The
driver stays outside it. A runaway worker is killed inside the slice; the driver
and the host services are not in that cgroup.

`MemoryHigh=` is the throttling line and `MemoryMax=` is the last line of
defense, as `systemd.resource-control(5)` recommends. `MemoryMax=` does not cap
swap, so `MemorySwapMax=` is set as well. The unit file in this directory
carries no values: all three are set per deployment, sized for that host, in a
limits drop-in installed next to the unit
(`~/.config/systemd/user/lu-dispatch.slice.d/10-limits.conf`). The same holds
for `lu.slice`. There is no environment override.

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
- After install, `systemctl --user show -p MemoryHigh,MemoryMax,MemorySwapMax,DropInPaths lu-dispatch.slice`
  prints finite values and lists the limits drop-in. A slice without the
  drop-in, or a slice name systemd synthesized, reports `MemoryMax=infinity`
  and does not count.

### Install

Order matters, so the limits never lapse: first the deployment installs the
limits drop-in and verifies with `systemctl --user show` that the effective
values are the intended ones; only then is the value-free unit installed from
the updated checkout, followed by `systemctl --user daemon-reload` before more
workers are dispatched. `dispatch_isolation.py` reads the effective `MemoryMax`
and `MemorySwapMax` at runtime and uses the slice only when both are finite;
otherwise dispatch falls back to plain `Popen` without the slice memory cap.

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

Units are **Linux-native `Type=simple`** processes (the sources server is
`Type=notify`, which also supervises the listener). Do not wrap
`./services.sh start` in `Type=oneshot RemainAfterExit=yes`: that is
launchd-shaped and does not supervise the listener on Linux. macOS still
uses `./services.sh supervise api` / launchd.

Public fixtures use opaque ids `host-teacher` (and mapped `host-job` only when needed).

Available service templates:
- `learn-ukrainian-api.service`: Monitor API service (`scripts/api/main.py`).
- `learn-ukrainian-astro.service`: Astro frontend UI.
- `learn-ukrainian-sources.service`: Sources lookup service, supervised by systemd's watchdog (`Type=notify`, see [Sources MCP server](#sources-mcp-server-call-governor-and-systemd-supervision-10674)).
- `learn-ukrainian-sources-alert.service` and `learn-ukrainian-sources-alert.timer`: its failure notices.
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

### 4. Data Backup (`learn-ukrainian-backup.service` + `.timer`) and Retention (`learn-ukrainian-backup-retention.service` + `.timer`)

- **Frequency**: backup daily at 03:30 UTC (`OnCalendar=*-*-* 03:30:00 UTC`, `Persistent=true`, `RandomizedDelaySec=15min`); retention weekly on Sunday at 05:15 UTC, after that day's backup. Target host: the data host whose checkout holds the live `data/` tree.
- **What it does**: the backup service runs `scripts/orchestration/run_scheduled_backup.sh`, which executes `scripts/backup-data.sh backup --execute` (restic via the rclone remote) and records the outcome in `batch_state/backups/last-run.json`. The retention service uses the same wrapper's `retention` mode to run `scripts/backup-data.sh retention --execute`, applying the operator-approved `--keep-daily 7 --keep-weekly 4 --keep-monthly 6` policy run-aware to the `learn-ukrainian-data` tag only: completed runs are kept or dropped as a unit and snapshots are forgotten by explicit snapshot ID, so a retained receipt never loses a snapshot it references. Other snapshot families in the repository are untouched.
- **Secrets**: both services pass `LU_BACKUP_ENV_FILE=%h/.secrets/learn-ukrainian-backup.env` to the wrapper. The wrapper opens the file once, refuses a symlink, requires a regular file owned by the service user with no group/world write bit, and requires its parent directory to be owned by that user and not group/world-writable. Mode `0600` is recommended for the file. The wrapper sources shell syntax with export enabled, expanding `$HOME` and variable references that systemd `EnvironmentFile=` cannot expand. The file's last command must succeed: sourcing checks its final exit status, so a failed earlier command can be missed. Manual runs can omit `LU_BACKUP_ENV_FILE` when the environment is already populated. Validation and sourcing errors name the variable and condition without its value. The wrapper redacts the configured repository, its rclone spec without the `rclone:` prefix, and the password-file path from both services' output before it reaches the journal. An unsafe or missing configured file fails the backup and writes a failure receipt.
- **Disk safety**: `LU_BACKUP_TMPDIR=@REPO_ROOT@/data/.backup-staging` keeps SQLite staging on the same filesystem as `data/` (gitignored; see `scripts/backup-data.sh` — databases are staged sequentially and each staged copy is deleted before the next). `Nice=15` + `IOSchedulingClass=idle` keep the run off the fast path; `TimeoutStartSec=10800` allows one hour of lock wait plus two hours for backup or retention.
- **Data-volume guard**: the two backup services have drop-ins among the thirteen in `packaging/systemd/dropins/`. Each checks the configured data volume before executing the redacting `run_scheduled_backup.sh` wrapper; a failed guard exits 78 and does not restart. Install the drop-ins as described in `docs/runbooks/storage-topology.md` before enabling the timers on a migrated data host.
- **Failure visibility**: a failed run exits non-zero, and a failed log capture or `last-run.json` write fails the backup service even when the backup succeeded. Monitor's `/api/orient?sections=health` reports `health.backup_last_run.status`, `exit_status`, and `finished_at_utc` from that receipt, so the next morning's health glance shows a failed night. A success older than 26 hours is `stale`, covering a timer or systemd preflight failure before the wrapper starts. `unknown` means the receipt is absent, unreadable, or invalid; check the unit journal. `last-run.json` also carries start/end, run id, snapshot count, and bytes added.
- **Failure alert (change-only)**: both services set `OnFailure=learn-ukrainian-backup-alert@%n.service`. The template runs `scripts/orchestration/backup_failure_alert.py failed <unit>`, which posts one report to the Fleet Comms `cto` channel (`--sender sre-timers --kind report`) and records the unit under `batch_state/backups/alerts/`. Later failures of the same unit stay quiet. Each service's `ExecStartPost=-... recovered %n` runs only after a successful run; it posts one recovery report when the unit was recorded as failing and clears the record. A publish that fails leaves the record unchanged, so the next run retries, and the alert unit shows as failed. `install_backup_timer.py` installs the template with the other four units.
- **Broken and batch_state symlinks**: a dangling symlink under a recovery root (`data/`, `batch_state/`, `.agent/`, `.claude/*-epic`) no longer aborts the backup. It is skipped with a `WARNING: Skipping broken symlink ...` line, excluded from the snapshot, and listed in the receipt's `exclusions` as `<path> broken symlink skipped`. Absolute or escaping symlinks under `batch_state/` (such as temporary test fixtures, mock binaries, and runtime links) are likewise skipped with a warning and excluded from the snapshot so they do not abort the nightly backup. Absolute or escaping symlinks in other recovery roots (`.agent/`, `.claude/*-epic`, `data/`) still fail closed.
- **Backend connections**: `LU_BACKUP_RCLONE_CONNECTIONS` (1-16, default 1) sets the rclone backend connection limit. `restic prune` refuses fewer than two, so prune always uses at least 2, and the retention service sets `LU_BACKUP_RCLONE_CONNECTIONS=2`.
- **Install** (preview by default; writes only with `--apply`):
  ```bash
  .venv/bin/python scripts/orchestration/install_backup_timer.py --repo-root /path/to/primary
  .venv/bin/python scripts/orchestration/install_backup_timer.py --repo-root /path/to/primary --apply --enable
  ```
  After merge, the data-host driver runs the preview and then the `--apply --enable` command from the updated primary checkout to replace both installed service units and reload the user manager. The driver then checks `/api/orient?sections=health` and the next timer-triggered `last-run.json` receipt.

### 5. OpenCode Session Retention (`learn-ukrainian-opencode-retention.service` + `.timer`)

- **Frequency**: daily at 04:15 UTC, with up to 15 minutes of jitter and a persistent catch-up run. Target host: the user account that owns the OpenCode session database.
- **What it does**: deletes a root session and its descendants only when every session in that family was last updated strictly more than seven days ago. `opencode session list --format json` is project-scoped and excludes child sessions, so the job uses a read-only `opencode db` query to list all session IDs, parent IDs, and timestamps in the database, then `opencode session delete` for each selected ID. Children are deleted before parents. A family with an old session and a recent member is skipped and logged with its root ID and newest member's age; unrelated old families are still deleted. It checks that every selected ID is gone and every preserved ID remains. It skips the run when any `opencode` process is active. It logs every deleted ID, checkpoints the WAL through `opencode db`, and logs the main DB and WAL bytes plus SQLite freelist/page counts before and after. It does not issue SQL writes to session tables. Deletion puts pages on SQLite's freelist for later inserts: a successful delete and checkpoint can leave the main DB at its working-set high-water mark while preventing renewed growth from retained old sessions. `VACUUM` is intentionally not run.
- **Preview**: from the primary checkout on the target host, run `"$(pwd -P)/.venv/bin/python" scripts/orchestration/opencode_session_retention.py --dry-run`. Use `--days N` to change the retention window. This preview reads the database through OpenCode's CLI; development tests must use an isolated scratch data directory.
- **Data-volume guard**: install the matching `data-volume.conf` with the unit so the timer checks the configured data volume before retention runs. A failed guard exits 78 and prevents restart.
- **Install, only after operator approval**: from the primary checkout on the target host, render the two templates into the user unit directory, replacing `@REPO_ROOT@` with the absolute checkout path and `@PYTHON@` with that checkout's absolute project interpreter. Verify the rendered units before enabling:
  ```bash
  repo_root=$(pwd -P)
  unit_dir="$HOME/.config/systemd/user"
  mkdir -p "$unit_dir"
  sed -e "s|@REPO_ROOT@|$repo_root|g" -e "s|@PYTHON@|$repo_root/.venv/bin/python|g" \
    packaging/systemd/learn-ukrainian-opencode-retention.service > "$unit_dir/learn-ukrainian-opencode-retention.service"
  cp packaging/systemd/learn-ukrainian-opencode-retention.timer "$unit_dir/"
  mkdir -p "$unit_dir/learn-ukrainian-opencode-retention.service.d"
  sed -e "s|@REPO_ROOT@|$repo_root|g" -e "s|@PYTHON@|$repo_root/.venv/bin/python|g" \
    packaging/systemd/dropins/learn-ukrainian-opencode-retention.service.d/data-volume.conf \
    > "$unit_dir/learn-ukrainian-opencode-retention.service.d/data-volume.conf"
  systemd-analyze verify "$unit_dir/learn-ukrainian-opencode-retention.service" "$unit_dir/learn-ukrainian-opencode-retention.timer"
  systemctl --user daemon-reload
  systemctl --user enable --now learn-ukrainian-opencode-retention.timer
  journalctl --user -u learn-ukrainian-opencode-retention.service -n 30
  ```
  The templates do not install or enable themselves.

## Daily issue quality report

`learn-ukrainian-issue-quality-report.service` runs a counts-only fleet census
and publishes its persisted payload to Fleet Comms. Its independent daily timer
runs at 07:00 UTC with up to five minutes of jitter and catches missed runs.
It does not use the five-minute project-state reporter. Private repositories
contribute counts only and explicit unknown membership. A failed publication
fails the service; retry reuses the day's ignored `batch_state/reports/` payload
and idempotency key.

Preview and verify with
`.venv/bin/python -m scripts.orchestration.install_issue_quality_report_timer --check`.
After landing and approval, use `--apply`, or `--apply --enable` to start the
timer. The installer uses `safe_unit_install` and refuses symlinked destinations.
The data-volume drop-in is installed through the existing drop-in installer.
No unit is installed or enabled by tests or by preparing this source candidate.

## Sources MCP server: call governor and systemd supervision (#10674)

### Call governor (in the server)

`scripts/rag/call_governor.py` bounds the sources server's tool calls. At most 12 tool calls hold a slot at once and the rest queue for up to 30 s; a call with no result after 120 s is answered `Tool call failed: <tool> (call_timeout: ...)`, a call that cannot get a slot `(... server_busy: ...)`. A timed-out call keeps its slot until its worker thread actually finishes (Python cannot kill the thread), so timeouts never let more than 12 calls' work run at once; while every slot is held by such work, new and queued calls are refused at once with `(... server_overloaded: ...)`. The calls' worker threads come from the server's own pool of the slot count plus 4, not Python's default pool (`min(32, CPUs + 4)` threads), so all 12 slots can run on any host and no call's timeout is spent waiting for a thread. Each call logs `call_start`/`call_end` lines (id, tool, in-flight, queued and abandoned counts, outcome, duration; never argument values) to the service log, and a timed-out call a `call_released` line when its work ends. Override the limits with `LU_SOURCES_MAX_CONCURRENT_CALLS`, `LU_SOURCES_QUEUE_TIMEOUT_S` and `LU_SOURCES_CALL_TIMEOUT_S`.

### Readiness and the watchdog

`learn-ukrainian-sources.service` is `Type=notify` with `NotifyAccess=main` and `WatchdogSec=90`. The server (`scripts/rag/sources_supervision.py`, standard library only) sends:

- `READY=1` once, after uvicorn is listening and one health probe has passed;
- `WATCHDOG=1` only after a probe completes inside its deadline.

A probe is one small coroutine on the serving event loop. It enters the real call governor as tool `_watchdog_probe`, then looks up one form on the shared VESUM connection through the governor's executor, taking the same connection lock as every VESUM tool. That connection is where the server deadlocked in #10674 (a Python callback under SQLite's connection mutex). A blocked event loop, a governor whose slots are all held by stuck work, or a held connection lock therefore stop the pings, and systemd treats 90 s without one as a failure. Probes start every 22.5 s (a quarter of the interval) with a 45 s deadline (half), and only one is outstanding: no new probe starts until the previous probe's job has finished. Keep `LU_SOURCES_QUEUE_TIMEOUT_S` below half of `WatchdogSec`, so a probe that waits the whole queue timeout for a slot can still meet its deadline. Each probe logs the governor's `call_start`/`call_end` lines; a failed one also logs `watchdog_probe outcome=deadline|error|still_running`.

Under systemd only: the stdio server, and a standalone server started without `$NOTIFY_SOCKET`, send nothing and arm no dump. The data-volume drop-in's guard `exec`s into the server, so the server keeps the main PID that `NotifyAccess=main` accepts.

### Dump before the kill

On a missed watchdog systemd sends `SIGABRT` (the default `WatchdogSignal=`). At start-up the server armed `faulthandler` on a file it opened in the unit's state directory, so the signal writes every thread's Python stack there and the process dies; after `TimeoutAbortSec=30` systemd sends `SIGKILL` (`SendSIGKILL=yes`, `KillMode=control-group`), then restarts the unit after `RestartSec=5`.

- **Where:** `StateDirectory=learn-ukrainian-sources`, created by systemd with mode 0700: `$XDG_STATE_HOME/learn-ukrainian-sources/` (usually `~/.local/state/...`) under a user manager, `/var/lib/learn-ukrainian-sources/` under the system manager. Files are `abort-<UTC start time>-pid<N>-<random>.txt`, mode 0600. Read the newest non-empty one after a watchdog notice.
- **Bounds:** every server process creates one file, and a fatal signal ends the process, so a file holds at most one dump (faulthandler caps it at 100 threads of 100 frames, under 11 MiB). At start-up the server removes earlier empty files and keeps the newest earlier dumps within 7 files and 21 MiB, so the directory never holds more than 8 dump files or 32 MiB. A file whose lock is held by a live process is never removed, and the directory is opened once without following symlinks; nothing is created or opened by path at crash time.
- **Privacy:** stacks carry file names, line numbers and function names, never argument values. Core dumps are off (`LimitCORE=0`, and the server sets `PR_SET_DUMPABLE` to 0, which also stops a piped `core_pattern` helper), so process memory never leaves the process.
- The directory also holds `ready-invocation`, the systemd invocation id of the last run that became ready, which tells the failure notice a start-up failure from a later one; `notices/`, the failure records (below); and `mcp-sources-requests.jsonl`, the server's request log (`LU_MCP_SOURCES_LOG_DIR`), because the checkout is read-only to the service. Every dump-pruning step and the creation and locking of a new dump file run under an exclusive lock on the directory, so no pruner can remove a new file before its lifetime lock is taken.

### Restart budget

`Restart=on-failure` restarts the server after a watchdog kill, a crash or a non-zero exit (except exit 78, the data-volume guard's refusal, which `RestartPreventExitStatus=78` leaves failed). `[Unit]` limits it with `StartLimitIntervalSec=30min`, `StartLimitBurst=5` and `StartLimitAction=none`.

- systemd counts **starts**, including the first and manual ones, in a **fixed window**: the first start after the previous window ended opens a new 30-minute window, and a sixth start inside it is refused. It is not a rolling count of the last 30 minutes.
- Why these values: the shortest watchdog cycle is about 100 s (start, 90 s without a ping, abort, 5 s delay), so a server that hangs again soon after each start uses up a window's 5 starts within about 8 minutes, and one that crashes during start-up within about a minute. A hang that recurs less often than every 6 minutes keeps being restarted, and every failure sends a notice. systemd's default (5 starts in 10 s) never catches a watchdog cycle.
- **Exhausted:** the unit stays `failed` (`Result=start-limit-hit`); systemd makes no further automatic restart, and time alone does not start it. A `start_limit` notice goes to the `cto` channel. No reboot or other action follows.
- **Recovery is manual:** read the dump and `journalctl --user -u learn-ukrainian-sources.service`, fix the cause, then run `systemctl --user reset-failed learn-ukrainian-sources.service` and `systemctl --user start learn-ukrainian-sources.service` (without `--user` for a system install). `reset-failed` clears the counter at once. Once the window has ended, a manual `start` also succeeds without `reset-failed`, because the next start opens a new window; inside the window, manual starts count against the same 5. Automated resets and starts are prohibited: no timer, script or agent runs `reset-failed` or `start` on this unit to get around the budget.
- **While the server is down:** sources tools fail for every seat that reaches the server over HTTP at `127.0.0.1:8766` (the default `.mcp.json` client and the V7 writer seats), so lookups and VESUM verification wait until it is back, or follow the documented fallbacks in the rules. Formal review seats start their own stdio server and keep working. Monitor's health glance reports `mcp_sources: false`; it only checks the port, so a hung server that still accepts connections reads `true` until the watchdog kills it.

### Failure notices

`scripts/orchestration/sources_failure_alert.py` records and publishes them. No notice depends on a systemd trigger surviving: systemd merges a start request into a run of the same unit that is still going, so a trigger can be lost, and nothing here waits for its own trigger.

- **Episode:** one failed run of the unit (one systemd invocation id), plus, separately, the start-limit refusal that follows the last one. Each episode sends exactly one message. A watchdog kill that systemd then recovers from **does** notify: the server hung and its dump is waiting. The start limit caps them at 5 failure notices per window, plus one start-limit notice that ends the run of restarts until a manual recovery.
- **Recording a failed run** (`ExecStopPost=` of the server unit, `record`): systemd runs it after every run of the server, in that run's own stop path, with the run's `$SERVICE_RESULT` and `$INVOCATION_ID`. It classifies a failure as `watchdog`, `startup` (the run never became ready) or `other` and writes one record into `notices/` under the server's state directory (fsync, then an atomic link, so the same episode keeps its first record). It is local and takes well under a second; it never contacts Fleet Comms or systemd, and its `-` prefix keeps it from failing the unit.
- **Recording the start-limit refusal** (`notify`, below): a refused start runs no server process, so there is no `ExecStopPost=`. Instead, before each scan, the notifier reads the unit's state from systemd (`systemctl [--user] show`: `ActiveState`, `SubState`, `Result`, `InvocationID`; the manager is the one running the notifier) and records a failure the unit is still in. The refusal leaves the unit `failed` until an operator recovers it, so a scan finds it even when its own trigger was merged away. A run that is waiting for its automatic restart is recorded under the same key as its `ExecStopPost=` record, so it is never counted twice.
- **Publishing** (`learn-ukrainian-sources-alert.service`, `notify`, `TimeoutStartSec=300`): started by the server's `OnFailure=` and every 5 minutes by `learn-ukrainian-sources-alert.timer`. It sends every pending record, oldest first, through the backup alert's Fleet Comms publisher (`channel publish cto --sender sre-timers --kind report`) with the idempotency key `lu-sources-alert:v1:<episode>`, then renames it to `<episode>.sent`, which stops the persisting start-limit state from being recorded again (the newest 256 markers are kept). It rescans until nothing new is pending and starts no publish after 150 s. **Exit 0** means nothing is pending; **exit 75** means a record is still pending (its publish failed, or the time ran out before it was tried) and the timer's next run retries it; **exit 1** means the unit state could not be read (pending records were still published). The unit has no start limit of its own (its starts are bounded by the server's start limit and the timer) and no restart loop: the timer is the retry. If the notifier is killed after Fleet Comms stored a message, the retry sends the same bytes with the same key and Fleet Comms keeps one message. At most 64 records wait; beyond that the oldest go.
- **Content:** only the allowlisted fields: schema version, `service=sources`, an opaque episode id (a hash, not the invocation id), the UTC time of the record and the class, plus a fixed sentence per class. For example:

  ```text
  [sources-alert] schema=1 service=sources class=watchdog episode=3f2a...e1 at=2026-10-15T15:00:00Z
  systemd killed the sources MCP server after missed health pings and restarted it; its all-thread stack dump is in the unit's state directory.
  ```

  Exception text, exit details, health bodies, paths and stacks never enter a record or a message; a record with any other field, or a file left by the old watchdog, is deleted unsent.

### Install and rollout (operator-approved only)

The templates do not install themselves.

1. **Read the live install first.** This repository does not record whether the live sources service runs under the user manager or the system manager, or which drop-ins it has. Check with `systemctl --user cat learn-ukrainian-sources.service` (or `systemctl cat ...`) on the host and use the matching manager in every command below.
2. **Check the narrow binds.** The template keeps its restrictions, with the home trees in `ProtectHome=tmpfs` mode: `/home`, `/root` and `/run/user` are covered by empty read-only file systems, and only the paths the server needs are bound back ([systemd.exec(5)](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html#ProtectHome=) documents this mode for exactly that):
   - read-only (`BindReadOnlyPaths=`): the checkout `@REPO_ROOT@`, its virtual environment `@VENV_ROOT@`, and the base interpreter's installation `@PYTHON_ROOT@` (its `bin` and standard library);
   - writable (`BindPaths=`): the data directory `@DATA_ROOT@` only. `sources.db` is a WAL database, and SQLite must create or write its `-shm` file beside it even for a read-only connection; with the directory read-only, opening it fails with `attempt to write a readonly database` whenever no other process holds the database open;
   - the unit's state directory, bound writable by `StateDirectory=`.
   No other path is writable, the checkout stays read-only, and no whole home directory is exposed. From the checkout, run `.venv/bin/python -m scripts.rag.sources_supervision check-paths --repo-root "$(pwd -P)"`. It resolves every path the server needs (checkout, virtual environment, interpreter, standard library, data directory, and the directory of each database it reads), prints each with the setting that exposes it, then prints the four substitutions. Exit 0: every path resolves inside the unit's view. Exit 1: a path is missing, would stay hidden or read-only (`HIDDEN`), or a bind would expose a whole home directory or tree or make the checkout writable (`BROAD`). Do not widen the binds on the host; a layout that fails needs a reviewed change. Under a user manager `ProtectHome=` also implies `PrivateUsers=yes` (unprivileged user namespaces must be enabled), and `ProtectProc=`/`ProcSubset=` are available to system services only.
3. **Render and verify** the server unit, the notifier service and its timer into the manager's unit directory with `.venv/bin/python -m scripts.rag.sources_supervision render --repo-root "$(pwd -P)" packaging/systemd/<unit> > <unit directory>/<unit>` (it runs the same check first and refuses an unknown placeholder), install the data-volume drop-ins with `scripts/storage/install_data_volume_dropins.py`, then run `systemd-analyze [--user] verify` on the rendered files (it reports problems as warnings while still exiting 0, so read its output), `systemctl [--user] daemon-reload`, `systemctl [--user] enable --now learn-ukrainian-sources-alert.timer` and `systemctl [--user] restart learn-ukrainian-sources.service`. Check `systemctl [--user] show -p Type,WatchdogUSec,NRestarts learn-ukrainian-sources.service`, the journal's `sd_notify ready` line and a successful sources tool call.
4. **One supervisor only.** This repository ships no `learn-ukrainian-sources-watchdog` unit (a test enforces it). A host that ever installed the parked custom watchdog's `learn-ukrainian-sources-watchdog.service` and `.timer` must stop, disable and delete them, then reload the manager, before native supervision goes live, so two supervisors never act on the same server.
5. **Live drill:** dump, kill, restart, start-limit failure, notices, manual recovery and a successful MCP tool call afterwards need separate CTO consent; the unit tests run without a service manager.
