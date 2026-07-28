"""GLM adapter tests migrated to the consolidated surface."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from tests.test_launcher_contract import run_launcher

_GLM_CREDENTIALS = {
    "GLMCC_AUTH_TOKEN": "",
    "ZAI_API_KEY": "",
    "ZHIPU_API_KEY": "",
    "GLM_API_KEY": "",
}


def _stub_claude(tmp_path: Path) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    binary = bin_dir / "claude"
    binary.write_text(
        "#!/usr/bin/env bash\n"
        "printf 'base=%s\\n' \"${ANTHROPIC_BASE_URL:-unset}\"\n"
        "printf 'model=%s\\n' \"${ANTHROPIC_MODEL:-unset}\"\n"
        "printf 'profile=%s\\n' \"${LEARN_UKRAINIAN_PROFILE_ID:-unset}\"\n"
        "printf 'window=%s\\n' \"${CLAUDE_CODE_MAX_CONTEXT_TOKENS:-unset}\"\n"
        "printf 'compact=%s\\n' \"${CLAUDE_CODE_AUTO_COMPACT_WINDOW:-unset}\"\n"
        "printf 'args=%s\\n' \"$*\"\n",
        encoding="utf-8",
    )
    binary.chmod(0o755)
    return bin_dir


def test_glm_rejects_native_harness_and_missing_explicit_credential(tmp_path: Path) -> None:
    native = run_launcher("start-glm.sh", "--harness", "native")
    missing = run_launcher(
        "start-glm.sh",
        env={**_GLM_CREDENTIALS, "HOME": str(tmp_path / "home")},
    )
    assert native.returncode == 2
    assert "native is unsupported" in native.stderr
    assert missing.returncode == 3
    assert "no explicit GLM credential" in missing.stderr


def test_glm_never_uses_an_ambient_anthropic_token(tmp_path: Path) -> None:
    foreign = "anthropic-secret-must-not-appear"
    result = run_launcher(
        "start-glm.sh",
        env={**_GLM_CREDENTIALS, "HOME": str(tmp_path / "home"), "ANTHROPIC_AUTH_TOKEN": foreign},
    )
    assert result.returncode == 3
    assert "no explicit GLM credential" in result.stderr
    assert foreign not in result.stdout + result.stderr


@pytest.mark.parametrize("credential", ("GLMCC_AUTH_TOKEN", "ZAI_API_KEY", "ZHIPU_API_KEY", "GLM_API_KEY"))
def test_glm_accepts_each_explicit_credential_source_without_leaking_value(credential: str, tmp_path: Path) -> None:
    secret = f"{credential.lower()}-secret"
    result = run_launcher(
        "start-glm.sh",
        env={**_GLM_CREDENTIALS, credential: secret, "HOME": str(tmp_path / "home")},
    )
    assert result.returncode == 0, result.stderr
    assert f"credential_source={credential}" in result.stdout
    assert secret not in result.stdout + result.stderr


@pytest.mark.parametrize("alias", ("glm-5.2", "glm52", "glm"))
def test_glm_catalog_aliases_resolve_to_the_allowlisted_model(alias: str, tmp_path: Path) -> None:
    result = run_launcher(
        "start-glm.sh",
        "--model",
        alias,
        env={**_GLM_CREDENTIALS, "ZAI_API_KEY": "test-key", "HOME": str(tmp_path / "home")},
    )
    assert result.returncode == 0, result.stderr
    assert "would exec claude --model glm-5.2" in result.stdout


def test_glm_rejects_unknown_model_endpoint_and_isolation_value(tmp_path: Path) -> None:
    env = {**_GLM_CREDENTIALS, "ZAI_API_KEY": "test-key", "HOME": str(tmp_path / "home")}
    model = run_launcher("start-glm.sh", "--model", "unknown", env=env)
    endpoint = run_launcher("start-glm.sh", "--endpoint", "unknown", env=env)
    isolation = run_launcher("start-glm.sh", env={**env, "LAUNCHER_ISOLATE_CONFIG": "2"})
    assert model.returncode == endpoint.returncode == isolation.returncode == 2


def test_glm_no_isolate_config_fails_closed_on_route_pins(tmp_path: Path) -> None:
    home = tmp_path / "home"
    config_dir = home / ".claude"
    config_dir.mkdir(parents=True)
    (config_dir / "settings.json").write_text(
        json.dumps({"env": {"ANTHROPIC_BASE_URL": "https://foreign.invalid"}}), encoding="utf-8"
    )
    result = run_launcher(
        "start-glm.sh",
        "--no-isolate-config",
        env={**_GLM_CREDENTIALS, "ZAI_API_KEY": "test-key", "HOME": str(home), "CLAUDE_CONFIG_DIR": ""},
    )
    assert result.returncode == 1
    assert "GLM refuses to launch" in result.stderr
    assert "ANTHROPIC_BASE_URL" in result.stderr


def test_glm_exports_trusted_profile_and_capacity_to_the_claude_adapter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bin_dir = _stub_claude(tmp_path)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    result = run_launcher(
        "start-glm.sh",
        env={**_GLM_CREDENTIALS, "ZAI_API_KEY": "test-key", "HOME": str(tmp_path / "home")},
        dry_run=False,
    )
    assert result.returncode == 0, result.stderr
    assert "base=https://api.z.ai/api/anthropic" in result.stdout
    assert "model=glm-5.2" in result.stdout
    assert "profile=glmcc_glm52" in result.stdout
    assert "window=1048576" in result.stdout
    assert "compact=996147" in result.stdout
