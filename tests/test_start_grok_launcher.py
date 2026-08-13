"""Grok adapter and driver lifecycle tests."""

from __future__ import annotations

import pytest

from tests.test_launcher_contract import run_launcher


def test_grok_interactive_defaults_to_native_harness_and_rejects_epic() -> None:
    interactive = run_launcher("start-grok.sh")
    epic = run_launcher("start-grok.sh", "--epic", "atlas")
    assert interactive.returncode == 0, interactive.stderr
    assert "would exec grok" in interactive.stdout
    assert "--model grok-4.5" not in interactive.stdout
    assert "--model" not in interactive.stdout
    assert "--reasoning-effort" not in interactive.stdout
    assert "--effort" not in interactive.stdout
    assert epic.returncode == 2
    assert "interactive launchers reject --epic" in epic.stderr


def test_grok_explicit_model_still_pins() -> None:
    result = run_launcher("start-grok.sh", "--model", "grok-4.5")
    assert result.returncode == 0, result.stderr
    assert "--model grok-4.5" in result.stdout


def test_grok_effort_injects_reasoning_effort_only_when_set() -> None:
    with_effort = run_launcher("start-grok.sh", "--effort", "high")
    without = run_launcher("start-grok.sh")
    assert with_effort.returncode == 0, with_effort.stderr
    assert "--reasoning-effort high" in with_effort.stdout
    assert without.returncode == 0, without.stderr
    assert "--reasoning-effort" not in without.stdout
    assert "--effort" not in without.stdout


@pytest.mark.parametrize("selector", ("atlas", "practice", "infra.devops", "seminars-folk", "infra"))
def test_grok_driver_claims_a_lease_for_supported_selectors(selector: str) -> None:
    result = run_launcher("start-grok-driver.sh", "--epic", selector)
    assert result.returncode == 0, result.stderr
    assert "would claim lease" in result.stdout
    assert "would run provider canary" in result.stdout
    assert "would bind drive-epic" in result.stdout
    assert "--model grok-4.5" not in result.stdout
    assert "--model" not in result.stdout


def test_grok_driver_rejects_uncertified_model_and_non_grok_harness() -> None:
    uncertified = run_launcher("start-grok-driver.sh", "--epic", "devops", "--model", "grok-unknown")
    harness = run_launcher("start-grok.sh", "--harness", "agy")
    assert uncertified.returncode == 4
    assert harness.returncode == 2
    assert "only --harness grok" in harness.stderr


def test_grok_forwards_provider_arguments_only_after_separator() -> None:
    result = run_launcher("start-grok.sh", "--", "--reasoning", "high")
    assert result.returncode == 0, result.stderr
    assert "--reasoning high" in result.stdout
