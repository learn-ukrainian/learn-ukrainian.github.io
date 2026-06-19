# Dashboard-Panel Endpoint Conformance Audit

This report is a deterministic audit of which dashboards and panels reference live vs. dead API endpoints, checked against the OpenAPI route definitions served by the API.

## #M-4 DETERMINISTIC PREAMBLE
- **API Status**: UP and running at `http://localhost:8765`
- **OpenAPI Route Template Count**: "184" paths found in `/openapi.json`
- **Total Audited HTML Dashboards**: 21

---

## Conformance Summary

| Dashboard | Classification | Live Refs (Count) | Dead Refs | Recommendation |
| :--- | :--- | :---: | :--- | :--- |
| [admin.html](file:///Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/agy/dashboard-endpoint-audit/dashboards/admin.html) | **healthy** | 11 | None | keep |
| [artifacts.html](file:///Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/agy/dashboard-endpoint-audit/dashboards/artifacts.html) | **healthy** | 1 | None | keep |
| [audit-dashboard.html](file:///Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/agy/dashboard-endpoint-audit/dashboards/audit-dashboard.html) | **healthy** | 4 | None | keep |
| [build-events.html](file:///Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/agy/dashboard-endpoint-audit/dashboards/build-events.html) | **healthy** | 2 | None | keep |
| [channels.html](file:///Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/agy/dashboard-endpoint-audit/dashboards/channels.html) | **healthy** | 5 | None | keep |
| [comms.html](file:///Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/agy/dashboard-endpoint-audit/dashboards/comms.html) | **healthy** | 11 | None | keep |
| [consultation.html](file:///Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/agy/dashboard-endpoint-audit/dashboards/consultation.html) | **healthy** | 6 | None | keep |
| [cost.html](file:///Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/agy/dashboard-endpoint-audit/dashboards/cost.html) | **healthy** | 4 | None | keep |
| [curriculum-dashboard.html](file:///Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/agy/dashboard-endpoint-audit/dashboards/curriculum-dashboard.html) | **healthy** | 3 | None | keep |
| [delegate.html](file:///Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/agy/dashboard-endpoint-audit/dashboards/delegate.html) | **healthy** | 2 | None | keep |
| [headroom.html](file:///Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/agy/dashboard-endpoint-audit/dashboards/headroom.html) | **healthy** | 1 | None | keep |
| [image-explorer.html](file:///Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/agy/dashboard-endpoint-audit/dashboards/image-explorer.html) | **healthy** | 9 | None | keep |
| [images.html](file:///Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/agy/dashboard-endpoint-audit/dashboards/images.html) | **static** | 0 | None | keep |
| [index.html](file:///Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/agy/dashboard-endpoint-audit/dashboards/index.html) | **healthy** | 14 | None | keep |
| [orient.html](file:///Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/agy/dashboard-endpoint-audit/dashboards/orient.html) | **healthy** | 2 | None | keep |
| [progress.html](file:///Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/agy/dashboard-endpoint-audit/dashboards/progress.html) | **healthy** | 3 | None | keep |
| [quality.html](file:///Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/agy/dashboard-endpoint-audit/dashboards/quality.html) | **healthy** | 5 | None | keep |
| [routing.html](file:///Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/agy/dashboard-endpoint-audit/dashboards/routing.html) | **healthy** | 4 | None | keep |
| [runtime.html](file:///Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/agy/dashboard-endpoint-audit/dashboards/runtime.html) | **healthy** | 4 | None | keep |
| [track-health.html](file:///Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/agy/dashboard-endpoint-audit/dashboards/track-health.html) | **healthy** | 8 | None | keep |
| [wiki.html](file:///Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/agy/dashboard-endpoint-audit/dashboards/wiki.html) | **healthy** | 5 | None | keep |

---

## Deterministic Evidence per Dashboard

Below is the raw evidence for each audited dashboard, listing the exact `/api/...` reference strings extracted from the source files and the corresponding OpenAPI route templates they match.

### admin.html
- **Classification**: **HEALTHY**
- **Live Reference Matches**:
  - Extract: `/api/admin/backup/${filename}`
    Matches template: `/api/admin/backup/{filename}`
  - Extract: `/api/admin/backup/list`
    Matches template: `/api/admin/backup/list`
  - Extract: `/api/admin/backup/qdrant`
    Matches template: `/api/admin/backup/qdrant`
  - Extract: `/api/admin/collections`
    Matches template: `/api/admin/collections`
  - Extract: `/api/admin/collections/verify`
    Matches template: `/api/admin/collections/verify`
  - Extract: `/api/admin/disk-usage`
    Matches template: `/api/admin/disk-usage`
  - Extract: `/api/admin/health`
    Matches template: `/api/admin/health`
  - Extract: `/api/admin/maintenance/annotation-stats`
    Matches template: `/api/admin/maintenance/annotation-stats`
  - Extract: `/api/admin/maintenance/clean-logs?max_age_days=${days}`
    Matches template: `/api/admin/maintenance/clean-logs`
  - Extract: `/api/admin/maintenance/embedding-cache-stats`
    Matches template: `/api/admin/maintenance/embedding-cache-stats`
  - Extract: `/api/admin/maintenance/vacuum-broker`
    Matches template: `/api/admin/maintenance/vacuum-broker`

### artifacts.html
- **Classification**: **HEALTHY**
- **Live Reference Matches**:
  - Extract: `/api/artifacts/html`
    Matches template: `/api/artifacts/html`

### audit-dashboard.html
- **Classification**: **HEALTHY**
- **Live Reference Matches**:
  - Extract: `/api/dashboard/module/${trackId}/${slug}`
    Matches template: `/api/dashboard/module/{track_id}/{slug}`
  - Extract: `/api/dashboard/overview`
    Matches template: `/api/dashboard/overview`
  - Extract: `/api/dashboard/track/${trackId}/summary`
    Matches template: `/api/dashboard/track/{track_id}/summary`
  - Extract: `/api/state/module/${trackId}/${num}`
    Matches template: `/api/state/module/{track_id}/{num}`

### build-events.html
- **Classification**: **HEALTHY**
- **Live Reference Matches**:
  - Extract: `/api/build/events/active`
    Matches template: `/api/build/events/active`
  - Extract: `/api/build/events/recent?${recentQuery()}`
    Matches template: `/api/build/events/recent`

### channels.html
- **Classification**: **HEALTHY**
- **Live Reference Matches**:
  - Extract: `/api/comms/channels`
    Matches template: `/api/comms/channels`
  - Extract: `/api/comms/channels/${encName}`
    Matches template: `/api/comms/channels/{name}`
  - Extract: `/api/comms/channels/${encName}/messages?tail=50`
    Matches template: `/api/comms/channels/{name}/messages`
  - Extract: `/api/comms/channels/${encodeURIComponent(activeChannel)}/deliveries?status=pending&limit=20`
    Matches template: `/api/comms/channels/{name}/deliveries`
  - Extract: `/api/comms/channels/${encodeURIComponent(activeChannel)}/post`
    Matches template: `/api/comms/channels/{name}/post`

### comms.html
- **Classification**: **HEALTHY**
- **Live Reference Matches**:
  - Extract: `/api/build/events/active`
    Matches template: `/api/build/events/active`
  - Extract: `/api/build/events/recent?limit=${Math.max(DISPATCH_LIMIT, 40)}`
    Matches template: `/api/build/events/recent`
  - Extract: `/api/comms/acknowledge/${id}`
    Matches template: `/api/comms/acknowledge/{message_id}`
  - Extract: `/api/comms/batch-progress`
    Matches template: `/api/comms/batch-progress`
  - Extract: `/api/comms/conversation/${encodeURIComponent(taskId)}?${params}`
    Matches template: `/api/comms/conversation/{task_id}`
  - Extract: `/api/comms/health`
    Matches template: `/api/comms/health`
  - Extract: `/api/comms/messages?${params}`
    Matches template: `/api/comms/messages`
  - Extract: `/api/comms/messages?limit=1&offset=0`
    Matches template: `/api/comms/messages`
  - Extract: `/api/comms/send`
    Matches template: `/api/comms/send`
  - Extract: `/api/comms/stats`
    Matches template: `/api/comms/stats`
  - Extract: `/api/comms/zombies`
    Matches template: `/api/comms/zombies`

### consultation.html
- **Classification**: **HEALTHY**
- **Live Reference Matches**:
  - Extract: `/api/config`
    Matches template: `/api/config`
  - Extract: `/api/consultation/history?limit=200`
    Matches template: `/api/consultation/history`
  - Extract: `/api/consultation/metrics`
    Matches template: `/api/consultation/metrics`
  - Extract: `/api/consultation/queue`
    Matches template: `/api/consultation/queue`
  - Extract: `/api/consultation/queue/${filename}`
    Matches template: `/api/consultation/queue/{filename}`
  - Extract: `/api/consultation/queue/${filename}/${action}?confirm=true`
    Matches template: `/api/consultation/queue/{filename}/approve`

### cost.html
- **Classification**: **HEALTHY**
- **Live Reference Matches**:
  - Extract: `/api/analytics/cost`
    Matches template: `/api/analytics/cost`
  - Extract: `/api/analytics/cost/module/${encodeURIComponent(level)}/${encodeURIComponent(slug)}`
    Matches template: `/api/analytics/cost/module/{level}/{slug}`
  - Extract: `/api/analytics/cost/phase/${encodeURIComponent(query)}`
    Matches template: `/api/analytics/cost/phase/{name}`
  - Extract: `/api/analytics/cost?track=${encodeURIComponent(query)}`
    Matches template: `/api/analytics/cost`

### curriculum-dashboard.html
- **Classification**: **HEALTHY**
- **Live Reference Matches**:
  - Extract: `/api/dashboard/module/${trackId}/${slug}`
    Matches template: `/api/dashboard/module/{track_id}/{slug}`
  - Extract: `/api/dashboard/overview`
    Matches template: `/api/dashboard/overview`
  - Extract: `/api/dashboard/track/${trackId}`
    Matches template: `/api/dashboard/track/{track_id}`

### delegate.html
- **Classification**: **HEALTHY**
- **Live Reference Matches**:
  - Extract: `/api/delegate/tasks/${encodeURIComponent(taskId)}`
    Matches template: `/api/delegate/tasks/{task_id}`
  - Extract: `/api/delegate/tasks?limit=100`
    Matches template: `/api/delegate/tasks`

### headroom.html
- **Classification**: **HEALTHY**
- **Live Reference Matches**:
  - Extract: `/api/runtime/headroom/stats`
    Matches template: `/api/runtime/headroom/stats`

### image-explorer.html
- **Classification**: **HEALTHY**
- **Live Reference Matches**:
  - Extract: `/api/images/annotations/${imageId}`
    Matches template: `/api/images/annotations/{image_id}`
  - Extract: `/api/images/annotations/bulk`
    Matches template: `/api/images/annotations/bulk`
  - Extract: `/api/images/annotations?${params}`
    Matches template: `/api/images/annotations`
  - Extract: `/api/images/cleanup`
    Matches template: `/api/images/cleanup`
  - Extract: `/api/images/page/${currentStem}/${currentPage}`
    Matches template: `/api/images/page/{pdf_stem}/{page_num}`
  - Extract: `/api/images/page_render/${currentStem}/${currentPage}.png`
    Matches template: `/api/images/page_render/{pdf_stem}/{page_num}.png`
  - Extract: `/api/images/stats`
    Matches template: `/api/images/stats`
  - Extract: `/api/images/textbooks`
    Matches template: `/api/images/textbooks`
  - Extract: `/api/rag/search_${searchType}`
    Matches template: `/api/rag/search_images`

### images.html
- **Classification**: **STATIC**
- No API references found (pure static page).

### index.html
- **Classification**: **HEALTHY**
- **Live Reference Matches**:
  - Extract: `/api/analytics/cost`
    Matches template: `/api/analytics/cost`
  - Extract: `/api/build/events/active`
    Matches template: `/api/build/events/active`
  - Extract: `/api/comms/batch-progress`
    Matches template: `/api/comms/batch-progress`
  - Extract: `/api/consultation/metrics`
    Matches template: `/api/consultation/metrics`
  - Extract: `/api/contracts/routes`
    Matches template: `/api/contracts/routes`
  - Extract: `/api/dashboard/overview`
    Matches template: `/api/dashboard/overview`
  - Extract: `/api/delegate/tasks?limit=100`
    Matches template: `/api/delegate/tasks`
  - Extract: `/api/orient`
    Matches template: `/api/orient`
  - Extract: `/api/runtime/agents`
    Matches template: `/api/runtime/agents`
  - Extract: `/api/runtime/headroom/stats`
    Matches template: `/api/runtime/headroom/stats`
  - Extract: `/api/state/pipeline-versions?fresh=true`
    Matches template: `/api/state/pipeline-versions`
  - Extract: `/api/state/summary?fresh=true`
    Matches template: `/api/state/summary`
  - Extract: `/api/state/weak-points?limit=1`
    Matches template: `/api/state/weak-points`
  - Extract: `/api/wiki/status`
    Matches template: `/api/wiki/status`

### orient.html
- **Classification**: **HEALTHY**
- **Live Reference Matches**:
  - Extract: `/api/discussions/active`
    Matches template: `/api/discussions/active`
  - Extract: `/api/orient`
    Matches template: `/api/orient`

### progress.html
- **Classification**: **HEALTHY**
- **Live Reference Matches**:
  - Extract: `/api/state/pipeline-versions?fresh=true`
    Matches template: `/api/state/pipeline-versions`
  - Extract: `/api/state/pipeline/${trackId}?fresh=true`
    Matches template: `/api/state/pipeline/{track_id}`
  - Extract: `/api/state/summary?fresh=true`
    Matches template: `/api/state/summary`

### quality.html
- **Classification**: **HEALTHY**
- **Live Reference Matches**:
  - Extract: `/api/state/issues`
    Matches template: `/api/state/issues`
  - Extract: `/api/state/research-coverage`
    Matches template: `/api/state/research-coverage`
  - Extract: `/api/state/review-coverage`
    Matches template: `/api/state/review-coverage`
  - Extract: `/api/state/scores/${track}`
    Matches template: `/api/state/scores/{track}`
  - Extract: `/api/state/weak-points?limit=500`
    Matches template: `/api/state/weak-points`

### routing.html
- **Classification**: **HEALTHY**
- **Live Reference Matches**:
  - Extract: `/api/delegate/tasks?limit=100`
    Matches template: `/api/delegate/tasks`
  - Extract: `/api/runtime/agents`
    Matches template: `/api/runtime/agents`
  - Extract: `/api/runtime/usage?days=7`
    Matches template: `/api/runtime/usage`
  - Extract: `/api/state/routing-budget`
    Matches template: `/api/state/routing-budget`

### runtime.html
- **Classification**: **HEALTHY**
- **Live Reference Matches**:
  - Extract: `/api/runtime/agents`
    Matches template: `/api/runtime/agents`
  - Extract: `/api/runtime/headroom?agent=${encodeURIComponent(agent.name)}&model=${encodeURIComponent(agent.default_model || '')}`
    Matches template: `/api/runtime/headroom`
  - Extract: `/api/runtime/recent?limit=50`
    Matches template: `/api/runtime/recent`
  - Extract: `/api/runtime/usage?days=7`
    Matches template: `/api/runtime/usage`

### track-health.html
- **Classification**: **HEALTHY**
- **Live Reference Matches**:
  - Extract: `/api/comms/by-module/${trackId}/${mod.slug}`
    Matches template: `/api/comms/by-module/{track}/{slug}`
  - Extract: `/api/state/build-status`
    Matches template: `/api/state/build-status`
  - Extract: `/api/state/build-status/${trackId}`
    Matches template: `/api/state/build-status/{track_id}`
  - Extract: `/api/state/enrichment-status`
    Matches template: `/api/state/enrichment-status`
  - Extract: `/api/state/module/${trackId}/${num}`
    Matches template: `/api/state/module/{track_id}/{num}`
  - Extract: `/api/state/pipeline-versions?track=${trackId}`
    Matches template: `/api/state/pipeline-versions`
  - Extract: `/api/state/summary?fresh=true`
    Matches template: `/api/state/summary`
  - Extract: `/api/state/track-health/${trackId}`
    Matches template: `/api/state/track-health/{track_id}`

### wiki.html
- **Classification**: **HEALTHY**
- **Live Reference Matches**:
  - Extract: `/api/state/summary?fresh=true`
    Matches template: `/api/state/summary`
  - Extract: `/api/wiki/build-log?${params.toString()}`
    Matches template: `/api/wiki/build-log`
  - Extract: `/api/wiki/quality-gate/${encodeURIComponent(selectedTrack)}`
    Matches template: `/api/wiki/quality-gate/{track}`
  - Extract: `/api/wiki/status`
    Matches template: `/api/wiki/status`
  - Extract: `/api/wiki/status/${encodeURIComponent(selectedTrack)}`
    Matches template: `/api/wiki/status/{track}`

---

## Proposed Conformance CI Gate

To prevent future API rot and ensure that dashboards do not reference deprecated or removed API endpoints, we propose establishing a conformance test check in the CI pipeline:

1. **Extraction Stage**:
   - Utilize a custom Python parser/linter script (similar to the extraction logic used in this audit) to scan all `dashboards/*.html` files for `/api/...` string patterns (extracting from HTML links, JS single/double-quoted strings, and template literals).
   - Resolve base API variables (e.g., `const API = '/api/dashboard'`) to expand them to full routes.

2. **Cross-Reference Gate**:
   - Fetch the latest OpenAPI schema (e.g. from `http://localhost:8765/openapi.json` or a generated schemas file).
   - Perform segment-by-segment matching using two-pass comparison (strict matching for resource routes, permissive matching for action routing variables).
   - Reject the commit if any extracted reference does not match a valid OpenAPI route template.

3. **Integration**:
   - Run this check as a pre-commit hook or a GitHub Actions workflow step on every pull request.
   - Maintain a whitelist configuration file (e.g., `.dashboard-api-whitelist.json`) if there are valid non-registered routes (such as external third-party API urls) that need to be bypassed.
