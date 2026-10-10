"""Who-is-doing-what routes for the fleet board."""

from __future__ import annotations

import ast
import inspect
import json
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from scripts.api import main as api_main
from scripts.api.fleet_board import activity as activity_mod
from scripts.api.fleet_board import router as router_mod
from scripts.api.fleet_board import sources as sources_mod
from scripts.api.fleet_board import view as view_mod
from scripts.api.fleet_board.sources import report

client = TestClient(api_main.app, raise_server_exceptions=False)
FROZEN = datetime(2026, 10, 9, 12, 0, 0, tzinfo=UTC)
FRESH = "2026-10-09T11:59:40Z"
SCREEN = "busy compiling output"


@pytest.fixture(autouse=True)
def _isolated(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in sources_mod.LOCATION_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    for name in ("FLEET_GITHUB_REPO", "GH_REPO", "GITHUB_REPOSITORY", "FLEET_PR_STALE_MIN"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(view_mod, "utc_now", lambda: FROZEN)
    monkeypatch.setattr(view_mod, "load_delegate_health", lambda: report("delegate", "ok"))
    monkeypatch.setattr(view_mod, "load_occupancy_activity", lambda: (report("occupancy", "ok"), {}))


def _write(path, payload) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _roster() -> dict:
    return {
        "generated_at": FRESH,
        "interval_s": 30,
        "epics": [
            {
                "epic": "alpha",
                "title": "Alpha",
                "focus": "seeds",
                "parent": None,
                "layer": 0,
                "intended": "running",
                "since": "2026-10-09T11:00:00Z",
                "driver": {
                    "agent_id": "driver-alpha",
                    "cli": "codex",
                    "model": "model-a",
                    "harness": "codex",
                    "pid_alive": True,
                    "pane_text": SCREEN,
                },
                "task": {"kind": "issue", "number": 11, "title": "alpha task"},
                "workers": [
                    {
                        "agent_id": "worker-alpha",
                        "cli": "codex",
                        "model": "model-b",
                        "task": "alpha work",
                        "activity": "working",
                        "pid_alive": True,
                        "since": "2026-10-09T11:10:00Z",
                    }
                ],
            },
            {
                "epic": "beta",
                "title": "Beta",
                "layer": 1,
                "intended": "running",
                "since": "2026-10-09T11:17:00Z",
                "driver": {
                    "agent_id": "driver-beta",
                    "cli": "codex",
                    "model": "model-a",
                    "harness": "codex",
                    "pid_alive": True,
                    "activity": "idle",
                    "idle_min": 6,
                },
                "task": {"kind": "issue", "number": 12, "title": "beta task"},
                "workers": [],
            },
            {
                "epic": "gamma",
                "title": "Gamma",
                "layer": 1,
                "intended": "running",
                "since": "2026-10-09T10:00:00Z",
                "driver": {
                    "agent_id": "driver-gamma",
                    "cli": "codex",
                    "model": "model-a",
                    "harness": "codex",
                    "pid_alive": True,
                },
                "task": {"kind": "pr", "number": 13, "title": "gamma change"},
                "workers": [],
            },
            {
                "epic": "delta",
                "title": "Delta",
                "layer": 0,
                "intended": "running",
                "since": "2026-10-09T09:00:00Z",
                "driver": {
                    "agent_id": "driver-delta",
                    "cli": "codex",
                    "model": "model-a",
                    "harness": "codex",
                    "pid_alive": True,
                    "activity": "working",
                    "pane_text": SCREEN,
                },
                "task": {"kind": "issue", "number": 14, "title": "delta task"},
                "workers": [],
            },
            {
                "epic": "theta",
                "title": "Theta",
                "layer": 0,
                "intended": "running",
                "since": "2026-10-09T08:00:00Z",
                "driver": {
                    "agent_id": "driver-theta",
                    "cli": "codex",
                    "model": "model-a",
                    "harness": "codex",
                    "pid_alive": False,
                    "pane_text": SCREEN,
                },
                "task": {"kind": "none", "number": 0, "title": "ignored"},
                "workers": [],
            },
            {
                "epic": "epsilon",
                "title": "Epsilon",
                "layer": 1,
                "intended": "paused",
                "since": "2026-10-09T11:10:00Z",
                "driver": None,
                "task": None,
                "workers": [],
            },
            {
                "epic": "zeta",
                "title": "Zeta",
                "layer": 2,
                "intended": "postponed",
                "workers": [],
            },
            {
                "epic": "eta",
                "title": "Eta",
                "intended": "running",
                "driver": {
                    "agent_id": "driver-eta",
                    "cli": "codex",
                    "model": "model-a",
                    "harness": "codex",
                },
                "workers": [],
            },
        ],
        "bots": [
            {
                "agent_id": "bot-check",
                "task": "waiting",
                "activity": "idle",
                "pid_alive": True,
                "last_seen": "2026-10-09T11:40:00Z",
            },
            {
                "agent_id": "bot-sweep",
                "task": "running check",
                "activity": "working",
                "pid_alive": True,
                "last_seen": "2026-10-09T11:50:00Z",
            },
        ],
        "foundations": [
            {"foundation": "queue", "red": True, "reasons": ["held"]},
            {"foundation": "mainline", "red": False, "reasons": ["clear"]},
            {"foundation": "unnamed", "reasons": ["missing flag"]},
        ],
        "prs": [
            {
                "number": 13,
                "title": "gamma change",
                "ci": "green",
                "cf_at_head": True,
                "mq": "not_queued",
                "unqueued_min": 74,
            },
            {
                "number": 15,
                "title": "fresh change",
                "ci": "green",
                "cf_at_head": True,
                "mq": "not_queued",
                "unqueued_min": 10,
            },
            {
                "number": 16,
                "title": "queued change",
                "ci": "green",
                "cf_at_head": True,
                "mq": "queued",
                "unqueued_min": 90,
            },
            {
                "number": 17,
                "title": "old approval",
                "ci": "green",
                "cf_at_head": False,
                "mq": "not_queued",
                "unqueued_min": 90,
            },
            {
                "number": 18,
                "title": "unknown age",
                "ci": "green",
                "cf_at_head": True,
                "mq": "not_queued",
                "unqueued_min": None,
            },
        ],
        "alerts": [
            {
                "name": "ExampleWarning",
                "severity": "warning",
                "summary": "example warning",
            },
            {
                "name": "ExampleCritical",
                "severity": "critical",
                "summary": "example critical",
            },
        ],
        "usage": [
            {"subscription": "lane-a", "used_pct": 83, "hard_stop_pct": 90},
            {"subscription": "lane-b", "used_pct": 96, "hard_stop_pct": 90},
            {"subscription": "lane-c", "used_pct": 10},
            {"subscription": "lane-d"},
        ],
    }


def _harness() -> dict:
    return {
        "generated_at": FRESH,
        "interval_s": 30,
        "agents": {
            "driver-alpha": {"pid_alive": True, "activity": "working", "idle_min": None},
            "driver-gamma": {"pid_alive": True, "activity": "idle", "idle_min": 56},
            "driver-delta": {"pid_alive": False, "idle_min": None, "pane_text": SCREEN},
        },
    }


def _install(monkeypatch: pytest.MonkeyPatch, tmp_path, roster: dict, harness: dict | None) -> None:
    roster_path = tmp_path / "roster.json"
    _write(roster_path, roster)
    monkeypatch.setenv("FLEET_ROSTER_SNAPSHOT", str(roster_path))
    if harness is not None:
        harness_path = tmp_path / "harness.json"
        _write(harness_path, harness)
        monkeypatch.setenv("FLEET_HARNESS_SNAPSHOT", str(harness_path))


def test_fixture_snapshot_states_and_attention_order(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _install(monkeypatch, tmp_path, _roster(), _harness())
    response = client.get("/api/fleet/v1/now")

    assert response.status_code == 200
    body = response.json()
    assert body["schema"] == "fleet.v1.now"
    assert SCREEN not in response.text
    by_epic = {item["epic"]: item for item in body["data"]["epics"]}
    assert [item["epic"] for item in body["data"]["epics"]] == [
        "alpha",
        "beta",
        "gamma",
        "delta",
        "theta",
        "epsilon",
        "zeta",
        "eta",
    ]
    assert by_epic["alpha"]["state"] == "working"
    assert by_epic["alpha"]["state_reason"] == "recorded working"
    assert by_epic["alpha"]["layer"] == 0
    assert by_epic["alpha"]["driver"]["pid_alive"] is True
    assert by_epic["alpha"]["workers"][0]["state"] == "working"
    assert by_epic["alpha"]["workers"][0]["state_reason"] == "recorded working"
    assert by_epic["beta"]["state"] == "idle"
    assert by_epic["gamma"]["state"] == "stuck"
    assert by_epic["gamma"]["state_reason"] == "idle while intended running"
    assert by_epic["delta"]["state"] == "dead"
    assert by_epic["delta"]["state_reason"] == "process is not alive"
    assert by_epic["delta"]["driver"]["pid_alive"] is False
    assert by_epic["theta"]["state"] == "dead"
    assert by_epic["theta"]["task"] == {"kind": "none", "number": None, "title": None}
    assert by_epic["epsilon"]["state"] == "paused"
    assert by_epic["epsilon"]["driver"] is None
    assert by_epic["zeta"]["state"] == "off"
    assert by_epic["zeta"]["state_reason"] == "postponed"
    assert by_epic["zeta"]["since"] is None
    assert by_epic["eta"]["state"] == "stuck"
    assert by_epic["eta"]["state_reason"] == "liveness unknown"
    assert by_epic["eta"]["driver"]["pid_alive"] is None
    assert by_epic["eta"]["layer"] is None
    assert [item["kind"] + ":" + item["title"] for item in body["data"]["attention"]] == [
        "dead_driver:Delta",
        "dead_driver:Theta",
        "stuck_driver:Eta",
        "stuck_driver:Gamma",
        "red_foundation:queue",
        "unqueued_pr:gamma change",
        "alert:ExampleCritical",
        "alert:ExampleWarning",
        "usage:lane-b",
        "usage:lane-a",
    ]
    roster = next(item for item in body["sources"] if item["name"] == "roster_snapshot")
    harness = next(item for item in body["sources"] if item["name"] == "harness_snapshot")
    assert roster["status"] == "ok"
    assert roster["age_s"] == 20
    assert harness["status"] == "ok"
    assert str(tmp_path) not in response.text


@pytest.mark.parametrize("endpoint", ["now", "epics", "agents", "epics/alpha", "agents/driver-alpha"])
@pytest.mark.parametrize("unrelated_configured", [False, True])
def test_board_reports_only_evaluated_sources(
    monkeypatch: pytest.MonkeyPatch, tmp_path, endpoint: str, unrelated_configured: bool,
) -> None:
    _install(monkeypatch, tmp_path, _roster(), _harness())
    if unrelated_configured:
        for source in sources_mod.EXTERNAL_SOURCES:
            if source.name not in {"roster_snapshot", "harness_snapshot"}:
                monkeypatch.setenv(source.env_var, "configured-but-unread")

    response = client.get(f"/api/fleet/v1/{endpoint}")

    assert response.status_code == 200
    rows = response.json()["sources"]
    expected_names = ["roster_snapshot", "harness_snapshot", "delegate", "occupancy"]
    if endpoint == "now":
        expected_names.extend(["github", "mq_state", "stale_prs"])
    assert [row["name"] for row in rows] == expected_names
    assert all(row["status"] == "ok" for row in rows[:4])
    if endpoint == "now":
        assert rows[4]["status"] == "not_configured"
        expected_status = "unavailable" if unrelated_configured else "not_configured"
        assert all(row["status"] == expected_status for row in rows[5:])
    assert rows[0]["age_s"] == rows[1]["age_s"] == 20


def test_missing_snapshot_is_not_configured_and_http_200() -> None:
    response = client.get("/api/fleet/v1/now")

    assert response.status_code == 200
    body = response.json()
    assert body["data"] == {"attention": [], "epics": []}
    by_name = {item["name"]: item for item in body["sources"]}
    assert by_name["roster_snapshot"] == {
        "name": "roster_snapshot",
        "status": "not_configured",
        "age_s": None,
        "error": None,
    }
    assert by_name["harness_snapshot"]["status"] == "not_configured"
    assert by_name["delegate"]["status"] == "ok"
    assert by_name["occupancy"]["status"] == "ok"


def test_stale_snapshot_stays_http_200(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    roster = {
        "generated_at": "2026-10-09T11:58:59Z",
        "interval_s": 30,
        "epics": [
            {
                "epic": "alpha",
                "title": "Alpha",
                "intended": "running",
                "layer": 0,
                "driver": {
                    "agent_id": "driver-alpha",
                    "cli": "codex",
                    "model": "model-a",
                    "harness": "codex",
                    "pid_alive": True,
                    "activity": "working",
                },
                "workers": [],
            }
        ],
    }
    _install(monkeypatch, tmp_path, roster, {"generated_at": "2026-10-09T11:58:59Z", "interval_s": 30, "agents": {}})

    response = client.get("/api/fleet/v1/epics")

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["epics"][0]["state"] == "working"
    roster_source = next(item for item in body["sources"] if item["name"] == "roster_snapshot")
    harness_source = next(item for item in body["sources"] if item["name"] == "harness_snapshot")
    assert roster_source["status"] == "stale"
    assert roster_source["age_s"] == 61
    assert harness_source["status"] == "stale"
    assert roster_source["error"] is None


def test_unreadable_snapshot_is_unavailable(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    missing = tmp_path / "absent.json"
    monkeypatch.setenv("FLEET_ROSTER_SNAPSHOT", str(missing))

    response = client.get("/api/fleet/v1/now")

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["epics"] == []
    roster = next(item for item in body["sources"] if item["name"] == "roster_snapshot")
    assert roster == {"name": "roster_snapshot", "status": "unavailable", "age_s": None, "error": "unavailable"}
    assert str(missing) not in response.text


def test_collector_failure_stays_http_200(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode():
        raise RuntimeError("boom-token")

    monkeypatch.setattr(view_mod, "load_occupancy_activity", explode)

    response = client.get("/api/fleet/v1/agents")

    assert response.status_code == 200
    occupancy = next(item for item in response.json()["sources"] if item["name"] == "occupancy")
    assert occupancy["status"] == "unavailable"
    assert "boom-token" not in response.text


@pytest.mark.parametrize(
    ("path", "schema_name", "data"),
    [
        ("/now", "now", {"attention": [], "epics": []}),
        ("/epics", "epics", {"epics": []}),
        ("/epics/missing", "epic", None),
        ("/agents", "agents", {"agents": []}),
        ("/agents/missing", "agent", None),
    ],
)
def test_board_failure_retains_endpoint_schema(monkeypatch: pytest.MonkeyPatch, path, schema_name, data) -> None:
    def explode():
        raise RuntimeError("board-failure-private-marker")

    monkeypatch.setattr(router_mod, "load_board", explode)

    response = client.get("/api/fleet/v1" + path)

    assert response.status_code == 200
    body = response.json()
    assert body["schema"] == "fleet.v1." + schema_name
    assert body["data"] == data
    expected = [{"name": "board", "status": "unavailable", "age_s": None, "error": "unavailable"}]
    if path == "/now":
        expected.extend(
            {"name": name, "status": "not_configured", "age_s": None, "error": None}
            for name in ("github", "mq_state", "stale_prs")
        )
    assert body["sources"] == expected
    assert "board-failure-private-marker" not in response.text
    document = client.get("/api/fleet/v1/schema").json()["data"]["endpoints"][body["schema"]]
    Draft202012Validator(document).validate(body)


def test_delegate_failure_is_unavailable_without_erasing_snapshot(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    def explode():
        raise RuntimeError("delegate-failure-private-marker")

    _install(monkeypatch, tmp_path, _roster(), _harness())
    monkeypatch.setattr(activity_mod, "seat_delegate_tasks", explode)
    monkeypatch.setattr(view_mod, "load_delegate_health", activity_mod.load_delegate_health)

    response = client.get("/api/fleet/v1/now")

    assert response.status_code == 200
    body = response.json()
    assert {item["epic"] for item in body["data"]["epics"]} == {item["epic"] for item in _roster()["epics"]}
    delegate = next(item for item in body["sources"] if item["name"] == "delegate")
    assert delegate == {"name": "delegate", "status": "unavailable", "age_s": None, "error": "unavailable"}
    assert "delegate-failure-private-marker" not in response.text


def test_role_bot_and_agent_lookup(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _install(monkeypatch, tmp_path, _roster(), _harness())

    bots = client.get("/api/fleet/v1/agents", params={"role": "bot"})
    one = client.get("/api/fleet/v1/agents/bot-check")
    missing = client.get("/api/fleet/v1/agents/missing-agent")
    rejected = client.get("/api/fleet/v1/agents", params={"role": "other"})

    assert bots.status_code == 200
    assert [item["agent_id"] for item in bots.json()["data"]["agents"]] == ["bot-check", "bot-sweep"]
    assert {item["state"] for item in bots.json()["data"]["agents"]} == {"idle", "working"}
    assert one.status_code == 200
    assert one.json()["data"]["role"] == "bot"
    assert one.json()["data"]["last_seen"] == "2026-10-09T11:40:00Z"
    assert one.json()["data"]["state_reason"]
    assert missing.status_code == 404
    assert missing.json()["data"] is None
    assert missing.json()["schema"] == "fleet.v1.agent"
    assert rejected.status_code == 400
    assert rejected.json()["data"] == {"agents": []}


def test_epic_lookup(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _install(monkeypatch, tmp_path, _roster(), _harness())

    found = client.get("/api/fleet/v1/epics/gamma")
    missing = client.get("/api/fleet/v1/epics/missing-epic")

    assert found.status_code == 200
    assert found.json()["schema"] == "fleet.v1.epic"
    assert found.json()["data"]["state"] == "stuck"
    assert missing.status_code == 404
    assert missing.json()["data"] is None


def test_unbound_delegate_zombie_cannot_override_snapshot_liveness(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    roster = {
        "generated_at": FRESH,
        "interval_s": 30,
        "epics": [
            {
                "epic": "alpha",
                "title": "Alpha",
                "intended": "running",
                "driver": {
                    "agent_id": "driver-alpha",
                    "pid_alive": True,
                    "activity": "working",
                    "pane_text": SCREEN,
                },
                "workers": [],
            }
        ],
    }
    _install(monkeypatch, tmp_path, roster, None)
    monkeypatch.setattr(view_mod, "load_delegate_health", activity_mod.load_delegate_health)
    monkeypatch.setattr(activity_mod, "seat_delegate_tasks", lambda: {"tasks": [
        {"agent": "driver-alpha", "alive": False, "status": "zombie"}
    ]})

    response = client.get("/api/fleet/v1/epics/alpha")

    assert response.status_code == 200
    assert response.json()["data"]["state"] == "working"
    assert SCREEN not in response.text
    harness = next(item for item in response.json()["sources"] if item["name"] == "harness_snapshot")
    assert harness["status"] == "not_configured"


def test_schema_validates_now_epic_and_agent(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _install(monkeypatch, tmp_path, _roster(), _harness())
    schema = client.get("/api/fleet/v1/schema").json()["data"]["endpoints"]
    now = client.get("/api/fleet/v1/now").json()
    epic = client.get("/api/fleet/v1/epics/alpha").json()
    agent = client.get("/api/fleet/v1/agents/driver-alpha").json()

    Draft202012Validator(schema["fleet.v1.now"]).validate(now)
    Draft202012Validator(schema["fleet.v1.epic"]).validate(epic)
    Draft202012Validator(schema["fleet.v1.agent"]).validate(agent)
    Draft202012Validator(schema["fleet.v1.epics"]).validate(client.get("/api/fleet/v1/epics").json())
    Draft202012Validator(schema["fleet.v1.agents"]).validate(client.get("/api/fleet/v1/agents").json())


def test_harness_health_projects_known_metrics_and_keeps_missing_null(monkeypatch, tmp_path):
    roster = _roster()
    roster["epics"][0]["driver"]["agent_id"] = "codex"
    harness = {"interval_s": 30, "measured_at": FRESH, "drivers": [{
        "agent_id": "codex", "context_pct": 0, "compactions": 0,
        "stop_count": 0, "ask_count": 2.5, "idle_min": 0,
    }]}
    _install(monkeypatch, tmp_path, roster, harness)
    health = client.get("/api/fleet/v1/epics/alpha").json()["data"]["health"]
    assert health == {"agent_id": "codex", "status": "ok", "measured_at": FRESH,
                      "context_pct": 0, "compactions": 0, "stop_count": 0, "ask_count": 2.5, "idle_min": 0}
    from scripts.api.fleet_board.file_sources import unknown_health
    assert client.get("/api/fleet/v1/epics/beta").json()["data"]["health"] == unknown_health()


def test_delegate_and_occupancy_wrappers_call_the_collectors(monkeypatch: pytest.MonkeyPatch) -> None:
    def delegate_loader():
        return {
            "total": 1,
            "tasks": [{"agent": "driver-alpha", "alive": True, "status": "running", "task_id": "secret-task"}],
        }

    def occupancy_loader():
        return {"hosts": {"row-1": {"status": "fresh", "occupants": [{"agent": "driver-beta", "status": "idle"}]}}}

    monkeypatch.setattr(activity_mod, "seat_delegate_tasks", delegate_loader)
    monkeypatch.setattr(activity_mod, "occupancy_payload", occupancy_loader)

    delegate_report = activity_mod.load_delegate_health()
    occupancy_report, activity = activity_mod.load_occupancy_activity()

    assert delegate_report.status == "ok"
    assert delegate_report.as_dict() == {"name": "delegate", "status": "ok", "age_s": None, "error": None}
    assert "secret-task" not in repr(delegate_report)
    assert occupancy_report.status == "ok"
    assert activity == {}  # Unbound label-only observations cannot supply seat activity.
    assert "row-1" not in repr(activity)


def _markers() -> dict[str, str]:
    return {
        "title": "/" + "private" + "/marker",
        "focus": ".".join(("10", "1", "2", "3")),
        "task": "worker" + "." + "internal",
        "reason": "~" + "/marker",
        "summary": "ssh " + "ops-box",
        "long": "x" * 161,
    }


def test_emitted_strings_follow_the_public_text_bound(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    marks = _markers()
    roster = {
        "generated_at": FRESH,
        "interval_s": 30,
        "epics": [
            {
                "epic": "kept",
                "title": "Kept",
                "focus": "plain focus",
                "intended": "running",
                "driver": {"agent_id": "driver-kept", "pid_alive": False},
                "task": {"kind": "issue", "number": 21, "title": "kept task"},
                "workers": [{"agent_id": "worker-kept", "task": "kept work"}],
            },
            {
                "epic": "marked",
                "title": marks["title"],
                "focus": marks["focus"],
                "intended": "running",
                "driver": {"agent_id": "driver-marked", "pid_alive": True, "activity": "idle"},
                "task": {"kind": "issue", "number": 22, "title": marks["task"]},
                "workers": [{"agent_id": "worker-marked", "task": marks["long"]}],
            },
        ],
        "foundations": [{"foundation": "queue", "red": True, "reasons": [marks["reason"]]}],
        "alerts": [{"name": "ExampleWarning", "severity": "warning", "summary": marks["summary"]}],
        "prs": [
            {
                "number": 31,
                "title": marks["title"],
                "ci": "green",
                "cf_at_head": True,
                "mq": "not_queued",
                "unqueued_min": 74,
            }
        ],
    }
    _install(monkeypatch, tmp_path, roster, None)

    response = client.get("/api/fleet/v1/now")

    assert response.status_code == 200
    body = response.text
    for mark in marks.values():
        assert mark not in body
    by_epic = {item["epic"]: item for item in response.json()["data"]["epics"]}
    assert by_epic["kept"]["title"] == "Kept"
    assert by_epic["kept"]["state"] == "dead"
    assert by_epic["marked"]["title"] == "[redacted]"
    assert by_epic["marked"]["focus"] == "[redacted]"
    assert by_epic["marked"]["task"]["title"] == "[redacted]"
    assert by_epic["marked"]["workers"][0]["task"] == "[redacted]"
    agent = client.get("/api/fleet/v1/agents/worker-marked").json()["data"]
    assert agent["task"] == "[redacted]"
    attention = response.json()["data"]["attention"]
    foundation = next(item for item in attention if item["kind"] == "red_foundation")
    assert foundation["summary"] == "[redacted]"
    alert = next(item for item in attention if item["kind"] == "alert")
    assert alert["summary"] == "[redacted]"
    pull = next(item for item in attention if item["kind"] == "unqueued_pr")
    assert pull["title"] == "[redacted]"
    assert "Kept" in body


@pytest.mark.parametrize(
    "probe",
    [
        "Burst 85% used",
        "3 of 8 slots free",
        "quota 300 left",
        "12 requests queued",
        "headroom for 4 seats",
        "gpu 16 GB free",
    ],
)
def test_capacity_figures_are_redacted(probe: str) -> None:
    assert activity_mod.text(probe) == "[redacted]"


@pytest.mark.parametrize(
    "probe",
    [
        "16-GB",
        "16_GB",
        "16:GB",
        "16;GB",
        "16 - GB",
        "16 (GB)",
        "16–GB",
        "16—GB",
        "16’GB",
        "16. GB",
        "7-qps",
        "7_qps",
        "7 - qps",
        "12-requests",
        "12 - requests",
        "85-percent",
        "85 - percent",
        "85 per cent",
        "85 percentage",
        "90-pct",
        "3-of-8",
        "3_of_8",
        "3 - of - 8",
        "hard - stop",
        "HARD - STOP",
        "rate — limit",
        "16 gigabytes",
        "16 GIGABYTES",
        "16 giga bytes",
        "8 megabytes",
        "16 mbps",
        "16 gbit",
        "16gbs",
        "quóta",
        "capácity",
        "1\u03016-GB",
        "\uff11\uff16\uff27\uff22",
        "\uff11\uff16 GB",
        "16 \u0413\u0411",
        "16 \u0433\u0456\u0433\u0430\u0431\u0430\u0439\u0442",
        "3 \u043ef 8",
        "cap\u0430city",
        "p\u0430ssword",
    ],
)
def test_split_capacity_figures_are_redacted(probe: str) -> None:
    assert activity_mod.text(probe) == "[redacted]"
    assert activity_mod.seat_id(probe) is None


@pytest.mark.parametrize("unit", ["qps", "rps", "cps"])
@pytest.mark.parametrize("template", ["7 {unit}", "7{unit}", "7.5 {unit}", "7 {unit}_peak"])
@pytest.mark.parametrize("uppercase", [False, True])
def test_rate_figures_are_redacted(unit: str, template: str, uppercase: bool) -> None:
    probe = template.format(unit=unit.upper() if uppercase else unit)
    assert activity_mod.text(probe) == "[redacted]"
    assert activity_mod.seat_id(probe) is None


@pytest.mark.parametrize(
    "probe",
    [
        "buildbox7 is slow",
        "gpu01 queue backed up",
        "build_box2 restart",
        "vps reboot pending",
        "ops server down",
        "lab laptop offline",
    ],
)
def test_machine_names_are_redacted(probe: str) -> None:
    assert activity_mod.text(probe) == "[redacted]"


@pytest.mark.parametrize(
    "probe",
    [
        "rotate 2fa seed",
        "oauth refresh stuck",
        "firewall rule changed",
        "ssh_key missing",
        "allowlist entry added",
        "sudo rights revoked",
        "api key expired",
    ],
)
def test_security_mechanism_details_are_redacted(probe: str) -> None:
    assert activity_mod.text(probe) == "[redacted]"


@pytest.mark.parametrize("token", ["password", "quota", "firewall", "buildbox7", "7 qps"])
@pytest.mark.parametrize("stress", ["\u0301", "\u0301\u0301"])
def test_combining_stress_cannot_bypass_publication_filter(token: str, stress: str) -> None:
    for position in range(1, len(token)):
        marked = token[:position] + stress + token[position:]
        for probe in (marked, marked.upper()):
            assert activity_mod.text(probe) == "[redacted]"
            assert activity_mod.seat_id(probe) is None


@pytest.mark.parametrize("key", ["id_rsa", "id_ed25519"])
@pytest.mark.parametrize("template", ["{}", "Review {} status", "check_{}_state", "check-{}-state"])
@pytest.mark.parametrize("uppercase", [False, True])
def test_key_file_identifiers_are_redacted(key: str, template: str, uppercase: bool) -> None:
    for spelling in (key, key[:4] + "\u0301" + key[4:]):
        probe = template.format(spelling.upper() if uppercase else spelling)
        assert activity_mod.text(probe) == "[redacted]"
        assert activity_mod.seat_id(probe) is None


@pytest.mark.parametrize("probe", ["Поя\u0301снення", "Украї\u0301на", "Review gpt4 compatibility", "driver-2"])
def test_benign_stress_and_existing_labels_are_preserved(probe: str) -> None:
    assert activity_mod.text(probe) == probe
    assert activity_mod.seat_id(probe) == probe


@pytest.mark.parametrize("probe", ["pa\u0301ssword", "quo\u0301ta", "id_rsa", "id_ed25519"])
def test_publication_gaps_are_closed_across_board_routes(monkeypatch, tmp_path, probe: str) -> None:
    roster = {
        "generated_at": FRESH,
        "interval_s": 30,
        "epics": [
            {
                "epic": "kept", "title": "Kept", "intended": "running",
                "driver": {"agent_id": "driver-kept", "pid_alive": False}, "workers": [],
            },
            {
                "epic": "marked", "title": probe, "focus": probe, "intended": "running",
                "driver": {"agent_id": probe},
                "task": {"kind": "issue", "number": 22, "title": probe},
                "workers": [{"agent_id": "worker-marked", "task": probe}, {"agent_id": probe}],
            },
            {"epic": probe, "title": "Omitted identity"},
        ],
        "foundations": [{"foundation": "queue", "red": True, "reasons": [probe]}],
        "alerts": [{"name": "ExampleWarning", "severity": "warning", "summary": probe}],
        "prs": [{"number": 31, "title": probe, "ci": "green", "cf_at_head": True,
                 "mq": "not_queued", "unqueued_min": 74}],
    }
    _install(monkeypatch, tmp_path, roster, None)
    now = client.get("/api/fleet/v1/now")
    assert now.status_code == 200
    body = now.json()
    schemas = client.get("/api/fleet/v1/schema").json()["data"]["endpoints"]
    Draft202012Validator(schemas[body["schema"]]).validate(body)
    by_epic = {row["epic"]: row for row in body["data"]["epics"]}
    assert set(by_epic) == {"kept", "marked"}
    assert by_epic["kept"]["title"] == "Kept"
    assert by_epic["kept"]["state"] == "dead"
    marked = by_epic["marked"]
    assert marked["driver"] is None
    assert marked["title"] == marked["focus"] == marked["task"]["title"] == "[redacted]"
    assert marked["workers"] == [{
        "agent_id": "worker-marked", "cli": None, "model": None, "task": "[redacted]",
        "state": "idle", "state_reason": "idle", "since": None,
    }]
    for kind in ("red_foundation", "alert", "unqueued_pr"):
        item = next(row for row in body["data"]["attention"] if row["kind"] == kind)
        assert item["title" if kind == "unqueued_pr" else "summary"] == "[redacted]"
    for route in ("epics", "epics/marked", "agents", "agents/worker-marked"):
        response = client.get("/api/fleet/v1/" + route)
        assert response.status_code == 200
        payload = response.json()
        Draft202012Validator(schemas[payload["schema"]]).validate(payload)
        assert probe not in response.text
    assert client.get("/api/fleet/v1/agents/worker-marked").json()["data"]["task"] == "[redacted]"


@pytest.mark.parametrize(
    "probe",
    [
        "path/with/slash",
        "50 % cpu",
        "user@example",
        "emoji \U0001F600",
        "a=b",
    ],
)
def test_unlisted_shapes_fail_closed(probe: str) -> None:
    assert activity_mod.text(probe) == "[redacted]"


@pytest.mark.parametrize(
    "probe",
    [
        "Kept",
        "plain focus",
        "driver-kept",
        "worker-2",
        "claude-opus-5-5",
        "not_queued",
        "Epic #4387",
        "A1 M03",
        "Пояснення: вступ “ок” «1»",
    ],
)
def test_plain_labels_stay_publishable(probe: str) -> None:
    assert activity_mod.text(probe) == probe


@pytest.mark.parametrize("term", ["gpt4", "ipv4", "utf8", "base64", "html5"])
@pytest.mark.parametrize("template", ["{}", "Review {} compatibility", "check_{}_format"])
@pytest.mark.parametrize("uppercase", [False, True])
def test_numbered_technical_terms_remain_publishable(term: str, template: str, uppercase: bool) -> None:
    probe = template.format(term.upper() if uppercase else term)
    assert activity_mod.text(probe) == probe


@pytest.mark.parametrize("label", ["sample01", "sample-01", "xx-sample-01", "sample-node-01"])
@pytest.mark.parametrize("template", ["{}", "Review {} status", "check_{}_state"])
@pytest.mark.parametrize("uppercase", [False, True])
def test_numbered_label_variants_fail_closed(label: str, template: str, uppercase: bool) -> None:
    probe = template.format(label.upper() if uppercase else label)
    assert activity_mod.text(probe) == "[redacted]"
    assert activity_mod.seat_id(probe) is None


@pytest.mark.parametrize("term", ["jwt", "jwts", "rbac", "admin", "admins", "secret", "secrets"])
@pytest.mark.parametrize("template", ["{}", "Review {} status", "check_{}_state", "check-{}-state"])
@pytest.mark.parametrize("uppercase", [False, True])
def test_additional_security_terms_fail_closed(term: str, template: str, uppercase: bool) -> None:
    probe = template.format(term.upper() if uppercase else term)
    assert activity_mod.text(probe) == "[redacted]"
    assert activity_mod.seat_id(probe) is None


@pytest.mark.parametrize("term", ["instance", "instances", "user", "users"])
@pytest.mark.parametrize("template", ["{}", "7 {}", "check_{}_state", "check-{}-state"])
@pytest.mark.parametrize("uppercase", [False, True])
def test_additional_capacity_terms_fail_closed(term: str, template: str, uppercase: bool) -> None:
    probe = template.format(term.upper() if uppercase else term)
    assert activity_mod.text(probe) == "[redacted]"
    assert activity_mod.seat_id(probe) is None


@pytest.mark.parametrize("probe", ["secretary", "administration", "userland", "instanced", "driver-2"])
def test_added_patterns_respect_word_boundaries(probe: str) -> None:
    assert activity_mod.text(probe) == probe


def test_redacted_summary_drops_the_seat_identity() -> None:
    assert activity_mod.seat_id("buildbox7") is None
    assert activity_mod.seat_id("driver-kept") == "driver-kept"


def test_malformed_epic_keeps_sibling_records(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    roster = {
        "generated_at": FRESH,
        "interval_s": 30,
        "epics": [
            {
                "epic": "bad-kind",
                "title": "Bad kind",
                "intended": "running",
                "driver": {"agent_id": "driver-kind", "pid_alive": True},
                "task": {"kind": [], "title": "skip"},
                "workers": [],
            },
            {
                "epic": "bad-number",
                "title": "Bad number",
                "intended": "running",
                "driver": {"agent_id": "driver-number", "pid_alive": True},
                "task": {"kind": "issue", "number": 10**400, "title": "count"},
                "workers": [],
            },
            {
                "epic": "kept",
                "title": "Kept",
                "intended": "running",
                "driver": {"agent_id": "driver-kept", "pid_alive": False},
                "workers": [],
            },
        ],
    }
    _install(monkeypatch, tmp_path, roster, None)

    response = client.get("/api/fleet/v1/now")

    assert response.status_code == 200
    by_epic = {item["epic"]: item for item in response.json()["data"]["epics"]}
    assert by_epic["kept"]["state"] == "dead"
    assert by_epic["kept"]["title"] == "Kept"
    assert by_epic["bad-kind"]["task"] == {"kind": "none", "number": None, "title": None}
    assert by_epic["bad-number"]["task"] == {"kind": "issue", "number": None, "title": "count"}
    kinds = [item["kind"] for item in response.json()["data"]["attention"]]
    assert "dead_driver" in kinds


def test_occupancy_presence_without_status_stays_idle(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(view_mod, "load_occupancy_activity", activity_mod.load_occupancy_activity)
    monkeypatch.setattr(
        activity_mod,
        "occupancy_payload",
        lambda: {"hosts": {"row-1": {"status": "fresh", "occupants": [{"agent": "driver-beta"}]}}},
    )
    roster = {
        "generated_at": FRESH,
        "interval_s": 30,
        "epics": [
            {
                "epic": "beta",
                "title": "Beta",
                "intended": "running",
                "driver": {"agent_id": "driver-beta", "pid_alive": True, "activity": "idle", "idle_min": 6},
                "workers": [],
            }
        ],
    }
    _install(monkeypatch, tmp_path, roster, None)

    response = client.get("/api/fleet/v1/epics/beta")

    assert response.status_code == 200
    assert response.json()["data"]["state"] == "idle"
    assert "row-1" not in response.text


def test_stale_occupancy_does_not_override_idle(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(view_mod, "load_occupancy_activity", activity_mod.load_occupancy_activity)
    monkeypatch.setattr(
        activity_mod,
        "occupancy_payload",
        lambda: {
            "hosts": {
                "row-1": {
                    "status": "stale",
                    "age_seconds": 90,
                    "occupants": [{"agent": "driver-beta", "status": "working"}],
                }
            }
        },
    )
    roster = {
        "generated_at": FRESH,
        "interval_s": 30,
        "epics": [
            {
                "epic": "beta",
                "title": "Beta",
                "intended": "running",
                "driver": {"agent_id": "driver-beta", "pid_alive": True, "activity": "idle", "idle_min": 6},
                "workers": [],
            }
        ],
    }
    _install(monkeypatch, tmp_path, roster, None)

    response = client.get("/api/fleet/v1/epics/beta")

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["state"] == "idle"
    occupancy = next(item for item in body["sources"] if item["name"] == "occupancy")
    assert occupancy["status"] == "stale"
    assert occupancy["age_s"] == 90
    assert occupancy["error"] is None
    assert "row-1" not in response.text


@pytest.mark.parametrize(
    "host_states,expected_status,expected_age",
    [
        ((), "ok", None),
        (("fresh",), "ok", None),
        (("stale",), "stale", 90),
        (("unavailable",), "unavailable", None),
        (("fresh", "fresh"), "ok", None),
        (("stale", "stale"), "stale", 120),
        (("unavailable", "unavailable"), "unavailable", None),
        (("fresh", "stale"), "ok", None),
        (("fresh", "unavailable"), "ok", None),
        (("stale", "unavailable"), "stale", 90),
        (("fresh", "stale", "unavailable"), "ok", None),
    ],
)
def test_occupancy_host_health_matrix(
    monkeypatch: pytest.MonkeyPatch, tmp_path, host_states, expected_status, expected_age
) -> None:
    from scripts.api.occupancy import _shape_host

    hosts = {}
    for index, status in enumerate(host_states):
        # Exercise producer-shaped failures with retained occupants, not just
        # empty failures. Nonfresh working rows must not override fresh idle.
        occupants = (
            [
                {"agent": "driver-alpha", "status": "working"},
                {"agent": "worker-alpha", "status": "idle"},
                {"agent": "bot-check", "status": "working"},
            ]
            if status == "fresh"
            else [
                {"agent": "worker-alpha", "status": "working"},
                {"agent": "driver-beta", "status": "working"},
            ]
        )
        host_id = f"row-{index}"
        hosts[host_id] = _shape_host(
            host_id,
            load_entry={"status": status, "age_seconds": 90 + index * 30},
            occupants=occupants,
            burn_state="unknown",
            burn_sources={},
        )
    monkeypatch.setattr(activity_mod, "occupancy_payload", lambda: {"hosts": hosts})
    monkeypatch.setattr(view_mod, "load_occupancy_activity", activity_mod.load_occupancy_activity)
    source, activity = activity_mod.load_occupancy_activity()
    assert activity == {}  # These observations intentionally have no canonical session binding.
    expected_source = {
        "name": "occupancy",
        "status": expected_status,
        "age_s": expected_age,
        "error": "unavailable" if expected_status == "unavailable" else None,
    }
    assert source.as_dict() == expected_source
    roster = _roster()
    roster["epics"] = roster["epics"][:2]
    roster["epics"][0]["workers"][0]["activity"] = "idle"
    roster["bots"] = roster["bots"][:1]
    _install(monkeypatch, tmp_path, roster, None)
    schema = client.get("/api/fleet/v1/schema").json()["data"]["endpoints"]
    expected_alpha = "idle"
    for path in ("now", "epics", "epics/alpha", "agents", "agents/driver-alpha"):
        response = client.get(f"/api/fleet/v1/{path}")
        assert response.status_code == 200
        body = response.json()
        Draft202012Validator(schema[body["schema"]]).validate(body)
        assert next(row for row in body["sources"] if row["name"] == "occupancy") == expected_source
        if path in {"now", "epics"}:
            alpha, beta = body["data"]["epics"]
            assert alpha["state"] == expected_alpha
            assert alpha["workers"][0]["state"] == "idle"
            assert beta["state"] == "idle"
        elif path == "agents":
            by_id = {row["agent_id"]: row for row in body["data"]["agents"]}
            assert by_id["driver-alpha"]["state"] == expected_alpha
            assert by_id["worker-alpha"]["state"] == "idle"
            assert by_id["driver-beta"]["state"] == "idle"
            assert by_id["bot-check"]["state"] == expected_alpha
        else:
            assert body["data"]["state"] == expected_alpha
        assert all(host_id not in response.text for host_id in hosts)


@pytest.mark.parametrize("status,expected", [
    ("working", {("driver-alpha", "session-alpha"): "working"}),
    ("idle", {("driver-alpha", "session-alpha"): "idle"}),
    ("running", {}), ("live", {}), ("active", {}), ("blocked", {}), (None, {}),
])
def test_occupancy_activity_contract_rejects_unsupported_aliases(
    monkeypatch: pytest.MonkeyPatch, status, expected
) -> None:
    monkeypatch.setattr(activity_mod, "occupancy_payload", lambda: {"hosts": {
        "row-1": {"status": "fresh", "occupants": [{"kind": "observer", "agent": "driver-alpha", "session_id": "session-alpha", "instance_id": "instance-alpha", "status": status}]}
    }})
    source, activity = activity_mod.load_occupancy_activity()
    assert source.status == "ok"
    assert activity == expected


@pytest.mark.parametrize("payload", [
    None, [], {}, {"hosts": []}, {"hosts": {"row-1": None}},
    {"hosts": {"row-1": {"occupants": [{"agent": "driver-alpha", "status": "working"}]}}},
    {"hosts": {"row-1": {"status": "unknown", "occupants": [{"agent": "driver-alpha", "status": "working"}]}}},
])
def test_invalid_occupancy_observations_are_unavailable(monkeypatch: pytest.MonkeyPatch, payload) -> None:
    monkeypatch.setattr(activity_mod, "occupancy_payload", lambda: payload)
    source, activity = activity_mod.load_occupancy_activity()
    assert source.as_dict() == {
        "name": "occupancy", "status": "unavailable", "age_s": None, "error": "unavailable"
    }
    assert activity == {}


@pytest.mark.parametrize("signal", [None, "roster", "harness", "occupancy"])
def test_unknown_pid_precedence_for_each_role(monkeypatch: pytest.MonkeyPatch, tmp_path, signal) -> None:
    roster = _roster()
    roster["epics"] = roster["epics"][:1]
    roster["bots"] = roster["bots"][:1]
    seats = [roster["epics"][0]["driver"], roster["epics"][0]["workers"][0], roster["bots"][0]]
    for seat in seats:
        seat.update(pid_alive=None, activity="working" if signal == "roster" else "idle", intended="running")
    harness = None
    if signal == "harness":
        harness = {"generated_at": FRESH, "interval_s": 30, "agents": {
            seat["agent_id"]: {"activity": "working"} for seat in seats
        }}
    if signal == "occupancy":
        monkeypatch.setattr(view_mod, "load_occupancy_activity", activity_mod.load_occupancy_activity)
        monkeypatch.setattr(activity_mod, "occupancy_payload", lambda: {"hosts": {
            "row-1": {"status": "fresh", "occupants": [
                {"agent": seat["agent_id"], "status": "working"} for seat in seats
            ]}
        }})
    _install(monkeypatch, tmp_path, roster, harness)
    epic = client.get("/api/fleet/v1/epics/alpha").json()["data"]
    assert epic["driver"]["pid_alive"] is None
    agents = client.get("/api/fleet/v1/agents").json()["data"]["agents"]
    assert {agent["role"] for agent in agents} == {"driver", "worker", "bot"}
    for agent in agents:
        expected = (("stuck", "liveness unknown") if agent["role"] == "driver" else
                    ("working", "recorded working") if signal in {"roster", "harness"} else ("idle", "idle"))
        assert (agent["state"], agent["state_reason"]) == expected


def test_derived_dead_delegate_row_is_health_only(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    import scripts.api.delegate_router as delegate_router

    monkeypatch.setattr(view_mod, "load_delegate_health", activity_mod.load_delegate_health)
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "seat-row.json").write_text(
        json.dumps(
            {
                "task_id": "seat-row",
                "agent": "driver-alpha",
                "status": "running",
                "pid": 1,
                "started_at": "2026-10-09T11:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(delegate_router, "_tasks_dir", lambda ctx=None: tasks_dir)
    monkeypatch.setattr(delegate_router, "_pid_alive", lambda pid: False)
    delegate_router._TASK_STATE_CACHE.clear()
    delegate_router._LAST_TASKS_DIR_STR = ""
    roster = {
        "generated_at": FRESH,
        "interval_s": 30,
        "epics": [
            {
                "epic": "alpha",
                "title": "Alpha",
                "intended": "running",
                "driver": {
                    "agent_id": "driver-alpha",
                    "pid_alive": True,
                    "activity": "working",
                    "pane_text": SCREEN,
                },
                "workers": [],
            }
        ],
    }
    _install(monkeypatch, tmp_path, roster, None)
    try:
        assert delegate_router.active_delegate_tasks()["total"] == 0
        assert delegate_router.seat_delegate_tasks()["tasks"][0]["status"] == "zombie"
        assert activity_mod.load_delegate_health().status == "ok"
        response = client.get("/api/fleet/v1/now")
        assert response.status_code == 200
        epic = response.json()["data"]["epics"][0]
        assert epic["state"] == "working"
        assert epic["state_reason"] == "recorded working"
        assert response.json()["data"]["attention"] == []
        assert next(row for row in response.json()["sources"] if row["name"] == "delegate")["status"] == "ok"
        assert "seat-row" not in response.text
        assert SCREEN not in response.text
        assert str(tasks_dir) not in response.text
    finally:
        delegate_router._TASK_STATE_CACHE.clear()
        delegate_router._LAST_TASKS_DIR_STR = ""


@pytest.mark.parametrize("stamp,status", [("2026-10-09T06:00:00Z", "stale"), (None, "unavailable")])
@pytest.mark.parametrize("pid,idle,activity,expected", [
    (False, 6, "idle", "dead"),
    (True, 45, "idle", "stuck"),
    (True, 6, "idle", "idle"),
])
def test_nonfresh_harness_cannot_override_fresh_roster(
    monkeypatch: pytest.MonkeyPatch, tmp_path, stamp, status, pid, idle, activity, expected
) -> None:
    roster = _roster()
    roster["epics"] = [roster["epics"][0]]
    roster["epics"][0]["driver"].update(pid_alive=pid, idle_min=idle, activity=activity)
    harness = {"interval_s": 30, "agents": {
        "driver-alpha": {"pid_alive": True, "idle_min": 0, "activity": "working", "pane_text": SCREEN}
    }}
    if stamp is not None:
        harness["generated_at"] = stamp
    _install(monkeypatch, tmp_path, roster, harness)
    response = client.get("/api/fleet/v1/now")
    assert response.status_code == 200
    body = response.json()
    epic = body["data"]["epics"][0]
    assert epic["state"] == expected
    assert epic["driver"]["pid_alive"] is pid
    assert next(row for row in body["sources"] if row["name"] == "harness_snapshot")["status"] == status
    if expected == "dead":
        assert body["data"]["attention"][0]["kind"] == "dead_driver"
    elif expected == "stuck":
        assert body["data"]["attention"][0]["kind"] == "stuck_driver"
    assert SCREEN not in response.text


@pytest.mark.parametrize("fields", [
    {"idle_min": None, "activity": None},
    {"idle_min": "invalid", "activity": "busy"},
    {"idle_min": True, "activity": False},
    {"idle_min": float("nan"), "activity": 7},
    {"idle_min": float("inf"), "activity": {}},
    {"idle_min": float("-inf"), "activity": []},
    {"idle_min": {}, "activity": ""},
    {"idle_min": [], "activity": "unknown"},
])
@pytest.mark.parametrize("idle,expected", [(6, "working"), (55, "stuck")])
def test_fresh_harness_unusable_fields_preserve_roster(
    monkeypatch: pytest.MonkeyPatch, tmp_path, fields, idle, expected,
) -> None:
    roster = _roster()
    roster["epics"] = [roster["epics"][0]]
    driver = roster["epics"][0]["driver"]
    driver.update(idle_min=idle, activity="working")
    _install(monkeypatch, tmp_path, roster, {
        "generated_at": FRESH, "interval_s": 30, "agents": {"driver-alpha": fields}
    })

    response = client.get("/api/fleet/v1/now")

    assert response.status_code == 200
    body = response.json()
    assert next(row for row in body["sources"] if row["name"] == "harness_snapshot")["status"] == "ok"
    assert activity_mod.resolve_idle_min(driver, fields) == idle
    assert activity_mod.resolve_activity(driver, fields) == "working"
    epic = body["data"]["epics"][0]
    assert epic["state"] == expected
    if expected == "stuck":
        assert epic["state_reason"] == "idle while intended running"
        assert any(item["kind"] == "stuck_driver" and item["title"] == "Alpha"
                   for item in body["data"]["attention"])
    else:
        assert epic["state_reason"] == "recorded working"
        assert not any(item["kind"] == "stuck_driver" for item in body["data"]["attention"])


@pytest.mark.parametrize("fields,expected", [
    ({"pid_alive": True, "idle_min": 0, "activity": "working"}, "working"),
    ({"pid_alive": True, "idle_min": 1, "activity": "working"}, "working"),
    ({"pid_alive": False, "idle_min": 1, "activity": "working"}, "dead"),
    ({"pid_alive": True, "idle_min": 45, "activity": "idle"}, "stuck"),
])
def test_fresh_harness_still_overrides_roster(monkeypatch: pytest.MonkeyPatch, tmp_path, fields, expected) -> None:
    roster = _roster()
    roster["epics"] = [roster["epics"][0]]
    roster["epics"][0]["driver"].update(pid_alive=False, idle_min=55, activity="idle")
    _install(monkeypatch, tmp_path, roster, {
        "generated_at": FRESH, "interval_s": 30, "agents": {"driver-alpha": fields}
    })
    body = client.get("/api/fleet/v1/now").json()
    assert body["data"]["epics"][0]["state"] == expected
    assert body["data"]["epics"][0]["driver"]["pid_alive"] is fields["pid_alive"]
    assert next(row for row in body["sources"] if row["name"] == "harness_snapshot")["status"] == "ok"


@pytest.mark.parametrize("invalid", [
    {"generated_at": None}, {"generated_at": "invalid"}, {"interval_s": None},
    {"interval_s": 0}, {"generated_at": "2026-10-09T12:00:01Z"},
])
def test_unknown_roster_freshness_has_no_usable_payload(monkeypatch: pytest.MonkeyPatch, tmp_path, invalid) -> None:
    roster = _roster()
    roster.update(invalid)
    _install(monkeypatch, tmp_path, roster, _harness())
    for path, empty in [("now", {"epics": [], "attention": []}), ("epics", {"epics": []}),
                        ("agents", {"agents": []})]:
        response = client.get(f"/api/fleet/v1/{path}")
        assert response.status_code == 200
        body = response.json()
        assert body["data"] == empty
        assert next(row for row in body["sources"] if row["name"] == "roster_snapshot") == {
            "name": "roster_snapshot", "status": "unavailable", "age_s": None, "error": "unavailable"
        }
    for path in ("epics/alpha", "agents/driver-alpha"):
        response = client.get(f"/api/fleet/v1/{path}")
        assert response.status_code == 404
        assert response.json()["data"] is None


@pytest.mark.parametrize("role", ["driver", "worker", "bot"])
@pytest.mark.parametrize("pid", [True, False, None])
@pytest.mark.parametrize("seat_id,task", [
    ("codex", {"agent": "codex", "task_id": "unrelated-zombie", "alive": False, "status": "zombie"}),
    ("claude", {"agent": "claude", "task_id": "unrelated-live", "alive": True, "status": "running"}),
    ("same-task", {"agent": "codex", "task_id": "same-task", "alive": True, "status": "running"}),
    ("codex", {"agent": "codex", "task_id": "unknown-pid", "alive": None, "status": "running"}),
])
def test_delegate_identity_coincidences_do_not_change_any_role(
    monkeypatch: pytest.MonkeyPatch, tmp_path, role, pid, seat_id, task
) -> None:
    monkeypatch.setattr(view_mod, "load_delegate_health", activity_mod.load_delegate_health)
    monkeypatch.setattr(activity_mod, "seat_delegate_tasks", lambda: {"tasks": [task]})
    seat = {"agent_id": seat_id, "pid_alive": pid, "activity": "idle"}
    epic = {"epic": "alpha", "intended": "running", "driver": seat, "workers": []}
    roster = {"generated_at": FRESH, "interval_s": 30, "epics": [epic], "bots": []}
    if role == "worker":
        epic["driver"] = {"agent_id": "driver-alpha", "pid_alive": False}
        epic["workers"] = [seat]
    elif role == "bot":
        roster["epics"] = []
        roster["bots"] = [seat]
    _install(monkeypatch, tmp_path, roster, None)
    body = client.get("/api/fleet/v1/agents").json()
    agent = next(row for row in body["data"]["agents"] if row["agent_id"] == seat_id)
    assert agent["role"] == role
    expected = "dead" if pid is False else "stuck" if role == "driver" and pid is None else "idle"
    assert agent["state"] == expected
    now = client.get("/api/fleet/v1/now").json()
    if role == "driver":
        assert now["data"]["epics"][0]["driver"]["pid_alive"] is pid
        assert [row["kind"] for row in now["data"]["attention"]] == (
            ["dead_driver"] if expected == "dead" else ["stuck_driver"] if expected == "stuck" else []
        )
    elif role == "worker":
        assert now["data"]["epics"][0]["driver"]["pid_alive"] is False
        assert now["data"]["attention"][0]["kind"] == "dead_driver"
    else:
        assert now["data"]["attention"] == []
    assert next(row for row in body["sources"] if row["name"] == "delegate")["status"] == "ok"
    assert task["task_id"] not in json.dumps(body["sources"])


@pytest.mark.parametrize("payload,status", [(None, "unavailable"), ([], "unavailable"),
                                            ({}, "ok"), ({"tasks": [None, {}]}, "ok")])
def test_delegate_health_does_not_interpret_rows(monkeypatch: pytest.MonkeyPatch, payload, status) -> None:
    monkeypatch.setattr(activity_mod, "seat_delegate_tasks", lambda: payload)
    source = activity_mod.load_delegate_health()
    assert source.status == status
    assert source.name == "delegate"


def test_respond_has_no_unreachable_statements_after_return() -> None:
    tree = ast.parse(inspect.getsource(router_mod.respond))
    for node in ast.walk(tree):
        for field in ("body", "orelse", "finalbody"):
            statements = getattr(node, field, [])
            if not isinstance(statements, list):
                continue
            for index, statement in enumerate(statements):
                if isinstance(statement, ast.Return):
                    assert index == len(statements) - 1, "Unreachable statement after return"


@pytest.mark.parametrize("path,schema_id", [("epics/alpha", "fleet.v1.epic"),
                                            ("agents/driver-alpha", "fleet.v1.agent")])
@pytest.mark.parametrize("failure", ["missing", "board", "envelope"])
def test_single_item_error_fallback_preserves_null(
    monkeypatch: pytest.MonkeyPatch, path, schema_id, failure
) -> None:
    from scripts.api.fleet_board.envelope import endpoint_schema

    def explode(*args, **kwargs):
        raise RuntimeError("private-error-marker")

    if failure == "board":
        monkeypatch.setattr(router_mod, "load_board", explode)
    monkeypatch.setattr(router_mod, "envelope", explode)
    if failure == "envelope":
        monkeypatch.setattr(router_mod, "utc_timestamp", explode)
    response = client.get(f"/api/fleet/v1/{path}")
    assert response.status_code == (200 if failure == "board" else 404)
    body = response.json()
    assert body["schema"] == schema_id
    assert body["data"] is None
    assert body["sources"] == [{"name": "response", "status": "unavailable", "age_s": None, "error": "unavailable"}]
    if failure == "envelope":
        assert body["generated_at"] == "1970-01-01T00:00:00Z"
    Draft202012Validator(endpoint_schema(schema_id)).validate(body)
    assert "private-error-marker" not in response.text


@pytest.mark.parametrize("case", ["matching", "wrong-session", "wrong-instance", "wrong-host", "no-observer", "duplicate", "expired", "closed", "unknown-pid"])
def test_canonical_lease_presence_chain_controls_driver_activity(monkeypatch, tmp_path, case):
    from agents_extensions.shared.session_streams.db import SessionStreamDatabase
    from agents_extensions.shared.session_streams.model import LeaseHolder
    from agents_extensions.shared.session_streams.store import SessionStreamStore
    from scripts.api import occupancy as occ
    from scripts.api.observer_presence import ObserverPresence

    database = SessionStreamDatabase(tmp_path / "sessions.sqlite3")
    store = SessionStreamStore(database)
    lease = store.open_session(stream_id="epic:7101", session_id="session-alpha", lease_id="lease-alpha",
                       lineage_id="lineage-alpha", ttl_seconds=600,
                       holder=LeaseHolder(agent="driver-alpha", harness="sample", instance_id="instance-alpha",
                                          process_id=41001, task_id="task-alpha"))
    if case == "duplicate":
        store.open_session(stream_id="epic:7102", session_id="session-beta", lease_id="lease-beta",
                           lineage_id="lineage-beta", ttl_seconds=600,
                           holder=LeaseHolder(agent="driver-alpha", harness="sample", instance_id="instance-beta",
                                              process_id=41002, task_id="task-beta"))
    if case == "closed":
        store.close_session(lease)
    observer = ObserverPresence(agent="driver-alpha", kind="driver", task_id="task-alpha", epic="7101",
                                status="working", summary=None, host_id="sample-host" if case != "wrong-host" else "other-host",
                                instance_id="instance-alpha" if case != "wrong-instance" else "other-instance",
                                ctx_tokens=None, window_tokens=None, updated_at=FRESH,
                                updated_at_mono=100, expires_at_mono=200)
    snapshot = occ.OccupancySnapshot({"sample-box": "sample-host"},
                                    () if case == "no-observer" else (observer,), 100, datetime.now(UTC) + (timedelta(seconds=601) if case == "expired" else timedelta()))
    monkeypatch.setattr(occ, "_build_snapshot", lambda **kwargs: snapshot)
    monkeypatch.setattr(occ, "_load_entry_for_selected", lambda *args, **kwargs: {"status": "fresh", "age_seconds": 0})
    monkeypatch.setattr("scripts.api.occupancy_local.session_streams_db_path", lambda: database.path)
    monkeypatch.setenv("MONITOR_OCCUPANCY_DRIVER_HOST_ID", "sample-host")
    monkeypatch.setenv("MONITOR_OCCUPANCY_MARKERS", str(tmp_path / "no-markers"))
    monkeypatch.setenv("ATLAS_JOB_REGISTRY", str(tmp_path / "no-jobs"))
    monkeypatch.setattr(activity_mod, "occupancy_payload", lambda: occ.occupancy_payload(host_id="sample-host"))
    monkeypatch.setattr(view_mod, "load_occupancy_activity", activity_mod.load_occupancy_activity)
    roster = _roster()
    roster["epics"] = roster["epics"][:1]
    roster["epics"][0]["driver"].update(session_id="other-session" if case == "wrong-session" else "session-alpha",
                                          activity="idle", pid_alive=None if case == "unknown-pid" else True)
    _install(monkeypatch, tmp_path, roster, None)
    raw = occ.occupancy_payload(host_id="sample-host")
    if case in {"matching", "unknown-pid"}:
        presence = next(row for row in raw["hosts"]["sample-host"]["occupants"] if row["kind"] == "observer")
        assert presence["session_id"] == "session-alpha"
        assert presence["instance_id"] == "instance-alpha"
    response = client.get("/api/fleet/v1/now")
    assert response.status_code == 200
    body = response.json()
    expected = "working" if case == "matching" else "stuck" if case == "unknown-pid" else "idle"
    assert body["data"]["epics"][0]["state"] == expected
    assert any(row["kind"] == "stuck_driver" for row in body["data"]["attention"]) == (case == "unknown-pid")
    assert "session-alpha" not in response.text
    assert "instance-alpha" not in response.text


@pytest.mark.parametrize("stamp,interval,status", [
    (FRESH, 30, "ok"), ("2026-10-09T11:59:00Z", 30, "ok"),
    ("2026-10-09T11:58:59Z", 30, "stale"), (None, 30, "unknown"),
    ("bad", 30, "unknown"), ("2026-10-09T12:00:01Z", 30, "unknown"),
    (FRESH, None, "unknown"), (FRESH, 0, "unknown"), (FRESH, -1, "unknown"),
    (FRESH, True, "unknown"), (FRESH, float("inf"), "unknown"),
])
def test_canonical_health_measurement_window_and_independent_counters(monkeypatch, tmp_path, stamp, interval, status):
    roster = _roster()
    roster["epics"][0]["driver"]["agent_id"] = "codex"
    harness = {"interval_s": interval, "drivers": [{"agent_id": "codex", "measured_at": stamp,
                                                 "stop_count": 0, "idle_min": 1.5, "context_pct": 2.5}]}
    _install(monkeypatch, tmp_path, roster, harness)
    body = client.get("/api/fleet/v1/now").json()
    health = body["data"]["epics"][0]["health"]
    assert health["status"] == status
    assert health["agent_id"] == "codex"
    assert health["stop_count"] == (0 if status == "ok" else None)
    assert health["ask_count"] is None
    assert health["context_pct"] == (2.5 if status == "ok" else None)
    assert health["idle_min"] == (1.5 if status == "ok" else None)
    from scripts.api.fleet_board.envelope import endpoint_schema
    Draft202012Validator(endpoint_schema("fleet.v1.now")).validate(body)


@pytest.mark.parametrize("rows", [[], [{"agent_id": "other"}], [{"agent_id": "codex"}, {"agent_id": "codex"}]])
def test_canonical_health_never_guesses_driver_identity(monkeypatch, tmp_path, rows):
    roster = _roster()
    roster["epics"][0]["driver"].update(agent_id="codex", cli="codex", harness="codex")
    _install(monkeypatch, tmp_path, roster, {"interval_s": 30, "measured_at": FRESH, "drivers": rows})
    health = client.get("/api/fleet/v1/epics/alpha").json()["data"]["health"]
    assert health["status"] == "unknown"
    assert health["agent_id"] is None
    assert all(health[key] is None for key in ("context_pct", "compactions", "stop_count", "ask_count", "idle_min"))
