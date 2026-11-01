"""Approved #12378 cases for execution, Sources provenance and interpreter admission."""

import json
import shlex
import subprocess
import tomllib
from pathlib import Path

import pytest

from scripts.agent_runtime import review_mcp
from scripts.common.repo_root import project_interpreter
from scripts.dispatcher import agy_sandbox, review_tools
from scripts.dispatcher.providers import agy, load
from scripts.dispatcher.types import TaskSpec

ROUTES = ("claude", "codex", "agy", "cursor", "muse", "opencode")


@pytest.mark.parametrize("route", ROUTES)
def test_review_shell_policy_reuses_worker_denies(tmp_path, route):
    """Defect: granting execution accidentally also grants ordinary publication commands."""
    review_tools.checkout_interpreter(tmp_path)
    for allowed in (".venv/bin/python --version", ".venv/bin/python -m pytest tests/example.py -q",
                    ".venv/bin/python scripts/probe.py", "git rev-parse HEAD", "curl https://docs.python.org"):
        assert review_tools.shell_blocked(allowed) is None
    command = shlex.split(review_tools.hook_command(harness=route, review=True))
    for denied in ("git push origin HEAD", "git -C . commit -m forbidden", "bash -c 'git commit -m forbidden'",
                   "gh -R owner/repo pr merge 1", ".venv/bin/python -m scripts.publish pr-merge --number 1",
                   ".venv/bin/python --version"):
        payload = {"tool_name": "Bash", "tool_input": {"command": denied}, "cwd": str(tmp_path)}
        if route == "cursor":
            payload = {"command": denied, "cwd": str(tmp_path)}
        elif route == "agy":
            payload = {"toolCall": {"name": "run_command", "args": {"CommandLine": denied}}, "cwd": str(tmp_path)}
        result = subprocess.run(command, input=json.dumps(payload), capture_output=True, text=True, timeout=20)
        expected = "allow" if denied == ".venv/bin/python --version" else "deny"
        if route in {"cursor", "agy"}:
            assert result.returncode == 0, result.stderr
            assert json.loads(result.stdout)["permission"] == expected
        elif expected == "allow":
            assert result.returncode == 0, result.stderr
        else:
            assert result.returncode == 2, result.stderr
            assert "review_mutation_denied" in result.stderr


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("mode", ("read-only", "workspace-write"))
def test_sources_config_comes_from_trusted_dispatcher(tmp_path, monkeypatch, route, mode):
    """Defect: Sources is absent or the reviewed checkout can replace its launch command."""
    monkeypatch.setattr(agy, "read_only_refusal", lambda *args: None)
    monkeypatch.setattr(agy_sandbox, "launcher", lambda spec, argv: argv)
    token = tmp_path / "test-oauth"
    token.write_text("fixture")
    monkeypatch.setattr(review_mcp, "_real_agy_token", lambda: token)
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Review the exact head.")
    (tmp_path / ".mcp.json").write_text('{"mcpServers":{"sources":{"command":"untrusted-checkout-command"}}}')
    model = "gpt-6.1-sol" if route == "codex" else "explicit-model"
    spec = TaskSpec("review-tools", route, model, "high", mode, tmp_path, prompt, tmp_path / "result")
    originals = review_tools.prepare(spec)
    try:
        invocation = load(route).build(spec, {"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"})
        if route == "claude":
            config = json.loads(invocation.argv[invocation.argv.index("--mcp-config") + 1])["mcpServers"]["sources"]
        elif route == "codex":
            text = next(arg for arg in invocation.argv if arg.startswith("mcp_servers.sources="))
            config = tomllib.loads(text)["mcp_servers"]["sources"]
        elif route == "cursor":
            config = json.loads((tmp_path / ".cursor/mcp.json").read_text())["mcpServers"]["sources"]
            assert json.loads((tmp_path / ".cursor/sandbox.json").read_text()) == {"networkPolicy": {"default": "allow"}}
        elif route == "muse":
            text = next(arg for arg in invocation.argv if arg.startswith("mcpServers.sources="))
            config = json.loads(text.partition("=")[2])
        elif route == "opencode":
            config = json.loads(invocation.env["OPENCODE_CONFIG_CONTENT"])["mcp"]["sources"]
            assert config["type"] == "local" and config["enabled"] is True
            config = {"command": config["command"][0], "args": config["command"][1:]}
        elif mode == "workspace-write":
            home = Path(invocation.env["HOME"])
            config = json.loads((home / ".gemini/config/mcp_config.json").read_text())["mcpServers"]["sources"]
        else:
            # The existing AGY boundary owns the relay; its live canary and relay tests cover that route.
            assert "--add-dir" in invocation.argv
            return
        if route == "codex":
            assert config["required"] is True
        elif route == "muse":
            assert config["mode"] == "required"
        assert config["command"] == "/usr/bin/env"
        assert config["args"][:3] == ["-i", "PATH=/usr/bin:/bin", "LC_ALL=C.UTF-8"]
        assert str(project_interpreter()) in config["args"]
        assert "-I" in config["args"]
        assert str(review_mcp.sources_server_launch()[1]) == config["args"][-1]
        assert "untrusted-checkout-command" not in json.dumps(config)
    finally:
        review_tools.restore(tmp_path, originals)


def test_review_checkout_exposes_project_interpreter(tmp_path):
    """Defect: literal .venv/bin/python is missing or an existing foreign interpreter is replaced."""
    review_tools.checkout_interpreter(tmp_path)
    result = subprocess.run([str(tmp_path / ".venv/bin/python"), "-c", "print('review-interpreter-ok')"],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "review-interpreter-ok\n"
    review_tools.checkout_interpreter(tmp_path)
    other = tmp_path / "foreign"
    other.mkdir()
    (other / ".venv").mkdir()
    with pytest.raises(ValueError, match="review_interpreter_conflict"):
        review_tools.checkout_interpreter(other)
    assert (other / ".venv").is_dir() and not (other / ".venv").is_symlink()
