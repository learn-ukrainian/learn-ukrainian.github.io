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
- Supervisor refuses (live unexpired lease, claimer PID not live, etc.) →
  launcher exits with an error; no session is started.
- Incomplete supervisor output → launcher fails closed.

## Claude

Claude's SessionStart hook currently owns its own lease binding. PR-J2 will
integrate the common supervisor into `start-claude.sh` so `--epic` claims the
lease before SessionStart binds it.

## Related

- `scripts/session_supervisor/__init__.py`
- `scripts/session_supervisor/__main__.py`
- `agents_extensions/shared/session_streams/hooks.py`
- `scripts/lib/session_supervisor.sh`
- `docs/runbooks/grok-session-canary.md`
- `docs/runbooks/kimi-orchestrator.md`
