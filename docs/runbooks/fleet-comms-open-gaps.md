# Fleet communication open gaps — runbook

Status board for the three residual fleet-comms problems after Sol phases 0–5.

## 1. Large ask replies — #5392

**Problem:** Big review/diff replies could land as a short SQLite body with no
marker that transport clipped them.

**Fix (code):** `scripts/ai_agent_bridge/_reply_sidecar.py` + `send_message`.

- Responses over `AB_REPLY_INLINE_MAX_BYTES` (default **12 KiB**), or that match
  mid-deliverable tail heuristics, write the **full** body to
  `batch_state/asks/<task-id>/reply-<agent>-<sha16>.md` (gitignored).
- The messages-table body becomes a head excerpt + explicit footer:

  ```
  TRUNCATED: full reply offloaded to sidecar …
  path: …
  sha256: …
  bytes: …
  ```

- Metadata JSON also carries `reply_sidecar: {path, sha256, bytes, truncated}`.

**Operator:** when you see `TRUNCATED`, open the path — do not re-run the model
just because the inline body looks short.

## 2. Session-stream dual-write (not full cutover)

**Shipped:** SQLite streams + phase-one CLI; live streams include
`epic:4387` (atlas), `epic:4707` (infra), `epic:4542`, `epic:4706`.

**This PR:** dual-write inventory without retiring files:

```bash
.venv/bin/python -m agents_extensions.shared.session_streams dual-write-status
.venv/bin/python -m agents_extensions.shared.session_streams inventory --register
# DB-first projection receipts + drift detection (no file rewrite / no cutover):
.venv/bin/python -m agents_extensions.shared.session_streams project
.venv/bin/python -m agents_extensions.shared.session_streams check-drift
# under an active lease (SESSION_STREAM_* env):
.venv/bin/python -m agents_extensions.shared.session_streams mirror-handoff \
  --stream epic:4387
```

Registry: manifest inventory from `scripts/config/issue_streams.yaml` via
`agents_extensions/shared/session_streams/inventory.py` (Sol PR-H; not a hard-coded
epic subset). Projection receipts land in `legacy_projection_receipts` after
inventory; unrecorded file mutation is flagged as `drift` without flipping modes.

**Still blocked for cutover:** operator gate after per-harness acceptance;
file handoffs remain authoritative until then.

## 3. Hygiene residuals

| Issue | Fix |
| --- | --- |
| **#5113** dead `gemini` inbox nags | Backlog warnings skip `dead_lane_agents()`; expire via `ab cleanup --expire` (already bulk-expires dead lanes). |
| **#4915** empty body on background process | `assert_ask_content_present` on process paths — empty DB body fails as **transport**, not model stall. |
| **#4956** disk retention | Read-only scanner: `.venv/bin/python scripts/hygiene/lane_disk_retention.py [--include-home] [--json]` |

## Closeout checklist

- [ ] #5392 — green tests for sidecar + TRUNCATED footer
- [ ] dual-write-status returns registered streams
- [ ] backlog warning does not mention `gemini` when it is a dead lane
- [ ] empty-body process-ask records `transport empty-ask-body`
