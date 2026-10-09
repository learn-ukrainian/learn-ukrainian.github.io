"""Canary summaries report execution evidence, never a hook's exit status (#10266)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("provider", ("gemini", "cursor", "grok"))
@pytest.mark.parametrize("dry_run", ("0", "1"))
def test_noop_adapter_does_not_claim_a_canary(provider: str, dry_run: str, tmp_path: Path) -> None:
    result = subprocess.run(
        [
            "bash", "-euo", "pipefail", "-c",
            'source "$1/scripts/lib/launcher_core.sh"; '
            'source "$1/scripts/launchers/$2.sh"; '
            'LC_DRY_RUN="$3"; LC_ROOT="$4"; LC_EPIC=infra; LC_FORWARD_ARGS=(); '
            'launcher_inject_driver_agent() { :; }; '
            'fleet_comms_cold_clause() { printf "test plane"; }; '
            'launcher_adapter_canary; launcher_bind_drive_epic; '
            'printf "%s\n" "$LC_DRIVER_PROMPT"',
            "bash", str(REPO), provider, dry_run, str(tmp_path),
        ],
        capture_output=True, text=True, check=False, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "provider canary: not run" in result.stdout
    assert "ran its provider canary" not in result.stdout
    if provider != "grok":
        assert f"{provider} adapter: provider canary: not run" in result.stdout
        assert "would run provider canary" not in result.stdout


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
            'launcher_bind_drive_epic; printf "%s\n" "$LC_DRIVER_PROMPT"',
            "bash", str(REPO), ran, dry_run, str(tmp_path),
        ],
        capture_output=True, text=True, check=False, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert f"provider canary: {expected}" in result.stdout
