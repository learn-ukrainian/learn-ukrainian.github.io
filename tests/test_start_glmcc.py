"""Behavior checks for the interactive Claude Code + GLM (glmcc) launcher."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LAUNCHER = _REPO_ROOT / "start-glmcc.sh"


def _resolve_venv_python() -> Path | None:
    """Project venv; falls back to the main worktree when run from a linked worktree."""
    candidates = [_REPO_ROOT / ".venv" / "bin" / "python"]
    try:
        common = subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if common.returncode == 0 and common.stdout.strip():
            candidates.append(Path(common.stdout.strip()).parent / ".venv" / "bin" / "python")
    except (OSError, subprocess.SubprocessError):
        pass
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


_VENV_PYTHON = _resolve_venv_python()


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _require_launcher_sources() -> None:
    """Seed from checkout once; do not depend on root scripts surviving full CI suite."""
    missing = [
        path
        for path in (
            _LAUNCHER,
            _REPO_ROOT / "scripts" / "secret_redactor.py",
            _REPO_ROOT / "scripts" / "lib" / "claude_route_guard.sh",
            _REPO_ROOT / "scripts" / "lib" / "profile_resolver.sh",
            _REPO_ROOT / "scripts" / "lib" / "context_profiles.py",
            _REPO_ROOT / "scripts" / "review" / "model_catalog.py",
            _REPO_ROOT / "scripts" / "config" / "model_catalog.yaml",
        )
        if not path.is_file()
    ]
    if missing:
        names = ", ".join(str(path.relative_to(_REPO_ROOT)) for path in missing)
        raise FileNotFoundError(f"glmcc launcher sources missing: {names}")


def _seed_fake_project(tmp_path: Path) -> Path:
    """Copy launcher + sourced helpers into an isolated project root."""
    _require_launcher_sources()
    project = tmp_path / "project"
    lib = project / "scripts" / "lib"
    lib.mkdir(parents=True)
    cfg = project / "scripts" / "config"
    review = project / "scripts" / "review"
    cfg.mkdir(parents=True)
    review.mkdir(parents=True)
    venv_bin = project / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    _write_executable(project / "start-glmcc.sh", _LAUNCHER.read_text(encoding="utf-8"))
    _write_executable(
        project / "start-claude.sh",
        "#!/usr/bin/env bash\n# Test stub: glmcc already exported env; exec fake claude from PATH.\nexec claude \"$@\"\n",
    )
    secret_redactor = _REPO_ROOT / "scripts" / "secret_redactor.py"
    (project / "scripts" / "secret_redactor.py").write_text(
        secret_redactor.read_text(encoding="utf-8"), encoding="utf-8"
    )
    for name in ("claude_route_guard.sh", "profile_resolver.sh", "context_profiles.py"):
        src = _REPO_ROOT / "scripts" / "lib" / name
        dest = lib / name
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        if name.endswith(".py"):
            dest.chmod(0o755)
    profiles = _REPO_ROOT / "scripts" / "config" / "context_profiles.yaml"
    if profiles.is_file():
        (cfg / "context_profiles.yaml").write_text(profiles.read_text(encoding="utf-8"), encoding="utf-8")
    (cfg / "model_catalog.yaml").write_text(
        (_REPO_ROOT / "scripts" / "config" / "model_catalog.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (review / "model_catalog.py").write_text(
        (_REPO_ROOT / "scripts" / "review" / "model_catalog.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    if _VENV_PYTHON is not None:
        (venv_bin / "python").symlink_to(_VENV_PYTHON)
    else:
        _write_executable(
            venv_bin / "python",
            "#!/usr/bin/env bash\nexec python3 \"$@\"\n",
        )

    bin_dir = project / "bin"
    bin_dir.mkdir(parents=True)
    _write_executable(
        bin_dir / "claude",
        "#!/usr/bin/env bash\n"
        "printf 'CAPTURED_BASE_URL=%s\\n' \"${ANTHROPIC_BASE_URL:-}\"\n"
        "printf 'CAPTURED_AUTH_TOKEN=%s\\n' \"${ANTHROPIC_AUTH_TOKEN:-}\"\n"
        "printf 'CAPTURED_MODEL=%s\\n' \"${ANTHROPIC_MODEL:-}\"\n"
        "printf 'CAPTURED_SUBAGENT=%s\\n' \"${CLAUDE_CODE_SUBAGENT_MODEL:-}\"\n"
        "printf 'CAPTURED_TOOL_SEARCH=%s\\n' \"${ENABLE_TOOL_SEARCH:-}\"\n"
        "printf 'CAPTURED_TIMEOUT=%s\\n' \"${API_TIMEOUT_MS:-}\"\n"
        "printf 'CAPTURED_CONFIG_DIR=%s\\n' \"${CLAUDE_CONFIG_DIR:-}\"\n"
        "printf 'CAPTURED_MANAGED_LAUNCH=%s\\n' \"${LEARN_UKRAINIAN_GLMCC_MANAGED_LAUNCH-unset}\"\n"
        "printf 'CAPTURED_TRANSPORT=%s\\n' \"${LEARN_UKRAINIAN_TRANSPORT:-}\"\n"
        "printf 'CAPTURED_PROFILE_ID=%s\\n' \"${LEARN_UKRAINIAN_PROFILE_ID:-}\"\n"
        "printf 'CAPTURED_WINDOW=%s\\n' \"${LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS:-}\"\n"
        "printf 'CAPTURED_AUTO_COMPACT=%s\\n' \"${CLAUDE_CODE_AUTO_COMPACT_WINDOW:-}\"\n"
        "printf 'ARGS: %s\\n' \"$*\"\n",
    )

    git_dir = project / ".git"
    git_dir.mkdir()
    (git_dir / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")

    return project


def _run_glmcc(
    project: Path,
    arguments: list[str],
    *,
    env_updates: dict[str, str] | None = None,
    home_dir: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    # Clear ambient route keys
    for var in (
        "ZAI_API_KEY",
        "ZHIPU_API_KEY",
        "GLM_API_KEY",
        "GLMCC_AUTH_TOKEN",
        "ANTHROPIC_AUTH_TOKEN",
        "ANTHROPIC_BASE_URL",
        "ANTHROPIC_MODEL",
        "GLMCC_DRY_RUN",
        "GLMCC_MODEL",
        "GLMCC_ENDPOINT",
        "GLMCC_ISOLATE_CONFIG",
        "GLMCC_AGENT",
        "CLAUDE_CONFIG_DIR",
        "LEARN_UKRAINIAN_TRANSPORT",
        "LEARN_UKRAINIAN_REQUESTED_PROFILE_ID",
        "LEARN_UKRAINIAN_GLMCC_MANAGED_LAUNCH",
    ):
        env.pop(var, None)

    env["PATH"] = f"{project / 'bin'}:{env.get('PATH', '')}"
    if home_dir is not None:
        env["HOME"] = str(home_dir)
        (home_dir / ".claude").mkdir(parents=True, exist_ok=True)
    if env_updates:
        env.update(env_updates)

    return subprocess.run(
        [str(project / "start-glmcc.sh"), *arguments],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )


def test_glmcc_dry_run_fails_honest_without_credential(tmp_path: Path) -> None:
    project = _seed_fake_project(tmp_path)
    res = _run_glmcc(project, [], env_updates={"GLMCC_DRY_RUN": "1"}, home_dir=tmp_path / "home")
    assert res.returncode == 1
    assert "Error: no GLM API credential found for the glmcc route." in res.stderr
    assert "ZAI_API_KEY, ZHIPU_API_KEY, GLM_API_KEY, or GLMCC_AUTH_TOKEN" in res.stderr


@pytest.mark.parametrize(
    ("env_var", "token_val"),
    [
        ("GLMCC_AUTH_TOKEN", "glmcc-test-token"),
        ("ZAI_API_KEY", "zai-test-key"),
        ("ZHIPU_API_KEY", "zhipu-test-key"),
        ("GLM_API_KEY", "glm-test-key"),
        ("ANTHROPIC_AUTH_TOKEN", "anthropic-test-token"),
    ],
)
def test_glmcc_auth_token_precedence_and_dry_run(tmp_path: Path, env_var: str, token_val: str) -> None:
    project = _seed_fake_project(tmp_path)
    res = _run_glmcc(
        project,
        [],
        env_updates={env_var: token_val, "GLMCC_DRY_RUN": "1"},
        home_dir=tmp_path / "home",
    )
    assert res.returncode == 0
    output = res.stdout
    assert "GLMCC: model=glm-5.2 alias=glm-5.2 endpoint=coding profile=glmcc_glm52" in output
    assert "window=1048576 compact=996147" in output
    assert "base=https://api.z.ai/api/anthropic" in output
    assert f"auth={env_var}" in output
    assert "agent=infra-orchestrator" in output
    assert "GLMCC_DRY_RUN=1: would exec" in output


@pytest.mark.parametrize(
    ("alias", "expected_model"),
    [
        ("glm-5.2", "glm-5.2"),
        ("glm52", "glm-5.2"),
        ("glm", "glm-5.2"),
    ],
)
def test_glmcc_model_aliases(tmp_path: Path, alias: str, expected_model: str) -> None:
    project = _seed_fake_project(tmp_path)
    res = _run_glmcc(
        project,
        ["--model", alias],
        env_updates={"ZAI_API_KEY": "test-key", "GLMCC_DRY_RUN": "1"},
        home_dir=tmp_path / "home",
    )
    assert res.returncode == 0
    assert f"GLMCC: model={expected_model}" in res.stdout


def test_glmcc_rejects_unknown_model(tmp_path: Path) -> None:
    project = _seed_fake_project(tmp_path)
    res = _run_glmcc(
        project,
        ["--model", "invalid-model"],
        env_updates={"ZAI_API_KEY": "test-key"},
        home_dir=tmp_path / "home",
    )
    assert res.returncode == 2
    assert "Error: unsupported model 'invalid-model'" in res.stderr


def test_glmcc_rejects_unknown_endpoint(tmp_path: Path) -> None:
    project = _seed_fake_project(tmp_path)
    res = _run_glmcc(
        project,
        ["--endpoint", "invalid-endpoint"],
        env_updates={"ZAI_API_KEY": "test-key"},
        home_dir=tmp_path / "home",
    )
    assert res.returncode == 2
    assert "Error: unsupported endpoint 'invalid-endpoint'" in res.stderr


def test_glmcc_rejects_forwarded_model_argument(tmp_path: Path) -> None:
    project = _seed_fake_project(tmp_path)
    res = _run_glmcc(
        project,
        ["--", "--model", "some-other-model"],
        env_updates={"ZAI_API_KEY": "test-key"},
        home_dir=tmp_path / "home",
    )
    assert res.returncode == 2
    assert "Error: GLMCC owns the lead model (glm-5.2); drop --model" in res.stderr


def test_glmcc_launches_claude_stub_with_expected_env(tmp_path: Path) -> None:
    project = _seed_fake_project(tmp_path)
    res = _run_glmcc(
        project,
        ["--verbose"],
        env_updates={"ZAI_API_KEY": "test-secret-key"},
        home_dir=tmp_path / "home",
    )
    assert res.returncode == 0
    stdout = res.stdout
    assert "CAPTURED_BASE_URL=https://api.z.ai/api/anthropic" in stdout
    assert "CAPTURED_AUTH_TOKEN=test-secret-key" in stdout
    assert "CAPTURED_MODEL=glm-5.2" in stdout
    assert "CAPTURED_SUBAGENT=glm-5.2" in stdout
    assert "CAPTURED_TOOL_SEARCH=false" in stdout
    assert "CAPTURED_TIMEOUT=3000000" in stdout
    assert "CAPTURED_TRANSPORT=glmcc" in stdout
    assert "CAPTURED_PROFILE_ID=glmcc_glm52" in stdout
    assert "CAPTURED_WINDOW=1048576" in stdout
    assert "CAPTURED_AUTO_COMPACT=996147" in stdout
    assert "ARGS: --model glm-5.2 --verbose --agent infra-orchestrator" in stdout


def test_glmcc_omits_default_agent_when_epic_given(tmp_path: Path) -> None:
    project = _seed_fake_project(tmp_path)
    res = _run_glmcc(
        project,
        ["--epic", "harness"],
        env_updates={"ZAI_API_KEY": "test-key"},
        home_dir=tmp_path / "home",
    )
    assert res.returncode == 0
    assert "agent=(epic lane set; identity derives from --epic, no default agent)" in res.stdout
    assert "ARGS: --model glm-5.2 --epic harness" in res.stdout


def test_glmcc_refuses_when_settings_json_has_route_env_keys(tmp_path: Path) -> None:
    project = _seed_fake_project(tmp_path)
    home = tmp_path / "home"
    claude_dir = home / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    settings = claude_dir / "settings.json"
    settings.write_text(json.dumps({"env": {"ANTHROPIC_BASE_URL": "https://bad.route"}}), encoding="utf-8")

    res = _run_glmcc(
        project,
        ["--no-isolate-config"],
        env_updates={"ZAI_API_KEY": "test-key"},
        home_dir=home,
    )
    assert res.returncode == 1
    assert "Error: GLMCC refuses to launch because" in res.stderr
    assert "ANTHROPIC_BASE_URL" in res.stderr
