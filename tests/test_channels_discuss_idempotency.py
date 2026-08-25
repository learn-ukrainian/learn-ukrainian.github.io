"""#7160: the discussion-root idempotency key is scoped to channel (+ body).

The authority stores channel/recipient metadata next to the message key,
so a body-only digest made a same-brief retry on a FRESH channel fail
with ``idempotency_key_reused_with_different_payload``. The derived key
now binds the channel, and ``--idempotency-key`` offers an explicit
escape hatch that replaces the old body-mutating workaround.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.ai_agent_bridge import _channels, _channels_cli


@pytest.fixture
def discuss_plane(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(tmp_path / "fleet"))
    monkeypatch.setenv("LU_AGENT_COMM_TRANSPORT", "acp")
    monkeypatch.delenv("LU_RUNTIME_INITIATOR", raising=False)
    monkeypatch.delenv("LU_RUNTIME_INITIATOR_SOURCE", raising=False)
    monkeypatch.delenv("SESSION_HANDOFF_AGENT", raising=False)
    monkeypatch.setenv("CODEX_THREAD_ID", "thread-7160")
    monkeypatch.setattr(
        _channels,
        "load_channel_context",
        lambda _channel: {"body": "", "revs": {}, "missing": []},
    )

    def fake_discussion(**kwargs):
        return {
            "conversation_id": "conversation_" + "a" * 32,
            "state": "COMPLETE",
            "rounds_completed": 1,
            "synthesis": "done",
        }

    monkeypatch.setattr("agent_runtime.acpx_discuss.run_discussion", fake_discussion)
    return tmp_path / "fleet"


def _args(
    channel: str, body: str, idempotency_key: str | None = None
) -> SimpleNamespace:
    return SimpleNamespace(
        channel=channel,
        body=body,
        with_agents="codex,claude",
        max_rounds=2,
        review=False,
        models=None,
        efforts=None,
        idempotency_key=idempotency_key,
    )


def _discussion_roots(fleet_root: Path) -> list[tuple[str, str]]:
    db_path = fleet_root / "comms.sqlite3"
    if not db_path.is_file():
        return []
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """SELECT c.name AS channel, m.message_id AS message_id
               FROM comms_messages m
               JOIN authority_message_metadata meta ON meta.message_id = m.message_id
               JOIN authority_channels c ON c.channel_id = meta.channel_id
               WHERE m.kind = 'discussion-root'"""
        ).fetchall()
    finally:
        conn.close()
    return [(str(row["channel"]), str(row["message_id"])) for row in rows]


def test_derived_key_is_stable_and_channel_scoped() -> None:
    key_alpha = _channels_cli._discussion_root_idempotency_key("alpha", "Same brief.")
    key_alpha_replay = _channels_cli._discussion_root_idempotency_key("alpha", "Same brief.")
    key_beta = _channels_cli._discussion_root_idempotency_key("beta", "Same brief.")
    assert key_alpha.startswith("discussion-root:")
    assert key_alpha == key_alpha_replay
    assert key_alpha != key_beta


def test_same_brief_retry_on_fresh_channel_succeeds(discuss_plane: Path) -> None:
    assert _channels_cli._handle_discuss(_args(channel="alpha", body="Retry me.")) == 0
    assert _channels_cli._handle_discuss(_args(channel="beta", body="Retry me.")) == 0
    roots = _discussion_roots(discuss_plane)
    assert sorted(channel for channel, _ in roots) == ["alpha", "beta"]
    assert roots[0][1] != roots[1][1]


def test_same_channel_replay_dedupes_root(discuss_plane: Path) -> None:
    assert _channels_cli._handle_discuss(_args(channel="alpha", body="Same brief.")) == 0
    assert _channels_cli._handle_discuss(_args(channel="alpha", body="Same brief.")) == 0
    roots = _discussion_roots(discuss_plane)
    assert len(roots) == 1
    assert roots[0][0] == "alpha"


def test_explicit_idempotency_key_replays_and_mints_fresh_roots(
    discuss_plane: Path,
) -> None:
    assert (
        _channels_cli._handle_discuss(
            _args(channel="alpha", body="Same brief.", idempotency_key="attempt-1")
        )
        == 0
    )
    assert (
        _channels_cli._handle_discuss(
            _args(channel="alpha", body="Same brief.", idempotency_key="attempt-2")
        )
        == 0
    )
    assert (
        _channels_cli._handle_discuss(
            _args(channel="alpha", body="Same brief.", idempotency_key="attempt-2")
        )
        == 0
    )
    roots = _discussion_roots(discuss_plane)
    assert len(roots) == 2
    assert roots[0][1] != roots[1][1]


def test_blank_explicit_idempotency_key_is_rejected(
    discuss_plane: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert (
        _channels_cli._handle_discuss(
            _args(channel="alpha", body="Same brief.", idempotency_key="   ")
        )
        == 1
    )
    assert "--idempotency-key must not be empty" in capsys.readouterr().err
    assert _discussion_roots(discuss_plane) == []
