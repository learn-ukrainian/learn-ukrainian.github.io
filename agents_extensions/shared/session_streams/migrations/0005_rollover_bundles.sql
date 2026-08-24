-- Cross-host strict rollover continuity bundles.  Rows are immutable while
-- retained; the store removes only rows beyond the per-lineage five-row cap.
CREATE TABLE rollover_bundles (
    bundle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stream_id TEXT NOT NULL REFERENCES streams(stream_id),
    agent TEXT NOT NULL,
    lineage_id TEXT NOT NULL,
    generation INTEGER NOT NULL CHECK (generation > 0),
    rollover_id TEXT NOT NULL,
    bundle_sha256 TEXT NOT NULL CHECK (length(bundle_sha256) = 64) UNIQUE,
    manifest_json TEXT NOT NULL CHECK (json_valid(manifest_json)),
    blob BLOB NOT NULL CHECK (length(blob) > 0),
    uploaded_at TEXT NOT NULL,
    uploaded_by_lease_id TEXT NOT NULL REFERENCES stream_leases(lease_id),
    UNIQUE (stream_id, agent, lineage_id, rollover_id)
) STRICT;

CREATE INDEX rollover_bundles_lineage_order
    ON rollover_bundles(stream_id, agent, lineage_id, bundle_id DESC);

CREATE INDEX rollover_bundles_stream_order
    ON rollover_bundles(stream_id, bundle_id DESC);
