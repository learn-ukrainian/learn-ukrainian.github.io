# PR #2256 codex review — 2026-05-24

## Verdict

`REQUEST_CHANGES`

## Summary (3 sentences)

PR #2256 migrates `comms.html` off `/api/comms/live-activity`, polishes `artifacts.html`, applies shared monitor styling to the audit dashboard, and changes `/api/images/textbooks` to avoid opening every PDF on list calls. The endpoint migration exists and is REST JSON, not SSE, but the image endpoint now returns an indexed-image page maximum instead of the true PDF page count, and the dashboard data generation path is still split between `playgrounds/` and `dashboards/`. I would not merge until those runtime/path issues and the stale consumer-map doc are fixed; CI could not be rechecked because `gh` cannot reach `api.github.com` in this sandbox.

## Findings

### Critical (block merge)
- None

### Significant (delay merge for fix)
- A: `/api/images/textbooks` no longer opens every PDF, but it also no longer returns the real PDF `page_count`; `image-explorer.html` uses that value as the hard navigation limit.
- E: `scripts/build/build_playgrounds.py` now reads `dashboards/data/status.json`, but `npm run dashboards:data` still writes `scripts/playgrounds/data/status.json`, so `npm run dashboards` can build from stale tracked dashboard data.
- G: `docs/api-endpoint-consumer-map-2026-05-06.md` says its scope is `dashboards/*.html`, but most consumer rows still list `playgrounds/*.html` and still claim `playgrounds/comms.html` consumes `/api/comms/live-activity`.

### Nit (track as follow-up, don't block)
- B: No new blocking XSS found in the changed `artifacts.html` flow; loading failure cleanup and refresh disabling are present. Existing `escapeHtml()` is still used in HTML attributes, so a future hardening pass should use DOM construction or an attribute escaper.
- C: `/api/build/events` is registered and `comms.html` calls `/api/build/events/active` plus `/api/build/events/recent`; no SSE reconnect handling is needed because these are JSON endpoints.
- D: `monitor.css` defines the parchment variables and shared nav classes used by `audit-dashboard.html`.
- F: The tests add endpoint coverage and timing budget entries, but they do not assert that `pymupdf.open()` / `_read_pdf_page_count()` is not called by `/api/images/textbooks`.

## CI cross-check

`gh pr view 2256 --json statusCheckRollup,mergeStateStatus` — paste raw output here.
