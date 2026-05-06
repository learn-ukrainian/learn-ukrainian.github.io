# API Stability Audit - 2026-05-06

Scope: all `playgrounds/*.html` dashboards. Measurements used 5 `curl` samples
unless noted. Patched-code measurements used the worktree API on `127.0.0.1:8877`.
Broker-backed comms measurements used the live local API on `127.0.0.1:8765`,
because this worktree has an empty broker DB.

## Ranked Stressors

| Rank | Endpoint | Dashboard(s) | Before | After | Fix |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | `/api/wiki/status` | `index.html`, `wiki.html` | timed out at 20 s on live single worker | p99 0.56-0.68 s cold, median <1 ms cached | Reused article index, stopped per-slug source gathering, added TTL cache |
| 2 | `/api/dashboard/overview` | `index.html`, `audit-dashboard.html`, `curriculum-dashboard.html` | p99 7.9-8.6 s cold | p99 0.30 s cold, median 0.035 s | Switched overview to lightweight summary scan |
| 3 | `/api/comms/batch-progress` | `index.html`, `comms.html` | median 0.47-0.51 s every poll | p99 0.045 s in patched code | Bounded log reads to 256 KiB tail, added 10 s TTL cache |
| 4 | `/api/state/weak-points?limit=1` | `index.html` | p99 7.5-8.3 s cold | p99 0.098 s cold, median <1 ms cached | Avoided 1,776 plan YAML reads when `word_count == 0`, added TTL cache |
| 5 | `/api/rag/search_text` | `image-explorer.html` | can stall single worker when Qdrant is down | fast 503 after socket probe | Added 250 ms Qdrant port check |

## Server Findings

- Middleware-level request concurrency limits: none found.
- Uvicorn process model: `package.json` runs one default uvicorn worker. No
  `--workers` or `--limit-concurrency` is configured.
- Single-worker impact: reproduced. A wedged dashboard request caused `/api/health`
  to time out until that request returned.
- Live server process during audit: PID 54081, RSS about 54 MiB, open FDs about 78.
- Existing broker indexes: channel tables were indexed, legacy `messages` was not.
  Added idempotent `messages` indexes and applied them to the live local DB.

## Endpoint Matrix

`Pagination` means the endpoint has a caller-visible `limit`, `tail`, `page`, or
equivalent bounded response control. `SQL/plan` is abbreviated to the dominant
backend path.

