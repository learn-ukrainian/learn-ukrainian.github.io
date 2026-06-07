# Monitor API/UI Audit - 2026-06-07

Issue: #2794
Baseline: `2a768923d6` (`fix(monitor): make status dashboard trustworthy (#2790)`)

## Scope

This pass audits the local Monitor API and dashboard UI after #2790 made
`/api/state` and the main state dashboards trustworthy. The inventory covers:

- FastAPI routes mounted from `scripts/api/main.py` and `scripts/api/**`
- Local dashboard pages in `dashboards/**`
- Monitor API consumers in `starlight/src/**`
- Dashboard generation and Monitor-client scripts that consume the API

Route inventory was generated from the FastAPI app object, not by guessing from
source text. Dashboard consumer inventory was checked with literal `/api/...`
references in `dashboards/**` and `starlight/src/**`.

## Current Inventory

- FastAPI public HTTP routes: 175 total
- Routes under `/api/*`: 169
- Deprecated API routes: 6
- WebSocket routes: 1 (`/ws/batch`)
- Local dashboard HTML pages: 20 plus `dashboards/monitor.css` and
  `dashboards/data/status.json`
- Starlight Monitor API consumer: `starlight/src/components/LiveStatus.tsx`

## Route Matrix

| Endpoint family | Purpose | Source of truth | Cache / freshness contract | Primary consumers | Overlap / duplication | Stale or misleading risk | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/api/state/*` except `/api/state/reviewer-ghosts/*` | Canonical project, track, module, research, review, build, routing, manifest state | `curriculum.yaml`, `plans/**`, orchestration `state.json`, research/dossier docs, generated/published artifacts, review/audit files, cost records | Explicit per-endpoint TTLs in `state_router.py`; major endpoints return `meta.source`, `meta.cache`, `meta.stale_after_s`; `?fresh=true` on summary, pipeline, coverage, versions | `progress.html`, `track-health.html`, `quality.html`, `index.html`, Starlight `LiveStatus`, agents | Overlaps old `/api/blue/live-status`, `/api/dashboard/overview`, and some `/api/gold/*` views | Low after #2790 for summary/progress; medium for state endpoints that still omit `meta` | Keep canonical. Add a machine-readable route contract registry so every endpoint has an explicit source/freshness statement even when payload lacks `meta`. |
| `/api/state/reviewer-ghosts/*` | Reviewer hallucination telemetry for missing-anchor `<fixes>` bundles | `curriculum/l2-uk-en/{track}/review/*-ghost-review-r*.yaml` | No route cache; per-request directory scan with optional `slug` and `since` filters | Future dashboards, agents, tests | Physically under `/api/state`, logically telemetry | Low/medium: globbing it into canonical state would misstate purpose | Keep as a distinct contract row despite the `/api/state` mount. |
| `/api/dashboard/*` | Rich dashboard projections for audit/curriculum/comms pages | Dashboard helper scans over plans, status cache, research, review, orchestration, broker | `_track_cache` 30s, `_summary_cache` 60s, shared state-summary cache 60s for overview; most payloads do not expose meta | `audit-dashboard.html`, `curriculum-dashboard.html`, `index.html` | Overlaps `/api/state/*` for counts/progress; richer module detail remains distinct | Medium: consumers can forget these are derived projections, not canonical state | Keep for page-specific detail. Contract says `/api/state/*` is canonical for counts and freshness-sensitive state. |
| `/api/blue/*` | Legacy Blue/final-review helper endpoints | Status cache, module files, activity YAML, review files, batch state | No route cache; `/audit?...fresh=true` runs audit script as side effect; `/live-status` is deprecated and returns deprecation headers | Agents and old docs; no active dashboard for `/live-status` | `/live-status` duplicates `/api/state/build-status`; audit/final-review overlap artifact/state endpoints | High for `/live-status`; low/medium for final-review workflow | Retain final-review helpers. Keep `/live-status` deprecated with replacement header until consumers are gone. |
| `/api/gold/*` and `/api/agent/*` | Older team/agent module inspection views | Plans, module files, orchestration, broker/runtime files | No route cache; live filesystem/broker reads | Agent docs and older workflows | Overlaps `/api/state/module`, `/api/artifacts`, `/api/dashboard/module` | Medium: legacy names hide canonical source | Retain for compatibility. Future slice can merge into `/api/state` and `/api/artifacts` after consumer audit. |
| `/api/artifacts/*`, `/artifacts/*`, `/files/*` | Artifact classification, ship-ready checks, HTML/report file serving | Plans, generated files, Starlight MDX, review/audit docs, docs/audit reports | No route cache; file manifests and drift checks are live reads | `artifacts.html`, agents | Complements `/api/state`; overlaps on published/stale signals | Low | Keep. Contract should flag generated/status/review files as read-only evidence and not PR artifacts. |
| `/api/comms/channels*`, `/api/comms/inbox`, `/api/comms/agent-activity` | Canonical channel bridge and agent activity | SQLite message broker and delivery tables | No route cache; live broker reads | `channels.html`, `/api/state/manifest`, agents | Replaces legacy message/conversation endpoints | Low | Keep canonical. |
| `/api/comms/messages`, `/api/comms/conversations`, `/api/comms/conversation/*`, `/api/comms/send`, `/api/comms/live-activity` | Legacy direct-message bridge | SQLite broker and process probes | No route cache; deprecated in OpenAPI | `comms.html`, old `ask-*` path | Duplicates channel bridge | Medium: hidden legacy UI is still linked in primary nav; routes are deprecated but alive | Retain with explicit legacy contract. Do not delete before CLI/old UI migration. |
| `/api/comms/batch-progress`, `/api/comms/zombies`, `/api/comms/active-processes`, `/api/comms/stats`, `/api/comms/health`, `/api/comms/cleanup`, `/api/comms/acknowledge`, `/api/comms/by-module/*` | Broker/process health, batch progress, zombie cleanup, module-linked messages | SQLite broker, process table/probes, build state | No route cache; live reads/writes where method is POST | `comms.html`, `track-health.html`, agents | Some status overlaps `/api/delegate/*` and `/api/build/events/*` | Low/medium | Keep; separate from deprecated legacy message send/list routes in contracts. |
| `/api/delegate/*` | Delegated task list, active task count, result detail | `batch_state/tasks/*.json`, process liveness, result files | No route cache; live filesystem/process reads | `delegate.html`, `index.html`, agent cold starts | Complements `/api/orient.delegate` and `/api/comms` | Low | Keep. |
| `/api/worktrees` | Active git worktree registry | `git worktree list --porcelain`, per-worktree `git status`, and `git log -1` | No route cache; bounded subprocess timeout per git call | Agents, cold-start tooling, worktree hygiene | Complements `/api/git/hygiene` and `/api/git/cleanup` | Low; failures degrade to empty/error payload | Keep. |
| `/api/build/events/*` | Recent and active module build events | `curriculum/l2-uk-en/**/orchestration/**/dispatch/*-meta.json` plus state files | No route cache; scan capped at 5000 meta files | `build-events.html`, `comms.html`, `index.html` | Complements delegate and comms activity | Low | Keep. |
| `/api/runtime/*` | Agent inventory, usage, headroom, auth mode | Runtime config, usage JSONL, environment presence booleans, OAuth credential presence | No route cache; live file/env reads; auth endpoint never returns secret values | `runtime.html`, `index.html`, agents | Cost/headroom overlaps `/api/state/routing-budget` and cost API | Low | Keep. |
| `/api/cost/*`, `/api/analytics/cost/*` | Cost summaries by project/module/phase | `batch_state/api_usage/**` cost records | No route cache; live usage reads | `cost.html`, `index.html` | Duplicate mount: `/api/analytics/cost` and `/api/cost` | Low | Keep `/api/analytics/cost` canonical for UI; retain `/api/cost` as compatibility alias. |
| `/api/wiki/*` | Wiki compilation status, quality gates, sources inventory | Wiki progress DB/state, wiki markdown files, `data/sources.db` | Uses shared TTL cache for selected expensive aggregate reads; article detail reads file bodies | `wiki.html`, `index.html` | Complements state summary published/wiki status | Low/medium | Keep. Contract should distinguish aggregate status from article body detail. |
| `/api/images/*`, `/api/rag/*`, `/images/*` | Textbook image explorer, annotations, RAG search, page rendering | `data/textbook_images/**`, `data/textbooks/**`, annotation JSONL, Qdrant/RAG collections | Lazy in-memory image index; PDF pool and render LRU cache; `/api/images/reload` resets index | `image-explorer.html`; `images.html` redirects there | RAG search overlaps external MCP/source tools but UI-specific | Low | Keep. Preserve `images.html` as a redirect alias, not a full page. |
| `/api/admin/*` | Local maintenance: health, backups, disk, broker vacuum, logs, Qdrant collection checks | Qdrant snapshots/storage, broker DB, logs, data directories | No route cache; live local maintenance operations | `admin.html` | None; operational only | Medium because POST/DELETE mutates local state | Keep local-only; contract must mark mutating endpoints. |
| `/api/consultation/*` | Template proposal queue/history/metrics | Consultation queue/history files | No route cache; live filesystem reads/writes where method is POST | `consultation.html`, `index.html` | None | Low | Keep. |
| `/api/decisions/*`, `/api/state/governance` | Decision/ADR governance | `docs/decisions/**`, ADR docs | No route cache in decision router; governance summary is cached through orient only | Docs, agents, orient | Related but distinct: decisions are detailed, governance is aggregate | Low | Keep. |
| `/api/issues/map` | Open issue map with categories | `gh issue list` output | No route cache in handler; `/api/orient` wraps issue collection with a 120s cache and short timeout | Agents, issue hygiene | Overlaps `/api/orient.issues` | Medium if GitHub times out; handler returns best effort | Keep. |
| `/api/rules`, `/api/session/current`, `/api/state/manifest`, `/api/orient` | Agent cold-start coordination | Deployed rules, session-state files, git/GH/runtime/wiki/health probes | Manifest hashes rules/session; rules/session support cache semantics; orient has section TTLs and `?fresh=true` | Agents, `orient.html`, session-start tooling | Replaces direct file spelunking | Low | Keep; document as cold-start source of truth. |
| `/api/site/*`, `/api/health`, `/api/config`, `/api/git/*`, `/api/telemetry/*`, `/api/discussions/active`, `/api/batch/*` | Site reachability, server config, git hygiene, telemetry, discussions, legacy batch state | Public site probe/GH deployments, config constants, git, transcript timing records, broker, batch_state files | Mostly no route cache; orient may cache summaries of some sections | Agents, `orient.html`, `index.html`, docs | `/api/batch/*` overlaps delegate/build/comms and is older | Low/medium | Keep. Treat `/api/batch/*` as compatibility until orchestration clients migrate. |
| `/ws/batch` | Legacy batch heartbeat stream | API process heartbeat loop | Sends `{"type":"heartbeat"}` every 5s while connected; no persisted state or cache | Legacy live monitors | Overlaps newer polling dashboards | Low/medium because it is invisible in OpenAPI | Keep with explicit WebSocket contract until websocket consumers are audited. |
| Static: `/{path}`, `/docs`, `/openapi.json` | Static dashboards and FastAPI generated docs | `dashboards/**`, FastAPI app | Browser/static caching only; no API freshness contract | Humans | Catch-all can hide missing dashboard files if links are stale | Medium | Keep. Dashboard page contracts must scan literal files, not only FastAPI route list. |

## Page Matrix

| Page | Purpose | Source of truth | Cache / freshness behavior | Consumers | Overlap / duplication | Risk | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/` (`dashboards/index.html`) | Operations launchpad and aggregate cards | API fanout: dashboard overview, state summary, orient, runtime, delegate, wiki, cost | Client fetches live endpoints with 5s timeout; state summary called with `fresh=true` | Humans | Links to every major dashboard | Low after #2790 | Keep. |
| `/progress.html` | Canonical visual project progress | `/api/state/summary?fresh=true`, `/api/state/pipeline-versions?fresh=true`, `/api/state/pipeline/{track}?fresh=true` | Explicit fresh requests and freshness banner | Humans | Overlaps audit/curriculum but owns current progress | Low after #2790 | Keep canonical. |
| `/audit-dashboard.html` | QA gate and audit drill-down | `/api/dashboard/overview`, `/api/dashboard/track/*`, `/api/dashboard/module/*`, `/api/state/module/*` | Dashboard helper caches 30/60s; state module is live | Humans | Overlaps progress counts | Medium | Keep for QA details; contract says progress/state are canonical for counts. |
| `/quality.html` | Fix queue across research/reviews/issues/weak points | `/api/state/research-coverage`, `/api/state/review-coverage`, `/api/state/issues`, `/api/state/weak-points` | State coverage TTLs where configured; weak-points 60s cache | Humans | Complements progress | Low | Keep. |
| `/track-health.html` | One-track build/audit/enrichment/review health | `/api/state/build-status`, `/api/state/enrichment-status`, `/api/state/track-health/*`, `/api/state/module/*`, `/api/comms/by-module/*` | Build-status 15/30s caches; enrichment 120s; track-health 30s | Humans | Overlaps progress | Low | Keep. |
| `/curriculum-dashboard.html` | Plan/meta/module inspection | `/api/dashboard/overview`, `/api/dashboard/track/*`, `/api/dashboard/module/*` | Dashboard helper caches 30/60s | Humans | Overlaps audit/progress | Medium | Keep as inspection workflow, not canonical progress. |
| `/channels.html` | Canonical channel bridge UI | `/api/comms/channels*` | Live broker reads; client refresh/deeplink state | Humans/agents | Replaces legacy comms | Low | Keep. |
| `/comms.html` | Legacy direct-message, zombie, batch progress UI | Deprecated legacy comms routes plus build events and broker health | Live broker/process reads | Humans if needed | Duplicates channels for chat | Medium | Explicitly retain as legacy operations page until old CLI/users migrate. |
| `/delegate.html` | Delegated task observability | `/api/delegate/tasks*` | Live task JSON/process reads | Humans | Complements comms/build-events | Low | Keep. |
| `/runtime.html` | Agent runtime, usage, auth/headroom | `/api/runtime/*` | Live file/env reads with 5s client timeout | Humans | Complements routing/cost | Low | Keep. |
| `/routing.html` | Agent routing guidance | Currently static stale snapshot | Manual refresh only | Humans via index card | Duplicates runtime, delegate, cost, routing-budget | High | Refactor in this slice to live `/api/state/routing-budget` + runtime/delegate data. |
| `/cost.html` | Cost reports | `/api/analytics/cost*` | Live cost record reads | Humans | Complements routing/runtime | Low | Keep. |
| `/build-events.html` | Build dispatch event timeline | `/api/build/events/*` | Live capped filesystem scans | Humans | Complements comms/delegate | Low | Keep. |
| `/wiki.html` | Wiki build/quality/source overview | `/api/wiki/*` | Wiki router caches selected aggregates | Humans | Complements state published/wiki signals | Low | Keep. |
| `/artifacts/` and `/artifacts.html` | Artifact/report browser | `/api/artifacts/html`, static file serving | Live metadata scan | Humans | Links all ops pages | Low | Keep. |
| `/image-explorer.html` | Textbook image/RAG annotation UI | `/api/images/*`, `/api/rag/*`, `/images/*` | Lazy image index and render LRU | Humans | None | Low | Keep. |
| `/images.html` | Redirect alias | No API source; meta refresh to `/image-explorer.html` | Static redirect | Legacy links | Duplicate alias | Low | Retain as redirect-only alias. |
| `/admin.html` | Local maintenance | `/api/admin/*` | Live local operations | Humans | None | Medium due to mutating POST/DELETE actions | Keep. |
| `/consultation.html` | Template proposal queue/history | `/api/consultation/*`, `/api/config` | Live queue/history reads | Humans | None | Low | Keep. |
| `/orient.html` | Cold-start/session snapshot | `/api/orient`, `/api/discussions/active` | Orient section TTLs; client auto-refresh | Humans/agents | Mirrors agent bootstrap | Low | Keep. |

## Smallest Coherent Implementation Slice

1. Add a route/page contract registry and serve it as
   `GET /api/contracts/routes`.
   - It should declare purpose, source of truth, freshness/cache behavior,
     consumers, overlap, risk, and recommendation for endpoint families and
     dashboard pages.
   - Tests should fail if a public FastAPI HTTP route, public WebSocket route,
     or literal dashboard page has no contract entry.
   - Dashboard-page tests must scan `dashboards/*.html`; FastAPI's catch-all
     route does not enumerate individual dashboard files.
2. Refactor `dashboards/routing.html` from a stale static snapshot to a live
   dashboard page that reads:
   - `/api/state/routing-budget`
   - `/api/runtime/agents`
   - `/api/runtime/usage?days=7`
   - `/api/delegate/tasks?limit=100`
3. Update dashboard tests so `routing.html` is explicitly retained as a live
   page and no longer contains the manual-refresh/static-snapshot warning.

This slice is intentionally not a broad data-path rewrite. It makes contracts
visible and testable, removes the highest-risk stale dashboard surface, and
leaves future consolidation decisions backed by a route/page matrix.

## Deferred Follow-Ups

- Decide whether to remove `dashboards/images.html` after external/legacy link
  audit. It is harmless as a redirect alias.
- Migrate or remove legacy direct-message endpoints after old `ask-*` and
  `comms.html` consumers are gone.
- Consider deprecating `/api/cost/*` in favor of `/api/analytics/cost/*` once
  no scripts depend on the shorter alias.
- Consider folding `/api/gold/*` and `/api/agent/*` into `/api/state` and
  `/api/artifacts` after agent consumer audit.
