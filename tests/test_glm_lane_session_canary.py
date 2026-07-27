"""Tests for GLM session canary lane (T1.3, LOCAL-ONLY guarded)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from scripts.agent_runtime.adapters.glm import _CI_ENV_VARS, GlmAdapter, GlmEgressForbiddenError
from scripts.agent_runtime.result import ParseResult
from scripts.session_canary import glm_lane

_REPO = Path(__file__).resolve().parents[1]


def _py() -> str:
    venv = _REPO / ".venv" / "bin" / "python"
    return str(venv) if venv.is_file() else sys.executable


@pytest.fixture
def clear_ci_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in _CI_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def _allowed_capsule() -> dict[str, object]:
    return {"execution_allowed": True}


def test_assert_glm_egress_allowed_passes_when_no_ci_env(clear_ci_env: None) -> None:
    glm_lane.assert_glm_egress_allowed("test")


@pytest.mark.parametrize("var", _CI_ENV_VARS)
def test_assert_glm_egress_allowed_raises_under_ci(monkeypatch: pytest.MonkeyPatch, var: str) -> None:
    monkeypatch.setenv(var, "true")
    with pytest.raises(GlmEgressForbiddenError, match="China-hosted"):
        glm_lane.assert_glm_egress_allowed("test")


def test_assert_glm_egress_allowed_raises_on_empty_ci_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CI", "")
    with pytest.raises(GlmEgressForbiddenError, match="China-hosted"):
        glm_lane.assert_glm_egress_allowed("test")


def test_verify_transport_preconditions_refused_under_ci(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    precond = glm_lane.verify_transport_preconditions()
    assert precond["status"] == "refused"
    assert precond["reason"] == "ci_egress_forbidden"
    assert "China-hosted" in precond["message"]


def test_verify_transport_preconditions_opencode_missing(clear_ci_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(glm_lane.shutil, "which", lambda bin_name: None)
    precond = glm_lane.verify_transport_preconditions()
    assert precond["status"] == "failed"
    assert precond["reason"] == "opencode_binary_missing"
    assert "opencode binary not found on PATH" in precond["message"]


def test_verify_transport_preconditions_ok(clear_ci_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(glm_lane.shutil, "which", lambda bin_name: "/usr/local/bin/opencode")
    precond = glm_lane.verify_transport_preconditions()
    assert precond["status"] == "ok"
    assert precond["reason"] == "preconditions_satisfied"
    assert precond["opencode_binary"] == "/usr/local/bin/opencode"
    assert precond["model_route"] == "zai-coding-plan/glm-5.2"


def test_run_glm_probe_refused_under_ci(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CI", "1")
    with patch("subprocess.run") as mock_sub:
        receipt = glm_lane.run_glm_probe()
        assert receipt["status"] == "refused"
        assert receipt["reason"] == "ci_egress_forbidden"
        mock_sub.assert_not_called()


def test_run_glm_probe_mocked_success(clear_ci_env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(glm_lane.shutil, "which", lambda bin_name: "/usr/local/bin/opencode")

    fake_proc = MagicMock()
    fake_proc.returncode = 0
    fake_proc.stdout = "GLM-CANARY-7718"
    fake_proc.stderr = ""

    parse_res = ParseResult(
        ok=True,
        response="GLM-CANARY-7718",
        stderr_excerpt=None,
        rate_limited=False,
        session_id=None,
        tokens=None,
        tool_calls=[],
    )

    fake_adapter = MagicMock(spec=GlmAdapter)
    fake_adapter.build_invocation.return_value = MagicMock(
        cmd=["/usr/local/bin/opencode", "run", "--model", "zai-coding-plan/glm-5.2", "--", "prompt"],
        cwd=tmp_path,
        stdin_payload="",
        env_overrides={},
    )
    fake_adapter.parse_response.return_value = parse_res

    with patch("subprocess.run", return_value=fake_proc):
        receipt = glm_lane.run_glm_probe(repo=tmp_path, adapter=fake_adapter)

    assert receipt["status"] == "ok"
    assert receipt["reason"] == "probe_passed"
    assert receipt["score"] == 1.0
    assert receipt["expected_token"] == "GLM-CANARY-7718"
    assert receipt["received_text"] == "GLM-CANARY-7718"


def test_run_glm_probe_mocked_shape_mismatch(clear_ci_env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(glm_lane.shutil, "which", lambda bin_name: "/usr/local/bin/opencode")

    fake_proc = MagicMock()
    fake_proc.returncode = 0
    fake_proc.stdout = "I am GLM and I answered something else"
    fake_proc.stderr = ""

    parse_res = ParseResult(
        ok=True,
        response="I am GLM and I answered something else",
        stderr_excerpt=None,
        rate_limited=False,
        session_id=None,
        tokens=None,
        tool_calls=[],
    )

    fake_adapter = MagicMock(spec=GlmAdapter)
    fake_adapter.build_invocation.return_value = MagicMock(
        cmd=["/usr/local/bin/opencode", "run", "--model", "zai-coding-plan/glm-5.2", "--", "prompt"],
        cwd=tmp_path,
        stdin_payload="",
        env_overrides={},
    )
    fake_adapter.parse_response.return_value = parse_res

    with patch("subprocess.run", return_value=fake_proc):
        receipt = glm_lane.run_glm_probe(repo=tmp_path, adapter=fake_adapter)

    assert receipt["status"] == "failed"
    assert receipt["reason"] == "probe_shape_mismatch"
    assert receipt["score"] == 0.0


def test_bootstrap_creates_boards(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(glm_lane, "_gl", glm_lane._gl)
    rc = glm_lane.main(["--repo", str(tmp_path), "bootstrap", "--epic", "harness"])
    assert rc == 0

    epic_dir = tmp_path / ".claude" / "harness-epic"
    cold_start = epic_dir / "GLM-COLD-START.md"
    handoff = epic_dir / "GLM-DRIVER-HANDOFF.md"

    assert cold_start.is_file()
    assert handoff.is_file()

    cs_text = cold_start.read_text(encoding="utf-8")
    assert "GLM cold-start" in cs_text
    assert "Seat:" in cs_text
    assert "GLM-5.2" in cs_text

    ho_text = handoff.read_text(encoding="utf-8")
    assert "GLM driver handoff" in ho_text
    assert "Seat: GLM-5.2" in ho_text


def test_mint_score_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(glm_lane.shared_hydration, "build_hydration_capsule", lambda stream, lane: _allowed_capsule())
    monkeypatch.setattr(glm_lane._gl, "_load_stream_entries", lambda *a, **k: [
        {"type": "binding_order", "body": f"Pinned binding order text {i} with enough content."}
        for i in range(1, 6)
    ] + [
        {"type": "negative_constraint", "body": "Do not lower quality gates."},
        {"type": "negative_constraint", "body": "Do not bypass CI."},
        {"type": "next_action", "body": "Dual-write handoff after each batch."},
        {"type": "next_action", "body": "Re-score canary after auto-compact."},
        {"type": "decision", "body": "Canary end signal is score not compact count."},
    ])

    canary_dir = tmp_path / "canary"
    handoff = tmp_path / "GLM-DRIVER-HANDOFF.md"
    handoff.write_text(
        "## Next drive order\n- Keep dual-write current\n- Score canary after compact\n"
        "## Hands-off\n- Foreign lanes\n",
        encoding="utf-8",
    )

    rc_mint = glm_lane.main([
        "--repo", str(_REPO),
        "mint",
        "--epic", "harness",
        "--stream", "epic:4707",
        "--handoff", str(handoff),
        "--out-dir", str(canary_dir),
    ])
    assert rc_mint == 0
    probe = json.loads((canary_dir / "probe.json").read_text(encoding="utf-8"))
    anchors = probe["anchors"]
    assert len(anchors) == 10

    answers = {a["id"]: a["a"] for a in anchors}
    answers_path = canary_dir / "answers.json"
    answers_path.write_text(json.dumps(answers), encoding="utf-8")

    def fake_run(cmd: list[str], **kwargs: Any) -> MagicMock:
        res = MagicMock()
        res.returncode = 0
        res.stdout = "SCORE 10/10 = 1.00  ->  PASS\n"
        res.stderr = ""
        return res

    monkeypatch.setattr(glm_lane.subprocess, "run", fake_run)
    rc_score = glm_lane.main([
        "--repo", str(_REPO),
        "score",
        "--epic", "harness",
        "--out-dir", str(canary_dir),
        "--answers", str(answers_path),
        "--context-tokens", "100000",
        "--model", "glm-5.2",
    ])
    assert rc_score == 0
    verdict = json.loads((canary_dir / "last_verdict.json").read_text(encoding="utf-8"))
    assert verdict["verdict"] == "PASS"


def test_score_fail_handoff_closes_exact_lease_and_exits(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(glm_lane, "_with_glm_handoffs", lambda function, args: 2)
    monkeypatch.setattr(glm_lane, "_close_exact_lease", lambda repo, epic: True)

    assert glm_lane.main(["score", "--epic", "harness", "--answers", "answers.json"]) == 2
    assert "FAIL-HANDOFF — exact lease closed" in capsys.readouterr().out


def test_hydrate_refuses_to_continue_when_capsule_is_blocked(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        glm_lane.shared_hydration,
        "build_hydration_capsule",
        lambda stream, lane: {"execution_allowed": False},
    )

    assert glm_lane.main(["hydrate", "--epic", "harness"]) == 2
    assert "hydration blocked" in capsys.readouterr().err


def test_protocol_and_status_cli(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    rc_proto = glm_lane.main(["protocol", "--epic", "harness"])
    assert rc_proto == 0
    out_proto = capsys.readouterr().out
    assert "GLM lane session canary" in out_proto
    assert "LOCAL-ONLY" in out_proto

    rc_stat = glm_lane.main(["--repo", str(tmp_path), "status", "--epic", "harness"])
    assert rc_stat == 0
    out_stat = capsys.readouterr().out
    assert "GLM canary status" in out_stat
