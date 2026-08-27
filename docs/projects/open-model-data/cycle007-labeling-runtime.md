# Cycle 007 resumable labeling runtime

Status: implementation plan for issue #6375. Labeling remains OFF until the
operator explicitly starts a provider stage.

## Frozen outcome contract

- User-visible outcome: independently label every one of the 10,159 frozen
  Cycle 007 rows with Gemini and Grok, deterministically compare both label
  sets, adjudicate every disagreement, resolve any explicitly authorized
  residual, and certify zero unresolved rows.
- Source denominator: 204 immutable evidence packets containing 10,159 rows.
- Completion terms:
  - `storage_ready`: every runtime output root is mounted on the explicit
    backing filesystem and passes identity, permission, and free-space checks.
  - `provider_complete`: one provider has a verified sealed result for all
    204 packets and all 10,159 row identities.
  - `dual_complete`: both providers independently satisfy
    `provider_complete`.
  - `compared`: deterministic comparison covers the exact dual-complete
    identity set.
  - `adjudicated`: every disagreement has a verified adjudication result.
  - `certified`: the existing Cycle 007 certifier reports 204 packets, 10,159
    rows, both providers complete, and zero unresolved rows.
- Stop policy: stop without deleting a committed packet on mount drift,
  identity drift, a second guardian, inadequate actual free space, a provider
  stop receipt, a non-contiguous stage seal, an invalid committed packet, or
  an ambiguous provider/adjudicator attempt that started but did not commit a
  terminal receipt. A bind-mount command that exceeds 30 seconds stops with
  `bind_mount_timeout`. A controller status call that exceeds 300 seconds or a
  stage call that exceeds 72 hours stops with `controller_timeout`. The stage
  timeout kills only the controller wrapper, not a possibly surviving paid
  runner; the runner retains the inherited execution lock until it exits.
- Residual policy: provider or semantic failures remain explicit stop receipts;
  they are never normalized away or automatically retried by the guardian.
- Independent held-out evaluation: a frozen black-box fixture and expected
  text-free receipts, separate from the implementation-focused unit fixtures,
  use fake packages and fake providers to prove mount restoration, duplicate
  exclusion, exact packet resume, stage resume, and terminal completion without
  reading or depending on production content.

## Non-goals

- No evidence, packet, prompt, label schema, model, validator, endpoint,
  denominator, chunk size, custody, or certification-policy change.
- No copy of the approximately 81 GiB evidence bundle.
- No database, queue service, container platform, or new background daemon.
- No provider call during installation, storage preparation, status, or plan.
- No automatic clearing of provider-stop receipts or semantic failures.
- One explicit `recover-gemini-stop` action is available for an exact
  provider-return incident with the historical generic envelope code or a
  bounded transient status: quota, capacity, timeout, cancellation, or
  internal-provider failure. It hash-binds and archives the immutable text-free
  stop, binds the exact packet, chunk, attempt, started marker, terminal marker, and
  predecessor recovery receipt, and authorizes exactly one additional Gemini
  subscription call. It cannot recover authentication, structured-request
  rejection, an unknown or semantic failure, a changed stop, or a sealed Gemini
  stage. There is no permanent attempt ceiling: every later call still requires
  a new exact-stop operator recovery, so no automatic retry loop is possible.
- No persistent `/etc/fstab` or systemd mutation. Re-running the same guardian
  command after reboot restores the bind mounts and resumes from seals.

## Minimal architecture

The existing reviewed controller remains the authority for provider preflight,
packet verification, stage ordering, and stage seals. A pristine installation
may run provider-free `prepare`, `status`, and `plan` without provider bindings.
The bootstrap `status` and `plan` paths fail closed if they find any stage state,
provider receipt, non-empty output root, controller, or worker. Before `resume`, and whenever
provider state exists, the guardian requires explicit absolute AGY and Grok
executable bindings and all three preflight receipts. The controller verifies
each resolved regular file against its provider-attested canary hash before any
provider execution. The controller also passes the three preflight-verified
Sources server/database hashes to each provider runner explicitly; immutable
code releases do not need local copies of the source databases merely to
revalidate the already-frozen evidence identity. No provider executable is
discovered from a workstation path or from `PATH`. A small Linux-only guardian adds only the missing
operational layer:

