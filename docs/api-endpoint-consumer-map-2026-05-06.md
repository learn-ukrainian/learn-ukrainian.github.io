# API Endpoint Consumer Map - 2026-05-06

Scope: `scripts/api/*_router.py`, `scripts/api/main.py`, and `dashboards/*.html`. Route inventory comes from the FastAPI app object; consumers were checked with `rg` across `dashboards/`, `scripts/`, and `docs/`. `MEMORY.md` is not present in this worktree.

## Endpoint x Consumer Matrix

| Route | HTTP method | Router file | Consumer(s) | Last touched | Verdict |
| --- | --- | --- | --- | --- | --- |
| /api/admin/backup/list | GET | scripts/api/admin_router.py | playgrounds/admin.html; docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/admin/backup/qdrant | POST | scripts/api/admin_router.py | playgrounds/admin.html; docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/admin/backup/{filename} | DELETE | scripts/api/admin_router.py | playgrounds/admin.html; docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/admin/collections | GET | scripts/api/admin_router.py | playgrounds/admin.html; docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/admin/collections/verify | POST | scripts/api/admin_router.py | playgrounds/admin.html; docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/admin/disk-usage | GET | scripts/api/admin_router.py | playgrounds/admin.html; docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/admin/health | GET | scripts/api/admin_router.py | playgrounds/admin.html; docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/admin/maintenance/annotation-stats | GET | scripts/api/admin_router.py | playgrounds/admin.html; docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/admin/maintenance/clean-logs | POST | scripts/api/admin_router.py | playgrounds/admin.html; docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/admin/maintenance/embedding-cache-stats | GET | scripts/api/admin_router.py | playgrounds/admin.html; docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/admin/maintenance/vacuum-broker | POST | scripts/api/admin_router.py | playgrounds/admin.html; docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/agent/module/{level}/{slug} | GET | scripts/api/agent_router.py | docs/MONITOR-API.md | 2026-05-05 | KEEP |
| /api/agent/orchestration/{level}/{slug} | GET | scripts/api/agent_router.py | docs/MONITOR-API.md | 2026-05-05 | KEEP |
| /api/agent/prompt-summary/{level}/{slug} | GET | scripts/api/agent_router.py | docs/MONITOR-API.md | 2026-05-05 | KEEP |
| /api/agent/runtime | GET | scripts/api/agent_router.py | docs/MONITOR-API.md | 2026-05-05 | KEEP |
| /api/agent/worktree | GET | scripts/api/agent_router.py | docs/MONITOR-API.md | 2026-05-05 | KEEP |
| /api/artifacts/ship-ready | GET | scripts/api/artifacts_router.py | docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/artifacts/{track}/{slug} | GET | scripts/api/artifacts_router.py | docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/artifacts/{track}/{slug}/drift | GET | scripts/api/artifacts_router.py | docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/artifacts/{track}/{slug}/files | GET | scripts/api/artifacts_router.py | docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/artifacts/{track}/{slug}/force-preview | GET | scripts/api/artifacts_router.py | docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/artifacts/{track}/{slug}/review-snapshot | GET | scripts/api/artifacts_router.py | docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/blue/activity-errors/{track_id}/{slug} | GET | scripts/api/blue_router.py | docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/blue/audit/{track_id}/{slug} | GET | scripts/api/blue_router.py | docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/blue/final-review-summary/{track_id}/{slug} | GET | scripts/api/blue_router.py | docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/blue/freshness | GET | scripts/api/blue_router.py | docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/blue/health | GET | scripts/api/blue_router.py | docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/blue/history | GET | scripts/api/blue_router.py | docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/blue/live-status | GET | scripts/api/blue_router.py | docs/MONITOR-API.md | 2026-05-04 | DEPRECATE |
| /api/blue/metrics | GET | scripts/api/blue_router.py | docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/build/events/active | GET | scripts/api/build_events_router.py | playgrounds/build-events.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/build/events/recent | GET | scripts/api/build_events_router.py | playgrounds/build-events.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/comms/acknowledge/{message_id} | POST | scripts/api/comms_router.py | playgrounds/channels.html; playgrounds/track-health.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/comms/active-processes | GET | scripts/api/comms_router.py | playgrounds/channels.html; playgrounds/track-health.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/comms/batch-progress | GET | scripts/api/comms_router.py | playgrounds/channels.html; playgrounds/track-health.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/comms/batch-progress/{track} | GET | scripts/api/comms_router.py | playgrounds/channels.html; playgrounds/track-health.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/comms/by-module/{track}/{slug} | GET | scripts/api/comms_router.py | playgrounds/channels.html; playgrounds/track-health.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/comms/channels | GET | scripts/api/comms_router.py | playgrounds/channels.html; playgrounds/track-health.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/comms/channels/{name} | GET | scripts/api/comms_router.py | playgrounds/channels.html; playgrounds/track-health.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/comms/channels/{name}/deliveries | GET | scripts/api/comms_router.py | playgrounds/channels.html; playgrounds/track-health.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/comms/channels/{name}/messages | GET | scripts/api/comms_router.py | playgrounds/channels.html; playgrounds/track-health.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/comms/channels/{name}/post | POST | scripts/api/comms_router.py | playgrounds/channels.html; playgrounds/track-health.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/comms/channels/{name}/threads/{thread_id} | GET | scripts/api/comms_router.py | playgrounds/channels.html; playgrounds/track-health.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/comms/cleanup | POST | scripts/api/comms_router.py | playgrounds/channels.html; playgrounds/track-health.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/comms/conversation/{task_id} | GET | scripts/api/comms_router.py | playgrounds/comms.html; docs/MONITOR-API.md | 2026-05-06 | DEPRECATE |
| /api/comms/conversations | GET | scripts/api/comms_router.py | playgrounds/comms.html; docs/MONITOR-API.md | 2026-05-06 | DEPRECATE |
| /api/comms/health | GET | scripts/api/comms_router.py | playgrounds/channels.html; playgrounds/track-health.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/comms/inbox | GET | scripts/api/comms_router.py | playgrounds/channels.html; playgrounds/track-health.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/comms/live-activity | GET | scripts/api/comms_router.py | playgrounds/comms.html; docs/MONITOR-API.md | 2026-05-06 | DEPRECATE |
| /api/comms/messages | GET | scripts/api/comms_router.py | playgrounds/comms.html; docs/MONITOR-API.md | 2026-05-06 | DEPRECATE |
| /api/comms/send | POST | scripts/api/comms_router.py | playgrounds/comms.html; docs/MONITOR-API.md | 2026-05-06 | DEPRECATE |
| /api/comms/stats | GET | scripts/api/comms_router.py | playgrounds/channels.html; playgrounds/track-health.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/comms/zombies | GET | scripts/api/comms_router.py | playgrounds/channels.html; playgrounds/track-health.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/consultation/history | GET | scripts/api/consultation_router.py | playgrounds/consultation.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-05 | KEEP |
| /api/consultation/history/{track}/{slug} | GET | scripts/api/consultation_router.py | playgrounds/consultation.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-05 | KEEP |
| /api/consultation/metrics | GET | scripts/api/consultation_router.py | playgrounds/consultation.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-05 | KEEP |
| /api/consultation/queue | GET | scripts/api/consultation_router.py | playgrounds/consultation.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-05 | KEEP |
| /api/consultation/queue/{filename} | GET | scripts/api/consultation_router.py | playgrounds/consultation.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-05 | KEEP |
| /api/consultation/queue/{filename}/approve | POST | scripts/api/consultation_router.py | playgrounds/consultation.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-05 | KEEP |
| /api/consultation/queue/{filename}/reject | POST | scripts/api/consultation_router.py | playgrounds/consultation.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-05 | KEEP |
| /api/analytics/cost | GET | scripts/api/cost_router.py | playgrounds/cost.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-04-11 | KEEP |
| /api/analytics/cost/module/{level}/{slug} | GET | scripts/api/cost_router.py | playgrounds/cost.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-04-11 | KEEP |
| /api/analytics/cost/phase/{name} | GET | scripts/api/cost_router.py | playgrounds/cost.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-04-11 | KEEP |
| /api/dashboard/activity-config | GET | scripts/api/dashboard_router.py | playgrounds/audit-dashboard.html; playgrounds/curriculum-dashboard.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/dashboard/comms | GET | scripts/api/dashboard_router.py | playgrounds/audit-dashboard.html; playgrounds/curriculum-dashboard.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/dashboard/comms/conversation/{task_id} | GET | scripts/api/dashboard_router.py | playgrounds/audit-dashboard.html; playgrounds/curriculum-dashboard.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/dashboard/comms/message/{message_id} | GET | scripts/api/dashboard_router.py | playgrounds/audit-dashboard.html; playgrounds/curriculum-dashboard.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/dashboard/comms/messages | GET | scripts/api/dashboard_router.py | playgrounds/audit-dashboard.html; playgrounds/curriculum-dashboard.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/dashboard/module/{track_id}/{slug} | GET | scripts/api/dashboard_router.py | playgrounds/audit-dashboard.html; playgrounds/curriculum-dashboard.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/dashboard/overview | GET | scripts/api/dashboard_router.py | playgrounds/audit-dashboard.html; playgrounds/curriculum-dashboard.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/dashboard/pipeline | GET | scripts/api/dashboard_router.py | playgrounds/audit-dashboard.html; playgrounds/curriculum-dashboard.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/dashboard/research | GET | scripts/api/dashboard_router.py | playgrounds/audit-dashboard.html; playgrounds/curriculum-dashboard.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/dashboard/track/{track_id} | GET | scripts/api/dashboard_router.py | playgrounds/audit-dashboard.html; playgrounds/curriculum-dashboard.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/dashboard/track/{track_id}/summary | GET | scripts/api/dashboard_router.py | playgrounds/audit-dashboard.html; playgrounds/curriculum-dashboard.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/decisions | GET | scripts/api/decisions_router.py | docs/MONITOR-API.md; docs/decisions/* | 2026-04-04 | KEEP |
| /api/decisions/budget | GET | scripts/api/decisions_router.py | docs/MONITOR-API.md; docs/decisions/* | 2026-04-04 | KEEP |
| /api/decisions/scope/{scope} | GET | scripts/api/decisions_router.py | docs/MONITOR-API.md; docs/decisions/* | 2026-04-04 | KEEP |
| /api/decisions/stale | GET | scripts/api/decisions_router.py | docs/MONITOR-API.md; docs/decisions/* | 2026-04-04 | KEEP |
| /api/decisions/{dec_id} | GET | scripts/api/decisions_router.py | docs/MONITOR-API.md; docs/decisions/* | 2026-04-04 | KEEP |
| /api/delegate/tasks | GET | scripts/api/delegate_router.py | playgrounds/delegate.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-04-23 | KEEP |
| /api/delegate/tasks/{task_id} | GET | scripts/api/delegate_router.py | playgrounds/delegate.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-04-23 | KEEP |
| /api/git/cleanup | GET | scripts/api/git_hygiene_router.py | docs/MONITOR-API.md | 2026-04-25 | KEEP |
| /api/git/hygiene | GET | scripts/api/git_hygiene_router.py | docs/MONITOR-API.md | 2026-04-25 | KEEP |
| /api/gold/active-orchestration | GET | scripts/api/gold_router.py | docs/MONITOR-API.md | 2026-05-05 | KEEP |
| /api/gold/broker-messages | GET | scripts/api/gold_router.py | docs/MONITOR-API.md | 2026-05-05 | KEEP |
| /api/gold/ground-truth | GET | scripts/api/gold_router.py | docs/MONITOR-API.md | 2026-05-05 | KEEP |
| /api/gold/health | GET | scripts/api/gold_router.py | docs/MONITOR-API.md | 2026-05-05 | KEEP |
| /api/gold/inspect/{track_id}/{slug} | GET | scripts/api/gold_router.py | docs/MONITOR-API.md | 2026-05-05 | KEEP |
| /api/gold/orchestration/{track_id}/{slug} | GET | scripts/api/gold_router.py | docs/MONITOR-API.md | 2026-05-05 | KEEP |
| /api/gold/plan-details/{track_id} | GET | scripts/api/gold_router.py | docs/MONITOR-API.md | 2026-05-05 | KEEP |
| /api/gold/union-stats | GET | scripts/api/gold_router.py | docs/MONITOR-API.md | 2026-05-05 | KEEP |
| /api/state/governance | GET | scripts/api/governance_router.py | docs/MONITOR-API.md; docs/session-state/* | 2026-04-24 | KEEP |
| /api/images/annotations | GET | scripts/api/images_router.py | playgrounds/image-explorer.html; docs/MONITOR-API.md | 2026-04-17 | KEEP |
| /api/images/annotations/bulk | POST | scripts/api/images_router.py | playgrounds/image-explorer.html; docs/MONITOR-API.md | 2026-04-17 | KEEP |
| /api/images/annotations/{image_id} | PUT | scripts/api/images_router.py | playgrounds/image-explorer.html; docs/MONITOR-API.md | 2026-04-17 | KEEP |
| /api/images/cleanup | POST | scripts/api/images_router.py | playgrounds/image-explorer.html; docs/MONITOR-API.md | 2026-04-17 | KEEP |
| /api/images/page/{pdf_stem}/{page_num} | GET | scripts/api/images_router.py | playgrounds/image-explorer.html; docs/MONITOR-API.md | 2026-04-17 | KEEP |
| /api/images/page_render/{pdf_stem}/{page_num}.png | GET | scripts/api/images_router.py | playgrounds/image-explorer.html; docs/MONITOR-API.md | 2026-04-17 | KEEP |
| /api/images/reload | POST | scripts/api/images_router.py | playgrounds/image-explorer.html; docs/MONITOR-API.md | 2026-04-17 | KEEP |
| /api/images/stats | GET | scripts/api/images_router.py | playgrounds/image-explorer.html; docs/MONITOR-API.md | 2026-04-17 | KEEP |
| /api/images/textbooks | GET | scripts/api/images_router.py | playgrounds/image-explorer.html; docs/MONITOR-API.md | 2026-04-17 | KEEP |
| /api/issues/map | GET | scripts/api/issues_router.py | playgrounds/quality.html; docs/MONITOR-API.md | 2026-04-17 | KEEP |
| /api/batch/active | GET | scripts/api/main.py | playgrounds/index.html; docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/batch/checkpoints | GET | scripts/api/main.py | playgrounds/index.html; docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/batch/dispatcher | GET | scripts/api/main.py | playgrounds/index.html; docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/batch/dispatcher/logs | GET | scripts/api/main.py | playgrounds/index.html; docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/batch/dispatcher/running | GET | scripts/api/main.py | playgrounds/index.html; docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/batch/dispatcher/scan | POST | scripts/api/main.py | playgrounds/index.html; docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/batch/failures | GET | scripts/api/main.py | playgrounds/index.html; docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/batch/usage | GET | scripts/api/main.py | playgrounds/index.html; docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/config | GET | scripts/api/main.py | playgrounds/consultation.html; docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/health | GET | scripts/api/main.py | playgrounds/* smoke tests; docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /api/orient | GET | scripts/api/main.py | playgrounds/orient.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-04 | KEEP |
| /images/{path:path} | GET | scripts/api/main.py | playgrounds/image-explorer.html | 2026-05-04 | KEEP |
| /{path:path} | GET | scripts/api/main.py | playgrounds/*.html static serving | 2026-05-04 | KEEP |
| /api/rag/browse_images | GET | scripts/api/rag_router.py | playgrounds/image-explorer.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/rag/search_images | GET | scripts/api/rag_router.py | playgrounds/image-explorer.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/rag/search_literary | GET | scripts/api/rag_router.py | playgrounds/image-explorer.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/rag/search_text | GET | scripts/api/rag_router.py | playgrounds/image-explorer.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/rag/stats | GET | scripts/api/rag_router.py | playgrounds/image-explorer.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/state/reviewer-ghosts/{track} | GET | scripts/api/reviewer_ghosts_router.py | docs/MONITOR-API.md | 2026-04-24 | KEEP |
| /api/rules | GET | scripts/api/rules_router.py | docs/MONITOR-API.md; docs/session-state/* | 2026-04-17 | KEEP |
| /api/runtime/agents | GET | scripts/api/runtime_router.py | playgrounds/runtime.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-04-21 | KEEP |
| /api/runtime/auth | GET | scripts/api/runtime_router.py | playgrounds/runtime.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-04-21 | KEEP |
| /api/runtime/headroom | GET | scripts/api/runtime_router.py | playgrounds/runtime.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-04-21 | KEEP |
| /api/runtime/recent | GET | scripts/api/runtime_router.py | playgrounds/runtime.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-04-21 | KEEP |
| /api/runtime/usage | GET | scripts/api/runtime_router.py | playgrounds/runtime.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-04-21 | KEEP |
| /api/session/current | GET | scripts/api/session_router.py | docs/MONITOR-API.md | 2026-04-17 | KEEP |
| /api/site/deployments | GET | scripts/api/site_router.py | docs/MONITOR-API.md | 2026-04-17 | KEEP |
| /api/site/health | GET | scripts/api/site_router.py | docs/MONITOR-API.md | 2026-04-17 | KEEP |
| /api/state/build-stats | GET | scripts/api/state_router.py | playgrounds/index.html; playgrounds/progress.html; playgrounds/quality.html; playgrounds/track-health.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/state/build-stats/{track_id} | GET | scripts/api/state_router.py | playgrounds/index.html; playgrounds/progress.html; playgrounds/quality.html; playgrounds/track-health.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/state/build-status | GET | scripts/api/state_router.py | playgrounds/index.html; playgrounds/progress.html; playgrounds/quality.html; playgrounds/track-health.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/state/build-status/{track_id} | GET | scripts/api/state_router.py | playgrounds/index.html; playgrounds/progress.html; playgrounds/quality.html; playgrounds/track-health.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/state/enrichment-status | GET | scripts/api/state_router.py | playgrounds/index.html; playgrounds/progress.html; playgrounds/quality.html; playgrounds/track-health.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/state/failing | GET | scripts/api/state_router.py | playgrounds/index.html; playgrounds/progress.html; playgrounds/quality.html; playgrounds/track-health.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/state/final-reviews/{track_id} | GET | scripts/api/state_router.py | playgrounds/index.html; playgrounds/progress.html; playgrounds/quality.html; playgrounds/track-health.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/state/issues | GET | scripts/api/state_router.py | playgrounds/index.html; playgrounds/progress.html; playgrounds/quality.html; playgrounds/track-health.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/state/manifest | GET | scripts/api/state_router.py | playgrounds/index.html; playgrounds/progress.html; playgrounds/quality.html; playgrounds/track-health.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/state/module/{track_id}/slug/{slug} | GET | scripts/api/state_router.py | playgrounds/index.html; playgrounds/progress.html; playgrounds/quality.html; playgrounds/track-health.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/state/module/{track_id}/{num} | GET | scripts/api/state_router.py | playgrounds/index.html; playgrounds/progress.html; playgrounds/quality.html; playgrounds/track-health.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/state/pipeline-versions | GET | scripts/api/state_router.py | playgrounds/index.html; playgrounds/progress.html; playgrounds/quality.html; playgrounds/track-health.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/state/pipeline/{track_id} | GET | scripts/api/state_router.py | playgrounds/index.html; playgrounds/progress.html; playgrounds/quality.html; playgrounds/track-health.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/state/range/{track_id} | GET | scripts/api/state_router.py | playgrounds/index.html; playgrounds/progress.html; playgrounds/quality.html; playgrounds/track-health.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/state/ready-to-build | GET | scripts/api/state_router.py | playgrounds/index.html; playgrounds/progress.html; playgrounds/quality.html; playgrounds/track-health.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/state/research-coverage | GET | scripts/api/state_router.py | playgrounds/index.html; playgrounds/progress.html; playgrounds/quality.html; playgrounds/track-health.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/state/research/{track_id} | GET | scripts/api/state_router.py | playgrounds/index.html; playgrounds/progress.html; playgrounds/quality.html; playgrounds/track-health.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/state/review-coverage | GET | scripts/api/state_router.py | playgrounds/index.html; playgrounds/progress.html; playgrounds/quality.html; playgrounds/track-health.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/state/summary | GET | scripts/api/state_router.py | playgrounds/index.html; playgrounds/progress.html; playgrounds/quality.html; playgrounds/track-health.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/state/track-health/{track_id} | GET | scripts/api/state_router.py | playgrounds/index.html; playgrounds/progress.html; playgrounds/quality.html; playgrounds/track-health.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/state/weak-points | GET | scripts/api/state_router.py | playgrounds/index.html; playgrounds/progress.html; playgrounds/quality.html; playgrounds/track-health.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/telemetry/tool-timings | GET | scripts/api/telemetry_router.py | docs/MONITOR-API.md | 2026-04-25 | KEEP |
| /api/telemetry/tool-timings | POST | scripts/api/telemetry_router.py | docs/MONITOR-API.md | 2026-04-25 | KEEP |
| /api/wiki/article/{track}/{slug} | GET | scripts/api/wiki_router.py | playgrounds/wiki.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/wiki/build-log | GET | scripts/api/wiki_router.py | playgrounds/wiki.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/wiki/quality-gate | GET | scripts/api/wiki_router.py | playgrounds/wiki.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/wiki/quality-gate/{track} | GET | scripts/api/wiki_router.py | playgrounds/wiki.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/wiki/sources | GET | scripts/api/wiki_router.py | playgrounds/wiki.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/wiki/sources/{track}/{slug} | GET | scripts/api/wiki_router.py | playgrounds/wiki.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/wiki/status | GET | scripts/api/wiki_router.py | playgrounds/wiki.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/wiki/status/{track} | GET | scripts/api/wiki_router.py | playgrounds/wiki.html; playgrounds/index.html; docs/MONITOR-API.md | 2026-05-06 | KEEP |
| /api/worktrees | GET | scripts/api/worktrees_router.py | docs/MONITOR-API.md | 2026-04-17 | KEEP |

## Playground x Usefulness Matrix

| File | Linked from index.html? | Last visited (mtime / git log) | Functional today? | Endpoints used | Verdict |
| --- | --- | --- | --- | --- | --- |
| playgrounds/admin.html | yes | mtime 2026-05-06; git 2026-05-06 | yes (covered by smoke test) | /api/admin/health; /api/admin/disk-usage; /api/admin/backup/list; /api/admin/maintenance/*; /api/admin/collections* | KEEP |
| playgrounds/audit-dashboard.html | yes | mtime 2026-05-06; git 2026-04-17 | yes (covered by smoke test) | /api/dashboard/overview; /api/dashboard/track/{track_id}/summary; /api/dashboard/module/{track_id}/{slug}; /api/state/module/{track_id}/{num} | KEEP |
| playgrounds/build-events.html | yes | mtime 2026-05-06; git 2026-04-11 | yes (covered by smoke test) | /api/build/events/active; /api/build/events/recent | KEEP |
| playgrounds/channels.html | yes | mtime 2026-05-06; git 2026-05-06 | yes (covered by smoke test) | /api/comms/channels; /api/comms/channels/{name}; /api/comms/channels/{name}/messages; /api/comms/channels/{name}/deliveries; /api/comms/channels/{name}/post | KEEP |
| playgrounds/comms.html | no | mtime 2026-05-06; git 2026-05-03 | yes (legacy UI, hidden from index) | /api/comms/messages; /api/comms/conversation/{task_id}; /api/comms/live-activity; /api/comms/batch-progress; /api/comms/zombies; /api/comms/acknowledge/{id}; /api/comms/send; /api/comms/stats; /api/comms/health | DEPRECATE |
| playgrounds/consultation.html | yes | mtime 2026-05-06; git 2026-04-17 | yes (covered by smoke test) | /api/config; /api/consultation/queue; /api/consultation/history; /api/consultation/metrics; /api/consultation/queue/{filename}/{action} | KEEP |
| playgrounds/cost.html | yes | mtime 2026-05-06; git 2026-04-11 | yes (covered by smoke test) | /api/analytics/cost; /api/analytics/cost/module/{level}/{slug}; /api/analytics/cost/phase/{name} | KEEP |
| playgrounds/curriculum-dashboard.html | yes | mtime 2026-05-06; git 2026-04-17 | yes (covered by smoke test) | /api/dashboard/overview; /api/dashboard/track/{track_id}; /api/dashboard/module/{track_id}/{slug} | KEEP |
| playgrounds/delegate.html | yes | mtime 2026-05-06; git 2026-04-11 | yes (covered by smoke test) | /api/delegate/tasks; /api/delegate/tasks/{task_id} | KEEP |
| playgrounds/image-explorer.html | yes | mtime 2026-05-06; git 2026-05-06 | yes (covered by smoke test) | /api/images/textbooks; /api/images/stats; /api/images/annotations; /api/images/annotations/{image_id}; /api/images/annotations/bulk; /api/images/cleanup; /api/images/page/{stem}/{page}; /api/rag/search_text; /api/rag/search_images; /api/rag/search_literary; /images/{path} | KEEP |
| playgrounds/images.html | no | mtime 2026-05-06; git 2026-03-01 | yes (redirect-only) | none; redirect-only alias to /image-explorer.html | DELETE |
| playgrounds/index.html | n/a | mtime 2026-05-06; git 2026-05-06 | yes (root dashboard) | /api/dashboard/overview; /api/state/pipeline-versions; /api/consultation/metrics; /api/state/summary; /api/comms/batch-progress; /api/state/weak-points?limit=1; /api/orient; /api/runtime/agents; /api/delegate/tasks?limit=100; /api/build/events/active; /api/wiki/status; /api/analytics/cost | KEEP |
| playgrounds/orient.html | yes | mtime 2026-05-06; git 2026-04-11 | yes (covered by smoke test) | /api/orient | KEEP |
| playgrounds/progress.html | yes | mtime 2026-05-06; git 2026-04-17 | yes (covered by smoke test) | /api/state/pipeline/{track}; /api/state/summary; /api/state/pipeline-versions | KEEP |
| playgrounds/quality.html | yes | mtime 2026-05-06; git 2026-04-17 | yes (covered by smoke test) | /api/state/research-coverage; /api/state/review-coverage; /api/state/issues; /api/state/weak-points?limit=500 | KEEP |
| playgrounds/runtime.html | yes | mtime 2026-05-06; git 2026-04-11 | yes (covered by smoke test) | /api/runtime/agents; /api/runtime/usage; /api/runtime/headroom; /api/runtime/recent; /api/runtime/auth | KEEP |
| playgrounds/track-health.html | yes | mtime 2026-05-06; git 2026-04-17 | yes (covered by smoke test) | /api/state/build-status; /api/state/enrichment-status; /api/state/track-health/{track}; /api/state/module/{track}/{num}; /api/comms/by-module/{track}/{slug} | KEEP |
| playgrounds/wiki.html | yes | mtime 2026-05-06; git 2026-04-11 | yes (covered by smoke test) | /api/wiki/status; /api/wiki/status/{track}; /api/wiki/quality-gate/{track}; /api/wiki/build-log | KEEP |

## Candidates for deletion

| Path | LOC | Why it is dead or stale | Risk if deleted |
| --- | ---: | --- | --- |
| `playgrounds/images.html` | 11 | Redirect-only alias to `image-explorer.html`; not linked from `playgrounds/index.html`; no API calls. | low |
| `playgrounds/comms.html` | 860 | Hidden legacy comms UI. It is the only active UI consumer of deprecated legacy broker routes; `channels.html` is the current chat surface. | medium; user signoff before deletion |
| `scripts/api/comms_router.py` legacy route section | 1485 | The file still has active channel routes, but `/messages`, `/conversations`, `/conversation/{task_id}`, `/live-activity`, and `/send` only serve hidden `comms.html` plus docs. | medium; delete only after migrating/removing `comms.html` |
| `scripts/api/blue_router.py` `/api/blue/live-status` | 413 | Already marked deprecated; retained for monitor-client compatibility tests. | medium; remove only after docs/tests/client migration |

## Structural-Cause Diagnosis

1. **Single-worker launch plus unbounded request admission.** Before this pass, `package.json` launched normal uvicorn without `--workers` or `--limit-concurrency`, so one slow dashboard request could occupy the only worker. This PR changes `npm run api` and `npm run api:bg` to `--workers 2 --limit-concurrency 32 --timeout-keep-alive 5`, while leaving reload mode single-worker because uvicorn reload and workers are not compatible.

2. **No process-wide timeout or saturation response.** Endpoint-specific fixes cannot protect the server when the next heavy handler appears. `scripts/api/resilience.py` now installs middleware that returns 504 for requests exceeding `API_REQUEST_TIMEOUT_S` and 503 with `Retry-After` when `API_MAX_CONCURRENCY` is saturated. `/api/health` exposes timeout, saturation, in-flight, and recent slow request counters.

3. **Sync SQLite in async handlers with no timing visibility.** Broker/wiki/telemetry/admin handlers use SQLite from async routes. This PR routes API SQLite connections through `connect_sqlite()`, which logs slow `execute`/`executemany`/`executescript` calls over `API_SLOW_SQL_MS` and surfaces recent slow SQL in `/api/health`. Longer-term, the heaviest async handlers should either become sync FastAPI handlers or wrap filesystem/SQLite work with `asyncio.to_thread`.

4. **Whole-tree and whole-file cold scans remain the main endpoint-level stressor.** The first pass fixed the worst scans. This pass found one remaining cold path in `/api/wiki/status`: status calculation scanned article bodies to compute word counts when progress metadata was empty. `scripts/api/wiki_router.py` now builds candidates from progress metadata plus path-only disk discovery and avoids body reads for aggregate status; article body reads remain scoped to `/api/wiki/article/{track}/{slug}`.

5. **Optional external CLI probes can dominate cold dashboard load.** `/api/orient` includes GitHub issue context, but `gh issue list` was taking roughly 0.5 seconds locally. This PR caps that collector at 250 ms so a slow `gh` or network path returns a degraded issues section instead of pushing the dashboard over the 500 ms smoke budget.

6. **Process-local caches are now an explicit tradeoff.** `state_helpers._ttl_cache`, wiki caches, and dashboard helper caches are per worker after the uvicorn change. That is acceptable for local dashboards because values are short-lived, but a future shared cache or persisted snapshot would be needed before treating this as a multi-user service.
