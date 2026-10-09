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

### Supervisory wake ownership and failure status

The launcher opens separate read and write descriptors for the wake file,
then immediately unlinks its temporary name. The watcher inherits only the
write side as stdout; it never owns deletion. The launcher reads the delivery
through its retained descriptor after the watcher exits. Removing or replacing
the former pathname cannot discard those bytes. Launcher cleanup closes the
descriptor after reaping the watcher, and never deletes a replacement file.
This follows the [open-file lifetime defined by unlink(2)](https://man7.org/linux/man-pages/man2/unlink.2.html).

A missing/unreadable wake descriptor or empty delivery reports
`wake-file-missing`; an unsuccessful watcher reports `watcher-failed`.
Both clear the delivery, stop the provider, close the predecessor's existing
lease, then attempt one status publication before returning the original
non-zero status. Neither executes a successor.

Before clearing `SESSION_STREAM_*` for a supervisory successor, the launcher
captures the predecessor generation in
`LC_SUPERVISORY_PREDECESSOR_GENERATION`. If the successor fails to start its
scope entry, the waiting launcher reports `scope-start-failed`, attempts one
status publication, and exits 6 before preparation or lease acquisition.
Other configuration and verification refusals exit 6 without publishing.
The captured generation is cleared on verified launcher re-entry.

Publication uses the already-resolved project interpreter and
`scripts.fleet_comms channel publish cto -`, with the driver's sender identity,
kind `status`, and idempotency key `<stream>-<generation>-<reason>`. The JSON
body contains exactly `stream`, numeric `generation`, and `reason`. It contains
no diagnostic details. The launcher never creates the channel, retries the
successor, or changes its exit status when publication fails.

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
It checks at most 64 pending supervisory events per tick. Offline events invoke
only the selected existing launcher; ordinary unread Codex inbox rows can resume
an idle live thread as described below. The launcher remains the sole
process/lease supervisor. An active remote lease prevents launcher startup;
unknown authority fails closed.

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

### Live Codex inbox readiness (#10133)

With `--wake-driver codex`, unread ordinary bridge rows for an occupied Codex
lease are coalesced into one `codex exec resume` turn, oldest message first.
The watcher discovers the exact lease owner's Codex process and open rollout,
checks the inherited lease envelope, and reconciles remote authority again.
It never launches a second driver, types into tmux, signals the live process,
or claims, renews or releases its lease. Wake mode off only notifies.

Readiness comes from a forward streaming scan of complete rollout JSONL
records, with a cached byte offset and last lifecycle state across polls.
Cold start scans the file once; inode replacement, observed truncation or a
same-size rewrite resets the cache. No record or file size cap limits the scan.
Long message strings are validated and skipped with bounded memory; JSON grammar,
escapes, UTF-8 and nesting are validated before a record can decide readiness.
Only the top-level `type="event_msg"` and its direct `payload.type` count.
`payload.id`, nested envelopes and type-like text inside strings do not count.

The last lifecycle event decides: `task_started` / `turn_started` is BUSY;
`task_complete` / `turn_complete` / `turn_aborted` is READY. An abort closes the
turn even without a turn ID; a later start supersedes that abort. A complete
valid rollout with no lifecycle event has no recorded open turn. The installed
CLI's rollout vocabulary was verified against its own events and the
[upstream EventMsg protocol](https://github.com/openai/codex/blob/2351d9e1b608e6f9d9a3699b71d7eb39ee41cfa4/codex-rs/protocol/src/protocol.rs#L1511-L1522):
`task_*` are the v1 wire names; `turn_started` and `turn_complete` are aliases,
and `turn_aborted` follows the enum's snake-case encoding.

Fail-closed reasons include:

- `start_event:<type>`: an unmatched start, regardless of its age. There is **no
  time-based staleness escape**. A crashed driver ends through lease/session
  expiry and the normal launcher recovery path.
- `partial_final_line`: any record without its terminating newline, even if
  its current bytes happen to form valid JSON. An append can complete it.
- `decode_error:<exception>`: malformed JSON anywhere in the scanned history,
  duplicate lifecycle fields, invalid UTF-8, invalid string escapes, decoder
  failures, nesting beyond 256 containers, or numeric tokens longer than 4,300
  bytes. These last two are decoder safety limits, not record size limits.
  Decoder faults remain BUSY until the rollout is replaced or truncated.
- `read_error:<exception>`: missing or unreadable rollout; retried next poll.
- `rollout_changing`: after each scan, device/inode, size and modification time
  are checked again. Appends are rescanned, up to three passes. A file still
  changing remains BUSY and is retried next poll.
- `rollout_unavailable`: discovery did not provide an exact rollout path.

BUSY reports `codex_wake_busy:<reason>`. A missing binary or resume exception
reports `codex_resume_error:<exception>`; a nonzero exit, missing turn evidence,
or failed/error event reports `codex_resume_error:failed`. The supervisory loop
catches all ordinary wake exceptions, emits a typed `wake_error`, leaves the
rows unread, and polls again. Only a successful resume advances the watcher's
in-memory cursor; the live driver still records durable inbox consumption.

Readiness is checked after lease reconciliation and message framing and again
immediately before the resume subprocess is spawned. **A residual window still
exists between that last check and the subprocess attaching**: another turn
can start during that interval. File observation cannot provide atomic turn
admission. [#10217](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/10217),
owned by the harness stream's accountable driver, tracks that admission work.
This gate does not claim to close the race.

#### Manual throwaway-session receipt

The following creates a fresh, isolated Codex session and resumes only the UUID
returned by that creation. Run it from a dispatch checkout using the configured
project interpreter (replace `.venv/bin/python` with that interpreter when
shared). It uses the existing managed `$TMPDIR`, and asserts the rollout's
recorded working directory is the throwaway directory before resuming. It never
accepts a production thread ID. This receipt proves resume/readiness behavior;
it does not certify a production lease or atomic admission. Do not run a receipt
against a live production driver.

```bash
.venv/bin/python - <<'PY'
import json
import os
import subprocess
import tempfile
from pathlib import Path
from scripts.ai_agent_bridge import _ui_codex as ui

with tempfile.TemporaryDirectory(dir=os.environ["TMPDIR"], prefix="wake-receipt-") as scratch:
    first = subprocess.run(
        ["codex", "exec", "--json", "--disable", "apps", "--skip-git-repo-check", "-"],
        input="Reply exactly RECEIPT-START. Do not run tools.", cwd=scratch,
        capture_output=True, text=True, timeout=180, check=True,
    )
    events = [json.loads(line) for line in first.stdout.splitlines() if line.strip()]
    thread = next(event["thread_id"] for event in events if event["type"] == "thread.started")
    assert any(event["type"] == "turn.completed" for event in events)
    rollout = ui.find_session_file(thread)
    assert rollout is not None
    with rollout.open("rb") as stream:
        metadata = json.loads(stream.readline())
    assert metadata["payload"]["id"] == thread
    assert Path(metadata["payload"]["cwd"]).resolve() == Path(scratch).resolve()
    reader = ui.RolloutReader()
    def check_ready():
        ready, reason = ui.rollout_is_ready(rollout, reader=reader)
        assert ready, reason
    check_ready()
    before = rollout.stat().st_size
    result = ui.send(
        thread, "Reply exactly RECEIPT-RESUMED. Do not run tools.",
        cwd=Path(scratch), timeout_s=180, before_resume=check_ready,
    )
    types = [event["type"] for event in result["events"]]
    assert result["exit_code"] == 0
    assert types.count("turn.started") == types.count("turn.completed") == 1
    assert not {"turn.failed", "error"}.intersection(types)
    assert result["final_message"] == "RECEIPT-RESUMED"
    assert rollout.stat().st_size > before
    check_ready()
    print(json.dumps({"schema": "codex-wake-receipt.v1", "same_thread": True,
                      "new_turns": 1, "ready_after_resume": True}))
PY
```

## Related

- `scripts/session_supervisor/__init__.py`
- `scripts/session_supervisor/__main__.py`
- `agents_extensions/shared/session_streams/hooks.py`
- `scripts/lib/session_supervisor.sh`
- `docs/runbooks/grok-session-canary.md`
- `docs/runbooks/kimi-orchestrator.md`
