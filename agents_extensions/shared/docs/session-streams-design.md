# Agent-Agnostic Epic Session Streams on SQLite

**Status:** Design for operator review; implementation is not authorized by this document
**Operator order:** 2026-07-18
**Tracking issue:** #5422, under infra-harness stream epic #4707
**Source of truth:** `agents_extensions/`; `.claude/`, `.codex/`, and other
harness directories remain generated deploy targets

## Decision summary

Store long-lived epic memory in one repository-owned SQLite database shared by
every local harness. An epic is a stable stream such as `epic:4707`; a driver
run is a session within that stream. Entries and lifecycle evidence are
append-only. The small current-session and current-lease rows are transactional
projections over that immutable history and are never deleted.

Cold start loads all pinned `binding_order` and `negative_constraint` entries,
then only the last configured `N` other entries. The Monitor API renders this
digest for every harness. Drivers write through the same source-owned CLI or
library with an exact stream lease and fencing token. A stale heartbeat permits
planning, not takeover. Lease transfer occurs only after the existing rollover
claim, strict-recall, canary, and confirmation receipts pass. `closed` is a
terminal session state enforced in SQLite and in the command layer.

This is a storage layer beneath the existing rollover protocol. It does not
replace provider task identity, native task creation, canary semantics,
Task Family Manager receipts, or proof-gated predecessor cleanup.

## Scope and non-goals

This design covers:

- per-epic and fleet-shared stream identity;
- versioned SQLite schema and append-only invariants;
- session and lease state, heartbeat, rollover, and takeover;
- pinned-plus-tail cold-start projection;
- Monitor API and operator CLI read surfaces;
- migration from Claude epic handoffs and `docs/session-state/current.*.md`;
- Claude, Codex, other CLI harness, and Monitor TUI onboarding;
- backup, export, privacy, failure recovery, and implementation sequencing.

This design does not:

- implement the database, routes, hooks, or migration;
- authorize a cutover or retirement of any file handoff;
- add a second thread-rollover or context-canary protocol;
- write provider-owned task databases, including Codex's private SQLite state;
- infer stream ownership from an agent name, branch prefix, or mutable title;
- merge the design PR.

## Disposition of the seven design constraints

| # | Disposition | Design consequence |
| --- | --- | --- |
| 1 | Accept: pinned entries beat last-N. | `binding_order` and `negative_constraint` are always selected. Explicit supersession labels an old pinned entry inactive but never hides or deletes it. |
| 2 | Accept: integrate with rollover. | `thread_handoff.py`, the rollover registry, `context_canary.py`, and `thread_handoff_canary.py` continue to own replacement identity and continuity proof. Stream code consumes their exact receipts. |
| 3 | Accept: one active driver lease. | One mutable lease projection per stream, an increasing fencing token, append-only lease events, and proof-gated transfer. Sessions use `open`, `rolling`, and terminal `closed`. |
| 4 | Accept: operator window and backups. | An argparse-standard CLI provides `tail`, `dump`, and `grep`; online SQLite snapshots and portable exports are periodic, immutable, verified, and never rotated away. |
| 5 | Accept: shared stream and Monitor. | Fleet facts live once in `shared:fleet`; epic entries reference shared entry IDs. Monitor resolves references and is the only harness read surface. |
| 6 | Accept: Claude compatibility is critical. | SessionStart injects the stream digest in the current epic-handoff slot, after any rollover packet. Migration dual-writes before DB authority; file fallback remains available until per-harness acceptance passes. |
| 7 | Accept: WAL, versioning, envelope, and hygiene. | WAL is mandatory; migrations are checksummed; the logical entry envelope carries `stream`, `session_id`, `agent`, `harness`, `ts`, `type`, `body`, and `refs`; writes reject secret/PII-bearing content. |

## Existing machinery and the integration boundary

The current system already has the hard parts of safe thread continuity:

- `scripts/orchestration/thread_handoff.py` prepares an exact lineage-scoped
  lease and replacement packet, binds predecessor and replacement task IDs,
  reserves semantic-snapshot and proof paths, and keeps cleanup locked.
- `scripts/context_canary.py` requires exactly 3 goals, 3
  decisions/rationales, 2 negative constraints, and 2 next actions from
  allowed durable sources, then emits a strict 10/10 verdict.
- `scripts/orchestration/thread_handoff_canary.py` binds a PASS to the exact
  rollover ID, replacement task ID, and challenge.
- The rollover registry preserves exact identity and orders
  `PREPARED -> ... -> CONFIRMED -> PREDECESSOR_ARCHIVED -> HEARTBEAT_RETIRED`.
- `agents_extensions/shared/hooks/session-setup.sh` detects a pending packet
  first. It then tells an epic driver to read
  `.claude/<epic>-epic/CLAUDE-DRIVER-HANDOFF.md`.
- `scripts/api/session_router.py` serves file-backed agent handoffs through
  `/api/session/current` and exposes their hash through
  `/api/state/manifest`.
- Task Family Manager uses exact task UUIDs and typed relations. Its Codex
  SQLite bridge is deliberately read-only and must stay unrelated to this DB.

The session-stream layer changes only the durable semantic-memory source and
the stream lease. Rollover packet files remain short-lived protocol evidence;
they are not a second long-lived memory store. When a canary needs the current
stream state, the adapter renders the selected DB entries into the existing
reserved semantic-snapshot path under `.agent/thread-rollovers/`. That keeps
the current closed `source_ref` grammar and confirmation commands intact.

### Reuse map

| Session-stream responsibility | Existing authority reused | New behavior |
| --- | --- | --- |
| Identify predecessor/replacement | `task-identity.v1`, Task Family Manager, rollover registry | Store exact receipt references and holder IDs; never match titles. |
| Prepare rollover | `thread_handoff.py prepare` | Atomically mark the stream session `rolling` only after the prepared receipt exists. |
| Claim replacement | `detect` then exact `resume` | Candidate receives the DB digest in SessionStart and claims only the detected packet. |
| Prove restored context | `context_canary.py` strict snapshot/questions/score | Snapshot content is selected from pinned-plus-tail DB entries and rendered at the existing reserved path. |
| Prove replacement process | `thread_handoff_canary.py` | No change. |
| Confirm successor | `thread_handoff.py confirm-started` | Its exact PASS receipts authorize, but do not themselves perform, stream lease transfer. |
| Archive/retire predecessor | Task Family Manager and rollover cleanup proofs | Stream lease transfer records the new holder; existing cleanup remains independently gated. |
| Reconcile stale state | rollover registry `audit`/`reconcile-exact`/proof-gated maintenance | A stale heartbeat is only a signal. Any recovery plan names the exact existing packet or exact recovery preparation command. |

## Source layout and runtime location

All new session-stream logic, SQL, prompt fragments, route handlers, CLI code,
and tests belong under one source package:

