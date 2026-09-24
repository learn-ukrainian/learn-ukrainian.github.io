"""Bridge acknowledgments must respect the Fleet Comms authority cutover."""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path

import pytest

from scripts.ai_agent_bridge import _db
from scripts.fleet_comms.authority import AuthorityService


@pytest.mark.parametrize("mode", ["off", "authority"])
@pytest.mark.parametrize("live", [False, True])
@pytest.mark.parametrize("command", ["ack", "ack-all"])
def test_ack_commands_do_not_write_legacy_store_in_authority_mode(
    isolated_bridge_db: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
    live: bool,
    command: str,
) -> None:
    authority_root = tmp_path / "fleet-comms"
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(authority_root))
    with AuthorityService(root=authority_root) as service:
        delivery_id = service.publish_message(
            sender="operator", body="test", recipients=("codex",),
        ).delivery_ids[0]

    with closing(_db.init_db()) as conn:
        message_id = conn.execute(
            """INSERT INTO messages (from_llm, to_llm, content, timestamp)
               VALUES ('claude', 'codex', 'test', '2026-01-01T00:00:00Z')"""
        ).lastrowid
        conn.commit()

    args = [command, str(message_id) if command == "ack" else "codex"]
    if live:
        args.append("--consumed-by-live-driver")
    result = subprocess.run(
        [sys.executable, "-m", "scripts.ai_agent_bridge", *args],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "FLEET_COMMS_MESSAGE_PLANE": mode},
    )

    with sqlite3.connect(isolated_bridge_db) as conn:
        receipt = conn.execute(
            "SELECT acknowledged, consumed_by_live_driver, consumed_at FROM messages WHERE id = ?",
            (message_id,),
        ).fetchone()

    if mode == "authority":
        assert result.returncode != 0
        assert f"bridge `{command}` cannot acknowledge legacy inbox message IDs" in result.stderr
        assert "deliveries claim" in result.stderr
        assert "deliveries consume" in result.stderr
        assert "deliveries ack" in result.stderr
        assert receipt == (0, 0, None)
    else:
        assert result.returncode == 0, result.stderr
        assert receipt[:2] == (1, int(live))
        assert (receipt[2] is not None) == live

    with AuthorityService(root=authority_root) as service:
        assert service.get_delivery(delivery_id).state == "queued"