| Dashboard | Polling | Endpoint | Median / p99 latency | Median / p99 bytes | SQL / plan | Pagination |
| --- | --- | --- | ---: | ---: | --- | --- |
| `index.html` | none | `/api/dashboard/overview` | 0.035 / 0.301 s | 7,857 / 7,857 | filesystem status summary | no, cached |
| `index.html` | none | `/api/state/pipeline-versions` | 0.0008 / 0.099 s | 1,253 / 1,253 | filesystem, cached | no |
| `index.html` | none | `/api/consultation/metrics` | 0.0008 / 0.005 s | 349 / 349 | filesystem | no |
| `index.html` | none | `/api/state/summary` | 0.0008 / 0.194 s | 4,128 / 4,128 | filesystem, cached | no |
| `index.html` | none | `/api/comms/batch-progress` | 0.0007 / 0.044 s | 85 / 85 | bounded log tail + `ps` | bounded tail |
| `index.html` | none | `/api/state/weak-points?limit=1` | 0.0007 / 0.098 s | 24 / 24 | filesystem audit/research scan | yes |
| `index.html` | none | `/api/orient` | 0.0017 / 0.623 s | 10,693 / 10,701 | mixed cached collectors | no |
| `index.html` | none | `/api/runtime/agents` | 0.0020 / 0.002 s | 583 / 583 | filesystem | no |
| `index.html` | none | `/api/delegate/tasks?limit=100` | 0.0008 / 0.001 s | 22 / 22 | filesystem | yes |
| `index.html` | none | `/api/build/events/active` | 0.0028 / 0.004 s | 13 / 13 | JSONL tail | bounded |
| `index.html` | none | `/api/wiki/status` | 0.0008 / 0.559 s | 1,696 / 1,696 | filesystem + progress cache | no, cached |
| `index.html` | none | `/api/analytics/cost` | 0.0042 / 0.005 s | 11,509 / 11,509 | dispatch meta glob | no |
| `channels.html` | 5 s | `/api/comms/channels` | 0.0013 / 0.001 s live | 2,098 / 2,098 | `channel_messages` covering index | no |
| `channels.html` | active channel load | `/api/comms/channels/{name}` | 0.001 s class | varies | indexed `channels.name`, channel count | no |
| `channels.html` | active channel load | `/api/comms/channels/{name}/messages?tail=50` | 0.0012 / 0.001 s live for missing `general` | 39 / 39 | `idx_channel_messages_channel_time` | yes |
| `channels.html` | active channel load | `/api/comms/channels/{name}/deliveries?status=pending&limit=20` | 0.001 s class | varies | `idx_channel_messages_channel_time` + `idx_deliveries_message` | yes |
| `channels.html` | user action | `POST /api/comms/channels/{name}/post` | not benchmarked | n/a | indexed insert fanout | n/a |
| `comms.html` | 15 s | `/api/comms/messages?limit=1&offset=0` | 0.003 s live | small | rowid scan in descending id order | yes |
| `comms.html` | 15 s | `/api/comms/messages?limit=50` | 0.0029 / 0.031 s live | 23,910 / 23,910 | rowid scan, indexed filters if present | yes |
| `comms.html` | 15 s | `/api/comms/live-activity?minutes=30` | 0.0032 / 0.0047 s live | 9,716 / 9,716 | filesystem recent-state scan + message tail | bounded |
| `comms.html` | 15 s | `/api/comms/batch-progress` | 0.51 s live before patch | 5,460 / 5,460 | unbounded logs before patch | bounded tail after patch |
| `comms.html` | 15 s | `/api/comms/zombies` | 0.005 / 0.009 s live | 280 / 280 | `idx_messages_acknowledged`, `message_type` | no, indexed |
| `comms.html` | 15 s | `/api/comms/stats` | 0.0035 / 0.0036 s live | 233 / 233 | `messages` aggregate counts | no, indexed |
| `comms.html` | 15 s | `/api/comms/health` | 0.0007 / 0.001 s | 113 / 113 | `idx_messages_acknowledged` | no |
| `comms.html` | user action | `POST /api/comms/send` | not benchmarked | n/a | legacy message insert | n/a |
| `comms.html` | user action | `POST /api/comms/acknowledge/{id}` | not benchmarked | n/a | primary-key update | n/a |
| `admin.html` | health every 30 s | `/api/admin/health` | 0.0117 / 0.0145 s | 321 / 321 | filesystem + broker probe | no |
| `admin.html` | on demand | `/api/admin/disk-usage` | 0.0019 / 0.0044 s | 1,545 / 1,545 | filesystem | no |
| `admin.html` | on demand | `/api/admin/backup/list` | 0.0006 / 0.0009 s | 154 / 154 | filesystem | no |
| `admin.html` | on demand | `/api/admin/maintenance/embedding-cache-stats` | 0.0006 / 0.0009 s | 54 / 54 | filesystem | no |
| `admin.html` | on demand | `/api/admin/maintenance/annotation-stats` | 0.0005 / 0.0010 s | 47 / 47 | filesystem | no |
| `admin.html` | on demand | `/api/admin/collections` | 0.0014 / 0.0018 s, 503 when Qdrant absent | 63 / 63 | Qdrant probe | no |
| `admin.html` | user action | backup, vacuum, clean logs, verify collections | not benchmarked | n/a | mutating operations | n/a |
| `audit-dashboard.html` | none | `/api/dashboard/overview` and dashboard detail endpoints | see overview / track rows | see rows | filesystem summary/detail | no |
| `build-events.html` | 10 s | `/api/build/events/active` | 0.0028 / 0.004 s | 13 / 13 | build event JSONL | bounded |
| `build-events.html` | 10 s | `/api/build/events/recent?limit=50&offset=0` | 0.0029 / 0.0036 s | 6,526 / 6,526 | build event JSONL | yes |
| `consultation.html` | none | `/api/config` | not rebenchmarked; health smoke passed | small | static config | no |
| `consultation.html` | on demand | `/api/consultation/metrics` | 0.0008 / 0.005 s | 349 / 349 | filesystem | no |
| `cost.html` | none | `/api/analytics/cost` | 0.0042 / 0.005 s | 11,509 / 11,509 | dispatch meta glob | no |
| `cost.html` | search | `/api/analytics/cost?track={track}` | same class | varies | filtered dispatch meta glob | no |
| `cost.html` | search | `/api/analytics/cost/module/{level}/{slug}` | same class | varies | scoped dispatch meta glob | no |
| `cost.html` | search | `/api/analytics/cost/phase/{name}` | same class | varies | filtered dispatch meta glob | no |
| `curriculum-dashboard.html` | 30 s | `/api/dashboard/overview` | 0.035 / 0.301 s | 7,857 / 7,857 | lightweight filesystem summary | no, cached |
| `delegate.html` | none | `/api/delegate/tasks?limit=100` | 0.0008 / 0.001 s | 22 / 22 | filesystem task dirs | yes |
| `delegate.html` | detail click | `/api/delegate/tasks/{task_id}` | not benchmarked | n/a | filesystem detail | n/a |
| `image-explorer.html` | none | `/api/rag/search_text?q=test&limit=5` | fast 503 after patch when Qdrant down | 503 body | Qdrant socket probe + query | yes |
| `image-explorer.html` | none | `/api/rag/search_images`, `/api/rag/search_literary` | same class | varies | Qdrant socket probe + query | yes |
| `images.html` | none | `/api/images/textbooks` | direct function 0.135 s cold | large catalog | PDF catalog scan | no, cached singleton |
| `images.html` | none | `/api/images/annotations` | same index class | varies | JSONL index + pagination | yes |
| `images.html` | none | `/api/images/stats` | same index class | small | JSONL index aggregate | no, cached singleton |
| `orient.html` | 30 s | `/api/orient` | 0.0017 / 0.623 s | 10,693 / 10,701 | mixed collectors, per-section TTLs | no |
| `progress.html` | none | `/api/state/pipeline/{track}` | not in broad matrix | varies | filesystem pipeline state | no, cached |
| `progress.html` | none | `/api/state/summary` | 0.0008 / 0.194 s | 4,128 / 4,128 | filesystem summary | no, cached |
| `progress.html` | none | `/api/state/pipeline-versions` | 0.0008 / 0.099 s | 1,253 / 1,253 | filesystem | no, cached |
| `quality.html` | none | `/api/state/research-coverage` | health smoke passed | varies | filesystem research scan | no, cached |
| `quality.html` | none | `/api/state/review-coverage` | health smoke passed | varies | filesystem review scan | no, cached |
| `quality.html` | none | `/api/state/issues` | health smoke passed | varies | filesystem review/audit scan | no |
| `quality.html` | none | `/api/state/weak-points?limit=500` | patched class | varies | filesystem audit/research scan | yes, cached |
| `runtime.html` | 30 s | `/api/runtime/agents` | 0.0020 / 0.002 s | 583 / 583 | filesystem/process state | no |
| `runtime.html` | 30 s | `/api/runtime/usage?days=7` | health smoke passed | varies | runtime logs | bounded by days |
| `runtime.html` | 30 s | `/api/runtime/headroom?...` | per-agent fanout | varies | runtime config | no |
| `runtime.html` | 30 s | `/api/runtime/recent?limit=50` | health smoke passed | varies | runtime logs | yes |
| `track-health.html` | 30 s | `/api/state/build-status` | health smoke passed | varies | filesystem build status | no, cached |
| `track-health.html` | 30 s | `/api/state/enrichment-status` | health smoke passed | varies | filesystem plan scan | no, cached |
| `track-health.html` | 30 s | `/api/state/track-health/a1` | health smoke passed | varies | filesystem track scan | no, cached |
| `track-health.html` | track click | `/api/state/module/a1/1` | health smoke passed | varies | filesystem module detail + comms preview | no |
| `track-health.html` | track click | `/api/comms/by-module/a1/hello` | worktree DB empty; live class indexed poorly for leading wildcard | varies | `LIKE '%slug%'` scan | yes limit, cannot index leading wildcard |
| `wiki.html` | 60 s | `/api/wiki/status` | 0.0008 / 0.559 s | 1,696 / 1,696 | filesystem + progress cache | no, cached |
| `wiki.html` | 60 s | `/api/wiki/status/a1` | 0.0011 / 0.305 s | 5,369 / 5,369 | filesystem + progress cache | no, cached |
| `wiki.html` | 60 s | `/api/wiki/quality-gate/a1` | health smoke passed | varies | filesystem markdown scan | no |
| `wiki.html` | 60 s | `/api/wiki/build-log?limit=50` | health smoke passed | varies | log tail | yes |

