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
unchanged). `reference` / `is_referenced` remain sqlite-only in this slice (out of scope; they hang off the sqlite
`comms_messages` / authority tables that don't exist under `pg` here).

Authority efficiency metrics, backlog, and dead-letter collectors use the same
storage switch (#7486). Their read-only connections use dialect-aware metadata
queries, parameters, and latency aggregation; pg reads do not depend on a local
SQLite file. Legacy broker collectors remain explicit file-backed projections.
Dual-engine coverage lives in `tests/fleet_comms/test_efficiency_metrics_authority.py`.

Phase 0b residuals on private #603 (not this PR): HTTP Idempotency-Key.

No Patroni, dual-write, public bind, live DSN flip, or DSN in git.

## Unreferenced artifact retention citation sources

The unreferenced rule (#12574, #12611) requires all five declared sources.
It also scans the store's message text, metadata and message-linked blobs.
Every source is scanned for artifact ids and sha256 tokens.

| Argument | Source |
| --- | --- |
| `--cited-from-tasks` | Dispatcher task tree, including archived task records and transcripts; at least one `.json` file |
| `--cited-from-docs` | Repository docs tree, every file and subtree; at least one `.md` file |
| `--cited-from-github` | Complete GitHub JSONL export of issues, PRs and comments, fetched within 24 hours; format in `retention --help` |
| `--cited-from-export` | Caller-supplied citation export file, plain text or JSON; handoff tooling exports its artifact citations here |
| `--cited-from-batch-state` | `batch_state/` tree, including receipts outside `tasks/` and archived subtrees; only this store's own resolved root is excluded |

The export must be non-empty, and the batch-state tree must contain at least
one file. Pass the full batch-state root even when the tasks tree is inside it;
each source has its own coverage entry. An artifact cited only in the export
or in a receipt stays held as cited. The export has no required schema.
No private store or location is built into the scanner.

The batch-state scan excludes only the current `ArtifactStore` root. Its
artifact index and unlinked blobs are not outside citations; message text
and linked blobs remain covered by the store source. The batch-state coverage
entry lists the excluded root in `excluded_subtrees` with reason
`artifact_store`. Every other subtree is scanned completely. A batch-state
root equal to or inside the store refuses the run.

A dry run writes nothing and reports each source's path, scanned bytes and
file or record counts in `unreferenced.sources`. The tree receipts also count
exact generated checkout-inventory blob listings ignored as non-citations.
The export and batch-state scan use the same compressed-content handling as
the other file sources. A missing, unreadable, incomplete or invalid declared
source refuses the entire run before either retention rule computes candidates.
Symlinks and non-regular files in the export or scanned trees also refuse.

```bash
.venv/bin/python -m scripts.fleet_comms retention \
  --cited-from-tasks batch_state/tasks \
  --cited-from-docs docs \
  --cited-from-github github.jsonl \
  --cited-from-export citations.txt \
  --cited-from-batch-state batch_state
```

With no citation arguments, only the message rule runs. A partial source list
refuses. The unreferenced rule keeps its minimum 90-day cutoff and existing
retention classes. Apply still requires `--apply --backup-dir` and a verified
backup before unlinking; no rows or digests are deleted.
