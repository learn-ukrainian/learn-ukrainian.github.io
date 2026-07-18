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
    proof_json TEXT NOT NULL DEFAULT '{}'
        CHECK (json_valid(proof_json)),
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
        'acquired', 'heartbeat', 'released', 'stale_observed', 'force_closed'
    )),
    holder_agent TEXT NOT NULL,
    holder_harness TEXT NOT NULL,
    holder_instance_id TEXT NOT NULL,
    holder_task_id TEXT,
    holder_process_id INTEGER NOT NULL CHECK (holder_process_id > 0),
    ttl_seconds INTEGER NOT NULL CHECK (ttl_seconds > 0),
    ts TEXT NOT NULL,
    proof_json TEXT NOT NULL DEFAULT '{}'
        CHECK (json_valid(proof_json)),
    reason TEXT NOT NULL,
    FOREIGN KEY (session_id, stream_id)
        REFERENCES sessions(session_id, stream_id)
) STRICT;

CREATE TABLE stream_leases (
    stream_id TEXT PRIMARY KEY REFERENCES streams(stream_id),
    session_id TEXT NOT NULL,
    lease_id TEXT NOT NULL UNIQUE,
    generation INTEGER NOT NULL CHECK (generation > 0),
    fencing_token INTEGER NOT NULL CHECK (fencing_token > 0),
    state TEXT NOT NULL CHECK (state IN ('active', 'released')),
    holder_agent TEXT NOT NULL,
    holder_harness TEXT NOT NULL,
    holder_instance_id TEXT NOT NULL,
    holder_task_id TEXT,
    holder_process_id INTEGER NOT NULL CHECK (holder_process_id > 0),
    heartbeat_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    ttl_seconds INTEGER NOT NULL CHECK (ttl_seconds > 0),
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
    writer_instance_id TEXT,
    fencing_token INTEGER,
    idempotency_key TEXT NOT NULL,
    FOREIGN KEY (session_id, stream_id)
        REFERENCES sessions(session_id, stream_id),
    CHECK (
        (origin = 'live' AND writer_lease_id IS NOT NULL
         AND writer_instance_id IS NOT NULL AND fencing_token > 0)
        OR
        (origin = 'migration' AND writer_lease_id IS NULL
         AND writer_instance_id IS NULL AND fencing_token IS NULL)
    ),
    UNIQUE (stream_id, idempotency_key)
) STRICT;

CREATE TABLE entry_refs (
    entry_id INTEGER NOT NULL REFERENCES entries(entry_id),
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    kind TEXT NOT NULL,
    target_entry_id INTEGER REFERENCES entries(entry_id),
    uri TEXT,
    CHECK (
        (target_entry_id IS NOT NULL AND uri IS NULL)
        OR
        (target_entry_id IS NULL AND uri IS NOT NULL)
    ),
    PRIMARY KEY (entry_id, ordinal)
) STRICT;

CREATE TABLE legacy_mirrors (
    mirror_id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile TEXT NOT NULL,
    source_path TEXT NOT NULL,
    source_sha256 TEXT NOT NULL CHECK (length(source_sha256) = 64),
    source_bytes INTEGER NOT NULL CHECK (source_bytes > 0),
    stream_id TEXT NOT NULL REFERENCES streams(stream_id),
    session_id TEXT NOT NULL,
    entry_id INTEGER NOT NULL REFERENCES entries(entry_id),
    mirrored_at TEXT NOT NULL,
    FOREIGN KEY (session_id, stream_id)
        REFERENCES sessions(session_id, stream_id),
    UNIQUE (profile, source_path, source_sha256)
) STRICT;

CREATE INDEX entries_stream_order ON entries(stream_id, entry_id DESC);
CREATE INDEX entries_stream_type_order
    ON entries(stream_id, type, entry_id DESC);
CREATE INDEX entries_session_order ON entries(session_id, entry_id DESC);
CREATE INDEX entry_refs_target ON entry_refs(target_entry_id, kind);
CREATE INDEX session_events_stream_order
    ON session_events(stream_id, event_id DESC);
CREATE INDEX lease_events_stream_order
    ON lease_events(stream_id, event_id DESC);

CREATE UNIQUE INDEX entry_refs_unique_target
    ON entry_refs(entry_id, kind, target_entry_id)
    WHERE target_entry_id IS NOT NULL;

CREATE UNIQUE INDEX entry_refs_unique_uri
    ON entry_refs(entry_id, kind, uri)
    WHERE uri IS NOT NULL;

CREATE TRIGGER sessions_valid_state_transition
BEFORE UPDATE OF state ON sessions
WHEN NEW.state != OLD.state AND NOT (
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
    SELECT 1 FROM stream_leases AS lease
    WHERE lease.stream_id = NEW.stream_id
      AND lease.session_id = NEW.session_id
      AND lease.state != 'released'
)
BEGIN
    SELECT RAISE(ABORT, 'session close requires a released lease');
END;

CREATE TRIGGER sessions_no_delete
BEFORE DELETE ON sessions
BEGIN
    SELECT RAISE(ABORT, 'sessions are never deleted');
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

CREATE TRIGGER leases_never_target_closed_session_insert
BEFORE INSERT ON stream_leases
WHEN NEW.state != 'released' AND EXISTS (
    SELECT 1 FROM sessions AS session
    WHERE session.session_id = NEW.session_id AND session.state = 'closed'
)
BEGIN
    SELECT RAISE(ABORT, 'closed session cannot hold a lease');
END;

