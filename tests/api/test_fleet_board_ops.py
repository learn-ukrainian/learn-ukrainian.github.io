"""Operations sources for fleet board v1. Fixtures and mocked HTTP only."""

from __future__ import annotations

import threading
import time
import urllib.parse
import urllib.request

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

import scripts.api.fleet_board.router as board_routes
from scripts.api import main as api_main
from scripts.api.fleet_board import http_sources, values
from scripts.api.fleet_board import sources as sources_mod
from scripts.api.fleet_board.cache import CACHE
from scripts.api.fleet_board.fetch import _DeadlineRedirect, fetch_json

client = TestClient(api_main.app, raise_server_exceptions=False)

_QUERIES = {
    "fleet_disk_used_percent",
    "fleet_memory_used_percent",
    "fleet_drivers_live",
    "fleet_api_probe_up",
}


@pytest.fixture(autouse=True)
def _isolated(monkeypatch: pytest.MonkeyPatch):
    CACHE.clear()
    for name in sources_mod.LOCATION_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("FLEET_DOWNLOAD_STALL_MIN", raising=False)
    yield
    CACHE.clear()


def _with_userinfo(host: str, tail: str = "") -> str:
    return "https://" + "user" + ":" + "userinfo-token" + "@" + host + tail


def _validate(body: dict) -> None:
    document = client.get("/api/fleet/v1/schema").json()["data"]["endpoints"][body["schema"]]
    Draft202012Validator(document).validate(body)


def _source(body: dict) -> dict:
    name = body["schema"].removeprefix("fleet.v1.")
    matching = [source for source in body["sources"] if source["name"] == name]
    assert len(matching) == 1
    return matching[0]


class _Body:
    def __init__(self, payload: bytes, status: int = 200) -> None:
        self._payload = payload
        self._sent = False
        self.status = status

    def read(self, _size: int) -> bytes:
        if self._sent:
            return b""
        self._sent = True
        return self._payload

    def __enter__(self) -> _Body:
        return self

    def __exit__(self, *_args: object) -> bool:
        return False


def test_fetch_caps_timeout_and_rejects_other_schemes() -> None:
    seen: dict[str, object] = {}

    def opener(request, timeout):
        seen["timeout"] = timeout
        seen["url"] = request.full_url
        return _Body(b"[]")

    assert fetch_json(_with_userinfo("metrics.example", "/v1"), timeout_s=30, opener=opener) == []
    assert seen["timeout"] == pytest.approx(2.0, abs=0.05)
    assert seen["url"] == "https://metrics.example/v1"
    with pytest.raises(ValueError):
        fetch_json("ftp://metrics.example/v1", opener=opener)
    assert seen["url"] == "https://metrics.example/v1"


def test_fetch_returns_when_the_body_stalls() -> None:
    started = threading.Event()
    release = threading.Event()

    def opener(request, timeout):
        class Slow:
            status = 200

            def read(self, _size: int) -> bytes:
                started.set()
                release.wait(5)
                return b"[]"

            def __enter__(self) -> Slow:
                return self

            def __exit__(self, *_args: object) -> bool:
                return False

        return Slow()

    try:
        began = time.monotonic()
        with pytest.raises(TimeoutError):
            fetch_json("https://metrics.example/v1", timeout_s=0.05, opener=opener)
        assert time.monotonic() - began < 0.5
        assert started.is_set()
    finally:
        release.set()


def test_redirect_stops_at_the_deadline_and_drops_userinfo() -> None:
    request = urllib.request.Request("https://metrics.example/v1")
    expired = _DeadlineRedirect(time.monotonic() - 0.01)
    with pytest.raises(TimeoutError):
        expired.redirect_request(request, None, 302, "found", {}, "https://metrics.example/next")
    live = _DeadlineRedirect(time.monotonic() + 5)
    redirected = live.redirect_request(
        request,
        None,
        302,
        "found",
        {},
        _with_userinfo("metrics.example", "/next"),
    )
    assert redirected.full_url == "https://metrics.example/next"
    with pytest.raises(ValueError):
        live.redirect_request(request, None, 302, "found", {}, "ftp://metrics.example/next")


