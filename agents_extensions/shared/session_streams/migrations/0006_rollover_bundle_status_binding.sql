-- Permit one immutable row for each status/prepared-time tuple while keeping
-- the bundle digest globally unique.  Migration 0005 is already fingerprinted
-- by schema_migrations, so rebuild rather than editing that applied DDL.
DROP INDEX IF EXISTS rollover_bundles_lineage_order;
DROP INDEX IF EXISTS rollover_bundles_stream_order;

ALTER TABLE rollover_bundles RENAME TO rollover_bundles_v5;

CREATE TABLE rollover_bundles (
    bundle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stream_id TEXT NOT NULL REFERENCES streams(stream_id),
    agent TEXT NOT NULL,
    lineage_id TEXT NOT NULL,
    generation INTEGER NOT NULL CHECK (generation > 0),
    rollover_id TEXT NOT NULL,
    status TEXT NOT NULL,
    prepared_at TEXT NOT NULL,
    bundle_sha256 TEXT NOT NULL CHECK (length(bundle_sha256) = 64),
    manifest_json TEXT NOT NULL CHECK (json_valid(manifest_json)),
    blob BLOB NOT NULL CHECK (length(blob) > 0),
    uploaded_at TEXT NOT NULL,
    uploaded_by_lease_id TEXT NOT NULL REFERENCES stream_leases(lease_id)
) STRICT;

INSERT INTO rollover_bundles(
    bundle_id, stream_id, agent, lineage_id, generation, rollover_id,
    status, prepared_at, bundle_sha256, manifest_json, blob, uploaded_at,
    uploaded_by_lease_id
)
SELECT
    bundle_id, stream_id, agent, lineage_id, generation, rollover_id,
    json_extract(manifest_json, '$.status'),
    json_extract(manifest_json, '$.prepared_at'),
    bundle_sha256, manifest_json, blob, uploaded_at, uploaded_by_lease_id
FROM rollover_bundles_v5;

DROP TABLE rollover_bundles_v5;

CREATE UNIQUE INDEX rollover_bundles_bundle_sha256_unique
    ON rollover_bundles(bundle_sha256);

CREATE UNIQUE INDEX rollover_bundles_identity_unique
    ON rollover_bundles(
        stream_id, agent, lineage_id, rollover_id, status, prepared_at
    );

CREATE INDEX rollover_bundles_lineage_order
    ON rollover_bundles(stream_id, agent, lineage_id, bundle_id DESC);

CREATE INDEX rollover_bundles_stream_order
    ON rollover_bundles(stream_id, bundle_id DESC);
