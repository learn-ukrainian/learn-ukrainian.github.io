"""Frontend CI hydrates and builds once and reuses only a verified build (#9718)."""

from __future__ import annotations

import os
import re
import shlex
import subprocess
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.repo_invariant

ROOT = Path(__file__).resolve().parents[1]
CI = ROOT / ".github/workflows/ci.yml"
STEP = "Build, drift check, unit and built-output tests"
def frontend_jobs_steps() -> list[dict]:
    return yaml.safe_load(CI.read_text(encoding="utf-8"))["jobs"]["frontend"]["steps"]


def build_step() -> dict:
    return next(step for step in frontend_jobs_steps() if step.get("name") == STEP)


def run_lines(step: dict) -> list[str]:
    joined = re.sub(r"\\\n\s*", "", step["run"])
    return [line.strip() for line in joined.splitlines() if line.strip()]


def clean_git_env() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


def test_drift_check_fails_on_generated_teacher_key_drift(tmp_path: Path) -> None:
    site = tmp_path / "site"
    (site / "src/data").mkdir(parents=True)
    teacher_keys = site / "src/data/lexicon-teacher-lesson-keys.json"
    teacher_keys.write_text('{"keys": []}\n', encoding="utf-8")
    (site / "src/data/practice-zno-meta.json").write_text("{}\n", encoding="utf-8")
    env = clean_git_env()
    git = ["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false"]
    for args in (["init", "-q"], ["add", "."], ["commit", "-q", "-m", "fixture"]):
        subprocess.run([*git, *args], cwd=tmp_path, env=env, check=True, timeout=60)
    drift = shlex.split(next(line for line in run_lines(build_step()) if line.startswith("git diff")))

    assert subprocess.run(drift, cwd=site, env=env, capture_output=True, timeout=60).returncode == 0
    teacher_keys.write_text('{"keys": ["drifted"]}\n', encoding="utf-8")
    assert subprocess.run(drift, cwd=site, env=env, capture_output=True, timeout=60).returncode == 1