1. Acquire one non-blocking outer guardian lock located outside the disposable
   worktree and hold it through storage validation and child completion. Pass a
   different stable lock path to the existing controller; the guardian never
   tries to acquire the controller lock itself. Also acquire a third stable
   execution lock and explicitly inherit its open descriptor through the
   guardian, controller, and actual provider/adjudicator runner. Because the
   kernel lock survives until the last inheriting process exits, a replacement
   guardian cannot start a duplicate even if the guardian and controller are
   killed while their runner remains alive.
2. Validate the explicit package and backing roots without discovering either.
   Hidden flags accept explicit absolute `sudo` and `mount` executables. The
   guardian inserts the non-interactive `-n` option and executes the fixed argv
   without a shell; PATH discovery and arbitrary privilege options are rejected.
3. Create six private backing directories and six empty package mountpoints
   with the frozen lexical names `label-output-gemini-cycle007-v1`,
   `label-output-grok-cycle007-v1`, `dual-label-output-cycle007-v1`,
   `consensus-audit-cycle007-v1`, `dual-label-adjudication-cycle007-v1`, and
   `dual-label-final-cycle007-v1`.
4. Idempotently bind-mount each backing directory at the unchanged package path.
   Package and backing roots must be absolute, distinct, non-overlapping, and
   contain no symlink component. The backing device must differ from the
   package/evidence device. An unmounted target must be empty. An existing mount
   is accepted only when `/proc/self/mountinfo` has an exact target entry,
   source and target have the same device and inode, all six targets share the
   backing device, ownership matches the explicit required `--owner-uid` and
   `--owner-gid` values, and modes are `0700`. A wrong existing mount fails
   without unmounting or remounting it.
   Actual free space is computed from `statvfs.f_bavail * f_frsize` and must be
   at least the operator-supplied floor before every stage.
5. Quarantine automatically only orphan atomic temporary names that cannot be
   a committed result, using a same-filesystem rename into a private bounded
   recovery directory. Automatic quarantine is capped at 64 files and 16 MiB
   per invocation; exceeding either bound fails with
   `recovery_bound_exceeded`. Never copy, read, delete, move, or overwrite a complete
   verified packet. A started-without-terminal attempt, partial provider or
   adjudicator final set, or provider-stop receipt is ambiguous and always
   blocks for explicit operator recovery. Package-top `.cycle007-*` residue
   remains on the package filesystem and is never copied across filesystems.
6. Read the existing text-free stage-seal chain and invoke the existing
   controller for exactly the first incomplete stage. Repeat until the requested
   terminal stage is sealed or a safe stop occurs.
7. For Gemini and Grok, use their existing per-attempt and packet/chunk receipts
   rather than a stage-wide marker. When the execution lock is free, resume at
   the first missing packet only after every committed unit verifies and there
   is no started attempt lacking either a complete verified unit or a terminal
   failure receipt, no partial seal, and no provider stop. For `audit` and
   `adjudicate`, which lack equivalent durable per-call markers, atomically write
   and parent-directory-fsync a conservative text-free active-stage marker
   before invoking the controller. Remove it and fsync the directory only after
   the controller has committed and verified that stage seal. If such a marker
   exists without its complete stage seal, a replacement guardian reports
   `ambiguous_provider_attempt` and performs zero provider calls. If the stage
   seal is complete, the marker is safely stale and may be removed without
   rerunning the stage.
8. Atomically write a text-free guardian receipt containing counts, stage,
   mount identities, code identity, and safe failure code. It contains no
   packet content, prompts, labels, responses, account data, or infrastructure
   locator.

