"""Contract tests for start-codex-driver.sh (sustained driver vs --governor mode)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LAUNCHER = _REPO_ROOT / "start-codex-driver.sh"


def _clean_environ() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def _run_driver(
    *arguments: str,
    env_override: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = _clean_environ()
    env["CODEX_DRIVER_DRY_RUN"] = "1"
    if env_override:
        env.update(env_override)
    return subprocess.run(
        ["bash", str(_LAUNCHER), *arguments],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )


def test_default_mode_forwards_epic_without_model_pin() -> None:
    res = _run_driver("devops")
    assert res.returncode == 0, res.stderr
    assert "would exec" in res.stdout
    assert "--epic devops" in res.stdout
    assert "--model" not in res.stdout


def test_default_mode_forwards_extra_flags() -> None:
    res = _run_driver("atlas", "--verbose", "--foo=bar")
    assert res.returncode == 0, res.stderr
    assert "--epic atlas" in res.stdout
    assert "--verbose --foo=bar" in res.stdout


def test_governor_mode_pins_model_unsets_epic_and_passes_prompt() -> None:
    res = _run_driver("--governor", "devops", env_override={"SESSION_EPIC": "should_be_unset"})
    assert res.returncode == 0, res.stderr
    assert "would exec" in res.stdout
    assert "--model gpt-5.6-sol" in res.stdout
    assert "--epic" not in res.stdout
    assert "dynamic-area-epic-fleet-governor.md" in res.stdout
    assert "TARGET=devops GOAL=AUTO" in res.stdout


def test_governor_mode_auto_selector_bypasses_validation() -> None:
    res = _run_driver("--governor", "AUTO")
    assert res.returncode == 0, res.stderr
    assert "--model gpt-5.6-sol" in res.stdout
    assert "TARGET=AUTO GOAL=AUTO" in res.stdout


def test_governor_mode_missing_selector_exits_2() -> None:
    res = _run_driver("--governor")
    assert res.returncode == 2
    assert "Usage:" in res.stderr


def test_unknown_selector_fails_in_default_and_governor_modes() -> None:
    res_def = _run_driver("unknown_selector_xyz")
    assert res_def.returncode == 2
    assert "Error: unknown lane selector 'unknown_selector_xyz'." in res_def.stderr

    res_gov = _run_driver("--governor", "unknown_selector_xyz")
    assert res_gov.returncode == 2
    assert "Error: unknown lane selector 'unknown_selector_xyz'." in res_gov.stderr
