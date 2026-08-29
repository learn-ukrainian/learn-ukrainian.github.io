"""Loopback Monitor epics stub for subprocess launcher acceptance tests."""

from __future__ import annotations

import socket
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from threading import Thread
from urllib.request import urlopen

import uvicorn
from fastapi import FastAPI

from agents_extensions.shared.session_streams.store import SessionStreamStore
from scripts.api import epics_router
from scripts.api.monitor_context import fixture_context


def epics_app_for_store(
    store: SessionStreamStore,
    root: Path,
    *,
    live_repo_root: Path | None = None,
) -> FastAPI:
    """Build a FastAPI app whose epics routes read ``store`` via MonitorContext."""
    ctx = fixture_context(root)
    if live_repo_root is not None:
        ctx = replace(ctx, roots=replace(ctx.roots, live_repo_root=Path(live_repo_root)))
    ctx = replace(ctx, stores=replace(ctx.stores, epics_store=store))
    app = FastAPI()
    app.state.ctx = ctx
    app.include_router(epics_router.router, prefix="/api/epics")
    return app


@contextmanager
def epics_monitor_stub(store: SessionStreamStore) -> Iterator[str]:
    """Serve the production epics router on an owned loopback port.

    The router is the same contract exercised in ``tests/api/test_epics_router.py``;
    this wrapper adds a real socket so launcher subprocesses cannot bypass the
    remote lifecycle client with an in-process test adapter.
    """
    app = epics_app_for_store(store, store.database.path.parent)

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = int(probe.getsockname()[1])

    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host="127.0.0.1",
            port=port,
            lifespan="off",
            log_level="error",
        )
    )
    thread = Thread(target=server.run, name="epics-monitor-stub", daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"
    health_url = f"{base_url}/api/epics/v1/health"
    try:
        for _ in range(100):
            try:
                with urlopen(health_url, timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(0.05)
        else:
            raise RuntimeError("Monitor epics stub did not become ready")
        yield base_url
    finally:
        server.should_exit = True
        thread.join(timeout=5)
