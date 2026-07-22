"""Machine-readable Monitor API and dashboard contracts.

The registry is intentionally family-based: most Monitor endpoints belong to
router families with the same source and freshness behavior. Tests verify that
every public FastAPI route and literal dashboard HTML page matches a contract.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter

ContractKind = Literal["http", "websocket"]
MatchType = Literal["exact", "prefix"]


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
    mutates: bool = False
    replacement: str | None = None

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
        "/api/contracts/routes", "exact", "http",
        "Machine-readable Monitor route and dashboard contract registry.",
        "This module's ROUTE_CONTRACTS and PAGE_CONTRACTS declarations.",
        "Generated per request; no route cache.",
        ("tests", "agents", "docs"),
        "Documents every other local Monitor endpoint.",
        "low",
        "keep",
    ),
    RouteContract(
        "/api/state/reviewer-ghosts", "prefix", "http",
        "Reviewer hallucination telemetry for missing-anchor reviewer fixes.",
        "curriculum/l2-uk-en/{track}/review/*-ghost-review-r*.yaml",
        "No route cache; per-request review-directory scan with optional filters.",
        ("agents", "future dashboards", "tests"),
        "Mounted under /api/state but logically telemetry, not canonical module state.",
        "medium if treated as generic /api/state progress data",
        "keep as a distinct contract family",
    ),
    RouteContract(
        "/api/state/preparation", "prefix", "http",
        "Versioned active-manifest roster and one-module canonical preparation projection for agents.",
        "curriculum.yaml + canonical four-file learner bundles + learner publication files + "
        "curriculum_readiness.evaluate_preparation().",
        "Recomputed from deterministic local sources on every request; strong ETag addresses exact response bytes.",
        ("agents", "session_start.sh", "orchestrators"),
        "Replaces readiness inferences from legacy /api/state/summary, /module, and /ready-to-build telemetry.",
        "low — failures in manifest, readiness contracts, selectors, or repository authority fail closed",
        "keep as the canonical agent-facing curriculum preparation contract",
    ),
    RouteContract(
        "/api/state/ready-to-build", "exact", "http",
        "Deprecated research-complete candidate list; never generation readiness.",
        "Legacy orchestration research/dossier presence and pipeline content phase state.",
        "No route cache; generated per request without canonical preparation evaluation.",
        ("legacy agents",),
        "Misleading predecessor to /api/state/preparation; candidate membership is preserved for compatibility.",
        "high if treated as generation authority",
        "deprecated; migrate to /api/state/preparation",
        replacement="/api/state/preparation",
    ),
    RouteContract(
        "/api/state", "prefix", "http",
        "Mixed legacy pipeline telemetry plus canonical project, review, build, routing, and cold-start state.",
        "curriculum.yaml, plans, orchestration state, research/dossier docs, audit/review files, artifacts, and cost records.",
        "State router TTLs by endpoint; major endpoints expose meta.source, meta.cache, meta.stale_after_s; selected endpoints support ?fresh=true.",
        ("progress.html", "track-health.html", "quality.html", "index.html", "Site LiveStatus", "agents"),
        "Overlaps /api/dashboard projections, /api/blue/live-status, and legacy team views.",
        "low after #2790 for summary/progress; medium for state endpoints that do not expose meta yet",
        "keep for compatible telemetry; use /api/state/preparation for curriculum readiness decisions",
    ),
    RouteContract(
        "/api/dashboard", "prefix", "http",
        "Rich dashboard projections for audit, curriculum, pipeline, and comms pages.",
        "Dashboard helper scans over plans, status cache, research, reviews, orchestration, and broker data.",
        "Dashboard helper caches are process-local: track detail 30s, summary 60s, overview reuses state summary 60s. /overview includes meta (derived from state-summary + dashboard caches); most other payloads do not.",
        ("audit-dashboard.html", "curriculum-dashboard.html", "index.html"),
        "Overlaps /api/state counts; richer module/audit detail remains distinct.",
        "medium if consumers treat it as canonical fresh state",
        "keep for page-specific detail; use /api/state/* (with ?fresh=true + meta) for canonical freshness-sensitive counts and state. Dashboard meta is secondary/derived.",
    ),
    RouteContract(
        "/api/blue/live-status", "exact", "http",
        "Deprecated legacy live build status.",
        "Filesystem scan over module files and status cache.",
        "No route cache; returns deprecation headers and replacement guidance.",
        ("legacy agents", "docs"),
        "Duplicates /api/state/build-status.",
        "high because stale consumers can bypass the canonical state contract",
        "deprecated; migrate to /api/state/build-status",
        replacement="/api/state/build-status",
    ),
    RouteContract(
        "/api/blue", "prefix", "http",
        "Legacy Blue/final-review helper endpoints.",
        "Status cache, module files, activity YAML, review files, and batch state.",
        "No route cache; /audit?...fresh=true runs audit as a side effect.",
        ("agents", "final-review workflow"),
        "Overlaps /api/state and /api/artifacts for some module evidence.",
        "low for final-review helpers; medium for write-side effects",
        "retain compatibility helpers",
    ),
    RouteContract(
        "/api/gold", "prefix", "http",
        "Legacy Gold/team module inspection endpoints.",
        "Plans, module files, orchestration, and broker data.",
        "No route cache; live filesystem and broker reads.",
        ("legacy agents", "docs"),
        "Overlaps /api/state/module, /api/artifacts, and /api/dashboard/module.",
        "medium because canonical source is not obvious from the route name",
        "retain until agent consumers migrate",
    ),
    RouteContract(
        "/api/agent", "prefix", "http",
        "Agent-oriented module, orchestration, prompt, runtime, and worktree snapshots.",
        "Module files, orchestration files, runtime files, and git worktree state.",
        "No route cache; live filesystem and git/process reads.",
        ("agents", "docs"),
        "Overlaps /api/state, /api/artifacts, /api/runtime, and /api/worktrees.",
        "medium because it is a compatibility facade",
        "retain until agent consumers migrate",
    ),
    RouteContract(
        "/api/artifacts", "prefix", "http",
        "Artifact classification, ship-ready checks, report listing, drift, and force-preview evidence.",
        "Plans, generated curriculum files, site MDX, review/audit docs, docs/audit reports.",
        "No route cache; live filesystem reads.",
        ("artifacts.html", "agents", "docs"),
        "Complements /api/state published/stale signals.",
        "low",
        "keep",
    ),
    RouteContract(
        "/artifacts", "prefix", "http",
        "Human artifact browser and approved documentation artifact serving.",
        "docs, audit, and other approved artifact roots.",
        "No route cache; serves artifacts.html for browser requests and JSON/file listings on demand.",
        ("artifacts.html", "humans"),
        "Shares artifact metadata with /api/artifacts/html.",
        "low",
        "keep",
    ),
    RouteContract(
        "/files", "prefix", "http",
        "Approved documentation artifact serving alias.",
        "docs, audit, and other approved artifact roots.",
        "No route cache; live filesystem serving with extension/root allowlists.",
        ("humans", "agents"),
        "Alias of /artifacts file serving without the browser page default.",
        "low",
        "keep",
    ),
    RouteContract(
        "/api/comms/messages", "exact", "http",
        "Deprecated legacy direct-message list.",
        "SQLite message broker.",
        "No route cache; live broker reads.",
        ("comms.html", "legacy ask-* path"),
        "Replaced by channel message endpoints.",
        "medium",
        "deprecated; migrate to /api/comms/channels/{name}/messages",
        replacement="/api/comms/channels/{name}/messages",
    ),
    RouteContract(
        "/api/comms/conversations", "exact", "http",
        "Deprecated legacy direct-message conversation list.",
        "SQLite message broker.",
        "No route cache; live broker reads.",
        ("comms.html", "legacy ask-* path"),
        "Replaced by channel threads.",
        "medium",
        "deprecated; migrate to /api/comms/channels/{name}/threads/{thread_id}",
        replacement="/api/comms/channels/{name}/threads/{thread_id}",
    ),
    RouteContract(
        "/api/comms/conversation", "prefix", "http",
        "Deprecated legacy direct-message conversation detail.",
        "SQLite message broker.",
        "No route cache; live broker reads.",
        ("comms.html", "legacy ask-* path"),
        "Replaced by channel threads.",
        "medium",
        "deprecated; migrate to /api/comms/channels/{name}/threads/{thread_id}",
        replacement="/api/comms/channels/{name}/threads/{thread_id}",
    ),
    RouteContract(
        "/api/comms/live-activity", "exact", "http",
        "Deprecated legacy live activity summary.",
        "SQLite broker and process probes.",
        "No route cache; live broker/process reads.",
        ("legacy docs",),
        "Replaced by channel activity and delegate/build event endpoints.",
        "medium",
        "deprecated; migrate to /api/comms/agent-activity and /api/delegate/active",
        replacement="/api/comms/agent-activity",
    ),
    RouteContract(
        "/api/comms/send", "exact", "http",
        "Deprecated legacy direct-message send endpoint.",
        "SQLite message broker.",
        "No route cache; POST mutates broker state.",
        ("comms.html", "legacy ask-* path"),
        "Replaced by channel post endpoint.",
        "medium",
        "deprecated; migrate to /api/comms/channels/{name}/post",
        mutates=True,
        replacement="/api/comms/channels/{name}/post",
    ),
    RouteContract(
        "/api/comms", "prefix", "http",
        "Canonical channel bridge plus broker/process health, batch progress, zombies, acknowledgements, and module-linked messages.",
        "SQLite message broker, delivery tables, process probes, and build state.",
        "No route cache; live broker/process reads. POST routes mutate broker/message state.",
        ("channels.html", "comms.html", "track-health.html", "index.html", "agents"),
        "Canonical channels replace legacy direct-message routes; status overlaps delegate/build events.",
        "low/medium",
        "keep",
    ),
    RouteContract(
        "/api/delegate", "prefix", "http",
        "Delegated task list, active task count, and task result detail.",
        "batch_state/tasks/*.json, process liveness, and task result files.",
        "No route cache; live filesystem/process reads.",
        ("delegate.html", "index.html", "agents"),
        "Complements /api/orient.delegate and /api/build/events.",
        "low",
        "keep",
    ),
    RouteContract(
        "/api/coordination", "prefix", "http",
        "Parallel-agent coordination ledger summary, active task list, and task detail.",
        "orchestration/agent-ledger/tasks/*.json written by scripts/orchestration/agent_ledger.py.",
        "No route cache; live filesystem reads from the local coordination ledger.",
        ("agents", "orchestrator", "future dashboards"),
        "Complements /api/delegate process state with explicit task ownership and review metadata.",
        "low while JSON ledger is healthy; invalid task files surface as errors instead of silent stale state",
        "keep",
    ),
    RouteContract(
        "/api/worktrees", "exact", "http",
        "Active git worktree registry.",
        "git worktree list --porcelain, per-worktree git status, and git log -1.",
        "No route cache; each git subprocess has a bounded timeout.",
        ("agents", "cold-start tooling", "worktree hygiene"),
        "Complements /api/git/hygiene and /api/git/cleanup.",
        "low; failures degrade to empty/error payload",
        "keep",
    ),
    RouteContract(
        "/api/build/events", "prefix", "http",
        "Recent and active module build event timeline.",
        "curriculum/l2-uk-en/**/orchestration/**/dispatch/*-meta.json plus module state files.",
        "No route cache; filesystem scan capped at 5000 dispatch metadata files.",
        ("build-events.html", "comms.html", "index.html"),
        "Complements delegate and comms activity.",
        "low",
        "keep",
    ),
    RouteContract(
        "/api/runtime", "prefix", "http",
        "Agent runtime inventory, usage, default-model quota headroom, recent calls, and auth mode.",
        "Runtime config, usage JSONL, environment presence booleans, and OAuth credential presence.",
        "No route cache; live file/env reads. Auth reports booleans/source names only, never secret values.",
        ("runtime.html", "routing.html", "index.html", "agents"),
        "Usage complements /api/state/routing-budget and cost endpoints.",
        "low",
        "keep",
    ),
    RouteContract(
        "/api/state/routing-budget", "exact", "http",
        "Per-agent soft-cap burn and routing recommendation.",
        "scripts/config/agent_budgets.yaml, cost records, and delegate in-flight state.",
        "No route cache; computes from current cost records and active delegate task state.",
        ("routing.html", "delegate.py", "agents"),
        "Overlaps runtime usage and cost summaries but adds routing recommendation.",
        "low",
        "keep canonical for routing guidance",
    ),
    RouteContract(
        "/api/analytics/cost", "prefix", "http",
        "Cost summaries by project, module, and phase.",
        "batch_state/api_usage/** cost records.",
        "No route cache; live usage record reads.",
        ("cost.html", "index.html", "routing.html"),
        "Duplicate mount with /api/cost.",
        "low",
        "keep canonical UI path",
    ),
    RouteContract(
        "/api/cost", "prefix", "http",
        "Compatibility alias for cost summaries.",
        "batch_state/api_usage/** cost records.",
        "No route cache; live usage record reads.",
        ("legacy scripts", "docs"),
        "Alias of /api/analytics/cost.",
        "low",
        "retain compatibility alias",
        replacement="/api/analytics/cost",
    ),
    RouteContract(
        "/api/wiki", "prefix", "http",
        "Wiki compilation status, quality gates, build log, article preview, and source inventory.",
        "Wiki progress state/DB, wiki markdown files, and data/sources.db.",
        "Selected aggregate reads use short shared TTL cache; article detail reads file bodies on demand.",
        ("wiki.html", "index.html"),
        "Complements /api/state published/wiki status signals.",
        "low/medium",
        "keep",
    ),
    RouteContract(
        "/api/images", "prefix", "http",
        "Textbook image catalog, page rendering, annotations, stats, cleanup, and reload.",
        "data/textbook_images/**, data/textbooks/**, and annotation JSONL.",
        "Lazy in-memory image index; PDF pool and page-render LRU cache; /reload resets the index.",
        ("image-explorer.html",),
        "Complements /api/rag image search.",
        "low; mutating annotation/cleanup/reload routes are local-only",
        "keep",
    ),
    RouteContract(
        "/images", "prefix", "http",
        "Static textbook image file serving.",
        "data/textbook_images/** image files.",
        "FileResponse with Cache-Control max-age=3600.",
        ("image-explorer.html",),
        "Static companion to /api/images metadata.",
        "low",
        "keep",
    ),
    RouteContract(
        "/api/rag", "prefix", "http",
        "RAG text, image, and literary search plus collection stats.",
        "Local RAG/Qdrant collections and related corpus indexes.",
        "No Monitor route cache; search backend freshness follows collection build state.",
        ("image-explorer.html", "agents"),
        "Overlaps MCP/source tools but is UI-specific.",
        "low/medium if collections are stale",
        "keep",
    ),
    RouteContract(
        "/api/admin", "prefix", "http",
        "Local maintenance: health, backups, disk, broker vacuum, logs, and collection verification.",
        "Qdrant snapshots/storage, broker DB, logs, data directories, and collection metadata.",
        "No route cache; live local maintenance operations. POST/DELETE routes mutate local state.",
        ("admin.html",),
        "Operational-only surface.",
        "medium because several routes mutate local state",
        "keep local-only",
    ),
    RouteContract(
        "/api/consultation", "prefix", "http",
        "Template proposal queue, detail, approve/reject, history, and metrics.",
        "Consultation queue/history files.",
        "No route cache; live filesystem reads. Approve/reject POST routes mutate queue/history state.",
        ("consultation.html", "index.html"),
        "None.",
        "low",
        "keep",
    ),
    RouteContract(
        "/api/decisions", "prefix", "http",
        "Decision registry listing, stale/budget/lineage views, scope lookups, and detail.",
        "docs/decisions/**.",
        "No route cache; live filesystem reads.",
        ("agents", "docs"),
        "Related to /api/state/governance aggregate.",
        "low",
        "keep",
    ),
    RouteContract(
        "/api/state/governance", "exact", "http",
        "Governance aggregate for decisions and ADR hygiene.",
        "docs/decisions/** and ADR docs.",
        "No route cache in the endpoint; /api/orient may cache the governance section for 120s.",
        ("orient.html", "agents"),
        "Aggregate counterpart to /api/decisions detail endpoints.",
        "low",
        "keep",
    ),
    RouteContract(
        "/api/hermes-cron/latest", "exact", "http",
        "Latest nightly sweep audit results and insights.",
        "batch_state/hermes_cron/latest.json and latest.md.",
        "No route cache; reads from the latest generated nightly audit artifacts.",
        ("agents", "docs"),
        "None.",
        "low",
        "keep",
    ),
    RouteContract(
        "/api/issues/map", "exact", "http",
        "Open issue map grouped by category.",
        "gh issue list output.",
        "No route cache in handler; /api/orient wraps issue collection with a 120s cache and short timeout.",
        ("agents", "issue hygiene"),
        "Overlaps /api/orient.issues.",
        "medium if GitHub is slow or unavailable",
        "keep best-effort",
    ),
    RouteContract(
        "/api/issues/streams", "exact", "http",
        "Issue-stream hygiene report (#4708): orphans without a stream epic, multi-homed, pending native links.",
        "batch_state/issue_stream_audit.json auditor cache; ?fresh=true reruns the auditor.",
        "Cache TTL 3600s; session-setup hook 11b refreshes in background when stale.",
        ("agents", "issue hygiene", "orchestrators"),
        "Complements /api/issues/map (label categories) with stream-epic membership.",
        "low — degrades to {error:...} without gh",
        "keep best-effort",
    ),
    RouteContract(
        "/api/rules", "exact", "http",
        "Condensed agent rule set for cold start.",
        "Deployed rule/source markdown files.",
        "Hash/ETag semantics when telemetry footer is disabled; otherwise generated per request.",
        ("agents", "docs"),
        "Replaces direct rule-file reads at cold start.",
        "low",
        "keep cold-start source of truth",
    ),
    RouteContract(
        "/api/session/current", "exact", "http",
        "Agent-specific current session handoff.",
        "docs/session-state/current.md router and current.<agent>.md handoff files.",
        "Hash/ETag semantics when telemetry footer is disabled; generated per request otherwise.",
        ("agents", "docs"),
        "Replaces direct session-state file spelunking.",
        "low",
        "keep cold-start source of truth",
    ),
    RouteContract(
        "/api/orient", "exact", "http",
        "One-shot agent and dashboard orientation snapshot.",
        "Git, GitHub issues, pipeline state, runtime files, delegate state, broker, rollover registry, wiki, governance, health, and session hints.",
        "Per-section TTLs in main.py; ?fresh=true invalidates orient cache entries.",
        ("orient.html", "index.html", "agents"),
        "Aggregates many other API sections.",
        "low/medium when upstream collectors degrade",
        "keep cold-start source of truth",
    ),
    RouteContract(
        "/api/rollovers", "exact", "http",
        "Read-only fleet rollover audit and exact selector projection.",
        "Versioned registry records under .agent/thread-rollover-registry/v1/.",
        "Generated per request; no mutation path is exposed over HTTP.",
        ("agents", "monitor client", "orchestrators"),
        "Compact actionable entries are also exposed through /api/orient.",
        "low — corrupt records are isolated and returned as explicit errors",
        "keep as the canonical rollover observability surface",
    ),
    RouteContract(
        "/api/knowledge", "prefix", "http",
        "ADR-011 bounded Project Research Registry discovery: task-scoped pointer "
        "manifest and per-record compact digest bodies.",
        "docs/references/research-registry.yaml + docs/references/research-digests/** "
        "via the P1 validator primitives (scripts/audit/check_research_registry.py).",
        "No route cache; per-request deterministic registry load. Strong ETags: a "
        "context-scoped ETag on /manifest and the P1 content_hash on /record/{id}. "
        "Disabled by default behind the research_registry kill switch.",
        ("agents", "dispatch", "cold-start tooling"),
        "Pointer index for /api/state/manifest's research component; bodies never "
        "enter cold start.",
        "low; disabled or a failed load degrades to an empty/disabled projection",
        "keep as the research discovery surface",
    ),
    RouteContract(
        "/api/state/manifest", "exact", "http",
        "Tiny cold-start manifest with hashes and URLs.",
        "Rules/session hash helpers plus static endpoint metadata.",
        "Generated per request; rules/session hashes let agents skip unchanged payloads.",
        ("agents", "monitor client"),
        "Index for /api/rules, /api/session/current, /api/orient, comms inbox/activity.",
        "low",
        "keep cold-start source of truth",
    ),
    RouteContract(
        "/api/site", "prefix", "http",
        "Public site health and deployment observability.",
        "Public site probe and GitHub Pages deployment data.",
        "No route cache; each request probes/queries live state with bounded subprocess/network behavior.",
        ("agents", "docs"),
        "Complements local build/status dashboards.",
        "medium if network/GitHub is unavailable",
        "keep",
    ),
    RouteContract(
        "/api/agent-monitor/status", "exact", "http",
        "Host-local resource, process, and active agent lease snapshot.",
        "psutil host/process metrics and the transactional agent-monitor lease store.",
        "Computed per request; dead and expired leases reconciled at read time; no response cache.",
        ("runtime.html", "agent launchers", "orchestrators", "tests"),
        "Complements /api/runtime provider usage and /api/delegate task telemetry.",
        "medium if launcher heartbeat coverage is incomplete",
        "keep as canonical host-capacity snapshot",
    ),
    RouteContract(
        "/api/agent-monitor/preflight", "exact", "http",
        "Atomically evaluates capacity and creates a short-lived pending reservation.",
        "Configured capacity policy, live psutil memory, and active lease reservations.",
        "Evaluated transactionally per request; no cache.",
        ("agent launchers", "orchestrators", "tests"),
        "Memory admission only; does not replace provider quota headroom.",
        "high if implemented as a non-atomic check",
        "keep; registration must consume the exact reservation",
        mutates=True,
    ),
    RouteContract(
        "/api/agent-monitor/register", "exact", "http",
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
        "/api/agent-monitor/heartbeat", "exact", "http",
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
        "/api/agent-monitor/release", "exact", "http",
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
        "/api/git", "prefix", "http",
        "Git hygiene and cleanup dry-run reporting.",
        "Local git branches, worktrees, and batch_state task metadata.",
        "No route cache; live git/filesystem reads.",
        ("agents", "docs"),
        "Complements /api/worktrees.",
        "low/medium",
        "keep read-only cleanup planning",
    ),
    RouteContract(
        "/api/telemetry", "prefix", "http",
        "Tool timing and module-build token telemetry ingest/readback.",
        "Telemetry SQLite state used by Monitor instrumentation and module-build PR reporting.",
        "No route cache; POST mutates telemetry stores, GET reads current telemetry state.",
        ("agents", "runtime tooling"),
        "Complements optional telemetry footer, runtime usage logs, and analytics cost summaries.",
        "low",
        "keep",
    ),
    RouteContract(
        "/api/discussions/active", "exact", "http",
        "Active multi-agent discussion snapshot.",
        "Channel bridge SQLite messages and discussion state.",
        "No route cache; live broker reads.",
        ("orient.html", "channels.html"),
        "Complements channel message endpoints.",
        "low",
        "keep",
    ),
    RouteContract(
        "/api/batch", "prefix", "http",
        "Legacy batch dispatcher, active orchestration, failures, usage, checkpoints, and logs.",
        "batch_state files and dispatcher process/log state.",
        "No route cache; live filesystem/process reads. Dispatcher scan POST mutates dispatcher state.",
        ("legacy scripts", "docs"),
        "Overlaps delegate, build-events, and comms progress surfaces.",
        "medium because it is older orchestration vocabulary",
        "retain compatibility until clients migrate",
    ),
    RouteContract(
        "/api/config", "exact", "http",
        "Monitor config and level metadata.",
        "scripts/api/config.py constants.",
        "Generated per request; no route cache.",
        ("consultation.html", "agents"),
        "None.",
        "low",
        "keep",
    ),
    RouteContract(
        "/api/health", "exact", "http",
        "API process health, uptime, timeout/saturation counters.",
        "API process state and resilience middleware counters.",
        "Generated per request; no route cache.",
        ("health checks", "tests", "agents"),
        "Related to /api/admin/health and /api/orient.health.",
        "low",
        "keep",
    ),
    RouteContract(
        "/ws/batch", "exact", "websocket",
        "Legacy batch heartbeat stream.",
        "API process heartbeat loop.",
        "Sends {'type':'heartbeat'} every 5s while connected; no persisted state or cache.",
        ("legacy live monitors",),
        "Overlaps newer polling dashboards.",
        "medium because WebSockets are not visible in OpenAPI",
        "retain until websocket consumers are audited",
    ),
    RouteContract(
        "/", "exact", "http",
        "Dashboard root static page.",
        "dashboards/index.html.",
        "Static FileResponse; page fetches live API data client-side.",
        ("humans",),
        "Catch-all static route also serves other dashboard files.",
        "low",
        "keep",
    ),
    RouteContract(
        "/{path:path}", "exact", "http",
        "Static dashboard file serving catch-all.",
        "dashboards/**.",
        "Static FileResponse; dashboard freshness comes from client-side API calls.",
        ("humans",),
        "Can hide missing page contracts unless dashboard files are scanned separately.",
        "medium",
        "keep; require explicit page contracts for dashboards/*.html",
    ),
)


PAGE_CONTRACTS: tuple[PageContract, ...] = (
    PageContract(
        "index.html", "/",
        "Operations launchpad and aggregate cards.",
        "Fanout across dashboard, state, orient, runtime, delegate, wiki, and cost APIs.",
        "Client fetches live endpoints with 5s timeout; state summary uses ?fresh=true.",
        ("humans",),
        "Links to every major dashboard.",
        "low",
        "keep",
    ),
    PageContract(
        "progress.html", "/progress.html",
        "Canonical visual project progress.",
        "/api/state/summary, /api/state/pipeline-versions, /api/state/pipeline/{track}.",
        "Explicit ?fresh=true requests and freshness banner.",
        ("humans",),
        "Overlaps audit/curriculum but owns current progress.",
        "low",
        "keep canonical",
    ),
    PageContract(
        "routing.html", "/routing.html",
        "Live agent routing guidance.",
        "/api/state/routing-budget, /api/runtime/*, /api/delegate/tasks.",
        "Client fetches live endpoints with 5s timeout; no static usage snapshot.",
        ("humans",),
        "Complements runtime, delegate, cost, and routing-budget endpoints.",
        "low after live refactor",
        "keep live",
    ),
    PageContract(
        "audit-dashboard.html", "/audit-dashboard.html",
        "QA gate and audit drill-down.",
        "/api/dashboard/* and /api/state/module/*.",
        "Dashboard helper caches 30/60s; state module is live.",
        ("humans",),
        "Overlaps progress counts.",
        "medium",
        "keep for QA detail",
    ),
    PageContract(
        "quality.html", "/quality.html",
        "Research/review/issues/weak-points fix queue.",
        "/api/state/research-coverage, /api/state/review-coverage, /api/state/issues, /api/state/weak-points.",
        "State coverage TTLs where configured; weak-points has a 60s cache.",
        ("humans",),
        "Complements progress.",
        "low",
        "keep",
    ),
    PageContract(
        "track-health.html", "/track-health.html",
        "One-track build, audit, enrichment, review, and comms health.",
        "/api/state/build-status, /api/state/enrichment-status, /api/state/track-health, /api/state/module, /api/comms/by-module.",
        "Build-status 15/30s caches; enrichment 120s; track-health 30s.",
        ("humans",),
        "Overlaps progress.",
        "low",
        "keep",
    ),
    PageContract(
        "curriculum-dashboard.html", "/curriculum-dashboard.html",
        "Plan/meta/module inspection.",
        "/api/dashboard/overview, /api/dashboard/track, /api/dashboard/module.",
        "Dashboard helper caches 30/60s.",
        ("humans",),
        "Overlaps audit/progress.",
        "medium",
        "keep as inspection workflow",
    ),
    PageContract(
        "channels.html", "/channels.html",
        "Canonical channel bridge UI.",
        "/api/comms/channels*.",
        "Live broker reads; client preserves deeplink state.",
        ("humans", "agents"),
        "Replaces legacy comms chat.",
        "low",
        "keep canonical",
    ),
    PageContract(
        "comms.html", "/comms.html",
        "Legacy direct-message, zombie, and batch progress UI.",
        "Deprecated legacy comms routes plus build events and broker health.",
        "Live broker/process reads.",
        ("humans",),
        "Duplicates channels for chat.",
        "medium",
        "retain as legacy operations page until old users/CLI migrate",
    ),
    PageContract(
        "delegate.html", "/delegate.html",
        "Delegated task observability.",
        "/api/delegate/tasks*.",
        "Live task JSON/process reads.",
        ("humans",),
        "Complements comms/build-events.",
        "low",
        "keep",
    ),
    PageContract(
        "runtime.html", "/runtime.html",
        "Agent runtime, usage, and auth.",
        "/api/runtime/*.",
        "Live file/env reads with 5s client timeout.",
        ("humans",),
        "Complements routing/cost.",
        "low",
        "keep",
    ),
    PageContract(
        "cost.html", "/cost.html",
        "Cost reports.",
        "/api/analytics/cost*.",
        "Live cost record reads.",
        ("humans",),
        "Complements routing/runtime.",
        "low",
        "keep",
    ),
    PageContract(
        "build-events.html", "/build-events.html",
        "Build dispatch event timeline.",
        "/api/build/events/*.",
        "Live capped filesystem scans.",
        ("humans",),
        "Complements comms/delegate.",
        "low",
        "keep",
    ),
    PageContract(
        "wiki.html", "/wiki.html",
        "Wiki build, quality, source, and log overview.",
        "/api/wiki/*.",
        "Wiki router caches selected aggregates.",
        ("humans",),
        "Complements state published/wiki signals.",
        "low",
        "keep",
    ),
    PageContract(
        "artifacts.html", "/artifacts/",
        "Artifact/report browser.",
        "/api/artifacts/html and /artifacts file serving.",
        "Live metadata scan.",
        ("humans",),
        "Links all ops pages.",
        "low",
        "keep",
    ),
    PageContract(
        "image-explorer.html", "/image-explorer.html",
        "Textbook image/RAG annotation UI.",
        "/api/images/*, /api/rag/*, /images/*.",
        "Lazy image index and render LRU.",
        ("humans",),
        "None.",
        "low",
        "keep",
    ),
    PageContract(
        "images.html", "/images.html",
        "Redirect alias to image explorer.",
        "No API source; static meta refresh to /image-explorer.html.",
        "Static redirect only.",
        ("legacy links",),
        "Duplicate alias.",
        "low",
        "retain redirect-only alias",
    ),
    PageContract(
        "admin.html", "/admin.html",
        "Local maintenance dashboard.",
        "/api/admin/*.",
        "Live local operations.",
        ("humans",),
        "None.",
        "medium due to mutating POST/DELETE actions",
        "keep local-only",
    ),
    PageContract(
        "consultation.html", "/consultation.html",
        "Template proposal queue/history dashboard.",
        "/api/consultation/* and /api/config.",
        "Live queue/history reads.",
        ("humans",),
        "None.",
        "low",
        "keep",
    ),
    PageContract(
        "orient.html", "/orient.html",
        "Cold-start/session orientation snapshot.",
        "/api/orient and /api/discussions/active.",
        "Orient section TTLs; client auto-refreshes.",
        ("humans", "agents"),
        "Mirrors agent bootstrap.",
        "low",
        "keep",
    ),
)

router = APIRouter(tags=["contracts"])


def contracts_for_route(path: str, kind: ContractKind = "http") -> list[RouteContract]:
    """Return matching contracts, most specific first."""
    return sorted(
        (contract for contract in ROUTE_CONTRACTS if contract.matches(path, kind)),
        key=lambda item: item.specificity,
        reverse=True,
    )


def contract_for_route(path: str, kind: ContractKind = "http") -> RouteContract | None:
    matches = contracts_for_route(path, kind)
    return matches[0] if matches else None


def contract_for_page(filename: str) -> PageContract | None:
    for contract in PAGE_CONTRACTS:
        if contract.file == filename:
            return contract
    return None


@router.get("/routes")
async def route_contracts():
    """Public Monitor route/page contract registry."""
    return {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "route_contracts": [contract.to_dict() for contract in ROUTE_CONTRACTS],
        "page_contracts": [contract.to_dict() for contract in PAGE_CONTRACTS],
    }
