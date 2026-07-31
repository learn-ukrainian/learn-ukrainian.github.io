-- GUI-native holders have a task UUID rather than an honest stable PID.
-- Rebuild only the two lease projections; 0001/0002 remain immutable receipts.

DROP TRIGGER leases_never_target_closed_session_insert;
DROP TRIGGER leases_never_target_closed_session_update;
DROP TRIGGER sessions_close_requires_released_lease;
DROP TRIGGER leases_projection_event_matches_insert;
DROP TRIGGER leases_projection_event_matches_update;
DROP TRIGGER leases_projection_monotonic;
DROP TRIGGER leases_no_delete;
DROP TRIGGER lease_events_no_update;
DROP TRIGGER lease_events_no_delete;
DROP TRIGGER entries_live_append_requires_current_lease;
DROP TRIGGER entries_no_update;

ALTER TABLE lease_events RENAME TO lease_events_v2;

CREATE TABLE lease_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stream_id TEXT NOT NULL REFERENCES streams(stream_id),
    session_id TEXT NOT NULL,
    lease_id TEXT NOT NULL,
    generation INTEGER NOT NULL CHECK (generation > 0),
    fencing_token INTEGER NOT NULL CHECK (fencing_token > 0),
    event_type TEXT NOT NULL CHECK (event_type IN (
        'acquired', 'heartbeat', 'appended', 'transitioned', 'released',
        'stale_observed', 'force_closed', 'recovered'
    )),
    holder_kind TEXT NOT NULL CHECK (holder_kind IN ('process', 'app_thread')),
    holder_agent TEXT NOT NULL,
    holder_harness TEXT NOT NULL,
    holder_instance_id TEXT NOT NULL,
    holder_task_id TEXT,
    holder_process_id INTEGER,
    ttl_seconds INTEGER NOT NULL CHECK (ttl_seconds > 0),
    ts TEXT NOT NULL,
    proof_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(proof_json)),
    reason TEXT NOT NULL,
    FOREIGN KEY (session_id, stream_id) REFERENCES sessions(session_id, stream_id),
    CHECK ((holder_kind = 'process' AND holder_process_id > 0)
        OR (holder_kind = 'app_thread' AND holder_process_id IS NULL AND holder_task_id IS NOT NULL))
) STRICT;

INSERT INTO lease_events(
    event_id, stream_id, session_id, lease_id, generation, fencing_token, event_type,
    holder_kind, holder_agent, holder_harness, holder_instance_id, holder_task_id,
    holder_process_id, ttl_seconds, ts, proof_json, reason
)
SELECT event_id, stream_id, session_id, lease_id, generation, fencing_token, event_type,
       'process', holder_agent, holder_harness, holder_instance_id, holder_task_id,
       holder_process_id, ttl_seconds, ts, proof_json, reason
FROM lease_events_v2;

ALTER TABLE stream_leases RENAME TO stream_leases_v2;

CREATE TABLE stream_leases (
    stream_id TEXT PRIMARY KEY REFERENCES streams(stream_id),
    session_id TEXT NOT NULL,
    lease_id TEXT NOT NULL UNIQUE,
    generation INTEGER NOT NULL CHECK (generation > 0),
    fencing_token INTEGER NOT NULL CHECK (fencing_token > 0),
    state TEXT NOT NULL CHECK (state IN ('active', 'released')),
    holder_kind TEXT NOT NULL CHECK (holder_kind IN ('process', 'app_thread')),
    holder_agent TEXT NOT NULL,
    holder_harness TEXT NOT NULL,
    holder_instance_id TEXT NOT NULL,
    holder_task_id TEXT,
    holder_process_id INTEGER,
    heartbeat_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    ttl_seconds INTEGER NOT NULL CHECK (ttl_seconds > 0),
    version INTEGER NOT NULL CHECK (version > 0),
    last_event_id INTEGER NOT NULL UNIQUE REFERENCES lease_events(event_id),
    FOREIGN KEY (session_id, stream_id) REFERENCES sessions(session_id, stream_id),
    CHECK ((holder_kind = 'process' AND holder_process_id > 0)
        OR (holder_kind = 'app_thread' AND holder_process_id IS NULL AND holder_task_id IS NOT NULL))
) STRICT;

INSERT INTO stream_leases(
    stream_id, session_id, lease_id, generation, fencing_token, state, holder_kind,
    holder_agent, holder_harness, holder_instance_id, holder_task_id, holder_process_id,
    heartbeat_at, expires_at, ttl_seconds, version, last_event_id
)
SELECT stream_id, session_id, lease_id, generation, fencing_token, state, 'process',
       holder_agent, holder_harness, holder_instance_id, holder_task_id, holder_process_id,
       heartbeat_at, expires_at, ttl_seconds, version, last_event_id
FROM stream_leases_v2;

DROP TABLE stream_leases_v2;
DROP TABLE lease_events_v2;

CREATE INDEX lease_events_stream_order ON lease_events(stream_id, event_id DESC);

ALTER TABLE entries ADD COLUMN writer_holder_kind TEXT;
ALTER TABLE entries ADD COLUMN writer_receipt_digest TEXT;
UPDATE entries SET writer_holder_kind = CASE WHEN origin = 'live' THEN 'process' ELSE NULL END;

