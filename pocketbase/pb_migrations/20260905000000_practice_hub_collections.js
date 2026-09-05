/// <reference path="../pb_data/types.d.ts" />
/**
 * Practice Hub §10.3 collections (GH #4384/#4920).
 *
 * - users        PocketBase-native auth collection + the account-level
 *                `fsrsParamsVersion` pin (§10.1 ⟦codex v4⟧: devices never fold
 *                the same log under different parameters). Ordinary clients
 *                cannot PATCH the pin (`updateRule` + hook); superusers still
 *                manage via admin.
 * - review_events  the §10.1 append-only event log. Unique `eventId`
 *                (idempotent push), per-user monotonic `serverSeq` (the pull
 *                cursor), `serverReceivedAt` + clamped `reviewedAt` stamped by
 *                pb_hooks/review_events.pb.js. updateRule/deleteRule are null
 *                (append-only); user deletion hard-deletes events via
 *                `cascadeDelete` (§10.3: DB-layer cascade, not API rules).
 *                Ingest also rejects mixed-version appends against existing
 *                history so the log stays uniform for replay.
 * - snapshots    `(user, schemaVersion, blob, updatedAt)` — optional
 *                fast-restore cache, never authority.
 *
 * Compatible with PocketBase v0.23+ (pinned in README.md).
 */
migrate((app) => {
  const users = app.findCollectionByNameOrId("users");
  users.fields.add(new Field({
    name: "fsrsParamsVersion",
    type: "number",
    required: true,
    min: 1,
    noDecimal: true,
  }));
  // Account pin is authority for replay (§10.1): ordinary clients may create
  // with an initial value but must not PATCH it later. Superusers still manage
  // via the admin UI (API rules do not apply to them). `:changed` is v0.23+.
  const selfUpdate = users.updateRule || "id = @request.auth.id";
  users.updateRule =
    "(" + selfUpdate + ") && (@request.body.fsrsParamsVersion:changed = false)";
  app.save(users);

  const reviewEvents = new Collection({
    name: "review_events",
    type: "base",
    listRule: "user = @request.auth.id",
    viewRule: "user = @request.auth.id",
    createRule: '@request.auth.id != ""',
    updateRule: null,
    deleteRule: null,
    fields: [
      {
        name: "eventId",
        type: "text",
        required: true,
        min: 26,
        max: 26,
        pattern: "^[0-9A-HJKMNP-TV-Z]{26}$",
      },
      {
        name: "user",
        type: "relation",
        required: true,
        collectionId: users.id,
        maxSelect: 1,
        cascadeDelete: true,
      },
      { name: "lemmaId", type: "text", required: true, max: 200 },
      { name: "mode", type: "text", required: true, max: 50 },
      {
        name: "rating",
        type: "select",
        required: true,
        maxSelect: 1,
        values: ["again", "hard", "good", "easy"],
      },
      { name: "reviewedAt", type: "number", required: true, noDecimal: true },
      { name: "deckVersion", type: "number", required: true, min: 0, noDecimal: true },
      { name: "clientId", type: "text", required: true, max: 100 },
      { name: "fsrsParamsVersion", type: "number", required: true, min: 1, noDecimal: true },
      { name: "presentation", type: "json", required: false, maxSize: 4096 },
      { name: "serverSeq", type: "number", required: true, min: 1, noDecimal: true },
      { name: "serverReceivedAt", type: "number", required: true, noDecimal: true },
    ],
    indexes: [
      "CREATE UNIQUE INDEX idx_review_events_event_id ON review_events (eventId)",
      "CREATE UNIQUE INDEX idx_review_events_user_server_seq ON review_events (user, serverSeq)",
      "CREATE INDEX idx_review_events_user_reviewed_at ON review_events (user, reviewedAt)",
    ],
  });
  app.save(reviewEvents);

  const snapshots = new Collection({
    name: "snapshots",
    type: "base",
    listRule: "user = @request.auth.id",
    viewRule: "user = @request.auth.id",
    createRule: "user = @request.auth.id",
    updateRule: "user = @request.auth.id",
    deleteRule: "user = @request.auth.id",
    fields: [
      {
        name: "user",
        type: "relation",
        required: true,
        collectionId: users.id,
        maxSelect: 1,
        cascadeDelete: true,
      },
      { name: "schemaVersion", type: "number", required: true, min: 1, noDecimal: true },
      { name: "blob", type: "json", required: true, maxSize: 5242880 },
      { name: "updatedAt", type: "autodate", onCreate: true, onUpdate: true },
    ],
    indexes: [
      "CREATE UNIQUE INDEX idx_snapshots_user_schema_version ON snapshots (user, schemaVersion)",
    ],
  });
  app.save(snapshots);
}, (app) => {
  for (const name of ["snapshots", "review_events"]) {
    const collection = app.findCollectionByNameOrId(name);
    app.delete(collection);
  }
  const users = app.findCollectionByNameOrId("users");
  const field = users.fields.getByName("fsrsParamsVersion");
  if (field) {
    users.fields.removeById(field.id);
    app.save(users);
  }
});
