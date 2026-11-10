"""Held-out checks for the Monitor split (C-4687): routes, pages, boundary and the product entry.

The product half of the Monitor API lives in ``scripts/project_api`` and
reaches the app only through the configured product entry. These checks pin
what the split must not change (every mounted route still resolves to its own
endpoint, product routes come from product modules, every dashboard page
loads) and what it must hold (no machinery module under ``scripts/api``
imports product code; the loader refuses a bad product root).
"""

from __future__ import annotations

import json
import re
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from fastapi.routing import _IncludedRouter
from fastapi.testclient import TestClient
from lu_machinery.api import main as api_main
from lu_machinery.api import product_contribution
from lu_machinery.api.monitor_context import fixture_context
from lu_machinery.api.product_contribution import EMPTY, ProductContribution, ProductEntryError, load_product
from lu_machinery.ci.components import scan_imports
from lu_machinery.ops.product_entry import ConfiguredModuleError, load_configured_module
from starlette.routing import Match

from tests.api.opsec_sweep import registry

REPO_ROOT = Path(__file__).resolve().parents[2]


@asynccontextmanager
async def _no_lifespan(_app):
    yield


def _app(tmp_path: Path, product: ProductContribution | None = None):
    app = api_main.create_app(fixture_context(tmp_path), lifespan=_no_lifespan, product=product)
    app.openapi()  # builds the included routers' route contexts, as the first request does
    return app


def _sample(template: str) -> str:
    return re.sub(r"\{[^}]+\}", "x1", re.sub(r"\{[^}:]+:path\}", "a/b", template))


def _resolve(app, method: str, path: str):
    """The endpoint the app dispatches ``method path`` to, following included routers in order."""
    scope = {
        "type": "websocket" if method == "WEBSOCKET" else "http",
        "path": path,
        "method": "GET" if method == "WEBSOCKET" else method,
        "root_path": "",
        "query_string": b"",
        "headers": [],
    }
    for route in app.router.routes:
        match, _ = route.matches(scope)
        if match != Match.FULL:
            continue
        while isinstance(route, _IncludedRouter):
            match, _, route, _ = route._match(scope)
            if match != Match.FULL or route is None:
                return None
        return getattr(route, "endpoint", None)
    return None


def _declared(app) -> dict[tuple[str, str], object]:
    """Each mounted method and full path template, mapped to the endpoint that declares it."""
    declared: dict[tuple[str, str], object] = {}
    for top in app.router.routes:
        contexts = top.effective_route_contexts() if isinstance(top, _IncludedRouter) else [top]
        for context in contexts:
            route = getattr(context, "original_route", context)
            path = getattr(context, "path", None) or getattr(getattr(context, "starlette_route", None), "path", None)
            path = registry.normalize_path_template(path or route.path)
            for method in getattr(context, "methods", None) or ["WEBSOCKET"]:
                declared.setdefault((method, path), getattr(route, "endpoint", None))
    return declared


def _operations(app) -> set[tuple[str, str]]:
    return {(op.method, op.path_template) for _, op in registry._walk_routes(app)}


def test_every_route_resolves_to_its_own_endpoint_and_matches_the_frozen_route_set(tmp_path: Path) -> None:
    app = _app(tmp_path)
    operations = _operations(app)
    http = [registry.Operation(method, path) for method, path in operations if method != "WEBSOCKET"]
    websockets = [registry.Operation(method, path) for method, path in operations if method == "WEBSOCKET"]
    assert len(http) == registry.FROZEN_HTTP_OPERATION_COUNT
    assert registry.denominator_digest(http, websockets) == registry.FROZEN_DENOMINATOR_SHA256

    declared = _declared(app)
    shadowed = [
        (method, template)
        for method, template in sorted(operations)
        if declared.get((method, template)) is None or _resolve(app, method, _sample(template)) is not declared[(method, template)]
    ]
    assert shadowed == []


