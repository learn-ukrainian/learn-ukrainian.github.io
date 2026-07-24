"""Codex canary control-flow tests."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from scripts.session_canary import codex_lane


def _allowed_capsule() -> dict[str, object]:
    return {"execution_allowed": True}


def test_score_pass_hydrates_then_continues(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(codex_lane, "_with_codex_handoffs", lambda function, args: 0)
    monkeypatch.setattr(codex_lane.shared_hydration, "build_hydration_capsule", lambda stream, lane: _allowed_capsule())

    assert codex_lane.main(["score", "--epic", "harness", "--answers", "answers.json"]) == 0
    assert "hydration ready — continue" in capsys.readouterr().out


def test_score_fail_handoff_closes_exact_lease_and_exits(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(codex_lane, "_with_codex_handoffs", lambda function, args: 2)
    monkeypatch.setattr(codex_lane, "_close_exact_lease", lambda repo, epic: True)

    assert codex_lane.main(["score", "--epic", "harness", "--answers", "answers.json"]) == 2
    assert "FAIL-HANDOFF — exact lease closed" in capsys.readouterr().out


def test_hydrate_refuses_to_continue_when_capsule_is_blocked(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        codex_lane.shared_hydration,
        "build_hydration_capsule",
        lambda stream, lane: {"execution_allowed": False},
    )

    assert codex_lane.main(["hydrate", "--epic", "harness"]) == 2
    assert "hydration blocked" in capsys.readouterr().err


def test_score_closes_lease_when_post_pass_hydration_blocks(monkeypatch: pytest.MonkeyPatch) -> None:
    closed: list[tuple[object, str]] = []
    monkeypatch.setattr(codex_lane, "_with_codex_handoffs", lambda function, args: 0)
    monkeypatch.setattr(codex_lane, "cmd_hydrate", lambda args: 2)
    monkeypatch.setattr(codex_lane, "_close_exact_lease", lambda repo, epic: closed.append((repo, epic)) or True)

    assert codex_lane.main(["score", "--epic", "harness", "--answers", "answers.json"]) == 2
    assert closed and closed[0][1] == "harness"


def test_lease_environment_parser_reuses_gemini_reader(tmp_path: Path) -> None:
    env_path = tmp_path / "session-lease.env"
    env_path.write_text(
        "export SESSION_STREAM_PROCESS_ID=\"1234\"\n"
        "export SESSION_STREAM_GENERATION='2'\n"
        "unrelated=value\n",
        encoding="utf-8",
    )

    assert codex_lane._read_lease_environment(env_path) == {
        "SESSION_STREAM_PROCESS_ID": "1234",
        "SESSION_STREAM_GENERATION": "2",
    }


@pytest.mark.parametrize(
    ("argv", "handler_name"),
    [
        (["bootstrap", "--epic", "Harness"], "cmd_bootstrap"),
        (["status", "--epic", "Harness"], "cmd_status"),
        (["hydrate", "--epic", "Harness"], "cmd_hydrate"),
        (["score", "--epic", "Harness", "--answers", "answers.json"], "cmd_score"),
    ],
)
def test_main_normalizes_epic_across_canary_subcommands(
    monkeypatch: pytest.MonkeyPatch, argv: list[str], handler_name: str
) -> None:
    observed: list[str] = []

    def record_epic(args: argparse.Namespace) -> int:
        observed.append(args.epic)
        return 0

    monkeypatch.setattr(codex_lane, handler_name, record_epic)

    assert codex_lane.main(argv) == 0
    assert observed == ["harness"]


def test_bootstrap_uses_normalized_epic_for_default_stream_id(tmp_path: Path) -> None:
    assert codex_lane.main(["--repo", str(tmp_path), "bootstrap", "--epic", " HARNESS "]) == 0

    board = (tmp_path / ".claude" / "harness-epic" / "CODEX-COLD-START.md").read_text(encoding="utf-8")
    assert "**Stream:** `epic:4707`" in board
    assert "none selected; start fresh and do not resume historical packets" in board
    assert "never invoke `codex resume`, `codex fork`" in board
    assert "launcher already minted the canary" in board
    assert "no Monitor-equivalent background capability" in board
    assert "never on compact count" in board


def test_bootstrap_uses_dedicated_devops_stream(tmp_path: Path) -> None:
    assert codex_lane.main(["--repo", str(tmp_path), "bootstrap", "--epic", "devops"]) == 0

    board = (tmp_path / ".claude" / "devops-epic" / "CODEX-COLD-START.md").read_text(
        encoding="utf-8"
    )
    assert "**Stream:** `epic:5703`" in board


def test_bootstrap_records_exact_rollover_without_rendering_lease_credentials(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SESSION_STREAM_LEASE_ID", "lease-must-not-render")
    monkeypatch.setenv("CODEX_LAUNCHER_ROLLOVER_AGENT", "codex-infra")
    monkeypatch.setenv("CODEX_LAUNCHER_ROLLOVER_LINEAGE_ID", "lineage-launcher-fresh")
    monkeypatch.setenv("CODEX_LAUNCHER_ROLLOVER_ID", "rollover-launcher-fresh")

    assert codex_lane.main(["--repo", str(tmp_path), "bootstrap", "--epic", "infra"]) == 0

    board = (tmp_path / ".claude" / "infra-epic" / "CODEX-COLD-START.md").read_text(encoding="utf-8")
    assert "lineage-launcher-fresh" in board
    assert "rollover-launcher-fresh" in board
    assert "SessionStart must bind this task" in board
    assert "lease-must-not-render" not in board
    assert "credentials not rendered" in board


def test_bootstrap_rejects_partial_rollover_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CODEX_LAUNCHER_ROLLOVER_LINEAGE_ID", "lineage-partial")
    monkeypatch.delenv("CODEX_LAUNCHER_ROLLOVER_AGENT", raising=False)
    monkeypatch.delenv("CODEX_LAUNCHER_ROLLOVER_ID", raising=False)

    assert codex_lane.main(["--repo", str(tmp_path), "bootstrap", "--epic", "infra"]) == 2
    assert not (tmp_path / ".claude" / "infra-epic" / "CODEX-COLD-START.md").exists()