```text
agents_extensions/shared/session_streams/
├── __init__.py
├── __main__.py
├── cli.py
├── db.py
├── schema.sql
├── model.py
├── digest.py
├── lease.py
├── migration.py
├── backup.py
├── monitor_router.py
├── prompts/
└── tests/
```

The existing source-owned SessionStart hook in
`agents_extensions/shared/hooks/session-setup.sh` imports or invokes this
package. Monitor's host application may contain the minimal mount call needed
to attach the source-owned FastAPI router, but no session-stream SQL, policy,
or rendering is duplicated under `scripts/`. Provider directories receive only
generated deploy copies through the existing deploy process.

The runtime database lives at the canonical primary checkout, not the invoking
worktree:

```text
.agent/session-streams/v1/session-streams.sqlite3
```

The canonical root is resolved from Git's common directory, matching
`thread_handoff.canonical_state_root()`. Therefore Claude, Codex, Grok,
Gemini/AGY, Kimi, interim stand-ins, Monitor, and all linked worktrees see the
same database. `.agent/` is already gitignored.

`db.py` applies `foreign_keys=ON`, `busy_timeout=5000`, and
`synchronous=FULL` on every connection; only WAL persists as file-level state.
Connection setup immediately reads `PRAGMA foreign_keys` back and fails closed
unless it is `1`. Read connections additionally set `query_only=ON`. The DDL
header below also sets the values for standalone validation, but it is not
treated as sufficient runtime configuration.

## Logical model

### Stream

A stream is provider-independent and stable:

- `epic:<number>` for one registered stream epic, for example `epic:4707`;
- `shared:fleet` for fleet-wide facts referenced by multiple epics.

Issue-to-epic membership remains authoritative in
`scripts/config/issue_streams.yaml` and `/api/issues/streams`. Agent name,
harness, branch prefix, mutable title, and most-recent activity never establish
stream identity.

The current launcher `--epic <slug>` identifies a lane, not necessarily one
numeric stream epic: some registry lanes contain multiple epics. Session-stream
onboarding therefore adds an explicit numeric `stream_epic` to the launch/task
identity carrier. SessionStart validates that number against the assigned lane
and registry. It may derive the number only when the registry has exactly one
candidate; zero or multiple candidates fail closed and require an explicit
value. The resulting canonical ID is always `epic:<number>`.

### Session

A session is one continuous driver lineage within a stream. Native task/thread
rollovers and an approved interim-driver transfer keep the same `session_id`.
A later, independent driver run after close opens a new session. Historical
entries from every session remain part of the stream.

States are:

```text
                 rollover/takeover prepared
        +-----------------------------------------+
        |                                         v
      open  <---- exact confirmation + transfer ---- rolling
        |                                             |
        +---------------- close proof ----------------+
                              |
                              v
                            closed
                         (no outgoing edge)
```

Allowed transitions are `open -> rolling`, `rolling -> open`, `open -> closed`,
and proof-gated `rolling -> closed`. The last transition is for an explicitly
abandoned or terminated rollover after registry reconciliation; it is never a
timeout shortcut. `closed` is terminal.

### Entry

The logical API envelope is:

```json
{
  "entry_id": 123,
  "stream": "epic:4707",
  "session_id": "session-opaque-id",
  "agent": "claude",
  "harness": "claude-code",
  "ts": "2026-07-18T12:00:00Z",
  "type": "binding_order",
  "body": "Operator-approved instruction",
  "refs": [
    {"kind": "github", "uri": "https://github.com/.../issues/5422"},
    {"kind": "shared_entry", "entry_id": 91}
  ]
}
```

Allowed entry types are exactly:

- `binding_order` — user/operator orders and binding scope;
- `negative_constraint` — prohibitions and unsafe actions;
- `decision` — a choice plus enough rationale to preserve it;
- `state` — current factual state or in-flight work;
- `next_action` — a concrete next action and boundary;
- `note` — useful context that is not one of the above.

Only the first two types are pinned. Writers must type entries explicitly;
ordinary live writes never guess a type from prose.

## SQLite schema

The following is the proposed v1 DDL. `STRICT` tables, foreign keys, check
constraints, immutable-history triggers, a one-live-session partial index, and
closed-session guards make the core safety properties database-visible rather
than prompt-only.

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = FULL;
PRAGMA busy_timeout = 5000;

CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    ddl_sha256 TEXT NOT NULL CHECK (length(ddl_sha256) = 64),
    applied_at TEXT NOT NULL
) STRICT;

CREATE TABLE streams (
    stream_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL CHECK (kind IN ('epic', 'shared')),
    epic_number INTEGER,
    created_at TEXT NOT NULL,
    CHECK (
        (kind = 'epic' AND epic_number > 0
         AND stream_id = 'epic:' || epic_number)
        OR
        (kind = 'shared' AND epic_number IS NULL
         AND stream_id LIKE 'shared:%')
    )
) STRICT;

CREATE UNIQUE INDEX streams_one_row_per_epic
    ON streams(epic_number) WHERE epic_number IS NOT NULL;

CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    stream_id TEXT NOT NULL REFERENCES streams(stream_id),
    state TEXT NOT NULL CHECK (state IN ('open', 'rolling', 'closed')),
    lineage_id TEXT NOT NULL,
    opened_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    closed_at TEXT,
    state_version INTEGER NOT NULL DEFAULT 1 CHECK (state_version > 0),
    CHECK (
        (state = 'closed' AND closed_at IS NOT NULL)
        OR
        (state != 'closed' AND closed_at IS NULL)
    ),
    UNIQUE (session_id, stream_id)
) STRICT;

CREATE UNIQUE INDEX sessions_one_live_per_stream
    ON sessions(stream_id) WHERE state IN ('open', 'rolling');

CREATE TABLE session_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stream_id TEXT NOT NULL REFERENCES streams(stream_id),
    session_id TEXT NOT NULL,
    from_state TEXT CHECK (
        from_state IS NULL OR from_state IN ('open', 'rolling', 'closed')
    ),
    to_state TEXT NOT NULL CHECK (to_state IN ('open', 'rolling', 'closed')),
    ts TEXT NOT NULL,
    agent TEXT NOT NULL,
    harness TEXT NOT NULL,
    reason TEXT NOT NULL,
    proof_refs_json TEXT NOT NULL DEFAULT '[]'
        CHECK (json_valid(proof_refs_json)),
    FOREIGN KEY (session_id, stream_id)
        REFERENCES sessions(session_id, stream_id)
) STRICT;

