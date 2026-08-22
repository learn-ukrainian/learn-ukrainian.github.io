"""Loopback observer heartbeat helper (#7075)."""

from __future__ import annotations

import json
from urllib.error import URLError

import pytest

from scripts.orchestration.observer_heartbeat import (
    HeartbeatError,
    main,
    post_observer_presence,
    presence_url,
)


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_presence_url_rejects_non_loopback() -> None:
    with pytest.raises(HeartbeatError):
        presence_url("http://example.com:8765")


def test_post_observer_presence_posts_cursor_payload() -> None:
    captured: dict[str, object] = {}

    def opener(request: object, timeout: int = 0) -> _FakeResponse:
        del timeout
        captured["url"] = getattr(request, "full_url", None)
        captured["body"] = json.loads(getattr(request, "data", b"{}").decode("utf-8"))
        return _FakeResponse(
            {
                "agent": "cursor",
                "task_id": "7075",
                "status": "working",
                "host_id": "cloud-observer",
            }
        )

    row = post_observer_presence(
        agent="cursor",
        task_id="7075",
        epic="7073",
        summary="cursor driver occupancy heartbeat",
        opener=opener,
    )
    assert captured["url"] == "http://127.0.0.1:8765/api/observer/presence"
    assert captured["body"] == {
        "agent": "cursor",
        "kind": "observer",
        "task_id": "7075",
        "status": "working",
        "epic": "7073",
        "summary": "cursor driver occupancy heartbeat",
    }
    assert row["agent"] == "cursor"
    assert row["host_id"] == "cloud-observer"


def test_main_prints_opaque_ack_only(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    def opener(request: object, timeout: int = 0) -> _FakeResponse:
        del request, timeout
        return _FakeResponse({"agent": "cursor", "task_id": "7075", "status": "working"})

    monkeypatch.setattr("urllib.request.urlopen", opener)
    assert main(["--agent", "cursor", "--task-id", "7075", "--status", "working"]) == 0
    out = capsys.readouterr().out
    assert "agent=cursor" in out
    assert "127.0.0.1" not in out
    assert "atlas-runner" not in out


def test_main_fail_open_message_on_unreachable(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    def opener(request: object, timeout: int = 0) -> _FakeResponse:
        del request, timeout
        raise URLError("down")

    monkeypatch.setattr("urllib.request.urlopen", opener)
    assert main(["--agent", "cursor", "--task-id", "7075"]) == 1
    err = capsys.readouterr().err
    assert "monitor unreachable" in err
    assert "127.0.0.1" not in err
