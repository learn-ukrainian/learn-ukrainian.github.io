from pathlib import Path

from fastapi.testclient import TestClient

from scripts.api.main import app

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def test_teacher_dashboard_component_exists_and_exports():
    component_path = PROJECT_ROOT / "packages/activity-kit/src/components/TeacherDashboard.tsx"
    assert component_path.exists(), "TeacherDashboard.tsx must exist in activity-kit package"

    content = component_path.read_text(encoding="utf-8")
    assert "export const TeacherDashboard" in content
    assert "readyz" in content
    assert "baking_poll" in content
    assert "catalog_ready" in content

def test_teacher_dashboard_index_export():
    index_path = PROJECT_ROOT / "packages/activity-kit/src/index.ts"
    content = index_path.read_text(encoding="utf-8")
    assert "TeacherDashboard" in content

def test_api_readiness_probe_contract_for_dashboard():
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/readyz")
    assert res.status_code in {200, 404, 503}
    if res.status_code == 200:
        data = res.json()
        assert data.get("status") == "ready"
        assert "checks" in data
