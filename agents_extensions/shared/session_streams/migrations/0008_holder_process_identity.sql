-- Kernel-derived holder process identity (#10657).
--
-- holder_process_identity is the session supervisor's fingerprint of the
-- long-lived holder process, fixed when a generation is acquired. It is
-- optional: leases acquired before this migration, or by an older client, keep
-- NULL and renew and release exactly as before; only owner attestation and lane
-- succession, which require the proof, refuse them. Heartbeats copy the stored
-- value and never populate it.

ALTER TABLE lease_events ADD COLUMN holder_process_identity TEXT
    CHECK (holder_process_identity IS NULL OR (
        holder_kind = 'process'
        AND length(holder_process_identity) = 67
        AND substr(holder_process_identity, 1, 3) = 'v1:'
        AND substr(holder_process_identity, 4) NOT GLOB '*[^0-9a-f]*'
    ));
ALTER TABLE stream_leases ADD COLUMN holder_process_identity TEXT
    CHECK (holder_process_identity IS NULL OR (
        holder_kind = 'process'
        AND length(holder_process_identity) = 67
        AND substr(holder_process_identity, 1, 3) = 'v1:'
        AND substr(holder_process_identity, 4) NOT GLOB '*[^0-9a-f]*'
    ));

DROP TRIGGER leases_projection_event_matches_insert;
DROP TRIGGER leases_projection_event_matches_update;
DROP TRIGGER leases_projection_monotonic;

-- The projection's identity must be the one its own lease event carries, so a
-- writer that omits the column cannot carry a predecessor's identity into a new
-- generation.
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
      AND event.holder_process_identity IS NEW.holder_process_identity
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
      AND event.holder_process_identity IS NEW.holder_process_identity
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
         AND NEW.holder_host_id IS OLD.holder_host_id
         AND NEW.holder_process_identity IS OLD.holder_process_identity)
        OR
        (NEW.fencing_token > OLD.fencing_token AND NEW.generation > OLD.generation)
    )
)
BEGIN SELECT RAISE(ABORT, 'lease projection counters must advance monotonically'); END;

-- Renewal, transition, release and append keep the generation and so keep the
-- identity; only a new generation (a new holder acquisition) may set another.
CREATE TRIGGER leases_process_identity_immutable
BEFORE UPDATE ON stream_leases
WHEN NEW.generation = OLD.generation
     AND NEW.holder_process_identity IS NOT OLD.holder_process_identity
BEGIN SELECT RAISE(ABORT, 'holder process identity is immutable within a lease generation'); END;

-- A stream has one projection row, replaced only through the guarded UPDATE
-- path. INSERT OR REPLACE would delete and re-insert it without firing any
-- update or delete trigger.
CREATE TRIGGER leases_single_projection_insert
BEFORE INSERT ON stream_leases
WHEN EXISTS (SELECT 1 FROM stream_leases AS lease WHERE lease.stream_id = NEW.stream_id)
BEGIN SELECT RAISE(ABORT, 'lease projections are replaced only by a guarded update'); END;
