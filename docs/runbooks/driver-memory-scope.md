# Driver memory scopes

Every real driver route enters a unique `lu-driver-<provider>-<lane>-<uuid>.scope`
in the user manager's `lu-driver.slice` before rules loading, provider preparation,
deploy, rollover import or lease acquisition. Normal, untrusted and governor
routes share this boundary. Help and dry-run do not contact the manager.

`scripts/lib/driver_scope.sh` is the single per-session configuration point:
`MemoryHigh=6 GiB`, `MemoryMax=9 GiB`, `MemorySwapMax=1 GiB`, with explicit
`OOMPolicy=continue`. Limits are read back from the actual cgroup; unit ID,
ControlGroup, Slice, ActiveState and OOMPolicy must agree. Re-entry requires the
same launcher PID and verified unit. A nested driver gets a new UUID and scope.

The outside shell only waits and forwards signals. Scope mode preserves the
terminal, stdin and process group; the existing inner launcher supervises the
provider, renewal and lease cleanup. The command's status (including refusal
codes 1–5) propagates. Failure to enter or verify returns 6 and a typed
`DRIVER_SCOPE_REFUSED reason=...`. There is no unbounded override. Restore the
user manager/bus and install the unit; do not bypass this boundary. The helper
derives a missing runtime directory only from the current user's owned logind
directory and bus socket. Headless tool shells, cron and service callers must
have access to that user's manager; an inaccessible manager is a refusal.
Before starting a scope, `lu-driver.slice` must report both `LoadState=loaded`
and a non-empty `FragmentPath`. A loaded implicit slice with no unit file is
refused as `slice-not-installed` before preparation or lease acquisition.

SIGQUIT remains ignored throughout the scoped tree because Bash launches the
scope wrapper as a background job without job control. INT, TERM and HUP are
forwarded; when trapped, their conventional statuses (130, 143 and 129) replace
the inner status. An ordinary unsignalled exit preserves the provider's status.

## Sizing evidence and rule

The original 3/5 GiB defaults used summed living-process `VmHWM` samples
whose largest envelope was about 1.488 GiB. Those samples exclude exited
children, page cache and persistent charges. They do not establish a safe
ceiling for drivers that run local pytest or builds. The observed session-tree
range supplied for sizing is 0.4–4.5 GiB, including existing children; retain
4.5 GiB as a conservative session envelope and reserve another child workload
in addition. This can double-count existing tools, deliberately leaving room
for a new local command.

On 2026-10-03, a foreground `pytest -n 2` run of 34 explicit launcher and
isolation test files (2,295 items) ran under a verified finite user scope:
High=5 GiB minus 40 KiB, Max=5 GiB, swap=0. Its cgroup `memory.peak` was
**906801152 bytes (0.845 GiB)**, `memory.swap.peak` was **0**, and every
`memory.events` counter was **0**, including High, Max and OOM events. The
measurement includes the pytest coordinator, two xdist workers and descendants
remaining in that scope; launched drivers enter their own bounded sibling
scopes and are accounted separately. The measurement scope accidentally used
the production driver namespace, triggering 80 fallback refusals in
tests that inherited the caller's ambient cgroup. That run is sizing evidence,
not a passing validation run. Tests now inject caller-scope detection through
the shared autouse fixture, with explicit inside/outside fallback cases and
production cgroup-reading coverage. Production still reads the real caller's
cgroup and refuses fallback inside a driver scope; the test selection can run
inside the production driver namespace without changing those semantics.

The final neutral-scope rerun, after the fixture and ceiling changes, passed
**2,291 tests**, with eight skips (the opt-in OOM soak and seven sparse-tree
dependencies). It collected 2,299 items and peaked at **799076352 bytes
(0.744 GiB)**, with zero swap and zero memory-event counters. Keep the larger
0.845 GiB diagnostic peak for the reserve. The bounded live OOM soak and
launcher-death renewal regression were then run explicitly: **2 passed**.
The tracked project tree was materialized for a targeted follow-up (three
passed, seven skipped); the remaining content guards also require the
untracked lexicon-data directory, which Git cannot materialize. They remain
for the full-checkout CI run; no empty directory or fabricated data was used.

Use `envelope = session upper bound + measured child-workload cgroup peak`,
`MemoryHigh = ceil(envelope / GiB) GiB`, and
`MemoryMax = ceil(1.5 × envelope / GiB) GiB`. Here the combined envelope is
5.345 GiB, giving **6/9 GiB**. Keep the swap ceiling at **1 GiB**; do not use
swap to make the resident-memory budget appear sufficient. These finite
ceilings reserve local-command space and retain emergency headroom, but do
not guarantee that every large selection or build fits.

A successful representative V7 build and a healthy full driver-session cgroup
soak remain required before claiming general production sizing validated.
Measure `memory.peak`, `memory.swap.peak` and `memory.events` for each new
workload; update the envelope if it exceeds this sample. The DevOps driver
owns that confirmation and aggregate admission/capacity review. Raising a
per-driver ceiling does not establish safe concurrency or a shared-pool cap.

`LU_DRIVER_MEMORY_HIGH`, `LU_DRIVER_MEMORY_MAX` and
`LU_DRIVER_MEMORY_SWAP_MAX` accept decimal byte values to **lower** the limits
for a bounded test. High must be positive and strictly below Max; Max and swap
cannot exceed the configured defaults. Effective values are logged. Changing
production ceilings requires updating this configuration and its sizing proof.
Use values aligned to the host's memory page size: the kernel rounds unaligned
values, and exact read-back verification then refuses them as `limits-mismatch`.

## Install after review

From the reviewed checkout, in the operator's user session:

