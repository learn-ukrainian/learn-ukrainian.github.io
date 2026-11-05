"""Machine-readable Monitor API and dashboard contracts.

The registry is intentionally family-based: most Monitor endpoints belong to
router families with the same source and freshness behavior. Tests verify that
every public FastAPI route and literal dashboard HTML page matches a contract.

The declarations here cover the machinery routes and pages. The product
contribution adds its own (``scripts.project_api.route_contracts``), and the
lookups and ``/api/contracts/routes`` read both: machinery first, then product
(Monitor split, C-4687).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, Request

from .monitor_context import MonitorContext, get_ctx, resolve_context
from .product_contribution import ProductContribution, installed_product

ContractKind = Literal["http", "websocket"]
MatchType = Literal["exact", "prefix"]
RouteLocality = Literal["host_affine", "cluster_authoritative", "mixed"]


@dataclass(frozen=True)
class RouteContract:
    pattern: str
    match: MatchType
    kind: ContractKind
    purpose: str
    source_of_truth: str
    freshness: str
    consumers: tuple[str, ...]
    overlap: str
    stale_risk: str
    recommendation: str
    locality: RouteLocality = "host_affine"
    mutates: bool = False
    replacement: str | None = None
    response_schema_version: str | None = None

    def matches(self, path: str, kind: ContractKind) -> bool:
        if self.kind != kind:
            return False
        if self.match == "exact":
            return path == self.pattern
        prefix = self.pattern.rstrip("/")
        return path == prefix or path.startswith(f"{prefix}/")

    @property
    def specificity(self) -> tuple[int, int]:
        return (1 if self.match == "exact" else 0, len(self.pattern))

    def to_dict(self) -> dict:
        data = asdict(self)
        data["consumers"] = list(self.consumers)
        return data


@dataclass(frozen=True)
class PageContract:
    file: str
    url: str
    purpose: str
    source_of_truth: str
    freshness: str
    consumers: tuple[str, ...]
    overlap: str
    stale_risk: str
    recommendation: str

    def to_dict(self) -> dict:
        data = asdict(self)
        data["consumers"] = list(self.consumers)
        return data


ROUTE_CONTRACTS: tuple[RouteContract, ...] = (
    RouteContract(
        "/api/epics/v1",
        "prefix",
        "http",
        "Remote TTL-fenced epic registry, lease claim, heartbeat, handoff, release, and bounded digest projection.",
        "API-host SessionStreamStore seeded at process start from the release snapshot's scripts/config/issue_streams.yaml; no PID probe and no GitHub enrichment.",
        "Registry identity is fresh at the last successful API restart; lease state and bounded digest are read per request.",
        ("remote orchestrators", "launchers", "Monitor"),
        "Complements local session-supervisor hooks; it is the remote authority for v1 epic leases and a snapshot projection for registry identity.",
        "high if callers treat lease: null as never claimed, or treat registry status as live parity rather than last-restart snapshot state",
        "keep as the M2 registry-seeded remote lifecycle contract",
        locality="cluster_authoritative",
        mutates=True,
    ),
    RouteContract(
        "/api/session-streams",
        "prefix",
        "http",
        "Read-only session-stream health, status, digest, dual-write, and projection-drift surfaces.",
        "SessionStreamStore plus bounded legacy-handoff inventory and projection receipts.",
        "Health and inventory are generated per request; store schema versions are read from the configured database.",
        ("agents", "Monitor", "session-stream consumers"),
        "Complements the remote /api/epics/v1 lifecycle projection; it never exposes filesystem paths.",
        "medium if callers treat local inventory as remote lease authority",
        "keep as the path-free session-stream observability contract",
        locality="mixed",
        response_schema_version="session-streams.v2",
    ),
    RouteContract(
        "/api/ops/v1/test-slots",
        "exact",
        "http",
        "Host test-slot pool (#10662): slots in use, holders by task, the FIFO queue with positions, and wait times.",
        "This host's private test-slot pool directory: flock-live holder records and queue tickets "
        "(scripts/common/test_slots.py).",
        "Read live per request; flock decides liveness, so a crashed holder disappears at once. No cache.",
        ("operators", "dispatch", "agents"),
        "Same data as `python -m scripts.common.test_slots status --json`; dispatch admission reads the queue depth.",
        "low; read-only and path-free",
        "keep",
        response_schema_version="test-slots.status.v1",
    ),
    RouteContract(
        "/api/ops/v1/load-samples",
        "exact",
        "http",
        "Bounded high-load attribution: CPU command names and test-slot holders (#10715).",
        "Ignored batch_state load-samples ring on this Monitor host.",
        "Existing Monitor periodic collector; above LU_LOAD_SAMPLE_THRESHOLD, at most once per 60 seconds; last 500 samples.",
        ("operators", "agents"),
        "Complements the live test-slot status; CPU shares use one CPU as 100%.",
        "low; read-only, command names only, no process arguments or paths",
        "keep",
        response_schema_version="load-samples.v1",
    ),
    RouteContract(
        "/api/contracts/routes",
        "exact",
        "http",
        "Machine-readable Monitor route and dashboard contract registry.",
        "This module's ROUTE_CONTRACTS and PAGE_CONTRACTS declarations.",
        "Generated per request; no route cache.",
        ("tests", "agents", "docs"),
        "Documents every other local Monitor endpoint.",
        "low",
        "keep",
    ),
    RouteContract(
        "/api/state/github-budget",
        "exact",
        "http",
        "Cached health probe of the authenticated GitHub GraphQL primary rate limit.",
        "Shared GitHub client REST `rate_limit` read of `resources.graphql`.",
        "In-process 60-second TTL cache with single-flight coalescing; probe failures report exhausted=null.",
        ("agents", "Monitor", "operators"),
        "Agents can read the shared observation instead of spending separate GraphQL calls.",
        "medium if a stale response is treated as the current budget after its 60-second cache window",
        "read this endpoint for a lightweight shared GraphQL health signal",
        response_schema_version="github-budget.v1",
    ),
    RouteContract(
        "/artifacts",
        "prefix",
        "http",
        "Human artifact browser and approved documentation artifact serving.",
        "docs, audit, and other approved artifact roots.",
        "No route cache; serves artifacts.html for browser requests and JSON/file listings on demand.",
        ("artifacts.html", "humans"),
        "Shares artifact metadata with /api/artifacts/html.",
        "low",
        "keep",
    ),
    RouteContract(
        "/files",
        "prefix",
        "http",
        "Approved documentation artifact serving alias.",
        "docs, audit, and other approved artifact roots.",
        "No route cache; live filesystem serving with extension/root allowlists.",
        ("humans", "agents"),
        "Alias of /artifacts file serving without the browser page default.",
        "low",
        "keep",
    ),
    RouteContract(
        "/api/fleet/operations",
        "exact",
        "http",
        "Read-only broker, live-process, zombie, and batch-progress projection for Fleet Observer operations panels.",
        "Existing legacy broker SQLite, PID, and bounded batch/log read models, sanitized into aggregate metadata.",
        "Generated per request; broker SQLite is opened with mode=ro and query_only, and item lists are capped at 50.",
        ("fleet.html", "operators", "agents"),
        "Canonical visible home for unique diagnostics formerly associated with the retired Broker Ops page; legacy /api/comms/* routes remain unchanged.",
        "medium if missing stores are mistaken for zero activity or sanitized aggregates are treated as control-plane authority",
        "keep as the read-only canonical operations projection; do not use it to mutate, clean, expire, or retire routes",
        locality="mixed",
    ),
    RouteContract(
        "/api/fleet/agents",
        "exact",
        "http",
        "Configured and durable fleet agent endpoint inventory with configuration secrets omitted.",
        "Endpoint registry (scripts/config) plus durable agent_endpoints rows from the fleet-comms v1 SQLite read model.",
        "Generated per request; every fleet route opens the durable plane read-only. No response cache.",
        ("fleet.html", "operators", "agents"),
        "Specific member of the /api/fleet observer family; /api/fleet/endpoints serves the same handler as an alias.",
        "low — read-only inventory; agents missing from the durable plane are reported via durable_registration=false",
        "keep as the exact agent-endpoint contract beside the /api/fleet prefix family",
        locality="cluster_authoritative",
        mutates=False,
    ),
    RouteContract(
        "/api/fleet/v1",
        "prefix",
        "http",
        "Read-only fleet board with now, epics, agents, roster, budget, PRs, alerts, stats, links, and schema inventory.",
        "Configured local roster and harness snapshots, in-process delegate and occupancy collectors, and endpoint-specific configured files, directories, and bounded HTTP reads.",
        "Generated per request; snapshot timestamps and collector results report source age and explicit ok, stale, unavailable, or not_configured status.",
        ("operators", "agents", "fleet board consumers"),
        "Distinct from the durable fleet-comms observer under /api/fleet; board snapshots and local activity are projections, not plane authority.",
        "high if missing or stale snapshots are treated as live fleet state or unread sources are reported healthy",
        "keep as the host-local, read-only fleet board contract",
        locality="host_affine",
        response_schema_version="fleet.v1",
    ),
    RouteContract(
        "/api/fleet",
        "prefix",
        "http",
        "Unified read-only observer for durable fleet-comms requests, authority queue jobs, messages, discussions, ACP rounds, formal reviews, endpoints, migrations, dead letters, provenance, and operations health.",
        "Fleet-comms v1 SQLite read models, endpoint registry metadata, sanitized runtime/ACP projections, and sanitized legacy operations read models.",
        "No response cache; every route opens the durable plane in SQLite read-only mode. Lists have deterministic order and bounded limit/offset pages; inline bodies are preview-only, redacted, and never fetch artifact blobs.",
        ("fleet.html", "operators", "agents"),
        "Consolidates observation previously spread across comms, runtime, ACP, and session-stream pages; legacy pages remain during the pre-flip soak.",
        "medium if a consumer mistakes the observer for plane authority or relies on an absent optional table as evidence of no historical work",
        "keep as the pre-flip consolidated observer; file handoffs remain authoritative and all fleet routes are read-only",
        locality="cluster_authoritative",
        response_schema_version="comms.v2",
    ),
    RouteContract(
        "/api/comms/messages",
        "exact",
        "http",
        "Deprecated legacy direct-message list.",
        "SQLite message broker.",
        "No route cache; live broker reads.",
        ("legacy external callers",),
        "Replaced by channel message endpoints.",
        "medium",
        "deprecated; migrate to /api/comms/channels/{name}/messages (NOTE: compat_keep gated by #6106 and legacy telemetry)",
        replacement="/api/comms/channels/{name}/messages",
    ),
    RouteContract(
        "/api/comms/conversations",
        "exact",
        "http",
        "Deprecated legacy direct-message conversation list.",
        "SQLite message broker.",
        "No route cache; live broker reads.",
        ("legacy external callers",),
        "Replaced by channel threads.",
        "medium",
        "deprecated; migrate to /api/comms/channels/{name}/threads/{thread_id} (NOTE: compat_keep gated by #6106 and legacy telemetry)",
        replacement="/api/comms/channels/{name}/threads/{thread_id}",
    ),
    RouteContract(
        "/api/comms/conversation",
        "prefix",
        "http",
        "Deprecated legacy direct-message conversation detail.",
        "SQLite message broker.",
        "No route cache; live broker reads.",
        ("legacy external callers",),
        "Replaced by channel threads.",
        "medium",
        "deprecated; migrate to /api/comms/channels/{name}/threads/{thread_id} (NOTE: compat_keep gated by #6106 and legacy telemetry)",
        replacement="/api/comms/channels/{name}/threads/{thread_id}",
    ),
    RouteContract(
        "/api/comms/live-activity",
        "exact",
        "http",
        "Deprecated legacy live activity summary.",
        "SQLite broker and process probes.",
        "No route cache; live broker/process reads.",
        ("legacy docs",),
        "Replaced by channel activity and delegate/build event endpoints.",
        "medium",
        "deprecated; migrate to /api/comms/agent-activity and /api/delegate/active (NOTE: compat_keep gated by #6106 and legacy telemetry)",
        replacement="/api/comms/agent-activity",
    ),
    RouteContract(
        "/api/comms/send",
        "exact",
        "http",
        "Deprecated legacy direct-message send endpoint.",
        "SQLite message broker.",
        "No route cache; the retired POST returns 410 and does not mutate broker state.",
        ("legacy external callers",),
        "Replaced by channel post endpoint.",
        "medium",
        "deprecated; migrate to /api/comms/channels/{name}/post (NOTE: compat_keep gated by #6106 and legacy telemetry)",
        replacement="/api/comms/channels/{name}/post",
    ),
    RouteContract(
        "/api/comms",
        "prefix",
        "http",
        "Canonical channel bridge plus broker/process health, batch progress, zombies, acknowledgements, and module-linked messages.",
        "SQLite message broker, delivery tables, process probes, and build state.",
        "No route cache; live broker/process reads. POST routes mutate broker/message state.",
        ("progress.html", "index.html", "agents"),
        "Canonical channels replace legacy direct-message routes; status overlaps delegate/build events.",
        "low/medium",
        "keep",
        locality="mixed",
        response_schema_version="comms.v2",
    ),
    RouteContract(
        "/api/delegate",
        "prefix",
        "http",
        "Delegated task list, active task count, and task result detail.",
        "batch_state/tasks/*.json, process liveness, and task result files.",
        "No route cache; live filesystem/process reads.",
        ("delegate.html", "index.html", "agents"),
        "Complements /api/orient.delegate and /api/build/events.",
        "low",
        "keep",
    ),
    RouteContract(
        "/api/coordination",
        "prefix",
        "http",
        "Parallel-agent coordination ledger summary, active task list, and task detail.",
        "orchestration/agent-ledger/tasks/*.json written by scripts/orchestration/agent_ledger.py.",
        "No route cache; live filesystem reads from the local coordination ledger.",
        ("agents", "orchestrator", "future dashboards"),
        "Complements /api/delegate process state with explicit task ownership and review metadata.",
        "low while JSON ledger is healthy; invalid task files surface as errors instead of silent stale state",
        "keep",
    ),
    RouteContract(
        "/api/worktrees",
        "exact",
        "http",
        "Active git worktree registry.",
        "git worktree list --porcelain, per-worktree git status, and git log -1.",
        "No route cache; each git subprocess has a bounded timeout.",
        ("agents", "cold-start tooling", "worktree hygiene"),
        "Complements /api/git/hygiene and /api/git/cleanup.",
        "low; failures degrade to empty/error payload",
        "keep",
    ),
    RouteContract(
        "/api/runtime/routing-assignments",
        "exact",
        "http",
        "Body-free recent routing decisions with initiator, requested target, selected route, outcome, and lifecycle evidence.",
        "Fleet Comms routing-reservation decision ledger read through its read-only authority projection.",
        "Generated per request from at most ten times the requested event limit, then aggregated and capped to 1-100 recent assignments; quota fields are decision-time snapshots, not live provider health.",
        ("runtime.html", "agents", "orchestrators", "operators"),
        "Complements /api/state/routing-budget and CodexBar health/quota signals; it does not expose all-time routing weights or choose a route.",
        "medium if the bounded loaded window is treated as all-time distribution or stale activity as provider-liveness proof",
        "keep as the canonical read-only routing-decision observer",
        locality="cluster_authoritative",
    ),
    RouteContract(
        "/api/runtime",
        "prefix",
        "http",
        "Agent runtime inventory, usage, ACPX shadow evidence, ACP conversation observability, default-model quota headroom, recent calls, auth mode, and cached transport health.",
        "Runtime config, usage JSONL, the fleet-comms ACP SQLite store, sanitized probe receipt, environment presence booleans, and OAuth credential presence.",
        "No route cache; live file/env/SQLite reads. ACPX is aggregate evidence only and never launches a probe; ACP transcript bodies require a direct loopback peer and host and are returned no-store; transport health carries its own receipt expiry; auth reports booleans/source names only, never secret values.",
        ("runtime.html", "acp.html", "routing.html", "index.html", "agents"),
        "Usage complements /api/state/routing-budget and cost endpoints.",
        "medium; transcript bodies are restricted to the local conversation reader",
        "keep",
        locality="mixed",
    ),
    RouteContract(
        "/api/state/routing-budget",
        "exact",
        "http",
        "Per-agent soft-cap burn and routing recommendation.",
        "scripts/config/agent_budgets.yaml, cost records, delegate in-flight state, and the process-local CodexBar snapshot.",
        "No route cache for ledger/runtime; CodexBar allotment is a 12-minute TTL snapshot refreshed in the background. HTTP ?fresh_codexbar=true kicks a refresh and still returns cache/LKG — it never waits for the CLI.",
        ("routing.html", "agents"),
        "Overlaps runtime usage and cost summaries but adds routing recommendation.",
        "low",
        "keep canonical for routing guidance",
    ),
    RouteContract(
        "/api/issues/map",
        "exact",
        "http",
        "Open issue map grouped by category.",
        "gh issue list output.",
        "No route cache in handler; /api/orient wraps issue collection with a 120s cache and short timeout.",
        ("agents", "issue hygiene"),
        "Overlaps /api/orient.issues.",
        "medium if GitHub is slow or unavailable",
        "keep best-effort",
    ),
    RouteContract(
        "/api/issues/streams",
        "exact",
        "http",
        "Issue-stream hygiene report (#4708): orphans without a stream epic, multi-homed, pending native links.",
        "batch_state/issue_stream_audit.json auditor cache plus a runtime-only refresh state sidecar; ?fresh=true schedules one detached worker.",
        "Cache TTL 3600s with a 7-day stale fallback; every response reports privacy-safe scheduled/running/terminal refresh state.",
        ("agents", "issue hygiene", "orchestrators"),
        "Complements /api/issues/map (label categories) with stream-epic membership.",
        "low — nonblocking single-flight refresh records allowlisted failure state without raw errors",
        "keep best-effort",
    ),
    RouteContract(
        "/api/rules",
        "exact",
        "http",
        "Condensed agent rule set for cold start.",
        "Deployed rule/source markdown files.",
        "Hash/ETag semantics when telemetry footer is disabled; otherwise generated per request.",
        ("agents", "docs"),
        "Replaces direct rule-file reads at cold start.",
        "low",
        "keep cold-start source of truth",
    ),
    RouteContract(
        "/api/session/current",
        "exact",
        "http",
        "Agent-specific current session handoff.",
        "docs/session-state/current.md router and current.<agent>.md handoff files.",
        "Hash/ETag semantics when telemetry footer is disabled; generated per request otherwise.",
        ("agents", "docs"),
        "Replaces direct session-state file spelunking.",
        "low",
        "keep cold-start source of truth",
    ),
    RouteContract(
        "/api/orient",
        "exact",
        "http",
        "One-shot agent and dashboard orientation snapshot.",
        "Git, GitHub issues, pipeline state, runtime files, delegate state, broker, rollover registry, wiki, governance, health, and session hints.",
        "Per-section TTLs in main.py; ?fresh=true invalidates orient cache entries.",
        ("orient.html", "index.html", "agents"),
        "Aggregates many other API sections.",
        "low/medium when upstream collectors degrade",
        "keep cold-start source of truth",
        locality="mixed",
        response_schema_version="orient.v2",
    ),
    RouteContract(
        "/api/rollovers",
        "exact",
        "http",
        "Read-only fleet rollover audit and exact selector projection.",
        "Versioned registry records under .agent/thread-rollover-registry/v1/.",
        "Generated per request; no mutation path is exposed over HTTP.",
        ("agents", "monitor client", "orchestrators"),
        "Compact actionable entries are also exposed through /api/orient.",
        "low — corrupt records are isolated and returned as explicit errors",
        "keep as the canonical rollover observability surface",
    ),
    RouteContract(
        "/api/knowledge",
        "prefix",
        "http",
        "ADR-011 bounded Project Research Registry discovery: task-scoped pointer "
        "manifest and per-record compact digest bodies.",
        "docs/references/research-registry.yaml + docs/references/research-digests/** "
        "via the P1 validator primitives (scripts/audit/check_research_registry.py).",
        "No route cache; per-request deterministic registry load. Strong ETags: a "
        "context-scoped ETag on /manifest and the P1 content_hash on /record/{id}. "
        "Registry-serving endpoints obey the research_registry kill switch; /find and "
        "consumption metadata remain ungated.",
        ("agents", "dispatch", "cold-start tooling"),
        "Pointer index for /api/state/manifest's research component; bodies never enter cold start.",
        "low; disabled or a failed load degrades to an empty/disabled projection",
        "keep as the research discovery surface",
    ),
    RouteContract(
        "/api/state/manifest",
        "exact",
        "http",
        "Tiny cold-start manifest with hashes and URLs.",
        "Rules/session hash helpers plus static endpoint metadata.",
        "Generated per request; rules/session hashes let agents skip unchanged payloads.",
        ("agents", "monitor client"),
        "Index for /api/rules, /api/session/current, /api/orient, comms inbox/activity.",
        "low",
        "keep cold-start source of truth",
    ),
    RouteContract(
        "/api/agent-monitor/status",
        "exact",
        "http",
        "Aggregate host-local resource, process, and capacity reservation summary.",
        "psutil host/process metrics and aggregate agent-monitor lease counts.",
        "Computed per request; dead and expired leases reconciled at read time; no response cache.",
        ("runtime.html", "agent launchers", "orchestrators", "tests"),
        "Complements /api/runtime provider usage and /api/delegate task telemetry.",
        "medium if launcher heartbeat coverage is incomplete",
        "keep as canonical aggregate host-capacity summary",
    ),
    RouteContract(
        "/api/agent-monitor/status/details",
        "exact",
        "http",
        "Detailed host capacity status including active lease process listings (requires auth).",
        "psutil host/process metrics and detailed transactional agent-monitor lease store.",
        "Computed per request; dead and expired leases reconciled at read time; no response cache.",
        ("agent launchers", "orchestrators", "tests"),
        "Complements /api/agent-monitor/status for authorized detailed process telemetry.",
        "medium if launcher heartbeat coverage is incomplete",
        "keep as canonical detailed host-capacity snapshot",
    ),
    RouteContract(
        "/api/agent-monitor/preflight",
        "exact",
        "http",
        "Advisory read-only capacity check evaluating host allocatable headroom.",
        "Configured capacity policy, live psutil memory, and active lease reservations.",
        "Evaluated per request; no cache.",
        ("agent launchers", "orchestrators", "tests"),
        "Memory admission check prior to atomic lease registration.",
        "low",
        "keep advisory preflight",
        mutates=False,
    ),
    RouteContract(
        "/api/agent-monitor/register",
        "exact",
        "http",
        "Activates an admitted reservation for an identified agent process.",
        "Pending reservation plus verified PID and process creation time.",
        "Transactional mutation; immediately visible.",
        ("agent launchers", "tests"),
        "Complements task ownership in /api/delegate and /api/coordination.",
        "medium if process identity is not verified",
        "keep",
        mutates=True,
    ),
    RouteContract(
        "/api/agent-monitor/heartbeat",
        "exact",
        "http",
        "Renews one live agent lease.",
        "Existing lease identity and verified process liveness.",
        "Transactional TTL renewal; immediately visible.",
        ("agent launchers", "tests"),
        "None.",
        "low with bounded TTL and identity validation",
        "keep",
        mutates=True,
    ),
    RouteContract(
        "/api/agent-monitor/release",
        "exact",
        "http",
        "Explicitly releases one agent capacity reservation.",
        "Existing lease identity.",
        "Transactional removal; immediately visible.",
        ("agent launchers", "tests"),
        "Expired/dead-lease reconciliation is the fallback.",
        "low",
        "keep",
        mutates=True,
    ),
    RouteContract(
        "/api/git",
        "prefix",
        "http",
        "Git hygiene and cleanup dry-run reporting.",
        "Local git branches, worktrees, and batch_state task metadata.",
        "No route cache; live git/filesystem reads.",
        ("agents", "docs"),
        "Complements /api/worktrees.",
        "low/medium",
        "keep read-only cleanup planning",
    ),
    RouteContract(
        "/api/telemetry",
        "prefix",
        "http",
        "Tool timing, module-build token, and body-free legacy HTTP/one-shot bridge telemetry ingest/readback.",
        "Telemetry SQLite state used by Monitor instrumentation and module-build PR reporting.",
        "No route cache; POST mutates telemetry stores, GET reads current telemetry state. Legacy HTTP and one-shot bridge usage is retained only as hourly allowlisted aggregates for 90 days.",
        ("agents", "runtime tooling"),
        "Complements optional telemetry footer, runtime usage logs, analytics cost summaries, and #6106 legacy comms retirement evidence.",
        "low",
        "keep",
    ),
    RouteContract(
        "/api/discussions/active",
        "exact",
        "http",
        "Active multi-agent discussion snapshot.",
        "Channel bridge SQLite messages and discussion state.",
        "No route cache; live broker reads.",
        ("orient.html",),
        "Complements channel message endpoints.",
        "low",
        "keep",
        locality="mixed",
    ),
    RouteContract(
        "/api/health",
        "exact",
        "http",
        "API process health, uptime, resilience counters, and loopback instance identity (opaque host id, checkout_sha/git_sha alias, serving_sha, serving_mode).",
        "API process state, LIVE_REPO_ROOT git HEAD, PROJECT_ROOT release layout, and resilience middleware counters.",
        "Generated per request; no route cache.",
        ("health checks", "tests", "agents"),
        "Related to /api/admin/health and /api/orient.health.",
        "low",
        "keep",
        locality="host_affine",
    ),
    RouteContract(
        "/api/cluster/readiness",
        "exact",
        "http",
        "Cluster readiness: reports storage-seam authority and ability to open authority stores for cluster-authoritative reads without claiming multi-host HA.",
        "scripts/control_plane/storage.py authority resolution and authority store connectivity.",
        "Evaluated per request; no cache.",
        ("agents", "orchestrators", "monitor client", "tests"),
        "Complements host-affine /api/health; distinct cluster-authoritative readiness contract.",
        "low",
        "keep as canonical cluster readiness endpoint",
        locality="cluster_authoritative",
    ),
    RouteContract(
        "/api/work",
        "prefix",
        "http",
        "Read-only Work control-plane projection: normalized public attention list, source envelopes, open PR rows plus bounded merged history qualified only by GitHub merged_at, and optional private-source capability seam.",
        "GitHub open issue/PR list enumerations (cap 1000), public /api/issues/streams, and frozen class-4 summaries (/api/delegate/active, /api/delegate/tasks, /api/fleet/reviews).",
        "Warm projection cache ~30s with cache_age_s; warm target <=2s; typed degradation within 5s; never proxies private adapters.",
        ("work.html", "operators", "agents"),
        "Joins existing GH list + streams + class-4 summaries; does not replace GitHub or those sources as authority.",
        "medium if GitHub is slow or a class-4 section degrades independently",
        "keep as the Work foundation surface; FOUNDATION_COMPLETE only",
    ),
    RouteContract(
        "/api/occupancy",
        "exact",
        "http",
        "Opaque host occupancy: load fields, sanitized occupants {kind, agent, task_id, epic, optional instance_id}, burn_state in {active, idle, unknown}, top-level attention items empty_host_underused:<host_id> and empty_host_unknown_capacity:<host_id>; burn_sources has exactly atlas_job, driver, foundry, service, and observer, each with state in {active, clear, unknown} and non-negative observation_age_s. Default glance always includes host-teacher and observer-only mac-operator; host-job is a retired batch-host role and never appears, even if a MONITOR_OCCUPANCY_HOST_IDS mapping still points a canonical alias at it; empty-map Linux API fills host-teacher in-process; live observer heartbeats merge into that Mac row, and legacy cloud-observer stays presence-gated with honest presence age.",
        "In-process atlas-jobs load cache plus local atlas-jobs registry, local session-stream driver leases, optional occupancy markers, and the in-process observer presence store keyed by (host, agent, instance); host keys from MONITOR_OCCUPANCY_HOST_IDS (or empty-map API self-fill).",
        "Stale-while-revalidate via the existing HOST_LOAD_FRESH_S and HOST_LOAD_MAX_STALE_S load-cache constants; local marker TTL is DEFAULT_MARKER_TTL_S (15 minutes); never probes SSH on the request path.",
        ("operators", "dispatch", "tests", "qa-engineer", "grok-bot"),
        "Reuses GET /api/atlas-jobs/load cache; does not add a second probe board. Observer presence is not a RAM lease.",
        "low",
        "keep",
        mutates=False,
    ),
    RouteContract(
        "/api/observer/presence",
        "exact",
        "http",
        "Loopback-only observer heartbeat: grok-bot/QA/Cursor/Codex/Claude report current task or notebook session without a RAM lease; optional opaque host, instance, and bounded context counters are validated.",
        "In-process TTL store keyed by (opaque host, observer agent, instance); occupancy partitions live rows and the fresh matching instance can supply notebook-presence telemetry.",
        "Upsert immediately; row expires after 15 minutes without a heartbeat; Monitor restart drops the store.",
        ("qa-engineer", "grok-bot", "cursor", "codex", "tests"),
        "Not a fleet seat, not POST /api/agent-monitor/register, and never writes fleet-comms.",
        "low with loopback-only mutation and a short TTL",
        "keep",
        mutates=True,
    ),
    RouteContract(
        "/api/fleet/projects/v1",
        "exact",
        "http",
        "Per opaque host: primary checkout vs origin/main, worktree count, service serving SHA drift (fresh|stale|unknown), and attention items.",
        "In-process live collection on the API host plus loopback-pushed TTL reports from remote reporters keyed by MONITOR_OCCUPANCY_HOST_IDS and mac-operator.",
        "Remote reports expire after 15 minutes without a heartbeat; origin_main_age_s > 3600 degrades drift to unknown; API host is always fresh in-process.",
        ("operators", "dispatch", "tests", "fleet.html"),
        "Complements GET /api/occupancy; does not probe SSH on the request path.",
        "low",
        "keep",
        locality="mixed",
        mutates=False,
    ),
    RouteContract(
        "/api/fleet/projects/v1/report",
        "exact",
        "http",
        "Loopback-only ingest for sanitized per-host project-state documents from remote reporters; schema v2 adds required workers block semantics (missing workers => unreported, [] => verified zero) and optional allowlisted lane_usage weekly rows {lane, window, used_pct, resets_at}.",
        "In-process TTL store keyed by opaque host_id; reporter must be allowlisted via MONITOR_OCCUPANCY_HOST_IDS or mac-operator.",
        "Upsert immediately when collected_at is newer than the stored report; 409 stale_report when older or equal; collected_at bounds return 400; row expires after 15 minutes without a report.",
        ("operators", "dispatch", "tests"),
        "Push complement to GET /api/fleet/projects/v1 and GET /api/fleet/workers/v1; API host self-reports in-process without POST.",
        "low with loopback-only mutation and a short TTL",
        "keep",
        mutates=True,
    ),
    RouteContract(
        "/api/fleet/workers/v1",
        "exact",
        "http",
        "Per opaque host AI worker map: one row per source identity (driver, delegate, observer, job, marker, project_state), host freshness plus its own report age_s, workers_status reported|unreported, unattributed host bucket for hostless leases, related links only with proof.",
        "Cache-only adapters: session-stream leases, local batch_state delegate tasks, observer presence, atlas-job registry, occupancy markers, and pushed project-state workers; never calls occupancy load refresh or SSH probes.",
        "Fresh hosts count toward counts.live; expired project-state reports yield freshness unknown and workers unreported; stale upstream does not synthesize worker rows.",
        ("operators", "dispatch", "tests", "fleet.html"),
        "Complements GET /api/occupancy burn board without merging identities across sources.",
        "low",
        "keep",
        locality="mixed",
        mutates=False,
    ),
    RouteContract(
        "/api",
        "exact",
        "http",
        "API root: 307 redirect to the interactive /docs explorer so the bare path never 404s (#7090).",
        "FastAPI app routes; redirect target is the built-in Swagger UI page.",
        "Static redirect; generated per request, no cache.",
        ("humans", "agents"),
        "Complements /api/contracts/routes, the machine-readable route registry.",
        "low",
        "keep; do not grow this into a new docs site",
    ),
    RouteContract(
        "/",
        "exact",
        "http",
        "Dashboard root static page.",
        "The product home, scripts/project_api/static/index.html, unless dashboards/index.html exists.",
        "Static FileResponse; page fetches live API data client-side.",
        ("humans",),
        "Catch-all static route also serves other dashboard files.",
        "low",
        "keep",
    ),
    RouteContract(
        "/{path:path}",
        "exact",
        "http",
        "Static dashboard file serving catch-all.",
        "dashboards/** (machinery pages), then the files the product entry declares (scripts/project_api/static/).",
        "Static FileResponse; dashboard freshness comes from client-side API calls.",
        ("humans",),
        "Can hide missing page contracts unless dashboard files are scanned separately.",
        "medium",
        "keep; require explicit page contracts for dashboards/*.html and the product's declared pages",
    ),
)


PAGE_CONTRACTS: tuple[PageContract, ...] = (
    PageContract(
        "routing.html",
        "/routing.html",
        "Live agent routing guidance.",
        "/api/state/routing-budget, /api/runtime/*, /api/delegate/tasks.",
        "Client fetches live endpoints with 5s timeout; no static usage snapshot.",
        ("humans",),
        "Complements runtime, delegate, cost, and routing-budget endpoints.",
        "low after live refactor",
        "keep live",
    ),
    PageContract(
        "work.html",
        "/work.html",
        "Read-only Work attention surface with evidence rail, authority/freshness, and private-source unavailable seam.",
        "GET /api/work/v1/projection?stream=<lane> and /api/work/v1/capabilities over public Monitor sources only.",
        "Client fetches live projection with 5s timeout; API reports cache_age_s and per-source degradation.",
        ("humans", "operators"),
        "Complements fleet/delegate/orient without becoming a second planning authority.",
        "medium if a degraded source is mistaken for empty work",
        "keep as the public Work foundation (FOUNDATION_COMPLETE)",
    ),
    PageContract(
        "fleet.html",
        "/fleet.html",
        "Consolidated read-only fleet-comms and operations observer.",
        "/api/fleet/* over the existing durable-plane SQLite read models, endpoint registry, sanitized runtime/ACP evidence, bounded legacy operations read models, GET /api/occupancy for cloud-observer presence, GET /api/fleet/workers/v1 for the AI worker map, and GET /api/fleet/projects/v1 for per-host checkout and serving-SHA drift.",
        "Client fetches bounded read-only projections with a 5s timeout, including AI workers, occupancy, and project-state panels; no client mutation controls or artifact-body retrieval.",
        ("humans", "operators"),
        "Consolidates observer entry points; the retired comms and channels pages are removed, while runtime and ACP pages remain available during pre-flip soak.",
        "medium if optional tables are absent or an operator mistakes the dashboard for post-flip authority",
        "keep as a pre-flip observer; file handoffs remain authoritative until an operator/advisor-approved default change",
    ),
    PageContract(
        "epics.html",
        "/epics.html",
        "Read-only operator dashboard for registry identity, honest no-lease states, remote TTL-fenced claims, heartbeats, handoffs, and bounded digests.",
        "GET /api/epics/v1 and /api/epics/v1/{stream} over the API-host SessionStreamStore seeded from the release registry at process start.",
        "Client fetches live epic streams with 5s timeout and auto-refreshes every 15s; no client mutation controls.",
        ("humans", "operators", "orchestrators"),
        "Complements work and fleet dashboards with authoritative remote lease and handoff state.",
        "low — lease health is determined by transactional TTL and heartbeat timestamps",
        "keep as the canonical remote epic lifecycle observer",
    ),
    PageContract(
        "epics-map.html",
        "/epics-map.html",
        "Read-only relationship map of issue-stream areas, epic lease/status nodes, and cached issue membership.",
        "GET /api/epics/graph/v1 over issue_streams.yaml area membership, API-host SessionStreamStore projections, and the bounded issue-stream audit cache.",
        "Client fetches the live graph with a 5s timeout and auto-refreshes every 15s; stale/no-cache markers are rendered explicitly and there are no client mutation controls.",
        ("humans", "operators", "orchestrators"),
        "Complements epics.html's flat lifecycle table with area grouping and issue-membership detail.",
        "medium if stale or no-cache data is mistaken for confirmed zero issue membership",
        "keep as the read-only epic relationship-map observer",
    ),
    PageContract(
        "delegate.html",
        "/delegate.html",
        "Delegated task observability.",
        "/api/delegate/tasks*.",
        "Live task JSON/process reads.",
        ("humans",),
        "Complements comms/build-events.",
        "low",
        "keep",
    ),
    PageContract(
        "runtime.html",
        "/runtime.html",
        "Agent runtime, usage, routing-decision overview, read-only ACPX shadow evidence, and auth.",
        "/api/runtime/*.",
        "Live file/env/Fleet Comms projection reads with 5s client timeout; routing shows a bounded loaded recent window.",
        ("humans", "orchestrators"),
        "Complements routing/cost.",
        "medium if routing summaries are treated as all-time weights or live provider health",
        "keep",
    ),
    PageContract(
        "acp.html",
        "/acp.html",
        "Readable, read-only local ACP transcript with an operational event rail.",
        "/api/runtime/acp/conversations*.",
        "Single-shot live fetch on page load; list/detail metadata stay body-free and the loopback-only transcript response is no-store. The browser uses its platform-default request timeout and does not poll.",
        ("humans",),
        "Complements runtime and channels without adding message composition or control.",
        "medium; body-bearing transcript fetch is loopback-only and no-store",
        "keep as the canonical ACP conversation observer",
    ),
    PageContract(
        "fleet-board.html",
        "/fleet-board.html",
        "Read-only fleet board home and epic detail.",
        "GET /api/fleet/v1/now, /epics, /epics/{epic}, and /agents.",
        (
            "Client refreshes every 30s. Each shown payload keeps its own age. "
            "A stale source, an unavailable roster, or a refresh older than "
            "2 minutes warns without clearing the last values."
        ),
        ("humans", "operators"),
        "Roster, pull requests, budget, and ops stay placeholders for later slices.",
        "medium if a missing source is shown as empty instead of not installed",
        "keep as the fleet board home slice",
    ),
)

router = APIRouter(tags=["contracts"])


def all_route_contracts(product: ProductContribution | None = None) -> tuple[RouteContract, ...]:
    """Machinery route contracts, then the product's (the installed product when none is given)."""
    return (*ROUTE_CONTRACTS, *(installed_product() if product is None else product).route_contracts)