The provider concurrency remains exactly one. The inherited execution lock is
held by the actual child runner for its entire lifetime, including before the
child writes its started marker. Packet and chunk receipts are the
durable checkpoint; the guardian does not maintain a second progress database.
Certification and controller files intentionally remain on the package
filesystem. The existing provider atomic helpers are not changed by this
runtime and do not fsync parent directories after every rename, so the guarantee
is deliberately limited to process death and orderly reboot. A power-loss or
kernel/filesystem crash that leaves an ambiguous attempt fails closed instead
of being claimed as automatically resumable.

## Recovery guarantees

| Interruption | Recovery behavior |
| --- | --- |
| Guardian killed between packets | Next invocation validates all committed packets and starts at the first missing packet. |
| Orderly server reboot | Next invocation recreates missing bind mounts, validates their identity, and resumes from the existing seals. |
| Process death during an atomic file write, before a provider attempt starts | The orphan atomic temporary name is moved without inspection by same-filesystem rename; the uncommitted unit is rerun. |
| Started provider/adjudicator attempt without a terminal receipt | Fail with `ambiguous_provider_attempt`; preserve every file and wait for explicit operator recovery. |
| Partial provider/adjudicator final set | Fail with `ambiguous_partial_seal`; preserve every file and wait for explicit operator recovery. |
| Guardian/controller/runner killed after an adjudicator or audit provider returns but before its stage seal | The durable active-stage marker remains; replacement returns `ambiguous_provider_attempt` and makes zero provider calls. |
| Guardian/controller killed between two verified Gemini or Grok packets | With no surviving execution lock or ambiguous attempt, replacement verifies the durable prefix and starts exactly at the next packet. |
| Crash between stages | The completed stage seal is validated and the next stage starts. |
| Wrong backing directory mounted | Fail with `mount_identity_drift`; do not run a provider. |
| Duplicate guardian | Fail with `guardian_already_running`; do not run a provider. |
| Guardian and controller killed while their runner survives | The runner retains the inherited execution lock; a replacement fails with `active_worker` and makes zero provider calls. |
| Bind-mount command exceeds 30 seconds | Fail with `bind_mount_timeout`; no provider has been invoked and the operator must inspect storage state before retrying. |
| Controller status call exceeds 300 seconds | Fail with `controller_timeout`; status never invokes a provider, so no paid runner is created by this path. |
| Controller stage call exceeds 72 hours | Kill only the controller wrapper and fail with `controller_timeout`. A surviving paid runner is deliberately not signalled, retains the inherited execution lock, and makes a replacement return `active_worker` with zero additional provider calls. After it exits, durable receipts, seals, and active-stage markers determine the only safe recovery point. |
| Provider or semantic stop receipt | Preserve the stop and wait for explicit operator recovery direction. |
| Exact Gemini provider-return stop after explicit recovery direction | `recover-gemini-stop --expected-stop-sha256 …` preserves the stop in the private backing filesystem and publishes one text-free receipt for exactly the next attempt. It verifies the contiguous attempt and authorization chain for that packet and chunk, preserves committed earlier chunks and packets without reading their content, and invokes no provider. |
| Repeated transient Gemini provider-return stops | Each new runner stop atomically includes its chunk, attempt, and terminal-marker digest. Each explicit recovery binds that occurrence, the failed attempt markers, exact provider-call count, and predecessor receipt. A fresh process accepts the resulting next attempt once; another terminal failure remains stopped until another explicit recovery. Attempt numbers are not capped. |
| Reviewed code or provider executable identity changes before any stage seal | Provider-bound `prepare` validates the complete successor preflight and both public canaries under the execution and controller locks. Rotation is accepted only when the successor names the exact installed preflight SHA-256, preserves canonical superseded receipts, writes the authoritative preflight copy last, and remains idempotent after interruption. Any existing stage seal blocks rotation. No provider is invoked. |

## Run sequence