CREATE TABLE lease_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stream_id TEXT NOT NULL REFERENCES streams(stream_id),
    session_id TEXT NOT NULL,
    lease_id TEXT NOT NULL,
    generation INTEGER NOT NULL CHECK (generation > 0),
    fencing_token INTEGER NOT NULL CHECK (fencing_token > 0),
    event_type TEXT NOT NULL CHECK (event_type IN (
        'acquired', 'heartbeat', 'transfer_prepared', 'transferred',
        'released', 'stale_observed', 'closed'
    )),
    holder_agent TEXT NOT NULL,
    holder_harness TEXT NOT NULL,
    holder_instance_id TEXT NOT NULL,
    holder_task_id TEXT,
    ts TEXT NOT NULL,
    rollover_id TEXT,
    proof_refs_json TEXT NOT NULL DEFAULT '[]'
        CHECK (json_valid(proof_refs_json)),
    reason TEXT NOT NULL,
    FOREIGN KEY (session_id, stream_id)
        REFERENCES sessions(session_id, stream_id)
) STRICT;

-- Coordination projection. History lives in lease_events and is never erased.
CREATE TABLE stream_leases (
    stream_id TEXT PRIMARY KEY REFERENCES streams(stream_id),
    session_id TEXT NOT NULL,
    lease_id TEXT NOT NULL UNIQUE,
    generation INTEGER NOT NULL CHECK (generation > 0),
    fencing_token INTEGER NOT NULL CHECK (fencing_token > 0),
    state TEXT NOT NULL CHECK (state IN ('active', 'transferring', 'released')),
    holder_agent TEXT NOT NULL,
    holder_harness TEXT NOT NULL,
    holder_instance_id TEXT NOT NULL,
    holder_task_id TEXT,
    heartbeat_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    rollover_id TEXT,
    version INTEGER NOT NULL CHECK (version > 0),
    last_event_id INTEGER NOT NULL UNIQUE REFERENCES lease_events(event_id),
    FOREIGN KEY (session_id, stream_id)
        REFERENCES sessions(session_id, stream_id)
) STRICT;

CREATE TABLE entries (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stream_id TEXT NOT NULL REFERENCES streams(stream_id),
    session_id TEXT NOT NULL,
    agent TEXT NOT NULL,
    harness TEXT NOT NULL,
    ts TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN (
        'binding_order', 'negative_constraint', 'decision',
        'state', 'next_action', 'note'
    )),
    body TEXT NOT NULL CHECK (
        length(CAST(body AS BLOB)) BETWEEN 1 AND 65536
    ),
    body_sha256 TEXT NOT NULL CHECK (length(body_sha256) = 64),
    origin TEXT NOT NULL CHECK (origin IN ('live', 'migration')),
    writer_lease_id TEXT,
    fencing_token INTEGER,
    idempotency_key TEXT NOT NULL,
    FOREIGN KEY (session_id, stream_id)
        REFERENCES sessions(session_id, stream_id),
    CHECK (
        (origin = 'live' AND writer_lease_id IS NOT NULL
         AND fencing_token > 0)
        OR
        (origin = 'migration' AND writer_lease_id IS NULL
         AND fencing_token IS NULL)
    ),
    UNIQUE (stream_id, idempotency_key)
) STRICT;

-- The logical entry.refs array is normalized here for integrity and indexing.
CREATE TABLE entry_refs (
    entry_id INTEGER NOT NULL REFERENCES entries(entry_id),
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    kind TEXT NOT NULL CHECK (kind IN (
        'supersedes', 'shared_entry', 'github', 'rollover_proof',
        'legacy_source', 'artifact'
    )),
    target_entry_id INTEGER REFERENCES entries(entry_id),
    uri TEXT,
    CHECK (
        (target_entry_id IS NOT NULL AND uri IS NULL)
        OR
        (target_entry_id IS NULL AND uri IS NOT NULL)
    ),
    PRIMARY KEY (entry_id, ordinal)
) STRICT;

CREATE INDEX entries_stream_order ON entries(stream_id, entry_id DESC);
CREATE INDEX entries_stream_type_order
    ON entries(stream_id, type, entry_id DESC);
CREATE INDEX entries_session_order ON entries(session_id, entry_id DESC);
CREATE INDEX entry_refs_target ON entry_refs(target_entry_id, kind);

CREATE UNIQUE INDEX entry_refs_unique_target
    ON entry_refs(entry_id, kind, target_entry_id)
    WHERE target_entry_id IS NOT NULL;

CREATE UNIQUE INDEX entry_refs_unique_uri
    ON entry_refs(entry_id, kind, uri)
    WHERE uri IS NOT NULL;

CREATE TABLE legacy_imports (
    import_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_path TEXT NOT NULL,
    source_sha256 TEXT NOT NULL CHECK (length(source_sha256) = 64),
    parser_version INTEGER NOT NULL CHECK (parser_version > 0),
    stream_id TEXT NOT NULL REFERENCES streams(stream_id),
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    imported_at TEXT NOT NULL,
    first_entry_id INTEGER NOT NULL REFERENCES entries(entry_id),
    last_entry_id INTEGER NOT NULL REFERENCES entries(entry_id),
    unresolved_pinned_candidates INTEGER NOT NULL DEFAULT 0
        CHECK (unresolved_pinned_candidates >= 0),
    status TEXT NOT NULL CHECK (status IN ('imported', 'review_required')),
    UNIQUE (source_path, source_sha256)
) STRICT;

CREATE TABLE backup_receipts (
    backup_id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL CHECK (kind IN ('sqlite_snapshot', 'jsonl_export')),
    path TEXT NOT NULL UNIQUE,
    sha256 TEXT NOT NULL CHECK (length(sha256) = 64),
    created_at TEXT NOT NULL,
    verified_at TEXT NOT NULL,
    high_water_entry_id INTEGER NOT NULL REFERENCES entries(entry_id),
    schema_version INTEGER NOT NULL,
    byte_count INTEGER NOT NULL CHECK (byte_count > 0)
) STRICT;

CREATE TRIGGER sessions_valid_state_transition
BEFORE UPDATE OF state ON sessions
WHEN NOT (
    (OLD.state = 'open' AND NEW.state IN ('rolling', 'closed'))
    OR
    (OLD.state = 'rolling' AND NEW.state IN ('open', 'closed'))
)
BEGIN
    SELECT RAISE(ABORT, 'invalid session state transition');
END;

CREATE TRIGGER sessions_closed_are_terminal
BEFORE UPDATE ON sessions
WHEN OLD.state = 'closed'
BEGIN
    SELECT RAISE(ABORT, 'closed sessions are terminal');
END;

CREATE TRIGGER sessions_close_requires_released_lease
BEFORE UPDATE OF state ON sessions
WHEN NEW.state = 'closed' AND EXISTS (
    SELECT 1 FROM stream_leases l
    WHERE l.stream_id = NEW.stream_id
      AND l.session_id = NEW.session_id
      AND l.state != 'released'
)
BEGIN
    SELECT RAISE(ABORT, 'session close requires a released lease');
END;

CREATE TRIGGER sessions_no_delete
BEFORE DELETE ON sessions
BEGIN
    SELECT RAISE(ABORT, 'sessions are never deleted');
END;