CREATE TRIGGER leases_never_target_closed_session_update
BEFORE UPDATE ON stream_leases
WHEN NEW.state != 'released' AND EXISTS (
    SELECT 1 FROM sessions AS session
    WHERE session.session_id = NEW.session_id AND session.state = 'closed'
)
BEGIN
    SELECT RAISE(ABORT, 'closed session cannot hold or regain a lease');
END;

CREATE TRIGGER leases_projection_event_matches_insert
BEFORE INSERT ON stream_leases
WHEN NOT EXISTS (
    SELECT 1 FROM lease_events AS event
    WHERE event.event_id = NEW.last_event_id
      AND event.stream_id = NEW.stream_id
      AND event.session_id = NEW.session_id
      AND event.lease_id = NEW.lease_id
      AND event.generation = NEW.generation
      AND event.fencing_token = NEW.fencing_token
      AND event.holder_agent = NEW.holder_agent
      AND event.holder_harness = NEW.holder_harness
      AND event.holder_instance_id = NEW.holder_instance_id
      AND event.holder_task_id IS NEW.holder_task_id
      AND event.holder_process_id = NEW.holder_process_id
      AND event.ttl_seconds = NEW.ttl_seconds
)
BEGIN
    SELECT RAISE(ABORT, 'lease projection must match its lease event');
END;

CREATE TRIGGER leases_projection_event_matches_update
BEFORE UPDATE ON stream_leases
WHEN NOT EXISTS (
    SELECT 1 FROM lease_events AS event
    WHERE event.event_id = NEW.last_event_id
      AND event.stream_id = NEW.stream_id
      AND event.session_id = NEW.session_id
      AND event.lease_id = NEW.lease_id
      AND event.generation = NEW.generation
      AND event.fencing_token = NEW.fencing_token
      AND event.holder_agent = NEW.holder_agent
      AND event.holder_harness = NEW.holder_harness
      AND event.holder_instance_id = NEW.holder_instance_id
      AND event.holder_task_id IS NEW.holder_task_id
      AND event.holder_process_id = NEW.holder_process_id
      AND event.ttl_seconds = NEW.ttl_seconds
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
            AND NEW.holder_process_id = OLD.holder_process_id
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

CREATE TRIGGER entries_no_update
BEFORE UPDATE ON entries
BEGIN
    SELECT RAISE(ABORT, 'entries are append-only');
END;

CREATE TRIGGER entries_no_delete
BEFORE DELETE ON entries
BEGIN
    SELECT RAISE(ABORT, 'entries are never deleted');
END;

CREATE TRIGGER entries_live_append_requires_current_lease
BEFORE INSERT ON entries
WHEN NEW.origin = 'live' AND NOT EXISTS (
    SELECT 1
    FROM stream_leases AS lease
    JOIN sessions AS session
      ON session.session_id = lease.session_id
     AND session.stream_id = lease.stream_id
    WHERE lease.stream_id = NEW.stream_id
      AND lease.session_id = NEW.session_id
      AND lease.lease_id = NEW.writer_lease_id
      AND lease.fencing_token = NEW.fencing_token
      AND lease.holder_agent = NEW.agent
      AND lease.holder_harness = NEW.harness
      AND lease.holder_instance_id = NEW.writer_instance_id
      AND lease.state = 'active'
      AND lease.expires_at > NEW.ts
      AND session.state IN ('open', 'rolling')
)
BEGIN
    SELECT RAISE(ABORT, 'live entry requires a valid current fenced lease');
END;

CREATE TRIGGER entry_refs_no_update
BEFORE UPDATE ON entry_refs
BEGIN
    SELECT RAISE(ABORT, 'entry refs are append-only');
END;

CREATE TRIGGER entry_refs_no_delete
BEFORE DELETE ON entry_refs
BEGIN
    SELECT RAISE(ABORT, 'entry refs are append-only');
END;

CREATE TRIGGER session_events_no_update
BEFORE UPDATE ON session_events
BEGIN
    SELECT RAISE(ABORT, 'session events are append-only');
END;

CREATE TRIGGER session_events_no_delete
BEFORE DELETE ON session_events
BEGIN
    SELECT RAISE(ABORT, 'session events are append-only');
END;

CREATE TRIGGER session_events_reject_closed_target
BEFORE INSERT ON session_events
WHEN EXISTS (
    SELECT 1 FROM sessions AS session
    WHERE session.session_id = NEW.session_id AND session.state = 'closed'
)
BEGIN
    SELECT RAISE(ABORT, 'closed sessions accept no later events');
END;

CREATE TRIGGER lease_events_no_update
BEFORE UPDATE ON lease_events
BEGIN
    SELECT RAISE(ABORT, 'lease events are append-only');
END;

CREATE TRIGGER lease_events_no_delete
BEFORE DELETE ON lease_events
BEGIN
    SELECT RAISE(ABORT, 'lease events are append-only');
END;

CREATE TRIGGER schema_migrations_no_update
BEFORE UPDATE ON schema_migrations
BEGIN
    SELECT RAISE(ABORT, 'schema migration receipts are immutable');
END;

CREATE TRIGGER schema_migrations_no_delete
BEFORE DELETE ON schema_migrations
BEGIN
    SELECT RAISE(ABORT, 'schema migration receipts are never deleted');
END;

CREATE TRIGGER legacy_mirrors_no_update
BEFORE UPDATE ON legacy_mirrors
BEGIN
    SELECT RAISE(ABORT, 'legacy mirror receipts are append-only');
END;

CREATE TRIGGER legacy_mirrors_no_delete
BEFORE DELETE ON legacy_mirrors
BEGIN
    SELECT RAISE(ABORT, 'legacy mirror receipts are append-only');
END;
