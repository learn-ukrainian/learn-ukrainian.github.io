# Phase 0b control-plane storage seam (private #603)

Stamped packet v3 SHA-256:
`d29a13cedcdc50c6e97516b237155dad9f53116051aba29211b73bfb058c3bcc`

Sqlite remains the **default** live authority. `scripts/control_plane/storage.py`
is the single resolver for durable control-plane stores — still a resolver, not
a dialect-neutral SQL switchboard (callers own transactions).

| Store id | Canonical sqlite path |
| --- | --- |
| `fleet_comms` | `batch_state/fleet-comms/v1/comms.sqlite3` |
| `session_streams` | `.agent/session-streams/v1/session-streams.sqlite3` |
| `write_ownership` | `batch_state/tasks/write-ownership.sqlite3` |
| `task_index` | *(no sqlite in Phase 0 / not this slice)* |

Authority per store: `sqlite` (default) · `shadow` · `pg`.

- **`sqlite` / `shadow`**: open the canonical sqlite file. In this slice `shadow`
  remains a sqlite synonym (no dual-write).
- **`pg`**: opens a **real** Postgres connection via psycopg 3 using
  `LEARN_UKRAINIAN_CP_PG_DSN` only. Missing DSN → fail closed
  (`ControlPlanePgDsnMissingError`). Present → connect with
  `connect_timeout` ≤ 3s. Never falls back to sqlite and never creates a
  sqlite file for that store. Errors report the store id only (no DSN
  hostnames / userinfo).

Env vars are documented in the module docstring. Postgres DSNs are env-only;
do not flip `LEARN_UKRAINIAN_CP_AUTHORITY` on live hosts in this slice.

Dual-engine contract tests live under `tests/control_plane/` (`sqlite` and
`postgres`-marked `pg`). CI ephemeral Postgres attaches to the existing
`python` shard job; local default pytest stays sqlite-only when the DSN is
unset (`pytest.skip` on `postgres` tests).

First consumer: `scripts/guardrails/delegate_ownership.py` routes `_connect()`
through the seam (sqlite by default).

Seam consumers already routed in Phase 0a:
- `agents_extensions/shared/session_streams/db.py` (`SessionStreamDatabase._connect_once`)
- `scripts/fleet_comms/artifacts.py` (`ArtifactStore`), `cli.py`, `cold_start_board.py`,
  `message_plane.py`, `routing_reservations.py`, and `efficiency_metrics.py`
- `scripts/fleet_comms/authority.py` delegates to `ArtifactStore`

Remaining allowlisted direct opens in `scripts/hygiene/lint_control_plane_sqlite.py`:
- Monitor API routers (`scripts/api/fleet_router.py`, `scripts/api/fleet_workers_collect.py`, `scripts/api/runtime_router.py` — handled in #7269 steps 3/4/6)
- Entire context diagnostic readers (`scripts/entire_context/reconcile.py`, `scripts/entire_context/resolvers.py`)
- Runtime / slot routing readers (`scripts/agent_runtime/acpx_discuss.py`, `scripts/orchestration/slot_routing.py`)

Legacy broker `messages.db` call sites remain direct non-authority file opens.

Phase 0b residuals on private #603 (not this PR): artifact byte-plane,
cluster-readiness `SELECT 1`, HTTP Idempotency-Key, `efficiency_metrics` move.

No Patroni, dual-write, public bind, live DSN flip, or DSN in git.
