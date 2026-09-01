"""Regression coverage for Monitor context construction and shutdown costs."""

from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import replace
from pathlib import Path
from unittest.mock import AsyncMock, Mock

from fastapi.testclient import TestClient

from scripts.api import git_hygiene_router, images_router, monitor_context, wiki_router, work_router
from scripts.api import main as api_main
from scripts.api.monitor_context import fixture_context, production_context


def test_production_context_is_constructed_once_until_cache_clear(monkeypatch) -> None:
    original_build_context = monitor_context._build_context
    build_calls = 0

    def counted_build_context(**kwargs):
        nonlocal build_calls
        build_calls += 1
        return original_build_context(**kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(monitor_context, "_build_context", counted_build_context)
        production_context.cache_clear()
        first = production_context()
        second = production_context()
        assert first is second
        assert build_calls == 1

    # Restore the normal process singleton for tests that use main.app.
    production_context.cache_clear()
    production_context()


def test_epics_and_session_streams_share_one_database_store(monkeypatch, tmp_path: Path) -> None:
    real_database = monitor_context.SessionStreamDatabase
    database_paths: list[Path] = []

    class CountingDatabase(real_database):
        def __init__(self, path=None, **kwargs):
            database_paths.append(Path(path))
            super().__init__(path, **kwargs)

    monkeypatch.setattr(monitor_context, "SessionStreamDatabase", CountingDatabase)
    context = fixture_context(tmp_path)

    assert len(database_paths) == 1
    assert context.stores.epics_database is context.stores.session_streams_database
    assert context.stores.epics_store is context.stores.session_streams_store


def test_policy_exemptions_are_cached_on_the_serving_context(monkeypatch, tmp_path: Path) -> None:
    context = fixture_context(tmp_path)
    policy_doc = context.roots.project_root / "docs" / "best-practices" / "git-hygiene.md"
    policy_doc.parent.mkdir(parents=True)
    policy_doc.write_text("## Exemption paths\n- `wiki/**`\n", encoding="utf-8")

    original_extract = git_hygiene_router._extract_policy_exemptions
    extract_calls = 0

    def counted_extract(path: Path) -> list[str]:
        nonlocal extract_calls
        extract_calls += 1
        return original_extract(path)

    monkeypatch.setattr(git_hygiene_router, "_extract_policy_exemptions", counted_extract)
    git_hygiene_router.compute_git_hygiene(context.roots.live_repo_root, ctx=context)
    git_hygiene_router.compute_git_hygiene(context.roots.live_repo_root, ctx=context)

    assert extract_calls == 1


def test_wiki_article_candidates_are_scanned_once_per_context(monkeypatch, tmp_path: Path) -> None:
    context = fixture_context(tmp_path)
    wiki_dir = tmp_path / "wiki" / "periods"
    wiki_dir.mkdir(parents=True)
    (wiki_dir / "kyivan-rus.md").write_text("# Kyivan Rus\n", encoding="utf-8")
    monkeypatch.setattr(wiki_router.wiki_state, "load_progress", lambda: {"articles": {}})

    original_build = wiki_router._build_article_candidates
    build_calls = 0

    def counted_build(path: Path):
        nonlocal build_calls
        build_calls += 1
        return original_build(path)

    monkeypatch.setattr(wiki_router, "_build_article_candidates", counted_build)
    first = wiki_router._list_article_candidates(context)
    second = wiki_router._list_article_candidates(context)

    assert first is second
    assert first["kyivan-rus"][0]["path"] == "periods/kyivan-rus.md"
    assert build_calls == 1


def test_image_store_fallback_is_context_scoped_and_warm(monkeypatch, tmp_path: Path) -> None:
    context = fixture_context(tmp_path)
    context_without_store = replace(
        context,
        stores=replace(context.stores, image_store=None),
    )
    real_image_store = images_router.ImageStore
    create_calls = 0

    def counted_image_store(**kwargs):
        nonlocal create_calls
        create_calls += 1
        return real_image_store(**kwargs)

    monkeypatch.setattr(images_router, "ImageStore", counted_image_store)
    first = images_router._resolve_image_store(context_without_store)
    second = images_router._resolve_image_store(context_without_store)

    assert first is second
    assert first.index is second.index
    assert create_calls == 1


def test_lifespan_closes_context_resources_for_repeated_apps(monkeypatch, tmp_path: Path) -> None:
    for name in ("preload_all", "install_signal_logging", "ensure_broker_db_ready", "seed_manifest_inventory"):
        monkeypatch.setattr(api_main, name, Mock())
    monkeypatch.setattr(api_main.isa, "schedule_refresh", Mock())
    # CF finding (PR #7571): a bare Mock left _WORKER_LOOP unexercised across
    # repeated lifecycles. Start the real worker loop (without queueing a
    # build) so each lifespan exit must actually drain and stop it.
    monkeypatch.setattr(
        api_main,
        "warm_projection_cache",
        lambda *_a, **_k: work_router._ensure_worker_loop(),
    )
    monkeypatch.setattr(api_main, "start_periodic_refresh", Mock())
    monkeypatch.setattr(api_main, "stop_periodic_refresh", Mock())

    resources: list[AsyncMock] = []
    for index in range(2):
        context = fixture_context(tmp_path / f"app-{index}")
        resource = AsyncMock()
        context = replace(context, stores=replace(context.stores, image_store=resource))
        resources.append(resource)
        app = api_main.create_app(context)
        with TestClient(app):
            pass

    for resource in resources:
        resource.close.assert_awaited_once_with()


def test_lifespan_drains_projection_work_and_stops_worker_thread(monkeypatch, tmp_path: Path) -> None:
    work_router.shutdown_worker_loop()
    context = fixture_context(tmp_path)

    async def completed_build(*_args, **_kwargs):
        return {"items": []}

    monkeypatch.setattr(work_router, "_run_build_job", completed_build)
    handle = work_router._ensure_in_flight("ctx-cost-test", {}, context)

    start = time.monotonic()
    asyncio.run(work_router.drain_context_background_work(context, timeout_s=5.0))
    elapsed = time.monotonic() - start

    assert handle.done()
    # CF finding (PR #7571): the generous timeout_s previously absorbed a
    # shutdown hang. With completed in-flight work, drain must be fast.
    assert elapsed < 1.0, f"drain took {elapsed:.2f}s — shutdown stall regressed"
    assert not any(
        thread.name == "work-proj-loop" and thread.is_alive()
        for thread in threading.enumerate()
    )
