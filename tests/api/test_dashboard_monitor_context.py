"""#7327 step 9: dashboard family reads roots/stores via MonitorContext."""

from __future__ import annotations

import inspect
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scripts.api import dashboard_comms, dashboard_helpers, dashboard_router
from scripts.api import main as api_main
from scripts.api.monitor_context import fixture_context

pytestmark = pytest.mark.repo_invariant

DASHBOARD_MODULES = (dashboard_router, dashboard_helpers, dashboard_comms)


def _absolute_path_globals(module) -> list[str]:
    return sorted(
        name
        for name, value in vars(module).items()
        if isinstance(value, Path) and value.is_absolute()
    )


@asynccontextmanager
async def _no_lifespan(_app):
    yield


def test_dashboard_family_has_no_absolute_path_globals() -> None:
    leaked = {
        module.__name__: names
        for module in DASHBOARD_MODULES
        if (names := _absolute_path_globals(module))
    }
    assert leaked == {}


def test_dashboard_routes_inject_monitor_context() -> None:
    for route in dashboard_router.router.routes:
        endpoint = getattr(route, "endpoint", None)
        if endpoint is None:
            continue
        params = inspect.signature(endpoint).parameters
        assert "ctx" in params or "_ctx" in params, route.path


def test_overview_last_good_path_uses_context_project_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(dashboard_router.DASHBOARD_OVERVIEW_LAST_GOOD_ENV, raising=False)
    ctx = fixture_context(tmp_path)
    path = dashboard_router.overview_last_good_path(ctx)
    assert path == ctx.roots.project_root / ".cache" / "dashboard_overview_last_good.json"
    assert path.is_relative_to(tmp_path)


def test_module_detail_reads_curriculum_from_context(tmp_path: Path) -> None:
    ctx = fixture_context(tmp_path)
    track_dir = ctx.roots.curriculum_root / "a1"
    status_dir = track_dir / "status"
    status_dir.mkdir(parents=True)
    (status_dir / "hello.json").write_text('{"overall": {"status": "pass"}}', encoding="utf-8")

    import asyncio
    from unittest.mock import patch

    with (
        patch.object(dashboard_router, "LEVELS", [{"id": "a1", "path": "a1"}]),
        patch.object(dashboard_router, "read_yaml_file", lambda _path: None),
        patch.object(dashboard_router, "find_research_path", lambda _track_dir, _slug: None),
        patch.object(dashboard_router, "default_research_info", lambda _track: {"exists": False}),
        patch.object(
            dashboard_router,
            "extract_review_info",
            lambda _track_dir, _slug: {
                "review_score": None,
                "review_verdict": None,
                "plan_review_verdict": None,
            },
        ),
        patch.object(dashboard_router, "get_orchestration_info", lambda _orch_dir: {}),
    ):
        result = asyncio.run(dashboard_router.module_detail("a1", "hello", ctx=ctx))

    assert result["status"] == {"overall": {"status": "pass"}}
    assert result["slug"] == "hello"
    assert result["track"] == "a1"


def test_comms_and_pipeline_isolate_to_fixture_context(tmp_path: Path) -> None:
    first = fixture_context(tmp_path / "first")
    second = fixture_context(tmp_path / "second")

    first_stuck = first.roots.curriculum_root / "stuck"
    first_stuck.mkdir(parents=True)
    (first_stuck / "only-first.md").write_text("first stuck task", encoding="utf-8")
    first.roots.batch_state_dir.mkdir(parents=True, exist_ok=True)
    (first.roots.batch_state_dir / "dispatcher_state.json").write_text(
        '{"owner": "first"}', encoding="utf-8"
    )

    second_stuck = second.roots.curriculum_root / "stuck"
    second_stuck.mkdir(parents=True)
    (second_stuck / "only-second.md").write_text("second stuck task", encoding="utf-8")
    second.roots.batch_state_dir.mkdir(parents=True, exist_ok=True)
    (second.roots.batch_state_dir / "dispatcher_state.json").write_text(
        '{"owner": "second"}', encoding="utf-8"
    )

    first_app = api_main.create_app(first, lifespan=_no_lifespan)
    second_app = api_main.create_app(second, lifespan=_no_lifespan)

    with TestClient(first_app) as first_client, TestClient(second_app) as second_client:
        first_comms = first_client.get("/api/dashboard/comms")
        second_comms = second_client.get("/api/dashboard/comms")
        assert first_comms.status_code == 200
        assert second_comms.status_code == 200
        first_ids = {row["task_id"] for row in first_comms.json()["stuck_tasks"]}
        second_ids = {row["task_id"] for row in second_comms.json()["stuck_tasks"]}
        assert first_ids == {"only-first"}
        assert second_ids == {"only-second"}

        first_pipeline = first_client.get("/api/dashboard/pipeline")
        second_pipeline = second_client.get("/api/dashboard/pipeline")
        assert first_pipeline.status_code == 200
        assert second_pipeline.status_code == 200
        assert first_pipeline.json()["dispatcher_state"] == {"owner": "first"}
        assert second_pipeline.json()["dispatcher_state"] == {"owner": "second"}

        activity = first_client.get("/api/dashboard/activity-config")
        assert activity.status_code == 200
        body = activity.json()
        assert "types" in body
        assert "levels" in body
        assert "restrictions" in body
