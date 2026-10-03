# Driver memory scopes

Every real driver route enters a unique `lu-driver-<provider>-<lane>-<uuid>.scope`
in the user manager's `lu-driver.slice` before rules loading, provider preparation,
deploy, rollover import or lease acquisition. Normal, untrusted and governor
routes share this boundary. Help and dry-run do not contact the manager.

`scripts/lib/driver_scope.sh` is the single per-session configuration point:
`MemoryHigh=3 GiB`, `MemoryMax=5 GiB`, `MemorySwapMax=1 GiB`, with explicit
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

## Sizing evidence and rule

A read-only measurement on 2026-10-03 followed the process trees of five live
`start-*-driver.sh` launchers, retaining descendants in the launcher's cgroup
and excluding dispatched workers in other cgroups. Summed `/proc/<pid>/status`
`VmHWM` values were **877608, 601660, 673512, 1559928 and 707568 KiB**.
One-process heartbeat subshells (3444–3644 KiB) were not counted as separate
sessions. The largest measured living-tree high-water envelope is
1559928 KiB = about 1.488 GiB.

Use `MemoryHigh = ceil(2 × envelope / GiB) GiB`, `MemoryMax =
ceil(3 × envelope / GiB) GiB`; this gives 3/5 GiB. The swap budget is one third
of MemoryHigh (1 GiB). This rule gives reclaim headroom and a larger emergency
ceiling without copying the contaminated terminal-scope peaks. These are
process high-water measurements, **not complete session cgroup peaks**: exited
tools, page cache and persistent shared-memory charges are not captured. A
healthy-session soak must measure the new cgroups' `memory.peak` and
`memory.swap.peak` before claiming production sizing validated. Ownership of
that sizing confirmation remains with the DevOps driver.

`LU_DRIVER_MEMORY_HIGH`, `LU_DRIVER_MEMORY_MAX` and
`LU_DRIVER_MEMORY_SWAP_MAX` accept decimal byte values to **lower** the limits
for a bounded test. High must be positive and strictly below Max; Max and swap
cannot exceed the configured defaults. Effective values are logged. Changing
production ceilings requires updating this configuration and its sizing proof.

## Install after review

From the reviewed checkout, in the operator's user session:

```bash
install -d -m 0700 "$HOME/.config/systemd/user"
install -m 0644 packaging/systemd/lu-driver.slice "$HOME/.config/systemd/user/lu-driver.slice"
systemctl --user daemon-reload
systemctl --user show lu-driver.slice -p LoadState -p FragmentPath
```

No enable step is needed: transient scopes activate the slice. No system unit,
linger setting, service unit or dispatch limit is changed. No `lu.slice` pool
cap is included. The accountable driver installs after independent review.

## Death and admission behavior

`OOMPolicy=continue` prevents systemd from terminating every survivor after a
kernel OOM victim, but does not guarantee which process survives. If the
provider dies, the existing launcher closes its lease and preserves its exit
status. If the launcher dies, renewal stops when its owner is gone and the
existing TTL/expiry path recovers the lease; no early reclaim is introduced.

Plain dispatch fallback inside a driver scope is refused with
`fallback-refused: inside-driver-scope`. No harness has a validated bounded
fallback exemption. Missing caller cgroup evidence also refuses fallback.
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
[scope OOM policy](https://raw.githubusercontent.com/systemd/systemd/v259/man/systemd.scope.xml),
[kernel memory accounting](https://docs.kernel.org/admin-guide/cgroup-v2.html#memory-interface-files).
