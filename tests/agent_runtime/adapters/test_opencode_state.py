"""#10959: OpenCode startup must leave a dispatch checkout untouched."""

from __future__ import annotations

import os
import shlex
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from agent_runtime.adapters import acpx
from agent_runtime.adapters._opencode_state import opencode_command
from agent_runtime.adapters.deepseek import DeepSeekAdapter
from agent_runtime.adapters.glm import GlmAdapter
from agent_runtime.env_sanitize import build_agent_env
from agent_runtime.telemetry import _resolve_cli_version


@pytest.mark.parametrize("route", ["deepseek", "glm", "acpx-deepseek-shadow", "acpx-glm-shadow", "acpx-gemma-shadow"])
@pytest.mark.parametrize("existing_project_config", [False, True])
def test_opencode_startup_writes_only_to_dispatch_scratch(tmp_path, monkeypatch, route, existing_project_config):
    checkout = tmp_path / "worker checkout"
    checkout.mkdir()
    if existing_project_config:
        (checkout / ".opencode").mkdir()
        (checkout / ".opencode" / "opencode.json").write_text("{}", encoding="utf-8")
    before = sorted(path.relative_to(checkout) for path in checkout.rglob("*"))
    scratch = tmp_path / "dispatch scratch"
    scratch.mkdir()
    monkeypatch.setenv("LU_RUNTIME_TMP_ROOT", str(scratch))
    monkeypatch.setenv("TMPDIR", str(scratch))
    # Inherited selectors must not redirect startup writes into the checkout.
    monkeypatch.setenv("OPENCODE_CONFIG_DIR", str(checkout / ".opencode"))
    monkeypatch.setenv("OPENCODE_DISABLE_PROJECT_CONFIG", "0")
    monkeypatch.setenv("XDG_CACHE_HOME", str(checkout / "cache"))
    monkeypatch.setenv("XDG_STATE_HOME", str(checkout / "state"))
    for name in ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILDKITE", "JENKINS_URL"):
        monkeypatch.delenv(name, raising=False)

    binary = tmp_path / "fake-opencode"
    binary.write_text(
        f"#!{sys.executable}\n"
        "import os\n"
        "import sys\n"
        "from pathlib import Path\n"
        "if sys.argv[1:] == ['--version']:\n"
        "    print('1.0.0')\n"
        "    sys.exit(0)\n"
        "# Reproduce config dependency installation and XDG cache/state writes.\n"
        "roots = [Path(os.environ.get('OPENCODE_CONFIG_DIR', '.opencode')),\n"
        "         Path(os.environ.get('XDG_CACHE_HOME', 'cache')),\n"
        "         Path(os.environ.get('XDG_STATE_HOME', 'state'))]\n"
        "if os.environ.get('OPENCODE_DISABLE_PROJECT_CONFIG') != '1':\n"
        "    roots.append(Path('.opencode'))\n"
        "for root in roots:\n"
        "    root.mkdir(parents=True, exist_ok=True)\n"
        "    (root / 'startup-probe').write_text('written', encoding='utf-8')\n",
        encoding="utf-8",
    )
    binary.chmod(0o755)
    if route.startswith("acpx-"):
        adapter = {
            "acpx-deepseek-shadow": acpx.AcpxDeepSeekShadowAdapter,
            "acpx-glm-shadow": acpx.AcpxGlmShadowAdapter,
            "acpx-gemma-shadow": acpx.AcpxGemmaShadowAdapter,
        }[route]()
        monkeypatch.setattr(acpx, "_resolve_participant_binary", lambda *_a, **_kw: (str(binary), "1.0.0"))
        monkeypatch.setattr(acpx, "_resolve_host_node_binary", lambda **_kw: Path(sys.executable))
        command, _metadata = adapter._custom_agent_command(checkout)
        cmd = shlex.split(command)
        overrides = adapter._env_overrides()
    else:
        adapter = DeepSeekAdapter() if route == "deepseek" else GlmAdapter()
        monkeypatch.setattr(f"agent_runtime.adapters.{route}.shutil.which", lambda _name: str(binary))
        monkeypatch.setattr("agent_runtime.adapters.deepseek._cached_flash_name", lambda: None)
        plan = adapter.build_invocation(prompt="offline probe", mode="workspace-write", cwd=checkout)
        assert plan.cwd == checkout
        cmd, overrides = plan.cmd, plan.env_overrides
        if route == "deepseek":
            assert _resolve_cli_version(route, plan) == "1.0.0"

    env = build_agent_env(provider=route, overrides=overrides)
    result = subprocess.run(cmd, cwd=checkout, env=env, capture_output=True, text=True, check=False, timeout=10)

    assert result.returncode == 0, result.stderr
    assert sorted(path.relative_to(checkout) for path in checkout.rglob("*")) == before
    assert sorted(path.relative_to(scratch).as_posix() for path in scratch.rglob("startup-probe")) == [
        "opencode/cache/startup-probe",
        "opencode/config/startup-probe",
        "opencode/state/startup-probe",
    ]
    assert os.environ["OPENCODE_CONFIG_DIR"] == str(checkout / ".opencode")


@pytest.mark.parametrize("source", ["LU_RUNTIME_TMP_ROOT", "TMPDIR", "default"])
def test_opencode_state_uses_existing_scratch_root(tmp_path, monkeypatch, source):
    checkout = tmp_path / "checkout"
    scratch = tmp_path / "scratch"
    monkeypatch.delenv("LU_RUNTIME_TMP_ROOT", raising=False)
    monkeypatch.delenv("TMPDIR", raising=False)
    if source == "default":
        monkeypatch.setattr("agent_runtime.adapters._opencode_state.tempfile.gettempdir", lambda: str(scratch))
    else:
        monkeypatch.setenv(source, str(scratch))
    command = opencode_command(["opencode", "run"], cwd=checkout)

    launcher = Path(command[0])
    assert launcher.is_relative_to(scratch / "opencode")
    assert stat.S_IMODE(launcher.stat().st_mode) == 0o700
    assert command[1:] == ["run"]
    assert (
        launcher.read_text(encoding="utf-8")
        == "#!/bin/sh\nexec "
        + shlex.join(
            [
                "env",
                f"OPENCODE_CONFIG_DIR={scratch}/opencode/config",
                "OPENCODE_DISABLE_PROJECT_CONFIG=1",
                f"XDG_CACHE_HOME={scratch}/opencode/cache",
                f"XDG_STATE_HOME={scratch}/opencode/state",
                "opencode",
            ]
        )
        + ' "$@"\n'
    )


@pytest.mark.parametrize("redirect", ["scratch", "config", "cache", "state"])
def test_opencode_state_refuses_paths_inside_checkout(tmp_path, monkeypatch, redirect):
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    scratch = tmp_path / "scratch"
    if redirect == "scratch":
        scratch = checkout
    else:
        (scratch / "opencode").mkdir(parents=True)
        (scratch / "opencode" / redirect).symlink_to(checkout, target_is_directory=True)
    monkeypatch.setenv("LU_RUNTIME_TMP_ROOT", str(scratch))

    with pytest.raises(ValueError, match="OpenCode state must be outside the worker checkout"):
        opencode_command(["opencode", "run"], cwd=checkout)
    assert list(checkout.iterdir()) == []
