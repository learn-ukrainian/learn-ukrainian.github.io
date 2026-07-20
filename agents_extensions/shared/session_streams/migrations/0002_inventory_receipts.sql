-- Sol PR-H / #5512: inventory + import/projection receipt structures.
-- Migration modes progress inventory → shadow → dual_write → db_primary → legacy_retired.
-- This migration does NOT flip cutover defaults; registration starts at inventory.

CREATE TABLE stream_migration_state (
    stream_id TEXT PRIMARY KEY REFERENCES streams(stream_id),
    mode TEXT NOT NULL CHECK (mode IN (
        'inventory', 'shadow', 'dual_write', 'db_primary', 'legacy_retired'
    )),
    stream_name TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    inventoried_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    inventory_source TEXT NOT NULL DEFAULT 'scripts/config/issue_streams.yaml',
    version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0)
) STRICT;

CREATE TABLE stream_inventory_receipts (
    receipt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stream_id TEXT NOT NULL REFERENCES streams(stream_id),
    stream_name TEXT NOT NULL,
    epic_number INTEGER NOT NULL CHECK (epic_number > 0),
    title TEXT NOT NULL DEFAULT '',
    source_path TEXT NOT NULL,
    source_sha256 TEXT NOT NULL CHECK (length(source_sha256) = 64),
    handoff_candidates_json TEXT NOT NULL CHECK (json_valid(handoff_candidates_json)),
    recorded_at TEXT NOT NULL,
    UNIQUE (stream_id, source_sha256)
) STRICT;

CREATE INDEX stream_inventory_receipts_stream_order
    ON stream_inventory_receipts(stream_id, receipt_id DESC);

-- File presence / content inventory without requiring a session entry yet.
CREATE TABLE legacy_import_receipts (
    import_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stream_id TEXT NOT NULL REFERENCES streams(stream_id),
    source_path TEXT NOT NULL,
    source_sha256 TEXT NOT NULL CHECK (length(source_sha256) = 64 OR source_sha256 = ''),
    source_bytes INTEGER NOT NULL CHECK (source_bytes >= 0),
    status TEXT NOT NULL CHECK (status IN (
        'missing', 'inventoried', 'imported', 'review_required'
    )),
    recorded_at TEXT NOT NULL,
    entry_id INTEGER REFERENCES entries(entry_id),
    UNIQUE (stream_id, source_path, source_sha256, status)
) STRICT;

CREATE INDEX legacy_import_receipts_stream_order
    ON legacy_import_receipts(stream_id, import_id DESC);

-- DB → legacy file projection receipts (append-only; failure is visible drift).
CREATE TABLE legacy_projection_receipts (
    projection_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stream_id TEXT NOT NULL REFERENCES streams(stream_id),
    target_path TEXT NOT NULL,
    target_sha256 TEXT NOT NULL CHECK (length(target_sha256) = 64 OR target_sha256 = ''),
    high_water_entry_id INTEGER,
    projection_hash TEXT NOT NULL CHECK (length(projection_hash) = 64),
    status TEXT NOT NULL CHECK (status IN ('ok', 'failed', 'drift')),
    recorded_at TEXT NOT NULL,
    error TEXT NOT NULL DEFAULT '',
    UNIQUE (stream_id, target_path, projection_hash, status)
) STRICT;

CREATE INDEX legacy_projection_receipts_stream_order
    ON legacy_projection_receipts(stream_id, projection_id DESC);

CREATE TABLE stream_control_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stream_id TEXT NOT NULL REFERENCES streams(stream_id),
    event_type TEXT NOT NULL CHECK (event_type IN (
        'inventory_registered',
        'mode_transition',
        'cutover_proposed',
        'cutover_applied',
        'cutover_refused',
        'drift_detected',
        'drift_cleared'
    )),
    from_mode TEXT,
    to_mode TEXT,
    proof_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(proof_json)),
    recorded_at TEXT NOT NULL,
    agent TEXT NOT NULL DEFAULT 'system',
    reason TEXT NOT NULL DEFAULT ''
) STRICT;

CREATE INDEX stream_control_events_stream_order
    ON stream_control_events(stream_id, event_id DESC);

CREATE TRIGGER stream_inventory_receipts_no_update
BEFORE UPDATE ON stream_inventory_receipts
BEGIN
    SELECT RAISE(ABORT, 'stream inventory receipts are append-only');
END;

CREATE TRIGGER stream_inventory_receipts_no_delete
BEFORE DELETE ON stream_inventory_receipts
BEGIN
    SELECT RAISE(ABORT, 'stream inventory receipts are never deleted');
END;

CREATE TRIGGER legacy_import_receipts_no_update
BEFORE UPDATE ON legacy_import_receipts
BEGIN
    SELECT RAISE(ABORT, 'legacy import receipts are append-only');
END;

CREATE TRIGGER legacy_import_receipts_no_delete
BEFORE DELETE ON legacy_import_receipts
BEGIN
    SELECT RAISE(ABORT, 'legacy import receipts are never deleted');
END;

CREATE TRIGGER legacy_projection_receipts_no_update
BEFORE UPDATE ON legacy_projection_receipts
BEGIN
    SELECT RAISE(ABORT, 'legacy projection receipts are append-only');
END;

CREATE TRIGGER legacy_projection_receipts_no_delete
BEFORE DELETE ON legacy_projection_receipts
BEGIN
    SELECT RAISE(ABORT, 'legacy projection receipts are never deleted');
END;

CREATE TRIGGER stream_control_events_no_update
BEFORE UPDATE ON stream_control_events
BEGIN
    SELECT RAISE(ABORT, 'stream control events are append-only');
END;

CREATE TRIGGER stream_control_events_no_delete
BEFORE DELETE ON stream_control_events
BEGIN
    SELECT RAISE(ABORT, 'stream control events are never deleted');
END;
