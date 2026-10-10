"""Canary summaries report execution evidence, never a hook's exit status (#10266)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
PROVIDERS = ("gemini", "cursor", "grok", "claude", "kimi", "glm", "codex")


def _canary_binding_probe(
    provider: str, dry_run: str, tmp_path: Path, *, inherited: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "bash", "-euo", "pipefail", "-c",
            'source "$1/scripts/lib/launcher_core.sh"; '
            # Codex is a core-only consumer here: do not mint/bootstrap real state.
            'launcher_adapter_canary() { :; }; '
            'if [ "$2" != codex ]; then source "$1/scripts/launchers/$2.sh"; fi; '
            'CANARY_TEST_DRY_RUN="$3"; CANARY_TEST_ROOT="$4"; '
            'launcher_inject_driver_agent() { :; }; '
            'fleet_comms_cold_clause() { printf "test plane"; }; '
            'canary_binding_probe() { '
            'LC_DRY_RUN="$CANARY_TEST_DRY_RUN"; LC_ROOT="$CANARY_TEST_ROOT"; '
            'LC_EPIC=infra; LC_FORWARD_ARGS=(); '
            'launcher_adapter_canary; launcher_bind_drive_epic; '
            'printf "LC_DRIVER_PROMPT=%s\n" "$LC_DRIVER_PROMPT"; }; '
            # Exercise actual entry initialization, stopping before startup side effects.
            'if [ "$5" = 1 ]; then '
            'launcher_defaults() { canary_binding_probe; exit; }; '
            'launcher_main "$2" driver; '
            'else canary_binding_probe; fi',
            "bash", str(REPO), provider, dry_run, str(tmp_path),
            "1" if inherited else "0",
        ],
        env={**os.environ, "LC_PROVIDER_CANARY_RAN": "1" if inherited else "0"},
        capture_output=True, text=True, check=False, timeout=30,
    )


def _driver_prompt(result: subprocess.CompletedProcess[str]) -> str:
    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith("LC_DRIVER_PROMPT=")]
    assert len(lines) == 1, result.stdout
    return lines[0]


@pytest.mark.parametrize("provider", PROVIDERS)
@pytest.mark.parametrize("dry_run", ("0", "1"))
def test_noop_adapter_does_not_claim_a_canary(provider: str, dry_run: str, tmp_path: Path) -> None:
    result = _canary_binding_probe(provider, dry_run, tmp_path)
    assert "provider canary: not run" in _driver_prompt(result)
    assert "provider canary: ran" not in result.stdout
    assert "ran its provider canary" not in result.stdout
    if provider in ("gemini", "cursor") or (provider in ("claude", "kimi") and dry_run == "1"):
        assert f"{provider} adapter: provider canary: not run" in result.stdout
        assert "would run provider canary" not in result.stdout


@pytest.mark.parametrize("provider", PROVIDERS)
@pytest.mark.parametrize("dry_run", ("0", "1"))
def test_main_clears_inherited_canary_execution_report(
    provider: str, dry_run: str, tmp_path: Path,
) -> None:
    result = _canary_binding_probe(provider, dry_run, tmp_path, inherited=True)
    assert "provider canary: not run" in _driver_prompt(result)
    assert "provider canary: ran" not in result.stdout


@pytest.mark.parametrize(
    ("ran", "dry_run", "expected"),
    (("1", "0", "ran"), ("0", "0", "not run"), ("1", "1", "not run")),
)
def test_binding_uses_explicit_adapter_execution_report(
    ran: str, dry_run: str, expected: str, tmp_path: Path
) -> None:
    result = subprocess.run(
        [
            "bash", "-euo", "pipefail", "-c",
            'source "$1/scripts/lib/launcher_core.sh"; '
            'LC_PROVIDER_CANARY_RAN="$2"; LC_DRY_RUN="$3"; LC_ROOT="$4"; '
            'LC_EPIC=infra; LC_FORWARD_ARGS=(); '
            'launcher_inject_driver_agent() { :; }; '
            'fleet_comms_cold_clause() { printf "test plane"; }; '
            'launcher_bind_drive_epic; printf "LC_DRIVER_PROMPT=%s\n" "$LC_DRIVER_PROMPT"',
            "bash", str(REPO), ran, dry_run, str(tmp_path),
        ],
        capture_output=True, text=True, check=False, timeout=30,
    )
    assert f"provider canary: {expected}" in _driver_prompt(result)
