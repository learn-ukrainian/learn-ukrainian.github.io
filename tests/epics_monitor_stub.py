"""Loopback Monitor epics stub for subprocess launcher acceptance tests."""

from __future__ import annotations

import socket
import time
from collections.abc import Iterator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import replace
from pathlib import Path
from threading import Thread
from urllib.request import urlopen

import uvicorn
from fastapi import FastAPI

from agents_extensions.shared.session_streams.store import SessionStreamStore
from scripts.api.main import create_app
from scripts.api.monitor_context import fixture_context


@asynccontextmanager
async def _stub_lifespan(_app: FastAPI):
    """No schedulers / inventory seed — acceptance stubs only need the router."""
    yield


def epics_app_for_store(
    store: SessionStreamStore,
    root: Path,
    *,
    live_repo_root: Path | None = None,
) -> FastAPI:
    """Build a create_app() Monitor instance whose epics routes read ``store``.

    Goes through ``create_app`` so OPSEC path-sanitizer middleware (and the
    rest of the production stack) actually runs — the prior bare-FastAPI
    bypass was #7494 item 4.8a.
    """
    ctx = fixture_context(root)
    if live_repo_root is not None:
        ctx = ctx.with_roots(live_repo_root=Path(live_repo_root))
    ctx = replace(ctx, stores=replace(ctx.stores, epics_store=store))
    return create_app(ctx, lifespan=_stub_lifespan)


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
