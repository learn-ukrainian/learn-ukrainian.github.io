"""Installed Monitor must compose fleet and product drill routes in one process.

The child inspects the very app it serves, before starting uvicorn. No public
origin-debug endpoint exists. Only the context is replaced with fixture stores;
routers and handlers are the configured installed app's real contribution.
Lifespan is disabled to avoid background refreshes and external services.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener

import pytest

pytestmark = pytest.mark.reads_content

# Packet step 7: fleet routes first, then the product contribution.
ROUTES = {
    "/api/comms/health": ("lu_machinery.api.comms_router", {"db_exists": bool, "queue_depth": int}),
    "/api/fleet/health": ("lu_machinery.api.fleet_router", {"observer": str, "read_only": bool}),
    "/api/delegate/tasks": ("lu_machinery.api.delegate_router", {"tasks": list}),
    "/api/session-streams/v1/health": ("lu_machinery.api.session_streams_router", {"ok": bool, "store": dict}),
    "/api/rules": ("lu_machinery.api.rules_router", {}),
    "/api/consultation/queue": ("scripts.project_api.consultation_router", {"pending": list, "count": int}),
    "/api/atlas-jobs/health": ("scripts.project_api.atlas_jobs_router", {"ok": bool, "schema": str}),
    "/api/sources/stats": ("scripts.project_api.sources_router", {"sources_db": dict}),
    "/api/analytics/cost": ("scripts.project_api.cost_router", {"scope": dict, "windows": dict}),
}

_CHILD = """
import inspect
import json
import sys
from pathlib import Path

import uvicorn
from lu_machinery.api.main import app
from lu_machinery.api.monitor_context import fixture_context

app.state.ctx = fixture_context(Path(sys.argv[1]))
paths = json.loads(sys.argv[4])
# FastAPI wraps each include_router in an included router whose own entry has
# no path; its effective route contexts carry the full path and the endpoint.
routes = []
for top in app.router.routes:
    contexts = top.effective_route_contexts() if hasattr(top, 'effective_route_contexts') else [top]
    for context in contexts:
        route = getattr(context, 'original_route', context)
        routes.append((getattr(context, 'path', None) or getattr(route, 'path', None), route))
origins = {}
for path in paths:
    matches = [route for route_path, route in routes
               if route_path == path and 'GET' in (getattr(route, 'methods', None) or ())]
    assert len(matches) == 1, (path, len(matches))
    endpoint = inspect.unwrap(matches[0].endpoint)
    origins[path] = {'module': endpoint.__module__, 'file': inspect.getfile(endpoint)}
Path(sys.argv[2]).write_text(json.dumps(origins), encoding='utf-8')
uvicorn.run(app, fd=int(sys.argv[3]), lifespan='off', log_level='warning')
"""


def test_installed_monitor_does_not_drop_or_shadow_drill_routes(tmp_path: Path, record_property) -> None:
    """Catch missing product mounts and checkout machinery shadowing the release."""
    try:
        release = distribution("lu-machinery")
    except PackageNotFoundError:
        if os.environ.get("CI"):
            pytest.fail("CI must install the locked lu-machinery release for this integration test")
        pytest.skip("requires the installed lu-machinery release")

    checkout = Path(__file__).resolve().parents[2]
    # A fresh primary checkout as the state fixture, not a clone or linked worktree. The
    # release refuses a configured primary whose .git is not a real Git directory (0.1.6).
    state = tmp_path / "state"
    subprocess.run(
        ["git", "init", "-q", str(state)],
        check=True,
        env={key: value for key, value in os.environ.items() if not key.startswith("GIT_")},
        timeout=30,
    )
    origins_path = tmp_path / "origins.json"
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("LEARN_UK", "LU_", "PYTHON", "BACKUP_", "AB_DB_"))
    }
    env.update(
        {
            "LU_PRODUCT_ROOT": str(checkout),
            "LEARN_UKRAINIAN_PRIMARY_REPO_ROOT": str(state),
            "LEARN_UKRAINIAN_STATE_ROOT": str(state),
            "LEARN_UKRAINIAN_CP_AUTHORITY": "sqlite",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    opener = build_opener(ProxyHandler({}))
    with socket.socket() as listener, (tmp_path / "server.log").open("w+") as log:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        assert port != 8765
        child = subprocess.Popen(
            [
                sys.executable,
                "-P",
                "-c",
                _CHILD,
                str(state),
                str(origins_path),
                str(listener.fileno()),
                json.dumps(list(ROUTES)),
            ],
            cwd=tmp_path,
            env=env,
            pass_fds=(listener.fileno(),),
            stdout=log,
            stderr=log,
        )
        try:
            deadline = time.monotonic() + 60
            while True:
                if child.poll() is not None:
                    log.seek(0)
                    pytest.fail(f"installed Monitor exited before readiness:\n{log.read()}")
                try:
                    with opener.open(f"http://127.0.0.1:{port}/api/session-streams/v1/health", timeout=1):
                        break
                except (URLError, TimeoutError):
                    if time.monotonic() >= deadline:
                        pytest.fail("installed Monitor did not become ready within 60 seconds")
                    time.sleep(0.1)

            origins = json.loads(origins_path.read_text(encoding="utf-8"))
            installed_files = {Path(release.locate_file(path)).resolve() for path in release.files or ()}
            for path, (module, shape) in ROUTES.items():
                origin = origins[path]
                assert origin["module"] == module, (path, origin)
                source = Path(origin["file"]).resolve()
                if module.startswith("lu_machinery."):
                    assert source in installed_files, (path, origin)
                    # Not the checkout's in-tree copy; a venv inside the checkout (CI) is the release.
                    assert not source.is_relative_to(checkout / "scripts"), (path, origin)
                else:
                    assert source == checkout / Path(*module.split(".")).with_suffix(".py"), (path, origin)
                record_property(f"origin:{path}", json.dumps(origin, sort_keys=True))
                with opener.open(f"http://127.0.0.1:{port}{path}", timeout=20) as response:
                    assert response.status == 200, path
                    if path == "/api/rules":
                        assert response.headers["X-Rules-Scope"] == "core"
                        assert response.headers["Content-Type"].startswith("text/markdown")
                        assert response.read().decode("utf-8").strip()
                        continue
                    body = json.load(response)
                assert isinstance(body, dict), path
                if path in {"/api/session-streams/v1/health", "/api/atlas-jobs/health"}:
                    assert body["ok"] is True, path
                if path == "/api/fleet/health":
                    assert body["observer"] == "fleet-comms-v1"
                    assert body["read_only"] is True
                for key, expected_type in shape.items():
                    assert key in body and isinstance(body[key], expected_type), (path, key, body)
        finally:
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
