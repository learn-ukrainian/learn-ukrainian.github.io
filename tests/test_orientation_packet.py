"""Bounded orientation packet and lane-sized Work projection."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scripts.api.main import app
from scripts.api.work_router import projection_cache_key
from scripts.orchestration.issue_stream_audit import load_registry
from scripts.orientation_packet import PACKET_MAX_BYTES, build_packet, cap_projection, json_bytes
from scripts.work.normalize import build_projection
from scripts.work.sources_public import SectionResult

CLIENT = TestClient(app)


def _state(tmp_path: Path, epic: str, body: str) -> None:
    directory = tmp_path / ".claude" / f"{epic}-epic"
    directory.mkdir(parents=True)
    (directory / "DRIVER-STATE.md").write_text(body, encoding="utf-8")


def _orders(count: int = 1) -> dict:
    ids = [f"message_{index:032x}" for index in range(count)]
    return {"probe": "ok", "count": count, "ids": ids, "truncated": False}


def _session() -> dict:
    return {
        "hash": "abc",
        "bytes": 12,
        "locator": "docs/session-state/current.md",
        "sections": {"agent": "monitor"},
        "observed_at": "2026-10-17T00:00:00Z",
        "freshness": "live",
    }


@pytest.mark.parametrize("epic", sorted(load_registry()))
def test_every_registered_lane_packet_fits(epic, tmp_path, monkeypatch):
    monkeypatch.delenv("LU_DRIVER_MIN_WORKERS", raising=False)
    _state(
        tmp_path,
        epic,
        "## Current goals\n- keep the lane inside one packet\n"
        "## Next\n- read the packet\n"
        "## Holds\n- a public hold\n"
        "## Stops\n- a public stop\n",
    )
    packet = build_packet(
        epic,
        root=tmp_path,
        orders=_orders(),
        session=_session(),
    )
    raw = json_bytes(packet, newline=True)
    assert len(raw) <= PACKET_MAX_BYTES
    assert packet["epic"] == epic
    assert set(packet["runtime"]) == {"worker_target"}
    assert packet["runtime"]["worker_target"] == "UNKNOWN"
    assert [row["id"] for row in packet["holds"]] == ["hold-1"]
    assert [row["id"] for row in packet["stops"]] == ["stop-1"]
    assert [row["id"] for row in packet["goals"]] == ["goal-1"]
    assert [row["id"] for row in packet["orders"]] == ["message_" + f"{0:032x}"]
    assert "markdown" not in packet["session"]
    assert packet["freshness"] == "live"
    assert packet["complete"] is True
    names = {source["name"] for source in packet["sources"]}
    assert {"driver_state", "orders", "session", "open_prs", "live_workers", "plane"} <= names


def test_overflow_keeps_hold_stop_and_goal_ids(tmp_path, monkeypatch):
    monkeypatch.delenv("LU_DRIVER_MIN_WORKERS", raising=False)
    holds = "\n".join(f"- hold {index} " + ("h" * 400) for index in range(6))
    stops = "\n".join(f"- stop {index} " + ("s" * 400) for index in range(6))
    goals = "\n".join(f"- goal {index} " + ("g" * 400) for index in range(6))
    nxt = "\n".join(f"- next {index} " + ("n" * 400) for index in range(6))
    _state(
        tmp_path,
        "monitor",
        f"## Current goals\n{goals}\n## Next\n{nxt}\n## Holds\n{holds}\n## Stops\n{stops}\n",
    )
    packet = build_packet(
        "monitor",
        root=tmp_path,
        orders=_orders(400),
        session=_session(),
    )
    assert len(json_bytes(packet, newline=True)) <= PACKET_MAX_BYTES
    assert [row["id"] for row in packet["holds"]] == [f"hold-{index}" for index in range(1, 7)]
    assert [row["id"] for row in packet["stops"]] == [f"stop-{index}" for index in range(1, 7)]
    assert [row["id"] for row in packet["goals"]] == [f"goal-{index}" for index in range(1, 7)]
    assert packet["orders"]
    assert len(packet["orders"]) < 400
    assert packet["complete"] is False
    assert packet["omitted"]["count"] > 0


def _public_projection():
    payload = build_projection(
        {
            "issues": SectionResult(
                "issues", "ok", payload=[{"number": 10917, "title": "Fixture", "state": "OPEN"}], count=1
            )
        }
    )
    payload["items"][0]["projections"]["stream"] = {"status": "homed", "streams": ["monitor"]}
    payload["sources"] = payload["sources"][:1]
    payload["sources"][0]["reason"] = ""
    return payload


def test_projection_records_unassigned_pr(monkeypatch):
    import scripts.api.work_router as work_router

    payload = _public_projection()
    item = payload["items"][0]
    item["resource_kind"] = "pr"
    item["work_id"] = "wp1:pr:10917"
    payload["attention"][0]["work_id"] = item["work_id"]
    item["projections"]["stream"] = {"status": "n/a"}
    payload["denominator"].update(prs_open=1, streams_complete=True, omissions=[])
    before = deepcopy(payload)
    monkeypatch.setattr(work_router, "cache_get_with_age", lambda *_a, **_kw: (payload, 1.0))
    response = CLIENT.get("/api/work/v1/projection?stream=monitor")
    assert response.status_code == 200
    assert len(response.content) <= PACKET_MAX_BYTES
    body = response.json()
    assert body["items"] == []
    omission = body["denominator"]["omissions"][-1]
    assert omission["work_id"] == "wp1:pr:10917"
    assert omission["locator"] == "/api/work/v1/projection#/items/0"
    assert body["denominator"]["streams_complete"] is False
    assert payload == before


def test_cap_projection_keeps_attention_prefix_and_does_not_mutate():
    items = []
    attention = []
    for index in range(40):
        work_id = f"wp1:issue:{index}"
        items.append({"work_id": work_id, "title": "t" * 500})
        attention.append({"work_id": work_id, "attention_rank": index})
    payload = {"items": items, "attention": attention, "denominator": {"omissions": []}}
    capped = cap_projection(payload)
    assert len(json_bytes(capped)) <= PACKET_MAX_BYTES
    assert len(capped["items"]) < len(items)
    assert capped["items"][0]["work_id"] == "wp1:issue:0"
    assert capped["denominator"]["omissions"][-1] == {
        "class": "orientation_bound",
        "reason": "lane_projection_bytes",
        "count": len(items) - len(capped["items"]),
        "locator": "/api/work/v1/projection#/items",
    }
    assert len(payload["items"]) == 40
    assert "omissions" not in payload or payload["denominator"]["omissions"] == []


def test_projection_lane_filter_caps_and_leaves_the_cache(monkeypatch):
    import scripts.api.work_router as work_router

    items = []
    attention = []
    for index in range(30):
        work_id = f"wp1:issue:{index}"
        lane = "infra-harness" if index % 2 == 0 else "devops"
        items.append(
            {
                "work_id": work_id,
                "title": "t" * 2000,
                "projections": {"stream": {"streams": [lane]}},
            }
        )
        attention.append({"work_id": work_id, "attention_rank": index})
    payload = {"items": items, "attention": attention, "denominator": {"omissions": []}, "cache_age_s": 1.0}
    monkeypatch.setattr(work_router, "cache_get_with_age", lambda *_args, **_kwargs: (payload, 1.0))
    monkeypatch.setattr(work_router, "_known_streams", lambda *_args, **_kwargs: ["devops", "infra-harness"])
    response = CLIENT.get("/api/work/v1/projection?stream=infra-harness")
    assert response.status_code == 200
    body = response.json()
    assert len(response.content) <= PACKET_MAX_BYTES
    assert body["items"]
    assert all(item["projections"]["stream"]["streams"] == ["infra-harness"] for item in body["items"])
    assert len(body["items"]) < 15
    assert body["denominator"]["omissions"][-1]["reason"] == "lane_projection_bytes"
    assert len(payload["items"]) == 30
    assert payload["items"][1]["projections"]["stream"]["streams"] == ["devops"]
    assert payload["denominator"]["omissions"] == []
    # The warm key stays unscoped. A lane query must not mint a second cache entry.
    assert "stream" not in projection_cache_key({})
