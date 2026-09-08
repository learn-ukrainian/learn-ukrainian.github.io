"""Review commands may use their temp lease without making the checkout writable."""

import os
import subprocess
import tomllib
from pathlib import Path

import pytest

from scripts.agent_runtime.adapters.codex import CodexAdapter


@pytest.fixture(autouse=True)
def scratch_base(tmp_path, monkeypatch):
    monkeypatch.setenv("LU_RUNTIME_TMP_BASE_ROOT", str(tmp_path))


def review_plan(cwd, lease, session_id=None):
    return CodexAdapter().build_invocation(
        prompt="Review the change",
        mode="read-only",
        cwd=cwd,
        model=None,
        task_id="review-test",
        session_id=session_id,
        tool_config={"read_only_tmp_root": str(lease)},
    )


@pytest.mark.parametrize("args", [("issue", "view", "7814"), ("pr", "comment", "123", "--body", "verdict")])
def test_review_gh_shim_creates_and_cleans_tempfiles(tmp_path, args):
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    lease = tmp_path / "learn-ukrainian" / "review-test"
    lease.mkdir(parents=True)
    backend = tmp_path / "fake-gh"
    backend.write_text(
        '#!/bin/sh\nset -eu\ntest -f "$TMPDIR"/agent-gh.stdout.*\ntest -f "$TMPDIR"/agent-gh.stderr.*\nprintf "%s\\n" "$@"\n'
    )
    backend.chmod(0o755)
    shim = Path(__file__).resolve().parents[1] / "scripts/agent_runtime/shims/gh"
    env = {**os.environ, "TMPDIR": str(tmp_path / "missing"), "AGENT_REAL_GH": str(backend), "AGENT_NO_MERGE": "1"}
    before = subprocess.run([str(shim), *args], env=env, capture_output=True, text=True, timeout=30)
    assert before.returncode != 0
    assert "mktemp" in before.stderr

    plan = review_plan(checkout, lease)
    after = subprocess.run([str(shim), *args], env={**env, **plan.env_overrides}, capture_output=True, text=True, timeout=30)
    assert after.returncode == 0, after.stderr
    assert after.stdout.splitlines() == list(args)
    assert not list(lease.glob("agent-gh.*"))


@pytest.mark.parametrize("session_id", [None, "2c8337b6-35da-415d-806d-91d10b5b1381"])
def test_review_permissions_only_write_lease(tmp_path, session_id):
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    lease = tmp_path / "learn-ukrainian" / 'review-"quoted"-📚'
    lease.mkdir(parents=True)
    plan = review_plan(checkout, lease, session_id)
    configs = [plan.cmd[i + 1] for i, arg in enumerate(plan.cmd[:-1]) if arg == "-c"]
    config = tomllib.loads("\n".join(value for value in configs if not value.startswith("model_reasoning_effort=")))
    profile = config["permissions"][config["default_permissions"]]
    assert profile["filesystem"] == {":root": "read", str(lease): "write"}
    assert profile["network"]["enabled"] is True
    assert profile["network"]["domains"] == {"github.com": "allow", "api.github.com": "allow"}
    assert config["features"]["network_proxy"] is True
    assert config["approval_policy"] == "never"
    assert "-s" not in plan.cmd
    assert "--dangerously-bypass-approvals-and-sandbox" not in plan.cmd
    assert plan.env_overrides["TMPDIR"] == str(lease)
    assert plan.output_file.parent == lease


@pytest.mark.parametrize("invalid", ["relative", "/", "checkout", "parent", "missing", "symlink"])
def test_review_rejects_unsafe_temp_roots(tmp_path, invalid):
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    link = tmp_path / "link"
    link.symlink_to(checkout, target_is_directory=True)
    root = {
        "relative": "relative",
        "/": "/",
        "checkout": checkout,
        "parent": tmp_path,
        "missing": tmp_path / "missing",
        "symlink": link,
    }[invalid]
    with pytest.raises(ValueError, match="read_only_tmp_root"):
        review_plan(checkout, root)
