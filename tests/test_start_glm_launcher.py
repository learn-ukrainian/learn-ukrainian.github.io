"""GLM adapter tests migrated to the consolidated surface."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from tests.test_launcher_contract import REPO, run_launcher

_GLM_CREDENTIALS = {
    "GLMCC_AUTH_TOKEN": "",
    "ZAI_API_KEY": "",
    "ZHIPU_API_KEY": "",
    "GLM_API_KEY": "",
}


def _repo_python() -> Path:
    """Resolve the project venv Python without hardcoding a machine path."""
    candidate = REPO / ".venv" / "bin" / "python"
    if candidate.is_file():
        return candidate
    common = subprocess.run(
        [
            "git",
            "-C",
            str(REPO),
            "rev-parse",
            "--path-format=absolute",
            "--git-common-dir",
        ],
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if common.returncode == 0:
        primary = Path(common.stdout.strip()).parent / ".venv" / "bin" / "python"
        if primary.is_file():
            return primary
    pytest.fail(f"project .venv python not found for {REPO}")


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


def test_glm_isolated_config_still_fails_closed_on_stale_route_pins(tmp_path: Path) -> None:
    """Sol P1: isolation must not skip inspecting $CLAUDE_CONFIG_DIR/settings.json."""
    home = tmp_path / "home"
    isolated = home / ".claude-glmcc"
    isolated.mkdir(parents=True)
    (isolated / "settings.json").write_text(
        json.dumps({"env": {"ANTHROPIC_BASE_URL": "https://foreign.invalid"}}),
        encoding="utf-8",
    )
    result = run_launcher(
        "start-glmcc.sh",
        env={**_GLM_CREDENTIALS, "ZAI_API_KEY": "test-key", "HOME": str(home)},
    )
    assert result.returncode == 1
    assert "GLM refuses to launch" in result.stderr
    assert "ANTHROPIC_BASE_URL" in result.stderr
    assert ".claude-glmcc/settings.json" in result.stderr
    assert "test-key" not in result.stdout + result.stderr


@pytest.mark.parametrize(
    "relative_settings",
    (".claude/settings.json", ".claude/settings.local.json"),
)
def test_claude_route_guard_checks_project_local_and_ignores_settings_path_decoy(
    relative_settings: str, tmp_path: Path
) -> None:
    """Sol P1 r4: inspect project/local scopes; CLAUDE_SETTINGS_PATH is not a substitute."""
    home = tmp_path / "home"
    user_cfg = home / ".claude-glmcc"
    user_cfg.mkdir(parents=True)
    (user_cfg / "settings.json").write_text("{}", encoding="utf-8")

    project = tmp_path / "project"
    settings_path = project / relative_settings
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(
        json.dumps({"env": {"ANTHROPIC_BASE_URL": "https://project-or-local.invalid"}}),
        encoding="utf-8",
    )

    decoy = tmp_path / "decoy-clean.json"
    decoy.write_text("{}", encoding="utf-8")
    python_bin = _repo_python()

    script = f"""
set -euo pipefail
source "{REPO}/scripts/lib/claude_route_guard.sh"
export CLAUDE_CONFIG_DIR="{user_cfg}"
export CLAUDE_SETTINGS_PATH="{decoy}"
export CLAUDE_ROUTE_GUARD_PYTHON="{python_bin}"
assert_claude_settings_route_clean "GLM" "{project}"
"""
    result = subprocess.run(
        ["bash", "-c", script],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "GLM refuses to launch" in result.stderr
    assert "ANTHROPIC_BASE_URL" in result.stderr
    assert relative_settings in result.stderr
    # Decoy must not be the only inspected file — the real pin path is reported.
    assert str(settings_path) in result.stderr or relative_settings in result.stderr


def test_claude_route_guard_refuses_provider_selector_pins(tmp_path: Path) -> None:
    """Sol P1 r5: CLAUDE_CODE_USE_* in settings must fail closed."""
    home = tmp_path / "home"
    user_cfg = home / ".claude-glmcc"
    user_cfg.mkdir(parents=True)
    (user_cfg / "settings.json").write_text(
        json.dumps({"env": {"CLAUDE_CODE_USE_BEDROCK": "1"}}),
        encoding="utf-8",
    )
    python_bin = _repo_python()
    script = f"""
set -euo pipefail
source "{REPO}/scripts/lib/claude_route_guard.sh"
export CLAUDE_CONFIG_DIR="{user_cfg}"
export CLAUDE_ROUTE_GUARD_PYTHON="{python_bin}"
assert_claude_settings_route_clean "GLM" "{tmp_path / 'empty-project'}"
"""
    result = subprocess.run(
        ["bash", "-c", script],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "CLAUDE_CODE_USE_BEDROCK" in result.stderr


def test_claude_route_guard_checks_primary_checkout_settings_for_linked_worktree(
    tmp_path: Path,
) -> None:
    """Sol P1 r6: linked worktrees resolve local settings on the primary checkout."""
    primary = tmp_path / "primary"
    worktree = tmp_path / "worktree"
    primary.mkdir()
    subprocess.run(["git", "init", "--quiet", str(primary)], check=True, timeout=30)
    subprocess.run(
        ["git", "-C", str(primary), "commit", "--allow-empty", "--quiet", "-m", "init"],
        check=True,
        timeout=30,
        env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"},
    )
    subprocess.run(
        ["git", "-C", str(primary), "worktree", "add", "--quiet", str(worktree), "HEAD"],
        check=True,
        timeout=30,
    )
    primary_settings = primary / ".claude" / "settings.local.json"
    primary_settings.parent.mkdir(parents=True)
    primary_settings.write_text(
        json.dumps({"env": {"ANTHROPIC_BASE_URL": "https://primary-local.invalid"}}),
        encoding="utf-8",
    )
    home = tmp_path / "home"
    user_cfg = home / ".claude-glmcc"
    user_cfg.mkdir(parents=True)
    (user_cfg / "settings.json").write_text("{}", encoding="utf-8")
    python_bin = _repo_python()
    script = f"""
