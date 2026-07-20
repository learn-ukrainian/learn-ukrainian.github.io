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
.venv/bin/python -m scripts.session_supervisor --db /approved/session-streams.sqlite3 \
  --repo-root "$PWD" open --role driver --stream epic:4707 --agent codex \
  --harness codex-cli --instance-id codex-4707-1 --process-id "$$" \
  --lineage-id lineage-4707-codex --ttl-seconds 300
```

The capsule contains lease identifiers for binding and audit only; it exports no
lease credentials and gives no model-owned lifecycle command. A future launcher
keeps the exact lease envelope in its supervisor-owned environment, then calls
the matching lifecycle action on clean exit:

```bash
.venv/bin/python -m scripts.session_supervisor --db /approved/session-streams.sqlite3 close --role driver
```

`resume` and `heartbeat` also consume that exact supervisor-owned
`SESSION_STREAM_*` envelope. Fencing is enforced by
`agents_extensions.shared.session_streams`; a stale envelope is refused.

## Worker launches

Workers never acquire a lease. They receive a capsule only after the stream
already exists, and their child environment must be built by removing every
`SESSION_STREAM_*` field. The `worker-env` command exposes that stripping
operation for launcher integration tests.

```bash
.venv/bin/python -m scripts.session_supervisor --repo-root "$PWD" \
  --db /approved/session-streams.sqlite3 capsule --role worker --stream epic:4707
```

Automatic crash recovery is intentionally fail-closed in this slice. It awaits
the recovery-plan digest and exact repository/runtime/rollover receipts required
by the fleet-comms architecture; operators retain the existing audited recovery
path until that contract is available.
