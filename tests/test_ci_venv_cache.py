"""Lock the CI venv cache: skip the 79s lockfile unpack on a verified hit.

Live evidence (2026-08-28, public Actions jobs on this repo):

- PR 33216291039 fastlane: pip-wheels restore hit, then
  ``Install fastlane test dependencies`` still ran 79s (22:19:47–22:21:06).
  That job was the PR-tier critical path (3m32s vs secret-scan 1m33s / ruff 40s).
- merge_group 33215933820 shard 1/4: pip-wheels hit, then
  ``Install dependencies`` still ran 79s (22:15:48–22:17:07) on the MQ
  pytest-spine critical path.

The wheel cache is necessary but not sufficient. Caching the populated
``.venv`` (exact lockfile key, no restore-keys) is the remaining unpack skip.
A hit is accepted only after ``scripts/ci/accept_ci_venv.py`` imports pytest
and coverage; otherwise the existing pip install runs. CI Gate needs, fail-closed
semantics, and merge_group cancel-in-progress are unchanged.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

import yaml

from scripts.ci.accept_ci_venv import REQUIRED_IMPORTS, accept_ci_venv, main

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI = _REPO_ROOT / ".github" / "workflows" / "ci.yml"
_ACCEPT = _REPO_ROOT / "scripts" / "ci" / "accept_ci_venv.py"

CI_VENV_KEY = (
    "ci-venv-${{ runner.os }}-py3.12-"
    "${{ hashFiles('requirements-lock.txt') }}-no-live-ml-mp0.70.18-hf1.24.0"
)
_CACHE_ACTION = "actions/cache/restore@55cc8345863c7cc4c66a329aec7e433d2d1c52a9"
_SAVE_ACTION = "actions/cache/save@55cc8345863c7cc4c66a329aec7e433d2d1c52a9"


def _load_ci() -> dict:
    data = yaml.safe_load(_CI.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _steps(job_id: str) -> list[dict]:
    job = _load_ci()["jobs"][job_id]
    assert isinstance(job, dict)
    steps = job["steps"]
    assert isinstance(steps, list)
    return steps


def _named(job_id: str, name: str) -> dict:
    for step in _steps(job_id):
        if step.get("name") == name:
            return step
    raise AssertionError(f"{job_id} is missing step {name!r}")


def _write_fake_python(venv: Path, script: str) -> None:
    bin_dir = venv / "bin"
    bin_dir.mkdir(parents=True)
    python = bin_dir / "python"
    python.write_text(script, encoding="utf-8")
    python.chmod(python.stat().st_mode | stat.S_IEXEC)


def test_accept_rejects_restore_miss_even_if_venv_looks_valid(tmp_path: Path) -> None:
    venv = tmp_path / ".venv"
    _write_fake_python(venv, "#!/bin/sh\nexit 0\n")
    assert accept_ci_venv(venv, restore_hit=False) is False


def test_accept_rejects_missing_or_broken_python(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    assert accept_ci_venv(missing, restore_hit=True) is False

    broken = tmp_path / "broken"
    _write_fake_python(broken, "#!/bin/sh\nexit 1\n")
    assert accept_ci_venv(broken, restore_hit=True) is False


def test_accept_requires_pytest_and_coverage(tmp_path: Path) -> None:
    venv = tmp_path / ".venv"
    _write_fake_python(
        venv,
        "#!/bin/sh\n"
        "case \"$2\" in\n"
        "  *pytest*coverage*) exit 0 ;;\n"
        "  *) exit 1 ;;\n"
        "esac\n",
    )
    assert REQUIRED_IMPORTS == ("pytest", "coverage")
    assert accept_ci_venv(venv, restore_hit=True) is True


def test_main_writes_github_output_and_never_fails_closed_on_cache(tmp_path: Path) -> None:
    output = tmp_path / "github-output"
    env = os.environ.copy()
    env["GITHUB_OUTPUT"] = str(output)
    env["RESTORE_HIT"] = "false"
    env["CI_VENV"] = str(tmp_path / "no-such-venv")
    monkey_keys = {"GITHUB_OUTPUT", "RESTORE_HIT", "CI_VENV"}
    old = {key: os.environ.get(key) for key in monkey_keys}
    try:
        os.environ.update(env)
        assert main([]) == 0
    finally:
        for key, value in old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    assert output.read_text(encoding="utf-8") == "cache-hit=false\n"


def test_fastlane_and_shards_share_exact_venv_key_without_restore_keys() -> None:
    for job_id, restore_name, save_name in (
        ("pytest-fastlane", "Restore CI venv", "Save CI venv"),
        ("python", "Restore CI venv", "Save CI venv"),
    ):
        restore = _named(job_id, restore_name)
        save = _named(job_id, save_name)
        assert restore["uses"].startswith(_CACHE_ACTION)
        assert save["uses"].startswith(_SAVE_ACTION)
        assert restore["with"]["path"] == ".venv"
        assert save["with"]["path"] == ".venv"
        assert restore["with"]["key"] == CI_VENV_KEY
        assert save["with"]["key"] == CI_VENV_KEY
        assert "restore-keys" not in restore["with"]


def test_coverage_floor_restores_same_venv_key_and_does_not_save() -> None:
    restore = _named("coverage-floor", "Restore CI venv")
    assert restore["with"]["key"] == CI_VENV_KEY
    assert restore["with"]["path"] == ".venv"
    assert "restore-keys" not in restore["with"]
    names = [step.get("name") for step in _steps("coverage-floor")]
    assert "Save CI venv" not in names


def test_install_and_wheel_restore_are_skipped_on_accepted_venv() -> None:
    fastlane_install = _named(
        "pytest-fastlane", "Install fastlane test dependencies (lock minus live ML)"
    )
    fastlane_wheels = _named("pytest-fastlane", "Restore pip wheel cache")
    assert "steps.ci-venv.outputs.cache-hit != 'true'" in str(fastlane_install["if"])
    assert "steps.plan.outputs.has_tests == 'true'" in str(fastlane_install["if"])
    assert "steps.ci-venv.outputs.cache-hit != 'true'" in str(fastlane_wheels["if"])

    shard_install = _named("python", "Install dependencies")
    shard_wheels = _named("python", "Restore pip wheel cache")
    for step in (shard_install, shard_wheels):
        condition = str(step["if"])
        assert "steps.ci-venv.outputs.cache-hit != 'true'" in condition
        assert "docs_skills" in condition


def test_accept_step_uses_stdlib_helper_not_inline_probe() -> None:
    for job_id in ("pytest-fastlane", "python", "coverage-floor"):
        step = _named(job_id, "Accept restored CI venv")
        assert "scripts/ci/accept_ci_venv.py" in step["run"]
        assert step["env"]["RESTORE_HIT"] == "${{ steps.ci-venv-cache.outputs.cache-hit }}"
        assert "id" in step and step["id"] == "ci-venv"


def test_gate_and_merge_group_invariants_hold() -> None:
    workflow = _load_ci()
    concurrency = workflow["concurrency"]
    assert concurrency["cancel-in-progress"] == "${{ github.event_name == 'pull_request' }}"
    gate = workflow["jobs"]["ci-gate"]
    assert gate["if"] == "always() && !cancelled()"
    assert gate["needs"] == [
        "ruff",
        "secret-scan",
        "landing-class",
        "pytest-plan",
        "pytest-fastlane",
        "python",
        "contracts",
        "frontend",
        "coverage-floor",
        "pytest-duration-publish",
    ]


def test_coverage_floor_still_enforces_fail_under_and_skips_render() -> None:
    combine = _named("coverage-floor", "Combine and enforce")
    run = combine["run"]
    assert "coverage combine" in run
    assert "coverage report --fail-under=35" in run
    assert "refusing to pass vacuously" in run
    assert "coverage xml" not in run
    assert "coverage html" not in run
    assert "CI_VENV_HIT" in combine.get("env", {})


def test_venv_key_embeds_workflow_extra_pins() -> None:
    """Extras are installed after the lockfile; they must bust the venv key."""
    install = _named("python", "Install dependencies")["run"]
    assert "multiprocess==0.70.18" in install
    assert "huggingface-hub==1.24.0" in install
    assert "mp0.70.18" in CI_VENV_KEY
    assert "hf1.24.0" in CI_VENV_KEY


def test_accept_helper_is_tracked() -> None:
    assert _ACCEPT.is_file()
    text = _ACCEPT.read_text(encoding="utf-8")
    assert "fail-open toward a fresh install" in text
    assert "pytest" in text and "coverage" in text
