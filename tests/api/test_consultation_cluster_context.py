"""#7269 step 12b: consultation / delegate / discussions cluster uses MonitorContext."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from scripts.api.main import create_app
from scripts.api.monitor_context import fixture_context


def test_gold_active_orchestration_empty_when_curriculum_missing(tmp_path: Path) -> None:
    """A fixture context with no curriculum tree returns the documented empty list."""
    client = TestClient(create_app(fixture_context(tmp_path)))
    response = client.get("/api/gold/active-orchestration")
    assert response.status_code == 200
    assert response.json() == []
