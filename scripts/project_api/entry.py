"""The configured product entry of the Monitor API (Monitor split, C-4687).

``scripts/curriculum/monitor_paths.v1.json`` names this module as
``product_api``. The machinery loader (``scripts.api.product_contribution``)
imports it through the configured entry point and calls :func:`build_api`.

Example:
  .venv/bin/python -c "from scripts.api.monitor_context import production_context as c; from scripts.project_api.entry import build_api; print(len(build_api(c()).routers))"
"""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType
from typing import Any

from scripts.api.monitor_context import MonitorContext
from scripts.api.product_contribution import ProductContribution, RouterMount

from . import (
    admin_router,
    agent_router,
    artifacts_router,
    atlas_jobs_router,
    batch_progress,
    batch_router,
    build_events_router,
    consultation_router,
    core_router,
    cost_router,
    dashboard_router,
    decisions_router,
    governance_router,
    images_router,
    module_builds,
    orient,
    reviewer_ghosts_router,
    route_contracts,
    site_router,
    sources_router,
    state_router,
    wiki_router,
)

# The product pages and assets the Monitor serves, by URL path. Only these are
# served; the static catch-all never lists or walks this directory.
STATIC_ROOT = Path(__file__).resolve().parent / "static"
STATIC_FILES = (
    "index.html",
    "admin.html",
    "artifacts.html",
    "build-events.html",
    "consultation.html",
    "cost.html",
    "curriculum-dashboard.html",
    "image-explorer.html",
    "orient.html",
    "progress.html",
    "quality.html",
    "wiki.html",
    "data/status.json",
)

# Product modules whose import closure the startup preload warms.
PRELOAD_MODULES = (
    "scripts.project_api.state_build",
    "scripts.project_api.review_parsing",
    "audit.config",
    "audit.checks.activity_validation",
    "yaml_activities",
    "scripts.build.phase_constants",
    "research_quality",
    "research.research_markdown_utils",
)

OPTIONAL_PRELOAD_MODULES = (
    "pymupdf",
    # Not the deprecated `fitz` alias: its import calls pymupdf.message_warning,
    # which writes to the stream captured when pymupdf was imported. A closed
    # pytest capture stream then raises ValueError and aborts API startup.
    "rag.poc_pair_page",
    "rag.query",
)

# Same prefixes, tags and relative order as before the split.
ROUTERS = (
    RouterMount(admin_router.router, "/api/admin"),
    RouterMount(agent_router.router, "/api/agent", ("agent",)),
    RouterMount(artifacts_router.router, "/api/artifacts", ("artifacts",)),
    RouterMount(atlas_jobs_router.router, "/api/atlas-jobs", ("atlas-jobs",)),
    RouterMount(batch_progress.router, "/api/comms"),
    RouterMount(consultation_router.router, "/api/consultation"),
    RouterMount(cost_router.router, "/api/analytics/cost"),
    RouterMount(dashboard_router.router, "/api/dashboard"),
    RouterMount(decisions_router.router, "/api/decisions", ("decisions",)),
    RouterMount(governance_router.router, "/api/state/governance", ("governance",)),
    RouterMount(build_events_router.router, "/api/build/events"),
    RouterMount(images_router.router, "/api/images"),
    RouterMount(sources_router.router, "/api/sources", ("sources",)),
    # GH #1529 P3 — reviewer-ghost telemetry nested under /api/state so clients
    # can discover it alongside the other state-query endpoints.
    RouterMount(reviewer_ghosts_router.router, "/api/state/reviewer-ghosts", ("reviewer-ghosts",)),
    RouterMount(site_router.router, "/api/site", ("site",)),
    RouterMount(state_router.router, "/api/state"),
    RouterMount(module_builds.router),
    RouterMount(wiki_router.router, "/api/wiki", ("wiki",)),
    RouterMount(batch_router.router),
    RouterMount(core_router.router),
)


def _warm_state_scans(ctx: MonitorContext) -> None:
    state_router.warm_state_scans(ctx)


def _health_fields(ctx: MonitorContext) -> dict[str, Any]:
    return orient.health_fields(ctx)


def _fleet_batches(ctx: MonitorContext | None) -> dict[str, Any]:
    return batch_progress.fleet_batch_snapshot(ctx)


def build_api(context: MonitorContext) -> ProductContribution:
    """Return the product contribution for one Monitor app.

    The contribution does not depend on ``context`` today: the product
    routes read their roots and stores from the request's context. The hooks
    look their target up when called, so a test that replaces one on its
    module is seen by the machinery caller.
    """
    return ProductContribution(
        routers=ROUTERS,
        static_files=MappingProxyType({name: STATIC_ROOT / name for name in STATIC_FILES}),
        route_contracts=route_contracts.ROUTE_CONTRACTS,
        page_contracts=route_contracts.PAGE_CONTRACTS,
        preload=PRELOAD_MODULES,
        preload_optional=OPTIONAL_PRELOAD_MODULES,
        warmup=(_warm_state_scans,),
        orient_sections=orient.orient_sections,
        health=_health_fields,
        atlas=atlas_jobs_router.ATLAS_PROVIDER,
        fleet_batches=_fleet_batches,
    )