CREATE TRIGGER leases_never_target_closed_session_insert
BEFORE INSERT ON stream_leases
WHEN NEW.state != 'released' AND EXISTS (
    SELECT 1 FROM sessions s
    WHERE s.session_id = NEW.session_id AND s.state = 'closed'
)
BEGIN
    SELECT RAISE(ABORT, 'closed session cannot hold a lease');
END;

CREATE TRIGGER leases_never_target_closed_session_update
BEFORE UPDATE ON stream_leases
WHEN NEW.state != 'released' AND EXISTS (
    SELECT 1 FROM sessions s
    WHERE s.session_id = NEW.session_id AND s.state = 'closed'
)
BEGIN
    SELECT RAISE(ABORT, 'closed session cannot hold or regain a lease');
END;

CREATE TRIGGER leases_projection_event_matches_insert
BEFORE INSERT ON stream_leases
WHEN NOT EXISTS (
    SELECT 1 FROM lease_events e
    WHERE e.event_id = NEW.last_event_id
      AND e.stream_id = NEW.stream_id
      AND e.session_id = NEW.session_id
      AND e.lease_id = NEW.lease_id
      AND e.generation = NEW.generation
      AND e.fencing_token = NEW.fencing_token
      AND e.holder_agent = NEW.holder_agent
      AND e.holder_harness = NEW.holder_harness
      AND e.holder_instance_id = NEW.holder_instance_id
      AND e.holder_task_id IS NEW.holder_task_id
)
BEGIN
    SELECT RAISE(ABORT, 'lease projection must match its lease event');
END;

CREATE TRIGGER leases_projection_event_matches_update
BEFORE UPDATE ON stream_leases
WHEN NOT EXISTS (
    SELECT 1 FROM lease_events e
    WHERE e.event_id = NEW.last_event_id
      AND e.stream_id = NEW.stream_id
      AND e.session_id = NEW.session_id
      AND e.lease_id = NEW.lease_id
      AND e.generation = NEW.generation
      AND e.fencing_token = NEW.fencing_token
      AND e.holder_agent = NEW.holder_agent
      AND e.holder_harness = NEW.holder_harness
      AND e.holder_instance_id = NEW.holder_instance_id
      AND e.holder_task_id IS NEW.holder_task_id
)
BEGIN
    SELECT RAISE(ABORT, 'lease projection must match its lease event');
END;

CREATE TRIGGER leases_projection_monotonic
BEFORE UPDATE ON stream_leases
WHEN NOT (
    NEW.version > OLD.version
    AND NEW.last_event_id > OLD.last_event_id
    AND NEW.fencing_token >= OLD.fencing_token
    AND NEW.generation >= OLD.generation
    AND (
        (
            NEW.session_id = OLD.session_id
            AND NEW.lease_id = OLD.lease_id
            AND NEW.holder_agent = OLD.holder_agent
            AND NEW.holder_harness = OLD.holder_harness
            AND NEW.holder_instance_id = OLD.holder_instance_id
        )
        OR
        (
            NEW.fencing_token > OLD.fencing_token
            AND NEW.generation > OLD.generation
        )
    )
)
BEGIN
    SELECT RAISE(ABORT, 'lease projection counters must advance monotonically');
END;

CREATE TRIGGER leases_no_delete
BEFORE DELETE ON stream_leases
BEGIN
    SELECT RAISE(ABORT, 'lease projections are never deleted');
END;

CREATE TRIGGER streams_no_update
BEFORE UPDATE ON streams
BEGIN
    SELECT RAISE(ABORT, 'stream identity is immutable');
END;

CREATE TRIGGER streams_no_delete
BEFORE DELETE ON streams
BEGIN
    SELECT RAISE(ABORT, 'streams are never deleted');
END;

CREATE TRIGGER entries_no_update
BEFORE UPDATE ON entries
BEGIN
    SELECT RAISE(ABORT, 'entries are append-only');
END;

CREATE TRIGGER entries_no_live_append_to_closed_session
BEFORE INSERT ON entries
WHEN NEW.origin = 'live' AND EXISTS (
    SELECT 1 FROM sessions s
    WHERE s.session_id = NEW.session_id
      AND s.stream_id = NEW.stream_id
      AND s.state = 'closed'
)
BEGIN
    SELECT RAISE(ABORT, 'live entries cannot target a closed session');
END;

CREATE TRIGGER entries_live_append_requires_current_lease
BEFORE INSERT ON entries
WHEN NEW.origin = 'live' AND NOT EXISTS (
    SELECT 1
    FROM stream_leases l
    JOIN sessions s
      ON s.session_id = l.session_id AND s.stream_id = l.stream_id
    WHERE l.stream_id = NEW.stream_id
      AND l.session_id = NEW.session_id
      AND l.lease_id = NEW.writer_lease_id
      AND l.fencing_token = NEW.fencing_token
      AND l.holder_agent = NEW.agent
      AND l.holder_harness = NEW.harness
      AND l.state IN ('active', 'transferring')
      AND s.state IN ('open', 'rolling')
)
BEGIN
    SELECT RAISE(ABORT, 'live entry requires the current fenced stream lease');
END;

CREATE TRIGGER entries_no_delete
BEFORE DELETE ON entries
BEGIN
    SELECT RAISE(ABORT, 'entries are never deleted');
END;

CREATE TRIGGER entry_refs_no_update
BEFORE UPDATE ON entry_refs
BEGIN
    SELECT RAISE(ABORT, 'entry refs are append-only');
END;

CREATE TRIGGER entry_refs_no_delete
BEFORE DELETE ON entry_refs
BEGIN
    SELECT RAISE(ABORT, 'entry refs are never deleted');
END;

CREATE TRIGGER session_events_no_update
BEFORE UPDATE ON session_events
BEGIN
    SELECT RAISE(ABORT, 'session events are append-only');
END;

CREATE TRIGGER session_events_no_delete
BEFORE DELETE ON session_events
BEGIN
    SELECT RAISE(ABORT, 'session events are never deleted');
END;

CREATE TRIGGER lease_events_no_update
BEFORE UPDATE ON lease_events
BEGIN
    SELECT RAISE(ABORT, 'lease events are append-only');
END;

CREATE TRIGGER lease_events_no_delete
BEFORE DELETE ON lease_events
BEGIN
    SELECT RAISE(ABORT, 'lease events are never deleted');
END;

CREATE TRIGGER legacy_imports_no_update
BEFORE UPDATE ON legacy_imports
BEGIN
    SELECT RAISE(ABORT, 'legacy import receipts are append-only');
END;

CREATE TRIGGER legacy_imports_no_delete
BEFORE DELETE ON legacy_imports
BEGIN
    SELECT RAISE(ABORT, 'legacy import receipts are never deleted');
END;

CREATE TRIGGER backup_receipts_no_update
BEFORE UPDATE ON backup_receipts
BEGIN
    SELECT RAISE(ABORT, 'backup receipts are append-only');
END;

CREATE TRIGGER backup_receipts_no_delete
BEFORE DELETE ON backup_receipts
BEGIN
    SELECT RAISE(ABORT, 'backup receipts are never deleted');