def test_product_routes_come_from_product_modules_and_machinery_routes_from_machinery(tmp_path: Path) -> None:
    full = _app(tmp_path / "full")
    machinery = _app(tmp_path / "machinery", product=EMPTY)
    product_only = _operations(full) - _operations(machinery)
    assert product_only, "the product contribution mounted no routes"
    declared = _declared(full)
    for method, template in sorted(_operations(full)):
        module = getattr(declared.get((method, template)), "__module__", "")
        if (method, template) in product_only:
            assert module.startswith("scripts.project_api."), (method, template, module)
        elif template != "/{path:path}":
            assert not module.startswith("scripts.project_api."), (method, template, module)
    # Hramatka moves as product code but stays unmounted.
    assert not any(template.startswith("/api/hramatka") for _, template in _operations(full))


PRODUCT_STATIC = REPO_ROOT / "scripts" / "project_api" / "static"


def _pages() -> list[tuple[str, Path]]:
    machinery = REPO_ROOT / "dashboards"
    rows = [(path.relative_to(machinery).as_posix(), path) for path in machinery.rglob("*") if path.is_file()]
    rows += [(path.relative_to(PRODUCT_STATIC).as_posix(), path) for path in PRODUCT_STATIC.rglob("*") if path.is_file()]
    return sorted(rows)


@pytest.mark.parametrize(("page", "source"), _pages(), ids=[page for page, _ in _pages()])
def test_every_dashboard_page_loads_from_its_owner(tmp_path: Path, page: str, source: Path) -> None:
    ctx = fixture_context(tmp_path).with_roots(dashboards_dir=REPO_ROOT / "dashboards")
    app = api_main.create_app(ctx, lifespan=_no_lifespan)
    with TestClient(app) as client:
        response = client.get(f"/{page}")
        assert response.status_code == 200
        assert response.content == source.read_bytes()
        if page.endswith(".html") and "/" not in page:
            assert client.get(f"/{page.removesuffix('.html')}").content == response.content
        if page == "index.html":
            assert client.get("/").content == response.content


def test_product_static_map_is_explicit_complete_and_disjoint_from_machinery_pages() -> None:
    from scripts.project_api import entry

    declared = set(entry.STATIC_FILES)
    on_disk = {path.relative_to(PRODUCT_STATIC).as_posix() for path in PRODUCT_STATIC.rglob("*") if path.is_file()}
    machinery = {path.relative_to(REPO_ROOT / "dashboards").as_posix() for path in (REPO_ROOT / "dashboards").rglob("*") if path.is_file()}
    assert declared == on_disk
    assert declared.isdisjoint(machinery)
    assert len(machinery) == 12 and len(declared) == 13


def test_undeclared_and_escaping_product_files_are_not_served(tmp_path: Path, monkeypatch) -> None:
    product = load_product(fixture_context(tmp_path / "ctx"))
    assert product_contribution.product_file(product, "../entry.py") is None
    assert product_contribution.product_file(product, "entry.py") is None
    assert product_contribution.product_file(product, "orient") == (PRODUCT_STATIC / "orient.html").resolve()

    root = tmp_path / "product"
    (root / "static").mkdir(parents=True)
    outside = tmp_path / "outside.html"
    outside.write_text("outside", encoding="utf-8")
    (root / "static" / "escape.html").symlink_to(outside)
    monkeypatch.setattr(product_contribution.config, "PRODUCT_ROOT", root)
    escaping = ProductContribution(
        static_files={"escape.html": root / "static" / "escape.html", "missing.html": root / "static" / "missing.html"}
    )
    assert product_contribution.product_file(escaping, "escape.html") is None
    assert product_contribution.product_file(escaping, "missing.html") is None


