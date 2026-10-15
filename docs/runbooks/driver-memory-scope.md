# Driver and interactive session memory scopes

Every real launcher session enters a unique scope in the user manager's
`lu-driver.slice` before rules loading, provider preparation, deploy, rollover
import or lease acquisition (#9624). That covers every driver route (normal,
untrusted and governor), every interactive and compatibility wrapper
(`start-claude.sh`, `start-codex.sh`, `start-gemini.sh`, `start-grok.sh`,
`start-kimi.sh`, `start-kimicc.sh`, `start-glm.sh`, `start-glmcc.sh`) and
`scripts/start-bio-driver.sh`. Driver units are
`lu-driver-<provider>-<lane>-<uuid>.scope`. Interactive units are
`lu-interactive-<provider>-<label>-<uuid>.scope`, where the label names the
invoked wrapper (`claude`, `codex`, `gemini`, `grok`, `kimi`, `kimicc`, `glm`,
`glmcc` or `bio`), so a journal OOM record names the session's route.
Interactive sessions get the same limits in the same slice as drivers; there is
no separate sub-slice. Lease claim and renewal, rollover import, adapter
prelease, provider canary and supervisory start-failure publication stay
driver-only, whatever an interactive session inherits. Help and dry-run do not
contact the manager.

`scripts/lib/driver_scope.sh` is the single per-session configuration point. It
sets `MemoryHigh=`, `MemoryMax=` and `MemorySwapMax=` from the deployment's
configuration (see [Limits are set per deployment](#limits-are-set-per-deployment)),
with explicit `OOMPolicy=continue`. Limits are read back from the actual cgroup; unit ID,
ControlGroup, Slice, ActiveState and OOMPolicy must agree. Re-entry requires the
same launcher PID and verified unit. A nested launch gets a new UUID and scope.

The outside shell only waits. Scope mode preserves the terminal, stdin and
process group; for drivers the existing inner launcher supervises the provider,
renewal and lease cleanup, and an interactive launcher replaces itself with the
provider. The command's status, including the earlier refusal codes, propagates.
Failure to enter or verify returns 6 and a typed `DRIVER_SCOPE_REFUSED
reason=...` for drivers and interactive sessions alike. There is no unbounded
override. Restore the user manager/bus and install the unit; do not bypass this
boundary. The helper derives a missing runtime directory only from the current
user's owned logind directory and bus socket. Headless tool shells, cron and
service callers must have access to that user's manager; an inaccessible manager
is a refusal. Before starting a scope, `lu-driver.slice` must report both
`LoadState=loaded` and a non-empty `FragmentPath`. A loaded implicit slice with
no unit file is refused as `slice-not-installed` before preparation or lease
acquisition.

Admission refusals keep their own codes and come before any manager contact:
usage errors (2), certification and Muse refusals (4), uncertified Gemini driver
models (4) and the Claude weekly cap or Opus block (7). Refusals after entry,
such as an adapter preflight, keep their codes too, but run inside the scope.

## Entry, replay and identity

Entry starts `systemd-run --scope`, which runs the entry helper and then
replays the wrapper the caller invoked, with the caller's arguments byte for
byte. The wrapper is the invoked script itself, resolved inside the checkout and
checked against the tracked allowlist in `driver_scope.sh`, never a name derived
from the provider: `start-glmcc.sh` must not become `start-glm.sh`, which selects
another route. Arguments a wrapper adds itself (the CTO lane, the kimicc harness,
the bio agent) are kept out of the replayed arguments, so the replayed wrapper
adds them exactly once.

The entry helper verifies the unit against the launcher's validated mode; the
replayed wrapper verifies it again against its own mode, provider and label.
Typed refusals: `entrypoint-not-allowlisted` (a copy, alias or other script
calling the shared core, which cannot be replayed), `entrypoint-mismatch` (a
tracked name running another provider or mode), `mode-mismatch` and
`identity-mismatch`.

## Signals and the terminal

Drivers: INT, TERM and HUP are forwarded; when trapped, their conventional
statuses (130, 143 and 129) replace the inner status. SIGQUIT remains ignored
throughout the scoped driver tree because Bash launches the scope wrapper as a
background job without job control.

Interactive sessions: the provider shares the terminal's foreground process
group, so a keyboard INT or QUIT reaches it directly, exactly once. The waiting
launcher relays INT and QUIT only when its process group is not the terminal's
foreground group, for example a session without a terminal. TERM and HUP are
relayed. The provider keeps the default QUIT disposition, as with direct
execution. The status is the provider's own unless the launcher relayed a
signal (130, 143, 129 or 131). Window resizes and terminal suspend/resume reach
the whole job.

Known limits, each with a test or listed as untested: a terminal Ctrl-C reaches
a driver's provider twice, once from the terminal and once from the supervisor
shell (`test_driver_keyboard_interrupt_reaches_the_provider_exactly_once`,
expected failure, owned by DevOps). A provider that suspends only its own process
leaves the waiting launcher running, so the shell regains the terminal only on
a second Ctrl-Z (untested with a real TUI).

## Nesting

A launch from inside a driver or interactive scope gets a new sibling scope in
`lu-driver.slice`; its memory then counts against its own scope, not the
parent's. A launch from inside `lu-dispatch.slice` is refused as
`inside-dispatch-slice` before any manager contact, so a worker cannot leave its
slice's cap; an unreadable caller cgroup is refused as
`caller-cgroup-unavailable`. Dispatch from an interactive session behaves as from
a driver: bounded worker scopes start, and the unbounded fallback is refused.

## Entry marker ownership

The waiting launcher opens separate read and write descriptors for the entry
marker and immediately unlinks its temporary name. The entry helper inherits
the write descriptor, writes `verified` after successful verification, closes
it, then replaces itself with the launcher. The waiting owner reads that exact
marker through its retained descriptor when the child exits. It preserves the
child's status even if a sibling removed or hid the former pathname.

Configuration or containment verification failures write a refusal marker and
exit 6; the waiting launcher preserves that refusal without publishing a
successor-start failure. An absent verified/refusal marker is
`scope-start-failed`. Only a supervisory driver successor with a captured
predecessor generation publishes that status, after refusal and before exit 6;
an interactive session never publishes, even with inherited supervisor
variables. This path
never prepares a provider, claims a lease, closes a lease, or retries entry.
See [supervisory wake status](session-supervisor.md#supervisory-wake-ownership-and-failure-status).

## Limits are set per deployment

The public tree carries no host sizing. Each deployment sets its own limits,
sized from measurements on that host, and keeps the numbers and the sizing
evidence in its private operations docs.

Per-session driver limits come from, in order:

1. the environment: `LU_DRIVER_MEMORY_HIGH`, `LU_DRIVER_MEMORY_MAX`,
   `LU_DRIVER_MEMORY_SWAP_MAX` (decimal bytes) and `LU_DRIVER_PYTEST_MAX_WORKERS`;
2. the deployment config file, `LU_DRIVER_SCOPE_CONFIG` or by default
   `${XDG_CONFIG_HOME:-$HOME/.config}/learn-ukrainian/driver-scope.env`. It holds
   `KEY=VALUE` lines with the same four keys and is parsed, never sourced. Other
   keys and malformed lines are ignored;
3. built-in generic fallbacks. They are deliberately conservative and are not
   sized for any host, so a deployment that relies on them gets tight limits,
   not loose ones.

High must be positive and strictly below Max. Max cannot exceed the host's
physical memory (`MemTotal`) and swap cannot exceed Max, so there is no
unbounded override. Effective values are logged at scope entry. Use values
aligned to the host's memory page size: the kernel rounds unaligned values, and
exact read-back verification then refuses them as `limits-mismatch`.

Sizing rule for deployments: take the session upper bound plus the measured
child-workload cgroup peak (`memory.peak`) as the envelope, set `MemoryHigh` to
the envelope rounded up and `MemoryMax` to about one and a half times the
envelope, and keep swap small. Do not use swap to make the resident-memory
budget look sufficient. Re-measure `memory.peak`, `memory.swap.peak` and
`memory.events` for each new workload. Raising a per-driver ceiling does not
establish safe concurrency or a shared-pool cap.

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

`lu.slice` is the shared pool (#9624) and `lu-dispatch.slice` has its own cap.
The unit files in `packaging/systemd/` carry no memory or swap values: each
deployment installs a limits drop-in (`<unit>.d/10-limits.conf` next to the
installed unit) with its own `MemoryHigh=`, `MemoryMax=` and `MemorySwapMax=`.
Install the drop-ins and verify them with `systemctl --user show` **before**
installing a unit file without values, so the live limits never lapse. Install,
check and undo `lu.slice` only through the helper, from the reviewed checkout:

```bash
scripts/ops/lu_slice_apply.sh check     # needs the limits drop-in; refuses (exit 4) if memory.current is above its MemoryMax, warns at or above MemoryHigh
scripts/ops/lu_slice_apply.sh apply     # check, install the unit, daemon-reload, verify the cgroup files equal the drop-in values
scripts/ops/lu_slice_apply.sh rollback  # lift the cap at once, remove the unit and control drop-ins, verify max
systemctl --user show lu.slice -p LoadState -p FragmentPath -p MemoryHigh -p MemoryMax -p MemorySwapMax
```

`check` and `apply` read the expected values from `systemctl --user show
lu.slice`, and refuse (exit 7, `limits-dropin-missing`) unless a
`lu.slice.d/*.conf` drop-in next to the installed unit is loaded and all three
values are finite. `apply` runs `check` first. A slice limit change via
`daemon-reload` updates the cgroup in place and does not restart or stop running
scopes. If the reload does not reach the live cgroup, `apply` falls back to
`systemctl --user set-property --runtime` with the same values.

`rollback` runs `systemctl --user set-property --runtime lu.slice
MemoryHigh=infinity MemoryMax=infinity MemorySwapMax=infinity` first, so the cap
lifts immediately, then removes the installed `lu.slice` unit, its limits
drop-ins and the `lu.slice.d` control drop-ins under both `systemd/user.control` locations (the
persistent one in the user config directory and the runtime one under
`$XDG_RUNTIME_DIR`), runs `daemon-reload`, and verifies that `memory.high`,
`memory.max` and `memory.swap.max` read `max`. Without removing the control
drop-ins, a runtime override would keep the cap in force until reboot. The
deployment tooling reinstalls the limits drop-in on its next run, so disable
that first if the rollback must stick.

Inside a driver or interactive scope, `scripts/lib/driver_scope.sh` exports
`PYTEST_XDIST_AUTO_NUM_WORKERS` capped at `LU_DRIVER_PYTEST_MAX_WORKERS` (set per
deployment, conservative generic fallback; an inherited value from zero up to the
cap is kept), so `pytest -n auto` and `-n logical` stay within the cap. An explicit
`-n <number>` is not rewritten. CI does not enter a driver scope and keeps its
own worker count.

## Death and admission behavior

`OOMPolicy=continue` prevents systemd from terminating every survivor after a
kernel OOM victim, but does not guarantee which process survives. If the
provider dies, the existing launcher closes its lease and preserves its exit
status. If the launcher dies, renewal stops when its owner is gone and the
existing TTL/expiry path recovers the lease; no early reclaim is introduced.
An interactive session has no lease; its exit status is the provider's.

Plain dispatch fallback inside a driver or interactive scope is refused with
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
It also checks the shared `lu.slice` pool (#9975): a new write worker is
refused when the pool's non-cache use (`memory.current` minus `active_file` and
`inactive_file` from `memory.stat`) plus the configured per-worker reserve
(`DISPATCH_WORKER_MEM_RESERVE_GIB`) would exceed `memory.high` (`memory.max`
only when `memory.high` is the literal `max`). The nightly data tier runs two
separate checks, each requiring a fixed headroom: for `lu-dispatch.slice` it subtracts
non-cache use from the slice's systemd `MemoryMax`, and for `lu.slice` it uses
the same pool check as admission, against `memory.high`. Without the cgroup
files, or with a `memory.high`/`memory.max` that is neither a number nor `max`,
the pool check is skipped and the reason appears in the admitted line and in a
warning (admission) or on stderr (data tier).
Persistent charges therefore remain visible after a writer exits. Samples are
observations, not reservations or guarantees against concurrent growth.

## Containment proof and residuals

The live soak is an opt-in test, never part of CI:
`LU_RUN_DRIVER_SCOPE_SOAK=1 .venv/bin/python -m pytest -q
tests/test_launcher_driver_scope.py::test_bounded_live_scope_soak
tests/test_launcher_interactive_scope.py::test_bounded_live_interactive_scope_soak`.
It uses a throwaway scope with `MemoryHigh` 128M, `MemoryMax` 192M and swap 0,
refuses to start while the one-minute load is above 18, while another soak holds
its lock (one run at a time) or without twice the scope's maximum free in the
`lu.slice` pool, so it never fills the live pool. The synthetic allocator reads
its scope's three limits back and checks them before it allocates anything.
Use the real launcher with a synthetic provider; raise only the hog's OOM
score so the cleanup shell is likely to survive. Require SIGKILL, an OOM record
for the exact unit, normal launcher cleanup and the provider's exit status.
Compare all four shared services' MainPID, memory, invocation ID, restart count
and OOM counters before/after. A memory sample can vary during normal service
activity; identity/restart/OOM evidence must remain unchanged. Never run the
allocator outside its verified finite scope.

The four services are siblings in `app.slice`, outside driver and worker
scopes. Without the separately approved shared parent cap, aggregate session
and worker growth can still cause global pressure. A future parent OOM can
choose another driver, interactive session or worker before the growing
session's own maximum is reached; per-session maxima do not prevent sibling
victims at a parent limit. Interactive sessions now share the `lu.slice` pool
with drivers and workers, so this pool-level failure mode applies to them as
well: an interactive session can be the victim of another session's growth.
Test parent saturation separately after its cap is approved.

Escape classes remain uncontained: login shells, terminal-multiplexer panes
started outside a launcher (including new panes created through an existing
multiplexer server) and ad hoc commands run from them. The operator owns that
residual. Repository detached jobs are a separate step of #9624. Per-session
containment does not complete the whole issue denominator.

References: [systemd-run](https://raw.githubusercontent.com/systemd/systemd/v259/man/systemd-run.xml),
[memory controls](https://raw.githubusercontent.com/systemd/systemd/v259/man/systemd.resource-control.xml),
[scope OOM policy](https://raw.githubusercontent.com/systemd/systemd/v259/man/systemd.scope.xml),
[kernel memory accounting](https://docs.kernel.org/admin-guide/cgroup-v2.html#memory-interface-files).

<!-- CodeQL retrigger after 2026-10-07 GitHub outage; no content change. -->