## SQL Query Plans

Plans were run against the live broker DB after applying the new indexes.

```text
/api/comms/messages?limit=50
SCAN messages

/api/comms/zombies stale messages
SEARCH messages USING INDEX idx_messages_acknowledged (acknowledged=?)

/api/comms/by-module/{track}/{slug}
SCAN messages
Reason: task_id LIKE '%slug%' has a leading wildcard and cannot use the task index.

/api/comms/channels
SCAN channel_messages USING COVERING INDEX idx_channel_messages_channel_time

/api/comms/channels/{name}/messages?tail=50
SEARCH channel_messages USING INDEX idx_channel_messages_channel_time (channel=?)

/api/comms/channels/{name}/deliveries?status=pending&limit=20
SEARCH cm USING INDEX idx_channel_messages_channel_time (channel=?)
SEARCH d USING INDEX idx_deliveries_message (message_id=?)
```

## Fixes Applied

- `scripts/api/wiki_router.py`: cached aggregate and per-track status, reused a
  single article candidate index per request, and used progress metadata for
  `source_count` instead of gathering discovery sources for every slug.
- `scripts/api/dashboard_router.py` and `scripts/api/dashboard_helpers.py`:
  overview now uses lightweight summaries instead of full research scoring.
- `scripts/api/comms_router.py`: `/api/comms/batch-progress` reads only the last
  256 KiB of each current log and caches for 10 seconds.
- `scripts/api/state_router.py`: `/api/state/weak-points` avoids plan YAML reads
  when no word count exists and caches by query parameters for 60 seconds.
- `scripts/api/rag_router.py`: Qdrant-backed search endpoints fail fast when the
  local Qdrant port is closed.
- `scripts/ai_agent_bridge/_db.py` and `.mcp/servers/message-broker/server.py`:
  added idempotent indexes for legacy `messages` filters used by dashboards.
