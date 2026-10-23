"""Kimi Claude-Code adapter tests migrated to the consolidated surface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.test_launcher_contract import run_launcher

pytestmark = pytest.mark.usefixtures("hermetic_monitor")

_KIMI_CREDENTIALS = {
    "KIMICC_AUTH_TOKEN": "",
    "MOONSHOT_API_KEY": "",
    "KIMI_API_KEY": "",
}


def test_kimi_claude_code_rejects_foreign_ambient_auth(tmp_path: Path) -> None:
    foreign = "anthropic-secret-must-not-appear"
    result = run_launcher(
        "start-kimi.sh",
        "--harness",
        "claude-code",
        env={**_KIMI_CREDENTIALS, "HOME": str(tmp_path / "home"), "ANTHROPIC_AUTH_TOKEN": foreign},
    )
    # OO-58: the retired default is refused before the credential check. The secret still must not appear.
    assert result.returncode == 2
    assert "is retired in the model catalog" in result.stderr
    assert foreign not in result.stdout + result.stderr


@pytest.mark.parametrize("credential", ("KIMICC_AUTH_TOKEN", "MOONSHOT_API_KEY", "KIMI_API_KEY"))
def test_kimi_claude_code_accepts_only_explicit_kimi_credentials(credential: str, tmp_path: Path) -> None:
    secret = f"{credential.lower()}-secret"
    result = run_launcher(
        "start-kimi.sh",
        "--harness",
        "claude-code",
        env={**_KIMI_CREDENTIALS, credential: secret, "HOME": str(tmp_path / "home")},
    )
    assert result.returncode == 2, result.stdout
    assert "is retired in the model catalog" in result.stderr
    assert secret not in result.stdout + result.stderr
    assert "would exec" not in result.stdout


@pytest.mark.parametrize(
    ("endpoint", "alias"),
    (("platform", "k3"), ("coding", "k2.7"), ("platform", "k2.7-highspeed")),
)
def test_kimi_catalog_aliases_are_retired_before_an_endpoint_route(endpoint: str, alias: str, tmp_path: Path) -> None:
    """OO-58: a historical alias is refused before Claude Code argv is built."""
    result = run_launcher(
        "start-kimi.sh",
        "--harness",
        "claude-code",
        "--endpoint",
        endpoint,
        "--model",
        alias,
        env={**_KIMI_CREDENTIALS, "KIMICC_AUTH_TOKEN": "test-key", "HOME": str(tmp_path / "home")},
    )
    assert result.returncode == 2, result.stdout
    assert "is retired in the model catalog" in result.stderr
    assert "would exec" not in result.stdout


def test_kimicc_interactive_dry_run_refuses_retired_pins(tmp_path: Path) -> None:
    env = {**_KIMI_CREDENTIALS, "KIMICC_AUTH_TOKEN": "test-key", "HOME": str(tmp_path / "home")}
    default = run_launcher("start-kimicc.sh", env=env)
    k3 = run_launcher("start-kimicc.sh", "--model", "k3", env=env)
    override = run_launcher("start-kimicc.sh", env={**env, "KIMICC_EFFORT_LEVEL": "max"})

    assert default.returncode == k3.returncode == override.returncode == 2
    assert "k3-256k" in default.stderr
    assert "is retired in the model catalog" in k3.stderr
    assert "kimi-code/k3" in k3.stderr
    assert "would exec" not in default.stdout + k3.stdout + override.stdout


def test_kimicc_interactive_k2_7_is_retired(tmp_path: Path) -> None:
    result = run_launcher(
        "start-kimicc.sh",
        "--model",
        "k2.7",
        env={**_KIMI_CREDENTIALS, "KIMICC_AUTH_TOKEN": "test-key", "HOME": str(tmp_path / "home")},
    )

    assert result.returncode == 2, result.stdout
    assert "is retired in the model catalog" in result.stderr
    assert "would exec" not in result.stdout


def test_kimi_rejects_unknown_model_endpoint_and_isolation_value(tmp_path: Path) -> None:
    env = {**_KIMI_CREDENTIALS, "KIMICC_AUTH_TOKEN": "test-key", "HOME": str(tmp_path / "home")}
    model = run_launcher("start-kimi.sh", "--harness", "claude-code", "--model", "unknown", env=env)
    endpoint = run_launcher("start-kimi.sh", "--harness", "claude-code", "--endpoint", "unknown", env=env)
    isolation = run_launcher("start-kimi.sh", "--harness", "claude-code", env={**env, "LAUNCHER_ISOLATE_CONFIG": "2"})
    assert model.returncode == endpoint.returncode == isolation.returncode == 2


def test_kimi_no_isolate_config_fails_closed_on_route_pins(tmp_path: Path) -> None:
    home = tmp_path / "home"
    config_dir = home / ".claude"
    config_dir.mkdir(parents=True)
    (config_dir / "settings.json").write_text(
        json.dumps({"env": {"ANTHROPIC_BASE_URL": "https://foreign.invalid"}}), encoding="utf-8"
    )
    result = run_launcher(
        "start-kimi.sh",
        "--harness",
        "claude-code",
        "--no-isolate-config",
        env={**_KIMI_CREDENTIALS, "KIMICC_AUTH_TOKEN": "test-key", "HOME": str(home), "CLAUDE_CONFIG_DIR": ""},
    )
    assert result.returncode == 2, result.stdout
    assert "is retired in the model catalog" in result.stderr
    assert "https://foreign.invalid" not in result.stdout + result.stderr
    assert "would exec" not in result.stdout


def test_kimi_isolation_preserves_live_settings_and_uses_a_separate_config(tmp_path: Path) -> None:
    home = tmp_path / "home"
    config_dir = home / ".claude"
    config_dir.mkdir(parents=True)
    settings = config_dir / "settings.json"
    settings.write_text(json.dumps({"env": {"ANTHROPIC_BASE_URL": "https://foreign.invalid"}}), encoding="utf-8")
    result = run_launcher(
        "start-kimi.sh",
        "--harness",
        "claude-code",
        env={**_KIMI_CREDENTIALS, "KIMICC_AUTH_TOKEN": "test-key", "HOME": str(home), "CLAUDE_CONFIG_DIR": ""},
    )
    assert result.returncode == 2, result.stdout
    assert "is retired in the model catalog" in result.stderr
    assert settings.read_text(encoding="utf-8") == json.dumps(
        {"env": {"ANTHROPIC_BASE_URL": "https://foreign.invalid"}}
    )
    assert not (home / ".claude-kimicc").exists()
    assert "would exec" not in result.stdout
