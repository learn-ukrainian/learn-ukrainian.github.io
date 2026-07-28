"""Claude driver's lease and drive-epic lifecycle tests."""

from __future__ import annotations

import pytest

from tests.test_launcher_contract import run_launcher


@pytest.mark.parametrize("selector", ("devops", "infra.devops", "atlas.practice", "seminars-folk"))
def test_driver_accepts_canonical_and_legacy_lane_selectors(selector: str) -> None:
    result = run_launcher("start-claude-driver.sh", "--epic", selector)
    assert result.returncode == 0, result.stderr
    assert "would claim lease" in result.stdout
    assert "would bind drive-epic" in result.stdout


def test_claude_driver_claims_before_canary_and_drive_epic() -> None:
    result = run_launcher("start-claude-driver.sh", "--epic", "devops")
    assert result.returncode == 0, result.stderr
    assert result.stdout.index("would claim lease") < result.stdout.index("would run provider canary")
    assert result.stdout.index("would run provider canary") < result.stdout.index("would bind drive-epic")


@pytest.mark.parametrize("arguments", (("--epic",), ("--epic", "unknown-lane"), ("--governor", "AUTO")))
def test_claude_driver_rejects_invalid_lifecycle_inputs(arguments: tuple[str, ...]) -> None:
    result = run_launcher("start-claude-driver.sh", *arguments)
    assert result.returncode == 2
    assert "Error:" in result.stderr