```bash
install -d -m 0700 "$HOME/.config/systemd/user"
install -m 0644 packaging/systemd/lu-driver.slice "$HOME/.config/systemd/user/lu-driver.slice"
systemctl --user daemon-reload
systemctl --user show lu-driver.slice -p LoadState -p FragmentPath
```

No enable step is needed: transient scopes activate the slice. No system unit,
linger setting, service unit or dispatch limit is changed. The accountable
driver installs after independent review.
The read-back must show `LoadState=loaded` and a non-empty `FragmentPath`;
`LoadState=loaded` alone does not prove that the unit file is installed.

`lu.slice` is the shared pool (#9624): `MemoryHigh=24G`, `MemoryMax=26G`,
`MemorySwapMax=4G` (read back as 25769803776, 27917287424 and 4294967296).
`lu-dispatch.slice` keeps its own 20G cap. Install, check and undo it only
through the helper, from the reviewed checkout:

```bash
scripts/ops/lu_slice_apply.sh check     # refuses (exit 4) if lu.slice memory.current > 26G; warns at >= 24G
scripts/ops/lu_slice_apply.sh apply     # check, install the unit, daemon-reload, verify the cgroup files
scripts/ops/lu_slice_apply.sh rollback  # lift the cap at once, remove the unit and control drop-ins, verify max
systemctl --user show lu.slice -p LoadState -p FragmentPath -p MemoryHigh -p MemoryMax -p MemorySwapMax
```

`apply` runs `check` first. A slice limit change via `daemon-reload` updates the
cgroup in place and does not restart or stop running scopes. If the reload does
not reach the live cgroup, `apply` falls back to `systemctl --user set-property
--runtime` with the same values.

`rollback` runs `systemctl --user set-property --runtime lu.slice
MemoryHigh=infinity MemoryMax=infinity MemorySwapMax=infinity` first, so the cap
lifts immediately, then removes the installed `lu.slice` unit and the
`lu.slice.d` control drop-ins under both `systemd/user.control` locations (the
persistent one in the user config directory and the runtime one under
`$XDG_RUNTIME_DIR`), runs `daemon-reload`, and verifies that `memory.high`,
`memory.max` and `memory.swap.max` read `max`. Without removing the control
drop-ins, a runtime override would keep the cap in force until reboot.

Inside a driver scope, `scripts/lib/driver_scope.sh` exports
`PYTEST_XDIST_AUTO_NUM_WORKERS=8` (an inherited 0–8 value is kept), so
`pytest -n auto` and `-n logical` start at most 8 workers. An explicit
`-n <number>` is not rewritten. CI does not enter a driver scope and keeps its
own worker count.

## Death and admission behavior

`OOMPolicy=continue` prevents systemd from terminating every survivor after a
kernel OOM victim, but does not guarantee which process survives. If the
provider dies, the existing launcher closes its lease and preserves its exit
status. If the launcher dies, renewal stops when its owner is gone and the
existing TTL/expiry path recovers the lease; no early reclaim is introduced.

Plain dispatch fallback inside a driver scope is refused with
`fallback-refused: inside-driver-scope`. No harness has a validated bounded
fallback exemption. Missing caller cgroup evidence also refuses fallback.
This caller check precedes `allow_fallback`, so missing or unverifiable cgroup
evidence can refuse fallback even outside a driver scope or hide an earlier
startup reason. Dispatch records these refusals as `dispatch_fallback_refused`
with `worker process was not started`, retaining the detail in `stderr_excerpt`.
Successful dispatch scopes continue under `lu-dispatch.slice`.

The launcher reports live parent `memory.current` and `memory.swap.current`.
Dispatch admission reads `memory.current`, `memory.max`, `memory.swap.current`
and `memory.swap.max` from the manager's actual slice cgroup on every sample.
Persistent charges therefore remain visible after a writer exits. Samples are
observations, not reservations or guarantees against concurrent growth.

## Containment proof and residuals

A soak must first verify a test scope's finite memory and swap limits before
starting a synthetic allocator (for example High=384 MiB, Max=512 MiB, swap=0).
Use the real launcher with a synthetic provider; raise only the hog's OOM
score so the cleanup shell is likely to survive. Require SIGKILL, an increase
in the scope's `memory.events` `oom_kill`, normal launcher cleanup and the
provider's exit status. Compare all four shared services' MainPID, memory,
invocation ID, restart count and OOM counters before/after. A memory sample
can vary during normal service activity; identity/restart/OOM evidence must
remain unchanged. Never run the allocator outside its verified finite scope.

The four services are siblings in `app.slice`, outside driver and worker
scopes. Without the separately approved shared parent cap, aggregate driver
and worker growth can still cause global pressure. A future parent OOM can
choose another driver or worker before the growing driver's own maximum is
reached; per-driver maxima do not prevent sibling victims at a parent limit.
Test parent saturation separately after its cap is approved.

Interactive shells and terminal-multiplexer panes started outside a launcher,
including new panes created through an existing multiplexer server, remain
uncontained. The operator owns that residual. Per-driver containment does not
complete the whole issue denominator.

References: [systemd-run](https://raw.githubusercontent.com/systemd/systemd/v259/man/systemd-run.xml),
[memory controls](https://raw.githubusercontent.com/systemd/systemd/v259/man/systemd.resource-control.xml),
[scope OOM policy](https://raw.githubusercontent.com/systemd/systemd/v259/man/systemd.scope.xml),
[kernel memory accounting](https://docs.kernel.org/admin-guide/cgroup-v2.html#memory-interface-files).

<!-- CodeQL retrigger after 2026-10-07 GitHub outage; no content change. -->
