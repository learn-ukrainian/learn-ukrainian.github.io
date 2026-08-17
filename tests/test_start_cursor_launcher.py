"""Cursor driver launcher seat + lifecycle tests (#6956)."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.test_launcher_contract import REPO, run_launcher

DRIVER = "start-cursor-driver.sh"


def test_cursor_driver_wrapper_calls_launcher_main_cursor() -> None:
    text = (REPO / DRIVER).read_text(encoding="utf-8")
    assert "launcher_core.sh" in text
    assert "launcher_main cursor driver" in text
    assert (REPO / DRIVER).stat().st_mode & 0o111


def test_cursor_driver_help_mentions_epic() -> None:
    result = run_launcher(DRIVER, "--help")
    assert result.returncode == 0, result.stderr
    assert "--epic" in result.stdout
    assert "Usage:" in result.stdout


def test_cursor_driver_requires_epic_fail_closed() -> None:
    """Launching without --epic must not silently claim main orchestrator."""
    missing = run_launcher(DRIVER)
    assert missing.returncode == 2, missing.stderr
    assert "driver launch requires --epic" in missing.stderr


@pytest.mark.parametrize("selector", ("infra", "devops", "atlas", "corpus"))
def test_cursor_driver_claims_lease_for_supported_selectors(selector: str) -> None:
    result = run_launcher(DRIVER, "--epic", selector)
    assert result.returncode == 0, result.stderr
    assert "would claim lease" in result.stdout
    assert "would run provider canary" in result.stdout
    assert "would bind drive-epic" in result.stdout
    assert "--model auto" in result.stdout


def test_cursor_driver_rejects_uncertified_model_and_foreign_harness() -> None:
    uncertified = run_launcher(DRIVER, "--epic", "devops", "--model", "cursor-unknown")
    harness = run_launcher(DRIVER, "--epic", "devops", "--harness", "agy")
    assert uncertified.returncode == 4
    assert "not certified" in uncertified.stderr
    assert harness.returncode == 2
    assert "only --harness cursor-agent" in harness.stderr


@pytest.mark.parametrize("model", ("auto", "grok-4.6", "composer-2.5"))
def test_cursor_driver_accepts_allowlisted_models(model: str) -> None:
    result = run_launcher(DRIVER, "--epic", "infra", "--model", model)
    assert result.returncode == 0, result.stderr
    assert f"--model {model}" in result.stdout


def test_cursor_seat_enumerated_in_launcher_core_and_public_estate() -> None:
    """Seat hooks live as case arms (no separate seat list) next to sibling drivers."""
    core = (REPO / "scripts/lib/launcher_core.sh").read_text(encoding="utf-8")
    assert "cursor)" in core
    assert "handoff_identity_for_cursor_epic" in core
    assert "cursor:auto|cursor:grok-4.6|cursor:composer-2.5" in core
    assert Path(REPO / "scripts/launchers/cursor.sh").is_file()
    assert DRIVER in {
        path.name for path in REPO.glob("start-*-driver.sh") if path.parent == REPO
    }