END;

CREATE TRIGGER schema_migrations_no_update
BEFORE UPDATE ON schema_migrations
BEGIN
    SELECT RAISE(ABORT, 'schema migration receipts are append-only');
END;

CREATE TRIGGER schema_migrations_no_delete
BEFORE DELETE ON schema_migrations
BEGIN
    SELECT RAISE(ABORT, 'schema migration receipts are never deleted');
END;
```

### Append-only boundary

`entries`, references, session events, lease events, imports, backup receipts,
and stream identity are immutable. No production command exposes `DELETE`,
truncate, compact-history, or cleanup. SQLite checkpointing and `VACUUM` may
reorganize pages but may not remove logical rows; automated `VACUUM` is not
required in v1.

`sessions` and `stream_leases` are explicit current-state projections. They may
be updated only in the same `BEGIN IMMEDIATE` transaction that first appends a
matching event and advances the projection's version/`last_event_id`. They are
never deleted. This reconciles append-only audit history with a practical
single-row lease heartbeat. Recovery can rebuild and compare projections from
events; disagreement fails closed.

Schema changes use forward-only, checksummed migrations. Startup refuses a DB
with a newer schema or a changed migration checksum. Every migration takes an
online snapshot first and records its receipt after verification.

## Cold-start selection and pinned semantics

For one stream, the non-reference selection is deliberately simple and
deterministic:

```sql
WITH pinned AS (
    SELECT * FROM entries
    WHERE stream_id = :stream
      AND type IN ('binding_order', 'negative_constraint')
),
recent AS (
    SELECT * FROM entries
    WHERE stream_id = :stream
      AND type NOT IN ('binding_order', 'negative_constraint')
    ORDER BY entry_id DESC
    LIMIT :n
),
selected AS (
    SELECT * FROM pinned
    UNION ALL
    SELECT * FROM recent
)
SELECT * FROM selected ORDER BY entry_id;
```

The digest records `N`, the stream high-water `entry_id`, pinned count, recent
count, resolved reference count, active session state, lease freshness, and a
SHA-256 over the canonical JSON projection. The default `N` is configuration,
not hard-coded policy; every caller and response states the actual value.

Pinned entries are never silently replaced by recency. A later pinned entry
may carry an explicit `supersedes` reference to an older pinned entry. Both are
still represented regardless of `N`: active pinned entries retain their full
bodies, while superseded pinned entries render as compact identity, digest, and
`SUPERSEDED by entry <id>` records. Their full immutable bodies remain
available through entry lookup, `tail`, `dump`, and `grep`. Two contradictory
pinned entries without an explicit supersession keep their full bodies and
render under a conflict warning. The renderer never infers last-write-wins
from timestamps or prose.

Reference targets are resolved after selection. They are not extra history
tail entries: they are the exact objects named by selected entries. Reference
resolution is cycle-detected and depth-bounded, and every resolved target keeps
its source stream and entry ID.

## Cross-epic shared stream

Fleet-wide facts are stored once in `shared:fleet`. Every epic digest
automatically includes active pinned `binding_order` and
`negative_constraint` entries from that stream as resolved references; a newly
appended fleet-wide prohibition therefore reaches existing epics without
rewriting them. Non-pinned shared facts require an epic entry whose
`refs.kind = shared_entry`; its body names the relationship but does not copy
the fact. A newer shared fact explicitly supersedes its prior shared entry. The
resolver follows that chain to the active shared head while still showing the
referenced history and supersession.

For example, a fleet-wide seat-loading order is appended once as a shared
pinned entry and appears by reference in every epic digest. A non-binding seat
availability observation is referenced explicitly from the epics that need
it. No fact body is copied into an epic stream.

The Monitor response distinguishes primary entries from `resolved_refs` so a
harness cannot mistake shared state for locally authored epic state. A missing,
cyclic, cross-database, or corrupt reference fails the digest with an explicit
error; it never falls back to a copied body.

## Single-active-driver lease

### Identity and fencing

A holder is the tuple:

```text
(stream_id, session_id, lease_id, generation, fencing_token,
 holder_agent, holder_harness, holder_instance_id, holder_task_id?)
```

`holder_instance_id` is the harness's exact runtime session/task identity, not
a title. `holder_task_id` is present when the harness exposes an exact native
task ID. Agent and harness describe provenance; they do not partition the
store. `generation` is the human- and receipt-visible holder/transfer epoch;
`fencing_token` is the database write-authority counter used in every compare
and append. Both counters are per-stream and never reset across closed/new
session boundaries. A heartbeat advances only projection `version`; a new
holder or new live session strictly advances both generation and fencing
token.

Every live append includes `writer_lease_id` and `fencing_token`. The write
transaction selects the current lease and requires all of the following:

- exact stream and session match;
- lease state is `active` or the same predecessor's `transferring` state;
- lease ID, fencing token, holder agent, harness, and instance match;
- session is `open` or `rolling`, never `closed`;
- idempotency key is new or resolves to the byte-identical prior entry.

Lease acquisition or transfer increments the fencing token. A delayed old
driver therefore cannot append after transfer even if its process remains
alive.

### Initial open

1. Resolve the epic through the authoritative issue-stream registry.
2. In `BEGIN IMMEDIATE`, ensure the stream has no `open`/`rolling` session and
   no non-released lease.
3. Insert the new `open` session and `acquired` session/lease events.
4. Insert the lease projection with generation 1 and fencing token 1 only for
   the stream's first session. For every later session, advance both counters
   beyond the retained released projection, then commit.
5. Return the exact lease envelope to the holder; no other holder may write.

### Normal rollover or deliberate interim transfer

1. The holder runs the existing `thread_handoff.py prepare` flow. Its exact
   rollover registry key and immutable plan are persisted before stream state
   changes.
2. `session-streams lease transfer-prepare` validates that receipt, appends a
   `transfer_prepared` lease event, moves the session `open -> rolling`, and
   marks the current lease `transferring`. The predecessor remains the only
   writer.
3. SessionStart detects the exact packet. The replacement reads the stream
   digest, runs exact `resume`, writes the reserved semantic snapshot, scores
   strict recall, runs the challenge canary, and calls `confirm-started`.
4. `session-streams lease transfer-apply` validates the exact registry state
   and both proof files. In one transaction it appends `transferred`, increments
   generation and fencing token, installs the replacement holder, updates the
   heartbeat, and moves `rolling -> open`.
5. Only then can the successor write stream entries. Existing rollover cleanup
   separately decides whether the predecessor task and heartbeat automation
   may be archived or retired.

### Stale-holder recovery

Heartbeat expiry alone never transfers a lease. It appends `stale_observed`
once for the observed lease version and makes a read-only takeover plan
available.

The plan fails immediately if the session is `closed`. Otherwise:

- If a live prepared/resumed rollover exists, the plan names that exact
  `(agent, lineage_id, rollover_id)` and emits only the existing detect/resume,
  strict-recall, canary, and confirmation commands. It never chooses by age or
  filesystem order.
- If rollover state is ambiguous or corrupt, the plan requires rollover
  registry `audit` and `reconcile-exact`. No DB mutation occurs.
- If no packet exists because the holder died before preparation, an explicit
  operator recovery plan names the exact predecessor holder and invokes the
  existing `thread_handoff.py prepare` path with recovery evidence. The stream
  layer does not mint an alternative claim protocol. The candidate still must
  pass exact resume, strict recall, canary, and confirmation before transfer.

Recovery-prepare authority belongs only to the operator or to the accountable
stream orchestrator carrying a durable launch/task-identity receipt that sets
`recovery_takeover=true` and binds the exact stream, predecessor lease
ID/version, and candidate instance ID. The plan also records the stale-observed
event, heartbeat age, clean source-checkout binding, rollover audit showing no
live packet, and proof that the session is not closed. Ordinary drivers cannot
self-authorize this path.

`takeover --apply` accepts only the immutable plan digest and the resulting
existing rollover receipts. A different candidate, holder, lease version,
session, rollover, or stream invalidates the plan. No unattended timer performs
this action.

### Close

An ordinary `open -> closed` close requires the current lease/fencing token, no
unresolved rollover, and an explicit close plan. A `rolling -> closed` close is
a separate recovery variant: rollover registry reconciliation must prove the
exact packet abandoned or terminal, no valid replacement owns it, no native
create is unrecorded, and no heartbeat depends on it. Timeout alone cannot
satisfy that proof.

The holder appends final `state`/`next_action` entries as appropriate, creates
and verifies a backup, then applies the approved close plan in one transaction:

- append session `closed` and lease `closed`/`released` events;
- move the lease projection to `released`;
- move the session to `closed` with `closed_at`;
- commit.

The SQL trigger rejects all later session updates and any non-released lease
for that session. Resuming work means opening a new session in the same stream;
it is never called takeover of the closed session.

## Monitor API: the shared read surface

Agents and harnesses do not open the DB directly. The operator CLI is the only
supported direct reader. Monitor exposes:

```text
GET /api/session/streams/{stream_id}/digest
    ?limit=<N>&format=markdown|json

