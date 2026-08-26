# Phase 0 control-plane storage seam (#7365)

Stamped packet v3 SHA-256:
`d29a13cedcdc50c6e97516b237155dad9f53116051aba29211b73bfb058c3bcc`

Sqlite remains the live authority in this slice. `scripts/control_plane/storage.py`
is the single resolver for durable control-plane stores:

| Store id | Canonical sqlite path |
| --- | --- |
| `fleet_comms` | `batch_state/fleet-comms/v1/comms.sqlite3` |
| `session_streams` | `.agent/session-streams/v1/session-streams.sqlite3` |
| `write_ownership` | `batch_state/tasks/write-ownership.sqlite3` |
| `task_index` | *(no sqlite in Phase 0)* |

Authority per store: `sqlite` (default) · `shadow` · `pg`. Env vars are documented
in the module docstring. Postgres DSNs are env-only; pg authority refuses sqlite
opens and fails closed without `LEARN_UKRAINIAN_CP_PG_DSN`.

First consumer: `scripts/guardrails/delegate_ownership.py` routes `_connect()`
through the seam. Fleet-comms and session-streams direct opens remain allowlisted
in `scripts/hygiene/lint_control_plane_sqlite.py` until later slices migrate them.

No Patroni, dual-write, or public bind in Phase 0.
