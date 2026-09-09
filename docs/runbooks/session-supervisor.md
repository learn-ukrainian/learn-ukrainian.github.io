# Common session supervisor

`scripts.session_supervisor` is the PR-I launcher boundary for a session-stream
driver. It opens the fenced lease before a harness starts, then emits the
read-only bootstrap capsule. A harness or model must never open, renew, close,
or recover its own lease.

## Launcher contract

Launch a driver with an exact numeric stream and an explicit role. The command
returns a JSON capsule in the required order: identity, pending rollover slot,
digest watermark, dual-write handoff status, then diagnostics.

```bash
.venv/bin/python -m scripts.session_supervisor \
  --repo-root "$PWD" open \
  --role driver --stream epic:4707 --agent grok \
  --harness grok-tui --instance-id grok-4707-1 --process-id $$ \
  --lineage-id lineage-4707-grok --ttl-seconds 300
```

The capsule contains lease identifiers for binding and audit only; the supervisor
exports no lease credentials and gives no model-owned lifecycle command. The
launcher reads the capsule, exports the full `SESSION_STREAM_*` envelope that the
hook surface requires, and writes a small diagnostics capsule before exec-ing the
harness.

On clean exit the launcher (or a wrapper) calls the matching lifecycle action:

```bash
.venv/bin/python -m scripts.session_supervisor close --role driver
```

`resume` and `heartbeat` also consume that exact supervisor-owned
`SESSION_STREAM_*` envelope. Fencing is enforced by
`agents_extensions.shared.session_streams`; a stale envelope is refused.

### Close-failure observability

`scripts/lib/launcher_core.sh`'s `launcher_close_driver_lease` retries the
close command once, then reports failure without echoing raw stderr (which
may carry host paths or other operational detail). `launcher_classify_close_failure`
maps known-safe marker substrings to one of a fixed set of stable, privacy-safe
codes, appended to the failure message as `close_failure_reason=<code>`:

| Code | Meaning |
| --- | --- |
| `missing-required-environment` | The `SESSION_STREAM_*` envelope was stripped or incomplete (e.g. after wake). |
| `lease-fenced` | The lease was fenced out from under this holder (superseded generation/fencing token). |
| `monitor-unreachable` | The remote Monitor API could not be reached. |
| `monitor-error` | The remote Monitor API reachable but refused or errored the request. |
| `store-error` | A local session-stream store error not covered above. |
| `unknown` | No known-safe marker matched; check the host's own logs, not this classification. |

## Environment envelope

A launcher that claims a lease must export every `SESSION_STREAM_*` variable the
hook surface expects:

| Variable | Source | Example |
| --- | --- | --- |
| `SESSION_STREAM_ID` | stream id | `epic:4707` |
| `SESSION_STREAM_SESSION_ID` | new session id | `session-…` |
| `SESSION_STREAM_LEASE_ID` | new lease id | `lease-…` |
| `SESSION_STREAM_GENERATION` | session generation | `1` |
| `SESSION_STREAM_FENCING_TOKEN` | fencing token | `1` |
| `SESSION_STREAM_AGENT` | agent identity | `grok` |
| `SESSION_STREAM_HARNESS` | harness identity | `grok-tui` |
| `SESSION_STREAM_INSTANCE_ID` | distinct runtime instance | `grok-12345` |
| `SESSION_STREAM_PROCESS_ID` | holder PID | `12345` |
| `SESSION_STREAM_TASK_ID` | optional task id | `5512-pr-j1-launchers` |
| `SESSION_STREAM_HEARTBEAT_AT` | last heartbeat timestamp | `2026-07-20T21:00:00Z` |
| `SESSION_STREAM_EXPIRES_AT` | lease expiry timestamp | `2026-07-21T03:00:00Z` |
| `SESSION_STREAM_TTL_SECONDS` | lease TTL | `21600` |
| `SESSION_STREAM_VERSION` | lease schema version | `1` |

The hook CLI consumes the same envelope:

```bash
.venv/bin/python -m agents_extensions.shared.session_streams hook heartbeat
.venv/bin/python -m agents_extensions.shared.session_streams hook close
```

## Launcher helper

`scripts/lib/session_supervisor.sh` is the shared bash helper for non-Claude
launchers.

```bash
source "${PROJECT_DIR}/scripts/lib/session_supervisor.sh"
claim_session_supervisor_env \
  "epic:4707" "grok" "grok-tui" "5512-pr-j1-launchers" "grok-$$" \
  "$PROJECT_DIR" "start-grok.sh" "harness"
```

The helper:

1. Calls `scripts.session_supervisor open --role driver`.
2. Parses the JSON capsule and exports `SESSION_STREAM_*` from the lease plus the
   launcher-supplied holder fields.
3. Writes a JSON capsule under
   `<canonical-state-root>/.agent/session-capsules/<stream-safe>/<iso>-<pid>.json`
   in the canonical state root.
4. Exports `SESSION_SUPERVISOR_CAPSULE_PATH` pointing to the capsule.
5. Fails the launch closed on supervisor error or an incomplete envelope.

## Capsule schema

```json
{
  "schema_version": 1,
  "written_at": "2026-07-20T21:00:00Z",
  "launcher": "start-grok.sh",
  "epic": "harness",
  "stream_id": "epic:4707",
  "session_id": "session-…",
  "lease_id": "lease-…",
  "agent": "grok",
  "harness": "grok-tui",
  "instance_id": "grok-12345",
  "process_id": 12345,
  "task_id": "5512-pr-j1-launchers"
}
```