def all_page_contracts(product: ProductContribution | None = None) -> tuple[PageContract, ...]:
    """Machinery page contracts, then the product's (the installed product when none is given)."""
    return (*PAGE_CONTRACTS, *(installed_product() if product is None else product).page_contracts)


def contracts_for_route(path: str, kind: ContractKind = "http") -> list[RouteContract]:
    """Return matching contracts, most specific first."""
    return sorted(
        (contract for contract in all_route_contracts() if contract.matches(path, kind)),
        key=lambda item: item.specificity,
        reverse=True,
    )


def contract_for_route(path: str, kind: ContractKind = "http") -> RouteContract | None:
    matches = contracts_for_route(path, kind)
    return matches[0] if matches else None


def contract_for_page(filename: str) -> PageContract | None:
    for contract in all_page_contracts():
        if contract.file == filename:
            return contract
    return None


@router.get("/routes")
async def route_contracts(request: Request, ctx: MonitorContext = Depends(get_ctx)):
    """Public Monitor route/page contract registry."""
    _ = resolve_context(ctx)
    product = getattr(request.app.state, "product", None)
    return {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "route_contracts": [contract.to_dict() for contract in all_route_contracts(product)],
        "page_contracts": [contract.to_dict() for contract in all_page_contracts(product)],
    }
