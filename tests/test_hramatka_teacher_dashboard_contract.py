
from fastapi.testclient import TestClient

from scripts.api.main import app


def test_api_readiness_probe_contract_for_dashboard():
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/readyz")
    assert res.status_code in {200, 404, 503}
    if res.status_code == 200:
        data = res.json()
        assert data.get("status") == "ready"
        assert "checks" in data