Capsules are runtime diagnostics only; they are not committed and are not a
source of truth for lease state.

## Worker launches

Workers never acquire a lease. They receive a capsule only after the stream
already exists, and their child environment must be built by removing every
`SESSION_STREAM_*` field. The `worker-env` command exposes that stripping
operation for launcher integration tests.

```bash
.venv/bin/python -m scripts.session_supervisor \
  --repo-root "$PWD" capsule --role worker --stream epic:4707
```

## Error behavior

- Unknown epic → launcher fails before calling the supervisor.
- Supervisor refuses (live holder process, claimer PID not live, etc.) →
  launcher exits with an error; no session is started.
- Incomplete supervisor output → launcher fails closed.

### Recovery authority: remote TTL/CAS and local dead-process proof

Remote drivers claim through Monitor. An unexpired remote lease remains live
regardless of whether a PID happens to exist on the successor host. A successor
must wait for an exact-envelope clean release or TTL expiry; Monitor atomically
claims the next generation and fencing token. A late predecessor is fenced
once that successor claim commits. Remote unavailability fails closed.

Clean exits release only their exact lease envelope. Attributed `release --force`
is an exceptional, separately authorized operator action, never automatic recovery.

Explicit `--local` mode can recover a local process lease before TTL expiry when
the exact holder PID is absent and the distinct candidate process is live.
It cannot use local PID evidence to close a lease acquired through Monitor,
even after that remote lease expires. A still-running local holder is refused.

A successor bootstrap reconciles its exact lease with Monitor's active projection
before returning the capsule. Rollover resume requires the prepared durable
handoff to be present and nonempty. Restore missing continuity evidence before
retrying; a successful claim alone does not prove rollover continuity.

## Supervisory event integration

The inbox watcher has explicit Fleet Comms modes in addition to its legacy
read-only notification mode. These require the generation-bound consumption API
from PR #7781; a missing API fails closed, without generic acknowledgment fallback.

The common launcher process loop starts and stops the supervisory watcher,
handles its wake notification, reaps the provider, and closes the exact lease
before executing the existing driver entrypoint with the original arguments.
A transient Monitor transport outage or HTTP 5xx response leaves the provider alive: the live watcher
logs, sleeps, and retries until recovery or launcher termination. It signals the
launcher only after writing a successfully prepared delivery (exit 75). A
transient watcher exit (76) restarts the watcher under the same lease; USR1 alone
never authorizes a wake. Permanent watcher failures still stop the provider
without authorizing a successor.

Exact lease close retries Monitor failures with exponential backoff from 1 second
up to 30 seconds for ten minutes (override: `LC_DRIVER_CLOSE_RETRY_SECONDS`). It
logs `waiting for Monitor API to recover (close attempt N)` without remote stderr.
Fencing or missing lease environment fails immediately. Exhausted close retries
retain safe `close_failure_reason=` classification and prevent successor execution.
Recovery waits do not override lease fencing or the heartbeat TTL: losing the
lease still stops the provider.

Supervisory requests use the existing authority message/delivery store and the
recipient `supervisor:epic:<number>`, keeping automatic events out of ordinary
driver inbox traffic. Enqueue through `enqueue_supervisory_request` with an
idempotency key and a bounded JSON body:

```json
{"schema":"supervisory-wake.v1","action":"restart","stream_id":"epic:9999","generation":1}
```

Only `wake` and `restart` are accepted. The generation names the predecessor;
zero denotes a stream without a previous lease. The body cannot choose a
launcher, model, command, approval setting, or filesystem path.

The intended host-resident invocation uses the existing watcher process:

```bash
scripts/ai_agent_bridge/inbox_watch.sh grok-infra --wake-driver grok --epic infra
scripts/ai_agent_bridge/inbox_watch.sh grok-atlas --wake-driver grok --epic atlas
```

Run it in an existing persistent host terminal or service allocation. The
watcher does not install another service or make an offline host available.
It checks at most 64 pending events per tick and invokes only the selected
existing launcher. The launcher remains the sole process/lease supervisor.
An active remote lease prevents startup; unknown authority fails closed.

For a clean restart, launcher-owned consumption records the exact generation
before preparing a durable stream handoff. The process loop must stop and reap
the provider, stop renewal, and release the exact envelope before replacing
itself with the same entrypoint and original arguments. A deterministic
successor session identity plus the post-claim generation check allows at most
one provider start for a predecessor generation. Remote crash recovery remains
TTL/CAS, and `release --force` is never part of this path.

The successor reclaims the delivery through its existing 60-second delivery
lease and new fence, records its own generation-bound consumption, and only
then acknowledges its verified live envelope. Delivery attempts are bounded at
three. A consumption receipt alone never proves successor startup. Failed or
ambiguous outcomes retain reconciliation work; they do not authorize a blind
second start. A later generation requires a new explicitly targeted event.

All certified provider driver entrypoints, including Claude, use the common
launcher lease boundary before starting their provider adapters.

## Related

- `scripts/session_supervisor/__init__.py`
- `scripts/session_supervisor/__main__.py`
- `agents_extensions/shared/session_streams/hooks.py`
- `scripts/lib/session_supervisor.sh`
- `docs/runbooks/grok-session-canary.md`
- `docs/runbooks/kimi-orchestrator.md`