1. `prepare`: mount and verify storage; when complete provider bindings are
   supplied, validate and install or explicitly chain-rotate their preflight
   identities. Provider calls remain off.
2. `status`: verify the pristine provider-off state and safe counts only.
3. `plan`: report Gemini as the next missing stage and safe counts only.
4. `resume --through gemini`: require the complete provider preflight, then
   finish and seal Gemini.
5. `resume --through grok`: finish and seal Grok.
6. `resume --through adjudicate`: compare, audit, and adjudicate after both
   provider seals exist.
7. `resume --through certify`: run authorized resolution when required and the
   existing certifier; success requires zero unresolved rows.

The staged `--through` boundary prevents an operator intending to start one
provider from accidentally starting the other or entering adjudication.
When an exact Gemini call has a recoverable provider-return stop, the operator may
insert the reviewed `recover-gemini-stop` action before repeating step 4. The
recovery action is idempotent, preserves the original stop by same-filesystem
link-and-unlink, holds the guardian and inherited execution locks while the
controller verifies stopped status, and
does not authorize Grok or any later stage.
If the authorized call stops again, another invocation with that new exact stop
hash publishes a chunk-local receipt chained to the prior authorization and
authorizes exactly one more call. Existing attempt-2 and attempt-3 receipts use
their reviewed legacy locations and remain valid; later receipts are local to
the stopped chunk so recovery remains collision-free after committed progress.
The already-installed version-1 stop format is accepted only for its bounded
clean-label packet-1/chunk-1 attempts through attempt 3. Every newly emitted
recoverable stop uses the occurrence-bound version-2 format, preventing a stale
identical stop hash from authorizing a later occurrence.

## Acceptance evidence

- Unit tests cover exact mount-table identity, no-symlink components, ownership,
  permissions, `f_bavail` free-space floor, distinct devices, non-overlapping
  roots, empty targets, wrong-mount refusal, idempotent remount, distinct outer
  and controller locks, inherited execution-lock continuity, a real child lock
  invocation, duplicate guardian,
  zero-provider prepare/plan/status, completed-packet preservation, requested
  `--through` boundaries, stage continuation, and safe stop receipts. Renewable
  recovery tests cover the exact third timeout, a fresh-process attempt-4
  resume, committed-prefix preservation without content reads, per-chunk receipt
  isolation, exact pre-call versus provider-call accounting, occurrence-bound
  stop identities, a twelve-link chain with no permanent ceiling, and refusal
  when any one-call authorization link is absent or changed.
- Preflight-rotation tests cover the exact predecessor link, immutable archives,
  authoritative-last replacement, idempotent retry, wrong-chain refusal, and
  the no-rotation-after-seal boundary.
- Interruption tests cover the boundary before a started marker, after the
  started marker, after provider return, after each final file, and after the
  terminal receipt. Only the pre-start orphan-temp case auto-recovers; every
  ambiguous paid-call boundary preserves files and stops.
- One process test pauses a runner before its started marker, kills its guardian
  and controller, and proves a replacement guardian returns `active_worker`
  while making zero additional provider calls.
- One process test triggers the guardian's real controller-timeout path against
  a long-running controller with a long-running child, proves the controller is
  killed while its child survives with the inherited execution lock, and proves
  a replacement guardian returns `active_worker` with zero additional provider
  calls.
- One process test kills the guardian and controller immediately after a
  verified Gemini/Grok packet boundary, then proves replacement execution starts
  at exactly the next packet with no duplicate provider call.
- A second process test kills the adjudicator after provider return and runtime
  cleanup but before its stage seal, then proves the durable active-stage marker
  makes replacement execution return `ambiguous_provider_attempt` with zero
  additional provider calls and no file loss.
- A synthetic end-to-end run reaches the existing certification stage, then a
  second invocation performs zero provider work.
- The exact PR head passes repository CI and an independent cross-family code
  review before merge.
- Production preflight is content-blind and labeling stays OFF until the
  operator executes an explicit `resume --through ...` command.
