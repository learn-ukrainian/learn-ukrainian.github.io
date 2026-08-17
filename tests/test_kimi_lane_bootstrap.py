"""Unit tests for Kimi stream bootstrap helpers (no live stream DB required)."""

from __future__ import annotations

from pathlib import Path

import yaml

from scripts.session_canary import kimi_lane

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ISSUE_STREAMS = _REPO_ROOT / "scripts" / "config" / "issue_streams.yaml"


def _infra_harness_stream_id() -> str:
    """Anchor on the live infra-harness epic so succession cannot stale this suite."""
    epics = yaml.safe_load(_ISSUE_STREAMS.read_text(encoding="utf-8"))["streams"]["infra-harness"][
        "epics"
    ]
    assert epics, "infra-harness must list at least one epic in issue_streams.yaml"
    return f"epic:{int(epics[0])}"


INFRA_STREAM_ID = _infra_harness_stream_id()


def test_cold_start_body_contains_binding_rules() -> None:
    body = kimi_lane._cold_start_body(
        epic="harness",
        stream_id="epic:4707",
        handoff_rel=".claude/harness-epic/INTERIM-DRIVER-HANDOFF.md",
        lease_summary="test",
    )
    assert "epic:4707" in body
    assert "KIMI-COLD-START" not in body or "Kimi cold-start" in body
    assert "read-only" in body.lower()
    assert "FAIL-HANDOFF" in body or "8/10" in body
    assert "#5556" in body


def test_write_cold_start_creates_file(tmp_path: Path) -> None:
    epic_dir = tmp_path / ".claude" / "harness-epic"
    epic_dir.mkdir(parents=True)
    (epic_dir / "INTERIM-DRIVER-HANDOFF.md").write_text("# interim\n", encoding="utf-8")
    kimi_lane._write_cold_start(
        epic_dir,
        epic="harness",
        stream_id="epic:4707",
        lease_summary="opened test",
        repo=tmp_path,
    )
    path = epic_dir / "KIMI-COLD-START.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "epic:4707" in text
    assert "INTERIM-DRIVER-HANDOFF.md" in text


def test_handoff_candidates_prefer_kimi_driver(tmp_path: Path) -> None:
    cands = kimi_lane._handoff_candidates(tmp_path, "harness")
    assert cands[0].name == "KIMI-DRIVER-HANDOFF.md"


def test_protocol_prints_launcher(capsys) -> None:
    import argparse

    rc = kimi_lane.cmd_protocol(argparse.Namespace(epic="harness", stream=None))
    assert rc == 0
    out = capsys.readouterr().out
    # Post-cutover (#5958): kimi has NO certified driver entrypoint; the
    # protocol points at certified provider drivers instead of start-kimi.sh.
    assert "no certified public driver entrypoint" in out
    assert INFRA_STREAM_ID in out
