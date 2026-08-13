"""Gemini adapter and driver lifecycle tests."""

from __future__ import annotations

import pytest

from tests.test_launcher_contract import run_launcher


def test_gemini_interactive_defaults_to_agy_and_rejects_epic() -> None:
    interactive = run_launcher("start-gemini.sh")
    epic = run_launcher("start-gemini.sh", "--epic", "atlas")
    assert interactive.returncode == 0, interactive.stderr
    assert "would exec agy --model gemini-3.7-flash-high" in interactive.stdout
    assert epic.returncode == 2
    assert "interactive launchers reject --epic" in epic.stderr


@pytest.mark.parametrize("selector", ("atlas", "practice", "infra.devops", "seminars-bio"))
def test_gemini_driver_claims_a_lease_for_supported_selectors(selector: str) -> None:
    result = run_launcher("start-gemini-driver.sh", "--epic", selector)
    assert result.returncode == 0, result.stderr
    assert "would claim lease" in result.stdout
    assert "would run provider canary" in result.stdout
    assert "would bind drive-epic" in result.stdout


@pytest.mark.parametrize("model", ("gemini-3.6-flash-high", "gemini-3.1-pro-high"))
def test_gemini_driver_allows_only_certified_models(model: str) -> None:
    result = run_launcher("start-gemini-driver.sh", "--epic", "devops", "--model", model)
    assert result.returncode == 0, result.stderr


def test_gemini_driver_rejects_uncertified_model_and_non_agy_harness() -> None:
    uncertified = run_launcher("start-gemini-driver.sh", "--epic", "devops", "--model", "gemini-unknown")
    harness = run_launcher("start-gemini.sh", "--harness", "gemini-cli")
    assert uncertified.returncode == 4
    assert harness.returncode == 2
    assert "only --harness agy" in harness.stderr


def test_gemini_forwards_provider_arguments_only_after_separator() -> None:
    result = run_launcher("start-gemini.sh", "--", "--sandbox", "read-only")
    assert result.returncode == 0, result.stderr
    assert "--sandbox read-only" in result.stdout
