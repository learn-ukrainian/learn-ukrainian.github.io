# Session streams Monitor API (Sol PR-K)

Read-only Monitor surfaces for epic session streams. **No silent cutover.**

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/session-streams/v1/health` | DB presence / repo root |
| GET | `/api/session-streams/v1/status/{stream_id}` | Lease/handoff diagnosis (`epic:N`) |
| GET | `/api/session-streams/v1/digest/{stream_id}?limit=20` | Pinned + recent entries |
| GET | `/api/session-streams/v1/dual-write-status` | Handoff file inventory existence |
| GET | `/api/session-streams/v1/drift?dry_run=true` | Projection receipts snapshot (default) |
| GET | `/api/session-streams/v1/plane-continuity` | Bundle board (streams + dual-write + plane pointer) |

Message plane status remains `/api/comms/v1/plane-status` (default off).

Parent: #5512 · stream #4707.
