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

Cluster-readiness pings Postgres with `SELECT 1` (DSN presence alone is not
readiness).

## Live authority (current production, 2026-09-02, after public #7606/#7607 and the host freeze/import)

| Store | Live authority | Notes |
| --- | --- | --- |
| `fleet_comms` | `pg` | create/get + execute/claim paths on Postgres |
| `session_streams` | `sqlite` | sqlite-only by design in this slice (#7482 interlock). Do not port now. |
| `write_ownership` | `sqlite` | same class as session_streams |
| `task_index` | (none yet) | planned pg-only store; not live |
| `teacher` | `sqlite` | out of scope; must remain hosted |

A Postgres copy of `session_streams`/`write_ownership` was imported then unfenced back to sqlite, and those pg tables were renamed to `*_import_stale_20260902` so they cannot be mistaken for authority. Receipt: `batch_state/cp-pg-stale-import-neutralise-20260902.json`.

## Artifact byte-plane (this slice)

`ArtifactStore.store_bytes` / `read_bytes` / `get` / `materialize`: when
`fleet_comms` authority is `pg`, payload bytes live in Postgres (`BYTEA`,
content-addressed by sha256) in a small dedicated table
(`fleet_comms_artifact_blobs`) — not a mirror of the sqlite `artifacts`
schema, just enough columns to serve `ArtifactRecord` plus the payload. This
closes the NO-GO: a pg metadata row can no longer point at a blob file that
only exists on the writer's host — a second process with the DSN and no
local `blobs/sha256/...` tree still reads bytes back correctly. Default
authority stays sqlite (today's file-backed content-addressed store,
unchanged). `reference` / `is_referenced` / `garbage_collect_unreferenced`
remain sqlite-only in this slice (out of scope; they hang off the sqlite
`comms_messages` / authority tables that don't exist under `pg` here).

Phase 0b residuals on private #603 (not this PR): HTTP Idempotency-Key,
`efficiency_metrics` move.

No Patroni, dual-write, public bind, live DSN flip, or DSN in git.