def test_contract_registry_composes_machinery_then_product_declarations(tmp_path: Path) -> None:
    from lu_machinery.api import route_contracts

    from scripts.project_api import route_contracts as product_contracts

    app = _app(tmp_path)
    with TestClient(app) as client:
        body = client.get("/api/contracts/routes").json()
    patterns = [row["pattern"] for row in body["route_contracts"]]
    expected = [c.pattern for c in (*route_contracts.ROUTE_CONTRACTS, *product_contracts.ROUTE_CONTRACTS)]
    assert patterns == expected
    pages = {row["file"] for row in body["page_contracts"]}
    html_pages = {page for page, _ in _pages() if page.endswith(".html")}
    assert html_pages <= pages
    assert route_contracts.contract_for_route("/api/state/preparation").pattern == "/api/state/preparation"


def test_no_machinery_api_module_imports_product_code() -> None:
    sources = {
        path.relative_to(REPO_ROOT).as_posix(): path.read_bytes()
        for package in ("scripts/api", "scripts/project_api")
        for path in (REPO_ROOT / package).rglob("*.py")
    }
    graph = scan_imports(sources)
    forbidden = [
        (importer, target)
        for importer, target in graph["file_edges"]
        if importer.startswith("scripts/api/") and target.startswith("scripts/project_api/")
    ]
    assert forbidden == []


def test_loader_refuses_a_bad_product_root(tmp_path: Path) -> None:
    with pytest.raises(ConfiguredModuleError, match="absolute"):
        load_configured_module("lu_machinery.lib.readonly_sqlite", product_root=Path("relative"))
    with pytest.raises(ConfiguredModuleError, match="no scripts/ directory"):
        load_configured_module("lu_machinery.lib.readonly_sqlite", product_root=tmp_path)
    (tmp_path / "scripts").mkdir()
    with pytest.raises(ConfiguredModuleError, match="not a file in this checkout"):
        load_configured_module("lu_machinery.lib.readonly_sqlite", product_root=tmp_path)
    with pytest.raises(ConfiguredModuleError, match="SQLite"):
        load_configured_module("scripts.sqlite3", product_root=REPO_ROOT)
    assert load_configured_module("lu_machinery.lib.readonly_sqlite", product_root=REPO_ROOT).__name__ == (
        "lu_machinery.lib.readonly_sqlite"
    )


def _product_root(tmp_path: Path, document: object) -> Path:
    data = tmp_path / product_contribution.PRODUCT_DATA
    data.parent.mkdir(parents=True)
    data.write_text(json.dumps(document), encoding="utf-8")
    return tmp_path


def test_load_product_builds_the_configured_contribution_and_refuses_bad_entries(tmp_path: Path) -> None:
    ctx = fixture_context(tmp_path / "ctx")
    product = load_product(ctx)
    assert isinstance(product, ProductContribution)
    assert {"pipeline", "wiki", "governance"} == set(product.orient_sections())

    base = {"schema": product_contribution.PRODUCT_DATA_SCHEMA, "schema_version": 1}
    with pytest.raises(ProductEntryError, match="not a regular file"):
        load_product(ctx, product_root=tmp_path / "missing")
    with pytest.raises(ProductEntryError, match="schema_version"):
        load_product(ctx, product_root=_product_root(tmp_path / "v2", {**base, "schema_version": 2}))
    with pytest.raises(ProductEntryError, match="product_api"):
        load_product(ctx, product_root=_product_root(tmp_path / "none", base))
    foreign = _product_root(tmp_path / "foreign", {**base, "product_api": "scripts.project_api.entry"})
    (foreign / "scripts").mkdir(exist_ok=True)
    with pytest.raises(ProductEntryError, match="refused"):
        load_product(ctx, product_root=foreign)


def test_atlas_provider_is_injected_and_falls_back_to_the_registry_adapter(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(product_contribution, "_atlas", None)
    fallback = product_contribution.atlas_provider()
    assert fallback is not None
    with pytest.raises(LookupError):
        fallback.host_load_entry("host", fresh=False)

    _app(tmp_path)
    from scripts.project_api.atlas_jobs_router import ATLAS_PROVIDER

    assert product_contribution.atlas_provider() is ATLAS_PROVIDER
    assert product_contribution.fleet_batches() is not None