def test_unset_sources_are_not_configured_and_do_not_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode(*_args, **_kwargs):
        raise AssertionError("fetch")

    monkeypatch.setattr(http_sources, "fetch_json", explode)
    paths = (
        ("/api/fleet/v1/alerts", "alerts", "fleet.v1.alerts"),
        ("/api/fleet/v1/stats", "stats", "fleet.v1.stats"),
        ("/api/fleet/v1/links", "links", "fleet.v1.links"),
    )
    for path, source, schema in paths:
        response = client.get(path)
        assert response.status_code == 200
        body = response.json()
        assert body["schema"] == schema
        assert _source(body) == {"name": source, "status": "not_configured", "age_s": None, "error": None}
        _validate(body)


def test_blank_alert_location_is_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FLEET_ALERTMANAGER_URL", "   ")
    response = client.get("/api/fleet/v1/alerts")
    assert response.status_code == 200
    assert _source(response.json())["status"] == "not_configured"


def test_index_does_not_read_a_configured_location(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode(*_args, **_kwargs):
        raise AssertionError("fetch")

    monkeypatch.setattr(http_sources, "fetch_json", explode)
    monkeypatch.setenv("FLEET_ALERTMANAGER_URL", "https://alerts.example")
    response = client.get("/api/fleet/v1")
    assert response.status_code == 200
    alerts = next(item for item in response.json()["sources"] if item["name"] == "alerts")
    assert alerts["status"] == "ok"
    assert "alerts.example" not in response.text


def test_alerts_keep_only_sanitised_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    def fetch(url, **_kwargs):
        assert url == "https://alerts.example/api/v2/alerts"
        return [
            {
                "labels": {
                    "alertname": "DiskSpace",
                    "severity": "Warning",
                    "instance": "host-token.example",
                },
                "annotations": {"summary": "Low space https://host-token.example/item now"},
                "startsAt": "2026-10-09T09:00:00Z",
                "generatorURL": "https://host-token.example/graph",
                "status": {"state": "active", "silencedBy": ["x"]},
            },
            "skip",
        ]

    monkeypatch.setattr(http_sources, "fetch_json", fetch)
    monkeypatch.setenv("FLEET_ALERTMANAGER_URL", "https://alerts.example")
    response = client.get("/api/fleet/v1/alerts")
    assert response.status_code == 200
    body = response.json()
    _validate(body)
    assert _source(body)["status"] == "ok"
    assert body["data"]["alerts"] == [
        {
            "name": "DiskSpace",
            "severity": "warning",
            "summary": "Low space now",
            "starts_at": "2026-10-09T09:00:00Z",
            "state": "active",
        }
    ]
    assert "host-token" not in response.text


def _address() -> str:
    return ":".join(("2001", "db8", "0", "0", "0", "0", "0", "17"))


def _measure() -> str:
    return "12" + "GiB"


def test_alerts_publish_only_approved_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    marker = "leak-token"
    host = f"{marker}.example"
    address = _address()
    path = "/" + "srv" + "/" + marker
    measure = _measure()

    def fetch(_url, **_kwargs):
        return [
            {
                "labels": {"alertname": "DiskSpace", "severity": "warning"},
                "annotations": {"summary": f"Queue delay {host} {address} {path} {measure} remains"},
                "startsAt": "2026-10-09T09:00:00Z",
                "status": {"state": "active"},
            },
            {"labels": {"alertname": host}, "annotations": {"summary": "Plain words"}, "status": {"state": "active"}},
            {
                "labels": {"alertname": address},
                "annotations": {"summary": "Plain words"},
                "status": {"state": "active"},
            },
            {"labels": {"alertname": path}, "annotations": {"summary": "Plain words"}, "status": {"state": "active"}},
            {
                "labels": {"alertname": "Node" + measure},
                "annotations": {"summary": "Plain words"},
                "status": {"state": "active"},
            },
        ]

    monkeypatch.setattr(http_sources, "fetch_json", fetch)
    monkeypatch.setenv("FLEET_ALERTMANAGER_URL", "https://alerts.example")
    response = client.get("/api/fleet/v1/alerts")
    assert response.status_code == 200
    body = response.json()
    _validate(body)
    assert body["data"]["alerts"][0] == {
        "name": "DiskSpace",
        "severity": "warning",
        "summary": "Queue delay remains",
        "starts_at": "2026-10-09T09:00:00Z",
        "state": "active",
    }
    assert [item["name"] for item in body["data"]["alerts"][1:]] == [None, None, None, None]
    assert marker not in response.text
    assert address not in response.text
    assert measure not in response.text


def test_alert_timeout_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    def fetch(_url, **_kwargs):
        raise TimeoutError("slow-token")

    monkeypatch.setattr(http_sources, "fetch_json", fetch)
    monkeypatch.setenv("FLEET_ALERTMANAGER_URL", "https://alerts.example")
    response = client.get("/api/fleet/v1/alerts")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["alerts"] == []
    assert _source(body)["status"] == "unavailable"
    assert "slow-token" not in response.text
    assert "alerts.example" not in response.text


def test_failed_refresh_serves_cached_alerts_as_stale(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def fetch(_url, **_kwargs):
        calls["n"] += 1
        if calls["n"] > 1:
            raise TimeoutError("slow-token")
        return [{"labels": {"alertname": "DiskSpace"}, "annotations": {}, "status": {"state": "active"}}]

    monkeypatch.setattr(http_sources, "fetch_json", fetch)
    monkeypatch.setenv("FLEET_ALERTMANAGER_URL", "https://alerts.example")
    first = client.get("/api/fleet/v1/alerts")
    second = client.get("/api/fleet/v1/alerts")
    assert first.status_code == second.status_code == 200
    assert calls["n"] == 1
    assert _source(second.json())["status"] == "ok"
    monkeypatch.setattr(values, "CACHE_TTL_S", 0)
    third = client.get("/api/fleet/v1/alerts")
    assert third.status_code == 200
    assert calls["n"] == 2
    assert _source(third.json())["status"] == "stale"
    assert third.json()["data"]["alerts"][0]["name"] == "DiskSpace"
    assert "slow-token" not in third.text


def test_loader_bug_stays_http_200(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode():
        raise RuntimeError("boom-token")

    monkeypatch.setattr(board_routes, "load_alerts", explode)
    response = client.get("/api/fleet/v1/alerts")
    assert response.status_code == 200
    body = response.json()
    assert body["schema"] == "fleet.v1.alerts"
    assert body["data"] == {"alerts": []}
    assert _source(body)["status"] == "unavailable"
    assert "boom-token" not in response.text



def _series(raw: str) -> dict:
    return {
        "status": "success",
        "data": {
            "resultType": "vector",
            "result": [{"metric": {"instance": "host-token.example"}, "value": [1, raw]}],
        },
    }


def test_stats_ignore_client_queries_and_isolate_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str] = []

    def fetch(url, **_kwargs):
        assert url.startswith("https://metrics.example/api/v1/query?")
        query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["query"][0]
        seen.append(query)
        if query == "fleet_memory_used_percent":
            return {"status": "error", "error": "hidden-query-token"}
        return _series("4")

    monkeypatch.setattr(http_sources, "fetch_json", fetch)
    monkeypatch.setenv("FLEET_PROMETHEUS_URL", _with_userinfo("metrics.example"))
    response = client.get("/api/fleet/v1/stats", params={"query": "up"})
    assert response.status_code == 200
    body = response.json()
    _validate(body)
    assert _source(body)["status"] == "ok"
    assert [item["name"] for item in body["data"]["stats"]] == [
        "disk_pct",
        "memory_pct",
        "drivers_live",
        "probe_status",
    ]
    by_name = {item["name"]: item for item in body["data"]["stats"]}
    assert by_name["memory_pct"] == {"name": "memory_pct", "value": None, "status": "unavailable"}
    assert by_name["disk_pct"]["value"] == 4
    assert by_name["drivers_live"]["status"] == "ok"
    assert set(seen) == _QUERIES
    assert len(seen) == 4
    assert "up" not in seen
    assert "host-token" not in response.text
    assert "userinfo-token" not in response.text
    assert "hidden-query-token" not in response.text
    assert "metrics.example" not in response.text


def test_stats_transport_failure_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    def fetch(_url, **_kwargs):
        raise TimeoutError("slow-token")

    monkeypatch.setattr(http_sources, "fetch_json", fetch)
    monkeypatch.setenv("FLEET_PROMETHEUS_URL", "https://metrics.example")
    response = client.get("/api/fleet/v1/stats")
    assert response.status_code == 200
    body = response.json()
    _validate(body)
    assert _source(body)["status"] == "unavailable"
    assert all(item["status"] == "unavailable" and item["value"] is None for item in body["data"]["stats"])
    assert "slow-token" not in response.text
    assert "metrics.example" not in response.text


def test_stats_do_not_wait_out_a_slow_query(monkeypatch: pytest.MonkeyPatch) -> None:
    release = threading.Event()

    def fetch(_url, **_kwargs):
        release.wait(1)
        return _series("4")

    monkeypatch.setattr(http_sources, "fetch_json", fetch)
    monkeypatch.setattr(http_sources, "HTTP_TIMEOUT_S", 0.05)
    monkeypatch.setenv("FLEET_PROMETHEUS_URL", "https://metrics.example")
    try:
        started = time.monotonic()
        response = client.get("/api/fleet/v1/stats")
        assert time.monotonic() - started < 0.4
    finally:
        release.set()
    assert response.status_code == 200
    body = response.json()
    _validate(body)
    assert _source(body)["status"] == "unavailable"


def test_stats_application_failure_keeps_a_cached_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    phase = {"fresh": True}

    def fetch(url, **_kwargs):
        query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["query"][0]
        assert query in _QUERIES
        if phase["fresh"]:
            return _series("4")
        return {"status": "error", "error": "hidden-query-token"}

    monkeypatch.setattr(http_sources, "fetch_json", fetch)
    monkeypatch.setenv("FLEET_PROMETHEUS_URL", "https://metrics.example")
    first = client.get("/api/fleet/v1/stats")
    assert _source(first.json())["status"] == "ok"
    assert first.json()["data"]["stats"][0]["value"] == 4
    phase["fresh"] = False
    monkeypatch.setattr(values, "CACHE_TTL_S", 0)
    second = client.get("/api/fleet/v1/stats")
    assert second.status_code == 200
    body = second.json()
    _validate(body)
    assert _source(body)["status"] == "stale"
    assert [item["value"] for item in body["data"]["stats"]] == [4, 4, 4, 4]
    assert "hidden-query-token" not in second.text
    assert "metrics.example" not in second.text


def test_stats_application_failure_without_a_cache_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    def fetch(_url, **_kwargs):
        return {"status": "error", "error": "hidden-query-token"}

    monkeypatch.setattr(http_sources, "fetch_json", fetch)
    monkeypatch.setenv("FLEET_PROMETHEUS_URL", "https://metrics.example")
    response = client.get("/api/fleet/v1/stats")
    assert response.status_code == 200
    body = response.json()
    _validate(body)
    assert _source(body)["status"] == "unavailable"
    assert all(item["value"] is None for item in body["data"]["stats"])
    assert "hidden-query-token" not in response.text


def test_links_are_built_from_the_base_without_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "FLEET_GRAFANA_URL",
        _with_userinfo("boards.example", "/grafana") + "?" + "token" + "=" + "userinfo-token",
    )
    response = client.get("/api/fleet/v1/links")
    assert response.status_code == 200
    body = response.json()
    _validate(body)
    assert _source(body)["status"] == "ok"
    assert body["data"]["links"] == [
        {"name": "overview", "href": "https://boards.example/grafana/d/overview"},
        {"name": "fleet", "href": "https://boards.example/grafana/d/fleet"},
    ]
    assert "userinfo-token" not in response.text


def test_links_reject_a_non_http_base(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FLEET_GRAFANA_URL", "ftp://boards.example/grafana")
    response = client.get("/api/fleet/v1/links")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["links"] == []
    assert _source(body)["status"] == "unavailable"
    assert "boards.example" not in response.text
