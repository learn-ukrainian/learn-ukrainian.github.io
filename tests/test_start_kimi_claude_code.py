"""Kimi Claude-Code adapter tests migrated to the consolidated surface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.test_launcher_contract import run_launcher

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
    assert result.returncode == 3
    assert "no Kimi API credential" in result.stderr
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
    assert result.returncode == 0, result.stderr
    assert f"credential_source={credential}" in result.stdout
    assert secret not in result.stdout + result.stderr


@pytest.mark.parametrize(
    ("endpoint", "alias", "resolved"),
    (("platform", "k3", "kimi-k3[1m]"), ("coding", "k2.7", "kimi-for-coding"), ("platform", "k2.7-highspeed", "kimi-k2.7-code-highspeed")),
)
def test_kimi_catalog_aliases_use_the_endpoint_allowlist(endpoint: str, alias: str, resolved: str, tmp_path: Path) -> None:
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
    assert result.returncode == 0, result.stderr
    escaped_model = resolved.replace("[", "\\[").replace("]", "\\]")
    assert f"would exec claude --model {escaped_model}" in result.stdout


def test_kimicc_interactive_dry_run_reports_k3_high_and_explicit_override(tmp_path: Path) -> None:
    env = {**_KIMI_CREDENTIALS, "KIMICC_AUTH_TOKEN": "test-key", "HOME": str(tmp_path / "home")}
    default = run_launcher("start-kimicc.sh", env=env)
    k3 = run_launcher("start-kimicc.sh", "--model", "k3", env=env)
    override = run_launcher("start-kimicc.sh", env={**env, "KIMICC_EFFORT_LEVEL": "max"})

    assert default.returncode == k3.returncode == override.returncode == 0
    # Operator 2026-08-13: the default model is k3-256k with no forced effort;
    # the k3-high default applies only when full k3 is explicitly selected.
    assert "KimiCC route: effort=not-exposed" in default.stdout
    assert "KimiCC route: effort=high" in k3.stdout
    assert "KimiCC route: effort=max" in override.stdout


def test_kimicc_interactive_k2_7_dry_run_has_no_k3_effort_default(tmp_path: Path) -> None:
    result = run_launcher(
        "start-kimicc.sh",
        "--model",
        "k2.7",
        env={**_KIMI_CREDENTIALS, "KIMICC_AUTH_TOKEN": "test-key", "HOME": str(tmp_path / "home")},
    )

    assert result.returncode == 0, result.stderr
    assert "KimiCC route: effort=not-exposed" in result.stdout


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
    assert result.returncode == 1
    assert "KimiCC refuses to launch" in result.stderr
    assert "ANTHROPIC_BASE_URL" in result.stderr


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
    assert result.returncode == 0, result.stderr
    assert settings.read_text(encoding="utf-8") == json.dumps(
        {"env": {"ANTHROPIC_BASE_URL": "https://foreign.invalid"}}
    )
    assert (home / ".claude-kimicc").is_dir()