set -euo pipefail
source "{REPO}/scripts/lib/claude_route_guard.sh"
export CLAUDE_CONFIG_DIR="{user_cfg}"
export CLAUDE_ROUTE_GUARD_PYTHON="{python_bin}"
assert_claude_settings_route_clean "GLM" "{worktree}"
"""
    result = subprocess.run(
        ["bash", "-c", script],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "ANTHROPIC_BASE_URL" in result.stderr
    assert "settings.local.json" in result.stderr


def test_glm_clears_ambient_provider_selector_before_route(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sol P2 r6: stub Claude must observe all five selectors unset."""
    home = tmp_path / "home"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    binary = bin_dir / "claude"
    binary.write_text(
        "#!/usr/bin/env bash\n"
        "for key in CLAUDE_CODE_USE_BEDROCK CLAUDE_CODE_USE_VERTEX "
        "CLAUDE_CODE_USE_FOUNDRY CLAUDE_CODE_USE_MANTLE CLAUDE_CODE_USE_ANTHROPIC_AWS; do\n"
        '  if printenv "$key" >/dev/null 2>&1; then\n'
        '    printf "%s=set\\n" "$key"\n'
        "  else\n"
        '    printf "%s=unset\\n" "$key"\n'
        "  fi\n"
        "done\n",
        encoding="utf-8",
    )
    binary.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    result = run_launcher(
        "start-glmcc.sh",
        env={
            **_GLM_CREDENTIALS,
            "ZAI_API_KEY": "test-key",
            "HOME": str(home),
            "CLAUDE_CODE_USE_BEDROCK": "1",
            "CLAUDE_CODE_USE_VERTEX": "1",
            "CLAUDE_CODE_USE_FOUNDRY": "1",
            "CLAUDE_CODE_USE_MANTLE": "1",
            "CLAUDE_CODE_USE_ANTHROPIC_AWS": "1",
        },
        dry_run=False,
    )
    assert result.returncode == 0, result.stderr
    for key in (
        "CLAUDE_CODE_USE_BEDROCK",
        "CLAUDE_CODE_USE_VERTEX",
        "CLAUDE_CODE_USE_FOUNDRY",
        "CLAUDE_CODE_USE_MANTLE",
        "CLAUDE_CODE_USE_ANTHROPIC_AWS",
    ):
        assert f"{key}=unset" in result.stdout, result.stdout


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


def test_glm_loads_owner_only_secret_file_without_leaking_value(tmp_path: Path) -> None:
    home = tmp_path / "home"
    secret_dir = home / ".secret"
    secret_dir.mkdir(parents=True)
    secret_path = secret_dir / "zai.key"
    secret_value = "file-backed-zai-secret-must-not-appear"
    secret_path.write_text(f"{secret_value}\n", encoding="utf-8")
    secret_path.chmod(0o600)

    result = run_launcher(
        "start-glmcc.sh",
        env={**_GLM_CREDENTIALS, "HOME": str(home)},
    )
    assert result.returncode == 0, result.stderr
    assert "credential_source=file:~/.secret/zai.key" in result.stdout
    assert secret_value not in result.stdout + result.stderr
    # File-sourced keys must not be re-exported under ZAI_* names in dry-run text.
    assert "ZAI_API_KEY=" not in result.stdout


def test_glm_rejects_group_readable_secret_file(tmp_path: Path) -> None:
    home = tmp_path / "home"
    secret_dir = home / ".secret"
    secret_dir.mkdir(parents=True)
    secret_path = secret_dir / "zai.key"
    secret_path.write_text("insecure-secret\n", encoding="utf-8")
    secret_path.chmod(0o640)

    result = run_launcher(
        "start-glm.sh",
        env={**_GLM_CREDENTIALS, "HOME": str(home)},
    )
    assert result.returncode == 3
    assert "no explicit GLM credential" in result.stderr or "could not load GLM credential" in result.stderr
    assert "insecure-secret" not in result.stdout + result.stderr


def test_glm_env_credential_wins_over_secret_file(tmp_path: Path) -> None:
    home = tmp_path / "home"
    secret_dir = home / ".secret"
    secret_dir.mkdir(parents=True)
    secret_path = secret_dir / "zai.key"
    secret_path.write_text("file-secret-should-lose\n", encoding="utf-8")
    secret_path.chmod(0o600)

    result = run_launcher(
        "start-glm.sh",
        env={**_GLM_CREDENTIALS, "HOME": str(home), "ZAI_API_KEY": "env-secret-wins"},
    )
    assert result.returncode == 0, result.stderr
    assert "credential_source=ZAI_API_KEY" in result.stdout
    assert "file-secret-should-lose" not in result.stdout + result.stderr
    assert "env-secret-wins" not in result.stdout + result.stderr