CREATE TRIGGER sessions_close_requires_released_lease
BEFORE UPDATE OF state ON sessions
WHEN NEW.state = 'closed' AND EXISTS (
    SELECT 1 FROM stream_leases AS lease
    WHERE lease.stream_id = NEW.stream_id AND lease.session_id = NEW.session_id AND lease.state != 'released'
)
BEGIN SELECT RAISE(ABORT, 'session close requires a released lease'); END;

CREATE TRIGGER leases_never_target_closed_session_insert
BEFORE INSERT ON stream_leases
WHEN NEW.state != 'released' AND EXISTS (
    SELECT 1 FROM sessions AS session WHERE session.session_id = NEW.session_id AND session.state = 'closed'
)
BEGIN SELECT RAISE(ABORT, 'closed session cannot hold a lease'); END;

CREATE TRIGGER leases_never_target_closed_session_update
BEFORE UPDATE ON stream_leases
WHEN NEW.state != 'released' AND EXISTS (
    SELECT 1 FROM sessions AS session WHERE session.session_id = NEW.session_id AND session.state = 'closed'
)
BEGIN SELECT RAISE(ABORT, 'closed session cannot hold or regain a lease'); END;

CREATE TRIGGER leases_projection_event_matches_insert
BEFORE INSERT ON stream_leases
WHEN NOT EXISTS (
    SELECT 1 FROM lease_events AS event WHERE event.event_id = NEW.last_event_id
      AND event.stream_id = NEW.stream_id AND event.session_id = NEW.session_id AND event.lease_id = NEW.lease_id
      AND event.generation = NEW.generation AND event.fencing_token = NEW.fencing_token
      AND event.holder_kind = NEW.holder_kind AND event.holder_agent = NEW.holder_agent
      AND event.holder_harness = NEW.holder_harness AND event.holder_instance_id = NEW.holder_instance_id
      AND event.holder_task_id IS NEW.holder_task_id AND event.holder_process_id IS NEW.holder_process_id
      AND event.ttl_seconds = NEW.ttl_seconds
)
BEGIN SELECT RAISE(ABORT, 'lease projection must match its lease event'); END;

CREATE TRIGGER leases_projection_event_matches_update
BEFORE UPDATE ON stream_leases
WHEN NOT EXISTS (
    SELECT 1 FROM lease_events AS event WHERE event.event_id = NEW.last_event_id
      AND event.stream_id = NEW.stream_id AND event.session_id = NEW.session_id AND event.lease_id = NEW.lease_id
      AND event.generation = NEW.generation AND event.fencing_token = NEW.fencing_token
      AND event.holder_kind = NEW.holder_kind AND event.holder_agent = NEW.holder_agent
      AND event.holder_harness = NEW.holder_harness AND event.holder_instance_id = NEW.holder_instance_id
      AND event.holder_task_id IS NEW.holder_task_id AND event.holder_process_id IS NEW.holder_process_id
      AND event.ttl_seconds = NEW.ttl_seconds
)
BEGIN SELECT RAISE(ABORT, 'lease projection must match its lease event'); END;

CREATE TRIGGER leases_projection_monotonic
BEFORE UPDATE ON stream_leases
WHEN NOT (
    NEW.version > OLD.version AND NEW.last_event_id > OLD.last_event_id
    AND NEW.fencing_token >= OLD.fencing_token AND NEW.generation >= OLD.generation
    AND ((NEW.session_id = OLD.session_id AND NEW.lease_id = OLD.lease_id
          AND NEW.holder_kind = OLD.holder_kind AND NEW.holder_agent = OLD.holder_agent
          AND NEW.holder_harness = OLD.holder_harness AND NEW.holder_instance_id = OLD.holder_instance_id
          AND NEW.holder_task_id IS OLD.holder_task_id AND NEW.holder_process_id IS OLD.holder_process_id)
         OR (NEW.fencing_token > OLD.fencing_token AND NEW.generation > OLD.generation))
)
BEGIN SELECT RAISE(ABORT, 'lease projection counters must advance monotonically'); END;

CREATE TRIGGER leases_no_delete BEFORE DELETE ON stream_leases
BEGIN SELECT RAISE(ABORT, 'lease projections are never deleted'); END;
CREATE TRIGGER lease_events_no_update BEFORE UPDATE ON lease_events
BEGIN SELECT RAISE(ABORT, 'lease events are append-only'); END;
CREATE TRIGGER lease_events_no_delete BEFORE DELETE ON lease_events
BEGIN SELECT RAISE(ABORT, 'lease events are never deleted'); END;
CREATE TRIGGER entries_no_update BEFORE UPDATE ON entries
BEGIN SELECT RAISE(ABORT, 'entries are append-only'); END;

CREATE TRIGGER entries_live_append_requires_current_lease
BEFORE INSERT ON entries
WHEN NEW.origin = 'live' AND NOT EXISTS (
    SELECT 1 FROM stream_leases AS lease JOIN sessions AS session
      ON session.session_id = lease.session_id AND session.stream_id = lease.stream_id
    WHERE lease.stream_id = NEW.stream_id AND lease.session_id = NEW.session_id
      AND lease.lease_id = NEW.writer_lease_id AND lease.fencing_token = NEW.fencing_token
      AND lease.holder_kind = NEW.writer_holder_kind AND lease.holder_agent = NEW.agent
      AND lease.holder_harness = NEW.harness AND lease.holder_instance_id = NEW.writer_instance_id
      AND lease.state = 'active' AND lease.expires_at > NEW.ts AND session.state IN ('open', 'rolling')
)
BEGIN SELECT RAISE(ABORT, 'live entry requires a valid current fenced lease'); END;
