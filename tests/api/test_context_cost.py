"""Regression coverage for Monitor context construction and shutdown costs."""

from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import replace
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

from scripts.api import main as api_main
from scripts.api import work_router
from scripts.api.monitor_context import fixture_context

pytestmark = pytest.mark.reads_content


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
