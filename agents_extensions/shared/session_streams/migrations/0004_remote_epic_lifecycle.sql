-- Remote epic lifecycle identity and TTL-expiry projection.
--
-- Existing local sessions keep the same open/rolling/closed state machine.  A
-- session that is replaced by a remote TTL claim is closed transactionally and
-- receives expired_at; the store exposes that terminal row as SessionState.EXPIRED
-- without weakening the original SQL close trigger or inventing a second lease
-- table.

ALTER TABLE sessions ADD COLUMN expired_at TEXT;
ALTER TABLE lease_events ADD COLUMN holder_host_id TEXT;
ALTER TABLE stream_leases ADD COLUMN holder_host_id TEXT;

DROP TRIGGER leases_projection_event_matches_insert;
DROP TRIGGER leases_projection_event_matches_update;
DROP TRIGGER leases_projection_monotonic;

CREATE TRIGGER leases_projection_event_matches_insert
BEFORE INSERT ON stream_leases
WHEN NOT EXISTS (
    SELECT 1 FROM lease_events AS event WHERE event.event_id = NEW.last_event_id
      AND event.stream_id = NEW.stream_id AND event.session_id = NEW.session_id AND event.lease_id = NEW.lease_id
      AND event.generation = NEW.generation AND event.fencing_token = NEW.fencing_token
      AND event.holder_kind = NEW.holder_kind AND event.holder_agent = NEW.holder_agent
      AND event.holder_harness = NEW.holder_harness AND event.holder_instance_id = NEW.holder_instance_id
      AND event.holder_task_id IS NEW.holder_task_id AND event.holder_process_id IS NEW.holder_process_id
      AND event.holder_host_id IS NEW.holder_host_id
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
      AND event.holder_host_id IS NEW.holder_host_id
      AND event.ttl_seconds = NEW.ttl_seconds
)
BEGIN SELECT RAISE(ABORT, 'lease projection must match its lease event'); END;

CREATE TRIGGER leases_projection_monotonic
BEFORE UPDATE ON stream_leases
WHEN NOT (
    NEW.version > OLD.version AND NEW.last_event_id > OLD.last_event_id
    AND NEW.fencing_token >= OLD.fencing_token AND NEW.generation >= OLD.generation
    AND (
        (NEW.session_id = OLD.session_id AND NEW.lease_id = OLD.lease_id
         AND NEW.holder_kind = OLD.holder_kind AND NEW.holder_agent = OLD.holder_agent
         AND NEW.holder_harness = OLD.holder_harness AND NEW.holder_instance_id = OLD.holder_instance_id
         AND NEW.holder_task_id IS OLD.holder_task_id AND NEW.holder_process_id IS OLD.holder_process_id
         AND NEW.holder_host_id IS OLD.holder_host_id)
        OR
        (NEW.fencing_token > OLD.fencing_token AND NEW.generation > OLD.generation)
    )
)
BEGIN SELECT RAISE(ABORT, 'lease projection counters must advance monotonically'); END;
