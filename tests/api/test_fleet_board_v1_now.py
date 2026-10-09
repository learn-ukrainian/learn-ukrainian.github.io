"""Who-is-doing-what routes for the fleet board."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from scripts.api import main as api_main
from scripts.api.fleet_board import activity as activity_mod
from scripts.api.fleet_board import sources as sources_mod
from scripts.api.fleet_board import view as view_mod
from scripts.api.fleet_board.activity import DelegateFact
from scripts.api.fleet_board.sources import report

client = TestClient(api_main.app, raise_server_exceptions=False)
FROZEN = datetime(2026, 10, 9, 12, 0, 0, tzinfo=UTC)
FRESH = "2026-10-09T11:59:40Z"
SCREEN = "busy compiling output"


@pytest.fixture(autouse=True)
def _isolated(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in sources_mod.LOCATION_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("FLEET_PR_STALE_MIN", raising=False)
    monkeypatch.setattr(view_mod, "utc_now", lambda: FROZEN)
    monkeypatch.setattr(view_mod, "load_delegate_facts", lambda: (report("delegate", "ok"), {}))
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


def _delegate(monkeypatch: pytest.MonkeyPatch, facts: dict[str, DelegateFact]) -> None:
    monkeypatch.setattr(view_mod, "load_delegate_facts", lambda: (report("delegate", "ok"), facts))


def test_fixture_snapshot_states_and_attention_order(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _install(monkeypatch, tmp_path, _roster(), _harness())
    _delegate(
        monkeypatch,
        {
            "driver-delta": DelegateFact(True, "running"),
            "worker-alpha": DelegateFact(True, "running"),
        },
    )

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
    assert by_epic["alpha"]["workers"][0]["state_reason"] == "active task"
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


def test_delegate_zombie_is_dead_even_when_snapshot_pid_is_alive(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
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
    _delegate(monkeypatch, {"driver-alpha": DelegateFact(False, "zombie")})

    response = client.get("/api/fleet/v1/epics/alpha")

    assert response.status_code == 200
    assert response.json()["data"]["state"] == "dead"
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


def test_delegate_and_occupancy_wrappers_call_the_collectors(monkeypatch: pytest.MonkeyPatch) -> None:
    def delegate_loader():
        return {
            "total": 1,
            "tasks": [{"agent": "driver-alpha", "alive": True, "status": "running", "task_id": "secret-task"}],
        }

    def occupancy_loader():
        return {"hosts": {"row-1": {"occupants": [{"agent": "driver-beta", "status": "idle"}]}}}

    monkeypatch.setattr(activity_mod, "seat_delegate_tasks", delegate_loader)
    monkeypatch.setattr(activity_mod, "occupancy_payload", occupancy_loader)

    delegate_report, facts = activity_mod.load_delegate_facts()
    occupancy_report, activity = activity_mod.load_occupancy_activity()

    assert delegate_report.status == "ok"
    assert facts["driver-alpha"] == DelegateFact(True, "running")
    assert "secret-task" not in repr(facts)
    assert occupancy_report.status == "ok"
    assert activity == {"driver-beta": "idle"}
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


def test_derived_dead_delegate_row_marks_the_seat_dead(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    import scripts.api.delegate_router as delegate_router

    monkeypatch.setattr(view_mod, "load_delegate_facts", activity_mod.load_delegate_facts)
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
        _report, facts = activity_mod.load_delegate_facts()
        assert facts["driver-alpha"] == DelegateFact(False, "zombie")
        response = client.get("/api/fleet/v1/now")
        assert response.status_code == 200
        epic = response.json()["data"]["epics"][0]
        assert epic["state"] == "dead"
        assert epic["state_reason"] == "process is not alive"
        assert response.json()["data"]["attention"][0]["kind"] == "dead_driver"
        assert "seat-row" not in response.text
        assert SCREEN not in response.text
        assert str(tasks_dir) not in response.text
    finally:
        delegate_router._TASK_STATE_CACHE.clear()
        delegate_router._LAST_TASKS_DIR_STR = ""
