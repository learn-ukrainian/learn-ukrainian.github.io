"""Prevent diagnostic coverage from changing the CI denominator or accepting moving refs."""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = yaml.safe_load((ROOT / ".github/workflows/coverage-ref.yml").read_text())
CI = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())


def step(job, name):
    return next(item for item in job["steps"] if item.get("name") == name)


@pytest.mark.parametrize(
    "sha,valid",
    [
        ("a" * 40, True),
        ("B" * 40, True),
        ("main", False),
        ("a" * 39, False),
        ("g" * 40, False),
        ("a" * 40 + "\n", False),
        ("$(touch injected)", False),
    ],
)
def test_validation_rejects_moving_refs_and_shell_input(tmp_path, sha, valid):
    validate = step(WORKFLOW["jobs"]["prepare"], "Validate an exact repository commit")
    gh = tmp_path / "gh"
    gh.write_text('#!/bin/bash\nprintf "%s\\n" "${SHA,,}"\n')
    gh.chmod(0o755)
    output = tmp_path / "output"
    env = os.environ | {
        "PATH": f"{tmp_path}:{os.environ['PATH']}",
        "SHA": sha,
        "REPO": "test/repo",
        "GITHUB_OUTPUT": str(output),
    }
    result = subprocess.run(
        ["bash", "-c", validate["run"]], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=10
    )
    assert (result.returncode == 0) is valid, result.stdout + result.stderr
    assert output.read_text() == f"sha={sha.lower()}\n" if valid else not output.exists()
    assert not (tmp_path / "injected").exists()


def test_nonrepository_commit_fails_even_when_syntax_is_valid(tmp_path):
    gh = tmp_path / "gh"
    gh.write_text("#!/bin/bash\nexit 1\n")
    gh.chmod(0o755)
    env = os.environ | {
        "PATH": f"{tmp_path}:{os.environ['PATH']}",
        "SHA": "a" * 40,
        "REPO": "test/repo",
        "GITHUB_OUTPUT": str(tmp_path / "output"),
    }
    result = subprocess.run(
        ["bash", "-c", WORKFLOW["jobs"]["prepare"]["steps"][0]["run"]],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        timeout=10,
    )
    assert result.returncode != 0
    assert not (tmp_path / "output").exists()


def test_ci_partition_and_pytest_denominator_are_unchanged():
    """Detect marker/option/file-split drift that would silently measure a smaller suite."""
    baseline = CI["jobs"]["pytest"]
    measured = WORKFLOW["jobs"]["pytest"]
    assert measured["strategy"] == baseline["strategy"]
    before = step(baseline, "Run pytest")["run"]
    after = step(measured, "Run CI pytest suite with branch coverage")["run"]
    assert (
        before[before.index("git ls-files") : before.index(".venv/bin/python -m pytest")]
        == after[after.index("git ls-files") : after.index('.venv/bin/python "$RUNNER_TEMP')]
    )
    original = shlex.split(
        before[before.index(".venv/bin/python -m pytest") : before.index("# Postgres")].replace("\\\n", "")
    )
    instrumented = shlex.split(
        after[after.index('.venv/bin/python "$RUNNER_TEMP') : after.index("# Postgres")].replace("\\\n", "")
    )
    instrumented = instrumented[instrumented.index("--") + 1 :]
    assert [arg for arg in instrumented if not arg.startswith("--cov")] == original[3:]
    for name in ("Python CI environment", "Download pytest duration snapshot"):
        assert (
            step(measured, name)["uses" if name == "Python CI environment" else "run"]
            == step(baseline, name)["uses" if name == "Python CI environment" else "run"]
        )
    assert measured["timeout-minutes"] > baseline["timeout-minutes"]


def test_workflow_is_manual_and_uploads_hidden_data_even_after_failure():
    assert WORKFLOW["on"] == {
        "workflow_dispatch": {
            "inputs": {
                "sha": {
                    "description": "Repository commit SHA to measure (40 hexadecimal characters)",
                    "required": True,
                    "type": "string",
                }
            }
        }
    }
    raw = step(WORKFLOW["jobs"]["pytest"], "Upload raw branch coverage and receipt")
    assert raw["if"] == "${{ always() }}"
    assert raw["with"]["include-hidden-files"] is True
    assert raw["with"]["if-no-files-found"] == "error"
    merge = WORKFLOW["jobs"]["combine"]
    assert merge["if"] == "${{ always() }}"
    assert set(merge["needs"]) == {"prepare", "pytest"}
    assert "continue-on-error" not in step(merge, "Validate receipts, combine and report")