GET /api/session/streams/{stream_id}/entries/{entry_id}
    ?format=markdown|json
```

The digest JSON includes:

- schema version, stream identity, digest hash, and high-water entry ID;
- current session ID/state and safe lease provenance/freshness fields;
- `limit`, `pinned_count`, `recent_count`, and truncation metadata;
- ordered primary entries with logical `refs` arrays;
- `resolved_refs`, preserving target stream/entry identity and supersession;
- conflict, stale-heartbeat, migration, and corruption warnings.

Bodies are never returned from another stream merely because an agent name
matches. Reads are parameterized, `query_only`, bounded, and ETag-aware. The
manifest gains an explicit stream component only when the caller supplies a
known stream; generic bootstrap stays stream-free and does not guess.

`MonitorClient.bootstrap(stream="epic:4707", limit=20)` returns rules plus the
stream digest. `/api/session/current` remains compatibility-only during
migration. Once a stream is supplied, its response is the same canonical
digest projection, not a second file-backed interpretation.

Monitor TUI consumes the JSON endpoint and displays stream, session state,
lease holder/freshness, pinned orders/constraints, recent entries, resolved
shared facts, conflicts, migration status, and backup age. V1 TUI is read-only;
it shows exact copyable CLI commands for mutations rather than inventing a
second mutation surface.

## Operator CLI

The CLI entry point is:

```bash
.venv/bin/python -m agents_extensions.shared.session_streams --help
```

Every parser and subparser follows
`agents_extensions/shared/rules/cli-help-standard.md`: two-line description,
meaningful help and defaults for every argument, concrete examples, outputs,
side effects, exit codes, and related contracts.

### Required read window

```bash
# Pinned entries plus the last 20 non-pinned entries.
.venv/bin/python -m agents_extensions.shared.session_streams tail \
  --stream epic:4707 --limit 20 --format table

# Complete, ordered history for operator inspection or a portable artifact.
.venv/bin/python -m agents_extensions.shared.session_streams dump \
  --stream epic:4707 --format jsonl --output /absolute/approved/path.jsonl

# Literal body search across all history; results stay bounded.
.venv/bin/python -m agents_extensions.shared.session_streams grep \
  --stream epic:4707 --fixed-strings "seat loading" --limit 100
