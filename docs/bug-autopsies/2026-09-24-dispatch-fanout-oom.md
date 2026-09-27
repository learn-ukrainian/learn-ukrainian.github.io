# Bug Autopsy: dispatch fan-out OOM killed the infra driver and its workers

Issue: #8645 (2026-09-24).

## Timeline

On 2026-09-24 at 09:13:56Z the kernel OOM killer fired on this 15 GB host
(`global_oom`). The victim was in the infra driver's tmux pane scope
(`tmux-spawn-b8ae538c-….scope`). systemd then failed the whole scope
(`Failed with result 'oom-kill'`). The scope's peak was 12.9 GB of memory
and 6.3 GB of swap.

Everything in that scope died at once: the infra driver session and all
eight dispatch workers (`impl-8638-r5`, `impl-8514-deepseek-start`,
`impl-8593-acp-transports`, `impl-8505-ci-triggers`,
`impl-8508-finalize-rescue`, `impl-8540-r2`, `review-8624`,
`review-8502`). They stayed `running` in `batch_state/tasks/` until a
status probe marked them `crashed` 40 minutes later. Five of them left
uncommitted work in their worktrees.

Kernel report, largest resident sets at kill time:

- one cluster of 9 contiguous `python` pids (486666–486687), one
  pytest-xdist run: 1957 + 782 + 720 + 649 + 617 + 614 + 583 + 473 MB
  ≈ 6.4 GB
- two more pytest pairs (837524/837567, 842874/842881): ≈ 2.2 GB
- agent CLIs (claude, agy, kimi-code, codex): 100–240 MB each

A contributing cause was in the driver's own brief:
`.claude/infra-epic/briefs/impl-8638-r5.md` step 4 told the worker to run
the whole suite once (`-n auto` is fine). Worker `impl-8638-r5` (pid
473252) started just before the 486666–486687 xdist cluster that held
about 6.4 GB.

## Root cause

Three gaps, all present at the same time:

1. **No memory admission.** `delegate.py dispatch`, `capacity_pick`, and
   the §2c admission codes check quota, disk, and WIP, but nothing reads
   `MemAvailable`. The driver's "~8 concurrent" estimate was based on core
   count, not memory. A `MemAvailable` snapshot alone is also TOCTOU:
   workers admitted one after another can each pass the floor and then
   balloon together.
2. **Unbounded xdist fan-out.** Each worker picks its own `pytest -n`
   (`auto` or 8 is common). N workers × 8 xdist processes × 0.5–2 GB each
   goes past 15 GB well before N = 8. One `-n auto` full run was the
   ≈6.4 GB cluster above, prompted by that driver brief.
3. **Workers share the driver cgroup.** `start_new_session=True` detaches
   the process group but not the cgroup. One runaway pytest takes down the
   driver session and every sibling worker. Other lanes' workers in other
   panes survived.

Measured the same morning (2026-09-24 10:00–11:00Z): 5–7 concurrent workers,
all using targeted tests with `-n 2`, kept `MemAvailable` between 11.1 and
13.5 GB. The OOM needed full-suite `-n auto` runs.

## Fix plan

Driver disposition (claude-infra), reconciling the Codex and Kimi design
seats. Three PRs, in this order:

1. **B — test fan-out cap** (`tests/conftest.py` / pytest hook): when the
   dispatch env marker is set, clamp xdist to `--maxprocesses=2` (explicit
   `-n`, `-n auto`, and `-n logical`) and make full-suite runs take one
   host-wide lock, acquired before the session starts. Lands after #8641.
2. **A — admission plus liveness** (`delegate.py dispatch`,
   `scripts/config.py`): a static cap on live write workers (default 5,
   configurable) plus a `MemAvailable` floor (default 3.5 GiB), both
   reported in `capacity_pick`; per-worker peak RSS recorded in the task
   record; a liveness sweep that marks a dead pid `crashed` within one
   sweep interval. Lands after #8508.
3. **C — isolation (landed):** a single `lu-dispatch.slice` for all workers
   (`MemoryMax=11G`, `MemoryHigh=10G`, `MemorySwapMax=1G`; unit file
   `packaging/systemd/lu-dispatch.slice`), driver outside it. Each detached
   worker is `systemd-run --user --scope --expand-environment=no --slice=lu-dispatch.slice
   --unit=lu-worker-<task>-<nonce>-<8 hex> --collect`. `--scope` execs the
   worker in place, so the dispatch pid, pipes, and cancel signal stay the
   worker's. The 8 hex characters are new on every launch, so a reused nonce
   cannot collide with a unit systemd still has registered. If the user
   manager, cgroup2 memory delegation, the slice limits, or linger is missing,
   or if `systemd-run` exits before the worker writes its start marker, or
   is still `systemd-run` when the startup window ends, dispatch stops that
   process, falls back to plain Popen, prints one warning, and records
   `launch_mode` (`scope` or `popen-fallback`) on the task record. If the
   process image is already the worker, that process is kept. A marker that
   arrives only as that process is stopped, or a `/proc` image that cannot be
   read, fails the dispatch instead of relaunching. Running without the slice
   installed is supported. Per-worker limits stay out
   until sibling starvation shows up.

Parts A and B have landed (admission, liveness, the pytest fan-out cap).
Part C is in the launcher; the slice limits apply only after
`packaging/systemd/lu-dispatch.slice` is installed in the user manager.
Until that install, and whenever the probe falls back, keep the driver
rule that survived the incident: targeted tests only, `-n 2` at most.

## Detection and lessons

The workers stayed `running` for 40 minutes because nothing probed pid
liveness on a sweep interval; a status probe was the first thing that
marked them `crashed`. A worker limit cannot prevent every global or
ancestor-cgroup OOM, and `MemoryMax` does not cap swap — the scope used
6.3 GB of swap — so isolation has to set `MemorySwapMax` as well.

Briefs that say "run the whole suite once (`-n auto` is fine)" are enough
to start the cluster. The cap has to hold when a brief gets that wrong:
targeted tests, `-n 2` at most, full suite in CI, and a second full-suite
run on a dispatch host fails before it executes any test.
