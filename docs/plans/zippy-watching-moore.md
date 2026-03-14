# Plan: Redesign Audit Dashboard for Performance

## Context

All dashboard pages are slow. The audit dashboard is the worst — it loads a 1.3MB research endpoint on every page load AND every 60 seconds. Track detail responses are 100KB+. With 1728 modules across 23 tracks, the DOM rendering is also heavy.

## Root Causes

1. **Research endpoint (1.3MB)** loaded eagerly + refreshed every 60s
2. **Track detail loads ALL module data** when expanded (100KB per track)
3. **All tracks rendered on page load** even though most are collapsed
4. **No server-side response trimming** — full module objects sent when only slug/status needed
5. **setInterval refresh every 30s** for overview + 60s for research — thrashing

## Plan

### 1. Lazy-load research section

Move research from eager load to a collapsible section that fetches on click. Remove the 60s setInterval. Research data is rarely needed — only when investigating weak modules.

**Change in `audit-dashboard.html`:**
- Research section starts collapsed with a "Load Research Coverage" button
- `fetchResearch()` only called when button clicked
- Remove `setInterval(fetchResearch, 60000)`

### 2. Lightweight overview (no module-level data)

The overview endpoint already returns track-level stats (8KB). The problem is track detail (100KB) loads when expanded. Keep the current lazy-load-on-expand pattern but trim the track detail response.

**Change in `dashboard_router.py` / `dashboard_helpers.py`:**
- Add `GET /api/dashboard/track/{id}/summary` — returns only `[{num, slug, status, pipeline_version, has_review}]` (no plan, no meta, no activities)
- The existing `/api/dashboard/track/{id}` stays for the side panel (full detail per module)

### 3. Reduce refresh frequency

- Overview: 30s → 120s (modules don't change that fast)
- Research: remove auto-refresh entirely (manual only)
- Track cache on client: keep expanded track data until user refreshes or 5 min TTL

### 4. Virtual scrolling for module grids (optional)

For tracks with 200+ modules, rendering 200 cells is fine. No virtual scrolling needed — the real issue is data transfer, not DOM.

## Files to modify

- `playgrounds/audit-dashboard.html` — lazy research, reduced refresh, trimmed fetch
- `scripts/api/dashboard_router.py` — add lightweight track summary endpoint
- `scripts/api/dashboard_helpers.py` — add summary scan function

## Verification

1. Open audit dashboard — should load in <1s (only overview: 8KB)
2. Expand a track — should load in <200ms (summary: ~10KB vs 100KB)
3. Click module — side panel loads full detail (unchanged)
4. Research section — only loads when clicked
5. No auto-refresh thrashing in network tab