```

`tail` uses cold-start semantics by default and marks pinned, superseded,
conflicting, and reference-resolved rows. `--recent-only` is an explicit
operator option. `dump` includes entries, refs, sessions, lease events, imports,
schema migrations, and backup receipts; it never mutates. `grep` searches all
entry bodies with parameterized SQL, not only the tail, and reports truncation.

### Other command groups

```text
append                         append one typed entry under the exact lease
session open|close-plan|close-apply
lease show|heartbeat|transfer-prepare|transfer-apply|takeover-plan|takeover-apply
migrate inventory|plan|apply|verify
backup snapshot|export|verify
audit                          integrity, projection, pin, ref, lease, backup checks
```

Planning commands are read-only. Mutating commands require exact IDs,
idempotency keys, and plan digests as applicable. No command accepts a mutable
title as identity. Proposed exit classes are 0 success, 2 usage, 3 not found,
4 lease/version conflict, 5 integrity/corruption failure, and 6 secret/PII
rejection.

## Migration and Claude compatibility

Migration is per stream and per harness. There is no repository-wide big-bang
switch.

### Sources

The importer supports:

- `.claude/<epic>-epic/CLAUDE-DRIVER-HANDOFF.md` and its local archive;
- `docs/session-state/current.<agent>.md` and agent-specific durable handoffs;
- the compatibility router only as a path map, never as semantic content when
  it merely points elsewhere.

Epic handoff paths map directly to an explicitly supplied epic stream.
Agent-only `current.*.md` paths do not prove an epic and require
`--stream epic:<number>` or `--stream shared:fleet`; the importer never infers
scope from `claude`, `codex`, or `orchestrator`.

### Import semantics

Import is two-step and idempotent:

1. `migrate plan` records path, content SHA-256, target stream/session, proposed
   typed entries, and unresolved pinned candidates without writing.
2. `migrate apply` accepts that plan digest, creates entries with
   `origin=migration`, and appends a `legacy_imports` receipt. Repeating the same
   path/hash is a no-op; changed content is a new import, never an update.

The full legacy document is preserved as a `state` entry with a
`legacy_source` reference and content hash. Only explicit structural markers
are automatically split into typed entries. The importer may surface candidate
orders/constraints for review, but it never guesses that free prose is pinned.
Cutover is blocked while `unresolved_pinned_candidates > 0`. The operator or
current driver appends the reviewed `binding_order`/`negative_constraint`
entries with references back to the import.

Legacy imports use a closed migration session so they can never acquire or be
taken over as a live driver session.

### Phases

#### Phase 0: inventory and snapshot

- Inventory every configured epic handoff and `current.*.md` source.
- Record missing, unreadable, oversized, duplicate, and ambiguous sources.
- Take and verify pre-migration copies; do not edit or delete a source.
- Create streams and closed migration sessions only after explicit mapping.

#### Phase 1: shadow import

- Files remain authoritative.
- Import and render DB digests side-by-side with file hashes.
- Resolve all pinned candidates and reference errors.
- SessionStart still injects the file handoff, plus a short shadow-status line;
  DB digest is not yet trusted as continuity state.

#### Phase 2: dual write

- Update source-owned driver prompts to use one `append --legacy-target ...`
  shim. It appends to the DB first under an idempotency key, then atomically
  updates the compatibility file with the DB entry ID/hash marker.
- A file-write failure does not roll back durable DB history. It records a
  delivery failure and retry command; the file remains authoritative until the
  pair verifies.
- SessionStart injects the canonical DB digest in the existing epic-handoff
  slot and retains the exact file fallback path immediately below it.
- A startup drift check imports or blocks on manual file edits so an older
  Claude driver cannot silently bypass dual write.

#### Phase 3: per-stream cutover

Cut over one stream only after:

- every known source hash has an import receipt;
- unresolved pinned candidates and broken refs are zero;
- two successive cold starts for Claude and one non-Claude harness produce the
  expected pinned-plus-tail digest;
- one real rollover passes exact resume, strict 10/10 recall, challenge canary,
  confirmation, and stream lease transfer;
- snapshot restore is tested in a temporary location;
- the operator approves that stream's evidence.

The DB becomes authoritative. Files become generated compatibility projections
and are no longer manually edited.

#### Phase 4: file retirement

After all required harnesses pass and the operator separately authorizes
retirement:

- remove file reads and writes from normal cold start;
- stop generating compatibility projections;
- retain legacy files and import receipts as read-only historical evidence;
- keep explicit offline recovery documentation and immutable exports.

Retirement means "not a live protocol," not deletion. No migration phase
deletes handoffs or archive files.

### SessionStart injection order

Claude compatibility preserves the current layering:

```text
1. Session profile capsule and assigned epic identity
2. Exact pending/resumed rollover packet from thread_handoff.py, if any
3. Canonical stream digest from Monitor  <-- replaces the live file-handoff slot
4. During dual write only: exact legacy file fallback and drift status
5. Existing setup issues/info
```

The stream digest is therefore loaded exactly where the epic driver handoff is
read today: after the rollover packet, before ordinary orientation and queue
work. It never precedes or hides an exact rollover claim.

If Monitor or the DB is unavailable during dual write, SessionStart visibly
falls back to the verified file and marks the DB degraded. After file
retirement, unavailability is a stop condition; a harness must not continue
from an empty or guessed stream.

## Harness onboarding flows

### Claude epic driver

1. Launcher/task identity supplies the assigned lane and numeric stream epic;
   SessionStart validates both and resolves `epic:<number>`. A multi-epic lane
   without the numeric value stops rather than guessing.
2. SessionStart detects and injects any exact rollover packet first.
3. It requests the Monitor digest and injects pinned orders/constraints,
   resolved shared facts, and the last `N` other entries in the old handoff
   slot.
4. Claude acquires or resumes the exact stream lease before appending.
5. During migration, the dual-write shim keeps the existing epic file current.
6. Rollover follows existing commands; stream transfer consumes the resulting
   confirmation receipts.

### Codex and Task Family Manager

1. Codex's SessionStart hook receives an explicit stream from task identity or
   the user assignment; absent stream identity stays generic and does not
   guess.
2. It uses the same Monitor digest and source-owned write CLI.
3. Native task UUIDs and typed replacement relations come from Task Family
   Manager/rollover receipts. Session streams never read or write Codex's
   provider-owned SQLite DB.
4. Task archive/restore and predecessor cleanup remain Task Family Manager
   operations, independent from stream lease transfer.

### Grok, Gemini/AGY, Kimi, and interim stand-ins

1. The dispatch or launcher carries exact `stream_id`, session intent, actual
   agent, actual harness, and exact runtime instance ID.
2. The harness calls Monitor for the digest and the common CLI for heartbeat
   and writes. No provider-specific handoff parser is needed.
3. A stand-in either receives a confirmed lease transfer within the open
   session or opens a new session after close. It never rewrites agent-owned
   memory because memory is stream-owned.
4. If a harness lacks native task IDs, its exact harness instance ID is the
   holder identity and the rollover fallback receipt records that limitation.

### Monitor TUI/operator

The operator selects a stream, sees the current/closed session, exact holder,
heartbeat age, pinned set, recent tail, resolved shared facts, conflicts,
migration drift, and latest verified backup. The TUI reads Monitor only and
does not run SQL or infer ownership. Mutations remain copyable CLI plans in v1.

## Backup, export, and recovery

WAL does not replace backup. The system creates:

- an online SQLite backup through `sqlite3.Connection.backup()`;
- a canonical JSONL export ordered by table and primary key;
- a manifest containing schema version, high-water entry ID, file sizes, and
  SHA-256 digests;
- an append-only `backup_receipts` row only after reopening and verifying the
  snapshot/export.

Triggers are:

- before and after every schema migration;
- before session close;
- after successful per-stream cutover;
- periodically through the existing Monitor/scheduler mechanism, not an agent
  polling loop.

Backups use timestamped, never-overwritten names in an operator-configurable
directory outside the DB directory. No automatic rotation or cleanup exists.
The default should be on a different durable volume when configured; a same-disk
snapshot is still useful for logical corruption but is not disaster recovery.

Exports and snapshots are recovery artifacts, not alternate cold-start stores.
Restore always targets a new temporary path, runs `PRAGMA integrity_check`,
validates migration checksums, replays projection audits, compares the
high-water receipt, and requires explicit operator promotion. It never
overwrites the live DB in place.

## Secret, PII, and content hygiene

The write boundary applies the same no-secret rule as the project hooks and
adds stream-specific validation:

- reject known token/key/private-key/dotenv dump shapes and high-confidence
  credential patterns;
- reject email addresses, phone numbers, and other configured PII patterns
  unless an explicit non-sensitive allow-list rule exists;
- reject binary/NUL content, control characters, invalid UTF-8, empty bodies,
  and bodies over 64 KiB;
- store references and hashes instead of logs, transcripts, environment dumps,
  or large tool output;
- return only the rule name and safe location on rejection, never echo the
  suspected secret;
- apply the same safe-output check to CLI and Monitor renderers as defense in
  depth.

Automatic detection is a guardrail, not permission to store questionable data.
Prompts explicitly prohibit secrets/PII. A discovered sensitive entry cannot
be deleted under the append-only contract; incident handling must revoke the
secret, quarantine DB access, append a redaction notice, and restore a
sanitized replacement DB under an operator-approved exceptional procedure.
This is why prevention is a release gate.

## Failure modes and mitigations

| Risk | Consequence | Mitigation / fail-closed behavior |
| --- | --- | --- |
| Binding order scrolls out | Operator intent is lost. | Pinned types bypass `N`; digest tests assert this with more than `N` later entries. |
| Conflicting pinned orders | Agent chooses a convenient interpretation. | Both render; only explicit `supersedes` changes active status; unresolved conflict is prominent. |
| Two drivers write concurrently | Split-brain stream history. | `BEGIN IMMEDIATE`, one lease row, increasing fencing token, exact holder tuple, idempotency key. |
| Dead driver heartbeat expires | Unsafe automatic takeover. | Expiry only appends `stale_observed`; existing rollover/canary proof plus exact plan digest is required. |
| Closed session is reclaimed | Terminal history is rewritten as live. | SQL terminal trigger, one-live-session index, lease closed guard, command-level rejection, regression tests. |
| File and DB diverge in migration | Claude and interim drivers see different memory. | Hash markers, idempotent imports, visible drift, per-stream cutover gate, verified file fallback. |
| Shared fact is copied | Epics drift from fleet truth. | `shared:fleet` entry IDs and explicit refs; resolver returns target identity; no copied body in epic entry. |
| Shared ref is broken/cyclic | Digest is incomplete or loops. | FK integrity for local targets, cycle/depth checks, explicit digest failure. |
| WAL/DB corruption | All harnesses lose current memory. | Full synchronous writes, integrity audit, online snapshots, JSONL export, restore drill, no in-place overwrite. |
| DB grows forever | Read or backup performance degrades. | Indexed bounded reads, no cold-start full scans, measurable size/latency SLOs, incremental implementation profiling; no history deletion. |
| Heartbeat history grows quickly | Unnecessary append volume. | Configurable bounded heartbeat cadence; one event per accepted heartbeat, indexed by stream/event ID; no busy polling. |
| Monitor unavailable | Harness silently cold-starts empty. | Dual-write file fallback before retirement; hard stop after retirement; no guessed default stream. |
| Provider title used as identity | Wrong task/stream takeover. | Exact task/runtime IDs and typed receipts only; titles are display data. |
| Secret enters append-only DB | Durable sensitive data exposure. | Pre-write and pre-render guards, rejection without echo, tests, operator incident procedure. |
| Migration classifier guesses semantics | A user order becomes an unpinned note. | Full-document state import, explicit-marker-only typing, unresolved-pinned gate, human/driver review before cutover. |

## Implementation chunks

Each chunk is one reviewable PR, stays below the 20-file artifact warning where
practical, and contains no generated deploy targets or runtime DB/export files.
No implementation chunk starts until the operator accepts this design.

### PR 1: Core schema and deterministic storage

- Add the source package, v1 DDL, canonical-root resolution, migrations,
  immutable triggers, transaction helpers, entry model, and audit.
- Add tests for WAL, schema checksums, append immutability, pinned selection,
  explicit supersession, one-live-session, closed terminality, idempotency, and
  fencing.
- No hooks, Monitor routes, file migration, or lease takeover yet.

### PR 2: Operator CLI and safe rendering

- Add argparse-standard `tail`, `dump`, `grep`, `append`, and `audit`.
- Add secret/PII rejection and safe-output tests.
- Validate DDL and CLI against a temporary DB; no live DB creation by tests.

### PR 3: Monitor read API and TUI read panel

- Mount the source-owned router, ETag/hash support, bounded JSON/Markdown
  digest, explicit stream manifest component, entry lookup, and resolved refs.
- Add read-only TUI panel and route-contract tests.
- Preserve generic bootstrap and `/api/session/current` compatibility.
- Exercise session/lease fields through fixtures and closed migration sessions;
  live lease integration coverage belongs to PR 4.

### PR 4: Session and lease lifecycle

- Add open, heartbeat, close plan/apply, lease projection/event audit, and
  fencing enforcement on append.
- Add concurrent-writer, stale-heartbeat, projection-rebuild, and closed-session
  adversarial tests.
- Do not add takeover until ordinary lifecycle is proven.

### PR 5: Rollover adapter and proof-gated transfer

- Compose existing `thread_handoff` detect/prepare/resume/confirm receipts;
  render DB-selected semantic anchors at the existing reserved packet path.
- Add transfer-prepare/apply and read-only takeover-plan/apply.
- Test normal rollover, pending-packet recovery, ambiguous registry refusal,
  stale-only refusal, mismatched receipt refusal, old-token fencing, and
  independent predecessor-cleanup gating.

### PR 6: Legacy inventory, import, and dual-write shim

- Add inventory/plan/apply/verify for Claude epic and `current.*` sources.
- Add full-source preservation, explicit-marker parsing, unresolved pinned
  review, drift detection, and idempotent hash receipts.
- Update source prompts/hooks for dual write; deploy copies remain generated.
- Run shadow mode only; no stream cutover in this PR.

### PR 7: Per-harness cold-start acceptance and first gated cutover

- Inject the digest in the current SessionStart handoff slot.
- Prove Claude, Codex, one other CLI harness, Monitor TUI, and one full rollover.
- Exercise backup restore and capture latency/size evidence.
- Present evidence to the operator; cut over only the explicitly approved pilot
  stream. Keep file fallback for every other stream.

### PR 8: Backup scheduling and later file retirement

- Wire periodic online snapshot/export through the existing scheduler.
- Add freshness warnings and restore drills.
- Retire compatibility files only per stream after all acceptance evidence and
  a separate operator authorization. Retain historical files; never delete.

## Acceptance evidence required before implementation dispatch

The operator should approve or amend this design before PR 1. Implementation
briefs must preserve these measurable gates:

- a closed session cannot be updated, live-appended, leased, or taken over in
  direct SQL and public-command tests;
- two simultaneous holders cannot both append, and an old fencing token fails
  after transfer;
- reopening a stream after close advances the retained per-stream generation
  and fencing counters rather than resetting them;
- a stale heartbeat without rollover/canary proof cannot transfer a lease;
- every pinned order/constraint is present after more than `N` later entries;
- a shared fact is stored once and resolved by exact entry reference;
- Claude receives rollover first and stream digest in the prior file-handoff
  slot, with verified fallback during dual write;
- each migration source has a content hash/import receipt and zero unresolved
  pinned candidates before cutover;
- WAL, integrity check, verified snapshot, JSONL export, and restore audit pass;
- every opened read/write connection proves `foreign_keys=1` and applies the
  configured timeout/synchronous policy;
- no session-stream source logic or prompts are maintained in deploy targets;
- no secrets, PII, runtime DBs, telemetry, generated handoffs, or backup exports
  appear in a PR diff.

Until those gates are implemented and the operator approves a pilot cutover,
the current file handoffs and rollover machinery remain authoritative.
