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
through the seam.

Phase 0 remainder (#7365):
- `agents_extensions/shared/session_streams/db.py` (`SessionStreamDatabase._connect_once`) routes `session_streams` through the seam, preserving bounded lock retry, migration verification, and synchronous pragmas.
- `scripts/fleet_comms/artifacts.py` (`ArtifactStore`), `cli.py` (`_open_plane_db_ro`), `cold_start_board.py` (`_probe_inbox_authority`), `message_plane.py` (`_read_applied_schema_version`), `routing_reservations.py` (`list_routing_decisions`), and `efficiency_metrics.py` (`_connect_ro`) route authority-plane `comms.sqlite3` opens through the seam.
- `scripts/fleet_comms/authority.py` delegates to `ArtifactStore` for its comms plane storage.

Remaining allowlisted direct opens in `scripts/hygiene/lint_control_plane_sqlite.py`:
- Monitor API routers (`scripts/api/fleet_router.py`, `scripts/api/fleet_workers_collect.py`, `scripts/api/runtime_router.py` — handled in #7269 steps 3/4/6)
- Entire context diagnostic readers (`scripts/entire_context/reconcile.py`, `scripts/entire_context/resolvers.py`)
- Runtime / slot routing readers (`scripts/agent_runtime/acpx_discuss.py`, `scripts/orchestration/slot_routing.py`)

Legacy broker `messages.db` call sites (e.g. `legacy_broker_report.py`, `_probe_inbox_legacy`) remain direct non-authority file opens.

No Patroni, dual-write, public bind, or DSN in git in Phase 0.
